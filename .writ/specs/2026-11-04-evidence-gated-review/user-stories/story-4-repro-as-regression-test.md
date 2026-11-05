# Story 4: Confirmed repros become regression tests

> **Status:** Completed ✅ (2026-11-04)
> **Priority:** High
> **Dependencies:** Story 3

## User Story

**As a** developer running `/implement-story`
**I want to** a confirmed repro saved to a manifest and checked on re-review
**So that** a recode cannot silently drop or weaken the test that proved a finding real

## Acceptance Criteria

> **AC IDs assigned through:** AC-4.5

- [x] Given a `test` repro that the recorded run shows failing, when `evidence` runs with `--manifest-out`, then it writes an `evidence-manifest-v1` file atomically, with one entry per confirmed `test` repro holding finding key, path, normalized SHA-256, kind, and location. If the write fails, it adds `reason: manifest_write_failed` and leaves line 1 unchanged. `[AC-4.1]`
- [x] Given a manifest repro whose path is missing from `--changed`, or whose normalized SHA-256 differs from the file on disk, when `evidence --prior` runs on any agent verdict (PASS, PAUSE, or FAIL), then line 1 is `fail` with `reason: repro_removed <path>` or `reason: repro_modified <path>`. On a FAIL verdict, new findings are evaluated after those checks. On PASS or PAUSE, only the prior checks run. CRLF endings, trailing whitespace, and the final newline alone do not count as a change. `[AC-4.2]`
- [x] Given a manifest repro that is in `--changed` and unmodified, when `evidence --prior` runs against a recorded run that does not contain the repro's path or has no `exit code: 0` line, then line 1 is `fail` with `reason: repro_still_failing <path>`. When the recorded run names the path and exits 0, no reason line prints for it. `[AC-4.3]`
- [x] Given a `--prior` manifest that is missing, unreadable, or not `evidence-manifest-v1`, when `evidence --prior` runs, then line 1 is `unverifiable` with `reason: bad_manifest`, the exit code is 0, and the agent verdict stands. `[AC-4.4]`
- [x] Given a Gate 3 FAIL with a confirmed `test` repro, when Gate 3 builds the recode brief, then the brief adds an `## Evidence repros` section with the finding, path, exact fenced content, and a no-edit instruction. On re-review, the recorded test run includes every manifest path. `[AC-4.5]`

## Implementation Tasks

- [x] 4.1 Write failing pytest cases for the manifest write in `scripts/tests/test_review_override.py`: entry shape, normalized-hash equivalence (CRLF, trailing whitespace, extra final newlines), merge with an existing manifest (earlier entries kept, same path replaced, no new confirmations leaves the file unchanged), and an unwritable manifest path. Append them above the `__main__` block under a comment naming `2026-11-04-evidence-gated-review`, and cite each test's ID in its docstring `[AC-4.1, AC-4.2]`
- [x] 4.2 Write failing pytest cases for `--prior` in the same class: removed path, modified hash, still failing, passing, and missing or wrong-schema manifest `[AC-4.2, AC-4.3, AC-4.4]`
- [x] 4.3 Write failing wiring assertions in `scripts/tests/test_evidence_gate_wiring.py` (created by Story 3; name the spec in its docstring): the recode brief in `commands/implement-story.md` carries `## Evidence repros` with the no-edit instruction, and the re-review's recorded test command includes each manifest path `[AC-4.5]`
- [x] 4.4 Implement the manifest write in `scripts/review-override.py` `evidence`: one normalization helper shared by the write and the `--prior` compare, an atomic write copied from `_write_json_atomic` in `scripts/review-panel.py` (copy, do not import), and the `--manifest-out` path. Run the 4.1 cases to green `[AC-4.1, AC-4.2]`
- [x] 4.5 Implement `--prior` in `scripts/review-override.py`: `repro_removed`, `repro_modified`, `repro_still_failing`, and `bad_manifest`, run before new findings are evaluated. Read the recorded output and file bytes only: no repro run, no git write. Run the 4.2 cases to green `[AC-4.2, AC-4.3, AC-4.4]`
- [x] 4.6 Edit `commands/implement-story.md`. Add the `## Evidence repros` section to the recode brief written at Gate 3. Add the manifest paths to the re-review's recorded test command. When a manifest exists, run `evidence --prior` on every agent verdict (spec.md Gate 3 decision row 3a). Record `wc -c` before and after the edit. Run `python3 scripts/gen-platform-trees.py`. Run the 4.3 cases to green `[AC-4.5]`
- [x] 4.7 Verify, one run at a time: pytest on Python 3.9 for `scripts/tests/test_review_override.py` and `scripts/tests/test_evidence_gate_wiring.py`, the same on Python 3.14, `python3 scripts/gen-platform-trees.py --check`, then `bash scripts/eval.sh`. Never run pytest alongside eval.sh `[AC-4.1, AC-4.2, AC-4.3, AC-4.4, AC-4.5]`

## Notes

**Codebase facts (verify at implementation)**
- `evidence` does not exist yet. Story 2 adds it to `scripts/review-override.py`, which today has `check`, `switch`, and `safety-fact`. Confirm Story 2 declares `--manifest-out` and `--prior`. If not, add them here.
- Reuse, do not import: `_emit` (line 93), `_inside` (line 328), `_read_text` (line 353) in `review-override.py`; `_write_json_atomic` (line 553) in `review-panel.py`.
- Check shape: line 1 `pass`, `fail`, or `unverifiable`; `reason:` lines; summary last; exit 0, 1, or 2 (`.writ/docs/agent-cli-contract.md`, check shape).
- Normalization on both sides: CRLF to LF, strip trailing whitespace per line, exactly one final newline. One helper serves the write and the compare.
- `--prior` reads the recorded output and file bytes. It runs no repro.
- Python 3.9 floor: stdlib only, `from __future__ import annotations`, no `match` statements.
- Test citations: an AC token counts only after a spec name appears above it in the same file (`.writ/docs/acceptance-criteria-ids.md`, Scan Bounds). Name the spec above the new tests.
- Run pytest alone. Concurrent writes under `.writ/state/` break the smoke and app-verify tests (`CLAUDE.md`).

**Byte budget**
- `commands/implement-story.md` is 40,759 bytes at authoring, before Story 3. Re-run `wc -c` at the start of task 4.6, because Story 3 edits the file first.
- Net change across the stories that edit it (3, 4, and 7) must be zero or less (`spec.md` → `## Implementation Approach` → Byte budget; `technical-spec.md` → `## Byte Budget`). Keep the recode brief addition short.

**Gaps found at generation, resolved in the spec (2026-11-04)**
- **A passing re-review used to skip `--prior`.** Now `--prior` runs on every agent verdict when a manifest exists (`spec.md` → `### Gate 3 decision`, row 3a; `### Repro as regression test`).
- **There was no match rule for `repro_still_failing`.** The match is by file. The recorded run must contain the path and an `exit code: 0` line, the same rule `_tested_ok` uses (`technical-spec.md` → `## Manifest`).
- **Manifest overwrite.** `--manifest-out` merges with an existing file, and an entry with the same path is replaced. A run with no new confirmations leaves the file unchanged (`technical-spec.md` → `## Manifest`). Task 4.1 adds a merge case.

**Assumptions**
- `user_type` was not supplied. "Developer running `/implement-story`" comes from `spec.md` → `## Experience Design` → `### Who uses it`.
- The coder creates each repro file in the working tree, per `technical-spec.md` → `## Gate 3 Wiring`. The contract says "commits." This story follows the technical spec.

**Integration**
- Depends on Story 3: the `evidence` call, the Gate 3 report line, and `test_evidence_gate_wiring.py`.
- Stories 6 and 7 also edit Gate 3 of `commands/implement-story.md`. Run in sequence.
- Generated trees: after any edit to `commands/`, run `python3 scripts/gen-platform-trees.py` and commit the trees in the same story.

## Definition of Done

- [x] All tasks completed
- [x] All acceptance criteria met
- [x] Tests passing
- [x] Code reviewed
- [x] Documentation updated

## Context for Agents

- **Error map rows:** [Write the manifest, --prior] — `technical-spec.md` → `## Error & Rescue Map`
- **Shadow paths:** [Happy] — `technical-spec.md` → `## Shadow Paths`
- **Business rules:** [Repro as regression test, normalization on both sides] — `spec.md` → `## Business Rules (Expanded)` → `### Repro as regression test`; `technical-spec.md` → `## Manifest`, `## Gate 3 Wiring (Story 3, Story 4)`
- **Experience:** [Coder receives the repro file itself, Gate 3 journey steps 4 and 5] — `spec.md` → `## Experience Design` → `### Interaction patterns`, `### Journey (Gate 3)`

---

## What Was Built

**Implementation Date:** 2026-11-04

### Context

Merge commit `a6a8e8c` landed before this story. It brought in design-divergence Story 6, which removed the design-divergence skill and its Gate 0 wiring, and it fixed `test_divergence_trial_outcome.py`, which failed during Story 3. The story's tasks and AC still say "row 3a". After DEV-026 that row is 4a.

### Files Created

1. **`scripts/tests/test_prior_reasons_survive_runner_not_found_repro.py`** (59 lines)
   - Gate 3 iteration 1, F1. It is the confirmed repro, committed verbatim. Case: FAIL verdict, a manifest repro missing from `--changed`, and a runner binary missing from PATH. Result: line 1 `fail` with `repro_removed`, not `unverifiable (runner_not_found)`.
   - `_normalized_sha256` matches the manifest: `89bfdd78238ce9efd20d2c403d62946ecc50af7f4b5e64ec8da755c6f14e3ef7`.
2. **`scripts/tests/test_prior_unread_verdict_repro.py`** (39 lines)
   - Gate 3 iteration 1, F2. It is the confirmed repro, committed verbatim. Case: a `**REVIEW_RESULT:** FAIL` line the script cannot parse, plus a valid manifest. Result: `verdict_not_fail`, not `pass (prior_ok)`, so row 9 cannot turn the FAIL into PASS.
   - `_normalized_sha256` matches the manifest: `38c4fdabe07eb0218b2bb225590b7647fc24a2dffdfa1481df88641f59ff9877`.

### Files Modified

- **`scripts/review-override.py`** (`evidence`; +195 −21)
  - Normalization: `_normalized` and `_normalized_sha256` are one helper for both the write and the compare. It converts CRLF to LF, strips trailing whitespace on each line, and leaves exactly one final newline.
  - Manifest write: `_write_json_atomic` is copied from `scripts/review-panel.py`, not imported. `_write_manifest` merges with an existing manifest and replaces an entry with the same path. A run with no new confirmations leaves the file unchanged. A failed write adds `reason: manifest_write_failed` and leaves line 1 unchanged.
  - Entry fields: finding, path, `sha256`, kind, location, and `content` (DEV-027). A run that changed the tree writes no entry (DEV-020).
  - `_load_manifest` and `_manifest_path_ok` report `bad_manifest` for: a missing or unreadable file, the wrong schema, an entry without a string `sha256`, an absolute or `..` path, or a `content` that is not a string (DEV-022). `content` is optional.
  - `_prior_reasons` reports `repro_removed`, `repro_modified`, or `repro_still_failing`. Repros are checked in manifest order, and each reports its first failing check (DEV-021).
  - `_run_names_ok` holds the recorded-run rule, which `_tested_ok` and `repro_still_failing` now share.
  - `_run_level` handles a stop after a failed prior check: `verdict_not_fail`, `no_git`, `runner_not_found`, or `abort`. It prints `fail`, then the prior reasons, then the stop's reason (DEV-028, F1).
  - Only PASS and PAUSE take the prior-only path (F2).
  - `--prior` and `--manifest-out` used to say "accepted; does nothing yet". Both now do what their help text says.
- **`plugins/writ/scripts/review-override.py`**: generated, byte-identical to the source.
- **`commands/implement-story.md`** (`#### Gate 2`, `#### Gate 3`): 39731 → 39929 bytes, +198
  - Gate 2 binds `<checks>`.
  - `recorded_test_results` covers the story's tests and each path in `<manifest>` = `.writ/state/evidence-<story-stem>.json`.
  - `--repo .` is dropped from `check` and `safety-fact`.
  - The `<review>`/`<tests>` save runs on every verdict, and the Jev shadow reuses both files.
  - Evidence runs on an agent FAIL. Once `<manifest>` exists, it runs on any verdict with `--prior <manifest>`. It always passes `--manifest-out <manifest>` and `--checks <checks>`.
  - Decision table: row 1 is `repro_mutated_tree` → BLOCKED (DEV-026). Row 4a is `repro_removed`, `repro_modified`, or `repro_still_failing` → FAIL → recode. The other rows are relabelled, and the old row 6 is gone.
  - Recode briefs add `## Evidence repros`: for each repro, its finding, path, fenced content, and "Create it exactly; do not edit it. Make it pass." (DEV-019). On row 4a, these come from `<manifest>`.
- **`cursor/plugin/commands/implement-story.md`, `plugins/writ/commands/implement-story.md`**: generated.
- **`skills/evidence-gated-findings/SKILL.md`** (reason table) and its 2 generated copies (`cursor/plugin/skills/`, `plugins/writ/skills/`): six rows, `repro_removed` through `prior_ok`.
- **`.writ/docs/agent-cli-contract.md`** (`review-override.py` entry): documents the prior-only form on PASS or PAUSE and `manifest_write_failed`.
- **`scripts/tests/test_review_override.py`**:
  - `EvidenceManifestTests` has 22 tests, under a comment that names `2026-11-04-evidence-gated-review`.
  - Story 2's `test_known_surfaces_and_later_story_flags_parse` no longer passes `--prior`, because the flag has behavior now.
- **`scripts/tests/test_evidence_gate_wiring.py`**:
  - New: `RecodeBriefTest` (6), `ReReviewReplayTest` (3), `test_a_tree_mutation_outranks_every_row`, and `test_jev_shadow_reuses_the_saved_files`.
  - The `ReplayCase` base class is split out of `ReplayTest`.
  - `test_nine_rows_numbered_in_order` is renamed `test_rows_numbered_in_order`. The mirrors are renumbered.
- **`scripts/tests/test_governor_enforcement.py`**: `KNOWN_OVER_BUDGET["commands/implement-story.md"]` 14771 → 14969, with a dated comment.
- **`scripts/tests/test_jev_shadow_hooks.sh`**: the ac-shadow needles now use `<tests>` and `<review>`. The "targeted run" guard moved to the `recorded_test_results` sentence.
- **`.writ/specs/2026-11-04-evidence-gated-review/spec-lite.md`**:
  - The Story 2 and Story 5 amendment blocks and the Story 4 amendments are consolidated into one "As built (drift-log DEV-004 to DEV-028)" block.
  - It went from 102 to 91 lines, because eval's length check failed at 102 of 100.
- **`.writ/specs/2026-11-04-evidence-gated-review/drift-log.md`**: the Story 4 section, DEV-019 to DEV-028, is appended. Existing entries are untouched.

### Implementation Decisions

1. **A tree mutation outranks every row (DEV-026).** The orchestrator made this call. The locked contract's Hardest Constraint says any tree mutation is BLOCKED, and the contract outranks spec.md's table. So `repro_mutated_tree` → BLOCKED is now row 1. The spec.md amendment is pending, for the user.
2. **Manifest entries carry `content` (DEV-027).** Without it, a row 4a recode for `repro_removed` or `repro_modified` has no source for the repro. `content` is optional when loaded, so the manifest from iteration 1 stays valid.
3. **Prior failures survive a run-level stop (DEV-028).** The conflict was between § CLI (run-level `unverifiable`) and § Manifest (`fail`). It was settled in favor of AC-4.2. This closes F1.
4. **Only PASS and PAUSE take the prior-only path.** An unread verdict stays `verdict_not_fail`. This closes F2, which failed open.
5. **One normalization helper.** The write and the compare cannot drift apart.
6. **Byte offsets for the additions (DEV-025):**
   - `<checks>` is bound once.
   - The save is unconditional, so the Jev shadow reuses `<review>` and `<tests>`.
   - `--repo .` is dropped.

### Test Results

**Verification:** Automated, test-first
**Coverage:** unverifiable (no coverage report)

- ✅ Gate 1, first pass: red at 15 + 13 failed, then green at 244.
- ✅ Gate 1, recode 1: red at the 2 repros + 7 + 7 failed, then green at 255.
- ✅ Gate 1 mutation probes: 7/7 killed.
- ✅ Recorded run, 313 passed, `exit code: 0`. It covers every changed test file and all five committed repros: this story's two and Story 5's three.
- ✅ Full suite on 3.9: 4212 passed, 2 skipped, 0 failed.
- ✅ Full suite on 3.14: 4212 passed, 2 skipped, 0 failed, 1231 subtests.
- ✅ Bash suite: all green.
- ✅ `python3 scripts/gen-platform-trees.py --check`: pass.
- ✅ `bash scripts/eval.sh`: exit 0, after the spec-lite trim.
- ✅ Authenticity: pass on both repros.
- ✅ Review iteration 2: 16/17 seeded mutants killed. The survivor, N10 (`_run_level` failing on `--surface review`), is on an unreachable path, because `commands/review.md` never passes `--prior`.

### Byte count

`wc -c commands/implement-story.md`: before 39731, after 39929, delta +198. Stories 3 and 4 together: +1378.

### Review Outcome

**Result:** PASS

- **Iteration count:** 2 iteration(s)
- **Drift:** Medium (DEV-026); DEV-019 to DEV-025, DEV-027, and DEV-028 Small, auto-amended
- **Security:** Low
- **Boundary Compliance:** Every hand edit outside the Owned files is one of three things: a confirmed repro committed verbatim, a doc change the iteration-1 review asked for, or a pin that follows a deliberate change. The rest are regenerated trees.

### Gate record

**REVIEW_RESULT:** FAIL

Iteration 1, `review-agent`, saved at `.writ/state/gate3-review-story-4-repro-as-regression-test-iter1.md`. `evidence-gate: 2 confirmed, 2 advisory, 0 unverifiable`.

- F1, Major, confirmed: on an agent FAIL, a run-level stop after the prior checks (`no_git`, `runner_not_found`, `abort`) dropped the prior failure.
- F2, Major, confirmed: a verdict line the script could not read took the prior-only path and printed `pass (prior_ok)`.
- F3, Minor, advisory: the Evidence opener could be read as leaving `--prior` off on an agent FAIL.
- F4, Minor, advisory: the `repro_modified` branches had no tests. Mutant S19 survived.
- The evidence step wrote the first real manifest, `.writ/state/evidence-story-4-repro-as-regression-test.json`. Both repros were committed verbatim.

**Orchestrator decision (DEV-026):** the locked contract's Hardest Constraint says any tree mutation is BLOCKED, and the contract outranks spec.md's table.

- `repro_mutated_tree` → BLOCKED is now row 1.
- The old row 6 is gone, and the other rows are relabelled.
- The spec.md amendment is pending, for the user.

**REVIEW_RESULT:** PASS

Iteration 2, `review-agent`, saved at `.writ/state/gate3-review-story-4-repro-as-regression-test.md`.

- F1 to F4 are fixed, and 16/17 mutants are killed.
- The re-review ran `evidence --prior <manifest>` on the PASS. Result: `pass (prior_ok)`.
- Both repros are present, unmodified, and pass in the recorded run.

- **Gate 0:** arch-check pass (rederived proceed). `gate0-divergence:` design-divergence Story 6 (merged in `a6a8e8c`) removed that surface, so no line applies.
- **Gate 0.5:** boundary map computed (`.writ/state/boundary-story-4-repro-as-regression-test.json`)
- **Gate 1:** coding-agent, test-first. First pass: red at 15 + 13 failed, then green at 244. Recode 1: red at the 2 repros + 7 + 7 failed, then green at 255. Mutation probes 7/7 killed.
- **Gate 2:** no linters. `arch-lint: none — see .writ/docs/architecture-lint.md`. `build-smoke: unverifiable (unsupported_stack)`
- **Gate 2.5:** cross-component. `gate3-route: review-agent (outside_boundary test_governor_enforcement.py, test_jev_shadow_hooks.sh, generated trees)`
- **Gate 3:** `reviewer-filters: on`. 2 iterations: FAIL, then PASS. `review-override check`: pass. `safety-fact: tested (claimed tested)`. `evidence-gate: 2 confirmed, 2 advisory, 0 unverifiable` (iteration 1), then `prior_ok` on the iteration-2 PASS. `review-panel: skipped — platform cannot spawn other vendors`. `jev: not run`.
- **Gate 3.5:** Overall Medium. DEV-026 is Medium: logged, PASS. DEV-019 to DEV-025, DEV-027, and DEV-028 are Small, auto-amended into spec-lite.
  - drift-format: `fail large_drift_without_pause`. This is the known false positive from Story 1's DEV-001, so no PAUSE line was added.
- **Gate 4:**
  - Recorded run: 313 passed.
  - Full suite: 4212 passed, 2 skipped, 0 failed on 3.9 and on 3.14.
  - Bash suite: green. `gen-platform-trees.py --check`: pass. `eval.sh`: exit 0.
  - Authenticity: pass. Coverage: unverifiable (no report).
- **Gate 4.5:** `app-verify: unverifiable (no_recipe)`
- **Gate 5:** `docs-check: unverifiable (no public exports in the changed set)`. The skill's reason table gained six rows. `agent-cli-contract.md` now describes the prior-only form.

### Deviations from Spec

- **[DEV-019] The no-edit line is shorter** (Small)
  - Spec said: technical-spec § Gate 3 Wiring: "Create this file with this exact content and do not edit it. Make it pass."
  - Reality: "Create it exactly; do not edit it. Make it pass." The instruction is the same, and the change saves bytes.
  - Resolution: Auto-amended spec-lite.md.
- **[DEV-020] A run that changed the tree writes no manifest** (Small)
  - Spec said: § Manifest says to write on confirmation. It does not mention mutation.
  - Reality: no entry is written when `run.mutated` is set. A mutation is a BLOCKED escalation, not a recode.
  - Resolution: Auto-amended spec-lite.md.
- **[DEV-021] What `repro_removed` and `repro_modified` cover** (Small)
  - Spec said: `repro_removed` means the path is not in `--changed`. `repro_modified` means the hash differs.
  - Reality: `repro_removed` also covers a file gone from disk. `repro_modified` also covers a directory, an unreadable file, non-UTF-8 content, and a symlink that resolves outside the repo.
  - Resolution: Auto-amended spec-lite.md.
- **[DEV-022] Manifest entries are validated lexically** (Small)
  - Spec said: a missing or wrong-schema manifest gives `bad_manifest`.
  - Reality: `bad_manifest` also covers an entry without a string `sha256`, an absolute or `..` path, or a `content` that is not a string.
  - Resolution: Auto-amended spec-lite.md.
- **[DEV-023] The prior-only output form on PASS and PAUSE** (Small)
  - Spec said: the summary was unspecified.
  - Reality: `review-override evidence: <state> (<first reason>)`. Only PASS and PAUSE take this path.
  - Resolution: Auto-amended spec-lite.md.
- **[DEV-024] `no_review_output` is checked before the manifest** (Small)
  - Spec said: the `--prior` checks run "before anything else".
  - Reality: the switch and the review-output read come first.
  - Resolution: Auto-amended spec-lite.md.
- **[DEV-025] Gate 3 byte cuts** (Small)
  - Spec said: technical-spec shows `--repo .`, and the Story 3 save was conditional.
  - Reality: `--repo .` is dropped, `<checks>` is bound once, and the save runs on every verdict.
  - Resolution: Auto-amended spec-lite.md.
- **[DEV-026] ⚠️ The tree-mutation row is first, ahead of every other row** (Medium)
  - Spec said: spec.md § Gate 3 decision puts `repro_mutated_tree` at row 6, after `check`, contradicts, safety-fact, 3a, PASS/PAUSE, and switch off.
  - Reality: `repro_mutated_tree` → BLOCKED is row 1. Spec rows 1 to 3 become 2 to 4, 3a becomes 4a, 4 and 5 become 5 and 6, and the old row 6 is gone. Story 3 routing changes for one case only: an evidence run that mutated the tree now BLOCKs even when `check` fails or the safety fact is below floor.
  - Resolution: fixed in the command, logged, PASS.
  - Spec amendment: pending, for the user. spec.md § Gate 3 decision and technical-spec § Interaction Edge Cases need the new order.
- **[DEV-027] Manifest entries carry the normalized `content`, and a row 4a brief reads it** (Small)
  - Spec said: § Manifest lists finding, path, sha256, kind, and location.
  - Reality: new entries also store `content`. It is optional when loaded.
  - Resolution: Auto-amended spec-lite.md.
- **[DEV-028] A run-level stop after a failed prior check prints `fail`** (Small)
  - Spec said: § CLI makes `no_git`, `runner_not_found`, and `verdict_not_fail` run-level `unverifiable`. § Manifest says a prior failure makes line 1 `fail`.
  - Reality: on gate3 with prior failures, line 1 is `fail`, followed by the prior reasons and then the stop's reason.
  - Resolution: Auto-amended spec-lite.md.

Full entries: `drift-log.md` → Story 4.

### Notes for Downstream Stories

- **Story 7, bytes:**
  - Story 7 must free at least 1378 bytes from `commands/implement-story.md`, or the user decides (DEV-010).
  - Stories 3 and 4 together are +1378, about 28 bytes over the ~1,350 that Story 7's panel removals are expected to free.
- **Story 7, test update:** must update `RoadmapLineTest` in `test_adr_032_inventory.py`.
- **Not fixed:**
  - `_load_manifest` accepts a `content` that does not hash to `sha256`. It fails closed: restoring the wrong content gives `repro_modified`. But the recode loop would then run to the cap.
  - A row 4a brief has no fallback for an entry without `content`.
  - `agent-cli-contract.md:137` says `<verdict>` where it means `<state>`.
  - `evidence-gate: not run (PASS)` prints even when the prior checks ran.
  - `repro_still_failing` uses a substring match, as the spec requires (it reuses `_tested_ok`'s rule). A path-boundary match would move Safety Fact behavior too.
  - Tamper resistance: the manifest is in gitignored `.writ/state/`, so deleting it turns the guard off, as AC-4.4 specifies. The user decides whether to change that.
