# Story 2 Verification Checklist

> **Story:** [Spec Frontmatter `owner:` Field](../story-2-spec-owner-field.md)
> **Date:** 2026-04-24
> **Result:** Passed with manual verification

## Acceptance Criteria

- [x] `/create-spec` documents `owner:` generation in `spec.md` frontmatter using `git config user.name`, `@` prefixing, and space stripping.
- [x] `/create-spec` documents the unset-name fallback: write `owner: @unknown` and warn with `git config user.name 'Your Name'`.
- [x] `/verify-spec` documents Check 8 for new specs created on or after `2026-04-24`, with WARN-only behavior and opt-in backfill.
- [x] `/verify-spec` documents legacy specs created before `2026-04-24` as `legacy — owner not required` with no warning.
- [x] `/status` documents an Owner column/value for active specs and displays `—` when owner metadata is absent.

## Manual Checks

- [x] Confirmed current repo `git config user.name` resolves to `Adam Sellke`; the documented default would render as `@AdamSellke`.
- [x] Confirmed the Phase 4 spec header already includes `Owner: @adam`, satisfying self-dogfood for this in-flight spec.
- [x] Scanned `.writ/specs/*/spec.md`: the only spec dated `2026-04-24` is the Phase 4 spec and it has owner metadata; older specs without owner metadata classify as legacy.
- [x] Confirmed the Phase 4 spec has no first-add git commit yet because it is still untracked; Check 8 documentation includes the required `git log --diff-filter=A --format=%aI -- {spec.md} | tail -1` path plus an uncommitted-spec fallback.
- [x] Confirmed no legacy spec migration or automatic backfill was added.

## Notes

This repository has no application build or automated test suite. Verification is therefore a documentation-command smoke pass against the markdown surfaces owned by Story 2.
