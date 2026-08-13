# Writ Context

> Last Updated: 2026-08-13T03:04:05+00:00

## Product Mission

Writ is the thin, portable methodology layer on top of capable AI harnesses. It owns the durable contracts — specs, drift logs, decisions, knowledge, phase state — in plain markdown on git, and delegates mechanics (context management, subagents, browsing, retrieval) to the platform underneath. As harnesses absorb mechanics natively, Writ sheds them and concentrates on what compounds: the negotiated contract layer no harness provides.

## Active Spec

- **Spec:** `2026-08-12-recalibrate-implement-loop` — Recalibrate the implement-spec / implement-story Loop
- **Status:** All 3 stories complete; not yet archived
- **Story:** 3 of 3 — Sub-Agent Worktree Integration (Completed ✅)
- **Progress:** 3/3 stories complete (100%)

## Artifact Map

| Artifact | Path | Present |
|---|---|---|
| Product mission | `.writ/product/mission.md` | yes |
| Roadmap | `.writ/product/roadmap.md` | yes |
| Active spec | `.writ/specs/2026-08-12-recalibrate-implement-loop/` | yes — spec.md, spec-lite.md, sub-specs/, user-stories/ |
| Knowledge ledger | `.writ/knowledge/` | yes (26 entries) |
| Decision records | `.writ/decision-records/` | yes |
| Docs | `.writ/docs/` | yes (21 files) |
| Issues | `.writ/issues/` | yes |

**Integrity:** ✅ all required present. Optional artifacts absent are reported, not fatal.

## Recent Drift

No `drift-log.md` for `2026-08-12-recalibrate-implement-loop` — all drift was inline, documentation-level corrections recorded in each story's What Was Built rather than a standalone log:

- **Story 1** — an unrelated transcription slip ("Gate 0/1/3/4/5" → corrected to "Gate 0/1/3/4/4.5") caught and fixed during Story 2's review pass.
- **Story 2** — first-draft blockquote wording matched `technical-spec.md`'s illustrative insertion text verbatim, but that draft omitted the "this note owns *when*...; the skill owns *how*" ownership-split clause the story's own acceptance criterion requires exactly; resolved in favor of the acceptance criterion over the technical-spec draft, re-reviewed clean.
- **Story 3** — none; the phrasing-convention gap found in Story 2 was already fixed before Story 3's blockquote was authored, so it matched on first review.

## Open Issues

4 files under `.writ/issues/` — unchanged this run; not investigated as part of this spec's scope.

## Release

v0.30.3 tagged 2026-08-12. `2026-08-12-recalibrate-implement-loop` is implemented and verified (`bash scripts/lint-skill.sh` clean on both new skills, full `bash scripts/eval.sh` suite green — Findings 0, Run errors 0) but not yet shipped/released — next steps are optional `/verify-spec`, then `/ship`.
