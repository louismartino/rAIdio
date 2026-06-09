import asyncio
import email
import logging
import ssl
from dataclasses import dataclass
from datetime import date, timedelta
from email.message import Message
from email.policy import default

import certifi
from bs4 import BeautifulSoup
from imapclient import IMAPClient

from .config import IMAP_FOLDER, IMAP_HOST, Settings

logger = logging.getLogger(__name__)


def _imap_ssl_context() -> ssl.SSLContext:
    """Use certifi's CA bundle — fixes CERTIFICATE_VERIFY_FAILED on macOS Python installs."""
    return ssl.create_default_context(cafile=certifi.where())


@dataclass(frozen=True)
class NewsletterFetchResult:
    newsletters: list[str]
    error: str | None = None


def _extract_html_body(email_message: Message) -> str:
    if email_message.is_multipart():
        for part in email_message.walk():
            if part.get_content_type() == "text/html":
                payload = part.get_payload(decode=True)
                if isinstance(payload, bytes):
                    return payload.decode(errors="ignore")
                return ""
        return ""

    payload = email_message.get_payload(decode=True)
    if isinstance(payload, bytes):
        return payload.decode(errors="ignore")
    return ""


def _fetch_newsletters_sync(settings: Settings, target_date: date) -> NewsletterFetchResult:
    """Blocking IMAP fetch — run via asyncio.to_thread from the async entrypoint."""
    logger.info("Connecting to mailbox for date %s...", target_date.isoformat())
    newsletters: list[str] = []

    try:
        with IMAPClient(IMAP_HOST, use_uid=True, ssl_context=_imap_ssl_context()) as imap_client:
            imap_client.login(settings.email_user, settings.email_pass.get_secret_value())
            imap_client.select_folder(IMAP_FOLDER)
            next_day = target_date + timedelta(days=1)
            messages = imap_client.search(["SINCE", target_date, "BEFORE", next_day])
            logger.info("Found %d newsletter(s) for %s.", len(messages), target_date.isoformat())

            if not messages:
                return NewsletterFetchResult(newsletters=[])

            for msg_id, data in imap_client.fetch(messages, ["RFC822"]).items():
                try:
                    raw_email = data[b"RFC822"]
                    email_message = email.message_from_bytes(raw_email, policy=default)
                    subject = email_message["subject"] or "Sans sujet"
                    logger.info("Processing: %s", subject)

                    body = _extract_html_body(email_message)
                    soup = BeautifulSoup(body, "html.parser")
                    clean_text = soup.get_text(separator=" ", strip=True)
                    newsletters.append(f"Sujet: {subject}\nContenu: {clean_text}")
                except Exception:
                    logger.exception("Failed to process email %s", msg_id)

        return NewsletterFetchResult(newsletters=newsletters)
    except Exception as exc:
        logger.exception("Mail fetch failed")
        return NewsletterFetchResult(newsletters=[], error=str(exc))


async def fetch_newsletters(settings: Settings, target_date: date) -> NewsletterFetchResult:
    """Fetch emails from the Newsletters folder for the given date."""
    return await asyncio.to_thread(_fetch_newsletters_sync, settings, target_date)
