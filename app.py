"""HuggingFace Spaces entry point for claimbounded."""

from claimbounded.ui import build_demo

# demo must be at module level — HF Gradio SDK imports this file and finds it here
demo = build_demo()

if __name__ == "__main__":
    # Only called when running locally: python app.py
    # HF Spaces handles launching itself after finding demo above
    demo.launch()
