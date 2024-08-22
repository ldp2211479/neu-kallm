import argparse
import json
from pathlib import Path

from tqdm import tqdm

# init gloabl variables
# import utils.globalvar
# utils.globalvar.init()

import os
os.environ["OPENAI_API_KEY"] = ''
# os.environ["SERPAPI_KEY"] = '07083bd236bdb1ed80fa702bffce819b0552b27d3e367461493edc10aac82443'


# python run.py --model llama3:70b --dataset --input --output 
if __name__ == "__main__":
    # read arguments
    parser = argparse.ArgumentParser()
    parser.add_argument("--model", type=str, default="gpt-3.5-turbo-0613", help="Base model name(gpt-/text-davinci/llama)")
    parser.add_argument("--dataset", type=str, help="Dataset name(tiq/timequestions)")
    parser.add_argument("--input", type=str, help="Input path")
    parser.add_argument("--output", type=str, help="Output path")

    args = parser.parse_args()
    
    # TODO: add other datasets, as well as a parser for each dataset
    if args.dataset == "tiq":
        from utils.parser.tiq_parser import tiq
        dataset = tiq(args.input)
    elif args.dataset == "timequestions":
        from utils.parser.timequestions_parser import timequestions
        dataset = timequestions(args.input)
    else:
        raise Exception("Invalid dataset name")

    # load data
    Path(args.output).parent.mkdir(exist_ok=True, parents=True)
    data = dataset.get_dataset()
    print('original data length:', len(data))
    #下面这段代码主要防止运行时中断，可以在断点重新运行
    if os.path.exists(args.output):
        print('Found existing outputs, will replace the original data with the existing outputs')
        # read existing outputs
        output_data = json.load(open(args.output, "r"))
        print('Found {} existing outputs'.format(len(output_data)))
        # replace the original data with the existing outputs
        replace_count = 0
        for d in output_data:
            for i in range(len(data)):
                if d['question'] == data[i]['question']:
                    data[i] = d
                    replace_count += 1
                    break
        print('replaced {} existing outputs'.format(replace_count))
        print('Found {} prepared outputs.'.format(len([x["id"] for x in data if 'cot_answer' in x])))#cot的结果
        print('Found {} edited outputs.'.format(len([x["id"] for x in data if 'final_answer' in x])))#cot修正后的结果
        

    for i in tqdm(range(len(data))):
        data_point = data[i]
        print("####################################", data_point["id"], "####################################")
        
        # add filtering to ensure we have not previously produced the results
        if 'cot_answer' not in data_point:
            print("****************** Start stage 1: 先让大模型自己回答一遍 ...")
            print("****** question:\n", dataset.get_question(data_point))
            dataset.get_cot_results(data_point, args.model)
            print("****** CoT answer:\n", data_point["cot_response"])
            data[i] = data_point
            with open(args.output, "w") as f:
                json.dump(data, f)
        if 'knowl_list' not in data_point:
            dataset.retrieve_once(data_point)
            data[i] = data_point
            with open(args.output, "w") as f:
                json.dump(data, f)
        
        # if 'final_answer' not in data_point:
            ##### run stage 2: 对于timequestion 直接基于检索到的依据和原来的回答 给出新的回答 new reason和new answer
        # dataset.get_final_results(data_point,"Q_1",args.model)
        # print("****** Final respond:\n", data_point["correct_qa1_respond"])
        # data[i] = data_point
        # with open(args.output, "w") as f:
        #     json.dump(data, f)
        #     elif args.dataset == "tiq":
        #         data_point = dataset.get_final_results(data_point,"question",args.model)
        #         data[i] = data_point
        #         with open(args.output, "w") as f:
        #             json.dump(data, f)

            # ##### run stage 3: answer consolidation
            # data_point = s3_answer_consolidation(dataset, data_point, args.model)

            # # update the datapoint
            # data[i] = data_point

            # with open(args.output, "w") as f:
            #     json.dump(data, f)

    print("ALL DONE!!")

