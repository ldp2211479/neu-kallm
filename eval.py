#############################################################################
import argparse
from pathlib import Path
from tqdm import tqdm
import json
import os
from utils.eval_utils import precision_at_1
import utils.globalvar
utils.globalvar.init()

# python eval.py --model llama3:70b --dataset tiq --input outputs/tiq/tiq_output.json --output outputs/tiq/tiq_eval_output.json --use_cot_answer True --mode in

if __name__ == "__main__":
    # read arguments
    parser = argparse.ArgumentParser()
    # parser.add_argument("--model", type=str, default="gpt-3.5-turbo-0613", help="OpenAI API model name")#使用gpt4进行评估
    parser.add_argument("--dataset", type=str, help="Dataset name")
    parser.add_argument("--input", type=str, help="input path")
    parser.add_argument("--output", type=str, help="output path")
    parser.add_argument("--use_cot_answer", type=bool, default=False, help="use cot answer or final answer")
    parser.add_argument("--mode", type=str, default="in", help="the mode of eval, include [in, equal, entity]")

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
    
    tp_p_at_1 = 0.0
    output = []
    exception = 0
    for i in tqdm(range(len(data))):
        data_point = data[i]
        question = dataset.get_question(data_point)
        gold_answers = dataset.get_ground_truth(data_point)
        if not  gold_answers:
            exception += 1
            print("not gold_answers: "+question)
            continue
        answers = dataset.get_cot_answers(data_point) if args.use_cot_answer else dataset.get_final_answers(data_point)
        
        if not answers or (len(answers) == 1 and answers[0] in ["error", "i don't know", "none"]):
            #回答的答案列表为空 或 回答格式错误导致的error 或 回答的是不知道 或 none
            continue
        else:
            p_at_1 = precision_at_1(answers, gold_answers, args.mode)
            tp_p_at_1 += p_at_1
            output.append({"question":question,  "gold_answers": gold_answers, "answers": answers, "p@1":p_at_1})
    
    print("p@1 score", tp_p_at_1 / (len(data)-exception))
    with open(args.output, "w") as f:
        json.dump(output, f)

