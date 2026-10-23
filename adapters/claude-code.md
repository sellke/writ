# Claude Code Platform Adapter

Native integration with Claude Code's subagent system, git worktrees, and hooks. Writ agents are `.claude/agents/` markdown files with YAML frontmatter; no shell scripting is needed.

---

## Installation

### Automated (recommended)

```bash
bash <(curl -s https://raw.githubusercontent.com/sellke/writ/main/scripts/install.sh) --platform claude
```

This installs all commands, Claude Code–native agents (with YAML frontmatter), and `.claude/system-instructions.md` into your project, and adds the Writ block to `CLAUDE.md` between `<!-- writ:start -->` and `<!-- writ:end -->` markers. Your own text outside the markers is kept. Preview first with `--dry-run`. Update later with:

```bash
bash <(curl -s https://raw.githubusercontent.com/sellke/writ/main/scripts/update.sh) --platform claude
```

The updater uses a manifest (`.claude/.writ-manifest`) for three-way overlay merges. Files you have customized are never overwritten.

### Manual Installation

If you prefer to install manually, or need to customize the setup:

#### Step 1: Copy files and add the Writ block

```bash
mkdir -p .claude/agents .claude/commands .writ/state
cp path/to/writ/commands/*.md .claude/commands/
cp path/to/writ/claude-code/agents/*.md .claude/agents/
[ -s CLAUDE.md ] && [ -n "$(tail -c 1 CLAUDE.md)" ] && printf '\n' >> CLAUDE.md   # end the file with a newline first
{ printf '%s\n' '<!-- writ:start -->'; cat path/to/writ/claude-code/CLAUDE.md; printf '%s\n' '<!-- writ:end -->'; } >> CLAUDE.md
cp path/to/writ/system-instructions.md .claude/system-instructions.md
```

Run these lines on a first install only. They append the Writ template to `CLAUDE.md` between the markers and leave your own text in place; a missing `CLAUDE.md` is created. A manual install writes no manifest, so there is no recorded baseline for the block. A later `install.sh` or `update.sh` run therefore keeps the block whenever it differs from the current template and reports it as locally modified, even if you edited nothing. `--force` replaces only the block in `CLAUDE.md`, but it also overwrites every other Writ file that differs from upstream, customized or not. Neither script changes text outside the markers. `install.sh --platform claude` does all of Step 1 for you and writes the manifest.

`CLAUDE.md` imports `.claude/system-instructions.md` with the line `@.claude/system-instructions.md`, and Claude Code asks once to approve an import that resolves outside the working directory.

Agent source files live in `claude-code/agents/` in the Writ repo. They carry YAML frontmatter (`name`, `tools`, `model`, `permissionMode`, `isolation`, `maxTurns`, `memory`). `scripts/gen-claude-agents.py` generates every one of them from the canonical `agents/*.md` file plus a Claude frontmatter overlay; do not hand-edit them. After changing `agents/<stem>.md`, run `python3 scripts/gen-claude-agents.py`. `bash scripts/eval.sh` and `bash scripts/check-agent-parity.sh` fail when a generated file is stale, missing, orphaned, or has no overlay entry.

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
├── CLAUDE.md                          # Auto-loaded every session; Writ block between markers
├── .claude/
│   ├── system-instructions.md         # Writ root contract, imported by CLAUDE.md
│   ├── agents/                        # Native subagent definitions
│   │   ├── writ-architect.md          # isolation: worktree, plan mode
│   │   ├── writ-coder.md             # isolation: worktree, acceptEdits
│   │   ├── writ-reviewer.md          # read-only, persistent memory
│   │   ├── writ-tester.md            # acceptEdits
│   │   ├── writ-documenter.md        # inherit, acceptEdits
│   │   ├── writ-evaluator.md         # read-only, persistent memory
│   │   ├── writ-story-gen.md         # haiku model, worktree
│   │   └── writ-visual-qa.md         # read-only
│   ├── commands/                      # Writ command workflows
│   │   ├── create-spec.md
│   │   ├── implement-story.md
│   │   └── ... (all commands)
│   └── agent-memory/                  # Persistent agent memory (auto-created)
│       ├── writ-architect/
│       ├── writ-coder/
│       ├── writ-evaluator/
│       └── writ-reviewer/
└── .writ/                             # Runtime artifacts
    ├── specs/
    ├── decision-records/
    └── state/
```

### Plugin

Writ also installs as a Claude Code plugin from this repository: the marketplace file is `.claude-plugin/marketplace.json` at the repository root, and the plugin is `plugins/writ/`. `python3 scripts/gen-platform-trees.py` generates both from `commands/`, `agents/`, `skills/`, `scripts/`, `system-instructions.md`, and `VERSION`, and `--check` fails when either differs from a fresh render. Do not hand-edit them.

```bash
claude plugin marketplace add sellke/writ
claude plugin install writ@writ
```

Under the plugin, commands and agents carry the `writ` namespace and scripts run from the plugin's own `scripts/`, so the project needs no `scripts/` folder. The plugin does not include the `.writ/docs/` reference docs that `install.sh` copies. A command that cites `.writ/docs/<name>.md` reads the project's copy, and a project with only the plugin has none.

Platform facts, from the Verification Record of spec `2026-10-22-plugin-distribution`:

- **Install.** `claude plugin marketplace add` takes a GitHub `owner/repo`, and `claude plugin install <plugin>@<marketplace>` installs at user scope unless `--scope` names another (docs read 2026-10-23, https://code.claude.com/docs/en/plugins/install.md). A local-path add and install of a scratch copy of this layout worked on Claude Code 2.1.309 on 2026-10-23 (same page). The install from `sellke/writ` itself has not run yet: a GitHub-sourced plugin runs from a cache copy, not in place (docs read 2026-10-23, https://code.claude.com/docs/en/plugins/loading.md).
- **Validation.** On the generated tree, `claude plugin validate plugins/writ` exits 0 with warnings (the prompt-template docs in `agents/` have no frontmatter), and `claude plugin validate .` exits 0 with no warnings (Claude Code 2.1.309, 2026-10-23, https://code.claude.com/docs/en/plugins/cli-reference.md).
- **Namespacing.** Plugin commands run as `/writ:<command>`, so the front door is `/writ:writ`, and plugin agents are `writ:<agent>`, for example `writ:writ-coder` (Claude Code 2.1.309, 2026-10-23, https://code.claude.com/docs/en/plugins/components.md). The generated commands spell every cross-reference this way.
- **Scripts.** Claude Code substitutes `${CLAUDE_PLUGIN_ROOT}` in command, skill, and agent bodies but not in the Bash tool's environment, so the generated commands spell `python3 ${CLAUDE_PLUGIN_ROOT}/scripts/<name>.py` inline (docs read 2026-10-23, https://code.claude.com/docs/en/plugins/manifest-reference.md).
- **Prime Directive carrier.** `plugins/writ/output-styles/writ.md` with `force-for-plugin: true` and `keep-coding-instructions: true`; its body is the body of `system-instructions.md`. Observed on Claude Code 2.1.309 on 2026-10-23 in a scratch plugin: asked to quote the first Hard Constraints bullet, the session quoted it and named the Prime Directive as its source, and it named its persona Writ; with no carrier it answered `NONE` (https://code.claude.com/docs/en/output-styles.md).
- **Carrier cost: your output style.** A forced style overrides your `outputStyle` while the plugin is enabled, and when another enabled plugin also forces a style, the first loaded wins (docs read 2026-10-23, https://code.claude.com/docs/en/output-styles.md).
- **Carrier cost: subagents.** Output styles reach the main conversation and forks, not other subagents, so each Writ agent carries its own instructions in its body (docs read 2026-10-23, https://code.claude.com/docs/en/output-styles.md).
- **Ignored agent keys.** Plugin agents ignore `permissionMode`, `hooks`, and `mcpServers`, and the field table marks `initialPrompt` ignored as well (docs read 2026-10-23, https://code.claude.com/docs/en/sub-agents.md). All eight Writ agents set `permissionMode`, so the modes in [Permission Modes](#permission-modes) do not apply under the plugin; no Writ agent sets the other three. `isolation: worktree` and `memory: project` took effect in a scratch plugin agent on Claude Code 2.1.309 on 2026-10-23 (same page).
- **Both installs in one project.** A project with an `install.sh` install and the plugin has both command sets, `/create-spec` from `.claude/commands/` and `/writ:create-spec` from the plugin, and a project command does not shadow the plugin command of the same name (Claude Code 2.1.309, 2026-10-23, https://code.claude.com/docs/en/plugins/components.md). Plugin agents rank lowest among same-named agents, but their names carry the `writ:` prefix, so `writ-coder` is the project's agent and `writ:writ-coder` the plugin's (docs read 2026-10-23, https://code.claude.com/docs/en/sub-agents.md). Writ commands spawn agents from the prompt templates in `agents/`, not by name. Use one install path per project.

---

## Key Features Used

### Git Worktree Isolation (`isolation: worktree`)

When a subagent has `isolation: worktree`, Claude Code:
1. Creates a temporary git worktree for it. The worktree branches from the repository's default branch unless `worktree.baseRef` is `"head"`, which branches from your current local `HEAD`.
2. Runs the subagent in that worktree, so parallel agents do not edit the same files.
3. Removes the worktree when the subagent finishes with no changes.
4. Otherwise, the worktree stays on disk holding the changes until a periodic sweep can remove it without losing work. Nothing copies the changes into your checkout.

The orchestrator reconciles those changes by following the [worktree integration skill](../skills/subagent-worktree-integration/SKILL.md): diff the worktree against its own checkout, copy the changed files, re-verify in its own checkout, then remove the worktree. Source: [Claude Code worktrees docs](https://code.claude.com/docs/en/worktrees), § Isolate subagents with worktrees.

**Writ agents using worktrees:**
- `writ-architect` — reads codebase without interfering
- `writ-coder` — implements in isolation, no conflicts with parallel stories
- `writ-story-gen` — generates story files in parallel without conflicts

**Parallel stories:** `/implement-spec` runs independent stories in parallel batches, and each `/implement-story` reconciles its agents' worktrees per the skill before it trusts their output.

### Persistent Memory (`memory: project`)

Agents learn across sessions. The review agent remembers patterns it's seen, the architect remembers architectural decisions, the coder remembers conventions.

```
.claude/agent-memory/
├── writ-architect/MEMORY.md    # "This project uses repository pattern for data access"
├── writ-coder/MEMORY.md        # "Tests use vitest with MSW for API mocking"
└── writ-reviewer/MEMORY.md     # "Previous review caught SQL injection in routes/search.ts"
```

### Model Selection

The eight Claude-native agents under `claude-code/agents/` (`writ-architect`, `writ-coder`, `writ-evaluator`, `writ-reviewer`, `writ-tester`, `writ-documenter`, `writ-story-gen`, `writ-visual-qa`) carry their `model_tier` ([ADR-024](../.writ/decision-records/adr-024-model-delegation.md); contract text in `system-instructions.md` § Model Tiers) as a static `model:` frontmatter value, set in the `scripts/gen-claude-agents.py` overlay. The table resolves the tiers:

| Origin source | `anchor` | `floor` | escalation |
|---|---|---|---|
| `anchor.model` = the model Claude Code reports for the session; `anchor.effort` = `unknown` unless an effort setting is present in `.claude/settings*.json`; `anchor.platform = claude-code` | `model: inherit` | `model: haiku`. `haiku` is the family bottom, so it is at or below any Claude origin; static frontmatter can carry it without a runtime `min(haiku, origin)` check. If `haiku` is unavailable on the install: `model: inherit` + `effort: low`. | `model: inherit` |

**Degradation:** an unrecognized `model_tier`, or a family alias the install cannot resolve (verify `haiku`/`inherit` still resolve if your Claude Code version's defaults drift), warns and falls back to `inherit`. Never hard-fail the spawn. A Claude origin already at `haiku` means `floor` collapses to `anchor`, said once, no `degraded`.

| Agent | `model_tier` | `model:` |
|-------|------|------|
| writ-architect | `floor` | `haiku` |
| writ-story-gen | `floor` | `haiku` |
| writ-coder | `anchor` | `inherit` |
| writ-evaluator | `anchor` | `inherit` |
| writ-reviewer | `anchor` | `inherit` |
| writ-tester | `anchor` | `inherit` |
| writ-documenter | `anchor` | `inherit` |
| writ-visual-qa | `anchor` | `inherit` |

`sonnet` is gone from `writ-tester` and `writ-documenter`: both are `anchor`, and a fixed `sonnet` would exceed a `haiku` origin. `inherit` is the only anchor value that respects the ceiling.

**Review panel (ADR-028): unavailable.** Subagent `model` accepts Anthropic aliases, full Anthropic IDs, or `inherit`, so no other vendor can be spawned. Gate 3 runs as today; `review-panel.py status --platform claude-code` prints the skip.

### Permission Modes

| Agent | Mode | Why |
|-------|------|-----|
| writ-architect | `plan` | Read-only analysis, no modifications |
| writ-coder | `acceptEdits` | Auto-accept file changes (TDD flow) |
| writ-evaluator | `plan` | Read-only evaluation, cannot modify |
| writ-reviewer | `plan` | Read-only review, cannot modify |
| writ-tester | `acceptEdits` | May need to fix tests |
| writ-documenter | `acceptEdits` | Creates/updates doc files |
| writ-story-gen | `acceptEdits` | Creates story files |
| writ-visual-qa | `plan` | Read-only visual checks, cannot modify |

---

## Native Memory & the Writ Ledger

> **Native memory holds session preferences and trivia; the Writ ledger holds negotiated decisions, conventions, and lessons — the reviewable markdown layer that feeds native memory and any external index.**

On Claude Code, native memory is **`CLAUDE.md`** (auto-loaded into every session) plus **`.claude/agent-memory/`** (the per-agent `MEMORY.md` files where the architect, coder, and reviewer accumulate what they have learned). Let `CLAUDE.md` carry stable project preferences and let agent memory hold cross-session working notes. When a decision, convention, or lesson is negotiated and needs to outlive one machine's memory store, write it to the ledger under `.writ/decision-records/` or `.writ/knowledge/`, the layer a teammate reviews in a PR.

**Anti-pattern:** negotiated decisions that live only in native memory are unreviewable and are lost on a reinstall, a new machine, or a teammate who never had your store. Write the decision, the convention, or the lesson to the ledger, and let native memory keep only the ephemeral trivia.

**Three layers, one system of record:** native memory (session prefs/trivia, per platform) → the Writ ledger (canonical, reviewable markdown in git) → an optional external index (GBrain, disposable). [`.writ/docs/gbrain-recipe.md`](../.writ/docs/gbrain-recipe.md) covers the external-index layer. Removing that index loses nothing; the ledger is the only copy.

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
| `todo_write` | `TodoWrite` | Native todo list; phases mirror here |
| `read_file` | `Read(path)` | Direct equivalent |
| `run_terminal_cmd` | `Bash(command)` | Direct equivalent |
| `list_dir` | `Glob("dir/*")` or `Bash("ls")` | Built-in Glob tool |
| `canvas-preview` | An artifact, or the preview pane | One self-contained HTML page per draft. No renderer: write a structural description of each draft and say the drafts were not rendered. |
| `Plan Mode` | `EnterPlanMode`; present the contract proposal as the plan; after `ExitPlanMode` approval, lock with AskQuestion | If the platform has no toggle, say so and proceed read-only. |

#### Verification record — 2026-10-22

| Check | Platform & version | Observed | Source | Status |
|---|---|---|---|---|
| Publish one self-contained HTML draft as an artifact | Claude Code 2.1.308 (`claude --version`), desktop app session (Browser pane tools present) | The `Artifact` tool published `draft-a.html` (inline CSS, no network fetch, one labeled region per component) from the session scratchpad to a private claude.ai URL as version 1. Reading the URL back returned the page inside the viewer's document shell, and the Browser pane rendered the URL in the artifact viewer with all four labeled regions visible. | https://code.claude.com/docs/en/artifacts | verified 2026-10-22 |
| Open the same draft in the preview (Browser) pane | Claude Code 2.1.308 (`claude --version`), desktop app session (Browser pane tools present) | `navigate` to the `file://` path opened the draft in the pane as a static snapshot; a screenshot of the local-file tab was refused, so that render was not inspected. Served from the scratchpad over `http://127.0.0.1` by a static file server, `navigate` rendered the page and a screenshot showed all four labeled regions. | https://code.claude.com/docs/en/desktop#preview-your-app | verified 2026-10-22 |
| Native design surface reachable from a command run | Claude Code 2.1.308 (`claude --version`), desktop app session (Browser pane tools present) | The `Artifact` tool's read-only `quickstart` (intent `design`) listed the Claude Design type with a `type_url` and said to publish to that URL to start a canvas. Listed and addressable from inside the run without the user typing the native `/design` command; nothing was published and no canvas was created. | https://code.claude.com/docs/en/artifacts#draft-a-design-canvas | verified 2026-10-22 |
| Headless run (`claude -p`): no-renderer path | Claude Code 2.1.308 (`claude --version`), desktop app session; `-p` not run, docs read 2026-10-22 | Not exercised in this run. The docs list `-p` from a terminal or script among the contexts where artifacts are off by default, so a headless `/prototype` run takes the row's no-renderer clause. | https://code.claude.com/docs/en/artifacts#availability | unverified 2026-10-22 |

### Agent Paths

Commands name agents by canonical path, as in `> **Agent:** agents/coding-agent.md`. On Claude Code, each path resolves to the generated subagent file:

| Command reference | Claude Code agent file |
|---|---|
| `agents/architecture-check-agent.md` | `.claude/agents/writ-architect.md` |
| `agents/coding-agent.md` | `.claude/agents/writ-coder.md` |
| `agents/documentation-agent.md` | `.claude/agents/writ-documenter.md` |
| `agents/evaluator-agent.md` | `.claude/agents/writ-evaluator.md` |
| `agents/review-agent.md` | `.claude/agents/writ-reviewer.md` |
| `agents/testing-agent.md` | `.claude/agents/writ-tester.md` |
| `agents/user-story-generator.md` | `.claude/agents/writ-story-gen.md` |
| `agents/visual-qa-agent.md` | `.claude/agents/writ-visual-qa.md` |

Spawn the `writ-*` agent by name. Its body is the canonical file's body, so the instructions match.

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

### implement-story --full-pipeline: Single Story

Default `/implement-story` is `writ-coder` + `writ-evaluator` plus scripts. The six-agent hatch is `--full-pipeline`:

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
# Each story file stays in its worktree until the orchestrator copies it back
```

The orchestrator copies each story file back per the [worktree integration skill](../skills/subagent-worktree-integration/SKILL.md) before it reads or commits the file.

### Quality Gates with Hooks

A `SubagentStop` hook runs when a subagent finishes. This one runs the checks when `writ-coder` stops:

```json
// .claude/settings.json
{
  "hooks": {
    "SubagentStop": [
      {
        "matcher": "^writ-coder$",
        "hooks": [{ "type": "command", "command": "\"$CLAUDE_PROJECT_DIR\"/.claude/hooks/writ-coder-checks.sh" }]
      }
    ]
  }
}
```

```bash
#!/usr/bin/env bash
# .claude/hooks/writ-coder-checks.sh: reads the hook input JSON on stdin.
dir=$(python3 -c 'import json, sys; print(json.load(sys.stdin)["cwd"])')
cd "$dir" || exit 0
npm test && npx tsc --noEmit && exit 0
echo "Tests or typecheck failed. Fix them before you stop." >&2
exit 2
```

Facts from the [Claude Code hooks docs](https://code.claude.com/docs/en/hooks) (§ SubagentStart, § SubagentStop):

- The `SubagentStop` matcher is the agent type. For a custom subagent, that is its frontmatter `name`, so `^writ-coder$` matches only `writ-coder`.
- Exit code 2 keeps the subagent running and gives it the stderr text.
- The hook input JSON carries `cwd`. The docs do not say whether `cwd` is a worktree-isolated subagent's worktree, so the orchestrator re-runs the checks in its own checkout after it reconciles the worktree (step 4 of the [worktree integration skill](../skills/subagent-worktree-integration/SKILL.md)).

### The /goal Stop Hook

Claude Code's `/goal <condition>` registers a session-scoped prompt-type Stop hook: on every stop attempt an evaluator judges the condition met / not-met+reason / impossible+reason, and not-met forces the run to continue. It is the same native hook mechanism as the `SubagentStop` example above, aimed at `scripts/exit-criteria.py check`. See `.writ/specs/archive/2026-08-12-machine-evaluable-exit-criteria/spec.md` § "What `/goal` showed, and why it is not the answer" for the case against treating `/goal` itself as the mechanism.

**The checker is the authority; `/goal` is only the delivery vehicle.** Story 5's command wiring makes `exit-criteria.py check` the independent, read-only re-derivation that `implement-phase` and `implement-spec` defer to in their completion steps. The `/goal` condition below likewise asks the checker and relays the verdict without restating or reinterpreting it. Never write a `/goal` condition that encodes its own pass/fail logic.

Register one goal at the outermost running command (`/implement-phase` or `/implement-spec`), with a condition that is satisfiable by pausing as well as by finishing (spec.md Business Rule 1: "Reaching a retained pause satisfies the gate"). A condition that only accepts a clean checker pass pushes the model past a human gate; spec.md's "What `/goal` showed" section documents `/goal`'s own injected prompt ("do not pause to ask the user what to do") causing this.

**Paste the emitter's printed invoke line unchanged.** After `/create-goal` saves a `loop: yes` card, or `/implement-phase` resolves a Goal Card origin, `python3 scripts/goal-emit.py emit --card PATH` prints the `/goal` text between its `pass` line and its summary. Paste that printed text as-is. It must match the three-way template below; do not rewrite clauses (a)/(b)/(c).

Word the condition as an explicit three-way disjunction:

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

1. **Stale worktrees can overwrite newer work**: By default a subagent worktree branches from the repository's default branch on the remote (usually `main`). It then lacks every commit on your current branch that is not on that branch, unpushed commits included, even ones made before the worktree was created. With `worktree.baseRef: "head"` it branches from your local `HEAD`, but it still lacks commits that land after it was created. Copying its files back as they are can overwrite that newer work in the orchestrator's checkout. Diff before you copy, and follow step 6 of the [worktree integration skill](../skills/subagent-worktree-integration/SKILL.md#6-recognize-and-resolve-a-stale-worktree).

2. **Memory bootstrapping**: Agent memory starts empty. First few runs will be less effective. Ask agents explicitly to "update your memory with patterns you discover."

3. **Haiku for story-gen is the floor, not a knob**: `writ-story-gen` carries `model: haiku` because it is a `floor` agent under ADR-024 (templated output the user reviews before lock). Do not change it to a fixed `model: sonnet` — the anchor is the ceiling, and a fixed `sonnet` exceeds a `haiku` origin (see the tier table above). If a generated story fails validation, `/create-spec` Step 2.6a already re-runs it once at `anchor` (`inherit`); that escalate-once path is the quality lever.

4. **Subagents nest**: three-deep nesting is observed in practice (`/implement-phase` → spec-runner → `/implement-story` → gate agents). `/goal` does not nest: see **Single-slot behavior** under *The /goal Stop Hook* above. Only the outermost running command may hold one.

5. **Plan mode is read-only**: `permissionMode: plan` blocks all writes at the tool level. The architect and reviewer cannot modify files, even if prompted to.

## Model-specific

Claude Fable 5.1 may serialize independent tool calls: issue independent reads, searches, and checks as one batched message, not one at a time (the only model-specific line this adapter carries — ADR-026; see ADR-024 for delegation).
