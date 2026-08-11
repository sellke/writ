# Story 7: Agent Config Contracts Across Both Carriers

> **Status:** Complete
> **Priority:** Medium
> **Dependencies:** Story 1

## User Story

**As a** maintainer auditing Writ's SDLC gates
**I want to** all seven agents to declare problem, outcome, and exit criteria in the fenced block that already carries `model_tier`
**So that** the gates that return PASS/FAIL declare what they are asserting PASS *about*, and the seventh agent's divergent carrier does not silently drop out of the audit

## Scope

Seven files in `agents/`, across two carriers:

| Carrier | Files | Heading | Fence |
|---|---|---|---|
| A | `architecture-check-agent`, `coding-agent`, `documentation-agent`, `review-agent`, `testing-agent`, `user-story-generator` | `## Agent Configuration` (line 7) | unlabeled |
| B | `visual-qa-agent` | `## Agent Specification` (line 18) | ` ```yaml ` |

Both are written to **as they are**. Converting B to A, or A to B, is out of scope (Business Rule 6).

## Acceptance Criteria

- [x] Given all seven agents carry a fenced config block with `model_tier` and no `problem:`, when this story lands, then each block carries `problem:`, `outcome:`, and `exit_criteria:` appended after the last existing key, inside the existing fence.
- [x] Given `agents/visual-qa-agent.md` uses a different heading, a different heading position, and a labelled fence, when this story lands, then it carries the three fields **and** still has `## Agent Specification`, still uses ` ```yaml `, and still uses `## Role` rather than `## Purpose` — nothing normalized.
- [x] Given the six carrier-A agents, when this story lands, then each still has `## Agent Configuration` with an unlabeled fence, and no key of theirs was reformatted — including `model: default (inherits from parent)`, which is not valid YAML and is deliberately left alone.
- [x] Given four of the seven return a PASS/FAIL verdict (`architecture-check`, `review`, `testing`, `visual-qa`), when their `exit_criteria` are read, then each names **what the verdict is about** — acceptance criteria coverage, coverage thresholds, mockup conformance — not merely that a verdict was returned.
- [x] Given Business Rules 1 and 2, when any entry is pasted into another agent's block, then it reads as false or nonsensical there; `review-agent` and `architecture-check-agent` are the adjacent pair and must be checked explicitly against each other.
- [x] Given Business Rule 4, when each file is diffed, then its config block grew by at most 7 lines.
- [x] Given the mirrors are out of scope, when `git diff --name-only` is read, then it lists only files under `agents/` — no `claude-code/agents/`, no `codex/agents/`, no `scripts/`.
- [x] Given `check-agent-parity.sh` checks file existence rather than field parity, when it is run after this story, then it still reports "parity OK".

## Implementation Tasks

- [x] 7.1 Read `.writ/docs/component-contract.md` (Story 1) for the agent-carrier schema, then read all seven agent files
- [x] 7.2 Locate the config block in each file by matching `^## Agent (Configuration|Specification)$` — **not** `## Agent Configuration` alone, which silently skips `visual-qa-agent.md` and reports 6/7 as success
- [x] 7.3 For each agent, derive its terminal condition from its Responsibilities and its output contract: what the orchestrating command receives back, and what must be true for that return value to be honest
- [x] 7.4 Author `problem:`, `outcome:`, and 2–4 `exit_criteria` per agent, appended after the last existing key inside the existing fence; run the swap test across all seven, starting with `review-agent` / `architecture-check-agent`
- [x] 7.5 Verify per file: ≤7 added lines, three fields present inside the fence, heading text unchanged, fence label unchanged, existing keys byte-for-byte unchanged
- [x] 7.6 Run `bash scripts/check-agent-parity.sh` (expect "parity OK") and `bash scripts/eval.sh` (expect no new findings); confirm `git diff --name-only` lists only `agents/` files

## Notes

**Technical considerations:**

- The seventh-file trap is the concrete risk here. An editor matching only `^## Agent Configuration$` produces a clean-looking 6/7 result that reads as success. The acceptance criteria are written to catch that specific outcome, and Task 7.2 exists solely to prevent it.
- The six carrier-A blocks are not valid YAML today — `model: default (inherits from parent)` parses as a plain string but the block has never been fed to a parser. Appending a `exit_criteria:` block sequence neither improves nor worsens that. Do not "fix" it; if a future check wants to parse these blocks, converting them is that spec's problem (spec.md → Technical Concerns).
- The four verdict-returning agents are where boilerplate is most likely. "The agent returns PASS or FAIL" is true of all four and asserts nothing. `testing-agent` enforces a coverage threshold — that is a number and therefore an observable. `review-agent` reviews against acceptance criteria — that is a mapping and therefore countable. `architecture-check-agent` runs before any code exists, so its criteria cannot reference test results at all.
- `visual-qa-agent` is conditionally activated (`## Visual References` section present, or a `mockups/` directory). Its `problem:` should reflect that it is an optional gate, and its criteria should hold for the activated case — a skipped run is not a completed run.
- `user-story-generator` runs as parallel instances in worktrees. Its outcome is per-story-file, not per-spec; a criterion phrased at spec granularity would misdescribe it.

**Risks / challenges:**

- Agent files are shorter and more uniform than command files, which makes them the easiest place in the spec to write seven near-identical field sets and have nobody notice. Swap-test the whole set at the end, not per file.
- `claude-code/agents/*.md` and `codex/agents/*.toml` mirrors exist and are tempting to update for consistency. ADR-020 names `agents/` only; parity is checked by file existence, not field content. Out of scope.
- `agents/` files are also referenced from `commands/implement-story.md`'s gate descriptions. This story does not touch that file — the gates' documented behavior is unchanged.

**Integration points:**

- Depends on Story 1 for the agent-carrier schema in `.writ/docs/component-contract.md`.
- Disjoint from every command story, so it runs in parallel with Stories 2–6.
- Story 6 carries the aggregate line-budget measurement across both `commands/` and `agents/`, so this story's 49-line ceiling contribution must land before that measurement.

## Definition of Done

- [x] All tasks completed
- [x] All acceptance criteria met
- [x] 7/7 agent files changed — verified by count, not assumed
- [x] Both carrier styles intact and unconverted
- [x] `bash scripts/check-agent-parity.sh` reports parity OK
- [x] `bash scripts/eval.sh` shows no new findings

## Context for Agents

- **Business rules:** [BR1 swap test, BR2 restatement test, BR3 observable requirement, BR4 line budget (7 lines per agent), BR5 one-line fields, BR6 no carrier normalization] — from spec.md → 📋 Business Rules
- **Detailed requirements:** [The contract schema → agent carrier] — from spec.md → ## Detailed Requirements
- **Out of scope:** [`claude-code/agents/` and `codex/agents/` mirrors; carrier normalization] — from spec.md → ## Out of Scope
- **Contract:** [Must include: `agents/visual-qa-agent.md` uses `## Agent Specification` with a `yaml` fence where the other 6 use `## Agent Configuration` with a plain fence; both carriers must be handled] — from spec.md → ## Contract (Locked)
- **Technical spec:** [Carrier Analysis → Agent config blocks — two carriers; Error & Rescue Map → Append keys to an agent fence] — from sub-specs/technical-spec.md
