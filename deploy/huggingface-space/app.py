"""Gradio Space entrypoint mounting SkinAI's FastAPI API and ZeroGPU smoke check."""

# Import spaces before torch or any project module that imports torch.
import spaces

import os
from typing import Any

import gradio as gr
import numpy as np
import uvicorn

from backend.app import main as api_module
from backend.app.inference import get_predictor


# Load the checkpoint once at startup so ZeroGPU can prepare model weights.
predictor = get_predictor()


@spaces.GPU(duration=30)
def zero_gpu_predict(rgb: np.ndarray, mode: str = "summary") -> dict[str, Any]:
    """Run a prediction inside a ZeroGPU lease.

    `full` is used by FastAPI and contains arrays required for its report and
    visualization routes. `summary` is JSON-safe for the Gradio smoke check.
    """
    if rgb is None:
        raise gr.Error("Upload an image to run the model check.")

    with predictor.lock:
        result = predictor.predict(np.asarray(rgb, dtype=np.uint8))

    if mode == "full":
        return result
    return {
        "model": predictor.info(),
        "details": result["details"],
        "probabilities": {
            name: float(probability)
            for name, probability in zip(predictor.classes, result["probs"])
        },
        "status": "ok",
    }


# FastAPI's existing upload route calls this hook. Keep all validation, auth,
# reports, progress, chat and acne-guide routes in the existing app module.
api_module.predict_rgb = zero_gpu_predict

with gr.Blocks(title="SkinAI model check") as demo:
    gr.Markdown(
        "# SkinAI model check\n"
        "Educational pre-screening support only. This is not a diagnosis."
    )
    image = gr.Image(type="numpy", label="Skin image")
    run_button = gr.Button("Run model check", variant="primary")
    output = gr.JSON(label="Model response")
    run_button.click(fn=zero_gpu_predict, inputs=image, outputs=output)


# The Gradio UI is mounted at the root, alongside every existing /api route.
app = gr.mount_gradio_app(api_module.app, demo, path="/")


if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=int(os.getenv("PORT", "7860")))
