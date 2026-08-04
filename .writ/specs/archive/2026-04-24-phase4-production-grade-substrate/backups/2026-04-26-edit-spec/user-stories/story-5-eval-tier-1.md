# Story 5: Eval Tier 1 (Static Checks)

> **Status:** In Progress
> **Priority:** High
> **Effort:** S (~1 day; +0.5 day for triage of pre-existing violations)
> **Dependencies:** Stories 2, 3, 4 (checks reference owner field, manifest, preamble references)
> **Source recommendation:** Research addendum → "Skills-Creation Infrastructure" → "Build Tier 1 only. Defer Tier 2/3."

## User Story

**As a** Writ maintainer
**I want** a single bash script (`scripts/eval.sh`) that runs cheap static checks against command/agent files (required sections, anti-sycophancy phrasing, prime-directive sync, broken refs, length sanity, manifest well-formedness, preamble references, owner-field presence)
**So that** I have a quality floor I can trust before merging changes — and I can ship faster with confidence that obvious regressions don't slip through

## Acceptance Criteria

- [x] Given the spec ships, when I run `bash scripts/eval.sh` against the full Writ surface (post-Stories 1–4), then it exits 0 with no findings
- [x] Given a violation in the checked surface, when I run `bash scripts/eval.sh`, then it exits 1 with a finding citing file:line and one-line remediation hint
- [x] Given a violation in a category supporting auto-fix (`preamble`), when I run `bash scripts/eval.sh --check=preamble --fix`, then the missing reference is appended and the next run exits 0
- [ ] Given the CI gate (`.github/workflows/eval.yml`) is wired, when a PR introduces a violation, then the workflow fails and uploads `eval-report.md` as an artifact
- [x] Given `system-instructions.md` and `cursor/writ.mdc` Prime Directive sections are compared, when `bash scripts/eval.sh --check=prime-directive-sync` runs, then it verifies they are in sync locally
- [x] Given a pre-existing violation in the post-Stories 1–4 surface that cannot be auto-fixed and is not worth fixing now, when I document it, then it has an `<!-- eval-exempt: reason -->` comment and a tracking issue under `.writ/issues/`

## Implementation Tasks

- [x] 5.1 Write a verification checklist covering all 6 acceptance criteria; commit as `.writ/specs/.../user-stories/story-5-verification.md`
- [x] 5.2 Author `scripts/eval.sh` matching the bash style of `install.sh`, `ralph.sh`, `gen-skill.sh`; implement runner skeleton with `--check=NAME`, `--report=PATH`, `--fix` flags
- [x] 5.3 Implement the 8 checks per `sub-specs/technical-spec.md` → Story 5 → "Check details" table: `required-sections`, `anti-sycophancy`, `prime-directive-sync`, `broken-refs`, `length`, `manifest`, `preamble`, `owner`
- [x] 5.4 Run `bash scripts/eval.sh` against the post-Stories 1–4 surface; triage every finding (fix or `eval-exempt` with tracking issue)
- [x] 5.5 Implement `--fix` for the `preamble` check (append References section if missing)
- [x] 5.6 Wire `.github/workflows/eval.yml` to run `bash scripts/eval.sh --report=eval-report.md`, upload artifact on failure (per technical-spec → Story 5 → CI gate)
- [ ] 5.7 Test the CI gate end-to-end: deliberate violation in a test branch → CI fails → revert → CI passes
- [x] 5.8 Verify all locally testable acceptance criteria via checklist; capture results in `## What Was Built`

## Notes

**Dual-use justification (per ADR-007):** Solo dev: cheap quality floor; lets you ship faster without manually verifying conventions on every PR. Team-readiness: every contributor's PR is held to the same bar by the same script — no "did the maintainer notice?" variance. Eval Tier 1 is the bar that lets a team scale the command/agent surface without quality variance.

**Technical considerations:**
- All 8 checks are pure-bash + standard tools (grep, awk, diff, git); `yq` is needed only for the `manifest` check (reuse `gen-skill.sh`'s yq-or-fallback pattern)
- The anti-sycophancy phrase list is extensible — committed as a small data file, not hardcoded; future contributors can append patterns without touching script logic
- Owner-field date determination uses `git log --diff-filter=A` (matches Story 2's approach for `verify-spec`); legacy specs are exempt by date, not by content
- Pre-existing violations: assume a small triage budget (~0.5 day); broken refs and missing sections are usually quick fixes; length-budget overruns may need `eval-exempt` for legitimately-long commands like `commands/create-spec.md` (947 lines today, well under the 2000 limit)
- Output is a markdown report grouped by check category; non-zero exit on any failure; CI uploads on failure for easy review

**Risks:**
- **Pre-existing violations exceed triage budget:** mitigated by `eval-exempt` escape hatch + tracking issue (per AC6); each grandfathering decision is recorded
- **Anti-sycophancy phrase list flags false positives in legitimately exuberant content (e.g., the welcome messages in `system-instructions.md`):** mitigated by the phrase list being extensible — exempt the welcome-greetings block via `eval-exempt` if needed; or make the check ignore lines starting with `- "..."` in a "greetings" block
- **Length-sanity overrides legitimate growth:** the 2000-line command threshold is generous; if a future command genuinely needs more, raise the threshold rather than `eval-exempt` the file
- **CI flakiness from `yq` install:** mitigated by snap-install step + pure-bash fallback if snap fails

**Integration points:**
- Reads `.writ/manifest.yaml` (Story 3) for `manifest` check
- Reads `commands/_preamble.md` (Story 4) and verifies references in commands (`preamble` check)
- Reads spec frontmatter (Story 2) for `owner` check
- Reads `system-instructions.md` and `cursor/writ.mdc` for `prime-directive-sync` check
- Wired into the same `.github/workflows/eval.yml` that Story 3 introduced

## Definition of Done

- [ ] All tasks completed
- [ ] All 6 acceptance criteria verified
- [x] `bash scripts/eval.sh` exits 0 against the full Writ surface (post-Stories 1–4)
- [ ] CI gate verified by deliberate-violation test in a branch (then reverted)
- [x] All pre-existing violations either fixed or grandfathered with `eval-exempt` + tracking issue
- [x] Anti-sycophancy phrase list documented in a comment block at the top of the data file
- [x] Drift log entries (if any) recorded
- [x] `## What Was Built` section appended

## Context for Agents

- **Error map rows:** Each of the 8 check categories has its own error mode; `system-instructions.md` and `cursor/writ.mdc` Prime Directive drift; broken cross-file refs; missing required sections; length-budget overruns (`spec.md → 🎯 Experience Design → Error experience` and `sub-specs/technical-spec.md → Story 5 → Check details`)
- **Shadow paths:** Happy path: PR opened → CI runs eval → 0 findings → merge proceeds. Upstream error: pre-existing violation in main → triage to fix or `eval-exempt`. Empty input: file under 100 chars → eval skips (no false-positive on near-empty stubs)
- **Business rules:** Eval gates every PR; no merging on red; auto-fix only for `preamble` (others are safer manual); `eval-exempt` requires tracking issue (`spec.md → 📋 Business Rules`)
- **Experience:** Output is grouped markdown report with file:line + remediation hint; CI uploads artifact on failure for easy review (`spec.md → 🎯 Experience Design → Feedback model` and `Error experience`)
- **Technical reference:** `sub-specs/technical-spec.md → Story 5` (runner interface, all 8 check details, CI gate workflow, triage protocol, local dev workflow)
- **Source recommendation:** Research addendum → "Skills-Creation Infrastructure" → third row → "Build Tier 1 only. Defer Tier 2/3"

## What Was Built

Story 5 is implemented locally. Writ now has a bash-based Eval Tier 1 runner, an extensible anti-sycophancy phrase list, CI wiring, and a green local eval across the post-Stories-1-4 surface.

### Files Changed

- `scripts/eval.sh` — Added the eval runner with `--check=NAME`, `--report=PATH`, `--fix`, grouped markdown reports, and all 8 required checks.
- `.writ/eval/anti-sycophancy-phrases.txt` — Added the extensible banned-phrase list with top-of-file documentation.
- `.github/workflows/eval.yml` — Preserved `gen-skill.sh --check`, added `eval.sh --report=eval-report.md`, and configured failure artifact upload.
- `commands/create-spec.md` and `commands/plan-product.md` — Added narrow `## Invocation` sections to satisfy required-section checks.
- `.writ/specs/2026-03-27-context-engine/spec-lite.md` — Added a targeted `eval-exempt: length` comment for a pre-existing lite-spec budget violation.
- `.writ/issues/improvements/2026-04-24-trim-context-engine-spec-lite.md` — Added the required tracking issue for the grandfathered length violation.
- `user-stories/story-5-verification.md` — Added the verification checklist and command evidence.
- `user-stories/story-5-eval-tier-1.md` and `user-stories/README.md` — Updated Story 5 progress honestly.

### Verification

- `bash -n scripts/eval.sh` passed.
- `bash scripts/eval.sh --report=.writ/state/eval-story5-triaged.md` passed with 0 findings.
- `bash scripts/eval.sh --check=preamble --report=.writ/state/eval-story5-fix-confirm.md` passed after temporary auto-fix smoke testing.
- `bash scripts/eval.sh --check=prime-directive-sync --report=.writ/state/eval-story5-prime.md` passed.
- `bash scripts/gen-skill.sh --check` passed using the pure-bash fallback parser.

### Drift / Boundary Notes

- Remote GitHub artifact-upload behavior is not verified because this implementation pass was explicitly no-commit/no-push. The workflow is wired, but the deliberate pushed-PR violation smoke remains pending.
- The Story 5 task wording said to "commit" the checklist; the checklist was created but not committed, per the no-commit instruction.
