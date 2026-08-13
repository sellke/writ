# Spec: Recalibrate the implement-spec / implement-story Loop

> **Status:** Complete (2026-08-12)
> **Created:** 2026-08-12
> **Owner:** @AdamSellke
> **Dependencies:** []
> **Origin:** A full 6-story `/implement-spec` run (`2026-08-12-machine-evaluable-exit-criteria`), followed by `/verify-spec` and a `/refresh-command` signal-gathering pass, surfaced five concrete, evidenced friction points in how `/implement-spec` and `/implement-story` operate. This spec formalizes the fixes.

## Contract (Locked)

**Deliverable:** Recalibrate `/implement-spec` and `/implement-story` against
concrete friction from the just-completed 6-story run: clarify how per-story
pipelines are actually spawned, close two completion-bookkeeping gaps
(`spec.md` header sync, execution-state write), and add two new skills
(sub-agent result completeness, sub-agent worktree integration) that
`implement-story.md` references the same way it already references
`tdd-cycle`, `drift-triage`, `boundary-map-computation`, etc.

**Must Include:** The two new skills must be *referenced* from
`implement-story.md`'s existing "this gate owns *when*, the skill owns *how*"
pattern — not just written as standalone files nobody reads. A skill nobody
references is invisible, and invisibility is exactly how this friction stayed
undocumented through the prior run.

**Hardest Constraint:** `implement-story.md` sits on `/refresh-command`'s
Tier-2 structural allowlist (`create-spec`, `implement-story`, `ship`,
`refactor`) — any edit must preserve required-sections presence, the
`_preamble.md` reference, and keep `bash scripts/eval.sh` green. Per
[ADR-009](../../decision-records/adr-009-command-agent-skill-boundary.md), a
skill describes a **capability**, not a workflow or a role — both new skills
must pass `scripts/lint-skill.sh`.

## Why This Exists

`2026-08-12-machine-evaluable-exit-criteria` ran all 6 of its own stories
through hand-orchestrated Gate 0/1/3 sub-agent calls (architecture-check,
coding, review), because invoking `/implement-story` via the platform's Skill
mechanism loaded its instructions inline rather than backgrounding — the
orchestrator had to manually spawn each story's gates instead of trusting a
nested command call to parallelize. Across roughly 18 sub-agent calls in that
run:

- **Nearly every spawned agent stopped mid-synthesis at least once** — visible
  as a partial finding or a "now let me check X" narration with no final
  verdict — requiring a manual resume-and-ask-again nudge before the
  orchestrator could act on the result. This roughly doubled the orchestration
  cost of the run.
- **Agent-tool subagents ran in isolated git worktrees by default**, including
  read-only ones. Nothing in `implement-story.md` documents how to reconcile
  an isolated worktree's output with the orchestrator's own checkout, so the
  diff → copy → re-verify → cleanup dance was invented fresh for every gate,
  every story.

Separately, `/verify-spec` on the completed spec found `spec.md`'s own header
status still read `Not Started` after all 6 stories were `Completed ✅` —
`implement-spec.md`'s completion step updates story files and
`user-stories/README.md`, but never the spec's own header. And the
orchestrator's execution-state JSON (`.writ/state/execution-*.json`) was
written once at the start of the run and never updated per-story — progress
was tracked ad hoc instead, and the stale file was ultimately discarded rather
than maintained, which would have broken `--resume` had the run been
interrupted.

None of these are hypothetical: each is a specific, repeated event from one
real run, not a generic "commands could be better" concern.

## 🎯 Experience Design

This is a tooling spec — the "user" is the maintainer/orchestrator running
`/implement-spec` or `/implement-story`, not an end-user UI.

- **Entry point:** a maintainer running `/implement-spec` across a
  multi-story spec, or `/implement-story` directly on one story
- **Happy path:** a spawned gate agent returns its complete verdict on first
  stop; if the platform isolated it in a worktree, the orchestrator integrates
  it back via a documented, repeatable procedure instead of improvising one
- **Moment of truth:** the orchestrator stops having to manually judge "was
  that a real verdict or a mid-task narration?" before deciding whether to
  resume the agent
- **Feedback model:** the orchestrator's next action (merge the worktree, or
  resume the agent for its final verdict) is named by the skill it read, not
  invented per-story
- **Error experience:** a spawned agent stopping mid-task is itself the
  condition `subagent-result-completeness` names, with a concrete recovery
  step — resume it, never advance the gate on a partial return

## 📋 Business Rules

1. **Skills describe capabilities, not workflows** (ADR-009). The two new
   skills document *what a spawned agent's final output must contain* and
   *how to reconcile isolated-worktree output* — never "run implement-story"
   or any other workflow restatement.
2. **Every new skill reference in `implement-story.md` follows its existing
   phrasing convention exactly**: `` `Read skills/<name>/SKILL.md` for *how*
   ... This gate owns *when*...; the skill owns *how*. `` — the same pattern
   already used for `tdd-cycle`, `boundary-map-computation`,
   `change-surface-classification`, and `drift-triage`.
3. **No existing gate's behavior changes.** These are additive
   clarifications and bookkeeping fixes, not a pipeline redesign. Gate 0/1/3's
   PROCEED/CAUTION/ABORT and PASS/FAIL/PAUSE result contracts are untouched.
4. **`implement-spec.md`'s `Phase-Orchestrated Lane Mode` section and
   nested-worker constraints are untouched** — the fixes here apply to
   direct top-level invocation the same way they apply inside a phase lane,
   without needing separate treatment.
5. **The concurrent peer-session editing risk is explicitly out of scope.**
   During the prior run, another session refactored `implement-story.md`
   mid-execution. This spec does not attempt to detect or guard against that
   — it is a harder, separate problem, noted here so it is not silently
   forgotten, not solved here.

## Scope Boundaries

### Included

| File | Change |
|---|---|
| `commands/implement-spec.md` | Step 3.2 spawn-mechanism note; Step 3.3 execution-state write reinforcement; completion step spec.md-header sync |
| `commands/implement-story.md` | Reference the two new skills at every gate that spawns an isolated sub-agent |
| `skills/subagent-result-completeness/SKILL.md` | new — what a spawned agent's final output must contain before its turn is treated as done |
| `skills/subagent-worktree-integration/SKILL.md` | new — how to reconcile a spawned agent's isolated worktree with the orchestrator's checkout |

### Excluded

- **The concurrent peer-session command-file-editing risk** — noted in § Why
  This Exists, deliberately not solved here (see Business Rule 5)
- **`agents/*.md` agent definitions** — this session's evidence points at
  orchestration-level gaps (what the orchestrator does with an agent's
  output), not at the individual agent definitions themselves
- **`commands/implement-phase.md`** — not exercised in the run that produced
  this evidence; no finding here applies to it
- **Rewriting any existing gate's PROCEED/CAUTION/ABORT or
  PASS/FAIL/PAUSE contract** — out of scope; these fixes are additive

## Implementation Approach

1. **Story 1 — `implement-spec.md` orchestration & bookkeeping clarity.**
   Amend Step 3.2 (spawn-mechanism note), Step 3.3 (execution-state write
   reinforcement), and the completion step (spec.md header sync). No
   dependencies.
2. **Story 2 — sub-agent result completeness.** Author
   `skills/subagent-result-completeness/SKILL.md`; reference it from
   `implement-story.md`'s Gate 0/1/3 (and 4/4.5) sections. No dependencies.
3. **Story 3 — sub-agent worktree integration.** Author
   `skills/subagent-worktree-integration/SKILL.md`; reference it from
   `implement-story.md`. Depends on Story 2 — both touch the same file's
   adjacent sections, sequenced to avoid concurrent-write risk.

## Success Criteria

1. `implement-spec.md` Step 3.2 explicitly addresses the
   inline-vs-backgrounded `/implement-story` invocation ambiguity
2. `implement-spec.md`'s completion step updates `spec.md`'s own header
   status, not just story files and `README.md`
3. `implement-spec.md` Step 3.3's execution-state write is stated as a
   required disk write, not an optional log line
4. `skills/subagent-result-completeness/SKILL.md` and
   `skills/subagent-worktree-integration/SKILL.md` exist, pass
   `scripts/lint-skill.sh`, and are referenced from `implement-story.md` at
   every gate that spawns an isolated sub-agent
5. `bash scripts/eval.sh` stays green, including the Tier-2 structural check
   for `implement-story.md`
