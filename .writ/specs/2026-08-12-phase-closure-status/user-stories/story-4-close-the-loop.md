# Story 4: Close The Loop On The Live Phase 10b State

> **Status:** Not Started
> **Priority:** Medium
> **Dependencies:** Story 3
> **Estimated Tasks:** 6

## User Story

**As** the maintainer who filed this issue after watching `/status` report a finished
phase as five specs of work in flight,
**I want** the shipped `close-spec` run against the live Phase 10b state file,
**So that** the defect that motivated the spec is demonstrably gone rather than merely
unreachable in a test fixture.

## Context

This is the moment of truth. The issue was filed on an observation, not a hypothesis:

```
$ python3 scripts/phase-state.py progress --state .writ/state/phase-execution-20260812-0200.json
{'pending': 5, 'integrated': 2, ...}
```

Those five specs — `2026-08-12-disclosure-{create-spec,implement-phase,release,ship,verify-spec}`
— are all archived with `Status: Closed — Not Implemented (measured evidence, 2026-08-12)`.
Each declares `dependencies: [2026-08-12-disclosure-implement-story]`, which is
`integrated`; none is depended upon by anything, so the cascade of Story 2 has no effect
here. All five have `laneBranch: null` and `attempts: 0` — the no-lane path.

**Stated concern, carried forward deliberately:** `.writ/state/` is gitignored. This
story commits nothing. It is retained because it is the only story that exercises the
full chain against real data, and because leaving the live file wrong would mean the
issue's own reproduction still reproduces after the spec ships. Its definition of done
is captured command output recorded in this file, not a diff.

The issue explicitly rejected hand-editing this JSON as the *fix* — that would have left
the schema unable to express the state. Now that the schema can express it, running the
shipped subcommand is the legitimate correction rather than the workaround.

## Acceptance Criteria

**AC-1: Each closed spec is recorded with a reason drawn from its archived spec**
```
Given the five archived disclosure specs, each headed
      "Status: Closed — Not Implemented (measured evidence, 2026-08-12)"
When close-spec is run once per spec against .writ/state/phase-execution-20260812-0200.json
Then each spec's status is closed_unimplemented
And each closure.reason cites the measured evidence that closed it, matching the
    archived spec's recorded rationale rather than a generic placeholder
```

**AC-2: The phase stops reporting closed work as pending**
```
Given all five specs have been closed
When `phase-state.py progress --state .writ/state/phase-execution-20260812-0200.json` runs
Then pending is 0
And closed_unimplemented is 5
And integrated is 2
And current is null
```

**AC-3: Git is untouched**
```
Given the repository before Story 4 begins
When the five close-spec invocations complete
Then `git status --porcelain` shows no change attributable to this story
And no branch was created, renamed, or deleted
And each result reported phaseBranchClean: true
```

**AC-4: Health and reconciliation stay clean**
```
Given the corrected state file
When `phase-state.py reconcile --state S --repo .` runs
Then it returns consistent with attention: false
And `phase-state.py health --state S --repo .` returns no Attention attributable to
    the closures
```

**AC-5: `/status` reports the phase honestly**
```
Given the corrected state file
When the /status Step 4 phase-progress summary is produced from the reducer output
Then the phase is not presented as having work in flight
And the five closed specs are surfaced as closed by decision, with their reasons
```

## Implementation Tasks

- [ ] Capture the **before** state as evidence: record the current
      `progress` output verbatim in this story file under a "## Evidence" heading, so the
      defect and its correction are both preserved after the gitignored file changes.
- [ ] Read each of the five archived specs' `Status:` header and closure rationale from
      `.writ/specs/archive/2026-08-12-disclosure-*/spec.md` to source a real reason
      string per spec (AC-1) — do not invent a generic one.
- [ ] Run `close-spec` once per spec against
      `.writ/state/phase-execution-20260812-0200.json` with `--repo .` and the sourced
      reason, confirming each invocation reports `phaseBranchClean: true`.
- [ ] Capture the **after** evidence: `progress`, `reconcile`, and `health` output
      verbatim in the "## Evidence" section (AC-2, AC-4).
- [ ] Confirm `git status --porcelain` is unchanged by this story and that
      `git branch --list 'writ/*'` matches its pre-story listing (AC-3).
- [ ] **Verify:** produce the `/status` Step 4 phase-progress summary from the corrected
      file and confirm it reads honestly (AC-5); then run the full `bash scripts/eval.sh`
      one final time as the spec's exit check.

## Technical Notes

- **All five are the no-lane path.** `laneBranch: null`, `worktreePath: null`,
  `attempts: 0`. No worktree removal occurs and no branch is touched — which is exactly
  why AC-3 is checkable as a strict "git unchanged" assertion.
- **The cascade is a no-op here.** Each closed spec depends on
  `2026-08-12-disclosure-implement-story` (integrated), and nothing depends on the closed
  five. If a `skipped_blocked` appears in the after-state, something in Story 2's
  `_transitive_dependents` reuse is walking the graph backwards — treat it as a Story 2
  defect, not a data quirk to accommodate.
- **`2026-08-12-governor-enforcement` must stay `integrated`.** It depends on
  `disclosure-implement-story`, not on any of the five. It is also in
  `TERMINAL_SPEC_STATUSES`, so Story 2's skip rule protects it twice. Verify it after.
- **Phase `status` remains `executing` unless separately decided.** This story corrects
  *spec* statuses. Whether the phase record itself should move to a terminal status is a
  `/implement-phase` completion concern (BR-6) and is out of scope here — note the
  observed value in the evidence rather than changing it.
- Record the evidence in this story file, not in `.writ/state/`. The point of the
  exercise is that the proof survives the ephemeral file.

## Definition of Done

- [ ] Before and after `progress` output is recorded verbatim in this file's
      "## Evidence" section
- [ ] All five specs are `closed_unimplemented` with sourced, spec-specific reasons
- [ ] `progress` reports `pending: 0`, `closed_unimplemented: 5`, `integrated: 2`,
      `current: null`
- [ ] `2026-08-12-governor-enforcement` and `2026-08-12-disclosure-implement-story` are
      still `integrated`
- [ ] `reconcile` is `consistent`; `health` shows no closure-caused `Attention`
- [ ] `git status --porcelain` and the `writ/*` branch listing are unchanged by this story
- [ ] Full `bash scripts/eval.sh` reports no new findings

## Evidence

_(Populated during implementation — see task 1 and task 4.)_

**Before:**

```
```

**After:**

```
```

## Context for Agents

- **The originating observation:** `spec.md → ## The Defect` carries the exact
  `progress` output this story must eliminate
- **Business rules:** BR-1 (terminal), BR-2 (reason required — hence the sourced reasons),
  BR-5 (health path stays clean) — `spec.md → ## Business Rules`
- **The stated concern about this story's value:** `spec.md → ## Implementation Approach
  → ### Closing the loop`
- **Live data shape:** `spec.md → ## The Defect` and this story's Technical Notes record
  the dependency graph and lane state of all seven specs in the file
- **Source for reasons:** `.writ/specs/archive/2026-08-12-disclosure-*/spec.md` headers
  and their "Not implemented — closed 2026-08-12 on measured evidence" blocks
- **Do not** hand-edit the JSON. Every mutation goes through `close-spec`; that is the
  whole point of the preceding three stories.
