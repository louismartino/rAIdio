from google import genai

from ..config import Settings


class GeminiProvider:
    """Google Gemini implementation."""

    def __init__(self, settings: Settings) -> None:
        self._client = genai.Client(api_key=settings.llm_api_key.get_secret_value())

    def generate(self, prompt: str, settings: Settings) -> str | None:
        response = self._client.models.generate_content(
            model=settings.llm_model,
            contents=prompt,
        )
        return response.text
