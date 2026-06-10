#!/usr/bin/env python3
"""
generate.py — Grounded generation using Groq + retrieved chunks.

Exposes ask() for use by app.py and a __main__ block for CLI testing.

Usage:
  python generate.py "your question here"
  python generate.py          # runs all 5 evaluation queries
"""

import os
import sys
from pathlib import Path

from dotenv import load_dotenv
from groq import Groq

from retrieve import query as retrieve_chunks, EVAL_QUERIES

load_dotenv()

MODEL = "llama-3.3-70b-versatile"

_client: Groq | None = None


def _get_client() -> Groq:
    global _client
    if _client is None:
        api_key = os.getenv("GROQ_API_KEY")
        if not api_key:
            raise RuntimeError("GROQ_API_KEY not set. Add it to your .env file.")
        _client = Groq(api_key=api_key)
    return _client


SYSTEM_PROMPT = """\
You are a USC professor review assistant. Your job is to answer student questions about USC CS professors using ONLY the review excerpts provided in the user message.

STRICT RULES — you must follow every one of them:
1. Answer ONLY from the text in the "Retrieved context" block below the question.
2. Do NOT use any information from your training data, general knowledge, or assumptions.
3. If the retrieved context does not contain enough information to answer the question, respond with this exact sentence and nothing else: "I don't have enough information on that."
4. Do NOT speculate, generalize, or hedge with phrases like "typically," "generally," or "it is likely" unless those exact words appear in the retrieved text.
5. Do NOT fabricate professor names, course numbers, or review sentiment.
6. Cite the source document name in parentheses after each claim you make, e.g., (rmp_bill_cheng.txt). Every factual sentence must have a citation.
"""


def _build_context_block(chunks: list[dict]) -> str:
    lines = ["Retrieved context:"]
    for i, chunk in enumerate(chunks, 1):
        m = chunk["metadata"]
        professor = m.get("professor", "Unknown")
        source_file = m.get("source_file", "unknown_source")
        course = m.get("course", "")
        url = m.get("url", "")
        header = f"[{i}] Source: {source_file}"
        if professor:
            header += f" | Professor: {professor}"
        if course:
            header += f" | Course: {course}"
        if url:
            header += f" | URL: {url}"
        lines.append(header)
        lines.append(chunk["text"])
        lines.append("")
    return "\n".join(lines)


def ask(question: str, k: int = 5) -> dict:
    """
    Retrieve top-k chunks, generate a grounded answer, and return:
      {
        "answer":  str,          # LLM response (must cite sources inline)
        "sources": list[str],    # programmatically extracted source names
      }
    Sources are always appended from retrieved metadata regardless of
    whether the LLM cites them, ensuring attribution is never lost.
    """
    chunks = retrieve_chunks(question, k=k)

    # Programmatically collect sources before calling the LLM so attribution
    # is guaranteed even if the model omits inline citations.
    seen = set()
    ordered_sources = []
    for chunk in chunks:
        m = chunk["metadata"]
        source_file = m.get("source_file", "")
        professor = m.get("professor", "")
        url = m.get("url", "")
        key = source_file
        if key and key not in seen:
            seen.add(key)
            label = source_file
            if professor:
                label += f" (Professor: {professor})"
            if url:
                label += f" — {url}"
            ordered_sources.append(label)

    context_block = _build_context_block(chunks)
    user_message = f"{context_block}\n\nQuestion: {question}"

    response = _get_client().chat.completions.create(
        model=MODEL,
        messages=[
            {"role": "system", "content": SYSTEM_PROMPT},
            {"role": "user", "content": user_message},
        ],
        temperature=0.0,
        max_tokens=1024,
    )

    answer = response.choices[0].message.content.strip()
    return {"answer": answer, "sources": ordered_sources}


def main() -> None:
    queries = [" ".join(sys.argv[1:])] if len(sys.argv) > 1 else EVAL_QUERIES
    for q in queries:
        print(f"\n{'=' * 70}")
        print(f"Query: {q}")
        print("=" * 70)
        result = ask(q)
        print(f"\nAnswer:\n{result['answer']}")
        print("\nSources retrieved:")
        for s in result["sources"]:
            print(f"  • {s}")


if __name__ == "__main__":
    main()
