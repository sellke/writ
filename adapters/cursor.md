# Cursor Setup Guide

Writ commands and agents are written natively for Cursor. This guide covers installation and configuration.

## Quick Install

Copy the commands, agents, and rules into your project's `.cursor/` directory:

```bash
# From your project root
mkdir -p .cursor/commands .cursor/agents .cursor/rules

# Commands
cp path/to/writ/commands/*.md .cursor/commands/

# Agents
cp path/to/writ/agents/*.md .cursor/agents/

# Rules file (alwaysApply: true — loads every Cursor session)
cp path/to/writ/cursor/writ.mdc .cursor/rules/

# Remove old Code Captain rules if present
rm -f .cursor/rules/cc.mdc
```

## Directory Structure

```
your-project/
├── .cursor/
│   ├── rules/
│   │   └── writ.mdc               # Writ identity & rules (alwaysApply: true)
│   ├── commands/
│   │   ├── create-spec.md         # /create-spec
│   │   ├── implement-story.md     # /implement-story
│   │   ├── refactor.md            # /refactor
│   │   ├── plan-product.md        # /plan-product
│   │   ├── create-adr.md          # /create-adr
│   │   ├── create-issue.md        # /create-issue
│   │   ├── research.md            # /research
│   │   ├── edit-spec.md           # /edit-spec
│   │   ├── verify-spec.md         # /verify-spec
│   │   ├── release.md             # /release
│   │   ├── security-audit.md      # /security-audit
│   │   ├── status.md              # /status
│   │   ├── migrate.md             # /migrate
│   │   ├── initialize.md          # /initialize
│   │   ├── explain-code.md        # /explain-code
│   │   ├── new-command.md         # /new-command
│   └── agents/
│       ├── architecture-check-agent.md  # Pre-implementation gate
│       ├── coding-agent.md              # TDD implementation
│       ├── review-agent.md              # Quality + security gate
│       ├── testing-agent.md             # Tests + coverage
│       ├── documentation-agent.md       # Framework-adaptive docs
│       └── user-story-generator.md      # Parallel story creation
└── .writ/                 # Created at runtime (add to .gitignore or commit)
    ├── specs/
    ├── product/
    ├── research/
    ├── decision-records/
    ├── docs/
    ├── issues/
    ├── explanations/
    └── state/
```

## Usage

Commands are invoked directly in Cursor's chat:

```
/create-spec "real-time notifications"
/implement-story
/status
/refactor
```

Cursor auto-discovers `.md` files in `commands/` and makes them available as slash commands.

## Native Tool Availability

These Cursor tools are used directly — no adapter needed:

| Tool | Used By | Purpose |
|------|---------|---------|
| `Task()` | implement-story, create-spec | Spawn sub-agents (coding, review, testing, docs, story generator) |
| `AskQuestion()` | create-spec, implement-story | Structured multi-choice questions with UI rendering |
| `codebase_search` | Most commands | Semantic code search across the project |
| `file_search` | Most commands | Find files by name/pattern |
| `todo_write` | implement-story | Visual progress tracking in Cursor sidebar |
| `read_file` | All commands | Read file contents |
| `run_terminal_cmd` | implement-story | Run shell commands |
| `list_dir` | initialize, status | List directory contents |

## Agent Configuration Notes

### Sub-Agent Models

Agents specify `model: "fast"` or inherit the default. In Cursor:
- `"fast"` → uses Cursor's fast model (typically Haiku-class)
- Default → inherits from your Cursor settings

For better story generation quality, you can edit `user-story-generator.md` to remove `model: "fast"` and use the default model instead.

### Read-Only Agents

The review agent specifies `readonly: true`. Cursor enforces this at the tool level — the agent literally cannot write files. This is stronger than prompt-based restrictions used on other platforms.

### Parallel Agent Limits

Cursor supports up to 4 concurrent `Task()` sub-agents in a single message. If you have more than 4 stories to generate, they'll be batched automatically (first 4, then next 4, etc.). This is handled in the `create-spec` command's Step 2.6.

## Command Workflow Integrity

When a Writ command uses Plan Mode for discovery (e.g., `/create-spec` Phase 1, `/plan-product` discovery), Plan Mode serves as a phase within the command — not a replacement for it.

**Rule:** After Plan Mode discovery completes, the command must resume its documented phases in Agent Mode and produce its documented artifacts (spec files, stories, ADRs, etc.). The conversation is an intermediate step, not the deliverable.

**Common failure:** The agent stays in Plan Mode and treats the planning conversation as the command's output, or switches to Agent Mode and offers to implement/build. Neither is correct — the command's next phase is artifact creation, not implementation.

**Reference:** System instructions → Prime Directive → Hard Constraints → "Never let Plan Mode absorb a command's workflow."

## Skills

Skills are the third Writ primitive (peer to commands and agents) — capability files that describe how to do a specific thing well. See [ADR-009](../.writ/decision-records/adr-009-command-agent-skill-boundary.md) for the verb/noun/tool framing and [`.writ/docs/skills.md`](../.writ/docs/skills.md) for the user-facing explainer.

Cursor uses a **platform-namespaced** install path (below). Codex CLI installs Writ skills at `.agents/skills/` per the AgentSkills standard — see [ADR-009 § Amendments](../.writ/decision-records/adr-009-command-agent-skill-boundary.md#amendments).

### Install Path

```
.cursor/skills/<name>/SKILL.md
```

`install.sh` and `update.sh` fan skills out alongside commands and agents using the same three-way overlay logic — local modifications to `.cursor/skills/<name>/SKILL.md` are preserved across updates. Sidecar files inside a skill folder (anything that isn't `SKILL.md`) are install-once: they're copied on first install and never overwritten on subsequent updates.

### Loading Mechanism

Cursor exposes installed skills via the `<agent_skills>` system context block. This means Cursor's auto-discovery will surface skill `description:` text to the model and make it eligible for ambient invocation by description match.

**Writ-authored skills opt out of ambient invocation** by setting `disable-model-invocation: true` in their frontmatter. This keeps every skill load deterministic and traceable in transcripts — agents and commands name skills explicitly when they need them. Community skills installed by other means (e.g. `clawhub`, `agentskills.io` catalogs) are out of Writ's control and follow whatever invocation behavior their installer configured.

### Invocation

Commands and agents that need a skill load it explicitly:

```
Read skills/<name>/SKILL.md
```

The orchestrator (or command body) issues the `Read` call when the relevant phase begins. The skill's content is then in the agent's context for that phase.

For commands and agents that declare `required_skills:` in their frontmatter (the convention defined in this spec — see Story 5 / `system-instructions.md`), the harness pre-loads each named skill before the consumer's first phase begins. `required_skills:` is reserve-only in the foundation spec; pilot skills will adopt it as they ship.

### Authoring & Reference

| Need | Tool |
|---|---|
| Scaffold a new skill | `/new-skill <name>` (boundary lint enforced at authoring time) |
| Lint an existing skill against the role convention | `/refresh-command` → boundary check |
| Cross-platform format spec | [AgentSkills standard](https://agentskills.io) |
| Boundary rationale | [ADR-009](../.writ/decision-records/adr-009-command-agent-skill-boundary.md) |
| User-facing explainer | [`.writ/docs/skills.md`](../.writ/docs/skills.md) |

## Project Initialization

For a new project, run these in order:

```
/initialize              # Detects greenfield/brownfield, sets up .writ/
/plan-product            # Define vision, mission, roadmap (optional)
/create-spec "feature"   # Spec your first feature
/implement-story         # Build it with the full SDLC pipeline
```

For an existing project:

```
/initialize              # Analyzes existing codebase, creates .writ/docs/
/status                  # See what's there
/create-spec "feature"   # Start speccing
```

## .gitignore Recommendations

```gitignore
# Writ state (ephemeral)
.writ/state/

# Keep specs and docs (valuable)
# !.writ/specs/
# !.writ/docs/
# !.writ/decision-records/
```

Or commit everything — specs, ADRs, and research are all worth version-controlling.

## Customization

### Adding Project Context

Create these files in `.writ/docs/` to give commands better context:

- **`tech-stack.md`** — Your stack, versions, key dependencies
- **`code-style.md`** — Coding conventions, patterns, naming rules
- **`best-practices.md`** — Project-specific practices, things to avoid
- **`objective.md`** — What the project does, who it's for

Commands like `create-spec` and `implement-story` auto-load these during context scanning.

### Knowledge Loading

`/implement-story` also scans `.writ/knowledge/` during Step 2. Cursor does not need a special runtime hook: the orchestrator extracts story keywords, searches knowledge entries, and passes the optional `knowledge_context` block directly into the architecture-check, coding, and review agent prompts.

### Preamble Convention

Every installed command has a final `## References` section pointing to `commands/_preamble.md` and `system-instructions.md`. Cursor discovers the command markdown as the slash command; the agent reads the linked preamble alongside the command context, so no Cursor-specific runtime injection hook is required.

### Creating New Commands

Use the meta-command:

```
/new-command "my-custom-workflow"
```

This walks you through creating a new command file following Writ conventions.
