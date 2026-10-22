# Story 5: Smoke Test Across Five Targets, README Install Order, and Live-Run Evidence

> **Status:** Not Started
> **Priority:** High
> **Dependencies:** Story 2, Story 3, Story 4

## User Story

**As a** new user reading the README
**I want to** install Writ through the path the smoke test has passed
**So that** I am never sent down an install path that was not proven to work, and the maintainer sees in one test run which of the five paths is broken

## Acceptance Criteria

> **AC IDs assigned through:** AC-5.5

- [ ] Given `scripts/tests/test_plugin_smoke.sh` and five targets (`cursor`, `claude`, `codex`, `claude-plugin`, `cursor-plugin`), when it runs, then it prints one line per target and check in the form `<target> <check> <pass|fail|unverifiable (reason)>`, prints one summary line per target in the form `<target> <pass|fail|unverifiable>` where a target reads `pass` only when every check passed, and exits 1 when any check fails and 0 otherwise `[AC-5.1]`
- [ ] Given the five installed trees (`cursor`, `claude`, `codex` built by `scripts/install.sh --platform <p>` in fresh `git init` temp projects from a committed temp copy of the working tree; `claude-plugin` and `cursor-plugin` built from temp copies of their plugin directories), when the checks run, then each target checks that every `file:` in the `commands:` list of `.writ/manifest.yaml` exists at the platform's command path, that `python3 <root>/scripts/spec-status.py --help` exits 0 from the resolved root, that the instructions file exists at the path the platform loads (or the Writ block imports it), and that `scaffold-writ.py scaffold --project <empty temp dir>` creates the `.writ/` tree; `install.sh` targets also pass `scaffold-writ.py --check` in the installed project; and no check runs `install.sh` against the Writ repository `[AC-5.2]`
- [ ] Given `claude` is not on `PATH`, when the `claude-plugin` target runs, then its `claude plugin validate` line reads `unverifiable (no claude CLI)`, its other checks still run, and its summary reads `unverifiable`; given `claude` is on `PATH` and validate exits 1 or 2, then that line reads `fail`; and given the Story 3 Cursor layout has no plugin-root `scripts/` directory, when the `cursor-plugin` target runs, then its script-run line reads `unverifiable (no cursor session)` and its other checks still run `[AC-5.3]`
- [ ] Given `scripts/tests/fixtures/plugin-smoke-results.txt` with the summary lines from a recorded run, when `test_readme_install_order` runs, then: README § Quick Start has a `### Claude Code (plugin)` subsection before `### Cursor (one-line install)`, containing `claude plugin marketplace add`, `claude plugin install`, and `/writ:initialize`, only when `claude-plugin` reads `pass`; a `### Cursor (plugin)` subsection exists after `### Cursor (one-line install)` with the sentence "local install; marketplace listing pending" unless `cursor-plugin` reads `pass` and the `cursor-uat` line reads `run`, in which case it comes before `### Cursor (one-line install)`; the `install.sh` subsections keep their headings and text; and `adapters/codex.md` has one added dated line stating Codex has no plugin path in this release and `install.sh` remains its install path `[AC-5.4]`
- [ ] Given a fresh empty temp project with the Claude Code plugin installed from the marketplace, when the maintainer runs `/writ:initialize` and then `/writ:writ "add a health endpoint"` in a live Claude Code session, then What Was Built records the `claude --version` output and the transcript lines showing the `.writ/` scaffold and the route the session chose `[AC-5.5]`

## Implementation Tasks

- [ ] 5.1 Write the failing tests first. Add cases to `scripts/tests/test_plugin_smoke.sh` that put a stub `claude` on `PATH` (present, then absent) and assert the line format, the summary rule, the exit codes, and the `unverifiable` labels. Add `test_readme_install_order` to `scripts/tests/test_plugin_distribution.py`; it reads the fixture and the README. Run both and confirm they fail on the current tree for the expected reasons (no smoke script, no fixture, no plugin subsections) `[AC-5.1, AC-5.2, AC-5.3, AC-5.4]`
- [ ] 5.2 Implement the `install.sh` targets (`cursor`, `claude`, `codex`). Copy the working tree into a temp source dir, `git init` and commit it (follow `commit_src` in `scripts/tests/test_install_update_claude_parity.sh`), run `scripts/install.sh --platform <p>` in a fresh `git init` temp project, then run the checks. Remove every temp dir with a `trap`. Make the `install.sh` cases from 5.1 pass `[AC-5.1, AC-5.2]`
- [ ] 5.3 Implement the plugin targets. `claude-plugin`: copy the plugin directory from Story 2's layout (under layout A, exclude `.git/` and `.writ/` from the copy), run the checks on the copy, and run `claude plugin validate <copy>` only when `command -v claude` succeeds. `cursor-plugin`: copy the Story 3 layout, run the checks, and report the script-run line as `unverifiable (no cursor session)` when the layout has no plugin-root `scripts/`. Make the plugin and unverifiable cases from 5.1 pass `[AC-5.1, AC-5.2, AC-5.3]`
- [ ] 5.4 Run `scripts/tests/test_plugin_smoke.sh` on this machine, outside any sandbox. Save the `<target> <result>` summary lines to `scripts/tests/fixtures/plugin-smoke-results.txt`, with `#` comment lines for the run date and the `claude --version` output (or `no claude CLI`). Add a `cursor-uat` line reading `pending` unless the Cursor UAT protocol has run `[AC-5.4]`
- [ ] 5.5 Edit README § Quick Start by heading, never by line number. Add `### Claude Code (plugin)` and `### Cursor (plugin)` as AC-5.4 specifies. Leave the `### Cursor (one-line install)`, `### Updating`, `### Claude Code (one-line install)`, and `### Codex CLI (one-line install)` subsections unchanged (confirm with `git diff`). Add the dated Codex line under `## Overview` in `adapters/codex.md`. Make `test_readme_install_order` pass `[AC-5.4]`
- [ ] 5.6 Live run (manual; not a test). Make the marketplace source reachable (see Notes), then in an empty temp project run `claude plugin marketplace add`, `claude plugin install writ@writ`, `/writ:initialize`, and `/writ:writ "add a health endpoint"`. Paste the `claude --version` output and the transcript lines showing the scaffold and the route into What Was Built `[AC-5.5]`
- [ ] 5.7 Verify: `uv run --python 3.9 pytest`; `for t in scripts/tests/test_*.sh; do bash "$t" || echo "FAIL $t"; done` prints no `FAIL` line; `bash scripts/eval.sh`, run outside the sandbox, reports 0 findings; `bash scripts/tests/test_plugin_smoke.sh` exits 0 on this machine; the README and the fixture agree `[AC-5.1, AC-5.2, AC-5.3, AC-5.4, AC-5.5]`

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

- [ ] All tasks completed
- [ ] All acceptance criteria met
- [ ] Tests passing
- [ ] Code reviewed
- [ ] Documentation updated

## Context for Agents

- **Error map rows:** []
- **Shadow paths:** `technical-spec.md → ## Shadow Paths` (Happy path, Nil input, Empty input, Upstream error)
- **Business rules:** `spec.md → ## Business Rules (Expanded)` (Rule 1 Verification record first; Rule 9 Smoke test; Rule 10 README; Rule 11 Live run evidence; Rule 12 Runtime)
- **Experience:** `spec.md → ## Experience Design → ### State Catalog` (Claude Code plugin installed, project without `.writ/`; `claude plugin validate .`; Smoke test on a machine without the `claude` CLI; README install section)
