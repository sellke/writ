# Core A-Grade Refinement Specification

> Created: 2026-03-18
> Status: Complete
> Contract Locked: ✅

## Contract Summary

**Deliverable:** Refine all three core Writ commands (plan-product, create-spec, implement-spec/implement-story) and five of seven agents to A-grade quality by replacing templates and procedures with principles and quality bars.

**Must Include:** Every line in every file must pass the litmus test — teaches something non-obvious, sets a quality bar the AI wouldn't reach alone, or prevents a specific mistake.

**Hardest Constraint:** Cutting aggressively without losing the genuine insights embedded in the current commands — the experience-first discovery ordering, the drift severity model, the change surface classification.

## Design Philosophy

These commands are guidance for an AI, not programs to execute. The AI doesn't need exact markdown templates — it needs to know what matters, what's non-obvious, and where the pitfalls are.

**The litmus test for every line:**

1. Does this teach the AI something non-obvious? (Keep)
2. Does this set a quality bar the AI wouldn't reach alone? (Keep)
3. Does this prevent a specific mistake the AI would likely make? (Keep)
4. None of the above? (Cut)

**The simplification principle:** Replace templates with principles. Replace procedures with quality bars. Replace examples with one demonstration that shows judgment. Trust the AI to format, structure, and write files — tell it *what matters*, not *how to type*.

## Scope

### In Scope (10 files)

| File | Current Lines | Target | Grade Change |
|------|--------------|--------|-------------|
| commands/plan-product.md | 623 | ~280 | B- → A |
| commands/create-spec.md | 805 | ~400 | B+ → A |
| commands/implement-spec.md | 294 | ~250 | A- → A |
| commands/implement-story.md | 469 | ~320 | B → A |
| agents/review-agent.md | 454 | ~280 | B- → A |
| agents/coding-agent.md | 269 | ~200 | B+ → A |
| agents/documentation-agent.md | 299 | ~180 | B → A |
| agents/architecture-check-agent.md | 206 | ~180 | A- → A |
| agents/testing-agent.md | 256 | ~220 | B+ → A |
| **Total** | **3,675** | **~2,310** | **~37% reduction** |

### Out of Scope

- Non-core commands (ship, review, retro, status, refactor, etc.)
- Scripts (install.sh, update.sh, migrate.sh)
- System instructions, adapters, writ.mdc
- user-story-generator agent (already A)
- visual-qa-agent (already A)

## Detailed Requirements

### Cross-Cutting Changes (all files)

These mechanical changes apply to every file in scope:

1. **Remove SwitchMode references** — Cursor doesn't support programmatic mode switching. Replace with natural guidance: "This discovery phase works best in Plan Mode" — the user controls the mode.
2. **Remove "Key Improvements" sections** — Changelogs comparing to a previous version. Not execution guidance.
3. **Remove "Tool Integration" sections** — The AI already knows what tools it has.
4. **Remove "Best Practices" sections that repeat the command body** — Redundant with inline guidance.
5. **Remove "Integration with Writ Ecosystem" sections** — Cross-references for human readers, not agent guidance. Exception: keep the orchestration contract table in implement-spec.

### plan-product.md (B- → A)

**Keep intact:** Phase 1 discovery (posture selection, premise challenge, dream state mapping, one-question-at-a-time, opinionated pushback format). This is excellent — ~168 lines of genuine value.

**Simplify:** Contract format — keep the structure (Vision, Target Market, MVP Scope, Risks, Recommendations, Roadmap Phases), cut the mandatory architecture diagram (makes sense for technical specs, not product vision), compress Critical Failure Surfaces to a concept rather than exact table format.

**Rewrite:** Phase 2 file creation — replace 265 lines of markdown templates with ~40 lines of principles. For each output file (mission.md, roadmap.md, decisions.md, mission-lite.md), state what it should contain and its purpose, not an exact template. The AI can create excellent documents from the locked contract.

**Rewrite:** Contract decision — replace exact AskQuestion JSON with natural language: "Confirm with the user: lock and create, edit the contract, explore risks, or continue discussion."

**Cut entirely:** "Key Improvements Over Basic Product Planning" (34 lines), "Tool Integration" (13 lines), "Integration with Writ Ecosystem" (16 lines), "Best Practices" (29 lines).

### create-spec.md (B+ → A)

**Keep intact:** Phase 1 discovery — experience-first ordering (experience → rules → technical), pushback examples, conversation rules, cross-spec overlap check, contract format. This is the crown jewel of Writ (~206 lines).

**Keep but trim:** Visual references step — solid feature, minor compression of handling descriptions.

**Rewrite:** Phase 2 file creation — same principle as plan-product. Replace ~380 lines of templates with ~60 lines of principles for spec.md, spec-lite.md, story generation, and sub-specs.

**Rewrite:** Error mapping — keep the three concepts (Error & Rescue Map, Shadow Paths, Interaction Edge Cases) and their scope detection trigger. Compress from ~50 lines to ~25 by stating each concept with one example row instead of full templates.

**Trim:** Keep Example 2 (full discovery flow, ~95 lines) — demonstrates the feel. Cut Example 1 (simple flow, ~25 lines) — doesn't add beyond the instructions.

**Cut entirely:** "User Stories Best Practices" (33 lines — repeats template), "Key Improvements Over Original" (26 lines).

### implement-spec.md (A- → A)

**Simplify:** Pre-flight assessment — replace 35 lines reimplementing assess-spec checks with ~5 lines of principles: "Flag specs with >8 stories, >50 tasks, dependency depth >3, or any story with >7 tasks. Present flags above the execution plan and offer full /assess-spec."

**Compress:** Failure handling dialogs — tighten the options presentation.

**Keep everything else:** Dependency graph, parallel batching, execution state, resume support — all well-designed and appropriately sized.

### implement-story.md (B → A)

**Keep intact:** Pipeline diagram, gate model, change surface classification (Gate 2.5), quick mode, "What Was Built" record, error handling — all sound.

**Rewrite:** Gate 3.5 drift response — 117 lines to ~40 lines. Keep the three-tier model expressed as principles:
- Small (naming, cosmetic): Auto-amend spec-lite.md, log to drift-log.md, continue PASS. Always log what was changed visibly.
- Medium (scope/integration): Flag with warning, log, continue PASS.
- Large (fundamental): PAUSE pipeline, present to user with accept/reject/modify options.

Cut: atomic write procedure, DEV-ID continuation numbering, exact drift-log format, mixed-severity interaction rules. Add: explicit warning that spec-lite auto-mutation must be visible in pipeline summary.

**Simplify:** Commit format — replace prescriptive format with principle: "Commit with a descriptive message including story title, file counts, test results, drift status."

**Cut:** Deprecation note (8 lines).

### review-agent.md (B- → A)

**Rewrite checklist:** Replace 31 individual items with categorized principles (~15 lines):
- Acceptance Criteria (primary gate)
- Code Quality (pattern consistency, error handling, no debug artifacts)
- Security (validation, injection, auth, secrets — security is never Minor)
- Test Coverage (AC coverage, error paths, edge cases, no vacuous assertions)
- Integration (breaking changes, circular deps, migrations, env vars)

**Condense examples:** Keep PASS-with-drift and FAIL examples. Cut PASS-no-drift (trivial) and PASS-medium-drift (incremental). 140 lines → ~70 lines.

**Keep:** Drift analysis section and change surface weighting — non-obvious judgment the AI needs.

### coding-agent.md (B+ → A)

**Extract:** Prototype scope detection (50 lines) — replace with single conditional principle: "If spawned by /prototype, flag scope escalation when >5 files modified, schema changes detected, or core architecture touched."

**Keep everything else:** TDD requirements, self-verification, resume template, output format.

### documentation-agent.md (B → A)

**Restructure:** Move "no framework detected" to the primary path (top). This is 90%+ of usage.

**Compress:** Replace five detailed framework sections (~40 lines) with one conditional: "If a documentation framework is detected (VitePress, Docusaurus, Nextra, MkDocs, Storybook), follow its conventions for file placement, navigation config, and page format."

**Keep:** Mermaid diagram types, JSDoc standards, output format.

### architecture-check-agent.md (A- → A)

**Compress:** Output examples ~20% each — remove redundant commentary lines within the PROCEED, CAUTION, and ABORT examples. Already well-structured.

### testing-agent.md (B+ → A)

**Compress:** Test runner detection — the AI knows how to detect vitest vs jest vs pytest. Remove the explicit detection recipes.

**Keep:** Coverage thresholds, failure analysis table, coverage best practices — all non-obvious.

## Implementation Approach

Work file-by-file in this order:

1. **Cross-cutting pass** — Remove SwitchMode, redundant sections from all 10 files (mechanical, fast)
2. **plan-product.md** — Biggest percentage reduction, establishes the "templates → principles" pattern
3. **create-spec.md** — Apply the same pattern, careful with error mapping (keep the insights)
4. **implement-story.md** — Drift handling rewrite is the highest-risk change
5. **implement-spec.md** — Minor, mostly pre-flight simplification
6. **review-agent.md** — Biggest agent lift, checklist → principles
7. **coding-agent.md** — Extract prototype section
8. **documentation-agent.md** — Restructure to default-first
9. **architecture-check + testing agents** — Minor compression
10. **Validation** — Line count audit, litmus test, cross-reference check

## Success Criteria

- All 10 files pass the three-question litmus test on every section
- Total line count: ~2,310 (±10% acceptable)
- No command references a section that was cut from another command
- Zero functional capability lost — same pipeline, same quality gates, same artifacts
- The drift-log format reference in `.writ/docs/drift-report-format.md` remains consistent with simplified Gate 3.5 guidance

## Risks

| Risk | Impact | Mitigation |
|------|--------|------------|
| Drift handling simplification loses edge case coverage | AI mishandles mixed-severity or Large drift | Keep one complete drift-log example and the severity classification principles |
| Review checklist reduction misses security items | Security vulnerabilities pass review | Keep security items explicit; add "security is never Minor" as a bright-line rule |
| Cut too much from create-spec Phase 2 | AI generates poor spec packages | Keep the directory structure, file purposes, and error mapping concepts; cut only the exact markdown templates |
| Cross-reference breakage | Commands reference cut sections | Validation story includes explicit cross-reference audit |
