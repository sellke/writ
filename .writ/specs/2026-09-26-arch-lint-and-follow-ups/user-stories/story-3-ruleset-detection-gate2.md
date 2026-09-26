# Story 3: Ruleset Detection and Gate 2 Wiring

> **Status:** Not Started
> **Priority:** High
> **Dependencies:** None

## User Story

**As a** Writ user whose project encodes architecture rules as a lint ruleset
**I want to** have `/implement-story` Gate 2 detect that ruleset, run it next to the existing linters, and report it in one `arch-lint:` line
**So that** an import across a forbidden layer fails Gate 2 mechanically, while a project without a ruleset is never blocked

## Acceptance Criteria

> **AC IDs assigned through:** AC-3.5

- [ ] Given temp fixture repos, when `python3 scripts/arch-lint.py detect --repo <dir>` runs, then it detects dependency-cruiser (`.dependency-cruiser.{js,cjs,mjs,json}`; `run` when `node_modules/.bin/depcruise` exists, else `not-installed`), import-linter (`.importlinter`, `[importlinter]` in `setup.cfg`, or `[tool.importlinter]` in `pyproject.toml`; `run` when `lint-imports` is on `PATH`, else `not-installed`), eslint-plugin-boundaries (`via-eslint`), and ArchUnit (`via-tests`) exactly per technical-spec §3, printing one `tool: <name> <mode> <config>` line per ruleset in table order `[AC-3.1]`
- [ ] Given a runnable tool, when `detect` prints its `command:` line, then dependency-cruiser uses a `package.json` script containing `depcruise` as `npm run <name>`, else `npx --no-install depcruise --config <cfg> <src|.>`, and import-linter uses `lint-imports`; `not-installed`, `via-eslint`, and `via-tests` tools print no `command:` line; the helper uses no subprocess or network and never installs anything `[AC-3.2]`
- [ ] Given any repo, when `detect` finishes, then it prints `pass` or `unverifiable` first and `arch-lint detect: <n> ruleset(s), <m> runnable` last; no ruleset gives `pass` with `0 ruleset(s), 0 runnable`; an unreadable or unparseable config (invalid `package.json` JSON, undecodable file) gives `unverifiable` with `reason: config_unreadable <path>` while other detections still print; exit is 0 when it ran and 2 on usage errors, under Python 3.9 `[AC-3.3]`
- [ ] Given `commands/implement-story.md` Gate 2, when the existing linters have run, then the command runs `arch-lint.py detect`, runs each `command:` line from the repo root, sends a non-zero exit down the existing Gate 2 lint failure path (flag for review; no auto-fix), and never fails the gate for a missing or not-installed ruleset; Gate 2 and Step 4 item 8 print the `arch-lint:` line per the §3 table (`<names>`, `(via eslint)`, `(via tests)`, `(not installed)`, `none — see .writ/docs/architecture-lint.md`, `unverifiable (<reason>)`), and `--quick` keeps it `[AC-3.4]`
- [ ] Given the edited command, when `spawn-cap.py check --command commands/implement-story.md` and the governor and lean suites run, then `spawn-cap` prints `pass`, `KNOWN_OVER_BUDGET["commands/implement-story.md"]` and `DEFAULT_SHA256["implement-story"]` are re-pinned with dated comments naming `2026-09-26-arch-lint-and-follow-ups`, `commands/implement-story.lean.md` is byte-identical, and a wiring test pins the Gate 2 detect-and-run prose and the `arch-lint:` report line `[AC-3.5]`

## Implementation Tasks

- [ ] 3.1 Write failing tests in `scripts/tests/test_arch_lint.py` using temp fixture repos: each of the four tools with each mode, config variants (`setup.cfg`, `pyproject.toml`-only), the `npm run <name>` and `npx --no-install` command forms (with and without `src/`), empty `package.json` object, no ruleset, invalid-JSON `package.json`, output order, summary counts, and usage exit 2 `[AC-3.1, AC-3.2, AC-3.3]`
- [ ] 3.2 Implement `scripts/arch-lint.py detect [--repo .]` (stdlib only, Python 3.9, read-only, no subprocess, no network; `shutil.which` for `lint-imports`) until the tests pass `[AC-3.1, AC-3.2, AC-3.3]`
- [ ] 3.3 Append a failing wiring test class at the end of `scripts/tests/test_quality_gate_wiring.py`, with a docstring naming `2026-09-26-arch-lint-and-follow-ups`, pinning the Gate 2 `arch-lint.py detect` invocation, the run-each-`command:` sentence through the lint failure path, the missing-ruleset-never-blocks rule, and the `arch-lint:` line in Gate 2 and Step 4 item 8 `[AC-3.4, AC-3.5]`
- [ ] 3.4 Edit Gate 2 and Step 4 item 8 in `commands/implement-story.md` per technical-spec §3 as prose inside the existing gate (no new gate number, no `> **Agent:**` or `Task(` marker); trim adjacent prose where meaning is unchanged to limit growth `[AC-3.4]`
- [ ] 3.5 Re-pin `KNOWN_OVER_BUDGET["commands/implement-story.md"]` in `scripts/tests/test_governor_enforcement.py` and `DEFAULT_SHA256["implement-story"]` in `scripts/tests/test_lean_commands.py` with dated disclosure comments naming this spec `[AC-3.5]`
- [ ] 3.6 Verify: `spawn-cap.py check --command commands/implement-story.md` pass; `git diff --quiet HEAD -- commands/implement-story.lean.md`; `uv run --python 3.9 pytest` on touched suites; `bash scripts/eval.sh` Findings 0 `[AC-3.3, AC-3.5]`

## Notes

Only dependency-cruiser and import-linter are run (Business Rule 3); eslint-plugin-boundaries already runs inside eslint and ArchUnit inside the test suite, so re-running them would double-report. The helper only reads files and checks for `node_modules/.bin/depcruise` and `lint-imports`. Gate 2 executes the printed commands, and `npx --no-install` keeps that offline. The `none` line links `.writ/docs/architecture-lint.md`, which Story 4 creates; the link may dangle until Story 4 lands. `spawn-cap.py` counts only `> **Agent:**` lines and `Task(` calls, so the Gate 2 edit must stay in prose.

## Definition of Done

- [ ] All tasks completed
- [ ] All acceptance criteria met
- [ ] Tests passing
- [ ] Code reviewed
- [ ] Documentation updated

## Context for Agents

- **Business rules:** spec.md → ## 📋 Business Rules (1 Missing ruleset never blocks, 2 Detected ruleset uses the existing lint path, 3 Run only standalone checkers, 4 Read-only and offline detection, 7 Lean sibling untouched)
- **Technical:** sub-specs/technical-spec.md → ## 3, ## 5
- **Experience:** spec.md → ## 🎯 Experience Design → State Catalog
