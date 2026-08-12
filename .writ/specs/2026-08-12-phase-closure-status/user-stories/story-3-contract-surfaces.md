# Story 3: Contract Surfaces — Schema Doc and Commands

> **Status:** Not Started
> **Priority:** High
> **Dependencies:** Story 2
> **Estimated Tasks:** 7

## User Story

**As a** maintainer running `/implement-phase` or `/status`,
**I want** the schema contract and both commands to describe closure the way the
reducer now implements it,
**So that** a closed spec is understood rather than merely tolerated — and a phase that
descoped work says so out loud instead of quietly reporting COMPLETE.

## Context

Stories 1 and 2 changed behavior. This story changes the contracts that behavior is
supposed to satisfy — the canonical schema doc and the two commands that write and read
the state.

Two of these edits are load-bearing rather than descriptive:

- **The widened `blockedBy`.** The issue's own argument against reusing
  `skipped_blocked` was that it "requires a `blockedBy` upstream *failure*." The chosen
  cascade makes `blockedBy` mean "upstream reached a terminal state without delivering."
  Undocumented, that sends a `/status` reader hunting for a quarantine branch that never
  existed.
- **The mandatory report section.** A phase may report COMPLETE with closed specs. That
  is only honest if the report names each one and its reason.

## Acceptance Criteria

**AC-1: The schema doc describes the new status and the widened field**
```
Given .writ/docs/phase-execution-state-format.md
When it is read
Then the specs.{id}.status row lists closed_unimplemented and challenge_required
And a "Closure by Decision" section defines the status as terminal, contrasts it with
    failed/quarantined/skipped_blocked, and states the required-reason rule
And blockedBy is documented as "upstream reached a terminal state without delivering
    — quarantine or closure"
And the Progress and Health section's status enumeration matches SPEC_STATUSES exactly
```

**AC-2: Exit criterion 1 admits closure as terminal**
```
Given commands/implement-phase.md frontmatter
When exit_criteria[0] is read
Then it names closed_unimplemented alongside merged, quarantined, and skipped_blocked
And the criterion still requires failed work to exist only on writ/quarantine/ branches
```

**AC-3: Both closure paths are wired into the command**
```
Given commands/implement-phase.md
When Step 1.2b and Step 3.3 are read
Then Step 1.2b describes closing a resolved spec at decomposition time rather than
    authoring or building it
And Step 3.3 describes mid-run closure and explicitly distinguishes it from failure
    handling — no retry, no quarantine, no recovery path implied
And both cite `phase-state.py close-spec --reason` as the mechanism
```

**AC-4: The phase report must name every closed spec**
```
Given a phase where every spec is integrated or closed_unimplemented
When the completion report is produced
Then the terminal verdict is COMPLETE
And the report carries a "Closed by decision" section listing each closed spec with the
    reason recorded in its closure record
And the section is mandatory whenever any spec is closed — never omitted for brevity
```

**AC-5: `/status` reports the new counts**
```
Given commands/status.md Step 4
When the per-status count list is read
Then it includes closed_unimplemented and challenge_required
And the section remains explicitly read-only
```

**AC-6: Static assertions lock the surfaces in place**
```
Given check_phase_closure() in scripts/eval.sh
When `bash scripts/eval.sh --check=phase-closure` runs
Then require_literal assertions verify the reducer exposes cmd_close_spec, the schema
    doc carries the closure section, implement-phase carries both closure paths and the
    report section, and status.md carries the new counts
And the check reports zero findings
```

## Implementation Tasks

- [ ] **Write the static assertions first.** Add the AC-6 `require_literal` calls to
      `check_phase_closure()` in `scripts/eval.sh`, modeled on the assertion block at
      the tail of `check_phase_health()` (`scripts/eval.sh:2398-2407`). They fail
      against the current docs and commands.
- [ ] Update `.writ/docs/phase-execution-state-format.md`: the `specs.{id}.status` row
      in the field-contract table, a new "Closure by Decision" section placed after
      "Quarantine and Resume", the widened `blockedBy` definition, and the status
      enumeration under "Progress and Health" (AC-1).
- [ ] Update `commands/implement-phase.md` frontmatter `exit_criteria[0]` to admit
      `closed_unimplemented` (AC-2).
- [ ] Wire Step 1.2b: record the decomposition-time closure path — a feature that
      resolves to a spec the pre-pass decides not to build is closed with a reason
      rather than authored (AC-3).
- [ ] Wire Step 3.3: record the mid-run closure path and state plainly how it differs
      from the failure path above it — no `classify`, no retry, no `quarantine`, no
      recovery command (AC-3).
- [ ] Add the mandatory "Closed by decision" section to the completion report in
      `commands/implement-phase.md`, and update `commands/status.md` Step 4's count list
      (AC-4, AC-5).
- [ ] **Verify:** run `bash scripts/eval.sh --check=phase-closure`, then the full
      `bash scripts/eval.sh` to confirm the doc and command edits break no other check —
      `length`, `broken-refs`, `required-sections`, `loop-bounds`, and
      `autonomy-governance` all read these files.

## Technical Notes

- **`--check=length` and `--check=leanness` read `commands/implement-phase.md`.** It is
  already a large file under a byte budget. Add prose economically; a verbose closure
  section can fail a size check that has nothing to do with this spec.
- **`loop-bounds` reads the frontmatter.** Editing `exit_criteria` touches the block
  that `scripts/eval-loop-bounds.py` validates. Re-run that check specifically, not just
  `phase-closure`.
- **Do not soften exit criterion 1's quarantine clause.** "Failed work exists only on
  `writ/quarantine/<spec-id>` branches" stays true: a closed lane is retained under
  `writ/phase/...`, and it is not failed work. Adding closure must not create a loophole
  that lets genuinely failed work sit outside quarantine.
- **BR-6 is the honesty constraint.** COMPLETE-with-closures is only defensible because
  the report names them. If the report section is ever made conditional or optional, the
  COMPLETE verdict becomes a lie. Keep the word "mandatory" in the command text so the
  static assertion has something to anchor to.
- The adapters (`adapters/cursor.md`, `adapters/claude-code.md`, `adapters/codex.md`)
  reference tool names, not status vocabularies. Check whether
  `check_phase_quarantine` asserts against them (`scripts/eval.sh:2279-2281`) and
  follow that precedent only if closure genuinely needs a platform translation — it
  probably does not.

## Definition of Done

- [ ] The schema doc carries the closure section, the updated status row, and the
      widened `blockedBy` definition
- [ ] `exit_criteria[0]` admits `closed_unimplemented`
- [ ] Step 1.2b and Step 3.3 both describe their closure path and cite `close-spec`
- [ ] The completion report's "Closed by decision" section is documented as mandatory
- [ ] `commands/status.md` Step 4 lists both new statuses and stays read-only
- [ ] `check_phase_closure()` carries static assertions for every surface above
- [ ] `bash scripts/eval.sh --check=phase-closure` reports zero findings
- [ ] Full `bash scripts/eval.sh` shows no new findings in any other check

## Context for Agents

- **Business rules:** BR-4 (the widened `blockedBy` and why it must be documented),
  BR-6 (COMPLETE but named) — `spec.md → ## Business Rules`
- **Surface inventory:** `spec.md → ## Implementation Approach → ### Contract surfaces`
  lists every edit with its rationale
- **File ownership:** this story is the sole writer of the schema doc,
  `commands/implement-phase.md`, and `commands/status.md` — `spec.md → ## File Ownership`
- **Assertion pattern:** the `require_literal` block at `scripts/eval.sh:2398-2407`
- **Precedent for the doc shape:** the existing "Quarantine and Resume (R4 — Story 4)"
  section in `.writ/docs/phase-execution-state-format.md` — match its register and
  density
- **Do not** change reducer behavior here. If an assertion reveals a reducer gap, that
  is a Story 2 defect to fix in Story 2's file, not a contract to reword around.
