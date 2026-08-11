# No Destructive-Class Command Records a Restore Path Before Mutating

> **Type:** Improvement
> **Priority:** High
> **Effort:** Medium
> **Created:** 2026-08-11
> **spec_ref:** _(set automatically when promoted via `/create-spec --from-issue`)_

## TL;DR

ADR-022's reversibility precondition requires the restore path to be recorded *before* the mutation; none of the four destructive-class commands does this, so condition (2) currently fails for all of them and there is no mechanism to satisfy it.

## Current State

- **`/revert`** presents the resolved commit list and the `base` SHA in its Phase 3 plan, before mutating — but presents them, in conversation. The only durable write is the Phase 5 git-notes audit entry, which is explicitly **optional** and happens *after* Phase 4 executes.
- **`/refactor`** writes nothing before its first edit. The first durable artifact is the first refactor commit, which lands after the first mutation.
- **`/uninstall-writ`** counts customized files in its Step 2 confirmation and states they "will be lost". A count is a warning, not a restore path. The Step 5 summary prints a reinstall command *after* deletion, and that restores upstream defaults, not the user's customizations.
- **`/reinstall-writ`** has manifest **baseline hashes** — which detect that a file was customized but cannot reconstruct its contents — and Step 3 deletes the manifest itself.
- There is no shared convention, file, or helper for "write down what this operation is about to destroy, before it destroys it".

## Expected Outcome

- A single recording convention destructive-class commands share: a pre-mutation record naming the target set, the pre-mutation git ref, and — for content that is untracked or about to leave the repository — the content itself or a durable copy.
- The record is written while the pre-mutation state still exists, and is durable (a file, not conversation output).
- `/revert`'s optional git-notes audit becomes required, or is superseded by that convention.
- With a mechanism in place, condition (2) of the precondition becomes checkable rather than uniformly false.

## Relevant Files

- `commands/_preamble.md` - the `## Autonomy Gate Classes` section states the precondition that this would make satisfiable
- `commands/uninstall-writ.md` - the clearest gap; deletes files whose contents nothing records
- `commands/reinstall-writ.md` - manifest baselines are hashes, so they detect change rather than enable restore

## Related Issues

- [2026-08-11-refactor-has-no-dirty-tree-guard](../bugs/2026-08-11-refactor-has-no-dirty-tree-guard.md) - the condition-(1) counterpart from the same assessment

## Notes

Found by the read-only applicability pass in `.writ/specs/2026-08-11-autonomy-gate-classes/user-stories/story-3-destructive-command-applicability.md`.

Relevant to ADR-022's **2026-11-11 review trigger**. The practical effect of the missing mechanism is that ADR-022's destructive-class row — nominally "autonomous, subject to a reversibility precondition" — resolves to *pause* for all four commands today, because condition (2) cannot be satisfied by any of them. That is the precondition holding the line rather than failing, but it also means the autonomy the ADR intended to unlock is not yet available. Closing this issue is what would actually unlock it, and it should be closed deliberately rather than by relaxing the precondition's wording.
