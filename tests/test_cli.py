"""Tests for CLI helpers and constants."""

from protonmail_cli.cli import FOLDER_ALIASES


class TestFolderAliases:
    def test_inbox(self):
        assert FOLDER_ALIASES["inbox"] == "0"

    def test_sent(self):
        assert FOLDER_ALIASES["sent"] == "2"

    def test_drafts(self):
        assert FOLDER_ALIASES["drafts"] == "1"

    def test_spam(self):
        assert FOLDER_ALIASES["spam"] == "6"

    def test_trash(self):
        assert FOLDER_ALIASES["trash"] == "7"

    def test_all_aliases_present(self):
        expected = {
            "inbox",
            "drafts",
            "sent",
            "starred",
            "archive",
            "all",
            "spam",
            "trash",
        }
        assert set(FOLDER_ALIASES.keys()) == expected
