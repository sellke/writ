# Spec: Terminal Status For A Spec Closed By Decision

> **Status:** Complete
> **Created:** 2026-08-12
> **Owner:** @AdamSellke
> **Dependencies:** []
> **Origin:** Promoted from issue `.writ/issues/improvements/2026-08-12-phase-execution-closed-unimplemented-status.md`

## Specification Contract

**Deliverable:** `phase-execution-v2` gains an *enforced* spec-status vocabulary that
includes a terminal `closed_unimplemented` for a spec closed by decision, a
`close-spec` reducer subcommand that writes it, and honest reporting of it through
`progress`, `/status`, and the phase report.

**Must Include:** The status is *enforced*, not documentary. `SPEC_STATUSES` is
currently dead code — adding a value to it changes nothing. Every status write goes
through one validator; `cmd_progress` seeds its counts from the same set so the two
cannot drift again.

**Hardest Constraint:** Validate on **write**, tolerate on **read**. The schema's
compatibility story is "unknown fields preserved so later stories can extend it." A
reducer that rejected an unrecognized status while *reading* would turn a newer state
file into a hard failure. `_set_status` guards mutation; `cmd_progress` keeps its
`counts.get(...)` fallback so an unknown status read from disk is still counted under
its own key.

**Success Criteria:**

1. `close-spec` on a `pending` spec yields `closed_unimplemented` with a recorded
   reason and `closedAt`; `progress` counts it separately and reports `0` for it when
   absent.
2. `close-spec` on an `implementing` spec removes the worktree, retains `laneBranch`,
   and leaves the phase branch head byte-identical.
3. A spec whose only unmet dependency is a closed spec becomes `skipped_blocked` with
   the closed spec in `blockedBy` and the cause reported as closure, not failure.
4. `reconcile` returns `consistent` for a phase containing closed specs; `health`
   returns no `Attention` attributable to closure.
5. Any attempt to write a status outside `SPEC_STATUSES` fails as a `ContractError`; a
   state file *read* with an unrecognized status still reports.
6. `bash scripts/eval.sh --check=phase-closure` passes, and it is green after **each**
   story — not only the last.

**Scope Boundaries:**

- **Included:** `scripts/phase-state.py`; a new `scripts/eval-phase-closure.py` plus
  `check_phase_closure` in `scripts/eval.sh`;
  `.writ/docs/phase-execution-state-format.md`; `commands/implement-phase.md` (exit
  criterion 1, Step 1.2b and Step 3.3 wiring, a mandatory "Closed by decision"
  phase-report section); `commands/status.md` Step 4 status list.
- **Excluded:** the spec-layer `Closed` handling in `scripts/spec-status.py` (already
  correct); any change to `phase-spec-result-v1`; any `schemaVersion` bump; migration
  tooling for existing state files (an additive change needs none).

## The Defect

`SPEC_STATUSES` in `scripts/phase-state.py:52-55` cannot express "terminated by
decision, will never run." None of the six existing values fits a spec the maintainer
deliberately chose not to build:

| Existing status | Why it does not fit |
|---|---|
| `failed` | Implies something went wrong. Nothing did. |
| `quarantined` | Preserves a recovery lane for work that broke. There is nothing to recover. |
| `skipped_blocked` | Requires an upstream blocker. These specs were not blocked. |
| `pending` | Means "not started yet." These will never start. |

Observed, on the live Phase 10b state file:

```
$ python3 scripts/phase-state.py progress --state .writ/state/phase-execution-20260812-0200.json
{'pending': 5, 'integrated': 2, ...}
```

Those five are `2026-08-12-disclosure-{create-spec,implement-phase,release,ship,verify-spec}`,
all archived with `Status: Closed — Not Implemented (measured evidence, 2026-08-12)`.
`commands/status.md` Step 4 reads this file on every `/status` run, so a finished phase
is reported as five specs of work in flight.

The spec layer already models this correctly — `scripts/spec-status.py:54` sets
`COMPLETE_FAMILY_PREFIXES = ("Complete", "Closed")`, treating `Closed` as terminal. The
phase-execution layer has no equivalent.

### Two findings that reshape the fix

**`SPEC_STATUSES` is dead code.** It is declared at `scripts/phase-state.py:52` and
referenced nowhere — no validation, no lookup, no membership test anywhere in the
repository. Adding `closed_unimplemented` to that set changes *zero* behavior. The
issue's framing ("`scripts/phase-state.py` — `SPEC_STATUSES`") therefore understates
the work: the deliverable is a `close-spec` subcommand that writes the status, plus
`cmd_progress` counting it, plus the doc and command wiring — and, since we are here,
making the set load-bearing so this class of drift cannot recur.

**The set is already wrong today.** `cmd_record_challenge` (`scripts/phase-state.py:316`)
writes `status = "challenge_required"`, a value absent from `SPEC_STATUSES` and absent
from the `cmd_progress` counts initializer. Enforcement added without also admitting
`challenge_required` would reject a write the reducer performs today. It joins the
vocabulary in Story 1.

## Business Rules

### BR-1 — `closed_unimplemented` is terminal

No lane is opened, no retry is scheduled, no recovery path is implied. It is distinct
from `failed`/`quarantined` (nothing failed) and from `skipped_blocked` (nothing
upstream blocked it). Once written, the only transition out is a human editing state.

### BR-2 — A closure without a reason is rejected

`close-spec --reason` is **required and non-empty**. The phase report is contractually
obliged to name each closed spec *and* its reason (BR-6), so an unexplained closure is
an invalid write, not a blank line in a report. A missing or whitespace-only reason
raises `ContractError("invalid_closure", ...)`.

### BR-3 — Mid-run closure frees the worktree, keeps the branch

A spec may be closed after its lane already exists. The reducer removes the worktree
(as `cmd_quarantine` does) but leaves the lane branch under its original
`writ/phase/{phase}/{spec}` name, recorded in `laneBranch`. Partial work is preserved
without a `writ/quarantine/` rename that would imply failure. The reducer captures the
phase-branch head before and after and reports `phaseBranchClean`, exactly as
quarantine does.

### BR-4 — Dependents cascade to `skipped_blocked`, and the cause is recorded

Direct and transitive dependents of a closed spec become `skipped_blocked` with the
closed spec appended to `blockedBy`.

This **widens `blockedBy`** from "upstream failure" to "upstream reached a terminal
state without delivering" — quarantine *or* closure. That widening is the price of the
chosen cascade and it must be paid explicitly: left undocumented, a reader who sees
`skipped_blocked: 3` in `/status` goes hunting for a quarantine branch that was never
created. Therefore:

- `.writ/docs/phase-execution-state-format.md` documents the widened meaning.
- `progress` reports the *cause* alongside the count, distinguishing dependents blocked
  by a quarantine from dependents blocked by a closure.

### BR-5 — Health never counts spec statuses, and must not start

`cmd_health` reads eval, verification, drift, and reconciliation — never spec statuses.
The issue's requirement that "health does not treat it as outstanding work" is
therefore satisfied by construction *provided* the one path from spec status into
health stays clean: a closed spec must produce **no `reconcile` mismatch**. Reconcile
gains explicit handling so a recorded closed lane is understood rather than flagged as
an anomaly.

### BR-6 — A phase with closed specs may report COMPLETE, but must name them

Exit criterion 1 of `/implement-phase` gains `closed_unimplemented` as a terminal
disposition. A phase whose every spec is `integrated` or `closed_unimplemented` reports
**COMPLETE** — matching the spec layer, where `Closed` is already in the complete
family. The phase report then carries a **mandatory "Closed by decision" section**
listing each closed spec and its recorded reason. The verdict stays clean; the
descoped work stays visible.

### BR-7 — Validate on write, tolerate on read

`_set_status` rejects any value outside `SPEC_STATUSES` at every mutation site.
Readers — `cmd_progress`, `cmd_show`, `cmd_reconcile` — never reject an unrecognized
status. `cmd_progress` seeds its counts dict from `SPEC_STATUSES` (so the two can never
drift) *and* retains `counts.get(status, 0) + 1` (so a status written by a newer
reducer is still counted under its own key rather than crashing or vanishing).

### BR-8 — The schema stays at version 2

New status values and an additive `closure` record are minor-compatible. No
`schemaVersion` bump, no migration tooling. Existing state files remain readable; the
reducer already preserves unknown fields.

### BR-9 — `phase-spec-result-v1` is unchanged

Closure is an *orchestrator* decision, never a subagent-reported result. `RESULT_STATUSES`
gains no value; `validate_result` is untouched. A subagent has no vocabulary for
"do not build this" and should not acquire one.

## Implementation Approach

### Reducer (`scripts/phase-state.py`)

```python
SPEC_STATUSES = {
    "pending", "implementing", "integrated", "failed",
    "quarantined", "skipped_blocked", "challenge_required",
    "closed_unimplemented",
}
TERMINAL_SPEC_STATUSES = {
    "integrated", "quarantined", "skipped_blocked", "closed_unimplemented",
}
```

A single guarded mutation helper replaces every direct `record["status"] = ...`
assignment:

```python
def _set_status(record: dict[str, Any], value: str) -> None:
    if value not in SPEC_STATUSES:
        raise ContractError("invalid_status", f"unknown spec status: {value!r}")
    record["status"] = value
```

Call sites converted: `cmd_create_lane`, `cmd_record_challenge`, `cmd_integrate`
(both the merge-conflict and success paths), `cmd_retry`, `cmd_quarantine` (both the
rename-failure and success paths, plus the dependent loop), and the new `cmd_close_spec`.
`cmd_init` builds records from a literal and is validated once at construction.

`cmd_close_spec` mirrors `cmd_quarantine`'s shape without its rename:

1. Require a non-empty `--reason` (BR-2).
2. Capture the phase-branch head.
3. Remove the worktree if one exists; null `worktreePath`; **retain** `laneBranch` (BR-3).
4. Set `closed_unimplemented`; write `closure: {reason, closedAt}`; append a
   `closed:{reason}` evidence entry.
5. Cascade transitive dependents to `skipped_blocked`, appending to `blockedBy` and
   recording the cause as closure (BR-4).
6. Re-read the phase-branch head; report `phaseBranchClean`.

`cmd_progress` seeds counts from `sorted(SPEC_STATUSES)` and adds a `blocked` breakdown
naming, per blocked spec, whether its blocker was quarantined or closed.

`cmd_reconcile` gains a `closed_unimplemented` branch: a recorded `laneBranch` that no
longer exists in git is reported as a mismatch, symmetric with the existing quarantine
handling, and `worktreePath` must be null.

### Eval coverage (`scripts/eval-phase-closure.py`, `scripts/eval.sh`)

A new `phase-closure` check follows the established pattern: a Python scenario file
emitting `PASS`/`FAIL` TSV over disposable git repositories, consumed by a
`check_phase_closure()` function in `scripts/eval.sh` that adds `require_literal`
static assertions against the reducer, the schema doc, and the two commands.

The check is **built incrementally so every story leaves it green**: Story 1 creates
the file and the `eval.sh` registration with only vocabulary/enforcement scenarios;
Story 2 appends the `close-spec` scenarios; Story 3 appends the static doc and command
assertions. `bash scripts/eval.sh --check=phase-closure` must pass at the end of each.

Eval scripts are excluded from the install surface automatically by
`is_shippable_script` (`scripts/install.sh:726`, `eval-*` pattern), so no manifest entry
is required. `phase-state.py` itself ships and is unaffected by the addition.

### Contract surfaces

- `.writ/docs/phase-execution-state-format.md` — the status list in the field-contract
  table, a "Closure by Decision" section, the widened `blockedBy` meaning (BR-4), and
  the `progress` status enumeration under "Progress and Health."
- `commands/implement-phase.md` — exit criterion 1 admits `closed_unimplemented`;
  Step 1.2b records the decomposition-time closure path; Step 3.3 records the mid-run
  closure path and distinguishes it from failure handling; the completion report gains
  the mandatory "Closed by decision" section (BR-6).
- `commands/status.md` Step 4 — the per-status count list gains the two new values.

### Closing the loop

Story 4 runs the shipped `close-spec` against
`.writ/state/phase-execution-20260812-0200.json` for the five archived disclosure specs,
then re-runs `progress` and `health` to prove the finished phase reports honestly.

**Stated concern, built anyway:** `.writ/state/` is gitignored, so Story 4 commits
nothing. It is retained because it is the observed defect the issue was filed on
(`pending: 5` on a phase that closed) and the only story proving the whole chain end to
end. Its definition of done is captured command output in the story file, not a diff.

## File Ownership

Single-writer per file, enforced by a strict story chain (1 → 2 → 3 → 4) so no two
stories touch a shared file concurrently.

| File | Story |
|---|---|
| `scripts/phase-state.py` | 1 (vocabulary, `_set_status`, progress), 2 (`close-spec`, reconcile) |
| `scripts/eval-phase-closure.py` | 1 (create), 2 (extend), 3 (extend) |
| `scripts/eval.sh` | 1 (register check), 3 (static assertions) |
| `.writ/docs/phase-execution-state-format.md` | 3 |
| `commands/implement-phase.md` | 3 |
| `commands/status.md` | 3 |
| `.writ/state/phase-execution-20260812-0200.json` | 4 |

## Out of Scope

- `scripts/spec-status.py` — the spec layer already treats `Closed` as terminal.
- `phase-spec-result-v1` and `RESULT_STATUSES` (BR-9).
- A `schemaVersion` bump or migration tooling (BR-8).
- A dedicated `writ/closed/{spec}` branch namespace — the lane keeps its original name
  (BR-3).
- Retroactive closure of the Phase 9 or Phase 10 state files; only the Phase 10b file
  named in the issue is corrected.
