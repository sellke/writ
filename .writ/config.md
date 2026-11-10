# Writ Project Config

> Last Updated: 2026-11-09

## Conventions

- **Default Branch:** main
- **Test Runner:** `python3 scripts/check.py`, then `uv run --isolated --python 3.9 --with pytest pytest`, then `for t in scripts/tests/test_*.sh; do bash "$t"; done`
- **Version File:** VERSION
- **Judgment Provider:** vercel-gateway

## Paths

- **Changelog:** CHANGELOG.md
- **Writ Specs:** .writ/specs/
- **Writ Issues:** .writ/issues/
