# UAT Plan: Harness Cuts

> **Generated:** 2026-10-21
> **Spec:** `.writ/specs/2026-10-20-harness-cuts/`
> **Stories Covered:** 4 of 4 completed
> **Total Scenarios:** 32
> **Verification recipe:** does not apply. Writ has no running app, so no `.writ/docs/app-verification.md` was drafted, saved, or bound. Every scenario is `human — no recipe`. The `**Automated Test:**` line on each scenario names the committed test that already asserts the same behavior, if any.

> **Known issue at generation (2026-10-21, `7922922`):** the guard test fails on the phase branch. `scripts/tests/test_harness_cuts.py::LeanFilesGoneTest::test_ac_1_1_ac_2_1_guard_grep_is_empty_repo_wide` finds one line: `.writ/specs/2026-10-20-ci-and-update-integrity/uat-plan.md:609` ("… or an unshipped `*.lean.md` command."). That UAT plan was committed on the phase branch (`7e79861`) while this spec ran in its lane, and the lane merge (`7922922`) brought the two together. Full pytest on `7922922`: `1 failed, 2606 passed, 2 skipped`. Scenarios 1 (repo-wide part), 5, and 7 fail until that line is reworded or the guard excludes that folder. This plan does not fix it.

## How to Use This Plan

1. Work through scenarios in order (they're grouped by story, ordered by priority)
2. For each scenario, follow the steps exactly as written
3. Mark Pass or Fail — add notes for any unexpected behavior
4. Scenarios marked Fail should be filed as issues or fed back to the spec
5. A feature passes UAT when all scenarios pass (or failures are accepted as known limitations)

**Conventions for this plan:**

- **Never run `install.sh` or `update.sh` in the Writ repo.** `.claude/` and `.cursor/` there are symlinks into the source (Business Rule 10). Every install and update below runs from a committed copy at `$SRC` into a temp folder under `$W`.
- Suite runs, eval checks, and deliberate breakage happen in a clone at `$CL`, never in `$REPO`.
- Run the plan in `bash` on macOS (`shasum`, `sed -i ''`), outside any sandbox. The steps run `git init` and `git commit` in temp folders.
- Paste this setup block once per shell:

  ```bash
  REPO=/Users/asellke/Projects/writ          # the Writ checkout; read from, never installed into
  W=$(mktemp -d "${TMPDIR:-/tmp}/writ-uat-cuts.XXXXXX")
  cd "$W"   # run every helper from the temp folder: an empty path then fails instead of writing to the Writ repo
  h()      { shasum -a 256 "$1" | cut -d' ' -f1; }
  digest() { (cd "$1" && find . -type f -exec shasum -a 256 {} + | LC_ALL=C sort | shasum -a 256 | cut -d' ' -f1); }
  # Committed copy of the working tree. install.sh and update.sh run from here.
  SRC="$W/src"; mkdir -p "$SRC"
  (cd "$REPO" && tar --exclude=.git --exclude=.cursor --exclude=.claude --exclude=.codex \
     --exclude=.writ --exclude='.writ-lanes-*' --exclude=__pycache__ --exclude=.venv \
     --exclude=.pytest_cache -cf - .) | (cd "$SRC" && tar -xf -)
  mkdir -p "$SRC/.writ/docs" && cp "$REPO"/.writ/docs/*.md "$SRC/.writ/docs/"
  git -C "$SRC" init -q -b main
  git -C "$SRC" -c user.name=t -c user.email=t@example.invalid add -A
  git -C "$SRC" -c user.name=t -c user.email=t@example.invalid commit -q -m source
  # Clone of the committed repo, for suite runs and deliberate breakage.
  CL="$W/clone"; git clone -q "$REPO" "$CL"
  # inst <project> <claude|cursor|codex> [flags]; upd <project> <platform> [flags]
  inst() { local p="$1" pf="$2"; shift 2; mkdir -p "$p" && (cd "$p" && bash "$SRC/scripts/install.sh" --platform "$pf" --no-commit "$@"); }
  upd()  { local p="$1" pf="$2"; shift 2; (cd "$p" && WRIT_REPO="${UPSTREAM:-$SRC}" bash "$SRC/scripts/update.sh" --platform "$pf" --no-commit "$@"); }
  # mline <project> <platform> <file under project> <manifest path>: record the file's hash the way an older install did.
  mline() { printf '%s  %s\n' "$(h "$1/$3")" "$4" >> "$1/.$2/.writ-manifest"; }
  # plant_lean <claude project> <name> [edit]: an old lean command with its manifest line, optionally edited after.
  plant_lean() { printf '# old %s from an earlier install\n' "$2" > "$1/.claude/commands/$2"
    mline "$1" claude ".claude/commands/$2" "commands/$2"; [ "${3:-}" != edit ] || printf 'local edit\n' >> "$1/.claude/commands/$2"; }
  # plant_stage <project> <platform> <path> [edit]: an upstream copy with its manifest line, optionally edited after.
  plant_stage() { mkdir -p "$1/$(dirname "$3")" && cp "$SRC/$3" "$1/$3"
    mline "$1" "$2" "$3" "$3"; [ "${4:-}" != edit ] || printf '\n# local edit\n' >> "$1/$3"; }
  HL=scripts/recommend-state.py
  SD=.writ/docs/recommended-delivery-state-format.md
  ```

- **Why some scenarios plant an extra unmodified file.** When the only difference is a kept file, `update.sh` prints "Already up to date" and exits before it rewrites the manifest. A manifest check after such a run proves nothing. Scenarios that check a kept file's baseline also plant one unmodified stale file, so run 1 removes something and rewrites the manifest.
- Manifests: Claude Code `.claude/.writ-manifest`, Cursor `.cursor/.writ-manifest`, Codex `.codex/.writ-manifest`. Each line is `<sha256>  <path>`.
- Expected output was observed on 2026-10-21 against `7922922` when this plan was generated. Hashes, versions, temp paths, and counts that grow with the repo (33 commands, 35 shipped scripts, 27 shipped docs) will differ later.
- When done: `rm -rf "$W"`.
- **Automated Test line:** names the test in `scripts/tests/` (or the `eval.sh` check) that asserts the behavior, `partial` when a test covers part of it, or `none — manual only`. CI runs pytest, every bash test, and `eval.sh` on each PR.

## Coverage Summary

| Story | Status | Scenarios | Source Breakdown |
|-------|--------|-----------|-----------------|
| Story 1: Delete the Lean Siblings and Their Install Logic | ✅ Covered | 6 | AC: 5, Errors: 1, Shadow: 0, Edge: 0 |
| Story 2: Remove the Lean Code Paths from the Scripts | ✅ Covered | 7 | AC: 5, Errors: 0, Shadow: 1, Edge: 0, Experience: 1 |
| Story 3: Remove the ADR-025 No-Op Lines and Correct the /ship Description | ✅ Covered | 4 | AC: 4, Errors: 0, Shadow: 0, Edge: 0 |
| Story 4: Make Recommended-Delivery Staging Dev-Only | ✅ Covered | 15 | AC: 7, Errors: 1, Shadow: 5, Edge: 1, Experience: 1 |

Error-map, shadow-path, edge-case, and state-catalog items that a scenario already exercises are folded into it and named on its **Source** line, not counted twice. Shadow paths shared by Stories 1 and 4 (update with no manifest, empty manifest, failed clone) and the `--force` edge case are listed under Story 4 and plant both kinds of cut file.

**Automated vs. manual:** 20 scenarios are asserted by a committed test, 4 partly, 8 are manual only. See the table at the end.

---

## Story 1: Delete the Lean Siblings and Their Install Logic

### Scenario 1: No lean command file or lean skip logic remains

**Source:** Acceptance Criteria — Story 1 (AC-1.1)
**Feature:** none
**Verification:** human — no recipe
**Automated Test:** `scripts/tests/test_harness_cuts.py` (`LeanFilesGoneTest`, `LeanSkipLogicGoneTest`)

**Preconditions:**
- Setup block pasted.

**Steps:**
1. `cd "$REPO" && ls commands/*.lean.md; echo "exit $?"`
2. `git grep -n -e WRIT_HARNESS_LEAN -e '\.lean\.md' -- commands README.md scripts/install.sh scripts/update.sh .writ/docs .writ/issues; echo "exit $?"`
3. `grep -c is_unshipped_lean_sibling scripts/install.sh scripts/update.sh`

**Expected Result:**
- Step 1: `ls: commands/*.lean.md: No such file or directory`, `exit 1`.
- Step 2: no output, `exit 1`.
- Step 3: `scripts/install.sh:0` and `scripts/update.sh:0`.

**Status:** [x] Pass  [ ] Fail

**Notes:** The Story 1 paths are clean. The repo-wide version of this grep (Scenario 7) currently fails on a path outside these; see Known Issue.

agent-run 2026-10-21 @ b850e66: step 1 `ls: commands/*.lean.md: No such file or directory`, `exit 1`; step 2 no output, `exit 1`; step 3 `scripts/install.sh:0`, `scripts/update.sh:0`.

**Implementation Reference:** Story 1 — five `commands/*.lean.md` deleted; `is_unshipped_lean_sibling` removed from both scripts, including the `write_copy_manifest` loops (DEV-001).

---

### Scenario 2: A Claude Code install lists, copies, and records no lean file

**Source:** Acceptance Criteria — Story 1 (AC-1.2); Error Map (Fresh install: a cut file ships anyway); Experience Design (State: fresh install)
**Feature:** none
**Verification:** human — no recipe
**Automated Test:** `scripts/tests/test_install_update_harness_cuts.sh` (AC-1.2 blocks)

**Preconditions:**
- Setup block pasted.

**Steps:**
1. `inst "$W/s2-dry" claude --dry-run > "$W/s2-dry.txt" 2>&1; echo "exit $?"; grep 'Commands:  ' "$W/s2-dry.txt"; grep -c '\.lean\.md' "$W/s2-dry.txt"; grep 'commands/implement-story.md' "$W/s2-dry.txt"; find "$W/s2-dry" -mindepth 1 | wc -l`
2. `inst "$W/s2" claude > "$W/s2.txt" 2>&1; echo "exit $?"`
3. `ls "$W/s2/.claude/commands" | grep -c '\.lean\.md$'; grep -c '\.lean\.md$' "$W/s2/.claude/.writ-manifest"; ls "$W/s2/.claude/commands" | wc -l; ls "$SRC"/commands/*.md | wc -l`

**Expected Result:**
- Step 1: `exit 0`; `📋 Commands:  33`; `0`; `✨ New:       commands/implement-story.md`; `0` (the dry run wrote nothing).
- Step 2: `exit 0`.
- Step 3: `0`, `0`, `33`, `33`. The installed command count equals every `commands/*.md` in the source.

**Status:** [x] Pass  [ ] Fail

**Notes:** agent-run 2026-10-21 @ b850e66: dry run `exit 0`, `📋 Commands:  33`, `0`, `✨ New:       commands/implement-story.md`, `0` files written; install `exit 0`; step 3 `0`, `0`, `33`, `33`.

---

### Scenario 3: Update removes unmodified lean copies; the dry run lists them and writes nothing

**Source:** Acceptance Criteria — Story 1 (AC-1.3); Error Map (Update removes an unmodified cut file); Experience Design (State: update, old unmodified copies present); Edge Case (`update.sh --dry-run`)
**Feature:** none
**Verification:** human — no recipe
**Automated Test:** `scripts/tests/test_install_update_harness_cuts.sh` (AC-1.3 blocks)

**Preconditions:**
- Setup block pasted.

**Steps:**
1. `P="$W/s3"; inst "$P" claude > /dev/null 2>&1; plant_lean "$P" implement-story.lean.md; plant_lean "$P" _preamble.lean.md`
2. `before=$(digest "$P"); upd "$P" claude --dry-run > "$W/s3-dry.txt" 2>&1; echo "exit $?"; [ "$(digest "$P")" = "$before" ] && echo "tree unchanged"; sed -n '/Stale files/,$p' "$W/s3-dry.txt"`
3. `upd "$P" claude > "$W/s3.txt" 2>&1; echo "exit $?"; grep 'Removed' "$W/s3.txt"`
4. `ls "$P/.claude/commands" | grep -c '\.lean\.md$'; grep -c '\.lean\.md$' "$P/.claude/.writ-manifest"`

**Expected Result:**
- Step 2: `exit 0`, `tree unchanged`, then:
  ```
    Stale files (removed upstream, would be deleted):
      🗑  commands/implement-story.lean.md
      🗑  commands/_preamble.lean.md
  ```
- Step 3: `exit 0`, `🗑  Removed: commands/implement-story.lean.md`, `🗑  Removed: commands/_preamble.lean.md`.
- Step 4: `0`, `0`.

**Status:** [x] Pass  [ ] Fail

**Notes:** agent-run 2026-10-21 @ b850e66: dry run `exit 0`, `tree unchanged`, both lean files listed under `Stale files (removed upstream, would be deleted):`; update `exit 0`, `🗑  Removed:` for both; step 4 `0`, `0`.

---

### Scenario 4: Update keeps an edited lean copy on every run and warns each time

**Source:** Acceptance Criteria — Story 1 (AC-1.4); Error Map (Update keeps a modified cut file: both rows); Experience Design (State: update, a copy edited locally; moment of truth); Edge Case (update run twice in a row)
**Feature:** none
**Verification:** human — no recipe
**Automated Test:** `scripts/tests/test_install_update_harness_cuts.sh` (AC-1.4 blocks)

**Preconditions:**
- Setup block pasted.

**Steps:**
1. `P="$W/s4"; inst "$P" claude > /dev/null 2>&1; plant_lean "$P" verify-spec.lean.md edit; plant_lean "$P" implement-phase.lean.md`
2. `F="$P/.claude/commands/verify-spec.lean.md"; B=$(grep '  commands/verify-spec.lean.md$' "$P/.claude/.writ-manifest"); E=$(h "$F")`
3. `for run in 1 2; do upd "$P" claude > "$W/s4-$run.txt" 2>&1; echo "run $run exit $?"; grep -e 'Stale' -e 'Removed' -e 'Already up to date' "$W/s4-$run.txt"; [ "$(h "$F")" = "$E" ] && echo "edited copy unchanged"; [ "$(grep '  commands/verify-spec.lean.md$' "$P/.claude/.writ-manifest")" = "$B" ] && echo "baseline kept"; done`

**Expected Result:**
- Run 1: `run 1 exit 0`, `⚠️  Stale (no longer shipped, locally modified — kept): commands/verify-spec.lean.md`, `🗑  Removed: commands/implement-phase.lean.md`, `edited copy unchanged`, `baseline kept`.
- Run 2: `run 2 exit 0`, the same `⚠️  Stale …` line, `✅ Already up to date! (<hash>)`, `edited copy unchanged`, `baseline kept`.

**Status:** [x] Pass  [ ] Fail

**Notes:** The unmodified `implement-phase.lean.md` makes run 1 rewrite the manifest, so "baseline kept" after run 1 is meaningful (see Conventions).

agent-run 2026-10-21 @ b850e66: run 1 `exit 0`, `⚠️  Stale (no longer shipped, locally modified — kept): commands/verify-spec.lean.md`, `🗑  Removed: commands/implement-phase.lean.md`, `edited copy unchanged`, `baseline kept`; run 2 `exit 0`, same Stale line, `✅ Already up to date! (d732939)`, `edited copy unchanged`, `baseline kept`.

**Implementation Reference:** Story 1 — `update.sh` `detect_stale_files` keeps the `! -f "$upstream_file"` test and the kept-modified branch from `2026-10-20-ci-and-update-integrity`.

---

### Scenario 5: Every suite passes and no test reads a lean file

**Source:** Acceptance Criteria — Story 1 (AC-1.5); Error Map (Delete a lean file: a test or eval pin still reads it; Remove a lean code path: files removed after code paths); spec Success Criteria
**Feature:** none
**Verification:** human — no recipe
**Automated Test:** partial — `scripts/tests/test_harness_cuts.py` (`NoTestReadsALeanFileTest`) asserts no mixed test or eval check names a lean file; CI runs the three suites. Running them here is by hand.

**Preconditions:**
- Setup block pasted. Outside any sandbox. About 2.5 min for pytest, 5 min for the bash tests, and several minutes for `eval.sh`.

**Steps:**
1. `cd "$CL" && uv run --python 3.9 pytest -q 2>&1 | tail -1`
2. `for t in scripts/tests/test_*.sh; do bash "$t" > /dev/null 2>&1 || echo "FAIL $t"; done; echo "bash tests done"`
3. `bash scripts/eval.sh --report="$W/eval.md" > /dev/null 2>&1; echo "exit $?"; sed -n '/^## Summary/,$p' "$W/eval.md"`
4. `ls scripts/tests/test_lean_commands.py scripts/tests/test_lean_preamble.py scripts/tests/test_install_update_lean_siblings.sh 2>&1 | sed 's/.*: //'`

**Expected Result:**
- Step 1: `N passed, 2 skipped` with no failures.
- Step 2: only `bash tests done`.
- Step 3: `exit 0` and `- Findings: 0`.
- Step 4: three lines of `No such file or directory`.

**Status:** [x] Pass  [ ] Fail

**Notes:** Observed on `7922922`: Step 1 `1 failed, 2606 passed, 2 skipped` (the guard test; see Known Issue). Step 2: 39 bash tests, 0 failed. Step 3: `exit 0`, `- Findings: 0`, `- Run errors: 0`. Only Step 1 fails.

agent-run 2026-10-21 @ b850e66: step 1 `2774 passed, 2 skipped` (no failures; the guard test passes since `8974202`); step 2 only `bash tests done` (45 bash tests); step 3 `exit 0`, `- Findings: 0`, `- Run errors: 0`; step 4 three `No such file or directory`.

---

### Scenario 6: A lean file update never recorded is left alone

**Source:** Error Map (Update removes an unmodified cut file: manifest has no line for it) — Story 1; Edge Case (user re-creates a lean file by hand after the update)
**Feature:** none
**Verification:** human — no recipe
**Automated Test:** none — manual only for a lean file. `test_install_update_harness_cuts.sh` checks the same rule for the staging files (Scenario 26).

**Preconditions:**
- Setup block pasted.

**Steps:**
1. `P="$W/s6"; inst "$P" claude > /dev/null 2>&1; printf '# my own notes\n' > "$P/.claude/commands/create-spec.lean.md"; E=$(h "$P/.claude/commands/create-spec.lean.md"); plant_lean "$P" implement-phase.lean.md`
2. `upd "$P" claude > "$W/s6.txt" 2>&1; echo "exit $?"; grep -e Removed -e Stale "$W/s6.txt"; [ "$(h "$P/.claude/commands/create-spec.lean.md")" = "$E" ] && echo "hand-made file unchanged"; grep -c 'create-spec.lean.md' "$P/.claude/.writ-manifest"`
3. `upd "$P" claude > "$W/s6b.txt" 2>&1; echo "exit $?"; grep -c 'create-spec.lean.md' "$W/s6b.txt"; tail -1 "$W/s6b.txt"`

**Expected Result:**
- Step 2: `exit 0`; the only line is `🗑  Removed: commands/implement-phase.lean.md`; `hand-made file unchanged`; `0` (not recorded).
- Step 3: `exit 0`, `0`, `✅ Already up to date! (<hash>)`.

**Status:** [x] Pass  [ ] Fail

**Notes:** agent-run 2026-10-21 @ b850e66: step 2 `exit 0`, only `🗑  Removed: commands/implement-phase.lean.md`, `hand-made file unchanged`, `0`; step 3 `exit 0`, `0`, `✅ Already up to date! (d732939)`.

---

## Story 2: Remove the Lean Code Paths from the Scripts

### Scenario 7: The guard grep is empty repo-wide, and the Story 2 files are gone

**Source:** Acceptance Criteria — Story 2 (AC-2.1); drift DEV-005
**Feature:** none
**Verification:** human — no recipe
**Automated Test:** `scripts/tests/test_harness_cuts.py` (`test_ac_1_1_ac_2_1_guard_grep_is_empty_repo_wide`, `test_ac_2_1_lean_decision_and_story2_lean_tests_are_deleted`)

**Preconditions:**
- Setup block pasted.

**Steps:**
1. The guard's current pathspec (what the test runs since DEV-009 excluded `.writ/specs` as a whole):
   `cd "$REPO" && git grep -n -e WRIT_HARNESS_LEAN -e '\.lean\.md' -- . ':!CHANGELOG.md' ':!.writ/decision-log.md' ':!.writ/specs' ':!.writ/research' ':!.writ/product' ':!.writ/decision-records' ':!scripts/tests/test_harness_cuts.py' ':!scripts/tests/test_install_update_harness_cuts.sh'; echo "exit $?"`
2. The literal Business Rule 2 pathspec, counted by folder:
   `git grep -n -e WRIT_HARNESS_LEAN -e '\.lean\.md' -- . ':!CHANGELOG.md' ':!.writ/decision-log.md' ':!.writ/specs/archive' ':!.writ/research' ':!.writ/product' ':!.writ/decision-records' ':!.writ/specs/2026-10-12-agent-cli-contract' ':!.writ/specs/2026-10-20-harness-cuts' ':!scripts/tests/test_harness_cuts.py' ':!scripts/tests/test_install_update_harness_cuts.sh' | cut -d: -f1 | cut -d/ -f1-3 | sort | uniq -c`
3. `ls scripts/lean-decision.py scripts/tests/test_lean_decision.py scripts/tests/test_measure_invocation_lean.py scripts/tests/test_eval_manifest_lean.sh 2>&1 | sed 's/.*: //'`

**Expected Result:**
- Step 1: no output, `exit 1`.
- Step 2: hits only under `.writ/specs/2026-10-20-platform-neutral-names` (12) and `.writ/specs/2026-10-20-shipped-command-hygiene` (15). These are the Not Started sibling specs that DEV-005 excludes. That exclusion is flagged for review and is not yet in Business Rule 2.
- Step 3: four lines of `No such file or directory`.

**Status:** [x] Pass  [ ] Fail

**Notes:** Observed on `7922922`: Step 1 prints `.writ/specs/2026-10-20-ci-and-update-integrity/uat-plan.md:609:- No line for a dev-only script (for example `scripts/harness-cost.py`) or an unshipped `*.lean.md` command.` and exits 0. Step 2 shows that folder too (`1`). See Known Issue.

agent-run 2026-10-21 @ b850e66: the step 1 pathspec as written still prints the `2026-10-20-ci-and-update-integrity/uat-plan.md:609` line (exit 0), but it is no longer what the test runs: `8974202` (DEV-009, Business Rule 2 amended) replaced the per-folder spec exclusions with `':!.writ/specs'`, and that pathspec prints nothing, `exit 1`; the guard test passes in the full suite (Scenario 5).
Step 2: `1` ci-and-update-integrity, `12` platform-neutral-names, `26` shipped-command-hygiene (was 15; that spec grew after `7922922`). Step 3: four `No such file or directory`.
- maintainer sign-off 2026-10-21 (delegated): Pass accepted; the guard test excludes .writ/specs as a whole since 8974202 (DEV-009). Step 1 pathspec updated.

---

### Scenario 8: `story-context.py` accepts `--state-dir` as a hidden no-op and truncates as before

**Source:** Acceptance Criteria — Story 2 (AC-2.2); Error Map (Remove a lean code path: a shipped caller passes `--state-dir`)
**Feature:** none
**Verification:** human — no recipe
**Automated Test:** `scripts/tests/test_story_context.py` (`StateDirIsAHiddenNoOpTests`); `scripts/tests/test_harness_cuts.py` (`OldLeanVariableIsIgnoredTest`)

**Preconditions:**
- Setup block pasted.

**Steps:**
1. `cd "$CL"; S=.writ/specs/2026-10-20-harness-cuts/user-stories/story-1-delete-lean-siblings.md; n0=$(ls -A .writ/state 2>/dev/null | wc -l)`
2. `python3 scripts/story-context.py assemble --story "$S" --budget-bytes 500 > "$W/sc-a.json"; echo "exit $?"`
3. `python3 scripts/story-context.py assemble --story "$S" --budget-bytes 500 --state-dir "$W/sc-state" > "$W/sc-b.json"; echo "exit $?"`
4. `cmp "$W/sc-a.json" "$W/sc-b.json" && echo identical; python3 -c "import json,sys; d=json.load(open(sys.argv[1])); print(sorted(d), d['truncated'], d['bytes']['total']); print([w for w in d['warnings'] if 'truncated' in w])" "$W/sc-a.json"`
5. `ls "$W/sc-state" 2>&1 | sed 's/.*: //'; [ "$(ls -A .writ/state 2>/dev/null | wc -l)" = "$n0" ] && echo ".writ/state unchanged"; python3 scripts/story-context.py assemble --help | grep -c state-dir`

**Expected Result:**
- Steps 2 and 3: `exit 0` each.
- Step 4: `identical`; `['bytes', 'fetched_context', 'truncated', 'warnings'] True 500`; `['⚠️ fetched_context truncated (2563 of 500 bytes)']` (the first number depends on the story).
- Step 5: `No such file or directory` (nothing written under the state dir); `.writ/state unchanged`; `0` (the flag is not shown in help).

**Status:** [x] Pass  [ ] Fail

**Notes:** agent-run 2026-10-21 @ b850e66: steps 2–3 `exit 0`; `identical`; `['bytes', 'fetched_context', 'truncated', 'warnings'] True 500`; `['⚠️ fetched_context truncated (2563 of 500 bytes)']`; step 5 `No such file or directory`, `.writ/state unchanged`, `0`.

**Implementation Reference:** Story 2 — `scripts/story-context.py`: spill path removed; `--state-dir` kept with `help=argparse.SUPPRESS` (Business Rule 7).

---

### Scenario 9: `pipeline-baseline.py` has no `--lean`, writes the five-key `writ` block, and still validates legacy records

**Source:** Acceptance Criteria — Story 2 (AC-2.3)
**Feature:** none
**Verification:** human — no recipe
**Automated Test:** `scripts/tests/test_pipeline_baseline_run.py` (`LeanArmRemovedTest`); `scripts/tests/test_pipeline_baseline.py` (`test_legacy_harness_lean_in_the_writ_block_still_validates`)

**Preconditions:**
- Setup block pasted.

**Steps:**
1. `cd "$CL" && python3 scripts/pipeline-baseline.py run --help | grep -c -- --lean`
2. `python3 scripts/pipeline-baseline.py run --baseline "$W/none.json" --yuss "$W/none" --lean 2>&1 | tail -1; echo "exit ${PIPESTATUS[0]}"; ls "$W/none.json" 2>&1 | sed 's/.*: //'`
3. `grep -n '^WRIT_KEYS' scripts/pipeline-baseline.py; grep -n -i lean scripts/pipeline-baseline.py | grep -v -i clean | wc -l`
4. `uv run --python 3.9 pytest -q scripts/tests/test_pipeline_baseline_run.py scripts/tests/test_pipeline_baseline.py -k "LeanArmRemoved or legacy_harness_lean" 2>&1 | tail -1`

**Expected Result:**
- Step 1: `0`.
- Step 2: `pipeline-baseline.py: error: unrecognized arguments: --lean`, `exit 2`, `No such file or directory` (it stopped before writing anything).
- Step 3: `719:WRIT_KEYS = ("source", "commit", "dirty", "checkout_manifest_version", "manifest_diff_count")` and `0`.
- Step 4: `4 passed, 149 deselected`. These tests run `overlay_writ` and check the record's `writ` block has exactly the five keys, and validate records carrying `harness_lean` true and false.

**Status:** [x] Pass  [ ] Fail

**Notes:** The committed baselines in `.writ/eval/baselines/2026-09-25-lean-arms/` already fail `validate` for an unrelated reason ("expected 8 records, got 2"), so legacy tolerance is pinned by a fixture, not by those files (Story 2 What Was Built).

agent-run 2026-10-21 @ b850e66: step 1 `0`; step 2 `pipeline-baseline.py: error: unrecognized arguments: --lean`, `exit 2`, `No such file or directory`; step 3 `719:WRIT_KEYS = ("source", "commit", "dirty", "checkout_manifest_version", "manifest_diff_count")`, `0`; step 4 `4 passed, 149 deselected`.

---

### Scenario 10: Every `commands/*.md` counts as a command, whatever its name

**Source:** Acceptance Criteria — Story 2 (AC-2.4)
**Feature:** none
**Verification:** human — no recipe
**Automated Test:** `scripts/tests/test_eval_leanness_contract.py` (`EveryCommandFileCountsTests`); `scripts/tests/test_harness_cuts.py` (`EveryCommandFileIsACommandTest`, `OldLeanVariableIsIgnoredTest`)

**Preconditions:**
- Setup block pasted.

**Steps:**
1. `T="$W/s10"; mkdir -p "$T/commands"; printf '# a\n' > "$T/commands/a.md"; printf '# b\n' > "$T/commands/b.variant.md"`
2. `python3 "$CL/scripts/eval-leanness.py" --root "$T" --baseline "$W/s10-baseline.json" --update-baseline; python3 -c "import json,sys; print(json.load(open(sys.argv[1]))['commands'])" "$W/s10-baseline.json"`
3. Build a root with a listed command and an unlisted dotted one, then run the manifest check:
   `R="$W/s10m"; mkdir -p "$R/scripts" "$R/commands" "$R/agents" "$R/.writ/state"; cp "$CL/scripts/eval.sh" "$R/scripts/"; for n in listed listed.lean; do printf -- '---\nname: %s\ndescription: "d"\n---\n\n## Overview\n' "$n" > "$R/commands/$n.md"; done; printf 'commands:\n  - name: listed\n    file: commands/listed.md\nagents:\n' > "$R/.writ/manifest.yaml"; (cd "$R" && bash scripts/eval.sh --check=manifest --report=eval-report.md > /dev/null 2>&1); grep 'not listed' "$R/eval-report.md"`
4. `cd "$CL" && python3 scripts/measure-invocation.py --root "$CL" --tokenizer estimate | grep -c harness_lean`

**Expected Result:**
- Step 2: `Wrote baseline: …` then `2` (both files are commands).
- Step 3: one line: `` - `commands/listed.lean.md`: command file exists but is not listed in .writ/manifest.yaml. … `` and none for `commands/listed.md`. (The report also has a `.writ/manifest.yaml` generator-validation finding because the fixture manifest is minimal; ignore it.)
- Step 4: `0`.

**Status:** [x] Pass  [ ] Fail

**Notes:** agent-run 2026-10-21 @ b850e66: step 2 `Wrote baseline: ../s10-baseline.json`, `2`; step 3 one `not listed` finding, for `commands/listed.lean.md` only (plus the expected `.writ/manifest.yaml` generator-validation finding); step 4 `0`.

---

### Scenario 11: The three script filters match and drop `lean-decision.py`; update removes an old installed copy

**Source:** Acceptance Criteria — Story 2 (AC-2.5); Error Map (Delete `lean-decision.py`: a test copies it as a fixture)
**Feature:** none
**Verification:** human — no recipe
**Automated Test:** `scripts/tests/test_harness_cuts.py` (`ShipFilterDropsLeanDecisionTest`); `scripts/tests/test_install_update_dev_scripts.sh`

**Preconditions:**
- Setup block pasted.

**Steps:**
1. `cd "$REPO"; f() { sed -n '/^is_shippable_script() {/,/^}/p' "scripts/$1.sh"; }; [ "$(f install)" = "$(f update)" ] && [ "$(f install)" = "$(f unlink)" ] && echo "three identical"; f install | grep -c lean-decision`
2. `grep -c lean-decision .writ/docs/agent-cli-contract.md commands/update-writ.md`
3. `cd "$CL" && bash scripts/tests/test_install_update_dev_scripts.sh 2>&1 | tail -1`
4. `P="$W/s11"; inst "$P" claude > /dev/null 2>&1; printf '# old lean-decision.py\n' > "$P/scripts/lean-decision.py"; mline "$P" claude scripts/lean-decision.py scripts/lean-decision.py; upd "$P" claude 2>&1 | grep -e Removed -e Stale; ls "$P/scripts/lean-decision.py" 2>&1 | sed 's/.*: //'; grep -c lean-decision "$P/.claude/.writ-manifest"`

**Expected Result:**
- Step 1: `three identical`, `0`.
- Step 2: `.writ/docs/agent-cli-contract.md:0`, `commands/update-writ.md:0`.
- Step 3: `PASS test_install_update_dev_scripts` (its kept-modified fixture is now `prune-ledger.py`).
- Step 4: `🗑  Removed: scripts/lean-decision.py`, `No such file or directory`, `0`.

**Status:** [x] Pass  [ ] Fail

**Notes:** agent-run 2026-10-21 @ b850e66: `three identical`, `0`; `.writ/docs/agent-cli-contract.md:0`, `commands/update-writ.md:0`; `PASS test_install_update_dev_scripts`; `🗑  Removed: scripts/lean-decision.py`, `No such file or directory`, `0`.

---

### Scenario 12: A reintroduced lean reference fails the guard and names the file

**Source:** Shadow Path (Guard grep: upstream error, nil input) — Stories 1–3; Edge Case (a `.lean.md` command added on purpose); Experience Design (error: a leftover reference fails the guard test naming file and line)
**Feature:** none
**Verification:** human — no recipe
**Automated Test:** none — manual only. This checks that the guard test fails when it should.

**Preconditions:**
- Setup block pasted. Uses the clone at `$CL`; Step 5 restores it.

**Steps:**
1. `cd "$CL" && printf -- '---\nname: zz-new\ndescription: "d"\n---\n\n# zz-new\n' > commands/zz-new.lean.md && git add commands/zz-new.lean.md && printf '\nExport WRIT_HARNESS_LEAN=1 to try it.\n' >> README.md`
2. `uv run --python 3.9 pytest -q scripts/tests/test_harness_cuts.py -k "guard_grep or no_lean_command_files" 2>&1 | grep -E 'still exist|^E +README.md:|failed'`
3. `P="$W/s12"; mkdir -p "$P" && (cd "$P" && bash "$CL/scripts/install.sh" --platform claude --no-commit) > /dev/null 2>&1; echo "exit $?"; ls "$P/.claude/commands/zz-new.lean.md"; grep -c '  commands/zz-new.lean.md$' "$P/.claude/.writ-manifest"`
4. `uv run --python 3.9 python -c "import os,sys; sys.path.insert(0,'scripts/tests'); import test_harness_cuts as t; os.environ['PATH']='/nonexistent'; t.guard_grep(('.',))" 2>&1 | tail -1`
5. `git rm -q --cached commands/zz-new.lean.md && rm commands/zz-new.lean.md && git checkout -q README.md && git status --short`

**Expected Result:**
- Step 2: a line ending `lean command files still exist: zz-new.lean.md`; a line `E       README.md:386:Export WRIT_HARNESS_LEAN=1 to try it.` (file and line); `2 failed, 40 deselected`.
- Step 3: `exit 0`, the file is listed, `1`. A `.lean.md` command ships like any other; the guard test is the signal.
- Step 4: `FileNotFoundError: [Errno 2] No such file or directory: 'git'`. The guard errors; it does not pass.
- Step 5: no output.

**Status:** [x] Pass  [ ] Fail

**Notes:** Until the Known Issue is fixed, Step 2's README failure also lists the `2026-10-20-ci-and-update-integrity/uat-plan.md:609` line.

agent-run 2026-10-21 @ b850e66: step 2 `E       + [] : lean command files still exist: zz-new.lean.md`, `E       README.md:386:Export WRIT_HARNESS_LEAN=1 to try it.`, `2 failed, 40 deselected` (the ci-and-update-integrity line no longer appears); step 3 `exit 0`, file listed, `1`; step 4 `FileNotFoundError: [Errno 2] No such file or directory: 'git'`; step 5 no output.

---

### Scenario 13: Exporting the old lean variable changes nothing

**Source:** Experience Design (State: maintainer exports the old lean variable) — Story 2; Edge Case (operator still exports the lean variable)
**Feature:** none
**Verification:** human — no recipe
**Automated Test:** partial — `scripts/tests/test_harness_cuts.py` (`OldLeanVariableIsIgnoredTest`) covers `story-context.py` and `measure-invocation.py`; the install comparison is by hand.

**Preconditions:**
- Setup block pasted.

**Steps:**
1. `cd "$REPO" && grep -rln WRIT_HARNESS_LEAN scripts commands agents skills adapters cursor claude-code codex`
2. `inst "$W/s13a" claude --dry-run > "$W/s13a.txt" 2>&1; WRIT_HARNESS_LEAN=1 inst "$W/s13b" claude --dry-run > "$W/s13b.txt" 2>&1; diff <(sed "s|$W/s13[ab]|P|g" "$W/s13a.txt") <(sed "s|$W/s13[ab]|P|g" "$W/s13b.txt") && echo "install dry runs identical"`
3. `cd "$CL" && python3 scripts/measure-invocation.py --root "$CL" --tokenizer estimate > "$W/mi-a.json"; WRIT_HARNESS_LEAN=1 python3 scripts/measure-invocation.py --root "$CL" --tokenizer estimate > "$W/mi-b.json"; cmp "$W/mi-a.json" "$W/mi-b.json" && echo "measure-invocation identical"`
4. `S=.writ/specs/2026-10-20-harness-cuts/user-stories/story-1-delete-lean-siblings.md; python3 scripts/story-context.py assemble --story "$S" --budget-bytes 500 > "$W/sc-c.json"; WRIT_HARNESS_LEAN=1 python3 scripts/story-context.py assemble --story "$S" --budget-bytes 500 > "$W/sc-d.json"; cmp "$W/sc-c.json" "$W/sc-d.json" && echo "story-context identical"`

**Expected Result:**
- Step 1: only `scripts/tests/test_harness_cuts.py` (one of the two guard-excluded tests).
- Steps 2–4: `install dry runs identical`, `measure-invocation identical`, `story-context identical`.

**Status:** [x] Pass  [ ] Fail

**Notes:** agent-run 2026-10-21 @ b850e66: step 1 only `scripts/tests/test_harness_cuts.py`; `install dry runs identical`, `measure-invocation identical`, `story-context identical`.

---

## Story 3: Remove the ADR-025 No-Op Lines and Correct the /ship Description

### Scenario 14: No `escalated(...)` emit or sink sentence is left in `commands/`

**Source:** Acceptance Criteria — Story 3 (AC-3.1)
**Feature:** none
**Verification:** human — no recipe
**Automated Test:** `scripts/tests/test_harness_cuts.py` (`NoOpEmitLinesGoneTest`); `scripts/tests/test_implement_story_default_path.py` (Gate 0 `assertNotIn` lines)

**Preconditions:**
- Setup block pasted.

**Steps:**
1. `cd "$REPO" && grep -rn "no-op until ADR-025" commands; echo "exit $?"; grep -rn "The line has no sink today" commands; echo "exit $?"; grep -c 'escalated(' commands/create-spec.md commands/implement-story.md`
2. Open `commands/create-spec.md` at `#### Step 2.6a: Validate Generated Stories` (`grep -n 'Step 2.6a: Validate' commands/create-spec.md`). Count the numbered items before the paragraph that starts "Escalation fires only on a *returned* file".
3. Open `commands/implement-story.md` at `**Anchor confirmation (ADR-024):**` (`grep -n 'Anchor confirmation' commands/implement-story.md`) and read the paragraph.

**Expected Result:**
- Step 1: no output and `exit 1`, twice; `commands/create-spec.md:0`, `commands/implement-story.md:0`.
- Step 2: items 1, 2, and 3 only. Item 3 re-runs each failing story once at `anchor`.
- Step 3: the paragraph re-runs `architecture-check-agent` once at `anchor` and ends with the "Iteration accounting: …" sentence. It does not tell the agent to print an `escalated(...)` line.

**Status:** [x] Pass  [ ] Fail

**Notes:** agent-run 2026-10-21 @ b850e66: step 1 no output and `exit 1` twice, `commands/create-spec.md:0`, `commands/implement-story.md:0`. Step 2.6a (line 554) has items 1–3 only; item 3 re-runs each failing story once at `anchor`. Gate 0 anchor confirmation (line 192) re-runs `architecture-check-agent` once at `anchor`, ends with the "Iteration accounting: …" sentence, and has no `escalated(...)` line.

---

### Scenario 15: Escalate-once is unchanged and still pinned by eval

**Source:** Acceptance Criteria — Story 3 (AC-3.2); Error Map (Remove the ADR-025 emit line: the iteration sentence is cut too); Experience Design (State: agent reads `/create-spec` Step 2.6a or `/implement-story` Gate 0)
**Feature:** none
**Verification:** human — no recipe
**Automated Test:** `scripts/tests/test_harness_cuts.py` (`EscalateOnceUnchangedTest`, which also runs this eval check on temp trees)

**Preconditions:**
- Setup block pasted. Uses the clone at `$CL`; Step 5 restores it.

**Steps:**
1. `cd "$REPO" && grep -c 'the floor attempt and its anchor re-run count as one attempt — there is no second regeneration' commands/create-spec.md; grep -c 'the floor attempt and its anchor re-run count as one attempt against `loop.max_iterations`' commands/implement-story.md; grep -c 'loop.max_iterations' commands/create-spec.md`
2. `sed -n '/^check_model_escalation()/,/^}/p' scripts/eval.sh | grep -c -e noop_prefix -e missing_sink -e 'escalated(agent='`
3. `cd "$CL" && bash scripts/eval.sh --check=model-escalation --report="$W/me.md" > /dev/null 2>&1; echo "exit $?"; grep -A2 '^## model-escalation' "$W/me.md"`
4. `sed -i '' 's/count as one attempt — there is no second regeneration/count once/' commands/create-spec.md && bash scripts/eval.sh --check=model-escalation --report="$W/me2.md" > /dev/null 2>&1; echo "exit $?"; grep -A4 '^## model-escalation' "$W/me2.md" | tail -1`
5. `git checkout -q commands/create-spec.md && git status --short`

**Expected Result:**
- Step 1: `1`, `1`, `0`.
- Step 2: `0`.
- Step 3: `exit 0`, then `## model-escalation`, a blank line, `PASS`.
- Step 4: `exit 1` and a finding: `` - `commands/create-spec.md`: create-spec.md Step 2.6a must state the pair-counts-once iteration rule verbatim, … ``.
- Step 5: no output.

**Status:** [x] Pass  [ ] Fail

**Notes:** agent-run 2026-10-21 @ b850e66: step 1 `1`, `1`, `0`; step 2 `0`; step 3 `exit 0`, `## model-escalation`, blank, `PASS`; step 4 `exit 1` and the `commands/create-spec.md`: "…must state the pair-counts-once iteration rule verbatim…" finding; step 5 no output.

---

### Scenario 16: `/ship` says it opens a PR; its problem, outcome, and exit criteria are unchanged

**Source:** Acceptance Criteria — Story 3 (AC-3.3); Experience Design (State: agent or user reads `/ship`)
**Feature:** none
**Verification:** human — no recipe
**Automated Test:** `scripts/tests/test_harness_cuts.py` (`ShipSaysItOpensAPRTest`)

**Preconditions:**
- Setup block pasted.

**Steps:**
1. `cd "$REPO" && sed -n 3p commands/ship.md; grep -n -i -e 'merged PR' -e 'branch to merged' -e 'gets it merged' commands/ship.md; echo "exit $?"`
2. `diff <(git show dd763b7^:commands/ship.md | sed -n 1,30p) <(sed -n 1,30p commands/ship.md) | grep '^[0-9]'`
3. Read `## Overview` in `commands/ship.md` (lines 15–25).
4. `inst "$W/s16" claude > /dev/null 2>&1; sed -n 3p "$W/s16/.claude/commands/ship.md"; grep -n '/ship' "$W/s16/CLAUDE.md"`

**Expected Result:**
- Step 1: `description: "Take a green branch to an open PR - merge the default branch, organize commits, write the PR description, push, and open it."`; no grep hits; `exit 1`.
- Step 2: `3c3`, `17c17`, `19c19`, `25c25`. Only the description and three Overview lines changed. The `problem:`, `outcome:`, and `exit_criteria:` lines (4–10) did not.
- Step 3: the Overview says `/ship` takes a green branch to an open PR, opens a PR, and owns the "branch to open PR" path ending `→ open PR`. It does not say `/ship` merges.
- Step 4: the installed `ship.md` has the same description. The installed `CLAUDE.md` still lists `/ship` as `Branch to merged PR workflow`.

**Status:** [x] Pass  [ ] Fail

**Notes:** The `CLAUDE.md` line comes from `claude-code/CLAUDE.md:20`, which Story 3 left out of scope. See Not Covered.

agent-run 2026-10-21 @ b850e66: steps 1–3 as expected (`3c3`, `17c17`, `19c19`, `25c25`; Overview says green branch to open PR, path ends `→ open PR`, no merge claim). Step 4: installed `ship.md` description matches.
Installed `CLAUDE.md:42` now reads `Take a green branch through commit intelligence and PR creation.`, not `Branch to merged PR workflow`: `claude-code/CLAUDE.md` is generated from the manifest since `98b773d` (after `7922922`), which closes the Not Covered gap.

---

### Scenario 17: `ship.md` did not grow and the recorded overages fell

**Source:** Acceptance Criteria — Story 3 (AC-3.4); Error Map (Reword ship.md: file grows past its recorded overage)
**Feature:** none
**Verification:** human — no recipe
**Automated Test:** `scripts/tests/test_governor_enforcement.py`; `scripts/tests/test_harness_cuts.py` (`OverageLedgerFellTest`)

**Preconditions:**
- Setup block pasted.

**Steps:**
1. `cd "$REPO" && wc -c commands/ship.md commands/create-spec.md commands/implement-story.md`
2. `grep -n -e '"commands/ship.md":' -e '"commands/create-spec.md":' -e '"commands/implement-story.md":' -e 'harness-cuts Story 3' scripts/tests/test_governor_enforcement.py`
3. `cd "$CL" && uv run --python 3.9 pytest -q scripts/tests/test_governor_enforcement.py 2>&1 | tail -1`

**Expected Result:**
- Step 1: `28983 commands/ship.md` (at most 28,990), `53693 commands/create-spec.md`, `36493 commands/implement-story.md`.
- Step 2: `"commands/create-spec.md": 28733`, `"commands/ship.md": 4023`, `"commands/implement-story.md": 11533`. Each equals the file size minus 24,960. Each has a dated `2026-10-20 (2026-10-20-harness-cuts Story 3)` comment naming its old value (29304, 4030, 12013).
- Step 3: `49 passed`.

**Status:** [x] Pass  [ ] Fail

**Notes:** Sizes are as of `7922922`. Later Phase 13 specs may edit these files and their ledger entries.

agent-run 2026-10-21 @ b850e66: sizes `28907` ship.md (≤ 28,990), `38562` create-spec.md, `36226` implement-story.md, smaller than at `7922922` (later shipped-command-hygiene and platform-neutral-names edits). Ledger `13602`, `3947`, `11266`, each = size − 24,960; each keeps the harness-cuts Story 3 comment naming 29304, 4030, 12013, followed by later dated comments. Step 3 `58 passed` (was 49).

---

## Story 4: Make Recommended-Delivery Staging Dev-Only

### Scenario 18: Both ship filters reject the staging files and stay identical

**Source:** Acceptance Criteria — Story 4 (AC-4.1)
**Feature:** none
**Verification:** human — no recipe
**Automated Test:** `scripts/tests/test_install_update_harness_cuts.sh` (AC-4.1 block)

**Preconditions:**
- Setup block pasted.

**Steps:**
1. Call the script filter from each of the three files:
   ```bash
   for s in install update unlink; do
     bash -c "$(sed -n '/^is_shippable_script() {/,/^}/p' "$REPO/scripts/$s.sh")"'
       is_shippable_script recommend-state.py; a=$?; is_shippable_script spec-status.py; echo "$1: recommend-state.py=$a spec-status.py=$?"' _ $s
   done
   ```
2. Run every source doc through the doc filter in both files:
   ```bash
   for s in install update; do
     bash -c "$(sed -n '/^is_shippable_writ_doc() {/,/^}/p' "$REPO/scripts/$s.sh")"'
       for f in "$2"/.writ/docs/*.md; do is_shippable_writ_doc "$(basename "$f")" || echo "$1 rejects: $(basename "$f")"; done' _ $s "$REPO"
   done
   ```
3. `f() { sed -n "/^$1() {/,/^}/p" "$REPO/scripts/$2.sh"; }; [ "$(f is_shippable_script install)" = "$(f is_shippable_script update)" ] && [ "$(f is_shippable_script install)" = "$(f is_shippable_script unlink)" ] && echo "script filter: 3 identical"; [ "$(f is_shippable_writ_doc install)" = "$(f is_shippable_writ_doc update)" ] && echo "doc filter: 2 identical"`
4. `ls "$REPO/$HL" "$REPO/$SD"`

**Expected Result:**
- Step 1: `install: recommend-state.py=1 spec-status.py=0`, and the same for `update` and `unlink` (1 = rejected).
- Step 2: exactly `install rejects: recommended-delivery-state-format.md` and `update rejects: recommended-delivery-state-format.md`. Every other doc is accepted.
- Step 3: `script filter: 3 identical`, `doc filter: 2 identical`.
- Step 4: both files listed. They stay in the source repo.

**Status:** [x] Pass  [ ] Fail

**Notes:** agent-run 2026-10-21 @ b850e66: `recommend-state.py=1 spec-status.py=0` for install, update, unlink; only `install rejects:` and `update rejects: recommended-delivery-state-format.md`; `script filter: 3 identical`, `doc filter: 2 identical`; both files listed.

**Implementation Reference:** Story 4 — `is_shippable_script` dev-only arm in `install.sh`, `update.sh`, `unlink.sh`; new `is_shippable_writ_doc` in `install.sh` and `update.sh`.

---

### Scenario 19: No platform installs the staging files; everything else still installs

**Source:** Acceptance Criteria — Story 4 (AC-4.2); Error Map (Fresh install: filter not wired at one call site); Shadow Path (Install: happy path); Experience Design (State: fresh install, any platform)
**Feature:** none
**Verification:** human — no recipe
**Automated Test:** `scripts/tests/test_install_update_harness_cuts.sh` (AC-4.2, all three platforms); `eval.sh` `install-{platform}-*` scenarios

**Preconditions:**
- Setup block pasted.

**Steps:**
1. For each platform, a dry run and then a real install:
   ```bash
   for pf in claude cursor codex; do
     P="$W/s19-$pf"
     inst "$P" $pf --dry-run > "$W/s19-$pf-dry.txt" 2>&1; d=$?; wrote=$(find "$P" -mindepth 1 | wc -l | tr -d ' ')
     inst "$P" $pf > "$W/s19-$pf.txt" 2>&1; r=$?
     echo "$pf: dry exit $d, dry wrote $wrote, install exit $r," \
       "names: $(cat "$W/s19-$pf-dry.txt" "$W/s19-$pf.txt" | grep -c -e recommend-state -e recommended-delivery)," \
       "on disk: $(ls "$P/$HL" "$P/$SD" 2>/dev/null | wc -l | tr -d ' ')," \
       "manifest: $(grep -c -e "  $HL\$" -e "  $SD\$" "$P/.$pf/.writ-manifest")," \
       "scripts: $(ls "$P/scripts" | wc -l | tr -d ' '), docs: $(ls "$P/.writ/docs" | wc -l | tr -d ' ')"
   done
   ```
2. `diff <(ls "$SRC/.writ/docs") <(ls "$W/s19-codex/.writ/docs")`
3. Count the scripts the source's own filter ships: `(cd "$SRC/scripts" && bash -c "$(sed -n '/^is_shippable_script() {/,/^}/p' "$SRC/scripts/install.sh")"'; for n in *; do [ -f "$n" ] && is_shippable_script "$n" && echo "$n"; done') | wc -l`

**Expected Result:**
- Step 1, for each of `claude`, `cursor`, `codex`: `dry exit 0, dry wrote 0, install exit 0, names: 0, on disk: 0, manifest: 0, scripts: 35, docs: 27`.
- Step 2: only `< recommended-delivery-state-format.md`.
- Step 3: `35`, matching the installed script count.

**Status:** [x] Pass  [ ] Fail

**Notes:** agent-run 2026-10-21 @ b850e66: claude, cursor, codex each `dry exit 0, dry wrote 0, install exit 0, names: 0, on disk: 0, manifest: 0, scripts: 35, docs: 28` (docs was 27; the source now has 29 docs). Step 2 only `< recommended-delivery-state-format.md`; step 3 `35`.

**Implementation Reference:** Story 4 — `overlay_scan_flat_dir` gets a `doc` filter at the four `.writ/docs` call sites; both `append_manifest_writ_docs` skip rejected docs.

---

### Scenario 20: Update removes unmodified staging copies even though upstream still has them

**Source:** Acceptance Criteria — Story 4 (AC-4.3, unmodified half); Error Map (Update removes an unmodified cut file: upstream still has the doc); Experience Design (State: update, old unmodified copies present); Edge Case (`update.sh --dry-run`)
**Feature:** none
**Verification:** human — no recipe
**Automated Test:** `scripts/tests/test_install_update_harness_cuts.sh` (AC-4.3 blocks); `eval.sh` `update-{platform}-*` scenarios

**Preconditions:**
- Setup block pasted.

**Steps:**
1. `P="$W/s20"; inst "$P" claude > /dev/null 2>&1; plant_stage "$P" claude $HL; plant_stage "$P" claude $SD`
2. `before=$(digest "$P"); upd "$P" claude --dry-run > "$W/s20-dry.txt" 2>&1; echo "exit $?"; [ "$(digest "$P")" = "$before" ] && echo "tree unchanged"; sed -n '/Stale files/,$p' "$W/s20-dry.txt"`
3. `upd "$P" claude > "$W/s20.txt" 2>&1; echo "exit $?"; grep Removed "$W/s20.txt"`
4. `ls "$P/$HL" "$P/$SD" 2>/dev/null | wc -l; grep -c -e "  $HL\$" -e "  $SD\$" "$P/.claude/.writ-manifest"`

**Expected Result:**
- Step 2: `exit 0`, `tree unchanged`, then:
  ```
    Stale files (removed upstream, would be deleted):
      🗑  scripts/recommend-state.py
      🗑  .writ/docs/recommended-delivery-state-format.md
  ```
- Step 3: `exit 0`, `🗑  Removed: scripts/recommend-state.py`, `🗑  Removed: .writ/docs/recommended-delivery-state-format.md`.
- Step 4: `0`, `0`.

**Status:** [x] Pass  [ ] Fail

**Notes:** The heading says "removed upstream" although upstream still has both files. That is today's wording and matches the spec's State Catalog.

agent-run 2026-10-21 @ b850e66: dry run `exit 0`, `tree unchanged`, both staging files listed under `Stale files (removed upstream, would be deleted):`; update `exit 0`, `🗑  Removed:` for both; step 4 `0`, `0`.

---

### Scenario 21: Update keeps edited staging copies on every run with their original baselines

**Source:** Acceptance Criteria — Story 4 (AC-4.3, modified half); Error Map (Update keeps a modified cut file: both rows); Experience Design (State: update, a copy edited locally; moment of truth)
**Feature:** none
**Verification:** human — no recipe
**Automated Test:** `scripts/tests/test_install_update_harness_cuts.sh` (AC-4.3 kept-project block)

**Preconditions:**
- Setup block pasted.

**Steps:**
1. `P="$W/s21"; inst "$P" claude > /dev/null 2>&1; plant_stage "$P" claude scripts/harness-cost.py; plant_stage "$P" claude $HL edit; plant_stage "$P" claude $SD edit`
2. `E1=$(h "$P/$HL"); E2=$(h "$P/$SD"); grep -e "  $HL\$" -e "  $SD\$" "$P/.claude/.writ-manifest" > "$W/s21-base.txt"`
3. `for run in 1 2; do upd "$P" claude > "$W/s21-$run.txt" 2>&1; echo "run $run exit $?"; grep -e 'Stale' -e 'Removed' -e 'Already up to date' "$W/s21-$run.txt"; [ "$(h "$P/$HL")" = "$E1" ] && [ "$(h "$P/$SD")" = "$E2" ] && echo "both edited copies unchanged"; grep -e "  $HL\$" -e "  $SD\$" "$P/.claude/.writ-manifest" | cmp -s - "$W/s21-base.txt" && echo "baselines kept"; done`

**Expected Result:**
- Run 1: `run 1 exit 0`; `⚠️  Stale (no longer shipped, locally modified — kept): scripts/recommend-state.py`; `⚠️  Stale (no longer shipped, locally modified — kept): .writ/docs/recommended-delivery-state-format.md`; `🗑  Removed: scripts/harness-cost.py`; `both edited copies unchanged`; `baselines kept`.
- Run 2: `run 2 exit 0`; the same two `⚠️  Stale …` lines; `✅ Already up to date! (<hash>)`; `both edited copies unchanged`; `baselines kept`.

**Status:** [x] Pass  [ ] Fail

**Notes:** The unmodified dev-only `harness-cost.py` makes run 1 rewrite the manifest (see Conventions).

agent-run 2026-10-21 @ b850e66: run 1 `exit 0`, both `⚠️  Stale (… — kept)` lines, `🗑  Removed: scripts/harness-cost.py`, `both edited copies unchanged`, `baselines kept`; run 2 `exit 0`, both Stale lines, `✅ Already up to date! (d732939)`, `both edited copies unchanged`, `baselines kept`.

---

### Scenario 22: Shipped files stop pointing at the staging script, and `SKILL.md` matches its generator

**Source:** Acceptance Criteria — Story 4 (AC-4.4); Error Map (Regenerate SKILL.md: `SKILL.md` and `gen-skill.sh` disagree)
**Feature:** none
**Verification:** human — no recipe
**Automated Test:** `scripts/tests/test_harness_cuts.py` (`DriftTriageHasNoRecommendedBranchTest`, `StagingIsNamedDevOnlyTest`); `scripts/tests/test_install_update_harness_cuts.sh` (AC-4.4 grep); `scripts/tests/test_agent_cli_contract_doc.py`

**Preconditions:**
- Setup block pasted.

**Steps:**
1. `cd "$REPO" && grep -n -i -e recommend -e 'sha-256' -e 'never batch' skills/drift-triage/SKILL.md; echo "exit $?"; sed -n '/^### Small/,/^### /p' skills/drift-triage/SKILL.md | head -6`
2. `grep -rnF -e 'scripts/recommend-state.py' -e 'recommend-state.py record-' commands agents skills adapters SKILL.md .writ/docs | grep -vF '.writ/docs/recommended-delivery-state-format.md:'; echo "exit $?"`
3. `sed -n '/^## Runtime Contract/,/^## Available/p' SKILL.md; bash scripts/gen-skill.sh --check | tail -1`
4. `grep -n 'recommend-state' .writ/docs/agent-cli-contract.md | cut -c1-160; grep -n "source-repo" .writ/docs/acceptance-criteria-ids.md`
5. `grep -n -e 'recommend-state.py' -e 'docs filter excludes' commands/update-writ.md | cut -c1-80`, then read lines 111, 115, and 124 in full.

**Expected Result:**
- Step 1: no grep hits, `exit 1`. The Small route reads "Auto-amend **only** `spec-lite.md` and append **one unique `DEV-NNN` entry** to `drift-log.md`." then "Continue **PASS**."
- Step 2: no output, `exit 1`.
- Step 3: the Runtime Contract says the state doc "records ADR-013's dormant staging design. It stays in the Writ source repo with its reducer and is not installed." Then `gen-skill: pass (SKILL.md matches .writ/manifest.yaml)`.
- Step 4: one line from `agent-cli-contract.md`, 126, the "Not in the table" note. Read in full, it lists six dev-only scripts ending with `recommend-state.py`, which "holds ADR-013's dormant staging reducers". No table row names it. Then line 34 of `acceptance-criteria-ids.md`: "Writ's source-repo `recommend-state.py` (dev-only, not installed) parses criterion lines …".
- Step 5: lines 111, 115, 124. Line 111 lists `recommend-state.py` among the dev-only helpers. Line 115 ships every doc except `recommended-delivery-state-format.md`. Line 124 counts "manifest-listed docs the docs filter excludes" as stale.

**Status:** [x] Pass  [ ] Fail

**Notes:** agent-run 2026-10-21 @ b850e66: step 1 no hits, `exit 1`, Small route text matches; step 2 `exit 1`; step 3 Runtime Contract text matches, `gen-skill: pass (SKILL.md matches .writ/manifest.yaml)`; step 4 line 126 lists six dev-only scripts ending `recommend-state.py` ("holds ADR-013's dormant staging reducers"), no table row, and `acceptance-criteria-ids.md:34` matches; step 5 lines 111, 115, 124 match.

**Implementation Reference:** Story 4 — `skills/drift-triage/SKILL.md`, `.writ/docs/agent-cli-contract.md`, `.writ/docs/acceptance-criteria-ids.md`, `commands/update-writ.md` Step 3, `scripts/gen-skill.sh` + `SKILL.md`; comments in `scripts/exit-criteria.py` and `scripts/story-deps.py` no longer name the script (Gate 3 iteration 1 finding).

---

### Scenario 23: Eval still runs the reducers in the source repo, and its lifecycle scenarios assert the new behavior

**Source:** Acceptance Criteria — Story 4 (AC-4.5); Error Map (Rewrite the eval lifecycle scenarios: the rewrite drops the reducer scenarios); Experience Design (State: Writ source repo)
**Feature:** none
**Verification:** human — no recipe
**Automated Test:** partial — `scripts/tests/test_harness_cuts.py` (`EvalLifecycleScenariosInvertedTest`) checks the eval source; the eval run below is the pass evidence (CI runs `eval.sh`).

**Preconditions:**
- Setup block pasted. Outside any sandbox. Step 3 takes about 70 s.

**Steps:**
1. `cd "$CL" && ls scripts/recommend-state.py .writ/docs/recommended-delivery-state-format.md scripts/eval-recommend-*.py`
2. `grep -o 'f"\(install\|update\|unlink\)-{platform}-[a-z-]*"' scripts/eval.sh`
3. `bash scripts/eval.sh --check=recommended-spec-implementation --report="$W/rsi.md" > /dev/null 2>&1; echo "exit $?"; grep -e '^Scenarios' -e '^Supplementary' -e 'Findings' "$W/rsi.md"`
4. `bash scripts/eval.sh --check=recommended-staging --report="$W/rs.md" > /dev/null 2>&1; echo "exit $?"; grep -e '^Scenarios' -e 'Findings' "$W/rs.md"`

**Expected Result:**
- Step 1: five files listed (the helper, the state doc, `eval-recommend-merge-release.py`, `eval-recommend-stage.py`, `eval-recommend-state-adversarial.py`).
- Step 2: exactly seven names: `install-{platform}-dry-run-names-neither`, `install-{platform}-omits-helper`, `install-{platform}-omits-state-doc`, `update-{platform}-dry-run-lists-stale`, `update-{platform}-removes-helper`, `update-{platform}-removes-state-doc`, `unlink-{platform}-skips-helper`. None of the old shipping names (`-helper-executable`, `-restores-`, `-copies-`, `-dry-run-helper`, `-dry-run-state-doc`) appear.
- Step 3: `exit 0`, `Scenarios: 147/147 passed`, `Supplementary static assertions: 16/16 passed`, `- Findings: 0`. 147 = 21 lifecycle (7 × 3 platforms) + 76 reducer + 50 adversarial.
- Step 4: `exit 0`, `Scenarios: 60/60 passed`, `- Findings: 0`.

**Status:** [x] Pass  [ ] Fail

**Notes:** agent-run 2026-10-21 @ b850e66: step 1 five files; step 2 exactly the seven names, none of the old ones; step 3 `exit 0`, `Scenarios: 147/147 passed`, `Supplementary static assertions: 16/16 passed`, `- Findings: 0`; step 4 `exit 0`, `Scenarios: 60/60 passed`, `- Findings: 0`.

---

### Scenario 24: Unlink leaves the helper symlink alone; the next update removes the converted state doc

**Source:** Acceptance Criteria — Story 4 (AC-4.5, unlink; AC-4.3, stale removal)
**Feature:** none
**Verification:** human — no recipe
**Automated Test:** partial — `eval.sh` `unlink-{platform}-skips-helper` covers the helper symlink; the update after unlink is manual only (the eval unlink state-doc scenarios were deleted by design).

**Preconditions:**
- Setup block pasted.

**Steps:**
1. Build a linked Claude Code install whose manifest version is the source's real commit:
   ```bash
   L="$W/s24"; mkdir -p "$L/.claude" "$L/scripts" "$L/.writ/docs"
   ln -s "$SRC/commands" "$L/.claude/commands"; ln -s "$SRC/claude-code/agents" "$L/.claude/agents"; ln -s "$SRC/claude-code/CLAUDE.md" "$L/CLAUDE.md"
   ln -s "$SRC/$HL" "$L/$HL"; ln -s "$SRC/$SD" "$L/$SD"
   printf '# mode: link\n# platform: claude\n# version: %s\n# link_target: %s\n' "$(git -C "$SRC" rev-parse --short HEAD)" "$SRC" > "$L/.claude/.writ-manifest"
   ```
2. `(cd "$L" && bash "$SRC/scripts/unlink.sh" --platform claude --no-commit --dry-run) > "$W/s24-dry.txt" 2>&1; echo "exit $?"; grep -c recommend-state "$W/s24-dry.txt"; grep -c 'recommended-delivery-state-format.md →' "$W/s24-dry.txt"`
3. `(cd "$L" && bash "$SRC/scripts/unlink.sh" --platform claude --no-commit) > "$W/s24.txt" 2>&1; echo "exit $?"; grep -c recommend-state "$W/s24.txt"; [ -L "$L/$HL" ] && [ "$(readlink "$L/$HL")" = "$SRC/$HL" ] && echo "helper symlink untouched"; [ -f "$L/$SD" ] && [ ! -L "$L/$SD" ] && echo "state doc is now a regular file"; grep -c "  $HL\$" "$L/.claude/.writ-manifest"; grep -c "  $SD\$" "$L/.claude/.writ-manifest"`
4. `upd "$L" claude > "$W/s24-upd.txt" 2>&1; echo "exit $?"; grep -e "$SD" -e recommend-state "$W/s24-upd.txt"; ls "$L/$SD" 2>&1 | sed 's/.*: //'; [ -L "$L/$HL" ] && echo "helper symlink still untouched"; grep -c -e "  $HL\$" -e "  $SD\$" "$L/.claude/.writ-manifest"`

**Expected Result:**
- Step 2: `exit 0`; `0` lines name `recommend-state`; `1` line converts the state doc symlink.
- Step 3: `exit 0`; `0`; `helper symlink untouched`; `state doc is now a regular file`; manifest `0` for the helper and `1` for the state doc.
- Step 4: `exit 0`; `🗑  Removed: .writ/docs/recommended-delivery-state-format.md`; `No such file or directory`; `helper symlink still untouched`; `0`.

**Status:** [x] Pass  [ ] Fail

**Notes:** Unlink writes a manifest without the `# baselines: shipped` header, so the first update takes the legacy path and rebuilds baselines from upstream at `# version:`. With a version upstream does not have (tried with `# version: fixture`), update preserves every differing file and lists nothing as stale, so the state doc copy stays. That is the dependency spec's legacy rule, not this spec's.

agent-run 2026-10-21 @ b850e66: step 2 `exit 0`, `0`, `1`; step 3 `exit 0`, `0`, `helper symlink untouched`, `state doc is now a regular file`, `0`, `1`; step 4 `exit 0`, `🗑  Removed: .writ/docs/recommended-delivery-state-format.md`, `No such file or directory`, `helper symlink still untouched`, `0`.

---

### Scenario 25: Re-installing over an old project leaves old copies on disk and out of the manifest

**Source:** Experience Design (State: re-install with `install.sh` over an old project) — Story 4; Error Map (Re-install over an old project: out of scope, documented behavior)
**Feature:** none
**Verification:** human — no recipe
**Automated Test:** `scripts/tests/test_install_update_harness_cuts.sh` (Codex re-install block)

**Preconditions:**
- Setup block pasted.

**Steps:**
1. `P="$W/s25"; inst "$P" codex > /dev/null 2>&1; cp "$SRC/$HL" "$P/$HL"; cp "$SRC/$SD" "$P/$SD"`
2. `inst "$P" codex > "$W/s25.txt" 2>&1; echo "exit $?"; grep -c -e recommend-state -e recommended-delivery "$W/s25.txt"`
3. `cmp "$SRC/$HL" "$P/$HL" && cmp "$SRC/$SD" "$P/$SD" && echo "both copies unchanged"; grep -c -e "  $HL\$" -e "  $SD\$" "$P/.codex/.writ-manifest"`

**Expected Result:**
- Step 2: `exit 0`, `0`.
- Step 3: `both copies unchanged`, `0`. `install.sh` never removes files, so old copies stay, untracked (same as the ADR-029 dev-only scripts).

**Status:** [x] Pass  [ ] Fail

**Notes:** agent-run 2026-10-21 @ b850e66: `exit 0`, `0`; `both copies unchanged`, `0`.

---

### Scenario 26: Staging copies without a manifest line are left alone and not recorded

**Source:** Error Map (Update removes an unmodified cut file: manifest has no line for it) — Story 4
**Feature:** none
**Verification:** human — no recipe
**Automated Test:** `scripts/tests/test_install_update_harness_cuts.sh` (Codex nil-input block)

**Preconditions:**
- Setup block pasted.

**Steps:**
1. `P="$W/s26"; inst "$P" codex > /dev/null 2>&1; cp "$SRC/$HL" "$P/$HL"; cp "$SRC/$SD" "$P/$SD"; plant_stage "$P" codex scripts/harness-cost.py`
2. `upd "$P" codex > "$W/s26.txt" 2>&1; echo "exit $?"; grep -e Removed -e Stale "$W/s26.txt"`
3. `cmp "$SRC/$HL" "$P/$HL" && cmp "$SRC/$SD" "$P/$SD" && echo "both copies unchanged"; grep -c -e "  $HL\$" -e "  $SD\$" "$P/.codex/.writ-manifest"`

**Expected Result:**
- Step 2: `exit 0`; the only line is `🗑  Removed: scripts/harness-cost.py` (proof the manifest was rewritten).
- Step 3: `both copies unchanged`, `0`.

**Status:** [x] Pass  [ ] Fail

**Notes:** agent-run 2026-10-21 @ b850e66: `exit 0`, only `🗑  Removed: scripts/harness-cost.py`; `both copies unchanged`, `0`.

---

### Scenario 27: Update with no manifest removes nothing

**Source:** Shadow Path (Update over an old install: Nil Input) — Stories 1, 4
**Feature:** none
**Verification:** human — no recipe
**Automated Test:** none — manual only

**Preconditions:**
- Setup block pasted.

**Steps:**
1. `P="$W/s27"; inst "$P" claude > /dev/null 2>&1; rm "$P/.claude/.writ-manifest"; printf '# old\n' > "$P/.claude/commands/implement-story.lean.md"; cp "$SRC/$HL" "$P/$HL"; cp "$SRC/$SD" "$P/$SD"`
2. `before=$(digest "$P"); upd "$P" claude > "$W/s27.txt" 2>&1; echo "exit $?"; grep -e 'No manifest' -e Removed -e Stale -e 'Already up to date' "$W/s27.txt"; [ "$(digest "$P")" = "$before" ] && echo "tree unchanged"`

**Expected Result:**
- Step 2: `exit 0`; `⚠️  No manifest found — this is an older installation.`; `✅ Already up to date! (<hash>)`; no `Removed` or `Stale` line; `tree unchanged`.

**Status:** [x] Pass  [ ] Fail

**Notes:** The spec's shadow path says "update refuses as today". It does not refuse: it warns and treats differing files as locally modified. The safety property holds: nothing is removed. Update also prints "A manifest will be created after update" but writes none when nothing differs. Both are behavior from before this spec.

agent-run 2026-10-21 @ b850e66: `exit 0`, `⚠️  No manifest found — this is an older installation.`, `✅ Already up to date! (d732939)`, no Removed or Stale line, `tree unchanged`.

---

### Scenario 28: Update whose manifest lists no cut file removes nothing

**Source:** Shadow Path (Update over an old install: Empty Input) — Stories 1, 4
**Feature:** none
**Verification:** human — no recipe
**Automated Test:** none — manual only

**Preconditions:**
- Setup block pasted.

**Steps:**
1. `P="$W/s28"; inst "$P" claude > /dev/null 2>&1`
2. `before=$(digest "$P"); upd "$P" claude > "$W/s28.txt" 2>&1; echo "exit $?"; grep -c -e Removed -e Stale "$W/s28.txt"; tail -1 "$W/s28.txt"; [ "$(digest "$P")" = "$before" ] && echo "tree unchanged"`

**Expected Result:**
- Step 2: `exit 0`, `0`, `✅ Already up to date! (<hash>)`, `tree unchanged`.

**Status:** [x] Pass  [ ] Fail

**Notes:** agent-run 2026-10-21 @ b850e66: `exit 0`, `0`, `✅ Already up to date! (d732939)`, `tree unchanged`.

---

### Scenario 29: A failed source clone stops update before it touches any cut file

**Source:** Shadow Path (Update over an old install: Upstream Error; Update with a modified cut file: Upstream Error) — Stories 1, 4
**Feature:** none
**Verification:** human — no recipe
**Automated Test:** none — manual only

**Preconditions:**
- Setup block pasted.

**Steps:**
1. `P="$W/s29"; inst "$P" claude > /dev/null 2>&1; plant_lean "$P" implement-story.lean.md; plant_lean "$P" verify-spec.lean.md edit; plant_stage "$P" claude $HL; plant_stage "$P" claude $SD edit`
2. `before=$(digest "$P"); UPSTREAM="$W/no-such-repo" upd "$P" claude > "$W/s29.txt" 2>&1; echo "exit $?"; grep -e '❌' -e Removed -e Stale "$W/s29.txt"; [ "$(digest "$P")" = "$before" ] && echo "tree unchanged"`

**Expected Result:**
- Step 2: `exit 1`; `❌ Failed to clone <W>/no-such-repo`; no `Removed` or `Stale` line; `tree unchanged`.

**Status:** [x] Pass  [ ] Fail

**Notes:** agent-run 2026-10-21 @ b850e66: `exit 1`, `❌ Failed to clone <W>/no-such-repo`, no Removed or Stale line, `tree unchanged`.

---

### Scenario 30: `update.sh --force` does not change stale handling

**Source:** Edge Case (`update.sh --force`) — Stories 1, 4
**Feature:** none
**Verification:** human — no recipe
**Automated Test:** none — manual only

**Preconditions:**
- Setup block pasted.

**Steps:**
1. `P="$W/s30"; inst "$P" claude > /dev/null 2>&1; plant_lean "$P" implement-story.lean.md; plant_lean "$P" verify-spec.lean.md edit; plant_stage "$P" claude $HL; plant_stage "$P" claude $SD edit`
2. `upd "$P" claude --force > "$W/s30.txt" 2>&1; echo "exit $?"; grep -e Removed -e Stale "$W/s30.txt"`
3. `ls "$P/.claude/commands" | grep '\.lean\.md$'; ls "$P/$HL" "$P/$SD" 2>&1 | sed "s|$P/||; s|.*: ||"`

**Expected Result:**
- Step 2: `exit 0`; `⚠️  Stale (no longer shipped, locally modified — kept): commands/verify-spec.lean.md`; `⚠️  Stale (no longer shipped, locally modified — kept): .writ/docs/recommended-delivery-state-format.md`; `🗑  Removed: commands/implement-story.lean.md`; `🗑  Removed: scripts/recommend-state.py`.
- Step 3: `verify-spec.lean.md`; `No such file or directory` (the helper); `.writ/docs/recommended-delivery-state-format.md` (kept).

**Status:** [x] Pass  [ ] Fail

**Notes:** `--force` overwrites customized shipped files, but edited stale files are still kept, the same as without it.

agent-run 2026-10-21 @ b850e66: `exit 0`, Stale-kept for `commands/verify-spec.lean.md` and the state doc, Removed for `commands/implement-story.lean.md` and `scripts/recommend-state.py`; step 3 `verify-spec.lean.md`, `No such file or directory`, `.writ/docs/recommended-delivery-state-format.md`.

---

### Scenario 31: Install from a source with no `.writ/docs` succeeds and records no docs

**Source:** Shadow Path (Install: Nil Input) — Story 4
**Feature:** none
**Verification:** human — no recipe
**Automated Test:** none — manual only

**Preconditions:**
- Setup block pasted.

**Steps:**
1. `N="$W/src-nodocs"; git clone -q "$SRC" "$N"; git -C "$N" rm -rq .writ/docs; git -C "$N" -c user.name=t -c user.email=t@example.invalid commit -qm "no docs"`
2. `P="$W/s31"; mkdir -p "$P"; (cd "$P" && bash "$N/scripts/install.sh" --platform claude --no-commit) > "$W/s31.txt" 2>&1; echo "exit $?"`
3. `ls -A "$P/.writ/docs" | wc -l; grep -c '  \.writ/docs/' "$P/.claude/.writ-manifest"; ls "$P/.claude/commands" | wc -l`

**Expected Result:**
- Step 2: `exit 0`.
- Step 3: `0` (the folder exists, empty), `0`, `33`.

**Status:** [x] Pass  [ ] Fail

**Notes:** agent-run 2026-10-21 @ b850e66: install `exit 0`; `0`, `0`, `33`.

---

### Scenario 32: A failed clone stops a standalone install before it writes anything

**Source:** Shadow Path (Install: Upstream Error) — Story 4
**Feature:** none
**Verification:** human — no recipe
**Automated Test:** none — manual only

**Preconditions:**
- Setup block pasted. The step rewrites GitHub URLs to a missing local path for this one command, so no network is used.

**Steps:**
1. `P="$W/s32"; mkdir -p "$P/bin"; cp "$SRC/scripts/install.sh" "$P/bin/"`
2. `(cd "$P" && GIT_CONFIG_COUNT=1 GIT_CONFIG_KEY_0='url.file:///nonexistent/.insteadOf' GIT_CONFIG_VALUE_0='https://github.com/' bash bin/install.sh --platform claude --no-commit) > "$W/s32.txt" 2>&1; echo "exit $?"; grep -e 'Cloning' -e '❌' "$W/s32.txt"; ls -A "$P"`

**Expected Result:**
- Step 2: `exit 1`; `📥 Cloning writ from GitHub...`; `❌ Failed to clone https://github.com/sellke/writ.git`; `bin` (nothing else was written).

**Status:** [x] Pass  [ ] Fail

**Notes:** `install.sh` clones only when it is not inside a Writ checkout. Every other scenario runs it from `$SRC`, which never clones.

agent-run 2026-10-21 @ b850e66: `exit 1`, `📥 Cloning writ from GitHub...`, `❌ Failed to clone https://github.com/sellke/writ.git`, `bin` only.

---

## Automated vs. Manual

| Kind | Scenarios | Count |
|---|---|---|
| Asserted by a committed test (CI runs it) | 1, 2, 3, 4, 7, 8, 9, 10, 11, 14, 15, 16, 17, 18, 19, 20, 21, 22, 25, 26 | 20 |
| Partly automated (a test covers part; suite runs, eval evidence, or extra paths by hand) | 5, 13, 23, 24 | 4 |
| Manual only | 6, 12, 27, 28, 29, 30, 31, 32 | 8 |

The test behind Scenarios 1 (repo-wide part) and 7 is red on `7922922`; see Known Issue.

## Not Covered by This Plan

- **`claude-code/CLAUDE.md:20` still says `/ship` is a "Branch to merged PR workflow".** It is installed into every Claude Code project's `CLAUDE.md` (Scenario 16, step 4). Story 3 left it out of scope; no open issue names it as of generation.
- **`.writ/docs/model-tiers.md` lines ~101, ~134, ~178 still describe the `escalated` signal.** Out of scope for Story 3; tracked in `.writ/issues/improvements/2026-10-20-retired-references-in-shipped-docs.md`.
- **DEV-005 is unresolved.** The guard test excludes two sibling spec folders that Business Rule 2 does not list. A human decides whether to amend Business Rule 2 and the Success Criteria (Scenario 7).
- **Re-install never removes old copies.** Out of scope by design; Scenario 25 checks the documented behavior only.
- **Unlink followed by update with a version upstream lacks** keeps the state doc copy (Scenario 24 Notes). Legacy-manifest behavior from `2026-10-20-ci-and-update-integrity`.
- **`.writ/docs/agent-cli-contract.md:81`** says a dev-only script needs a case arm in `install.sh` and `update.sh`; `unlink.sh` holds a third copy that must match (Business Rule 3). Doc wording only; behavior is correct (Scenario 18).

## Pending Stories

None. All four stories are Completed ✅.
