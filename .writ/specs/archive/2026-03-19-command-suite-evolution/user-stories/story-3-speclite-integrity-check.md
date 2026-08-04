# Story 3 — Spec-Lite Integrity Check

> Status: Completed ✅
> Priority: High
> Dependencies: None

## User Story

As a Writ maintainer, I want `verify-spec` to compare `spec-lite.md` against authoritative `spec.md` (with an optional full regeneration path) so that condensed spec-lite cannot silently diverge from the source of truth after flows like `implement-story` auto-amend spec-lite on Small drift.

## Acceptance Criteria

**Given** `commands/verify-spec.md` after this story
**When** a reader reviews the check suite description
**Then** Check 9 is listed alongside existing checks (Checks 1–5 and 8), and its purpose — spec-lite integrity vs `spec.md` — is clear.

**Given** a spec folder containing both `spec.md` and `spec-lite.md`
**When** Check 9 runs
**Then** it compares the key sections **What**, **Constraints**, **Success Criteria**, and **Files in Scope** in spec-lite to the corresponding sections in `spec.md` and evaluates material divergence (not cosmetic-only noise).

**Given** Check 9 detects material divergence between spec-lite and `spec.md`
**When** the verification report is produced
**Then** the report explicitly flags the divergence (which sections or a clear summary) so maintainers can act without re-reading both files side by side.

**Given** the agent invokes verify-spec with `--fix` (or equivalent documented flag) for Check 9
**When** fix mode runs
**Then** `spec-lite.md` is fully regenerated from `spec.md` (not a partial patch), and the regenerated file includes a clear marker such as **regenerated from spec.md on [date]** so provenance is obvious.

## Implementation Tasks

- [x] Write an AC verification checklist first: sample `spec.md` / `spec-lite.md` pairs (aligned, drifted per section, edge cases), expected Check 9 outcomes, and expected `--fix` output including the regeneration marker — use it as the test plan for these markdown-only changes.
- [x] Update `commands/verify-spec.md` to add **Check 9** to the documented check suite (numbering consistent with Checks 1–5, 8, and 9; no reintroduction of absent Checks 6–7 unless explicitly out of scope).
- [x] In Check 9 instructions, define how each key section in spec-lite maps to the corresponding `spec.md` section and what counts as **material divergence** vs ignorable formatting.
- [x] Specify the verification report shape for Check 9 (pass, fail, and how divergences are listed) so agents emit consistent, scannable output.
- [x] Document the **`--fix`** behavior for Check 9: full regeneration of `spec-lite.md` derived only from `spec.md`; forbid partial or hand-edited merge semantics in fix mode.
- [x] Require the regenerated `spec-lite.md` to carry an unambiguous regeneration line (e.g. regenerated from spec.md on [date]) at a stable, visible location per command conventions.
- [x] Walk the verification checklist against `commands/verify-spec.md` and at least one real spec folder; confirm every AC passes and wording matches `implement-story.md` assumptions about spec.md vs spec-lite roles.

## Technical Notes

- **Source of truth:** `spec.md` is authoritative; `spec-lite.md` is a derivative kept under ~100 lines for AI context. Check 9 closes the gap where spec-lite can drift over time without a dedicated verifier.
- **Context:** `implement-story.md` may auto-amend spec-lite on Small drift without editing `spec.md`; Check 9 is the backstop that detects when the derivative no longer reflects the contract in `spec.md`.
- **Scope:** Edits to existing markdown command docs only (no runtime code). Align paths with the product layout (`commands/verify-spec.md` as shipped in the Writ repo).
- **Fix semantics:** `--fix` means **replace** spec-lite content by regenerating from `spec.md`, not patching individual sentences; partial updates risk leaving hidden inconsistency.
- **Sections under comparison:** At minimum **What**, **Constraints**, **Success Criteria**, and **Files in Scope**; if headings differ slightly between files, the command text should tell the agent how to resolve headings (normalize or map explicitly).

## Definition of Done

- [x] All tasks complete
- [x] All AC verified
- [x] Tests passing
- [x] Code reviewed
- [x] Docs updated if needed
