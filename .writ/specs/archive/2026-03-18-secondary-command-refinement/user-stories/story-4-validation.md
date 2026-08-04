# Story 4: Validation

> **Status:** Not Started
> **Priority:** High
> **Dependencies:** Stories 1, 2, 3

## User Story

**As a** Writ maintainer
**I want to** validate all three refined commands against the litmus test and cross-reference integrity
**So that** the refinement maintains the same quality bar as the core A-grade refinement

## Acceptance Criteria

1. **Given** the three refined files (create-issue.md, design.md, prototype.md), **when** applying the litmus test to every section, **then** each line either teaches something non-obvious, sets a quality bar the AI wouldn't reach alone, or prevents a specific mistake — with no filler.

2. **Given** the three refined files, **when** counting total lines, **then** the combined total is within ~550 ±10% (495–605 lines), with create-issue ~140, design ~200, prototype ~210.

3. **Given** the refined files, **when** checking cross-references, **then** prototype references `agents/coding-agent.md`, design references `agents/visual-qa-agent.md`, and design's Gate 1 → coding-agent pipeline integration remain intact and resolvable.

4. **Given** the refined files, **when** comparing capabilities to the pre-refinement versions, **then** zero functional capability is lost — every workflow step, mode, output format, and decision point from the originals is still executable from the refined text.

5. **Given** the refined files, **when** comparing voice and density to already-refined commands (assess-spec, edit-spec, plan-product, create-spec), **then** the tone is consistent (direct, principle-driven, no filler) and the information density matches — no section feels bloated or sparse relative to the reference set.

## Implementation Tasks

1. **Line count audit** — Count lines in each refined file. Record: create-issue (target 126–154), design (target 180–220), prototype (target 189–231). Sum total (target 495–605). Flag any file outside its range.

2. **Section-by-section litmus test on each file** — Walk every section of create-issue.md, design.md, and prototype.md. For each line, ask: (1) teaches non-obvious? (2) sets quality bar? (3) prevents mistake? Mark any line that fails all three. Pay special attention: create-issue (question triggers, skip-if-obvious); design (Mode A wireframe conventions, Mode C/D, pipeline integration); prototype (scope escalation flags, pipeline diagram, experience-gaps). Document failures in validation report.

3. **Cross-reference check** — Grep for `coding-agent`, `visual-qa-agent`, `Gate 1`. Verify: prototype.md contains `agents/coding-agent.md`; design.md contains `agents/visual-qa-agent.md` and Gate 1 → coding agent pipeline text. Confirm paths resolve to existing files. Document any breakage.

4. **Capability comparison** — List all capabilities from pre-refinement versions (workflow steps, modes, outputs, decision points). For each, confirm the refined text still enables execution. Produce a before/after capability matrix. Flag any gap.

5. **Voice and density comparison** — Read assess-spec.md, edit-spec.md, plan-product.md, create-spec.md. Extract patterns: sentence length, use of tables vs prose, principle vs prescription ratio. Compare refined create-issue, design, prototype against these. Note any section that feels off — bloated, sparse, or tonally inconsistent. Document findings.

6. **Document validation report** — Consolidate findings from tasks 1–5 into a validation report. Include: line counts (actual vs target), litmus test failures by file, cross-reference status, capability matrix, voice/density notes. Store in `.writ/specs/2026-03-18-secondary-command-refinement/` or append to spec. Mark pass/fail per file and overall.

## Notes

**Common litmus test failures:**
- Restating the obvious ("The AI should read the file")
- Redundant process summaries that duplicate step headers
- Overly prescriptive templates where principles would suffice
- Generic advice ("Be thorough") without a specific bar or mistake prevented
- Scaffolding text that adds structure but no guidance

**Cross-reference patterns to check:**
- `> **Agent:**` blocks — prototype and implement-story use this format
- Inline references like "See: `agents/visual-qa-agent.md`"
- Gate 1 / Gate 4.5 pipeline descriptions in design.md
- Paths must be relative from commands/ to agents/

**Voice/density comparison:**
- Refined core commands use: short paragraphs (2–4 lines), tables for structured data, bullets for lists, no "you should" filler
- Principle-first over step-by-step prescription where the AI can infer
- Consistent section headers (Overview, Invocation, Command Process, Notes)
- If a refined secondary command reads "chatty" or "manual-like" next to assess-spec, it needs tightening

## Definition of Done

- [ ] All tasks completed
- [ ] All acceptance criteria met
- [ ] All three files confirmed at A grade
- [ ] Validation report documented
