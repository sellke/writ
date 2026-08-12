# Story 6: Prove the Gate Bites — Mutation, Then Revert

> **Status:** Not Started
> **Priority:** High
> **Dependencies:** Story 5

## User Story

**As a** Writ maintainer who has just made four checks and a byte budget blocking
**I want to** each gated property broken on a real file, observed red, and reverted — one at a time
**So that** "the gate works" is a run I can point at rather than an inference from a green suite, because a green suite is exactly what a gate that silently stopped working also produces

## Acceptance Criteria

- [ ] Given a clean tree, when `bash scripts/eval.sh` runs, then it exits 0 — the baseline every mutation is measured against, recorded before any mutation.
- [ ] Given a real command file padded past 24,960 bytes, when `bash scripts/eval.sh --check=leanness` runs, then it exits **non-zero**, the report FAILs, and the finding names that file with its measured bytes, the budget, and the overage. Reverted, the run is green again.
- [ ] Given a real command with its `problem:` frontmatter field removed, when the eval runs, then it FAILs with a finding naming **that file and that field**. Reverted, green.
- [ ] Given a real command with its `## Completion` section removed, when the eval runs, then it FAILs naming that file and the exact heading it wants. Reverted, green.
- [ ] Given a real loop-bearing command with `loop.max_iterations` removed, when the eval runs, then it FAILs naming that file and that field. Reverted, green.
- [ ] Given a real agent with a contract field removed from its config carrier, when the eval runs, then it FAILs naming that file and that field — both carriers (`## Agent Configuration` plain fence and `## Agent Specification` ```yaml fence) exercised at least once across the story.
- [ ] Given `.writ/leanness-baseline.json` carrying a bound justification naming the surface of an over-budget command at an inflated value, when the eval runs, then the budget finding is **still present and still blocking**. A justification explains growth against a baseline; it has no meaning against an absolute budget (Business Rule 3).
- [ ] Given an `eval-exempt: length` marker added to an over-budget command, when the eval runs, then the **byte cap still FAILs** — `eval-leanness.py` has no exemption reader, so the marker cannot reach it. Asserted so non-silenceability is a demonstrated property, not a claim in a comment.
- [ ] Given `required_skills:` naming a non-existent skill on a real command, when the eval runs, then it produces a **non-blocking** `WARNING` and `eval.sh` exits **0** — the graceful-degradation pin survives the flip in the live gate, not only in fixtures. Reverted, green.
- [ ] Given every mutation reverted, when `git status` runs, then the tree is **clean** and `bash scripts/eval.sh` exits 0. No mutation survives the story.
- [ ] Given `python3 scripts/eval-loop-bounds.py` after this story, when the `governor-boundary-intact` scenario runs, then it **passes** — asserted, not assumed, because "we did not touch it" is not evidence.
- [ ] Given the story completes, when its Notes are read, then each mutation is recorded with the command run, the exit code, and the finding text observed — a reader must be able to see the gate bite without re-running it.

## Implementation Tasks

- [ ] 6.1 Record the clean-tree baseline: `bash scripts/eval.sh` exit code and report path
- [ ] 6.2 Set up the mutation harness on a **scratch copy or fixture root** — never the committed tree — following the discipline `EvalShBoundaryTests` established in `2026-08-11-governor-instrumentation` Story 7
- [ ] 6.3 Mutation A — byte budget: pad a real command past 24,960; assert FAIL, exit non-zero, and the finding names file/bytes/budget/overage; revert; assert green
- [ ] 6.4 Mutation B — contract presence: remove a `problem:` from a real command; assert FAIL naming file and field; revert; assert green
- [ ] 6.5 Mutation C — `## Completion`: remove the section from a real command; assert FAIL; revert; assert green
- [ ] 6.6 Mutation D — loop bounds: remove `loop.max_iterations` from a real loop-bearing command; assert FAIL; revert; assert green
- [ ] 6.7 Mutation E — agent carrier: remove a contract field from a real agent, covering both carrier forms across the story; assert FAIL; revert; assert green
- [ ] 6.8 Mutation F — justification immunity: plant an inflated bound justification over an over-budget command; assert the budget finding survives; revert
- [ ] 6.9 Mutation G — exemption immunity: add `eval-exempt: length` to an over-budget command; assert the byte cap still FAILs; revert
- [ ] 6.10 Mutation H — graceful degradation: point `required_skills:` at a non-existent skill on a real command; assert non-blocking WARNING and exit 0; revert
- [ ] 6.11 Assert `governor-boundary-intact` passes in `python3 scripts/eval-loop-bounds.py`
- [ ] 6.12 Assert the tree is clean (`git status --porcelain` empty for mutated paths) and `bash scripts/eval.sh` is green
- [ ] 6.13 Record every mutation's command, exit code, and observed finding text in the Notes
- [ ] 6.14 Raise `surfaces.scripts.justifications.{lines,chars}` for this story if it grew `scripts`, dated, naming this story
- [ ] 6.15 Verify acceptance criteria and run the full suite: all `scripts/tests/*.py`, `test_eval_leanness.sh`, `eval-loop-bounds.py`, and `bash scripts/eval.sh`

## Notes

**Technical considerations:**

- **A green suite is not evidence of a working gate.** It is equally consistent with a gate that stopped asserting anything — which is precisely what Story 5 found in two tests that kept passing after the flip by matching a comment instead of a statement. The only proof that a gate bites is watching it bite, on the real tree, once per gated property.
- **One property per mutation, reverted before the next.** A batch mutation that produces a red run tells you *something* failed, not that each check independently does. The whole value is the one-to-one correspondence between the property broken and the finding named.
- **Mutations F and G are the ones that would be easiest to skip and hardest to recover.** They test the *absence* of a silencing path — the property Business Rules 1 and 3 exist for — and absence is exactly what unit tests over fixtures assert least convincingly. If a real `eval-exempt:` marker or a real justification could quiet the budget, this is where it shows.
- **Mutation H proves the pin survives into the live gate.** Instrumentation Business Rule 6 and `system-instructions.md` both require unresolvable skill names to warn and never hard-fail. The fixture tests assert it; this asserts it in a FAILing-capable, post-flip `eval.sh` run.
- **The committed tree is never mutated.** Scratch copy or fixture root, per the discipline instrumentation Story 7 established. The story's exit condition is a clean `git status`.

**Risks / challenges:**

- **This is the story most likely to be quietly skipped.** It is slow, it edits real files, and every assertion is about a state the implementer must deliberately create and then undo. The cheap substitute — asserting the same properties against fixtures — is what the existing suite already does, and it cannot tell you whether the *real* gate on the *real* tree bites. If the mutation run genuinely cannot be automated in this harness, record the reduced coverage in the drift log honestly rather than claiming a proof that was not run.
- **A mutation left behind is a red tree for everyone.** Now that the gate blocks, an un-reverted mutation does not merely produce a stale warning — it fails every subsequent run until someone finds it. Task 6.12's clean-tree assertion is not ceremony.
- **Blocking gates can block their own fix.** If a real regression lands, every subsequent commit fails `eval.sh` until it is trimmed — including a commit that is trimming it across two steps. `file_has_exemption()` is the escape hatch that exists and Business Rule 1 forbids it. The deliberate disposition: the emergency escape is `git revert` of the commit that broke the budget — reversible, reviewable, and self-expiring — not a marker in a file that outlives the emergency by months. This story is where that path gets exercised for real; record how it felt.
- **`governor-boundary-intact` is a literal grep.** `scripts/eval-loop-bounds.py:539-555` checks for the string `check_loop_bounds` in `eval-leanness.py` and degrades to a reported skip if absent. Nothing in this spec renames it — but a refactor during Stories 2 or 5 could, and the failure mode is a silent skip rather than a failure. Assert the pass, do not read for it.

**Integration points:**

- Depends on Story 5 — there is no blocking behavior to prove before the flip.
- Exercises Story 2's cap, Story 4's gate (which must go red under Mutation A and green after the revert), and every one of the four contract checks.
- `scripts/eval-loop-bounds.py` — read-only, asserted.
- Closes the spec. Its recorded mutation log is the evidence a reviewer reads instead of re-running the story.

## Definition of Done

- [ ] All tasks completed
- [ ] All acceptance criteria met
- [ ] Tests passing
- [ ] Code reviewed
- [ ] Documentation updated

## Context for Agents

- **Business rules:** [Rule 1 (no exemption path — Mutation G proves it structurally); Rule 3 (an absolute cap is not silenceable by a justification — Mutation F); Rule 4 (every blocking finding names the exact file and field — asserted in every mutation's finding text)] — from spec.md → 📋 Business Rules
- **Detailed requirements:** [The mutation proof — the mutation list, the scratch-copy discipline, the `governor-boundary-intact` assertion, and the clean-tree exit condition] — from spec.md → ## Detailed Requirements → ### The mutation proof
- **Error map rows:** [Mutation left in the tree after Story 6 → non-clean `git status` fails the story; rescue is `git checkout` of the mutated path] — from sub-specs/technical-spec.md → ## Error & Rescue Map
- **Contract:** [Hardest constraint: "This spec turns a green suite red the moment any file regresses" — this story is where that claim is tested rather than asserted; hard constraint 6: keep `governor-boundary-intact` passing] — from spec.md → ## Contract (Locked)
