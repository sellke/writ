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

### Recommendation Interaction Mapping

Assign each bounded option a stable identity independent of its displayed
number. Append `(Recommended)` only to the display label identified by the
shared policy; numbering, affirmative wording, and omission of a reply are not
selection evidence. If the policy finds options explicitly equivalent, label
none and state the equivalence before requesting a reply.

Preserve stable option identity across display, selection, rationale, and resume.
Adapters map interaction mechanics only; they do not choose recommendation policy.
Equivalent observable semantics are required: recommendation label or disclosed equivalence, classified pause, concise rationale, and same-session continuation after an answer.

In `--recommend` mode, map the policy's selected stable identity to the numbered
option, or render its classified bounded pause with missing evidence and a safe
next action. Show the concise decision, evidence, material alternatives, risk,
reversibility, selection source, and result/artifact fields; do not expose
private chain-of-thought or transcript content. After a required reply, continue
the active top-level session automatically with recommendation mode retained and
do not ask the completed question again. Persistent or cross-session resumption
belongs to the neutral orchestration contract, not this interaction adapter.
Sandbox, authentication, permission, and unavailable-capability failures remain
hard platform blockers.

### Fresh Isolated Execution Lanes

For `/implement-phase`, map the platform-neutral lane contract onto Claude Code's
native subagents and git worktrees:

- **Isolated worktree.** The orchestrator runs `scripts/phase-state.py create-lane`
  to create the lane branch `writ/phase/{phase-id}/{spec-id}` and an
  isolated worktree from the phase-branch head. The subagent works only inside
  that worktree; the primary checkout is untouched during lane work.
- **Fresh context.** Dispatch the spec to a native subagent seeded only with
  artifact paths (spec path, phase-state path, lane branch/worktree, mode) —
  **no prior conversational transcript** is forwarded. Claude Code subagents
  already start with clean context; do not replay the parent transcript.
- **Run identifier.** Record the subagent invocation ID as `agentRunId`.
- **Structured result.** The subagent returns a single `phase-spec-result-v1`
  object; the parent validates it with `scripts/phase-state.py validate-result`
  and merges only a verified success into the phase branch.

### Quarantine and Resume

Terminal failure disposition and `--resume` reconciliation are plain git plus the
neutral reducer:

- On terminal failure the orchestrator calls `scripts/phase-state.py quarantine`,
  which removes the lane worktree and renames the lane branch to
  `writ/quarantine/{spec-id}` (deterministic suffix on collision). The phase branch
  stays clean; dependents become `skipped_blocked`.
- Claude Code dispatches a fresh subagent for the single permitted transient retry
  in the same lane.
- `--resume` runs `scripts/phase-state.py reconcile` (read-only) first; on a
  state/git mismatch it reports the discrepancy and recovery command without
  mutating git.

### Recommended Delivery Context and Resume

The parent Claude Code session carries `delivery_context` through command and
agent calls and normalizes each nested response to
`recommend-command-result-v1`. Preserve execution ID, canonical state/spec
paths, recommend mode, non-secret propagation token, parent command, return
schema, and package manifest digest. Worktree subagents do not create a second
delivery execution or independently terminate recommended delivery; the
implement-spec parent may wrap their ordinary structured report.

Before yielding for required input, preserve stable question and option IDs,
recommend mode, and the exact resume transition. Durable resume selects an
explicit execution ID or one unambiguous spec/branch execution, then performs
repository-only reconciliation in the parent before edits or subagent launch.

State creation is exclusive. Replacement re-reads revision and unknown fields,
validates the whole next document, writes and flushes a validated sibling
temporary file where supported, and atomically renames it. If the active Claude
Code sandbox cannot perform an equivalent crash-safe replacement, stop with a
classified blocker rather than falling back to truncate-in-place.

Claude Code worktree-isolated subagents must return absolute worktree path, full
ref/HEAD, story/delegated execution IDs, and ownership token in
`recommend-worktree-launch-v1` before Gate 1. The parent verifies
`git worktree list --porcelain`, persists the keyed record through
`scripts/recommend-state.py reserve-worktree`, and returns
`recommend-worktree-reservation-ack-v1`; only then may the subagent edit.
Independent DAG stories may run concurrently when every reservation is unique.
If isolation or stable identity is unavailable, use one-at-a-time serial
in-place execution with the repository root/ref/HEAD handshake, or block before
delegation. A subagent name is not ownership evidence.

Story 3 repository-only reconciliation remains provider-free. Story 4 uses the
configured provider integration or authenticated `gh`/`gh api`:

- `findPullRequest`/`getPullRequest`: query exact repository, base, and head
  branch and normalize one open PR with provider ID, number, URL, and full SHA.
- `createPullRequest`: only after the persisted Pending operation and absent
  lookup. Derive the key from repository/base/head, persist `authorized`, call
  `mark-pr-create-attempt` to persist `attempted`, perform at most one `gh pr create`, then observe as
  `created` or `reconciled`. Repeated absence cannot reauthorize.
- `listRequiredChecks`: combine branch-protection required contexts/check suites
  from `gh api` with separately classified configured additive names. Normalize
  provider/repository/query-time/head, stable provider IDs/names/set digest or
  explicit provider zero, `authenticated: true`, and the concrete
  `listRequiredChecks` query-operation ID/start/completion. Never infer
  authentication from command success; re-query the complete set before advancing.
  Unavailable, needs-auth, and authorization-denied remain distinct.
- `findPreview`: read existing deployment/status/check metadata or a configured
  integration. Existing Vercel metadata is eligible only when `Preview Project`
  identifies its existing project and the deployment binds to the full PR head
  SHA. Normalize it as `previewProjectId`; detected IDs remain execution-only
  and are never auto-saved. Return configured
  provider/source/repository/project identity plus observable integration ID,
  provenance kind/time, and full SHA; URL-pattern-only evidence is invalid.
  Enforce `deployment-status → provider-deployment|provider-status`,
  `check-output → provider-check`, and
  `project-convention → project-convention`.

Immediately before approval, return one fresh same-operation envelope binding
the capability/config snapshot digest, current PR/head, complete reconciled
check-set digest/IDs/statuses, preview provenance/status, UAT digest, and query
time. One attempt ID binds UTC RFC3339 observations after presentation/current
evidence, within configured-or-five-minute freshness and 30-second future skew.
Persist the stable interaction ID and its bound recommendation entry.

After PR observation, finalize the exact Pending entry with canonical provider
ID/number/URL, reconcile it, and invoke `finalize-pr-audit` before checks. Never
advance a later staging transition with any Pending mutation audit.

Normalize evidence into local files and invoke only the explicit reducer
operations. Persist before waiting; after waits and before approval re-read the
PR head, full required set, and preview. Render one explicit approve/reject
question, preserve or generate a stable local event ID only for an explicit
reply, and persist approval before returning `production_approved`.

No browser automation, preview provisioning, Vercel access bypass,
`deploy_to_vercel`, merge call, or release operation is permitted in Story 4.
Authentication/authorization denial is reported once and stops. A platform that
cannot wait unattended preserves `waiting_ci` or `discovering_preview` and
instructs explicit resume.

---

## Workflow Patterns

### implement-story: Single Story

```
1. Orchestrator gathers context (reads story, spec, codebase)
   → Scans .writ/knowledge/ and builds optional knowledge_context
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

### Knowledge Loading

`/implement-story` performs the knowledge-loading hook before delegation. Claude Code does not need a separate hook or agent memory feature for this path: the top-level orchestrator greps `.writ/knowledge/`, assembles the optional `knowledge_context` block, and includes it in the prompts for `writ-architect`, `writ-coder`, and `writ-reviewer`.

### Preamble Convention

Manual and scripted installs copy `commands/_preamble.md` into `.claude/commands/` with the rest of the command files. Claude Code loads the invoked command markdown; the command's final `## References` section points the orchestrator at `_preamble.md` and `system-instructions.md`, so the convention stays markdown-driven rather than hook-driven.

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

## Skills

Skills are the third Writ primitive (peer to commands and agents) — capability files that describe how to do a specific thing well. See [ADR-009](../.writ/decision-records/adr-009-command-agent-skill-boundary.md) for the verb/noun/tool framing and [`.writ/docs/skills.md`](../.writ/docs/skills.md) for the user-facing explainer.

Claude Code uses a **platform-namespaced** install path (below). Codex CLI installs Writ skills at `.agents/skills/` per the AgentSkills standard — see [ADR-009 § Amendments](../.writ/decision-records/adr-009-command-agent-skill-boundary.md#amendments).

### Install Path

```
.claude/skills/<name>/SKILL.md
```

`install.sh --platform claude` and `update.sh --platform claude` fan skills out alongside commands and agents using the same three-way overlay logic — local modifications to `.claude/skills/<name>/SKILL.md` are preserved across updates. Sidecar files inside a skill folder (anything that isn't `SKILL.md`) are install-once: they're copied on first install and never overwritten on subsequent updates.

### Loading Mechanism

Claude Code's skill discovery scans `.claude/skills/` and surfaces installed skills to the model with their frontmatter `description:` text. By default Claude may auto-invoke skills based on description match.

**Writ-authored skills opt out of ambient invocation** by setting `disable-model-invocation: true` in their frontmatter. This keeps every skill load deterministic and traceable — Writ commands and agents name skills explicitly when they need them. Community skills installed by other means (e.g. `clawhub`, `agentskills.io` catalogs) are out of Writ's control and follow whatever invocation behavior their installer configured.

### Invocation

Commands and agents that need a skill load it explicitly:

```
Read skills/<name>/SKILL.md
```

In Claude Code's tool model, this maps directly to the native `Read` tool. The orchestrator (or command body) issues the `Read` call when the relevant phase begins; the skill's content lands in the agent's context for that phase.

For commands and agents that declare `required_skills:` in their frontmatter (the convention defined in this spec — see Story 5 / `system-instructions.md`), the harness issues `Read skills/<name>/SKILL.md` calls before the consumer's first phase begins. `required_skills:` is reserve-only in the foundation spec; pilot skills will adopt it as they ship.

### Authoring & Reference

| Need | Tool |
|---|---|
| Scaffold a new skill | `/new-skill <name>` (boundary lint enforced at authoring time) |
| Lint an existing skill against the role convention | `/refresh-command` → boundary check |
| Cross-platform format spec | [AgentSkills standard](https://agentskills.io) |
| Boundary rationale | [ADR-009](../.writ/decision-records/adr-009-command-agent-skill-boundary.md) |
| User-facing explainer | [`.writ/docs/skills.md`](../.writ/docs/skills.md) |

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

## Autonomous Multi-Spec Execution (retired CLI loop)

The former unattended CLI loop for multi-spec execution is **retired and archived**
(see `archive/`). Supervised multi-spec execution now runs through `/implement-phase`,
which sequences specs by cross-spec dependency, gives each spec a fresh isolated
execution lane (branch + worktree), quarantines terminal failures while independent
specs continue, and reconciles state read-only on resume. Map it to Claude Code as
the orchestrator session driving one `/implement-spec` worker per lane.

Bounded single-spec autonomy is a separate, explicitly supported path:
`/implement-spec --recommend <one-spec>` (session-started, one locked spec, finite,
one SHA-bound production approval). Multi-spec `/implement-phase --recommend` remains
excluded.

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

5. **Subagents can't spawn subagents**: The orchestrator (main session or top-level CLI invocation) must handle all delegation. Agents spawned as subagents can't delegate further — use agent teams if you need inter-agent communication. Note: a top-level CLI session IS the orchestrator, so it can spawn sub-agents (e.g., a review sub-agent).

6. **Plan mode is truly read-only**: `permissionMode: plan` blocks all writes at the tool level. The architect and reviewer genuinely cannot modify files, even if prompted to.
