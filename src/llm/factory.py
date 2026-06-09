from collections.abc import Callable

from ..config import Settings
from .gemini import GeminiProvider
from .protocol import LLMProvider

ProviderFactory = Callable[[Settings], LLMProvider]

# Register additional providers here when forking the project.
# Example: "openai": OpenAIProvider,
_PROVIDERS: dict[str, ProviderFactory] = {
    "gemini": GeminiProvider,
}


def get_llm_provider(settings: Settings) -> LLMProvider:
    """Return the LLM provider configured in settings."""
    provider_name = settings.llm_provider.lower()
    provider_factory = _PROVIDERS.get(provider_name)

    if provider_factory is None:
        supported = ", ".join(sorted(_PROVIDERS))
        raise ValueError(
            f"Unsupported LLM provider {settings.llm_provider!r}. "
            f"Supported providers: {supported}. "
            "To add a new provider, create src/llm/<name>.py and register it in "
            "src/llm/factory.py."
        )

    return provider_factory(settings)
