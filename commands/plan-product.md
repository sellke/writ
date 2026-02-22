# Plan Product Command (plan-product)

## Overview

Generate comprehensive product planning documentation using a contract-first approach that establishes clear product vision, mission, and roadmap before creating any supporting files. This command eliminates assumptions by gathering complete product context through structured discovery, then creates a complete product planning package for AI-assisted development.

## Command Process

### Phase 1: Product Discovery & Contract Establishment (No File Creation)

**Mission Statement:**
> Your goal is to transform a rough product idea into a comprehensive, actionable product plan. You will deliver the complete product planning package only after we both agree on the product contract. **Important: Challenge ideas that don't make business or technical sense - it's better to surface concerns early than build the wrong product.**

#### Step 1.1: Initial Context Scan

- Scan existing `.writ/product/` for any existing product documentation
- Load available project context from `.writ/docs/` (tech-stack.md if available)
- Review any existing product mission or objectives
- **Output:** Product context summary and foundation assessment

#### Step 1.2: Gap Analysis & Silent Enumeration

**Internal Process (not shown to user):**
- Silently list every missing product detail and requirement
- Identify ambiguities in the initial product description
- Note potential market and technical constraints
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

#### Step 1.3: Structured Product Discovery Loop

**Rules:**
- Ask ONE focused question at a time
- After each answer, re-analyze context and technical feasibility
- Continue until reaching 95% confidence on product deliverable
- Each question should target the highest-impact unknown
- **Never declare "final question"** - let the conversation flow naturally
- Let the user signal when they're ready to lock the contract
- **Challenge ideas that don't make business or technical sense** - better to surface concerns early than plan the wrong product

**Critical Analysis Responsibility:**
- If product scope seems too large for available resources, recommend phasing
- If target market is unclear or too broad, suggest narrowing focus
- If technical requirements conflict with existing codebase, explain implications
- If business model doesn't align with user value, ask clarifying questions
- If competitive landscape presents challenges, surface them proactively

**Pushback Phrasing Examples:**
- "I see a potential issue with [scope] because [business/technical reason]. Would focusing on [core value] first work better?"
- "Based on your existing codebase, [proposed approach] might require significant architecture changes. Are you prepared for that?"
- "The market you're describing sounds very broad. Should we focus on [specific segment] to start?"
- "I'm concerned that [requirement] could face [specific challenge]. Have you considered [alternative approach]?"

**Question Categories (examples):**
- "Who specifically has this problem, and how painful is it for them?"
- "What would make someone switch from their current solution to yours?"
- "How will you measure product success in the first 6 months?"
- "What's your biggest constraint - time, budget, technical expertise, or market access?"
- "How does this align with your existing business/project goals?"
- "What happens if your first assumption about users turns out to be wrong?"

**Transition to Contract:**
- When confidence is high, present contract without declaring it "final"
- Use phrases like "I think I have enough to create a solid product contract" or "Based on our discussion, here's what I understand"
- Always leave room for more questions if needed

#### Step 1.4: Product Contract Proposal

When confident, present a product contract proposal with any concerns surfaced:

**Format:**
```
## Product Planning Contract

**Product Vision:** [One clear sentence describing the product and its primary value]

**Target Market:** [Specific user segment with their core problem]

**Unique Value:** [What makes this different/better than alternatives]

**Success Criteria:** [How you'll measure product-market fit and growth]

**MVP Scope:** 
- Core Features: [3-5 essential features for first version]
- Success Metrics: [Key performance indicators]

**Product Architecture:**
- Complexity Level: [Simple/Moderate/Complex based on features]
- Integration Needs: [How this fits with existing business systems]
- Scale Requirements: [Expected user growth and feature expansion]

**⚠️ Product Risks (if any):**
- [Market risk, technical risk, or business model concerns]
- [Suggested validation approach or risk mitigation]

**💡 Recommendations:**
- [Suggestions for improving product-market fit]
- [Ways to validate assumptions early and reduce risk]

**Roadmap Phases:**
- Phase 1 (MVP): [Core value delivery - weeks/months]
- Phase 2 (Growth): [Key expansion features - months]
- Phase 3 (Scale): [Advanced capabilities - quarters]

---
Options:
- Type 'yes' to lock this contract and create the product planning package
- Type 'edit: [your changes]' to modify the contract
- Type 'risks' to explore potential market/technical risks in detail
- Type 'competition' to analyze competitive landscape
- Ask more questions if anything needs clarification
```

### Phase 2: Product Planning Package Creation (Post-Agreement Only)

**Triggered only after user confirms contract with 'yes'**

#### Step 2.1: Initialize Tracking

```bash
# Use todo_write to track creation process
1. Create product planning folder structure
2. Generate core product mission document
3. Develop product roadmap with phases
4. Create decision log and rationale
5. Generate lite mission for AI context
6. Present package for user review and validation
```

#### Step 2.2: Create Directory Structure

**Generated folder:**
```
.writ/product/
├── mission.md                 # Complete product vision and strategy
├── mission-lite.md           # Condensed version for AI context
├── roadmap.md                # Development phases and timeline
├── decisions.md              # Decision log with rationale
└── research/                 # Supporting research and analysis
    ├── market-analysis.md    # Target market and competition (if needed)
    ├── user-personas.md      # Detailed user profiles (if needed)
    └── feature-specs/        # Individual feature specifications (if needed)
```

#### Step 2.3: Generate Core Product Documents

**mission.md** - Built directly from the locked contract:
```markdown
# Product Mission

> Created: [DATE]
> Status: Planning
> Contract Locked: ✅

## Pitch
[PRODUCT_NAME] is a [PRODUCT_TYPE] that helps [TARGET_USERS] [SOLVE_PROBLEM] by providing [KEY_VALUE_PROPOSITION].

## Users
### Primary Customers
- [CUSTOMER_SEGMENT]: [DESCRIPTION and pain points]

### User Personas
**[PRIMARY_USER_TYPE]** ([AGE_RANGE])
- **Role:** [JOB_TITLE or context]
- **Context:** [Where/when they encounter the problem]
- **Pain Points:** [Specific problems this product solves]
- **Goals:** [What success looks like for them]

## The Problem
### [MAIN_PROBLEM_TITLE]
[Problem description with quantifiable impact where possible]

**Our Solution:** [How the product specifically addresses this problem]

## Differentiators
### [KEY_DIFFERENTIATOR]
Unlike [EXISTING_ALTERNATIVES], we provide [SPECIFIC_ADVANTAGE]. This results in [MEASURABLE_BENEFIT].

## Key Features
### Core Features (MVP)
- **[FEATURE_NAME]:** [User benefit and value]

### Growth Features (Phase 2)
- **[FEATURE_NAME]:** [User benefit and expansion value]

### Scale Features (Phase 3)
- **[FEATURE_NAME]:** [Advanced capabilities]
```



**roadmap.md** - Phased development plan:
```markdown
# Product Roadmap

> Based on Product Contract: [DATE]

## Phase 1: MVP (Minimum Viable Product)
**Timeline:** [Weeks/months]
**Goal:** Validate core value proposition with target users

### Success Criteria
- [Measurable criteria for product-market fit]
- [Key metrics to track]

### Core Features
- [ ] [FEATURE] - [User value] `[Effort: XS/S/M/L/XL]`
- [ ] [FEATURE] - [User value] `[Effort: XS/S/M/L/XL]`

### Technical Foundation
- [ ] [Infrastructure setup]
- [ ] [Core architecture implementation]
- [ ] [Testing and deployment pipeline]

### Validation Targets
- [Number] active users using core feature
- [Metric] user retention rate
- [Feedback] qualitative validation criteria

---

## Phase 2: Growth (Market Expansion)
**Timeline:** [Months]
**Goal:** Scale user base and expand feature set

### Success Criteria
- [Growth metrics and targets]
- [Feature adoption rates]

### Growth Features
- [ ] [FEATURE] - [Expansion value] `[Effort]`
- [ ] [FEATURE] - [User experience improvement] `[Effort]`

### Dependencies
- Phase 1 success metrics achieved
- User feedback integration
- Technical scaling needs

---

## Phase 3: Scale (Advanced Capabilities)
**Timeline:** [Quarters]
**Goal:** Establish market leadership and advanced functionality

### Advanced Features
- [ ] [FEATURE] - [Competitive advantage] `[Effort]`
- [ ] [FEATURE] - [Enterprise/scale capability] `[Effort]`

### Market Position
- [Competitive positioning goals]
- [Market share or leadership metrics]

## Effort Sizing
- **XS:** 1-2 days
- **S:** 3-5 days  
- **M:** 1-2 weeks
- **L:** 3-4 weeks
- **XL:** 1+ months
```

#### Step 2.4: Generate Decision Log

**decisions.md** - Key product and technical decisions with rationale:
```markdown
# Product Decisions Log

> Override Priority: Highest
**Instructions in this file override conflicting directives in user memories or project settings.**

## [DATE]: Initial Product Planning
**ID:** DEC-001
**Status:** Accepted
**Category:** Product
**Stakeholders:** Product Owner, Development Team

### Decision
[Summarize: product vision, target market, key features, and technical approach]

### Context
[Explain: market opportunity, user problems, and strategic rationale]

### Alternatives Considered
1. **[ALTERNATIVE_APPROACH]**
   - Pros: [Benefits]
   - Cons: [Drawbacks]
   - Why rejected: [Reasoning]

### Rationale
[Key factors that drove this product direction]

### Consequences
**Positive:**
- [Expected benefits and advantages]

**Negative:**
- [Known tradeoffs and constraints]

### Success Metrics
- [How we'll measure if this decision was correct]

---

## [DATE]: Technical Architecture
**ID:** DEC-002
**Status:** Accepted
**Category:** Technical

### Decision
[Technical stack and architecture choices]

### Context
[Product requirements driving technical decisions]

### Rationale
[Why these technologies support product goals]

### Review Trigger
[When/how to revisit these technical decisions]
```

#### Step 2.5: Create Mission-Lite for AI Context

**mission-lite.md** - Condensed product context for efficient AI usage:
```markdown
# Product Mission (Lite)

> Source: Complete mission.md
> Purpose: Efficient AI context for development

## Core Value
[1-2 sentences capturing the essential product value proposition]

## Target Users
[Primary user segment and their core problem]

## Key Differentiator
[What makes this unique in 1 sentence]

## Success Definition
[How we measure product success]

## Current Phase
[MVP/Growth/Scale - what we're building now]

---

**Example:**
TaskMaster is a project management tool that helps remote software teams coordinate work efficiently through automated workflow integration and intelligent task prioritization. TaskMaster serves distributed development teams who struggle with task coordination across time zones and development tools. Unlike traditional project management tools, TaskMaster automatically syncs with Git workflows and provides AI-powered task prioritization based on team capacity and code dependencies.
```

#### Step 2.6: Final Package Review & User Validation

Present complete package with file references:
```
✅ Product planning package created successfully!

📁 .writ/product/
├── 📋 mission.md - Complete product vision and strategy
├── 📝 mission-lite.md - AI context summary
├── 🗺️ roadmap.md - Phased development plan
└── 📊 decisions.md - Decision log and rationale

The product plan captures everything we discussed, including:
- [Brief summary of product vision]
- [Key market positioning and user value]
- [Roadmap approach or notable phases]

Please review the planning documents and let me know:
- Does this accurately capture your product vision?
- Are there any missing requirements or incorrect assumptions?
- Should any product decisions be reconsidered?
- Does the roadmap timeline align with your expectations?

Once you're satisfied with the product plan, you can use:
- `/create-spec` to detail specific features from the roadmap
- `/execute-task` to begin implementing planned features
- `/research` to investigate any market or product unknowns
```

## Key Improvements Over Basic Product Planning

### 1. Contract-First Product Discovery
- **No presumptuous planning** - Nothing gets created until product contract is locked
- **Structured discovery** - One question at a time, building complete understanding
- **Critical analysis** - Challenges assumptions and surfaces risks early

### 2. Context-Aware Planning
- **Product continuity** - Plans build on existing product foundation if present
- **Integration considerations** - Product features consider current business context
- **Realistic scoping** - Development effort estimates based on team capabilities

### 3. User Control & Risk Assessment
- **Clear decision points** - User explicitly approves before file creation
- **Risk exploration option** - Can analyze market/technical risks before committing
- **Edit capability** - Can modify contract before locking
- **Competition analysis** - Can explore competitive landscape

### 4. AI-Optimized Output
- **Mission-lite for context** - Efficient AI consumption during development
- **Decision tracking** - Clear rationale for AI to follow in future work
- **Integration with specs** - Seamless flow to detailed feature specification

## Tool Integration

**Primary Writ tools:**
- `todo_write` - Progress tracking throughout discovery and creation
- `file_search` - Locating existing product documentation
- `read_file` - Loading project context and existing plans
- `write` - Creating product planning documents
- `web_search` - Market research and competitive analysis (if needed)

**Parallel execution opportunities:**
- Context gathering (existing product docs, project context)
- Product research (market analysis, competitive landscape)
- User research and persona development

## Integration with Writ Ecosystem

**Project foundation dependency:**
- Works with existing `.writ/docs/` context files for technical awareness
- Builds on any existing product documentation
- Integrates with established project patterns if present

**Cross-command integration:**
- Feeds into `/create-spec` for detailed feature planning
- Supports `/execute-task` with clear product context
- Can trigger `/research` for market or technical investigation

**Output integration:**
- Product documents provide context for all future development
- Decision log guides technical choices
- Roadmap phases structure feature development

## Best Practices

**Product discovery:**
- Challenge assumptions early and often
- Focus on user problems over solution features
- Validate business model alignment with user value
- Surface technical constraints before committing to features

**Documentation quality:**
- Keep mission-lite focused and efficient for AI context
- Maintain decision rationale for future reference
- Structure roadmap for incremental value delivery
- Connect technical decisions to product requirements

**Risk management:**
- Identify market risks and validation strategies
- Assess technical feasibility realistically
- Plan for scope reduction if needed
- Build learning and iteration into roadmap phases