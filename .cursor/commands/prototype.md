# Prototype Command (prototype)

## Overview

Lightweight execution for small-to-medium code changes that don't warrant a full spec. Describe the change, answer 2-3 fast questions, ship code with TDD and lint verification — no spec files, no multi-gate ceremony.

Use `/prototype` when the cost of creating a specification exceeds the value of the change itself. For anything that touches core architecture, requires cross-team coordination, or spans many files, use `/create-spec` + `/implement-story` instead.

**How it differs from `--quick` mode on `/implement-story`:**

| | `/prototype` | `/implement-story --quick` |
|---|---|---|
| **Spec required?** | No — operates without any spec | Yes — requires an existing story file |
| **Input** | Freeform description + 2-3 questions | Story file with tasks and acceptance criteria |
| **Pipeline** | Contract → Code → Lint → Done | Code → Lint → Test (skips arch-check, review, docs) |
| **Best for** | Ad-hoc changes, bug fixes, small features | Prototyping a specific story within a larger spec |

## Invocation

| Invocation | Behavior |
|---|---|
| `/prototype` | Interactive — asks what you want to build (full quick contract) |
| `/prototype "description"` | Pre-filled — skips the "what" question, asks only about scope and constraints |

## Pipeline

```
┌───────────────┐   ┌───────────────┐   ┌───────────────┐   ┌───────────────┐
│  QUICK        │──▶│  CODING       │──▶│  LINT &       │──▶│  SUMMARY      │
│  CONTRACT     │   │  AGENT        │   │  TYPECHECK    │   │  + ESCALATION │
│ (2-3 Q's)     │   │  (TDD)        │   │  (auto)       │   │  (if needed)  │
└───────────────┘   └───────────────┘   └───────────────┘   └───────────────┘
                           │
                           │ complexity detected?
                           ▼
                    ESCALATE → suggest /create-spec
```

## Command Process

### Step 1: Quick Contract

The quick contract establishes just enough shared understanding to code confidently. No spec files are created — the contract lives in conversation context only.

---

#### Path A: No Arguments (`/prototype`)

All three questions are asked:

```
AskQuestion({
  title: "Prototype — Quick Contract",
  questions: [
    {
      id: "change_description",
      prompt: "What do you want to build or change?",
      options: [
        { id: "describe", label: "I'll describe it (free text follow-up)" },
        { id: "bug_fix", label: "Fix a bug" },
        { id: "small_feature", label: "Add a small feature" },
        { id: "refactor", label: "Refactor / improve existing code" },
        { id: "utility", label: "Add a utility or helper" }
      ]
    },
    {
      id: "scope",
      prompt: "What area of the codebase does this touch?",
      options: [
        { id: "single_file", label: "Single file" },
        { id: "one_module", label: "One module / directory" },
        { id: "few_files", label: "A few related files (2-4)" },
        { id: "cross_cutting", label: "Cross-cutting (multiple areas)" },
        { id: "unsure", label: "Not sure — let the agent figure it out" }
      ]
    },
    {
      id: "constraints",
      prompt: "Any constraints or things to watch out for?",
      options: [
        { id: "none", label: "No constraints — just make it work" },
        { id: "backwards_compat", label: "Must be backwards-compatible" },
        { id: "perf_sensitive", label: "Performance-sensitive area" },
        { id: "shared_code", label: "Touches shared/imported code" },
        { id: "other", label: "Other (I'll explain)" }
      ]
    }
  ]
})
```

**Follow-ups:**
- If `change_description` is "describe" → ask free-text: "Describe what you want to build in a sentence or two."
- If `constraints` is "other" → ask free-text: "What constraints should the agent be aware of?"

---

#### Path B: With Description (`/prototype "add dark mode toggle to settings"`)

The description is captured from the argument. Skip the first question and ask only scope and constraints:

```
AskQuestion({
  title: "Prototype — Quick Contract",
  questions: [
    {
      id: "scope",
      prompt: "What area of the codebase does this touch?",
      options: [
        { id: "single_file", label: "Single file" },
        { id: "one_module", label: "One module / directory" },
        { id: "few_files", label: "A few related files (2-4)" },
        { id: "cross_cutting", label: "Cross-cutting (multiple areas)" },
        { id: "unsure", label: "Not sure — let the agent figure it out" }
      ]
    },
    {
      id: "constraints",
      prompt: "Any constraints or things to watch out for?",
      options: [
        { id: "none", label: "No constraints — just make it work" },
        { id: "backwards_compat", label: "Must be backwards-compatible" },
        { id: "perf_sensitive", label: "Performance-sensitive area" },
        { id: "shared_code", label: "Touches shared/imported code" },
        { id: "other", label: "Other (I'll explain)" }
      ]
    }
  ]
})
```

---

### Step 2: Context Scan

Before spawning the coding agent, gather lightweight context:

1. **Scan the target area** — if the user specified a module or directory, read its structure and key files
2. **Detect tech stack** — identify language, framework, test runner, linter configuration
3. **Find related patterns** — look for similar implementations in the codebase to guide the agent
4. **Check for test conventions** — identify test file locations and patterns

Output a brief context summary (not shown to user — passed to coding agent):

```
Context:
- Tech: TypeScript, Next.js, Jest, ESLint + Prettier
- Target area: src/components/settings/
- Related patterns: existing toggle components use `useLocalStorage` hook
- Test location: __tests__/components/settings/
```

### Step 3: Spawn Coding Agent

> **Agent:** `agents/coding-agent.md` (prototype mode)

Spawn the coding agent with the prototype contract and codebase context. The agent follows TDD — tests first, then implementation.

```
Task({
  subagent_type: "generalPurpose",
  description: "Prototype: [brief description]",
  prompt: `You are the Coding Agent running in **prototype mode** — a lightweight pipeline for small-to-medium changes.

## Prototype Contract

**Change:** {change_description}
**Scope:** {scope}
**Constraints:** {constraints}

## Codebase Context

{context_scan_output}

## Instructions

1. **Write tests first** (TDD) — cover the core behavior and obvious edge cases
2. **Implement the change** — match existing codebase patterns and conventions
3. **Keep it focused** — this is a prototype, not a full feature build
4. **Document only if non-obvious** — skip docs for straightforward changes

## Scope Detection (IMPORTANT)

While implementing, monitor for signs this change has outgrown prototype scope. Flag in your output if ANY of the following are true:

- More than 5 files need creation or modification
- New database schema changes or migrations are required
- The change touches core architecture, shared utilities, or base classes
- Test coverage in the affected area is already low (<50%)
- The change depends on other incomplete or in-flight work
- New external dependencies need to be added

If any flags trigger, still complete the implementation but include a scope escalation notice in your output.

## Output Format

Return your results in this exact structure:

### Implementation Summary

[2-3 sentence description of what was built]

### Files Created
- \`path/to/file\` — description

### Files Modified
- \`path/to/file\` — what changed

### Tests Written
- \`path/to/test\` — test descriptions

### Scope Flags
[NONE | List any scope detection flags that triggered]

### Concerns
[Any risks, edge cases not covered, or follow-up work needed]
`
})
```

### Step 4: Lint & Typecheck

**Runs inline — no sub-agent needed.** Reuses the same pattern as Gate 2 in `/implement-story`.

Auto-detect and run project linters:
- **Node/TS:** `tsc --noEmit`, `eslint`, `prettier --check`
- **Python:** `mypy`, `ruff`, `black --check`
- **Rust:** `cargo check`, `cargo clippy`, `cargo fmt --check`

**On failure:**
1. Auto-fix what's fixable (`eslint --fix`, `prettier --write`, `black`, `cargo fmt`)
2. Re-run checks
3. If still failing → send errors back to coding agent for one fix attempt
4. If still failing after retry → report in summary with details

### Step 5: Output Summary

Present the final results to the user.

---

#### On Success (no scope flags):

```
✅ Prototype Complete

**Change:** [description]

**Files:**
- Created: [N] — [list]
- Modified: [N] — [list]

**Tests:** [N] passing
**Lint:** ✅ clean
**Typecheck:** ✅ clean

Ready to commit. Run `git add -A && git commit -m "feat: [description]"` or ask me to commit.
```

---

#### On Success with Scope Escalation:

```
✅ Prototype Complete

**Change:** [description]

**Files:**
- Created: [N] — [list]
- Modified: [N] — [list]

**Tests:** [N] passing
**Lint:** ✅ clean
**Typecheck:** ✅ clean

⚠️ Scope Escalation Recommended

This change grew beyond typical prototype scope:
- [specific flags that triggered, e.g., "8 files modified", "touches shared utility base class"]

The implementation is complete and working, but consider running `/create-spec` to formalize this as a tracked feature — especially if follow-up work is needed.

Ready to commit, or escalate with `/create-spec "[description]"`.
```

---

#### On Lint/Typecheck Failure (after retries):

```
⚠️ Prototype Complete (with issues)

**Change:** [description]

**Files:**
- Created: [N] — [list]
- Modified: [N] — [list]

**Tests:** [N] passing
**Lint:** ❌ [N] errors remaining
**Typecheck:** ❌ [N] errors remaining

Remaining issues:
{error_details}

Options:
1. Fix these manually and commit
2. Let me take another pass at fixing them
3. Discard and start over
```

---

## Error Handling

**Agent crash:** Retry once automatically. If retry fails, present error to user with partial progress summary.

**Implementation blocked:**
```
⚠️ Prototype blocked.

Blocker: {description}
Attempted: {what was tried}
Partial progress: {files created/modified so far}

Options:
1. Provide guidance and retry
2. Escalate to /create-spec for proper planning
3. Discard changes
```

**User cancels during contract:**
No files have been created or modified. Clean exit.

## When to Use /prototype vs Other Commands

| Scenario | Use |
|---|---|
| Quick bug fix | `/prototype "fix off-by-one in pagination"` |
| Add a utility function | `/prototype "add string truncation helper"` |
| Small UI tweak | `/prototype "add loading spinner to save button"` |
| Multi-file feature with dependencies | `/create-spec` + `/implement-story` |
| Refactoring a specific file | `/refactor` |
| Exploring an approach before committing | `/prototype` (then escalate if it works out) |
| Change within an existing spec | `/implement-story --quick` |
