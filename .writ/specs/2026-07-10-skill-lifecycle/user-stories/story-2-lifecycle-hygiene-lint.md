# Story 2: Lifecycle Hygiene Lint

> **Status:** Completed ✅
> **Priority:** High
> **Dependencies:** Story 1

## User Story

**As a** reviewer running `/refresh-command --lint-skills`
**I want to** have `scripts/lint-skill.sh` prove that each skill's declared `status:` is earned by the evidence present, and have a `skill-lifecycle` eval check guard the rules
**So that** no skill can silently claim a maturity it has not earned, and the contract is enforced identically at authoring time, review time, and in CI

## Acceptance Criteria

- [x] Given a `SKILL.md` with no `status:` field or an out-of-vocabulary value, when `scripts/lint-skill.sh` runs, then it emits a lifecycle finding (missing status / invalid status) in the existing finding format and exits `1`.
- [x] Given a skill declaring `proven` with fewer than three evidence entries, or `promoted` without a `type: promotion` entry, when the lint runs, then it emits an "unearned state" finding naming the exact shortfall and exits `1`.
- [x] Given an evidence entry missing any of `date`, `type`, `ref`, `note`, or using an out-of-vocabulary `type`, when the lint runs, then it emits an evidence finding naming the missing or invalid field and exits `1`.
- [x] Given a valid `candidate` (no evidence), `proven` (≥3 entries), and `promoted` (proven bar + promotion) skill, when the lint runs, then each passes with exit `0` and no lifecycle finding.
- [x] Given `scripts/eval.sh`, when the `skill-lifecycle` check runs, then it drives all eight fixtures through `lint-skill.sh`, asserts each expected exit code, and confirms via `require_literal` that the lint script and `.writ/docs/skills.md` encode the earned-state contract.

## Implementation Tasks

- [x] 2.1 Write the eight failing lifecycle fixtures FIRST (valid candidate/proven/promoted; unearned proven; unearned promoted; invalid status; malformed evidence; missing status) under a disposable fixtures path excluded from product discovery.
- [x] 2.2 Add a `lint_lifecycle` step to `scripts/lint-skill.sh`, invoked from `lint_file` after the description-shape and body-shape checks, reusing the existing `awk` frontmatter extraction.
- [x] 2.3 Implement checks L1 (status present), L2 (vocabulary), L3 (non-candidate meets its evidence-count threshold), and L4 (`promoted` carries a `type: promotion` entry), emitting findings in the existing format and incrementing the shared violation counter.
- [x] 2.4 Implement L5 evidence-entry well-formedness parsing (key-based, tolerant of reordered keys, `evidence: []`, and indentation drift) with a finding that names the missing/invalid field.
- [x] 2.5 Add `check_skill_lifecycle` to `scripts/eval.sh` and append `skill-lifecycle` to the `CHECKS` array (append-only, distinct region; note the SHARED-ADDITIVE seam with skill-extraction).
- [x] 2.6 Run the fixtures through `bash scripts/lint-skill.sh` and confirm each produces its expected exit code and finding; confirm `skills/conventional-commits/SKILL.md` (proven, from Story 1) passes.
- [x] 2.7 Run `bash scripts/eval.sh --check=skill-lifecycle`, then `bash scripts/lint-skill.sh skills/*/SKILL.md` and full `bash scripts/eval.sh`; confirm `commands/refresh-command.md` is unedited via targeted search.

> **Note:** The `skill-lifecycle` eval check's `require_literal` anchors on `.writ/docs/skills.md` are satisfied by the Story 3 lifecycle doc section; the fixture scenarios (8/8) and the lint-script anchors are green from this story. Full `eval.sh` goes green once Story 3 lands.

## Notes

- All lifecycle logic lives in `scripts/lint-skill.sh`. Do NOT add lifecycle logic to `commands/refresh-command.md` — its Phase 5 `--lint-skills` flag already invokes `bash scripts/lint-skill.sh skills/*/SKILL.md`, so new checks flow through automatically.
- Exit codes stay `0` (clean), `1` (violations), `2` (usage error). Lifecycle findings are violations, counted alongside description-shape and body-shape findings.
- The lint validates evidence *shape and thresholds only* — it never fetches or verifies that a cited path or transcript UUID is genuine.
- Fixtures are failing-first: write them before the `lint-skill.sh` edits so the red→green transition is observable.
- `scripts/eval.sh` is SHARED-ADDITIVE with `2026-07-10-skill-extraction`; append one function and one `CHECKS` line. Sequential phase execution keeps the additions conflict-free.

## Definition of Done

- [x] All tasks completed
- [x] All acceptance criteria met
- [x] Eight fixtures produce their expected exit codes
- [x] `skill-lifecycle` registered in `CHECKS` and passing within full `eval.sh`
- [x] `commands/refresh-command.md` confirmed unedited
- [x] `bash scripts/lint-skill.sh skills/*/SKILL.md` clean

## Context for Agents

- **Error map rows:** [`technical-spec.md` → `## Error & Rescue Map` → `Parse skill frontmatter`, `Validate status value`, `Enforce earned state`, `Parse evidence block`, `Eval registration`, `Refresh-command leakage`]
- **Shadow paths:** [`technical-spec.md` → `## Shadow Paths` → `Status validation`, `Evidence parsing`, `Earned-state`, `Eval check`]
- **Design decisions:** [`technical-spec.md` → `### D3 — State Is Earned From Evidence`, `### D4 — Lint Is the Single Validator`, `### D5 — Evidence Parsing Without a YAML Library`]
- **Fixtures:** [`technical-spec.md` → `## Fixture Design`]
- **Business rules:** [`spec.md` → `### Business Rules` → Rule 3 (earned from evidence), Rules 5–7 (thresholds and monotone ladder), Rule 9 (violation model)]
- **Requirements:** [`spec.md` → `### Detailed Requirements` → `R4 — Lifecycle Hygiene Lint`, `R5 — Lifecycle Eval Check`]
- **Matrix:** [`technical-spec.md` → `## File × Story Matrix` → S2 rows for `scripts/lint-skill.sh`, `scripts/eval.sh`, and lifecycle lint fixtures]
