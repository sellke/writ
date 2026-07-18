# Writ Command Preamble

> Every command in `commands/` references this file. Standing instructions that
> apply across the surface area live here, not duplicated per command.

## Plan Mode Integrity

When a command uses Plan Mode for discovery, the conversation is a phase, not the
deliverable. After discovery, resume the command's documented phases and produce
its artifacts. Planning commands create files and stop; they never offer to code.

### Narrow Recommended-Delivery Exception

Only a command that explicitly documents `--recommend` may act autonomously.
`/create-spec --recommend` authors a locked spec package and **stops**; only
`/implement-phase --recommend` continues into implementation, ending at the
completion report with manual UAT handoff. Every `--recommend` command enters an
explicit recommend-mode branch, validates its invocation matrix before mutation,
records decisions in `recommendation-log.md`, and retains every pause. No
`--recommend` command merges, opens PRs, or releases; without that explicit branch,
planning commands create files and stop.

## User Challenge (Scope-Degradation Escalation)

A **User Challenge** is a structured escalation used **only** when a proposed choice
would weaken **roadmap scope, a locked spec contract, or exit criteria**. It is a
narrow, semantic trigger — never a generic wrapper for uncertainty, progress,
retries, or ordinary failures, and never used for decisions already answered by
repository artifacts.

Every qualifying challenge carries a `trigger` (`scope_degradation` or
`exit_criteria_degradation`) and all **four required parts**:

1. **What the roadmap/spec said** (`roadmap_or_spec_said`)
2. **What Writ recommends** (`recommendation`)
3. **What context may be missing** (`possibly_missing_context`)
4. **Cost if the recommendation is wrong** (`cost_if_wrong`)

Apply an **evidence-based select-or-pause** boundary (ADR-013): a defensible,
low-risk, reversible choice may be selected automatically **with** a persisted
audit trail (the challenge plus decision evidence); missing evidence, critical
ambiguity, or material irreversible risk instead **pauses** and returns
`challenge_required` with selectable options for one explicit `AskQuestion`.

In phase orchestration, nested commands **return** an audited selection or
`challenge_required`; only the parent `/implement-phase` presents the choice and
persists the challenge, selected option, and decision timestamp for resume and
audit. The executable validator is `scripts/phase-state.py validate-challenge`. A
malformed challenge (any missing required part) is a **contract error**, not a
User Challenge and not an ordinary failure.

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

Before starting work, load relevant `.writ/knowledge/` entries and treat them as
first-class context, not optional reading.

## Adapter Neutrality

Commands must work identically on Cursor, Claude Code, and OpenClaw through the
generic tool-name vocabulary. Do not require platform-specific runtime hooks.
