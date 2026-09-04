---
name: safe-refactor-loop
description: "Change code structure without changing behavior — one verified, independently revertable commit per concern under a continuously green baseline."
disable-model-invocation: true
status: candidate
status_evidence: "Extracted 2026-07-10 from refactor Phase 3. 1 consumer (commands/refactor.md); proven needs >=3 — see ADR-014."
---

# Safe Refactor Loop

## Purpose

Change the structure of existing code — names, shape, duplication, nesting,
module boundaries — **without changing its observable behavior**, verifiably at
every step. The loop runs under a continuously green baseline: checkpoint, make
one change, verify (tests + types + lint), then commit if green or revert if
red. One commit holds exactly one concern, so every step is independently
reviewable, bisectable, and revertable.

This capability covers how to execute a behavior-preserving change safely. The
consumer decides what to change and in what order — the analysis, the risk
ranking, the plan the user approved, and the before/after reporting. If a change
alters what the code does rather than how it is arranged, it is not a refactor
and this discipline does not cover it.

## When to Use

- Restructuring code whose behavior must stay identical: extracting helpers,
  removing duplication, flattening nesting, renaming, splitting modules,
  modernizing patterns, tightening types, deleting dead code.
- Any structural change where a test suite, typechecker, and linter can prove
  behavior was preserved after each step.
- Distinct from growing new behavior test-first — that is a red → green →
  refactor cycle. This loop changes structure under an already-green baseline
  and never adds behavior.
- Not for feature work, bug fixes, or API changes — those change behavior by
  intent and belong to a different workflow.

## How to Apply

### 0. Establish a green baseline first — and stop if you can't

Before touching anything, run the test suite, typechecker, and linter. **All
three must pass.** If the baseline is red, stop and report the specific failures
rather than working around them: on a broken baseline you cannot distinguish a
regression you introduced from a pre-existing failure. Record the baseline
metrics (test count and pass rate, type-error count, lint-error count, and any
mode-specific counts) so the end state can be compared against them.

If the code under change has **no test coverage**, stop and flag that too:
without tests, behavior preservation cannot be verified. Add
characterization tests that pin the current behavior first, then refactor under
them.

### 1. Run the per-change loop

For each approved change, in the planned order (safest first):

1. **Checkpoint** — record the restore point before touching anything. Capture
   the current commit as this change's **revert target**:

   ```
   git rev-parse HEAD
   git status --porcelain
   ```

   The tree must be clean at the **top of every iteration**, not merely the
   first: step 4 leaves it clean on both branches, so anything uncommitted here
   is either a partial commit, an incomplete revert, or an edit made outside the
   loop. If the second command prints anything,
   **stop and report what is uncommitted** — a revert cannot tell your work from
   the edit it is about to undo. Outside a git repository there is nothing to protect and no way to
   revert: say so, report that per-change revert is unavailable, and continue.
2. **Apply** — make a surgical, minimal edit. Touch only what this one change
   requires; do not fold in unrelated cleanups.
3. **Verify** — run tests, typecheck, and lint. All three must pass.
4. **Commit or revert:**
   - **Green** → commit with a descriptive message scoped to this one change,
     then move to the next.
   - **Red** → revert to the checkpoint's **revert target**. Restoration must
     cover everything the change touched, **including files the change created** —
     a plain restore leaves new untracked files behind, and the
     next iteration's checkpoint would then stop on this loop's own leftovers.
     Report what broke and why, and decide whether to skip this change or stop
     the remaining plan. Never leave the tree red to "fix it in the next step."

### 2. One concern per commit

Each commit addresses exactly one refactoring concern. Do not combine "extract
constants" with "simplify conditionals" in the same commit even when they touch
the same file. Single-concern commits keep review, bisection, and rollback
simple, and a reverted change removes only itself.

### 3. Move code and its imports together

When a change moves or extracts code, update every import path across dependent
files **in the same commit** as the structural move, and confirm no file still
references the old location. A commit that relocates code but leaves dangling
imports is not done.

### 4. Preserve the interface and stay in scope

Keep public signatures, return types, and export names stable unless the plan
explicitly calls for changing them; internal restructuring should be invisible
to consumers. When splitting a module that outside code imports by its old path,
leave a re-export at the original location so existing imports keep working, then
migrate them incrementally. If execution surfaces new issues that were not in the
approved plan, note them for a follow-up rather than silently widening scope.

### 5. Reconsider the plan when a safe change fails

If a low-risk change breaks verification, the failure often reveals an
assumption the plan missed. Pause and reconsider whether the riskier downstream
changes are still safe before continuing. If a reverted change was a
prerequisite for later ones, skip those too and re-present what remains.

## Examples

**A clean per-change sequence, one concern each, each green before the next:**

```text
checkpoint → extract auth role magic-strings to constants → tests+types+lint green
          → commit "refactor: extract auth role constants"
checkpoint → deduplicate validation into a shared validator  → green
          → commit "refactor: deduplicate validation into shared validator"
checkpoint → split auth.ts into auth/session/token modules,
             updating all importers in the SAME commit          → green
             (had this gone red, the revert must also delete the
              new module files, or the next checkpoint stops)
          → commit "refactor: split auth.ts into auth, session, token modules"
```

**A red step that reverts cleanly instead of cascading:**

```text
checkpoint → convert callback error handling to async/await → 2 tests fail (red)
          → revert to the checkpoint SHA; tree is clean again, not merely green
          → report: "async conversion broke ordering in retry path; skip or stop?"
```
