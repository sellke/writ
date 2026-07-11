---
name: safe-refactor-loop
description: "Change code structure without changing behavior — one verified, independently revertable commit per concern under a continuously green baseline."
disable-model-invocation: true
status: candidate
status_evidence: "Extracted 2026-07-10 from refactor Phase 3; candidate until consumer transcripts prove reuse (prototype work is the plausible second consumer)."
---

# Safe Refactor Loop

## Purpose

Change the *structure* of existing code — names, shape, duplication, nesting,
module boundaries — **without changing its observable behavior**, in a way that
is provably safe at every step. The discipline is a tight per-change loop run
under a continuously green baseline: checkpoint, make one surgical change,
verify (tests + types + lint), then commit if green or revert if red. One commit
holds exactly one concern, so every step is independently reviewable, bisectable,
and revertable.

This capability owns *how to execute a behavior-preserving change safely*. The
consumer owns *what* to change and *in what order* — the analysis, the risk
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
  refactor cycle. This loop changes structure under an *already-green* baseline
  and never adds behavior; the two compose but are separate disciplines.
- Not for feature work, bug fixes, or API changes — those change behavior by
  intent and belong to a different workflow.

## How to Apply

### 0. Establish a green baseline first — and stop if you can't

Before touching anything, run the test suite, typechecker, and linter. **All
three must pass.** If the baseline is red, stop and report the specific failures
rather than working around them: on a broken baseline you cannot tell a
regression you introduced from a failure that was already there, so "safe" is
unprovable. Record the baseline metrics (test count and pass rate, type-error
count, lint-error count, and any mode-specific counts) so the end state can be
compared against them.

If the code under change has **no test coverage**, treat that as a stop-and-flag
too: refactoring untested code is gambling on behavior preservation. Add
characterization tests that pin the current behavior first, then refactor under
them.

### 1. Run the per-change loop

For each approved change, in the planned order (safest first, so confidence
builds before riskier transformations):

1. **Checkpoint** — note the current clean git state so a revert is one step.
2. **Apply** — make a surgical, minimal edit. Touch only what this one change
   requires; resist folding in an unrelated cleanup you notice along the way.
3. **Verify** — run tests, typecheck, and lint. All three must pass.
4. **Commit or revert:**
   - **Green** → commit with a descriptive message scoped to this one change,
     then move to the next.
   - **Red** → revert immediately, report what broke and why, and decide whether
     to skip this change or stop the remaining plan. Never leave the tree red to
     "fix it in the next step."

### 2. One concern per commit

Each commit addresses exactly one refactoring concern. Do not combine "extract
constants" with "simplify conditionals" in the same commit even when they touch
the same file. Atomic, single-concern commits are what make review, bisection,
and rollback trivial — and what let a reverted change take out only itself.

### 3. Move code and its imports together

When a change moves or extracts code, update every import path across dependent
files **in the same commit** as the structural move, and confirm no file still
references the old location. A commit that relocates code but leaves dangling
imports is not green and is not done — never hand a broken import to whoever
reads the diff next.

### 4. Preserve the interface and stay in scope

Keep public signatures, return types, and export names stable unless the plan
explicitly calls for changing them; internal restructuring should be invisible
to consumers. When splitting a module that outside code imports by its old path,
leave a re-export at the original location so existing imports keep working, then
migrate them incrementally. If execution surfaces new issues that were not in the
approved plan, note them for a follow-up rather than silently widening scope.

### 5. Reconsider the plan when a safe change fails

Changes are ordered safest-first for a reason: if a low-risk change unexpectedly
breaks verification, that failure often reveals an assumption the plan missed, so
pause and reconsider whether the riskier changes downstream are still safe before
continuing. If a reverted change was a prerequisite for later ones, skip those
too and re-present what remains.

## Examples

**A clean per-change sequence, one concern each, each green before the next:**

```text
checkpoint → extract auth role magic-strings to constants → tests+types+lint green
          → commit "refactor: extract auth role constants"
checkpoint → deduplicate validation into a shared validator  → green
          → commit "refactor: deduplicate validation into shared validator"
checkpoint → split auth.ts into auth/session/token modules,
             updating all importers in the SAME commit          → green
          → commit "refactor: split auth.ts into auth, session, token modules"
```

**A red step that reverts cleanly instead of cascading:**

```text
checkpoint → convert callback error handling to async/await → 2 tests fail (red)
          → revert immediately; tree is green again
          → report: "async conversion broke ordering in retry path; skip or stop?"
```

The invariant at every step is the same: the suite, the typechecker, and the
linter are green, exactly one concern is committed, no imports dangle, and the
code behaves exactly as it did before the change.
