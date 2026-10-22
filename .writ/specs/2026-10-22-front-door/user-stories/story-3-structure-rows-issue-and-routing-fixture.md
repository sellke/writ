# Story 3: Structure Rows, Issue Resolution, and Routing Fixture

> **Status:** Not Started
> **Priority:** High
> **Dependencies:** Story 1, Story 2

## User Story

**As a** maintainer **I want to** pin the `/writ` rule table and its `entry_level` in the command-structure checker, close the in-your-own-words issue, and record the routing fixture against the rule table **So that** I have evidence the rule table routes real requests as the roadmap intends, and I can review at phase close whether work starts from `/writ`.

## Acceptance Criteria

> **AC IDs assigned through:** AC-3.5

- [ ] Given `scripts/eval-command-structure.py` `ROWS` has a `heading` row for `## Routing Rules` and a `frontmatter` row for `entry_level`, both against `commands/writ.md`, when `python3 scripts/eval-command-structure.py --root .` runs, then both rows report `PASS` and the helper's `self_test()` still passes. `[AC-3.1]`
- [ ] Given `.writ/issues/features/2026-10-13-in-your-own-words.md`, when this story is complete, then its last H2 is `## Resolution`, which names this spec, `/writ` Step 1 Restate as the absorbed restatement (it does not end the turn because it routes), and the date 2026-10-22, and its `spec_ref` line is `.writ/specs/2026-10-22-front-door/`. `[AC-3.2]`
- [ ] Given the eight requests in `technical-spec.md → ## Routing Fixture`, when Steps 1–3 of `commands/writ.md` are applied to each, stopping before the AskQuestion, then this story's What Was Built gives each request's restatement and proposed route beside its expected route. `[AC-3.3]`
- [ ] Given a fixture request whose proposed route differs from its expected route, when the mismatch is resolved, then `commands/writ.md → ## Routing Rules` is corrected, `drift-log.md` records the reason under Spec said / Implementation did / Reason / Resolution, and the fixture table is unchanged. `[AC-3.4]`
- [ ] Given the changes from this story, when `uv run --python 3.9 pytest`, the bash test loop, and `bash scripts/eval.sh` run outside any sandbox, then the pytest run and bash loop show no failures and `eval.sh` reports 0 findings. `[AC-3.5]`

## Implementation Tasks

- [ ] 3.1 Write the failing tests first. In `scripts/tests/test_front_door.py` (issue section), add a test that the in-your-own-words issue's last H2 is `## Resolution` and its `spec_ref` is `.writ/specs/2026-10-22-front-door/`. Run it and confirm it fails. Confirm the structure output has no PASS for the two new rows yet. `[AC-3.1, AC-3.2]`
- [ ] 3.2 Add the `heading` row (`## Routing Rules`) and the `frontmatter` row (`entry_level`) for `commands/writ.md` to `ROWS` in `scripts/eval-command-structure.py`. Match the heading text exactly. Run `python3 scripts/eval-command-structure.py --root .` and confirm both rows PASS and `self_test()` still passes. `[AC-3.1]`
- [ ] 3.3 Append `## Resolution` to `.writ/issues/features/2026-10-13-in-your-own-words.md`. Name this spec, the `/writ` command (Step 1 Restate is the absorbed restatement; it does not end the turn because it routes), and 2026-10-22. Set `spec_ref` to `.writ/specs/2026-10-22-front-door/`. Confirm the task 3.1 test passes. `[AC-3.2]`
- [ ] 3.4 Apply `commands/writ.md` Steps 1–3 to each of the eight requests in `technical-spec.md → ## Routing Fixture`, stopping before the AskQuestion. Record each restatement and proposed route beside its expected route in this story's What Was Built. `[AC-3.3]`
- [ ] 3.5 For each mismatch between a proposed route and its expected route, correct `commands/writ.md → ## Routing Rules`, record the reason in `drift-log.md` (create it if absent), and re-apply Steps 1–3 to the affected request. Do not edit the fixture table. If no mismatch occurs, record that in What Was Built. `[AC-3.4]`
- [ ] 3.6 Run `uv run --python 3.9 pytest` and the bash test loop. Confirm no failures and no `FAIL` lines. `[AC-3.5]`
- [ ] 3.7 Run `bash scripts/eval.sh` outside any sandbox. Confirm 0 findings and record the summary line in What Was Built. `[AC-3.5]`

## Notes

**Technical considerations**

- `scripts/eval-command-structure.py`: `KINDS = ("heading", "frontmatter", "invocation")`. `ROWS` is a tuple of (command file, kind, value) rows. Read the module docstring and an existing row before adding one.
- `has_heading` ignores fenced code. The `## Routing Rules` heading must sit outside a code fence in `commands/writ.md`.
- `self_test()` runs one case per kind. The helper prints TSV (`PASS|FAIL\t<name>\t<reason>`) that `check_command_structure` in `scripts/eval.sh` consumes.
- The fixture is applied by the implementing agent reading `commands/writ.md` and reasoning. No script runs it. The recorded table is the evidence.
- Issue pinning: `test_issue_closure_wiring.py` and `test_platform_neutral_names.py::test_issue_resolution` pin other resolutions. This issue has no pin yet, so the test goes in `scripts/tests/test_front_door.py`. Model the resolution on `.writ/issues/bugs/2026-10-19-prototype-visual-preview-cursor-only.md`.
- Drift log labels: "Spec said / Implementation did / Reason / Resolution", as in `.writ/specs/2026-10-20-ci-and-update-integrity/drift-log.md`.
- Python 3.9 standard library only.

**Risks**

- A mismatch tempts a fixture edit. The fix goes in the rule table. The fixture table stays as written.
- The structure row value must match the heading text exactly. A mismatch fails `check_command_structure`.

**Integration**

- Stories 1 and 2 must be complete. Story 1 creates `scripts/tests/test_front_door.py` with the command section. Story 2 adds the registration section. This story adds the issue section.
- This story closes the spec. The recorded fixture run and a 0-finding `eval.sh` are the phase-close evidence.

## Definition of Done

- [ ] All tasks completed
- [ ] All acceptance criteria met
- [ ] Tests passing
- [ ] Code reviewed
- [ ] Documentation updated

## Context for Agents

- **Error map rows:** []
- **Shadow paths:** `technical-spec.md → ## Shadow Paths` (Happy path)
- **Business rules:** `spec.md → ## Business Rules (Expanded)` (1 Rule table is the classifier; 2 Tie-break; 3 Restatement shape)
- **Experience:** `spec.md → ## Experience Design → ### State Catalog` (Request names a roadmap phase or feature; Request is a why or how question; Request is a fork; Request lacks a done check or proof)
