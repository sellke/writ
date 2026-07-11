---
name: tdd-cycle
description: "Grow code test-first through the red → green → refactor cycle, one small unit of behavior at a time."
disable-model-invocation: true
status: candidate
status_evidence: "Extracted 2026-07-10 from implement-story's coding phase; candidate until consumer transcripts prove reuse across coding and testing consumers."
---

# TDD Cycle

## Purpose

Grow implementation code **test-first**, one small increment at a time, so that
every line of production code exists to satisfy a test that failed before it was
written. The discipline is a tight three-beat loop — **red** (write a failing
test), **green** (write the least code that passes it), **refactor** (clean up
under a passing suite) — repeated per unit of behavior until the work is done.

This capability owns *how to run the loop well*. It does not decide *which*
units to build, how work is routed between roles, or what happens when the loop
stalls past its limits — those belong to the consumer that wields it. The value
is that the same discipline produces code that is designed for testability,
minimal, and continuously verified rather than tested as an afterthought.

## When to Use

- Implementing new behavior where a test can express the desired outcome before
  the code exists — the default for feature and bug-fix work.
- Fixing a bug: reproduce it with a failing test first, then make that test pass,
  so the fix is proven and the regression is guarded.
- Any change where "designed for testability" matters and a fast test runner is
  available to make the loop cheap.
- Not the right tool for pure structural change under an already-green suite —
  that is a behavior-preserving refactor loop, a different discipline.

## How to Apply

### The three beats

Run this loop for each small unit of behavior, not for the whole feature at once.

1. **Red — write one failing test.** Express a single, concrete piece of desired
   behavior as a test and run it. Confirm it fails, and fails *for the right
   reason* (the behavior is missing — not a typo, missing import, or broken
   harness). A test that passes immediately, or errors before it even asserts,
   teaches you nothing; fix the test until the failure is meaningful.

2. **Green — make it pass with the least code.** Write the simplest
   implementation that turns the test green. Resist building for imagined future
   cases: only the current test's behavior earns code right now. "Simplest" means
   least code, not sloppiest — but a hard-coded return that passes is a legitimate
   first step you will generalize in the next cycle. Run the test; confirm green.

3. **Refactor — clean up under green.** With the test passing, improve the
   structure: remove duplication, clarify names, extract helpers, tighten types.
   Change structure only, never behavior, and re-run the tests after each edit so
   the suite stays green throughout. If a refactor turns something red, undo it or
   fix it immediately before moving on — never leave the loop on a red.

Then repeat: pick the next small unit, write the next failing test, and go again.

### Sizing each cycle

Keep each pass small enough that the failing test is obvious and the passing code
is a few lines. A good unit is one branch, one edge case, or one small behavior —
not a whole module. Prioritize the cycles in the order bugs hide: error and
failure paths first, then edge cases, then happy-path variants. If writing the
test is hard, that is a design signal — the code under test is probably doing too
much or is too coupled, and the friction is telling you to reshape it.

### Staying honest

- **Never weaken a test to make it pass.** Skipping it, deleting the assertion,
  loosening a threshold, or widening a matcher until it stops failing all defeat
  the point. When a test cannot legitimately pass, the implementation is wrong or
  the test's expectation is — fix the real cause.
- **Fix failures with the context you have.** When a check fails, feed the
  specific failure into the next small change rather than rewriting broadly; the
  failing output names exactly what to address.
- **Keep the loop green between units.** Do not start the next red beat while the
  previous cycle is still red. A continuously-green baseline is what makes each
  new failure trustworthy.
- **Know when to stop.** If the same failure resists repeated, distinct fix
  attempts, stop rather than thrashing — a persistently red test after several
  genuine tries is a signal that the problem needs a rethink, not another patch.

## Examples

**Growing a small function, one cycle per behavior:**

```text
Cycle 1 — red:   test "returns 0 for an empty list"        → fails (no fn)
          green: `function sum(xs){ return 0 }`            → passes
Cycle 2 — red:   test "returns the element for [5]"        → fails (returns 0)
          green: `return xs.reduce((a,b)=>a+b, 0)`         → passes; cycle 1 still green
          refactor: name is clear, no duplication          → nothing to do
Cycle 3 — red:   test "throws on a non-array argument"     → fails (returns 0)
          green: add a guard that throws TypeError         → passes
          refactor: extract the guard to `assertArray(xs)` → tests stay green
```

**A bug fix that starts with a failing reproduction:**

```text
red:   test "parseDate('') returns null, does not throw"   → fails (throws)
green: guard the empty-string case before parsing          → passes
refactor: fold the guard into the existing validation block → suite stays green
```

The guarantee at the end of each cycle is the same: a test that would have failed
without the change now passes, every earlier test still passes, and the structure
is a little cleaner than it was.
