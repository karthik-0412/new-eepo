import os
import requests
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from dotenv import load_dotenv
from fastapi.middleware.cors import CORSMiddleware

# Load environment variables from a .env file if present (but read values at runtime)
load_dotenv()

# Default models (actual keys are read at request time so changes take effect without restart)
DEFAULT_HF_MODEL = os.getenv("HF_MODEL", "google/flan-t5-small")
DEFAULT_OPENROUTER_MODEL = os.getenv("OPENROUTER_MODEL", "gpt-4o-mini")

app = FastAPI(title="Personna Chatbot API")

import logging
logger = logging.getLogger("personna_chatbot")
logging.basicConfig(level=logging.INFO)

# Enable CORS for local frontend
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173", "http://localhost:3000"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

class ChatRequest(BaseModel):
    message: str
    history: list | None = None

class ChatResponse(BaseModel):
    reply: str


@app.get("/health")
def health():
    """Return which model provider is active (openrouter, huggingface, or dev)."""
    openrouter_key = os.getenv("OPENROUTER_API_KEY")
    hf_token = os.getenv("HF_API_TOKEN")
    dev_fb = os.getenv("DEV_FALLBACK", "true").lower() in ("1", "true", "yes")
    if openrouter_key:
        return {"status": "ok", "provider": "openrouter", "model": os.getenv("OPENROUTER_MODEL", DEFAULT_OPENROUTER_MODEL)}
    if hf_token:
        return {"status": "ok", "provider": "huggingface", "model": os.getenv("HF_MODEL", DEFAULT_HF_MODEL)}
    return {"status": "ok", "provider": "dev-fallback" if dev_fb else "none"}

@app.post("/chat", response_model=ChatResponse)
def chat(req: ChatRequest):
    # Build prompt using instruction format
    prompt_parts = []
    for turn in req.history or []:
        user = turn.get("user", "")
        assistant = turn.get("assistant", "")
        if user:
            prompt_parts.append(f"Question: {user}")
        if assistant:
            prompt_parts.append(f"Answer: {assistant}")
    prompt_parts.append(f"Question: {req.message}")
    prompt_parts.append("Answer:")
    prompt = "\n".join(prompt_parts)

    # Read provider config at request time so env var changes are picked up without restarting
    openrouter_key = os.getenv("OPENROUTER_API_KEY")
    openrouter_model = os.getenv("OPENROUTER_MODEL", DEFAULT_OPENROUTER_MODEL)
    hf_token = os.getenv("HF_API_TOKEN")
    hf_model = os.getenv("HF_MODEL", DEFAULT_HF_MODEL)
    dev_fallback_enabled = os.getenv("DEV_FALLBACK", "true").lower() in ("1", "true", "yes")

    # Prefer OpenRouter if configured
    if openrouter_key:
        try:
            # build messages from history
            messages = []
            for turn in req.history or []:
                if turn.get('user'):
                    messages.append({"role": "user", "content": turn.get('user')})
                if turn.get('assistant'):
                    messages.append({"role": "assistant", "content": turn.get('assistant')})
            # append current user message
            messages.append({"role": "user", "content": req.message})

            or_headers = {"Authorization": f"Bearer {openrouter_key}", "Content-Type": "application/json"}
            or_payload = {"model": openrouter_model, "messages": messages}
            logger.info("Calling OpenRouter model=%s", openrouter_model)
            r = requests.post("https://api.openrouter.ai/v1/chat/completions", headers=or_headers, json=or_payload, timeout=60)
            try:
                r.raise_for_status()
            except Exception as e:
                # include response body in log for debugging
                body = None
                try:
                    body = r.text
                except Exception:
                    body = "<could not read body>"
                logger.error("OpenRouter call failed: %s; status=%s body=%s", e, r.status_code, body)
                raise
            data = r.json()
            # OpenRouter follows chat completions shape similar to OpenAI
            reply = None
            if isinstance(data, dict) and "choices" in data and len(data["choices"]) > 0:
                choice = data["choices"][0]
                # some providers nest the message
                if isinstance(choice.get("message"), dict) and "content" in choice.get("message"):
                    reply = choice["message"]["content"]
                elif "text" in choice:
                    reply = choice["text"]
            if reply is None:
                reply = str(data)
            return ChatResponse(reply=reply)
        except Exception as e:
            # if OpenRouter fails and HF_TOKEN exists, fall back to HF
            if not hf_token:
                # If dev fallback is enabled, return a friendly dev reply instead of hard failing
                if dev_fallback_enabled:
                    logger.warning("OpenRouter error and no HF token, returning dev-fallback: %s", e)
                    return ChatResponse(reply=f"You said: '{req.message}'. How can I help?")
                raise HTTPException(status_code=502, detail=f"OpenRouter error and no Hugging Face token to fall back: {e}")
            # else continue to HF handling

    # Fallback to Hugging Face Inference API if OpenRouter not configured or failed
    if not hf_token:
        # if no HF token and dev fallback is allowed, return dev responder
        if dev_fallback_enabled:
            logger.info("No HF token configured, returning dev-fallback reply")
            return ChatResponse(reply=f"You said: '{req.message}'. How can I help?")
        raise HTTPException(status_code=503, detail="No model API configured (set OPENROUTER_API_KEY or HF_API_TOKEN).")

    headers = {
        "Authorization": f"Bearer {hf_token}",
        "Content-Type": "application/json"
    }
    payload = {
        "inputs": prompt,
        "options": {"wait_for_model": True}
    }

    try:
        response = requests.post(
            f"https://api-inference.huggingface.co/models/{hf_model}",
            headers=headers,
            json=payload,
            timeout=60
        )
        response.raise_for_status()
        result = response.json()

        # Extract reply
        if isinstance(result, dict) and "generated_text" in result:
            reply = result["generated_text"]
        elif isinstance(result, list) and len(result) > 0 and isinstance(result[0], dict) and "generated_text" in result[0]:
            reply = result[0]["generated_text"]
        else:
            reply = str(result)

    except Exception as e:
        # if dev fallback allowed, return friendly reply
        if dev_fallback_enabled:
            logger.warning("Hugging Face API error, returning dev-fallback: %s", e)
            return ChatResponse(reply=f"You said: '{req.message}'. How can I help?")
        raise HTTPException(status_code=500, detail=f"Hugging Face API error: {e}")

    return ChatResponse(reply=reply)
