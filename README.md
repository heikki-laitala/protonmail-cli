# pmail — Proton Mail CLI

A command-line interface for reading and sending Proton Mail emails, built on top of [protonmail-api-client](https://github.com/opulentfox-29/protonmail-api-client).

## Install

```bash
git clone https://github.com/heikki-laitala/protonmail-cli.git
cd protonmail-cli
uv sync
```

Then run commands with:

```bash
uv run pmail --help
```

Or use the wrapper script:

```bash
./pmail.sh --help
```

## Login

```bash
pmail login -u you@proton.me
```

Session is saved to `~/.config/pmail/session.pickle` and auto-refreshes. You only need to log in once.

Supports 2FA — you'll be prompted for the code if enabled.

## Usage

### Read emails

```bash
pmail ls                        # list inbox (20 most recent)
pmail ls sent                   # list sent folder
pmail ls -n 50                  # show 50 messages
pmail read 0                    # read message #0 from inbox
pmail thread <conversation-id>  # read full conversation
pmail count                     # unread counts per folder
pmail folders                   # list all folders & labels
```

### Send emails

```bash
pmail send -t user@example.com -s "Hello" -b "Hi there!"
pmail send -t a@x.com -t b@x.com --cc c@x.com -s "Meeting" -b "Let's meet"
pmail send -t user@x.com -s "Report" -a report.pdf -b "See attached."
echo "piped body" | pmail send -t user@x.com -s "From stdin"
```

### Reply & forward

```bash
pmail reply 0 -b "Thanks!"            # reply to inbox message #0
pmail reply 0 --all -b "Thanks all!"  # reply-all
pmail forward 0 -t other@example.com  # forward message #0
```

### Manage emails

```bash
pmail archive 0 1 2       # archive messages by index
pmail delete 0             # permanently delete
pmail star 3               # star a message
pmail spam 5               # mark as spam
pmail unread 0             # mark as unread
pmail download 0 -o ./out  # download attachments
```

### Watch for new messages

```bash
pmail watch                # live watch (poll every 10s)
pmail watch -i 30 -t 300   # poll every 30s, stop after 5 min
```

### Account

```bash
pmail whoami   # show account info
pmail logout   # remove saved session
```

## Folders

`pmail ls` accepts these folder names: `inbox`, `sent`, `drafts`, `starred`, `archive`, `all`, `spam`, `trash`.

## Notes

- Proton Mail does not offer a public API. This tool uses the community [protonmail-api-client](https://github.com/opulentfox-29/protonmail-api-client) library which may break if Proton changes their internal APIs.
- Session files contain sensitive authentication data — do not share them.
- CAPTCHA may be triggered on login. The library attempts automatic solving; if that fails, you'll be prompted for manual token entry.

## License

MIT
