# Verify Spec Command (verify-spec)

## Overview

Comprehensive specification validation and synchronization. Verifies that story files, README tracking, tests, coverage, and documentation are all consistent and correct. Optionally syncs discrepancies and updates external trackers (Trello, GitHub).

This is the "pre-flight check" before `/release`. Run it after `/implement-story` completes, or anytime you suspect drift.

## Modes

| Invocation | Mode | Behavior |
|---|---|---|
| `/verify-spec` | Interactive | Select spec, full verification, prompt to fix |
| `/verify-spec --check` | Read-only | Verify only, report issues, change nothing |
| `/verify-spec --fix` | Auto-fix | Verify and fix all discrepancies without prompting |
| `/verify-spec --sync-trello` | With Trello | Include Trello card sync (update/create/move) |
| `/verify-spec --pre-deploy` | Deployment gate | Full test suite + lint + typecheck + verification |

## Command Process

### Phase 1: Spec Discovery & Loading

#### Step 1.1: Select Specification

**If not specified:**
```
AskQuestion({
  title: "Spec Verification",
  questions: [
    {
      id: "spec",
      prompt: "Which specification to verify?",
      options: [
        // Dynamically populated from .writ/specs/
        { id: "latest", label: "[DATE]-[name] (most recent)" },
        { id: "spec_2", label: "[DATE]-[name]" },
        { id: "all", label: "Verify ALL specifications" }
      ]
    }
  ]
})
```

#### Step 1.2: Load Everything

```
1. Read spec.md (contract, deliverables checklist)
2. Read spec-lite.md (summary)
3. Read user-stories/README.md (progress table)
4. Read ALL user-stories/story-N-*.md files
5. Read sub-specs/ (technical-spec, api-spec, etc.)
6. Read CHANGELOG.md (if exists)
7. Scan git log for commits referencing this spec
```

Build complete data model:
```json
{
  "spec": {
    "name": "feature-name",
    "date": "2026-02-22",
    "status": "Planning",
    "deliverables": [
      { "text": "Auth middleware", "checked": false, "fileExists": true }
    ]
  },
  "readme": {
    "stories": [
      { "number": 1, "title": "Auth", "status": "Completed", "tasks": "5/5" }
    ],
    "totalProgress": "5/15"
  },
  "storyFiles": [
    {
      "file": "story-1-auth.md",
      "number": 1,
      "status": "Completed ✅",
      "tasks": { "total": 5, "checked": 5 },
      "acceptanceCriteria": { "total": 4, "checked": 4 },
      "definitionOfDone": { "total": 5, "checked": 5 },
      "dependencies": ["None"]
    }
  ]
}
```

---

### Phase 2: Verification Checks

Run all checks, collect findings. Never stop at the first failure — report everything.

---

#### Check 1: Story File Integrity

**1a. Orphan detection — files without README entries:**
```
For each story-N-*.md file in user-stories/:
  Does README.md reference this story? → if not, flag as orphan
```

**1b. Phantom detection — README entries without files:**
```
For each story row in README.md table:
  Does a corresponding story-N-*.md file exist? → if not, flag as phantom
```

**1c. Status header present:**
```
Every story file must have:
  > **Status:** [Not Started | In Progress | Completed ✅]
If missing or malformed → flag
```

**1d. Required sections present:**
```
Every story file must have:
  - User Story (As a / I want to / So that)
  - Acceptance Criteria
  - Implementation Tasks
  - Definition of Done
If any section missing → flag
```

---

#### Check 2: Status Consistency

**2a. README ↔ story file status sync:**
```
For each story:
  README says "Completed" but file says "In Progress"? → discrepancy
  README says "Not Started" but file says "Completed"? → discrepancy
```

**2b. Task count accuracy:**
```
For each story:
  README says "5/7 tasks" but file has 6 total tasks with 4 checked? → mismatch
  Count actual - [ ] and - [x] in Implementation Tasks section
```

**2c. Total progress accuracy:**
```
README footer says "Total: 15/20 tasks (75%)"
Sum actual checked tasks across all stories
If sum doesn't match → flag
```

---

#### Check 3: Completion Integrity

**3a. Acceptance criteria verification (for "Completed" stories):**
```
If story status is "Completed ✅":
  Are ALL acceptance criteria checked? (- [x] Given...)
  Any unchecked criteria → flag as false completion
```

**3b. Definition of Done verification (for "Completed" stories):**
```
If story status is "Completed ✅":
  Is the entire Definition of Done section checked?
  - [x] All tasks completed
  - [x] All acceptance criteria met
  - [x] Tests passing
  - [x] Code reviewed
  - [x] Documentation updated
  Any unchecked items → flag as incomplete DoD
```

**3c. Task completion (for "Completed" stories):**
```
If story status is "Completed ✅":
  Are ALL implementation tasks checked? (- [x] N.X ...)
  Any unchecked tasks → flag
```

**3d. Premature status (for "In Progress" or "Not Started" stories):**
```
If story status is "Not Started" but has checked tasks → should be "In Progress"
If story status is "In Progress" but all tasks checked → should be "Completed"
```

---

#### Check 4: Dependency Validation

**4a. Dependency satisfaction:**
```
For each story with dependencies:
  Are all dependency stories "Completed ✅"?
  If story is "Completed" but a dependency is not → flag ordering violation
```

**4b. Circular dependencies:**
```
Build dependency graph
Check for cycles → flag if found
```

**4c. Missing dependency declarations:**
```
Cross-reference with spec.md and sub-specs/technical-spec.md
Flag if obvious dependencies are undeclared (heuristic — based on shared files/modules)
```

---

#### Check 5: Deliverables Checklist (spec.md)

**5a. Deliverable file existence:**
```
For each deliverable in spec.md checklist:
  Extract file paths mentioned
  Do the files exist? → if not, flag
  Is the checklist item checked but file doesn't exist? → flag as false deliverable
  Is the file present but checklist item unchecked? → flag as unsync'd
```

**5b. Spec status header:**
```
If ALL stories completed AND all deliverables checked:
  spec.md status should be "Complete" or "Completed"
  If not → flag
```

---

#### Check 6: Test Verification

**Run actual tests (not just trust checkboxes):**

```bash
# Detect test runner
if [ -f package.json ]; then
  # Check for spec-specific test scripts first
  npm run test:${spec_name} 2>/dev/null || npm test
elif [ -f pyproject.toml ] || [ -f setup.py ]; then
  python -m pytest
elif [ -f Cargo.toml ]; then
  cargo test
elif [ -f go.mod ]; then
  go test ./...
fi
```

**Report results:**
- Total tests, passed, failed, skipped
- If any failures → flag (stories cannot be "Complete" with failing tests)

**In `--pre-deploy` mode, additionally run:**
```bash
# Full regression suite
npm test                    # all tests
npx tsc --noEmit           # typecheck
npx eslint .               # lint
npx prettier --check .     # format
```

---

#### Check 7: Coverage Verification

**Run coverage analysis:**

```bash
# Auto-detect and run
npx vitest run --coverage 2>/dev/null || \
  npx jest --coverage 2>/dev/null || \
  npx c8 npm test 2>/dev/null
```

**Check thresholds:**
- New files (created by this spec): ≥80% line coverage
- Modified files: coverage not decreased
- Report overall coverage

---

#### Check 8: Spec Contract vs Implementation

**Drift detection — does the built thing match the specced thing?**

```
Read spec.md "Contract Summary" section
Read spec.md "Scope Boundaries" → Included / Excluded lists

For each "Included" item:
  Is there evidence of implementation? (files, tests, stories covering it)
  If not → flag as unimplemented scope

For each "Excluded" item:
  Is there implementation that shouldn't be there? (scope creep detection — heuristic)
```

This check is heuristic and may have false positives. Report with lower confidence.

---

### Phase 3: Verification Report

Present all findings in a structured report:

```
🔍 Spec Verification Report: 2026-02-22-feature-name

══════════════════════════════════════════════════
 CHECK                          STATUS   FINDINGS
══════════════════════════════════════════════════
 1. Story file integrity        ✅       All clean
 2. Status consistency          ❌       2 discrepancies
 3. Completion integrity        ⚠️       1 unchecked DoD item
 4. Dependency validation       ✅       All satisfied
 5. Deliverables checklist      ❌       3 items unsync'd
 6. Test verification           ✅       45/45 passing
 7. Coverage                    ⚠️       72% (below 80% threshold)
 8. Contract vs implementation  ✅       All scope items implemented
══════════════════════════════════════════════════

Overall: ⚠️ 4 issues found (2 auto-fixable, 2 need attention)

── Auto-Fixable ──────────────────────────────────

[FIX-1] README status mismatch
  Story 2: file says "Completed ✅", README says "In Progress"
  → Will update README

[FIX-2] README task count wrong
  Story 3: README says "3/5", actual is "5/5"
  → Will update README

[FIX-3] Deliverables checklist unsync'd
  3 deliverables exist but aren't checked in spec.md
  → Will check them off

[FIX-4] Spec status header
  All stories complete but spec.md says "Planning"
  → Will update to "Complete"

── Needs Attention ───────────────────────────────

[WARN-1] Unchecked Definition of Done
  Story 2: "Documentation updated" is unchecked
  → Was documentation actually updated? If yes, check it off.
    If no, run documentation agent.

[WARN-2] Coverage below threshold
  src/lib/feature.ts: 72% line coverage (threshold: 80%)
  → Add tests for uncovered lines 45-62, 78-85
```

Then prompt:
```
AskQuestion({
  title: "Verification Actions",
  questions: [
    {
      id: "action",
      prompt: "How would you like to proceed?",
      options: [
        { id: "fix_all", label: "Auto-fix all fixable issues" },
        { id: "fix_and_report", label: "Auto-fix + generate report file" },
        { id: "report_only", label: "Generate report file only (no changes)" },
        { id: "done", label: "I'll handle it manually" }
      ]
    }
  ]
})
```

---

### Phase 4: Auto-Fix (if requested)

#### 4.1: Sync README with Story Files

- Update status column to match story file headers
- Update task counts to match actual checked/total counts
- Recalculate total progress
- Update Quick Links with completion markers

#### 4.2: Sync Deliverables Checklist

- Check off deliverables whose files exist
- Uncheck deliverables whose files are missing (with warning)

#### 4.3: Fix Status Headers

- Stories with all tasks done → "Completed ✅"
- Stories with some tasks done → "In Progress"
- Stories with no tasks done → "Not Started"
- Spec with all stories done → "Complete"

#### 4.4: Generate/Update CHANGELOG

If all stories are complete and no CHANGELOG entry exists for this spec:
- Generate a Keep a Changelog entry from completed stories
- Prepend to CHANGELOG.md

#### 4.5: Trello Sync (if `--sync-trello`)

```
1. Search Trello board for cards matching spec/feature name
2. If found:
   - Update card description with completion summary
   - Move to "live" list if spec complete
3. If not found:
   - Create cards for completed features
   - Place in appropriate list
4. If multiple matches:
   - Present options for user to select
```

---

### Phase 5: Verification Report File

Write to `.writ/specs/[spec-folder]/verification-YYYY-MM-DD.md`:

```markdown
# Verification Report: [Feature Name]

> **Date:** YYYY-MM-DD
> **Spec:** [spec folder]
> **Result:** ✅ Passed / ⚠️ Passed with warnings / ❌ Failed

## Summary

| Check | Status | Details |
|-------|--------|---------|
| Story file integrity | ✅ | N stories, all well-formed |
| Status consistency | ✅ | README in sync (auto-fixed) |
| Completion integrity | ✅ | All criteria and DoD checked |
| Dependency validation | ✅ | All dependencies satisfied |
| Deliverables checklist | ✅ | N/N deliverables verified |
| Test verification | ✅ | X/X tests passing |
| Coverage | ⚠️ | X% average (threshold: 80%) |
| Contract alignment | ✅ | All scope items implemented |

## Test Results
- Total: X tests
- Passed: X
- Failed: 0
- Coverage: X%

## Stories
| # | Title | Status | Tasks | Criteria | DoD |
|---|-------|--------|-------|----------|-----|
| 1 | Auth | ✅ | 5/5 | 4/4 | 5/5 |
| 2 | API | ✅ | 6/6 | 3/3 | 5/5 |

## Issues Found & Resolved
- [FIX-1] README status sync (auto-fixed)
- [FIX-2] Task count correction (auto-fixed)

## Outstanding Warnings
- [WARN-1] Coverage below threshold on src/lib/feature.ts

## Recommendation
[Ready for release / Needs attention before release]
```

---

### Phase 6: Build Verification (when spec is complete)

If all stories are "Completed ✅" after fixes:

```bash
# Full build check
npm run build 2>&1      # or equivalent
npx tsc --noEmit 2>&1   # typecheck
npm test 2>&1            # full test suite
```

**Pass:**
```
✅ Spec verification COMPLETE

All 8 checks passed.
Build: ✅ successful
Tests: 45/45 passing
Coverage: 87% average

This spec is ready for /release.
```

**Fail:**
```
❌ Build verification FAILED

Build error in src/components/Feature.tsx:34
  Type 'string' is not assignable to type 'number'

Spec is NOT ready for release. Fix build errors and re-run /verify-spec.
```

---

## Integration with Writ

| Command | Relationship |
|---------|-------------|
| `/implement-story --all` | Auto-runs verify-spec after all stories complete |
| `/release` | Run verify-spec before releasing (verify-spec → release) |
| `/security-audit` | Complementary — verify-spec checks correctness, security-audit checks safety |
| `/status` | Quick overview; verify-spec is the deep validation |

**Recommended flow:**
```
/implement-story --all    # Build everything
/verify-spec              # Validate everything
/security-audit --quick   # Security check
/release                  # Ship it
```
