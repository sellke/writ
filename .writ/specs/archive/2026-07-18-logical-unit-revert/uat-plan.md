# UAT Plan: Logical-Unit Revert (`/revert`)

> **Generated:** 2026-07-19
> **Spec:** `.writ/specs/2026-07-18-logical-unit-revert/`
> **Stories Covered:** 4 of 4 completed
> **Total Scenarios:** 19

## How to Use This Plan

1. Work through scenarios in order (grouped by story).
2. Follow the steps exactly; mark Pass or Fail; add notes for anything unexpected.
3. Failures should be filed as issues or fed back to the spec.
4. The feature passes UAT when all scenarios pass (or failures are accepted as known limitations).

> **Safety note:** `/revert` mutates git history. Run any live-mutation scenario on a **throwaway clone or scratch branch**, never on protected history. The resolver (`revert-resolve.py`) is read-only and safe to run anywhere.

## Coverage Summary

| Story | Status | Scenarios | Source Breakdown |
|-------|--------|-----------|------------------|
| Story 1: Record story commit SHA | ✅ Covered | 3 | AC: 3 |
| Story 2: Commit resolver (`revert-resolve.py`) | ✅ Covered | 5 | AC: 5 |
| Story 3: `/revert` command | ✅ Covered | 7 | AC: 6, Error: 1 |
| Story 4: Artifact restoration + eval | ✅ Covered | 4 | AC: 4 |

---

## Story 1: Record Story Commit SHA

### Scenario 1: Story completion records its commit SHA

**Source:** Acceptance Criteria — Story 1

**Preconditions:**
- A spec with an in-progress story, run through `/implement-story` to Step 4 (completion commit) on a scratch project.

**Steps:**
1. Complete a story via `/implement-story`.
2. Open the completed story file header.

**Expected Result:**
- The header gained `> **Commit:** <full-sha>` matching `git rev-parse HEAD` of the completion commit.

**Status:** [ ] Pass  [ ] Fail

**Implementation Reference:** Story 1 — Files: `commands/implement-story.md` (Step 4)

**Notes:**

---

### Scenario 2: Re-running a story updates the SHA idempotently

**Source:** Acceptance Criteria — Story 1

**Preconditions:**
- A story that already has a `> **Commit:**` field.

**Steps:**
1. Re-implement/re-commit the story via `/implement-story`.
2. Inspect the header.

**Expected Result:**
- The `Commit:` field is updated to the new SHA — not duplicated (single field remains).

**Status:** [ ] Pass  [ ] Fail

**Notes:**

---

### Scenario 3: Legacy story without the field is tolerated

**Source:** Acceptance Criteria — Story 1 (backward-compat)

**Preconditions:**
- A story file with no `> **Commit:**` field.

**Steps:**
1. Run `python3 scripts/revert-resolve.py story <id> --json` against it.

**Expected Result:**
- Resolution does not error on the missing field; it falls back to later resolver layers (ref-footer / phase-state / ghost).

**Status:** [ ] Pass  [ ] Fail

**Notes:**

---

## Story 2: Commit Resolver (`revert-resolve.py`)

### Scenario 4: Recorded SHA present in history resolves exact

**Source:** Acceptance Criteria — Story 2

**Preconditions:**
- A story with a recorded `> **Commit:**` SHA that exists in history.

**Steps:**
1. Run `python3 scripts/revert-resolve.py story <id> --json`.

**Expected Result:**
- Output includes that commit with `"source": "recorded"` and `"confidence": "exact"`.

**Status:** [ ] Pass  [ ] Fail

**Implementation Reference:** Story 2 — Files: `scripts/revert-resolve.py`

**Notes:**

---

### Scenario 5: Ship `Ref:` footer resolves when no recorded SHA

**Source:** Acceptance Criteria — Story 2

**Preconditions:**
- Shipped work whose commit carries a `Ref: <id>` footer; no recorded SHA in the story.

**Steps:**
1. Run the resolver for the unit.

**Expected Result:**
- Commits are found via the `Ref:` footer with `"source": "ref-footer"`.

**Status:** [ ] Pass  [ ] Fail

**Notes:**

---

### Scenario 6: Rewritten SHA emits a ghost candidate (never auto-selected)

**Source:** Acceptance Criteria — Story 2

**Preconditions:**
- A recorded SHA that is absent from history (simulate a rebase/squash that rewrote it).

**Steps:**
1. Run the resolver.
2. Inspect the `ghost` array in the output.

**Expected Result:**
- A `ghost` entry lists the recorded SHA, a top message-similarity `candidate`, and a `similarity` score.
- The candidate is NOT placed in `commits` (not auto-selected) — it awaits confirmation.

**Status:** [ ] Pass  [ ] Fail

**Notes:**

---

### Scenario 7: Spec unit returns the union + scaffolding commit

**Source:** Acceptance Criteria — Story 2

**Preconditions:**
- A spec with multiple completed stories.

**Steps:**
1. Run `python3 scripts/revert-resolve.py spec <folder-id> --json`.

**Expected Result:**
- Output is the union of all story commits plus the spec-scaffolding commit (the one that added `spec.md`), ordered newest→oldest, deduped.

**Status:** [ ] Pass  [ ] Fail

**Notes:**

---

### Scenario 8: Base computation and duplicate warnings

**Source:** Acceptance Criteria — Story 2

**Preconditions:**
- Any resolvable unit.

**Steps:**
1. Run the resolver and inspect `base` and `warnings`.

**Expected Result:**
- `base` = parent of the earliest resolved commit.
- Merge commits / cherry-pick duplicates produce entries in `warnings`.

**Status:** [ ] Pass  [ ] Fail

**Notes:**

---

## Story 3: `/revert` Command

### Scenario 9: Guided menu when no target given

**Source:** Acceptance Criteria — Story 3

**Preconditions:**
- A project with in-progress and recently completed units.

**Steps:**
1. Run `/revert` with no argument.

**Expected Result:**
- A guided menu shows in-progress units first, then recent completed, max ~4 options, plus "Other".

**Status:** [ ] Pass  [ ] Fail

**Implementation Reference:** Story 3 — Files: `commands/revert.md`

**Notes:**

---

### Scenario 10: Plan presented before any mutation

**Source:** Acceptance Criteria — Story 3

**Preconditions:**
- Clean working tree; a resolvable unit.

**Steps:**
1. Run `/revert story-<n>` (or `/revert spec <id>`).

**Expected Result:**
- Before any git-mutating command, a plan shows commit SHAs + subjects, strategy choices, and the Writ artifacts that will be reset.

**Status:** [ ] Pass  [ ] Fail

**Notes:**

---

### Scenario 11: Ghost substitution requires explicit confirmation

**Source:** Acceptance Criteria — Story 3

**Preconditions:**
- A unit that resolves with a ghost candidate.

**Steps:**
1. Run `/revert` for that unit.

**Expected Result:**
- Each ghost substitution is presented and requires explicit confirmation before use.

**Status:** [ ] Pass  [ ] Fail

**Notes:**

---

### Scenario 12: Dirty tree halts before any git op

**Source:** Acceptance Criteria — Story 3

**Preconditions:**
- Working tree with uncommitted changes (`git status --porcelain` non-empty).

**Steps:**
1. Run `/revert <unit>`.

**Expected Result:**
- The command halts at the plan gate with "commit or stash before reverting"; no git operation runs.

**Status:** [ ] Pass  [ ] Fail

**Notes:**

---

### Scenario 13: Safe strategy reverts newest→oldest

**Source:** Acceptance Criteria — Story 3

**Preconditions:**
- Clean tree; resolvable multi-commit unit.

**Steps:**
1. Run `/revert <unit>`, confirm plan, choose Safe (Recommended).

**Expected Result:**
- `git revert --no-edit` runs for each commit newest→oldest; history is preserved via new revert commits.

**Status:** [ ] Pass  [ ] Fail

**Notes:**

---

### Scenario 14: Revert conflict halts with guidance

**Source:** Error Experience — Story 3

**Preconditions:**
- A unit whose revert will conflict with later changes.

**Steps:**
1. Run a safe `/revert` that conflicts.

**Expected Result:**
- The command halts with clear manual-resolution instructions and leaves the repo mid-revert for the user.

**Status:** [ ] Pass  [ ] Fail

**Notes:**

---

### Scenario 15: Hard reset requires a second destructive confirmation

**Source:** Acceptance Criteria — Story 3

**Preconditions:**
- Clean tree; resolvable unit.

**Steps:**
1. Run `/revert <unit>`, choose Hard reset (destructive).

**Expected Result:**
- A second destructive confirmation naming the base SHA (and warning about lost work) is required before `git reset --hard <base>` runs.

**Status:** [ ] Pass  [ ] Fail

**Notes:**

---

## Story 4: Artifact Restoration + Eval

### Scenario 16: Story revert restores all Writ artifacts

**Source:** Acceptance Criteria — Story 4

**Preconditions:**
- A successfully reverted story.

**Steps:**
1. After the revert, inspect the story file, `drift-log.md`, and `context.md`.

**Expected Result:**
- Story status → `Not Started`; tasks/AC unchecked; `## What Was Built` prefixed with a `> **Reverted:**` banner (record preserved, not deleted); a revert entry appended to `drift-log.md`; `context.md` regenerated.

**Status:** [ ] Pass  [ ] Fail

**Implementation Reference:** Story 4 — Files: `commands/revert.md`, `.writ/docs/what-was-built-format.md`

**Notes:**

---

### Scenario 17: Spec revert applies restoration across all stories

**Source:** Acceptance Criteria — Story 4

**Preconditions:**
- A reverted spec unit.

**Steps:**
1. Inspect all the spec's story files and spec status.

**Expected Result:**
- Restoration is applied across every story; spec status is reset appropriately.

**Status:** [ ] Pass  [ ] Fail

**Notes:**

---

### Scenario 18: Reverted WWB is non-authoritative downstream

**Source:** Acceptance Criteria — Story 4

**Preconditions:**
- A story with a reverted (banner-annotated) WWB record that a later story depends on.

**Steps:**
1. Run `/implement-story` for the downstream story and observe dependency-context loading.

**Expected Result:**
- The reverted WWB record is treated as non-authoritative (skipped or flagged), per the documented convention.

**Status:** [ ] Pass  [ ] Fail

**Notes:**

---

### Scenario 19: Eval asserts guards and resolver tests pass

**Source:** Acceptance Criteria — Story 4

**Preconditions:**
- Repo checked out.

**Steps:**
1. Run `bash scripts/eval.sh --check=revert` (or the full suite).

**Expected Result:**
- The check passes: `revert.md` references the dirty-tree guard, plan-before-mutate gate, and hard-reset second confirmation; the `revert-resolve.py` unit tests pass (≥80% coverage — measured 90%).

**Status:** [ ] Pass  [ ] Fail

**Implementation Reference:** Story 4 — Files: `scripts/eval-revert-resolve.py`, `scripts/tests/test_revert_resolve.py`, `scripts/eval.sh`

**Notes:**

---

## Pending Stories

None — all four stories are complete.
