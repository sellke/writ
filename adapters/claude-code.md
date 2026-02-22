# Claude Code Platform Adapter

Maps Cursor-specific tool calls to Claude Code CLI equivalents for running Writ commands via `claude` (Anthropic's CLI agent).

---

## Installation

### Step 1: Create Directory Structure

```bash
# From your project root
mkdir -p .claude/commands .claude/agents .writ/state
```

### Step 2: Install CLAUDE.md (Project Instructions)

Create `CLAUDE.md` in your project root — Claude Code auto-loads this file every session:

```bash
cat > CLAUDE.md << 'EOF'
# Writ

You are **Writ** — a methodical AI development partner. You organize all work in `.writ/` folders.

## Commands

Run Writ commands by reading the command file and following its workflow:

| Command | File | Purpose |
|---------|------|---------|
| `/create-spec` | `.claude/commands/create-spec.md` | Contract-first feature specification |
| `/implement-story` | `.claude/commands/implement-story.md` | Full SDLC via multi-phase workflow |
| `/execute-task` | `.claude/commands/execute-task.md` | TDD implementation (100% test pass) |
| `/plan-product` | `.claude/commands/plan-product.md` | Product planning |
| `/create-adr` | `.claude/commands/create-adr.md` | Architecture Decision Records |
| `/create-issue` | `.claude/commands/create-issue.md` | Quick issue capture |
| `/research` | `.claude/commands/research.md` | Systematic research |
| `/edit-spec` | `.claude/commands/edit-spec.md` | Modify existing specs |
| `/verify-spec` | `.claude/commands/verify-spec.md` | Verify spec sync |
| `/status` | `.claude/commands/status.md` | Project status report |
| `/swab` | `.claude/commands/swab.md` | One small cleanup |
| `/refresh-docs` | `.claude/commands/refresh-docs.md` | Sync docs with code |
| `/initialize` | `.claude/commands/initialize.md` | Project setup |
| `/explain-code` | `.claude/commands/explain-code.md` | Code explanation |
| `/new-command` | `.claude/commands/new-command.md` | Create new commands |
| `/test-database` | `.claude/commands/test-database.md` | Database diagnostics |
| `/prisma-migration` | `.claude/commands/prisma-migration.md` | Prisma migrations |

When a user types a command, read the corresponding file and follow it precisely.

## Agent Specs

Sub-agent prompts and output formats are defined in `.claude/agents/`:
- `coding-agent.md` — TDD implementation
- `review-agent.md` — Code review quality gate
- `testing-agent.md` — Test execution & verification
- `documentation-agent.md` — VitePress documentation
- `user-story-generator.md` — Parallel story creation

## Tool Translations

Writ commands reference Cursor tools. In Claude Code:
- `Task()` → Execute inline or spawn via `Bash("claude -p '...'")` for parallel work
- `AskQuestion()` → Present numbered text options, ask user to reply
- `codebase_search` → `Bash("rg 'pattern' src/")`
- `file_search` → `Bash("fd 'pattern'")`
- `todo_write` → `Write .writ/state/tracking.json`
- `readonly: true` → Use only `Read` and `Bash` (no `Write`/`Edit`)

See `.claude/agents/` files for full prompt templates.

## Principles
- **Contract-first**: Establish agreement before creating files
- **TDD**: Tests first, then implementation
- **Challenge assumptions**: Push back on bad ideas with evidence
- **Commit incrementally**: Small commits, not big bangs
EOF
```

### Step 3: Copy Commands and Agents

```bash
# Copy all commands
cp path/to/writ/commands/*.md .claude/commands/

# Copy agent specifications
cp path/to/writ/agents/*.md .claude/agents/
```

### Step 4: Add Project Context (Optional but Recommended)

```bash
mkdir -p .writ/docs

# Tech stack
cat > .writ/docs/tech-stack.md << 'EOF'
# Tech Stack
- Runtime: Node.js 22 / Bun
- Framework: [your framework]
- Database: [your DB]
- Testing: [your test runner]
EOF

# Code style
cat > .writ/docs/code-style.md << 'EOF'
# Code Style
- [Your conventions here]
EOF
```

### Step 5: .gitignore

```gitignore
# Writ ephemeral state
.writ/state/

# Keep everything else (specs, ADRs, research are valuable)
```

### Final Structure

```
your-project/
├── CLAUDE.md                      # Auto-loaded by Claude Code every session
├── .claude/
│   ├── commands/                  # Command workflows
│   │   ├── create-spec.md
│   │   ├── implement-story.md
│   │   ├── execute-task.md
│   │   └── ... (14 more)
│   └── agents/                    # Sub-agent prompt templates
│       ├── coding-agent.md
│       ├── review-agent.md
│       ├── testing-agent.md
│       ├── documentation-agent.md
│       └── user-story-generator.md
├── .writ/                 # Runtime artifacts
│   ├── specs/
│   ├── product/
│   ├── research/
│   ├── decision-records/
│   ├── docs/
│   │   ├── tech-stack.md
│   │   └── code-style.md
│   ├── issues/
│   ├── explanations/
│   └── state/
└── ...
```

---

## Usage

### Interactive Session

```bash
cd your-project
claude

# Then type commands in the chat:
> /create-spec "user authentication"
> /implement-story
> /status
```

### One-Shot (Non-Interactive)

```bash
claude -p "/status" 
claude -p "/create-issue 'Login page crashes on empty email'"
```

### With Permission Bypass (for CI/automation)

```bash
claude -p "/execute-task story-1" --permission-mode acceptEdits
claude -p "/implement-story" --permission-mode bypassPermissions  # ⚠️ sandbox only
```

---

## Multi-Agent Patterns

### Using `--agents` Flag

Claude Code supports custom agent definitions via JSON:

```bash
claude --agents '{
  "writ": {
    "description": "Methodical development partner",
    "prompt": "You are Writ. Read .claude/commands/ for available workflows."
  },
  "reviewer": {
    "description": "Code review specialist", 
    "prompt": "You are the Review Agent. Read .claude/agents/review-agent.md for your mission. Do NOT modify any files."
  }
}'
```

Then switch agents mid-session with `/agent writ` or `/agent reviewer`.

### Parallel Sub-Agents via Background Processes

For `implement-story` and `create-spec` parallel work:

```bash
# Orchestrator spawns parallel story generators
claude -p "Create story-1-auth.md at .writ/specs/2026-02-22-feature/user-stories/. [full prompt]" \
  --allowedTools Read,Write,Bash \
  --permission-mode acceptEdits \
  --no-session-persistence &

claude -p "Create story-2-api.md at .writ/specs/2026-02-22-feature/user-stories/. [full prompt]" \
  --allowedTools Read,Write,Bash \
  --permission-mode acceptEdits \
  --no-session-persistence &

# Wait for all to complete
wait
```

### Review Loop Pattern

```bash
# Phase 1: Coding agent
claude -p "Read .writ/state/story-context.json. Implement the story. Write summary to .writ/state/coding-output.md" \
  --allowedTools Read,Write,Edit,Bash \
  --permission-mode acceptEdits

# Phase 2: Review agent (read-only)
claude -p "Read .writ/state/coding-output.md. Review against acceptance criteria. Write REVIEW_RESULT to .writ/state/review-result.md" \
  --allowedTools Read,Bash \
  --permission-mode acceptEdits

# Phase 3: Check result, loop if needed
RESULT=$(grep "REVIEW_RESULT" .writ/state/review-result.md)
if [[ "$RESULT" == *"FAIL"* ]]; then
  claude -p "Read .writ/state/review-result.md for feedback. Fix all issues. Update .writ/state/coding-output.md" \
    --allowedTools Read,Write,Edit,Bash \
    --permission-mode acceptEdits
fi
```

---

## Quick Reference

| Cursor Tool | Claude Code Equivalent | Notes |
|---|---|---|
| `Task({ prompt })` | `claude -p "prompt"` via `exec` | One-shot, or background for parallel |
| `Task({ resume: id })` | Kill + respawn with accumulated context | No native resume |
| `AskQuestion({ questions })` | Formatted text with numbered options | No interactive UI |
| `codebase_search` | `Bash("rg 'pattern' src/")` | ripgrep |
| `file_search` | `Bash("fd 'pattern'")` | fd or find |
| `todo_write` | `Write(".writ/state/tracking.json", ...)` | File-based |
| `read_file` | `Read(path)` | Direct equivalent |
| `run_terminal_cmd` | `Bash(command)` | Direct equivalent |
| `list_dir` | `Bash("ls -la path/")` | Direct equivalent |
| `readonly: true` | `--allowedTools Read,Bash` | Restricts tool access |

---

## Running Modes

### Standalone Claude Code (user runs `claude` directly)

When a developer runs `claude` in their terminal and invokes Writ commands, the tools map naturally — Claude Code already has `Read`, `Write`, `Edit`, `Bash`.

The key difference is **sub-agents**. Claude Code doesn't have `Task()`, so you need:

### Pattern A: Sequential (simple)
Run each agent phase inline — orchestrator does everything in one session.

### Pattern B: Parallel via background processes
Spawn multiple `claude -p` processes for parallel work.

### Pattern C: OpenClaw-hosted Claude Code
Use `exec pty:true command:"claude -p '...'"` from an OpenClaw agent, combining both platforms.

---

## Detailed Mappings

### 1. Spawning Sub-Agents (`Task` → `claude -p` via Bash)

**Cursor:**
```
Task({
  subagent_type: "generalPurpose",
  model: "fast",
  description: "Create user story 1",
  prompt: "You are a User Story Generator agent..."
})
```

**Claude Code (inline — no sub-agent):**
Just execute the work directly. Claude Code is already an agent with file access.

**Claude Code (parallel via background):**
```bash
# From an OpenClaw orchestrator or shell script:

# Story 1 (background)
exec({
  command: "claude -p 'You are a User Story Generator. Create story-1-auth.md in .writ/specs/2026-02-22-feature/user-stories/ with the following requirements: ...' --allowedTools Read,Write,Bash",
  workdir: "/path/to/project",
  pty: true,
  background: true
})

# Story 2 (background, parallel)
exec({
  command: "claude -p 'You are a User Story Generator. Create story-2-api.md ...' --allowedTools Read,Write,Bash",
  workdir: "/path/to/project",
  pty: true,
  background: true
})
```

**Monitor parallel agents:**
```
process({ action: "list" })                    // See all running
process({ action: "poll", sessionId: "..." })  // Check if done
process({ action: "log", sessionId: "..." })   // Read output
```

### 2. Resuming Agents (no native resume — use context passing)

**Cursor:**
```
Task({
  resume: "{coding_agent_id}",
  prompt: "Fix these review issues..."
})
```

**Claude Code:**
There's no session resume. Instead, capture the previous agent's output and pass it as context to a new invocation:

```bash
# Capture coding agent output to file
process({ action: "log", sessionId: "coding-agent-session" })
# Save relevant output to a context file

# Spawn new agent with accumulated context
exec({
  command: "claude -p 'PREVIOUS IMPLEMENTATION:\n[paste or reference output]\n\nREVIEW FEEDBACK:\n[issues]\n\nFix the issues above and re-run tests.' --allowedTools Read,Write,Edit,Bash",
  workdir: "/path/to/project",
  pty: true
})
```

**File-based context passing (recommended for large contexts):**
```bash
# After coding agent completes, it writes summary:
# .writ/state/coding-output.md

# Review agent reads it:
exec({
  command: "claude -p 'Read .writ/state/coding-output.md for implementation context. Review the changes and output REVIEW_RESULT: PASS or FAIL with details.' --allowedTools Read,Bash",
  ...
})

# If FAIL, next coding run reads both:
exec({
  command: "claude -p 'Read .writ/state/coding-output.md and .writ/state/review-feedback.md. Fix all issues marked Critical or Major.' --allowedTools Read,Write,Edit,Bash",
  ...
})
```

### 3. Structured Questions (`AskQuestion` → formatted text)

**Cursor:**
```
AskQuestion({
  title: "Feature Clarification",
  questions: [{ id: "user_type", prompt: "Who is the primary user?", options: [...] }]
})
```

**Claude Code:**
No interactive UI available. Use formatted text:

```
**Feature Clarification - Round 1**

Who is the primary user of this feature?
  1. End users/customers
  2. Administrators/internal staff
  3. Developers/API consumers
  4. Multiple user types

Reply with the number of your choice.
```

For multi-question rounds:
```
**Round 1 — Core Understanding**

1. **Primary user?**
   a) End users  b) Admins  c) Developers  d) Multiple

2. **Integration approach?**
   a) Standalone  b) Extends existing  c) Replaces existing  d) Deep integration

3. **Priority?**
   a) MVP first  b) Complete feature  c) Iterative

Reply like: "1a, 2b, 3c"
```

### 4. Code Search (`codebase_search` → `Bash` with ripgrep)

**Cursor:**
```
codebase_search("authentication pattern")
```

**Claude Code:**
```bash
Bash("rg -n 'authenticate|authorize' src/ --type ts")
Bash("rg -l 'auth' src/ --type ts --type tsx")
Bash("rg -C 3 'export.*Auth' src/")
```

### 5. File Search (`file_search` → `Bash` with fd)

**Cursor:**
```
file_search("AuthService")
```

**Claude Code:**
```bash
Bash("fd AuthService")
Bash("fd -e ts -e tsx auth")
Bash("find . -name '*auth*' -not -path '*/node_modules/*'")
```

### 6. Progress Tracking (`todo_write` → file-based JSON)

**Cursor:**
```
todo_write({ todos: [{ id: "phase-1", content: "Gather context", status: "completed" }] })
```

**Claude Code:**
```
Write(".writ/state/tracking.json", JSON.stringify({
  phases: {
    "context-gathering": { status: "completed", completedAt: "2026-02-22T17:40:00Z" },
    "coding-phase": { status: "in_progress" },
    "review-phase": { status: "pending" }
  }
}, null, 2))
```

### 7. Read-Only Agents (`readonly: true` → `--allowedTools`)

**Cursor:**
```
Task({ readonly: true, prompt: "Review the implementation..." })
```

**Claude Code:**
```bash
claude -p "Review the implementation..." --allowedTools Read,Bash
```

This restricts the agent to only reading files and running shell commands (for grep/find). No `Write`, `Edit`, or destructive operations.

**Tool restriction patterns:**
| Mode | `--allowedTools` | Use Case |
|------|---|---|
| Read-only | `Read,Bash` | Review agent, analysis |
| Full access | `Read,Write,Edit,Bash` | Coding agent, docs agent |
| Minimal | `Read` | Pure analysis, no shell |

---

## Workflow Patterns

### implement-story: Sequential (Single Session)

When running in a single `claude` session (no parallelism), the orchestrator just does each phase inline:

```
1. Read story file and spec
2. Search codebase for patterns (rg, fd)
3. Write tests (TDD)
4. Implement code
5. Self-review against acceptance criteria
6. Run tests (Bash)
7. Update documentation
8. Update story status
```

This is simpler but loses the multi-agent quality gates.

### implement-story: Multi-Agent (Parallel Processes)

```bash
# Phase 1: Context (orchestrator gathers, writes to state file)
Write(".writ/state/story-context.json", { story, spec, patterns })

# Phase 2: Coding agent
exec({
  pty: true,
  workdir: "/project",
  command: "claude -p 'Read .writ/state/story-context.json. Implement the story following TDD. Write your output summary to .writ/state/coding-output.md when done.' --allowedTools Read,Write,Edit,Bash"
})

# Phase 3: Review agent (read-only)
exec({
  pty: true,
  workdir: "/project",
  command: "claude -p 'Read .writ/state/coding-output.md. Review against the story acceptance criteria in .writ/state/story-context.json. Write REVIEW_RESULT to .writ/state/review-result.md.' --allowedTools Read,Bash"
})

# Check review result
Read(".writ/state/review-result.md")
# Parse PASS/FAIL, loop if needed

# Phase 4: Testing agent
exec({
  pty: true,
  workdir: "/project",
  command: "claude -p 'Run all tests. Read .writ/state/coding-output.md for files to test. Fix failures if possible. Write TEST_RESULT to .writ/state/test-result.md.' --allowedTools Read,Write,Edit,Bash"
})

# Phase 5: Documentation agent
exec({
  pty: true,
  workdir: "/project",
  command: "claude -p 'Read .writ/state/coding-output.md. Create/update VitePress docs in docs/. Write summary to .writ/state/docs-result.md.' --allowedTools Read,Write,Edit,Bash"
})
```

### create-spec: Parallel Story Generation

```bash
# After contract is locked, spawn story generators in parallel:

# All background with PTY
exec({ pty: true, background: true, workdir: "/project",
  command: "claude -p 'Create story-1-auth.md at [path]. [Full template + context]' --allowedTools Read,Write,Bash"
})
exec({ pty: true, background: true, workdir: "/project",
  command: "claude -p 'Create story-2-api.md at [path]. [Full template + context]' --allowedTools Read,Write,Bash"
})
exec({ pty: true, background: true, workdir: "/project",
  command: "claude -p 'Create story-3-ui.md at [path]. [Full template + context]' --allowedTools Read,Write,Bash"
})

# Monitor completion
process({ action: "list" })
# Wait for all to finish, then create README.md
```

---

## Claude Code CLI Reference

### Key Flags

| Flag | Purpose | Example |
|------|---------|---------|
| `-p "prompt"` | Non-interactive one-shot | `claude -p "Explain this code"` |
| `--allowedTools` | Restrict available tools | `--allowedTools Read,Bash` |
| `--model` | Model override | `--model claude-sonnet-4-20250514` |
| `--max-turns` | Limit agent iterations | `--max-turns 20` |
| `--output-format json` | Structured output | For parsing results |
| `--no-input` | No stdin prompts | Prevents hanging in background |

### Common Invocation

```bash
claude -p "Your detailed prompt here" \
  --allowedTools Read,Write,Edit,Bash \
  --max-turns 30 \
  --no-input
```

### Output Capture

```bash
# Capture to file for next agent
claude -p "..." --output-format text > .writ/state/output.md

# Or have the agent write its own output file (more reliable)
claude -p "... When done, write your summary to .writ/state/result.md"
```

---

## Gotchas

1. **No session resume**: Claude Code doesn't support resuming sessions. Use file-based context passing between agent phases. Write outputs to `.writ/state/`, read them in the next phase.

2. **No interactive UI**: No `AskQuestion` equivalent. Use numbered text options. This means contract-first clarification in `create-spec` will be more conversational and less structured.

3. **`-p` flag for non-interactive**: Always use `-p` when running as a sub-process. Without it, `claude` expects interactive terminal input and may hang.

4. **`--no-input` for background**: Add this flag when running in background to prevent the process from waiting on stdin.

5. **Working directory matters**: Each `claude -p` invocation starts fresh. Set `workdir` to the project root so the agent has proper context.

6. **Tool restrictions are advisory**: `--allowedTools` restricts what tools Claude Code will use, but the agent could still be instructed to write via `Bash("echo > file")`. For true read-only, combine `--allowedTools Read,Bash` with explicit prompt instructions.

7. **Cost control**: Each `claude -p` invocation is a separate API session. For 4 parallel story generators, that's 4× the context loading cost. Consider whether sequential is acceptable for smaller specs.

8. **Max turns**: Set `--max-turns` to prevent runaway agents. 20-30 turns is usually enough for a single story implementation. Review agents need fewer (5-10).
