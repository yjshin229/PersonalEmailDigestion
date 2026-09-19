"""Build a readable digest from a list of email summaries."""

from __future__ import annotations

import html
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


def _group_by_sender(emails: list[EmailSummary]) -> dict[str, list[EmailSummary]]:
    by_sender: dict[str, list[EmailSummary]] = defaultdict(list)
    for email_summary in emails:
        by_sender[_sender_name(email_summary.sender)].append(email_summary)
    return dict(sorted(by_sender.items(), key=lambda item: -len(item[1])))


def _category_counts(emails: list[EmailSummary]) -> dict[str, int]:
    counts: dict[str, int] = defaultdict(int)
    for email_summary in emails:
        counts[email_summary.category] += 1
    return dict(sorted(counts.items(), key=lambda item: -item[1]))


def _category_summary_text(emails: list[EmailSummary]) -> str:
    counts = _category_counts(emails)
    return "By category: " + ", ".join(f"{category} {count}" for category, count in counts.items())


def build_digest_markdown(emails: list[EmailSummary], window_label: str) -> str:
    """Render a Markdown digest grouping emails by sender, newest-looking first."""
    if not emails:
        return f"# Email Digest ({window_label})\n\nNo new emails.\n"

    unread_count = sum(1 for e in emails if e.unread)
    by_sender = _group_by_sender(emails)

    lines = [
        f"# Email Digest ({window_label})",
        "",
        f"{len(emails)} email(s) from {len(by_sender)} sender(s), {unread_count} unread.",
        _category_summary_text(emails),
        "",
    ]

    for sender, sender_emails in by_sender.items():
        lines.append(f"## {sender} ({len(sender_emails)})")
        for e in sender_emails:
            flag = " \U0001f7e2" if e.unread else ""
            lines.append(f"- **{e.subject}**{flag} — {_truncate(e.snippet)}")
            lines.append(f"  [Open in Gmail]({e.gmail_link})")
        lines.append("")

    return "\n".join(lines).rstrip() + "\n"


def build_digest_html(emails: list[EmailSummary], window_label: str) -> str:
    """Render the same digest as a self-contained HTML fragment, for HTML emails."""
    title = html.escape(f"Email Digest ({window_label})")
    if not emails:
        return f"<h1>{title}</h1><p>No new emails.</p>"

    unread_count = sum(1 for e in emails if e.unread)
    by_sender = _group_by_sender(emails)

    parts = [
        f"<h1>{title}</h1>",
        f"<p>{len(emails)} email(s) from {len(by_sender)} sender(s), {unread_count} unread.</p>",
        f"<p>{html.escape(_category_summary_text(emails))}</p>",
    ]

    for sender, sender_emails in by_sender.items():
        parts.append(f"<h2>{html.escape(sender)} ({len(sender_emails)})</h2><ul>")
        for e in sender_emails:
            flag = " \U0001f7e2" if e.unread else ""
            subject = html.escape(e.subject)
            snippet = html.escape(_truncate(e.snippet))
            link = html.escape(e.gmail_link)
            parts.append(
                f"<li><strong>{subject}</strong>{flag} — {snippet}"
                f'<br><a href="{link}">Open in Gmail</a></li>'
            )
        parts.append("</ul>")

    return "\n".join(parts)
