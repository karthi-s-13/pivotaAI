"""
Ollama LLM Provider.

Connects to a local Ollama instance for LLM inference using langchain-ollama.
"""

import logging
from typing import AsyncGenerator

import httpx
from langchain_ollama import ChatOllama
from langchain_core.messages import HumanMessage, SystemMessage

from app.ai.providers.llm.base import LLMProvider
from app.ai.config import ai_settings

logger = logging.getLogger(__name__)


class OllamaLLMProvider(LLMProvider):
    """Ollama-based LLM provider using langchain-ollama."""

    def __init__(
        self,
        model: str | None = None,
        base_url: str | None = None,
    ):
        self._model = model or ai_settings.LLM_MODEL
        self._base_url = base_url or ai_settings.OLLAMA_BASE_URL
        self._llm = ChatOllama(
            model=self._model,
            base_url=self._base_url,
            temperature=0.1,
        )

    async def generate(
        self,
        prompt: str,
        system_prompt: str = "",
        temperature: float = 0.1,
        max_tokens: int = 2048,
    ) -> str:
        """Generate a text completion from Ollama."""
        messages = []
        if system_prompt:
            messages.append(SystemMessage(content=system_prompt))
        messages.append(HumanMessage(content=prompt))

        llm = self._llm.bind(options={"temperature": temperature, "num_predict": max_tokens})
        response = await llm.ainvoke(messages)
        return response.content

    async def generate_structured(
        self,
        prompt: str,
        system_prompt: str = "",
        temperature: float = 0.1,
    ) -> str:
        """Generate structured (JSON) output from Ollama."""
        messages = []
        if system_prompt:
            messages.append(SystemMessage(content=system_prompt))
        messages.append(HumanMessage(content=prompt))

        llm = ChatOllama(
            model=self._model,
            base_url=self._base_url,
            format="json",
            options={"temperature": temperature},
        )
        response = await llm.ainvoke(messages)
        return response.content

    async def stream(
        self,
        prompt: str,
        system_prompt: str = "",
        temperature: float = 0.1,
    ) -> AsyncGenerator[str, None]:
        """Stream text tokens from Ollama."""
        messages = []
        if system_prompt:
            messages.append(SystemMessage(content=system_prompt))
        messages.append(HumanMessage(content=prompt))

        llm = self._llm.bind(options={"temperature": temperature})
        async for chunk in llm.astream(messages):
            if chunk.content:
                yield chunk.content

    async def health_check(self) -> bool:
        """Check if the Ollama service is reachable."""
        try:
            async with httpx.AsyncClient(timeout=5.0) as client:
                response = await client.get(f"{self._base_url}/api/tags")
                if response.status_code == 200:
                    data = response.json()
                    models = [m.get("name", "") for m in data.get("models", [])]
                    # Check if our model is available
                    model_base = self._model.split(":")[0]
                    return any(model_base in m for m in models)
            return False
        except Exception as e:
            logger.warning(f"Ollama health check failed: {e}")
            return False

    def get_model_name(self) -> str:
        """Return the configured model name."""
        return self._model


# Singleton instance
_provider_instance: OllamaLLMProvider | None = None


def get_llm_provider() -> LLMProvider:
    """Get or create the singleton LLM provider instance."""
    global _provider_instance
    if _provider_instance is None:
        _provider_instance = OllamaLLMProvider()
    return _provider_instance
