import requests
import numpy as np

def server_retrieve(
    query: str,
    num_paragraphs: int,
    top_p=1,
):
    response = requests.get(
        'http://127.0.0.1:5000/search',
        json={"query": query, "evi_num": num_paragraphs, "source": "wikitable"},
    )
    if response.status_code != 200:
        raise Exception("ColBERT Search API Error: %s" % str(response))
    results = response.json()
    tables = []
    table_titles = []
    for r in results["tables"]:
        r = r.split("<EOT>", maxsplit=1)
        table_titles.append(r[0].split("<BOT>")[1].strip())
        tables.append(r[1].strip())
    scores = results["table_scores"]
    probs = results["table_probs"]
    # print("probs = ", probs)
    top_p_cut_off = np.cumsum(probs) > top_p
    if not np.any(top_p_cut_off):
        # even if we include everything, we don't get to top_p
        top_p_cut_off = len(scores)
    else:
        top_p_cut_off = np.argmax(top_p_cut_off) + 1
    # print("top_p_cut_off = ", top_p_cut_off)
    tables, scores, table_titles = (
        tables[:top_p_cut_off],
        scores[:top_p_cut_off],
        table_titles[:top_p_cut_off],
    )
    return tables, scores, table_titles

def execute_wikipedia_query(query, constraint="none", num_paragraphs=3, top_p=1):
    print("the time constraint is ", constraint)

    tables, scores, table_titles = server_retrieve(query, num_paragraphs, top_p)
    
    # knowl = ""
    # for passage_title, passage in zip(passage_titles, passages):
    #     knowl += passage_title + ", " + passage
    #     knowl += " "
    return [[table_titles[i], tables[i]] for i in range(len(tables))]


def retrieve_wikitable_knowledge(query, constraint="none", num_paragraphs=3, top_p=1):
    print(query)
    print("Retrieve knowledge...")
    knowl = server_retrieve(query, constraint, num_paragraphs, top_p)
    print(knowl)
    return knowl