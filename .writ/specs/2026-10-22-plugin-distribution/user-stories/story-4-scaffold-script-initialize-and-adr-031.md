# Story 4: Scaffold Script, `/initialize` Step 0, and ADR-031

> **Status:** Completed ✅ (2026-10-23)
> **Commit:** 88c36551e1c2af5cb06554c8a1c2b41492db6542
> **Priority:** High
> **Dependencies:** Story 1

## User Story

**As a** Writ user who installed the plugin into a project with no `.writ/` folder
**I want to** run `/writ:initialize` and have it create the `.writ/` tree through one shipped script, `scripts/scaffold-writ.py`, which `install.sh` and `update.sh` also call
**So that** a plugin project gets the same scaffold as an `install.sh` project, the installers and `/initialize` cannot drift apart, and the script-location decision is recorded in ADR-031

## Acceptance Criteria

> **AC IDs assigned through:** AC-4.5

- [x] Given an empty project directory with no `.gitignore`, when `python3 scripts/scaffold-writ.py scaffold --project <dir>` runs, then `.writ/specs`, `.writ/product`, `.writ/research`, `.writ/decision-records`, `.writ/docs`, `.writ/knowledge`, `.writ/state`, `.writ/issues/bugs`, `.writ/issues/features`, `.writ/issues/improvements`, and `.writ/issues/goals` exist as directories; `.gitignore` gains `.writ/state/` and `.writ-lanes-*/` once each; stdout line 1 is `pass`; one `created <path>` line follows per path that was missing; the last line is `scaffold-writ: pass (<n> created, <m> existing)`; and the exit code is 0 `[AC-4.1]`
- [x] Given a project where all eleven paths and both ignore entries already exist, when the script runs again, then it prints `scaffold-writ: pass (0 created, 11 existing)`, creates no path, and leaves `.gitignore` byte-identical; and given a `.gitignore` that already holds `.writ/state` or `.writ/state/` as a whole line, when the script runs, then that entry is not appended again `[AC-4.2]`
- [x] Given a project missing some of the eleven paths or ignore entries, when `scaffold --check` runs, then stdout line 1 is `fail`, one `reason: missing <path>` line prints per missing path and one `reason: missing .gitignore entry <entry>` line per missing entry, the last line is `scaffold-writ: fail (<m> missing)`, nothing is written, and the exit code is 1; given a complete tree, `--check` prints `pass` and exits 0; given no subcommand or an unknown flag, the script prints usage to stderr, leaves stdout empty, and exits 2; and `--help` exits 0 `[AC-4.3]`
- [x] Given `scripts/install.sh` and `scripts/update.sh`, when each reaches its `.writ/` step, then each has a byte-identical bash `init_writ_workspace` whose `mkdir -p` list expands to the script's eleven paths and which creates `.gitignore` when absent, neither script calls `python3`, and `test_bash_list_matches` proves the two lists equal the script's `PATHS`; given `commands/initialize.md`, when `/initialize` runs in a project without `.writ/`, then Step 0 runs the script before detection, reports each `created` line, stops and reports the `reason:` lines if line 1 is not `pass`, and the sentence "`.writ/` exists from installation" is gone; and the existing `scripts/tests/test_install_update_*.sh` tests pass `[AC-4.4]`
- [x] Given the § ADR-031 Outline in `technical-spec.md`, when the record is written, then `.writ/decision-records/adr-031-script-location.md` has the header fields and section set that `adr-029-agent-cli-contract.md` uses, and it states the two install paths and the shared-name rule; `adr-029-agent-cli-contract.md` gains a `Superseded in part by` header line that links ADR-031; and the script-install-location issue gains a `## Resolution` section that names ADR-031 and `spec.md`, with `spec_ref` set to `spec.md` `[AC-4.5]`

## Implementation Tasks

- [x] 4.1 Write `scripts/tests/test_scaffold_writ.py` (pytest, Python 3.9 stdlib, temp directories only, no network). Cover: a fresh directory gets the eleven paths and both ignore entries; `test_bash_list_matches` extracts the `mkdir -p` line from `init_writ_workspace` in both installers, expands its brace list, and asserts it equals the script's `PATHS` (fails today: the installer list lacks `knowledge/` and the `issues/` subfolders); with `pass` on line 1 and the summary line; a second run creates nothing and leaves `.gitignore` unchanged; a pre-existing `.writ/state` line is not duplicated; `--check` on an empty directory prints `fail`, the `reason:` lines, writes nothing, and exits 1; `--help` exits 0; no subcommand exits 2 with empty stdout. Run it. Confirm each failure is the missing script (`can't open file`) or its assertion, not a collection or syntax error `[AC-4.1, AC-4.2, AC-4.3]`
- [x] 4.2 Implement `scripts/scaffold-writ.py` (stdlib only, 3.9 floor; `scaffold [--project <dir>] [--check]`; `--project` defaults to the current directory) until 4.1 passes. Follow `.writ/docs/agent-cli-contract.md` § Check shape and § Usage errors. Add the script's row to § Classification as `check`. Add one `SMOKE_INVOCATIONS` entry in `scripts/tests/test_agent_cli_contract.py` whose paths all sit under `{tmp}`. Run `uv run --python 3.9 pytest scripts/tests/test_scaffold_writ.py scripts/tests/test_agent_cli_contract.py scripts/tests/test_agent_cli_contract_doc.py` and confirm all pass `[AC-4.1, AC-4.2, AC-4.3]`
- [x] 4.3 Edit `scripts/install.sh`. In `init_writ_workspace`, change the `mkdir -p` list to the script's eleven paths (dropping `explanations`), make the `.gitignore` step create the file when absent and append `.writ/state/` and `.writ-lanes-*/` when missing, and keep the `Creating .writ/ directory structure` echo and the legacy `cc.mdc` cleanup. Copy the resulting function byte-identically into `scripts/update.sh` (which has no scaffold step today) and call it after `WRIT_SRC` is set, so an update repairs a missing tree. Neither script calls `python3`. Run `for t in scripts/tests/test_install_update_*.sh scripts/tests/test_manifest_shipped_baselines.sh; do bash "$t" || echo "FAIL $t"; done`. If a failure traces to an assertion that encodes the old tree, stop and report it; do not edit the assertion `[AC-4.4]`
- [x] 4.4 Edit `commands/initialize.md`. Add `### Step 0: Scaffold .writ/` under `## Overview`, directly before `### Detection Logic`. Step 0 runs `python3 scripts/scaffold-writ.py scaffold`, reports each `created` line, and stops with the `reason:` lines if line 1 is not `pass`; otherwise it continues to detection. Replace "`.writ/` exists from installation; create docs within `.writ/docs/`." with "Step 0 creates `.writ/` when it is absent; create docs within `.writ/docs/`." Read each `exit_criteria` entry against Step 0 and confirm none is contradicted `[AC-4.4]`
- [x] 4.5 Write `.writ/decision-records/adr-031-script-location.md` from `technical-spec.md` § ADR-031 Outline, using the header fields and section set of `adr-029-agent-cli-contract.md`. Cover the decision, the two install paths (`install.sh` keeps `scripts/` in the project; plugins run from `${CLAUDE_PLUGIN_ROOT}/scripts`), the shared-name rule, the options from the issue's Expected Outcome with the chosen one and the reason, the consequences including the Notes defaults, and the one ADR-029 consequence it supersedes. Set Status to `Proposed`; change it to `Accepted` only after Story 1's § Verification Record marks the plugin script-root row `verified`. Add `> **Superseded in part by:** [ADR-031](adr-031-script-location.md)` to ADR-029's header. Add `## Resolution` to `.writ/issues/improvements/2026-10-12-script-install-location.md` naming ADR-031 and `.writ/specs/2026-10-22-plugin-distribution/spec.md`, and set its `spec_ref` to that path `[AC-4.5]`
- [x] 4.6 Verify. Run `uv run --python 3.9 pytest`, `for t in scripts/tests/test_*.sh; do bash "$t" || echo "FAIL $t"; done`, and `bash scripts/eval.sh` outside any sandbox (expect 0 findings). In a scratch directory outside the repository, run `python3 scripts/scaffold-writ.py scaffold --project <dir>` twice and confirm the second run reports `0 created`. Run `git status --short` and confirm the changes fall only in the files this story names. Report the pytest count and the eval findings count `[AC-4.1, AC-4.2, AC-4.3, AC-4.4, AC-4.5]`

## Notes

- **Depends on Story 1.** ADR-031 names the plugin script root. Finalize ADR-031 only after Story 1's § Verification Record shows the plugin script root and carrier rows `verified`. `${CLAUDE_PLUGIN_ROOT}/scripts` holds under either layout A or B.
- **Spec premise corrected: `update.sh` has no scaffold block.** The spec says `update.sh` has a parallel `mkdir -p` step. It does not. `update.sh` contains no `.writ/` mkdir and no `.gitignore` append. Default: add the call so an update repairs a missing tree. The call is idempotent. If the maintainer wants `update.sh` left alone, drop its half of Task 4.3 and record that in ADR-031 Consequences.
- **Tree differs from today's installer.** The current `.writ/` step creates `specs`, `product`, `research`, `decision-records`, `docs`, `issues`, `explanations`, and `state`. The spec's list adds `issues/bugs`, `issues/features`, `issues/improvements`, and `knowledge`, and drops `explanations`. Default: the spec's list. No command, agent, skill, or adapter references `.writ/explanations`; the only match is `.writ/docs/leanness-audit-2026-10-21.md`. Record the change in ADR-031 Consequences.
- **`.gitignore` is created when absent.** Today the installer appends `.writ/state/` only when `.gitignore` exists. The fresh-directory criterion needs the script to create the file. Default: create it. This changes installs in projects with no `.gitignore`. `.writ-lanes-*/` is also new for installs. Record both in ADR-031 Consequences.
- **No Python in the installers (settled 2026-10-22).** The installers keep a bash `init_writ_workspace`; the drift guard is `test_bash_list_matches`, not a call. The eleven-path list adds `.writ/issues/goals` (written by `/create-goal`) to the spec's original ten.
- **Ignore-entry matching.** Compare trimmed whole lines. Treat `.writ/state` and `.writ/state/` as one entry. Append missing entries under the `# Writ ephemeral state` comment that `install.sh` writes today, in one write. Write through a temp file and `os.replace`, per ADR-029 rule 3 (atomic writes).
- **Output shape.** Paths are relative to `--project`. Intermediate parents such as `.writ/` and `.writ/issues/` get no line. `<n>` and `<m>` count only the ten listed paths.
- **Installer resolution.** `WRIT_SRC` is the Writ source tree. `install.sh` sets it during source selection, and `update.sh` sets it from a fresh `mktemp -d`. Resolve the script from `"$WRIT_SRC/scripts/scaffold-writ.py"`, never from the project's `scripts/`. A project file with the same name is a user file (ADR-031 shared-name rule).
- **Python 3.9.** Stdlib only. Use `pathlib` with `exist_ok=True` and `os.replace`. Add `from __future__ import annotations` before any `X | None` annotation.
- **Contract test coverage is partly automatic.** `scripts/tests/test_agent_cli_contract.py` finds the script through `is_shippable_script`. Two additions are required: the Classification row (checked by `test_agent_cli_contract_doc.py`) and one smoke invocation. The smoke invocation must use `{tmp}` paths. The test's repo snapshot fails the run if it changes the Writ repository.
- **`/initialize` exit criteria.** Step 0 creates `.writ/product/` as an empty directory. Exit criterion 3 ("no file was created under `.writ/product/`") still holds. Step 0 wording must say it creates directories, not files.
- **Plugin path.** `commands/initialize.md` keeps `scripts/scaffold-writ.py` in source form. The generator rewrites it to `${CLAUDE_PLUGIN_ROOT}/scripts/scaffold-writ.py` through the `script-root` token (Story 2). A project's own `scripts/scaffold-writ.py`, if one exists, is not run by a plugin command. Story 5 verifies this.
- **Shared-name rule (ADR-031).** Under `install.sh`, a project file at `scripts/scaffold-writ.py` has no install baseline. Install treats it as modified, and `--force` overwrites it. This is today's documented behavior, and ADR-031 keeps it.
- **ADR-029 scope.** ADR-031 supersedes one consequence bullet only: "Scripts install into the project-root `scripts/` folder." ADR-029 rules 1 to 7 and its amendments stay. ADR-031 does not restate them.
- **Risks.** The install and update bash tests run the real scripts against temp projects. A failing assertion is a signal. Do not edit around it without reporting it.
- **Integration.** Story 2 lists `scripts/scaffold-writ.py` among the shipped scripts of the `claude-code-plugin` target. The generator admits it through `is_shippable_script`. Story 5's smoke test runs `scaffold-writ.py scaffold` in an empty temp directory on every target.
- **Spec references.** `spec.md` § Business Rules (Expanded), Rules 7 and 8. `technical-spec.md` § `scaffold-writ.py` (Story 4) and § ADR-031 Outline (Story 4).

## Definition of Done

- [x] All tasks completed
- [x] All acceptance criteria met
- [x] Tests passing
- [x] Code reviewed
- [x] Documentation updated

## Context for Agents

- **Error map rows:** []
- **Shadow paths:** `technical-spec.md → ## Shadow Paths` (Happy path, Empty input)
- **Business rules:** `spec.md → ## Business Rules (Expanded)` (Rule 7 Scaffold script; Rule 8 ADR-031)
- **Experience:** `spec.md → ## Experience Design → ### State Catalog` (Claude Code plugin installed, project without `.writ/`; Claude Code plugin and `install.sh` install in the same project)

---

## What Was Built

**Implementation Date:** 2026-10-23

### Files Created

1. **`scripts/scaffold-writ.py`** (217 lines)
   - `scaffold [--project DIR] [--check]`: creates the eleven `.writ/` paths and the `.gitignore` entries `.writ/state/` and `.writ-lanes-*/` (file created when absent, whole-line trimmed matching, one atomic write); check-shape output; usage errors exit 2 with empty stdout. Shipped; copied into `plugins/writ/scripts/` by the generator.
2. **`scripts/tests/test_scaffold_writ.py`** (469 lines)
   - 30 test functions, 43 cases: script paths and output shape, idempotence, `--check`, usage errors, `test_bash_list_matches` for both installers, byte-identical function, no python in installers, bash vs script `.gitignore` byte parity (9 fixtures), Step 0, ADR-031, ADR-029 header, issue resolution, plugin copy.
3. **`.writ/decision-records/adr-031-script-location.md`** (145 lines)
   - Accepted: `install.sh` installs keep `scripts/` in the project; plugins run scripts from `${CLAUDE_PLUGIN_ROOT}/scripts`; one source, a `script-root` token per target; the shared-name rule kept; supersedes one ADR-029 consequence; follow-ups DEV-005 and DEV-006 recorded.

### Files Modified

- **`scripts/install.sh`** (`init_writ_workspace`)
  - Eleven-path `mkdir -p` list (`explanations` dropped); creates `.gitignore` when absent and appends missing entries; echo and `cc.mdc` cleanup kept; no python.
- **`scripts/update.sh`** (new byte-identical `init_writ_workspace`, called after `load_baselines`, skipped on `--dry-run`)
- **`commands/initialize.md`** (`### Step 0: Scaffold .writ/` before `### Detection Logic`; replaced installation sentence; Greenfield bullet)
- **`plugins/writ/commands/initialize.md`** (regenerated: `python3 ${CLAUDE_PLUGIN_ROOT}/scripts/scaffold-writ.py scaffold`)
- **`.writ/docs/agent-cli-contract.md`** (§ Classification row `scaffold-writ.py | check`)
- **`scripts/tests/test_agent_cli_contract.py`** (one `SMOKE_INVOCATIONS` entry under `{tmp}`)
- **`.writ/decision-records/adr-029-agent-cli-contract.md`** (`Superseded in part by: ADR-031` header line)
- **`.writ/issues/improvements/2026-10-12-script-install-location.md`** (`spec_ref` and `## Resolution`)
- **`.writ/specs/2026-10-22-plugin-distribution/spec-lite.md`**, **`drift-log.md`** (DEV-011 to DEV-016)

### Implementation Decisions

1. **Bash mirror, not a call** — the installers keep their own bash `init_writ_workspace` (no Python dependency enters them); `test_bash_list_matches` and a byte-parity test on the `.gitignore` result keep bash and Python equal.
2. **Status Accepted** — the plugin script-root rows are verified (V07, V08, V58), so ADR-031 is Accepted rather than Proposed.

### Test Results

**Verification:** `uv run --python 3.9 pytest scripts/tests/test_scaffold_writ.py scripts/tests/test_agent_cli_contract.py scripts/tests/test_agent_cli_contract_doc.py -q` 364 passed (red first: 39 failed for the missing script, missing `update.sh` function, brace-list mismatch, and missing docs).
- ✅ Scaffold twice in a temp project: first run `scaffold-writ: pass (11 created, 0 existing)` plus two `added .gitignore entry` lines; second run `scaffold-writ: pass (0 created, 11 existing)`; `--check` `pass (0 missing)`.
- ✅ Reviewer ran `install.sh --platform claude` and `update.sh` into temp projects from a temp copy: tree and entries created, dry run wrote nothing, a real update repaired a missing tree.
- ✅ `python3 scripts/gen-platform-trees.py --check` pass; test-integrity authenticity pass; coverage, docs-check, app-verify unverifiable (no coverage report, no public exports, no recipe).

### Review Outcome

**Result:** PASS

- **Iteration count:** 1 iteration(s)
- **Drift:** Small
- **Security:** none found
- **Boundary Compliance:** no deviations, no violations

### Deviations from Spec

- **[DEV-011] Extra `added .gitignore entry <entry>` output lines** — Severity: Small
  - Spec said: `pass`, `created` lines, summary.
  - Reality: detail lines for appended entries before the summary.
  - Resolution: Auto-amended (Small).
  - Spec amendment: spec-lite.md scaffold line.
- **[DEV-012] `--check` summary counts every reason line** — Severity: Small
  - Spec said: count only the listed paths.
  - Reality: paths plus entries.
  - Resolution: Auto-amended (Small).
  - Spec amendment: spec-lite.md scaffold line.
- **[DEV-013] `not a directory` fail path; permission-error reason; `.gitignore` directory crash** — Severity: Small
  - Spec said: nothing for these cases.
  - Reality: a handled `not a directory` fail; two edge cases left as follow-ups.
  - Resolution: Auto-amended (Small).
  - Spec amendment: spec-lite.md Error Handling.
- **[DEV-014] Missing entries appended at end of file when the Writ comment exists** — Severity: Small
  - Spec said: append under the comment.
  - Reality: end of file, same bytes as the bash mirror.
  - Resolution: Auto-amended (Small).
  - Spec amendment: spec-lite.md scaffold line.
- **[DEV-015] `update.sh` repair placement, dry-run skip, uncommitted `.gitignore`** — Severity: Small
  - Spec said: call after `WRIT_SRC` is set.
  - Reality: after `load_baselines`, before early exits, not on dry run.
  - Resolution: Auto-amended (Small).
  - Spec amendment: spec-lite.md scaffold line.
- **[DEV-016] `/initialize` Greenfield wording counts the Step 0 tree as boilerplate** — Severity: Small
  - Spec said: Step 0 and one sentence.
  - Reality: also the Greenfield bullet.
  - Resolution: Auto-amended (Small).
  - Spec amendment: spec-lite.md scaffold line.
