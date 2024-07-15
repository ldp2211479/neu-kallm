# # wikidata
# from typing import Optional, Any
# import transformers
# import torch
# from peft import PeftModel
# from transformers.utils import is_accelerate_available, is_bitsandbytes_available
# from transformers import (
#     AutoTokenizer,
#     AutoModelForCausalLM,
#     GenerationConfig,
#     pipeline,
# )
# import json
# import requests
# from utils.retrieval.linking import test_linking
# import re
# from SPARQLWrapper import SPARQLWrapper, JSON
# from tqdm.notebook import tqdm
# import utils.globalvar

# # prompt = """
# # ### Instruction: Generate a correct SPARQL query that returns the answer of the following question. Generate four incorrect SPARQL queries of different types.
# # ### Input: 
# # ### Output: """

# def formatting_prompts_func(ipt):
#     text = f"### Instruction: Generate a correct SPARQL query that returns the answer of the following question. Generate four incorrect SPARQL queries of different types.\n### Input: {ipt}\n### Output: "
#     return text

# ### Query Generation ###############################################
# def llama_pipeline(prompt):
#     # base_model = "./model/Meta-Llama-3-8B-hf"
#     # peft_model = "./model/Meta-Llama-3-8B-hf-sparql-contrastive"
    
#     # # load the model only once
#     # if utils.globalvar.model is None:
#     #     utils.globalvar.model = AutoModelForCausalLM.from_pretrained(
#     #         base_model,
#     #         use_safetensors=True,
#     #         torch_dtype=torch.float16,
#     #         load_in_8bit=True,
#     #         device_map="auto"
#     #     )
#     #     utils.globalvar.model = PeftModel.from_pretrained(utils.globalvar.model, peft_model)
#     #     # utils.globalvar.model = PeftModel.from_pretrained(utils.globalvar.model, peft_model).merge_and_unload()
#     #     utils.globalvar.tokenizer = AutoTokenizer.from_pretrained(base_model)
    
#     # print("Model loaded...")
#     # pipeline = transformers.pipeline(
#     #     "text-generation",
#     #     model=utils.globalvar.model,
#     #     tokenizer=utils.globalvar.tokenizer,
#     #     torch_dtype=torch.float16,
#     #     device_map="auto",
#     # )

#     # sequences = pipeline(
#     #     prompt,
#     #     max_length=256,
#     #     #do_sample=False,
#     #     do_sample=True,
#     #     top_k=10,
#     #     num_return_sequences=1,
#     #     eos_token_id=utils.globalvar.tokenizer.eos_token_id,
#     #     # pad_token_id = pipeline.tokenizer.eos_token_id
#     # )
    
#     # return sequences[0]["generated_text"].strip()
#     merged_model = "./model/Meta-Llama-3-8B-hf-merged"
    
#     # load the model only once
#     if utils.globalvar.model is None:
#         utils.globalvar.model = AutoModelForCausalLM.from_pretrained(
#             merged_model,
#             use_safetensors=True,
#             torch_dtype=torch.float16,
#             # load_in_8bit=True,
#             device_map="auto"
#         )
#         utils.globalvar.tokenizer = AutoTokenizer.from_pretrained(merged_model)
#     print("Model loaded...")
#     pipeline = transformers.pipeline(
#         "text-generation",
#         model=utils.globalvar.model,
#         tokenizer=utils.globalvar.tokenizer,
#         torch_dtype=torch.float16,
#         device_map="auto",
#     )

#     sequences = pipeline(
#         prompt,
#         max_length=256,
#         do_sample=True,
#         top_k=10,
#         num_return_sequences=1,
#         eos_token_id=utils.globalvar.tokenizer.eos_token_id,
#     )
#     return sequences[0]["generated_text"].strip()

# ###############################################


# #### Entity Linking ###############################################
# def get_property_code(property_name):
#     # Wikidata API endpoint
#     url = f"https://www.wikidata.org/w/api.php?action=wbsearchentities&format=json&language=en&type=property&search={property_name}"

#     try:
#         # Send a GET request to the Wikidata API
#         response = requests.get(url)
#         data = response.json()

#         # Check if a matching property is found
#         if "search" in data and data["search"]:
#             # Retrieve the code of the first matching property
#             code = data["search"][0]["id"]
#             return code
#         else:
#             return None
#     except requests.exceptions.RequestException as e:
#         # print(f"An error occurred: {e}")
#         return None


# # def get_elements(string):
# #     slashes = [i for i in range(len(string)) if string[i] == '/']
# #     if len(slashes) % 2 == 0:
# #         entities = []
# #         relations = []
# #         for i in range(int(len(slashes)/2)):
# #             start = slashes[i * 2] + 1
# #             end = slashes[i * 2 + 1]
            
# #             if string[start - 3 : start - 2] == 'd':
# #                 entities.append(string[start:end])
# #             elif string[start - 3 : start - 2] == 't':
# #                 relations.append(string[start:end])
# #             else:
# #                 None
# #         return (entities, relations)
# #     else:
# #         return None

# def get_elements(query_correct):
#     slashes = [i for i in range(len(query_correct)) if query_correct[i] == '/']
#     if len(slashes) % 2 == 0:
#         entities = []
#         relations = []
#         for i in range(int(len(slashes)/2)):
#             start = slashes[i * 2] + 1
#             end = slashes[i * 2 + 1]
            
#             prefix = query_correct[slashes[i * 2] - 3:slashes[i * 2]]
#             if re.search(r'wd:|d/', prefix):                   # wd
#                 entities.append(query_correct[start:end])
#             elif re.search(r'p:|ps:|pq:|dt:', prefix):         # wdt p ps pq
#                 relations.append(query_correct[start:end])
#             else:
#                 None
#         return (list(set(entities)), list(set(relations)))
#     else:
#         return None



# def post_process_query(string):
#     query1 = string.split('Correct query:')[-1].strip().split('Incorrect query 1')[0].strip()
#     print("Origin query:", query1)
#     get_elements_results = get_elements(query1)
#     if get_elements_results is not None:
#         entity_list, relation_list = get_elements_results[0], get_elements_results[1]
#     else:
#         entity_list = []
#         relation_list = []
#     print("elements:", entity_list)
#     print("relations", relation_list)
#     # get ids for entities and relations, and then replace in the string
#     # print("Processing entity linkings...")
#     for i in range(len(entity_list)):
#         tmp_entity = test_linking(entity_list[i])
#         try:
#             # tmp_link = tmp_entity[0]['links'][0]
#             tmp_link = tmp_entity[0]
#             query1 = query1.replace(entity_list[i], tmp_link)
#         except:
#             None
#     # print("Processing relation linkings...")
#     for i in range(len(relation_list)):
#         tmp_relations = get_property_code(relation_list[i].lower())
#         try:
#             query1 = query1.replace(relation_list[i], tmp_relations)
#         except:
#             None
            
#     query1 = query1.replace('/', '')
    
#     return query1


# def query_wiki(query):
#   endpoint_url = "https://query.wikidata.org/sparql"

#   # Create a SPARQLWrapper object and set the endpoint URL
#   sparql = SPARQLWrapper(endpoint_url)

#   # Set the SPARQL query
#   sparql.setQuery(query)

#   # Set the returned format to JSON
#   sparql.setReturnFormat(JSON)

#   # Execute the query and fetch the results
#   results = sparql.query().convert()

#   # Process the results
#   item_labels = []
#   for result in results["results"]["bindings"]:
#       item_labels.append(result)
      
#   return item_labels


# def get_entity_name(entity_id):
#     url = f"https://www.wikidata.org/w/api.php?action=wbgetentities&format=json&ids={entity_id}"
#     response = requests.get(url)
#     data = response.json()

#     # Extract the entity name
#     entity = data["entities"][entity_id]
#     entity_name = entity["labels"]["en"]["value"]  # Assuming you want the English name

#     return entity_name


# def get_wiki_info(list_of_info):
#     info_list = []
#     for i in range(len(list_of_info)):
#         tmp_info = list_of_info[i]
        
#         if len(tmp_info) == 1:
#             if 'obj' in tmp_info:
#                 # info_list.append(tmp_info['obj']['value'])
#                 tmp_value = tmp_info['obj']['value']
#             elif 'value' in tmp_info:
#                 # info_list.append(tmp_info['value']['value'])
#                 tmp_value = tmp_info['value']['value']
#             elif 'answer' in tmp_info:
#                 # info_list.append(get_entity_name(tmp_info['answer']['value'].split('/')[-1]))
#                 tmp_value = tmp_info['answer']['value']
#             elif 'ent' in tmp_info:
#                 # info_list.append(get_entity_name(tmp_info['ent']['value'].split('/')[-1]))
#                 tmp_value = tmp_info['ent']['value']
#             else:
#                 raise ValueError
            
#             if 'http://www.wikidata.org/' in tmp_value:
#                 info_list.append(get_entity_name(tmp_value.split('/')[-1]))
#             else:
#                 info_list.append(tmp_value)
#         else:
#             # ans_1 ans_2
#             info_list.append(get_entity_name(tmp_info['ans_1']['value'].split('/')[-1]))
#             info_list.append(get_entity_name(tmp_info['ans_2']['value'].split('/')[-1]))
    
#     # convert list to string
#     opt = ''
#     for i in info_list:
#         opt += i
#         opt += ', '
        
#     return opt[:-2]+'.'

# ###############################################


# def generate_wikidata_query(input):
#     error = 0
#     while error<10:
#         prompt = formatting_prompts_func(input)
#         query = llama_pipeline(prompt)
#         if "Correct query:" in query:
#             processed_query = post_process_query(query)
#             return query, processed_query
#         else:
#             error += 1
#             continue
#     raise Exception("Stage 2: Wikidata generate error")

# def execute_wikidata_query(query, processed_query):
#     knowl = ""
#     try:
#         info = query_wiki(processed_query)
#         if len(info) != 0:
#             tmp_answer = get_wiki_info(info)
#             knowl += processed_query.strip()
#             knowl += " Answer: "
#             knowl += tmp_answer.strip()
#     except:
#         knowl = ""
#     return knowl

# def retrieve_wikidata_knowledge(input):
#     print("Generate query...")
#     query, processed_query = generate_wikidata_query(input)
#     print(processed_query)
#     print("Retrieve knowledge...")
#     knowl = execute_wikidata_query(query, processed_query)
#     print(knowl)
#     return knowl


import requests
def server_retrieve(
    query: str
):
    response = requests.get(
        'http://127.0.0.1:5000/search',
        json={"query": query, "source": "wikidata"},
    )
    if response.status_code != 200:
        raise Exception("Retrieval Wikidata Search API Error: %s" % str(response))
    results = response.json()
    prediction_results, sparql = results
    return prediction_results, sparql



def retrieve_wikidata_knowledge(query):
    print(query)
    print("Retrieve knowledge...")
    knowl, sparql = server_retrieve(query)
    if knowl == "":
        print(sparql)
    else:
        print(knowl)
    return knowl




