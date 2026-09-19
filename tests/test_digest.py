from personal_email_digest.digest import build_digest_html, build_digest_markdown
from personal_email_digest.gmail_client import EmailSummary


def make_email(**overrides) -> EmailSummary:
    defaults = dict(
        message_id="m1",
        thread_id="t1",
        sender='"Alice Example" <alice@example.com>',
        subject="Hello",
        date="Mon, 1 Jan 2024 00:00:00 +0000",
        snippet="This is a test email body snippet.",
        unread=True,
    )
    defaults.update(overrides)
    return EmailSummary(**defaults)


def test_empty_digest():
    result = build_digest_markdown([], "last 24h")
    assert "No new emails" in result
    assert "last 24h" in result


def test_groups_by_sender_and_shows_counts():
    emails = [
        make_email(message_id="1", subject="First"),
        make_email(message_id="2", subject="Second"),
        make_email(message_id="3", sender='"Bob" <bob@example.com>', subject="Third", unread=False),
    ]
    result = build_digest_markdown(emails, "last 24h")

    assert "3 email(s) from 2 sender(s), 2 unread." in result
    assert "## Alice Example (2)" in result
    assert "## Bob (1)" in result
    assert "**First**" in result
    assert "**Second**" in result
    assert "**Third**" in result


def test_unread_flag_only_on_unread():
    emails = [make_email(unread=True), make_email(message_id="2", unread=False, subject="Read one")]
    result = build_digest_markdown(emails, "last 24h")

    lines = result.splitlines()
    hello_line = next(line for line in lines if "**Hello**" in line)
    read_line = next(line for line in lines if "**Read one**" in line)
    assert "\U0001f7e2" in hello_line
    assert "\U0001f7e2" not in read_line


def test_truncates_long_snippets():
    long_snippet = "x" * 300
    emails = [make_email(snippet=long_snippet)]
    result = build_digest_markdown(emails, "last 24h")
    assert "x" * 300 not in result
    assert "…" in result


def test_gmail_link_uses_thread_id():
    email_summary = make_email(thread_id="abc123")
    assert email_summary.gmail_link == "https://mail.google.com/mail/u/0/#all/abc123"


def test_html_digest_empty():
    result = build_digest_html([], "last 24h")
    assert "No new emails" in result
    assert "last 24h" in result


def test_html_digest_escapes_untrusted_content():
    emails = [make_email(subject="<script>alert(1)</script>", snippet="safe & sound")]
    result = build_digest_html(emails, "last 24h")

    assert "<script>" not in result
    assert "&lt;script&gt;" in result
    assert "safe &amp; sound" in result


def test_html_digest_groups_by_sender():
    emails = [
        make_email(message_id="1", subject="First"),
        make_email(message_id="2", sender='"Bob" <bob@example.com>', subject="Second", unread=False),
    ]
    result = build_digest_html(emails, "last 24h")

    assert "<h2>Alice Example (1)</h2>" in result
    assert "<h2>Bob (1)</h2>" in result
    assert "<strong>First</strong>" in result
    assert "<strong>Second</strong>" in result


def test_markdown_digest_shows_category_breakdown():
    emails = [
        make_email(message_id="1", category="Primary"),
        make_email(message_id="2", category="Promotions"),
        make_email(message_id="3", category="Promotions"),
    ]
    result = build_digest_markdown(emails, "last 24h")

    assert "By category: Promotions 2, Primary 1" in result


def test_html_digest_shows_category_breakdown():
    emails = [
        make_email(message_id="1", category="Updates"),
        make_email(message_id="2", category="Updates"),
    ]
    result = build_digest_html(emails, "last 24h")

    assert "By category: Updates 2" in result
