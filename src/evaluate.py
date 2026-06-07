# Runs my 5 evaluation questions through the full system and dumps the
# results to eval_results.md so I can fill in the accuracy judgments in the
# README. Needs the Groq key set in .env.

from query import ask

# question + the answer I expect based on actually reading the reviews
TESTS = [
    {
        "q": "What do students say about Professor Steele's responsiveness to emails?",
        "expected": "Multiple students say she is rude and doesn't respond to emails, "
                    "often redirecting them to a TA who also doesn't answer.",
    },
    {
        "q": "Is Professor Sammie Johnson well regarded? Would students take him again?",
        "expected": "Yes, very highly rated (around 4.9/5) with reviews saying students "
                    "would take him again.",
    },
    {
        "q": "Does Professor Steele reopen assignments, and when?",
        "expected": "Yes, several reviews mention she reopens assignments around the "
                    "midterm and final periods.",
    },
    {
        "q": "How does Professor Ashton Brice grade and treat students?",
        "expected": "Easy grader, gives extra credit, described as kind, funny, relatable "
                    "and understanding about extensions.",
    },
    {
        "q": "Which professors give extra credit?",
        "expected": "At least 7 professors' reviews mention extra credit (Brice, Brown, "
                    "Enurah, Fuller, Morales, Rahman, Steele). This is a cross-document "
                    "aggregation question and I expect the system to struggle with it.",
    },
]

lines = ["# Evaluation Results\n"]
for i, t in enumerate(TESTS, 1):
    print(f"running {i}/{len(TESTS)}: {t['q']}")
    out = ask(t["q"])

    lines.append(f"## Q{i}: {t['q']}\n")
    lines.append(f"**Expected:** {t['expected']}\n")
    lines.append(f"**System answer:** {out['answer']}\n")
    lines.append("**Retrieved chunks:**")
    for h in out["chunks"]:
        m = h["meta"]
        lines.append(f"- dist={h['distance']:.3f} | {m['source']} | Prof. {m['professor']} | {m['course']}")
    lines.append("\n**Accuracy judgment:** _TODO: accurate / partially accurate / inaccurate_\n")

with open("eval_results.md", "w", encoding="utf-8") as f:
    f.write("\n".join(lines))
print("\nwrote eval_results.md")
