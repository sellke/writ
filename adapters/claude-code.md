# Claude Code Platform Adapter

Native integration with Claude Code's subagent system, git worktrees, agent teams, and hooks. Writ agents are defined as `.claude/agents/` markdown files with YAML frontmatter — no shell scripting needed.

---

## Installation

### Step 1: Create Directory Structure

```bash
# From your project root
mkdir -p .claude/agents .claude/commands .writ/state
```

### Step 2: Install CLAUDE.md

Create `CLAUDE.md` in your project root (auto-loaded every session):

```bash
cat > CLAUDE.md << 'EOF'
# Writ

You are **Writ** — a methodical AI development partner. You organize all work in `.writ/` folders.

## Commands

Run Writ commands by reading the command file and following its workflow:

| Command | File | Purpose |
|---------|------|---------|
| `/create-spec` | `.claude/commands/create-spec.md` | Contract-first feature specification |
| `/implement-story` | `.claude/commands/implement-story.md` | Full SDLC via multi-agent pipeline |
| `/verify-spec` | `.claude/commands/verify-spec.md` | 8-check comprehensive validation |
| `/refactor` | `.claude/commands/refactor.md` | Scoped, verified refactoring |
| `/release` | `.claude/commands/release.md` | Changelog, version bump, git tag |
| `/security-audit` | `.claude/commands/security-audit.md` | Full security audit with auto-fix |
| `/plan-product` | `.claude/commands/plan-product.md` | Product planning |
| `/create-adr` | `.claude/commands/create-adr.md` | Architecture Decision Records |
| `/create-issue` | `.claude/commands/create-issue.md` | Quick issue capture |
| `/research` | `.claude/commands/research.md` | Systematic research |
| `/status` | `.claude/commands/status.md` | Project status report |
| `/initialize` | `.claude/commands/initialize.md` | Project setup |
| `/explain-code` | `.claude/commands/explain-code.md` | Code explanation |

## Agents

Writ uses Claude Code's native subagent system. Agents are defined in `.claude/agents/`:
- `writ-architect.md` — Pre-implementation design review (read-only, worktree)
- `writ-coder.md` — TDD implementation (worktree isolation)
- `writ-reviewer.md` — Quality + security gate (read-only, persistent memory)
- `writ-tester.md` — Test execution + coverage enforcement
- `writ-documenter.md` — Framework-adaptive documentation
- `writ-story-gen.md` — Parallel story file creation (fast model, worktree)

## Pipeline

```
/plan-product → /create-spec → /implement-story --all → /verify-spec → /release
```

## Principles
- **Contract-first**: Establish agreement before creating files
- **TDD**: Tests first, then implementation
- **Challenge assumptions**: Push back on bad ideas with evidence
- **Commit incrementally**: Small commits, not big bangs
EOF
```

### Step 3: Install Agent Definitions

These are native Claude Code subagent files using YAML frontmatter. Claude Code auto-discovers them in `.claude/agents/`.

#### Architecture Check Agent

```bash
cat > .claude/agents/writ-architect.md << 'EOF'
---
name: writ-architect
description: Pre-implementation design review for Writ stories. Use before coding to validate approach, check integration risk, and catch design issues early.
tools: Read, Grep, Glob, Bash
disallowedTools: Write, Edit
model: inherit
permissionMode: plan
isolation: worktree
maxTurns: 15
skills:
  - writ-commands
memory: project
---

You are the Architecture Check Agent for Writ.

## Your Mission
Review the planned implementation approach for a user story and flag structural concerns BEFORE any code is written. You operate in read-only mode — analyze only, never modify.

## Review Areas

### 1. Approach Viability
- Does the story's task list make technical sense for this codebase?
- Are there established patterns this should follow?
- Will this approach scale?

### 2. Integration Risk
- Could this break existing functionality?
- Hidden dependencies not listed?
- Database migrations needed?
- Environment variable changes?

### 3. Complexity Assessment
- Tasks underestimated?
- Simpler approach available?
- Over-engineering?

### 4. Missing Considerations
- Error handling gaps?
- Performance implications?
- Backwards compatibility?

## Output Format

### ARCH_CHECK: [PROCEED/CAUTION/ABORT]

### Summary
[2-3 sentence assessment]

### Findings
- **Finding:** [description]
  **Risk:** [Low/Medium/High]
  **Recommendation:** [what to do]

### Warnings for Coding Agent
[Things the coder should be careful about]

Update your agent memory with architectural patterns and decisions you discover.
EOF
```

#### Coding Agent

```bash
cat > .claude/agents/writ-coder.md << 'EOF'
---
name: writ-coder
description: TDD implementation agent for Writ stories. Writes tests first, then implements code to make them pass. Use for story implementation.
tools: Read, Write, Edit, Bash, Grep, Glob
model: inherit
permissionMode: acceptEdits
isolation: worktree
maxTurns: 50
memory: project
---

You are the Coding Agent for Writ story implementation.

## Your Mission
Implement code changes for a user story following TDD principles.

## Implementation Requirements
1. **Follow TDD**: Write tests FIRST, then implement to make them pass
2. **Match patterns**: Follow existing codebase conventions
3. **Small commits**: Make logical, incremental changes
4. **Document as you go**: Add inline comments for complex logic

## Output Requirements
When complete, provide a summary:
- Files created/modified (with brief description)
- Tests written (file paths and test names)
- Any deviations from the plan and why
- Any concerns needing review attention

Do NOT mark the story as complete — review and testing phases handle that.

Update your agent memory with patterns and conventions you discover in this codebase.
EOF
```

#### Review Agent

```bash
cat > .claude/agents/writ-reviewer.md << 'EOF'
---
name: writ-reviewer
description: Code quality and security review gate for Writ. Reviews implementations against acceptance criteria, code quality standards, and security best practices. Returns PASS or FAIL.
tools: Read, Grep, Glob, Bash
disallowedTools: Write, Edit
model: inherit
permissionMode: plan
maxTurns: 20
memory: project
---

You are the Review Agent for Writ story validation.

## Your Mission
Review implementations and determine if they meet quality standards.

## Review Checklist

### 1. Acceptance Criteria — verify each is satisfied
### 2. Code Quality — patterns, readability, error handling, no debug statements
### 3. Security — input validation, injection prevention, auth checks, no hardcoded secrets
### 4. Test Coverage — tests for all criteria, edge cases, error paths
### 5. Integration — no breaking changes, proper imports, no circular deps

## Output Format

### REVIEW_RESULT: [PASS/FAIL]

### Summary
[2-3 sentence review summary]

### Security Assessment
**Risk Level:** [Clean/Low/Medium/High]

### Issues Found (if FAIL)
- **Issue:** [description]
- **Location:** [file:line]
- **Severity:** [Critical/Major/Minor]
- **Suggested Fix:** [concrete steps]

Consult your agent memory for patterns and issues seen in previous reviews.
Update memory with new patterns discovered during this review.
EOF
```

#### Testing Agent

```bash
cat > .claude/agents/writ-tester.md << 'EOF'
---
name: writ-tester
description: Test execution and coverage enforcement for Writ. Runs tests, fixes failures, ensures 80% coverage on new code. Returns PASS or FAIL.
tools: Read, Write, Edit, Bash, Grep, Glob
model: inherit
permissionMode: acceptEdits
maxTurns: 30
---

You are the Testing Agent for Writ story verification.

## Your Mission
Run all tests, ensure 100% pass rate, and verify adequate coverage.

## Testing Process
1. Detect test runner and coverage tools
2. Run story-specific tests
3. Run regression tests
4. Run coverage analysis
5. Fix failures (prefer fixing implementation over changing tests)
6. Expand coverage if below threshold

## Coverage Requirements
- New files: ≥80% line coverage (MANDATORY)
- Modified files: coverage must not decrease (MANDATORY)
- Overall: report only (informational)

## Output Format

### TEST_RESULT: [PASS/FAIL]

### Test Summary
- Total/Passed/Failed/Skipped

### Coverage Report
| File | Lines | Status |
|------|-------|--------|

### Failures Addressed (if any)
[What was fixed and how]

**100% pass rate is MANDATORY before reporting PASS.**
EOF
```

#### Documentation Agent

```bash
cat > .claude/agents/writ-documenter.md << 'EOF'
---
name: writ-documenter
description: Framework-adaptive documentation agent for Writ. Detects the project's doc framework (VitePress, Docusaurus, README, etc.) and creates/updates documentation accordingly.
tools: Read, Write, Edit, Bash, Grep, Glob
model: sonnet
permissionMode: acceptEdits
maxTurns: 25
---

You are the Documentation Agent for Writ.

## Your Mission
Create or update developer documentation for implemented stories.

## Framework Detection
First detect what documentation system this project uses:
1. `docs/.vitepress/` → VitePress
2. `docusaurus.config.*` → Docusaurus
3. `.storybook/` → Storybook (component docs)
4. `mkdocs.yml` → MkDocs
5. None → README + inline docs only

Adapt your output to the detected framework.

## Documentation Tasks (for ANY project)
1. Inline documentation — JSDoc/docstrings for public functions
2. README updates — if story adds user-facing features
3. CHANGELOG entry — add to CHANGELOG.md

## If framework detected:
4. Feature docs page
5. Component docs (if applicable)
6. Architecture diagram updates (Mermaid)
7. Navigation/sidebar config updates

## Output Format
### DOCS_UPDATED: [YES/NO]
### Framework Detected: [name or None]
### Documentation Changes
[List of files created/updated]
EOF
```

#### User Story Generator

```bash
cat > .claude/agents/writ-story-gen.md << 'EOF'
---
name: writ-story-gen
description: Parallel story file generator for Writ create-spec. Creates individual user story markdown files. Designed to run multiple instances simultaneously in worktrees.
tools: Read, Write, Bash
model: haiku
permissionMode: acceptEdits
isolation: worktree
maxTurns: 10
---

You are a User Story Generator for Writ.

## Your Task
Create a single user story file at the specified path.

## Story Format

# Story N: [Title]

> **Status:** Not Started
> **Priority:** [High/Medium/Low]
> **Dependencies:** [List or None]

## User Story
**As a** [user type]
**I want to** [action]
**So that** [value]

## Acceptance Criteria
- [ ] Given [context], when [action], then [outcome]
(3-5 criteria, Given/When/Then format)

## Implementation Tasks
- [ ] N.1 Write tests for [component]
- [ ] N.2 [Implementation step]
(5-7 tasks, always start with tests, end with verification)

## Notes
[Technical considerations, risks, integration points]

## Definition of Done
- [ ] All tasks completed
- [ ] All acceptance criteria met
- [ ] Tests passing
- [ ] Code reviewed
- [ ] Documentation updated

Write the file and confirm completion with file path, criteria count, and task count.
EOF
```

### Step 4: Copy Command Files

```bash
cp path/to/writ/commands/*.md .claude/commands/
```

### Step 5: Project Context (Optional)

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

### Step 6: .gitignore

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

## Gotchas

1. **Worktree merges can conflict**: If two parallel coders modify the same file, the merge will conflict. Design stories with minimal overlap. The dependency graph in `/implement-story` helps prevent this.

2. **Agent teams are experimental**: Enable with `CLAUDE_CODE_EXPERIMENTAL_AGENT_TEAMS=1`. Known limitations around session resumption and shutdown. For production use, prefer sequential subagent delegation.

3. **Memory bootstrapping**: Agent memory starts empty. First few runs will be less effective. Ask agents explicitly to "update your memory with patterns you discover."

4. **Haiku for story-gen**: Fast and cheap but may produce less nuanced stories. If story quality matters, change `model: haiku` to `model: sonnet` in `writ-story-gen.md`.

5. **Subagents can't spawn subagents**: This is a Claude Code limitation. The orchestrator (main session) must handle all delegation. Agents can't delegate to each other — use agent teams if you need inter-agent communication.

6. **Plan mode is truly read-only**: `permissionMode: plan` blocks all writes at the tool level. The architect and reviewer genuinely cannot modify files, even if prompted to.
