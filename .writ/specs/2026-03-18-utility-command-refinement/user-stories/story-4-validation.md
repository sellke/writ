# Story 4: Validation

> **Status:** Not Started
> **Priority:** High
> **Dependencies:** Stories 1, 2, 3

## User Story

**As a** Writ maintainer validating refinement quality
**I want to** validate all three refined commands against the litmus test, cross-reference integrity, capability preservation, and voice/density consistency with already-refined commands
**So that** the refinement maintains the same A-grade quality bar as the core and secondary refinement specs

## Acceptance Criteria

1. **Given** the three refined files (initialize.md, research.md, create-adr.md), **when** applying the litmus test to every section, **then** each line either teaches something non-obvious, sets a quality bar the AI wouldn't reach alone, or prevents a specific mistake — with no filler.

2. **Given** the three refined files, **when** counting total lines, **then** the combined total is within ~530 ±10% (477–583 lines), with initialize ~170 (153–187), research ~160 (144–176), create-adr ~200 (180–220).

3. **Given** the refined files, **when** checking cross-references, **then** create-adr references `commands/research.md` as prerequisite gate; initialize recommends `/plan-product` as next step; create-adr references `.writ/decision-records/` and `.writ/research/` — all paths resolvable and intact.

4. **Given** the refined files, **when** comparing capabilities to the pre-refinement versions, **then** zero functional capability is lost — every workflow step, mode, output format, decision point, and quality gate from the originals is still executable from the refined text.

5. **Given** the refined files, **when** comparing voice and density to already-refined commands (assess-spec.md, edit-spec.md as benchmarks), **then** the tone is consistent (direct, principle-driven, no filler) and the information density matches — no section feels bloated or sparse relative to the reference set.

## Implementation Tasks

1. **Line count audit** — Count lines in each refined file. Record: initialize (target 153–187), research (target 144–176), create-adr (target 180–220). Sum total (target 477–583). Flag any file outside its range.

2. **Section-by-section litmus test on each file** — Walk every section of initialize.md, research.md, and create-adr.md. For each line, ask: (1) teaches non-obvious? (2) sets quality bar? (3) prevents mistake? Mark any line that fails all three. Pay special attention: initialize (greenfield/brownfield detection heuristic, gap analysis, plan-product recommendation); research (4-phase structure, Exa vs non-Exa per-phase strategies, output path convention); create-adr (prerequisite gate for research, ADR numbering, status lifecycle, "When to Use" triggers). Document failures in validation report.

3. **Cross-reference check** — Grep for `research.md`, `plan-product`, `.writ/decision-records/`, `.writ/research/`. Verify: create-adr.md contains prerequisite gate referencing `commands/research.md`; initialize.md recommends `/plan-product` as next step; create-adr references `.writ/decision-records/` and `.writ/research/` for output locations. Confirm paths resolve to existing conventions. Document any breakage.

4. **Capability comparison** — List all capabilities from pre-refinement versions (workflow steps, phases, modes, outputs, decision points, quality gates). For each, confirm the refined text still enables execution. Produce a before/after capability matrix. Flag any gap. Key capabilities: initialize (greenfield vs brownfield detection, two-workflow structure, gap analysis categories, tech-stack/code-style docs); research (4-phase structure, Exa tips, output path + date); create-adr (prerequisite check, decision analysis flow, ADR numbering, status lifecycle).

5. **Voice and density comparison** — Read assess-spec.md (203 lines), edit-spec.md (118 lines). Extract patterns: sentence length, use of tables vs prose, principle vs prescription ratio, section structure. Compare refined initialize, research, create-adr against these. Note any section that feels off — bloated, sparse, or tonally inconsistent. Document findings.

6. **Document validation report** — Consolidate findings from tasks 1–5 into a validation report. Include: line counts (actual vs target), litmus test failures by file, cross-reference status, capability matrix, voice/density notes. Store in `.writ/specs/2026-03-18-utility-command-refinement/validation-report.md`. Mark pass/fail per file and overall.

## Notes

**Common litmus test failures:**
- Restating the obvious ("The AI should read the file")
- Redundant process summaries that duplicate step headers
- Overly prescriptive templates where principles would suffice
- Generic advice ("Be thorough") without a specific bar or mistake prevented
- Scaffolding text that adds structure but no guidance
- Todo examples or JSON blocks — the AI knows how to track todos

**Cross-reference patterns to check:**
- create-adr prerequisite gate: "Check for existing research in `.writ/research/`" → "recommend running `/research` first"
- initialize next step: single instance recommending `/plan-product`
- Path references: `commands/research.md`, `.writ/decision-records/`, `.writ/research/`
- Paths must be relative and resolvable from commands/ context

**Voice/density comparison:**
- Refined core commands use: short paragraphs (2–4 lines), tables for structured data, bullets for lists, no "you should" filler
- Principle-first over step-by-step prescription where the AI can infer
- Consistent section headers (Overview, Invocation, Command Process, Notes)
- If a refined utility command reads "chatty" or "manual-like" next to assess-spec or edit-spec, it needs tightening

## Definition of Done

- [ ] All tasks completed
- [ ] All acceptance criteria met
- [ ] All three files confirmed at A grade
- [ ] Validation report documented at `.writ/specs/2026-03-18-utility-command-refinement/validation-report.md`
