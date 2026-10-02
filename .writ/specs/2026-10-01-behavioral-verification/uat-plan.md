# UAT Plan: Behavioral Verification

> **Generated:** 2026-10-01
> **Spec:** `.writ/specs/2026-10-01-behavioral-verification/`
> **Stories Covered:** 5 of 5 completed
> **Total Scenarios:** 35 (0 machine, 35 human)
> **Verification recipe:** skipped. Writ is a markdown and scripts repo with no running app (no dev or start command, no readiness URL), and this spec forbids Writ from shipping `.writ/docs/app-verification.md` (Story 1's guard test). So every scenario is `human — no recipe`.

## How to Use This Plan

1. Work through scenarios in order (they're grouped by story, ordered by priority)
2. For each scenario, follow the steps exactly as written
3. Mark Pass or Fail — add notes for any unexpected behavior
4. Scenarios marked Fail should be filed as issues or fed back to the spec
5. A feature passes UAT when all scenarios pass (or failures are accepted as known limitations)

**Running the commands:**
- Run every command from the repository root, `/Users/asellke/Projects/writ`. The fixture recipes name repo-relative paths.
- The fixture recipes use port **8765**. Before any `run` scenario, `lsof -nP -iTCP:8765 -sTCP:LISTEN` must print nothing. If something is listening, `run` correctly refuses with `instance_already_running`, which is Scenario 19's expected result and the wrong result anywhere else.
- `F` is shorthand for the fixture folder. Set it once per terminal: `F=scripts/tests/fixtures/app-verify`.
- Run outside any agent sandbox. The `run` commands start a local server on 127.0.0.1, and `eval.sh` runs `git init` in a temp folder.
- Scenarios 7, 8, 9, 11, 13, 14 and 26 need a **separate scratch project** with a small test suite and a start command. Never run them in the Writ repo: choosing *save* here would create the forbidden `.writ/docs/app-verification.md`.

## Coverage Summary

| Story | Status | Scenarios | Source Breakdown |
|-------|--------|-----------|-----------------|
| Story 1: Recipe format, validator, and product amendments | ✅ Covered | 6 | AC: 5, Errors: 1, Shadow: 0, Edge: 0 |
| Story 2: `/create-uat-plan` drafts the recipe and binds scenarios | ✅ Covered | 8 | AC: 6, Errors: 1, Shadow: 1, Edge: 0 |
| Story 3: Run script and fixture app | ✅ Covered | 10 | AC: 7, Errors: 2, Shadow: 0, Edge: 1 |
| Story 4: Gate 4.5 becomes behavioral verification | ✅ Covered | 7 | AC: 6, Errors: 0, Shadow: 1, Edge: 0 |
| Story 5: `exit-criteria.py` evidence check, mutation, eval check | ✅ Covered | 4 | AC: 4, Errors: 0, Shadow: 0, Edge: 0 |

Deduplication: the Error Map rows *Read recipe* and *Validate recipe* are listed in the context hints of Stories 1 through 4, but each appears once here, under Story 1. The Gate 4.5 shadow cells *app never ready* and *no mapped features* show up as script behavior under Story 3 (Scenarios 15 and 21), and the gate's reaction to them shows up under Story 4 (Scenarios 25 and 31). The spec's Experience Design scenarios (entry point, moment of truth, state catalog) are folded into Scenarios 7, 16, and 32 rather than repeated.

---

## Story 1: Recipe Format, Validator, and Product Amendments

### Scenario 1: The recipe format doc defines the full grammar

**Source:** Acceptance Criteria — Story 1 (AC-1.1)
**Feature:** none
**Verification:** human — no recipe

**Preconditions:**
- None

**Steps:**
1. Open `.writ/docs/app-verification-format.md`.
2. Find the list of required sections.
3. Find the Feature Map, Patterns, Safety, and Validator Findings sections.
4. Read the Worked Example section.

**Expected Result:**
- Exactly six recipe sections are required: Launch, Safety, Login, Feature Map, Evidence, Cleanup.
- Settings are `- **Key:** value` lines.
- The Feature Map is a table with the columns `ID | Feature | Paths | Check`. IDs are kebab-case and unique. `Check` is either a backticked command or `human-only: <reason>`.
- `Allowed`, `Never`, and `Paths` are described as shell-style globs.
- The doc says recipes store only variable names and patterns, never secret values.
- It includes one worked example and points to the fixture recipe under `scripts/tests/fixtures/app-verify/` as a second example.

**Implementation Reference:** Story 1 — `.writ/docs/app-verification-format.md`

**Status:** [ ] Pass  [ ] Fail

**Notes:**

---

### Scenario 2: A valid recipe validates cleanly, in text and JSON

**Source:** Acceptance Criteria — Story 1 (AC-1.2)
**Feature:** none
**Verification:** human — no recipe

**Preconditions:**
- `F=scripts/tests/fixtures/app-verify`

**Steps:**
1. Run `python3 scripts/app-verify.py validate --recipe $F/recipe-pass.md; echo "exit=$?"`
2. Run `python3 scripts/app-verify.py validate --recipe $F/recipe-pass.md --json; echo "exit=$?"`

**Expected Result:**
- Step 1 prints exactly `app-verify: recipe valid — 2 features (1 check, 1 human-only)` then `exit=0`.
- Step 2 prints the same line, then one JSON object containing `"schema": "app-verify-v1"`, `"verdict": "valid"`, `"findings": []`, and `"features": ["home", "oauth"]`, then `exit=0`.

**Implementation Reference:** Story 1 — `scripts/app-verify.py` (`validate`)

**Status:** [ ] Pass  [ ] Fail

**Notes:**

---

### Scenario 3: A broken recipe names its first defect and exits 1

**Source:** Acceptance Criteria — Story 1 (AC-1.3); also Error Map row *Validate recipe*
**Feature:** none
**Verification:** human — no recipe

**Preconditions:**
- `F=scripts/tests/fixtures/app-verify`
- `B=$(mktemp -d) && sed 's/^## Safety$/## Safetee/' $F/recipe-pass.md > $B/bad.md` (renames the Safety section so it is missing)

**Steps:**
1. Run `python3 scripts/app-verify.py validate --recipe $B/bad.md; echo "exit=$?"`
2. Run `uv run --python 3.9 pytest -q scripts/tests/test_app_verify.py` to cover the other finding codes, which each have a fixture in the suite.

**Expected Result:**
- Step 1 prints `app-verify: recipe invalid — missing_section (Safety)` then `exit=1`.
- Step 2 reports `71 passed`. That count includes one test per finding code (`missing_section`, `missing_launch_command`, `missing_ready`, `missing_safety`, `bad_feature_row`, `duplicate_feature_id`, `bad_feature_id`, `secret_value`, `bad_timeout`).

**Status:** [ ] Pass  [ ] Fail

**Notes:**

---

### Scenario 4: Writ itself ships no project recipe

**Source:** Acceptance Criteria — Story 1 (AC-1.4)
**Feature:** none
**Verification:** human — no recipe

**Preconditions:**
- None

**Steps:**
1. Run `ls .writ/docs/app-verification.md`
2. Run `ls .writ/docs/app-verification-format.md`

**Expected Result:**
- Step 1 prints `No such file or directory`. The format doc ships to projects, but a project-authored recipe must never come from Writ.
- Step 2 lists the file.

**Status:** [ ] Pass  [ ] Fail

**Notes:**

---

### Scenario 5: ADR-028 and the product docs describe the recipe design

**Source:** Acceptance Criteria — Story 1 (AC-1.5)
**Feature:** none
**Verification:** human — no recipe

**Preconditions:**
- None

**Steps:**
1. Open `.writ/decision-records/adr-028-behavioral-verification-and-cross-family-panels.md` and read Decisions 1 and 2, plus the runtime boundary paragraph.
2. Open `.writ/product/roadmap.md` and read the section `## Phase 12: Behavioral Verification`.
3. Search the Phase 12 lines in `.writ/product/mission.md` and `.writ/product/mission-lite.md`.
4. Run `rg -n "verify-<app>" .writ/product .writ/decision-records`

**Expected Result:**
- ADR-028 names the recipe at `.writ/docs/app-verification.md`, drafted by `/create-uat-plan`. It records that Features 1 and 2 merged. It states that a script which launches only commands the recipe names, and keeps no state between runs, is not a Writ runtime.
- Roadmap Phase 12 has one merged behavioral-verification feature, its success criterion is a fixture app (not yuss.app), and it says nothing about `/initialize` generating the recipe.
- The mission files agree with the roadmap.
- Every `verify-<app>` hit is a historical or explicitly superseded mention.

**Implementation Reference:** Story 1 — ADR-028, `roadmap.md`, `mission.md`, `mission-lite.md`

**Status:** [ ] Pass  [ ] Fail

**Notes:**

---

### Scenario 6: A missing recipe is reported as unverifiable, not invalid

**Source:** Error Map (*Read recipe* — file missing) — Story 1
**Feature:** none
**Verification:** human — no recipe

**Preconditions:**
- None

**Steps:**
1. Run `python3 scripts/app-verify.py validate --recipe /nonexistent.md; echo "exit=$?"`

**Expected Result:**
- Prints `app-verify: unverifiable (no_recipe)` then `exit=2`. Exit 2 (nothing to check) is distinct from exit 1 (recipe has defects).

**Status:** [ ] Pass  [ ] Fail

**Notes:**

---

## Story 2: `/create-uat-plan` Drafts the Recipe and Binds Scenarios to Feature IDs

### Scenario 7: First UAT plan in a project drafts a recipe and asks once

**Source:** Acceptance Criteria — Story 2 (AC-2.1); Experience Design entry point
**Feature:** none
**Verification:** human — no recipe

**Preconditions:**
- A scratch project, not the Writ repo, with Writ installed, a pytest suite, a start command (for example `python3 app.py` serving on a port), and one spec with at least one completed story.
- No `.writ/docs/app-verification.md` in the scratch project.

**Steps:**
1. In the scratch project, run `/create-uat-plan <spec-folder>`.
2. Read the draft recipe the command shows.
3. Look at the question that follows.

**Expected Result:**
- The draft has the six sections and a Launch command taken from the project's start command.
- Features that have an existing test get a backticked `Check` command. Every other feature reads `human-only: no check yet`.
- Exactly one question appears, with three options: Save, Edit the draft first, and Skip. Only **Save** is marked `(Recommended)`, because a launch command was detected.
- The command never writes a new test file or check script.

**Implementation Reference:** Story 2 — `commands/create-uat-plan.md` Step 1.3

**Status:** [ ] Pass  [ ] Fail

**Notes:**

---

### Scenario 8: An existing recipe gets no question, and `--check` changes nothing

**Source:** Acceptance Criteria — Story 2 (AC-2.1)
**Feature:** none
**Verification:** human — no recipe

**Preconditions:**
- The scratch project from Scenario 7, with the recipe saved to `.writ/docs/app-verification.md`.

**Steps:**
1. Run `git status --porcelain` and note the output.
2. Run `/create-uat-plan <spec-folder> --check`.
3. Run `git status --porcelain` again, and check whether an `evidence/` folder appeared in the spec.
4. Run `/create-uat-plan <spec-folder>`.

**Expected Result:**
- Step 2 shows a scenario-count report, asks no question, writes no file, and starts no app.
- Step 3 output is identical to step 1, and no new `evidence/` folder exists.
- Step 4 shows no draft and asks no recipe question. It validates the existing recipe and goes straight to scenario generation.

**Status:** [ ] Pass  [ ] Fail

**Notes:**

---

### Scenario 9: An invalid existing recipe is left alone, and every scenario falls back to human

**Source:** Acceptance Criteria — Story 2 (AC-2.2)
**Feature:** none
**Verification:** human — no recipe

**Preconditions:**
- The scratch project, with the `## Safety` heading in `.writ/docs/app-verification.md` renamed to `## Safetee`. Commit that edit so you can diff against it.

**Steps:**
1. Run `/create-uat-plan <spec-folder>`.
2. Run `git diff .writ/docs/app-verification.md`.
3. Open the generated `uat-plan.md`.

**Expected Result:**
- The command prints `app-verify: recipe invalid — missing_section (Safety)`.
- Step 2 shows no diff, because the command does not rewrite the recipe.
- Every scenario reads `**Feature:** none` and `**Verification:** human — recipe invalid`.
- The final report tells you to fix the recipe and run the command again.

**Status:** [ ] Pass  [ ] Fail

**Notes:**

---

### Scenario 10: Every scenario in a populated plan carries Feature and Verification lines

**Source:** Acceptance Criteria — Story 2 (AC-2.3); Shadow Path (`/create-uat-plan`, *Developer skips → today's human plan*)
**Feature:** none
**Verification:** human — no recipe

**Preconditions:**
- None. This plan is a live instance of the skip path.

**Steps:**
1. Run `rg -c '^### Scenario ' .writ/specs/2026-10-01-behavioral-verification/uat-plan.md`
2. Run `rg -c '^\*\*Feature:\*\* none$' .writ/specs/2026-10-01-behavioral-verification/uat-plan.md`
3. Run `rg -c '^\*\*Verification:\*\* human — no recipe$' .writ/specs/2026-10-01-behavioral-verification/uat-plan.md`
4. Run `python3 scripts/exit-criteria.py check-uat --spec .writ/specs/2026-10-01-behavioral-verification; echo "exit=$?"`

**Expected Result:**
- Steps 1, 2 and 3 each print `35`.
- Step 4 prints a JSON object with `"verdict": "met"` and `"evidence": "no machine scenarios: 2026-10-01-behavioral-verification"`, then `exit=0`.

**Status:** [ ] Pass  [ ] Fail

**Notes:**

---

### Scenario 11: Machine scenarios are ticked only from the script's result

**Source:** Acceptance Criteria — Story 2 (AC-2.3, AC-2.4); Experience Design moment of truth
**Feature:** none
**Verification:** human — no recipe

**Preconditions:**
- The scratch project with a valid saved recipe. One feature row has a `Check` whose `Paths` match a completed story's changed files, and a second row is `human-only: <reason>` with matching paths.

**Steps:**
1. Run `/create-uat-plan <spec-folder>`.
2. Open `uat-plan.md` and find the scenarios bound to each feature.
3. Open `<spec-folder>/evidence/uat/<id>/result.json` for the machine feature.
4. Break the check (make the test fail), run `/create-uat-plan <spec-folder>` again, and reopen the plan.

**Expected Result:**
- Step 2: the machine scenario reads `**Verification:** machine — evidence: evidence/uat/<id>/result.json` with Status `[x] Pass`. The human-only scenario reads `**Verification:** human — <reason>` with Status unticked.
- Step 3: `"verdict": "pass"`.
- The report shows one `app-verify:` summary line and the count of machine and human scenarios. The app launched once for all machine features, not once per feature.
- Step 4: the same machine scenario is now `[x] Fail`. It is not rewritten as human.

**Status:** [ ] Pass  [ ] Fail

**Notes:**

---

### Scenario 12: The command text is pinned by its hook test and stays under budget

**Source:** Acceptance Criteria — Story 2 (AC-2.5)
**Feature:** none
**Verification:** human — no recipe

**Preconditions:**
- None

**Steps:**
1. Run `bash scripts/tests/test_uat_plan_verification_hooks.sh; echo "exit=$?"`
2. Run `wc -c commands/create-uat-plan.md`
3. Run `ls commands/create-uat-plan.lean.md`

**Expected Result:**
- Step 1 ends with `All create-uat-plan verification hook assertions passed.` then `exit=0`. The second-to-last line reports `21399 bytes < 24960, no twin, no recipe`.
- Step 2 prints `21399 commands/create-uat-plan.md`.
- Step 3 prints `No such file or directory`.

**Status:** [ ] Pass  [ ] Fail

**Notes:**

---

### Scenario 13: A project with no test harness gets an all-human draft

**Source:** Error Map (`/create-uat-plan` draft — no harness detected) — Story 2
**Feature:** none
**Verification:** human — no recipe

**Preconditions:**
- A scratch project with a start command but no test harness (no Playwright, Cypress, pytest, or `package.json` test script), no recipe, and a spec with one completed story.

**Steps:**
1. Run `/create-uat-plan <spec-folder>`.
2. Read the draft's Feature Map.
3. Choose **Skip** at the question.

**Expected Result:**
- The command notes `ℹ️ No test harness found`.
- Every Feature Map row reads `human-only: no check yet`.
- After Skip, no `.writ/docs/app-verification.md` exists, and `uat-plan.md` is fully populated. Every scenario is `**Verification:** human — no recipe`, and the plan is not a stub.

**Status:** [ ] Pass  [ ] Fail

**Notes:**

---

### Scenario 14: A refused safety check turns machine scenarios into human ones

**Source:** Shadow Path (`/create-uat-plan`, upstream error: safety refused) — Story 2
**Feature:** none
**Verification:** human — no recipe

**Preconditions:**
- The scratch project's recipe has a `- **Variable:**` entry, for example `DATABASE_URL`, with `- **Allowed:** *dev*`. In your shell, set that variable to a value that does not match, for example `export DATABASE_URL=postgres://prod-host/db`.

**Steps:**
1. Run `/create-uat-plan <spec-folder>`.
2. Open `uat-plan.md`.
3. Check whether the app process started (for example `lsof -nP -iTCP:<port> -sTCP:LISTEN`, run during and after the command).

**Expected Result:**
- The command prints one line starting `app-verify: refused (`, which names the variable but not its value.
- Scenarios that would have been machine scenarios read `**Verification:** human — refused`, with Status unticked.
- The app never started.

**Status:** [ ] Pass  [ ] Fail

**Notes:**

---

## Story 3: Run Script and Fixture App

### Scenario 15: `touched` maps changed files to features that have a check

**Source:** Acceptance Criteria — Story 3 (AC-3.1)
**Feature:** none
**Verification:** human — no recipe

**Preconditions:**
- `F=scripts/tests/fixtures/app-verify`

**Steps:**
1. Run `python3 scripts/app-verify.py touched --recipe $F/recipe-pass.md --changed $F/app.py; echo "exit=$?"`
2. Run `python3 scripts/app-verify.py touched --recipe $F/recipe-pass.md --changed README.md; echo "exit=$?"`
3. Run `python3 scripts/app-verify.py touched --recipe $F/recipe-pass.md --changed $F/auth/login.py; echo "exit=$?"` (this path matches only the human-only `oauth` row)
4. Run `python3 scripts/app-verify.py touched --recipe /nonexistent.md --changed x; echo "exit=$?"`

**Expected Result:**
- Step 1 prints `home` then `exit=0`.
- Steps 2 and 3 each print `app-verify: no mapped features touched by this story` then `exit=0`. The human-only row is never printed.
- Step 4 prints `app-verify: unverifiable (no_recipe)` then `exit=2`.

**Status:** [ ] Pass  [ ] Fail

**Notes:**

---

### Scenario 16: A passing run writes full evidence

**Source:** Acceptance Criteria — Story 3 (AC-3.3); Experience Design moment of truth
**Feature:** none
**Verification:** human — no recipe

**Preconditions:**
- `F=scripts/tests/fixtures/app-verify; T=$(mktemp -d)`
- Port 8765 is free.

**Steps:**
1. Run `python3 scripts/app-verify.py run --recipe $F/recipe-pass.md --spec $T --run-label uat; echo "exit=$?"`
2. Run `ls $T/evidence/uat $T/evidence/uat/home $T/evidence/uat/_launch`
3. Run `cat $T/evidence/uat/home/result.json`
4. Run `python3 scripts/app-verify.py run --recipe $F/recipe-pass.md --spec $T --run-label only-home --features home; echo "exit=$?"`

**Expected Result:**
- Step 1 prints `app-verify: 1/1 pass — evidence/uat/; human-only — oauth (third-party consent screen)` then `exit=0`.
- Step 2 shows a `home/` and a `_launch/` folder. `home/` holds `result.json`, `stdout.log`, `stderr.log`, and `home-body.txt` (saved by the check itself). `_launch/` holds `stdout.log` and `stderr.log`.
- Step 3 shows `"schema": "app-verify-result-v1"`, `"feature": "home"`, `"exit_code": 0`, `"verdict": "pass"`, plus `command`, `started_at`, `ended_at`, `duration_s`, a 64-character `recipe_sha256`, `truncated` (`stdout` and `stderr` both `false`), and `artifacts: []`.
- Step 4 prints `app-verify: 1/1 pass — evidence/only-home/` with no human-only clause, then `exit=0`.

**Implementation Reference:** Story 3 — `scripts/app-verify.py` (`run`), `scripts/tests/fixtures/app-verify/app.py`, `check_home.py`

**Status:** [ ] Pass  [ ] Fail

**Notes:**

---

### Scenario 17: A failing check fails the run, with a recorded verdict

**Source:** Acceptance Criteria — Story 3 (AC-3.4); Error Map row *Run check — non-zero exit*
**Feature:** none
**Verification:** human — no recipe

**Preconditions:**
- `F=scripts/tests/fixtures/app-verify; T=$(mktemp -d)`
- Port 8765 is free.

**Steps:**
1. Run `python3 scripts/app-verify.py run --recipe $F/recipe-fail.md --spec $T --run-label fail; echo "exit=$?"`
2. Run `python3 -c "import json;print(json.load(open('$T/evidence/fail/broken/result.json'))['verdict'])"`
3. Run `python3 -c "import json;print(json.load(open('$T/evidence/fail/home/result.json'))['verdict'])"`

**Expected Result:**
- Step 1 prints `app-verify: 1/2 fail — broken (exit 1) — evidence/fail/broken/` then `exit=1`.
- Step 2 prints `fail`.
- Step 3 prints `pass`. One failing feature does not hide the other's result.

**Status:** [ ] Pass  [ ] Fail

**Notes:**

---

### Scenario 18: A disallowed database target refuses before anything launches

**Source:** Acceptance Criteria — Story 3 (AC-3.2); Error Map rows *Resolve safety variable*, *Read env file*
**Feature:** none
**Verification:** human — no recipe

**Preconditions:**
- `F=scripts/tests/fixtures/app-verify; T=$(mktemp -d)`
- `$F/fixture.env` sets `APP_VERIFY_FIXTURE_DB=fixture-prod-host`. The recipe allows `*fixture-dev*` and never `*prod*`.
- `APP_VERIFY_FIXTURE_DB` is not set in your shell.

**Steps:**
1. Run `python3 scripts/app-verify.py run --recipe $F/recipe-safety-refused.md --spec $T --run-label refused; echo "exit=$?"`
2. Run `ls $T/evidence/refused`
3. Run `APP_VERIFY_FIXTURE_DB=fixture-dev-host python3 scripts/app-verify.py run --recipe $F/recipe-safety-refused.md --spec $T --run-label allowed; echo "exit=$?"`
4. Run `git status --porcelain $F/fixture.env`

**Expected Result:**
- Step 1 prints `app-verify: refused (APP_VERIFY_FIXTURE_DB matches a Never pattern)` then `exit=2`. The line names the variable but not its value.
- Step 2 prints `No such file or directory`, because nothing launched and no evidence was written.
- Step 3 prints `app-verify: 1/1 pass — evidence/allowed/` then `exit=0`. A value in the process environment wins over the env file.
- Step 4 prints nothing. The env file is read but never written.

**Status:** [ ] Pass  [ ] Fail

**Notes:**

---

### Scenario 19: A second run on a busy port refuses rather than reusing an unknown server

**Source:** Acceptance Criteria — Story 3 (AC-3.2); Error Map row *Pre-launch probe*; Edge Case *two runs at once on one port*
**Feature:** none
**Verification:** human — no recipe

**Preconditions:**
- `F=scripts/tests/fixtures/app-verify; T=$(mktemp -d)`

**Steps:**
1. In a second terminal at the repo root, run `PORT=8765 python3 scripts/tests/fixtures/app-verify/app.py` and leave it running.
2. In the first terminal, run `python3 scripts/app-verify.py run --recipe $F/recipe-pass.md --spec $T --run-label dup; echo "exit=$?"`
3. Check that the server in the second terminal is still running, then stop it with Ctrl-C.

**Expected Result:**
- Step 2 prints `app-verify: refused (instance_already_running)` then `exit=2`.
- Step 3: the server you started was not stopped by the script. It only stops processes it started itself.

**Status:** [ ] Pass  [ ] Fail

**Notes:**

---

### Scenario 20: Running only human-only or unknown features does nothing and says why

**Source:** Acceptance Criteria — Story 3 (AC-3.5)
**Feature:** none
**Verification:** human — no recipe

**Preconditions:**
- `F=scripts/tests/fixtures/app-verify; T=$(mktemp -d)`

**Steps:**
1. Run `python3 scripts/app-verify.py run --recipe $F/recipe-pass.md --spec $T --run-label ho --features oauth; echo "exit=$?"`
2. Run `python3 scripts/app-verify.py run --recipe $F/recipe-pass.md --spec $T --run-label u --features nope; echo "exit=$?"`

**Expected Result:**
- Step 1 prints `app-verify: human-only — oauth (third-party consent screen)` then `exit=2`.
- Step 2 prints `app-verify: unverifiable (unknown_feature: nope)` then `exit=2`.

**Status:** [ ] Pass  [ ] Fail

**Notes:**

---

### Scenario 21: An app that never becomes ready fails the run, and its logs are kept

**Source:** Acceptance Criteria — Story 3 (AC-3.4); Error Map row *Readiness — timeout*
**Feature:** none
**Verification:** human — no recipe

**Preconditions:**
- `F=scripts/tests/fixtures/app-verify; T=$(mktemp -d)`
- Port 8765 is free. The not-ready recipe has a 2 s timeout.

**Steps:**
1. Run `python3 scripts/app-verify.py run --recipe $F/recipe-not-ready.md --spec $T --run-label nr; echo "exit=$?"`
2. Run `ls $T/evidence/nr $T/evidence/nr/_launch`

**Expected Result:**
- After about 2 seconds, step 1 prints `app-verify: fail (not_ready 2s) — evidence/nr/_launch/` then `exit=1`.
- Step 2 shows only `_launch/`, which holds `stdout.log` and `stderr.log`. No feature folder exists, because no check ran.

**Status:** [ ] Pass  [ ] Fail

**Notes:**

---

### Scenario 22: No fixture process survives any run

**Source:** Acceptance Criteria — Story 3 (AC-3.5); Error Map row *Cleanup*
**Feature:** none
**Verification:** human — no recipe

**Preconditions:**
- Scenarios 16, 17, 18, 20 and 21 have just been run. Scenario 19's manual server has been stopped.

**Steps:**
1. Run `pgrep -fl "app-verify/app.py" || echo "no fixture process"`
2. Run `lsof -nP -iTCP:8765 -sTCP:LISTEN || echo "port free"`

**Expected Result:**
- Step 1 prints `no fixture process`.
- Step 2 prints `port free`.

**Status:** [ ] Pass  [ ] Fail

**Notes:**

---

### Scenario 23: The remaining run-time failure rows are covered by the test suite

**Source:** Error Map rows *Launch — command exits immediately*, *Run check — timeout*, *Copy artifacts*, *Cleanup — process survives SIGTERM / failing After* — Story 3
**Feature:** none
**Verification:** human — no recipe

**Preconditions:**
- `uv` is installed.

**Steps:**
1. Run `uv run --python 3.9 pytest -q scripts/tests/test_app_verify.py -k "launch_exited or timeout or artifact or After or after or sigterm or SIGTERM or survive"`
2. Run `uv run --python 3.9 pytest -q scripts/tests/test_app_verify.py`
3. Run `pgrep -fl "app-verify/app.py" || echo "no fixture process"`

**Expected Result:**
- Step 1 selects at least one test and they all pass. The selected tests cover four things: a launch command that exits before the app is ready gives `fail (launch_exited <code>)` with its launch logs kept; a check that runs past its timeout gets verdict `fail (timeout)`; artifacts over 5 MB are recorded by path and missing ones are recorded as `missing`; and a failing `After` command is a note, not a fail.
- Step 2 reports `71 passed` on Python 3.9.
- Step 3 prints `no fixture process`.

**Status:** [ ] Pass  [ ] Fail

**Notes:**

---

### Scenario 24: Windows is refused cleanly rather than half-run

**Source:** Edge Case (*Windows*) — Story 3 (AC-3.2)
**Feature:** none
**Verification:** human — no recipe

**Preconditions:**
- `uv` is installed. On macOS this is checked through the test that patches the platform check.

**Steps:**
1. Run `uv run --python 3.9 pytest -q scripts/tests/test_app_verify.py -k unsupported_platform`
2. Run `rg -n "unsupported_platform" scripts/app-verify.py`

**Expected Result:**
- Step 1 selects at least one test, and it passes.
- Step 2 shows that a non-POSIX platform exits 2 with `unverifiable (unsupported_platform)` before anything launches.

**Status:** [ ] Pass  [ ] Fail

**Notes:**

---

## Story 4: Gate 4.5 Becomes Behavioral Verification

### Scenario 25: Gate 4.5 is a script with three exit-code outcomes and no question

**Source:** Acceptance Criteria — Story 4 (AC-4.1)
**Feature:** none
**Verification:** human — no recipe

**Preconditions:**
- None

**Steps:**
1. Open `commands/implement-story.md` and read `#### Gate 4.5: Behavioral Verification`.
2. Run `rg -n "app-verify.py touched|--run-label story-N" commands/implement-story.md commands/implement-story.lean.md`

**Expected Result:**
- The gate runs `app-verify.py touched` on the story's changed files, then `run … --run-label story-N --features <touched ids, comma-joined>`. It spawns no Task and asks no question.
- **exit 0** continues. **exit 1** (check, launch, or readiness failed) goes back to Gate 1 for recode on the shared review-loop cap.
- **exit 2** (no recipe, invalid recipe, or refused), or no touched IDs, relays one `app-verify:` line and continues. The story is **not** marked `⚠️ DEGRADED`.
- `--quick` skips the gate. Under `--review-only`, a fail ends the run with no recode.
- Step 2 finds both lines in both files.

**Implementation Reference:** Story 4 — `commands/implement-story.md`, `commands/implement-story.lean.md`

**Status:** [ ] Pass  [ ] Fail

**Notes:**

---

### Scenario 26: Gate 4.5 runs a story's checks in a real project

**Source:** Acceptance Criteria — Story 4 (AC-4.1); User Journey step 3
**Feature:** none
**Verification:** human — no recipe

**Preconditions:**
- The scratch project, with a valid recipe whose feature row's `Paths` cover a file the next story will change, and a spec with a Not Started story touching that file.

**Steps:**
1. Run `/implement-story <story>` on the default pipeline.
2. When it finishes, look in `<spec-folder>/evidence/story-N/`.
3. Make the feature's check fail on purpose (for example, break the behavior it tests), then run `/implement-story` on another story that touches the same path.

**Expected Result:**
- Step 1's story report contains an `app-verify:` line such as `app-verify: 1/1 pass — evidence/story-N/`, and the gate asks no question.
- Step 2 holds `<id>/result.json` with `"verdict": "pass"`, plus `_launch/` logs.
- Step 3: Gate 4.5 reports a fail, the story goes back to Gate 1 for recode, and the iteration counts toward the 3-iteration cap.

**Status:** [ ] Pass  [ ] Fail

**Notes:**

---

### Scenario 27: Mockup comparison is advisory and can no longer fail a story

**Source:** Acceptance Criteria — Story 4 (AC-4.2)
**Feature:** none
**Verification:** human — no recipe

**Preconditions:**
- None

**Steps:**
1. In `commands/implement-story.md`, read the `--full-pipeline` subsection under Gate 4.5.
2. Read the Pipeline table row for Gate 4.5 and the `**Review loop:**` paragraph.
3. Open `agents/visual-qa-agent.md` and read what happens on a FAIL.

**Expected Result:**
- `visual-qa-agent` runs after the script, and only under `--full-pipeline`. Its mismatches go to the story report as notes, and they never fail the gate or increment the review-loop counter.
- The Pipeline row reads `` `app-verify.py` (no spawn); `--full-pipeline` adds notes-only `visual-qa-agent` on visual refs ``.
- The review-loop paragraph lists the shared-counter sites as Gate 3 FAIL, Gate 3.5 Reject, Gate 3.5 Modify spec, and **Gate 4.5 script fail**. A visual-QA FAIL is not one of them.
- The visual-QA agent describes its FAIL as notes only.

**Status:** [ ] Pass  [ ] Fail

**Notes:**

---

### Scenario 28: Only one gate is left without a script, and the cap enforces it

**Source:** Acceptance Criteria — Story 4 (AC-4.3)
**Feature:** none
**Verification:** human — no recipe

**Preconditions:**
- None

**Steps:**
1. Run `python3 scripts/verdict-provenance.py check --command commands/implement-story.md --prose-only-blocking; echo "exit=$?"`
2. Run `rg -n "gate4_5_behavior|gate4_5_visual" commands/implement-story.md scripts/verdict-provenance.py`
3. Run `bash scripts/tests/test_eval_verdict_provenance.sh; echo "exit=$?"`

**Expected Result:**
- Step 1 prints `note: prose_only_count: 1 (cap 1)` and `gates: 10 entries, headings: 10, script: 9, prose-only: 1, findings: 0`, then `exit=0`.
- Step 2 shows only `gate4_5_behavior`, with `script: scripts/app-verify.py` in the frontmatter. `gate4_5_visual` does not appear.
- Step 3 exits 0. That test also proves a fixture with two prose-only gates is a blocking finding.

**Status:** [ ] Pass  [ ] Fail

**Notes:**

---

### Scenario 29: The coding agent writes checks; it never grades them

**Source:** Acceptance Criteria — Story 4 (AC-4.4); User Journey step 4
**Feature:** none
**Verification:** human — no recipe

**Preconditions:**
- None

**Steps:**
1. Run `rg -n "Behavioral checks" agents/coding-agent.md codex/agents/coding-agent.toml`

**Expected Result:**
- Rule 6 in `agents/coding-agent.md` applies when a recipe exists and a story adds user-facing behavior that no Feature Map row covers. It says to write a check in the project's own test harness and add a matching row (ID, feature, paths, check). It also says the check's exit code is the verdict and the agent never grades the result.
- The regenerated Codex TOML carries the same rule.

**Status:** [ ] Pass  [ ] Fail

**Notes:**

---

### Scenario 30: The default pipeline still spawns at most two subagents, and the lean twin matches

**Source:** Acceptance Criteria — Story 4 (AC-4.5)
**Feature:** none
**Verification:** human — no recipe

**Preconditions:**
- `uv` is installed.

**Steps:**
1. Run `python3 scripts/spawn-cap.py check --command commands/implement-story.md; echo "exit=$?"`
2. Run `python3 scripts/verdict-provenance.py check --command commands/implement-story.lean.md --prose-only-blocking; echo "exit=$?"`
3. Run `uv run --python 3.9 pytest -q scripts/tests/test_lean_commands.py scripts/tests/test_governor_enforcement.py scripts/tests/test_implement_story_default_path.py`
4. Run `rg -n "2026-10-01-behavioral-verification" scripts/tests/test_lean_commands.py scripts/tests/test_governor_enforcement.py`

**Expected Result:**
- Step 1 prints `spawn-cap: pass (default spawn sites at or under cap)` then `exit=0`.
- Step 2 reports `prose_only_count: 1 (cap 1)` and `findings: 0`, then `exit=0`.
- Step 3 reports all passed.
- Step 4 shows the dated re-pin comments for `DEFAULT_SHA256["implement-story"]` and `KNOWN_OVER_BUDGET["commands/implement-story.md"]`. The over-budget overage went down (11110 → 11103), not up.

**Status:** [ ] Pass  [ ] Fail

**Notes:**

---

### Scenario 31: Gate 4.5 continues normally in a project with no recipe

**Source:** Shadow Path (Gate 4.5, nil input: no recipe; empty input: no mapped features) — Story 4
**Feature:** none
**Verification:** human — no recipe

**Preconditions:**
- `T=$(mktemp -d)`. The Writ repo has no `.writ/docs/app-verification.md` (Scenario 4).

**Steps:**
1. Run `python3 scripts/app-verify.py touched --recipe .writ/docs/app-verification.md --changed commands/implement-story.md; echo "exit=$?"`
2. Run `python3 scripts/app-verify.py run --recipe .writ/docs/app-verification.md --spec $T --run-label story-1; echo "exit=$?"`
3. Re-read the **exit 2** bullet under Gate 4.5 in `commands/implement-story.md`.

**Expected Result:**
- Steps 1 and 2 each print `app-verify: unverifiable (no_recipe)` then `exit=2`.
- Step 3 confirms that exit 2 means "relay the line and continue, not DEGRADED". So a story in a project without a recipe completes as it did before Phase 12.

**Status:** [ ] Pass  [ ] Fail

**Notes:**

---

## Story 5: `exit-criteria.py` Evidence Check, Mutation Test, and Eval Check

### Scenario 32: A passing UAT scenario cannot stand once its evidence is deleted

**Source:** Acceptance Criteria — Story 5 (AC-5.4, AC-5.1); Business Rule 6 mutation; Experience Design moment of truth
**Feature:** none
**Verification:** human — no recipe

**Preconditions:**
- `F=scripts/tests/fixtures/app-verify; T=$(mktemp -d)`
- Port 8765 is free.

**Steps:**
1. Run `python3 scripts/app-verify.py run --recipe $F/recipe-pass.md --spec $T --run-label uat`
2. Create a one-scenario plan: `printf '# UAT Plan: Fixture\n\n### Scenario 1: Home renders\n\n**Source:** Acceptance Criteria — Story 1\n**Feature:** home\n**Verification:** machine — evidence: evidence/uat/home/result.json\n\n**Status:** [x] Pass\n' > $T/uat-plan.md`
3. Run `python3 scripts/exit-criteria.py check-uat --spec $T; echo "exit=$?"`
4. Run `rm $T/evidence/uat/home/result.json`
5. Run `python3 scripts/exit-criteria.py check-uat --spec $T; echo "exit=$?"`

**Expected Result:**
- Step 1 prints `app-verify: 1/1 pass — evidence/uat/; human-only — oauth (third-party consent screen)`.
- Step 3 prints JSON with `"verdict": "met"`, `"outcome": "pass"`, and `"evidence": "1/1 machine scenarios cite passing evidence"`, then `exit=0`. No human step was involved.
- Step 5 prints JSON with `"verdict": "unmet"`, `"outcome": "missing"`, and `"reason": "evidence missing: <temp-folder-name> / Scenario 1 (evidence/uat/home/result.json)"`, then `exit=1`.

**Implementation Reference:** Story 5 — `scripts/exit-criteria.py` (`check-uat`, evidence half of `implement-phase.c2`)

**Status:** [ ] Pass  [ ] Fail

**Notes:**

---

### Scenario 33: Failing, unreadable, or out-of-folder evidence is unmet

**Source:** Acceptance Criteria — Story 5 (AC-5.1)
**Feature:** none
**Verification:** human — no recipe

**Preconditions:**
- The `$T` folder and `uat-plan.md` from Scenario 32, after step 5.

**Steps:**
1. Run `echo '{"verdict":"fail"}' > $T/evidence/uat/home/result.json && python3 scripts/exit-criteria.py check-uat --spec $T; echo "exit=$?"`
2. Run `echo 'not json' > $T/evidence/uat/home/result.json && python3 scripts/exit-criteria.py check-uat --spec $T; echo "exit=$?"`
3. Run `sed -i '' 's#evidence/uat/home/result.json#../outside.json#' $T/uat-plan.md && python3 scripts/exit-criteria.py check-uat --spec $T; echo "exit=$?"` (on Linux, use `sed -i` without `''`)

**Expected Result:**
- Step 1: `"outcome": "not_pass"`, with a reason starting `evidence not pass:` and ending `: verdict 'fail')`, then `exit=1`.
- Step 2: `"outcome": "unreadable"`, with a reason starting `evidence unreadable:` and ending `: JSONDecodeError)`, then `exit=1`.
- Step 3: `"outcome": "outside_spec"`, with a reason starting `evidence outside spec folder:`, then `exit=1`.
- Every reason names the spec folder and `Scenario 1`.

**Status:** [ ] Pass  [ ] Fail

**Notes:**

---

### Scenario 34: Older plans and all-human plans pass, with a note; a missing spec is impossible

**Source:** Acceptance Criteria — Story 5 (AC-5.2, AC-5.3)
**Feature:** none
**Verification:** human — no recipe

**Preconditions:**
- `L=$(mktemp -d); printf '# UAT Plan: Legacy\n\n### Scenario 1: X\n\n**Source:** AC — Story 1\n\n**Status:** [ ] Pass\n' > $L/uat-plan.md`

**Steps:**
1. Run `python3 scripts/exit-criteria.py check-uat --spec $L; echo "exit=$?"`
2. Run `python3 scripts/exit-criteria.py check-uat --spec .writ/specs/2026-10-01-behavioral-verification; echo "exit=$?"`
3. Run `python3 scripts/exit-criteria.py check-uat --spec /nonexistent-spec; echo "exit=$?"`
4. Open `.writ/docs/exit-criteria-classification.md`, find the `implement-phase.c2` Bucket Table row and the `## implement-phase.c2` section.

**Expected Result:**
- Step 1: `"verdict": "met"` and `"evidence": "legacy plan: <temp-folder-name>"`, then `exit=0`.
- Step 2: `"verdict": "met"` and `"evidence": "no machine scenarios: 2026-10-01-behavioral-verification"`, then `exit=0`.
- Step 3: `"verdict": "impossible"` and `"reason": "spec folder not found: /nonexistent-spec"`, then `exit=2`. There is no traceback.
- Step 4: the row reads `evaluable-now (split: presence + ordering + evidence)`, and the section has an **Evidence — evidence half** paragraph.

**Status:** [ ] Pass  [ ] Fail

**Notes:**

---

### Scenario 35: The quality gate proves the whole path end to end

**Source:** Acceptance Criteria — Story 5 (AC-5.5); spec Success Criteria
**Feature:** none
**Verification:** human — no recipe

**Preconditions:**
- A terminal outside any sandbox. `uv` is installed.

**Steps:**
1. Run `bash scripts/eval.sh --check=app-verify; echo "exit=$?"` and open the report path it prints.
2. Run `bash scripts/tests/test_eval_app_verify.sh; echo "exit=$?"`
3. Run `bash scripts/eval.sh; echo "exit=$?"` and open the report.
4. Run `uv run pytest -q`
5. Run `pgrep -fl "app-verify/app.py" || echo "no fixture process"`

**Expected Result:**
- Step 1: `exit=0`. The report's `## app-verify` section reads `PASS`, with a note that the fixture pass, fail, and refused runs and the missing-evidence mutation were checked on some port. The summary reads `Findings: 0` and `Run errors: 0`.
- Step 2: `exit=0`. A stubbed script that always exits 0 is caught as a finding.
- Step 3: the full report reads `Findings: 0`.
- Step 4: `2109 passed, 1 skipped` (or more, if tests were added later).
- Step 5: `no fixture process`.

**Status:** [ ] Pass  [ ] Fail

**Notes:**

---

## Pending Stories

None. All five stories are Completed ✅.
