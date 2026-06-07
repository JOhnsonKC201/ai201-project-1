# Gradio web UI for The Unofficial Guide.
# Run with:  python app.py   then open http://localhost:7860

import sys, os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "src"))

import gradio as gr
from query import ask


def handle_query(question):
    if not question.strip():
        return "Type a question above and hit Ask.", "_No sources yet._"

    result = ask(question)
    answer = result["answer"]

    if result["sources"]:
        sources = "\n".join(f"- 📄 **{s}**" for s in result["sources"])
    else:
        # happens on the refusal / out-of-scope case
        sources = "_No matching reviews — the system declined to answer._"

    return answer, sources


# Morgan State colors are blue + orange, so I themed it around that
theme = gr.themes.Soft(
    primary_hue="orange",
    secondary_hue="blue",
    neutral_hue="slate",
    font=[gr.themes.GoogleFont("Inter"), "system-ui", "sans-serif"],
)

css = """
.gradio-container { max-width: 860px !important; margin: auto !important; }
#title { text-align: center; margin-bottom: 0; }
#subtitle { text-align: center; color: #64748b; margin-top: 4px; }
#answer-box textarea { font-size: 16px; line-height: 1.6; }
footer { visibility: hidden; }
"""

EXAMPLES = [
    "Is Professor Steele responsive to emails?",
    "Is Sammie Johnson a good professor?",
    "Does Professor Brice give extra credit?",
    "Which professors give extra credit?",
    "What's the parking like at the law school?",
]

with gr.Blocks(theme=theme, css=css, title="The Unofficial Guide") as demo:
    gr.Markdown("# 🎓 The Unofficial Guide", elem_id="title")
    gr.Markdown(
        "The stuff the course catalog won't tell you — answered straight from real "
        "Morgan State student reviews, with sources.",
        elem_id="subtitle",
    )

    with gr.Row():
        inp = gr.Textbox(
            label="Your question",
            placeholder="e.g. Is Professor Steele responsive to emails?",
            scale=5,
            autofocus=True,
        )
    with gr.Row():
        btn = gr.Button("Ask", variant="primary", scale=1)

    gr.Examples(examples=EXAMPLES, inputs=inp, label="Try one of these")

    answer = gr.Textbox(label="Answer", lines=7, elem_id="answer-box")
    gr.Markdown("**Retrieved from**")
    sources = gr.Markdown(value="_No sources yet._")
    gr.Markdown("<sub>Answers are grounded only in retrieved reviews. If the reviews "
                "don't cover it, the system says so instead of guessing.</sub>")

    btn.click(handle_query, inputs=inp, outputs=[answer, sources])
    inp.submit(handle_query, inputs=inp, outputs=[answer, sources])


if __name__ == "__main__":
    demo.launch()
