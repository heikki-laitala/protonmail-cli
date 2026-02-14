"""Proton Mail CLI — read and send emails from the terminal."""

import getpass
import sys

import click

from protonmail_cli.config import (
    SESSION_FILE,
    ensure_config_dir,
    get_client,
)
from protonmail_cli.formatting import (
    SYSTEM_LABELS,
    console,
    format_size,
    format_timestamp,
    print_message,
    print_message_list,
    strip_html,
)


@click.group()
@click.version_option(version="0.1.0")
def cli():
    """pmail — Proton Mail from the command line."""


# ---------------------------------------------------------------------------
# Auth
# ---------------------------------------------------------------------------

@cli.command()
@click.option("--username", "-u", prompt="Username", help="Proton Mail username/email")
def login(username):
    """Authenticate and save session."""
    from protonmail import ProtonMail

    password = getpass.getpass("Password: ")
    ensure_config_dir()

    proton = ProtonMail(logging_level=4)

    def get_2fa():
        return input("2FA code: ")

    try:
        with console.status("Logging in..."):
            proton.login(username, password, getter_2fa_code=get_2fa)
    except Exception as e:
        raise SystemExit(f"Login failed: {e}")

    proton.save_session(str(SESSION_FILE))
    console.print(f"[green]Logged in as {username}[/]")
    console.print(f"[dim]Session saved to {SESSION_FILE}[/]")


@cli.command()
def logout():
    """Remove saved session."""
    if SESSION_FILE.exists():
        SESSION_FILE.unlink()
        console.print("[green]Session removed.[/]")
    else:
        console.print("[yellow]No active session.[/]")


@cli.command()
def whoami():
    """Show current account info."""
    proton = get_client()
    for addr in proton.account_addresses:
        name = f" ({addr.name})" if addr.name else ""
        console.print(f"{addr.email}{name}")


# ---------------------------------------------------------------------------
# Reading emails
# ---------------------------------------------------------------------------

FOLDER_ALIASES = {
    "inbox": "0",
    "drafts": "1",
    "sent": "2",
    "starred": "3",
    "archive": "4",
    "all": "5",
    "spam": "6",
    "trash": "7",
}


@cli.command()
@click.argument("folder", default="inbox")
@click.option("-n", "--limit", default=20, help="Number of messages to show")
@click.option("-p", "--page", default=0, help="Page number (0-indexed)")
def ls(folder, limit, page):
    """List messages. FOLDER can be: inbox, sent, drafts, starred, archive, spam, trash, all."""
    proton = get_client()
    label_id = FOLDER_ALIASES.get(folder.lower(), folder)
    folder_name = SYSTEM_LABELS.get(label_id, folder)

    with console.status(f"Fetching {folder_name}..."):
        messages = proton.get_messages_by_page(page=page, page_size=limit)
        # Filter by label if not "all"
        if label_id != "5":
            messages = [m for m in proton.get_messages(page_size=limit, label_or_id=label_id)]
            messages = messages[:limit]

    if not messages:
        console.print(f"[dim]No messages in {folder_name}.[/]")
        return

    print_message_list(messages, folder_name)
    console.print(f"\n[dim]Use [bold]pmail read <#>[/bold] with the # from this list.[/]")


@cli.command()
@click.argument("message_ref")
@click.option("--html", "show_html", is_flag=True, help="Show raw HTML body")
@click.option("--no-mark-read", is_flag=True, help="Don't mark as read")
def read(message_ref, show_html, no_mark_read):
    """Read a message by ID or index number from the last listing."""
    proton = get_client()

    # If it looks like a small number, treat it as an inbox index
    msg_id = message_ref
    if message_ref.isdigit() and len(message_ref) <= 4:
        idx = int(message_ref)
        with console.status("Fetching inbox..."):
            messages = proton.get_messages(page_size=idx + 1, label_or_id="0")
        if idx >= len(messages):
            raise SystemExit(f"Index {idx} out of range (have {len(messages)} messages)")
        msg_id = messages[idx].id

    with console.status("Reading message..."):
        message = proton.read_message(msg_id, mark_as_read=not no_mark_read)

    if show_html:
        console.print(message.body)
    else:
        print_message(message)


@cli.command()
@click.argument("conversation_ref")
def thread(conversation_ref):
    """Read all messages in a conversation thread."""
    proton = get_client()

    with console.status("Loading conversation..."):
        messages = proton.read_conversation(conversation_ref)

    for i, msg in enumerate(messages):
        if i > 0:
            console.rule()
        print_message(msg)


# ---------------------------------------------------------------------------
# Sending emails
# ---------------------------------------------------------------------------

@cli.command()
@click.option("--to", "-t", "recipients", required=True, multiple=True, help="Recipient email(s)")
@click.option("--cc", multiple=True, help="CC recipient(s)")
@click.option("--bcc", multiple=True, help="BCC recipient(s)")
@click.option("--subject", "-s", required=True, help="Subject line")
@click.option("--body", "-b", help="Message body (plain text). Omit to read from stdin.")
@click.option("--html", "is_html", is_flag=True, help="Treat body as HTML")
@click.option("--attach", "-a", multiple=True, type=click.Path(exists=True), help="File attachment(s)")
def send(recipients, cc, bcc, subject, body, is_html, attach):
    """Send an email."""
    proton = get_client()

    if body is None:
        if sys.stdin.isatty():
            console.print("[dim]Enter message body (Ctrl+D to finish):[/]")
        body = sys.stdin.read()

    attachments = []
    for filepath in attach:
        from pathlib import Path
        p = Path(filepath)
        content = p.read_bytes()
        att = proton.create_attachment(content=content, name=p.name)
        attachments.append(att)

    if not is_html:
        # Wrap plain text in basic HTML for proper rendering
        escaped = body.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")
        html_body = f"<pre>{escaped}</pre>"
    else:
        html_body = body

    msg = proton.create_message(
        recipients=list(recipients),
        cc=list(cc) if cc else [],
        bcc=list(bcc) if bcc else [],
        subject=subject,
        body=html_body,
        attachments=attachments,
    )

    with console.status("Sending..."):
        sent = proton.send_message(msg, is_html=True)

    console.print(f"[green]Sent![/] Subject: {sent.subject}")


@cli.command()
@click.argument("message_ref")
@click.option("--body", "-b", help="Reply body (plain text). Omit to read from stdin.")
@click.option("--all", "reply_all", is_flag=True, help="Reply to all recipients")
def reply(message_ref, body, reply_all):
    """Reply to a message."""
    proton = get_client()

    # Resolve index to ID
    msg_id = message_ref
    if message_ref.isdigit() and len(message_ref) <= 4:
        idx = int(message_ref)
        with console.status("Fetching inbox..."):
            messages = proton.get_messages(page_size=idx + 1, label_or_id="0")
        if idx >= len(messages):
            raise SystemExit(f"Index {idx} out of range")
        msg_id = messages[idx].id

    with console.status("Reading original..."):
        original = proton.read_message(msg_id)

    if body is None:
        if sys.stdin.isatty():
            console.print(f"[dim]Replying to: {original.subject}[/]")
            console.print(f"[dim]From: {original.sender.address}[/]")
            console.print("[dim]Enter reply (Ctrl+D to finish):[/]")
        body = sys.stdin.read()

    recipients = [original.sender.address]
    cc = []
    if reply_all:
        # Add all original recipients except ourselves
        my_addresses = {a.email.lower() for a in proton.account_addresses}
        for r in original.recipients:
            if r.address.lower() not in my_addresses:
                recipients.append(r.address)
        for r in original.cc:
            if r.address.lower() not in my_addresses:
                cc.append(r.address)

    escaped = body.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")
    html_body = f"<pre>{escaped}</pre>"

    reply_msg = proton.create_message(
        recipients=recipients,
        cc=cc,
        subject=f"Re: {original.subject}" if not original.subject.startswith("Re:") else original.subject,
        body=html_body,
        in_reply_to=original.external_id,
    )

    with console.status("Sending reply..."):
        sent = proton.send_message(reply_msg, is_html=True)

    console.print(f"[green]Reply sent![/] To: {', '.join(recipients)}")


@cli.command()
@click.argument("message_ref")
@click.option("--body", "-b", help="Forward body (plain text). Omit to read from stdin.")
@click.option("--to", "-t", "recipients", required=True, multiple=True, help="Forward to email(s)")
def forward(message_ref, body, recipients):
    """Forward a message."""
    proton = get_client()

    msg_id = message_ref
    if message_ref.isdigit() and len(message_ref) <= 4:
        idx = int(message_ref)
        with console.status("Fetching inbox..."):
            messages = proton.get_messages(page_size=idx + 1, label_or_id="0")
        if idx >= len(messages):
            raise SystemExit(f"Index {idx} out of range")
        msg_id = messages[idx].id

    with console.status("Reading original..."):
        original = proton.read_message(msg_id)

    note = ""
    if body is not None:
        escaped = body.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")
        note = f"<pre>{escaped}</pre><hr>"
    elif sys.stdin.isatty():
        console.print("[dim]Add a note (Ctrl+D to finish, or just Ctrl+D for none):[/]")
        raw = sys.stdin.read()
        if raw.strip():
            escaped = raw.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")
            note = f"<pre>{escaped}</pre><hr>"

    fwd_body = f"""{note}
<p><b>---------- Forwarded message ----------</b><br>
From: {original.sender.address}<br>
Date: {format_timestamp(original.time)}<br>
Subject: {original.subject}</p>
{original.body}"""

    fwd_msg = proton.create_message(
        recipients=list(recipients),
        subject=f"Fwd: {original.subject}",
        body=fwd_body,
    )

    with console.status("Forwarding..."):
        sent = proton.send_message(fwd_msg, is_html=True)

    console.print(f"[green]Forwarded![/] To: {', '.join(recipients)}")


# ---------------------------------------------------------------------------
# Managing emails
# ---------------------------------------------------------------------------

@cli.command()
@click.argument("message_refs", nargs=-1, required=True)
def delete(message_refs):
    """Delete message(s) by ID or index number."""
    proton = get_client()
    ids = _resolve_refs(proton, message_refs)

    with console.status("Deleting..."):
        proton.delete_messages(ids)

    console.print(f"[green]Deleted {len(ids)} message(s).[/]")


@cli.command()
@click.argument("message_refs", nargs=-1, required=True)
def archive(message_refs):
    """Move message(s) to archive."""
    proton = get_client()
    ids = _resolve_refs(proton, message_refs)

    with console.status("Archiving..."):
        proton.set_label_for_messages("4", ids)
        # Remove from inbox
        proton.unset_label_for_messages("0", ids)

    console.print(f"[green]Archived {len(ids)} message(s).[/]")


@cli.command()
@click.argument("message_refs", nargs=-1, required=True)
def spam(message_refs):
    """Move message(s) to spam."""
    proton = get_client()
    ids = _resolve_refs(proton, message_refs)

    with console.status("Marking spam..."):
        proton.set_label_for_messages("6", ids)
        proton.unset_label_for_messages("0", ids)

    console.print(f"[green]Marked {len(ids)} message(s) as spam.[/]")


@cli.command()
@click.argument("message_refs", nargs=-1, required=True)
def star(message_refs):
    """Star message(s)."""
    proton = get_client()
    ids = _resolve_refs(proton, message_refs)

    with console.status("Starring..."):
        proton.set_label_for_messages("10", ids)

    console.print(f"[green]Starred {len(ids)} message(s).[/]")


@cli.command()
@click.argument("message_refs", nargs=-1, required=True)
def unread(message_refs):
    """Mark message(s) as unread."""
    proton = get_client()
    ids = _resolve_refs(proton, message_refs)

    with console.status("Marking unread..."):
        proton.mark_messages_as_unread(ids)

    console.print(f"[green]Marked {len(ids)} message(s) as unread.[/]")


# ---------------------------------------------------------------------------
# Folders & labels
# ---------------------------------------------------------------------------

@cli.command()
def folders():
    """List all folders and labels."""
    proton = get_client()

    with console.status("Fetching labels..."):
        all_labels = proton.get_all_labels()

    console.print("[bold]System folders:[/]")
    for label in all_labels:
        if label.type == 4:
            console.print(f"  {label.name:<20} [dim](id: {label.id})[/]")

    user_labels = [l for l in all_labels if l.type == 1]
    if user_labels:
        console.print("\n[bold]Labels:[/]")
        for label in user_labels:
            console.print(f"  {label.name:<20} [dim](id: {label.id})[/]")

    user_folders = [l for l in all_labels if l.type == 3]
    if user_folders:
        console.print("\n[bold]Custom folders:[/]")
        for label in user_folders:
            console.print(f"  {label.name:<20} [dim](id: {label.id})[/]")


@cli.command()
def count():
    """Show message counts per folder."""
    proton = get_client()

    with console.status("Fetching counts..."):
        counts = proton.get_messages_count()

    from rich.table import Table
    table = Table(title="Message counts")
    table.add_column("Folder", style="cyan")
    table.add_column("Total", justify="right")
    table.add_column("Unread", justify="right", style="yellow")

    for entry in counts:
        label_id = entry.get("LabelID", "")
        name = SYSTEM_LABELS.get(label_id, label_id)
        if label_id not in SYSTEM_LABELS:
            continue
        total = entry.get("Total", 0)
        unread_count = entry.get("Unread", 0)
        unread_str = str(unread_count) if unread_count > 0 else ""
        table.add_row(name, str(total), unread_str)

    console.print(table)


# ---------------------------------------------------------------------------
# Attachments
# ---------------------------------------------------------------------------

@cli.command()
@click.argument("message_ref")
@click.option("--output", "-o", type=click.Path(), default=".", help="Output directory")
def download(message_ref, output):
    """Download attachments from a message."""
    from pathlib import Path
    proton = get_client()

    msg_id = message_ref
    if message_ref.isdigit() and len(message_ref) <= 4:
        idx = int(message_ref)
        with console.status("Fetching inbox..."):
            messages = proton.get_messages(page_size=idx + 1, label_or_id="0")
        if idx >= len(messages):
            raise SystemExit(f"Index {idx} out of range")
        msg_id = messages[idx].id

    with console.status("Reading message..."):
        message = proton.read_message(msg_id)

    if not message.attachments:
        console.print("[yellow]No attachments.[/]")
        return

    out_dir = Path(output)
    out_dir.mkdir(parents=True, exist_ok=True)

    with console.status("Downloading attachments..."):
        proton.download_files(message.attachments)

    for att in message.attachments:
        if att.is_decrypted and att.content:
            filepath = out_dir / att.name
            filepath.write_bytes(att.content)
            console.print(f"[green]Saved:[/] {filepath} ({format_size(att.size)})")
        else:
            console.print(f"[yellow]Skipped:[/] {att.name} (could not decrypt)")


# ---------------------------------------------------------------------------
# Watch for new messages
# ---------------------------------------------------------------------------

@cli.command()
@click.option("--timeout", "-t", default=0, help="Timeout in seconds (0 = forever)")
@click.option("--interval", "-i", default=10, help="Poll interval in seconds")
def watch(timeout, interval):
    """Watch for new messages (live)."""
    proton = get_client()

    console.print(f"[dim]Watching for new messages (poll every {interval}s)... Press Ctrl+C to stop.[/]")

    def on_event(response):
        new_msgs = response.get("Messages", [])
        for entry in new_msgs:
            action = entry.get("Action")
            msg_data = entry.get("Message", {})
            if action == 1:  # new message
                sender = msg_data.get("SenderAddress", "unknown")
                subject = msg_data.get("Subject", "(no subject)")
                console.print(f"[bold green]New:[/] {sender} — {subject}")

    try:
        proton.event_polling(
            on_event,
            interval=interval,
            timeout=timeout,
            rise_timeout=False,
        )
    except KeyboardInterrupt:
        console.print("\n[dim]Stopped watching.[/]")


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _resolve_refs(proton, refs):
    """Resolve message references (index numbers or IDs) to message IDs."""
    ids = []
    inbox_cache = None
    for ref in refs:
        if ref.isdigit() and len(ref) <= 4:
            idx = int(ref)
            if inbox_cache is None:
                max_idx = max(int(r) for r in refs if r.isdigit() and len(r) <= 4)
                with console.status("Fetching inbox..."):
                    inbox_cache = proton.get_messages(page_size=max_idx + 1, label_or_id="0")
            if idx >= len(inbox_cache):
                raise SystemExit(f"Index {idx} out of range")
            ids.append(inbox_cache[idx].id)
        else:
            ids.append(ref)
    return ids


if __name__ == "__main__":
    cli()
