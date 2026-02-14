"""Session and configuration management for protonmail-cli."""

import os
from pathlib import Path

CONFIG_DIR = Path(os.environ.get("PMAIL_CONFIG_DIR", Path.home() / ".config" / "pmail"))
SESSION_FILE = CONFIG_DIR / "session.pickle"


def ensure_config_dir():
    CONFIG_DIR.mkdir(parents=True, exist_ok=True)


def get_client():
    """Return an authenticated ProtonMail client, loading saved session."""
    from protonmail import ProtonMail

    if not SESSION_FILE.exists():
        raise SystemExit(
            "Not logged in. Run: pmail login"
        )

    proton = ProtonMail(logging_level=4)  # ERROR only
    proton.load_session(str(SESSION_FILE), auto_save=True)
    return proton
