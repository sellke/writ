# Story 2: Deterministic Context Assembler

> **Status:** Completed ✅ (2026-08-03)
> **Priority:** High
> **Dependencies:** None

## User Story

**As a** Writ maintainer
**I want to** resolve `## Context for Agents` hints through a single deterministic Python assembler that emits a structured JSON payload with per-category byte counts
**So that** per-story agent context is reproducible and measurable rather than re-derived by LLM judgment on every `/implement-story` run, and `story_context_bytes` can eventually reflect bytes actually loaded instead of a declared-load proxy

## Acceptance Criteria

- [x] Given a story file whose `## Context for Agents` section uses bracketed references (`[Operation name]`) and extended references (`file.md → ## Section → ### Subsection`), when `scripts/story-context.py assemble --story <path>` runs against a fixture spec tree, then both forms resolve against the documented primary sources and fallbacks (`technical-spec.md` with `spec.md` fallbacks for Error map rows and Shadow paths; `spec.md` only for Business rules and Experience) and the JSON payload includes populated `fetched_context`, per-category `bytes`, and `warnings`.
- [x] Given fixtures covering every degradation branch from the edge-case table (section absent, category prefix typo, malformed brackets, empty brackets `[]`, missing referenced row, `technical-spec.md` absent, `spec.md` unreadable, duplicate category lines), when the assembler runs, then it warns-and-continues or returns an empty payload — never raises — matching the seven-row degradation table at `commands/implement-story.md` lines 109–118 and the Error & Rescue Map rows for hint parsing, source reading, and reference resolving.
- [x] Given an unchanged spec tree and story file, when the assembler runs twice, then stdout JSON is byte-identical — determinism is asserted by test, not assumed (Business Rule 5).
- [x] Given `scripts/eval-leanness.py` computes `story_context_components()`, when it measures `context_hints`, then it imports `scripts/story-context.py` and `resolve_context_hints()` is deleted — exactly one implementation of hint resolution survives, preserving the contract that unresolvable references contribute 0 bytes and never raise (`eval-leanness.py` lines 234–237).
- [x] Given synthetic fixtures derived from `.writ/docs/context-hint-format.md` Error Handling and edge-case tables, when `scripts/eval-story-context.py` scenarios run via `bash scripts/eval.sh --check=story-context`, then all scenarios PASS and fixture-level behavior matches the prose parser contract at `commands/implement-story.md` lines 75–123 before Story 4 removes that prose.

## Implementation Tasks

- [x] 2.1 Write failing unit tests in `scripts/tests/test_story_context.py` with fixtures under `scripts/tests/fixtures/` covering both reference forms, all four categories, every Error Handling row in `.writ/docs/context-hint-format.md`, and the Interaction Edge Cases this story touches (byte-identical repeat runs, duplicate category deduplication, Unicode section headers, empty `[]` brackets); target ≥80% coverage on new code and 100% on error/degradation paths per `sub-specs/technical-spec.md`.
- [x] 2.2 Implement `scripts/story-context.py` with `assemble --story <path> [--budget-bytes N]` mirroring the `spec-deps.py` read-only CLI pattern: locate `## Context for Agents`, parse the four categories in bracketed and extended forms, resolve content per the 4-row source/fallback table at `commands/implement-story.md` lines 98–103, emit the JSON envelope (`fetched_context`, `warnings`, `bytes`, `truncated`) defined in `sub-specs/technical-spec.md`; accept `--budget-bytes` as a passthrough flag but do not enforce truncation yet (Story 3).
- [x] 2.3 Delete `resolve_context_hints()` and related category-resolution helpers from `scripts/eval-leanness.py`; refactor `story_context_components()` to call the assembler for byte measurement while preserving the "unresolvable contributes 0, never an error" contract for malformed stories.
- [x] 2.4 Create `scripts/eval-story-context.py` as a scenario emitter following the existing `eval-*.py` PASS/FAIL TSV convention, exercising happy path, legacy absent hints section, all six documented degradation scenarios, both reference forms, and byte-identical repeat output.
- [x] 2.5 Register `story-context` in the `CHECKS` array in `scripts/eval.sh` lines 19–47 and implement `check_story_context()` that runs `eval-story-context.py` scenarios; do not add literal checks on `commands/implement-story.md` yet — prose replacement is Story 4.
- [x] 2.6 Run `python3 -m pytest scripts/tests/test_story_context.py`, `python3 scripts/eval-story-context.py`, `bash scripts/eval.sh --check=story-context`, and `bash scripts/eval.sh --check=leanness`; verify all acceptance criteria pass and Tier 1 eval stays green.
- [x] 2.7 Record baseline justification for `scripts/` surface growth (ADR-019 ratchet) in the story's What Was Built summary — moving the hint contract from unmeasured `.writ/docs/` prose into measured `scripts/` is expected growth, not an exemption.

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
- Extended references use backtick-delimited `` `file.md → ## Section → ### Subsection` `` paths with the `→` arrow only (`>>` is not a supported arrow form — see drift-log.md DEV-002).
- Duplicate category lines merge references, deduplicate, and warn once (Interaction Edge Cases).
- Empty brackets `[]` skip the category silently — valid signal, not an error.

## Definition of Done

- [x] All tasks completed
- [x] All acceptance criteria met
- [x] Tests passing
- [x] Code reviewed
- [x] Documentation updated

## Context for Agents

- **Error map rows:** [Read story file, Locate hints section, Parse hint category, Read source spec, Resolve reference, `eval-leanness` calls assembler]
- **Shadow paths:** [Context assembly, Leanness measurement]
- **Business rules:** [One implementation per contract, Determinism is a testable property, Legacy stories never break, Orchestration policy stays in the command]
- **Experience:** [Entry Point, Happy Path, Error Experience, Feedback Model]

---

## What Was Built

**Implementation Date:** 2026-08-03

### Files Created

1. **`scripts/story-context.py`** (~500 lines) — the deterministic context-hint assembler: `assemble --story <path> [--budget-bytes N]`. Parses `## Context for Agents`, resolves bracketed and single-arrow (`→`) extended references against `technical-spec.md`/`spec.md` per the documented 4-category source/fallback table, applies multi-row concatenation for duplicate table-row names (exact match, backticks preserved, table order, deduplicated, no warning), and always exits 0 with a valid JSON payload — never raises, even on invalid UTF-8 or a missing story file.
2. **`scripts/tests/test_story_context.py`** (53 unit tests) — temp-dir `make_spec_tree()` fixtures (no static fixtures directory, matching Story 1's precedent), covering every edge-case-table row, both reference forms × all 4 categories, byte-identical repeat runs, and — added during the review/testing cycle — two path-traversal regression tests and one invalid-UTF-8/internal-error-branch test.
3. **`scripts/eval-story-context.py`** (39-scenario PASS/FAIL emitter) — happy path (both forms, all 4 categories), all documented degradation branches, duplicate-row concatenation, byte-identical repeats, and (added during the fix/test cycle) 3 scenarios covering path-traversal rejection and undecodable-byte handling.

### Files Modified

- **`scripts/eval-leanness.py`** — deleted `resolve_context_hints()` and its category-keyword/extended-ref/heading helpers entirely; `story_context_components()`'s `context_hints` sub-component now calls `assembler_bytes_for_story()`, which subprocess-invokes `story-context.py` (hyphenated filename precludes `import`, mirroring `eval-spec-deps.py` → `spec-deps.py`) and degrades to `0` on any subprocess failure, non-zero exit, or JSON-decode error. Note precisely: only this sub-component became a real measured value — `story_context_bytes` as a whole remains a documented declared-load proxy; deriving/enforcing the full budget from real measurement is Story 3's scope.
- **`scripts/eval.sh`** — added `story-context` to `CHECKS` (after Story 1's `story-deps`) and `check_story_context()`, structurally mirroring `check_story_deps()`. Purely additive against Story 1's already-committed portion (independently verified via `git diff` at every review/test iteration — no interference either direction).
- **`.writ/specs/2026-08-03-deterministic-story-substrate/user-stories/story-2-context-assembler.md`** (this file) — Notes line corrected to drop an inaccurate `>>` arrow claim (only `→` is supported) as a Small-drift auto-amendment.
- **`.writ/specs/2026-08-03-deterministic-story-substrate/drift-log.md`** (new) — records DEV-001 (doc example vs. canonical form) and DEV-002 (the `>>` arrow correction above).

### Implementation Decisions

1. **Single-arrow (`→`) only, not `→`/`>>`** — the story's own Notes claimed both were supported, but AC1 and both canonical docs (`technical-spec.md`, `context-hint-format.md`) only ever show `→`. Traced `>>` to an implementation accident inherited from the pre-existing `eval-leanness.py` regex (`r"[→>]{1,2}"`), not a real contract requirement. Logged as DEV-002; the story's Notes text was corrected.
2. **Canonical single-backtick-span form over `context-hint-format.md`'s stale illustrative example** — that doc's own prescriptive sections and this story's AC1 agree on one backtick span (`` `file.md → ## Section` ``); only one illustrative example elsewhere in the same doc breaks pattern with per-segment backticks. Implemented the majority/authoritative form; logged as DEV-001, deferred to Story 4's doc rewrite.
3. **`resolve_bracket_refs()`'s trailing `return ""`** — confirmed during documentation to be genuinely unreachable dead code (callers only ever pass a label already narrowed to `CATEGORIES`), not a real fallback path. Left in place as a defensive default; documented as such rather than removed, since removing it would require re-proving the narrowing invariant holds at every call site.

### Security Fix (Review Iteration 1 → 2)

**Finding (Major):** `resolve_spec_file()` joined a story-declared filename onto `spec_folder` with no confinement check. A crafted extended reference — `` `../../secret.md → ## Heading` `` (relative traversal) or `` `/etc/passwd → ## Heading` `` (absolute path; `pathlib`'s `/` operator silently discards the left operand when the right is absolute) — could read and leak the **full content** of any file on disk into `fetched_context`. This was a genuine escalation over the code it replaced, which only ever leaked a byte-count.

**Fix:** `resolve_spec_file()` now resolves each candidate and requires `resolved.is_relative_to(spec_folder.resolve())` before accepting it; a rejected candidate returns `None`, indistinguishable from a genuinely-missing file (same warning text, no new branch, no raise) — verified by the reviewer to leave no signal an attacker could use to distinguish "rejected" from "not found."

**Verification chain:** orchestrator independently reproduced the exploit before dispatching the fix → coding agent fixed + added 2 regression tests + 1 scenario → orchestrator independently re-ran the exploit against the fix → review agent independently re-exploited with its own fresh payloads (not reusing existing test strings) → testing agent independently re-attempted with yet another fresh exploit script (relative, absolute, backslash, and mixed `./../../` variants) → orchestrator re-verified the final test/scenario counts directly. Four independent verification passes on the same fix before it was accepted.

### Test Results

**Verification:** Automated (unit tests + eval scenario emitters), independently re-run by review, testing, and the orchestrator at every iteration.
- ✅ 53/53 unit tests (`scripts/tests/test_story_context.py`)
- ✅ 39/39 `eval-story-context.py` scenarios
- ✅ `bash scripts/eval.sh --check=story-context` — 0 findings
- ✅ `bash scripts/eval.sh --check=story-deps` — 16/16, 0 findings (regression check — Story 1's shared `eval.sh` portion unaffected)
- ✅ `bash scripts/eval.sh --check=leanness` — 0 findings (6 non-blocking `scripts`/`commands`/`skills` surface-growth WARNING notes, expected per Task 2.7 below)

**Coverage:** Structural/manual walk (no `coverage` tool installed) — every function and every documented degradation row has direct test coverage; the testing agent additionally found and closed one genuine gap (the CLI's outer catch-all exception branch, which only fires on non-`OSError` failures like `UnicodeDecodeError` from invalid-UTF-8 story content).

**Task 2.7 — ADR-019 baseline justification:** `scripts/` grew ~+950 lines net across the three new/modified files (assembler + tests + scenario emitter + `eval-leanness.py` refactor). This is expected growth per the spec's own Business Rule 8 — moving the hint contract from unmeasured `.writ/docs/` prose into measured, tested `scripts/` code. `.writ/leanness-baseline.json` was not updated with a formal justification entry since the ratchet isn't yet firing a blocking finding (only non-blocking WARNING notes); this justification record in the WWB satisfies Task 2.7's requirement as written.

### Review Outcome

**Result:** PASS (after 1 fix iteration — 2 review iterations total, both counted toward the 3-iteration cap)

- **Iteration 1:** FAIL — one Major security finding (path traversal, above). All 5 ACs, code quality, test coverage, integration, and boundary compliance were already clean at this iteration.
- **Iteration 2:** PASS — security fix independently re-verified with fresh exploit payloads; all other categories confirmed unaffected.
- **Drift:** Small (DEV-001, DEV-002 — both auto-amended, see Implementation Decisions)
- **Security:** Clean (post-fix) — `subprocess.run` uses an argument list, no `shell=True`; path resolution now confined to `spec_folder`
- **Boundary Compliance:** All changes within Owned scope; `eval.sh`/`eval-leanness.py` shared-surface overlap with Story 1 confirmed additive-only at every iteration

### Deviations from Spec

See DEV-001 and DEV-002 in `drift-log.md` — both Small, both auto-amended, neither affects `spec.md`/`spec-lite.md`.

### Lessons Learned

1. **A byte-count side channel and a content-disclosure vulnerability can share identical-looking code** — the pre-existing `eval-leanness.py` had the same unconfined path join as the new `story-context.py`, but returning a length vs. returning the actual text is the difference between negligible and Major severity. Replacing "measure this" code with "return this" code deserves a fresh security pass even when copying an existing pattern.
2. **`pathlib`'s `/` operator silently discards the left operand for absolute right operands** — `Path("/safe") / "/etc/passwd"` is `/etc/passwd`, not an error. This is surprising enough that both the review and testing agents independently constructed absolute-path exploits distinct from the relative-`../`-traversal case, treating them as genuinely separate bypass mechanisms worth independent test coverage.
3. **A story's own Notes section is not infallible** — DEV-002's `>>` arrow claim came from the story file itself, not an implementation guess. Cross-checking Notes against AC text and the canonical docs (rather than implementing Notes literally) caught an inherited inaccuracy before it became a permanent parser feature.

### Next Story

**Story 3:** Derived Context Budget & Real Measurement — measures `fetched_context` bytes across real specs (dogfooding this assembler against the corpus, including the heading-mismatch case the testing agent already flagged on this very story's own `spec.md`), derives a `--budget-bytes` cap from that distribution, and enforces truncation (currently a no-op passthrough in this story).
