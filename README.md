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
