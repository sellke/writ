# Product Reconciliation (Lite)

> Source: .writ/specs/2026-07-11-product-reconciliation/spec.md
> Purpose: Efficient AI context for implementation

## For Coding Agents

**Deliverable:** Three mode additions to existing commands so a Writ project can
re-verify and revise its product layer. User-facing (ships to users).

**Implementation Approach:**
- Story 1: `/verify-spec --product` — new mode in `verify-spec.md`, a SEPARATE
  ~4-check set over mission ↔ roadmap ↔ mission-lite ↔ .writ/context.md. Hybrid
  auto-fix (regen derivatives; report-only authoritative divergence).
- Story 2: `/plan-product --reconcile` — revision posture in `plan-product.md`:
  scan existing docs → diff vs reality (shipped specs, roadmap statuses, git) →
  propose targeted revisions (Plan Mode). Not greenfield.
- Story 3: `/retro` nudge — read-only step mirroring retro Step 5.5.

**Files in Scope:**
- `commands/verify-spec.md` — add --product mode
- `commands/plan-product.md` — add --reconcile posture
- `commands/retro.md` — add product-drift nudge
- `.writ/product/roadmap.md` — entry

**Boundary (critical):** --product = consistency lint (before); --reconcile =
revision (after). State + cross-reference in both files. --product uses its OWN
checks, NOT spec checks 1–7.

## For Review Agents

**Acceptance Criteria:**
1. `/verify-spec --product` flags current live drift (mission "Phase 6 (next)"
   vs roadmap complete).
2. verify-spec.md: mode in Modes table + Product Consistency section; auto-fix
   (derivatives) vs report-only (authoritative) explicit; boundary vs --reconcile.
3. plan-product.md: --reconcile = scan→diff→propose, distinct from greenfield.
4. retro.md: read-only nudge, silent with no signal.
5. No new command files; /status allowlist untouched.

**Business Rules:**
- Hybrid auto-fix: regen mission-lite/context; report-only on mission↔roadmap.
- --product check set separate from spec checks 1–7.
- Nudge is read-only, skips silently (identical to Step 5.5 contract).
- --reconcile proposes in Plan Mode; new ADRs only for direction changes.

## For Testing Agents

**Success Criteria:**
1. --product detects phase-status mismatch across mission/roadmap.
2. Derivative-freshness check regenerates mission-lite/context; authoritative
   divergence is reported, not silently rewritten.
3. Nudge prints nothing when product docs are consistent.

**Shadow Paths to Verify:**
- Consistent docs → --product PASS; retro nudge silent.
- Phase mismatch → --product reports (no auto-rewrite of mission/roadmap).
- Missing ADR reference → --product reports.
- Stale mission-lite → --product auto-regenerates it.

**Edge Cases:**
- No `.writ/product/` → --product skips gracefully.
- Missing `.writ/context.md` → treat as derivative to (re)generate, not an error.
