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
│   │   ├── test-database.md       # /test-database
│   │   └── prisma-migration.md    # /prisma-migration
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
| `run_terminal_cmd` | implement-story, test-database | Run shell commands |
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

### Creating New Commands

Use the meta-command:

```
/new-command "my-custom-workflow"
```

This walks you through creating a new command file following Writ conventions.
