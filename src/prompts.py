from functools import lru_cache
from pathlib import Path

from .config import Settings


def format_newsletter_order_for_prompt(newsletter_names: list[str]) -> str:
    """Turn an ordered newsletter list into natural French phrasing for the prompt."""
    if not newsletter_names:
        return "aucune newsletter spécifiée"
    if len(newsletter_names) == 1:
        return newsletter_names[0]
    if len(newsletter_names) == 2:
        return f"{newsletter_names[0]}, puis {newsletter_names[1]}"
    return ", puis ".join(newsletter_names[:-1]) + f" et enfin {newsletter_names[-1]}"


def resolve_prompt_template_path(settings: Settings) -> Path:
    """Resolve the prompt template path from settings (cwd-relative or absolute)."""
    configured_path = settings.prompt_template_path
    if configured_path.is_absolute():
        return configured_path
    return Path.cwd() / configured_path


@lru_cache(maxsize=8)
def _read_prompt_template(resolved_path: str) -> str:
    path = Path(resolved_path)
    if not path.exists():
        raise FileNotFoundError(
            f"Prompt template not found at {path}. Check PROMPT_TEMPLATE_PATH in your environment."
        )
    return path.read_text(encoding="utf-8")


def load_prompt_template(settings: Settings) -> str:
    """Load the prompt template from disk."""
    resolved_path = resolve_prompt_template_path(settings)
    return _read_prompt_template(str(resolved_path.resolve()))


def build_radio_script_prompt(raw_text: str, settings: Settings) -> str:
    """Build the full LLM prompt from the template file and user-specific settings."""
    template = load_prompt_template(settings)
    return template.format(
        user_first_name=settings.user_first_name,
        newsletter_order=format_newsletter_order_for_prompt(settings.newsletter_order),
        newsletter_limit_name=settings.newsletter_limit_name,
        newsletter_limit_count=settings.newsletter_limit_count,
        raw_text=raw_text,
    )
