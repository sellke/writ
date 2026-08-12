# Spec: `/refactor` Dirty-Tree Guard

> **Status:** Not Started
> **Owner:** @AdamSellke
> **Created:** 2026-08-12
> **Dependencies:** []
> **Origin:** Filed as a bug by Phase 10's own UAT — `.writ/issues/bugs/2026-08-11-refactor-has-no-dirty-tree-guard.md`. Story 3 of `2026-08-11-autonomy-gate-classes` ran a read-only applicability pass over the four destructive-class commands and found `/refactor` has no porcelain check anywhere, while `/revert` HALTs on one before any git operation and lists it as Safety Guarantee #1.

## Contract (Locked)

**Deliverable:** A `git status --porcelain` guard in `/refactor` before its baseline verification, mirroring `/revert`'s discipline, plus an executable checkpoint in `safe-refactor-loop` and an untracked-target check for `--dead-code`.

**Must include:** The guard HALTs before Step 1.2, using the wording discipline `commands/revert.md:60-67` already establishes. `skills/safe-refactor-loop/SKILL.md`'s "note the current clean git state" becomes an instruction that captures the HEAD SHA and asserts cleanliness, rather than an assumption. `--dead-code` deletion targets are checked against `git ls-files` so an untracked orphan is surfaced, never silently removed.

**Hardest constraint:** `/refactor`'s per-change loop reverts immediately on a red verify. On a dirty tree that revert cannot distinguish the refactor's own edit from the user's uncommitted work — and for an untracked file deleted by `--dead-code`, there is no git object to restore from at all. The guard must therefore run *before* the first mutation, not before the first commit.

## Why This Exists

ADR-022 classifies destructive operations as autonomous **subject to a reversibility precondition**: the effect must be provably git-revertable, and the restore path recorded before the mutation. `/refactor` satisfies neither today. It is the clearest live instance of the gap that ADR-022's own UAT surfaced, and it is small enough to fix without ceremony.

## 📋 Business Rules

1. **The guard runs before the first mutation, not the first commit.** A revert-on-red that fires against mixed working-tree state is the failure being prevented.
2. **Mirror `/revert`, do not invent.** `commands/revert.md:60-67` is the established wording and behaviour for this exact check; matching it keeps one discipline rather than two.
3. **`--dead-code` checks targets against `git ls-files`.** An untracked deletion target is surfaced and skipped, never removed — it has no restore path.
4. **No behavioural change on a clean tree.** A `/refactor` run that would have succeeded before must be byte-identical in behaviour after.

## Detailed Requirements

- `commands/refactor.md` — porcelain guard ahead of Step 1.2 Baseline Verification, with a HALT and a named remedy.
- `skills/safe-refactor-loop/SKILL.md` — step 1's checkpoint captures `HEAD` and asserts a clean tree.
- `--dead-code` — deletion targets intersected with `git ls-files`; untracked targets reported.

## Out of Scope

- Any change to `/revert`, `/uninstall-writ`, or `/reinstall-writ` (the improvement issue tracks the wider restore-path work).
- Enforcing ADR-022's precondition generally — this fixes one command.
