# Product Consistency Report

> **Date:** 2026-10-02
> **Mode:** `--product` (default)
> **Trigger:** post-release check after v0.40.0 (Phase 12 merged in PR #56)
> **Result:** ⚠️ Passed with warnings: authoritative drift found (P1)

## Summary

| Check | Status | Details |
|-------|--------|---------|
| P1. Phase-status parity | ❌ | `roadmap.md`: Phase 12 "◐ Implemented, pending human UAT". `mission.md` Key Features: "Phase 12 (📋 committed)"; Next Horizon: "Phase 12 is committed". |
| P2. ADR reference resolution | ✅ | Every ADR referenced in mission, roadmap, and mission-lite resolves under `.writ/decision-records/` |
| P3. Derivative freshness | 🔧 | `mission-lite.md` regenerated. `.writ/context.md` is rewritten by the `/status` run that follows this check. |
| P4. Shipped-claim sanity | ✅ | Every spec marker in the roadmap's condensed history resolves to an active or archived spec folder; shipped phase versions have changelog entries |

## Regenerated

- `.writ/product/mission-lite.md`: the Current Phase section said "through v0.39.0" and "Phase 12 … committed, not started". It now records v0.40.0 product-check direction, and describes Phase 12 as implemented and released in v0.40.0, pending human UAT, with the panel trial verdict `keep`. Status is taken from `roadmap.md`, which is authoritative for phase status. Other sections are unchanged in substance.

## Outstanding (needs human judgment)

- **[P1] Phase 12 status in `mission.md`.** The Key Features heading `### Phase 12 — Behavioral Verification (📋 committed)` and the Next Horizon sentence "Phase 12 is committed" lag `roadmap.md` and the v0.40.0 release. Run `/plan-product --reconcile` to realign; it decides whether Phase 12 reads "implemented, pending human UAT" or closes after UAT.
- **[P1, related] `mission.md` Phase 11 bullet.** "Gate 1 and Gate 4.5 stay `prose-only`" was true at Phase 11 close, but Gate 4.5 is now behavioral verification. Reconcile decides whether the Phase 11 block stays a historical record or gets a forward note.
- **[P4, inverse] Phase 12 success criteria in `roadmap.md`.** Criterion 4 (panel) is marked met. Criteria 1–3 (fixture app UAT with machine evidence; Gate 4.5 leaves `prose-only`; `exit-criteria.py` mutation proof) are unmarked, although the behavioral-verification spec is Complete and shipped in v0.40.0. Confirm each against the spec evidence before marking.
- **Roadmap header date.** "Current status (2026-10-01)" describes 2026-10-02 state and doesn't mention the v0.40.0 release. Cosmetic; fold into the reconcile pass.

## Notes

`mission.md` and `roadmap.md` were not modified. Verification surfaces drift after implementation; `/plan-product --reconcile` realigns the baseline when it does.
