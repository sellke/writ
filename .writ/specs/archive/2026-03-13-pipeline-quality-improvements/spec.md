# Pipeline Quality Improvements Specification

> Created: 2026-03-13
> Status: Complete ✅
> Contract Locked: ✅
> Implementation Mode: `--quick` (prompt/protocol changes to markdown files)

## Contract Summary

**Deliverable:** Eight improvements to Writ's agent pipeline and command set that increase first-pass code quality, reduce review iterations, and make specs progressively more accurate — all implemented as changes to existing markdown prompt files.

**Must Include:** Coding agent self-check (highest leverage — reduces pipeline round-trips) and weighted review (most frequently-hit path in the pipeline).

**Hardest Constraint:** Several recommendations touch `implement-story.md` (weighted review, "what was built," living spec amendment). These changes must compose cleanly with each other and with the existing drift handling from Phase 1.

**Success Criteria:**
- Coding agent reports test/typecheck results in its output before handoff
- Review agent output is measurably shorter for style-only changes (fewer N/A checklist items)
- `spec-lite.md` contains at least one auto-applied Small amendment after a story with drift
- Cross-spec overlap warning fires when two specs touch the same domain area
- Architecture check agent uses `model: "fast"` with no quality regression on triage decisions

**Scope Boundaries:**
- Included: Self-check, weighted review, what-was-built, living amendment, cross-spec check, doc agent agnosticism, arch check model, status entry point
- Excluded: Parallel lint+review (dropped — dependency is real), context cache (dropped — coordination cost exceeds benefit), edit-spec cross-spec check (follow-up), Figma MCP deep integration

## Design Decisions

These decisions were made during the discovery conversation and stress-tested via adversarial questioning before contract lock.

### "What Was Built" Record
Appends to the story file itself after all gates pass — not a separate file. Keeps context co-located for future agents reading the story. The format is a `## What Was Built` section with implementation date, file counts, key decisions made during implementation, and deviation references.

### Living Spec Auto-Amendment
Modifies `spec-lite.md` only for Small drift severity. When Gate 3.5 processes a Small deviation with a proposed spec amendment, it applies the amendment text to `spec-lite.md` in addition to logging it in `drift-log.md`. Medium and Large deviations still require human approval — unchanged from Phase 1.

### Weighted Review (not Proportional Review)
The review agent always scans every category — no categories are ever skipped. Instead, the `implement-story` orchestrator classifies the change surface and passes it to the review agent as a `change_surface` parameter. The review agent allocates deep scrutiny to relevant areas and quick-scan to others. This preserves defense-in-depth while directing attention proportionally.

Change surface classifications:
- **style-only** — CSS, Tailwind, className changes. Deep: visual consistency, accessibility. Quick-scan: everything else.
- **single-component** — one component's state/handlers/props. Deep: AC verification, code quality, test coverage. Quick-scan: security, integration.
- **cross-component** — hooks, utils, context, shared code. Deep: all code quality + security + integration. Quick-scan: none (full depth).
- **full-stack** — API routes, schema, auth, migrations. Deep: everything. Quick-scan: none (maximum scrutiny).

### Cross-Spec Consistency Check
Scoped to `create-spec.md` only for this spec. `edit-spec.md` is follow-up work. The check is a lightweight heuristic — keyword overlap in affected domain areas across in-progress specs — not deep semantic analysis.

### Status Entry Point
Goes in `system-instructions.md` (loaded every session) as a brief auto-orientation suggestion, not the full `/status` health check. When Writ is first invoked without a specific command, it should surface: current branch, active spec, and suggested next action.

### Documentation Agent Framework Agnosticism
Restructured with a detection-first prompt: detect the project's documentation framework, then branch to framework-specific instructions. Default fallback is "inline docs + README updates" for projects with no documentation framework.

### Architecture Check Model
One-line change: `model: "fast"` in the agent configuration. Read-only triage operation (PROCEED/CAUTION/ABORT) doesn't require the expensive model.

## Recommendations Dropped (with rationale)

### Context Cache (dropped)
A `.writ/context/project-profile.md` cache was proposed to avoid redundant codebase scanning across commands. Dropped because: Writ commands are stateless markdown prompts with no persistent runtime for cache invalidation. Staleness bugs are invisible — the agent won't say "I'm working from stale context." The ~5s scanning cost per command doesn't justify the coordination complexity.

### Parallel Lint + Review (dropped)
Running Gate 2 (lint) and Gate 3 (review) in parallel was proposed to save a round-trip. Dropped because: the review agent's prompt explicitly accepts `lint_results` as input, and its FAIL criteria includes "Lint/typecheck failures not addressed." If review runs before lint completes, the review evaluates code that might change after lint auto-fix — potentially adding a re-run rather than saving one.

## Detailed Requirements

### Coding Agent Self-Check
The coding agent must run the project's test suite and typecheck before reporting completion. If tests fail, it fixes them itself with warm context rather than sending broken code through the pipeline. The self-check results (pass/fail counts, any issues fixed) must be included in the structured output so the pipeline knows what to expect at Gate 2.

### Weighted Review
The `implement-story` orchestrator must classify the change surface after the coding agent completes (based on files changed, file types, and change patterns). This classification is passed to the review agent as structured context. The review agent's prompt must be restructured to accept `change_surface` and adjust its review depth per category accordingly — deep scrutiny for focus areas, quick scan (flag only if something obvious) for others.

### "What Was Built" Completion Record
After all gates pass in `/implement-story`, before the commit, a `## What Was Built` section is appended to the story file. It captures: implementation date, files created/modified counts, key decisions made during implementation (derived from coding agent output and drift log), and references to any drift deviations. This creates the "system spec" — a record of implementation reality.

### Living Spec Auto-Amendment
In Gate 3.5 of `/implement-story`, when a Small deviation is processed: (1) log to drift-log.md as today, (2) additionally, read `spec-lite.md`, apply the proposed amendment text from the review agent's drift report, and write the updated `spec-lite.md`. The drift-log entry gets an additional field: `Spec-lite updated: Yes`.

### Cross-Spec Consistency Check
During Step 1.4 (Contract Proposal) of `/create-spec`, before presenting the contract, scan all other specs in `.writ/specs/` that are not status "Complete." For each, read its `spec-lite.md` and check for keyword overlap in domain areas (models mentioned, routes mentioned, shared utilities mentioned). If overlap is detected, add a `⚠️ Cross-Spec Overlap` section to the contract.

### Documentation Agent Framework Agnosticism
Restructure the documentation agent's prompt template with a detection phase: (1) check for VitePress, Docusaurus, Nextra, MkDocs, Storybook, or plain README, (2) branch to framework-specific instructions, (3) default to inline JSDoc + README updates for projects with no framework. Remove the VitePress-specific directory structure from the default path.

### Architecture Check Model
Change `model: default (inherits from parent)` to `model: "fast"` in the agent configuration block.

### Status Auto-Orientation
Add a note to `system-instructions.md` that when Writ is first invoked in a session without a specific command, it should provide a brief orientation: current git branch, active spec (if any), and suggested next action. This is not the full `/status` command — it's a 3-line summary.

## Implementation Approach

All changes are edits to existing markdown files in `commands/` and `agents/`. No new files, no runtime code, no new dependencies. Implement via `/prototype` per story since these are prompt/protocol changes.

### Files Affected

| File | Stories |
|------|---------|
| `agents/coding-agent.md` | 1 |
| `agents/review-agent.md` | 2 |
| `commands/implement-story.md` | 2, 3, 4 |
| `commands/create-spec.md` | 5 |
| `agents/documentation-agent.md` | 6 |
| `agents/architecture-check-agent.md` | 7 |
| `commands/status.md` | 7 |
| `system-instructions.md` | 7 |
