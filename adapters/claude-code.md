# Claude Code Platform Adapter

Native integration with Claude Code's subagent system, git worktrees, agent teams, and hooks. Writ agents are defined as `.claude/agents/` markdown files with YAML frontmatter — no shell scripting needed.

---

## Installation

### Automated (recommended)

```bash
bash <(curl -s https://raw.githubusercontent.com/sellke/writ/main/scripts/install.sh) --platform claude
```

This installs all commands, Claude Code–native agents (with YAML frontmatter), and `CLAUDE.md` into your project. Preview first with `--dry-run`. Update later with:

```bash
bash <(curl -s https://raw.githubusercontent.com/sellke/writ/main/scripts/update.sh) --platform claude
```

The updater uses a manifest (`.claude/.writ-manifest`) for three-way overlay merges — files you've customized are never overwritten.

### Manual Installation

If you prefer to install manually, or need to customize the setup:

#### Step 1: Copy files

```bash
mkdir -p .claude/agents .claude/commands .writ/state
cp path/to/writ/commands/*.md .claude/commands/
cp path/to/writ/claude-code/agents/*.md .claude/agents/
cp path/to/writ/claude-code/CLAUDE.md ./CLAUDE.md
```

Agent source files live in `claude-code/agents/` in the Writ repo — these are Claude Code–native with YAML frontmatter (`name`, `tools`, `model`, `permissionMode`, `isolation`, `maxTurns`, `memory`).

#### Step 2: Project Context (Optional)

```bash
mkdir -p .writ/docs

cat > .writ/docs/tech-stack.md << 'EOF'
# Tech Stack
- Runtime: [your runtime]
- Framework: [your framework]
- Database: [your DB]
- Testing: [your test runner]
EOF
```

#### Step 3: .gitignore

```gitignore
# Writ ephemeral state
.writ/state/

# Claude Code agent memory (project-level, consider committing for team use)
# .claude/agent-memory/
```

### Final Structure

```
your-project/
├── CLAUDE.md                          # Auto-loaded every session
├── .claude/
│   ├── agents/                        # Native subagent definitions
│   │   ├── writ-architect.md          # isolation: worktree, plan mode
│   │   ├── writ-coder.md             # isolation: worktree, acceptEdits
│   │   ├── writ-reviewer.md          # read-only, persistent memory
│   │   ├── writ-tester.md            # acceptEdits
│   │   ├── writ-documenter.md        # sonnet model, acceptEdits
│   │   └── writ-story-gen.md         # haiku model, worktree
│   ├── commands/                      # Writ command workflows
│   │   ├── create-spec.md
│   │   ├── implement-story.md
│   │   └── ... (all commands)
│   └── agent-memory/                  # Persistent agent memory (auto-created)
│       ├── writ-architect/
│       ├── writ-coder/
│       └── writ-reviewer/
└── .writ/                             # Runtime artifacts
    ├── specs/
    ├── decision-records/
    └── state/
```

---

## Key Features Used

### Git Worktree Isolation (`isolation: worktree`)

The game-changer for parallel execution. When a subagent has `isolation: worktree`, Claude Code:
1. Creates a temporary git worktree (isolated copy of the repo)
2. Runs the subagent in that worktree (no file conflicts with other agents)
3. Merges changes back when the subagent completes
4. Auto-cleans the worktree if no changes were made

**Writ agents using worktrees:**
- `writ-architect` — reads codebase without interfering
- `writ-coder` — implements in isolation, no conflicts with parallel stories
- `writ-story-gen` — generates story files in parallel without conflicts

**Why this matters for `/implement-story --all`:**
Multiple stories can be implemented simultaneously in separate worktrees. Each coder gets its own branch/worktree, implements independently, and changes merge back. No file locking, no conflicts on shared files.

### Persistent Memory (`memory: project`)

Agents learn across sessions. The review agent remembers patterns it's seen, the architect remembers architectural decisions, the coder remembers conventions.

```
.claude/agent-memory/
├── writ-architect/MEMORY.md    # "This project uses repository pattern for data access"
├── writ-coder/MEMORY.md        # "Tests use vitest with MSW for API mocking"
└── writ-reviewer/MEMORY.md     # "Previous review caught SQL injection in routes/search.ts"
```

### Model Selection

Each agent uses the most cost-effective model for its role:

| Agent | Model | Rationale |
|-------|-------|-----------|
| writ-architect | inherit (Opus/Sonnet) | Needs deep reasoning about architecture |
| writ-coder | inherit | Needs full coding capability |
| writ-reviewer | inherit | Needs thorough analysis |
| writ-tester | inherit | Needs to understand and fix code |
| writ-documenter | sonnet | Good enough for docs, saves cost |
| writ-story-gen | haiku | Template-based generation, fast + cheap |

### Permission Modes

| Agent | Mode | Why |
|-------|------|-----|
| writ-architect | `plan` | Read-only analysis, no modifications |
| writ-coder | `acceptEdits` | Auto-accept file changes (TDD flow) |
| writ-reviewer | `plan` | Read-only review, cannot modify |
| writ-tester | `acceptEdits` | May need to fix tests |
| writ-documenter | `acceptEdits` | Creates/updates doc files |
| writ-story-gen | `acceptEdits` | Creates story files |

---

## Tool Mapping (Cursor → Claude Code)

### Quick Reference

| Cursor Tool | Claude Code Native | Notes |
|---|---|---|
| `Task({ prompt })` | Automatic delegation to named subagent | Claude routes based on `description` field |
| `Task({ readonly: true })` | `permissionMode: plan` + `disallowedTools: Write, Edit` | Enforced at tool level |
| `AskQuestion()` | Formatted text with numbered options | No interactive UI |
| `codebase_search` | `Grep("pattern")` or `Bash("rg 'pattern'")` | Built-in Grep tool |
| `file_search` | `Glob("**/pattern*")` | Built-in Glob tool |
| `todo_write` | `Write(".writ/state/tracking.json")` | File-based |
| `read_file` | `Read(path)` | Direct equivalent |
| `run_terminal_cmd` | `Bash(command)` | Direct equivalent |
| `list_dir` | `Glob("dir/*")` or `Bash("ls")` | Built-in Glob tool |

### Triggering Agents

Claude Code delegates to subagents automatically based on the `description` field. In Writ command workflows, you can explicitly request delegation:

```
Use the writ-coder agent to implement this story.
Use the writ-reviewer agent to review the implementation.
```

Or Claude will delegate automatically when the task matches an agent's description.

### Structured Questions (no AskQuestion equivalent)

```
**Feature Clarification - Round 1**

Who is the primary user of this feature?
  1. End users/customers
  2. Administrators/internal staff
  3. Developers/API consumers
  4. Multiple user types

Reply with the number of your choice.
```

---

## Workflow Patterns

### implement-story: Single Story

```
1. Orchestrator gathers context (reads story, spec, codebase)
2. Delegates to writ-architect (worktree, read-only)
   → Returns PROCEED/CAUTION/ABORT
3. Delegates to writ-coder (worktree, full access)
   → Implements in isolation, returns summary
4. Orchestrator runs lint/typecheck inline
5. Delegates to writ-reviewer (read-only, uses memory)
   → Returns PASS/FAIL
6. If FAIL: re-delegate to writ-coder with feedback (max 3×)
7. Delegates to writ-tester (full access)
   → Returns PASS/FAIL with coverage
8. Delegates to writ-documenter (sonnet, full access)
   → Updates docs
9. Orchestrator updates story status, commits
```

### implement-story --all: Agent Teams (Experimental)

For full spec execution with inter-agent communication:

```
Enable agent teams:
  CLAUDE_CODE_EXPERIMENTAL_AGENT_TEAMS=1

Create a team to implement the spec at .writ/specs/2026-02-22-feature/.
Spawn teammates:
  - Story 1 implementer (use writ-coder agent in worktree)
  - Story 3 implementer (use writ-coder agent in worktree)
  - Reviewer (use writ-reviewer agent, reviews stories as they complete)

Stories 1 and 3 have no dependencies and can run in parallel.
After both complete, the reviewer reviews them.
Then spawn Story 2 (depends on 1) and Story 4 (depends on 3).
```

Agent teams provide:
- Shared task list (stories become tasks)
- Inter-agent messaging (reviewer can send feedback to coders)
- Self-coordination (agents claim available tasks)
- Plan approval (architect reviews before coders implement)

### create-spec: Parallel Story Generation

```
# Orchestrator locks contract, then delegates story generation:
# Each runs in its own worktree — no file conflicts

Use the writ-story-gen agent to create story-1-auth.md at [path].
  Context: [contract + requirements for story 1]

Use the writ-story-gen agent to create story-2-api.md at [path].
  Context: [contract + requirements for story 2]

Use the writ-story-gen agent to create story-3-ui.md at [path].
  Context: [contract + requirements for story 3]

# All run in parallel in separate worktrees
# Changes merge back automatically
```

### Quality Gates with Hooks

Use Claude Code hooks to enforce quality gates automatically:

```json
// .claude/settings.json
{
  "hooks": {
    "SubagentCompleted": [
      {
        "matcher": "writ-coder",
        "hooks": [{
          "type": "command",
          "command": "cd $WORKTREE && npm test && npx tsc --noEmit"
        }]
      }
    ]
  }
}
```

If tests fail after the coder completes, the hook returns exit code 2 and sends the coder back to fix.

---

## CLI Usage

### Interactive Session

```bash
cd your-project
claude

> /create-spec "user authentication"
> /implement-story
> /status
```

### One-Shot

```bash
claude -p "/status"
claude -p "/create-issue 'Login page crashes on empty email'"
```

### With Specific Agents

```bash
# Run with inline agent override
claude --agents '{
  "quick-reviewer": {
    "description": "Quick code review",
    "prompt": "Review the last commit for issues.",
    "tools": ["Read", "Grep", "Glob", "Bash"],
    "model": "haiku"
  }
}'
```

### Permission Bypass (CI/automation)

```bash
claude -p "/verify-spec --check" --permission-mode acceptEdits
```

---

## Ralph / CLI Story Pipeline

Ralph extends Writ with autonomous multi-spec execution via CLI. The developer plans in Cursor (`/ralph plan`), hands off to a CLI loop (`./ralph.sh`), and reviews in Cursor (`/ralph status`).

### When to Use the CLI Pipeline

| Use Case | Tool |
|----------|------|
| Interactive single-story implementation | `/implement-story` (Cursor) |
| Supervised multi-story execution | `/implement-spec` (Cursor) |
| Autonomous overnight/batch execution | `./ralph.sh` (CLI) |

### How It Works

1. **Plan** — `/ralph plan` in Cursor scans specs, resolves dependencies, generates `scripts/PROMPT_build.md` and `scripts/ralph.sh` tailored to the project
2. **Execute** — `./ralph.sh` loops: each iteration pipes `PROMPT_build.md` to the CLI agent (fresh context), implements one story, validates with tests/lint, commits, pushes
3. **Review** — `/ralph status` in Cursor reads `.writ/state/ralph-*.json` and presents progress

### CLI Agent Invocation

```bash
claude -p "$(cat PROMPT_build.md)" \
  --dangerously-skip-permissions \
  --model opus \
  --verbose
```

Flags are configurable via `.writ/config.md` Ralph keys (`Ralph CLI Agent`, `Ralph CLI Model`, `Ralph CLI Flags`).

### Key Differences from Supervised Pipeline

- **Review via sub-agent** — the CLI agent spawns a read-only review sub-agent (Phase 2.5) for AC verification, code quality, security, and drift analysis. Max 2 review iterations per story. Large drift escalates to developer.
- **No architecture check** — single-story scope and dependency ordering manage risk
- **No boundary map** — story isolation provides implicit boundaries
- **No visual QA** — headless environment, no browser
- **No documentation agent** — `## What Was Built` records (enriched by review sub-agent data) serve as the primary record
- **Fresh context each iteration** — no accumulated state; Ralph state file bridges iterations

### References

- **PROMPT template:** `scripts/PROMPT_build.md` — single-iteration instruction set
- **CLI pipeline docs:** `.writ/docs/ralph-cli-pipeline.md` — gate mapping, back pressure, state protocol
- **State format:** `.writ/docs/ralph-state-format.md` — JSON schema for `ralph-*.json`
- **Loop script:** `scripts/ralph.sh` — outer loop with stop conditions

---

## Command Workflow Integrity

When a Writ command uses a planning phase for discovery, the planning conversation serves the command — it does not become the command.

**Rule:** After discovery completes, the command resumes its documented phases and produces its documented artifacts (spec files, stories, ADRs, etc.). After artifact creation, the command terminates with a next-step suggestion. Do not spawn implementation subagents or offer to begin building after a planning command completes.

**Common failure:** After writing spec artifacts, the session offers to run `/implement-spec` or spawn coding subagents. Planning commands produce files and stop — implementation is a separate command the user invokes deliberately.

**Reference:** System instructions → Prime Directive → Hard Constraints → "Never let Plan Mode absorb a command's workflow."

---

## Gotchas

1. **Worktree merges can conflict**: If two parallel coders modify the same file, the merge will conflict. Design stories with minimal overlap. The dependency graph in `/implement-story` helps prevent this.

2. **Agent teams are experimental**: Enable with `CLAUDE_CODE_EXPERIMENTAL_AGENT_TEAMS=1`. Known limitations around session resumption and shutdown. For production use, prefer sequential subagent delegation.

3. **Memory bootstrapping**: Agent memory starts empty. First few runs will be less effective. Ask agents explicitly to "update your memory with patterns you discover."

4. **Haiku for story-gen**: Fast and cheap but may produce less nuanced stories. If story quality matters, change `model: haiku` to `model: sonnet` in `writ-story-gen.md`.

5. **Subagents can't spawn subagents**: The orchestrator (main session or top-level CLI invocation) must handle all delegation. Agents spawned as subagents can't delegate further — use agent teams if you need inter-agent communication. Note: Ralph's CLI agent IS the top-level session, so it can spawn sub-agents (e.g., review sub-agent in Phase 2.5).

6. **Plan mode is truly read-only**: `permissionMode: plan` blocks all writes at the tool level. The architect and reviewer genuinely cannot modify files, even if prompted to.
