# Explain Code Command (explain-code)

## Overview

On-demand code explanation. Reads a function, class, file, or code region and produces a clear, structured explanation in the conversation. Adapts depth and format to the target — simple code gets a concise summary, complex code gets detailed breakdowns with diagrams where they genuinely aid understanding.

**Scope boundary:** This command explains existing code. It does not modify code, generate tests, or propose changes. If the user needs improvements, direct them to `/refactor`. If they need to understand a broader system, use `/research`.

## Modes

| Invocation | Mode | Behavior |
|---|---|---|
| `/explain-code src/auth.ts` | File | Explain the full file — purpose, exports, key logic |
| `/explain-code handlePayment` | Symbol | Explain a specific function, class, or method |
| `/explain-code src/utils.ts:45-78` | Region | Explain a specific line range |
| `/explain-code` | Interactive | Ask what to explain, then proceed |

## Command Process

### Step 1: Identify Target

If a target is provided in the invocation, locate it and proceed to Step 2.

If no target, ask the user what they want explained. Accept a file path, function/class name, or line range. If the name is ambiguous (multiple matches), present the options and let the user choose.

### Step 2: Read and Analyze

Read the target code and its immediate context:

- **The code itself** — full source of the target
- **Direct dependencies** — what the target imports or calls
- **Callers** — who uses this code (scan for references)
- **Types** — relevant type definitions, interfaces, or schemas

Do not read the entire codebase. Read only what is needed to explain the target accurately.

### Step 3: Explain

Produce a structured explanation adapted to the target. Every explanation includes these sections, but their depth scales with complexity:

**Purpose** — What this code does, in one or two sentences. Lead with this.

**How It Works** — Step-by-step walkthrough of the logic. For simple functions, a paragraph suffices. For complex flows, use a numbered breakdown. Cover:
- Input handling and validation
- Core logic and decision points
- Error handling and edge cases
- Return values and side effects

**Context** — Where this code fits in the system:
- What calls it and when
- What it depends on
- Design patterns in use (name them only if they're genuinely present)

**Diagrams** — Include a Mermaid diagram only when it adds clarity that prose cannot:
- Flowcharts for multi-branch decision logic
- Sequence diagrams for multi-service or multi-step call chains
- Class diagrams for inheritance hierarchies with 3+ classes

Do not generate diagrams for simple functions, CRUD operations, or linear flows. A diagram that restates what the prose already says adds noise, not clarity.

**Complexity Notes** (only if relevant) — Time/space complexity, performance characteristics, or known gotchas. Skip this section for straightforward code.

### Step 4: Deliver

Print the explanation to the conversation. Do not auto-save to any file.

If the explanation is substantial and the user might want to reference it later, offer to save it to a location of their choice. Do not assume a default directory.

---

## Output Guidelines

**Adapt to the audience.** Match the technical level of the codebase. A React component explanation uses React terminology; a systems-level function explanation uses systems terminology. Do not over-explain language fundamentals unless the user asks.

**Be honest about uncertainty.** If the code's intent is unclear, say so. If a pattern looks unusual and you're not sure why it was chosen, flag it rather than inventing a rationale.

**Stay concise.** A 10-line utility function needs a 3-sentence explanation, not a page. Scale output to match input complexity.

## Completion

This command succeeds when a structured explanation (Purpose, How It Works, Context) has been delivered to the conversation. The explanation should be proportional to the target's complexity — a simple utility gets a concise summary, a complex flow gets a detailed breakdown with diagrams.

If the target cannot be located (file missing, symbol not found, ambiguous name with no user resolution), report the failure clearly rather than explaining something the user didn't ask about.

---

## Integration with Writ

| Command | Relationship |
|---------|-------------|
| `/research` | For broader system-level understanding beyond a single target |
| `/refactor` | When explanation reveals code that should be restructured |
| `/create-spec` | Understanding existing code before specifying changes |
| `/implement-story` | Reference during implementation to understand existing patterns |
| `/create-adr` | When explanation uncovers architectural decisions worth documenting |

---

## References

- Standing instructions: [`commands/_preamble.md`](_preamble.md)
- Identity & Prime Directive: [`system-instructions.md`](../system-instructions.md)
