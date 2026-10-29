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
