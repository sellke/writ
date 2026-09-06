# Writ Project Context

> Last Updated: 2026-09-06T13:30:00Z

## Product Mission

Writ is the thin, portable methodology layer on top of capable AI harnesses. It owns the durable contracts — specs, drift logs, decisions, knowledge, phase state — in plain markdown on git, and delegates mechanics (context management, subagents, browsing, retrieval) to the platform underneath. As harnesses absorb mechanics natively, Writ sheds them and concentrates on what compounds: the negotiated contract layer no harness provides.

## Active Spec

- **Spec:** `2026-09-05-phase11-repair-and-baseline` — Phase 11 Stage 1 of the contract-and-verifier-layer Goal Card (`.writ/issues/goals/2026-09-05-writ-contract-and-verifier-layer.md`)
- **Status:** In Progress — Story 1 Completed ✅ (2026-09-06); Stories 2–5 Not Started
- **Story:** next batch is Stories 2 (validated token measurement) and 3 (yuss.app story selection), parallel; then 4 (replay runner), then 5 (baseline capture + `check_pipeline_baseline`)
- **Progress:** 1/5 stories · 7/35 tasks · 5/25 AC

Last landed: Story 1 closed the 19 dead ends from `.writ/product/2026-09-05-goldilocks-assessment.md` §2.4 and added three blocking `eval.sh` checks (`referenced-paths`, `skill-manifest-parity`, `knowledge-integrity`; 47 → 50 checks), fixed the `phase-state.py knowledge_writeback` string-iteration bug that shredded ten knowledge lessons, and reconstructed all ten. `.writ/decision-log.md` created (one line per Stage 1 story). Prerequisites still missing for Stories 4–5: `ANTHROPIC_API_KEY`, `~/Projects/yuss` clone (Story 3 task 3.6 clones it).

## Artifact Map

- **Product:** roadmap.md, mission.md, mission-lite.md, decisions.md present; `2026-09-05-goldilocks-assessment.md` (analysis + plan) untracked
- **Research:** `2026-09-05-goldilocks-harness-research.md` untracked
- **Active spec:** `.writ/specs/2026-09-05-phase11-repair-and-baseline/` (spec, spec-lite, technical-spec, 5 stories, drift-log) — 62 archived under .writ/specs/archive/ (LEDGER.md current)
- **Knowledge:** .writ/knowledge/ (21 entries; 10 lessons reconstructed 2026-09-06)
- **Docs:** .writ/docs/ (23 files)
- **Config:** .writ/config.md present (Default Branch main · Test Runner `uv run pytest` · Version File VERSION)
- **Integrity:** ✅ all required present

## Recent Drift

From `2026-09-05-phase11-repair-and-baseline/drift-log.md` (Story 1, Gate 3):

- [DEV-001] `check_knowledge_integrity` also blocks on an empty `## TL;DR` — Medium ⚠️
- [DEV-005] Bare `*.md` tokens in `check_referenced_paths` resolve by basename anywhere in `git ls-files -co`; ~10 runtime-created names pass via the dogfooding workspace rather than an allowlist row — Small (follow-up candidate)
- [DEV-002/003/004/006/007] wording-level deviations recorded; `spec-lite.md` amended

## Open Issues

6 files under `.writ/issues/` — Goal Card `2026-09-05-writ-contract-and-verifier-layer.md` promoted (spec_ref set, Stage 1); `2026-09-03-test-integrity-authenticity-flags-every-bash-test.md` confirmed again this run (`test_imports_no_source` fires on every test in this repo — checker false-positive class); 4 older issues without `spec_ref`.

## Verification State

2026-09-06, Story 1 closing commit:

- `bash scripts/eval.sh` — Findings: 0, Run errors: 0, 50 checks (leanness WARNING `adapters.lines` 1724 vs 1709 ceiling, accepted in Story 1 What Was Built)
- `uv run pytest` — 809 passed, 1 skipped (3.13); `uv run --python 3.9 pytest scripts/tests/test_phase_state.py scripts/tests/test_governor_enforcement.py` — 78 passed (floor)
- `scripts/tests/test_*.sh` — 11/11 OK (new: `test_eval_dead_end_checks.sh`, 11 assertions)
- `scripts/story-context.py assemble` — returned 0 bytes for Story 1: generated `## Context for Agents` categories not recognized by the assembler (hint grammar and generator out of sync — Stage 2 data point)
