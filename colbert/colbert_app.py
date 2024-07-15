import argparse
import logging
import sys
from flask import Flask
from flask_cors import CORS
from flask_restful import Api, reqparse
import math
from functools import lru_cache
import atexit
import utils.globalvar

sys.path.insert(0, "./ColBERT/")

from colbert import Searcher
from colbert.infra import Run, RunConfig
from colbert.infra.config.config import ColBERTConfig
from utils.wikidata import execute_wikidata_query, wikidata_load

########## server ########## 
app = Flask(__name__)
CORS(app)
api = Api(app)
logger = logging.getLogger(__name__)

req_parser = reqparse.RequestParser()
req_parser.add_argument("query", type=str, help="The search query")
req_parser.add_argument("evi_num", type=int, help="Number of documents to return")
req_parser.add_argument("source", type=str, help="source [wikipedia, wikidata, wikitable]")



@lru_cache(maxsize=20000)
def wikipedia_search(query, k):
    search_results = utils.globalvar.widipedia_searcher.search(
        query, k=k
    )  # retrieve more results so that our probability estimation is more accurate
    passage_ids, passage_ranks, passage_scores = search_results
    passages = [utils.globalvar.widipedia_searcher.collection[passage_id] for passage_id in passage_ids]
    passage_probs = [math.exp(score) for score in passage_scores]
    passage_probs = [prob / sum(passage_probs) for prob in passage_probs]
    results = {
        "passages": passages[:k],
        "passage_ids": passage_ids[:k],
        "passage_ranks": passage_ranks[:k],
        "passage_scores": passage_scores[:k],
        "passage_probs": passage_probs[:k],
    }
    return results

@lru_cache(maxsize=20000)
def wikidata_search(query):
    prediction_results, sparql = execute_wikidata_query(query)
    return prediction_results, sparql


@app.route("/search", methods=["GET", "POST"])
def get():
    args = req_parser.parse_args()
    user_query = args["query"]
    source = args["source"]
    logger.info(source)
    if source == "wikipedia":
        evi_num = args["evi_num"]
        try:
            results = wikipedia_search(user_query, evi_num)
        except Exception as e:
            logger.error(str(e))
            return {}, 500
    elif source == 'wikidata':
        try:
            results = wikidata_search(user_query)
        except Exception as e:
            logger.error(str(e))
            return {}, 500

    return results


def init():
    utils.globalvar.init()

    arg_parser = argparse.ArgumentParser()
    # wikipedia arg
    arg_parser.add_argument(
        "--memory_map",
        type=str,
        choices=["True", "False", "true", "false"],
        default="False",
        help="If set, will keep the ColBERT index on disk, so that we use less RAM. But you need to coalesce the index first.",
    )# Has the type str since it has to support inputs from gunicorn
    arg_parser.add_argument(
        "--wikipedia_colbert_experiment_name",
        type=str,
        default="wikipedia_all",
        help="name of wikipedia colbert indexing experiment",
    )
    arg_parser.add_argument(
        "--wikipedia_colbert_index_path",
        type=str,
        help="path to wikipedia colbert index",
    )
    arg_parser.add_argument(
        "--wikipedia_colbert_checkpoint",
        type=str,
        help="path to the folder containing the wikipedia colbert model checkpoint",
    )
    arg_parser.add_argument(
        "--wikipedia_colbert_collection_path",
        type=str,
        help="path to wikipedia colbert document collection",
    )
    # wikidata arg
    arg_parser.add_argument(
        "--wikidata_llama_model_path",
        type=str,
        help="path to wikidata llama pipeline which is finetuned",
    )
    arg_parser.add_argument(
        "--wikidata_refined_model_name",
        type=str,
        help="path to wikidata refined pipeline which is finetuned",
    )
    arg_parser.add_argument(
        "--wikidata_path_qid_title_map",
        type=str,
    )
    arg_parser.add_argument(
        "--wikidata_path_title_pid_map",
        type=str,
    )


    args, unknown = arg_parser.parse_known_args()

    if args.memory_map.lower() == "true":
        args.memory_map = True
    else:
        args.memory_map = False

    ############## WikiPedia ##############
    with Run().context(RunConfig(experiment=args.wikipedia_colbert_experiment_name, index_root="")):
        utils.globalvar.widipedia_searcher = Searcher(
            index=args.wikipedia_colbert_index_path,
            checkpoint=args.wikipedia_colbert_checkpoint,
            collection=args.wikipedia_colbert_collection_path,
            config=ColBERTConfig(load_index_with_mmap=args.memory_map)
        )

    # warm up Server
    wikipedia_search("Query ColBERT in order to warm it up.", k=5)
    wikipedia_search("Since the first few queries are quite slow", k=5)
    wikipedia_search("Especially with memory_map=True", k=5)

    ############## Wikidata ##############
    wikidata_load(args.wikidata_llama_model_path, args.wikidata_refined_model_name, args.wikidata_path_qid_title_map, args.wikidata_path_title_pid_map)


@atexit.register
def save_and_close():
    utils.globalvar.refinedLinker.save_titles()
    global logger
    logger.info("saved finished!")
    logger.info("Server is shutting down...")
 
    
# used as a way to pass commandline arguments to gunicorn
def gunicorn_app(*args, **kwargs):
    import sys
    sys.argv = ['--gunicorn']
    for k in kwargs:
        sys.argv.append("--" + k)
        sys.argv.append(kwargs[k])
    init()
    return app

if __name__ == "__main__":
    # Run the app with Flask
    init()
    app.run(port=5000, debug=False, use_reloader=False)

