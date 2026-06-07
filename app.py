# Simple Gradio web UI for The Unofficial Guide.
# Run with:  python app.py   then open http://localhost:7860

import sys, os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "src"))

import gradio as gr
from query import ask


def handle_query(question):
    if not question.strip():
        return "Ask me something about a Morgan State professor.", ""
    result = ask(question)
    sources = "\n".join(f"• {s}" for s in result["sources"])
    return result["answer"], sources


with gr.Blocks(title="The Unofficial Guide") as demo:
    gr.Markdown("# The Unofficial Guide")
    gr.Markdown("Ask about Morgan State University professors — answers come straight from real student reviews.")

    inp = gr.Textbox(label="Your question", placeholder="e.g. Is Professor Steele responsive to emails?")
    btn = gr.Button("Ask", variant="primary")
    answer = gr.Textbox(label="Answer", lines=8)
    sources = gr.Textbox(label="Retrieved from", lines=4)

    btn.click(handle_query, inputs=inp, outputs=[answer, sources])
    inp.submit(handle_query, inputs=inp, outputs=[answer, sources])


if __name__ == "__main__":
    demo.launch()
