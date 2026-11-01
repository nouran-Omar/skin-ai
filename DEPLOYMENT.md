# SkinAI deployment

## Frontend on Vercel

The repository-root `vercel.json` builds the Vite application in `frontend/`, publishes `frontend/dist`, adds SPA deep-link handling, and sets baseline browser security headers.

1. Import the Git repository into Vercel and keep the **Root Directory** at the repository root.
2. Use the project configuration from `vercel.json` (install: `npm --prefix frontend ci`; build: `npm --prefix frontend run build`; output: `frontend/dist`).
3. Leave `VITE_API_URL` unset. The `/api/:path*` rewrite in `vercel.json` proxies requests to the Hugging Face Space at `https://nouranomar-skin-ai-backend.hf.space`, keeping browser requests same-origin so the HttpOnly session cookie works.
4. Deploy the production branch. The verified production URL is `https://skin-ai-psi-two.vercel.app/`; update the canonical, Open Graph, sitemap, and robots URLs if the Vercel project is later assigned a different hostname.

## Hugging Face Spaces API service

The deployable Gradio SDK + ZeroGPU bundle is in [`deploy/huggingface-space/`](deploy/huggingface-space/). Copy the contents of that directory (including `models/best.pt`) to the `nouranomar/skin-ai-backend` Space repository. Configure its SDK as Gradio, Python 3.12, and select ZeroGPU hardware in Space Settings. Its Gradio interface and existing FastAPI routes are served together.

Configure the API service with:

- `SKINAI_ENV=production`
- `SKINAI_JWT_SECRET` set to a long random secret in the provider's secret manager
- `SKINAI_COOKIE_SECURE=true`
- `SKINAI_CORS=https://skin-ai-psi-two.vercel.app`
- `SKINAI_STORAGE=/tmp/skinai-storage` (Space storage is ephemeral; saved accounts and reports can be lost on rebuild/restart)
- Optional assistant generation: `HF_TOKEN` with Inference Providers permission and `SKINAI_ASSISTANT_MODEL` set to a supported chat-completion model ID. The UI asks before sending recent turns to this provider; leave either unset for local retrieval-only answers.

Do not set `VITE_API_URL` in Vercel unless changing the API host. Confirm `/api/health`, account flows, image analysis, chatbot retrieval/generation, and PDF downloads against the deployed service after launch. Hugging Face ZeroGPU provides the supported PyTorch runtime; the bundle pins the matching torchvision version and does not install a conflicting torch wheel. Optional chat generation sends only a visitor-opted-in question and recent turns to the configured Hugging Face Inference Provider; do not request or send identifying health details.

## SEO checks

- Confirm `/robots.txt`, `/sitemap.xml`, `/favicon.svg`, and `/og-skinai.png` resolve over HTTPS after deployment.
- Verify the canonical and Open Graph URLs match the final production hostname.
- Check the rendered title, description, and JSON-LD with a structured-data validator and social preview tools.
- Keep clinical language educational and non-diagnostic; do not add claims of clinical validation unless supported by evidence.
