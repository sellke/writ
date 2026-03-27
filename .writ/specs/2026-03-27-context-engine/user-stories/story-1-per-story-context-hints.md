# Story 1: Per-Story Context Hints

> **Status:** Completed ✅ (2026-03-27)
> **Priority:** High
> **Dependencies:** None

## User Story

**As a** Writ user creating a specification
**I want** each user story to automatically include context hints that index into the full spec
**So that** pipeline agents receive targeted, relevant context instead of generic spec summaries

## Acceptance Criteria

- [x] Given a spec with error maps and business rules, when user-story-generator creates a story file, then the file includes a "## Context for Agents" section with references to relevant error map rows, shadow paths, business rules, and experience elements
- [x] Given context hints that reference specific spec content, when the orchestrator reads the hints, then it can fetch the referenced content from spec.md and technical-spec.md (format documented, orchestrator implementation in Story 4)
- [x] Given a story with context hints, when /implement-story runs, then agents receive the targeted content (format established, routing implementation in Story 4)
- [x] Given missing or malformed context hints, when the orchestrator parses them, then it logs a warning and skips gracefully without blocking the pipeline (edge cases documented)
- [x] Given the context hint format documentation, when a developer reads it, then they understand the syntax and can manually add hints if needed

## Implementation Tasks

- [x] 1.1 Create `.writ/docs/context-hint-format.md` documenting the context hint syntax and examples
- [x] 1.2 Update `agents/user-story-generator.md` prompt template to generate "## Context for Agents" section
- [x] 1.3 Update `commands/create-spec.md` Step 2.6 to pass full spec content (spec.md + technical-spec.md) to user-story-generator agents
- [x] 1.4 Document validation strategy for hint generation (golden file comparison, dogfooding)
- [x] 1.5 Document parsing rules and edge cases in context-hint-format.md (orchestrator implementation in Story 4)
- [x] 1.6 Verify context hints are present in generated story files (dogfood on this spec itself)
- [x] 1.7 Verify all acceptance criteria are met and validation complete

## Notes

**Technical considerations:**

- Context hints are indexes, not content duplication — story file points to "error map row: Create session" and orchestrator fetches that row from technical-spec.md
- Hint format should be parseable by orchestrator (simple markdown structure, not complex YAML)
- user-story-generator needs access to full spec.md and technical-spec.md to know what to reference
- Graceful degradation: if a hint references nonexistent content, log and skip (don't fail the pipeline)

**Integration points:**

- `/create-spec` Step 2.6 (parallel story generation) passes additional context
- `/implement-story` Step 2 (Load Context) will parse these hints in Story 4
- This story establishes the format; Story 4 implements the orchestrator logic

**Risks:**

- Hints could be inaccurate (point to wrong rows) — mitigation: generate during /create-spec when spec is fresh
- Hints could reference nonexistent content — mitigation: orchestrator validates and skips gracefully

## Definition of Done

- [x] Context hint format documented in `.writ/docs/context-hint-format.md`
- [x] user-story-generator agent updated to generate hints
- [x] create-spec command passes full spec content to generator
- [x] Validation strategy documented (golden file + edge cases)
- [x] Dogfood validation: this spec's stories include context hints
- [x] Code reviewed (PASS with Medium drift logged)
- [x] Documentation updated (CHANGELOG, AGENTS.md)

## Context for Agents

- **Error map rows:** `technical-spec.md` — target the error-map table for this spec when present; if absent, reference `spec.md` → `## 🎯 Experience Design` → `### Error Experience` (orchestrator warning/skip behavior for bad hints)
- **Shadow paths:** `spec.md` → `## 🎯 Experience Design` → `### Happy Path Flow` (steps 1–3: `/create-spec` → hint generation → `/implement-story` consumption)
- **Business rules:** `spec.md` → `## 📋 Business Rules` → `### Context Hint Requirements`; `### Spec Modification Rules` (full `spec.md` stable; hints must reference real content)
- **Experience:** `spec.md` → `## 🎯 Experience Design` → `### Entry Point`; `### Moment of Truth` (silent improvement; validation via agent behavior)
- **Format reference:** `spec.md` → `## Implementation Approach` → `### Technical Decisions` → **Context hint format** (example markdown block)
- **Files in scope:** `spec.md` → `## Implementation Approach` → `### Files in Scope` — `agents/user-story-generator.md`, `commands/create-spec.md`, `.writ/docs/context-hint-format.md`

---

## What Was Built

> Completed: 2026-03-27 at Gate 5

### Files Created

- **`.writ/docs/context-hint-format.md`** (470 lines) — Comprehensive format specification for context hints
  - Overview and core principles (hints are indexes, not duplication)
  - Format structure with four hint categories: error map rows, shadow paths, business rules, experience
  - Generation guidelines for user-story-generator agents
  - Parsing guide for orchestrators with error handling
  - Complete examples (minimal, rich, extended reference format)
  - Validation strategy (golden file comparison, edge case documentation)

### Files Modified

- **`agents/user-story-generator.md`** — Added context hint generation capability
  - New parameters: `spec_content`, `technical_spec_content`
  - Prompt template includes "## Context for Agents" generation instructions
  - Format guidance with selection criteria and quality rules
  - Graceful degradation handling when technical-spec.md doesn't exist

- **`commands/create-spec.md`** — Updated Step 2.6 to pass full spec content
  - Passes full `spec.md` content to user-story-generator agents
  - Passes `technical-spec.md` content (or empty string if parallel generation)
  - Timing note addresses parallel generation risk
  - Updated expected story structure to include context hints section

- **`CHANGELOG.md`** — Added entry for context hints feature

- **`AGENTS.md`** — Updated user-story-generator description to mention context hint generation

### Implementation Decisions

- **Format choice:** Markdown-based with bracketed lists for parseability (not YAML for simplicity)
- **Index not duplication:** Hints reference content locations, orchestrator fetches actual content
- **Graceful degradation:** Missing/malformed hints log warnings and skip, don't block pipeline
- **Phased delivery:** Story 1 establishes format and generation; Story 4 implements orchestrator parsing
- **Validation approach:** Golden file comparison and dogfooding (appropriate for markdown system with no test suite)
- **Technical-spec timing:** Handle parallel generation by passing empty string if not yet available, scope hints to spec.md only

### Validation Results

- **Generation validation:** Agent template updated correctly, all 5 stories in this spec have context hints ✅
- **Format validation:** 470-line specification is parseable, comprehensive, with clear examples ✅
- **Dogfooding:** All stories demonstrate format works in practice ✅
- **Boundary compliance:** All changes within owned files (agents/user-story-generator.md, commands/create-spec.md, .writ/docs/context-hint-format.md) ✅
- **Coverage:** 100% — All acceptance criteria have validation approaches ✅

### Review Notes

- **Result:** PASS (with Medium drift logged)
- **Drift:** Story 1 scope correctly limited to format + generation + documentation; AC2-AC4 runtime verification deferred to Story 4 as documented
- **Quality:** Comprehensive documentation, clean implementation, format works as designed
- **Security:** Clean (markdown-only changes)
- **Integration:** Additive, no breaking changes
- **Iterations:** Zero — implementation passed review on first attempt

### Pipeline Summary

- **Gate 0 (Architecture Check):** CAUTION — warnings about AC overlap with Story 4, technical-spec timing, and test strategy (all addressed in implementation)
- **Gate 1 (Coding):** Complete — format docs + agent template + command updates
- **Gate 2 (Lint):** PASS — no linter errors
- **Gate 3 (Review):** PASS — boundary compliant, quality good, medium drift logged
- **Gate 3.5 (Drift):** Logged DEV-001 (orchestrator ACs) and DEV-002 (test approach) to drift-log.md
- **Gate 4 (Testing):** PASS — 100% validation coverage via documented strategy
- **Gate 5 (Documentation):** Complete — CHANGELOG, AGENTS.md updated
