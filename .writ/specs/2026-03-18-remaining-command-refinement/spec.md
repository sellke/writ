# Remaining Command Refinement Specification

> Created: 2026-03-18
> Status: Planning
> Contract Locked: ✅

## Contract Summary

**Deliverable:** Refine `/new-command`, `/refactor`, `/review`, and `/retro` to A-grade quality using the same litmus test and simplification principles proven in the core, secondary, and utility refinement specs.

**Must Include:** Every line in every file must pass the litmus test — teaches something non-obvious, sets a quality bar the AI wouldn't reach alone, or prevents a specific mistake.

**Hardest Constraint:** `/review` is already relatively tight at 292 lines — the challenge is cutting without losing its structured technique approach, which is genuinely valuable. `/retro` has the most bulk but also embeds real algorithmic judgment (session detection, streak heuristics) that needs preserving as principles rather than procedures.

## Design Philosophy

Identical to the core, secondary, and utility refinement specs. These commands are guidance for an AI, not programs to execute. The AI doesn't need exact markdown templates — it needs to know what matters, what's non-obvious, and where the pitfalls are.

**The litmus test for every line:**

1. Does this teach the AI something non-obvious? (Keep)
2. Does this set a quality bar the AI wouldn't reach alone? (Keep)
3. Does this prevent a specific mistake the AI would likely make? (Keep)
4. None of the above? (Cut)

**The simplification principle:** Replace templates with principles. Replace procedures with quality bars. Replace examples with one demonstration that shows judgment. Trust the AI to format, structure, and write files — tell it *what matters*, not *how to type*.

## Scope

### In Scope (4 files)

| File | Current Lines | Target | Grade Change |
|------|--------------|--------|-------------|
| commands/new-command.md | 438 | ~200 | B- → A |
| commands/refactor.md | 416 | ~220 | B → A |
| .cursor/commands/review.md | 292 | ~200 | B+ → A |
| .cursor/commands/retro.md | 455 | ~220 | B → A |
| **Total** | **1,601** | **~840** | **~47% reduction** |

### Out of Scope

- Core commands (already refined: plan-product, create-spec, implement-spec, implement-story)
- Secondary commands (in-flight: create-issue, design, prototype)
- Utility commands (in-flight: initialize, research, create-adr)
- Recently refined commands (assess-spec, edit-spec)
- All agents, scripts, system instructions, Cursor adapter layer

### File Location Note

`review.md` and `retro.md` live in `.cursor/commands/` (Cursor adapter), not `commands/` (product source). In the Writ repo, `.cursor/` is symlinked to product source, so edits to these files are edits to the product. Refine them in place.

## Detailed Requirements

### `new-command.md` (438 → ~200, B- → A)

**Keep intact:** Contract-first workflow (Phase 1 discovery). This follows the same pattern as `create-spec` and is Writ's crown jewel interaction model. Critical analysis responsibility and pushback phrasing — non-obvious guidance that prevents the AI from being a yes-machine. Command category awareness (planning, implementation, setup, quality, meta).

**Cut entirely:**
- AI Implementation Prompt (lines 274–325, ~52 lines) — restates the entire process above it. The AI executing `/new-command` reads the whole file; it doesn't need a redundant summary.
- Template Sections Based on Command Type (lines 206–240, ~35 lines) — per-type template scaffolding (contract style, direct execution, setup, implementation, integration). The AI can infer appropriate structure from the command's execution style.
- Implementation Details / Command Name Validation (lines 329–348, ~20 lines) — regex validation and conflict checking are obvious.
- Template Selection Logic (lines 349–395, ~47 lines) — hardcoded line numbers for documentation updates that break as files change. Category taxonomy the AI already knows.
- Documentation Update Locations (lines 377–395) — hardcoded line numbers into cc.md, cc.mdc, README.md. These break on every edit.
- Error Handling section (lines 396–416, ~20 lines) — error messages the AI can compose on the spot.
- Future Enhancements (lines 428–438, ~11 lines) — planning noise, not execution guidance.
- Integration Notes (lines 418–426, ~9 lines) — generic statements about consistency and extensibility.

**Compress:**
- Phase 1 discovery questions — keep the critical analysis responsibility and pushback phrasing, tighten the topic exploration areas.
- Echo Check format — keep as a principle ("present a command contract covering: name, purpose, unique value, execution style, workflow, inputs, outputs, concerns"), not a markdown template.
- Phase 2 creation — the AI knows how to write a well-structured command file. State what a good command file contains (overview, invocation table, command process, core rules, integration table) and the quality bars, not the exact section templates.
- Step 3 validation — compress to a principle about verifying integration consistency.

### `refactor.md` (416 → ~220, B → A)

**Keep intact:** Mode table at the top (concise, valuable reference for invocation patterns). Baseline verification requirement (non-obvious — the AI would likely skip this and refactor on broken tests). Commit-per-change discipline (non-obvious — the AI's instinct is to batch). Safety guarantees (green baseline required, verify after every change, automatic rollback, commit per change, import updates, no behavior changes, ADR for major changes). Analysis report format with risk/impact assessment. Refactoring plan table with risk ordering.

**Cut entirely:**
- Bash example blocks throughout Step 1.3 (lines 93–196, ~100 lines) — detailed `rg`, `wc`, `for` loops for each mode. The AI knows how to search a codebase. State *what* to analyze per mode, not *how* to grep.
- Mode-Specific Workflows section (lines 358–395, ~38 lines) — each of the 5 modes (duplicates, dead-code, modernize, types, extract) repeats the same pattern: scan → propose → execute → verify. State this once as a principle.
- Import update bash (lines 298–304) — obvious.
- Baseline metrics JSON (lines 78–87) — obvious format.

**Compress:**
- Step 1.3 Deep Analysis — keep the concept of what to analyze (size, exports, importers, dependencies, test coverage for file mode; similar signatures for duplicates; unused exports for dead code; legacy patterns for modernize; `any` types for types). Express as principles per mode, not bash scripts.
- Phase 3 Execution — the verify-after-each-change pattern is clear. Compress the 4-step procedure to a principle.
- Phase 4 Verification Report — good before/after comparison format. Keep as a quality bar ("produce a before/after metrics comparison and list all commits"), not a full markdown template.
- AskQuestion blocks — keep the decision points, compress the surrounding scaffolding.

### `review.md` (292 → ~200, B+ → A)

Already the tightest of the four. The 5 techniques are genuinely valuable, structured, and non-obvious.

**Keep intact:** All 5 review techniques (Error & Rescue Map, Shadow Path Tracing, Interaction Edge Cases, Failure Modes Registry, Architecture Diagram). The severity classification table. The "Recommendation is the soul" quality bar. Trust boundary focus for shadow paths. The "I recommend" judgment calls within each technique. Invocation table. Integration with `/ship` (output-based coupling via `.writ/state/`). Table format note about shared structure with `/create-spec` error mapping.

**Cut:**
- "How `/review` differs from pipeline review" comparison table (lines 11–19) — context for humans reading the command file, not guidance for the AI executing it.
- Error Handling section (lines 254–282) — "No changes to review", "Diff too large", "No default branch" messages are obvious.
- "When to Use /review vs Other Commands" table (lines 283–292) — generic routing the AI can determine from context.

**Compress:**
- Step 2 (Scan the Diff) — good categories (data flows, UI, infrastructure, trust boundaries, external dependencies, what's absent) but can be tighter.
- Technique introductions — each technique has a 1-2 line intro before its table. Some can be cut where the table is self-explanatory.
- Architecture Diagram guidance — keep the when-to-include/skip criteria, compress the example slightly.

### `retro.md` (455 → ~220, B → A)

**Keep intact:** Session detection concept (2-hour gap threshold, single-commit exclusion, bot/CI filtering, merge commit handling — this is genuinely non-obvious). Streak calculation with the "≥5 days" acknowledgment threshold. Writ context collection concept (specs, stories, drift, commands refreshed). Ship of the Week selection heuristic (spec completion > commit breadth > message signals > LOC impact > Writ context). Opinionated pattern detection guidance with pattern type table. Tweetable forcing function. Compare mode concept. Spec-scoping. Snapshot persistence for trend comparison.

**Cut entirely:**
- Full JSON schema for snapshot (lines 287–337, ~50 lines) — state the required fields and their purpose as principles. The AI knows how to write JSON.
- Full JSON schema for trends (lines 352–376, ~25 lines) — same treatment.
- Step 7 full output template (lines 203–248, ~45 lines) — markdown template the AI can write from principles about what each section should contain and its quality bar.
- Compare mode output template (lines 392–407, ~15 lines) — same.
- Detailed bash commands for git metrics (lines 62–96, ~35 lines) — `git log --oneline`, `git log --numstat`, `git log --name-only`. The AI knows git.
- Test file pattern list (lines 90–95) — the AI knows what test files look like.
- Session statistics table (lines 130–136) — obvious once the concept is stated.
- Schema notes section (lines 339–343) — version field purpose is obvious.

**Compress:**
- Auto-detect environment section — concept (detect timezone, default branch, period) is good; verbose with bash examples.
- Session detection algorithm — express as heuristic principles (gap threshold, exclusions, edge cases) rather than step-by-step pseudocode.
- Streak calculation — compress to concept + quality bars.
- Writ context collection — list what to collect and graceful skip behavior, not step-by-step instructions.
- Error handling section — compress to 2-3 sentences about graceful failure.

## Implementation Approach

Work file-by-file. Each file is independent — no cross-dependencies between the four commands being refined.

1. **`new-command.md`** — Heaviest cut ratio (438 → ~200, 54%). Most mechanical: AI Implementation Prompt, templates, and hardcoded line numbers are clear cuts. Good warmup.
2. **`refactor.md`** — Bash script replacement (procedures → principles). Medium judgment — deciding which mode-specific details are genuinely non-obvious.
3. **`review.md`** — Lightest touch (292 → ~200, 31%). Already tight. Precision trimming — remove supporting context, preserve technique substance.
4. **`retro.md`** — Algorithmic content needs careful compression: session detection, streak calculation, and pattern guidance encode real judgment. Express as principles, not pseudocode.
5. **Validation** — Line count audit, litmus test, cross-reference check, capability comparison, voice/density comparison.

## Success Criteria

- All 4 files pass the three-question litmus test on every section
- Total line count: ~840 (±10% acceptable, 756–924)
- No cross-reference breakage (review → ship integration, refactor → create-adr, retro → .writ/retros/)
- Zero functional capability lost — same features, same quality gates, same outputs
- Consistent voice and density with already-refined commands (assess-spec, edit-spec as benchmarks)

## Risks

| Risk | Impact | Mitigation |
|------|--------|------------|
| Review technique compression loses the structured judgment framework | Review outputs become generic checklists instead of failure-mode analysis | Preserve all 5 technique tables and severity classifications intact; only compress surrounding prose |
| Retro session detection becomes too vague | Session metrics lose accuracy or the AI invents its own (wrong) heuristics | Keep the 2-hour gap threshold, single-commit exclusion, and bot filtering as explicit principles |
| New-command template cut makes generated commands inconsistent | New commands don't follow Writ patterns | State what a good command file contains and its quality bars; include the invocation table and integration table as required elements |
| Refactor bash cuts lose mode-specific analysis guidance | AI doesn't know what to look for in each mode | Express what-to-detect per mode as principles (dead-code: unused exports, orphan files; modernize: var, require, callbacks, class components; types: any, ts-ignore, missing returns) |
