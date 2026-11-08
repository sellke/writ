# Plugin Distribution

> **Status:** Complete
> **Created:** 2026-10-22
> **Owner:** @AdamSellke
> **Dependencies:** [2026-10-22-generated-platform-trees]
> **Phase:** 14 — Front Door and Distribution ([roadmap](../../product/roadmap.md), [ADR-030](../../decision-records/adr-030-contract-verifier-boundary-front-door.md))
> **Origin:** Phase 14 decomposition pre-pass (`/implement-phase 14`, 2026-10-22). Promoted from the roadmap parking lot on 2026-10-20; pstack research F6 and Further Research 1. Closes `.writ/issues/improvements/2026-10-12-script-install-location.md`.

## Specification Contract

**Deliverable:** Writ installs as a plugin in Claude Code and in Cursor from this repository, built from the generated trees, with scripts run from the plugin root and `/initialize` scaffolding `.writ/`. One smoke test runs against both plugin installs and the three `install.sh` installs. `install.sh` stays.

**Must Include:**

1. **Story 1 is verification, not code.** Both plugin formats are checked against first-party docs and one live install each, recorded with dates, versions, and URLs in `sub-specs/technical-spec.md` § Verification Record. It decides the plugin root layout, how commands reach scripts, agents, skills, and the preamble from inside a plugin, how `system-instructions.md` reaches a plugin session, and command and agent namespacing. If Cursor cannot install a third-party repository outside its marketplace, the Cursor deliverable is a plugin-ready layout installable from `~/.cursor/plugins/local`, plus a marketplace submission the maintainer makes, and the contract says so.
2. **Claude Code.** `.claude-plugin/plugin.json` and `.claude-plugin/marketplace.json` at the repository root so one `marketplace add` and one `install` suffice. Commands, agents, and skills point at a generated tree whose `script-root` is `${CLAUDE_PLUGIN_ROOT}/scripts`, produced by a new target in `scripts/gen-platform-trees.py` with the token classes the inventory in Story 1 shows are needed. The Prime Directive reaches the session by the mechanism Story 1 verifies (candidates: a plugin-root `settings.json` naming a main-thread agent whose body is `system-instructions.md`; an output style with `force-for-plugin`). `claude plugin validate` passes.
3. **Cursor.** `.cursor-plugin/plugin.json` with the same component set (rules carry `writ.mdc`; commands, agents, skills as the docs place them), installable from the local plugins folder; the live session check is a UAT protocol.
4. **`/initialize` scaffolds `.writ/`** when absent, through a new shipped `scripts/scaffold-writ.py` that creates the tree Writ's commands write into (eleven paths, more than `install.sh` creates today, which omits `knowledge/` and every `issues/` subfolder) and the `.gitignore` entries, idempotently. `install.sh` and `update.sh` keep a bash `init_writ_workspace` with the same list (no Python dependency enters the installers), and a test asserts the bash list and the script's list are identical, so the two never drift.
5. **ADR-031** records the script-location decision: `install.sh` installs keep `scripts/` in the project; plugins run scripts from their root; a project file sharing a shipped script's name keeps today's documented behavior. Closes the script-install-location issue.
6. **Smoke test**, one script, five targets: commands discoverable at the platform's path; one shipped script runs from the resolved root; system instructions reachable; `.writ/` scaffolded by `scaffold-writ.py`. For the Claude Code plugin it also runs `claude plugin validate` when the CLI is present, and reports `unverifiable` when it is not. `README.md`'s install section lists plugin install first only for a platform whose smoke test passes.

**Hardest Constraint:** Platform plugin formats are moving targets and partly undocumented. Every claim in the spec and the adapters carries a date and a URL, and the smoke test is the only evidence the README may cite. Under a plugin, command and agent names are namespaced (`/writ:create-spec`, `writ:writ-coder`); the generated tree must spell every cross-reference the way the platform resolves it.

**Success Criteria:** smoke test green on the three `install.sh` targets and the Claude Code plugin, and green or `unverifiable (no cursor session)` on Cursor; a fresh empty project with the Claude Code plugin installed runs `/writ:writ` and `/writ:initialize` in a live session (recorded); `uv run --python 3.9 pytest`, the bash tests, and `bash scripts/eval.sh` (0 findings) pass.

**Scope out:** OpenClaw, npm or archive distribution, plugin auto-update, removing `install.sh`, Cursor marketplace listing (the submission is a maintainer action after the phase).

## Technical Concerns

*Found while grounding the contract on 2026-10-22, from the Claude Code docs (read that day) and the Cursor plugin docs page. Each is re-verified in Story 1.*

- **Claude Code manifest.** `.claude-plugin/plugin.json` needs only `name`. `commands` (path, array, or object; replaces the default scan), `agents` (`.md` paths; directories rejected), `skills` (adds to the default `skills/` scan), `hooks`, `mcpServers`. Paths start with `./` and stay inside the plugin root. `${CLAUDE_PLUGIN_ROOT}` is substituted in command, skill, and agent bodies, not in the Bash tool's environment. Source: code.claude.com/docs/en/plugins/manifest-reference.md, components.md.
- **Namespacing.** Plugin commands are `/writ:<name>`; a project `.claude/commands/<name>.md` does not collide. Plugin agents are `writ:<name>` and lose name collisions; `hooks`, `mcpServers`, `permissionMode`, `initialPrompt` in plugin agent frontmatter are ignored. Writ's generated agents use `permissionMode` and `isolation`; the plugin target must drop or document what the platform ignores. Source: sub-agents.md, skills.md.
- **Prime Directive.** A `CLAUDE.md` at the plugin root is not loaded. A plugin-root `settings.json` with `"agent": "<name>"` makes the main thread run as that agent, so its system prompt applies to the session; `output-styles/<name>.md` with `force-for-plugin: true` is the documented alternative. Source: components.md, output-styles.md. Story 1 picks the one that observably carries the hard constraints.
- **Marketplace.** `.claude-plugin/marketplace.json` with `name`, `owner.name`, `plugins[]` each `name` and `source` (relative `./path`, `{source: github, repo}`, `{source: url}`). Add with `claude plugin marketplace add sellke/writ`; install with `claude plugin install writ@<marketplace name>`. A repository that is both marketplace and plugin is not a documented pattern; the schema accepts `"."`. Story 1 tests both root-as-plugin and `plugins/writ/` layouts. Layout B (`plugins/writ/`) is the default; A is kept only if `claude plugin validate .` passes, a live install from a local path works, and the root `skills/` default scan does not load the un-tokenized source skills beside the generated ones. Source: marketplace-reference.md, install.md.
- **Validation and eval.** `claude plugin validate <path>` (exit 0 pass, 1 fail, 2 error; `--strict`). `claude plugin eval` exists in early access and bills model calls; out of scope. Source: cli-reference.md, plugin-evals.md.
- **Cursor.** `.cursor-plugin/plugin.json` requires only `name`; rules in `rules/`, skills in `skills/`, MCP in `mcp.json`; agents, commands, and hooks are listed as components with undocumented directories. Official marketplace entries are reviewed by the Cursor team; team marketplaces import repository URLs; a local plugin goes in `~/.cursor/plugins/local` and loads after reload. `${CURSOR_PLUGIN_ROOT}` is documented only for `mcp.json`. Source: cursor.com/docs/plugins (read 2026-10-22). Whether a Cursor plugin command can run a script from the plugin root is unknown; if not, the Cursor plugin ships commands that still expect `scripts/` in the project and the README says so.
- **Relative paths in commands.** Commands cite `agents/<x>.md`, `skills/<x>/SKILL.md`, `commands/_preamble.md`, `system-instructions.md`, and `.writ/docs/<x>.md`. Under a plugin, the first four live in the plugin root and the last in the project. The inventory in Story 1 classifies every form; each class that must resolve inside the plugin gets a token in `gen-platform-trees.py` (`agent-path`, `skill-path`, `preamble-path`, `instructions-path`), following the `script-root` pattern.
- **Scaffold.** `install.sh` creates the `.writ/` tree and adds `.writ/state/` to `.gitignore`. `commands/initialize.md` says "`.writ/` exists from installation". `scaffold-writ.py` makes that true for plugins and is named by `/initialize` (ADR-029 rule 4).

## Experience Design

### Who uses it

- **A new Claude Code user** who runs two `/plugin` commands and then `/writ:writ "<request>"` in any project.
- **A Cursor user** who installs from the marketplace once Cursor lists Writ, or from the local plugins folder before then.
- **The maintainer** who cuts a release and wants one source of truth for five install paths.

### Journey

1. Entry (Claude Code): `claude plugin marketplace add sellke/writ`, `claude plugin install writ@writ`, open a project, `/writ:initialize`.
2. Happy path: `/writ:initialize` scaffolds `.writ/`, detects the stack, writes the docs. `/writ:writ "fix the pagination bug"` restates and routes to `/writ:prototype --no-diverge`, which runs a shipped script from the plugin root.
3. Moment of truth: the session carries the Prime Directive, and a command's script invocation resolves without a `scripts/` folder in the project.
4. Feedback: the smoke test output in CI, and the README's install section listing the plugin path first for the platforms where the test passes.

### State Catalog

| State | What the user sees |
|---|---|
| Claude Code plugin installed, project without `.writ/` | `/writ:initialize` creates `.writ/` and proceeds; other commands that write under `.writ/` say "run `/writ:initialize` first" when it is absent. |
| Claude Code plugin, command calls a script | `python3 ${CLAUDE_PLUGIN_ROOT}/scripts/<name>.py` resolves to the plugin's copy. |
| Claude Code plugin, command spawns an agent | The namespaced agent (`writ:writ-coder`) is spawned; the generated command names it that way. |
| Claude Code plugin and `install.sh` install in the same project | Both sets of commands exist (`/create-spec` and `/writ:create-spec`); the adapter documents which wins for agents and recommends one install path per project. |
| Cursor local plugin | Rules load from the plugin's `rules/writ.mdc`; commands appear; script invocations resolve per Story 1's finding (plugin root, or `scripts/` still required and documented). |
| `claude plugin validate .` | `pass`; a malformed manifest fails CI through the smoke test. |
| Smoke test on a machine without the `claude` CLI | The Claude Code plugin target reports `unverifiable (no claude CLI)`; the other targets still run. |
| README install section | Plugin install first for each platform whose smoke test passes; `install.sh` sections follow unchanged. |

### Interaction Patterns

- One source, five install paths, one smoke test.
- Every platform claim in the adapters carries a date and a URL (the rendering-rows precedent).

## Business Rules (Expanded)

1. **Verification record first.** Story 1 writes `sub-specs/technical-spec.md` § Verification Record: a table `Claim | Platform & version | Observed | Source | Status` for every bullet under Technical Concerns, with the same status grammar as the rendering-rows spec. No layout decision is made from an unverified claim.
2. **Plugin target.** `gen-platform-trees.py` gains target `claude-code-plugin` writing to `claude-code/plugin/` (or the layout Story 1 selects) with `script_root: ${CLAUDE_PLUGIN_ROOT}/scripts` and the token classes Story 1's inventory requires. Generated output is committed and covered by `--check`.
3. **Scripts in the plugin.** The plugin root contains the shipped script set (the files `is_shippable_script` admits), either as the repository's own `scripts/` when the root is the repository (layout A), or as a generated copy under the plugin directory (layout B). A plugin command never references a dev-only script; under layout B dev-only scripts are absent, and under layout A they are present in the clone but unreferenced. A test asserts the generator's shipped set equals the bash rule's.
4. **Agents in the plugin.** The generated Claude agents are reused; frontmatter keys the platform ignores in plugins are listed in the adapter so a reader knows what does not apply.
5. **Prime Directive carrier.** One mechanism, chosen in Story 1, recorded in `adapters/claude-code.md` § Installation with the observation that proved it.
6. **Cursor layout.** `.cursor-plugin/plugin.json` with `name`, `description`, `version` (from `VERSION`); `rules/writ.mdc` (the generated file); `skills/`; `commands/` and `agents/` where the docs place them if documented on the run date, else at `commands/` and `agents/` (the same shape `install.sh` gives `.cursor/`) labelled `unverified (pending UAT)`. This is the one deliberate exception to Rule 1: the lane has no Cursor session, and shipping a labelled layout is the only alternative to shipping nothing. The README never lists the Cursor plugin first until the UAT run flips the rows. A `## Plugin` section in `adapters/cursor.md` records what was verified and what is pending UAT.
7. **Scaffold script.** `scripts/scaffold-writ.py scaffold [--project <dir>] [--check]` creates the eleven paths `.writ/{specs,product,research,decision-records,docs,knowledge,state}` and `.writ/issues/{bugs,features,improvements,goals}` (`explanations/`, which `install.sh` creates today, is dropped: nothing shipped references it), and ensures `.gitignore` lists `.writ/state/` and `.writ-lanes-*/`, creating the file when absent; idempotent; check-shape output. `install.sh` keeps its bash `init_writ_workspace` and `update.sh` gains a byte-identical copy (it has none today), both with the same eleven paths and the same `.gitignore` behavior; `scripts/tests/test_scaffold_writ.py` asserts the bash function's path list equals the script's. `/initialize` runs the script as Step 0 and reports the result.
8. **ADR-031.** `.writ/decision-records/adr-031-script-location.md`: decision, the two install paths, the shared-name behavior, consequences. The script-install-location issue gets `## Resolution` pointing at it.
9. **Smoke test.** `scripts/tests/test_plugin_smoke.sh`, targets `cursor`, `claude`, `codex` (via `install.sh` into temp projects), `claude-plugin` (the plugin directory), `cursor-plugin` (the Cursor layout). When the Cursor layout's commands keep the identity `scripts/` form, the `cursor-plugin` script-root check runs against a temp project that holds `install.sh`'s script copy and its result line reads `pass (requires project scripts/)`. Checks: every manifest command file present at the platform's command path; `python3 <root>/scripts/spec-status.py --help` exits 0 from the resolved root; the system-instructions file is at the path the platform loads or the Writ block imports; `scaffold-writ.py scaffold` creates the tree in an empty temp dir. `claude plugin validate` runs when `command -v claude` succeeds; else that one check prints `unverifiable`. The test never runs against the Writ repo itself.
10. **README.** § Quick Start gains a "Claude Code (plugin)" subsection first, with the two commands, only when the smoke test passes on `claude-plugin`; a "Cursor (plugin)" subsection first for Cursor only when `cursor-plugin` passes and the UAT protocol has been run; when the target passes but the UAT has not run, it appears after the Cursor `install.sh` section and says "local install; marketplace listing pending"; when the target fails, the subsection is omitted. `unverifiable` never counts as a pass. The smoke test records its per-target results in `scripts/tests/fixtures/plugin-smoke-results.txt` when run with `--record`, and `test_readme_install_order` checks the README against that file. `install.sh` sections stay.
11. **Live run evidence.** Story 5 records one live Claude Code session in a fresh temp project with the plugin installed from the local checkout as the marketplace source (`claude plugin marketplace add <path to this checkout>`; the GitHub-sourced `sellke/writ` install is the UAT step after the phase merges): `/writ:initialize` scaffolds; `/writ:writ "<request>"` restates and routes. Transcript excerpt in What Was Built with the Claude Code version.
12. **Runtime.** Python 3.9 standard library, POSIX bash. Tests make no network calls; the marketplace add in Story 1 is a recorded manual step, not a test.

## Detailed Requirements

### Story 1: Verify both plugin formats and decide the layout

- Read the first-party pages named under Technical Concerns on the run date; perform `claude plugin validate` on a scratch layout, a `marketplace add` from a local path, an `install`, and one `/writ:<command>` invocation plus one agent spawn in a scratch project; place a scratch Cursor plugin in `~/.cursor/plugins/local` and record what loads if a Cursor session is available, else mark pending UAT.
- Inventory every relative path form in `commands/`, `agents/`, `skills/`; classify each; list the token classes needed.
- Write the Verification Record and the decisions (layout, Prime Directive carrier, tokens, namespacing) into the technical spec.

### Story 2: Claude Code plugin

- Manifest and marketplace files; the `claude-code-plugin` target and token classes in `gen-platform-trees.py` (with tests); the Prime Directive carrier; `claude plugin validate` in `test_plugin_smoke.sh`'s `claude-plugin` target (Story 5 wires the rest); `adapters/claude-code.md` § Installation gains the plugin path and the ignored-keys list.

### Story 3: Cursor plugin

- `.cursor-plugin/plugin.json`, `rules/writ.mdc` placement, commands, agents, skills; local-install protocol in `adapters/cursor.md` § Plugin with status; UAT protocol for the live session in the technical spec.

### Story 4: Scaffold script, `/initialize` Step 0, ADR-031

- `scripts/scaffold-writ.py` with tests; `install.sh` and `update.sh` call it; `commands/initialize.md` Step 0; ADR-031; issue resolution.

### Story 5: Smoke test and README

- `test_plugin_smoke.sh` across five targets; README install sections per Rule 10; live-run evidence per Rule 11; `adapters/codex.md` untouched except a one-line note that Writ ships no Codex plugin in this release (a statement about Writ, not a platform claim, so it needs no URL).

## Implementation Approach

- **Order.** Story 1 first and alone. Story 2 and Story 4 depend on it and touch disjoint files, so they may run as one batch. Story 3 depends on Story 2 as well, because both add targets to `TARGETS` in `scripts/gen-platform-trees.py` and both extend `scripts/tests/test_plugin_distribution.py` (which Story 1 creates). Story 5 depends on 2, 3, and 4.
- **Evidence over inference.** Any platform behavior not seen in a live run or a first-party page stays `unverified` in the record, and the README does not cite it.
- **Reuse the generator.** No second generation path: the plugin tree is a `gen-platform-trees.py` target, so `--check` keeps it honest.
- **Verification.** `uv run --python 3.9 pytest`, the bash test loop, and `bash scripts/eval.sh` after every story.
