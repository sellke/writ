# Story 4: /refresh-command Execution-Failure and Used-Skill Criteria

> **Status:** Completed ✅ (2026-10-29)
> **Commit:** 87493aed118ed060c26efa0fdb06ee69eb3ffd87
> **Priority:** High
> **Dependencies:** None

## User Story

**As a** maintainer running `/refresh-command` on a Writ command
**I want to** have the command reject a signal its guidance already covers, and edit a skill only when the cited transcript read that skill
**So that** amendments land only where the agent failed to follow existing guidance or where a skill actually shaped the run, and the command file and its skills improve from evidence.

## Acceptance Criteria

> **AC IDs assigned through:** AC-4.5

- [x] Given `commands/refresh-command.md` § Phase 3, when its text is read, then it contains the bold labels `**Covered already?**` and `**Skill targets**`, and it states that a covered signal is logged under reason `execution failure` with the covering section, and that a skill target the transcript does not show in use is rejected with `skill not used` `[AC-4.1]`
- [x] Given `commands/refresh-command.md` § Step 4.1a, when its text is read, then it contains `bash scripts/lint-skill.sh skills/<name>/SKILL.md` for skill amendments and states that line 1 `fail` rejects with `eval failed`, and given § Step 4.2, then its rejected examples contain all four tokens `no evidence`, `eval failed`, `execution failure`, and `skill not used` `[AC-4.2]`
- [x] Given the frontmatter of `commands/refresh-command.md`, when `exit_criteria` is read, then it names all four tokens, the `description` value equals its value before the edit, and the `## Completion` section contains the sentence `improves one command file, and the skills that run read, from evidence.` `[AC-4.3]`
- [x] Given `scripts/eval-refresh-evidence.py`, when `python3 scripts/eval-refresh-evidence.py` runs, then it prints `PASS` for `rejected-execution-failure-is-valid-record`, `rejected-skill-not-used-is-valid-record`, and `rejected-unknown-token-fails`, and its missing-token message lists all four tokens `[AC-4.4]`
- [x] Given `commands/refresh-command.md` and `scripts/eval.sh`, when `bash scripts/eval.sh --check=refresh-evidence` runs, then it exits 0, every literal `check_refresh_evidence` pins still matches, and `wc -c commands/refresh-command.md` reports fewer than 24,960 bytes `[AC-4.5]`

## Implementation Tasks

- [x] 4.1 Write `scripts/tests/test_refresh_command_criteria.py` before any edit. Pin the labels, the four tokens, `lint-skill.sh` in Step 4.1a, the frontmatter `description`, the Completion sentence, and the byte ceiling. Add a test that runs `python3 scripts/eval-refresh-evidence.py` and asserts the three scenario names print `PASS`. Run the file and confirm it fails on the unedited command `[AC-4.1, AC-4.2, AC-4.3, AC-4.4, AC-4.5]`
- [x] 4.2 Edit `commands/refresh-command.md` § Phase 3. Add `**Covered already?**` before the five required fields, with the search of the command file and each `skills/<name>/SKILL.md` it names. Add `**Skill targets**` with the rule from spec Business Rule 14. Extend the Evidence block's "Affected section" format to name a skill section `[AC-4.1]`
- [x] 4.3 Edit `commands/refresh-command.md` § Step 4.1a (skill lint, line 1 `fail` rejects with `eval failed`), § Step 4.2 (four tokens in the rejected examples; "Target file" lists the command and any skill), and the frontmatter `exit_criteria`. Edit § Completion and the terminal constraint. Leave `description` unchanged `[AC-4.2, AC-4.3]`
- [x] 4.4 Edit `scripts/eval-refresh-evidence.py`: `_REASON_RE` accepts the four tokens, the missing-token message lists them, and the three scenarios emit PASS/FAIL TSV rows. Edit `.writ/docs/refresh-log-format.md` § Rejection reasons (two rows) and the field reference's Rejected and Target file rows. Keep the four literals `check_refresh_evidence` pins `[AC-4.4]`
- [x] 4.5 Run `python3 scripts/gen-platform-trees.py` to regenerate the trees. Never hand-edit generated copies. Run `python3 scripts/gen-platform-trees.py --check` and confirm `pass` `[AC-4.5]`
- [x] 4.6 Verify the targeted gates. Run `bash scripts/eval.sh --check=refresh-evidence` and `uv run --python 3.9 pytest scripts/tests/test_refresh_command_criteria.py`. Confirm all five criteria, the byte ceiling, and the pinned literals `[AC-4.1, AC-4.2, AC-4.3, AC-4.4, AC-4.5]`
- [x] 4.7 Verify the full suite. Run `uv run --python 3.9 pytest`, `for t in scripts/tests/test_*.sh; do bash "$t" || echo "FAIL $t"; done`, and `bash scripts/eval.sh` outside any sandbox. Confirm no failures and no findings `[AC-4.5]`

## Definition of Done

- [x] All tasks completed
- [x] All acceptance criteria met
- [x] Tests passing
- [x] Code reviewed
- [x] Documentation updated

## Notes

- **Byte budget.** `commands/refresh-command.md` is 21,586 bytes today. `COMMAND_BYTE_BUDGET` in `scripts/eval-leanness.py` is 24,960 bytes and is reported, not blocking. Keep this story's additions under about 2,500 bytes, so the file stays under the ceiling after Story 3 and any other Phase 15 edit.
- **Pinned literals.** `check_refresh_evidence` in `scripts/eval.sh` pins `**Evidence:**`, `**Rejected:**`, `no evidence`, `eval failed`, `verbatim private transcript bodies`, the Tier 2 allowlist sentence, and `structural only — not an LLM-as-judge`. Keep each one verbatim. Do not edit `scripts/eval.sh`. The new tokens run through the existing scenario loop in `scripts/eval-refresh-evidence.py`.
- **Prose.** Added text follows `skills/plain-prose/SKILL.md`. Do not link to `.writ/research/`, `.writ/decision-records/`, or archived specs from the command (`check_shipped_refs`).
- **Logging precedent.** The 2026-10-12 `/retro` entry in `.writ/refresh-log.md` (heading `(rewrite, human override)`) records an unevidenced change with an `**Override:**` line. This story does not add an override path. A `no evidence` or `execution failure` rejection is logged, not applied.
- **Skill edits.** A skill target is allowed only when the cited transcript is readable here and shows a read of `skills/<name>/SKILL.md` or an invocation of that skill. An unreadable transcript cannot show use, so the rule rejects it with `skill not used`. The two rules are pinned in text only. The eval script checks the reason tokens, not the transcript.
- **Scope.** Story 4 touches only `commands/refresh-command.md`, `scripts/eval-refresh-evidence.py`, `.writ/docs/refresh-log-format.md`, the new test file, and regenerated trees. It does not depend on Stories 1 to 3 and can run beside any of them.

## Context for Agents

- **Error map rows:** [/refresh-command skill target (transcript not readable; lint-skill.sh line 1 fail)] from `sub-specs/technical-spec.md → ## Error & Rescue Map`
- **Shadow paths:** [/refresh-command signal (signal already covered; skill target with unreadable transcript)] from `sub-specs/technical-spec.md → ## Shadow Paths`
- **Business rules:** [13 Refresh execution failure (covered means already stated in the command or a skill it reads), 14 Refresh skill targets (command path check plus transcript read check), 15 Reason tokens (exactly four tokens)] from `spec.md → ## Business Rules (Expanded)`
- **Experience:** [Signal already covered (Rejected list, covering section named), Skill target not used (rejection names skill and transcript)] from `spec.md → ## Experience Design → ### State Catalog`
- **Edit map:** `sub-specs/technical-spec.md → ## commands/refresh-command.md changes (by section)` and `## scripts/eval-refresh-evidence.py and .writ/docs/refresh-log-format.md`
- **Test pattern:** `sub-specs/technical-spec.md → ## Tests` (third row) and `scripts/tests/test_prompting_guide.py` for the read-as-text style
- **Current gate:** `commands/refresh-command.md → ## Phase 4` (Step 4.0 evidence gate, Step 4.1a eval gate) for the order of checks

## What Was Built

**Implementation Date:** 2026-10-29

### Files Created

- **`scripts/tests/test_refresh_command_criteria.py`** (45 tests) — pins the Phase 3 labels and rules, the Step 4.1a skill lint, the Step 4.2 rejected examples, the unchanged `description`, the four tokens in `exit_criteria` and Completion, the Completion sentence, the byte ceiling, every `check_refresh_evidence` literal, and runs `scripts/eval-refresh-evidence.py` for the three new PASS rows.

### Files Modified

- **`commands/refresh-command.md`** (21,586 → 23,187 bytes; budget 24,960) — Phase 3 gains `**Covered already?**` (a covered signal is logged under `**Rejected:**` as `execution failure` with the covering section) and `**Skill targets**` (a skill amendment needs the path in the command and a readable transcript that read or invoked the skill, else `skill not used`). The Evidence block may name `skills/<name>/SKILL.md → "<section>"`. Step 4.1a lints skill amendments with `bash scripts/lint-skill.sh skills/<name>/SKILL.md`; line 1 `fail` rejects with `eval failed`. Step 4.2, `exit_criteria`, and Completion carry all four tokens; the terminal constraint reads "improves one command file, and the skills that run read, from evidence." `description` unchanged.
- **`scripts/eval-refresh-evidence.py`** — `REASON_TOKENS` holds the four tokens and builds `_REASON_RE`; the missing-token message lists them; new scenarios `rejected-execution-failure-is-valid-record`, `rejected-skill-not-used-is-valid-record`, `rejected-unknown-token-fails`.
- **`.writ/docs/refresh-log-format.md`** — two Rejection-reasons rows, the Rejected and Target file field rows, an overview bullet, the `eval failed` row naming `lint-skill.sh`, and a skill form of the Affected section.
- Generated: `cursor/plugin/commands/refresh-command.md`, `plugins/writ/commands/refresh-command.md`.

### Implementation Decisions

1. **Skills named in three more places** (Step 4.1, Cross-References, log-format overview and rows) so the command and doc agree with contract item 8 (DEV-006).
2. **Skill lint runs with the diff applied** and restores the file on `fail` (DEV-007).
3. **A recurring covered signal points to `/retro`**, as the State Catalog says (DEV-008).
4. **`outcome` frontmatter left unchanged** — the spec names only `exit_criteria` and `description`.

### Test Results

**Verification:** `uv run --python 3.9 pytest scripts/tests/test_refresh_command_criteria.py scripts/tests/test_gen_claude_agents.py scripts/tests/test_plugin_distribution.py -q` → 214 passed; `python3 scripts/eval-refresh-evidence.py` → 25 PASS, 0 FAIL; full `uv run --python 3.9 pytest -q` → 3630 passed, 3 skipped; bash loop → 51/51, no FAIL; `bash scripts/eval.sh` → Findings: 0; `gen-platform-trees.py --check` → pass.
- ✅ test-integrity authenticity: pass
- coverage: unverifiable (`no_coverage_report`; markdown pins and a subprocess run)

### Review Outcome

**Result:** PASS

- **Iteration count:** 1 iteration(s)
- **Drift:** Small
- **Security:** Clean (regex alternation over fixture strings; no new input surface)
- **Boundary Compliance:** four owned files; two generated copies justified
- **gate3-route:** review-agent (outside_boundary cursor/plugin/commands/refresh-command.md; outside_boundary plugins/writ/commands/refresh-command.md)
- **reviewer-filters:** on
- **gate0-divergence:** skip (route evaluator-agent)
- **review-panel:** skipped — platform cannot spawn other vendors
- **review-override check:** unverifiable (test-integrity coverage: no_coverage_report)
- **safety-fact:** traced (claimed tested) — every literal `check_refresh_evidence` pins is still present
- **jev shadow:** unverifiable (no_evaluator_ids) — advisory only
- **arch-lint:** none — see .writ/docs/architecture-lint.md
- **build-smoke:** unverifiable (unsupported_stack)
- **app-verify:** unverifiable (no_recipe)
- **docs-check:** unverifiable (no public exports in the changed set)

### Deviations from Spec

- **[DEV-006] Three more places name skills so the command and log format stay consistent** — Severity: Small — Resolution: Auto-amended
- **[DEV-007] Step 4.1a lints the skill with the diff applied and restores it on `fail`** — Severity: Small — Resolution: Auto-amended
- **[DEV-008] A covered signal suggests `/retro` when it recurs** — Severity: Small — Resolution: Auto-amended
