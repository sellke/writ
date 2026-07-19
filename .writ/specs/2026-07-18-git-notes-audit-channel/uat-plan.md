# UAT Plan: Git-Notes Audit Channel

> **Generated:** 2026-07-19
> **Spec:** `.writ/specs/2026-07-18-git-notes-audit-channel/`
> **Stories Covered:** 4 of 4 completed
> **Total Scenarios:** 18

## How to Use This Plan

1. Work through scenarios in order (grouped by story, ordered by priority).
2. For each scenario, follow the steps exactly as written.
3. Mark Pass or Fail — add notes for any unexpected behavior.
4. Scenarios marked Fail should be filed as issues or fed back to the spec.
5. The feature passes UAT when all scenarios pass (or failures are accepted as known limitations).

> **Note on this methodology repo:** Deliverables are markdown/scripts, so several scenarios are validated by reading a command file or running a script rather than exercising a live UI. Where a scenario requires a real `/ship` or `/release`, use a throwaway spec/branch on a scratch clone so you do not pollute this repo's history.

## Coverage Summary

| Story | Status | Scenarios | Source Breakdown |
|-------|--------|-----------|------------------|
| Story 1: Audit digest format + ADR-017 | ✅ Covered | 3 | AC: 3 |
| Story 2: `/ship` integration — spec digest | ✅ Covered | 6 | AC: 5, Error: 1 |
| Story 3: `/release` integration — version rollup | ✅ Covered | 4 | AC: 4 |
| Story 4: Sync config + opt-out + `/status` + eval | ✅ Covered | 5 | AC: 5 |

---

## Story 1: Audit Digest Format + ADR-017

### Scenario 1: Format doc fully specifies the audit contract

**Source:** Acceptance Criteria — Story 1

**Preconditions:**
- Repo checked out on the phase branch.

**Steps:**
1. Open `.writ/docs/git-notes-audit-format.md`.
2. Confirm it contains the spec-level digest schema, the version rollup schema, the `refs/notes/writ` ref convention, and read/sync/opt-out instructions.

**Expected Result:**
- All four elements are present and internally consistent.
- A field-provenance table maps every digest field to a WWB source field or a git-derived value.

**Status:** [ ] Pass  [ ] Fail

**Implementation Reference:** Story 1 — Files: `.writ/docs/git-notes-audit-format.md`

**Notes:**

---

### Scenario 2: ADR-017 records the decision and rationale

**Source:** Acceptance Criteria — Story 1

**Preconditions:**
- None.

**Steps:**
1. Open `.writ/decision-records/adr-017-git-notes-audit-channel.md`.
2. Confirm it records the decision, the squash-survival rationale (attach post-land, not per-story), the audit-only content constraint (no transcripts/CoT), and the WWB-vs-notes boundary.

**Expected Result:**
- ADR follows the house format and covers all four points, plus considered alternatives.

**Status:** [ ] Pass  [ ] Fail

**Implementation Reference:** Story 1 — Files: `.writ/decision-records/adr-017-git-notes-audit-channel.md`

**Notes:**

---

### Scenario 3: No orphan fields across Stories 2–4

**Source:** Acceptance Criteria — Story 1

**Preconditions:**
- None.

**Steps:**
1. Read the digest fields emitted by `commands/ship.md` (Step 6) and `commands/release.md` (Audit Rollup).
2. For each field, find its definition in `.writ/docs/git-notes-audit-format.md`.

**Expected Result:**
- Every field emitted by ship/release is defined in the format doc; none are undocumented.

**Status:** [ ] Pass  [ ] Fail

**Notes:**

---

## Story 2: `/ship` Integration — Spec Digest

### Scenario 4: Digest attaches to the landed commit

**Source:** Acceptance Criteria — Story 2

**Preconditions:**
- A scratch clone with a spec whose stories have `## What Was Built` records.
- `writ.auditNotes` unset or `true`.

**Steps:**
1. Run `/ship` for the spec and let the branch land on the base branch.
2. Run `git log --notes=writ` on the base branch.

**Expected Result:**
- The spec-level digest appears inline under the landed commit.
- `/ship` printed `📝 Audit note attached to <sha> (refs/notes/writ)`.

**Status:** [ ] Pass  [ ] Fail

**Implementation Reference:** Story 2 — Files: `commands/ship.md` (Step 6)

**Notes:**

---

### Scenario 5: Squash-merge attaches to the surviving commit

**Source:** Acceptance Criteria — Story 2

**Preconditions:**
- A spec shipped via squash-merge (produces a new SHA).

**Steps:**
1. Ship the spec with a squash-merge.
2. Inspect `refs/notes/writ` with `git notes --ref=writ list`.

**Expected Result:**
- The note is on the squash commit that landed on the base branch — never on an orphaned pre-merge story commit.

**Status:** [ ] Pass  [ ] Fail

**Notes:**

---

### Scenario 6: Minimal digest when no WWB records exist

**Source:** Acceptance Criteria — Story 2

**Preconditions:**
- A spec/branch with no `## What Was Built` records (e.g., manual work).

**Steps:**
1. Run `/ship`.
2. Read the attached note via `git notes --ref=writ show <landed-sha>`.

**Expected Result:**
- A minimal digest (spec ref + landed SHA + `git diff --stat`) is attached.
- A warning noting the missing WWB records was logged; ship still succeeded.

**Status:** [ ] Pass  [ ] Fail

**Notes:**

---

### Scenario 7: Note attachment failure never blocks the ship

**Source:** Error Map — Story 2

**Preconditions:**
- A condition that makes `git notes add` fail (e.g., simulate by making the notes ref unwritable).

**Steps:**
1. Run `/ship`.

**Expected Result:**
- The ship completes successfully.
- A `⚠️ audit note not attached — {error}` warning is shown; no exception aborts the flow.

**Status:** [ ] Pass  [ ] Fail

**Notes:**

---

### Scenario 8: Opt-out suppresses note composition

**Source:** Acceptance Criteria — Story 2

**Preconditions:**
- `git config writ.auditNotes false` set in the repo.

**Steps:**
1. Run `/ship`.
2. Check `git log --notes=writ` for the landed commit.

**Expected Result:**
- No note is composed or attached (silent no-op).

**Status:** [ ] Pass  [ ] Fail

**Notes:**

---

### Scenario 9: Re-ship overwrites the note on the same SHA

**Source:** Acceptance Criteria — Story 2 (overwrite rule)

**Preconditions:**
- A spec already shipped with a note on its landed commit.

**Steps:**
1. Re-run `/ship` targeting the same landed commit.
2. Inspect the note.

**Expected Result:**
- The note is overwritten (`add -f`), not duplicated; a single up-to-date digest remains.

**Status:** [ ] Pass  [ ] Fail

**Notes:**

---

## Story 3: `/release` Integration — Version Rollup

### Scenario 10: Version rollup attaches to the tag target

**Source:** Acceptance Criteria — Story 3

**Preconditions:**
- A scratch clone with completed specs since the previous release tag.

**Steps:**
1. Run `/release` and let it tag the release commit.
2. Run `git notes --ref=writ show $(git rev-list -n 1 v<version>)`.

**Expected Result:**
- The version rollup note (version, date, list of shipped specs + aggregate verdicts, changelog ref) is attached to the tag's target commit.

**Status:** [ ] Pass  [ ] Fail

**Implementation Reference:** Story 3 — Files: `commands/release.md` (Step 4.4)

**Notes:**

---

### Scenario 11: Rollup reuses the changelog spec list

**Source:** Acceptance Criteria — Story 3

**Preconditions:**
- None (static review acceptable).

**Steps:**
1. Read the Audit Rollup step in `commands/release.md`.

**Expected Result:**
- The rollup body is built from the existing changelog-from-completed-specs list (no re-scan), and references per-spec digests rather than duplicating them.

**Status:** [ ] Pass  [ ] Fail

**Notes:**

---

### Scenario 12: Release rollup failure is non-blocking

**Source:** Acceptance Criteria — Story 3

**Preconditions:**
- A condition making the rollup note attachment fail.

**Steps:**
1. Run `/release`.

**Expected Result:**
- The release completes; a warning is shown; no abort.

**Status:** [ ] Pass  [ ] Fail

**Notes:**

---

### Scenario 13: Opt-out suppresses the rollup

**Source:** Acceptance Criteria — Story 3

**Preconditions:**
- `git config writ.auditNotes false`.

**Steps:**
1. Run `/release`.
2. Check the tag target for a Writ note.

**Expected Result:**
- No rollup note is attached (silent).

**Status:** [ ] Pass  [ ] Fail

**Notes:**

---

## Story 4: Sync Config + Opt-Out + `/status` + Eval

### Scenario 14: install.sh adds notes refspecs idempotently

**Source:** Acceptance Criteria — Story 4

**Preconditions:**
- A target project git repo with a remote (use a scratch project, not the Writ source repo).

**Steps:**
1. Run the Writ install/setup.
2. Inspect `.git/config` for `remote.<remote>.fetch` and `.push`.
3. Run install/setup again.

**Expected Result:**
- `+refs/notes/writ:refs/notes/writ` (fetch) and `refs/notes/writ` (push) refspecs are present.
- Re-running does not duplicate the refspecs (idempotent).

**Status:** [ ] Pass  [ ] Fail

**Implementation Reference:** Story 4 — Files: `scripts/install.sh` (`configure_audit_notes_sync()`)

**Notes:**

---

### Scenario 15: Opt-out leaves no git-config residue

**Source:** Acceptance Criteria — Story 4

**Preconditions:**
- A project where Writ previously added the notes refspecs.

**Steps:**
1. Set `git config writ.auditNotes false`.
2. Run install/setup.
3. Inspect `.git/config`.

**Expected Result:**
- The Writ-added `refs/notes/writ` refspecs are removed; no residue; user's own refspecs untouched.

**Status:** [ ] Pass  [ ] Fail

**Notes:**

---

### Scenario 16: `/status` shows the latest audit note

**Source:** Acceptance Criteria — Story 4

**Preconditions:**
- At least one Writ audit note exists in the repo.

**Steps:**
1. Run `/status`.

**Expected Result:**
- Output includes `📝 Last audit note: <sha> — <spec title> (<date>)`.

**Status:** [ ] Pass  [ ] Fail

**Implementation Reference:** Story 4 — Files: `commands/status.md`

**Notes:**

---

### Scenario 17: `/status` omits the line when no notes exist

**Source:** Acceptance Criteria — Story 4 (shadow path: nil)

**Preconditions:**
- A repo with no `refs/notes/writ` notes.

**Steps:**
1. Run `/status`.

**Expected Result:**
- No audit-note line is shown (clean omission, no error).

**Status:** [ ] Pass  [ ] Fail

**Notes:**

---

### Scenario 18: Eval check asserts the audit contract

**Source:** Acceptance Criteria — Story 4

**Preconditions:**
- Repo checked out.

**Steps:**
1. Run `bash scripts/eval.sh --check=git-notes-audit` (or the full suite).

**Expected Result:**
- The `git-notes-audit` check passes (26/26 scenarios), asserting ship/release reference `refs/notes/writ` + non-blocking rule, and install.sh guards the refspec config behind the opt-out.

**Status:** [ ] Pass  [ ] Fail

**Implementation Reference:** Story 4 — Files: `scripts/eval-git-notes-audit.py`, `scripts/eval.sh`

**Notes:**

---

## Pending Stories

None — all four stories are complete.
