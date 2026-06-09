from src.user_messages import (
    audio_delivery_failed,
    llm_generation_failed,
    mailbox_fetch_failed,
    no_newsletters_found,
    pipeline_failed,
)


def test_llm_generation_failed_includes_last_error() -> None:
    message = llm_generation_failed(3, "quota exceeded")

    assert "after 3 attempts" in message
    assert "quota exceeded" in message


def test_llm_generation_failed_without_last_error() -> None:
    message = llm_generation_failed(3, None)

    assert "empty responses" in message


def test_mailbox_fetch_failed_describes_error() -> None:
    message = mailbox_fetch_failed("IMAP auth failed")

    assert "failed to fetch newsletters" in message.lower()
    assert "IMAP auth failed" in message


def test_no_newsletters_found_message() -> None:
    message = no_newsletters_found()

    assert "no newsletters" in message.lower()


def test_audio_delivery_failed_describes_error() -> None:
    message = audio_delivery_failed("Telegram upload failed")

    assert "failed to send the audio message" in message.lower()
    assert "Telegram upload failed" in message


def test_pipeline_failed_describes_stage_and_error() -> None:
    message = pipeline_failed("script generation", "prompt file missing")

    assert "script generation" in message
    assert "prompt file missing" in message
