# Refresh Command (refresh-command)

## Overview

The learning loop. After running a Writ command, `/refresh-command` turns your experience into concrete improvements. You describe what worked and what didn't — the agent reads the command file, proposes diffs, and applies approved changes. Commands get better through use.

This is **local-first**: amendments are applied to the project's command copy. Core commands in `commands/` stay untouched unless you manually promote changes.

## Invocation

| Invocation | Behavior |
|---|---|
| `/refresh-command` | Interactive — select command from list, or run skills boundary lint |
| `/refresh-command create-spec` | Refresh a specific command |
| `/refresh-command refresh-command` | Bootstrap — refresh-command improves itself |
| `/refresh-command --lint-skills` | Run boundary lint against every `skills/*/SKILL.md` and exit |
| `/refresh-command --check-parity` | Run agent parity lint (`agents/` ↔ `claude-code/agents/` ↔ `codex/agents/`) and exit |

---

## Phase 1: Select Command

**If `--check-parity` is passed:** skip phases 2–5 and run **Phase 6: Agent parity check** only (then stop). Do not append `refresh-log.md` for parity runs unless you also ran a command refresh or `--lint-skills` in the same invocation.

**If a command name was provided as an argument:**
1. Resolve to `commands/{name}.md`
2. Verify the file exists — if not, list available commands and ask the user to pick

**If no argument provided:**
1. Check conversation context — if a command was recently run, suggest it: *"You just ran /create-spec. Refresh that one?"*
2. If no recent command or user declines, present a top-level choice via `AskQuestion`:

   ```
   AskQuestion({
     title: "What do you want to refresh?",
     questions: [{
       id: "target",
       prompt: "Pick a refresh target.",
       options: [
         { id: "command", label: "Refresh a command (pick from list)" },
         { id: "lint-skills", label: "Run boundary lint across all skills" },
         { id: "parity", label: "Run agent parity check (agents ↔ Claude ↔ Codex TOMLs)" }
       ]
     }]
   })
   ```

   - **command** → list all files in `commands/` and ask the user to pick.
   - **lint-skills** → jump to **Phase 5: Skills Boundary Lint** and skip phases 2–4.
   - **parity** → jump to **Phase 6: Agent parity check** and skip phases 2–4.

**If `--lint-skills` is passed:** skip phases 2–4 and run **Phase 5** directly.

**Output:** The resolved command name and file path (or `skills lint` / `parity check` mode).

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

## Phase 5: Skills Boundary Lint

> **Triggered when:** the user picks `lint-skills` from the Phase 1 menu, or invokes `/refresh-command --lint-skills`. This is a separate refresh path — it does *not* run when refreshing a specific command, and the command-refresh flow above does *not* invoke it.

The boundary lint enforces the role convention from [ADR-009](../.writ/decision-records/adr-009-command-agent-skill-boundary.md) — skills describe a **capability**, not a workflow and not a role. The grammar is shared with `/new-skill`; both commands invoke `scripts/lint-skill.sh` so there is **no divergence** between authoring-time and review-time checks.

### Step 5.1: Discover Skills

Glob for `skills/*/SKILL.md` from the repository root.

If no skills exist, output:

```
No skills found. Run /new-skill to create one.
```

…and exit. Do not proceed to lint or write a refresh-log entry.

### Step 5.2: Run the Lint

```bash
bash scripts/lint-skill.sh skills/*/SKILL.md
```

The script processes every file and exits `0` (all clean), `1` (one or more violations), or `2` (usage error). Capture stdout — the script prints a per-file `✅` or `❌ <category> — <remediation>` line plus a summary tally.

### Step 5.3: Present Results

**If exit `0`:**

```
✅ All skills clean ({N} files checked)

  ✅ skills/<name-1>/SKILL.md
  ✅ skills/<name-2>/SKILL.md
  ...
```

**If exit `1`:** Surface the script's output verbatim — the user needs the exact line numbers, categories, and remediations. Then group by file and add a one-line summary:

```
❌ {V} violation(s) across {F} file(s)

Recommended next step: open each flagged file and revise the description
or body so it reads as a verb-phrase capability, not a role or workflow.
For deep boundary questions, see ADR-009.
```

Do **not** auto-rewrite skill files. The lint surfaces problems; the human (and `/new-skill` for net-new skills) owns the fix. This preserves the contract that skills are deliberately authored, not auto-generated.

**If exit `2`:** Surface the script's stderr and abort.

### Step 5.4: Log the Lint Run

Append an entry to `.writ/refresh-log.md` (create if missing):

```markdown
## [DATE] — skills boundary lint

**Source:** /refresh-command --lint-skills
**Files checked:** {N}
**Result:** {clean | {V} violation(s) across {F} file(s)}

{For each violating file, list the file path and violation categories.}

**Action:** No automatic edits — violations require human revision.
```

The log captures the lint run even when no edits are made; this gives `/status` and future audits a record of when boundary checks ran.

### Step 5.5: Final Output

If clean:

```
✅ Skills boundary lint complete — all {N} skills clean

Logged to .writ/refresh-log.md
```

If violations:

```
❌ Skills boundary lint complete — {V} violation(s) across {F} file(s)

Open each flagged file and revise. The lint will re-run on the next
/refresh-command --lint-skills invocation.

Logged to .writ/refresh-log.md
```

---

## Phase 6: Agent parity check

> **Triggered when:** the user picks `parity` from the Phase 1 menu, or invokes `/refresh-command --check-parity`.

Cross-platform Writ agents exist in three shapes: `agents/*.md` (canonical bodies), `claude-code/agents/writ-*.md`, and `codex/agents/*.toml`. This phase warns when a canonical agent is missing a counterpart — **warnings only; exit code is always 0** when the script completes.

### Exclusions

Contributors may omit a Claude Markdown variant when the role is intentionally Cursor/Codex-only:

| Canonical agent (`agents/<name>.md`) | Exemption |
|---|---|
| `visual-qa-agent` | No `claude-code/agents/` file today — parity lint skips the Claude check for this agent only. Codex and Cursor still carry the role. |

Add new rows here when a platform legitimately does not ship an agent (with rationale).

### Step 6.1: Run the parity script

From the repository root:

```bash
bash scripts/check-agent-parity.sh
```

Capture stdout verbatim.

### Step 6.2: Present results

**If output ends with the parity OK line and no `⚠️` lines appeared:**

```
✅ Agent parity check complete — parity OK

agents/, claude-code/agents/, and codex/agents/ are aligned (subject to documented exclusions).
```

**If one or more `⚠️` lines appeared:**

Print the script output verbatim, then summarize:

```
⚠️ Agent parity check complete — missing counterpart(s) reported above.

These are warnings only (exit 0). Restore or author the missing platform file,
or add a documented exclusion in Phase 6 if the omission is intentional.

Regenerate Codex TOMLs after editing canonical agents:

python3 scripts/gen-codex-agent-tomls.py
```

Do **not** auto-create agent files — surfacing drift is the goal.

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
| `skills/*/SKILL.md` | Lint targets in `--lint-skills` mode |
| `agents/*.md`, `claude-code/agents/*.md`, `codex/agents/*.toml` | Parity targets in `--check-parity` mode |
| `scripts/lint-skill.sh` | Boundary lint grammar — shared with `/new-skill` |
| `scripts/check-agent-parity.sh` | Agent parity warnings (always exit 0) |
| `scripts/gen-codex-agent-tomls.py` | Regenerate `codex/agents/*.toml` from canonical `agents/*.md` |
| `.writ/refresh-log.md` | Append-only improvement history (commands and skill lint runs) |
| `/verify-spec` | Can validate refreshed commands still produce spec-compliant output |
| `/new-command` | Creates new commands; `/refresh-command` improves existing ones |
| `/new-skill` | Creates new skills with the same lint enforced at authoring time |

---

## References

- Standing instructions: [`commands/_preamble.md`](_preamble.md)
- Identity & Prime Directive: [`system-instructions.md`](../system-instructions.md)
