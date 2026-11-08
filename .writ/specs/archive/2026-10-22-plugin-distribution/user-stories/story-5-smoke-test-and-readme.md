# Story 5: Smoke Test Across Five Targets, README Install Order, and Live-Run Evidence

> **Status:** Completed ✅ (2026-10-23)
> **Commit:** 0e4085eeebeb34df1a90e2fbf2938b61ef14e81a
> **Priority:** High
> **Dependencies:** Story 2, Story 3, Story 4

## User Story

**As a** new user reading the README
**I want to** install Writ through the path the smoke test has passed
**So that** I am never sent down an install path that was not proven to work, and the maintainer sees in one test run which of the five paths is broken

## Acceptance Criteria

> **AC IDs assigned through:** AC-5.5

- [x] Given `scripts/tests/test_plugin_smoke.sh` and five targets (`cursor`, `claude`, `codex`, `claude-plugin`, `cursor-plugin`), when it runs, then it prints one line per target and check in the form `<target> <check> <pass|fail|unverifiable (reason)>`, prints one summary line per target in the form `<target> <pass|fail|unverifiable>` where a target reads `pass` only when every check passed, and exits 1 when any check fails and 0 otherwise `[AC-5.1]`
- [x] Given the five installed trees (`cursor`, `claude`, `codex` built by `scripts/install.sh --platform <p>` in fresh `git init` temp projects from a committed temp copy of the working tree; `claude-plugin` and `cursor-plugin` built from temp copies of their plugin directories), when the checks run, then each target checks that every `file:` in the `commands:` list of `.writ/manifest.yaml` exists at the platform's command path, that `python3 <root>/scripts/spec-status.py --help` exits 0 from the resolved root, that the instructions file exists at the path the platform loads (or the Writ block imports it), and that `scaffold-writ.py scaffold --project <empty temp dir>` creates the `.writ/` tree; `install.sh` targets also pass `scaffold-writ.py --check` in the installed project; and no check runs `install.sh` against the Writ repository `[AC-5.2]`
- [x] Given `claude` is not on `PATH`, when the `claude-plugin` target runs, then its `claude plugin validate` line reads `unverifiable (no claude CLI)`, its other checks still run, and its summary reads `unverifiable`; given `claude` is on `PATH` and validate exits 1 or 2, then that line reads `fail`; and given the Story 3 Cursor layout has no plugin-root `scripts/` directory, when the `cursor-plugin` target runs, then its script-run line reads `unverifiable (no cursor session)` and its other checks still run `[AC-5.3]`
- [x] Given `scripts/tests/fixtures/plugin-smoke-results.txt` with the summary lines from a recorded run, when `test_readme_install_order` runs, then: README § Quick Start has a `### Claude Code (plugin)` subsection before `### Cursor (one-line install)`, containing `claude plugin marketplace add`, `claude plugin install`, and `/writ:initialize`, only when `claude-plugin` reads `pass`; a `### Cursor (plugin)` subsection exists after `### Cursor (one-line install)` with the sentence "local install; marketplace listing pending" unless `cursor-plugin` reads `pass` and the `cursor-uat` line reads `run`, in which case it comes before `### Cursor (one-line install)`; the `install.sh` subsections keep their headings and text; and `adapters/codex.md` has one added dated line stating Codex has no plugin path in this release and `install.sh` remains its install path `[AC-5.4]`
- [x] Given a fresh empty temp project with the Claude Code plugin installed from the marketplace, when the maintainer runs `/writ:initialize` and then `/writ:writ "add a health endpoint"` in a live Claude Code session, then What Was Built records the `claude --version` output and the transcript lines showing the `.writ/` scaffold and the route the session chose `[AC-5.5]`

## Implementation Tasks

- [x] 5.1 Write the failing tests first. Add cases to `scripts/tests/test_plugin_smoke.sh` that put a stub `claude` on `PATH` (present, then absent) and assert the line format, the summary rule, the exit codes, and the `unverifiable` labels. Add `test_readme_install_order` to `scripts/tests/test_plugin_distribution.py`; it reads the fixture and the README. Run both and confirm they fail on the current tree for the expected reasons (no smoke script, no fixture, no plugin subsections) `[AC-5.1, AC-5.2, AC-5.3, AC-5.4]`
- [x] 5.2 Implement the `install.sh` targets (`cursor`, `claude`, `codex`). Copy the working tree into a temp source dir, `git init` and commit it (follow `commit_src` in `scripts/tests/test_install_update_claude_parity.sh`), run `scripts/install.sh --platform <p>` in a fresh `git init` temp project, then run the checks. Remove every temp dir with a `trap`. Make the `install.sh` cases from 5.1 pass `[AC-5.1, AC-5.2]`
- [x] 5.3 Implement the plugin targets. `claude-plugin`: copy the plugin directory from Story 2's layout (under layout A, exclude `.git/` and `.writ/` from the copy), run the checks on the copy, and run `claude plugin validate <copy>` only when `command -v claude` succeeds. `cursor-plugin`: copy the Story 3 layout, run the checks, and report the script-run line as `unverifiable (no cursor session)` when the layout has no plugin-root `scripts/`. Make the plugin and unverifiable cases from 5.1 pass `[AC-5.1, AC-5.2, AC-5.3]`
- [x] 5.4 Run `scripts/tests/test_plugin_smoke.sh` on this machine, outside any sandbox. Save the `<target> <result>` summary lines to `scripts/tests/fixtures/plugin-smoke-results.txt`, with `#` comment lines for the run date and the `claude --version` output (or `no claude CLI`). Add a `cursor-uat` line reading `pending` unless the Cursor UAT protocol has run `[AC-5.4]`
- [x] 5.5 Edit README § Quick Start by heading, never by line number. Add `### Claude Code (plugin)` and `### Cursor (plugin)` as AC-5.4 specifies. Leave the `### Cursor (one-line install)`, `### Updating`, `### Claude Code (one-line install)`, and `### Codex CLI (one-line install)` subsections unchanged (confirm with `git diff`). Add the dated Codex line under `## Overview` in `adapters/codex.md`. Make `test_readme_install_order` pass `[AC-5.4]`
- [x] 5.6 Live run (manual; not a test). Make the marketplace source reachable (see Notes), then in an empty temp project run `claude plugin marketplace add`, `claude plugin install writ@writ`, `/writ:initialize`, and `/writ:writ "add a health endpoint"`. Paste the `claude --version` output and the transcript lines showing the scaffold and the route into What Was Built `[AC-5.5]`
- [x] 5.7 Verify: `uv run --python 3.9 pytest`; `for t in scripts/tests/test_*.sh; do bash "$t" || echo "FAIL $t"; done` prints no `FAIL` line; `bash scripts/eval.sh`, run outside the sandbox, reports 0 findings; `bash scripts/tests/test_plugin_smoke.sh` exits 0 on this machine; the README and the fixture agree `[AC-5.1, AC-5.2, AC-5.3, AC-5.4, AC-5.5]`

## Notes

**Preconditions.** Stories 2, 3, and 4 are built. The Story 1 Verification Record is filled. The layout (`sub-specs/technical-spec.md` → `## Candidate Layouts`) sets the `claude-plugin` directory; the Cursor script form sets the `cursor-plugin` check.

**Decisions in this story (confirm or override)**

- **Results file: committed fixture, not a temp file.** A temp file is gone after the run, so `test_readme_install_order` cannot read it without re-running the smoke test. The maintainer copies the summary lines into the fixture after each run. The run date line makes a stale fixture visible.
- **`unverifiable` is not `pass` for the README.** A target reads `pass` only when every check passed. An unverifiable Claude plugin does not get the first-position subsection. This follows `spec.md` → `## Business Rules (Expanded)` Rule 10.
- **Cursor subsection on fail or unverifiable.** Rule 10's "else" clause keeps `### Cursor (plugin)` after the install.sh section for any result short of pass plus UAT. The Claude subsection has no such clause and appears only on `pass`. If the maintainer wants a failing Cursor plugin removed from the README, amend Rule 10 first.
- **Label for the Cursor script check.** The spec's Success Criteria name `unverifiable (no cursor session)`. No Cursor check is automatable. This story applies that label only to the script-run check when the layout has no plugin-root `scripts/`. Under that form the layout cannot run its own scripts, so the check cannot pass without a session.

**Technical considerations**

- Every target builds into `mktemp -d` dirs removed by a `trap`. Nothing writes under `~/.cursor` or `~/.claude`.
- Plugin targets check a copy of the plugin directory. Under layout A the plugin directory is the repository root, so checking it in place would test the source tree instead of the installed tree.
- The `install.sh` targets pick up Story 4's change: `install.sh` calls `scaffold-writ.py`, so a regression in that call fails the `scaffold` check.
- Reuse `scripts/tests/test_install_update_claude_parity.sh` (`commit_src`, `fail()`, Writ block extraction between `writ:start` and `writ:end`) and `scripts/tests/test_merge_agents_md.sh` (Codex block). Command paths per target: `sub-specs/technical-spec.md` → `## Smoke Test`.
- The pytest test makes no network call and runs no install. It reads only the README, `adapters/codex.md`, and the fixture.
- The Codex line states a platform claim. Rule 1 requires a date and a source URL. If no first-party Codex page is read in this story, the line carries `unverified <date>` in the grammar from `sub-specs/technical-spec.md` → `## Verification Record`.

**Risks**

- **README promises an unproven path.** Mitigated by the fixture gate in `test_readme_install_order`.
- **Smoke test checks the source tree.** Mitigated by the copy and install rule in AC-5.2.
- **`install.sh` run against the Writ repository.** This repo uses symlinks for `.claude/` and `.cursor/`, and `CLAUDE.md` forbids running `install.sh` here. Mitigated by temp projects only.
- **Live-run marketplace source.** `claude plugin marketplace add sellke/writ` reads the GitHub repository, not this working tree. Confirm which ref it reads before 5.6. If that ref is `main`, Stories 2 to 4 must be merged first. Otherwise use the local-path form that Story 1 verified and say so in What Was Built.
- **Fixture drift.** A platform change makes the fixture stale. The run date and version lines show when it was recorded. Re-run and re-record on any change to the plugin layout or the platform version.

**Integration**

- Stories 2 to 4 supply the plugin directories, `scaffold-writ.py`, and the `install.sh` change. This story reads their outputs and does not edit their files, except the README and `adapters/codex.md`.
- The front-door and prompting-guide specs own the top of § Quick Start. The plugin subsections go after that content and before `### Cursor (one-line install)`. Edit by heading.
- The Cursor live check stays a UAT protocol (`sub-specs/technical-spec.md` → `## UAT Protocols`). The `cursor-uat` line in the fixture records its result.

---

## Definition of Done

- [x] All tasks completed
- [x] All acceptance criteria met
- [x] Tests passing
- [x] Code reviewed
- [x] Documentation updated

## Context for Agents

- **Error map rows:** []
- **Shadow paths:** `technical-spec.md → ## Shadow Paths` (Happy path, Nil input, Empty input, Upstream error)
- **Business rules:** `spec.md → ## Business Rules (Expanded)` (Rule 1 Verification record first; Rule 9 Smoke test; Rule 10 README; Rule 11 Live run evidence; Rule 12 Runtime)
- **Experience:** `spec.md → ## Experience Design → ### State Catalog` (Claude Code plugin installed, project without `.writ/`; `claude plugin validate .`; Smoke test on a machine without the `claude` CLI; README install section)

---

## What Was Built

**Implementation Date:** 2026-10-23

### Files Created

1. **`scripts/tests/test_plugin_smoke.sh`** (730 lines)
   - Five targets (`cursor`, `claude`, `codex` via `install.sh --no-commit` from a committed temp copy into fresh `git init` projects; `claude-plugin` and `cursor-plugin` on temp copies of `plugins/writ/` and `cursor/plugin/`), one `<target> <check> <result>` line per check and one summary per target, exit 1 on any fail; temp HOME and temp dirs only; `claude plugin validate` only with the CLI on PATH; eight self-tests (summary rule, record file, usage errors, missing plugin directories, no CLI, stub CLI exiting 0, 1, 2); `--record`, `--targets`, `--no-self-test`, `--verbose`.
2. **`scripts/tests/fixtures/plugin-smoke-results.txt`** (10 lines)
   - Recorded 2026-10-23 with `claude --version` 2.1.309: `cursor pass`, `claude pass`, `codex pass`, `claude-plugin pass`, `cursor-plugin unverifiable`, `cursor-uat pending`.

### Files Modified

- **`scripts/tests/test_plugin_distribution.py`** (`test_readme_install_order` and helpers; sha256 pins on the four install.sh README subsections)
- **`README.md`** (§ Quick Start: `### Claude Code (plugin)` before `### Cursor (one-line install)`; `### Cursor (plugin)` after `### Updating` with "local install; marketplace listing pending"; the four install.sh subsections byte-unchanged)
- **`adapters/codex.md`** (one dated line under `## Overview`: no Codex plugin in this release; `install.sh --platform codex` remains the install path)
- **`.writ/specs/2026-10-22-plugin-distribution/sub-specs/technical-spec.md`** (§ Verification Record: V81 to V85 from the live run; V72 verified)
- **`.writ/specs/2026-10-22-plugin-distribution/spec-lite.md`**, **`drift-log.md`** (DEV-021 to DEV-024)

### Implementation Decisions

1. **Local-checkout marketplace for the live run** — the plugin was installed from this checkout (`claude plugin marketplace add <checkout> --scope local`) in a fresh temp project; the GitHub-sourced `sellke/writ` install is the post-merge UAT step (V73 stays unverified).
2. **README order from the fixture** — the Claude plugin subsection is first because `claude-plugin pass`; the Cursor plugin subsection follows the Cursor install.sh section because `cursor-plugin unverifiable` and `cursor-uat pending`.

### Test Results

**Verification:** `bash scripts/tests/test_plugin_smoke.sh` exit 0 (28 check lines; summaries `cursor pass`, `claude pass`, `codex pass`, `claude-plugin pass`, `cursor-plugin unverifiable`); `uv run --python 3.9 pytest scripts/tests/test_plugin_distribution.py -q` 115 passed (red first: no fixture, then the missing Codex line).
- ✅ Live run (task 5.6, 2026-10-23T20:45Z, lane HEAD 23bbfbd). `claude --version`: `2.1.309 (Claude Code)`. Marketplace add and install from this checkout, local scope: rc 0, "Successfully installed plugin: writ@writ (scope: local)".
- ✅ `/writ:initialize` in the empty project ran `python3 <checkout>/plugins/writ/scripts/scaffold-writ.py scaffold`: `pass`, eleven `created .writ/...` lines, `added .gitignore entry .writ/state/`, `added .gitignore entry .writ-lanes-*/`, `scaffold-writ: pass (11 created, 0 existing)`; then "This is a greenfield project." and the four technical-discovery questions. The project has no `scripts/`.
- ✅ `/writ:writ "add a health endpoint"`: "Goal: The project serves an HTTP health endpoint (e.g. GET /health → 200 with a small JSON body)." and "Proposed: `/writ:prototype` (Recommended)", with route options spelled `/writ:<command>`.
- ✅ Session init listed exactly the eight `writ:writ-*` agents (no prompt-template doc loaded as an agent) and 49 `writ:` slash commands (33 commands + 16 skills, no `_preamble`); the P2 probe quoted the first Hard Constraint with `SOURCE Prime Directive`.
- ✅ Undo: `claude plugin uninstall writ@writ --scope local` and `claude plugin marketplace remove writ` rc 0; `installed_plugins.json` and `known_marketplaces.json` equal their pre-run snapshots; `~/.claude/settings.json` sha256 unchanged.
- ✅ Gate scripts: test-integrity authenticity pass for the Python test; the bash smoke test reads `test_imports_no_source` like every existing `scripts/tests/*.sh` (checker reads `.py` only, DEV-024); mutation runs show it exercises the source.

### Review Outcome

**Result:** PASS

- **Iteration count:** 1 iteration(s) (review-agent route; Minor pre-commit fixes: missing-directory lines, subsection hash pins, `cursor-uat run` carried forward, scaffold detail; V72 flipped)
- **Drift:** Medium
- **Security:** Clean
- **Boundary Compliance:** all changes in owned or orchestrator-recorded paths; no violations

### Deviations from Spec

- **[DEV-021] `cursor-plugin` script-run reads `unverifiable (no cursor session)`** — Severity: Small
  - Spec said: Rule 9, `pass (requires project scripts/)`.
  - Reality: AC-5.3's label.
  - Resolution: Auto-amended (Small).
  - Spec amendment: spec-lite.md smoke test line.
- **[DEV-022] `### Cursor (plugin)` stays in the README when `cursor-plugin` fails** — Severity: Medium
  - Spec said: Rule 10 omits it on fail.
  - Reality: AC-5.4 keeps it after the install.sh section for any result short of pass + UAT.
  - Resolution: Flagged for review.
- **[DEV-023] Smoke test adds checks and flags beyond the AC** — Severity: Small
  - Spec said: four checks plus validate.
  - Reality: `install`, `validate-marketplace`, `--record` and other flags.
  - Resolution: Auto-amended (Small).
  - Spec amendment: spec-lite.md smoke test line.
- **[DEV-024] test-integrity authenticity has no shell analysis** — Severity: Small
  - Spec said: `test_imports_no_source` is blocking.
  - Reality: the checker reads `.py` tests only; mutation runs stand in.
  - Resolution: Auto-amended (Small).
  - Spec amendment: spec-lite.md Test Strategy.
