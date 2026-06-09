from typing import Protocol

from ..config import Settings


class LLMProvider(Protocol):
    """Contract for LLM backends used to generate the radio script."""

    def generate(self, prompt: str, settings: Settings) -> str | None:
        """Return generated text, or None when the provider returns an empty response."""
