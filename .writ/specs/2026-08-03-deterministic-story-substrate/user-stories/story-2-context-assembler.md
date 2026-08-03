# Story 2: Deterministic Context Assembler

> **Status:** Not Started
> **Priority:** High
> **Dependencies:** None

## User Story

**As a** Writ maintainer
**I want to** resolve `## Context for Agents` hints through a single deterministic Python assembler that emits a structured JSON payload with per-category byte counts
**So that** per-story agent context is reproducible and measurable rather than re-derived by LLM judgment on every `/implement-story` run, and `story_context_bytes` can eventually reflect bytes actually loaded instead of a declared-load proxy

## Acceptance Criteria

- [ ] Given a story file whose `## Context for Agents` section uses bracketed references (`[Operation name]`) and extended references (`file.md → ## Section → ### Subsection`), when `scripts/story-context.py assemble --story <path>` runs against a fixture spec tree, then both forms resolve against the documented primary sources and fallbacks (`technical-spec.md` with `spec.md` fallbacks for Error map rows and Shadow paths; `spec.md` only for Business rules and Experience) and the JSON payload includes populated `fetched_context`, per-category `bytes`, and `warnings`.
- [ ] Given fixtures covering every degradation branch from the edge-case table (section absent, category prefix typo, malformed brackets, empty brackets `[]`, missing referenced row, `technical-spec.md` absent, `spec.md` unreadable, duplicate category lines), when the assembler runs, then it warns-and-continues or returns an empty payload — never raises — matching the seven-row degradation table at `commands/implement-story.md` lines 109–118 and the Error & Rescue Map rows for hint parsing, source reading, and reference resolving.
- [ ] Given an unchanged spec tree and story file, when the assembler runs twice, then stdout JSON is byte-identical — determinism is asserted by test, not assumed (Business Rule 5).
- [ ] Given `scripts/eval-leanness.py` computes `story_context_components()`, when it measures `context_hints`, then it imports `scripts/story-context.py` and `resolve_context_hints()` is deleted — exactly one implementation of hint resolution survives, preserving the contract that unresolvable references contribute 0 bytes and never raise (`eval-leanness.py` lines 234–237).
- [ ] Given synthetic fixtures derived from `.writ/docs/context-hint-format.md` Error Handling and edge-case tables, when `scripts/eval-story-context.py` scenarios run via `bash scripts/eval.sh --check=story-context`, then all scenarios PASS and fixture-level behavior matches the prose parser contract at `commands/implement-story.md` lines 75–123 before Story 4 removes that prose.

## Implementation Tasks

- [ ] 2.1 Write failing unit tests in `scripts/tests/test_story_context.py` with fixtures under `scripts/tests/fixtures/` covering both reference forms, all four categories, every Error Handling row in `.writ/docs/context-hint-format.md`, and the Interaction Edge Cases this story touches (byte-identical repeat runs, duplicate category deduplication, Unicode section headers, empty `[]` brackets); target ≥80% coverage on new code and 100% on error/degradation paths per `sub-specs/technical-spec.md`.
- [ ] 2.2 Implement `scripts/story-context.py` with `assemble --story <path> [--budget-bytes N]` mirroring the `spec-deps.py` read-only CLI pattern: locate `## Context for Agents`, parse the four categories in bracketed and extended forms, resolve content per the 4-row source/fallback table at `commands/implement-story.md` lines 98–103, emit the JSON envelope (`fetched_context`, `warnings`, `bytes`, `truncated`) defined in `sub-specs/technical-spec.md`; accept `--budget-bytes` as a passthrough flag but do not enforce truncation yet (Story 3).
- [ ] 2.3 Delete `resolve_context_hints()` and related category-resolution helpers from `scripts/eval-leanness.py`; refactor `story_context_components()` to call the assembler for byte measurement while preserving the "unresolvable contributes 0, never an error" contract for malformed stories.
- [ ] 2.4 Create `scripts/eval-story-context.py` as a scenario emitter following the existing `eval-*.py` PASS/FAIL TSV convention, exercising happy path, legacy absent hints section, all six documented degradation scenarios, both reference forms, and byte-identical repeat output.
- [ ] 2.5 Register `story-context` in the `CHECKS` array in `scripts/eval.sh` lines 19–47 and implement `check_story_context()` that runs `eval-story-context.py` scenarios; do not add literal checks on `commands/implement-story.md` yet — prose replacement is Story 4.
- [ ] 2.6 Run `python3 -m pytest scripts/tests/test_story_context.py`, `python3 scripts/eval-story-context.py`, `bash scripts/eval.sh --check=story-context`, and `bash scripts/eval.sh --check=leanness`; verify all acceptance criteria pass and Tier 1 eval stays green.
- [ ] 2.7 Record baseline justification for `scripts/` surface growth (ADR-019 ratchet) in the story's What Was Built summary — moving the hint contract from unmeasured `.writ/docs/` prose into measured `scripts/` is expected growth, not an exemption.

## Notes

**Scope boundary — deliberate stops:** This story creates and proves the assembler; it does **not** wire `/implement-story` Step 2 to call it (Story 4) and does **not** measure real specs, derive, or enforce a `fetched_context` byte budget (Story 3). The prose parser at `commands/implement-story.md` lines 75–123 remains the runtime implementation until Story 4 is gated on Story 3.

**Equivalence is the real risk.** An LLM following prose and a regex following a grammar will not agree on every ambiguous input, and the prose has no test suite defining correct behavior. Fixtures are derived from the edge-case table in `.writ/docs/context-hint-format.md` because it is the closest thing to a written specification that exists. A brittle assembler is **worse** than prose — an LLM improvises around a malformed hint and a regex does not — which is why every failure mode degrades rather than raising, and why Story 4 is gated on Story 3 so the script is exercised on real specs before the prose is removed.

**Integration points:**

- `.writ/docs/context-hint-format.md` — 433-line contract this script becomes the executable reference for (docs rewrite pointing at the script is Story 4).
- `commands/implement-story.md` lines 75–123 — behavior to reproduce on fixtures; routing table at lines 191–195 stays untouched (Business Rule 7).
- `scripts/eval-leanness.py` — consumer that must import the assembler so `story_context_bytes` can eventually match delivered bytes.
- `scripts/spec-deps.py` — precedent for CLI shape, JSON envelope, and `eval.sh` registration pattern.

**Parser details worth encoding in tests:**

- Section extraction runs from `## Context for Agents` to the next `##` heading or EOF (`context_for_agents_section()` in `eval-leanness.py` lines 223–231 is the starting point, but bracketed item resolution must match row names exactly, not whole-section keyword heuristics).
- Extended references use backtick-delimited `` `file.md → ## Section → ### Subsection` `` paths with `→` or `>>` arrows.
- Duplicate category lines merge references, deduplicate, and warn once (Interaction Edge Cases).
- Empty brackets `[]` skip the category silently — valid signal, not an error.

## Definition of Done

- [ ] All tasks completed
- [ ] All acceptance criteria met
- [ ] Tests passing
- [ ] Code reviewed
- [ ] Documentation updated

## Context for Agents

- **Error map rows:** [Read story file, Locate hints section, Parse hint category, Read source spec, Resolve reference, `eval-leanness` calls assembler]
- **Shadow paths:** [Context assembly, Leanness measurement]
- **Business rules:** [One implementation per contract, Determinism is a testable property, Legacy stories never break, Orchestration policy stays in the command]
- **Experience:** [Entry Point, Happy Path, Error Experience, Feedback Model]
