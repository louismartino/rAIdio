import pytest

from src.config import Settings

REQUIRED_ENV: dict[str, str] = {
    "LLM_PROVIDER": "gemini",
    "LLM_MODEL": "gemini-3.5-flash",
    "LLM_API_KEY": "test-llm-key",
    "EMAIL_USER": "user@example.com",
    "EMAIL_PASS": "test-email-pass",
    "TELEGRAM_TOKEN": "test-telegram-token",
    "TELEGRAM_CHAT_ID": "123456789",
    "USER_FIRST_NAME": "Louis",
    "NEWSLETTER_ORDER": "Newsletter A;Newsletter B",
    "NEWSLETTER_LIMIT_NAME": "Newsletter B",
    "NEWSLETTER_LIMIT_COUNT": "5",
    "PROMPT_TEMPLATE_PATH": "prompts/radio_script.fr.txt",
    "TTS_VOICE": "fr-FR-DeniseNeural",
    "TTS_RATE": "+15%",
    "FASTAPI_API_KEY": "test-api-key",
}


def apply_required_env(monkeypatch: pytest.MonkeyPatch) -> None:
    for name, value in REQUIRED_ENV.items():
        monkeypatch.setenv(name, value)


@pytest.fixture
def settings(monkeypatch: pytest.MonkeyPatch) -> Settings:
    """Build Settings from isolated env vars — never reads the developer's .env file."""
    apply_required_env(monkeypatch)
    return Settings(_env_file=None)
