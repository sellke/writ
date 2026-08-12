# UAT Plan: Autonomy Gate Classes

> **Generated:** 2026-08-11
> **Spec:** `.writ/specs/2026-08-11-autonomy-gate-classes/`
> **Stories Covered:** 3 of 3 completed
> **Total Scenarios:** 16

## How to Use This Plan

1. Work through scenarios in order (grouped by story).
2. Run the commands exactly as written, from the repository root, on a branch that contains this spec (`phase/10-component-contract` or later).
3. Mark Pass or Fail — add notes for anything that differs from the Expected Result.
4. A Fail is filed as an issue or fed back to the spec; it is not fixed inline.
5. The feature passes UAT when every scenario passes, or when a failure is explicitly accepted as a known limitation.

> **Note on this methodology repo:** the deliverables are markdown and shell. Most scenarios are validated by reading a file or running `scripts/eval.sh`, not by exercising a UI. **Scenario 2 temporarily modifies a tracked file** and tells you how to restore it; read its Preconditions before starting.

## Coverage Summary

| Story | Status | Scenarios | Source Breakdown |
|-------|--------|-----------|------------------|
| Story 1: Raise the `_preamble` cap and prove it still binds | ✅ Covered | 6 | AC: 4, Ownership boundary: 1, Tripwire: 1 |
| Story 2: Gate-class table + reversibility precondition | ✅ Covered | 5 | AC: 4, Regression: 1 |
| Story 3: Destructive-command applicability (read-only) | ✅ Covered | 5 | AC: 3, Finding verification: 2 |

---

## Story 1: Raise the `_preamble` Cap and Prove It Still Binds

### Scenario 1: The length check passes on the real repository

**Source:** Acceptance Criteria — Story 1; Success Criterion 1

**Preconditions:**
- Clean checkout at the repository root.

**Steps:**
1. Run `wc -l commands/_preamble.md`.
2. Run `bash scripts/eval.sh --check=length`.
3. Run `echo $?` immediately afterwards.

**Expected Result:**
- Step 1 prints **93**.
- Step 2 prints only an `Eval report: .writ/state/eval-<timestamp>.md` line — no `commands/_preamble.md` finding.
- Step 3 prints `0`.

**Status:** [ ] Pass  [ ] Fail

**Implementation Reference:** Story 1 — Files: `scripts/eval.sh` (`check_length`, `_preamble` branch)

**Notes:**

---

### Scenario 2: The cap still binds — 96 lines fails with `limit 95`

**Source:** Business Rule 2; Success Criterion 2. **This is the scenario that distinguishes a resized cap from a deleted one.** Everything else in Story 1 is consistent with the check having been quietly removed; only this proves it still fires.

**Preconditions:**
- `git status --porcelain commands/_preamble.md` is empty before you start. If it is not, stop — you would lose uncommitted work in step 5.
- If you prefer not to touch a tracked file at all, use the fixture variant in the Notes below instead; it produces the same finding text.

**Steps:**
1. Confirm the starting size: `wc -l commands/_preamble.md` → 93.
2. Append three lines: `printf 'x\ny\nz\n' >> commands/_preamble.md`.
3. Confirm the file is now 96 lines: `wc -l commands/_preamble.md`.
4. Run `bash scripts/eval.sh --check=length; echo "EXIT=$?"`, then open the report path it printed.
5. **Restore immediately:** `git checkout -- commands/_preamble.md` and confirm `wc -l commands/_preamble.md` is back to 93.

**Expected Result:**
- Step 4 prints `EXIT=1`.
- The report contains, verbatim:
  `` - `commands/_preamble.md`: 96 lines (limit 95). _Remediation:_ Move command-specific detail out of the shared preamble. ``
- The finding is under the report's blocking `FAIL` section, not a non-blocking note.
- After step 5 the tree is clean again.

**Status:** [ ] Pass  [ ] Fail

**Implementation Reference:** Story 1 — Files: `scripts/eval.sh:411-412`

**Notes:**
Fixture variant (no tracked file touched): create a temp dir with `scripts/`, `commands/`, `.writ/state/`; copy in `scripts/eval.sh` and the real `commands/_preamble.md`; append the three lines to the copy; run `bash scripts/eval.sh --check=length` from that temp root. This variant was used to verify the expected text above.

---

### Scenario 3: The regression test that carries this proof is green

**Source:** Acceptance Criteria — Story 1; Business Rule 2

**Preconditions:**
- `git` and `bash` available. The test `git init`s a temp fixture root; no git identity is required.

**Steps:**
1. Run `bash scripts/tests/test_eval_length_caps.sh`.
2. Read the seven `PASS:` lines.

**Expected Result:**
- Exit 0 and `All 7 length-cap assertions passed.`
- The seven lines cover: 95 → exit 0; 96 → exit 1 with a blocking `limit 95`; the `commands/*.md` limit still at `limit 2000`; the `spec-lite.md` limit still at `limit 100`; `eval-exempt: length` demonstrated as a full bypass; the real `_preamble.md` carrying no exemption marker; the real `_preamble.md` within 95 lines.
- The last line reports `real commands/_preamble.md is 93 lines, within the 95-line cap`.

**Status:** [ ] Pass  [ ] Fail

**Implementation Reference:** Story 1 — Files: `scripts/tests/test_eval_length_caps.sh`

**Notes:**

---

### Scenario 4: The diff touched two lines and nothing else

**Source:** Business Rule 3; Success Criterion 3

**Preconditions:**
- Full git history available.

**Steps:**
1. Run `git show -U0 c944ce7 -- scripts/eval.sh` (the `feat(eval): raise the _preamble length cap` commit).
2. Read the hunk header and the changed lines.

**Expected Result:**
- One hunk: `@@ -411,2 +411,2 @@ check_length() {`.
- Exactly two lines removed and two added: `-gt 80` → `-gt 95`, and `limit 80` → `limit 95` in the finding message.
- The remediation hint (`Move command-specific detail out of the shared preamble.`), the `[ -f "$file" ]` guard, and the `file_has_exemption` guard are unchanged.

**Status:** [ ] Pass  [ ] Fail

**Implementation Reference:** Story 1 — Files: `scripts/eval.sh:411-412`

**Notes:**

---

### Scenario 5: Ownership boundary — the two adjacent limits still fire

**Source:** Business Rule 3; Story 1 AC 4. The command limit sits eleven lines below the line that moved; a loose search-and-replace would have taken both.

**Preconditions:**
- None.

**Steps:**
1. Run `grep -n 'limit 100\|limit 95\|limit 2000' scripts/eval.sh`.
2. Confirm three distinct limits appear inside `check_length`: `-gt 100` (spec-lite), `-gt 95` (`_preamble`), `-gt 2000` (command files).
3. Re-read the two ownership-boundary `PASS` lines from Scenario 3's output — a 2001-line command file reports `limit 2000`, a 101-line `spec-lite.md` reports `limit 100`.

**Expected Result:**
- All three limits are present with their own numbers.
- Neither adjacent limit was changed to match the new `_preamble` number, and both still produce findings on their own fixtures.

**Status:** [ ] Pass  [ ] Fail

**Implementation Reference:** Story 1 — Files: `scripts/eval.sh` (`check_length`), `scripts/tests/test_eval_length_caps.sh` scenarios 3-4

**Notes:**

---

### Scenario 6: No exemption marker — the cap was resized, not bypassed

**Source:** Business Rule 4; Story 1 AC 5

**Preconditions:**
- None.

**Steps:**
1. Run `grep -n 'eval-exempt' commands/_preamble.md; echo "EXIT=$?"`.
2. Read Scenario 5 of `scripts/tests/test_eval_length_caps.sh` (the exemption-trap block) to see what the marker would have done.

**Expected Result:**
- Step 1 prints no match and `EXIT=1`.
- The test demonstrates the trap it guards: a 96-line `_preamble.md` carrying `<!-- eval-exempt: length -->` exits 0 with **no finding at all** — the exemption removes the cap rather than resizing it, and nothing else in the suite would notice.

**Status:** [ ] Pass  [ ] Fail

**Implementation Reference:** Story 1 — Files: `commands/_preamble.md`, `scripts/eval.sh` (`file_has_exemption`)

**Notes:**

---

## Story 2: The Gate-Class Table and Reversibility Precondition

### Scenario 7: Five gate classes, faithful to ADR-022

**Source:** Business Rule 8; Story 2 AC 1-2; Success Criterion 4

**Preconditions:**
- None.

**Steps:**
1. Open `commands/_preamble.md` and find `## Autonomy Gate Classes` (line 49).
2. Open `.writ/decision-records/adr-022-autonomy-gate-classes.md` and find its Decision table (lines 13-19).
3. Compare row by row: class names, then behaviors.

**Expected Result:**
- Five rows in both, same five classes, no sixth: Product & spec direction; Production boundary; Design & UX judgment; Destructive / irreversible; Everything else.
- The three human gates carry the same reason in each: contract lock is an explicit human action; Prime Directive hard constraint; taste is not evidence-decidable.
- The destructive row reads **"Autonomous only when the precondition below holds"** — neither a human gate nor unconditional autonomy. This is ADR-022's "Autonomous, subject to a reversibility precondition" compressed, not changed.
- The preamble's production-boundary row names the operations explicitly (`merge/PR/release/tag/publish`), which the ADR states in prose. Compression added specificity here; it removed none.

**Status:** [ ] Pass  [ ] Fail

**Implementation Reference:** Story 2 — Files: `commands/_preamble.md:53-59`, ADR-022

**Notes:**

---

### Scenario 8: The reversibility precondition is normative and complete

**Source:** Business Rule 5; Story 2 AC 3-4

**Preconditions:**
- None.

**Steps:**
1. Read the precondition paragraph at `commands/_preamble.md:61`.
2. Check for both conditions, numbered `(1)` and `(2)`.
3. Check the quantifier and the consequence.
4. Run a hedge grep over the section:
   `sed -n '49,61p' commands/_preamble.md | grep -nEi 'should|consider|prefer|where practical|generally|typically|ideally|try to'`

**Expected Result:**
- Condition (1): "provably git-revertable — confined to tracked files with a resolvable revert target".
- Condition (2): "the restore path is recorded **before** the mutation", with `before` emphasized — the ordering *is* the rule.
- The quantifier reads **"only when both hold"**, not "when either holds" and not "where practical".
- The consequence is stated as behavior: "If either fails, it **pauses** with a bounded `AskQuestion`."
- The hedge grep returns nothing.

**Status:** [ ] Pass  [ ] Fail

**Implementation Reference:** Story 2 — Files: `commands/_preamble.md:61`

**Notes:**

---

### Scenario 9: The section extends ADR-013 and stays out of the ADR's business

**Source:** Business Rules 6 and 7; Story 2 AC 5 and 8

**Preconditions:**
- None.

**Steps:**
1. Read the line directly under the `## Autonomy Gate Classes` heading.
2. Note where the section sits relative to `## User Challenge (Scope-Degradation Escalation)` and `## File Organization`.
3. Search the section for ADR-022's reasoning, the recorded objection, and the review date: `sed -n '49,61p' commands/_preamble.md | grep -niE 'objection|dissent|regression|2026-11-11'`.

**Expected Result:**
- Step 1: "Extends ADR-013's select-or-pause boundary above; it does not replace it."
- Step 2: the section is immediately after `User Challenge` (where ADR-013's boundary is already stated) and before `File Organization`.
- Step 3 returns nothing — the preamble carries the rule; ADR-022 carries the argument, the recorded objection, and the **2026-11-11 review trigger**. Confirm those three do exist in ADR-022 (they are in its "The disagreement, recorded" section and its Consequences).

**Status:** [ ] Pass  [ ] Fail

**Implementation Reference:** Story 2 — Files: `commands/_preamble.md:49-61`, ADR-022

**Notes:**

---

### Scenario 10: The section landed inside its stated budget

**Source:** Business Rule 1; Story 2 AC 6. The budget is the artifact that survives, not the number 95.

**Preconditions:**
- Full git history available.

**Steps:**
1. Run `git show fe2af84:commands/_preamble.md | wc -l` (the file as it stood before this spec).
2. Run `git show --numstat 845de04 -- commands/_preamble.md | tail -1`.
3. Run `wc -l commands/_preamble.md`.

**Expected Result:**
- Step 1: **79** — the baseline the budget was derived from.
- Step 2: `14	0	commands/_preamble.md` — fourteen lines added, none removed, exactly the 14-line section budget.
- Step 3: **93** — 79 + 14, with both reserve lines unspent, against a 95-line cap.
- The arithmetic 79 + 14 + 2 = 95 is reconstructable without reading the finished section, which is the test the spec set for itself.

**Status:** [ ] Pass  [ ] Fail

**Implementation Reference:** Story 2 — Files: `commands/_preamble.md`; commits `c944ce7` (cap, first) then `845de04` (content, second)

**Notes:**

---

### Scenario 11: The other eval checks that read `_preamble.md` still pass

**Source:** Story 2 AC 7; Success Criterion 5

**Preconditions:**
- None.

**Steps:**
1. Run `bash scripts/eval.sh --check=preamble; echo "EXIT=$?"`.
2. Run `bash scripts/eval.sh --check=autonomy-governance; echo "EXIT=$?"`.
3. Optionally run the full `bash scripts/eval.sh` and compare its findings against the pre-spec baseline.

**Expected Result:**
- Both checks exit `0`. `check_preamble` validates reference integrity; `check_autonomy_governance` validates policy-surface consistency across `system-instructions.md`, `cursor/writ.mdc`, and `_preamble.md`. Adding the section tripped neither.
- The full run produces no findings that the pre-spec baseline did not already have.

**Status:** [ ] Pass  [ ] Fail

**Implementation Reference:** Story 2 — Files: `scripts/eval.sh` (`check_preamble`, `check_autonomy_governance`)

**Notes:**

---

## Story 3: Applicability to the Destructive-Class Commands (Read-Only)

> Story 3 asked one narrow question of four commands: **can an agent evaluate both precondition conditions before acting?** The answer it recorded is uncomfortable, and the scenarios below exist so a human can confirm it rather than take it on trust.

### Scenario 12: The applicability record is complete — twelve cells, no blanks

**Source:** Story 3 AC 1; Success Criterion 6

**Preconditions:**
- None.

**Steps:**
1. Open `.writ/specs/2026-08-11-autonomy-gate-classes/user-stories/story-3-destructive-command-applicability.md`.
2. Find the applicability table under "What Was Built".
3. Count the cells: four commands × (condition 1, condition 2, evaluable).

**Expected Result:**
- Twelve cells, every one an explicit Yes or No — no blanks, no `n/a`.
- Eight are **No**: condition (1) and condition (2) fail for all four commands.
- All four "Evaluable by an agent" cells are **Yes**.
- Every No is followed by prose naming the specific path or file that fails.

**Status:** [ ] Pass  [ ] Fail

**Implementation Reference:** Story 3 — Files: the story file above

**Notes:**

---

### Scenario 13: Spot-check the `/revert` and `/refactor` findings against the command files

**Source:** Story 3 AC 2 and 4. Do not take the table on trust; the commands are readable in two minutes.

**Preconditions:**
- None.

**Steps:**
1. Run `grep -n 'porcelain' commands/revert.md`.
2. Read `commands/revert.md` around line 59 (Phase 3, "Dirty-tree guard FIRST").
3. In the same file, find the `git reset --hard <base>` strategy behind a second confirmation.
4. Run `grep -n 'porcelain' commands/refactor.md skills/safe-refactor-loop/SKILL.md`.
5. Read `commands/refactor.md:51-57` (Step 1.2 Baseline Verification) and `skills/safe-refactor-loop/SKILL.md:62` (the "Checkpoint" step).

**Expected Result:**
- Steps 1-2: `/revert` HALTs on a non-empty `git status --porcelain` **before any git operation**, and lists that guard as Safety Guarantee #1 (line 138). Porcelain reports untracked entries as `??`, so this one guard closes both the untracked-file and uncommitted-changes failure modes — condition (1) implemented under another name.
- Step 3: the hard-reset path discards commits that survive only in the reflog. There is no revert target by construction, so condition (1) is a per-invocation answer for `/revert`, not a per-command one. That is exactly the discrimination ADR-022 wanted from replacing a name-based blocklist.
- Step 4: **no matches** in either file. `/refactor` has no dirty-tree guard.
- Step 5: Step 1.2 gates on tests, typechecker, and linter only — git state is not among them. The skill's step 1 says "note the current clean git state so a revert is one step", which *assumes* a clean tree and prescribes nothing that establishes one. `/refactor` reverts on every red verification, so this gap is live.
- Filed as `.writ/issues/bugs/2026-08-11-refactor-has-no-dirty-tree-guard.md`.

**Status:** [ ] Pass  [ ] Fail

**Implementation Reference:** Story 3 — Files: `commands/revert.md`, `commands/refactor.md`, `skills/safe-refactor-loop/SKILL.md`

**Notes:**

---

### Scenario 14: Spot-check the `/uninstall-writ` and `/reinstall-writ` findings

**Source:** Story 3 AC 3. `/uninstall-writ` is the case the precondition was written to catch.

**Preconditions:**
- None.

**Steps:**
1. Run `grep -n 'git add -u\|will be lost\|No git repo' commands/uninstall-writ.md`.
2. Read line 113's rationale for `git add -u`, and the Error Handling row at line 144.
3. Run `grep -n 'git clone\|baseline hashes\|curl' commands/reinstall-writ.md`.
4. Read line 78 (baseline-hash comparison), line 125 (`git clone` from GitHub), the removal list around line 111, and the recovery instruction around line 187.

**Expected Result:**
- `/uninstall-writ` Step 2 computes "Customized files: [K] (will be lost)" **before** deleting — a warning computed pre-mutation that preserves none of the K files. A count is not a restore path.
- Step 4 stages with `git add -u`, documented as "stage deletions without adding untracked files": deleting an untracked platform file is captured in no commit and produces no warning. In a target project `.claude/` or `.cursor/` is commonly gitignored, so this is not a hypothetical.
- Error Handling documents `No git repo | Skip commit step` — an invocation with no revert target at all.
- `/reinstall-writ` compares **baseline hashes**, which detect that a file was customized but cannot reconstruct a byte of it; and the manifest holding those hashes is itself deleted at line 111. Its Step 4 `git clone` reaches outside the repository, and its documented recovery from a failed clone is a `curl | bash` reinstall, not a git operation.

**Status:** [ ] Pass  [ ] Fail

**Implementation Reference:** Story 3 — Files: `commands/uninstall-writ.md`, `commands/reinstall-writ.md`

**Notes:**

---

### Scenario 15: The consequential finding — the destructive row resolves to *pause* today

**Source:** Story 3 Task 3.8 verdict. **This is the finding a human should personally confirm.** ADR-022 moved the destructive class to autonomous-with-precondition in order to unlock autonomy. As implemented, it has not: condition (2) is unsatisfied by all four commands, so the row resolves to pause in every real case today.

**Preconditions:**
- None. This is a reading exercise over four files.

**Steps:**
1. Re-read condition (2) at `commands/_preamble.md:61`: the restore path is recorded **before** the mutation.
2. For each of `commands/revert.md`, `commands/refactor.md`, `commands/uninstall-writ.md`, `commands/reinstall-writ.md`, look for a step that writes something **durable** (a file, a git ref, a note) naming what the operation is about to destroy, **before** the first mutating step. Conversation output does not count — it does not survive the session and nothing downstream can read it.
3. For `/revert` specifically, check the Phase 5 git-notes audit entry: note that it is optional ("may attach", "skip silently if the channel is absent") and lands **after** Phase 4 has already executed.
4. Read the verdict in the Story 3 file and the improvement issue `.writ/issues/improvements/2026-08-11-restore-path-recording-for-destructive-commands.md`.

**Expected Result:**
- You find **no such durable pre-mutation write in any of the four**. `/revert` presents its plan; `/refactor` writes nothing before its first edit; `/uninstall-writ` prints a count; `/reinstall-writ` holds hashes in a manifest it then deletes.
- Therefore condition (2) is false for all four, "only when both hold" fails, and every invocation pauses.
- Two consequences, both stated plainly in the story's verdict and the filed issue: the safety regression the recorded objection warned about **has not materialized**, because the precondition holds the line — and the autonomy ADR-022 intended to unlock **is not available**, because nothing can satisfy it. The gate moved from a name-based blocklist to a risk test that currently returns false for everything in the class.
- The issue states that it should be closed by building the recording mechanism, never by relaxing the precondition's wording to fit what the commands already do. Confirm that instruction is present — it is the thing most likely to be quietly inverted later.

**Status:** [ ] Pass  [ ] Fail

**Implementation Reference:** Story 3 verdict (Task 3.8); `.writ/issues/improvements/2026-08-11-restore-path-recording-for-destructive-commands.md`; ADR-022's 2026-11-11 review trigger

**Notes:**

---

### Scenario 16: Read-only held — no command file changed except `_preamble.md`

**Source:** Business Rule 9; Story 3 AC 5-6

**Preconditions:**
- Full git history available.

**Steps:**
1. Run `git show --stat d18f61d` (the Story 3 commit) and inspect the changed paths.
2. Run `git show --stat c944ce7 845de04 | grep -E '^\s(commands|scripts)/'`.
3. Run `ls .writ/issues/bugs/ .writ/issues/improvements/`.

**Expected Result:**
- Story 3's commit touches only files under `.writ/` — no path under `commands/`.
- Across the whole spec, the only files changed are `scripts/eval.sh`, `scripts/tests/test_eval_length_caps.sh`, `commands/_preamble.md`, and `.writ/` artifacts. `commands/revert.md`, `refactor.md`, `uninstall-writ.md`, and `reinstall-writ.md` are untouched.
- Both issues exist and are referenced by path from the Story 3 file: `2026-08-11-refactor-has-no-dirty-tree-guard.md` (bug) and `2026-08-11-restore-path-recording-for-destructive-commands.md` (improvement).

**Status:** [ ] Pass  [ ] Fail

**Implementation Reference:** Story 3 — Files: `.writ/issues/`, commits `c944ce7`, `845de04`, `d18f61d`

**Notes:**

---

## Discrepancies Worth Recording

These are not scenario failures — the spec was implemented as written. They are places where the *reasoning* upstream of the spec is weaker than it reads, and a UAT tester should see them stated rather than discover them later.

1. **ADR-022's git-reversibility argument is incomplete in two places, and Story 3 found both.** The ADR's "defensible reading" lists `/revert` as producing "revert *commits* — additive history, fully undoable" without mentioning its `git reset --hard` path, which is not undoable; and lists `/reinstall-writ` as safe because "the manifest records baselines", when those baselines are hashes that cannot reconstruct a customization and the manifest is deleted mid-operation. The decision may still be right, but two of its four supporting examples do not hold as stated.

2. **The ADR's intended effect and its actual effect are opposites today.** ADR-022 moved destructive operations from human-gated to autonomous-with-precondition to expand autonomy "measurably". Because no command records a restore path before mutating, the precondition returns false for every invocation of all four commands, so the class is *more* restricted in practice than a human gate would be — a human gate at least offers a way through. This is Scenario 15, and it is the single most consequential result of the phase.

3. **The precondition is prose, not enforcement, and the spec says so.** There is no mechanical "provably git-revertable" check; nothing fails a build if a command ignores the precondition. It binds only agents that read `_preamble.md` and follow it. ADR-022 records this as a known negative consequence; Story 3 measured the gap across four commands and confirmed it is real. Do not read a passing UAT as evidence that the precondition is enforced.

4. **The cap raise is defensible, not free.** 95 was derived from a stated budget before any content existed (Scenario 10), a regression test proves it still fires (Scenarios 2-3), and the exemption escape hatch is banned and tripwired (Scenario 6). That is three more defenses than the 2000-line command limit ever had. It is still a limit that moved to accommodate content, and the next request to move it should have to make the same argument from a new budget rather than cite this one as precedent.

---

## Sign-Off

| Role | Name | Date | Result |
|------|------|------|--------|
| Tester | | | [ ] Pass [ ] Fail |
| Reviewer | | | [ ] Pass [ ] Fail |

**Overall UAT:** [ ] Pass  [ ] Fail

**Notes:**
