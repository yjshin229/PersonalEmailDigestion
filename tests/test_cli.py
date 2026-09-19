from personal_email_digest import cli
from personal_email_digest.gmail_client import EmailSummary


def make_email(**overrides) -> EmailSummary:
    defaults = dict(
        message_id="1",
        thread_id="t1",
        sender='"Alice" <alice@example.com>',
        subject="Hello",
        date="Mon, 1 Jan 2024 00:00:00 +0000",
        snippet="A snippet.",
        unread=True,
    )
    defaults.update(overrides)
    return EmailSummary(**defaults)


def test_main_prints_digest_to_stdout(monkeypatch, capsys):
    monkeypatch.setattr(cli, "build_gmail_service", lambda credentials, token: "fake-service")
    captured_query = {}

    def fake_fetch_messages(service, query, max_results):
        captured_query["query"] = query
        captured_query["max_results"] = max_results
        return [make_email()]

    monkeypatch.setattr(cli, "fetch_messages", fake_fetch_messages)

    exit_code = cli.main(["--hours", "6"])

    assert exit_code == 0
    assert captured_query == {"query": "newer_than:6h", "max_results": 50}
    out = capsys.readouterr().out
    assert "Email Digest (last 6h)" in out
    assert "**Hello**" in out


def test_main_writes_digest_to_output_file(monkeypatch, tmp_path):
    monkeypatch.setattr(cli, "build_gmail_service", lambda credentials, token: "fake-service")
    monkeypatch.setattr(cli, "fetch_messages", lambda service, query, max_results: [make_email()])

    output_path = tmp_path / "digest.md"
    exit_code = cli.main(["--output", str(output_path)])

    assert exit_code == 0
    assert "**Hello**" in output_path.read_text()


def test_main_unread_only_composes_with_hours(monkeypatch):
    monkeypatch.setattr(cli, "build_gmail_service", lambda credentials, token: "fake-service")
    captured_query = {}

    def fake_fetch_messages(service, query, max_results):
        captured_query["query"] = query
        return []

    monkeypatch.setattr(cli, "fetch_messages", fake_fetch_messages)

    cli.main(["--hours", "6", "--unread-only"])

    assert captured_query["query"] == "newer_than:6h is:unread"


def test_main_unread_only_composes_with_custom_query(monkeypatch):
    monkeypatch.setattr(cli, "build_gmail_service", lambda credentials, token: "fake-service")
    captured_query = {}

    def fake_fetch_messages(service, query, max_results):
        captured_query["query"] = query
        return []

    monkeypatch.setattr(cli, "fetch_messages", fake_fetch_messages)

    cli.main(["--query", "label:important", "--unread-only"])

    assert captured_query["query"] == "label:important is:unread"


def test_main_uses_custom_query_over_hours(monkeypatch, capsys):
    monkeypatch.setattr(cli, "build_gmail_service", lambda credentials, token: "fake-service")
    captured_query = {}

    def fake_fetch_messages(service, query, max_results):
        captured_query["query"] = query
        return []

    monkeypatch.setattr(cli, "fetch_messages", fake_fetch_messages)

    cli.main(["--query", "is:unread label:important", "--hours", "6"])

    assert captured_query["query"] == "is:unread label:important"
    assert "is:unread label:important" in capsys.readouterr().out


def test_main_sends_digest_email_when_requested(monkeypatch):
    monkeypatch.setattr(cli, "build_gmail_service", lambda credentials, token: "fake-service")
    monkeypatch.setattr(cli, "fetch_messages", lambda service, query, max_results: [make_email()])

    sent = {}

    def fake_send_digest_email(service, to_address, subject, body_text, body_html=None):
        sent["to_address"] = to_address
        sent["subject"] = subject
        sent["body_text"] = body_text
        sent["body_html"] = body_html
        return "sent-id"

    monkeypatch.setattr(cli, "send_digest_email", fake_send_digest_email)

    cli.main(["--send-to", "me@example.com"])

    assert sent["to_address"] == "me@example.com"
    assert "**Hello**" in sent["body_text"]
    assert "<strong>Hello</strong>" in sent["body_html"]


def test_main_does_not_send_email_by_default(monkeypatch):
    monkeypatch.setattr(cli, "build_gmail_service", lambda credentials, token: "fake-service")
    monkeypatch.setattr(cli, "fetch_messages", lambda service, query, max_results: [make_email()])

    def fail_if_called(*args, **kwargs):
        raise AssertionError("send_digest_email should not be called without --send-to")

    monkeypatch.setattr(cli, "send_digest_email", fail_if_called)

    exit_code = cli.main([])

    assert exit_code == 0
