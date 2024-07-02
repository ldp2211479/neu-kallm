from utils.retrieval.wikidata import retrieve_wikidata_knowledge
from utils.retrieval.wikipedia import retrieve_wikipedia_knowledge

# domain and knowledge sources mapping
domain_mapping = {
    "wikidata": retrieve_wikidata_knowledge,
    # "wikitable": retrieve_wikitable_knowledge,
    # "dpr": retrieve_dpr_knowledge,
    "wikipedia": retrieve_wikipedia_knowledge
}


def retrieve_knowledge(input, data_point):
    # input is a string
    knowl = {}
    for source in domain_mapping:
        print("--- Retrieving knowledge from", source)
        tmp_knowl = domain_mapping[source](input, data_point)
        # print(tmp_knowl)
        knowl[source] = tmp_knowl
    return knowl

def knowl_is_empty(knowl):
    for x in knowl:
        if knowl[x] != '':
            return False
    return True