---
name: _preamble
description: "Shared standing instructions referenced by every Writ command. Not directly invocable."
disable-model-invocation: true
---

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
would weaken **roadmap scope, a locked spec contract, or exit criteria** — a narrow,
semantic trigger, never a generic wrapper for uncertainty, progress, retries,
ordinary failures, or decisions already answered by repository artifacts.

Every qualifying challenge carries a `trigger` (`scope_degradation` or
`exit_criteria_degradation`) and all **four required parts**: `roadmap_or_spec_said`,
`recommendation`, `possibly_missing_context`, `cost_if_wrong`.

Apply an **evidence-based select-or-pause** boundary (ADR-013): a defensible,
low-risk, reversible choice may be selected automatically **with** a persisted audit
trail; missing evidence, critical ambiguity, or material irreversible risk instead
**pauses** and returns `challenge_required` with options for one explicit
`AskQuestion`. Nested commands **return** an audited selection or
`challenge_required`; only `/implement-phase` presents and persists the choice
(validator: `scripts/phase-state.py validate-challenge`). A malformed challenge is a
**contract error**, not a User Challenge.

## Autonomy Gate Classes

Extends ADR-013's select-or-pause boundary above; it does not replace it.

| Class | Behavior |
|---|---|
| Product & spec direction | **Human gate** — contract lock is an explicit human action |
| Production boundary (merge/PR/release/tag/publish) | **Human gate** — Prime Directive hard constraint |
| Design & UX judgment | **Human gate** — taste is not evidence-decidable |
| Destructive / irreversible | **Autonomous** only when the precondition below holds |
| Everything else | **Autonomous** within ADR-013's boundary, with audit rationale |

**Reversibility precondition.** A destructive-class operation runs unattended **only when both hold**: (1) its effect is provably git-revertable — confined to tracked files with a resolvable revert target; (2) the restore path is recorded **before** the mutation. If either fails, it **pauses** with a bounded `AskQuestion`.

**Stakes triage (ADR-023).** Before spending diligence on any decision — a read, a gate, a question, a verification step — answer two questions from what you already know. **Does the answer change what happens?** If no, it is not a decision: drop it. **How bad if it's wrong?** Reversible and contained → decide, act, record, no verification step. Irreversible or wide blast radius → full rigor, and the gate class above applies. The triage must cost less than the decision it governs; if answering it needs investigation, that *is* the answer — escalate. No universal exchange rate exists between a decision and its cost, so don't seek one. **Safety gates are never capped by count** — rarity is not irrelevance; a gate names the failure it catches and the cost of missing it, and one that can name neither is the candidate for removal.

## File Organization

All work is organized into `.writ/`: `specs/` (contracts, stories), `product/`
(roadmap, mission, strategy), `research/` (investigation outputs),
`decision-records/` (ADRs), `knowledge/` (accumulating cross-cutting facts),
`issues/` (fast-capture bugs/features), `state/` (ephemeral, gitignored).

## Artifact Integrity

Before doing work, verify declared **Required Artifacts** (*required* or *optional*) exist.
- **Required missing** → HALT; offer a bounded repair via AskQuestion naming the creating command. Never auto-run a mutating repair without confirmation.
- **Optional missing** → warn and continue in degraded mode.

Creating commands: roadmap/`mission.md` → `/plan-product`; `.writ/docs/` → `/initialize`; a spec under `.writ/specs/` → `/create-spec`. This is adapter-neutral: pure existence checks, no platform hooks; never inspect `.writ/state/`.

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
