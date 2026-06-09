import pytest
from pydantic import SecretStr

from src.config import Settings
from src.llm.factory import get_llm_provider
from src.llm.gemini import GeminiProvider


def _make_settings(**overrides: object) -> Settings:
    defaults: dict[str, object] = {
        "llm_provider": "gemini",
        "llm_model": "gemini-3.5-flash",
        "llm_api_key": SecretStr("test-key"),
        "email_user": "user@example.com",
        "email_pass": SecretStr("pass"),
        "telegram_token": SecretStr("token"),
        "telegram_chat_id": "123",
        "user_first_name": "Louis",
        "newsletter_order": ["Newsletter A"],
        "newsletter_limit_name": "Newsletter A",
        "newsletter_limit_count": 5,
        "prompt_template_path": "prompts/radio_script.fr.txt",
        "tts_voice": "fr-FR-DeniseNeural",
        "tts_rate": "+15%",
        "fastapi_api_key": SecretStr("test-api-key"),
    }
    defaults.update(overrides)
    return Settings(_env_file=None, **defaults)


def test_get_llm_provider_returns_gemini_by_default() -> None:
    settings = _make_settings()

    provider = get_llm_provider(settings)

    assert isinstance(provider, GeminiProvider)


def test_get_llm_provider_rejects_unknown_provider() -> None:
    settings = _make_settings(llm_provider="unknown")

    with pytest.raises(ValueError, match="Unsupported LLM provider"):
        get_llm_provider(settings)
