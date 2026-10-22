# Story 2: Claude Code Plugin

> **Status:** Not Started
> **Priority:** High
> **Dependencies:** Story 1

## User Story

**As a** new Claude Code user working in any project
**I want to** run `claude plugin marketplace add sellke/writ`, then `claude plugin install writ@writ`, then `/writ:writ "<request>"`
**So that** Writ's commands, agents, and system instructions load from the plugin, its scripts run from the plugin root, and I copy nothing into my project

## Acceptance Criteria

> **AC IDs assigned through:** AC-2.5

- [ ] Given the `VERSION` file and the layout Story 1's Verification Record marks verified, when the plugin manifest and `marketplace.json` are read, then the manifest has `name` `writ`, a `description`, an `author`, and a `version` equal to `VERSION`; and `marketplace.json` has `name`, `owner.name`, and one `plugins[]` entry named `writ` whose `source` is the form the record verified `[AC-2.1]`
- [ ] Given the `claude-code-plugin` target in `scripts/gen-platform-trees.py`, when it writes the plugin tree, then every script call in a command or skill body reads `${CLAUDE_PLUGIN_ROOT}/scripts/<name>`, every agent spawn names `writ:<agent>`, every command cross-reference reads `/writ:<command>`, the plugin root's `scripts/` holds only the set `is_shippable_script` admits, and `--check` reports a `reason:` line for any generated plugin file that differs from a fresh render `[AC-2.2]`
- [ ] Given `system-instructions.md` and the Prime Directive carrier the record names, when the plugin tree is generated, then the carrier's body equals `system-instructions.md`'s body, and editing either file without regenerating makes `--check` fail `[AC-2.3]`
- [ ] Given `claude` on the `PATH`, when the plugin test runs, then `claude plugin validate <plugin dir>` exits 0; given no `claude` on the `PATH`, then that test reports `skip` with reason `no claude CLI` `[AC-2.4]`
- [ ] Given `adapters/claude-code.md` § Installation, when its `### Plugin` subsection is read, then it gives both install commands; names the carrier with the date, Claude Code version, and source URL of the observation that proved it; lists each agent frontmatter key the record marks ignored in plugins; and states that a project with both an `install.sh` install and the plugin has both command sets `[AC-2.5]`

## Implementation Tasks

- [ ] 2.1 Write failing tests in `scripts/tests/test_plugin_distribution.py`: manifest shape and `version` against `VERSION`; the generated-tree scan (no bare `python3 scripts/<name>.py` or `bash scripts/<name>.sh`, no un-namespaced `writ-<agent>` spawn, no dev-only script under the plugin root's `scripts/`); carrier body equality and `--check` drift; the `claude plugin validate` test with its `command -v claude` skip branch. Each test runs on a temp copy of the tree. Run the file and confirm every non-skipped test fails on the current tree `[AC-2.1, AC-2.2, AC-2.3, AC-2.4]`
- [ ] 2.2 Write `.claude-plugin/plugin.json` and `.claude-plugin/marketplace.json` at the layout's root. Under layout A the manifest sits at the repository root; under layout B it sits at `plugins/writ/.claude-plugin/plugin.json` and the marketplace stays at the root. Generate `version` from `VERSION`. Make the manifest test from 2.1 pass `[AC-2.1]`
- [ ] 2.3 Add the `claude-code-plugin` target to the existing `TARGETS` table in `scripts/gen-platform-trees.py`: `script_root: ${CLAUDE_PLUGIN_ROOT}/scripts`, plus the token classes `agent-path`, `skill-path`, `preamble-path`, `instructions-path` for the forms in § Relative Path Inventory, following the `script-root` pattern. Spell `/writ:<cmd>` and `writ:<agent>`. Compute the shippable set with the rule in `is_shippable_script`, and add a test that the Python set and the bash rule agree on every file in `scripts/`. Commit the generated tree and add it to `--check`. Make the tree test from 2.1 pass `[AC-2.2]`
- [ ] 2.4 Generate the carrier the record names: a plugin-root `settings.json` with `agent`, plus the agent file whose body is `system-instructions.md`; or `output-styles/writ.md` with `force-for-plugin: true`. Copy the body after each file's own frontmatter. Add the carrier to `--check` and make the carrier test from 2.1 pass `[AC-2.3]`
- [ ] 2.5 Run `claude plugin validate <plugin dir>` on the generated tree and record the exit code and the CLI version in What Was Built. Confirm the validate test from 2.1 passes with the CLI present and reports `skip` (reason `no claude CLI`) with it absent `[AC-2.4]`
- [ ] 2.6 Add a `### Plugin` subsection under `## Installation` in `adapters/claude-code.md`: the two install commands; the carrier, with the observation's date, version, and source URL; the ignored-key list from the record; the note that a project with both an `install.sh` install and the plugin has both command sets. Every claim carries a date and a URL `[AC-2.5]`
- [ ] 2.7 Verify: `uv run --python 3.9 pytest`; `for t in scripts/tests/test_*.sh; do bash "$t" || echo "FAIL $t"; done` with no `FAIL` lines; `python3 scripts/gen-platform-trees.py --check` prints `pass`; `bash scripts/eval.sh` outside any sandbox reports 0 findings `[AC-2.1, AC-2.2, AC-2.3, AC-2.4, AC-2.5]`

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

- [ ] All tasks completed
- [ ] All acceptance criteria met
- [ ] Tests passing
- [ ] Code reviewed
- [ ] Documentation updated

## Context for Agents

- **Error map rows:** []
- **Shadow paths:** `technical-spec.md → ## Shadow Paths` (Happy path, Nil input, Upstream error)
- **Business rules:** `spec.md → ## Business Rules (Expanded)` (Rule 1 Verification record first; Rule 2 Plugin target; Rule 3 Scripts in the plugin; Rule 4 Agents in the plugin; Rule 5 Prime Directive carrier; Rule 12 Runtime)
- **Experience:** `spec.md → ## Experience Design → ### State Catalog` (Claude Code plugin, command calls a script; Claude Code plugin, command spawns an agent; Claude Code plugin and `install.sh` install in the same project; `claude plugin validate .`; Smoke test on a machine without the `claude` CLI)
