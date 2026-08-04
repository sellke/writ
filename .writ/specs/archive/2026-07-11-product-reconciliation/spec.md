# Spec: Product Reconciliation

> **Status:** Complete
> **Created:** 2026-07-11
> **Owner:** @adam
> **Type:** Product feature (ships to all Writ users)

## Contract Summary

Three coordinated additions that let any Writ project re-verify and revise its
**product layer** the way it already does for specs:

- **`/verify-spec --product`** — a consistency linter over the product docs.
- **`/plan-product --reconcile`** — a revision posture that diffs docs vs reality.
- **`/retro` product-drift nudge** — a read-only advisory when drift is detected.

**Deliverable:** Close the gap where Writ can verify and revise a *spec* but has
no equivalent for the *product* layer, even though mission/roadmap drift silently
across the four files that describe strategy.

**Hardest Constraint:** `/verify-spec --product` and `/plan-product --reconcile`
both read the product docs — their boundary must be crisp (consistency-check
*before* vs revision *after*), or they blur the way `assess-spec`/`verify-spec`
could have.

## Why This, Why Now

The strategic layer drifts and nothing catches it. Live example at time of
writing: `roadmap.md` (updated 2026-07-11) marks Phases 6–7 **complete** and
Phase 8 **implemented**, while `mission.md` (updated 2026-07-10, one day apart)
still lists under Key Features:

```
### Phase 6 — Autonomy Ceiling (next)
```

`mission-lite.md` and `.writ/context.md` are derived from these and are read on
nearly every agent run — so the strategy an agent orients against is already
stale, updated in one file and forgotten in three. Writ has `/verify-spec` and
`/assess-spec` for specs but no product-level analog; this spec adds the missing
before/after pair plus a nudge.

## Boundary Discipline (the core risk)

| Mode | Question | When |
|---|---|---|
| `/verify-spec --product` | "Is the product layer internally consistent and true to reality?" | Lint, anytime |
| `/plan-product --reconcile` | "Is it still the *right* plan? Revise it." | After deciding to change |

Each command file must state this boundary and cross-reference the other — the
same discipline that keeps `assess-spec` (before) and `verify-spec` (after)
distinct. `--product` runs its **own** small check set — **not** spec checks 1–7
pointed at product docs.

## Scope Boundaries

**Included:**
- `commands/verify-spec.md` — add `--product` mode + Product Consistency checks.
- `commands/plan-product.md` — add `--reconcile` posture.
- `commands/retro.md` — add read-only product-drift nudge step.
- `.writ/product/roadmap.md` — add a roadmap entry.

**Excluded:**
- Any new command file (mode additions only).
- Any `scripts/` or eval change.
- The **leanness guardian** (`2026-07-11-leanness-guardian`) — separate
  dogfooding spec; complementary, no file overlap.
- Auto-editing *authoritative* mission/roadmap prose (only derivatives regen).
- `commands/status.md` changes — the nudge lives in `/retro` by decision.

## Business Rules

- **`/verify-spec --product` hybrid auto-fix:** regenerate derivatives
  (`mission-lite.md`, `.writ/context.md`) from `mission.md`; **report-only** on
  authoritative divergence (mission ↔ roadmap phase status — human decides which
  is right). Mirrors verify-spec's spec-lite regen (auto) vs Check 4/6
  (report-only).
- **`--product` check set is separate** from spec checks 1–7.
- **`/retro` nudge is read-only:** mutates nothing, skips silently with no
  signal — identical contract to retro Step 5.5 (knowledge-consolidation nudge).
- **`--reconcile` proposes, the human disposes:** revisions are presented in Plan
  Mode; new ADRs only for genuine direction changes.

## The `--product` Check Set (~4 checks)

1. **Phase-status parity** — a phase marked complete/shipped in `roadmap.md` but
   labeled "next"/planned in `mission.md` (or vice versa). → report-only.
2. **ADR reference resolution** — every `adr-0NN` referenced in mission/roadmap
   resolves to a file in `.writ/decision-records/`. → report-only (missing file
   is a real bug worth human eyes).
3. **Derivative freshness** — `mission-lite.md` and `.writ/context.md` reflect
   current `mission.md` (core value, current phase). → auto-fix (regenerate).
4. **Shipped-claim sanity** — a roadmap feature marked shipped/complete has
   plausible evidence (a matching spec folder or changelog entry). → report-only,
   heuristic.

Cap at ~4. Resist mirroring all seven spec checks onto product docs.

## Success Criteria

1. `/verify-spec --product` flags the current live drift (mission "Phase 6
   (next)" vs roadmap complete).
2. `verify-spec.md` documents the mode in the Modes table + a Product Consistency
   section, with the auto-fix (derivatives) vs report-only (authoritative) split
   explicit and the boundary vs `--reconcile` stated.
3. `plan-product.md` documents `--reconcile` as scan → diff → propose, clearly
   distinct from greenfield, with the boundary vs `--product` stated.
4. `retro.md` gains the read-only nudge; silent with no signal.
5. Roadmap entry added.
6. **No new command files**; `/status` allowlist untouched (all three commands
   already listed).

## Deliverables Checklist

- [x] `commands/verify-spec.md` — `--product` mode + check set + boundary note
- [x] `commands/plan-product.md` — `--reconcile` posture + boundary note
- [x] `commands/retro.md` — product-drift nudge step (mirrors Step 5.5)
- [x] `.writ/product/roadmap.md` — product-reconciliation entry
