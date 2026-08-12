# Writ Project Context

> Last Updated: 2026-08-12T07:20:00Z

## Product Mission

Writ is the thin, portable methodology layer on top of capable AI harnesses. It owns the durable contracts — specs, drift logs, decisions, knowledge, phase state — in plain markdown on git, and delegates mechanics (context management, subagents, browsing, retrieval) to the platform underneath. "Thin" is currently a target, not a state: `commands/` measured 516,589 chars on 2026-08-11, and Phase 10 closes the gap.

## Active Spec

- **Spec:** 2026-08-12-refactor-dirty-tree-guard — `/refactor` Dirty-Tree Guard
- **Status:** In Progress (1/2 stories complete)
- **Story:** 1 of 2 — Porcelain Guard Before Baseline Verification (Completed ✅, review PASS)
- **Progress:** 4/8 tasks complete (50%)

## Artifact Map

- **Product:** .writ/product/roadmap.md, mission.md, mission-lite.md
- **Active spec:** .writ/specs/2026-08-12-refactor-dirty-tree-guard/ — spec.md + spec-lite.md, user-stories/, sub-specs/, drift-log.md
- **Knowledge:** .writ/knowledge/ (21 entries)
- **Docs:** .writ/docs/ (20 files)
- **Integrity:** ✅ all required present

## Recent Drift

Story 1 landed with Small drift (2 items, `drift-log.md`). **DEV-001** — the guard was implemented as its own numbered step, `#### Step 1.1b: Dirty-Tree Guard`, rather than as inline prose ahead of Step 1.2. This came out of a Gate 3 FAIL: the first implementation placed the guard as bold prose in the tail of Step 1.1's no-target branch while the direct-target jump at `commands/refactor.md:48` read "proceed to Step 1.2", jumping straight over it — so the guard never fired on `/refactor <path>`, the first row of the Modes table and the most common invocation. Promoting it to a numbered step and retargeting the jump made reachability structural rather than positional, and gave the eval a stable heading to pin. `spec-lite.md` auto-amended; `spec.md` unmodified. **DEV-002** — the 19-line `scripts/eval.sh` addition tripped the `scripts/` leanness ratchet (lines 32538 → 32557, chars 1407447 → 1409164). Non-blocking: those route through `add_note`, not `add_finding`, so the run stays `Findings: 0`. `--update-baseline` was deliberately not run; the increment is left for the baseline owner to record with a dated reason.

**Open follow-up (not drift):** nothing pins the jump sentence `proceed to Step 1.1b` at `commands/refactor.md:48`. Both the review and testing gates independently flagged that reverting that one line would leave all 8 new `require_literal` pins green while re-opening the exact defect Story 1 fixed. Both declined to block on it. A 9th pin closes it.

## Open Issues

Open backlog: 3 files under `.writ/issues/` (bugs/, features/, improvements/).
