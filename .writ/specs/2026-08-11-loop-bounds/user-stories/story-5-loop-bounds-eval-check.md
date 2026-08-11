# Story 5: The loop-bounds Eval Check

> **Status:** Not Started
> **Priority:** High
> **Dependencies:** Story 2, Story 3, Story 4

## User Story

**As a** maintainer who just learned that `## Completion` survived in only 13 of 32 commands precisely because nothing ever mandated or checked it
**I want** a check that fails when a loop bound is uncited, illegally valued, or set below a value a real run already reached
**So that** these bounds do not become the next unenforced contract, and so that a mis-calibrated bound cannot ship green past a presence check that only asks whether the keys are there

## Acceptance Criteria

- [ ] Given a command file with no `loop:` block, when the check runs, then it skips that file and reports `deferred_to_check3` — `2026-08-11-governor-instrumentation` Check 3 owns presence, this check owns correctness, and the same missing block is never reported twice by two checks.
- [ ] Given a `loop:` block exists, when the check runs, then it asserts `unit` and `calibrated_against` are present alongside the two contract-named keys, at the top level and in every `nested` entry; that `max_iterations` is a positive integer literal; that `unit` values are unique within the file; and that `nested` does not itself contain `nested`.
- [ ] Given a `loop:` block with an illegal `on_exhaustion`, when the check runs, then it fails naming the file and the value — and when that value is `retry` specifically, the failure message states the reason: retry is a pre-exhaustion state already governed by `scripts/phase-state.py`'s `attempts < 2` guard.
- [ ] Given `on_exhaustion: quarantine`, when the check runs, then it is accepted only on a unit with a `phase-execution-*.json` record and rejected on `implement-story`, `refactor`, and `verify-spec`.
- [ ] Given `.writ/state/` contains recorded runs, when the check runs, then it compares `implement-phase`'s `spec` bound against `len(specOrder)` in every `phase-execution-*.json`, and `implement-spec`'s `story` bound against `len(stories)` in every `execution-*.json` and `stories_total` in every `phase*result*.json` — failing with the file and value if any declared bound is lower.
- [ ] Given `.writ/state/` contains no run files (a fresh clone or CI, since `.writ/state/` is gitignored), when the check runs, then the historical-run assertion reports `skipped` with an explicit reason in the check's output rather than passing silently.
- [ ] Given `implement-phase`'s nested `spec_attempt` bound, when the check runs, then it compares that number against the `attempts < 2` guard read from `scripts/phase-state.py` itself, not against a constant hardcoded in the check — so the two cannot drift apart.
- [ ] Given `commands/refactor.md`, when the check runs, then it asserts `calibrated_against` contains the literal `no recorded run`, so the weak evidence cannot be replaced with a confident-looking citation without an explicit edit.
- [ ] Given `bash scripts/eval.sh --check=loop-bounds`, when it is invoked, then it runs this check and follows the same one-JSON-object contract and reporting shape as the existing `eval-*.py` scripts, and `bash scripts/eval.sh` full Tier 1 continues to exit 0 with 0 findings.
- [ ] Given the blocking-`structural` finding machinery from roadmap Phase 10's "Make the governor bite" feature has not landed yet, when the check runs, then it degrades to a non-blocking report rather than failing to run or asserting a classification that does not exist.

## Implementation Tasks

- [ ] 5.1 Read `2026-08-11-governor-instrumentation`'s Check 3 before writing any code and confirm the presence/correctness boundary still holds; if that spec has broadened Check 3, resolve the overlap explicitly rather than shipping two checks that both report a missing `loop:` block
- [ ] 5.2 Write tests for all eight assertions against fixture command files, using the malformation fixture set produced by Story 1: missing `unit`/`calibrated_against`, `on_exhaustion: retry`, out-of-set `on_exhaustion`, non-integer `max_iterations`, duplicate `unit`, `nested` inside `nested`, `loop:` present but not a mapping — plus the no-`loop:`-block case asserting `deferred_to_check3` rather than a finding
- [ ] 5.3 Write tests for the historical-run assertion: a fixture `.writ/state/` containing a run larger than a declared bound must fail with the file and value named; an empty fixture state dir must report `skipped` with a reason
- [ ] 5.4 Implement `scripts/eval-loop-bounds.py` with assertions 1–6 (key completeness, integer type, enum membership, citation containing a path token or the literal `no recorded run`, `unit` uniqueness and one-level `nested` cap, `quarantine` legality) and the `deferred_to_check3` skip path
- [ ] 5.5 Implement assertion 7, the historical-run regression check, reading `.writ/state/phase-execution-*.json`, `execution-*.json`, and `phase*result*.json` — with the explicit `skipped` path when no state files exist
- [ ] 5.6 Implement assertion 8's transcription cross-reads: `scripts/phase-state.py`'s `attempts < 2` guard against the declared `spec_attempt` bound; `implement-story.md:595`/`:732` and `agents/*-agent.md`'s `MAX_SELF_FIX_ITERATIONS` against `implement-story`'s three numbers; the grep guard asserting `commands/verify-spec.md` still has no re-check step; the literal `no recorded run` in `refactor`'s citation. Hardcode none of these values
- [ ] 5.7 Wire `--check=loop-bounds` into `scripts/eval.sh`'s check registry following the existing pattern, and document in the check's docstring that its named-command list is the enforcement point when a sixth command acquires a loop
- [ ] 5.8 Verify acceptance criteria are met and all tests pass, including graceful degradation when the `structural` classification machinery is absent, and confirm `bash scripts/eval.sh` full Tier 1 still exits 0 with 0 findings and no new unjustified-growth warnings

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

## Definition of Done

- [ ] All tasks completed
- [ ] All acceptance criteria met
- [ ] Tests passing
- [ ] Code reviewed
- [ ] Documentation updated

## Context for Agents

- **Business rules:** [Rule 2 (no bound below the highest observed historical value — mechanized as assertion 7, this story's reason to exist), Rule 1 (every bound cites the run it was calibrated against — mechanized as assertion 5), Rule 4 (`retry` is not a legal `on_exhaustion` value — mechanized as assertion 4), Rule 7 (transcribed numbers must equal their sources — mechanized as assertion 8), Rule 8 (thin evidence stated in-file — mechanized as the `no recorded run` literal assertion)] — from spec.md → 📋 Business Rules
- **Detailed requirements:** [The `loop:` frontmatter block and its key contract; The `on_exhaustion` vocabulary's three-value closed set] — from spec.md → ## Detailed Requirements
- **Error map rows:** [Declared bound below recorded history → finding with file and value, corrected not exempted; `.writ/state/` empty → explicit `skipped`, never a silent pass; `quarantine` on a command with no phase-state integration → rejected by schema; malformed frontmatter → blocking finding naming file and key] — from sub-specs/technical-spec.md → Error & Rescue Map
- **Contract:** ["a bound set too low turns a working loop into a spurious failure. Bounds must be calibrated against observed real runs"] — from spec.md → ## Contract (Locked); Out of Scope → presence checking belongs to `2026-08-11-governor-instrumentation` Check 3 and the generic `structural` machinery to that same spec, not to this one
