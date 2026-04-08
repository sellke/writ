# Plan Mode Must Not Offer to Implement

> **Type:** Improvement
> **Priority:** High
> **Effort:** Medium
> **Created:** 2026-04-08
> **spec_ref:** .writ/specs/2026-04-08-plan-mode-command-integrity/spec.md

## TL;DR

Planning commands (`/create-spec`, `/plan-product`, `/new-command`) should produce markdown artifacts and stop — AI platforms default to offering implementation, violating Writ's contract-first boundary.

## Current State

- After `/create-spec` completes Phase 2 (spec package creation), Cursor and Claude Code often follow up with "Want me to start building this?" or switch into implementation mode unprompted
- Plan Mode's read-only enforcement prevents file creation *during* discovery, but nothing prevents the AI from pivoting to implementation *after* the spec files are written
- The system instructions define the planning/execution separation conceptually (ADR-001), but don't include an explicit "do not offer to implement" constraint at command exit
- Users who follow the prompt and say "yes" to building bypass the full SDLC pipeline (`/implement-story` gates: arch-check, boundary map, TDD, review, drift handling, testing, docs)

## Expected Outcome

- Planning commands terminate cleanly with their markdown deliverables and a "next steps" suggestion pointing to `/implement-spec` or `/implement-story`
- The AI never offers to implement, build, or code what was just planned — regardless of platform
- System instructions include an explicit hard constraint: planning commands produce specs, implementation commands produce code
- Adapter guides reinforce this boundary for platform-specific behaviors (Cursor's mode switching, Claude Code's subagent spawning)

## Relevant Files

- `system-instructions.md` — Root behavioral contract; needs an explicit planning/implementation boundary constraint
- `commands/create-spec.md` — Primary affected command; completion section should reinforce the boundary
- `adapters/claude-code.md` — Claude Code adapter; platform-specific tendency to offer implementation

## Related Issues

- [2026-04-02-codex-openclaw-lifecycle-support](../features/2026-04-02-codex-openclaw-lifecycle-support.md) — Adapter lifecycle concerns overlap with how platforms handle command exit

## Notes

- This is an enforcement gap, not a design gap — ADR-001 already establishes the principle. The issue is that the principle isn't enforced at the instruction level where AI platforms actually read it.
- The fix likely involves both a system-instructions hard constraint and per-command exit language. Commands already have `## Completion` sections that could include "do not offer implementation" as a terminal condition.
- Risk: over-constraining could make Writ feel rigid when users genuinely want a quick prototype. The `/prototype` command exists for that — the constraint should reference it as the escape valve.
