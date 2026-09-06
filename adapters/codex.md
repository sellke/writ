# Codex CLI Platform Adapter

Native integration with OpenAI Codex CLI: project-scoped TOML subagents under `.codex/agents/`, `AGENTS.md` as the primary instruction surface, and Codex’s tool stack (`Read`, `Write`, `Edit`, `Bash`, `Grep`, `Glob`) backing Writ commands. Writ does not register custom slash commands in Codex; users invoke workflows by asking the assistant to follow the Markdown files under `.codex/commands/`.

**Official references (verify claims here first):**

- [Slash commands](https://developers.openai.com/codex/cli/slash-commands)
- [Custom instructions with AGENTS.md](https://developers.openai.com/codex/guides/agents-md)
- [Subagents / multi-agent](https://developers.openai.com/codex/multi-agent/)
- [Advanced configuration](https://developers.openai.com/codex/config-advanced)

---

## Overview

| Concept | Codex CLI expression |
|---------|----------------------|
| User workflows | Markdown command files (`.codex/commands/*.md`) read via `Read` |
| Specialized roles | TOML subagents (`.codex/agents/*.toml`) spawned through Codex’s subagent system |
| Project guidance | `AGENTS.md` (+ optional `AGENTS.override.md`) with layered discovery |
| Skills | AgentSkills-format folders under `.agents/skills/<name>/SKILL.md` ([AgentSkills](https://agentskills.io)) |
| Safe defaults | `sandbox_mode` on each subagent (`read-only` vs `workspace-write`) |

Writ-authored agents for Codex live in the Writ repo at `codex/agents/*.toml` and install (copy or symlink) into `.codex/agents/`.

---

## Installation

### Automated (recommended)

`install.sh --platform codex` is supported today:

```bash
bash <(curl -s https://raw.githubusercontent.com/sellke/writ/main/scripts/install.sh) --platform codex
```

Preview overlays first:

```bash
bash <(curl -s https://raw.githubusercontent.com/sellke/writ/main/scripts/install.sh) --dry-run --platform codex
```

Updates use the same manifest + three-way overlay model as Cursor and Claude Code:

```bash
bash <(curl -s https://raw.githubusercontent.com/sellke/writ/main/scripts/update.sh) --platform codex
```

### Manual installation

For contributors wiring a fork by hand:

```bash
mkdir -p .codex/commands .codex/agents .agents/skills .writ/state
cp path/to/writ/commands/*.md .codex/commands/
cp path/to/writ/codex/agents/*.toml .codex/agents/
# Merge Writ block from codex/AGENTS.md.template into AGENTS.md (see Story 4 merge semantics)
```

Baseline Codex config is optional but recommended: copy `codex/config.toml.template` to `.codex/config.toml` once. Writ treats it as install-once and user-owned thereafter.

### `.gitignore` snippet

```gitignore
# Writ ephemeral workflow state (never commit transient automation)
.writ/state/

# Optional: local Codex overrides you do not want shared yet
# AGENTS.override.md
```

### Final structure (target)

```
your-project/
├── AGENTS.md                         # Project + Writ block (Writ-owned region marked)
├── .codex/
│   ├── agents/*.toml                 # Codex-native subagent definitions
│   ├── commands/*.md               # Writ command workflows
│   └── config.toml                 # User-owned (seeded once from template)
├── .agents/skills/<skill>/SKILL.md   # AgentSkills layout for Codex
└── .writ/                            # Specs, ADRs, runtime state
```

---

## Key Features Used

### Project subagents (`codex/agents/*.toml`)

Codex loads project agents from `.codex/agents/` (personal agents use `~/.codex/agents/`). Each file carries `name`, `description`, `sandbox_mode`, `developer_instructions`, and, on `floor` agents only, `model_reasoning_effort`. Writ never emits `model`. Writ ships seven agents aligned with the Cursor/Claude pipeline; see **Tool Mapping** for the inventory.

### Sandbox enforcement

`sandbox_mode` maps coarse permissions:

| `sandbox_mode` | Writ usage |
|----------------|------------|
| `read-only` | Architecture check, review, visual QA — must not mutate workspace |
| `workspace-write` | Coding, testing, documentation, story generator — may edit files and run commands |

This replaces Cursor’s `readonly:` flag and Claude Code’s `permissionMode` / `disallowedTools` with Codex’s native policy surface.

### AGENTS.md layering

Codex walks from repo root toward the working directory, merging `AGENTS.override.md` then `AGENTS.md`. Writ owns only the HTML-comment-delimited block injected by the installer; everything outside that region stays user-controlled. The default per-file budget is 32 KiB. Keep the Writ block small (the template targets ≤ 8 KiB) so projects retain room for product context.

When an install would push `AGENTS.md` beyond Codex’s effective limit, raise `project_doc_max_bytes` in `.codex/config.toml` (see [advanced configuration](https://developers.openai.com/codex/config-advanced)) or move bulky guidance into ordinary Markdown files under `.writ/docs/` that agents `Read` on demand.

### Experimental features

Codex exposes `/experimental` to toggle optional capabilities ([docs](https://developers.openai.com/codex/cli/slash-commands#toggle-experimental-features-with-experimental)). Writ does not require experimental flags for baseline `/implement-story`; multi-thread fan-out may benefit from settings your Codex version documents alongside `/agent`. Experimental toggles are operator preference. Mirror them in team docs if everyone needs the same behavior.

### Hooks (`codex_hooks`)

Writ’s `codex/config.toml.template` ships with `[features] codex_hooks = false`. Hooks are noisy for first-time installs, so users opt in. Writ ships no hook handlers — the seven TOMLs under `codex/agents/` are agent definitions, not hooks — and no Writ gate depends on one. *(unverified)*: whether Codex hooks can carry a Writ gate has not been observed on an install; keep hooks off unless you own the automation surface.

---

## Native Memory & the Writ Ledger

> **Native memory holds session preferences and trivia; the Writ ledger holds negotiated decisions, conventions, and lessons — the reviewable markdown layer that feeds native memory and any external index.**

On Codex, native memory is **`AGENTS.md`**, the primary instruction surface Codex merges from repo root toward the working directory. Writ owns only the HTML-comment-delimited block the installer injects; the surrounding region and **`AGENTS.override.md`** stay user-controlled for local, unshared preferences. Let `AGENTS.md` and `AGENTS.override.md` hold session-level and machine-local trivia. When a decision or convention is negotiated, write it to the ledger under `.writ/decision-records/` or `.writ/knowledge/`, where it is reviewable in git.

**Anti-pattern:** negotiated decisions that live only in native memory are unreviewable and are lost on a reinstall, a new machine, or a teammate who never had your store. Write the decision, the convention, or the lesson to the ledger, and let native memory keep only the ephemeral trivia.

**Three layers, one system of record:** native memory (session prefs/trivia, per platform) → the Writ ledger (canonical, reviewable markdown in git) → an optional external index (GBrain, disposable). The [`gbrain-interop` skill](../skills/gbrain-interop/SKILL.md) and [`.writ/docs/gbrain-recipe.md`](../.writ/docs/gbrain-recipe.md) cover the external-index layer. Removing that index loses nothing; the ledger is the only copy.

---

## Tool Mapping (Cursor → Codex CLI)

### Quick reference — orchestration primitives

| Cursor / Writ generic | Codex CLI | Notes |
|----------------------|-----------|-------|
| `Task({ prompt, readonly })` | Subagent spawn with matching `sandbox_mode` | Use explicit agent names from `.codex/agents/*.toml` |
| `AskQuestion()` | Structured numbered options in prose | No modal UI — mimic with clear option lists |
| `codebase_search` | `Grep` / `Glob` / ripgrep via `Bash` | Prefer native `Grep`/`Glob` when possible |
| `read_file` | `Read(path)` | Direct equivalent |
| `run_terminal_cmd` | `Bash(command)` | Respect sandbox of the active agent |
| `list_dir` | `Glob("pattern")` or `Bash("ls")` | Codex has no dedicated list-dir tool |
| `todo_write` | `Write(".writ/state/...json")` | File-based tracking |

### Writ agents ↔ Codex TOML

Each agent's `model_tier` ([ADR-024](../.writ/decision-records/adr-024-model-delegation.md); contract text in `system-instructions.md` § Model Tiers) resolves to the TOML header `scripts/gen-codex-agent-tomls.py` emits. Codex is single-vendor, so the floor is family-locked and effort-only:

| Origin source | `anchor` | `floor` | escalation |
|---|---|---|---|
| `.codex/config.toml` (project, else `~/.codex/config.toml`) → `model` and `model_reasoning_effort`; `unknown` when the keys are absent (`codex/config.toml.template` sets neither); `anchor.platform = codex` | omit `model` (parent's model and effort) | omit `model`, `model_reasoning_effort = "low"` | omit `model`, parent effort |

**Degradation:** an unrecognized `model_tier` warns and is emitted as `anchor` (both keys omitted). A parent already at `low` effort means `floor` collapses to `anchor`, said once, no `degraded`. If a Codex version rejects `model_reasoning_effort` on a subagent, drop the key and run at `anchor` with one `degraded` line. Never hard-fail the spawn.

| Agent (`agents/*.md`) | `.codex/agents/*.toml` | `sandbox_mode` | `model_tier` | Emitted header |
|-----------------------|-------------------------|----------------|---------------|-----------------|
| architecture-check-agent | `architecture-check-agent.toml` | `read-only` | `floor` | `model_reasoning_effort = "low"` |
| coding-agent | `coding-agent.toml` | `workspace-write` | `anchor` | — |
| documentation-agent | `documentation-agent.toml` | `workspace-write` | `anchor` | — |
| review-agent | `review-agent.toml` | `read-only` | `anchor` | — |
| testing-agent | `testing-agent.toml` | `workspace-write` | `anchor` | — |
| user-story-generator | `user-story-generator.toml` | `workspace-write` | `floor` | `model_reasoning_effort = "low"` |
| visual-qa-agent | `visual-qa-agent.toml` | `read-only` | `anchor` | — |

### Triggering agents

Use natural language together with `/agent` thread switching:

```
Spawn architecture-check-agent (read-only sandbox) to review story X before coding.
Then spawn coding-agent (workspace-write) for implementation.
```

Codex also exposes `/agent` as a built-in slash command for switching threads and inspecting subagent work ([docs](https://developers.openai.com/codex/cli/slash-commands#switch-agent-threads-with-agent)).

### MCP tools

Writ commands sometimes reference MCP servers generically. Codex surfaces MCP through `/mcp` ([docs](https://developers.openai.com/codex/cli/slash-commands#list-mcp-tools-with-mcp)). Configure servers in `.codex/config.toml`; the Writ template ships only a commented placeholder block; no servers are enabled by default.

### Apps & plugins

Codex lists connectors via `/apps` and plugins via `/plugins` ([slash reference](https://developers.openai.com/codex/cli/slash-commands)). Writ neither bundles nor requires plugins.

---

## Skills

Writ skills install to `.agents/skills/<name>/SKILL.md` on Codex, the AgentSkills layout Codex documents for shared capability files (see ADR-009 Amendments). Commands and agents load skills explicitly via `Read skills/<name>/SKILL.md` (path relative to repo root in Writ prompts).

Regenerate parity after editing canonical agents:

```bash
python3 scripts/gen-codex-agent-tomls.py
bash scripts/check-agent-parity.sh
```

---

## Workflow Patterns

### implement-story (single story)

1. Orchestrator reads `.writ/context.md`, story file, spec-lite, optional `.writ/knowledge/`.
2. Spawn **architecture-check-agent** (`read-only`) → PROCEED / CAUTION / ABORT.
3. Spawn **coding-agent** (`workspace-write`) → implements with TDD discipline.
4. Run lint / typecheck inline in orchestrator (per command).
5. Spawn **review-agent** (`read-only`) → PASS / FAIL (≤ 3 review loops combined with visual QA per command contract).
6. Spawn **testing-agent** (`workspace-write`).
7. Optionally spawn **visual-qa-agent** when story lists visual references.
8. Spawn **documentation-agent** (`workspace-write`).
9. Update story checkboxes / status; commit if policy allows.

Parallel fan-out inside a phase uses multiple Codex subagent threads; use `/agent` to inspect each thread.

### create-spec — parallel story generation

Delegate multiple **user-story-generator** instances (each `workspace-write`) with disjoint outputs, one path per story file, to avoid contention.

### Preamble convention

Writ commands reference `commands/_preamble.md` and `system-instructions.md` in their `## References` sections. Ensure both exist in the installation target and `Read` them when starting a command.

Copy `_preamble.md` beside the other command markdown files during install so relative paths resolve inside `.codex/commands/`.

### Knowledge loading (`/implement-story`)

Before spawning architecture-check or coding agents, `/implement-story` loads optional `.writ/knowledge/` snippets keyed to story keywords. On Codex there is no separate memory daemon; the orchestrator must `Read` or `Grep` those files into the prompt bundle. Keep knowledge files small; large dumps belong in specs.

### Structured questions (`AskQuestion` emulation)

Cursor exposes `AskQuestion`; Codex does not. When a Writ command specifies `AskQuestion`, render the options as numbered Markdown choices and wait for the user’s reply in the composer. Maintain the contract: bounded decision space, explicit labels, no hidden defaults.

Assign each bounded option a stable identity that does not change when its
display number changes. Append `(Recommended)` only to the label selected by the
shared policy; never infer selection from numbering, affirmative wording, or
silence. If the policy finds explicit equivalence, label no option and disclose
the equivalence.

Preserve stable option identity across display, selection, rationale, and resume.
Adapters map interaction mechanics only; they do not choose recommendation policy.
Equivalent observable semantics are required: recommendation label or disclosed equivalence, classified pause, concise rationale, and same-session continuation after an answer.

For `--recommend`, translate the policy's selected stable identity to the
displayed number, or present its classified pause with missing evidence, bounded
choices, and a safe next action. Show decision, evidence, material alternatives,
risk, reversibility, selection source, and result/artifact without private
chain-of-thought or transcript content. After a required composer reply,
continue the active parent session with recommendation mode retained and do not
repeat the answered decision. Durable or cross-session recovery remains the
neutral orchestrator's responsibility. Sandbox, approval, authentication, and
unavailable-capability failures remain hard platform blockers.

### Fresh Isolated Execution Lanes

For `/implement-phase`, map the platform-neutral lane contract onto Codex CLI
agent threads and git worktrees:

- **Isolated worktree.** The orchestrator runs `scripts/phase-state.py create-lane`
  to create the lane branch `writ/phase/{phase-id}/{spec-id}` and an
  isolated worktree from the phase-branch head. The Codex agent thread runs with
  that worktree as its working directory; the primary checkout is never mutated
  during lane work.
- **Fresh context.** Start a new Codex agent thread seeded only with artifact
  paths (spec path, phase-state path, lane branch/worktree, mode) —
  **no prior conversational transcript** is forwarded. Load context from
  repository artifacts by path rather than replaying history.
- **Run identifier.** Record the Codex thread/agent ID as `agentRunId`.
- **Structured result.** The thread returns a single `phase-spec-result-v1`
  object; the parent validates it with `scripts/phase-state.py validate-result`
  and merges only a verified success into the phase branch.

### Quarantine and Resume

Terminal failure disposition and `--resume` reconciliation are plain git plus the
neutral reducer:

- On terminal failure the orchestrator calls `scripts/phase-state.py quarantine`,
  which removes the lane worktree and renames the lane branch to
  `writ/quarantine/{spec-id}` (deterministic suffix on collision). The phase branch
  stays clean; dependents become `skipped_blocked`.
- Codex starts a fresh agent thread for the single permitted transient retry in the
  same lane.
- `--resume` runs `scripts/phase-state.py reconcile` (read-only) first; on a
  state/git mismatch it reports the discrepancy and recovery command without
  mutating git.

### `/implement-spec` batches

`/implement-spec` computes story dependency batches. Parallel batches map to concurrent Codex subagent threads when safe; sequential batches stay ordered. The orchestrator session owns dependency bookkeeping; subagents must not mutate story files outside their assigned scope.

### Autonomous multi-spec execution (retired CLI loop)

The former unattended CLI loop for multi-spec execution is retired and archived
(see `archive/`). Use `/implement-phase` for supervised multi-spec execution: it
sequences specs by cross-spec dependency, isolates each spec in a fresh execution
lane (branch + worktree), quarantines terminal failures while independent specs
continue, and reconciles state read-only on resume. Recommended autonomy is a
separate supported path on two commands. `/create-spec --recommend` authors and
locks one spec package from evidence, then stops. `/implement-phase --recommend`
runs the phase end to end: it authors any missing specs, implements the phase's
specs through the isolated lanes above, and ends at the completion report with
manual UAT handoff. It never merges, opens PRs, or releases.

---

## CLI Usage

### Interactive session

```bash
cd your-project
codex
```

Confirm Codex picked up project root (`AGENTS.md`, `.codex/config.toml`). Use `/status` for Codex session diagnostics ([built-in](https://developers.openai.com/codex/cli/slash-commands#inspect-the-session-with-status)).

### Non-interactive / automation

Prefer the Codex CLI flags documented upstream for your version (`codex --help`). Writ commands themselves remain Markdown-driven regardless of headless vs TTY.

### Session housekeeping

Codex provides `/compact` for transcript compression, `/clear` for a fresh chat inside the CLI, `/fork` and `/side` for branching conversations, `/resume` for returning to saved sessions, and `/copy` for copying the latest assistant output ([slash reference](https://developers.openai.com/codex/cli/slash-commands)). On long `/implement-spec` runs, `/compact` between batches keeps earlier story context from crowding out active work.

### Permissions & approvals

`/permissions` adjusts approval presets interactively ([docs](https://developers.openai.com/codex/cli/slash-commands#update-permissions-with-permissions)). Align CLI approvals with Writ’s gate expectations: set `sandbox_mode = "read-only"` on read-only agents' TOML files so Codex enforces the boundary rather than relying on human diligence.

### Debugging configuration drift

Use `/debug-config` when an effective setting disagrees with `.codex/config.toml` ([docs](https://developers.openai.com/codex/cli/slash-commands#inspect-config-layers-with-debug-config)). This is common during Writ upgrades when users overlay local experimentation. Capture `/debug-config` output before filing upstream issues.

---

## Command Workflow Integrity

Writ commands assume Plan Mode vs Agent Mode discipline (see `commands/_preamble.md`): discovery may switch to Plan Mode, but the command must finish in Agent Mode and produce its artifacts. Codex's built-in `/plan` slash command is Codex planning UX, not Writ Plan Mode. When a Writ command says “switch to Plan Mode,” follow the Writ command’s linked phases rather than invoking `/plan`, unless the user explicitly chooses Codex plan mode for exploration.

---

## Built-in Codex Commands vs Writ Commands

Codex exposes many built-ins (`/plan`, `/review`, `/status`, `/init`, `/permissions`, `/model`, `/agent`, `/fork`, `/side`, `/compact`, …) documented in the [slash command reference](https://developers.openai.com/codex/cli/slash-commands). Writ ships Markdown workflows with overlapping names (`/plan-product`, `/review`, `/status`, …), but those Writ names live in documentation and `.codex/commands/` filenames, not as Codex slash registrations.

**Coexistence rules:**

- Bare `/status`, `/review`, or `/plan` in the Codex composer runs Codex’s built-ins.
- To run Writ’s `/status`, `/review`, or `/plan-product` workflows, instruct the assistant to `Read` the corresponding `.codex/commands/<name>.md` file and execute its phases verbatim.

Writ does not rename commands to avoid collisions; this documentation carries the resolution.

### Collision reference table (non-exhaustive)

| Codex built-in (bare slash) | Typical Codex behavior | Writ workflow that overlaps by name | How to reach the Writ workflow |
|-----------------------------|----------------------|-------------------------------------|--------------------------------|
| `/plan` | Enter Codex plan mode for exploratory planning | `/plan-product` (Markdown command) | `Read .codex/commands/plan-product.md` and execute phases |
| `/review` | Working-tree review assistant | `/review` diff QA command | `Read .codex/commands/review.md` |
| `/status` | Session diagnostics (model, tokens, roots) | `/status` project dashboard command | `Read .codex/commands/status.md` |
| `/init` | Scaffold `AGENTS.md` | `/initialize` Writ bootstrap | `Read .codex/commands/initialize.md` |

Consult the official slash popup; OpenAI adds commands over time.

---

## Gotchas

| Issue | Mitigation |
|-------|------------|
| AGENTS.md budget (32 KiB default) | Keep Writ template lean; split large guidance into repo docs under `.writ/docs/` |
| Built-in slash ambiguity | Default to Codex built-ins for bare `/commands`; require explicit `Read` of Writ markdown for Writ workflows |
| Subagent schema drift | Track upstream [multi-agent](https://developers.openai.com/codex/multi-agent/) docs — regenerate TOML via `scripts/gen-codex-agent-tomls.py` after editing `agents/*.md` |
| Skills path divergence | Codex uses `.agents/skills/` while Cursor/Claude remain platform-namespaced — see ADR-009 Amendments |
| Floor is effort-only | `model_reasoning_effort = "low"` with `model` omitted — the parent's model is used; verify the parent model with `/model` |
| Markdown fenced blocks inside TOML `developer_instructions` | Preserve triple-quote escaping — regenerate via `scripts/gen-codex-agent-tomls.py` rather than hand-editing huge blobs |
| Parallel agents confusing transcripts | Name threads explicitly; use `/agent` to confirm which subagent owns which phase |
| Browser / vision tooling | Optional UI flows (`visual-qa-agent`) expect browser-class tools when available — skip when running minimal sandboxes |

---

## Quality gate cheat sheet (Codex)

Use this when translating `/implement-story` gates without Cursor-specific tooling:

| Gate | Codex enforcement idea |
|------|------------------------|
| Architecture | Spawn `architecture-check-agent` (`read-only`). Abort path stops before edits. |
| Boundary map | Orchestrator lists planned files; no Codex-native helper — keep as Markdown checklist in-command. |
| Coding | `coding-agent` (`workspace-write`) owns edits + tests. |
| Lint / typecheck | Orchestrator runs repo-native commands via `Bash`. |
| Review | `review-agent` (`read-only`). Parse PASS/FAIL from structured response headers per command contract. |
| Testing | `testing-agent` (`workspace-write`). Enforce coverage policy via repo tooling. |
| Documentation | `documentation-agent` (`workspace-write`). |

Codex does not replay failures across gates; the orchestrator command markdown (`implement-story.md`) owns the loops.

### Maintainer checklist (ship / upgrade)

1. Regenerate `codex/agents/*.toml` after touching `agents/*.md`.
2. Run `bash scripts/check-agent-parity.sh`; warnings must be intentional.
3. Re-measure `wc -c codex/AGENTS.md.template` after manifest command churn (stay ≤ 8192 bytes).
4. Re-read OpenAI Codex release notes when bumping pinned CLI assumptions; adjust the slash collision table if new built-ins overlap Writ names.
5. Verify dry-run install output lists seven agents and correct `SKILLS_DIR` (`.agents/skills/`).

### Observability

Writ stores durable artifacts under `.writ/` (specs, logs like `refresh-log.md`, execution snapshots under `.writ/state/`). Codex’s `/feedback` command ships diagnostics to OpenAI ([slash docs](https://developers.openai.com/codex/cli/slash-commands#send-feedback-with-feedback)); it is unrelated to Writ’s logging. When debugging a Writ-on-Codex issue, capture both the relevant `.writ/` files and the Codex `/debug-config` / `/status` output so maintainers can compare CLI policy with methodology state.

### Windows sandbox note

`/sandbox-add-read-dir` exists for Windows-only extra read roots ([slash docs](https://developers.openai.com/codex/cli/slash-commands#grant-sandbox-read-access-with-sandbox-add-read-dir)). Writ examples assume POSIX paths; adjust drive-letter paths when scripting `Bash` steps on Windows hosts.

### Security posture

Writ’s `/security-audit` command remains Markdown-orchestrated; Codex’s sandbox reduces blast radius but does not replace dependency audits or secret scanning. Keep `[features] codex_hooks = false` until your team documents hook handlers; an accidental auto-approval hook turns CLI convenience into CI policy.

Read-only agents (`sandbox_mode = "read-only"`) constrain lateral movement during architecture, review, and visual QA phases. Tighten sandbox defaults before weakening prompts.

**Baseline reminders:**

- Never paste production secrets into agent prompts; treat transcripts as semi-public.
- Review `Bash` proposals carefully before approving workspace-write agents.
- Use `/permissions` intentionally after changing repos or checking out unfamiliar branches.

---

## Cross-references

| Related | Relationship |
|---------|--------------|
| `adapters/claude-code.md` | Closest parallel for workflow depth |
| `adapters/cursor.md` | Task/AskQuestion idioms |
| `codex/agents/*.toml` | Canonical Codex-native Writ agents |
| `codex/AGENTS.md.template` | Merge template fragment |
| `codex/config.toml.template` | Install-once baseline |
| `.writ/decision-records/adr-009-command-agent-skill-boundary.md` | Skills boundary + Codex path amendment |
