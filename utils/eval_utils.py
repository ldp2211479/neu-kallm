from utils.retrieval.linking import test_linking

def check_answers_id(answer_candidate_id, gold_answers):
    """Check if candidate is answer."""

    gold_answer_ids = [answer["id"] for answer in gold_answers]

    # perform check
    if answer_candidate_id in gold_answer_ids:
        return True

    # no match found
    return False
import re
def check_date_format(date_string):
    # 正则表达式匹配 "YYYY-MM-DD"、"YYYY-MM" 或 "YYYY"
    pattern = r"^\d{4}(-\d{2}(-\d{2})?)?$"
    if re.match(pattern, date_string):
        return True
    else:
        return False

def check_answers_string(answer, gold_answers, mode="in"):
    """Check if candidate is answer."""
    # normalize
    answer_label = answer
    gold_answers_label = [answer['label'].strip().lower() for answer in gold_answers]
    #处理是时间的情况
    if check_date_format(answer_label):
        mode = "in"
    # perform check
    if mode == "in":
        for gold_answer in gold_answers_label:
            if answer_label in gold_answer:
                return True
    else:
        for gold_answer in gold_answers_label:
            if answer_label == gold_answer:
                return True
    # no match found
    return False



def precision_at_1(answers:list, gold_answers:list, mode="in"):
    """ Compute P@1 score for given answers and gold answers.
        
        -- answers : [ answer_text_1, answer_text_2 …… ] if mode != 'entity' else [{id,entity}……]
        -- gold_answers : [{id, label}……]
    
    """

    correct_count = 0
    # go through answer candidates
    for answer in answers:
        if mode == "entity": #只有答案一定全是实体的时候才用
            entities = test_linking(answer)
            if len(entities)==0:
                continue
            correct_count += check_answers_id(entities[0], gold_answers) #取概率最高的
        else:
            correct_count += check_answers_string(answer, gold_answers, mode)
    return correct_count / len(gold_answers) #计算它答对了几个
















