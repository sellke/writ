# Story 3 Integration Test Plan: Cross-Story Continuity

## Purpose

This test plan validates that "What Was Built" records enable cross-story continuity by dogfooding the Context Engine spec itself. Story 3 depends on Story 2, making it the perfect test case for verifying the full flow.

## Test Strategy

**Approach:** Manual integration test via dogfooding
- **Test subject:** Story 3 (this story) implementation
- **Dependency:** Story 2 (completed with manual WWB section)
- **Validation:** Story 3's coding agent receives and uses Story 2's WWB record
- **Evidence:** Agent outputs, logs, and final Story 3 WWB section

## Test Scenarios

### Scenario 1: Dependency WWB Loading (Step 2)

**Objective:** Verify Step 2 loads Story 2's "What Was Built" section and passes to coding agent

**Pre-conditions:**
- Story 2 marked `Completed ✅` (status: true as of 2026-03-27)
- Story 2 has `## What Was Built` section (lines 73-168 of story-2-agent-specific-spec-views.md)
- Story 3 has `> **Dependencies:** Story 2` in metadata

**Test Steps:**

1. **Execute:** Run `/implement-story story-3`
2. **Observe:** Step 2 (Load Context) orchestrator logs
3. **Check:** Look for log message:
   ```
   ✓ Loading "What Was Built" from Story 2...
   ✓ Story 2 WWB record loaded (95 lines)
   ```
4. **Verify:** No warning about incomplete dependency
5. **Verify:** No error about missing WWB section

**Expected Results:**
- Story 2's WWB section successfully extracted (lines 73-168, approximately 95 lines)
- No truncation needed (under 1000-line limit)
- WWB content passed to coding agent in prompt

**Pass Criteria:**
- ✅ Story 2 dependency detected
- ✅ WWB section found and extracted
- ✅ No warnings or errors logged
- ✅ Coding agent receives dependency context

---

### Scenario 2: Coding Agent Uses Dependency Context (Gate 1)

**Objective:** Verify coding agent is aware of Story 2's implementation and builds on it

**Pre-conditions:**
- Scenario 1 passed (WWB loaded)
- Coding agent prompt includes Story 2 WWB content

**Test Steps:**

1. **Execute:** Continue Story 3 implementation to Gate 1
2. **Observe:** Coding agent output
3. **Check:** Look for references to Story 2 details:
   - Mentions Story 1 overlap discovery
   - References verification approach (manual, not automated)
   - Acknowledges format already exists (Story 1)
   - Aware of spec-lite-format-verification.md creation
4. **Verify:** Coding agent builds on existing work rather than reinventing

**Expected Results:**
- Coding agent demonstrates knowledge of Story 2's deliverables
- Implementation decisions reference upstream context
- No duplicate work (e.g., doesn't recreate verification guide)
- Continuity in approach (follows Story 2's verification pattern)

**Pass Criteria:**
- ✅ Coding agent mentions Story 2 implementation in output
- ✅ Decisions informed by Story 2 context (not assumptions)
- ✅ No scope overlap or duplication of Story 2 work

---

### Scenario 3: WWB Extraction at Gate 3.5

**Objective:** Verify Gate 3.5 extracts data from review agent output and stores in orchestrator state

**Pre-conditions:**
- Gate 3 (Review Agent) completes
- Review agent output contains required sections

**Test Steps:**

1. **Execute:** Continue Story 3 to Gate 3 completion
2. **Observe:** Gate 3.5 orchestrator logs
3. **Check:** Look for extraction log messages:
   ```
   ✓ Extracting "What Was Built" data from review agent output...
   ✓ Files created: 3 files
   ✓ Files modified: 1 file
   ✓ Implementation decisions: 5 items
   ✓ Review outcome: PASS
   ✓ Drift: {level}
   ✓ Security: {level}
   ✓ Stored in what_was_built_data for Gate 5 append
   ```
4. **Verify:** No validation errors for mandatory fields
5. **Check:** Warnings logged if best-effort fields missing (acceptable)

**Expected Results:**
- Files created/modified parsed from coding agent output (via review agent)
- Implementation decisions extracted
- Test results captured (from Gate 4 if available, else N/A)
- Review outcome fields populated
- Drift analysis deviations extracted (if any)

**Pass Criteria:**
- ✅ All mandatory fields extracted (files, review result)
- ✅ Best-effort fields attempted
- ✅ Data stored in `what_was_built_data` object
- ✅ Pipeline continues (no blocking)

---

### Scenario 4: WWB Validation with Missing Fields (Gate 3.5)

**Objective:** Verify graceful degradation when review agent output is incomplete

**Pre-conditions:**
- Review agent output may have missing sections (edge case)

**Test Steps:**

1. **Simulate:** (Natural occurrence if review output incomplete)
2. **Observe:** Gate 3.5 logs for validation warnings:
   ```
   ⚠️ Review agent output missing section: Implementation Decisions
   ⚠️ WWB validation: Using fallback for implementation_decisions
   ```
3. **Verify:** Pipeline continues despite warnings
4. **Verify:** `what_was_built_data` contains fallback values

**Expected Results:**
- Missing optional sections logged as warnings
- Fallback values used per `.writ/docs/what-was-built-format.md`
- Pipeline does NOT abort
- Partial data stored for use at Gate 5

**Pass Criteria:**
- ✅ Warnings logged for missing fields
- ✅ Fallback values applied
- ✅ Pipeline continues to Gate 4
- ✅ No blocking errors

---

### Scenario 5: WWB Append at Step 4

**Objective:** Verify "What Was Built" section is appended to Story 3 file after Gate 5 completes

**Pre-conditions:**
- All gates passed (Gate 5 documentation complete)
- `what_was_built_data` populated from Gate 3.5

**Test Steps:**

1. **Execute:** Complete Story 3 through all gates
2. **Observe:** Step 4 (Story Completion) logs:
   ```
   ✓ Formatting "What Was Built" record...
   ✓ Appending to story file: story-3-what-was-built-records.md
   ```
3. **Open:** `story-3-what-was-built-records.md`
4. **Scroll to bottom:** Look for `## What Was Built` section
5. **Verify:** Section structure matches `.writ/docs/what-was-built-format.md`

**Expected Content:**

```markdown
---

## What Was Built

**Implementation Date:** 2026-03-27

### Files Created

1. **`.writ/docs/what-was-built-format.md`** (~300 lines)
   - Comprehensive format documentation
   - Field definitions (mandatory + best-effort)
   - Parsing guidance for each section

2. **`.writ/specs/2026-03-27-context-engine/user-stories/story-3-verification-guide.md`** (~250 lines)
   - Manual verification procedures
   - Acceptance criteria mapping

3. **`.writ/specs/2026-03-27-context-engine/user-stories/story-3-integration-test-plan.md`** (~200 lines)
   - Cross-story continuity test plan

### Files Modified

- **`commands/implement-story.md`** (Gate 3.5, Step 4, Step 2 sections)
  - Gate 3.5: Added WWB extraction logic
  - Step 4: Updated WWB record assembly process
  - Step 2: Enhanced dependency loading with size limits

### Implementation Decisions

[Decisions from coding agent output]

### Test Results

**Verification:** Manual (markdown-only project)
- ✅ Format documentation complete
- ✅ Verification procedures defined
- ✅ Integration test plan created
- ✅ All modifications to implement-story.md complete

### Review Outcome

**Result:** PASS

- **Iteration count:** {N} iteration(s)
- **Drift:** {level}
- **Security:** Clean (documentation only)

### Deviations from Spec

[List or "None"]
```

**Pass Criteria:**
- ✅ `## What Was Built` section present
- ✅ Separator `---` before section
- ✅ Implementation date in YYYY-MM-DD format
- ✅ All mandatory sections present (Files, Review Outcome)
- ✅ Content matches template from format doc

---

### Scenario 6: Story 4 Reads Story 3's WWB (Forward Continuity)

**Objective:** Verify downstream story (Story 4) can read Story 3's auto-generated WWB record

**Pre-conditions:**
- Story 3 completed with WWB section appended
- Story 4 depends on Story 3 (per spec)

**Test Steps:**

1. **Execute:** Run `/implement-story story-4` (after Story 3 completes)
2. **Observe:** Step 2 logs for Story 4:
   ```
   ✓ Loading "What Was Built" from Story 3...
   ✓ Story 3 WWB record loaded (120 lines)
   ```
3. **Verify:** Story 4's coding agent receives Story 3's WWB
4. **Check:** Story 4 coding agent references Story 3's deliverables

**Expected Results:**
- Story 4 coding agent knows what Story 3 produced
- Story 4 builds on Story 3's implementation (context routing)
- No assumptions or rework of Story 3's functionality

**Pass Criteria:**
- ✅ Story 3 WWB loaded at Story 4 Step 2
- ✅ Story 4 coding agent demonstrates Story 3 context
- ✅ Cross-story continuity maintained

---

## Acceptance Criteria Mapping

### AC1: WWB Section Appended at Gate 5

**Validated by:** Scenario 5

**Evidence:**
- Story 3 file has `## What Was Built` section after completion
- Section format matches documentation
- Appended after `---` separator

---

### AC2: Downstream Story Receives Record

**Validated by:** Scenario 2 (Story 3 receives Story 2's WWB), Scenario 6 (Story 4 receives Story 3's WWB)

**Evidence:**
- Story 3 coding agent receives Story 2 WWB
- Story 4 coding agent receives Story 3 WWB (when Story 4 runs)
- Coding agent outputs reference upstream implementation

---

### AC3: Record Includes All Required Sections

**Validated by:** Scenario 3, Scenario 5

**Evidence:**
- Gate 3.5 extraction logs show all fields attempted
- Final Story 3 WWB section contains:
  - Files created/modified
  - Implementation decisions
  - Test count/coverage
  - Review notes (result, drift, security)

---

### AC4: Graceful Degradation on Incomplete Data

**Validated by:** Scenario 4

**Evidence:**
- Validation warnings logged for missing fields
- Pipeline continues to completion
- Partial WWB record appended (not blocked)

---

### AC5: Multiple Dependencies Loaded

**Validated by:** Scenario 1 (for Story 3, though only 1 dependency)

**Evidence:**
- Story 2 WWB loaded successfully
- For stories with 2+ dependencies (future), all direct dependencies loaded

---

## Edge Cases

### Edge Case A: Dependency Incomplete

**Scenario:** Story 3 runs before Story 2 is marked complete

**Expected Behavior:**
- Step 2 logs: `⚠️ Story 3 depends on Story 2 (not yet complete). Proceeding anyway...`
- No WWB loaded for Story 2
- Pipeline continues with available context

**Test:** Manually revert Story 2 status to "In Progress" and run Story 3 Step 2

---

### Edge Case B: Large WWB Record (>1000 lines)

**Scenario:** Dependency has verbose WWB section exceeding limit

**Expected Behavior:**
- Step 2 truncates to 1000 lines using priority order
- Log: `⚠️ Truncated Story N "What Was Built" record (1234 → 1000 lines)`
- Truncated version passed to coding agent

**Test:** Manually create a large WWB section in a test story (or observe if Story 3's WWB is unexpectedly large)

---

### Edge Case C: No Dependencies

**Scenario:** Story 1 has no dependencies

**Expected Behavior:**
- Step 2 skips dependency loading step
- No warnings logged
- Coding agent receives story content and spec context only

**Test:** Observe Story 1 execution logs (historical)

---

## Success Criteria

Story 3 implementation is successful if:

1. ✅ Story 2's WWB record loaded and passed to Story 3 coding agent
2. ✅ Story 3 coding agent demonstrates awareness of Story 2's implementation
3. ✅ Gate 3.5 successfully extracts data from review agent output
4. ✅ Story 3's WWB section auto-generated and appended to story file
5. ✅ Story 3's WWB format matches documentation
6. ✅ All mandatory fields present in Story 3's WWB
7. ✅ Validation warnings logged but don't block completion
8. ✅ Story 4 can load Story 3's WWB when it runs

## Evidence Collection

During Story 3 execution, collect:

1. **Step 2 logs** — dependency loading and WWB extraction
2. **Coding agent output** — mentions of Story 2 context
3. **Gate 3.5 logs** — WWB data extraction and validation
4. **Step 4 logs** — WWB formatting and append
5. **Final story file** — `story-3-what-was-built-records.md` with WWB section
6. **Story 4 logs** (when run) — loading Story 3's WWB

## Post-Test Validation

After Story 3 completes:

1. **Self-verification:** Compare Story 3's WWB section to format documentation
2. **Completeness:** Verify all mandatory fields present
3. **Format compliance:** Check structure matches template
4. **Readability:** Ensure WWB is human-readable and useful for Story 4

## Notes for Review Agent

- This test plan is the "test suite" for Story 3's cross-story continuity feature
- All scenarios are manual (no automated test framework for markdown projects)
- Evidence should be collected from orchestrator logs and file contents
- Success = dogfood validation complete + Story 4 readiness confirmed
