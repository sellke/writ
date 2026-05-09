# Business-Process Writ — Sister Pipeline

> **Type:** Feature
> **Priority:** High
> **Effort:** Large
> **Created:** 2026-05-03
> **spec_ref:** _(set automatically when promoted via `/create-spec --from-issue`)_

## TL;DR

A sister pipeline to the existing dev-focused Writ that applies the same methodical, contract-first, AI-assisted workflow to **business processes** (not just software development), with shared visibility through the Kanban view.

## Current State

- Writ today is exclusively scoped to software-development workflows: specs, stories, code, tests, releases.
- Many of the same primitives — capture-an-issue, define-a-contract, decompose-into-units-of-work, track-status, hand-off-between-agents — apply equally well to business processes (hiring loops, procurement, contract review, quarterly planning, vendor onboarding, etc.).
- Right now, business work has no home in the `.writ/` workspace. It either lives in scattered tools (docs, trackers, email) or doesn't get the same rigor that dev work gets.
- The forthcoming Kanban view (see `.writ/specs/2026-05-03-*-kanban*` once promoted) is being scoped to current Writ data (issues + specs), but the renderer should be able to ingest additional source types so a business-process pipeline can plug in later without a redesign.

## Expected Outcome

- A second Writ pipeline exists alongside the dev pipeline, sharing core primitives (issue capture, contract-first specs, multi-agent workflows, status tracking) but with templates, commands, and agents tuned for business processes.
- Both pipelines feed the **same Kanban view** so a single board surfaces all in-flight work — dev *and* business — across the project.
- A clear taxonomy of what a "business process work item" looks like (likely analogous to issues+specs+stories, but the unit names and lifecycle may differ).
- Distribution model unchanged: markdown command files, optional CLI helpers, platform-agnostic.

## Relevant Files

- `commands/create-issue.md` — closest existing capture flow; business-process equivalent likely mirrors this
- `commands/create-spec.md` — contract-first pattern that should generalize
- `agents/` — current agent set is dev-shaped (architect, coder, tester, reviewer); business pipeline needs its own agent definitions
- `system-instructions.md` — defines Writ's identity; needs to accommodate (or be parallel to) a business-process identity
- `.writ/specs/[future-kanban-spec]/` — Kanban renderer must be source-type-extensible to support this pipeline later

## Notes

- **Open question — scope of "business process":** Hiring? Procurement? Contract review? Quarterly planning? Sales pipeline? The MVP needs a concrete first process to anchor the design; trying to be universal up front will produce something that fits nothing.
- **Open question — same product or sister product:** Does this ship as part of `@sellke/writ` (one tool, two pipelines) or as a parallel package? Affects naming, install flow, and command prefixes (e.g., `/biz-create-issue` vs. namespacing).
- **Open question — work-item shape:** Business processes often have approval gates, stakeholder sign-offs, and external dependencies that don't map cleanly to "stories with implementation tasks." May need a different decomposition primitive.
- **Kanban dependency:** This issue is **coupled to the Kanban spec** by design. Decision recorded 2026-05-03: Kanban v1 ships scoped to current Writ data (issues+specs), with the renderer architected to accept additional source types so this pipeline can integrate without a renderer redesign.
- **Likely first concrete artifact:** an ADR (`/create-adr`) capturing the "two pipelines, one workspace" decision and the work-item taxonomy before any commands are written.
