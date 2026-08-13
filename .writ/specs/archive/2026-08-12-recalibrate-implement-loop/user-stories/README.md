# User Stories — Recalibrate the implement-spec / implement-story Loop

> **Status:** Completed ✅ — 3/3 stories (100%)

| # | Story | Status | Depends on | Files |
|---|---|---|---|---|
| 1 | implement-spec orchestration & bookkeeping clarity | Completed ✅ | — | `commands/implement-spec.md` |
| 2 | Sub-agent result completeness | Completed ✅ | — | `skills/subagent-result-completeness/SKILL.md`, `commands/implement-story.md` |
| 3 | Sub-agent worktree integration | Completed ✅ | 2 | `skills/subagent-worktree-integration/SKILL.md`, `commands/implement-story.md` |

## Dependency graph

```
1 (independent)
2 ─→ 3
```

Story 1 touches only `implement-spec.md` and has no dependency on 2/3. Stories
2 and 3 both touch `implement-story.md` — sequenced (3 depends on 2) to avoid
concurrent edits to the same file's adjacent inserted sections.

## File ownership

`commands/implement-spec.md` is owned solely by **Story 1**.
`commands/implement-story.md` is touched by **both Story 2 and Story 3** —
this is why they are sequenced rather than run in parallel. Each new skill
file (`skills/subagent-result-completeness/SKILL.md`,
`skills/subagent-worktree-integration/SKILL.md`) is owned by its own story
only.

## Cut order

If shortened, drop from the bottom: **3**, then **2**. Story 1 is the
smallest, most self-contained fix (three bookkeeping amendments to one file)
and delivers value independent of the other two. Story 2 delivers value on
its own even without Story 3. Story 3 must not ship without Story 2, since it
depends on it directly.
