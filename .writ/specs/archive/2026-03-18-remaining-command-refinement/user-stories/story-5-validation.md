# Story 5: Validation

> **Status:** Not Started
> **Priority:** High
> **Dependencies:** Stories 1, 2, 3, 4

## User Story

**As a** Writ maintainer validating refinement quality
**I want to** validate all four refined commands against the litmus test, cross-reference integrity, capability preservation, and voice/density consistency with already-refined commands
**So that** the refinement maintains the same A-grade quality bar as the core, secondary, and utility refinement specs

## Acceptance Criteria

1. **Given** the four refined files (new-command.md, refactor.md, review.md, retro.md), **when** applying the litmus test to every section, **then** each line either teaches something non-obvious, sets a quality bar the AI wouldn't reach alone, or prevents a specific mistake — with no filler.

2. **Given** the four refined files, **when** counting total lines, **then** the combined total is within ~840 ±10% (756–924 lines), with new-command ~200 (180–220), refactor ~220 (198–242), review ~200 (180–220), retro ~220 (198–242).

3. **Given** the refined files, **when** checking cross-references, **then** review references `.writ/state/` for ship integration; refactor references `/create-adr` for major refactors; retro references `.writ/retros/`, `.writ/specs/`, and `.writ/refresh-log.md` — all paths resolvable and intact.

4. **Given** the refined files, **when** comparing capabilities to the pre-refinement versions, **then** zero functional capability is lost — every workflow step, mode, output format, decision point, and quality gate from the originals is still executable from the refined text.

5. **Given** the refined files, **when** comparing voice and density to already-refined commands (assess-spec.md, edit-spec.md as benchmarks), **then** the tone is consistent (direct, principle-driven, no filler) and the information density matches — no section feels bloated or sparse relative to the reference set.

## Implementation Tasks

1. **Line count audit** — Count lines in each refined file. Record: new-command (target 180–220), refactor (target 198–242), review (target 180–220), retro (target 198–242). Sum total (target 756–924). Flag any file outside its range.

2. **Section-by-section litmus test on each file** — Walk every section of all four files. For each line, ask: (1) teaches non-obvious? (2) sets quality bar? (3) prevents mistake? Mark any line that fails all three. Pay special attention: new-command (contract-first discovery, critical analysis, pushback phrasing); refactor (safety guarantees, baseline verification, mode detection targets); review (5 techniques, severity classification, judgment calls); retro (session detection heuristics, pattern guidance, Ship of the Week selection). Document failures in validation report.

3. **Cross-reference check** — Verify: review.md references `.writ/state/review-[branch].md` for ship integration; refactor.md references `/create-adr` for architectural refactors; retro.md references `.writ/retros/` for snapshots and trends, `.writ/specs/` for spec context, `.writ/refresh-log.md` for command refresh data. Confirm paths resolve to existing conventions. Document any breakage.

4. **Capability comparison** — List all capabilities from pre-refinement versions (modes, techniques, workflows, outputs, decision points, quality gates). For each, confirm the refined text still enables execution. Produce a before/after capability matrix per file. Key capabilities: new-command (contract-first discovery, all 5 command categories, echo check, Phase 2 creation, validation); refactor (all 8 modes, baseline verification, analysis report, refactoring plan, per-change verification, rollback, ADR creation); review (all 5 techniques, spec comparison, ship integration, large-diff handling); retro (all 5 invocation modes, session detection, streaks, Writ context, Ship of the Week, patterns, tweetable, compare mode, spec-scoping, snapshot persistence, trends).

5. **Voice and density comparison** — Read assess-spec.md and edit-spec.md as benchmarks. Extract patterns: sentence length, table vs prose ratio, principle vs prescription, section structure. Compare all four refined files. Note any section that feels off — bloated, sparse, or tonally inconsistent. Document findings.

6. **Document validation report** — Consolidate findings from tasks 1–5 into a validation report at `.writ/specs/2026-03-18-remaining-command-refinement/validation-report.md`. Include: line counts (actual vs target), litmus test failures by file, cross-reference status, capability matrix, voice/density notes. Mark pass/fail per file and overall.

## Notes

**Common litmus test failures:**
- Restating the obvious ("The AI should read the file")
- Redundant process summaries that duplicate step headers
- Overly prescriptive templates where principles would suffice
- Generic advice ("Be thorough") without a specific bar or mistake prevented
- Scaffolding text that adds structure but no guidance
- Bash scripts the AI knows how to write
- JSON schemas the AI knows how to structure
- Markdown templates the AI can compose from principles

**Cross-reference patterns to check:**
- review → ship: `.writ/state/review-[branch].md` file written by review, read by ship
- refactor → create-adr: auto-created ADR for significant architectural refactors
- retro → writ artifacts: `.writ/retros/`, `.writ/specs/`, `.writ/refresh-log.md`
- All paths must be relative and resolvable from the command's execution context

**Voice/density comparison:**
- Refined commands use: short paragraphs (2–4 lines), tables for structured data, bullets for lists, no "you should" filler
- Principle-first over step-by-step prescription where the AI can infer
- Consistent section headers (Overview, Invocation, Command Process, Notes/Integration)
- If a refined command reads "chatty" or "manual-like" next to assess-spec or edit-spec, it needs tightening

## Definition of Done

- [ ] All tasks completed
- [ ] All acceptance criteria met
- [ ] All four files confirmed at A grade
- [ ] Validation report documented at `.writ/specs/2026-03-18-remaining-command-refinement/validation-report.md`
