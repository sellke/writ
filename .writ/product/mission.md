# Writ — Product Mission

> Created: 2026-02-27
> Last Updated: 2026-03-22
> Status: Planning
> Contract Locked: ✅

## Pitch

Writ is an elegant development workflow that gives solo builders the engineering discipline of a great team — clear steps, firm boundaries, and quality that doesn't degrade as the project, team, or AI platform changes around it.

AI coding tools made generating code trivially easy and building durable software harder. Writ provides the discipline layer: structured pipelines, specialized agents, quality gates, and adaptive ceremony that right-sizes process to the work. The result is code, methodology, and accumulated knowledge that hold up over time — across sessions, contributors, and the AI platforms that come and go.

## Users

### Primary Customers

**Solo builders shipping real products with AI.** They use Cursor, Claude Code, or similar tools daily. They've experienced the pain firsthand: AI generates code fast, but the product still breaks at integration, drifts from intent, skips edge cases, and accumulates debt faster than they can pay it down. There's no team to catch these problems — every failure lands on one person.

### User Personas

**The Ambitious Solo Builder** (25-45)
- **Role:** Independent developer, technical founder, or senior dev working solo on a meaningful project
- **Context:** Building a real product (not a toy) with AI coding tools. Shipping to users who expect reliability.
- **Pain Points:**
  - AI-generated code works in isolation but breaks at integration
  - Specs become fiction as implementation reveals complexity — no structured way to reconcile
  - Every session starts cold. The AI doesn't remember what worked last time.
  - Six months later, returning to a feature shipped last quarter, even the original developer struggles to reconstruct *why* a decision was made — and AI can't help reconstruct it either
  - Quality is inconsistent — sometimes brilliant, sometimes embarrassing
  - The overhead of "doing it right" feels like it cancels out the speed gains of AI
- **Goals:** Ship with confidence, not hope. Build a product they're proud to open-source. Spend time on hard problems, not rework.

**The Framework Tinkerer** (secondary)
- **Role:** Developer who loves process tools and methodology
- **Context:** Tries every new dev framework. Evaluates Writ against alternatives.
- **Pain Points:** Most AI dev frameworks are tool-centric (CLIs, APIs) rather than methodology-centric
- **Goals:** Find the "right way" to work with AI agents. Contribute improvements back.

## The Problem

### AI Made Code Easy and Software Hard

AI coding tools have a quality ceiling. Without external structure, they:

1. **Generate code that works in isolation but fails at integration.** The AI doesn't see the whole system. It solves the immediate problem without understanding how it connects.

2. **Drift from intent as complexity reveals itself.** The plan says one thing, implementation discovers another, and there's no structured way to reconcile them. The coder adapts silently, the spec becomes fiction.

3. **Skip quality steps unless forced.** Tests, security review, documentation, edge case handling — these aren't laziness, they're outside the AI's incentive structure. It optimizes for "done," not "done right."

4. **Never improve from past mistakes.** Every session is a fresh start. Patterns discovered in one project don't inform the next. The same mistakes repeat across sessions, projects, and contexts.

5. **Produce impressive demos and fragile products.** The gap between "it works on my machine" and "it works for users" widens as AI accelerates the first part without addressing the second.

**The result:** Developers ship faster in the small but spend *more* time debugging, refactoring, and fixing integration issues in the large. The net productivity gain is smaller than it appears.

**Our Solution:** Writ treats AI agents like brilliant junior engineers who need structure. It provides a complete development workflow — from product planning through release — designed specifically for how AI agents work: contract-first specs, separation of concerns across specialized agents, automated quality gates, and adaptive ceremony that matches process to change size. Clear steps and firm boundaries drive consistent, high-quality outcomes.

## Differentiators

### Non-Degrading by Construction

Unlike AI workflows where artifacts evaporate at session end and quality varies by prompt, Writ is built so the code, the specs, and the accumulated project knowledge survive. Plain-text artifacts in git mean specs and decisions are reviewable forever. The drift log means intent and implementation reconcile rather than diverge silently. The adapter abstraction means a Writ project survives the AI tool churn that breaks tool-specific workflows. Six months from now, the contributor reading the codebase — even if it's a future version of yourself — finds context, not mystery. The structural reason this is defensible against velocity-first AI dev frameworks: spec-as-team-contract on a plain-text + git substrate ([ADR-006](../decision-records/adr-006-non-degrading-destination.md), [ADR-008](../decision-records/adr-008-spec-as-team-contract-moat.md)).

### Methodology, Not Just Tooling

Unlike AI dev tools that provide CLI commands or API wrappers, Writ provides a *way of thinking* about building with AI. The markdown-as-instructions approach means it works on any platform (Cursor, Claude Code, OpenClaw) without lock-in. As platforms add native features, Writ adapts to use them rather than competing with them.

### Adaptive Ceremony

Unlike rigid pipelines that apply the same process to every change, Writ right-sizes ceremony to the work. A prototype spike gets lightweight treatment. A core feature gets the full 6-gate pipeline. The framework suggests the appropriate level, not one-size-fits-all.

### Self-Correcting Pipeline

Unlike pipelines that hard-fail when reality diverges from plan, Writ's tiered spec-healing responds proportionally. Small deviations auto-heal. Medium deviations get flagged for review. Large deviations pause the pipeline. The process adapts to reality instead of pretending the plan was perfect.

### Clear Steps, Firm Boundaries

Unlike flexible-but-vague AI workflows, Writ defines explicit steps with firm boundaries at every stage. Each command has a clear entry point, structured phases, and a defined exit. Agents know exactly what they're responsible for and when to hand off. The result is predictable, repeatable quality — not brilliant one day and embarrassing the next.

## What Writ Is Not Building

Some directions sound related but would compromise the destination. Naming them explicitly so the surface area stays focused:

- **Not a velocity-first sprint flow.** Writ trades raw shipping speed for durability. Frameworks optimized for parallel sprints (e.g., GStack-style multi-agent flows) target a different problem.
- **Not a persistent-database knowledge layer.** Knowledge lives in plain-text markdown in git ([ADR-005](../decision-records/adr-005-knowledge-substrate-markdown-over-database.md)). Reviewability and auditability are non-negotiable.
- **Not a browser daemon or tool-specific runtime.** Writ adapts to whatever AI platform you're on rather than competing with one.
- **Not a cross-AI orchestration layer.** Adapter abstraction handles platform portability. Multi-AI parallel coordination is out of scope.
- **Not a SaaS or hosted service.** Writ is markdown, git, and shell scripts. No accounts, no servers, no telemetry.

## Key Features

### Core Features (Phase 1 — Foundation)

- **`/prototype` command:** Lightweight execution mode for small changes. Right-sized ceremony without the full 6-gate pipeline. The biggest day-to-day friction reducer.
- **Tiered spec-healing:** When implementation reveals the spec was wrong, the pipeline self-corrects proportionally. Small deviations auto-heal with logged amendments. Medium deviations get flagged for post-implementation review. Large deviations pause the pipeline and surface the conflict for human decision.
- **`/refresh-command`:** The learning loop. After using a command, scan the thread, identify what worked and what was friction, propose amendments to the command file. Local-first: improvements land in the project's copy, with a promotion review process for upstreaming to Writ core.

### Growth Features (Phase 2 — Reach)

- **`/ship` command:** Unified shipping workflow from branch to PR — merge, test, commit splitting, structured PR body. Absorbs the PR agent concept.
- **Standalone `/review` command:** Pre-landing code review with error mapping, shadow path tracing, and failure modes registry.
- **`/retro` command:** Git-based retrospective with metrics, trend comparison, and persistent snapshots.
- **Enhanced error mapping in `/create-spec`:** Failure-aware specs with error & rescue maps, shadow paths, and interaction edge cases.

### Context Engine (Phase 3 — Intelligence)

- **Per-story context hints:** Story files index into full specs with `## Context for Agents` sections — which error map rows, shadow paths, business rules, and experience design elements are relevant to *this* story. Agents get targeted context, not everything or nothing.
- **"What Was Built" records:** After each story completes, a structured summary is appended to the story file. Downstream stories know exactly what their dependencies actually produced — files created, implementation decisions, error handling approach, test coverage.
- **Agent-specific spec views:** `spec-lite.md` restructured with labeled sections (`## For Coding Agents`, `## For Review Agents`, `## For Testing Agents`). Each agent gets exactly what matters to their role. Same <100 line budget, better targeting.
- **UAT plan generation:** Human-readable test scenarios generated from acceptance criteria, error maps, and shadow paths. Bridges the gap between "AI says it works" and "a human confirmed it works."

### Production-Grade Substrate (Phase 4 — Foundations)

Build the foundations the destination requires. Everything in this phase pays off for solo dev now AND sets up team-readiness later. Entry condition: Phase 1 features materially dogfooded and stable enough to build on; dogfooding continues indefinitely as an operating practice, not a one-time completion event.

- **Knowledge ledger (`.writ/knowledge/`):** Plain-text markdown directory accumulating cross-cutting conventions, lessons, glossary, and small decisions that don't fit specs/ADRs. Reviewable in PRs, versioned in git, survives platform churn. ([ADR-005](../decision-records/adr-005-knowledge-substrate-markdown-over-database.md))
- **`SKILL.md` template generation:** Auto-generates command/agent docs from a single source of truth so docs cannot drift from behavior.
- **Preamble enforcement for commands:** Standing instructions injected consistently so agents don't miss conventions across the surface area.
- **Eval Tier 1 (static checks for commands and agents):** Required-section validation, anti-sycophancy phrasing checks, broken-reference detection, length sanity. Cheap quality floor that catches regressions before release.
- **Spec frontmatter `owner:` field:** Seed of the team-readiness pattern at zero solo cost. Solo devs see their own name on every spec; the moment a teammate joins, the field is already there.

### Operationalize the Destination (Phase 5 — Make It Falsifiable)

Make the production-grade claim measurable, not aspirational. Lean into delight where it makes the destination *felt*.

- **`/audit` command:** Operationalizes the production-grade criteria (auditable, reviewable, reproducible, onboarding-friendly, failure-isolatable) as a checkable diagnostic with a numeric scorecard. Makes "production-grade" a thing you can measure, not a thing you can claim.
- **Spec-as-team-contract substrate (non-team parts):** Dependency block in spec frontmatter; status board across `.writ/specs/`. Foundations the team affordances will build on, useful to solo devs as project-management primitives in the meantime.
- **`/lessons` micro-command:** 30-second mid-flow capture of a learning to the knowledge ledger. Closes the gap between "noticed something" and "wrote it down."
- **`/status` shows a production-grade health score:** One-line scorecard at session start. Top gaps surfaced. Tangible feedback at every entry point.
- **Per-story production-grade scorecard:** Story completion shows numeric quality + drift summary. Quantifies the destination per shipped unit.
- **Drift entries can self-promote to lessons:** A `lesson: true` flag in a drift entry's frontmatter auto-creates a knowledge ledger entry. Closes the learning loop without ceremony.

> **Beyond Phase 5 (parking lot):** Cross-project learning corpus (Phase 6+ extension of the knowledge ledger), self-improving context routing (complements eval Tier 1), autonomous refactoring (long-horizon experimental). Multi-developer affordances (cross-dev drift reconciliation, `/review-spec`, multi-repo orchestration) are designed-on-paper but deferred-on-shipping until a concrete team-collaboration signal arrives — see [ADR-007](../decision-records/adr-007-team-audience-sequencing.md).
