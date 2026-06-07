# Planning — The Unofficial Guide

## Domain

My Unofficial Guide covers **student reviews of professors at Morgan State University**. I pulled reviews from RateMyProfessors for 10 different professors across several departments (Computer Science, Information Science, Mathematics, English, Religion). This kind of knowledge is hard to find through official channels because the course catalog and department pages will never tell you that a professor doesn't answer emails, curves the midterm, or reopens assignments before the final — that stuff only lives in student reviews, and you usually have to dig through dozens of them to get the real picture.

## Documents

10 plain-text files, one per professor, scraped/copied from ratemyprofessors.com. Each file has a short header (name, department, overall rating) and then all of that professor's individual reviews separated by `---`.

- brice_reviews.txt — Ashton Brice (English, ENGL101)
- brown_reviews.txt — Leiza Brown (English, ENG102/HUMA201)
- dacon_reviews.txt — Jamell Dacon (Computer Science)
- enurah_reviews.txt — Nadezhda Enurah (Mathematics)
- fuller_reviews.txt — Julian Fuller (Mathematics)
- gibson_reviews.txt — Dr. Gibson (Computer Science / Information Science)
- johnson_reviews.txt — Sammie Johnson (Information Science / Cybersecurity, CYBR & INSS courses)
- morales_reviews.txt — Harold Morales (Religion)
- rahman_reviews.txt — Md Rahman (Computer Science)
- steele_reviews.txt — Grace Steele (Computer Science, COSC110)

I picked professors with a mix of good and bad ratings on purpose so the system has to handle both glowing reviews and harsh ones, not just one tone.

## Chunking Strategy

**One review = one chunk.** Each individual review becomes its own chunk instead of splitting on a fixed character count.

- **Chunk size:** capped at ~800 characters (~200 tokens), but most chunks are way under that — a typical review is 1–4 sentences. The 800 cap exists because the embedding model (all-MiniLM-L6-v2) only reads about 256 tokens, so anything longer would get truncated anyway.
- **Overlap:** 0 between reviews. Reviews are separate opinions from different students, so overlapping them would just mash two unrelated opinions together. The only time I use overlap (100 chars) is the rare case where a *single* review is longer than 800 chars and has to be sentence-split into sub-chunks.
- **Why this fits:** the reviews are already written as small self-contained units. A review like "she is rude and never answers emails" makes complete sense on its own — it doesn't need the review before or after it for context. Fixed-size splitting (e.g. every 500 chars) would cut reviews in half and merge the end of one student's review with the start of another's, which is exactly the kind of thing that breaks retrieval.

To make each chunk fully standalone I prepend a small context line to the review text: `Professor <name> (<dept>), course <course>, <date>, rated <quality>/5:`. That way even a one-sentence review still carries who/what it's about when it gets retrieved.

This produced **310 chunks** across the 10 files, which is comfortably inside the recommended 50–2,000 range.

## Retrieval Approach

- **Embedding model:** `all-MiniLM-L6-v2` via sentence-transformers. It runs locally with no API key and no rate limits, which is perfect for a class project, and it's fast enough to embed all 310 chunks in a couple seconds.
- **Vector store:** ChromaDB (local, persistent), set to **cosine distance** so the scores are easy to read (0 = identical, lower = more similar). Chroma's default is squared-L2 which gives weird-looking numbers.
- **top-k:** 5. Each review is short, so one chunk usually isn't enough context — pulling 5 lets the LLM see a few different students' opinions and find the consensus. Going much higher (like 15) started dragging in loosely related reviews that pull the answer off-topic.
- **If cost wasn't a constraint:** for a real deployment I'd think about a bigger embedding model with a longer context window (so longer reviews don't get truncated), and possibly one tuned for short opinion text. all-MiniLM is general-purpose. I'd also weigh API models (like OpenAI's text-embedding-3) for accuracy vs. the privacy/no-rate-limit benefit of keeping it local. Latency matters too — a local model has no network round-trip.

Semantic search works here even when the query doesn't share exact words with a review because the embeddings capture meaning — "is she responsive?" lands near "never answers emails" even though they share no words.

## Evaluation Plan

| # | Question | Expected answer |
|---|----------|-----------------|
| 1 | What do students say about Professor Steele's responsiveness to emails? | She's rude and doesn't answer emails; redirects students to a TA who also doesn't respond. |
| 2 | Is Professor Sammie Johnson well regarded? Would students take him again? | Yes — extremely high rating (~4.9/5), reviews say he cares, explains well, would take again. |
| 3 | Does Professor Steele reopen assignments, and when? | Yes, around the midterm and final periods. |
| 4 | How does Professor Ashton Brice grade and treat students? | Easy grader, gives extra credit, described as kind, funny, relatable, flexible with extensions. |
| 5 | Which professors give extra credit? | At least 7 professors' reviews mention extra credit (Brice, Brown, Enurah, Fuller, Morales, Rahman, Steele). |

Q5 is intentionally the hardest because it asks the system to aggregate across every professor's reviews, which is where I expect semantic retrieval to fall short.

## Anticipated Challenges

1. **Aggregation questions.** Questions like "which professors give extra credit?" ask the system to pull together info across many documents. Semantic search returns the chunks most similar to the query, not a complete list across every professor, so these come back incomplete. (This turned out to be my real failure case.)
2. **Mixed sentiment per professor.** A professor can have both 5-star and 1-star reviews. If retrieval happens to grab mostly one side, the answer can look more one-sided than the full review set actually is.
3. **Buried keywords.** Things like "Extra credit." show up as short tags at the end of lots of reviews, which confuses similarity for queries built around that phrase.

## AI Tool Plan

I used Claude to help implement the pipeline. Specifically:
- Gave it my chunking strategy (one-review-per-chunk, 800 char cap) and had it write the `ingest.py` parser that splits on `---` and prepends the professor context line.
- Had it write the ChromaDB embedding/indexing code and the retrieval function, then I checked the distance scores myself and asked it to switch from L2 to cosine when the raw numbers looked off.
- Had it write the grounding prompt for the LLM and the Gradio interface.
- I reviewed everything it produced, ran each stage to verify the output, and adjusted (e.g. the cosine fix, confirming chunk counts, picking the eval questions from reviews I actually read).

## Architecture

```
  10 .txt review files
          |
          v
  [ Ingestion + Cleaning ]   ingest.py  (split on ---, strip html, prepend context)
          |
          v
  [ Chunking ]               one review per chunk, ~800 char cap, 310 chunks
          |
          v
  [ Embedding ]              all-MiniLM-L6-v2  (sentence-transformers, local)
          |
          v
  [ Vector Store ]           ChromaDB  (cosine distance, persistent)
          |
          v
  [ Retrieval ]              top-k=5 semantic search        query.py
          |
          v
  [ Generation ]             Groq llama-3.3-70b-versatile  (grounded, cites sources)
          |
          v
  [ Gradio UI ]              app.py  ->  http://localhost:7860
```
