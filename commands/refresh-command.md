# Refresh Command (refresh-command)

## Overview

The learning loop. After running a Writ command, `/refresh-command` turns your experience into concrete improvements. You describe what worked and what didn't — the agent reads the command file, proposes diffs, and applies approved changes. Commands get better through use.

This is **local-first**: amendments are applied to the project's command copy. Core commands in `commands/` stay untouched unless you manually promote changes.

## Invocation

| Invocation | Behavior |
|---|---|
| `/refresh-command` | Interactive — select command from list |
| `/refresh-command create-spec` | Refresh a specific command |
| `/refresh-command refresh-command` | Bootstrap — refresh-command improves itself |

---

## Phase 1: Select Command

**If a command name was provided as an argument:**
1. Resolve to `commands/{name}.md`
2. Verify the file exists — if not, list available commands and ask the user to pick

**If no argument provided:**
1. Check conversation context — if a command was recently run, suggest it: *"You just ran /create-spec. Refresh that one?"*
2. If no recent command or user declines, list all files in `commands/` and ask the user to pick

**Output:** The resolved command name and file path.

---

## Phase 2: Gather Context

Read the full command file.

Then ask the user — use your platform's question tool with freeform input:

> **How did `/[command]` go?**
> What worked well? What was confusing, slow, or unnecessary? What would you change?
>
> (If you just ran the command in this conversation, I can also infer from what happened above.)

**Two input paths:**

1. **User describes friction directly** — use their description as the primary signal
2. **User says "infer from the conversation"** (or similar) — scan the conversation history for the most recent `/[command]` run and extract:
   - Steps that required user correction or retry
   - Questions the user had to clarify or override
   - Steps that produced unexpected output
   - Steps that went smoothly (preserve these)

Summarize the gathered signals before proceeding:

```
Signals from your /[command] run:
- [friction point 1]
- [friction point 2]
- [positive: thing that worked well]
```

Ask: *"Does this capture it? Anything to add or correct?"*

---

## Phase 3: Propose Amendments

Analyze the command file against the gathered signals. For each actionable signal, generate a concrete amendment proposal.

**For each proposal, provide:**

1. **Title** — short description of the change
2. **Rationale** — why this improves the command, tied to the specific friction
3. **Confidence** — High / Medium / Low
4. **Diff** — the exact text change (old → new), with enough surrounding context to locate it

**Format:**

```
### Amendment 1: [Title]
**Rationale:** [Why — linked to specific friction signal]
**Confidence:** [High/Medium/Low]

**Diff:**
  Lines before for context...
- Old text to remove
+ New text to add
  Lines after for context...
```

**Guidelines:**
- Limit to 1–5 proposals. If you have more, prioritize by confidence and impact.
- Each diff must be surgical — change only what's needed, preserve surrounding structure
- Don't propose changes for things that worked well
- If a signal points to a problem but the fix isn't clear, say so rather than proposing a low-confidence guess

**Present proposals and ask:**

> Apply all / Pick which ones / Skip all?

If the user picks, present each proposal individually for yes/no.

---

## Phase 4: Apply & Log

### Step 4.1: Apply Changes

For each approved amendment, apply the diff to the command file. After applying all changes, show a summary:

```
Applied [N] of [M] proposed amendments to commands/[command].md
```

### Step 4.2: Write Refresh Log

Append an entry to `.writ/refresh-log.md` (create if it doesn't exist):

```markdown
## [DATE] — /[command] refreshed

**Source:** Conversation context
**Signals found:** [N] total, [M] actionable
**Amendments applied:** [X] of [Y] proposed

**Changes:**
- [Amendment title] (Confidence: [H/M/L], applied/skipped)
- [Amendment title] (Confidence: [H/M/L], applied/skipped)

**Not applied:**
- [Amendment title] — [reason: user declined / low confidence / unclear fix]

**Scope:** Local only
**Target file:** commands/[command].md
```

### Step 4.3: Final Output

```
✅ /[command] refreshed — [X] amendments applied

Changes:
  ✅ [Amendment 1 title]
  ✅ [Amendment 2 title]
  ⏭️ [Skipped amendment title]

Changelog: .writ/refresh-log.md updated

💡 Run /[command] again and /refresh-command afterward
   to continue the improvement loop.
```

If no amendments were proposed (signals were non-actionable or the command is solid):

```
✅ /[command] reviewed — no amendments needed

Signals were either non-actionable or the command handled them correctly.
Logged to .writ/refresh-log.md for reference.
```

---

## Error Handling

**Command file not found:**
List available commands, ask the user to pick. Don't fail silently.

**User provides no feedback and no recent command run exists in conversation:**
Explain that `/refresh-command` works best right after running a command, when the experience is fresh. Offer to proceed anyway with the user providing feedback manually.

**All proposals declined:**
Log as "reviewed, no changes applied" in refresh-log. This is a valid outcome — not every run produces improvements.

---

## Cross-References

| Related | Relationship |
|---|---|
| All commands in `commands/` | Potential refresh targets |
| `.writ/refresh-log.md` | Append-only improvement history |
| `/verify-spec` | Can validate refreshed commands still produce spec-compliant output |
| `/new-command` | Creates new commands; `/refresh-command` improves existing ones |

---

## References

- Standing instructions: [`commands/_preamble.md`](_preamble.md)
- Identity & Prime Directive: [`system-instructions.md`](../system-instructions.md)
