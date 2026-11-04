# Evidence-Gated Review (Lite)

> Source: .writ/specs/2026-11-04-evidence-gated-review/spec.md
> Purpose: Efficient AI context for implementation

## For Coding Agents

**Deliverable:** Gate 3 and `/review` findings block only with executed evidence. The reviewer filters and the review panel are removed. The Safety Fact floor becomes `tested`.

**Implementation Approach:**
- `review-override.py evidence` sits beside `check`, `switch`, and `safety-fact`. It reuses `_inside`, `_cite_ok`, and `_emit`, and copies the `review-panel.py` parser patterns rather than importing them.
- The four evidence kinds (`test`, `recorded`, `check`, `security-path`) are defined in `skills/evidence-gated-findings/SKILL.md`. Agents get one `Read` line and one `**Evidence:**` field.
- Repros run in the working tree, with a git snapshot taken before and after. The executable comes only from `Test Runner` or Gate 2's recorded commands.
- Gate 3 order: `check` → `safety-fact` → `evidence`. The decision table is in spec.md § Gate 3 decision.

**Files in Scope:**
- `scripts/review-override.py`: `evidence` subcommand, `evidence-gate` switch, `FLOOR = "tested"`, `reviewer-filters` removed
- `skills/evidence-gated-findings/SKILL.md`: new. `skills/review-judgment-filters/`: deleted
- `commands/implement-story.md` Gate 3, `commands/review.md`, `agents/evaluator-agent.md`, `agents/review-agent.md`
- `scripts/review-panel.py`: `status`/`tally` removed, trial helpers kept
- `.writ/docs/config-format.md`, `adapters/*.md`, `scripts/eval.sh`, `.writ/decision-records/adr-032-evidence-gated-review.md`

**Error Handling:**
- No `Test Runner` or no git → `unverifiable`, and the agent FAIL stands.
- Collection error, timeout, unknown runner, or bad path → that finding is `unverifiable` (advisory).
- Tree changed after a run → `fail repro_mutated_tree` → BLOCKED.

**Line Budget Constraints:** `implement-story.md` must have a net byte change ≤ 0 across Stories 3, 4, 6, and 7.

---

## For Review Agents

**Acceptance Criteria:**
1. An agent FAIL with only unbacked findings becomes PASS with advisory lines. With one confirmed repro, it stays FAIL. `[AC-3.1, AC-3.5]`
2. Each kind confirms only under its rule (runner test-failed class; recorded failure; changed-file check output; resolving source and sink). `[AC-2.3, AC-2.4]`
3. A tree mutation is BLOCKED and names the paths. The repro file is always deleted. `[AC-2.5]`
4. On re-review, a missing, modified, or still-failing prior repro fails Gate 3. `[AC-4.2, AC-4.3]`
5. `/review` shows unconfirmed Critical and High findings as `Medium (unconfirmed)`, and says not-ready only on confirmed findings. `[AC-5.1, AC-5.2]`
6. Filters and panel are gone from shipped files. A leftover `Review Panel` line and `--panel` point to ADR-032. `[AC-6.2, AC-7.4]`
7. `safety-fact` on a traced-only section returns `safety_fact_below_floor`. `[AC-6.3]`

**Business Rules:**
- Large-drift PAUSE is unchanged. `check` and `safety-fact` routing is unchanged.
- A blocking finding is Critical or Major, cites an AC ID or is security or architecture, and has its location in the change set.
- The reviewer never chooses the executable. Each run has a 120 s timeout, and each call allows at most five runs.
- The coder commits a confirmed repro byte-for-byte and never edits it. Disputes go to the loop cap and then to the user.
- `Evidence Gate: off` restores the agent verdict for the whole story.

**Experience Design:**
- Entry: Gate 3 and `/review`, unchanged.
- Happy path: the repro fails → FAIL → the coder commits the repro and fixes the code → the repro passes → PASS.
- Moment of truth: `evidence-gate: 1 confirmed, 3 advisory, 0 unverifiable`.
- Feedback: one `finding Fn:` line per finding.
- Error: `evidence-gate: unverifiable (<reason>)` or `blocked (repro_mutated_tree …)`.

---

## For Testing Agents

**Success Criteria:**
1. Pytest on Python 3.9 and 3.14 covers each evidence kind: confirmed, unconfirmed, broken, no runner, mutation, prior removed or modified, bad security citation.
2. A replay fixture proves both Gate 3 decision outcomes.
3. A scan test finds no filter or panel names outside ADRs and history.
4. `eval.sh`, the bash suite, and `gen-platform-trees.py --check` pass.

**Shadow Paths to Verify:**
- **Happy path:** a FAIL with a `test` repro that fails on exit 1 → `fail`, manifest written
- **Nil input:** missing review output → `unverifiable no_review_output`
- **Empty input:** a FAIL with an empty Issues Found → `pass`, all counts 0
- **Upstream error:** missing runner binary → `unverifiable runner_not_found`

**Edge Cases:**
- Two findings with the same repro path → the second is `unverifiable path_exists`
- A `check` with `--fix` → BLOCKED by the snapshot
- `--review-only` → no recode; the evidence result decides PASS or FAIL

**Coverage Requirements:**
- New code ≥ 80%. Every reason code in technical-spec § Error & Rescue Map is tested.

**Test Strategy:**
- Stub runners are Python scripts that print each runner's output and exit with its code. A real pytest mini-project backs the `test` kind.
- Run pytest on its own, never alongside `eval.sh` or the bash tests.
