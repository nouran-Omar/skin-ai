"""Gradio Server entrypoint for SkinAI's FastAPI API and ZeroGPU inference."""

# Import spaces before torch or any project module that imports torch.
import spaces

import os
from typing import Any

import gradio as gr
import numpy as np

from backend.app import main as api_module
from backend.app.inference import get_predictor


# Load checkpoint weights onto CPU, then register `.to("cuda")` at module scope
# so ZeroGPU can pack the model. Do not load safetensors directly onto CUDA.
predictor = get_predictor()
if not predictor.demo:
    import torch

    predictor.model.to("cuda" if torch.cuda.is_available() else "cpu")
    predictor.device = next(predictor.model.parameters()).device


app = gr.Server()
api_routes = list(api_module.app.router.routes)
app.router.routes[0:0] = api_routes
for middleware in reversed(api_module.app.user_middleware):
    app.add_middleware(middleware.cls, *middleware.args, **middleware.kwargs)
app.exception_handlers.update(api_module.app.exception_handlers)
app.router.lifespan_context = api_module.app.router.lifespan_context


@app.api(name="zero_gpu_predict")
@spaces.GPU(duration=30)
def zero_gpu_predict(rgb: np.ndarray, mode: str = "summary") -> dict[str, Any]:
    """Run a prediction inside a ZeroGPU lease.

    `full` is used by FastAPI and contains arrays required for its report and
    visualization routes. `summary` is JSON-safe for the Gradio API.
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

if __name__ == "__main__":
    # Server mode is designed for external React frontends plus custom
    # FastAPI routes, while keeping Gradio's ZeroGPU integration available.
    app.launch(server_name="0.0.0.0", server_port=int(os.getenv("APP_PORT") or "7860"))
