def llm_generation_failed(attempts: int, last_error: str | None) -> str:
    if last_error:
        return (
            f"rAIdio could not generate today's radio script after {attempts} attempts. "
            f"Last error: {last_error}"
        )
    return (
        f"rAIdio could not generate today's radio script after {attempts} attempts: "
        "the LLM returned empty responses."
    )


def no_newsletters_found() -> str:
    return "rAIdio found no newsletters in the mailbox. The morning radio was not generated."


def mailbox_fetch_failed(error: str) -> str:
    return f"rAIdio failed to fetch newsletters from the mailbox: {error}"


def audio_delivery_failed(error: str) -> str:
    return f"rAIdio generated the script but failed to send the audio message: {error}"


def pipeline_failed(stage: str, error: str) -> str:
    return f"rAIdio stopped during {stage}: {error}"
