from email.message import EmailMessage
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText

from src.newsletter_fetcher import _extract_html_body


def test_extract_html_body_from_simple_html_message() -> None:
    message = EmailMessage()
    message.set_content("<p>Hello <strong>world</strong></p>", subtype="html")

    body = _extract_html_body(message)

    assert "Hello" in body
    assert "world" in body


def test_extract_html_body_from_multipart_message() -> None:
    message = MIMEMultipart("alternative")
    message.attach(MIMEText("Plain text fallback", "plain"))
    message.attach(MIMEText("<p>Newsletter <em>content</em></p>", "html"))

    body = _extract_html_body(message)

    assert "Newsletter" in body
    assert "content" in body
    assert "Plain text fallback" not in body


def test_extract_html_body_returns_plain_text_for_non_multipart_message() -> None:
    message = EmailMessage()
    message.set_content("Plain text only", subtype="plain")

    assert _extract_html_body(message).strip() == "Plain text only"


def test_extract_html_body_returns_empty_when_multipart_has_no_html() -> None:
    message = MIMEMultipart("alternative")
    message.attach(MIMEText("Plain text only", "plain"))

    assert _extract_html_body(message) == ""
