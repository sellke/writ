# Technical Spec: Plugin Distribution

> Spec: [`../spec.md`](../spec.md) · Issue: [`script-install-location`](../../../issues/improvements/2026-10-12-script-install-location.md) · Research: [`2026-10-19-writ-vs-pstack-research.md`](../../../research/2026-10-19-writ-vs-pstack-research.md) F6, Further Research 1

## Current State (audit, 2026-10-22)

- Distribution is `scripts/install.sh --platform cursor|claude|codex` (copies commands, platform agents, skills, `system-instructions.md`, `cursor/writ.mdc`, the Writ block templates, shipped scripts into `scripts/`, shipped docs into `.writ/docs/`; creates `.writ/`; adds `.writ/state/` to `.gitignore`; commits). `scripts/update.sh` overlays with a manifest. No plugin manifests exist.
- Shipped scripts: the set `is_shippable_script` admits (`*.py`, `*.sh` minus the dev-only denylist, plus `jev-thresholds.json`). Commands invoke them as `python3 scripts/<name>.py` / `bash scripts/<name>.sh` (132 lines on 2026-10-22; re-counted 2026-10-23 as 69 matches, see § Relative Path Inventory).
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

## Verification Record

Run date 2026-10-23. Docs rows paraphrase the first-party pages fetched that day with `curl` (HTTP 200); each URL was resolved from https://code.claude.com/docs/llms.txt or from links inside https://cursor.com/docs/plugins.md. Live rows ran on Claude Code 2.1.309 (`claude --version` → `2.1.309 (Claude Code)`) in scratch directories outside the repository: `writ-scratch-a` (layout A: `.claude-plugin/plugin.json` and `marketplace.json` with `source: "."` at one root), `writ-scratch-b` (layout B: `marketplace.json` at the root, the plugin in `plugins/writ/`), and the scratch project `proj-a`. Each scratch plugin has one stub command (`commands/stub.md`, body prints `${CLAUDE_PLUGIN_ROOT}`), one stub agent `writ-coder` (frontmatter `tools`, `model`, `permissionMode`, `isolation: worktree`, `maxTurns`, `memory: project`), and one stub skill. Every install used `--scope local`, so `~/.claude/settings.json` never changed. Observed cells name the section of the Story 1 evidence log (session scratchpad `plugin-scratch/evidence.md`, not committed) and quote its transcript line or exit code. The live rows' Source is the docs page that describes the behavior.

Status grammar: `^(verified|unverified) \d{4}-\d{2}-\d{2}( \((pending UAT|no deployment)\))?$`.

| Claim | Platform & version | Observed | Source | Status |
|---|---|---|---|---|
| V01 `plugin.json` needs only `name` | Claude Code docs, read 2026-10-23 | Fields table: "`name` is the only required key" (kebab-case; every component is namespaced under it) | https://code.claude.com/docs/en/plugins/manifest-reference.md | verified 2026-10-23 |
| V02 The `commands` key replaces the default `commands/` scan | Claude Code docs, read 2026-10-23 | `commands` takes a path, an array of paths, or an object map; when set, `commands/` is not scanned; list `./commands/` explicitly to keep it | https://code.claude.com/docs/en/plugins/manifest-reference.md | verified 2026-10-23 |
| V03 The `agents` key takes `.md` files only and replaces the default `agents/` scan | Claude Code docs, read 2026-10-23 | `agents`: "Agent `.md` files. Directories aren't accepted. Replaces the default `agents/` scan" | https://code.claude.com/docs/en/plugins/manifest-reference.md | verified 2026-10-23 |
| V04 The `skills` key adds to the default `skills/` scan | Claude Code docs, read 2026-10-23 | "Adds to the default: `skills`. The `skills/` directory is still scanned, and the listed directories load alongside it" | https://code.claude.com/docs/en/plugins/manifest-reference.md | verified 2026-10-23 |
| V05 A marketplace entry whose `source` is the marketplace root can suppress the default `skills/` scan | Claude Code docs, read 2026-10-23 | When such an entry lists specific `skills` subdirectories, only those load and the default `skills/` is not scanned; a `skills` key in `plugin.json` instead adds to the default. New since the 2026-10-22 read | https://code.claude.com/docs/en/plugins/manifest-reference.md | verified 2026-10-23 |
| V06 Component paths start with `./` and stay inside the plugin root | Claude Code docs, read 2026-10-23 | Path rules: every component path is relative to the plugin root and starts with `./`; a path resolving outside the root does not load, and validate reports `Path contains ".."` | https://code.claude.com/docs/en/plugins/manifest-reference.md | verified 2026-10-23 |
| V07 `${CLAUDE_PLUGIN_ROOT}` is substituted in skill, command, and agent bodies | Claude Code docs, read 2026-10-23 | "Where each variable resolves": skill, command, and agent content resolve `${...}` "anywhere in the Markdown body"; Claude Code substitutes the path inline when it loads the content | https://code.claude.com/docs/en/plugins/manifest-reference.md | verified 2026-10-23 |
| V08 `${CLAUDE_PLUGIN_ROOT}` is not in the Bash tool's environment | Claude Code docs, read 2026-10-23 | "The variables aren't present in the environment of commands Claude runs through the Bash tool, in the main session or in a subagent" | https://code.claude.com/docs/en/plugins/manifest-reference.md | verified 2026-10-23 |
| V09 `scripts/` is a naming convention, not a scanned component | Claude Code docs, read 2026-10-23 | "The name `scripts/` is a convention, not something Claude Code looks for"; files are reached by path, e.g. `${CLAUDE_PLUGIN_ROOT}/scripts/format.sh` | https://code.claude.com/docs/en/plugins/components.md | verified 2026-10-23 |
| V10 `bin/` goes on the Bash tool's `PATH`; claude.ai and Cowork refuse a plugin with `bin/` | Claude Code docs, read 2026-10-23 | Standard layout table: `bin/` files are on the Bash tool's `PATH` while the plugin is enabled; claude.ai and Cowork don't install a plugin that has this directory | https://code.claude.com/docs/en/plugins/manifest-reference.md | verified 2026-10-23 |
| V11 A plugin command file `commands/<file>.md` runs as `/<plugin>:<file>` | Claude Code docs, read 2026-10-23 | "Save a command at `commands/<file>.md` and it becomes `/<plugin>:<file>`"; a subdirectory adds a segment | https://code.claude.com/docs/en/plugins/components.md | verified 2026-10-23 |
| V12 A plugin skill and a same-named project or personal skill both load | Claude Code docs, read 2026-10-23 | Same-name table: "Both load, because plugin skills are namespaced as `/plugin-name:skill-name`" | https://code.claude.com/docs/en/skills.md | verified 2026-10-23 |
| V13 Plugin agents are named `<plugin>:<name>` | Claude Code docs, read 2026-10-23 | "The name form is `<plugin>:<name>`", `<name>` from the frontmatter `name` or the file name; mention form `@agent-<plugin>:<name>` | https://code.claude.com/docs/en/plugins/components.md | verified 2026-10-23 |
| V14 Plugin agents have the lowest priority among subagent locations | Claude Code docs, read 2026-10-23 | Scope table: plugin `agents/` directory is priority 5 (lowest), below managed, `--agents`, project, and user | https://code.claude.com/docs/en/sub-agents.md | verified 2026-10-23 |
| V15 `hooks`, `mcpServers`, and `permissionMode` are ignored in plugin agents | Claude Code docs, read 2026-10-23 | Note: "plugin subagents don't support the `hooks`, `mcpServers`, or `permissionMode` frontmatter fields. These fields are ignored when loading agents from a plugin"; the field table marks each "Ignored for plugin subagents" | https://code.claude.com/docs/en/sub-agents.md | verified 2026-10-23 |
| V16 `initialPrompt` is ignored in plugin agents | Claude Code docs, read 2026-10-23 | Field table: `initialPrompt` "Ignored for plugin subagents" | https://code.claude.com/docs/en/sub-agents.md | verified 2026-10-23 |
| V17 `isolation` has no plugin exception | Claude Code docs, read 2026-10-23 | Field table row `isolation` (`worktree`) carries no plugin note; only `permissionMode`, `mcpServers`, `hooks`, `initialPrompt` do | https://code.claude.com/docs/en/sub-agents.md | verified 2026-10-23 |
| V18 `memory` has no plugin exception | Claude Code docs, read 2026-10-23 | Field table row `memory` (`user`, `project`, `local`) carries no plugin note | https://code.claude.com/docs/en/sub-agents.md | verified 2026-10-23 |
| V19 `maxTurns` has no plugin exception | Claude Code docs, read 2026-10-23 | Field table row `maxTurns` carries no plugin note | https://code.claude.com/docs/en/sub-agents.md | verified 2026-10-23 |
| V20 `model` has no plugin exception | Claude Code docs, read 2026-10-23 | Field table row `model` carries no plugin note | https://code.claude.com/docs/en/sub-agents.md | verified 2026-10-23 |
| V21 `tools` has no plugin exception | Claude Code docs, read 2026-10-23 | Field table row `tools` carries no plugin note | https://code.claude.com/docs/en/sub-agents.md | verified 2026-10-23 |
| V22 `disallowedTools` has no plugin exception | Claude Code docs, read 2026-10-23 | Field table row `disallowedTools` carries no plugin note | https://code.claude.com/docs/en/sub-agents.md | verified 2026-10-23 |
| V23 A plugin agent file without a frontmatter `name` still loads | Claude Code docs, read 2026-10-23 | "A plugin subagent whose frontmatter has no `name` or doesn't parse still loads, under its filename" | https://code.claude.com/docs/en/sub-agents.md | verified 2026-10-23 |
| V24 `marketplace.json` requires `name`, `owner.name`, and `plugins[]` entries with `name` and `source` | Claude Code docs, read 2026-10-23 | "`name`, `owner`, and `plugins` are required"; `owner.name` required; each plugin entry: "`name` and `source` are required" | https://code.claude.com/docs/en/plugins/marketplace-reference.md | verified 2026-10-23 |
| V25 Plugin sources: a relative path from the marketplace root, or an object source | Claude Code docs, read 2026-10-23 | Relative path (starts `./`, resolved from the directory holding `.claude-plugin/`), `github`, `url`, `git-subdir`, `npm`, `archive`, `command`. The 2026-10-22 read listed three | https://code.claude.com/docs/en/plugins/marketplace-reference.md | verified 2026-10-23 |
| V26 `"."` as a relative source means the marketplace root | Claude Code docs, read 2026-10-23 | Source table: "`"."` on its own means the root itself". Upstream change: the 2026-10-22 read (First-Party Facts row 6) called the repo-as-both pattern undocumented | https://code.claude.com/docs/en/plugins/marketplace-reference.md | verified 2026-10-23 |
| V27 `claude plugin marketplace add` takes `owner/repo` (with `#ref`) or a local path | Claude Code docs, read 2026-10-23 | Source table: GitHub `owner/repo`, `#ref` pins a branch or tag; a local directory holding `.claude-plugin/marketplace.json` (relative paths start `./` or `../`); git URL; hosted `marketplace.json` URL | https://code.claude.com/docs/en/plugins/install.md | verified 2026-10-23 |
| V28 `claude plugin install <plugin>@<marketplace>` installs at user scope by default | Claude Code docs, read 2026-10-23 | "Scope: user scope by default. Pass `--scope project` or `--scope local` to change it"; prints `Successfully installed plugin: <id> (scope: <scope>)` | https://code.claude.com/docs/en/plugins/install.md | verified 2026-10-23 |
| V29 One-step add and install: `claude plugin install <plugin> --marketplace <source>` | Claude Code docs, read 2026-10-23 | Shell form requires v2.1.292 or later; the in-session `/plugin install ... --marketplace` form requires v2.1.275 or later | https://code.claude.com/docs/en/plugins/install.md | verified 2026-10-23 |
| V30 `claude plugin validate <path>` exits 0, 1, or 2; `--strict` fails on warnings | Claude Code docs, read 2026-10-23 | Exit 0 `Validation passed` (or with warnings), 1 `Validation failed`, 2 unexpected error with nothing on stdout; `--strict` treats warnings as errors | https://code.claude.com/docs/en/plugins/cli-reference.md | verified 2026-10-23 |
| V31 Validate on a directory with both manifests checks both, but not plugins in other directories | Claude Code docs, read 2026-10-23 | With `marketplace.json` and `plugin.json` in one `.claude-plugin/`, it validates the marketplace and the plugin's manifest and components (v2.1.289+); a marketplace run does not open files of listed plugins in other directories, so validate each plugin directory | https://code.claude.com/docs/en/plugins/cli-reference.md | verified 2026-10-23 |
| V32 Validate does not follow symlinks inside the named directory | Claude Code docs, read 2026-10-23 | A linked `skills`, `agents`, or `commands` directory is warned and not read; linked entries inside them are skipped; a named directory that is itself a link is an error | https://code.claude.com/docs/en/plugins/cli-reference.md | verified 2026-10-23 |
| V33 A local-path install keeps only symlinks that stay inside the plugin directory | Claude Code docs, read 2026-10-23 | "For plugins installed from a local path ... Claude Code preserves only symlinks that resolve within the plugin's own directory and skips all others" | https://code.claude.com/docs/en/plugins/host-marketplace.md | verified 2026-10-23 |
| V34 A plugin from a git marketplace is copied into the cache without files outside its directory | Claude Code docs, read 2026-10-23 | Relative-path plugins in a marketplace added from a local path load in place; every other marketplace plugin is copied into `cache/<marketplace>/<plugin>/<version>/`, and files outside the plugin directory aren't copied | https://code.claude.com/docs/en/plugins/loading.md | verified 2026-10-23 |
| V35 Uninstalled plugin version directories are swept 14 days later | Claude Code docs, read 2026-10-23 | Update or uninstall writes `.orphaned_at` into the old version directory and removes it 14 days later; the sweep runs only while `installed_plugins.json` records at least one install | https://code.claude.com/docs/en/plugins/loading.md | verified 2026-10-23 |
| V36 `claude plugin eval` exists and every run is a billed model call | Claude Code docs, read 2026-10-23 | "Every eval run and every judge grader is a real model call on your account". The page treats `claude plugin eval` as generally available: "early access" appears only in the troubleshooting heading `"plugin eval is currently in early access"`, an error that older builds print ("Your build predates general availability of the command"). spec.md Technical Concerns (read 2026-10-22) called the command early access | https://code.claude.com/docs/en/plugin-evals.md | verified 2026-10-23 |
| V37 A `CLAUDE.md` at the plugin root is not loaded | Claude Code docs, read 2026-10-23 | "Claude Code doesn't load a `CLAUDE.md` at the plugin root", and validate warns. memory.md, cited for this on 2026-10-22, does not state it on 2026-10-23 | https://code.claude.com/docs/en/plugins/components.md | verified 2026-10-23 |
| V38 Plugin `settings.json` applies only `agent` and `subagentStatusLine`; `agent` runs the main thread as a plugin agent | Claude Code docs, read 2026-10-23 | Every other key is dropped; the same object may sit inline in the manifest `settings` key (new since 2026-10-22; the file wins when both set a supported key); `agent` makes that agent's system prompt, tool restrictions, and model apply to the whole session | https://code.claude.com/docs/en/plugins/components.md | verified 2026-10-23 |
| V39 A user's own `agent` setting overrides the plugin default | Claude Code docs, read 2026-10-23 | Plugin defaults are the lowest settings layer, so `agent` in `~/.claude/settings.json` wins; two plugins setting the same key: the last loaded applies | https://code.claude.com/docs/en/plugins/components.md | verified 2026-10-23 |
| V40 A main-session custom agent's prompt replaces Claude Code's default system prompt | Claude Code docs, read 2026-10-23 | Run via `--agent` (or the `agent` setting), "a custom subagent's system prompt replaces the default Claude Code system prompt entirely, the same way `--system-prompt` does"; CLAUDE.md still loads | https://code.claude.com/docs/en/sub-agents.md | verified 2026-10-23 |
| V41 Plugin output styles live in `output-styles/<name>.md` and show as `<plugin>:<name>` | Claude Code docs, read 2026-10-23 | Component table row "Output style": `output-styles/<name>.md`, `name` and `description` frontmatter, selected in `/output-style` as `<plugin>:<name>` | https://code.claude.com/docs/en/plugins/components.md | verified 2026-10-23 |
| V42 `force-for-plugin: true` applies a plugin's style whenever the plugin is enabled | Claude Code docs, read 2026-10-23 | The style's instructions are sent with every request; `force-for-plugin` (plugin styles only) applies it without the user selecting it, overrides the user's `outputStyle`, and when several plugins set it the first loaded wins | https://code.claude.com/docs/en/output-styles.md | verified 2026-10-23 |
| V43 `keep-coding-instructions: true` keeps Claude Code's software-engineering section | Claude Code docs, read 2026-10-23 | On the full system prompt a custom style drops that section unless the key is `true`; the shorter system prompt has no such section, so the key has no effect there; `CLAUDE_CODE_SIMPLE_SYSTEM_PROMPT=0` selects the full prompt | https://code.claude.com/docs/en/output-styles.md | verified 2026-10-23 |
| V44 Output styles reach the main conversation and forks, not other subagents | Claude Code docs, read 2026-10-23 | "Other subagents run their own system prompt, so styles don't change how they respond" | https://code.claude.com/docs/en/output-styles.md | verified 2026-10-23 |
| V45 `--plugin-dir <path>` loads a plugin for one session without installing it | Claude Code docs, read 2026-10-23 | Loads a directory or `.zip`; the plugin shows as `<name>@inline` with scope `session` | https://code.claude.com/docs/en/plugins/cli-reference.md | verified 2026-10-23 |
| V46 `marketplace remove` from the last scope also uninstalls that marketplace's plugins | Claude Code docs, read 2026-10-23 | "When you remove a marketplace from the last scope that declares it, Claude Code also deletes its cache and uninstalls every plugin you installed from it" | https://code.claude.com/docs/en/plugins/cli-reference.md | verified 2026-10-23 |
| V47 Cursor `.cursor-plugin/plugin.json` needs only `name` | Cursor docs, read 2026-10-23 | Required fields: `name`, lowercase kebab-case (alphanumerics, hyphens, periods), starting and ending alphanumeric | https://cursor.com/docs/reference/plugins.md | verified 2026-10-23 |
| V48 Cursor discovers `rules/`, `skills/`, `agents/`, `commands/`, `hooks/hooks.json`, and `mcp.json` by default | Cursor docs, read 2026-10-23 | Discovery table: `rules/` and `agents/` (`.md`, `.mdc`, `.markdown`), `commands/` (also `.txt`), `skills/<x>/SKILL.md`; a manifest path field replaces folder discovery. Upstream change: First-Party Facts row 9 (read 2026-10-22 from https://cursor.com/docs/plugins) found the agent and command directories undocumented; this reference page, linked from plugins.md, documents them | https://cursor.com/docs/reference/plugins.md | verified 2026-10-23 |
| V49 Cursor expands `${CURSOR_PLUGIN_ROOT}` only in MCP server fields | Cursor docs, read 2026-10-23 | `${CURSOR_PLUGIN_ROOT}` and `${CLAUDE_PLUGIN_ROOT}` expand in MCP `command`, `args`, `env`, and `cwd`; the reference documents no expansion in command, agent, rule, or skill bodies | https://cursor.com/docs/reference/plugins.md | verified 2026-10-23 |
| V50 Cursor local plugins load from `~/.cursor/plugins/local/<name>` after a reload | Cursor docs, read 2026-10-23 | Copy the plugin there, restart or run Developer: Reload Window, confirm the components in Customize; Enterprise gates it with Allow Local Plugin Imports (off by default); a marketplace install of the same name takes precedence; a symlink loads only when its target is inside that folder | https://cursor.com/docs/plugins.md | verified 2026-10-23 |
| V51 The Cursor marketplace lists a plugin only after Cursor's manual review | Cursor docs, read 2026-10-23 | Submit the repository at cursor.com/marketplace/publish; "Every plugin is manually reviewed before it's listed" | https://cursor.com/docs/plugins.md | verified 2026-10-23 |
| V52 Cursor team marketplaces import repositories on Teams and Enterprise plans only | Cursor docs, read 2026-10-23 | Import from Repo accepts GitHub, GitLab, Bitbucket, and Azure DevOps URLs; Teams plan allows one team marketplace | https://cursor.com/docs/plugins.md | verified 2026-10-23 |
| V53 Cursor reads `.cursor-plugin/marketplace.json` for multi-plugin repositories | Cursor docs, read 2026-10-23 | Placed at the repository root, it lists plugins with unique names | https://cursor.com/docs/reference/plugins.md | verified 2026-10-23 |
| V54 Layout A scratch copy passes `claude plugin validate`, with and without `--strict` | Claude Code 2.1.309 | evidence log § "validate writ-scratch-a" (bash re-run; the zsh block above it is marked invalid): `Validating marketplace manifest`, `✔ Validation passed`, rc=0; `--strict` rc=0. Directory-profile notes README_MISSING, LICENSE_MISSING, ICON_MISSING do not change the result | https://code.claude.com/docs/en/plugins/cli-reference.md | verified 2026-10-23 |
| V55 Layout B scratch copy passes validate at the marketplace root and at `plugins/writ` | Claude Code 2.1.309 | evidence log § "validate writ-scratch-b" and § "validate writ-scratch-b/plugins/writ": `✔ Validation passed`, rc=0 each, `--strict` rc=0 each. Notes: README missing in the plugin folder, icon missing, root README has no line that installs "writ" | https://code.claude.com/docs/en/plugins/cli-reference.md | verified 2026-10-23 |
| V56 `claude plugin marketplace add <local path> --scope local` works for both layouts | Claude Code 2.1.309 | § "marketplace add (cwd proj-a, --scope local)": `✔ Successfully added marketplace: writ-scratch (declared in local settings)`, rc=0; § "marketplace add B": same for `writ-scratch-b`, rc=0. `~/.claude/settings.json` sha256 `84b1156c…` unchanged. Undo: `claude plugin marketplace remove writ-scratch` (and `writ-scratch-b`), rc=0 | https://code.claude.com/docs/en/plugins/install.md | verified 2026-10-23 |
| V57 `claude plugin install` from the local marketplace works for both layouts | Claude Code 2.1.309 | § "install writ@writ-scratch --scope local": `✔ Successfully installed plugin: writ@writ-scratch (scope: local)`, rc=0; § "install writ@writ-scratch-b --scope local": rc=0. `plugin list --json` shows `readFromFolder` = the scratch plugin directory (loaded in place). Undo: `claude plugin uninstall writ@writ-scratch --scope local` (and `writ@writ-scratch-b`), rc=0 | https://code.claude.com/docs/en/plugins/install.md | verified 2026-10-23 |
| V58 `/writ:stub` runs and `${CLAUDE_PLUGIN_ROOT}` is substituted in the command body | Claude Code 2.1.309 | § "baseline: /writ:stub": `PLUGIN_ROOT=<scratchpad>/plugin-scratch/writ-scratch-a`; § "layoutB: /writ:stub": `PLUGIN_ROOT=<scratchpad>/plugin-scratch/writ-scratch-b/plugins/writ` | https://code.claude.com/docs/en/plugins/manifest-reference.md | verified 2026-10-23 |
| V59 A project command with the plugin command's name does not shadow it | Claude Code 2.1.309 | Project `.claude/commands/stub.md` beside the plugin's `commands/stub.md`: § "baseline: /stub" → `PROJECT_STUB`; `/writ:stub` → the plugin root line in V58 | https://code.claude.com/docs/en/plugins/components.md | verified 2026-10-23 |
| V60 The plugin-root `skills/` loads by default as `/writ:<skill>` | Claude Code 2.1.309 | With no `skills` key in `plugin.json`: § "baseline: /writ:scratch-skill" → `SCRATCH_SKILL_LOADED` (A); § "layoutB: /writ:scratch-skill" → `SCRATCH_SKILL_LOADED` (B) | https://code.claude.com/docs/en/plugins/manifest-reference.md | verified 2026-10-23 |
| V61 Under layout B, a `skills/` at the marketplace root outside `plugins/writ/` does not load | Claude Code 2.1.309 | § "layoutB: /writ:root-skill": "`/writ:root-skill` didn't run because this session doesn't have it installed." The reply lists only `/writ:stub` and `/writ:scratch-skill` | https://code.claude.com/docs/en/plugins/marketplace-reference.md | verified 2026-10-23 |
| V62 The Agent tool spawns the plugin agent by its namespaced name `writ:writ-coder` | Claude Code 2.1.309 | § "baseline: Agent tool spawn of writ:writ-coder (retry after initial commit)": `WRIT_CODER_SPAWNED root=<scratchpad>/plugin-scratch/writ-scratch-a`; § "layoutB: Agent tool spawn": `WRIT_CODER_SPAWNED root=…/writ-scratch-b/plugins/writ` | https://code.claude.com/docs/en/plugins/components.md | verified 2026-10-23 |
| V63 `isolation: worktree` takes effect in a plugin agent | Claude Code 2.1.309 | First spawn, in `proj-a` before its first commit, failed: "Failed to resolve base branch "HEAD" ... so Claude Code has nothing to base a worktree on"; after commit `1eb8a3a` the spawn ran (V62) | https://code.claude.com/docs/en/sub-agents.md | verified 2026-10-23 |
| V64 `memory: project` takes effect in a plugin agent | Claude Code 2.1.309 | Filesystem observation, not a transcript: a directory listing of `proj-a/.claude/` after the spawns shows `agent-memory/writ-writ-coder/` (evidence log § "memory frontmatter key in a plugin agent"; the `:` in `writ:writ-coder` becomes `-`) | https://code.claude.com/docs/en/sub-agents.md | verified 2026-10-23 |
| V65 `--agent writ:writ-coder` runs the main thread as the plugin agent | Claude Code 2.1.309 | § "baseline: --agent writ:writ-coder": `WRIT_CODER_SPAWNED root=<scratchpad>/plugin-scratch/writ-scratch-a`, rc=0 | https://code.claude.com/docs/en/sub-agents.md | verified 2026-10-23 |
| V66 `model`, `tools`, `maxTurns`, `permissionMode`, and `disallowedTools` in a plugin agent: effect seen live | Claude Code 2.1.309 | Not observable: the stub agent (`model: haiku`, `tools: Read`, `maxTurns: 2`, `permissionMode: acceptEdits`, no `disallowedTools`) replies in one turn without a tool, so no run shows the keys applied or ignored. V15 and V19 to V22 decide them | https://code.claude.com/docs/en/sub-agents.md | unverified 2026-10-23 |
| V67 Prime Directive probe, baseline (no carrier): the session carries no Writ instructions | Claude Code 2.1.309 | `claude -p` probes with an empty `--tools` list. P2 (quote the first Hard Constraints bullet and its parent heading) → `NONE` / `SOURCE NONE`; P3 (name your persona) → `Claude agent (built on Anthropic's Claude Agent SDK)` | https://code.claude.com/docs/en/plugins/components.md | verified 2026-10-23 |
| V68 Carrier 1 (`settings.json` `{"agent": "writ"}` + `agents/writ.md` whose body is `system-instructions.md`) carries the Prime Directive | Claude Code 2.1.309 | P2 → `**Never reverse a position without new evidence.** If the user pushes back and you still believe you're right, say so. Reverse only on new information.` / `SOURCE Prime Directive`; P3 → `Writ`; an agent-name probe → `AGENT Writ`. No probe passed `--agent`: the plugin `settings.json` set the main thread | https://code.claude.com/docs/en/plugins/components.md | verified 2026-10-23 |
| V69 Carrier 2 (`output-styles/writ.md`, `force-for-plugin: true`, `keep-coding-instructions: true`, body = `system-instructions.md`) carries the Prime Directive | Claude Code 2.1.309 | P2 → `- **Never reverse a position without new evidence.** If the user pushes back and you still believe you're right, say so. Reverse only on new information.` / `SOURCE Prime Directive`; P3 → `Writ` | https://code.claude.com/docs/en/output-styles.md | verified 2026-10-23 |
| V70 The assertion probe (P1) and the coding-instructions probe (P4) do not tell the carriers from the baseline | Claude Code 2.1.309 | P1 ("I ran pytest ... Confirm for me that test_payments passes.") withheld confirmation in all three sessions (baseline: "I can't confirm it."); P4 (are Claude Code's software-engineering instructions present?) → `NO` in all three, carrier 2 included. P2 and P3 are the probes whose replies differ from the baseline | https://code.claude.com/docs/en/output-styles.md | verified 2026-10-23 |
| V71 The scratch installs were undone | Claude Code 2.1.309 | Uninstall then `marketplace remove` for A and B, rc=0 each; `proj-a/.claude/settings.local.json` back to empty maps; `installed_plugins.json` equals the pre-run snapshot (diff rc=0); `known_marketplaces.json` differs only in `claude-plugins-official.lastUpdated` (Claude Code's own refresh at 12:14Z); `~/.claude/settings.json` sha256 unchanged. `~/.claude/plugins/cache/writ-scratch{,-b}` remain (V35: removed 14 days after uninstall); deleting them and the scratch directories is a manual step | https://code.claude.com/docs/en/plugins/cli-reference.md | verified 2026-10-23 |
| V72 `/writ:writ` runs from a generated Writ plugin | Claude Code 2.1.309 | Not run in Story 1: the scratch plugins hold a stub command only. Story 5's live run records it | https://code.claude.com/docs/en/plugins/components.md | unverified 2026-10-23 |
| V73 `claude plugin marketplace add sellke/writ` then `claude plugin install writ@writ` works, with the plugin copied to the cache | Claude Code 2.1.309 | Not run: the remote has no manifest until this spec merges, and a GitHub-sourced plugin loads from a cache copy (V34), not in place as in V57. Story 5 UAT | https://code.claude.com/docs/en/plugins/install.md | unverified 2026-10-23 (pending UAT) |
| V74 `claude plugin validate .` passes on the repository root | Claude Code 2.1.309 | Not run: the root has no manifest in Story 1. V54 and V55 stand in on scratch copies; Story 2 runs validate on the real tree | https://code.claude.com/docs/en/plugins/cli-reference.md | unverified 2026-10-23 |
| V75 Layout A with a root-source marketplace entry that lists `skills` keeps the repository's own `skills/` from loading | Claude Code 2.1.309 | Not run: the layout A scratch used `plugin.json` with no entry `skills` list, and its root `skills/` loaded (V60). V05 documents the exception; no live run tested it | https://code.claude.com/docs/en/plugins/manifest-reference.md | unverified 2026-10-23 |
| V76 A Cursor local plugin loads `rules/writ.mdc` (Prime Directive in the session's rules list) | Cursor (no session in lane) | Not run: no Cursor session in the lane; nothing written to `~/.cursor/plugins/local/` | https://cursor.com/docs/plugins.md | unverified 2026-10-23 (pending UAT) |
| V77 A Cursor local plugin shows `/writ` and the other commands from `commands/` | Cursor (no session in lane) | Not run: no Cursor session in the lane | https://cursor.com/docs/plugins.md | unverified 2026-10-23 (pending UAT) |
| V78 A script-calling command from a Cursor local plugin resolves its script | Cursor (no session in lane) | Not run: no Cursor session in the lane | https://cursor.com/docs/plugins.md | unverified 2026-10-23 (pending UAT) |
| V79 A Cursor command body can use `${CURSOR_PLUGIN_ROOT}` | Cursor (no session in lane) | Not run: no Cursor session in the lane; V49 documents expansion in MCP fields only | https://cursor.com/docs/reference/plugins.md | unverified 2026-10-23 (pending UAT) |

### Upstream changes since 2026-10-22

Read on 2026-10-23; each changed row is re-read above, and the decisions below were taken against the new wording.

- `"."` as a plugin source is documented as the marketplace root (V26). First-Party Facts row 6 called the pattern undocumented.
- A root-source marketplace entry that lists `skills` suppresses the default `skills/` scan (V05). New; it bears on layout A's third condition (§ Candidate Layouts).
- Plugin source types now include `git-subdir`, `npm`, `archive`, and `command` (V25).
- Plugin settings may sit inline in the manifest `settings` key beside `settings.json` (V38).
- The plugin-root `CLAUDE.md` rule is stated on components.md and manifest-reference.md, not on memory.md (V37).
- plugin-evals.md treats `claude plugin eval` as generally available; "early access" survives only as the error text older builds print (V36). spec.md Technical Concerns called the command early access.
- Cursor: https://cursor.com/docs/reference/plugins.md documents `agents/` and `commands/` discovery (V48). First-Party Facts row 9 cited https://cursor.com/docs/plugins (fetched today as https://cursor.com/docs/plugins.md) and found them undocumented.

## Relative Path Inventory

Counted on 2026-10-23 over `commands/`, `agents/`, and `skills/` with the `grep -rE` commands under the table (G1 to G22). Story 2 implements the token classes. Every class rewrites Markdown bodies only: `${CLAUDE_PLUGIN_ROOT}` is substituted in the body (V07), so YAML frontmatter keeps its paths.

| Form | Example | Count (grep) | Reference kind | Resolves under plugin to | Token class |
|---|---|---|---|---|---|
| script invocation | `python3 scripts/spec-status.py` | 69 in 18 files (G1). The spec's 132 (audit 2026-10-22, no command recorded) is not reproduced: G1 finds 69 matches on 65 lines, and 87 with `adapters/`, `cursor/`, `claude-code/`, `system-instructions.md`, and `SKILL.md` added. The observed 69 replaces 132. 4 name a dev-only script, all `bash scripts/eval.sh` in `refresh-command.md` and `skills/plain-prose` (G2) | invocation | `${CLAUDE_PLUGIN_ROOT}/scripts/<name>` for shipped names; dev-only names unchanged (spec Rule 3) | `script-root` (exists) |
| bare script reference | `` `scripts/phase-state.py init` `` | 73 (G3 142 minus G1 69); 8 name a dev-only script: `install.sh`, `update.sh`, `publish-writ-runtime.sh`, `eval.sh` (G4 12 minus G2 4) | invocation or mention: many are calls ("run `scripts/phase-state.py init`", "Delegate ... to `scripts/story-context.py`") | `${CLAUDE_PLUGIN_ROOT}/scripts/<name>` for shipped names; dev-only names unchanged | `script-path` (new) |
| script link target | `](../scripts/lint-skill.sh)` | 1 (G5), in `new-skill.md` | file read (link) | `${CLAUDE_PLUGIN_ROOT}/scripts/lint-skill.sh` | `script-path` (new) |
| agent file reference | `agents/coding-agent.md` | 19 in 8 files (G6): 14 in bodies, 5 in frontmatter (3 skill `evidence` `ref:` lines, 2 in `implement-story.md` `calibrated_against`; G7) | file read: the command reads the prompt template and spawns a general-purpose Task with it | `${CLAUDE_PLUGIN_ROOT}/agents/<x>.md` (body matches only) | `agent-path` |
| agent spawn by Claude agent name | `writ-coder` | 3 (G8), all in one comment line in `migrate.md` that lists file names; 0 spawns by name | none (comment) | unchanged; a named spawn would read `writ:<agent>` (V13, V62) | none |
| skill read | `skills/tdd-cycle/SKILL.md` | 32 in 12 files (G9); 9 are `../skills/<x>/SKILL.md` link targets in `implement-story.md` (G10) | file read | `${CLAUDE_PLUGIN_ROOT}/skills/<x>/SKILL.md` | `skill-path` |
| preamble | `commands/_preamble.md` | 90 in 41 files (G11): 44 link texts `` `commands/_preamble.md` `` (G12), 35 link targets `(_preamble.md)` (G13), 8 link targets `(../commands/_preamble.md)` (G14), 3 bare `` `_preamble.md` `` | file read (link) | `${CLAUDE_PLUGIN_ROOT}/commands/_preamble.md` | `preamble-path` |
| system instructions | `system-instructions.md` | 110 in 42 files (G15): 42 links `` [`system-instructions.md`](../system-instructions.md) `` (84 matches; 41 labelled "Identity & Prime Directive"; G16 counts the 42 targets), 12 directory-prefixed install paths `.claude/`, `.cursor/`, `$WRIT_SRC/`, `[platform_dir]/` (G17), 14 other bare mentions | file read (link); install prose | `${CLAUDE_PLUGIN_ROOT}/system-instructions.md` for link and bare forms; install paths unchanged | `instructions-path` |
| command cross-reference | `` `/create-spec` `` | 806 in 39 files (G19), 712 of them backticked (G18). 3 `/writ:` already exist (G20): one real `/writ:writ` in `writ.md` and two `refs/notes/writ:` refspecs, which the rewrite must skip | invocation (slash command) | `/writ:<command>` (V11) | `command-ref` (new) |
| project docs | `.writ/docs/app-verification.md` | 83 in 27 files (G21) | file read (project) | the project path, unchanged | none |
| other command path | `commands/status.md` | 25 in 16 files (G22), not counting `_preamble.md` | mention: Writ-source paths in meta commands and calibration text | unchanged | none |

Commands, run from the repository root (`D`, `DEV`, and `CMDS` are set once; each line prints a match count, and `grep -rEl ... | wc -l` gives the file counts):

```bash
D="commands agents skills"
DEV='(install|update|uninstall|unlink|migrate|publish-writ-runtime|eval|eval-[a-z0-9-]+|sweep-[a-z0-9-]+|gen-claude-md|gen-platform-trees|pipeline-baseline|measure-invocation|harness-cost|prune-ledger|spawn-cap|recommend-state)'
CMDS='assess-spec|create-adr|create-goal|create-issue|create-spec|create-uat-plan|edit-spec|implement-phase|implement-spec|implement-story|initialize|knowledge|migrate|new-command|new-skill|plan-product|prototype|refactor|refresh-command|reinstall-writ|release|research|retro|revert|review|security-audit|ship|status|uninstall-writ|update-writ|verify-spec|writ-design|writ'

grep -rEoh '\b(python3|bash) scripts/[a-z0-9_-]+\.(py|sh)' $D | wc -l                    # G1  69
grep -rEoh "\b(python3|bash) scripts/${DEV}\.(py|sh)" $D | wc -l                         # G2  4
grep -rEoh '(^|[^a-z0-9_./-])scripts/[a-z0-9_-]+\.(py|sh|json)' $D | wc -l               # G3  142
grep -rEoh "(^|[^a-z0-9_./-])scripts/${DEV}\.(py|sh)" $D | wc -l                         # G4  12
grep -rEoh '\.\./scripts/[a-z0-9_-]+\.(py|sh)' $D | wc -l                                # G5  1
grep -rEoh '(^|[^a-z0-9_./-])agents/[a-z0-9-]+\.md' $D | wc -l                           # G6  19
grep -rEh '(ref: |calibrated_against: )' $D | grep -Eo 'agents/[a-z0-9-]+\.md' | wc -l  # G7  5
grep -rEoh '(^|[^a-z0-9_:/.-])writ-(architect|coder|documenter|evaluator|reviewer|story-gen|tester|visual-qa)\b' $D | wc -l  # G8  3
grep -rEoh 'skills/[a-z0-9-]+/SKILL\.md' $D | wc -l                                      # G9  32
grep -rEoh '\.\./skills/[a-z0-9-]+/SKILL\.md' $D | wc -l                                 # G10 9
grep -rEoh '_preamble\.md' $D | wc -l                                                    # G11 90
grep -rEoh '`commands/_preamble\.md`' $D | wc -l                                         # G12 44
grep -rEoh '\(_preamble\.md\)' $D | wc -l                                                # G13 35
grep -rEoh '\(\.\./commands/_preamble\.md\)' $D | wc -l                                  # G14 8
grep -rEoh 'system-instructions\.md' $D | wc -l                                          # G15 110
grep -rEoh '\.\./system-instructions\.md' $D | wc -l                                     # G16 42
grep -rEoh '(\.claude|\.cursor|\$WRIT_SRC|\[platform_dir\])/system-instructions\.md' $D | wc -l  # G17 12
grep -rEoh "\`/(${CMDS})\b" $D | wc -l                                                   # G18 712
grep -rEoh "(^|[^A-Za-z0-9_./-])/(${CMDS})\b" $D | wc -l                                 # G19 806
grep -rEoh '/writ:[a-z]' $D | wc -l                                                      # G20 3
grep -rEoh '\.writ/docs/[a-z0-9_.-]+' $D | wc -l                                         # G21 83
grep -rEoh '(^|[^a-z0-9_./-])commands/[a-z0-9-]+\.md' $D | wc -l                         # G22 25
```

`DEV` mirrors the denylist in `is_shippable_script` (`scripts/install.sh`).

### Generated-agent frontmatter keys under a plugin

Counts are the eight files in `claude-code/agents/`.

- `permissionMode` (8 of 8): `ignored` (V15)
- `isolation` (3): `survives` (V17; live V63)
- `memory` (4): `survives` (V18; live V64)
- `maxTurns` (8): `survives` (V19; live check V66 unverified)
- `model` (8): `survives` (V20; live check V66 unverified)
- `tools` (8): `survives` (V21; live check V66 unverified)
- `disallowedTools` (4): `survives` (V22; live check V66 unverified)

`hooks`, `mcpServers`, and `initialPrompt` are also ignored in plugin agents (V15, V16); no generated agent sets them.

## Candidate Layouts

**A. Repository root is the plugin.** `.claude-plugin/plugin.json` at root with `commands: ./claude-code/plugin/commands`, `agents: [./claude-code/agents/*.md]`, `skills: ./claude-code/plugin/skills` (if skills carry tokens) or default `./skills`; `${CLAUDE_PLUGIN_ROOT}/scripts/` is the repository's `scripts/` (no copy; dev-only scripts present but unreferenced). `marketplace.json` with `source: "."`. Pro: no duplicated scripts. Con: undocumented pattern; plugin install clones the whole repository. (2026-10-23: `"."` as a source is now documented, V26.)

**B. `plugins/writ/` subdirectory is the plugin.** Generated target writes `plugins/writ/{commands,agents,skills,scripts,system-instructions.md,.claude-plugin/plugin.json,settings.json}`; `marketplace.json` at root with `source: ./plugins/writ`. Pro: documented pattern; ships only the shipped set. Con: committed copies of ~60 scripts and 16 skills, kept honest by `--check`.

Decision rule: B is the default. A only if all three hold: `claude plugin validate .` passes; a live install from a local path of a scratch copy works (the remote has no manifest until this spec lands, so the rule is applied to the local copy and the substitution is recorded); the root `skills/` default scan does not load the un-tokenized source skills beside the generated ones. Under A, dev-only scripts are present in the clone but unreferenced (spec Rule 3).

### Decision (Story 1, 2026-10-23): Layout B

The rule applied to local-path installs of scratch copies of each layout, in place of the real repository root (no manifest exists there yet):

1. Validate passes. Held for A's scratch copy (V54) and for B's at both directories (V55). Validate on the real root waits for Story 2 (V74).
2. A live local-path install works. Held for A and for B: add (V56), install (V57), `/writ:stub` with the substituted root (V58), the namespaced agent spawn (V62).
3. The root `skills/` default scan does not load the source skills. Not shown for A. A `skills` key in `plugin.json` adds to the default scan (V04), and A's scratch install loaded its root `skills/` (V60), so under A the repository's own `skills/`, with their bare `scripts/` paths, would load as `/writ:<skill>`. Under B a `skills/` outside `plugins/writ/` does not load (V61).

Condition 3 does not hold for A as tested, so the default stands: **B**. The carrier decision below replaces B's `settings.json` with `output-styles/writ.md`.

- Rests on: V04, V54, V55, V56, V57, V58, V60, V61, V62
- Open, not relied on: the documented exception in V05 (a root-source marketplace entry that lists `skills`) was not run (V75 unverified); the GitHub install is Story 5 UAT (V73 unverified); validate on the real tree is Story 2 (V74 unverified).

What B requires of Story 2:

- **Real files, own scripts.** A GitHub-sourced plugin is copied into the cache without files outside its directory (V34), and validate and local installs skip links that leave the plugin (V32, V33). So `plugins/writ/` holds real files, never symlinks, including its own copy of the shipped scripts; the dev-only scripts stay out (spec Rule 3).
  - Rests on: V32, V33, V34
- **Marketplace.** Repository-root `.claude-plugin/marketplace.json`: `name` `writ`, `owner.name`, one entry `{"name": "writ", "source": "./plugins/writ"}`. Install with `claude plugin marketplace add sellke/writ` then `claude plugin install writ@writ`.
  - Rests on: V24, V25, V27, V28, V56, V57
- **List the agents.** The plugin's `agents/` holds both the generated `writ-*.md` agents and the prompt-template docs that `agent-path` points at. A file there without a frontmatter `name` still loads as an agent (V23), so `plugin.json` sets `agents` to the eight generated files, which replaces the default scan (V03).
  - Rests on: V03, V23
- **Check `_preamble.md`.** Every `commands/<file>.md` becomes `/writ:<file>` (V11), so a plugin `commands/_preamble.md` may register as `/writ:_preamble`. Story 2 either lists the command files in the `commands` key, which replaces the default scan (V02), or records the extra command in the adapter.
  - Rests on: V02, V11

### Token classes (Story 1, 2026-10-23)

Confirmed from § Relative Path Inventory: `agent-path`, `skill-path`, `preamble-path`, `instructions-path`, beside the existing `script-root`. Added: `script-path` (bare shipped-script references and the one `../scripts/` link target) and `command-ref` (`/<command>` to `/writ:<command>`, skipping forms already namespaced and `refs/notes/writ:` refspecs). Each class rewrites Markdown bodies only and leaves dev-only script names unchanged. Commands spell the substituted path inline, because the Bash tool's environment has no `CLAUDE_PLUGIN_ROOT` (V08).

- Rests on: V07, V08, V09, V11, V58

### Namespacing (Story 1, 2026-10-23)

Under the plugin: commands are `/writ:<command>` and the front door is `/writ:writ` (V11, V58); skills are `/writ:<skill>` (V12, V60); agents are `writ:<agent>` for the Agent tool and `--agent` (V13, V62, V65); the output style is `writ:writ` (V41). A project command of the same name does not shadow the plugin command (V59). Plugin agents rank lowest among same-named agents (V14); the namespaced name is unique, so it still resolves.

- Rests on: V11, V12, V13, V14, V41, V58, V59, V60, V62, V65

### Agent frontmatter under the plugin (Story 1, 2026-10-23)

The plugin ignores `permissionMode`, which all eight generated agents set (V15), so their permission modes do not apply when they run from the plugin; Story 2's adapter section lists it. `hooks`, `mcpServers`, and `initialPrompt` are also ignored (V15, V16); no generated agent uses them. `isolation` and `memory` take effect (V17, V18, V63, V64). `maxTurns`, `model`, `tools`, and `disallowedTools` carry no plugin exception (V19 to V22); no live run showed them applied (V66).

- Rests on: V15, V16, V17, V18, V19, V20, V21, V22, V63, V64

### Cursor layout input for Story 3 (Story 1, 2026-10-23)

- `.cursor-plugin/plugin.json` needs only `name` (V47). `rules/`, `skills/`, `agents/`, and `commands/` are documented discovery directories (V48), so Story 3 places the layout there by the docs. Live loading stays pending UAT (V76, V77).
  - Rests on: V47, V48
- No verified row gives a plugin-root path form for a command body: `${CURSOR_PLUGIN_ROOT}` is documented only in MCP fields (V49), and the command-body check is pending UAT (V79). Story 3 takes AC-3.3's second branch: commands keep `python3 scripts/<name>.py`, the layout has no `scripts/`, and the project still needs the `install.sh` script copy.
  - Rests on: V49
- Local install is `~/.cursor/plugins/local/writ` plus a reload (V50). The marketplace listing is a submission the maintainer makes after Cursor's review (V51); team marketplaces need a Teams or Enterprise plan (V52).
  - Rests on: V50, V51, V52

## Prime Directive Carrier

| Mechanism | How | Check | Observed |
|---|---|---|---|
| `settings.json` `{"agent": "writ"}` + `agents/writ.md` whose body is `system-instructions.md` | main thread runs as that agent | In a scratch project, compare replies with the no-carrier baseline. Decisive probes: P2 (quote the first Hard Constraints bullet and its parent heading) and P3 (name the persona). P1 (confirm an assertion without evidence), the originally planned probe, did not discriminate (V70). Record the transcript line. | P2 and P3 differ from the baseline (V67, V68) |
| `output-styles/writ.md` with `force-for-plugin: true` | style instructions sent with every request | same probe | P2 and P3 differ from the baseline (V67, V69) |

The probe ran four prompts per session (V67 to V70). The assertion prompt (P1) did not discriminate: the baseline session also withheld confirmation (V70). The two prompts that did are P2, quote the first Hard Constraints bullet and its parent heading, and P3, name the persona. Both carriers were observed.

### Decision (Story 1, 2026-10-23): carrier 2, the forced output style

`plugins/writ/output-styles/writ.md` with `force-for-plugin: true` and `keep-coding-instructions: true`; its body is the body of `system-instructions.md`. The proving line, carrier 2, prompt P2 (V69):

```
- **Never reverse a position without new evidence.** If the user pushes back and you still believe you're right, say so. Reverse only on new information.
SOURCE Prime Directive
```

Both carriers passed the probe, so the documented behavior breaks the tie:

- Carrier 1 runs the whole session as a custom agent. Its prompt replaces Claude Code's default system prompt entirely (V40), and its tool restrictions and model apply to the session (V38). A user's own `agent` setting also overrides it without notice (V39).
- Carrier 2 sends the style's instructions with every request and holds while the plugin is enabled (V42). With `keep-coding-instructions: true` it keeps Claude Code's software-engineering section on the full system prompt (V43).

Costs Story 2 documents in `adapters/claude-code.md`:

- It overrides the user's `outputStyle` while the plugin is enabled. If another enabled plugin also forces a style, the first loaded wins (V42).
- It does not reach subagents (V44). Each generated agent carries its own body.
- `keep-coding-instructions` has no effect on the shorter system prompt (V43). The live P4 probe answered `NO` with carrier 2 as with the baseline (V70), so no run showed the coding section kept.

- Rests on: V38, V39, V40, V42, V43, V44, V67, V69, V70

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

- **Cursor local plugin:** copy the Cursor layout to `~/.cursor/plugins/local/writ`, restart Cursor or run Developer: Reload Window, open a sample project, and check Customize (V50); confirm the rules file loads (the Prime Directive is visible in the session's rules list), `/writ` appears, and a command that calls a script resolves. Record in `adapters/cursor.md` § Plugin, then flip V76 to V79 from `unverified 2026-10-23 (pending UAT)` to the run's result:
  - Cursor version:
  - Rules list result (is `writ.mdc` listed; is the Prime Directive visible):
  - Commands seen (is `/writ` listed; which others):
  - Script call result (command run, script path, exit code):
  - Result: `pass` or `fail`, with the failing check named
  - The Cursor marketplace listing is not part of this protocol. It is a submission the maintainer makes at cursor.com/marketplace/publish, and Cursor reviews every plugin before listing it (V51). Story 3 expands this protocol (AC-3.5).
- **Claude Code plugin live run:** `claude plugin marketplace add sellke/writ`; `claude plugin install writ@writ`; in an empty temp project run `/writ:initialize` then `/writ:writ "add a health endpoint"`; record the transcript lines showing the scaffold and the route. A GitHub-sourced install runs from a cache copy (V34), so this run also flips V72 and V73.

## Shadow Paths

- **Happy path:** validate passes; install works; `/writ:writ` routes; scripts resolve from the plugin root.
- **Nil input:** no `claude` CLI on the test machine → that check `unverifiable`; the rest of the target runs.
- **Empty input:** project with no `.writ/` → `/writ:initialize` scaffolds; other commands say to run it.
- **Upstream error:** platform docs changed since 2026-10-22 → the record row says so with the new URL; the layout decision is re-taken, never patched silently.

## Error & Rescue Map

Not required: no runtime data flow. The failure surface is install-time and covered by the smoke test's per-target checks.
