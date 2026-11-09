# Writ Project Context

> Last Updated: 2026-11-09T16:40:00Z

## Product Mission

Writ is the thin, portable methodology layer on top of capable AI harnesses. It owns three things and delegates or deletes the rest: the contract (spec, acceptance and exit criteria, stakes), the verifier (scripts that re-derive verdicts about the code and the running app), and the boundary (when an agent stops and asks a person: on reasonable doubt, not on principle, per ADR-033). Users reach all three through one front door, `/writ`, that restates, classifies, and routes each request.

## Active Spec

- **Spec:** `2026-11-09-delete-merged-branches` — Delete Merged Branches
- **Status:** Complete (integration suite green; not yet shipped)
- **Story:** 2 of 2 — /ship deletes the landed local branch (Completed ✅); Story 1 (integrate deletes the merged lane branch) Completed ✅
- **Progress:** 14/14 tasks complete (100%)
- **Also open:** `2026-10-25-gate-upgrade-removal-measurement` (amendment requested). v0.47.2 (2026-11-09) is the latest release.

## Artifact Map

- **Product:** roadmap.md, mission.md, mission-lite.md (v0.47.2 latest release, 2026-11-09)
- **Last spec:** .writ/specs/archive/2026-11-09-delete-merged-branches/ (archived after PR #76)
- **Knowledge:** .writ/knowledge/ (30 entries)
- **Docs:** .writ/docs/ (30 files)
- **Integrity:** ✅ all required present

## Recent Drift

- DEV-005 Squash proof on the re-run entry points: plain `/ship` reads `headRefOid` before Step 2 (person's decision) — delete-merged-branches (Medium)
- DEV-003 `pull --ff-only --no-rebase` and a HEAD check after checkout — delete-merged-branches (Small)
- DEV-002 Step 6b does not run under `--dry-run` — delete-merged-branches (Small)

## Open Issues

25 open issue files in .writ/issues/ (47 total; 22 closed with `## Resolution`, 1 Goal Card)
