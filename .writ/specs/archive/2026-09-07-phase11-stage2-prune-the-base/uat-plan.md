# UAT Plan: Phase 11 Stage 2a: Prune the Base

> **Generated:** 2026-09-25
> **Spec:** `.writ/specs/2026-09-07-phase11-stage2-prune-the-base/`
> **Stories Covered:** 5 of 5 completed
> **Total Scenarios:** 38
> **Updated:** 2026-09-25 after defect fixes

## How to Use This Plan

1. Work through scenarios in order (grouped by story, ordered by priority).
2. Run every command from the repository root in **bash** (several scenarios use `<( … )` and `for` loops). Scenarios marked "scratch" build throwaway files under a temp directory; scenarios marked "worktree" edit a detached git worktree. Neither touches tracked files in your checkout.
3. Mark Pass or Fail. Add notes for any output that differs from the Expected Result.
4. File a Fail as an issue or feed it back to the spec. Do not fix it inline.
5. The feature passes UAT when every scenario passes, or when a failure is accepted as a known limitation.

> **Note on this methodology repo:** the deliverables are two Python scripts (`scripts/prune-ledger.py`, `scripts/verdict-provenance.py`), two `eval.sh` checks, an ADR, a ledger, edits to two markdown base files, four `.writ/docs/` files, four adapter lines, a `gates:` frontmatter block, and one baseline JSON. There is no UI.
>
> **`eval.sh` writes its result to a report file, not the terminal.** After each `bash scripts/eval.sh --check=<name>` the terminal prints `Eval report: .writ/state/eval-<timestamp>.md`. Read the check's section with:
> ```
> sed -n '/^## /,$p' "$(ls -t .writ/state/eval-*.md | head -1)"
> ```
> `eval.sh` runs `git init` in a temp dir; run it outside any sandbox.

### Setup A — scratch directory (run once)

```
export UAT=$(mktemp -d)
```

Delete it with `rm -rf "$UAT"` when done.

### Setup B — ledger scratch repo (Story 1 scenarios)

A tiny git repo with both base files, pinned at its own commit so the check can diff against it.

```
export R="$UAT/repo"
mkdir -p "$R/commands" "$R/.writ/decision-records"
git -C "$R" init -q
printf '# Base\nkeep me\ncut me\nhas | pipe\nmove me\n' > "$R/system-instructions.md"
printf '# Pre\npre line\n' > "$R/commands/_preamble.md"
git -C "$R" add -A
git -C "$R" -c user.email=uat@example.com -c user.name=uat commit -qm base
export B=$(git -C "$R" rev-parse HEAD)
export L="$R/.writ/decision-records/pruned-instructions-ledger.md"
reset_fixture() { git -C "$R" checkout -q -- system-instructions.md commands/_preamble.md; printf '| Date | File | Class | Reason | Text |\n|---|---|---|---|---|\n' > "$L"; }
```

`reset_fixture` restores both base files and writes a ledger with a header and zero rows.

### Setup C — detached worktree of the current tree (Story 3 error scenarios)

```
S=$(git stash create); git worktree add -q --detach "$UAT/wt" "${S:-HEAD}"
export W="$UAT/wt"
```

`git stash create` makes a commit object of your uncommitted tracked changes without touching the checkout or the stash list; with a clean tree it prints nothing and the worktree is HEAD. The worktree then carries the same `system-instructions.md`, ledger, and `eval.sh` you are testing.

Reset between scenarios with `git -C "$W" checkout -q -- .`. Remove it when done with `git worktree remove --force "$W"`.

## What This Spec Delivered

The shared base every Writ invocation loads (`system-instructions.md` + `commands/_preamble.md`) went from 28,157 bytes to 9,704. Story 2 moved four documentation sections to `.writ/docs/` (28,157 → 15,713). Story 3 cut behavior requests and duplicates (15,713 → 9,704) and flipped the 10,000-byte cap to blocking. Every removed line is a row in `.writ/decision-records/pruned-instructions-ledger.md` (187 rows), and `scripts/prune-ledger.py check` fails if a removal has no row or a row's text comes back. Story 4 added a `gates:` block to `commands/implement-story.md` and `scripts/verdict-provenance.py` to keep it in step with the `#### Gate` headings. Story 5 re-ran the eight Fable 5.1 baseline replays on the pruned base: 8/8 exit criteria met, same as Stage 1, so the cut was kept.

On 2026-09-25 one kept line was reworded to drop its reference to the cut `## Session Auto-Orientation` section, with a ledger row for the old text. The base is now 9,676 bytes and the ledger has 188 rows. Scenarios below use today's numbers; historical numbers (9,704 at Story 3's close) appear only where a scenario checks a past commit or record.

## Honest Notes (read before signing off)

1. **This spec is superseded; some shipped state has moved on.** Stage 2b (`2026-09-08-phase11-stage2b-mechanize-the-gates`) changed six gates from `prose-only` to `script` and made `eval.sh` pass `--prose-only-blocking`. Story 4 shipped 2 script / 8 prose-only with a non-blocking count. Today the file reads 8 script / 2 prose-only. Scenarios 26 and 29 check both: the Story 4 commit as it shipped, and HEAD as it is now.
2. **The revert path was never run end to end.** Story 5 kept the cut, so the "revert Stories 2–3" branch never ran. Scenario 38 checks only that `scripts/revert-resolve.py` resolves the right commits for Stories 2 and 3 (it does, after the 2026-09-25 fix that scopes `Ref:` footers to the spec and adds the `task-subject` layer). No `/revert` was executed.
3. **The keep decision rests on a result inside the noise.** 8/8 held, but total cost moved −4.7%, within the 59% cache-read spread Stage 1 measured between identical runs. Only cache-creation tokens (−36%) moved more than the noise. UAT does not re-run the eight replays (about $180 and 6 hours); Scenarios 33–36 check the recorded evidence.
4. **One kept line was reworded after the spec closed.** On 2026-09-25 the Startup Update Awareness trigger lost its reference to the cut `## Session Auto-Orientation` ("before session auto-orientation or any command-specific workflow" became "before any command-specific workflow"). Business Rule 5 forbids rewording a kept line, so the old text was logged as a removal: a 2026-09-25 ledger row of class `duplicate`, whose reason names the rewording. The ledger has no `reworded` class; decide whether `duplicate` is acceptable. Scenarios 15 and 19 show the effect.
5. **The check reads the working tree, not the last commit.** `git diff <base>` compares the working tree, so `prune-ledger.py check` is green or red for uncommitted edits too. This is intended (Story 1, Implementation Decision 4) and is why the worktree scenarios work.

## Coverage Summary

| Story | Status | Scenarios | Source Breakdown |
|-------|--------|-----------|-----------------|
| Story 1: Pruning Policy ADR and Ledger Tooling | ✅ Covered | 10 | AC: 5, Errors: 2, Shadow: 1, Edge: 2 |
| Story 2: Move Documentation Out | ✅ Covered | 7 | AC: 5, Errors: 0, Shadow: 0, Edge: 1, Experience: 1 |
| Story 3: Cut Behavior Requests | ✅ Covered | 8 | AC: 5, Errors: 2, Shadow: 0, Edge: 1 |
| Story 4: Gate Verification Markers and Provenance Check | ✅ Covered | 7 | AC: 5, Errors: 1, Shadow: 1, Edge: 0 |
| Story 5: Baseline Re-run and Keep-or-Revert | ✅ Covered | 6 | AC: 4, Errors: 1, Shadow: 0, Edge: 1 |

Technical-spec §1 finding codes: `removed_not_in_ledger` and `ledger_text_reappeared` → Scenarios 4, 23, 24; `over_cap` → 5, 25; `malformed_row` → 7; `ledger_missing` → 2. Technical-spec §5 finding codes → Scenario 27. Shadow paths from spec-lite: nil input (no ledger) → 2; empty input (empty `gates:`) → 32; upstream error (bad base commit) → 3. Edge cases: re-add → 4, 24; pipe in text → 9; reflowed kept line → 10; differing `selection` → 37. The edge case "`runs_per_story` differs → per-story medians" has no scenario: both committed files carry `runs_per_story: 2`.

---

## Story 1: Pruning Policy ADR and Ledger Tooling

### Scenario 1: ADR-026 states the three-way test and its negative consequence

**Source:** Acceptance Criteria (AC-1.1) — Story 1

**Preconditions:**
- None.

**Steps:**
1. `grep -n "three-way test" .writ/decision-records/adr-026-constraint-test-pruning.md`
2. `grep -n "costs a baseline re-run to discover" .writ/decision-records/adr-026-constraint-test-pruning.md`
3. Open `.writ/decision-records/adr-026-constraint-test-pruning.md` and read the Decision and Alternatives sections.

**Expected Result:**
- Step 1 finds the decision sentence: every line of the two base files is classified by a three-way test and only the first two classes stay.
- Step 2 finds the bullet under **Negative**: "A behavior request later found load-bearing costs a baseline re-run to discover."
- Step 3: the three classes are environment fact, human boundary, and behavior request. Alternatives include a byte target alone, per-model prompt tuning, and do nothing.

**Status:** [ ] Pass  [ ] Fail

**Implementation Reference:** Story 1 — `.writ/decision-records/adr-026-constraint-test-pruning.md` (106 lines)

**Notes:**

---

### Scenario 2: No ledger, or an empty ledger, is a note and exit 0

**Source:** Acceptance Criteria (AC-1.2); Shadow Path (nil input) — Story 1

**Preconditions:**
- Setups A and B done.

**Steps:**
1. `rm -f "$L"; python3 scripts/prune-ledger.py check --repo "$R" --base-commit "$B"; echo "exit=$?"`
2. `reset_fixture; python3 scripts/prune-ledger.py check --repo "$R" --base-commit "$B"; echo "exit=$?"`
3. On the real repo: `python3 scripts/prune-ledger.py check --repo .; echo "exit=$?"`

**Expected Result:**
- Step 1 prints `note: ledger_missing: no ledger file yet (.writ/decision-records/pruned-instructions-ledger.md)`, then `base: 56 bytes (cap 10000), ledger: 0 rows, removed: 0, re-added: 0`; `exit=0`.
- Step 2 prints `note: ledger_missing: no rows yet (…)` and the same summary; `exit=0`.
- Step 3 prints only `base: 9676 bytes (cap 10000), ledger: 188 rows, removed: 188, re-added: 0`; `exit=0`.
- The summary line is always the last line.

**Status:** [ ] Pass  [ ] Fail

**Implementation Reference:** Story 1 — `scripts/prune-ledger.py` (`check`)

**Notes:**

---

### Scenario 3: A bad base commit exits 2 with git's own error

**Source:** Shadow Path (upstream error); Acceptance Criteria (AC-1.2) — Story 1

**Preconditions:**
- None.

**Steps:**
1. `python3 scripts/prune-ledger.py check --repo . --base-commit nosuchrev > "$UAT/out.txt"; echo "exit=$?"; echo "stdout bytes: $(wc -c < "$UAT/out.txt")"`

**Expected Result:**
- stderr shows `fatal: bad revision 'nosuchrev'` (git's message, not a rewritten one).
- `exit=2`.
- `stdout bytes: 0` — no findings or summary are printed.

**Status:** [ ] Pass  [ ] Fail

**Notes:**

---

### Scenario 4: A removal without a row, and a row whose text comes back, are findings

**Source:** Acceptance Criteria (AC-1.3) — Story 1

**Preconditions:**
- Setups A and B done.

**Steps:**
1. Remove `cut me` with no ledger row:
   ```
   reset_fixture
   printf '# Base\nkeep me\nhas | pipe\nmove me\n' > "$R/system-instructions.md"
   python3 scripts/prune-ledger.py check --repo "$R" --base-commit "$B"; echo "exit=$?"
   ```
2. Add the row and run again:
   ```
   echo '| 2026-09-07 | system-instructions.md | behavior-request | uat | cut me |' >> "$L"
   python3 scripts/prune-ledger.py check --repo "$R" --base-commit "$B"; echo "exit=$?"
   ```
3. Put `cut me` back at the end of the file (a re-add) while the row stays:
   ```
   printf '# Base\nkeep me\nhas | pipe\nmove me\ncut me\n' > "$R/system-instructions.md"
   python3 scripts/prune-ledger.py check --repo "$R" --base-commit "$B"; echo "exit=$?"
   ```

**Expected Result:**
- Step 1: `removed_not_in_ledger: system-instructions.md: cut me`, a `ledger_missing` note, the summary with `removed: 1`; `exit=1`.
- Step 2: only the summary, `ledger: 1 rows, removed: 1, re-added: 0`; `exit=0`.
- Step 3: `ledger_text_reappeared: 2026-09-07 system-instructions.md: cut me` (names the ledger date and file), summary with `removed: 0, re-added: 1`; `exit=1`.

**Status:** [ ] Pass  [ ] Fail

**Implementation Reference:** Story 1 — `scripts/prune-ledger.py`; "reappeared" means present as a whole line and not among that file's net removals (DEV-003).

**Notes:**

---

### Scenario 5: Over the cap is a note by default and a finding with `--cap-blocking`

**Source:** Acceptance Criteria (AC-1.4) — Story 1

**Preconditions:**
- Setups A and B done.

**Steps:**
1. `reset_fixture; python3 scripts/prune-ledger.py check --repo "$R" --base-commit "$B" --cap 20; echo "exit=$?"`
2. `python3 scripts/prune-ledger.py check --repo "$R" --base-commit "$B" --cap 20 --cap-blocking; echo "exit=$?"`

**Expected Result:**
- Step 1: `note: over_cap: 56 bytes > cap 20`, the `ledger_missing` note (the fixture ledger has no rows), then the summary with `(cap 20)`; `exit=0`.
- Step 2: `over_cap: 56 bytes > cap 20` with no `note:` prefix, the `ledger_missing` note, then the summary; `exit=1`.

**Status:** [ ] Pass  [ ] Fail

**Notes:**

---

### Scenario 6: `eval.sh` runs the `pruned-base` check and relays its output

**Source:** Acceptance Criteria (AC-1.5) — Story 1

**Preconditions:**
- Outside any sandbox. `uv` on PATH.

**Steps:**
1. `bash scripts/eval.sh --check=pruned-base; echo "exit=$?"`, then read the report section (see "How to Use").
2. `bash scripts/tests/test_eval_pruned_base.sh; echo "exit=$?"`
3. `uv run --python 3.9 pytest -q scripts/tests/test_prune_ledger.py`

**Expected Result:**
- Step 1: `exit=0`. The report shows `## pruned-base`, `PASS`, and the note `NOTE [pruned-base]: base: 9676 bytes (cap 10000), ledger: 188 rows, removed: 188, re-added: 0`. `Findings: 0`.
- Step 2: ends `All 9 pruned-base check assertions passed.`; `exit=0`. These assertions cover a removal without a row surfacing as a finding, the cap flipping from note to finding when the marker is added (with the over-cap remediation text, not the ledger-row text), and a missing helper.
- Step 3: `31 passed`.

**Status:** [ ] Pass  [ ] Fail

**Implementation Reference:** Story 1 — `scripts/eval.sh` (`check_pruned_base`; base commit `${WRIT_PRUNE_BASE_COMMIT:-cf84742}`, DEV-001), `scripts/tests/test_eval_pruned_base.sh`

**Notes:**

---

### Scenario 7: A malformed ledger row is a finding

**Source:** Error Map (`malformed_row`) — Story 1

**Preconditions:**
- Setups A and B done.

**Steps:**
1. ```
   reset_fixture
   echo '| bad row |' >> "$L"
   python3 scripts/prune-ledger.py check --repo "$R" --base-commit "$B"; echo "exit=$?"
   ```

**Expected Result:**
- Prints `malformed_row: .writ/decision-records/pruned-instructions-ledger.md:3: | bad row |` (file and line number of the bad row), the `ledger_missing` note (the bad row is not counted as a row), then the summary; `exit=1`.

**Status:** [ ] Pass  [ ] Fail

**Notes:**

---

### Scenario 8: A missing base file or missing subcommand exits 2

**Source:** Error Map (exit codes) — Story 1

**Preconditions:**
- Setups A and B done.

**Steps:**
1. `rm "$R/commands/_preamble.md"; python3 scripts/prune-ledger.py check --repo "$R" --base-commit "$B"; echo "exit=$?"; reset_fixture`
2. `python3 scripts/prune-ledger.py; echo "exit=$?"`

**Expected Result:**
- Step 1: stderr `check: error: commands/_preamble.md is missing under --repo <path>`; `exit=2`.
- Step 2: argparse usage on stderr naming `{check,measure}`; `exit=2`.

**Status:** [ ] Pass  [ ] Fail

**Implementation Reference:** Story 1 — DEV-004 (missing base file is exit 2; `eval.sh` notes a tree with no base instead)

**Notes:**

---

### Scenario 9: Moving a line within a file is not a removal; pipes in text round-trip

**Source:** Edge Case (move within file; pipe in text) — Story 1

**Preconditions:**
- Setups A and B done.

**Steps:**
1. Swap two lines, with no ledger rows:
   ```
   reset_fixture
   printf '# Base\nkeep me\ncut me\nmove me\nhas | pipe\n' > "$R/system-instructions.md"
   python3 scripts/prune-ledger.py check --repo "$R" --base-commit "$B"; echo "exit=$?"
   ```
2. Remove the line containing a pipe, then add its row with the pipe escaped as `\|`:
   ```
   printf '# Base\nkeep me\ncut me\nmove me\n' > "$R/system-instructions.md"
   python3 scripts/prune-ledger.py check --repo "$R" --base-commit "$B"; echo "exit=$?"
   echo '| 2026-09-07 | system-instructions.md | moved | .writ/docs/x.md | has \| pipe |' >> "$L"
   python3 scripts/prune-ledger.py check --repo "$R" --base-commit "$B"; echo "exit=$?"
   ```

**Expected Result:**
- Step 1: `ledger_missing` note and summary with `removed: 0`; `exit=0`.
- Step 2, first run: `removed_not_in_ledger: system-instructions.md: has | pipe`; `exit=1`.
- Step 2, second run: summary only, `ledger: 1 rows, removed: 1`; `exit=0`. The escaped `\|` in the row matched the literal `|` in the removed line.

**Status:** [ ] Pass  [ ] Fail

**Notes:**

---

### Scenario 10: Reflowing a kept line reads as a removal without a row

**Source:** Edge Case (kept line reflowed) — Story 1

**Preconditions:**
- Setups A and B done.

**Steps:**
1. Add a second space inside `keep me`:
   ```
   reset_fixture
   printf '# Base\nkeep  me\ncut me\nhas | pipe\nmove me\n' > "$R/system-instructions.md"
   python3 scripts/prune-ledger.py check --repo "$R" --base-commit "$B"; echo "exit=$?"
   ```

**Expected Result:**
- Prints `removed_not_in_ledger: system-instructions.md: keep me` (plus the `ledger_missing` note and summary); `exit=1`. No whitespace normalization: a changed kept line is treated as a removal, which the spec says is intended (Business Rule 5).

**Status:** [ ] Pass  [ ] Fail

**Notes:**

---

## Story 2: Move Documentation Out

### Scenario 11: The documentation sections left the base and each left one pointer line

**Source:** Acceptance Criteria (AC-2.1) — Story 2

**Preconditions:**
- None.

**Steps:**
1. `grep -nE '^(### entry_level|### .required_skills|### Skill authoring)' system-instructions.md commands/_preamble.md; echo "grep-exit=$?"`
2. `grep -n 'See `.writ/docs' system-instructions.md`
3. `ls .writ/docs/model-tiers.md .writ/docs/skills.md .writ/docs/startup-update-awareness.md .writ/docs/recommendation-semantics.md`
4. `grep -n "normative" .writ/docs/model-tiers.md | head -1; grep -n '^### `required_skills:`\|^## Authoring a Skill' .writ/docs/skills.md; head -3 .writ/docs/startup-update-awareness.md; head -3 .writ/docs/recommendation-semantics.md`

**Expected Result:**
- Step 1: no matches; `grep-exit=1`.
- Step 2: four pointer lines, one each for `recommendation-semantics.md`, `startup-update-awareness.md`, `skills.md`, `model-tiers.md`.
- Step 3: all four files exist.
- Step 4: `model-tiers.md` says it is the normative contract text since 2026-09-07; `skills.md` has the `required_skills:` convention heading and `## Authoring a Skill`; the two new files open with a Status line saying the text moved from `system-instructions.md` under ADR-026.

**Status:** [ ] Pass  [ ] Fail

**Implementation Reference:** Story 2 — `model-tiers.md` and `skills.md` were merged into (existing docs); `startup-update-awareness.md` and `recommendation-semantics.md` are new. The Startup Update Awareness trigger sentence and the Recommendation Semantics labeling rule stayed in the base. The spec says "five sections"; the story moved them in four commits (Skill authoring went with `required_skills:`).

**Notes:**

---

### Scenario 12: The ledger check is green at every move commit, and every move row is class `moved`

**Source:** Acceptance Criteria (AC-2.2) — Story 2

**Preconditions:**
- Setup A done. Uses its own worktree at `$UAT/wt2`.

**Steps:**
1. ```
   git worktree add -q --detach "$UAT/wt2" 25518d0
   for c in 25518d0 2b11f7d 30e987e 724e86a; do
     git -C "$UAT/wt2" checkout -q --detach "$c"
     printf '%s ' "$c"; python3 scripts/prune-ledger.py check --repo "$UAT/wt2" | tail -1
   done
   git worktree remove --force "$UAT/wt2"
   ```
2. `for c in 25518d0 2b11f7d 30e987e 724e86a; do git show --stat --format='%h %s' "$c" | grep -E '^[0-9a-f]{7} |system-instructions|ledger'; done`
3. `grep -c '^| 2026-09-07 | system-instructions.md | moved | .writ/docs/' .writ/decision-records/pruned-instructions-ledger.md`

**Expected Result:**
- Step 1 prints, in order: `ledger: 30 rows, removed: 30`, `56 / 56`, `82 / 82`, `102 / 102`, each with `re-added: 0`, and base bytes 23814, 20700, 17333, 15713. No finding lines appear.
- Step 2: each move commit touches both `system-instructions.md` and the ledger file (row in the same commit as the removal).
- Step 3: `102`.

**Status:** [ ] Pass  [ ] Fail

**Notes:**

---

### Scenario 13: The Prime Directive mirror stays in sync and the pointer paths resolve

**Source:** Acceptance Criteria (AC-2.3) — Story 2

**Preconditions:**
- Outside any sandbox.

**Steps:**
1. `bash scripts/eval.sh --check=prime-directive-sync; echo "exit=$?"` and read the report.
2. `bash scripts/eval.sh --check=referenced-paths; echo "exit=$?"` and read the report.
3. `for p in $(grep -o '\.writ/docs/[a-z-]*\.md' system-instructions.md); do test -f "$p" && echo "ok $p" || echo "MISSING $p"; done`
4. Prove the check scans the base (Setups A and C done; worktree reset):
   ```
   echo 'See `.writ/docs/no-such-doc.md` for nothing.' >> "$W/system-instructions.md"
   bash "$W/scripts/eval.sh" --check=referenced-paths; echo "exit=$?"
   sed -n '/^## referenced-paths/,$p' "$(ls -t "$W"/.writ/state/eval-*.md | head -1)"
   git -C "$W" checkout -q -- .
   ```

**Expected Result:**
- Steps 1 and 2: `PASS`, `Findings: 0`, `exit=0`.
- Step 3: four `ok` lines, no `MISSING`.
- Step 4: `exit=1`, `FAIL (1 finding(s))` with `` `system-instructions.md:83`: references '.writ/docs/no-such-doc.md', which does not exist and no command is recorded as creating. `` and `Findings: 1`.

**Status:** [ ] Pass  [ ] Fail

**Implementation Reference:** `scripts/eval.sh` `referenced_paths_files` — `check_referenced_paths` scans `commands/*.md` plus `system-instructions.md` and `commands/_preamble.md` (fixed 2026-09-25; DEV-008 recorded that it scanned `commands/*.md` only).

**Notes:**

---

### Scenario 14: Story 2's closing byte count is recorded and at most 16,000

**Source:** Acceptance Criteria (AC-2.4) — Story 2

**Preconditions:**
- Setup A done.

**Steps:**
1. ```
   git worktree add -q --detach "$UAT/wt2" f8daec1
   python3 scripts/prune-ledger.py measure --repo "$UAT/wt2" | tail -1
   git worktree remove --force "$UAT/wt2"
   ```
2. `grep -n "stage-2: Story 2" .writ/decision-log.md`
3. `grep -n "15,713" .writ/specs/2026-09-07-phase11-stage2-prune-the-base/user-stories/story-2-move-documentation-out.md | head -3`

**Expected Result:**
- Step 1: `total: 15713 bytes` (at or under 16,000).
- Step 2: one line naming `28,157 -> 15,713`.
- Step 3: the What Was Built totals line names 15,713 bytes.

**Status:** [ ] Pass  [ ] Fail

**Implementation Reference:** `f8daec1` is Story 2's close (named in Story 3's classification table).

**Notes:**

---

### Scenario 15: The only additions are four pointer lines and one logged rewording

**Source:** Acceptance Criteria (AC-2.5) — Story 2

**Preconditions:**
- None.

**Steps:**
1. `git diff --no-color -U0 cf84742 -- system-instructions.md commands/_preamble.md | grep '^+' | grep -v '^+++'`

**Expected Result:**
- Exactly five lines. Four start `+See `.writ/docs/…`. The fifth is `+When first invoked in a session, run a quiet Writ update awareness check before any command-specific workflow. …`, the 2026-09-25 rewording (Honest Note 4).
- Confirm the rewording is logged: `grep -c '^| 2026-09-25 | system-instructions.md | duplicate |' .writ/decision-records/pruned-instructions-ledger.md` prints `1`, and that row's text is the old line ending "before session auto-orientation or any command-specific workflow. …".
- No other line was added, so no other kept line was reflowed or reworded (a reworded line shows as an added line here).

**Status:** [ ] Pass  [ ] Fail

**Notes:**

---

### Scenario 16: The governor pins followed the moved text

**Source:** Edge Case (DEV-005, DEV-006) — Story 2

**Preconditions:**
- Outside any sandbox. `uv` on PATH.

**Steps:**
1. `bash scripts/eval.sh --check=recommendation-semantics; echo "exit=$?"` and read the report.
2. `uv run --python 3.9 pytest -q scripts/tests/test_governor_enforcement.py -k MechanismRecordTests`

**Expected Result:**
- Step 1: `PASS`, `Findings: 0`. The moved bullets are pinned in `.writ/docs/recommendation-semantics.md`, the labeling rule in the base.
- Step 2: `4 passed`. The skills-convention pins read `.writ/docs/skills.md`.

**Status:** [ ] Pass  [ ] Fail

**Notes:**

---

### Scenario 17: An installed project receives the moved docs

**Source:** Experience Design (Entry point) — Story 2

**Preconditions:**
- Setup A done.

**Steps:**
1. ```
   mkdir -p "$UAT/proj" && git -C "$UAT/proj" init -q
   (cd "$UAT/proj" && bash "$OLDPWD/scripts/install.sh" --dry-run --platform claude) | grep -E 'model-tiers|skills\.md|startup-update-awareness|recommendation-semantics'
   ls -A "$UAT/proj"
   ```

**Expected Result:**
- Four lines under "Writ docs": `✨ New: .writ/docs/model-tiers.md`, `recommendation-semantics.md`, `skills.md`, `startup-update-awareness.md`.
- `ls -A` shows only `.git` (dry run wrote nothing).

**Status:** [ ] Pass  [ ] Fail

**Notes:**

---

## Story 3: Cut Behavior Requests

### Scenario 18: The classification table covers the base with exactly three classes

**Source:** Acceptance Criteria (AC-3.1) — Story 3

**Preconditions:**
- None.

**Steps:**
1. `S=.writ/specs/2026-09-07-phase11-stage2-prune-the-base/user-stories/story-3-cut-behavior-requests.md; grep -n '^| File | Section' "$S"`
2. `awk -F'|' '/^\| `(system-instructions|commands\/_preamble)\.md` \|/ {gsub(/ /,"",$6); print $6}' "$S" | sort | uniq -c`
3. Open the table in the story's What Was Built and compare the line ranges to `git show f8daec1:system-instructions.md | wc -l` and `git show f8daec1:commands/_preamble.md | wc -l`.

**Expected Result:**
- Step 1: the header `| File | Section | Lines (f8daec1) | Line count | Class | Action |`.
- Step 2: four class values. `behavior-request`, `environment-fact`, `human-boundary` (the three classes), plus `duplicate` on 4 rows.
- Step 3: the ranges run contiguously from line 1 to 181 for `system-instructions.md` and 1 to 95 for `_preamble.md`.

**Status:** [ ] Pass  [ ] Fail

**Notes:** AC-3.1 (amended 2026-09-25) allows the three research classes plus the marker `duplicate` on removed-duplicate rows, so Step 2's four values meet it.

---

### Scenario 19: Every cut line has a `behavior-request` or `duplicate` row with a short reason

**Source:** Acceptance Criteria (AC-3.2) — Story 3

**Preconditions:**
- None.

**Steps:**
1. `for c in moved behavior-request duplicate; do echo "$c $(grep -c "^| [0-9-]* | [^|]* | $c |" .writ/decision-records/pruned-instructions-ledger.md)"; done`
2. ```
   python3 -c "
   import re
   rows=[l for l in open('.writ/decision-records/pruned-instructions-ledger.md') if re.match(r'^\| \d{4}-',l)]
   br=[re.split(r'(?<!\\\\)\|',l)[4].strip() for l in rows if ' | behavior-request | ' in l]
   print(len(br), 'max reason length', max(len(r) for r in br))"
   ```
3. `grep -nE '^(## Identity & Approach|## Command Execution Protocol|### Judgment Principles|### Prose|## Session Auto-Orientation|## Tool Selection|## Knowledge Context|## Adapter Neutrality)' system-instructions.md commands/_preamble.md; echo "grep-exit=$?"`
4. `grep -c '^## File Organization' system-instructions.md commands/_preamble.md`

**Expected Result:**
- Step 1: `moved 102`, `behavior-request 67`, `duplicate 19` (188 total). Eighteen `duplicate` rows are from Story 3; the nineteenth is the 2026-09-25 rewording (Honest Note 4).
- Step 2: `67 max reason length 120` (at the 120-character limit, not over).
- Step 3: no matches; `grep-exit=1`.
- Step 4: `system-instructions.md:0`, `commands/_preamble.md:1` (the surviving copy).

**Status:** [ ] Pass  [ ] Fail

**Notes:**

---

### Scenario 20: The protected sections are byte-identical to `cf84742`

**Source:** Acceptance Criteria (AC-3.3) — Story 3

**Preconditions:**
- None.

**Steps:**
1. `diff <(git show cf84742:system-instructions.md | sed -n '/^## Prime Directive/,/^### Recommendation Semantics/p') <(sed -n '/^## Prime Directive/,/^### Recommendation Semantics/p' system-instructions.md) && echo SAME`
2. `diff <(git show cf84742:commands/_preamble.md | sed -n '/^## Plan Mode Integrity/,/^## Artifact Integrity/p') <(sed -n '/^## Plan Mode Integrity/,/^## Artifact Integrity/p' commands/_preamble.md) && echo SAME`
3. `diff <(git show cf84742:commands/_preamble.md | sed -n '/^## Artifact Integrity/,/^## Tool Selection/p' | sed '$d' | grep -v '^$') <(sed -n '/^## Artifact Integrity/,$p' commands/_preamble.md | grep -v '^$') && echo SAME`

**Expected Result:**
- Each step prints `SAME` with no diff output.
- Step 1 covers Hard Constraints and the Recommended Delivery Exception. Step 2 covers Plan Mode Integrity, the Narrow Recommended-Delivery Exception, User Challenge, Autonomy Gate Classes, and File Organization. Step 3 covers Artifact Integrity (non-blank lines; its trailing blank line became the file end, DEV-002).

**Status:** [ ] Pass  [ ] Fail

**Notes:**

---

### Scenario 21: One Fable 5.1 line per adapter; the Cursor rule matches the base

**Source:** Acceptance Criteria (AC-3.4) — Story 3

**Preconditions:**
- None.

**Steps:**
1. `for f in adapters/claude-code.md adapters/cursor.md adapters/codex.md adapters/openclaw.md; do echo "$f whole=$(grep -c 'Fable 5.1' $f) section=$(awk '/^## Model-specific/{f=1;next} f&&/^## /{f=0} f' $f | grep -c 'Fable 5.1')"; done`
2. `sed -n '/^## Model-specific/,$p' adapters/claude-code.md`
3. `cmp system-instructions.md cursor/writ.mdc && echo IDENTICAL`

**Expected Result:**
- Step 1: `section=1` for all four; this is AC-3.4's proof as amended 2026-09-25. `whole=1` for claude-code, codex, openclaw; `whole=3` for cursor (DEV-009, an older verification record in that file names the model twice), which the amended AC allows.
- Step 2: one line saying Claude Fable 5.1 may serialize independent tool calls and should batch them, and that this is the only model-specific line the adapter carries.
- Step 3: `IDENTICAL`.

**Status:** [ ] Pass  [ ] Fail

**Notes:**

---

### Scenario 22: The base is under the cap and the cap is blocking

**Source:** Acceptance Criteria (AC-3.5) — Story 3

**Preconditions:**
- Outside any sandbox.

**Steps:**
1. `python3 scripts/prune-ledger.py check --repo . --cap-blocking; echo "exit=$?"`
2. `grep -Fxc '<!-- cap: blocking -->' .writ/decision-records/pruned-instructions-ledger.md`
3. `wc -c system-instructions.md commands/_preamble.md`
4. `bash scripts/eval.sh; echo "exit=$?"`, then `sed -n '/^## Summary/,$p' "$(ls -t .writ/state/eval-*.md | head -1)"`

**Expected Result:**
- Step 1: `base: 9676 bytes (cap 10000), ledger: 188 rows, removed: 188, re-added: 0`; `exit=0`.
- Step 2: `1`.
- Step 3: `4572`, `5104`, total `9676`.
- Step 4 (about 2 minutes): `Findings: 0`, `Run errors: 0`, `exit=0`.

**Status:** [ ] Pass  [ ] Fail

**Notes:**

---

### Scenario 23: Removing a protected line now blocks, naming the file and text

**Source:** Error Map (`removed_not_in_ledger`); Experience Design (Error experience) — Story 3

**Preconditions:**
- Setups A and C done. Worktree reset: `git -C "$W" checkout -q -- .`

**Steps:**
1. Delete one Hard Constraints line in the worktree only:
   ```
   grep -vx 'These apply to every command, agent, and session. No exceptions.' "$W/system-instructions.md" > "$UAT/si.tmp" && mv "$UAT/si.tmp" "$W/system-instructions.md"
   python3 scripts/prune-ledger.py check --repo "$W" --cap-blocking; echo "exit=$?"
   ```
2. `git -C "$W" checkout -q -- .`

**Expected Result:**
- Step 1: `removed_not_in_ledger: system-instructions.md: These apply to every command, agent, and session. No exceptions.`, summary `base: 9611 bytes (cap 10000), ledger: 188 rows, removed: 189, re-added: 0`; `exit=1`.
- Your main checkout is unchanged (`git status --short system-instructions.md` prints the same as before Step 1: nothing once the 2026-09-25 fixes are committed, ` M system-instructions.md` until then).

**Status:** [ ] Pass  [ ] Fail

**Notes:**

---

### Scenario 24: Re-adding a cut line is a finding naming the ledger date

**Source:** Edge Case (line removed then re-added; Business Rule 2) — Story 3

**Preconditions:**
- Setups A and C done. Worktree reset.

**Steps:**
1. ```
   echo '## Session Auto-Orientation' >> "$W/system-instructions.md"
   python3 scripts/prune-ledger.py check --repo "$W" --cap-blocking; echo "exit=$?"
   git -C "$W" checkout -q -- .
   ```

**Expected Result:**
- `ledger_text_reappeared: 2026-09-07 system-instructions.md: ## Session Auto-Orientation`, summary `base: 9704 bytes (cap 10000), ledger: 188 rows, removed: 187, re-added: 1`; `exit=1`.

**Status:** [ ] Pass  [ ] Fail

**Notes:**

---

### Scenario 25: Growing the base past 10,000 bytes fails `eval.sh`

**Source:** Error Map (`over_cap` as a finding after the flip) — Story 3

**Preconditions:**
- Setups A and C done. Worktree reset. Outside any sandbox.

**Steps:**
1. ```
   head -c 400 /dev/zero | tr '\0' 'x' >> "$W/commands/_preamble.md"; echo >> "$W/commands/_preamble.md"
   bash "$W/scripts/eval.sh" --check=pruned-base; echo "exit=$?"
   sed -n '/^## pruned-base/,$p' "$(ls -t "$W"/.writ/state/eval-*.md | head -1)"
   git -C "$W" checkout -q -- .
   ```

**Expected Result:**
- `exit=1`. The report shows `FAIL (1 finding(s))` with `` `pruned-base:over_cap`: 10077 bytes > cap 10000 `` and `Findings: 1`.
- The remediation reads "Bring system-instructions.md + commands/_preamble.md under the cap: cut more lines (each with a ledger row) or move reference material out to a doc the base points to; see ADR-026."
- The note `NOTE [pruned-base]: base: 10077 bytes (cap 10000), ledger: 188 rows, removed: 188, re-added: 0`.

**Status:** [ ] Pass  [ ] Fail

**Notes:**

---

## Story 4: Gate Verification Markers and Provenance Check

### Scenario 26: The `gates:` block names all ten gates with truthful sources

**Source:** Acceptance Criteria (AC-4.1) — Story 4

**Preconditions:**
- Setup A done.

**Steps:**
1. As Story 4 shipped:
   ```
   git show e6be367:commands/implement-story.md > "$UAT/is-story4.md"
   python3 scripts/verdict-provenance.py check --command "$UAT/is-story4.md" --repo .; echo "exit=$?"
   ```
2. As it is today: `python3 scripts/verdict-provenance.py check --command commands/implement-story.md; echo "exit=$?"`
3. `sed -n '/^gates:/,/^---/p' commands/implement-story.md`

**Expected Result:**
- Step 1: `note: prose_only_count: 8 (cap 2)`, `gates: 10 entries, headings: 10, script: 2, prose-only: 8, findings: 0`; `exit=0`. This matches AC-4.1 as written.
- Step 2: `note: prose_only_count: 2 (cap 2)`, `gates: 10 entries, headings: 10, script: 8, prose-only: 2, findings: 0`; `exit=0`. Stage 2b mechanized six gates after this spec.
- Step 3: ten entries with ids `gate0_arch`, `gate0_5_boundary`, `gate1_coding`, `gate2_build`, `gate2_5_surface`, `gate3_review`, `gate3_5_drift`, `gate4_tests`, `gate4_5_visual`, `gate5_docs`. `gate2_build` is `scripts/build-smoke.py` and `gate4_tests` is `scripts/test-integrity.py`.

**Status:** [ ] Pass  [ ] Fail

**Notes:**

---

### Scenario 27: Each of the six drift types is a finding naming the file and gate

**Source:** Acceptance Criteria (AC-4.2); Error Map (technical-spec §5 findings) — Story 4

**Preconditions:**
- Setup A done.

**Steps:**
1. Define a fixture builder (two headings, Gate 0 and Gate 2) and run each drift:
   ```
   mk(){ f="$UAT/$1.md"; printf -- '---\nname: x\ngates:\n%b---\n\n#### Gate 0: A\n\n#### Gate 2: B\n' "$2" > "$f"; echo "--- $1"; python3 scripts/verdict-provenance.py check --command "$f" --repo . | head -1; }
   mk clean    '  - id: gate0_arch\n    script: scripts/arch-check.py\n  - id: gate2_build\n    verification: prose-only\n'
   mk noentry  '  - id: gate0_arch\n    script: scripts/arch-check.py\n'
   mk extra    '  - id: gate0_arch\n    script: scripts/arch-check.py\n  - id: gate2_build\n    verification: prose-only\n  - id: gate5_docs\n    verification: prose-only\n'
   mk nosource '  - id: gate0_arch\n  - id: gate2_build\n    verification: prose-only\n'
   mk both     '  - id: gate0_arch\n    script: scripts/arch-check.py\n    verification: prose-only\n  - id: gate2_build\n    verification: prose-only\n'
   mk missing  '  - id: gate0_arch\n    script: scripts/nope.py\n  - id: gate2_build\n    verification: prose-only\n'
   mk unknown  '  - id: gate0_arch\n    script: scripts/arch-check.py\n  - id: gate2_build\n    verification: manual\n'
   ```
2. Check the exit code of one drift: `python3 scripts/verdict-provenance.py check --command "$UAT/noentry.md" --repo . > /dev/null; echo "exit=$?"`

**Expected Result:**
- `clean`: first line `note: prose_only_count: 1 (cap 2)` (no finding).
- `noentry`: `heading_without_entry: <path>/noentry.md gate2_build (#### Gate heading has no gates: entry)`
- `extra`: `entry_without_heading: <path>/extra.md gate5_docs (gates: entry has no #### Gate heading)`
- `nosource`: `entry_without_source: <path>/nosource.md gate0_arch (neither script nor verification)`
- `both`: `entry_both_sources: <path>/both.md gate0_arch (both script and verification)`
- `missing`: `script_missing: <path>/missing.md gate0_arch (scripts/nope.py not found under .)`
- `unknown`: `unknown_verification_value: <path>/unknown.md gate2_build ('manual' is not 'prose-only')`
- Step 2: `exit=1`.

**Status:** [ ] Pass  [ ] Fail

**Notes:**

---

### Scenario 28: Too many prose-only gates is a note by default and a finding when blocking

**Source:** Acceptance Criteria (AC-4.3) — Story 4

**Preconditions:**
- Setup A done.

**Steps:**
1. ```
   printf -- '---\nname: x\ngates:\n  - id: gate0_arch\n    verification: prose-only\n  - id: gate1_coding\n    verification: prose-only\n  - id: gate2_build\n    verification: prose-only\n---\n\n#### Gate 0: A\n\n#### Gate 1: B\n\n#### Gate 2: C\n' > "$UAT/three.md"
   python3 scripts/verdict-provenance.py check --command "$UAT/three.md" --repo .; echo "exit=$?"
   python3 scripts/verdict-provenance.py check --command "$UAT/three.md" --repo . --prose-only-blocking; echo "exit=$?"
   ```

**Expected Result:**
- First run: `note: prose_only_count: 3 (cap 2)`, summary `findings: 0`; `exit=0`.
- Second run: `prose_only_count: 3 (cap 2)` with no `note:` prefix, summary `findings: 1`; `exit=1`.

**Status:** [ ] Pass  [ ] Fail

**Notes:**

---

### Scenario 29: `eval.sh` runs the `verdict-provenance` check

**Source:** Acceptance Criteria (AC-4.4) — Story 4

**Preconditions:**
- Outside any sandbox. `uv` on PATH.

**Steps:**
1. `bash scripts/eval.sh --check=verdict-provenance; echo "exit=$?"` and read the report.
2. `sed -n '/^check_verdict_provenance()/,/^}/p' scripts/eval.sh | grep -n 'check --command'`
3. `bash scripts/tests/test_eval_verdict_provenance.sh; echo "exit=$?"`
4. `uv run --python 3.9 pytest -q scripts/tests/test_verdict_provenance.py`

**Expected Result:**
- Step 1: `PASS`, notes `prose_only_count: 2 (cap 2)` and `Metrics: gates: 10 entries, headings: 10, script: 8, prose-only: 2, findings: 0`, `Findings: 0`; `exit=0`.
- Step 2: the invocation passes `--prose-only-blocking`. Story 4 shipped it without that flag; Stage 2b added it (Honest Note 1).
- Step 3: `All 7 verdict-provenance check assertions passed.`; `exit=0`.
- Step 4: `27 passed`.

**Status:** [ ] Pass  [ ] Fail

**Notes:**

---

### Scenario 30: Gate 4.5 has no percentage thresholds and the other frontmatter checks stay green

**Source:** Acceptance Criteria (AC-4.5) — Story 4

**Preconditions:**
- Outside any sandbox.

**Steps:**
1. `sed -n '/^#### Gate 4.5/,/^#### Gate 5/p' commands/implement-story.md | grep -c '%'`
2. `sed -n '/^#### Gate 4.5/,/^#### Gate 5/p' commands/implement-story.md | grep -o 'SOFT PASS\|\*\*PASS\*\*\|\*\*FAIL\*\*' | sort -u`
3. `git show e6be367~1:commands/implement-story.md | sed -n '/^#### Gate 4.5/,/^#### Gate 5/p' | grep '%'`
4. `bash scripts/eval.sh --check=required-sections; echo "exit=$?"` and `bash scripts/eval.sh --check=loop-bounds; echo "exit=$?"`

**Expected Result:**
- Step 1: `0`.
- Step 2: `**FAIL**`, `**PASS**`, `SOFT PASS`.
- Step 3 (before the story): the old Results line with `≥85% match`, `≥70% match`, `<70% match`.
- Step 4: both `exit=0`, `Findings: 0`.

**Status:** [ ] Pass  [ ] Fail

**Notes:**

---

### Scenario 31: A missing command file or a file without frontmatter exits 2

**Source:** Error Map (exit codes as §1) — Story 4

**Preconditions:**
- Setup A done.

**Steps:**
1. `python3 scripts/verdict-provenance.py check --command "$UAT/nope.md"; echo "exit=$?"`
2. `printf '# no frontmatter\n' > "$UAT/nofm.md"; python3 scripts/verdict-provenance.py check --command "$UAT/nofm.md"; echo "exit=$?"`

**Expected Result:**
- Step 1: stderr `check: error: --command <path>/nope.md does not exist`; `exit=2`.
- Step 2: stderr `check: error: <path>/nofm.md: file does not open with a --- frontmatter fence`; `exit=2`.

**Status:** [ ] Pass  [ ] Fail

**Notes:**

---

### Scenario 32: An empty `gates:` block gives one finding per gate heading

**Source:** Shadow Path (empty input) — Story 4

**Preconditions:**
- Setup A done.

**Steps:**
1. `printf -- '---\nname: x\ngates:\n---\n\n#### Gate 0: A\n\n#### Gate 2: B\n' > "$UAT/empty.md"; python3 scripts/verdict-provenance.py check --command "$UAT/empty.md" --repo .; echo "exit=$?"`

**Expected Result:**
- Two `heading_without_entry` lines (`gate0_arch`, `gate2_build`), the note `prose_only_count: 0 (cap 2)`, summary `gates: 0 entries, headings: 2, … findings: 2`; `exit=1`.

**Status:** [ ] Pass  [ ] Fail

**Notes:**

---

## Story 5: Baseline Re-run and Keep-or-Revert

### Scenario 33: The re-run file reuses Stage 1's selection and criteria verbatim

**Source:** Acceptance Criteria (AC-5.1) — Story 5

**Preconditions:**
- None.

**Steps:**
1. ```
   python3 -c "
   import json
   a=json.load(open('.writ/eval/baselines/2026-09-06-claude-fable-5-1.json')); b=json.load(open('.writ/eval/baselines/2026-09-07-claude-fable-5-1.json'))
   print('selection', a['selection']==b['selection'], 'criteria', a['criteria']==b['criteria'], 'runs', len(b['runs']), 'runs_per_story', b['runs_per_story'])"
   ```

**Expected Result:**
- `selection True criteria True runs 8 runs_per_story 2`.

**Status:** [ ] Pass  [ ] Fail

**Notes:**

---

### Scenario 34: The re-run file validates and the eval check is clean

**Source:** Acceptance Criteria (AC-5.2) — Story 5

**Preconditions:**
- Outside any sandbox.

**Steps:**
1. `python3 scripts/pipeline-baseline.py validate .writ/eval/baselines/2026-09-07-claude-fable-5-1.json; echo "exit=$?"`
2. `bash scripts/eval.sh --check=pipeline-baseline; echo "exit=$?"` and read the report.

**Expected Result:**
- Step 1: no output; `exit=0`.
- Step 2: `PASS`, `Findings: 0`; `exit=0`.

**Status:** [ ] Pass  [ ] Fail

**Notes:** This checks the committed evidence. The `run` step itself (eight headless Fable 5.1 replays under `nohup`, about $180) is not repeated in UAT.

---

### Scenario 35: `compare` prints 2/2 exit criteria on all four stories

**Source:** Acceptance Criteria (AC-5.3); Experience Design (Moment of truth) — Story 5

**Preconditions:**
- None.

**Steps:**
1. `python3 scripts/pipeline-baseline.py compare .writ/eval/baselines/2026-09-06-claude-fable-5-1.json .writ/eval/baselines/2026-09-07-claude-fable-5-1.json > "$UAT/compare.txt"; echo "exit=$?"`
2. `grep exit_criteria "$UAT/compare.txt"`
3. `grep cost_usd "$UAT/compare.txt"`

**Expected Result:**
- Step 1: `exit=0` (no refusal).
- Step 2: four rows, one per story (event-creation, settlement-view, fee-sharing, messaging-migration), each `2/2  2/2  0`.
- Step 3: four rows with deltas of about +1.98, −1.45, −5.35, +0.37, matching the compare table in Story 5's What Was Built.

**Status:** [ ] Pass  [ ] Fail

**Notes:**

---

### Scenario 36: The keep decision is recorded with its numbers

**Source:** Acceptance Criteria (AC-5.4, AC-5.5) — Story 5

**Preconditions:**
- None.

**Steps:**
1. `grep -n "^2026-09-08 stage-2:" .writ/decision-log.md`
2. `grep -n "Decision: KEEP" .writ/specs/2026-09-07-phase11-stage2-prune-the-base/user-stories/story-5-baseline-rerun-keep-or-revert.md`
3. `python3 -c "import json; d=json.load(open('.writ/specs/2026-09-07-phase11-stage2-prune-the-base/user-stories/story-5-failed-first-attempts.json')); print(len(d))"`
4. `git log --oneline -1 -- .writ/eval/baselines/2026-09-07-claude-fable-5-1.json`

**Expected Result:**
- Step 1: one line stating 8/8 vs Stage 1's 8/8, $178.69 vs $187.60 (−4.7%), cache-creation −36%, and that the cut is KEPT.
- Step 2: one match.
- Step 3: `2` (the two driver-killed first attempts that were retried once each).
- Step 4: a commit exists (the baseline JSON is committed).

**Status:** [ ] Pass  [ ] Fail

**Notes:**

---

### Scenario 37: `compare` refuses when the selection differs

**Source:** Edge Case (differing `selection`) — Story 5

**Preconditions:**
- Setup A done.

**Steps:**
1. ```
   python3 -c "
   import json,sys; b=json.load(open('.writ/eval/baselines/2026-09-07-claude-fable-5-1.json')); b['selection'][0]['parent_sha']='0'*40; json.dump(b,open(sys.argv[1],'w'))" "$UAT/bad-selection.json"
   python3 scripts/pipeline-baseline.py compare .writ/eval/baselines/2026-09-06-claude-fable-5-1.json "$UAT/bad-selection.json"; echo "exit=$?"
   ```

**Expected Result:**
- Prints `compare: selection mismatch: first differing story is .writ/specs/archive/2026-07-24-per-event-fee-revenue-model/user-stories/story-2-event-creation-payment-flow.md`; `exit=2`. No metric rows are printed.

**Status:** [ ] Pass  [ ] Fail

**Notes:**

---

### Scenario 38: The revert path would resolve exactly Stories 2–3's commits

**Source:** Error Map (re-run below 8/8 → revert Stories 2–3) — Story 5

**Preconditions:**
- None. `revert-resolve.py` is read-only; it changes nothing.

**Steps:**
1. `python3 scripts/revert-resolve.py story 2 --spec 2026-09-07-phase11-stage2-prune-the-base`
2. `python3 scripts/revert-resolve.py story 3 --spec 2026-09-07-phase11-stage2-prune-the-base`
3. For reference, the commits that actually changed the base: `git log --oneline 25518d0~1..2fc26f9 -- system-instructions.md commands/_preamble.md`

**Expected Result:**
- Step 1 lists, newest first: `e1a60abd [recorded]` (Story 2's completion commit), then `724e86a7`, `30e987ef`, `2b11f7d6`, `25518d0d`, each `[task-subject]` (the four move commits). Base (hard-reset target) `272da3d8…`. No commit from another spec; `exit=0`.
- Step 2 lists `2fc26f93 [recorded]` (Story 3's completion commit), then `85962814`, `99c1b0e8`, `ece8cc5f`, `11f590b0`, `f6fa3af5`, each `[task-subject]` (the cut commits). Base `f8daec1e…` (Story 2's close). No commit from another spec; `exit=0`.
- Step 3 lists the seven Story 2/3 task commits that touched the base; every one appears in Step 1 or Step 2. Step 2 also lists `99c1b0e` and `8596281`, which touched only the adapters (`99c1b0e`) and the ledger marker plus `cursor/writ.mdc` (`8596281`), not the base.

**Status:** [ ] Pass  [ ] Fail

**Implementation Reference:** technical-spec §6 (revert path via `/revert` and `scripts/revert-resolve.py`); Story 3's What Was Built names the contiguous range `25518d0` through its completion commit. `revert-resolve.py` scopes `Ref:` footers to the spec and resolves `Story N (N.x):` subjects inside the spec's commit range (`task-subject`, fixed 2026-09-25). The resolver is checked; `/revert` itself is not run (Honest Note 2).

**Notes:**

---

## Pending Stories

None. All five stories are Completed ✅.
