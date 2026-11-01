# UAT Plan: Shipped Command Hygiene

> **Generated:** 2026-10-21
> **Spec:** `.writ/specs/2026-10-20-shipped-command-hygiene/`
> **Stories Covered:** 3 of 3 completed
> **Total Scenarios:** 29
> **Verification recipe:** does not apply. Writ has no running app, so no `.writ/docs/app-verification.md` was drafted, saved, or bound. Every scenario is `human — no recipe`. The `**Automated Test:**` line on each scenario names the committed test or `eval.sh` check that already asserts the same behavior, if any.

## How to Use This Plan

1. Work through scenarios in order (they're grouped by story, ordered by priority)
2. For each scenario, follow the steps exactly as written
3. Mark Pass or Fail — add notes for any unexpected behavior
4. Scenarios marked Fail should be filed as issues or fed back to the spec
5. A feature passes UAT when all scenarios pass (or failures are accepted as known limitations)

**Conventions for this plan:**

- **Never run `install.sh` or `update.sh` in the Writ repo.** `.claude/` and `.cursor/` there are symlinks into the source. Scenario 12 installs from a clone into a new scratch project.
- Every mutation happens in a clone at `$CL`, never in `$REPO`. A `git clone` carries only committed files, so `.writ-lanes-*` folders and untracked files stay behind.
- Run the plan in `bash` on macOS (`sed -i ''`), outside any sandbox. `eval.sh` runs `git init` in temp folders, and some checks build install sandboxes.
- Paste this setup block once per shell:

  ```bash
  REPO=/Users/asellke/Projects/writ            # read from, never mutated or installed into
  W=$(mktemp -d "${TMPDIR:-/tmp}/writ-uat-hygiene.XXXXXX")
  CL="$W/clone"; git clone -q "$REPO" "$CL"   # committed tree on the current branch
  SPEC="$CL/.writ/specs/2026-10-20-shipped-command-hygiene"
  PM="$SPEC/pin-map.md"
  # ev <check>: run one eval check in the clone; print the exit code, findings, and counts.
  ev() { (cd "$CL" && bash scripts/eval.sh --check="$1" --report="$W/$1.md" >/dev/null 2>&1); echo "exit $?"
         grep -E '^- `|^Scenarios:|^- (Findings|Run errors):' "$W/$1.md" | cut -c1-220; }
  # reset: undo every edit to tracked files in the clone; prints nothing when clean.
  reset() { git -C "$CL" checkout -q -- . && git -C "$CL" status --short; }
  # The pin inventory recipe from technical-spec.md, saved outside the repo.
  awk '/^### Pin inventory recipe/{f=1} f&&/^```python/{p=1;next} p&&/^```/{exit} p' \
    "$SPEC/sub-specs/technical-spec.md" > "$W/pin-recipe.py"
  ```

- Expected output was observed on 2026-10-21 against `ef65139` (branch `phase/13-subtract-and-repair`). Line numbers, counts that grow with the repo, and temp paths will differ later.
- `loop-bounds` reports 37/37 in a clone. A working copy that holds `.writ/state/` run records also runs `historical-run-regression` and reports 38/38.
- After each scenario that edits the clone, run `reset` and confirm it prints nothing.
- When done: `rm -rf "$W"`.
- **Automated Test line:** names the test in `scripts/tests/` (or the `eval.sh` check) that asserts the behavior, `partial` when a test covers part of it, or `none — manual only`. CI runs pytest, every bash test, and `eval.sh` on each PR.

## Coverage Summary

| Story | Status | Scenarios | Source Breakdown |
|-------|--------|-----------|-----------------|
| Story 1: Strip Internal References and Add `shipped-refs` | ✅ Covered | 12 | AC: 6, Errors: 2, Shadow: 1, Edge: 1, Experience: 2 |
| Story 2: Pin Map and Conversions | ✅ Covered | 9 | AC: 6, Errors: 1, Shadow: 0, Edge: 0, Experience: 2 |
| Story 3: `create-spec.md` Reduction Pass | ✅ Covered | 8 | AC: 6, Errors: 0, Shadow: 0, Edge: 1, Experience: 1 |

The technical spec has an Error & Rescue Map but no Shadow Paths or Interaction Edge Cases tables. Shadow paths and edge cases come from `spec-lite.md` → For Testing Agents. Error-map rows, shadow paths, edge cases, and State Catalog rows that a scenario already exercises are named on its **Source** line and not counted twice.

**Automated vs. manual:** 13 scenarios are asserted by a committed test, 9 partly, 7 are manual only. Scenario 29 needs a person driving a `/create-spec` session. See the table at the end.

---

## Story 1: Strip Internal References and Add `shipped-refs`

### Scenario 1: The helper flags each kind of internal reference with file, line, kind, and token

**Source:** Acceptance Criteria — Story 1 (AC-1.1); Edge Case (old path to an archived spec → FAIL)
**Feature:** none
**Verification:** human — no recipe
**Automated Test:** `scripts/tests/test_eval_shipped_refs.py` (`HelperPositiveTests`)

**Preconditions:**
- Setup block pasted.

**Steps:**
1. Build a temp root with one line per kind and an archive folder for the old-path case:
   ```bash
   T="$W/s1"; mkdir -p "$T/commands" "$T/.writ/specs/archive/2026-07-18-logical-unit-revert"
   cat > "$T/commands/x.md" <<'EOF'
   See [ADR-013](../.writ/decision-records/adr-013-autonomy-governance.md).
   See [ADR-009](../../decision-records/adr-009-command-agent-skill-boundary.md).
   Design: `.writ/specs/archive/2026-08-12-machine-evaluable-exit-criteria/spec.md`.
   Technical spec: .writ/specs/2026-07-18-logical-unit-revert/sub-specs/technical-spec.md
   Cost: `.writ/research/2026-04-24-writ-vs-gstack-rigor-comparison.md`
     calibrated_against: "Observed: .writ/state/phase-execution-20260719-121255.json."
   EOF
   ```
2. `python3 "$CL/scripts/eval-shipped-refs.py" --root "$T"; echo "exit $?"`
3. `rmdir "$T/.writ/specs/archive/2026-07-18-logical-unit-revert"; python3 "$CL/scripts/eval-shipped-refs.py" --root "$T" | grep -c FAIL`

**Expected Result:**
- Step 2: four `PASS shipped-refs-rule-<kind>` lines, then six FAIL lines, then `exit 1`:
  - `shipped-refs:commands/x.md:1` `adr: decision-records/adr-013-autonomy-governance.md`
  - `shipped-refs:commands/x.md:2` `adr: decision-records/adr-009-command-agent-skill-boundary.md`
  - `shipped-refs:commands/x.md:3` `archived-spec: .writ/specs/archive/2026-08-12-machine-evaluable-exit-criteria`
  - `shipped-refs:commands/x.md:4` `archived-spec: .writ/specs/2026-07-18-logical-unit-revert`
  - `shipped-refs:commands/x.md:5` `research: .writ/research/2026-04-24-writ-vs-gstack-rigor-comparison.md`
  - `shipped-refs:commands/x.md:6` `calibration-state: .writ/state/phase-execution-20260719-121255.json`
- Step 3: `5`. Without the archive folder, the old-form path on line 4 is no longer a finding.

**Status:** [ ] Pass  [ ] Fail

**Notes:**

**Implementation Reference:** Story 1 — `scripts/eval-shipped-refs.py` (four rules; the old-path form checks `<root>/.writ/specs/archive/<name>/` on disk).

---

### Scenario 2: Runtime paths, globs, and example IDs produce no finding

**Source:** Acceptance Criteria — Story 1 (AC-1.2); Error Map (Run `shipped-refs`: runtime path flagged); Edge Case (example ID with no archive folder; `.writ/state/phase-execution-*.json` glob on a `calibrated_against` line)
**Feature:** none
**Verification:** human — no recipe
**Automated Test:** `scripts/tests/test_eval_shipped_refs.py` (`HelperNegativeTests`)

**Preconditions:**
- Setup block pasted.

**Steps:**
1. Build a temp root holding only runtime paths:
   ```bash
   T="$W/s2"; mkdir -p "$T/commands"
   cat > "$T/commands/x.md" <<'EOF'
   State lives in `.writ/state/`.
     calibrated_against: "Recalibrate against .writ/state/phase-execution-*.json records."
   Spec folder: `.writ/specs/<name>/`, archived as `.writ/specs/archive/<name>/`, ledger `.writ/specs/archive/LEDGER.md`.
   Research: `.writ/research/[DATE]-[topic-name]-research.md`.
   ADRs: `.writ/decision-records/adr-*.md`. Lifecycle: `.writ/docs/spec-lifecycle.md`.
   Example: `.writ/specs/2026-03-15-auth-system/spec.md`.
   EOF
   ```
2. `python3 "$CL/scripts/eval-shipped-refs.py" --root "$T"; echo "exit $?"`

**Expected Result:**
- Four `PASS shipped-refs-rule-<kind>` lines, then `PASS shipped-refs-tree`, then `exit 0`. No FAIL line.

**Status:** [ ] Pass  [ ] Fail

**Notes:**

---

### Scenario 3: An ADR link pasted into a command fails eval with its file and line

**Source:** Acceptance Criteria — Story 1 (AC-1.3); Experience Design (Moment of truth, Feedback, Error; State: tree clean, ADR link added)
**Feature:** none
**Verification:** human — no recipe
**Automated Test:** `scripts/tests/test_eval_shipped_refs.py` (`EvalMutationTests`)

**Preconditions:**
- Setup block pasted. Clone is clean (`reset` prints nothing).

**Steps:**
1. `ev shipped-refs`
2. `printf '\nSee [ADR-017](../.writ/decision-records/adr-017-git-notes-audit-channel.md).\n' >> "$CL/commands/ship.md"; ev shipped-refs`
3. `reset; ev shipped-refs`

**Expected Result:**
- Step 1: `exit 0`, `Scenarios: 5/5 passed`, `Findings: 0`, `Run errors: 0`.
- Step 2: `exit 1`; one finding that names the file and line first, then the kind and token, then the remediation: `` `shipped-refs:commands/ship.md:646`: adr: decision-records/adr-017-git-notes-audit-channel.md _Remediation:_ Remove the link to Writ's development history. If an installed user needs the reason, state it in one plain sentence. ``; `Scenarios: 4/5 passed`; `Findings: 1`.
- Step 3: `exit 0`, `Scenarios: 5/5 passed`.

**Status:** [ ] Pass  [ ] Fail

**Notes:**

**Implementation Reference:** Story 1 — `check_shipped_refs` in `scripts/eval.sh`, registered after `referenced-paths`.

---

### Scenario 4: Archived-spec and research paths fail eval with their own kinds

**Source:** Experience Design (State Catalog: dated archive or research path added; old path to an archived spec) — Story 1
**Feature:** none
**Verification:** human — no recipe
**Automated Test:** partial — `HelperPositiveTests` covers each kind at helper level; `EvalMutationTests` covers only the `adr` kind through `eval.sh`

**Preconditions:**
- Setup block pasted. Clone is clean.

**Steps:**
1. Put back the old `revert.md` clause Story 1 removed, and add a research path and a dated archive path:
   ```bash
   sed -i '' 's|^- Resolver: `scripts/revert-resolve.py`$|- Resolver: `scripts/revert-resolve.py` · Technical spec: `.writ/specs/2026-07-18-logical-unit-revert/sub-specs/technical-spec.md`|' "$CL/commands/revert.md"
   printf 'Background: `.writ/research/2026-04-24-writ-vs-gstack-rigor-comparison.md`\n' >> "$CL/commands/research.md"
   printf 'Design: `.writ/specs/archive/2026-08-12-machine-evaluable-exit-criteria/spec.md`\n' >> "$CL/commands/status.md"
   git -C "$CL" diff --stat
   ```
2. `ev shipped-refs`
3. `reset`

**Expected Result:**
- Step 1: three files changed (`research.md`, `revert.md`, `status.md`).
- Step 2: `exit 1`, `Scenarios: 4/7 passed`, `Findings: 3`:
  - `shipped-refs:commands/research.md:190` `research: .writ/research/2026-04-24-writ-vs-gstack-rigor-comparison.md`
  - `shipped-refs:commands/revert.md:178` `archived-spec: .writ/specs/2026-07-18-logical-unit-revert` (the clone has `.writ/specs/archive/2026-07-18-logical-unit-revert/`)
  - `shipped-refs:commands/status.md:499` `archived-spec: .writ/specs/archive/2026-08-12-machine-evaluable-exit-criteria`
- Step 3: prints nothing.

**Status:** [ ] Pass  [ ] Fail

**Notes:** The contract grep (Scenario 8) misses the `revert.md` form; only the on-disk archive check catches it.

---

### Scenario 5: A missing helper is a run error, not a pass

**Source:** Error Map (Run `shipped-refs`: helper missing) — Story 1 (AC-1.3); Shadow Path (Nil input); Experience Design (State: helper missing)
**Feature:** none
**Verification:** human — no recipe
**Automated Test:** `scripts/tests/test_eval_shipped_refs.py` (`EvalMutationTests.test_check_passes_bites_recovers_and_errors_without_the_helper`)

**Preconditions:**
- Setup block pasted. Clone is clean.

**Steps:**
1. `mv "$CL/scripts/eval-shipped-refs.py" "$W/"; ev shipped-refs`
2. `mv "$W/eval-shipped-refs.py" "$CL/scripts/"; ev shipped-refs; reset`

**Expected Result:**
- Step 1: `exit 2`; `` `scripts/eval-shipped-refs.py`: shipped-refs helper is missing. _Remediation:_ Restore scripts/eval-shipped-refs.py (shipped-command-hygiene spec, Story 1). ``; `Findings: 1`; `Run errors: 1`.
- Step 2: `exit 0`, `Scenarios: 5/5 passed`; `reset` prints nothing.

**Status:** [ ] Pass  [ ] Fail

**Notes:**

---

### Scenario 6: No command files to scan is a run error at helper and eval level

**Source:** Shadow Path (Empty input) — Story 1; DEV-002
**Feature:** none
**Verification:** human — no recipe
**Automated Test:** partial — `test_missing_commands_directory_is_a_run_error_not_a_pass` covers the helper; the eval-level branch (helper exit above 1) has no test, per the Story 1 reviewer residual

**Preconditions:**
- Setup block pasted. Clone is clean.

**Steps:**
1. `T="$W/s6"; mkdir -p "$T/commands"; python3 "$CL/scripts/eval-shipped-refs.py" --root "$T"; echo "exit $?"`
2. `mv "$CL/commands" "$W/commands.bak"; ev shipped-refs`
3. `mv "$W/commands.bak" "$CL/commands"; ev shipped-refs; reset`

**Expected Result:**
- Step 1: the four rule self-tests print PASS; stderr says `eval-shipped-refs: no shipped command files under <T> (commands/*.md)`; `exit 2`. There is no `PASS shipped-refs-tree` line.
- Step 2: `exit 2`; `` `scripts/eval-shipped-refs.py`: shipped-refs helper failed to run (exit 2). ``; `Run errors: 1`.
- Step 3: `exit 0`, `Scenarios: 5/5 passed`; `reset` prints nothing.

**Status:** [ ] Pass  [ ] Fail

**Notes:**

---

### Scenario 7: A rule regex that matches nothing fails its own self-test

**Source:** Error Map (Run `shipped-refs`: a rule regex broken) — Story 1; Shadow Path (Upstream error); Experience Design (State: a rule regex broken)
**Feature:** none
**Verification:** human — no recipe
**Automated Test:** `scripts/tests/test_eval_shipped_refs.py` (`SelfTestTests.test_a_dead_rule_fails_its_own_scenario`)

**Preconditions:**
- Setup block pasted. Clone is clean.

**Steps:**
1. `sed -i '' 's/r"decision-records\/adr-/r"NEVER-MATCHES-adr-/' "$CL/scripts/eval-shipped-refs.py"; git -C "$CL" diff --stat`
2. `python3 "$CL/scripts/eval-shipped-refs.py"; echo "exit $?"`
3. `ev shipped-refs`
4. `reset`

**Expected Result:**
- Step 1: `scripts/eval-shipped-refs.py | 2 +-`.
- Step 2: `FAIL shipped-refs-rule-adr missed: [ADR-017](…) ; missed: [ADR-009](…)`; the other three rules PASS; `PASS shipped-refs-tree` (the dead rule hides nothing on the clean tree, but the check still fails); `exit 1`.
- Step 3: `exit 1`; finding `` `shipped-refs-rule-adr` `` with remediation `Fix the rule's pattern in scripts/eval-shipped-refs.py.`
- Step 4: prints nothing.

**Status:** [ ] Pass  [ ] Fail

**Notes:**

---

### Scenario 8: The real tree passes, and the contract grep returns only runtime paths

**Source:** Acceptance Criteria — Story 1 (AC-1.4); Experience Design (Entry point, Happy path)
**Feature:** none
**Verification:** human — no recipe
**Automated Test:** partial — `RealTreeTests.test_real_tree_is_clean` and `eval.sh --check=shipped-refs` in CI; reading the grep output is manual

**Preconditions:**
- Setup block pasted. Clone is clean.

**Steps:**
1. `ev shipped-refs`
2. `cd "$CL" && grep -n -E '\.writ/(specs/archive|research)/|decision-records/adr-|calibrated_against' commands/*.md | cut -c1-120`
3. `grep -h 'calibrated_against' commands/*.md | grep -oE '\.writ/(state|specs/archive)[^ "]*' | sort | uniq -c`

**Expected Result:**
- Step 1: `exit 0`, `Scenarios: 5/5 passed`.
- Step 2: 26 lines. Each is one of:
  - a runtime directory, placeholder, or glob: `create-spec.md:263` (`.writ/specs/archive/**`), `create-adr.md:42,47,153`, `implement-spec.md:53`, `migrate.md:26`, `research.md:5,8,130,175,182`, `status.md:268,278,483`, `release.md:170`, `verify-spec.md:47,639,676`;
  - a `calibrated_against` value: `implement-phase.md:16,21`, `implement-spec.md:15`, `implement-story.md:15,20,24`, `refactor.md:15`, `verify-spec.md:15`.
  - None names a dated archived spec, a dated research file, or an `adr-NNN-` file.
- Step 3: `1 .writ/state/execution-*.json` and `1 .writ/state/phase-execution-*.json`. Both are globs; no value names a single record.

**Status:** [ ] Pass  [ ] Fail

**Notes:**

---

### Scenario 9: Removed links left no bare ADR label, and only reference lines changed

**Source:** Acceptance Criteria — Story 1 (AC-1.4); Error Map (Strip a link: a bare `ADR-NNN` label left behind); Business Rule 4 (Removal)
**Feature:** none
**Verification:** human — no recipe
**Automated Test:** none — manual only

**Preconditions:**
- Setup block pasted. The clone holds full history.

**Steps:**
1. `cd "$CL" && git show --format='%h %s' --stat 7967ea3 ce6e8ac -- commands/ | grep -E '^[0-9a-f]{7} |changed'`
2. Count ADR labels on removed and added lines:
   ```bash
   git show --format= 7967ea3 ce6e8ac -- commands/ | grep -E '^-' | grep -v '^--- ' | grep -cE 'ADR-[0-9]{3}'
   git show --format= 7967ea3 ce6e8ac -- commands/ | grep -E '^\+' | grep -v '^+++ ' | grep -cE 'ADR-[0-9]{3}'
   ```
3. Read the reference diff: `git show --format= -U0 7967ea3 -- commands/ | cut -c1-200`
4. Check the kept and added sentences:
   ```bash
   grep -c 'Tier 2 is structural only — not an LLM-as-judge.' commands/refresh-command.md
   grep -c 'measured at about \$0.15 and' commands/refresh-command.md
   grep -c 'This check does not use a harness `/goal` Stop hook.' commands/implement-phase.md
   ```

**Expected Result:**
- Step 1: `7967ea3` touches 9 command files (13 insertions, 19 deletions); `ce6e8ac` touches 4 (5 insertions, 5 deletions). `implement-phase.md` is in both, so together that is the 12 files the technical spec lists.
- Step 2: `11` removed lines carried an ADR label; `0` added lines do.
- Step 3: every hunk is one of the 14 ADR, archived-spec, or research rows in technical-spec.md → Internal references, or one of the two replacement sentences (`implement-phase.md` `/goal` hook, `refresh-command.md` cost reason). `new-command.md` keeps its `model-tiers.md` link; `release.md` and `ship.md` keep their `git-notes-audit-format.md` links. No unrelated wording changed.
- Step 4: `1`, `1`, `1`.

**Status:** [ ] Pass  [ ] Fail

**Notes:** Diff against each commit's own parent (`git show`), not against an older base. A wider range picks up unrelated edits from merged lanes.

**Implementation Reference:** Story 1 — `7967ea3` (link removals), `ce6e8ac` (`calibrated_against` rewrites).

---

### Scenario 10: Rewritten `calibrated_against` values pass `loop-bounds`, and drift in them fails

**Source:** Acceptance Criteria — Story 1 (AC-1.5); Error Map (Rewrite `calibrated_against`: no path token; Rewrite refactor's value: literal dropped); Experience Design (State: `calibrated_against` names a `.writ/state/` file)
**Feature:** none
**Verification:** human — no recipe
**Automated Test:** partial — `test_eval_shipped_refs.py` (`CalibrationValueTests`) asserts the current values; the three mutations below are by hand

**Preconditions:**
- Setup block pasted. Clone is clean.

**Steps:**
1. `ev loop-bounds`
2. `cd "$CL" && grep -h 'calibrated_against' commands/implement-phase.md commands/implement-spec.md commands/implement-story.md commands/refactor.md | cut -c1-110`
3. Drop the refactor literal: `sed -i '' 's/calibrated_against: "no recorded run - Writ had/calibrated_against: "Writ had/' commands/refactor.md; ev loop-bounds; reset`
4. Strip every path token from one value: `sed -i '' 's/^  calibrated_against: "Counts stories dispatched.*$/  calibrated_against: "Set from experience."/' commands/implement-spec.md; ev loop-bounds; reset`
5. Cite a single run record: `sed -i '' 's|Recalibrate against this project|Observed: .writ/state/execution-20260718-1101.json. Recalibrate against this project|' commands/implement-spec.md; ev shipped-refs; reset`

**Expected Result:**
- Step 1: `exit 0`, `Scenarios: 37/37 passed` (38/38 on a working copy with run records).
- Step 2: seven values (two in `implement-phase.md`, three in `implement-story.md`). `refactor.md`'s starts `no recorded run - Writ had no recorded /refactor execution…`. The others cite `commands/…`, `agents/…`, `scripts/…`, or a `.writ/state/…-*.json` glob.
- Step 3: `exit 1`, `Scenarios: 36/37 passed`; finding `loop-bounds:refactor-no-recorded-run-literal` (`commands/refactor.md's calibrated_against must contain the literal 'no recorded run'…`).
- Step 4: `exit 1`, `Scenarios: 36/37 passed`; finding `loop-bounds:schema-implement-spec` (`…calibrated_against cites no path and does not say 'no recorded run'…`).
- Step 5: `exit 1`; finding `shipped-refs:commands/implement-spec.md:15` `calibration-state: .writ/state/execution-20260718-1101.json`.
- Each `reset` prints nothing.

**Status:** [ ] Pass  [ ] Fail

**Notes:**

---

### Scenario 11: `_preamble.md` is scanned; `agents/` is not

**Source:** Edge Case — Story 1 (Business Rule 1: shipped commands include `_preamble.md`; Scope out: `agents/`)
**Feature:** none
**Verification:** human — no recipe
**Automated Test:** `scripts/tests/test_eval_shipped_refs.py` (`test_preamble_is_a_shipped_command_and_is_scanned`, `test_other_directories_are_not_scanned`, `test_scanned_directories_live_in_one_constant`)

**Preconditions:**
- Setup block pasted. Clone is clean.

**Steps:**
1. `L='See [ADR-017](../.writ/decision-records/adr-017-git-notes-audit-channel.md).'; printf '\n%s\n' "$L" >> "$CL/agents/coding-agent.md"; ev shipped-refs`
2. `printf '\n%s\n' "$L" >> "$CL/commands/_preamble.md"; ev shipped-refs`
3. `reset`

**Expected Result:**
- Step 1: `exit 0`, `Scenarios: 5/5 passed`. An ADR link in an agent file is out of scope for this spec.
- Step 2: `exit 1`; one finding, `shipped-refs:commands/_preamble.md:80`; none for `agents/coding-agent.md`.
- Step 3: prints nothing.

**Status:** [ ] Pass  [ ] Fail

**Notes:** Widening the scan to `agents/`, `adapters/`, `skills/`, and `.writ/docs/` is a later pass (`SCANNED_DIRS` in the helper).

---

### Scenario 12: An installed project's commands name no Writ-only path, and the eval helpers are not installed

**Source:** Experience Design (Who uses it: a developer in an installed project) — Story 1; Business Rule 12 (eval helpers are dev-only)
**Feature:** none
**Verification:** human — no recipe
**Automated Test:** partial — `scripts/tests/test_install_update_dev_scripts.sh` covers dev-only `eval*` exclusion; no test greps an installed copy for Writ-only links

**Preconditions:**
- Setup block pasted. This installs from the clone into a new scratch project, never into the Writ repo.

**Steps:**
1. `P="$W/proj"; mkdir -p "$P" && git -C "$P" init -q && (cd "$P" && bash "$CL/scripts/install.sh" --platform claude --no-commit) > "$W/inst.txt" 2>&1; echo "exit $?"`
2. `ls "$P/.claude/commands" | wc -l; cmp "$P/.claude/commands/create-spec.md" "$CL/commands/create-spec.md" && echo same`
3. `grep -rnE 'decision-records/adr-[0-9]{3}|\.writ/specs/archive/[0-9]{4}-|\.writ/research/[0-9]{4}-' "$P/.claude/commands/" | wc -l`
4. `ls "$P/scripts" | grep -c '^eval'; grep -c 'eval-shipped-refs\|eval-command-structure' "$P/.claude/.writ-manifest"`

**Expected Result:**
- Step 1: `exit 0`.
- Step 2: `33`, `same`.
- Step 3: `0`.
- Step 4: `0`, `0`.

**Status:** [ ] Pass  [ ] Fail

**Notes:** Keep `$P` for Scenario 29.

---

## Story 2: Pin Map and Conversions

### Scenario 13: The pin inventory recipe reproduces the pin map's before and after counts

**Source:** Acceptance Criteria — Story 2 (AC-2.1, AC-2.4); Error Map (Inventory pins: recipe misses a pin form; Start before dependencies land: lean files present)
**Feature:** none
**Verification:** human — no recipe
**Automated Test:** partial — `test_eval_command_structure.py` (`PinMapTests.test_header_totals_match_the_rows_and_the_count_fell`) checks the header's arithmetic; `test_harness_cuts.py` checks no lean file exists; re-running the recipe is manual

**Preconditions:**
- Setup block pasted (it saves the recipe as `$W/pin-recipe.py`).

**Steps:**
1. `cd "$CL" && ls commands/*.lean.md; echo "exit $?"`
2. Run the recipe on `eval.sh` at the inventory commit and now:
   ```bash
   git show 04799a9:scripts/eval.sh > "$W/eval-before.sh"
   python3 "$W/pin-recipe.py" "$W/eval-before.sh" > "$W/pins-before.tsv" 2> "$W/pins-before.err"
   python3 "$W/pin-recipe.py" scripts/eval.sh     > "$W/pins-now.tsv"    2> "$W/pins-now.err"
   for f in before now; do echo "$f: $(wc -l < "$W/pins-$f.tsv" | tr -d ' ') rows, $(cut -f2 "$W/pins-$f.tsv" | sort -u | wc -l | tr -d ' ') lines, $(tail -1 "$W/pins-$f.err"), $(grep -c '^unresolved' "$W/pins-$f.err") unresolved"; done
   grep -c -E '^\s*(require_literal|forbid_literal|forbid_literal_ci) ' "$W/eval-before.sh" scripts/eval.sh
   grep '^unresolved' "$W/pins-now.err" | cut -f2 | sort | uniq -c
   ```
3. `sed -n 3,5p "$PM"`

**Expected Result:**
- Step 1: `ls: commands/*.lean.md: No such file or directory`, `exit 1`.
- Step 2: `before: 207 rows, 199 lines, parsed 572 pin call lines, 22 unresolved`; `now: 144 rows, 144 lines, parsed 518 pin call lines, 22 unresolved`. `grep -c` gives `572` and `518`, equal to the parsed counts. The 22 unresolved targets are `check_autonomy_governance` 13, `check_exit_criteria` 5, `check_recommended_spec_implementation` 4 (spec files read through `resolve_spec_path`, not commands).
- Step 3: `Inventory commit: 04799a9`; `Before: 207 instances at 199 call sites · After: 144 instances at 144 call sites`; `keep 144 · convert 29 · remove 34 · 144 + 29 + 34 = 207`.

**Status:** [ ] Pass  [ ] Fail

**Notes:**

**Implementation Reference:** Story 2 — `pin-map.md` (207 rows at `04799a9`).

---

### Scenario 14: Every pin-map row matches the inventory; keep literals are still pinned; convert and remove literals are gone

**Source:** Acceptance Criteria — Story 2 (AC-2.1, AC-2.2, AC-2.4)
**Feature:** none
**Verification:** human — no recipe
**Automated Test:** none — manual only. `PinMapTests` checks the map's internal shape, not the map against `eval.sh`

**Preconditions:**
- Scenario 13 done (`$W/pins-before.tsv` and `$W/pins-now.tsv` exist).

**Steps:**
1. Save the checker:
   ```bash
   cat > "$W/pinmap-check.py" <<'EOF'
   """Check pin-map.md against the recipe output before and after Story 2."""
   import re, sys
   from collections import Counter
   pin_map, before_tsv, now_tsv = sys.argv[1:4]
   SAFETY = {"prime-directive", "recommend-boundary", "gate-class", "loop-bound",
             "script-invocation", "verdict-provenance", "parsed-format"}
   def literal(cell):                       # undo Markdown code-span quoting
       m = re.match(r"^(`+)(.*?)\1$", cell.strip())
       body = m.group(2) if m else cell.strip()
       if m and len(body) > 1 and body[0] == body[-1] == " " and body.strip():
           body = body[1:-1]
       return body.replace("\\|", "|")
   def pins(path):                           # recipe TSV: function, line, kind, target, literal
       return [l.rstrip("\n").split("\t") for l in open(path, encoding="utf-8")]
   rows = [[c.strip() for c in re.split(r"(?<!\\)\|", l.strip())[1:-1]]
           for l in open(pin_map, encoding="utf-8") if re.match(r"^\| \d+ \|", l)]
   before = Counter((t, s) for _, _, _, t, s in pins(before_tsv))
   before_at = {(int(n), t) for _, n, _, t, _ in pins(before_tsv)}
   now = Counter((t, s) for _, _, _, t, s in pins(now_tsv))
   problems = []
   for n, fn, line, target, kind, lit, cat, disp, reason in rows:
       key = (target, literal(lit))
       if key not in before or (int(line), target) not in before_at:
           problems.append(f"row {n}: not in the recipe output at the inventory commit")
       if cat in SAFETY and disp == "remove":
           problems.append(f"row {n}: safety category {cat} is marked remove")
       if disp == "keep" and key not in now:
           problems.append(f"row {n}: keep literal no longer pinned: {key[1]!r} on {target}")
       if disp in ("convert", "remove") and key in now:
           problems.append(f"row {n}: {disp} literal still pinned: {key[1]!r} on {target}")
   tally = Counter((r[6], r[7]) for r in rows)
   for cat in sorted({c for c, _ in tally}):
       print(f"{cat:20} " + "  ".join(f"{d} {tally[(cat, d)]}" for d in ("keep", "convert", "remove") if tally[(cat, d)]))
   d = Counter(r[7] for r in rows)
   print(f"rows {len(rows)}: keep {d['keep']}, convert {d['convert']}, remove {d['remove']}; pins on commands/ now {sum(now.values())}")
   print("\n".join(problems) if problems else "no problems")
   EOF
   ```
2. `python3 "$W/pinmap-check.py" "$PM" "$W/pins-before.tsv" "$W/pins-now.tsv"`
3. Prove the checker bites: delete one keep pin from the clone's `eval.sh` and re-run:
   ```bash
   sed -i '' '/verbatim private transcript bodies/d' "$CL/scripts/eval.sh"
   python3 "$W/pin-recipe.py" "$CL/scripts/eval.sh" > "$W/pins-sab.tsv" 2>/dev/null
   python3 "$W/pinmap-check.py" "$PM" "$W/pins-before.tsv" "$W/pins-sab.tsv" | tail -2; reset
   ```

**Expected Result:**
- Step 2:
  ```
  gate-class           keep 58  convert 2
  loop-bound           keep 6
  parsed-format        keep 17
  prime-directive      keep 8  convert 1
  recommend-boundary   keep 12  convert 2
  retired-text         remove 12
  script-invocation    keep 3  convert 15
  structure            keep 10  convert 9  remove 7
  verdict-provenance   keep 30
  wording              remove 15
  rows 207: keep 144, convert 29, remove 34; pins on commands/ now 144
  no problems
  ```
  Every `remove` falls in `retired-text`, `structure`, or `wording`.
- Step 3: `…pins on commands/ now 143` and `row 110: keep literal no longer pinned: 'verbatim private transcript bodies' on commands/refresh-command.md`; `reset` prints nothing.

**Status:** [ ] Pass  [ ] Fail

**Notes:**

---

### Scenario 15: No safety-category row is `remove`, and a planted one fails the tests

**Source:** Acceptance Criteria — Story 2 (AC-2.2, AC-2.4); Error Map (Mark a safety row `remove`); Experience Design (State: safety pin marked `remove` in the map)
**Feature:** none
**Verification:** human — no recipe
**Automated Test:** `scripts/tests/test_eval_command_structure.py` (`PinMapTests`)

**Preconditions:**
- Setup block pasted. Clone is clean.

**Steps:**
1. `cd "$CL" && uv run --python 3.9 pytest -q scripts/tests/test_eval_command_structure.py -k PinMap 2>&1 | tail -1`
2. Mark row 2 (`recommend-boundary`, keep) as remove: `sed -i '' 's/^\(| 2 | .*| recommend-boundary | \)keep |/\1remove |/' "$PM"; grep '^| 2 |' "$PM" | cut -c1-200`
3. `uv run --python 3.9 pytest -q scripts/tests/test_eval_command_structure.py -k PinMap 2>&1 | grep -E 'FAILED|passed|failed'`
4. `reset`

**Expected Result:**
- Step 1: `4 passed, 30 deselected`.
- Step 2: row 2 now reads `… | recommend-boundary | remove | …`.
- Step 3: `FAILED …PinMapTests::test_no_safety_row_is_removed` and `FAILED …PinMapTests::test_header_totals_match_the_rows_and_the_count_fell`; `2 failed, 2 passed`.
- Step 4: prints nothing.

**Status:** [ ] Pass  [ ] Fail

**Notes:**

---

### Scenario 16: A kept safety pin still fails eval when its command text drifts

**Source:** Acceptance Criteria — Story 2 (AC-2.2); spec.md → Hardest Constraint
**Feature:** none
**Verification:** human — no recipe
**Automated Test:** none — manual only (no test mutates these two literals)

**Preconditions:**
- Setup block pasted. Clone is clean.

**Steps:**
1. Row 110 (`prime-directive`, keep): `sed -i '' 's/verbatim private transcript bodies/private transcript text/' "$CL/commands/refresh-command.md"; ev refresh-evidence; reset`
2. Row 118 (`gate-class`, keep): `sed -i '' 's/does not commit/commits when done/' "$CL/commands/knowledge.md"; ev knowledge-consolidate; reset`

**Expected Result:**
- Step 1: `exit 1`; `` `commands/refresh-command.md`: refresh-command must forbid storing verbatim private transcript bodies (Prime Directive privacy). ``; `Findings: 1`.
- Step 2: `exit 1`; `` `commands/knowledge.md`: Knowledge --consolidate must leave a reviewable diff without committing. ``; `Findings: 1`.
- Each `reset` prints nothing.

**Status:** [ ] Pass  [ ] Fail

**Notes:** Scenario 25 does the same for a `loop-bound` keep row on `create-spec.md` (row 67).

---

### Scenario 17: A converted pin fails when its structure breaks, which the old substring pin did not catch

**Source:** Acceptance Criteria — Story 2 (AC-2.3); Edge Case (heading text left only as prose → `command-structure` FAIL); Experience Design (State: heading demoted to prose after conversion)
**Feature:** none
**Verification:** human — no recipe
**Automated Test:** `scripts/tests/test_eval_command_structure.py` (`TableTests.test_each_row_passes_on_its_real_target_and_fails_on_its_mutation`, `PhaseStateRowTests`)

**Preconditions:**
- Setup block pasted. Clone is clean.

**Steps:**
1. Demote row 78's heading to prose and reduce row 31's call to a bare mention:
   ```bash
   sed -i '' 's/^## User Challenge (Scope-Degradation Escalation)/User Challenge (Scope-Degradation Escalation)/' "$CL/commands/_preamble.md"
   sed -i '' 's|scripts/archive-sweep.py sweep|archive-sweep.py|g' "$CL/commands/status.md"
   grep -c '## User Challenge' "$CL/commands/_preamble.md"; grep -c 'archive-sweep.py' "$CL/commands/status.md"
   ```
2. `ev command-structure`
3. `reset; ev command-structure`

**Expected Result:**
- Step 1: `0` (no `## User Challenge` line is left, though the words remain as prose) and a count of at least `1` (the script name survives as a mention, which a substring pin on `archive-sweep.py` would still accept).
- Step 2: `exit 1`; `Scenarios: 31/33 passed`; two findings:
  - `` `command-structure:commands/status.md:invocation:scripts/archive-sweep.py sweep` `` … `(no line calls 'scripts/archive-sweep.py sweep'; was check_archive_sweep)`
  - `` `command-structure:commands/_preamble.md:heading:User Challenge` `` … `(no heading outside fenced code starts with 'User Challenge'; was check_phase_challenges)`
- Step 3: `exit 0`, `Scenarios: 33/33 passed`.

**Status:** [ ] Pass  [ ] Fail

**Notes:** The table has 30 rows: 13 `heading`, 17 `invocation`, no `frontmatter` row. The `frontmatter` kind is exercised only by the helper's self-test and `FrontmatterKindTests`.

**Implementation Reference:** Story 2 — `scripts/eval-command-structure.py` (`ROWS`, one self-test per kind), `check_command_structure` in `scripts/eval.sh`.

---

### Scenario 18: `command-structure` passes on the tree, and a missing helper or missing `commands/` is a run error

**Source:** Error Map (Convert a pin: structural row passes vacuously) — Story 2 (AC-2.3)
**Feature:** none
**Verification:** human — no recipe
**Automated Test:** `scripts/tests/test_eval_command_structure.py` (`RealTreeTests`, `EvalWiringTests`, `OutputTests.test_missing_commands_directory_is_a_run_error_not_a_pass`, `SelfTestTests`)

**Preconditions:**
- Setup block pasted. Clone is clean.

**Steps:**
1. `python3 "$CL/scripts/eval-command-structure.py" | cut -f1 | sort | uniq -c`
2. `mv "$CL/scripts/eval-command-structure.py" "$W/"; ev command-structure; mv "$W/eval-command-structure.py" "$CL/scripts/"`
3. `mv "$CL/commands" "$W/commands.bak"; ev command-structure; mv "$W/commands.bak" "$CL/commands"`
4. `ev command-structure; reset`

**Expected Result:**
- Step 1: `33 PASS` (3 kind self-tests and 30 rows).
- Step 2: `exit 2`; `` `scripts/eval-command-structure.py`: command-structure helper is missing. ``; `Run errors: 1`.
- Step 3: `exit 2`; `` `scripts/eval-command-structure.py`: command-structure helper failed to run (exit 2). ``; `Run errors: 1`.
- Step 4: `exit 0`, `Scenarios: 33/33 passed`; `reset` prints nothing.

**Status:** [ ] Pass  [ ] Fail

**Notes:**

---

### Scenario 19: Rewording text behind a removed pin needs no eval edit

**Source:** Experience Design (Who uses it: the maintainer rewords a command) — Story 2
**Feature:** none
**Verification:** human — no recipe
**Automated Test:** none — manual only

**Preconditions:**
- Scenario 13 done (`$W/eval-before.sh` exists). Clone is clean.

**Steps:**
1. Reword the text behind rows 116 (`merge, never append`), 21 (`topological`), and 22 (`roadmap order`):
   ```bash
   sed -i '' 's/merge, never append/merge into the existing entry instead of appending/' "$CL/commands/knowledge.md"
   sed -i '' 's/topological/dependency/g; s/roadmap order/the order the roadmap lists/g' "$CL/commands/implement-phase.md"
   git -C "$CL" diff --stat
   ```
2. `ev knowledge-consolidate; ev spec-dependencies`
3. For contrast, run the same checks with `eval.sh` from the inventory commit: `cp "$W/eval-before.sh" "$CL/scripts/eval.sh"; ev spec-dependencies; ev knowledge-consolidate`
4. `reset`

**Expected Result:**
- Step 1: `implement-phase.md` 5 lines changed, `knowledge.md` 1.
- Step 2: both `exit 0` with `Findings: 0` (11/11 and 13/13 scenarios).
- Step 3: `spec-dependencies` `exit 1` with two findings (`Implement-phase must topologically order the explicit DAG.`, `Implement-phase must use roadmap order as the independent-spec tie-break.`); `knowledge-consolidate` `exit 1` (`Knowledge --consolidate must state the merge-never-append principle.`).
- Step 4: prints nothing.

**Status:** [ ] Pass  [ ] Fail

**Notes:** Step 3 shows what the old pins enforced. Judge whether their messages describe behavior or wording; Scenario 20 covers that judgment for a wider sample.

---

### Scenario 20: Sampled pin-map rows hold up against the command text

**Source:** Experience Design (Who uses it: a reviewer checks `pin-map.md` row by row) — Story 2; spec.md → Hardest Constraint; DEV-004, DEV-005, DEV-006
**Feature:** none
**Verification:** human — no recipe
**Automated Test:** none — manual only (a person judges each category)

**Preconditions:**
- Scenario 13 done. Clone is clean.

**Steps:**
1. Print the sample: `grep -E '^\| (2|67|110|74|78|151|33|116|130|198) \|' "$PM" | cut -c1-320`
2. Keep rows: `cd "$CL"; grep -n 'planning commands create files and stop' commands/_preamble.md; grep -n 'there is no second regeneration' commands/create-spec.md | cut -c1-80; grep -n 'verbatim private transcript bodies' commands/refresh-command.md | cut -c1-80`
3. Convert rows: `grep -n 'phase-state.py create-lane\|phase-state.py validate-result' commands/implement-phase.md | cut -c1-90; grep -n '^## User Challenge' commands/_preamble.md; grep -n '^#### Step 1.1b: Dirty-Tree Guard' commands/refactor.md; grep -nE '"(User Challenge|Step 1.1b: Dirty-Tree Guard|scripts/phase-state.py (create-lane|validate-result))"' scripts/eval-command-structure.py`
4. Convert and remove literals are off `eval.sh`: `awk -F'\t' '($4=="commands/_preamble.md" && $5=="## User Challenge") || ($4=="commands/implement-phase.md" && $5=="scripts/phase-state.py") || ($4=="commands/knowledge.md" && $5=="merge, never append")' "$W/pins-now.tsv" | wc -l`
5. Remove rows, claims in their reasons:
   ```bash
   grep -c 'grep -v archive' commands/status.md; grep -n 'never recurse into' commands/status.md | cut -c1-100
   grep -n 'merge, never append' scripts/eval.sh | cut -c1-80
   grep -n 'Last audit note:' scripts/eval-git-notes-audit.py
   grep -n 'gate3-route:`, `review-panel:' scripts/tests/test_review_panel.py commands/implement-story.md | cut -c1-120
   ```
6. Read all 34 remove rows with their reasons: `grep -E '^\| [0-9]+ \|.*\| remove \|' "$PM" | cut -c1-400`

**Expected Result:**
- Step 2: each keep literal is present in its command (`_preamble.md`, `create-spec.md` Step 2.6a, `refresh-command.md`).
- Step 3: `implement-phase.md` lines 216 and 220 call `create-lane` and `validate-result`; `_preamble.md:29` is `## User Challenge (Scope-Degradation Escalation)`; `refactor.md:63` is the Step 1.1b heading; the helper holds a row for each value.
- Step 4: `0` (the same filter over `$W/pins-before.tsv` gives `3`).
- Step 5: `0`, then `status.md:265` (single-level glob, never recurse into `archive/`); two `eval.sh` lines pin `merge, never append` on the reducer and the knowledge README; `eval-git-notes-audit.py` asserts `Last audit note:` (scenario `status-audit-pointer-line`); `test_review_panel.py:803` and `implement-story.md:417` both carry the `gate3-route:`, `review-panel:` sentence.
- Step 6: each reason says why no gate, verdict, loop bound, script call, or parsed format depends on the text, or names the scenario or test that still asserts it. Mark Fail and name the row if any remove row reads like a safety contract.

**Status:** [ ] Pass  [ ] Fail

**Notes:**

---

### Scenario 21: Tests that mutated removed pins changed in the same commit, and no keep-row test was deleted

**Source:** Acceptance Criteria — Story 2 (AC-2.5); Error Map (Remove a pin: a test mutates that pin); Business Rule 9 (Tests move with pins)
**Feature:** none
**Verification:** human — no recipe
**Automated Test:** none — manual only (commit history review)

**Preconditions:**
- Setup block pasted. The clone holds full history.

**Steps:**
1. `cd "$CL" && git show --stat --format='%h %s' 6bf0ded c1f7a7f 8ead450 | grep -E '^[0-9a-f]{7} | scripts/'`
2. `git diff 04799a9 882dac4 -- scripts/tests | grep -E '^-\s+def test_'`
3. `git show 6bf0ded -- scripts/tests/test_review_panel.py | grep -A3 '^-    def test_report_entry_pin_bites'`
4. `grep -c 'product-check-direction' scripts/eval.sh; grep -n 'def test_' scripts/tests/test_product_check_direction.py | head`

**Expected Result:**
- Step 1: `6bf0ded` (review-panel pin, pin-map row 198) changes `scripts/eval.sh` and `scripts/tests/test_review_panel.py` together. `c1f7a7f` (delete `check_product_check_direction`, rows 199–207) changes `scripts/eval.sh` and `scripts/tests/test_product_check_direction.py` together. `8ead450` moves the retired pins' mutation cases into pytest as direct text assertions.
- Step 2: three deleted tests: `test_story1_pins_pass_and_each_mutation_bites`, `test_story2_pins_bite_and_issue_is_resolved` (both ran `eval.sh --check=product-check-direction`, whose nine pins are all `remove` rows), and `test_report_entry_pin_bites` (row 198, `remove`).
- Step 3: the deleted test cut `` `review-panel:`, `` from `implement-story.md`, the text of row 198.
- Step 4: `0` (the check and its `CHECKS` entry are gone); `test_product_check_direction.py` still has tests that assert the command text directly.

**Status:** [ ] Pass  [ ] Fail

**Notes:**

---

## Story 3: `create-spec.md` Reduction Pass

### Scenario 22: The cut log accounts for every lean-twin change, with no byte reasons

**Source:** Acceptance Criteria — Story 3 (AC-3.1); DEV-007
**Feature:** none
**Verification:** human — no recipe
**Automated Test:** partial — `test_governor_enforcement.py` (`CreateSpecCutLogTests.test_every_twin_change_is_adopted_coaching_or_declined_with_a_class`) checks classes, numbering, named declines, and byte words; completeness against the twin diff is manual

**Preconditions:**
- Setup block pasted. The clone holds full history.

**Steps:**
1. `CUT="$SPEC/cut-log.md"; awk -F' [|] ' '/^\| [0-9]+ \|/ {print $4}' "$CUT" | sort | uniq -c`
2. `awk -F' [|] ' '/^\| [0-9]+ \|/ {print $3" "$5}' "$CUT" | grep -ciE 'byte|[0-9] ?kb'`
3. `cd "$CL" && git show 617037b:commands/create-spec.lean.md > "$W/lean.md"; git show 37e097e:commands/create-spec.md > "$W/start.md"; diff -u "$W/start.md" "$W/lean.md" | grep -c '^@@'`
4. Open `diff -u "$W/start.md" "$W/lean.md" | less`. For at least five hunks, find the cut-log row (Adopted or Declined) that names the change.

**Expected Result:**
- Step 1: `54 coaching`, `8 behavior`, `4 constraint`, `3 test-pinned`, `3 addition`, `1 wording` (73 rows).
- Step 2: `0`.
- Step 3: `20` twin hunks (several hunks hold more than one logged change).
- Step 4: every sampled twin change has a row. Each Declined row names what the change would have touched; no Adopted row is a constraint or behavior change.

**Status:** [ ] Pass  [ ] Fail

**Notes:**

**Implementation Reference:** Story 3 — `cut-log.md` (54 adopted, 19 declined, hunk map).

---

### Scenario 23: Frontmatter, step numbers, AskQuestion blocks, and script calls are intact

**Source:** Acceptance Criteria — Story 3 (AC-3.3); Business Rule 10 (step numbers stay)
**Feature:** none
**Verification:** human — no recipe
**Automated Test:** `scripts/tests/test_governor_enforcement.py` (`CreateSpecBeforeAfterTests`)

**Preconditions:**
- Setup block pasted. The clone holds full history.

**Steps:**
1. Compare the frontmatter:
   ```bash
   cd "$CL"; fm() { awk 'NR==1&&/^---$/{f=1;print;next} f{print} f&&/^---$/{exit}'; }
   diff <(git show 37e097e:commands/create-spec.md | fm) <(fm < commands/create-spec.md) && echo "frontmatter identical"
   fm < commands/create-spec.md | grep -c '^  - '
   ```
2. `diff <(git show 37e097e:commands/create-spec.md | grep '^#### Step') <(grep '^#### Step' commands/create-spec.md)`
3. `for r in 37e097e HEAD; do git show "${r}:commands/create-spec.md" | grep -c 'AskQuestion({'; done; grep -c 'AskQuestion titled "Jev judgment provider"' commands/create-spec.md`
4. `diff <(git show 37e097e:commands/create-spec.md | grep -oE 'python3 scripts/[a-z-]+\.py [a-z-]+' | sort) <(grep -oE 'python3 scripts/[a-z-]+\.py [a-z-]+' commands/create-spec.md | sort) && echo "calls identical"`

**Expected Result:**
- Step 1: `frontmatter identical`; `3` exit criteria.
- Step 2: only two lines, both deletions: `< #### Step 1.2: Switch to Plan Mode for Discovery` and `< #### Step 2.1: Initialize Tracking`. No heading is renumbered; 1.2 and 2.1 are gaps, and both are logged (cut-log rows 17 and 34).
- Step 3: `3`, `3`, `1` (three AskQuestion code blocks plus the Jev provider prompt).
- Step 4: `calls identical` (seven calls: `ac-trace.py check`, `jev-judge.py setup`, `jev-judge.py spec-findings`, `jev-judge.py status`, `spec-analyze.py check`, `spec-status.py is-complete`, `supersession-writeback.py apply`).

**Status:** [ ] Pass  [ ] Fail

**Notes:**

---

### Scenario 24: Text the cut was told to leave is still in `create-spec.md`

**Source:** Edge Case — Story 3 (technical-spec.md → What the cuts must not touch; cut-log Declined rows 59–73; re-decided rows 18, 21, 38, 50, 51)
**Feature:** none
**Verification:** human — no recipe
**Automated Test:** partial — `test_jev_setup_hooks.sh` and `test_spec_analyze_command_hooks.sh` pin the Jev text; `test_harness_cuts.py` pins Step 2.6a; the rest is manual

**Preconditions:**
- Setup block pasted.

**Steps:**
1. Run:
   ```bash
   cd "$CL"; while IFS= read -r s; do printf '%s\t%s\n' "$(grep -ciF -- "$s" commands/create-spec.md)" "$s"; done <<'EOF'
   any relevant phase/source metadata
   or exploration record
   Never mark Story 1 complete
   Jev setup (once)
   Any `jev-judge.py` or `spec-analyze.py` `fail`
   the one-time Jev setup prompt is the only exception
   Add one note: `jev:
   Iteration accounting: the floor attempt and its anchor re-run count as one attempt — there is no second regeneration
   never an escalation
   Ask clarifying questions when business logic does not align
   integration points and dependencies
   Follow wireframe conventions from
   never blocks or fails spec package creation
   no reverse pointer
   (gitignored)
   Read skills/error-rescue-mapping/SKILL.md
   EOF
   ```

**Expected Result:**
- Every line prints a count of `1` or more. A `0` means the cut removed text it was told to keep.

**Status:** [ ] Pass  [ ] Fail

**Notes:** `5536b31` restored "ask clarifying questions" and "dependencies" after the first cut copied two twin edits (cut-log rows 71, 72).

---

### Scenario 25: Kept pins, structural rows, and the Jev and spec-analyze tests pass on the reduced file

**Source:** Acceptance Criteria — Story 3 (AC-3.2); Error Map (Cut `create-spec.md`: pinned or tested text removed)
**Feature:** none
**Verification:** human — no recipe
**Automated Test:** `scripts/tests/test_governor_enforcement.py` (`CreateSpecBeforeAfterTests.test_keep_pins_and_structural_rows_hold_at_the_end_commit`), `scripts/tests/test_jev_setup_hooks.sh`, `scripts/tests/test_spec_analyze_command_hooks.sh`, and `eval.sh` in CI

**Preconditions:**
- Setup block pasted. Clone is clean.

**Steps:**
1. `cd "$CL" && bash scripts/tests/test_jev_setup_hooks.sh >/dev/null 2>&1; echo "jev $?"; bash scripts/tests/test_spec_analyze_command_hooks.sh >/dev/null 2>&1; echo "spec-analyze $?"`
2. `for c in recommended-spec-implementation spec-dependencies model-escalation command-structure shipped-refs; do echo "== $c"; ev $c; done`
3. Break pin-map row 67 (`loop-bound`, keep): `sed -i '' 's/count as one attempt — there is no second regeneration/count as one attempt; there is no second regeneration/' commands/create-spec.md; ev model-escalation; reset`

**Expected Result:**
- Step 1: `jev 0`, `spec-analyze 0`.
- Step 2: every check `exit 0` with `Findings: 0`. `recommended-spec-implementation` takes longer: it builds install sandboxes.
- Step 3: `exit 1`; `` `commands/create-spec.md`: create-spec.md Step 2.6a must state the pair-counts-once iteration rule verbatim… ``; `reset` prints nothing.

**Status:** [ ] Pass  [ ] Fail

**Notes:**

---

### Scenario 26: The file shrank, the overage is repinned exactly, and an upward repin or unrecorded growth fails

**Source:** Acceptance Criteria — Story 3 (AC-3.4); Error Map (Repin: value not exact; value not lower); Experience Design (State: `create-spec.md` overage repinned upward); DEV-009
**Feature:** none
**Verification:** human — no recipe
**Automated Test:** `scripts/tests/test_governor_enforcement.py` (`CreateSpecRepinTests`, `ComplianceGateTests.test_the_byte_cap_is_the_half_that_does_not_comply_and_is_not_blocking`)

**Preconditions:**
- Setup block pasted. Clone is clean.

**Steps:**
1. `cd "$CL" && git show 37e097e:commands/create-spec.md | wc -c; wc -c < commands/create-spec.md; grep -n '"commands/create-spec.md": ' scripts/tests/test_governor_enforcement.py`
2. `grep -B8 '"commands/create-spec.md": 13602' scripts/tests/test_governor_enforcement.py | grep -A7 'Story 3'`
3. Repin upward: `sed -i '' 's/"commands\/create-spec.md": 13602,/"commands\/create-spec.md": 29304,/' scripts/tests/test_governor_enforcement.py; uv run --python 3.9 pytest -q scripts/tests/test_governor_enforcement.py 2>&1 | grep -E 'FAILED|passed|failed'; reset`
4. Grow the file without a repin: `printf '\nTip: ask the user friendly questions.\n' >> commands/create-spec.md; uv run --python 3.9 pytest -q scripts/tests/test_governor_enforcement.py 2>&1 | grep -E 'FAILED|passed|failed'; reset`

**Expected Result:**
- Step 1: `53612` at Story 3 start, `38562` now; `"commands/create-spec.md": 13602,` (38,562 − 24,960 = 13,602, below 28,652 and 29,304).
- Step 2: the dated comment `2026-10-21 (2026-10-20-shipped-command-hygiene Story 3): 28652 -> 13602` names the coaching cut (topic questions, pushback phrasing, Plan Mode rationale, duplicated framing, history and labels, Phase 2 rationale, Example Usage) and says "Each cut removed coaching, not a byte goal".
- Step 3: `2 failed, 56 passed`: `CreateSpecRepinTests::test_recorded_overage_is_below_start_and_ceiling` and the exact-sum `ComplianceGateTests` test.
- Step 4: at least one failure; the exact-sum assertion reports `57164 != 57125` and the repin test `13602 != 13641`.
- Each `reset` prints nothing.

**Status:** [ ] Pass  [ ] Fail

**Notes:**

---

### Scenario 27: Every hunk of the reduction maps to an adopted coaching row

**Source:** Acceptance Criteria — Story 3 (AC-3.5); Experience Design (Interaction patterns: `cut-log.md` read beside `git diff`)
**Feature:** none
**Verification:** human — no recipe
**Automated Test:** partial — `CreateSpecCutLogTests.test_hunk_map_is_the_story_diff` and `test_every_hunk_maps_to_adopted_rows_only` check hunk ranges and row numbers; whether each hunk removes only coaching is a reading task

**Preconditions:**
- Setup block pasted. The clone holds full history.

**Steps:**
1. `cd "$CL" && git log --oneline 5536b31..HEAD -- commands/create-spec.md | wc -l`
2. `diff <(git diff 37e097e 5536b31 -- commands/create-spec.md | grep '^@@' | sed -E 's/^@@ (-[0-9]+,[0-9]+) .*/\1/') <(grep -E '^\| -[0-9]' "$SPEC/cut-log.md" | awk -F'|' '{gsub(/ /,"",$2); print $2}') && echo "hunk map matches"`
3. Open `git diff 37e097e 5536b31 -- commands/create-spec.md` beside `cut-log.md` → Hunk map. Read at least the four largest hunks (`-291,129`, `-692,114`, `-870,85`, `-192,45`) against their rows.

**Expected Result:**
- Step 1: `0` (no later commit touched the file).
- Step 2: `hunk map matches` (22 hunks).
- Step 3: each removed passage is coaching (sample questions, example phrasing, rationale, history labels, the Example Usage dialogue, duplicated framing). No step, gate, rule, AskQuestion block, or script call is removed without a surviving equivalent.

**Status:** [ ] Pass  [ ] Fail

**Notes:**

---

### Scenario 28: Full eval, pytest, and bash tests are green

**Source:** Acceptance Criteria — Story 3 (AC-3.5); also Story 1 task 1.7, Story 2 AC-2.5, and spec.md → Success criteria
**Feature:** none
**Verification:** human — no recipe
**Automated Test:** CI runs all three on each PR

**Preconditions:**
- Setup block pasted. Clone is clean. Outside any sandbox. Full eval takes about two minutes.

**Steps:**
1. `(cd "$CL" && bash scripts/eval.sh --report="$W/full.md" >/dev/null 2>&1); echo "exit $?"; tail -3 "$W/full.md"; grep -o 'commands/create-spec.md +[0-9]*' "$W/full.md" | head -1`
2. `(cd "$CL" && uv run --python 3.9 pytest -q 2>&1 | tail -1)`
3. `(cd "$CL" && n=0 f=0; for t in scripts/tests/test_*.sh; do n=$((n+1)); bash "$t" >/dev/null 2>&1 || { f=$((f+1)); echo "FAIL $t"; }; done; echo "bash tests: $n run, $f failed")`

**Expected Result:**
- Step 1: `exit 0`; `Findings: 0`, `Run errors: 0`; `commands/create-spec.md +13602`.
- Step 2: `2774 passed, 2 skipped` on `ef65139` (the count grows with later commits; there must be no failure).
- Step 3: `bash tests: 45 run, 0 failed`.

**Status:** [ ] Pass  [ ] Fail

**Notes:**

---

### Scenario 29: A `/create-spec` session with the reduced command still produces a valid spec package (human step)

**Source:** Experience Design — Story 3 (the developer who runs `/create-spec`); spec.md → Scope out (no behavior change to any command)
**Feature:** none
**Verification:** human — no recipe
**Automated Test:** none — manual only. A person drives an interactive agent session; no test runs `/create-spec`.

**Preconditions:**
- Scenario 12 done: `$P` is a scratch project with Writ installed for Claude Code from the clone.
- Claude Code is installed. Use a model and thinking level of at least the command's `entry_level: high`.
- Seed the project:
  ```bash
  printf '# Notes CLI\n\nA shell script that appends notes to notes.txt.\n' > "$P/README.md"
  printf '#!/bin/sh\necho "$*" >> notes.txt\n' > "$P/note.sh"
  git -C "$P" add -A && git -C "$P" -c user.name=t -c user.email=t@example.invalid commit -qm init
  ```

**Steps:**
1. `cd "$P" && claude`
2. Type: `/create-spec add a --list flag to note.sh that prints saved notes with line numbers`
3. Answer the discovery questions. Before approving a contract, run `git -C "$P" status --short` in a second shell.
4. When the contract appears, choose **Lock contract and create spec package** in the Contract Decision prompt.
5. If a Visual References prompt appears, skip it. If the "Jev judgment provider" prompt appears, choose **Not now**.
6. When the final package review appears, exit the session and run:
   ```bash
   S=$(ls -d "$P"/.writ/specs/*/ | head -1); ls -R "$S"
   grep -nE '^> \*\*(Status|Dependencies):\*\*' "$S/spec.md"
   for f in "$S"/user-stories/story-*.md; do echo "$(basename "$f"): AC $(grep -c '^- \[ \] Given' "$f"), tasks $(grep -cE '^- \[ \] [0-9]+\.[0-9]+' "$f")"; done
   wc -l < "$S/spec-lite.md"
   (cd "$P" && python3 scripts/ac-trace.py check --spec "${S%/}" --repo "${S%/}"; echo "ac-trace exit $?")
   ```

**Expected Result:**
- Step 3: discovery asks one question per prompt when the answers depend on each other (independent bounded choices may share a prompt) and pushes back where the request is unclear or conflicts with the code. `git status` shows no new file under `.writ/specs/` before the contract is locked.
- Step 4: the full contract is printed as a visible message before the Contract Decision prompt, in Plan Mode or not, and shows Deliverable, Must Include, Hardest Constraint, Experience Design, Business Rules, Success Criteria, and Scope Boundaries. The prompt offers four options (lock, edit or ask more questions, risks, blueprint), plus the free-text "Other" that Claude Code adds.
- Step 6:
  - The package holds `spec.md`, `spec-lite.md`, `user-stories/README.md`, one or more `user-stories/story-N-*.md`, and `sub-specs/technical-spec.md`.
  - `spec.md` has a `Status` line and a `Dependencies` line (`[]` here).
  - Every story has 3–5 acceptance criteria and 5–7 tasks.
  - `spec-lite.md` is under 100 lines.
  - `ac-trace` reports no finding that blocks (exit 0).
  - The final review lists the file tree, story and task counts, the `spec-analyze.py` verdict as a note, and one `jev:` note.
- The session never offers to implement the spec (Terminal constraint).

**Status:** [ ] Pass  [ ] Fail

**Notes:** Optional comparison: install from `37e097e` (`git -C "$CL" worktree add "$W/pre" 37e097e`, then install from `$W/pre` into a second scratch project) and run the same request. The two packages should have the same structure; wording will differ run to run.

---

## Automated vs. Manual

| Kind | Scenarios | Count |
|---|---|---|
| Asserted by a committed test (CI runs it) | 1, 2, 3, 5, 7, 11, 15, 17, 18, 23, 25, 26, 28 | 13 |
| Partly automated (a test covers part; the rest is a recipe run, a mutation, or reading by hand) | 4, 6, 8, 10, 12, 13, 22, 24, 27 | 9 |
| Manual only | 9, 14, 16, 19, 20, 21, 29 | 7 |

Scenario 29 is the only one that needs an interactive agent session. Scenarios 9, 20, 22, and 27 need a person to judge text; the rest are scripted and give fixed output.

## Not Covered by This Plan

- **Bare ADR labels stay.** 23 lines in 10 commands name a Writ ADR without a link (`(ADR-013)` in `_preamble.md`, `Design principle (ADR-001)`). Out of scope; left for the later pass.
- **Other shipped surfaces are not scanned.** `agents/`, `adapters/`, `skills/`, and `.writ/docs/` can still link Writ's own history (Scenario 11).
- **Removed retired-text forbids leave nothing guarding that text.** Rows 33–35 (`grep -v archive`), 60–61 (retired story-context prose), and 104–105 (`ralph` in two commands) are no longer checked anywhere. Rows 201–204 and 207 are still asserted by `test_product_check_direction.py`. This is allowed by the categories rule; a reviewer should know it.
- **Weak single-word safety pins were kept as they are** (`AskQuestion`, `read-only`). Strengthening them is not in this spec.
- **Never pinned, per the Story 2 reviewer:** `verify-spec.md`'s 4a–4c report-only / 4d blocking boundary and `implement-phase.md`'s `scripts/spec-deps.py validate` call.
- **Intermediate commit `6434d9c`** carries a lean-file skip that `ccfa77c` removes, so that one commit fails the harness-cuts guard. History only; the branch tip passes.
- **`frontmatter` kind has no table row.** It is tested only synthetically (Scenario 17 Notes).

## Pending Stories

None. All three stories are Completed ✅.
