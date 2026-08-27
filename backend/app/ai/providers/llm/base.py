"""
LLM Provider Interface.

Abstract base class for all LLM providers. Enables swapping LLM backends
(Ollama, OpenAI, Anthropic, etc.) without changing the AI pipeline.
"""

from abc import ABC, abstractmethod
from typing import AsyncGenerator, Any, Dict, List, Optional


class LLMProvider(ABC):
    """Abstract LLM provider interface."""

    @abstractmethod
    async def generate(
        self,
        prompt: str,
        system_prompt: str = "",
        temperature: float = 0.1,
        max_tokens: int = 2048,
    ) -> str:
        """
        Generate a text completion.

        Args:
            prompt: The user prompt.
            system_prompt: System-level instructions.
            temperature: Sampling temperature (lower = more deterministic).
            max_tokens: Maximum tokens to generate.

        Returns:
            Generated text response.
        """
        pass

    @abstractmethod
    async def generate_structured(
        self,
        prompt: str,
        system_prompt: str = "",
        temperature: float = 0.1,
    ) -> str:
        """
        Generate a structured (JSON) response from the LLM.

        Args:
            prompt: The user prompt requesting structured output.
            system_prompt: System-level instructions.
            temperature: Sampling temperature.

        Returns:
            Raw string response (caller parses JSON).
        """
        pass

    @abstractmethod
    async def stream(
        self,
        prompt: str,
        system_prompt: str = "",
        temperature: float = 0.1,
    ) -> AsyncGenerator[str, None]:
        """
        Stream text tokens from the LLM.

        Args:
            prompt: The user prompt.
            system_prompt: System-level instructions.
            temperature: Sampling temperature.

        Yields:
            Individual text tokens/chunks.
        """
        pass

    @abstractmethod
    async def health_check(self) -> bool:
        """
        Check if the LLM service is available.

        Returns:
            True if the LLM is reachable and ready.
        """
        pass

    @abstractmethod
    def get_model_name(self) -> str:
        """Return the configured model name."""
        pass
