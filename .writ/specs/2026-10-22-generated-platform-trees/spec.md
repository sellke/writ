# Generated Platform Trees

> **Status:** Complete
> **Created:** 2026-10-22
> **Owner:** @AdamSellke
> **Dependencies:** [2026-10-22-front-door, 2026-10-22-rendering-delegation-rows]
> **Phase:** 14 — Front Door and Distribution ([roadmap](../../product/roadmap.md), [ADR-030](../../decision-records/adr-030-contract-verifier-boundary-front-door.md))
> **Origin:** Phase 14 decomposition pre-pass (`/implement-phase 14`, 2026-10-22). Finding F6 in `.writ/research/2026-10-19-writ-vs-pstack-research.md` (pstack's `generate-pstack-harness-trees.mjs` is the reference). Closes `.writ/issues/improvements/2026-10-21-adapter-mappings-never-reach-installed-projects.md` and `.writ/issues/improvements/2026-10-22-create-spec-discovery-skips-plan-mode-on-claude-code.md`.

## Specification Contract

**Deliverable:** `scripts/gen-platform-trees.py`, one Python 3.9 driver that generates every per-platform file from source, emits each platform's capability map into its root instruction file, fails on an unmapped capability or a vendor tool name in shipped text, and has a `--check` mode wired into `eval.sh` and CI.

**Must Include:**

1. **One driver, one `--check`.** It owns `cursor/writ.mdc` (generated from `system-instructions.md` plus the map), `claude-code/CLAUDE.md` (via `gen-claude-md.py`, whose template gains the map), `claude-code/agents/` (via `gen-claude-agents.py`), `codex/AGENTS.md.template` (newly generated from the manifest and the map; its stale command and skill lists and its "map tools via `adapters/codex.md`" line go away), and `codex/agents/` (via `gen-codex-agent-tomls.py`). The existing generators and their eval checks stay; the driver calls them and adds one `check_platform_trees`.
2. **Capability map.** The adapter tool tables are parsed by heading; the first column is the capability vocabulary. Each root file gets a generated `## Capability Map` section with that platform's rows and degradation text, so an installed project resolves every capability without `adapters/`.
3. **Coverage check, derivable rule.** A name is neutral if it is a first-column entry; it is vendor-only if it appears as a backticked identifier in a mapping cell and in no first column. Every neutral name must have a row in all four adapters; a vendor-only name in `commands/`, `agents/`, or `skills/` fails. A short, justified allowlist in the script covers identifiers that double as English verbs. Agent CLI check shape. Every vendor hit the first `coverage` run finds on the current tree (on 2026-10-22: `` `Grep` `` and `` `Glob` `` in `commands/create-issue.md`) is rewritten to its neutral name (`codebase_search`, `file_search`) in the same story, one line each, recorded in What Was Built; that rewrite is the structural fix this check exists for, and it is the only prose edit the coverage check may cause.
4. **`Plan Mode` becomes a mapped capability**, one row per adapter, under the decision taken at discovery (2026-10-22): the agent enters it where a tool exists (Claude Code: `EnterPlanMode`, the contract proposal is the plan it exits with, then AskQuestion locks); Cursor asks the user to switch; Codex and OpenClaw run discovery as a read-only conversation and say so. `create-spec.md`, `plan-product.md`, and `new-command.md` each point their discovery step at the adapter's `Plan Mode` row in one sentence. This closes the Plan Mode issue.
5. **Marked tokens.** One token class, `script-root`: the `scripts/<name>.py|.sh` path in an invocation line. The three install targets resolve it to `scripts` (identity), so source stays runnable in this repo and in every install. A target with another root emits a full `commands/` and `skills/` tree into its own output directory; this spec ships the machinery and a fixture target, and `2026-10-22-plugin-distribution` adds the real ones.
6. **Only what differs is committed.** Commands and skills are platform-identical by the coverage check and the identity token, so `install.sh` keeps copying them from source. No duplicated markdown.
7. **Table parity repairs** needed for parsing: `adapters/codex.md` gains the missing `file_search` row; `adapters/openclaw.md`'s `readonly: true` row folds into its `Task` rows; any other first-column name missing from an adapter gets a row. The generated-trees spec owns table structure; the canvas rows from `2026-10-22-rendering-delegation-rows` are read, not rewritten.
8. **Evidence.** A temp-project install on each of `cursor`, `claude`, and `codex` contains the capability map in the file that platform loads every session.

**Hardest Constraint:** Adapter tables were written for humans. The parser must be strict enough to fail loudly on a malformed row and loose enough to read four differently headed tables. Structure changes land here, after `2026-10-22-rendering-delegation-rows` has written its rows and records.

**Success Criteria:** `python3 scripts/gen-platform-trees.py --check` prints `pass` on a clean tree and `fail` with a `reason:` line after a hand edit to any generated file; a vendor name injected into a fixture command fails `coverage`; a fixture target with a non-identity script root rewrites every invocation line and nothing else; temp-project installs on three platforms contain `## Capability Map`; `uv run --python 3.9 pytest`, the bash tests, and `bash scripts/eval.sh` (0 findings) pass.

**Scope out:** plugin manifests and plugin targets (next spec), any change to command prose beyond the token rule, the three Plan Mode sentences, and the vendor-name rewrites the first `coverage` run requires, an OpenClaw install path, rewriting `adapters/*.md` prose outside the tool tables.

## Technical Concerns

*Found while grounding the contract on 2026-10-22. None changes scope.*

- The four tool tables have different headers: `Tool | Used By | Purpose` (cursor), `Cursor Tool | Claude Code Native | Notes` (claude-code), `Cursor / Writ generic | Codex CLI | Notes` (codex), `Cursor Tool | OpenClaw Equivalent | Notes` (openclaw). The parser keys on the section heading per adapter and takes column 1 as the capability and column 2 as the mapping (for cursor, column 3, since column 1 is the tool itself). First-column cells carry call syntax (`Task({ prompt })`, `AskQuestion()`); the capability name is the leading identifier, so `Task({ readonly: true })` and `Task({ resume: id })` are variants of `Task` and render as sub-rows in the map.
- Parity gaps today: `file_search` has no Codex row; `readonly: true` is an OpenClaw-only first-column entry; `Plan Mode` has no row anywhere although six commands use it. The check would fail on the current tree, which is the point; Story 1 repairs the tables first.
- `gen-claude-md.py` is dev-only (`is_shippable_script` denylist) and renders from the manifest with no adapter input today. The map section is a new template slot filled by a function the driver exposes. `scripts/_archival_hook_model.py` is the precedent for a shared module under `scripts/`; underscore-prefixed files are not shipped.
- `codex/AGENTS.md.template` today lists 28 commands (missing `create-goal`, `implement-phase`, `revert`, and after the front door `writ`) and one skill of sixteen. Codex's AGENTS.md budget is 32 KiB; the generated template with every command, agent, skill, and the map is estimated under 12 KiB and the test caps it at 16 KiB.
- `cursor/writ.mdc` is today a hand copy of `system-instructions.md` with `alwaysApply: true`; `check_prime_directive_sync` diffs their Prime Directive sections. Generating `writ.mdc` makes that check pass by construction; it stays as a cheap independent guard.
- `scripts/eval-leanness.py` counts `commands/`, `agents/`, `skills/`, `adapters/`, `scripts/`, and `system-instructions.md`; generated directories are not surfaces, so nothing new needs excluding. The map adds about 15 lines to each root file.
- 132 script invocation lines in `commands/` match the `script-root` pattern (`python3 scripts/<name>.py`, `bash scripts/<name>.sh`). Prose mentions of `scripts/` outside invocation lines are not tokens and are never rewritten.
- The front-door spec lands before this one, so the generated catalogs include `/writ`; this spec's generated Codex template and `--check` must agree with the front-door spec's hand edits to `codex/AGENTS.md.template` at the moment of takeover (the generator replaces the hand-maintained file; its first run is the baseline).

## Experience Design

### Who uses it

- **A user of an installed project** on any platform whose agent reaches a capability name in a command and finds the platform's mapping in the file it already loads.
- **The maintainer** who adds a capability row, a command, or an agent and runs one command to regenerate everything, with CI catching what they forgot.
- **The plugin spec** that needs a full tree with a different script root.

### Journey

1. Entry: the maintainer edits `adapters/claude-code.md` (a new row) or `agents/coding-agent.md`, then runs `python3 scripts/gen-platform-trees.py`.
2. Happy path: the driver rewrites `cursor/writ.mdc`, `claude-code/CLAUDE.md`, `claude-code/agents/*.md`, `codex/AGENTS.md.template`, `codex/agents/*.toml`; prints `pass`, one `wrote <path>` line per file, and a summary.
3. Moment of truth: the maintainer forgets to regenerate. `bash scripts/eval.sh` fails with `stale cursor/writ.mdc` and names the regenerate command.
4. Feedback: check shape on every run (verdict line, `reason:` lines, summary line); nothing is written when any reason exists.

### State Catalog

| State | What the maintainer or user sees |
|---|---|
| Clean tree | `--check` prints `pass`, `gen-platform-trees: pass (0 stale, 0 missing, 0 unmapped, 0 vendor)`. |
| Hand edit to a generated file | `fail`, `reason: stale <path>`, remedy names `python3 scripts/gen-platform-trees.py`. |
| Capability used in a command with no row in one adapter | `fail`, `reason: unmapped <name> in adapters/<x>.md`. |
| Vendor identifier in a shipped command | `fail`, `reason: vendor <name> in commands/<file>.md:<line>`. |
| Malformed table row (wrong column count, empty first cell) | `fail`, `reason: malformed adapters/<x>.md:<line>`; nothing written. |
| Adapter section heading missing | `unverifiable`, `reason: section <heading> in adapters/<x>.md`; exit 0; nothing written. |
| Fixture target with `script_root: ${PLUGIN_ROOT}/scripts` | `commands/` and `skills/` written to `--out-dir`; every invocation line rewritten; prose with `scripts/` untouched. |
| Installed Cursor project | `.cursor/rules/writ.mdc` ends with `## Capability Map` and the Cursor rows. |
| Installed Claude Code project | The `CLAUDE.md` Writ block carries `## Capability Map` with the Claude Code rows. |
| Installed Codex project | The `AGENTS.md` Writ block carries `## Capability Map` with the Codex rows and no reference to `adapters/`. |
| `/create-spec` discovery on Claude Code | The agent calls `EnterPlanMode`; the contract proposal is the plan; AskQuestion locks after exit. |

### Interaction Patterns

- Regenerate, never hand-edit: every generated file opens with a comment naming the generator.
- Check shape everywhere (agent CLI contract): verdict first, one reason per problem, summary last.

## Business Rules (Expanded)

1. **Driver CLI.** `python3 scripts/gen-platform-trees.py [--check] [--target <name>] [--out-dir <dir>] [coverage]`. Default writes all identity targets in place. `--check` writes nothing. `coverage` runs only the coverage check. Exit 0 pass or unverifiable, 1 fail, 2 usage. Dev-only: added to `is_shippable_script`'s denylist beside `gen-claude-md.py`.
2. **Adapter parsing.** Per adapter, one tool-table section by heading: cursor § Native Tool Availability; claude-code § Tool Mapping (Cursor → Claude Code) → Quick Reference; codex § Tool Mapping (Cursor → Codex CLI) → Quick reference — orchestration primitives; openclaw § Quick Reference. The first table under the heading is the tool table. Capability name = leading identifier of column 1 after stripping backticks (`[A-Za-z_][A-Za-z0-9_ -]*` up to `(` or `{`, trimmed; so `Plan Mode` and `canvas-preview` are single names). Mapping = column 2; for cursor, column 3 (Purpose), because column 1 is the tool itself. Notes = last column.
3. **Vocabulary and parity.** Neutral names = union of first-column names across the four adapters. Every neutral name must appear in every adapter; a missing one is `unmapped`. Variants (`Task` with options) count as the base name.
4. **Vendor-only names.** Backticked identifiers in mapping cells that are not neutral names, for example `Grep`, `Glob`, `TodoWrite`, `EnterPlanMode`, `sessions_spawn`, `exec`, `cursor-ide-browser`. A backticked token in `commands/*.md`, `agents/*.md`, or `skills/*/SKILL.md` is matched by its leading identifier (the same normalization as the first column, so `` `Grep("pattern")` `` is a hit for `Grep`); a match on a vendor-only name is `vendor`. Hits found on the current tree are rewritten to the neutral name in Story 4. The allowlist (`Read`, `Write`, `Bash` as bare verbs) lives in the script with one comment per entry; adding to it requires a reason in the commit.
5. **Capability Map section.** Appended to each root file as `## Capability Map`, a table `Capability | On this platform | When unavailable`, one row per neutral name, in the adapter's row order. The "when unavailable" cell is the degradation text when the row has one, else "—". A one-line lead: "Commands name capabilities; this table maps them to this platform."
6. **`cursor/writ.mdc`** = `---\nalwaysApply: true\n---\n` + a generated-file comment + the body of `system-instructions.md` (its own frontmatter stripped) + the map.
7. **`claude-code/CLAUDE.md`** = `gen-claude-md.py` output with a `{capability_map}` slot after the Commands table, filled by the parser.
8. **`codex/AGENTS.md.template`** = the Writ-managed comment, `## Writ on Codex` (one paragraph; "map tools via `adapters/codex.md`" replaced by "the Capability Map below"), command tables by manifest category, agents table, all skills table, the Codex built-ins section (a literal block in the generator), the map, and the catalog-source note. Under 16 KiB (test).
9. **Plan Mode rows** (verbatim mapping cells): cursor "Ask the user to switch to Plan Mode; continue when they have"; claude-code "`EnterPlanMode`; present the contract proposal as the plan; after `ExitPlanMode` approval, lock with AskQuestion"; codex "No agent-side mode: run discovery as a read-only conversation and say so; Codex's `/plan` is user-side"; openclaw "No agent-side mode: run discovery as a read-only conversation and say so". Degradation cell for all: "If the platform has no toggle, say so and proceed read-only."
10. **Command sentences.** `create-spec.md` Step 1.3, `plan-product.md` discovery step, `new-command.md` Step 1.2: one sentence each, "Enter Plan Mode through the adapter's `Plan Mode` row." No other prose change.
11. **Tokens.** `TARGETS` table in the script: `cursor`, `claude-code`, `codex` with `script_root: "scripts"`; `fixture` with `script_root: "${PLUGIN_ROOT}/scripts"` used only by tests. Pattern: `(python3|bash) scripts/([a-z0-9_-]+\.(py|sh))` → `(python3|bash) <script_root>/\2`. Identity targets write no `commands/` or `skills/`; non-identity targets write both under `--out-dir/<target>/`.
12. **Generated-file comment.** Every generated file carries `<!-- generated by scripts/gen-platform-trees.py from <sources> — do not hand-edit; regenerate -->` (TOML: `#` comment). Existing generators keep their own comments.
13. **Eval.** `check_platform_trees` runs `--check` then `coverage`; each `reason:` line becomes a finding with the remedy `python3 scripts/gen-platform-trees.py`. `check_prime_directive_sync` and the three per-generator checks stay.
14. **Install evidence test.** `scripts/tests/test_install_platform_trees.sh`: fresh install on `cursor`, `claude`, `codex` into temp projects from a committed source copy; assert the map in `.cursor/rules/writ.mdc`, the `CLAUDE.md` Writ block, and the `AGENTS.md` Writ block; assert no `adapters/` mention in the Codex block. Never run against the Writ repo.
15. **Runtime.** Python 3.9 standard library, POSIX bash. No network.

## Detailed Requirements

### Story 1: Adapter table parser and parity repairs

- `scripts/gen-platform-trees.py` with `parse_adapter(path) -> AdapterTable` (rows, names, mappings, notes, line numbers) and `vocabulary(adapters) -> (neutral, vendor_only)`; fixture adapters under `scripts/tests/fixtures/platform-trees/` for the malformed, missing-section, and parity cases.
- Repairs: Codex `file_search` row; OpenClaw `readonly: true` folded into `Task({ readonly: true })`; `Plan Mode` row in all four (Rule 9); the three command sentences (Rule 10); `## Resolution` on the Plan Mode issue.

### Story 2: Driver write mode for Cursor and Claude Code root files

- `write` for `cursor/writ.mdc` (Rule 6) and the `{capability_map}` slot in `gen-claude-md.py` (Rule 7); the driver calls `gen-claude-agents.py` and `gen-codex-agent-tomls.py` and aggregates their check output.
- Generated-file comments (Rule 12). Tests on a temp copy of the tree.

### Story 3: Generated Codex template

- `codex/AGENTS.md.template` from the manifest, the skills directory, the built-ins literal, and the map (Rule 8); the first generated file is diffed against the hand-maintained one and the diff recorded in What Was Built; size test.

### Story 4: `--check`, coverage, tokens, and eval wiring

- `--check` (stale, missing, orphan per generated path); `coverage` (unmapped, vendor, allowlist); `TARGETS` with the fixture target and `--out-dir` writing `commands/` and `skills/` (Rule 11); `check_platform_trees` in `eval.sh` with a bash test in the style of `test_eval_claude_md.sh`; `is_shippable_script` denylist entry in `install.sh` and `update.sh`.

### Story 5: Install evidence and issue closure

- `scripts/tests/test_install_platform_trees.sh` (Rule 14); `## Resolution` on the adapter-mappings issue with the three observed install paths; `adapters/codex.md` and `adapters/claude-code.md` install sections no longer tell users to read `adapters/`.

## Implementation Approach

- **Order.** Stories 1 → 2 → 3 → 4 → 5, each depending on the previous. Story 1 must land before anything parses the tables.
- **Takeover of hand-maintained files.** The first `write` of `cursor/writ.mdc` and `codex/AGENTS.md.template` replaces hand-maintained content. Diff each against the previous file and record what changed in the story's What Was Built; a lost sentence is a bug, not drift.
- **Check shape.** Follow `scripts/gen-claude-agents.py`'s output contract exactly, so `eval.sh` parses reasons the same way.
- **Verification.** `uv run --python 3.9 pytest`, the bash test loop, and `bash scripts/eval.sh` (outside the sandbox) after every story.
