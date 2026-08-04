# Command Suite Evolution — Phase A Spec Lite

> Source: spec.md
> Created: 2026-03-19
> Phase: A of 2 (foundation + independent changes)
> Phase B: `.writ/specs/2026-03-19-command-suite-evolution-phase-b/`

## What We're Building

Six structural improvements to the Writ command/agent suite. All changes are edits to existing markdown files — no runtime code. Phase A establishes the foundation (config layer, iteration caps, spec-lite integrity, status rewrite, prototype escalation, ADR unification) that Phase B builds on.

## The Six Phase A Changes

| # | Name | Effort | Files | Dependencies |
|---|------|--------|-------|--------------|
| 1 | Config persistence layer | XS | ship, release, status, initialize | None |
| 2 | Agent iteration caps | XS | coding-agent, testing-agent, implement-story | None |
| 3 | Spec-lite integrity check | XS | verify-spec | None |
| 4 | `/status` North Star rewrite | XS | status | Story 1 |
| 6 | Prototype → spec escalation | S | prototype, create-spec | None |
| 8 | ADR unification | S | plan-product, create-adr | None |

## Key Constraints

- Stories 1 → 4 must be sequential (status.md touched by both)
- `MAX_SELF_FIX_ITERATIONS = 3` is a hard cap — no exceptions in agents
- `--fix` in verify-spec uses spec.md as source of truth — spec-lite is always the derivative
- decisions.md deprecation is soft — existing files untouched, new plan-product runs output ADRs
- `--from-prototype` marks Story 1 as Completed ✅ on spec creation
- Phase B requires Phase A complete before starting

## Files in Scope

**Commands:** commands/ship.md, commands/release.md, commands/status.md, commands/initialize.md, commands/verify-spec.md, commands/implement-story.md, commands/prototype.md, commands/create-spec.md, commands/plan-product.md, commands/create-adr.md

**Agents:** agents/coding-agent.md, agents/testing-agent.md

## Success Criteria

- `/status` orients instantly on second+ run using cached config
- Agents escalate cleanly (BLOCKED) after 3 self-fix attempts
- `verify-spec --fix` regenerates spec-lite from spec.md
- `/prototype` escalation → one command to formalize as spec
- `plan-product` outputs ADRs, not decisions.md
- Phase B can begin: config format defined, status rewrite complete
