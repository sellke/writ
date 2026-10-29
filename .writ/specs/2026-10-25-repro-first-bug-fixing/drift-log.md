# Drift Log

> Spec: .writ/specs/2026-10-25-repro-first-bug-fixing/
> Created: 2026-10-29
> ⚠️ Append-only — do not modify existing entries.

---

## Story 1: Repro-Order Check Script — Drift Report

> Run: 2026-10-29
> Overall Drift: Small

### Deviations

#### [DEV-001] Switch-line regex follows the existing switch readers, not the technical spec
- **Severity:** Small
- **Spec said:** technical-spec § Order of work step 1 gives `^\s*-\s*\*\*Repro First:\*\*\s*(\S+)\s*$`; story task 1.2 says to use the `scripts/review-panel.py` `config_value` pattern.
- **Implementation did:** `^- \*\*Repro First:\*\*[ \t]*(.*)$`, first match, value stripped, with the semantics of `scripts/review-override.py` `_resolve_switch`: absent, empty, or `on` (any case) → on; `off` (any case) → `unverifiable` / `reason: repro-first off` before any git call; another value → on plus `reason: repro-first value <v> read as on`. An indented line is not read, and `off # note` reads as on with the value reason line.
- **Reason:** The story task is the more specific instruction, and it keeps all four Phase 15 config switches on one line shape.
- **Resolution:** Auto-amended
- **Spec amendment:** technical-spec § Order of work step 1 reads `^- \*\*Repro First:\*\*[ \t]*(.*)$` (first match, value stripped; empty reads as on). None needed in spec-lite.md; it does not give the pattern.

#### [DEV-002] Rule 6 freezes only the repro's test-classified, written paths
- **Severity:** Small
- **Spec said:** Check Rule 6 covers "a path the repro commit added or modified"; Business Rule 5 says "any file the repro commit added or changed".
- **Implementation did:** Freezes paths the repro commit added, modified, type-changed, or renamed/copied to that classify as test files. `.writ/` paths and paths the repro deleted are not frozen; a source path in a repro already fails Rule 3.
- **Reason:** Freezing `.writ/` would fail every story completion commit, and reporting a fix's edit to a source file as `repro_test_modified` would misname the problem.
- **Resolution:** Auto-amended
- **Spec amendment:** Check Rule 6 reads "No later non-repro commit modifies, renames, or deletes a test file the repro commit added or modified (`.writ/` paths are never frozen)." None needed in spec-lite.md.

#### [DEV-003] Which commit the `<sha>` in a reason line names
- **Severity:** Small
- **Spec said:** Reason codes carry `<sha>` without saying which commit.
- **Implementation did:** Rules 4 (`source_before_repro`) and 6 (`repro_test_modified`) name the offending commit; Rules 2, 3, and 5 name the repro commit. Documented in the script docstring and the contract Notes.
- **Reason:** Fills a gap; Story 4's consumers print these lines.
- **Resolution:** Auto-amended
- **Spec amendment:** Under the Check Rules table: "In rules 4 and 6, `<sha>` is the offending commit; in rules 2, 3, and 5 it is the repro commit." None needed in spec-lite.md.

#### [DEV-004] Printed paths and subjects escape control characters; an unsearchable `.writ/` exits 2
- **Severity:** Small
- **Spec said:** Error & Rescue Map: an unreadable config exits 2. Nothing on control characters in output.
- **Implementation did:** The existence check and the read share one `OSError`/`UnicodeDecodeError` handler, so a `.writ/` that cannot be searched exits 2 instead of a traceback. Every `reason:` line passes through `printable()`, which escapes C0, DEL, C1, U+2028, and U+2029, so a filename holding a newline cannot add a `reason:` line. Both came from Gate 3 recommendations, each with a test.
- **Reason:** Keeps the exit-2 contract and the one-finding-per-line output shape that consumers parse.
- **Resolution:** Auto-amended
- **Spec amendment:** technical-spec § CLI adds "Control characters in printed paths and subjects are escaped." None needed in spec-lite.md.

---

## Story 2: The tdd-cycle Bug Path — Drift Report

> Run: 2026-10-29
> Overall Drift: Small

### Deviations

#### [DEV-005] `## Repro First` sits after `## Reviewer Filters`, not after `## Review Panel`
- **Severity:** Small
- **Spec said:** Task 2.4: add a `## Repro First` section "after `## Review Panel`" that follows that section's pattern.
- **Implementation did:** The row is last in Supported Keys and the section follows `## Reviewer Filters`, the last of the three switch sections (Gate 0 Divergence, Safety Fact, Reviewer Filters) that sibling Phase 15 specs added after Review Panel. It uses their pattern: fenced `off` example, then one paragraph.
- **Reason:** Placing it directly after Review Panel would split the switch sections, and Review Panel is a slug list, not an on/off switch. The contract and technical spec set no placement.
- **Resolution:** Auto-amended
- **Spec amendment:** Task 2.4 reads "add a `## Repro First` section after `## Reviewer Filters` that follows the switch sections' pattern". None needed in spec-lite.md.

#### [DEV-006] Step 3 says the `Repro:` trailer shares the last paragraph with other trailers; the example shows it on its own line
- **Severity:** Small
- **Spec said:** technical-spec § Skill Section Draft step 3: "a trailer `Repro: <issue path or one-line bug>` in the message's last paragraph"; the Examples block shows `Repro:` on the subject line.
- **Implementation did:** Step 3 adds "with any other trailers and no blank line between them". The example puts `Repro: login fails for plus-sign emails` on an indented line under the repro `commit:` line.
- **Reason:** `scripts/repro-order.py` reads only the final paragraph (Story 1); a separate `Repro:` paragraph followed by a `Co-Authored-By:` or `Ref:` paragraph is not detected, and a one-line message with `Repro:` on the subject fails `no_repro_commit`.
- **Resolution:** Auto-amended
- **Spec amendment:** technical-spec § Skill Section Draft step 3 and Examples block as built. None needed in spec-lite.md.

#### [DEV-007] Removal Inventory row 1 omits the When to Use bullet this story changes
- **Severity:** Small
- **Spec said:** Removal Inventory, `skills/tdd-cycle/SKILL.md` row: "`### Bug fixes: repro first` section and its example; restore the original two-line bug example".
- **Implementation did:** Per AC-2.3, the When to Use bug bullet also changed to point at the section. The removed example was three lines (red / green / refactor), not two.
- **Reason:** Followed literally, the row would leave a bullet pointing at a deleted heading. `2026-10-25-gate-upgrade-removal-measurement` consumes this inventory.
- **Resolution:** Auto-amended
- **Spec amendment:** Removal Inventory row reads "`### Bug fixes: repro first` section; the bug example under `## Examples` (restore the three-line `parseDate('')` example); the When to Use bug bullet (restore the 'reproduce it with a failing test first' bullet)". Recorded here because the pipeline never auto-modifies `spec.md`. None needed in spec-lite.md.

---
