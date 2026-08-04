# Verification Checklists

Per-story manual verification artifacts. One file per story, named `story-{N}.md` to match its sibling contract `../story-{N}-{slug}.md`.

These are **not story contracts** — they are evidence that the story's acceptance criteria and Definition of Done were checked. Tooling that walks `user-stories/story-N-*.md` for spec contracts should ignore this subdirectory.

## Convention

| File | Purpose |
|---|---|
| `../story-{N}-{slug}.md` | The story contract — acceptance criteria, tasks, DoD, "What Was Built" |
| `verification/story-{N}.md` | The checklist that verified the contract was met |

Each verification file links back to its contract via `../story-{N}-{slug}.md`. Move pattern established 2026-04-26 to eliminate the `story-N-*.md` glob collision.
