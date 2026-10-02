# Domain modules for non-software product work

> **Type:** Feature
> **Priority:** Normal
> **Effort:** Large
> **Created:** 2026-10-01
> **spec_ref:** _(set automatically when promoted via `/create-spec --from-issue`)_

## TL;DR

Add optional Writ modules so the same contract-first method can produce non-software artifacts — starting with a curriculum builder and a presentation builder — without thickening the software path.

## Current State

- Writ's mission owns the durable contracts of software development: specs, stories, code, tests, releases.
- Commands and agents assume a software product (`/plan-product`, the implement pipeline, review and test agents).
- Non-software product work — lessons, pitch content, slides, playbooks, white papers, one-pagers, sites — has no module, templates, or artifact lifecycle inside `.writ/`.
- The parked business-process pipeline is a different idea: operational workflows (hiring, procurement), deferred until a concrete first process. It does not cover content products.

## Expected Outcome

- Writ can load domain modules for non-software product uses. The software pipeline stays the default and does not grow to absorb them.
- A **curriculum-builder** module produces tutorial, lesson, and pitch content under the same contract-first flow (agree the artifact, then build it).
- A **presentation-builder** module produces supporting vehicles: slides, playbooks, white papers, one-pagers, and websites.
- Each module declares its artifact types, templates, and done-criteria. Shared primitives (issue capture, specs, status, knowledge) stay common; domain-specific commands and agents stay in the module.

## Relevant Files

- `.writ/product/mission.md` — identity currently scopes Writ to software-development contracts
- `.writ/product/roadmap.md` — parking lot holds the adjacent business-process pipeline, deferred for lack of a concrete anchor
- `commands/plan-product.md` — product-planning entry assumes a software product and would be the seam a module forks from

## Related Issues

- [2026-05-03-business-process-writ-pipeline](2026-05-03-business-process-writ-pipeline.md) — sister pipeline for operational business processes, parked; related widening of scope, different artifact and a different trigger

## Notes

- **Open question — mechanism:** one pluggable module slot with two first modules, or two standalone builders. The request says "modules … such as," so a slot plus these two examples is the working read.
- **Open question — distribution:** optional packs inside `@sellke/writ`, or separate installs. Either way the software install should not pull curriculum or presentation commands by default.
- **Concrete anchors already named:** curriculum (tutorial / lesson / pitch) and presentation vehicles (slides, playbooks, white papers, one-pagers, websites). That is enough to spec one module first rather than a universal content framework.
- **Identity change:** shipping this revises "what Writ is" in the mission. It should not be folded into Phase 12 (behavioral verification).
