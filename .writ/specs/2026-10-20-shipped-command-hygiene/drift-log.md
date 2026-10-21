# Drift Log

> Spec: .writ/specs/2026-10-20-shipped-command-hygiene/
> Created: 2026-10-21
> ⚠️ Append-only — do not modify existing entries.

---

## Story 1: Strip Internal References and Add `shipped-refs` — Drift Report

> Run: 2026-10-21
> Overall Drift: Small

### Deviations

#### [DEV-001] `shipped-refs` scans every `commands/*.md`, including any `*.lean.md`
- **Severity:** Small
- **Spec said:** Business Rule 1, technical-spec.md → Rules, and the Story 1 Notes say the helper scans every `commands/*.md` except `*.lean.md`, because lean files never ship.
- **Implementation did:** `scripts/eval-shipped-refs.py` scans every top-level `commands/*.md` with no name skipped.
- **Reason:** `2026-10-20-harness-cuts` merged after this spec was written. install.sh now ships every `commands/*.md`, so the premise of the skip is false, and its guard `test_harness_cuts.py::test_ac_1_1_ac_2_1_guard_grep_is_empty_repo_wide` fails on any `\.lean\.md` text under `scripts/`. No lean file exists, so the output on the tree is the same.
- **Resolution:** Auto-amended
- **Spec amendment:** spec-lite.md → For Review Agents → Business Rules: "Shipped = every `commands/*.md`, including `_preamble.md`; no name is skipped (install.sh ships them all after `2026-10-20-harness-cuts`)."

#### [DEV-002] No `commands/*.md` under `--root` is a run error, not a PASS
- **Severity:** Small
- **Spec said:** spec-lite.md → For Testing Agents → Shadow Paths: "Empty input: `commands/` empty in a temp root → PASS, self-tests still run."
- **Implementation did:** The self-test rows still print PASS, then the helper exits 2 ("no shipped command files"), and `check_shipped_refs` records a run error (eval exit 2). `test_missing_commands_directory_is_a_run_error_not_a_pass` pins it.
- **Reason:** The contract and technical-spec.md do not cover this case. A vacuous PASS on a wrong `--root` or a broken checkout would hide a real problem; this matches the State Catalog's "helper missing → run error".
- **Resolution:** Auto-amended
- **Spec amendment:** spec-lite.md Shadow Paths: "Empty input: no `commands/*.md` under `--root` → self-tests print, then the helper exits 2 and eval records a run error."

#### [DEV-003] Story 1 repins `KNOWN_OVER_BUDGET` for five commands
- **Severity:** Small
- **Spec said:** technical-spec.md → Files in Scope assigns `scripts/tests/test_governor_enforcement.py` to Story 3 only.
- **Implementation did:** Repinned five entries downward to their exact measured overage: create-spec 28738 → 28652, implement-phase 10361 → 9921, release 7655 → 7571, ship 4023 → 3947, implement-story 11533 → 11266.
- **Reason:** `test_the_byte_cap_is_the_half_that_does_not_comply_and_is_not_blocking` asserts `total_overage == sum(KNOWN_OVER_BUDGET.values())`, so the reference removals that shrank these files force a repin in the same change. Story 3 now starts from 28652; Business Rule 11 still holds.
- **Resolution:** Auto-amended
- **Spec amendment:** spec-lite.md → Files in Scope names `scripts/tests/test_governor_enforcement.py` for S1 (downward repins forced by the exact-sum assertion) as well as S3.

---

## Story 2: Pin Map and Conversions — Drift Report

> Run: 2026-10-21
> Overall Drift: Small

### Deviations

#### [DEV-004] Structure pins removed as duplicates of `eval-*.py` scenarios
- **Severity:** Small
- **Spec said:** The contract defines remove as "pins wording only; no behavior depends on it". technical-spec.md says `## Artifact Map` in `implement-story.md` "stays literal".
- **Implementation did:** Pin-map rows 130, 132, 135, and 136 (`Last audit note:`, `Required Artifacts`, `## Artifact Map`, `**Integrity:**`) are removed because a scenario that the same check function still runs (`eval-git-notes-audit.py`, `eval-artifact-integrity.py`) asserts the same text in the same file.
- **Reason:** Enforcement is unchanged and the `structure` category allows remove, but the reason is "enforced elsewhere", not "wording only". Rewording that text still needs an edit, now in the `eval-*.py` helper. The reviewer verified each duplicate and that no shipped script parses these strings.
- **Resolution:** Auto-amended
- **Spec amendment:** spec-lite.md → For Review Agents → Business Rules: "A `structure` pin whose exact text an `eval-*.py` scenario run by the same check also asserts on the same file may be removed as a duplicate; the reason names the scenario."

#### [DEV-005] `merge, never append` removed beyond the per-function guidance
- **Severity:** Small
- **Spec said:** technical-spec.md's guidance for `check_knowledge_consolidate` names only the retro nudge wording as a remove candidate.
- **Implementation did:** Also removed pin-map row 116, `merge, never append` in `commands/knowledge.md`, as `wording`.
- **Reason:** The guidance table says pin-map.md decides per row. The phrase is a design-principle sentence; `knowledge-consolidate.py` and its README keep their own pins on it, and the approval (`AskQuestion`) and no-commit pins on the command stay.
- **Resolution:** Auto-amended
- **Spec amendment:** None needed. The guidance table lists candidates, not an exhaustive set; the row's reason in pin-map.md records the decision.

#### [DEV-006] One pin instance maps to two structural rows
- **Severity:** Small
- **Spec said:** A converted pin becomes a `heading`, `frontmatter`, or `invocation` row in `scripts/eval-command-structure.py`.
- **Implementation did:** Pin-map row 74 (bare `scripts/phase-state.py` on `commands/implement-phase.md`) maps to two invocation rows, `scripts/phase-state.py create-lane` and `scripts/phase-state.py validate-result`. The invocation kind no longer accepts a path with no subcommand. The pin-map arithmetic still counts row 74 as one instance.
- **Reason:** Gate 3 iteration 1 found the path-only row passed on the `calibrated_against` note in the frontmatter, so it guarded nothing. Binding the lane-creation and merge-gate calls is stricter; counts are unaffected.
- **Resolution:** Auto-amended
- **Spec amendment:** spec-lite.md → For Coding Agents: "A convert row may map to more than one structural row when a bare-path pin is replaced by the specific calls the command must make."
