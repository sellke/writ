---
name: create-goal
description: "Interview for a recurring task, then write a Goal Card with a machine-checkable finish line, or record that a loop is the wrong tool and give the best single prompt instead."
problem: "Recurring tasks get handed to autonomous loops without a checkable finish line, a sandbox where mistakes are cheap, or convergence, so the loop runs to its cap and nobody can say whether it finished."
outcome: "A Goal Card at .writ/issues/goals/ states the objective, output, DONE WHEN criteria in exit_criteria grammar, stages, and stop caps, or records a loop: no verdict with a single-prompt version."
entry_level: high
exit_criteria:
  - "the file is at .writ/issues/goals/<YYYY-MM-DD>-<slug>.md with a slug of at most 40 characters and a loop: yes|no header line"
  - "every DONE WHEN line names a count, a path, a named section, a length limit, or a format match, and none uses good, clear, insightful, or high-quality"
  - "the interview used at most three rounds and the card carries between two and four STAGES"
---

# Create Goal Command (create-goal)

## Overview

Interview the user about a recurring task, then write a Goal Card: the contract an autonomous loop needs before it cycles through plan, act, check, and adjust. The card's DONE WHEN lines use the same grammar as Writ's `exit_criteria`, so `/create-spec --from-issue` lifts them into the spec unchanged and `/implement-spec` runs against them.

When the task lacks one of the three loop ingredients below, the command says "don't loop this", writes the best single-prompt version, and saves that verdict. A `loop: no` card is a full success, not a failed run.

**When to use** — a task you expect to hand to a loop more than once, or anything described as "keep going until". Run it before `/create-spec` on such work.

## Invocation

| Invocation | Behavior |
|---|---|
| `/create-goal` | Interactive — describe the recurring task |
| `/create-goal "weekly changelog digest"` | Start with the task pre-loaded |

## The Three Ingredients

A loop is the right tool only when all three are present. Test each during the interview and name the first one that is missing.

| Ingredient | Present when | Missing when |
|---|---|---|
| **Checkable finish line** | Done can be decided by counting, matching, or checking presence, with no human judgment | Done means "good", "insightful", "clear", "ready", or "the user is happy" |
| **Bounded sandbox** | A wrong pass costs a revert, a rerun, or a discarded file | A wrong pass sends an email, spends money, deletes data, or changes production |
| **Convergent task** | Pass N+1 has strictly less left to do than pass N, and the remainder is measurable | Each pass can undo or redo the last one; the target moves; the work is one decision, not a series |

## Command Process

### Phase 1: Interview (Plan Mode)

Switch to Plan Mode. Ask at most three rounds of 2 to 4 questions each. This is a deliberate exception to Writ's one-question-at-a-time convention: the field set is fixed, the round cap is the command's promise to the user, and grouping questions is the narrower option space here. Do not extend past three rounds; missing fields after round three become part of the verdict.

**Round 1 — task, output, sandbox.** What is produced, in what form, at what path, for whom. What happens if a pass gets it wrong. Whether the output can be regenerated from scratch each pass or is edited in place.

**Round 2 — finish line and convergence.** Ask the user to finish the sentence "this is done when". Convert each answer to a checkable form before accepting it. Ask what pass N+1 knows or has that pass N did not; if the answer is "it tries again", convergence is missing.

**Round 3 — gaps only.** CONTEXT sources, CONSTRAINTS, STAGES, and caps not settled by rounds 1 and 2. Skip this round when nothing is open.

**Pushback rules.** Vague finish lines are refused, not softened. Propose a checkable proxy and ask the user to accept or replace it:

| The user says | Offer instead |
|---|---|
| "good", "high quality" | A rubric the card names: length limit, required sections, zero lint findings |
| "insightful", "useful" | Every claim cites a source; at most N items; each item names a decision it informs |
| "complete", "covers everything" | A checklist file the loop ticks; the count of unticked items is zero |
| "clear", "readable" | Reading-level ceiling, sentence-length ceiling, or a named style linter passing |
| "the user is happy" | Not checkable. Name the observable the user would look at and check that |

Name a missing ingredient as soon as its absence is confirmed. From that point the interview shortens toward the single-prompt version instead of filling the remaining fields.

### Phase 2: Card and Verdict (Plan Mode)

Present the completed Goal Card in the format below, then one paragraph of verdict. The verdict names each ingredient, says whether it is present, and states which one is weakest. "Loop it" and "don't loop this" are both acceptable verdicts. Do not soften a "don't loop this" into "loop it with caution".

**DONE WHEN grammar.** Each line is a present-tense assertion a script could check. Apply the two tests Writ already uses for `exit_criteria`: the swap test (pasted into another card, the line would be false or nonsensical) and the restatement test (the line cannot be derived from OBJECTIVE alone). Counts, presence of named sections, citation per claim, length limits, and format matches pass. Adjectives fail.

**STOP-CAPS vocabulary.** Use the loop bounds Writ's runners already read: `loop.max_iterations: N` and `on_exhaustion: halt_reported`, plus one line for the stall rule: `stalled 3 turns: stop and report`. A stall is three consecutive passes with no change to the DONE WHEN tally.

### Phase 3: Decision and Save (Agent Mode)

Return to Agent Mode and confirm with AskQuestion:

```
AskQuestion({
  title: "Goal Card",
  questions: [{
    id: "action",
    prompt: "Save this Goal Card?",
    options: [
      { id: "save", label: "Save it" },
      { id: "edit", label: "Edit a field first (I'll say which)" },
      { id: "reopen", label: "I have new information — one more round" }
    ]
  }]
})
```

**save**: write the file. **edit**: apply the stated change to the card text and re-present the decision. **reopen**: allowed once, only when the user supplies information the interview did not have; it does not raise the three-round cap for the next run.

**File location:** `.writ/issues/goals/YYYY-MM-DD-{slug}.md`. Create the folder if it is absent. The slug is lowercase, hyphenated, at most 40 characters, derived from OBJECTIVE. Write the card for both verdicts; the `loop:` header line carries the result.

**Confirmation:**

```
Created: .writ/issues/goals/YYYY-MM-DD-{slug}.md

{Title} (loop: yes, {N} DONE WHEN criteria, {S} stages, cap {N} iterations)
```

For `loop: no`, the second line reads `{Title} (loop: no — {missing ingredient}; single prompt saved)`.

**Emit after save.** After the card file is written, emit paste-ready `/goal` files. Do not AskQuestion on emit notes. Core Rule 4 still holds.

1. If `scripts/goal-emit.py` is missing, `add_finding` and continue. The save confirmation above still stands.
2. Otherwise run:

```bash
python3 scripts/goal-emit.py emit --card .writ/issues/goals/<YYYY-MM-DD>-<slug>.md
```

3. Print the invoke line the helper prints after its summary on a `pass` emit.
4. Relay the helper verdict:
   - `pass`, `fail`, or `unverifiable` (including `loop_no` when the saved card is `loop: no`) → `add_note`. The helper writes no emit dir on `loop: no`; do not create one yourself.
   - helper exit 2 → `add_finding`.
5. A `loop: no` save is still success. Emit notes never fail this command.

## Goal Card Format

```markdown
# {Title}

> **Type:** Goal
> **Priority:** {Low|Normal|High|Critical}
> **Effort:** {Small|Medium|Large}
> **Created:** {YYYY-MM-DD}
> **loop:** {yes|no}
> **spec_ref:** _(set when promoted via `/create-spec --from-issue`)_

## OBJECTIVE

{What is produced and for whom. One or two sentences.}

## OUTPUT

{The artifact and the path where it lives. Regenerated or edited in place.}

## DONE WHEN

- {present-tense, checkable assertion}
- {present-tense, checkable assertion}

## QUALITY

{Rules that raise the bar above DONE WHEN. Each one still checkable.}

## CONTEXT

- `{path or URL}` - {why it is needed}

## CONSTRAINTS

- {style or scope rule}
- Each cycle appends one line to the decision log: `{date} {stage}: {what changed and why}`

## STAGES

1. {stage} - {what it produces}
2. {stage} - {what it produces}

## STOP-CAPS

- loop.max_iterations: {N}
- on_exhaustion: halt_reported
- stalled 3 turns: stop and report

## VERDICT

{One paragraph: each ingredient, present or missing, and which is weakest.}

## SINGLE PROMPT

{Present only when loop: no. The best one-shot prompt for the task.}
```

**Section rules.** DONE WHEN carries 2 to 6 lines. STAGES carries 2 to 4. CONTEXT lists at most 5 sources; a card that needs more has an unbounded task. SINGLE PROMPT is omitted when `loop: yes`.

## Core Rules

1. **Boring and checkable.** A finish line the user cannot verify by counting or matching is refused. The proxy table in Phase 1 is the default answer to every adjective.
2. **Zero-loop is success.** A saved `loop: no` card with a single prompt meets this command's outcome. Do not steer the interview toward `loop: yes`.
3. **Three rounds is a cap, not a target.** Stop as soon as the card is complete or an ingredient is confirmed missing.
4. **The card is not a runner.** This command never registers a `/goal` hook, never iterates, and never calls `/create-spec`. Promotion is the user's next step.
5. **Sources are named, not invented.** CONTEXT lists paths and URLs the user supplied or that exist in the repository. Do not add sources the loop would have to discover.

## Integration with Writ

| Command | Relationship |
|---|---|
| `/create-spec --from-issue` | Promotes a `loop: yes` card: OBJECTIVE becomes the deliverable, DONE WHEN lines become success criteria, STAGES seed the stories, STOP-CAPS become the spec's `loop` block. Refuses `loop: no` cards and points at SINGLE PROMPT |
| `/implement-spec` | Runs the promoted spec under the card's caps |
| `/create-issue` | Captures bugs and ideas fast; use it when the task is not recurring and needs no finish-line test |
| `/implement-phase` | Supplies the `loop.max_iterations` and `on_exhaustion` vocabulary the card reuses |
| `/prototype` | The right next step when the verdict is `loop: no` and the single prompt is a code change |

## Completion

This command succeeds when:

1. **Goal Card saved** — a `.md` file exists at `.writ/issues/goals/YYYY-MM-DD-{slug}.md` with the header block and every section the format requires for its `loop:` value
2. **Finish line is checkable** — each DONE WHEN line passes the swap and restatement tests and contains no unverifiable adjective
3. **Verdict recorded** — the VERDICT section names all three ingredients and the weakest one
4. **Interview stayed bounded** — at most three rounds, plus at most one reopened round on new information
5. **Confirmation presented** — the user saw the file path and the one-line summary

A `loop: no` card with a SINGLE PROMPT section satisfies every criterion above.

**Suggested next step:** For `loop: yes`, run `/create-spec --from-issue .writ/issues/goals/{file}`. For `loop: no`, use the single prompt directly or run `/prototype` if it describes a code change.

**Terminal constraint:** This command produces a Goal Card (`.writ/issues/goals/`). Do not start the loop, do not call `/create-spec`, and do not execute the single prompt. The user decides when the card is promoted.

---

## References

- Standing instructions: [`commands/_preamble.md`](_preamble.md)
- Identity & Prime Directive: [`system-instructions.md`](../system-instructions.md)
