from typing import List, Optional, Mapping, Any
import os
from langchain.llms.base import LLM
from pydantic import BaseModel
from .chatgroq_client import ChatGROQClient


class ChatGROQLangChain(LLM):
    """A minimal LangChain-compatible wrapper around the existing ChatGROQ client.

    This implements the synchronous `__call__` and `generate` shape expected by
    some LangChain components. It delegates to ChatGROQClient which is async, so
    this wrapper will call it via an async loop when needed.
    """

    api_key: Optional[str] = None
    model: str = "llama-3.1-8b-instant"

    class Config:
        arbitrary_types_allowed = True

    def _get_client(self) -> ChatGROQClient:
        return ChatGROQClient(api_key=self.api_key)

    def _call(self, prompt: str, stop: Optional[List[str]] = None) -> str:
        # LangChain expects a synchronous call for simple LLMs.
        # We'll craft a minimal message list and run the async client using
        # anyio.to_thread or asyncio.run for a quick implementation.
        import asyncio

        async def _async_chat():
            client = self._get_client()
            messages = [{"role": "user", "content": prompt}]
            return await client.chat(system_prompt="", messages=messages)

        return asyncio.get_event_loop().run_until_complete(_async_chat())

    @property
    def _identifying_params(self) -> Mapping[str, Any]:
        return {"model": self.model}

    @property
    def _llm_type(self) -> str:
        return "chatgroq"


# Small test helper if executed directly
if __name__ == "__main__":
    import dotenv

    dotenv.load_dotenv()
    llm = ChatGROQLangChain()
    print(llm._call("Hello from LangChain wrapper"))
