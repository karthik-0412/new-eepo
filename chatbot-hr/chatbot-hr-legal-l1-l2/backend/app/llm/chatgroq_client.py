import os
from typing import List, Dict, Any
import httpx
from dotenv import load_dotenv

load_dotenv()

class ChatGROQClient:
    def __init__(self, api_key: str = None):
        self.api_key = api_key or os.getenv("CHATGROQ_API_KEY")
        self.base_url = os.getenv("CHATGROQ_BASE_URL", "https://api.groq.com/openai/v1")

    async def chat(self, system_prompt: str, messages: List[Dict[str, Any]]) -> str:
        if not self.api_key:
            return self._mock_reply(system_prompt, messages)

        # Build OpenAI-compatible messages
        formatted_messages = [{"role": "system", "content": system_prompt}]
        for m in messages:
            role = m.get("role", "").lower()
            if role == "user" or role == "assistant":
                formatted_messages.append({"role": role, "content": m["content"]})
            else:
                # Skip invalid roles
                continue

        payload = {
            "model": "llama-3.1-8b-instant",  # replace with a valid Groq model
            "messages": formatted_messages,
            "temperature": 0.7
        }

        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json"
        }

        url = f"{self.base_url}/chat/completions"
        async with httpx.AsyncClient(timeout=60.0) as client:
            resp = await client.post(url, json=payload, headers=headers)
            resp.raise_for_status()
            data = resp.json()
            return data["choices"][0]["message"]["content"]

    def _mock_reply(self, system_prompt: str, messages: List[Dict[str, Any]]) -> str:
        last = messages[-1]["content"] if messages else ""
        return f"(mock) I received your message: '{last}'"
