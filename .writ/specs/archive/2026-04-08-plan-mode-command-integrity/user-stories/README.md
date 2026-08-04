# User Stories — Plan Mode Command Integrity

> Spec: `.writ/specs/2026-04-08-plan-mode-command-integrity/spec.md`

## Stories Summary

| # | Story | Status | Priority | Dependencies | Tasks | AC |
|---|-------|--------|----------|--------------|-------|----|
| 1 | [System-Level Hard Constraint](story-1-system-constraint.md) | Complete | High | None | 7 | 4 |
| 2 | [Per-Command Completion Sections](story-2-command-completion-sections.md) | Complete | High | Story 1 | 6 | 5 |
| 3 | [Adapter Reinforcement](story-3-adapter-reinforcement.md) | Complete | Medium | Story 1 | 7 | 5 |

**Total:** 3 stories, 20 tasks, 14 acceptance criteria

## Dependency Graph

```
Story 1 (System Constraint)
  ├── Story 2 (Command Completion Sections)
  └── Story 3 (Adapter Reinforcement)
```

Story 1 is the foundation — it adds the hard constraint that Stories 2 and 3 reference. Stories 2 and 3 are independent of each other and can run in parallel after Story 1 completes.

## Execution Order

1. **Story 1** — must complete first (2 files: `system-instructions.md`, `cursor/writ.mdc`)
2. **Story 2** and **Story 3** — can run in parallel after Story 1
   - Story 2: 9 command files
   - Story 3: 3 adapter files

## Progress

- [x] Story 1: System-Level Hard Constraint
- [x] Story 2: Per-Command Completion Sections
- [x] Story 3: Adapter Reinforcement
