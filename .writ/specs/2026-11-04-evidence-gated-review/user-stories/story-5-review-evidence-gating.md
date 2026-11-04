# Story 5: Evidence gating in `/review`

> **Status:** Not Started
> **Priority:** Medium
> **Dependencies:** Story 2

## User Story

**As a** developer running `/review`
**I want to** have Critical and High findings count toward the ship recommendation only when executed evidence backs them
**So that** a "do not ship" verdict rests on a failing test or a cited input-to-sink path

## Acceptance Criteria

> **AC IDs assigned through:** AC-5.5

- [ ] Given a `/review` report whose Critical or High registry row has no `#### FM-NNN` evidence block, or whose block is not confirmed, when `review-override.py evidence --surface review` runs, then the row's mapped severity is `Medium (unconfirmed)`, and the row keeps its ID and description. `[AC-5.1]`
- [ ] Given a Critical or High row of any category (error handling, shadow path, interaction, security, architecture) whose `test` evidence block fails in the scoped run, when the Recommendation is written, then a confirmed Critical gives "Do not ship", a confirmed High with no confirmed Critical gives "Ship with caution", and a report with neither gives "ready to ship" and lists the unconfirmed findings under the Recommendation as worth a look. `[AC-5.2]`
- [ ] Given a `/review` report whose evidence blocks are `recorded` or `check`, when `evidence --surface review` runs, then each such row reads `unverifiable kind_unavailable` and maps to `Medium (unconfirmed)`, and only `test` and `security-path` blocks can confirm. `[AC-5.3]`
- [ ] Given a `/review` run, when Step 4 writes the report header, then the header has a `> Evidence gate: on|off|unverifiable (<reason>)` line beside the `> Reviewer filters: on|off` line, and with `Evidence Gate: off` in `.writ/config.md` it reads `> Evidence gate: off` and no row is downgraded. `[AC-5.4]`
- [ ] Given the updated `commands/review.md`, when Step 3 and the Completion section are read, then Step 3 reads `skills/evidence-gated-findings/SKILL.md` after the filters `Read`, the filters `Read` and the `reviewer-filters` switch line stay, and the Outcome interpretation table counts confirmed findings only. `[AC-5.5]`

## Implementation Tasks

- [ ] 5.1 Write `ReviewSurfaceParseTests` in `scripts/tests/test_review_override.py` first. Cover: the Severity column of each registry row is read; a `#### FM-NNN` block binds to its row by ID; a row with no block reports `no_evidence`; only Critical and High rows are run; an empty `--changed` maps every row to `location_outside_change_set`. Confirm they fail on the current tree. `[AC-5.1]`
- [ ] 5.2 Write `ReviewSurfaceMappingTests` in the same file. Cover: a confirmed `test` row keeps its severity, including a row with Category `Error handling`; no row reports `no_claim` on this surface; `recorded` and `check` blocks report `kind_unavailable`; switch `off` prints `evidence-gate: off` and runs no repro. Confirm they fail on the current tree. `[AC-5.2, AC-5.3, AC-5.4]`
- [ ] 5.3 Add `ReviewWiringTests` to `scripts/tests/test_evidence_gate_wiring.py`. Assert on `commands/review.md`: Step 3 reads the evidence skill after the filters Read; the filters Read and the `reviewer-filters` switch line are present; the header template has both a `> Evidence gate:` line and a `> Reviewer filters:` line; the Recommendation and the Outcome table follow confirmed findings. Confirm they fail on the current tree. `[AC-5.2, AC-5.4, AC-5.5]`
- [ ] 5.4 Implement registry-table and `#### FM-NNN` parsing for `--surface review` in `scripts/review-override.py`, so the 5.1 tests pass. Follow the pattern of `review-panel.py` `_issue_entries`. Do not import it. Reuse `_inside`, `_cite_ok`, `_read_text`, and `_emit`. Stdlib only, Python 3.9 floor. `[AC-5.1]`
- [ ] 5.5 Add kind rules, the per-row mapped severity, and the switch-off path to `--surface review`, so the 5.2 tests pass. Each per-row line prints its mapped severity. Line 1 is `fail` when any row confirms, otherwise `pass`. Skip the verdict check on this surface. A run-level unverifiable result leaves every severity unchanged. `[AC-5.2, AC-5.3, AC-5.4]`
- [ ] 5.6 Edit `commands/review.md` so the 5.3 wiring tests pass. (a) Step 3 reads `skills/evidence-gated-findings/SKILL.md` after the filters Read. Keep the switch line, the filters Read, and the sentence that feeds the Step 4 filters header. (b) Technique 4 records one `#### FM-NNN` block per Critical or High row under `## Evidence`. (c) Step 4 writes the draft report, runs `evidence --surface review`, applies the mapping, then writes the header and the Recommendation. (d) The report template gains the `## Evidence` section after the Failure Modes Registry, and the evidence header line beside the reviewer-filters line. (e) The Recommendation and the Completion Outcome table count confirmed findings only. The Summary line counts mapped severities. Downgraded rows stay in the registry in full. Then run `python3 scripts/gen-platform-trees.py` and include the regenerated `cursor/plugin/commands/review.md` in the same change. `[AC-5.2, AC-5.4, AC-5.5]`
- [ ] 5.7 Verify, one run at a time. Run the full `pytest` suite on Python 3.9, then on 3.14 (`uv run --isolated --python <version> --with pytest pytest`). Run `python3 scripts/gen-platform-trees.py --check`. Run `bash scripts/eval.sh`. Never run pytest alongside `eval.sh`. Confirm each criterion has a passing test or wiring assertion. `[AC-5.1, AC-5.2, AC-5.3, AC-5.4, AC-5.5]`

## Notes

- **Dependency.** Story 2 supplies `evidence`, the `evidence-gate` switch, and the `test` and `security-path` kinds. Story 2 accepts `--surface review` as a no-op. This story gives the flag behavior.
- **Shared test file.** Story 3 creates `scripts/tests/test_evidence_gate_wiring.py`. Run this story after Story 3 to avoid edit collisions. If Story 3 has not landed, create the file with this story's class only.
- **Filters stay.** The `reviewer-filters` switch line, the filters Read, and the `> Reviewer filters:` header line stay (spec.md → Amendment). The evidence lines go beside them.
- **Resolved (2026-11-04): claim test on `/review`.** On `--surface review`, any category can confirm, and the confirmed evidence is the claim. The Location-in-diff rule still applies (`spec.md` → `### /review`).
- **Resolved (2026-11-04): unverifiable on `/review`.** A per-row unverifiable is downgraded the same way an advisory row is. A run-level unverifiable leaves every severity as written, and the header shows the reason (`spec.md` → `### /review`).
- **Assumption: no verdict on `/review`.** `/review` writes no FAIL verdict, so the `pass` and `verdict_not_fail` rules do not apply on `--surface review`.
- **Assumption: Major means High.** The `security-path` kind requires Major or above. `/review` has no Major rows, so High counts.
- **Parser limit, resolved.** `scripts/story-context.py` matches headings exactly. The spec headings are now `### /review` and `### /review form`, with no backticks, so the hints resolve.
- **Summary line.** The Step 4 summary counts mapped severities, so downgraded rows count under medium.

## Definition of Done

- [ ] All tasks completed
- [ ] All acceptance criteria met
- [ ] Tests passing
- [ ] Code reviewed
- [ ] Documentation updated

## Context for Agents

- **Error map rows:** [`/review`, Parse issues, Read the review output] — technical-spec.md → ## Error & Rescue Map (row for /review: No diff files)
- **Shadow paths:** [Happy, Nil, Upstream error] — technical-spec.md → ## Shadow Paths
- **Business rules:** `spec.md → ## Business Rules (Expanded) → ### Which findings are evaluated`, `spec.md → ## Business Rules (Expanded) → ### Evidence outcomes`, `spec.md → ## Business Rules (Expanded) → ### Switch`, `technical-spec.md → ## Evidence Block Grammar`, `spec.md → ## Business Rules (Expanded) → ### /review`
- **Experience:** `spec.md → ## Experience Design → ### Who uses it`, `spec.md → ## Experience Design → ### Interaction patterns`
