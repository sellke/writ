# Enhanced Create Spec Command (create-spec)

## Overview

Generate comprehensive feature specifications using a contract-first approach that ensures complete alignment between developer and AI before creating any supporting files. This command uses **Plan Mode for open-ended discovery** and **AskQuestion for bounded decisions**, eliminating presumptuous file creation by establishing a clear "contract" through collaborative conversation.

## Invocation

- `/create-spec` — discover and create a full contract-first spec package
- `/create-spec --from-prototype` — formalize recent prototype work into a spec with Story 1 already complete

## Command Process

### `--from-prototype` Mode

**Invocation:** `/create-spec --from-prototype`

Used when a `/prototype` run triggered scope escalation signals and you want to formalize the prototype work as Story 1 (already complete) and plan Story 2+ onward.

**This mode replaces Phase 1 (discovery) with a shorter, prototype-anchored flow:**

#### Step 0: Read Prototype Context

1. **Read the current git diff** — `git diff HEAD` (or `git diff --cached` if staged). Extract: files changed, lines added/removed, new dependencies added.
2. **Read the coding agent implementation summary** from the conversation thread if available — it describes what was built and how.
3. **Build a pre-populated contract draft:**
   - **Deliverable:** Inferred from diff file names and implementation summary (e.g., "Adds [feature] to [area]")
   - **Files in Scope:** Directly from the diff — list every file created or modified
   - **Implementation Approach:** From the coding agent summary where available; fall back to diff analysis
   - **Story 1:** `[Prototype: description of what was built] — Status: Completed ✅`

If no git diff exists (clean working tree), warn: *"No changes detected in working tree. `--from-prototype` requires an uncommitted or staged diff to read context from."* and offer: proceed with manual description, or cancel.

#### Step 1: Shortened Discovery Conversation (Plan Mode)

Switch to Plan Mode. The prototype is done — **do not re-litigate what was already built.** Discovery is focused exclusively on what comes next.

**Opening framing:**
> "The prototype built [summary from diff]. Story 1 is already complete. Let's figure out what Story 2+ should accomplish — what does this need to grow into?"

**Discovery anchor questions (focused on the future, not the past):**
- What's the gap between this prototype and something you'd actually ship?
- What does Story 2 unlock that the prototype didn't have?
- Are there error states, edge cases, or production concerns the prototype skipped?
- What's the first thing you'd add after this? What would make users actually love it?
- Are there integration points or shared components the prototype touched that need productionizing?

Skip questions that are already answered by the diff (files in scope, approach used, features built). The discovery conversation should take 3–5 exchanges, not 15.

#### Step 2: Contract Proposal (Plan Mode)

Use the pre-populated contract draft from Step 0 as the base. Augment with discovery answers. Present in Plan Mode for review — the contract should reflect both what's already built (Story 1) and what comes next.

**Key contract shape for `--from-prototype`:**
```
## Specification Contract

**Deliverable:** [inferred from diff + discovery]
**Origin:** Formalized from prototype (Story 1 already complete)

**Story 1 (Complete):** [description of prototype work — what was built]
**Story 2+:** [what the discovery conversation revealed comes next]

**Files in Scope:** [from git diff — already in the codebase]

[standard contract sections: Constraints, Success Criteria, Scope Boundaries]
```

#### Step 3: Phase 2 with Story 1 Pre-Marked Complete

When the user locks the contract, proceed to Phase 2 (Spec Package Creation) with one modification:

- **Story 1** is generated with `Status: Completed ✅` immediately — do not mark it Not Started
- Story 1's description captures the prototype work: what was implemented, files touched, and that it was done via `/prototype`
- Story 1's Implementation Tasks are all checked: `- [x] [task]`
- Story 1's Definition of Done is all checked
- All subsequent stories start at `Status: Not Started`
- The `user-stories/README.md` progress reflects Story 1 as already complete

**Why Story 1 is auto-complete:** The prototype work already exists in the codebase. Marking it Not Started would misrepresent the project state and confuse `/implement-spec` into trying to re-implement existing work.

---

### `--from-issue` Mode

**Invocation:** `/create-spec --from-issue [path]`

Used when a captured issue under `.writ/issues/` is ready to be promoted into a full specification. This mode pre-populates the discovery contract from the issue file so triage work flows directly into the pipeline — no manual translation.

**This mode replaces Phase 1 (discovery) with a shorter, issue-anchored flow:**

#### Step 0: Read Issue Context

1. **Validate the path** — confirm the file exists under `.writ/issues/{bugs,features,improvements}/`. If the path is invalid or the file is missing:
   ```
   ⚠️ Issue file not found: [path]
   Expected under .writ/issues/{bugs,features,improvements}/YYYY-MM-DD-{slug}.md
   Provide a valid path or cancel.
   ```
   Do not modify the issue file on error.

2. **Parse the issue file** — extract these fields:
   - `Type` (from frontmatter line `**Type:**`)
   - `Priority` (from `**Priority:**`)
   - `Effort` (from `**Effort:**`)
   - `TL;DR` section → one-sentence summary
   - `Current State` section → what's broken/missing
   - `Expected Outcome` section → what success looks like
   - `Relevant Files` section → affected files list

3. **Build a pre-populated contract draft:**
   - **Deliverable:** Inferred from issue TL;DR and type (e.g., "Fix [bug summary]" or "Add [feature summary]")
   - **Origin:** `Promoted from issue: [path]`
   - **Files in Scope:** From the issue's Relevant Files section
   - **Priority signal:** From issue Priority field
   - **Effort signal:** From issue Effort field

#### Step 1: Shortened Discovery Conversation (Plan Mode)

Switch to Plan Mode. The issue describes the problem space — **do not re-ask what's already documented in the issue.** Discovery focuses on shaping the solution into stories.

**Opening framing:**
> "This issue captures [TL;DR from issue]. Let's shape it into a spec. What does the fix/feature need to accomplish beyond what the issue describes?"

**Discovery anchor questions (forward-looking, gap-filling):**
- What story decomposition makes sense — single story or multiple?
- Are there edge cases or error states the issue didn't capture?
- What acceptance criteria would confirm this is fully resolved?
- Any integration points or dependencies not mentioned in the issue?
- Are there constraints (performance, backward-compat, scope limits) the issue omits?

Skip questions that are already answered by the issue. The discovery conversation should take 2–4 exchanges.

#### Step 2: Contract Proposal (Plan Mode)

Use the pre-populated contract draft from Step 0 as the base. Augment with discovery answers. Present for review.

**Key contract shape for `--from-issue`:**
```
## Specification Contract

**Deliverable:** [inferred from issue + discovery]
**Origin:** Promoted from issue: [path]

**Stories:** [decomposition revealed by discovery]

**Files in Scope:** [from issue Relevant Files + discovery additions]

[standard contract sections: Constraints, Success Criteria, Scope Boundaries]
```

#### Step 3: Phase 2 with `spec_ref` Writeback

When the user locks the contract, proceed to Phase 2 (Spec Package Creation) with one addition:

**After the spec directory is created** (after `spec.md` is written), update the source issue file with the spec reference:

1. Read the issue file
2. Replace the `spec_ref:` line (which reads `_(set automatically when promoted via ...)_`) with the actual spec path:
   ```
   > **spec_ref:** .writ/specs/[date]-[name]/spec.md
   ```
3. Write the issue file back — **only the `spec_ref` line changes**. All other issue content is preserved exactly as-is. The issue is never deleted or archived.

**If the spec_ref line is absent** from the issue file (older issue predating this field), append it to the frontmatter block rather than failing.

---

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

#### Step 1.2: Switch to Plan Mode for Discovery

**After the context scan, this discovery phase works best in Plan Mode.** The user controls when to switch — the discovery phase is a conversation, not a questionnaire.

- **Read-only enforcement** — structurally prevents premature file creation
- **Conversational UX** — open-ended back-and-forth instead of multiple-choice boxes
- **Clear phase signal** — the mode switch tells the user "we're shaping the idea, not building yet"

> **Design principle (ADR-001):** Use AskQuestion when you know the option space. Use Plan Mode when you need to discover it.

#### Step 1.3: Discovery Conversation (Plan Mode)

**Internal Process (not shown to user) — do this before speaking:**

- Silently list every missing fact, constraint, or requirement
- Identify ambiguities in the initial description
- Note potential integration points and dependencies
- Catalog unknowns — what concrete information is still missing?

  **Experience gaps:** Entry point, happy path flow, key interaction moments, feedback/confirmation model, error/empty/loading states, responsive behavior
  **Business rule gaps:** Permissions & access control, validation rules & limits, state transitions & lifecycle, time-based rules, pricing/billing implications, domain edge cases, compliance requirements
  **Technical gaps:** Integration points, performance requirements, security needs, data persistence
  **Scope gaps:** Success criteria, in/out boundaries, implementation approach, timeline

**Conversation Rules:**

- Ask ONE focused question at a time, targeting the highest-impact unknown
- After each answer, re-scan codebase for additional context if relevant
- Continue until reaching 95% confidence on the deliverable
- **Never declare "final question"** — let the conversation flow naturally
- Let the user signal when they're ready to see a contract
- **Challenge ideas that don't make technical or business sense** — better to surface concerns early than build the wrong thing

**Topic Areas to Explore (across the conversation):**

Start with *experience*, then fill in *rules*, then address *technical* constraints. This ordering ensures the spec captures what the feature should feel like — not just what it does.

**Experience first — how should this feel to use?**
- Walk me through the ideal interaction: the user does X, sees Y, feels Z
- What's the first thing they see? What draws their eye? What do they do first?
- What's the "wow" moment — the instant they get the value and think "this is great"?
- What happens when there's no data yet? (empty states, onboarding, first-use experience)
- What happens when something fails? (error messages, recovery paths, graceful degradation)
- Are there moments that need to feel *fast*? Moments that can afford a loading state?
- What existing patterns in the app should this mirror? What should it deliberately break from?
- How does the user know the action succeeded? (toast, redirect, inline update, animation?)
- Is discoverability important, or is this a power-user feature?

**Rules next — what business logic constrains the design space?**
- Who can and can't do this? (roles, permissions, subscription tiers, feature gates)
- What validation rules apply? (input constraints, format requirements, limits)
- Are there state machines or lifecycle rules? (draft → published → archived, pending → approved)
- Are there time-based rules? (expiration, cooldowns, scheduling, rate limiting)
- Are there pricing/billing/usage implications?
- What domain-specific edge cases exist? (timezone handling, currency, localization, leap years)
- Are there audit, compliance, or regulatory requirements?
- What happens at the boundaries? (max items, storage limits, concurrent access)

**Technical last — what does the system need?**
- How should this integrate with what already exists?
- Implementation approach — MVP, complete, iterative?
- Performance, scale, and latency requirements
- Data persistence and security needs
- Feature boundaries — what's in scope, what's explicitly out?
- Success criteria and how we'll know it's working
- Timeline constraints and dependencies

**Critical Analysis Responsibility:**

- If requirements seem technically infeasible with current architecture, explain why and suggest alternatives
- If scope seems too large for a single feature, recommend breaking it down
- If user requests conflict with existing patterns found in codebase, point out the inconsistency
- If business logic doesn't align with stated user value, ask clarifying questions
- If performance/security/scalability concerns arise, surface them proactively
- If the error/empty/loading experience hasn't been discussed, ask — these states are where users form lasting impressions
- If business rules are vague or assumed ("admins can do it"), probe for specifics — who exactly, under what conditions, what are the exceptions?
- If the described experience has unnecessary friction (extra clicks, confirmations, page reloads), suggest smoother alternatives

**Pushback Phrasing Examples:**

- "I see a potential issue with [requirement] because [technical reason]. Would [alternative approach] work better?"
- "Based on your existing codebase, [proposed approach] might conflict with [existing pattern]. How should we handle this?"
- "The scope you're describing sounds like it might be 3-4 separate features. Should we focus on [core piece] first?"
- "I'm concerned that [requirement] could create [specific problem]. Have you considered [alternative]?"
- "We haven't talked about what happens when [error/empty case]. Users will hit this — what should they see?"
- "You mentioned [role] can do this. What about [other role]? And what happens if someone tries without permission?"
- "That flow has the user [extra steps]. What if we [shorter path] instead? It would feel faster."

**Transition to Contract:**

- When confidence is high, present the contract (still in Plan Mode)
- Use phrases like "I think I have a clear picture now — here's what I'd propose" or "Based on our discussion, here's the contract"
- Always leave room for more questions if needed

#### Step 1.3b: Cross-Spec Overlap Check (Automatic)

Before presenting the contract, scan for potential conflicts with other in-progress specifications:

1. **List all spec folders** in `.writ/specs/`
2. **Filter out completed specs** — read each `spec.md` header and skip specs with `Status: Complete`
3. **Read each remaining `spec-lite.md`** — these are small, condensed files designed for quick scanning
4. **Extract domain keywords** from the new contract: models/entities mentioned, routes/endpoints, shared utilities, domain-specific terms, files to be modified
5. **Compare against existing specs** — check for keyword overlap in domain areas (same models, same routes, same shared utilities)
6. **If overlap detected** — add a `⚠️ Cross-Spec Overlap` section to the contract (see format below)
7. **If no overlap** — proceed silently (no section added to contract)

This check is a lightweight heuristic — keyword matching, not deep semantic analysis. False positives are acceptable (user can dismiss). The goal is to catch obvious planning-level conflicts before they reach implementation.

#### Step 1.4: Contract Proposal (Still in Plan Mode)

When confident, present a contract proposal with any concerns surfaced:

**Format:**

```
## Specification Contract

**Deliverable:** [One clear sentence describing what will be built]

**Must Include:** [Critical requirement that makes this valuable]

**Hardest Constraint:** [Biggest technical/business limitation to navigate]

**🎯 Experience Design:**
- **Entry point:** [How the user reaches this feature]
- **Happy path:** [The ideal flow in 2-3 steps]
- **Moment of truth:** [The instant the user gets the value]
- **Feedback model:** [How the user knows it worked — toast, redirect, animation, etc.]
- **Error experience:** [What failure looks like to the user — not the system]

**📋 Business Rules:**
- [Key rule 1 — e.g., "Only workspace admins can invite members"]
- [Key rule 2 — e.g., "Free tier limited to 3 projects"]
- [Key rule 3 — e.g., "Invoices transition: draft → sent → paid → void"]
- [Edge cases or domain-specific constraints discovered during conversation]

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

**⚠️ Cross-Spec Overlap (if detected):**
- [Spec name] ([status]) also touches [domain area] — [specific overlap details]
- Consider: sequencing these specs, declaring a dependency, or coordinating the shared area
```

Present this in Plan Mode and discuss any refinements conversationally. When the user approves and switches back to Agent Mode, confirm with AskQuestion:

#### Step 1.4b: Contract Decision (Agent Mode)

**When the user returns to Agent Mode after approving the contract direction, use AskQuestion to confirm:**

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
- **questions**: Switch back to Plan Mode and return to discovery conversation

#### Step 1.5: Visual References (Optional)

**After contract lock, before creating files**, check if this feature has UI components:

If the spec involves any user-facing UI, ask:

```
AskQuestion({
  title: "Visual References",
  questions: [
    {
      id: "visuals",
      prompt: "Do you have any visual references for this feature?",
      options: [
        { id: "screenshots", label: "I have screenshots or mockups to share" },
        { id: "sketch", label: "I have an Excalidraw sketch" },
        { id: "generate", label: "Generate wireframes from the spec" },
        { id: "existing", label: "Match existing app patterns (capture current UI)" },
        { id: "none", label: "No visual references — text spec is enough" }
      ]
    }
  ]
})
```

**Handling responses:**
- **screenshots**: Accept image uploads/paths. Store in `mockups/`. Analyze with vision model to extract layout structure, components, and design patterns. Generate `mockups/README.md` and `mockups/component-inventory.md`.
- **sketch**: Accept `.excalidraw` file. Store in `mockups/`. Parse JSON to extract component names and layout.
- **generate**: After creating `spec.md`, generate Excalidraw wireframes for each screen/view described in the spec. Store in `mockups/`. Follow wireframe conventions from `/design` command.
- **existing**: Capture screenshots of the current app at relevant routes. Store in `mockups/current/`. These become the "before" state.
- **none**: Create empty `mockups/` directory. Skip visual references in story files.

**When mockups are provided or generated:**
- Add `## Visual References` section to each relevant story file, linking to the specific mockups that story should implement
- Generate `mockups/component-inventory.md` listing all components, their states, and which stories own them
- Reference design system tokens from `.writ/docs/design-system.md` if it exists; if not, extract one from the mockups

### Phase 2: Spec Package Creation (Post-Agreement Only)

**Triggered only after user confirms contract with 'yes'**

#### Step 2.1: Initialize Tracking

Track creation progress with `todo_write`: folder structure, core documents, user stories (parallel), sub-specs, and final review.

#### Step 2.2: Determine Current Date

Get current date by running: `npx @devobsessed/writ date`

This returns `YYYY-MM-DD` format for folder naming: `.writ/specs/[DATE]-[feature-name]/`

Resolve the spec owner from git config before writing `spec.md`:

```bash
OWNER="@$(git config user.name 2>/dev/null | tr -d ' ' || echo 'unknown')"
if [ "$OWNER" = "@" ]; then
  OWNER="@unknown"
  echo "⚠️ No git user.name configured; writing owner: @unknown. Set it with: git config user.name 'Your Name'"
fi
```

The owner value is intentionally simple: prefix `@`, strip spaces, and do not consult any external user directory. If `git config user.name` is unset or empty, write `owner: @unknown` and show the warning above.

#### Step 2.3: Create Directory Structure

```
.writ/specs/[DATE]-{feature-name}/
├── spec.md
├── spec-lite.md
├── mockups/
├── user-stories/
│   ├── README.md
│   ├── story-1-{name}.md
│   └── story-N-{name}.md
└── sub-specs/
    └── technical-spec.md (+ database-schema.md, api-spec.md, ui-wireframes.md as needed)
```

#### Step 2.4: Generate Core Documents

**spec.md** — Main specification built from the locked contract. Must contain:

- **Frontmatter** — include status, created date, owner, and any relevant phase/source metadata:
  ```markdown
  > **Status:** Not Started
  > **Created:** [DATE]
  > **Owner:** [OWNER]
  ```
- **Contract summary** — echo the locked contract verbatim
- **Experience design** — expand the 🎯 section: user journey, state catalog (empty/loading/populated/error/edge), interaction patterns, responsive behavior
- **Business rules** — expand the 📋 section: permissions, validation, state transitions, domain edge cases, compliance
- **Detailed requirements** — expanded from clarification responses
- **Implementation approach** — technical strategy based on codebase analysis

**spec-lite.md** — Condensed version for AI context windows with agent-specific sections. Total budget: <100 lines (hard limit). Format:

```markdown
# [Feature Name] (Lite)

> Source: .writ/specs/[DATE]-[name]/spec.md
> Purpose: Efficient AI context for implementation

## For Coding Agents

[35 lines max]

**Deliverable:** [One-sentence summary]

**Implementation Approach:**
- [Key technical decisions]
- [Architecture patterns to use]
- [Integration strategy]

**Files in Scope:**
- `path/to/file.ext` — [what changes here]

**Error Handling:**
- [Error case] → [planned handling]

**Integration Points:**
- [Command/agent interactions]

**Line Budget Constraints:** [if relevant to this spec]

---

## For Review Agents

[35 lines max]

**Acceptance Criteria:**
1. [Measurable criterion with target]
2. [Business rule verification]
3. [Integration success condition]

**Business Rules:**
- [Permission/access control rules]
- [Validation constraints]
- [State transition rules]
- [Domain-specific edge cases]

**Experience Design:**
- Entry: [How user reaches this]
- Happy path: [Ideal flow]
- Moment of truth: [Value realization point]
- Feedback: [Success confirmation]
- Error: [Failure experience]

**[Domain-Specific Section if applicable]:**
- Error & Rescue Map structure
- Shadow Paths format
- Drift Analysis thresholds

---

## For Testing Agents

[30 lines max]

**Success Criteria:**
1. [Quantifiable metric with threshold]
2. [Coverage requirement]
3. [Performance/quality target]

**Shadow Paths to Verify:**
- **Happy path:** [Normal flow outcome]
- **Nil input:** [Missing data handling]
- **Empty input:** [Zero-state handling]
- **Upstream error:** [External failure handling]

**Edge Cases:**
- [Feature-specific edge case] → [expected behavior]
- [Interaction edge case] → [expected behavior]

**Coverage Requirements:**
- New code: ≥80%
- Critical paths: 100%
- Error paths: 100%

**Test Strategy:**
- [Test types needed]
- [Key scenarios to verify]
```

**Content Selection Guidelines:**

When building each section, prioritize based on feature type:

- **Data flow features** (APIs, auth, payments, integrations): emphasize error handling, shadow paths, business rules
- **UI features**: emphasize experience design, interaction edge cases, responsive behavior
- **Refactors**: emphasize affected files, integration points, backward compatibility
- **Documentation/tooling**: emphasize success criteria, verification approach

**Line Budget Enforcement:**

The total spec-lite.md must stay under 100 lines. The agent-specific sections target 35/35/30 lines, but the three horizontal rules (`---`) and section headers add ~10 lines, leaving ~90 lines for content. Budget breakdown:

- Header block (title, source, purpose): ~5 lines
- Section headers + dividers: ~10 lines
- Coding section content: ≤35 lines
- Review section content: ≤35 lines
- Testing section content: ≤30 lines
- **Total: ~90 content + 10 structural = 100 lines**

When content risks exceeding limits:

1. **Cut nice-to-haves first**: Remove verbose descriptions, combine bullets, use terse phrasing
2. **Prioritize critical information**: Error maps, business rules, and acceptance criteria are highest value
3. **Use references**: Point to spec.md sections instead of duplicating content (e.g., "See spec.md → ## Technical Decisions")
4. **Truncate sections proportionally**: If total exceeds 100, reduce all three sections by same percentage

**Backward Compatibility Note:**

Older specs may use the previous single-block format (no agent-specific sections). This is expected — only specs created after Context Engine (Story 2) should use the new format. Do not retroactively convert old specs unless explicitly requested.

#### Step 2.5: Plan User Stories

Before creating files, plan the stories:

1. Analyze the contract deliverable and scope
2. Break into logical user stories (each delivering standalone value)
3. Identify dependencies between stories
4. Ensure each story has 5-7 implementation tasks max

Output a story plan:

```
Story Plan:
1. story-1-{name}: [Description] - Dependencies: None
2. story-2-{name}: [Description] - Dependencies: Story 1
3. story-3-{name}: [Description] - Dependencies: None
```

#### Step 2.6: Generate User Stories in Parallel

Launch parallel Task subagents to create all story files simultaneously. Reference `agents/user-story-generator.md` for the agent spec and prompt template.

For each story, spawn a Task subagent (`generalPurpose`, model `fast`) in a single message. Provide each agent with: output path, story number, title, description, dependencies, priority, the locked contract, relevant codebase patterns, **and full specification content for context hint generation**.

**Context hint generation (new):** Pass these additional parameters to each user-story-generator agent:
- `spec_content` — full text of `spec.md` (read from `.writ/specs/{spec-folder}/spec.md`)
- `technical_spec_content` — full text of `technical-spec.md` if it exists; otherwise pass empty string `""` with note that hints should reference `spec.md` sections directly

**Timing note:** If running Step 2.6 in parallel with Step 2.8 (technical sub-spec generation), `technical-spec.md` may not exist yet. In that case, pass empty string for `technical_spec_content` and note in the prompt: "Technical spec not yet generated — scope hints to spec.md sections only (e.g., 'spec.md → ## 🎯 Experience Design → ### Error Experience')."

Each story file should contain: status/priority/dependencies metadata, user story (As a / I want / So that), 3-5 acceptance criteria in Given/When/Then, 5-7 implementation tasks (tests first, verification last), technical notes, definition of done, **and a "## Context for Agents" section with targeted hints** referencing relevant error map rows, shadow paths, business rules, and experience elements.

Launch up to 4 subagents simultaneously. If more than 4 stories, batch them.

#### Step 2.7: Create User Stories README

After all subagents complete, create `user-stories/README.md` with: stories summary table (status, task counts, progress), dependency descriptions, and quick links to each story file.

#### Step 2.8: Generate Technical Sub-Specs

Can run in parallel with user story generation. Only create sub-specs the contract requires: `technical-spec.md` (always), plus `database-schema.md`, `api-spec.md`, `ui-wireframes.md` as needed. Each references relevant user stories for traceability.

**Error Mapping (Required for Data Flow Features):**

Include when the spec touches: API routes, auth flows, payments, file operations, or external integrations. Skip for pure UI/CSS, docs, config, or internal refactors. When in doubt, include it. These tables use identical structures to `/review`'s output, enabling plan-vs-actual comparison.

**Error & Rescue Map:**

| Operation | What Can Fail | Planned Handling | Test Strategy |
|---|---|---|---|
| Create session | DB unavailable | Retry 3x, then error page | Integration test with DB down |

The `[UNPLANNED]` marker is the highest-value output — it forces planning or an explicit `[OUT OF SCOPE — reason]` declaration. Every `[UNPLANNED]` must be resolved before implementation. Start with external service operations.

**Shadow Paths** — each cell describes what the *user sees*, not what the system does:

| Flow | Happy Path | Nil Input | Empty Input | Upstream Error |
|---|---|---|---|---|
| User registration | Account → welcome email | 422 + field errors | 422 + "required" msg | 503 + retry prompt |

**Interaction Edge Cases** — standard four for any interactive feature, plus feature-specific:

| Edge Case | Planned Handling |
|---|---|
| Double-click submit | Debounce — disable after first click |

A payment form needs "card declined." A search needs "rapid keystrokes." Think about what's specific to *this* feature.

**Shared Format Principle:** Discrepancies between spec error mapping and `/review`'s code analysis are drift signals. An `[UNPLANNED]` that remains unhandled in code is a critical gap.

#### Step 2.9: Final Package Review

Present the complete package: file tree, story count and total task count, key items for the user to review (accuracy, story sizing, missing requirements), and suggested next steps.

## Completion

This command succeeds when all of:

1. **Contract was locked** — the user explicitly approved the specification contract
2. **Spec package exists** — `spec.md`, `spec-lite.md`, all story files, and `user-stories/README.md` are written
3. **Stories are actionable** — each story has 3-5 acceptance criteria (Given/When/Then) and 5-7 implementation tasks
4. **Sub-specs generated** — `technical-spec.md` and any additional sub-specs the contract requires exist in `sub-specs/`
5. **Package reviewed** — the final package summary was presented to the user

If `--from-prototype`: Story 1 is marked `Completed ✅` with all tasks checked. If `--from-issue`: the source issue file's `spec_ref` line is updated with the spec path.

**Suggested next step:** `/implement-spec` to execute the full implementation pipeline, or `/implement-story` for individual stories.

**Terminal constraint:** This command produces specification artifacts (`.writ/specs/{date}-{name}/`). Do not offer to implement, build, or execute what was specified. For implementation, the user should run `/implement-spec` or `/implement-story`. For quick prototyping, use `/prototype`.

## Example Usage

### Example: Feature Provided with Full Flow

```
Developer: /create-spec "real-time multiplayer chat with blockchain integration"

Agent: [Scans existing code, finds a simple React app with basic authentication]
       [Switches to Plan Mode for discovery]

--- PLAN MODE ---

I found your existing React application with basic user authentication.
Before I dive in, I'm noticing a potential concern: real-time chat typically
requires sub-100ms latency, but blockchain transactions can take seconds
or minutes. What problem does blockchain solve in this chat context?

Developer: We want spam prevention via crypto micropayments and eventually
permanent message storage, but spam prevention is the must-have.

Agent: That makes sense. If spam prevention is the core value, we need the
blockchain interaction to not block the real-time UX. I'm thinking a hybrid
approach — messages deliver instantly, blockchain settlement happens in the
background. Does that match your mental model, or do you need messages to
be confirmed on-chain before they're visible?

Developer: Hybrid is exactly right. Instant delivery, background settlement.

Agent: Good. For the cost target — Ethereum mainnet would be $1-5+ per message
during congestion, which kills the micropayment model. A Layer 2 like Polygon
would put you in the $0.01-0.10 range. Do you have a target cost per message,
or should I recommend based on the spam prevention use case?

Developer: $0.01-0.10 range sounds right. What happens if settlement fails?

Agent: Three options: hide the message until settled (bad UX), show with a
"pending" badge (confusing for chat), or show normally and notify the user
only if settlement fails (cleanest UX, rare failure case). I'd recommend
the third — it keeps chat feeling real-time. Thoughts?

Developer: Agreed, show normally and notify on failure. I think that covers it.

Agent: Here's the contract:

## Specification Contract

**Deliverable:** Hybrid real-time chat with immediate message delivery and
background Polygon verification for anti-spam

**Must Include:** Sub-second message delivery while maintaining blockchain
verification for spam prevention

**Hardest Constraint:** Balancing real-time UX with blockchain settlement
delays and gas cost management

**⚠️ Technical Concerns:**
- Background settlement failures need graceful handling and user notification
- Wallet integration adds authentication complexity to existing simple auth
- Need message batching strategy to keep costs in target range

**💡 Recommendations:**
- Use Polygon for $0.01-0.10 per message cost target
- Implement message batching to settle multiple messages per transaction
- Add fallback mode for when blockchain settlement fails

**Success Criteria:** Messages appear instantly, spam is prevented via crypto
payments, blockchain verification happens within 5 minutes

**Scope Boundaries:**
- Included: Real-time chat, wallet integration, background Polygon settlement
- Excluded: Advanced chat features (file sharing, voice), custom token
  creation, permanent storage (deferred to v2)

Developer: Looks good, let's lock it.
           [Switches back to Agent Mode → AskQuestion confirms → Phase 2 begins]
```

**Key UX difference:** The discovery conversation felt natural — open-ended questions, real dialogue, collaborative pushback. The AskQuestion confirmation at the end is a clean gate before file creation. Plan Mode for discovery, AskQuestion for decisions.

---

## References

- Standing instructions: [`commands/_preamble.md`](_preamble.md)
- Identity & Prime Directive: [`system-instructions.md`](../system-instructions.md)
