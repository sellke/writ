# OpenClaw Platform Adapter

Maps Cursor-specific tool calls to OpenClaw equivalents for running Writ commands via OpenClaw agents.

## Quick Reference

| Cursor Tool | OpenClaw Equivalent | Notes |
|---|---|---|
| `Task({ prompt })` | `sessions_spawn({ task: prompt })` | Auto-announces completion |
| `Task({ resume: id })` | `subagents({ action: "steer", target, message })` | Steers existing sub-agent |
| `AskQuestion({ questions })` | `message({ action: "send", buttons })` | Telegram inline buttons |
| `codebase_search` | `exec({ command: "rg 'pattern' src/" })` | ripgrep preferred |
| `file_search` | `exec({ command: "fd 'pattern'" })` | or `find` fallback |
| `todo_write` | `Write({ path: ".writ/state/tracking.json" })` | File-based tracking |
| `read_file` | `Read({ path })` | Direct equivalent |
| `run_terminal_cmd` | `exec({ command })` | Direct equivalent |
| `list_dir` | `exec({ command: "ls -la path/" })` | Direct equivalent |
| `readonly: true` | Add constraint to task prompt | "Do NOT modify any files" |

---

## Detailed Mappings

### 1. Spawning Sub-Agents (`Task` → `sessions_spawn`)

**Cursor:**
```
Task({
  subagent_type: "generalPurpose",
  model: "fast",
  description: "Create user story 1",
  prompt: "You are a User Story Generator agent..."
})
```

**OpenClaw:**
```
sessions_spawn({
  task: "You are a User Story Generator agent...",
  label: "cc-story-1"
})
```

**Parallel spawning** — launch multiple in one turn:
```
sessions_spawn({ task: "Create story 1...", label: "cc-story-1" })
sessions_spawn({ task: "Create story 2...", label: "cc-story-2" })
sessions_spawn({ task: "Create story 3...", label: "cc-story-3" })
sessions_spawn({ task: "Create story 4...", label: "cc-story-4" })
```

All run concurrently. Each auto-announces completion back to the requester chat.

**Key differences:**
- No `subagent_type` — all OpenClaw sub-agents are general purpose
- No `model: "fast"` — use `model` param if you want a specific model override
- `label` is optional but recommended for identification
- Completion is push-based — no polling needed

### 2. Resuming / Steering Agents (`resume` → `subagents steer`)

**Cursor:**
```
Task({
  subagent_type: "generalPurpose",
  resume: "{coding_agent_id}",
  prompt: "The Review Agent found issues..."
})
```

**OpenClaw:**
```
subagents({
  action: "steer",
  target: "cc-coding-agent",    // label from spawn
  message: "The Review Agent found issues..."
})
```

**Alternative — kill and respawn with context:**
```
subagents({ action: "kill", target: "cc-coding-agent" })
sessions_spawn({
  task: "PREVIOUS CONTEXT: [coding agent output]\n\nREVIEW FEEDBACK: [review issues]\n\nFix the issues above...",
  label: "cc-coding-agent-v2"
})
```

**When to use which:**
- `steer` — agent is still running, send new instructions mid-flight
- `kill + respawn` — agent finished, need a fresh run with accumulated context (more reliable for the review loop)

### 3. Structured Questions (`AskQuestion` → `message` with buttons)

**Cursor:**
```
AskQuestion({
  title: "Feature Clarification - Round 1",
  questions: [
    {
      id: "user_type",
      prompt: "Who is the primary user?",
      options: [
        { id: "end_user", label: "End users/customers" },
        { id: "admin", label: "Administrators" },
        { id: "developer", label: "Developers" }
      ]
    }
  ]
})
```

**OpenClaw (Telegram with inline buttons):**
```
message({
  action: "send",
  message: "**Feature Clarification - Round 1**\n\nWho is the primary user of this feature?",
  buttons: [
    [
      { "text": "End users/customers", "callback_data": "user_type:end_user" },
      { "text": "Administrators", "callback_data": "user_type:admin" }
    ],
    [
      { "text": "Developers", "callback_data": "user_type:developer" }
    ]
  ]
})
```

**Multi-question rounds** — since Telegram buttons support one action per press, batch questions as sequential messages or combine into a single formatted message with numbered options:

```
message({
  action: "send",
  message: "**Round 1 — Core Understanding**\n\n1️⃣ **Primary user?**\n2️⃣ **Integration approach?**\n3️⃣ **Implementation priority?**\n\nReply with your choices (e.g., '1: End users, 2: Extends existing, 3: MVP')",
})
```

**Fallback for non-button channels:**
```
Just present numbered options as text:
1. End users/customers
2. Administrators
3. Developers

Reply with the number.
```

### 4. Code Search (`codebase_search` → `exec` with ripgrep)

**Cursor:**
```
codebase_search("authentication pattern")
```

**OpenClaw:**
```
exec({ command: "rg -l 'auth' src/ --type ts" })           // find files
exec({ command: "rg -n 'authenticate|authorize' src/" })     // find lines
exec({ command: "rg -C 3 'export.*Auth' src/" })             // with context
```

**For broader searches:**
```
exec({ command: "rg -l 'pattern' --type ts --type tsx" })    // by file type
exec({ command: "rg 'pattern' -g '!node_modules' -g '!dist'" })  // exclude dirs
```

### 5. File Search (`file_search` → `exec` with fd)

**Cursor:**
```
file_search("AuthService")
```

**OpenClaw:**
```
exec({ command: "fd AuthService" })                          // filename match
exec({ command: "fd -e ts -e tsx auth" })                    // by extension
exec({ command: "find . -name '*auth*' -not -path '*/node_modules/*'" })  // fallback
```

### 6. Progress Tracking (`todo_write` → file-based JSON)

**Cursor:**
```
todo_write({
  todos: [
    { id: "context-gathering", content: "Gather context", status: "completed" },
    { id: "coding-phase", content: "Launch coding agent", status: "in_progress" },
    { id: "review-phase", content: "Launch review agent", status: "pending" }
  ]
})
```

**OpenClaw:**
```
Write({
  path: ".writ/state/implement-story-2026-02-22.json",
  content: JSON.stringify({
    story: "story-1-feature-name",
    startedAt: "2026-02-22T17:40:00Z",
    phases: {
      "context-gathering": { status: "completed", completedAt: "..." },
      "coding-phase": { status: "in_progress", agentLabel: "cc-coding-agent" },
      "review-phase": { status: "pending" },
      "testing-phase": { status: "pending" },
      "documentation-phase": { status: "pending" }
    }
  }, null, 2)
})
```

**Update progress** — use `Edit` to patch specific fields, or `Write` to overwrite the whole state file.

### 7. Read-Only Agents

**Cursor:**
```
Task({
  subagent_type: "generalPurpose",
  readonly: true,
  prompt: "Review the implementation..."
})
```

**OpenClaw:**
```
sessions_spawn({
  task: "Review the implementation...\n\n⚠️ CONSTRAINT: You are in READ-ONLY mode. Do NOT create, modify, or delete any files. Use only Read and exec (for grep/find) tools. Your job is analysis and reporting only.",
  label: "cc-review-agent"
})
```

---

## Workflow Patterns

### implement-story Full Flow

```
// Phase 1: Context gathering (orchestrator does this directly)
Read({ path: "user-stories/story-1-feature.md" })
Read({ path: "spec-lite.md" })
exec({ command: "rg -l 'relevant_pattern' src/" })

// Phase 2: Spawn coding agent
sessions_spawn({
  task: "[Full coding agent prompt with all context]",
  label: "cc-coding-agent"
})
// Wait for auto-announce completion, capture output

// Phase 3: Spawn review agent (read-only)
sessions_spawn({
  task: "[Review prompt with coding agent output]\n\n⚠️ READ-ONLY MODE...",
  label: "cc-review-agent"
})
// Parse REVIEW_RESULT from output

// If FAIL: respawn coding agent with feedback
sessions_spawn({
  task: "[Original context + review feedback]",
  label: "cc-coding-agent-v2"
})

// If PASS: spawn testing agent
sessions_spawn({
  task: "[Testing prompt with files to test]",
  label: "cc-testing-agent"
})

// Phase 5: Spawn documentation agent
sessions_spawn({
  task: "[Documentation prompt with implementation summary]",
  label: "cc-docs-agent"
})

// Phase 6: Update story status
Edit({ path: "user-stories/story-1-feature.md", ... })
```

### Review Feedback Loop

```
max_iterations = 3
iteration = 0

while iteration < max_iterations:
  // Spawn review agent
  review_result = spawn review agent, wait for completion
  
  if PASS:
    break → continue to testing
  
  if FAIL:
    iteration++
    // Respawn coding agent with accumulated feedback
    spawn coding agent with: original context + all review feedback so far
    wait for completion

if iteration >= max_iterations:
  // Escalate to user
  message({ action: "send", message: "⚠️ Review loop exceeded 3 iterations..." })
```

### State Persistence

For long-running implement-story workflows, persist state after each phase:

```json
// .writ/state/implement-story-2026-02-22T174000.json
{
  "story": "story-1-feature-name",
  "spec": "2026-02-22-feature-name",
  "startedAt": "2026-02-22T17:40:00Z",
  "currentPhase": "review",
  "iteration": 1,
  "phases": {
    "coding": {
      "status": "completed",
      "agentLabel": "cc-coding-agent",
      "output": "Files created: ...",
      "filesModified": ["src/lib/feature.ts", "src/components/Feature.tsx"],
      "testsWritten": ["__tests__/lib/feature.test.ts"]
    },
    "review": {
      "status": "in_progress",
      "agentLabel": "cc-review-agent",
      "iteration": 1
    },
    "testing": { "status": "pending" },
    "documentation": { "status": "pending" }
  }
}
```

This enables recovery if the orchestrator session is interrupted.

---

## Gotchas

1. **Sub-agent output capture**: `sessions_spawn` auto-announces completion. The orchestrator receives the result as a system message. Parse the output from there.

2. **No direct return values**: Unlike Cursor's `Task()` which returns output inline, OpenClaw sub-agents deliver results asynchronously. Design your orchestration to handle this.

3. **Button limitations**: Telegram inline buttons have a 64-byte callback_data limit. Keep IDs short. For complex multi-question forms, use sequential messages.

4. **Parallel spawn limit**: OpenClaw doesn't enforce a hard limit on concurrent sub-agents, but be mindful of API costs. 4 parallel story generators is fine; 20 might get expensive.

5. **File conflicts**: When multiple sub-agents write files in the same workspace, ensure they write to different paths. The user-story-generator pattern (each agent writes its own `story-N-*.md`) is safe.

6. **Model for sub-agents**: Pass `model` param to `sessions_spawn` if you want a cheaper/faster model for boilerplate tasks (story generation). Omit for default (inherits from config).
