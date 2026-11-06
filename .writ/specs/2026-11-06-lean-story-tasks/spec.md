# Lean Story Tasks

> **Status:** Not Started
> **Created:** 2026-11-06
> **Owner:** @AdamSellke
> **Dependencies:** []
> **Origin:** Promoted from issue: `.writ/issues/improvements/2026-11-06-spec-tasks-over-prescribe.md`. Authored with `/create-spec`; decisions in [`recommendation-log.md`](recommendation-log.md).
> **Type:** Improvement. **Priority:** Normal. **Effort:** Medium.

## Specification Contract

**Deliverable:** `/create-spec` generates stories whose tasks name files, external contracts, and test/verification order. Tasks leave internal structure to the coding agent, rules are stated once, and stories carry no generic Definition of Done. A trial on one archived spec measures the effect.

**Must Include:** a mechanical check on task size in Step 2.6a, so the rule isn't advice the generator can ignore.

**Hardest Constraint:** `create-spec.md` (+14,169) and `verify-spec.md` (+10,818) are already over the command byte budget. Any growth needs a disclosed ledger entry in `test_governor_enforcement.py`, and the target is net-zero.

**🎯 Experience Design:**
- **Entry point:** `/create-spec`, `/edit-spec`, or `/implement-phase` (all run `user-story-generator`)
- **Happy path:** contract lock → stories generated → Step 2.6a passes task-size and AC checks
- **Moment of truth:** Story 1 of a typical spec reads in about half the words, and its ACs and Notes are unchanged in depth
- **Feedback model:** Step 2.6a names each over-long task. The story is regenerated once at `anchor`, and a second failure surfaces in Step 2.9.
- **Error experience:** a legacy story with a DoD still passes `/verify-spec`. A new story without one isn't flagged.

**📋 Business Rules:**
1. A task names the files it creates or changes, plus any external contract it fixes (CLI flags, file format, exit/reason codes, a function another story or spec calls). It does not prescribe internal signatures, helper names, formatter classes, or step order inside a function.
2. A task is at most 50 words, not counting its AC tag. Step 2.6a counts words, and a story with any longer task fails.
3. Probed facts, gotchas, and environment constraints go in Notes, not tasks.
4. A business rule is written once, in `spec.md` → Business Rules. The expanded section, technical-spec, and stories cite it by number and do not restate it.
5. New stories have no `## Definition of Done`. `/verify-spec` requires it only if present, and 3b checks it only if present. Legacy stories are left alone.
6. Tasks still name every file to be created (the coding-agent file-creation rule depends on it).

**Success Criteria:**
- Generator, Step 2.6a, and verify-spec changes ship with tests. Both pytest interpreters and `eval.sh` stay green, and `gen-platform-trees.py --check` is clean.
- Trial report: one archived spec's stories are regenerated under the new rules, and both versions are run through `/implement-story` in worktrees cut at the pre-implementation commit. The report compares story word count, drift-log entries, review findings, and gate outcomes. If the new version has more drift or more findings, the report says so; nothing reverts automatically.

**Scope Boundaries:**
- Included: `agents/user-story-generator.md`, `commands/create-spec.md` (Steps 2.4, 2.6, 2.6a, 2.8, Completion), `commands/verify-spec.md` (1d, 3b), byte-budget ledger, generated platform trees, trial report
- Excluded: rewriting existing or archived specs, changing `spec-lite.md` format, changing AC format or the 3–5/5–7 counts, the `spec-analyze` fixtures

**⚠️ Technical Concerns:**
- One trial spec is a sample of one, so it can show a regression but can't prove an improvement. The report says so.
- Running `/implement-story` twice costs real tokens. Pick a small archived spec (≤3 stories).

**💡 Recommendations:**
- Count words with a small function in an existing script (`ac-trace.py check` already parses task lines) instead of asking the orchestrator to count by hand.

**⚠️ Cross-Spec Overlap:**
- `2026-11-06-archived-dependencies-resolve` (Not Started) also edits `commands/verify-spec.md` (Check 3f) and its byte-budget ledger line. Different checks; whichever lands second rebases the ledger number.

## Evidence

Measured 2026-11-06 over every `user-stories/story-*.md` under `.writ/specs/` (2,827 task lines). Words per task exclude the `- [ ] N.M` prefix and the trailing AC tag.

| Spec month | Tasks | Median words | p90 | Over 50 words |
|---|---|---|---|---|
| 2026-03 | 361 | 19 | 33 | 1% |
| 2026-07 | 374 | 20 | 35 | 1% |
| 2026-08 | 843 | 25 | 50 | 9% |
| 2026-09 | 311 | 38 | 80 | 25% |
| 2026-10 | 563 | 36 | 69 | 25% |
| 2026-11 | 102 | 53 | 97 | 52% |

- The 50-word cap (Business Rule 2) is the p90 of specs written before September, when tasks were still short.
- **Drift does not track task length in the archive.** Across the 24 archived specs with a drift log, the correlation between median task words and `[DEV-` entries per story is r = −0.23. The two specs with the longest tasks (`2026-09-03-model-delegation`, `2026-09-05-phase11-repair-and-baseline`) logged no `[DEV-` entries, but their drift logs use a different format, so the count may be undercounted. This spec therefore does not claim lean tasks reduce drift. The trial (Story 5) tests it.
- **Restated rules do cause drift.** `2026-10-25-design-divergence` DEV-001: the AC, the technical spec, and the story Notes disagreed on the axis-catalog shape, and the coding agent had to pick one. Business Rule 4 targets this.

## 🎯 Experience Design

### User Journey

1. A spec author runs `/create-spec` (or `/edit-spec` adds stories, or `/implement-phase` authors a spec).
2. The orchestrator spawns `user-story-generator` per story with the new task rules.
3. Step 2.6a runs `ac-trace.py check`. Any `oversized_task` finding on a story counts as that story failing, alongside the existing count and tag checks.
4. A failing story is regenerated once at `anchor`. A second failure is listed in the Step 2.9 package review with the over-long task IDs and their word counts.
5. `/implement-story` reads the shorter tasks. The coding agent decides internal structure. The file list in the tasks still bounds what it may create.

### State Catalog

| State | What the author sees |
|---|---|
| All tasks ≤50 words | Step 2.6a passes. No new output. |
| A task over 50 words, first attempt | Story regenerated at `anchor`; Step 2.9 does not mention it if the retry passes |
| A task over 50 words after retry | Step 2.9 lists `story=N task N.M words=W` for each one; the package is still written |
| Legacy story with DoD | `/verify-spec` 1d passes; 3b checks the DoD as before for completed stories |
| New story with no DoD | `/verify-spec` 1d passes; 3b reports nothing for it |
| Completed or In Progress story with long tasks | No `oversized_task` finding (the check covers `Not Started` stories only) |

## 📋 Business Rules (Expanded)

Detail beyond the contract. The rules themselves are not restated; see the contract above.

- **Rule 1, external contract.** A detail is an external contract when something outside the story's own files depends on it: a CLI another command calls, a file another script reads, an exit or reason code a test or command matches, or a function the contract names as used by another story or spec. Everything else is internal.
- **Rule 1, file names.** Naming a file and saying what changes in it ("add the `verify-ledger.py` row to `.writ/docs/agent-cli-contract.md`") is allowed. Naming the helpers to write inside it is not.
- **Rule 2, counting.** Strip the leading `- [ ]` or `- [x]`, the `N.M` task number, and the trailing AC tag; split the rest on whitespace. Inline code counts as the words it contains.
- **Rule 2, scope.** `oversized_task` applies only to stories whose status is `Not Started`, so finished and in-flight work is never re-flagged. It is informational in `ac-trace.py` and never changes its exit code; Step 2.6a, not the script, makes it a regeneration trigger.
- **Rule 4, where rules live.** The contract's numbered list is the source. This expanded section adds detail per rule number. `technical-spec.md` and story Context for Agents cite "Business Rule N". A story task may cite a rule number; it may not paraphrase the rule.
- **Rule 5, legacy.** No migration. Existing stories keep their DoD, and `/revert`'s "uncheck the DoD list" step still applies to them.

## Detailed Requirements

- `scripts/ac-trace.py check` adds the informational finding `oversized_task`, with `story`, `file`, `line`, and a `detail` holding the task number and word count. Schema stays `ac-trace-check-v1`; a new code is additive.
- `.writ/docs/acceptance-criteria-ids.md` → Finding Codes lists `oversized_task`.
- `agents/user-story-generator.md`: task rules state Business Rules 1, 2, 3, and 6, and the template drops `## Definition of Done`. The Implementation Tasks quality guideline says the same. The Context for Agents business-rule hint cites rule numbers.
- `commands/create-spec.md`: Step 2.6's story-contents sentence drops the definition of done; Step 2.6a item 2 counts `oversized_task` as a failure; Step 2.9 lists a second failure's over-long tasks (this follows from the Step 2.6a change, though the contract's Included list doesn't name Step 2.9); Step 2.4's business-rules bullet and Step 2.8 say to cite rule numbers, not restate; Completion item 3 is unchanged except for any DoD mention.
- `commands/verify-spec.md`: Check 1d no longer requires Definition of Done; Check 3b runs only when the section exists.
- Generated platform copies (`claude-code/agents/writ-story-gen.md`, `cursor/plugin/...`) are regenerated with `scripts/gen-platform-trees.py`.
- `scripts/tests/test_governor_enforcement.py` → `KNOWN_OVER_BUDGET` gets a dated, disclosed entry for any byte change to `create-spec.md` or `verify-spec.md`.
- The trial writes `trial-report.md` in this spec folder.

## Implementation Approach

- Story 1 adds the finding to `ac-trace.py` first, so later stories have a working check to cite.
- Stories 2–4 change prose in the generator and two commands, each with an eval or pytest assertion pinning the new wording, and each regenerating platform trees.
- Story 5 runs the trial in temporary git worktrees outside the main checkout (CLAUDE.md: `git worktree` changes in the same checkout while pytest runs break `test_smoke_leaves_repo_unchanged`; run the trial when no pytest run is in flight).
- Stories run in order: 2, 3, and 4 all edit `agents/user-story-generator.md` and `commands/create-spec.md`.
