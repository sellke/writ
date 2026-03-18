# Story 2: refactor.md Refinement

> **Status:** Not Started
> **Priority:** High
> **Dependencies:** None

## User Story

**As a** Writ maintainer
**I want to** refine refactor.md to A-grade quality
**So that** every line teaches the AI something non-obvious, sets a quality bar, or prevents a specific mistake — with no redundant filler

## Acceptance Criteria

1. **Given** the refined refactor.md, **when** an AI agent executes the command, **then** safety guarantees (baseline verification, verify-per-change, rollback, commit-per-change, no behavior changes, ADR for major changes) remain fully intact.

2. **Given** the refined file, **when** applying the litmus test to every line, **then** each line either teaches something non-obvious, sets a quality bar, or prevents a specific mistake — with no filler.

3. **Given** the refined file, **when** counting lines, **then** the total is within ~220 ±10% (198–242 lines), down from 416.

4. **Given** the refined file, **when** checking for bash example blocks per mode, **then** all are replaced with principles about what each mode detects.

5. **Given** the refined file, **when** reading the mode-specific workflows section, **then** the 5 modes (duplicates, dead-code, modernize, types, extract) no longer repeat scan→propose→execute→verify; instead a single principle states the universal workflow, with only mode-unique detection targets listed.

## Implementation Tasks

1. **Read the current file** — Verify line numbers for bash blocks, mode-specific workflows, safety guarantees. Confirm the mode table, baseline verification, analysis report format, refactoring plan table, AskQuestion decision points.

2. **Replace bash examples with principles per mode** — Step 1.3 has ~100 lines of rg/wc/for-loop bash for file/module/duplicates/dead-code/modernize/types modes. Replace each with a principle stating what to analyze: **file** — size, exports, importers, dependencies, test coverage, issues like god modules, nested conditionals, magic strings, legacy patterns; **duplicates** — similar function signatures and bodies; **dead-code** — unused exports, orphan files; **modernize** — var, require, callbacks, class components, CJS; **types** — any, ts-ignore, ts-expect-error, missing return types.

3. **Collapse mode-specific workflows** — The 5 subsections (duplicates, dead-code, modernize, types, extract) at lines 358–395 each repeat: scan → group → propose → execute → verify. State this once as the universal mode workflow principle, then list only what's unique per mode (what to scan for, how to group findings).

4. **Cut baseline metrics JSON** — The JSON block (lines 78–87) is obvious format. State: "Record baseline test count, type errors, lint errors for post-refactoring comparison."

5. **Cut import update bash** — Lines 298–304 are obvious. Keep the principle: "When moving exports, update all importers automatically."

6. **Compress Phase 3 and Phase 4** — Phase 3's 4-step procedure (checkpoint → apply → verify → commit/revert) is clear as a principle. Phase 4's verification report is a good format — express as quality bar ("produce before/after metrics comparison, list all commits made"), not a full markdown template.

7. **Verify and tighten** — Apply the litmus test to every remaining line. Preserve: mode table, safety guarantees, baseline requirement, commit-per-change discipline, risk-ordered execution, AskQuestion decision points. Ensure line count within target.

## Notes

- **Technical:** The safety guarantees section (lines 399–406) is the crown jewel of this command — every item is genuinely non-obvious and prevents the AI from cutting corners. Preserve it verbatim or as prominently-stated principles.

- **Risk:** Removing bash examples could make the AI unsure what each mode should analyze. Mitigate by expressing detection targets as explicit principles per mode (e.g., "modernize mode detects: var→const/let, require→import, .then→async/await, CJS→ESM, React.FC→function components, class→hooks").

- **Watch for:** The AskQuestion blocks for scope selection and plan approval are decision gates that should be preserved. Don't cut the decision points, only the surrounding scaffolding.

## Definition of Done

- [ ] All tasks completed
- [ ] All acceptance criteria met
- [ ] Line count within target range (~220 ±10%)
- [ ] Safety guarantees section preserved prominently
- [ ] No bash script blocks remain — all expressed as principles
