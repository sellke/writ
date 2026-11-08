# UAT Plan: CI and Update Integrity

> **Generated:** 2026-10-20
> **Spec:** `.writ/specs/2026-10-20-ci-and-update-integrity/`
> **Stories Covered:** 5 of 5 completed
> **Total Scenarios:** 43
> **Verification recipe:** does not apply. Writ has no running app, so no `.writ/docs/app-verification.md` was drafted, saved, or bound. Every scenario is `human — no recipe`. The `**Automated Test:**` line on each scenario names the committed test that already asserts the same behavior, if any.

## How to Use This Plan

1. Work through scenarios in order (they're grouped by story, ordered by priority)
2. For each scenario, follow the steps exactly as written
3. Mark Pass or Fail — add notes for any unexpected behavior
4. Scenarios marked Fail should be filed as issues or fed back to the spec
5. A feature passes UAT when all scenarios pass (or failures are accepted as known limitations)

**Conventions for this plan:**

- **Never run `install.sh` or `update.sh` in the Writ repo.** It is symlinked into `.claude/` and `.cursor/`. Every scenario below installs into a temp folder under `$W`. (`update.sh` also refuses to run in the source repo.)
- Run the plan in `bash`, outside any sandbox (the steps run `git init` and `git commit` in temp folders).
- Paste this setup block once per shell. Story sections add their own setup blocks on top of it.

  ```bash
  REPO=/Users/asellke/Projects/writ          # the Writ checkout; read from, never installed into
  W=$(mktemp -d "${TMPDIR:-/tmp}/writ-uat.XXXXXX")
  cd "$W"   # run every helper from the temp folder: an empty path then fails instead of writing to the Writ repo
  h()  { shasum -a 256 "$1" | cut -d' ' -f1; }
  gc() { case "$SRC" in "$W"/?*) ;; *) echo "gc: SRC='$SRC' is not under $W; refusing" >&2; return 1;; esac
         git -C "$SRC" -c user.name=t -c user.email=t@example.invalid add -A &&
         git -C "$SRC" -c user.name=t -c user.email=t@example.invalid commit -q -m "$1"; }
  # A committed copy of the working tree at $W/src-<name>. Sets SRC.
  new_src() {
    SRC="$W/src-$1"; mkdir -p "$SRC"
    (cd "$REPO" && tar --exclude=.git --exclude=.cursor --exclude=.claude --exclude=.codex \
       --exclude=.writ --exclude='.writ-lanes-*' --exclude=__pycache__ --exclude=.venv \
       --exclude=.pytest_cache -cf - .) | (cd "$SRC" && tar -xf -)
    mkdir -p "$SRC/.writ/docs" && cp "$REPO"/.writ/docs/*.md "$SRC/.writ/docs/"
    git -C "$SRC" init -q -b main && gc "source"
  }
  # inst <project> <claude|cursor|codex> [flags]; upd <project> <platform> [flags]
  inst() { local p="$1" pf="$2"; shift 2; mkdir -p "$p" && (cd "$p" && bash "$SRC/scripts/install.sh" --platform "$pf" --no-commit "$@"); }
  upd()  { local p="$1" pf="$2"; shift 2; (cd "$p" && WRIT_REPO="${UPSTREAM:-$SRC}" bash "$SRC/scripts/update.sh" --platform "$pf" --no-commit "$@"); }
  # An unrelated upstream change, so the next update has work to do and rewrites the manifest.
  bump() { printf '\n<!-- uat bump %s -->\n' "$RANDOM$RANDOM" >> "$SRC/commands/create-issue.md" && gc "bump"; }
  # Did the last update rewrite this manifest? (Its "# version:" must name the source HEAD.)
  rewritten() { local v; v=$(sed -n 's/^# version: //p' "$1")
    [ -n "$v" ] && [ "$(git -C "$SRC" rev-parse -q --verify "$v^{commit}" 2>/dev/null)" = "$(git -C "$SRC" rev-parse HEAD)" ] \
      && echo "manifest rewritten" || echo "manifest NOT rewritten"; }
  ```

- **Why `bump` matters.** When nothing is left to apply, `update.sh` prints "Already up to date" and exits before it rewrites the manifest. A manifest check after such a run proves nothing. Scenarios that check the manifest call `bump` first and then `rewritten`.
- Manifests: Claude Code `.claude/.writ-manifest`, Cursor `.cursor/.writ-manifest`, Codex `.codex/.writ-manifest`. Each line is `<sha256>  <path>`.
- Expected output was observed on 2026-10-20 against `c74eb22` when this plan was generated. Hashes, versions, and temp paths will differ.
- When done: `rm -rf "$W"`.
- **Automated Test line:** names the test in `scripts/tests/` that asserts the behavior, `partial` when a test covers part of it, or `none — manual only`. CI runs every test named here on each PR (Story 1).

## Coverage Summary

| Story | Status | Scenarios | Source Breakdown |
|-------|--------|-----------|-----------------|
| Story 1: CI Runs Every Suite | ✅ Covered | 8 | AC: 5, Errors: 1, Shadow: 1, Edge: 0, Experience: 1 |
| Story 2: Keep the Codex Config Baseline on Update | ✅ Covered | 4 | AC: 4, Errors: 0, Shadow: 0, Edge: 0 |
| Story 3: Baselines Only for Shipped Paths; Customized Files Keep Their Baseline | ✅ Covered | 10 | AC: 7, Errors: 0, Shadow: 1, Edge: 2 |
| Story 4: Keep Modified Stale Files in Every Category | ✅ Covered | 9 | AC: 5, Errors: 1, Shadow: 0, Edge: 3 |
| Story 5: Repair Legacy Manifests and Remove Stale Files From Their Real Path | ✅ Covered | 12 | AC: 8, Errors: 2, Shadow: 1, Edge: 0, Experience: 1 |

Error-map, shadow-path, and state-catalog items that an AC scenario already exercises are folded into that scenario and named on its **Source** line, not counted twice.

**Automated vs. manual:** 25 scenarios are asserted by a committed test, 6 partly, 12 are manual only. See the table at the end.

---

## Story 1: CI Runs Every Suite

### Scenario 1: The workflow keeps its old steps and adds uv and pytest on Python 3.9

**Source:** Acceptance Criteria — Story 1 (AC-1.1)
**Feature:** none
**Verification:** human — no recipe
**Automated Test:** `scripts/tests/test_ci_workflow.py` (trigger, kept steps, setup-uv pin and order, pytest step)

**Preconditions:**
- None

**Steps:**
1. Open `.github/workflows/eval.yml`.
2. Check the `on:` block and the steps of the `eval` job.
3. Run `cd "$REPO" && uv run --python 3.9 pytest scripts/tests/test_ci_workflow.py`

**Expected Result:**
- `on:` lists `pull_request:` and `push:`.
- These steps are still present: `actions/checkout@v4` with `fetch-depth: 0`, `bash scripts/gen-skill.sh --check`, `bash scripts/eval.sh --report=eval-report.md`, and the upload step with `if: failure()`.
- New steps: `uses: astral-sh/setup-uv@v7` (a major tag), then a step running `uv run --python 3.9 pytest`, then a bash-tests step. All three carry `if: ${{ !cancelled() }}`.
- The pytest run reports `9 passed`.

**Status:** [x] Pass  [ ] Fail

**Notes:** agent-run 2026-10-21 @ b850e66: `on:` has `pull_request:` and `push:`; checkout@v4 (fetch-depth 0), `gen-skill.sh --check`, `eval.sh --report=eval-report.md`, upload `if: failure()` all present; setup-uv@v7, then `uv run --python 3.9 pytest`, then Run bash tests, each `if: ${{ !cancelled() }}`. pytest: `11 passed in 0.08s` (9 at plan time; tests added since c74eb22, intent holds).

**Implementation Reference:** Story 1 — `.github/workflows/eval.yml`; `scripts/tests/test_ci_workflow.py`. `@v7` is the newest bare major tag; v8+ publish only full version tags.

---

### Scenario 2: The bash-tests step runs every test and fails when any is red

**Source:** Acceptance Criteria — Story 1 (AC-1.2); Error Map (CI bash step: a test fails); Experience Design (State: PR, several bash tests red)
**Feature:** none
**Verification:** human — no recipe
**Automated Test:** `scripts/tests/test_ci_workflow.py` (`test_bash_block_fails_on_red_and_runs_every_test`, `test_bash_block_reports_each_failure`)

**Preconditions:**
- Setup block pasted.

**Steps:**
1. Extract the step's `run:` block:
   `awk '/name: Run bash tests/{f=1} f && /run: \|/{r=1; next} r && /^          /{sub(/^          /, ""); print; next} r{exit}' "$REPO/.github/workflows/eval.yml" > "$W/block.sh" && cat "$W/block.sh"`
2. Build a fixture with one passing and two failing tests:
   `mkdir -p "$W/ci-red/scripts/tests" && printf 'exit 0\n' > "$W/ci-red/scripts/tests/test_pass.sh" && printf 'exit 1\n' > "$W/ci-red/scripts/tests/test_fail.sh" && printf 'exit 1\n' > "$W/ci-red/scripts/tests/test_fail2.sh"`
3. Run it the way Actions does on Linux: `(cd "$W/ci-red" && bash -e "$W/block.sh"; echo "exit $?")`

**Expected Result:**
- Step 1 prints a loop over `scripts/tests/test_*.sh` that counts failures and ends with `[ "$fails" -eq 0 ]`.
- Step 3 prints:
  ```
  == scripts/tests/test_fail.sh
  FAIL scripts/tests/test_fail.sh
  == scripts/tests/test_fail2.sh
  FAIL scripts/tests/test_fail2.sh
  == scripts/tests/test_pass.sh
  bash tests failed: 2
  exit 1
  ```
- All three tests ran; the first failure did not stop the loop.

**Status:** [x] Pass  [ ] Fail

**Notes:** agent-run 2026-10-21 @ b850e66: block is the counting loop ending `[ "$fails" -eq 0 ]`; step 3 printed the expected 7 lines exactly, ending `bash tests failed: 2` / `exit 1`.

**Implementation Reference:** Story 1 — `.github/workflows/eval.yml` (Run bash tests). The loop in `CLAUDE.md` (`|| echo "FAIL $t"`) exits 0 on failure; this step does not.

---

### Scenario 3: The bash-tests step passes when every test is green

**Source:** Acceptance Criteria — Story 1 (AC-1.2)
**Feature:** none
**Verification:** human — no recipe
**Automated Test:** `scripts/tests/test_ci_workflow.py` (`test_bash_block_passes_on_green`)

**Preconditions:**
- `$W/block.sh` from Scenario 2, step 1.

**Steps:**
1. `mkdir -p "$W/ci-green/scripts/tests" && printf 'exit 0\n' > "$W/ci-green/scripts/tests/test_pass.sh"`
2. `(cd "$W/ci-green" && bash -e "$W/block.sh"; echo "exit $?")`

**Expected Result:**
```
== scripts/tests/test_pass.sh
bash tests failed: 0
exit 0
```

**Status:** [x] Pass  [ ] Fail

**Notes:** agent-run 2026-10-21 @ b850e66: `== scripts/tests/test_pass.sh`, `bash tests failed: 0`, `exit 0`.

---

### Scenario 4: An empty test folder runs zero tests and exits 0

**Source:** Shadow Path (CI run — nil input: no `test_*.sh`) — Story 1; drift DEV-001
**Feature:** none
**Verification:** human — no recipe
**Automated Test:** `scripts/tests/test_ci_workflow.py` (`test_bash_block_with_no_tests_exits_zero`)

**Preconditions:**
- `$W/block.sh` from Scenario 2, step 1.

**Steps:**
1. `mkdir -p "$W/ci-empty/scripts/tests"`
2. `(cd "$W/ci-empty" && bash -e "$W/block.sh"; echo "exit $?")`

**Expected Result:**
```
bash tests failed: 0
exit 0
```
- No `FAIL scripts/tests/test_*.sh` line (the literal glob is skipped).

**Status:** [x] Pass  [ ] Fail

**Notes:** If the test folder ever moves, CI would pass with zero tests; only the `bash tests failed: 0` line with no `==` lines shows it.

agent-run 2026-10-21 @ b850e66: `bash tests failed: 0`, `exit 0`; no `==` or `FAIL` line.

---

### Scenario 5: The Linux runner choice is backed by recorded evidence

**Source:** Acceptance Criteria — Story 1 (AC-1.3); Error Map (CI runner: a test needs BSD userland)
**Feature:** none
**Verification:** human — no recipe
**Automated Test:** none — manual only

**Preconditions:**
- None

**Steps:**
1. Read the comment above `runs-on:` in `.github/workflows/eval.yml`.
2. Re-run the scan for BSD-only calls:
   `cd "$REPO" && grep -nE "stat -f|date -r|sed -i ''|sed -i \"\"|readlink -f|grep -P|(^|[^a-z_])md5( |$)|gdate|gsed|pbcopy|sw_vers|xcrun|mktemp -t" scripts/tests/*.sh scripts/*.sh; echo "grep exit $?"`
3. Read Story 1's What Was Built → Test Results (BSD scan and Linux run).

**Expected Result:**
- `runs-on: ubuntu-latest`, with a comment naming the grep, the patterns, and the `ubuntu:24.04` container run (35 tests, 0 failures).
- Step 2 prints no matches and `grep exit 1`.
- No `macos-latest` job exists.

**Status:** [x] Pass  [ ] Fail

**Notes:** Scenario 7 is the real Linux check.

agent-run 2026-10-21 @ b850e66: `runs-on: ubuntu-latest`; comment names the grep, its patterns, and the ubuntu:24.04 run (35 tests, 0 failures). Scan printed no matches and `grep exit 1`. eval.yml is the only workflow; no `macos`. Story 1 Test Results record both.

---

### Scenario 6: All three suites pass locally

**Source:** Acceptance Criteria — Story 1 (AC-1.4)
**Feature:** none
**Verification:** human — no recipe
**Automated Test:** none — manual only (this scenario runs the suites; CI repeats it in Scenario 7)

**Preconditions:**
- `uv` installed. Outside any sandbox. About 6 minutes for all three.

**Steps:**
1. `cd "$REPO" && uv run --python 3.9 pytest`
2. `fails=0; for t in scripts/tests/test_*.sh; do bash "$t" || { echo "FAIL $t"; fails=$((fails+1)); }; done; echo "bash tests failed: $fails"`
3. `bash scripts/eval.sh; echo "exit $?"`

**Expected Result:**
- pytest ends with `passed` and no `failed` (2623 passed, 2 skipped at Story 5; the count may be higher now).
- Step 2 prints no `FAIL` line and `bash tests failed: 0` (40 test files at plan time).
- `eval.sh` reports `Findings: 0`, `Run errors: 0`, and `exit 0`.

**Status:** [x] Pass  [ ] Fail

**Notes:** agent-run 2026-10-21 @ b850e66: pytest `2774 passed, 2 skipped in 207.35s` (higher than 2623, as expected); bash loop no `FAIL`, `bash tests failed: 0` over 45 files (40 at plan time); eval.sh `Findings: 0`, `Run errors: 0`, `exit 0`.

---

### Scenario 7: The first CI run on the phase PR shows each suite as its own green step

**Source:** Error Map (CI pytest step: uv cannot provide 3.9) — Story 1; Shadow Path (CI run — upstream error: uv install fails); Experience Design (State: PR, all suites green). Story 1 Definition of Done item still open.
**Feature:** none
**Verification:** human — no recipe
**Automated Test:** none — manual only (needs GitHub Actions)

**Preconditions:**
- The Phase 13 branch is pushed and its PR is open. Not yet done when this plan was written.

**Steps:**
1. Open the PR's **Checks** tab and the `Eval Tier 1` → `eval` job.
2. Open the `Run pytest (Python 3.9 floor)` step log.
3. Open the `Run bash tests` step log and scroll to the end.

**Expected Result:**
- The job is green. Separate steps are listed for the SKILL.md check, Eval Tier 1, setup-uv, pytest, and bash tests.
- The pytest log shows uv fetching or using CPython 3.9.x and ends with `passed`, no `failed`.
- The bash log has one `== scripts/tests/<name>.sh` line per test and ends with `bash tests failed: 0`.

**Status:** [x] Pass  [ ] Fail

**Notes:** If the pytest step is red because uv cannot provide 3.9 on the x86_64 runner, mark Fail and file an issue. The spec allows a switch to `actions/setup-python` only with that failure as evidence.
orchestrator-run 2026-10-21 via `gh run view 39678517441` (PR #60, pull_request, b3ebd3d): job `eval` success; steps listed separately (SKILL.md check, Eval Tier 1, setup-uv@v7, pytest, bash tests, all success); `Using CPython 3.9.25`; `2774 passed, 2 skipped`; 45 `== scripts/tests/` lines; `bash tests failed: 0`. Push run 39678515273 also success.

needs live session (GitHub Actions): open the PR's Checks → `Eval Tier 1` → `eval` and read the pytest and bash-tests step logs. Pointer only: `gh pr checks 60` (2026-10-21) lists two `eval` runs, both `pass`; step logs not read by the agent.

---

### Scenario 8: A red suite turns the job red, names the failing test, and later suites still run

**Source:** Experience Design (State: PR, one suite red) — Story 1
**Feature:** none
**Verification:** human — no recipe
**Automated Test:** none — manual only (needs GitHub Actions; Scenario 2 checks the same block locally)

**Preconditions:**
- Optional. Pushes a throwaway branch to `origin`, which triggers the workflow through its `push:` trigger. Skip if you don't want a red run on the remote.

**Steps:**
1. In a scratch clone of the Writ repo (not the main checkout): `git switch -c uat/red-suite`
2. Add one failing pytest test and one failing bash test:
   `printf 'def test_uat_red():\n    assert False, "deliberate failure"\n' > scripts/tests/test_uat_red.py`
   `printf '#!/usr/bin/env bash\necho deliberate failure; exit 1\n' > scripts/tests/test_uat_red.sh`
   `git add scripts/tests/test_uat_red.* && git commit -m "uat: deliberate red tests"`
3. `git push -u origin uat/red-suite`, then open the run under **Actions**.
4. When done: `git push origin --delete uat/red-suite`.

**Expected Result:**
- The `eval` job is red.
- The pytest step is red, and its summary names `scripts/tests/test_uat_red.py::test_uat_red`.
- The bash-tests step still ran after the red pytest step (it is not skipped). It is red, its log has `FAIL scripts/tests/test_uat_red.sh` and `bash tests failed: 1`, and every other test file still has its `==` line.

**Status:** [x] Pass  [ ] Fail

**Notes:** The unchanged upload step also fires on this failure; `eval-report.md` will be uploaded even though `eval.sh` passed (known, Minor).

needs live session (GitHub Actions): requires pushing a throwaway `uat/red-suite` branch to origin; the agent does not push. Not run.
- orchestrator-run 2026-10-22 (maintainer approved the push): branch uat/red-suite (0b6e8e8), run 39795856168 conclusion failure; pytest step failure with 'FAILED scripts/tests/test_uat_red.py::test_uat_red' and '1 failed, 2774 passed, 2 skipped'; bash step still ran and failed with 'FAIL scripts/tests/test_uat_red.sh' and 'bash tests failed: 1'; 46 '== scripts/tests/' lines. Branch deleted afterwards.

---

## Story 2: Keep the Codex Config Baseline on Update

**Story setup** (on top of the main setup block):

```bash
new_src codex
PX="$W/codex"; inst "$PX" codex > "$W/codex-install.txt" 2>&1; echo "install exit $?"
MX="$PX/.codex/.writ-manifest"
CB=$(grep '  .codex/config.toml.baseline$' "$MX"); echo "$CB"
printf '\n# my edit\n' >> "$PX/.codex/config.toml"; CFG=$(h "$PX/.codex/config.toml")
```

### Scenario 9: The Codex config baseline line survives a manifest-rewriting update

**Source:** Acceptance Criteria — Story 2 (AC-2.1); Error Map (Rewrite manifest: Codex baseline read after truncation); Experience Design (State: Codex update)
**Feature:** none
**Verification:** human — no recipe
**Automated Test:** `scripts/tests/test_update_codex_config_baseline.sh` (AC-2.1 block)

**Preconditions:**
- Story 2 setup run. `install exit 0`, and `$CB` printed one `<hash>  .codex/config.toml.baseline` line.

**Steps:**
1. `bump; upd "$PX" codex > "$W/x1.txt" 2>&1; echo "exit $?"; rewritten "$MX"`
2. `grep -c '  .codex/config.toml.baseline$' "$MX"; [ "$(grep '  .codex/config.toml.baseline$' "$MX")" = "$CB" ] && echo "same line"`
3. `[ "$(h "$PX/.codex/config.toml")" = "$CFG" ] && echo "config unchanged"`

**Expected Result:**
- `exit 0` and `manifest rewritten`.
- `1` and `same line`.
- `config unchanged` (the edited `.codex/config.toml` is untouched).

**Status:** [x] Pass  [ ] Fail

**Notes:** Before the fix, this run left 0 baseline lines.

agent-run 2026-10-21 @ b850e66: `exit 0`, `manifest rewritten`; `1`, `same line`; `config unchanged`.

**Implementation Reference:** Story 2 — `scripts/update.sh` (`write_copy_manifest` reads the line before truncating; Story 3 moved all lookups to a per-run baseline file).

---

### Scenario 10: A second update and a dry run keep the line; the dry run writes nothing

**Source:** Acceptance Criteria — Story 2 (AC-2.2)
**Feature:** none
**Verification:** human — no recipe
**Automated Test:** `scripts/tests/test_update_codex_config_baseline.sh` (AC-2.2 block)

**Preconditions:**
- Project after Scenario 9.

**Steps:**
1. `bump; upd "$PX" codex > /dev/null 2>&1; echo "exit $?"; rewritten "$MX"; [ "$(grep '  .codex/config.toml.baseline$' "$MX")" = "$CB" ] && echo "same line"`
2. `cp "$MX" "$W/mx.before"; bump; upd "$PX" codex --dry-run > "$W/xdry.txt" 2>&1; echo "exit $?"`
3. `cmp "$MX" "$W/mx.before" && echo "manifest byte-identical"; tail -3 "$W/xdry.txt"`

**Expected Result:**
- Step 1: `exit 0`, `manifest rewritten`, `same line`.
- Step 2: `exit 0`.
- Step 3: `manifest byte-identical`, and the output ends with `🏃 DRY RUN — No changes applied.`

**Status:** [x] Pass  [ ] Fail

**Notes:** agent-run 2026-10-21 @ b850e66: step 1 `exit 0`, `manifest rewritten`, `same line`; step 2 `exit 0`; step 3 `manifest byte-identical`, output ends `🏃 DRY RUN — No changes applied.`

---

### Scenario 11: With no baseline line, update exits 0 and writes none

**Source:** Acceptance Criteria — Story 2 (AC-2.3); Error Map (Rewrite manifest: no prior Codex baseline); Shadow Path (Codex baseline — nil input); Experience Design (State: Codex manifest with no baseline line)
**Feature:** none
**Verification:** human — no recipe
**Automated Test:** `scripts/tests/test_update_codex_config_baseline.sh` (AC-2.3 block)

**Preconditions:**
- Project after Scenario 10.

**Steps:**
1. `awk '$2 != ".codex/config.toml.baseline"' "$MX" > "$W/mx.tmp" && cat "$W/mx.tmp" > "$MX"; grep -c '  .codex/config.toml.baseline$' "$MX"`
2. `bump; upd "$PX" codex > /dev/null 2>&1; echo "exit $?"; rewritten "$MX"`
3. `grep -c '  .codex/config.toml.baseline$' "$MX"`

**Expected Result:**
- Step 1 prints `0`.
- Step 2: `exit 0`, `manifest rewritten`.
- Step 3 prints `0`. No empty-hash line was invented.

**Status:** [x] Pass  [ ] Fail

**Notes:** agent-run 2026-10-21 @ b850e66: `0`; `exit 0`, `manifest rewritten`; `0`; no malformed (non-64-hex) line in the manifest.

---

### Scenario 12: The Codex test fails on the pre-fix script and passes now; the issue is resolved

**Source:** Acceptance Criteria — Story 2 (AC-2.4)
**Feature:** none
**Verification:** human — no recipe
**Automated Test:** partial — CI runs the test and checks it passes; the pre-fix failure (step 2) is checked only by hand

**Preconditions:**
- Setup block pasted. Outside any sandbox.

**Steps:**
1. `bash "$REPO/scripts/tests/test_update_codex_config_baseline.sh"; echo "exit $?"`
2. `X="$W/prefix-2"; mkdir -p "$X" && git -C "$REPO" archive 953f47e | tar -x -C "$X" && cp "$REPO/scripts/tests/test_update_codex_config_baseline.sh" "$X/scripts/tests/" && bash "$X/scripts/tests/test_update_codex_config_baseline.sh"; echo "exit $?"`
3. Open `.writ/issues/bugs/2026-10-12-codex-config-baseline-dropped-on-update.md` and read the end.

**Expected Result:**
- Step 1: `PASS test_update_codex_config_baseline`, `exit 0`.
- Step 2 (observed): `FAIL: first update: .codex/config.toml.baseline line count is 0, want 1`, `exit 1`.
- Step 3: the file ends with a `## Resolution` section naming the read-before-truncate change and `scripts/tests/test_update_codex_config_baseline.sh`.

**Status:** [x] Pass  [ ] Fail

**Notes:** `953f47e` is the commit before this spec's code changes.

agent-run 2026-10-21 @ b850e66: step 1 `PASS test_update_codex_config_baseline`, exit 0; step 2 `FAIL: first update: .codex/config.toml.baseline line count is 0, want 1`, exit 1; issue ends with `## Resolution` naming the read-before-truncate change and the test.

---

## Story 3: Record Baselines Only for Shipped Paths; Customized Files Keep Their Baseline

**Story setup** (on top of the main setup block):

```bash
new_src s3
P3="$W/claude-user"; M3="$P3/.claude/.writ-manifest"
mkdir -p "$P3/.writ/docs" "$P3/scripts" "$P3/.claude/commands"
echo "# our stack"      > "$P3/.writ/docs/tech-stack.md"
printf '#!/bin/sh\necho deploy\n' > "$P3/scripts/deploy.sh"
echo "# my own command" > "$P3/.claude/commands/my-own.md"
echo "# my review"      > "$P3/.claude/commands/review.md"     # same name as a shipped command
U3=".writ/docs/tech-stack.md scripts/deploy.sh .claude/commands/my-own.md .claude/commands/review.md"
(cd "$P3" && for f in $U3; do h "$f"; done) > "$W/u3.before"
```

### Scenario 13: Install leaves pre-existing user files alone and writes the header

**Source:** Acceptance Criteria — Story 3 (AC-3.1); Error Map (Rewrite manifest: user-authored file recorded; Install over a user file at a shipped path); Shadow Path (User-authored file — nil input: no manifest); Experience Design (States: install into a project with user files; install over a user file at a shipped path)
**Feature:** none
**Verification:** human — no recipe
**Automated Test:** `scripts/tests/test_manifest_shipped_baselines.sh` (AC-3.1 install)

**Preconditions:**
- Story 3 setup run. No Writ install in `$P3` yet.

**Steps:**
1. `inst "$P3" claude > "$W/inst3.txt" 2>&1; echo "exit $?"; grep 'file(s) preserved' "$W/inst3.txt"`
2. `(cd "$P3" && for f in $U3; do h "$f"; done) | diff - "$W/u3.before" && echo "user files unchanged"`
3. `grep -c '^# baselines: shipped$' "$M3"`
4. `grep -E '  (\.writ/docs/tech-stack\.md|scripts/deploy\.sh|commands/my-own\.md|commands/review\.md)$' "$M3" || echo "no line for any user file"`

**Expected Result:**
- `exit 0` and `1 file(s) preserved (local modifications kept)` (that is `review.md`).
- `user files unchanged`.
- `1`.
- `no line for any user file`. `commands/review.md` was preserved with no baseline, so it gets no line.

**Status:** [x] Pass  [ ] Fail

**Notes:** Before the fix, install recorded all three user files and the first update removed them.

agent-run 2026-10-21 @ b850e66: `exit 0`, `1 file(s) preserved (local modifications kept)`; `user files unchanged`; `1`; `no line for any user file`.

**Implementation Reference:** Story 3 — `scripts/install.sh` (`write_copy_manifest`, `record_file_baseline`, `previous_manifest_hash_for`).

---

### Scenario 14: Re-installing over a manifest without the header writes no header

**Source:** Acceptance Criteria — Story 3 (AC-3.1, header rule)
**Feature:** none
**Verification:** human — no recipe
**Automated Test:** `scripts/tests/test_manifest_shipped_baselines.sh` (AC-3.1 header-less re-install)

**Preconditions:**
- Story 3 setup run (for `$SRC`).

**Steps:**
1. `P="$W/reinstall"; inst "$P" claude > /dev/null 2>&1; M="$P/.claude/.writ-manifest"; grep -c '^# baselines: shipped$' "$M"`
2. Remove the header: `grep -vx '# baselines: shipped' "$M" > "$W/m.tmp"; cat "$W/m.tmp" > "$M"`
3. `inst "$P" claude > /dev/null 2>&1; echo "exit $?"; grep -c '^# baselines: shipped$' "$M"`

**Expected Result:**
- Step 1: `1`.
- Step 3: `exit 0`, then `0`. Install leaves the manifest marked as legacy so the next `update.sh` repairs it (Story 5).

**Status:** [x] Pass  [ ] Fail

**Notes:** Residual risk (spec, not fixed here): re-install over a legacy manifest trusts its old baselines; `update.sh` is the supported upgrade path.

agent-run 2026-10-21 @ b850e66: step 1 `1`; step 3 `exit 0`, `0`.

---

### Scenario 15: Three updates never record, mention, or remove user files

**Source:** Acceptance Criteria — Story 3 (AC-3.2); Shadow Path (Customized shipped file — nil input: no baseline → preserved, still no line); Experience Design (State: update, user-authored file in a tracked folder)
**Feature:** none
**Verification:** human — no recipe
**Automated Test:** `scripts/tests/test_manifest_shipped_baselines.sh` (AC-3.2 updates 1–3)

**Preconditions:**
- Project after Scenario 13.

**Steps:**
1. Add two more user files: `echo "# style" > "$P3/.writ/docs/code-style.md"; mkdir -p "$P3/.claude/agents"; echo "# my agent" > "$P3/.claude/agents/my-agent.md"`
2. Run three updates:
   `for i in 1 2 3; do bump; upd "$P3" claude > "$W/u3-$i.txt" 2>&1; echo "update $i exit $?"; rewritten "$M3"; grep -E 'tech-stack|deploy\.sh|my-own|code-style|my-agent|review\.md|Stale|Removed' "$W/u3-$i.txt"; done`
3. `(cd "$P3" && for f in $U3; do h "$f"; done) | diff - "$W/u3.before" && echo "user files unchanged"; ls "$P3/.writ/docs/code-style.md" "$P3/.claude/agents/my-agent.md"`
4. `grep -E '  (\.writ/docs/(tech-stack|code-style)\.md|scripts/deploy\.sh|commands/(my-own|review)\.md|agents/my-agent\.md)$' "$M3" || echo "no line for any user file"`

**Expected Result:**
- Each update: `exit 0`, `manifest rewritten`, and exactly these matching lines:
  ```
  ⚡ Preserved: commands/review.md (no baseline, assuming modified)
  commands/review.md
  ```
  (the second is the end-of-run preserved list). No `Stale` or `Removed` line, and no line naming any other user file.
- `user files unchanged`; both new files still exist.
- `no line for any user file`.

**Status:** [x] Pass  [ ] Fail

**Notes:** Before the fix, files created after install were recorded by update 1 and removed by update 2.

agent-run 2026-10-21 @ b850e66: each update `exit 0`, `manifest rewritten`, and only `⚡ Preserved: commands/review.md (no baseline, assuming modified)` + `commands/review.md`; `user files unchanged`, both new files exist; `no line for any user file`.

**Implementation Reference:** Story 3 — `scripts/update.sh` (`load_baselines`, `record_file_baseline`, `write_copy_manifest` walks the shipped set from the source).

---

### Scenario 16: A customized command and CLAUDE.md Writ block keep their install-time baselines across upstream changes

**Source:** Acceptance Criteria — Story 3 (AC-3.3, Claude Code); Error Map (Rewrite manifest: preserved file re-baselined); Experience Design (State: update, customized shipped file, upstream changes it again)
**Feature:** none
**Verification:** human — no recipe
**Automated Test:** `scripts/tests/test_manifest_shipped_baselines.sh` (AC-3.3 claude)

**Preconditions:**
- Project after Scenario 15.

**Steps:**
1. Record the baselines: `SB=$(grep '  commands/status.md$' "$M3"); BB=$(grep '  CLAUDE.md.writ-block$' "$M3")`
2. Customize both:
   `printf '\n<!-- local edit -->\n' >> "$P3/.claude/commands/status.md"`
   `awk '{ print } $0 == "<!-- writ:start -->" { print "Local note inside the Writ block." }' "$P3/CLAUDE.md" > "$W/c.md" && cat "$W/c.md" > "$P3/CLAUDE.md"`
   `SL=$(h "$P3/.claude/commands/status.md"); CL=$(h "$P3/CLAUDE.md")`
3. Update 1: `bump; upd "$P3" claude > "$W/c1.txt" 2>&1; echo "exit $?"; rewritten "$M3"; grep 'Preserved' "$W/c1.txt"`
4. Upstream changes both: `printf '\n<!-- up -->\n' >> "$SRC/commands/status.md"; printf '\n<!-- up -->\n' >> "$SRC/claude-code/CLAUDE.md"; bump`
5. Update 2: `upd "$P3" claude > "$W/c2.txt" 2>&1; echo "exit $?"; rewritten "$M3"; grep 'Preserved' "$W/c2.txt"`
6. `[ "$(h "$P3/.claude/commands/status.md")" = "$SL" ] && [ "$(h "$P3/CLAUDE.md")" = "$CL" ] && echo "both unchanged"; [ "$(grep '  commands/status.md$' "$M3")" = "$SB" ] && [ "$(grep '  CLAUDE.md.writ-block$' "$M3")" = "$BB" ] && echo "baselines unchanged"`

**Expected Result:**
- Steps 3 and 5: `exit 0`, `manifest rewritten`, and among the Preserved lines:
  ```
  ⚡ Preserved: commands/status.md (local modifications)
  ⚡ Preserved: CLAUDE.md (Writ block has local modifications)
  ```
- Step 6: `both unchanged` and `baselines unchanged`.

**Status:** [x] Pass  [ ] Fail

**Notes:** Before the fix, update 1 re-baselined `status.md` to its local hash, and update 2 overwrote it (`🔄 Update`).

agent-run 2026-10-21 @ b850e66: steps 3 and 5 `exit 0`, `manifest rewritten`, both expected Preserved lines (plus review.md no-baseline); step 6 `both unchanged`, `baselines unchanged`.

---

### Scenario 17: A customized Cursor `rules/writ.mdc` keeps its install-time baseline

**Source:** Acceptance Criteria — Story 3 (AC-3.3, Cursor)
**Feature:** none
**Verification:** human — no recipe
**Automated Test:** `scripts/tests/test_manifest_shipped_baselines.sh` (AC-3.3 cursor)

**Preconditions:**
- Story 3 setup run (for `$SRC`).

**Steps:**
1. `PC="$W/cursor"; inst "$PC" cursor > /dev/null 2>&1; MC="$PC/.cursor/.writ-manifest"; RB=$(grep '  rules/writ.mdc$' "$MC"); echo "$RB"`
2. `printf '\n<!-- local edit -->\n' >> "$PC/.cursor/rules/writ.mdc"; RL=$(h "$PC/.cursor/rules/writ.mdc")`
3. `bump; upd "$PC" cursor > "$W/r1.txt" 2>&1; echo "exit $?"; rewritten "$MC"; grep 'writ.mdc' "$W/r1.txt"`
4. `printf '\n<!-- up -->\n' >> "$SRC/cursor/writ.mdc"; bump; upd "$PC" cursor > "$W/r2.txt" 2>&1; echo "exit $?"; rewritten "$MC"; grep 'writ.mdc' "$W/r2.txt"`
5. `[ "$(h "$PC/.cursor/rules/writ.mdc")" = "$RL" ] && echo "rule unchanged"; [ "$(grep '  rules/writ.mdc$' "$MC")" = "$RB" ] && echo "baseline unchanged"`

**Expected Result:**
- Steps 3 and 4: `exit 0`, `manifest rewritten`, and `⚡ Preserved: rules/writ.mdc (local modifications)`.
- Step 5: `rule unchanged` and `baseline unchanged`.

**Status:** [x] Pass  [ ] Fail

**Notes:** agent-run 2026-10-21 @ b850e66: steps 3 and 4 `exit 0`, `manifest rewritten`, `⚡ Preserved: rules/writ.mdc (local modifications)`; `rule unchanged`, `baseline unchanged`.

---

### Scenario 18: Every shipped path has exactly one well-formed line

**Source:** Acceptance Criteria — Story 3 (AC-3.4); Shadow Path (User-authored file — empty input: no user files → manifest equals the shipped set)
**Feature:** none
**Verification:** human — no recipe
**Automated Test:** `scripts/tests/test_manifest_shipped_baselines.sh` (`check_complete` on claude, cursor, and codex, after install and after an update)

**Preconditions:**
- Story 3 setup run (for `$SRC`).

**Steps:**
1. `PF="$W/fresh"; inst "$PF" claude > /dev/null 2>&1; MF="$PF/.claude/.writ-manifest"`
2. `awk '!/^#/ && NF {print $2}' "$MF" | sort > "$W/recorded"; echo "duplicates:"; uniq -d "$W/recorded"; echo "malformed:"; awk '!/^#/ && NF && $1 !~ /^[0-9a-f]{64}$/' "$MF"`
3. List what install put on disk and compare:
   `(cd "$PF" && { find .claude/commands .claude/agents -type f | sed 's|^\.claude/||'; (cd .claude && find skills -name SKILL.md); find scripts .writ/docs -type f; echo system-instructions.md; echo CLAUDE.md.writ-block; }) | sort > "$W/ondisk"; diff "$W/recorded" "$W/ondisk" && echo "one line per shipped file"`
4. `bump; upd "$PF" claude > /dev/null 2>&1; rewritten "$MF"`, then repeat steps 2 and 3.

**Expected Result:**
- After install and after the update: nothing under `duplicates:` or `malformed:`, and `one line per shipped file` (122 lines at plan time).
- No line for a dev-only script (for example `scripts/harness-cost.py`) or an unshipped `*.lean.md` command.

**Status:** [x] Pass  [ ] Fail

**Notes:** For a Codex check, the automated test also confirms the `.codex/config.toml.baseline` line is present once.

agent-run 2026-10-21 @ b850e66: after install and after the update (`manifest rewritten`): no duplicates, no malformed lines, 122 lines, no harness-cost.py or `*.lean.md` line. Step 3's diff printed only `< system-instructions.md` instead of `one line per shipped file`: Claude Code has shipped `.claude/system-instructions.md` since 18b1fe0 (after c74eb22); the file is on disk with the recorded hash, and the step's find list omits it. Legitimate growth; intent holds.
- maintainer sign-off 2026-10-21 (delegated): Pass accepted; .claude/system-instructions.md is shipped since 18b1fe0. Step 3's find list updated.

---

### Scenario 19: The shipped-baselines test fails on the pre-fix scripts and passes now

**Source:** Acceptance Criteria — Story 3 (AC-3.5)
**Feature:** none
**Verification:** human — no recipe
**Automated Test:** partial — CI runs the test and the regression tests; the pre-fix failure (step 2) is checked only by hand

**Preconditions:**
- Setup block pasted. Outside any sandbox. About 65 s per run.

**Steps:**
1. `bash "$REPO/scripts/tests/test_manifest_shipped_baselines.sh"; echo "exit $?"`
2. `X="$W/prefix-3"; mkdir -p "$X" && git -C "$REPO" archive ef012f5 | tar -x -C "$X" && git -C "$REPO" show c74eb22:scripts/tests/test_manifest_shipped_baselines.sh > "$X/scripts/tests/test_manifest_shipped_baselines.sh" && bash "$X/scripts/tests/test_manifest_shipped_baselines.sh"; echo "exit $?"`
3. `cd "$REPO" && for t in scripts/tests/test_install_update_*.sh scripts/tests/test_update_*.sh; do bash "$t" > /dev/null 2>&1 && echo "ok $t" || echo "FAIL $t"; done`

**Expected Result:**
- Step 1: `PASS test_manifest_shipped_baselines`, `exit 0`.
- Step 2 (recorded in What Was Built): `FAIL: AC-3.1 install: manifest records user file .writ/docs/tech-stack.md`, `exit 1`.
- Step 3: `ok` for every file, no `FAIL`.

**Status:** [x] Pass  [ ] Fail

**Notes:** `ef012f5` is the lane head after Story 2, before Story 3.

agent-run 2026-10-21 @ b850e66: step 1 `PASS test_manifest_shipped_baselines`, exit 0; step 3 `ok` for all 9 files. Step 2 expected `FAIL: AC-3.1 install: manifest records user file .writ/docs/tech-stack.md`, got `FAIL: cannot load is_shippable_writ_doc from update.sh`, exit 1. Stale expectation, not a product bug: the test now loads `is_shippable_writ_doc` (added in fff2582, after ef012f5). The plan-time test (`git show c74eb22:scripts/tests/test_manifest_shipped_baselines.sh`) on the same ef012f5 extract prints the expected FAIL line, exit 1.
- maintainer sign-off 2026-10-21 (delegated): Pass. Intent holds: the test that shipped with the fix (c74eb22) fails on the pre-fix extract with the expected AC-3.1 line; today's test fails earlier on a helper added later (fff2582). Step 2 updated to run the c74eb22 test.

---

### Scenario 20: An update whose source cannot be cloned changes nothing

**Source:** Shadow Path (upstream error: clone fails → no write) — Story 3; the same row applies to the customized-file, kept-stale, and Codex flows
**Feature:** none
**Verification:** human — no recipe
**Automated Test:** none — manual only

**Preconditions:**
- Project after Scenario 16.

**Steps:**
1. `cp "$M3" "$W/m3.before"`
2. `UPSTREAM="$W/does-not-exist" upd "$P3" claude; echo "exit $?"`
3. `cmp "$M3" "$W/m3.before" && echo "manifest byte-identical"; (cd "$P3" && for f in $U3; do h "$f"; done) | diff - "$W/u3.before" && echo "user files unchanged"`

**Expected Result:**
- Step 2 ends with:
  ```
  ❌ Failed to clone <path>/does-not-exist
     Check your network connection and try again.
  exit 1
  ```
- Step 3: `manifest byte-identical` and `user files unchanged`.

**Status:** [x] Pass  [ ] Fail

**Notes:** agent-run 2026-10-21 @ b850e66: ends `❌ Failed to clone <W>/does-not-exist`, `Check your network connection and try again.`, `exit 1`; `manifest byte-identical`, `user files unchanged`.

---

### Scenario 21: `--force` overwrites a preserved file and records the upstream hash

**Source:** Edge Case (`--force` with a preserved file) — Story 3
**Feature:** none
**Verification:** human — no recipe
**Automated Test:** none — manual only (evaluator probe during Story 3)

**Preconditions:**
- Project after Scenario 16 (`status.md` and the Writ block customized).

**Steps:**
1. `upd "$P3" claude --force > "$W/f.txt" 2>&1; echo "exit $?"; grep -E 'status\.md|CLAUDE' "$W/f.txt"`
2. `cmp "$P3/.claude/commands/status.md" "$SRC/commands/status.md" && echo "equals upstream"`
3. `[ "$(grep '  commands/status.md$' "$M3" | cut -d' ' -f1)" = "$(h "$SRC/commands/status.md")" ] && echo "upstream hash recorded"`

**Expected Result:**
- `exit 0`, with `🔄 Update:    commands/status.md (forced)` and `🔄 Updated: CLAUDE.md (Writ block forced)`.
- `equals upstream`.
- `upstream hash recorded`.

**Status:** [x] Pass  [ ] Fail

**Notes:** `--force` also overwrites the user-written `commands/review.md` (it is at a shipped path). That is expected.

agent-run 2026-10-21 @ b850e66: `exit 0`, `🔄 Update:    commands/status.md (forced)`, `🔄 Updated: CLAUDE.md (Writ block forced)`; `equals upstream`; `upstream hash recorded`.

---

### Scenario 22: A deleted shipped file is re-copied and gets the upstream hash

**Source:** Edge Case (user deletes a shipped file) — Story 3
**Feature:** none
**Verification:** human — no recipe
**Automated Test:** none — manual only (evaluator probe during Story 3)

**Preconditions:**
- Story 3 setup run (for `$SRC`).

**Steps:**
1. `PD="$W/deleted"; inst "$PD" claude > /dev/null 2>&1; MD="$PD/.claude/.writ-manifest"`
2. `rm "$PD/.claude/commands/status.md"`
3. `bump; upd "$PD" claude > "$W/d.txt" 2>&1; echo "exit $?"; grep 'status.md' "$W/d.txt"`
4. `cmp "$PD/.claude/commands/status.md" "$SRC/commands/status.md" && echo "re-copied"; [ "$(grep '  commands/status.md$' "$MD" | cut -d' ' -f1)" = "$(h "$SRC/commands/status.md")" ] && echo "upstream hash recorded"`

**Expected Result:**
- `exit 0` and a `✨ New:` line for `commands/status.md`.
- `re-copied` and `upstream hash recorded`.

**Status:** [x] Pass  [ ] Fail

**Notes:** agent-run 2026-10-21 @ b850e66: `exit 0`, `✨ New:       commands/status.md`; `re-copied`, `upstream hash recorded`.

---

## Story 4: Keep Modified Stale Files in Every Category

**Story setup** (on top of the main setup block). Source A ships five `zz-kept` files and an unmodified `zz-clean.md`; source B is a clean copy without them.

```bash
new_src s4b; SRC_B="$SRC"
new_src s4a; SRC_A="$SRC"
mkdir -p "$SRC/skills/zz-kept"
for f in commands/zz-kept.md commands/zz-clean.md claude-code/agents/zz-kept.md skills/zz-kept/SKILL.md .writ/docs/zz-kept.md; do
  printf '# %s\n\nfixture\n' "$f" > "$SRC/$f"; done
printf 'print("zz")\n' > "$SRC/scripts/zz_kept.py"
gc "source A"
P4="$W/stale"; inst "$P4" claude > /dev/null 2>&1; echo "install exit $?"; M4="$P4/.claude/.writ-manifest"
K4=".claude/commands/zz-kept.md .claude/agents/zz-kept.md .claude/skills/zz-kept/SKILL.md .writ/docs/zz-kept.md scripts/zz_kept.py"
STALE_RE='  (commands/zz-|agents/zz-|skills/zz-|\.writ/docs/zz-|scripts/zz_)'
grep -E "$STALE_RE" "$M4" > "$W/kept-install-lines"; grep -v zz-clean "$W/kept-install-lines" > "$W/kept-lines"
for f in $K4; do printf '\nmy edit\n' >> "$P4/$f"; done
(cd "$P4" && for f in $K4; do h "$f"; done) > "$W/k4.edited"
SRC="$SRC_B"     # from here on, upstream no longer ships any zz file
```

### Scenario 23: Edited files in five categories survive three updates after upstream drops them

**Source:** Acceptance Criteria — Story 4 (AC-4.1); Error Map (Rewrite manifest: kept stale path); Experience Design (State: update, modified stale file, any category)
**Feature:** none
**Verification:** human — no recipe
**Automated Test:** `scripts/tests/test_update_kept_stale_files.sh` (updates 1–3)

**Preconditions:**
- Story 4 setup run. `install exit 0`.

**Steps:**
1. `for i in 1 2 3; do [ $i -gt 1 ] && bump; upd "$P4" claude > "$W/s4-$i.txt" 2>&1; echo "update $i exit $?"; rewritten "$M4"; (cd "$P4" && for f in $K4; do h "$f"; done) | diff -q - "$W/k4.edited" > /dev/null && echo "kept files unchanged"; done`

**Expected Result:**
- For each of the three updates: `exit 0`, `manifest rewritten`, `kept files unchanged`.

**Status:** [x] Pass  [ ] Fail

**Notes:** Update 1 rewrites the manifest because it removes `zz-clean.md`; updates 2 and 3 because of `bump`.

agent-run 2026-10-21 @ b850e66: updates 1-3 each `exit 0`, `manifest rewritten`, `kept files unchanged`.

**Implementation Reference:** Story 4 — `scripts/update.sh` (`detect_stale_files` warns and carries the old baseline in every category).

---

### Scenario 24: Every run warns about all five kept files, including up-to-date runs and dry runs

**Source:** Acceptance Criteria — Story 4 (AC-4.2); Error Map (Update early exit: only kept stale files differ); Experience Design (State: update, second and later runs)
**Feature:** none
**Verification:** human — no recipe
**Automated Test:** `scripts/tests/test_update_kept_stale_files.sh` (updates 1–3, "Already up to date" run, dry run)

**Preconditions:**
- Project after Scenario 23.

**Steps:**
1. `for i in 1 2 3; do echo "update $i:"; grep -c 'Stale (no longer shipped, locally modified — kept)' "$W/s4-$i.txt"; done; grep 'Stale' "$W/s4-3.txt"`
2. Up-to-date run: `cp "$M4" "$W/m4.before"; upd "$P4" claude > "$W/s4-utd.txt" 2>&1; echo "exit $?"; grep -E 'Stale|Already' "$W/s4-utd.txt"; cmp "$M4" "$W/m4.before" && echo "manifest byte-identical"`
3. Dry run with a change pending: `bump; upd "$P4" claude --dry-run > "$W/s4-dry.txt" 2>&1; echo "exit $?"; grep -E 'Stale|DRY' "$W/s4-dry.txt"; cmp "$M4" "$W/m4.before" && echo "manifest byte-identical"`

**Expected Result:**
- Step 1: `5` for each update, and update 3 prints:
  ```
  ⚠️  Stale (no longer shipped, locally modified — kept): scripts/zz_kept.py
  ⚠️  Stale (no longer shipped, locally modified — kept): .writ/docs/zz-kept.md
  ⚠️  Stale (no longer shipped, locally modified — kept): commands/zz-kept.md
  ⚠️  Stale (no longer shipped, locally modified — kept): agents/zz-kept.md
  ⚠️  Stale (no longer shipped, locally modified — kept): skills/zz-kept/SKILL.md
  ```
- Step 2: `exit 0`, the same five warnings, `✅ Already up to date! (<version>)`, and `manifest byte-identical`.
- Step 3: `exit 0`, the same five warnings, `🏃 DRY RUN — No changes applied.`, and `manifest byte-identical`.

**Status:** [x] Pass  [ ] Fail

**Notes:** The warning text is byte-identical to the pre-fix text; other tests match it.

agent-run 2026-10-21 @ b850e66: `5` for each update and the five expected Stale lines; up-to-date run `exit 0`, five warnings, `✅ Already up to date! (0454087)`, `manifest byte-identical`; dry run `exit 0`, five warnings, `🏃 DRY RUN — No changes applied.`, `manifest byte-identical`.

---

### Scenario 25: Each kept file keeps one install-time line; the unmodified dropped file is removed

**Source:** Acceptance Criteria — Story 4 (AC-4.3); Experience Design (State: update, unmodified stale file)
**Feature:** none
**Verification:** human — no recipe
**Automated Test:** `scripts/tests/test_update_kept_stale_files.sh` (manifest checks after each run; `zz-clean.md` removal)

**Preconditions:**
- Project after Scenario 24.

**Steps:**
1. `grep 'Removed' "$W/s4-1.txt"; ls "$P4/.claude/commands/zz-clean.md" 2>&1 | sed 's/.*: //'`
2. `grep -E "$STALE_RE" "$M4" | sort | diff - <(sort "$W/kept-lines") && echo "kept lines carry install-time hashes"`

**Expected Result:**
- Step 1: `🗑  Removed: commands/zz-clean.md` and `No such file or directory`.
- Step 2: `kept lines carry install-time hashes`. Five lines, one per kept path, no `zz-clean.md` line, and no local (edited) hash.

**Status:** [x] Pass  [ ] Fail

**Notes:** agent-run 2026-10-21 @ b850e66: `🗑  Removed: commands/zz-clean.md`, `No such file or directory`; `kept lines carry install-time hashes` (5 lines).

---

### Scenario 26: Deleting a kept file ends its warning and drops its line

**Source:** Error Map (Stale removal: user deleted the kept file) — Story 4; Acceptance Criteria (AC-4.3, last clause); Experience Design (State: user deletes a kept stale file)
**Feature:** none
**Verification:** human — no recipe
**Automated Test:** `scripts/tests/test_update_kept_stale_files.sh` (delete-then-update)

**Preconditions:**
- Project after Scenario 25.

**Steps:**
1. `rm "$P4/.writ/docs/zz-kept.md"`
2. `bump; upd "$P4" claude > "$W/s4-del.txt" 2>&1; echo "exit $?"; rewritten "$M4"; grep -c 'Stale' "$W/s4-del.txt"; grep 'zz-kept.md' "$W/s4-del.txt" | grep -c '\.writ/docs'`
3. `grep -c '  .writ/docs/zz-kept.md$' "$M4"`

**Expected Result:**
- Step 2: `exit 0`, `manifest rewritten`, `4` warnings, and `0` lines naming `.writ/docs/zz-kept.md`.
- Step 3: `0`.

**Status:** [x] Pass  [ ] Fail

**Notes:** agent-run 2026-10-21 @ b850e66: `exit 0`, `manifest rewritten`, `4`, `0`; step 3 `0`.

---

### Scenario 27: The kept-stale test fails on the pre-fix script and passes now

**Source:** Acceptance Criteria — Story 4 (AC-4.4)
**Feature:** none
**Verification:** human — no recipe
**Automated Test:** partial — CI runs the test and `test_install_update_dev_scripts.sh`; the pre-fix failure (step 2) is checked only by hand

**Preconditions:**
- Setup block pasted. Outside any sandbox. About 45 s per run.

**Steps:**
1. `bash "$REPO/scripts/tests/test_update_kept_stale_files.sh"; echo "exit $?"; bash "$REPO/scripts/tests/test_install_update_dev_scripts.sh"; echo "exit $?"`
2. `X="$W/prefix-4"; mkdir -p "$X" && git -C "$REPO" archive ce2f049 | tar -x -C "$X" && cp "$REPO/scripts/tests/test_update_kept_stale_files.sh" "$X/scripts/tests/" && bash "$X/scripts/tests/test_update_kept_stale_files.sh"; echo "exit $?"`

**Expected Result:**
- Step 1: `PASS test_update_kept_stale_files`, `exit 0`, then `exit 0` for the dev-scripts test.
- Step 2 (recorded in What Was Built): starts with `FAIL: update 1: no stale warning for the kept commands/zz-kept.md.`, `exit 1`.

**Status:** [x] Pass  [ ] Fail

**Notes:** AC-4.4 says the failure names a removed file. After Story 3 the pre-fix script drops the line instead, so the test fails on the missing warning (DEV-004, accepted).

agent-run 2026-10-21 @ b850e66: step 1 `PASS test_update_kept_stale_files`, exit 0, then `PASS test_install_update_dev_scripts`, exit 0; step 2 starts `FAIL: update 1: no stale warning for the kept commands/zz-kept.md.`, exit 1.

---

### Scenario 28: `/update-writ` describes the fixed manifest, and the stale-files issue is resolved

**Source:** Acceptance Criteria — Story 4 (AC-4.5)
**Feature:** none
**Verification:** human — no recipe
**Automated Test:** partial — `test_update_kept_stale_files.sh` checks the Step 7 template header and that four retired claims are gone; reading the sections and the issue is manual

**Preconditions:**
- None

**Steps:**
1. Open `commands/update-writ.md`. Read the frontmatter `outcome` and exit criteria, Step 3 "Detect stale files", Step 6 item 6, Step 7 (prose, template, bullets), and Completion.
2. Open `.writ/issues/bugs/2026-10-12-update-deletes-modified-stale-files.md` and read the end.

**Expected Result:**
- Frontmatter, Step 7, and Completion each say: only shipped paths get baselines; a kept customized or stale file keeps its previous baseline; a modified stale file is flagged on every run.
- Step 3 and Step 6 item 6 state the shipped-only and stale-file claims (DEV-005: they omit the customized-file claim, accepted).
- The Step 7 manifest template contains `# baselines: shipped` and a kept-stale example line.
- Nothing says a kept file gets a fresh baseline or that the manifest re-baselines to what is on disk.
- The issue ends with `## Resolution` naming shipped-only recording (Story 3), the `detect_stale_files` change, and `scripts/tests/test_update_kept_stale_files.sh`.

**Status:** [x] Pass  [ ] Fail

**Notes:** Known wording gap (evaluator, Minor): Step 7 and Completion say a kept customized file is asked about again "when upstream changes" it; it is reported on every run while it differs from upstream.

needs maintainer judgment: read `commands/update-writ.md` frontmatter (outcome, exit criteria), Step 3 "Detect stale files", Step 6 item 6, Step 7 and Completion, and judge whether the three claims are stated clearly. Agent pre-check: Step 7 template has `# baselines: shipped` and a kept-stale example line; no "fresh" / "on disk" / "re-baselin" claim found; the issue ends with `## Resolution` naming Stories 3 and 4, `detect_stale_files`, and the test.
- maintainer judgment 2026-10-21: Pass; wording gap filed as .writ/issues/improvements/2026-10-21-update-writ-kept-file-wording.md.

---

### Scenario 29: Upstream re-adding a kept path preserves the user's copy

**Source:** Edge Case (upstream re-adds a path the user kept) — Story 4
**Feature:** none
**Verification:** human — no recipe
**Automated Test:** none — manual only (evaluator probe during Story 4)

**Preconditions:**
- Project after Scenario 26.

**Steps:**
1. `cp "$SRC_A/commands/zz-kept.md" "$SRC/commands/zz-kept.md"; bump`
2. `upd "$P4" claude > "$W/s4-readd.txt" 2>&1; echo "exit $?"; rewritten "$M4"; grep -E 'zz-kept|zz_kept' "$W/s4-readd.txt"`
3. `grep '  commands/zz-kept.md$' "$M4"; h "$SRC_A/commands/zz-kept.md"`

**Expected Result:**
- `exit 0`, `manifest rewritten`, and `⚡ Preserved: commands/zz-kept.md (local modifications)`. No Stale line for `commands/zz-kept.md`; the other kept files still warn.
- The manifest hash for `commands/zz-kept.md` equals the source A hash printed after it (the carried baseline).

**Status:** [x] Pass  [ ] Fail

**Notes:** agent-run 2026-10-21 @ b850e66: `exit 0`, `manifest rewritten`, `⚡ Preserved: commands/zz-kept.md (local modifications)`, no Stale line for it, the other three kept files still warn; manifest hash `3f92fc2c…` equals the source A hash.

---

### Scenario 30: Reverting a kept file to its shipped content lets update remove it

**Source:** Edge Case (user reverts a kept file to the original) — Story 4
**Feature:** none
**Verification:** human — no recipe
**Automated Test:** none — manual only (evaluator probe during Story 4)

**Preconditions:**
- Project after Scenario 29.

**Steps:**
1. `cp "$SRC_A/claude-code/agents/zz-kept.md" "$P4/.claude/agents/zz-kept.md"; bump`
2. `upd "$P4" claude > "$W/s4-rev.txt" 2>&1; echo "exit $?"; grep -E 'agents/zz-kept' "$W/s4-rev.txt"; ls "$P4/.claude/agents/zz-kept.md" 2>&1 | sed 's/.*: //'`

**Expected Result:**
- `exit 0`, `🗑  Removed: agents/zz-kept.md`, and `No such file or directory`.

**Status:** [x] Pass  [ ] Fail

**Notes:** agent-run 2026-10-21 @ b850e66: `exit 0`, `🗑  Removed: agents/zz-kept.md`, `No such file or directory`.

---

### Scenario 31: `--force` does not change how kept stale files are handled

**Source:** Edge Case (`--force` with a kept stale file) — Story 4; Business Rule 7
**Feature:** none
**Verification:** human — no recipe
**Automated Test:** none — manual only (evaluator probe during Story 4)

**Preconditions:**
- Project after Scenario 30 (kept: `scripts/zz_kept.py`, `skills/zz-kept/SKILL.md`). `commands/zz-kept.md` is shipped again, so `--force` overwrites it; that is expected.

**Steps:**
1. `(cd "$P4" && h scripts/zz_kept.py; h .claude/skills/zz-kept/SKILL.md) > "$W/k4.force"`
2. `upd "$P4" claude --force > "$W/s4-force.txt" 2>&1; echo "exit $?"; grep -E 'Stale|Removed' "$W/s4-force.txt"`
3. `(cd "$P4" && h scripts/zz_kept.py; h .claude/skills/zz-kept/SKILL.md) | diff - "$W/k4.force" && echo "kept files unchanged"`

**Expected Result:**
- `exit 0` and the same Stale warnings for `scripts/zz_kept.py` and `skills/zz-kept/SKILL.md`. No `Removed` line for either.
- `kept files unchanged`.

**Status:** [x] Pass  [ ] Fail

**Notes:** agent-run 2026-10-21 @ b850e66: `exit 0`, Stale warnings for `scripts/zz_kept.py` and `skills/zz-kept/SKILL.md`, no Removed line; `kept files unchanged`.

---

## Story 5: Repair Legacy Manifests and Remove Stale Files From Their Real Path

**Story setup** (on top of the main setup block). It builds source A with retired fixtures, installs one base project per platform, then commits source B, which drops the fixtures. Each scenario copies a base project and turns its manifest into one a pre-fix release would have written.

```bash
new_src s5
mkdir -p "$SRC/skills/zz-old" "$SRC/skills/zz-locked"
printf '# zz-retired\n\nShipped by source A only.\n' > "$SRC/commands/zz-retired.md"
printf '# zz-old\n'    > "$SRC/skills/zz-old/SKILL.md"
printf '# zz-locked\n' > "$SRC/skills/zz-locked/SKILL.md"
gc "source A"; VA=$(git -C "$SRC" log -1 --format=%h); echo "VA=$VA"
for pf in claude codex cursor; do inst "$W/base-$pf" $pf > /dev/null 2>&1 && echo "base-$pf installed"; done
git -C "$SRC" rm -q commands/zz-retired.md skills/zz-old/SKILL.md skills/zz-locked/SKILL.md
printf '\n<!-- upstream change B -->\n' >> "$SRC/commands/status.md"
printf '\n<!-- upstream change B -->\n' >> "$SRC/cursor/writ.mdc"
printf '# zz-new\n\nAdded by source B.\n' > "$SRC/commands/zz-new.md"     # gives every run something to apply
gc "source B"

# Strip the header and set "# version:" ("" removes the line), as a pre-fix manifest.
make_legacy() {
  awk -v v="$2" '$0 == "# baselines: shipped" { next }
    /^# version:/ { if (v != "") print "# version: " v; next } { print }' "$1" > "$W/legacy.tmp" &&
    cat "$W/legacy.tmp" > "$1"
}
# add_user_files <project> <.claude|.codex|.cursor>: three user files, recorded at
# their local hashes the way pre-fix scripts did.
add_user_files() {
  local p="$1" d="$2" m="$1/$2/.writ-manifest"
  mkdir -p "$p/.writ/docs" "$p/scripts" "$p/$d/commands"
  echo "# our stack" > "$p/.writ/docs/tech-stack.md"
  printf '#!/bin/sh\necho deploy\n' > "$p/scripts/deploy.sh"
  echo "# my own command" > "$p/$d/commands/my-own.md"
  printf '%s  .writ/docs/tech-stack.md\n%s  scripts/deploy.sh\n%s  commands/my-own.md\n' \
    "$(h "$p/.writ/docs/tech-stack.md")" "$(h "$p/scripts/deploy.sh")" "$(h "$p/$d/commands/my-own.md")" >> "$m"
  (cd "$p" && h .writ/docs/tech-stack.md; h scripts/deploy.sh; h "$d/commands/my-own.md") > "$p.user-hashes"
}
# Edit commands/status.md and re-baseline it to its local hash, as pre-fix scripts did.
customize_status() {
  local m="$1/.claude/.writ-manifest" f="$1/.claude/commands/status.md"
  printf '\n<!-- local edit -->\n' >> "$f"
  awk -v hh="$(h "$f")" '!/^#/ && $2 == "commands/status.md" { print hh "  commands/status.md"; next } { print }' \
    "$m" > "$W/cs.tmp" && cat "$W/cs.tmp" > "$m"
}
user_files_same() {
  (cd "$1" && h .writ/docs/tech-stack.md; h scripts/deploy.sh; h "$2/commands/my-own.md") | diff -q - "$1.user-hashes" > /dev/null \
    && echo "user files unchanged" || echo "user files CHANGED"
  grep -E '  (\.writ/docs/tech-stack\.md|scripts/deploy\.sh|commands/my-own\.md)$' "$1/$2/.writ-manifest" || echo "no line for any user file"
}
```

### Scenario 32: First update from a legacy manifest leaves the user's own files alone

**Source:** Acceptance Criteria — Story 5 (AC-5.1); Error Map (Legacy manifest: version found); Experience Design (Moment of truth: the first fixed update on an old install deletes nothing of the user's; State: legacy manifest, version found)
**Feature:** none
**Verification:** human — no recipe
**Automated Test:** `scripts/tests/test_update_legacy_manifest.sh` (case A, and the second-update check)

**Preconditions:**
- Story 5 setup run; three `base-*` lines printed.

**Steps:**
1. `PA="$W/legacy-a"; cp -R "$W/base-claude" "$PA"; MA="$PA/.claude/.writ-manifest"; make_legacy "$MA" "$VA"; add_user_files "$PA" .claude; customize_status "$PA"`
2. `grep -c '^# baselines' "$MA"; grep -E '  (\.writ/docs/tech-stack\.md|scripts/deploy\.sh|commands/my-own\.md)$' "$MA"`
3. `upd "$PA" claude > "$W/a1.txt" 2>&1; echo "exit $?"; rewritten "$MA"; grep -E 'Removed|Stale|predates' "$W/a1.txt"`
4. `grep -c '^# baselines: shipped$' "$MA"; user_files_same "$PA" .claude`
5. Second update: `bump; upd "$PA" claude > "$W/a2.txt" 2>&1; echo "exit $?"; grep -E 'tech-stack|deploy|my-own' "$W/a2.txt" || echo "no line names a user file"; user_files_same "$PA" .claude`

**Expected Result:**
- Step 2: `0`, then three lines recording the user files (the legacy state).
- Step 3: `exit 0`, `manifest rewritten`, and exactly:
  ```
  🗑  Removed: commands/zz-retired.md
  🗑  Removed: skills/zz-locked/SKILL.md
  🗑  Removed: skills/zz-old/SKILL.md
  ```
  No line names `tech-stack.md`, `deploy.sh`, or `my-own.md`. No legacy notice.
- Step 4: `1`, `user files unchanged`, `no line for any user file`.
- Step 5: `exit 0`, `no line names a user file`, `user files unchanged`, `no line for any user file`.

**Status:** [x] Pass  [ ] Fail

**Notes:** Before the fix, the same run printed `🗑  Removed:` for all three user files and deleted them. An `unlink.sh`-written manifest also lacks the header and takes this same path (evaluator probe; not reproduced here because `unlink.sh` needs a linked install from GitHub).

agent-run 2026-10-21 @ b850e66: step 2 `0` + three user-file lines; step 3 `exit 0`, `manifest rewritten`, exactly the three expected Removed lines, no user file named, no notice; step 4 `1`, `user files unchanged`, `no line for any user file`; step 5 `exit 0`, `no line names a user file`, unchanged, no line.

**Implementation Reference:** Story 5 — `scripts/update.sh` (`load_baselines`, `load_legacy_baselines`, `legacy_source_path`, `legacy_resolve_commit`).

---

### Scenario 33: The same update removes the retired Writ file and preserves the re-baselined customization

**Source:** Acceptance Criteria — Story 5 (AC-5.2)
**Feature:** none
**Verification:** human — no recipe
**Automated Test:** `scripts/tests/test_update_legacy_manifest.sh` (case A)

**Preconditions:**
- Run Scenario 32 steps 1–3 first; this scenario checks the same run. Note: source B changed `commands/status.md` upstream.

**Steps:**
1. `ls "$PA/.claude/commands/zz-retired.md" 2>&1 | sed 's/.*: //'`
2. `grep 'status.md' "$W/a1.txt"`
3. `grep '  commands/status.md$' "$MA" | cut -d' ' -f1; git -C "$SRC" show "$VA:commands/status.md" | shasum -a 256 | cut -d' ' -f1`
4. `grep -c 'local edit' "$PA/.claude/commands/status.md"`

**Expected Result:**
- Step 1: `No such file or directory`.
- Step 2: `⚡ Preserved: commands/status.md (local modifications)` (and the same path in the end-of-run list). No `🔄 Update` line for it.
- Step 3: the two hashes are equal. The baseline is the upstream content at the recorded version, not the local hash the old script wrote.
- Step 4: `1` (the edit survived).

**Status:** [x] Pass  [ ] Fail

**Notes:** Before the fix, the old local-hash baseline made the edited file look unmodified, and the update overwrote it.

agent-run 2026-10-21 @ b850e66: `No such file or directory`; `⚡ Preserved: commands/status.md (local modifications)` + end-of-run path, no Update line; both hashes `8fe6d62b…`; `1`.

---

### Scenario 34: A legacy manifest with an unknown or missing version falls back safely

**Source:** Acceptance Criteria — Story 5 (AC-5.3, fallback); Error Map (Legacy manifest: version not found); Shadow Path (Legacy manifest upgrade — nil input: `# version:` missing or `unknown`); Experience Design (State: legacy manifest, version not found)
**Feature:** none
**Verification:** human — no recipe
**Automated Test:** `scripts/tests/test_update_legacy_manifest.sh` (case B: `unknown` and no version line)

**Preconditions:**
- Story 5 setup run.

**Steps:**
1. `PU="$W/legacy-unknown"; cp -R "$W/base-claude" "$PU"; MU="$PU/.claude/.writ-manifest"; make_legacy "$MU" unknown; add_user_files "$PU" .claude; customize_status "$PU"; SU=$(h "$PU/.claude/commands/status.md")`
2. `upd "$PU" claude > "$W/u1.txt" 2>&1; echo "exit $?"; rewritten "$MU"; grep -E 'predates|Removed|Stale|Preserved|New' "$W/u1.txt"`
3. `ls "$PU/.claude/commands/zz-retired.md" "$PU/.claude/skills/zz-old/SKILL.md"; [ "$(h "$PU/.claude/commands/status.md")" = "$SU" ] && echo "status unchanged"; user_files_same "$PU" .claude; grep -c '^# baselines: shipped$' "$MU"`
4. Missing version line: `PN="$W/legacy-nover"; cp -R "$W/base-claude" "$PN"; make_legacy "$PN/.claude/.writ-manifest" ""; grep -c '^# version' "$PN/.claude/.writ-manifest"; upd "$PN" claude 2>&1 | grep -c predates`

**Expected Result:**
- Step 2: `exit 0`, `manifest rewritten`, one notice:
  `⚠️  Manifest predates shipped-only baselines and its version is unknown; files that differ from upstream are preserved this run.`
  Then `⚡ Preserved: commands/status.md (no baseline, assuming modified)` (plus the same for `commands/create-issue.md` if an earlier scenario ran `bump`) and `✨ New:       commands/zz-new.md`. No `Removed` or `Stale` line.
- Step 3: both retired files still listed by `ls`; `status unchanged`; `user files unchanged`; `no line for any user file`; `1`.
- Step 4: `0`, then `1` (the same notice, once).

**Status:** [x] Pass  [ ] Fail

**Notes:** After a fallback, an unedited but outdated file may show as "Preserved (no baseline)" on later runs until the user deletes it or uses `--force`. This is conservative by design (evaluator residual).

agent-run 2026-10-21 @ b850e66: step 2 `exit 0`, `manifest rewritten`, the "its version is unknown" notice once, Preserved (no baseline) for `create-issue.md` and `status.md`, `✨ New:       commands/zz-new.md`, no Removed/Stale; step 3 both retired files listed, `status unchanged`, user files unchanged, no line, `1`; step 4 `0`, `1`.

---

### Scenario 35: A version that is not a known commit falls back with "not found upstream"

**Source:** Error Map (Legacy manifest: version not found, or fetch fails) — Story 5; Shadow Path (Legacy manifest upgrade — upstream error); drift DEV-009
**Feature:** none
**Verification:** human — no recipe
**Automated Test:** partial — `test_update_legacy_manifest.sh` covers `0000000` over a plain and a shallow `file://` clone; `HEAD` and other non-hex values were evaluator probes only

**Preconditions:**
- Story 5 setup run.

**Steps:**
1. `for v in 0000000 HEAD; do P="$W/legacy-$v"; cp -R "$W/base-claude" "$P"; make_legacy "$P/.claude/.writ-manifest" "$v"; upd "$P" claude > "$W/v-$v.txt" 2>&1; echo "$v exit $?"; grep -E 'predates|Removed' "$W/v-$v.txt"; done`
2. Shallow clone: `P="$W/legacy-shallow-bogus"; cp -R "$W/base-claude" "$P"; make_legacy "$P/.claude/.writ-manifest" 0000000; UPSTREAM="file://$SRC" upd "$P" claude > "$W/v-sh.txt" 2>&1; echo "exit $?"; grep -E 'predates|Removed' "$W/v-sh.txt"`

**Expected Result:**
- Each run: `exit 0` and one notice, with no `Removed` line:
  - `⚠️  Manifest predates shipped-only baselines and version 0000000 was not found upstream; files that differ from upstream are preserved this run.`
  - `⚠️  Manifest predates shipped-only baselines and version HEAD was not found upstream; files that differ from upstream are preserved this run.`
- Step 2 prints the `0000000` notice even though the shallow clone first fetched its full history.

**Status:** [x] Pass  [ ] Fail

**Notes:** Only 4–40 lowercase hex characters are treated as a version, so a value like `HEAD`, `main`, or `--help` from the manifest never reaches git as a ref or option.

agent-run 2026-10-21 @ b850e66: `0000000 exit 0` and `HEAD exit 0`, each with its exact "was not found upstream" notice and no Removed line; shallow `file://` run `exit 0` with the `0000000` notice.

---

### Scenario 36: On Codex, the fallback keeps the config baseline line

**Source:** Acceptance Criteria — Story 5 (AC-5.3, Codex)
**Feature:** none
**Verification:** human — no recipe
**Automated Test:** `scripts/tests/test_update_legacy_manifest.sh` (case B, Codex)

**Preconditions:**
- Story 5 setup run.

**Steps:**
1. `PXU="$W/legacy-codex"; cp -R "$W/base-codex" "$PXU"; MXU="$PXU/.codex/.writ-manifest"; make_legacy "$MXU" unknown; CBU=$(grep '  .codex/config.toml.baseline$' "$MXU"); printf '\n# local edit\n' >> "$PXU/.codex/config.toml"; CFU=$(h "$PXU/.codex/config.toml")`
2. `upd "$PXU" codex > "$W/xu.txt" 2>&1; echo "exit $?"; rewritten "$MXU"; grep -E 'predates|Removed' "$W/xu.txt"`
3. `[ "$(grep '  .codex/config.toml.baseline$' "$MXU")" = "$CBU" ] && echo "config line unchanged"; [ "$(h "$PXU/.codex/config.toml")" = "$CFU" ] && echo "config unchanged"; grep -c '^# baselines: shipped$' "$MXU"`

**Expected Result:**
- Step 2: `exit 0`, `manifest rewritten`, the "its version is unknown" notice, no `Removed` line.
- Step 3: `config line unchanged`, `config unchanged`, `1`.

**Status:** [x] Pass  [ ] Fail

**Notes:** agent-run 2026-10-21 @ b850e66: `exit 0`, `manifest rewritten`, "its version is unknown" notice, no Removed; `config line unchanged`, `config unchanged`, `1`.

---

### Scenario 37: On Cursor, the fallback preserves a customized rule and system instructions

**Source:** Acceptance Criteria — Story 5 (AC-5.3, Cursor); drift DEV-007 (recoded at iteration 2)
**Feature:** none
**Verification:** human — no recipe
**Automated Test:** `scripts/tests/test_update_legacy_manifest.sh` (Cursor unresolved, plus the second update)

**Preconditions:**
- Story 5 setup run. Source B changed `cursor/writ.mdc` upstream.

**Steps:**
1. `PCU="$W/legacy-cursor"; cp -R "$W/base-cursor" "$PCU"; MCU="$PCU/.cursor/.writ-manifest"; make_legacy "$MCU" unknown`
2. `printf '\n<!-- local edit -->\n' >> "$PCU/.cursor/rules/writ.mdc"; printf '\n<!-- local edit -->\n' >> "$PCU/.cursor/system-instructions.md"; R=$(h "$PCU/.cursor/rules/writ.mdc"); S=$(h "$PCU/.cursor/system-instructions.md")`
3. `upd "$PCU" cursor > "$W/cu1.txt" 2>&1; echo "exit $?"; rewritten "$MCU"; grep -E 'writ\.mdc|system-instructions|predates' "$W/cu1.txt"`
4. Second update (now a header manifest with no line for either unit): `bump; upd "$PCU" cursor > "$W/cu2.txt" 2>&1; echo "exit $?"; grep -E 'Preserved: (rules|system)' "$W/cu2.txt"`
5. `[ "$(h "$PCU/.cursor/rules/writ.mdc")" = "$R" ] && [ "$(h "$PCU/.cursor/system-instructions.md")" = "$S" ] && echo "both unchanged"`

**Expected Result:**
- Step 3: `exit 0`, `manifest rewritten`, the "its version is unknown" notice, and:
  ```
  ⚡ Preserved: rules/writ.mdc (no baseline, assuming modified)
  ⚡ Preserved: system-instructions.md (no baseline, assuming modified)
  ```
- Step 4: `exit 0` and the same two Preserved lines.
- Step 5: `both unchanged`.

**Status:** [x] Pass  [ ] Fail

**Notes:** Iteration 1 overwrote both files here while printing the "preserved" notice. A Cursor project with no manifest at all still gets both units updated, as before.

agent-run 2026-10-21 @ b850e66: step 3 `exit 0`, `manifest rewritten`, notice, both `⚡ Preserved: … (no baseline, assuming modified)` lines; step 4 `exit 0`, same two lines; `both unchanged`.

---

### Scenario 38: A legacy run with nothing to apply stays legacy and repeats the notice

**Source:** Experience Design (State: legacy manifest, version not found) — Story 5; drift DEV-008 (accepted)
**Feature:** none
**Verification:** human — no recipe
**Automated Test:** none — manual only (the tests always force a manifest rewrite)

**Preconditions:**
- Story 5 setup run.

**Steps:**
1. `PE="$W/legacy-idle"; cp -R "$W/base-claude" "$PE"; ME="$PE/.claude/.writ-manifest"; make_legacy "$ME" unknown; cp "$SRC/commands/zz-new.md" "$PE/.claude/commands/zz-new.md"`
2. `for i in 1 2; do upd "$PE" claude > "$W/e$i.txt" 2>&1; echo "run $i exit $?"; grep -E 'predates|Already' "$W/e$i.txt"; grep -c '^# baselines: shipped$' "$ME"; done`

**Expected Result:**
- Each run: `exit 0`, the "its version is unknown" notice, `✅ Already up to date! (<version>)`, and `0` (no header written).
- Nothing was removed or overwritten.

**Status:** [x] Pass  [ ] Fail

**Notes:** The repair and notice repeat until a run has something to apply and rewrites the manifest. Safe; the only cost is the repeated notice.

agent-run 2026-10-21 @ b850e66: runs 1 and 2 each `exit 0`, the notice, `✅ Already up to date! (b2bf01e)`, `0`; full-tree hash compare after both runs showed no change.

---

### Scenario 39: A shallow clone fetches history once and then repairs like a full clone

**Source:** Acceptance Criteria — Story 5 (AC-5.3, shallow clone); Shadow Path (Legacy manifest upgrade — upstream: `--unshallow`)
**Feature:** none
**Verification:** human — no recipe
**Automated Test:** `scripts/tests/test_update_legacy_manifest.sh` (case C, including the dry run)

**Preconditions:**
- Story 5 setup run. `$VA` is older than the source tip, so a `--depth 1` clone of `file://$SRC` does not contain it.

**Steps:**
1. `PS="$W/legacy-shallow"; cp -R "$W/base-claude" "$PS"; MS="$PS/.claude/.writ-manifest"; make_legacy "$MS" "$VA"; add_user_files "$PS" .claude; customize_status "$PS"`
2. Dry run: `cp "$MS" "$W/ms.before"; UPSTREAM="file://$SRC" upd "$PS" claude --dry-run > "$W/sd.txt" 2>&1; echo "exit $?"; cmp "$MS" "$W/ms.before" && echo "manifest byte-identical"; grep -c predates "$W/sd.txt"`
3. `UPSTREAM="file://$SRC" upd "$PS" claude > "$W/s1.txt" 2>&1; echo "exit $?"; rewritten "$MS"; grep -E 'Removed|predates|status\.md' "$W/s1.txt"`
4. `user_files_same "$PS" .claude; grep -c '^# baselines: shipped$' "$MS"`

**Expected Result:**
- Step 2: `exit 0`, `manifest byte-identical`, `0` (no notice: the version resolved).
- Step 3: `exit 0`, `manifest rewritten`, the three `🗑  Removed:` lines from Scenario 32, `⚡ Preserved: commands/status.md (local modifications)`, and no notice.
- Step 4: `user files unchanged`, `no line for any user file`, `1`.

**Status:** [x] Pass  [ ] Fail

**Notes:** `WRIT_REPO` must be a `file://` URL here. Git ignores `--depth` for a plain local path, so a plain path is never shallow.

agent-run 2026-10-21 @ b850e66: dry run `exit 0`, `manifest byte-identical`, `0`; real run `exit 0`, `manifest rewritten`, the three Removed lines, `⚡ Preserved: commands/status.md (local modifications)`, no notice; `user files unchanged`, `no line for any user file`, `1`.

---

### Scenario 40: A legacy manifest with nothing stale is only repaired

**Source:** Shadow Path (Legacy manifest upgrade — empty input: no stale paths) — Story 5
**Feature:** none
**Verification:** human — no recipe
**Automated Test:** none — manual only

**Preconditions:**
- Story 5 setup run (source B committed).

**Steps:**
1. `PR="$W/legacy-clean"; inst "$PR" claude > /dev/null 2>&1; MR="$PR/.claude/.writ-manifest"; make_legacy "$MR" "$(git -C "$SRC" log -1 --format=%h)"; add_user_files "$PR" .claude`
2. `bump; upd "$PR" claude > "$W/r.txt" 2>&1; echo "exit $?"; rewritten "$MR"; grep -E 'Removed|Stale|predates' "$W/r.txt" || echo "no stale, removal, or notice lines"`
3. `user_files_same "$PR" .claude; grep -c '^# baselines: shipped$' "$MR"`

**Expected Result:**
- Step 2: `exit 0`, `manifest rewritten`, `no stale, removal, or notice lines`.
- Step 3: `user files unchanged`, `no line for any user file`, `1`.

**Status:** [x] Pass  [ ] Fail

**Notes:** agent-run 2026-10-21 @ b850e66: `exit 0`, `manifest rewritten`, `no stale, removal, or notice lines`; `user files unchanged`, `no line for any user file`, `1`.

---

### Scenario 41: On Codex, an unmodified stale skill is removed from `.agents/skills`

**Source:** Acceptance Criteria — Story 5 (AC-5.4); Error Map (Stale removal: Codex skill path wrong); Experience Design (State: Codex update, retired skill)
**Feature:** none
**Verification:** human — no recipe
**Automated Test:** `scripts/tests/test_update_legacy_manifest.sh` (case D)

**Preconditions:**
- Story 5 setup run. `base-codex` has a header manifest (no legacy edit here).

**Steps:**
1. `PK="$W/codex-skills"; cp -R "$W/base-codex" "$PK"; MK="$PK/.codex/.writ-manifest"; ls "$PK/.agents/skills/zz-old/SKILL.md"`
2. `upd "$PK" codex > "$W/k1.txt" 2>&1; echo "exit $?"; grep 'Removed' "$W/k1.txt"`
3. For every Removed path, check it is gone: `grep -o 'Removed: .*' "$W/k1.txt" | sed 's/Removed: //' | while read -r p; do case "$p" in skills/*) f="$PK/.agents/$p";; *) f="$PK/.codex/$p";; esac; [ -e "$f" ] && echo "STILL ON DISK: $f" || echo "gone: $p"; done`

**Expected Result:**
- Step 2: `exit 0`, including `🗑  Removed: skills/zz-old/SKILL.md` and `🗑  Removed: skills/zz-locked/SKILL.md`.
- Step 3: `gone:` for every path; no `STILL ON DISK` line.

**Status:** [x] Pass  [ ] Fail

**Notes:** Before the fix, update printed `🗑  Removed:` for a Codex skill but looked under `.codex/skills`, so the file stayed in `.agents/skills`. Skill sidecar files other than `SKILL.md` stay behind (residual risk, unchanged).

agent-run 2026-10-21 @ b850e66: `exit 0`, Removed lines for `commands/zz-retired.md`, `skills/zz-locked/SKILL.md`, `skills/zz-old/SKILL.md`; `gone:` for all three, no `STILL ON DISK`.

---

### Scenario 42: A stale file that cannot be deleted gets no Removed line and is retried next run

**Source:** Error Map (Stale removal: `rm` fails) — Story 5; drift DEV-006
**Feature:** none
**Verification:** human — no recipe
**Automated Test:** `scripts/tests/test_update_legacy_manifest.sh` (case D, `chmod 555` skill)

**Preconditions:**
- Story 5 setup run. Not run as root (root ignores the permission).

**Steps:**
1. `PL="$W/codex-locked"; cp -R "$W/base-codex" "$PL"; ML="$PL/.codex/.writ-manifest"; chmod 555 "$PL/.agents/skills/zz-locked"`
2. `upd "$PL" codex > "$W/l1.txt" 2>&1; echo "exit $?"; grep -E 'Removed' "$W/l1.txt"; ls "$PL/.agents/skills/zz-locked/SKILL.md"; grep '  skills/zz-' "$ML"`
3. `chmod 755 "$PL/.agents/skills/zz-locked"; upd "$PL" codex > "$W/l2.txt" 2>&1; echo "exit $?"; grep -E 'Removed' "$W/l2.txt"; ls "$PL/.agents/skills/zz-locked/SKILL.md" 2>&1 | sed 's/.*: //'; grep -c '  skills/zz-' "$ML"`

**Expected Result:**
- Step 2: `exit 0`; `🗑  Removed: commands/zz-retired.md` and `🗑  Removed: skills/zz-old/SKILL.md`, but no Removed line for `zz-locked`; the `zz-locked` file is still listed; the manifest still has a `skills/zz-locked/SKILL.md` line.
- Step 3: `exit 0`, `🗑  Removed: skills/zz-locked/SKILL.md`, `No such file or directory`, `0`.

**Status:** [x] Pass  [ ] Fail

**Notes:** agent-run 2026-10-21 @ b850e66: step 2 `exit 0`, Removed for `commands/zz-retired.md` and `skills/zz-old/SKILL.md` only, zz-locked file still listed, manifest keeps its `skills/zz-locked/SKILL.md` line; step 3 `exit 0`, `🗑  Removed: skills/zz-locked/SKILL.md`, `No such file or directory`, `0`.

---

### Scenario 43: The legacy test fails on the pre-fix script and passes now; Step 3 documents legacy handling

**Source:** Acceptance Criteria — Story 5 (AC-5.5; AC-5.3 doc sentence)
**Feature:** none
**Verification:** human — no recipe
**Automated Test:** partial — CI runs the test, including its check for the Step 3 sentence; the pre-fix failure (step 2) is checked only by hand

**Preconditions:**
- Setup block pasted. Outside any sandbox. About 2 min 20 s per run.

**Steps:**
1. `bash "$REPO/scripts/tests/test_update_legacy_manifest.sh"; echo "exit $?"`
2. `X="$W/prefix-5"; mkdir -p "$X" && git -C "$REPO" archive 6f24327 | tar -x -C "$X" && cp "$REPO/scripts/tests/test_update_legacy_manifest.sh" "$X/scripts/tests/" && bash "$X/scripts/tests/test_update_legacy_manifest.sh"; echo "exit $?"`
3. Open `commands/update-writ.md`, Step 3, and find the `**Legacy manifests:**` paragraph.

**Expected Result:**
- Step 1: `PASS test_update_legacy_manifest`, `exit 0`.
- Step 2 (recorded in What Was Built): starts with `FAIL: A update 1: user file .writ/docs/tech-stack.md was removed.`, `exit 1`.
- Step 3: one sentence says a manifest without `# baselines: shipped` has its baselines rebuilt from upstream at its `# version:` (fetching full history once if needed), paths upstream did not have are dropped, and if the commit cannot be found only the Codex config line is kept, so differing files are preserved and nothing is removed.

**Status:** [x] Pass  [ ] Fail

**Notes:** `6f24327` is the lane head after Story 4, before Story 5.

agent-run 2026-10-21 @ b850e66: step 1 `PASS test_update_legacy_manifest`, exit 0; step 2 starts `FAIL: A update 1: user file .writ/docs/tech-stack.md was removed.`, exit 1; step 3 the `**Legacy manifests:**` paragraph states all four points (rebuild at `# version:`, fetch full history once, drop paths upstream lacked, unresolved → keep only the Codex config line, preserve, remove nothing).

---

## Automated vs. Manual

| Kind | Scenarios | Count |
|---|---|---|
| Asserted by a committed test (CI runs it) | 1, 2, 3, 4, 9, 10, 11, 13, 14, 15, 16, 17, 18, 23, 24, 25, 26, 32, 33, 34, 36, 37, 39, 41, 42 | 25 |
| Partly automated (test passes in CI; pre-fix re-proof, doc reading, or extra inputs by hand) | 12, 19, 27, 28, 35, 43 | 6 |
| Manual only | 5, 6, 7, 8, 20, 21, 22, 29, 30, 31, 38, 40 | 12 |

Scenarios 7 and 8 need GitHub Actions. Scenario 7 is Story 1's open Definition of Done item and cannot pass until the phase PR's first CI run.

## Not Covered by This Plan

- **Paths containing spaces.** Out of scope in the spec (`manifest_files` splits on whitespace).
- **Legacy manifest written by `unlink.sh`.** `unlink.sh` needs a linked install and fetches from GitHub, so it is not reproduced here. Its manifests lack the header and take the same legacy path as Scenarios 32–40 (evaluator probe in Story 5).
- **Residual risks listed in the technical spec** (re-install over a legacy manifest, retired entries dropped by install over a legacy manifest, stale-skill sidecars). These are known limits, not regressions.

## Pending Stories

None. All five stories are Completed ✅.
