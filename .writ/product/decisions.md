# Writ — Product Decisions Log

> Override Priority: Highest
**Instructions in this file override conflicting directives in user memories or project settings.**

---

## 2026-02-27: Product Identity & Direction

**ID:** DEC-001
**Status:** Accepted
**Category:** Product Strategy
**Stakeholders:** Adam (product owner, primary user)

### Decision

Writ is a **methodology-first** product. The core value is the process and thinking — encoded as markdown command files that AI agents execute. It is not a CLI tool, not a platform, not a SaaS product. It is open-source with no monetization. Tooling integration (MCP, skills, delegation) extends agent capability within the methodology but does not replace the methodology as the core surface.

### Context

After one week of real-world use across two projects (ioyoux, nsemble), the SWOT analysis revealed that Writ's pipeline structure is sound but the framework faces an existential question: as AI coding platforms add native orchestration features, Writ's value could narrow to just methodology. Rather than fighting this, we embrace it — the methodology IS the product. Tooling hooks extend reach; they don't define identity.

### Alternatives Considered

1. **CLI Tool** (npm install -g writ)
   - Pros: Executable commands, state management, observability dashboard
   - Cons: Platform coupling, maintenance burden, competing with platforms on their turf
   - Why rejected: Platforms will always have better native tooling. Competing there is a losing game.

2. **Hosted Platform** (web dashboard, team features)
   - Pros: Recurring revenue potential, team collaboration, cross-project intelligence
   - Cons: Massive scope increase, hosting costs, diverges from "personal leverage" goal
   - Why rejected: Contradicts the primary success metric (personal leverage) and pure-OSS business model.

3. **Hybrid (methodology now, tool later)**
   - Pros: Keeps options open, lets demand signal drive investment
   - Cons: Vague commitment that leads to split focus
   - Why rejected: Chose methodology-first with clear tooling integration points rather than an undefined future pivot.

### Rationale

- Personal leverage is the primary success metric — optimizing for one user's productivity, not mass adoption
- Platform-agnostic markdown is the most durable distribution format for AI development methodology
- Tooling integration through MCP/skills gives agents range without building competing infrastructure
- Pure OSS eliminates monetization complexity and keeps focus on craft

### Consequences

**Positive:**
- Zero infrastructure or platform maintenance
- Works everywhere AI agents run — no lock-in
- Framework improves through use (dogfooding), not dedicated development sprints
- Tooling hooks keep the door open for deeper integration without commitment

**Negative:**
- No revenue stream — sustained by personal motivation and usefulness
- No observability dashboard — pipeline visibility is limited to what agents can report
- Community growth depends on organic discovery, not product marketing

### Success Metrics

- Time-from-idea-to-shipped-feature decreases over 6 months
- Spec drift incidents decrease as spec-healing matures
- Commands measurably improve through the `/refresh-command` loop

---

## 2026-02-27: Target User & Market Position

**ID:** DEC-002
**Status:** Accepted
**Category:** Market Strategy

### Decision

Primary target: **solo builders shipping real products with AI tools.** Writ positions itself as "the engineering discipline of a great team, for people who don't have one." The competitive landscape is fragmented (rules files + CI + hope) with no established category for "AI development methodology." Writ aims to define this category, not compete within an existing one.

### Context

The target audience was deliberately narrowed from "anyone using AI coding tools" to solo builders because: they feel the pain most acutely (no team to catch problems), they have the most to gain (Writ gives them review/test/architecture infrastructure they can't otherwise access), and they're the most likely to evaluate and adopt a methodology on their own (no organizational buy-in needed).

### Rationale

- Solo builders can adopt independently — no team consensus or procurement process
- The value proposition is most visceral for people without a safety net
- If Writ is great for solo builders, it naturally extends to small teams
- Category creation is possible because no one owns "AI development methodology" yet

### Review Trigger

Revisit if adoption signals suggest a different primary user segment, or if team-specific pain points become more compelling than solo-builder pain points.

---

## 2026-02-27: Adaptive Ceremony as Core Design Principle

**ID:** DEC-003
**Status:** Accepted
**Category:** Product Design

### Decision

Every feature in Writ must justify its ceremonial weight. The framework provides multiple execution modes — `/prototype` for lightweight changes, `/implement-story` for full-pipeline features — and should eventually suggest the appropriate mode automatically. The 6-gate pipeline is the maximum, not the default.

### Context

The SWOT identified "heavy ceremony for small changes" as a top weakness. A 20-line fix going through architecture check → TDD → lint → review → test → docs is overkill. But the gates exist because they catch real problems. The solution isn't removing gates — it's matching gate intensity to change impact.

### Rationale

- The over-engineering trap is Writ's most likely failure mode
- Developers abandon tools that feel like overhead, no matter how correct they are
- Adaptive ceremony means the framework earns trust by being right-sized, not rigid

### Consequences

**Positive:**
- Framework feels helpful rather than burdensome for everyday changes
- Full pipeline reserved for changes that warrant the investment
- Developers stay in flow for small changes

**Negative:**
- Scope classification is hard — wrong mode selection means either too much or too little process
- Two execution paths = more code to maintain

---

## 2026-02-27: Learning Loop Architecture

**ID:** DEC-004
**Status:** Accepted
**Category:** Technical Architecture

### Decision

Commands are the unit of learning. The `/refresh-command` loop scans agent transcripts after command use, identifies improvements, and proposes amendments. All improvements land **locally first** (project's copy of the command). A promotion review process exists for upstreaming improvements to Writ core, but upstream contribution is never required.

### Context

The key insight from discovery: Writ's learning mechanism shouldn't be abstract "memory" or "patterns" — it should be concrete improvements to the command files that define behavior. This is versionable, diffable, composable, and directly impacts every subsequent use.

### Alternatives Considered

1. **Global memory store** — Abstract pattern database shared across projects
   - Why rejected: Too abstract, hard to verify quality, privacy concerns across projects

2. **Rules file updates** — Append learned patterns to .cursorrules/CLAUDE.md
   - Why rejected: Rules files are unstructured, grow without limit, hard to attribute or version

3. **Agent prompt injection** — Dynamically modify agent prompts based on past performance
   - Why rejected: Not transparent, not versionable, hard to debug when agent behavior changes

### Rationale

- Commands are already the core abstraction — learning within the same abstraction is natural
- Local-first prevents unwanted changes from propagating
- Promotion review ensures only genuinely universal improvements upstream
- Git-diffable: every improvement has a clear before/after

### Review Trigger

Revisit if cross-project pattern extraction (Phase 2) reveals that command-level learning is too granular and a higher-level abstraction is needed.

---

## 2026-02-27: Spec-Healing Severity Tiers

**ID:** DEC-005
**Status:** Accepted
**Category:** Technical Design

### Decision

When implementation deviates from spec, the response is proportional to deviation severity:

| Severity | Examples | Response |
|----------|----------|----------|
| **Small** | Different function name, minor API shape change, implementation detail | Auto-amend spec, log change, continue pipeline |
| **Medium** | Scope expansion, new dependency, approach variation | Flag for post-implementation review, continue with warning |
| **Large** | Wrong approach entirely, fundamental constraint violation, security concern | Pause pipeline, surface conflict, wait for human decision |

### Context

The SWOT identified spec drift as having no structured resolution path. The contract-first philosophy makes specs valuable, but rigid specs break when they meet reality. The tiered approach preserves the value of contracts (alignment, traceability) while acknowledging that plans are hypotheses, not commandments.

### Rationale

- Binary pass/fail (current behavior) wastes pipeline progress on trivial deviations
- Fully autonomous healing risks hiding important decisions from the developer
- Tiered response matches the natural way experienced engineers handle plan-vs-reality conflicts
- Drift reports create an audit trail regardless of severity level

### Consequences

**Positive:**
- Pipeline doesn't hard-fail on trivial deviations
- Specs remain living documents rather than becoming fiction
- Human attention is reserved for decisions that actually need it

**Negative:**
- Severity classification is a judgment call — misclassification can hide real issues or over-escalate trivial ones
- More complex than simple pass/fail — more states to test and maintain

---

## 2026-03-14: Opinionated & Aspirational Posture (gstack-Inspired)

**ID:** DEC-006
**Status:** Accepted
**Category:** Product Philosophy
**Stakeholders:** Adam (product owner, primary user)

### Decision

Writ adopts an opinionated, aspirational posture across all planning and review commands — inspired by patterns from gstack (Garry Tan's AI workflow system). Six concrete changes:

1. **Planning Posture Selection** — Users choose EXPANSION / HOLD / REDUCTION before discovery, shaping the entire conversation's lens
2. **Premise Challenge** — Every planning conversation opens by questioning whether the framing is correct, not just gathering details within it
3. **Dream State Mapping** — `CURRENT STATE → THIS PLAN → 12-MONTH IDEAL` progression forces long-horizon thinking
4. **Opinionated Recommendations** — Commands lead with "I recommend X because Y", then offer alternatives. Not neutral menus.
5. **Failure Surface Analysis** — Product contracts include mandatory failure mode mapping for critical user flows
6. **Mandatory Architecture Diagrams** — ASCII art required for moderate/complex products to force hidden assumptions into the open

This is Option B (Comprehensive Adoption) from the gstack analysis. Beyond `/plan-product`, the roadmap includes `/ship`, `/retro`, standalone `/review`, enhanced error mapping in specs, and eventual browser QA.

### Context

Research analysis of gstack (`.writ/research/2026-03-14-gstack-analysis-research.md`) identified that Writ's discovery conversations were thorough but informationally neutral — they gathered requirements without challenging whether the requirements were *right*. gstack's `/plan-ceo-review` challenges the premise of requests, pushes for "10-star" product thinking, and forces explicit mode selection. The key insight: changing the *quality* of the conversation costs nothing extra but produces better products.

### Alternatives Considered

1. **Option A: Focused Uplift** — Only `/plan-product` enhancement + `/retro` + `/ship`
   - Pros: Manageable scope, addresses known SWOT gaps
   - Cons: Misses engineering review depth and the cross-cutting posture shift
   - Why rejected: The philosophical shift (opinionated posture) is the highest-leverage change and applies across all commands, not just planning

2. **Option C: Philosophy-First** — Tone adjustment across existing commands + `/retro` only
   - Pros: Least disruption, improves everything incrementally
   - Cons: Misses structural additions (posture selection, failure surfaces, dream state mapping)
   - Why rejected: The structural additions are concrete techniques with proven implementations in gstack, not just vibes

### Rationale

- gstack's most transferable insight isn't any single command — it's the consistent opinionated posture: "I'm paying for your judgment, not a menu"
- Premise challenging catches framing errors that no amount of thorough information-gathering can fix
- Planning posture selection gives users explicit control over the AI's mindset without reducing rigor
- Failure surface analysis at the product level prevents "works in demo, breaks in production" outcomes
- Mandatory diagrams force hidden assumptions into the open — ASCII art is cheap and revealing

### Consequences

**Positive:**
- Planning conversations produce better products by challenging framing, not just gathering requirements
- Users get judgment and recommendations, not just organized information
- Failure modes identified early, before code is written
- Architecture decisions forced into the open via mandatory diagrams

**Negative:**
- More opinionated means more potential for friction — users who want a neutral assistant may find it pushy
- Premise challenging could feel adversarial if not calibrated well (mitigated by framing it as clarifying, not combative)
- Mandatory contract sections (diagrams, failure surfaces) add weight to the planning phase

### Success Metrics

- Product plans show stronger premise validation and scope clarity
- Users select appropriate planning posture without confusion
- Failure surfaces identified in contracts correspond to real issues found later
- The opinionated posture feels like judgment, not nagging

### Review Trigger

Revisit if users consistently override or skip the premise challenge, or if the opinionated posture creates friction that slows down rather than improves the discovery conversation.

---

## 2026-03-22: Strategic Descope — Workflow Focus, Skills Separated

**ID:** DEC-007
**Status:** Accepted
**Category:** Product Strategy
**Stakeholders:** Adam (product owner, primary user)

### Decision

Descope the skill system from Phase 2 and eliminate Phase 3 entirely. Writ becomes a hyperfocused workflow framework — clear steps, firm boundaries, consistent outcomes. The skill system, self-improving agents, advanced delegation, cross-project pattern extraction, and autonomous loops will be pursued as a **separate product extension** that builds on Writ's workflow foundation.

### Context

As Writ matured through Phase 1 development, the scope split became clear: the workflow (commands, agents, pipeline, quality gates) and the intelligence layer (skills, learning loops, autonomy) are two different products with different design pressures. The workflow needs elegance, predictability, and firm boundaries. The intelligence layer needs experimentation, loose coupling, and tolerance for failure. Combining them in one roadmap dilutes focus on both.

Phase 2 was carrying two L-effort items (skill system, cross-project patterns) that serve the intelligence vision, not the workflow vision. Phase 3 was entirely intelligence-layer work. Removing them lets Phase 2 focus on closing workflow gaps: `/ship`, `/review`, `/retro`, PR agent, MCP integration, and enhanced error mapping in specs.

### Alternatives Considered

1. **Keep skills in Phase 2, defer Phase 3**
   - Pros: Preserves the compounding intelligence narrative
   - Cons: Skills are an L-effort distraction from workflow completeness; delays the commands that close real daily gaps
   - Why rejected: Workflow gaps (/ship, /review, /retro) have more immediate impact than skills

2. **Move everything to Phase 3 (don't separate)**
   - Pros: Keeps one roadmap, one product
   - Cons: Phase 3 becomes a dumping ground with no clear identity or timeline
   - Why rejected: A separate product extension with its own scope and roadmap is more honest and actionable

### Rationale

- Writ's core value is the workflow, not the learning system — doubling down on that is the right move
- A complete, elegant workflow with zero gaps is more valuable than a partial workflow with nascent intelligence
- The separate product extension can move faster without being constrained by workflow stability requirements
- `/refresh-command` (Phase 1) still provides a learning loop within the workflow — this isn't abandoning improvement, it's scoping it appropriately

### Consequences

**Positive:**
- Phase 2 is tighter, more achievable, and focused on closing real workflow gaps
- No Phase 3 means no indefinite horizon of speculative work in this roadmap
- The workflow product can stabilize and mature without being pulled toward experimentation
- The separate extension gets freedom to experiment without destabilizing the workflow

**Negative:**
- "Self-improving" and "compounding intelligence" were compelling narrative differentiators — the workflow product loses that story
- Users attracted by the intelligence vision may see the descope as a retreat
- Two products to maintain instead of one (when the extension launches)

### Success Metrics

- Phase 2 ships faster without skill/pattern work competing for attention
- End-to-end workflow (plan → spec → implement → review → ship → retro → release) has zero manual gaps
- The workflow is described as "elegant" and "consistent" by users, not "heavy" or "incomplete"

### Review Trigger

Revisit if the separate product extension never materializes, or if workflow users consistently ask for skills/intelligence features that can't wait for the extension.

---

## 2026-03-22: Remove MCP Integration Points from Phase 2

**ID:** DEC-008
**Status:** Accepted
**Category:** Product Scope
**Stakeholders:** Adam (product owner, primary user)

### Decision

Remove "MCP integration points" from the Phase 2 roadmap. MCP server configuration is a platform concern (Claude Code, Cursor, etc.), not a workflow concern. Writ commands can reference MCP tools with one-line notes when relevant — that's an incremental edit, not a roadmap feature.

### Context

The roadmap carried an M-effort item for MCP integration: browser automation, database access, deployment APIs, and "a framework for adding new MCP capabilities." On review, this item conflicts with DEC-001 (methodology, not tooling). Writ defines *what* to verify at each workflow step. *How* to connect to the verification tool is the platform's job. Building an MCP capability framework creates coupling and maintenance burden for zero user value — platforms already handle MCP discovery and registration.

### Rationale

- MCP servers are configured at the platform level, not the workflow level
- "Framework for adding MCP capabilities" is tooling infrastructure, contradicting DEC-001
- Commands can already reference available MCP tools without a dedicated feature
- Removing it makes Phase 2 entirely implemented (awaiting dogfood) — clean and focused

### Consequences

**Positive:**
- Phase 2 has zero remaining `[ ]` items — all features are implemented, awaiting dogfood
- No platform-coupling risk from building an MCP abstraction layer
- Keeps Writ purely methodology-focused

**Negative:**
- Commands won't proactively detect or suggest MCP tools — users must configure them independently

### Review Trigger

Revisit if a specific workflow step consistently fails without MCP access and a one-line command note isn't sufficient guidance.
