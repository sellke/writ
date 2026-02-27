# Writ

AI-powered development workflow framework — contract-first specs, multi-agent SDLC, automated quality gates.

Issue writs. The framework executes them. ⚡

## What is Writ?

Writ is a structured development workflow system that turns rough ideas into shipped code through a disciplined pipeline:

```
/plan-product → /create-spec → /implement-spec → /verify-spec → /release
```

Each stage is documented as a command file that AI agents (Claude, GPT, etc.) follow precisely. The framework is **platform-agnostic** — it runs in Cursor, Claude Code, OpenClaw, or any AI coding assistant that can read markdown instructions.

## Key Features

- **Contract-first specifications** — No code until requirements are agreed upon
- **Multi-agent SDLC** — Dedicated agents for coding, review, testing, and documentation with feedback loops
- **Automated quality gates** — Architecture pre-check, lint/typecheck, security review, coverage enforcement (≥80%)
- **Parallel execution** — Independent stories run simultaneously with dependency resolution
- **Platform adapters** — Native support for Cursor, Claude Code, and OpenClaw

## Pipeline

```
┌──────────┐   ┌─────────────┐   ┌─────────────────┐   ┌─────────────┐   ┌─────────┐
│  plan-   │──▶│  create-    │──▶│  implement-     │──▶│  verify-    │──▶│ release │
│  product │   │  spec       │   │  spec           │   │  spec       │   │         │
└──────────┘   └─────────────┘   └─────────────────┘   └─────────────┘   └─────────┘
                                         │
                              Dependency graph + parallel batches
                                         │
                                    Per story (/implement-story):
                              ┌─ Arch check (pre-impl)
                              ├─ Coding agent (TDD)
                              ├─ Lint/typecheck gate
                              ├─ Review agent (+ security)
                              ├─ Testing agent (+ coverage)
                              ├─ Visual QA (optional, when mockups exist)
                              └─ Documentation agent

Lightweight path (/prototype) — no spec required:
   Quick Contract (2-3 Q's) → Coding Agent (TDD) → Lint & Typecheck → Done
                                     ↑ complexity? → escalate to /create-spec
```

## Commands

### Planning & Specification
| Command | Purpose |
|---------|---------|
| `/plan-product` | Product planning with contract-first approach |
| `/create-spec` | Feature specification with structured clarification |
| `/edit-spec` | Safely modify existing specifications |
| `/design` | Visual design companion — wireframes, mockup management, screenshot capture, visual comparison |
| `/create-adr` | Architecture Decision Records (auto-researches first) |
| `/create-issue` | Quick issue capture (<2 minutes) |
| `/research` | Systematic 4-phase research workflow |

### Implementation & Quality
| Command | Purpose |
|---------|---------|
| `/prototype` | **Lightweight executor.** No spec needed — describe the change, answer 2-3 questions, ship with TDD + lint. Auto-detects when to escalate to `/create-spec`. |
| `/implement-spec` | **Spec orchestrator.** Reads a spec, builds dependency graph, resolves parallel batches, calls `/implement-story` per story. End-to-end uninterrupted execution. |
| `/implement-story` | **Per-story executor.** 6-gate SDLC pipeline: arch-check → code → lint → review → test → docs. |
| `/refactor` | Scoped refactoring — file analysis, deduplication, dead code removal, pattern modernization, type strengthening. Verified after every change. |
| `/status` | Comprehensive project status report |

### Validation & Release
| Command | Purpose |
|---------|---------|
| `/verify-spec` | 8-check validation: integrity, status sync, completion, dependencies, tests, coverage, contract drift |
| `/security-audit` | Full security audit: dependencies, secrets, code analysis, infrastructure |
| `/release` | Changelog generation, version bump, git tag, GitHub release |

### Learning & Maintenance
| Command | Purpose |
|---------|---------|
| `/refresh-command` | **Learning loop.** Scans agent transcripts, identifies friction patterns, proposes concrete diffs to command files. Commands get better through use. |

### Setup & Utilities
| Command | Purpose |
|---------|---------|
| `/initialize` | Project setup (greenfield/brownfield detection) |
| `/explain-code` | Code explanation with diagrams |
| `/new-command` | Create new Writ commands |
| `/test-database` | Database diagnostic and auto-fixing |
| `/prisma-migration` | Prisma migration workflow |

## Agents

The `/implement-story` command orchestrates these specialized agents:

| Agent | Role |
|-------|------|
| Architecture Check | Pre-implementation design review (PROCEED/CAUTION/ABORT) |
| Coding Agent | TDD implementation — tests first, then code |
| Review Agent | Code quality + security gate + spec drift analysis (PASS/FAIL/PAUSE, max 3 iterations) |
| Testing Agent | Test execution + coverage enforcement (≥80% on new code) |
| Documentation Agent | Framework-adaptive docs (VitePress, Docusaurus, README, etc.) |
| Visual QA | Optional UI validation — compares implementation screenshots against mockups |
| User Story Generator | Parallel story file creation during `/create-spec` |

## Platform Support

Writ runs on any AI coding platform. Adapters translate tool calls:

| Platform | Setup Guide | Key Pattern |
|----------|-------------|-------------|
| **Cursor** | [`adapters/cursor.md`](adapters/cursor.md) | Native — `Task()`, `AskQuestion()` |
| **Claude Code** | [`adapters/claude-code.md`](adapters/claude-code.md) | `claude -p`, `CLAUDE.md`, `--allowedTools` |
| **OpenClaw** | [`adapters/openclaw.md`](adapters/openclaw.md) | `sessions_spawn`, Telegram buttons, `exec` |

## Migrating from Code Captain

Already using Code Captain? Migrate in seconds — all specs, stories, ADRs, and progress preserved:

```bash
# Clone writ, run migration from your project root
git clone https://github.com/sellke/writ.git /tmp/writ
bash /tmp/writ/scripts/migrate.sh

# Then install Writ commands + agents
cp /tmp/writ/commands/*.md .cursor/commands/
cp /tmp/writ/agents/*.md .cursor/agents/
```

Preview first with `--dry-run`:
```bash
bash /tmp/writ/scripts/migrate.sh --dry-run
```

See [`commands/migrate.md`](commands/migrate.md) for the full interactive migration command.

## Quick Start

### Cursor

```bash
# Copy commands and agents into your project
mkdir -p .cursor/commands .cursor/agents
cp writ/commands/*.md .cursor/commands/
cp writ/agents/*.md .cursor/agents/
cp writ/system-instructions.md .cursor/

# Start using
# In Cursor chat: /create-spec "my feature"
```

### Claude Code

```bash
# Copy to .claude/ directory
mkdir -p .claude/commands .claude/agents
cp writ/commands/*.md .claude/commands/
cp writ/agents/*.md .claude/agents/

# Create CLAUDE.md (see adapters/claude-code.md for template)

# Start using
claude
> /create-spec "my feature"
```

### OpenClaw

```bash
# Install as a skill
cp -r writ/ ~/.openclaw/workspace/skills/writ/

# Commands are available via the skill system
```

## Directory Structure

When Writ runs, it creates a `.writ/` directory in your project:

```
.writ/
├── specs/                    # Feature specifications
│   └── YYYY-MM-DD-feature/
│       ├── spec.md           # Main specification (from contract)
│       ├── spec-lite.md      # Condensed for AI context
│       ├── user-stories/     # Individual story files
│       │   ├── README.md     # Progress tracking
│       │   └── story-N-*.md  # 5-7 tasks each
│       ├── drift-log.md      # Spec amendment record (auto-generated)
│       └── sub-specs/        # Technical deep-dives
├── product/                  # Product planning docs
├── decision-records/         # Architecture Decision Records
├── research/                 # Research outputs
├── security/                 # Security audit reports
├── issues/                   # Quick-captured issues
├── docs/                     # Project documentation
│   ├── tech-stack.md
│   ├── code-style.md
│   └── best-practices.md
├── explanations/             # Code explanations
└── state/                    # Workflow state (ephemeral)
```

## Philosophy

1. **Contract-first** — Establish agreement before creating files. Challenge bad ideas early.
2. **TDD always** — Tests first, then implementation. 100% pass rate mandatory.
3. **Quality gates, not quality hopes** — Automated checks at every stage.
4. **Parallel by default** — Independent work runs simultaneously.
5. **Platform-agnostic** — Markdown instructions work anywhere AI agents run.

## Attribution

Writ is derived from [Code Captain](https://github.com/devobsessed/code-captain) by [@DevObsessed](https://github.com/devobsessed), originally released under the MIT License. This project extends the original with multi-agent orchestration, automated quality gates, platform adapters, and additional commands.

## License

MIT — see [LICENSE](LICENSE).
