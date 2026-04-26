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
| `/prototype` | Uses conversation context — attached files, preceding messages, or user's description |
| `/prototype "description"` | Explicit inline description |
| `/prototype @issue-file.md` | Reads the attached issue/file as the change description |

All invocations go straight to Context Scan — no interactive questions. If the input is ambiguous, ask a single clarifying question in natural language rather than presenting a menu.

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

**Error recovery** (apply at any pipeline step):
- **Agent crash** → retry once automatically; if retry fails, surface partial progress to user
- **Blocked** → present the blocker, what was attempted, and options: provide guidance, escalate to `/create-spec`, or discard
- **Insufficient context** → ask one natural-language clarifying question (never a menu)

## Command Process

### Step 1: Extract Intent

Parse the change description from the user's input:

1. **Inline text** — `/prototype "fix pagination off-by-one"`
2. **Attached file** — `/prototype @issue-file.md` (read for description, files, constraints)
3. **Conversation context** — `/prototype` with preceding messages
4. **Bare invocation** — no context → ask: "What do you want to build or change?"

Extract: **what** to change, **where** (file hints for context scan), and **watch-outs** (constraints, compatibility, design notes). Issue files typically contain all three; one-liners rely on the context scan to discover the rest.

### Step 2: Context Scan

Gather lightweight context before coding:

1. **Read the target area** — files from the description plus their surrounding module
2. **Detect tech stack** — language, framework, test runner, linter config
3. **Find related patterns** — similar implementations to guide the approach
4. **Check test conventions** — test file locations and naming patterns
5. **Discover scope** — which files need modification
6. **Sniff nearby rules** — scan for permission checks, validation logic, state machines, or business rules the change must respect. Pass discovered rules to the coding agent.
7. **Detect UI surface** — classify as UI-touching (triggers Visual Preview)

**UI detection heuristic** — UI-touching if ANY of:
- Files match frontend patterns: `*.tsx`, `*.jsx`, `*.vue`, `*.svelte`, `*.html`
- Target area includes: `components/`, `pages/`, `app/`, `views/`, `layouts/`, `screens/`
- Description contains visual language: "button", "modal", "layout", "form", "page", "dashboard", "sidebar", "card", "table", "nav", "header", "footer", "responsive", "style", "CSS", "UI", "design"

**Figma MCP detection** — if `cursor-ide-browser` MCP and `design-system.md` or Figma MCP server are available, note in context so the coding agent generates token-referenced code instead of hardcoded values.

Output a brief context summary (internal — passed to coding agent, not shown to user):

```
Context:
- Tech: TypeScript, Next.js, Jest, ESLint + Prettier
- Target area: src/components/settings/
- Related patterns: existing toggle components use `useLocalStorage` hook
- Test location: __tests__/components/settings/
- Files to modify: [list]
- Nearby rules: [e.g., "requireAuth middleware on this route", or "none found"]
- UI change: true
- Design tokens: .writ/docs/design-system.md (loaded)
```

### Step 2.5: Visual Preview (UI Changes Only)

**Skip entirely if no UI change.** For backend, utility, or non-visual changes, go directly to Step 3.

When a change touches user-facing UI, generate a quick visual preview *before* production code. A 30-second preview that saves 10-15 minutes of rework.

**How it works:**

1. **Generate a canvas-based HTML mockup** using `cursor-ide-browser` canvas tool — live, interactive, approximating the intended UI. Use the project's CSS framework and design tokens from Step 2.
2. **Keep low-fidelity but structurally accurate.** Layout, hierarchy, flow — not pixel-perfect polish. Placeholder content, approximate colors, real component names as labels. Wireframe-in-code.
3. **Present to the user** with a brief description and key design decisions:

```
🎨 Visual Preview — [change description]
[Canvas opens — live HTML preview]

Key decisions: [layout choice] · [component structure] · [interaction pattern]
Adjust the layout or interaction pattern before I write production code?
```

4. **Wait for response:** approval → proceed with visual as reference; adjustment → regenerate canvas; skip ("just build it") → proceed without reference.

**Canvas guidelines:**
- Use the project's actual component library names and CSS framework
- Reference design tokens from `design-system.md` if available
- Include responsive behavior if relevant to the project
- Show multiple states if relevant (empty, loading, error, populated)
- Keep to a single focused screen

**What the canvas is NOT:**
- Not a design deliverable — it's a conversation starter
- Not production code — the coding agent builds the real implementation
- Not required — user can skip if they'd rather just see code

### Step 3: Spawn Coding Agent

> **Agent:** `agents/coding-agent.md` (prototype mode)

Spawn the coding agent with extracted intent and codebase context.

**Required context to include in prompt:**
- Change description and watch-outs
- Full context scan output (tech stack, patterns, nearby rules, files to modify)
- Visual reference path if preview was approved (instruct agent to match its layout)
- Design tokens reference if available

**Principles to instruct:**

1. **TDD** — tests first covering core behavior and obvious edge cases
2. **Match codebase** — follow existing patterns and conventions
3. **Respect nearby rules** — don't bypass auth, skip validation, or ignore state transitions. Prototype ≠ permission to cut corners on correctness.
4. **Don't ship only the happy path** — handle error, empty, and loading states. A prototype that crashes on edge cases isn't lightweight — it's broken.
5. **Keep focused** — prototype scope, not full feature build
6. **Match visual reference** — if a preview was approved, match its layout and component hierarchy

**Scope escalation signals** — instruct the agent to flag if ANY are true:

- More than 5 files need creation or modification
- New database schema changes or migrations are required
- The change touches core architecture, shared utilities, or base classes
- Test coverage in the affected area is already low (<50%)
- The change depends on other incomplete or in-flight work
- New external dependencies need to be added

If flags trigger, complete the implementation but include a scope escalation notice.

### Step 4: Lint & Typecheck

Auto-detect and run project linters and typecheckers. The AI infers tool selection from the project's config files.

**On failure:** auto-fix what's fixable (formatter, auto-fixable lint rules) → re-run → still failing → send to coding agent for one fix attempt → still failing → report remaining issues in summary.

### Step 5: Output Summary

**On success:**

```
✅ Prototype Complete — [description]
Files: [created/modified list] · Tests: [N] passing · Lint: ✅ · Typecheck: ✅
Visual preview: [approved / skipped — no UI changes]
Ready to commit.
```

**On scope escalation:** Same as above, plus a ⚠️ block listing the specific flags that triggered, followed by an active escalation offer — not just a note. Present the following:

```
⚠️ Scope Escalation Detected

This implementation grew beyond prototype scope. Signals triggered:
  • [list each signal that fired: >5 files modified, schema change, core architecture, external dependency, etc.]

The implementation is complete and in your working tree. Want to formalize it?

Running /create-spec --from-prototype will:
  • Create a spec using the current diff as context for files-in-scope and approach
  • Mark the prototype work as Story 1 (already complete — it's already built)
  • Start discovery focused on Story 2+ (what comes next)
```

```
AskQuestion({
  title: "Formalize as Spec?",
  questions: [{
    id: "escalation_path",
    prompt: "What would you like to do with this prototype?",
    options: [
      { id: "formalize", label: "Yes — run /create-spec --from-prototype now" },
      { id: "later", label: "Not now — I'll formalize it manually later" },
      { id: "leave", label: "Leave as-is — this stays a prototype" }
    ]
  }]
})
```

If the user selects **"Yes — run /create-spec --from-prototype now"**, immediately invoke the `--from-prototype` flow from `create-spec.md` (no need to re-invoke as a separate command — continue inline).

**On lint/typecheck failure after retries:**

```
⚠️ Prototype Complete (with issues) — [N] errors remaining
[error details]
Options: fix manually · retry · discard
```

---

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

---

## References

- Standing instructions: [`commands/_preamble.md`](_preamble.md)
- Identity & Prime Directive: [`system-instructions.md`](../system-instructions.md)
