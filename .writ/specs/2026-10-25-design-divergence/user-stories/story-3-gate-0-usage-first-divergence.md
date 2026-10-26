# Story 3: Gate 0 Usage-First Divergence and the Gate 0 Divergence Switch

> **Status:** Not Started
> **Priority:** High
> **Dependencies:** Story 1

## User Story

**As a** Writ maintainer
**I want to** add a boundary-crossing Gate 0 block to `commands/implement-story.md` that writes the caller usage first, then gets two independent read-only design sketches, picks one, and hands it to Gate 1 through the existing warnings channel, with a named config switch
**So that** stories that cross an API, schema, migration, or auth boundary start from a design that differs in structure, and the switch can turn the upgrade off without touching other gates

## Acceptance Criteria

> **AC IDs assigned through:** AC-3.5

- [ ] Given commands/implement-story.md, when the `#### Gate 0: Architecture Check` section is read, then it contains `**Design divergence (boundary-crossing route).**`, `Read skills/design-divergence/SKILL.md`, the three route-predictor commands from technical-spec.md, the triggers `--full-pipeline`, `--panel`, and `route: review-agent`, the caller usage written to `.writ/state/divergence-<story-stem>.md` before any axis is declared, two `readonly` spawns at `anchor` in one message returning `COMMITMENT:`, `SKETCH:`, and `USAGE FIT:`, and the hand-off label `design sketch (Gate 0 divergence)` `[AC-3.1]`
- [ ] Given the switch, when Gate 0 and .writ/docs/config-format.md are read, then both name the literal `- **Gate 0 Divergence:** off`, state that an absent line means on and any other value means on with `gate0-divergence: on (malformed: <value>)`, and Gate 0 names every report state from spec.md → State Catalog, each starting `gate0-divergence:` `[AC-3.2]`
- [ ] Given the never-blocking rule, when Gate 0 is read and `uv run pytest scripts/tests/test_implement_story_default_path.py` and `python3 scripts/verdict-provenance.py check --command commands/implement-story.md --repo . --prose-only-blocking` run, then Gate 0 states no DEGRADED mark, no AskQuestion, no `review_cycle` increment, and no retry for any divergence outcome, the tests pass with no unguarded `> **Agent:**` marker in Gate 0, and verdict-provenance passes with no new `gates:` entry `[AC-3.3]`
- [ ] Given the diff to commands/implement-story.md, when it is inspected, then outside the Gate 0 section only the `## Pipeline` Gate 0 row (Runs-as clause and Skill cell `design-divergence (boundary-crossing route)`), the `## Overview` default-spawn clause, and the `## References` skills line changed, and the Gate 0.5 through Gate 5 sections, the routing table, and the sub-agent completeness and worktree notes are byte-identical `[AC-3.4]`
- [ ] Given the block is under 2,000 bytes and the `"commands/implement-story.md"` entry in scripts/tests/test_governor_enforcement.py is re-pinned to the measured overage with a dated disclosure naming this spec and Story 3, when `python3 scripts/gen-platform-trees.py --check`, `uv run pytest`, `uv run --python 3.9 pytest`, the bash tests, and `bash scripts/eval.sh` run, then all pass with 0 findings `[AC-3.5]`

## Implementation Tasks

- [ ] 3.1 Add tests to scripts/tests/test_design_divergence_wiring.py for every Gate 0 literal in technical-spec.md's text contract, the switch literal in Gate 0 and config-format.md, the report states, and the Pipeline/Overview/References edits `[AC-3.1, AC-3.2, AC-3.4]`
- [ ] 3.2 Write the Gate 0 block after the `--full-pipeline` anchor-confirmation paragraph and before the `---` preceding Gate 0.5 `[AC-3.1, AC-3.3]`
- [ ] 3.3 Write the switch, route-predictor, and report-state text, and add the config-format.md row and `## Gate 0 Divergence` section `[AC-3.2]`
- [ ] 3.4 Update the Pipeline Gate 0 row, the Overview clause, and the References line `[AC-3.4]`
- [ ] 3.5 Measure the block's bytes, re-pin the `"commands/implement-story.md"` ratchet in test_governor_enforcement.py with the dated disclosure, and regenerate platform trees `[AC-3.5]`
- [ ] 3.6 Verify acceptance criteria, including the default-path tests and the verdict-provenance check `[AC-3.1, AC-3.2, AC-3.3, AC-3.4]`
- [ ] 3.7 Verify all tests pass: `uv run pytest`, `uv run --python 3.9 pytest`, the bash tests, and `bash scripts/eval.sh` run outside the sandbox `[AC-3.5]`

## Notes

- **Ordering.** Gate 0 runs before Gate 0.5 and Gate 2.5. It cannot read `gate3_route`, so it predicts the route by running `boundary-map.py compute`, `change-surface.py classify`, and `boundary-map.py crossings` over the planned files. Those scripts already exist.
- **Gate 1 is unchanged.** Gate 1 already receives "any arch-check warnings". The chosen sketch travels in that channel. Do not edit Gate 1.
- **No new gate heading.** Do not add a `#### Gate` heading. The block stays inside `#### Gate 0: Architecture Check`, so `verdict-provenance.py` needs no new `gates:` entry.
- **Out of scope.** Do not edit `agents/architecture-check-agent.md`, Gate 2.5, or Gate 3.
- **Switch name is a seam.** `Gate 0 Divergence` is the name the later spec `2026-10-25-gate-upgrade-removal-measurement` toggles. Keep it exactly as written.
- **Byte budget.** `commands/implement-story.md` is already over its ratchet (11266 bytes in `scripts/tests/test_governor_enforcement.py`). The block must stay under 2,000 bytes. Measure after writing, then re-pin to the measured total.
- **Ratchet conflicts.** Sibling Phase 15 specs may re-pin the same `"commands/implement-story.md"` entry. Whichever lands second re-pins from the first one's value and cites it in the disclosure.
- **Platform-name test.** `scripts/tests/test_platform_neutral_names.py` pins the `/prototype` render table. This story does not touch `commands/prototype.md`, so that test should not change. Confirm it still passes.
- **Default-path tests.** `scripts/tests/test_implement_story_default_path.py` requires Gate 0 to carry no unguarded `> **Agent:**` marker. The sketch spawns are plain read-only subagents with no agent file, so they must not use that marker.
- **Sketch spawns are not agent files.** Do not add an agent definition for the sketches.
- **Gate 0 does not re-run.** Gate 1 recode after a Gate 3 FAIL, and two-fail escalation to `--full-pipeline`, do not re-run Gate 0. The sketch stays in the warnings.

## Definition of Done

- [ ] All tasks completed
- [ ] All acceptance criteria met
- [ ] Tests passing
- [ ] Code reviewed
- [ ] Documentation updated

## Context for Agents

- **Error map rows:** [Gate 0 switch read, Route predictor, Sketch spawn] — from technical-spec.md Error & Rescue Map
- **Shadow paths:** [Gate 0 divergence] — from technical-spec.md Shadow Paths
- **Business rules:** [Switch (rule 1), Route (rule 2), Usage first (rule 3), Two sketches independent (rule 4), Choice (rule 6), Hand-off to Gate 1 (rule 7), Never blocking (rule 8)] — from spec.md → Business Rules (Expanded)
- **Experience:** [Report line states (State Catalog), Interaction patterns (every Gate 0 line starts `gate0-divergence:`)] — from spec.md → Experience Design → State Catalog and Interaction Patterns
- **Text contract:** [Gate 0 literals, route-predictor commands, report states] — from technical-spec.md → Gate 0 Divergence (Story 3)
- **Edit table:** [Pipeline Gate 0 row, Overview clause, References line] — from technical-spec.md → Gate 0 Divergence, "Other edits"
- **Ratchet and config:** [`test_governor_enforcement.py` re-pin, `config-format.md` section] — from technical-spec.md → Files in Scope
