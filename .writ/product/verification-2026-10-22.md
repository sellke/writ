# Product Consistency Report

> **Date:** 2026-10-22
> **Mode:** `--product` (default)
> **Trigger:** post-UAT check after v0.43.0 (Phase 13) shipped and its 176 UAT scenarios were run. The UAT records are on `docs/phase-13-uat`, PR #61, not yet merged.
> **Result:** ⚠️ Passed with warnings. Mission and roadmap agree with each other (P1 ✅), but both lag reality on Phase 13 (P4): they still say "unreleased" and "UAT handed off".

## Summary

| Check | Status | Details |
|-------|--------|---------|
| P1. Phase-status parity | ✅ | Both files label Phase 12 "implemented and released, human UAT open", Phase 13 "implemented, pending human UAT, unreleased", and Phases 14–16 "committed". They agree. The Phase 13 label is stale in both; see P4. |
| P2. ADR reference resolution | ✅ | All distinct ADR ids resolve under `.writ/decision-records/`: 16 in mission, 20 in roadmap, 9 in mission-lite. |
| P3. Derivative freshness | 🔧 | `.writ/context.md` regenerated. It placed Phase 13 on the phase branch, and its knowledge and issue counts were stale. `mission-lite.md` matches `mission.md`, so it was not changed; it inherits the P4 staleness. |
| P4. Shipped-claim sanity | ⚠️ | Every shipped claim has evidence. The new row, Claude Agent Generator v0.43.0, matches CHANGELOG `[0.43.0]`. Three facts run the other way: built, released, or measured, but not recorded (below). |

## Regenerated

- `.writ/context.md`, full rewrite per `/status` Step 8:
  - Active Spec: Phase 13 shipped in v0.43.0, with its UAT result.
  - Knowledge count: 24 (was 23).
  - Open issues: 27 of 38 (was 22 of 33).
  - Recent Drift: unchanged.

## Outstanding (needs human judgment)

### Phase 13 status (P4, inverse)

1. **Phase 13 is released, but the docs say "unreleased".**
   - Evidence: tag `v0.43.0`, `VERSION` 0.43.0, and CHANGELOG `[0.43.0] - 2026-10-21`.
   - Stale lines:
     - `roadmap.md` line 7, the Current status: "integrated on `phase/13-subtract-and-repair`, unreleased"
     - `roadmap.md` line 584, the Closure status: "(unreleased)"
     - `mission.md` line 182, the Phase 13 heading: "unreleased"
     - `mission.md` line 210, Next Horizon: "on an unreleased branch"
   - `roadmap.md` contradicts itself: its own Claude Agent Generator row already says v0.43.0.
2. **The first CI run has happened.**
   - Phase 13 success criterion 2 (`roadmap.md` line 597) still says "⚑ the first GitHub Actions run awaits a push".
   - Evidence: PR #60 run `39678517441` passed on 2026-10-21. Throwaway-branch run `39795856168` failed on 2026-10-22, as designed, which proves CI goes red (ci S8).
3. **Phase 13 UAT has run.** The docs say "176 UAT scenarios … handed off". The result is 172 Pass, 2 Fail, and 2 not runnable here.
   - **names S9 (Fail):** headless `claude -p` falsely said the Claude Code adapter "doesn't define canvas-preview". Installed projects get no `adapters/` folder. This is the open issue `2026-10-21-adapter-mappings-never-reach-installed-projects`, which Phase 14's generated per-platform trees could cover.
   - **hygiene S29 (Fail):** `/create-spec` asked to lock a contract it never displayed. The maintainer confirmed this. Phase 13 claimed its `create-spec` cut had no behavior change, so this failure counts against a Phase 13 deliverable. Bug `2026-10-22-create-spec-can-lock-an-unseen-contract` is filed, and a fix is in progress in a separate session.
   - **names S12, S13:** need OpenClaw, so they were not runnable here.

**Decision for `/plan-product --reconcile`:** close Phase 13 with the two failures tracked as issues, or keep it open until the S29 fix lands and S29 passes on a re-run. Closing would also add a Phase 13 row to the condensed history; Phase 11 got its row when it closed. S29 is a regression in a Phase 13 deliverable, so keeping Phase 13 open until the fix lands is the more honest record.

### Unchanged since 2026-10-21

- Phase 12's human UAT is still open, and Phase 16 is still gated on it. Both files say so consistently.

## Outcome

The same day, the maintainer chose to fix S29 before closing. The fix (PR #62) passed a live re-run, and S29 is marked Pass. The `/plan-product --reconcile` pass then closed Phase 13, which resolves P4 items 1–3 (see the roadmap Revision Log, 2026-10-22).

## Notes

- `mission.md` and `roadmap.md` were not modified by this check.
- This report and the regenerated `context.md` are on `docs/phase-13-uat`. They describe UAT records that reach `main` only when PR #61 merges.
- Verification surfaces drift after implementation; `/plan-product --reconcile` realigns the baseline when it does.
