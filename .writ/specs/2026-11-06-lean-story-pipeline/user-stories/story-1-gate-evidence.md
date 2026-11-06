# Story 1: Gate declarations and evidence

> **Status:** Completed ✅ (2026-11-06)
> **Priority:** High
> **Dependencies:** None

## User Story

**As a** Writ maintainer
**I want to** declare, for each gate in `commands/implement-story.md`, the failure it catches, its recorded evidence, and a checkable removal condition
**So that** gates with no recorded catch can be moved to `--full-pipeline` with a traceable reason

## Acceptance Criteria

> **AC IDs assigned through:** AC-1.5

- [x] Given a `gates:` entry in `commands/implement-story.md` that lacks `catches:`, `evidence:`, or `kill_when:`, when `verdict-provenance.py check` runs, then it reports `missing_catches`, `missing_evidence`, or `missing_kill_when` for that gate `[AC-1.1]`
- [x] Given a `gates:` entry whose `path:` is neither `default` nor `full-pipeline`, when the check runs, then it reports `unknown_path_value` for that gate, and an entry with no `path:` produces no finding `[AC-1.2]`
- [x] Given every `gates:` entry has all three fields and a valid or absent `path:`, when the check runs, then it reports no new finding codes, and existing finding codes and exit codes are unchanged `[AC-1.3]`
- [x] Given `gate-evidence.md`, when it is read, then it has one row per `gates:` entry giving a dated catch citation or `none recorded`, the dependency reason if any, and a path decision that follows Business Rules 2 and 3 (`full-pipeline` only for `none recorded` with no kept dependent) `[AC-1.4]`
- [x] Given Story 1 is complete, when the diff of `commands/implement-story.md` is read, then only `gates:` frontmatter lines changed, and no gate section, script call, or prose changed `[AC-1.5]`

## Implementation Tasks

- [x] 1.1 Write tests in `scripts/tests/test_verdict_provenance.py` for the three missing-field codes, `unknown_path_value`, and an absent `path:` producing no finding `[AC-1.1, AC-1.2]`
- [x] 1.2 Extend `scripts/verdict-provenance.py` `check` to emit `missing_catches`, `missing_evidence`, `missing_kill_when`, and `unknown_path_value`, and to read the optional `path:` key. Existing codes and exit codes stay unchanged `[AC-1.1, AC-1.2, AC-1.3]`
- [x] 1.3 Write `.writ/specs/2026-11-06-lean-story-pipeline/gate-evidence.md` with one row per gate: the catch citation or `none recorded`, the dependency reason under Business Rule 3, and the path decision `[AC-1.4]`
- [x] 1.4 Add `catches:`, `evidence:`, `kill_when:`, and `path:` to each `gates:` entry in `commands/implement-story.md`, using the values recorded in `gate-evidence.md`. Change no body text `[AC-1.4, AC-1.5]`
- [x] 1.5 Run `verdict-provenance.py check` on the updated `commands/implement-story.md`. Confirm zero findings and exit 0, and confirm `test_verdict_provenance.py` passes `[AC-1.3]`
- [x] 1.6 Verify `git diff` of `commands/implement-story.md` touches only `gates:` frontmatter, and that `test_eval_verdict_provenance.sh` and `test_implement_story_default_path.py` pass `[AC-1.5]`

## Notes

- **Evidence sources.** Cite only dated artifacts that show a gate changing an outcome: `.writ/retros/2026-10-30-phase-15.md` (for example F26), `.writ/specs/2026-10-25-gate-upgrade-removal-measurement/trial-report.md`, `.writ/eval/supervisor-trial/report.md`, `.writ/specs/2026-11-06-lean-story-tasks/trial-report.md`, `gate3-review-*` records, and fix commits. "Would catch X" is not evidence (spec Business Rule 1).
- **Kept gates stay on the default path.** Safety Fact, Reviewer Filters, Gate 0 Divergence, and the ADR-032 evidence gate are not demoted. Their inputs stay too: `gate2_5_surface` (change-surface) feeds the risk route that turns Safety Fact on, so it keeps `path: default` with that dependency as its reason (Business Rule 3). Record each kept gate in `gate-evidence.md` as staying on the default path.
- **kill_when must be checkable.** Write it as a condition over `story-gate.py tally` output or a named file, for example `sole_catches == 0 over 20 default-path records`. Story 1 does not build the tally; the wording only has to be checkable later (Business Rule 7).
- **Parser.** `verdict-provenance.py` uses a line parser with no YAML library. Confirm that quoted values containing `:`, `==`, or `.` parse as plain scalars before relying on them.
- **No behavior change.** This story only declares and records. The 42 test and eval files that pin text in `implement-story.md` read the body, so frontmatter-only edits should not break them. `test_gate_upgrade_trial_outcome.py` ties kept upgrades to presence probes in that file and must keep passing.
- **Byte size.** Frontmatter additions grow `implement-story.md`. `KNOWN_OVER_BUDGET` in `scripts/tests/test_governor_enforcement.py` may need a dated entry, but the spec assigns those entries to Stories 2–5 only. If that test fails here, raise it with the maintainer before adding an entry.
- **Targeted verification only.** Run this story's test files. The full pytest suite and `eval.sh` run once at the end of the spec, not per story. Run pytest alone: `eval.sh`, bash tests, writes under `.writ/state/`, or `git worktree` changes in the same checkout during pytest break `test_smoke_leaves_repo_unchanged`.
- **Interpreters.** Targeted pytest runs must pass on Python 3.9, the floor. Stdlib only.

## Context for Agents

- **Business rules:** [Business Rule 1, Business Rule 3, Business Rule 7]
- **Error map rows:** []
- **Shadow paths:** []
- **Experience:** []

---

## What Was Built

**Implementation Date:** 2026-11-06

### Files Created

1. **`.writ/specs/2026-11-06-lean-story-pipeline/gate-evidence.md`** (58 lines)
   - One row per `gates:` entry: evidence (the frontmatter value verbatim), Business Rule 3 dependency, and path decision; Sources with full paths and commits; a Not counted section; kill conditions
2. **`scripts/tests/test_gate_evidence_drift_citation_repro.py`** (32 lines)
   - Gate 3 iteration 1 evidence repro (ADR-032), committed unchanged: the `gate3_5_drift` citation must name a drift entry that records a Gate 3 PAUSE

### Files Modified

- **`scripts/verdict-provenance.py`** (`EVIDENCE_FIELDS`, `PATH_VALUES`, `FINDING_CODES`, docstring)
  - New findings `missing_catches`, `missing_evidence`, `missing_kill_when` (absent or empty), `unknown_path_value`; absent `path:` gives no finding; existing codes, summary, and exit codes unchanged
- **`commands/implement-story.md`** (`gates:` frontmatter only)
  - Every entry gains `path`, `catches`, `evidence`, `kill_when`; `gate0_arch`, `gate4_5_behavior`, `gate5_docs` read `path: full-pipeline` (bodies unchanged until Story 2)
- **`scripts/tests/test_verdict_provenance.py`** (`GateEvidenceFieldTests`, real-file test, fixtures)
- **`scripts/tests/test_eval_verdict_provenance.sh`** (fixtures; `no-catches` and `bad-path` cases)
- **`scripts/tests/test_repro_first_wiring.py`** (`test_gate1_stays_prose_only` narrowed to the verdict-source lines; still fails if `gate1_coding` gains a `script:`)
- **`scripts/tests/test_governor_enforcement.py`** (`KNOWN_OVER_BUDGET`: `implement-story` 13591 → 16566, dated, temporary; maintainer approved 2026-11-06)
- **`cursor/plugin/commands/implement-story.md`, `plugins/writ/commands/implement-story.md`, `plugins/writ/scripts/verdict-provenance.py`** (generated by `gen-platform-trees.py`)

### Implementation Decisions

1. **Path decisions** — 3 gates have a recorded catch (`gate3_review`, `gate3_5_drift`, `gate4_tests`); 4 stay `default` under Business Rule 3 as inputs to kept gates (`gate0_5_boundary`, `gate2_5_surface`, `gate2_build`, `gate1_coding`); 3 move to `full-pipeline` (`gate0_arch`, `gate4_5_behavior`, `gate5_docs`).
2. **Gate 0 history not counted** — Gate 0's 2026-09 catches came from the architecture agent, which has run only under `--full-pipeline` since `b99c4a3`.
3. **Gate 3.5 catch is the drift pause, not `drift-format.py`** — the script's own record is one miss and false failures; Story 2 must not move the Gate 3.5 section.

### Test Results

**Verification:** Automated

- ✅ Orchestrator's recorded run (Python 3.9): 149 passed across the repro, `test_verdict_provenance.py`, `test_implement_story_default_path.py`, `test_repro_first_wiring.py`, `test_governor_enforcement.py`; `test_eval_verdict_provenance.sh` 10/10
- ✅ `verdict-provenance.py check` on the shipped file: pass, 10 entries, 0 findings
- ✅ `gen-platform-trees.py --check`: pass
- ⚠️ `test-integrity.py authenticity`: `test_imports_no_source` on the repro, recorded as a false positive by maintainer decision (drift-log DEV-005)
- Full suite and `eval.sh`: run once at spec end (`implement-spec` Step 4.1)

**Coverage:** N/A — `test-integrity.py coverage` unverifiable (no coverage report in this repo)

### Review Outcome

**Result:** PASS

- **Iteration count:** 2 iteration(s) (iteration 1 FAIL: F1, `gate3_5_drift` cited a catch Gate 3.5 did not make; confirmed by the evidence gate and recoded in `31d8c29`)
- **Gate 3 route:** `review-agent` (cross-component; 5 boundary crossings)
- **Drift:** Medium
- **Security:** Clean
- **Boundary Compliance:** Owned changes in scope; generated mirrors, the repro, and the `test_repro_first_wiring.py` narrowing justified; the `KNOWN_OVER_BUDGET` raise approved by the maintainer
- **Safety fact:** measured `tested` (claimed `tested`)
- **Evidence gate:** iteration 1 `1 confirmed`; iteration 2 `prior_ok`

### Deviations from Spec

See `drift-log.md` Story 1: DEV-001, DEV-002, DEV-004 (Small, auto-amended in spec-lite), DEV-003 (Medium, budget raise, maintainer approved), DEV-005 (Medium, Gate 4 false positive, maintainer decision).

### Lessons Learned

1. **A gate's catch must be its own** — the first `gate3_5_drift` citation was a catch the orchestrator made during Gate 1; reading the Gate 3 record, not the drift entry alone, exposed it.
2. **ADR-032 repros of data files trip `test-integrity.py authenticity`** — the extractor only sees quoted JS-style specifiers; same blind spot as the 2026-09-03 bash-test issue.

### Next Story

**Story 2:** Demote gates with no recorded catch — move `gate0_arch`, `gate4_5_behavior`, `gate5_docs` sections under `--full-pipeline`, keep Gate 3.5 § A on the default path, and bring `implement-story.md` back toward 38551 bytes.
