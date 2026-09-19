"""Fetch and parse Gmail messages via the Gmail API."""

from __future__ import annotations

import base64
from dataclasses import dataclass

from googleapiclient.discovery import Resource


@dataclass(frozen=True)
class EmailSummary:
    message_id: str
    thread_id: str
    sender: str
    subject: str
    date: str
    snippet: str
    unread: bool

    @property
    def gmail_link(self) -> str:
        return f"https://mail.google.com/mail/u/0/#all/{self.thread_id}"


def _header(headers: list[dict], name: str) -> str:
    for header in headers:
        if header.get("name", "").lower() == name.lower():
            return header.get("value", "")
    return ""


def fetch_messages(
    service: Resource,
    query: str = "newer_than:1d",
    max_results: int = 50,
) -> list[EmailSummary]:
    """Fetch messages matching a Gmail search query and return parsed summaries."""
    message_ids: list[str] = []
    request = service.users().messages().list(userId="me", q=query, maxResults=min(max_results, 500))
    while request is not None and len(message_ids) < max_results:
        response = request.execute()
        message_ids.extend(m["id"] for m in response.get("messages", []))
        request = service.users().messages().list_next(request, response)

    summaries: list[EmailSummary] = []
    for message_id in message_ids[:max_results]:
        msg = (
            service.users()
            .messages()
            .get(userId="me", id=message_id, format="metadata", metadataHeaders=["From", "Subject", "Date"])
            .execute()
        )
        headers = msg.get("payload", {}).get("headers", [])
        summaries.append(
            EmailSummary(
                message_id=msg["id"],
                thread_id=msg["threadId"],
                sender=_header(headers, "From"),
                subject=_header(headers, "Subject") or "(no subject)",
                date=_header(headers, "Date"),
                snippet=msg.get("snippet", ""),
                unread="UNREAD" in msg.get("labelIds", []),
            )
        )
    return summaries


def send_digest_email(
    service: Resource,
    to_address: str,
    subject: str,
    body_text: str,
    body_html: str | None = None,
) -> str:
    """Send the digest to the given address, as HTML with a plain-text fallback when provided."""
    from email.mime.multipart import MIMEMultipart
    from email.mime.text import MIMEText

    if body_html:
        message = MIMEMultipart("alternative")
        message.attach(MIMEText(body_text, "plain"))
        message.attach(MIMEText(body_html, "html"))
    else:
        message = MIMEText(body_text)

    message["to"] = to_address
    message["subject"] = subject
    raw = base64.urlsafe_b64encode(message.as_bytes()).decode()
    sent = service.users().messages().send(userId="me", body={"raw": raw}).execute()
    return sent["id"]
