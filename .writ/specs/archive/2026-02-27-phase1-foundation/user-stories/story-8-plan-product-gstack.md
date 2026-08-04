# Story 8: /plan-product gstack Enhancement

> **Status:** Completed ✅
> **Priority:** Medium
> **Dependencies:** None (research-driven, independent of pipeline features)
> **Completed:** 2026-03-14

## User Story

**As a** solo developer using Writ to plan products
**I want to** have `/plan-product` challenge my premises, push for the best version of my idea, and lead with opinionated recommendations
**So that** planning conversations produce better products by elevating the quality of discovery, not just the thoroughness of information gathering

## Context

Research analysis of gstack (`.writ/research/2026-03-14-gstack-analysis-research.md`) identified that Writ's discovery conversations were thorough but informationally neutral — they gathered requirements without challenging whether the requirements were *right*. This story implements Option B (Comprehensive Adoption) from the research, applying six concrete techniques from gstack's `/plan-ceo-review` pattern.

Decision record: DEC-006 (Opinionated & Aspirational Posture)

## Acceptance Criteria

- [x] **AC1:** Given I invoke `/plan-product`, when the discovery phase begins, then I am prompted with a Planning Posture selection (EXPANSION / HOLD / REDUCTION) before any discovery questions are asked; the selected posture visibly shapes the conversation's lens throughout.
- [x] **AC2:** Given the discovery phase begins, when the first substantive question is asked, then it is a premise challenge — questioning whether the framing is correct ("Is this the right problem to solve?") — not an information-gathering question.
- [x] **AC3:** Given EXPANSION posture is selected, when the discovery conversation is underway, then Dream State Mapping (`CURRENT STATE → THIS PLAN → 12-MONTH IDEAL`) is constructed with the user, and delight opportunities are actively explored.
- [x] **AC4:** Given any posture is selected, when the command makes recommendations, then they lead with "I recommend X because Y" format — not neutral menus of options — throughout the discovery and contract phases.
- [x] **AC5:** Given the product contract is presented, when it includes user-facing features of Moderate or Complex scope, then it contains a mandatory Failure Surface Analysis table (User Flow / What Can Break / User Impact / Mitigation) and a mandatory ASCII architecture diagram.

## Implementation Tasks

- [x] 8.1 Conduct gstack research — read all 8 gstack SKILL.md files, ARCHITECTURE.md, CLAUDE.md; compare against Writ's planning commands; produce research document at `.writ/research/2026-03-14-gstack-analysis-research.md`.
- [x] 8.2 Write DEC-006 decision record — document the decision to adopt an opinionated, aspirational posture; record alternatives considered (Option A: Focused Uplift, Option B: Comprehensive Adoption, Option C: Philosophy-First); append to `.writ/product/decisions.md`.
- [x] 8.3 Update `commands/plan-product.md` — add Planning Posture Selection step (1.1c), mandatory Premise Challenge as opening move, Dream State Mapping section, posture-specific discovery behaviors, opinionated recommendation format, Failure Surface Analysis table in contract template, mandatory architecture diagrams for Moderate/Complex.
- [x] 8.4 Update product documents — update `.writ/product/mission-lite.md` (add opinionated guidance differentiator, design principle 6), `.writ/product/mission.md` (add last-updated date), `.writ/product/roadmap.md` (add `/plan-product` enhancement, new Phase 2 items from research, design principle 6).
- [x] 8.5 Verify coherence — confirm `plan-product.md` changes are internally consistent (posture selection flows through discovery, contract, and recommendations); confirm product documents align; confirm roadmap accurately reflects new Phase 2 items from research (retro, ship, review, error mapping, browser QA).

## Notes

**This story is retroactive documentation.** The work was completed on 2026-03-14 as part of the gstack research and roadmap update cycle. The story was added to the spec during a 2026-03-14 spec edit to maintain traceability.

**Research-driven, not pipeline-driven.** Unlike Stories 1-6 which produce command files and agent extensions, this story's primary artifacts are the research document, decision record, and modifications to an existing command file. No new commands or agents were created.

**Cross-cutting impact.** The opinionated posture (Design Principle 6) applies beyond `/plan-product` — it's a philosophical shift that should influence all Writ commands over time. This story captures the explicit `/plan-product` changes; the broader adoption is an ongoing concern.

**Integration points:**
- `commands/plan-product.md` — primary command file modified
- `.writ/product/` — mission, roadmap, decisions updated
- `.writ/research/` — research document produced
- Phase 2 roadmap items — `/retro`, `/ship`, `/review`, error mapping, browser QA added as future work

## Definition of Done

- [x] All tasks completed
- [x] All acceptance criteria met
- [x] Research document produced and complete
- [x] Decision record (DEC-006) documented
- [x] `commands/plan-product.md` updated with all six gstack-inspired techniques
- [x] Product documents (mission, mission-lite, roadmap) updated
