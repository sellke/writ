# Drift and Architecture Guards for the Default Story Path

> **Status:** Not Started
> **Created:** 2026-09-26
> **Owner:** @unknown
> **Dependencies:** []
> **Extends:** [2026-09-09-phase11-stage4b-pipeline-demote](../archive/2026-09-09-phase11-stage4b-pipeline-demote/spec.md)
> **Origin:** Session assessment 2026-09-26 of default `/implement-story` coverage. Evidence: default Gate 0 `arch-check.py` compares the planned set to a boundary map derived from the same task list; `--changed` is replay-only, so no post-coding boundary check runs; the evaluator is told not to tour integration; Medium drift never stops; drift is judged against auto-amended `spec-lite.md`.

## Specification Contract

**Deliverable:** The default `/implement-story` path catches out-of-scope file changes and architectural drift mechanically. When one occurs, Gate 3 routes to `review-agent`, which has the mandate for boundary and integration compliance, while still spawning two agents.

**Must Include:**
- A mechanical post-coding boundary check that lists changed files outside the story's boundary map, excluding Writ's own pipeline outputs.
- A deterministic Gate 3 route: `review-agent` instead of `evaluator-agent` when the change surface is `full-stack` or the boundary check finds crossings. Otherwise the evaluator runs, as today.
- Drift judged against the human-approved `spec.md` contract, not only the auto-amended `spec-lite.md`.
- A drift roll-up in the `/implement-spec` completion report, so Medium warnings are not lost across stories.

**Hardest Constraint:** Keep the two-spawn default provable: `spawn-cap.py` still passes, and a routed story swaps its Gate 3 agent rather than adding one. `implement-story.md` is already about 9.6 KB over its byte budget, so growth must be small and disclosed in the ratchet.

**Stories:**
1. **Boundary crossings script.** `boundary-map.py crossings` prints crossings and a `route:` line, excluding the story's spec folder, `.writ/context.md`, and `.writ/state/`. Built test-first.
2. **Gate 3 risk route.** `implement-story.md` runs `crossings` after Gate 2.5, routes Gate 3 by its `route:` line, passes crossings to the Gate 3 agent, and prints one route line in the story report. Two-fail escalation is unchanged. Budget and hash ratchets re-pinned with disclosure.
3. **Contract-anchored drift and severity.** Both Gate 3 agents (and their Claude Code and Codex peers) receive `spec.md`'s `## Specification Contract` section verbatim. A new runtime dependency not in the spec, a changed interface at an integration point, or a changed architectural approach is **Large** (pause), not Medium. `drift-report-format.md` and `drift-triage` match.
4. **Drift roll-up.** `drift-format.py summary` counts Small / Medium / Large deviations logged in this run; `/implement-spec` Step 4.2 reports it with the Medium headlines.

**Success Criteria:** A default story that touches a file outside its boundary, or a `full-stack` path, runs Gate 3 as `review-agent`, and the story report says why. A clean single-component story still runs the evaluator. `spawn-cap.py` passes. `uv run pytest`, the bash suite, and `eval.sh` are green.

**Scope Boundaries:**
- **Included:** the four stories above.
- **Excluded:** `implement-story.lean.md` (the unchanged experiment arm, as in the Jev pilot); review-agent shadow runs; planted-bug baselines; architecture-as-lint guidance for user projects (filed as an issue); visual QA on the default path.

**⚠️ Technical Concerns:**
- Routed stories make the Jev shadow report `unverifiable (no_evaluator_ids)`, because `review-agent` checklist lines carry no `[AC-N.M]` tags. Harmless; those stories leave the Jev agreement sample.
- `change-surface.py` classifies ambiguous changes UP to `cross-component`, so every non-`components/` change lands there. `cross-component` is therefore **not** a route trigger; it would restore `review-agent` on nearly every story.
- Test files and lockfiles not named in a story's tasks count as crossings and route to `review-agent`. Accepted: the route swaps an agent, it does not add one.

---

## 🎯 Experience Design

**Entry point.** A maintainer runs `/implement-story story-N` (no flag), or `/implement-spec`, which calls it.

**Happy path.** Coding finishes inside the story's boundary on a non-full-stack surface. Gate 2.5 prints `route: evaluator-agent`. Gate 3 runs the evaluator exactly as today.

**Moment of truth.** A story that quietly edits a file outside its task list is reviewed by `review-agent` with those files named, and the story report says `gate3-route: review-agent (outside_boundary <path>)`.

**Feedback model.** One `gate3-route:` line per story report. `/implement-spec` completion adds one `Drift this run:` line plus Medium headlines.

**Error experience.** An unreadable boundary map or a crossings helper that cannot run routes UP to `review-agent` (never silently to the evaluator) and says why. Architecture-class drift pauses with the existing accept / reject / modify-spec options.

### State Catalog

| State | What the user sees |
|---|---|
| Clean story | `gate3-route: evaluator-agent` |
| Boundary crossing | `gate3-route: review-agent (outside_boundary a.py; …)` |
| Full-stack surface | `gate3-route: review-agent (full_stack_surface)` |
| Map unreadable / helper missing | `gate3-route: review-agent (unverifiable: <reason>)` |
| Architecture-class drift | Gate 3 PAUSE → Gate 3.5 § A options |
| Spec end | `Drift this run: S small, M medium, L large` + Medium DEV headlines |

---

## 📋 Business Rules

1. **Swap, never add.** The risk route replaces the Gate 3 agent. A default story still has at most two spawn sites; `spawn-cap.py` still passes.
2. **Route UP on doubt.** When the crossings check cannot run (unreadable map, missing helper), route to `review-agent`.
3. **Triggers are exactly two.** `full-stack` change surface, or at least one crossing. `cross-component` alone does not route.
4. **Pipeline outputs are not crossings.** The story's own spec folder, `.writ/context.md`, and `.writ/state/` are excluded.
5. **Two-fail escalation unchanged.** Gate 3 FAILs count the same whichever agent ran; two consecutive FAILs continue the story as `--full-pipeline`.
6. **The contract is the drift reference.** `spec.md`'s `## Specification Contract` outranks `spec-lite.md` when they disagree; `spec.md` is still never auto-modified.
7. **Architecture-class drift is Large.** New runtime dependency not in the spec, changed interface at an integration point another story or the contract names, or changed architectural approach.
8. **Roll-up is report-only.** `drift-format.py summary` never blocks and never changes a story verdict.
9. **Lean sibling untouched.** `commands/implement-story.lean.md` is out of scope.

---

## Detailed Requirements

### Crossings (Story 1)

`python3 scripts/boundary-map.py crossings --map PATH --changed FILE… [--story PATH] [--surface CLASS] [--repo .]`

Output, helper-family shape: one verdict line (`pass` / `unverifiable`), one `route:` line, `reason:` lines, summary last. Exit 0 when it ran; exit 2 on usage (no `--changed`). A crossing is not a failure: it is a routing signal.

### Route (Story 2)

Gate 0.5 saves its JSON map under `.writ/state/`. Gate 2.5 runs `crossings` with the changed files and the `change-surface.py` class. Gate 3 spawns the agent named on the `route:` line and passes the `reason:` lines to `review-agent` as `boundary_overlap_summary`.

### Drift reference and severity (Story 3)

Gate 3 context routing adds `contract_content` (the `## Specification Contract` section of `spec.md`, verbatim; empty string when absent). Both agents' drift rubrics move the three architecture-class cases to Large.

### Roll-up (Story 4)

`python3 scripts/drift-format.py summary --drift-log PATH [--since YYYY-MM-DD]` counts deviations in story sections whose `> Run:` date is on or after `--since`, and prints each Medium and Large DEV headline. A missing log is `pass` with zero counts (absence is the no-drift signal).

## Implementation Approach

Extend existing helpers rather than add new scripts: `boundary-map.py` already owns the map, `drift-format.py` already parses `drift-log.md`. Command edits are prose lines in existing gates; no new gate numbers. Every helper change is test-first in the existing `scripts/tests/test_boundary_map.py` and `test_drift_format.py`, with wiring pinned in a bash or pytest wiring test.
