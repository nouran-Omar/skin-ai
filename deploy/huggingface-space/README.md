---
title: SkinAI Backend
sdk: gradio
python_version: "3.12"
app_file: app.py
short_description: Bilingual skin lesion pre-screening API and model demo
---

# SkinAI Backend (Hugging Face Spaces)

This bundle serves the existing FastAPI routes through a Gradio Space and adds
a small ZeroGPU model check. It includes `models/best.pt` (43 MB).

## Publish to the Space

Copy the **contents** of this directory into the clone of
`nouranomar/skin-ai-backend`, preserving the `backend/`, `ml/`, and `models/`
directories. Use Git LFS for `models/best.pt` if uploading with Git.

In Space Settings, choose the Gradio SDK, Python 3.12, and ZeroGPU hardware.
The runtime supplies the compatible PyTorch 2.8+ build, Gradio, and `spaces`;
`requirements.txt` pins the matching torchvision package without replacing the
managed Torch build.

Set these Space secrets/variables before launch:

- `SKINAI_ENV=production`
- `SKINAI_JWT_SECRET`: a long, random secret
- `SKINAI_COOKIE_SECURE=true`
- `SKINAI_CORS=https://skin-ai-psi-two.vercel.app`
- Optional generative chat: `HF_TOKEN` (Inference Providers permission) and `SKINAI_ASSISTANT_MODEL` (a supported chat-completion model ID)

Assistant retrieval and source-linked answers work without a model token. The
frontend sends a chat message and recent turns to Hugging Face only after the
visitor explicitly checks the optional generation control; greetings and
small talk remain local. Do not enable this for a deployment unless its privacy
notice explains that opted-in questions are processed by the selected provider.

The Vercel frontend proxies `/api/*` to
`https://nouranomar-skin-ai-backend.hf.space/api/*`. Check `/api/health`, login,
analysis, chatbot, progress, acne guide, and PDF routes after the Space starts.
The assistant retrieves from a small local English/Arabic set of curated,
source-linked dermatology guidance and can optionally synthesize a grounded
reply through Hugging Face Inference Providers. Provider failures fall back to
the local retrieved answer.

Hugging Face Spaces local storage is ephemeral. Account/history data in the
included SQLite store may be lost when the Space is restarted or rebuilt. Use
an external durable database before treating saved history as persistent.

## Local launch

Install compatible ZeroGPU dependencies in an appropriate Python 3.12
environment, then run `python app.py`. The hosted ZeroGPU GPU callback itself
cannot be fully validated outside Hugging Face's runtime.
