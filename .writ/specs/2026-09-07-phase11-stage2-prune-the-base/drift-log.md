# Drift Log — Phase 11 Stage 2a: Prune the Base

> Parent: [`spec.md`](spec.md)

Deviations recorded during implementation. Per-story detail lives in each
story's `## What Was Built` → *Deviations from Spec*; this file carries the
spec-level entries. Append-only; `spec.md` is never auto-modified. Story 4
numbers from DEV-101 (it ran in parallel with Story 1, which numbers from
DEV-001).

| ID | Story | Severity | Title |
|---|---|---|---|
| DEV-001 | 1 | Small | `check_pruned_base()` reads `WRIT_PRUNE_BASE_COMMIT` to override the `cf84742` pin (fixture trees only) |
| DEV-002 | 1 | Medium | Whitespace-only lines are exempt from ledger accounting |
| DEV-003 | 1 | Small | `ledger_text_reappeared` requires the text to be absent from the file's net removals, not merely present at HEAD |
| DEV-004 | 1 | Small | `check`/`measure` exit 2 when a base file is missing; `check_pruned_base()` notes and skips a tree with no shared base |
| DEV-101 | 4 | Medium | `KNOWN_OVER_BUDGET` pin for `implement-story.md` raised 4414 → 5381 in `test_governor_enforcement.py` |
| DEV-102 | 4 | Small | `agents/visual-qa-agent.md` still names the 85/70 match thresholds the command body dropped |

---

## DEV-001 — `WRIT_PRUNE_BASE_COMMIT` override in `check_pruned_base()`

**Severity:** Small · **Story:** 1 · **Found:** 2026-09-07, Gate 0 arch check

Technical-spec §1 says `eval.sh` decides only `--cap-blocking` (from the ledger marker). `test_eval_pruned_base.sh` builds a fixture git repo whose history cannot contain `cf84742`, so the check needs a way to point at the fixture's own base commit. `check_pruned_base()` passes `--base-commit "${WRIT_PRUNE_BASE_COMMIT:-cf84742}"`. Unset in normal runs, so the pin is unchanged. `spec-lite.md` amended.

## DEV-002 — Whitespace-only lines exempt from ledger accounting

**Severity:** Medium · **Story:** 1 · **Found:** 2026-09-07, Gate 0 arch check; confirmed at Gate 3 review

**Spec said:** every removed line needs a ledger row with identical text (Business Rule 3, technical-spec §1). **Implementation did:** `net_removals()` drops whitespace-only texts after the move cancellation, so a removed blank line needs no row and produces no `removed_not_in_ledger`; `run_check()` also skips blank-text rows in the reappeared scan. **Why it matters:** under the literal rule the check is unsatisfiable for Stories 2 and 3 — a section removed whole takes its blank lines with it, each would need a row with empty text, and every such row would immediately read as `ledger_text_reappeared` because other blank lines remain in the file. A blank line carries no instruction to account for. Recorded in ADR-026 § Consequences (negative) as a small hole in "every line". **Resolution:** ⚠️ flagged; pipeline PASS. `spec.md` unchanged; a maintainer who disagrees removes the `text.strip()` filter in `net_removals()` and the matching guard in `run_check()`, and the fixture `test_blank_line_removal_needs_no_row` flips.

## DEV-003 — Reappeared means present *and* not a net removal

**Severity:** Small · **Story:** 1 · **Found:** 2026-09-07, Gate 0 arch check

Technical-spec §1 defines `ledger_text_reappeared` as "a ledger row's text is present as a whole line in the same base file at HEAD". With one of two identical lines removed (a table separator, a shared sentence), the row is honest but the text is still present. The implementation flags a row only when its text is present and not among that file's net removals, so the duplicate case is clean while a real remove-then-re-add (net diff empty, text present) still fires. Fixture `test_same_file_duplicate_one_copy_removed_is_not_reappeared` covers it. `spec-lite.md` amended.

## DEV-004 — Missing base file is a usage error; no-base tree is a note

**Severity:** Small · **Story:** 1 · **Found:** 2026-09-07, Gate 3 review

The spec is silent on a missing `system-instructions.md` or `commands/_preamble.md`. `check` and `measure` refuse with exit 2 (`<command>: error: <file> is missing under --repo …`), matching the usage-error class rather than fabricating a zero-byte file. `check_pruned_base()` first tests for both files and emits one note and returns when either is absent, mirroring `check_pipeline_baseline()`'s "installed projects have none" note. `spec-lite.md` amended.

---

## DEV-101 — `KNOWN_OVER_BUDGET` pin raised for `implement-story.md`

**Severity:** Medium · **Story:** 4 · **Found:** 2026-09-07, Gate 4 full-suite run

**Spec said:** the story touches `commands/implement-story.md` frontmatter, `scripts/`, and `eval.sh`; the Risks note foresaw that the `gates:` block grows the command file and said the growth "must not be treated as a pruning target". **Implementation did:** `scripts/tests/test_governor_enforcement.py::ComplianceGateTests` pins each over-budget command's overage and fails on growth; the block plus the Gate 4.5 sentence grew `implement-story.md` 29,374 → 30,341 bytes (+967), so the pin was raised 4414 → 5381 with a dated comment in the file's own convention (the 2026-09-04 and 2026-09-06 updates did the same). **Why it matters:** a test file outside the story's file list was edited; the leanness warning for the file already fired before this story and still does. **Resolution:** ⚠️ flagged; pipeline PASS. `spec.md` unchanged.

## DEV-102 — `agents/visual-qa-agent.md` still carries the thresholds

**Severity:** Small · **Story:** 4 · **Found:** 2026-09-07, Gate 0 review. Task 4.5 scopes the percentage removal to the command body's `#### Gate 4.5` section, which now names no percentage. `agents/visual-qa-agent.md` (outcome, exit criterion, and the PASS / SOFT PASS / FAIL list at lines 132–134) still says 85 / 70. Left as authored — the agent file is outside this story's boundary and the mechanization spec that gives Gate 4.5 a real diff owns the rewrite. `spec-lite.md` amended with one parenthetical.
