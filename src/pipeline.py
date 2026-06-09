import logging
from dataclasses import dataclass
from datetime import date

from .config import Settings, load_settings
from .newsletter_fetcher import fetch_newsletters
from .script_generator import generate_radio_script
from .telegram_client import send_audio_message, send_text_message
from .user_messages import (
    audio_delivery_failed,
    mailbox_fetch_failed,
    no_newsletters_found,
    pipeline_failed,
)

logger = logging.getLogger(__name__)


@dataclass(frozen=True)
class PipelineOutcome:
    status: str
    target_date: date
    detail: str | None = None


async def run_pipeline(
    settings: Settings | None = None,
    target_date: date | None = None,
) -> PipelineOutcome:
    """Orchestrate the full newsletter-to-radio pipeline."""
    resolved_settings = settings or load_settings()
    resolved_target_date = target_date or date.today()

    try:
        return await _run_pipeline_stages(resolved_settings, resolved_target_date)
    except Exception as exc:
        logger.exception("Pipeline failed with an unexpected error")
        await send_text_message(
            resolved_settings,
            pipeline_failed("pipeline execution", str(exc)),
        )
        raise


async def _run_pipeline_stages(settings: Settings, target_date: date) -> PipelineOutcome:
    fetch_result = await fetch_newsletters(settings, target_date)
    if fetch_result.error is not None:
        await send_text_message(settings, mailbox_fetch_failed(fetch_result.error))
        return PipelineOutcome(
            status="mailbox_fetch_failed",
            target_date=target_date,
            detail=fetch_result.error,
        )

    if not fetch_result.newsletters:
        logger.info("No newsletters found for %s.", target_date.isoformat())
        await send_text_message(settings, no_newsletters_found())
        return PipelineOutcome(status="no_newsletters", target_date=target_date)

    full_text = "\n\n".join(fetch_result.newsletters)
    generation_result = await generate_radio_script(full_text, settings)

    if generation_result.script is None:
        failure_message = generation_result.failure_message or pipeline_failed(
            "script generation",
            "Unknown script generation error.",
        )
        await send_text_message(settings, failure_message)
        return PipelineOutcome(
            status="script_generation_failed",
            target_date=target_date,
            detail=failure_message,
        )

    try:
        await send_audio_message(settings, generation_result.script, target_date)
    except Exception as exc:
        logger.exception("Audio delivery failed")
        await send_text_message(settings, audio_delivery_failed(str(exc)))
        return PipelineOutcome(
            status="audio_delivery_failed",
            target_date=target_date,
            detail=str(exc),
        )

    return PipelineOutcome(status="completed", target_date=target_date)
