# ADR-011: Memory Interop — Markdown Canonical, Indexes Disposable

> Status: Accepted
> Date: 2026-07-09
> Deciders: Adam (product owner)
> Part of: 2026-07-09 strategic refresh (`/plan-product` audit vs. current harnesses, GStack, GBrain)
> Extends: [ADR-005](adr-005-knowledge-substrate-markdown-over-database.md) (knowledge substrate: markdown over database)

## Context

ADR-005 chose plain-text markdown in git over a database for Writ's knowledge substrate, and `mission.md` declared "not a persistent-database knowledge layer" as a non-goal. Two things changed:

1. **Native memory arrived everywhere.** Claude Code ships memdir with a maintenance loop, Cursor ships memories plus semantic codebase indexing, Hermes ships native memory. Writ projects now coexist with memory layers whether Writ acknowledges them or not.
2. **GBrain matured into best-in-class external memory** — synthesis with citations and gap analysis, a self-wiring knowledge graph with benchmarked retrieval lift, overnight consolidation. Critically, GBrain's own architecture endorses the split Writ needs: *"the brain repo is the system of record; GBrain syncs the repo into Postgres for retrieval."* The git repo stays canonical; the database is a disposable index.

The stakeholder wants Writ compatible with GBrain. The unrevised "no database layer" framing would read as prohibiting that. The audit also surfaced a self-inflicted gap: Writ's ledger is append-only with no consolidation — it will degrade, which contradicts the product's one-word mission.

## Decision Drivers

1. **Reviewability is non-negotiable** — knowledge must remain PR-reviewable, git-versioned, onboarding-friendly (ADR-005's production-grade criteria all still hold)
2. **Retrieval quality matters at scale** — grep over markdown loses to hybrid search + graph traversal as the corpus grows; pretending otherwise caps Writ's value
3. **Zero owned infrastructure** — Writ must not build or maintain retrieval engines
4. **Graceful absence** — a Writ project with no external memory must work identically; removing an index must lose zero canonical data

## Considered Options

**Option A — Pure markdown, no interop (status quo).**
Pros: simplest; no external surface. Cons: ignores the native-memory reality; leaves retrieval quality on the table; append-only ledger still degrades. Effort: none.

**Option B — Markdown canonical + documented interop with external indexes + owned consolidation. (Chosen)**
Pros: keeps every ADR-005 guarantee; gains best-in-class retrieval where users want it; blast radius of a moving external API is one recipe doc; consolidation fixes the degradation gap independently of any index. Cons: integration docs to maintain; a soft dependency on external release cadence. Effort: S–M (Phase 7 consolidation + Phase 8 recipes).

**Option C — Build or embed Writ-owned retrieval (index, embeddings, or bundled brain).**
Pros: controlled experience. Cons: violates zero-infrastructure driver; competes with GBrain and native memory instead of riding them; permanent maintenance load. Effort: L–XL.

## Decision

**Option B.** Three-part policy:

1. **Markdown in git is the canonical system of record.** Specs, ADRs, knowledge entries, drift logs — all remain plain text, all remain the only authoritative copy. Unchanged from ADR-005.
2. **External memory layers are welcome consumers, never owners.** Phase 8 ships a GBrain compatibility recipe (register `.writ/` via `gbrain sources add`, map knowledge/specs/ADRs to page types, brain-first retrieval guidance when a brain is detected, graceful removal when absent) and per-adapter guidance on native memory (session preferences and trivia belong in native memory; negotiated decisions, conventions, and lessons belong in the ledger, which feeds the rest). Round-trip test: removing any index loses zero canonical data.
3. **Writ owns consolidation, not retrieval.** Phase 7 adds a consolidation pass over the ledger — merge duplicates, surface contradictions, prune stale entries; merge, never append. Markdown in, markdown out, reviewable in a PR. This is the maintenance loop the substrate was missing, and it improves every downstream index for free.

`mission.md` language updates from "not a persistent-database knowledge layer" to "not a memory database or retrieval engine — external indexes are welcome consumers of the markdown substrate."

## Consequences

**Positive:** Writ gets best-in-class retrieval (GBrain) and native-memory coexistence without owning a line of retrieval infrastructure; the ledger stops degrading; ADR-005's guarantees survive intact; the integration story becomes a differentiator ("bring your own brain").

**Negative:** Recipe docs track external APIs that move fast (GBrain ships weekly) — accepted because the blast radius is one doc, not a dependency. Two-place guidance (native memory vs. ledger) adds a judgment call users must learn.

**Review trigger:** If the GBrain recipe requires more than doc-level maintenance for two consecutive Writ releases, demote it from shipped recipe to community-maintained example.
