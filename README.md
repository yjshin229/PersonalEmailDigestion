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

# Custom Gmail search query instead of a time window
email-digest --query "is:unread label:important"

# Generate the digest and email it to yourself
email-digest --send-to you@example.com
```

Run `email-digest --help` for all options.

## Development

```bash
pip install -e ".[dev]"
pytest
```

`credentials.json` and `token.json` hold real credentials and are gitignored
— never commit them.
