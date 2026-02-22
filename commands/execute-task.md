# Execute Task Command (execute-task)

> **⚠️ DEPRECATED:** This command is superseded by `/implement-story`, which provides the same TDD workflow plus automated review, testing, coverage enforcement, and documentation via sub-agents.
>
> **Migration:**
> - `/execute-task story-1` → `/implement-story story-1`
> - For quick TDD without review gates: `/implement-story story-1 --quick`
>
> This file is retained for reference. Use `/implement-story` for all new work.

## Overview

Execute a specific task and its sub-tasks systematically following a Test-Driven Development (TDD) workflow. This command reads task specifications from `.writ/specs/` directories and implements features with comprehensive testing, following established code standards and best practices.

## CRITICAL REQUIREMENT: 100% Test Pass Rate

**⚠️ ZERO TOLERANCE FOR FAILING TESTS ⚠️**

This command enforces strict test validation:
- **NO story can be marked "COMPLETED" with ANY failing tests**
- **100% test pass rate is MANDATORY before completion**
- **"Edge case" or "minor" test failures are NOT acceptable**
- **Implementation is considered incomplete until all tests pass**

If tests fail, the story remains "IN PROGRESS" until all failures are resolved.

## Command Process

### Step 1: Task Discovery & Selection

**Scan for available specifications:**

- Search `.writ/specs/` for dated specification folders
- Load user stories from `user-stories/` folders in each spec
- Read `user-stories/README.md` for story overview and progress
- Parse individual `story-N-{name}.md` files for available tasks
- Present available stories and tasks organized by specification

**Create execution todo tracking:**

Use `todo_write` to track the execution process:

```json
{
  "todos": [
    {
      "id": "task-discovery",
      "content": "Discover and select task from available specifications",
      "status": "in_progress"
    },
    {
      "id": "context-gathering",
      "content": "Gather context from spec documents and codebase analysis",
      "status": "pending"
    },
    {
      "id": "subtask-execution",
      "content": "Execute all subtasks in TDD order",
      "status": "pending"
    },
    {
      "id": "test-verification",
      "content": "Verify all task-specific tests pass",
      "status": "pending"
    },
    {
      "id": "task-completion",
      "content": "Update task status and mark complete",
      "status": "pending"
    }
  ]
}
```

**Story selection process:**

1. **If multiple specs exist**: Present selection menu with spec dates and story summaries
2. **If single spec exists**: Show available stories and their tasks within that specification
3. **If story/task specified**: Validate story exists and select specific task for execution
4. **If no specs exist**: Guide user to run `/create-spec` first

**Selection format:**
```
Available specifications:
├── 2024-01-15-user-auth/ (3 stories, 12 total tasks)
│   ├── Story 1: User Registration (5 tasks) - Not Started
│   ├── Story 2: User Login (4 tasks) - Not Started
│   └── Story 3: Password Reset (3 tasks) - Not Started
└── 2024-01-20-payment-system/ (2 stories, 8 total tasks)
    ├── Story 1: Payment Processing (5 tasks) - In Progress (2/5)
    └── Story 2: Refund Management (3 tasks) - Not Started
```

### Step 2: Context Gathering & Analysis

**Load specification context:**

- Read primary spec document: `spec.md`
- Load user stories overview: `user-stories/README.md`
- Read selected story file: `user-stories/story-N-{name}.md`
- Review technical specifications: `sub-specs/technical-spec.md`
- Parse task breakdown from individual story file

**Analyze current codebase:**

Use `codebase_search` to understand:

- Current architecture and patterns
- Related existing functionality
- Integration points for new features
- Testing frameworks and conventions

**Load project standards:**

- Code style guide: `.writ/docs/code-style.md`
- Technology stack: `.writ/docs/tech-stack.md`
- Best practices: `.writ/docs/best-practices.md`

### Step 3: Story & Task Analysis

**Parse selected story structure:**

- Load complete story file: `user-stories/story-N-{name}.md`
- Extract user story, acceptance criteria, and implementation tasks
- Analyze task dependencies and execution order within the story
- Understand test requirements (first task typically writes tests)
- Plan implementation approach based on story's task breakdown

### Step 3.5: Update README Status to In Progress (MANDATORY)

**⚠️ REQUIRED before beginning implementation:**

Before writing any code, update `user-stories/README.md` to reflect the story is now in progress:

1. **Update summary table:**
   - Change story status from "Not Started" to "In Progress"
   - This creates accountability and visibility into active work

2. **Example update:**
```markdown
| Story | Title | Status | Tasks | Progress |
|-------|-------|--------|-------|----------|
| 1 | User Authentication | In Progress 🔄 | 5 | 0/5 |
| 2 | Password Reset | Not Started | 4 | 0/4 |
```

3. **Update Quick Links section** (if present):
```markdown
- [Story 1: User Authentication](./story-1-user-auth.md) 🔄 In Progress
```

**Why this matters:** This prevents the README from becoming out of sync with actual work. If you start a story but don't update the README, the overview becomes misleading.

**Validate TDD approach within story:**

- **First task**: Should write tests for the story functionality
- **Middle tasks**: Implement functionality to pass tests (max 5-7 tasks total)
- **Final task**: Verify all tests pass and acceptance criteria are met
- **Integration considerations**: Update adjacent/related tests as needed

**Example story structure verification:**

```markdown
# Story 1: User Authentication

## User Story
**As a** new user
**I want to** register with email and password
**So that** I can access personalized features

## Acceptance Criteria
- [ ] User can register with valid email/password
- [ ] Email validation prevents invalid formats
- [ ] Password meets security requirements

## Implementation Tasks
- [ ] 1.1 Write tests for authentication middleware
- [ ] 1.2 Implement JWT token generation
- [ ] 1.3 Create password hashing utilities
- [ ] 1.4 Build login/logout endpoints
- [ ] 1.5 Verify all tests pass and acceptance criteria met
```

### Step 4: Pre-Implementation Preparation

**Create execution tracking:**

Update todos to reflect specific story tasks:

```json
{
  "todos": [
    {
      "id": "story-1-task-1",
      "content": "1.1 Write tests for authentication middleware (Story 1: User Authentication)",
      "status": "in_progress"
    },
    {
      "id": "story-1-task-2",
      "content": "1.2 Implement JWT token generation (Story 1: User Authentication)",
      "status": "pending"
    },
    {
      "id": "story-1-task-3",
      "content": "1.3 Create password hashing utilities (Story 1: User Authentication)",
      "status": "pending"
    },
    {
      "id": "story-1-task-4",
      "content": "1.4 Build login/logout endpoints (Story 1: User Authentication)",
      "status": "pending"
    },
    {
      "id": "story-1-task-5",
      "content": "1.5 Verify all tests pass and acceptance criteria met (Story 1: User Authentication)",
      "status": "pending"
    }
  ]
}
```

**Validate testing setup:**

- Confirm testing framework is configured
- Verify test directories and naming conventions
- Check existing test patterns and utilities
- Ensure test runner is functional

### Step 5: Story Task Execution (TDD Workflow)

**Execute story tasks in sequential order:**

#### Task 1: Write Tests (Test-First Approach)

**Actions:**

- Write comprehensive test cases for the entire feature
- Include unit tests, integration tests, and edge cases
- Cover happy path, error conditions, and boundary cases
- Ensure tests fail appropriately (red phase)

**Test categories to include:**

- **Unit tests**: Individual function/method testing
- **Integration tests**: Component interaction testing
- **Edge cases**: Boundary conditions and error scenarios
- **Acceptance tests**: User story validation

#### Tasks 2-N: Implementation (Green Phase)

**For each implementation task within the story:**

1. **Focus on specific functionality**: Implement only what's needed for current task
2. **Make tests pass**: Write minimal code to satisfy failing tests
3. **Update related tests**: Modify adjacent tests if behavior changes
4. **Maintain compatibility**: Ensure no regressions in existing functionality
5. **Refactor when green**: Improve code quality while tests remain passing

**Implementation approach:**

- Start with simplest implementation that passes tests
- Add complexity incrementally as required by test cases
- Keep tests passing at each step
- Refactor for clarity and maintainability

#### Final Task: Test & Acceptance Verification

**CRITICAL: 100% Test Pass Rate Required**

**Mandatory Actions (ALL must succeed before story completion):**

1. **Run complete test suite for this story**
2. **Achieve 100% pass rate for ALL tests** - NO EXCEPTIONS
3. **Verify no regressions in existing test suites**
4. **Validate all acceptance criteria are met for the user story**
5. **Confirm story delivers the specified user value**

**⚠️ STORY CANNOT BE MARKED COMPLETE WITH ANY FAILING TESTS ⚠️**

If ANY tests fail:
- **STOP IMMEDIATELY** - Do not mark story as complete
- Debug and fix each failing test
- Re-run test suite until 100% pass rate achieved
- Only then proceed to mark story as complete

### Step 6: Story-Specific Test Validation

**Run targeted test validation:**

Use available testing tools to verify:

- All tests written in first task are passing
- New functionality works as specified in user story
- All acceptance criteria are satisfied
- No regressions introduced to existing features
- Performance requirements are met (if specified)

**Test execution strategy:**

- **First**: Run only tests for current story/feature
- **Then**: Run related test suites to check for regressions
- **Finally**: Consider full test suite if significant changes made
- **Acceptance**: Validate user story acceptance criteria are met

**Failure handling:**

**ZERO TOLERANCE FOR FAILING TESTS:**
- **If ANY tests fail**: Story CANNOT be marked complete
- **Required action**: Debug and fix ALL failing tests before proceeding
- **No exceptions**: "Edge case" or "minor" failing tests are NOT acceptable
- **If performance issues**: Optimize implementation until all tests pass
- **If regressions found**: Fix regressions - story completion is blocked until resolved

**Failure Resolution Process:**
1. Identify root cause of each failing test
2. Fix implementation to make test pass
3. Re-run ALL tests to ensure 100% pass rate
4. Repeat until NO tests fail
5. Only then mark story as complete

### Step 7: Story Completion & Status Updates

**Update story file status:**

Mark completed tasks in the individual story file (`user-stories/story-N-{name}.md`):

```markdown
# Story 1: User Authentication

> **Status:** Completed ✅
> **Priority:** High
> **Dependencies:** None

## User Story
**As a** new user
**I want to** register with email and password
**So that** I can access personalized features

## Acceptance Criteria
- [x] User can register with valid email/password ✅
- [x] Email validation prevents invalid formats ✅
- [x] Password meets security requirements ✅

## Implementation Tasks
- [x] 1.1 Write tests for authentication middleware ✅
- [x] 1.2 Implement JWT token generation ✅
- [x] 1.3 Create password hashing utilities ✅
- [x] 1.4 Build login/logout endpoints ✅
- [x] 1.5 Verify all tests pass and acceptance criteria met ✅

## Definition of Done
- [x] All tasks completed ✅
- [x] All acceptance criteria met ✅
- [x] **ALL tests passing (100% pass rate)** ✅ **MANDATORY**
- [x] Code reviewed ✅
- [x] Documentation updated ✅

**NOTE:** Story CANNOT be marked complete without 100% test pass rate
```

### Step 7.1: Sync README Summary (MANDATORY)

**⚠️ REQUIRED immediately after updating story file:**

The README MUST be updated to reflect story completion. This is NOT optional.

**Update process:**

1. **Read all story files** in `user-stories/` to get current statuses
2. **Update summary table** in `user-stories/README.md`:

```markdown
| Story | Title | Status | Tasks | Progress |
|-------|-------|--------|-------|----------|
| 1 | User Authentication | Completed ✅ | 5 | 5/5 ✅ |
| 2 | Password Reset | Not Started | 4 | 0/4 |
| 3 | Profile Management | Not Started | 6 | 0/6 |

**Total Progress:** 5/15 tasks (33%)
```

3. **Update Quick Links section:**
```markdown
- [Story 1: User Authentication](./story-1-user-auth.md) ✅
- [Story 2: Password Reset](./story-2-password-reset.md)
```

4. **Update dependency/order section** to show completed stories

### Step 7.2: Check for Spec Completion & Build Verification

**If ALL stories in the specification are now complete:**

1. **Update spec status** in README header:
```markdown
> **Status:** ✅ Complete
```

2. **Run build verification:**
```bash
pnpm build
```

3. **If build succeeds:**
   - Add completion summary section to README
   - Update main `spec.md` status to Complete

4. **If build fails:**
   - Do NOT mark spec as complete
   - Document build failure in README
   - Investigate and fix before finalizing

**Build verification is MANDATORY when all stories complete.** This ensures the combined changes from all stories work together correctly.

**Document completion:**

- Update spec status if all stories in the specification are complete
- Note any deviations from original plan in story notes
- Document lessons learned or improvements made
- Identify any follow-up tasks or technical debt

**Present completion summary:**

**ONLY present if ALL tests pass (100% pass rate):**

```
Story completed successfully:

**Story:** Story 1: User Authentication
**Tasks completed:** 5/5 ✅
**Acceptance criteria met:** 3/3 ✅
**Tests written:** 12 test cases
**Tests passing:** 12/12 (100%) ✅ REQUIRED FOR COMPLETION
**Files modified:** 6 files
**User value delivered:** New users can register with email/password and access personalized features

Current specification progress: 5/15 tasks (33%)

Next available stories:
- Story 2: Password Reset (4 tasks) - Not Started
- Story 3: Profile Management (6 tasks) - Not Started

Would you like to proceed with the next story?
```

**If ANY tests fail, present this instead:**

```
Story implementation INCOMPLETE - Tests failing:

**Story:** Story 1: User Authentication
**Tasks completed:** 5/5 (implementation done, but validation failed)
**Tests written:** 12 test cases
**Tests passing:** 10/12 (83%) ❌ COMPLETION BLOCKED
**Failing tests:** 2 tests must be fixed before story completion
**Status:** IN PROGRESS - Cannot mark complete until 100% test pass rate

REQUIRED ACTIONS:
1. Debug and fix all failing tests
2. Re-run test suite to achieve 100% pass rate
3. Only then mark story as complete
```

## Tool Integration

**Primary Writ tools:**

- `todo_write` - Progress tracking throughout execution
- `codebase_search` - Understanding existing architecture and patterns
- `file_search` - Locating relevant specifications and test files
- `read_file` - Loading spec documents and existing code
- `search_replace` / `MultiEdit` - Implementing code changes
- `run_terminal_cmd` - Executing tests and build processes

**Parallel execution opportunities:**

- Context gathering (multiple spec files, codebase analysis)
- Test file analysis (existing patterns, framework configuration)
- Implementation validation (running tests, checking integration)

## Integration with Writ Ecosystem

**Specification dependency:**

- Requires existing spec created by `/create-spec`
- Uses story breakdown from `user-stories/` folder in spec directories
- Loads individual story files: `user-stories/story-N-{name}.md`
- Tracks progress in `user-stories/README.md`
- Follows technical approach from `sub-specs/technical-spec.md`

**Code style compliance:**

- Adheres to patterns in `.writ/docs/code-style.md`
- Uses technology stack from `.writ/docs/tech-stack.md`
- Follows best practices from `.writ/docs/best-practices.md`

**Cross-command integration:**

- Complements `/create-spec` for complete development workflow
- Can trigger `/research` if unknown technologies encountered
- Integrates with testing and validation workflows

## Quality Standards

**Test-Driven Development:**

- Tests written before implementation
- **100% test pass rate MANDATORY before task completion**
- **ZERO TOLERANCE for failing tests - no story completion with any failures**
- Comprehensive coverage including edge cases
- Regression testing for existing functionality
- Failed tests = incomplete implementation that must be fixed

**Code quality requirements:**

- Follows established project patterns and conventions
- Maintains backward compatibility unless specified otherwise
- Implements proper error handling and validation
- Includes appropriate logging and monitoring

**Documentation standards:**

- Code changes include appropriate comments
- Complex logic is documented inline
- API changes are reflected in technical specifications
- Task completion updates specification status

## Error Handling & Recovery

**Common failure scenarios:**

- **No specifications found**: Guide to `/create-spec`
- **Test framework issues**: Provide setup guidance
- **Implementation conflicts**: Suggest conflict resolution
- **Performance issues**: Recommend optimization approaches

**Blocking issue management:**

If blocked by technical issues:

```markdown
- [ ] N.X Task description ⚠️ Blocking issue: [DESCRIPTION]
```

Update story status and notes section to document the blocking issue.

**Resolution strategies:**

1. Try alternative implementation approach
2. Research solution using `/research`
3. Break down task into smaller components
4. Maximum 3 attempts before escalating or documenting as blocked

## Best Practices

**TDD adherence:**

- Always start with failing tests
- Implement minimal code to pass tests
- Refactor only when tests are green
- **MANDATORY: 100% test pass rate before story completion**
- **NO EXCEPTIONS: Failing tests = incomplete story**

**Incremental development:**

- Complete story tasks sequentially
- Verify functionality at each step
- Commit working code frequently
- Test integration points early
- Validate acceptance criteria incrementally

**Communication:**

- Update story file status immediately after task completion
- **MANDATORY: Update README.md progress tracking after story completion**
- **MANDATORY: Update README.md when starting a story (mark "In Progress")**
- Document any deviations from specification in story notes
- Note technical decisions and rationale in story file
- Highlight areas requiring future attention
- Ensure user value is clearly demonstrated upon story completion

**README Sync Requirements (Non-Negotiable):**

- README summary table MUST match individual story file statuses
- Update README when STARTING a story (In Progress)
- Update README when COMPLETING a story (Completed ✅)
- Run build verification when ALL stories are complete
- Never leave README out of sync with actual story states
