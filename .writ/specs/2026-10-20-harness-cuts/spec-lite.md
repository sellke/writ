# Harness Cuts (Lite)

> Source: .writ/specs/2026-10-20-harness-cuts/spec.md
> Purpose: Efficient AI context for implementation

## For Coding Agents

**Deliverable:** Writ stops shipping and maintaining the lean siblings, the ADR-025 no-op emit lines, the dormant recommended-delivery staging files in user projects, and a `/ship` description that says "merged PR".

**Implementation Approach:**
- Order: S1 deletes the five `commands/*.lean.md` files and their install/update skip logic; S2 removes the lean code paths in `scripts/`; S3 and S4 follow S2. Deleting files first keeps every tree green.
- Tests first. For a deletion, the failing test is the guard grep, an absence assert, or an inverted eval scenario.
- Ship filter: `is_shippable_script` stays byte-identical in `install.sh`, `update.sh`, and `unlink.sh`. New `is_shippable_writ_doc` (install, update) rejects `recommended-delivery-state-format.md`.
- `update.sh` `detect_stale_files`: lean arm goes (absent upstream is already stale); add a filter-rejected `.writ` arm beside the `scripts/` arm.
- `story-context.py` keeps `--state-dir` as a hidden no-op. `pipeline-baseline.py run --lean` goes; `validate` still accepts legacy `harness_lean`.

**Files in Scope:**
- `commands/*.lean.md` (delete), `install.sh`, `update.sh` (every `is_unshipped_lean_sibling` call, including the commands and agents loops in `write_copy_manifest`), README, mixed tests plus `test_manifest_shipped_baselines.sh`, `eval.sh` review-panel and product-check pins (S1)
- S1 also: AC-1.5 absence tests in `test_harness_cuts.py`; real `AC-2.2`/`AC-2.4` citations for `2026-10-20-claude-agent-generator` in `test_gen_claude_agents.py` and `test_jev_shadow_hooks.sh`, replacing the bare tokens the deleted `test_lean_preamble.py` carried (DEV-001 to DEV-004)
- `story-context.py`, `measure-invocation.py`, `eval-leanness.py`, `pipeline-baseline.py`, `eval.sh` `check_manifest`, `lean-decision.py` (delete) and lean tests (S2)
- S2 also: `scripts/tests/test_ci_workflow.py` gets AC-1.3/AC-1.4 citations for `2026-10-20-ci-and-update-integrity`, replacing the bare tokens the deleted `test_measure_invocation_lean.py` carried; the AC-1.4 test is a structural check (DEV-006)
- `commands/create-spec.md:773`, `commands/implement-story.md:192`, `eval.sh` `check_model_escalation`, `commands/ship.md` 3/17/19/25, `KNOWN_OVER_BUDGET` (S3)
- Ship filters, `skills/drift-triage/SKILL.md`, `agent-cli-contract.md`, `acceptance-criteria-ids.md`, `update-writ.md`, `gen-skill.sh` + `SKILL.md`, eval lifecycle scenarios (S4)
- S4 also: `test_harness_cuts.py` gains AC-4.4 prose tests and AC-4.5 structural tests on the eval source (AC-4.5's pass evidence is the `eval.sh` run); `test_manifest_shipped_baselines.sh`'s shipped-set builder applies `is_shippable_writ_doc` (DEV-007, DEV-008)
- New: `scripts/tests/test_harness_cuts.py`, `scripts/tests/test_install_update_harness_cuts.sh`

**Error Handling:**
- Kept modified file deleted on run 2 → dependency spec carries the baseline forward.
- Only a kept file differs → update exits before rewriting; fixtures also remove an unmodified file.
- `ship.md` grows → governor test fails; it sits at its exact overage (28,990 bytes).

**Integration Points:**
- Depends on `2026-10-20-ci-and-update-integrity` (kept stale files, every category).
- Never run install.sh/update.sh against the Writ repo; use temp directories.

See spec.md → ## Business Rules (Expanded) and sub-specs/technical-spec.md for the full inventory.

---

## For Review Agents

**Acceptance Criteria:**
1. No `*.lean.md` exists and install/update carry no lean skip logic `[AC-1.1]`
2. Install ships no lean file; update removes unmodified lean copies and keeps modified ones with a warning `[AC-1.2, AC-1.3, AC-1.4]`
3. Every non-lean test and eval pin still runs and passes `[AC-1.5]`
4. The guard grep is empty repo-wide outside the excluded paths; `lean-decision.py`, its ship-filter entry, and the lean-only tests are gone `[AC-2.1, AC-2.5]`
5. `story-context.py`, `pipeline-baseline.py`, `measure-invocation.py`, and `eval-leanness.py` behave as their flag-off paths did; legacy baselines validate `[AC-2.2, AC-2.3, AC-2.4]`
6. No `no-op until ADR-025` line or sink sentence in `commands/`; escalate-once and its pins unchanged `[AC-3.1, AC-3.2]`
7. `/ship` says it opens a PR, with no byte growth; recorded overages fall `[AC-3.3, AC-3.4]`
8. `recommend-state.py` and the state doc are dev-only: filters reject them, no platform installs them, update removes or keeps them per stale rules `[AC-4.1, AC-4.2, AC-4.3]`
9. No shipped file points at them; drift-triage loses its recommended branch `[AC-4.4]`
10. Reducer scenarios still run in the source repo; eval reports 0 findings `[AC-4.5]`

**Business Rules:**
- Historical records and the Complete `2026-10-12-agent-cli-contract` spec are not edited.
- Guard grep exclusions are exactly spec.md Business Rule 2.
- Dev-only: stays in source, eval runs it, never installed, stale on update.
- Escalate-once and both iteration sentences stay verbatim.
- Byte budgets only go down.

**Experience Design:**
- Entry: a user runs `install.sh` or `update.sh`; an agent reads `/create-spec`, `/implement-story`, `/ship`.
- Happy path: fewer files installed; old copies cleaned up.
- Moment of truth: an edited old copy survives every update with a warning.
- Feedback: `🗑  Removed: <path>` and the kept-stale warning.
- Error: a leftover reference fails the guard test naming file and line.

---

## For Testing Agents

**Success Criteria:**
1. `uv run --python 3.9 pytest` passes, including `test_harness_cuts.py`.
2. Every `scripts/tests/test_*.sh` passes, including `test_install_update_harness_cuts.sh`.
3. `bash scripts/eval.sh` (outside the sandbox) reports 0 findings.

**Shadow Paths to Verify:**
- **Happy path:** fresh install on claude, cursor, codex has none of the cut files.
- **Nil input:** a cut file with no manifest line is left alone by update.
- **Empty input:** a manifest listing none of the cut files → update removes nothing.
- **Upstream error:** `WRIT_REPO` clone fails → update exits with today's error, removes nothing.

**Edge Cases:**
- Modified copy → kept byte for byte on two consecutive runs, warned each time.
- `update.sh --dry-run` → lists stale files, writes nothing.
- `--state-dir` passed to `story-context.py` → accepted, no file written.

**Test Strategy:**
- Install/update tests use committed source copies in temp dirs, never the Writ repo.
- Absence tests: guard grep, absence asserts, inverted eval lifecycle scenarios.
