# Story 2: Move Documentation Out — Five Base Sections Relocated to .writ/docs/ With Ledger Rows and a Measured Byte Count

> **Status:** Not Started
> **Priority:** High
> **Dependencies:** Story 1

## User Story

**As a** Writ maintainer pruning the shared base
**I want to** move the five documentation-class sections out of `system-instructions.md` into `.writ/docs/`, each behind at most one pointer line, one commit per section with its ledger rows
**So that** the base shrinks toward the 10,000-byte cap without losing any content, and Story 3 starts its cut from a measured, recorded byte count

## Acceptance Criteria

> **AC IDs assigned through:** AC-2.5

- [ ] Given the base at the start of Story 2 (`## Model Tiers` + `### entry_level`, `### required_skills: frontmatter convention`, `### Skill authoring`, `## Startup Update Awareness`, and the tutorial portion of `### Recommendation Semantics` all present in `system-instructions.md`), when all five move commits have landed, then none of those five sections' body text remains in `system-instructions.md` or `commands/_preamble.md`, each is present in a `.writ/docs/` file (new or merged into an existing doc already covering the topic), and each leaves behind at most one pointer line of the form `See .writ/docs/<file> for <topic>.` `[AC-2.1]`
- [ ] Given each of the five move commits in turn, when `python3 scripts/prune-ledger.py check --repo .` runs against that commit, then it exits 0, every removed line from that commit has a ledger row in `.writ/decision-records/pruned-instructions-ledger.md` dated that commit's date with class `moved` and a reason naming the destination `.writ/docs/` path, and the ledger row lands in the same commit as the removal `[AC-2.2]`
- [ ] Given the base after all five sections have moved, when `bash scripts/eval.sh` runs, then `check_referenced_paths` resolves every new `.writ/docs/` pointer link and `check_prime_directive_sync` reports `cursor/writ.mdc` still byte-identical to `system-instructions.md`'s Prime Directive block `[AC-2.3]`
- [ ] Given `python3 scripts/prune-ledger.py measure --repo .` run after the fifth commit, when its byte total is compared to the pre-Story-2 measurement taken in task 2.1, then the post-move total is recorded in Story 2's What Was Built and in a `{date} stage-2: ...` decision-log line, and it is at most 16,000 bytes `[AC-2.4]`
- [ ] Given the pinned Stage 1 closeout commit `cf84742`, when every line still present in `system-instructions.md` and `commands/_preamble.md` after Story 2 is diffed against that commit, then the diff of kept lines is empty — no kept line was reflowed, rewrapped, or reworded during the move `[AC-2.5]`

## Implementation Tasks

- [ ] 2.1 Run `python3 scripts/prune-ledger.py measure --repo .` and record the before-move byte total for `system-instructions.md` + `commands/_preamble.md`; list the current contents of `.writ/docs/` and, for each of the five sections, decide new-file vs. merge-into-existing-doc (checking `model-tiers.md` and `skills.md` in particular, both of which already exist and already cover adjacent ground) `[AC-2.1, AC-2.4]`
- [ ] 2.2 Move `## Model Tiers` + `### entry_level` (4,519 bytes) into `.writ/docs/model-tiers.md` (existing file — merge rather than create; it already states the normative text lives in `system-instructions.md` → Model Tiers, so that claim moves with the content), leave one pointer line in the base, add the ledger row(s) with class `moved`, and land it as one commit `[AC-2.1, AC-2.2, AC-2.5]`
- [ ] 2.3 Move `### required_skills: frontmatter convention` (2,809 bytes) and `### Skill authoring` (458 bytes) into `.writ/docs/skills.md` (existing file — it already documents the `required_skills:` convention and skill authoring in detail; reconcile rather than duplicate), leave one pointer line in the base for the `## Skills` section, add the ledger rows with class `moved`, and land it as one commit `[AC-2.1, AC-2.2, AC-2.5]`
- [ ] 2.4 Move `## Startup Update Awareness` (3,784 bytes) into `.writ/docs/startup-update-awareness.md` (new file), leave one pointer line in the base that preserves the one-line trigger `update.sh` may read, add the ledger row with class `moved`, and land it as one commit `[AC-2.1, AC-2.2, AC-2.5]`
- [ ] 2.5 Move the tutorial portion of `### Recommendation Semantics` (~1,875 bytes) into `.writ/docs/recommendation-semantics.md` (new file), leaving the rule sentence itself in the base plus one pointer line to the tutorial, add the ledger row with class `moved`, and land it as one commit `[AC-2.1, AC-2.2, AC-2.5]`
- [ ] 2.6 Verify: `python3 scripts/prune-ledger.py check --repo .` exits 0 at HEAD; `bash scripts/eval.sh` reports `Findings: 0` with `check_referenced_paths` and `check_prime_directive_sync` both green; `python3 scripts/prune-ledger.py measure --repo .` run again for the after total, recorded in What Was Built and in a `{date} stage-2: ...` decision-log line naming the before/after byte counts so Story 3 knows its depth `[AC-2.3, AC-2.4]`

## Notes

**Byte-identical kept lines.** Business Rule 5 diffs every kept line against `cf84742`. A section move must delete the section's lines wholesale and add a single pointer line — never reflow the paragraph above or below the cut to "read better." If a neighboring line looks awkward after the cut, leave it; smoothing it is Story 3's job at best, and doing it here would fail `prune-ledger.py check`'s removal detection (a reflowed kept line reads as a removal with no ledger row).

**Pointer line wording.** `See .writ/docs/<file> for <topic>.` — one line, no elaboration. `check_referenced_paths` in `scripts/eval.sh` resolves `.md` paths named in the base, so the path must be exact and relative-correct from the base file's location.

**Startup Update Awareness may be read by `update.sh`.** The technical spec (§3) flags this section as possibly consumed at runtime by the install/update path, not just by a human reading the base. Confirm whether `scripts/update.sh` (or `scripts/install.sh`) greps or references any text inside this section before cutting it down to a pointer; if it does, the one-line trigger it depends on stays in the base verbatim rather than moving, and only the surrounding explanation moves.

**Merge before create.** `.writ/docs/model-tiers.md` and `.writ/docs/skills.md` already exist and already cover much of what `## Model Tiers` and `## Skills` describe (confirmed by reading both files during story generation: `model-tiers.md` states the normative contract lives in the base, and `skills.md` already documents `required_skills:` frontmatter and skill authoring in full). Task 2.2 and 2.3 reconcile the moved base text into these existing docs rather than creating near-duplicate new files — check for overlap and fold in, don't append redundantly.

**One commit per section (Business Rule 4, Recommendation).** Each of tasks 2.2–2.5 is its own commit carrying both the base-file edit and the matching ledger rows, so a single bad move is a single revertable commit and `prune-ledger.py check` stays green at every commit on the branch, not only at story close.

**Integration with Story 3.** Story 3 classifies and cuts everything that remains after this story, starting from the byte count this story records — Business Rule 6 requires the measurement to happen between the move and the cut, not be estimated. Integration with Story 5: the revert path (spec.md §"Revert path") resolves this story's completion commits as a contiguous range if Stage 5's baseline re-run comes up short, so keeping each move as a clean, self-contained commit (task 2.2–2.5) keeps that range resolvable.

## Definition of Done

- [ ] All tasks completed
- [ ] All acceptance criteria met
- [ ] Tests passing
- [ ] Code reviewed
- [ ] Documentation updated

## Context for Agents

- **Error map rows:** spec.md → `## 🎯 Experience Design` → Error experience → "A removal without a ledger line: `eval.sh` blocks naming the file and the missing text"; "A kept line accidentally reflowed: it shows as a removal without a ledger line, which is the intended behavior"
- **Shadow paths:** spec.md → `## 🎯 Experience Design` → State catalog → "moves in progress (bytes falling, every commit green)"; technical-spec.md → `## 3. Move targets (Story 2)` → the merge-vs-new-file decision per section
- **Business rules:** spec.md → `## 📋 Business Rules` → 2 (ledger append-only), 3 (removed includes moved — reason class `moved`), 4 (ledger entries land in the same commit as the removal), 5 (kept lines stay byte-identical, diffed against `cf84742`), 6 (moves before cuts, measured between), 8 (Prime Directive mirror stays byte-identical), 12 (decision-log line format)
- **Experience:** spec.md → `## 🎯 Experience Design` → Happy path step (2) ("Story 2 moves five documentation sections out, one commit per section, each commit carrying its ledger lines; the check reports bytes after each")
- **Requirements:** spec.md → `## Detailed Requirements` → `### Story 2 — Move documentation out`; technical-spec.md → `## 3. Move targets (Story 2)` (byte counts per section, target files, pointer-line format, expected ~15,000-byte total)
- **Codebase:** `/Users/asellke/Projects/writ/system-instructions.md` (section line ranges: `## Model Tiers` at line 269, `### entry_level` at 302, `### required_skills: frontmatter convention` at 228, `### Skill authoring` at 263, `## Startup Update Awareness` at 175, `### Recommendation Semantics` at 83); `/Users/asellke/Projects/writ/.writ/docs/model-tiers.md` and `/Users/asellke/Projects/writ/.writ/docs/skills.md` (existing docs to merge into); `scripts/prune-ledger.py` (Story 1) `check` and `measure` subcommands; `scripts/eval.sh` → `check_referenced_paths`, `check_prime_directive_sync`
