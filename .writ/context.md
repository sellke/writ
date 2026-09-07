# Writ Project Context

> Last Updated: 2026-09-07T19:40:00Z

## Product Mission

Writ is the thin, portable methodology layer on top of capable AI harnesses. It owns the durable contracts — specs, drift logs, decisions, knowledge, phase state — in plain markdown on git, and delegates mechanics (context management, subagents, browsing, retrieval) to the platform underneath. As harnesses absorb mechanics natively, Writ sheds them and concentrates on what compounds: the negotiated contract layer no harness provides.

## Active Spec

- **Spec:** `2026-09-05-phase11-repair-and-baseline` — Phase 11 Stage 1 of the contract-and-verifier-layer Goal Card (`.writ/issues/goals/2026-09-05-writ-contract-and-verifier-layer.md`)
- **Status:** Complete — Stories 1–5 Completed ✅ (Story 5 on 2026-09-07, commit `cf84742`, SHA record `9840386`)
- **Story:** 5 of 5 — Baseline Capture and Gate (Completed ✅)
- **Progress:** 35/35 tasks complete (100%)

The Fable 5.1 pipeline baseline is committed at `.writ/eval/baselines/2026-09-06-claude-fable-5-1.json`: eight runs (four yuss stories × 2), every exit criteria met, driver cost $187.60 over 5.5 h. `validate` exit 0; `eval.sh` Findings 0; `compare <file> <file>` all-zero deltas. Stage 2 (the next Goal Card stage) gets its own spec. Not started.

`/implement-spec` checker verdict: `implement-spec.c1` met, `c2` met, `c3` unmet only because the checker requires `typecheck == "pass"` and this stack has no typechecker — filed as `.writ/issues/improvements/2026-09-07-exit-criteria-c3-rejects-stacks-without-a-typechecker.md`.

## Artifact Map

- **Product:** roadmap.md, mission.md, mission-lite.md, decisions.md, `2026-09-05-goldilocks-assessment.md` present
- **Research:** `2026-09-05-goldilocks-harness-research.md` present
- **Active spec:** `.writ/specs/2026-09-05-phase11-repair-and-baseline/` (spec, spec-lite, technical-spec, 5 stories, drift-log) — Complete, eligible for `/status --archive`; 62 archived under .writ/specs/archive/ (LEDGER.md current)
- **Baselines:** `.writ/eval/baselines/2026-09-06-claude-fable-5-1.json` (committed)
- **Knowledge:** .writ/knowledge/ (21 entries)
- **Docs:** .writ/docs/ (23 files)
- **Config:** .writ/config.md present (Default Branch main · Test Runner `uv run pytest` · Version File VERSION)
- **Integrity:** ✅ all required present

## Recent Drift

From `2026-09-05-phase11-repair-and-baseline/drift-log.md`:

- [DEV-028] Driver is not a model vendor — no Writ-resident API key; `ingest` path for Grok/local/Cursor — Medium
- [DEV-027] Leak walk also rejects embedded newlines, shared with `scrub()` — Small
- [DEV-026] `validate` checks `len(selection) == 4` (list), not `selection.stories` — Small

## Open Issues

7 files under `.writ/issues/` — 3 untriaged: `2026-08-11-restore-path-recording-for-destructive-commands.md` (27 days), `2026-09-03-test-integrity-authenticity-flags-every-bash-test.md`, `2026-09-07-exit-criteria-c3-rejects-stacks-without-a-typechecker.md` (new).

## Verification State

2026-09-07, spec closeout:

- `uv run --python 3.9 pytest` — 1017 passed, 1 skipped
- `for t in scripts/tests/test_*.sh` — all green
- `bash scripts/eval.sh` — Findings: 0 (report `.writ/state/eval-20260907-193029.md`), with the committed baseline present
- Typecheck: skipped, no typechecker configured (ad-hoc mypy: 105 pre-existing errors, not a gate)
- Story 2's real-key `measure-invocation.py --tokenizer anthropic` run remains pending a maintainer
- Baseline cost note: the task 5.6 formula ($52.54) understates the driver's `cost_usd` ($187.60) 3.6×; `cost_usd` is the price of record
