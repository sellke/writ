# ADR-036: Writ Ships as Plain-Language Skills Named `writ-*`

> **Date:** 2026-11-09
> **Status:** Accepted
> **Category:** Packaging & Platforms
> **Deciders:** @AdamSellke
> **Origin:** `/plan-product --reconcile` (2026-11-09). The maintainer's direction: stay compatible with Claude on the desktop and the command line, OpenAI on the desktop and the command line, and Cursor; use plain language; devise a naming convention that sets Writ's commands apart from other skills and tools.
> **Supersedes:** [ADR-009](adr-009-command-agent-skill-boundary.md) (three primitives), [ADR-014](adr-014-skill-lifecycle.md), [ADR-016](adr-016-model-tier-delegation.md) and [ADR-024](adr-024-model-delegation.md) (model tiers), [ADR-020](adr-020-component-contract.md), [ADR-026](adr-026-constraint-test-pruning.md), [ADR-029](adr-029-agent-cli-contract.md), [ADR-031](adr-031-script-location.md), [ADR-015](adr-015-leanness-self-governance.md) and [ADR-019](adr-019-full-surface-leanness-measurement.md) (leanness governance), and [ADR-001](adr-001-askquestion-vs-plan-mode.md) as a mechanism.
> **Evidence base:** [2026-11-09 surface audit](../research/2026-11-09-writ-1.0-surface-audit.md) §§ 1, 3, 6.

## Context

Writ 0.49 had three kinds of component (commands, agents, skills), written against platform-neutral tool names that four adapters (1,894 lines) translated. A generator (1,822 lines, 4,328 lines of tests) produced per-platform trees, so each command existed three times and each agent six. Install, update, and uninstall were 3,708 lines of bash that also merged blocks into `CLAUDE.md`, `AGENTS.md`, and a Cursor rule.

As of 2026-11-09, Claude Code, Cursor, and Codex (command line and the ChatGPT desktop app) all load Agent Skills: a folder with a `SKILL.md` carrying `name` and `description`. Claude Code has merged custom commands into skills. Cursor ships a command that converts commands to skills.

Names collide. Cursor has built-in `/review`, `/loop`, `/autopilot`, and `/canvas`. Codex has `/review`, `/status`, `/plan`, and `/init`. Claude Code has `/review`, `/init`, and more. Writ already renamed `/design` once for this reason. The user's own tool list in the session that made this decision held `create-spec` beside `write-spec`, and `security-audit` beside `security-review`.

## Decision Drivers

1. **One source, no copies.** Nothing generated, nothing to keep in step.
2. **Works on five surfaces** without a translation layer.
3. **A person can tell at a glance what belongs to Writ.**
4. **Install is one line and safe to repeat.**

## Considered Options

### Option A: Keep commands, agents, adapters, and the generator

- **Pros:** Proven on Cursor and Claude Code.
- **Cons:** Most of the install and eval weight exists to serve this. Codex never got slash commands from it.

### Option B: Skills, with names left as they are

- **Pros:** Familiar names.
- **Cons:** `review`, `status`, `ship`, and `release` collide with or sit beside platform and third-party commands.

### Option C: Plain-language skills, every one named `writ` or `writ-<verb>` (chosen)

## Decision

**1. Everything Writ ships is a skill.** One folder, `plugins/writ/`, is both the source and the plugin. It holds `skills/` and three small manifests (a portable `plugin.json`, `.claude-plugin/plugin.json`, `.cursor-plugin/plugin.json`). Three marketplace files at the repository root point at it. There are no agent definition files: the verifier is a skill that a fresh helper is told to follow, which works wherever a helper can be started.

**2. Skills are written in plain language.** A skill says what must happen ("ask the person one question", "start a fresh helper that has not seen your work"), never which tool does it. `scripts/check.py` fails on a platform tool name in a skill. Frontmatter carries `name` and `description` only.

**3. Naming.** The front door is `writ`. Every other skill is `writ-<verb>`: `writ-plan`, `writ-research`, `writ-prototype`, `writ-spec`, `writ-build`, `writ-verify`, `writ-ship`, `writ-issue`, `writ-retro`. The optional second reader is `writ-jev`. The name is the same on every platform, so one skill can name another in its text. Under a Claude Code plugin the platform adds its own prefix (`/writ:writ-build`); typing `writ-build` still finds it. The project folder stays `.writ/`. Everything Writ owns starts with `writ`.

**4. Shared rules are one file.** `skills/writ/rules.md` holds who decides, honest assessment, proof, how to write for the person, and where records live. Each skill reads it first. Nothing is merged into a project's standing instruction files.

**5. Install.** Claude Code: the plugin. Cursor and Codex: the plugin where the marketplace allows, or `scripts/install.sh`, which copies the skill folders into `.agents/skills/` (read by both) or `.claude/skills/`, keeps a manifest of hashes, never overwrites a file the person changed, and removes only what it installed. A project with a 0.x install is told to run the 0.49 uninstaller first.

**6. The only code that ships** is `writ-jev/jev.py` ([ADR-037](adr-037-jev-second-reader.md)), inside its skill folder, optional, standard-library Python.

## Consequences

**Positive**

- Adapters, generated trees, the generator, model-tier configuration, the component contract, and the three lifecycle commands are gone.
- Codex users get real, invocable skills for the first time.
- A new platform that reads Agent Skills needs a manifest, not an adapter.

**Negative**

- Plain language leans on the model mapping "ask the person" or "start a fresh helper" to its own tools. A weaker model or a platform without helpers will do this worse than an adapter row would.
- The Prime Directive is no longer always on. It applies when a Writ skill runs, not in every session.
- Under the Claude Code plugin the name stutters (`/writ:writ-build`).
- A project that installs for both Claude Code (into `.claude/skills/`) and Cursor shows Cursor two copies, because Cursor also reads `.claude/skills/`. The plugin avoids this on Claude Code.
- Every 0.x command name is gone. Muscle memory and any saved prompts break.

**Review triggers**

- A platform stops loading skills from the folders named above, or changes how they are invoked.
- A skill misfires on a platform because a plain-language instruction was misread. Reword it first; add a platform note only if rewording fails twice.
- The Cursor or Codex marketplace accepts the plugin: make it the documented install there and retire that path from `install.sh`.
