# Story 2: Claude Code Plugin

> **Status:** Completed ✅ (2026-10-23)
> **Commit:** bc7e964c41fd0705dc601113e67f5d243b8ef587
> **Priority:** High
> **Dependencies:** Story 1

## User Story

**As a** new Claude Code user working in any project
**I want to** run `claude plugin marketplace add sellke/writ`, then `claude plugin install writ@writ`, then `/writ:writ "<request>"`
**So that** Writ's commands, agents, and system instructions load from the plugin, its scripts run from the plugin root, and I copy nothing into my project

## Acceptance Criteria

> **AC IDs assigned through:** AC-2.5

- [x] Given the `VERSION` file and the layout Story 1's Verification Record marks verified, when the plugin manifest and `marketplace.json` are read, then the manifest has `name` `writ`, a `description`, an `author`, and a `version` equal to `VERSION`; and `marketplace.json` has `name`, `owner.name`, and one `plugins[]` entry named `writ` whose `source` is the form the record verified `[AC-2.1]`
- [x] Given the `claude-code-plugin` target in `scripts/gen-platform-trees.py`, when it writes the plugin tree, then every script call in a command or skill body reads `${CLAUDE_PLUGIN_ROOT}/scripts/<name>`, every agent spawn names `writ:<agent>`, every command cross-reference reads `/writ:<command>`, the plugin root's `scripts/` holds only the set `is_shippable_script` admits, and `--check` reports a `reason:` line for any generated plugin file that differs from a fresh render `[AC-2.2]`
- [x] Given `system-instructions.md` and the Prime Directive carrier the record names, when the plugin tree is generated, then the carrier's body equals `system-instructions.md`'s body, and editing either file without regenerating makes `--check` fail `[AC-2.3]`
- [x] Given `claude` on the `PATH`, when the plugin test runs, then `claude plugin validate <plugin dir>` exits 0; given no `claude` on the `PATH`, then that test reports `skip` with reason `no claude CLI` `[AC-2.4]`
- [x] Given `adapters/claude-code.md` § Installation, when its `### Plugin` subsection is read, then it gives both install commands; names the carrier with the date, Claude Code version, and source URL of the observation that proved it; lists each agent frontmatter key the record marks ignored in plugins; and states that a project with both an `install.sh` install and the plugin has both command sets `[AC-2.5]`

## Implementation Tasks

- [x] 2.1 Write failing tests in `scripts/tests/test_plugin_distribution.py`: manifest shape and `version` against `VERSION`; the generated-tree scan (no bare `python3 scripts/<name>.py` or `bash scripts/<name>.sh`, no un-namespaced `writ-<agent>` spawn, no dev-only script under the plugin root's `scripts/`); carrier body equality and `--check` drift; the `claude plugin validate` test with its `command -v claude` skip branch. Each test runs on a temp copy of the tree. Run the file and confirm every non-skipped test fails on the current tree `[AC-2.1, AC-2.2, AC-2.3, AC-2.4]`
- [x] 2.2 Write `.claude-plugin/plugin.json` and `.claude-plugin/marketplace.json` at the layout's root. Under layout A the manifest sits at the repository root; under layout B it sits at `plugins/writ/.claude-plugin/plugin.json` and the marketplace stays at the root. Generate `version` from `VERSION`. Make the manifest test from 2.1 pass `[AC-2.1]`
- [x] 2.3 Add the `claude-code-plugin` target to the existing `TARGETS` table in `scripts/gen-platform-trees.py`: `script_root: ${CLAUDE_PLUGIN_ROOT}/scripts`, plus the token classes `agent-path`, `skill-path`, `preamble-path`, `instructions-path` for the forms in § Relative Path Inventory, following the `script-root` pattern. Spell `/writ:<cmd>` and `writ:<agent>`. Compute the shippable set with the rule in `is_shippable_script`, and add a test that the Python set and the bash rule agree on every file in `scripts/`. Commit the generated tree and add it to `--check`. Make the tree test from 2.1 pass `[AC-2.2]`
- [x] 2.4 Generate the carrier the record names: a plugin-root `settings.json` with `agent`, plus the agent file whose body is `system-instructions.md`; or `output-styles/writ.md` with `force-for-plugin: true`. Copy the body after each file's own frontmatter. Add the carrier to `--check` and make the carrier test from 2.1 pass `[AC-2.3]`
- [x] 2.5 Run `claude plugin validate <plugin dir>` on the generated tree and record the exit code and the CLI version in What Was Built. Confirm the validate test from 2.1 passes with the CLI present and reports `skip` (reason `no claude CLI`) with it absent `[AC-2.4]`
- [x] 2.6 Add a `### Plugin` subsection under `## Installation` in `adapters/claude-code.md`: the two install commands; the carrier, with the observation's date, version, and source URL; the ignored-key list from the record; the note that a project with both an `install.sh` install and the plugin has both command sets. Every claim carries a date and a URL `[AC-2.5]`
- [x] 2.7 Verify: `uv run --python 3.9 pytest`; `for t in scripts/tests/test_*.sh; do bash "$t" || echo "FAIL $t"; done` with no `FAIL` lines; `python3 scripts/gen-platform-trees.py --check` prints `pass`; `bash scripts/eval.sh` outside any sandbox reports 0 findings `[AC-2.1, AC-2.2, AC-2.3, AC-2.4, AC-2.5]`

## Notes

- **Spec-level dependency.** `2026-10-22-generated-platform-trees` must be integrated before this story runs: it provides `scripts/gen-platform-trees.py`, its `TARGETS` table, the `TOKEN` pattern, and `--check`. The spec header declares it; the story-level line above lists stories only.

**Preconditions.** Both are unmet on 2026-10-22. Do not start until both hold.

- Story 1's Verification Record (`sub-specs/technical-spec.md` § Verification Record) has no rows. The layout (§ Candidate Layouts), carrier (§ Prime Directive Carrier), namespacing, and ignored-key list are undecided. Each decision row must read `verified <date>`.
- `scripts/gen-platform-trees.py` does not exist. Its `TARGETS` table, `script-root` token, and `--check` come from `2026-10-22-generated-platform-trees`, which is Not Started. This story extends that generator. It does not create a second one.

**Technical considerations**

- Manifest location depends on the layout. Layout A puts `.claude-plugin/plugin.json` at the repository root. Layout B puts it under `plugins/writ/`. The "repository root" wording in the spec applies to layout A only.
- `is_shippable_script` is bash, in `scripts/install.sh`. The generator is Python. One rule must serve both. Task 2.3's agreement test guards against drift.
- Token classes rewrite only the forms listed in § Relative Path Inventory. Project paths such as `.writ/docs/` stay unchanged.
- Generated agents come from `scripts/gen-claude-agents.py` (overlay frontmatter in `claude-code/agents/writ-*.md`). Do not hand-edit them.
- The candidate ignored keys in § Technical Concerns (`hooks`, `mcpServers`, `permissionMode`, `initialPrompt`) are unverified. The adapter lists only the keys the record verifies.
- A skipped validate test is not a pass. Story 5's smoke test reports `unverifiable` for the same case.

**Risks**

- Layout A conflicts with Business Rule "Scripts in the plugin." Under A the plugin root is the whole repository, so dev-only scripts ship inside the plugin. The rule says they never do. Story 1 must pick layout B, or the spec must amend the rule before this story starts.
- Layout A also loads the repository's root `skills/`, because the `skills` key adds to the default scan. Those files carry unrewritten `scripts/` calls. The record must account for this.
- A token class that rewrites prose. Mitigation: the tree test in 2.1 checks that only inventory forms change.
- Ignored agent keys: overlay values such as `permissionMode` do not apply in plugins. Do not drop them without a record row. Document them in the adapter.
- A marketplace `source` the live install rejects. The `source` value comes only from the record.

**Integration**

- Story 1's record is the only authority for layout, carrier, namespacing, and ignored keys. If platform docs change, the record row gets the new URL and the decision is retaken, never patched silently (§ Shadow Paths, Upstream error).
- Story 3 (Cursor) reuses the token classes from task 2.3.
- Story 5 adds `claude plugin validate` to the `claude-plugin` target of `scripts/tests/test_plugin_smoke.sh`. The validate test in this story is separate from that smoke test.
- The front-door command under the plugin is `/writ:writ`.

---

## Definition of Done

- [x] All tasks completed
- [x] All acceptance criteria met
- [x] Tests passing
- [x] Code reviewed
- [x] Documentation updated

## Context for Agents

- **Error map rows:** []
- **Shadow paths:** `technical-spec.md → ## Shadow Paths` (Happy path, Nil input, Upstream error)
- **Business rules:** `spec.md → ## Business Rules (Expanded)` (Rule 1 Verification record first; Rule 2 Plugin target; Rule 3 Scripts in the plugin; Rule 4 Agents in the plugin; Rule 5 Prime Directive carrier; Rule 12 Runtime)
- **Experience:** `spec.md → ## Experience Design → ### State Catalog` (Claude Code plugin, command calls a script; Claude Code plugin, command spawns an agent; Claude Code plugin and `install.sh` install in the same project; `claude plugin validate .`; Smoke test on a machine without the `claude` CLI)

---

## What Was Built

**Implementation Date:** 2026-10-23

### Files Created

1. **`.claude-plugin/marketplace.json`** (14 lines)
   - Generated marketplace: `name` writ, `owner.name`, one entry `writ` with `source: "./plugins/writ"`.
2. **`plugins/writ/`** (104 files, generated, no symlinks)
   - `.claude-plugin/plugin.json` (version from `VERSION`, 0.43.0; `commands` lists 33 commands without `_preamble.md`; `agents` lists the 8 `writ-*.md`), `commands/` (34), `agents/` (8 prompt-template docs + 8 Claude agents rendered through gen-claude-agents' `render()`), `skills/` (16), `scripts/` (35 byte copies of the `is_shippable_script` set, modes kept), `system-instructions.md`, `output-styles/writ.md` (the carrier).

### Files Modified

- **`scripts/gen-platform-trees.py`** (`claude-code-plugin` target, token classes, `--check`, write mode)
  - New target with `script_root` `${CLAUDE_PLUGIN_ROOT}/scripts`; `is_shippable_script` mirror; seven body-only token classes (`script-root`, `script-path`, `agent-path`, `skill-path`, `preamble-path`, `instructions-path` link form only, `command-ref`), idempotent, whole-line HTML comments skipped; `--check` reports `stale`/`missing`/`orphan` for every plugin file and the marketplace; write mode writes the tree and removes orphans; symlink guard refuses any link on the plugin or marketplace paths before anything is written or deleted.
- **`scripts/tests/test_plugin_distribution.py`** (new classes beside `TestVerificationRecord`)
  - TestPluginManifest, TestMarketplace, TestTokenClasses, TestPluginTree, TestShippableSet, TestCarrier, TestPluginCheck, TestPluginWriteSafety, TestPluginValidate, TestAdapterPluginSection, TestStory1Record.
- **`adapters/claude-code.md`** (`## Installation` → `### Plugin`)
  - Install commands, validation, namespacing, scripts, carrier with its observation, carrier costs, ignored agent keys, both installs in one project, the `.writ/docs/` gap; each claim dated with a URL.
- **`scripts/tests/test_gen_platform_trees.py`**, **`scripts/tests/test_eval_platform_trees.sh`** (fixture trees copy the plugin inputs and outputs; expectations count the plugin reasons)
- **`scripts/eval-leanness.py`** (`OUT_OF_SCOPE` gains `plugins`, a generated tree like `claude-code/` and `codex/`)
- **`.writ/specs/2026-10-22-plugin-distribution/sub-specs/technical-spec.md`** (inventory row for `system-instructions.md`: dated re-take, link form only)
- **`.writ/specs/2026-10-22-plugin-distribution/spec-lite.md`**, **`drift-log.md`** (DEV-005 to DEV-010)

### Implementation Decisions

1. **Agents rendered, not copied** — the plugin's Claude agents come from gen-claude-agents' `render()` over `agents/*.md`, so a source edit cascades into `--check` without reading `claude-code/agents/` from disk.
2. **`_preamble.md` ships as a file, not a command** — the `commands` key lists the 33 real commands (V02), so `/writ:_preamble` does not register (V11) while the `preamble-path` token still resolves.
3. **Carrier note in YAML** — the generated-file note sits as a YAML comment inside the carrier's frontmatter so its body stays byte-equal to `system-instructions.md` (AC-2.3).
4. **Symlink refusal** — write mode refuses any symlink at `.claude-plugin`, `plugins`, `plugins/writ`, the marketplace file, or under the plugin, and re-checks every write and unlink, after review reproduced writes through a linked `commands/` and deletes through a linked plugin root.

### Test Results

**Verification:** `claude --version` 2.1.309 (Claude Code); `claude plugin validate plugins/writ` exit 0, "Validation passed with warnings" (8 "No frontmatter block found" on the prompt-template docs); `claude plugin validate .` exit 0, "Validation passed"; `python3 scripts/gen-platform-trees.py --check` pass (0 stale, 0 missing, 0 orphan, 0 unmapped, 0 vendor).
- ✅ Story tests: `uv run --python 3.9 pytest scripts/tests/test_plugin_distribution.py scripts/tests/test_gen_platform_trees.py` 168 passed (red first: 11 failed, 34 errors for the missing target, helpers, tree, and section); validate tests skip with `no claude CLI` off PATH.
- ✅ Gate scripts: test-integrity authenticity pass; coverage, docs-check, app-verify unverifiable (no coverage report, no public exports, no recipe).

### Review Outcome

**Result:** PASS

- **Iteration count:** 2 iteration(s) (Gate 3 FAIL: write mode followed directory symlinks; recoded with a guard and tests)
- **Drift:** Medium
- **Security:** Major finding closed (write and delete through symlinks)
- **Boundary Compliance:** deviations in test_gen_platform_trees.py, test_eval_platform_trees.sh, eval-leanness.py, and the technical-spec inventory row, each the narrowest fix; no violations

### Deviations from Spec

- **[DEV-005] Self-locating Writ-source scripts resolve their root to the plugin** — Severity: Medium
  - Spec said: the plugin ships the `is_shippable_script` set and runs scripts from its root.
  - Reality: gen-claude-agents.py, gen-codex-agent-tomls.py, check-agent-parity.sh, gen-skill.sh locate their root from their own path, so under the plugin they read and would write inside the plugin.
  - Resolution: Flagged for review.
- **[DEV-006] `.writ/docs/` reference docs are absent in a plugin-only project** — Severity: Medium
  - Spec said: `.writ/docs/` is a project path, unchanged.
  - Reality: the plugin ships none of the format docs install.sh copies; the adapter says so.
  - Resolution: Flagged for review.
- **[DEV-007] Inventory re-take: `instructions-path` rewrites link forms only; comment lines skipped** — Severity: Small
  - Spec said: link and bare forms rewrite.
  - Reality: link form only; bare mentions name installed files.
  - Resolution: Auto-amended (Small).
  - Spec amendment: spec-lite.md token line.
- **[DEV-008] Dev-only script calls stay bare in plugin bodies** — Severity: Small
  - Spec said: a plugin command never references a dev-only script.
  - Reality: record rule "dev-only names unchanged" kept; none ships in `plugins/writ/scripts/`.
  - Resolution: Auto-amended (Small).
  - Spec amendment: spec-lite.md Business Rules.
- **[DEV-009] Prompt-template docs excluded from agent loading by the manifest only** — Severity: Small
  - Spec said: the `agents` key keeps them from loading.
  - Reality: set; runtime loading unverified until Story 5's live run.
  - Resolution: Auto-amended (Small).
  - Spec amendment: spec-lite.md Integration Points.
- **[DEV-010] Story 1 record tests added; marketplace and manifest gain optional fields** — Severity: Small
  - Spec said: AC-2.1 fields.
  - Reality: adds `repository`, `license`, a marketplace `description`, and `TestStory1Record`.
  - Resolution: Auto-amended (Small).
  - Spec amendment: spec-lite.md Files in Scope.
