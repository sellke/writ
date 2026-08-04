# Story 2: Leanness Audit Ritual (Tier B cadence)

> **Status:** Complete
> **Priority:** Medium
> **Dependencies:** Story 1

## User Story

As the **Writ maintainer**, I want a repeatable, cadence-bound audit ritual that
re-applies the "does the harness do this natively now?" test and surfaces prune
candidates, so that strategic leanness is a scheduled discipline rather than a
lucky observation.

## Acceptance Criteria

1. **Given** the Tier A metrics exist, **when** I open
   `.writ/docs/leanness-audit-format.md`, **then** it defines inputs, a judgment
   checklist (native displacement, overlap, existence justification, prune
   candidates), an output contract, and a cadence (per-phase-close/quarterly,
   never per-release).
2. **Given** the template, **when** I run the first audit, **then**
   `.writ/docs/leanness-audit-2026-07-11.md` exists with findings → decisions →
   follow-ups (dogfood proof).
3. **Given** `self-dogfooding.md`, **then** it carries a "Leanness cadence"
   subsection pointing to the template and stating the trigger.
4. **Given** the audit, **then** it recommends only — it deletes no surface
   automatically; decisions route to ADR/roadmap/issues.

## Implementation Tasks

- [x] 2.1 Create `.writ/docs/leanness-audit-format.md` — the ritual template
      (inputs, judgment checklist, dated output contract, cadence).
- [x] 2.2 Run the ritual against the current repo; write the first dated audit
      `.writ/docs/leanness-audit-2026-07-11.md` using real Tier A metrics.
- [x] 2.3 Add a "Leanness cadence" subsection to `.writ/docs/self-dogfooding.md`.
- [x] 2.4 Add a Leanness Guardian entry to `.writ/product/roadmap.md`.

## Technical Notes

- Template consumes Story 1's `--check=leanness` metrics output as an input.
- Precedent for a dated strategic doc: `.writ/docs/swot-2026-03-01.md`; the 2026
  harness audit that produced ADR-010–013 is the ad-hoc version of this ritual.
- Cadence lives as documented discipline — it must **not** hook into any shipping
  command (e.g. `/release`, `/implement-phase`), which would leak to users.

## Definition of Done

- [x] All acceptance criteria pass.
- [x] Template + first dated audit committed.
- [x] `self-dogfooding.md` cadence note and roadmap entry committed.
- [x] Ritual adds zero user-facing surface.

## What Was Built

**Tier B leanness audit ritual — cadence-bound maintainer judgment layer.**

- `.writ/docs/leanness-audit-format.md` — the reusable template. Defines: **when
  to run** (per-phase-close or quarterly, never per-release, never hooked into a
  shipping command); **inputs** (Tier A metrics via `python3 scripts/eval-leanness.py`
  or the `--check=leanness` Notes block, baseline delta, manifest, adapters,
  recent harness changes); a **judgment checklist** (a: native displacement /
  Principle #4, b: command overlap, c: existence justification, d: prune
  candidates); and an **output contract** (dated `leanness-audit-YYYY-MM-DD.md`
  with a findings→decisions table where decision ∈ {keep, prune, merge, defer}
  and every non-`keep` routes to an ADR/roadmap/issue). Recommend-only.
- `.writ/docs/leanness-audit-2026-07-11.md` — first dated audit (dogfood proof),
  produced from the template against the real repo (metrics 31/7/6, 10,659 lines,
  0 structural, 0 warnings, 0% baseline drift). Honest result: mostly **keep**,
  one **defer** watch item (`/research` vs. native agentic search).
- `.writ/docs/self-dogfooding.md` — new "Leanness Cadence" subsection pointing to
  both tiers and stating the trigger.
- `.writ/product/roadmap.md` — "Self-Governance: Leanness Guardian" entry
  (flagged dogfooding-only, does not ship to users).

**Zero user-facing surface:** no `commands/*.md`, no manifest command/agent
change, no `/status` allowlist change.
