#!/usr/bin/env python3
"""
embed.py — Embed all chunks and load them into ChromaDB.

Reads documents/chunks.json (produced by chunk.py), encodes each chunk
with all-MiniLM-L6-v2, and upserts vectors + metadata into a persistent
ChromaDB collection at ./chroma_db/.

Usage:
  python embed.py           # embed and store all chunks
  python embed.py --reset   # drop the collection first, then re-embed
"""

import json
import sys
from pathlib import Path

import chromadb
from sentence_transformers import SentenceTransformer

CHUNKS_PATH = Path("documents/chunks.json")
CHROMA_DIR = Path("chroma_db")
COLLECTION_NAME = "trojans"
MODEL_NAME = "all-MiniLM-L6-v2"
BATCH_SIZE = 64


def load_chunks() -> list[dict]:
    if not CHUNKS_PATH.exists():
        print(f"ERROR: {CHUNKS_PATH} not found. Run python chunk.py first.", file=sys.stderr)
        sys.exit(1)
    chunks = json.loads(CHUNKS_PATH.read_text(encoding="utf-8"))
    print(f"Loaded {len(chunks)} chunks from {CHUNKS_PATH}")
    return chunks


def make_chunk_id(chunk: dict, idx: int) -> str:
    source = chunk["metadata"].get("source_file", "unknown").replace(".", "_")
    chunk_index = chunk["metadata"].get("chunk_index", idx)
    return f"{source}__{chunk_index}"


def sanitize_metadata(meta: dict) -> dict:
    # ChromaDB requires metadata values to be str, int, float, or bool
    return {k: str(v) for k, v in meta.items()}


def main() -> None:
    reset = "--reset" in sys.argv

    chunks = load_chunks()

    print(f"Loading embedding model: {MODEL_NAME} ...")
    model = SentenceTransformer(MODEL_NAME)

    client = chromadb.PersistentClient(path=str(CHROMA_DIR))

    if reset:
        try:
            client.delete_collection(COLLECTION_NAME)
            print(f"Dropped existing collection '{COLLECTION_NAME}'.")
        except Exception:
            pass

    collection = client.get_or_create_collection(
        name=COLLECTION_NAME,
        metadata={"hnsw:space": "cosine"},
    )

    texts = [c["text"] for c in chunks]
    ids = [make_chunk_id(c, i) for i, c in enumerate(chunks)]
    metadatas = [sanitize_metadata(c["metadata"]) for c in chunks]

    print(f"Embedding {len(texts)} chunks in batches of {BATCH_SIZE} ...")
    all_embeddings: list[list[float]] = []
    for start in range(0, len(texts), BATCH_SIZE):
        batch = texts[start : start + BATCH_SIZE]
        vecs = model.encode(batch, show_progress_bar=False).tolist()
        all_embeddings.extend(vecs)
        print(f"  Encoded {min(start + BATCH_SIZE, len(texts))} / {len(texts)}")

    print("Upserting into ChromaDB ...")
    for start in range(0, len(texts), BATCH_SIZE):
        collection.upsert(
            ids=ids[start : start + BATCH_SIZE],
            embeddings=all_embeddings[start : start + BATCH_SIZE],
            documents=texts[start : start + BATCH_SIZE],
            metadatas=metadatas[start : start + BATCH_SIZE],
        )

    count = collection.count()
    print(f"\nDone. Collection '{COLLECTION_NAME}' now has {count} vectors.")
    print(f"ChromaDB persisted at: {CHROMA_DIR.resolve()}")
    print("Next step: run  python retrieve.py  to test retrieval.")


if __name__ == "__main__":
    main()
