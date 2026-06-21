"""HuggingFace Spaces entry point for claimbounded.

Deploy to HuggingFace Spaces:
  1. Create a new Space at huggingface.co/new-space (SDK: Gradio)
  2. Push this repo — HF Spaces auto-detects app.py and requirements.txt
  3. The Space URL becomes your shareable one-click link

No Python install needed for end users — they just open the URL.
"""

from claimbounded.ui import launch

# server_name="0.0.0.0" required for HuggingFace Spaces networking
launch(server_name="0.0.0.0", server_port=7860)
