# Ralph Loop Orchestration — User Stories

> **Spec:** `.writ/specs/2026-03-27-ralph-loop-orchestration/`
> **Total Stories:** 4
> **Status:** Complete (4/4 complete)

## Stories Overview

| # | Story | Status | Priority | Tasks | Progress |
|---|-------|--------|----------|-------|----------|
| 1 | [/ralph plan — Cross-Spec Execution Planning](story-1-ralph-plan-command.md) | Completed ✅ | High | 7 | 7/7 |
| 2 | [CLI-Adapted Story Pipeline](story-2-cli-story-pipeline.md) | Completed ✅ | High | 7 | 7/7 |
| 3 | [Loop Script, Handoff, and Configuration](story-3-loop-script-and-handoff.md) | Completed ✅ | High | 7 | 7/7 |
| 4 | [/ralph status — Monitoring and Cursor Re-entry](story-4-ralph-status-and-review.md) | Completed ✅ | Medium | 7 | 7/7 |

**Total Tasks:** 28 (28 complete, 0 remaining)

## Dependencies

```
Story 1 (plan command)
    ↓           ↘
Story 2 (CLI)   Story 4 (status)
    ↓
Story 3 (loop + handoff)
```

- **Story 1** has no dependencies — it's the foundation (state format, planning command)
- **Story 2** depends on Story 1 (needs state format for CLI agent state updates)
- **Story 3** depends on Stories 1 and 2 (needs state format and PROMPT templates)
- **Story 4** depends on Story 1 (needs state format to read and display)
- Stories 2 and 4 can run in parallel after Story 1 completes

## Story Descriptions

### Story 1: `/ralph plan` — Cross-Spec Execution Planning

Create the `/ralph plan` Cursor command that scans all non-complete specs, resolves cross-spec and cross-story dependencies, assesses codebase state, and generates a cross-spec execution plan. Includes designing the state file format and execution plan structure. This is the entry point for the entire Ralph workflow.

**Key deliverables:**
- `commands/ralph.md` (plan mode section)
- `.writ/docs/ralph-state-format.md`
- State file format design
- Execution plan structure with dependency resolution

### Story 2: CLI-Adapted Story Pipeline

Design and create the PROMPT_build.md template that instructs a CLI agent how to execute a single Writ story through a simplified gate pipeline with back pressure (code → test → lint → state update → commit). Includes the state update protocol and CLI pipeline reference documentation.

**Key deliverables:**
- `scripts/PROMPT_build.md` template
- `.writ/docs/ralph-cli-pipeline.md`
- State update protocol for CLI agents
- `adapters/claude-code.md` Ralph execution section

### Story 3: Loop Script, Handoff Artifacts, and Configuration

Create the `scripts/ralph.sh` loop script with mode selection (plan/build), max iterations, and git push. Update `/ralph plan` to generate project-tailored handoff artifacts. Add Ralph configuration to `.writ/docs/config-format.md`.

**Key deliverables:**
- `scripts/ralph.sh` loop script template
- Handoff artifact generation in `/ralph plan`
- Ralph configuration keys in config format docs

### Story 4: `/ralph status` — Monitoring and Cursor Re-entry

Add status/review mode to `commands/ralph.md` that reads Ralph state files, presents human-readable progress, shows blockers and escalation reports, and guides the developer on next steps. Closes the Cursor→CLI→Cursor loop.

**Key deliverables:**
- `commands/ralph.md` (status mode section)
- Progress dashboard presentation
- Blocker/escalation display
- Next-step guidance

## Implementation Notes

### Recommended Order

1. **Story 1** first (foundation — everything depends on state format)
2. **Stories 2 and 4** in parallel after Story 1 completes
3. **Story 3** after Stories 1 and 2 complete (integration layer)

### Platform Awareness

- Stories 1 and 4 produce Cursor-native command content (`commands/ralph.md`)
- Story 2 produces CLI-native artifacts (PROMPT template, adapter updates)
- Story 3 bridges both (loop script + handoff generation from Cursor command)

### Success Criteria

- Autonomous execution across 3+ specs without intervention
- CLI pipeline produces code passing tests and lint
- State files enable resume after any interruption
- Genuine blockers escalate (<10% of iterations)
- Seamless Cursor→CLI→Cursor round-trip via state files
