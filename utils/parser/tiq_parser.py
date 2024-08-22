import os
import json
import re
import time
from utils.openai_utils import call_openai_api
from utils.knowl_query import retrieve_knowledge
from utils.other_prompts import tiq_cot_prompt_demonstration, tiq_correct_1_prompt_demonstration,tiq_correct_2_prompt_demonstration

class tiq:
    def __init__(self, dataset_path):
        # load data
        with open(dataset_path, "r") as f:
            self.data = json.load(f)
        
        self.cot_prompt_demonstration = tiq_cot_prompt_demonstration
        
        self.tiq_correct_1_prompt_demonstration = tiq_correct_1_prompt_demonstration

        self.tiq_correct_2_prompt_demonstration = tiq_correct_2_prompt_demonstration

        
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
                #可能会出现 完全没有Final answer 一般是没看懂 此时Final answer为error
                #Final answer 为none的情况
                #通过prompt的设置 Final answer 为i dont know的情况
                if "Final answer:" in cot_text_response:#用answer的话 我怕它在子问题上 给一个 answer:
                    cot_answer = cot_text_response.split("Final answer:")[1].strip().lower() #小写用于答案对比
                else:
                    raise Exception("Stage 1: Incorrect answer format")
                patterns = {
                            "Origin Sub-question 1": r"Sub-question 1: (.*?)\n",
                            "Origin Answer 1": r"Answer 1: (.*?)\n",
                            "Origin Constraint": r"for Sub-question 2 is: (.*?)\n",
                            "Origin Sub-question 2": r"Sub-question 2: (.*?)\n",
                            "Origin Answer 2": r"Answer 2: (.*?)\n",
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
            data_point['cot_answer'] = "error" #保证cot_answer都是小写
            return data_point
            

        # store the results
        data_point["cot_response"] = cot_text_response
        data_point["cot_answer"] = cot_answer
        data_point["cot_qa1"] = {
            "q":results['Origin Sub-question 1'],
            "a":results['Origin Answer 1']
        }
        data_point['cot_constraint'] = results['Origin Constraint']
        data_point["cot_qa2"] = {
            "q":results['Origin Sub-question 2'],
            "a":results['Origin Answer 2']
        }
        return data_point
    

    def get_ground_truth(self, data_point):
        #"answer": [
        #     {
        #         "id": "Q10966671",
        #         "label": "Wikipedia:English pronunciation respelling key",
        #         "wikipedia": "https://en.wikipedia.org/wiki/Help:Pronunciation_respelling_key"
        #     }
        # ],
        return data_point["answer"]

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

    def retrieve_once(self, data_point):
        if "cot_qa1" not in data_point:
            return
        subquestion_1 = data_point["cot_qa1"]["q"] 
        answer_1 = data_point["cot_qa1"]["a"]
        #三种检索的策略
        #1.仅用子问题检索
        subquestion_1_knowl = retrieve_knowledge(subquestion_1, "none")

        #2.用子问题拼接答案检索
        subquestion_1_answer_1_knowl = retrieve_knowledge(subquestion_1 + " "+ answer_1, "none")

        #2.仅用子问题的回答检索
        answer_1_knowl = retrieve_knowledge(answer_1, "none")

        data_point['knowl_list'] = {'Q_1': subquestion_1_knowl, \
                                              'Q_1+A_1': subquestion_1_answer_1_knowl, \
                                              'A_1': answer_1_knowl, \
                                    }
        return data_point
    
    def retrieve_twice(self, data_point):
        subquestion_2,answer_2 = data_point["new_cot_qa2"]
        #三种检索的策略
        #1.仅用子问题检索
        subquestion_2_knowl = retrieve_knowledge(subquestion_2, "none")

        #2.用子问题拼接答案检索
        subquestion_2_answer_2_knowl = retrieve_knowledge(subquestion_2 + " "+ answer_2, "none")

        #2.仅用子问题的回答检索
        answer_2_knowl = retrieve_knowledge(answer_2, "none")

        # 如果 'knowl_list' 已经存在，则向其中添加新内容，否则初始化为一个空字典
        if 'knowl_list' not in data_point:
            data_point['knowl_list'] = {}

        # 添加新的检索结果到已有的 'knowl_list'
        data_point['knowl_list'].update({
            'subquestion_2': subquestion_2_knowl,
            'subquestion_2+answer_2': subquestion_2_answer_2_knowl,
            'answer_2': answer_2_knowl,
        })
        return data_point

    # 两个correct过程非常类似,可以抽象出来实现链式的效果 

    def correct_once(self,data_point,retrieval_base,model):
        try:
            # self.retrieve_once(data_point)
            if "cot_qa1" not in data_point:
                print("****** qa1 missing data:\n", data_point["question"])
                return
            correct_1_prompt = self.tiq_correct_1_prompt_demonstration.format(
                sub_question_1=data_point["cot_qa1"]["q"], answer_1=data_point["cot_qa1"]["a"],knowl_wikipedia_list = data_point["knowl_list"][retrieval_base]["wikipedia"])
            # print(correct_1_prompt)
            correct_1_response = call_openai_api(model, correct_1_prompt, max_tokens=256, temperature=0)
            print(correct_1_response[0])
            if correct_1_response is not None:
                correct_1_text_response = correct_1_response[1]
                patterns = {
                    "New Answer": r"New answer: (.*?)\n",
                    "Explanation": r"Explanation: (.*?)\n"
                }
                results = {}
                for key in patterns.keys():
                    match = re.search(patterns[key], correct_1_text_response, re.DOTALL)
                    if match:
                        results[key] = match.group(1).strip()
                    else:
                        raise Exception("Stage 1: Incorrect answer format")
            else:
                raise Exception("Stage 1: language model API call failed")
        except Exception as e:
            print('Retry due to:', e)
            if correct_1_response is not None:
                data_point["correct_qa1_respond"] = correct_1_response[1]
            else: data_point["correct_qa1_respond"] = "None"
            data_point["correct_qa1_explanation"] = "None"
            data_point["correct_qa1"] = {
                "q":data_point["cot_qa1"]["q"],
                "a":"error"
            }
            
            return data_point
        data_point["correct_qa1_respond"] = correct_1_response[1]
        data_point["correct_qa1_explanation"] = results["Explanation"]
        data_point["correct_qa1"] = {
            "q":data_point["cot_qa1"]["q"],
            "a":results["New Answer"]
        }
        
        return data_point

    def correct_twice(self,data_point,retrieval_base,model):
        try:
            self.retrieve_twice(data_point)
            correct_2_prompt = self.tiq_correct_2_prompt_demonstration.format(
            question=data_point["question"], sub_question_1=data_point['correct_qa1'][0], answer_1=data_point["correct_qa1"][1],new_cot_constraint=data_point["new_cot_constraint"],sub_question_2=data_point["new_cot_qa2"]["q"],answer_2=data_point["new_cot_qa2"]["a"],knowl_wikipedia_list = data_point["knowl_list"][retrieval_base]["wikipedia"])
            correct_2_response = call_openai_api(model, correct_2_prompt, max_tokens=256, temperature=0)
            
            if correct_2_response is not None:
                correct_2_answer = correct_2_response[1].strip().lower()
            else:
                raise Exception("Stage 1: language model API call failed")
        except Exception as e:
            print('Retry due to:', e)
            data_point['correct_1_answer'] = "error"
            return data_point
        # store the results
        data_point["correct_2_answer"] = correct_2_answer
        return data_point

    def get_final_results(self, data_point, retrieval_base, model):
        self.correct_once(data_point,retrieval_base,model)
        # try:
        #     cot_prompt = self.s1_prompt_demonstration + "Question: " + data_point["question"].strip() + \
        #             "Sub-question 1: " + data_point["correct_qa1"]["q"] + \
        #         "Answer 1: " + data_point["correct_qa1"]["a"]
        #     cot_response = call_openai_api(model, cot_prompt, max_tokens=256, temperature=0)
        #     cot_text_response = cot_response[1]
        #     if "Final answer:" in cot_text_response:#用answer的话 我怕它在子问题上 给一个 answer:
        #         cot_answer = cot_text_response.split("Final answer:")[1].strip().lower() #小写用于答案对比
        #     patterns = {
        #                     "New Constraint": r"for Sub-question 2 is: (.*?)\n",
        #                     "New Sub-question 2": r"Sub-question 2: (.*?)\n",
        #                     "New Answer 2": r"Answer 2: (.*?)\n"
        #                 }

        #     results = {}
        #     for key in patterns.keys():
        #         match = re.search(patterns[key], cot_text_response, re.DOTALL)
        #         if match:
        #             results[key] = match.group(1).strip()
        #         else:
        #             raise Exception("Stage 1: Incorrect answer format")
        #     else:
        #         raise Exception("Stage 1: language model API call failed")
        # except Exception as e:
        #     print('Retry due to:', e)
        #     if cot_response is not None:
        #         data_point['new_cot_response'] = cot_response[1]
        #     else: data_point['new_cot_response'] = "None"
        #     data_point['new_cot_answer'] = "error" #保证cot_answer都是小写
        #     ###############################
        # data_point["new_cot_response"] = cot_text_response
        # data_point["new_cot_answer"] = cot_answer
        # data_point['new_cot_constraint'] = results['New Constraint']
        # data_point["new_cot_qa2"] = {
        #     "q":results['New Sub-question 2'],
        #     "a":results['New Answer 2']
        # }
        # self.correct_twice(data_point,retrieval_base,model)
        
        

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
    # def get_s2_edit_prompt(self, rationale, rationale_knowledge):
    #     sentence = self.s2_edit_prompt_demonstration + "Sentence: " + rationale + "\nKnowledge: "
    #     for source in rationale_knowledge:
    #         sentence += rationale_knowledge[source] + " "
    #     sentence += "\nEdited sentence: "
    #     return sentence
    
    # def get_s2_prompt_rationale1(self, question, subquestion_1, edit_rationale_1):
    #     s2_prompt_rationale1 = self.s1_prompt_demonstration + \
    #     "\nQuestion: " + question + \
    #     "\nSub-question 1: " + subquestion_1 + \
    #     "\nAnswer 1: " + edit_rationale_1 + \
    #     "\n"
    #     return s2_prompt_rationale1

    # def get_s3_consolidation_prompt(self, question, subquestion_1, subquestion_2, rationale_1, rationale_2, constraint):
    #     s3_consolidation_prompt = self.s1_prompt_demonstration + \
    #     "\nQuestion: " + question + \
    #     "\nSub-question 1: " + subquestion_1 + \
    #     "\nAnswer 1: " + rationale_1 + \
    #     "\nAccording to Answer 1, the time of Subquestion 1 is: " + constraint + \
    #     "\nSub-question 2: " + subquestion_2 + \
    #     "\nAnswer 2: " + rationale_2 # + \
    #     # "\nFinal answer: "
    #     return s3_consolidation_prompt
    
    # def update_rationales_step_by_step(self, model, data_point):
    #     question = data_point["question"].strip()
    #     rationale_1, rationale_2 = data_point["cot_rationales"]
    #     subquestion_1, subquestion_2 = data_point["cot_subquestions"]
    #     constraint = data_point['cot_constraint']

    #     if "new_rationale_2" in data_point:
    #         new_rationale_2 = data_point["new_rationale_2"]
    #     else:
    #         print("****** Editing Rationale 1 ******")
    #         # retrieve knowledge for rationale 1 first
    #         rationale_1_knowl = retrieve_knowledge(subquestion_1, "none")

    #         # edit rationale 1 based on rationale 1_knowl
    #         s2_edit_prompt_rationale_1 = self.get_s2_edit_prompt(rationale_1, rationale_1_knowl)
    #         # print(s2_edit_prompt_rationale_1)
    #         edited_rationale_1 = call_openai_api(model, s2_edit_prompt_rationale_1, max_tokens=256, temperature=0, n=1)[1].strip()
    #         print("*** Original rationale 1:", rationale_1)
    #         print("*** Edited rationale 1:", edited_rationale_1)

    #     #-------------------------------------------------  get new rationale2 ------------------------------------------------#       
            
    #         print("****** Get New Rationale 2 ******")
    #         # generate rationale 2 using edited rationale 1
    #         new_rationale_2_prompt = self.get_s2_prompt_rationale1(question, subquestion_1, edited_rationale_1)
    #         # print(new_rationale_2_prompt)
    #         new_rationale_2_response = call_openai_api(model, new_rationale_2_prompt, max_tokens=256, temperature=0, n=1)[1].strip()
    #         # get the rationale, remove the answer sentence
    #         match = re.search(r"for Sub-question 2 is: (.*?)\n", new_rationale_2_response, re.DOTALL)
    #         if match:
    #             new_constraint = match.group(1).strip()
    #         else:
    #             new_constraint = constraint
    #         match = re.search(r"Sub-question 2: (.*?)\n", new_rationale_2_response, re.DOTALL)
    #         if match:
    #             new_subquestion_2 = match.group(1).strip()
    #         else:
    #             new_subquestion_2 = subquestion_2
    #         match = re.search(r"Answer 2: (.*?)\n", new_rationale_2_response, re.DOTALL)
    #         if match:
    #             new_rationale_2 = match.group(1).strip()
    #         else:
    #             new_rationale_2 = rationale_2
    #             print("-----------------------ERROR-----------------------------")
    #             print(new_rationale_2_response)
    #             print('---------------------------------------------------------')
            
    #         print("*** New constraint 2:", new_constraint)
    #         print("*** New sub-question 2:", new_subquestion_2)
    #         print("*** New rationale 2:", new_rationale_2)
            
    #         data_point["rationale_1_knowl"] = rationale_1_knowl
    #         data_point["edited_rationale_1"] = edited_rationale_1
    #         data_point["new_subquestion_2"] = new_subquestion_2
    #         data_point["new_constraint"] = new_constraint
    #         data_point["new_rationale_2"] = new_1_2

    # #-------------------------------------------------  edit rationale2 ------------------------------------------------#
        
    #     print("****** Edit Rationale 2 ******")
    #     # retreive knowledge for rationale 2
    #     rationale_2_knowl = retrieve_knowledge(new_subquestion_2, new_constraint)

    #     # edit rationale 2 based on rationale 2_knowl
    #     s2_edit_prompt_rationale_2 = self.get_s2_edit_prompt(new_rationale_2, rationale_2_knowl)
    #     # print(s2_edit_prompt_rationale_2)
    #     edited_rationale_2 = call_openai_api(model, s2_edit_prompt_rationale_2, max_tokens=256, temperature=0, n=1)[1].strip()
    #     print("*** Original rationale 2:", rationale_2)
    #     print("*** Edited rationale 2:", edited_rationale_2)

    #     # store the results
    #     data_point["rationale_2_knowl"] = rationale_2_knowl
    #     data_point["edited_rationale_2"] = edited_rationale_2

    #     return data_point



    
    # def get_final_answer(self, model, data_point):
    #     print("****** Get Final Answer ******")
    #     question = data_point["question"].strip()
    #     rationale_1 = data_point["edited_rationale_1"]
    #     rationale_2 = data_point["edited_rationale_2"]
    #     subquestion_1 = data_point["cot_subquestions"][0]
    #     subquestion_2 = data_point["new_subquestion_2"]
    #     constraint = data_point['new_constraint']
    #     error = 0
    #     while error < 10:
    #         s3_answer_consolidation_prompt = self.get_s3_consolidation_prompt(question, subquestion_1, subquestion_2, rationale_1, rationale_2, constraint)
    #         final_answer = call_openai_api(model, s3_answer_consolidation_prompt, max_tokens=256, temperature=0, n=1)[1].strip()
    #         if "Final Answer" in final_answer:
    #             data_point["final_answer"] = final_answer.split("Final answer:")[1].strip().lower()
    #             continue
    #         else:
    #             error += 1
    #             print("final answer error: ", error)
    #     if error == 10:
    #         data_point["final_answer"] = final_answer
    #     print("****** Final answer:", final_answer)
    #     print("****** Original answer:", data_point["cot_answer"])
    #     print("****** Gold answer:", data_point["answer"][0]['label'])
    #     return data_point
