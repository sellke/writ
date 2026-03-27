# Story 5: UAT Plan Generation

> **Status:** Not Started
> **Priority:** Medium
> **Dependencies:** Story 3

## User Story

**As a** developer who wants to manually validate a completed feature
**I want** a structured UAT plan generated from the spec
**So that** I can systematically verify the feature works without reading implementation code

## Acceptance Criteria

- [ ] Given a spec with completed stories, when `/create-uat-plan` runs, then it generates a `uat-plan.md` file with human-readable test scenarios
- [ ] Given acceptance criteria, error maps, shadow paths, and edge cases from the spec, when scenarios are generated, then they include preconditions, steps, expected result, and pass/fail checkbox
- [ ] Given a generated UAT plan, when a human executes it, then 90%+ of scenarios are executable without reading implementation code (clarity threshold)
- [ ] Given a spec where some stories are incomplete, when `/create-uat-plan` runs, then it generates scenarios only for completed stories and notes which are pending
- [ ] Given "What Was Built" records, when scenarios are generated, then they reference actual implementation details (e.g., "Login at `/auth/login` endpoint" not "Login at authentication page")

## Implementation Tasks

- [ ] 5.1 Write tests for UAT scenario generation (given acceptance criteria + error maps, generate scenarios with preconditions, steps, expected result)
- [ ] 5.2 Create `commands/create-uat-plan.md` with command structure (Overview, Invocation, Phases, Integration)
- [ ] 5.3 Implement Phase 1: Read spec folder and identify completed stories (check "Status: Completed" in story files)
- [ ] 5.4 Implement Phase 2: Extract acceptance criteria, error maps, shadow paths, edge cases from `spec.md` and `technical-spec.md`
- [ ] 5.5 Implement Phase 3: Generate scenarios from extracted content (standard template: preconditions, steps, expected result, checkbox)
- [ ] 5.6 Implement Phase 4: Enhance scenarios with "What Was Built" details (reference actual files, endpoints, components)
- [ ] 5.7 Implement Phase 5: Write `uat-plan.md` to spec folder root (`.writ/specs/{spec}/uat-plan.md`)
- [ ] 5.8 Test on dogfood (generate UAT plan for this Context Engine spec)
- [ ] 5.9 Verify all acceptance criteria are met and tests pass

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

- [ ] All tasks completed
- [ ] `/create-uat-plan` command created
- [ ] Scenario generation implemented (acceptance criteria, error maps, shadow paths, edge cases)
- [ ] "What Was Built" integration for concrete details
- [ ] Tests passing for scenario generation
- [ ] Dogfood validation: UAT plan generated for this spec
- [ ] Manual UAT execution on 2 features confirms 90%+ scenario clarity
- [ ] Code reviewed
- [ ] Documentation updated

## Context for Agents

- **Error map rows:** `UAT plan generation failure` — surface parse/extraction/write errors clearly; partial plans allowed when some stories incomplete (document pending)
- **Shadow paths:** Happy path: read completed stories → extract criteria/maps/paths → generate scenarios → write `uat-plan.md`
- **Business rules:** UAT plans generated after story completion, not during spec creation
- **Experience:** Entry: `/create-uat-plan` after stories complete; happy path: structured scenarios enable validation without code reading
