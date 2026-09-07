# Writ Project Context

> Last Updated: 2026-09-07T22:35:00Z

## Product Mission

Writ is the thin, portable methodology layer on top of capable AI harnesses. It owns the durable contracts — specs, drift logs, decisions, knowledge, phase state — in plain markdown on git, and delegates mechanics (context management, subagents, browsing, retrieval) to the platform underneath. As harnesses absorb mechanics natively, Writ sheds them and concentrates on what compounds: the negotiated contract layer no harness provides.

## Active Spec

- **Spec:** `2026-09-07-phase11-stage2-prune-the-base` — Phase 11 Stage 2a (Goal Card `.writ/issues/goals/2026-09-05-writ-contract-and-verifier-layer.md`, Stage 2 first of two specs)
- **Status:** In Progress — Stories 1–4 Completed ✅ (2026-09-07); Story 5 In Progress
- **Story:** 5 of 5 — Baseline Re-run and Keep-or-Revert (task 5.2: eight Fable 5.1 runs in flight since 22:28 UTC, detached under nohup)
- **Progress:** 27/33 tasks complete (82%)

Base is 9,704 bytes (from 28,157), 187 ledger rows, cap blocking. Story commits: 1 `6fa3540`, 4 `e6be367`, 2 `e1a60ab`, 3 `2fc26f9`; batch-1 merge `272da3d`. Re-run file `.writ/eval/baselines/2026-09-07-claude-fable-5-1.json` (selection/criteria identical to Stage 1). Keep if `compare` shows exit criteria 2/2 on all four rows; else retry the failed pair once, then `/revert` Stories 2–3. State: `.writ/state/execution-20260907T211644Z.json`.

## Artifact Map

- **Product:** roadmap.md, mission.md, mission-lite.md, decisions.md, `2026-09-05-goldilocks-assessment.md` present
- **Research:** `2026-09-05-goldilocks-harness-research.md` present
- **Active spec:** `.writ/specs/2026-09-07-phase11-stage2-prune-the-base/` (spec, spec-lite, technical-spec, 5 stories, drift-log DEV-001..011, DEV-101..102) — previous spec `2026-09-05-phase11-repair-and-baseline` Complete, eligible for archive; 62 archived under .writ/specs/archive/
- **Baselines:** `2026-09-06-claude-fable-5-1.json` (Stage 1, committed) · `2026-09-07-claude-fable-5-1.json` (Stage 2 re-run, filling)
- **Decision records:** ADR-026 constraint-test pruning · `pruned-instructions-ledger.md` (187 rows, `<!-- cap: blocking -->`)
- **Knowledge:** .writ/knowledge/ (21 entries)
- **Docs:** .writ/docs/ (25 files; +startup-update-awareness, +recommendation-semantics; model-tiers and skills now source of truth)
- **Config:** .writ/config.md present (Default Branch main · Test Runner `uv run pytest` · Version File VERSION)
- **Integrity:** ✅ all required present

## Recent Drift

From `2026-09-07-phase11-stage2-prune-the-base/drift-log.md`:

- [DEV-011] `cursor/writ.mdc` re-synced whole (20,885 → 4,600) as Cursor's alwaysApply rule — Medium
- [DEV-009] AC-3.4 `grep -c` proxy cannot return 1 for cursor.md (pre-existing verification record) — Medium
- [DEV-006] `check_recommendation_semantics` literals retargeted to the new doc, 3 rule pins stay on the base — Medium

## Open Issues

7 files under `.writ/issues/` — 3 untriaged (`2026-08-11-restore-path-recording…`, `2026-09-03-test-integrity-authenticity…`, `2026-09-07-exit-criteria-c3-rejects-stacks-without-a-typechecker.md`).

## Verification State

2026-09-07, after Story 3 (`e5792ce`):

- `uv run --python 3.9 pytest -q` — 1075 passed, 1 skipped
- `scripts/tests/test_*.sh` — 14/14 green
- `bash scripts/eval.sh` — Findings 0, Run errors 0 (54 checks incl. new `pruned-base`, `verdict-provenance`)
- `prune-ledger.py check --cap-blocking` — exit 0, `base: 9704 bytes (cap 10000), ledger: 187 rows, removed: 187, re-added: 0`
- `verdict-provenance.py check` — exit 0, note `prose_only_count: 8 (cap 2)` (mechanization spec flips to blocking)
- Story 5 re-run: in flight
