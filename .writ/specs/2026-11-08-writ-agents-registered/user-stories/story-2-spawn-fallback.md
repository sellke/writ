# Story 2: Spawn fallback and no inline coding

> **Status:** Not Started
> **Priority:** Medium
> **Dependencies:** Story 1

## User Story

**As a** maintainer running `/implement-story` in this repo from a session that has no `writ-*` agent types
**I want to** every spawn to have a stated fallback, and Gate 1 to refuse inline coding
**So that** a story is never coded by the orchestrator itself, and the report shows which agent ran

## Acceptance Criteria

> **AC IDs assigned through:** AC-2.4

- [ ] Given `adapters/claude-code.md` § Agent Paths, when the session lists no `writ-*` type, then the adapter says to spawn a general-purpose agent whose prompt begins "Read and follow `agents/<file>.md`", with the same inputs, and to name the agent type that ran in the report `[AC-2.1]`
- [ ] Given Gate 1 in `commands/implement-story.md`, when read, then one sentence states that no coding-agent type routes to the adapter fallback, that nothing spawnable routes to the BLOCKED escalation, and that the orchestrator never codes a story itself `[AC-2.2]`
- [ ] Given the ESCALATE rule in `agents/supervisor-agent.md`, when read, then it lists "code in the commit range with no coding-agent spawn in the report", and `claude-code/agents/writ-supervisor.md` and the generated `implement-story.md` copies carry the same sentences, with both generator `--check` runs clean `[AC-2.3]`
- [ ] Given the Gate 1 and adapter edits, when `scripts/tests/test_gate_upgrade_trial_outcome.py`, `scripts/tests/test_governor_enforcement.py`, and `scripts/tests/test_harness_cuts.py` run, then all pass, the presence probes in `implement-story.md` still match, and `commands/implement-story.md` is within its byte budget or its pinned overage is re-pinned with a dated comment `[AC-2.4]`

## Implementation Tasks

- [ ] 2.1 Write `scripts/tests/test_agent_spawn_fallback.py` pinning the adapter fallback sentence, the Gate 1 sentence, and the supervisor ESCALATE clause in source and generated copies. Run it and confirm it fails before any edit `[AC-2.1, AC-2.2, AC-2.3]`
- [ ] 2.2 Add the general-purpose fallback rule to `adapters/claude-code.md` § Agent Paths after "Spawn the `writ-*` agent by name." It covers no `writ-*` type, the prompt opening, the same inputs, and naming the agent type in the report `[AC-2.1]`
- [ ] 2.3 Add the one Gate 1 sentence to `commands/implement-story.md`: no coding-agent type routes to the adapter fallback, nothing spawnable routes to BLOCKED escalation, and the orchestrator never codes a story itself. Offset bytes in the same file `[AC-2.2, AC-2.4]`
- [ ] 2.4 Add the ESCALATE clause "code in the commit range with no coding-agent spawn in the report" to `agents/supervisor-agent.md` (Business Rule 4) `[AC-2.3]`
- [ ] 2.5 Run `python3 scripts/gen-claude-agents.py` and `python3 scripts/gen-platform-trees.py`. Confirm both `--check` modes pass and the generated copies carry the three sentences `[AC-2.1, AC-2.2, AC-2.3]`
- [ ] 2.6 Run `scripts/tests/test_gate_upgrade_trial_outcome.py`, `test_governor_enforcement.py`, and `test_harness_cuts.py` alone on Python 3.9 and 3.14. Confirm the presence probes and byte-ledger tests pass `[AC-2.2, AC-2.4]`
- [ ] 2.7 Verify all acceptance criteria. Run `scripts/tests/test_agent_spawn_fallback.py` and `bash scripts/eval.sh --check=claude-agents --report=<scratch path>`. Check each AC against its tagged test or command `[AC-2.1, AC-2.2, AC-2.3, AC-2.4]`

## Notes

- **Byte budget.** `commands/implement-story.md` is over budget by a pinned amount in `KNOWN_OVER_BUDGET` in `scripts/tests/test_governor_enforcement.py`. Offset first. Re-pin only a residual, with a comment `# 2026-11-08 (...)` directly after `# ` (the `test_harness_cuts.py` ledger regex requires the date there).
- **Pinned phrases.** Before trimming any Gate 1 or Gate 0.5 prose, `git grep` each phrase. Do not remove any literal that `test_gate_upgrade_trial_outcome.py` or another test or eval check pins.
- **Generated copies.** Edit `agents/*.md` and `commands/*.md` sources only. Copies under `claude-code/agents/`, `plugins/writ/commands/`, and `cursor/plugin/commands/` come from the generators.
- **Story 1 dependency.** The fallback sentences matter only once `.claude/agents` resolves to `claude-code/agents/`. This story's pytest file checks text, not registration. The live session check belongs to Story 1.
- **Tests.** Python 3.9 floor, Python 3.14 also required. Run pytest alone; do not run `eval.sh` or other writes under `.writ/state/` while pytest runs.

## Context for Agents

- **Error map rows:** [session lists no `writ-*` type, no subagent tool at all, report shows code with no coding spawn] — technical-spec.md → ## Error & Rescue Map
- **Shadow paths:** [Happy path, Upstream error] — technical-spec.md → ## Shadow Paths
- **Business rules:** [Business Rule 3, Business Rule 4] — spec.md → ## Specification Contract → 📋 Business Rules; spec.md → ## Business Rules (Expanded)
- **Experience:** [State catalog] — spec.md → ## 🎯 Experience Design → ### State catalog
