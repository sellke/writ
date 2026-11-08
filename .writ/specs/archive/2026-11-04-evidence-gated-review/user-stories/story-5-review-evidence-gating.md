# Story 5: Evidence gating in `/review`

> **Status:** Completed ✅ (2026-11-04)
> **Commit:** 70163485a9d67a42e171570b9b6754dd05b577f4
> **Priority:** Medium
> **Dependencies:** Story 2

## User Story

**As a** developer running `/review`
**I want to** have Critical and High findings count toward the ship recommendation only when executed evidence backs them
**So that** a "do not ship" verdict rests on a failing test or a cited input-to-sink path

## Acceptance Criteria

> **AC IDs assigned through:** AC-5.5

- [x] Given a `/review` report whose Critical or High registry row has no `#### FM-NNN` evidence block, or whose block is not confirmed, when `review-override.py evidence --surface review` runs, then the row's mapped severity is `Medium (unconfirmed)`, and the row keeps its ID and description. `[AC-5.1]`
- [x] Given a Critical or High row of any category (error handling, shadow path, interaction, security, architecture) whose `test` evidence block fails in the scoped run, when the Recommendation is written, then a confirmed Critical gives "Do not ship", a confirmed High with no confirmed Critical gives "Ship with caution", and a report with neither gives "ready to ship" and lists the unconfirmed findings under the Recommendation as worth a look. `[AC-5.2]`
- [x] Given a `/review` report whose evidence blocks are `recorded` or `check`, when `evidence --surface review` runs, then each such row reads `unverifiable kind_unavailable` and maps to `Medium (unconfirmed)`, and only `test` and `security-path` blocks can confirm. `[AC-5.3]`
- [x] Given a `/review` run, when Step 4 writes the report header, then the header has a `> Evidence gate: on|off|unverifiable (<reason>)` line beside the `> Reviewer filters: on|off` line, and with `Evidence Gate: off` in `.writ/config.md` it reads `> Evidence gate: off` and no row is downgraded. `[AC-5.4]`
- [x] Given the updated `commands/review.md`, when Step 3 and the Completion section are read, then Step 3 reads `skills/evidence-gated-findings/SKILL.md` after the filters `Read`, the filters `Read` and the `reviewer-filters` switch line stay, and the Outcome interpretation table counts confirmed findings only. `[AC-5.5]`

## Implementation Tasks

- [x] 5.1 Write `ReviewSurfaceParseTests` in `scripts/tests/test_review_override.py` first. Cover: the Severity column of each registry row is read; a `#### FM-NNN` block binds to its row by ID; a row with no block reports `no_evidence`; only Critical and High rows are run; an empty `--changed` maps every row to `location_outside_change_set`. Confirm they fail on the current tree. `[AC-5.1]`
- [x] 5.2 Write `ReviewSurfaceMappingTests` in the same file. Cover: a confirmed `test` row keeps its severity, including a row with Category `Error handling`; no row reports `no_claim` on this surface; `recorded` and `check` blocks report `kind_unavailable`; switch `off` prints `evidence-gate: off` and runs no repro. Confirm they fail on the current tree. `[AC-5.2, AC-5.3, AC-5.4]`
- [x] 5.3 Add `ReviewWiringTests` to `scripts/tests/test_evidence_gate_wiring.py`. Assert on `commands/review.md`: Step 3 reads the evidence skill after the filters Read; the filters Read and the `reviewer-filters` switch line are present; the header template has both a `> Evidence gate:` line and a `> Reviewer filters:` line; the Recommendation and the Outcome table follow confirmed findings. Confirm they fail on the current tree. `[AC-5.2, AC-5.4, AC-5.5]`
- [x] 5.4 Implement registry-table and `#### FM-NNN` parsing for `--surface review` in `scripts/review-override.py`, so the 5.1 tests pass. Follow the pattern of `review-panel.py` `_issue_entries`. Do not import it. Reuse `_inside`, `_cite_ok`, `_read_text`, and `_emit`. Stdlib only, Python 3.9 floor. `[AC-5.1]`
- [x] 5.5 Add kind rules, the per-row mapped severity, and the switch-off path to `--surface review`, so the 5.2 tests pass. Each per-row line prints its mapped severity. Line 1 is `fail` when any row confirms, otherwise `pass`. Skip the verdict check on this surface. A run-level unverifiable result leaves every severity unchanged. `[AC-5.2, AC-5.3, AC-5.4]`
- [x] 5.6 Edit `commands/review.md` so the 5.3 wiring tests pass. (a) Step 3 reads `skills/evidence-gated-findings/SKILL.md` after the filters Read. Keep the switch line, the filters Read, and the sentence that feeds the Step 4 filters header. (b) Technique 4 records one `#### FM-NNN` block per Critical or High row under `## Evidence`. (c) Step 4 writes the draft report, runs `evidence --surface review`, applies the mapping, then writes the header and the Recommendation. (d) The report template gains the `## Evidence` section after the Failure Modes Registry, and the evidence header line beside the reviewer-filters line. (e) The Recommendation and the Completion Outcome table count confirmed findings only. The Summary line counts mapped severities. Downgraded rows stay in the registry in full. Then run `python3 scripts/gen-platform-trees.py` and include the regenerated `cursor/plugin/commands/review.md` in the same change. `[AC-5.2, AC-5.4, AC-5.5]`
- [x] 5.7 Verify, one run at a time. Run the full `pytest` suite on Python 3.9, then on 3.14 (`uv run --isolated --python <version> --with pytest pytest`). Run `python3 scripts/gen-platform-trees.py --check`. Run `bash scripts/eval.sh`. Never run pytest alongside `eval.sh`. Confirm each criterion has a passing test or wiring assertion. `[AC-5.1, AC-5.2, AC-5.3, AC-5.4, AC-5.5]`

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

- [x] All tasks completed
- [x] All acceptance criteria met
- [x] Tests passing
- [x] Code reviewed
- [x] Documentation updated

## Context for Agents

- **Error map rows:** [`/review`, Parse issues, Read the review output] — technical-spec.md → ## Error & Rescue Map (row for /review: No diff files)
- **Shadow paths:** [Happy, Nil, Upstream error] — technical-spec.md → ## Shadow Paths
- **Business rules:** `spec.md → ## Business Rules (Expanded) → ### Which findings are evaluated`, `spec.md → ## Business Rules (Expanded) → ### Evidence outcomes`, `spec.md → ## Business Rules (Expanded) → ### Switch`, `technical-spec.md → ## Evidence Block Grammar`, `spec.md → ## Business Rules (Expanded) → ### /review`
- **Experience:** `spec.md → ## Experience Design → ### Who uses it`, `spec.md → ## Experience Design → ### Interaction patterns`

---

## What Was Built

**Implementation Date:** 2026-11-04

> The Gate 3 review loop exceeded its cap with user approval: three review iterations returned FAIL, and the user approved one more fix past the cap. No fourth review ran; the orchestrator verified the fix.

### Files Created

1. **`scripts/tests/test_review_mutation_stops_repro.py`** (9 lines)
   - Iteration 1, F2's confirmed `test` repro, committed verbatim. It asserts that Step 4 of `commands/review.md` names `repro_mutated_tree`, so a tree mutation stops `/review`.
2. **`scripts/tests/test_review_gate_off_outcome_repro.py`** (11 lines)
   - Iteration 1, F3's confirmed `test` repro, committed verbatim. It asserts that the Outcome interpretation names `off` and `unverifiable`, so with the gate off or unverifiable, Critical rows do not read ready to ship.
3. **`scripts/tests/test_review_gate_off_no_question_repro.py`** (10 lines)
   - Iteration 3, F1's confirmed `test` repro, committed verbatim (extracted with the script's own parser). It asserts that Step 4 conditions the question on the gate, so the gate `off` asks nothing.

### Files Modified

- **`scripts/review-override.py`** (module docstring; `--surface review` constants; `Finding.bound`; `_evidence_findings`; new `_registry_rows` and `_review_findings`; `_evidence_unverifiable`; `evidence`; `--surface` help; `main`)
  - `--surface review` reads a `/review` report: the Failure Modes Registry rows, keyed by FM ID, each bound to its `#### FM-NNN` block under `## Evidence`. Registry columns are found by header name, else taken as the first three. Fenced lines are never rows or headings.
  - Critical and High rows are evaluated. Any Category can confirm, so there is no `no_claim` on this surface. There is no verdict check. `recorded` and `check` give `unverifiable kind_unavailable`.
  - Line 2 is `evidence-gate: on|off|unverifiable (<reason>)`. Each `finding FM-NNN:` line ends `; severity <mapped>`. An unconfirmed Critical or High row maps to `Medium (unconfirmed)`.
  - A run-level `unverifiable`, a tree mutation included, prints no finding lines, so every severity stays as written. A repeated registry row is dropped with `reason: duplicate_row FM-NNN`.
  - Every new branch is gated on `review = surface == "review"`. The Gate 3 surface is unchanged: a 20-case differential against HEAD gave identical output.
- **`scripts/tests/test_review_override.py`** (`EvidenceEnvelopeTests`; new `ReviewSurfaceTestCase`, `ReviewSurfaceParseTests`, `ReviewSurfaceMappingTests`)
  - `ReviewSurfaceParseTests` (12) and `ReviewSurfaceMappingTests` (13), on the Story 2 fixture project and stubs.
  - `test_known_surfaces_and_later_story_flags_parse` now expects the `evidence-gate: on` line for `--surface review`.
- **`scripts/tests/test_evidence_gate_wiring.py`** (new `ReviewWiringTests`)
  - 12 wiring tests on `commands/review.md`, the skill, and the generated copies. They include `test_step4_always_asks_before_running_repros` and the W20 pin on "apply the first rule that matches".
- **`commands/review.md`** (Step 3; Technique 4; Step 4; report template; Recommendation section; Completion Outcome interpretation) — 10593 → 13279 bytes, +2686
  - Step 3: `switch --name evidence-gate`; on `on`, read `skills/evidence-gated-findings/SKILL.md` before Technique 4. The filters switch line, the filters Read, and the header sentence are unchanged.
  - Technique 4: an **Evidence.** paragraph. One `#### FM-NNN` block per Critical or High row; High reads as Major; the Location must be a file in the diff; only `test` and `security-path` apply.
  - Step 4: write the draft, then ask with AskQuestion before every run. A decline, a headless run, or no answer writes `> Evidence gate: unverifiable (untrusted_branch)`. With the gate `off`, skip the question. Run `evidence --surface review ... --timeout 60`, then apply the first matching rule: stop on `repro_mutated_tree`, map severities on `pass` or `fail`, leave them as written on `unverifiable`. The Summary line and the Recommendation are written last.
  - Template: `> Evidence gate: on|off|unverifiable (<reason>)` after `> Reviewer filters: on|off`, and a `## Evidence` section after the Failure Modes Registry.
  - Recommendation and Outcome table: count confirmed findings. With the gate `off` or `unverifiable`, every Critical and High row counts as written. With no confirmed Critical or High, the report says ready to ship and lists the `Medium (unconfirmed)` rows as worth a look.
- **`skills/evidence-gated-findings/SKILL.md`** (selection rules; reason table)
  - One sentence deferring `/review`'s rules to `commands/review.md`, and a `kind_unavailable` row.
- **5 generated trees** (`scripts/gen-platform-trees.py`)
  - `cursor/plugin/commands/review.md`, `plugins/writ/commands/review.md`, `cursor/plugin/skills/evidence-gated-findings/SKILL.md`, `plugins/writ/skills/evidence-gated-findings/SKILL.md`, `plugins/writ/scripts/review-override.py`.
- **`.writ/docs/config-format.md`** (Evidence Gate)
  - The gate covers a `/review` run. A paragraph on `Medium (unconfirmed)`, the question before the run, `untrusted_branch`, and `off`.
- **`.writ/docs/agent-cli-contract.md`** (`review-override.py` row)
  - The `--surface review` output form, and the exit-code difference on a tree mutation: `unverifiable`, exit 0 on `review`; `fail`, exit 1 on `gate3`.
- **`README.md`** (Shipping & Review table, `/review` row)
  - The question before the run and the `Medium (unconfirmed)` downgrade.
- **`.writ/specs/2026-11-04-evidence-gated-review/spec-lite.md`** (For Review Agents)
  - A "Story 5 `/review` surface (DEV-012 to DEV-017)" block.
- **`.writ/specs/2026-11-04-evidence-gated-review/drift-log.md`** (Story 5 section)
  - DEV-012 to DEV-018 appended. Existing entries untouched.

### Implementation Decisions

1. **The registry gives the Severity; the block gives the Location and Evidence** — the block's Category wins when it has one, with the registry's as fallback. A block's own Severity never lifts a row (DEV-015).
2. **A row with no block is `no_evidence`** — with diff files, it is unevidenced, not out of scope. With an empty `--changed`, every row is `location_outside_change_set`.
3. **The mapped severity is the cell's first word** — so a bold `**High**` cell prints `severity High`, and an unconfirmed Critical or High row prints `severity Medium (unconfirmed)`.
4. **A tree mutation is run-level `unverifiable` on this surface** — no row's evidence can be trusted after the tree changed, so every severity stays as written, and Step 4 stops on the reason before any Recommendation (DEV-012).
5. **Always ask before the run** — the user's second decision. The question names the risk: the step runs the branch's own test code in the user's working tree. A decline, a headless run, or no answer is `untrusted_branch` (DEV-016).
6. **The gate `off` asks nothing** — the past-cap fix. With nothing to run, the question has no purpose, and AC-5.4 requires `> Evidence gate: off`.
7. **`--timeout 60`** — five runs fit a 600 s tool call, as on Gate 3 (DEV-017).

### Test Results

**Verification:** Automated, test-first.
**Coverage:** new `--surface review` code 98.3% lines. `scripts/review-override.py` 91.4% → 92.0% lines; re-derived by `test-integrity.py coverage --report … --prior …`: pass, 92.05%.

- ✅ Red first: Gate 1 red at 19 + 7 failed, then green. Recode 1: red at 8 failed, then 218 passed. Recode 2: the always-ask rule. Past-cap fix: the iteration-3 repro went red, then green.
- ✅ Story tests: 219/219 on Python 3.9 and on 3.14.
- ⚠️ Full suite: 4310 passed, 1 failed, 2 skipped on both interpreters. The failure is `test_divergence_trial_outcome.py::test_repo_matches_the_committed_verdict`. It predates this story, and origin's design-divergence commits fix it.
- ✅ Bash suite: all green.
- ✅ `bash scripts/eval.sh`: exit 0.
- ✅ `python3 scripts/gen-platform-trees.py --check`: pass.
- ⚠️ Authenticity on the three repros: `test_imports_no_source`. This is the known false positive for tests that read docs (open issue 2026-09-03).

### Byte count

`wc -c commands/review.md`: before 10593, after 13279, delta +2686. `commands/implement-story.md` is not touched by this story.

### Review Outcome

**Result:** FAIL at the review-loop cap (3 iterations); closed by a user-approved past-cap fix

- **Iteration count:** 3 iteration(s), plus one user-approved fix past the cap
- **Drift:** Medium (DEV-016 and DEV-018, logged); DEV-012 to DEV-015 and DEV-017 Small, spec-lite auto-amended
- **Security:** Low (iteration 3). Medium in iterations 1 and 2, until the always-ask step.
- **Boundary Compliance:** All hand edits are in Owned files. The outside-boundary files are regenerated trees or confirmed repros committed verbatim, which is justified. The iteration-2 trust repro was rightly not created; a user decision overtook it.

### Gate record

**REVIEW_RESULT:** FAIL

Iteration 1, `review-agent`, saved at `.writ/state/gate3-review-story-5-review-evidence-gating-iter1.md`. `evidence-gate: 3 confirmed, 3 advisory, 0 unverifiable`.

- F1, `security-path`: `/review` ran the checked-out branch's code by default.
- F2, `test` repro: a tree mutation did not stop `/review`. Repro committed verbatim as `scripts/tests/test_review_mutation_stops_repro.py`.
- F3, `test` repro: with the gate `off` or `unverifiable`, Critical rows read ready to ship. Repro committed verbatim as `scripts/tests/test_review_gate_off_outcome_repro.py`.

**REVIEW_RESULT:** FAIL

Iteration 2, `review-agent`, saved at `.writ/state/gate3-review-story-5-review-evidence-gating-iter2.md`. `evidence-gate: 1 confirmed, 2 advisory, 0 unverifiable`.

- F1, confirmed by `test` repro: the rule gave no outcome when the user cannot be asked (headless).
- F2, advisory, no evidence: the author email (`%ae`) can be forged.
- The F1 repro (`scripts/tests/test_review_trust_rule_repro.py`) was not committed. Its `"every commit"` assertion encoded the email rule the user then removed (DEV-018). Its "no answer" intent is pinned by `test_step4_always_asks_before_running_repros`.

**REVIEW_RESULT:** FAIL

Iteration 3, `review-agent`, saved at `.writ/state/gate3-review-story-5-review-evidence-gating-iter3.md`. `evidence-gate: 1 confirmed, 0 advisory, 0 unverifiable`.

- F1, confirmed by `test` repro: Step 4 asked the question even with the gate `off`, so a decline wrote `unverifiable (untrusted_branch)`, not `off`.
- Review-loop cap reached; escalated to the user.

**Past-cap fix (user-approved):** the user chose "Apply fix, past cap". The orchestrator committed the iteration-3 repro `scripts/tests/test_review_gate_off_no_question_repro.py` verbatim and added one sentence to Step 4: "With the evidence gate `off`, skip the question: the step runs nothing and prints `evidence-gate: off`." The repro went red, then green. No fourth review ran.

**User decisions:**

1. 2026-11-04, after iteration 1: ask before the evidence run unless every commit is the user's.
2. 2026-11-04, after iteration 2: always ask. A headless run or no answer counts as a decline. The email rule is removed.

- **Gate 0:** arch-check pass (rederived proceed). `gate0-divergence: skip (usage locked by spec.md § /review and technical-spec § /review form)`
- **Gate 0.5:** boundary map computed (`.writ/state/boundary-story-5-review-evidence-gating.json`)
- **Gate 1:** coding-agent, test-first. Red at 19 + 7 failed, then green. Recode 1: red at 8, then 218. Recode 2: the always-ask rule. Past-cap fix: one sentence, applied by the orchestrator with the user's approval.
- **Gate 2:** no linters. `arch-lint: none — see .writ/docs/architecture-lint.md`. `build-smoke: unverifiable (unsupported_stack)`
- **Gate 2.5:** cross-component. `gate3-route: review-agent (outside_boundary plugins/writ/commands/review.md plugins/writ/scripts/review-override.py)`
- **Gate 3:** `reviewer-filters: on`. 3 iterations, all FAIL, plus one user-approved past-cap fix. evaluator_fail_count reached 2, so the rest of the story ran as `--full-pipeline`. `review-override check`: pass. `safety-fact: tested (claimed tested)`. `review-panel: skipped — platform cannot spawn other vendors`. `jev: not run` (the diff is large; Story 2's run was `state_too_large`).
- **Gate 3.5:** Overall Medium. DEV-012 to DEV-015 and DEV-017 Small: spec-lite auto-amended. DEV-016 Medium: the always-ask consent step, user-approved. DEV-018 Medium: the overtaken repro. drift-format: `fail large_drift_without_pause`. This is the known false positive from Story 1's DEV-001 section; Story 5 had no Large drift, so no PAUSE line was added.
- **Gate 4:** testing-agent (`--full-pipeline`), TEST_RESULT PASS. 219/219 targeted on 3.9 and 3.14. Full suite 4310 passed, 1 failed (predates this story), 2 skipped on both. Coverage as above. Bash suite green. `eval.sh` exit 0. `gen-platform-trees.py --check` pass.
- **Gate 4.5:** `app-verify: unverifiable (no_recipe)`. No visual refs, so no visual-qa.
- **Gate 5:** documentation-agent (`--full-pipeline`), DOCS_UPDATED: YES. `docs-check: unverifiable (no public exports in the changed set)`

### Deviations from Spec

- **[DEV-012] A tree mutation on `/review` is run-level `unverifiable`, and the command stops on the reason** — Severity: Small (Medium in iteration 1; the stop added in recode 1 restores BLOCKED)
  - Spec said: Contract Hardest Constraint: "the result is BLOCKED with `repro_mutated_tree`." technical-spec § CLI: line 1 `fail` when the tree changed, with that reason first.
  - Reality: `--surface review` prints `unverifiable` and `evidence-gate: unverifiable (repro_mutated_tree <paths>)`, exit 0, and no finding lines. Step 4's first rule stops on the reason and holds back the Recommendation and `/ship` until the user decides. "First rule that matches" is pinned.
  - Resolution: Auto-amended spec-lite.md
  - Spec amendment: technical-spec § CLI: "On `--surface review`, a tree change prints line 1 `unverifiable` with `reason: repro_mutated_tree <paths>` and no finding lines; `/review` stops on that reason until the user decides."
- **[DEV-013] With no `Test Runner`, `/review` stays run-level unless a `security-path` row reaches confirmed or advisory** — Severity: Small
  - Spec said: § /review: run-level `unverifiable` includes "`no_test_runner` with no `security-path` rows".
  - Reality: DEV-003's rule. A run whose `security-path` rows are all unverifiable stays run-level, and its severities stay as written. `test_no_test_runner_with_an_advisory_security_path_row` covers the advisory side (kills M24).
  - Resolution: Auto-amended spec-lite.md
  - Spec amendment: § /review: replace "`no_test_runner` with no `security-path` rows" with "`no_test_runner` when no `security-path` row reaches `confirmed` or `advisory`".
- **[DEV-014] `/review` output form: line 2 is the header value, and finding lines end `; severity <mapped>`** — Severity: Small
  - Spec said: technical-spec § CLI shows only the Gate 3 form. Task 5.5 gives no format for the mapped severity.
  - Reality: Line 2 is `evidence-gate: on|off|unverifiable (<reason>)`. Each `finding FM-NNN:` line ends `; severity <word>`, where the word is the cell's first word, or `Medium (unconfirmed)`.
  - Resolution: Auto-amended spec-lite.md
  - Spec amendment: technical-spec § CLI: "On `--surface review`, line 2 is `evidence-gate: on|off|unverifiable (<reason>)`, and each `finding FM-NNN:` line ends `; severity <mapped>`."
- **[DEV-015] Registry and block binding rules the spec leaves open** — Severity: Small
  - Spec said: technical-spec § /review form shows a block with its own Category. The spec does not say which Category wins, or what a repeated block or row does.
  - Reality: The block's Category wins, with the registry's as fallback, and the registry's Severity always wins. A second block for an ID adds `reason: extra_evidence FM-NNN`. A repeated registry row is dropped with `reason: duplicate_row FM-NNN`.
  - Resolution: Auto-amended spec-lite.md
  - Spec amendment: technical-spec § /review form: "The block's Category wins over the registry's; the registry's Severity always wins. A second block for an ID is ignored with `reason: extra_evidence FM-NNN`, and a repeated registry row with `reason: duplicate_row FM-NNN`."
- **[DEV-016] `/review` always asks before the evidence run (`untrusted_branch`)** — Severity: Medium
  - Spec said: § /review lists the run-level `unverifiable` reasons as `no_review_output`, `no_git`, and `no_test_runner`. It has no consent step.
  - Reality: Step 4 asks with AskQuestion before every run. A decline, a headless run, or no answer skips the run, writes `unverifiable (untrusted_branch)`, and leaves every severity as written. The iteration-2 email rule (`%ae`, `user.email`, `<base>`) is removed. The past-cap fix closed the open edge: with the gate `off`, Step 4 asks nothing.
  - Resolution: ⚠️ Medium — logged, PASS. User-approved on 2026-11-04 (two decisions: ask unless yours, then always ask).
  - Spec amendment: § /review: "With the evidence gate `on`, `/review` asks before every evidence run. A decline, a headless run, or no answer gives `unverifiable (untrusted_branch)`, and every severity stays as written."
- **[DEV-017] `/review` passes `--timeout 60`** — Severity: Small
  - Spec said: technical-spec § CLI default timeout is 120 s. DEV-011 set 60 s for Gate 3.
  - Reality: The Step 4 command passes `--timeout 60`, pinned by `test_step4_runs_evidence_on_the_draft_then_maps_severities`.
  - Resolution: Auto-amended spec-lite.md
  - Spec amendment: technical-spec § CLI: "`/review` passes `--timeout 60`, as Gate 3 does (DEV-011)."
- **[DEV-018] A confirmed repro was not committed: the user's decision overtook it** — Severity: Medium
  - Spec said: Business Rules: the coder commits a confirmed repro byte for byte and never edits it; disputes go to the loop cap and then to the user.
  - Reality: The iteration-2 repro `scripts/tests/test_review_trust_rule_repro.py` was confirmed, but it asserted `"every commit"`, which encodes the email rule. The user then replaced that rule with always-ask. The orchestrator did not commit the repro. Its other intent (no answer or headless = decline) is pinned by `test_step4_always_asks_before_running_repros`, and the iteration-3 reviewer agreed.
  - Resolution: ⚠️ Medium — logged, PASS.
  - Spec amendment: None. Story 4's re-review check (`repro_removed`) only covers repros listed in a manifest; this one never entered one.

### Notes for Downstream Stories

- **Story 4: first real examples.** The three committed repros are the first real instances of "commit a confirmed repro verbatim". Story 4's manifest and `--prior` logic should treat them as its examples: `scripts/tests/test_review_mutation_stops_repro.py`, `scripts/tests/test_review_gate_off_outcome_repro.py`, and `scripts/tests/test_review_gate_off_no_question_repro.py`.
- **Optional, left for the user:** ask only when some block uses `test`, so a headless run can still confirm `security-path` rows. This narrows always-ask.
- **Not fixed:** mutant W23, an inverted headless clause that keeps the word "headless" ("in a headless run, run it"), survives. Phrase pins cannot catch it.
