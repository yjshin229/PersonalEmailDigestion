# PersonalEmailDigestion

A small CLI tool that fetches your recent Gmail messages and turns them into a
readable Markdown digest, grouped by sender, with unread emails flagged and
links back to each message.

## Setup

1. In [Google Cloud Console](https://console.cloud.google.com/), create a
   project, enable the **Gmail API**, and create an OAuth client ID of type
   "Desktop app". Download the client secrets and save them as
   `credentials.json` in the project root.
2. Install the package (editable install also gives you the `email-digest` command):

   ```bash
   pip install -e .
   ```

3. Run the digest:

   ```bash
   email-digest
   # or: python -m personal_email_digest.cli
   ```

   The first run opens a browser to complete the OAuth consent flow and
   caches the resulting token in `token.json` for future runs.

## Usage

```bash
# Digest of the last 24 hours (default), printed to stdout
email-digest

# Digest of the last 3 days, written to a file
email-digest --hours 72 --output digest.md

# Only unread messages from the last 3 days
email-digest --hours 72 --unread-only

# Custom Gmail search query instead of a time window
email-digest --query "label:important"

# Generate the digest and email it to yourself
email-digest --send-to you@example.com
```

Run `email-digest --help` for all options.

## Scheduling

Run the digest automatically, so it's waiting for you instead of something
you have to remember to run.

**Built-in daemon mode** — keeps running and regenerates the digest on an
interval (useful in a container or a background process manager):

```bash
email-digest --daemon --interval-minutes 60 --send-to you@example.com
```

**cron** (Linux/macOS) — e.g. every morning at 7am, run `crontab -e` and add:

```cron
0 7 * * * cd /path/to/PersonalEmailDigestion && .venv/bin/email-digest --send-to you@example.com >> digest.log 2>&1
```

**systemd timer** (Linux) — create `~/.config/systemd/user/email-digest.service`:

```ini
[Service]
WorkingDirectory=/path/to/PersonalEmailDigestion
ExecStart=/path/to/PersonalEmailDigestion/.venv/bin/email-digest --send-to you@example.com
```

and `~/.config/systemd/user/email-digest.timer`:

```ini
[Timer]
OnCalendar=*-*-* 07:00:00
Persistent=true

[Install]
WantedBy=timers.target
```

then `systemctl --user enable --now email-digest.timer`.

Either way, run the tool interactively once first so the OAuth consent flow
completes and `token.json` is cached — a scheduled run can't open a browser.

## Development

```bash
pip install -e ".[dev]"
pytest
ruff check .
```

`credentials.json` and `token.json` hold real credentials and are gitignored
— never commit them.
