# Story 2: Demote gates with no recorded catch

> **Status:** Not Started
> **Priority:** High
> **Dependencies:** Story 1

## User Story

**As a** developer running `/implement-story` on the default path
**I want to** gates with no recorded catch moved under `--full-pipeline`, and gates with a recorded catch left on the default path
**So that** the default path runs fewer checks and each kept check has evidence behind it

## Acceptance Criteria

> **AC IDs assigned through:** AC-2.5

- [ ] Given `gate-evidence.md` marks a gate for demotion, when Story 2 is complete, then that gate's section sits under the `--full-pipeline` heading in `commands/implement-story.md` and its `gates:` entry reads `path: full-pipeline` `[AC-2.1]`
- [ ] Given a gate whose evidence cites a recorded catch, when Story 2 is complete, then its section and its inputs stay on the default path and its `gates:` entry has no `path:` line `[AC-2.2]`
- [ ] Given the pinning tests, when Story 2 is complete, then each assertion on a demoted gate's default-path wording asserts the full-pipeline wording instead and no guarded behavior is dropped `[AC-2.3]`
- [ ] Given `commands/implement-story.md` changes byte size, when `scripts/tests/test_governor_enforcement.py` runs, then `KNOWN_OVER_BUDGET` holds a dated entry for the new size and `python3 scripts/gen-platform-trees.py --check` passes `[AC-2.4]`
- [ ] Given the demotion is complete, when the repo is checked, then no gate script, agent, or test file is deleted and `scripts/tests/test_gate_upgrade_trial_outcome.py` still passes `[AC-2.5]`

## Implementation Tasks

- [ ] 2.1 Write failing tests in `scripts/tests/test_implement_story_default_path.py` asserting demoted gate sections sit under `--full-pipeline` and kept gates stay on the default path `[AC-2.1, AC-2.2]`
- [ ] 2.2 Move each demoted gate section in `commands/implement-story.md` under the `--full-pipeline` heading, unchanged in content. Add `path: full-pipeline` to each demoted `gates:` entry. Leave kept gates in place `[AC-2.1, AC-2.2]`
- [ ] 2.3 Change wording pins to full-pipeline wording in `scripts/tests/test_implement_story_default_path.py`, `scripts/tests/test_boundary_map.py`, `scripts/tests/test_change_surface.py`, `scripts/tests/test_docs_check.py`, and each other pin listed in Notes. Keep every guarded check `[AC-2.3]`
- [ ] 2.4 Add a dated `KNOWN_OVER_BUDGET` entry for the new `commands/implement-story.md` byte size in `scripts/tests/test_governor_enforcement.py`. Run `python3 scripts/gen-platform-trees.py` to regenerate `claude-code/`, `cursor/plugin/`, and `codex/` `[AC-2.4]`
- [ ] 2.5 Verify acceptance criteria: run `scripts/tests/test_gate_upgrade_trial_outcome.py` and the tests changed above. Confirm no gate script, agent, or test file was removed `[AC-2.1, AC-2.2, AC-2.3, AC-2.4, AC-2.5]`
- [ ] 2.6 Verify all targeted tests pass on Python 3.9 and `python3 scripts/gen-platform-trees.py --check` is clean `[AC-2.3, AC-2.4]`

## Notes

- **Input dependency:** `gate-evidence.md` does not exist yet. Story 1 writes it. Its rows decide which gates move. Start only after each `gates:` entry is marked keep or demote.
- **Current `gates:` entries** in `commands/implement-story.md`: `gate0_arch`, `gate0_5_boundary`, `gate1_coding` (prose-only), `gate2_build`, `gate2_5_surface`, `gate3_review`, `gate3_5_drift`, `gate4_tests`, `gate4_5_behavior`, `gate5_docs`.
- **Finding pins:** the spec counts 42 test and eval files that pin `implement-story.md` text. Build the full list for demoted gates with `grep -rln` on each demoted gate's script name and section heading under `scripts/tests/` and the eval scripts. The four named files in task 2.3 are examples, not the full set.
- **Business Rule 3:** a kept gate that reads another gate's output keeps that producer on the default path. Safety Fact reads the Gate 2.5 risk route and blast radius. The removal-trial keep verdicts (Safety Fact, Reviewer Filters, Gate 0 Divergence) and the ADR-032 evidence gate are not reopened.
- **Business Rule 2:** demotion moves text only. Gate scripts, agents, and tests stay in the product.
- **Presence probes:** `test_gate_upgrade_trial_outcome.py` ties each kept upgrade to a presence probe in `implement-story.md`. Those probes must keep passing (this spec's Business Rule 3; spec.md → Cross-Spec Overlap).
- **Symlinks:** `.claude/` and `.cursor/` point at product source. Editing `commands/implement-story.md` changes them. Do not run `install.sh` on this repo.
- **Test runs:** run pytest alone. `eval.sh`, bash tests, and `.writ/state/` writes in the same checkout during pytest break `test_smoke_leaves_repo_unchanged`. The full pytest suite (both 3.9 and 3.14) and `eval.sh` run once at the end of the spec, not in this story.
- **Failure mode:** if a pinning test guards a default-path behavior that a kept gate needs, the gate stays on the default path and `gate-evidence.md` records the dependency (technical-spec error map, "Demotion (Story 2)").

## Context for Agents

- **Error map rows:** [Demotion (Story 2)] — from technical-spec.md error map
- **Shadow paths:** []
- **Business rules:** [2, 3] — from spec.md → Specification Contract → 📋 Business Rules
- **Experience:** []
