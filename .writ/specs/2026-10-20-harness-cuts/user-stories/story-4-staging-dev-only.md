# Story 4: Make Recommended-Delivery Staging Dev-Only

> **Status:** Completed ✅
> **Priority:** High
> **Dependencies:** Story 2

## User Story

**As a** Writ maintainer and developer who installs Writ into their projects
**I want to** stop shipping `recommend-state.py` and the recommended-delivery state-format doc, and drop the drift-triage branch that calls them
**So that** installed projects stop carrying 3,807 lines of staging code and a 794-line contract that no command uses, while the design and its eval checks stay in the Writ source repo

## Acceptance Criteria

> **AC IDs assigned through:** AC-4.5

- [x] Given `scripts/install.sh`, `scripts/update.sh`, and `scripts/unlink.sh`, when `is_shippable_script recommend-state.py` runs from each body, then it returns non-zero in all three and the bodies are byte-identical; and `is_shippable_writ_doc` exists in `install.sh` and `update.sh` with identical bodies, rejects `recommended-delivery-state-format.md`, accepts every other `.writ/docs/*.md`, and both source files still exist `[AC-4.1]`
- [x] Given a temp project for each of claude, cursor, and codex, when `install.sh --no-commit` runs with `--dry-run` and then for real, then neither `scripts/recommend-state.py` nor `.writ/docs/recommended-delivery-state-format.md` appears in the output, on disk, or in the platform manifest, and every other shipped script and doc still installs `[AC-4.2]`
- [x] Given a temp project whose manifest records unmodified copies of both files, when `update.sh --dry-run` and then `update.sh` run, then the dry run lists both as stale and removes nothing, and the real run removes both and prints `🗑  Removed: <path>` for each; and given locally modified copies instead, both survive two runs byte for byte and each run prints the kept-stale warning naming each path `[AC-4.3]`
- [x] Given the shipped sources, when they are read, then `skills/drift-triage/SKILL.md` has no recommended-mode text and no pre-edit SHA-256 capture, no file under `commands/`, `agents/`, `skills/`, `adapters/`, or `.writ/docs/` (except the state doc itself) or `SKILL.md` names `scripts/recommend-state.py`, `SKILL.md` no longer says install, update, and unlink manage the state doc and `bash scripts/gen-skill.sh --check` prints `pass`, `.writ/docs/agent-cli-contract.md` lists `recommend-state.py` with the dev-only scripts and has no table row for it, and `commands/update-writ.md` Step 3 names both exclusions `[AC-4.4]`
- [x] Given `bash scripts/eval.sh` in the source repo, when it runs, then `check_recommended_spec_implementation` and `check_recommended_staging` still run and pass their reducer, static, and state-doc scenarios against the source tree, the lifecycle scenarios assert absence on install, removal on update, and an untouched helper symlink on unlink for all three platforms, and the run reports 0 findings `[AC-4.5]`

## Implementation Tasks

- [x] 4.1 Write failing tests first: extend `scripts/tests/test_install_update_harness_cuts.sh` with the filter checks, the claude upgrade-path cases, and the shipped-source grep (technical-spec.md → ### Upgrade-path test additions); add `recommend-state.py` to `DEV_ONLY` in `scripts/tests/test_agent_cli_contract_doc.py`; rewrite the lifecycle scenarios in `scripts/eval.sh` `check_recommended_spec_implementation` (lines 1793-1939) per the technical spec's table. Run them and record the failures `[AC-4.1, AC-4.2, AC-4.3, AC-4.4, AC-4.5]`
- [x] 4.2 Ship filters: add `recommend-state.py` to the dev-only arm of `is_shippable_script` in `install.sh`, `update.sh`, and `unlink.sh`; add `is_shippable_writ_doc` to `install.sh` and `update.sh`; pass the `doc` filter at the four `.writ/docs` `overlay_scan_flat_dir` call sites; skip rejected docs in both `append_manifest_writ_docs`; add the filter-rejected `.writ` arm to `update.sh` `detect_stale_files` `[AC-4.1, AC-4.2, AC-4.3]`
- [x] 4.3 `skills/drift-triage/SKILL.md`: the Small route becomes "Auto-amend **only** `spec-lite.md` and append **one unique `DEV-NNN` entry** to `drift-log.md`", then "Continue **PASS**" and the run-summary bullet. Delete the two recommended-mode bullets (lines 37-43) and the "never batch" bullet (lines 79-82) `[AC-4.4]`
- [x] 4.4 Prose: in `.writ/docs/agent-cli-contract.md` delete the `recommend-state.py` row (111) and note (137), add it to the dev-only sentence (126), and drop it as the example at line 43; in `.writ/docs/acceptance-criteria-ids.md:34,43` name it as the source-repo, dev-only parser without the `scripts/` path; in `commands/update-writ.md` add it to the dev-only list (111), exclude the state doc from the docs paragraph (115), and add filter-rejected docs to "Detect stale files" (124) `[AC-4.4]`
- [x] 4.5 `scripts/gen-skill.sh` lines 612-616: reword the Runtime Contract paragraph to say the state doc records ADR-013's dormant staging design, stays in the Writ source repo, and is not installed. Run `bash scripts/gen-skill.sh` to regenerate `SKILL.md`, then `bash scripts/gen-skill.sh --check` must print `pass`. Leave `.writ/manifest.yaml` `metadata.runtime_contract` as it is `[AC-4.4]`
- [x] 4.6 Verify install and update: `for t in scripts/tests/test_*.sh; do bash "$t" || echo "FAIL $t"; done`, then `bash scripts/install.sh --dry-run --no-commit --platform <p>` from a fresh temp directory for each of claude, cursor, and codex, confirming neither file is listed. Never run `install.sh` or `update.sh` against the Writ repo itself; use temp directories `[AC-4.1, AC-4.2, AC-4.3]`
- [x] 4.7 Verify the suite: `uv run --python 3.9 pytest` (including `test_agent_cli_contract.py` table completeness) and `bash scripts/eval.sh` outside the sandbox with 0 findings; confirm the `eval-recommend-stage.py` and `eval-recommend-state-adversarial.py` scenarios are still counted `[AC-4.4, AC-4.5]`

## Notes

- **The `.writ/docs` filter is new.** Today every file in the source `.writ/docs/` ships, and `append_manifest_writ_docs` records every local `.writ/docs/*.md`. Without the `detect_stale_files` arm, the state doc stays upstream, never counts as stale, and is never removed.
- **AC-4.3's kept-doc case depends on `2026-10-20-ci-and-update-integrity`.** The kept-script case works today. Read `detect_stale_files` and `write_copy_manifest` as that spec left them and match its warning text.
- **The eval lifecycle scenarios pin the opposite behavior today.** They require install, update, and unlink to ship both files. Invert them; do not delete the check. Keep the reducer scenarios, the static `create-spec` matrix checks, and `check_recommended_staging` unchanged.
- **`unlink.sh` gets only the arm change.** Its `.writ/docs` loop still converts a symlinked state doc to a copy, and the next `update.sh` removes that copy as stale. The unlink state-doc scenarios are deleted.
- **Why drift-triage loses the SHA capture.** The pre-edit SHA-256 was the "prior SHA-256" argument to `record-spec-lite-amendment`. Nothing else reads it.
- **Do not add `recommend-state.py` to `DEV_SCRIPTS` in `test_install_update_dev_scripts.sh`.** That test greps the source `.writ/docs/`, which still contains the state doc that names the script. The new test excludes that one file.
- **Leave alone:** `scripts/recommend-state.py`, `scripts/eval-recommend-*.py`, `scripts/tests/test_recommend_state_ac_tag_compat.py`, ADR-013, `.writ/docs/recommended-delivery-state-format.md`, `.writ/docs/config-format.md`'s staging keys, and `.writ/docs/exit-criteria-classification.md:138` (bare name, describes legacy plans).
- **Never run `install.sh` or `update.sh` against the Writ repo.** Use temp directories.

## Definition of Done

- [x] All tasks completed
- [x] All acceptance criteria met
- [x] Tests passing
- [x] Code reviewed
- [x] Documentation updated

## Context for Agents

- **Error map rows:** [Fresh install, Update removes an unmodified cut file, Update keeps a modified cut file, Re-install over an old project, Rewrite the eval lifecycle scenarios, Regenerate SKILL.md]
- **Shadow paths:** [Install (any platform), Update over an old install, Update with a modified cut file]
- **Business rules:** [Rule 3 (ship filters stay identical), Rule 4 (dev-only and stale handling), Rule 9 (no dangling reference), Rule 10 (never run install/update against the Writ repo), Rule 11 (every story leaves the tree green)]
- **Experience:** [State Catalog: Fresh install any platform, Update old unmodified copies present, Update a copy edited locally, Re-install with install.sh over an old project, Writ source repo]
- **Technical:** technical-spec.md → ## Current State → ### Recommended-delivery staging inventory; ## Story 4 Design

---

## What Was Built

**Implementation Date:** 2026-10-21

### Files Created

[None created]

### Files Modified

- **`scripts/install.sh`, `scripts/update.sh`, `scripts/unlink.sh`** — `recommend-state.py` joins the dev-only arm of `is_shippable_script`; the three bodies stay byte-identical.
- **`scripts/install.sh`, `scripts/update.sh`** — new `is_shippable_writ_doc` (rejects only `recommended-delivery-state-format.md`; identical in both); `overlay_scan_flat_dir` gains a `doc` filter passed at the four `.writ/docs` call sites; both `append_manifest_writ_docs` skip rejected docs.
- **`scripts/update.sh`** (`detect_stale_files`) — a manifest-listed `.writ` doc the filter rejects is stale, beside the `scripts` arm. The kept-modified branch is unchanged.
- **`scripts/exit-criteria.py`, `scripts/story-deps.py`** — one comment and one docstring no longer name `recommend-state.py` (Business Rule 9; Gate 3 iteration 1 finding).
- **`skills/drift-triage/SKILL.md`** — the Small route no longer captures a pre-edit SHA-256 or has a recommended-mode branch; the "never batch" principle is gone.
- **`.writ/docs/agent-cli-contract.md`** — no `recommend-state.py` row, note, or usage example; it is the sixth dev-only script, holding ADR-013's dormant staging reducers.
- **`.writ/docs/acceptance-criteria-ids.md`** — names the parser as Writ's source-repo `recommend-state.py` (dev-only, not installed).
- **`commands/update-writ.md`** (Step 3) — names `recommend-state.py` as dev-only, ships every doc except the state doc, and counts filter-rejected docs as stale.
- **`scripts/gen-skill.sh`, `SKILL.md`** — the Runtime Contract says the state doc records ADR-013's dormant design, stays in the source repo with its reducer, and is not installed. `.writ/manifest.yaml` is unchanged.
- **`scripts/eval.sh`** (`check_recommended_spec_implementation` lifecycle block) — per platform (cursor, claude, codex): `install-{p}-dry-run-names-neither`, `install-{p}-omits-helper`, `install-{p}-omits-state-doc`, `update-{p}-dry-run-lists-stale`, `update-{p}-removes-helper`, `update-{p}-removes-state-doc`, `unlink-{p}-skips-helper`. The 12 old lifecycle names per platform are gone, including the unlink state-doc scenarios. Emitted name templates went from 56 to 51; no reducer, static, state-doc, or adversarial name changed.
- **`scripts/tests/test_install_update_harness_cuts.sh`** — AC-4.1 filter checks; AC-4.2 dry and real installs on claude, cursor, and codex (no output line, file, or manifest line for either file; every other shipped script and doc installed and recorded with its upstream hash; a codex re-install does not record old copies); AC-4.3 unmodified copies listed stale then removed with `🗑  Removed:`, modified copies kept byte for byte across two runs with a warning each run and the original baseline, and a nil-input case; AC-4.4 shipped-source grep plus a guard over every shipped script.
- **`scripts/tests/test_harness_cuts.py`** — 7 AC-4.4 prose tests and 4 AC-4.5 structural tests (DEV-007).
- **`scripts/tests/test_agent_cli_contract_doc.py`** — `recommend-state.py` in `DEV_ONLY`; six dev-only scripts.
- **`scripts/tests/test_manifest_shipped_baselines.sh`** — the shipped-set builder applies `is_shippable_writ_doc` (DEV-008).

### Implementation Decisions

1. **The shipped-scripts guard uses `is_shippable_script` itself**, so the shipped set comes from the filter rather than a list in the test.
2. **A nil-input codex case** was added because the first mutation run showed that removing update.sh's manifest skip survived: the kept-file carry-forward wrote the same line.

### Test Results

**Verification:** test-first, then full suites.

- Red: the bash test failed on the unchanged scripts (`install.sh: is_shippable_script accepts recommend-state.py`), then on the AC-4.4 grep; 9 of 11 new Python tests failed on a `git archive HEAD` copy; all 21 new eval lifecycle scenarios failed before the script changes while the 76 reducer, 16 static, 50 adversarial, and 60 stage scenarios passed; the shipped-scripts guard failed naming `exit-criteria.py:200` and `story-deps.py:263` before the comment edits.
- Mutations (coder and reviewer, scratch copies): removing the `.writ` stale arm, either manifest skip, or a `doc` filter call site each fails the bash test; a planted mention in a shipped script fails the guard.
- AC-4.5 evidence: `bash scripts/eval.sh` → recommended-spec-implementation 147/147 scenarios and 16/16 static, recommended-staging 60/60, Findings 0 (orchestrator run of `--check=recommended-spec-implementation`: 147/147, Findings 0).
- Orchestrator run: `test_harness_cuts.py`, `test_agent_cli_contract_doc.py`, `test_agent_cli_contract.py`, `test_drift_severity_wiring.py`, `test_recommend_state_ac_tag_compat.py` → 369 passed; five install/update bash tests → PASS; `gen-skill.sh --check` → pass.
- Full suites (coder and reviewer, run alone): pytest → 2607 passed, 2 skipped (+11 new, −5 contract cases for the no-longer-shipped script); bash loop → 39 run, 0 failed; `bash scripts/eval.sh` → `Findings: 0`.
- Completion simulation: `review-override.py check` → `pass`.

### Review Outcome

**Result:** PASS

- **Iteration count:** 2 iteration(s)
- **Drift:** Small (DEV-007, DEV-008)
- **Security:** Clean
- **Boundary Compliance:** all edits in owned or orchestrator-allowed files
- gate3-route: review-agent (outside_boundary SKILL.md). review-panel: skipped (platform cannot spawn other vendors). arch-lint: none — see .writ/docs/architecture-lint.md.
- Gate 0 arch-check: pass. Gate 2: no linter configured; `bash -n`, `py_compile`, and `lint-skill.sh` clean; build-smoke unverifiable (unsupported stack). Gate 3 iteration 1: PASS with Medium drift (two shipped scripts still named `recommend-state.py` in comments, Business Rule 9); the orchestrator sent it back for the comment fix. Iteration 2: PASS. Gate 3.5 drift-format: pass. Gate 4 coverage: unverifiable (no report). Gate 4 authenticity: `test_imports_no_source` on `test_install_update_harness_cuts.sh`, the known false positive for bash tests (`.writ/issues/improvements/2026-10-12-test-integrity-shell-tests.md`); carried on the red-phase and mutation evidence above, not DEGRADED. Gate 4.5: app-verify unverifiable (no recipe). Gate 5: docs-check unverifiable (no public exports).

### Deviations from Spec

- **[DEV-007] AC-4.4 and AC-4.5 tests added to `test_harness_cuts.py`** — Severity: Small
  - Spec said: Story 4 tests live in the bash test, `test_agent_cli_contract_doc.py`, and the eval scenarios.
  - Reality: 11 more tests in `test_harness_cuts.py` so every criterion has a test-file citation.
  - Resolution: Auto-amended.
  - Spec amendment: spec-lite.md S4 line.
- **[DEV-008] `test_manifest_shipped_baselines.sh` applies the new doc filter** — Severity: Small
  - Spec said: not in the inventory.
  - Reality: its shipped-set builder skips docs `is_shippable_writ_doc` rejects.
  - Resolution: Auto-amended.
  - Spec amendment: spec-lite.md S4 line.
