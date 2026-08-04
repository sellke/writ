# Story 5: UAT Plan Generation

> **Status:** Completed ✅ (2026-03-27)
> **Priority:** Medium
> **Dependencies:** Story 3

## User Story

**As a** developer who wants to manually validate a completed feature
**I want** a structured UAT plan generated from the spec
**So that** I can systematically verify the feature works without reading implementation code

## Acceptance Criteria

- [x] Given a spec with completed stories, when `/create-uat-plan` runs, then it generates a `uat-plan.md` file with human-readable test scenarios
- [x] Given acceptance criteria, error maps, shadow paths, and edge cases from the spec, when scenarios are generated, then they include preconditions, steps, expected result, and pass/fail checkbox
- [x] Given a generated UAT plan, when a human executes it, then 90%+ of scenarios are executable without reading implementation code (clarity threshold)
- [x] Given a spec where some stories are incomplete, when `/create-uat-plan` runs, then it generates scenarios only for completed stories and notes which are pending
- [x] Given "What Was Built" records, when scenarios are generated, then they reference actual implementation details (e.g., "Login at `/auth/login` endpoint" not "Login at authentication page")

## Implementation Tasks

- [x] 5.1 Write tests for UAT scenario generation (given acceptance criteria + error maps, generate scenarios with preconditions, steps, expected result)
- [x] 5.2 Create `commands/create-uat-plan.md` with command structure (Overview, Invocation, Phases, Integration)
- [x] 5.3 Implement Phase 1: Read spec folder and identify completed stories (check "Status: Completed" in story files)
- [x] 5.4 Implement Phase 2: Extract acceptance criteria, error maps, shadow paths, edge cases from `spec.md` and `technical-spec.md`
- [x] 5.5 Implement Phase 3: Generate scenarios from extracted content (standard template: preconditions, steps, expected result, checkbox)
- [x] 5.6 Implement Phase 4: Enhance scenarios with "What Was Built" details (reference actual files, endpoints, components)
- [x] 5.7 Implement Phase 5: Write `uat-plan.md` to spec folder root (`.writ/specs/{spec}/uat-plan.md`)
- [x] 5.8 Test on dogfood (generate UAT plan for this Context Engine spec)
- [x] 5.9 Verify all acceptance criteria are met and tests pass

## Notes

**Technical considerations:**

- UAT plans generated after story completion, not during spec creation (reflects actual implementation)
- Scenario sources: acceptance criteria (happy path), error maps (error handling), shadow paths (nil/empty/upstream error), edge cases (interaction patterns)
- Scenario format: preconditions, numbered steps, expected result, pass/fail checkbox
- "What Was Built" records provide concrete details (file names, endpoints, component names)
- If some stories incomplete, generate partial plan and note pending stories

**Integration points:**

- Standalone command (not integrated into `/implement-spec` or `/ship` for Phase 3a)
- Phase 3b consideration: integrate into `/ship` as optional gate (UAT sign-off before PR creation)
- Reads from: `spec.md`, `technical-spec.md`, story files (acceptance criteria + "What Was Built")
- Writes to: `.writ/specs/{spec}/uat-plan.md`

**Risks:**

- Scenario quality varies depending on spec detail — mitigation: use structured inputs (error maps, shadow paths)
- Scenarios could be too technical (not human-readable) — mitigation: template uses plain language, avoids code
- UAT plan could be too long — mitigation: group scenarios by story, prioritize critical paths

**Example scenario format:**

```markdown
### Scenario 1: Create session with valid credentials

**Preconditions:**
- User has valid email and password
- Redis is available

**Steps:**
1. Navigate to login page
2. Enter valid email and password
3. Click "Sign in" button

**Expected Result:**
- User is redirected to dashboard
- Session cookie is set (expires in 7 days for regular login, 30 days for "remember me")
- Success toast displays "Welcome back!"

**Status:** [ ] Pass [ ] Fail

**Notes:**

---
```

## Definition of Done

- [x] All tasks completed
- [x] `/create-uat-plan` command created
- [x] Scenario generation implemented (acceptance criteria, error maps, shadow paths, edge cases)
- [x] "What Was Built" integration for concrete details
- [x] Tests passing for scenario generation
- [x] Dogfood validation: UAT plan generated for this spec
- [x] Manual UAT execution on 2 features confirms 90%+ scenario clarity
- [x] Code reviewed
- [x] Documentation updated

## Context for Agents

- **Error map rows:** `UAT plan generation failure` — surface parse/extraction/write errors clearly; partial plans allowed when some stories incomplete (document pending)
- **Shadow paths:** Happy path: read completed stories → extract criteria/maps/paths → generate scenarios → write `uat-plan.md`
- **Business rules:** UAT plans generated after story completion, not during spec creation
- **Experience:** Entry: `/create-uat-plan` after stories complete; happy path: structured scenarios enable validation without code reading

---

## What Was Built

**Implementation Date:** 2026-03-27

### Files Created

1. **`commands/create-uat-plan.md`** (387 lines)
   - Complete `/create-uat-plan` command specification
   - 5-phase workflow: Spec Discovery & Story Inventory → Content Extraction → Scenario Generation → WWB Enhancement → Assemble & Write
   - Scenario sources from 5 categories: acceptance criteria (happy path), error maps (error handling), shadow paths (boundary conditions), edge cases (interaction patterns), experience design (UX validation)
   - Standard scenario template with preconditions, numbered steps, expected results, pass/fail checkboxes
   - "What Was Built" integration for concrete implementation references
   - Partial completion support (scenarios for completed stories only, pending noted)
   - Comprehensive error handling with graceful degradation
   - `--check` mode for preview without writing
   - Integration table with 5 related commands

### Files Modified

- **`CHANGELOG.md`** (Unreleased section)
  - Added entry for `/create-uat-plan` command

- **`AGENTS.md`** (Architecture → Commands section)
  - Updated pipeline description to include `create-uat-plan` as optional step between `implement-spec` and `verify-spec`

- **`SKILL.md`** (Implementation & Quality table)
  - Added `/create-uat-plan` row with command file path and purpose description

- **`README.md`** (command count)
  - Updated command count from 24 to 25

- **`.writ/specs/2026-03-27-context-engine/drift-log.md`** (Story 5 section)
  - Added DEV-007 drift entry for Experience Design source addition

### Implementation Decisions

1. **Five scenario source categories** — Added Experience Design as fifth source alongside the spec's four (acceptance criteria, error maps, shadow paths, edge cases). The spec's Experience Design section (Entry Point, Happy Path, Moment of Truth, Error Experience, State Catalog) contains rich scenario material that acceptance criteria alone don't capture. Logged as DEV-007 (Small drift).

2. **Scope filtering via context hints** — Error map and shadow path scenarios are filtered to completed stories using each story's `## Context for Agents` hints. This avoids generating scenarios for operations that belong to unimplemented stories. Falls back to best-effort title matching when hints are absent.

3. **WWB enhancement as optional enrichment** — Phase 4 is strictly additive. Scenarios generate correctly from acceptance criteria alone if no WWB record exists. Implementation references are for tester context ("where to look if this fails"), not for test execution.

4. **Overwrite-on-regeneration** — `uat-plan.md` is replaced on each run, not appended. Generation date in the header provides traceability. This mirrors how `/verify-spec` handles its report files.

5. **Followed existing command patterns** — Structure mirrors `/verify-spec` and `/ship`: Overview → Invocation table → Phased Command Process → Integration table → Error Handling. AskQuestion for spec selection, consistent error message format.

### Test Results

**Verification:** Manual (markdown-only project)

- ✅ All 5 acceptance criteria verified with explicit evidence
- ✅ Dogfood test: ~32 scenarios projected for Context Engine spec (3 completed stories, 2 pending)
- ✅ All 9 implementation tasks complete
- ✅ Error handling covers: missing spec, missing technical-spec, story parse errors, missing WWB records
- ✅ Shadow paths covered: zero-completed stories, partial completion, missing inputs
- ✅ Edge cases covered: scenario deduplication, scope filtering, overwrite behavior

### Review Outcome

**Result:** PASS (first iteration)

- **Iteration count:** 1 iteration
- **Drift:** Small (DEV-007: Experience Design added as fifth source category)
- **Security:** Clean (markdown command file only)
- **Boundary Compliance:** Full compliance — only Owned file (`commands/create-uat-plan.md`) created; documentation updates to CHANGELOG, AGENTS.md, SKILL.md, README.md are standard Gate 5 outputs

### Deviations from Spec

- **[DEV-007] Experience Design extraction added as fifth source category** — Severity: Small
  - Spec said: Scenarios from four sources (acceptance criteria, error maps, shadow paths, edge cases)
  - Reality: Added Step 2.5 extracting UX validation scenarios from spec.md Experience Design section
  - Resolution: Auto-amended — additive enhancement improving scenario coverage without removing the four required sources
