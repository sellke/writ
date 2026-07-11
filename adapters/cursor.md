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
to the active command in the same session with recommendation mode retained;
durable and cross-session resume mechanics follow the neutral contract mapped
in the next section.
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

### Recommended Delivery Context and Resume

For Story 3, the top-level Cursor command transports the canonical
`delivery_context` into nested work and normalizes each nested response as
`recommend-command-result-v1`. Keep the execution ID, state/spec paths, mode,
non-secret propagation token, parent command, return schema, and package
manifest digest intact. The implement-spec parent may wrap an existing
implement-story report at this deterministic boundary; subagents do not mint
delivery executions or claim terminal delivery.

When user input is required, preserve stable question and option IDs in state
before yielding, retain recommend mode, and resume the same transition from the
returned Cursor option identity. Durable resume reloads by explicit execution
ID or one unambiguous spec/branch match and completes repository-only
reconciliation before any write.

Create state exclusively. For replacement, re-read revision and unknown fields,
validate the complete next document, write and flush a validated sibling
temporary file where supported, then atomically rename it. If Cursor's active
filesystem surface cannot provide equivalent crash-safe replacement, block
instead of weakening the contract.

For recommended story launch, Cursor must expose absolute working path, full git
ref/HEAD, story/delegated execution IDs, and ownership token in
`recommend-worktree-launch-v1`. The parent persists that result with
`scripts/recommend-state.py reserve-worktree` and returns
`recommend-worktree-reservation-ack-v1` before Gate 1 edits. Cursor Task
execution does not guarantee isolated linked-worktree identity, so the safe
baseline is serial in-place execution: one story at a time, reserving the
repository root/ref/HEAD through the same handshake. Use parallel Task stories
only when each has a distinct observable git worktree. Missing stable identity
blocks; never infer ownership from a Task label or transcript.

Story 3 repository-only reconciliation remains provider-free. After verified
implementation, Story 4 maps the neutral staging capabilities as follows:

- `findPullRequest`, `createPullRequest`, and `getPullRequest`: use the
  authenticated GitHub MCP pull-request tools when they can query exact
  repository/base/head identity and return full head SHA. Otherwise use
  authenticated `gh pr list/create/view --json` with structured arguments.
- `listRequiredChecks`: use authenticated `gh api` against branch-protection
  required status-check contexts/check-runs and PR head status. GitHub MCP PR
  status alone is insufficient unless it exposes the complete provider-required
  set. Return provider/repository/query-time/full-SHA identity, stable provider
  IDs/names/set digest or explicit provider-zero declaration, and separately
  classified config checks. Include explicit `authenticated: true` and a
  bounded `listRequiredChecks` query-operation ID/start/completion; caller
  success never implies authentication. Re-query the complete set before advancement.
  Unknown, needs-auth, and authorization-denied are distinct, never zero.
- `findPreview`: use authenticated `gh api` deployment/status/check metadata or
  existing Vercel project/deployment metadata only when `Preview Provider:
  vercel` and `Preview Project` identify an existing integration. Normalize
  `Preview Project` as `previewProjectId`; detected IDs are execution-only and
  never silently saved. Return only a safe
  URL whose deployment metadata contains the exact full PR head SHA. Normalize
  configured provider/evidence source/repository/project plus observable
  integration ID, provenance kind, and observation time; a URL pattern alone is
  not evidence.
  Enforce source/kind pairs: `deployment-status` maps to
  `provider-deployment`/`provider-status`, `check-output` to `provider-check`,
  and `project-convention` to itself.

Persist normalized evidence before waiting and pass it only to the explicit
reducer operations. Before `createPullRequest`, derive the operation key from
repository/base/head, persist and reconcile the bound Pending audit entry,
lookup, persist `authorized`, then persist `attempted` before the sole mutation.
Observe as `created`/`reconciled`, persist canonical IDs, and finalize. Repeated
absence after authorization blocks. Finalize the exact PR audit entry with
canonical provider ID/number/URL, reconcile the log, and call
`finalize-pr-audit` before checks; no later staging transition advances with a
Pending mutation audit. After any wait and immediately before
approval, repeat all three reads and return one same-operation reconciliation
envelope containing capability snapshot digest, PR/head, complete check-set
digest/statuses, preview provenance/status, UAT digest, and query time. One
attempt ID binds UTC RFC3339 observations after presentation and current
evidence; enforce five-minute/configured freshness and 30-second future skew.

Use `AskQuestion()` once for production approval with stable approve/reject IDs;
persist the returned actor/event identity and SHA before returning
`production_approved`. Silence is not a selection. No browser automation,
`deploy_to_vercel`, Vercel access-bypass URLs, merge tools/calls, and release
operations are forbidden in Story 4. Authentication or authorization denial is
reported once and stops.

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
