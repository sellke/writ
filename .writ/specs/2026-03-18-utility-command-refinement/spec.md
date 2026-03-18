# Utility Command Refinement Specification

> Created: 2026-03-18
> Status: Planning
> Contract Locked: ✅

## Contract Summary

**Deliverable:** Refine `/initialize`, `/research`, and `/create-adr` to A-grade quality using the same litmus test and simplification principles proven in the core and secondary refinement specs.

**Must Include:** Every line in every file must pass the litmus test — teaches something non-obvious, sets a quality bar the AI wouldn't reach alone, or prevents a specific mistake.

**Hardest Constraint:** `/create-adr` is the heaviest at 499 lines with a 155-line ADR template and an embedded auto-execute pattern for `/research` that needs to become a lightweight prerequisite gate.

## Design Philosophy

Identical to the core and secondary refinement specs. These commands are guidance for an AI, not programs to execute. The AI doesn't need exact markdown templates — it needs to know what matters, what's non-obvious, and where the pitfalls are.

**The litmus test for every line:**

1. Does this teach the AI something non-obvious? (Keep)
2. Does this set a quality bar the AI wouldn't reach alone? (Keep)
3. Does this prevent a specific mistake the AI would likely make? (Keep)
4. None of the above? (Cut)

**The simplification principle:** Replace templates with principles. Replace procedures with quality bars. Replace examples with one demonstration that shows judgment. Trust the AI to format, structure, and write files — tell it *what matters*, not *how to type*.

## Scope

### In Scope (3 files)

| File | Current Lines | Target | Grade Change |
|------|--------------|--------|-------------|
| commands/initialize.md | 398 | ~170 | B- → A |
| commands/research.md | 343 | ~160 | B → A |
| commands/create-adr.md | 499 | ~200 | B- → A |
| **Total** | **1,239** | **~530** | **~57% reduction** |

### Out of Scope

- Core commands (already refined: plan-product, create-spec, implement-spec, implement-story)
- Secondary commands (in-flight: create-issue, design, prototype)
- Recently refined commands (assess-spec, edit-spec)
- All other commands, agents, scripts, system instructions

## Detailed Requirements

### `initialize.md` (398 → ~170, B- → A)

**Keep intact:** Greenfield vs brownfield detection logic (the classification heuristic is non-obvious and prevents the AI from asking the user). The two-workflow structure is the organizing spine. Gap analysis concept for brownfield (analyze and document what exists). Plan-product recommendation as the next step (once, not three times).

**Cut entirely:**
- JSON todo_write blocks (2 blocks, ~60 lines combined) — the AI knows how to track todos.
- `tech-stack.md` template (30 lines) — state what it should contain and its purpose, not exact markdown headers.
- `code-style.md` template (22 lines) — same treatment.
- Duplicate next-steps guidance — appears three times (greenfield Phase 4, brownfield Phase 4, CRITICAL section at end). Keep one instance.
- "Tool Integration" section (13 lines) — same pattern cut from all commands.
- "Output Locations & File Structure" section (32 lines) — duplicates what the process steps already establish.
- "Todo Integration" with example JSON (33 lines) — the AI knows how to use todo_write.
- "File Creation Verification" checklist (7 lines) — obvious.

**Compress:**
- Phase descriptions for both workflows — state what each phase accomplishes and its quality bar, not step-by-step procedures. The AI can determine how to scan a codebase, create config files, and write documentation.
- Greenfield Phase 2 tech recommendations — state the categories (stack, architecture, dev tools, structure) as a principle, not a bullet list.
- Brownfield Phase 2 documentation generation — state what each doc should capture, not the exact section headers.
- Brownfield Phase 3 gap analysis — state the concept (identify gaps and technical debt), compress the category list.

### `research.md` (343 → ~160, B → A)

**Keep intact:** The 4-phase structure (define scope → initial discovery → deep dive → synthesis). This is a good research methodology and the AI benefits from the structured progression. Exa vs non-Exa search strategy distinction — genuinely non-obvious, prevents token blowout and bad search patterns. Per-phase Exa tips (use `/answer` for orientation, `highlights` for scanning, `text` with `max_characters` for reading, categories for targeting). Output file path convention and date determination.

**Cut entirely:**
- Research document template (86 lines) — replace with principles: what sections an excellent research doc needs and the quality bar for each (executive summary, findings with evidence, options analysis with effort/risk, recommendations, sources). The AI can write a great research doc from this.
- "Output Structure" section (22 lines) — duplicates the template content.
- Todo progression examples (30 lines) — the AI knows how to update todos.
- "Common Pitfalls to Avoid" (8 lines) — generic advice (confirmation bias, stopping too early) that the AI already understands.
- "Best Practices: Critical Thinking" (5 lines) — generic ("question assumptions", "consider credibility").
- "Best Practices: Documentation" (5 lines) — generic ("keep track of sources", "note the date").

**Compress:**
- "Best Practices: Search Strategy" — keep the Exa-specific tips (non-obvious), cut the generic search advice that's already in the phase descriptions.
- Phase action lists — solid substance but wordy. Each phase's actions can be tighter.
- "When to Use" list — compress to 2-3 bullet points from 5.

### `create-adr.md` (499 → ~200, B- → A)

**Structural change:** Remove the auto-execute pattern for `/research`. Step 0 becomes a lightweight prerequisite gate: check for existing research in `.writ/research/`, and if none found, recommend running `/research` first rather than auto-executing the entire research workflow. This decouples the two commands and follows Writ's pattern where commands are invoked explicitly, not embedded.

**Keep intact:** The decision analysis flow (context → scope/criteria → alternatives → document). ADR numbering convention (sequential NNNN). Status lifecycle (Proposed → Accepted → Deprecated → Superseded). "When to Use" triggers — these are non-obvious and prevent the AI from creating ADRs for trivial decisions.

**Cut entirely:**
- ADR document template (155 lines) — replace with principles: what sections an excellent ADR must contain and the quality bar for each (context with driving forces, alternatives with pros/cons/effort/risk each, decision outcome with rationale, consequences both positive and negative, implementation notes). The AI can write a great ADR from principles.
- "Best Practices" (34 lines) — generic ADR advice (focus on one decision, include sufficient context, use clear language) the AI already knows.
- "Common Pitfalls to Avoid" (31 lines) — generic warnings (rushing decisions, writing ADRs too technical, not following up).
- JSON todo_write block (20 lines) — the AI knows how to track todos.

**Compress:**
- Step 0 (auto-research) — 50 lines of prerequisite + auto-execute scaffolding → ~10 lines of prerequisite gate.
- Step 1 (analyze context) — solid but verbose with substeps and deliverables that partially duplicate each other.
- Step 2 (define scope) — same treatment.
- Step 3 (research alternatives) — keep the evaluation framework categories, compress the surrounding prose.
- Step 4 (document ADR) — keep the preparation steps (date, numbering), state what the ADR must contain as principles.

## Implementation Approach

Work file-by-file. Each file is independent — no cross-dependencies between the three commands being refined.

1. **`initialize.md`** — Most mechanical cuts (duplicate sections, templates, todo examples). Good warmup.
2. **`research.md`** — Template replacement + Exa tip preservation. Medium judgment.
3. **`create-adr.md`** — Heaviest work: template → principles, auto-execute → prerequisite gate, 60% line reduction.
4. **Validation** — Line count audit, litmus test, cross-reference check.

## Success Criteria

- All 3 files pass the three-question litmus test on every section
- Total line count: ~530 (±10% acceptable)
- No cross-reference breakage (create-adr → research prerequisite, initialize → plan-product recommendation)
- Zero functional capability lost — same features, same quality gates, same outputs
- Consistent voice and density with already-refined commands (assess-spec, edit-spec as benchmarks)

## Risks

| Risk | Impact | Mitigation |
|------|--------|------------|
| Research template cut loses structure for AI-generated docs | Research outputs become inconsistent or miss key sections | State the required sections and quality bar as principles; keep the file path convention |
| ADR template cut loses section coverage | ADRs miss consequences or alternatives analysis | Keep the section list as principles with quality bars for each; "alternatives must include status quo option" |
| Initialize brownfield analysis becomes too vague | AI skips important analysis categories | Keep the gap analysis concept and category list as a compressed principle |
| Auto-execute removal breaks expected create-adr behavior | Users expect research to happen automatically | Clear prerequisite messaging: "Check for research first, recommend /research if missing" |
