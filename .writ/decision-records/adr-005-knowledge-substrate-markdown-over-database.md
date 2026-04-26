# ADR-005: Knowledge Substrate — Markdown Ledger over Database

> **Status:** Proposed
> **Date:** 2026-04-24
> **Deciders:** Product owner
> **Part of:** Strategic response to GStack rigor comparison
> **Supersedes:** None
> **Related:** ADR-003 (Context Engine Architecture) — complementary; ADR-003 covers intra-spec context delivery, this ADR covers cross-spec, cross-session knowledge accumulation

## Context

Writ already persists structured knowledge across multiple artifact types:

| Artifact | What it captures | Scope |
|---|---|---|
| `.writ/specs/<slug>/spec.md` | Feature contract, acceptance criteria, business rules | Per-feature |
| `.writ/specs/<slug>/drift-log.md` | Spec-vs-implementation deltas | Per-feature |
| `.writ/decision-records/adr-NNNN.md` | Architectural choices with rationale | Per-decision |
| `.writ/research/<topic>.md` | Investigation outputs feeding decisions | Per-topic |
| Story `## What Was Built` sections (ADR-003) | What each story produced | Per-story |

These cover most of what Writ needs to record. They do **not** cover a category of knowledge that accumulates as a project matures and is consulted by agents on every task:

- "This codebase uses pattern X for Y" (conventions discovered through use, not a per-feature decision)
- "Library Z has gotcha W — we hit it on 2026-03-04" (lessons that aren't tied to any single spec)
- "Domain term 'sprint' means a 2-week iteration here, not 8 weeks" (glossary/vocabulary)
- "We tried X for caching, it failed because Y" (postmortem-style learnings worth carrying forward)

Today, this knowledge lives wherever it falls — sometimes in code comments, sometimes scattered across specs, often only in the maintainer's head. When an agent starts a new task, this context is unavailable unless the maintainer remembers to include it in the prompt. Across sessions, machines, and contributors, it does not survive at all.

The recent comparison with GStack ([`.writ/research/2026-04-24-writ-vs-gstack-rigor-comparison.md`](../research/2026-04-24-writ-vs-gstack-rigor-comparison.md), Findings 8 and 9) surfaced this gap and recommended building a dedicated knowledge layer. This ADR decides **what shape that layer takes** — specifically, whether to follow GStack's database approach (GBrain) or use a plain-text approach native to git.

**The question this ADR answers:** What is the storage substrate for Writ's cross-cutting accumulated knowledge — a database, a markdown directory, an external system, or something hybrid?

**Out of scope (decided elsewhere or later):**

- Whether to build the knowledge layer at all → Implied yes; the spec for v1 of `.writ/knowledge/` will follow this ADR
- The exact directory structure inside `.writ/knowledge/` → Implementation detail for the spec
- How `/research`, `/create-adr`, `/create-spec` interact with the layer → Subsequent decisions
- Indexing, retrieval optimization, or any cross-machine sync → Only if measured need emerges

## Decision Drivers

Force-ranked top three drivers — these are what tip the decision:

1. **Reviewability for team collaboration.** Writ's stated near-term audience is small teams. Knowledge changes must be inspectable in pull requests, commentable line-by-line, and rejectable at review time. Anything that bypasses code review for knowledge is unacceptable for a team artifact.

2. **Auditability for production-grade output.** Writ's stated quality goal is production-grade output. A new contributor or auditor should be able to reconstruct *why* the codebase looks the way it does, six months later, from the artifacts alone — without an oral history session.

3. **Solo-maintainer cost ceiling.** Writ has one maintainer. The v1 implementation budget is ≤4 days. Ongoing operational cost must be near zero — no databases to administer, no infrastructure to maintain, no separate backup story.

Other relevant factors (real but lower-priority):

- **Onboarding-friendliness** — new contributor clones the repo, finds the knowledge
- **Reproducibility across machines** without external infrastructure
- **Survival across AI platform churn** (Cursor → Claude Code → next-gen agent)
- **Composition with existing Writ artifacts** — must not duplicate or contradict specs, ADRs, research, drift logs
- **Retrieval performance** — agents must be able to find relevant knowledge quickly enough

## Considered Options

### Option 1: Status Quo — No Dedicated Knowledge Layer

**Approach:** Continue without a dedicated knowledge layer. Knowledge lives in specs, ADRs, research, code comments, drift logs, and agent memory. Cross-cutting knowledge that doesn't fit any of those goes nowhere.

**Pros:**

- Zero implementation cost
- No new artifact type to maintain or document
- Existing artifacts (specs/ADRs/research) already cover most knowledge categories
- Avoids premature abstraction — we may not actually need a new layer

**Cons:**

- The categories listed in Context (conventions, lessons, glossary) genuinely have no home today
- Knowledge that lives only in maintainer memory does not survive context-window resets, machine changes, or contributor turnover
- Agents repeatedly re-derive context they should be loading from disk
- The team-collaboration goal (Finding 9 of the research doc) requires a shared knowledge substrate; status quo blocks it

**Effort:** None

**Risk:** Medium — the gap is real and growing; postponing has compounding cost

**Verdict:** Considered, rejected — the gap is genuine and the team-collab goal makes addressing it strategic, not optional

### Option 2: Markdown Ledger in `.writ/knowledge/` (Recommended)

**Approach:** A directory of plain-text markdown files in the repo, organized by category. Authored by humans and by Writ commands; read by agents at task start via grep + context loading. Versioned in git like all other Writ artifacts.

Initial structure (subject to refinement during the implementation spec):

```
.writ/knowledge/
├── decisions/      # "We chose X because Y" — small decisions that don't warrant a full ADR
├── conventions/    # "This codebase uses pattern Z for tests"
├── glossary/       # Domain terminology, one file per concept
└── lessons/        # "We tried X, it failed because Y"
```

Each file is timestamped (`YYYY-MM-DD-short-slug.md`) and has a minimal frontmatter (category, tags, related artifacts). Retrieval is initially grep-based — agents are pointed at relevant subdirectories by command logic.

**Pros:**

- **Drivers 1 and 2 (reviewability, auditability):** every entry is a markdown file in git; full history visible in `git log`; line-by-line review in PRs; never silently mutated
- **Driver 3 (cost):** v1 is a directory, a frontmatter convention, and minimal command integration — well within the 4-day budget; zero ongoing operational cost
- **Onboarding:** new contributor reads `.writ/knowledge/` like documentation
- **Platform-agnostic:** survives any AI tool change because the substrate is the filesystem
- **Composes with existing artifacts:** entries can link to specs/ADRs/research; no duplication needed
- **Reversible:** if the approach proves wrong, deletion is one command; no migration burden

**Cons:**

- **Retrieval is initially slower than a database** — grep over hundreds of files is fine; over hundreds of thousands, it would not be. Mitigation: when corpus growth reaches that scale, an *index* over the markdown can be added without changing the source of truth.
- **No structured query** — "show me all lessons about caching from the last 3 months" requires either grep gymnastics or a future indexer
- **Discipline-dependent** — without a clear schema and command-driven authoring, the directory can become a junk drawer
- **Risk of duplicating ADRs/specs/research** if the boundaries aren't enforced — a "decision" entry in `.writ/knowledge/decisions/` could overlap with an ADR if rules aren't clear

**Effort:** S-M (2–4 days for v1: directory layout + frontmatter spec + minimal `/knowledge` command for read/write + agent context-loading hook)

**Risk:** Low — failure mode is "directory underused," which is reversible at zero cost

**Verdict:** Recommended

### Option 3: Local Database (GBrain-Style)

**Approach:** Mirror GStack's GBrain pattern — embedded Postgres (PGLite) by default, optional Supabase for cross-machine sync. Knowledge stored as rows with structured schema. Skills/commands query and write via SQL or a thin abstraction layer. Per-remote trust policy for what agents on which machines can access which keyspaces.

**Pros:**

- Fast indexed retrieval at scale (the original strength)
- Built-in cross-machine sync via Supabase
- Structured queries enable analytics ("what conventions do we cite most in code reviews?")
- Schema enforcement prevents the junk-drawer failure mode of Option 2
- Proven design — GStack ships it and presumably it works for them

**Cons (against drivers):**

- **Driver 1 (reviewability) — fails:** A teammate cannot review a colleague's GBrain entries the way they'd review a markdown file. Database changes don't show up in PRs in any useful form.
- **Driver 2 (auditability) — fails or partial:** Postgres has change-data-capture, but no human-readable diff history per knowledge entry. "Why was this entry written?" is much harder to answer than for a git-versioned file.
- **Driver 3 (cost) — fails:** Implementing GBrain-equivalent functionality is weeks, not days. Operational cost is non-zero — schema migrations, backup story, sync conflict resolution. Far over the 4-day v1 budget.
- **Onboarding — fails:** New team member runs setup, gets an empty database; the team's institutional knowledge lives in someone else's PGLite instance. Plain-text-in-repo solves this for free.
- **Reproducibility — degrades:** Local-first PGLite means each developer's GBrain diverges silently between syncs.
- **Survivor-bias concern:** GStack's adoption signal (82.4k stars) measures attention, not in-anger production usage by teams. The research doc explicitly hedged this. We don't have independent evidence GBrain works for *team* knowledge management — it's documented as "AI agents that remember across conversations and machines," which is a single-user framing.

**Effort:** L (3–6 weeks for a credible implementation, plus ongoing operational burden)

**Risk:** High — wrong shape for the audience; expensive to roll back once data is in the database

**Verdict:** Rejected

### Option 4: Hybrid — Markdown Source of Truth + SQLite Index

**Approach:** Keep markdown as canonical (Option 2 substrate), but maintain a SQLite index built from the markdown for fast queries. Index is a derived artifact, regenerable from source.

**Pros:**

- Preserves all of Option 2's reviewability/auditability/onboarding wins
- Fast structured queries for retrieval-heavy use cases
- Index is throwaway — no migration risk
- Future-proofs for scale without committing to it now

**Cons:**

- **Hybrid bias warning** (per the `/create-adr` command guidance) — combines two things, often hides integration cost
- Index staleness — must regenerate on every commit/edit, or queries return stale data
- Two systems to debug when retrieval misbehaves
- Premature optimization — agents don't currently need indexed queries; grep over a few hundred files is sub-second
- The implementation spec for v1 would balloon from "directory + frontmatter + command" to "directory + frontmatter + command + indexer + index schema + invalidation logic + query layer"

**Effort:** M (1–2 weeks for a credible hybrid implementation)

**Risk:** Medium — the index layer is a non-trivial moving part; can be added later if grep proves inadequate, with no source-of-truth migration

**Verdict:** Considered, deferred — Option 2 first; revisit if and only if grep-based retrieval is measurably inadequate

### Option 5: External Knowledge Tool (Notion, Obsidian, Hosted Wiki)

**Approach:** Don't build a Writ-internal layer. Point users at an external knowledge tool (Notion, Obsidian vault, GitHub wiki, etc.). Provide conventions for how Writ commands reference external URLs.

**Pros:**

- Zero implementation cost in Writ itself
- Leverages mature tools with rich UX
- Users already have their preferred knowledge tools

**Cons:**

- **Not in the repo** — agents cannot reliably load context from arbitrary external systems
- **Not survivable** — Notion outage, Obsidian price change, wiki vendor sunset, all break Writ's knowledge layer
- **Not reproducible** — clone the repo, you get nothing
- **Auth/access nightmare** for team scenarios — every agent needs credentials to every external system
- **Defeats Writ's plain-text-in-repo philosophy** — the same philosophy that makes specs and ADRs work
- **Different per user** — one teammate uses Notion, another Obsidian; collaboration requires picking one and forcing it on the team

**Effort:** None for Writ; high coordination cost for users

**Risk:** High strategic risk — outsources a core capability to systems Writ does not control

**Verdict:** Rejected

## Decision

**Chosen: Option 2 — Markdown Ledger in `.writ/knowledge/`**

### Rationale

The decision is determined by Drivers 1 and 2, which Option 2 satisfies and Options 3 and 5 fail outright:

**Driver 1 (reviewability) is non-negotiable for the team-collaboration goal.** Knowledge that bypasses code review is not team knowledge — it is one person's notes. Markdown files in git pass through the same review and approval flow as code, by construction. Database rows do not.

**Driver 2 (auditability) is non-negotiable for the production-grade output goal.** "Why is this convention in place?" must be answerable from the artifacts. `git log` on a markdown file gives a complete answer including the message of the commit that introduced it. Database change history rarely gives the same.

**Driver 3 (solo-maintainer cost) makes Option 3 infeasible regardless of the other drivers.** A 4-day budget cannot fund a credible database-backed implementation; Option 3 is weeks of work plus ongoing operational burden.

Option 4 (hybrid) is the most plausible alternative and is explicitly *deferred*, not rejected. The indexer can be added later as a derived artifact with no source-of-truth migration. Premature complexity is the more dangerous failure mode here.

### What This Commits Writ To

- `.writ/knowledge/` will be the canonical location for cross-cutting accumulated knowledge
- Every entry is a plain-text markdown file with frontmatter, versioned in git
- No database, no external system, no proprietary format will be introduced as the source of truth
- Retrieval is grep-based for v1; an index layer can be added later if and only if measured retrieval performance becomes inadequate

### What This Does Not Commit Writ To

- The exact directory structure (decisions/conventions/glossary/lessons is a starting proposal, not a contract — refined in the implementation spec)
- A specific authoring command (whether knowledge is written via `/knowledge`, via `/research`, via spec creation, or directly is an implementation question)
- Any cross-machine sync mechanism beyond `git push`/`git pull`
- Any retrieval API beyond what agents already do with markdown files

## Consequences

### Positive

- **Team-ready substrate** — knowledge changes flow through PRs like everything else
- **Auditable by default** — git log + line-level diffs + commit messages = full history
- **Onboarding works** — clone repo, read `.writ/knowledge/`, you have the project's accumulated context
- **Survives platform churn** — markdown in a directory works on any AI platform Writ adapts to
- **Composes with existing artifacts** — entries can cross-reference specs, ADRs, research, drift logs without duplication
- **Cheap to revert** — `rm -rf .writ/knowledge/` is the rollback; no data migration

### Negative

- **Retrieval is grep-bounded** — at corpus sizes the project doesn't currently approach, this would become a performance issue. Mitigation: Option 4 (markdown + SQLite index) remains available as a non-breaking upgrade path.
- **Discipline-dependent** — without enforced conventions and command-driven authoring, the directory can degrade into a junk drawer. Mitigation: implementation spec must define a frontmatter schema and at least one command (`/knowledge` or equivalent) that enforces it.
- **Boundary risk with existing artifacts** — "decision" entries in `.writ/knowledge/decisions/` could shade into ADR territory if the boundary is fuzzy. Mitigation: implementation spec must clearly delineate when something belongs in `.writ/knowledge/` vs `.writ/decision-records/` vs `.writ/research/` (rough rule: ADRs for architectural choices with serious blast radius; research for investigations that produced specific recommendations; knowledge for the smaller, accumulating, cross-cutting facts that don't fit either).
- **No structured queries today** — "show me all lessons about caching" requires grep. For now, that is a feature (forces agents to scan and synthesize) not a bug.

### Risks

| Risk | Likelihood | Impact | Mitigation |
|---|---|---|---|
| Junk-drawer drift — directory accumulates noise without structure | Medium | Medium | Implementation spec defines frontmatter schema + an authoring command that enforces it |
| Boundary confusion with specs/ADRs/research | Medium | Medium | Implementation spec includes a one-page "what goes where" decision tree; this ADR's "What This Commits Writ To" section is the contract |
| Premature scale concerns — someone argues for indexing before there's a real need | Low | Low | This ADR explicitly defers Option 4; require measured retrieval-performance evidence before introducing the index |
| Knowledge becomes orphaned — entries written, never read by agents | Medium | High | Implementation spec requires agents to load relevant knowledge subdirectories at task start; usage is part of the success criteria |
| Conflict with `What Was Built` records (ADR-003) — both are persistent post-task records | Low | Low | Different scopes: `What Was Built` is per-story implementation records bound to a spec; knowledge ledger is cross-spec institutional facts. Boundary is documented in the implementation spec. |

### Review Triggers

This ADR should be revisited if any of the following occur:

1. **Retrieval becomes measurably slow** — if agent task latency is dominated by knowledge-loading time, evaluate Option 4 (markdown + index)
2. **The directory becomes a junk drawer** — if `.writ/knowledge/` grows to >100 entries with no discernible structure or usage, revisit the schema and authoring discipline before scaling further
3. **Team collaboration adoption fails** — if real teams (≥2 contributors) try Writ and report that the knowledge layer doesn't serve them, the failure mode informs whether the issue is shape (markdown vs database) or surface area (commands, conventions, integration)
4. **An agent platform makes structured knowledge first-class** — if Cursor/Claude Code/etc. ship native primitives for persistent knowledge that solve the problem better, evaluate whether the markdown layer should integrate, defer to, or persist independent of them

## Implementation Notes

### Prerequisites

- Implementation spec at `.writ/specs/<date>-knowledge-ledger/` — should be the next `/create-spec` invocation
- Implementation spec must define:
  - Frontmatter schema (minimum: category, tags, created, related artifacts)
  - Directory structure (validate or refine the decisions/conventions/glossary/lessons proposal)
  - Authoring command(s) and conventions
  - Agent integration — how and when agents load knowledge subdirectories
  - "What goes where" decision tree distinguishing knowledge from specs/ADRs/research

### Key Implementation Steps (informational, not normative)

1. Define the frontmatter schema and document it in the implementation spec
2. Create `.writ/knowledge/` with a `README.md` explaining the structure and authoring rules
3. Add a `/knowledge` command (or similar) that creates conformant entries from a CLI prompt
4. Update agent context-loading in `commands/implement-story.md` and the orchestrator to surface relevant knowledge subdirectories at task start
5. Backfill 5–10 high-value initial entries from existing research docs and drift logs to validate the schema before declaring v1 done

### Success Criteria

- An agent on a fresh task can find and load relevant knowledge entries without the maintainer prompting it
- New contributor can read `.writ/knowledge/` and orient on project conventions in under 30 minutes
- After 30 days of use, the corpus has at least 10 entries authored across at least 2 categories, with no schema drift requiring rework
- Zero external dependencies introduced (no database, no service, no auth)

### Review Date

Revisit this ADR 90 days after the implementation spec ships, against the success criteria above and the review triggers in the Consequences section.

## Recorded Dissent

The research doc that informs this ADR ([2026-04-24-writ-vs-gstack-rigor-comparison.md, Open Question #3](../research/2026-04-24-writ-vs-gstack-rigor-comparison.md#honest-open-questions)) explicitly flags a counterposition worth recording here:

> "Is the knowledge ledger valuable enough to justify building it before any user has asked for it? It's an engineering investment based on extrapolation, not user research."

**The case for waiting** is real: Writ has shipped without this layer; no user has filed an issue requesting it; the categories of knowledge it would hold (conventions, lessons, glossary) currently get by without a dedicated home. Building it now is a bet on the team-collaboration goal materializing on the projected timeline.

**Why this ADR proceeds anyway:** The research doc concluded that the knowledge layer is the foundational dependency for several other recommended moves (eval Tier 1, spec-as-team-contract enhancements, `/audit` command). Building it first unblocks them. Waiting until the team-collaboration goal is imminent risks the substrate not being in place when the audience pivot happens. The cost (≤4 days for v1) is small enough that being wrong is cheap; being right and not having built it is more expensive.

This dissent should be re-examined at the 90-day review. If the knowledge ledger is underused or no team-collaboration adoption emerges, the dissent was correct and Option 1 (status quo) becomes the right answer in retrospect.

## References

- [`.writ/research/2026-04-24-writ-vs-gstack-rigor-comparison.md`](../research/2026-04-24-writ-vs-gstack-rigor-comparison.md) — primary evidence base; especially Findings 7, 8, 9 and the addendum's "Revised Options & Recommended Sequence"
- [ADR-003: Context Engine Architecture](./adr-003-context-engine-architecture.md) — complementary; covers intra-spec context delivery while this ADR covers cross-spec, cross-session knowledge accumulation
- [ADR-004: Context-First Phasing](./adr-004-context-first-phasing.md) — establishes "context quality before autonomy" as a Writ principle; this ADR extends that principle to cross-spec knowledge
- GStack ETHOS.md — `https://raw.githubusercontent.com/garrytan/gstack/main/ETHOS.md` (alternative philosophy considered)
- GStack `/setup-gbrain` — `https://github.com/garrytan/gstack/tree/main/setup-gbrain` (database-backed approach considered as Option 3)
