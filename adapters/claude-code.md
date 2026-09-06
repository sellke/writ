# Claude Code Platform Adapter

Native integration with Claude Code's subagent system, git worktrees, agent teams, and hooks. Writ agents are `.claude/agents/` markdown files with YAML frontmatter; no shell scripting is needed.

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

The updater uses a manifest (`.claude/.writ-manifest`) for three-way overlay merges. Files you have customized are never overwritten.

### Manual Installation

If you prefer to install manually, or need to customize the setup:

#### Step 1: Copy files

```bash
mkdir -p .claude/agents .claude/commands .writ/state
cp path/to/writ/commands/*.md .claude/commands/
cp path/to/writ/claude-code/agents/*.md .claude/agents/
cp path/to/writ/claude-code/CLAUDE.md ./CLAUDE.md
```

Agent source files live in `claude-code/agents/` in the Writ repo. They carry YAML frontmatter (`name`, `tools`, `model`, `permissionMode`, `isolation`, `maxTurns`, `memory`).

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
│   │   ├── writ-documenter.md        # inherit, acceptEdits
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

When a subagent has `isolation: worktree`, Claude Code:
1. Creates a temporary git worktree (isolated copy of the repo)
2. Runs the subagent in that worktree (no file conflicts with other agents)
3. Merges changes back when the subagent completes
4. Auto-cleans the worktree if no changes were made

**Writ agents using worktrees:**
- `writ-architect` — reads codebase without interfering
- `writ-coder` — implements in isolation, no conflicts with parallel stories
- `writ-story-gen` — generates story files in parallel without conflicts

**`/implement-story --all`:** stories run simultaneously in separate worktrees. Each coder gets its own branch and worktree, and changes merge back. No file locking, no conflicts on shared files.

### Persistent Memory (`memory: project`)

Agents learn across sessions. The review agent remembers patterns it's seen, the architect remembers architectural decisions, the coder remembers conventions.

```
.claude/agent-memory/
├── writ-architect/MEMORY.md    # "This project uses repository pattern for data access"
├── writ-coder/MEMORY.md        # "Tests use vitest with MSW for API mocking"
└── writ-reviewer/MEMORY.md     # "Previous review caught SQL injection in routes/search.ts"
```

### Model Selection

The six Claude-native agents under `claude-code/agents/` (`writ-architect`, `writ-coder`, `writ-reviewer`, `writ-tester`, `writ-documenter`, `writ-story-gen`) carry their `model_tier` ([ADR-024](../.writ/decision-records/adr-024-model-delegation.md); contract text in `system-instructions.md` § Model Tiers) as a static `model:` frontmatter value. There is no `visual-qa` equivalent here yet; do not infer a seventh. The table resolves the tiers:

| Origin source | `anchor` | `floor` | escalation |
|---|---|---|---|
| `anchor.model` = the model Claude Code reports for the session; `anchor.effort` = `unknown` unless an effort setting is present in `.claude/settings*.json`; `anchor.platform = claude-code` | `model: inherit` | `model: haiku`. `haiku` is the family bottom, so it is at or below any Claude origin; static frontmatter can carry it without a runtime `min(haiku, origin)` check. If `haiku` is unavailable on the install: `model: inherit` + `effort: low`. | `model: inherit` |

**Degradation:** an unrecognized `model_tier`, or a family alias the install cannot resolve (verify `haiku`/`inherit` still resolve if your Claude Code version's defaults drift), warns and falls back to `inherit`. Never hard-fail the spawn. A Claude origin already at `haiku` means `floor` collapses to `anchor`, said once, no `degraded`.

| Agent | `model_tier` | `model:` |
|-------|------|------|
| writ-architect | `floor` | `haiku` |
| writ-story-gen | `floor` | `haiku` |
| writ-coder | `anchor` | `inherit` |
| writ-reviewer | `anchor` | `inherit` |
| writ-tester | `anchor` | `inherit` |
| writ-documenter | `anchor` | `inherit` |

`sonnet` is gone from `writ-tester` and `writ-documenter`: both are `anchor`, and a fixed `sonnet` would exceed a `haiku` origin. `inherit` is the only anchor value that respects the ceiling.

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

## Native Memory & the Writ Ledger

> **Native memory holds session preferences and trivia; the Writ ledger holds negotiated decisions, conventions, and lessons — the reviewable markdown layer that feeds native memory and any external index.**

On Claude Code, native memory is **`CLAUDE.md`** (auto-loaded into every session) plus **`.claude/agent-memory/`** (the per-agent `MEMORY.md` files where the architect, coder, and reviewer accumulate what they have learned). Let `CLAUDE.md` carry stable project preferences and let agent memory hold cross-session working notes. When a decision, convention, or lesson is negotiated and needs to outlive one machine's memory store, write it to the ledger under `.writ/decision-records/` or `.writ/knowledge/`, the layer a teammate reviews in a PR.

**Anti-pattern:** negotiated decisions that live only in native memory are unreviewable and are lost on a reinstall, a new machine, or a teammate who never had your store. Write the decision, the convention, or the lesson to the ledger, and let native memory keep only the ephemeral trivia.

**Three layers, one system of record:** native memory (session prefs/trivia, per platform) → the Writ ledger (canonical, reviewable markdown in git) → an optional external index (GBrain, disposable). The [`gbrain-interop` skill](../skills/gbrain-interop/SKILL.md) and [`.writ/docs/gbrain-recipe.md`](../.writ/docs/gbrain-recipe.md) cover the external-index layer. Removing that index loses nothing; the ledger is the only copy.

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
8. Delegates to writ-documenter (inherit, full access)
   → Updates docs
9. Orchestrator updates story status, commits
```

### Knowledge Loading

`/implement-story` performs the knowledge-loading hook before delegation. Claude Code does not need a separate hook or agent memory feature for this path: the top-level orchestrator greps `.writ/knowledge/`, assembles the optional `knowledge_context` block, and includes it in the prompts for `writ-architect`, `writ-coder`, and `writ-reviewer`.

### Preamble Convention

Manual and scripted installs copy `commands/_preamble.md` into `.claude/commands/` with the rest of the command files. Claude Code loads the invoked command markdown; the command's final `## References` section points the orchestrator at `_preamble.md` and `system-instructions.md`, No hook is needed.

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

### The /goal Stop Hook

Claude Code's `/goal <condition>` registers a session-scoped prompt-type Stop hook: on every stop attempt an evaluator judges the condition met / not-met+reason / impossible+reason, and not-met forces the run to continue. It is the same native hook mechanism as the `SubagentCompleted` example above, aimed at `scripts/exit-criteria.py check`. See `.writ/specs/archive/2026-08-12-machine-evaluable-exit-criteria/spec.md` § "What `/goal` showed, and why it is not the answer" for the case against treating `/goal` itself as the mechanism.

**The checker is the authority; `/goal` is only the delivery vehicle.** Story 5's command wiring makes `exit-criteria.py check` the independent, read-only re-derivation that `implement-phase` and `implement-spec` defer to in their completion steps. The `/goal` condition below likewise asks the checker and relays the verdict without restating or reinterpreting it. Never write a `/goal` condition that encodes its own pass/fail logic.

Register one goal at the outermost running command (`/implement-phase` or `/implement-spec`), with a condition that is satisfiable by pausing as well as by finishing (spec.md Business Rule 1: "Reaching a retained pause satisfies the gate"). A condition that only accepts a clean checker pass pushes the model past a human gate; spec.md's "What `/goal` showed" section documents `/goal`'s own injected prompt ("do not pause to ask the user what to do") causing this. Word the condition as an explicit three-way disjunction:

```
/goal Treat this stop as acceptable when ANY of the following is true — do not
collapse these into "the checker passed":
(a) `python3 scripts/exit-criteria.py check --command implement-phase --state .writ/state/phase-execution-{timestamp}.json` exits 0 (verdict: met);
(b) the run is currently paused awaiting a retained AskQuestion — for example the
    Step 2.3 execute/edit/abort confirmation — regardless of whether the checker
    has been invoked yet; this state is met on its own;
(c) the checker exits 2 (verdict: impossible) — a tripped loop bound, an
    unresolved challenge_required, or a phase-state/git mismatch.
If none of these hold, the condition is not-met: continue the run rather than
stopping, and never treat a pause as something to route around.
```

Clause (b) must stand on its own in the condition text; the checker does not report it. `implement-phase.md` and `implement-spec.md` invoke the checker late (Step 4.1c / the completion step), while a retained `AskQuestion`, such as Step 2.3's execute/edit/abort confirmation, can occur before the checker has run. A condition that only names "exits 0" and mentions the pause as an aside is the anti-pattern the spec's "What `/goal` showed" section warns against. Naming all three states keeps the hook compatible with `on_exhaustion: halt_reported` and the Autonomy Gate Classes.

**Single-slot behavior.** Registering a goal removes every existing top-level prompt Stop hook. Goals cannot nest: if `/implement-phase` holds a goal, calls `/implement-spec`, and `/implement-spec` also registers one, "the innermost silently destroys the outer, and clears leaving nothing behind." So only the outermost running command may hold a goal. `/implement-story`, the innermost loop of the three, must never register one.

**Refusal modes.** `/goal` can fail to register in two ways. Both return a message rather than throwing, so check for the message instead of assuming enforcement is active:

- **Restricted hooks** — the session has `disableAllHooks` set, or `allowManagedHooksOnly` is set and the goal hook isn't managed.
- **Untrusted workspace** — the project has not been marked trusted.

Both register nothing. A silently unset goal is worse than none: the run proceeds believing it is gated. Treat a missing confirmation message as a failure to diagnose, not as enforcement.

`adapters/cursor.md`, `adapters/codex.md`, and `adapters/openclaw.md` need no change for this wiring. They get the checker through the `exit-criteria.py check` calls already embedded in `implement-phase.md` and `implement-spec.md`, which are adapter-neutral. `/goal` adds to that; it does not replace it.

---

## Skills

Skills are the third Writ primitive, peer to commands and agents: capability files that describe how to do one thing well. See [ADR-009](../.writ/decision-records/adr-009-command-agent-skill-boundary.md) for the verb/noun/tool framing and [`.writ/docs/skills.md`](../.writ/docs/skills.md) for the user-facing explainer.

Claude Code uses a platform-namespaced install path (below). Codex CLI installs Writ skills at `.agents/skills/` per the AgentSkills standard; see [ADR-009 § Amendments](../.writ/decision-records/adr-009-command-agent-skill-boundary.md#amendments).

### Install Path

```
.claude/skills/<name>/SKILL.md
```

`install.sh --platform claude` and `update.sh --platform claude` fan skills out alongside commands and agents using the same three-way overlay logic, so local modifications to `.claude/skills/<name>/SKILL.md` survive updates. Sidecar files inside a skill folder (anything other than `SKILL.md`) are install-once: copied on first install, never overwritten on update.

### Loading Mechanism

Claude Code's skill discovery scans `.claude/skills/` and surfaces installed skills to the model with their frontmatter `description:` text. By default Claude may auto-invoke skills based on description match.

**Writ-authored skills opt out of ambient invocation** by setting `disable-model-invocation: true` in their frontmatter. Every skill load is then deterministic and traceable: Writ commands and agents name skills explicitly when they need them. Community skills installed by other means (e.g. `clawhub`, `agentskills.io` catalogs) follow whatever invocation behavior their installer configured.

### Invocation

Commands and agents that need a skill load it explicitly:

```
Read skills/<name>/SKILL.md
```

This maps to the native `Read` tool. The orchestrator (or command body) issues the `Read` call when the relevant phase begins, and the skill's content enters the agent's context for that phase.

For commands and agents that declare `required_skills:` in their frontmatter (see Story 5 / `system-instructions.md`), the harness issues `Read skills/<name>/SKILL.md` calls before the consumer's first phase begins. The convention was resolved revisit-to-adopt on 2026-08-11 on the strength of a named future consumer, Phase 10 progressive disclosure (ADR-021). Phase 10 evaluated the mechanism and did not adopt it: an eager pre-load moves extracted bytes into the floor that every invocation pays, so a disclosed command costs more per invocation than the monolith it replaced. Phase 10 loads its skills with an inline `Read skills/<name>/SKILL.md` at the point of need. The convention therefore has no consumer; nothing in the product declares the field. The schema, this mechanism, and the graceful-degradation rule are unchanged and stay supported. The adoption carries a review trigger of **2026-11-11**, aligned to ADR-021's own review: no consumer by then, deprecate; a consumer appears, record it and reset. See `system-instructions.md` → `required_skills:` frontmatter convention.

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

The former unattended CLI loop for multi-spec execution is retired and archived
(see `archive/`). Supervised multi-spec execution now runs through `/implement-phase`,
which sequences specs by cross-spec dependency, gives each spec a fresh isolated
execution lane (branch + worktree), quarantines terminal failures while independent
specs continue, and reconciles state read-only on resume. Map it to Claude Code as
the orchestrator session driving one `/implement-spec` worker per lane.

Recommended autonomy is a separate supported path on two commands.
`/create-spec --recommend` authors and locks one spec package from evidence, then
stops; it never implements. `/implement-phase --recommend` runs the phase end to
end: it authors any missing specs via `/create-spec --recommend`, implements the
phase's specs through the isolated lanes above, and ends at the completion report
with manual UAT handoff. It never merges, opens PRs, or releases.

---

## Command Workflow Integrity

When a Writ command uses a planning phase for discovery, the planning conversation serves the command; it does not become the command.

**Rule:** After discovery completes, the command resumes its documented phases and produces its documented artifacts (spec files, stories, ADRs, etc.). After artifact creation, the command terminates with a next-step suggestion. Do not spawn implementation subagents or offer to begin building after a planning command completes.

**Common failure:** After writing spec artifacts, the session offers to run `/implement-spec` or spawn coding subagents. Planning commands produce files and stop. Implementation is a separate command the user invokes.

**Reference:** System instructions → Prime Directive → Hard Constraints → "Never let Plan Mode absorb a command's workflow."

---

## Gotchas

1. **Worktree merges can conflict**: If two parallel coders modify the same file, the merge will conflict. Design stories with minimal overlap. The dependency graph in `/implement-story` helps prevent this.

2. **Agent teams are experimental**: Enable with `CLAUDE_CODE_EXPERIMENTAL_AGENT_TEAMS=1`. Known limitations around session resumption and shutdown. For production use, prefer sequential subagent delegation.

3. **Memory bootstrapping**: Agent memory starts empty. First few runs will be less effective. Ask agents explicitly to "update your memory with patterns you discover."

4. **Haiku for story-gen is the floor, not a knob**: `writ-story-gen` carries `model: haiku` because it is a `floor` agent under ADR-024 (templated output the user reviews before lock). Do not change it to a fixed `model: sonnet` — the anchor is the ceiling, and a fixed `sonnet` exceeds a `haiku` origin (see the tier table above). If a generated story fails validation, `/create-spec` Step 2.6a already re-runs it once at `anchor` (`inherit`); that escalate-once path is the quality lever.

5. **Subagents nest**: three-deep nesting is observed in practice (`/implement-phase` → spec-runner → `/implement-story` → gate agents). `/goal` does not nest: see **Single-slot behavior** under *The /goal Stop Hook* above. Only the outermost running command may hold one.

6. **Plan mode is read-only**: `permissionMode: plan` blocks all writes at the tool level. The architect and reviewer cannot modify files, even if prompted to.
