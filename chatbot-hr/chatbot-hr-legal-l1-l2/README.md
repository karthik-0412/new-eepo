# Chatbot (React frontend + FastAPI backend)

Starter project scaffold that wires a React (Vite) frontend to a FastAPI backend and a small ChatGROQ LLM client wrapper. Includes domain routing for HR, Legal, L1 and L2 conversations.

Quick steps (PowerShell):

1. Backend

```powershell
cd C:\Users\dhaya\Desktop\chatbot\backend
python -m venv .venv; .\.venv\Scripts\Activate.ps1; pip install -r requirements.txt
# copy .env.example to .env and set CHATGROQ_API_KEY and CHATGROQ_BASE_URL (optional)
uvicorn app.main:app --reload --port 8000
```

2. Frontend

```powershell
cd C:\Users\dhaya\Desktop\chatbot\frontend
npm install
npm run dev
```

Notes:

- If `CHATGROQ_API_KEY` is not provided the backend will return mocked responses so you can develop the UI without the LLM key.
- The backend stores conversation history in memory (per-process). For production, replace with a DB or vector store.

API contract (POST /api/chat):

- request: { domain?: 'auto'|'hr'|'legal'|'l1'|'l2', session_id?: string, messages: [{role:'user'|'assistant', content:string}] }
- response: { reply: string, domain: string, session_id: string }

Note on sessions: if you pass back the returned session_id on subsequent calls, the backend will include previous messages as context.
