# ADR-001: AskQuestion vs Plan Mode in Commands

> **Date:** 2026-03-01
> **Status:** Accepted
> **Category:** Command Design

## Decision

Commands use **Plan Mode** for open-ended discovery and **AskQuestion** for bounded decisions. These are complementary tools, not interchangeable.

### The Principle

> **Use AskQuestion when you know the option space. Use Plan Mode when you need to discover it.**

| Signal | Tool |
|--------|------|
| Finite, enumerable choices | AskQuestion |
| "Pick one and go" decisions | AskQuestion |
| Confirmation gates (Lock / Edit / Abort) | AskQuestion |
| Open-ended design or strategy | Plan Mode |
| Ambiguity about *what* to build | Plan Mode |
| Trade-offs requiring collaborative discussion | Plan Mode |

The strongest pattern is **Plan Mode for discovery, AskQuestion for decisions** — they sequence naturally.

## Context

All 14 commands with user interaction used AskQuestion exclusively. This worked well for selection and confirmation, but forced open-ended conversations into multiple-choice boxes. When a user is shaping a feature idea, picking from pre-defined options is reductive — the real value is in the dialogue.

Plan Mode provides structural guarantees that align with contract-first commands:
- **Read-only enforcement** — can't accidentally create files during discovery
- **Conversational UX** — back-and-forth discussion, not transactional Q&A
- **Clear phase signal** — the mode switch itself communicates "we're planning, not building"

## Commands Affected

| Command | Change |
|---------|--------|
| `create-spec` | Plan Mode for discovery (Steps 1.2–1.3). AskQuestion kept for feature selection, contract decision, visual references. |
| `plan-product` | Plan Mode for product discovery. AskQuestion kept for initial product direction and contract confirmation. |
| `new-command` | Plan Mode for command shaping. AskQuestion kept for contract confirmation. |
| `system-instructions` | Added interaction tool selection guidance. |

Commands like `implement-spec`, `refactor`, `release`, and `migrate` are unaffected — their decisions are already bounded.

## Typical Flow

```
Agent Mode  →  context scan, initial selection (AskQuestion if needed)
     ↓
Plan Mode   →  discovery conversation, gap analysis, pushback, shaping
     ↓
Plan Mode   →  present contract, discuss, refine
     ↓
Agent Mode  →  user approves, final decisions (AskQuestion), file creation
```

## Consequences

**Positive:**
- Discovery phases feel natural instead of forced
- Read-only enforcement during planning prevents premature file creation
- Clear phase boundaries between planning and execution
- Open-ended questions get open-ended conversation

**Negative:**
- Mode switches add a small interaction cost (user must approve switch)
- Commands that span both modes are slightly more complex to author
- Not all platforms support Plan Mode (adapter consideration)

## Adapter Notes

- **Cursor:** Native `SwitchMode` tool with `target_mode_id: "plan"`
- **Claude Code:** `permissionMode: plan` for read-only subagents (closest equivalent)
- **OpenClaw / other adapters:** May need to simulate with conversational free-text
