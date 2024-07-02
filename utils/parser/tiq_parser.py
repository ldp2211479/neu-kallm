import os
import json
import re
from utils.openai_utils import call_openai_api
from utils.knowl_query import retrieve_knowledge
from utils.other_prompts import tiq_s1_prompt_demonstration, tiq_s2_edit_prompt_demonstration

class tiq:
    def __init__(self):
        # load data
        with open("datasets/tiq/simplified_data.json", "r") as f:
            self.data = json.load(f)
        
        # s1_prompt
        self.s1_prompt_demonstration = tiq_s1_prompt_demonstration
        
        # s2_edit_prompt
        self.s2_edit_prompt_demonstration = tiq_s2_edit_prompt_demonstration
        
    def get_dataset(self):
        return self.data
    
    def get_question(self, data_point):
        return data_point["question"]
    
    def get_ground_truth(self, data_point):
        return data_point["answer"]
    
    def get_s1_prompt(self, question):
        return self.s1_prompt_demonstration + "Question: " + question.strip()

    def get_s2_edit_prompt(self, rationale, rationale_knowledge):
        sentence = self.s2_edit_prompt_demonstration + "Sentence: " + rationale + "\nKnowledge: "
        for source in rationale_knowledge:
            sentence += rationale_knowledge[source] + " "
        sentence += "\nEdited sentence: "
        return sentence
    
    def get_s2_prompt_rationale1(self, question, subquestion_1, edit_rationale_1):
        s2_prompt_rationale1 = self.s1_prompt_demonstration + \
        "\nQuestion: " + question + \
        "\nSub-question 1: " + subquestion_1 + \
        "\nAnswer 1: " + edit_rationale_1 + \
        "\n"
        return s2_prompt_rationale1

    # def get_s3_consolidation_prompt(self, question, rationale_1, rationale_2):
        # return self.s1_prompt_demonstration + "Q: " + question.strip() + "\nA: First, " + rationale_1 + " Second, " + rationale_2 + " The answer is "
    
    def get_cot_results(self, data_point, model, cot_prompt):
        error = 0
        while error < 3:
            print("error: ", error)
            cot_response = call_openai_api(model, cot_prompt, max_tokens=256, temperature=0.7)
        
            if cot_response is not None:
                cot_text_response = cot_response[1]
                # all_cot_text_response = [x["text"].strip() for x in cot_sc_responses[0]["choices"]] # for text models
                
                if "Final answer:" in cot_text_response:
                    cot_answer = cot_text_response.split("Final answer:")[1].strip().lower()
                elif "answer:" in cot_text_response:
                    cot_answer = cot_text_response.split("answer:")[1].strip().lower()
                else:
                    None
                
                patterns = {
                            "Origin Sub-question 1": r"Sub-question 1: (.*?)\n",
                            "Origin Answer 1": r"Answer 1: (.*?)\n",
                            "Origin Constraint": r"the time constraint for Sub-question 2 is: (.*?)\n",
                            "Origin Sub-question 2": r"Sub-question 2: (.*?)\n",
                            "Origin Answer 2": r"Answer 2: (.*?)\n",
                        }
                results = {}
                for key, pattern in patterns.items():
                    match = re.search(pattern, cot_text_response, re.DOTALL)
                    if match:
                        results[key] = match.group(1).strip()
                    else:
                        error += 1
                        continue
            else:
                raise Exception("Stage 1: OpenAI API call failed")
            
            # store the results
            data_point["cot_response"] = cot_text_response
            data_point["cot_answer"] = cot_answer
            data_point["cot_rationales"] = [results['Origin Answer 1'], results['Origin Answer 2']]
            data_point["cot_subquestions"] = [results['Origin Sub-question 1'], results['Origin Sub-question 1']]
            data_point['cot_constraint'] = results['Origin Constraint']
            return data_point
    
    def update_rationales_step_by_step(self, model, data_point):
        question = data_point["question"].strip()
        rationale_1, rationale_2 = data_point["cot_rationales"]
        Subquestion_1, Subquestion_2 = data_point["cot_subquestions"]
        constraint = data_point['constraint']

        print("****** Editing Rationale 1 ******")
        # retrieve knowledge for rationale 1 first
        rationale_1_knowl = retrieve_knowledge(rationale_1, data_point)

        # edit rationale 1 based on rationale 1_knowl
        s2_edit_prompt_rationale_1 = self.get_s2_edit_prompt(rationale_1, rationale_1_knowl)
        # print(s2_edit_prompt_rationale_1)
        edited_rationale_1 = call_openai_api(model, s2_edit_prompt_rationale_1, max_tokens=256, temperature=0, n=1)[1].strip()
        print("*** Original rationale 1:", rationale_1)
        print("*** Edited rationale 1:", edited_rationale_1)
        
        print("****** Editing Rationale 2 ******")
        # generate rationale 2 using edited rationale 1
        new_rationale_2_prompt = self.get_s2_prompt_rationale1(question, Subquestion_1, edited_rationale_1)
        # print(new_rationale_2_prompt)
        new_rationale_2 = call_openai_api(model, new_rationale_2_prompt, max_tokens=256, temperature=0, n=1)[1].strip()
        # get the rationale, remove the answer sentence
        new_rationale_2 = new_rationale_2.split("The answer is")[0].strip()
        print("*** New rationale 2:", new_rationale_2)
        
        data_point["rationale_1_knowl"] = rationale_1_knowl
        data_point["edited_rationale_1"] = edited_rationale_1
        data_point["new_rationale_2"] = new_rationale_2

        # retreive knowledge for rationale 2
        rationale_2_knowl = retrieve_knowledge(new_rationale_2, data_point)

        # edit rationale 2 based on rationale 2_knowl
        s2_edit_prompt_rationale_2 = self.get_s2_edit_prompt(new_rationale_2, rationale_2_knowl)
        # print(s2_edit_prompt_rationale_2)
        edited_rationale_2 = call_openai_api(model, s2_edit_prompt_rationale_2, max_tokens=256, temperature=0, n=1)[1].strip()
        print("*** Original rationale 2:", rationale_2)
        print("*** Edited rationale 2:", edited_rationale_2)

        # store the results
        data_point["rationale_2_knowl"] = rationale_2_knowl
        data_point["edited_rationale_2"] = edited_rationale_2

        return data_point

        
    # def update_rationales_at_once(self, model, data_point):
    #     domains = data_point["s1_domains"]
    #     rationales = [x.strip() for x in data_point["cot_sc_rationales"]]
    #     rationale_1 = rationales[0]
    #     rationale_2 = rationales[1]

    #     print("****** Editing Rationale 1 ...")
    #     # retrieve knowledge for rationale 1 first
    #     rationale_1_knowl = retrieve_knowledge(domains, rationale_1, data_point)

    #     # edit rationale 1 based on rationale 1_knowl
    #     s2_edit_prompt_rationale_1 = self.get_s2_edit_prompt(rationale_1, rationale_1_knowl)
    #     # print(s2_edit_prompt_rationale_1)
    #     edited_rationale_1 = call_openai_api(model, s2_edit_prompt_rationale_1, max_tokens=256, temperature=0, n=1)[1].strip()
    #     print("*** Original rationale 1:", rationale_1)
    #     print("*** Edited rationale 1:", edited_rationale_1)
        
    #     print("****** Editing Rationale 2 ...")        
        
    #     data_point["rationale_1_knowl"] = rationale_1_knowl
    #     data_point["edited_rationale_1"] = edited_rationale_1

    #     # retreive knowledge for rationale 2
    #     rationale_2_knowl = retrieve_knowledge(domains, rationale_2, data_point)

    #     # edit rationale 2 based on rationale 2_knowl
    #     s2_edit_prompt_rationale_2 = self.get_s2_edit_prompt(rationale_2, rationale_2_knowl)
    #     # print(s2_edit_prompt_rationale_2)
    #     edited_rationale_2 = call_openai_api(model, s2_edit_prompt_rationale_2, max_tokens=256, temperature=0, n=1)[1].strip()
    #     print("*** Original rationale 2:", rationale_2)
    #     print("*** Edited rationale 2:", edited_rationale_2)

    #     # store the results
    #     data_point["rationale_2_knowl"] = rationale_2_knowl
    #     data_point["edited_rationale_2"] = edited_rationale_2

    #     return data_point

    
    def get_final_answer(self, model, data_point):
        print("****** Edited rationales: ", "First, " + data_point["edited_rationale_1"] + " Second, " + data_point["edited_rationale_2"])
        s3_answer_consolidation_prompt = self.get_s3_consolidation_prompt(data_point["question"], data_point["edited_rationale_1"], data_point["edited_rationale_2"])
        final_answer = call_openai_api(model, s3_answer_consolidation_prompt, max_tokens=256, temperature=0, n=1)[1].strip()
        data_point["final_answer"] = final_answer
        print("****** Final answer:", final_answer)
        print("****** Original answer:", data_point["cot_sc_answer"])
        print("****** Gold answer:", data_point["answer"])
        return data_point
