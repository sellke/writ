# Story 3: create-adr.md Refinement

> **Status:** Not Started
> **Priority:** High
> **Dependencies:** None

## User Story

**As a** Writ maintainer
**I want to** refine create-adr.md to A-grade quality
**So that** every line teaches something non-obvious, sets a quality bar, or prevents a specific mistake — with the decision analysis flow preserved and the command decoupled from auto-executing research

## Acceptance Criteria

1. **Given** the refined create-adr.md, **when** an AI agent executes the command, **then** the core process (Steps 0–4) remains fully executable: prerequisite research check → context analysis → scope/criteria → alternatives evaluation → ADR documentation.

2. **Given** the refined file, **when** checking Step 0, **then** it is a lightweight prerequisite gate (~10 lines): check `.writ/research/` for existing research; if none found, recommend running `/research` first rather than auto-executing it. No auto-execute scaffolding or embedded research workflow.

3. **Given** the refined file, **when** counting lines, **then** the total is within ~200 ±10% (180–220 lines), down from 499.

4. **Given** the refined file, **when** checking for removed sections, **then** the following are cut entirely: ADR document template (lines 228–357, ~130 lines), Best Practices (lines 368–401), Common Pitfalls (lines 403–433), JSON todo_write block (lines 84–122).

5. **Given** the refined file, **when** reviewing preserved content, **then** the following remain intact: "When to Use" triggers (prevent trivial ADRs), ADR numbering convention (sequential NNNN), status lifecycle (Proposed → Accepted → Deprecated → Superseded), Step 3 evaluation framework categories, Step 4 preparation steps (date via `npx @devobsessed/writ date`, numbering). Step 4 ADR content is expressed as principles (what sections an excellent ADR needs and quality bar for each), not a template.

## Implementation Tasks

1. **Read and map the current file** — Open `commands/create-adr.md`, verify line numbers for sections to cut/compress. Confirm Step 0 (lines 27–73), todo block (84–122), ADR template (228–357), Best Practices (368–401), Common Pitfalls (403–433). Note the decision analysis flow structure.

2. **Replace Step 0 with prerequisite gate** — Replace the auto-execute pattern (~47 lines) with ~10 lines: use `Grep`/`Glob` to check `.writ/research/` for relevant research; if none found, recommend "Run `/research` first to document alternatives, then return to create the ADR." Remove all auto-execute messaging, research workflow embedding, and "IMMEDIATELY read and execute research.md" instructions. This decouples the two commands.

3. **Cut the ADR document template** — Remove the 155-line template (lines 228–357). Replace with principles: what sections an excellent ADR needs (Context/Problem, Decision Drivers, Considered Options with pros/cons/effort/risk, Decision Outcome with rationale, Consequences positive/negative/mitigation, References) and quality bar for each. Trust the AI to structure; the principles encode judgment.

4. **Cut Best Practices and Common Pitfalls** — Remove Best Practices (lines 368–401) and Common Pitfalls (lines 403–433). Generic ADR advice the AI already knows. Preserve any non-obvious items by inlining them into the relevant steps (e.g., "include status quo option" in Step 3).

5. **Cut the JSON todo_write block** — Remove lines 84–122. The AI knows how to track todos; the block adds no unique guidance.

6. **Compress Steps 1–4** — State what each step accomplishes; compress substeps and deliverable lists. Step 3: keep the evaluation framework categories (technical feasibility, performance, security, effort, maintenance, risk); compress surrounding prose. Step 4: keep preparation steps (date, numbering); state ADR content as principles per task 3. Apply litmus test to every remaining line.

7. **Verification** — Confirm line count within target (~200 ±10%), run a mental execution to ensure no capability lost. Verify prerequisite gate recommends `/research` without auto-executing. Verify ADR numbering, status lifecycle, and "When to Use" triggers are preserved.

## Notes

**Technical considerations:**
- The auto-execute → prerequisite gate change is the most delicate transformation. The gate must be explicit: check for research, if absent recommend `/research` and pause — do not read or execute research.md. This decouples create-adr from research's full workflow.
- ADR principles must capture what makes an excellent ADR (driving forces, alternatives with effort/risk, honest consequences, mitigation) — the AI might produce shallow ADRs without this bar.
- "When to Use" triggers prevent trivial ADRs; preserve them verbatim.

**Risks:**
- Over-compression could remove nuance from the evaluation framework. The six categories (technical feasibility, performance, security, effort, maintenance, risk) encode judgment — keep them explicit.
- Prerequisite gate too terse could leave the agent unsure when to proceed vs pause. Make the branching logic clear: research found → continue; research absent → recommend `/research`, do not proceed.

**Watch for:**
- Step 1–4 flow must remain coherent; don't lose the "load research if found" behavior when research exists.
- ADR numbering (sequential NNNN) and status lifecycle are conventions — preserve them.
- `npx @devobsessed/writ date` for document date is a Writ-specific detail — keep it.

## Definition of Done

- [ ] All tasks completed
- [ ] All acceptance criteria met
- [ ] Line count within target range (~200 ±10%)
- [ ] No functional capability lost
- [ ] Step 0 is prerequisite gate only (no auto-execute)
- [ ] ADR content expressed as principles, not template
