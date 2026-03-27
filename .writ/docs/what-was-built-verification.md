# What Was Built — Verification Guide

> **Purpose:** Verification artifacts for WWB format implementation
> **Audience:** Review agents, testing agents, and future maintainers
> **Related:** `.writ/docs/what-was-built-format.md`

## Overview

This document provides example inputs (review agent + testing agent outputs) and expected WWB records for verification. Since this is a markdown-only project with no test runner, verification is manual.

## Verification Examples

### Example 1: Full Mode — PASS on First Iteration

#### Input: Review Agent Output

```markdown
### REVIEW_RESULT: PASS

### Summary
All acceptance criteria satisfied. Implementation follows existing command patterns, comprehensive documentation, no security concerns. Code quality is high, no drift detected.

### Checklist Results

#### Acceptance Criteria
- [x] Given a completed spec, when UAT plan is generated, then it includes scenarios from AC, error maps, shadow paths
- [x] Given missing shadow paths, when UAT generation runs, then it degrades gracefully with available content

#### Code Quality
Clean. Follows existing markdown command patterns. Proper error handling with graceful degradation.

#### Security
**Risk Level:** Clean — markdown-only command, no code execution

#### Test Coverage
Manual verification checklist created. Format examples comprehensive.

#### Integration
No breaking changes. New command integrates cleanly with existing workflow.

### Drift Analysis

**Overall Drift:** None

No deviations from spec contract.
```

#### Input: Testing Agent Output

```markdown
### TEST_RESULT: PASS

### Test Summary
- Total tests run: 0 (markdown-only project)
- Manual verification: Complete

### Coverage Report
N/A — markdown-only deliverable

Manual verification artifacts:
- `.writ/docs/uat-plan-verification.md` created (verification checklist)
- 3 example UAT plans generated and validated

### Coverage Assessment
✅ All acceptance criteria covered by manual verification examples.
```

#### Expected WWB Record

```markdown
## What Was Built

**Implementation Date:** 2026-03-27

### Files Created

1. **`commands/create-uat-plan.md`** (287 lines)
   - New command for UAT plan generation from completed stories

2. **`.writ/docs/uat-plan-format.md`** (145 lines)
   - Format reference for UAT scenarios

### Files Modified

- **`commands/implement-story.md`** Step 2 (lines 40-58)
  - Added UAT plan path check and loading logic

### Implementation Decisions

1. UAT generation timing: After all stories complete (not per-story)
2. Source prioritization: Acceptance criteria > error maps > shadow paths > edge cases
3. Format: Preconditions, steps, expected result, checkbox (manual execution)
4. Error handling: Graceful degradation if spec sources incomplete

### Test Results

- **Tests:** Manual verification complete
- **Coverage:** N/A (markdown-only deliverable)
- **Verification artifacts:** `.writ/docs/uat-plan-verification.md` (checklist + 3 examples)

### Review Outcome

**Result:** PASS (iteration 1)

- **Security:** Clean (markdown-only command, no execution)
- **Drift:** None
- **Notes:** Format well-structured, examples comprehensive

### Deviations from Spec

None — implementation matched spec contract.
```

---

### Example 2: Full Mode — FAIL on First, PASS on Second

#### Input: Review Agent Output (Iteration 1)

```markdown
### REVIEW_RESULT: FAIL

### Summary
Two issues: acceptance criterion "duplicate email rejection" not implemented, and SQL injection vulnerability in search endpoint.

### Issues Found

- **Issue:** Acceptance criterion "duplicate email rejection" not implemented
- **Location:** `src/routes/auth.ts:45` — no uniqueness check before insert
- **Severity:** Critical
- **Suggested Fix:** Add `SELECT count(*) FROM users WHERE email = $1` check before INSERT, return 409 Conflict. Add test case.

- **Issue:** SQL injection in search endpoint
- **Location:** `src/routes/search.ts:34` — `db.query(\`SELECT * FROM items WHERE name LIKE '%${query}%'\`)`
- **Severity:** Critical
- **Suggested Fix:** Use parameterized query: `db.query('SELECT * FROM items WHERE name LIKE $1', [\`%${query}%\`])`. Add test with malicious input.

### Security Assessment
**Risk Level:** High — SQL injection via string concatenation in query.

### Drift Analysis

**Overall Drift:** None
```

#### Input: Review Agent Output (Iteration 2)

```markdown
### REVIEW_RESULT: PASS

### Summary
All issues from iteration 1 resolved. Duplicate email check implemented with proper test coverage. SQL injection fixed with parameterized queries. No remaining issues.

### Checklist Results

#### Acceptance Criteria
- [x] Given duplicate email, when registration attempted, then 409 Conflict returned — Verified in `auth.test.ts`
- [x] Given malicious input, when search executed, then query safely parameterized — Verified in `search.test.ts`

#### Code Quality
Clean. Proper error handling. No debug artifacts.

#### Security
**Risk Level:** Clean — Parameterized queries used throughout, input validation present.

#### Drift Analysis

**Overall Drift:** None
```

#### Input: Testing Agent Output

```markdown
### TEST_RESULT: PASS

### Test Summary
- Total tests run: 18
- Passed: 18
- Failed: 0

### Coverage Report
| File | Lines | Branches | Functions | Status |
|------|-------|----------|-----------|--------|
| src/routes/auth.ts | 91% | 85% | 100% | ✅ New file ≥80% |
| src/routes/search.ts | 88% | 80% | 100% | ✅ New file ≥80% |

- New files average: 89.5% line coverage
- Coverage threshold met: YES

### Coverage Assessment
✅ All acceptance criteria covered by tests.
```

#### Expected WWB Record

```markdown
## What Was Built

**Implementation Date:** 2026-03-27

### Files Created

1. **`src/routes/auth.ts`** — User registration with duplicate email check
2. **`src/routes/search.ts`** — Search endpoint with parameterized queries

### Files Modified

- **`src/app.ts`** — Registered new routes

### Implementation Decisions

1. Duplicate email handling: Check before insert, return 409 Conflict with user-friendly message
2. SQL injection prevention: All queries use parameterized format (`$1`, `$2` placeholders)
3. Error responses: Structured JSON with `error`, `message`, `statusCode` fields

### Test Results

- **Tests:** 18 passing, 0 failing
- **Coverage:** 89.5% on new files
- **Test files:** `__tests__/routes/auth.test.ts`, `__tests__/routes/search.test.ts`

### Review Outcome

**Result:** PASS (iteration 2)

- **Security:** Clean (SQL injection fixed, parameterized queries throughout)
- **Drift:** None
- **Notes:** Iteration 1 found 2 Critical issues (duplicate email, SQL injection) — both resolved in iteration 2

### Deviations from Spec

None — implementation matched spec contract after iteration 2 fixes.
```

---

### Example 3: `--quick` Mode (Degraded)

#### Input: Coding Agent Output

```markdown
## Implementation Complete

### Files Created
- `src/lib/feature.ts` - Main feature implementation
- `src/components/Feature.tsx` - React component

### Files Modified
- `src/app/layout.tsx` - Added provider wrapper

### Tests Written
- `__tests__/lib/feature.test.ts`
  - `should convert values correctly`
  - `should handle edge cases`
  - `should throw on invalid input`

### Implementation Decisions
- Used existing auth context instead of creating new provider
- Error handling: try-catch blocks with toast notifications
- State management: Local useState (feature scoped)

### Self-Check Results
- **Tests:** 12 passing, 0 failing (test runner: vitest)
- **Typecheck:** ✅ clean
- **Self-fixed:** None
```

#### Input: Testing Agent Output

```markdown
### TEST_RESULT: PASS

### Test Summary
- Total tests run: 12
- Passed: 12
- Failed: 0

### Coverage Report
| File | Lines | Branches | Functions | Status |
|------|-------|----------|-----------|--------|
| src/lib/feature.ts | 86% | 82% | 100% | ✅ ≥80% |
| src/components/Feature.tsx | 82% | 78% | 100% | ✅ ≥80% |

- New files average: 84% line coverage
- Coverage threshold met: YES
```

#### Expected WWB Record

```markdown
## What Was Built

**Implementation Date:** 2026-03-27

**Mode:** `--quick` (review and documentation skipped — WWB sourced from coding and testing agents only)

### Files Created

1. **`src/lib/feature.ts`** — Main feature implementation
2. **`src/components/Feature.tsx`** — React component

### Files Modified

- **`src/app/layout.tsx`** — Added provider wrapper

### Implementation Decisions

1. Used existing auth context instead of creating new provider
2. Error handling: try-catch blocks with toast notifications
3. State management: Local useState (feature scoped)

### Test Results

- **Tests:** 12 passing, 0 failing (vitest)
- **Coverage:** 84% on new files
- **Test files:** `__tests__/lib/feature.test.ts`

### Review Outcome

**Result:** Not reviewed (skipped in `--quick` mode)
```

---

## Verification Checklist

Use this checklist to verify WWB format implementation:

### Format Structure

- [ ] WWB record starts with `## What Was Built` heading
- [ ] Implementation date present in `YYYY-MM-DD` format
- [ ] Degraded mode note present when `--quick` used
- [ ] All required sections present (Files Created/Modified, Decisions, Tests, Review)
- [ ] Optional sections (Lessons Learned, Deviations) present when applicable

### Data Source Integration

- [ ] Files created/modified sourced from review agent OR coding agent
- [ ] Implementation decisions sourced from review agent OR coding agent
- [ ] Test count/coverage sourced from testing agent
- [ ] Review notes sourced from review agent (when not `--quick`)

### Graceful Degradation

- [ ] Missing review data → uses coding agent + testing agent, includes note
- [ ] Missing testing data → uses review agent + coding agent, includes note
- [ ] Missing fields → shows "Not captured" or omits subsection, logs warning
- [ ] `--quick` mode → sources from coding + testing only, includes mode note
- [ ] Unparseable prose → extracts what's possible, uses "Partial data" note

### Cross-Story Continuity

- [ ] WWB record readable by downstream story's coding agent
- [ ] Key decisions documented clearly for future reference
- [ ] File paths precise and complete
- [ ] Implementation approach variations from spec captured

### Validation Warnings

- [ ] Orchestrator logs warnings for missing data
- [ ] Pipeline never blocks on incomplete WWB data
- [ ] Partial WWB records still appended
- [ ] Validation warnings visible in pipeline output

## Manual Verification Process

For each completed story in this repo:

1. **Read the story file** — locate `## What Was Built` section
2. **Verify format** — check against structure in `what-was-built-format.md`
3. **Check required fields** — all mandatory fields present or marked "Not captured"
4. **Validate data sources** — cross-reference review and testing agent outputs if available
5. **Assess completeness** — would downstream story have enough context?

## Example Verification (Story 2)

Story 2's WWB record can be found in `.writ/specs/2026-03-27-context-engine/user-stories/story-2-agent-specific-spec-views.md`. Verify:

- [ ] Record exists at end of file
- [ ] Format matches specification
- [ ] Files created/modified listed with descriptions
- [ ] Implementation decisions captured (scope overlap, Story 1 completion, etc.)
- [ ] Review outcome present (PASS with drift note)
- [ ] Deviations documented (DEV-001, DEV-002)

## Notes for Future Verification

When implementing Story 4 (context routing), verify that:

- Coding agent receives WWB records from dependency stories
- WWB content appears in coding agent prompt
- Cross-story continuity improves (Story 3+ builds on actual implementation)

This verification is deferred to Story 4 testing.
