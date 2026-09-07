# Writ Project Context

> Last Updated: 2026-09-06T22:52:00Z

## Product Mission

Writ is the thin, portable methodology layer on top of capable AI harnesses. It owns the durable contracts — specs, drift logs, decisions, knowledge, phase state — in plain markdown on git, and delegates mechanics (context management, subagents, browsing, retrieval) to the platform underneath. As harnesses absorb mechanics natively, Writ sheds them and concentrates on what compounds: the negotiated contract layer no harness provides.

## Active Spec

- **Spec:** `2026-09-05-phase11-repair-and-baseline` — Phase 11 Stage 1 of the contract-and-verifier-layer Goal Card (`.writ/issues/goals/2026-09-05-writ-contract-and-verifier-layer.md`)
- **Status:** In Progress — Stories 1–4 Completed ✅ (2026-09-06); Story 5 Not Started
- **Story:** 5 of 5 — Baseline Capture and Gate (Not Started)
- **Progress:** 28/35 tasks complete (80%)

Last landed (2026-09-06): Story 4 — `pipeline-baseline.py run`/`ingest` (isolated checkout at `parent_sha`, current-Writ overlay, headless `/implement-story`, scrubbed `RUN_KEYS` record). Task 4.2 live smoke run deferred (no `ANTHROPIC_API_KEY`). Story 2 real-key run still pending. Next: Story 5 (`validate`/`compare`/`check_pipeline_baseline` + eight Fable 5.1 runs). Prerequisites still missing for Story 5 live capture: `ANTHROPIC_API_KEY`. `claude` 2.1.260 and `pnpm` are on PATH; `~/Projects/yuss` exists (read-only). Spec-close item: `eval.sh` leanness WARNINGs — `scripts` lines/chars grew past the justified ceiling.

## Artifact Map

- **Product:** roadmap.md, mission.md, mission-lite.md, decisions.md present; `2026-09-05-goldilocks-assessment.md` (analysis + plan) untracked
- **Research:** `2026-09-05-goldilocks-harness-research.md` untracked
- **Active spec:** `.writ/specs/2026-09-05-phase11-repair-and-baseline/` (spec, spec-lite, technical-spec, 5 stories, drift-log) — 62 archived under .writ/specs/archive/ (LEDGER.md current)
- **Knowledge:** .writ/knowledge/ (21 entries; 10 lessons reconstructed 2026-09-06)
- **Docs:** .writ/docs/ (23 files)
- **Config:** .writ/config.md present (Default Branch main · Test Runner `uv run pytest` · Version File VERSION)
- **Integrity:** ✅ all required present

## Recent Drift

From `2026-09-05-phase11-repair-and-baseline/drift-log.md` (Stories 1–4):

- [DEV-018] Inputs staged from the parent commit, never yuss HEAD; `assert_answer_scrubbed` aborts with `answer_leak` — Medium ⚠️
- [DEV-019] Permission mode is bypass, not `acceptEdits`; compensating controls recorded — Medium ⚠️ (user-approved)
- [DEV-021] Current-repo Writ overlaid via `install.sh`; `writ{…}` replaces `writ_scripts` — Medium ⚠️ (user-approved)
- [DEV-008] technical-spec §2 names superseded by story-3 AC-3.1; `SCHEMA_KEYS`/`SELECTION_KEYS`/`REASONS`/`RUN_KEYS` are the contract — Medium ⚠️
- [DEV-020/022–025] completion predicates, suite/original tests, Popen/killpg, gate source, smoke run deferred

## Open Issues

6 files under `.writ/issues/` — Goal Card `2026-09-05-writ-contract-and-verifier-layer.md` promoted (spec_ref set, Stage 1); `2026-09-03-test-integrity-authenticity-flags-every-bash-test.md` confirmed again (`test_imports_no_source` fires on every test in this repo — checker false-positive class); 4 older issues without `spec_ref`.

## Verification State

2026-09-06, Story 4 closeout (resume):

- `uv run --python 3.9 pytest scripts/tests/test_pipeline_baseline_run.py scripts/tests/test_pipeline_baseline.py` — 119 passed (74 run/ingest + 45 select)
- `ANTHROPIC_API_KEY` unset in this environment — Story 4 smoke run and Story 5 eight-run capture cannot start
- `claude` 2.1.260 and `pnpm` on PATH; `~/Projects/yuss` present
