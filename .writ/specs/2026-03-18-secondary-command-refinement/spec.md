# Secondary Command Refinement Specification

> Created: 2026-03-18
> Status: Planning
> Contract Locked: ✅

## Contract Summary

**Deliverable:** Refine `/create-issue`, `/design`, and `/prototype` to A-grade quality using the same litmus test and simplification principles proven in the core refinement spec (`2026-03-18-core-agrade-refinement`).

**Must Include:** Every line in every file must pass the litmus test — teaches something non-obvious, sets a quality bar the AI wouldn't reach alone, or prevents a specific mistake.

**Hardest Constraint:** `/design` needs the most structural work — it has four modes with real value, but templates and JSON schemas obscure what actually matters.

## Design Philosophy

Identical to the core refinement spec. These commands are guidance for an AI, not programs to execute. The AI doesn't need exact markdown templates — it needs to know what matters, what's non-obvious, and where the pitfalls are.

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
| commands/create-issue.md | 307 | ~140 | B+ → A |
| commands/design.md | 377 | ~200 | B- → A |
| commands/prototype.md | 358 | ~210 | B+ → A |
| **Total** | **1,042** | **~550** | **~47% reduction** |

### Out of Scope

- Core commands (already refined: plan-product, create-spec, implement-spec, implement-story)
- Recently refined commands (assess-spec, edit-spec — in-flight on main)
- All other commands (ship, review, retro, status, refactor, etc.)
- Agents (already refined in core spec)
- Scripts, system instructions, adapters

## Detailed Requirements

### `create-issue.md` (307 → ~140, B+ → A)

**Keep intact:** Core process (Steps 1-6), "speed over completeness" philosophy, question triggers with skip-if-obvious logic, related issues check, section omission rules. This command is already well-designed — the process flow is tight and the judgment calls (when to ask, when to skip, when to search) are the valuable content.

**Cut entirely:**
- "AI Implementation Prompt" (55 lines) — restates the command process verbatim in a separate format. The AI is already reading the process as its instructions.
- "Integration Notes" (9 lines) — tool usage the AI already knows.
- "Folder Structure" (13 lines) — duplicates what Step 5 already specifies.
- "Future Enhancements" (10 lines) — product roadmap, not execution guidance.

**Compress:**
- Four examples → one. Keep Example 2 (the clarification case) — it demonstrates the key judgment: when to ask vs when to skip. The other three show straightforward happy paths that don't teach the AI anything it wouldn't do naturally.
- "Core Rules" section — merge into process steps as inline guidance rather than a separate section that partially duplicates them.

### `design.md` (377 → ~200, B- → A)

**Keep intact:** Modal structure (wireframe / attach / capture / compare / review) as the organizing spine. Wireframe conventions that are genuinely non-obvious: gray fills for placeholder media, dashed borders for conditional elements, red annotations for interaction notes, and critically — "label everything, the coding agent reads these labels." Pipeline integration concept (how the coding agent loads and uses visual references at Gate 1).

**Cut entirely:**
- "Tool Integration" table (9 lines) — same pattern cut from all core commands.
- Excalidraw JSON schema (20 lines) — the AI knows how to write Excalidraw JSON.
- Component primitive list (6 lines) — rectangles, text, lines are obvious.
- Bash code examples in Mode C (12 lines) — the browser MCP captures screenshots; Playwright scripts are misleading here.

**Replace templates with principles:**
- Component-inventory template (18 lines) → state what it should contain (components, states, design token references) and its purpose (feed the coding agent component structure).
- mockups/README template (17 lines) → describe the catalog purpose and key fields.
- Design system extraction template (35 lines) → state the concept (auto-extract from mockups if no design-system.md exists) and the categories to extract (colors, typography, spacing, component tokens). The AI can write excellent design system docs from this.

**Compress:**
- Mode C (capture current UI) and Mode D (compare) — each to ~10-15 lines expressing the concept and quality bar. Compare mode's table format (mockup vs implementation comparison) is the valuable part; the surrounding scaffolding isn't.
- Mode A's component states list — keep the concept (generate states: default, loading, empty, error), compress the naming convention.

### `prototype.md` (358 → ~210, B+ → A)

**Keep intact:** Pipeline diagram (shows the flow at a glance). Visual preview step (Step 2.5) — this is innovative, genuinely non-obvious, and well-written. Scope escalation flags (the six specific signals). Experience gaps concept in output. "When to Use" comparison table. UI detection heuristic. "Nearby rules" sniffing in context scan.

**Rewrite:** Agent spawn prompt (80 lines → ~25 lines of principles). The coding agent needs: change description, codebase context, TDD requirement, scope detection triggers, experience gap awareness, and the instruction to respect nearby rules. It doesn't need exact output format headers or the full instructions re-explained.

**Consolidate:** Three output format sections (success / success-with-escalation / failure) currently 70+ lines → ~20 lines covering the key elements: what to show, when to surface escalation notice, how to handle lint failures after retries.

**Merge:** Error handling section (18 lines) into the pipeline description. "Agent crash: retry once, surface partial progress" is one principle, not a formatted block. "Blocked: present blocker, partial progress, and options" is another.

**Keep but trim:** Lint & Typecheck step — the detection-and-retry logic is sound but the language/tool matrix is something the AI can figure out from the project.

## Implementation Approach

Work file-by-file. Each file is independent — no cross-dependencies between the three commands being refined.

1. **`create-issue.md`** — Simplest cut (mostly removing redundant sections). Good warmup.
2. **`design.md`** — Heaviest structural work (templates → principles across four modes).
3. **`prototype.md`** — Agent prompt rewrite is the most judgment-intensive change.
4. **Validation** — Line count audit, litmus test spot-check, cross-reference integrity.

## Success Criteria

- All 3 files pass the three-question litmus test on every section
- Total line count: ~550 (±10% acceptable)
- No cross-reference breakage (prototype → coding-agent, design → visual-qa-agent, design → coding-agent Gate 1)
- Zero functional capability lost — same features, same quality gates, same outputs
- Pattern consistency with already-refined commands (same voice, same density)

## Risks

| Risk | Impact | Mitigation |
|------|--------|------------|
| Design command's four modes lose clarity when compressed | AI conflates modes or skips steps | Keep modal structure as the organizing spine — compress within each mode, not across |
| Prototype's agent prompt compression loses scope detection nuance | Coding agent misses escalation signals | Keep the six scope flags as an explicit list — they're the non-obvious part |
| Create-issue becomes too terse for its "speed" philosophy | AI over-engineers issues or asks too many questions | Keep "speed over completeness" principle prominent and skip-if-obvious triggers |
| Pattern drift from core refinement | Inconsistent quality bar across commands | Reference already-refined assess-spec and edit-spec as style benchmarks |
