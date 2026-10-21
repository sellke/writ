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
