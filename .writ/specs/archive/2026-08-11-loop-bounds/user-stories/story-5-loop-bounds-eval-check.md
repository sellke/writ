# Story 5: The loop-bounds Eval Check

> **Status:** Completed
> **Priority:** High
> **Dependencies:** Story 2, Story 3, Story 4

## User Story

**As a** maintainer who just learned that `## Completion` survived in only 13 of 32 commands precisely because nothing ever mandated or checked it
**I want** a check that fails when a loop bound is uncited, illegally valued, or set below a value a real run already reached
**So that** these bounds do not become the next unenforced contract, and so that a mis-calibrated bound cannot ship green past a presence check that only asks whether the keys are there

## Acceptance Criteria

- [x] Given a command file with no `loop:` block, when the check runs, then it skips that file and reports `deferred_to_check3` — `2026-08-11-governor-instrumentation` Check 3 owns presence, this check owns correctness, and the same missing block is never reported twice by two checks.
- [x] Given a `loop:` block exists, when the check runs, then it asserts `unit` and `calibrated_against` are present alongside the two contract-named keys, at the top level and in every `nested` entry; that `max_iterations` is a positive integer literal; that `unit` values are unique within the file; and that `nested` does not itself contain `nested`.
- [x] Given a `loop:` block with an illegal `on_exhaustion`, when the check runs, then it fails naming the file and the value — and when that value is `retry` specifically, the failure message states the reason: retry is a pre-exhaustion state already governed by `scripts/phase-state.py`'s `attempts < 2` guard.
- [x] Given `on_exhaustion: quarantine`, when the check runs, then it is accepted only on a unit with a `phase-execution-*.json` record and rejected on `implement-story`, `refactor`, and `verify-spec`.
- [x] Given `.writ/state/` contains recorded runs, when the check runs, then it compares `implement-phase`'s `spec` bound against `len(specOrder)` in every `phase-execution-*.json`, and `implement-spec`'s `story` bound against `len(stories)` in every `execution-*.json` and `stories_total` in every `phase*result*.json` — failing with the file and value if any declared bound is lower.
- [x] Given `.writ/state/` contains no run files (a fresh clone or CI, since `.writ/state/` is gitignored), when the check runs, then the historical-run assertion reports `skipped` with an explicit reason in the check's output rather than passing silently.
- [x] Given `implement-phase`'s nested `spec_attempt` bound, when the check runs, then it compares that number against the `attempts < 2` guard read from `scripts/phase-state.py` itself, not against a constant hardcoded in the check — so the two cannot drift apart.
- [x] Given `commands/refactor.md`, when the check runs, then it asserts `calibrated_against` contains the literal `no recorded run`, so the weak evidence cannot be replaced with a confident-looking citation without an explicit edit.
- [x] Given `bash scripts/eval.sh --check=loop-bounds`, when it is invoked, then it runs this check and follows the same one-JSON-object contract and reporting shape as the existing `eval-*.py` scripts, and `bash scripts/eval.sh` full Tier 1 continues to exit 0 with 0 findings.
- [x] Given the blocking-`structural` finding machinery from roadmap Phase 10's "Make the governor bite" feature has not landed yet, when the check runs, then it degrades to a non-blocking report rather than failing to run or asserting a classification that does not exist.

## Implementation Tasks

- [x] 5.1 Read `2026-08-11-governor-instrumentation`'s Check 3 before writing any code and confirm the presence/correctness boundary still holds; if that spec has broadened Check 3, resolve the overlap explicitly rather than shipping two checks that both report a missing `loop:` block
- [x] 5.2 Write tests for all eight assertions against fixture command files, using the malformation fixture set produced by Story 1: missing `unit`/`calibrated_against`, `on_exhaustion: retry`, out-of-set `on_exhaustion`, non-integer `max_iterations`, duplicate `unit`, `nested` inside `nested`, `loop:` present but not a mapping — plus the no-`loop:`-block case asserting `deferred_to_check3` rather than a finding
- [x] 5.3 Write tests for the historical-run assertion: a fixture `.writ/state/` containing a run larger than a declared bound must fail with the file and value named; an empty fixture state dir must report `skipped` with a reason
- [x] 5.4 Implement `scripts/eval-loop-bounds.py` with assertions 1–6 (key completeness, integer type, enum membership, citation containing a path token or the literal `no recorded run`, `unit` uniqueness and one-level `nested` cap, `quarantine` legality) and the `deferred_to_check3` skip path
- [x] 5.5 Implement assertion 7, the historical-run regression check, reading `.writ/state/phase-execution-*.json`, `execution-*.json`, and `phase*result*.json` — with the explicit `skipped` path when no state files exist
- [x] 5.6 Implement assertion 8's transcription cross-reads: `scripts/phase-state.py`'s `attempts < 2` guard against the declared `spec_attempt` bound; `implement-story.md:595`/`:732` and `agents/*-agent.md`'s `MAX_SELF_FIX_ITERATIONS` against `implement-story`'s three numbers; the grep guard asserting `commands/verify-spec.md` still has no re-check step; the literal `no recorded run` in `refactor`'s citation. Hardcode none of these values
- [x] 5.7 Wire `--check=loop-bounds` into `scripts/eval.sh`'s check registry following the existing pattern, and document in the check's docstring that its named-command list is the enforcement point when a sixth command acquires a loop
- [x] 5.8 Verify acceptance criteria are met and all tests pass, including graceful degradation when the `structural` classification machinery is absent, and confirm `bash scripts/eval.sh` full Tier 1 still exits 0 with 0 findings and no new unjustified-growth warnings

## Notes

**Technical considerations:**

- **Assertions 7 and 8 are why this check exists.** `2026-08-11-governor-instrumentation` Check 3 asks whether the two contract-named keys are present. That is necessary and not sufficient: presence checking alone would let a bound of 1 ship green on a command whose recorded runs reached 4 — the failure the locked contract names as hardest. If assertion 7 proves impractical, that is a spec-level problem to surface, not a task to quietly drop.
- **Do not duplicate Check 3.** A file with no `loop:` block is Check 3's finding, not this check's. Reporting it twice trains a maintainer to skim the check registry, which is how an enforced contract decays back into an unenforced one.
- **`.writ/state/` is gitignored.** Assertion 7 therefore binds on a maintainer's working copy, where the history exists, and skips in CI, where it does not. A check that silently passes because its input is absent is exactly the failure mode ADR-020 diagnosed for `## Completion` — so the skip must be *reported*, with its reason, in the check's own output.
- **Prefer cross-reads over hardcoded constants everywhere.** Assertion 8's whole value is that it catches drift in either direction. A check that hardcodes 2 for `spec_attempt` would pass while `phase-state.py` changed underneath it, which is worse than no check.
- The existing `eval-*.py` scripts print one JSON object and always exit 0, with `eval.sh` owning the findings aggregation. Follow that contract; do not invent a second reporting convention.

**Risks / challenges:**

- **Scope creep into `2026-08-11-governor-instrumentation`.** That spec owns Check 3 (loop-bound presence), the blocking-`structural` classification, the `check_length` 2000 → 400 change, and the absolute `per_surface` byte cap. This story contributes only the correctness assertions and must work with or without that spec having landed. The last acceptance criterion is the boundary; do not implement the classification machinery or a second presence check here.
- **A false-failing check is worse than a missing one.** If assertion 7 misparses a state file shape it has not seen, it will fail a correct repo and train the maintainer to ignore it. Handle unknown or malformed state-file shapes as `skipped` with a reason, never as a finding.
- The command list is hardcoded to five. A sixth looping command will not be caught. That is accepted and documented rather than solved by heuristic loop detection, which would produce false positives across 32 prose files.

**Integration points:**

- Depends on Stories 2, 3, and 4 for the declared bounds it checks — it has nothing to assert until all five files carry `loop:` blocks.
- Consumes Story 1's fixture set directly; the schema doc and the fixtures should correspond one-for-one so this story invents no rules.
- Reads `scripts/phase-state.py`, `commands/implement-story.md`, `agents/coding-agent.md`, `agents/testing-agent.md`, and `commands/verify-spec.md` for cross-read assertions; modifies none of them.
- Adds `scripts/eval-loop-bounds.py` and one registry entry in `scripts/eval.sh`.

**Implementation record (2026-08-11):**

- **Task 5.1: the presence/correctness boundary was re-read and still holds.** `2026-08-11-governor-instrumentation` is still `pending` and its Check 3 (`spec.md:161-165`, `sub-specs/technical-spec.md:146-162`) still asserts presence only, still names the same five commands, still expects 10 findings, and still explicitly defers field shape to this spec. Its own story 5 notes even anticipate this split by name. No overlap to resolve — `scripts/eval-loop-bounds.py` skips a file with no `loop:` block as `deferred_to_check3`, and `check_loop_bounds()` in `eval.sh` carries a comment stating that the absent `require_literal 'loop:'` is absent *on purpose*.
- **Reporting convention: PASS/FAIL/SKIP TSV, matching the 20+ sibling scenario emitters.** The story's notes describe the existing contract as "one JSON object"; that is true of `eval-leanness.py` alone. Every scenario emitter — `eval-artifact-integrity.py`, `eval-story-deps.py`, `eval-revert-resolve.py` and the rest — prints TSV that `eval.sh` reads with `while IFS=$'\t' read -r status name reason`. Following the dominant convention is what "do not invent a second reporting convention" asks for; inventing JSON here would have been the second convention.
- **`SKIP` was added as a third TSV verb** because `eval.sh`'s existing reader recognises only `PASS`/`FAIL` and would have silently dropped a skip line — reproducing the exact silent-pass failure this check exists to prevent. `check_loop_bounds` routes `SKIP` to the existing `add_note` mechanism, so skips appear in the report as non-blocking notes even when the check passes.
- **Two scenarios skip routinely today and both are reported.** `historical-run-regression` skips when `.writ/state/` is empty (gitignored, so always in CI) with a reason that says the bounds were *not* compared. `governor-boundary-intact` skips because Check 3 has not landed, and states that presence is therefore currently unchecked and that this check is deliberately not filling the gap — which is also how the last acceptance criterion (degrade rather than assert a `structural` classification that does not exist) is satisfied.
- **No expected value is hardcoded.** `spec_attempt` is compared against the integer parsed out of `scripts/phase-state.py`'s own `attempts < N` guard; `review_cycle` and `testing_cycle` against integers parsed out of `implement-story.md`'s prose caps; `agent_self_fix` against `MAX_SELF_FIX_ITERATIONS` read from **both** agent files, with a separate finding if the two disagree. Cross-reads read the command **body with frontmatter stripped**, so a declaration can never validate itself.
- **The `verify-spec` re-check guard reads structure, not prose.** A naive grep would fire on the bound's own citation, which says the words "re-check", "re-run", and "re-verify" while asserting their absence. The guard inspects heading and numbered-step lines only, so a described absence cannot trip it while an added `#### 4.5: Re-check After Fixes` does.
- **A minimal YAML-subset parser was written rather than taking a dependency.** PyYAML is not available and Writ ships with none. The parser is deliberately strict about scalar shape: an integer is returned only for a bare, unquoted, all-digit token, so `"twelve"`, `3-5`, and `null` arrive as strings and fail the positive-integer assertion instead of being coerced into passing.
- **Verified by making it fail, eight ways.** Lowering `implement-spec`'s bound to 2 with the real state files present -> `historical-run-regression` names the file and the recorded 4. Drifting `review_cycle` to 4 -> `drift-review-cycle`. Changing `phase-state.py`'s guard to `attempts < 3` -> `drift-spec-attempt` (proving the 2 is not hardcoded). Removing the `no recorded run` literal -> `refactor-no-recorded-run-literal`. Appending a `#### 4.5: Re-check After Fixes` heading -> `verify-spec-no-recheck-step`. Setting `on_exhaustion: retry` -> rejected by name with the reason. Deleting a named command file -> a finding naming the absent file, not a crash. Deleting a whole `loop:` block -> `SKIP ... deferred_to_check3`, not a finding. Every mutation was reverted.
- **Assertion 7 was run against the real recorded history**, by copying the maintainer working copy's `.writ/state/*.json` into the lane: observed maxima are `spec=5`, `story=4`. Every shipped bound clears them (`spec` 12 > 5, `story` 12 > 4, `spec_attempt` 2 = the enforced guard, `review_cycle` 3 > the archived maximum of 2). **No declared bound would have failed any recorded run.** The copies were removed afterwards.
- **Measured cost:** `scripts/eval-loop-bounds.py` 733 lines (36 scenarios) plus 50 lines of `scripts/eval.sh` wiring. `bash scripts/eval.sh` full Tier 1: **Findings 0, Run errors 0**, exit 0, with the same six pre-existing non-blocking leanness growth warnings as the pre-change baseline — no new warning category.

## Definition of Done

- [x] All tasks completed
- [x] All acceptance criteria met
- [x] Tests passing
- [x] Code reviewed
- [x] Documentation updated

## Context for Agents

- **Business rules:** [Rule 2 (no bound below the highest observed historical value — mechanized as assertion 7, this story's reason to exist), Rule 1 (every bound cites the run it was calibrated against — mechanized as assertion 5), Rule 4 (`retry` is not a legal `on_exhaustion` value — mechanized as assertion 4), Rule 7 (transcribed numbers must equal their sources — mechanized as assertion 8), Rule 8 (thin evidence stated in-file — mechanized as the `no recorded run` literal assertion)] — from spec.md → 📋 Business Rules
- **Detailed requirements:** [The `loop:` frontmatter block and its key contract; The `on_exhaustion` vocabulary's three-value closed set] — from spec.md → ## Detailed Requirements
- **Error map rows:** [Declared bound below recorded history → finding with file and value, corrected not exempted; `.writ/state/` empty → explicit `skipped`, never a silent pass; `quarantine` on a command with no phase-state integration → rejected by schema; malformed frontmatter → blocking finding naming file and key] — from sub-specs/technical-spec.md → Error & Rescue Map
- **Contract:** ["a bound set too low turns a working loop into a spurious failure. Bounds must be calibrated against observed real runs"] — from spec.md → ## Contract (Locked); Out of Scope → presence checking belongs to `2026-08-11-governor-instrumentation` Check 3 and the generic `structural` machinery to that same spec, not to this one
