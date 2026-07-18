# Writ Project Context

> Last Updated: 2026-07-18T15:05:00Z

## Product Mission

Writ is the thin, portable methodology layer on top of capable AI harnesses. It owns durable contracts — specs, drift logs, decisions, knowledge, phase state — in plain markdown on git, and delegates mechanics to the platform underneath.

## Active Spec

- **Spec:** Model-Tier Delegation Across Agents (`2026-07-10-model-tier-delegation`)
- **Status:** Not Started — the only non-terminal spec in `.writ/specs/`
- **Stories:** 0 of 4 started (Story 1 "Tier Contract + ADR-014" is first)
- **Tasks:** 0/24 complete
- **Branch:** main (at v0.21.0)

## Recent Housekeeping (2026-07-18)

- Reconciled 9 stale spec headers to terminal states (Complete/Closed) with commit-level evidence; `2026-03-18-infrastructure-command-refinement` closed as Abandoned (targets moved to `contrib/`).
- Triaged all 7 stale issues: 5 closed with evidence and deleted (delete-on-close; resolution notes preserved in git history), 1 parked (business-process pipeline → roadmap parking lot), 1 kept open (`implement-spec` branch preflight — still valid).
- Purged `.writ/state/` of ~110 completed execution/eval/review artifacts; only the update-check cache remains.

## Open Issues

Open backlog: `improvements/2026-05-06-implement-spec-branch-preflight.md` (valid, unpromoted) and `bugs/2026-07-11-lane-worktree-path-relative-repo.md` (one-line fix specified in issue). `improvements/2026-07-11-eval-recommended-spec-spawn-heaviness.md` is mitigated with one optional lever remaining.
