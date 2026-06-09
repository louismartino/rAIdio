from pathlib import Path

import pytest
from pydantic import SecretStr

from src.config import Settings
from src.prompts import (
    build_radio_script_prompt,
    format_newsletter_order_for_prompt,
    load_prompt_template,
    resolve_prompt_template_path,
)


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
        "newsletter_order": ["Newsletter A", "Newsletter B"],
        "newsletter_limit_name": "Newsletter B",
        "newsletter_limit_count": 5,
        "prompt_template_path": "prompts/radio_script.fr.txt",
        "tts_voice": "fr-FR-DeniseNeural",
        "tts_rate": "+15%",
        "fastapi_api_key": SecretStr("test-api-key"),
    }
    defaults.update(overrides)
    return Settings(_env_file=None, **defaults)


def test_format_newsletter_order_for_prompt_single_item() -> None:
    assert format_newsletter_order_for_prompt(["Aktionnaire"]) == "Aktionnaire"


def test_format_newsletter_order_for_prompt_two_items() -> None:
    assert (
        format_newsletter_order_for_prompt(["The Economist", "Bloomberg"])
        == "The Economist, puis Bloomberg"
    )


def test_format_newsletter_order_for_prompt_multiple_items() -> None:
    assert (
        format_newsletter_order_for_prompt(["A", "B", "C", "D"]) == "A, puis B, puis C et enfin D"
    )


def test_build_radio_script_prompt_includes_raw_text() -> None:
    raw_text = "Unique newsletter payload for testing."
    settings = _make_settings()

    prompt = build_radio_script_prompt(raw_text, settings)

    assert raw_text in prompt
    assert "Salut Louis, voici les newsletters du jour" in prompt
    assert "CONTENU BRUT" in prompt


def test_build_radio_script_prompt_uses_custom_first_name() -> None:
    settings = _make_settings(user_first_name="Alice")

    prompt = build_radio_script_prompt("content", settings)

    assert "Salut Alice, voici les newsletters du jour" in prompt
    assert "Et voilà Alice, c'est tout pour aujourd'hui" in prompt
    assert "Louis" not in prompt


def test_build_radio_script_prompt_formats_newsletter_order_from_list() -> None:
    settings = _make_settings(newsletter_order=["The Economist", "Bloomberg", "FT"])

    prompt = build_radio_script_prompt("content", settings)

    assert "Dans l'ordre (s'il y a): The Economist, puis Bloomberg et enfin FT." in prompt


def test_build_radio_script_prompt_uses_custom_newsletter_limit() -> None:
    settings = _make_settings(newsletter_limit_name="Ma newsletter", newsletter_limit_count=3)

    prompt = build_radio_script_prompt("content", settings)

    assert 'pour la newsletter "Ma newsletter" ne mets que les news importantes' in prompt
    assert "limite-toi à 3 pour cette newsletter" in prompt


def test_load_prompt_template_from_default_file() -> None:
    settings = _make_settings()

    template = load_prompt_template(settings)

    assert "{user_first_name}" in template
    assert "{newsletter_order}" in template
    assert "{raw_text}" in template


def test_build_radio_script_prompt_uses_custom_template_file(tmp_path: Path) -> None:
    template_path = tmp_path / "custom_prompt.txt"
    template_path.write_text(
        "Hello {user_first_name}. Order: {newsletter_order}. Limit: {newsletter_limit_count}. "
        "Data: {raw_text}",
        encoding="utf-8",
    )
    settings = _make_settings(
        prompt_template_path=template_path,
        user_first_name="Alice",
        newsletter_order=["A", "B"],
        newsletter_limit_count=7,
    )

    prompt = build_radio_script_prompt("payload", settings)

    assert prompt == "Hello Alice. Order: A, puis B. Limit: 7. Data: payload"


def test_resolve_prompt_template_path_supports_relative_paths() -> None:
    settings = _make_settings(prompt_template_path=Path("prompts/custom.txt"))

    resolved = resolve_prompt_template_path(settings)

    assert resolved == Path.cwd() / "prompts/custom.txt"


def test_load_prompt_template_raises_when_file_is_missing(tmp_path: Path) -> None:
    from src.prompts import _read_prompt_template

    _read_prompt_template.cache_clear()
    missing_path = tmp_path / "missing.txt"
    settings = _make_settings(prompt_template_path=missing_path)

    with pytest.raises(FileNotFoundError, match="Prompt template not found"):
        load_prompt_template(settings)

    _read_prompt_template.cache_clear()
