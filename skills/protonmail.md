---
name: protonmail
description: Manage Proton Mail from the terminal using pmail CLI
tools: [shell]
---

You have access to the `pmail` CLI for managing Proton Mail.

## Install

If `pmail` is not on your PATH, install it first:

```bash
uv tool install git+https://github.com/heikki-laitala/protonmail-cli.git
```

This installs `pmail` as a standalone binary on your PATH. Verify with `pmail --help`.

## Commands

### Reading
- `pmail ls` — List 20 most recent inbox messages
- `pmail ls sent` — Sent folder (also: drafts, starred, archive, all, spam, trash)
- `pmail ls -n 50` — Show N messages
- `pmail read <index>` — Read a message by index
- `pmail thread <conversation-id>` — View full conversation thread
- `pmail count` — Unread counts per folder
- `pmail folders` — List all folders and labels

### Sending
- `pmail send -t user@example.com -s "Subject" -b "Body"`
- Multiple recipients: `-t a@x.com -t b@x.com --cc c@x.com`
- Attachments: `-a file.pdf`
- Body from stdin: `echo "text" | pmail send -t user@x.com -s "Subject"`

### Reply & Forward
- `pmail reply <index> -b "Thanks!"`
- `pmail reply <index> --all -b "Thanks all!"`
- `pmail forward <index> -t other@example.com`

### Management
- `pmail archive <index> [index...]` — Archive messages
- `pmail delete <index>` — Permanently delete
- `pmail star <index>` — Star a message
- `pmail spam <index>` — Mark as spam
- `pmail unread <index>` — Mark as unread
- `pmail download <index> -o ./out` — Save attachments

### Monitoring
- `pmail watch` — Live monitoring (10s polling)
- `pmail watch -i 30 -t 300` — Custom interval and timeout

### Account
- `pmail whoami` — Show account info
- `pmail logout` — Remove session

## Notes
- Message indices are 0-based and **resolve against the inbox only**. Actions like `read`, `reply`, `forward`, `delete`, `archive`, etc. always operate on inbox messages. Do not use indices from non-inbox listings (sent, spam, drafts, etc.) — they will reference the wrong message.
- Always run `pmail ls` (inbox) before using an index for any action.
- Confirm with the user before sending, replying, forwarding, or deleting.
