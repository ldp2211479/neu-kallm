# import json
# from serpapi import GoogleSearch
# import pickle
# from tqdm.notebook import tqdm
# import os.path
# import os
# import openai
# from datasets import load_dataset
# from transformers import DPRQuestionEncoder, DPRQuestionEncoderTokenizer
# from utils.openai_utils import call_openai_api

# verify_question_demonstration = """
# Write a question that asks about the answer to the overall question.

# Overall Question: The Sentinelese language is the language of people of one of which Islands in the Bay of Bengal?
# Answer: The language of the people of North Sen- tinel Island is Sentinelese.
# Question: What peoples ́ language is Sentinelese?

# Overall Question: Two positions were filled in The Voice of Ireland b which British-Irish girl group based in London, England?
# Answer: Little Mix is based in London, England. 
# Question: What girl group is based in London, England?

# Overall Question: Where were the Olympics held when the 1993 World Champion figure skater's home country won it's second Winter Games gold medal?
# Answer: the 1993 World Champion figure skater's home country is Canada.
# Question: What is the home country of the 1993 World Champion figure skater?
# """

# def generate_wikipedia_query(input, overall_question):
#     prompt = verify_question_demonstration + "\nOverall Question: " + overall_question + \
#             "\nAnswer: " + input + "\nQuestion: "
            
#     # query = call_openai_api("text-davinci-003", prompt, max_tokens=256, temperature=0, n=1)[1].strip()
#     query = call_openai_api("llama3:70b", prompt, max_tokens=256, temperature=0, n=1)[1].strip()
#     query += " @wikipedia"
#     return query

# def execute_wikipedia_query(query):
#     key = os.environ.get("SERPAPI_KEY")
#     params = {
#         "engine": "google",
#         "q": query,
#         "api_key": key,
#     }

#     search = GoogleSearch(params)
#     results = search.get_dict()
#     # if "error" in results:
#     #     raise Exception(results["error"])

#     knowl = ""

#     if "answer_box" in results:
#         if "snippet" in results["answer_box"]:
#             knowl += results["answer_box"]["snippet"]
#             knowl += " "
        
#     # organic answers
#     if "organic_results" in results:
#         # yield maximun 3 snippets
#         if len(knowl) == 0:
#             # if no answer box, yield maximun 3 snippets
#             num_snippets = min(3, len(results["organic_results"]))
#         else:
#             num_snippets = min(2, len(results["organic_results"]))
            
#         for i in range(num_snippets):
#             if "snippet" in results["organic_results"][i]:
#                 knowl += results["organic_results"][i]["snippet"]
#                 knowl += " "
#     return knowl


# def retrieve_wikipedia_knowledge(input, data_point):
#     print("Generate query...")
#     query = generate_wikipedia_query(input, data_point["question"])
#     print(query)
#     print("Retrieve knowledge...")
#     knowl = execute_wikipedia_query(query)
#     print(knowl)
#     return knowl


import requests
import numpy as np
import logging
import re
import spacy

logger = logging.getLogger(__name__)

spacy_nlp = spacy.load("en_core_web_sm")

def server_retrieve(
    query: str,
    num_paragraphs: int,
    rerank="none",
    top_p=1,
):
    """
    Args:
        `num_paragraphs`: number of paragraphs that will be output
        `rerank` (str): one of 'none', 'recent' or a year like '2005'. 'none' disables reranking. 'recent' retrieves more and returns the most recent ones.
                        '2005' boosts the ranking of results that match 2005. The date of a result is determined by the year numbers it contains.
        `top_p` (float): chooses from the smallest possible set of results whose cumulative probability exceeds top_p
    Returns:
        `passages` (list): a list of passage texts (excluding the title) with the highest similarities to the `query`
        `passage_scores` (list): a list of similarity scores of each passage in `passsages` with `query`
        `passage_titles` (list): a list of passage titles
    """

    # print(self.colbert_endpoint, {'query': query, 'evi_num': num_paragraphs})
    response = requests.get(
        'http://127.0.0.1:5000/search',
        json={"query": query, "evi_num": num_paragraphs, "source": "wikipedia"},
    )
    if response.status_code != 200:
        raise Exception("ColBERT Search API Error: %s" % str(response))
    results = response.json()
    passages = []
    passage_titles = []
    for r in results["passages"]:
        r = r.split("|", maxsplit=1)
        passage_titles.append(r[0].strip())
        passages.append(r[1].strip())
    scores = results["passage_scores"]
    probs = results["passage_probs"]
    # print("probs = ", probs)
    top_p_cut_off = np.cumsum(probs) > top_p
    if not np.any(top_p_cut_off):
        # even if we include everything, we don't get to top_p
        top_p_cut_off = len(scores)
    else:
        top_p_cut_off = np.argmax(top_p_cut_off) + 1
    # print("top_p_cut_off = ", top_p_cut_off)
    passages, scores, passage_titles = (
        passages[:top_p_cut_off],
        scores[:top_p_cut_off],
        passage_titles[:top_p_cut_off],
    )

    if rerank == "none":
        pass
    else:
        all_passage_dates = []
        for t, p in zip(passage_titles, passages):
            passage_years = extract_year(title=t, passage=p)
            all_passage_dates.append(passage_years)
        if rerank == "recent":
            sort_fn = lambda x: max(
                x[3] if len(x[3]) > 0 else [0]
            )  # sort based on the latest year mentioned in the paragraph, demoting paragraphs that don't mention a year
        else:
            # rerank is a year
            try:
                query_year = int(rerank)
            except ValueError as e:
                # raise ValueError('rerank should be none, recent or an integer.')
                logger.error(e)
                return (
                    passages[:num_paragraphs],
                    scores[:num_paragraphs],
                    passage_titles[:num_paragraphs],
                )
            sort_fn = lambda x: x[3].count(
                query_year
            )  # boost the passages that have a matching year with the query, the more they mention the date the more we boost

        # logger.info('Search result dates before date-based reranking: %s', str(all_passage_dates))
        passages, scores, passage_titles, all_passage_dates = list(
            zip(
                *sorted(
                    zip(passages, scores, passage_titles, all_passage_dates),
                    reverse=True,
                    key=sort_fn,
                )
            )
        )
        # logger.info('Search result dates after date-based reranking: %s', str(all_passage_dates))

    # choose top num_paragraphs paragraphs
    passages, scores, passage_titles = (
        passages[:num_paragraphs],
        scores[:num_paragraphs],
        passage_titles[:num_paragraphs],
    )

    return passages, scores, passage_titles


def extract_year(title, passage): #找到一个段落所涉及的所有年份
    if title:
        passage = title + " | " + passage
    years = []
    year_pattern = r"\d{4}"
    year_duration_pattern = r"\b\d{4}[--–]\d{2}\b"
    year_to_pattern = r"\b\d{4} to \d{4}\b"
    # extract "1990 to 1998" before spacy because spacy would split it to 1990 and 1998
    re_year_tos = re.findall(year_to_pattern, passage)
    for re_year_to in re_year_tos:
        re_years = re.findall(year_pattern, re_year_to)
        if len(re_years) != 2:
            continue
        year1, year2 = re_years
        years.extend(list(range(int(year1), int(year2) + 1)))
        passage.replace(re_year_to, " ")

    doc = spacy_nlp(passage)
    dates = [(X.text, X.label_) for X in doc.ents if X.label_ == "DATE"]
    for date in dates:
        date = date[0]
        # "the 2006–07 season"
        re_year_durations = re.findall(year_duration_pattern, date)
        if re_year_durations:
            for re_year_duration in re_year_durations:
                if "–" in re_year_duration:
                    year1, year2 = re_year_duration.split("–")
                elif "-" in re_year_duration:
                    year1, year2 = re_year_duration.split("-")
                else:
                    continue
                year2 = year1[:2] + year2
                years.extend([year1, year2])
            continue
        # any 4 digits
        re_years = re.findall(year_pattern, date)
        if re_years:
            years.extend(re_years)
    # years = list(sorted(set([int(year) for year in years])))#这里有个set操作 但是sort_fn = lambda x: x[3].count(query_year)这里的计数排序 永远只有1
    years = list(sorted([int(year) for year in years]))
    return years


def execute_wikipedia_query(query, constraint="none", num_paragraphs=3, top_p=1):
    print("the time constraint is ", constraint)
    # rerank = extract_year("", constraint) # 抽取这个约束里包含的时间
    # if len(rerank) > 0:
    #     rerank = rerank[0] #如果是跨度时间 这里并不能很好的处理 因此我们先统一将constraint设置为none先
    # else:
    #     rerank = 'none'
    passages, scores, passage_titles = server_retrieve(query, num_paragraphs, "none", top_p)
    
    # knowl = ""
    # for passage_title, passage in zip(passage_titles, passages):
    #     knowl += passage_title + ", " + passage
    #     knowl += " "
    return [[passage_titles[i], passages[i]] for i in range(len(passages))]



def retrieve_wikipedia_knowledge(query, constraint="none", num_paragraphs=3, top_p=1):
    print(query)
    print("Retrieve knowledge...")
    knowl = execute_wikipedia_query(query, constraint, num_paragraphs, top_p)
    print(knowl)
    return knowl