#!/usr/bin/env python3
"""
retrieve.py — Query the ChromaDB vector store for relevant chunks.

Exposes a query() function for use by generate.py, and a __main__
block for interactive testing against the 5 evaluation plan queries.

Usage:
  python retrieve.py                      # run all 5 evaluation queries
  python retrieve.py "your question here" # run a single custom query
"""

import sys
from pathlib import Path

import chromadb
from sentence_transformers import SentenceTransformer

CHROMA_DIR = Path("chroma_db")
COLLECTION_NAME = "trojans"
MODEL_NAME = "all-MiniLM-L6-v2"

# Module-level singletons so repeated calls within a process skip re-loading
_model: SentenceTransformer | None = None
_collection = None


def _get_model() -> SentenceTransformer:
    global _model
    if _model is None:
        _model = SentenceTransformer(MODEL_NAME)
    return _model


def _get_collection():
    global _collection
    if _collection is None:
        if not CHROMA_DIR.exists():
            raise RuntimeError(
                f"ChromaDB store not found at '{CHROMA_DIR}'. Run python embed.py first."
            )
        client = chromadb.PersistentClient(path=str(CHROMA_DIR))
        _collection = client.get_collection(COLLECTION_NAME)
    return _collection


def query(question: str, k: int = 5) -> list[dict]:
    """
    Embed question and return the top-k most similar chunks.

    Each returned dict contains:
      text      — the chunk text
      metadata  — dict with source_file, professor, course, url, chunk_index, ...
      distance  — cosine distance (0 = identical, 1 = orthogonal; lower is better)
    """
    embedding = _get_model().encode(question).tolist()
    results = _get_collection().query(
        query_embeddings=[embedding],
        n_results=k,
        include=["documents", "metadatas", "distances"],
    )

    return [
        {"text": doc, "metadata": meta, "distance": dist}
        for doc, meta, dist in zip(
            results["documents"][0],
            results["metadatas"][0],
            results["distances"][0],
        )
    ]


def _print_results(question: str, hits: list[dict]) -> None:
    print(f"\n{'=' * 70}")
    print(f"Query: {question}")
    print(f"{'=' * 70}")
    for i, hit in enumerate(hits, 1):
        m = hit["metadata"]
        print(f"\n[{i}] distance={hit['distance']:.4f}")
        print(f"    Professor : {m.get('professor', '?')}")
        print(f"    Course    : {m.get('course', '?')}")
        print(f"    Source    : {m.get('source_file', '?')}")
        print(f"    URL       : {m.get('url', '?')}")
        print()
        preview = hit["text"][:400].replace("\n", "\n    ")
        print(f"    {preview}")
        if len(hit["text"]) > 400:
            print("    [...]")


EVAL_QUERIES = [
    "What do students say about Bill Cheng's grading in CSCI 402 (Operating Systems)?",
    "Is Mark Redekopp a good professor for students who are new to programming?",
    "How much homework does Andrew Goodney typically assign in his CS courses?",
    "What is the general student opinion of Saty Raghavachary's teaching style in CSCI 585 (Database Systems)?",
    "Which USC CS professors are most praised for being available and helpful outside of class?",
]


def main() -> None:
    queries = [" ".join(sys.argv[1:])] if len(sys.argv) > 1 else EVAL_QUERIES
    for q in queries:
        hits = query(q, k=5)
        _print_results(q, hits)


if __name__ == "__main__":
    main()
