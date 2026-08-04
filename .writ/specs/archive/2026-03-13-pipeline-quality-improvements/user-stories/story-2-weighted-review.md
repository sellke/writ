# Story 2: Weighted Review

> **Status:** Completed ✅
> **Priority:** High
> **Dependencies:** None

## User Story

**As a** Writ pipeline operator
**I want** the review agent to allocate attention proportionally to the change surface
**So that** small changes get faster, shorter reviews without sacrificing defense-in-depth for larger changes

## Acceptance Criteria

- [x] Given the coding agent completes a style-only change (CSS/Tailwind/className), when the review runs, then the output focuses deep scrutiny on visual consistency and accessibility, with quick-scan for other categories
- [x] Given the coding agent completes a full-stack change (API routes, schema, auth), when the review runs, then every category receives full-depth review (same as current behavior)
- [x] Given the implement-story orchestrator receives coding agent output, when it prepares review agent input, then it classifies the change surface based on files changed and their types
- [x] Given the review agent receives a change_surface parameter, when it runs the checklist, then no categories are ever skipped — all are scanned at minimum quick-scan depth
- [x] Given a style-only change triggers a security issue (e.g., dynamic className from user input), when the review agent quick-scans security, then it still flags the issue

## Implementation Tasks

- [x] 2.1 Read current `agents/review-agent.md` and `commands/implement-story.md` to understand Gate 3 invocation
- [x] 2.2 Add change surface classification logic to `commands/implement-story.md` — after coding agent completes, classify as: style-only, single-component, cross-component, or full-stack based on files changed
- [x] 2.3 Update `commands/implement-story.md` Gate 3 to pass `change_surface` as a new input parameter to the review agent
- [x] 2.4 Add `change_surface` to the review agent's Input Requirements table in `agents/review-agent.md`
- [x] 2.5 Restructure the review agent's Review Checklist section to accept and use `change_surface` — deep scrutiny for focus areas, quick-scan (flag only if obvious) for others
- [x] 2.6 Verify the four classification levels (style-only → full-stack) have clear, correct focus/quick-scan mappings

## Notes

- Classification heuristic: style-only = only CSS/SCSS/Tailwind files or only className prop changes. single-component = changes in one component file (state, handlers, props). cross-component = shared hooks/utils/context. full-stack = API routes, schema, migrations, auth.
- The review agent's existing severity definitions (Critical/Major/Minor) are unchanged. Weighted review changes WHERE the agent looks hard, not HOW it judges what it finds.
- "Quick scan" means: scan the checklist items, flag anything that jumps out, don't write "N/A" for every item. The output should be shorter, not just faster.
- This touches TWO files: review-agent.md (prompt changes) and implement-story.md (classification + parameter passing).

## Definition of Done

- [x] All tasks completed
- [x] All acceptance criteria met
- [x] `agents/review-agent.md` accepts and uses `change_surface` parameter
- [x] `commands/implement-story.md` classifies change surface and passes it to Gate 3
- [x] No categories are ever fully skipped (defense-in-depth preserved)
