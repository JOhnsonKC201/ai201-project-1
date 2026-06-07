# Retrieval + grounded answer generation.
#   retrieve()  -> semantic search over the chroma collection
#   ask()       -> retrieve, then have the LLM answer using ONLY those chunks
#
# You can also run this straight from the terminal to test:
#   python src/query.py "what do students say about professor steele?"

import os
import sys
from dotenv import load_dotenv

from index import get_model, get_collection

load_dotenv()

TOP_K = 5

# Strong grounding prompt. The whole point is the model answers from the
# retrieved reviews and NOT from whatever it already knows about professors.
SYSTEM_PROMPT = """You are The Unofficial Guide, a tool that answers questions about Morgan State University professors using real student reviews.

Rules:
- Only use the reviews provided in the CONTEXT below. Do not use any outside knowledge.
- If the context doesn't contain enough information to answer, reply exactly: "I don't have enough information on that."
- Mention the professor by name and summarize what students actually said.
- Do not invent ratings, quotes, or details that aren't in the context."""


def retrieve(query, k=TOP_K):
    model = get_model()
    col = get_collection()
    q_emb = model.encode([query]).tolist()
    res = col.query(query_embeddings=q_emb, n_results=k)

    hits = []
    for i in range(len(res["documents"][0])):
        hits.append({
            "text": res["documents"][0][i],
            "meta": res["metadatas"][0][i],
            "distance": res["distances"][0][i],
        })
    return hits


def build_context(hits):
    blocks = []
    for i, h in enumerate(hits, 1):
        m = h["meta"]
        blocks.append(f"[{i}] (from {m['source']}, Prof. {m['professor']})\n{h['text']}")
    return "\n\n".join(blocks)


def ask(query, k=TOP_K):
    from groq import Groq

    hits = retrieve(query, k)
    context = build_context(hits)

    client = Groq(api_key=os.getenv("GROQ_API_KEY"))
    resp = client.chat.completions.create(
        model="llama-3.3-70b-versatile",
        temperature=0,   # keep it factual / repeatable
        messages=[
            {"role": "system", "content": SYSTEM_PROMPT},
            {"role": "user", "content": f"CONTEXT:\n{context}\n\nQUESTION: {query}"},
        ],
    )
    answer = resp.choices[0].message.content.strip()

    # build the source list ourselves so attribution is guaranteed, not
    # something we have to trust the LLM to remember to add
    seen = []
    for h in hits:
        tag = f"{h['meta']['source']} (Prof. {h['meta']['professor']})"
        if tag not in seen:
            seen.append(tag)

    # don't show sources if the model couldn't actually answer
    if "don't have enough information" in answer.lower():
        seen = []

    return {"answer": answer, "sources": seen, "chunks": hits}


if __name__ == "__main__":
    q = " ".join(sys.argv[1:]) or "what do students say about professor steele?"
    out = ask(q)
    print("Q:", q)
    print("\nANSWER:\n", out["answer"])
    print("\nSOURCES:")
    for s in out["sources"]:
        print(" -", s)
