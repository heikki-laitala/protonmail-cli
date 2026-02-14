#!/usr/bin/env bash
# Convenience wrapper — runs pmail from the venv
exec "$(dirname "$0")/.venv/bin/pmail" "$@"
