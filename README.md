My Unofficial Guide is basically everything I wish I had before registering for classes at Morgan State. I went through RateMyProfessors so you don't have to, pulling real student reviews for 10 professors across Computer Science, Information Science, Mathematics, English, and Religion. The course catalog will never tell you a professor doesn't answer emails, or that they curve the midterm, or that they reopen assignments right before the final. That stuff only comes from students who've been there, and finding it usually means scrolling through dozens of reviews hoping someone said the thing you actually needed to know.

Documents
There are 10 files total, one per professor, scraped from RateMyProfessors. Each file has a short header with the professor's name, department, and overall rating. \here are below:

brice_reviews.txt — Ashton Brice (English, ENGL101)
brown_reviews.txt — Leiza Brown (English, ENG102/HUMA201)
dacon_reviews.txt — Jamell Dacon (Computer Science)
enurah_reviews.txt — Nadezhda Enurah (Mathematics)
fuller_reviews.txt — Julian Fuller (Mathematics)
gibson_reviews.txt — Dr. Gibson (Computer Science / Information Science)
johnson_reviews.txt — Sammie Johnson (Information Science / Cybersecurity, CYBR & INSS courses)
morales_reviews.txt — Harold Morales (Religion)
rahman_reviews.txt — Md Rahman (Computer Science)
steele_reviews.txt — Grace Steele (Computer Science, COSC110)
The lineup covers Computer Science, Information Science, Mathematics, English, and Religion, and I intentionally picked a mix of well-rated and poorly-rated professors so the guide doesn't just read like a highlight reel. Some of these reviews are glowing, some are brutal, and that range is kind of the point.

Chunking Strategy
Show more 10:17 PM Each review gets its own chunk. Not split by character count, not merged with adjacent reviews — one student opinion, one chunk. Most reviews are only a sentence or two, so they sit well under the 800 character cap. That cap exists because the embedding model (all-MiniLM-L6-v2) tops out around 256 tokens anyway, so anything longer would just get cut off silently.

No overlap between reviews either. These are separate opinions from different students — overlapping them would just smash two unrelated takes together and confuse retrieval. The only exception is when a single review runs long enough to need sentence-splitting, and even then I use a small 100-character overlap just to keep the split from feeling abrupt.

The reason this works is that reviews are already self-contained. "She never answers emails and grades randomly" makes complete sense on its own. Fixed-size splitting would slice a review mid-sentence and glue the leftover to the next student's opinion, which is exactly how you break a retrieval system. To make each chunk fully standalone, I prepend a short context line before the review text: professor name, department, course, date, and rating. Even a one-liner carries enough context to be useful when it gets retrieved. Ended up with 310 chunks across all 10 files.

Retrieval Approach
I'm using all-MiniLM-L6-v2 through sentence-transformers. It runs fully local, no API key, no rate limits, and it's fast. For a class project that's hard to beat.

Top-k is 5. Too few and the LLM is working off one student's opinion, which might just be someone having a bad week. Too many and you're pulling in reviews that are only vaguely related, which muddies the answer. Five felt like the sweet spot for short opinion text.

Semantic search works here because embeddings capture meaning, not just words. "Is she responsive?" finds "never answers emails" even though they share nothing in common literally. That's the whole reason this approach is worth using over simple keyword search.

If cost wasn't a constraint I'd think hard about a model with a longer context window so longer reviews don't get silently truncated, and probably something trained on opinion or review text rather than a general-purpose model. all-MiniLM is solid but it's not built for this. API models like OpenAI's text-embedding-3 would likely be more accurate, but you'd lose the privacy and zero-latency benefits of keeping everything local. For real users that tradeoff actually matters.

Evaluation Plan
Five test questions, each specific enough to grade as right or wrong.

The first four are straightforward professor lookups: Steele's email responsiveness (short answer: she doesn't, and the TA doesn't either), whether Sammie Johnson is worth taking (yes, 4.9/5, students love him), whether Steele reopens assignments (yes, around midterms and finals), and how Brice grades (easy, extra credit, extensions, generally well-liked).

Question 5 is the one I'm actually curious about. It asks which professors give extra credit, which means the system has to pull relevant chunks from all 10 professors and aggregate them into one answer. Semantic retrieval isn't really built for that. It's good at finding the most similar chunks to a query, not scanning everything and summarizing a pattern across the whole dataset. I'm expecting it to miss some professors or only return the ones whose reviews happened to rank highest in similarity. That's the failure mode worth documenting.

Anticipated Challenges
Three things I expected to go wrong.

Aggregation queries were the biggest one. "Which professors give extra credit?" sounds simple until you realize it's asking the system to scan everything and compile a list. Semantic search doesn't do that. It grabs the 5 most similar chunks and stops, so you get a partial answer that looks complete. That one stung a little because it's such a natural question to ask.

Mixed sentiment was the other real risk. A professor can have glowing reviews and brutal ones in the same file. If retrieval happens to grab mostly one side, the answer is confidently wrong. The system has no way to know it's only seeing half the picture.

The third one I didn't fully anticipate. A lot of reviews end with short tags like "Extra credit." Those fragments score high on similarity for certain queries even though they're basically useless. You pull 5 chunks and half of them just say the words without any real context behind them.

AI Tool Plan
I used Claude for most of the implementation, and I was pretty upfront about that. For ingestion, I gave it my chunking strategy and had it write the parser that splits on --- and prepends the context line. For the vector store, I gave it my retrieval approach section and had it write the ChromaDB indexing and retrieval code. It came back with L2 distance by default, the scores looked wrong, I told it to switch to cosine. Small thing but it would've broken the whole scoring logic if I hadn't caught it. Same process for the grounding prompt and the Gradio interface, both built from the requirements doc.

Architecture
  10 .txt review files
          |
          v
  [ Ingestion + Cleaning ]   ingest.py  (split on ---)
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
  [ Generation ]             Groq llama-3.3 
          |
          v
  [ Gradio UI ]              app.py  ->  http://localhost:7860
