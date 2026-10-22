# Technical Spec: Plugin Distribution

> Spec: [`../spec.md`](../spec.md) · Issue: [`script-install-location`](../../../issues/improvements/2026-10-12-script-install-location.md) · Research: [`2026-10-19-writ-vs-pstack-research.md`](../../../research/2026-10-19-writ-vs-pstack-research.md) F6, Further Research 1

## Current State (audit, 2026-10-22)

- Distribution is `scripts/install.sh --platform cursor|claude|codex` (copies commands, platform agents, skills, `system-instructions.md`, `cursor/writ.mdc`, the Writ block templates, shipped scripts into `scripts/`, shipped docs into `.writ/docs/`; creates `.writ/`; adds `.writ/state/` to `.gitignore`; commits). `scripts/update.sh` overlays with a manifest. No plugin manifests exist.
- Shipped scripts: the set `is_shippable_script` admits (`*.py`, `*.sh` minus the dev-only denylist, plus `jev-thresholds.json`). Commands invoke them as `python3 scripts/<name>.py` / `bash scripts/<name>.sh` (132 lines).
- After `2026-10-22-generated-platform-trees`: `gen-platform-trees.py` has a `TARGETS` table with one token class (`script-root`) and a `fixture` non-identity target that writes `commands/` and `skills/` to an out-dir.
- `commands/initialize.md` assumes `.writ/` exists.

## First-Party Facts Read on 2026-10-22 (re-verify in Story 1)

| # | Claim | Source | Confidence |
|---|---|---|---|
| 1 | `.claude-plugin/plugin.json`: only `name` required; `commands` path/array/object replaces the default scan; `agents` `.md` paths only; `skills` adds to the default scan; paths start `./` and stay inside the root | https://code.claude.com/docs/en/plugins/manifest-reference.md | high |
| 2 | `${CLAUDE_PLUGIN_ROOT}` substituted in command, skill, and agent bodies and in hook/MCP config; not in the Bash environment; `scripts/` is a convention; `bin/` goes on PATH | manifest-reference.md, components.md, skills.md | high |
| 3 | Plugin commands invoked as `/writ:<name>`; project commands do not collide | components.md, skills.md | high (form), medium (collision) |
| 4 | Plugin agents named `writ:<name>`, lowest collision priority; `hooks`, `mcpServers`, `permissionMode`, `initialPrompt` ignored | sub-agents.md | high |
| 5 | `.claude-plugin/marketplace.json`: `name`, `owner.name`, `plugins[{name, source}]`; sources `./path`, github repo, url; add via `claude plugin marketplace add owner/repo`; install `claude plugin install <plugin>@<marketplace>` | marketplace-reference.md, install.md, host-marketplace.md | high |
| 6 | Repo as both marketplace and plugin: undocumented; schema accepts source `"."` | marketplace-reference.md | medium |
| 7 | `claude plugin validate <path>`: exit 0/1/2, `--strict` | cli-reference.md | high |
| 8 | Plugin-root `CLAUDE.md` not loaded; `settings.json` `"agent"` runs the main thread as that agent (its system prompt applies); `output-styles/*.md` `force-for-plugin: true` | memory.md, components.md, output-styles.md | high / medium |
| 9 | Cursor: `.cursor-plugin/plugin.json` needs only `name`; `rules/`, `skills/`, `mcp.json`; agents/commands/hooks dirs undocumented; local plugins in `~/.cursor/plugins/local`; marketplace listing by Cursor review; `${CURSOR_PLUGIN_ROOT}` only in `mcp.json` | https://cursor.com/docs/plugins | medium |

## Verification Record (Story 1 writes)

| Claim | Platform & version | Observed | Source | Status |
|---|---|---|---|---|
| (one row per claim above, plus: a live `marketplace add` from a local path; `install`; `/writ:writ` runs; a `writ:writ-coder` spawn by namespaced name; `${CLAUDE_PLUGIN_ROOT}` substituted in a command body; the Prime Directive carrier observable; each generated-agent frontmatter key `isolation`, `memory`, `maxTurns`, `model`, `tools`, `disallowedTools` honored or ignored in a plugin; whether a Cursor command body can use `${CURSOR_PLUGIN_ROOT}`; Cursor local plugin loads rules and commands) | | | | |

Status grammar: `^(verified|unverified) \d{4}-\d{2}-\d{2}( \((pending UAT|no deployment)\))?$`.

## Relative Path Inventory (Story 1 fills; Story 2 implements)

| Form | Example | Count | Resolves under plugin to | Token class |
|---|---|---|---|---|
| script invocation | `python3 scripts/spec-status.py` | 132 | `${CLAUDE_PLUGIN_ROOT}/scripts/…` | `script-root` (exists) |
| agent reference | `agents/coding-agent.md` | | plugin `agents/` or the namespaced agent name | `agent-path` |
| skill read | `skills/tdd-cycle/SKILL.md` | | `${CLAUDE_PLUGIN_ROOT}/skills/…` | `skill-path` |
| preamble link | `commands/_preamble.md` | | `${CLAUDE_PLUGIN_ROOT}/commands/_preamble.md` | `preamble-path` |
| system instructions | `system-instructions.md` | | `${CLAUDE_PLUGIN_ROOT}/system-instructions.md` | `instructions-path` |
| project docs | `.writ/docs/x.md` | | project (unchanged) | none |

## Candidate Layouts (Story 1 picks one)

**A. Repository root is the plugin.** `.claude-plugin/plugin.json` at root with `commands: ./claude-code/plugin/commands`, `agents: [./claude-code/agents/*.md]`, `skills: ./claude-code/plugin/skills` (if skills carry tokens) or default `./skills`; `${CLAUDE_PLUGIN_ROOT}/scripts/` is the repository's `scripts/` (no copy; dev-only scripts present but unreferenced). `marketplace.json` with `source: "."`. Pro: no duplicated scripts. Con: undocumented pattern; plugin install clones the whole repository.

**B. `plugins/writ/` subdirectory is the plugin.** Generated target writes `plugins/writ/{commands,agents,skills,scripts,system-instructions.md,.claude-plugin/plugin.json,settings.json}`; `marketplace.json` at root with `source: ./plugins/writ`. Pro: documented pattern; ships only the shipped set. Con: committed copies of ~60 scripts and 16 skills, kept honest by `--check`.

Decision rule: B is the default. A only if all three hold: `claude plugin validate .` passes; a live install from a local path of a scratch copy works (the remote has no manifest until this spec lands, so the rule is applied to the local copy and the substitution is recorded); the root `skills/` default scan does not load the un-tokenized source skills beside the generated ones. Under A, dev-only scripts are present in the clone but unreferenced (spec Rule 3).

## Prime Directive Carrier (Story 1 picks one)

| Mechanism | How | Check |
|---|---|---|
| `settings.json` `{"agent": "writ"}` + `agents/writ.md` whose body is `system-instructions.md` | main thread runs as that agent | In a scratch project, ask the session to confirm an assertion without evidence; the hard constraint fires. Record the transcript line. |
| `output-styles/writ.md` with `force-for-plugin: true` | style instructions sent with every request | same probe |

## `scaffold-writ.py` (Story 4)

```
python3 scripts/scaffold-writ.py scaffold [--project <dir>] [--check]
```

Creates the eleven paths `.writ/specs`, `.writ/product`, `.writ/research`, `.writ/decision-records`, `.writ/docs`, `.writ/knowledge`, `.writ/state`, `.writ/issues/bugs`, `.writ/issues/features`, `.writ/issues/improvements`, `.writ/issues/goals`; appends `.writ/state/` and `.writ-lanes-*/` to `.gitignore` when missing, creating the file when absent. Idempotent. Check shape: `pass`, `created <path>` lines, `gen`-style summary; `--check` reports `missing <path>` without writing. Installers: `install.sh` `init_writ_workspace` (the "📁 Creating .writ/ directory structure" step) changes its `mkdir -p` list to the same eleven paths and creates `.gitignore` when absent; `update.sh` gains a byte-identical `init_writ_workspace` (it has no scaffold step today) so an update repairs a missing tree; neither installer calls `python3`. `test_scaffold_writ.py::test_bash_list_matches` extracts the `mkdir -p` line from both installers and asserts the expanded path set equals the script's `PATHS`.

`commands/initialize.md` gains Step 0: run the script, report `created` lines, continue.

## ADR-031 Outline (Story 4)

Title: Script Location Under Two Install Paths. Decision: `install.sh` installs keep shipped scripts in the project's `scripts/`; plugin installs run them from the plugin root via `${CLAUDE_PLUGIN_ROOT}`; commands carry a `script-root` token resolved per target. Shared-name rule: a project file at a shipped script's path keeps today's behavior (no baseline, treated as modified, `--force` overwrites). Consequences: two resolved forms of every command, one source; `--check` guards both. Supersedes the "Scripts install into the project-root `scripts/` folder" consequence in ADR-029.

## Smoke Test (`scripts/tests/test_plugin_smoke.sh`, Story 5)

| Target | Setup | Commands path | Script root | Instructions | Scaffold |
|---|---|---|---|---|---|
| `cursor` | `install.sh` into temp project | `.cursor/commands/` | `scripts/` | `.cursor/system-instructions.md`, `.cursor/rules/writ.mdc` | `scaffold-writ.py --check` passes after install |
| `claude` | `install.sh --platform claude` | `.claude/commands/` | `scripts/` | `.claude/system-instructions.md` imported by the `CLAUDE.md` block | same |
| `codex` | `install.sh --platform codex` | `.codex/commands/` | `scripts/` | Writ block in `AGENTS.md` | same |
| `claude-plugin` | the plugin directory from the chosen layout | its `commands/` | its `scripts/` | the carrier file | `scaffold-writ.py scaffold` in an empty temp dir |
| `cursor-plugin` | the Cursor layout directory | its `commands/` (or as documented) | per Story 1; with the identity `scripts/` form, checked in a temp project holding `install.sh`'s script copy and reported `pass (requires project scripts/)` | `rules/writ.mdc` | same |

Per target: every `commands:` entry in the manifest has a file; `python3 <root>/scripts/spec-status.py --help` exits 0; the instructions file exists; scaffold check passes. `claude-plugin` adds `claude plugin validate <dir>` when `command -v claude` succeeds, else prints `unverifiable (no claude CLI)` for that check only.

## UAT Protocols (Story 3 and Story 5 write)

- **Cursor local plugin:** copy the Cursor layout to `~/.cursor/plugins/local/writ`, reload, open a sample project; confirm the rules file loads (the Prime Directive is visible in the session's rules list), `/writ` appears, and a command that calls a script resolves. Record the Cursor version and the observation in `adapters/cursor.md` § Plugin.
- **Claude Code plugin live run:** `claude plugin marketplace add sellke/writ`; `claude plugin install writ@writ`; in an empty temp project run `/writ:initialize` then `/writ:writ "add a health endpoint"`; record the transcript lines showing the scaffold and the route.

## Shadow Paths

- **Happy path:** validate passes; install works; `/writ:writ` routes; scripts resolve from the plugin root.
- **Nil input:** no `claude` CLI on the test machine → that check `unverifiable`; the rest of the target runs.
- **Empty input:** project with no `.writ/` → `/writ:initialize` scaffolds; other commands say to run it.
- **Upstream error:** platform docs changed since 2026-10-22 → the record row says so with the new URL; the layout decision is re-taken, never patched silently.

## Error & Rescue Map

Not required: no runtime data flow. The failure surface is install-time and covered by the smoke test's per-target checks.
