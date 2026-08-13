---
name: edit-spec
description: "Modify an existing spec contract-first - agree on a modification contract before any file changes, preventing scope surprises."
problem: "Changing a spec mid-flight quietly destroys completed work — tasks get rewritten, stories disappear, and afterwards nobody can tell what changed or how to get back."
outcome: "An existing spec folder reflects an agreed modification, with the pre-edit state preserved under backups/ and the change recorded in that spec's CHANGELOG.md."
exit_criteria:
  - "backups/<timestamp>/ holds the pre-edit copy of every file the modification touched"
  - "the spec's CHANGELOG.md gained an entry naming the change type, the files updated, and the backup location"
  - "no story file was deleted — stories dropped from scope are present under user-stories/archived/"
---

# Edit Spec Command (edit-spec)

## Overview

Modify existing specifications using a contract-first approach. No files change until the developer and AI agree on a modification contract through structured clarification. This prevents assumptions and scope surprises.

## Invocation

| Invocation | Behavior |
|---|---|
| `/edit-spec` | Interactive — select spec from `.writ/specs/` |
| `/edit-spec "user-auth"` | Edit named spec (partial match supported) |
| `/edit-spec "user-auth" "add biometric"` | Edit with change description pre-loaded |

## Command Process

### Phase 1: Understand the Change (No File Modifications)

**Guiding principle:** Deliver the updated spec package only after both sides agree on the modification contract. Challenge changes that could break existing work or create technical debt — surface concerns early.

#### Step 1.1: Load Current State

If no spec argument, present spec selection from `.writ/specs/` showing name, story count, completion percentage.

Once selected, read the full spec package: `spec.md`, all story files, sub-specs, and `user-stories/README.md`. Scan the codebase for implementation progress.

Present a concise current state summary: story count, completion status, which stories are in-progress.

#### Step 1.2: Classify the Change

If the user described their change upfront, analyze it and skip to Step 1.3.

Otherwise, ask two structured questions:
1. **Change type** — adding features, modifying existing stories, removing scope, reorganizing stories, changing technical approach, or multiple
2. **Change scope** — single story, 2-3 stories, broad, or unsure

If single story, follow up with story selection.

#### Step 1.3: Impact Analysis

Internally analyze the proposed change against the current spec. Identify:
- **Affected stories and task groups**
- **Ripple effects** — completed work at risk, dependency chain impacts, architecture conflicts, AC changes
- **Risk classification** — breaking changes, scope creep, dependency cascades

This analysis feeds your clarification questions and contract proposal. Don't present raw analysis — weave it into the conversation.

#### Step 1.4: Structured Clarification

Use AskQuestion for bounded decisions, batching related questions (max 5-7 per round).

**Round 1** should address the highest-uncertainty items: how to handle affected completed work, migration preference (incremental vs clean break), and scope tolerance (is added work acceptable, or trade something off).

**Round 2+** adapts based on Round 1 answers. Continue until you're 95% confident on the full impact. Use free-text follow-up only when structured options can't capture the nuance.

**Critical: push back constructively.** Examples of non-obvious pushback:
- "This would invalidate 3 completed tasks in Story 2. Is the rework worth it?"
- "I see a simpler path that only touches Story 4 instead of Stories 2-5. Want to explore that?"
- "This conflicts with your existing [pattern]. Update the pattern or adjust the change?"
- "Adding this pushes Story 3 to 9 tasks — I'd recommend splitting. Agree?"

#### Step 1.5: Modification Contract

When confident about the change, present a contract covering:

- **What changes** — clear description with change type
- **Impact** — stories modified/added/archived, tasks affected, completed work at risk
- **Migration strategy** — how to handle existing implementation, preserve completed work, rollback plan
- **Updated scope boundaries** — what's now in/out of scope
- **Risks & concerns** — specific, not generic
- **Recommendations** — safer approaches if they exist
- **Effort estimate** — additional/changed work involved

Then offer: lock contract (proceed), edit contract, show before/after comparison, explore risks in detail, understand rollback, or ask more questions.

Only proceed to Phase 2 when the user locks the contract.

### Phase 2: Update the Specification

#### Step 2.1: Backup & Track

Create a backup in `.writ/specs/[spec-folder]/backups/[timestamp]/`. Create or append to `CHANGELOG.md` within the spec folder: date, change type, what changed, files updated, backup location — and, whenever the edit assigned or retired an acceptance-criterion ID under Step 2.2's ID-stability rules, an **AC IDs assigned:** line and an **AC IDs retired:** line, each listing the affected IDs by story (`none` when the edit didn't touch that direction). These two lines are additive to the shape above, not a replacement for it.

Use `todo_write` to track the modification steps.

#### Step 2.2: Update Files

**spec.md and spec-lite.md:** Modify to reflect the new agreement.

**Modified stories:** Update tasks, AC, and notes. Preserve task completion status where work is still valid. Annotate tasks needing rework with ⚠️ and new tasks with 🆕.

**New stories:** Spawn parallel `Task` subagents using `agents/user-story-generator.md` (max 4 concurrent), same pattern as `/create-spec`.

**Removed stories:** Move to `user-stories/archived/` — never delete, preserve for rollback.

**Story management rules:**
- Story grows beyond 7 tasks → split it
- Story shrinks below 3 tasks → consider combining with a related story
- Update all dependency declarations across affected stories

**Acceptance-criterion ID stability (never renumber):** every criterion tag and marker
follows the grammar in `.writ/docs/acceptance-criteria-ids.md` — the `AC-<story>.<n>` form,
the trailing `` `[AC-n.m]` `` tag, and the `> **AC IDs assigned through:** AC-n.m` marker line
directly beneath the story's `## Acceptance Criteria` heading. That doc is the contract; the
three procedures below are how this command implements it. In all three, an existing
criterion's tag is either left byte-identical or not touched at all — never rewritten to a
different ID.

- **Insert (a criterion is added, anywhere in reading order):** read the story's own current
  marker value `<mark>`, assign the new criterion `<mark> + 1`, and advance the marker to that
  same new value. Do not change any existing criterion's tag. The new criterion's ID has no
  relationship to where it lands in reading order — reading order and ID order are
  deliberately independent, exactly as in the grammar doc's worked insert example (a marker at
  `AC-3.4` with a new criterion inserted second in reading order still gets `AC-3.5`, and the
  three pre-existing tags stay `AC-3.1`, `AC-3.3`, `AC-3.4`, untouched).
- **Remove (a criterion is deleted):** delete the criterion's line only. Do not move the
  marker down — it stays at the highest ID ever assigned to the story, even though that exact
  ID no longer labels any surviving criterion. The removed ID is retired permanently: no
  future insert in this story may ever be assigned that number, and the next insert still
  takes `<mark> + 1` from the unchanged marker. Before the edit completes, search the repo for
  citations of the retired ID — a self-contained scan this command runs itself, e.g. `grep -rn
  "AC-<n>.<m>" --include=*.md --include=*.py .` from the repo root, skipping `backups/` and
  anything git-ignored — and surface every match (a task tag or a test name/docstring still
  citing the retired ID) to the human as a reference that needs repointing to a surviving
  criterion or deleting outright. This grep is local to `/edit-spec`; it is not a call to
  `scripts/ac-trace.py`, which belongs to a different story and is not a dependency here.
  **Out of scope:** whole-story archival (the "Removed stories" rule above, moving a removed
  story to `user-stories/archived/`) is a different operation from removing a single criterion
  within a surviving story, and this citation-surfacing rule does not apply at the story
  level — mirroring how `sub-specs/technical-spec.md`'s Interaction Edge Cases table already
  scopes out story-renumbering as a separate, unimplemented concern.
- **First adoption (a legacy story with zero IDs and no marker gains a tagged criterion):**
  never tag only the new or changed criterion — tagging one criterion while its siblings stay
  untagged produces `partial_adoption`, which `/verify-spec` reports as blocking. Instead:
  create the `> **AC IDs assigned through:**` marker line directly beneath the story's
  `## Acceptance Criteria` heading (it does not exist yet in a legacy story), then assign
  `AC-<story>.1` through `AC-<story>.N` to every criterion currently in the story, in reading
  order, and set the marker to the final value assigned. The story leaves the edit either
  fully adopted — every criterion tagged — or entirely untouched. There is no partial state.

**README and sub-specs:** Update progress table, dependency graph, and quick links. Only update sub-specs that are actually affected.

**Supersession write-back (`Amends:`/`Extends:`):** if the modification contract adds or changes an `> **Amends:**` or `> **Extends:**` line on this spec's header (declaring that it now supersedes or builds on another spec), invoke the same reference implementation `create-spec.md` Step 2.4b uses for new specs:

```bash
python3 scripts/supersession-writeback.py apply --new-spec-file .writ/specs/[edited-spec-folder]/spec.md
```

This writes/updates `> **Superseded by:**` onto each resolvable referenced spec's header without touching its `Status:` line or any other content, skips non-spec targets (e.g. ADR links) under `skipped_other`, and reports broken references under `broken` rather than failing — a bad supersession pointer never blocks or rolls back the rest of the edit.

#### Step 2.3: Validate

Present the updated package: file tree with change indicators (⭐ Updated, 🆕 New, 🗃️ Archived), summary of stories modified/added/archived, tasks reorganized, and completed work preserved.

Then offer: approve, request minor adjustments, or rollback from backup.

## Completion

This command succeeds when all of:

1. **Modification contract was locked** — the user explicitly approved the proposed changes
2. **Backup created** — pre-edit state preserved in `backups/[timestamp]/`
3. **Files updated** — all affected spec files, stories, and sub-specs reflect the agreed changes
4. **Changelog appended** — the spec's `CHANGELOG.md` records what changed, when, and why
5. **Package validated** — the updated package summary was presented and the user approved or acknowledged

If the user selects rollback at Step 2.3, restoring from backup is a valid successful outcome — the command completed its job by preserving the user's intent.

**Suggested next step:** `/implement-spec` or `/implement-story` to continue implementation with the updated spec.

**Terminal constraint:** This command produces updated spec artifacts (`.writ/specs/{spec-folder}/`). Do not offer to implement, build, or execute what was modified. For implementation, the user should run `/implement-spec` or `/implement-story`. For quick prototyping, use `/prototype`.

---

## Integration with Writ

| Command | Relationship |
|---------|-------------|
| `/create-spec` | Creates specs that `/edit-spec` modifies |
| `/assess-spec` | Run after major edits to re-validate shape; assess can invoke edit for splits |
| `/implement-spec` | After editing, re-run to update execution plan |
| `/implement-story` | After editing, can target specific modified stories |

---

## References

- Standing instructions: [`commands/_preamble.md`](_preamble.md)
- Identity & Prime Directive: [`system-instructions.md`](../system-instructions.md)
