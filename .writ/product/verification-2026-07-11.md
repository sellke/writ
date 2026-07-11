# Product Consistency Report

> **Date:** 2026-07-11
> **Scope:** `.writ/product/` + `.writ/context.md` (`/verify-spec --product`, default mode)
> **Result:** ⚠️ Authoritative drift found (P1) — no derivatives needed regeneration; P1 needs human judgment

## Summary

| Check | Status | Findings |
|-------|--------|----------|
| P1. Phase-status parity (mission ↔ roadmap) | ❌ | `mission.md` is a full phase behind `roadmap.md` (Phases 6–8) |
| P2. ADR reference resolution | ✅ | All 10 referenced ADRs resolve |
| P3. Derivative freshness | ✅ | `mission-lite.md` + `context.md` mission content faithful to `mission.md` — nothing regenerated |
| P4. Shipped-claim sanity | ⚠️ | All shipped claims have matching specs; roadmap says "✅ Complete/Shipped" while closure prose says "pending `/release`" |

**Overall:** ⚠️ Authoritative drift (P1) — a human resolves via `/plan-product --reconcile`. Nothing auto-fixed: the derivatives aren't the problem, the authoritative `mission.md` is.

---

## P1 — Phase-Status Parity (report-only) ❌

`mission.md` (`> Last Updated: 2026-07-10`) frames its "Key Features" as forward-looking while `roadmap.md` (`> Last Updated: 2026-07-11`) marks the same phases done:

| Phase | `mission.md` Key Features label | `roadmap.md` status |
|---|---|---|
| Phase 6 — Autonomy Ceiling | **"(next)"** | **✅ Complete (2026-07-10)** |
| Phase 7 — Compounding Layer | *(no label — presented as upcoming)* | ✅ Complete (2026-07-11) |
| Phase 8 — Memory Interop | *(no label — presented as upcoming)* | IMPLEMENTED, pending validation (2026-07-11) |

The starkest divergence: `mission.md` line 103 heading `### Phase 6 — Autonomy Ceiling (next)` vs `roadmap.md` line 42 `## Phase 6: Autonomy Ceiling — ✅ Complete`. `mission.md` never advanced as Phases 6→8 shipped; it stopped at the 2026-07-10 strategic refresh.

This is the exact drift `2026-07-11-product-reconciliation` was built to catch (its motivating example, verbatim: "roadmap marked Phases 6–7 complete while mission still framed Phase 6 as 'next'").

> **Disposition: report-only.** `--product` never rewrites authoritative `mission.md`/`roadmap.md` prose. Resolve with `/plan-product --reconcile`, which decides *which* file is right (they aren't in dispute here — the phases genuinely shipped; `mission.md` is simply behind) and revises `mission.md`'s Key Features accordingly.

---

## P2 — ADR Reference Resolution (report-only) ✅

All ADR ids referenced in `mission.md`, `roadmap.md`, and `mission-lite.md` resolve to files under `.writ/decision-records/`:

`adr-005`, `adr-006`, `adr-007`, `adr-008`, `adr-010`, `adr-011`, `adr-012`, `adr-013`, `adr-014`, `adr-015` — all present. No dangling references.

---

## P3 — Derivative Freshness (auto-fix) ✅ — nothing regenerated

- **`mission-lite.md`** (`> Last Updated: 2026-07-10`) — faithful to `mission.md`. Same core value, same six differentiators, same "Current Phase" framing (including the same "Phase 6 (next)"). Because it mirrors its authoritative source, there is **no derivative divergence to fix** — the staleness lives upstream in `mission.md` (see P1). Regenerating would only reproduce the same "(next)" framing.
- **`.writ/context.md`** — its Product Mission blurb matches `mission.md`'s core value (no mission-fidelity divergence, so no P3 trigger). It does **not** cite a phase, so the "superseded phase" trigger does not fire.

**No files were regenerated.** The correct fix for the observed drift is the P1 human resolution, not a derivative rewrite.

### Outstanding (not a `--product` fix — `/status`-owned)

`.writ/context.md` is a stale *status snapshot* on axes `--product` does not own:
- `> Last Updated: 2026-07-10T19:30:00Z` (predates the 2026-07-11 shipped work)
- **Active Spec:** points to `2026-07-10-recommended-autonomous-delivery` (superseded by four specs completed 2026-07-11)
- **Open Issues:** says 14; actual count is 16

These are `/status` Step 8 fields, not `mission.md`-derived facts. Run `/status` to regenerate `context.md` authoritatively (it resolves the active spec correctly). `--product` deliberately does not guess an active spec.

---

## P4 — Shipped-Claim Sanity (report-only, heuristic) ⚠️

Every roadmap shipped/complete claim has a plausibly matching spec folder:

| Roadmap claim | Matching spec evidence |
|---|---|
| Phase 6 — Autonomy Ceiling | `2026-07-09-phase6-autonomy-ceiling` (Complete) |
| Phase 7 — Compounding Layer | `2026-07-10-skill-lifecycle`, `-skill-extraction`, `-evidence-bound-refresh-command`, `-knowledge-consolidation` |
| Phase 8 — Memory Interop | `2026-07-11-gbrain-compatibility-recipe`, `2026-07-11-native-memory-guidance` |
| Leanness Guardian (Shipped) | `2026-07-11-leanness-guardian` (Complete) |
| Product Reconciliation (Shipped) | `2026-07-11-product-reconciliation` (Complete) |
| Shipped history (1–4, 3a/3b, skills, codex) | corresponding spec folders present |

**Heuristic note (worth a glance, not a failure):** the roadmap marks Phases 6–8 and Product Reconciliation with "✅ Complete/Shipped", but each phase's own closure prose says "not merged to main / pending `/release`". "Shipped" in the table vs "pending release" in the body is a mild internal-consistency wrinkle a human may want to reconcile at `/release` time. Product Reconciliation's spec files are also still untracked on branch `feat/leanness-guardian`.

---

## Notes

Consistency lint only (the *before*). To act on P1, run [`/plan-product --reconcile`](../../commands/plan-product.md) (the *after*). To refresh the stale `context.md` snapshot, run `/status`.
