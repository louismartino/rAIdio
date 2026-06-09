from datetime import date
from unittest.mock import AsyncMock, patch

import pytest

from src.config import Settings
from src.newsletter_fetcher import NewsletterFetchResult
from src.pipeline import PipelineOutcome, run_pipeline
from src.script_generator import ScriptGenerationResult

TARGET_DATE = date(2026, 6, 8)


@pytest.mark.asyncio
async def test_pipeline_notifies_when_no_newsletters(settings: Settings) -> None:
    with (
        patch(
            "src.pipeline.fetch_newsletters",
            new_callable=AsyncMock,
            return_value=NewsletterFetchResult(newsletters=[]),
        ) as mock_fetch,
        patch(
            "src.pipeline.generate_radio_script",
            new_callable=AsyncMock,
        ) as mock_generate,
        patch(
            "src.pipeline.send_text_message",
            new_callable=AsyncMock,
        ) as mock_send_text,
        patch(
            "src.pipeline.send_audio_message",
            new_callable=AsyncMock,
        ) as mock_send_audio,
    ):
        outcome = await run_pipeline(settings=settings, target_date=TARGET_DATE)

    mock_fetch.assert_awaited_once_with(settings, TARGET_DATE)
    assert outcome == PipelineOutcome(status="no_newsletters", target_date=TARGET_DATE)
    mock_generate.assert_not_awaited()
    mock_send_text.assert_awaited_once()
    assert "no newsletters" in mock_send_text.await_args.args[1].lower()
    mock_send_audio.assert_not_awaited()


@pytest.mark.asyncio
async def test_pipeline_notifies_when_mailbox_fetch_fails(settings: Settings) -> None:
    with (
        patch(
            "src.pipeline.fetch_newsletters",
            new_callable=AsyncMock,
            return_value=NewsletterFetchResult(newsletters=[], error="IMAP auth failed"),
        ),
        patch(
            "src.pipeline.send_text_message",
            new_callable=AsyncMock,
        ) as mock_send_text,
        patch("src.pipeline.send_audio_message", new_callable=AsyncMock) as mock_send_audio,
    ):
        outcome = await run_pipeline(settings=settings, target_date=TARGET_DATE)

    assert outcome.status == "mailbox_fetch_failed"
    mock_send_text.assert_awaited_once()
    message = mock_send_text.await_args.args[1]
    assert "failed to fetch newsletters" in message.lower()
    assert "IMAP auth failed" in message
    mock_send_audio.assert_not_awaited()


@pytest.mark.asyncio
async def test_pipeline_sends_text_when_llm_fails(settings: Settings) -> None:
    failure_message = (
        "rAIdio could not generate today's radio script after 3 attempts. "
        "Last error: quota exceeded"
    )
    with (
        patch(
            "src.pipeline.fetch_newsletters",
            new_callable=AsyncMock,
            return_value=NewsletterFetchResult(
                newsletters=["Sujet: Test\nContenu: Hello"],
            ),
        ),
        patch(
            "src.pipeline.generate_radio_script",
            new_callable=AsyncMock,
            return_value=ScriptGenerationResult(failure_message=failure_message),
        ),
        patch(
            "src.pipeline.send_text_message",
            new_callable=AsyncMock,
        ) as mock_send_text,
        patch(
            "src.pipeline.send_audio_message",
            new_callable=AsyncMock,
        ) as mock_send_audio,
    ):
        outcome = await run_pipeline(settings=settings, target_date=TARGET_DATE)

    assert outcome.status == "script_generation_failed"
    mock_send_text.assert_awaited_once_with(settings, failure_message)
    mock_send_audio.assert_not_awaited()


@pytest.mark.asyncio
async def test_pipeline_sends_audio_when_llm_succeeds(settings: Settings) -> None:
    script = "Salut Louis, voici les newsletters du jour."

    with (
        patch(
            "src.pipeline.fetch_newsletters",
            new_callable=AsyncMock,
            return_value=NewsletterFetchResult(
                newsletters=["Sujet: Test\nContenu: Hello"],
            ),
        ),
        patch(
            "src.pipeline.generate_radio_script",
            new_callable=AsyncMock,
            return_value=ScriptGenerationResult(script=script),
        ),
        patch(
            "src.pipeline.send_text_message",
            new_callable=AsyncMock,
        ) as mock_send_text,
        patch(
            "src.pipeline.send_audio_message",
            new_callable=AsyncMock,
        ) as mock_send_audio,
    ):
        outcome = await run_pipeline(settings=settings, target_date=TARGET_DATE)

    assert outcome == PipelineOutcome(status="completed", target_date=TARGET_DATE)
    mock_send_text.assert_not_awaited()
    mock_send_audio.assert_awaited_once_with(settings, script, TARGET_DATE)


@pytest.mark.asyncio
async def test_pipeline_notifies_when_audio_delivery_fails(settings: Settings) -> None:
    with (
        patch(
            "src.pipeline.fetch_newsletters",
            new_callable=AsyncMock,
            return_value=NewsletterFetchResult(newsletters=["content"]),
        ),
        patch(
            "src.pipeline.generate_radio_script",
            new_callable=AsyncMock,
            return_value=ScriptGenerationResult(script="script"),
        ),
        patch(
            "src.pipeline.send_audio_message",
            new_callable=AsyncMock,
            side_effect=RuntimeError("Telegram upload failed"),
        ),
        patch(
            "src.pipeline.send_text_message",
            new_callable=AsyncMock,
        ) as mock_send_text,
    ):
        outcome = await run_pipeline(settings=settings, target_date=TARGET_DATE)

    assert outcome.status == "audio_delivery_failed"
    mock_send_text.assert_awaited_once()
    message = mock_send_text.await_args.args[1]
    assert "failed to send the audio message" in message.lower()
    assert "Telegram upload failed" in message


@pytest.mark.asyncio
async def test_pipeline_joins_newsletter_contents_before_llm(settings: Settings) -> None:
    with (
        patch(
            "src.pipeline.fetch_newsletters",
            new_callable=AsyncMock,
            return_value=NewsletterFetchResult(newsletters=["first", "second"]),
        ) as mock_fetch,
        patch(
            "src.pipeline.generate_radio_script",
            new_callable=AsyncMock,
            return_value=ScriptGenerationResult(script="script"),
        ) as mock_generate,
        patch("src.pipeline.send_audio_message", new_callable=AsyncMock),
    ):
        await run_pipeline(settings=settings, target_date=TARGET_DATE)

    mock_fetch.assert_awaited_once_with(settings, TARGET_DATE)
    mock_generate.assert_awaited_once_with("first\n\nsecond", settings)
