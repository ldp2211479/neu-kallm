from refined.inference.processor import Refined
import requests
import pickle
import torch
from transformers import AutoTokenizer,AutoModelForCausalLM
from vllm import LLM, SamplingParams
import re
from bidict import bidict
from SPARQLWrapper import SPARQLWrapper, JSON
from jinja2 import Environment, FileSystemLoader, select_autoescape
import utils.globalvar
from .wikidata_utils import fill_template, location_search


###########################################  ReFined Entity linker  ###########################################

# 实体链接模块
class RefinedEntityLinker():
    def __init__(self, model_name:str, path_qid_title_map:str, path_title_pid_map:str) -> None:
        
        # self.model_name = "/mnt/media_1/guest22/ldy/code/wikidata-emnlp23/models/refined"
        # self.path_qid_title_map = "./models/refined/qid_to_title_en.pkl"
        # self.path_title_pid_map = "./models/refined/title_to_pid_en.pkl"
        self.model_name = model_name
        self.path_qid_title_map = path_qid_title_map
        self.path_title_pid_map = path_title_pid_map
    
    def load_titles(self):
        try:
            with open(self.path_qid_title_map, "rb") as f:
                self.qid_title_map = pickle.load(f)
        except Exception as e:
            self.qid_title_map = bidict({})
            with open(self.path_qid_title_map, "wb") as f:
                pickle.dump(self.qid_title_map, f)

        try:
            with open(self.path_title_pid_map, "rb") as f:
                self.title_pid_map = pickle.load(f)
        except Exception as e:
            self.title_pid_map = {}
            with open(self.path_title_pid_map, "wb") as f:
                pickle.dump(self.title_pid_map, f)   

    def save_titles(self):
        # logger.info(f"Saving qid_title_map to {self.path_qid_title_map}...")
        with open(self.path_qid_title_map, "wb") as f:
            pickle.dump(self.qid_title_map, f)
        # logger.info(f"Saving title_pid_map to {self.path_title_pid_map}...")
        with open(self.path_title_pid_map, "wb") as f:
            pickle.dump(self.title_pid_map, f)   


    def load_model(self):
        self.model = Refined.from_pretrained(model_name=self.model_name,
                                        entity_set="wikidata",
                                        download_files=True,
                                        use_precomputed_descriptions=True)
    def load(self):
        self.load_titles()
        self.load_model()

    def get_name_from_qid(self, qid):
        if qid in self.qid_title_map:
            return self.qid_title_map[qid]
        else:
            # include the wd:Q part
            url = 'https://query.wikidata.org/sparql'
            query = '''
            SELECT ?label
            WHERE {{
            {} rdfs:label ?label.
            FILTER(LANG(?label) = "en").
            }}
            '''.format(qid)
            print("processing QID {}".format(qid))
            r = requests.get(url, params = {'format': 'json', 'query': query})
            r.raise_for_status()
            try:
                name = r.json()["results"]["bindings"][0]["label"]["value"]
                print("Found {} with name {}".format(qid, name))
                if name not in self.qid_title_map.values():
                    self.qid_title_map[qid] = name
                return name
            except Exception as e:
                return None

    def refined_ned(self, query):
        spans = self.model.process_text(query)
        output = set()
        for span in spans:
            if span.predicted_entity.wikidata_entity_id:
                qid = span.predicted_entity.wikidata_entity_id
                wikidata_name = self.get_name_from_qid("wd:" + qid)
                if wikidata_name is not None:
                    output.add((wikidata_name, qid))
                else:
                    output.add((" ", qid))
        
        return output  

    def run(self, query: str):
        return list(self.refined_ned(query))

###########################################  llama pipeline  ###########################################

# llama模块
def llama_pipeline_hf(prompt):    
    inputs = utils.globalvar.wikidata_llama_tokenizer(prompt, return_tensors='pt').to("cuda:0")
    outputs = utils.globalvar.wikidata_llama_model.generate(**inputs, max_length=256)
    sparql = utils.globalvar.wikidata_llama_tokenizer.decode(outputs[0], skip_special_tokens=True)
    sparql = sparql.replace("</s>", "").strip()  # 移除</s>标签
    return sparql

def llama_pipeline_vllm(prompt):
    sampling_params = SamplingParams(
        temperature=0,
        max_tokens=256, 
    )
    # Generate output with vLLM
    output = utils.globalvar.wikidata_llama_model.generate(prompt, sampling_params)

    # Decode the output tokens
    sparql = output[0].outputs[0].text
    sparql = sparql.replace("</s>", "").strip()
    if "Response" in sparql:
        sparql = sparql.split("Response:")[1].strip()
    elif "response" in sparql:
        sparql = sparql.split("response:")[1].strip()
    return sparql


# 生成sparql语句
def llama_sparql(query, mode='vllm'):
    pid_mapping_list = utils.globalvar.refinedLinker.run(query)  
    
    _input = fill_template('prompts/property-name-gen.input', {
        "query": query,
        "qid_list_tuples": pid_mapping_list
    })
    _instruction = fill_template('prompts/property-name-gen.instruction')
    prompt = "Below is an instruction that describes a task, paired with an input that provides further context.\nWrite a response that appropriately completes the request.\n\n### Instruction:\n{}\n\n### Input:\n{}\n\n### Response:".format(_instruction, _input)
    
    if mode=='hf':
        output = llama_pipeline_hf(prompt)
    else:
        output = llama_pipeline_vllm(prompt)
    return output


###########################################  get property code  ###########################################
def get_property_id_1(property_name):
    # Wikidata API endpoint
    url = f"https://www.wikidata.org/w/api.php?action=wbsearchentities&format=json&language=en&type=property&search={property_name}"
    try:
        # Send a GET request to the Wikidata API
        response = requests.get(url)
        data = response.json()

        # Check if a matching property is found
        if "search" in data and data["search"]:
            # Retrieve the code of the first matching property
            code = data["search"][0]["id"]
            return code
        else:
            return None
    except requests.exceptions.RequestException as e:
        return None

def get_property_id_2(property_name):
    url = 'https://query.wikidata.org/sparql'
    try:
        property_name = "basic_form_of_government"
        i = property_name.replace('_', ' ').lower()
        pid_query = """
                        SELECT ?property ?propertyLabel WHERE {
                        ?property rdf:type wikibase:Property .
                        ?property rdfs:label "%s"@en .
                        SERVICE wikibase:label { bd:serviceParam wikibase:language "en". }
                    }"""% i
        response = requests.get(url, params={'format': 'json', 'query': pid_query})
        response.raise_for_status()
        data = response.json()
        if 'results' in data and 'bindings' in data['results'] and len(data['results']['bindings']) > 0:
            # Extract the property ID from the response
            property_id = data['results']['bindings'][0]['property']['value']
            property_id = property_id.replace('http://www.wikidata.org/entity/', '')
            return property_id
        else:
            return None
    except requests.exceptions.RequestException as e:
        return None

def get_property_id(property_name):
    pid1 = get_property_id_1(property_name)
    if pid1 is not None:
        utils.globalvar.refinedLinker.title_pid_map[property_name] = pid1
        return pid1
    else:
        pid2 = get_property_id_2(property_name)
        if pid2 is not None:
            utils.globalvar.refinedLinker.title_pid_map[property_name] = pid2
            return pid2
        else:
            return None


###########################################  execute sparql  ###########################################

def query_wiki(query):
  endpoint_url = "https://query.wikidata.org/sparql"

  # Create a SPARQLWrapper object and set the endpoint URL
  sparql = SPARQLWrapper(endpoint_url)

  # Set the SPARQL query
  sparql.setQuery(query)

  # Set the returned format to JSON
  sparql.setReturnFormat(JSON)

  # Execute the query and fetch the results
  results = sparql.query().convert()

  # Process the results
  item_labels = []
  for result in results["results"]["bindings"]:
      item_labels.append(result)
      
  return item_labels

def get_entity_name(qid):
    # if qid in refinedLinker.qid_title_map.keys():
    #     return refinedLinker.qid_title_map[qid]
    
    url = f"https://www.wikidata.org/w/api.php?action=wbgetentities&format=json&ids={qid}"
    response = requests.get(url)
    data = response.json()

    # Extract the entity name
    entity = data["entities"][qid]
    entity_name = entity["labels"]["en"]["value"]  # Assuming you want the English name

    # if entity_name not in refinedLinker.qid_title_map.values():
    #     refinedLinker.qid_title_map[qid] = entity_name
    return entity_name

def get_wiki_info(list_of_info):
    info_list = []
    for i in range(len(list_of_info)):
        tmp_info = list_of_info[i]
        
        if len(tmp_info) == 1:
            if 'obj' in tmp_info:
                tmp_value = tmp_info['obj']['value']
            elif 'value' in tmp_info:
                tmp_value = tmp_info['value']['value']
            elif 'answer' in tmp_info:
                # info_list.append(get_entity_name(tmp_info['answer']['value'].split('/')[-1]))
                tmp_value = tmp_info['answer']['value']
            elif 'ent' in tmp_info:
                # info_list.append(get_entity_name(tmp_info['ent']['value'].split('/')[-1]))
                tmp_value = tmp_info['ent']['value']
            elif 'x' in tmp_info:
                tmp_value = tmp_info['x']['value']
            else:
                raise ValueError
            
            if 'http://www.wikidata.org/' in tmp_value:
                info_list.append(get_entity_name(tmp_value.split('/')[-1]))
            else:
                info_list.append(tmp_value)
        else:
            # ans_1 ans_2
            info_list.append(get_entity_name(tmp_info['ans_1']['value'].split('/')[-1]))
            info_list.append(get_entity_name(tmp_info['ans_2']['value'].split('/')[-1]))
    
    # convert list to string
    opt = ''
    for i in info_list:
        opt += i
        opt += ', '
        
    return opt[:-2]+ '.'

def execute_sparql(sparql):
    knowl = ""
    try:
        info = query_wiki(sparql)
        if len(info) != 0:
            tmp_answer = get_wiki_info(info)
            knowl += sparql.strip()
            knowl += " Answer: "
            knowl += tmp_answer.strip()
    except:
        knowl = ""
    return knowl


###########################################  retrieval wikidata  ###########################################
def execute_wikidata_query(query):
    sparql = llama_sparql(query)
    
    # replace property(to pid)
    property_list =  [x[1] for x in re.findall(r'(wdt:|p:|ps:|pq:)([a-zA-Z_\(\)(\/_)]+)(?![1-9])', sparql)]
    pid_replacements = {}
    for property in property_list:
        if property in utils.globalvar.refinedLinker.title_pid_map.keys():
            pid_replacements[property] = utils.globalvar.refinedLinker.title_pid_map[property]
        else:
            pid = get_property_id(property)
            if pid is not None:
                pid_replacements[property] = pid
            else:
                pid_replacements[property] = ""
    
    def sub_fcn(match):
        prefix = match.group(1)
        value = match.group(2)
        return prefix + pid_replacements[value]
    sparql = re.sub(r'(wdt:|p:|ps:|pq:)([a-zA-Z_\(\)(\/_)]+)(?![1-9])', lambda match: sub_fcn(match), sparql)

    # replace location entity(such as "anaheim, ca" to "anaheim, california")
    entity_list =  [x[1] for x in re.findall(r'(wd:)([a-zA-PR-Z_0-9-]+)', sparql)]
    qid_replacements = {}
    for entity in entity_list:
        if entity in utils.globalvar.refinedLinker.qid_title_map.keys():
            continue
        elif entity in utils.globalvar.refinedLinker.qid_title_map.values():
            qid_replacements[entity] = utils.globalvar.refinedLinker.qid_title_map[entity]
        elif entity.lower().replace(' ', '_').replace('/','_').replace('-', '_') in utils.globalvar.refinedLinker.qid_title_map.values():
            entity_stand = entity.lower().replace(' ', '_').replace('/','_').replace('-', '_')
            qid_replacements[entity_stand] = utils.globalvar.refinedLinker.qid_title_map[entity_stand]
        else:
            try_location = location_search(entity.replace("_", " "))
            if try_location is not None:
                try_location = "wd:" + try_location
                print("inserting {} for {}".format(try_location, entity))
                utils.globalvar.refinedLinker.qid_title_map[try_location] = entity
                qid_replacements[entity] = try_location
            else:
                print("CANNOT FIND ENTITY: {} for SPARQL {}".format(entity, sparql))
                return [], sparql
    
    def sub_entity_fcn(match):
        value = match.group(2)
        return qid_replacements[value]
    sparql = re.sub(r'(wd:)([a-zA-PR-Z_0-9-]+)', lambda match: sub_entity_fcn(match), sparql)
        
    # execute the result
    prediction_results = execute_sparql(sparql)
    return prediction_results, sparql

###########################################  main  ###########################################

def wikidata_load(llama_model_path:str, refined_model_name:str, path_qid_title_map:str, path_title_pid_map:str, mode='vllm'):
    utils.globalvar.refinedLinker = RefinedEntityLinker(refined_model_name, path_qid_title_map, path_title_pid_map)
    utils.globalvar.refinedLinker.load()
    
    llama_model_path = llama_model_path
    if mode=='hf':
        utils.globalvar.wikidata_llama_model = AutoModelForCausalLM.from_pretrained(
                llama_model_path,
                use_safetensors=True,
                torch_dtype=torch.float16,
                device_map={"":"cuda:0"}
            )
        utils.globalvar.wikidata_llama_tokenizer = AutoTokenizer.from_pretrained(llama_model_path)
    else:
        utils.globalvar.wikidata_llama_model = LLM(
                model=llama_model_path,
                tokenizer=llama_model_path,
                dtype="float16",  # Use float16 for efficient GPU usage
                trust_remote_code=True,
                gpu_memory_utilization=utils.globalvar.gpu_memory_utilization,
            )
    utils.globalvar.jinja_environment = Environment(loader=FileSystemLoader('./'),
                autoescape=select_autoescape(), trim_blocks=True, lstrip_blocks=True, line_comment_prefix='#')
