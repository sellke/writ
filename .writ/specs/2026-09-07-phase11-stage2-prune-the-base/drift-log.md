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
| DEV-005 | 2 | Medium | `MechanismRecordTests` pins in `test_governor_enforcement.py` follow the `required_skills:` text to `.writ/docs/skills.md` |
| DEV-006 | 2 | Medium | `check_recommendation_semantics` pins for the moved bullets read `.writ/docs/recommendation-semantics.md`; the `cursor/writ.mdc` pin reads the pointer line |
| DEV-007 | 2 | Small | `cursor/writ.mdc` took only the Prime Directive cut; its other sections still carry the pre-move text |
| DEV-008 | 2 | Small | `check_referenced_paths` scans `commands/*.md` only, so the base's pointer links are verified by hand, not by the check |
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

---

## DEV-005 — `MechanismRecordTests` pins follow the moved text

**Severity:** Medium · **Story:** 2 · **Found:** 2026-09-07, Gate 0 arch check; applied in commit `2b11f7d`

**Spec said:** Story 2 edits `system-instructions.md`, `.writ/docs/`, and the ledger. **Implementation did:** `scripts/tests/test_governor_enforcement.py::MechanismRecordTests` pinned four schema clauses, "no consumer", and the `2026-11-11` trigger in `system-instructions.md`; the `required_skills:` convention moved to `.writ/docs/skills.md`, so `CLAIM_FILES` and the clause test now read that file (a dated docstring records the move). **Why it matters:** a test outside the story's file list was edited; the pins still bite — the doc carries every clause verbatim. **Resolution:** ⚠️ flagged; pipeline PASS. `spec.md` unchanged.

## DEV-006 — `check_recommendation_semantics` pins retargeted

**Severity:** Medium · **Story:** 2 · **Found:** 2026-09-07, Gate 0 arch check; applied in commit `724e86a`

**Spec said:** the tutorial part of `### Recommendation Semantics` moves out, the rule sentence stays. **Implementation did:** `scripts/eval.sh` → `check_recommendation_semantics` required 16 literals in `system-instructions.md` covering every bullet of the section, so the move could not land without touching the check. The 13 pins for bullets 2–5 (evidence, select-or-pause, audit rationale, resume) now read `.writ/docs/recommendation-semantics.md`; the 3 pins for the labeling rule still read the base; the `cursor/writ.mdc` pin for the Story 2/3 boundary sentence now requires the pointer line instead (the mirror lost that sentence with the cut). A mutation run confirmed a changed literal in the doc still yields one finding. **Why it matters:** the governor now guarantees the text exists in a doc the model reads only on demand, not on every invocation — which is the intent of ADR-026, and `commands/_preamble.md` (User Challenge, Autonomy Gate Classes) still carries the select-or-pause boundary every command loads. **Resolution:** ⚠️ flagged; pipeline PASS. `spec.md` unchanged.

## DEV-007 — `cursor/writ.mdc` mirrors only the Prime Directive cut

**Severity:** Small · **Story:** 2 · **Found:** 2026-09-07, Gate 3 review

Before this story `cursor/writ.mdc` was `system-instructions.md` whole, behind a three-line frontmatter. Business Rule 8 and `check_prime_directive_sync` govern only the `## Prime Directive` block, so the Recommendation Semantics cut was mirrored (same commit) and the Model Tiers, Skills, and Startup Update Awareness moves were not: the Cursor rule still carries those sections in full (about 21,400 bytes against the base's 10,061). Left as authored — the spec scopes `writ.mdc` as the Prime Directive mirror, and re-syncing the whole file is a decision for Story 3 or the maintainer. `spec-lite.md` amended with one clause.

## DEV-008 — pointer links are verified by hand

**Severity:** Small · **Story:** 2 · **Found:** 2026-09-07, Gate 3 review

AC-2.3 and the story notes say `check_referenced_paths` resolves the new `.writ/docs/` links in the base. The check iterates `command_files()` — `commands/*.md` minus `_*.md` — and never reads `system-instructions.md`, so it is green regardless of the pointers. All four pointer paths exist on disk (`ls`), and `check_broken_refs` is green. No code change; extending the check to the base is outside the story. `spec-lite.md` amended.

---

## DEV-009 — `grep -c "Fable 5.1" adapters/cursor.md` cannot return 1

**Severity:** Medium · **Story:** 3 · **Found:** 2026-09-07, Gate 0 arch check; confirmed at Gate 3 review

**Spec said:** AC-3.4 proves the one-line-per-adapter rule by `grep -c "Fable 5.1" adapters/<file>.md` returning `1` for each of the four adapters. **Implementation did:** `adapters/cursor.md` already carried the model name on two lines before this story — the dated *Verification record — 2026-09-03* under `### Sub-Agent Models` (the origin line and the V1 self-report row), evidence from a real spawn experiment that must not be reworded to satisfy a grep. After the `## Model-specific` line lands, `grep -c` reads `1` for `claude-code.md`, `codex.md`, `openclaw.md` and `3` for `cursor.md`; the section-scoped count `awk '/^## Model-specific/,0' adapters/cursor.md | grep -c "Fable 5.1"` reads `1` for all four. **Why it matters:** the Goal Card rule ("no file under `adapters/` gains more than one model-specific instruction line per model") and Business Rule 7 hold — the story adds exactly one instruction line per file — but the AC's proxy counts mentions, not instruction lines. **Resolution:** ⚠️ flagged; pipeline PASS; the story records both counts; `spec.md` unchanged. A maintainer who wants the literal proxy can move the verification record out of `adapters/cursor.md`.

## DEV-010 — The base carried no literal Fable 5.1 batching line

**Severity:** Small · **Story:** 3 · **Found:** 2026-09-07, Gate 0 arch check

AC-3.4 and task 3.5 describe moving "the Fable 5.1 batching line currently in `system-instructions.md`". At `cf84742` neither base file names Fable 5.1; the batching instruction exists only in generic form — `## Command Execution Protocol` item 2 (*Use parallel tool execution when possible*), the *Methodical but efficient* personality bullet, and `_preamble.md` `## Tool Selection`'s *Parallel tool calls* bullet. Those three lines left with `behavior-request` rows whose reason names the adapters as the model-specific home (research F1 counter-signal), and the Fable 5.1 line itself was authored fresh under `## Model-specific` in each adapter (commit `99c1b0e`). `spec-lite.md` amended (Files in Scope, adapters row).

## DEV-011 — `cursor/writ.mdc` re-synced whole, not only its Prime Directive block

**Severity:** Medium · **Story:** 3 · **Found:** 2026-09-07, Gate 0 arch check; applied in commit `8596281`

**Spec said:** `cursor/writ.mdc` is the Prime Directive mirror; Business Rule 8 requires only that block to stay byte-identical, and DEV-007 left the decision about its other sections to this story. **Implementation did:** the file is now a byte-for-byte copy of the pruned `system-instructions.md` (4,600 bytes), as it was of the unpruned base at `cf84742`. `install.sh` copies `cursor/writ.mdc` to `.cursor/rules/` as the `alwaysApply: true` rule, so it is the base Cursor sessions actually load; leaving the moved and cut sections in it would have shipped the 20,885-byte pre-move base to Cursor while Claude Code and Codex got the pruned one, and Story 5's re-run would then measure a state Cursor users never see. Business Rule 8 holds trivially; `check_prime_directive_sync` green; the three `writ.mdc` literal pins (`check_autonomy_governance`, `check_recommendation_semantics`) are all inside the Prime Directive and still resolve. **Why it matters:** `spec-lite.md` line 19's parenthetical about DEV-007 is now historical. **Resolution:** ⚠️ flagged; pipeline PASS. `spec.md` unchanged.
