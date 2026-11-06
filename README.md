<div align="center">
<pre>
/\/\/\/\/\/\/\/\/\/\/\/\/\/\/\/\/\/\/\/\
  ██╗    ██╗██████╗ <span style="color: #FF9900;">  ██╗    </span>████████╗  
  ██║    ██║██╔══██╗<span style="color: #FF9900;">  ╚██╗   </span>╚══██╔══╝  
  ██║ █╗ ██║██████╔╝<span style="color: #FF9900;"> ██████╗ </span>   ██║     
  ██║███╗██║██╔══██╗<span style="color: #FF9900;"> ╚══██╔╝ </span>   ██║     
  ╚███╔███╔╝██║  ██║<span style="color: #FF9900;">   ██╔╝  </span>   ██║     
   ╚══╝╚══╝ ╚═╝  ╚═╝<span style="color: #FF9900;">   ╚═╝   </span>   ╚═╝     
\/\/\/\/\/\/\/\/\/\/\/\/\/\/\/\/\/\/\/\/
</pre>

**AI-powered development workflow framework**<br>
Contract-first specs · Script-backed gates · Evidence-gated review · One front door

⚡ *A writ is a written command by an authority--you. The framework executes them.*

</div>

---

## What is Writ?

Writ is a self-improving development methodology that turns rough ideas into shipped code through a disciplined pipeline:

```
/plan-product → /create-spec → /assess-spec → /implement-phase (or /implement-spec) → /review → /ship → /release
```

Each stage is a markdown command file that AI agents follow precisely. The framework is **platform-agnostic** — it runs in Cursor, Claude Code, or any AI coding assistant that can read markdown. Commands lead with opinionated recommendations, challenge premises, and improve through use.

The deeper goal: **code and methodology that doesn't degrade as projects, teams, and AI platforms churn around them.** Specs, decisions, and accumulated knowledge live as plain-text markdown in git — designed to survive any tooling shift.

Writ owns three things and delegates or deletes the rest ([ADR-030](.writ/decision-records/adr-030-contract-verifier-boundary-front-door.md)): the **contract** (the spec, its acceptance and exit criteria, and the stakes of each decision), the **verifier** (scripts that re-derive verdicts about the code and the running app, not only about Writ's own artifacts), and the **boundary** (when an agent stops and asks a person). Users reach all three through one front door, `/writ`.

## Three Primitives — Verb / Noun / Tool

Writ has three first-class building blocks. Each plays a distinct role and the boundary between them is enforced by tooling, not just discipline.

| Primitive | Grammar | What it is | Example |
|---|---|---|---|
| **Command** | Verb | A user-invoked workflow with phases and durable artifacts | `/create-spec`, `/implement-spec`, `/release` |
| **Agent** | Noun | A role with inherent behavior, spawned by a command for a phase | `coding-agent`, `evaluator-agent`, `review-agent` |
| **Skill** | Tool | A reusable capability — *how to do a specific thing well* | `conventional-commits`, `tdd-cycle`, `safe-refactor-loop` |

> Workflow → command. Role → agent. Capability → skill.

Composition is acyclic: commands spawn agents; commands and agents wield skills; skills don't call commands or chain other skills. See [`.writ/docs/skills.md`](.writ/docs/skills.md) for the full skills explainer and [ADR-009](.writ/decision-records/adr-009-command-agent-skill-boundary.md) for the rationale. The skills foundation shipped in `2026-05-03-skills-foundation`; 19 skills are live today (see [Skills](#skills) below), each carrying a candidate → proven → promoted lifecycle.

## Key Features

- **Contract-first specifications** — No code until requirements are agreed upon
- **Two-agent default, six-agent escalation** — `/implement-story` ships with a coding agent and a fresh-context evaluator. Architecture-check, review, testing, visual QA, and documentation spawn only on `--full-pipeline` (or after two consecutive evaluator FAILs); a story that crosses its boundary map gets the review agent instead of the evaluator. The default path is two Task spawns.
- **Script-backed quality gates** — Default `/implement-story` re-derives architecture, boundary, architecture-lint, review-override, test-integrity, drift format, and docs verdicts from `scripts/*.py`. Gate 1 (coding) and Gate 4.5 declare `prose-only`; when the project has a verification recipe (`.writ/docs/app-verification.md`), Gate 4.5's verdict comes from `scripts/app-verify.py` driving the running app. **Eval Tier 1** (`scripts/eval.sh`, enforced via GitHub Actions on every PR) adds required-section validation, broken-reference detection, length sanity, and anti-sycophancy phrase scanning across `.writ/` artifacts.
- **Evidence-gated review** — A Gate 3 or `/review` finding blocks only when it carries executed evidence: a failing test the reviewer wrote, a recorded failure, a static check, or a resolved source-to-sink path. `scripts/review-override.py evidence` runs it, and a confirmed repro is committed as a regression test ([ADR-032](.writ/decision-records/adr-032-evidence-gated-review.md)).
- **Rigor about the code, not only the artifacts** — On the review route, Gate 2.5 names the one fact a change is safe because of and the evidence rung it reached (floor: `tested`). Bug fixes commit a failing repro before the fix, and `scripts/repro-order.py` checks the order. Reviewers carry lead-judgment filters.
- **`/why` from the ledger** — Answers why code is the way it is from ADRs, drift logs, specs, What Was Built records, and git notes first, then git history, then connected MCP servers, with a confidence tier on every claim.
- **Spec assessment** — `/assess-spec` flags sizing, complexity, and context accumulation risks before you build. Recommends specific decomposition strategies. Runs automatically as a pre-flight check in `/implement-spec`.
- **Machine-evaluable exit criteria** — `scripts/exit-criteria.py` is a read-only checker that re-derives `met`/`unmet`/`unknown`/`impossible` for each `/implement-phase` and `/implement-spec` exit criterion from state on disk, instead of trusting the run's own self-report (`/implement-story`'s criteria are out of scope — already disk-checkable from the story file itself). Its verdict governs completion reports and (on Claude Code) the `/goal` Stop hook.
- **Cross-story continuity** — "What Was Built" records capture implementation reality from review outputs and automatically pass to downstream stories, so integration code matches what was actually built, not just what was planned
- **Knowledge accumulation** — `.writ/knowledge/` is a markdown ledger for cross-cutting decisions, conventions, glossary, and lessons. Capture with `/knowledge`; agents auto-load relevant entries at task start so context survives context-window resets and machine changes.
- **Deterministic context assembly** — `/implement-story`'s context-hint resolution runs through one script (`scripts/story-context.py`) instead of three drifting prose/code implementations, with an empirically derived `fetched_context` budget (21,000 bytes) that truncates by relevance and warns rather than loading unbounded context
- **Parallel execution** — Independent stories run simultaneously with dependency resolution
- **Opinionated guidance** — Commands lead with recommendations, challenge premises, and push for the best version of every idea
- **Self-improving** — `/refresh-command` turns session friction into cited command diffs. Every refinement carries transcript evidence and must pass an eval gate to merge. Commands get better through use. `/retro` reads a run's transcripts and proposes fixes to the agent's environment in a fixed order — architecture, types, lint, test, docs — and each new check must fail on a real past mistake.
- **Initiative, asked only on doubt** — Every question a command would ask is a decision. `scripts/jev-judge.py doubt` decides it from three signals: the evidence behind the recommended option, whether the act is git-revertable, and Jev's calibrated confidence that the recommendation is right. A pass acts and logs; anything else asks one bounded question. Without a calibrated judgment, scope and taste questions still reach you and method choices do not. Release, tag, and publish always wait for you. A merge waits too unless `pr-ready.py` passes for the PR's exact head with the ledger VERIFIED and the doubt check passes. Every decision lands in `.writ/state/doubt-log.jsonl`; your answers become labels that `doubt-calibrate` fits from, and a threshold is written only when at most 10% of the decisions Jev would act on are ones you would have overridden, at a 95% upper bound ([ADR-033](.writ/decision-records/adr-033-doubt-gated-autonomy.md)).
- **A supervisor over subagent work** — Before `/implement-spec` accepts a story or `/implement-phase` merges a lane, a fresh-context `supervisor-agent` re-derives each claim in the report from git, the spec's files, and Writ's checkers, and returns ACCEPT, RERUN, or ESCALATE with a claims table.
- **Optional judgment provider** — TypeSafe's Jev model (direct or via the Vercel AI Gateway) can pre-judge acceptance criteria during `/create-spec` and `/verify-spec` spec analysis, and logs a shadow verdict beside the Gate 3 evaluator. It is off by default and requires a double opt-in: a `Judgment Provider` line in `.writ/config.md` *and* the backend's API key. Below its calibrated threshold, an answer falls back to the normal path; no Jev answer decides a gate or skips a spawn ([ADR-027](.writ/decision-records/adr-027-optional-judgment-provider.md)). Set it up with `python3 scripts/jev-judge.py setup`.
- **Native-memory interop** — markdown stays canonical while adapters document how to ride each platform's native memory; external knowledge indexes (e.g., GBrain via MCP) are consumers
- **Platform adapters** — Native support for Cursor, Claude Code, and Codex CLI, plus an OpenClaw mapping guide

## Pipeline

```
┌──────────┐   ┌─────────────┐   ┌─────────────┐   ┌─────────────────┐   ┌──────────┐   ┌──────────┐   ┌─────────┐
│  plan-   │──▶│  create-    │──▶│  assess-    │──▶│  implement-     │──▶│  review  │──▶│  ship    │──▶│ release │
│  product │   │  spec       │   │  spec       │   │  spec           │   │ (opt.)   │   │          │   │         │
└──────────┘   └─────────────┘   └─────────────┘   └─────────────────┘   └──────────┘   └──────────┘   └─────────┘
                     │              Sizing checks       │                    │              │
               Error mapping     Context budget    Parallel batches   Failure modes   Merge → Test
               Shadow paths      Decomposition     Dependency graph   Shadow paths    Split commits
               Edge cases        recommendations         │            Edge cases      Open PR
                                                    Per story (/implement-story) — default:
                              ┌─ Arch-check script (no architecture-check agent)
                              ├─ Boundary map (Gate 0.5)
                              ├─ Coding agent (TDD; a bug fix commits its failing repro first)
                              ├─ Lint / build-smoke
                              ├─ Safety fact (Gate 2.5, review route: one fact, evidence rung ≥ tested)
                              ├─ Evaluator agent (fresh-context rubric) — a finding blocks only on executed evidence
                              ├─ Drift (Small → auto-amend spec-lite)
                              ├─ test-integrity.py (no testing agent)
                              ├─ app-verify.py (Gate 4.5, when the project has a verification recipe)
                              └─ docs-check.py (no documentation agent)
                         --full-pipeline adds architecture-check, review, testing,
                         visual QA, and documentation agents. Two consecutive
                         evaluator FAILs escalate the rest of that story.

Lightweight path (/prototype) — no spec required:
   Describe change → [Visual Preview] → Coding Agent (TDD) → Lint → Done
                                              ↑ complexity? → escalate to /create-spec

Phase path (/implement-phase — roadmap-driven, supervised):
   /plan-product → /implement-phase N → /create-uat-plan (per spec, auto) → UAT (machine where a recipe exists, a person where none can) → /ship
                        ↑ loops /implement-spec per spec, sequences by cross-spec dependency,
                          fresh isolated lane per spec, quarantine on failure, resume-safe

Feedback loop (/retro + /refresh-command):
   Run transcripts → Struggle findings → Environment fixes    |    Friction → Command diffs
```

## Commands

### Start here
| Command | Purpose |
|---------|---------|
| `/writ` | **The front door.** Restates a request as a goal, a problem, and a done check, routes it to the command whose ceremony fits, confirms only when the route is in doubt, and runs it with its phases on the todo list. |

### Planning & Specification
| Command | Purpose |
|---------|---------|
| `/plan-product` | Product planning with contract-first approach |
| `/create-spec` | Feature specification with structured clarification. After stories exist, `spec-analyze.py` notes contradictory, missing, or ambiguous criteria (advisory; Jev pre-judges first when enabled). Authors from evidence when the source settles intent, and runs discovery only while it is open; the lock reaches you on doubt. It stops at the locked package and never implements. |
| `/edit-spec` | Safely modify existing specifications |
| `/writ-design` | Visual design companion — wireframes, mockup management, screenshot capture, visual comparison |
| `/create-adr` | Architecture Decision Records (auto-researches first) |
| `/create-goal` | Goal Card for a recurring task: checkable finish line, stages, stop caps, or a recorded "don't loop this" verdict. A `loop: yes` save emits `GOAL.md` / `VERIFY.md` plus a printed Claude Code goal-mode invoke line (never registers the hook). |
| `/create-issue` | Quick issue capture (<2 minutes) |
| `/knowledge` | Capture durable project knowledge (decisions, conventions, glossary, lessons) into `.writ/knowledge/` |
| `/research` | Systematic 4-phase research workflow |
| `/why` | Answers why code is the way it is from the ledger, git history, and MCP servers, with a confidence tier on every claim; when a change follows, ends with a Preserve / Change / Avoid / Risk list `/create-spec` reads |

### Implementation & Quality
| Command | Purpose |
|---------|---------|
| `/prototype` | **Lightweight executor.** No spec needed — describe the change, answer 2-3 questions, ship with TDD + lint. Auto-detects when to escalate to `/create-spec`. |
| `/implement-phase` | **Phase orchestrator.** Reads a roadmap phase, resolves features to specs, sequences by dependency, loops `/implement-spec` → `/create-uat-plan` per spec, and verifies exit criteria. The layer above `/implement-spec`. Runs the phase end to end, asking only on doubt; a supervisor checks each lane's report before it merges. Ends at the completion report with the UAT handoff. |
| `/implement-spec` | **Spec orchestrator.** Reads a spec, validates the story dependency graph (blocking gate — cycles, missing/duplicate/self references), resolves parallel batches, calls `/implement-story` per story. End-to-end uninterrupted execution. |
| `/implement-story` | **Per-story executor.** Default: arch-check script → boundary map → coding (TDD) → lint → evaluator → drift → test-integrity → docs-check (two Task spawns). `--full-pipeline` is the six-agent SDLC. `--quick` is coding only. `--review-only` is evaluator only. |
| `/refactor` | Scoped refactoring — file analysis, deduplication, dead code removal, pattern modernization, type strengthening. Verified after every change. |
| `/revert` | **Logical-unit revert.** Unwinds a story or spec via a layered commit resolver (recorded SHA → `/ship` footer → phase-state → confirmed ghost match), safe `git revert` by default (hard reset behind a second confirmation), then restores story status, WWB, drift-log, and `context.md`. |
| `/status` | Comprehensive project status report, including a one-line production-grade health score |

### Shipping & Review
| Command | Purpose |
|---------|---------|
| `/review` | **Pre-landing code review.** Error & rescue maps, shadow path tracing, interaction edge cases, failure modes registry, mandatory architecture diagrams. Produces judgment, not checklists. With the Evidence Gate on, it asks before running the branch's tests. After the run, a Critical or High finding that no failing test or cited input-to-sink path confirms reads `Medium (unconfirmed)`. |
| `/ship` | **Unified shipping workflow.** Detect conventions → merge default branch → (optional `/ship --test`) → split commits → create PR with structured body, optional inline spec health, and auto-labels. |

### Validation & Release
| Command | Purpose |
|---------|---------|
| `/assess-spec` | **Pre-implementation health check.** Flags oversized stories, deep dependency chains, context accumulation risks, and file-overlap conflicts. Recommends specific decomposition strategies. Also runs as a pre-flight check inside `/implement-spec`. |
| `/verify-spec` | Metadata diagnostic (checks 1–8): story/README integrity, completion, dependencies, deliverables, contract drift, spec-lite integrity, owner field. Check 3g runs `spec-analyze.py` as notes (Jev first when enabled). Auto-fix by default; optional standalone pass. |
| `/create-uat-plan` | **UAT plan generation.** Reads completed stories and generates human-readable test scenarios from acceptance criteria, error maps, shadow paths, and edge cases. Enriches with "What Was Built" details. |
| `/security-audit` | Full security audit: dependencies, secrets, code analysis, infrastructure |
| `/release` | Inline release gate (spec checks, build probes, conditional test suite) → changelog, version bump, git tag, GitHub release. Also silently auto-archives the spec behind a just-merged PR, once resolved unambiguously. |

### Feedback & Learning
| Command | Purpose |
|---------|---------|
| `/retro` | **Transcript review.** Reads agent transcripts from a story, spec, phase, or session; ranks struggle findings by severity, each cited to a transcript; proposes fixes to the agent environment (steering files, rules, skills, docs), never the code. Routes command changes to `/refresh-command`. |
| `/refresh-command` | **Learning loop.** Turns session friction into cited command diffs — each refinement cites transcript evidence and passes an eval gate before it merges; unevidenced proposals are visibly rejected. Commands get better through use. |

### Setup & Lifecycle
| Command | Purpose |
|---------|---------|
| `/initialize` | Project setup (greenfield/brownfield detection) |
| `/new-command` | Create new Writ commands |
| `/new-skill` | Scaffold new skills with the role convention enforced via boundary lint |
| `/migrate` | Code Captain → Writ migration (preserves specs, stories, ADRs) |
| `/update-writ` | Interactive update — pull latest, per-file control over customized files |
| `/reinstall-writ` | Clean slate — remove all Writ files and install fresh from upstream |
| `/uninstall-writ` | Remove Writ platform files and the shipped scripts and `.writ/docs/` files you left unchanged. Keeps the rest of `.writ/`, files you changed, and the `.gitignore` lines that protect `.writ/` |

## Agents

Default `/implement-story` spawns two of these. The orchestrators add the supervisor once per story or lane. The rest run on `--full-pipeline`. Each declares a `model_tier` (`anchor` or `floor`) in its Agent Configuration block, derived by two questions and resolved by the platform adapter at spawn — see [`.writ/docs/model-tiers.md`](.writ/docs/model-tiers.md) for the full convention.

| Agent | Role | Default spawn |
|-------|------|---------------|
| Coding Agent | TDD implementation — tests first, then code | yes |
| Evaluator Agent | Fresh-context rubric over acceptance criteria and recorded test results (read-only) | yes |
| Architecture Check | Pre-implementation design review (PROCEED/CAUTION/ABORT) | `--full-pipeline` |
| Review Agent | Code quality + security gate + spec drift analysis (PASS/FAIL/PAUSE, max 3 iterations) | `--full-pipeline`, or in place of the evaluator when a story crosses its boundary map |
| Testing Agent | Test execution + coverage enforcement (≥80% on new code) | `--full-pipeline` |
| Documentation Agent | Framework-adaptive docs (VitePress, Docusaurus, README, etc.) | `--full-pipeline` |
| Visual QA | Optional UI validation — compares implementation screenshots against mockups | `--full-pipeline` |
| User Story Generator | Parallel story file creation during `/create-spec` | `/create-spec` |
| Supervisor | Re-derives each claim in a subagent's report before it is accepted (ACCEPT/RERUN/ESCALATE, read-only) | `/implement-spec` per story, `/implement-phase` per lane |

## Skills

Reusable capabilities — tools any command or agent can `Read` and apply at the right moment:

| Skill | Capability |
|-------|------------|
| [`conventional-commits`](skills/conventional-commits/SKILL.md) | Author Conventional Commits messages from a diff (type, scope, summary, body, footers) — matches the project's existing convention when one exists |
| [`tdd-cycle`](skills/tdd-cycle/SKILL.md) | Grow code test-first through the red → green → refactor cycle, one small unit of behavior at a time |
| [`safe-refactor-loop`](skills/safe-refactor-loop/SKILL.md) | Change code structure without changing behavior — one verified, independently revertable commit per concern under a continuously green baseline |
| [`error-rescue-mapping`](skills/error-rescue-mapping/SKILL.md) | Map a data-flow feature's failure modes into Error & Rescue, Shadow Path, and edge-case tables |
| [`code-explanation`](skills/code-explanation/SKILL.md) | Explain existing code — purpose, mechanics, context, complexity — at a depth proportional to the target |
| [`boundary-map-computation`](skills/boundary-map-computation/SKILL.md) | Compute an owned / readable / out-of-scope file ownership map from tasks, imports, and overlap data |
| [`change-surface-classification`](skills/change-surface-classification/SKILL.md) | Classify a change set as style-only, single-component, cross-component, or full-stack |
| [`dependency-context-loading`](skills/dependency-context-loading/SKILL.md) | Load, filter, and truncate upstream stories' implementation records into dependency context |
| [`drift-triage`](skills/drift-triage/SKILL.md) | Triage implementation deviations by severity and route each to amend, warn, or pause |
| [`evidence-gated-findings`](skills/evidence-gated-findings/SKILL.md) | Back a Critical or Major review finding with evidence a script can run or check, so the finding can block a verdict |
| [`project-context-snapshot`](skills/project-context-snapshot/SKILL.md) | Regenerate a whole-file project context snapshot from product, spec, drift, and issue sources |
| [`story-commit-provenance`](skills/story-commit-provenance/SKILL.md) | Record a completion commit SHA into a story file header idempotently and without amending it |
| [`story-context-assembly`](skills/story-context-assembly/SKILL.md) | Assemble the targeted context payload each pipeline agent receives — parsed hints, knowledge entries, and role-specific spec-lite sections |
| [`what-was-built-authoring`](skills/what-was-built-authoring/SKILL.md) | Extract implementation facts from agent output and format them into a What Was Built record |
| [`subagent-result-completeness`](skills/subagent-result-completeness/SKILL.md) | Tell a spawned gate agent's complete verdict apart from a mid-task stop, and recover when it stops early |
| [`subagent-worktree-integration`](skills/subagent-worktree-integration/SKILL.md) | Reconcile a spawned agent's isolated git worktree with the orchestrator's own checkout, and detect when that worktree is stale |
| [`plain-prose`](skills/plain-prose/SKILL.md) | Rewrite mannered prose in instructional markdown (commands, agents, skills, adapters) into plain, direct text that keeps every rule and literal |
| [`review-judgment-filters`](skills/review-judgment-filters/SKILL.md) | Separate findings that change a verdict from nits and untraced hypotheticals, without dismissing security findings |
| [`blast-radius`](skills/blast-radius/SKILL.md) | Name the one fact a change is safe because of and push its evidence up a five-rung ladder |

Skills are explicitly invoked via `Read skills/<name>/SKILL.md`. Writ-authored skills set `disable-model-invocation: true` so platforms don't ambient-load them — every load is traceable. Authored via `/new-skill`; boundary-linted via `scripts/lint-skill.sh` (also run by `/refresh-command --lint-skills`).

## Platform Support

Writ runs on any AI coding platform. Adapters translate tool calls:

| Platform | Setup Guide | Key Pattern |
|----------|-------------|-------------|
| **Cursor** | [`adapters/cursor.md`](adapters/cursor.md) | Native — `Task()`, `AskQuestion()` |
| **Claude Code** | [`adapters/claude-code.md`](adapters/claude-code.md) | `claude -p`, `CLAUDE.md`, `--allowedTools` |
| **Codex CLI** | [`adapters/codex.md`](adapters/codex.md) | `AGENTS.md`, `.codex/agents/*.toml`, native `/agent` |
| **OpenClaw** | [`adapters/openclaw.md`](adapters/openclaw.md) | `sessions_spawn()`, Telegram inline buttons (mapping guide — no installer flag yet) |

## Quick Start

Type `/writ` followed by what you want:

```
/writ "users can't paste into the search box on Safari"
→ Goal, Problem, Done check restated; route: /prototype --no-diverge; it runs, and asks first only when the route is in doubt.
```

New here? Read [`.writ/docs/prompting-guide.md`](.writ/docs/prompting-guide.md) (two minutes), then type `/writ` followed by what you want.

### What `/writ` routes to

Five commands take you from idea to PR:

| Command | What it does |
|---------|--------------|
| `/prototype` | Quick changes — no spec needed. Describe it, ship it. |
| `/create-spec` | Turn a feature idea into a structured contract with stories. |
| `/implement-spec` | Execute a spec end-to-end: dependency graph → parallel stories → quality gates. |
| `/ship` | Merge, split commits, open a PR. |
| `/status` | See where everything stands — specs, branches, progress. |

Everything else (planning, reviews, retros, releases) is there when you need it; `/writ` picks the route for you.

### Claude Code (plugin)

```bash
claude plugin marketplace add sellke/writ
claude plugin install writ@writ
```

Then open your project in Claude Code and run `/writ:initialize`, which creates the `.writ/` workspace. Under the plugin every command carries the `writ:` prefix, so the front door is `/writ:writ "my feature"`. Scripts run from the plugin's own folder, so the project needs no `scripts/` copy. The plugin does not include the `.writ/docs/` reference docs that `install.sh` copies; [`adapters/claude-code.md`](adapters/claude-code.md) → Installation → Plugin lists what else differs.

Smoke test: `claude-plugin pass` in [`scripts/tests/fixtures/plugin-smoke-results.txt`](scripts/tests/fixtures/plugin-smoke-results.txt), recorded by `bash scripts/tests/test_plugin_smoke.sh --record`.

### Cursor (one-line install)

From your project root:

```bash
bash <(curl -s https://raw.githubusercontent.com/sellke/writ/main/scripts/install.sh)
```

This copies all commands, agents, rules, and system instructions into `.cursor/`, creates the `.writ/` workspace, and commits the result. Preview first with `--dry-run`:

```bash
bash <(curl -s https://raw.githubusercontent.com/sellke/writ/main/scripts/install.sh) --dry-run
```

Then in Cursor chat: `/writ "my feature"`

### Updating

```bash
bash <(curl -s https://raw.githubusercontent.com/sellke/writ/main/scripts/update.sh)
```

The updater uses a manifest (`.cursor/.writ-manifest`) to track what was installed. Files you haven't touched update silently. Files you've customized are **never overwritten** — you're told which ones were preserved. Files removed upstream are cleaned up.

| Flag | Effect |
|------|--------|
| `--dry-run` | Preview changes without applying |
| `--force` | Overwrite all files, including your customizations |
| `--no-commit` | Don't auto-commit after update |

To reset a single file to upstream: delete it and re-run update.

### Cursor (plugin)

Status: local install; marketplace listing pending.

From a clone of this repository, copy the plugin folder into Cursor's local plugins folder, then restart Cursor or run **Developer: Reload Window**:

```bash
git clone https://github.com/sellke/writ.git && cd writ
rm -rf ~/.cursor/plugins/local/writ
mkdir -p ~/.cursor/plugins/local/writ
cp -R cursor/plugin/. ~/.cursor/plugins/local/writ/
```

The plugin ships no `scripts/`: its commands run `python3 scripts/<name>.py` in your project, so run the Cursor one-line install above as well. Smoke test: `cursor-plugin unverifiable` in [`scripts/tests/fixtures/plugin-smoke-results.txt`](scripts/tests/fixtures/plugin-smoke-results.txt), because the test runs no Cursor session; the Cursor UAT protocol has not run yet. Details: [`adapters/cursor.md`](adapters/cursor.md) → Plugin.

### Claude Code (one-line install)

```bash
bash <(curl -s https://raw.githubusercontent.com/sellke/writ/main/scripts/install.sh) --platform claude
```

This copies all commands and Claude Code–native agents (with YAML frontmatter) into `.claude/`, merges a Writ block into `CLAUDE.md` at your project root (creating it if absent, appending below any pre-existing hand-written content otherwise — your own instructions are never overwritten), and commits the result. Preview first with `--dry-run`:

```bash
bash <(curl -s https://raw.githubusercontent.com/sellke/writ/main/scripts/install.sh) --platform claude --dry-run
```

Then in Claude Code: `/writ "my feature"`

**Updating:**

```bash
bash <(curl -s https://raw.githubusercontent.com/sellke/writ/main/scripts/update.sh) --platform claude
```

### Codex CLI (one-line install)

```bash
bash <(curl -s https://raw.githubusercontent.com/sellke/writ/main/scripts/install.sh) --platform codex
```

This copies commands into `.codex/commands/` and `system-instructions.md` into `.codex/`, installs Codex-native TOML agents into `.codex/agents/`, merges a Writ block that carries the Prime Directive into `AGENTS.md`, seeds `.codex/config.toml` only if absent, and installs skills into `.agents/skills/`. Preview first with `--dry-run`:

```bash
bash <(curl -s https://raw.githubusercontent.com/sellke/writ/main/scripts/install.sh) --platform codex --dry-run
```

Restart Codex after install so it reloads `AGENTS.md`, then ask it to follow `.codex/commands/writ.md` for `/writ "my feature"`.

Tested against Codex CLI as of May 2026; TOML schema may evolve — see [`adapters/codex.md`](adapters/codex.md).

## Migrating from Code Captain

Already using Code Captain? Migrate in seconds — all specs, stories, ADRs, and progress preserved:

```bash
bash <(curl -s https://raw.githubusercontent.com/sellke/writ/main/scripts/migrate.sh)
```

Preview first with `--dry-run`:

```bash
bash <(curl -s https://raw.githubusercontent.com/sellke/writ/main/scripts/migrate.sh) --dry-run
```

Then install Writ with `install.sh` as shown above. See [`commands/migrate.md`](commands/migrate.md) for the full interactive migration command.

## Directory Structure

When Writ runs, it creates a `.writ/` directory in your project:

```
.writ/
├── config.md                 # Project settings (version file, test runner, judgment provider)
├── context.md                # Orientation snapshot, regenerated by /status
├── quality-baseline.md       # Acknowledged quality findings (from /initialize)
├── specs/                    # Feature specifications
│   ├── archive/              # Completed specs (moved by /status --archive or /release)
│   └── YYYY-MM-DD-feature/
│       ├── spec.md           # Main specification (from contract)
│       ├── spec-lite.md      # Condensed for AI context
│       ├── user-stories/     # Individual story files
│       │   ├── README.md     # Progress tracking
│       │   └── story-N-*.md  # 5-7 tasks each
│       ├── drift-log.md      # Spec amendment record (auto-generated)
│       ├── uat-plan.md       # Human UAT scenarios (from /create-uat-plan)
│       ├── recommendation-log.md  # Decisions made without asking, with their evidence
│       └── sub-specs/        # Technical deep-dives
├── product/                  # Product planning docs
├── decision-records/         # Architecture Decision Records
├── research/                 # Research outputs
├── retros/                   # Transcript retro findings and dispositions
├── security/                 # Security audit reports
├── issues/                   # Quick-captured issues (goals/ holds Goal Cards)
├── goals/                    # GOAL.md / VERIFY.md emitted from loop: yes Goal Cards
├── knowledge/                # Cross-cutting accumulated knowledge
│   ├── decisions/            # Small decisions that don't warrant a full ADR
│   ├── conventions/          # Codebase patterns and conventions
│   ├── glossary/             # Domain terminology
│   └── lessons/              # Postmortem-style learnings
├── eval/                     # Eval inputs (anti-sycophancy phrases, pipeline baselines)
├── docs/                     # Project documentation
│   ├── tech-stack.md
│   ├── code-style.md
│   └── best-practices.md
├── explanations/             # Code explanations
└── state/                    # Workflow state (ephemeral)
```

## Philosophy

1. **Contract-first** — Establish agreement before creating files. Challenge bad ideas early.
2. **Opinionated by default** — Lead with the recommendation, explain why, then offer alternatives.
3. **TDD always** — Tests first, then implementation. 100% pass rate mandatory.
4. **Quality gates** — Automated checks at every stage.
5. **Parallel by default** — Independent work runs simultaneously.
6. **Self-improving** — Commands get better through use. `/refresh-command` + `/retro` close the feedback loop.
7. **Platform-agnostic** — Markdown instructions work anywhere AI agents run.
8. **Durable substrate** — Specs, decisions, and accumulated knowledge live as plain-text markdown in git. Survives projects, teams, and AI platform churn.
9. **Ask on doubt, not on principle** — The harness decides, acts, and records. A person is asked only when evidence, reversibility, or a calibrated judgment says the answer is in doubt ([ADR-033](.writ/decision-records/adr-033-doubt-gated-autonomy.md)).

## Where Writ is going

The roadmap is in [`.writ/product/roadmap.md`](.writ/product/roadmap.md). Shipped through Phase 15: the contract layer, script-backed gates, behavioral verification, one front door, plugin distribution, code-level rigor, and evidence-gated review. Phase 17, Doubt-Gated Autonomy, shipped with it: one rule replaces the human gates by category, Jev runs first on every decision, and a supervisor checks subagent reports. Phases 14, 15, and 17 are in v0.44.0. Next:

- **Calibrate Jev on real decisions.** On 98 of the maintainer's past answers, Jev could not yet tell which ones the person would change, so it shadows and the decision's kind decides. Each answered question becomes a label; once they bound the share of its acts you would have overridden under 10%, Jev decides.
- **Phase 16 — Verified Landing.** A read-only PR-readiness check, a verification ledger bound to the PR head, and a `/ship` watch mode that drives a PR to merge-ready and, with the ledger green and doubt low, merges it. Release, tag, and publish stay asks.
- **After that:** command consolidation, measured by what is still invoked directly once the front door asks only on doubt, and a parking lot that earns its way in one phase at a time.

The standing rule is subtraction: each phase opens by removing what no longer earns its place, and no new phase starts while two finished ones wait on a person.

## Developing Writ

This repo uses Writ to build Writ. Product source lives in `commands/`, `agents/`, `skills/`, `adapters/`, `scripts/`, and `cursor/`. `.cursor/`, `.claude/`, and `.codex/` are symlinks back to it, so edits are live immediately. Don't run `install.sh` on this repo. See [`.writ/docs/self-dogfooding.md`](.writ/docs/self-dogfooding.md).

The product is markdown, but `scripts/` carries a Python and bash test suite plus the quality gate. The Python floor is 3.9, and the suite must stay green from 3.9 up. Run pytest alone: `eval.sh` or the bash tests in the same tree make its smoke test fail.

```bash
# Python tests, about 4 min each. Name both interpreters: a bare `uv run pytest`
# resolves to the 3.9 system Python, so it never tests a newer one.
uv run --isolated --python 3.9 --with pytest pytest
uv run --isolated --python 3.14 --with pytest pytest

# Bash tests, about 12 min
for t in scripts/tests/test_*.sh; do bash "$t" || echo "FAIL $t"; done

# Quality gate; --check=<name> for one check, --report=<path> for a read-only run
bash scripts/eval.sh
```

`eval.sh` runs `git init` in a temp directory, so run it outside any sandbox. It also runs on every PR via GitHub Actions.

## Attribution

Writ is derived from [Code Captain](https://github.com/devobsessed/code-captain) by [@DevObsessed](https://github.com/devobsessed), originally released under the MIT License. This project extends the original with multi-agent orchestration, automated quality gates, platform adapters, and additional commands.

## License

MIT — see [LICENSE](LICENSE).
