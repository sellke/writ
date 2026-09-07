# Story 3: Cut Behavior Requests — Line-by-Line Classification to a 10,000-Byte Base, Batching Line to Adapters

> **Status:** Not Started
> **Priority:** High
> **Dependencies:** Story 2

## User Story

**As a** Writ maintainer pruning the shared base under a Goal Card that caps it at 10,000 bytes, **I want to** classify every remaining line of `system-instructions.md` and `commands/_preamble.md` as an environment fact, a human boundary, or a behavior request, remove the behavior requests and the duplicate `File Organization` section with a dated ledger reason for each, and move the Fable 5.1 batching line to each adapter file, **so that** the base lands at or under the cap with nothing but facts, boundaries, and untouched hard constraints left in it, and `prune-ledger.py check --cap-blocking` proves it.

## Acceptance Criteria

> **AC IDs assigned through:** AC-3.5

- [ ] Given Story 2's closing base byte count, when the classification table in this story's What Was Built is read, then every remaining line of `system-instructions.md` and `commands/_preamble.md` appears in it with columns file, section, line count, class, and action, and the three classes used are exactly environment-fact, human-boundary, and behavior-request per the research test in `.writ/research/2026-09-05-goldilocks-harness-research.md` `[AC-3.1]`
- [ ] Given the cut candidates named in technical-spec §4 (Identity & Approach, Command Execution Protocol, Judgment Principles, Prose, Interaction Tool Selection beyond the tool-naming rule, Session Auto-Orientation, Skills, the duplicate File Organization, preamble Tool Selection, Knowledge Context, Adapter Neutrality), when each is removed, then every removed line has a corresponding row in `.writ/decision-records/pruned-instructions-ledger.md` of class `behavior-request` (reason ≤ 120 chars stating why Fable 5.1-class models do it unprompted) or, for the duplicate `## File Organization` section, class `duplicate` (reason naming where the surviving copy lives) `[AC-3.2]`
- [ ] Given the sections named as kept verbatim (Hard Constraints, the Recommended Delivery Exception's rule, Plan Mode Integrity, User Challenge's four-part shape, Autonomy Gate Classes, Artifact Integrity), when they are diffed against the pinned commit `cf84742`, then they are byte-identical with no reflow, rewrap, or reword `[AC-3.3]`
- [ ] Given the Fable 5.1 batching line currently in `system-instructions.md`, when it is moved, then each of `adapters/claude-code.md`, `adapters/cursor.md`, `adapters/codex.md`, and `adapters/openclaw.md` carries exactly one Fable 5.1 line under a `## Model-specific` heading, proved by `grep -c "Fable 5.1" adapters/<file>.md` returning `1` for each, and `cursor/writ.mdc`'s Prime Directive mirror stays byte-identical to `system-instructions.md`'s `[AC-3.4]`
- [ ] Given the base at or under 10,000 bytes, when `python3 scripts/prune-ledger.py check --repo . --cap-blocking` runs, then it exits 0, the ledger file carries the `<!-- cap: blocking -->` marker line, and `bash scripts/eval.sh` reports 0 findings `[AC-3.5]`

## Implementation Tasks

- [ ] 3.1 Write the classification table (file, section, line count, class, action) for every remaining line of `system-instructions.md` and `commands/_preamble.md` in this story's What Was Built, as the record against which the cut is executed and verified `[AC-3.1]`
- [ ] 3.2 Remove the duplicate `## File Organization` section and the preamble restatements (`## Tool Selection`, `## Knowledge Context`, `## Adapter Neutrality` where they restate adapter files), each removal's ledger rows landing in the same commit `[AC-3.2]`
- [ ] 3.3 Cut `## Identity & Approach`, `## Command Execution Protocol` coaching, `### Judgment Principles`, and `### Prose`, with ledger rows in the same commit `[AC-3.2]`
- [ ] 3.4 Cut `## Interaction Tool Selection` beyond the tool-naming rule, `## Session Auto-Orientation`, and the Skills explainer, with ledger rows in the same commit `[AC-3.2]`
- [ ] 3.5 Move the Fable 5.1 batching line out of `system-instructions.md` into each `adapters/*.md` file under its own `## Model-specific` heading, one line per file `[AC-3.4]`
- [ ] 3.6 Measure bytes with `prune-ledger.py measure`, stop cutting once the total is at or under 10,000 (do not cut past the cap for its own sake), append `<!-- cap: blocking -->` to the ledger, and sync `cursor/writ.mdc`'s Prime Directive mirror to match `system-instructions.md` `[AC-3.1, AC-3.3, AC-3.5]`
- [ ] 3.7 Verify all acceptance criteria: `python3 scripts/prune-ledger.py check --repo . --cap-blocking` exits 0, `bash scripts/eval.sh` shows 0 findings, `grep -c "Fable 5.1" adapters/<file>.md` returns `1` for all four adapters, `check_prime_directive_sync` and `check_anti_sycophancy` stay green, and append the decision-log line `{date} stage-2: Story 3 — behavior requests cut, base at <bytes> bytes, cap flipped to blocking` to the story's completion commit `[AC-3.1, AC-3.2, AC-3.3, AC-3.4, AC-3.5]`

## Notes

**Technical considerations.** The cap is the finish line, not the goal (Business Rule 1) — stop cutting once `prune-ledger.py measure` reports at or under 10,000 bytes, even if candidate sections remain uncut. A line that is half constraint, half coaching is split at the sentence boundary and only the coaching half is removed, never dropped as a whole line to save the trouble of splitting it. The reason column for every `behavior-request` row is capped at 120 characters and must name *why* Fable 5.1-class models do the thing unprompted, not just restate the removed text. Kept sections are diffed against `cf84742`, not against Story 2's closing commit, per Business Rule 5.

**Risks.** A behavior request that turns out to be load-bearing for Fable 5.1 will not surface until Story 5's baseline re-run — this story cannot verify that risk itself, only minimize it by following the constraint test from the research doc line by line rather than by byte-count pressure. Cutting the wrong half of a split line (constraint half instead of coaching half) silently weakens a hard boundary; the diff-against-`cf84742` check in AC-3.3 is the only guard, so the kept-sections list must be checked, not assumed, after every cut commit.

**Integration with later stories.** Story 4 works on `implement-story.md` frontmatter and does not touch the base files this story cuts. Story 5 reverts Stories 2 and 3 as one commit range if the baseline re-run falls short of 8/8 (Business Rule 10) — every commit in this story must therefore be independently revertible as part of that range, which is why ledger rows land in the same commit as their removal (Business Rule 4) rather than being batched at story close.

## Definition of Done

- [ ] All tasks completed
- [ ] All acceptance criteria met
- [ ] Tests passing
- [ ] Code reviewed
- [ ] Documentation updated

## Context for Agents

- **Error map rows** [technical-spec.md → ## 1. `scripts/prune-ledger.py` (Story 1) → Findings table: `removed_not_in_ledger`, `over_cap`] [technical-spec.md → ## 3. Move targets (Story 2) → cross-reference for the base byte count entering this story]
- **Shadow paths** [spec.md → 🎯 Experience Design → Error experience → "A kept line accidentally reflowed"] [spec.md → 🎯 Experience Design → Error experience → "A removal without a ledger line"]
- **Business rules** [spec.md → 📋 Business Rules → 1 (constraint test is the rule, bytes are the finish line)] [spec.md → 📋 Business Rules → 3 (removed includes moved; reason classes)] [spec.md → 📋 Business Rules → 4 (ledger rows land in the removal commit)] [spec.md → 📋 Business Rules → 5 (kept lines byte-identical against cf84742)] [spec.md → 📋 Business Rules → 7 (one model-specific line per model per adapter)] [spec.md → 📋 Business Rules → 8 (Prime Directive mirror stays byte-identical)] [spec.md → 📋 Business Rules → 12 (decision-log line)]
- **Experience** [spec.md → 🎯 Experience Design → Happy path, step 3] [spec.md → 🎯 Experience Design → State catalog → "cuts in progress" / "cap reached"]
- **Requirements** [spec.md → Detailed Requirements → Story 3 — Cut behavior requests]
- **Codebase** [technical-spec.md → ## 4. Cut candidates (Story 3) → classification table columns, candidate sections and bytes, kept-verbatim list, needed cut arithmetic] [technical-spec.md → ## 2. Ledger format (Story 1) → row format and class vocabulary] [.writ/research/2026-09-05-goldilocks-harness-research.md → the constraint-vs-behavior-request test] [system-instructions.md, commands/_preamble.md → the two files being cut] [adapters/claude-code.md, adapters/cursor.md, adapters/codex.md, adapters/openclaw.md → destination for the batching line] [cursor/writ.mdc → Prime Directive mirror to keep in sync]
