# Phase Closure Status (Lite)

> Source: .writ/specs/2026-08-12-phase-closure-status/spec.md
> Purpose: Efficient AI context for implementation

## For Coding Agents

**Deliverable:** `phase-execution-v2` gains an enforced spec-status vocabulary with a
terminal `closed_unimplemented`, a `close-spec` reducer subcommand, and honest
reporting through `progress`, `/status`, and the phase report.

**Implementation Approach:**
- `SPEC_STATUSES` is dead code today (declared, referenced nowhere). Make it
  load-bearing via one `_set_status(record, value)` guard used at every mutation site.
- Add BOTH `closed_unimplemented` and `challenge_required` — the latter is already
  written by `cmd_record_challenge` and would fail new enforcement.
- `cmd_close_spec` mirrors `cmd_quarantine` minus the branch rename.
- `cmd_progress` seeds counts from `SPEC_STATUSES`; keeps `counts.get(...)` fallback.
- Eval built incrementally: `phase-closure` check green after EACH story.

**Files in Scope:**
- `scripts/phase-state.py` — statuses, `_set_status`, `cmd_close_spec`, progress, reconcile
- `scripts/eval-phase-closure.py` — new scenario file (PASS/FAIL TSV)
- `scripts/eval.sh` — `phase-closure` in CHECKS + `check_phase_closure()`
- `.writ/docs/phase-execution-state-format.md` — schema contract
- `commands/implement-phase.md` — exit criterion 1, Step 1.2b, Step 3.3, report section
- `commands/status.md` Step 4 — count list

**Error Handling:**
- Status outside the set → `ContractError("invalid_status")`
- Empty/whitespace `--reason` → `ContractError("invalid_closure")`
- Unknown spec id → existing `unknown_spec`

**Integration Points:** `/implement-phase` writes it; `/status` reads it.

---

## For Review Agents

**Acceptance Criteria:**
1. `close-spec` writes `closed_unimplemented` + `closure{reason,closedAt}`; `progress`
   counts it separately and reports `0` when absent.
2. Mid-run closure removes worktree, RETAINS `laneBranch`, phase head byte-identical.
3. Dependents → `skipped_blocked` with closed spec in `blockedBy`, cause = closure.
4. `reconcile` returns `consistent` with closed specs; `health` shows no closure-caused
   `Attention`.
5. Invalid status write raises; invalid status READ still reports.
6. `bash scripts/eval.sh --check=phase-closure` green after each story.

**Business Rules:**
- `closed_unimplemented` is terminal — no recovery path, distinct from failed/blocked.
- Reason is REQUIRED and non-empty (the phase report must print it).
- Cascade widens `blockedBy` to "upstream terminal without delivering" — must be
  documented, and `progress` must distinguish quarantine-cause from closure-cause.
- Health never counts spec statuses; keep it that way.
- Phase reports COMPLETE with closed specs, but MUST list each + reason.
- `schemaVersion` stays 2. `phase-spec-result-v1` unchanged.

**Experience Design:**
- Entry: `/implement-phase` closes a spec; or `/status` on a phase with closed specs
- Happy path: close → `progress` shows `closed_unimplemented: N`, `pending: 0`
- Moment of truth: `/status` stops reporting a finished phase as work in flight
- Feedback: phase report's "Closed by decision" section names each spec + reason
- Error: an unexplained or unknown-status write is refused, never silently accepted

---

## For Testing Agents

**Success Criteria:**
1. Every `record["status"] = ...` site routed through `_set_status` (grep proves zero
   direct assignments remain)
2. `phase-closure` eval check exists and passes
3. Existing checks stay green: `phase-lanes`, `phase-challenges`, `phase-quarantine`,
   `phase-knowledge`, `phase-health`

**Shadow Paths to Verify:**
- **Nil input:** `--reason` omitted → `invalid_closure`, no state mutation
- **Empty input:** `--reason "   "` → `invalid_closure`, no state mutation
- **Unknown status on read:** hand-written state with `status: "future_value"` →
  `progress` still reports, counts it under its own key
- **Upstream error:** worktree path recorded but already gone → close still succeeds

**Edge Cases:**
- Close a spec with no lane (`pending`) → no git operation at all
- Close a spec already `closed_unimplemented` → idempotent or explicit refusal, decided
  and tested
- Close a spec whose dependents are already `integrated` → do NOT downgrade them
- Transitive cascade depth > 1 → all levels blocked

**Coverage Requirements:**
- New code: ≥80% | Critical paths: 100% | Error paths: 100%

**Test Strategy:** Disposable-git-repo scenarios in `eval-phase-closure.py` emitting
PASS/FAIL TSV, per the `eval-phase-quarantine.py` pattern.
