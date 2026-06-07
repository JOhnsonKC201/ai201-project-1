# Quick check that retrieval is actually pulling relevant chunks, BEFORE
# wiring up the LLM. No API key needed. Prints the top chunks + distance
# scores for a few of my eval questions so I can eyeball them.

from query import retrieve

QUERIES = [
    "what do students say about professor steele's emails?",
    "is professor sammie johnson a good teacher?",
    "which professors give extra credit?",
]

for q in QUERIES:
    print("=" * 70)
    print("QUERY:", q)
    hits = retrieve(q, k=4)
    for h in hits:
        m = h["meta"]
        print(f"\n  dist={h['distance']:.3f}  [{m['source']} | {m['professor']} | {m['course']}]")
        # just the review body, trimmed
        body = h["text"].split("\n", 1)[-1]
        print("  " + body[:180] + ("..." if len(body) > 180 else ""))
    print()
