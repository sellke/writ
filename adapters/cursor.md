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

### Recommendation Interaction Mapping

Cursor uses `AskQuestion()` for bounded human choices and its returned option
identity for continuation. Append `(Recommended)` only to the display label
identified by the shared policy; do not encode recommendation state through
option position, affirmative wording, or a preselected UI default. When the
policy reports explicit equivalence, show no suffix and disclose that no option
has a defensible advantage.

Preserve stable option identity across display, selection, rationale, and resume.
Adapters map interaction mechanics only; they do not choose recommendation policy.
Equivalent observable semantics are required: recommendation label or disclosed equivalence, classified pause, concise rationale, and same-session continuation after an answer.

In `--recommend` mode, consume the policy result by selecting its stable option
identity automatically or by rendering its bounded pause unchanged. Show the
policy's decision, evidence, material alternatives, risk, reversibility,
selection source, and result/artifact summary without exposing private
chain-of-thought or transcript content. After a required answer, return control
to the active command in the same session with recommendation mode retained.
Cursor permission, authentication, and unavailable-tool failures remain hard
platform blockers.

### Fresh Isolated Execution Lanes

For `/implement-phase`, map the platform-neutral lane contract onto Cursor's
Task subagents and git worktrees:

- **Isolated worktree.** Before launching a spec, the orchestrator runs
  `scripts/phase-state.py create-lane`, which creates the lane branch
  `writ/phase/{phase-id}/{spec-id}` and an isolated worktree from the phase-branch
  head. The Task subagent operates inside that worktree; the primary Cursor
  checkout is never mutated during lane work.
- **Fresh context.** Launch the spec with the Task tool as a fresh subagent seeded
  only with artifact paths (spec path, phase-state path, lane branch/worktree,
  mode) — **no prior conversational transcript** is forwarded. The subagent loads
  what it needs from repository artifacts by path.
- **Run identifier.** Record the Task subagent's ID as `agentRunId` in phase state.
- **Structured result.** The subagent returns a single `phase-spec-result-v1`
  object; the parent validates it with `scripts/phase-state.py validate-result` and
  merges only a verified success back into the phase branch.

### Quarantine and Resume

Terminal failure disposition and `--resume` reconciliation are plain git plus the
neutral reducer — no Cursor-specific runtime is required:

- On terminal failure the orchestrator calls `scripts/phase-state.py quarantine`,
  which removes the lane worktree and renames the lane branch to
  `writ/quarantine/{spec-id}` (deterministic suffix on collision). The phase branch
  is left clean; dependents become `skipped_blocked`.
- A fresh Cursor Task subagent is used for the single permitted transient retry in
  the same lane — never a reused context.
- `--resume` runs `scripts/phase-state.py reconcile` (read-only) before any action;
  on a state/git mismatch Cursor surfaces the discrepancy and recovery command and
  does not mutate git.

## Agent Configuration Notes

### Sub-Agent Models

Agents express weight intent via `model_tier` (see [ADR-016](../.writ/decision-records/adr-016-model-tier-delegation.md)), which Cursor resolves to its own native primitives:

| Tier | Cursor resolution |
|---|---|
| `orchestration` | `inherit` (anchor — runs at the user's session model) |
| `capability` | `"fast"` (floor — Cursor's own fast-model primitive) |
| unset | `inherit` (today's default behavior) |
| reserved ordinal `-N` | reserve-only; clamps to `"fast"` (2-band today) — not resolved to deeper steps |

This is a **relative**, native-primitive resolution — Writ ships zero concrete model names for Cursor; `inherit`/`fast` are Cursor's own abstractions, not a Writ-maintained ranking.

**Graceful degradation:** if Cursor cannot honor a requested tier (no fast model available, or an unrecognized `model_tier` value), warn and fall back to the parent/inherited model — never hard-fail.

`user-story-generator.md` ships with `model_tier: capability`, which resolves to `"fast"` regardless of whether a concrete `model:` field is also present — a concrete `model:` always wins over `model_tier:` per precedence, but removing `model:` alone no longer changes behavior once `model_tier: capability` is set. To get default-model story generation quality, override the tier itself (edit `user-story-generator.md` to set `model_tier: orchestration`, or set `model: default`/`model: inherit` explicitly) rather than just deleting the `model:` line.

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

## Native Memory & the Writ Ledger

> **Native memory holds session preferences and trivia; the Writ ledger holds negotiated decisions, conventions, and lessons — the reviewable markdown layer that feeds native memory and any external index.**

On Cursor, native memory is **Cursor Memories** (the preferences and facts Cursor remembers about you across chats) plus **semantic codebase indexing** (the embedding index Cursor builds over your files for retrieval). Let Cursor Memories hold your preferred tone, your name, editor trivia, and ephemeral session context, and let the semantic index accelerate search. Neither is the system of record: when you and the agent *negotiate* a decision or convention, write it to the ledger under `.writ/decision-records/` or `.writ/knowledge/`, where it is reviewable in a PR.

**Anti-pattern:** negotiated decisions that live *only* in native memory are unreviewable and evaporate on platform churn — a reinstall, a new machine, or a teammate who never had your store. Write the *why* (the decision, the convention, the lesson) to the ledger instead, and let native memory keep only the ephemeral trivia.

**Three layers, one system of record:** native memory (session prefs/trivia, per platform) → the Writ ledger (canonical, reviewable markdown in git) → an optional external index (GBrain, disposable). The external-index layer is covered by the [`gbrain-interop` skill](../skills/gbrain-interop/SKILL.md) and [`.writ/docs/gbrain-recipe.md`](../.writ/docs/gbrain-recipe.md); removing that index loses nothing, because the ledger is the only copy that matters.

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
