import asyncio
import os
from datetime import date

from .logging_setup import setup_logging
from .pipeline import run_pipeline


def _target_date_from_env() -> date | None:
    raw = os.environ.get("TARGET_DATE", "").strip()
    if not raw:
        return None
    return date.fromisoformat(raw)


def main() -> None:
    setup_logging()
    asyncio.run(run_pipeline(target_date=_target_date_from_env()))


if __name__ == "__main__":
    main()
