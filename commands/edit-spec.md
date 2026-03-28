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

Create a backup in `.writ/specs/[spec-folder]/backups/[timestamp]/`. Create or append to `CHANGELOG.md` within the spec folder: date, change type, what changed, files updated, backup location.

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

**README and sub-specs:** Update progress table, dependency graph, and quick links. Only update sub-specs that are actually affected.

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

---

## Integration with Writ

| Command | Relationship |
|---------|-------------|
| `/create-spec` | Creates specs that `/edit-spec` modifies |
| `/assess-spec` | Run after major edits to re-validate shape; assess can invoke edit for splits |
| `/implement-spec` | After editing, re-run to update execution plan |
| `/implement-story` | After editing, can target specific modified stories |
