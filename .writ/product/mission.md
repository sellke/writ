# Writ — Product Mission

> Created: 2026-02-27
> Status: Planning
> Contract Locked: ✅

## Pitch

Writ is a self-improving development methodology that gives solo builders the engineering discipline of a great team — adaptive enough to stay out of the way, intelligent enough to learn from every project.

AI coding tools made generating code trivially easy and building good software harder. Writ provides the discipline layer that turns AI speed into AI quality: structured pipelines, specialized agents, quality gates, and a learning loop that makes every project better than the last.

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

**Our Solution:** Writ treats AI agents like brilliant junior engineers who need structure. It provides a complete development methodology — from product planning through release — designed specifically for how AI agents work: contract-first specs, separation of concerns across specialized agents, automated quality gates, adaptive ceremony that matches process to change size, and a learning loop where commands improve through use.

## Differentiators

### Methodology, Not Just Tooling

Unlike AI dev tools that provide CLI commands or API wrappers, Writ provides a *way of thinking* about building with AI. The markdown-as-instructions approach means it works on any platform (Cursor, Claude Code, OpenClaw) without lock-in. As platforms add native features, Writ adapts to use them rather than competing with them.

### Adaptive Ceremony

Unlike rigid pipelines that apply the same process to every change, Writ right-sizes ceremony to the work. A prototype spike gets lightweight treatment. A core feature gets the full 6-gate pipeline. The framework suggests the appropriate level, not one-size-fits-all.

### Self-Correcting Pipeline

Unlike pipelines that hard-fail when reality diverges from plan, Writ's tiered spec-healing responds proportionally. Small deviations auto-heal. Medium deviations get flagged for review. Large deviations pause the pipeline. The process adapts to reality instead of pretending the plan was perfect.

### Compounding Intelligence

Unlike frameworks where every project starts from zero, Writ's `/refresh-command` loop means every use of the methodology improves the methodology. Commands refine through real-world use. Patterns discovered in one project inform the next. The framework gets smarter because you use it.

## Key Features

### Core Features (Phase 1 — Foundation)

- **`/prototype` command:** Lightweight execution mode for small changes. Right-sized ceremony without the full 6-gate pipeline. The biggest day-to-day friction reducer.
- **Tiered spec-healing:** When implementation reveals the spec was wrong, the pipeline self-corrects proportionally. Small deviations auto-heal with logged amendments. Medium deviations get flagged for post-implementation review. Large deviations pause the pipeline and surface the conflict for human decision.
- **`/refresh-command`:** The learning loop. After using a command, scan the thread, identify what worked and what was friction, propose amendments to the command file. Local-first: improvements land in the project's copy, with a promotion review process for upstreaming to Writ core.

### Growth Features (Phase 2 — Reach & Autonomy)

- **PR agent:** Automates the gap between "pipeline green" and "PR open." Structured PR descriptions linked to specs, test results, and coverage.
- **MCP integration points:** Agents can call external tools — browsers, databases, deployment APIs — when the methodology requires verification beyond file operations.
- **Skill system:** Reusable agent capabilities that persist and compound. Not one-off prompt instructions — encoded competence that agents carry across sessions.
- **Cross-project pattern extraction:** What `/refresh-command` does for single commands, this does across projects. Review patterns, common failures, and proven approaches feed back into agent prompts.

### Scale Features (Phase 3 — Intelligence)

- **Self-improving agent behaviors:** Agents that adjust their approach based on accumulated feedback. The coding agent that stops making the same mistake. The reviewer that learns what matters for *your* codebase.
- **Advanced delegation:** Agents that spawn sub-agents, coordinate parallel work, and manage their own task breakdown. More autonomy, less micromanagement.
- **Promotion pipeline:** Structured review process for graduating local command improvements to Writ core. The framework evolves through use.
