# Enhanced Create Spec Command (create-spec)

## Overview

Generate comprehensive feature specifications using a contract-first approach that ensures complete alignment between developer and AI before creating any supporting files. This command eliminates presumptuous file creation by establishing a clear "contract" through structured clarification rounds.

## Command Process

### Phase 1: Contract Establishment (No File Creation)

**Mission Statement:**

> Your goal is to turn my rough feature idea into a very clear work specification. You will deliver the complete spec package only after we both agree on the requirements contract. **Important: Challenge ideas that don't make technical or business sense - it's better to surface concerns early than build the wrong thing.**

#### Step 1.0: Feature Selection (if not provided)

**If user didn't specify a feature idea, use AskQuestion immediately:**

```
AskQuestion({
  title: "Feature Specification - What would you like to build?",
  questions: [
    {
      id: "feature_idea",
      prompt: "What feature would you like to create a specification for?",
      options: [
        // Dynamically generate options based on codebase scan
        // Include common feature types relevant to the project
        { id: "option_1", label: "[Feature suggestion based on codebase gaps]" },
        { id: "option_2", label: "[Another relevant feature suggestion]" },
        { id: "option_3", label: "[Third suggestion from TODO/roadmap]" },
        { id: "other", label: "Something else (I'll describe it)" }
      ]
    }
  ]
})
```

If user selects "Something else", follow up with a free-text question to get their idea.

#### Step 1.1: Initial Context Scan

- Scan existing `.writ/specs/` for related specifications
- Analyze current codebase architecture and patterns using `codebase_search`
- Load project context files (`tech-stack.md`, `code-style.md`, `objective.md`)
- **Output:** Context summary (no files created yet)

#### Step 1.2: Gap Analysis & Silent Enumeration

**Internal Process (not shown to user):**

- Silently list every missing fact, constraint, or requirement
- Identify ambiguities in the initial description
- Note potential integration points and dependencies
- Catalog unknowns across these domains:
  - Purpose & business value
  - Target audience & user personas
  - Technical constraints & requirements
  - Success criteria & acceptance tests
  - Scope boundaries (in/out of scope)
  - UI/UX requirements & design constraints
  - Performance & scalability needs
  - Security & compliance requirements
  - Integration points with existing systems
  - Risk tolerance & implementation approach

#### Step 1.3: Structured Clarification Loop

**Rules:**

- Use the **AskQuestion tool** for structured multiple-choice clarification
- Batch related questions together (max 5-7 questions per round)
- After each answer set, re-scan codebase for additional context if relevant
- Continue rounds until reaching 95% confidence on deliverable
- Follow up with free-text questions only when choices need elaboration
- **Challenge ideas that don't make technical or business sense** - better to surface concerns early than build the wrong thing

**Using AskQuestion Tool:**

Use the `AskQuestion` tool to gather structured information efficiently. Example:

```
AskQuestion({
  title: "Feature Clarification - Round 1",
  questions: [
    {
      id: "user_type",
      prompt: "Who is the primary user of this feature?",
      options: [
        { id: "end_user", label: "End users/customers" },
        { id: "admin", label: "Administrators/internal staff" },
        { id: "developer", label: "Developers/API consumers" },
        { id: "both", label: "Multiple user types" }
      ]
    },
    {
      id: "integration",
      prompt: "How should this integrate with existing systems?",
      options: [
        { id: "standalone", label: "Standalone - minimal integration" },
        { id: "extends", label: "Extends existing feature" },
        { id: "replaces", label: "Replaces existing functionality" },
        { id: "new_system", label: "New system with deep integration" }
      ]
    },
    {
      id: "priority",
      prompt: "What's the implementation priority?",
      options: [
        { id: "mvp", label: "MVP - minimal viable first" },
        { id: "complete", label: "Complete feature set" },
        { id: "iterative", label: "Iterative - start small, expand" }
      ]
    }
  ]
})
```

**Question Categories to Cover (across rounds):**

Round 1 - Core Understanding:
- User type / persona
- Integration approach
- Implementation priority / risk tolerance

Round 2 - Technical Requirements:
- Performance requirements (response time, scale)
- UI/UX constraints (web, mobile, accessibility)
- Data persistence needs
- Security/compliance level

Round 3 - Scope & Success (if needed):
- Feature boundaries (what's in/out)
- Success metrics
- Timeline constraints
- Dependencies on other features

**When to Use Free-Text Follow-up:**

- User selects "Other" or "Multiple" options
- Need specific details (numbers, names, examples)
- Clarifying edge cases or complex requirements
- Discussing technical concerns or alternatives

**Critical Analysis Responsibility:**

- If requirements seem technically infeasible with current architecture, explain why and suggest alternatives
- If scope seems too large for a single feature, recommend breaking it down
- If user requests conflict with existing patterns found in codebase, point out the inconsistency
- If business logic doesn't align with stated user value, ask clarifying questions
- If performance/security/scalability concerns arise, surface them proactively

**Pushback Phrasing Examples:**

- "I see a potential issue with [requirement] because [technical reason]. Would [alternative approach] work better?"
- "Based on your existing codebase, [proposed approach] might conflict with [existing pattern]. How should we handle this?"
- "The scope you're describing sounds like it might be 3-4 separate features. Should we focus on [core piece] first?"
- "I'm concerned that [requirement] could create [specific problem]. Have you considered [alternative]?"

**Transition to Contract:**

- When confidence is high after structured Q&A, present contract
- Use phrases like "Based on your selections, here's my understanding" or "The answers have given me enough to propose a contract"
- Always leave room for more questions if needed

#### Step 1.4: Echo Check (Contract Proposal)

When confident, present a contract proposal with any concerns surfaced:

**Format:**

```
## Specification Contract

**Deliverable:** [One clear sentence describing what will be built]

**Must Include:** [Critical requirement that makes this valuable]

**Hardest Constraint:** [Biggest technical/business limitation to navigate]

**Success Criteria:** [How we'll know it's working correctly]

**Scope Boundaries:**
- Included: [2-3 key features]
- Excluded: [2-3 things we won't build]

**⚠️ Technical Concerns (if any):**
- [Specific concern about feasibility, performance, or architecture]
- [Suggested alternative or mitigation approach]

**💡 Recommendations:**
- [Suggestions for improving the approach based on codebase analysis]
- [Ways to reduce risk or complexity]
```

**Then IMMEDIATELY use AskQuestion for contract decision:**

```
AskQuestion({
  title: "Contract Decision",
  questions: [
    {
      id: "contract_action",
      prompt: "How would you like to proceed with this contract?",
      options: [
        { id: "yes", label: "Lock contract and create spec package" },
        { id: "edit", label: "Edit the contract (I'll specify changes)" },
        { id: "risks", label: "Explore potential implementation risks first" },
        { id: "blueprint", label: "See the planned folder structure and documents" },
        { id: "questions", label: "I have more questions before deciding" }
      ]
    }
  ]
})
```

**Handling responses:**
- **yes**: Proceed to Phase 2 (Spec Package Creation)
- **edit**: Ask free-text follow-up: "What changes would you like to make to the contract?"
- **risks**: Present detailed risk analysis, then re-present contract with AskQuestion
- **blueprint**: Show planned folder structure, then re-present contract with AskQuestion
- **questions**: Ask "What would you like to clarify?" then return to clarification loop

### Phase 2: Spec Package Creation (Post-Agreement Only)

**Triggered only after user confirms contract with 'yes'**

#### Step 2.1: Initialize Tracking

```bash
# Use todo_write to track creation process
1. Get current date and create spec folder structure
2. Generate core specification document (spec.md, spec-lite.md)
3. Plan user stories (identify stories, dependencies, task counts)
4. Launch parallel subagents to create all user story files
5. Create user-stories/README.md after subagents complete
6. Generate technical sub-specifications (can parallel with step 4)
7. Present package for user review and validation
```

#### Step 2.2: Determine Current Date

Get current date by running: `npx @devobsessed/writ date`

This returns the current date in `YYYY-MM-DD` format for folder naming:
`.writ/specs/[DATE]-[feature-name]/`

#### Step 2.3: Create Directory Structure

**Generated folder (using determined date):**

```
.writ/specs/[DATE]-{feature-name}/
├── spec.md                    # Main specification (from contract)
├── spec-lite.md              # Condensed version for AI context
├── user-stories/             # Individual user story files
│   ├── README.md             # Overview and progress tracking
│   ├── story-1-{name}.md     # Individual user story with focused tasks
│   ├── story-2-{name}.md     # Each story kept small and manageable
│   └── story-N-{name}.md     # Max 5-7 implementation tasks per story
└── sub-specs/                # Technical deep-dives
    ├── technical-spec.md     # Architecture & implementation details
    ├── database-schema.md    # Database changes (if needed)
    ├── api-spec.md          # API documentation (if needed)
    └── ui-wireframes.md     # UI/UX specifications (if needed)
```

#### Step 2.4: Generate Core Documents

**spec.md** - Built directly from the locked contract:

```markdown
# [Feature Name] Specification

> Created: [DATE from Step 2.2 determination process]
> Status: Planning  
> Contract Locked: ✅

## Contract Summary

[Echo check content verbatim]

## Detailed Requirements

[Expanded from clarification responses]

## Implementation Approach

[Technical strategy based on codebase analysis]
```

**spec-lite.md** - Condensed version for AI context windows.

#### Step 2.5: Plan User Stories

Before creating user story files, plan out the stories based on the contract:

1. Analyze the contract deliverable and scope
2. Break down into logical user stories (each delivering standalone value)
3. Identify dependencies between stories
4. Ensure each story will have 5-7 implementation tasks max

**Output a story plan like:**

```
Story Plan:
1. story-1-{name}: [Brief description] - Dependencies: None
2. story-2-{name}: [Brief description] - Dependencies: Story 1
3. story-3-{name}: [Brief description] - Dependencies: None
4. story-4-{name}: [Brief description] - Dependencies: Story 2, 3
```

#### Step 2.6: Generate User Stories in Parallel (Using Task Subagents)

**Launch parallel subagents to create all user story files simultaneously.**

> **Agent Reference:** See `agents/user-story-generator.md` for the full agent specification and prompt template.

For each planned story, spawn a Task subagent:

```
// Launch ALL story subagents in a SINGLE message (parallel execution)
// Maximum 4 subagents at a time - batch if more stories needed

Task({
  subagent_type: "generalPurpose",
  model: "fast",
  description: "Create user story 1",
  prompt: `Create the user story file for:
  
**Spec folder:** .writ/specs/[DATE]-[feature-name]/user-stories/
**Story file:** story-1-{name}.md
**Story number:** 1
**Story title:** [Title]
**Story description:** [Description from plan]
**Dependencies:** [Dependencies from plan]

**Contract context:**
[Include relevant contract details]

**Codebase context:**
[Include relevant patterns/architecture found during clarification]

Create the story file following this template:

# Story 1: [Title]

> **Status:** Not Started
> **Priority:** [High/Medium/Low]
> **Dependencies:** [List or None]

## User Story

**As a** [user type]
**I want to** [action]
**So that** [value]

## Acceptance Criteria

- [ ] Given [context], when [action], then [outcome]
[3-5 acceptance criteria]

## Implementation Tasks

- [ ] 1.1 Write tests for [specific component]
- [ ] 1.2 [Focused technical step]
[5-7 tasks max, always start with tests, end with verification]

## Notes

[Technical considerations, risks, or dependencies]

## Definition of Done

- [ ] All tasks completed
- [ ] All acceptance criteria met
- [ ] Tests passing
- [ ] Code reviewed
- [ ] Documentation updated

Write the file and confirm completion.`
})

// Repeat for each story - ALL in the same message for parallel execution
Task({ ... story 2 ... })
Task({ ... story 3 ... })
Task({ ... story 4 ... })
```

**Important:** Launch up to 4 Task subagents simultaneously in a single message. If more than 4 stories, batch them (first 4, then next 4, etc.).

#### Step 2.7: Create User Stories README

**After all subagents complete**, create the README.md that links all stories:

**user-stories/README.md** - Overview and progress tracking:

```markdown
# User Stories Overview

> **Specification:** [Feature Name]
> **Created:** [DATE]
> **Status:** Planning

## Stories Summary

| Story | Title         | Status      | Tasks | Progress |
| ----- | ------------- | ----------- | ----- | -------- |
| 1     | [Story title] | Not Started | 5     | 0/5      |
| 2     | [Story title] | Not Started | 4     | 0/4      |
| 3     | [Story title] | Not Started | 6     | 0/6      |

**Total Progress:** 0/15 tasks (0%)

## Story Dependencies

- Story 2 depends on Story 1 completion
- Story 3 can run parallel to Story 2

## Quick Links

- [Story 1: {Title}](./story-1-{name}.md)
- [Story 2: {Title}](./story-2-{name}.md)
- [Story 3: {Title}](./story-3-{name}.md)
```

#### Step 2.8: Generate Technical Sub-Specs (Parallel with User Stories)

**Can run in parallel with user story generation using additional subagents.**

**Only create relevant sub-specs based on contract requirements:**

- **technical-spec.md**: Always created - architecture, patterns, dependencies
- **database-schema.md**: Only if database changes needed (determined during clarification)
- **api-spec.md**: Only if new API endpoints required
- **ui-wireframes.md**: Only if UI/UX requirements were discussed

**Cross-reference integration**: Each sub-spec references relevant user stories from the user-stories/ folder to maintain traceability between technical details and user value.

#### User Stories Best Practices

**Structure Philosophy:**

- Each user story gets its own file for better organization
- Implementation tasks are kept small and focused (max 5-7 per story)
- Complex stories are broken into multiple smaller stories
- README.md provides overview and progress tracking
- Acceptance criteria become verification checkpoints
- Each story follows TDD: test → implement → verify acceptance criteria

**Benefits of Parallel Generation:**

- **Speed**: All stories created simultaneously instead of sequentially
- **Consistency**: Each subagent follows the same template
- **Manageability**: Each file stays focused and readable
- **Parallel Work**: Multiple developers can work on different stories
- **Progress Tracking**: Clear visibility of completion status

**File Organization:**

- **README.md**: Overview, progress summary, dependencies
- **story-N-{name}.md**: Individual stories with focused tasks (5-7 tasks max)
- **Story Naming**: Clear, descriptive names for easy identification
- **Task Numbering**: N.1, N.2, N.3... within each story file

**Task Breakdown Strategy:**

- If a story would have >7 tasks, split into multiple stories
- Each story should deliver standalone user value
- Tasks within a story should be cohesive and related
- Always start with tests (N.1 Write tests...)
- Always end with verification (N.X Verify acceptance criteria met)

#### Step 2.9: Final Package Review & User Validation

Present complete package with file references:

```
✅ Specification package created successfully!

📁 .writ/specs/[DATE]-feature-name/
├── 📋 spec.md - Main specification document
├── 📝 spec-lite.md - AI context summary
├── 👥 user-stories/ - Individual user story files
│   ├── 📊 README.md - Overview and progress tracking
│   ├── 📝 story-1-{name}.md - Focused story with 5-7 tasks
│   ├── 📝 story-2-{name}.md - Manageable task groups
│   └── 📝 story-N-{name}.md - Easy navigation and parallel work
└── 📂 sub-specs/
    ├── 🔧 technical-spec.md - Technical requirements
    [Additional specs as created]

**Stories Created:** [N] user stories with focused task groups (max 5-7 tasks each)
**Total Tasks:** [X] implementation tasks across all stories
**Organization:** Each story is self-contained for better workflow management

Please take a moment to review the specification documents. The spec captures everything we discussed, including:
- [Brief summary of key features/requirements]
- [Notable technical approach or constraint]
- [Implementation approach or user story highlights]

Please read through the files and let me know:
- Does this accurately capture your vision?
- Are there any missing requirements or incorrect assumptions?
- Are the user stories appropriately sized (5-7 tasks each)?
- Should any stories be split further or combined?

The user-stories folder structure allows you to:
- Work on one story at a time for focused development
- Track progress easily with the README overview
- Assign different stories to different team members
- Keep task lists manageable and actionable

Once you're satisfied with the specification, I can help you start implementation with the first story, or we can make any needed adjustments.
```

## Key Improvements Over Original

### 1. Contract-First Approach

- **No presumptuous file creation** - Nothing gets built until contract is locked
- **Structured clarification** - One question at a time, building understanding
- **Echo check validation** - Clear contract summary before proceeding

### 2. Codebase-Aware Questioning

- **Context scanning between questions** - Each answer triggers fresh codebase analysis
- **Integration-focused queries** - Questions shaped by what exists in the codebase
- **Architecture consistency** - Recommendations align with existing patterns

### 3. User Control & Transparency

- **Clear decision points** - User explicitly approves before file creation
- **Risk assessment option** - Can explore implementation risks before committing
- **Blueprint preview** - Can see planned structure before creation
- **Edit capability** - Can modify contract before locking

### 4. Efficient Clarification Process

- **Gap enumeration** - Systematically identifies all unknowns
- **95% confidence threshold** - Stops asking when ready to deliver
- **Token efficiency** - Focused questions, no verbose explanations during clarification

## Example Usage Flows

### Example 1: No Feature Provided

```
Developer: /create-spec

Agent: [Scans codebase to identify potential features]

[Uses AskQuestion tool IMMEDIATELY]

┌─────────────────────────────────────────────────────────────┐
│ Feature Specification - What would you like to build?       │
├─────────────────────────────────────────────────────────────┤
│ What feature would you like to create a specification for?  │
│    ○ Location search - Let users find and select cities     │
│    ○ 7-day forecast - Display weekly weather data           │
│    ○ Saved locations - Store multiple cities                │
│    ○ Settings - Temperature units, dark mode, etc.          │
│    ○ Something else (I'll describe it)                      │
└─────────────────────────────────────────────────────────────┘

Developer: [Selects: "7-day forecast"]

Agent: [Continues with clarification rounds using AskQuestion...]
```

### Example 2: Feature Provided with Full Flow

```
Developer: /create-spec "real-time multiplayer chat with blockchain integration"

Agent: [Scans existing code, finds a simple React app with basic authentication]

I found your existing React application with basic user authentication. Before I dive into questions, I'm noticing a potential concern: real-time chat typically requires sub-100ms latency, but blockchain transactions can take seconds or minutes.

[Uses AskQuestion tool]

┌─────────────────────────────────────────────────────────────┐
│ Feature Clarification - Round 1                             │
├─────────────────────────────────────────────────────────────┤
│ 1. What problem does blockchain solve in this chat context? │
│    ○ Permanent message storage & verification               │
│    ○ Spam prevention via crypto payments                    │
│    ○ Decentralized ownership / censorship resistance        │
│    ○ Token-gated access to chat rooms                       │
│    ☑ Multiple of the above                                  │
│                                                             │
│ 2. What's your latency expectation for messages?            │
│    ○ Real-time (<1 second)                                  │
│    ○ Near real-time (1-5 seconds)                           │
│    ○ Async is fine (minutes)                                │
│                                                             │
│ 3. How should blockchain and real-time interact?            │
│    ○ Messages must be confirmed on-chain before display     │
│    ○ Hybrid: instant delivery, background blockchain        │
│    ○ Pre-purchase credits, instant spend                    │
└─────────────────────────────────────────────────────────────┘

Developer: [Selects: "Multiple of the above", "Real-time (<1 second)", "Hybrid: instant delivery, background blockchain"]

Agent: Good choices. The hybrid approach makes sense for real-time UX. Since you selected "Multiple" for blockchain purpose, let me clarify with a follow-up:

Which blockchain benefits are must-haves vs nice-to-haves?
- Permanent storage: Must-have / Nice-to-have / Not needed
- Spam prevention via payments: Must-have / Nice-to-have / Not needed

Developer: Spam prevention is must-have, permanent storage is nice-to-have

Agent: [Uses AskQuestion for Round 2 - Technical Requirements]

┌─────────────────────────────────────────────────────────────┐
│ Technical Requirements - Round 2                            │
├─────────────────────────────────────────────────────────────┤
│ 1. Which blockchain/network?                                │
│    ○ Ethereum mainnet                                       │
│    ○ Layer 2 (Polygon, Arbitrum, Optimism)                  │
│    ○ Solana                                                 │
│    ○ Let me recommend based on requirements                 │
│                                                             │
│ 2. Target cost per message for users?                       │
│    ○ Free (you absorb costs)                                │
│    ○ Micro (<$0.01)                                         │
│    ○ Small ($0.01-$0.10)                                    │
│    ○ Significant ($0.10+) - spam prevention priority        │
│                                                             │
│ 3. What happens if blockchain settlement fails?             │
│    ○ Hide message until settled                             │
│    ○ Show message with "pending" indicator                  │
│    ○ Show message, notify user of settlement failure        │
└─────────────────────────────────────────────────────────────┘

Developer: [Selects: "Let me recommend", "Small ($0.01-$0.10)", "Show message, notify user of settlement failure"]

Agent: Based on your $0.01-$0.10 target, I'd recommend Polygon - Ethereum mainnet would cost $1-5+ per message during congestion. Here's the contract:

## Specification Contract

**Deliverable:** Hybrid real-time chat with immediate message delivery and background Polygon verification for anti-spam

**Must Include:** Sub-second message delivery while maintaining blockchain verification for spam prevention

**Hardest Constraint:** Balancing real-time UX with blockchain settlement delays and gas cost management

**⚠️ Technical Concerns:**
- Background settlement failures need graceful handling and user notification
- Wallet integration adds authentication complexity to existing simple auth system
- Need message batching strategy to keep costs in target range

**💡 Recommendations:**
- Use Polygon for $0.01-0.10 per message cost target
- Implement message batching to settle multiple messages in single transaction
- Add fallback mode for when blockchain settlement fails

**Success Criteria:** Messages appear instantly, spam is prevented via crypto payments, blockchain verification happens within 5 minutes

**Scope Boundaries:**
- Included: Real-time chat, wallet integration, background Polygon settlement
- Excluded: Advanced chat features (file sharing, voice), custom token creation, permanent storage (deferred to v2)

[Uses AskQuestion for contract decision]

┌─────────────────────────────────────────────────────────────┐
│ Contract Decision                                           │
├─────────────────────────────────────────────────────────────┤
│ How would you like to proceed with this contract?           │
│    ○ Lock contract and create spec package                  │
│    ○ Edit the contract (I'll specify changes)               │
│    ○ Explore potential implementation risks first           │
│    ○ See the planned folder structure and documents         │
│    ○ I have more questions before deciding                  │
└─────────────────────────────────────────────────────────────┘

Developer: [Selects: "Lock contract and create spec package"]

Agent: ✅ Contract locked! Creating specification package...

[Creates files that account for the technical concerns and hybrid architecture discussed]
```

This approach ensures that every specification is built on solid understanding rather than assumptions, while respecting the developer's time and maintaining control over the process. The structured AskQuestion tool speeds up clarification while still allowing free-text follow-ups for nuanced details.
