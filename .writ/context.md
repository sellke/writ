# Writ Project Context

> Last Updated: 2026-09-04T13:08:00Z

## Product Mission

Writ is the thin, portable methodology layer on top of capable AI harnesses. It owns the durable contracts — specs, drift logs, decisions, knowledge, phase state — in plain markdown on git, and delegates mechanics (context management, subagents, browsing, retrieval) to the platform underneath. As harnesses absorb mechanics natively, Writ sheds them and concentrates on what compounds: the negotiated contract layer no harness provides.

## Active Spec

- **Spec:** none active
- **Status:** `2026-09-03-model-delegation` (Complete 2026-09-03, 33/33 tasks, 25/25 AC) and `2026-08-14-script-backed-quality-gates` (Complete) were archived by `/status --archive` on 2026-09-04 — moves are staged, not yet committed.
- **Story:** —
- **Progress:** —

Last landed: ADR-024 model delegation end to end (anchor/floor tiers, origin, ceiling,
escalate-once at `/create-spec` Step 2.6a and `/implement-story` Gate 0, `entry_level` on all
31 commands), then two follow-ups outside any spec: `ac-trace.py` now catches the
`RuntimeError` Python < 3.13 raises on a symlink loop (`ebbf064`), and the repo declares its
Python floor — `pyproject.toml` `requires-python >= 3.9`, `uv run pytest` as the one-command
runner, `.writ/config.md` pinning `Version File: VERSION` and `Test Runner` (`ec9db00`).
Branch `design/delegation-and-improvement-loop` is 12 commits ahead of `main`, unmerged.
Open thread for the next spec: ADR-025 Story 1 makes `escalated`/`degraded` live via
`signal.py append` — it must keep the `escalated(` tuple as `detail` or update the six
`eval.sh --check=model-escalation` pins in the same change.

## Artifact Map

- **Product:** roadmap.md, mission.md, mission-lite.md, decisions.md present
- **Active spec:** none — 62 archived under .writ/specs/archive/ (LEDGER.md current)
- **Knowledge:** .writ/knowledge/ (21 entries)
- **Docs:** .writ/docs/ (23 files)
- **Config:** .writ/config.md present (Default Branch main · Test Runner `uv run pytest` · Version File VERSION)
- **Integrity:** ✅ all required present

## Recent Drift

From the archived `2026-09-03-model-delegation` drift log:

- [DEV-014] Step 2.6a passes `--repo <spec folder>` to `ac-trace.py check` — a repo-wide scan misattributes other specs' dangling references at authoring time — Small
- [DEV-015] `test_governor_enforcement.py` `KNOWN_OVER_BUDGET` re-pinned in-story with dated disclosure — Small
- [DEV-009] Entry notice's positive path is not observable on Cursor today — every listed slug self-assesses ≥ `high` — Medium ⚠️ (for the ADR-025 ledger)

## Open Issues

5 files under `.writ/issues/` — 4 older than 7 days with no `spec_ref` (see `/status` Needs Triage); newest: `2026-09-03-test-integrity-authenticity-flags-every-bash-test.md` (1 day).

## Verification State

2026-09-04, after `ec9db00`:

- `uv run pytest` — 799 passed, 1 skipped (default interpreter 3.13); `uv run --python 3.9 pytest` — 799 passed, 1 skipped (the floor). Also green on 3.10, 3.11, 3.14.
- `scripts/tests/test_*.sh` — 10/10 OK
- `bash scripts/eval.sh` — Findings: 0, Run errors: 0 (`pyproject.toml`/`uv.lock` declared OUT_OF_SCOPE in `eval-leanness.py`)
- `python3 scripts/quality-config-audit.py check --project .` — pass, 0 findings (no `.writ/quality-baseline.md`; nothing to baseline)
