"""HuggingFace Spaces entry point for claimbounded.

Exposes ``demo`` at module level so HuggingFace's Gradio SDK can find it,
then launches with server_name="0.0.0.0" so the health checker can reach it.
"""

from claimbounded.ui import build_demo

# Build demo at module level — HF Gradio SDK imports this file and looks for 'demo'
demo = build_demo()

demo.launch(
    server_name="0.0.0.0",   # required for HF health checker
    server_port=7860,
    inbrowser=False,
    show_error=True,
)
