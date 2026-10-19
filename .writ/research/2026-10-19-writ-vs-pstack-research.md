# Writ vs. pstack: Comparison and Strategic Implications (October 2026)

**Date:** 2026-10-19
**Status:** Complete
**Subject:** [pstack](https://github.com/cursor/plugins/tree/main/pstack) 0.15.28 (`cursor/plugins` at `d457567`, 2026-10-19), by Lauren Tan (poteto). MIT. A Cursor plugin, also installable in Claude Code from a generated tree.
**Writ version compared:** 0.41.0 (branch `feature/agent-cli-contract` at `631e043`)
**Method:** Read pstack's full source: 32 skills, 24 principle skills, 23 playbooks, 2 agents, 5 tools, the guide, the Claude Code adapter, and the benny automation pack. Read its commit history (145 commits touching `pstack/` since 2026-05-23). Mapped Writ's shipped surface from source. Spot-checked every load-bearing claim on both sides against the files. Nothing from pstack was executed.
**Prior pstack borrowing:** ADR-028, ADR-029, and two open issues took single mechanisms from pstack. This is the first full comparison.

---

## Research Questions

1. What is pstack, mechanically, and how does its design differ from Writ's?
2. Where is pstack ahead in ways that fit Writ's mission?
3. Where is Writ ahead, and what in pstack should Writ not copy?
4. What does the comparison expose about Writ's own surface?
5. What should change in Writ's mission and roadmap?

---

## Executive Summary

pstack is one senior engineer's working method, packaged as Cursor skills. A 149-line router (`/poteto-mode`) matches a task to one of 23 playbooks, copies the playbook's steps into the todo list, and calls focused skills as the steps need them: design exploration, cross-model review, root-cause work, and verification against the running app. Its bet is depth per agent. If each agent proves its own work on the real artifact, many agents can run in parallel and land PRs while the operator sleeps. It has no planning layer by design. Almost all of its rules are prose, and five small tools are its only code.

Writ is a contract layer: specs, acceptance-criteria IDs, drift logs, ADRs, a knowledge ledger, and phase orchestration. Scripts re-derive most `/implement-story` gate verdicts. Writ is stricter than pstack about intent and enforcement, and weaker about the code itself: its gates check that artifacts are well formed and tests pass, while pstack's skills ask whether the design and the fix are right. Writ's autonomy stops before the PR opens. It reaches users through 32 commands rather than one entry point, and its Claude Code install ships without the Prime Directive.

**Recommendation:** keep the contract layer as Writ's identity and take four things from pstack, in this order, after a subtraction pass. (1) One front door that restates the request, classifies it, and picks the ceremony. (2) Plugin distribution with generated per-platform trees and an adapter coverage check, which also fixes the Claude Code parity gap. (3) Code-level rigor inside the existing gates, plus a `/why` that answers from Writ's own ledger first. (4) A verified-landing loop that binds verdicts to the PR head SHA, which Phase 12's evidence now makes possible to evaluate. Do not copy pstack's no-planning stance, its proceed-without-asking default for external side effects, or its single-author style rules.

---

## Side by Side

| | pstack 0.15.28 | Writ 0.41.0 |
|---|---|---|
| **Thesis** | Go deep per agent, then parallelize. Write less code. | Agree the contract before code. Keep intent, decisions, and lessons durable. |
| **Maintenance** | One primary author. 145 commits in 5 months, 55 of them in October 2026. | One maintainer. 701 commits in 7.7 months, 41 releases. |
| **Distribution** | Plugin: `/add-plugin pstack` in Cursor, `/plugin install` in Claude Code from a generated tree | `install.sh` copies commands, agents, skills, 34 scripts, and 28 docs into the project and commits |
| **Entry point** | One router (`/poteto-mode`). `/poteto-help` answers "which skill" without starting work. | 32 commands. README: "you only need five." |
| **Unit of work** | Playbook run, ending in small ordered PRs | Roadmap phase, then spec, then story, then gates |
| **Planning** | None by default. The README says code is the best spec. | Contract-first specs, product plan, roadmap |
| **Prose** | Skills and agents about 424 KB. Router 20 KB. Most playbooks under 5 KB. | Commands and agents 15,416 lines. `create-spec` 53 KB, `implement-story` 37 KB. |
| **Code** | 5 tools (TypeScript on Bun, plus 2 shell scripts), about 217 KB with tests | 74 Python and 10 shell scripts (about 46k lines), 95 test files, 67 eval checks |
| **Enforcement** | Prose, platform flags (`readonly`, `disable-model-invocation`), worktrees | Scripts re-derive gate verdicts. `eval.sh` runs in CI over Writ's own markdown. |
| **User-feature verification** | Project-local verify skill with a feature map. Plans require ten live lanes per PR. Formal-verification skills added 2026-10-18. | App-verification recipe and `app-verify.py` at Gate 4.5 (Phase 12, pending human UAT) |
| **Review** | `interrogate`: same prompt to Claude and Grok, then lead-judgment filters. `arena`, `architect`. | evaluator-agent or review-agent. Opt-in cross-vendor panel, Cursor only. |
| **Models** | Role-to-model rule. Code to Grok, judgment to Opus, panels cross-family. | `anchor`/`floor`, family-locked (ADR-024) |
| **Autonomy** | Proceeds on reversible work and on team chat and ticket updates. Autopilot lands verified PRs. Pauses for force-push, deploys, deletion, customer messages. | Never merges, opens PRs autonomously, or releases. `--recommend` on two commands. |
| **Long runs** | Harness `/loop` plus watchers. `orch` ledger keyed by (PR, SHA). `watch-pr` typed readiness. Decision-trail TSV. | `/implement-phase`: fresh context per spec, lanes, quarantine, `phase-state.py reconcile` |
| **Durable record** | PRs, plus an optional uncommitted `decisions.tsv` | Specs, drift logs, ADRs, knowledge ledger, What Was Built records, git notes |
| **Learning loop** | `reflect`, `correct`, `automate-me` | `/refresh-command`, `/retro` (transcripts since 0.41.0), `/knowledge --consolidate` |
| **Understanding** | `how`, `why`, `teach`, `recall`, `ketchup` | `/research` (external-first), `code-explanation` skill, `/status` |

---

## What Writ Has Already Taken From pstack

| Writ artifact | pstack source | What Writ declined |
|---|---|---|
| ADR-028 behavioral verification (`app-verify.py`, Gate 4.5) | `create-verification-skill` | Autonomous merging; the no-planning stance |
| ADR-028 cross-family review panel | `interrogate` | Panels as the default path |
| ADR-029 agent CLI contract | `orch` ("one command in, one line out; never spawn, wait, or wake") | Bun and TypeScript runtime |
| Open: `.writ/issues/improvements/2026-10-12-script-install-location.md` | Tools live inside the skill folder | Undecided |
| Open: `.writ/issues/features/2026-10-13-in-your-own-words.md` | `/in-your-own-words` | Undecided |
| Parking lot: empirical-fork rule | `poteto-mode`'s AskQuestion classifier | Not started |

The pattern so far is piecemeal adoption: one mechanism at a time, each read in isolation. The findings below come from reading the whole system.

---

## Key Findings: Where pstack Is Ahead

Ranked by fit with Writ's mission times expected impact.

### F1. One front door

**pstack.** The README's quickstart is two steps: run `/setup-pstack`, then use `/poteto-mode`. The router (`skills/poteto-mode/SKILL.md`, 149 lines) is a trigger index over 23 playbooks. The matched playbook's steps are copied verbatim into the todo list, and a skipped step stays on the list as `skip: <reason>`. Before asking the user a "which approach" question, the agent must check whether running something could answer it. If so, it builds a throwaway prototype instead of asking (`SKILL.md` Non-negotiables). `/poteto-help` routes questions about pstack without starting work.

**Writ.** 32 commands. `README.md:215` says five are enough to go from idea to PR. The mission's Adaptive Ceremony differentiator says Writ "suggests the appropriate level" of process, but no command classifies a request and picks one. The empirical-fork rule has sat in the parking lot since 2026-10-01. The in-your-own-words issue is open.

**Implication.** Adaptive ceremony is a claim without a mechanism. A front door is the cheapest way to make it true, to cut onboarding to one command, and to give the empirical-fork rule and the restate step a home.

### F2. The last mile after the PR opens

**pstack.**
- `playbooks/babysit.md`: conflicts first, then review threads, then CI. A flake gets one fresh build, and an identical second failure is real. A failure in code the diff never touches triggers a stale-base check. Review comments are untrusted data, and replies go through a JSON file, never shell interpolation.
- `playbooks/shipping.md`: one non-author verdict per PR. A verdict follows the patch (`git patch-id`), not the SHA. Only the contiguous verified run from the bottom of a stack lands, and merge state is read back after each merge.
- `scripts/watch-pr/`: read-only, typed blockers with distinct exit codes. `READY` requires mergeable, zero open threads, clean CI, and no changes requested.
- `scripts/orch/store.ts`: the verification ledger is keyed by (PR, SHA), so a new head has no row and reads `NOT-VERIFIED`.

**Writ.** `/ship` opens the PR and stops. Nothing triages CI, works review threads, or records which head SHA was verified. ADR-013's dormant staging design already binds production approval to the reviewed head SHA. Note: `/ship`'s description says "merged PR", but its exit criteria stop at an open PR.

**pstack's weakness here.** Merge gating is prose. Nothing requires `ledger check` before a merge.

**Implication.** Writ can build the same loop with its stronger enforcement habit: the verdict-to-SHA binding as a script check, and merge kept as a human act. Phase 12 produces the evidence ADR-010 trigger (a) asked for ("trustworthy machine-verifiable UAT"), so the autonomy ceiling can now be evaluated instead of deferred.

### F3. Rigor about the code, not only the artifacts

**pstack.**
- `architect`: at least two structurally distinct sketches from different models, the caller's usage written first, red flags written for agent contributors (importable internals, hand-synced lists, two ways to do one task), and a rationale with alternatives.
- `interrogate`: lead-judgment filters. If every finding is a nit, the code is fine. Trace the call site before accepting a "what if null." Be slow to dismiss security findings, even from one model.
- `blast-radius`: name the one fact the change is safe because of, and push its evidence up a five-rung ladder, from "you said so" to "reproduced in the running app."
- `playbooks/bug-fix.md`: reproduce on the same surface, commit the failing repro before the fix, and paste failing-then-passing output.
- `benchmark-checklist`: the verdict is inconclusive unless the limiter is named, both sides were tuned, and the timed region did the work.

**Writ.** Gate 0 is a floor-tier checklist agent; the goldilocks assessment rated its prompt about 55% coaching. Gate 2.5 is a path heuristic. `/review` and `/security-audit` are prose-only. There is no bug-fix flow. Writ's own lean-harness experiment compared costs inside a 59% run-to-run noise band.

**Implication.** Writ's verifier layer checks that artifacts are well formed and tests pass. pstack's checks ask whether the design and the fix are right. Writ should upgrade existing gates on the high-stakes route rather than add commands.

### F4. "Why" from evidence, with stated confidence

**pstack.** `skills/why/` builds a code anchor from `git blame`, `git log`, and PR metadata. It discovers available MCPs, assigns one investigator per evidence category, and synthesizes with five confidence tiers. It never cites code as evidence of its own intent, and it reports null results. When a change follows, it ends with a Preserve / Change / Avoid / Risk list.

**Writ.** Writ owns the best evidence for this question: ADRs, drift logs with `DEV-NNN` IDs, specs, What Was Built records, and git notes on landed commits. No command answers "why is this like this?" from them. `/research` is external-first.

**Implication.** This is the highest-fit idea in pstack. A `/why` that reads Writ's ledger first makes the contract layer's value visible on an ordinary workday. Its Preserve / Change / Avoid / Risk output is a ready-made input to `/create-spec` discovery.

### F5. Lessons into structure

**pstack.**
- `skills/correct/SKILL.md` fixes each recurring mistake class at the highest level that works: architecture, then types, then a lint whose error names the fix, then a behavior test, then docs last. Each new check must fail on a real past mistake. Common patterns fail only on additions. Exceptions carry an expiry. A rule-to-enforcer table lives in the agent instruction file, and a correction against an unenforced rule counts as a repeat.
- `skills/reflect/` runs three reviewers (judgment, tooling, divergent) and a synthesizer that scores eight criteria. Two of them stand out: if existing guidance already covers a finding, the problem is execution, not a missing rule; and findings may only edit skills the transcript actually used.

**Writ.** `/retro` became transcript-based in 0.41.0 and proposes environment fixes. `/refresh-command` has six log entries in seven months. ADR-025 (friction signals) was designed on 2026-09-03 and never built, and two commands print `(no-op until ADR-025 Story 1)` lines that nothing reads.

**Implication.** `/retro` already reads the same input pstack uses. Give it `correct`'s fix order and rule table as its output contract, and retire the signal-file design. That deletes a planned subsystem and the no-op lines.

### F6. Distribution and platform parity

**pstack.** Installs as a plugin in Cursor and Claude Code. The Claude Code tree is generated by `scripts/generate-pstack-harness-trees.mjs` (repository root). The generator fails when a skill uses a Cursor term the adapter has no row for, fails on dangling links, and has a `--check` mode that fails CI when the tree drifts. Tools live inside the skill folder, so they never collide with a project's own files.

**Writ.**
- `install.sh` copies 34 scripts into the project-root `scripts/` and commits.
- Claude Code installs skip `system-instructions.md` (`install.sh:1268`). They merge a 59-line `claude-code/CLAUDE.md` template that contains no Prime Directive, lists 25 commands, omits `/implement-phase`, `/knowledge`, and `/revert`, and calls `/retro` "Git-based." Meanwhile, 49 lines in `commands/` reference `system-instructions.md`.
- `adapters/claude-code.md` documents `/implement-story --all` and agent teams, which do not exist, and says worktree changes merge back automatically, which contradicts `skills/subagent-worktree-integration`.
- `check-agent-parity.sh` checks only that a counterpart file exists. Claude agent prompts are 45 to 79 lines against 160 to 390 in `agents/`.
- The review panel runs only in Cursor.

**Implication.** Writ's portability differentiator is weakest on Claude Code. pstack's generator check transfers directly and cheaply. Plugin distribution is already a parking-lot candidate and would also settle the script-location issue.

### F7. Continuous subtraction

**pstack.** In the last six weeks: distill skill prompts to cut tokens (#538), cut 19 instructions Opus 5.5 does not need (#419), restate four overspecified principles as reasoning instead of rules (#633), cut marginal sections from eleven skills (#571, #634), and add a docs-vs-tree check (#704).

**Writ.**
- `eval-leanness.py` reports every surface past its own justified ceiling: commands 13,335 lines against 11,081, scripts 87,066 against 46,748. All of it is warn-only.
- Dormant code ships: `recommend-state.py` (3,807 lines) is wired to no command, and it ships with a 794-line state-format doc and about 2,400 lines of tests.
- The five `.lean.md` siblings returned a null result on 2026-09-25 and have been co-edited eight times since.
- `eval.sh` holds 536 `require_literal` and 54 `forbid_literal` pins, so rewording a command means editing eval code.
- Shipped commands reference Writ-internal archive paths and ADRs that do not exist in a user's project.
- CI runs `eval.sh` but not `pytest` or the bash tests (`.github/workflows/eval.yml`).
- The Tier B leanness audits stopped after July.

**Implication.** Subtraction should come before any addition from this list. That is pstack's subtract-before-you-add principle and Writ's own design principle 1.

### F8. Hygiene for long orchestrated runs (lower priority)

**pstack** (`playbooks/orchestrate.md`):
- A brief template (GOAL, SCOPE, CONTEXT, ACCEPTANCE, VERIFY, TIMEBOX, FORBIDDEN, REPORT, STANDING). A unit with a missing field is not spawned.
- A standing-orders register that grows whenever the coordinator repeats an instruction.
- A pilot unit run end to end before fan-out.
- A fresh subagent for each fix round, with consolidated scope, because resumed agents drop directives.
- Liveness judged by side effects, not status text.

**Writ** already runs fresh context per spec and assembles story context with a budget. It has no pilot story and no standing-orders register.

**Implication.** These are small additions for `/implement-spec` and `/implement-phase`. Parking lot.

### F9. Model roles (lowest)

**pstack.** `setup-pstack` writes a role-to-model rule and a budget ladder that never changes a role's model family. Its own Claude Code port collapses every non-Claude role to the session model.

**Writ.** ADR-024's family lock plus an opt-in panel line.

**Implication.** pstack hits the same platform limit Writ did. No change, beyond letting `/initialize` offer the panel line.

---

## Where Writ Is Ahead

1. **Durable intent.** pstack keeps no record of what was agreed before code; its README rejects planning outright. Writ has contract lock, `[AC-N.M]` IDs traced by `ac-trace.py`, drift logs, ADRs, a consolidating knowledge ledger, and product docs with `--reconcile`.
2. **Enforcement in code.** Writ re-derives gate verdicts with scripts and runs 67 checks in CI. pstack's most dangerous invariants are prose: merge only after a verdict, one writer per branch, a non-author verifier. `check-plan.mjs` validates headings and phrasing, and its "valid" test fixture passes with boilerplate text.
3. **Recovery and provenance.** `/revert` by logical unit, git notes on landed commits, quarantine branches, and a `phase-state.py reconcile` that stops on any state/git mismatch. pstack has `pause-safely` and `session-pickup`, both prose.
4. **Bounded side effects.**
   - pstack posts to team chat and updates tickets without asking, and `reflect` files backlog items to a tracker without approval.
   - `make-bot-ui` binds to `0.0.0.0` and installs Tailscale with `curl | sudo sh`.
   - Writ's gate classes (ADR-022) and its double opt-in for network calls (ADR-027) are stricter.
5. **Product layer.** `/plan-product`, the roadmap, and `/verify-spec --product`. pstack has nothing above the PR.
6. **Portability in principle.** Writ's scripts use the Python standard library only and have no runtime dependencies. pstack's tools need Bun and run a dependency install on first use (`scripts/bootstrap.ts`).

---

## What Not to Copy

- **The no-planning stance.** It works for an expert who is the spec. It removes the thing Writ's users come for.
- **Proceed-without-asking for external side effects** (team chat, tickets), and `reflect`'s unapproved tracker writes.
- **Single-author style rules as universal rules:** no colons, no em dashes, and a 1,000-line file treated as a presumptive blocker. Writ's `plain-prose` skill already covers the useful part.
- **`check-plan`'s fixed plan shape:** ten live lanes and a perf block on every PR, docs-only PRs included.
- **Cursor-only machinery:** cloud agents, Bugbot triage, Automations (benny), and `make-bot-ui`.
- **Formal-verification skills, for now.** Both were added on 2026-10-18 and 2026-10-19. Revisit in a month.
- **The cost profile:** verbatim playbook copies, full principle reads before citing, and `why`'s seven-source sweep by default.

---

## Writ Defects Surfaced by the Comparison

| # | Defect | Evidence | Severity |
|---|---|---|---|
| 1 | Claude Code installs ship no Prime Directive; the CLAUDE.md template is stale | `install.sh:1268`; `claude-code/CLAUDE.md` (59 lines, 25 commands) | High |
| 2 | CI runs neither `pytest` nor the bash tests; the agent CLI contract test is local-only | `.github/workflows/eval.yml` | High (XS fix) |
| 3 | `update.sh` deletes a locally modified stale file on the second run | `.writ/issues/bugs/2026-10-12-update-deletes-modified-stale-files.md` (already filed) | High |
| 4 | `adapters/claude-code.md` documents a nonexistent `/implement-story --all` and contradicts the worktree skill | `adapters/claude-code.md:106,296,337` | Medium |
| 5 | Dormant `recommend-state.py` staging machinery ships to users | `scripts/recommend-state.py` (3,807 lines, no command references it) | Medium |
| 6 | `(no-op until ADR-025 Story 1)` emit lines that nothing reads | `commands/implement-story.md:192`, `create-spec` | Low |
| 7 | `/ship` description says "merged PR"; exit criteria stop at an open PR | `commands/ship.md:3` | Low |
| 8 | Lean siblings appear as invocable skills in this repo's Claude Code sessions | `.claude/commands` symlink | Low |

---

## Options Analysis

### Option A: Cherry-pick inside the current roadmap

Add `/why` and a PR-readiness checker as inter-phase specs. Leave the mission as it is.

- **Pros:** Smallest change. No new ADRs. Keeps momentum on Phase 12 close-out.
- **Cons:** Leaves onboarding, Claude Code parity, and surface growth untouched. Continues the piecemeal pattern that produced this doc's "already taken" table.
- **Effort:** S to M. **Risk:** Low.

### Option B: Refresh the mission around contract, verifier, boundary, and one front door (recommended)

Subtract first. Then build the front door and distribution, then code-level rigor, then verified landing, the last gated on Phase 12 evidence.

- **Pros:** Addresses adoption and parity, which are Writ's weakest areas. Makes Adaptive Ceremony true. Raises rigor where Writ checks least. Promotes the goldilocks assessment's framing (contract, verifier, boundary) to the mission, which was never done.
- **Cons:** Largest change. The front door adds a command that has to earn its place. Verified landing needs a new ADR that revisits ADR-010, ADR-013, and ADR-022.
- **Effort:** About 2 to 3 months at the current pace (Phase 11's six specs shipped in five days; Phase 12 in about two weeks). **Risk:** Medium.

### Option C: Compose with pstack

Writ owns contracts. It detects pstack and routes design to `/architect`, review to `/interrogate`, and PR work to the babysit playbook.

- **Pros:** Least new surface. Uses mechanisms that are already maintained.
- **Cons:**
  - Ties Writ to a fast-moving, single-author pack (55 commits in October) that is Cursor-first. Its panels collapse to one model in Claude Code.
  - Activates ADR-018's third-party trust model, which is reserve-only today.
  - Writ cannot gate on prose skills it does not control.
- **Effort:** S. **Risk:** High.

---

## Recommendations

**Primary: Option B**, sequenced so that each phase ships on its own.

1. **Close Phase 12 first.** Run the pending human UAT and record one real-project `app-verify.py` run. That evidence gates the last phase below.
2. **Phase 13, Subtract and Repair (S to M).**
   - Ship the Prime Directive in Claude Code installs, and generate the CLAUDE.md block from the command registry.
   - Run `pytest` and the bash tests in CI.
   - Stop shipping dormant staging machinery.
   - Delete the lean siblings.
   - Retire ADR-025 and its no-op emits.
   - Strip Writ-internal references from shipped commands.
   - Replace the highest-churn literal pins with structural checks.
   - Restart the phase-close leanness audit.
3. **Phase 14, Front Door and Distribution (M to L).**
   - Add a front-door command that restates noisy requests, classifies them, routes to the existing command at the right ceremony, mirrors that command's phases in the todo list with `skip: <reason>`, and sends empirically answerable forks to `/prototype`.
   - Ship plugin distribution for Cursor and Claude Code, with scripts inside the plugin.
   - Generate per-platform trees, and fail CI on an unmapped platform term.
   - Write a short prompting guide.
4. **Phase 15, Code-Level Rigor (M).**
   - Add `/why`: ledger first, then git, then MCPs, with confidence tiers and Preserve / Change / Avoid / Risk output.
   - Make Gate 0 usage-first with two sketches on the boundary-crossing route.
   - Add a blast-radius safety fact at Gate 2.5 on the review-agent route.
   - Add a bug path that commits a failing repro before the fix.
   - Add lead-judgment filters to the reviewers.
   - Give `/retro` `correct`'s fix order and rule table.
   - Each upgrade carries a removal measurement against the Phase 11 baseline set.
5. **Phase 16, Verified Landing (M, gated on step 1).**
   - Add a read-only `pr-ready.py` with typed blockers.
   - Add a verification ledger keyed by PR, head SHA, and patch-id.
   - Add a `/ship` watch mode that drives a PR to merge-ready and never merges.
   - Write a new ADR on whether autonomous PR open belongs inside `--recommend`.

**If Option B is too large:** do Phase 13 and the plugin half of Phase 14, and add `/why` as an inter-phase spec. That captures the parity fix and the highest-fit idea.

---

## Risks and Mitigation

| Risk | Mitigation |
|---|---|
| The front door becomes a 33rd command that nobody starts with | It routes only to existing commands and replaces the README command table as the documented start. If the maintainer still starts with direct commands after one phase, remove it. |
| Plugin distribution cannot scaffold `.writ/` or run Python scripts | `/initialize` scaffolds `.writ/`. Scripts stay stdlib Python 3.9 and are addressed by plugin-relative path. Keep `install.sh` until plugin parity is proven on both platforms. |
| Verified landing erodes accountability | Merge stays a human act. The SHA binding is a script check, not prose. The phase does not start until Phase 12 evidence exists. |
| Code-level rigor adds spawns and cost | Runs only on routes ADR-023 triage rates high-stakes. Each upgrade carries a keep-or-remove measurement. |
| Chasing pstack's cadence | pstack is one author's daily tool, built on Cursor-only infrastructure. Writ borrows mechanisms, not pace or style. |
| Subtraction breaks literal eval pins | Do the cuts in one spec and update the eval in the same commits. |

---

## Further Research

1. **Claude Code plugin format.** Can a plugin ship Python scripts, agents with frontmatter, and commands, and address scripts by plugin root? Needed before Phase 14 commits to plugins.
2. **Cross-vendor subagents in Claude Code.** If they become available, the review panel and `architect`-style sketches stop being Cursor-only.
3. **pstack's generator.** Read only through git objects in this pass. Read the full generator before copying its checks.
4. **pstack formal verification.** Two days old at the time of reading. Revisit in November 2026.
5. **Field evidence for pstack's autopilot.** No public measurements were found. Treat its unattended landing as a design reference, not as proof.

---

## Sources

**pstack** (all under https://github.com/cursor/plugins/tree/main/pstack, read at `d457567`):
- `README.md`, `plugin.json`, `.cursor-plugin/plugin.json`
- `skills/poteto-mode/SKILL.md`, `skills/poteto-mode/playbooks/*.md` (23 files), `skills/poteto-mode/references/bugbot-triage.md`
- `skills/poteto-mode/scripts/check-plan.mjs`, `orch/store.ts`, `orch/orch.ts`, `watch-pr/*.ts`, `worktree-audit.sh`, `bootstrap.ts`
- `skills/{architect,arena,swarm,interrogate,blast-radius,tdd,benchmark-checklist,no-comments}/`, `agents/comment-sicko.md`, `agents/poteto-agent.md`
- `skills/{create,maintain}-verification-skill/`, `skills/{create,maintain}-formal-verification-skill/`
- `skills/{how,why,teach,recall,ketchup,in-your-own-words,sharpen,bro}/`
- `skills/{reflect,correct,automate-me,figure-it-out,show-me-your-work,setup-pstack,poteto-help,unslop,technical-writing,make-bot-ui}/`
- `skills/principle-*/SKILL.md` (24 files)
- `docs/guide/*.md`, `docs/harness/claude-code.md`, `automations/benny/**`
- Repository root, read from git objects: `harness/pstack/README.md`, `scripts/generate-pstack-harness-trees.mjs`
- Commit history: `gh api repos/cursor/plugins/commits?path=pstack` (145 commits, 2026-05-23 to 2026-10-19)

**Writ** (this repository):
- `.writ/product/mission.md`, `roadmap.md`, `2026-09-05-goldilocks-assessment.md`
- `.writ/decision-records/adr-010`, `013`, `018`, `022`, `023`, `024`, `025`, `027`, `028`, `029`
- `commands/*.md`, `agents/*.md`, `claude-code/`, `adapters/*.md`, `skills/`
- `scripts/install.sh`, `scripts/eval.sh`, `scripts/eval-leanness.py`, `scripts/recommend-state.py`, `.github/workflows/eval.yml`
- `.writ/decision-log.md`, `.writ/leanness-baseline.json`, `.writ/issues/`
- `README.md`
