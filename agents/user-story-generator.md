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
