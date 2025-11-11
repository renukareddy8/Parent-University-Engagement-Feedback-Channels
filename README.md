# Parent-University Engagement — Agentic AI Prototype

Build an Agentic AI feedback and engagement platform for parents, with a focus on:
- Categorizing parent feedback and routing it to university departments.
- Analyzing sentiment and extracting structured information.
- A parent-perspective UI to submit feedback.

This starter implements a FastAPI backend, a simple web UI, and an "agent" classifier that:
- Uses LangChain + OpenAI if you provide an `OPENAI_API_KEY`.
- Falls back to a lightweight rule-based + VADER sentiment analyzer when no key is present.

Why this approach
- It gives you an agentic workflow (classification + routing) while remaining runnable offline for development.

Quick start (Windows PowerShell)

1) Create a virtual environment and install dependencies:

```powershell
python -m venv .venv; .\.venv\Scripts\Activate.ps1
pip install -r requirements.txt
```

2) Optional: provide an OpenAI API key (if you want LangChain/LLM classification):

```powershell
copy .env.example .env
# then edit .env and set OPENAI_API_KEY
```

3) Run the app:

```powershell
$env:PORT=8000; uvicorn src.main:app --reload --port $env:PORT
```

4) Open http://127.0.0.1:8000 in your browser to submit feedback as a parent.

Notes
- If `OPENAI_API_KEY` is not set or LangChain/OpenAI libs are not installed, a local fallback classifier will be used (keyword mapping + VADER sentiment).
- This is a minimal prototype designed for iteration. Next steps could include authentication, department routing integrations, richer LLM prompts, persistence to a DB, and admin dashboards.

Files created
- `src/main.py` - FastAPI app and endpoints
- `src/agents/classifier.py` - The agent that classifies feedback
- `src/storage.py` - Simple in-memory + file-backed storage
- `src/schemas.py` - Pydantic models
- `src/templates/index.html` and `src/static/css/style.css` - basic UI
- `requirements.txt` - Dependencies
- `tests/test_app.py` - Minimal test

If you'd like, I can: add department routing rules, wire an email/slack notifier, or convert the UI to React.

Deployment
----------

This repository includes a `Dockerfile` and a GitHub Actions workflow (`.github/workflows/build-and-publish.yml`) that builds a container image and pushes it to GitHub Container Registry (GHCR) on every push to `main`.

Quick deploy options:

- Use the built image from GHCR directly on platforms such as Render, Fly.io, Azure App Service (Container), or any Kubernetes cluster. The image name will be:

	ghcr.io/<your-github-username-or-org>/<repo-name>:latest

	Example: ghcr.io/renukareddy8/Parent-University-Engagement-Feedback-Channels:latest

- Deploy to Render (manual steps):
	1. Create a new "Web Service" on Render and choose "Docker".
	2. Use the GHCR image name above or connect Render to your GitHub repo and let it build from the `Dockerfile`.

- Deploy to Azure App Service (Container):
	1. Push the image to GHCR (workflow does that automatically).
	2. Create an Azure Web App for Containers and point it at the GHCR image. Provide credentials via the Azure portal.

If you want I can also:
- Add an Action to auto-deploy to Render/Azure when you provide API keys as repository secrets.
- Create a small `docker-compose` for local container development.

Auto-deploy to Render (recommended, free tier friendly)
-----------------------------------------------

This repo includes a GitHub Actions workflow that will automatically trigger a deploy to Render after the CI workflow builds and publishes the container image to GitHub Container Registry (GHCR).

What to set in your repository secrets (Settings → Secrets → Actions):

- `RENDER_SERVICE_ID` — the Render service ID (the UUID for the service you want to update). You can find this on the service's page in the Render dashboard (Service Settings).
- `RENDER_API_KEY` — a Render API key. Create one in your Render dashboard (Account → API Keys) and paste it here as a secret.

How it works:

1. On push to `main`, the existing CI runs tests and builds/pushes the image to GHCR.
2. If CI succeeds, the `deploy-to-render.yml` workflow runs and calls the Render API to create a new deploy using the published GHCR image.

If you'd like, I can also:
- Add a small helper script to find the Render Service ID (via the Render API) and print the exact value to copy into the GitHub secret.
- Add a `docker-compose.yml` for local container testing.

