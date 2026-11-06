# Lean Story Pipeline

> **Status:** Not Started
> **Created:** 2026-11-06
> **Owner:** @AdamSellke
> **Dependencies:** []
> **Origin:** Promoted from issue: `.writ/issues/improvements/2026-11-06-story-pipeline-over-prescribed.md`. Authored with `/create-spec`; decisions in [`recommendation-log.md`](recommendation-log.md).
> **Type:** Improvement. **Priority:** High. **Effort:** Large.

## Specification Contract

**Deliverable:** The default `/implement-story` path runs its deterministic checks through one `story-gate.py` call before review and one after. Every gate states the failure it catches and the evidence that it has caught one. Gates with no recorded catch move to `--full-pipeline`, and each story runs only targeted tests.

**Must Include:** `story-gate.py` writes one record per story, keyed to the head SHA it checked. Without that record the supervisor rejects the story, so a lane cannot skip a check and still pass (retro F6).

**Hardest Constraint:** 42 test and eval files pin text in `commands/implement-story.md`. Demotions and the runner must update those pins without weakening what they guard. `test_gate_upgrade_trial_outcome.py` also ties each kept upgrade to a presence probe in that file.

**🎯 Experience Design:**
- **Entry point:** `/implement-story`, `/implement-spec`, or an `/implement-phase` lane.
- **Happy path:** coder runs targeted tests → `story-gate.py run --phase pre-review` → Gate 3 agent → `story-gate.py run --phase post-review` → completion.
- **Moment of truth:** the story report shows one `story-gate:` line per phase, listing each check's verdict. The supervisor reads the record instead of re-running the checkers.
- **Feedback model:** report lines plus `.writ/state/story-gate-<story-stem>.json`.
- **Error experience:** a failing check prints its typed reason and the gate to restart (same recode and BLOCKED paths as today). `unverifiable` still continues and never marks a story `⚠️ DEGRADED`.

**📋 Business Rules:**
1. Every entry in `implement-story.md`'s `gates:` frontmatter declares `catches:` (the failure and the cost of missing it), `evidence:` (a cited recorded catch, or `none recorded`), and `kill_when:` (a checkable removal condition). `verdict-provenance.py check` fails an entry that lacks any of the three. This applies ADR-023 rule 6.
2. A gate whose `evidence:` is `none recorded` runs only under `--full-pipeline`. Its script, tests, and agent stay in the product. Nothing is deleted.
3. The removal-trial keep verdicts (Safety Fact, Reviewer Filters, Gate 0 Divergence) and the ADR-032 evidence gate are not reopened. They stay on the default path along with the inputs they need, such as the risk route that turns Safety Fact on.
4. `story-gate.py run --phase pre-review|post-review` runs the default-path checker scripts in a fixed order. It prints one JSON document with a verdict for each check and an overall verdict, writes the record atomically, and exits. It never spawns, polls, or sleeps (ADR-029 rules 1–2). Today's `unverifiable` semantics carry over unchanged.
5. A story reaches `Completed ✅` only when its `post-review` record names the head SHA of the story's final code commit. A code commit after the record needs a new record.
6. The coding agent and the Gate 3 agents run only the story's targeted tests. Reviewers read `recorded_test_results`. The full suite runs once per spec, at `implement-spec` Step 4.1, and `/ship` runs it for a standalone story.
7. `story-gate.py tally` reports, per gate, how many local records it changed a verdict in. Tally only reports: it never demotes or removes a gate.
8. The rule that limits agents to files the tasks name is unchanged ([lean-story-tasks](../2026-11-06-lean-story-tasks/spec.md) Business Rule 6).

**Success Criteria:**
- The default path in `implement-story.md` names at most 4 script invocations: context assembly, the two `story-gate` calls, and commit provenance. The file's byte size goes down.
- `verdict-provenance.py check` passes with all three fields present on every gate.
- Trial: one small archived spec is run through the default pipeline before and after, in worktrees cut from the same commit. The report compares blocking findings, Major+ defects that escape review, review iterations, wall-clock time, and tokens. More escaped defects counts as a regression, and the report says so.
- Both pytest interpreters, the bash tests, and `eval.sh` stay green, and `gen-platform-trees.py --check` is clean.

**Scope Boundaries:**
- Included:
  - `commands/implement-story.md` and `commands/implement-spec.md` (drop Step 2.3; regenerate `context.md` once per story)
  - `agents/supervisor-agent.md` and the coding, evaluator and review agents' test instructions
  - new `scripts/story-gate.py` with tests
  - the `verdict-provenance.py` extension
  - an ADR-029 note on what separates this runner from a dispatcher
  - generated platform trees
  - the trial report
- Excluded:
  - the file-creation rule
  - story task wording (lean-story-tasks covers it)
  - deleting any gate script
  - reopening the keep verdicts
  - retro F7/F8/F26 additions
  - `/implement-phase` lane mechanics (F22)

**⚠️ Technical Concerns:**
- ADR-029 rule 4 bars "an umbrella binary, dispatcher, or tool registry". `story-gate.py` is one command's fixed step, not a router across commands, and Story 3 records that distinction in ADR-029. If the distinction doesn't hold up in review, the fallback is to trim the prose and drop the runner.
- `.writ/state/` is gitignored, so tally data stays on one machine. Kill criteria can be checked locally, not across clones.
- One trial spec can show a regression but cannot prove an improvement.

**💡 Recommendations:**
- Evidence for `evidence:` comes from retros, drift logs, trial reports, and `gate3-review-*` records. A gate that cites none is demoted. Story 1 records the evidence in the spec as `gate-evidence.md` so every demotion can be traced back.

**⚠️ Cross-Spec Overlap:**
- `2026-10-25-gate-upgrade-removal-measurement` (In Progress) depends on presence probes in `implement-story.md`. They must keep passing (Business Rule 3).
- `2026-11-06-pr-ready-and-ledger` (Not Started): its ledger records the verified head per PR, while `story-gate` records are per story. The two share no file.

## Evidence

What the issue and this spec rest on, measured 2026-11-06:

- **Procedure size.** On the default path, `commands/implement-story.md` (38,551 bytes) has the orchestrator run 21 script subcommands. It also carries 14 `unverifiable` carve-outs, 16 `DEGRADED` rules, three `review-override.py switch` toggles, an opt-in Jev shadow, and a 9-row first-match evidence table.
- **Agents skip the procedure.** Phase 15 retro F6: lanes wrote code without spawning a coding agent and reviewed two stories in one Gate 3 pass. `exit-criteria.py` still returned `met`. The supervisor trial (`.writ/eval/supervisor-trial/report.md`) caught the same lane afterwards: `ESCALATE` on a report the checker had passed. Sample: one lane.
- **The full suite runs again and again.** Retro F21: coder, reviewer and lane each ran the full gates. Gate time was 3.2 h of lane 4's 4.6 h, and lane 2's reviewers ran the full suite 18 times.
- **Gates are cheaper to add than to remove.** The removal trial (`2026-10-25-gate-upgrade-removal-measurement`) built a 1,446-line harness and 309 tests over 4 baseline stories and 6 findings, and removed nothing. The default-path gates it did not cover (boundary map, change-surface routing, blast radius, drift-format, docs-check, app-verify) have no recorded measurement.
- **The core does the work.** The lean-story-tasks trial (`2026-11-06-lean-story-tasks/trial-report.md`) ran only Gate 1 and Gate 3. The evaluator caught and reproduced the one Major defect, a data-loss bug, and one recode fixed it.
- **Review loops are short.** In local execution records, most stories finish in 1 review iteration and a few take 2 or 3. The caps stay.

## 🎯 Experience Design

### User Journey

1. A developer runs `/implement-spec` (or `/implement-story`, or `/implement-phase` starts a lane).
2. Step 2 loads context. On the default path, Gate 0 and Gate 0.5 run only for checks that Story 1's evidence keeps there.
3. Gate 1: the coding agent writes tests first and runs only the story's targeted tests.
4. Gate 2: the orchestrator runs the project's linters and typecheck as today and saves the commands to `<checks>`.
5. The orchestrator runs `story-gate.py run --phase pre-review`. The record holds the change surface, the Gate 3 route, and any pre-review failure, with the gate to restart.
6. Gate 3: the evaluator, or `review-agent` on the risk route, reads `recorded_test_results` and does not run the full suite.
7. The orchestrator runs `story-gate.py run --phase post-review`. Override, safety fact, evidence, drift format, test integrity, and any surviving post-review checks run in a fixed order.
8. Step 4 completes the story. The report prints both `story-gate:` lines.
9. `/implement-spec` spawns the supervisor with the record path. The supervisor confirms that the record's head SHA is the story's final code commit, then checks the report's claims against the record and git.
10. After the last story, `implement-spec` Step 4.1 runs the full suite once.

### State Catalog

| State | What the developer sees |
|---|---|
| Every check passes | `story-gate: pass (phase post-review, N checks)`; story completes |
| One check fails | `story-gate: fail (<check>: <reason>)` plus `restart: gate1`, `gate2`, or `gate3`; the existing recode or BLOCKED path runs |
| A check cannot run | that check's line reads `unverifiable (<reason>)`; overall verdict is unaffected; never `⚠️ DEGRADED` |
| Code committed after the post-review record | supervisor returns `RERUN` with claim `story-gate record head <sha> ≠ final code commit <sha>` |
| No record at all | supervisor returns `RERUN`; a second `RERUN` is a story failure (existing rule) |
| `--full-pipeline` | the demoted gates run as today, in their own sections; `story-gate.py` still runs |
| `--quick` | both phases run. With no Gate 3 output, the review-dependent post-review checks print `unverifiable (no_review_output)`, and the record still satisfies Business Rule 5 |
| `story-gate.py` missing or crashes | the orchestrator reports `story-gate: unverifiable (<cause>)` and runs the default-path checks by hand from the technical-spec order. The story is marked `⚠️ DEGRADED`, because no record exists to check. |

### Interaction Patterns

- The orchestrator branches on line 1 of `story-gate.py` output and on the `restart:` line, never on prose.
- The report quotes the summary line verbatim; detail lives in the record file.

## 📋 Business Rules (Expanded)

Detail beyond the contract. The rules themselves are not restated; see the contract above.

- **Rule 1, evidence.** A recorded catch is a dated artifact that shows the gate changing an outcome: a retro finding, a drift-log entry, a trial report row, a `gate3-review-*` record, or a commit that fixed what the gate flagged. "Would catch X" is not evidence. `gate-evidence.md` holds one row per gate with the citation or `none recorded`.
- **Rule 1, kill_when.** It must be checkable from `story-gate.py tally` output or a named file, e.g. `sole_catches == 0 over 20 default-path records`. Prose such as "if it stops being useful" fails the check.
- **Rule 2, demotion.** The gate's section in `implement-story.md` moves under `--full-pipeline`, and its `gates:` entry gains `path: full-pipeline`. Tests that pin its default-path wording are changed to pin the full-pipeline wording, so nothing they guard is lost.
- **Rule 3, inputs.** If a kept gate reads another gate's output (Safety Fact reads the Gate 2.5 risk route and blast radius), that producer stays on the default path whatever its own evidence says. `gate-evidence.md` records the dependency as the reason.
- **Rule 4, order.** The check order inside each phase is fixed in the technical spec. The first `fail` sets `restart:`, but every check still runs, so the record is complete.
- **Rule 5, head SHA.** The record stores `git rev-parse HEAD` at the time it was written, plus the dirty-tree flag. A record written on a dirty tree that is not committed unchanged afterwards does not count.
- **Rule 6, targeted tests.** Targeted tests are the story's test files and any test file that imports a changed source file, as the orchestrator's recorded run already selects. A reviewer may run a single repro for the ADR-032 evidence gate. That is not a suite run.
- **Rule 7, catch.** For each check, tally counts `runs`, `fails`, and `sole_catches`: records where this check was the only `fail`.

## Detailed Requirements

- `scripts/story-gate.py` with subcommands `run` and `tally`, in the agent CLI check shape (`.writ/docs/agent-cli-contract.md`): the JSON record always printed as the last line, `--help`, exit codes 0/1/2, Python 3.9 stdlib, plus a row in that doc's script table.
- `scripts/verdict-provenance.py check` adds the finding codes `missing_catches`, `missing_evidence`, and `missing_kill_when`, and accepts the optional `path:` field (`default` or `full-pipeline`).
- `commands/implement-story.md`:
  - the `gates:` frontmatter carries the new fields
  - demoted gate sections move under `--full-pipeline`
  - the default path calls `story-gate.py` twice in place of the per-script blocks
  - Gate 4 text states targeted-test ownership
- `commands/implement-spec.md`:
  - Step 2.3 is removed (2.3b stays)
  - Step 3.3 stops regenerating `.writ/context.md`, because `implement-story` Step 4 already does
  - the supervisor spawn passes the `story-gate` record path
- `agents/supervisor-agent.md`: a new input `story_gate_record`, and a rule to read it and check its head SHA.
- `agents/coding-agent.md`, `agents/evaluator-agent.md`, `agents/review-agent.md`: test-run instructions per Business Rule 6.
- `.writ/decision-records/adr-029-*.md`: a dated note that a runner which runs one command's fixed check sequence is not a dispatcher.
- Generated trees (`claude-code/`, `cursor/plugin/`, `codex/`) regenerated with `python3 scripts/gen-platform-trees.py`.
- `trial-report.md` in this spec folder.

## Implementation Approach

- Story 1 records the evidence first, so every later demotion cites a row in `gate-evidence.md`.
- Story 2 demotes before Story 3 builds the runner, so the runner only ever covers the default set that remains.
- Story 3 replaces the per-script prose with two runner calls. The pinning tests move from "the command names script X" to "the runner runs check X on the default path", and a new test asserts that the runner's default check set equals the `gates:` entries whose `path` is `default`.
- Stories 4 and 5 both depend on Story 3 and do not share files: Story 4 edits the agents and Gate 4 prose, and Story 5 edits the supervisor and `implement-spec.md`.
- Story 6 runs the trial in worktrees outside the main checkout, with no pytest run in flight (CLAUDE.md).
- Byte size: `implement-story.md` must shrink (Success Criteria). `KNOWN_OVER_BUDGET` in `test_governor_enforcement.py` gets a dated entry for the new size.
