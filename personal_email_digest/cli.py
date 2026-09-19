"""Command-line entry point for generating (and optionally sending) an email digest."""

from __future__ import annotations

import argparse
import sys
import time
from pathlib import Path

from personal_email_digest.auth import DEFAULT_CREDENTIALS_PATH, DEFAULT_TOKEN_PATH, build_gmail_service
from personal_email_digest.digest import build_digest_html, build_digest_markdown
from personal_email_digest.gmail_client import fetch_messages, send_digest_email


def parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Generate a digest of recent Gmail messages.")
    parser.add_argument("--hours", type=int, default=24, help="Look back this many hours (default: 24).")
    parser.add_argument(
        "--query",
        default=None,
        help="Custom Gmail search query, overriding --hours (e.g. 'is:unread label:important').",
    )
    parser.add_argument(
        "--unread-only",
        action="store_true",
        help="Only include unread messages (composes with --hours or --query).",
    )
    parser.add_argument("--max-results", type=int, default=50, help="Maximum number of emails to include.")
    parser.add_argument(
        "--output", type=Path, default=None, help="Write digest to this file instead of stdout."
    )
    parser.add_argument("--send-to", default=None, help="Email address to send the digest to via Gmail.")
    parser.add_argument("--credentials", type=Path, default=DEFAULT_CREDENTIALS_PATH)
    parser.add_argument("--token", type=Path, default=DEFAULT_TOKEN_PATH)
    parser.add_argument(
        "--daemon",
        action="store_true",
        help="Run continuously, generating a fresh digest every --interval-minutes instead of exiting.",
    )
    parser.add_argument(
        "--interval-minutes",
        type=int,
        default=60,
        help="How often to regenerate the digest in --daemon mode (default: 60).",
    )
    return parser.parse_args(argv)


def _build_query_and_label(args: argparse.Namespace) -> tuple[str, str]:
    query = args.query or f"newer_than:{args.hours}h"
    window_label = args.query or f"last {args.hours}h"
    if args.unread_only:
        query += " is:unread"
        window_label += ", unread only"
    return query, window_label


def run_once(args: argparse.Namespace, service) -> None:
    query, window_label = _build_query_and_label(args)

    emails = fetch_messages(service, query=query, max_results=args.max_results)
    digest_markdown = build_digest_markdown(emails, window_label)

    if args.output:
        args.output.write_text(digest_markdown)
    else:
        sys.stdout.write(digest_markdown)

    if args.send_to:
        digest_html = build_digest_html(emails, window_label)
        send_digest_email(
            service, args.send_to, f"Your Email Digest ({window_label})", digest_markdown, digest_html
        )


def main(argv: list[str] | None = None) -> int:
    args = parse_args(argv)
    service = build_gmail_service(args.credentials, args.token)

    if not args.daemon:
        run_once(args, service)
        return 0

    print(
        f"Running in daemon mode: generating a digest every {args.interval_minutes} minute(s). "
        "Press Ctrl+C to stop.",
        file=sys.stderr,
    )
    try:
        while True:
            run_once(args, service)
            time.sleep(args.interval_minutes * 60)
    except KeyboardInterrupt:
        pass

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
