# Story 2: Default Path and Flags — Two-Spawn implement-story

> **Status:** Not Started
> **Priority:** High
> **Dependencies:** Story 1

## User Story

**As a** Writ maintainer implementing Phase 11 Stage 4b
**I want** no-flag `/implement-story` to spawn only `coding-agent` and `evaluator-agent`, with `--full-pipeline` / `--quick` / `--review-only` matching the locked matrix, two-fail escalation, and default Gate 4 script fail recoding via `coding-agent`
**So that** default Task count is ≤2 while Stage 2b scripts still run, FAIL-only `review-override.py` is unchanged, and the six-agent path stays behind `--full-pipeline`

## Acceptance Criteria

> **AC IDs assigned through:** AC-2.5

- [ ] Given `commands/implement-story.md`, when the Invocation table is rewritten, then it gains `--full-pipeline`; the no-flag / `/implement-story story-N` row is the 2-spawn default (`coding-agent` + `evaluator-agent`); `--quick` and `--review-only` match Business Rules 3–4 (`coding-agent` only / `evaluator-agent` only); and the file contains no `--default` token. `[AC-2.1]`
- [ ] Given the same command file, when default-path spawn sites and the Pipeline table `Runs as` / `Skipped in` columns are rewritten, then Gate 1 and Gate 3 on the default path name only `coding-agent` and `evaluator-agent`; completeness and worktree-integration notes that list spawn gates name only those two on default; Gate 3 `Runs as` is `evaluator-agent` on default and `review-agent` on `--full-pipeline`; architecture-check, testing, visual-qa, and docs spawn only on `--full-pipeline` (visual-qa still also skipped with no visual refs); and `--full-pipeline` still names architecture-check, review, testing, visual-qa, and documentation. `[AC-2.2]`
- [ ] Given a per-story `evaluator_fail_count` starting at 0, when the evaluator FAILs once, then the command recodes via Gate 1 without AskQuestion; when a second consecutive evaluator FAIL increments the count to 2, then it prints one notice and treats the remainder of this story as `--full-pipeline` without AskQuestion; `--quick` never escalates (no evaluator); and `--review-only` FAIL ends the run with no recode spawn and no silent `--full-pipeline`. `[AC-2.3]`
- [ ] Given Stage 2b’s FAIL-only override still after Gate 3, when the Gate 3 agent returns, then `review-override.py` is still invoked; the residual sentence on the default path names `evaluator-agent` (and still names `review-agent` on `--full-pipeline`); script `fail` recodes and script `pass` does not wash an evaluator FAIL; and on default a `test-integrity.py` `fail` uses BLOCKED escalation with agent `coding-agent` restarting Gate 1, while `--full-pipeline` keeps `testing-agent` restarting Gate 4. `[AC-2.4]`
- [ ] Given Gate 0 / 4.5 / 5 bodies and `gates:` frontmatter, when the default path runs, then Gate 0 / 5 run the script only (`arch-check.py` / `docs-check.py`), Gate 4.5 is skipped (no visual-qa spawn even with visual refs), Gate 0 ADR-024 floor→anchor ABORT re-run and ABORT confirmation are `--full-pipeline` only, Gate 3 heading stays (no new gate numbers), `gates:` provenance is unchanged (`gate3_review` still `script: scripts/review-override.py`), and this story does not edit `scripts/review-override.py`, `scripts/eval.sh`, or `agents/review-agent.md`. `[AC-2.5]`

## Implementation Tasks

- [ ] 2.1 Write `scripts/tests/test_implement_story_default_path.py` (pytest, Python 3.9) that reads `commands/implement-story.md` as text and asserts: no `--default` token; Invocation table contains `--full-pipeline`; no-flag / `--quick` / `--review-only` spawn claims match the matrix; default-path `> **Agent:**` (or equivalent spawn) names only `coding-agent` and `evaluator-agent`; `--full-pipeline` still names architecture-check, review, testing, visual-qa, documentation; two-fail escalation prose exists and does not AskQuestion; Gate 4 default fail names `coding-agent` / Gate 1; `review-override.py` is still invoked; `gates:` frontmatter provenance is unchanged (`gate3_review` still `script: scripts/review-override.py`) `[AC-2.1, AC-2.2, AC-2.3, AC-2.4, AC-2.5]`
- [ ] 2.2 Rewrite the Invocation table and Pipeline table in `commands/implement-story.md` per `technical-spec.md` → `## 2. Default path + flags` → `### Invocation` and `spec.md` → `## Detailed Requirements` → `### Story 2 — Default path + flags` (no `--default`) `[AC-2.1, AC-2.2]`
- [ ] 2.3 Update default-path spawn sites (Gate 1 / Gate 3), completeness and worktree-integration notes, and the Gate 3 body: spawn `evaluator-agent` on default, skip on `--quick`, evaluator-only on `--review-only`, `review-agent` on `--full-pipeline`; keep the Stage 2b `review-override.py` invoke; residual sentence names `evaluator-agent` on default only `[AC-2.2, AC-2.4]`
- [ ] 2.4 Add two-fail escalation (`evaluator_fail_count`, first FAIL → Gate 1 recode, second FAIL → one `--full-pipeline` notice, no AskQuestion) and rewrite the Gate 4 default `test-integrity.py` `fail` BLOCKED template to `coding-agent` / restart Gate 1 (`--full-pipeline` keeps `testing-agent` / Gate 4) `[AC-2.3, AC-2.4]`
- [ ] 2.5 Rewrite Gate 0 / 4.5 / 5 default bodies to script-only / skip; leave Gate 0 ABORT confirmation and ADR-024 floor→anchor re-run as `--full-pipeline` only; do not change `gates:` provenance; do not edit `scripts/review-override.py`, `scripts/eval.sh`, or `agents/review-agent.md` `[AC-2.5]`
- [ ] 2.6 Verify acceptance criteria: `uv run --python 3.9 pytest scripts/tests/test_implement_story_default_path.py` green; confirm the locked matrix, two-fail notice, Gate 4 default recode, FAIL-only override invoke, and unchanged `gate3_review` script line `[AC-2.1, AC-2.2, AC-2.3, AC-2.4, AC-2.5]`

## Notes

**Depends on Story 1.** `agents/evaluator-agent.md` (and counterparts) must already exist. This story only rewrites `commands/implement-story.md` plus the command-prose test. Do not invent the evaluator file here.

**Owned file.** `commands/implement-story.md` only. Do not rewrite `scripts/review-override.py`. Do not add `--default`. Do not edit `scripts/eval.sh` or `agents/review-agent.md` (Story 3 owns spawn-cap + adapters + eval wiring).

**Scope index.** `spec.md` → `## Detailed Requirements` → `### Story 2 — Default path + flags`; `spec.md` → `## 📋 Business Rules` 1–7 and 9–10; `technical-spec.md` → `## 2. Default path + flags`; `technical-spec.md` → `## 5. Error & Rescue Map`; `technical-spec.md` → `## 7. Interaction Edge Cases` (`--quick` and two-fail; `--review-only` FAIL; Visual refs on default).

**Risks.** Residual “full SDLC” overview sentences in this command can relitigate the default if left as-is; change only lines this story owns. Completeness / worktree notes that still list five spawn gates will fail the default-path scan. Gate 3 heading must stay Gate 3.

## Definition of Done

- [ ] All tasks completed
- [ ] All acceptance criteria met
- [ ] Tests passing
- [ ] Code reviewed
- [ ] Documentation updated

## Context for Agents

- **Error map rows:** `sub-specs/technical-spec.md → ## 5. Error & Rescue Map`
- **Shadow paths:** `sub-specs/technical-spec.md → ## 6. Shadow Paths` `sub-specs/technical-spec.md → ## 2. Default path + flags (Story 2)` `sub-specs/technical-spec.md → ## 7. Interaction Edge Cases`
- **Business rules:** [No-flag is the default, `--full-pipeline` is the hatch, `--quick` skips the evaluator, `--review-only` skips coding, Two-fail auto-escalate only, No new gate numbers, FAIL-only override stands, Default Gate 4 has no testing-agent, Gate 0 ABORT confirmation is `--full-pipeline` only]
- **Experience:** [Happy path flow, State catalog]
