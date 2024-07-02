################################
########### TIQ ###########
################################

tiq_s1_prompt_demonstration = """
Strictly follow the format of the below examples, decompose the question into two sub-questions before answering, and address them in a cascading manner.
Question: What multi-sport event did Liu Xiang win in the same year that he won at the Universiade in Beijing with a time of 13.33 seconds?
Sub-question 1: When did Liu Xiang win Universiade in Beijing with a time of 13.33 seconds?
Answer 1: In August 2001, he won at the Universiade in Beijing with a time of 13.33 seconds.
Based on Answer 1, the time constraint for Sub-question 2 is: 2001.
Sub-quesion 2: What multi-sport event did Liu Xiang win in 2001 except the Universiade in Beijing?
Answer 2: In 2001, He also won at the 2001 National Games of China that same year.
Final answer: the 2001 National Games of China.

Question: Who founded Bucks County when it was one of Pennsylvania's three original counties created by the colonial proprietor?
Sub-question 1: when was Bucks County one of Pennsylvania's three original counties?
Answer 1: Bucks County, Founded, November 1682.
According to Answer 1, the time of Subquestion 1 is: November 1682.
Sub-question 2: Who founded Bucks County in November 1682?
Answer 2: Bucks County is one of the three original counties created by colonial proprietor William Penn in 1682.
Final answer: William Penn

Question: What role did Habib Bourguiba hold before Tunisia became a republic under his presidency?
Sub-question 1: When did Tunisia become a republic under Habib Bourguiba's presidency？
Answer 1: On 25 July 1957, the monarchy was abolished with Tunisia reorganizing as a republic.
According to Answer 1, the time of Subquestion 1 is: 25 July 1957.
Sub-question 2: What role did Habib Bourguiba hold before 25 July 1957?
Answer 2: Following the country's independence in 1956, Bourguiba was appointed prime minister by king Muhammad VIII al-Amin and acted as de facto ruler before proclaiming the Republic, on 25 July 1957.
Final answer: Prime minister.

"""

tiq_s2_edit_prompt_demonstration = """
Strictly follow the format of the below examples. The given sentence may have temporal errors, please correct them based on the given external knowledge.
Sentence: U S Steel became the 8th largest steel producer in the world in 2008.
Knowledge: U.S. Steel. It was the eighth-largest steel producer in the world in 2008. 
Edited sentence: U S Steel became the 8th largest steel producer in the world in 2008.

Sentence: During N D Tiwari's tenure as Minister of External Affairs, Rajiv Gandhi signed the Indo-Sri Lanka Accord in July, 1987.
Knowledge: Rajiv Gandhi. Gandhi signed the Indo-Sri Lanka Accord in July 1987.
Edited sentence: During N D Tiwari's tenure as Minister of External Affairs, Rajiv Gandhi signed the Indo-Sri Lanka Accord in July, 1987.

Sentence: Scholastic Corporation was founded by Maurice R Robinson on October 22, 1920.
Knowledge: Scholastic Corporation. It covered high school sports and social activities; the four-page magazine debuted on October 22, 1920, and was distributed in 50 high schools.
Edited sentence: Scholastic Corporation was founded by Maurice R Robinson on October 22, 1920.

Sentence: Barbara Stanwyck received an Honorary Oscar in 1982, the Golden Globe Cecil B. DeMille Award in 1990 and several other honorary lifetime awards.
Knowledge: Barbara Stanwyck, award received, Golden Globe Cecil B. DeMille Award, point in time, 1986
Edited sentence: Barbara Stanwyck received an Honorary Oscar in 1982, the Golden Globe Cecil B. DeMille Award in 1986 and several other honorary lifetime awards.

Sentence: The Station nightclub fire occurred In January, 2003.
Knowledge: In February 2003, Great White was on an eighteen-date concert tour.
Edited sentence: The Station nightclub fire occurred In February, 2003.

Sentence: Citizen Lab was researching NSO Group in January 12, 2018.
Knowledge: According to a January 24, 2019 AP News report, Citizen Lab researchers were "being targeted" by "international undercover operatives" for its work on NSO Group.
Edited sentence: Citizen Lab was researching NSO Group in January 24, 2019.

"""