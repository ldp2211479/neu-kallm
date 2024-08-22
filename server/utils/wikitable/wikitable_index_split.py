from tqdm import trange, tqdm
import argparse
import pickle
import multiprocessing as mp
import logging
from wikitable_clean import *

logging.basicConfig(level=logging.INFO, format='%(asctime)s %(message)s')
logging.info('Starting processing...')

import os
# os.environ['CUDA_VISIBLE_DEVICES']='0,1,2,3'

def clean_program(text_and_list):
    text = text_and_list[0]
    result_list, module_list = text_and_list[1]
    
    text = text.replace("EOT", "<EOT>").strip() if "<EOT>" not in text else text.strip()

    if "<ROW>" in text:
        clean_text = text
        clean_text = clean_long_sentence(clean_text)
        if r"{{tree list" in clean_text:
            clean_text = clean_tree(clean_text)
        if r'{{harvnb' in clean_text:
            clean_text = clean_harvnb(clean_text)
        if r'{{notelist' in clean_text:
            clean_text = clean_notelist(clean_text)
        if r'<div' in clean_text:
            clean_text = clean_div(clean_text)
        for module in module_list:
            clean_text = module(clean_text)

        if '\n' not in clean_text:
            clean_text = clean_text.replace("\n", " ")
            result_list.append(clean_text)
        else:
            pass

def clean(args, module_list):
    with open(args.path_tables_text, "rb") as f:
        tables_text = pickle.load(f)
        manager = mp.Manager()
        result_list = manager.list()

        def table_text_generator(tables_text):
            for table_text in tables_text:
                yield table_text

        print("before the size is ", len(tables_text))
        with mp.Pool(mp.cpu_count()) as pool:
            for _ in tqdm(pool.imap_unordered(clean_program, ((table_text, (result_list, module_list)) for table_text in table_text_generator(tables_text))), desc="Processing pages"):
                pass
        
        # Combine results and write to file
        print("after the size is ", len(result_list))
        return result_list


############# colbert #############
def get_collection(tables_text, args):
    with open(args.collection, "w") as f:
        for i in trange(len(tables_text), desc=f"Writing blocks to {args.collection}"):
            f.write(
                str(i) + "\t" + tables_text[i] + "\n"
            )
    pass


def get_index(args):
    import sys
    sys.path.insert(0, "./ColBERT/")
    from colbert.infra import Run, RunConfig, ColBERTConfig
    from colbert.data import Queries, Collection
    from colbert import Indexer, Searcher

    collection = Collection(path=args.collection)

    f"Loaded {len(collection):,} tables"

    print("example table from collection: ", collection[0])
    print()

    with Run().context(
        RunConfig(nranks=args.nranks, root=args.root_path, experiment=args.experiment_name)
    ):  
        config = ColBERTConfig(doc_maxlen=args.doc_maxlen, nbits=args.nbits)
        indexer = Indexer(checkpoint=args.checkpoint, config=config)
        indexer.index(name=args.index_name, collection=collection, overwrite=True)
    
    query = "how many seasons are there in one tree hill"
    print(f"#> {query}")

    # Find the top-3 passages for this query
    with Run().context(RunConfig(experiment=args.experiment_name, index_root=args.root_path)):
        searcher = Searcher(
            index=os.path.join(f"{args.experiment_name}/indexes", args.index_name),
            collection=collection,
            checkpoint=args.checkpoint,
            config = ColBERTConfig(total_visible_gpus=0),
        )
    results = searcher.search(query, k=1)
    for passage_id, passage_rank, passage_score in zip(*results):
        print(
            f"\t [{passage_rank}] \t\t {passage_score:.1f} \t\t {searcher.collection[passage_id][:100]}"
        )


############# main #############
def main():
    arg_parser = argparse.ArgumentParser(description="")
    arg_parser.add_argument('--path_tables_text', type=str, default='./dataset/wikitable/tables_text.pkl', help='The path to wikitables text')
    arg_parser.add_argument('--collection', type=str, default='./model/wikitable/collection.tsv', help='The path to colbert collection')
    arg_parser.add_argument('--checkpoint', type=str, default="./model/wikitable/colbert", help='the path to colbert checkpoint which is finetuned')
    arg_parser.add_argument('--root_path', type=str, default="./model/wikitable", help='the name to colbert index')
    
    arg_parser.add_argument('--nbits', type=int, default=2)
    arg_parser.add_argument('--experiment_name', type=str, default="wikitable", help='the name of colbert experiment_name')
    arg_parser.add_argument('--index_name', type=str, default="wikitable_index.nbits=2", help='the name to colbert index')
    arg_parser.add_argument('--nranks', type=int, default=4, help='nranks specifies the number of GPUs to use')
    arg_parser.add_argument('--doc_maxlen', type=int, default=512)

    args = arg_parser.parse_args()

    # module_list = [clean_br, clean_word_ref, clean_ref, clean_flag, clean_font, clean_tooltip, clean_convert, clean_others, clean_convert, clean_list]
    # combined_tables_text = clean(args, module_list)
    # get_collection(combined_tables_text, args)
    get_index(args)


if __name__ == "__main__":
    main()