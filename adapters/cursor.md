# Cursor Setup Guide

Writ commands and agents are written natively for Cursor. This guide covers installation and configuration.

## Quick Install

Copy the commands and agents into your project's `.writ/` directory:

```bash
# From your project root
mkdir -p .writ/commands .writ/agents

# Commands
cp path/to/writ/commands/*.md commands/

# Agents
cp path/to/writ/agents/*.md agents/

# System instructions (applies to all Cursor sessions)
cp path/to/writ/system-instructions.md .writ/
```

## Directory Structure

```
your-project/
├── .writ/
│   ├── system-instructions.md     # Writ identity & rules (alwaysApply: true)
│   ├── commands/
│   │   ├── create-spec.md         # /create-spec
│   │   ├── implement-story.md     # /implement-story
│   │   ├── execute-task.md        # /execute-task
│   │   ├── plan-product.md        # /plan-product
│   │   ├── create-adr.md          # /create-adr
│   │   ├── create-issue.md        # /create-issue
│   │   ├── research.md            # /research
│   │   ├── edit-spec.md           # /edit-spec
│   │   ├── verify-spec.md         # /verify-spec
│   │   ├── status.md              # /status
│   │   ├── swab.md                # /swab
│   │   ├── refresh-docs.md        # /refresh-docs
│   │   ├── initialize.md          # /initialize
│   │   ├── explain-code.md        # /explain-code
│   │   ├── new-command.md         # /new-command
│   │   ├── test-database.md       # /test-database
│   │   └── prisma-migration.md    # /prisma-migration
│   └── agents/
│       ├── coding-agent.md        # Spawned by implement-story
│       ├── review-agent.md        # Spawned by implement-story
│       ├── testing-agent.md       # Spawned by implement-story
│       ├── documentation-agent.md # Spawned by implement-story
│       └── user-story-generator.md # Spawned by create-spec
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
/swab
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
| `todo_write` | execute-task, implement-story | Visual progress tracking in Cursor sidebar |
| `read_file` | All commands | Read file contents |
| `run_terminal_cmd` | execute-task, test-database | Run shell commands |
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

Commands like `create-spec` and `execute-task` auto-load these during context scanning.

### Creating New Commands

Use the meta-command:

```
/new-command "my-custom-workflow"
```

This walks you through creating a new command file following Writ conventions.
