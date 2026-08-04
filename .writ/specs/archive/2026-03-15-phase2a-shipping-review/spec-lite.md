# Phase 2a: Shipping & Review — Spec Lite

> Source: spec.md
> Created: 2026-03-15
> Last Updated: 2026-03-15
> Purpose: Efficient AI context for implementation

## What We're Building

Four features (five capabilities) that close the gap between "pipeline green" and "code merged," plus retrospective analysis and failure-aware planning:

1. **`/ship`** — Unified shipping workflow: detect conventions → merge main → run tests → split commits intelligently → create PR with structured body, auto-labels, and draft/ready detection. PR agent behavior is folded in — one command owns the full "branch to merged" path. Non-interactive by default.

2. **`/review`** — Standalone pre-landing code review. Produces error & rescue maps (method → failure → rescue → test → user impact), shadow path traces (happy/nil/empty/upstream), interaction edge cases (double-click, navigate-away, stale state, back button), failure modes registry, and mandatory ASCII diagrams for non-trivial flows. Outputs judgment, not checklists.

3. **`/retro`** — Git-based retrospective with persistent JSON snapshots. Metrics: commits, LOC, test ratio, session detection, streaks. Writ integration: specs completed, drift incidents. Ship-of-the-week, trend comparison, tweetable summary. Auto-detects timezone and default branch.

4. **Error mapping in `/create-spec`** — Three required sections in technical sub-specs for features with user-facing data flows: error & rescue map (planning phase), shadow paths, interaction edge cases. Shared format with `/review` — plan it in specs, verify it in review.

## Key Design Decisions

- PR agent absorbed into `/ship` — eliminates conceptual overlap, one command for the full shipping path
- `/review` is independent from the pipeline review agent — deeper analysis, usable on any code, not just pipeline output
- `/retro` persistence is JSON (machine-readable trends), output is markdown (human-readable snapshots)
- Error mapping format is shared between `/create-spec` (planning) and `/review` (verification) — same tables, two contexts
- All outputs are markdown files. No runtime code, no CLI, no server.
- Planning posture: HOLD — fill workflow gaps, strengthen foundation

## Story Dependencies

Batch 1 (parallel): `/ship` core, `/review` command, `/retro` analysis, error mapping
Batch 2 (parallel): `/ship` PR creation, `/retro` output & trends
Batch 3 (sequential): Integration testing & dogfooding

## Success Criteria

- `/ship` takes green branch to merged PR with zero manual PR body writing
- `/review` catches ≥1 failure mode per review that pipeline review missed
- `/retro` produces trend comparison against previous period snapshot
- Error mapping surfaces rescue gaps in technical sub-specs before implementation
