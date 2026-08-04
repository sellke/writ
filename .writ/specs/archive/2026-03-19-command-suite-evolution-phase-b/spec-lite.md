# Command Suite Evolution — Phase B Spec Lite

> Source: spec.md
> Created: 2026-03-19
> Phase: B of 2 (dependent extensions)
> Prerequisite: Phase A (`2026-03-19-command-suite-evolution`) must be complete first

## What We're Building

Three dependent extensions that connect previously disconnected systems: context auto-loading into agents, issue → spec promotion pipeline, and cross-session learning via batch refresh. All changes are edits to existing markdown files — no runtime code.

## The Three Phase B Changes

| # | Name | Effort | Files | Dependencies |
|---|------|--------|-------|--------------|
| 5 | `.writ/context.md` auto-loading | S | implement-story, implement-spec, status, coding-agent, review-agent, arch-check-agent | Phase A Stories 1+4 |
| 7 | Issue → spec promotion | S | create-spec, create-issue, status | Phase A Story 4 + Phase B Story 5 |
| 9 | `/refresh-command` batch analysis | M | refresh-command, status | Phase B Story 7 |

## Key Constraints

- All three stories are fully sequential: Story 5 → Story 7 → Story 9 (all touch `status.md`)
- `.writ/context.md` is always regenerated in full — never incrementally patched
- Issue promotion is additive — `spec_ref` written back, issue file never deleted
- Phase A must be complete before any Phase B story begins

## Files in Scope

**Commands:** commands/implement-story.md, commands/implement-spec.md, commands/status.md, commands/create-spec.md, commands/create-issue.md, commands/refresh-command.md

**Agents:** agents/coding-agent.md, agents/review-agent.md, agents/architecture-check-agent.md

## Success Criteria

- Every agent run starts with `.writ/context.md` loaded automatically
- Issues promote to specs with pre-populated discovery context
- `/status` surfaces stale untriaged issues (7+ days, no spec_ref)
- `refresh-command --batch` detects cross-session patterns with recurrence weighting
