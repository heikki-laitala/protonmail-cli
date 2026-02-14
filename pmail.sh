#!/usr/bin/env bash
# Convenience wrapper — runs pmail via uv
exec uv run --project "$(dirname "$0")" pmail "$@"
