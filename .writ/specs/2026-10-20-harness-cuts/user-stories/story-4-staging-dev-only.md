# Story 4: Make Recommended-Delivery Staging Dev-Only

> **Status:** Not Started
> **Priority:** High
> **Dependencies:** Story 2

## User Story

**As a** Writ maintainer and developer who installs Writ into their projects
**I want to** stop shipping `recommend-state.py` and the recommended-delivery state-format doc, and drop the drift-triage branch that calls them
**So that** installed projects stop carrying 3,807 lines of staging code and a 794-line contract that no command uses, while the design and its eval checks stay in the Writ source repo

## Acceptance Criteria

> **AC IDs assigned through:** AC-4.5

- [ ] Given `scripts/install.sh`, `scripts/update.sh`, and `scripts/unlink.sh`, when `is_shippable_script recommend-state.py` runs from each body, then it returns non-zero in all three and the bodies are byte-identical; and `is_shippable_writ_doc` exists in `install.sh` and `update.sh` with identical bodies, rejects `recommended-delivery-state-format.md`, accepts every other `.writ/docs/*.md`, and both source files still exist `[AC-4.1]`
- [ ] Given a temp project for each of claude, cursor, and codex, when `install.sh --no-commit` runs with `--dry-run` and then for real, then neither `scripts/recommend-state.py` nor `.writ/docs/recommended-delivery-state-format.md` appears in the output, on disk, or in the platform manifest, and every other shipped script and doc still installs `[AC-4.2]`
- [ ] Given a temp project whose manifest records unmodified copies of both files, when `update.sh --dry-run` and then `update.sh` run, then the dry run lists both as stale and removes nothing, and the real run removes both and prints `🗑  Removed: <path>` for each; and given locally modified copies instead, both survive two runs byte for byte and each run prints the kept-stale warning naming each path `[AC-4.3]`
- [ ] Given the shipped sources, when they are read, then `skills/drift-triage/SKILL.md` has no recommended-mode text and no pre-edit SHA-256 capture, no file under `commands/`, `agents/`, `skills/`, `adapters/`, or `.writ/docs/` (except the state doc itself) or `SKILL.md` names `scripts/recommend-state.py`, `SKILL.md` no longer says install, update, and unlink manage the state doc and `bash scripts/gen-skill.sh --check` prints `pass`, `.writ/docs/agent-cli-contract.md` lists `recommend-state.py` with the dev-only scripts and has no table row for it, and `commands/update-writ.md` Step 3 names both exclusions `[AC-4.4]`
- [ ] Given `bash scripts/eval.sh` in the source repo, when it runs, then `check_recommended_spec_implementation` and `check_recommended_staging` still run and pass their reducer, static, and state-doc scenarios against the source tree, the lifecycle scenarios assert absence on install, removal on update, and an untouched helper symlink on unlink for all three platforms, and the run reports 0 findings `[AC-4.5]`

## Implementation Tasks

- [ ] 4.1 Write failing tests first: extend `scripts/tests/test_install_update_harness_cuts.sh` with the filter checks, the claude upgrade-path cases, and the shipped-source grep (technical-spec.md → ### Upgrade-path test additions); add `recommend-state.py` to `DEV_ONLY` in `scripts/tests/test_agent_cli_contract_doc.py`; rewrite the lifecycle scenarios in `scripts/eval.sh` `check_recommended_spec_implementation` (lines 1793-1939) per the technical spec's table. Run them and record the failures `[AC-4.1, AC-4.2, AC-4.3, AC-4.4, AC-4.5]`
- [ ] 4.2 Ship filters: add `recommend-state.py` to the dev-only arm of `is_shippable_script` in `install.sh`, `update.sh`, and `unlink.sh`; add `is_shippable_writ_doc` to `install.sh` and `update.sh`; pass the `doc` filter at the four `.writ/docs` `overlay_scan_flat_dir` call sites; skip rejected docs in both `append_manifest_writ_docs`; add the filter-rejected `.writ` arm to `update.sh` `detect_stale_files` `[AC-4.1, AC-4.2, AC-4.3]`
- [ ] 4.3 `skills/drift-triage/SKILL.md`: the Small route becomes "Auto-amend **only** `spec-lite.md` and append **one unique `DEV-NNN` entry** to `drift-log.md`", then "Continue **PASS**" and the run-summary bullet. Delete the two recommended-mode bullets (lines 37-43) and the "never batch" bullet (lines 79-82) `[AC-4.4]`
- [ ] 4.4 Prose: in `.writ/docs/agent-cli-contract.md` delete the `recommend-state.py` row (111) and note (137), add it to the dev-only sentence (126), and drop it as the example at line 43; in `.writ/docs/acceptance-criteria-ids.md:34,43` name it as the source-repo, dev-only parser without the `scripts/` path; in `commands/update-writ.md` add it to the dev-only list (111), exclude the state doc from the docs paragraph (115), and add filter-rejected docs to "Detect stale files" (124) `[AC-4.4]`
- [ ] 4.5 `scripts/gen-skill.sh` lines 612-616: reword the Runtime Contract paragraph to say the state doc records ADR-013's dormant staging design, stays in the Writ source repo, and is not installed. Run `bash scripts/gen-skill.sh` to regenerate `SKILL.md`, then `bash scripts/gen-skill.sh --check` must print `pass`. Leave `.writ/manifest.yaml` `metadata.runtime_contract` as it is `[AC-4.4]`
- [ ] 4.6 Verify install and update: `for t in scripts/tests/test_*.sh; do bash "$t" || echo "FAIL $t"; done`, then `bash scripts/install.sh --dry-run --no-commit --platform <p>` from a fresh temp directory for each of claude, cursor, and codex, confirming neither file is listed. Never run `install.sh` or `update.sh` against the Writ repo itself; use temp directories `[AC-4.1, AC-4.2, AC-4.3]`
- [ ] 4.7 Verify the suite: `uv run --python 3.9 pytest` (including `test_agent_cli_contract.py` table completeness) and `bash scripts/eval.sh` outside the sandbox with 0 findings; confirm the `eval-recommend-stage.py` and `eval-recommend-state-adversarial.py` scenarios are still counted `[AC-4.4, AC-4.5]`

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

- [ ] All tasks completed
- [ ] All acceptance criteria met
- [ ] Tests passing
- [ ] Code reviewed
- [ ] Documentation updated

## Context for Agents

- **Error map rows:** [Fresh install, Update removes an unmodified cut file, Update keeps a modified cut file, Re-install over an old project, Rewrite the eval lifecycle scenarios, Regenerate SKILL.md]
- **Shadow paths:** [Install (any platform), Update over an old install, Update with a modified cut file]
- **Business rules:** [Rule 3 (ship filters stay identical), Rule 4 (dev-only and stale handling), Rule 9 (no dangling reference), Rule 10 (never run install/update against the Writ repo), Rule 11 (every story leaves the tree green)]
- **Experience:** [State Catalog: Fresh install any platform, Update old unmodified copies present, Update a copy edited locally, Re-install with install.sh over an old project, Writ source repo]
- **Technical:** technical-spec.md → ## Current State → ### Recommended-delivery staging inventory; ## Story 4 Design
