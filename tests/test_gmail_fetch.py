from unittest.mock import MagicMock

from personal_email_digest.gmail_client import fetch_messages


def _message_payload(message_id: str, thread_id: str, subject: str, unread: bool) -> dict:
    return {
        "id": message_id,
        "threadId": thread_id,
        "snippet": f"snippet for {subject}",
        "labelIds": ["UNREAD"] if unread else ["INBOX"],
        "payload": {
            "headers": [
                {"name": "From", "value": '"Alice" <alice@example.com>'},
                {"name": "Subject", "value": subject},
                {"name": "Date", "value": "Mon, 1 Jan 2024 00:00:00 +0000"},
            ]
        },
    }


def test_fetch_messages_parses_headers_and_unread_flag():
    mock_service = MagicMock()
    messages = mock_service.users.return_value.messages.return_value
    messages.list.return_value.execute.return_value = {"messages": [{"id": "1"}]}
    messages.list_next.return_value = None
    messages.get.return_value.execute.return_value = _message_payload("1", "t1", "Hi there", unread=True)

    result = fetch_messages(mock_service, query="is:unread", max_results=10)

    assert len(result) == 1
    email_summary = result[0]
    assert email_summary.message_id == "1"
    assert email_summary.thread_id == "t1"
    assert email_summary.sender == '"Alice" <alice@example.com>'
    assert email_summary.subject == "Hi there"
    assert email_summary.snippet == "snippet for Hi there"
    assert email_summary.unread is True


def test_fetch_messages_missing_subject_gets_placeholder():
    mock_service = MagicMock()
    messages = mock_service.users.return_value.messages.return_value
    messages.list.return_value.execute.return_value = {"messages": [{"id": "1"}]}
    messages.list_next.return_value = None
    payload = _message_payload("1", "t1", "", unread=False)
    payload["payload"]["headers"] = [h for h in payload["payload"]["headers"] if h["name"] != "Subject"]
    messages.get.return_value.execute.return_value = payload

    result = fetch_messages(mock_service, max_results=10)

    assert result[0].subject == "(no subject)"


def test_fetch_messages_follows_pagination():
    mock_service = MagicMock()
    messages = mock_service.users.return_value.messages.return_value

    page_1 = {"messages": [{"id": "1"}, {"id": "2"}]}
    page_2 = {"messages": [{"id": "3"}]}
    messages.list.return_value.execute.return_value = page_1

    next_page_request = MagicMock()
    next_page_request.execute.return_value = page_2
    messages.list_next.side_effect = [next_page_request, None]

    messages.get.return_value.execute.side_effect = [
        _message_payload("1", "t1", "First", unread=True),
        _message_payload("2", "t2", "Second", unread=True),
        _message_payload("3", "t3", "Third", unread=False),
    ]

    result = fetch_messages(mock_service, max_results=10)

    assert [e.message_id for e in result] == ["1", "2", "3"]


def test_fetch_messages_respects_max_results():
    mock_service = MagicMock()
    messages = mock_service.users.return_value.messages.return_value
    messages.list.return_value.execute.return_value = {
        "messages": [{"id": "1"}, {"id": "2"}, {"id": "3"}]
    }
    messages.list_next.return_value = None
    messages.get.return_value.execute.side_effect = [
        _message_payload("1", "t1", "First", unread=True),
        _message_payload("2", "t2", "Second", unread=True),
    ]

    result = fetch_messages(mock_service, max_results=2)

    assert [e.message_id for e in result] == ["1", "2"]
