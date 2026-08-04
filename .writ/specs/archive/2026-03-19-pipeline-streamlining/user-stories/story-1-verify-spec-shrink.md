# Story 1: Shrink verify-spec to Pure Diagnostic

> **Status:** Completed ✅
> **Priority:** High
> **Dependencies:** None

## User Story

**As a** developer using Writ
**I want to** run `/verify-spec` as a fast, metadata-only diagnostic that auto-fixes what it can
**So that** spec hygiene is a quick health check I run when I suspect drift, not a ceremonial pipeline bottleneck

## Acceptance Criteria

1. **Given** the rewritten `verify-spec.md`, **when** an AI agent executes `/verify-spec` with no flags, **then** it runs checks 1-5 and 8, auto-fixes all fixable discrepancies, and reports unfixable issues — without prompting.

2. **Given** the rewritten file, **when** searching for `--pre-deploy`, `--sync-trello`, `CHANGELOG`, or `Trello`, **then** zero matches are found.

3. **Given** the rewritten file, **when** reviewing the modes table, **then** exactly 4 modes exist: default (auto-fix), `--check` (read-only), `--spec [path]` (specific spec), `--all` (all specs).

4. **Given** the rewritten file, **when** reviewing the verification checks, **then** only checks 1-5 and 8 remain. Checks 6 (test verification) and 7 (coverage verification) are removed entirely.

5. **Given** the rewritten file, **when** reviewing the report template, **then** it shows 6 checks (not 8), has no "Skipped" rows, and no "release gate" language.

6. **Given** the rewritten file, **when** reviewing the integration table, **then** it describes verify-spec as a diagnostic tool, not a release prerequisite. No reference to "run verify-spec before releasing."

## Implementation Tasks

- [x] 1.1 Remove `--pre-deploy` mode — delete checks 6 (test verification), 7 (coverage verification), Phase 6 (build verification), and all conditional `--pre-deploy` branches throughout the file.

- [x] 1.2 Remove Phase 4.4 (CHANGELOG generation) — changelog generation belongs exclusively to `/release`.

- [x] 1.3 Remove Phase 4.5 (Trello sync) and `--sync-trello` mode — Trello integration is dropped from the pipeline entirely.

- [x] 1.4 Flip default behavior to auto-fix — current default prompts before fixing; new default auto-fixes silently, reports what couldn't be fixed. `--check` becomes the read-only mode. Remove `--fix` flag (it's now the default).

- [x] 1.5 Update modes table — reduce to 4 modes: default, `--check`, `--spec [path]`, `--all`.

- [x] 1.6 Update verification report template — remove rows for checks 6 and 7, remove "Skipped" indicators, remove `--pre-deploy` report variant, strip all "release gate" framing.

- [x] 1.7 Update integration table and boundary principle — reframe verify-spec as an independent diagnostic. Remove "run verify-spec before releasing" language. Update recommended flow to show verify-spec as optional, not a pipeline step.

## Notes

- **Key principle:** verify-spec is a diagnostic, not a gate. Like running a linter — useful when you want it, never blocking when you don't.

- **Risk:** Over-stripping could lose the report file generation (Phase 5), which is still valuable for audit trails. Keep Phase 5 but simplify its template to match the reduced check set.

- **Watch for:** The Phase 3 report currently shows 8 checks. After removal, the report format needs to show 6 checks with no "skipped" rows — the absence of checks 6-7 should be invisible, not called out.

## Definition of Done

- [x] All tasks completed
- [x] All acceptance criteria met
- [x] No references to --pre-deploy, Trello, or CHANGELOG generation remain
- [x] Default mode auto-fixes without prompting
- [x] Report template shows 6 checks cleanly
