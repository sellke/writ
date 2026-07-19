# Writ vs. Conductor — Spec-Driven Development Framework Analysis (July 2026)

**Date:** 2026-07-18
**Status:** Complete
**Subject:** [gemini-cli-extensions/conductor](https://github.com/gemini-cli-extensions/conductor) v0.3.0 — "Measure twice, code once." A Google-adjacent (gemini-cli-extensions org) Spec-Driven Development plugin for Antigravity and Claude Code. 3.6k stars, Apache-2.0.
**Method:** Read all of Conductor's actual protocol source (6 `SKILL.md` files, `workflow.md` template, `catalog.md`, `resume.py`, `rules/conductor_antigravity.md`, `plugin.json`) — not just the README. Compared against Writ's product source and `.writ/` conventions.

---

## Research Questions

1. **What is Conductor, mechanically?** Not the marketing — the actual protocol.
2. **What is genuinely remarkable** that Writ should consider adopting?
3. **Where does Writ hold real advantages** over Conductor?
4. **What's the honest strategic takeaway?**

---

## Executive Summary

Conductor is a **lean, git-native, single-lane SDD loop**: 6 skills, one `conductor/` directory, and a task-by-task TDD workflow where every task and phase is a commit whose SHA is recorded back into `plan.md`. It is disciplined, approachable, and its "the git repo *is* the database" audit model is cleaner than Writ's in one specific dimension.

Writ is a **deep, parallel, multi-agent SDLC methodology**: 4 orchestration levels (roadmap phase → spec → story → 6-gate agent pipeline), worktree isolation, drift classification, contract-first spec negotiation, an eval-enforced anti-sycophancy governance layer, and self-improvement machinery. It is far more sophisticated at execution and rigor.

They converge remarkably on principles — TDD-first, >80% coverage, conventional commits, spec-before-code, human confirmation gates, and *even the "(Recommended)"-labeled option convention* (independent convergence that validates Writ's ADR-013). They diverge hard on execution philosophy: Conductor is **one lane, fully supervised, minimal surface**; Writ is **many lanes, gated, governed, high surface**.

**The one genuinely remarkable idea worth adopting: `git notes` as the durable audit channel.** Everything else Writ either already does more rigorously, or is a deliberate scope choice Writ has made differently. Conductor is most valuable to us as a **leanness mirror** (ADR-015): it achieves a coherent SDD lifecycle with ~1/5th of Writ's surface area, and that is worth sitting with.

---

## Side-by-Side

| Dimension | Writ (v0.13.x) | Conductor (v0.3.0) |
|---|---|---|
| **Surface area** | 30 commands, 7 agents, 6 skills, 4 adapters, ~15 eval scripts | 6 skills, 1 rules file, 1 workflow template, 1 python helper |
| **Unit of work** | Roadmap phase → spec → user story → agent gates | "Track" (feature/bug/chore) → flat `plan.md` phases/tasks |
| **Orchestration depth** | 4 levels | 2 levels (track → task loop) |
| **Execution model** | DAG → parallel batches, worktree lanes, quarantine | Strictly sequential ("next available task… in sequential order"), single working tree |
| **Spec artifact** | `spec.md` + agent `spec-lite.md` + sub-specs (technical/db/api/ui) + user-stories DAG | Single `spec.md` (Overview, FR, NFR, AC, Out-of-scope) drafted via Q&A loop |
| **Plan artifact** | User stories w/ Given-When-Then AC, dependency frontmatter, Context-for-Agents hints | Flat `plan.md`: phases → tasks → sub-tasks with `[ ]`/`[~]`/`[x]` + inline SHAs |
| **Quality gates** | 6-gate pipeline: arch check, boundary map, TDD, lint, review+drift, testing (80%), visual QA, docs | Per-task TDD in `workflow.md`; per-phase checkpoint verification; `conductor-review` skill |
| **Code review** | Review Agent (PASS/FAIL, drift severity, max 3 iterations) | `conductor-review` (Principal Engineer persona, smart-chunking >300 lines, runs test suite, style guides = "Law") |
| **Drift handling** | First-class: Small/Medium/Large; Small auto-amends `spec-lite.md` + drift-log | None during build; post-hoc doc sync from completed track spec |
| **Git-aware revert** | Only inside `/refactor` loop (commit-or-revert per step) | **Dedicated `conductor-revert`**: maps track/phase/task → all associated commits, ghost-commit reconciliation, safe vs hard-reset |
| **Audit trail** | "What Was Built" records appended to story markdown; `.writ/state/*.json` | **`git notes`** attached to each task commit + full verification report note on phase checkpoints; SHAs recorded in `plan.md` |
| **Context loading** | Agent-specific spec-lite (<100 lines), per-story indexed hints, WWB from deps | Whole `product.md` + `tech-stack.md` + `workflow.md` + `spec.md` + `plan.md` each run (README warns of token cost) |
| **Autonomy** | Supervised phase loop after 1 confirmation; `--recommend` on 2 commands; never auto-merge/release | Always human-in-loop, per task; no autonomous mode |
| **Ceremony control** | `/prototype`, `--quick` for low ceremony | One-size-fits-all: every track gets full spec+plan+TDD |
| **Governance** | Prime Directive (eval-enforced anti-sycophancy), ADRs, leanness tripwire | Review persona "helpful but firm"; no governance/eval layer |
| **Self-improvement** | `/refresh-command` (transcript evidence), eval Tier 1 CI, skill lifecycle, knowledge consolidation | None — static skill set |
| **3rd-party skills** | First-party only today | **Trust model**: catalog discloses 1p/3p; 3p frozen at commit SHA + explicit warning; curl-installed |
| **Context wiring** | Convention (`.writ/` tree) + regenerated `.writ/context.md` | **`index.md` "Handshake"** — explicit single-source-of-truth pointer file, integrity-checked |
| **Platforms** | Cursor, Claude Code, Codex, OpenClaw (adapter layer + install/update w/ 3-way merge) | Antigravity, Claude Code (plugin marketplace, one-command install) |
| **UX adaptivity** | Per-adapter AskQuestion mapping | `rules` file: detects native `ask_question` modal, else text fallback w/ one-question-at-a-time barrier |
| **Doc sync** | `/plan-product --reconcile` (separate, manual) | Built into implement loop: propagates completed track → product.md/tech-stack.md/guidelines (diff + approval) |

---

## What Conductor Does That Is Genuinely Remarkable

### 1. `git notes` as the durable audit channel ⭐ (top recommendation)

This is the standout idea. Conductor's `workflow.md` attaches a **detailed task summary** to each task's commit via `git notes add`, and on phase completion attaches a **full verification report** (the exact test command run, the manual verification steps, and *the user's confirmation text*) as a note on the checkpoint commit.

Why it's elegant:
- **Audit lives in git, travels with the commit**, survives file moves/renames, and doesn't clutter the working tree or pollute the diff.
- It's **queryable** (`git log --notes`, `git notes show <sha>`) and **portable** across any tool.
- It decouples the "why/what/verification" record from the source files.

Writ's analog — "What Was Built" records — lives *inside story markdown files*. That's great for downstream-agent context loading, but it's a different channel: WWB is *forward-looking* (feeds the next agent), git notes are *backward-looking* (immutable audit bound to the artifact). **These are complementary, not competing.** Writ could attach a git note at story/spec completion carrying the WWB summary + coverage + review verdict, giving us an immutable, git-native audit trail without touching the working tree. Strong ADR candidate.

### 2. Third-party skill trust model

Conductor's `catalog.md` + setup/new-track skills implement a real supply-chain posture: each skill discloses **`Party: 1p` (official) vs `3p` (community)**, and third-party skills are **installed frozen at a specific commit SHA with an explicit user warning** ("It will be installed as a frozen version (commit <sha>) for your safety"). Detection signals (dependencies + keywords) drive contextual recommendation.

Writ ships first-party skills only today, so there's no *immediate* need. But the moment Writ's skill ecosystem opens to external/community skills, this is exactly the trust model to have designed *first*. Worth capturing as a reserve pattern (mirrors how ADR-016's `required_skills:` was reserved before adoption).

### 3. `index.md` "Handshake" — an explicit context pointer file

Conductor writes a single `conductor/index.md` that maps every context artifact via relative links (Definition, Workflow, Capabilities), and every skill's first act is "locate + read index.md, then verify every linked file exists (integrity check), else HALT." It's the deliberate wiring contract any tool resolves first.

Writ relies on the `.writ/` directory *convention* plus a regenerated `.writ/context.md` snapshot. Conductor's index is lighter and more explicit — a stable "here is where everything is" manifest with a health check, versus Writ's richer-but-regenerated snapshot. Minor, but the **integrity-check-then-HALT** discipline at the top of every workflow is a robustness pattern Writ's commands apply unevenly.

### 4. Ghost-commit reconciliation in git-aware revert

`conductor-revert` is a proper git-aware revert: it maps a logical unit (track/phase/task) to *all* associated commits — implementation commit(s), the plan-update commit that followed, and (for a full track) the track-creation commit. When a recorded SHA is missing from history (rebase/squash rewrote it), it **searches the log for a similar commit message and asks to substitute** ("ghost commit" handling), then offers safe (`git revert`) vs destructive (`git reset --hard`) with clear warnings.

Writ has **no general git-aware revert** — only the commit-or-revert loop inside `/refactor`. Because Writ *also* records SHAs (in phase state / stories), a `/revert-spec` or `/revert-story` command that unwinds a logical unit is a natural, high-value addition. The ghost-commit trick is the clever bit to steal.

### 5. Leanness as an existence proof (the uncomfortable one)

Conductor delivers a *complete, coherent* SDD lifecycle — setup, spec, plan, TDD implement, status, review, revert, doc-sync — in **6 skills and one directory**. Writ needs 30 commands, 7 agents, 6 skills, 4 adapters, and an 8-subdirectory `.writ/` tree plus JSON execution state to cover comparable ground (with more depth). Per Writ's own **ADR-015 (leanness self-governance)**, Conductor is a useful tripwire: it's evidence that much of an SDD loop can be expressed compactly. Not every Writ command earns its surface area, and Conductor is a clean foil for that audit.

---

## Where Writ Holds Real Advantages

1. **Execution depth & parallelism.** Writ's 6-gate multi-agent pipeline (arch → boundary → code → lint → review+drift → test → visual → docs) vs Conductor's single agent looping tasks sequentially. Writ has DAG-based parallel story batches, per-spec worktree lanes, and quarantine branches. Conductor is explicitly single-lane, single-tree. This is a category difference.

2. **Contract-first spec rigor.** Writ's `create-spec` refuses to write *any* file until the contract is locked in Plan Mode, does cross-spec overlap detection, and decomposes into user stories with Given-When-Then AC + dependency graphs + sub-specs. Conductor's spec is a single doc from a Q&A loop, then a flat checkbox plan. Writ negotiates the contract far harder.

3. **Drift as a first-class artifact.** Writ classifies Small/Medium/Large drift mid-build and auto-amends `spec-lite.md` (SHA-bound, logged) for small drift while keeping `spec.md` human-approved. Conductor has *no* concept of implementation-vs-spec drift during the build; it only syncs docs after the fact.

4. **Context engineering / token efficiency.** Writ hands each agent a purpose-built `spec-lite.md` (<100 lines) + indexed hints + WWB from dependencies. Conductor reloads whole product/tech-stack/workflow/spec/plan docs on every skill invocation — its own README warns about token consumption. Writ's context model is materially leaner *per agent step* even though its total surface is larger.

5. **Governance / anti-sycophancy.** Writ's Prime Directive is an explicit, eval-enforced honesty contract (`scripts/eval.sh` checks anti-sycophancy + prime-directive-sync). Conductor's rigor is a review *persona* ("helpful but firm") — no governance layer, no eval suite testing the framework itself.

6. **Self-improvement infrastructure.** Writ has `/refresh-command` (requires transcript evidence), a Tier-1 eval CI gate (~15+ static checks), a skill maturity lifecycle (candidate→proven→promoted), and knowledge consolidation. Conductor is a static skill set with no self-test or learning loop.

7. **Adaptive ceremony.** Writ scales down (`/prototype`, `--quick`) for chores and up (full pipeline) for production paths. Conductor runs the *same* full spec+plan+TDD ceremony for a one-line chore as for an MVP — heavy at the low end.

8. **Bounded autonomy with audit.** Writ's `--recommend` (2 commands only, evidence-bound select-or-pause, resumable, never auto-merge/release) gives supervised throughput. Conductor is safe-by-default but has *no* autonomous mode — every task waits on a human.

9. **Platform breadth + non-destructive updates.** Writ's adapter layer covers 4 platforms with install/update scripts that 3-way-merge to preserve local customizations. Conductor covers 2 via plugin marketplace (simpler for end-users, but no customization-preserving update story).

---

## Where They Converge (validation, not advantage)

- **TDD red-green-refactor** enforced task-by-task; **>80% coverage** gate.
- **Conventional commits** grammar.
- **Spec/contract before code**; human confirmation gates throughout.
- **"(Recommended)"-labeled options** with an explanation and an always-present "Other" — near-identical to Writ's ADR-013 recommendation semantics. Independent convergence is strong external validation of that decision.
- **Review appends a "Review Fixes" phase** to the plan rather than silently editing — same pattern as Writ.
- **Brownfield/greenfield detection** and read-only-scan-with-permission on existing repos.
- **Git-hygiene guard** (warn on uncommitted changes before proceeding).

---

## Honest Strategic Takeaway

Writ should **not** restructure toward Conductor. Conductor is the *simpler, shallower* tool; Writ is the *deeper, governed* one, and that depth (parallel gated execution, drift, contract rigor, governance) is the differentiated moat (ADR-008). Conductor validates a lot of Writ's principle choices by arriving at them independently.

**Adopt / evaluate (ranked):**

1. **`git notes` audit channel** — high leverage, low cost, git-native, complements WWB. Write an ADR + wire into `/implement-story` completion and `/release`. *Top pick.*
2. **`/revert-spec` / `/revert-story` command** with ghost-commit reconciliation — Writ records SHAs but has no logical-unit revert. Natural fit.
3. **Integrity-check-then-HALT + an explicit `.writ/index.md` handshake** — cheap robustness; standardize the "verify linked artifacts exist before working" preamble.
4. **Third-party skill trust model** — reserve-only now (like `required_skills:`), design before the ecosystem opens.
5. **Leanness audit against ADR-015** — use Conductor as the foil: which Writ commands don't earn their surface area?

**Do not adopt:** single-lane sequential execution, one-size-fits-all ceremony, coarse whole-doc context loading, or dropping the governance/eval layer. Those are precisely where Writ is ahead.
