# Writ — Product Mission

> Created: 2026-02-27
> Last Updated: 2026-03-22
> Status: Planning
> Contract Locked: ✅

## Pitch

Writ is an elegant development workflow that gives solo builders the engineering discipline of a great team — clear steps, firm boundaries, and consistent outcomes that turn AI speed into AI quality.

AI coding tools made generating code trivially easy and building good software harder. Writ provides the discipline layer: structured pipelines, specialized agents, quality gates, and adaptive ceremony that right-sizes process to the work. The result is high-quality, efficient, and consistent outcomes for the products being created with it.

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

### Methodology, Not Just Tooling

Unlike AI dev tools that provide CLI commands or API wrappers, Writ provides a *way of thinking* about building with AI. The markdown-as-instructions approach means it works on any platform (Cursor, Claude Code, OpenClaw) without lock-in. As platforms add native features, Writ adapts to use them rather than competing with them.

### Adaptive Ceremony

Unlike rigid pipelines that apply the same process to every change, Writ right-sizes ceremony to the work. A prototype spike gets lightweight treatment. A core feature gets the full 6-gate pipeline. The framework suggests the appropriate level, not one-size-fits-all.

### Self-Correcting Pipeline

Unlike pipelines that hard-fail when reality diverges from plan, Writ's tiered spec-healing responds proportionally. Small deviations auto-heal. Medium deviations get flagged for review. Large deviations pause the pipeline. The process adapts to reality instead of pretending the plan was perfect.

### Clear Steps, Firm Boundaries

Unlike flexible-but-vague AI workflows, Writ defines explicit steps with firm boundaries at every stage. Each command has a clear entry point, structured phases, and a defined exit. Agents know exactly what they're responsible for and when to hand off. The result is predictable, repeatable quality — not brilliant one day and embarrassing the next.

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

> **Note:** A separate product extension for skill-based automation, self-improving agents, and advanced delegation will be pursued independently.
