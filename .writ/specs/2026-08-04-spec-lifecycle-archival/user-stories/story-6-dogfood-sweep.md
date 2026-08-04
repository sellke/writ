# Story 6: Dogfood the Sweep Against This Repo

> **Status:** Not Started
> **Priority:** Medium
> **Dependencies:** Story 2

## User Story

**As a** Writ maintainer
**I want to** run the real `/status --archive` sweep against this repo's 39 production spec folders and capture verifiable evidence that at least one eligible spec moves correctly
**So that** Success Criteria 2 and 3 are proven against real data — not fixtures — confirming the archive mechanism works end-to-end and leaves the command suite unbroken

## Acceptance Criteria

- [ ] Given Story 2's archive sweep mechanism is merged and functional, when `/status --archive` (or its direct `scripts/archive-sweep.py` equivalent) runs against this repo's real `.writ/specs/` corpus, then at least one genuinely Complete spec with matching `.writ/knowledge/` evidence is moved via `git mv` to `.writ/specs/archive/<name>/`, and the terminal summary reports a non-zero archived count with a named skip count for Complete specs lacking knowledge evidence.
- [ ] Given a spec is archived during the dogfood run, when `.writ/specs/archive/LEDGER.md` is inspected, then one append-only line exists recording the spec folder name, the knowledge entry filename(s) that supplied eligibility evidence, and an ISO 8601 timestamp — and the cited knowledge entry's `related_artifacts` frontmatter genuinely references that spec's folder name (no false-positive match).
- [ ] Given at least one spec now lives under `.writ/specs/archive/<name>/`, when spot-checking the moved folder, then (a) all files remain fully readable at the new path, (b) `git log --follow -- .writ/specs/archive/<name>/spec.md` surfaces the spec's full pre-move history, and (c) any existing issue `spec_ref` or ADR `Amends:`/`Extends:` pointer that references the archived spec still makes sense to a human reader even though the literal path text was not rewritten (Business Rule 4 — confirm no confusing dead ends, not that rewriting occurred).
- [ ] Given `.writ/specs/archive/` is now populated after the sweep, when `/status`, `create-spec`'s Step 1.3b overlap check, `implement-spec`'s spec-selection listing, and `verify-spec` (default and `--all`) each run, then all behave correctly with no regression — archived specs are excluded from active scans via single-level glob nesting alone, and no command errors or misclassification from the archive folder's presence.
- [ ] Given the dogfood run completes, when this story's `## What Was Built` section is filled in, then it records which spec(s) were archived, why each was eligible (status + knowledge evidence), and the results of all four verification spot-checks — serving as the spec's concrete acceptance evidence for Success Criteria 2 and 3.

## Implementation Tasks

- [ ] 6.1 **Pre-flight inventory (before running the sweep):** With Story 1's detector active, enumerate all 39 real `.writ/specs/*/spec.md` files and cross-reference against `.writ/knowledge/{decisions,conventions,glossary,lessons}/*.md` `related_artifacts` to predict which specs are archive-eligible; document the predicted set and manually verify at least one predicted match is genuinely Complete + knowledge-cited (guards against false-positive folder-name substring matches before irreversible `git mv`).
- [ ] 6.2 **Run the real sweep:** Execute `/status --archive` (or `python3 scripts/archive-sweep.py` if that is the documented invocation path) against this repo — not a temp fixture — and capture terminal output (archived count, skipped count, any per-spec failures or collisions).
- [ ] 6.3 **Verify archive artifacts:** Confirm each archived spec exists at `.writ/specs/archive/<name>/` with unchanged internal content; inspect `.writ/specs/archive/LEDGER.md` for correct one-line-per-move entries naming the citing knowledge file(s); confirm `git status` shows the moves as renames, not delete+add pairs.
- [ ] 6.4 **Spot-check history and inbound references:** For each archived spec, run `git log --follow` on its `spec.md`; grep issues and ADRs for pointers to the old path and confirm a human reader can still resolve intent (path text unchanged per Business Rule 4 — document any pointer that reads confusingly as a finding, not a fix request).
- [ ] 6.5 **Write a post-sweep regression assertion script** (e.g. `scripts/tests/test_archive_dogfood.py` or an `eval.sh` scenario): assert `/status` active-spec detection excludes `archive/`, `create-spec` overlap scan excludes archived specs, `implement-spec` listing excludes them, and `verify-spec --all` does not visit `archive/` — all against this repo's real post-sweep tree; run and capture pass/fail output.
- [ ] 6.6 **Manual command smoke tests:** Run `/status` (no flag), skim `create-spec`'s overlap-check behavior against the current corpus, and confirm `implement-spec` and `verify-spec` spec enumeration still function — note any unexpected surfacing of archived specs as active candidates.
- [ ] 6.7 **Record acceptance evidence:** Populate this story's `## What Was Built` section with archived spec name(s), eligibility rationale (status header + knowledge entry cross-reference), ledger excerpt, spot-check outcomes (readability, `git log --follow`, pointer sanity, command-suite regression results), and any deviations or skipped specs — this section is the spec's own proof artifact for Success Criteria 2 and 3.

## Notes

**This is not a fixture test.** The entire point is running the shipped mechanism against this repo's real 39 spec folders (~27 Complete once Story 1 lands) and 12 `.writ/knowledge/` entries. Unit tests in Story 2 validate the reducer; this story validates production reality.

**Depends on Story 2 being fully functional.** Do not run the dogfood sweep until `scripts/archive-sweep.py`, `commands/status.md --archive`, and Story 2's tests pass. Story 1 must also be merged — eligibility requires correct Complete classification.

**False-positive risk on knowledge matching.** The folder-name substring heuristic (`spec.md` → `## Technical Concerns`) can theoretically match unrelated artifacts sharing a slug fragment. Before treating the run as successful, manually confirm the ledger-cited knowledge entry's `related_artifacts` genuinely references the archived spec — not a coincidental substring hit.

**Business Rule 4 is a sanity check, not a fix.** Issue `spec_ref` and ADR `Amends:`/`Extends:` pointers are intentionally not rewritten. The spot-check confirms humans can still understand references; it does not require building pointer-rewrite logic.

**Partial sweep is acceptable.** If some eligible specs fail `git mv` (dirty tree, collision), the sweep continues per Story 2's error handling — document failures in What Was Built; success requires at least one real archive, not a perfect sweep of every eligible spec.

**This repo does not run `install.sh` on itself.** Story 4's `.cursorindexingignore` seeding may not yet exist in this repo's root — that is out of scope for this story's verification (Story 4 owns install scaffolding; this story owns sweep + command-suite regression).

**Risks:**

- Running against real data moves real git-tracked folders — ensure working tree is clean enough and changes are intentional before committing.
- Archiving a spec still referenced as "active" in a maintainer's mental model could cause brief confusion — mitigated by ledger audit trail and reversibility via `git mv` back.
- If zero specs are eligible (no knowledge cross-references yet), the story cannot satisfy Success Criterion 2 — pre-flight inventory (Task 6.1) surfaces this blocker early; may require adding or confirming a knowledge entry cites a Complete spec before proceeding.

## Definition of Done

- [ ] All tasks completed
- [ ] All acceptance criteria met
- [ ] Tests passing
- [ ] Code reviewed
- [ ] Documentation updated

---

## What Was Built

_(To be populated during implementation with dogfood run evidence: archived spec(s), eligibility rationale, ledger entries, spot-check results, and command-suite regression outcomes.)_

## Context for Agents

- **Error map rows:** []
- **Shadow paths:** [Happy path — real spec archived] — `spec.md` → `## Success Criteria` (items 2 and 3)
- **Business rules:** [Eligibility = Complete status AND cited by knowledge evidence, Every move is a plain reversible git mv, Archived specs stay fully addressable]
- **Experience:** [Moment of Truth (real sweep, references still resolve)] — `spec.md` → `## 🎯 Experience Design` → `### Moment of Truth`
