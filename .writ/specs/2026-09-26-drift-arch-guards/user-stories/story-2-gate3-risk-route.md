# Story 2: Gate 3 Risk Route

> **Status:** Not Started
> **Priority:** High
> **Dependencies:** Story 1

## User Story

**As a** Writ maintainer
**I want to** default `/implement-story` to send stories that cross their boundary or touch full-stack paths to `review-agent` at Gate 3
**So that** the agent with a boundary and integration mandate reviews exactly the stories where architectural integrity is at risk, without adding a spawn

## Acceptance Criteria

> **AC IDs assigned through:** AC-2.5

- [ ] Given `commands/implement-story.md` Gate 0.5, when the map is computed, then the command saves the `compute` JSON under `.writ/state/` and Gate 2.5 runs `boundary-map.py crossings --map <saved> --changed <files> --story <story-file> --surface <class>` after `change-surface.py` `[AC-2.1]`
- [ ] Given Gate 3 on the default path, when the Gate 2.5 `route:` line names `review-agent`, then the command spawns `review-agent` instead of `evaluator-agent` and passes the `reason:` lines as `boundary_overlap_summary`; otherwise the evaluator runs as today; `--review-only` (no Gate 0.5 map) runs the evaluator and `--full-pipeline` always runs `review-agent` `[AC-2.2]`
- [ ] Given any default story that reaches Gate 3, when the story report is written, then it carries one `gate3-route: <agent> (<reasons>)` line; and the control flow counts Gate 3 FAILs from whichever agent ran toward the unchanged two-fail escalation `[AC-2.3]`
- [ ] Given the edited command, when `spawn-cap.py check --command commands/implement-story.md` runs, then it prints `pass`; and `commands/implement-story.lean.md` is byte-identical to its pre-story state `[AC-2.4]`
- [ ] Given the governor and lean-command suites, when they run, then `KNOWN_OVER_BUDGET["commands/implement-story.md"]` and the `implement-story` default SHA are re-pinned with dated comments naming this spec, and a wiring test pins the Gate 2.5 `crossings` line and the Gate 3 route sentence `[AC-2.5]`

## Implementation Tasks

- [ ] 2.1 Write a failing wiring test in `scripts/tests/test_quality_gate_wiring.py` pinning the Gate 0.5 save, the Gate 2.5 `crossings` invocation, the Gate 3 route sentence, and the `gate3-route:` report line `[AC-2.1, AC-2.2, AC-2.3, AC-2.5]`
- [ ] 2.2 Edit Gate 0.5 and Gate 2.5 in `commands/implement-story.md` per technical-spec §2 `[AC-2.1]`
- [ ] 2.3 Edit Gate 3, the Pipeline table row, the invocation row, and the control-flow paragraph so the default spawns the routed agent and FAIL counting is agent-neutral, without adding a `> **Agent:**` or `Task(` marker outside a `--full-pipeline` scope `[AC-2.2, AC-2.3, AC-2.4]`
- [ ] 2.4 Add the `gate3-route:` line to the Step 4 story report; trim adjacent prose to offset the growth where meaning is unchanged `[AC-2.3]`
- [ ] 2.5 Re-pin `KNOWN_OVER_BUDGET` in `scripts/tests/test_governor_enforcement.py` and `DEFAULT_SHA256["implement-story"]` in `scripts/tests/test_lean_commands.py` with dated disclosure comments `[AC-2.5]`
- [ ] 2.6 Verify: `spawn-cap.py` pass; `git diff --quiet HEAD -- commands/implement-story.lean.md`; `uv run pytest`; bash suite; `bash scripts/eval.sh` Findings 0 `[AC-2.4, AC-2.5]`

## Notes

`spawn-cap.py` counts only `> **Agent:**` lines and `Task(` calls outside a `**\`--full-pipeline\`:**` blockquote, so the route must be written as prose (as the two-fail escalation already is). `review-agent`'s Boundary Compliance category already treats `boundary_overlap_summary` as the "extra scrutiny" hook. On routed stories Jev `ac-shadow` reports `no_evaluator_ids`; leave it.

## Definition of Done

- [ ] All tasks completed
- [ ] All acceptance criteria met
- [ ] Tests passing
- [ ] Code reviewed
- [ ] Documentation updated

## Context for Agents

- **Business rules:** spec.md → ## 📋 Business Rules (1 Swap never add, 5 Two-fail unchanged, 9 Lean untouched)
- **Technical:** sub-specs/technical-spec.md → ## 2, ## 5
- **Experience:** spec.md → ## 🎯 Experience Design → State Catalog
