# ADR-031: Script Location Under Two Install Paths

> **Date:** 2026-10-23
> **Status:** Accepted
> **Category:** Framework Architecture
> **Deciders:** @AdamSellke
> **Origin:** [`2026-10-12-script-install-location`](../issues/improvements/2026-10-12-script-install-location.md), filed by ADR-029 Implementation Notes step 6
> **Supersedes in part:** [ADR-029](adr-029-agent-cli-contract.md), the Consequences bullet "Scripts install into the project-root `scripts/` folder." ADR-029 rules 1 to 7 and its amendments stand.
> **Keeps:** ADR-029 rules 1 to 7. Every shipped script follows the agent CLI contract on both install paths, and the contract test reads the shipped set from `is_shippable_script` as before.
> **Extends:** [ADR-030](adr-030-contract-verifier-boundary-front-door.md). Its 2026-10-20 amendment to ADR-029 said Phase 14's plugin, with scripts inside it, would settle the script-location consequence. This record settles it.
> **Respects:** [ADR-015](adr-015-leanness-self-governance.md) (no new command), [ADR-027](adr-027-optional-judgment-provider.md) (no runtime dependency: the installers stay bash and never call Python)
> **Evidence base:** [`technical-spec.md`](../specs/2026-10-22-plugin-distribution/sub-specs/technical-spec.md) § Verification Record of spec `2026-10-22-plugin-distribution`, rows V07, V08, V34, V49, V58 (Claude Code docs and Cursor docs read 2026-10-23; Claude Code 2.1.309 live run 2026-10-23). See Evidence below.

## Decision

**Shipped scripts stay where each install path puts them. Commands name them in one source form, and `scripts/gen-platform-trees.py` resolves that form per target.**

- **`install.sh` installs** (Cursor, Claude Code, Codex) keep shipped scripts in the project's `scripts/` folder, as today. Installed commands read `python3 scripts/<name>.py`.
- **Plugin installs** run shipped scripts from the plugin root. The Claude Code plugin (`plugins/writ/`) carries its own copy of the shipped set in `plugins/writ/scripts/`, and its commands read `python3 ${CLAUDE_PLUGIN_ROOT}/scripts/<name>.py`. Claude Code substitutes `${CLAUDE_PLUGIN_ROOT}` in command, skill, and agent bodies (V07, V58). The variable is not in the Bash tool's environment (V08), so a command spells the substituted path inline and never relies on `$CLAUDE_PLUGIN_ROOT` at run time.
- **One source.** `commands/`, `agents/`, and `skills/` keep the `scripts/<name>` form. The generator's `script-root` token rewrites it for the plugin target. `gen-platform-trees.py --check`, run by `eval.sh`, fails when a committed tree differs from its render.

### Shared-name rule

A project file at a shipped script's path (`scripts/<name>`) keeps today's documented behavior under `install.sh`. It has no install baseline, so install and update treat it as locally modified and keep it, and Writ's commands then run the project's file under Writ's name. `--force` overwrites it. This record keeps that behavior and adds no rename, prefix, or migration.

Under the plugin the collision cannot happen: a plugin command names `${CLAUDE_PLUGIN_ROOT}/scripts/<name>`, so it never runs a project file of the same name. A project with both installs has both command sets (`adapters/claude-code.md` § Installation → Plugin), and that section recommends one install path per project.

### The `.writ/` scaffold

A plugin project has no `install.sh` run, so nothing creates `.writ/`. `scripts/scaffold-writ.py scaffold` creates the tree Writ's commands write into, and `/initialize` runs it as Step 0. `install.sh` and `update.sh` keep a byte-identical bash `init_writ_workspace` with the same eleven paths and the same `.gitignore` rule, and neither calls Python. `scripts/tests/test_scaffold_writ.py` fails when the bash list or the bash `.gitignore` result differs from the script's (`test_bash_list_matches`, `test_bash_gitignore_matches_script`).

## Context and Problem Statement

ADR-029 recorded that scripts install into the project-root `scripts/` folder, where they can collide with a project's own scripts, and filed the question of where they should install. The issue's Expected Outcome asks for a recorded decision among three options and a rule for a project file that shares a script's name.

Phase 14 added a second install path. Spec `2026-10-22-plugin-distribution` ships Writ as a Claude Code plugin built from the generated trees, and a plugin project has no `scripts/` folder unless the user also runs `install.sh`. What holds on 2026-10-23:

- `install.sh` and `update.sh` copy the files `is_shippable_script` accepts (35 scripts and `jev-thresholds.json`) into the project's `scripts/`.
- Commands, agents, and skills call scripts as `python3 scripts/<name>.py` (69 invocations in 18 files) and name them bare in 73 more places (technical-spec.md § Relative Path Inventory).
- A plugin installed from a git marketplace is copied into Claude Code's cache, and files outside the plugin directory are not copied (V34). A plugin's scripts must live inside the plugin.
- `${CLAUDE_PLUGIN_ROOT}` resolves in command bodies (V07, V58) but not in the Bash tool's environment (V08).
- Cursor expands `${CURSOR_PLUGIN_ROOT}` only in MCP server fields, not in command bodies (V49).

## Decision Drivers

1. **One source.** Every install path renders from the same command, agent, and skill files.
2. **No migration.** Existing `install.sh` projects keep working without a move.
3. **Leanness.** No new command, install step, or runtime dependency in the installers (ADR-015, ADR-027).
4. **Nothing copied into a plugin project.** A plugin user's scripts run from the plugin.

## Considered Options

The issue's Expected Outcome names the first three.

### Option A — Keep `scripts/` for `install.sh`; run scripts from the plugin root under a plugin (chosen)

- **Pros:** No caller path changes in the source. No migration for installed projects. The plugin path works with an empty project. The generator already had the `script-root` token class.
- **Cons:** Two resolved forms of every command, and a committed copy of the shipped scripts under `plugins/writ/scripts/`. The `install.sh` collision stays.
- **Effort:** Small. A generator target, a scaffold script, and this record.
- **Risk:** Low. `--check` catches a stale copy, and each target is regenerated from one source.

### Option B — Move shipped scripts to a Writ-owned folder such as `.writ/scripts/`

- **Pros:** No collision with a project's `scripts/`. One location for every Writ-installed script.
- **Cons:** Every caller path changes in one release. `update.sh` must move scripts in existing installs and handle a project that already uses `.writ/scripts/`. `.writ/` holds the project's specs and state, and shipped code would sit beside them. The plugin still needs its own root, because a plugin copies nothing into the project.
- **Effort:** Medium to large: the move, the update migration, every caller, and the byte and hash pins on command files.
- **Risk:** Medium. A failed migration leaves an installed project with commands that call scripts that are not there.

### Option C — Keep each tool beside the skill or command that runs it (pstack's layout)

- **Pros:** No collision. Each tool sits with its one caller.
- **Cons:** Writ's scripts have many callers. `phase-state.py` alone is named in seven command files and three adapters. Commands are flat files, not folders, so there is no folder to put a tool beside. Shared scripts would need copies per caller or cross-folder paths.
- **Effort:** Large.
- **Risk:** Medium to high. Every install path and the contract test's shipped-set rule change.

### Option D — Plugin only; retire `install.sh`

- **Pros:** One install path, no collision.
- **Cons:** Codex has no Writ plugin, and the Cursor plugin cannot run scripts from its root (V49). Removing `install.sh` is out of the spec's scope.
- **Effort:** Not estimated.
- **Risk:** High. It would strand Codex and Cursor users.

## Decision Outcome

**Option A.** Driver 2 rules out B: it needs a migration of every installed project. Driver 1 and driver 3 rule out C: Writ's scripts are shared, and splitting them multiplies copies. D strands two platforms. A meets driver 4 through the plugin root and driver 1 through the generator and `--check`.

The collision ADR-029 named stays, for `install.sh` projects only. It is accepted with today's documented behavior. The plugin path does not have it.

**Dissent (recorded):** A project that ships its own `scripts/spec-status.py`, or any other shipped name, still has Writ's commands run the project's file after an `install.sh` install. Option B would remove that. Revisit if a user reports it.

## Consequences

**Positive**

- A Claude Code plugin project runs every shipped script with nothing copied into it.
- Existing `install.sh` projects need no migration, and their installed command text does not change.
- One source; `gen-platform-trees.py --check` guards the plugin form, and the contract test guards the scripts on both paths.
- `/initialize` creates `.writ/` when it is absent, so a plugin project gets the same tree as an `install.sh` project.

**Negative, with mitigations**

- **Two resolved forms of every command.** *Mitigation:* the generated tree is committed and `--check` fails on drift.
- **A committed copy of the shipped scripts in `plugins/writ/scripts/`.** *Mitigation:* `--check` reports each stale, missing, or orphan file.
- **The `install.sh` collision stays.** *Mitigation:* the shared-name rule above, and the adapter's advice to use one install path per project.
- **The `.writ/` tree differs from the old installer's.** The old step created `specs`, `product`, `research`, `decision-records`, `docs`, `issues`, `explanations`, and `state`. The new list adds `knowledge`, `issues/bugs`, `issues/features`, `issues/improvements`, and `issues/goals`, and drops `explanations`. No command, agent, skill, or adapter references `.writ/explanations`. A project that has the folder keeps it; nothing removes it.
- **`.gitignore` is created when absent.** The old installer appended `.writ/state/` only when the file existed. An install into a project with no `.gitignore` now creates one, and the install commit includes it.
- **`.writ-lanes-*/` is new for installs.** Every install, update, and `/initialize` run adds it when missing. An existing install's block gains the line without a second `# Writ ephemeral state` comment.
- **`update.sh` now repairs a missing tree.** Every update except `--dry-run` runs `init_writ_workspace`. Its scoped commit does not stage `.gitignore`, so an update that adds `.writ-lanes-*/` leaves that change for the user to commit.
- **The installers mirror the script instead of calling it.** Drift is caught by `test_scaffold_writ.py`, not prevented. *Mitigation:* the test compares the expanded `mkdir -p` list with `PATHS` and runs the bash function against the script on the same `.gitignore` fixtures.
- **Writ-source scripts locate their root from their own path (follow-up, drift DEV-005).** `gen-claude-agents.py`, `gen-codex-agent-tomls.py`, `check-agent-parity.sh`, and `gen-skill.sh` ship because `is_shippable_script` admits them, and each finds its working root from `__file__` or the script's directory. Run as `${CLAUDE_PLUGIN_ROOT}/scripts/<name>` from `/writ:refresh-command` or `/writ:new-skill`, they read and would write inside the plugin directory, not the project. Under `install.sh` their root is the project and the effect is harmless. Not fixed here. The follow-up is to classify them dev-only or make them resolve the project from the current directory.
- **The `.writ/docs/` reference docs are absent in a plugin-only project (follow-up, drift DEV-006).** `install.sh` copies Writ's format docs into `.writ/docs/`. The plugin ships none, and the scaffold creates the empty directory only, so command references to `.writ/docs/<x>` find nothing there. Not fixed here. Candidate follow-ups: `scaffold-writ.py` copies the shipped docs from the plugin root, or a token rewrites the references to the plugin.
- **The Cursor plugin keeps the `scripts/` form.** Cursor documents no plugin-root variable for command bodies (V49), so its commands still need `install.sh`'s copy in the project. *Mitigation:* spec `2026-10-22-plugin-distribution` Rules 6, 9, and 10 require the Cursor adapter, the smoke test, and the README to say so.

## Implementation Notes

**Prerequisite:** met. Story 1 of `2026-10-22-plugin-distribution` marked the plugin script-root rows verified (V07, V08, V58) and chose layout B.

**Steps**

1. Add the `claude-code-plugin` target to `scripts/gen-platform-trees.py`, with `script_root` `${CLAUDE_PLUGIN_ROOT}/scripts` and a copy of the shipped set in `plugins/writ/scripts/` (Story 2).
2. Add `scripts/scaffold-writ.py`, the bash `init_writ_workspace` in both installers, and `/initialize` Step 0 (Story 4).
3. Run one smoke test over the three `install.sh` targets and the two plugin targets (Story 5).
4. Close the script-install-location issue with a `## Resolution` that names this record.

**Success criteria:** `gen-platform-trees.py --check` passes; `test_scaffold_writ.py` passes; the smoke test passes on the `install.sh` targets and the Claude Code plugin.

**Review trigger:** reconsider Option B when a user reports a collision between a project script and a shipped name, or when a supported platform stops substituting the plugin root in command bodies.

## Evidence: plugin verification record (read 2026-10-23)

| Observation | Source |
|---|---|
| `${CLAUDE_PLUGIN_ROOT}` is substituted anywhere in skill, command, and agent Markdown bodies (V07) | https://code.claude.com/docs/en/plugins/manifest-reference.md |
| The variable is not in the environment of commands run through the Bash tool (V08) | https://code.claude.com/docs/en/plugins/manifest-reference.md |
| A git-marketplace plugin is copied into the cache without files outside its directory (V34) | https://code.claude.com/docs/en/plugins/loading.md |
| Cursor expands `${CURSOR_PLUGIN_ROOT}` only in MCP server fields (V49) | https://cursor.com/docs/reference/plugins.md |
| `/writ:stub` ran in Claude Code 2.1.309 with the plugin root substituted in its body, under layout A and layout B (V58) | https://code.claude.com/docs/en/plugins/manifest-reference.md |

## References

- [ADR-029](adr-029-agent-cli-contract.md) — the agent CLI contract and the superseded consequence
- [ADR-030](adr-030-contract-verifier-boundary-front-door.md) — Phase 14 and its amendment to ADR-029
- [`2026-10-12-script-install-location`](../issues/improvements/2026-10-12-script-install-location.md) — the issue this record closes
- [`2026-10-22-plugin-distribution`](../specs/2026-10-22-plugin-distribution/spec.md) — spec, Rules 7 and 8; [`technical-spec.md`](../specs/2026-10-22-plugin-distribution/sub-specs/technical-spec.md) § Verification Record, § Relative Path Inventory, § `scaffold-writ.py`, § ADR-031 Outline; [`drift-log.md`](../specs/2026-10-22-plugin-distribution/drift-log.md) DEV-005, DEV-006
- [`.writ/docs/agent-cli-contract.md`](../docs/agent-cli-contract.md) — the contract and the Classification table
