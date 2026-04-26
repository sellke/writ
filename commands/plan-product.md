# Plan Product Command (plan-product)

## Overview

Generate comprehensive product planning documentation using a contract-first approach that establishes clear product vision, mission, and roadmap before creating any supporting files. This command eliminates assumptions by gathering complete product context through structured discovery, then creates a complete product planning package for AI-assisted development.

## Invocation

- `/plan-product` — shape product mission, strategy, and roadmap artifacts through discovery

## Command Process

### Phase 1: Product Discovery & Contract Establishment (No File Creation)

**Mission Statement:**
> Your goal is to find the best possible version of a product idea and turn it into a comprehensive, actionable plan. You will deliver the complete product planning package only after we both agree on the product contract. **Don't just gather information — challenge the premise, push for the version that makes users' hearts sing, and surface the product that *should* exist.** It's better to discover the wrong framing early than build the wrong product well.

#### Step 1.1: Initial Context Scan

- Scan existing `.writ/product/` for any existing product documentation
- Load available project context from `.writ/docs/` (tech-stack.md if available)
- Review any existing product mission or objectives
- **Output:** Product context summary and foundation assessment

#### Step 1.1b: Product Direction (AskQuestion)

**If user didn't specify a clear product idea, use AskQuestion immediately:**

```
AskQuestion({
  title: "Product Planning - What are we building?",
  questions: [
    {
      id: "product_direction",
      prompt: "What kind of product are you envisioning?",
      options: [
        // Dynamically generate options based on existing codebase, .writ/product/, and project context
        { id: "option_1", label: "[Product type suggestion based on codebase/domain]" },
        { id: "option_2", label: "[Another relevant product direction]" },
        { id: "option_3", label: "[Third suggestion from roadmap/existing docs]" },
        { id: "other", label: "Something else (I'll describe it)" }
      ]
    }
  ]
})
```

If user selects "Something else", follow up with a free-text question to get their idea.

**If user already described the product idea clearly, skip this step.**

#### Step 1.1c: Planning Posture Selection (AskQuestion)

**Always present — this shapes the entire discovery conversation:**

```
AskQuestion({
  title: "Planning Posture",
  questions: [
    {
      id: "planning_posture",
      prompt: "What posture should I take for this product plan?",
      options: [
        { id: "expansion", label: "SCOPE EXPANSION — Dream big. Find the 10-star product hiding in this idea." },
        { id: "hold", label: "HOLD SCOPE — Your framing is right. Pressure-test it for gaps and make it bulletproof." },
        { id: "reduction", label: "SCOPE REDUCTION — Strip to the absolute minimum that delivers core value." }
      ]
    }
  ]
})
```

**How posture shapes everything downstream:**
- **EXPANSION:** Challenge whether the vision is ambitious *enough*. Ask "what's the version that's 10x more ambitious for 2x the effort?" Look for delight opportunities — adjacent 30-minute improvements that make the product sing. Push scope *up*, not just down. Dream State Mapping is mandatory.
- **HOLD:** The user's framing is roughly correct. Focus on pressure-testing assumptions, finding gaps, validating feasibility. This is the classic Writ discovery flow — thorough, balanced, critical.
- **REDUCTION:** Ruthlessly strip features. Every feature must justify its existence against "could we launch without this?" The goal is the smallest thing that proves the core value proposition.

The posture is a commitment — once selected, fully adopt that lens for the entire discovery and contract phase.

#### Step 1.2: Switch to Plan Mode for Product Discovery

**After context scan and initial product direction selection, this discovery phase works best in Plan Mode.** Product strategy is inherently open-ended — the real value is in the discussion, not multiple-choice boxes.

> **Design principle (ADR-001):** Use AskQuestion when you know the option space. Use Plan Mode when you need to discover it.

#### Step 1.3: Product Discovery Conversation (Plan Mode)

**Internal Process (not shown to user) — do this before speaking:**
- Silently list every missing product detail and requirement
- Identify ambiguities in the initial product description
- Note potential market and technical constraints
- Assess whether the user's framing of the problem is *correct* (not just complete)
- Catalog unknowns across these domains:
  - Product vision and core value proposition
  - Target market and user personas
  - Key features and functionality scope
  - Business model and monetization strategy
  - Technical feasibility and architecture requirements
  - Competitive landscape and differentiation
  - Success metrics and validation criteria
  - Timeline expectations and resource constraints
  - Risk factors and mitigation strategies
  - Failure modes and recovery paths for key user flows

**Opening Move — Premise Challenge (mandatory, before any other questions):**

Before gathering details, challenge the premise of the request itself:
- "Is this the right problem to solve? What would happen if we did nothing?"
- "Who benefits most from this — and is that who you think it is?"
- "What's the version of this that would make users *fall in love*, not just sign up?"

This isn't combative — it's clarifying. Most products fail not because of bad execution but because the framing was slightly off. Surface that now.

**Dream State Mapping (required in EXPANSION mode, encouraged in HOLD):**

At some point during discovery, construct this progression with the user:

    CURRENT STATE          →  THIS PLAN           →  12-MONTH IDEAL
    [How users solve today]   [What MVP delivers]    [The product that should exist]

This forces long-horizon thinking. The 12-month ideal isn't a commitment — it's a compass. It reveals whether the MVP is pointed in the right direction or just solving today's problem.

**Conversation Rules:**
- Ask ONE focused question at a time, targeting the highest-impact unknown
- After each answer, re-analyze context and technical feasibility
- Continue until reaching 95% confidence on product deliverable
- **Never declare "final question"** — let the conversation flow naturally
- Let the user signal when they're ready to see a contract
- **Be opinionated.** Lead with your recommendation, explain why, then offer alternatives. "I think the right move here is X because Y — but you could also Z" beats "here are three options, what do you think?"
- **Challenge ideas that don't make business or technical sense** — better to surface concerns early than plan the wrong product

**Posture-Specific Behavior:**
- **EXPANSION:** Actively look for the bigger opportunity. "What if this wasn't just [stated scope] but actually [larger vision]?" Ask about delight opportunities: "What adjacent 30-minute improvements would make this feature sing?" Push the user to articulate the 10-star version — the one that's 10x more ambitious for 2x the effort.
- **HOLD:** Balanced pressure-testing. Validate the framing, find gaps, confirm feasibility. Challenge where needed but respect the user's scope judgment.
- **REDUCTION:** Every feature is guilty until proven essential. "Could we launch without this? What's the absolute minimum that proves the core thesis?"

**Topic Areas to Explore (across the conversation):**
- "Who specifically has this problem, and how painful is it for them?"
- "What would make someone switch from their current solution to yours?"
- "How will you measure product success in the first 6 months?"
- "What's your biggest constraint — time, budget, technical expertise, or market access?"
- "How does this align with your existing business/project goals?"
- "What happens if your first assumption about users turns out to be wrong?"
- "What are the critical failure modes — where does this product break, and what does the user see?"
- Business model and monetization — discuss trade-offs conversationally
- MVP scope — collaboratively identify what delivers core value fastest
- Target audience — explore segments through dialogue, not dropdown
- **Delight opportunities** (EXPANSION mode): "What small touches would create outsized positive perception?"

**Critical Analysis Responsibility:**
- If product scope seems too large for available resources, **recommend** phasing and explain why: "I'd phase this into [A, then B] because [reason]. Trying to ship both at once risks [specific consequence]."
- If target market is unclear or too broad, **recommend** a segment: "I'd start with [segment] because [reason] — they have the most acute pain and shortest sales cycle."
- If technical requirements conflict with existing codebase, **state the cost**: "This would require [specific changes]. That's [effort estimate]. Worth it if [condition], not if [condition]."
- If business model doesn't align with user value, **name the tension**: "There's a tension between [monetization approach] and [user behavior]. Here's how I'd resolve it."
- If competitive landscape presents challenges, surface them with a recommendation attached

**Pushback Format — Always Lead with the Recommendation:**
- "I'd recommend [approach] because [reason]. The alternative is [other approach], but that risks [downside]."
- "Based on your existing codebase, [proposed approach] requires [specific changes]. I'd suggest [alternative] instead because [reason]."
- "The market you're describing is broad. I'd focus on [specific segment] first — they're the most underserved and give you the fastest feedback loop."
- "This feature has a failure mode worth thinking about: [scenario]. I'd handle it by [approach]."

**Transition to Contract:**
- When confidence is high, present the contract (still in Plan Mode)
- Lead with conviction: "Here's the product I think you should build, and why" — not just "here's what I gathered"
- Include the Dream State Map in the contract if one was developed
- Always leave room for more questions if needed

#### Step 1.4: Product Contract Proposal

When confident, present a product contract proposal with any concerns surfaced:

**Format:**
```
## Product Planning Contract

**Planning Posture:** [EXPANSION / HOLD / REDUCTION]

**Product Vision:** [One clear sentence describing the product and its primary value]

**Target Market:** [Specific user segment with their core problem]

**Unique Value:** [What makes this different/better than alternatives]

**Success Criteria:** [How you'll measure product-market fit and growth]

**Dream State Map** (if developed):

    CURRENT STATE          →  THIS PLAN           →  12-MONTH IDEAL
    [How users solve today]   [What MVP delivers]    [The product that should exist]

**MVP Scope:** 
- Core Features: [3-5 essential features for first version]
- Success Metrics: [Key performance indicators]

**Product Architecture:**
- Complexity Level: [Simple/Moderate/Complex based on features]
- Integration Needs: [How this fits with existing business systems]
- Scale Requirements: [Expected user growth and feature expansion]

**Critical Failure Surfaces:** Identify the critical user flows that can break — what breaks, what the user experiences, and how to mitigate it. Focus on flows where failure means lost data, broken trust, or abandoned sessions.

**⚠️ Product Risks (if any):**
- [Market risk, technical risk, or business model concerns]
- [Suggested validation approach or risk mitigation]

**💡 Recommendations (opinionated — lead with what you think they should do):**
- We recommend [approach] because [specific reason tied to user value or market dynamics]
- [Additional recommendations with rationale — not a neutral menu]

**Roadmap Phases:**
- Phase 1 (MVP): [Core value delivery - weeks/months]
- Phase 2 (Growth): [Key expansion features - months]
- Phase 3 (Scale): [Advanced capabilities - quarters]

```

Present this in Plan Mode and discuss refinements conversationally.

#### Step 1.4b: Contract Decision (Agent Mode)

When the user returns to Agent Mode, confirm with AskQuestion: lock contract and create files, edit the contract, explore risks, analyze competition, or continue discussion in Plan Mode.

- **Lock →** Proceed to Phase 2.
- **Edit →** Ask what to change, update contract, re-confirm.
- **Risks / Competition →** Do the analysis, fold findings into the contract, re-confirm.
- **More questions →** Switch back to Plan Mode, resume discovery.

### Phase 2: Product Planning Package Creation (Post-Agreement Only)

**Triggered only after user confirms contract with 'yes'**

#### Step 2.1: Initialize Tracking

Track creation progress with todo_write.

#### Step 2.2: Create Directory Structure

```
.writ/product/
├── mission.md
├── mission-lite.md
├── roadmap.md
└── research/

.writ/decision-records/
├── ADR-000-[product-posture].md
├── ADR-001-[market-focus].md
└── ADR-00N-[decision-title].md
```

> **Note:** This command no longer creates `decisions.md`. Foundational product decisions are now recorded as numbered ADR files in `.writ/decision-records/`. If your project already has a `.writ/product/decisions.md` from a previous run, it is **not** modified or deleted — soft deprecation only.

#### Step 2.3: Generate Core Product Documents

**mission.md** — Complete product vision and strategy document.
- Must contain: pitch (one-liner), target users with personas, problem statement with quantifiable impact, differentiators vs. alternatives, key features organized by phase (MVP/Growth/Scale)
- Quality bar: Someone reading only this file understands the entire product direction — who it's for, why it matters, what makes it different, and what gets built when

**roadmap.md** — Phased development plan with effort estimates.
- Must contain: phase definitions (MVP/Growth/Scale) with timelines and success criteria, features with effort sizing (XS: 1-2 days, S: 3-5 days, M: 1-2 weeks, L: 3-4 weeks, XL: 1+ months), dependencies between phases, validation targets per phase
- Quality bar: Each phase has clear entry/exit criteria and measurable success metrics — no phase starts without knowing what "done" looks like

#### Step 2.4: Generate Foundational ADR Files

For each major decision surfaced during the discovery conversation, create a numbered ADR file in `.writ/decision-records/`. These are the **000-series product ADRs** — they capture product posture and market focus, not technical architecture.

**Standard ADRs to generate (always):**
- `ADR-000-product-posture.md` — The planning posture chosen (EXPANSION / HOLD / REDUCTION) and why; what product tier/ambition level this product targets
- `ADR-001-market-focus.md` — The target user segment chosen and why; what segments were considered and rejected

**Additional ADRs for each major product decision from discovery** (examples):
- `ADR-002-positioning.md` — How this product differentiates from alternatives (if discussed)
- `ADR-003-monetization.md` — Business model decision (if discussed)
- `ADR-004-mvp-scope.md` — Why these features and not others (if scope tradeoffs were significant)

**Each ADR file must follow the standard ADR format** (aligned with `/create-adr`):

```markdown
# ADR-000: [Decision Title]

> Status: Accepted
> Date: YYYY-MM-DD
> Deciders: [product owner / team]
> Part of: /plan-product discovery for [product name]

## Context

[What decision needed to be made and why — the forces at play]

## Decision Drivers

[Force-ranked criteria that tipped this decision]

## Considered Options

[Each option with pros, cons, effort estimate]

## Decision

[Chosen option and rationale tied to drivers]

## Consequences

[Positive and negative consequences; review triggers]
```

**Number assignment:** Start at ADR-000 for the first product-level ADR. If `.writ/decision-records/` already has ADRs from a prior `plan-product` or `/create-adr` run, continue the sequence from the highest existing number.

**Quality bar:** A future AI reading these files understands *why* each product decision was made — the reasoning chain is preserved, not just the outcome. Alternatives considered with honest pros/cons. Every negative consequence documented.

#### Step 2.5: Create Mission-Lite for AI Context

**mission-lite.md** — Condensed product context for AI context windows.
- Must contain: core value proposition, target users, key differentiator, success definition, current phase — all expressible in ~5 sentences
- Quality bar: An AI with only this file can make product-aligned decisions

Example of the right feel:
> TaskMaster is a project management tool that helps remote software teams coordinate work efficiently through automated workflow integration and intelligent task prioritization. It serves distributed development teams who struggle with task coordination across time zones. Unlike traditional project management tools, TaskMaster automatically syncs with Git workflows and provides AI-powered task prioritization based on team capacity and code dependencies.

#### Step 2.6: Final Review

Present the file tree (including all ADR files created under `.writ/decision-records/`), summarize what was captured from the discovery conversation, suggest review focus areas, and recommend next commands (`/create-spec`, `/implement-story`, `/research`).

## Completion

This command succeeds when:

1. **Product vision documented** — `mission.md` exists in `.writ/product/` with pitch, target users, problem statement, differentiators, and phased features
2. **Roadmap created** — `roadmap.md` exists in `.writ/product/` with phased development plan, effort estimates, and success criteria per phase
3. **Mission-lite generated** — `mission-lite.md` exists in `.writ/product/` for AI context windows
4. **Foundational ADRs recorded** — product-level ADR files exist in `.writ/decision-records/` (at minimum `ADR-000-product-posture.md` and `ADR-001-market-focus.md`)
5. **Summary presented** — the user received a completion summary with file tree and suggested next steps

**Suggested next step:** `/create-spec` to spec individual features from the roadmap.

**Terminal constraint:** This command produces product strategy artifacts (`.writ/product/`, `.writ/decision-records/`). Do not offer to implement, build, or execute what was planned. For specification, the user should run `/create-spec`. For quick prototyping, use `/prototype`.

---

## References

- Standing instructions: [`commands/_preamble.md`](_preamble.md)
- Identity & Prime Directive: [`system-instructions.md`](../system-instructions.md)
