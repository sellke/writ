<div align="center">
<pre>
/\/\/\/\/\/\/\/\/\/\/\/\/\/\/\/\/\/\/\/\
  ██╗    ██╗██████╗ <span style="color: #FF9900;">  ██╗    </span>████████╗  
  ██║    ██║██╔══██╗<span style="color: #FF9900;">  ╚██╗   </span>╚══██╔══╝  
  ██║ █╗ ██║██████╔╝<span style="color: #FF9900;"> ██████╗ </span>   ██║     
  ██║███╗██║██╔══██╗<span style="color: #FF9900;"> ╚══██╔╝ </span>   ██║     
  ╚███╔███╔╝██║  ██║<span style="color: #FF9900;">   ██╔╝  </span>   ██║     
   ╚══╝╚══╝ ╚═╝  ╚═╝<span style="color: #FF9900;">   ╚═╝   </span>   ╚═╝     
\/\/\/\/\/\/\/\/\/\/\/\/\/\/\/\/\/\/\/\/
</pre>

**AI-powered development workflow framework**<br>
Contract-first specs · Multi-agent SDLC · Automated quality gates · Opinionated by default

⚡ *A writ is a written command by an authority--you. The framework executes them.*

</div>

---

## What is Writ?

Writ is a self-improving development methodology that turns rough ideas into shipped code through a disciplined pipeline:

```
/plan-product → /create-spec → /assess-spec → /implement-spec → /review → /ship → /release
```

Each stage is a markdown command file that AI agents follow precisely. The framework is **platform-agnostic** — it runs in Cursor, Claude Code, OpenClaw, or any AI coding assistant that can read markdown. Commands lead with opinionated recommendations, challenge premises, and improve through use.

## Key Features

- **Contract-first specifications** — No code until requirements are agreed upon
- **Multi-agent SDLC** — Dedicated agents for coding, review, testing, and documentation with feedback loops
- **Automated quality gates** — Architecture pre-check, lint/typecheck, security review, coverage enforcement (≥80%)
- **Spec assessment** — `/assess-spec` flags sizing, complexity, and context accumulation risks before you build. Recommends specific decomposition strategies. Runs automatically as a pre-flight check in `/implement-spec`.
- **Cross-story continuity** — "What Was Built" records capture implementation reality from review outputs and automatically pass to downstream stories, enabling accurate dependency integration
- **Parallel execution** — Independent stories run simultaneously with dependency resolution
- **Opinionated guidance** — Commands lead with recommendations, challenge premises, and push for the best version of every idea
- **Self-improving** — `/refresh-command` scans transcripts and proposes concrete improvements. Commands get better through use.
- **Platform adapters** — Native support for Cursor, Claude Code, and OpenClaw

## Pipeline

```
┌──────────┐   ┌─────────────┐   ┌─────────────┐   ┌─────────────────┐   ┌──────────┐   ┌──────────┐   ┌─────────┐
│  plan-   │──▶│  create-    │──▶│  assess-    │──▶│  implement-     │──▶│  review  │──▶│  ship    │──▶│ release │
│  product │   │  spec       │   │  spec       │   │  spec           │   │ (opt.)   │   │          │   │         │
└──────────┘   └─────────────┘   └─────────────┘   └─────────────────┘   └──────────┘   └──────────┘   └─────────┘
                     │              Sizing checks       │                    │              │
               Error mapping     Context budget    Parallel batches   Failure modes   Merge → Test
               Shadow paths      Decomposition     Dependency graph   Shadow paths    Split commits
               Edge cases        recommendations         │            Edge cases      Open PR
                                                    Per story (/implement-story):
                              ┌─ Arch check (pre-impl)
                              ├─ Boundary map (Gate 0.5 — owned/readable scope)
                              ├─ Coding agent (TDD) + loads "What Was Built" from deps
                              ├─ Lint/typecheck gate
                              ├─ Review agent (+ security + drift)
                              ├─ Testing agent (+ coverage)
                              ├─ Visual QA (optional)
                              ├─ Documentation agent
                              └─ "What Was Built" record appended to story file

Lightweight path (/prototype) — no spec required:
   Describe change → [Visual Preview] → Coding Agent (TDD) → Lint → Done
                                              ↑ complexity? → escalate to /create-spec

Feedback loop (/retro + /refresh-command):
   Git metrics → Patterns → Trends    |    Transcript scan → Friction → Command diffs
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
| `/implement-story` | **Per-story executor.** SDLC pipeline: arch-check → **boundary map (Gate 0.5)** → coding (TDD) → lint → review → drift → testing → visual QA (optional) → docs. `--quick` skips arch, boundary, review, drift, docs. |
| `/refactor` | Scoped refactoring — file analysis, deduplication, dead code removal, pattern modernization, type strengthening. Verified after every change. |
| `/status` | Comprehensive project status report |

### Shipping & Review
| Command | Purpose |
|---------|---------|
| `/review` | **Pre-landing code review.** Error & rescue maps, shadow path tracing, interaction edge cases, failure modes registry, mandatory architecture diagrams. Produces judgment, not checklists. |
| `/ship` | **Unified shipping workflow.** Detect conventions → merge default branch → (optional `/ship --test`) → split commits → create PR with structured body, optional inline spec health, and auto-labels. |

### Validation & Release
| Command | Purpose |
|---------|---------|
| `/assess-spec` | **Pre-implementation health check.** Flags oversized stories, deep dependency chains, context accumulation risks, and file-overlap conflicts. Recommends specific decomposition strategies. Also runs as a pre-flight check inside `/implement-spec`. |
| `/verify-spec` | Metadata diagnostic (checks 1–7): story/README integrity, completion, dependencies, deliverables, contract drift — auto-fix by default; optional standalone pass |
| `/security-audit` | Full security audit: dependencies, secrets, code analysis, infrastructure |
| `/release` | Inline release gate (spec checks, build probes, conditional test suite) → changelog, version bump, git tag, GitHub release |

### Feedback & Learning
| Command | Purpose |
|---------|---------|
| `/retro` | **Git-based retrospective.** Commits, LOC, test ratio, session detection, streaks, Ship of the Week, trend comparison. Persistent JSON snapshots for long-term analysis. |
| `/refresh-command` | **Learning loop.** Scans agent transcripts, identifies friction patterns, proposes concrete diffs to command files. Commands get better through use. |

### Setup & Utilities
| Command | Purpose |
|---------|---------|
| `/initialize` | Project setup (greenfield/brownfield detection) |
| `/explain-code` | Code explanation with diagrams |
| `/new-command` | Create new Writ commands |
| `/migrate` | Code Captain → Writ migration (preserves specs, stories, ADRs) |

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

## Quick Start

Writ ships 24 commands, but you only need five to go from idea to PR:

| Command | What it does |
|---------|--------------|
| `/prototype` | Quick changes — no spec needed. Describe it, ship it. |
| `/create-spec` | Turn a feature idea into a structured contract with stories. |
| `/implement-spec` | Execute a spec end-to-end: dependency graph → parallel stories → quality gates. |
| `/ship` | Merge, split commits, open a PR. |
| `/status` | See where everything stands — specs, branches, progress. |

Everything else (planning, reviews, retros, releases) is there when you need it. Start here.

### Cursor (one-line install)

From your project root:

```bash
bash <(curl -s https://raw.githubusercontent.com/sellke/writ/main/scripts/install.sh)
```

This copies all commands, agents, rules, and system instructions into `.cursor/`, creates the `.writ/` workspace, and commits the result. Preview first with `--dry-run`:

```bash
bash <(curl -s https://raw.githubusercontent.com/sellke/writ/main/scripts/install.sh) --dry-run
```

Then in Cursor chat: `/create-spec "my feature"`

### Updating

```bash
bash <(curl -s https://raw.githubusercontent.com/sellke/writ/main/scripts/update.sh)
```

The updater uses a manifest (`.cursor/.writ-manifest`) to track what was installed. Files you haven't touched update silently. Files you've customized are **never overwritten** — you're told which ones were preserved. Files removed upstream are cleaned up.

| Flag | Effect |
|------|--------|
| `--dry-run` | Preview changes without applying |
| `--force` | Overwrite all files, including your customizations |
| `--no-commit` | Don't auto-commit after update |

To reset a single file to upstream: delete it and re-run update.

### Claude Code

```bash
mkdir -p .claude/commands .claude/agents
cp writ/commands/*.md .claude/commands/
cp writ/agents/*.md .claude/agents/

# Create CLAUDE.md (see adapters/claude-code.md for template)

claude
> /create-spec "my feature"
```

### OpenClaw

```bash
cp -r writ/ ~/.openclaw/workspace/skills/writ/
```

## Migrating from Code Captain

Already using Code Captain? Migrate in seconds — all specs, stories, ADRs, and progress preserved:

```bash
bash <(curl -s https://raw.githubusercontent.com/sellke/writ/main/scripts/migrate.sh)
```

Preview first with `--dry-run`:

```bash
bash <(curl -s https://raw.githubusercontent.com/sellke/writ/main/scripts/migrate.sh) --dry-run
```

Then install Writ with `install.sh` as shown above. See [`commands/migrate.md`](commands/migrate.md) for the full interactive migration command.

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
├── retros/                   # Retrospective JSON snapshots
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
2. **Opinionated by default** — Lead with the recommendation, explain why, then offer alternatives. Judgment, not menus.
3. **TDD always** — Tests first, then implementation. 100% pass rate mandatory.
4. **Quality gates, not quality hopes** — Automated checks at every stage.
5. **Parallel by default** — Independent work runs simultaneously.
6. **Self-improving** — Commands get better through use. `/refresh-command` + `/retro` close the feedback loop.
7. **Platform-agnostic** — Markdown instructions work anywhere AI agents run.

## Attribution

Writ is derived from [Code Captain](https://github.com/devobsessed/code-captain) by [@DevObsessed](https://github.com/devobsessed), originally released under the MIT License. This project extends the original with multi-agent orchestration, automated quality gates, platform adapters, and additional commands.

## License

MIT — see [LICENSE](LICENSE).
