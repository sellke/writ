---
name: blast-radius
description: "Name the one fact a change is safe because of and push its evidence up a five-rung ladder."
disable-model-invocation: true
status: candidate
status_evidence: "Phase 15 (2026-10-25). 1 consumer: agents/review-agent.md; kept as a skill so the safety-fact switch can remove it cleanly."
---

# Blast Radius

## Purpose

A review can pass a change without saying why it is safe. This skill names the
one fact the change is safe because of, checks that fact against the code that
depends on the change, and records how well it was checked. A script re-derives
the rung from the cited evidence, so cite only what holds up.

This skill owns how to state the fact and gather its evidence. The consumer owns
when the section is required and what a failed check does to the verdict.

## When to Use

- A reviewer that must write a `### Safety Fact` section before it sets its
  verdict.
- Any review of a change whose callers could break: a changed function, file
  format, command-line interface, or contract.

## How to Apply

### Evidence Ladder

The ladder runs from weakest to strongest. The ladder is not cumulative: each
rung's evidence stands on its own, so a fact can reach `tested` without a `read`
line. The measured rung is the highest rung whose evidence checks out. The floor
is `traced`.

| # | Rung | Meaning | Evidence line |
|---|---|---|---|
| 1 | `claimed` | Someone said so: the coding agent's report, a commit message, a comment, the spec. | none; a non-empty **Fact** is enough |
| 2 | `read` | The reviewer read the code that makes the fact true. | `- read: path:line` or `- read: path:start-end` |
| 3 | `traced` | The reviewer followed the changed code to its callers, and each cited caller is consistent with the fact. | `- traced: path:line — <what this caller passes or expects>`, or `- traced: none — <search run>` |
| 4 | `tested` | A test exercises the fact and passed in the orchestrator's recorded run. | `- tested: path::test_name` |
| 5 | `reproduced` | The fact was observed in the running app. | `- reproduced: path/to/evidence/<label>/<feature>/result.json` |

What makes a line count:

- Paths are relative to the repo root. An absolute path, or one that resolves
  outside the repo (through `..` or a symlink), does not count.
- `read`: the file exists and the line, or the start of the range, is within it.
- `traced`: every cited `path:line` is valid as for `read`. When `blast_radius`
  lists consumers, at least one cited caller must be among them. `none` counts
  only when `blast_radius` has verdict `pass` and lists no consumers.
- `tested`: the test name occurs in the cited file, the recorded run has the
  line `exit code: 0`, and the recorded run names the test file.
- `reproduced`: the file is valid JSON with schema `app-verify-result-v1` and
  verdict `pass`.
- Every line you write for a rung must count. One bad citation drops that rung.

### Safety Fact section

Write this section after `### Security Assessment`:

```markdown
### Safety Fact
**Fact:** <one sentence: the single fact this change is safe because of>
**Holds:** yes | no
**Rung:** claimed | read | traced | tested | reproduced
**Evidence:**
- read: `src/parser.py:142`
- traced: `src/cli.py:88` — passes the user's file list, rejected earlier when empty
- tested: `tests/test_parser.py::test_empty_input`
```

The heading is exactly `### Safety Fact`, with nothing after it. **Rung** is the
rung you claim; the script prints your claim beside its measurement.

### Rules

- One fact. If the change is safe only because of two facts, name the weaker one.
- Name a fact about the code, not about the process: "no caller passes an empty
  list", not "the tests pass".
- Push the fact up the ladder as far as the evidence allows. Trace before you
  write `traced`; cite the test before you write `tested`.
- If tracing finds a caller that breaks the fact, write `**Holds:** no`, cite
  that caller, and FAIL with an issue at that location. Its category is
  `architecture`, or `security` when it is one.
- `**Holds:** no` beside a PASS verdict is a contradiction, and the gate fails
  it.

### Reading `blast_radius`

`blast_radius` is the JSON from `change-surface.py blast-radius`. For each
changed non-test file, `consumers` lists the files outside the change that
mention it, and `tests` lists the test files that do. `truncated` names the
changed files whose lists were capped.

- Start from it. Open each consumer of the file the fact is about and check
  what it passes or expects.
- It is a text-reference heuristic, not a call graph. A listed file may only
  mention the name, and a caller that builds the name at run time is not listed.
- When it is `(none)`, or its `verdict` is `unverifiable`, search for callers
  yourself and cite them.
- A file under `tests` supports `tested` only when you name the test and the
  file ran in `recorded_test_results`.

### `reproduced`

`reproduced` is out of reach on a first review, because behavioral verification
runs after review. Cite it only on a recode iteration, with a passing
`app-verify-result-v1` file for this story, and only when the paths that feature
checks did not change since that file was written.

### On a re-review

A re-review arrives with the script's `rung:` and `reason:` lines appended. Fix
what fell:

- `safety_fact_missing <item>`: write the section, or the named field.
- `safety_fact_below_floor <measured>`: the measured rung is under `traced`.
  Trace the callers and cite them, or cite a test from the recorded run.
- A `rung:` line whose measured rung is below your claim: a citation did not
  check out. Correct the path, the line, or the test name.
