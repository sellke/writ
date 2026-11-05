# Evidence-Gated Review

> **Status:** Complete
> **Created:** 2026-11-04
> **Owner:** @AdamSellke
> **Dependencies:** []
> **Phase:** 15 — Code-Level Rigor ([roadmap](../../product/roadmap.md), [ADR-030](../../decision-records/adr-030-contract-verifier-boundary-front-door.md))
> **Origin:** Promoted from issue: [`2026-11-03-minimize-adversarial-review-surface`](../../issues/improvements/2026-11-03-minimize-adversarial-review-surface.md)
> **Amends:** [2026-10-25-review-route-rigor](../2026-10-25-review-route-rigor/spec.md)

The amendment is partial. From `review-route-rigor` it replaces the `traced` floor only. The reviewer filters stay, because the `2026-10-25-gate-upgrade-removal-measurement` trial kept them (see the Amendment below). That trial's verdicts stand.

## Specification Contract

**Deliverable:** A Gate 3 or `/review` finding can block only when it carries executed evidence. That means a reviewer-supplied repro that a script runs and sees fail, a test that failed in the recorded run, or, for security, a cited input-to-sink path. Unbacked findings become advisory. The reviewer judgment filters and the review panel are removed, and the Safety Fact floor rises from `traced` to `tested`.

**Origin:** Promoted from issue: `.writ/issues/improvements/2026-11-03-minimize-adversarial-review-surface.md`

**Must Include:**
1. **Evidence grammar in one skill**, `skills/evidence-gated-findings/SKILL.md`. It replaces `skills/review-judgment-filters/`. Each blocking finding carries one `Evidence:` block of one of these kinds:
   - `test`: a new test file path and its full content, run through `.writ/config.md`'s `Test Runner` scoped to that file. Property-based tests count.
   - `recorded`: `path::test`, a test that failed in `recorded_test_results`.
   - `check`: a static-check command Gate 2 already ran for this story, with reviewer-supplied arguments. The output must name a file in the change set.
   - `security-path`: for Major+ security only. `source: path:line` (trust-boundary input) and `sink: path:line` (in the change set). Both citations must resolve.
2. **A confirm subcommand**, `review-override.py evidence`. It parses the review output's findings and runs each repro. Each finding gets `confirmed`, `unconfirmed`, or `unverifiable <reason>`, and the run ends with one verdict line.
3. **Gate 3 wiring** (`commands/implement-story.md`, `agents/evaluator-agent.md`, `agents/review-agent.md`, regenerated `claude-code/agents/`). A FAIL needs at least one confirmed finding, a valid `security-path`, or a script fail from `check` or `safety-fact`. An agent FAIL without any of these becomes PASS, and its findings move to advisory.
4. **Repro as regression test.** On recode, the coder commits each confirmed `test` repro verbatim at its declared path, and the script checks its hash. On re-review, the repro must be in the change set and pass in the recorded run. If it is missing or changed, Gate 3 fails with `repro_removed` or `repro_modified`.
5. **`/review` evidence gating.** Critical and High findings without confirmed evidence are reported as `Medium (unconfirmed)`. The Recommendation can say not-ready only when a confirmed finding exists.
6. **Subtractions:**
   - The Reviewer Filters skill, switch, config key, and consumer `Read` lines are removed.
   - The review panel's `status`/`tally` path, `--panel`, the `Review Panel` config key, and its eval check are removed. ADR-028 is amended.
   - The Safety Fact floor becomes `tested`.
   - Every removed line goes into `pruned-instructions-ledger.md`.
7. **One switch**, `- **Evidence Gate:** off` in `.writ/config.md`. It restores agent-verdict blocking. An absent line means on. It is resolved through `review-override.py switch`.
8. **Records:**
   - A new ADR for evidence-gated review, with a per-surface inventory table: keep, replace, demote, or remove.
   - Roadmap Phase 15 gains this feature, and its filters and traced-floor criteria are replaced.
   - `config-format.md` is updated.

**Hardest Constraint:** The script runs reviewer-written repros inside the user's project. They need the project's installed dependencies, so they run in the working tree, not a clean copy. Runners report a failing test and a broken test (collection or import error) differently. The run must leave the tree exactly as it found it. Rules:
- The repro path must be new and under a test directory.
- The script snapshots `git status --porcelain` and the diff hash before and after the run.
- If anything outside the repro path changed, the result is BLOCKED with `repro_mutated_tree`.
- A failure confirms only on the runner's test-failed exit class. pytest, jest/vitest, go test, cargo test, and rspec are classified. An unknown runner, a collection error, or a timeout makes that finding `unverifiable`, and the finding is advisory.

**🎯 Experience Design:**
- **Entry point:** `/implement-story` Gate 3 and `/review`, as today. Nothing new to invoke.
- **Happy path:**
  1. The reviewer writes a finding with a `test` repro.
  2. The script confirms it, and Gate 3 fails with the repro attached.
  3. The coder commits the repro and fixes the code.
  4. On re-review the repro passes, and Gate 3 passes.
- **Moment of truth:** the story report line `evidence-gate: 1 confirmed, 3 advisory, 0 unverifiable`.
- **Feedback model:** one line per finding: `finding <key>: confirmed (exit 1, tests/test_x.py::test_y)` or `advisory (<reason>)`.
- **Error experience:**
  - One broken repro makes that finding advisory, with the reason printed.
  - If the project has no `Test Runner` or the helper can't run, the result is `evidence-gate: unverifiable (<reason>)` and the agent verdict stands.
  - A tree mutation is BLOCKED and names the changed paths.

**📋 Business Rules:**
1. Large-drift PAUSE (Gate 3.5) does not change. It stays a human gate.
2. Each blocking finding cites an AC ID or a Critical/Major security or architecture defect. Its location must be in the story's change set.
3. Only the config `Test Runner` and the static-check commands Gate 2 recorded may execute. The reviewer never chooses the executable. Each run has a timeout.
4. The `review-override.py check` FAIL-only override and the `safety-fact` routing keep their current semantics. The only change is the floor, which becomes `tested`.
5. The three-iteration review loop counts confirmed-finding recodes the same way it counts recodes today. A repro the coder can't satisfy reaches the cap and goes to the user's existing escalation. The coder has no separate path to dispute a repro.
6. A `Review Panel` config line left in a project prints `review-panel: removed (ADR-NNN)` and does nothing else. `--panel` is rejected with that same pointer.
7. `Evidence Gate: off` applies to the whole story. Gate 3 and `/review` both print `evidence-gate: off`.

**Success Criteria:**
- Pytest on Python 3.9 and 3.14 covers each evidence kind with these fixtures:
  - confirmed
  - unconfirmed
  - broken repro → unverifiable
  - no Test Runner → agent verdict stands
  - tree mutation → BLOCKED
  - repro removed or modified on re-review
  - a security-path with a bad citation
- A replay fixture: an evaluator FAIL that has only unbacked findings yields Gate 3 PASS with advisory findings. The same FAIL with one confirmed repro yields FAIL.
- A shipped-file scan finds no `review-judgment-filters`, `reviewer-filters`, `Review Panel`, or `--panel` outside the ledger, ADRs, and history.
- `safety-fact` on a traced-only section returns `safety_fact_below_floor`.
- `bash scripts/eval.sh` exits 0, and the bash suite is green.

**Scope Boundaries:**
- **Included:**
  - Gate 3 (evaluator and review-agent)
  - `/review`
  - Safety Fact floor
  - removal of the filters and the panel
  - ADR, roadmap, config docs
- **Excluded:**
  - Gate 0 `architecture-check-agent` ABORT and design divergence. These are pre-implementation, and there is no code to run.
  - `/security-audit`, `visual-qa-agent`, the Jev shadow, and `/create-spec` Step 2.6c.
  - The discovery "challenge" prompts in `/plan-product`, `/create-spec`, `/new-command`, and `/edit-spec`.
  - New formal-verification tooling. The roadmap's watch item stays a watch item.

**⚠️ Technical Concerns:**
- `scripts/tests/test_panel_trial_outcome.py` ties the Phase 12 panel verdict to repo state. Removing the panel must update that test, not delete the evidence.
- `.writ/eval/gate-upgrade-trial/gate-upgrade-trial.py` reuses `review-panel.py`'s read-only checkout builder and finding-key parser. Keep those functions until that harness is deleted. Only the panel's `status`/`tally` path goes.
- A reviewer that has to write a whole test file inline costs output tokens. Keep the `test` kind to one file.

**💡 Recommendations:**
- Put the per-finding parser next to `safety-fact` in `review-override.py`, and reuse its `_inside` and `_cite_ok` for path checks. `review-panel.py` `parse_output` is the model for finding keys.
- Six stories:
  1. evidence skill and the confirm subcommand
  2. Gate 3 wiring and agents
  3. repro-as-regression-test on re-review
  4. `/review`
  5. removal of filters and panel, plus the Safety Fact floor
  6. ADR, roadmap, ledger, and config docs

**⚠️ Cross-Spec Overlap:**
- `2026-10-25-gate-upgrade-removal-measurement` (In Progress) decides keep or remove for Safety Fact and Reviewer Filters. This spec supersedes those two verdicts. Before this spec's Story 5, run `/edit-spec` on that spec to narrow its Story 4 to Gate 0 Divergence and Repro First. `spec.md` will carry `> **Amends:**` pointing at it.
- `2026-10-25-design-divergence` (In Progress) also edits `commands/implement-story.md`, but only Gate 0. Land Gate 3 edits after its Story 6, or rebase them on it.

### Corrections made at authoring (2026-11-04)

The contract above is the locked text. Package generation found four places where it does not match the repository. The rest of this package follows the corrections.

1. **Ledger (Must Include 6, last bullet).** `pruned-instructions-ledger.md` covers only lines removed from `system-instructions.md` and `commands/_preamble.md`. `scripts/prune-ledger.py` pins `BASE_FILES` to those two files. This spec removes nothing from either. ADR-032's inventory table records the removed files, sections, and keys instead. The ledger gets no rows.
2. **Test-path rule (Hardest Constraint, first rule).** Go keeps `*_test.go` next to the code, and Rust integration tests live in `tests/`. "Under a test directory" becomes "matches the runner's own test-file pattern" (technical spec § Repro Paths). The path must still be new and inside the repo.
3. **Story count (Recommendations).** Seven stories instead of six:
   - ADR-032 comes first, so later stories can link to it.
   - The panel removal becomes its own story, so neither removal story goes over seven tasks.
   - Each removal stays revertable on its own.
4. **`ADR-NNN` (Business Rule 6).** The next free number is `ADR-032`.

### Amendment (2026-11-04, during /implement-spec)

The user decided to keep the reviewer filters. The rest of the contract stands: evidence gating, the review panel removal, and the Safety Fact floor raise to `tested`.

**Evidence.** The removal measurement in [`trial-report.md`](../2026-10-25-gate-upgrade-removal-measurement/trial-report.md) (commit `ef0c418`) recorded Reviewer Filters `keep`: 1 valid upgrade-only catch on 4 stories. The catch is F01, Critical, `ac:AC-4.3`: a stale doc claim that still described the old behavior as current. The same trial kept Safety Fact, which fits with raising its floor. That spec's verdicts stand. This spec takes over none of them.

**What stays.** `skills/review-judgment-filters/`, the `reviewer-filters` switch, the `Reviewer Filters` config key, the agents' `reviewer_filters` input row and `Read` line, Gate 3's "Reviewer filters." paragraph, and `/review`'s Step 3 filters `Read` and switch line.

**Contract items this overrides:**
1. **Deliverable.** "The reviewer judgment filters and the review panel are removed" now reads: the review panel is removed.
2. **Must Include 1.** "It replaces `skills/review-judgment-filters/`" no longer holds. The new skill sits beside it.
3. **Must Include 6.** The Reviewer Filters bullet is dropped. The panel and floor bullets stand. The ledger bullet stands as corrected above.
4. **Must Include 8.** The roadmap's filters criterion stays. Only the traced-floor criterion changes.
5. **Success Criteria, shipped-file scan.** The filter names are dropped. The scan covers the panel names only: `Review Panel` and `--panel`.
6. **Scope Boundaries, Included.** "removal of the filters" is dropped. The panel removal stays.
7. **Recommendations, story 5.** It no longer removes the filters. Corrections item 3 already split its work into Story 6 (the floor) and Story 7 (the panel).
8. **Cross-Spec Overlap, the `/edit-spec` precondition.** Void. That spec's Story 4 already ran and removed nothing. This spec no longer amends it.

The rest of this package follows the Amendment.

**Post-implementation amendments (2026-11-04, user-approved).** Three expanded rules were corrected to match what shipped:
- `### Gate 3 decision`: the `repro_mutated_tree` row moved to row 1, ahead of the `check`, `safety-fact`, and prior-repro rows, because the Hardest Constraint makes any tree mutation BLOCKED (DEV-026). The old row 3a is now 4a.
- `### /review`: the consent step and the mutation stop (DEV-016, DEV-012).
- technical-spec `### Review panel (Story 7)`: `slug_vendor` and `origin_vendor` are kept (DEV-029).

## Experience Design

### Who uses it

- **The orchestrator running `/implement-story`.** At Gate 3 it saves the review output, runs `review-override.py evidence` after `check` and `safety-fact`, and acts on the result. On recode it hands the coder the confirmed repros. On re-review it checks that those repros are in place.
- **`evaluator-agent` and `review-agent`.** On FAIL, they attach an `Evidence:` block to every Critical or Major issue they want to block on. Without one, the issue still gets reported, but only as advisory.
- **The coding agent on recode.** It commits each confirmed `test` repro byte-for-byte and changes the code until the repro passes.
- **A developer running `/review`.** They see unconfirmed Critical and High findings reported as `Medium (unconfirmed)`, and a Recommendation that says not-ready only when something was confirmed.

### Journey (Gate 3)

1. The Gate 3 agent returns. If its verdict is PASS or PAUSE and no manifest exists for the story, Gate 3 continues as it does today and the evidence step does not run. If a manifest exists, `evidence --prior` runs on every verdict (step 5).
2. On FAIL, the orchestrator runs `review-override.py check` (unchanged), then `safety-fact` if it applies (unchanged except for the floor), then `review-override.py evidence`.
3. `evidence` resolves the `evidence-gate` switch and parses the issues. It runs up to five `test` and `check` repros in the working tree. It validates each `recorded` and `security-path` citation, then prints one line per finding and a verdict.
4. The orchestrator applies the § Gate 3 Decision table. On confirmed evidence, the recode brief carries each confirmed finding with its repro and the manifest path.
5. On re-review, `evidence --prior <manifest>` checks every confirmed repro before it evaluates any new findings.
6. The story report prints `evidence-gate: <c> confirmed, <a> advisory, <u> unverifiable`, or `evidence-gate: off`, or `evidence-gate: unverifiable (<reason>)`.

### State Catalog

| State | Story report line | Gate 3 result |
|---|---|---|
| Agent PASS | `evidence-gate: not run (PASS)` | PASS |
| Agent PAUSE | `evidence-gate: not run (PAUSE)` | PAUSE → Gate 3.5 |
| Agent FAIL, at least one finding confirmed | `evidence-gate: 1 confirmed, 2 advisory, 0 unverifiable` | FAIL → recode with the repros |
| Agent FAIL, nothing confirmed | `evidence-gate: 0 confirmed, 3 advisory, 1 unverifiable` | PASS, with the advisory findings listed |
| Agent FAIL, no `Test Runner` and no runnable kind | `evidence-gate: unverifiable (no_test_runner)` | FAIL stands |
| Agent FAIL, helper missing or exit 2 | `evidence-gate: unverifiable (<reason>)` | FAIL stands |
| A repro changed a file outside its own path | `evidence-gate: blocked (repro_mutated_tree <paths>)` | BLOCKED escalation |
| Re-review, prior repro missing, changed, or still failing | `evidence-gate: fail (repro_removed <path>)` | FAIL → recode |
| Switch off | `evidence-gate: off` | the agent's verdict |
| `check` script fail on any route | the line as above plus the `check` line | FAIL, as today |

### Interaction patterns

- Claim and measurement appear side by side, the same way `check` and `safety-fact` print them today.
- When an unconfirmed finding is downgraded, it is still reported in full. Downgraded findings go under `evidence-gate advisory:` lines, so a reader can see what the reviewer worried about.
- On recode, the coder gets the repro file itself, not a description of the bug.

## Business Rules (Expanded)

### Gate 3 decision

The order is `check`, then `safety-fact`, then `evidence`. Results are read in this order, and the first match decides:

| # | Condition | Result |
|---|---|---|
| 1 | `evidence` reason `repro_mutated_tree` | BLOCKED escalation (`evaluator-agent` or `review-agent`, restart Gate 3) |
| 2 | `check` line 1 is `fail` | FAIL → recode (unchanged) |
| 3 | `safety-fact` reason `safety_fact_contradicts_verdict` | FAIL → recode (unchanged; the reviewer wrote PASS) |
| 4 | `safety-fact` missing or below floor | existing re-review / BLOCKED / FAIL routing (unchanged) |
| 4a | A manifest from an earlier Gate 3 attempt on this story exists, and `evidence --prior` fails (`repro_removed`, `repro_modified`, `repro_still_failing`) | FAIL → recode, on any agent verdict |
| 5 | Agent verdict PASS or PAUSE | that verdict; `evidence` runs only the `--prior` checks when a manifest exists |
| 6 | `evidence-gate` switch `off` | the agent's FAIL stands |
| 7 | `evidence` line 1 `fail` | FAIL → recode with confirmed findings |
| 8 | `evidence` line 1 `unverifiable` | the agent's FAIL stands; reason printed; not `⚠️ DEGRADED` |
| 9 | `evidence` line 1 `pass` | PASS; every finding printed as advisory |

Row 1 comes first because the contract's Hardest Constraint makes any tree mutation BLOCKED, whatever the other rows say. A mutation can only come from an `evidence` run, so PASS and PAUSE routing does not change (drift-log DEV-026).

`safety-fact` reads the agent's own verdict line, not the verdict after the evidence step. A reviewer that writes `Holds: no` must FAIL, and the issue it raises at that location needs evidence like any other.

### Which findings are evaluated

- Only issues under `### Issues Found` with Severity `Critical` or `Major` are evaluated. In `/review`, that is registry rows with `Critical` or `High`. Lower severities are advisory and are never run.
- Each evaluated issue needs a Location inside the change set (the story's changed files, or the `/review` diff). A Location outside it makes the finding `advisory (location_outside_change_set)`.
- Each evaluated issue cites an AC ID or has Category `security` or `architecture`. Otherwise it is `advisory (no_claim)`.
- At most five `test` or `check` runs happen per `evidence` call. Later ones are `unverifiable repro_cap`. `recorded` and `security-path` cost no run and have no cap.

### Evidence outcomes

| Kind | Confirmed when | Advisory when | Unverifiable when |
|---|---|---|---|
| `test` | the scoped runner run lands in the runner's test-failed class | the run passes | unknown runner, collection or import error, timeout, path not new, path outside the repo, path not a test path |
| `recorded` | the recorded run has a non-zero exit, and its output names `path::test` as failed | the test is in the recorded run and passed | no recorded run (`/review`), or the test is not in the recorded run |
| `check` | the command starts with a Gate 2 recorded command, exits non-zero, and its output names a changed file | it exits 0, or it names no changed file | no Gate 2 record (`/review`), command not on the record, timeout |
| `security-path` | Category `security`, severity Major+, both citations resolve as `read` lines do, and the sink is in the change set | — | a citation fails to resolve (`bad_citation <token>`) |

A finding with no `Evidence:` block is `advisory (no_evidence)`.

### Execution rules

- The executable always comes from `.writ/config.md` `Test Runner`, or from a Gate 2 recorded command saved by the orchestrator to `.writ/state/gate2-checks-<story-stem>.txt`. The reviewer supplies only the repro file, or arguments after a recorded command.
- The default timeout is 120 seconds per run, set with `--timeout`.
- Each run is surrounded by the tree snapshot in technical spec § Tree Snapshot. The repro file is always deleted after its run, pass or fail.
- `evidence` never runs `git` commands that write. It reads `git status` and `git diff`.

### Repro as regression test

- Each confirmed `test` repro is recorded in `.writ/state/evidence-<story-stem>.json` (`evidence-manifest-v1`): finding key, path, SHA-256 of the normalized content, and kind.
- The recode brief tells the coder to create each repro at its path with exactly that content, then fix the code. The coder may not edit the repro.
- On re-review, `evidence --prior <manifest>` runs on every agent verdict, PASS included. It fails `repro_removed <path>` when the path is not in the change set, `repro_modified <path>` when the hash differs, and `repro_still_failing <path>` when the recorded run does not name the path or its `exit code:` line is not `0`. That is the same match rule `safety-fact` uses for `tested`. The re-review's recorded run includes every manifest path, so a failing repro makes the whole run non-zero.
- On an agent PASS or PAUSE, only the `--prior` checks run. New findings are not evaluated, because a PASS has nothing to downgrade.
- Normalization is the same on both sides: CRLF becomes LF, trailing whitespace is stripped from each line, and the file ends with exactly one trailing newline.

### /review

- Severity mapping: a Critical or High row without confirmed evidence becomes `Medium (unconfirmed)` in the registry. The row keeps its ID and description.
- Claim test: registry rows carry no AC IDs. On `--surface review`, any category (error handling, shadow path, interaction, security, architecture) can confirm. The confirmed evidence is the claim. The location rule still applies: the row's Location must be in the diff.
- Per-row `unverifiable` is downgraded the same way as no evidence. A run-level `unverifiable` (`no_review_output`, `no_git`, `no_test_runner` with no `security-path` rows) leaves every severity as written, and the header shows the reason. This matches the Gate 3 rule that the agent verdict stands.
- `/review` has no Major severity. For `security-path`, High counts as Major+.
- Recommendation: "Do not ship" and "Ship with caution" need at least one confirmed Critical or High finding. Otherwise the report says the code is ready to ship and lists the unconfirmed findings under the Recommendation as worth a look.
- Available kinds are `test` and `security-path`. `recorded` and `check` are `unverifiable kind_unavailable` because `/review` has no recorded run and no Gate 2.
- The header line `> Evidence gate: on|off|unverifiable (<reason>)` sits beside `> Reviewer filters: on|off`. Both lines stay in the header.
- Consent: the evidence step runs the branch's own test code in the user's working tree, so `/review` asks before every run. A decline, a headless run where nobody can be asked, or no answer skips the run and writes `> Evidence gate: unverifiable (untrusted_branch)`; every severity stays as written. With the gate `off`, `/review` asks nothing. The user chose always-ask over an author-email rule, because a commit's author email can be forged (drift-log DEV-016).
- A tree mutation during the run stops `/review` before any Recommendation or `/ship` hand-off, until the user decides (drift-log DEV-012).

### Switch

- `review-override.py switch --name evidence-gate` follows the existing resolution rules. An `off` value in any case turns it off. No line, an empty value, or `on` means on. Any other value means on with `malformed_value`.
- Off restores today's blocking for the whole story: the agent's FAIL stands, and `evidence` prints `evidence-gate: off` and runs nothing.

### Removals

- **Reviewer Filters.** Kept (Amendment).
- **Review panel.** These are removed:
  - `review-panel.py` `status`, `tally`, and their helpers
  - `--panel` and its conflict rule
  - the Gate 3 panel paragraph and the `review-panel:` report line
  - the words "panel reviewers" in Gate 3's "Reviewer filters." paragraph
  - the `Review Panel` config row and section
  - the four adapter "Review panel (ADR-028)" paragraphs
  - the `eval.sh` `review-panel` check

  These stay: `_prepare_run`, `PrepareError`, `parse_output`, `trial_key`, `_key_order`, and the trial subcommands.
- **Leftover config.** A `- **Review Panel:**` line in a project prints `review-panel: removed (ADR-032)` once per story and does nothing else. `/implement-story --panel` stops with `--panel was removed (ADR-032)`.
- **Safety Fact.** `FLOOR` becomes `tested`. The skill text and the script docstring are updated to match. The routing is unchanged.

## Detailed Requirements

### Story 1: ADR-032 and the review-surface inventory

`.writ/decision-records/adr-032-evidence-gated-review.md` records the decision: findings block only on executed evidence. Its inventory table has one row per adversarial-review surface: Gate 0 architecture check, Gate 0 divergence, evaluator-agent, review-agent, reviewer filters, Safety Fact, review panel, `/review`, Jev shadow, `/security-audit`, spec analysis, visual-qa-agent, and the discovery challenge prompts. Each row gives the fact the surface tries to establish, its cost (spawns, instruction bytes), and a verdict (keep, replace, demote, or remove) with a one-line reason. The reviewer filters row reads keep and cites the removal trial (`trial-report.md`, commit `ef0c418`).

ADR-028 gets an `Amended by: ADR-032` line covering the panel. The roadmap's Phase 15 Features list gains an unchecked line for this spec.

### Story 2: Evidence skill and the `evidence` subcommand

`skills/evidence-gated-findings/SKILL.md` holds the evidence grammar, the four kinds, and how to write a repro that fails for the right reason. It passes `bash scripts/lint-skill.sh` and is registered in `.writ/manifest.yaml`, the README Skills table, and root `SKILL.md`.

`review-override.py evidence` implements § Evidence outcomes, § Execution rules, and the `evidence-gate` switch. It uses the check shape. `config-format.md` gains the `Evidence Gate` row and section. Pytest on Python 3.9 covers each kind's fixture cases.

### Story 3: Gate 3 wiring

Gate 3 in `commands/implement-story.md` runs `evidence` on an agent FAIL and applies § Gate 3 decision. It also saves Gate 2's commands to `.writ/state/gate2-checks-<story-stem>.txt` and prints the `evidence-gate:` report line.

`agents/evaluator-agent.md` and `agents/review-agent.md` gain one `Read` line for the skill and one `**Evidence:**` field in their Issues Found format. Severity definitions say Critical and Major block only with evidence. Generated trees are rebuilt. A replay fixture runs § Gate 3 decision against a saved evaluator FAIL with and without a confirmed repro.

### Story 4: Repro as regression test

`evidence` writes the manifest on confirmation and accepts `--prior <manifest>`. The recode brief in Gate 3 names the repros and the no-edit rule. The re-review's recorded run includes every manifest path. Pytest covers removed, modified, still failing, and passing repros, with normalization on both sides.

### Story 5: `/review` evidence gating

`commands/review.md` Step 3 reads the skill. Technique 4 records evidence per Critical or High row under a `## Evidence` section keyed by FM ID. Step 4 runs `evidence --surface review --changed <diff files>`, applies § /review, and writes the header line. The Outcome interpretation table counts confirmed findings only. Pytest covers the report parser and the severity mapping.

### Story 6: Raise the Safety Fact floor to `tested`

The story makes the Safety Fact floor change listed in § Removals and updates the tests that assert the `traced` floor. Generated trees are rebuilt. It removes nothing and adds no scan test. The reviewer filters stay (Amendment).

### Story 7: Remove the review panel; close out the roadmap

The story makes every panel removal listed in § Removals, with the leftover-config and `--panel` messages. It removes the words "panel reviewers" from Gate 3's "Reviewer filters." paragraph in `commands/implement-story.md` and updates the `test_review_route_rigor.py` assertion that names them. It updates `test_review_panel.py`, `test_panel_trial_outcome.py` (the panel paragraph's absence now matches ADR-032, and the trial record stays guarded), `test_eval_shipped_refs.py`, `test_agent_cli_contract.py`, and the other tests that name the panel. It writes the shipped-file scan test, for the panel names only. It also deletes this repo's own `- **Review Panel:**` line from `.writ/config.md`, so Writ's self-runs do not print the leftover-config line.

It checks off this spec's roadmap line. It leaves Phase 15's "Reviewer prompts carry lead-judgment filters" criterion as written. It adds the `tested` floor to the Gate 2.5 criterion ("the evidence rung that fact reached, at or above `tested`"). It records ADR-032 in the roadmap's Phase 15 status.

## Implementation Approach

- **Script before prose.** Stories 2 and 4 write their pytest before the subcommand. Stories 3 and 5 write the wiring tests before editing the command files.
- **One script.** `evidence` lives in `scripts/review-override.py` beside `check`, `switch`, and `safety-fact`. It reuses `_inside`, `_cite_ok`, `_read_text`, `_emit`, and the `VERDICT_LINE` pattern. Finding parsing follows `review-panel.py` `_issue_entries` and `normalize_location`. Copy the patterns, not the import: Story 7 trims `review-panel.py`.
- **The skill owns the how.** Gate 3 and `/review` own when the step runs and what its result does. Agent bodies get one `Read` line and one output field.
- **Byte budget.** `commands/implement-story.md` is over its per-invocation budget. Across Stories 3, 4, and 7, and Story 6 if it touches the file, its net change must be zero or negative. Story 7's panel removals, including the "panel reviewers" trim, must free at least what the evidence wiring adds.
- **Regenerate, never hand-edit.** After any change to `agents/`, `commands/`, or `skills/`, run `python3 scripts/gen-platform-trees.py` and commit the trees in the same story.
- **Python 3.9 floor.** No `match`, no runtime `X | Y` unions, no 3.10+ `pathlib` or `str` methods. Use `from __future__ import annotations` as the other scripts do. `subprocess.run` with `timeout=` and `shell=False`. The `Test Runner` value is split with `shlex.split`.
- **Story order.** 1 → 2 → 3 → 4, with 5 after 2, then 6 after 4 and 5, then 7 after 6. Stories 3, 4, and 7 edit Gate 3 of `commands/implement-story.md`, so they run in sequence. Story 6 edits `scripts/review-override.py` and `scripts/tests/test_review_override.py` after Stories 4 and 5 have edited them.
