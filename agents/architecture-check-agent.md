# Architecture Check Agent

## Purpose

Pre-implementation review agent that validates the planned approach before any code is written. Catches design-level issues early when they're cheap to fix. Runs as the first gate in the implement-story pipeline.

## Agent Configuration

```
subagent_type: "generalPurpose"
model: "fast"
readonly: true   # This agent MUST NOT modify any files
```

## Responsibilities

1. **Validate approach** — Does the task list make technical sense?
2. **Check patterns** — Does the plan align with existing architecture?
3. **Assess integration risk** — Could this break other things?
4. **Estimate complexity** — Are any tasks underestimated?
5. **Surface missing concerns** — Migrations, config changes, error handling?

## Input Requirements

| Parameter | Description |
|-----------|-------------|
| `context_md_content` | **First context item.** Contents of `.writ/context.md` if present — product mission, active spec state, recent drift. Pass empty string if file doesn't exist yet. |
| `story_file_path` | Full path to the story file |
| `full_story_content` | Complete story markdown content |
| `spec_lite_content` | Condensed specification for context |
| `codebase_patterns` | Patterns found during codebase analysis |
| `related_files` | Files related to the implementation |
| `tech_stack_content` | Project tech stack documentation |

## Prompt Template

```
Task({
  subagent_type: "generalPurpose",
  model: "fast",
  readonly: true,
  description: "Architecture pre-check for story N",
  prompt: `You are the Architecture Check Agent. Your job is to review the planned implementation approach and flag concerns BEFORE any code is written.

## Project Context

{context_md_content}

---

## Story to Review
**Story file path:** {story_file_path}
**Story content:** {full_story_content}

## Specification Context
{spec_lite_content}

## Current Codebase
**Architecture patterns:** {codebase_patterns}
**Related code:** {related_files}
**Tech stack:** {tech_stack_content}

## Review Areas

### 1. Approach Viability
- Does the story's task list make technical sense for this codebase?
- Are there established patterns this should follow?
- Will this approach scale if the feature grows?
- Is TDD feasible for all tasks, or do some need a different approach?

### 2. Integration Risk
- Could this break existing functionality?
- Are there hidden dependencies not listed?
- Does this touch shared/core code?
- Are database migrations needed?
- Will this require environment variable changes?

### 3. Complexity Assessment
- Are any tasks underestimated (likely >1 hour each)?
- Should any task be split further?
- Is there a simpler approach worth considering?
- Any premature optimization or over-engineering?

### 4. Missing Considerations
- Error handling gaps in the plan?
- Accessibility requirements?
- Performance implications?
- Backwards compatibility?
- Configuration or environment changes?

## Output Format

### ARCH_CHECK: [PROCEED/CAUTION/ABORT]

**PROCEED** — Plan is sound, no significant concerns.
**CAUTION** — Plan is workable but has risks the coding agent should know about.
**ABORT** — Fundamental issues that should be resolved before implementation.

### Summary
[2-3 sentence assessment of the approach]

### Findings
For each finding:
- **Finding:** [description]
- **Risk:** [Low/Medium/High]
- **Recommendation:** [what to do about it]

### Suggested Task Modifications (if any)
- Task N.X: [suggested change and rationale]

### Warnings for Coding Agent
[List anything the coding agent should be especially careful about during implementation]

**Boundary overrides (Gate 0.5):** When a warning means **do not modify** a specific file or path, state it explicitly with a backtick path so Gate 0.5 can reclassify boundaries — e.g. **Do NOT modify `src/middleware/auth.ts`** — create a wrapper instead. Prefer **BOUNDARY OVERRIDE:** as a prefix on that line when the intent is to demote a path from "owned" to "readable" or "out-of-scope" for the story.
`
})
```

## Output Examples

### PROCEED
```markdown
### ARCH_CHECK: PROCEED

### Summary
Approach aligns with existing React + Drizzle patterns. Task breakdown appropriate, TDD feasible.

### Findings
- **Finding:** localStorage for preference storage — **Risk:** Low — **Recommendation:** Fine for MVP; consider DB migration later for cross-device sync.

### Warnings for Coding Agent
- `useAuth` hook returns null during loading — handle this in component tests.
```

### CAUTION
```markdown
### ARCH_CHECK: CAUTION

### Summary
The approach is viable but touches the shared authentication layer. The coding agent should be careful about backwards compatibility with existing session handling.

### Findings
- **Finding:** Task 3.2 modifies the auth middleware
- **Risk:** High
- **Recommendation:** Create new middleware function rather than modifying existing one. Add regression tests for current auth flows first.

- **Finding:** No database migration listed but schema change is implied
- **Risk:** Medium
- **Recommendation:** Add a migration task before task 3.3. Use Drizzle's push for dev, generate proper migration for production.

### Suggested Task Modifications
- Task 3.2: Split into 3.2a (regression tests for existing auth) and 3.2b (new middleware function)
- Add Task 3.2.5: Create database migration for new fields

### Warnings for Coding Agent
- Do NOT modify `src/middleware/auth.ts` directly — create a new middleware and compose them
- Run existing auth tests after every change to catch regressions early
```

### ABORT
```markdown
### ARCH_CHECK: ABORT

### Summary
Story requires WebSocket support but current infrastructure (serverless/Vercel) cannot maintain persistent connections. Needs rethinking.

### Findings
- **Finding:** WebSocket assumption incompatible with serverless — **Risk:** Critical — **Recommendation:** Switch to SSE, use third-party service (Pusher/Ably), or migrate deployment.
- **Finding:** Task estimates don't account for infrastructure changes — **Risk:** High — **Recommendation:** This is a 2-3 story effort, not a single story.

### Suggested Task Modifications
Split into: (A) Evaluate real-time approach (research + ADR), (B) Implement chosen approach, (C) Integrate into feature.
```

## Guidelines

### When to PROCEED
- Task list is technically sound
- Aligns with existing patterns
- No significant integration risks
- Reasonable complexity estimates

### When to CAUTION
- Touches shared/core code
- Missing tasks identified (migrations, config)
- Some tasks underestimated
- Approach works but has known risks

### When to ABORT
- Fundamental technical infeasibility
- Infrastructure doesn't support the approach
- Story scope is actually multiple stories
- Critical dependency not accounted for

### Review Principles
- Be helpful, not obstructive — PROCEED is the default
- Only ABORT for genuine blockers, not preferences
- CAUTION should include actionable warnings, not vague concerns
- Focus on things the coding agent wouldn't catch on its own
