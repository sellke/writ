# Create ADR Command (create-adr)

## Overview

Create Architecture Decision Records that document significant architectural choices with clear rationale, rigorous alternatives analysis, and honest consequences. The value of an ADR is proportional to the quality of its alternatives analysis — a decision without rigorous comparison is just a post-hoc justification.

**When to use** — not every technical choice deserves an ADR. Reserve them for:

- Decisions with high switching costs or vendor lock-in
- Choosing between meaningfully different architectural approaches
- Decisions that contradict team expectations or industry conventions
- Choices future developers will ask "why did we do it this way?"
- Compliance or governance requiring an audit trail

If the answer is "we'd obviously pick X and nobody would question it," skip the ADR.

## Invocation

| Invocation | Behavior |
|---|---|
| `/create-adr` | Interactive — describe the decision to document |
| `/create-adr "API gateway pattern"` | Start with decision topic pre-loaded |

## Command Process

### Step 0: Research Prerequisite Gate

Good ADRs require evidence. Before proceeding, check whether relevant research exists.

1. Use Grep/Glob to search `.writ/research/` for documents related to the decision topic
2. **Research found** → Load it, reference throughout the process. Continue to Step 1.
3. **No research found** → Recommend `/research` first:

```
"📚 No existing research found for this topic in `.writ/research/`.

Strong ADRs depend on thorough alternatives research. Recommend running
`/research` first to build the evidence base, then return to `/create-adr`.

Proceed without research? (Not recommended — alternatives analysis will be shallow)"
```

Do NOT auto-execute `/research`. If the user insists on proceeding, continue but flag that alternatives analysis will rely on existing knowledge rather than systematic research.

---

### Step 1: Analyze Decision Context

Understand the architectural landscape before proposing anything.

**Scan the codebase:**
- Search `.writ/decision-records/` for existing ADRs — note numbering, related decisions, status
- Check whether any existing *accepted* ADR contradicts or constrains this decision — surface conflicts early rather than creating contradictory records
- Identify current architectural patterns relevant to this decision
- Map dependencies and integration points the decision affects

**Establish the decision context:**
- What specific architectural question needs answering?
- What's driving the need for this decision *now*? (Business pressure, tech debt, scaling, new requirement)
- What constraints are non-negotiable vs. flexible?

Output: a clear problem statement and understanding of the decision's blast radius.

---

### Step 2: Define Scope & Evaluation Criteria

An ADR that tries to solve three architectural questions at once solves none well. Scope tightly.

**Define boundaries:**
- What is being decided — and explicitly what is NOT
- Who the decision stakeholders are
- What timeline or urgency constraints apply

**Establish evaluation criteria.** Common dimensions:

- Performance and scalability requirements
- Security and compliance constraints
- Team capability and learning curve
- Budget and timeline pressure
- Long-term maintainability

Force-rank the top 3 drivers that will actually tip the decision. Not everything matters equally.

---

### Step 3: Research & Evaluate Alternatives

Identify at minimum three alternatives. **Always include the status quo** — it's the baseline everything else is measured against.

**Source alternatives from:**
- Research documents loaded in Step 0
- Current codebase patterns and their natural evolution
- Industry-standard approaches for this problem class
- Emerging or hybrid approaches worth considering

**Evaluate each alternative against six dimensions:**

| Dimension | What to assess |
|---|---|
| Technical feasibility | Complexity, compatibility with existing architecture, PoC confidence |
| Performance & scalability | Throughput, latency, scaling characteristics under projected load |
| Security & compliance | Attack surface changes, regulatory alignment, data handling |
| Development effort | Implementation time, required expertise, migration complexity |
| Long-term maintenance | Operational burden, upgrade path, community/vendor health |
| Risk profile | What can go wrong, likelihood, severity, reversibility |

For each alternative: description, pros, cons, effort estimate, and risk assessment. If an option has no cons listed, you haven't analyzed it thoroughly enough.

**Watch for hybrid bias.** Hybrid approaches ("take the best of both") often look best on paper but hide integration complexity and maintenance burden. Evaluate them with extra skepticism on the effort and maintenance dimensions.

The "considered options" section is the most valuable part of the ADR — it's what prevents future teams from re-litigating settled decisions. Invest the most time here.

Present the evaluation and discuss trade-offs before committing to a recommendation.

---

### Step 4: Document the ADR

**Preparation:**

1. Get the current date:
   ```bash
   npx @devobsessed/writ date
   ```
2. Determine next ADR number — check `.writ/decision-records/` for existing ADRs, use sequential `NNNN` format (0001, 0002, etc.)
3. Create the file at `.writ/decision-records/NNNN-decision-title.md`

**What an excellent ADR contains:**

| Section | Quality bar |
|---|---|
| **Title & metadata** | ADR number, date, status (`Proposed`), deciders, related issues |
| **Context & problem statement** | A reader unfamiliar with the project understands *why* this decision exists. Include driving forces — the business, technical, and organizational pressures that forced this decision point. |
| **Decision drivers** | Force-ranked criteria from Step 2. These explain *what mattered most*. |
| **Considered options** | Each option: description, pros, cons, effort estimate, risk assessment. No strawmen — present every option fairly enough that a reasonable person could have chosen it. |
| **Decision outcome** | The chosen option with rationale tied to drivers. Not "we picked X" but "we picked X *because* drivers A and B outweigh the cost of con Y." |
| **Consequences** | Honest positive AND negative consequences. Every decision has downsides — document them. Include mitigation strategies for each negative consequence. |
| **Implementation notes** | Prerequisites, key steps, success criteria, review date |
| **References** | Related ADRs, research from `.writ/research/`, external sources |

**Record dissent.** If stakeholders disagreed, document the dissenting view and how it was addressed. ADRs that read as unanimously agreed when they weren't are dishonest and breed resentment.

**The test of a good ADR:** A new team member reads it in 5 minutes and understands not just *what* was decided, but *why*, and *what was rejected and why*.

**After writing:**
1. Review against the quality bars above
2. Set status to `Proposed` — becomes `Accepted` after stakeholder review
3. Link to related ADRs (supersedes, influenced by, etc.)
4. Present the completed ADR to the user

---

## ADR Conventions

**Numbering:** Sequential four-digit format — `0001`, `0002`, `0003`. Never reuse numbers, even for deprecated ADRs.

**File location:** `.writ/decision-records/NNNN-decision-title.md`

**Status lifecycle:**

| Status | Meaning |
|---|---|
| `Proposed` | Written, awaiting review and approval |
| `Accepted` | Approved and active — guides current architecture |
| `Deprecated` | No longer relevant due to changed circumstances |
| `Superseded` | Replaced by a newer ADR (link to successor) |

Transitions: Proposed → Accepted (after review). Accepted → Deprecated OR Superseded (when circumstances change). When superseding, update both the old and new ADR with cross-references.

**Supersede, don't amend.** If an accepted decision changes materially, create a new ADR that supersedes the old one. Editing accepted ADRs destroys the historical record of *why* the original decision made sense at the time. Minor corrections (typos, broken links) are fine to edit in place.

---

## Integration with Writ

| Command | Relationship |
|---------|-------------|
| `/research` | Run *before* `/create-adr` to build the evidence base for alternatives |
| `/create-spec` | ADRs inform spec decisions; reference relevant ADRs in technical specs |
| `/create-issue` | Architectural concerns surfaced during triage may warrant an ADR |
| `/design` | Design explorations may produce ADR-worthy decisions |
