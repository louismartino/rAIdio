import pytest
from pydantic import SecretStr, ValidationError
from tests.conftest import REQUIRED_ENV, apply_required_env

from src.config import Settings, load_settings


def test_settings_masks_secrets_in_repr(settings: Settings) -> None:
    rendered = repr(settings)
    assert "test-llm-key" not in rendered
    assert "test-email-pass" not in rendered
    assert "test-telegram-token" not in rendered
    assert "**********" in rendered


def test_settings_exposes_secret_values(settings: Settings) -> None:
    assert settings.llm_api_key.get_secret_value() == "test-llm-key"
    assert settings.email_pass.get_secret_value() == "test-email-pass"
    assert settings.telegram_token.get_secret_value() == "test-telegram-token"


def test_settings_is_frozen(settings: Settings) -> None:
    with pytest.raises(ValidationError):
        settings.email_user = "other@example.com"  # type: ignore[misc]


def test_parse_newsletter_order_from_semicolon_separated_env(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    apply_required_env(monkeypatch)
    monkeypatch.setenv("NEWSLETTER_ORDER", "Alpha;Beta;Gamma")

    settings = Settings(_env_file=None)

    assert settings.newsletter_order == ["Alpha", "Beta", "Gamma"]


def test_load_settings_from_env(monkeypatch: pytest.MonkeyPatch) -> None:
    apply_required_env(monkeypatch)
    monkeypatch.setenv("LLM_MODEL", "gemini-2.5-flash")
    monkeypatch.setenv("LLM_API_KEY", "env-llm-key")
    monkeypatch.setenv("EMAIL_USER", "env@example.com")
    monkeypatch.setenv("TELEGRAM_CHAT_ID", "987654321")

    loaded = load_settings()

    assert loaded.llm_api_key == SecretStr("env-llm-key")
    assert loaded.llm_model == "gemini-2.5-flash"
    assert loaded.email_user == "env@example.com"
    assert loaded.telegram_chat_id == "987654321"


def test_load_settings_accepts_legacy_gemini_api_key(monkeypatch: pytest.MonkeyPatch) -> None:
    apply_required_env(monkeypatch)
    monkeypatch.delenv("LLM_API_KEY", raising=False)
    monkeypatch.setenv("GEMINI_API_KEY", "legacy-gemini-key")

    loaded = Settings(_env_file=None)

    assert loaded.llm_api_key == SecretStr("legacy-gemini-key")


@pytest.mark.parametrize("missing_env", list(REQUIRED_ENV))
def test_load_settings_fails_when_required_env_is_missing(
    monkeypatch: pytest.MonkeyPatch,
    missing_env: str,
) -> None:
    apply_required_env(monkeypatch)
    monkeypatch.delenv(missing_env, raising=False)
    if missing_env == "LLM_API_KEY":
        monkeypatch.delenv("GEMINI_API_KEY", raising=False)

    with pytest.raises(ValidationError):
        Settings(_env_file=None)


def test_load_settings_fails_when_newsletter_order_is_empty(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    apply_required_env(monkeypatch)
    monkeypatch.setenv("NEWSLETTER_ORDER", "   ")

    with pytest.raises(ValidationError):
        Settings(_env_file=None)
