# Writ Project Context

> Last Updated: 2026-09-07T13:42:51Z

## Product Mission

Writ is the thin, portable methodology layer on top of capable AI harnesses. It owns the durable contracts — specs, drift logs, decisions, knowledge, phase state — in plain markdown on git, and delegates mechanics (context management, subagents, browsing, retrieval) to the platform underneath. As harnesses absorb mechanics natively, Writ sheds them and concentrates on what compounds: the negotiated contract layer no harness provides.

## Active Spec

- **Spec:** `2026-09-05-phase11-repair-and-baseline` — Phase 11 Stage 1 of the contract-and-verifier-layer Goal Card (`.writ/issues/goals/2026-09-05-writ-contract-and-verifier-layer.md`)
- **Status:** In Progress — Stories 1–4 Complete (2026-09-06); Story 5 In Progress. (`spec.md` header still reads `Not Started`; story-5 task checkboxes are unchecked while README reports 4/7 — run `/verify-spec`.)
- **Story:** 5 of 5 — Baseline Capture and Gate (In Progress; tasks 5.1–5.4 landed per README, 5.5 live capture next)
- **Progress:** 32/35 tasks complete (91%)

Last landed: Story 4 `eefffa1` (replay runner), SHA record `d2f92de`. Story 5 code for `validate` / `compare` / `check_pipeline_baseline` plus tests is in the working tree, uncommitted (11 modified, 1 untracked). DEV-028 removed the `ANTHROPIC_API_KEY` requirement: the `claude` CLI on `PATH` (`~/.local/bin/claude`) authenticates the headless driver. Next: task 5.5 — `python3 scripts/pipeline-baseline.py run --model claude-fable-5-1 --runs 2` outside the sandbox. Batch state: `.writ/state/execution-20260906T124537Z.json` (4 complete, 1 in progress).

## Artifact Map

- **Product:** roadmap.md, mission.md, mission-lite.md, decisions.md present; `2026-09-05-goldilocks-assessment.md` present
- **Research:** `2026-09-05-goldilocks-harness-research.md` present
- **Active spec:** `.writ/specs/2026-09-05-phase11-repair-and-baseline/` (spec, spec-lite, technical-spec, 5 stories, drift-log) — 62 archived under .writ/specs/archive/ (LEDGER.md current)
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

6 files under `.writ/issues/` — 2 untriaged and older than 7 days (`2026-08-11-restore-path-recording-for-destructive-commands.md`, `2026-09-03-test-integrity-authenticity-flags-every-bash-test.md`).

## Verification State

2026-09-06, Story 5 mid-pipeline (resume):

- Story 4 closeout: `eefffa1` / SHA record `d2f92de`; 119 pytest; eval.sh Findings 0 (before Story 5 registered the check)
- Story 5 Gates 0–3: ARCH_CHECK CAUTION → coding 5.1–5.4 → REVIEW PASS (Small drift DEV-026/027, Medium DEV-028)
- `uv run --python 3.9 pytest scripts/tests/test_pipeline_baseline.py scripts/tests/test_pipeline_baseline_run.py` — 146 passed
- `bash scripts/tests/test_eval_pipeline_baseline.sh` — 5 assertions passed
- Committed skeleton fails `validate` (`runs_per_story` null) until eight live records exist
- Quality config: pass, 0 findings (no `.writ/quality-baseline.md`)
