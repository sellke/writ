# Story 5 Verification Checklist

> **Story:** [Eval Tier 1 (Static Checks)](story-5-eval-tier-1.md)
> **Date:** 2026-04-24

## Acceptance Criteria

- [x] `bash scripts/eval.sh` exits 0 against the full post-Stories-1-4 Writ surface.
  - Evidence: `bash scripts/eval.sh --report=.writ/state/eval-story5-triaged.md`
- [x] Violations produce non-zero exit and file-specific findings.
  - Evidence: initial full eval reported missing command sections, anti-sycophancy false positives, and a pre-existing length violation with file references.
- [x] `preamble` auto-fix appends the missing reference and the next run exits 0.
  - Evidence: temporary `commands/eval-fix-smoke.md` was fixed by `bash scripts/eval.sh --check=preamble --fix --report=.writ/state/eval-story5-fix.md`, then confirmed by `bash scripts/eval.sh --check=preamble --report=.writ/state/eval-story5-fix-confirm.md`; the temporary file was deleted.
- [ ] GitHub artifact upload was verified on a pushed PR with a deliberate violation.
  - Not run: this requires commit/push activity, which is explicitly out of scope for this implementation pass.
- [x] `prime-directive-sync` runs clean locally.
  - Evidence: `bash scripts/eval.sh --check=prime-directive-sync --report=.writ/state/eval-story5-prime.md`
- [x] Pre-existing violations are fixed or grandfathered with `eval-exempt` plus issue.
  - Evidence: `.writ/specs/2026-03-27-context-engine/spec-lite.md` has a targeted `eval-exempt: length` comment and `.writ/issues/improvements/2026-04-24-trim-context-engine-spec-lite.md` tracks cleanup.

## Required Commands

- [x] `bash -n scripts/eval.sh`
- [x] `bash scripts/eval.sh`
- [x] `bash scripts/eval.sh --check=preamble`
- [x] `bash scripts/eval.sh --check=prime-directive-sync`
- [x] `bash scripts/eval.sh --check=preamble --fix` on a temporary command file
- [x] `bash scripts/gen-skill.sh --check`

## Notes

- CI wiring is present in `.github/workflows/eval.yml`: `gen-skill.sh --check` remains, `eval.sh --report=eval-report.md` runs after it, and `eval-report.md` uploads on failure.
- Remote CI behavior remains a final smoke test for the next pushed branch or PR.
