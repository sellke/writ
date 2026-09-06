# Writ Project Context

> Last Updated: 2026-09-06T13:30:00Z

## Product Mission

Writ is the thin, portable methodology layer on top of capable AI harnesses. It owns the durable contracts — specs, drift logs, decisions, knowledge, phase state — in plain markdown on git, and delegates mechanics (context management, subagents, browsing, retrieval) to the platform underneath. As harnesses absorb mechanics natively, Writ sheds them and concentrates on what compounds: the negotiated contract layer no harness provides.

## Active Spec

- **Spec:** `2026-09-05-phase11-repair-and-baseline` — Phase 11 Stage 1 of the contract-and-verifier-layer Goal Card (`.writ/issues/goals/2026-09-05-writ-contract-and-verifier-layer.md`)
- **Status:** In Progress — Stories 1–3 Completed ✅ (2026-09-06); Stories 4–5 Not Started
- **Story:** next is Story 4 (replay runner — isolated checkout at `parent_sha`, headless `/implement-story`, metrics per run; reads `selection[]` from the committed baseline), then Story 5 (eight Fable 5.1 runs + `check_pipeline_baseline`)
- **Progress:** 3/5 stories · 21/35 tasks · 15/25 AC

Last landed (2026-09-06): Story 2 `0286fab` — `measure-invocation.py` counts with Anthropic `count_tokens` (`--tokenizer auto|anthropic|estimate`, hash-only cache, per-item degradation, 401 fatal); no-key output byte-identical except `token_note`; **real-key run not yet performed** (no key in the implementing environment — task 2.6 partial). Story 3 `92eb2b2` — `pipeline-baseline.py select` and the committed baseline skeleton `.writ/eval/baselines/2026-09-06-claude-fable-5-1.json` (yuss `7c2d043`; picks `api_route 79d79ae`, `ui 8d97930`, `data_model c9350fc`, `refactor 12eea11`) under the **user-approved `--live-test-scope file` widening** — the spec's strict rule fills only 2 of 4 classes on the real archive. `~/Projects/yuss` now exists (read-only). Prerequisites still missing for Stories 4–5: `ANTHROPIC_API_KEY`; Claude Code CLI headless invocation (Story 4 task 4.2 smoke run decides `run` vs `ingest` fallback). Spec-close item: `eval.sh` leanness WARNINGs — `scripts` lines/chars grew past the justified ceiling (Stories 2–3, ~+1,900 lines); record the increment in `.writ/leanness-baseline.json` with justification at spec close.

## Artifact Map

- **Product:** roadmap.md, mission.md, mission-lite.md, decisions.md present; `2026-09-05-goldilocks-assessment.md` (analysis + plan) untracked
- **Research:** `2026-09-05-goldilocks-harness-research.md` untracked
- **Active spec:** `.writ/specs/2026-09-05-phase11-repair-and-baseline/` (spec, spec-lite, technical-spec, 5 stories, drift-log) — 62 archived under .writ/specs/archive/ (LEDGER.md current)
- **Knowledge:** .writ/knowledge/ (21 entries; 10 lessons reconstructed 2026-09-06)
- **Docs:** .writ/docs/ (23 files)
- **Config:** .writ/config.md present (Default Branch main · Test Runner `uv run pytest` · Version File VERSION)
- **Integrity:** ✅ all required present

## Recent Drift

From `2026-09-05-phase11-repair-and-baseline/drift-log.md` (Stories 1–3):

- [DEV-001] `check_knowledge_integrity` also blocks on an empty `## TL;DR` — Medium ⚠️
- [DEV-008] technical-spec §2 baseline field/class/reason names superseded by story-3 AC-3.1; `SCHEMA_KEYS`/`SELECTION_KEYS`/`REASONS` in `pipeline-baseline.py` are the contract Stories 4–5 import — Medium ⚠️
- [DEV-005] Bare `*.md` tokens in `check_referenced_paths` resolve by basename anywhere in `git ls-files -co`; ~10 runtime-created names pass via the dogfooding workspace rather than an allowlist row — Small (follow-up candidate)
- [DEV-002/003/004/006/007, DEV-009–017] wording-level and flag-level deviations recorded; `spec-lite.md` amended
- Approved Scope Addition (Story 3): `--live-test-scope file` — per-test-file live-service rule; recorded in the story file and `criteria.live_test_scope`

## Open Issues

6 files under `.writ/issues/` — Goal Card `2026-09-05-writ-contract-and-verifier-layer.md` promoted (spec_ref set, Stage 1); `2026-09-03-test-integrity-authenticity-flags-every-bash-test.md` confirmed again this run (`test_imports_no_source` fires on every test in this repo — checker false-positive class); 4 older issues without `spec_ref`.

## Verification State

2026-09-06, Story 3 closing commit (`92eb2b2`):

- `bash scripts/eval.sh` — Findings: 0, Run errors: 0, 23/23 scenarios (leanness WARNINGs: `skills.chars`, `scripts.lines` 51576 vs 46748 ceiling, `scripts.chars` — spec-close justification pending)
- `uv run --python 3.9 pytest scripts/tests/` — 885 passed, 1 skipped (before Gate 4 additions); `test_measure_invocation.py` + `test_governor_enforcement.py` 135 passed (3.9, 3.13); `test_pipeline_baseline.py` 45 passed (3.9.6, 3.12.13; needs to run outside the sandbox — fixtures `git init`)
- `scripts/tests/test_*.sh` — all OK
- AC-2.2 — HEAD vs working copy JSON, no key: only `token_note` differs (629 lines); `~/Projects/yuss` porcelain empty, HEAD `7c2d043` after every `select` run
- Gate 4 mutation checks: Story 2 — original aggregate-rounding fixture could not distinguish per-text rounding; replaced. Story 3 — grep boundary, `--no-renames`, tie-break, chmod all caught.
- `scripts/story-context.py assemble` — returned 0 bytes for Story 1: generated `## Context for Agents` categories not recognized by the assembler (hint grammar and generator out of sync — Stage 2 data point)
