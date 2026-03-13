# Prototype Command (prototype)

## Overview

Lightweight execution for small-to-medium code changes that don't warrant a full spec. Describe the change, ship code with TDD and lint verification — no spec files, no multi-gate ceremony, no pre-flight questions.

Use `/prototype` when the cost of creating a specification exceeds the value of the change itself. For anything that touches core architecture, requires cross-team coordination, or spans many files, use `/create-spec` + `/implement-story` instead.

**How it differs from `--quick` mode on `/implement-story`:**

| | `/prototype` | `/implement-story --quick` |
|---|---|---|
| **Spec required?** | No — operates without any spec | Yes — requires an existing story file |
| **Input** | Description (inline, attached file, or conversation context) | Story file with tasks and acceptance criteria |
| **Pipeline** | Scan → [Visual Preview] → Code → Lint → Done | Code → Lint → Test (skips arch-check, review, docs) |
| **Best for** | Ad-hoc changes, bug fixes, small features | Prototyping a specific story within a larger spec |

## Invocation

| Invocation | Behavior |
|---|---|
| `/prototype` | Uses the conversation context — attached files, preceding messages, or user's description |
| `/prototype "description"` | Explicit inline description |
| `/prototype @issue-file.md` | Reads the attached issue/file as the change description |

All invocations go straight to Context Scan — no interactive questions. The description, constraints, and scope are extracted from whatever the user provides. If the input is ambiguous or insufficient, the agent asks a single clarifying question in natural language rather than presenting a menu.

## Pipeline

```
┌───────────────┐   ┌───────────────┐   ┌───────────────┐   ┌───────────────┐   ┌───────────────┐
│  CONTEXT      │──▶│  VISUAL       │──▶│  CODING       │──▶│  LINT &       │──▶│  SUMMARY      │
│  SCAN         │   │  PREVIEW      │   │  AGENT        │   │  TYPECHECK    │   │  + ESCALATION │
│ (auto)        │   │  (UI only)    │   │  (TDD)        │   │  (auto)       │   │  (if needed)  │
└───────────────┘   └───────────────┘   └───────────────┘   └───────────────┘   └───────────────┘
                           │                   │
                     skip if no UI        complexity detected?
                                               ▼
                                        ESCALATE → suggest /create-spec
```

## Command Process

### Step 1: Extract Intent

Parse the change description from the user's input. The description can come from:

1. **Inline text** — `/prototype "fix pagination off-by-one"`
2. **Attached file** — `/prototype @issue-file.md` (read the file for description, relevant files, constraints)
3. **Conversation context** — `/prototype` with preceding messages describing the change
4. **Bare invocation** — `/prototype` with no context → ask one natural-language question: "What do you want to build or change?"

Extract from the input:
- **What** — the change to make
- **Where** — any files or areas mentioned (hints for the context scan, not constraints)
- **Watch-outs** — any constraints, compatibility requirements, or design notes the user mentioned

If the user provided an issue file, it likely contains all three. If they gave a one-liner, the context scan discovers the rest.

### Step 2: Context Scan

Gather lightweight context from the codebase before coding:

1. **Scan the target area** — read relevant files mentioned in the description or issue, plus their surrounding module
2. **Detect tech stack** — identify language, framework, test runner, linter configuration
3. **Find related patterns** — look for similar implementations in the codebase to guide the approach
4. **Check for test conventions** — identify test file locations and naming patterns
5. **Discover scope** — determine which files need modification (the agent figures this out, not the user)
6. **Sniff nearby rules** — scan files in the target area for permission checks, validation logic, state machines, or business rules the change must respect. Include any discovered rules in the context passed to the coding agent.
7. **Detect UI surface** — determine whether this change touches user-facing UI (see below)

**UI detection heuristic** — classify the change as UI-touching if ANY of:
- Files to modify match frontend patterns: `*.tsx`, `*.jsx`, `*.vue`, `*.svelte`, `*.html`
- Target area includes: `components/`, `pages/`, `app/`, `views/`, `layouts/`, `screens/`
- Description contains visual language: "button", "modal", "layout", "form", "page", "dashboard", "sidebar", "card", "table", "nav", "header", "footer", "responsive", "style", "CSS", "UI", "design"

If UI-touching → set `ui_change: true` in context. This triggers the Visual Preview step.

**Figma MCP detection** — if the `cursor-ide-browser` MCP is available AND a `design-system.md` or Figma MCP server is configured, note this in the context. Design tokens will be passed to the coding agent so it generates token-referenced code (`text-primary`) instead of hardcoded values (`text-gray-900`).

Output a brief context summary (not shown to user — passed to coding agent):

```
Context:
- Tech: TypeScript, Next.js, Jest, ESLint + Prettier
- Target area: src/components/settings/
- Related patterns: existing toggle components use `useLocalStorage` hook
- Test location: __tests__/components/settings/
- Files to modify: [list]
- Nearby rules: [e.g., "requireAuth middleware on this route", "max 10 items enforced in useCart hook", or "none found"]
- UI change: true
- Design tokens: .writ/docs/design-system.md (loaded)
```

### Step 2.5: Visual Preview (UI Changes Only)

**Skip this step entirely if `ui_change: false`.** For API-only, backend, utility, or non-visual changes, go directly to Step 3.

When a change touches user-facing UI, generate a quick visual preview *before* writing production code. This lets the user see the intended direction and course-correct early — a 30-second preview that saves 10-15 minutes of rework.

**How it works:**

1. **Generate a canvas-based HTML mockup** using the `cursor-ide-browser` canvas tool. The canvas should be a live, interactive HTML page that approximates the intended UI change — layout, key components, interaction states. Use the project's CSS framework (Tailwind, CSS Modules, etc.) and any design tokens found in Step 2.

2. **Keep it low-fidelity but structurally accurate.** The goal is layout, hierarchy, and flow — not pixel-perfect polish. Use placeholder content, approximate colors, and real component names as labels. Think wireframe-in-code, not production UI.

3. **Present the canvas to the user** with a brief description of what they're seeing:

```
🎨 Visual Preview

Here's a quick mockup of the [change description]:
[Canvas opens in browser — live HTML preview]

Key decisions shown:
- [Layout choice, e.g., "sidebar nav with collapsible sections"]
- [Component structure, e.g., "card grid with 3 columns on desktop, stacks on mobile"]
- [Interaction pattern, e.g., "modal triggered by the settings icon"]

Does this match what you had in mind? I can adjust the layout,
component structure, or interaction pattern before I write the
production code.
```

4. **Wait for user response:**
   - **Approval** (explicit or implicit — e.g., "looks good", "yes", "go ahead") → proceed to Step 3 with the visual as a reference
   - **Adjustment** (e.g., "make it a dropdown instead of a modal", "use tabs not cards") → regenerate the canvas with the feedback, then re-present
   - **Skip** (e.g., "just build it", "skip the preview") → proceed to Step 3 without visual reference

**Canvas guidelines:**
- Use the project's actual component library names and CSS framework in the mockup
- Reference design tokens from `design-system.md` if available
- Include responsive behavior if the description mentions mobile or the project uses responsive patterns
- Show multiple states if relevant (empty, loading, error, populated)
- Keep it to a single focused screen — don't mock the entire app

**What the canvas is NOT:**
- Not a design deliverable — it's a conversation starter
- Not production code — the coding agent builds the real implementation
- Not required — if the change is small enough that the user would rather just see the code, they can skip it

### Step 3: Spawn Coding Agent

> **Agent:** `agents/coding-agent.md` (prototype mode)

Spawn the coding agent with the extracted intent and codebase context. The agent follows TDD — tests first, then implementation. If a visual preview was approved in Step 2.5, include it as a reference.

```
Task({
  subagent_type: "generalPurpose",
  description: "Prototype: [brief description]",
  prompt: `You are the Coding Agent running in **prototype mode** — a lightweight pipeline for small-to-medium changes.

## Change Description

{change_description}

## Watch-outs

{constraints_if_any, or "None specified — use your judgment."}

## Codebase Context

{context_scan_output}

## Approved Visual Reference

{If visual preview was approved: "A canvas mockup was approved by the user. The HTML source is at {canvas_file_path}. Read it for layout structure, component hierarchy, and design decisions. Match the approved layout and interaction patterns in your implementation."

If no visual preview: "No visual preview was generated for this change."}

## Design Tokens

{If design-system.md exists: "Reference these design tokens in your implementation. Use token names (e.g., `text-primary`, `rounded-lg`, `shadow-sm`) instead of hardcoded values."

If Figma MCP is available: "Figma MCP is configured. Query it for component specs and design tokens when implementing UI components."

Otherwise: "No design system found — use your judgment for styling, matching existing codebase patterns."}

## Instructions

1. **Write tests first** (TDD) — cover the core behavior and obvious edge cases
2. **Implement the change** — match existing codebase patterns and conventions
3. **If a visual reference was approved**, match its layout structure and component hierarchy — the user already signed off on the direction
4. **Respect nearby rules** — if the context scan found permission checks, validation, or state logic in the target area, honor them. Don't bypass auth, skip validation, or ignore state transitions just because this is a prototype.
5. **Don't ship only the happy path** — if this touches UI, handle what the user sees on error, on empty, and on success. If it touches data, handle invalid input. A prototype that crashes on edge cases isn't lightweight — it's broken.
6. **Keep it focused** — this is a prototype, not a full feature build
7. **Document only if non-obvious** — skip docs for straightforward changes

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

### Experience Gaps
[NONE | List any user-facing states not handled — e.g., "no empty state for the list", "no error feedback on failed save", "no loading indicator during fetch". Flag these honestly rather than shipping silently.]

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
**Visual preview:** ✅ approved (or "skipped — no UI changes")

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

**Insufficient context:** If the user's input doesn't give enough to act on, ask a single natural-language clarifying question. Don't present menus — just ask what you need to know.

## When to Use /prototype vs Other Commands

| Scenario | Use |
|---|---|
| Quick bug fix | `/prototype "fix off-by-one in pagination"` |
| Add a utility function | `/prototype "add string truncation helper"` |
| Small UI tweak | `/prototype "add loading spinner to save button"` |
| Bug with issue file | `/prototype @issue-file.md` |
| Multi-file feature with dependencies | `/create-spec` + `/implement-story` |
| Refactoring a specific file | `/refactor` |
| Exploring an approach before committing | `/prototype` (then escalate if it works out) |
| Change within an existing spec | `/implement-story --quick` |
