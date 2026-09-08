# Writ Project Context

> Last Updated: 2026-09-08T22:35:00Z

## Product Mission

Writ is the thin, portable methodology layer on top of capable AI harnesses. It owns the durable contracts — specs, drift logs, decisions, knowledge, phase state — in plain markdown on git, and delegates mechanics (context management, subagents, browsing, retrieval) to the platform underneath. As harnesses absorb mechanics natively, Writ sheds them and concentrates on what compounds: the negotiated contract layer no harness provides.

## Active Spec

- **Spec:** `2026-09-08-phase11-stage2b-mechanize-the-gates` — Phase 11 Stage 2b (Goal Card `.writ/issues/goals/2026-09-05-writ-contract-and-verifier-layer.md`)
- **Status:** In Progress — Stories 1–5 Completed ✅ (spec header sync waits on implement-spec checker)
- **Story:** 5 of 5 — Gate 3.5 format + flip + watch (Completed ✅)
- **Progress:** 32/32 tasks complete (100%)

Frontmatter is 8 script / 2 prose-only (`gate1_coding`, `gate4_5_visual`). `--prose-only-blocking` is on. Replay totals: 54 agree / 42 note / 48 unverifiable. No keep-or-revert. No `/revert`.

## Artifact Map

- **Product:** roadmap.md, mission.md, mission-lite.md, decisions.md, `2026-09-05-goldilocks-assessment.md` present
- **Active spec:** .writ/specs/2026-09-08-phase11-stage2b-mechanize-the-gates/ — spec.md + spec-lite.md, user-stories/, sub-specs/
- **Knowledge:** .writ/knowledge/ (21 entries)
- **Docs:** .writ/docs/ (25 files)
- **Integrity:** ✅ all required present

## Recent Drift

From `2026-09-08-phase11-stage2b-mechanize-the-gates/drift-log.md`:

- [DEV-001] Parallel batch landed shared files in one checkout — Medium

## Open Issues

7 files under `.writ/issues/` — 1 goal, 5 improvements (including `2026-09-07-exit-criteria-c3-rejects-stacks-without-a-typechecker.md`), 1 feature.

## Verification State

2026-09-08, Story 5 closeout:

- `uv run --python 3.9 pytest -q` — 1146 passed, 1 skipped
- `python3 scripts/verdict-provenance.py check --command commands/implement-story.md --prose-only-blocking` — exit 0, `prose_only_count: 2 (cap 2)`
- `bash scripts/eval.sh` — Findings 0, Run errors 0
- Typecheck: skipped, none configured
- `test-integrity` coverage: unverifiable (`no_coverage_report`)
