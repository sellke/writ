# Story 4: Consumer Wiring and Ordered-Commit Integration

> **Status:** Completed ✅ (2026-10-29)
> **Commit:** cbf054a39d129314cc7bf6892ab87a0be94ea7cf
> **Priority:** High
> **Dependencies:** Story 3

## User Story

**As a** developer fixing a bug through `/prototype` or `/implement-story` **I want to** have both consumers reach the repro-first bug path and re-check the commit order after integration **So that** the failing repro lands before the fix in my checkout, and a broken order shows up in the run's report instead of passing quietly.

## Acceptance Criteria

> **AC IDs assigned through:** AC-4.5

- [x] Given `commands/prototype.md` Step 3, when it is read, then principle 1 names the bug path in `skills/tdd-cycle/SKILL.md`, and a `**Bug path:**` line records the base from `git rev-parse HEAD`, re-runs `python3 scripts/repro-order.py check --repo . --base <that SHA>` after integration, puts the output and the failing-then-passing output in the Step 5 summary; the line fires only when the report's `### Repro` block names commits, so a `Repro: off` report never triggers it; Step 2.5 is byte-identical to its state before this story `[AC-4.1]`
- [x] Given `commands/implement-story.md` Gate 1, when it is read, then a `**Bug path:**` line records the base, re-runs the check after integration, prints a `repro-order:` line in the Step 4 report, maps `fail` to `⚠️ DEGRADED` with its reason lines, lets `unverifiable` print and continue without DEGRADED, and fires only when the report's `### Repro` block names commits (a `Repro: off` report never triggers it); Gates 0, 2.5, and 3 and the `gates:` frontmatter (`gate1_coding: prose-only`) are unchanged `[AC-4.2]`
- [x] Given `skills/subagent-worktree-integration/SKILL.md`, when step 3 ends, then an "Ordered commits" paragraph says to carry commits with `git cherry-pick` oldest first instead of copying files, and says that on a conflict the orchestrator runs `git cherry-pick --abort`, copies the files, and reports that the order was lost `[AC-4.3]`
- [x] Given `scripts/tests/test_repro_first_wiring.py`, when any one Removal Inventory row's text or file is deleted from the repo, then at least one test in that module fails and names the row; every text row in `spec.md` → `## Removal Inventory` is pinned, and the generated-trees row is covered by `python3 scripts/gen-platform-trees.py --check` `[AC-4.4]`
- [x] Given the finished change, when the gates run, then `python3 scripts/gen-platform-trees.py --check` passes, `uv run --python 3.9 pytest` passes, the bash test loop prints no `FAIL` line, and `bash scripts/eval.sh` reports zero findings `[AC-4.5]`

## Implementation Tasks

- [x] 4.1 Extend `scripts/tests/test_repro_first_wiring.py` with text checks for the two `**Bug path:**` lines, the fires-only-on-named-commits condition, the ordered-commits paragraph, and one pin per Removal Inventory row. Create the module if Story 2 has not. Run it and confirm the new checks fail before any command or skill edit `[AC-4.1, AC-4.2, AC-4.3, AC-4.4]`
- [x] 4.2 Edit `commands/prototype.md` Step 3: replace principle 1's line with the bug-path sentence, and add the `**Bug path:**` line after the integration paragraph. Do not edit Step 2.5 or the spawn text `[AC-4.1]`
- [x] 4.3 Edit `commands/implement-story.md` Gate 1: add the `**Bug path:**` line after `**Report:**`. Leave the Gate 1 `**On STATUS: BLOCKED**` handling and the `gates:` frontmatter as they are `[AC-4.2]`
- [x] 4.4 Add the "Ordered commits" paragraph at the end of step 3 in `skills/subagent-worktree-integration/SKILL.md`. Run `bash scripts/lint-skill.sh skills/subagent-worktree-integration/SKILL.md` `[AC-4.3]`
- [x] 4.5 Run `python3 scripts/gen-platform-trees.py`, then `python3 scripts/gen-platform-trees.py --check`. Do not hand-edit `claude-code/`, `cursor/`, `codex/`, or plugin trees `[AC-4.5]`
- [x] 4.6 Run `python3 scripts/verdict-provenance.py check --command commands/implement-story.md` and the wiring module. Confirm the Gate 1 line did not make a gate name both a script and prose-only, and that every Removal Inventory pin passes `[AC-4.2, AC-4.4]`
- [x] 4.7 Verify: `uv run --python 3.9 pytest`, the bash test loop, and `bash scripts/eval.sh` outside any sandbox. Review `git diff` and confirm the only edits are `commands/prototype.md` Step 3, `commands/implement-story.md` Gate 1, the integration skill's step 3 paragraph, the wiring module, and generated trees `[AC-4.1, AC-4.2, AC-4.3, AC-4.4, AC-4.5]`

## Definition of Done

- [x] All tasks completed
- [x] All acceptance criteria met
- [x] Tests passing
- [x] Code reviewed
- [x] Documentation updated

## Notes

- **Cherry-pick conflicts.** A worktree branched from a stale base can conflict on cherry-pick. The paragraph says to abort and copy files. The re-run check then fails `no_repro_commit`, so the loss shows in the report. Test a conflict case in the wiring checks by text only; the behavior itself belongs to the skill's instructions.
- **Sibling specs on the same files.** The design-divergence spec owns `/prototype` Step 2.5 and Gate 0. The Gate 2.5 and Gate 3 spec owns those sections of `/implement-story`. Both edit the same command files. Keep this story's diff to the lines named above, and rebase on any sibling commit that lands first.
- **DEGRADED stops the spec.** A post-integration `fail` marks the story `⚠️ DEGRADED`, and a DEGRADED story can stop `/implement-spec`. A false `fail` from `repro-order.py` therefore blocks a whole spec run. Run the check against a real bug-fix history before wiring it into the consumers.
- **Pins for earlier stories.** The wiring module pins Removal Inventory rows that Stories 2 and 3 create. Those rows must exist before task 4.6 can pass.
- **Generated trees.** Command and skill edits reach the platform trees only through `scripts/gen-platform-trees.py`. A hand edit in a generated tree fails `--check`.

## Context for Agents

- **Error map rows:** `technical-spec.md → ## Error & Rescue Map → Integration` (cherry-pick conflict; abort, copy, report `no_repro_commit`)
- **Shadow paths:** `technical-spec.md → ## Shadow Paths` (Happy path: repro then fix, check `pass`, orchestrator re-run `pass`)
- **Business rules:** `spec.md → ## Business Rules (Expanded)` (Rule 9 switch-off: neither consumer runs the check; Rule 10 enforcement differs by consumer; Rule 11 the path adds no spawn)
- **Experience:** `spec.md → ## Experience Design → ### State Catalog` (Check fails after integration; Merge commit in the range; Cherry-pick conflict at integration)
- **Consumer lines:** `technical-spec.md → ## Consumer Lines` (the three replacement or new lines for `/prototype` Step 3, `/implement-story` Gate 1, and the integration skill)
- **Removal Inventory:** `spec.md → ## Removal Inventory` (every row; the wiring module pins each)
- **Tests:** `technical-spec.md → ## Tests → ### scripts/tests/test_repro_first_wiring.py`
- **Verdict check:** `scripts/verdict-provenance.py` (`entry_both_sources`) and `agents/coding-agent.md` are out of scope for this story

## What Was Built

**Implementation Date:** 2026-10-29

### Files Created

[None created]

### Files Modified

- **`commands/prototype.md`** (Step 3 only; 18,034 → 18,616 bytes) — principle 1: "A bug fix follows the bug path in `skills/tdd-cycle/SKILL.md`: a failing repro committed before the fix." New `**Bug path:**` line after the integration paragraph: record `git rev-parse HEAD` before spawning; when the `### Repro` block names commits, bring them in with `git cherry-pick`, oldest first, not through `git apply`; run `python3 scripts/repro-order.py check --repo . --base <that SHA>`; output and failing-then-passing output go in the Step 5 summary; `fail` → "Prototype Complete (with issues)".
- **`commands/implement-story.md`** (Gate 1 only; 40,229 → 40,677 bytes) — `**Bug path:**` line after `**Report:**`: base recorded before the story's first Gate 1 spawn and reused on recodes; check runs after integration only when the block names commits; first line printed as `repro-order:` in the Step 4 report; `fail` → `⚠️ DEGRADED` with its `reason:` lines; `unverifiable`, or exit 2 with its stderr cause, prints and continues. `gate1_coding` stays `prose-only`.
- **`skills/subagent-worktree-integration/SKILL.md`** (4,888 → 5,258 bytes) — "Ordered commits" paragraph at the end of step 3: `git cherry-pick <sha>...`, oldest first, instead of copying files; on a conflict `git cherry-pick --abort`, copy the files, and say the order was lost.
- **`scripts/tests/test_repro_first_wiring.py`** — 18 Story 4 cases (37 in the module): both Bug path lines (position, clauses, fires only on named commits, only in their section), `gate1_coding` prose-only plus `verdict-provenance.py check`, the ordered-commits paragraph and its lint, and `test_removal_inventory_row[...]` with one case per Removal Inventory row naming the row on failure; AC-3.5 / AC-4.5 citations.
- **`scripts/tests/test_governor_enforcement.py`** — `KNOWN_OVER_BUDGET["commands/implement-story.md"]` 15269 → 15717, dated.
- **`scripts/tests/test_review_route_rigor.py`** — `IMPLEMENT_STORY_CAP` 40234 → 40682 (+448, file + 5), dated.
- Regenerated: `cursor/plugin/` and `plugins/writ/` copies of `commands/prototype.md`, `commands/implement-story.md`, and the integration skill.

### Implementation Decisions

1. **Cherry-pick in the `/prototype` line** — Step 3's `git apply` sentence stays (pinned by `test_prototype_worktree_integration.py`); the Bug path line overrides it for named commits (DEV-012).
2. **Story-start base** — reused across recodes so a Gate 3 or Gate 4.5 recode cannot produce a false DEGRADED; exit 2 routed to print-and-continue (DEV-013).
3. **Sibling sections untouched** — `/prototype` Step 2.5 and `/implement-story` Gate 0, 2.5, 3, Pipeline, Step 4, frontmatter, and the Gate 1 BLOCKED line are byte-identical to the base (checked by script).

### Test Results

**Verification:** recorded run `uv run --python 3.9 pytest scripts/tests/test_repro_first_wiring.py scripts/tests/test_governor_enforcement.py scripts/tests/test_review_route_rigor.py scripts/tests/test_design_divergence_wiring.py scripts/tests/test_prototype_worktree_integration.py -q` → 214 passed; full `uv run --python 3.9 pytest -q` → 3518 passed, 3 skipped; bash loop → 51/51; `bash scripts/eval.sh` → 0 findings; `gen-platform-trees.py --check` → pass; `verdict-provenance.py check --command commands/implement-story.md` → pass (prose-only 1, cap 1); `lint-skill.sh` on both skills → pass. Mutation check (reviewer): 18 deletions across all 9 inventory rows each fail a test naming the row.
- ✅ test-integrity authenticity: pass
- coverage: no new source files in this story

### Review Outcome

**Result:** PASS

- **Iteration count:** 2 iteration(s) (cycle 1 FAIL: `git apply` integration in `/prototype`, per-spawn base in Gate 1; both fixed by recode)
- **Drift:** Small
- **Security:** Clean
- **Boundary Compliance:** product edits in owned files; generated copies and two dated byte-cap bumps justified
- **gate3-route:** review-agent (outside_boundary plugins/writ/commands/implement-story.md; outside_boundary plugins/writ/commands/prototype.md; outside_boundary plugins/writ/skills/subagent-worktree-integration/SKILL.md; outside_boundary scripts/tests/test_governor_enforcement.py; outside_boundary scripts/tests/test_review_route_rigor.py)
- **reviewer-filters:** on
- **gate0-divergence:** skip (route evaluator-agent)
- **review-panel:** skipped — platform cannot spawn other vendors
- **review-override check:** pass (no blocking helper finding)
- **safety-fact:** cycle 1 traced, holds no (per-spawn base); cycle 2 traced (claimed traced) — the story-start base keeps the repro in range on recodes
- **arch-lint:** none — see .writ/docs/architecture-lint.md
- **app-verify:** unverifiable (no_recipe)
- **docs-check:** unverifiable (no public exports in the changed set)

### Deviations from Spec

- **[DEV-010] Two whole-file byte caps raised by this story's growth** — Severity: Small — Resolution: Auto-amended
- **[DEV-011] AC-3.5 and AC-4.5 traced by citations in the wiring module** — Severity: Small — Resolution: Auto-amended
- **[DEV-012] `/prototype` Bug path line integrates by cherry-pick** — Severity: Small — Resolution: Auto-amended
- **[DEV-013] `/implement-story` Bug path line keeps the base across recodes and routes exit 2** — Severity: Small — Resolution: Auto-amended
