# Create ADR Command (create-adr)

## Overview

Create comprehensive Architecture Decision Records (ADRs) that systematically document architectural decisions with clear rationale, alternatives considered, and consequences through a structured analysis and review process.

## When to Use

- Making significant architectural decisions that affect system structure or design
- Documenting technology choices with vendor lock-in or high switching costs
- Recording decisions contrary to team expectations or industry standards
- Capturing complex trade-offs between competing architectural approaches
- Establishing architectural patterns and standards for team consistency
- Onboarding new team members to architectural reasoning and context
- Creating audit trails for compliance and governance requirements

## Prerequisites

**MANDATORY:** This command **automatically executes research** if no relevant research exists. The ADR creation process will:

1. Check for existing research on the decision topic
2. If no research found: **automatically read and execute** the complete research workflow from `commands/research.md`
3. Only proceed with ADR creation after research is completed and documented

## Command Process

### Step 0: Check for Existing Research and Auto-Execute if Missing

**Objective:** Ensure comprehensive research exists before creating ADR - automatically execute research if missing

**Actions:**

1. **Check for existing research:**

   - Use `Grep` to search for related research content in `.writ/research/` directory
   - Search for research documents that might relate to the architectural decision
   - Use `Glob` to explore the research directory structure (e.g., `.writ/research/*.md`)

2. **Automatic research execution if missing:**

   ```
   If no relevant research found:
   "❌ No existing research found for this architectural decision.

   Architecture Decision Records require comprehensive research to document alternatives properly.

   🔄 AUTOMATICALLY EXECUTING RESEARCH WORKFLOW FIRST...

   Reading commands/research.md and executing complete research process..."
   ```

3. **Execute research workflow automatically:**

   - **IMMEDIATELY** use `Read` to read `commands/research.md`
   - **EXECUTE** the complete 4-phase research methodology as defined in research.md:
     - Phase 1: Define Research Scope
     - Phase 2: Initial Discovery
     - Phase 3: Deep Dive Analysis
     - Phase 4: Synthesis and Recommendations
   - **CREATE** research document in `.writ/research/{date}-{topic}-research.md`
   - **ONLY CONTINUE** with ADR creation after research is completed

4. **Handle research workflow:**
   - If no research found: **AUTOMATICALLY execute complete research workflow first**
   - If existing research found: Load and reference it throughout the ADR process
   - If research is incomplete: Execute additional research before continuing

**Deliverables:**

- Research availability assessment
- **Completed research documentation** (auto-executed if missing)
- Research document ready for ADR reference

### Step 1: Analyze Decision Context and Current State

**Objective:** Understand the current architectural state and decision context before proceeding

**PREREQUISITE:** This step only begins AFTER Step 0 confirms research exists or completes automatic research execution

**CRITICAL:** If Step 0 executed research automatically, load and reference the newly created research document

**Create todo tracking:**

Use `todo_write` to track the ADR creation process:

```json
{
  "todos": [
    {
      "id": "check-research",
      "content": "Check for existing research and auto-execute if missing",
      "status": "completed"
    },
    {
      "id": "execute-research",
      "content": "Execute complete research workflow (auto-completed if needed)",
      "status": "completed"
    },
    {
      "id": "analyze-context",
      "content": "Analyze decision context and current architectural state",
      "status": "in_progress"
    },
    {
      "id": "define-scope",
      "content": "Define decision scope and evaluation criteria",
      "status": "pending"
    },
    {
      "id": "research-alternatives",
      "content": "Research alternatives and evaluate options",
      "status": "pending"
    },
    {
      "id": "document-adr",
      "content": "Document ADR with decision rationale",
      "status": "pending"
    }
  ]
}
```

**Analysis Actions:**

1. **Understand current architectural patterns:**

   - Use `codebase_search` with queries:
     - "What architectural patterns are currently in use?"
     - "How are similar decisions handled in the codebase?"
     - "What dependencies and integrations exist?"

2. **Find existing ADRs and documentation:**

   - Use `file_search` to find existing ADRs in `.writ/decision-records/` directory
   - Use `list_dir` to explore system structure and identify affected components

3. **Gather decision context:**
   - Identify decision stakeholders and their concerns
   - Determine the specific decision that needs to be made and its urgency
   - Document current architectural context summary

**Deliverables:**

- Current architectural context summary
- Decision scope and stakeholder identification
- Existing ADR inventory and numbering

### Step 2: Define Decision Scope and Criteria

**Objective:** Clearly define what decision needs to be made and establish evaluation criteria

**Actions:**

1. **Define the specific architectural decision** requiring documentation

2. **Identify driving forces and constraints:**

   - Business requirements and goals
   - Technical constraints and limitations
   - Performance, security, and scalability requirements
   - Team skills and organizational capabilities
   - Timeline and budget constraints

3. **Establish decision criteria and priorities**

4. **Determine decision maker(s) and approval process**

5. **Set boundaries for the decision scope**

**Deliverables:**

- Clear problem statement
- Decision criteria and evaluation framework
- Stakeholder roles and responsibilities
- Decision timeline and process

### Step 3: Research Alternatives and Evaluate Options

**Objective:** Systematically research and evaluate alternative approaches to the architectural decision

**Research Actions:**

1. **Leverage existing research (if found in Step 0):**

   - Review research documents from `.writ/research/` for relevant findings
   - Extract key insights, alternatives, and recommendations from prior research
   - Identify gaps in existing research that need additional investigation

2. **Conduct additional web research as needed:**

   - "[technology/pattern] architectural approaches"
   - "[decision area] best practices"
   - "[technology] vs [alternative] comparison"
   - "[pattern] pros and cons"
   - "[industry/domain] architecture patterns"
   - "[scale] architecture examples"

3. **Use `codebase_search` to understand current implementation approaches**

4. **Identify and document alternative options:**
   - Current state or status quo option
   - Industry standard approaches
   - Innovative or emerging alternatives
   - Hybrid approaches combining multiple patterns

**Evaluation Framework:**

For each alternative, evaluate against established criteria:

- Technical feasibility and complexity
- Performance and scalability implications
- Security and compliance considerations
- Development effort and timeline
- Long-term maintenance and evolution
- Risk assessment and mitigation strategies

**Deliverables:**

- Comprehensive alternatives analysis
- Pros and cons evaluation matrix
- Risk assessment for each option
- Expert opinions and team input summary

### Step 4: Document ADR with Decision Rationale

**Objective:** Create comprehensive ADR documentation with clear decision rationale and consequences

**Preparation Actions:**

1. **Get current date for document content:**

   ```bash
   npx @devobsessed/writ date
   ```

2. **Determine ADR number:**

   - Check existing ADRs in `.writ/decision-records/` directory
   - Use sequential numbering (0001, 0002, etc.)

3. **Create ADR directory structure:**

   Create the decision records directory:

**ADR Creation:**

Create markdown file: `.writ/decision-records/NNNN-decision-title.md`

**ADR Document Template:**

```markdown
# NNNN. [Decision Title]

**Date:** [Use output from npx @devobsessed/writ date]

**Status:** [Proposed/Accepted/Deprecated/Superseded]

**Deciders:** [Names or roles of decision makers]

**Technical Story:** [Brief reference to related issue, epic, or requirement]

## Context and Problem Statement

[Describe the architectural problem or decision that needs to be made. Include the business context, technical context, and driving forces that led to this decision being necessary.]

### Driving Forces

- **Business Driver 1:** [e.g., Need to support 10x user growth]
- **Technical Driver 2:** [e.g., Current monolith becoming unmaintainable]
- **Organizational Driver 3:** [e.g., Team scaling requires better separation of concerns]

### Assumptions

- [Any assumptions made during the decision process]
- [External dependencies or constraints assumed to remain stable]

## Decision Drivers

[List the key factors that influenced this architectural decision, in order of importance]

- **Driver 1:** [e.g., Scalability requirements]
- **Driver 2:** [e.g., Team autonomy and development velocity]
- **Driver 3:** [e.g., Technology stack modernization]
- **Driver 4:** [e.g., Operational complexity management]

## Considered Options

### Option 1: [Name of option, e.g., "Maintain Current Monolithic Architecture"]

**Description:** [Brief description of this approach]

**Pros:**

- [Positive aspect 1]
- [Positive aspect 2]

**Cons:**

- [Negative aspect 1]
- [Negative aspect 2]

**Effort:** [Implementation effort assessment]

**Risk:** [Risk level and key risks]

### Option 2: [Name of option, e.g., "Migrate to Microservices Architecture"]

**Description:** [Brief description of this approach]

**Pros:**

- [Positive aspect 1]
- [Positive aspect 2]

**Cons:**

- [Negative aspect 1]
- [Negative aspect 2]

**Effort:** [Implementation effort assessment]

**Risk:** [Risk level and key risks]

### Option 3: [Name of option, e.g., "Hybrid Modular Monolith Approach"]

**Description:** [Brief description of this approach]

**Pros:**

- [Positive aspect 1]
- [Positive aspect 2]

**Cons:**

- [Negative aspect 1]
- [Negative aspect 2]

**Effort:** [Implementation effort assessment]

**Risk:** [Risk level and key risks]

## Decision Outcome

**Chosen Option:** [Selected option with brief rationale]

### Rationale

[Detailed explanation of why this option was selected over the alternatives. Reference the decision drivers and how this option best addresses them.]

### Confirmation

[How will we know this decision is working? What metrics or indicators will we monitor?]

## Consequences

### Positive Consequences

- [Positive outcome 1 - what improvements this decision enables]
- [Positive outcome 2 - what capabilities this decision provides]
- [Positive outcome 3 - what risks this decision mitigates]

### Negative Consequences

- [Negative outcome 1 - what complexities this decision introduces]
- [Negative outcome 2 - what trade-offs this decision requires]
- [Negative outcome 3 - what new risks this decision creates]

### Mitigation Strategies

- [Strategy 1 for addressing negative consequences]
- [Strategy 2 for managing introduced complexities]

## Implementation Notes

### Prerequisites

- [What needs to be in place before implementing this decision]
- [Dependencies that must be resolved first]

### Implementation Steps

1. [Step 1 - immediate actions required]
2. [Step 2 - follow-up activities]
3. [Step 3 - validation and monitoring setup]

### Success Criteria

- [Measurable criteria for successful implementation]
- [Timeline for achieving implementation milestones]

## Follow-up Actions

- [Action item 1 with owner and timeline]
- [Action item 2 with owner and timeline]
- [Review date for evaluating decision effectiveness]

## References

- [Link to related ADRs]
- [Prior research documents from .writ/research/ (if applicable)]
- [External documentation, articles, or research]
- [Code repositories or examples]
- [Meeting notes or discussion records]

## Related Decisions

- [ADR-XXXX: Related decision that influences this one]
- [ADR-YYYY: Decision that this one supersedes or is superseded by]
```

**Review and Finalization:**

1. **Review ADR with stakeholders and decision makers**
2. **Update ADR status based on team consensus and approval**
3. **Link related ADRs to show decision evolution**
4. **Commit ADR to version control**

**Deliverables:**

- Comprehensive ADR document in `.writ/decision-records/NNNN-decision-title.md`
- Stakeholder review and approval record
- Updated todo status marking completion

## Best Practices

### Decision Scope and Focus

- Focus on one significant architectural decision per ADR
- Clearly separate the problem from potential solutions
- Include sufficient context for future readers to understand the decision
- Document the decision even if it seems obvious at the time
- Consider both technical and business implications

### Alternatives Analysis

- Always include the "do nothing" or "status quo" option
- Research industry standards and best practices
- Consider both short-term and long-term implications
- Include effort and risk assessments for each option
- Seek diverse perspectives and expert opinions

### Decision Documentation

- Use clear, jargon-free language that new team members can understand
- Include relevant diagrams, code examples, or architectural sketches
- Reference external sources and supporting documentation
- Document both positive and negative consequences honestly
- Plan for decision review and potential revision

### Stakeholder Engagement

- Involve all teams affected by the architectural decision
- Allow time for thoughtful review and feedback
- Document dissenting opinions and how they were addressed
- Ensure decision makers have sufficient context and time
- Follow up on implementation and measure success

### ADR Management

- Maintain sequential numbering for easy reference
- Store ADRs in version control alongside code
- Link related ADRs to show decision evolution
- Update status when decisions are superseded or deprecated
- Regular review of ADR effectiveness and team satisfaction

## Common Pitfalls to Avoid

### Decision Process Issues

- Rushing to document a decision without proper analysis
- Making decisions in isolation without stakeholder input
- Failing to research alternative approaches thoroughly
- Not considering long-term consequences and evolution
- Avoiding difficult trade-off discussions

### Documentation Problems

- Writing ADRs that are too technical for business stakeholders
- Failing to include sufficient context for future understanding
- Not updating ADR status when decisions change
- Creating ADRs for trivial decisions that don't warrant documentation
- Writing overly long ADRs that obscure the key decision

### Team and Process Challenges

- Not establishing clear decision-making authority
- Failing to follow up on implementation and monitoring
- Creating ADRs after decisions are already implemented
- Not linking ADRs to related architectural documentation
- Ignoring dissenting opinions without proper consideration

### Maintenance and Evolution

- Letting ADRs become stale or outdated
- Not reviewing and learning from past decisions
- Failing to update related ADRs when superseding decisions
- Not considering the cumulative effect of multiple ADRs
- Avoiding difficult conversations about failed decisions
