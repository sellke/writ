# Create UAT Plan Command (create-uat-plan)

## Overview

Generate a structured User Acceptance Test plan from a completed (or partially completed) specification. Reads story files, spec contracts, and technical sub-specs to produce human-readable test scenarios that enable manual validation **without reading implementation code**.

The UAT plan bridges the gap between "AI says it works" and "human confirmed it works." Scenarios are derived from four structured sources — acceptance criteria, error maps, shadow paths, and edge cases — then enriched with concrete implementation details from "What Was Built" records.

**Design principle:** UAT plans are generated **after** story completion, not during spec creation. They reflect actual implementation, not spec intentions.

## Invocation

| Invocation | Behavior |
|---|---|
| `/create-uat-plan` | Interactive — select spec from `.writ/specs/` |
| `/create-uat-plan [spec-folder]` | Generate UAT plan for the specified spec |
| `/create-uat-plan --check` | Preview scenario count and coverage without writing file |

## Command Process

### Phase 1: Spec Discovery & Story Inventory

#### Step 1.1: Select Specification

**If spec folder argument provided:** Resolve to `.writ/specs/{spec-folder}/`. Verify `spec.md` exists.

**If not specified:**
```
AskQuestion({
  title: "UAT Plan Generation",
  questions: [{
    id: "spec",
    prompt: "Which specification needs a UAT plan?",
    options: [
      // Dynamically populated from .writ/specs/
      { id: "latest", label: "[DATE]-[name] (most recent)" },
      { id: "spec_2", label: "[DATE]-[name]" }
    ]
  }]
})
```

#### Step 1.2: Inventory Stories

Read all story files from `{spec-folder}/user-stories/story-*.md`.

For each story file:
1. Parse status from header: `> **Status:** [Not Started | In Progress | Completed ✅]`
2. Parse story number and title
3. Classify as **completed** or **pending**

Build the story inventory:

```
completed_stories = stories where status is "Completed ✅"
pending_stories = stories where status is NOT "Completed ✅"
```

**If zero completed stories:**
- Write a minimal `uat-plan.md` with:
  ```markdown
  # UAT Plan: [Spec Name]

  > Generated: YYYY-MM-DD
  > Status: No completed stories — plan will be populated as stories complete.
  ```
- Report: "No completed stories found. UAT plan stub created."
- Exit.

**Output:**
```
📋 Found N completed stories (M pending) in [spec-name]
   Completed: Story 1, Story 3, Story 4
   Pending: Story 2, Story 5
```

---

### Phase 2: Content Extraction

Extract scenario source material from the spec package. Four categories, each producing a distinct scenario type.

#### Step 2.1: Extract Acceptance Criteria (→ happy path scenarios)

For each **completed** story, read the `## Acceptance Criteria` section. Parse each criterion:

```
Given [precondition], when [action], then [expected result]
```

Each acceptance criterion becomes one scenario. Preserve the Given/When/Then structure — it maps directly to Preconditions/Steps/Expected Result.

**Parsing rules:**
- Look for `- [x]` checkboxes (completed stories have all criteria checked)
- Extract the text after the checkbox
- If criteria don't follow Given/When/Then format, treat the full text as the scenario description and generate best-effort preconditions/steps/expected from context

#### Step 2.2: Extract Error Maps (→ error handling scenarios)

Read `{spec-folder}/sub-specs/technical-spec.md` (or `{spec-folder}/technical-spec.md`).

Look for the `## Error & Rescue Map` section (or similar: `## Error Map`, `## Error Handling`). Parse the table rows:

| Operation | What Can Fail | Planned Handling | Test Strategy |
|---|---|---|---|

Each error map row becomes one scenario:
- **Preconditions:** Set up the failure condition described in "What Can Fail"
- **Steps:** Trigger the operation
- **Expected Result:** Verify the "Planned Handling" behavior occurs

**Scope filtering:** Only generate error scenarios for operations related to **completed** stories. Use the story's `## Context for Agents` hints (if present) to determine which error map rows are relevant:
- Parse `- Error map rows: [row1, row2, ...]` from the story's context hints
- If no context hints, use best-effort matching by operation name against story title and tasks

#### Step 2.3: Extract Shadow Paths (→ boundary condition scenarios)

From the same technical spec, look for `## Shadow Paths` section. Parse the table:

| Flow | Happy Path | Nil Input | Empty Input | Upstream Error |
|---|---|---|---|---|

Each non-happy-path column becomes a scenario:
- **Nil Input** → scenario verifying behavior when required input is absent
- **Empty Input** → scenario verifying behavior with empty/zero-length input
- **Upstream Error** → scenario verifying behavior when a dependency fails

**Scope filtering:** Same approach as error maps — match flows to completed stories via context hints or story title matching.

#### Step 2.4: Extract Edge Cases (→ interaction pattern scenarios)

From the technical spec, look for `## Interaction Edge Cases` section. Parse the table:

| Edge Case | Planned Handling |
|---|---|

Each edge case becomes one scenario:
- **Preconditions:** Set up the edge case condition
- **Steps:** Trigger the interaction
- **Expected Result:** Verify the planned handling occurs

**Scope filtering:** Same approach — match to completed stories.

#### Step 2.5: Extract Experience Design (→ UX validation scenarios)

From `spec.md`, read the `## Experience Design` section (or `## 🎯 Experience Design`). Extract:

- **Entry Point** → scenario verifying the user can reach the feature
- **Happy Path Flow** → walkthrough scenario (may overlap with AC scenarios; deduplicate)
- **Moment of Truth** → critical validation scenarios
- **Error Experience** → user-facing error scenarios (complements error map scenarios with UX focus)
- **State Catalog** → scenarios for each documented state (empty, first-use, error, complete)

These produce higher-level, user-journey scenarios that complement the granular AC/error scenarios.

---

### Phase 3: Scenario Generation

Transform extracted content into structured scenarios using the standard template.

#### Step 3.1: Generate Scenarios

For each extracted item, produce a scenario following this template:

```markdown
### Scenario N: [Descriptive title]

**Source:** [Acceptance Criteria | Error Map | Shadow Path | Edge Case | Experience Design] — Story N

**Preconditions:**
- [Setup requirement 1]
- [Setup requirement 2]

**Steps:**
1. [Action 1]
2. [Action 2]
3. [Verification action]

**Expected Result:**
- [Observable outcome 1]
- [Observable outcome 2]

**Status:** [ ] Pass  [ ] Fail

**Notes:**

---
```

#### Step 3.2: Apply Scenario Quality Rules

Each scenario must satisfy these clarity criteria:

1. **Self-contained** — A human can execute it without reading other scenarios or source code
2. **Observable outcomes** — Expected results describe what the tester can see/verify, not internal state
3. **Concrete steps** — "Click the Submit button" not "Submit the form"; "Navigate to `/settings`" not "Go to settings"
4. **No implementation jargon** — Avoid function names, class names, or internal architecture terms in steps and expected results (these belong only in the "What Was Built" enhancement notes, not in tester-facing content)
5. **Numbered steps** — Always use ordered steps, even for single-step scenarios

#### Step 3.3: Group and Order Scenarios

Organize scenarios within the UAT plan:

1. **Group by story** — each completed story gets its own section
2. **Within each story, order by source type:**
   - Happy path scenarios (from acceptance criteria) first
   - Error handling scenarios (from error maps) second
   - Boundary condition scenarios (from shadow paths) third
   - Interaction edge cases fourth
   - Experience/UX scenarios last (often overlap with happy path; deduplicate)
3. **Number scenarios globally** — sequential across the entire plan (Scenario 1, 2, 3... not restarting per story)

#### Step 3.4: Deduplicate

Acceptance criteria and experience design scenarios may overlap (both describe the happy path). When two scenarios cover the same behavior:
- Keep the more specific one (usually the AC scenario)
- If the experience design scenario adds UX-specific details (feedback model, state transitions), keep both but note the relationship
- Never generate duplicate scenarios with identical steps and expected results

---

### Phase 4: "What Was Built" Enhancement

Enrich scenarios with concrete implementation details from completed stories' "What Was Built" records.

#### Step 4.1: Load WWB Records

For each completed story, check for `## What Was Built` section. Extract:
- **Files Created** — actual file paths
- **Files Modified** — actual file paths and change descriptions
- **Implementation Decisions** — concrete details about how features were built

#### Step 4.2: Enhance Scenarios

For each scenario, cross-reference with the relevant story's WWB record:

1. **Replace generic references with concrete paths:**
   - "Login page" → "Login page (`src/pages/login.tsx`)" if WWB lists that file
   - "Authentication endpoint" → "`POST /api/auth/login`" if WWB mentions it

2. **Add implementation context to Expected Results:**
   - "Session is created" → "Session is created (stored in Redis with 7-day TTL)" if WWB documents that decision

3. **Add a `**Implementation Reference:**` line** after the scenario when WWB provides useful context:
   ```markdown
   **Implementation Reference:** Story 1 — Files: `commands/create-spec.md` (Step 2.4), `agents/user-story-generator.md`
   ```

**Enhancement rules:**
- WWB details are **additive** — they enrich scenarios, never replace the human-readable steps
- If a story has no WWB record, scenarios are generated without enhancement (no degradation)
- Keep implementation references brief — file paths and key decisions only, not full WWB content
- Implementation references are for tester context ("where to look if this fails"), not for test execution

---

### Phase 5: Assemble & Write UAT Plan

#### Step 5.1: Assemble Document

Build the complete `uat-plan.md`:

```markdown
# UAT Plan: [Spec Name]

> **Generated:** YYYY-MM-DD
> **Spec:** `.writ/specs/{spec-folder}/`
> **Stories Covered:** N of M completed
> **Total Scenarios:** X

## How to Use This Plan

1. Work through scenarios in order (they're grouped by story, ordered by priority)
2. For each scenario, follow the steps exactly as written
3. Mark Pass or Fail — add notes for any unexpected behavior
4. Scenarios marked Fail should be filed as issues or fed back to the spec
5. A feature passes UAT when all scenarios pass (or failures are accepted as known limitations)

## Coverage Summary

| Story | Status | Scenarios | Source Breakdown |
|-------|--------|-----------|-----------------|
| Story 1: [title] | ✅ Covered | N | AC: X, Errors: Y, Shadow: Z, Edge: W |
| Story 2: [title] | ⏳ Pending | — | Not yet complete |
| Story 3: [title] | ✅ Covered | N | AC: X, Errors: Y, Shadow: Z, Edge: W |

---

## Story 1: [Title]

[Scenarios for Story 1]

---

## Story N: [Title]

[Scenarios for Story N]

---

## Pending Stories

The following stories are not yet complete. Scenarios will be added when they complete:

- **Story 2:** [title] — Status: [In Progress | Not Started]
- **Story 5:** [title] — Status: [Not Started]
```

#### Step 5.2: Write File

Write to `.writ/specs/{spec-folder}/uat-plan.md`.

If a `uat-plan.md` already exists, **overwrite** it — UAT plans are regenerated, not appended. The file header includes the generation date for traceability.

#### Step 5.3: Report

```
✅ UAT plan generated.

📄 File: .writ/specs/{spec-folder}/uat-plan.md
📊 Scenarios: X total (Y stories covered, Z pending)
   - From acceptance criteria: A
   - From error maps: B
   - From shadow paths: C
   - From edge cases: D
   - From experience design: E

💡 Next: Execute the plan manually. Mark each scenario Pass/Fail.
   When all pass, the feature is human-validated.
```

**`--check` mode:** Show the report but do not write the file. Useful for previewing before generation.

---

## Error Handling

**Spec folder not found:**
```
❌ Spec folder not found: .writ/specs/{spec-folder}/
   Check available specs with: ls .writ/specs/
```

**No spec.md in folder:**
```
❌ No spec.md found in .writ/specs/{spec-folder}/
   This doesn't appear to be a valid spec folder.
```

**No technical spec (error maps/shadow paths unavailable):**
```
⚠️ No technical-spec.md found — error map, shadow path, and edge case scenarios
   will not be generated. UAT plan will be based on acceptance criteria only.
```
Continue with acceptance criteria scenarios. The plan is still useful — just less comprehensive.

**Story file parse error:**
```
⚠️ Could not parse story file: story-N-{slug}.md
   Skipping this story. Check file format.
```
Continue with other stories. Log the skip in the plan's notes section.

**"What Was Built" record missing on completed story:**
```
ℹ️ Story N has no "What Was Built" record — scenarios generated without
   implementation references.
```
Not an error — Phase 4 enhancement is best-effort. Scenarios are still valid.

---

## Integration with Writ

| Command | Relationship |
|---------|-------------|
| `/create-spec` | Creates the spec package that `/create-uat-plan` reads |
| `/implement-story` | Completes stories and generates "What Was Built" records that enrich UAT scenarios |
| `/implement-spec` | Orchestrates all stories — run `/create-uat-plan` after stories complete |
| `/verify-spec` | Validates spec metadata integrity; `/create-uat-plan` validates feature behavior |
| `/ship` | Phase 3b consideration: UAT sign-off as optional gate before PR creation |

**Recommended flow:** `/implement-spec` (all stories) → `/create-uat-plan` → manual UAT execution → `/ship`

**Standalone usage:** `/create-uat-plan` works independently of the pipeline. Run it anytime after at least one story is complete — partial plans are valid and useful for incremental validation.

## Completion

This command succeeds when:

1. **UAT plan file created** — `uat-plan.md` exists in `.writ/specs/{spec-folder}/` with scenario count, coverage summary, and story groupings
2. **Scenarios generated** — structured scenarios exist for all completed stories, sourced from acceptance criteria, error maps, shadow paths, edge cases, and experience design
3. **Coverage reported** — the user received a completion report with scenario counts broken down by source type
4. **"What Was Built" enhancement applied** — scenarios for stories with WWB records include concrete file paths and implementation references

**Suggested next step:** Execute the UAT plan manually or with test tooling.

**Terminal constraint:** This command produces a UAT plan (`.writ/specs/{spec-folder}/uat-plan.md`). Do not offer to implement, build, or execute what was planned. For manual or automated execution, the user should follow the plan's instructions. For quick prototyping, use `/prototype`.

---

## References

- Standing instructions: [`commands/_preamble.md`](_preamble.md)
- Identity & Prime Directive: [`system-instructions.md`](../system-instructions.md)
