# Phase 6 Acceptance Evidence — Disposable Multi-Spec Sandbox

> **Scope:** MECHANICAL only. Captured by driving `scripts/phase-state.py`
> end-to-end against a throwaway git repository (removed on exit). Proves the
> integrated Story 1-6 behaviour. **Does not** close the roadmap's real-use
> User Challenge criterion — see "Pending" below.

**Result:** 17/17 mechanical checks passed.

## Sandbox shape

- Phase branch `phase/6`, specs `a,b,c,d,e`.
- Declared dependencies: `b → a`, `d → c`.
- `c` fails terminally (quarantined); `d` (its dependent) is blocked; `a`, `b`, `e` succeed and merge.

## Checks

| # | Check | Result |
|---|-------|--------|
| 1 | fresh-lane-merge-spec-a | ✅ PASS |
| 2 | dependency-ordered-merge-spec-b (b depends on a) | ✅ PASS |
| 3 | terminal-failure-classified-quarantine | ✅ PASS |
| 4 | quarantine-preserves-failed-lane | ✅ PASS |
| 5 | quarantine-keeps-phase-branch-clean | ✅ PASS |
| 6 | dependent-blocked | ✅ PASS |
| 7 | blocked-dependent-status-skipped_blocked | ✅ PASS |
| 8 | independent-spec-continues (e) | ✅ PASS |
| 9 | resume-reconcile-consistent | ✅ PASS |
| 10 | resume-reconcile-reports-mismatch-read-only | ✅ PASS |
| 11 | progress-counts-report | ✅ PASS |
| 12 | user-challenge-validates-four-parts | ✅ PASS |
| 13 | user-challenge-recorded-unresolved | ✅ PASS |
| 14 | user-challenge-resolved-by-selected-option | ✅ PASS |
| 15 | health-healthy-when-all-pass | ✅ PASS |
| 16 | health-warning-when-evidence-missing | ✅ PASS |
| 17 | health-attention-on-current-failure | ✅ PASS |

## Pending (not provable in a sandbox)

- **Real-use User Challenge criterion.** This run renders and resolves the
  four-part challenge contract mechanically. It does **not** demonstrate that a
  genuine phase run surfaced a real scope/exit-criteria decision to a human. That
  observation remains **PENDING** until a real `/implement-phase` run supplies it.

## Reproduction

Run `python3 /tmp/uat_phase6.py <evidence-path>` (driver is disposable and not
committed to active product discovery; the git sandbox is created and removed
within the run).
