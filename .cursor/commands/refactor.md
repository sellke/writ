# Refactor Command (refactor)

## Overview

Scoped, safe refactoring with automated verification. Analyzes a file, module, or pattern across the codebase, proposes structural improvements, and executes them with tests passing before AND after every change.

## Modes

| Invocation | Mode | Behavior |
|---|---|---|
| `/refactor src/lib/auth.ts` | File | Analyze one file, propose improvements |
| `/refactor src/lib/` | Module | Analyze a directory, propose structural changes |
| `/refactor --duplicates` | Deduplication | Find duplicated code across the project, propose consolidation |
| `/refactor --dead-code` | Dead code removal | Find and remove unused exports, functions, files |
| `/refactor --modernize` | Pattern upgrades | Upgrade legacy patterns to modern equivalents |
| `/refactor --types` | Type safety | Strengthen TypeScript types (remove `any`, add missing types) |
| `/refactor --extract pattern` | Extract | Pull a pattern into a shared utility/component |
| `/refactor --dry-run` | Preview | Analyze and report without making changes |

## Command Process

### Phase 1: Scope & Analysis

#### Step 1.1: Determine Scope

**If target provided:**
```
/refactor src/lib/auth.ts
→ Scope: single file analysis + cross-references
```

**If no target:**
```
AskQuestion({
  title: "Refactoring Scope",
  questions: [
    {
      id: "scope",
      prompt: "What would you like to refactor?",
      options: [
        { id: "file", label: "A specific file (I'll specify)" },
        { id: "module", label: "A directory/module (I'll specify)" },
        { id: "duplicates", label: "Find and consolidate duplicate code" },
        { id: "dead_code", label: "Find and remove dead code" },
        { id: "modernize", label: "Upgrade legacy patterns" },
        { id: "types", label: "Strengthen TypeScript types" },
        { id: "hotspots", label: "Analyze project and suggest refactoring targets" }
      ]
    }
  ]
})
```

#### Step 1.2: Baseline Verification

**Before touching anything, establish a green baseline:**

```bash
# Run tests — MUST pass before any refactoring begins
npm test 2>&1          # or equivalent
npx tsc --noEmit 2>&1  # typecheck
npx eslint . 2>&1      # lint
```

**If baseline fails:**
```
⚠️ Cannot refactor — baseline tests/lint are failing.

Failing:
  - 3 test failures in auth.test.ts
  - 2 type errors in utils.ts

Fix these first, then re-run /refactor. Refactoring on a broken baseline
makes it impossible to verify changes are safe.
```

**Store baseline metrics:**
```json
{
  "baseline": {
    "tests": { "total": 45, "passing": 45 },
    "typeErrors": 0,
    "lintErrors": 0,
    "timestamp": "2026-02-22T18:00:00Z"
  }
}
```

#### Step 1.3: Deep Analysis

**For file/module mode:**

```bash
# Understand the target
rg -n '(export|function|class|const|interface|type)\s' target_file
# Count lines, complexity
wc -l target_file
# Find all importers (who depends on this?)
rg -l "from ['\"].*target_module" src/
# Find all imports (what does this depend on?)
rg "^import" target_file
```

**Produce analysis report:**

```
## Refactoring Analysis: src/lib/auth.ts

**Size:** 342 lines (large — consider splitting)
**Exports:** 12 (high — possible God module)
**Importers:** 8 files depend on this module
**Dependencies:** 6 external imports
**Test coverage:** 78% (from last coverage run)

### Issues Found

1. **God module** — 12 exports spanning auth, session, and token concerns
   - Recommendation: Split into auth.ts, session.ts, token.ts
   - Risk: Medium (8 importers need updating)
   - Impact: High (separation of concerns)

2. **Duplicated validation** — Lines 45-62 duplicate logic in src/lib/validate.ts
   - Recommendation: Extract to shared validator
   - Risk: Low
   - Impact: Medium (DRY)

3. **Nested conditionals** — Lines 120-180, 4 levels deep
   - Recommendation: Extract early returns, simplify flow
   - Risk: Low
   - Impact: Medium (readability)

4. **Magic strings** — 7 hardcoded role names scattered through file
   - Recommendation: Extract to constants
   - Risk: Low
   - Impact: Low (maintainability)

5. **Legacy pattern** — Callback-style error handling (lines 200-230)
   - Recommendation: Convert to async/await with try/catch
   - Risk: Medium (behavior change if callers expect callbacks)
   - Impact: Medium (modernization)
```

**For `--duplicates` mode:**

```bash
# Find similar code blocks (heuristic)
# Look for functions with similar signatures and bodies
rg -n 'function\s+\w+.*\{' src/ --type ts
# Look for repeated patterns
rg -c 'pattern' src/ --type ts | sort -t: -k2 -rn | head -20
```

**For `--dead-code` mode:**

```bash
# Find exports that nobody imports
for export in $(rg -o 'export (const|function|class|type|interface)\s+(\w+)' src/ -r '$2' --no-filename | sort -u); do
  count=$(rg -l "$export" src/ --type ts | wc -l)
  if [ "$count" -le 1 ]; then
    echo "DEAD: $export (only defined, never imported)"
  fi
done

# Find files with no importers
for file in src/**/*.ts; do
  module=$(echo $file | sed 's|src/||;s|\.ts$||')
  count=$(rg -l "from.*$module" src/ | wc -l)
  if [ "$count" -eq 0 ]; then
    echo "ORPHAN: $file (never imported)"
  fi
done
```

**For `--modernize` mode:**

```bash
# Find legacy patterns
rg -n 'var\s' src/ --type ts              # var → const/let
rg -n '\.then\(' src/ --type ts           # Promise chains → async/await
rg -n 'require\(' src/ --type ts          # require → import
rg -n 'module\.exports' src/ --type ts    # CJS → ESM
rg -n 'React\.FC' src/ --type tsx         # React.FC → function components
rg -n 'componentDidMount\|componentWillUnmount' src/  # Class → hooks
```

**For `--types` mode:**

```bash
# Find weak types
rg -n ': any\b' src/ --type ts
rg -n 'as any\b' src/ --type ts
rg -n '@ts-ignore\|@ts-expect-error' src/ --type ts
# Find missing return types on exported functions
rg -n 'export (async )?function \w+\([^)]*\)\s*\{' src/ --type ts
```

---

### Phase 2: Refactoring Plan

#### Step 2.1: Propose Changes

Present a prioritized plan:

```
## Refactoring Plan: src/lib/auth.ts

Proposed changes (ordered by risk, low → high):

┌─────┬──────────────────────────────┬──────┬────────┐
│  #  │ Change                       │ Risk │ Impact │
├─────┼──────────────────────────────┼──────┼────────┤
│  1  │ Extract magic strings        │ Low  │ Low    │
│  2  │ Deduplicate validation       │ Low  │ Medium │
│  3  │ Simplify nested conditionals │ Low  │ Medium │
│  4  │ Modernize error handling     │ Med  │ Medium │
│  5  │ Split into 3 modules        │ Med  │ High   │
└─────┴──────────────────────────────┴──────┴────────┘

Tests will be verified after EACH change.
If any change breaks tests, it will be rolled back.

Estimated: 5 changes, ~15 minutes
```

```
AskQuestion({
  title: "Refactoring Plan",
  questions: [
    {
      id: "action",
      prompt: "How would you like to proceed?",
      options: [
        { id: "all", label: "Execute all changes (stop on failure)" },
        { id: "pick", label: "Let me pick which changes to apply" },
        { id: "low_only", label: "Only low-risk changes" },
        { id: "preview", label: "Show me detailed diffs first" },
        { id: "adr", label: "Create an ADR for the major changes first" }
      ]
    }
  ]
})
```

#### Step 2.2: Create ADR (for significant refactors)

If splitting modules or making architectural changes, auto-create an ADR:

```
Auto-creating ADR for this refactoring...
→ .writ/decision-records/XXXX-split-auth-module.md

This documents why the refactoring was done, what changed,
and how to navigate the new structure.
```

---

### Phase 3: Execution

**Golden rule: Tests pass after EVERY individual change.**

For each approved change:

```
Step 1: Create git checkpoint
  → git stash or note current state

Step 2: Apply the change
  → Edit files (surgical, minimal diffs)

Step 3: Verify
  → Run tests (must pass)
  → Run typecheck (must pass)
  → Run lint (must pass)

Step 4: If verification passes
  → git commit -m "refactor: [description]"
  → Proceed to next change

Step 4b: If verification fails
  → Revert the change
  → Report what broke
  → Ask whether to skip or abort
```

**Commit after each change** — not in a batch at the end. Each refactoring step gets its own commit:

```
refactor: extract auth role constants
refactor: deduplicate validation logic into shared validator
refactor: simplify nested conditionals with early returns
refactor: convert callback error handling to async/await
refactor: split auth.ts into auth.ts, session.ts, token.ts
```

**Update imports automatically** when extracting/splitting:

```bash
# When moving exports to a new file, update all importers
rg -l "from.*auth" src/ | while read file; do
  # Update import paths in each file that depends on the refactored module
done
```

---

### Phase 4: Verification & Report

After all changes applied:

```bash
# Full verification suite
npm test 2>&1
npx tsc --noEmit 2>&1
npx eslint . 2>&1
```

**Compare against baseline:**

```
✅ Refactoring Complete: src/lib/auth.ts

## Before → After

| Metric | Before | After | Change |
|--------|--------|-------|--------|
| Files | 1 | 3 | +2 (split) |
| Lines (total) | 342 | 298 | -44 (-13%) |
| Exports per file | 12 | 4/4/4 | Balanced |
| Max nesting depth | 4 | 2 | -2 |
| Magic strings | 7 | 0 | Eliminated |
| Duplicated logic | 18 lines | 0 | Consolidated |
| Tests | 45 passing | 45 passing | No regression |
| Type errors | 0 | 0 | Clean |

## Commits Made
1. `abc1234` refactor: extract auth role constants
2. `def5678` refactor: deduplicate validation logic
3. `ghi9012` refactor: simplify nested conditionals
4. `jkl3456` refactor: convert to async/await
5. `mno7890` refactor: split auth into auth/session/token

## Files Changed
- `src/lib/auth.ts` — Reduced to auth-only concerns (98 lines)
- `src/lib/session.ts` — NEW — Session management (104 lines)
- `src/lib/token.ts` — NEW — Token generation/validation (96 lines)
- `src/lib/constants/roles.ts` — NEW — Role constants
- `src/lib/validate.ts` — Added shared validation (moved from auth)
- `src/routes/*.ts` — Updated imports (8 files)

## ADR Created
- `.writ/decision-records/XXXX-split-auth-module.md`
```

---

## Mode-Specific Workflows

### `--duplicates`

1. Scan entire `src/` for repeated code patterns
2. Group duplicates by similarity
3. Propose extraction targets (shared utilities, base classes, HOCs)
4. Execute extractions one at a time with verification

### `--dead-code`

1. Find unused exports, orphan files, unreachable code
2. Present list with confidence levels
3. Remove confirmed dead code
4. Verify nothing breaks after each removal

### `--modernize`

1. Detect legacy patterns (var, require, callbacks, class components, etc.)
2. Group by pattern type
3. Propose modernization for each group
4. Apply per-file with verification

### `--types`

1. Find all `any` types, `@ts-ignore`, missing return types
2. Propose specific type replacements
3. Apply per-file with typecheck verification
4. Report remaining type weaknesses that need manual decisions

### `--extract pattern`

1. Find all occurrences of the named pattern across the codebase
2. Propose a shared utility/component/hook
3. Create the shared module
4. Replace all occurrences with imports to the shared module
5. Verify after each replacement

---

## Safety Guarantees

1. **Green baseline required** — won't start if tests are already failing
2. **Verify after every change** — tests + typecheck + lint after each individual refactoring
3. **Automatic rollback** — if any change breaks anything, it's reverted immediately
4. **Commit per change** — each refactoring is an isolated, revertable commit
5. **Import updates included** — when moving code, all dependents are updated
6. **No behavior changes** — refactoring changes structure, not behavior
7. **ADR for major changes** — architectural refactors get documented

## Integration with Writ

| Command | Relationship |
|---------|-------------|
| `/implement-story` | Refactoring may be needed before or after story implementation |
| `/verify-spec` | Run after refactoring to confirm spec alignment |
| `/create-adr` | Auto-created for significant architectural refactors |
| `/security-audit` | Refactoring can address security findings |
| `/status` | Shows recent refactoring commits |
