# Story 3 Verification Guide

## Purpose

This guide provides manual verification procedures for Story 3: "What Was Built" Records. Since Writ is a markdown-only project with no test suite, verification is performed through:

1. Format validation (documentation correctness)
2. Integration testing (dogfood on this spec)
3. Edge case checks (missing data handling)
4. Acceptance criteria mapping

## Verification Checklist

### ✅ Task 3.1: Format Documentation

- [ ] `.writ/docs/what-was-built-format.md` exists
- [ ] Document includes all mandatory fields table
- [ ] Document includes best-effort fields table
- [ ] Parsing guidance for each section is present
- [ ] Size and context budget guidelines defined
- [ ] Cross-story continuity process documented
- [ ] Backward compatibility notes included
- [ ] Example reference points to Story 2

**How to verify:** Read the documentation and confirm completeness against the story requirements.

---

### ✅ Task 3.2: Verification Procedures

- [ ] This verification guide exists
- [ ] All 8 tasks have verification steps
- [ ] Acceptance criteria verification steps defined
- [ ] Edge cases covered

**How to verify:** Self-referential — you're reading it now.

---

### ✅ Task 3.3: Gate 3.5 Extraction Logic

- [ ] `commands/implement-story.md` Gate 3.5 section updated
- [ ] Parsing logic for review agent output added
- [ ] Extraction covers all mandatory fields
- [ ] Extraction covers all best-effort fields
- [ ] Defensive parsing with fallbacks implemented
- [ ] Data stored in orchestrator state (not appended yet)

**How to verify:**

1. Read `commands/implement-story.md` lines around Gate 3.5
2. Confirm presence of:
   - Review agent output parsing instructions
   - Field extraction logic (files, decisions, tests, review outcome, drift)
   - Validation warnings for missing data
   - Storage in orchestrator state variable (e.g., `what_was_built_data`)

**Expected behavior:**
- Extract data from review agent sections: Coding Agent Output, Drift Analysis, Security Assessment, Boundary Compliance
- Store in structured format for later use at Gate 5
- Log warnings for missing optional fields
- Continue with partial data (no blocking)

---

### ✅ Task 3.4: Validation Logic

- [ ] Required field validation implemented
- [ ] Graceful degradation for missing fields
- [ ] Warning logs for validation failures
- [ ] Fallback values defined per `.writ/docs/what-was-built-format.md`

**How to verify:**

1. Check Gate 3.5 parsing logic for validation checks:
   - At least one file (created or modified) present
   - Review result is present
   - Implementation date can be generated

2. Confirm fallback behavior:
   - Missing files → empty lists with warning
   - Missing review result → "Unknown" with error log
   - Missing optional fields → omit section

**Expected behavior:**
- Mandatory fields: error logged if missing, fallback applied, pipeline continues
- Best-effort fields: warning logged if missing, section omitted, pipeline continues
- No blocking on incomplete data (per AC4)

---

### ✅ Task 3.5: Gate 5 Append Logic

- [ ] `commands/implement-story.md` Gate 5 section updated
- [ ] Append happens AFTER documentation agent completes
- [ ] Uses data from Gate 3.5 orchestrator state
- [ ] Formats according to `.writ/docs/what-was-built-format.md`
- [ ] Appends to story file with `---` separator

**How to verify:**

1. Read `commands/implement-story.md` Step 4 (Story Completion) or end of Gate 5
2. Confirm instructions to:
   - Retrieve `what_was_built_data` from orchestrator state
   - Format as markdown per the documented structure
   - Append to story file: `\n---\n\n## What Was Built\n\n{formatted_content}`
   - Include all mandatory fields with fallbacks
   - Include available best-effort fields

**Expected sections in output:**
```markdown
## What Was Built

**Implementation Date:** YYYY-MM-DD

### Files Created
[list or empty]

### Files Modified
[list or empty]

### Implementation Decisions
[list or omitted if empty]

### Test Results
[coverage info or "Verification: N/A"]

### Review Outcome
**Result:** PASS/FAIL/PAUSE
- **Drift:** level
- **Security:** risk level

### Deviations from Spec
[list or "None"]
```

---

### ✅ Task 3.6: Step 2 Dependency Loading

- [ ] `commands/implement-story.md` Step 2 (Load Context) updated
- [ ] Check for story dependencies
- [ ] Read "What Was Built" sections from dependency stories
- [ ] Apply size limits (1000 lines per record)
- [ ] Pass to coding agent in prompt
- [ ] Graceful fallback for incomplete dependencies

**How to verify:**

1. Read `commands/implement-story.md` Step 2 (Load Context)
2. Confirm new step (e.g., Step 2.7 or integrated into existing steps):
   - Parse dependencies from story file or spec
   - For each dependency, read dependency story file
   - Check for `## What Was Built` section
   - Extract full section content
   - Apply 1000-line truncation if needed
   - Pass to coding agent:
     ```
     ## Dependency Context
     
     **Story N completed — "What Was Built":**
     {record content}
     ```
3. Confirm fallback behavior:
   - Dependency story incomplete → warning, continue
   - Dependency story file missing → error log, continue
   - Only direct dependencies loaded (not transitive)

**Expected behavior:**
- Dependency records passed as additional context to coding agent
- Warning logged if dependency incomplete
- Pipeline continues with available context

---

### ✅ Task 3.7: Cross-Story Continuity Test Plan

- [ ] Test plan document created
- [ ] Dogfood test using this spec (Story 3 depends on Story 2)
- [ ] Verification steps for each gate
- [ ] Expected outcomes defined

**How to verify:**

1. Check for test plan document in this directory or `.writ/docs/`
2. Confirm it includes:
   - Test scenario: Story 3 reads Story 2's "What Was Built" record
   - Gate-by-gate verification steps
   - Expected coding agent context includes Story 2 details
   - Success criteria for cross-story continuity

**Manual test execution:**
- After Story 3 completes, verify:
  - Story 3's "What Was Built" section was auto-generated
  - Story 3's coding agent received Story 2's "What Was Built" record (check agent logs or output)
  - Story 4 (when run) will receive both Story 2 and Story 3 records

---

### ✅ Task 3.8: Acceptance Criteria Verification

See section below for detailed AC verification.

---

## Acceptance Criteria Verification

### AC1: "What Was Built" Section Appended at Gate 5

**Criterion:** Given a story that completes Gate 5 (documentation), when the orchestrator processes completion, then a "## What Was Built" section is appended to the story file

**How to verify:**
1. Complete a story through full pipeline (this story or a future story)
2. Open the completed story file
3. Scroll to bottom
4. Confirm presence of:
   ```markdown
   ---
   
   ## What Was Built
   
   **Implementation Date:** YYYY-MM-DD
   ```

**Pass if:**
- Section exists
- Separator `---` present
- Implementation date is ISO 8601 format
- At least Files Created/Modified and Review Outcome present

---

### AC2: Downstream Story Receives Record

**Criterion:** Given a completed story with "What Was Built" record, when a downstream story depends on it, then the downstream story's coding agent receives the record in its context

**How to verify:**
1. Complete Story 3 (has "What Was Built" section auto-generated)
2. Run Story 4 (depends on Story 3 per spec)
3. At Gate 1, inspect coding agent prompt or output
4. Confirm coding agent mentions Story 3's implementation details

**Pass if:**
- Coding agent prompt includes `## Dependency Context` section
- Story 3's "What Was Built" content is present in full or truncated form
- Coding agent references upstream decisions or files in its implementation

**Dogfood test:**
- Story 3 depends on Story 2 (per spec)
- This verification: check if Story 3's coding agent received Story 2's "What Was Built" record
- Expected: Coding agent knows Story 1 overlap, verification guide approach, no routing implementation

---

### AC3: Record Includes All Required Sections

**Criterion:** Given a review agent output from Gate 3, when "What Was Built" is generated, then it includes files created/modified, implementation decisions, test count/coverage, and review notes

**How to verify:**
1. Complete a story through Gate 3 (review)
2. At Gate 3.5, inspect orchestrator state or logs
3. Confirm extraction of:
   - Files created (list)
   - Files modified (list)
   - Implementation decisions (list or omitted)
   - Test results (coverage info or N/A)
   - Review outcome (result, drift, security)

**Pass if:**
- All mandatory fields present (files, review result)
- Best-effort fields attempted (decisions, tests)
- Missing data logged with warnings

---

### AC4: Graceful Degradation on Incomplete Data

**Criterion:** Given an incomplete review agent output, when "What Was Built" generation runs, then it uses partial data and logs a validation warning (doesn't block completion)

**How to verify:**
1. Simulate incomplete review output (or observe natural occurrence)
2. Check orchestrator logs during Gate 3.5 and Gate 5
3. Confirm warnings logged: `⚠️ "What Was Built" record incomplete — {reason}`
4. Confirm story completion proceeds anyway
5. Confirm "What Was Built" section includes available data with fallbacks

**Pass if:**
- Pipeline does NOT abort on missing optional data
- Warnings logged for validation issues
- Fallback values used per format documentation
- Story marked Completed ✅ even with partial record

---

### AC5: Multiple Dependencies Loaded

**Criterion:** Given multiple completed dependency stories, when Story 3 runs, then it receives "What Was Built" records from all dependencies

**How to verify:**
1. Run Story 3 (depends on Story 2 per spec; Story 2 depends on none)
2. At Gate 1, inspect coding agent context
3. Confirm Story 2's "What Was Built" record present
4. For future stories with 2+ dependencies, verify all are loaded

**Pass if:**
- All direct dependencies' records present in coding agent context
- Each dependency in separate section or clearly labeled
- Transitive dependencies NOT loaded (Story 3 should NOT receive Story 1 details directly)

---

## Edge Case Verification

### Edge Case 1: Missing Review Output Section

**Scenario:** Review agent output missing a section (e.g., no Drift Analysis)

**Expected behavior:**
- Gate 3.5 logs: `⚠️ Review agent output missing section: Drift Analysis`
- "What Was Built" → Deviations from Spec: "None"
- Review Outcome → Drift: "None"
- Pipeline continues

**How to test:** Inspect logs during Story 3 completion if review output is incomplete.

---

### Edge Case 2: Dependency Story Incomplete

**Scenario:** Story 3 depends on Story 2, but Story 2 status is "In Progress"

**Expected behavior:**
- Step 2 logs: `⚠️ Story 3 depends on Story 2 (not yet complete). Proceeding anyway — some integration points may be unavailable.`
- No "What Was Built" record loaded for Story 2
- Pipeline continues with available context

**How to test:** Start Story 3 before completing Story 2 (should not happen in normal flow, but test boundary).

---

### Edge Case 3: Large "What Was Built" Record

**Scenario:** Dependency story has a "What Was Built" record >1000 lines

**Expected behavior:**
- Step 2 truncates to 1000 lines
- Priority order: Files → Decisions → Tests → Review notes → Drift
- Log: `⚠️ Truncated Story N "What Was Built" record (1234 → 1000 lines)`
- Coding agent receives truncated version

**How to test:** Manually create a verbose "What Was Built" section in a test story, then load as dependency.

---

### Edge Case 4: Circular Dependencies

**Scenario:** Story A depends on Story B, Story B depends on Story A (should be prevented by spec validation)

**Expected behavior:**
- Detect in Step 2 (optional defensive check)
- Log error: `⚠️ Circular dependency detected: Story A ↔ Story B`
- Load available records, skip circular reference

**How to test:** Not applicable for this spec (no circular dependencies), but document behavior.

---

## Integration Test: Dogfood This Spec

**Scenario:** Story 3 reads Story 2's "What Was Built" record during its own implementation

**Steps:**
1. **Pre-condition:** Story 2 is marked Completed ✅ with "What Was Built" section (manual, lines 73-168)
2. **Execute:** Run `/implement-story story-3` (this story)
3. **Gate 0 (Arch Check):** Verify arch check agent receives Story 2 context if applicable
4. **Step 2 (Load Context):** Verify orchestrator detects Story 2 as dependency
5. **Step 2 (Load Context):** Verify Story 2's "What Was Built" section extracted
6. **Gate 1 (Coding Agent):** Verify coding agent prompt includes Story 2 record
7. **Gate 1 Output:** Verify coding agent mentions Story 2's verification approach or format
8. **Gate 5 (Documentation):** Verify documentation agent completes
9. **Story Completion:** Verify "What Was Built" section appended to `story-3-what-was-built-records.md`
10. **Post-condition:** Story 3 file has `## What Was Built` section with auto-generated content

**Success criteria:**
- Story 2 record loaded at Step 2
- Coding agent aware of Story 2's deliverables
- Story 3 "What Was Built" section auto-generated
- All mandatory fields present in Story 3 record

**Evidence to collect:**
- Orchestrator logs showing Story 2 record extraction
- Coding agent output mentioning Story 2 context
- Final Story 3 file with "What Was Built" section

---

## Definition of Done Verification

- [ ] All 8 tasks have implementation artifacts
- [ ] Format documentation complete and accurate
- [ ] Gate 3.5 extraction logic present in `implement-story.md`
- [ ] Gate 5 append logic present in `implement-story.md`
- [ ] Step 2 dependency loading logic present in `implement-story.md`
- [ ] Verification guide complete (this file)
- [ ] Cross-story continuity test plan defined (dogfood scenario above)
- [ ] All 5 acceptance criteria verifiable

---

## Post-Implementation Validation

After Story 3 completes and is marked ✅:

1. **Self-verification:** Check that Story 3's own "What Was Built" section was auto-generated correctly
2. **Format compliance:** Compare Story 3's record to `.writ/docs/what-was-built-format.md`
3. **Completeness:** Verify all mandatory fields present
4. **Story 4 readiness:** Confirm Story 4 will be able to load both Story 2 and Story 3 records

---

## Notes for Review Agent

This verification guide serves as the "test suite" for Story 3. When reviewing:

- Confirm all verification steps are addressable
- Confirm acceptance criteria map to verifiable outcomes
- Flag any gaps in verification coverage
- Confirm dogfood test is feasible with current spec state
