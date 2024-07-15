from utils.retrieval.wikidata import retrieve_wikidata_knowledge
from utils.retrieval.wikipedia import retrieve_wikipedia_knowledge

#  knowledge sources mapping
domain_mapping = {
    "wikidata": retrieve_wikidata_knowledge,
    # "wikitable": retrieve_wikitable_knowledge,
    "wikipedia": retrieve_wikipedia_knowledge
}


def retrieve_knowledge(query, constraint):
    # input is a string
    knowl = {}
    knowl_wikipedia_list = []
    for source in domain_mapping:
        print("--- Retrieving knowledge from", source)
        if 'wikidata' in source:
            tmp_knowl = domain_mapping[source](query)
        elif 'wikipedia' in source:
            tmp_knowl = domain_mapping[source](query, constraint)
        knowl[source] = tmp_knowl
    return knowl

def knowl_is_empty(knowl):
    for x in knowl:
        if knowl[x] != '':
            return False
    return True