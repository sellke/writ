# Story 4: The Compliance Pre-Check Gate

> **Status:** Not Started
> **Priority:** High
> **Dependencies:** Story 2, Story 3

## User Story

**As a** Writ maintainer about to make four checks blocking
**I want to** a committed test that proves — against the real repo, not a fixture — that the surface already complies
**So that** "we checked before flipping" is a gate rather than a hope, and the same assertion keeps guarding the precondition long after the flip lands

## Acceptance Criteria

- [ ] Given the real repo, when the gate test runs, then it asserts every non-infra `commands/*.md` is ≤ `COMMAND_BYTE_BUDGET`, and on failure its message lists **every** violator with its measured bytes and its overage — not a bare boolean.
- [ ] Given the real repo, when the gate test runs, then it asserts `eval-leanness.py` returns `structural: []` under the **shipped** severity **and** `structural: []` under an in-process `CONTRACT_CHECK_SEVERITY = "structural"` pin. The second assertion runs the post-flip world before the flip is thrown; without it this story is a report, not a gate.
- [ ] Given the real repo, when the gate test runs, then it asserts `contract_compliance` is saturated on all four pairs: `commands_with_contract == commands_checked`, `commands_with_completion == commands_checked`, `loop_commands_bounded == loop_commands_checked`, `agents_with_contract == agents_checked` — and names the unsaturated pair with its counts on failure.
- [ ] Given the 2026-08-12 mechanism ruling retired `required_skills:` for this phase, when the gate test runs, then it asserts **no command declares `required_skills:`** — `required_skills_declarations == 0` in `eval-leanness.py`'s metrics, cross-checked by a direct grep over `commands/*.md` frontmatter so a parser change cannot make the assertion vacuous. On failure it names the declaring file and the skill names. A declaration is an **eager** pre-load: it moves those bytes into the floor, where every invocation pays them, and silently invalidates every ceiling figure the six disclosure specs certified against — **without changing any command's own byte count**, so assertion 1 cannot catch it.
- [ ] Given the gate test is red, when this story runs, then **the spec halts here**. Story 5 does not start. The story's output is a report naming which files are over budget, by how many bytes, and which of the six disclosure specs owned each (Contract hardest constraint; hard constraint 3).
- [ ] Given the gate test is red, when a remedy is considered, then **no exemption is granted** — no `eval-exempt:` marker in any file, no exemption reader added to `eval-leanness.py`, no budget raise to accommodate a violator. Wanting one means a disclosure spec is unfinished (Business Rule 1).
- [ ] Given the gate test after Story 5 lands, when it runs, then it is **still in the suite and still green** — it is the permanent regression guard for the state the flip depends on.
- [ ] Given a command pushed back over budget by a later commit, when the suite runs, then the gate test fails with that file named, its bytes, and its overage — before that regression reaches `eval.sh` and turns a whole run red for a reason nobody can locate.
- [ ] Given the gate test runs in a checkout where `commands/` is absent or unreadable, when it executes, then it fails with a message saying the tree could not be measured — never a false green from an empty file list.

## Implementation Tasks

- [ ] 4.1 Run the measurement first and record it: every non-infra command's byte count, the count over budget, and the total overage. This is the story's evidence whether it turns out green or red
- [ ] 4.2 Write the gate test — real repo, **four** assertions, failure messages that list violators rather than asserting booleans
- [ ] 4.3 Add the empty-tree guard: assert the command list is non-empty before asserting every member is under budget, so an unreadable tree cannot pass vacuously (instrumentation Business Rule 8's lesson, applied to a gate)
- [ ] 4.4 Add the in-process `"structural"` pin assertion, restoring the shipped value via `addCleanup` so a failure cannot leak the flipped constant into later tests in the same run
- [ ] 4.5 Run the gate. **If red: stop the spec, write the report — files, overage, owning spec — and do not start Story 5**
- [ ] 4.6 If green, record the passing measurement with its date in this story's Notes as the precondition Story 5's handoff comment will cite
- [ ] 4.7 Raise `surfaces.scripts.justifications.{lines,chars}` for this story, dated, naming this story
- [ ] 4.8 Verify acceptance criteria and that `bash scripts/eval.sh` is green end to end

## Notes

**Technical considerations:**

- **A committed assertion is what makes this a gate.** A pre-flight check the implementer runs once and reports on is a ritual: it proves nothing after the moment it ran, and nothing stops the next commit from undoing it. A test in the suite fails on every future run that breaks the precondition — which is the only version of "verify before flipping" that survives the person who verified.
- **The in-process `"structural"` pin is the load-bearing assertion.** Asserting `structural: []` under the shipped `"warnings"` severity proves nothing about the post-flip world — the contract findings would be in `warnings` either way. Pinning `"structural"` in-process and asserting the list is *still* empty is what proves the flip is safe. Restore the constant via `addCleanup`.
- **Three preconditions, four assertions.** The contract checks measure declarations; the budget measures bytes; the `required_skills:` assertion measures the *loading mechanism*. None implies the others. A fully contract-compliant surface can be 67KB over budget — exactly today's state. And a fully byte-compliant surface can carry a `required_skills:` declaration that moves skill bytes into the floor without changing a single command's size, which is invisible to every other assertion here and to `check_length` besides. The gate needs all three.
- **Why the `required_skills:` assertion is cheap and load-bearing.** The number already exists: `check_required_skills()` computes `required_skills_declarations` and `metrics` reports it. Story 1 is separately making it *visible* in the report; this story makes it *binding* in the gate — same number, two channels. Cross-check it against a direct frontmatter grep so that a future change to `parse_skill_names()` cannot turn a green assertion into a vacuous one; that is the same lesson as task 4.3's empty-tree guard, applied to a different parser.
- **What it is guarding against, concretely.** The six disclosure specs each certified a ceiling on the assumption that nothing is declared eagerly. A stray declaration — a copy-paste from `commands/new-skill.md`'s example, or a well-meant "make the skills discoverable" edit — converts a conditional load into an eager one for every invocation of that command, forever, and the only symptom is a number in a report nobody re-derives. This assertion is how it gets caught in the commit that introduces it rather than in a re-measurement months later.
- **The empty-tree guard is not padding.** `all_command_files()` on an absent `commands/` returns `[]`, and "every element of an empty list is under budget" is `True`. A gate that passes vacuously is the same defect instrumentation Business Rule 8 named in the metrics channel, and here it would green-light a flip against a tree nobody measured.
- **This story's red state is a legitimate outcome, not a failure of the story.** If the disclosure specs left work undone, the correct deliverable of this spec is the report, and the spec stops. That is the Contract's hardest constraint operating as designed.

**Risks / challenges:**

- **The pressure to make it green.** A red gate here blocks the spec's headline deliverable, and the cheapest paths to green are all forbidden: an `eval-exempt:` marker, an exemption reader, or a budget raise. Every one converts enforcement into decoration, and Business Rule 1 exists because that pressure is predictable. The measured, correct response is a report naming the owning disclosure spec.
- **A real-repo test is environment-coupled.** It reads the checkout it runs in, so it behaves differently in a shallow clone, a partial worktree, or a fixture root. Locate the repo root the way the existing suite does (`REPO_ROOT` in `scripts/tests/test_eval_leanness_contract.py`) rather than inventing a path scheme.
- **Constant leakage across tests.** Setting `CONTRACT_CHECK_SEVERITY` in-process without `addCleanup` leaves a flipped module for every test that runs after it in the same process. The existing `FlipSeamTests.setUp` already models the correct pattern — reuse it.
- **This story partially overlaps Story 2's cap**, deliberately. Story 2 builds an ongoing gate on bytes; this story asserts that *both* preconditions hold *simultaneously* and records the measurement the flip's handoff comment will cite. Same measurement, different question.

**Integration points:**

- Depends on Story 2's `COMMAND_BYTE_BUDGET` and `check_command_budget()`, and on Story 3 having settled the line limit so `eval.sh` is stable.
- Story 5 cannot start until this story is green. That is the sequencing the whole spec rests on.
- Story 6 mutates real files and asserts this test goes red — proving the gate is not merely green but *sensitive*.
- Reads `contract_compliance` from the JSON directly, not from the report, so it does not depend on Story 1 — but a maintainer reading a failure needs Story 1's output to interpret it.

## Definition of Done

- [ ] All tasks completed
- [ ] All acceptance criteria met
- [ ] Tests passing
- [ ] Code reviewed
- [ ] Documentation updated

## Context for Agents

- **Business rules:** [Rule 2 (the flip is gated on measured compliance, and the gate is a committed assertion); Rule 1 (no exemption to make the flip possible); Rule 4 (findings name the exact file so a red gate is actionable)] — from spec.md → 📋 Business Rules
- **Detailed requirements:** [The compliance pre-check gate — the three assertions, the halt condition, and why the test stays in the suite after the flip] — from spec.md → ## Detailed Requirements → ### The compliance pre-check gate
- **Error map rows:** [A command over budget when Story 4 runs → halt and report; the rescue is the owning disclosure spec finishing, never an exemption] — from sub-specs/technical-spec.md → ## Error & Rescue Map
- **Contract:** [Hardest constraint: "It may flip **only** once the surface actually complies; a flip that lands with known violations recreates the problem it exists to solve."; hard constraint 3: "Verify compliance before flipping, and make that a gate, not a hope."] — from spec.md → ## Contract (Locked)
- **Mechanism ruling:** [the gate's second condition — no command declares `required_skills:`; a stray declaration silently converts a conditional load into an eager one] — from spec.md → ## Approved Scope Changes, 📋 Business Rule 2
