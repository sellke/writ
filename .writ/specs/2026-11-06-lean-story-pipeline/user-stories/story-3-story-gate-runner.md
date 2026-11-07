# Story 3: story-gate.py runner

> **Status:** Completed ✅ (2026-11-06)
> **Commit:** 603620566dfc41dd65770aca6398410e631a7360
> **Priority:** High
> **Dependencies:** Story 2

## User Story

**As a** `/implement-story` orchestrator, and the supervisor that reads the record
**I want to** run the default-path deterministic checks through one `story-gate.py` call before Gate 3 and one after, and read a single record per story keyed to the head SHA
**So that** the orchestrator stops invoking each checker by hand, a lane cannot skip a check and still pass, and the procedure file gets smaller

## Acceptance Criteria

> **AC IDs assigned through:** AC-3.5

- [x] Given `scripts/story-gate.py`, when `run --phase pre-review|post-review`, `tally`, `--help`, and exit codes are checked, then the script follows the agent CLI check shape: line 1 `pass|fail|unverifiable`, `reason:` lines, the summary, and `run`'s JSON record as the last line; exit 0/1/2 `[AC-3.1]`
- [x] Given a stub checker that fails and another that passes in a temp git repo, when `run --phase post-review` runs, then every check runs in fixed order, the record is written atomically to `<state-dir>/story-gate-<story-stem>-post-review.json` with `head_sha` and `dirty`, and `restart` names the first failing check's target `[AC-3.2]`
- [x] Given a check whose script is missing or exits outside 0, 1, or 2, when `run` completes, then that check reads `unverifiable (helper_error: ...)`, the remaining checks still run, and that check alone does not set the overall verdict to `fail` `[AC-3.3]`
- [x] Given records under `story-gate-history/`, when `tally` runs, then it prints `runs`, `fails`, and `sole_catches` per check id and writes no file; with no history it prints `unverifiable` and `reason: no_records` `[AC-3.4]`
- [x] Given the default path in `commands/implement-story.md`, when it is read, then it names exactly two `story-gate.py` calls (`--phase pre-review` before Gate 3, `--phase post-review` after), at most four script invocations in total, a smaller byte size than at story start, and default check ids equal to the `path: default` gates; `agent-cli-contract.md` has a `story-gate.py` row and ADR-029 a dated runner note `[AC-3.5]`

## Implementation Tasks

- [x] 3.1 Write tests in `scripts/tests/test_story_gate.py` for `run` and `tally` against stub checkers in a temp git repo, covering stdout, record schema, restart order, and `unverifiable`. Add a test that the default check ids equal the `path: default` gates in `commands/implement-story.md`. Confirm they fail first `[AC-3.1, AC-3.2, AC-3.3, AC-3.4, AC-3.5]`
- [x] 3.2 Create `scripts/story-gate.py` in the agent CLI check shape: `run --phase pre-review|post-review` and `tally`, with `--help` and exit codes 0/1/2. Invoke the default-path checks in the fixed order from the technical spec. Write the record atomically and keep history. Stdlib only `[AC-3.1, AC-3.2, AC-3.3, AC-3.4]`
- [x] 3.3 Edit the default path in `commands/implement-story.md`: one `story-gate.py run --phase pre-review` call before Gate 3 and one `--phase post-review` call after it, replacing the per-script blocks. Keep Gate 3 and Gate 4 wording otherwise unchanged `[AC-3.5]`
- [x] 3.4 Update the pinning tests that name the replaced per-script blocks, including `test_implement_story_default_path.py`, `test_boundary_map.py`, `test_change_surface.py`, and `test_docs_check.py`, to pin the runner calls. Keep each guarded behavior. Keep `test_gate_upgrade_trial_outcome.py` presence probes passing `[AC-3.5]`
- [x] 3.5 Add the `story-gate.py` row to `.writ/docs/agent-cli-contract.md`. Add a dated note to `.writ/decision-records/adr-029-*.md` that a runner for one command's fixed check sequence is not a dispatcher. Record the `implement-story.md` byte change in `KNOWN_OVER_BUDGET` in `scripts/tests/test_governor_enforcement.py`. Regenerate with `python3 scripts/gen-platform-trees.py` `[AC-3.5]`
- [x] 3.6 Verify acceptance criteria: map each criterion to a passing test or pinned text. Run `python3 scripts/gen-platform-trees.py --check` and confirm it passes `[AC-3.1, AC-3.2, AC-3.3, AC-3.4, AC-3.5]`
- [x] 3.7 Verify all tests pass: run the changed test files with `uv run --isolated --python 3.9 --with pytest pytest <files>`, then with `--python 3.14`. Confirm `test_gate_upgrade_trial_outcome.py` passes. Run pytest alone `[AC-3.1, AC-3.2, AC-3.3, AC-3.4, AC-3.5]`

## Notes

- **Stdout:** `run` always prints the JSON record as its last line, after the check-shape summary (Business Rule 4; `technical-spec.md` → `story-gate.py` → Stdout). There is no `--json` flag.
- **CLI shape is defined elsewhere.** The `run` and `tally` argument lists, the record schema, and the history path are in `technical-spec.md` → `story-gate.py`. Follow that section. Do not copy it into the script's help text.
- **Pre-code check contingency.** If a pre-code check survives Story 2, add a `pre-code` phase. The story then logs Medium drift against the four-invocation success criterion, as `spec.md` → Technical Concerns states.
- **ADR-029 rule 4.** The rule bars "an umbrella binary, dispatcher, or tool registry." The runner covers one command's fixed sequence and routes nothing across commands. If review rejects that distinction, trim the prose and drop the runner. Task 3.5 records the distinction either way.
- **Ledger.** `implement-story.md` must shrink. `KNOWN_OVER_BUDGET` takes a dated entry only for the recorded byte change. Keep the entry tied to the current size, as the test pins it.
- **Stub checkers.** Tests create stub scripts in a temp repo. Do not write under the real `.writ/state/`. Pass `--state-dir` to a temp path.
- **Record location.** `.writ/state/` is gitignored, so records stay local. Tests must not leave files in the checkout.
- **Python 3.9 floor.** Stdlib only. Do not use 3.10+ APIs. Run `scripts/tests/test_agent_cli_contract.py` against the new script.
- **Targeted verification only.** The full pytest suite and `eval.sh` run once at the end of the spec, not in this story. Run pytest alone. `eval.sh`, bash tests, `.writ/state/` writes, or `git worktree` changes in the same checkout make `test_smoke_leaves_repo_unchanged` fail.
- **File ownership.** This story edits `commands/implement-story.md` and the pinning tests. Agent prose (Story 4) and supervisor and `implement-spec.md` (Story 5) belong to later stories.

## Context for Agents

- **Business rules:** [Business Rule 4, Business Rule 5, Business Rule 7] — spec.md → ## Specification Contract → 📋 Business Rules
- **Error map rows:** [Compute changed files, Run one check, Write record, Tally] — technical-spec.md → ## Error & Rescue Map
- **Shadow paths:** [Happy: every check passes, Nil: no review output (`--quick`), Empty: story changed no files, Upstream: a checker script crashes] — technical-spec.md → ## Shadow Paths
- **Interaction edge cases:** [Coder commits again after post-review `pass`, Two stories in one parallel batch write records at once] — technical-spec.md → ## Interaction Edge Cases
- **Experience:** [Every check passes, One check fails (restart line), A check cannot run (`unverifiable`)] — spec.md → ## 🎯 Experience Design → ### State Catalog
- **Technical:** technical-spec.md → ## `story-gate.py` (`run`, `tally`, Record); spec.md → ## Detailed Requirements (`story-gate.py` bullet)

---

## What Was Built

**Implementation Date:** 2026-11-06

### Files Created

1. **`scripts/story-gate.py`** (979 lines)
   - Check-shape runner: `run --phase pre-review|post-review` and `tally`; JSON record always the last line; atomic record plus history; `head_sha` and `dirty` (ignores only the story's spec folder)
   - Pre-review: build smoke, arch-lint, change surface, crossings/route, blast radius; prints `route:`, `change_surface:`, `blast_radius:`, the three switch states, and `arch-lint:`
   - Post-review: `review-override.py` check, safety-fact, evidence; Gate 3's 9-row decision (`decide_gate3`); drift-format; test-integrity coverage and authenticity (supported-stack test files only); repro-order; Jev shadow (never counted)
2. **`scripts/tests/test_story_gate.py`** (824 lines) — stub checkers in temp git repos; every Error & Rescue Map row, shadow path, restart target, porcelain parsing, authenticity input
3. **`scripts/tests/test_story_gate_verdict_repro.py`**, **`scripts/tests/test_story_gate_respawn_repro.py`** — Gate 3 iteration 1 evidence repros (F1, F2), committed unchanged
4. **`plugins/writ/scripts/story-gate.py`** (generated)

### Files Modified

- **`commands/implement-story.md`** (Step 3 pointer to Gate 0 under `--full-pipeline`; Gate 1 `**Base:**`; Gate 2 pre-review call; Gate 3 post-review call and restart table; Gate 3.5 § A ordering; Gate 4; Quick Mode; `gate3_5_drift` `kill_when`) — 41128 → 38542 bytes
- **`.writ/docs/agent-cli-contract.md`** (`story-gate.py` row and note)
- **`.writ/decision-records/adr-029-agent-cli-contract.md`** (dated note: a runner for one command's fixed check sequence is not a dispatcher)
- **`scripts/tests/test_governor_enforcement.py`** (`KNOWN_OVER_BUDGET` 16168 → 13582; temporary raise gone)
- **Pin files moved to the runner** — `test_change_surface.py`, `test_drift_format.py`, `test_implement_story_default_path.py`, `test_boundary_map.py`, `test_quality_gate_wiring.py`, `test_repro_first_wiring.py`, `test_review_override.py`, `test_review_route_rigor.py`, `test_evidence_gate_wiring.py` (decision mirror calls `decide_gate3`; ordering pin restored), `test_jev_shadow_hooks.sh`
- **`.writ/specs/2026-11-06-lean-story-pipeline/gate-evidence.md`** (`gate3_5_drift` kill condition)
- **`.writ/issues/improvements/2026-09-03-test-integrity-authenticity-flags-every-bash-test.md`** (runner excludes shell tests)
- **`cursor/plugin/commands/implement-story.md`, `plugins/writ/commands/implement-story.md`** (generated)

### Implementation Decisions

1. **No `pre-code` phase** — Gate 0.5 stays a direct `boundary-map.py compute` call, so the default path has exactly two `story-gate.py` calls and four script calls in total.
2. **Gate 3's decision table lives in the runner** — the orchestrator acts on line 1 and `restart:`; agent spawns, the safety-fact re-spawn, § A's Large-drift PAUSE, BLOCKED, and recode stay in prose.
3. **Restart vocabulary** — `gate1`, `gate2`, `gate3`, `gate3-blocked`, `gate4`; no target → DEGRADED.

### Test Results

**Verification:** Automated

- ✅ Orchestrator's recorded run (Python 3.9): 1249 passed across 21 files; `test_jev_shadow_hooks.sh`, `test_eval_verdict_provenance.sh`, `test_eval_spawn_cap.sh`, `test_install_update_dev_scripts.sh` pass
- ✅ Reviewers' runs on Python 3.14: `test_story_gate.py`, repros, `test_agent_cli_contract.py` pass
- ✅ `gen-platform-trees.py --check`: pass
- ✅ Runner on its own story: pre-review pass; post-review `gate3: PASS (row 5)`, safety-fact `tested`, `dirty: false`
- ⚠️ Post-review `gate4_authenticity`: `test_imports_no_source` on the F2 repro, recorded as a false positive (drift-log DEV-017)
- Full suite and `eval.sh`: run once at spec end

**Coverage:** N/A — no coverage report in this repo

### Review Outcome

**Result:** PASS

- **Iteration count:** 3 iteration(s) (iteration 1 FAIL: F1 verdict parse, F2 evidence before re-spawn, both confirmed; iteration 2 PASS; orchestrator dogfood found the porcelain `dirty` bug and bash tests in authenticity, maintainer chose "Recode both"; iteration 3 PASS)
- **Gate 3 route:** `review-agent` (cross-component)
- **Drift:** Medium
- **Security:** Clean
- **Boundary Compliance:** every crossing justified by a task (ADR-029 note, generated copies, pin files, repros)
- **Safety fact:** measured `tested` (claimed `tested`)
- **Evidence gate:** iteration 1 `2 confirmed, 3 advisory`; later `prior_ok`

### Deviations from Spec

See `drift-log.md` Story 3: DEV-008–011, 013–015 (Small, spec-lite amended), DEV-012 and DEV-016 (Medium, follow-ups), DEV-017 (Medium, authenticity false positive under the DEV-005 precedent).

### Lessons Learned

1. **Run the runner on its own story** — two defects (`dirty` from stripped porcelain output, bash tests in authenticity) passed two reviews and surfaced only when the runner checked a real tree.
2. **`repro-order.py` judges every source commit since `<base>`** — a mid-story repro fails against earlier source commits, which pushed the coder to drop `Repro:` trailers. Needs a fix in `repro-order.py`.

### Next Story

**Stories 4 and 5** (parallel): targeted-test ownership in the agents; the supervisor reads the `story-gate` record and checks its head SHA. Follow-ups from this story: evidence-skip overshoot (Minor), § A/PAUSE ordering and one-record-per-iteration tally (DEV-012), `skip`→`unverifiable` for authenticity (DEV-016), `repro-order` range semantics, Python authenticity false positives.

