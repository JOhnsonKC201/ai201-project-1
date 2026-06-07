# Loads the RateMyProfessors .txt files and turns them into chunks.
# Each review becomes its own chunk since reviews are basically self-contained
# opinions. I prepend the professor + course info so a chunk still makes sense
# on its own when it gets retrieved later.

import os
import re
import glob
import html

REVIEWS_DIR = os.path.join(os.path.dirname(__file__), "..", "reviews txt files")

# all-MiniLM-L6-v2 only looks at ~256 tokens (~1000 chars) so I cap chunks a
# little under that. Most reviews are way shorter than this anyway.
MAX_CHARS = 800
OVERLAP = 100   # only matters when one review is longer than MAX_CHARS


def clean_text(text):
    # the files are pretty clean already but just in case there's leftover
    # html entities or tags from copy/paste, strip them out
    text = html.unescape(text)
    text = re.sub(r"<[^>]+>", "", text)
    text = re.sub(r"[ \t]+", " ", text)
    return text.strip()


def parse_header(header):
    # pull the professor name / department out of the top block
    def grab(field):
        m = re.search(field + r":\s*(.+)", header)
        return m.group(1).strip() if m else ""

    prof = grab("Professor")
    dept = grab("Department")
    # department line looks like "Computer Science, Morgan State University"
    dept = dept.split(",")[0].strip()
    return prof, dept


def parse_review_meta(meta_line):
    # the line that looks like: Quality: 5.0 | Difficulty: 4.0 | Course: COSC110 | Date: ...
    def grab(field):
        m = re.search(field + r":\s*([^|]+)", meta_line)
        return m.group(1).strip() if m else ""

    return {
        "course": grab("Course"),
        "date": grab("Date"),
        "quality": grab("Quality"),
    }


def split_long(text):
    # fallback for the rare review that's too long for the embedder.
    # split on sentences and pack them into windows with a little overlap.
    sentences = re.split(r"(?<=[.!?])\s+", text)
    chunks = []
    cur = ""
    for s in sentences:
        if len(cur) + len(s) > MAX_CHARS and cur:
            chunks.append(cur.strip())
            cur = cur[-OVERLAP:] + " " + s
        else:
            cur += " " + s
    if cur.strip():
        chunks.append(cur.strip())
    return chunks


def load_chunks():
    chunks = []
    files = sorted(glob.glob(os.path.join(REVIEWS_DIR, "*.txt")))

    for path in files:
        source = os.path.basename(path)
        with open(path, encoding="utf-8") as f:
            raw = f.read()

        # everything before the first --- is the professor header
        parts = raw.split("---")
        header = parts[0]
        reviews = parts[1:]
        prof, dept = parse_header(header)

        for i, block in enumerate(reviews):
            block = clean_text(block)
            if not block:
                continue

            # first line is the metadata, the rest is the actual review
            lines = block.split("\n", 1)
            meta_line = lines[0]
            body = lines[1].strip() if len(lines) > 1 else ""
            if not body:
                continue

            meta = parse_review_meta(meta_line)
            context = f"Professor {prof} ({dept}), course {meta['course']}, {meta['date']}, rated {meta['quality']}/5:"
            full = context + "\n" + body

            pieces = [full] if len(full) <= MAX_CHARS else split_long(full)
            for j, piece in enumerate(pieces):
                chunks.append({
                    "text": piece,
                    "source": source,
                    "professor": prof,
                    "department": dept,
                    "course": meta["course"],
                    "date": meta["date"],
                    "quality": meta["quality"],
                    "chunk_id": f"{source}-{i}-{j}",
                })

    return chunks


# quick sanity check: python src/ingest.py
if __name__ == "__main__":
    cs = load_chunks()
    print(f"total chunks: {len(cs)}")
    print("\n--- 5 sample chunks ---")
    for c in cs[:5]:
        print(f"\n[{c['source']} | {c['professor']} | {c['course']}]")
        print(c["text"])
