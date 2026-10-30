# Gate Upgrade Removal Measurement

> **Status:** In Progress
> **Created:** 2026-10-25
> **Owner:** @AdamSellke
> **Dependencies:** [2026-10-25-design-divergence, 2026-10-25-review-route-rigor, 2026-10-25-repro-first-bug-fixing]
> **Phase:** 15 — Code-Level Rigor ([roadmap](../../product/roadmap.md), [ADR-030](../../decision-records/adr-030-contract-verifier-boundary-front-door.md))
> **Origin:** Roadmap Phase 15 success criterion "Removal measurement" and ADR-030 § Consequences ("Each upgrade is kept only if a removal measurement on the Phase 11 baseline set shows it catching something the current gates passed"). Reuses the Phase 12 panel trial pattern ([`archive/2026-10-01-cross-family-review-panel`](../archive/2026-10-01-cross-family-review-panel/spec.md), [`trial-report.md`](../archive/2026-10-01-cross-family-review-panel/trial-report.md)). Authored with `/create-spec --recommend`; decisions in [`recommendation-log.md`](recommendation-log.md).

## Specification Contract

**Deliverable:** A retrospective trial that runs each Phase 15 gate upgrade with its switch on against the same gates with every switch off, over the four Phase 11 baseline stories, records the defects only the "on" arm raised, hands those findings to a human for a valid/invalid label, and then keeps each upgrade with at least one valid upgrade-only catch and removes the rest by their removal inventories.

**Must Include:**

1. A dev-only harness, `.writ/eval/gate-upgrade-trial/gate-upgrade-trial.py`, Python 3.9 stdlib, agent CLI check shape, with subcommands `init`, `prepare`, `record`, `sheet`, `label`, and `report`. It reuses `scripts/review-panel.py`'s read-only checkout builder and finding-key parser instead of copying them.
2. Four upgrades under test, each named by its switch: `Gate 0 Divergence`, `Safety Fact`, `Reviewer Filters`, `Repro First`. Each arm runs one upgrade on and the other three off. The "current gates" arm runs all four off, twice.
3. A per-story, per-upgrade exercise record. An upgrade counts as exercised on a story only when its own trigger fires there: the predicted review-agent route for Gate 0, the Gate 2.5 review-agent route for Safety Fact, every Gate 3 run for Reviewer Filters, and the skill's own bug recognition for Repro First.
4. A labeling sheet and `rating-handoff.md`. A human labels every upgrade-only finding `valid` or `invalid` against the story's acceptance criteria and acknowledges every upgrade the baseline never exercised. The lane never labels.
5. A human-gated verdict story that runs `report`, commits it verbatim as `trial-report.md`, carries out each upgrade's `keep` or `remove`, records the result in roadmap Phase 15 and ADR-030 § Review, and deletes the harness.
6. An outcome test, `scripts/tests/test_gate_upgrade_trial_outcome.py`, that does not import the harness and ties each upgrade's verdict to the repo state and this spec's status.

**Hardest Constraint:** The keep/remove verdict rests on human labels, and the baseline may not exercise every upgrade. The lane builds the harness, runs every arm, writes the sheet and the handoff, and stops. An upgrade the baseline never exercised is removed by the roadmap's literal rule unless the human explicitly asks for an amendment; it is never silently kept.

**🎯 Experience Design:**
- **Entry point:** `/implement-spec` on this spec after its three dependencies are complete. The maintainer re-enters once, to label.
- **Happy path:** Stories 1–3 run unattended and end at `rating-handoff.md`. The maintainer opens `labeling-sheet.md`, fills every label and acknowledgment, and runs one `label` command. Story 4 then runs `report` and acts on it.
- **Moment of truth:** `trial-report.md` prints one `upgrade:` line per upgrade with its verdict, how many stories exercised it, and its valid/invalid counts.
- **Feedback model:** every harness run ends with a `gate-upgrade-trial:` summary line; the spec status reads `In Progress — awaiting human labels (rating-handoff.md)` while the lane waits.
- **Error experience:** a missing arm, an unlabeled finding, or a missing acknowledgment makes that upgrade `unverifiable` with a named `reason:`. Story 4 leaves an unverifiable upgrade untouched and names it in the spec status.

**📋 Business Rules:**
- yuss is read-only. The harness only runs `git -C <yuss> rev-parse` and fetches from it into a fresh repo under `$TMPDIR`. Committed trial files hold story IDs, paths, SHAs, finding keys, severities, labels, and short notes, never yuss source, diff, story, or reviewer text.
- An upgrade-only finding is a finding key the upgrade's arm raised on a story that neither "current gates" run raised on that story.
- Verdict per upgrade: `keep` on one or more valid upgrade-only findings; `remove` when it was exercised and every upgrade-only finding is labeled with none valid; `remove` (reason `not_exercised`) when no story exercised it and the human acknowledged `remove`; `unverifiable` otherwise; `absent` when the upgrade was not in the repo at `init`.
- Only a human labels. `label` refuses an empty `--labeled-by` or one that names an agent or model.
- The trial record and `trial-report.md` are committed before any removal edit.

**Success Criteria:** `trial-report.md` is committed with the human-labeled trial file; for every upgrade, its verdict line matches the repo (wiring present for `keep`, `unverifiable`, and `absent`; absent per its removal inventory for `remove`); roadmap Phase 15's "Removal measurement" criterion links the report; ADR-030 § Review records the per-upgrade result; `uv run pytest`, `uv run --python 3.9 pytest`, the bash tests, `python3 scripts/gen-platform-trees.py --check`, and `bash scripts/eval.sh` pass with 0 findings; yuss HEAD, refs, and `git status --porcelain` are unchanged by the run.

**Scope Boundaries:**
- Included: the harness and its unit tests; trial inputs, prompts, the trial file, the labeling sheet, and the handoff; the outcome test; the verdict story's removal edits taken from each sibling spec's removal inventory; the roadmap Phase 15 "Removal measurement" line; the ADR-030 § Review note.
- Excluded: always-on multi-model panels; cross-vendor routing (ADR-024); formal verification; measuring `/why` or `/retro`; replaying full `/implement-story` runs; a substitute baseline; the design-divergence blind trial (owned by `2026-10-25-design-divergence`).
- Never touched, verdict story included: `commands/why.md`, `commands/writ.md`, `commands/retro.md`, `commands/refresh-command.md`.

**⚠️ Technical Concerns:**
- **Retrospective, not replay.** A full `/implement-story` replay cost about $26 and 56 minutes per run in the Phase 11 baseline; four upgrades, two arms, and four stories would be 32 runs, and one run per arm cannot separate an upgrade's effect from run-to-run variance. The trial instead re-reviews each story's historical diff, as Phase 12 did. Gate 0 and Repro First act before code exists, so their arms measure a proxy: a comparison reviewer names defects in the shipped diff that the chosen Gate 0 sketch avoids (each must cite the sketch line), and a repro written at the parent commit is re-run at the story commit.
- **Exercise at authoring time** (probe of the four story commits in scratch clones; yuss unchanged): Safety Fact 4 of 4 (Gate 2.5 routes all four to `review-agent`); Reviewer Filters 4 of 4; Gate 0 3 of 4 (the planned files of `2026-07-23-quick-split-single-transaction/story-3-settlement-view-share-link` classify `cross-component` and route `evaluator-agent`); Repro First 0 or 1 of 4 (three stories come from `.writ/issues/features/` issues; `story-4-messaging-migration-quick-split-guard` corrects stale limit messaging and may or may not meet the skill's bug test).
- **Reviewer Filters can only add a catch through filter 3.** Filters 1 and 2 drop findings, which the criterion does not count. The report prints off-only drops per upgrade for information; they never decide a verdict.
- **Run-to-run noise.** Two "current gates" runs per story narrow it; a finding counts as upgrade-only only when both missed it. Four stories and one on-run per arm is still a small sample, and the report says so.
- **Finding keys are coarse.** Keys are `ac:AC-N.M` and `<category>:<path>` (Critical or Major, security or architecture), as in Phase 12. Two different defects in one file share a key, which biases toward removal.
- **Raw outputs hold yuss text.** They go to the primary checkout's gitignored `.writ/state/gate-upgrade-trial/`, resolved through `git rev-parse --git-common-dir`, so they survive a lane worktree and are never committed.
- **The harness is dev-only.** It lives under `.writ/eval/`, so `is_shippable_script` never ships it and it needs no Classification row. It loads `scripts/review-panel.py` by path; if that script is gone, `prepare` and `record` exit 2.

**💡 Recommendations:**
- Use each upgrade's own trigger to decide exercise. A judgment about whether an upgrade "should" have fired is not evidence.
- Keep Story 4 to the edits each sibling's removal inventory already lists; do not invent removal steps.
- If a verdict depends on a stricter or looser key, amend the spec before labeling, not after.

**⚠️ Cross-Spec Overlap (advisory):**
- Every pre-Phase-15 spec is complete-family (`spec-status.py is-complete`). Five Phase 15 siblings are `Not Started`.
- `2026-10-25-design-divergence`, `2026-10-25-review-route-rigor`, and `2026-10-25-repro-first-bug-fixing` are hard dependencies: their switches must exist before Story 3 runs. Story 4 edits files they create, only by their removal inventories.
- `2026-10-25-design-divergence` Story 6 also edits ADR-030 § Review and roadmap Phase 15 and runs its own blind trial on the skill. Both specs use targeted edits; see Business Rule 12 for the combined outcome.
- `2026-10-25-why-command` and `2026-10-25-retro-fix-ladder` share no files with this spec.
- Shared hot spots in Story 4: the `"commands/implement-story.md"` ratchet in `scripts/tests/test_governor_enforcement.py`, `.writ/manifest.yaml`, the README Skills table, `.writ/docs/config-format.md`, and generated trees. Re-pin from the value present at execution time and regenerate, never hand-merge.

## Experience Design

### Who uses it

- **The `/implement-spec` lane.** It builds the harness, runs every arm, writes the sheet and handoff, and stops.
- **The maintainer as labeler,** once. They read each finding excerpt against the story's acceptance criteria at that commit and label it.
- **The `/implement-spec` lane again,** after the labels exist, to run Story 4.

### Journey

1. `init` reads the baseline's four-story `selection`, probes which of the four upgrades are present, and writes the trial file.
2. Per story, `prepare` builds a read-only checkout at the story commit, a worktree at its parent, the diff, story, and contract, both routes, the blast radius, and one config file per arm.
3. The lane spawns each arm with identical inputs and records it. `record` refuses an arm whose switch evidence does not match the arm.
4. `sheet` writes `labeling-sheet.md` with shuffled opaque finding IDs and one excerpt file per finding under `.writ/state/gate-upgrade-trial/findings/`.
5. The lane writes `rating-handoff.md`, confirms `report` prints `unverifiable` with `reason: unlabeled`, sets the spec status, and stops.
6. The maintainer fills the sheet and runs `label --sheet … --labeled-by "<name>"`.
7. Story 4 runs `report`, commits it, and acts per upgrade.

### State Catalog

| State | Trigger | Report line |
|---|---|---|
| Unlabeled | upgrade-only findings with no label | `upgrade: <name> verdict=unverifiable … reason=unlabeled` |
| Missing arm | an applicable story lacks the on arm or either off arm | `… verdict=unverifiable reason=missing_arm <story> <arm>` |
| Not exercised, unacknowledged | no story exercised it; sheet ack blank | `… verdict=unverifiable reason=not_exercised_unacknowledged` |
| Not exercised, remove | ack `remove` | `… verdict=remove reason=not_exercised` |
| Not exercised, amend | ack `amend` | `… verdict=unverifiable reason=amendment_requested` |
| Keep | one or more valid upgrade-only findings | `… verdict=keep exercised=3/4 upgrade_only=2 valid=1 invalid=1` |
| Remove | exercised; all labeled; none valid | `… verdict=remove exercised=4/4 upgrade_only=1 valid=0 invalid=1` |
| Absent | upgrade not in the repo at `init` | `… verdict=absent` |

### Interaction Patterns

- Every harness run ends with `gate-upgrade-trial: …`.
- The sheet shows opaque IDs (`F01`, `F02`, …), the story, the key, the severity, and the excerpt path. The upgrade name is in the trial file, not the sheet.

## Business Rules (Expanded)

1. **Baseline.** The story set is the `selection` of `.writ/eval/baselines/2026-09-07-claude-fable-5-1.json`: the four stories the Phase 12 panel trial used. No substitute baseline. A human who wants one asks for an amendment on the sheet; this spec does not define it.
2. **yuss isolation.** As in Phase 12 Story 4: read-only `rev-parse` before any write, then `git init` and `git fetch --depth 2` under `$TMPDIR`. The run snapshots yuss HEAD, refs, and `git status --porcelain` before and after and records equality.
3. **Arms.** All arms on a story get the same prepared diff, story, contract, the same model in one session, and the story's historical test results labeled "historical, not re-run". Each upgrade arm sets its own switch on and the other three off. Both "current gates" arms set all four off.
4. **Exercise.** Gate 0 Divergence runs on a story only when the predicted route over its planned files is `review-agent` (the design-divergence route predictor) and its report line reads `gate0-divergence: chose …`. Safety Fact runs only when Gate 2.5's `gate3_route` over the story's changed files is `review-agent`. Reviewer Filters runs on every story. Repro First runs its full arm only when the coding agent, reading `skills/tdd-cycle/SKILL.md` with the switch on, reports `Kind:` as a bug fix.
5. **Upgrade-only findings.** Keys come from `scripts/review-panel.py`'s parser. For the Gate 0 arm, only comparison issues that carry an `**Avoided by:**` line count. For the Repro First arm, a repro that fails at the parent commit for the bug's reason and still fails at the story commit yields the key `ac:<the AC it targets>` at Critical. A key is upgrade-only when neither "current gates" run raised it on that story.
6. **Labels.** `valid` only when the finding names a real unmet acceptance criterion, or a real Critical or Major security or architecture defect, in the story commit, judged against the story's acceptance criteria at that commit. For a Gate 0 finding, the cited sketch line must also avoid it. Notes are one line, at most 200 characters, with no code block and no quoted source.
7. **Acknowledgments.** Each upgrade no story exercised gets one sheet field, `ack: remove|amend`. `remove` applies the roadmap rule. `amend` holds the upgrade unchanged and leaves this spec open until `/edit-spec` adds an accepted substitute baseline.
8. **Verdict.** Per upgrade, as the State Catalog. The overall check line is `pass` when every upgrade is `keep`, `remove`, or `absent`, and `unverifiable` otherwise.
9. **Human gate.** The lane never fills the sheet and never runs `label`. Story 4 stops at its first task while `labeled_by` is null and reports that it waits on human input. It is never marked complete or skipped.
10. **Commit order.** The labeled trial file and `trial-report.md` are committed first. Removal edits follow. The harness and its unit tests are deleted last.
11. **Removal.** A `remove` verdict deletes exactly what the upgrade's sibling spec lists, plus that upgrade's own tests and wiring-test pins, then regenerates trees and re-pins the `implement-story.md` ratchet downward with a dated disclosure.
12. **Gate 0 and the blind trial.** If this spec removes the Gate 0 upgrade and the design-divergence blind trial says `keep`, the skill stays with `/prototype` Step 2.5 as its only caller; the roadmap's "two live callers" wording is no longer met, and the ADR-030 note says why. If the blind trial says `remove`, its Story 6 deletes the skill and the Gate 0 wiring together, whatever this trial says. Whichever runs second records "already removed" instead of editing.
13. **Spec status.** `Complete` when every upgrade is `keep`, `remove`, or `absent` and the repo matches. Otherwise `In Progress — <reason from report>`.

## Detailed Requirements

### Story 1: Harness — `init` and `prepare`

`init` reads the baseline selection, probes upgrade presence, and writes the `gate-upgrade-trial-v1` skeleton. `prepare` builds the read-only checkout through `review-panel.py`'s `_prepare_run`, adds a parent worktree, computes both routes and the blast radius, and writes one config file per arm. Unit tests use a stand-in git repo.

### Story 2: Harness — `record`, `sheet`, `label`, `report`

`record` stores keys and switch evidence per arm and recomputes upgrade-only findings. `sheet` writes the shuffled sheet and excerpt files. `label` imports a filled sheet. `report` applies Business Rule 8.

### Story 3: Run the arms and hand off for labeling

Write the outcome test first. Check the dependencies are complete and snapshot yuss. Run `init`, `prepare`, every arm, and `sheet`. Write `rating-handoff.md` and set the spec status.

### Story 4: Act on the labeled trial (human-gated)

Confirm the human labels. Commit the report and trial file. Remove each `remove` upgrade by its inventory. Record the result in roadmap and ADR-030. Delete the harness and its unit tests.

## Implementation Approach

- **Copy Phase 12, widen the arms.** Same schema-tagged trial file, read-only checkout, key grammar, label rules, and caveat line. The new parts are per-upgrade arms, two "current gates" runs, exercise tracking, and acknowledgments.
- **Reuse by path.** The harness imports `scripts/review-panel.py` with `importlib.util.spec_from_file_location` for `_prepare_run`, `parse_output`, `trial_key`, and `_key_order`. It runs `change-surface.py` and `boundary-map.py` as subprocesses, as Gate 0 and Gate 2.5 do.
- **Arm evidence comes from the upgrades' own outputs:** `review-override.py switch` line 1 for Safety Fact and Reviewer Filters, the presence of `### Safety Fact` and the `review-override.py safety-fact` verdict, the `gate0-divergence:` report line, and the coding agent's `### Repro` `Kind:` line.
- **Removal is a checklist, not a design.** Story 4 lists each sibling's inventory; see [`sub-specs/technical-spec.md`](sub-specs/technical-spec.md) § Verdict Execution.
- See [`sub-specs/technical-spec.md`](sub-specs/technical-spec.md) for the CLI, schema, arm procedures, error map, and files in scope.
