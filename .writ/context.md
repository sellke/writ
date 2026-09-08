# Writ Project Context

> Last Updated: 2026-09-08T15:50:00Z

## Product Mission

Writ is the thin, portable methodology layer on top of capable AI harnesses. It owns the durable contracts — specs, drift logs, decisions, knowledge, phase state — in plain markdown on git, and delegates mechanics (context management, subagents, browsing, retrieval) to the platform underneath. As harnesses absorb mechanics natively, Writ sheds them and concentrates on what compounds: the negotiated contract layer no harness provides.

## Active Spec

- **Spec:** `2026-09-07-phase11-stage2-prune-the-base` — Phase 11 Stage 2a (Goal Card `.writ/issues/goals/2026-09-05-writ-contract-and-verifier-layer.md`)
- **Status:** Complete — Stories 1–5 Completed ✅ (Story 5 on 2026-09-08, commit `deed2a1`, SHA record `212026d`)
- **Story:** 5 of 5 — Baseline Re-run and Keep-or-Revert (decision: KEEP)
- **Progress:** 33/33 tasks complete (100%)

The shared base is 9,704 bytes (from 28,157), 187 ledger rows, cap blocking. The Stage 2a re-run (`.writ/eval/baselines/2026-09-07-claude-fable-5-1.json`) met exit criteria 8/8 against Stage 1's 8/8; driver cost −4.7%, cache-creation tokens −36%. Next Goal Card work: Stage 2b (mechanize Gates 0, 0.5, 1, 2.5, 3, 5; flip `verdict-provenance` to blocking), not yet specced.

`/implement-spec` checker: c1 met, c2 met, c3 unmet only on the typecheck literal (no typechecker in this stack; issue `2026-09-07-exit-criteria-c3-rejects-stacks-without-a-typechecker.md`).

## Artifact Map

- **Product:** roadmap.md, mission.md, mission-lite.md, decisions.md, `2026-09-05-goldilocks-assessment.md` present
- **Research:** `2026-09-05-goldilocks-harness-research.md` present
- **Specs:** `2026-09-07-phase11-stage2-prune-the-base` Complete · `2026-09-05-phase11-repair-and-baseline` Complete — both eligible for `/status --archive`; 62 archived
- **Baselines:** `2026-09-06-claude-fable-5-1.json` (Stage 1) · `2026-09-07-claude-fable-5-1.json` (Stage 2a), both committed
- **Decision records:** ADR-026 constraint-test pruning · `pruned-instructions-ledger.md` (187 rows, `<!-- cap: blocking -->`)
- **Knowledge:** .writ/knowledge/ (21 entries)
- **Docs:** .writ/docs/ (25 files)
- **Config:** .writ/config.md present (Default Branch main · Test Runner `uv run pytest` · Version File VERSION)
- **Integrity:** ✅ all required present

## Recent Drift

From `2026-09-07-phase11-stage2-prune-the-base/drift-log.md`:

- [DEV-011] `cursor/writ.mdc` re-synced whole (20,885 → 4,600) as Cursor's alwaysApply rule — Medium
- [DEV-009] AC-3.4 `grep -c` proxy cannot return 1 for cursor.md (pre-existing verification record) — Medium
- [DEV-006] `check_recommendation_semantics` literals retargeted to the new doc — Medium

## Open Issues

7 files under `.writ/issues/` — 3 untriaged (`2026-08-11-restore-path-recording…`, `2026-09-03-test-integrity-authenticity…`, `2026-09-07-exit-criteria-c3-rejects-stacks-without-a-typechecker.md`).

## Verification State

2026-09-08, spec closeout (`212026d`):

- `uv run --python 3.9 pytest -q` — 1075 passed, 1 skipped
- `scripts/tests/test_*.sh` — 14/14 green
- `bash scripts/eval.sh` — Findings 0, Run errors 0
- `prune-ledger.py check --cap-blocking` — exit 0, `base: 9704 bytes (cap 10000), ledger: 187 rows, re-added: 0`
- `verdict-provenance.py check` — exit 0, note `prose_only_count: 8 (cap 2)`
- `pipeline-baseline.py compare` Stage 1 vs 2a — exit criteria 2/2 × 4
- Typecheck: skipped, none configured
- Host side effect from replays: Homebrew Postgres 17 running with `writ_story{2,3,4}_test` databases
