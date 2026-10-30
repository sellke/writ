# Writ — Product Mission

> Created: 2026-02-27
> Last Updated: 2026-10-30
> Status: Active
> Contract Locked: ✅ (2026-07-10 strategic refresh — see ADR-010, ADR-011, ADR-012, ADR-013; 2026-10-20 refresh — see [ADR-030](../decision-records/adr-030-contract-verifier-boundary-front-door.md))
> Last Revision: 2026-10-30 — reconcile pass after `/implement-phase 15`: Phases 14 and 15 recorded as implemented and pending human validation, both unmerged; PR #62 recorded as open, so the Phase 13 regression fix is not in `main`; Phase 12 UAT counted (3 of 89 run); the land-and-validate queue named as the current work; Design Principle 8 (land before you add) added as an [ADR-030](../decision-records/adr-030-contract-verifier-boundary-front-door.md) amendment.
>
> Earlier revision: 2026-10-22 — reconcile pass after Phase 13's human UAT: Phase 13 recorded as shipped in v0.43.0 and closed, with 173 of 176 UAT scenarios passing and the one regression fixed in PR #62. No new ADR.
>
> Earlier revision: 2026-10-21 — reconcile pass after `/implement-phase 13`: Phase 13 recorded as implemented, pending human UAT; `claude-agent-generator` recorded as inter-phase work; `/writ-design` and Claude Code's native `/design` stated as separate commands, with a matching non-goal.
>
> Previous revision: 2026-10-20 — **direction change** after the first full pstack comparison ([research](../research/2026-10-19-writ-vs-pstack-research.md)), recorded in [ADR-030](../decision-records/adr-030-contract-verifier-boundary-front-door.md):
> - Writ owns the contract, the verifier, and the boundary, and users reach it through one front door.
> - Phases 13–16 are committed.
> - `/prototype` is described as the exploration workflow (PR #59).
> - Friction signals are retired.
> - Two non-goals are added.
>
> Builds on the 2026-10-19 reconcile pass after v0.41.0.

## Pitch

Writ is the thin, portable methodology layer on top of increasingly capable AI harnesses. It owns the durable contracts of software development — specs, drift logs, decisions, knowledge, phase state — and delegates the mechanics (context management, subagent plumbing, browsing, retrieval) to whatever platform is underneath. The result is code, methodology, and accumulated knowledge that don't degrade as the project, team, or AI platform changes around them.

**Writ owns three things and delegates or deletes the rest** ([ADR-030](../decision-records/adr-030-contract-verifier-boundary-front-door.md)):

- **The contract:** the spec, its acceptance and exit criteria, and the stakes of each decision.
- **The verifier:** scripts that re-derive verdicts about the code and the running app, not only about Writ's own artifacts.
- **The boundary:** what an agent may not do without a human.

Users reach all three through one front door. It restates the request, classifies it, and routes it to the command whose ceremony fits.

> **"Thin" is an aspiration this document must keep earning — and Phase 10 changed how it is measured.** The 2026-08-11 alarm (516KB of command prose ≈ 129k tokens) was largely a measurement artifact: no invocation loads the directory. The worst real invocation is 77,669 bytes (~19.4k tokens), 7.2× smaller, now measured by `scripts/measure-invocation.py`. The deeper finding is that bytes measure the wrong quantity — the aim is economy of *steps and decisions to reach exit criteria*, and where the two diverge, bytes point the wrong way. Per [ADR-023](../decision-records/adr-023-stakes-proportional-diligence.md), "thin" is governed by stakes-proportional diligence per decision, assessed per-invocation, with **no mechanically enforced efficiency constraint** — a deliberate cost: an unenforceable true rule beat an enforceable wrong one. Bytes remain measured as drift signal only.

AI coding tools made generating code trivially easy and building durable software harder. In 2026 the harnesses themselves are strong: native memory, native skills, native subagents, native planning modes. What no harness provides is the **negotiated contract layer** — the structured agreement about what gets built, how deviations reconcile, and how knowledge compounds. Writ is that layer, in plain markdown, on git, portable across every platform.

## Users

### Primary Customers

**Solo builders shipping real products with AI.** They use Cursor, Claude Code, Codex, or similar tools daily. They've experienced the pain firsthand: AI generates code fast, but the product still breaks at integration, drifts from intent, skips edge cases, and accumulates debt faster than they can pay it down. There's no team to catch these problems — every failure lands on one person.

### User Personas

**The Ambitious Solo Builder** (25-45)
- **Role:** Independent developer, technical founder, or senior dev working solo on a meaningful project
- **Context:** Building a real product (not a toy) with AI coding tools. Shipping to users who expect reliability.
- **Pain Points:**
  - AI-generated code works in isolation but breaks at integration
  - Specs become fiction as implementation reveals complexity — no structured way to reconcile
  - Native harness memory captures preferences and trivia, not negotiated decisions and their rationale
  - Six months later, returning to a feature shipped last quarter, even the original developer struggles to reconstruct *why* a decision was made
  - Quality is inconsistent — sometimes brilliant, sometimes embarrassing
  - Opaque, unbounded agent loops produce volume without accountability; autonomy needs observable evidence and a human-owned production boundary
  - A framework with dozens of commands has to be learned before it helps; the first task should take one command
- **Goals:** Ship with confidence, not hope. Walk away from a running phase and come back to reviewable results. Spend time on hard problems, not rework.

**The Framework Tinkerer** (secondary)
- **Role:** Developer who loves process tools and methodology
- **Context:** Tries every new dev framework. Evaluates Writ against velocity-first alternatives (GStack), memory platforms (GBrain), and rigor skill packs (pstack).
- **Pain Points:** Most AI dev frameworks are tool-centric (CLIs, daemons, databases) rather than methodology-centric
- **Goals:** Find the "right way" to work with AI agents. Contribute improvements back.

## The Problem

### The Harness Got Smart. The Contract Layer Is Still Missing.

The 2024–2025 framing — "AI agents are brilliant juniors who need structure" — is now only half true. Modern harnesses natively handle todo tracking, planning modes, subagent orchestration, skill loading, semantic codebase indexing, and session memory with maintenance loops. Frameworks that re-implement those mechanics are depreciating assets.

What remains unsolved, and what no harness ships:

1. **No negotiated contract before code.** Harnesses execute; they don't force the expensive thinking to happen while changes cost nothing. Intent lives in chat scrollback, which evaporates.

2. **No structured reconciliation when reality diverges from plan.** The coder adapts silently, the spec becomes fiction, and native memory faithfully remembers the fiction.

3. **Autonomy without accountability.** Opaque, unbounded agent loops produce work faster than humans can meaningfully review it. Bounded delivery must remain observable, resumable, auditable, and explicitly approved at production.

4. **Memory that accumulates instead of compounding.** Native memory and brain layers capture facts, but an append-only store degrades — duplicates, contradictions, and stale entries pile up unless something consolidates them. And knowledge trapped in a database can't be reviewed in a PR.

5. **Platform churn erodes methodology.** Teams that encode their workflow in one tool's proprietary config rebuild it when the tool changes. The industry consensus now matches Writ's founding bet: the portable layer (plain files, git, conventions, CI checks) is the durable investment; tool-specific scaffolding is the disposable one.

**Our Solution:** Writ provides the contract layer — contract-first specs, a gated implementation pipeline, proportional drift healing, bounded recommended delivery, normal phase-level orchestration, and a consolidating knowledge ledger — all in plain markdown on git, adapted to each platform rather than competing with it, and reached through one front door. As harnesses absorb mechanics, Writ sheds them and concentrates on what compounds.

## Differentiators

### Non-Degrading by Construction

Plain-text artifacts in git mean specs, decisions, and lessons are reviewable forever. The drift log means intent and implementation reconcile rather than diverge silently. The adapter abstraction means a Writ project survives AI tool churn. The knowledge ledger *consolidates* — merge, never append — so accumulated context stays sharp instead of rotting. Six months from now, the contributor reading the codebase — even a future version of yourself — finds context, not mystery. ([ADR-006](../decision-records/adr-006-non-degrading-destination.md), [ADR-008](../decision-records/adr-008-spec-as-team-contract-moat.md))

### The Contract Layer, Not Another Harness

Unlike frameworks that ship daemons, browsers, or databases, Writ is markdown, git, and thin scripts. It rides *on top of* native harness capabilities — native memory, native skills, native subagents — and interoperates with external second brains (GBrain via MCP is the worked example) rather than re-implementing them. Markdown is the canonical system of record; every index over it is optional and disposable. ([ADR-011](../decision-records/adr-011-memory-interop-markdown-canonical.md)) The interop is being generalized from one vendor to engine detection — tracked in [`2026-10-03-generalize-second-brain-retrieval`](../issues/improvements/2026-10-03-generalize-second-brain-retrieval.md).

Skill packs are the other neighbor. pstack, for example, makes each agent rigorous: it explores designs, runs cross-model review, and verifies against the running app. It keeps no record of what was agreed before code. Writ keeps the project's intent and checks the result against it, across sessions, agents, and platforms. The two can run in the same project.

### Observable Autonomy, Deliberately Bounded

Normal `/implement-phase` runs an entire roadmap phase after one confirmation — fresh context per spec, quarantine branching on failure, User Challenge framing, and an honest completion report with UAT plans. Separately, `--recommend` adds evidence-backed autonomy on two commands: `/create-spec --recommend` authors and locks a spec package from evidence and then stops, and `/implement-phase --recommend` runs the phase as an end-to-end loop that also authors any missing specs. Both end at their normal terminal scope — neither merges, opens PRs, nor releases. Opaque unbounded loops remain out of scope: accountability, not volume, is the product. ([ADR-013](../decision-records/adr-013-recommended-autonomous-delivery.md)) The ceiling moves only on evidence: machine-verified UAT is the named precondition, and Phase 12 builds the verifier that would produce it ([ADR-028](../decision-records/adr-028-behavioral-verification-and-cross-family-panels.md)). Phase 16 evaluates verified landing once Phase 12's human UAT passes. It adds a PR-readiness check and a verification ledger bound to the PR head SHA. Merge stays a human act unless Phase 16's own ADR moves it ([ADR-030](../decision-records/adr-030-contract-verifier-boundary-front-door.md)).

### Self-Improvement With Evidence

The learning loop is falsifiable, not anecdotal. `/refresh-command` refinements must cite transcript evidence and pass eval checks before merging. `/retro` reads the agent transcripts of a run and proposes fixes to the *environment* — steering files, navigation hints, lint rules, docs — never to the code, with every finding cited to a transcript path and an observable signal (v0.41.0; [ADR-025](../decision-records/adr-025-friction-signals.md) amendment). Skills carry a lifecycle — candidate → proven → promoted — with the evidence recorded. Drift logs feed the knowledge ledger. The methodology improves the way the code does: through gates.

Phase 15 gives `/retro` a fix order: architecture first, then types, then a lint whose error names the fix, then a test, and docs last. Each new check must fail on a real past mistake, and a table pairs every rule with what enforces it. Friction signals are retired, because the transcript review covers their purpose ([ADR-030](../decision-records/adr-030-contract-verifier-boundary-front-door.md)).

### Adaptive Ceremony

An unsettled idea gets explored in `/prototype`, which is now the exploration workflow (PR #59, v0.42.0). It produces a few code-portable drafts on declared axes, records the choice and why each rejected draft lost, then builds the chosen direction or hands it to `/create-spec --from-prototype`. A small change runs through the same command with divergence off. A core feature gets the full gated pipeline. A roadmap phase gets supervised orchestration.

Today the user picks the level. Phase 14's front door picks it for them: it restates the request, classifies it, routes it, and sends any fork that running something could answer to `/prototype` instead of a question.

### Clear Steps, Firm Boundaries

Every command has explicit phases, defined handoffs, and predictable outcomes. Agents know exactly what they're responsible for and when to stop. The result is repeatable quality — not brilliant one day and embarrassing the next.

## What Writ Is Not Building

- **Not an opaque, unbounded loop runner.** Ralph-style iteration is deprecated. Normal `/implement-phase` remains session-bound and single-confirmation; `--recommend` adds evidence-backed autonomy on `/create-spec` (author and stop) and `/implement-phase` (end-to-end phase loop), both ending short of merge/PR/release. Autonomous production delivery remains excluded, per ADR-013.
- **Not a memory database or retrieval engine.** Markdown in git is the canonical knowledge substrate ([ADR-005](../decision-records/adr-005-knowledge-substrate-markdown-over-database.md)). External indexes — native harness memory, GBrain, anything else — are welcome *consumers* of that substrate via documented integration, never the system of record.
- **Not a velocity-first sprint flow.** Writ trades raw shipping speed for durability. Parallel-sprint frameworks (GStack) target a different problem.
- **Not a browser daemon or tool-specific runtime.** Writ uses the platform's native browser and tools through adapters.
- **Not a SaaS or hosted service.** Markdown, git, and shell scripts. No accounts, no servers, no telemetry.
- **Not a personal style pack.** Writ ships methodology, not one author's taste as universal rules. Punctuation bans and file-length vetoes are project choices, not Writ rules.
- **Not a wrapper over platform design tools.** `/writ-design` stays a separate command from Claude Code's native `/design`, and neither delegates to the other. `/prototype` may render its drafts on a platform's own design surface. That is `/prototype`'s choice of renderer and does not involve `/writ-design`.
- **Not a cross-vendor model router by default.** Agents stay family-locked ([ADR-024](../decision-records/adr-024-model-delegation.md)). Other vendors enter only as an opt-in review panel ([ADR-028](../decision-records/adr-028-behavioral-verification-and-cross-family-panels.md)).

## Key Features

### The Proven Core (shipped, load-bearing)

- **Contract-first specs (`/create-spec`):** Plan Mode discovery, negotiated contract, story decomposition — the expensive thinking happens before code.
- **Gated implementation (`/implement-story`, `/implement-spec`):** By default one coding agent and a fresh-context evaluator, with script-backed gates (build, tests, coverage, boundary crossings, drift) re-deriving the verdicts; the six-agent pipeline is the explicit `--full-pipeline` path. Tiered spec-healing when reality diverges from plan.
- **Issue capture (`/create-issue`), shipping (`/ship`), verification (`/verify-spec`), disciplined refactoring (`/refactor`):** The workflow from idea to merged PR with no manual gaps.
- **System instructions + Prime Directive:** The behavioral contract that sets every session on the right foot — identity, anti-sycophancy hard constraints, auto-orientation.

### Phase 6 — Autonomy Ceiling (✅ shipped, v0.19.0)

- **`/implement-phase` hardening:** Fresh context per spec, quarantine branching on failure, User Challenge framing for mid-run scope decisions, `dependencies:` spec frontmatter for deterministic sequencing, knowledge writeback at phase close.
- **Ralph deprecation:** The bash loop retires; its durable inventions (state schema rigor, escalation semantics, quarantine branches) live on inside `/implement-phase`.
- **`/status` health line:** One-line production-grade summary derived from existing checks (eval Tier 1, `/verify-spec`, drift logs).

### Phase 7 — Compounding Layer (✅ shipped, v0.19.0)

- **Skill lifecycle:** candidate → proven → promoted, with evidence recorded; 3–5 extractions from the highest-traffic commands.
- **Evidence-bound `/refresh-command`:** Refinements cite transcript evidence and pass evals before merging.
- **Knowledge consolidation:** Merge duplicates, surface contradictions, prune stale entries — markdown in, markdown out, reviewable in PRs.

### Phase 8 — Memory Interop (✅ shipped, v0.20.0)

- **GBrain compatibility recipe:** Register `.writ/` as a GBrain source; map knowledge, specs, and ADRs to page types; brain-first retrieval guidance when a brain is detected. Zero new Writ infrastructure; graceful absence when GBrain isn't installed. *(v0.41.0: the `gbrain-interop` skill was removed — it had no consumers. `.writ/docs/gbrain-recipe.md` remains and the adapters link it; a provider-neutral replacement is an open issue.)*
- **Native-memory guidance per adapter:** How Writ's ledger relates to Cursor memories, Claude Code memdir, and other native layers — the ledger is the reviewable layer that feeds them.

### Phase 9 — Git-Native Provenance & Recovery (✅ shipped, v0.23.0)

- **Git-notes audit channel:** Audit trail written to `git notes`, not a parallel ledger — provenance lives where the code lives.
- **Logical-unit revert:** `/revert` unwinds a story or a whole spec as a coherent unit, restoring Writ artifacts alongside the code.
- **Artifact-integrity handshake:** Commands verify declared Required Artifacts before doing work — HALT on required-missing, degraded mode on optional-missing.

### Phase 10 — Component Contract & Progressive Disclosure (◐ partially complete, v0.29–0.30)

- **Component contract (✅ shipped):** 31/31 commands and 7/7 agents declare `problem` / `outcome` / `exit_criteria`; all 31 commands carry `## Completion`. Machine-checked as blocking `structural` eval checks, proven to bite by mutation.
- **Loop bounds (✅ shipped):** All 5 loop-bearing commands declare `max_iterations` + `on_exhaustion` (was 0 of 5), each citing calibration evidence.
- **Autonomy gate classes (✅ shipped):** The gate-class table in `_preamble.md` — human gates only for product/spec direction, the production boundary, and design/UX taste ([ADR-022](../decision-records/adr-022-autonomy-gate-classes.md)).
- **Progressive disclosure (✗ stopped on evidence):** One command converted (`implement-story`, floor −35.9%); the pilot measured ~1,017 B irreducible overhead per skill and a +9.7% worst-path regression, and `required_skills:` turned out to pre-load eagerly rather than on demand. Five sibling specs closed unimplemented, contracts kept as design records.
- **The byte budget (✗ withdrawn, not deferred):** The absolute budget shipped non-blocking, then [ADR-023](../decision-records/adr-023-stakes-proportional-diligence.md) voided it — bytes measure file size, not the stated aim of step economy. No number replaces it.

### Phase 11 — Contract-and-Verifier Layer (✅ shipped, v0.36.0)

- **Pruned base:** `system-instructions.md` + `_preamble.md` under 10 KB; every cut recorded in an append-only ledger and kept only after a baseline re-run ([ADR-026](../decision-records/adr-026-constraint-test-pruning.md)).
- **Mechanized gates:** eight of ten `/implement-story` gates re-derive their verdict from a script; Gate 1 and Gate 4.5 stay `prose-only`. *(Historical, true at Phase 11 close. Phase 12 made Gate 4.5 behavioral verification: it still declares `prose-only`, but the verdict now comes from `scripts/app-verify.py`, and `implement-story.md` carries one `prose-only` declaration, not two.)*
- **Spec analysis:** `spec-analyze.py` flags contradictory, missing, and ambiguous acceptance criteria at lock; advisory.
- **Escalation, not default:** two-agent default pipeline; Goal Cards emit platform-runnable `/goal` contracts.

### Phase 12 — Behavioral Verification (◐ implemented and released, v0.40.0 — human UAT open, 3 of 89 scenarios run)

- **Behavioral verification:** a per-project recipe (`.writ/docs/app-verification.md`, drafted by `/create-uat-plan`) names the project's own checks; UAT scenarios cite its feature IDs; Gate 4.5 runs the checks against the running app, records evidence, and leaves `prose-only`. An exit code decides, never an agent.
- **Cross-family review panel:** opt-in, high-stakes only; findings raised by two or more vendors block. Kept only if it catches what the single-vendor evaluator misses ([ADR-028](../decision-records/adr-028-behavioral-verification-and-cross-family-panels.md)).

### Inter-phase — `/prototype` as Exploration (✅ shipped, v0.42.0, PR #59)

- **Exploration workflow:** `/prototype` opens with constructed divergence when there is UI surface or the direction is unsettled. It declares two or three orthogonal axes, runs one subagent per draft with no shared context, and caps at three code-portable drafts. It records the choice and why each rejected draft lost in `.writ/prototypes/<date>-<slug>/exploration.md`. A run that ends at a recorded choice with no code is complete. Rendering is delegated to the platform.
- **Consumer:** `/create-spec --from-prototype` reads the exploration record. The chosen draft becomes the Deliverable, and rejected drafts become a Directions Considered section.
- Evidence: [`2026-10-19-prototype-visual-drafts-research.md`](../research/2026-10-19-prototype-visual-drafts-research.md).

### Phase 13 — Subtract and Repair (✅ shipped, v0.43.0)

- **Repairs:**
  - Claude Code installs now carry the Prime Directive, and the `CLAUDE.md` block is generated from the manifest.
  - Install, update, and uninstall no longer delete or overwrite files the user wrote or customized, including `CLAUDE.md`.
  - CI runs `pytest` on the 3.9 floor and the bash tests.
  - `/design` is renamed `/writ-design`, so it no longer collides with Claude Code's native `/design`.
- **Cuts:** the lean siblings, the dormant staging machinery, the friction-signal no-op lines, and links to Writ's own history in shipped commands are gone. `eval.sh` literal pins on commands fell from 207 to 144. `create-spec.md` shrank from 54,264 to 38,562 bytes.
- All nine machine criteria pass, and 173 of 176 human UAT scenarios pass. One failure is tracked as an issue, two need OpenClaw, and the one regression UAT found is fixed on PR #62, which is still open, so the fix is not in `main`.

### Phases 14–16 ([ADR-030](../decision-records/adr-030-contract-verifier-boundary-front-door.md))

- **Phase 14, Front Door and Distribution (◐ implemented, pending human validation, PR #63 open):**
  - One entry command that restates, classifies, and routes.
  - Plugin distribution for Cursor and Claude Code, with scripts inside the plugin.
  - Generated per-platform trees, with a CI check that fails on any platform term an adapter does not map.
- **Phase 15, Code-Level Rigor (◐ implemented, pending human validation, branch only):**
  - `/why`, answering from Writ's ledger first.
  - A `design-divergence` skill shared by `/prototype` and a usage-first Gate 0, with a blind trial deciding whether it stays.
  - A blast-radius safety fact at Gate 2.5, repro-first bug fixing, reviewer judgment filters, and `/retro`'s fix ladder.
- **Phase 16, Verified Landing (📋 committed, gated):**
  - A read-only PR-readiness check, a verification ledger bound to the PR head SHA, and a `/ship` watch mode that drives a PR to merge-ready.
  - Starts after Phase 12's human UAT. Its own ADR decides the ceiling.

### Next Horizon

Phases 6–8 shipped the 2026 harness-audit strategy (supervised autonomy, evidence-based self-improvement, consolidating memory with external interop); Phase 9 made provenance and recovery git-native; Phase 10 made the surface deterministic and withdrew the byte goal ([ADR-023](../decision-records/adr-023-stakes-proportional-diligence.md)); Phase 11 moved quality guarantees from prose to scripts. **Phase 12 is implemented and released in v0.40.0:** Writ's verifiers so far checked Writ's own artifacts, and Phase 12 made one check the user's feature. Its three machinery criteria are met and the panel trial returned `keep`; the phase's own UAT plan is unticked, so human UAT is the open item, not more building. Inter-phase work since: `/retro` as a transcript review and the `gbrain-interop` removal (v0.41.0), and, in v0.42.0, the agent CLI contract ([ADR-029](../decision-records/adr-029-agent-cli-contract.md)) and `/prototype` as the exploration workflow (PR #59).

**Phase 13 shipped in v0.43.0 and closed after human UAT** (2026-10-22). The same release carries the `claude-agent-generator` spec (Claude Code agents generated from the canonical `agents/`). **Phases 14 and 15 are implemented and wait on human validation and merge; Phase 16 is committed and gated** ([ADR-030](../decision-records/adr-030-contract-verifier-boundary-front-door.md)). Nothing on the roadmap can start, so the current work is landing and validating what is built (the roadmap's *Current focus* section), under Design Principle 8: no new phase starts while two or more finished phases wait. Phase 13 subtracted and repaired before anything was added. Phase 14 gives Writ one front door and plugin distribution. Phase 15 extends the verifier from Writ's artifacts to the design and the fix. Phase 16 takes up verified landing once Phase 12's UAT gives it evidence.

> **Parking lot (kept as candidates):** cross-project learning corpus, `/writ-design` Mode A modernization, eval Tier 2 expansion, `/implement-phase` orchestration hygiene (pilot story, standing orders, brief template), a decision-trail review, a measured-performance workflow, and formal verification (watch only). **Promoted into Phase 14:** Cursor plugin distribution and the empirical-fork rule. **Retired:** friction signals ([ADR-030](../decision-records/adr-030-contract-verifier-boundary-front-door.md)). **Deferred until concrete signal:** team affordances (cross-dev drift reconciliation, `/review-spec`) per [ADR-007](../decision-records/adr-007-team-audience-sequencing.md); business-process sister pipeline. See the roadmap's *Beyond Phase 16* section for the authoritative list.
