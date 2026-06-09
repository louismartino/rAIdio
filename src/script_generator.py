import asyncio
import logging
from dataclasses import dataclass

from .config import (
    LLM_RETRY_DELAY_SECONDS,
    MAX_LLM_ATTEMPTS,
    Settings,
)
from .llm import get_llm_provider
from .prompts import build_radio_script_prompt
from .user_messages import llm_generation_failed

logger = logging.getLogger(__name__)


@dataclass(frozen=True)
class ScriptGenerationResult:
    script: str | None = None
    failure_message: str | None = None


async def generate_radio_script(raw_text: str, settings: Settings) -> ScriptGenerationResult:
    """Transform raw newsletter text into a radio script via the configured LLM."""
    provider = get_llm_provider(settings)
    logger.info(
        "Generating radio script with %s (%s)...",
        settings.llm_provider,
        settings.llm_model,
    )
    prompt = build_radio_script_prompt(raw_text, settings)
    last_error: str | None = None

    for attempt in range(MAX_LLM_ATTEMPTS):
        try:
            script = await asyncio.to_thread(provider.generate, prompt, settings)
            if not script:
                last_error = "The LLM returned an empty response."
                logger.warning(
                    "LLM returned an empty response on attempt %d/%d",
                    attempt + 1,
                    MAX_LLM_ATTEMPTS,
                )
                continue
            return ScriptGenerationResult(script=script)
        except Exception as exc:
            last_error = str(exc)
            logger.exception("Attempt %d/%d failed", attempt + 1, MAX_LLM_ATTEMPTS)
            if attempt < MAX_LLM_ATTEMPTS - 1:
                logger.info("Rate limit or transient error. Retrying in 60 seconds...")
                await asyncio.sleep(LLM_RETRY_DELAY_SECONDS)
            else:
                logger.error("All %d attempts failed.", MAX_LLM_ATTEMPTS)

    return ScriptGenerationResult(
        failure_message=llm_generation_failed(MAX_LLM_ATTEMPTS, last_error),
    )
