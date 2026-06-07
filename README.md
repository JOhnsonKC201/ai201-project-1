# The Unofficial Guide

A RAG (retrieval-augmented generation) system that answers plain-language questions about Morgan State University professors using real student reviews. You ask something like *"Is Professor Steele responsive to emails?"* and it pulls the most relevant reviews and gives you a grounded, cited answer instead of making something up.

## Setup

```bash
python -m venv .venv
source .venv/Scripts/activate        # Windows Git Bash  (Mac/Linux: source .venv/bin/activate)
pip install -r requirements.txt
cp .env.example .env                 # then paste your Groq key into .env
```

Get a free Groq key at https://console.groq.com (no card needed).

Then:

```bash
python src/index.py        # embed all chunks + build the vector store (run once)
python app.py              # launch the web UI at http://localhost:7860
```

Other useful scripts:
- `python src/ingest.py` — see the chunks without embedding
- `python src/retrieval_test.py` — check retrieval quality (no API key needed)
- `python src/query.py "your question"` — ask from the terminal
- `python src/evaluate.py` — run the 5 evaluation questions

## Domain and Document Sources

**Domain:** student reviews of Morgan State University professors. Official pages (course catalog, department sites) won't tell you a professor doesn't answer emails or reopens assignments before the final — that lives only in student reviews, and you normally have to dig through dozens of them.

**Sources:** 10 plain-text files, one per professor, from **ratemyprofessors.com**:

| File | Professor | Department |
|------|-----------|------------|
| brice_reviews.txt | Ashton Brice | English |
| brown_reviews.txt | Leiza Brown | English |
| dacon_reviews.txt | Jamell Dacon | Computer Science |
| enurah_reviews.txt | Nadezhda Enurah | Mathematics |
| fuller_reviews.txt | Julian Fuller | Mathematics |
| gibson_reviews.txt | Dr. Gibson | Computer Science / Info Science |
| johnson_reviews.txt | Sammie Johnson | Information Science / Cybersecurity |
| morales_reviews.txt | Harold Morales | Religion |
| rahman_reviews.txt | Md Rahman | Computer Science |
| steele_reviews.txt | Grace Steele | Computer Science |

I deliberately mixed high-rated (Johnson 4.9, Brice 5.0) and low-rated (Steele 2.0) professors so the system has to handle both glowing and harsh reviews.

## Ingestion Pipeline

`src/ingest.py` does three things:
1. **Loads** each `.txt` file.
2. **Cleans** it — unescapes any HTML entities (`&#39;` → `'`), strips stray HTML tags, and collapses extra whitespace. (The files were mostly clean already, but the cleaning step is there so copy/paste artifacts don't leak into chunks.)
3. **Chunks** it (see below).

## Chunking Strategy

**One review = one chunk.** Each file is split on the `---` separator, and every individual review becomes its own chunk.

- **Size:** capped at ~800 characters (~200 tokens). Most reviews are far shorter — a typical one is 1–4 sentences. The cap exists because `all-MiniLM-L6-v2` only reads ~256 tokens, so anything longer gets truncated anyway.
- **Overlap:** **0** between reviews — they're separate opinions from different students, so overlapping them would just merge unrelated thoughts. Overlap (100 chars) is only used in the rare case where a *single* review is longer than 800 chars and has to be sentence-split.
- **Why it fits:** reviews are already self-contained units. "She is rude and never answers emails" makes complete sense alone. Fixed 500-char splitting would cut reviews in half and glue the end of one student's review onto the start of another's — which is exactly what wrecks retrieval.

To keep each chunk standalone I prepend a context line: `Professor <name> (<dept>), course <course>, <date>, rated <quality>/5:` so even a one-sentence review still says who and what it's about.

**Result: 310 chunks** across 10 files (well inside the recommended 50–2,000).

## Sample Chunks

1. **steele_reviews.txt** — *Professor Grace Steele (Computer Science), course COSC110, Dec 20, 2025, rated 1.0/5:* "She is very rude. Our class had a hard time getting into Pearson and when we asked her about it she wouldn't respond to emails but sent out notifications basically trying to make it seem like we all were purposely not doing the work. We had to get a TA and go through him to even get a response from her about grades."

2. **johnson_reviews.txt** — *Professor Sammie Johnson (Information Science), course CYBR380, May 6, 2026, rated 5.0/5:* "Sammie Johnson is a great professor who explains the material clearly and connects real-life situations back to what we learn in class. He is always helpful after class, encourages students to speak confidently, and is a great connection for future opportunities."

3. **brice_reviews.txt** — *Professor Ashton Brice (English), course ENGL101, Dec 16, 2025, rated 5.0/5:* "Great professor, teaches well, easy reach and she is very understanding but she knows a lie from a truth so don't think you can do what you want. The class is mostly creative presentations based on the topic. All in all, I loved this class, no stress on my first year. Participation matters. Extra credit. Clear grading criteria."

4. **brown_reviews.txt** — *Professor Leiza Brown (English), course ENG102, Dec 4, 2024, rated 5.0/5:* "Dr. Leiza Brown's class challenged students to utilize critical skills that I project will be necessary for completing college... Get ready to read. Gives good feedback. So many papers."

5. **fuller_reviews.txt** — *Professor Julian Fuller (Mathematics), course MATH110, Jun 1, 2026, rated 3.0/5:* "He's chill as long as you show that you care and have a genuine interest in the course. Homework barely counts, the tests and quizzes mainly make or break your grade. Beware of pop quizzes."

## Embedding Model

I used **`all-MiniLM-L6-v2`** via sentence-transformers. It runs locally — no API key, no rate limits — and embeds all 310 chunks in a couple seconds. Vectors are stored in **ChromaDB** (local, persistent), using **cosine distance** so scores are readable (0 = identical, lower = more similar).

**Production tradeoffs (if cost weren't a constraint):** I'd consider a larger model with a longer context window so long reviews don't get truncated, and maybe one fine-tuned for short opinion text since MiniLM is general-purpose. I'd weigh an API model (e.g. OpenAI `text-embedding-3-large`) for better accuracy against the privacy and no-rate-limit benefits of staying local, and factor in latency — a local model has no network round-trip per query. For a multilingual student body I'd also want a multilingual embedding model.

## Retrieval Test Results

`top-k = 5`, cosine distance. Three queries (full output in the terminal via `python src/retrieval_test.py`):

**Query 1: "what do students say about professor steele's emails?"**
- 0.399 — steele_reviews.txt: "She is very rude... wouldn't respond to emails..."
- 0.427 — steele_reviews.txt: "she is rude and never answers emails at all... direct you to her TA..."
- 0.463 — steele_reviews.txt: "VERY rude and short, especially via email..."

*Why relevant:* all three top hits are from the correct professor (Steele) and directly about email responsiveness, even though only one of them literally contains the word "email" in the same form as the query — semantic search matched the *meaning* of "responsive" to "never answers." Distances are all under 0.5, which signals strong matches.

**Query 2: "is professor sammie johnson a good teacher?"**
- 0.288 — johnson_reviews.txt: "I love Prof. Sammie, he is an amazing teacher that actually cares..."
- 0.288 — johnson_reviews.txt: "Sammie Johnson is a great professor who explains the material clearly..."
- 0.290 — johnson_reviews.txt: "I have no complaints with this teacher..."

*Why relevant:* every hit is a Johnson review and every one speaks to teaching quality. The very low distances (~0.29) reflect that these reviews are almost a paraphrase of the question — strong, on-topic retrieval from the right source.

**Query 3: "which professors give extra credit?"**
- 0.473 — brown_reviews.txt (about being unorganized — *off topic*)
- 0.521+ — johnson_reviews.txt (general praise — *off topic*)

This one retrieves poorly on purpose — it's my failure case (see below).

## Grounded Generation

Grounding is enforced two ways:

1. **System prompt** (`src/query.py`): the model is told to answer *only* from the provided context, to reply exactly `"I don't have enough information on that."` when the context is insufficient, and to never invent ratings or quotes. Temperature is set to `0` for factual, repeatable answers.
2. **Pipeline structure**: the only professor content the model ever sees is the retrieved chunks — they're injected into the prompt as `CONTEXT`. Source attribution is built **programmatically** from chunk metadata after generation, not left to the LLM to remember, so citations can't be hallucinated. If the model returns the refusal string, the source list is suppressed (no point citing sources for a non-answer).

## Example Responses

**In-scope #1 — "what do students say about professor steele's emails?"**
> According to the reviews, students say that Professor Grace Steele does not respond to emails. One review states that "she wouldn't respond to emails" and instead sent out notifications. Another mentions she "is rude and never answers emails at all." A third describes her as "VERY rude and short, especially via email."
>
> **Retrieved from:** steele_reviews.txt (Prof. Grace Steele)

**In-scope #2 — "how does Professor Ashton Brice grade and treat students?"**
> Professor Ashton Brice is described as an "easy grader" who gives out extra credit and has clear grading criteria. Students say she is understanding, caring, and relatable, often giving extensions and good feedback.
>
> **Retrieved from:** brice_reviews.txt (Prof. Ashton Brice)

**Out-of-scope — "what is the parking situation like at the law school?"**
> I don't have enough information on that.
>
> *(no sources listed — the system declines instead of guessing)*

## Query Interface

A Gradio web app (`app.py`, opens at `http://localhost:7860`):
- **Input:** one textbox, "Your question."
- **Outputs:** "Answer" (the grounded response) and "Retrieved from" (the source files/professors the answer drew on).
- Works with the Ask button or by pressing Enter.

**Sample interaction:**
```
Your question:  Does Professor Steele reopen assignments?

Answer:         According to the reviews, Professor Grace Steele reopens
                assignments at the midterm and final periods, so students
                can take advantage of that to improve their grades.

Retrieved from: • steele_reviews.txt (Prof. Grace Steele)
```

## Evaluation Report

All 5 test questions, run through the full system. (The same content with raw distance scores is in **`eval_results.md`**, generated by `python src/evaluate.py`.)

**Summary: 4 accurate, 1 inaccurate (the failure case).**

### Q1 — What do students say about Professor Steele's responsiveness to emails?
- **Expected:** She's rude and doesn't answer emails; redirects students to a TA who also doesn't respond.
- **System answer:** "Professor Grace Steele does not respond to emails. One review states she 'wouldn't respond to emails' and instead sent out notifications. Another mentions she 'is rude and never answers emails at all.' A third describes her as 'VERY rude and short, especially via email.'"
- **Retrieved from:** 4 of 5 chunks from steele_reviews.txt (distances 0.39–0.51).
- **Judgment: Accurate.** Right professor, quotes the reviews, no invented detail.

### Q2 — Is Professor Sammie Johnson well regarded? Would students take him again?
- **Expected:** Yes — extremely high rating (~4.9/5), reviews say he cares, explains well, would take again.
- **System answer:** "Professor Sammie Johnson is well regarded... described as an 'amazing teacher' who 'actually cares about his students.' One student stated 'I look forward to taking his class again,' indicating a willingness to take his courses again."
- **Retrieved from:** all 5 chunks from johnson_reviews.txt (distances 0.33–0.37).
- **Judgment: Accurate.** Matches his 4.9/5 header rating and 100% would-take-again.

### Q3 — Does Professor Steele reopen assignments, and when?
- **Expected:** Yes, around the midterm and final periods.
- **System answer:** "Professor Grace Steele reopens assignments at the midterm and final periods, so students can take advantage of that to improve their grades."
- **Retrieved from:** top 3 chunks from steele_reviews.txt (distances 0.41–0.56).
- **Judgment: Accurate.** The specific "midterm and final" detail is correct and traceable.

### Q4 — How does Professor Ashton Brice grade and treat students?
- **Expected:** Easy grader, gives extra credit, kind, funny, relatable, flexible with extensions.
- **System answer:** "Professor Ashton Brice is described as an 'easy grader' who gives out extra credit and has clear grading criteria. Students say she is understanding, caring, and relatable, often giving extensions and good feedback."
- **Retrieved from:** 4 of 5 chunks from brice_reviews.txt (distances 0.26–0.41).
- **Judgment: Accurate.** Hits every expected point.

### Q5 — Which professors give extra credit?
- **Expected:** At least 7 professors' reviews mention extra credit (Brice, Brown, Enurah, Fuller, Morales, Rahman, Steele).
- **System answer:** "I don't have enough information on that."
- **Retrieved from:** 1 Brown chunk + 4 Johnson chunks (distances 0.47–0.55) — none of the 7 professors who actually mention extra credit.
- **Judgment: Inaccurate.** This is the failure case (below).

### Failure Case — Q5: "Which professors give extra credit?"

The documents **do** contain the answer: 7 professors' reviews mention extra credit (Brice, Brown, Enurah, Fuller, Morales, Rahman, Steele). But the system answered *"I don't have enough information on that."* — a false negative.

**Why it failed**, tied to the pipeline:
1. **Semantic search can't aggregate across documents.** It returns the 5 chunks most *similar* to the query, not one chunk per professor. So it grabbed 4 Johnson chunks + 1 Brown chunk and never saw the professors who actually mention extra credit.
2. **"Extra credit" is a low-signal buried tag.** It appears as a two-word tag at the *end* of reviews ("...Clear grading criteria. Extra credit."), which doesn't rank highly against a full-sentence query about giving extra credit.

With only weak, off-topic chunks, the grounding prompt did the *right* thing by refusing rather than guessing — so the safety behavior worked, but the final answer is still wrong. A real fix would be **hybrid search** (BM25 keyword match on "extra credit" combined with semantic search) or a higher top-k so more professors land in the context.

## Spec Reflection

**One way the spec helped:** writing the chunking section in `planning.md` first forced me to commit to "one review = one chunk, zero overlap" *before* coding. Because I'd already reasoned through why overlap doesn't help independent opinions, the `ingest.py` implementation was basically a direct translation of the plan instead of trial-and-error.

**One way the implementation diverged:** my plan assumed Q5 ("cross-document comparison") would be hard but answerable. In reality the original Q5 ("best cybersecurity professor") turned out *trivially easy* because Johnson is the only cyber professor, so it didn't surface any weakness. I changed Q5 to the "extra credit" aggregation question, which actually exposes the real limitation. I also added the cosine-distance setting, which wasn't in the original plan — Chroma's default L2 scores were unreadable, so I switched it after seeing the numbers.

## AI Usage

> _Note to self: confirm these match how you actually worked before submitting._

1. **Ingestion/chunking code.** I gave the AI my chunking strategy (one review per chunk, 800-char cap, prepend professor context) and had it write the `ingest.py` parser that splits on `---` and builds the context line. I reviewed the output, ran it, and verified the 310-chunk count and that chunks were self-contained.

2. **Distance metric fix.** The AI's first vector-store code used ChromaDB's default distance and the scores came back above 0.7 for good matches, which didn't match the spec's "below 0.5" guidance. I had it switch the collection to cosine distance, then re-ran the retrieval test to confirm the good matches dropped to the 0.28–0.46 range.

3. **Evaluation honesty.** When all 5 original eval questions passed, I recognized the spec wanted a real failure, found the "extra credit" aggregation weakness myself, and directed the AI to swap that question in and document the root cause rather than hide it.
