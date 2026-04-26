# Phase 4 Spec Changelog

> **Spec:** `.writ/specs/2026-04-24-phase4-production-grade-substrate/`
> Records material edits applied via `/edit-spec`.

---

## 2026-04-26 — Cleanup + completion roll-up

**Type:** Cleanup + status reframe (no scope change).

**Why:** `/verify-spec` and the `verification-2026-04-24.md` report flagged two presentational drifts:
1. `story-N-verification.md` files collided with the broad `story-N-*.md` glob used by tooling.
2. The status vocabulary overloaded "In Progress" — used both for active work and for implementation-complete-with-deferred-validation states.

**Changes:**

- **Verification files relocated.** All five `user-stories/story-N-verification.md` files moved to `user-stories/verification/story-N.md`. Story contracts and verification checklists no longer share a glob.
- **Story 1 → `Completed ✅`.** AC3 reframed: implementation-side validation is verified locally (knowledge-loading hook, grep selection, `knowledge_context` parameter routing); the *organic* dogfood proof (an agent loading a backfilled entry without prompt-side mention on a future feature) is tracked at `.writ/issues/improvements/2026-04-26-story-1-knowledge-loading-organic-validation.md`. The 90-day ADR-005 review remains the formal recheck trigger.
- **Story 5 → `Completed ✅`.** AC4 + Task 5.7 reframed: the workflow file (`.github/workflows/eval.yml`) is committed and structurally sound; *first future PR* validates the remote CI gate organically. Tracked at `.writ/issues/improvements/2026-04-26-story-5-remote-ci-gate-organic-validation.md`.
- **Spec status → `Completed ✅`.** All five stories now `Completed ✅`.
- **"Ongoing dogfooding" language removed from this spec.** Phase-entry condition restated past-tense ("Phase 1 features dogfooded and stable") in `spec.md` and `user-stories/README.md`. Mission/roadmap untouched — the operating-practice narrative legitimately lives there.
- **`verification-2026-04-26.md` added** reflecting the post-cleanup state. The earlier `verification-2026-04-24.md` is preserved as a historical record.
- **`.writ/context.md` synced** to match the completion roll-up.

**Files updated:**
- `spec.md`, `spec-lite.md`, `user-stories/README.md`
- `user-stories/story-1-knowledge-ledger.md`, `user-stories/story-5-eval-tier-1.md`
- `user-stories/story-{1,2,3,4,5}-verification.md` → `user-stories/verification/story-{1,2,3,4,5}.md`
- New: `verification-2026-04-26.md`
- New: `.writ/issues/improvements/2026-04-26-story-1-knowledge-loading-organic-validation.md`
- New: `.writ/issues/improvements/2026-04-26-story-5-remote-ci-gate-organic-validation.md`
- `.writ/context.md`

**Backup:** `backups/2026-04-26-edit-spec/`
