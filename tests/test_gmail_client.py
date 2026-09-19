import base64
from email import message_from_bytes
from unittest.mock import MagicMock

from personal_email_digest.gmail_client import send_digest_email


def _sent_raw_message(mock_service) -> bytes:
    send_call = mock_service.users.return_value.messages.return_value.send
    raw = send_call.call_args.kwargs["body"]["raw"]
    return base64.urlsafe_b64decode(raw)


def test_send_digest_email_plain_text_only():
    mock_service = MagicMock()
    mock_service.users.return_value.messages.return_value.send.return_value.execute.return_value = {
        "id": "abc123"
    }

    message_id = send_digest_email(mock_service, "to@example.com", "Subject", "plain body")

    assert message_id == "abc123"
    parsed = message_from_bytes(_sent_raw_message(mock_service))
    assert parsed["to"] == "to@example.com"
    assert parsed["subject"] == "Subject"
    assert not parsed.is_multipart()
    assert parsed.get_payload() == "plain body"


def test_send_digest_email_html_creates_multipart_alternative():
    mock_service = MagicMock()
    mock_service.users.return_value.messages.return_value.send.return_value.execute.return_value = {
        "id": "abc123"
    }

    send_digest_email(mock_service, "to@example.com", "Subject", "plain body", "<p>html body</p>")

    parsed = message_from_bytes(_sent_raw_message(mock_service))
    assert parsed.is_multipart()
    payloads = {part.get_content_type(): part.get_payload() for part in parsed.get_payload()}
    assert payloads["text/plain"] == "plain body"
    assert payloads["text/html"] == "<p>html body</p>"
