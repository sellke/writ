# Codex CLI Platform Adapter

Native integration with **OpenAI Codex CLI**: project-scoped TOML subagents under `.codex/agents/`, `AGENTS.md` as the primary instruction surface, and Codex’s tool stack (`Read`, `Write`, `Edit`, `Bash`, `Grep`, `Glob`) backing Writ commands. Writ does **not** register custom slash commands in Codex; users invoke workflows by asking the assistant to follow the Markdown files under `.codex/commands/`.

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

After this platform ships in Writ core:

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

Baseline Codex config is optional but recommended — copy `codex/config.toml.template` to `.codex/config.toml` once; Writ treats it as **install-once** user-owned thereafter.

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

Codex loads project agents from `.codex/agents/` (personal agents use `~/.codex/agents/`). Each file carries `name`, `description`, `developer_instructions`, optional `model`, and `sandbox_mode`. Writ ships seven agents aligned with the Cursor/Claude pipeline — see **Tool Mapping** for the inventory.

### Sandbox enforcement

`sandbox_mode` maps coarse permissions:

| `sandbox_mode` | Writ usage |
|----------------|------------|
| `read-only` | Architecture check, review, visual QA — must not mutate workspace |
| `workspace-write` | Coding, testing, documentation, story generator — may edit files and run commands |

This replaces Cursor’s `readonly:` flag and Claude Code’s `permissionMode` / `disallowedTools` with Codex’s native policy surface.

### AGENTS.md layering

Codex walks from repo root toward the working directory, merging `AGENTS.override.md` then `AGENTS.md`. Writ owns **only** the HTML-comment-delimited block injected by the installer; outside that region stays user-controlled. Default per-file budget is **32 KiB** — keep the Writ block lean (template targets ≤ 8 KiB) so projects retain room for product context.

When an install would push `AGENTS.md` beyond Codex’s effective limit, raise `project_doc_max_bytes` in `.codex/config.toml` (see [advanced configuration](https://developers.openai.com/codex/config-advanced)) or move bulky guidance into ordinary Markdown files under `.writ/docs/` that agents `Read` on demand.

### Experimental features

Codex exposes `/experimental` to toggle optional capabilities ([docs](https://developers.openai.com/codex/cli/slash-commands#toggle-experimental-features-with-experimental)). Writ does **not** require experimental flags for baseline `/implement-story`, but multi-thread fan-out may benefit from settings your Codex version documents alongside `/agent`. Treat experimental toggles as operator preference — mirror them in team docs if everyone needs the same behavior.

### Hooks (`codex_hooks`)

Writ’s `codex/config.toml.template` ships with `[features] codex_hooks = false`. Hooks are powerful but noisy for first-time installs — users opt in deliberately. Future specs may wire Codex hooks to Writ gates; until then, keep hooks off unless you own the automation surface.

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

| Agent (`agents/*.md`) | `.codex/agents/*.toml` | `sandbox_mode` | Optional fast model (`model:` in manifest) |
|-----------------------|-------------------------|----------------|---------------------------------------------|
| architecture-check-agent | `architecture-check-agent.toml` | `read-only` | `gpt-5-mini` |
| coding-agent | `coding-agent.toml` | `workspace-write` | — |
| documentation-agent | `documentation-agent.toml` | `workspace-write` | — |
| review-agent | `review-agent.toml` | `read-only` | — |
| testing-agent | `testing-agent.toml` | `workspace-write` | — |
| user-story-generator | `user-story-generator.toml` | `workspace-write` | `gpt-5-mini` |
| visual-qa-agent | `visual-qa-agent.toml` | `read-only` | inherit / unspecified |

Model IDs are concrete Codex model strings — verify against `/model` on your CLI if defaults drift.

### Triggering agents

Use natural language together with `/agent` thread switching:

```
Spawn architecture-check-agent (read-only sandbox) to review story X before coding.
Then spawn coding-agent (workspace-write) for implementation.
```

Codex also exposes `/agent` as a built-in slash command for switching threads inspecting subagent work ([docs](https://developers.openai.com/codex/cli/slash-commands#switch-agent-threads-with-agent)).

### MCP tools

Writ commands sometimes reference MCP servers generically. Codex surfaces MCP through `/mcp` ([docs](https://developers.openai.com/codex/cli/slash-commands#list-mcp-tools-with-mcp)). Configure servers in `.codex/config.toml`; the Writ template ships a commented placeholder block only — no servers are enabled by default.

### Apps & plugins

Codex lists connectors via `/apps` and plugins via `/plugins` ([slash reference](https://developers.openai.com/codex/cli/slash-commands)). Writ neither bundles nor requires plugins — treat them as optional acceleration, not dependencies of the methodology.

---

## Skills

Writ skills install to **`.agents/skills/<name>/SKILL.md`** on Codex — the AgentSkills-friendly layout Codex documents for shared capability files (see ADR-009 Amendments). Commands and agents continue to load skills explicitly via `Read skills/<name>/SKILL.md` (path relative to repo root in Writ prompts).

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

Parallel fan-out inside a phase is achieved by multiple Codex subagent threads — consult `/agent` to inspect each thread.

### create-spec — parallel story generation

Delegate multiple **user-story-generator** instances (each `workspace-write`) with disjoint outputs — isolate paths per story file to avoid contention.

### Preamble convention

As with other platforms, Writ commands reference `commands/_preamble.md` and `system-instructions.md` inside their `## References` sections — ensure both exist in the installation target (`Read` them when starting a command).

Copy `_preamble.md` beside the other command markdown files during install so relative paths resolve inside `.codex/commands/`.

### Knowledge loading (`/implement-story`)

Before spawning architecture-check or coding agents, `/implement-story` loads optional `.writ/knowledge/` snippets keyed to story keywords. On Codex there is no separate memory daemon — the orchestrator must `Read` or `Grep` those files into the prompt bundle explicitly. Keep knowledge files small and curated; large dumps belong in specs, not ambient knowledge.

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

### Recommended Delivery Context and Resume

The Codex parent thread transports `delivery_context` through command/subagent
boundaries and normalizes nested output as `recommend-command-result-v1`.
Preserve execution ID, canonical state/spec paths, recommend mode, non-secret
propagation token, parent command, return schema, and package manifest digest.
Subagent threads neither create delivery executions nor claim overall delivery
completion; implement-spec may wrap their existing report at its deterministic
normalization boundary.

Before waiting for a composer answer, preserve stable question and option IDs,
recommend mode, and the same resume transition. Durable resume selects an
explicit execution ID or one unambiguous spec/branch match and performs
repository-only reconciliation before any workspace write or agent fan-out.

Create state exclusively. On replacement, re-read revision and unknown fields,
validate the complete next document, write and flush a validated sibling
temporary file where supported, then atomically rename it. If the active Codex
sandbox cannot perform equivalent crash-safe replacement, block rather than
truncate the canonical state in place.

Before recommended Gate 1, a Codex thread must report absolute worktree path,
full ref/HEAD, story/delegated execution IDs, and ownership token as
`recommend-worktree-launch-v1`. The parent verifies git worktree identity,
persists it with `scripts/recommend-state.py reserve-worktree`, and returns
`recommend-worktree-reservation-ack-v1`. Parallel threads are allowed only when
each has a distinct observable linked worktree. Because Codex thread isolation
varies by version/configuration, fall back to documented one-at-a-time serial
in-place execution with the repository root/ref/HEAD handshake; if stable
identity is still unavailable, block. Thread names and `/agent` listings alone
are not ownership evidence.

Story 3 repository-only reconciliation remains provider-free. Story 4 maps
`findPullRequest`, `createPullRequest`, `getPullRequest`,
`listRequiredChecks`, and `findPreview` to a configured integration or
authenticated `gh`/`gh api`. PR lookup always uses provider repository/base/head
identity. Derive that operation key, reconcile its bound Pending entry, persist
`authorized`, then `attempted` before the sole create. Observe `created` or
`reconciled` by lookup before canonical IDs are finalized; repeated absence
after authorization blocks.
Finalize the exact PR entry with canonical provider ID/number/URL, reconcile
the log, and call `finalize-pr-audit` before checks. No later staging transition
advances while a mutation-related recommendation entry remains Pending.

Required-check discovery reads branch-protection/provider requirements and check
runs, then separately classifies configured additive names. Normalize
provider/repository/query time/head and stable provider IDs/names/set digest or
explicit provider zero plus `authenticated: true` and concrete
`listRequiredChecks` operation ID/start/completion; command success never
implies authentication. Re-query the full set before advancing. Unknown,
needs-auth, and authorization-denied remain distinct. Preview discovery reads
existing deployment/status/check metadata; configured Vercel metadata is
eligible only for a configured project/source with observable integration
provenance and exact full-SHA binding. `Preview Project` maps to
`previewProjectId`; detected IDs are execution-only and never auto-saved.
URL-pattern-only evidence is invalid. Enforce
`deployment-status → provider-deployment|provider-status`,
`check-output → provider-check`, and
`project-convention → project-convention`.
Persist normalized evidence before yielding. Immediately before approval,
repeat all reads and return one envelope binding capability snapshot digest,
PR/head, complete check-set digest/IDs/statuses, preview provenance/status, UAT
digest, and query time.
One reconciliation attempt ID binds UTC RFC3339 observations after
presentation/current evidence, within configured-or-five-minute freshness and
30-second future skew.

Codex renders one numbered approve/reject production decision with stable IDs
and no default. Only an explicit composer reply receives a persisted event ID;
silence remains `awaiting_approval`. If unattended waiting is unsupported,
preserve `waiting_ci` or `discovering_preview` and provide the exact resume
command.

No browser automation, deployment provisioning, `deploy_to_vercel`, access-
bypass URL, merge call, or release operation is allowed in Story 4. An
authentication or authorization denial is reported once and stops.

### `/implement-spec` batches

`/implement-spec` computes story dependency batches — parallel batches should map to concurrent Codex subagent threads when safe, sequential batches stay strictly ordered. The orchestrator session owns dependency bookkeeping; individual subagents should not mutate downstream story files outside their assigned scope.

### Autonomous multi-spec execution (retired CLI loop)

The former unattended CLI loop for multi-spec execution is **retired and archived**
(see `archive/`). Use `/implement-phase` for supervised multi-spec execution: it
sequences specs by cross-spec dependency, isolates each spec in a fresh execution
lane (branch + worktree), quarantines terminal failures while independent specs
continue, and reconciles state read-only on resume. Bounded single-spec autonomy is
a separate, explicitly supported path (`/implement-spec --recommend <one-spec>`);
multi-spec `/implement-phase --recommend` remains excluded.

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

Codex provides `/compact` for transcript compression, `/clear` for a fresh chat inside the CLI, `/fork` and `/side` for branching conversations, `/resume` for returning to saved sessions, and `/copy` for grabbing the latest assistant output ([slash reference](https://developers.openai.com/codex/cli/slash-commands)). Long `/implement-spec` runs benefit from occasional `/compact` passes so earlier story context does not crowd out active work — schedule compacts between batches when transcripts grow large.

### Permissions & approvals

`/permissions` adjusts approval presets interactively ([docs](https://developers.openai.com/codex/cli/slash-commands#update-permissions-with-permissions)). Align CLI approvals with Writ’s gate expectations: read-only agents should never rely on human diligence alone — prefer `sandbox_mode = "read-only"` on those TOML files so Codex enforces the boundary.

### Debugging configuration drift

Use `/debug-config` when an effective setting disagrees with `.codex/config.toml` ([docs](https://developers.openai.com/codex/cli/slash-commands#inspect-config-layers-with-debug-config)). Common during Writ upgrades when users overlay local experimentation — capture `/debug-config` output before filing upstream issues.

---

## Command Workflow Integrity

Writ commands assume **Plan Mode vs Agent Mode discipline** (see `commands/_preamble.md`): discovery may switch to Plan Mode, but the command must finish in Agent Mode producing its artifacts. Codex has a built-in `/plan` slash command — that is **Codex planning UX**, not Writ Plan Mode. When a Writ command says “switch to Plan Mode,” follow the **Writ command’s linked phases**, not an automatic `/plan` slash invocation, unless the user explicitly chooses Codex plan mode for exploration.

---

## Built-in Codex Commands vs Writ Commands

Codex exposes many built-ins (`/plan`, `/review`, `/status`, `/init`, `/permissions`, `/model`, `/agent`, `/fork`, `/side`, `/compact`, …) documented in the [slash command reference](https://developers.openai.com/codex/cli/slash-commands). Writ ships Markdown workflows that conceptually overlap names (`/plan-product`, `/review`, `/status`, …) but those **Writ names live in documentation + `.codex/commands/` filenames**, not as Codex slash registrations.

**Coexistence rules:**

- Bare `/status`, `/review`, or `/plan` in the Codex composer runs **Codex’s** built-ins.
- To run **Writ’s** `/status`, `/review`, or `/plan-product` workflows, instruct the assistant to `Read` the corresponding `.codex/commands/<name>.md` file and execute its phases verbatim.

Writ intentionally **does not rename** commands to avoid collisions — documentation carries the resolution.

### Collision reference table (non-exhaustive)

| Codex built-in (bare slash) | Typical Codex behavior | Writ workflow that overlaps by name | How to reach the Writ workflow |
|-----------------------------|----------------------|-------------------------------------|--------------------------------|
| `/plan` | Enter Codex plan mode for exploratory planning | `/plan-product` (Markdown command) | `Read .codex/commands/plan-product.md` and execute phases |
| `/review` | Working-tree review assistant | `/review` diff QA command | `Read .codex/commands/review.md` |
| `/status` | Session diagnostics (model, tokens, roots) | `/status` project dashboard command | `Read .codex/commands/status.md` |
| `/init` | Scaffold `AGENTS.md` | `/initialize` Writ bootstrap | `Read .codex/commands/initialize.md` |

Always consult the official slash popup — OpenAI adds commands over time.

---

## Gotchas

| Issue | Mitigation |
|-------|------------|
| AGENTS.md budget (32 KiB default) | Keep Writ template lean; split large guidance into repo docs under `.writ/docs/` |
| Built-in slash ambiguity | Default to Codex built-ins for bare `/commands`; require explicit `Read` of Writ markdown for Writ workflows |
| Subagent schema drift | Track upstream [multi-agent](https://developers.openai.com/codex/multi-agent/) docs — regenerate TOML via `scripts/gen-codex-agent-tomls.py` after editing `agents/*.md` |
| Skills path divergence | Codex uses `.agents/skills/` while Cursor/Claude remain platform-namespaced — see ADR-009 Amendments |
| Fast model aliases | Manifest `model: fast` becomes concrete IDs (`gpt-5-mini` today) — verify with `/model` |
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

Codex does not automatically replay failures across gates — the orchestrator command markdown owns loops (`implement-story.md`).

### Maintainer checklist (ship / upgrade)

1. Regenerate `codex/agents/*.toml` after touching `agents/*.md`.
2. Run `bash scripts/check-agent-parity.sh` — warnings must be intentional.
3. Re-measure `wc -c codex/AGENTS.md.template` after manifest command churn (stay ≤ 8192 bytes).
4. Re-read OpenAI Codex release notes when bumping pinned CLI assumptions — adjust slash collision tables if new built-ins overlap Writ names.
5. Verify dry-run install output lists seven agents and correct `SKILLS_DIR` (`.agents/skills/`).

### Observability

Writ stores durable artifacts under `.writ/` (specs, logs like `refresh-log.md`, execution snapshots under `.writ/state/`). Codex’s `/feedback` command ships diagnostics to OpenAI ([slash docs](https://developers.openai.com/codex/cli/slash-commands#send-feedback-with-feedback)) — it is unrelated to Writ’s own logging discipline. When debugging a Writ-on-Codex issue, capture **both** the relevant `.writ/` files **and** the Codex `/debug-config` / `/status` output so maintainers can see CLI policy versus methodology state.

### Windows sandbox note

`/sandbox-add-read-dir` exists for Windows-only extra read roots ([slash docs](https://developers.openai.com/codex/cli/slash-commands#grant-sandbox-read-access-with-sandbox-add-read-dir)). Writ agents assume POSIX paths in examples — adjust drive-letter paths when scripting `Bash` steps on Windows hosts.

### Security posture

Writ’s `/security-audit` command remains Markdown-orchestrated; Codex’s sandbox reduces blast radius but does not replace dependency audits or secret scanning. Keep `[features] codex_hooks = false` until your team documents hook handlers — accidental auto-approval hooks have burned teams that blurred “CLI convenience” with “CI policy.”

Read-only agents (`sandbox_mode = "read-only"`) materially constrain lateral movement during architecture/review/visual QA phases — prefer tightening sandbox defaults before weakening prompts.

**Baseline reminders:**

- Never paste production secrets into agent prompts — treat transcripts as semi-public.
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
