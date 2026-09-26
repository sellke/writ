# Story 4: Architecture-Lint Guide and ADR Hook

> **Status:** Not Started
> **Priority:** Medium
> **Dependencies:** Story 3

## User Story

**As a** developer on a Writ-managed project whose Gate 2 reports `arch-lint: none`
**I want to** a shipped guide with one minimal ruleset per ecosystem, and `/create-adr` prompting me to encode layering decisions as lint rules
**So that** architecture decisions are enforced mechanically in Gate 2 instead of relying on a reviewer to remember them

## Acceptance Criteria

> **AC IDs assigned through:** AC-4.4

- [ ] Given `.writ/docs/architecture-lint.md`, when a reader opens it, then it has sections covering why mechanical rules beat judgment, how Gate 2 finds and runs rulesets (the technical-spec §3 detection content: tool, detection file, mode, command), and how rulesets relate to ADRs `[AC-4.1]`
- [ ] Given the guide's examples, when each is copied into a project, then it is a minimal, valid ruleset: a dependency-cruiser `forbidden` rule, an import-linter `layers` contract, an eslint-plugin-boundaries `element-types` rule, and an ArchUnit `layeredArchitecture()` test; and each example names the file `arch-lint.py detect` looks for (`.dependency-cruiser.{js,cjs,mjs,json}`; `.importlinter` / `setup.cfg` `[importlinter]` / `pyproject.toml` `[tool.importlinter]`; `package.json`; `pom.xml` / `build.gradle` / `build.gradle.kts`) `[AC-4.2]`
- [ ] Given `commands/create-adr.md` Step 4 "After writing", when the decision constrains layering, import direction, or module dependencies, then one numbered step tells the author to add an **Enforcement** note naming the lint rule that encodes it and linking `.writ/docs/architecture-lint.md`; the file stays under its byte budget `[AC-4.3]`
- [ ] Given `scripts/tests/test_architecture_lint_doc.py` and `bash scripts/install.sh --dry-run`, when they run, then the test pins all four tool names and each tool's detection file in the doc plus the doc link in `create-adr.md`, and the dry run lists `.writ/docs/architecture-lint.md` under Writ docs `[AC-4.4]`

## Implementation Tasks

- [ ] 4.1 Write failing tests in `scripts/tests/test_architecture_lint_doc.py`: the doc exists, names dependency-cruiser, import-linter, eslint-plugin-boundaries, and ArchUnit, and names each tool's detection file from technical-spec §3; the four example markers (`forbidden`, `layers`, `element-types`, `layeredArchitecture()`) appear; `commands/create-adr.md` links `.writ/docs/architecture-lint.md` and mentions **Enforcement** `[AC-4.1, AC-4.2, AC-4.3, AC-4.4]`
- [ ] 4.2 Write `.writ/docs/architecture-lint.md`: why mechanical over judgment; how Gate 2 detects and runs rulesets (detection table, run vs. via-eslint / via-tests / not-installed, `arch-lint:` report line, link to `scripts/arch-lint.py`) `[AC-4.1]`
- [ ] 4.3 Add the four minimal examples to the guide, each with its config file name and a one-line explanation of the rule it encodes; add the "Relation to ADRs" section `[AC-4.1, AC-4.2]`
- [ ] 4.4 Edit `commands/create-adr.md` Step 4 "After writing": insert one numbered step before "Present the completed ADR" for the **Enforcement** note; renumber the final step `[AC-4.3]`
- [ ] 4.5 Run `bash scripts/install.sh --dry-run` against a temp target and confirm the new doc appears in the Writ docs overlay list `[AC-4.4]`
- [ ] 4.6 Verify: `uv run --python 3.9 pytest scripts/tests/test_architecture_lint_doc.py scripts/tests/test_governor_enforcement.py`, `uv run pytest`, bash suite, `bash scripts/eval.sh` Findings 0 `[AC-4.1, AC-4.2, AC-4.3, AC-4.4]`

## Notes

The doc ships to user projects through `install.sh`'s `.writ/docs/*.md` overlay; no install script change is expected. Examples must be minimal and syntactically valid for each tool's current config format; check each tool's docs rather than writing from memory. Keep the detection content consistent with Story 3's `arch-lint.py`; if they disagree, the helper is the source of truth. The `create-adr.md` edit is one short numbered step, with no re-pin.

## Definition of Done

- [ ] All tasks completed
- [ ] All acceptance criteria met
- [ ] Tests passing
- [ ] Code reviewed
- [ ] Documentation updated

## Context for Agents

- **Business rules:** spec.md → ## 📋 Business Rules (1 Missing ruleset never blocks, 3 Run only standalone checkers)
- **Experience:** spec.md → ## 🎯 Experience Design (State Catalog `arch-lint: none — see .writ/docs/architecture-lint.md`)
- **Technical:** sub-specs/technical-spec.md → ## 3 (detection table) and ## 4
