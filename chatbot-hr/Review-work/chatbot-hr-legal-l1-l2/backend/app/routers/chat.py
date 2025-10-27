from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from typing import List, Optional
from ..llm.chatgroq_client import ChatGROQClient
try:
    from ..llm.langchain_chatgroq import ChatGROQLangChain
except Exception:
    ChatGROQLangChain = None
from dotenv import load_dotenv
import os
import uuid

load_dotenv()

router = APIRouter()

llm = ChatGROQClient()

# simple in-memory conversation store: session_id -> List[dict(role, content)]
conversations = {}


class Message(BaseModel):
    role: str
    content: str


class ChatRequest(BaseModel):
    domain: Optional[str] = "auto"  # hr, legal, l1, l2, auto
    messages: List[Message]
    session_id: Optional[str] = None
    api_key: Optional[str] = None 


class ChatResponse(BaseModel):
    reply: str
    domain: str
    session_id: Optional[str] = None
    api_key: Optional[str] = None


@router.post("/chat", response_model=ChatResponse)
async def chat(req: ChatRequest):
    domain = req.domain.lower() if req.domain else "auto"

    # if a session id is provided, merge historic messages (if present)
    if req.session_id:
        history = conversations.get(req.session_id, [])
        merged = history + [m.dict() for m in req.messages]
    else:
        merged = [m.dict() for m in req.messages]

    # auto domain detection
    if domain == "auto":
        text = " ".join([m["content"] for m in merged]).lower()
        if any(k in text for k in ["salary", "benefit", "hr", "leave", "hiring"]):
            domain = "hr"
        elif any(k in text for k in ["contract", "policy", "compliance", "nda", "legal"]):
            domain = "legal"
        elif any(k in text for k in ["ticket", "issue", "bug", "incident"]):
            domain = "l1"
        else:
            domain = "l2"

    system_prompt = f"You are an assistant handling {domain.upper()} inquiries. Be helpful and concise."

    # 🧠 dynamically use API key
    api_key = req.api_key or os.getenv("CHATGROQ_API_KEY")

    # Decide whether to use LangChain wrapper. This can be triggered by setting
    # the environment variable USE_LANGCHAIN=1 or by using domain='langchain'.
    use_langchain = (os.getenv("USE_LANGCHAIN") == "1") or (domain == "langchain")

    if use_langchain and ChatGROQLangChain is not None:
        # LangChain wrapper exposes a synchronous _call method that returns text
        llm = ChatGROQLangChain(api_key=api_key)
        try:
            reply = llm._call("\n".join([m["content"] for m in merged]))
        except Exception as e:
            raise HTTPException(status_code=500, detail=f"LangChain wrapper error: {e}")
    else:
        llm = ChatGROQClient(api_key=api_key)

        try:
            reply = await llm.chat(system_prompt=system_prompt, messages=merged)
        except Exception as e:
            raise HTTPException(status_code=500, detail=str(e))

    sid = req.session_id or str(uuid.uuid4())
    conversations[sid] = merged + [{"role": "assistant", "content": reply}]

    return ChatResponse(reply=reply, domain=domain, session_id=sid)
