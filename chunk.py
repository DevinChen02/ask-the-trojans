#!/usr/bin/env python3
"""
chunk.py — Split scraped documents into retrieval-ready chunks.

Reads every .txt file in documents/, applies LangChain's
RecursiveCharacterTextSplitter (chunk_size=500, overlap=100),
drops fragments under 80 characters, and saves the result to
documents/chunks.json as a list of {text, metadata} dicts.

Usage:
  python chunk.py          # chunk all .txt files
  python chunk.py --sample # print 5 sample chunks and exit (no save)
"""

import json
import re
import sys
from pathlib import Path

from langchain_text_splitters import RecursiveCharacterTextSplitter

DOCUMENTS_DIR = Path(__file__).parent / "documents"
OUTPUT_PATH = DOCUMENTS_DIR / "chunks.json"

CHUNK_SIZE = 500      # characters — captures 2-4 short reviews per chunk
CHUNK_OVERLAP = 100   # characters — prevents a review from being silently split at boundaries
MIN_CHUNK_LEN = 80    # characters — discard bare metadata headers and stray punctuation

# Matches tags written by scrape.py, e.g. [Professor: Bill Cheng]
_META_RE = re.compile(r"\[([A-Za-z][A-Za-z _]+):\s*([^\]]+)\]")


def extract_file_metadata(content: str) -> dict:
    """Pull metadata tags from the first line of a scraped document."""
    first_line = content.split("\n", 1)[0]
    meta = {}
    for key, val in _META_RE.findall(first_line):
        meta[key.strip().lower().replace(" ", "_")] = val.strip()
    return meta


def extract_chunk_metadata(chunk_text: str, base_meta: dict) -> dict:
    """
    Merge base file metadata with any tags found inside the chunk itself.
    Inline tags take precedence, so a chunk that starts with
    [Professor: Bill Cheng] overrides a base file that covers multiple professors.
    """
    meta = dict(base_meta)
    for key, val in _META_RE.findall(chunk_text):
        meta[key.strip().lower().replace(" ", "_")] = val.strip()
    return meta


def load_documents() -> list[tuple[str, str]]:
    """Return [(filename, content)] for every non-empty .txt in documents/."""
    docs = []
    for path in sorted(DOCUMENTS_DIR.glob("*.txt")):
        content = path.read_text(encoding="utf-8").strip()
        if content:
            docs.append((path.name, content))
    return docs


def chunk_documents(docs: list[tuple[str, str]]) -> list[dict]:
    """
    Apply RecursiveCharacterTextSplitter to each document.
    Separators are ordered from coarsest to finest so the splitter
    prefers paragraph breaks over mid-sentence cuts.
    """
    splitter = RecursiveCharacterTextSplitter(
        chunk_size=CHUNK_SIZE,
        chunk_overlap=CHUNK_OVERLAP,
        length_function=len,
        separators=["\n\n", "\n", ". ", " ", ""],
    )

    chunks = []
    for filename, content in docs:
        base_meta = extract_file_metadata(content)
        base_meta["source_file"] = filename

        raw_chunks = splitter.split_text(content)

        kept = discarded = 0
        for i, raw in enumerate(raw_chunks):
            text = raw.strip()
            if len(text) < MIN_CHUNK_LEN:
                discarded += 1
                continue
            meta = extract_chunk_metadata(text, base_meta)
            meta["chunk_index"] = i
            chunks.append({"text": text, "metadata": meta})
            kept += 1

        print(f"  {filename}: {kept} chunks kept, {discarded} discarded (< {MIN_CHUNK_LEN} chars)")

    return chunks


def print_sample_chunks(chunks: list[dict], n: int = 5) -> None:
    """Print n evenly spaced chunks for manual inspection."""
    if not chunks:
        print("No chunks to display.")
        return

    step = max(1, len(chunks) // n)
    samples = [chunks[min(i * step, len(chunks) - 1)] for i in range(n)]

    print(f"\n{'=' * 60}")
    print(f"SAMPLE CHUNKS  (from {len(chunks)} total)")
    print(f"{'=' * 60}")
    for idx, chunk in enumerate(samples, 1):
        m = chunk["metadata"]
        print(f"\n--- Chunk {idx} ---")
        print(f"File    : {m.get('source_file', '?')}")
        print(f"Professor: {m.get('professor', '?')}   Course: {m.get('course', '?')}")
        print(f"Length  : {len(chunk['text'])} chars")
        print()
        print(chunk["text"])
    print(f"\n{'=' * 60}")


def print_stats(chunks: list[dict]) -> None:
    lengths = [len(c["text"]) for c in chunks]
    print(f"\nTotal chunks : {len(chunks)}")
    print(f"Min length   : {min(lengths)} chars")
    print(f"Max length   : {max(lengths)} chars")
    print(f"Avg length   : {sum(lengths) // len(lengths)} chars")

    if len(chunks) < 50:
        print("\nWARNING: Fewer than 50 chunks — chunks may be too large or documents too sparse.")
        print("         Consider reducing chunk_size or scraping more sources.")
    elif len(chunks) > 2000:
        print("\nWARNING: More than 2000 chunks — consider increasing chunk_size.")
    else:
        print(f"\nChunk count looks healthy ({len(chunks)} chunks in the 50–2000 range).")


def main() -> None:
    sample_only = "--sample" in sys.argv

    print("Loading documents from documents/ ...")
    docs = load_documents()
    if not docs:
        print("No .txt files found. Run  python scrape.py  first.", file=sys.stderr)
        sys.exit(1)

    print(f"Loaded {len(docs)} document(s):\n  " + "\n  ".join(f for f, _ in docs))
    print(f"\nChunking  (size={CHUNK_SIZE}, overlap={CHUNK_OVERLAP}, min_len={MIN_CHUNK_LEN}) ...")

    chunks = chunk_documents(docs)

    if not chunks:
        print("No chunks produced. Check that your documents contain substantive text.", file=sys.stderr)
        sys.exit(1)

    print_stats(chunks)
    print_sample_chunks(chunks)

    if not sample_only:
        OUTPUT_PATH.write_text(
            json.dumps(chunks, indent=2, ensure_ascii=False), encoding="utf-8"
        )
        print(f"\nChunks saved to {OUTPUT_PATH}")
        print("Next step: run  python embed.py  (Milestone 4)")


if __name__ == "__main__":
    main()
