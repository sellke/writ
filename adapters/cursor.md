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
│   ├── commands/                  # one file per `commands:` entry in .writ/manifest.yaml (32)
│   │   ├── assess-spec.md         # /assess-spec
│   │   ├── create-adr.md          # /create-adr
│   │   ├── create-goal.md         # /create-goal
│   │   ├── create-issue.md        # /create-issue
│   │   ├── create-spec.md         # /create-spec
│   │   ├── create-uat-plan.md     # /create-uat-plan
│   │   ├── design.md              # /design
│   │   ├── edit-spec.md           # /edit-spec
│   │   ├── implement-phase.md     # /implement-phase
│   │   ├── implement-spec.md      # /implement-spec
│   │   ├── implement-story.md     # /implement-story
│   │   ├── initialize.md          # /initialize
│   │   ├── knowledge.md           # /knowledge
│   │   ├── migrate.md             # /migrate
│   │   ├── new-command.md         # /new-command
│   │   ├── new-skill.md           # /new-skill
│   │   ├── plan-product.md        # /plan-product
│   │   ├── prototype.md           # /prototype
│   │   ├── refactor.md            # /refactor
│   │   ├── refresh-command.md     # /refresh-command
│   │   ├── reinstall-writ.md      # /reinstall-writ
│   │   ├── release.md             # /release
│   │   ├── research.md            # /research
│   │   ├── retro.md               # /retro
│   │   ├── revert.md              # /revert
│   │   ├── review.md              # /review
│   │   ├── security-audit.md      # /security-audit
│   │   ├── ship.md                # /ship
│   │   ├── status.md              # /status
│   │   ├── uninstall-writ.md      # /uninstall-writ
│   │   ├── update-writ.md         # /update-writ
│   │   └── verify-spec.md         # /verify-spec
│   ├── agents/                    # one file per `agents:` entry in .writ/manifest.yaml (7)
│   │   ├── architecture-check-agent.md  # Pre-implementation gate
│   │   ├── coding-agent.md              # TDD implementation
│   │   ├── documentation-agent.md       # Framework-adaptive docs
│   │   ├── review-agent.md              # Quality + security gate
│   │   ├── testing-agent.md             # Tests + coverage
│   │   ├── user-story-generator.md      # Parallel story creation
│   │   └── visual-qa-agent.md           # Optional UI validation (Gate 4.5)
│   └── skills/                    # one folder per `skills:` entry in .writ/manifest.yaml
│       └── <name>/SKILL.md
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

These Cursor tools are used directly; no adapter is needed:

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
neutral reducer; no Cursor-specific runtime is required:

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

Agents declare `model_tier: anchor | floor` ([ADR-024](../.writ/decision-records/adr-024-model-delegation.md); contract text in `system-instructions.md` § Model Tiers). Cursor resolves it through the `Task` tool's `model` parameter, whose schema lists the accepted slugs at run time:

| Origin source | `anchor` | `floor` | escalation |
|---|---|---|---|
| `anchor.model` = the model the harness prompt names ("powered by …"); `anchor.effort` = the effort suffix of the matching listed slug (`-thinking-high` → `high`, `-medium` → `medium`, none → `unknown`); `anchor.platform = cursor` | `inherit` (or omit `model`) | **(a)** a listed slug that shares the anchor's vendor prefix, is not the anchor's own slug, and whose embedded effort suffix is ≤ `anchor.effort` (when `anchor.effort` is `unknown`, the same-prefix slug with the lowest suffix). "Below" follows the vendor's published tier naming as read from the slug (Anthropic: haiku < sonnet < opus < fable; medium confidence; Writ keeps no ranking). **(b)** `inherit[effort=…]`: rejected by the tool on Cursor; skip. **(c)** `inherit`: when no listed same-prefix slug sits below the anchor. If the origin is the vendor's bottom tier (Anthropic: haiku/low), that is the family floor: say so once, no `degraded`. If the vendor has lower tiers that Cursor's list does not expose (an Opus origin today; no haiku/sonnet slug listed), emit one `degraded` line with `reason=no lower same-family slug listed`. The limit is the platform's, and the ADR-025 ledger records it. | `inherit` |

**Degradation:** if the schema lists only `inherit`, or the resolved slug is rejected, `floor` runs at `inherit` and emits one `degraded` line naming the observed reason. Never hard-fail. The retired string value `fast` is still accepted by the tool but self-reported the anchor model (medium confidence; see the verification record). It is not a cheaper value and must not be reintroduced.

#### Verification record — 2026-09-03

Origin: Claude Fable 5.1 / `high` @ cursor (harness prompt "powered by Claude Fable 5.1"; listed slug `claude-fable-5-1-thinking-high`). Slugs listed at run time: `inherit`, `claude-fable-5-1-thinking-high`, `claude-opus-5-thinking-high`, `composer-2.5-fast`, `cursor-grok-4.5-high-fast`, `cursor-grok-4.6-medium-fast`, `gpt-5.6-sol-medium`; `fast` not listed. Identical prompt for all three spawns: *"Report verbatim, and only, the model identity your own system prompt states. Do not use any tools. One line."*

| Spawn | `model` argument | Tool-level result (high confidence) | Self-report (medium confidence) |
|---|---|---|---|
| V1 | `fast` | accepted | "powered by Claude Fable 5.1" — the anchor |
| V2 | `inherit[effort=low]` | rejected — `Invalid model selection "inherit[effort=low]". Model could not be resolved to a valid subagent model.` + the allowed-slug list | — (never spawned) |
| V3 | `claude-opus-5-thinking-high` | accepted | "powered by Claude Opus 5" — a different model, same vendor prefix |

For this origin, (a) resolves to `claude-opus-5-thinking-high` (`-thinking-high` ≤ `high`, so the ceiling holds). The slug list changes between Cursor versions: re-derive from the live schema at spawn, and treat a stale record as a reason to re-verify, not a value to copy.

### Read-Only Agents

The review agent specifies `readonly: true`. Cursor enforces this at the tool level; the agent cannot write files. This is stronger than the prompt-based restrictions other platforms use.

### Parallel Agent Limits

Cursor supports up to 4 concurrent `Task()` sub-agents in a single message. More than 4 stories are batched (first 4, then next 4) by the `create-spec` command's Step 2.6.

## Command Workflow Integrity

When a Writ command uses Plan Mode for discovery (e.g., `/create-spec` Phase 1, `/plan-product` discovery), Plan Mode is a phase within the command, not a replacement for it.

**Rule:** After Plan Mode discovery completes, the command must resume its documented phases in Agent Mode and produce its documented artifacts (spec files, stories, ADRs, etc.). The conversation is an intermediate step, not the deliverable.

**Common failure:** The agent stays in Plan Mode and treats the planning conversation as the command's output, or switches to Agent Mode and offers to implement. Neither is correct; the command's next phase is artifact creation.

**Reference:** System instructions → Prime Directive → Hard Constraints → "Never let Plan Mode absorb a command's workflow."

## Skills

Skills are the third Writ primitive, peer to commands and agents: capability files that describe how to do one thing well. See [ADR-009](../.writ/decision-records/adr-009-command-agent-skill-boundary.md) for the verb/noun/tool framing and [`.writ/docs/skills.md`](../.writ/docs/skills.md) for the user-facing explainer.

Cursor uses a platform-namespaced install path (below). Codex CLI installs Writ skills at `.agents/skills/` per the AgentSkills standard; see [ADR-009 § Amendments](../.writ/decision-records/adr-009-command-agent-skill-boundary.md#amendments).

### Install Path

```
.cursor/skills/<name>/SKILL.md
```

`install.sh` and `update.sh` fan skills out alongside commands and agents using the same three-way overlay logic, so local modifications to `.cursor/skills/<name>/SKILL.md` survive updates. Sidecar files inside a skill folder (anything other than `SKILL.md`) are install-once: copied on first install, never overwritten on update.

### Loading Mechanism

Cursor exposes installed skills via the `<agent_skills>` system context block, which surfaces skill `description:` text to the model and makes each skill eligible for ambient invocation by description match.

**Writ-authored skills opt out of ambient invocation** by setting `disable-model-invocation: true` in their frontmatter. Every skill load is then deterministic and traceable in transcripts: agents and commands name skills explicitly when they need them. Community skills installed by other means (e.g. `clawhub`, `agentskills.io` catalogs) follow whatever invocation behavior their installer configured.

### Invocation

Commands and agents that need a skill load it explicitly:

```
Read skills/<name>/SKILL.md
```

The orchestrator (or command body) issues the `Read` call when the relevant phase begins. The skill's content is then in the agent's context for that phase.

For commands and agents that declare `required_skills:` in their frontmatter (see Story 5 / `system-instructions.md`), the harness pre-loads each named skill before the consumer's first phase begins. The convention was resolved revisit-to-adopt on 2026-08-11 on the strength of a named future consumer, Phase 10 progressive disclosure (ADR-021). Phase 10 evaluated the mechanism and did not adopt it: an eager pre-load moves extracted bytes into the floor that every invocation pays, so a disclosed command costs more per invocation than the monolith it replaced. Phase 10 loads its skills with an inline `Read skills/<name>/SKILL.md` at the point of need. The convention therefore has no consumer; nothing in the product declares the field. The schema, this mechanism, and the graceful-degradation rule are unchanged and stay supported. The adoption carries a review trigger of **2026-11-11**, aligned to ADR-021's own review: no consumer by then, deprecate; a consumer appears, record it and reset. See `system-instructions.md` → `required_skills:` frontmatter convention.

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

Or commit everything; specs, ADRs, and research are worth version-controlling.

## Native Memory & the Writ Ledger

> **Native memory holds session preferences and trivia; the Writ ledger holds negotiated decisions, conventions, and lessons — the reviewable markdown layer that feeds native memory and any external index.**

On Cursor, native memory is **Cursor Memories** (the preferences and facts Cursor remembers about you across chats) plus **semantic codebase indexing** (the embedding index Cursor builds over your files for retrieval). Let Cursor Memories hold your preferred tone, your name, editor trivia, and ephemeral session context, and let the semantic index accelerate search. Neither is the system of record: when you and the agent negotiate a decision or convention, write it to the ledger under `.writ/decision-records/` or `.writ/knowledge/`, where it is reviewable in a PR.

**Anti-pattern:** negotiated decisions that live only in native memory are unreviewable and are lost on a reinstall, a new machine, or a teammate who never had your store. Write the decision, the convention, or the lesson to the ledger, and let native memory keep only the ephemeral trivia.

**Three layers, one system of record:** native memory (session prefs/trivia, per platform) → the Writ ledger (canonical, reviewable markdown in git) → an optional external index (GBrain, disposable). The [`gbrain-interop` skill](../skills/gbrain-interop/SKILL.md) and [`.writ/docs/gbrain-recipe.md`](../.writ/docs/gbrain-recipe.md) cover the external-index layer. Removing that index loses nothing; the ledger is the only copy.

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
