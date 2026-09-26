# Story 4: Architecture-Lint Guide and ADR Hook

> **Status:** Completed ✅
> **Commit:** 4edbe5beb73a0cab57c8f3a0ba706f3994762d4b
> **Priority:** Medium
> **Dependencies:** Story 3

## User Story

**As a** developer on a Writ-managed project whose Gate 2 reports `arch-lint: none`
**I want to** a shipped guide with one minimal ruleset per ecosystem, and `/create-adr` prompting me to encode layering decisions as lint rules
**So that** architecture decisions are enforced mechanically in Gate 2 instead of relying on a reviewer to remember them

## Acceptance Criteria

> **AC IDs assigned through:** AC-4.4

- [x] Given `.writ/docs/architecture-lint.md`, when a reader opens it, then it has sections covering why mechanical rules beat judgment, how Gate 2 finds and runs rulesets (the technical-spec §3 detection content: tool, detection file, mode, command), and how rulesets relate to ADRs `[AC-4.1]`
- [x] Given the guide's examples, when each is copied into a project, then it is a minimal, valid ruleset: a dependency-cruiser `forbidden` rule, an import-linter `layers` contract, an eslint-plugin-boundaries `dependencies` rule (formerly `element-types`), and an ArchUnit `layeredArchitecture()` test; and each example names the file `arch-lint.py detect` looks for (`.dependency-cruiser.{js,cjs,mjs,json}`; `.importlinter` / `setup.cfg` `[importlinter]` / `pyproject.toml` `[tool.importlinter]`; `package.json`; `pom.xml` / `build.gradle` / `build.gradle.kts`) `[AC-4.2]`
- [x] Given `commands/create-adr.md` Step 4 "After writing", when the decision constrains layering, import direction, or module dependencies, then one numbered step tells the author to add an **Enforcement** note naming the lint rule that encodes it and linking `.writ/docs/architecture-lint.md`; the file stays under its byte budget `[AC-4.3]`
- [x] Given `scripts/tests/test_architecture_lint_doc.py` and `bash scripts/install.sh --dry-run`, when they run, then the test pins all four tool names and each tool's detection file in the doc plus the doc link in `create-adr.md`, and the dry run lists `.writ/docs/architecture-lint.md` under Writ docs `[AC-4.4]`

## Implementation Tasks

- [x] 4.1 Write failing tests in `scripts/tests/test_architecture_lint_doc.py`: the doc exists, names dependency-cruiser, import-linter, eslint-plugin-boundaries, and ArchUnit, and names each tool's detection file from technical-spec §3; the four example markers (`forbidden`, `layers`, `element-types`, `layeredArchitecture()`) appear; `commands/create-adr.md` links `.writ/docs/architecture-lint.md` and mentions **Enforcement** `[AC-4.1, AC-4.2, AC-4.3, AC-4.4]`
- [x] 4.2 Write `.writ/docs/architecture-lint.md`: why mechanical over judgment; how Gate 2 detects and runs rulesets (detection table, run vs. via-eslint / via-tests / not-installed, `arch-lint:` report line, link to `scripts/arch-lint.py`) `[AC-4.1]`
- [x] 4.3 Add the four minimal examples to the guide, each with its config file name and a one-line explanation of the rule it encodes; add the "Relation to ADRs" section `[AC-4.1, AC-4.2]`
- [x] 4.4 Edit `commands/create-adr.md` Step 4 "After writing": insert one numbered step before "Present the completed ADR" for the **Enforcement** note; renumber the final step `[AC-4.3]`
- [x] 4.5 Run `bash scripts/install.sh --dry-run` against a temp target and confirm the new doc appears in the Writ docs overlay list `[AC-4.4]`
- [x] 4.6 Verify: `uv run --python 3.9 pytest scripts/tests/test_architecture_lint_doc.py scripts/tests/test_governor_enforcement.py`, `uv run pytest`, bash suite, `bash scripts/eval.sh` Findings 0 `[AC-4.1, AC-4.2, AC-4.3, AC-4.4]`

## Notes

The doc ships to user projects through `install.sh`'s `.writ/docs/*.md` overlay; no install script change is expected. Examples must be minimal and syntactically valid for each tool's current config format; check each tool's docs rather than writing from memory. Keep the detection content consistent with Story 3's `arch-lint.py`; if they disagree, the helper is the source of truth. The `create-adr.md` edit is one short numbered step, with no re-pin.

## Definition of Done

- [x] All tasks completed
- [x] All acceptance criteria met
- [x] Tests passing
- [x] Code reviewed
- [x] Documentation updated

## Context for Agents

- **Business rules:** spec.md → ## 📋 Business Rules (1 Missing ruleset never blocks, 3 Run only standalone checkers)
- **Experience:** spec.md → ## 🎯 Experience Design (State Catalog `arch-lint: none — see .writ/docs/architecture-lint.md`)
- **Technical:** sub-specs/technical-spec.md → ## 3 (detection table) and ## 4

## What Was Built

**Implementation Date:** 2026-09-26

### Files Modified

1. **`.writ/docs/architecture-lint.md`** (new) — why mechanical rules beat judgment; how Gate 2 finds and runs rulesets (detection table, modes, commands and `arch-lint:` report lines matching `scripts/arch-lint.py`); four minimal examples encoding the same ui → domain → data layering (dependency-cruiser `forbidden`, import-linter `layers` in INI and `pyproject.toml`, eslint-plugin-boundaries `dependencies` with v7 `policies`, ArchUnit `layeredArchitecture()`); relation to ADRs. [AC-4.1, AC-4.2]
2. **`commands/create-adr.md`** — Step 4 "After writing" item 4: an **Enforcement** note naming the lint rule when a decision constrains layering, import direction, or module dependencies, linking the guide; "Present the completed ADR" is item 5. 11918 bytes, no re-pin. [AC-4.3]
3. **`scripts/tests/test_architecture_lint_doc.py`** (new) — 13 tests; detection file names loaded from `arch-lint.py`, example markers inside code blocks, current eslint rule names, Enforcement step position and triggers. [AC-4.1, AC-4.2, AC-4.3, AC-4.4]

### Verification

- 62 tests pass on Python 3.9 (doc + governor); `install.sh --dry-run` into a temp repo lists `.writ/docs/architecture-lint.md` under Writ docs.
- dependency-cruiser 18.4.0, eslint 10.11 + eslint-plugin-boundaries 7.2.0 and import-linter 2.15 each flagged a deliberate upward import from the guide's examples; ArchUnit not compiled (no Java runtime).
- Gate 3: `review-agent` (routed by boundary crossings) PASS, 3 Minor findings, all fixed (install caveat in the intro, eslint names pinned, detection names read from the helper).
- Drift: DEV-009..DEV-010, both Small.
