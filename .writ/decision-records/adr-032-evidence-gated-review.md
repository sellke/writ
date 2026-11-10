# ADR-032: Evidence-Gated Review

> **Date:** 2026-11-04
> **Status:** Accepted
> **Category:** Framework Architecture
> **Deciders:** @AdamSellke
> **Origin:** [`2026-11-03-minimize-adversarial-review-surface`](../issues/improvements/2026-11-03-minimize-adversarial-review-surface.md), promoted to spec [`2026-11-04-evidence-gated-review`](../specs/archive/2026-11-04-evidence-gated-review/spec.md)
> **Amends:** [ADR-028](adr-028-behavioral-verification-and-cross-family-panels.md) Decision 3, the cross-family review panel, which this record removes, and the panel cases in Decision 4. Decisions 1 and 2 stand.
> **Keeps:** the reviewer filters of [`2026-10-25-review-route-rigor`](../specs/archive/2026-10-25-review-route-rigor/spec.md), which the removal trial kept (spec.md § Amendment, 2026-11-04).
> **Evidence base:** the inventory below, measured 2026-11-04 at commit `ef0c418`; the removal trial's [`trial-report.md`](../specs/archive/2026-10-25-gate-upgrade-removal-measurement/trial-report.md).

## Decision

**A Gate 3 or `/review` finding blocks only when it carries executed evidence. A finding without it is reported as advisory.**

- **Evidence kinds.** Each blocking finding carries one `Evidence:` block of one kind:
  - `test`: a new test file, run with `.writ/config.md`'s `Test Runner` scoped to that file. It confirms when the runner reports a test failure.
  - `recorded`: `path::test`, a test that failed in the orchestrator's recorded run.
  - `check`: a static-check command Gate 2 already ran, with reviewer arguments. It confirms when it exits non-zero and its output names a changed file.
  - `security-path`: for Major or higher security findings only. A `source: path:line` at a trust boundary and a `sink: path:line` in the change set. Both must resolve. Nothing runs.
- **One script confirms.** `scripts/review-override.py evidence` runs or validates each finding. It prints one line per finding and one verdict line. The reviewer never picks the executable. Each run has a 120-second timeout, and one call runs at most five repros. A run that changes any file outside its repro path is BLOCKED.
- **Gate 3.** An agent FAIL stays FAIL when it has a confirmed finding, a valid `security-path`, or a `check` or `safety-fact` script fail. Otherwise it becomes PASS, and its findings print as advisory. When the evidence step cannot run at all (no `Test Runner` and no runnable kind, no git, or a failed helper), the agent's FAIL stands.
- **Repros become regression tests.** On recode, the coder commits each confirmed `test` repro unchanged and fixes the code. On re-review, a repro that is missing, changed, or still failing fails Gate 3.
- **`/review`.** A Critical or High finding without confirmed evidence is reported as `Medium (unconfirmed)`. The Recommendation says not-ready only when a confirmed finding exists.
- **One removal, one change.** The review panel is removed. The Safety Fact floor rises from `traced` to `tested`. The reviewer filters stay.
- **One switch.** `- **Evidence Gate:** off` in `.writ/config.md` restores agent-verdict blocking for the whole story. An absent line means on.

Large-drift PAUSE at Gate 3.5 stays a human gate. `review-override.py check` and the `safety-fact` routing keep their current semantics. The Gate 3 decision table is in [`spec.md`](../specs/archive/2026-11-04-evidence-gated-review/spec.md) § Gate 3 decision.

## Context and Problem Statement

What holds on 2026-11-04:

- Gate 3 spawns `evaluator-agent`, or `review-agent` on the risk route. An agent FAIL sends the story back to Gate 1. `review-override.py check` can add a FAIL but never removes one. A FAIL needs no run: a finding the agent read and believed blocks the same way as one a test showed.
- Phase 15 added the reviewer filters ([`2026-10-25-review-route-rigor`](../specs/archive/2026-10-25-review-route-rigor/spec.md)). They tell a model how to weigh findings. It also added the Safety Fact, whose floor on the review-agent route is `traced`, a reading rung.
- Phase 12 added the cross-family review panel (ADR-028 Decision 3). A panel block needs two vendors to raise the same finding. The panel is available only on Cursor; OpenClaw is unverified.
- The origin issue asks for an inventory of every surface where a model argues with a change, with a keep, replace, demote, or remove verdict for each.
- The removal trial reported over the four Phase 11 baseline stories: Gate 0 Divergence keep (2 valid upgrade-only catches), Safety Fact keep (2), Reviewer Filters keep (1), Repro First unverifiable (never exercised). The labels are the assistant's, made at the maintainer's request (that spec's [`drift-log.md`](../specs/archive/2026-10-25-gate-upgrade-removal-measurement/drift-log.md) DEV-012). One valid catch keeps an upgrade, which the report calls a low bar. Those verdicts stand.
- The design-divergence blind trial reported `remove` the same day: declared axes won 2 of 6 briefs, and 4 were needed ([`trial-report.md`](../specs/archive/2026-10-25-design-divergence/trial-report.md)). That spec's Story 6 acts on it.
- `commands/implement-story.md` is 40,759 bytes and over its per-invocation budget ([`leanness-audit-2026-10-21.md`](../docs/leanness-audit-2026-10-21.md)).

A model's reading decides verdicts that a test could decide. The panel adds spawns to referee those readings with other models' votes.

## Decision Drivers

1. **A block needs a measurement.** A verdict that sends work back rests on something a script ran and saw fail. This extends "Verify the claim, don't trust it", which `/implement-story` already applies to agent claims at Gates 0, 3, 3.5, 4, and 5.
2. **No new spawn on the default path.** The evidence step is a script.
3. **Fewer instruction bytes.** Across Stories 3, 4, 6, and 7, the net byte change to `commands/implement-story.md` is zero or negative.
4. **Today's path when nothing can run.** A project with no `Test Runner` or no git keeps agent-verdict blocking.
5. **Leave pre-implementation surfaces alone.** Gate 0 and the discovery prompts run before code exists, so there is nothing to execute.

## Alternatives Considered

### Option A — Keep agent-verdict blocking and the panel

- **Pros:** No change. The Phase 12 trial kept the panel.
- **Cons:** A finding blocks on a reading. The panel adds up to three spawns per story to referee model findings with votes.
- **Effort:** None.
- **Risk:** Low change risk. How often a block is wrong stays unmeasured.

### Option B — Evidence-gated findings; drop the panel, keep the filters (chosen)

- **Pros:** Each block carries a repro the coder can run. A confirmed repro becomes a regression test. The panel goes, with its spawns. The filters, which the removal trial kept, stay.
- **Cons:** A real defect with no runnable repro stops blocking. The reviewer spends output tokens on a test file. Repros run in the user's working tree.
- **Effort:** Medium. One subcommand, one skill, Gate 3 and `/review` wiring, a floor change, and one removal (Stories 2 to 7).
- **Risk:** Medium. The tree snapshot catches a repro that writes outside its path, and a broken repro is advisory.

### Option C — Scripts only; drop the Gate 3 agents

- **Pros:** No Gate 3 spawn. Every verdict is mechanical.
- **Cons:** Nothing writes repros, so a defect that no existing test covers can never block. `review-override.py check` covers traceability and coverage, not behavior.
- **Effort:** Medium.
- **Risk:** High. Gate 3 would pass defects the agents catch today.

### Option D — Make the panel default-on

- **Pros:** More independent readers per story.
- **Cons:** Two vendors agreeing is still a reading. It adds one spawn per listed vendor on every story and works only on Cursor (ADR-028 § Platform reach).
- **Effort:** Small.
- **Risk:** Medium. Cost grows with no evidence beyond the Phase 12 trial's four stories.

### Option E — Option B, and drop the reviewer filters as well

This was the contract before the 2026-11-04 Amendment.

- **Pros:** 4,267 fewer instruction bytes. Filters 1 and 2 overlap the evidence step: only Critical and Major findings are evaluated, and an untraced hypothetical has no failing repro.
- **Cons:** It drops the only trial arm that raised F01, against the removal trial's `keep`.
- **Effort:** Small on top of B.
- **Risk:** Medium. A reviewer without the filters may stop raising the kind of finding F01 was.

## Decision Outcome

**Option B.** Driver 1 rules out A and D: both block on readings. C meets driver 1 but drops the agent that writes the repro, so a defect no current test covers could never block. B meets drivers 1 to 4. Driver 5 is met by scope: Gate 0 and the discovery prompts keep their behavior, and Gate 0 loses only its `--panel` qualifier. The user chose B over E on 2026-11-04, because the removal trial kept the filters (spec.md § Amendment).

**Measured verdicts.** The removal trial kept the reviewer filters on one valid catch, F01: a Critical `ac:AC-4.3` finding in `per-event-fee-revenue-model/story-4-messaging-migration-quick-split-guard`, where a doc still described the old behavior as current. The filters act on what a reviewer reports. The evidence step acts on what blocks. The same trial kept Safety Fact on two valid catches; this record keeps it and raises its floor to `tested`. The Phase 12 trial kept the panel on four valid findings that needed another vendor. This record removes it: the panel's job was to turn agreement between vendors into a block, and executed evidence replaces that rule.

## Review-Surface Inventory

Spawns are counted from the command and agent text. Bytes are `wc -c` on the named file, or on the named lines through `sed -n`, at commit `ef0c418`. Bytes count text in commands, agents, skills, and adapters. Reference docs under `.writ/docs/` and script code are not counted. Line numbers are as of that commit.

| Surface | Fact it tries to establish | Cost (spawns; instruction bytes) | Verdict | Reason |
|---|---|---|---|---|
| Gate 0 architecture check | The story's plan is buildable and fits the codebase before code is written | Spawns: 0 on default (`scripts/arch-check.py` runs); 1 `architecture-check-agent` on `--full-pipeline`, plus 1 anchor re-run on a floor ABORT. Bytes: 2,709 (Gate 0 text, `commands/implement-story.md` lines 166–192) + 8,654 (`agents/architecture-check-agent.md`, `--full-pipeline` only) | keep | It runs before code exists, so there is nothing to execute; the default path is already a script. |
| Gate 0 divergence | A second design shape for a boundary-crossing interface fits the caller's usage better than the first | Spawns: 2 sketches per story on the boundary-crossing route; 0 otherwise. Bytes: 1,994 (`commands/implement-story.md` lines 194–210) + 5,238 (`skills/design-divergence/SKILL.md`) | remove | Removed by design-divergence Story 6 on 2026-11-04, after its blind trial reported `remove` (the removal trial had kept it); this spec made no change to it. |
| `evaluator-agent` | Each acceptance criterion is met by the code and the recorded tests | Spawns: 1 per Gate 3 attempt on the default route; the review loop allows 3. Bytes: 9,705 (`agents/evaluator-agent.md`); 10,358 in `claude-code/agents/writ-evaluator.md` | demote | Its FAIL blocks only with confirmed evidence; its verdict stands alone only when the evidence step is unverifiable. |
| `review-agent` | The change meets its criteria and has no security, architecture, or drift defect on a high-risk route | Spawns: 1 per Gate 3 attempt on the risk route or `--full-pipeline`, in place of the evaluator; +1 re-spawn on a missing or below-floor Safety Fact. Bytes: 21,082 (`agents/review-agent.md`); 21,740 in `claude-code/agents/writ-reviewer.md` | demote | Same rule as the evaluator: an unbacked finding is advisory. |
| Reviewer filters | Which findings should change a verdict: nits and untraced hypotheticals should not, security findings should not be dropped | Spawns: 0. Bytes: 4,267 = 3,264 (`skills/review-judgment-filters/SKILL.md`, read on each Gate 3 spawn) + 294 (`commands/implement-story.md` line 298) + 444 (input row and `Read` line in `agents/evaluator-agent.md` and `agents/review-agent.md`) + 265 (`commands/review.md` line 60) | keep | The removal trial kept it on 1 valid catch, F01 ([`trial-report.md`](../specs/archive/2026-10-25-gate-upgrade-removal-measurement/trial-report.md)); spec.md Amendment (2026-11-04). |
| Safety Fact | The one fact the change is safe because of, and the evidence rung it reached | Spawns: 0 of its own; +1 `review-agent` re-spawn on `safety_fact_missing` or `safety_fact_below_floor`. Bytes: 7,505 = 5,692 (`skills/blast-radius/SKILL.md`) + 346 (Gate 2.5, `commands/implement-story.md` line 286) + 1,047 (Gate 3, lines 324–330) + 420 (`agents/review-agent.md` lines 50, 51, 198, 215) | replace | The floor moves from `traced`, a reading rung, to `tested`, a test in the recorded run; the routing is unchanged. |
| Review panel | Reviewers from other vendors raise blocking findings the primary missed | Spawns: 1 per listed slug (3 in this repo's `.writ/config.md`) on the risk route, `--full-pipeline`, the two-fail escalation, or `--panel`, on Cursor only. Bytes: 2,253 = 1,178 (`commands/implement-story.md` line 302) + 1,075 (the four `adapters/*.md` panel paragraphs) | remove | Agreement between vendors is a reading, not a run; one reviewer's confirmed repro now blocks without a second vendor. |
| `/review` | A diff's failure modes, shadow paths, and interaction edge cases are handled before landing | Spawns: 0; the session model reviews inline. Bytes: 10,593 (`commands/review.md`) | demote | A Critical or High finding without confirmed evidence is reported as `Medium (unconfirmed)`. |
| Jev shadow | A typed judgment model agrees with the evaluator's verdict on each criterion | Spawns: 0; 1 Jev API call per story through `scripts/jev-judge.py ac-shadow` when `status` prints `pass`. Bytes: 552 (`commands/implement-story.md` line 332) | keep | Out of this spec's scope; it is a report note that never changes a verdict. |
| `/security-audit` | The project has no vulnerable dependencies, committed secrets, insecure code patterns, or unsafe configuration | Spawns: 0 for review; 1 coding-agent spawn only when the user picks Auto-fix. Bytes: 18,234 (`commands/security-audit.md`) | keep | Out of this spec's scope; its scan phases already run tools, and it gates no story. |
| Spec analysis (create-spec Step 2.6c) | The generated stories' acceptance criteria have no contradiction, gap, or ambiguity | Spawns: 0; one orchestrator pass per `/create-spec`, plus 1 optional Jev call. Bytes: 2,453 (`commands/create-spec.md` lines 587–613) | keep | Out of this spec's scope; it runs before code exists, and its findings are notes that never block. |
| `visual-qa-agent` | The built UI matches the spec's mockups and visual references | Spawns: 1 at Gate 4.5 on `--full-pipeline` when the story has visual references; 0 on default. Bytes: 5,968 (`agents/visual-qa-agent.md`) + 236 (`commands/implement-story.md` lines 407–410) | keep | Out of this spec's scope; its mismatches are notes that never fail Gate 4.5. |
| Discovery challenge prompts | The user's idea, premise, or requested change is the right one to build | Spawns: 0. Bytes: 2,211 = 1,980 (the 11 lines with the word "challenge" in `commands/plan-product.md`, `commands/create-spec.md`, `commands/new-command.md`, and `commands/edit-spec.md`) + 231 (the three Premise Challenge questions, `commands/plan-product.md` lines 204–206) | keep | Out of this spec's scope; they question the user's idea, not code, and no test can stand in for them. |

## Removals

This record lists what the spec removes and the one thing it changes. The reviewer filters stay (spec.md § Amendment). The pruned-instructions ledger records none of this: it covers only lines removed from `system-instructions.md` and `commands/_preamble.md` (`scripts/prune-ledger.py` `BASE_FILES`), and this spec removes nothing from either. The tables follow [`technical-spec.md`](../specs/archive/2026-11-04-evidence-gated-review/sub-specs/technical-spec.md) § Removals.

### Safety Fact floor (Story 6)

This is a change, not a removal.

| File | Change |
|---|---|
| `scripts/review-override.py` | `FLOOR` becomes `"tested"`; the module docstring's `Floor:` line and its `(measured <m>, floor traced)` example change to `tested` |
| `skills/blast-radius/SKILL.md` | in the Evidence Ladder, "The floor is `traced`" becomes `tested`; the re-review advice for `safety_fact_below_floor` becomes "the measured rung is under `tested`. Cite a test from the recorded run; only the coder can add one." |

### Review panel (Story 7)

| File | Removed or changed |
|---|---|
| `scripts/review-panel.py` | the `status` and `tally` subcommands and their helpers `resolve`, `config_value`, `load_tally`, `cmd_tally`, and `cmd_status`, with their parser entries. Kept for the gate-upgrade-trial harness: `_prepare_run`, `PrepareError`, `parse_output`, `trial_key`, `_key_order`, `normalize_location`, `_issue_entries`, and the trial subcommands. Kept because `trial-record` calls them: `slug_vendor` and `origin_vendor` |
| `commands/implement-story.md` | the `--panel` invocation row and its conflict rule; the `--panel` qualifier in Gate 0's Route line; the **Review panel (opt-in)** paragraph; the panel `block` clause in Gate 3.5 § A; "A fail counts as a panel `block`" in the safety-fact paragraph, which becomes "A fail is one review-loop increment"; the `review-panel:` report line; the panel in the default spawn count; the words "panel reviewers" in Gate 3's **Reviewer filters.** paragraph, which stays |
| `.writ/docs/config-format.md` | the `Review Panel` row and section; a "Removed keys" line points to this record |
| `.writ/config.md` (this repo only; does not ship) | the `- **Review Panel:**` line |
| `adapters/claude-code.md`, `adapters/codex.md`, `adapters/cursor.md`, `adapters/openclaw.md` | the **Review panel (ADR-028)** paragraph |
| `.writ/docs/agent-cli-contract.md` | the `review-panel.py` row now lists only the remaining subcommands |
| `scripts/eval.sh` | the `review-panel` check and its function |

A `- **Review Panel:**` line left in a project prints `review-panel: removed (ADR-032)` once per story and does nothing else. `/implement-story --panel` stops with `--panel was removed (ADR-032)`.

Stories 6 and 7 also update the tests that assert on the changed or removed text, as technical-spec.md § Removals lists, and regenerate the platform trees with `python3 scripts/gen-platform-trees.py`.

## Consequences

**Positive**

- Every Gate 3 block comes with a repro the coder can run, and the repro stays as a regression test.
- The panel's spawns, up to three per story, go, with 2,253 bytes of command and adapter text.
- `/review` stops calling a diff not-ready on findings nobody showed.
- One switch restores today's blocking for a project that wants it.

**Negative, with mitigations**

- **A real defect with no runnable repro stops blocking.** Design smells and missing cases that no test can show become advisory. *Mitigation:* advisory findings print in full under `evidence-gate advisory:` lines, and `- **Evidence Gate:** off` restores agent blocking.
- **A security finding needs a citation to block.** Filter 3 still keeps an uncited security finding at Major, but that finding now blocks only with a resolving `security-path` or a confirmed repro. *Mitigation:* `security-path` needs no run, and its citations resolve the same way Safety Fact `read` lines do.
- **The filters and the evidence step overlap.** Filters 1 and 2 shape what a reviewer reports, and the evidence step already keeps nits and untraced hypotheticals from blocking. The filters' 4,267 bytes stay. *Mitigation:* the filters cost no spawn, and the removal trial measured a catch with them on.
- **The panel's cross-vendor catches go.** In the Phase 12 trial, four valid findings needed another vendor to raise them. *Mitigation:* any one reviewer's confirmed repro now blocks.
- **Review output grows.** A `test` repro is a whole test file in the review output. *Mitigation:* one file per repro, and at most five runs per call.
- **Repros run in the user's working tree with the project's dependencies.** *Mitigation:* the executable comes only from `Test Runner` or Gate 2's recorded commands. Each run has a 120-second timeout. A `git status` and diff snapshot before and after BLOCKs any change outside the repro path, and the repro file is deleted after its run.
- **A wrong repro can use up the review loop.** A repro with a wrong assertion still confirms, because the runner reports a test failure, and the coder cannot satisfy it. *Mitigation:* the loop's three-iteration cap and its escalation to the user.
- **A project without a `Test Runner` gains little.** Its `test` findings are `unverifiable`, and the agent FAIL stands. *Mitigation:* `recorded` and `security-path` work without a runner.

## Implementation Notes

**Steps** (spec `2026-11-04-evidence-gated-review`)

1. Story 2: `skills/evidence-gated-findings/SKILL.md` and `review-override.py evidence`.
2. Story 3: Gate 3 wiring in `commands/implement-story.md`, `agents/evaluator-agent.md`, and `agents/review-agent.md`.
3. Story 4: the repro manifest and `evidence --prior`.
4. Story 5: `/review` evidence gating, beside the filters' header and `Read` line.
5. Story 6: raise the Safety Fact floor to `tested`.
6. Story 7: remove the review panel, trim "panel reviewers" from Gate 3's filters paragraph, add the panel scan test, and close out the roadmap line.

**Success criteria:** pytest on Python 3.9 and 3.14 covers each evidence kind; a replay fixture turns an evaluator FAIL with only unbacked findings into PASS, and the same FAIL with one confirmed repro stays FAIL; a shipped-file scan finds no `Review Panel` or `--panel`; `bash scripts/eval.sh` and the bash suite pass.

**Review trigger:** reconsider when an advisory finding is later confirmed as a shipped defect, or when the evidence step returns `unverifiable` on most stories in a project, which means that project has fallen back to agent blocking.

## References

- [ADR-028](adr-028-behavioral-verification-and-cross-family-panels.md): the review panel this record removes
- [ADR-030](adr-030-contract-verifier-boundary-front-door.md): Phase 15 and its removal-measurement rule
- [`2026-11-03-minimize-adversarial-review-surface`](../issues/improvements/2026-11-03-minimize-adversarial-review-surface.md): the origin issue
- [`2026-11-04-evidence-gated-review`](../specs/archive/2026-11-04-evidence-gated-review/spec.md): the spec and its § Amendment; [`technical-spec.md`](../specs/archive/2026-11-04-evidence-gated-review/sub-specs/technical-spec.md) § Removals, § Error & Rescue Map
- [`2026-10-25-gate-upgrade-removal-measurement`](../specs/archive/2026-10-25-gate-upgrade-removal-measurement/spec.md) and its [`trial-report.md`](../specs/archive/2026-10-25-gate-upgrade-removal-measurement/trial-report.md): the removal trial that kept the filters, Safety Fact, and Gate 0 divergence
- [`2026-10-25-review-route-rigor`](../specs/archive/2026-10-25-review-route-rigor/spec.md): the spec that added the filters and the `traced` floor
- [`2026-10-25-design-divergence`](../specs/archive/2026-10-25-design-divergence/spec.md) and its [`trial-report.md`](../specs/archive/2026-10-25-design-divergence/trial-report.md): the blind trial that decides Gate 0 divergence
- [Phase 12 panel `trial-report.md`](../specs/archive/2026-10-01-cross-family-review-panel/trial-report.md): the panel trial
