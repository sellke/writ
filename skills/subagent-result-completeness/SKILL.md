---
name: subagent-result-completeness
description: "Tell a spawned gate agent's complete verdict apart from a mid-task stop, and recover when it stops early."
disable-model-invocation: true
status: candidate
---

# Sub-Agent Result Completeness

## Purpose

Decide whether a spawned gate agent's turn actually ended with the verdict its
gate requires, or merely stopped partway through — a partial finding, or a
sentence describing what it is about to check next, with no verdict at all.
Every gate in `implement-story.md` that spawns a sub-agent names an exact
verdict shape; a turn that ends without producing that shape is not done, no
matter how much useful-looking output it produced first. Treating a mid-task
stop as a real result is how an orchestrator advances a gate on work nobody
actually reviewed.

## When to Use

- Immediately after any spawned gate agent's turn ends, before the
  orchestrator reads its output as a verdict and decides what happens next.
- Whenever a turn ends with a partial finding, an unfinished checklist, or a
  sentence like "now let me check X" — with no terminal verdict line — rather
  than the gate's required shape.
- Not needed for inline steps that carry no sub-agent (lint/typecheck, change
  surface classification, drift response) — those never produce this
  ambiguity because nothing was spawned.

## How to Apply

### 1. Know the verdict shape each gate requires

A turn is complete only when it ends in the exact shape its gate names —
never a paraphrase, and never inferred from how thorough the output looks:

| Gate | Agent | Complete-turn signal |
|---|---|---|
| Gate 0 | architecture-check-agent | An `ARCH_CHECK:` line naming exactly one of `PROCEED`, `CAUTION`, `ABORT` |
| Gate 1 | coding-agent | No explicit success tag — a complete report is itself the "done" signal: Files Created/Modified, Tests Written, Self-Check Results, Summary. The only explicit status field is `STATUS: BLOCKED`, marking the stop state after the iteration cap |
| Gate 3 | review-agent | A `REVIEW_RESULT:` line naming exactly one of `PASS`, `FAIL`, `PAUSE` |
| Gate 4 | testing-agent | A `TEST_RESULT:` line naming exactly one of `PASS`, `FAIL` (or `STATUS: BLOCKED` after its own iteration cap) |
| Gate 4.5 | visual-qa-agent | A Gate Decision naming exactly one of `PASS`, `SOFT PASS`, `FAIL` |

### 2. Recognize a mid-task stop

A turn is a mid-task stop, not a result, when it ends in any of these —
regardless of how much analysis preceded it:

- A partial finding, with some criteria or files evaluated and others simply
  not mentioned.
- A narration of upcoming work ("next I'll verify...", "let me also check...")
  with no verdict line following it.
- Any of the table's required lines missing entirely from the final output.

A verbose, thorough-looking report that never emits its gate's required line
is exactly as incomplete as a one-sentence stub — length is not a proxy for
completeness.

### 3. Recover, never advance on a partial return

When a spawned agent's turn ends mid-synthesis: resume the same agent with
the same context it already has, and explicitly ask it to finish and state
its final verdict in the required shape. Do not summarize the partial output
into a verdict on the agent's behalf, and do not treat silence past a
partial finding as an implicit PASS or PROCEED. The gate does not advance —
its result is not yet known — until the resumed turn produces the required
line.

## Examples

**Gate 0, mid-task stop:**

```
...the integration touches three existing modules. Let me check whether the
migration path is backward compatible before I finish.
```
No `ARCH_CHECK:` line — incomplete. Resume and ask for the final verdict.

**Gate 3, complete:**

```
### Issues Found
...
### REVIEW_RESULT: FAIL
```
The required line is present — the gate has its answer (send back to Gate 1),
even though the verdict is FAIL rather than PASS.

**Gate 4, incomplete despite passing tests:**

```
Ran the story's test suite: 12 passed, 0 failed. Coverage looks good on the
new files. Let me also run the regression suite to be thorough.
```
No `TEST_RESULT:` line yet — this is a mid-task stop, not a PASS. Resume and
ask explicitly for the `TEST_RESULT:` verdict before treating Gate 4 as
cleared.
