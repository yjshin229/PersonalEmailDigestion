"""Build a readable digest from a list of email summaries."""

from __future__ import annotations

import re
from collections import defaultdict

from personal_email_digest.gmail_client import EmailSummary

_SNIPPET_MAX_LEN = 140


def _sender_name(sender: str) -> str:
    match = re.match(r'^\s*"?([^"<]+?)"?\s*<', sender)
    return match.group(1).strip() if match else sender.strip()


def _truncate(text: str, max_len: int = _SNIPPET_MAX_LEN) -> str:
    text = text.strip()
    return text if len(text) <= max_len else text[: max_len - 1].rstrip() + "…"


def build_digest_markdown(emails: list[EmailSummary], window_label: str) -> str:
    """Render a Markdown digest grouping emails by sender, newest-looking first."""
    if not emails:
        return f"# Email Digest ({window_label})\n\nNo new emails.\n"

    unread_count = sum(1 for e in emails if e.unread)
    by_sender: dict[str, list[EmailSummary]] = defaultdict(list)
    for email_summary in emails:
        by_sender[_sender_name(email_summary.sender)].append(email_summary)

    lines = [
        f"# Email Digest ({window_label})",
        "",
        f"{len(emails)} email(s) from {len(by_sender)} sender(s), {unread_count} unread.",
        "",
    ]

    for sender in sorted(by_sender, key=lambda s: -len(by_sender[s])):
        sender_emails = by_sender[sender]
        lines.append(f"## {sender} ({len(sender_emails)})")
        for e in sender_emails:
            flag = " \U0001f7e2" if e.unread else ""
            lines.append(f"- **{e.subject}**{flag} — {_truncate(e.snippet)}")
            lines.append(f"  [Open in Gmail]({e.gmail_link})")
        lines.append("")

    return "\n".join(lines).rstrip() + "\n"
