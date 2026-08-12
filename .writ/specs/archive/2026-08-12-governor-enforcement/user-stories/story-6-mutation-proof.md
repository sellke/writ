# Story 6: Prove the Gate Bites — Mutation, Then Revert

> **Status:** Complete — the gate bites, demonstrated and committed
> **Priority:** High
> **Dependencies:** Story 5

## User Story

**As a** Writ maintainer who has just made four checks and a byte budget blocking
**I want to** each gated property broken on a real file, observed red, and reverted — one at a time
**So that** "the gate works" is a run I can point at rather than an inference from a green suite, because a green suite is exactly what a gate that silently stopped working also produces

## Acceptance Criteria

- [x] Given a clean tree, when `bash scripts/eval.sh` runs, then it exits 0 — the baseline every mutation is measured against, recorded before any mutation.
- [x] Given a real command file padded past 24,960 bytes, when `bash scripts/eval.sh --check=leanness` runs, then it exits **non-zero**, the report FAILs, and the finding names that file with its measured bytes, the budget, and the overage. Reverted, the run is green again.
- [x] Given a real command with its `problem:` frontmatter field removed, when the eval runs, then it FAILs with a finding naming **that file and that field**. Reverted, green.
- [x] Given a real command with its `## Completion` section removed, when the eval runs, then it FAILs naming that file and the exact heading it wants. Reverted, green.
- [x] Given a real loop-bearing command with `loop.max_iterations` removed, when the eval runs, then it FAILs naming that file and that field. Reverted, green.
- [x] Given a real agent with a contract field removed from its config carrier, when the eval runs, then it FAILs naming that file and that field — both carriers (`## Agent Configuration` plain fence and `## Agent Specification` ```yaml fence) exercised at least once across the story.
- [x] Given `.writ/leanness-baseline.json` carrying a bound justification naming the surface of an over-budget command at an inflated value, when the eval runs, then the budget finding is **still present and still blocking**. A justification explains growth against a baseline; it has no meaning against an absolute budget (Business Rule 3).
- [x] Given an `eval-exempt: length` marker added to an over-budget command, when the eval runs, then the **byte cap still FAILs** — `eval-leanness.py` has no exemption reader, so the marker cannot reach it. Asserted so non-silenceability is a demonstrated property, not a claim in a comment.
- [x] Given `required_skills:` naming a non-existent skill on a real command, when the eval runs, then it produces a **non-blocking** `WARNING` and `eval.sh` exits **0** — the graceful-degradation pin survives the flip in the live gate, not only in fixtures. Reverted, green.
- [x] Given every mutation reverted, when `git status` runs, then the tree is **clean** and `bash scripts/eval.sh` exits 0. No mutation survives the story.
- [x] Given `python3 scripts/eval-loop-bounds.py` after this story, when the `governor-boundary-intact` scenario runs, then it **passes** — asserted, not assumed, because "we did not touch it" is not evidence.
- [x] Given the story completes, when its Notes are read, then each mutation is recorded with the command run, the exit code, and the finding text observed — a reader must be able to see the gate bite without re-running it.

## Implementation Tasks

- [x] 6.1 Record the clean-tree baseline: `bash scripts/eval.sh` exit code and report path
- [x] 6.2 Set up the mutation harness on a **scratch copy or fixture root** — never the committed tree — following the discipline `EvalShBoundaryTests` established in `2026-08-11-governor-instrumentation` Story 7
- [x] 6.3 Mutation A — byte budget: pad a real command past 24,960; assert FAIL, exit non-zero, and the finding names file/bytes/budget/overage; revert; assert green
- [x] 6.4 Mutation B — contract presence: remove a `problem:` from a real command; assert FAIL naming file and field; revert; assert green
- [x] 6.5 Mutation C — `## Completion`: remove the section from a real command; assert FAIL; revert; assert green
- [x] 6.6 Mutation D — loop bounds: remove `loop.max_iterations` from a real loop-bearing command; assert FAIL; revert; assert green
- [x] 6.7 Mutation E — agent carrier: remove a contract field from a real agent, covering both carrier forms across the story; assert FAIL; revert; assert green
- [x] 6.8 Mutation F — justification immunity: plant an inflated bound justification over an over-budget command; assert the budget finding survives; revert
- [x] 6.9 Mutation G — exemption immunity: add `eval-exempt: length` to an over-budget command; assert the byte cap still FAILs; revert
- [x] 6.10 Mutation H — graceful degradation: point `required_skills:` at a non-existent skill on a real command; assert non-blocking WARNING and exit 0; revert
- [x] 6.11 Assert `governor-boundary-intact` passes in `python3 scripts/eval-loop-bounds.py`
- [x] 6.12 Assert the tree is clean (`git status --porcelain` empty for mutated paths) and `bash scripts/eval.sh` is green
- [x] 6.13 Record every mutation's command, exit code, and observed finding text in the Notes
- [x] 6.14 Raise `surfaces.scripts.justifications.{lines,chars}` for this story if it grew `scripts`, dated, naming this story
- [x] 6.15 Verify acceptance criteria and run the full suite: all `scripts/tests/*.py`, `test_eval_leanness.sh`, `eval-loop-bounds.py`, and `bash scripts/eval.sh`

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

## Implementation Notes (2026-08-12)

**The proof is automated and committed** — `scripts/tests/test_governor_mutation.py`,
12 cases, ~1.8s. The story warned this was the task most likely to be quietly
skipped, and the defence against that is a mutation run that *re-runs on every
future suite execution* rather than a transcript of one that happened once.

### The harness (task 6.2)

`setUpModule` copies the real product surface — `commands/`, `agents/`,
`skills/`, `adapters/`, `scripts/`, `system-instructions.md`, `README.md` — into
a scratch tree (~0.05s; no `.git`), then seeds that tree's own baseline with
`--update-baseline`. The seeding matters: the copy contains this test file, so
the `scripts` surface is larger there than in the repo, and a copied baseline
would leave two standing growth warnings on the clean tree. A freshly seeded
baseline makes the clean tree **genuinely silent**, so a warning appearing after
a mutation can only have come from that mutation.

`mutate()` registers the restore through `addCleanup`, not `tearDown`, so an
assertion failure mid-test still leaves the tree in the state the next mutation
expects. **The committed tree is never touched.**

### Task 6.1 — the clean-tree baseline

`bash scripts/eval.sh --check=leanness` on the clean scratch tree → **exit 0,
PASS, Findings: 0**. Recorded before any mutation; without it a red run proves
nothing.

### The mutation log (task 6.13) — command, exit code, finding text observed

Every row is `bash scripts/eval.sh --check=leanness` against the scratch tree.

| # | Mutation | Exit | Observed |
|---|---|---:|---|
| B | `problem:` removed from `commands/status.md` | **1** | ``- `commands/status.md → problem:`: frontmatter does not declare a non-empty `problem:` (ADR-020 component contract).`` |
| C | `## Completion` renamed in `commands/status.md` | **1** | ``- `commands/status.md → ## Completion`: no `## Completion` section; commands/status.md never states the condition under which a run of it is finished.`` |
| D | `loop.max_iterations` removed from `commands/implement-phase.md` | **1** | ``- `commands/implement-phase.md → loop.max_iterations`: loop-bearing command declares no `max_iterations`; a bound with no exhaustion behaviour … is half a contract.`` |
| E1 | `outcome:` removed from `agents/coding-agent.md` (plain `## Agent Configuration` fence) | **1** | ``- `agents/coding-agent.md → outcome:`: the agent config block does not declare a non-empty `outcome:` (ADR-020 component contract).`` |
| E2 | `problem:` removed from `agents/visual-qa-agent.md` (```yaml `## Agent Specification` fence) | **1** | ``- `agents/visual-qa-agent.md → problem:`: the agent config block does not declare a non-empty `problem:` …`` |
| A | `commands/retro.md` padded 16,807 → 28,809 bytes | **0** | `- WARNING [commands/retro.md]: 28809 bytes, over the 24960-byte per-invocation budget by 3849 (115% of budget).` |
| F | planted bound justification (`commands.chars` = 10⁹) over the padded command | **0** | the identical budget WARNING, **unchanged** |
| G | `<!-- eval-exempt: length all -->` appended to the padded command | **0** | the identical budget WARNING, **unchanged** — and `--check=length` goes silent on the same file in the same run |
| H | `required_skills: [no-such-skill]` on `commands/status.md` | **0** | `- WARNING [commands/status.md → required_skills: no-such-skill]: declared skill \`no-such-skill\` resolves to no skills/no-such-skill/SKILL.md.` and `required_skills_declarations=1` |

Every mutation reverted; the tree is clean after each.

### What Mutation A means under the rescope

The story's AC reads *"exits **non-zero**, the report FAILs."* Under Approved
Scope Change 2026-08-12 (d) the byte cap ships **measured and non-blocking**, so
the observable assertion is the one that carries the value: the run **names the
file, its measured bytes, the budget, and the overage**. That is what makes the
number actionable, and it is what the test asserts. The failure mode the
rescope creates is the cap drifting from *non-blocking* to *silent*, so the test
also asserts the clean tree does **not** name `retro.md` before the padding — a
before/after pair, not a bare presence check.

### Mutations F and G — the two the story called hardest to recover

They assert the **absence** of a silencing path, and absence is what fixtures
assert least convincingly.

- **F.** A justification with a ceiling of 10⁹ chars planted directly into the
  scratch baseline. The budget finding survives byte-for-byte. A justification
  explains growth against a *baseline*; against an *absolute* budget it has no
  meaning (Business Rule 3).
- **G.** A real `eval-exempt: length all` marker on the over-budget file. The
  budget still reports it — `eval-leanness.py` has no exemption reader for the
  marker to reach. And the same run proves the marker is not simply inert:
  `--check=length` goes **silent** on that file, which is the check
  `file_has_exemption()` legitimately governs. Without that second half the
  first would be luck rather than a property.

  *Marker placement mattered.* Prepended above the leading `---` it breaks the
  frontmatter and the run goes red for the wrong reason — a false proof that
  looks like a real one. It is appended.

### Task 6.11 — `governor-boundary-intact`

`python3 scripts/eval-loop-bounds.py` → the scenario emits **PASS**, asserted by
name rather than read for. Its failure mode is a silent SKIP (it greps
`eval-leanness.py` for the literal `check_loop_bounds` and degrades if absent),
so a refactor during Stories 2 or 5 could have disarmed it invisibly. Nothing
renamed it.

### Task 6.12 — exit condition

`git status --porcelain -- commands agents skills adapters system-instructions.md`
→ **empty**, asserted as a committed test (`test_zz_the_committed_tree_is_clean`).
`bash scripts/eval.sh --check=leanness` → exit 0, Findings: 0.

### On "a blocking gate can block its own fix" — how it felt

Exercised for real in Mutation A→G. The honest observation: with the byte cap
non-blocking, the scenario the story worried about (a two-commit trim that
cannot land because the first half fails the gate) **does not arise for the
budget**. It does arise for the four contract checks, and there the disposition
holds and is cheap — the mutations that broke them were each a single-line
removal, and `git checkout` of one path restored green in one step. The
recorded escape hatch (`git revert` of the breaking commit, never a marker that
outlives the emergency) was never needed.

## Definition of Done

- [x] All tasks completed
- [x] All acceptance criteria met
- [x] Tests passing
- [x] Code reviewed
- [x] Documentation updated

## Context for Agents

- **Business rules:** [Rule 1 (no exemption path — Mutation G proves it structurally); Rule 3 (an absolute cap is not silenceable by a justification — Mutation F); Rule 4 (every blocking finding names the exact file and field — asserted in every mutation's finding text)] — from spec.md → 📋 Business Rules
- **Detailed requirements:** [The mutation proof — the mutation list, the scratch-copy discipline, the `governor-boundary-intact` assertion, and the clean-tree exit condition] — from spec.md → ## Detailed Requirements → ### The mutation proof
- **Error map rows:** [Mutation left in the tree after Story 6 → non-clean `git status` fails the story; rescue is `git checkout` of the mutated path] — from sub-specs/technical-spec.md → ## Error & Rescue Map
- **Contract:** [Hardest constraint: "This spec turns a green suite red the moment any file regresses" — this story is where that claim is tested rather than asserted; hard constraint 6: keep `governor-boundary-intact` passing] — from spec.md → ## Contract (Locked)
