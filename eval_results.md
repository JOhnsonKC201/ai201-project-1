# Evaluation Results

## Q1: What do students say about Professor Steele's responsiveness to emails?

**Expected:** Multiple students say she is rude and doesn't respond to emails, often redirecting them to a TA who also doesn't answer.

**System answer:** According to the reviews, students say that Professor Grace Steele is unresponsive to emails. One student stated that "she wouldn't respond to emails" and instead sent out notifications. Another student mentioned that "she is rude and never answers emails at all." A third student described her as "VERY rude and short, especially via email" and said she is "Not of good assistance when asking questions." Overall, students have expressed difficulty in getting a response from Professor Steele via email.

**Retrieved chunks:**
- dist=0.390 | steele_reviews.txt | Prof. Grace Steele | COSC110
- dist=0.421 | steele_reviews.txt | Prof. Grace Steele | COSC110
- dist=0.487 | steele_reviews.txt | Prof. Grace Steele | COSC110
- dist=0.498 | brown_reviews.txt | Prof. Leiza Brown | ENGL102
- dist=0.507 | steele_reviews.txt | Prof. Grace Steele | COSC110

**Accuracy judgment:** Accurate. Retrieval pulled 4/5 chunks from the right professor and the answer quotes the reviews directly with no made-up details. (One brown_reviews chunk slipped in at 0.498 but the LLM correctly ignored it.)

## Q2: Is Professor Sammie Johnson well regarded? Would students take him again?

**Expected:** Yes, very highly rated (around 4.9/5) with reviews saying students would take him again.

**System answer:** Professor Sammie Johnson is well regarded by his students. According to the reviews, he is described as an "amazing teacher" who "actually cares about his students" and is "genuinely invested in student growth" and "success". Students have expressed gratitude for having him as a professor and appreciate his guidance, mentorship, and valuable teachings. One student explicitly stated, "I look forward to taking his class again," indicating a willingness to take his courses again. Overall, the reviews suggest that Professor Johnson is a knowledgeable, caring, and respected professor who pushes his students to succeed, and students would be happy to take his classes again.

**Retrieved chunks:**
- dist=0.326 | johnson_reviews.txt | Prof. Sammie Johnson | CYBR150
- dist=0.347 | johnson_reviews.txt | Prof. Sammie Johnson | INSS491
- dist=0.351 | johnson_reviews.txt | Prof. Sammie Johnson | CYBR150
- dist=0.368 | johnson_reviews.txt | Prof. Sammie Johnson | CYBR380
- dist=0.370 | johnson_reviews.txt | Prof. Sammie Johnson | CYBR380

**Accuracy judgment:** Accurate. All 5 chunks are Johnson reviews and the answer matches the overwhelmingly positive sentiment (his header rating is 4.9/5, 100% would take again). Low distances (0.32–0.37) show a strong match.

## Q3: Does Professor Steele reopen assignments, and when?

**Expected:** Yes, several reviews mention she reopens assignments around the midterm and final periods.

**System answer:** According to the reviews, Professor Grace Steele reopens assignments. Specifically, two students mentioned that she reopens assignments at the midterm and final periods, allowing students to take advantage of this and potentially improve their grades.

**Retrieved chunks:**
- dist=0.411 | steele_reviews.txt | Prof. Grace Steele | COSC110
- dist=0.512 | steele_reviews.txt | Prof. Grace Steele | COSC110
- dist=0.559 | steele_reviews.txt | Prof. Grace Steele | COSC110
- dist=0.618 | brown_reviews.txt | Prof. Leiza Brown | HUMA211
- dist=0.619 | brown_reviews.txt | Prof. Leiza Brown | ENG102

**Accuracy judgment:** Accurate. The top Steele chunks contain the "reopens assignments at the midterm and final periods" detail and the answer reports it correctly. The two Brown chunks at the bottom (0.61+) are off-topic but weren't used.

## Q4: How does Professor Ashton Brice grade and treat students?

**Expected:** Easy grader, gives extra credit, described as kind, funny, relatable and understanding about extensions.

**System answer:** Professor Ashton Brice is described by students as an "easy grader" who gives out extra credit. She has clear grading criteria, which suggests that students know what to expect from her assessments. Students also appreciate that she is understanding, caring, and relatable, often giving assignments and extensions, and providing good feedback. Overall, the reviews portray Professor Brice as a kind, funny, and supportive teacher who looks out for her students, as long as they communicate with her.

**Retrieved chunks:**
- dist=0.264 | brice_reviews.txt | Prof. Ashton Brice | ENGL101
- dist=0.328 | brice_reviews.txt | Prof. Ashton Brice | ENGL101
- dist=0.382 | brice_reviews.txt | Prof. Ashton Brice | ENGL101
- dist=0.409 | brice_reviews.txt | Prof. Ashton Brice | ENGL101
- dist=0.411 | brown_reviews.txt | Prof. Leiza Brown | ENGL102

**Accuracy judgment:** Accurate. Hits every point in the expected answer (easy grader, extra credit, kind/funny/relatable, extensions) and all the content traces back to the retrieved Brice reviews.

## Q5: Which professors give extra credit?

**Expected:** At least 7 professors' reviews mention extra credit (Brice, Brown, Enurah, Fuller, Morales, Rahman, Steele). This is a cross-document aggregation question and I expect the system to struggle with it.

**System answer:** I don't have enough information on that.

**Retrieved chunks:**
- dist=0.473 | brown_reviews.txt | Prof. Leiza Brown | HUMA201
- dist=0.521 | johnson_reviews.txt | Prof. Sammie Johnson | INSS491
- dist=0.529 | johnson_reviews.txt | Prof. Sammie Johnson | CYBR150
- dist=0.549 | johnson_reviews.txt | Prof. Sammie Johnson | CYBR380
- dist=0.552 | johnson_reviews.txt | Prof. Sammie Johnson | CYBR380

**Accuracy judgment:** INACCURATE — this is my failure case. The documents *do* contain the answer: 7 different professors' reviews mention extra credit (Brice, Brown, Enurah, Fuller, Morales, Rahman, Steele). But the system said "I don't have enough information on that." Two things broke: (1) semantic search can't do cross-document aggregation — it returns the 5 chunks most similar to the phrase, not one chunk per professor, so it grabbed 4 Johnson chunks and 1 Brown chunk and missed everyone else; (2) "Extra credit" appears only as a buried two-word tag at the end of reviews, which is too weak a signal to rank highly against the full query. With only those low-signal chunks, the grounding prompt correctly refused rather than guess — so the safety behavior was right, but the answer is still wrong. A fix would be hybrid search (BM25 keyword match on "extra credit" + semantic) or a higher top-k.
