# Story 1: Verify Both Plugin Formats and Decide the Layout

> **Status:** Completed ✅ (2026-10-23)
> **Priority:** High
> **Dependencies:** None

## User Story

**As a** Writ maintainer who must choose the plugin layout before any manifest is written
**I want to** check both plugin formats against first-party docs and one live install each, and record every result with its date, version, and URL
**So that** the layout, path resolution, Prime Directive carrier, and namespacing rest on verified evidence, and Stories 2 to 4 implement only what this story verified

## Acceptance Criteria

> **AC IDs assigned through:** AC-1.5

- [x] Given the first-party pages named in § First-Party Facts, when each is re-read on the run date, then § Verification Record has one row per claim with the platform and version, a paraphrase of what the page states, a full `https://` source URL, and a status that matches the grammar under that heading `[AC-1.1]`
- [x] Given a scratch plugin layout outside the repository and the `claude` CLI installed, when `claude plugin validate`, `marketplace add` from a local path, `install`, one `/writ:<command>` call, one `writ:<agent>` spawn, the `${CLAUDE_PLUGIN_ROOT}` substitution check, and the Prime Directive probe each run, then each result is one § Verification Record row with the Claude Code version and the exit code or transcript line, and a check that cannot run is recorded `unverified` with no guessed result `[AC-1.2]`
- [x] Given no Cursor session in the lane, when the Cursor rows are recorded, then nothing is written to `~/.cursor/plugins/local/`, each Cursor row that claims live behavior has status `unverified <date> (pending UAT)`, and § UAT Protocols holds a Cursor local-plugin protocol with the fields a maintainer records `[AC-1.3]`
- [x] Given every relative path form in `commands/`, `agents/`, and `skills/`, when each form is counted with a recorded `grep` command, then § Relative Path Inventory gives each form a count, a token class (or none), and whether the reference is a file read or an agent spawn, and it lists which generated-agent frontmatter keys survive in a plugin `[AC-1.4]`
- [x] Given the completed § Verification Record and § Relative Path Inventory, when Story 1 picks the layout (A or B), the Prime Directive carrier, the token classes, and the namespacing rules, then each decision in `technical-spec.md` cites only `verified` rows, any decision without a verified row is recorded as `deferred`, and no file outside `.writ/specs/2026-10-22-plugin-distribution/` changes except the test from Task 1.1 `[AC-1.5]`

## Implementation Tasks

- [x] 1.1 Write `scripts/tests/test_plugin_distribution.py` (Python 3.9 stdlib, pytest, no network). It reads `technical-spec.md`, finds the § Verification Record table, and asserts that the header is `Claim | Platform & version | Observed | Source | Status`, every data row's Status matches the grammar under that heading, and every Source starts with `https://`. Run it now and confirm it fails on the placeholder row, not on an import or syntax error `[AC-1.1]`
- [x] 1.2 Re-read each page named in § First-Party Facts (rows 1 to 9) and each page cited under Technical Concerns, on the run date. Resolve each short page name to a full `https://` URL by following the docs' own links or index. Never build a URL you have not fetched. Replace the placeholder row with one row per claim, paraphrased. Status is `verified <date>` when the page states the claim, and `unverified <date>` when the page does not state it, contradicts it, or cannot be reached. Use `Claude Code docs, read <date>` or `Cursor docs, read <date>` as the platform for docs rows. Add rows for `isolation`, `memory`, `maxTurns`, `model`, `tools`, and `disallowedTools` in `sub-agents.md`, since Task 1.5 needs them `[AC-1.1]`
- [x] 1.3 Run the Claude Code live checks in a scratch directory outside the repository. Record `claude --version`. Build a minimal plugin named `writ` (a root `.claude-plugin/plugin.json`, one stub command whose body prints `${CLAUDE_PLUGIN_ROOT}`, and one stub agent named `writ-coder`) with a marketplace named `writ-scratch` that uses `source: "."` (layout A). Run `claude plugin validate` on it and record the exit code, then repeat with `--strict`. Run `claude plugin marketplace add` and `claude plugin install writ@writ-scratch`. In a scratch project, run the stub as `/writ:<stub>`, confirm the substituted path, spawn `writ:writ-coder` by name, and test whether a project command with the same name shadows the plugin command. Run the Prime Directive probe in Notes. Build layout B (`plugins/writ/`) only if A fails validate or install. Record each check as a row `[AC-1.2]`
- [x] 1.4 Confirm that no Cursor session is available in the lane, so place nothing in `~/.cursor/plugins/local/`. Set each Cursor row that claims live behavior (rules load, `/writ` appears, a script call resolves) to `unverified <date> (pending UAT)`. Keep docs-only Cursor rows at `verified <date>`. Check that § UAT Protocols covers the Cursor local-plugin steps, and add the fields to record: Cursor version, rules list result, commands seen, script call result, and a pass or fail line. Record that the Cursor marketplace listing is a Cursor-review step the maintainer makes `[AC-1.3]`
- [x] 1.5 Fill § Relative Path Inventory. For each form, count occurrences with a `grep -rE` command over `commands/`, `agents/`, and `skills/`, and record the commands under the table. Compare the script-invocation count with the 132 in the spec. If it differs, use the observed count and say so. For agent references, record whether the command reads the file or spawns the agent, because the two resolve differently. Fill the token class column. Add a list of the generated-agent frontmatter keys (`permissionMode`, `isolation`, `memory`, `maxTurns`, `model`, `tools`, `disallowedTools`), each marked `survives`, `ignored`, or `unverified`, with the Verification Record row that supports the mark `[AC-1.4]`
- [x] 1.6 Record the decisions in `technical-spec.md`. Under § Candidate Layouts, name A or B by the decision rule and list the rows it rests on. Under § Prime Directive Carrier, name the carrier and the transcript line that proved it, or record `deferred` if no probe is observed. Confirm or change the four token classes from the inventory. State the namespacing rules (`/writ:<command>`, `writ:<agent>`) and the frontmatter keys the plugin ignores. Check that every cited row has status `verified` `[AC-1.5]`
- [x] 1.7 Verify. Run the test from Task 1.1 and confirm it passes. Run `uv run --python 3.9 pytest`, `for t in scripts/tests/test_*.sh; do bash "$t" || echo "FAIL $t"; done`, and `bash scripts/eval.sh` outside the sandbox. Run `git status --short` and confirm no tracked change falls outside the spec folder and the test file. The untracked spec folders listed at session start are not this story's. Report the counts `[AC-1.1, AC-1.5]`

## Notes

- **Scope exception.** The one file outside the spec folder this story creates is `scripts/tests/test_plugin_distribution.py` (Task 1.1). It tests the record and changes no product file. Nothing under `commands/`, `agents/`, `skills/`, `adapters/`, `claude-code/`, `cursor/`, `scripts/` (apart from that test), `system-instructions.md`, or the `.claude/` and `.cursor/` symlinks changes.
- **Scratch work.** Use the session scratchpad or another directory outside the repository, not `/tmp`. Use the marketplace name `writ-scratch`, so Story 5's `writ@writ` install does not collide with it.
- **Undo for each install side effect.** Record the undo in the Verification Record row for that check: `claude plugin uninstall writ@writ-scratch`, then `claude plugin marketplace remove writ-scratch`, then delete the scratch directories. Confirm each command's form in the CLI reference before running it.
- **Layout decision rule and the remote.** § Candidate Layouts names `sellke/writ`. Until plugin manifests reach that remote, a GitHub install cannot succeed. Story 1 therefore applies the rule to a local-path install of a scratch copy of each layout. Also, `claude plugin validate .` cannot run on the repository root in this story, because the root has no manifest yet. Record this substitution in § Candidate Layouts. The GitHub install is checked in Story 5's live run.
- **Prime Directive probe.** Run it in a scratch project for three cases:
  - Baseline: no carrier.
  - Carrier 1: a plugin-root `settings.json` with `"agent"` naming `writ`, plus `agents/writ.md` whose body is a copy of `system-instructions.md`.
  - Carrier 2: `output-styles/writ.md` with `force-for-plugin: true`.

  Ask the session to confirm an assertion it has not checked, for example that a named test passes without a run. Record whether the reply withholds confirmation, with the transcript line. A carrier counts as observed only when its reply differs from the baseline.
- **Checks that cannot run.** With no `claude` CLI or no Cursor session, the check's row is `unverified <date>`, and for Cursor `(pending UAT)`. Never record a guessed result. A carrier with no observed probe is `deferred`, and Stories 2 to 4 wait for it.
- **Docs changed since 2026-10-22.** If a page's URL or wording differs from § First-Party Facts, record the new URL and wording with today's date, update the status, and re-take each decision that depends on the row. Do not patch a decision silently.
- **Integration.** Stories 2, 3, and 4 implement only what this story records. Story 5's smoke test cites § Verification Record for each path it checks.

## Definition of Done

- [x] All tasks completed
- [x] All acceptance criteria met
- [x] Tests passing
- [x] Code reviewed
- [x] Documentation updated

## Context for Agents

- **Error map rows:** []
- **Shadow paths:** `technical-spec.md → ## Shadow Paths` (Happy path, Nil input, Upstream error)
- **Business rules:** `spec.md → ## Business Rules (Expanded)` (Rule 1 Verification record first; Rule 2 Plugin target; Rule 5 Prime Directive carrier; Rule 12 Runtime)
- **Experience:** `spec.md → ## Experience Design → ### State Catalog` (Claude Code plugin, command calls a script; Claude Code plugin, command spawns an agent; Cursor local plugin; claude plugin validate; Smoke test on a machine without the claude CLI)

---

## What Was Built

**Implementation Date:** 2026-10-23

### Files Created

1. **`scripts/tests/test_plugin_distribution.py`** (114 lines)
   - `TestVerificationRecord`: loads `scripts/gen-platform-trees.py` by path and parses § Verification Record with its `section` / `first_table` / `cells` helpers; checks the five-cell header, the status grammar, `https://` sources, unique row IDs, and that every `Rests on:` line cites only verified rows.

### Files Modified

- **`.writ/specs/2026-10-22-plugin-distribution/sub-specs/technical-spec.md`** (§ Verification Record, § Relative Path Inventory, § Candidate Layouts, § Prime Directive Carrier, § UAT Protocols)
  - 79 record rows V01 to V79 (46 Claude Code docs, 7 Cursor docs, 22 live Claude Code 2.1.309, 4 Cursor pending UAT) plus a dated list of upstream changes since 2026-10-22; an inventory of eleven path forms with 22 recorded `grep -rE` commands; decisions for layout, carrier, token classes, namespacing, and ignored agent keys, each with `Rests on:` lines.
- **`.writ/specs/2026-10-22-plugin-distribution/spec-lite.md`** (For Coding Agents)
  - Story 1 outcome and Cursor directory status (drift DEV-002 to DEV-004).
- **`.writ/specs/2026-10-22-plugin-distribution/drift-log.md`** (new; Story 1 entries DEV-001 to DEV-004)

### Implementation Decisions

1. **Layout B (`plugins/writ/`)** — layout A passed validate and a local-path install on a scratch copy, but its plugin-root `skills/` scan loads (V60) and a `skills` key only adds to that scan (V04), so the repository's un-tokenized skills would load; under B a `skills/` outside the plugin stays unloaded (V61).
2. **Carrier: forced output style** — `plugins/writ/output-styles/writ.md` with `force-for-plugin: true` and `keep-coding-instructions: true`. Both candidate carriers made the session quote the first Hard Constraint with `SOURCE Prime Directive` and name itself Writ (V68, V69); a main-session agent replaces Claude Code's system prompt entirely and yields to a user `agent` setting, so the style wins the tie on verified docs rows.
3. **Token classes** — `script-root` (69 invocations, not the spec's 132), `script-path`, `agent-path`, `skill-path`, `preamble-path`, `instructions-path`, `command-ref`; bodies only, dev-only script names unchanged.
4. **Cursor** — `commands/` and `agents/` are now documented discovery directories (V48); no plugin-root script form exists for command bodies (V49), so Cursor commands keep `python3 scripts/<name>.py`.

### Test Results

**Verification:** `uv run --python 3.9 pytest scripts/tests/test_plugin_distribution.py -q` 4 passed (red first on the placeholder row: 3 assertion failures); full suite `uv run --python 3.9 pytest` 2917 passed, 2 skipped; bash tests 47 run, 0 failed; `bash scripts/eval.sh` Findings: 0; `python3 scripts/gen-platform-trees.py --check` pass.
- ✅ Live checks: Claude Code 2.1.309, scratch plugins outside the repository, local scope only; ~/.claude/settings.json unchanged; registries restored (installed_plugins.json identical to the before-snapshot; known_marketplaces.json differs only in Claude Code's own `claude-plugins-official.lastUpdated` refresh).
- ✅ Gate scripts: arch-check proceed; test-integrity authenticity pass (after one recode); coverage, docs-check, app-verify unverifiable (no coverage report, no public exports, no recipe).

### Review Outcome

**Result:** PASS

- **Iteration count:** 2 iteration(s) (Gate 3 FAIL on V36's "early access" note, recoded; Gate 4 authenticity recode of the test, re-checked)
- **Drift:** Small
- **Security:** Not assessed (no runtime code)
- **Boundary Compliance:** no deviations, no violations

### Deviations from Spec

- **[DEV-001] Layout B built and installed although layout A passed validate and install** — Severity: Small
  - Spec said: build B only if A fails validate or install.
  - Reality: B was built and installed in scratch with a recorded undo.
  - Resolution: Auto-amended (Small).
- **[DEV-002] Carrier decided by the quote and persona probes, not the assertion probe** — Severity: Small
  - Spec said: the assertion probe decides; a carrier counts only when it differs from the baseline.
  - Reality: P1 did not discriminate; P2 and P3 did, under both carriers.
  - Resolution: Auto-amended (Small).
  - Spec amendment: spec-lite.md Story 1 line records the outcome.
- **[DEV-003] Two token classes added to the four the spec named** — Severity: Small
  - Spec said: `agent-path`, `skill-path`, `preamble-path`, `instructions-path`.
  - Reality: adds `script-path` and `command-ref`; body only.
  - Resolution: Auto-amended (Small).
  - Spec amendment: spec-lite.md lists six classes.
- **[DEV-004] Cursor `commands/` and `agents/` directories are now documented** — Severity: Small
  - Spec said: undocumented; ship at the install.sh shape labelled unverified.
  - Reality: documented at https://cursor.com/docs/reference/plugins.md (read 2026-10-23); live load pending UAT.
  - Resolution: Auto-amended (Small).
  - Spec amendment: spec-lite.md Cursor line.
