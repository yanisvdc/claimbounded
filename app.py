"""HuggingFace Spaces entry point for claimbounded."""

import os

# Set server config via env vars — HF Spaces standard approach
os.environ.setdefault("GRADIO_SERVER_NAME", "0.0.0.0")
os.environ.setdefault("GRADIO_SERVER_PORT", "7860")

from claimbounded.ui import launch

if __name__ == "__main__":
    launch(server_name="0.0.0.0", server_port=7860)
else:
    # Called by HF Spaces via import — env vars handle network config
    launch(server_name="0.0.0.0", server_port=7860)
