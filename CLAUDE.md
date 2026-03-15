# protonmail-cli — Agent Instructions

CLI for reading and sending Proton Mail emails, built on [protonmail-api-client](https://github.com/opulentfox-29/protonmail-api-client). Uses Click for commands and Rich for terminal output.

## Build & Run

```bash
uv sync --group dev  # Install dependencies (including dev tools)
uv run pmail --help  # Run CLI
./pmail.sh --help    # Wrapper script (calls uv run)
```

Validation before commit:

```bash
uv run ruff check . && uv run ruff format --check . && uv run pytest tests/ -v
```

## Project Structure

| Path | Purpose |
| ---- | ------- |
| `src/protonmail_cli/cli.py` | Click command definitions (all user-facing commands) |
| `src/protonmail_cli/config.py` | Session/config management, ProtonMail client factory |
| `src/protonmail_cli/formatting.py` | Rich-based output formatting, HTML stripping |
| `skills/protonmail.md` | Agent skill file for AI assistants |
| `pmail.sh` | Convenience wrapper for `uv run pmail` |
| `pyproject.toml` | Project metadata, dependencies, entry point |

## Conventions

- **Python 3.9+**, managed with uv
- **CLI framework**: Click with `@click.group()` / `@click.command()`
- **Output**: Rich console, tables, and panels — no bare `print()`
- **Config**: `~/.config/pmail/` (overridable via `PMAIL_CONFIG_DIR` env var)
- **Session**: Pickle-based, auto-refreshing. Login only needed once.
- **Git**: Conventional commits (`feat:`, `fix:`, `chore:`, `docs:`). No Co-Authored-By trailer. No "Generated with Claude Code" footer in PR descriptions.

## Engineering Principles

### KISS

Prefer straightforward control flow. Keep error paths obvious and localized.

### YAGNI

Do not add interfaces, config keys, or abstractions without a concrete caller. No speculative features.

### DRY (Rule of Three)

Duplicate small local logic when it preserves clarity. Extract shared helpers only after three repeated, stable patterns.

### Secure by Default

Never log secrets or tokens. Validate at system boundaries. Keep network/filesystem/shell scope narrow.

## Key Constraint

Message indices (used by `read`, `reply`, `forward`, `delete`, `archive`, etc.) resolve against the **inbox only**. Indices from non-inbox listings (`sent`, `spam`, etc.) will operate on the wrong message.

## Anti-Patterns (Do Not)

- Do not modify unrelated code "while here".
- Do not add dependencies without justification.
- Do not commit session files or credentials.
- Do not add speculative abstractions or features beyond what is requested.
