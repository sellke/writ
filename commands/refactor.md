# Refactor Command (refactor)

## Overview

Scoped, safe refactoring with automated verification. Analyzes a file, module, or pattern across the codebase, proposes structural improvements, and executes them with tests passing before AND after every change.

**Core discipline:** Each refactoring is an isolated, verified, revertable commit. Never batch changes. Never skip verification. Never refactor on a broken baseline. Refactoring changes structure, never behavior — if a change alters observable behavior, it's not a refactor.

**Scope boundary:** Refactoring does not add features, fix bugs, or change APIs. If the user needs behavioral changes, direct them to `/implement-story`. If they need security fixes, use `/security-audit`. This command makes existing code cleaner, not different.

## Modes

| Invocation | Mode | Behavior |
|---|---|---|
| `/refactor src/lib/auth.ts` | File | Analyze one file, propose improvements |
| `/refactor src/lib/` | Module | Analyze a directory, propose structural changes |
| `/refactor --duplicates` | Deduplication | Find duplicated code, propose consolidation |
| `/refactor --dead-code` | Dead code | Find and remove unused exports, functions, files |
| `/refactor --modernize` | Modernize | Upgrade legacy patterns to modern equivalents |
| `/refactor --types` | Type safety | Strengthen TypeScript types (remove `any`, add missing types) |
| `/refactor --extract pattern` | Extract | Pull a named pattern into a shared utility/component |
| `/refactor --dry-run` | Preview | Analyze and report without making changes |

All modes follow the same four-phase workflow. The mode determines *what to scan for* (Step 1.3), not *how to execute*.

## Command Process

### Phase 1: Scope & Analysis

#### Step 1.1: Determine Scope

If a target is provided in the invocation, use it directly and proceed to Step 1.2.

If no target, present scope selection via AskQuestion with these options:

- A specific file (follow up for path)
- A directory/module (follow up for path)
- Find and consolidate duplicate code
- Find and remove dead code
- Upgrade legacy patterns
- Strengthen TypeScript types
- Analyze the project and suggest refactoring targets

The last option triggers a **hotspot analysis**: scan the project for files with the highest complexity, most frequent git churn, largest size, and weakest test coverage. Present the top candidates ranked by refactoring value — complexity × churn is a strong signal for high-value targets. Let the user choose which to proceed with.

#### Step 1.2: Baseline Verification

**Before touching anything, establish a green baseline.** Run the project's test suite, typechecker, and linter. All three must pass.

**If the baseline fails, stop.** Report the specific failures and instruct the user to fix them first. Do not offer to "work around" failing tests or proceed with partial verification. Refactoring on a broken baseline makes it impossible to verify changes are safe — you cannot distinguish regressions you introduced from pre-existing failures.

Store baseline metrics for the Phase 4 comparison: test count and pass rate, type error count, lint error count, and mode-specific baselines (e.g., `any` count for `--types`, dead export count for `--dead-code`).

#### Step 1.3: Deep Analysis

Analyze the target scope and produce a structured analysis report. What to detect per mode:

| Mode | What to analyze |
|---|---|
| **File / Module** | Size, export count, importer count, dependency count, test coverage. Issues: god modules, deep nesting (3+ levels), magic strings/numbers, internal duplication, legacy patterns, tight coupling |
| **Duplicates** | Similar function signatures and bodies, repeated patterns across files. Group by similarity; identify extraction targets (shared utilities, base classes, HOCs, hooks) |
| **Dead code** | Unexported or unimported exports, orphan files, unreachable paths, unused package dependencies. Assign confidence: high/medium/low — some "dead" code may be used dynamically |
| **Modernize** | `var` → const/let, `require`/`module.exports` → ESM, `.then()` → async/await, callbacks → try/catch, class components → functions, `React.FC` → direct signatures |
| **Types** | `any` annotations, `as any` casts, `@ts-ignore`/`@ts-expect-error`, missing return types, untyped parameters. Propose specific replacements where inferable from usage |
| **Extract** | All occurrences of the named pattern, variation points between them, proposed shared abstraction (utility, component, hook, or base class) with parameterized variations |

**Report format:** For each issue, state the problem, recommended change, risk level (Low / Medium / High), and impact (Low / Medium / High). Risk reflects breakage likelihood and dependent count. Impact reflects improvement value.

**Order findings low → high risk.** This ordering determines execution priority in Phase 3 — safe changes land first, building confidence before riskier transformations.

For file/module mode, also report cross-cutting context: which files depend on the target (at risk during changes), the target's own dependencies, and test coverage gaps that increase refactoring risk.

---

### Phase 2: Refactoring Plan

#### Step 2.1: Propose Changes

Present the prioritized plan as a risk-ordered table:

| # | Change | Risk | Impact |
|---|---|---|---|
| 1 | Extract magic strings to constants | Low | Low |
| 2 | Deduplicate validation into shared utility | Low | Medium |
| 3 | Simplify nested conditionals with early returns | Low | Medium |
| 4 | Convert callback error handling to async/await | Med | Medium |
| 5 | Split module into single-responsibility files | Med | High |

Adapt table contents to the active mode — a `--types` plan lists specific type replacements, `--dead-code` lists exports/files to remove, `--extract` shows the shared abstraction and replacement sites.

For module splits and extractions, include a dependency summary: how many files import the target and will need updates. This helps the user assess blast radius before approving.

Include total change count and time estimate. State that tests are verified after each change and any failure triggers immediate rollback.

For large plans (7+ changes), recommend splitting into sessions: complete low-risk changes first, then return for medium and high-risk changes with a fresh baseline.

#### Step 2.2: Plan Approval

Present execution options via AskQuestion:

- **Execute all** — apply all changes in risk order, stop on first failure
- **Pick changes** — let the user select which changes to apply
- **Low-risk only** — apply only Low-risk changes, defer Medium and High
- **Preview diffs** — show detailed diffs for each proposed change before applying
- **Create ADR first** — document the architectural rationale before executing

If the user selects "Create ADR first," produce one following `/create-adr` conventions: document the refactoring rationale, what will change, impact on dependent code, and how to navigate the new structure. Then return to execution.

For `--dry-run` mode, the command ends here — present analysis and plan, then stop.

---

### Phase 3: Execution

**Golden rule: Tests pass after every individual change.**

For each approved change, follow this cycle:

1. **Checkpoint** — note the current git state for rollback
2. **Apply** — edit files with surgical, minimal diffs. Touch only what's necessary for this specific step.
3. **Verify** — run tests, typecheck, and lint. All three must pass.
4. **Commit or revert:**
   - **Green:** commit with a descriptive `refactor:` prefix message. Proceed to next change.
   - **Red:** revert immediately, report what broke and why, ask whether to skip this change or abort the remaining plan.

**Commit per change, not per batch.** Each refactoring step gets its own isolated commit. This makes every change independently revertable, bisectable, and code-reviewable. Example sequence:

- `refactor: extract auth role constants`
- `refactor: deduplicate validation logic into shared validator`
- `refactor: split auth.ts into auth, session, token modules`

**When moving or extracting code,** update all import paths across dependent files in the same commit as the structural change. Verify that no file still references the old location. Never leave broken imports for the user to clean up.

**Execution order matters.** Process changes low → high risk as planned. If a low-risk change unexpectedly fails, reconsider whether higher-risk changes are still safe — the failure may reveal assumptions the plan didn't account for.

**Mid-plan failure handling:** If a reverted change was a prerequisite for later changes, skip those automatically. Present the updated remaining plan and let the user decide whether to continue, adjust, or stop.

---

### Phase 4: Verification & Report

Run the full verification suite one final time. Compare against the Step 1.2 baseline and produce a completion report:

- **Before/after metrics table** — file count, total lines, exports per file, max nesting depth, mode-specific counts (e.g., `any` remaining, dead exports removed), test results, type errors, lint errors. Show baseline, final, and delta.
- **All commits** — hash and message for each refactoring commit, in execution order
- **Files changed** — each file with a one-line summary (modified, created, deleted, moved)
- **ADRs created** — link to any architecture decision records produced

**Quality bar:** Every metric should be equal or improved. If any metric regressed (e.g., file count increased from a module split), explain why the trade-off is acceptable. A reviewer reading this report should have complete confidence the refactoring was safe.

If any changes were skipped or reverted during execution, list them with the failure reason. This gives the user a clear picture of what was accomplished and what remains for a follow-up session.

---

## Safety Guarantees

These seven invariants hold for every refactoring operation:

1. **Green baseline required** — won't start if tests, types, or lint are already failing
2. **Verify after every change** — tests + typecheck + lint after each individual refactoring step
3. **Automatic rollback** — if any change breaks verification, it's reverted immediately
4. **Commit per change** — each refactoring is an isolated, independently revertable commit
5. **Import updates included** — when moving code, all dependent files are updated in the same commit
6. **No behavior changes** — refactoring changes structure, not observable behavior
7. **ADR for major changes** — module splits and architectural restructuring get decision records

---

## Refactoring Discipline

Non-obvious principles that prevent common refactoring failures:

**Stay in scope.** If you discover new issues during execution that weren't in the approved plan, note them for a follow-up session — don't silently expand scope. The user approved a specific plan; changing it mid-execution without consent erodes trust.

**Don't refactor without tests.** If the target code has no test coverage, flag this in the analysis report. Refactoring untested code is gambling — you can't verify behavioral preservation. Recommend adding characterization tests first.

**Don't refactor doomed code.** Check whether the target is scheduled for replacement or deletion in an active spec. Refactoring code that's about to be rewritten is wasted effort — surface this and let the user decide.

**Respect backward compatibility.** When splitting modules, consider whether external consumers import from the original path. If so, create a re-export barrel at the original location so existing imports continue working, then migrate consumers incrementally.

**Dead code confidence.** Not all "unused" exports are actually dead — they may be consumed dynamically via string-based lookups, reflection, test utilities, plugin systems, or CLI entry points. Flag low-confidence findings rather than auto-removing.

**One concern per commit.** Each commit should address exactly one refactoring concern. Don't combine "extract constants" with "simplify conditionals" in the same commit, even if they touch the same file. Atomic commits make review and rollback trivial.

**Preserve the public interface.** Unless the plan explicitly calls for API changes, keep function signatures, return types, and export names stable. Internal restructuring should be invisible to consumers.

---

## Integration with Writ

| Command | Relationship |
|---------|-------------|
| `/implement-story` | Refactoring may be needed before or after story implementation |
| `/verify-spec` | Run after refactoring to confirm spec alignment |
| `/create-adr` | Auto-created for significant architectural refactors |
| `/security-audit` | Refactoring can address security findings |
| `/research` | Investigate modernization patterns or architectural approaches before refactoring |
| `/status` | Shows recent refactoring commits |
