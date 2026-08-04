# Technical Specification: Secondary Command Refinement

## Architecture

This spec modifies three existing command files. No new files are created — the work is purely editorial refinement of existing content.

### Files in Scope

| File | Operation | Key Changes |
|------|-----------|-------------|
| `commands/create-issue.md` | Edit in place | Cut 5 sections (~87 lines), compress examples, merge Core Rules |
| `commands/design.md` | Edit in place | Cut 4 sections (~47 lines), replace 3 templates with principles, compress 2 modes |
| `commands/prototype.md` | Edit in place | Rewrite agent prompt (80→25 lines), consolidate 3 output formats, merge error handling |

### Cross-References to Preserve

| Source | Reference | Context |
|--------|-----------|---------|
| `commands/prototype.md` | `agents/coding-agent.md` | Agent spawn in Step 3 — prototype mode |
| `commands/design.md` | `agents/visual-qa-agent.md` | Gate 4.5 in implement-story pipeline |
| `commands/design.md` | Coding agent Gate 1 | How coding agent loads visual references |

### Pattern Reference

The refinement follows the same pattern established in `2026-03-18-core-agrade-refinement`:

**The litmus test (applied per-line):**
1. Teaches something non-obvious → Keep
2. Sets a quality bar the AI wouldn't reach alone → Keep
3. Prevents a specific mistake the AI would likely make → Keep
4. None of the above → Cut

**Common cut patterns (from core refinement):**
- "Tool Integration" tables — the AI knows its tools
- "Key Improvements" / "Integration Notes" sections — changelog material, not execution guidance
- "Future Enhancements" — product roadmap, not agent instructions
- Exact markdown templates where principles suffice — the AI can write good markdown
- JSON schemas for formats the AI already knows (Excalidraw, etc.)
- Multiple examples showing the same judgment — one demonstration suffices

**Common keep patterns:**
- Decision logic (when to ask vs skip, when to search vs not)
- Non-obvious conventions (wireframe annotation colors, label-everything for coding agent)
- Pipeline integration details (how one command's output feeds another's input)
- Scope detection heuristics (prototype's 6 escalation flags)
- Quality bars the AI wouldn't set for itself ("under 2 minutes", "max 3 files")

### Voice and Density Benchmarks

Already-refined commands to use as style references:

| File | Lines | Character |
|------|-------|-----------|
| `commands/assess-spec.md` | 203 | Dense tables, principle-per-row, minimal prose |
| `commands/edit-spec.md` | 118 | Extremely compressed, contract-first, no templates |
| `commands/plan-product.md` | ~273 | Discovery-heavy, preserves Phase 1 intact |
| `commands/create-spec.md` | ~400 | Crown jewel discovery, Phase 2 compressed |

The secondary commands should read at a similar density — direct, principle-driven, no filler.

## Implementation Order

Stories 1, 2, 3 are fully independent — no shared files, no shared content, no dependency between them. They can execute in any order or in parallel.

Story 4 (validation) must run after all three are complete.

## Risk Mitigations

| Risk | Mitigation |
|------|------------|
| Over-compression losing nuance | Each story's Notes section identifies the specific high-value content to protect |
| Cross-reference breakage | Story 4 includes explicit grep-based cross-reference verification |
| Pattern drift from core refinement | Story 4 includes voice/density comparison against already-refined commands |
| Scope escalation flags get summarized instead of preserved | Story 3 explicitly calls out: keep the six flags verbatim |
