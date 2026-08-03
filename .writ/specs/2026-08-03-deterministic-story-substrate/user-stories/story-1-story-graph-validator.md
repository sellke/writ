# Story 1: Story Graph Validator with Blocking Pre-Execution Gate

> **Status:** Completed ✅ (2026-08-03)
> **Priority:** High
> **Dependencies:** None

## User Story

**As a** Writ maintainer
**I want to** validate the user-story dependency graph with a deterministic program before `/implement-spec` computes parallel worktree batches
**So that** invalid metadata stops execution with a named diagnostic instead of spawning concurrent worktrees against unsatisfied dependencies

## Acceptance Criteria

- [x] Given a spec whose story files declare a valid dependency DAG, when `scripts/story-deps.py validate --spec-dir <path>` runs, then it exits 0 with `"status": "ok"` and emits topologically ordered batches with a numeric story-number tie-break that is byte-identical across repeated runs on an unchanged tree.
- [x] Given a story graph containing any of the five blocking error classes (`malformed_dependencies`, `missing_reference`, `self_reference`, `duplicate_reference`, `dependency_cycle`), when the validator runs, then it prints a `blocker` envelope naming the code and a summary that identifies the affected story (including the full cycle path for cycles) and **exits 1** — matching `spec-deps.py`'s `ContractError`/`_fail` contract at lines 50–52, verified by fixtures for all five classes.
- [x] Given `/implement-spec` is invoked on a spec with an invalid story graph, when Phase 2 begins, then execution stops before Step 2.2 batch computation with the exact blocking language mirroring `implement-phase.md`: invalid explicit metadata is blocking; do not guess an order around invalid metadata.
- [x] Given `/implement-spec` is invoked on a spec with a valid story graph, when the blocking gate passes, then the execution plan shows deterministic batches derived from the script output rather than agent-interpreted DAG inspection.
- [x] Given `scripts/recommend-state.py` calls story-dependency validation, when `validate_dag()` runs, then it imports the shared module from `scripts/story-deps.py` and the duplicate cycle/missing-reference implementation in `recommend-state.py` lines 376–394 does not survive this story.

## Implementation Tasks

- [x] 1.1 Write failing unit tests in `scripts/tests/test_story_deps.py` covering all five error classes, absent `Dependencies` headers (legacy `None`), deterministic batch ordering, byte-identical repeat runs, and fixtures under `scripts/tests/fixtures/` following the `eval-spec-deps.py` layout.
- [x] 1.2 Implement `scripts/story-deps.py` with `validate --spec-dir <path>`, reusing `spec-deps.py`'s `ContractError`/`_fail` shape — success prints `{"schema", "status", "batches", "graph"}` and exits 0; a violation prints a `blocker` envelope and exits 1. Parse `> **Dependencies:**` via the proven regex from `recommend-state.py` lines 363–366.
- [x] 1.3 Refactor `scripts/recommend-state.py` `validate_dag()` to import and call the shared `story-deps.py` module, removing the duplicate DFS implementation at lines 376–394.
- [x] 1.4 Create `scripts/eval-story-deps.py` as a scenario emitter following the `eval-spec-deps.py` PASS/FAIL TSV convention, exercising happy path, legacy absent headers, all five blocking classes, and deterministic batch output.
- [x] 1.5 Register `story-deps` in the `CHECKS` array in `scripts/eval.sh` lines 19–47 and implement `check_story_deps()` that runs `eval-story-deps.py` scenarios plus literal checks on `commands/implement-spec.md` for the blocking gate language.
- [x] 1.6 Wire the blocking pre-execution gate into `commands/implement-spec.md` before Step 2.2 (after Step 2.1 graph description), instructing the agent to run `scripts/story-deps.py validate --spec-dir <spec-folder>` and stop on invalid graphs — matching the posture at `implement-phase.md` lines 132–134.
- [x] 1.7 Run `python3 -m pytest scripts/tests/test_story_deps.py`, `python3 scripts/eval-story-deps.py`, and `bash scripts/eval.sh --check=story-deps`; verify all acceptance criteria against fixtures and the updated command file.

## Notes

**Central safety rule:** Graph validity **blocks**; context assembly **degrades**. This story enforces only the blocking half. A wrong story graph corrupts parallel worktree execution order and must halt `/implement-spec` before batch computation. Thin or missing context (Story 2's domain) never halts a story.

**Exit contract:** non-zero on an invalid graph, reusing `spec-deps.py`'s `ContractError`/`_fail` shape verbatim. Do not adopt `eval-leanness.py`'s always-exit-0 pattern here — that exists for a *reporting* check where `eval.sh` decides severity. This is a *blocking* validator, and a hard exit is what makes the documented invocation difficult to ignore silently. The sibling assembler in Story 2 deliberately does the opposite; the divergence encodes the blocks-versus-degrades rule in the exit codes themselves.

**Flag naming:** `--spec-dir` (one spec folder) is intentionally distinct from `spec-deps.py`'s `--specs-dir` (the `.writ/specs/` root). The near-collision is deliberate — do not "fix" it.

**Integration points:**

- `commands/implement-spec.md` Phase 2 — blocking gate before Step 2.2 parallel batch computation; Step 2.3b pre-flight remains advisory.
- `scripts/recommend-state.py` — `--recommend` eval fixtures currently reach the dormant `validate_dag()`; consolidation ensures one parser survives.
- `scripts/eval.sh` — new `story-deps` check in Tier 1 CI alongside existing `spec-dependencies`.

**Risks:**

- Agent could skip the documented script invocation (same weakness as `spec-deps.py` in `implement-phase.md` — accepted per spec Technical Concerns).
- `--from story-N` pruning must validate the **full** graph first, then prune (Interaction Edge Cases).
- Story marked Complete inside a cycle is still reported — completion does not repair invalid metadata.

## Definition of Done

- [x] All tasks completed
- [x] All acceptance criteria met
- [x] Tests passing
- [x] Code reviewed
- [x] Documentation updated

## Context for Agents

- **Error map rows:** [Read story file, Parse `Dependencies` header, Resolve dependency target, Topological sort, Invoke validator from `/implement-spec`]
- **Shadow paths:** [Story graph validation]
- **Business rules:** [Graph validity is blocking; context assembly is degrading, One implementation per contract, Error classes match the cross-spec validator exactly, Determinism is a testable property]
- **Experience:** [Entry Point, Happy Path, Error Experience, Feedback Model]

---

## What Was Built

**Implementation Date:** 2026-08-03

### Files Created

1. **`scripts/story-deps.py`** (~220 lines)
   - Executable `validate --spec-dir <path>` story-graph validator mirroring `spec-deps.py`'s `ContractError`/`_fail` JSON-envelope contract (no `--json` flag, matching the precedent's always-JSON output).
   - Detects all five blocking classes (`malformed_dependencies`, `missing_reference`, `self_reference`, `duplicate_reference`, `dependency_cycle`) plus `no_stories_found`; emits deterministic topological batches with a **numeric** (not lexicographic) story-number tie-break, proven against an 11-story fixture.
   - Exposes `validate_graph()` as a reusable function over an already-parsed graph so `recommend-state.py` never re-reads files from disk.
2. **`scripts/tests/test_story_deps.py`** (38 unit tests)
   - Covers all 5 error classes, legacy/absent headers, `None` case-insensitivity, numeric tie-break (flat and within a dependent batch), byte-identical repeat runs, and 3 additional error branches (unparseable story id, non-numeric story filename, duplicate story-number collision) found and closed during independent testing.
3. **`scripts/eval-story-deps.py`** (16-scenario PASS/FAIL emitter)
   - Mirrors `eval-spec-deps.py`'s TSV convention; exercises the CLI as a real subprocess against disposable temp-directory fixtures.

### Files Modified

- **`scripts/recommend-state.py`** — `validate_dag()` now lazily imports `story-deps.py` via `importlib.util` (following `test_revert_resolve.py`'s hyphenated-module recipe) and translates the imported module's `ContractError` into `recommend-state.py`'s own `ContractError` class, so the 4 existing `except ContractError` call sites continue to catch correctly. The old duplicate DFS implementation (lines 376–394) is gone. Import is lazy, not module-level, so standalone installs shipping only `recommend-state.py` are unaffected.
- **`scripts/eval.sh`** — added `story-deps` to the `CHECKS` array (immediately after `spec-dependencies`, positioned so Story 2's later `story-context` entry lands cleanly) and `check_story_deps()`; fixed a stale fixture assertion in `check_recommended_spec_implementation` (`package-dag` scenario: `invalid_dag` → `dependency_cycle`, since the delegated validator now returns the objectively correct code for that fixture's mutual two-story cycle).
- **`commands/implement-spec.md`** — Step 2.1/2.2 rewritten: Step 2.1 is now a blocking gate that runs the script and distinguishes a named blocker ("Invalid explicit metadata is blocking... Do not guess an order around invalid metadata," mirrored verbatim from `implement-phase.md`) from a missing/crashed script ("cannot verify story graph"); Step 2.2 consumes the script's `batches` array directly instead of an agent-computed ASCII diagram.
- **`README.md`** — `/implement-spec` command-table entry now names the blocking validation gate.

### Implementation Decisions

1. **Lazy import in `recommend-state.py`** — a module-level import broke standalone installs shipping only `recommend-state.py`; deferred to first call of `validate_dag()`.
2. **Widened dependency-value grammar beyond a strict `Story N` token** — dogfooding against all 39 real specs in `.writ/specs/` initially blocked 22 on legitimate prose forms (`Stories 1, 2, 3`, `Story 1 (annotation)`, `Stories 1–3`, `None (annotation)`, `Stories 1 and 2`). Widened without weakening `malformed_dependencies` detection for genuine typos (`Story ???` still fails closed — directly tested). Review classified this as a Small, non-contract-affecting implementation detail; no spec amendment needed.
3. **CHANGELOG entry deferred** — this repo's CHANGELOG batches entries per spec/release (cut at `/release`), not per individual story. With Stories 2–4 still pending, no entry was added; documentation agent confirmed this against the `[0.24.0]` precedent.

### Test Results

**Verification:** Automated (unit tests + eval scenario emitters), independently re-run by both review and testing agents, plus my own verification pass.
- ✅ 38/38 unit tests (`scripts/tests/test_story_deps.py`)
- ✅ 16/16 eval-story-deps.py scenarios
- ✅ `bash scripts/eval.sh --check=story-deps` — 0 findings
- ✅ `bash scripts/eval.sh --check=recommended-spec-implementation` — 162/162 scenarios, 16/16 static assertions, 0 findings (regression suite for the `recommend-state.py` refactor, run before and after)

**Coverage:** Structural/manual walk (no `coverage` tool installed in this environment) — every function in `story-deps.py` has direct test coverage on both happy and error paths; two genuinely-unreachable defensive branches documented and excluded.

### Review Outcome

**Result:** PASS

- **Iteration count:** 1 iteration
- **Drift:** None (two implementation-detail deviations assessed by review and found non-contract-affecting; no amendment warranted)
- **Security:** Clean — no shell/eval/string-built subprocess calls, typed path arguments, no secrets
- **Boundary Compliance:** All changes within Owned scope; readable precedent files confirmed unmodified via `git diff --stat`; BOUNDARY_DEVIATION: None, BOUNDARY_VIOLATION: None

### Deviations from Spec

None (see Implementation Decisions above for two implementation-detail choices explicitly reviewed and found non-contract-affecting).

### Lessons Learned

1. **Real-corpus dogfooding surfaces grammar gaps a minimal spec can't anticipate** — 22 of 39 real specs used legitimate prose forms the strict `Story N` grammar didn't parse. Running the validator against the actual `.writ/specs/` corpus during implementation (not just synthetic fixtures) caught this before it would have blocked real maintainer workflows.
2. **Exception-class identity across module boundaries is a silent trap** — two same-named `ContractError` classes in different modules do not satisfy each other's `except` blocks. Caught at architecture-check time via static reading, not discovered at runtime.
3. **A follow-up worth tracking (not blocking):** `recommend-state.py`'s `count_story_contract()` still parses `Dependencies:` with its own narrower regex, separate from `story-deps.py`'s richer parser — flagged by review as mild tension with "one implementation per contract" at the whole-spec level, deferred rather than expanded into this story's scope.

### Next Story

**Story 2:** Deterministic Context Assembler — `scripts/story-context.py`, the single context-hint implementation, byte-budgeted (budget enforcement itself is Story 3).
