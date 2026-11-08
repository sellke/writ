# Verification Report: Generated Platform Trees

> **Date:** 2026-10-25
> **Spec:** 2026-10-22-generated-platform-trees
> **Mode:** default
> **Result:** ⚠️ Passed with warnings

## Summary

| Check | Status | Details |
|-------|--------|---------|
| Story file integrity | ⚠️ | 5 stories well-formed; status headers carry a date suffix (INFO-1) |
| Status consistency | ✅ | README in sync by status: 5 stories, 33 tasks, 24 criteria |
| Completion integrity | ✅ | 3a to 3f clean: every completed story has all criteria, tasks, and Definition of Done checked; `scripts/ac-trace.py check` reports no findings. 3g: 3 advisory notes |
| Dependency validation | ✅ | Story dependencies satisfied, no cycle; `scripts/spec-deps.py validate` reports the cross-spec graph `ok`. |
| Deliverables checklist | ✅ | No checkbox list; every file the contract names resolves (bare names to `scripts/` and `commands/`); status Complete |
| Contract alignment | ⚠️ | 4 heuristic findings (WARN-1 to WARN-4) |
| Spec-lite integrity | ⚠️ | Diverged; not regenerated (WARN-5) |
| Spec owner field | ✅ | @AdamSellke |

## Stories

| # | Title | Status | Tasks | Criteria | DoD |
|---|---|---|---|---|---|
| 1 | Adapter Table Parser and Parity Repairs | ✅ | 7/7 | 5/5 | 5/5 |
| 2 | Driver Write Mode for the Cursor and Claude Code Root Files | ✅ | 7/7 | 5/5 | 5/5 |
| 3 | Generated Codex Template | ✅ | 7/7 | 4/4 | 5/5 |
| 4 | `--check`, Coverage, Tokens, and Eval Wiring | ✅ | 7/7 | 5/5 | 5/5 |
| 5 | Install Evidence and Issue Closure | ✅ | 5/5 | 5/5 | 5/5 |

## Issues Found & Resolved

- None. Nothing needed a safe metadata fix.

## Outstanding Warnings

- [WARN-1] Check 6, Rule 8: the Codex template now carries a `## Prime Directive` section (DEV-011) and a second intro paragraph from the Codex verify-gap fix. Rule 8 still describes a one-paragraph intro.
- [WARN-2] Check 6, Rule 13: `check_platform_trees` runs `--check` only (DEV-008). Rule 13 still says `--check` then `coverage`.
- [WARN-3] Check 6, Must Include 3: the third vendor hit (`browser_navigate` in `commands/writ-design.md`) was rewritten to plain prose, not a neutral name (DEV-009).
- [WARN-4] Check 6, Rule 9: commit 47137a1 changed the Claude Code `Plan Mode` row away from Rule 9's verbatim cell. No drift-log entry records it; only the acceptance report does.
- [WARN-5] Check 7: spec-lite diverges from spec.md in three places, and in each the spec-lite text is the accepted one: eval wiring (`--check` only, DEV-008), write blocking (sub-generator `stale`, `missing`, `absent`, and `extra` reasons do not block), and vendor rewrites (plain prose allowed when no neutral name exists, DEV-009). Regenerating spec-lite from spec.md would restore the superseded rules, so it was not regenerated. Amend Rule 13, Journey step 4, Must Include 3, and Rule 8 with `/edit-spec`, then run `/verify-spec --fix`.
- [INFO-1] Story status headers read `Completed ✅ (<date>)`. The command's grammar has no date suffix, so 1c flags it. `scripts/spec-status.py` matches status by prefix and reads these as completed, and the README rows agree on status, so nothing was rewritten and the dates are kept.

## Notes

- Check 3g (advisory): `scripts/spec-analyze.py check` prints `pass` with no `reason:` lines. Jev (`scripts/jev-judge.py spec-findings`) escalated most stories; the orchestrator judged them. These meaning-level notes do not fail the check or the report:
  - ambiguity, `story-2-driver-write-mode-cursor-and-claude-code.md` (AC-2.4): AC-2.4 says that "given any reason" write mode prints fail, but a missing adapter heading yields a reason the State Catalog and AC-1.3 map to unverifiable with exit 0, so write mode could exit 1 or 0 on the same input.
  - gap, `story-4-check-coverage-tokens-and-eval-wiring.md` (AC-4.2): AC-4.2 pins only a vendor name "as a whole backticked token", while Business Rule 4 says call syntax such as `Grep("pattern")` "is a hit for Grep" and the Notes leave that case undecided, so no criterion covers it.
  - gap, `story-4-check-coverage-tokens-and-eval-wiring.md` (story level): The story claims the missing-heading State Catalog row ("unverifiable ... exit 0; nothing written") and the Upstream error path ("reason: <gen> --check exited <rc>"), but no AC-4.x criterion covers either outcome for --check or coverage.
- `jev-judge.py status` printed `reason: model_unpinned`.
- Diagnostic only. Use `/release` when you are ready to publish; it runs build checks, conditional tests, and changelog work.
