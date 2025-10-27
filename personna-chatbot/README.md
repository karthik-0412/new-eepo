# Personna Chatbot

This repository contains a minimal example of a chatbot with a React (Vite) frontend and a FastAPI backend. The backend uses LangChain's HuggingFaceHub LLM wrapper to call a Hugging Face model.

Quickstart

1. Backend

- Copy `backend/.env.example` to `backend/.env` and set `HF_API_TOKEN`.
- Create a Python virtual environment and install requirements:

```powershell
python -m venv .venv; .\.venv\Scripts\Activate.ps1; pip install -r backend/requirements.txt
```

- Start the server:

```powershell
uvicorn backend.app.main:app --reload --port 8000
```

2. Frontend

- From `frontend/` install and run:

```powershell
cd frontend; npm install; npm run dev
```

Open the Vite URL (usually http://localhost:5173) and chat.

Notes

- The example uses Hugging Face Hub models via `HuggingFaceHub` from LangChain. Make sure your token has the required access for hosted inference of the chosen model.
- For large models you may prefer using hosted inference or an API-based model (e.g., Hugging Face Inference API) rather than local Transformers.
