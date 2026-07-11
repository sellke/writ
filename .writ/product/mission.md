# Writ — Product Mission

> Created: 2026-02-27
> Last Updated: 2026-07-11
> Status: Active
> Contract Locked: ✅ (2026-07-10 strategic refresh — see ADR-010, ADR-011, ADR-012, ADR-013)

## Pitch

Writ is the thin, portable methodology layer on top of increasingly capable AI harnesses. It owns the durable contracts of software development — specs, drift logs, decisions, knowledge, phase state — and delegates the mechanics (context management, subagent plumbing, browsing, retrieval) to whatever platform is underneath. The result is code, methodology, and accumulated knowledge that don't degrade as the project, team, or AI platform changes around them.

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
  - Opaque, unbounded agent loops produce volume without accountability; autonomy needs observable evidence and an immutable production boundary
- **Goals:** Ship with confidence, not hope. Walk away from a running phase and come back to reviewable results. Spend time on hard problems, not rework.

**The Framework Tinkerer** (secondary)
- **Role:** Developer who loves process tools and methodology
- **Context:** Tries every new dev framework. Evaluates Writ against velocity-first alternatives (GStack) and memory platforms (GBrain).
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

**Our Solution:** Writ provides the contract layer — contract-first specs, a gated implementation pipeline, proportional drift healing, bounded recommended delivery, normal phase-level orchestration, and a consolidating knowledge ledger — all in plain markdown on git, adapted to each platform rather than competing with it. As harnesses absorb mechanics, Writ sheds them and concentrates on what compounds.

## Differentiators

### Non-Degrading by Construction

Plain-text artifacts in git mean specs, decisions, and lessons are reviewable forever. The drift log means intent and implementation reconcile rather than diverge silently. The adapter abstraction means a Writ project survives AI tool churn. The knowledge ledger *consolidates* — merge, never append — so accumulated context stays sharp instead of rotting. Six months from now, the contributor reading the codebase — even a future version of yourself — finds context, not mystery. ([ADR-006](../decision-records/adr-006-non-degrading-destination.md), [ADR-008](../decision-records/adr-008-spec-as-team-contract-moat.md))

### The Contract Layer, Not Another Harness

Unlike frameworks that ship daemons, browsers, or databases, Writ is markdown, git, and thin scripts. It rides *on top of* native harness capabilities — native memory, native skills, native subagents — and interoperates with external brains (GBrain via MCP) rather than re-implementing them. Markdown is the canonical system of record; every index over it is optional and disposable. ([ADR-011](../decision-records/adr-011-memory-interop-markdown-canonical.md))

### Observable Autonomy, Deliberately Bounded

Normal `/implement-phase` runs an entire roadmap phase after one confirmation — fresh context per spec, quarantine branching on failure, User Challenge framing, and an honest completion report with UAT plans. Separately, commands that explicitly support `--recommend` may carry one locked spec through observable, resumable delivery to one explicit production approval bound to the reviewed PR head SHA. Opaque unbounded loops remain out of scope: accountability, not volume, is the product. ([ADR-013](../decision-records/adr-013-recommended-autonomous-delivery.md))

### Self-Improvement With Evidence

The learning loop is falsifiable, not anecdotal. `/refresh-command` refinements must cite transcript evidence and pass eval checks before merging. Skills carry a lifecycle — candidate → proven → promoted — with the evidence recorded. Drift logs feed the knowledge ledger. The methodology improves the way the code does: through gates.

### Adaptive Ceremony

A prototype spike gets lightweight treatment (`/prototype`). A core feature gets the full gated pipeline. A roadmap phase gets supervised orchestration. The framework right-sizes process to the work, and suggests the appropriate level.

### Clear Steps, Firm Boundaries

Every command has explicit phases, defined handoffs, and predictable outcomes. Agents know exactly what they're responsible for and when to stop. The result is repeatable quality — not brilliant one day and embarrassing the next.

## What Writ Is Not Building

- **Not an opaque, unbounded loop runner.** Ralph-style iteration is deprecated. Normal `/implement-phase` remains session-bound and single-confirmation; explicitly supported single-spec `--recommend` delivery uses observable state and one SHA-bound production approval. Multi-spec recommend mode remains excluded, per ADR-013.
- **Not a memory database or retrieval engine.** Markdown in git is the canonical knowledge substrate ([ADR-005](../decision-records/adr-005-knowledge-substrate-markdown-over-database.md)). External indexes — native harness memory, GBrain, anything else — are welcome *consumers* of that substrate via documented integration, never the system of record.
- **Not a velocity-first sprint flow.** Writ trades raw shipping speed for durability. Parallel-sprint frameworks (GStack) target a different problem.
- **Not a browser daemon or tool-specific runtime.** Writ uses the platform's native browser and tools through adapters.
- **Not a SaaS or hosted service.** Markdown, git, and shell scripts. No accounts, no servers, no telemetry.

## Key Features

### The Proven Core (shipped, load-bearing)

- **Contract-first specs (`/create-spec`):** Plan Mode discovery, negotiated contract, story decomposition — the expensive thinking happens before code.
- **Gated implementation (`/implement-story`, `/implement-spec`):** Architecture check, coding, review, testing, docs — with tiered spec-healing when reality diverges from plan.
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

### Phase 8 — Memory Interop (implemented — pending validation)

- **GBrain compatibility recipe:** Register `.writ/` as a GBrain source; map knowledge, specs, and ADRs to page types; brain-first retrieval guidance when a brain is detected. Zero new Writ infrastructure; graceful absence when GBrain isn't installed.
- **Native-memory guidance per adapter:** How Writ's ledger relates to Cursor memories, Claude Code memdir, and other native layers — the ledger is the reviewable layer that feeds them.

### Next Horizon

No committed phase is in flight — Phases 6–8 shipped the 2026 harness-audit strategy (supervised autonomy, evidence-based self-improvement, consolidating memory with external interop). The next candidates live in the roadmap parking lot (cross-project learning corpus, `/design` modernization, eval Tier 2 expansion), pulled forward only on concrete signal.

> **Parking lot:** Cross-project learning corpus, autonomous refactoring, team affordances (cross-dev drift reconciliation, `/review-spec`) — deferred until concrete signal per [ADR-007](../decision-records/adr-007-team-audience-sequencing.md).
