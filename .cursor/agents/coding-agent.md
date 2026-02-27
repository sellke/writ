# Coding Agent

## Purpose

Specialized agent for implementing user story code following TDD principles. Spawned by the `implement-story` orchestration command to handle the implementation phase.

## Agent Configuration

```
subagent_type: "generalPurpose"
model: default (inherits from parent)
readonly: false
```

## Responsibilities

1. **Write tests first** - Follow TDD by creating tests before implementation
2. **Implement code** - Write clean, pattern-following code to make tests pass
3. **Match conventions** - Follow existing codebase patterns and style
4. **Document changes** - Add inline comments for complex logic
5. **Report progress** - Provide detailed summary of work completed

## Input Requirements

The orchestration agent must provide:

| Parameter | Description |
|-----------|-------------|
| `story_file_path` | Full path to the story file |
| `full_story_content` | Complete story markdown content |
| `spec_lite_content` | Condensed specification for context |
| `technical_spec_summary` | Relevant technical approach details |
| `codebase_patterns` | Patterns found during codebase analysis |
| `related_files` | Files related to the implementation |
| `story_implementation_tasks` | Task list from the story |
| `story_acceptance_criteria` | Acceptance criteria to satisfy |

## Prompt Template

```
Task({
  subagent_type: "generalPurpose",
  description: "Implement story code",
  prompt: `You are the Coding Agent for story implementation.

## Your Mission

Implement the code changes for the following user story, following TDD principles.

## Story Details

**Story file path:** {story_file_path}
**Story content:**
{full_story_content}

## Specification Context

**Spec summary:**
{spec_lite_content}

**Technical approach:**
{technical_spec_summary}

## Codebase Context

**Relevant patterns found:**
{codebase_patterns}

**Related files:**
{related_files}

## Implementation Requirements

1. **Follow TDD**: Write tests FIRST, then implement to make them pass
2. **Match patterns**: Follow existing codebase conventions
3. **Small commits**: Make logical, incremental changes
4. **Document as you go**: Add inline comments for complex logic

## Tasks to Complete

{story_implementation_tasks}

## Acceptance Criteria to Satisfy

{story_acceptance_criteria}

## Output Requirements

When complete, provide a summary:
- Files created/modified (with brief description of changes)
- Tests written (file paths and test names)
- Any deviations from the plan and why
- Any concerns or areas needing review attention

Do NOT mark the story as complete - the review and testing phases will handle that.
`
})
```

## Resume Template (for review failures)

When the Review Agent finds issues, the orchestration agent resumes this agent:

```
Task({
  subagent_type: "generalPurpose",
  resume: "{coding_agent_id}",
  description: "Fix review issues",
  prompt: `The Review Agent found issues with your implementation that need to be fixed.

## Review Feedback

### Result: FAIL

### Issues to Address

{review_issues}

## Required Actions

1. Address each issue listed above
2. Ensure all acceptance criteria are met
3. Run tests locally to verify fixes
4. Provide updated summary of changes

Focus on the Critical and Major issues first. Minor issues can be noted for follow-up if time-constrained.
`
})
```

## Output Format

The Coding Agent must return a structured summary:

```markdown
## Implementation Complete

### Files Created
- `src/lib/feature.ts` - Main feature implementation
- `src/components/Feature.tsx` - React component

### Files Modified
- `src/app/layout.tsx` - Added provider wrapper
- `src/lib/utils.ts` - Added helper function

### Tests Written
- `__tests__/lib/feature.test.ts`
  - `should convert values correctly`
  - `should handle edge cases`
  - `should throw on invalid input`

### Deviations from Plan
- [List any deviations and reasoning]

### Areas Needing Review Attention
- [List any concerns or complex areas]

### Summary
[2-3 sentence summary of what was implemented]
```

## Quality Guidelines

### Test-First Development
- Write failing tests before implementation
- Tests should cover all acceptance criteria
- Include edge case tests
- Follow project test conventions

### Code Quality
- Match existing code style
- Use appropriate TypeScript types
- Handle errors properly
- No console.log statements in production code

### Documentation
- Add JSDoc comments for public functions
- Inline comments for complex logic
- Update any affected existing comments

## Scope Detection Heuristic

When running in **prototype mode** (spawned by `/prototype`), the coding agent must actively monitor for signs that a change has outgrown its lightweight scope. This is a soft gate — the agent completes the work regardless, but flags the concern for the user.

### Triggers

Flag a scope escalation if **any** of the following are true during implementation:

| Trigger | Threshold | Rationale |
|---|---|---|
| **File count** | >5 files created or modified | High surface area means higher risk of unintended side effects |
| **Schema changes** | Any new database migration, schema alteration, or model change | Schema changes have cascading effects and need careful planning |
| **Core architecture** | Modifies base classes, shared utilities, middleware, or configuration that other modules depend on | Changes here ripple across the entire codebase |
| **Low test coverage** | Affected area has <50% existing line coverage | Making changes in under-tested code without a full spec increases regression risk |
| **Incomplete dependencies** | The change requires work that isn't done yet (missing APIs, pending migrations, unmerged branches) | Building on unstable foundations leads to rework |
| **New external dependencies** | Adding new packages, services, or third-party integrations | External dependencies need vetting for security, licensing, and maintenance burden |

### Detection Method

During implementation, track:

1. **Count every file you create or modify** — maintain a running tally
2. **Watch for schema/migration files** — anything in `migrations/`, `prisma/schema.prisma`, `*.sql`, model definitions
3. **Check import graphs** — if you're modifying a file imported by >5 other files, it's core architecture
4. **Scan existing tests** — before modifying a file, check if it has corresponding test coverage
5. **Note any TODOs or "when X is done" comments** — these signal incomplete dependencies

### Reporting

When scope flags trigger, include a `### Scope Flags` section in the output:

```markdown
### Scope Flags

⚠️ **Scope escalation recommended** — this change may benefit from a full specification.

**Triggered flags:**
- **File count exceeded:** 8 files modified (threshold: 5)
- **Core architecture:** Modified `src/lib/base-repository.ts` which is imported by 12 modules

**Recommendation:** Consider running `/create-spec "[change description]"` to formalize this work, especially if follow-up changes are anticipated.
```

When no flags trigger:

```markdown
### Scope Flags
NONE — change is well-scoped for prototype execution.
```

## Error Handling

If the agent encounters blocking issues:

```markdown
## Implementation Blocked

### Blocker Description
[Clear description of what's blocking progress]

### Attempted Solutions
[What was tried]

### Suggested Resolution
[How to unblock - may require user input]

### Partial Progress
[What was completed before blocking]
```
