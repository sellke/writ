# Story 4: Act on the Labeled Trial (Human-Gated)

> **Status:** Not Started
> **Priority:** Medium
> **Dependencies:** Story 3

## User Story

**As a** Writ maintainer
**I want to** run `report` on the human-labeled trial, commit its output with the trial file, and then keep or remove each Phase 15 gate upgrade as its verdict decides
**So that** each upgrade stays only if it caught something the current gates passed, and the repo state, roadmap Phase 15, ADR-030, and the spec status all agree with a committed record

## Acceptance Criteria

> **AC IDs assigned through:** AC-4.5

- [ ] Given a `labeling-sheet.md` the human filled and recorded with `label --labeled-by <their name>`, when `python3 .writ/eval/gate-upgrade-trial/gate-upgrade-trial.py report --trial <file>` runs, then the trial file's `labeled_by` names a person and no upgrade-only finding has `label: null`, and the report output is committed verbatim as `.writ/specs/2026-10-25-gate-upgrade-removal-measurement/trial-report.md` together with the labeled trial file in a commit that precedes any removal edit; while `labeled_by` is null the story stops and reports that it waits on human input `[AC-4.1]`
- [ ] Given an upgrade with verdict `remove` (including `reason: not_exercised` with ack `remove`), when the story closes, then exactly that upgrade's removal inventory from technical-spec.md § Verdict Execution is applied, `bash scripts/gen-skill.sh` has run if a skill was removed, `python3 scripts/gen-platform-trees.py` has run, the `"commands/implement-story.md"` ratchet in `scripts/tests/test_governor_enforcement.py` is re-pinned downward with a dated disclosure naming this spec and Story 4, and the upgrade's literals return no wiring hits: `rg -n 'Gate 0 Divergence|Design divergence \(boundary-crossing route\)' commands .writ/docs` for gate0-divergence; `skills/blast-radius/` absent and `rg -n 'Safety Fact' commands agents .writ/docs` empty for safety-fact; `skills/review-judgment-filters/` absent and `rg -n 'Reviewer Filters|reviewer_filters' commands agents .writ/docs` empty for reviewer-filters; `scripts/repro-order.py` absent and `rg -n 'Repro First' commands agents skills .writ/docs` empty for repro-first `[AC-4.2]`
- [ ] Given an upgrade with verdict `keep`, `unverifiable`, or `absent`, when the story closes, then its presence probe matches its state at `init` and none of its files are edited; and for Gate 0, if this story removes the wiring while the design-divergence blind trial says `keep`, `skills/design-divergence/` stays with `/prototype` Step 2.5 as its only caller and its `status_evidence` names `/prototype`, while if the wiring is already gone the story records "already removed by design-divergence Story 6" and edits nothing for Gate 0 `[AC-4.3]`
- [ ] Given the committed report, when the records are written, then roadmap Phase 15's "Removal measurement" line alone gains the date, a link to trial-report.md, and `kept` or `removed` per upgrade; ADR-030 § Review gains a note with the date, the four story IDs, each upgrade's verdict and valid count, the not-exercised reasons, the proxy and small-sample caveats, and the Gate 0 / blind-trial outcome; and spec.md reads `> **Status:** Complete` when every verdict is `keep`, `remove`, or `absent`, else `> **Status:** In Progress — <reason from report>` `[AC-4.4]`
- [ ] Given the report commit exists, when the story closes, then `.writ/eval/gate-upgrade-trial/gate-upgrade-trial.py`, `scripts/tests/test_gate_upgrade_trial.py`, and `scripts/tests/fixtures/gate-upgrade-trial/` are deleted, `uv run pytest scripts/tests/test_gate_upgrade_trial_outcome.py` passes, `commands/why.md`, `commands/writ.md`, `commands/retro.md`, and `commands/refresh-command.md` are unchanged, and `uv run pytest`, `uv run --python 3.9 pytest`, the bash tests, `python3 scripts/gen-platform-trees.py --check`, and `bash scripts/eval.sh` all pass with 0 findings `[AC-4.5]`

## Implementation Tasks

- [ ] 4.1 Confirm the human gate: `labeling-sheet.md` is filled, and the trial file has `labeled_by` set to a person's name and no `label: null` among upgrade-only findings. If not, stop and report that the story is waiting on human input `[AC-4.1]`
- [ ] 4.2 Run `report`, write its output verbatim to `trial-report.md`, and commit it with the labeled trial file before touching any wiring `[AC-4.1]`
- [ ] 4.3 For each `remove` verdict, apply exactly its removal inventory (gate0-divergence list; review-route-rigor technical-spec.md § Clean Removal steps for safety-fact and reviewer-filters, deleting `review-override.py switch` and `scripts/tests/test_review_route_rigor.py` when both go; repro-first spec.md § Removal Inventory). When two removals edit `commands/implement-story.md`, apply them in one pass. Then run `bash scripts/gen-skill.sh` if a skill was removed, `python3 scripts/gen-platform-trees.py`, re-pin the ratchet once with a dated disclosure, and run the AC-4.2 `rg` checks `[AC-4.2]`
- [ ] 4.4 Leave every `keep`, `unverifiable`, and `absent` upgrade untouched. For Gate 0, check `.writ/specs/2026-10-25-design-divergence/trial-report.md`: if the wiring is already gone, record "already removed" and edit nothing; if this story removes it and the blind trial said `keep`, keep the skill with `/prototype` as its only caller `[AC-4.3]`
- [ ] 4.5 Append to the roadmap Phase 15 "Removal measurement" line, add the ADR-030 § Review note, and set the spec.md status. Use targeted edits only `[AC-4.4]`
- [ ] 4.6 Delete `.writ/eval/gate-upgrade-trial/gate-upgrade-trial.py`, `scripts/tests/test_gate_upgrade_trial.py`, and `scripts/tests/fixtures/gate-upgrade-trial/`, then confirm `scripts/tests/test_gate_upgrade_trial_outcome.py` passes `[AC-4.5]`
- [ ] 4.7 Verify all tests pass: `uv run pytest`, `uv run --python 3.9 pytest`, the bash tests, `python3 scripts/gen-platform-trees.py --check`, and `bash scripts/eval.sh` (outside the sandbox) with 0 findings; re-run the AC-4.2 `rg` checks for every removed upgrade `[AC-4.2, AC-4.3, AC-4.5]`

## Notes

- **Human-gated.** The implementing agent never fills `labeling-sheet.md` and never runs `label`. If `/implement-spec` reaches this story before the labels exist, it must stop at task 4.1 and report. It must not mark the story complete or blocked-and-skipped.
- **Commit order is load-bearing.** (1) labeled trial file + `trial-report.md`; (2) removal edits; (3) roadmap, ADR-030, spec status; (4) harness deletion. The harness is deleted only after the report commit exists.
- **Removal is a checklist.** Apply only what each sibling's removal inventory lists, plus that upgrade's own tests and wiring-test pins. Do not invent removal steps.
- **`unverifiable` is not a removal.** An `unverifiable` upgrade stays as it is; the spec status names its `reason:` and the spec stays open. An `amend` ack holds the upgrade until `/edit-spec` adds a substitute baseline.
- **Gate 0 and the blind trial.** `2026-10-25-design-divergence` Story 6 may run before or after this story. Whichever runs second records "already removed" instead of editing. If this story removes Gate 0 and the blind trial keeps the skill, the roadmap's "two live callers" wording is no longer met; the ADR-030 note says why.
- **Shared files.** `.writ/product/roadmap.md`, ADR-030, `.writ/manifest.yaml`, the README Skills table, `.writ/docs/config-format.md`, and generated trees are also edited by sibling Phase 15 specs. Use targeted edits. Re-pin the ratchet from the value present at execution time and regenerate trees; never hand-merge.
- **Outcome test independence.** `scripts/tests/test_gate_upgrade_trial_outcome.py` does not import the harness, so it survives task 4.6.
- **Small sample and proxies.** Four stories, one run per upgrade arm, and retrospective proxies for Gate 0 and Repro First. One valid catch keeps an upgrade. The report and the ADR note carry these caveats; a `keep` must not be cited later as proof of a general result.
- **Never touched:** `commands/why.md`, `commands/writ.md`, `commands/retro.md`, `commands/refresh-command.md`, and anything under yuss.

## Definition of Done

- [ ] All tasks completed
- [ ] All acceptance criteria met
- [ ] Tests passing
- [ ] Code reviewed
- [ ] Documentation updated

## Context for Agents

- **Error map rows:** [Story 4 (report `unverifiable` for an upgrade → that upgrade untouched; spec status names the reason), `report` (unlabeled, missing arm, missing ack → `unverifiable`)] — from technical-spec.md → Error & Rescue Map
- **Shadow paths:** [Story 4 (`labeled_by` null → stop at task 4.1; every verdict `keep` → records only; a removal leaves `rg` hits → story fails its own verification)] — from technical-spec.md → Shadow Paths
- **Business rules:** [Human gate (rule 9), Commit order (rule 10), Removal (rule 11), Gate 0 and the blind trial (rule 12), Spec status (rule 13)] — from spec.md → Business Rules (Expanded)
- **Experience:** [Error experience (an `unverifiable` upgrade is left untouched and named in the spec status)] — from spec.md → 🎯 Experience Design
- **Technical:** technical-spec.md → ## Verdict Execution (Story 4) (commit order, Removal inventories, Repo state the outcome test asserts, Records); technical-spec.md → ## Interaction Edge Cases (Gate 0 / blind-trial rows, both review-route upgrades removed, two removals editing implement-story.md); technical-spec.md → ## Files in Scope (Story 4 rows)
