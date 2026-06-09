from datetime import date

from .config import Settings, load_settings
from .pipeline import PipelineOutcome, run_pipeline


async def run_newsletter_process(
    target_date: date,
    settings: Settings | None = None,
) -> PipelineOutcome:
    """Run the newsletter pipeline for a specific date."""
    resolved_settings = settings or load_settings()
    return await run_pipeline(settings=resolved_settings, target_date=target_date)
