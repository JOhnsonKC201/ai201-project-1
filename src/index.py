# Embeds all the chunks with a local sentence-transformers model and stores
# them in ChromaDB. Run this once (python src/index.py) to build the database
# before querying. all-MiniLM-L6-v2 runs on my laptop, no API key needed.

import os
from sentence_transformers import SentenceTransformer
import chromadb

from ingest import load_chunks

DB_PATH = os.path.join(os.path.dirname(__file__), "..", "chroma_db")
COLLECTION = "professor_reviews"
MODEL_NAME = "all-MiniLM-L6-v2"

# load the model once and reuse it
_model = None
def get_model():
    global _model
    if _model is None:
        _model = SentenceTransformer(MODEL_NAME)
    return _model


def get_collection():
    client = chromadb.PersistentClient(path=DB_PATH)
    return client.get_or_create_collection(COLLECTION)


def build_index():
    chunks = load_chunks()
    print(f"loaded {len(chunks)} chunks")

    client = chromadb.PersistentClient(path=DB_PATH)
    # wipe and rebuild so re-running doesn't pile up duplicates
    try:
        client.delete_collection(COLLECTION)
    except Exception:
        pass
    # use cosine distance instead of chroma's default (squared L2) so the
    # scores are easy to read: 0 = identical, smaller = more similar
    col = client.create_collection(COLLECTION, metadata={"hnsw:space": "cosine"})

    model = get_model()
    texts = [c["text"] for c in chunks]
    print("embedding... (this takes a few seconds)")
    embeddings = model.encode(texts, show_progress_bar=True).tolist()

    # chroma metadata can't hold None so make sure everything is a string
    metadatas = []
    for c in chunks:
        metadatas.append({
            "source": c["source"],
            "professor": c["professor"],
            "course": c["course"],
            "date": c["date"],
            "quality": c["quality"],
        })

    col.add(
        ids=[c["chunk_id"] for c in chunks],
        documents=texts,
        embeddings=embeddings,
        metadatas=metadatas,
    )
    print(f"done. {col.count()} chunks in the '{COLLECTION}' collection.")


if __name__ == "__main__":
    build_index()
