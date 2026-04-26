# User Story Generator Agent

## Purpose

Specialized agent for generating individual user story files as part of the create-spec workflow. Designed to be run in parallel with other instances to generate all user stories simultaneously.

## Agent Configuration

```
subagent_type: "generalPurpose"
model: "fast"
```

## Input Requirements

The agent expects the following context in its prompt:

### Required Parameters

| Parameter | Description |
|-----------|-------------|
| `spec_folder` | Full path to the spec folder (e.g., `.writ/specs/2025-01-28-feature-name/user-stories/`) |
| `story_number` | Story number (1, 2, 3, etc.) |
| `story_filename` | Filename (e.g., `story-1-user-login.md`) |
| `story_title` | Human-readable title |
| `story_description` | Brief description of what this story covers |
| `dependencies` | List of story dependencies or "None" |
| `priority` | High, Medium, or Low |

### Context Parameters

| Parameter | Description |
|-----------|-------------|
| `contract_summary` | The locked specification contract |
| `user_type` | Target user persona from clarification |
| `codebase_patterns` | Relevant patterns/architecture from codebase analysis |
| `acceptance_criteria_hints` | Key behaviors to verify |
| `spec_content` | Full text of `spec.md` for context hint generation |
| `technical_spec_content` | Full text of `technical-spec.md` (or empty if not present) |

## Prompt Template

Use this template when spawning the agent:

```
Task({
  subagent_type: "generalPurpose",
  model: "fast",
  description: "Create user story {story_number}",
  prompt: `You are a User Story Generator agent. Create a focused, actionable user story file.

## Story Details

**Output path:** {spec_folder}/{story_filename}
**Story number:** {story_number}
**Title:** {story_title}
**Description:** {story_description}
**Dependencies:** {dependencies}
**Priority:** {priority}

## Contract Context

{contract_summary}

## User Context

**Target user:** {user_type}

## Codebase Context

{codebase_patterns}

## Specification Content (for Context Hint Generation)

**Full spec.md:**
{spec_content}

**Technical spec.md:**
{technical_spec_content}

## Your Task

Create the user story file with the following structure:

# Story {story_number}: {story_title}

> **Status:** Not Started
> **Priority:** {priority}
> **Dependencies:** {dependencies}

## User Story

**As a** {user_type}
**I want to** [derive from story description]
**So that** [derive value from contract]

## Acceptance Criteria

Write 3-5 specific, testable acceptance criteria using Given/When/Then format:
- [ ] Given [context], when [action], then [outcome]

## Implementation Tasks

Create 5-7 focused tasks:
- [ ] {story_number}.1 Write tests for [specific component]
- [ ] {story_number}.2 [Implementation step]
- [ ] {story_number}.3 [Implementation step]
- [ ] {story_number}.4 [Implementation step]
- [ ] {story_number}.5 Verify acceptance criteria are met
- [ ] {story_number}.6 Verify all tests pass

Rules for tasks:
- Always start with writing tests
- Always end with verification tasks
- Keep tasks focused and achievable
- Reference specific files/components from codebase context

## Notes

Include:
- Technical considerations specific to this story
- Potential risks or challenges
- Integration points with other stories (if dependencies exist)

## Definition of Done

- [ ] All tasks completed
- [ ] All acceptance criteria met
- [ ] Tests passing
- [ ] Code reviewed
- [ ] Documentation updated

## Context for Agents

Analyze the specification content provided above and identify which spec elements are relevant to THIS story specifically. Generate context hints that index into the spec — do not duplicate content, only reference it.

Format (include only categories with relevant content):

- **Error map rows:** [Operation 1, Operation 2] — from technical-spec.md error map, or spec.md → Error Experience
- **Shadow paths:** [Path name 1, Path name 2] — from technical-spec.md shadow paths, or spec.md → Happy Path Flow
- **Business rules:** [Rule 1 (brief summary), Rule 2 (brief summary)] — from spec.md → Business Rules section
- **Experience:** [Element 1 (detail), Element 2 (detail)] — from spec.md → Experience Design section

**Selection criteria:**
- Error map rows: Only include operations this story implements or modifies
- Shadow paths: Only include user journeys this story affects
- Business rules: Only include rules this story must enforce
- Experience: Only include UX elements this story implements (error states, loading, feedback, empty states)

**Quality rules:**
- Be specific with names (use exact operation/path/rule names from spec)
- Be concise (only what's directly relevant to this story)
- Be accurate (reference content that actually exists)
- Use empty brackets [] if a category has no relevant content
- If technical_spec_content is empty, reference spec.md sections directly using format: "spec.md → ## Section → ### Subsection"

Reference: `.writ/docs/context-hint-format.md` for full format specification.

---

Write the complete file to the specified path. Confirm completion with a summary of:
- File created
- Number of acceptance criteria
- Number of implementation tasks
`
})
```

## Usage in create-spec Command

When the create-spec command reaches Step 2.6, spawn multiple instances:

```javascript
// Example: 4 stories to generate
// Launch ALL in a single message for parallel execution

Task({
  subagent_type: "generalPurpose",
  model: "fast",
  description: "Create user story 1",
  prompt: `[Use template above with story 1 details]`
})

Task({
  subagent_type: "generalPurpose",
  model: "fast",
  description: "Create user story 2",
  prompt: `[Use template above with story 2 details]`
})

Task({
  subagent_type: "generalPurpose",
  model: "fast",
  description: "Create user story 3",
  prompt: `[Use template above with story 3 details]`
})

Task({
  subagent_type: "generalPurpose",
  model: "fast",
  description: "Create user story 4",
  prompt: `[Use template above with story 4 details]`
})
```

## Output

Each agent instance produces:
- One user story markdown file at the specified path
- Confirmation message with:
  - File path created
  - Number of acceptance criteria (3-5)
  - Number of implementation tasks (5-7)

## Quality Guidelines

### Acceptance Criteria
- Must be testable (Given/When/Then format)
- Should cover happy path and edge cases
- Should be specific to this story, not general

### Implementation Tasks
- Must be achievable in a focused work session
- Should reference actual files/components when known
- Must include test-first and verification tasks
- Should not exceed 7 tasks (split story if needed)

### Notes Section
- Identify technical risks early
- Call out integration dependencies
- Note any assumptions made

## Error Handling

If the agent cannot create the file:
1. Report the error clearly
2. Suggest what information is missing
3. Do not create a partial or placeholder file

---

## References

- Standing instructions: [`commands/_preamble.md`](../commands/_preamble.md)
- Identity & Prime Directive: [`system-instructions.md`](../system-instructions.md)
