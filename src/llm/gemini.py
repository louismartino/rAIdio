from google import genai
from google.genai import types

from ..config import Settings


class GeminiProvider:
    """Google Gemini implementation."""

    def __init__(self, settings: Settings) -> None:
        http_config = types.HttpOptions(api_version="v1")

        self._client = genai.Client(api_key=settings.llm_api_key.get_secret_value(), http_options=http_config)

    def generate(self, prompt: str, settings: Settings) -> str | None:
        response = self._client.models.generate_content(
            model=settings.llm_model,
            contents=prompt,
        )
        return response.text
