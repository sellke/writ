# Writ Command Preamble

> Every command in `commands/` references this file. Standing instructions that
> apply across the surface area live here, not duplicated per command.

## Plan Mode Integrity

When a command uses Plan Mode for discovery, the conversation is a phase, not the
deliverable. After discovery, resume the command's documented phases and produce
its documented artifacts. Planning commands create files and stop. They never
offer to implement, build, or code.

### Narrow Recommended-Delivery Exception

Only a command invocation that explicitly documents `--recommend` may continue
from completed planning artifacts into implementation. The command must enter an
explicit recommend-mode branch, validate its authoritative invocation matrix
before mutation, persist the canonical delivery context and audit state, and
retain every documented pause and production boundary. Without that explicit
branch, planning commands create files and stop.

## File Organization

All work is organized into `.writ/`:

- `specs/` - feature contracts and stories
- `product/` - roadmap, mission, strategy
- `research/` - investigation outputs
- `decision-records/` - ADRs
- `knowledge/` - accumulating cross-cutting facts
- `issues/` - fast-capture bugs and features
- `state/` - ephemeral runtime state (gitignored)

## Tool Selection

- **AskQuestion** - bounded decisions with enumerable options
- **Plan Mode** - open-ended discovery and shaping
- **todo_write** - multi-step task tracking
- **Parallel tool calls** - independent reads, searches, or checks

## Knowledge Context

Before starting work, the orchestrator may load relevant entries from
`.writ/knowledge/`. Treat populated knowledge entries as first-class context,
not optional reading.

## Adapter Neutrality

Commands must work identically on Cursor, Claude Code, and OpenClaw through the
generic tool-name vocabulary. Do not require platform-specific runtime hooks.
