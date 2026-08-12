# `/refactor` Dirty-Tree Guard (Lite)

> Source: .writ/specs/2026-08-12-refactor-dirty-tree-guard/spec.md
> Purpose: Efficient AI context for implementation

## For Coding Agents

**Deliverable:** A `git status --porcelain` guard in `/refactor` before baseline verification, an executable checkpoint in `safe-refactor-loop`, and an untracked-target check for `--dead-code`.

**Implementation Approach:**
- Mirror `commands/revert.md:60-67` — the established HALT wording for this exact check.
- Guard sits ahead of Step 1.2 Baseline Verification in `commands/refactor.md`.
- `skills/safe-refactor-loop/SKILL.md` step 1: capture HEAD SHA, assert clean tree.
- `--dead-code`: intersect deletion targets with `git ls-files`; surface untracked ones.

**Files in Scope:**
- `commands/refactor.md` — the guard (Story 1)
- `skills/safe-refactor-loop/SKILL.md` — executable checkpoint (Story 2)

**Error Handling:** Dirty tree → HALT with a named remedy, before any mutation. Untracked `--dead-code` target → report and skip, never delete.

**Watch-outs:** `commands/refactor.md` is NOT under the 24,960-byte budget work — it was never a disclosure target. Keep the guard compact. No behavioural change on a clean tree.
