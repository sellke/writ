# Technical Spec — Terminal Status For A Spec Closed By Decision

> Spec: [../spec.md](../spec.md)
> Stories: [1](../user-stories/story-1-enforced-status-vocabulary.md) ·
> [2](../user-stories/story-2-close-spec-subcommand.md) ·
> [3](../user-stories/story-3-contract-surfaces.md) ·
> [4](../user-stories/story-4-close-the-loop.md)

## Scope

A schema-level change to `phase-execution-v2`, implemented in its executable reference
`scripts/phase-state.py`, plus the contract surfaces that describe it and one correction
of live state. No application code exists in this repository; the deliverables are a
Python reducer, a bash eval check, a markdown schema doc, and two markdown command files.

## Current State (measured 2026-08-12)

```python
# scripts/phase-state.py:52-55
SPEC_STATUSES = {
    "pending", "implementing", "integrated", "failed",
    "quarantined", "skipped_blocked",
}
```

`grep -rn "SPEC_STATUSES" --include="*.py" --include="*.md" .` returns exactly one
non-issue hit: the declaration itself. The constant has **no consumers**.

Status mutation sites, all currently direct assignments:

| Site | Line | Writes |
|---|---|---|
| `cmd_init` | 132 | `"pending"` (record literal) |
| `cmd_create_lane` | 199 | `"implementing"` |
| `cmd_record_challenge` | 316 | `"challenge_required"` ← **not in the set** |
| `cmd_integrate` (conflict) | 369 | `"failed"` |
| `cmd_integrate` (success) | 381 | `"integrated"` |
| `cmd_retry` | 429 | `"implementing"` |
| `cmd_quarantine` (rename fail) | 477 | `"failed"` |
| `cmd_quarantine` (success) | 489 | `"quarantined"` |
| `cmd_quarantine` (dependents) | 499 | `"skipped_blocked"` |

`cmd_progress`'s counts initializer (line 685) hard-codes six keys and therefore also
omits `challenge_required` — the same drift, expressed twice.

## Target Design

### Vocabulary (Story 1)

```python
SPEC_STATUSES = {
    "pending", "implementing", "integrated", "failed",
    "quarantined", "skipped_blocked", "challenge_required",
    "closed_unimplemented",
}

TERMINAL_SPEC_STATUSES = {
    "integrated", "quarantined", "skipped_blocked", "closed_unimplemented",
}


def _set_status(record: dict[str, Any], value: str) -> None:
    """Single guarded mutation point. Write-validate; readers stay tolerant so a
    state file written by a newer reducer is never rejected on load."""
    if value not in SPEC_STATUSES:
        raise ContractError("invalid_status", f"unknown spec status: {value!r}")
    record["status"] = value
```

Every site in the table above routes through `_set_status`. `cmd_progress` seeds from
`sorted(SPEC_STATUSES)` and keeps `counts.get(status, 0) + 1`, so the initializer can
never again fall behind the vocabulary while unknown on-disk values still count.

### Closure (Story 2)

```python
def cmd_close_spec(args) -> dict[str, Any]:
    reason = (args.reason or "").strip()
    if not reason:                                    # before any load or git call
        raise ContractError("invalid_closure",
                            "a closure must record why the spec will not be built")
    state = _load(Path(args.state))
    record = _spec_record(state, args.spec)
    head_before = _git(repo, "rev-parse", state["phaseBranch"]).stdout.strip()

    wt = record.get("worktreePath")
    if wt and Path(wt).exists():
        _git(repo, "worktree", "remove", "--force", wt, check=False)
    record["worktreePath"] = None
    # laneBranch is RETAINED under its original writ/phase/{phase}/{spec} name.

    _set_status(record, "closed_unimplemented")
    record["closure"] = {"reason": reason, "closedAt": _now()}
    record.setdefault("evidence", []).append(f"closed:{reason}")

    for dep in _transitive_dependents(state, args.spec):
        dep_rec = state["specs"][dep]
        if dep_rec.get("status") in TERMINAL_SPEC_STATUSES:
            continue                                   # never downgrade finished work
        _set_status(dep_rec, "skipped_blocked")
        ...append args.spec to blockedBy...

    head_after = _git(repo, "rev-parse", state["phaseBranch"]).stdout.strip()
    ...atomic write; return phaseBranchClean = head_after == head_before...
```

Divergences from `cmd_quarantine`, each deliberate:

| Aspect | `quarantine` | `close-spec` |
|---|---|---|
| Branch | renamed to `writ/quarantine/{spec}` | **retained** as `writ/phase/{phase}/{spec}` |
| Worktree | removed | removed (same) |
| Reason | `--summary`, optional, defaults to `"terminal failure"` | `--reason`, **required, non-empty** |
| Failure record | `record["failure"]` | `record["closure"]` |
| Dependents | all cascade to `skipped_blocked` | cascade, **skipping terminal statuses** |
| Recovery hint | `git checkout {quarantine-branch}` | none — nothing to recover |

The terminal-status skip is a genuine behavioral difference from quarantine, not an
oversight to mirror. Quarantine cascades unconditionally; closure must not, because a
closed spec's dependent may legitimately already be `integrated`, and flipping it to
`skipped_blocked` would discard a recorded `mergeCommit`.

### Reconciliation and progress (Story 2)

`cmd_reconcile` gains a `closed_unimplemented` branch, symmetric with the existing
`quarantined` handling: a recorded `laneBranch` that no longer exists in git is a named
mismatch, and `worktreePath` must be null. Everything else about a closed spec is inert,
so a phase containing closures reconciles `consistent` — which is the only thing keeping
closure out of `cmd_health`'s `Attention` category (BR-5), since health never reads spec
statuses directly.

`cmd_progress` gains a per-blocked-spec cause breakdown, so `skipped_blocked: 3`
distinguishes dependents blocked by a quarantine from dependents blocked by a closure
(BR-4).

## Error & Rescue Map

Operations are file-and-git, not network — but the failure surface is real: a torn state
file or a mutated phase branch is unrecoverable damage to a resume boundary.

| Operation | What Can Fail | Planned Handling | Test Strategy |
|---|---|---|---|
| `close-spec` argument parse | `--reason` missing, empty, or whitespace-only | `blocker.code = invalid_closure`, exit 1, **state file bytes unchanged** — validated before `_load` and before any `_git` call | Scenario asserting byte-identical state file after each of the three bad-reason forms |
| `close-spec` spec lookup | `--spec` names a spec absent from `specs` | Existing `unknown_spec` blocker, exit 1, no mutation | Scenario with a bogus spec id |
| Any status write | Value outside `SPEC_STATUSES` | `invalid_status` naming the rejected value; nothing written | Scenario invoking a reducer path with a forced bad value |
| State read | On-disk status the reducer does not recognize | `progress` still exits 0 and counts it under its own key; **never rejected** | Scenario with a hand-written `status: "future_value"` |
| State read | File missing / malformed JSON | Existing `missing_state` / `invalid_state` blockers | Covered by existing sibling checks |
| Worktree removal | Recorded `worktreePath` already gone from disk | `check=False` on the git call; `worktreePath` nulled; closure proceeds | Scenario deleting the worktree directory before closing |
| Worktree removal | `git worktree remove` fails while the path exists | Closure proceeds and nulls `worktreePath`; the phase branch is still asserted clean. **Consequence:** a stale worktree may remain on disk. `[OUT OF SCOPE — quarantine has the identical `check=False` behavior at `scripts/phase-state.py:470`; diverging here would make closure stricter than the failure path it is meant to be gentler than.]` | Reuse the quarantine scenario's precedent |
| Phase-branch integrity | Phase head differs before vs. after | `phaseBranchClean: false` reported to the caller; no repair attempted | Scenario asserting `phaseBranchClean` on both no-lane and mid-run closures |
| State write | Interrupt mid-write | Existing `_atomic_write` temp-file + `os.replace` — prior or next valid state, never torn | Inherited invariant; no new scenario |
| Repeat closure | `close-spec` on an already-closed spec | **Decide in Story 2**: clean no-op returning the existing closure, or explicit `ContractError`. Not `[UNPLANNED]` — the story's DoD requires the choice be made, implemented, and covered | Scenario invoking `close-spec` twice |
| Cascade | A dependent is already `integrated` | Skipped via `TERMINAL_SPEC_STATUSES`; its `mergeCommit` preserved | Scenario with an integrated dependent |

No `[UNPLANNED]` cells remain. The one omission is declared out of scope with its reason.

## Shadow Paths

| Flow | Happy Path | Nil Input | Empty Input | Upstream Error |
|---|---|---|---|---|
| Close a pending spec | `closed_unimplemented` recorded with reason; `progress` shows it counted, `pending` decremented | `--reason` absent → `invalid_closure`, state untouched | `--reason "   "` → `invalid_closure`, state untouched | Phase branch missing → existing `git_error` blocker, no mutation |
| Close a mid-run spec | Worktree gone, lane branch retained, `phaseBranchClean: true` | `--spec` absent → argparse error, exit 2, nothing read | `--spec ""` → `unknown_spec`, no mutation | Worktree already deleted → closure still succeeds, `worktreePath` nulled |
| Read progress on a closed phase | `closed_unimplemented: N`, `pending: 0`, `current: null` | Missing state file → `missing_state` blocker | Empty `specs` object → all counts 0, `current: null` | Unrecognized status on disk → counted under its own key, exit 0 |
| Reconcile a closed phase | `consistent`, `attention: false` | — | — | Retained lane branch deleted → named mismatch, no git mutation |

## Interaction Edge Cases

| Edge Case | Planned Handling |
|---|---|
| Repeat invocation (double close) | Decided and implemented in Story 2; covered by scenario either way |
| Rapid repeat / concurrent close of two specs in one phase | Each invocation is a separate process doing load → mutate → atomic write. Last writer wins on the shared file. `[OUT OF SCOPE — the reducer has never held a lock; `/implement-phase` drives it sequentially, and adding locking here would be a change to every subcommand, not to closure.]` |
| Stale state — closing a spec whose lane was manually deleted | Worktree removal is `check=False`; `reconcile` afterwards reports the missing retained branch rather than silently agreeing |
| Closing every spec in a phase | Valid. `progress` reports `pending: 0` and `current: null`; the phase report says COMPLETE with a mandatory "Closed by decision" section (BR-6) |
| Closing a spec that is `quarantined` or `failed` | Permitted by the vocabulary but semantically muddy — a failed spec has a preserved quarantine branch that closure would not clean up. Story 2 must cover the interaction with a scenario and record the chosen behavior |
| Cascade depth > 1 | `_transitive_dependents` already walks transitively; scenario asserts all levels blocked |

## Eval Design

`scripts/eval-phase-closure.py` follows `scripts/eval-phase-health.py`: module docstring
naming the invariants, `emit(name, ok, detail)`, `helper(*args) -> (rc, payload)`,
`new_repo(tmp)` for disposable git fixtures, PASS/FAIL TSV on stdout only, non-zero exit
on any failure.

`check_phase_closure()` in `scripts/eval.sh` mirrors `check_phase_health()`
(`scripts/eval.sh:2369`): run the scenario file, tally PASS/FAIL into
`CURRENT_SCENARIOS`, `add_finding` per FAIL, then `require_literal` static assertions.

Built incrementally so the check is green after every story:

| Story | Adds |
|---|---|
| 1 | The file, the `CHECKS` entry, `check_phase_closure()`, vocabulary + enforcement + read-tolerance scenarios |
| 2 | `close-spec` scenarios (reason gate, lane disposition, cascade, reconcile) |
| 3 | `require_literal` assertions against reducer, schema doc, `implement-phase`, `status.md` |
| 4 | Nothing — Story 4 runs the real subcommand against live state |

Eval scripts are excluded from the install surface by `is_shippable_script`
(`scripts/install.sh:726`, `eval-*` pattern). No manifest registration.

## Compatibility

- **`schemaVersion` stays `2`.** New permitted status values and an additive `closure`
  object are minor-compatible; `_atomic_write` already preserves unknown fields.
- **Older reducers reading a closed spec:** `cmd_progress`'s
  `counts.get(status, 0) + 1` accumulation already tolerates an unrecognized status, so
  a pre-change reducer reports `closed_unimplemented` under its own key rather than
  crashing. No migration path is needed in either direction.
- **`phase-spec-result-v1` unchanged.** `RESULT_STATUSES` gains nothing. Closure is an
  orchestrator decision; a subagent has no vocabulary for "do not build this" and must
  not acquire one (BR-9).
- **Existing state files stay valid.** `phase-execution-20260719-121255.json` and
  `phase-execution-20260811-2030.json` contain no closed specs and are unaffected;
  only `phase-execution-20260812-0200.json` is corrected, by Story 4.

## Regression Surface

The reducer is shared by five existing eval checks. Every story's verification step runs
all of them:

```
bash scripts/eval.sh --check=phase-lanes
bash scripts/eval.sh --check=phase-challenges
bash scripts/eval.sh --check=phase-quarantine
bash scripts/eval.sh --check=phase-knowledge
bash scripts/eval.sh --check=phase-health
```

Story 3 additionally touches files read by `length`, `leanness`, `broken-refs`,
`required-sections`, `loop-bounds`, and `autonomy-governance` — it runs the full
`bash scripts/eval.sh`.
