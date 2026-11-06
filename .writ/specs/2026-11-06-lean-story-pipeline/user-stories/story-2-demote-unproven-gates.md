# Story 2: Demote gates with no recorded catch

> **Status:** Completed ✅ (2026-11-06)
> **Priority:** High
> **Dependencies:** Story 1

## User Story

**As a** developer running `/implement-story` on the default path
**I want to** gates with no recorded catch moved under `--full-pipeline`, and gates with a recorded catch left on the default path
**So that** the default path runs fewer checks and each kept check has evidence behind it

## Acceptance Criteria

> **AC IDs assigned through:** AC-2.5
> **Verified by:** AC-2.4 — `python3 scripts/gen-platform-trees.py --check` pass and `test_governor_enforcement.py` in the recorded run (`.writ/state/gate3-tests-story-2-demote-unproven-gates.txt`, exit 0); `KNOWN_OVER_BUDGET` 16168 = 41128 − 24960, recorded in What Was Built → Review Outcome
> **Verified by:** AC-2.5 — `git diff --diff-filter=DR dd07441 f09fc32` is empty, and `test_gate_upgrade_trial_outcome.py` passed in the recorded run, recorded in What Was Built → Review Outcome

- [x] Given `gate-evidence.md` marks a gate for demotion, when Story 2 is complete, then that gate's section sits under the `--full-pipeline` heading in `commands/implement-story.md` and its `gates:` entry reads `path: full-pipeline` `[AC-2.1]`
- [x] Given a gate whose evidence cites a recorded catch, when Story 2 is complete, then its section and its inputs stay on the default path and its `gates:` entry has no `path:` line `[AC-2.2]`
- [x] Given the pinning tests, when Story 2 is complete, then each assertion on a demoted gate's default-path wording asserts the full-pipeline wording instead and no guarded behavior is dropped `[AC-2.3]`
- [x] Given `commands/implement-story.md` changes byte size, when `scripts/tests/test_governor_enforcement.py` runs, then `KNOWN_OVER_BUDGET` holds a dated entry for the new size and `python3 scripts/gen-platform-trees.py --check` passes `[AC-2.4]`
- [x] Given the demotion is complete, when the repo is checked, then no gate script, agent, or test file is deleted and `scripts/tests/test_gate_upgrade_trial_outcome.py` still passes `[AC-2.5]`

## Implementation Tasks

- [x] 2.1 Write failing tests in `scripts/tests/test_implement_story_default_path.py` asserting demoted gate sections sit under `--full-pipeline` and kept gates stay on the default path `[AC-2.1, AC-2.2]`
- [x] 2.2 Move each demoted gate section in `commands/implement-story.md` under the `--full-pipeline` heading, unchanged in content. Add `path: full-pipeline` to each demoted `gates:` entry. Leave kept gates in place `[AC-2.1, AC-2.2]`
- [x] 2.3 Change wording pins to full-pipeline wording in `scripts/tests/test_implement_story_default_path.py`, `scripts/tests/test_boundary_map.py`, `scripts/tests/test_change_surface.py`, `scripts/tests/test_docs_check.py`, and each other pin listed in Notes. Keep every guarded check `[AC-2.3]`
- [x] 2.4 Add a dated `KNOWN_OVER_BUDGET` entry for the new `commands/implement-story.md` byte size in `scripts/tests/test_governor_enforcement.py`. Run `python3 scripts/gen-platform-trees.py` to regenerate `claude-code/`, `cursor/plugin/`, and `codex/` `[AC-2.4]`
- [x] 2.5 Verify acceptance criteria: run `scripts/tests/test_gate_upgrade_trial_outcome.py` and the tests changed above. Confirm no gate script, agent, or test file was removed `[AC-2.1, AC-2.2, AC-2.3, AC-2.4, AC-2.5]`
- [x] 2.6 Verify all targeted tests pass on Python 3.9 and `python3 scripts/gen-platform-trees.py --check` is clean `[AC-2.3, AC-2.4]`

## Notes

- **Input dependency:** `gate-evidence.md` does not exist yet. Story 1 writes it. Its rows decide which gates move. Start only after each `gates:` entry is marked keep or demote.
- **Current `gates:` entries** in `commands/implement-story.md`: `gate0_arch`, `gate0_5_boundary`, `gate1_coding` (prose-only), `gate2_build`, `gate2_5_surface`, `gate3_review`, `gate3_5_drift`, `gate4_tests`, `gate4_5_behavior`, `gate5_docs`.
- **Finding pins:** the spec counts 42 test and eval files that pin `implement-story.md` text. Build the full list for demoted gates with `grep -rln` on each demoted gate's script name and section heading under `scripts/tests/` and the eval scripts. The four named files in task 2.3 are examples, not the full set.
- **Business Rule 3:** a kept gate that reads another gate's output keeps that producer on the default path. Safety Fact reads the Gate 2.5 risk route and blast radius. The removal-trial keep verdicts (Safety Fact, Reviewer Filters, Gate 0 Divergence) and the ADR-032 evidence gate are not reopened.
- **Business Rule 2:** demotion moves text only. Gate scripts, agents, and tests stay in the product.
- **Presence probes:** `test_gate_upgrade_trial_outcome.py` ties each kept upgrade to a presence probe in `implement-story.md`. Those probes must keep passing (this spec's Business Rule 3; spec.md → Cross-Spec Overlap).
- **Symlinks:** `.claude/` and `.cursor/` point at product source. Editing `commands/implement-story.md` changes them. Do not run `install.sh` on this repo.
- **Test runs:** run pytest alone. `eval.sh`, bash tests, and `.writ/state/` writes in the same checkout during pytest break `test_smoke_leaves_repo_unchanged`. The full pytest suite (both 3.9 and 3.14) and `eval.sh` run once at the end of the spec, not in this story.
- **Failure mode:** if a pinning test guards a default-path behavior that a kept gate needs, the gate stays on the default path and `gate-evidence.md` records the dependency (technical-spec error map, "Demotion (Story 2)").

## Context for Agents

- **Error map rows:** [Demotion (Story 2)] — from technical-spec.md error map
- **Shadow paths:** []
- **Business rules:** [2, 3] — from spec.md → Specification Contract → 📋 Business Rules
- **Experience:** []

---

## What Was Built

**Implementation Date:** 2026-11-06

### Files Created

[None created]

### Files Modified

- **`commands/implement-story.md`** (Pipeline table, Control flow, new `### Full-Pipeline Gates` section, Quick Mode, exit criterion 3)
  - Gates 0, 4.5, and 5 moved under `### Full-Pipeline Gates (\`--full-pipeline\` only)`, placed after Gate 4; its lead says the default path, `--quick`, and `--review-only` skip them by design (not DEGRADED) and states the run order (Gate 0 before Gate 0.5; 4.5 and 5 after Gate 4)
  - Only the default/`--quick`/`--review-only` clauses inside the moved sections were removed; Gate 0's agent block now precedes its verify block
  - Gate 3.5 and the other kept gates stay in Step 3
- **`scripts/tests/test_implement_story_default_path.py`** (`GateDemotionTests`, 5 tests; Pipeline, Gate 0/4.5/5 pins moved to full-pipeline wording)
- **`scripts/tests/test_arch_check.py`, `test_change_surface.py`, `test_evidence_gate_wiring.py`, `test_harness_cuts.py`, `test_review_route_rigor.py`** (Gate 0 slice ends `#### Gate 0.5:` → `#### Gate 4.5:`; same text guarded)
- **`scripts/tests/test_docs_check.py`** (Gate 5 slice ends at Step 4; heading, order, and no-default-wording asserts)
- **`scripts/tests/test_governor_enforcement.py`** (`KNOWN_OVER_BUDGET` 16566 → 16168, dated; 2577-byte gap to 38551 left for Story 3)
- **`cursor/plugin/commands/implement-story.md`, `plugins/writ/commands/implement-story.md`** (generated)

### Implementation Decisions

1. **One full-pipeline section instead of in-place labels** — the three gates sit together after Gate 4, with the run order stated in the section lead and the Pipeline table.
2. **`**\`--full-pipeline\`:**` labels kept inside the section** — `_default_agent_markers` treats an unlabeled `> **Agent:**` line as a default spawn.

### Test Results

**Verification:** Automated

- ✅ Orchestrator's recorded run (Python 3.9): 675 passed across 16 files; `test_eval_spawn_cap.sh` 6/6; `test_eval_verdict_provenance.sh` 10/10
- ✅ Reviewer's extra run: 13 more pin files, 1210 passed, 1 skipped; `eval.sh --report` exit 0
- ✅ `gen-platform-trees.py --check`: pass; `verdict-provenance.py check --prose-only-blocking`: pass
- ✅ `test-integrity.py authenticity`: pass
- Full suite and `eval.sh`: run once at spec end

**Coverage:** N/A — `test-integrity.py coverage` unverifiable (no coverage report in this repo)

### Review Outcome

**Result:** PASS

- **Iteration count:** 1 iteration(s)
- **Gate 3 route:** `review-agent` (cross-component; 5 boundary crossings)
- **Drift:** Small
- **Security:** Clean
- **Boundary Compliance:** Every change in owned paths or in pins the story Notes direct the coder to find; five unlisted files justified (four slice-end test edits, one generated copy)
- **Safety fact:** measured `tested` (claimed `tested`)
- **AC-2.4:** `gen-platform-trees.py --check` pass; `KNOWN_OVER_BUDGET` 16168 = 41128 − 24960
- **AC-2.5:** `git diff --diff-filter=DR dd07441 f09fc32` empty; `test_gate_upgrade_trial_outcome.py` passed

### Deviations from Spec

See `drift-log.md` Story 2: DEV-006, DEV-007 (Small, auto-amended in spec-lite).

### Lessons Learned

1. **Slice-bounded pins move with their sections** — five tests ended their Gate 0 slice at `#### Gate 0.5:`; after the move each needed the new following heading, or it would have read to end of file and still passed.

### Next Story

**Story 3:** `story-gate.py` runner — replace the per-script blocks with two runner calls and close the 2577-byte gap to 38551. Carry forward: a short pointer at the top of Step 3 that `--full-pipeline` runs Gate 0 first (Gate 0.5 reads its `BOUNDARY OVERRIDE` warnings).

