import os
import json
import re
import time
from utils.openai_utils import call_openai_api
from utils.knowl_query import retrieve_knowledge
from utils.other_prompts import timequestions_cot_prompt_demonstration,timequestions_final_prompt_demonstration

class timequestions:
    def __init__(self, dataset_path):
        # load data
        with open(dataset_path, "r") as f:
            self.data = json.load(f)
        # s1_prompt
        self.cot_prompt_demonstration = timequestions_cot_prompt_demonstration

        self.final_prompt_demonstration = timequestions_final_prompt_demonstration
    
    def get_dataset(self):
        return self.data
    
    def get_question(self, data_point):
        return data_point["question"]

    def get_cot_results(self, data_point, model):#这里注意提前把答案小写
        try:
            cot_prompt = self.cot_prompt_demonstration + "Question: " + data_point["question"].strip()
            cot_response = call_openai_api(model, cot_prompt, max_tokens=256, temperature=0)
            
            if cot_response is not None:
                cot_text_response = cot_response[1]
                #可能会出现 格式错误 一般是没看懂 此时Final answer为error
                #Final answer 为none的情况
                #通过prompt的设置 Final answer 为i dont know的情况
                if "Final answer:" in cot_text_response:#用answer的话 我怕它在子问题上 给一个 answer:
                    cot_answer = cot_text_response.split("Final answer:")[1].strip().lower()
                else:
                    raise Exception("Stage 1: Incorrect answer format")
                    
                patterns = {
                            "Origin Reason": r"Reason: (.*?)\n"
                        }

                results = {}
                for key in patterns.keys():
                    match = re.search(patterns[key], cot_text_response, re.DOTALL)
                    if match:
                        results[key] = match.group(1).strip()
                    else:
                        raise Exception("Stage 1: Incorrect answer format")
            else:
                raise Exception("Stage 1: language model API call failed")
        except Exception as e:
            print('Retry due to:', e)
            if cot_response is not None:
                data_point['cot_response'] = cot_response[1]
            else: data_point['cot_response'] = "None"
            data_point['cot_reason'] = ""
            data_point['cot_answer'] = "error"
            return data_point
            

        # store the results
        data_point["cot_response"] = cot_text_response
        data_point['cot_reason'] = results['Origin Reason']
        data_point["cot_answer"] = cot_answer
        return data_point

    #评估
    def get_ground_truth(self, data_point):
        # "answer": [
        #     {
        #         "answertype": "Entity",
        #         "wikidataqid": "Q7072015", #用于基于实体链接的评估
        #         "wikidatalabel": "O-Lan Jones", #用于基于字符串的评估
        #         "wikipediaurl": "https://en.wikipedia.org/wiki/O-Lan_Jones"
        #     }
        # ],
        # "answer": [
        #     {
        #         "answertype": "Value",
        #         "answerargument": "1485-12-16T00:00:00Z" #用于基于字符串的评估 （日期需要做一些处理）
        #     },
        #     {
        #         "answertype": "Value",
        #         "answerargument": "21" #用于基于字符串的评估
        #     }
        # ],
        modified_answer = []
        for item in data_point["answer"]:
            if item["answertype"] == "Entity":
                modified_item = {
                    "answertype": item["answertype"],
                    "id": item["wikidataqid"], #用于基于实体链接的评估
                    "label": item["wikidatalabel"], #用于基于字符串的评估
                    "wikipediaurl": item["wikipediaurl"]
                }
            else:
                modified_item = {
                    "answertype": item["answertype"],
                    "label": item["answerargument"], #用于基于字符串的评估
                }
            modified_answer.append(modified_item)
        return modified_answer

    def get_cot_answers(self, data_point):
        if "cot_answer" in data_point:
            # 分割答案，去除前后空白，并过滤空字符串
            return [answer.strip() for answer in data_point["cot_answer"].split(',') if answer.strip()]
        else:
            return []

    def get_final_answers(self, data_point):
        if "final_answer" in data_point:
            return [answer.strip() for answer in data_point["final_answer"].split(',') if answer.strip()]
        else:
            return []
    ###


    def retrieve_once(self, data_point):
        question = data_point["question"]
        reason = data_point["cot_reason"]
        #三种检索的策略
        #1.仅用问题检索
        question_knowl = retrieve_knowledge(question, "none")

        #2.用子问题拼接答案检索
        question_reason_knowl = retrieve_knowledge(question + "? "+ reason, "none")#timequestion的问题缺个?

        #2.仅用子问题的回答检索
        reason_knowl = retrieve_knowledge(reason, "none")   
        data_point['knowl_list'] = {'Q': question_knowl, \
                                              'Q+R': question_reason_knowl, \
                                              'R': reason_knowl, \
                                    }
        return data_point

    def get_final_results(self, data_point, retrieval_base, model):
        try:
            # self.retrieve_once(data_point)
            final_prompt = self.final_prompt_demonstration.format(
                question=data_point["question"], cot_reason=data_point['cot_reason'], cot_answer=data_point["cot_answer"],knowl_wikipedia_list = data_point["knowl_list"][retrieval_base]["wikipedia"])
            final_response = call_openai_api(model, final_prompt, max_tokens=256, temperature=0.3)
            
            if final_response is not None:
                final_text_response = final_response[1]
                #可能会出现 格式错误 此时Final answer为error
                #Final answer 为none的情况
                #通过prompt的设置 Final answer 为i dont know的情况
                if "New final answer:" in final_text_response:#用answer的话 我怕它在子问题上 给一个 answer:
                    final_answer = final_text_response.split("New final answer:")[1].strip().lower()
                else:
                    raise Exception("Stage 1: Incorrect answer format")
                    
                patterns = {
                            "New Reason": r"New reason: (.*?)\n"
                }

                results = {}
                for key in patterns.keys():
                    match = re.search(patterns[key], final_text_response, re.DOTALL)
                    if match:
                        results[key] = match.group(1).strip()
                    else:
                        raise Exception("Stage 1: Incorrect answer format")
            else:
                raise Exception("Stage 1: language model API call failed")
        except Exception as e:
            print('Retry due to:', e)
            if final_response is not None:
                data_point['final_response'] = final_response[1]
            else: data_point['final_response'] = "None"
            data_point['final_reason'] = "None"
            data_point['final_answer'] = "error"
            return data_point
        # store the results
        data_point["final_response"] = final_response[1]
        data_point['final_reason'] = results['New Reason']
        data_point["final_answer"] = final_answer
        return data_point
        
        
    # def get_knowl_list(self, data_point):
    #     if "rationale_1_knowl" in data_point:
    #         knowl_1_wikipedia = data_point["rationale_1_knowl"]['wikipedia'].strip()
    #         knowl_1_wikipedia_list = [i.strip() for i in knowl_1_wikipedia.split('|')]
    #         # knowl_1_wikidata = data_point["rationale_1_knowl"]['wikidata'].strip()
    #     else:
    #         return None
    #     if "rationale_2_knowl" in data_point:
    #         knowl_2_wikipedia = data_point["rationale_2_knowl"]['wikipedia'].strip()
    #         knowl_2_wikipedia_list = [i.strip() for i in knowl_2_wikipedia.split('|')]
    #         # knowl_2_wikidata = data_point["rationale_2_knowl"]['wikidata'].strip()
    #     else:
    #         return None
    #     # return {  "know_1": {"wikipedia": knowl_1_wikipedia_list, "wikidata": knowl_1_wikidata} , \
    #     #           "know_2": {"wikipedia": knowl_2_wikipedia_list, "wikidata": knowl_2_wikidata} 
    #     #        }
    #     return {  "know_1": {"wikipedia": knowl_1_wikipedia_list} , \
    #               "know_2": {"wikipedia": knowl_2_wikipedia_list} 
    #            }


    

    # def get_final_answer(self, data_point):
    #     print("****** Get Final Answer ******")
    #     reason = data_point["cot_reason"]#TODO 再测一下用question单独检索 以及question拼接reason检索
    #     rationale_1_knowl_reason, knowl_wikipedia_reason_list = retrieve_knowledge(reason, "none")      
    #     data_point['knowl_wikipedia_list'] = knowl_wikipedia_reason_list
    #     return data_point




