# Dev-Only Governance Docs Ship to Every Installed Project

> **Type:** Improvement
> **Priority:** Normal
> **Effort:** Small
> **Created:** 2026-10-21
> **spec_ref:** _(set automatically when promoted via `/create-spec --from-issue`)_

## TL;DR

`install.sh` and `update.sh` copy every `.writ/docs/*.md` file except the recommended-delivery state doc. Writ's own leanness audits, its SWOT, and its explanations are not useful in a user's project, but they ship there anyway.

## Current State

- `is_shippable_writ_doc` in `scripts/install.sh` and `scripts/update.sh` rejects only `recommended-delivery-state-format.md`. Phase 13's harness-cuts spec added it.
- Shipped dev-only records include `.writ/docs/leanness-audit-2026-07-11.md`, `-07-18.md`, `-10-21.md`, and `swot-2026-03-01.md`. `.writ/explanations/2026-03-20-WritPipelineArchitecture .md` is also named as a shipped snapshot in the platform-neutral-names spec.
- The leanness audit format (`.writ/docs/leanness-audit-format.md`) requires the audit at `.writ/docs/leanness-audit-YYYY-MM-DD.md`, so every audit adds a shipped file.
- Found by the 2026-10-21 Tier B audit.

## Expected Outcome

- Dev-only records are excluded from the docs ship set by pattern (for example `leanness-audit-2*.md`, `swot-*.md`), and update removes unmodified copies from existing installs as stale.
- Alternatively, the audit format writes audits outside `.writ/docs/`, for example under `.writ/product/` beside other dogfooding records.
- A test fails when a dated dev-only record would ship.

## Relevant Files

- `scripts/install.sh`, `scripts/update.sh`: `is_shippable_writ_doc` (byte-identical)
- `.writ/docs/leanness-audit-format.md`: Output Contract path
- `scripts/tests/test_install_update_harness_cuts.sh`: the stale-removal test pattern
