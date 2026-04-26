# Story 5 — Remote CI Gate Organic Validation

> **Type:** Improvement
> **Priority:** Low
> **Effort:** Small
> **Created:** 2026-04-26
> **spec_ref:** .writ/specs/2026-04-24-phase4-production-grade-substrate/spec.md

## TL;DR

Confirm — on the first PR through CI — that the `.github/workflows/eval.yml` workflow fires correctly: `gen-skill.sh --check` and `eval.sh --report=eval-report.md` run, failures surface as a non-zero workflow exit, and `eval-report.md` uploads as a build artifact on failure.

## Current State

- `.github/workflows/eval.yml` is committed and structurally sound: `gen-skill.sh --check` runs first, then `eval.sh --report=eval-report.md`, and `actions/upload-artifact@v4` uploads `eval-report.md` with `if: failure()`.
- Local validation is green: `bash scripts/eval.sh` exits 0 across the post-Stories-1–4 surface; `bash scripts/eval.sh --check=preamble --fix` succeeds; `bash scripts/gen-skill.sh --check` succeeds.
- The only piece not yet validated is live behavior against GitHub Actions on a real pushed branch/PR.

## Expected Outcome

- On the first PR opened against `main` after Phase 4 ships, the eval workflow runs.
- If the PR contains any violations, the workflow fails AND `eval-report.md` is downloadable from the workflow run as a build artifact.
- If the PR is clean, the workflow passes silently.
- Outcome captured in that PR's review notes (or the next `verify-spec` run if the PR is the Phase 4 ship PR itself).

## Relevant Files

- `.github/workflows/eval.yml`
- `scripts/eval.sh`
- `scripts/gen-skill.sh`
- `.writ/specs/2026-04-24-phase4-production-grade-substrate/user-stories/story-5-eval-tier-1.md`

## Notes

- This issue is tracked rather than gated, per the 2026-04-26 contract update on the Phase 4 spec — see that spec's `CHANGELOG.md`.
- The Phase 4 ship PR itself is the natural validation event: it will be the first PR after Story 5 lands and will exercise both `gen-skill.sh --check` and `eval.sh` on the real workflow.
- If the workflow misbehaves on first run (silent pass with violations, or upload-artifact failure), that's a real bug to fix, not a documentation issue.
