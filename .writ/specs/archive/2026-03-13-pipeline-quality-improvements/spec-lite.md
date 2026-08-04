# Pipeline Quality Improvements — Spec Lite

> Source: spec.md
> Purpose: Efficient AI context for implementation

## What We're Building

Eight improvements to Writ's agent pipeline that increase first-pass code quality, reduce review iterations, and make specs progressively more accurate. All changes are edits to existing markdown prompt files — no new files, no runtime code.

1. **Coding Agent Self-Check** — Agent runs tests + typecheck before handoff. Fixes issues with warm context instead of cold pipeline round-trips. Highest leverage single change.

2. **Weighted Review** — Review agent always scans everything but allocates attention proportionally to change surface (style-only → full-stack). Preserves defense-in-depth, directs focus, shorter output for small changes.

3. **"What Was Built" Record** — After all gates pass, append a `## What Was Built` section to the story file capturing implementation reality: files, decisions, deviations. Creates the "system spec."

4. **Living Spec Auto-Amendment** — When Gate 3.5 processes a Small drift deviation, apply the proposed amendment to `spec-lite.md` in addition to logging in drift-log.md. Specs become progressively more accurate.

5. **Cross-Spec Consistency Check** — During `/create-spec` contract proposal, scan other in-progress specs for domain overlap. Surface warnings before conflicts reach implementation.

6. **Documentation Agent Framework Agnosticism** — Restructure prompt with detection-first approach. Auto-detect VitePress/Docusaurus/Nextra/MkDocs/Storybook/plain README. Default to inline docs + README.

7. **Architecture Check → model: "fast"** — One-line change. Read-only triage doesn't need the expensive model.

8. **Status Auto-Orientation** — Add lightweight auto-orientation to system instructions. First session invocation surfaces: branch, active spec, next action.

## Key Design Decisions

- Weighted review uses **weighting, not skipping** — all categories always scanned at minimum depth
- "What Was Built" appends to story file (co-located context), not a separate file
- Living amendment only applies to Small drift. Medium/Large unchanged.
- Cross-spec check is keyword heuristic, not deep semantic analysis
- Status entry point is a 3-line summary in system-instructions.md, not the full `/status` command

## Story Dependencies

All 7 stories are independent — single parallel batch. Stories 2, 3, 4 all touch `implement-story.md` but at different gate points (Gate 3, Step 4, Gate 3.5).

## Success Criteria

- Coding agent self-check catches test failures before Gate 2
- Review output shorter for style-only changes
- spec-lite.md auto-updated on Small drift
- Cross-spec overlap warning fires on domain collision
- Arch check runs on fast model with same triage quality
