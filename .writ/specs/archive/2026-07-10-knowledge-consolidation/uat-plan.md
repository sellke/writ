# UAT Plan: Knowledge Consolidation

> **Generated:** 2026-07-10
> **Spec:** `.writ/specs/2026-07-10-knowledge-consolidation/`
> **Stories Covered:** 3 of 3 completed
> **Total Scenarios:** 19

## How to Use This Plan

1. Work through scenarios in order (they're grouped by story, ordered by priority)
2. For each scenario, follow the steps exactly as written
3. Mark Pass or Fail — add notes for any unexpected behavior
4. Scenarios marked Fail should be filed as issues or fed back to the spec
5. A feature passes UAT when all scenarios pass (or failures are accepted as known limitations)

All commands assume the repository root `/Users/Adam/Projects/writ` as the working directory. The reducer defaults to `--dry-run` (writes nothing); only an explicit `--apply` after approval mutates files. Read exit codes with `echo $?`.

> **Known status carried from Story 3:** the consolidation *mechanism* is complete and proven by fixtures (11/11 scenarios). The roadmap's real-entry criterion (Success Criterion 8) is intentionally pending — the current 7 real ledger entries yield an honest no-op, and no real entries were force-merged. Scenario 19 validates that honest outcome rather than a forced merge.

## Coverage Summary

| Story | Status | Scenarios | Source Breakdown |
|-------|--------|-----------|-----------------|
| Story 1: Consolidation Reducer | ✅ Covered | 7 | AC: 5, Errors: 1, Shadow: 1 |
| Story 2: `/knowledge --consolidate` Command Mode | ✅ Covered | 6 | AC: 5, Shadow: 1 |
| Story 3: Eval, `/retro` Hook, and Docs | ✅ Covered | 6 | AC: 5, Experience: 1 |

---

## Story 1: Consolidation Reducer

### Scenario 1: A duplicate pair produces one merge proposal with a preview diff and no write

**Source:** Acceptance Criteria — Story 1

**Preconditions:**
- Repository checked out at `/Users/Adam/Projects/writ`
- Build a throwaway fixture ledger directory (e.g., `/tmp/uat-kc/knowledge/lessons/`) containing two entries in the same category with high token overlap (a genuine duplicate pair), each with valid frontmatter.

**Steps:**
1. Run the reducer in dry-run against the fixture ledger, e.g. `python3 scripts/knowledge-consolidate.py --dry-run` pointed at the fixture (or run `python3 scripts/eval-knowledge-consolidate.py`, whose fixtures include this case).
2. Inspect the proposal output and the preview diff.
3. Confirm the fixture files are byte-identical before and after (no write occurred).

**Expected Result:**
- The reducer proposes a single merge into one canonical entry and shows a preview unified diff.
- No file is written in dry-run.

**Status:** [ ] Pass  [ ] Fail

**Implementation Reference:** Story 1 — `scripts/knowledge-consolidate.py` (new), `scripts/eval-knowledge-consolidate.py`

**Notes:**

---

### Scenario 2: Conflicting entries surface as a contradiction with no auto-resolution

**Source:** Acceptance Criteria — Story 1

**Preconditions:**
- Repository checked out at `/Users/Adam/Projects/writ`
- Fixture ledger with two entries that share high subject overlap but assert conflicting facts.

**Steps:**
1. Run the reducer in dry-run against the fixture (or via `python3 scripts/eval-knowledge-consolidate.py`).
2. Inspect the contradiction section of the proposal.

**Expected Result:**
- The pair is surfaced as a contradiction for human review.
- The reducer proposes no resolution and applies no change.

**Status:** [ ] Pass  [ ] Fail

**Implementation Reference:** Story 1 — `scripts/knowledge-consolidate.py` (contradiction surfacing, D5)

**Notes:**

---

### Scenario 3: Stale is flagged on observable signal, not on age

**Source:** Acceptance Criteria — Story 1

**Preconditions:**
- Repository checked out at `/Users/Adam/Projects/writ`
- Fixture ledger with (a) an entry whose `related_artifacts` all point to missing paths, and (b) a merely-old entry whose artifacts still resolve.

**Steps:**
1. Run the reducer in dry-run against the fixture.
2. Inspect the stale-flag section of the proposal.

**Expected Result:**
- The entry with all-dangling `related_artifacts` is flagged stale with the observable signal.
- The merely-old-but-still-referenced entry is NOT flagged.

**Status:** [ ] Pass  [ ] Fail

**Implementation Reference:** Story 1 — `scripts/knowledge-consolidate.py` (stale signals, D6)

**Notes:**

---

### Scenario 4: Apply mode writes bidirectional lineage and tombstones

**Source:** Acceptance Criteria — Story 1

**Preconditions:**
- Repository checked out at `/Users/Adam/Projects/writ`
- A throwaway fixture ledger with an approved duplicate pair (never run apply against the real `.writ/knowledge/`).

**Steps:**
1. Run the reducer with `--apply` against the fixture ledger for the approved merge.
2. Open the surviving canonical entry and each merged-away entry.

**Expected Result:**
- The canonical entry gains `replaces: [superseded-slug, ...]`.
- Each merged-away entry becomes a tombstone whose frontmatter gains `superseded_by: <canonical-slug>` and whose body is a one-line pointer to the canonical entry.
- Every `replaces` slug has a matching `superseded_by` tombstone (bidirectional consistency).

**Status:** [ ] Pass  [ ] Fail

**Implementation Reference:** Story 1 — `scripts/knowledge-consolidate.py` (`--apply`, lineage/tombstones, D4)

**Notes:**

---

### Scenario 5: Clean ledger is a no-op; malformed entry is skipped with a reason

**Source:** Acceptance Criteria — Story 1

**Preconditions:**
- Repository checked out at `/Users/Adam/Projects/writ`
- Fixture A: a clean ledger with no duplicates/contradictions/stale. Fixture B: a ledger containing one entry with malformed frontmatter or a missing section.

**Steps:**
1. Run the reducer in dry-run against Fixture A; confirm no proposal and no file change.
2. Run the reducer in dry-run against Fixture B; inspect how the malformed entry is handled.

**Expected Result:**
- The clean ledger yields a valid no-op with no file written.
- The malformed entry is skipped with a named reason — never silently dropped, crashed on, or rewritten.

**Status:** [ ] Pass  [ ] Fail

**Implementation Reference:** Story 1 — `scripts/knowledge-consolidate.py` (tolerant parsing)

**Notes:**

---

### Scenario 6: Detection is conservative against false positives

**Source:** Error & Rescue Map (Duplicate detection false-positive / Contradiction detection) — Story 1

**Preconditions:**
- Repository checked out at `/Users/Adam/Projects/writ`
- Fixture ledger with two near-topic but genuinely distinct entries that fall below the duplicate threshold, plus an unrelated pair.

**Steps:**
1. Run the reducer in dry-run against the fixture.
2. Confirm the distinct entries below threshold are not proposed for merge.
3. Confirm unrelated entries are not surfaced as a contradiction.

**Expected Result:**
- Below-threshold distinct entries are left alone; unrelated entries are not flagged as contradictions. Every proposed merge would still require human approval against a diff.

**Status:** [ ] Pass  [ ] Fail

**Implementation Reference:** Story 1 — `scripts/knowledge-consolidate.py` (`_tokens` + Jaccard, conservative threshold, D3)

**Notes:**

---

### Scenario 7: Dry-run leaves the ledger byte-identical

**Source:** Shadow Paths (Duplicate detection / Stale flagging) — Story 1

**Preconditions:**
- Repository checked out at `/Users/Adam/Projects/writ`
- Any fixture ledger (duplicate pair present).

**Steps:**
1. Record a checksum/snapshot of the fixture ledger files.
2. Run the reducer in dry-run.
3. Re-check the fixture ledger files against the snapshot.

**Expected Result:**
- The fixture ledger is byte-identical before and after the dry-run (no write occurs without an explicit apply).

**Status:** [ ] Pass  [ ] Fail

**Implementation Reference:** Story 1 — `scripts/knowledge-consolidate.py` (non-destructive default, D2)

**Notes:**

---

## Story 2: `/knowledge --consolidate` Command Mode

### Scenario 8: --consolidate routes to a dry-run and presents proposals

**Source:** Acceptance Criteria — Story 2

**Preconditions:**
- Repository checked out at `/Users/Adam/Projects/writ`

**Steps:**
1. Open `commands/knowledge.md` and find the Step-2 routing.
2. Confirm a `--consolidate` branch exists alongside `--list` / `--read` that runs `scripts/knowledge-consolidate.py --dry-run`.
3. Confirm the mode presents proposed merges, contradiction pairs, and stale flags without writing any file.

**Expected Result:**
- `/knowledge --consolidate` routes to a reducer dry-run and presents merges/contradictions/stale flags, writing nothing.

**Status:** [ ] Pass  [ ] Fail

**Implementation Reference:** Story 2 — `commands/knowledge.md` (Step-2 `--consolidate` branch)

**Notes:**

---

### Scenario 9: Every write is gated on explicit approval

**Source:** Acceptance Criteria — Story 2

**Preconditions:**
- Repository checked out at `/Users/Adam/Projects/writ`

**Steps:**
1. Open `commands/knowledge.md` `--consolidate` flow.
2. Confirm any write is gated on an explicit `AskQuestion` approval.
3. Confirm that declining approval writes nothing and leaves the ledger unchanged.

**Expected Result:**
- The command gates all writes on `AskQuestion`; a declined approval results in no file change.

**Status:** [ ] Pass  [ ] Fail

**Implementation Reference:** Story 2 — `commands/knowledge.md` (approval gate)

**Notes:**

---

### Scenario 10: Approving a merge applies lineage and reports changed files

**Source:** Acceptance Criteria — Story 2

**Preconditions:**
- Repository checked out at `/Users/Adam/Projects/writ`

**Steps:**
1. Open `commands/knowledge.md` and confirm that, on approval, it invokes the reducer's apply mode.
2. Confirm the applied merge records `replaces` on the canonical entry and `superseded_by` on each tombstone.
3. Confirm the command reports the exact files changed and the lineage recorded, leaving a reviewable working-tree diff (it does not commit).

**Expected Result:**
- On approval, the command applies the merge with bidirectional lineage and reports the changed files, leaving a reviewable diff.

**Status:** [ ] Pass  [ ] Fail

**Implementation Reference:** Story 2 — `commands/knowledge.md` (approved-apply path)

**Notes:**

---

### Scenario 11: Contradictions are presented as decisions, never auto-resolved

**Source:** Acceptance Criteria — Story 2

**Preconditions:**
- Repository checked out at `/Users/Adam/Projects/writ`

**Steps:**
1. Open `commands/knowledge.md` `--consolidate` flow.
2. Confirm surfaced contradiction pairs are presented for a human decision.
3. Confirm the command never applies an automatic contradiction resolution.

**Expected Result:**
- Contradiction pairs are presented as decisions; no automatic resolution is applied.

**Status:** [ ] Pass  [ ] Fail

**Implementation Reference:** Story 2 — `commands/knowledge.md`, `scripts/knowledge-consolidate.py`

**Notes:**

---

### Scenario 12: README documents lineage frontmatter and the workflow

**Source:** Acceptance Criteria — Story 2

**Preconditions:**
- Repository checked out at `/Users/Adam/Projects/writ`

**Steps:**
1. Open `.writ/knowledge/README.md`.
2. Confirm it documents the lineage frontmatter fields (`superseded_by` / `replaces`) and their usage.
3. Confirm it documents the consolidation workflow (merge-never-append, dry-run → approval → apply → reviewable diff).

**Expected Result:**
- The README documents lineage frontmatter and the consolidation workflow consistently with the shipped command behavior.

**Status:** [ ] Pass  [ ] Fail

**Implementation Reference:** Story 2 — `.writ/knowledge/README.md`

**Notes:**

---

### Scenario 13: Command routing degrades gracefully with no ledger / nothing to consolidate

**Source:** Shadow Paths (Command routing) — Story 2

**Preconditions:**
- Repository checked out at `/Users/Adam/Projects/writ`

**Steps:**
1. Open `commands/knowledge.md` and confirm the documented handling when `.writ/` is absent: reuse the existing `/knowledge` guard (instruct to run `/initialize`) and write nothing.
2. Confirm the documented handling when there is nothing to consolidate: report a no-op and write no file.
3. Confirm the Completion section keeps the terminal constraint (produces knowledge docs and diffs only; does not offer to implement).

**Expected Result:**
- Missing `.writ/` triggers the initialize guard; a clean ledger reports a no-op; the terminal constraint is preserved.

**Status:** [ ] Pass  [ ] Fail

**Implementation Reference:** Story 2 — `commands/knowledge.md` (guards + Completion)

**Notes:**

---

## Story 3: Eval, `/retro` Hook, and Docs

### Scenario 14: The eval script covers all six scenario types

**Source:** Acceptance Criteria — Story 3

**Preconditions:**
- Repository checked out at `/Users/Adam/Projects/writ`
- Python 3 available on PATH

**Steps:**
1. Run: `python3 scripts/eval-knowledge-consolidate.py` and read the PASS/FAIL TSV output and `echo $?`.
2. Confirm scenarios cover: duplicate merge proposed, contradiction surfaced, stale flagged, non-destructive default (no file written in dry-run), lineage preserved (`replaces` + `superseded_by`), and clean-ledger no-op.

**Expected Result:**
- All six scenario families emit `PASS` (the shipped suite reports 11/11 scenarios), and the script exits `0`.

**Status:** [ ] Pass  [ ] Fail

**Implementation Reference:** Story 3 — `scripts/eval-knowledge-consolidate.py` (new)

**Notes:**

---

### Scenario 15: The check is registered by a single CHECKS append and runs by name

**Source:** Acceptance Criteria — Story 3

**Preconditions:**
- Repository checked out at `/Users/Adam/Projects/writ`

**Steps:**
1. Open `scripts/eval.sh` and confirm a `check_knowledge_consolidate` function plus exactly one appended `knowledge-consolidate` line in the `CHECKS` array (no reordering of existing entries).
2. Run: `bash scripts/eval.sh --check=knowledge-consolidate` and read `echo $?`.

**Expected Result:**
- The check runs the scenario harness plus `require_literal` static assertions (on the reducer, `commands/knowledge.md`, `commands/retro.md`, and `.writ/knowledge/README.md`) and exits `0`.

**Status:** [ ] Pass  [ ] Fail

**Implementation Reference:** Story 3 — `scripts/eval.sh` (`check_knowledge_consolidate` + `CHECKS` entry)

**Notes:**

---

### Scenario 16: /retro nudges toward consolidation on a growth signal without mutating

**Source:** Acceptance Criteria — Story 3

**Preconditions:**
- Repository checked out at `/Users/Adam/Projects/writ`

**Steps:**
1. Open `commands/retro.md` and find the read-only consolidation hook.
2. Confirm that, when a ledger growth signal is present, it prints a read-only nudge suggesting `/knowledge --consolidate`.
3. Confirm the hook mutates no knowledge file.

**Expected Result:**
- On a growth signal, `/retro` prints a read-only nudge and changes no knowledge file.

**Status:** [ ] Pass  [ ] Fail

**Implementation Reference:** Story 3 — `commands/retro.md` (advisory hook, D9)

**Notes:**

---

### Scenario 17: /retro skips gracefully with no signal or no ledger

**Source:** Acceptance Criteria — Story 3

**Preconditions:**
- Repository checked out at `/Users/Adam/Projects/writ`

**Steps:**
1. Open `commands/retro.md` consolidation hook.
2. Confirm that with no growth signal, or when `.writ/knowledge/` is absent or empty, the hook skips gracefully with no nudge and no error.

**Expected Result:**
- No-signal / absent-ledger cases skip cleanly with no nudge and no error.

**Status:** [ ] Pass  [ ] Fail

**Implementation Reference:** Story 3 — `commands/retro.md`

**Notes:**

---

### Scenario 18: Docs read consistently across surfaces

**Source:** Acceptance Criteria — Story 3

**Preconditions:**
- Repository checked out at `/Users/Adam/Projects/writ`

**Steps:**
1. Open `.writ/knowledge/README.md`.
2. Confirm the lineage frontmatter usage and the consolidation workflow (merge-never-append, non-destructive default) read consistently with the shipped `/knowledge --consolidate` behavior and the `/retro` nudge.

**Expected Result:**
- The finalized docs describe the lineage frontmatter and workflow consistently with the shipped command behavior.

**Status:** [ ] Pass  [ ] Fail

**Implementation Reference:** Story 3 — `.writ/knowledge/README.md`

**Notes:**

---

### Scenario 19: Real-ledger dry-run is an honest no-op (roadmap criterion pending)

**Source:** Experience Design / Interaction Edge Cases (real ledger has no duplicates yet) — Story 3

**Preconditions:**
- Repository checked out at `/Users/Adam/Projects/writ`

**Steps:**
1. Run: `python3 scripts/knowledge-consolidate.py --dry-run` against the real `.writ/knowledge/` ledger.
2. Inspect the proposal output.
3. Confirm the real ledger is unchanged (dry-run writes nothing).

**Expected Result:**
- The dry-run runs cleanly and reports an honest no-op against the current real entries (no genuine duplicate/contradiction/stale exists).
- No file is written. This confirms the documented pending status of the roadmap real-entry criterion — no entries were force-merged.

**Status:** [ ] Pass  [ ] Fail

**Implementation Reference:** Story 3 — `scripts/knowledge-consolidate.py`; honest-status note in `story-3-eval-retro-hook-and-docs.md`

**Notes:**

---
