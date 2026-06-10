#!/usr/bin/env python3
"""
app.py — Gradio web UI for Ask the Trojans.

Usage:
  python app.py
  then open http://localhost:7860
"""

import gradio as gr
from generate import ask


def handle_query(question: str):
    question = question.strip()
    if not question:
        return "Please enter a question.", ""
    result = ask(question)
    sources_text = "\n".join(f"• {s}" for s in result["sources"])
    return result["answer"], sources_text


with gr.Blocks(title="Ask the Trojans") as demo:
    gr.Markdown("## Ask the Trojans\nAsk anything about USC CS professors. Answers come only from scraped student reviews.")

    inp = gr.Textbox(
        label="Your question",
        placeholder="e.g. What do students say about Bill Cheng's grading in CSCI 402?",
        lines=2,
    )
    btn = gr.Button("Ask", variant="primary")

    answer = gr.Textbox(label="Answer", lines=10)
    sources = gr.Textbox(label="Retrieved from", lines=5)

    btn.click(handle_query, inputs=inp, outputs=[answer, sources])
    inp.submit(handle_query, inputs=inp, outputs=[answer, sources])

if __name__ == "__main__":
    demo.launch()
