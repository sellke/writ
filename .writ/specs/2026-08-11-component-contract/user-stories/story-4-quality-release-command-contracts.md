# Story 4: Quality and Release Command Contracts

> **Status:** Complete
> **Priority:** High
> **Dependencies:** Story 1

## User Story

**As a** maintainer taking work from green branch to tagged release
**I want to** each of the seven quality and release commands to declare its own problem, outcome, and exit criteria
**So that** commands whose only artifact is a report stop asserting "a report was produced" and start asserting what the report contains

## Scope

Seven commands: `review`, `verify-spec`, `security-audit`, `retro`, `ship`, `release`, `status`.

Only `review` carries a `## Completion` section today. The other six belong to Story 6.

## Acceptance Criteria

- [x] Given all seven files carry `---` frontmatter with `name` and `description` and no `problem:`, when this story lands, then each carries `problem:`, `outcome:`, and `exit_criteria:` in the fixed key order, with 2–4 `exit_criteria` entries.
- [x] Given four of the seven (`review`, `security-audit`, `retro`, `status`) produce a report as their primary artifact, when their `exit_criteria` are read, then no entry stops at "a report exists" — each names the report's path **and** a structural property of its contents (a required section, a classification, a count).
- [x] Given `ship` and `release` cross the production boundary, when their `exit_criteria` are read, then each names a git- or `gh`-observable fact (an open PR whose head is the current branch, a tag matching `v<VERSION>`, a changelog heading for `<VERSION>`), not an intention.
- [x] Given Business Rule 1, when any entry is pasted into another command in this batch, then it reads as false or nonsensical there. `review` / `security-audit` and `verify-spec` / `status` are the two adjacent pairs and must be checked explicitly against each other.
- [x] Given Business Rule 2, when any entry is compared against its own file's `description:`, then it asserts something the description does not already say.
- [x] Given Business Rule 4, when each file is diffed, then frontmatter grew by at most 7 lines, and `grep -c '^---$'` still returns exactly 2.
- [x] Given Business Rules 9 and 10, when `git diff --name-only` is read, then it lists only these seven files — no `scripts/` changes, no `## Completion` sections added, no command body prose rewritten.

## Implementation Tasks

- [x] 4.1 Read `.writ/docs/component-contract.md` (Story 1) and `commands/new-command.md`'s own frontmatter as the worked exemplar
- [x] 4.2 For each of the seven, identify the terminal artifact and its structural properties — report paths under `.writ/state/` or `.writ/retros/`, `VERSION`, `CHANGELOG.md`, git tags, PR state
- [x] 4.3 Author `problem:` and `outcome:` for all seven as single sentences; swap-test the `review` / `security-audit` pair and the `verify-spec` / `status` pair against each other first
- [x] 4.4 Author 2–4 `exit_criteria` per command; for the four report-producing commands, pair every path with a content assertion — a bare path is not an assertion (technical-spec.md → Anti-pattern to reject in review)
- [x] 4.5 Run the restatement test on every entry against its own `description:`
- [x] 4.6 Verify per file: ≤7 added frontmatter lines, `grep -c '^---$'` = 2, key order correct
- [x] 4.7 Run `bash scripts/eval.sh`; confirm no new findings and no `scripts/` changes; record any scoping defect surfaced in the Notes without acting on it

## Notes

**Technical considerations:**

- Report-producing commands are the single richest source of boilerplate in this spec. "The report is generated" is plausible for `review`, `security-audit`, `retro`, `research`, `status`, and `verify-spec` simultaneously — six commands, one worthless sentence. The fix is not better phrasing; it is naming a structural property of the specific report.
- `commands/review.md`'s existing `## Completion` section is the best incumbent example in the repo: it names the exact path, the required sections, and states explicitly that a zero-findings review is a valid outcome rather than an error. Derive its `exit_criteria` from that section (BR7) and use its shape as this batch's model.
- `/release` is 626 lines with a gate, changelog generation, version bump, tag, and optional GitHub release. Its criteria should assert the durable end state — `VERSION` changed, tag exists, changelog section exists — not the gate steps along the way.
- `/status` is explicitly a sub-10-second orientation command. A criterion asserting exhaustive analysis would contradict the command's own design; the honest observable is which state sources it read and reported on.
- `/verify-spec` auto-fixes some findings. Its criteria should distinguish auto-fixed from recorded-but-unfixable, since "all checks pass" and "all checks pass or are recorded" are different claims.

**Risks / challenges:**

- `release.md` (626), `ship.md` (613), and `security-audit.md` (513) are large. Budget the read; skimming produces exactly the boilerplate this batch is most prone to.
- `/ship` and `/release` are the production-boundary commands under ADR-022 and the Prime Directive. Nothing in this story changes their gates — the fields are declarative only, and a criterion must never read as authorization to skip a human gate.
- `/retro` produces a document derived from git history over a period. Its observable is the document plus the period it covers, not a quality judgment about the retrospective.

**Integration points:**

- Story 6 writes `## Completion` for six of these seven and will read the `exit_criteria` this story authors.
- `2026-08-11-governor-instrumentation` consumes these fields; `/verify-spec` and `/refresh-command` are named in ADR-020 as the eventual consumers of `exit_criteria` as a declared target.

## Definition of Done

- [x] All tasks completed
- [x] All acceptance criteria met
- [x] Every report-producing command's criteria pair a path with a content assertion
- [x] `bash scripts/eval.sh` shows no new findings
- [x] No criterion reads as authorization to bypass a human gate

## Context for Agents

- **Business rules:** [BR1 swap test, BR2 restatement test, BR3 observable requirement, BR4 line budget, BR5 one-line fields, BR7 no contradiction with `## Completion`, BR9 no eval checks, BR10 no substance rewrite] — from spec.md → 📋 Business Rules
- **Detailed requirements:** [The contract schema; Command batching → Quality & release] — from spec.md → ## Detailed Requirements
- **Technical concerns:** [`exit_criteria` is only nominally machine-checkable — the value is forcing a falsifiable condition] — from spec.md → ## Technical Concerns
- **Contract:** [Hardest constraint: machine-checkable assertions, not restated descriptions] — from spec.md → ## Contract (Locked)
- **Technical spec:** [Authoring `exit_criteria` — worked examples (`/release`, `/ship`, `/verify-spec` rows); Anti-pattern to reject in review] — from sub-specs/technical-spec.md
