# Story 6: The Eighteen Missing Completion Sections

> **Status:** Complete
> **Priority:** High
> **Dependencies:** Story 2, Story 3, Story 4, Story 5

## User Story

**As a** maintainer or agent finishing a Writ command run
**I want to** the eighteen commands with no `## Completion` section to declare their terminal condition and, where it applies, their terminal constraint
**So that** an agent knows when to stop rather than volunteering the next step, and `## Completion` coverage goes from 13/31 to 31/31

## Scope

Eighteen commands: `assess-spec`, `implement-spec`, `implement-story`, `initialize`, `migrate`, `prototype`, `refactor`, `refresh-command`, `reinstall-writ`, `release`, `retro`, `revert`, `security-audit`, `ship`, `status`, `uninstall-writ`, `update-writ`, `verify-spec`.

Each section is placed immediately before the file's final `## References` section — and before the `---` horizontal rule where one precedes it — matching the placement in all 13 incumbent files.

## Acceptance Criteria

- [x] Given 13 of 31 commands carry `## Completion` today, when this story lands, then `grep -l '^## Completion' commands/*.md | wc -l` returns 31, with exactly one such heading per file.
- [x] Given the placement rule, when each new section's line number is compared to its file's last `^## References` heading, then the section appears before it, and before any `---` rule that immediately precedes References.
- [x] Given Business Rule 4, when each new section is measured from its heading to the next `## ` heading, then it is at most 14 lines including blank lines and any trailing separator — under the 15–16 median of the 13 incumbents.
- [x] Given Business Rule 7, when each new section is read against the `exit_criteria` already in the same file's frontmatter (from Stories 2–5), then every `exit_criteria` entry is traceable to something the section also asserts, and neither contradicts the other.
- [x] Given the hardest constraint, when the eighteen sections are read as a set, then no two are structurally interchangeable — each names its own command's artifact, its own zero-result or failure mode where one exists, and its own terminal constraint where the command produces something an agent might otherwise volunteer to act on.
- [x] Given Business Rule 10, when `git diff` is read, then the only additions are the eighteen sections — no frontmatter changes (those landed in Stories 2–5), no `scripts/` changes, no command body prose rewritten.
- [x] Given this is the last story to touch `commands/`, when the aggregate line budget is measured, then `git diff --stat <base>..HEAD -- commands/ agents/` reports at most **518** added lines, with the actual number recorded in this story's evidence.

## Implementation Tasks

- [x] 6.1 Confirm Stories 2–5 have landed and every command's frontmatter carries `exit_criteria` — this story derives from those and cannot start before them
- [x] 6.2 Read the reference incumbents `commands/review.md` and `commands/new-command.md` for shape, and the `## Completion` guidance in `.writ/docs/component-contract.md` (Story 1)
- [x] 6.3 For each of the eighteen, read its `exit_criteria` and its Command Process, and write a one-sentence success condition naming the artifact or state produced
- [x] 6.4 Add, where applicable, the zero-result sentence (stating that a null or empty outcome is valid rather than an error) and the **Terminal constraint** line stating what the command does not do next — `ship`, `release`, `revert`, `security-audit`, `retro`, and `status` are the strongest candidates for a terminal constraint
- [x] 6.5 Insert each section immediately before the final `## References` (and before any preceding `---` rule); verify exactly one `^## Completion` per file and that its line number is below the last `^## References`
- [x] 6.6 Measure each new section heading-to-next-heading; any section over 14 lines is cut, not exempted. Cross-check each against the file's own `exit_criteria` for contradiction (BR7)
- [x] 6.7 Run the aggregate budget measurement (`git diff --stat` for `commands/` and `agents/`), record the number, and run `bash scripts/eval.sh` plus `bash scripts/check-agent-parity.sh` for regressions

## Notes

**Technical considerations:**

- This story is sequenced after Stories 2–5 for two reasons, and the second matters more than the first. Mechanically, 17 of these 18 files are also edited by those stories, so parallel execution guarantees merge conflicts across worktrees. Substantively, Business Rule 7 requires each section to be checked against `exit_criteria` that only exists once those stories land.
- Frontmatter and `## Completion` are not redundant. The frontmatter holds the machine-checkable assertions; the section holds what does not fit a YAML string — outcome interpretation tables, the statement that zero findings is a valid result, and the terminal constraint that stops an agent from offering to implement what it just specified.
- `commands/review.md`'s incumbent section is the model: one sentence naming the exact path and required sections, an outcome-interpretation table, and an explicit "zero findings is a valid outcome, not an error."
- A **terminal constraint** is the highest-value line here and the least likely to be written unprompted. `commands/new-command.md`'s reads: *"This command produces a command definition. Do not offer to implement, build, or execute what was defined."* `/ship` stops at an opened PR. `/security-audit` stops at findings. `/retro` stops at a document. Each of those is a place an agent will otherwise volunteer.
- A 6-line accurate section beats a 14-line padded one. The ceiling is a ceiling, not a target.

**Risks / challenges:**

- Eighteen sections written in one pass is the single strongest boilerplate pressure in the spec. By the tenth file the template is set and the last eight get filled in. Mitigation: write the eighteen success conditions first (Task 6.3) as a batch and compare them against each other before writing any full section.
- `implement-story.md` (961), `verify-spec.md` (711), `release.md` (626), and `ship.md` (613) are large. The insertion point is unambiguous — before the final `## References` — but locating it requires reading to the end of the file, not searching for the first `## References`-like string.
- Some of the 18 have a `---` rule immediately before `## References` and some do not. Check per file rather than assuming.
- This story carries the aggregate budget measurement. If it comes in over 518, the correct response is to cut sections and criteria, not to raise the budget.

**Integration points:**

- Depends on all four batch stories' `exit_criteria` (BR7).
- `2026-08-11-governor-instrumentation` adds a blocking `structural` check for `## Completion` presence in all 31 commands; this story is what makes that check landable non-red.
- ADR-020's enforcement-sequencing note (warnings first, blocking after compliance) depends on this story completing before that flip.

**Measured evidence (2026-08-11):**

`git diff --shortstat d373a6e -- commands/ agents/` → **38 files changed, 392 insertions(+), 0 deletions(-)**. Against the 518 aggregate ceiling, that is 126 lines of headroom.

| Surface | Ceiling | Measured |
|---|---|---|
| Command frontmatter (31 files) | 217 | 187 — 6 lines on 30 files, 7 on `implement-phase` |
| Agent config blocks (7 files) | 49 | 42 — 6 lines each |
| New `## Completion` sections (18) | 252 | 144 — 8 added lines each, measuring 10 heading-to-next-heading |
| `new-command.md` authoring-template edits (Story 1) | n/a | 19 |
| **Total** | **518** | **392** |

All 18 new sections measure **10 lines** heading-to-next-`## `, against the 14-line ceiling and the 15–16 incumbent median — verified with the same `awk` measurement that reproduces the spec's incumbent table (`review` 16, `new-command` 15, `knowledge` 12, `design` 18). Coverage: `grep -l '^## Completion' commands/*.md | wc -l` → **31**, exactly one heading per file, every one placed before its file's last `^## References`.

`bash scripts/eval.sh` → `Findings: 0, Run errors: 0`, identical to the pre-spec baseline. `bash scripts/check-agent-parity.sh` → `parity OK`.

**Note on the leanness warnings.** `eval.sh`'s leanness check emits non-blocking `WARNING` lines for `commands` (+390) and `agents` (+42) growth against `.writ/leanness-baseline.json`. These are notes, not findings — the run still reports `Findings: 0`. The baseline was deliberately left unedited: ADR-020's enforcement-sequencing note anticipates exactly this warnings-first state, and re-baselining is outside this spec's declared edit surface.

## Definition of Done

- [x] All tasks completed
- [x] All acceptance criteria met
- [x] 31/31 `## Completion` coverage verified by grep
- [x] Every new section ≤14 lines and consistent with its file's `exit_criteria`
- [x] Aggregate added-line count measured, recorded, and at or under 518
- [x] `bash scripts/eval.sh` and `bash scripts/check-agent-parity.sh` show no regressions

## Context for Agents

- **Business rules:** [BR1 swap test, BR4 line budget (14 lines per new section, 518 aggregate), BR7 no contradiction with `exit_criteria`, BR9 no eval checks, BR10 no substance rewrite] — from spec.md → 📋 Business Rules
- **Detailed requirements:** [`## Completion` section shape; The 18 commands missing `## Completion`] — from spec.md → ## Detailed Requirements
- **Technical concerns:** [Authoring under time pressure produces fields technically present and informationally empty] — from spec.md → ## Technical Concerns
- **Contract:** [Hardest constraint: the 18 missing `## Completion` sections are written, not templated] — from spec.md → ## Contract (Locked)
- **Technical spec:** [`## Completion` section shape; Placement Rules; Line Budget Arithmetic (incumbent measurements); Error & Rescue Map → Insert `## Completion`] — from sub-specs/technical-spec.md
