"""Output formatting helpers using Rich."""

import html
import re
from datetime import datetime

from rich.console import Console
from rich.table import Table
from rich.panel import Panel
from rich.text import Text

console = Console()


def strip_html(text: str) -> str:
    """Strip HTML tags and decode entities to plain text."""
    text = re.sub(r"<br\s*/?>", "\n", text, flags=re.IGNORECASE)
    text = re.sub(r"<p[^>]*>", "\n", text, flags=re.IGNORECASE)
    text = re.sub(r"</p>", "", text, flags=re.IGNORECASE)
    text = re.sub(r"<[^>]+>", "", text)
    text = html.unescape(text)
    # Collapse excessive blank lines
    text = re.sub(r"\n{3,}", "\n\n", text)
    return text.strip()


def format_timestamp(unix_ts: int) -> str:
    """Format a unix timestamp to a human-readable string."""
    dt = datetime.fromtimestamp(unix_ts)
    now = datetime.now()
    if dt.date() == now.date():
        return dt.strftime("%H:%M")
    if dt.year == now.year:
        return dt.strftime("%b %d %H:%M")
    return dt.strftime("%Y-%m-%d %H:%M")


def format_size(size_bytes: int) -> str:
    """Format byte size to human-readable."""
    for unit in ("B", "KB", "MB", "GB"):
        if size_bytes < 1024:
            return f"{size_bytes:.0f}{unit}"
        size_bytes /= 1024
    return f"{size_bytes:.1f}TB"


SYSTEM_LABELS = {
    "0": "Inbox",
    "1": "Drafts",
    "2": "Sent",
    "3": "Starred",
    "4": "Archive",
    "5": "All Mail",
    "6": "Spam",
    "7": "Trash",
    "8": "Draft-Sent",
    "10": "Scheduled",
}


def print_message_list(messages, folder_name="Inbox"):
    """Print a table of messages."""
    table = Table(title=f"{folder_name} ({len(messages)} messages)", show_lines=False)
    table.add_column("#", style="dim", width=4, justify="right")
    table.add_column("", width=2)  # unread indicator
    table.add_column("From", style="cyan", max_width=30, no_wrap=True)
    table.add_column("Subject", max_width=50)
    table.add_column("Date", style="green", width=14, justify="right")
    table.add_column("Size", style="dim", width=6, justify="right")

    for i, msg in enumerate(messages):
        unread = "[bold yellow]*[/]" if msg.unread else " "
        sender = msg.sender.name or msg.sender.address
        subject = msg.subject or "(no subject)"
        style = "bold" if msg.unread else ""

        table.add_row(
            str(i),
            unread,
            sender,
            Text(subject, style=style, overflow="ellipsis"),
            format_timestamp(msg.time),
            format_size(msg.size),
        )

    console.print(table)


def print_message(message):
    """Print a single message in detail."""
    sender = f"{message.sender.name} <{message.sender.address}>" if message.sender.name else message.sender.address
    to_list = ", ".join(
        f"{r.name} <{r.address}>" if r.name else r.address
        for r in message.recipients
    )
    cc_list = ", ".join(
        f"{r.name} <{r.address}>" if r.name else r.address
        for r in message.cc
    ) if message.cc else None

    header_lines = [
        f"[bold]From:[/]    {sender}",
        f"[bold]To:[/]      {to_list}",
    ]
    if cc_list:
        header_lines.append(f"[bold]CC:[/]      {cc_list}")
    header_lines.append(f"[bold]Date:[/]    {format_timestamp(message.time)}")
    header_lines.append(f"[bold]Subject:[/] {message.subject}")

    if message.attachments:
        att_list = ", ".join(
            f"{a.name} ({format_size(a.size)})" for a in message.attachments
        )
        header_lines.append(f"[bold]Files:[/]   {att_list}")

    header_lines.append(f"[dim]ID: {message.id}[/]")

    console.print(Panel("\n".join(header_lines), title="Message", border_style="blue"))
    console.print()

    body = strip_html(message.body) if message.body else "(empty)"
    console.print(body)
    console.print()
