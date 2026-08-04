# Writ Project Context

> Last Updated: 2026-08-04T22:18:00Z

## Product Mission

Writ is the thin, portable methodology layer on top of capable AI harnesses. It owns durable contracts — specs, drift logs, decisions, knowledge, phase state — in plain markdown on git, and delegates mechanics to the platform underneath.

## Active Spec

- **Spec:** 2026-08-04-post-merge-archival-hook — Post-Merge Archival Hook
- **Status:** Complete (4/4 stories). All 5 numbered Success Criteria fixture-satisfied; Story 4's AC5 (live merge-then-release confirmation of this spec and `2026-08-04-spec-lifecycle-archival`) remains an open, non-blocking follow-up — see story-4's Live Confirmation Status.
- **Story:** 4 of 4 — Dogfood and Verify (Completed ✅, review PASS)
- **Progress:** 30/30 tasks complete (100%)

## Artifact Map

- **Product:** .writ/product/roadmap.md, mission.md, mission-lite.md
- **Active spec:** .writ/specs/2026-08-04-post-merge-archival-hook/ — spec.md + spec-lite.md, user-stories/, sub-specs/, drift-log.md
- **Knowledge:** .writ/knowledge/ (11 entries)
- **Docs:** .writ/docs/ (19 files)
- **Integrity:** ✅ all required present

## Recent Drift

Story 4 landed with Small drift (1 item, auto-amended — see `drift-log.md`): DEV-004 (story-tracking metadata — status header, task checkboxes, README/spec.md rollups — left stale after the coding agent delivered the architecture-check-narrowed scope; the orchestrator flipped all of it to reflect the verified-complete work immediately after review PASS). Story 4's own architecture check returned CAUTION with 6 findings, all folded into the coding agent's task list pre-implementation: extracted the shared `run_archival_hook()` composition model into `scripts/_archival_hook_model.py` (avoiding near-total duplication of Story 3's existing 11-scenario test file), narrowed the new eval script to 2 smoke scenarios plus `release.md` Step 1.3c prose-pinning as its primary payload, reframed the gate-regression check as confirming Story 3's existing diff rather than re-running it, and required the new AC5 real-repo readiness probe (`scripts/eval-post-merge-dogfood.py`) to default non-failing and stay unregistered in `eval.sh` until real hook-triggered evidence exists. Story 4's review agent independently re-verified every claim (199/199 tests, literal-pin accuracy, boundary compliance) — PASS. Story 3 landed with Small drift (1 item, DEV-003 — SHA-extraction mechanism swap). Story 2 landed with Small drift (2 items). Story 1 landed with zero drift.

**Spec-level note:** All 5 of the spec's own numbered Success Criteria are now fixture-satisfied across Stories 1–4. Story 4's own Acceptance Criterion 5 (this spec and `2026-08-04-spec-lifecycle-archival` actually archiving via a real merge + `/release` cycle) is a stretch goal beyond the spec's numbered criteria and remains genuinely open — tracked in `story-4-dogfood-and-verify.md`'s Live Confirmation Status, not a blocker to the spec's own completion.

## Open Issues

Open backlog: 1 file under `.writ/issues/` (features/).
