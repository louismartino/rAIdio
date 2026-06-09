import json
from pathlib import Path
from typing import Annotated

from pydantic import AliasChoices, Field, SecretStr, field_validator
from pydantic_settings import BaseSettings, NoDecode, SettingsConfigDict

NEWSLETTER_ORDER_SEPARATOR = ";"

IMAP_HOST = "imap.gmail.com"
IMAP_FOLDER = "Newsletters"

NEWSLETTERS_DIR = Path("./newsletters")
THUMBNAIL_PATH = Path("news.jpg")

MAX_LLM_ATTEMPTS = 3
LLM_RETRY_DELAY_SECONDS = 60


class Settings(BaseSettings):
    """Application settings loaded exclusively from environment variables.

    Every field mapped to .env is required. Missing or empty values raise ValidationError.
    Sensitive values use SecretStr so they are never accidentally logged or printed.
    """

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=True,
        extra="ignore",
        frozen=True,
        populate_by_name=True,
    )

    llm_provider: str = Field(validation_alias="LLM_PROVIDER")
    llm_model: str = Field(validation_alias="LLM_MODEL")
    llm_api_key: SecretStr = Field(
        validation_alias=AliasChoices("LLM_API_KEY", "GEMINI_API_KEY"),
    )
    email_user: str = Field(validation_alias="EMAIL_USER")
    email_pass: SecretStr = Field(validation_alias="EMAIL_PASS")
    telegram_token: SecretStr = Field(validation_alias="TELEGRAM_TOKEN")
    telegram_chat_id: str = Field(validation_alias="TELEGRAM_CHAT_ID")
    user_first_name: str = Field(validation_alias="USER_FIRST_NAME")
    newsletter_order: Annotated[list[str], NoDecode] = Field(validation_alias="NEWSLETTER_ORDER")
    newsletter_limit_name: str = Field(validation_alias="NEWSLETTER_LIMIT_NAME")
    newsletter_limit_count: int = Field(validation_alias="NEWSLETTER_LIMIT_COUNT")
    prompt_template_path: Path = Field(validation_alias="PROMPT_TEMPLATE_PATH")
    tts_voice: str = Field(validation_alias="TTS_VOICE")
    tts_rate: str = Field(validation_alias="TTS_RATE")
    fastapi_api_key: SecretStr = Field(validation_alias="FASTAPI_API_KEY")

    @field_validator("newsletter_order", mode="before")
    @classmethod
    def parse_newsletter_order(cls, value: object) -> list[str]:
        if isinstance(value, list):
            return [str(item).strip() for item in value if str(item).strip()]

        if isinstance(value, str):
            stripped = value.strip()
            if not stripped:
                raise ValueError("NEWSLETTER_ORDER must not be empty.")

            if stripped.startswith("["):
                parsed = json.loads(stripped)
                if not isinstance(parsed, list):
                    raise TypeError("NEWSLETTER_ORDER JSON value must be a list.")
                items = [str(item).strip() for item in parsed if str(item).strip()]
                if not items:
                    raise ValueError("NEWSLETTER_ORDER must not be empty.")
                return items

            items = [
                item.strip() for item in stripped.split(NEWSLETTER_ORDER_SEPARATOR) if item.strip()
            ]
            if not items:
                raise ValueError("NEWSLETTER_ORDER must not be empty.")
            return items

        raise TypeError("NEWSLETTER_ORDER must be a list or a semicolon-separated string.")

    @field_validator(
        "llm_provider",
        "llm_model",
        "user_first_name",
        "newsletter_limit_name",
        "tts_voice",
        "tts_rate",
    )
    @classmethod
    def required_str_must_not_be_blank(cls, value: str) -> str:
        if not value.strip():
            raise ValueError("Required setting must not be empty.")
        return value


def load_settings() -> Settings:
    """Load and validate settings from the environment. Fails fast if any value is missing."""
    return Settings()
