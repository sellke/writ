# Drift Log

> Spec: .writ/specs/2026-10-20-harness-cuts/
> Created: 2026-10-20
> ⚠️ Append-only — do not modify existing entries.

---

## Story 1: Delete the Lean Siblings and Their Install Logic — Drift Report

> Run: 2026-10-20
> Overall Drift: Small

### Deviations

#### [DEV-001] More `is_unshipped_lean_sibling` call sites removed than the inventory lists
- **Severity:** Small
- **Spec said:** Remove the definition, the command-count call, and the `overlay_scan` call in `install.sh`; the definition, the `overlay_scan` call, and the `detect_stale_files` arm in `update.sh`.
- **Implementation did:** Also removed the calls in the commands and agents loops of `write_copy_manifest` in both scripts.
- **Reason:** The dependency spec `2026-10-20-ci-and-update-integrity` added those calls after the inventory was written. Leaving them would call an undefined function.
- **Resolution:** Auto-amended
- **Spec amendment:** spec-lite.md S1 Files in Scope line names every call, including the `write_copy_manifest` loops.

#### [DEV-002] `test_manifest_shipped_baselines.sh` edited though absent from the inventory
- **Severity:** Small
- **Spec said:** The Story 1 inventory lists nine mixed tests.
- **Implementation did:** Removed the `*.lean.md` case arm from its shipped-set builder and the lean half of its AC-3.4 codex fixture. The `harness-cost.py` half stays.
- **Reason:** The dependency spec added this test after the inventory; it copied the real `implement-story.lean.md`, which AC-1.5 forbids.
- **Resolution:** Auto-amended
- **Spec amendment:** spec-lite.md S1 Files in Scope line adds `test_manifest_shipped_baselines.sh`.

#### [DEV-003] Citations for another spec added outside Files in Scope
- **Severity:** Small
- **Spec said:** Nothing.
- **Implementation did:** Added an `AC-2.2` docstring citation in `scripts/tests/test_gen_claude_agents.py` and an `AC-2.4` comment in `scripts/tests/test_jev_shadow_hooks.sh`, both for `2026-10-20-claude-agent-generator`.
- **Reason:** The deleted `test_lean_preamble.py` held bare `AC-2.2`/`AC-2.4` tokens that `ac-trace.py` credited to that spec. Without new citations eval reports 3 `review-override:untested_criterion` findings (Business Rule 11). The reviewer confirmed both cited tests verify those criteria.
- **Resolution:** Auto-amended
- **Spec amendment:** spec-lite.md S1 line records the two citations.

#### [DEV-004] AC-1.5 gets its own tests
- **Severity:** Small
- **Spec said:** Task 1.1 writes tests for AC-1.1 to AC-1.4; AC-1.5 is checked by suite runs.
- **Implementation did:** Added four AC-1.5 tests to `test_harness_cuts.py`: the lean-only tests are deleted, the mixed tests and the two eval checks name no lean file, and the mixed tests still exist.
- **Reason:** `ac-trace.py` needs a test citation for every criterion once the story is Completed; without one eval reports `untested_criterion` (Gate 3 iteration 1 FAIL).
- **Resolution:** Auto-amended
- **Spec amendment:** spec-lite.md S1 line records the AC-1.5 absence tests.
