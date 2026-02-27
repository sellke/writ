# Refresh Command (refresh-command)

## Overview

The learning loop. `/refresh-command` scans agent transcripts after command use, identifies where things went wrong (or unexpectedly right), and proposes concrete improvements to the command file that caused the friction.

Every time a Writ command runs, it leaves a trail — the agent transcript. This command reads that trail, extracts patterns, and turns them into actionable diffs. Commands get better through use. The framework learns.

This is **local-first**: amendments are applied to the project's local command copy (`.cursor/commands/`, `.claude/commands/`). The core command in `commands/` stays untouched until explicitly promoted through the promotion pipeline (Phase 6). Promotion is optional and gated — only universally applicable, high-confidence improvements are eligible.

## Invocation

| Invocation | Behavior |
|---|---|
| `/refresh-command` | Interactive — select command and transcript |
| `/refresh-command create-spec` | Fixed command, select transcript interactively |
| `/refresh-command create-spec --last` | Auto-selects most recent transcript for that command |
| `/refresh-command refresh-command --last` | Bootstrap — refresh-command analyzes and improves itself |

## Pipeline

```
┌──────────────┐   ┌──────────────┐   ┌──────────────┐   ┌──────────────┐   ┌──────────────┐   ┌──────────────┐
│   PHASE 1    │──▶│   PHASE 2    │──▶│   PHASE 3    │──▶│   PHASE 4    │──▶│   PHASE 5    │──▶│   PHASE 6    │
│   SELECT     │   │   SCAN       │   │   ANALYZE    │   │   PROPOSE    │   │   APPLY      │   │   PROMOTE    │
│  command +   │   │  transcript  │   │  friction &  │   │  amendments  │   │  local copy  │   │  (optional)  │
│  transcript  │   │  (.jsonl)    │   │  patterns    │   │  (diffs)     │   │  + changelog │   │  upstream PR │
└──────────────┘   └──────────────┘   └──────────────┘   └──────────────┘   └──────────────┘   └──────────────┘
       │                  │                  │                  │                  │                  │
  interactive or     parse lines,      root cause,       diff + rationale   .cursor/commands/   Yes → PR
  arg-based          extract signals   impact, fixability + confidence       + refresh-log.md    No → local only
                                                                                                 Later → queued
```

## Command Process

### Phase 1: Command & Transcript Selection

#### Step 1.1: Determine Mode

Parse invocation arguments:

| Arguments | Mode | Command | Transcript |
|---|---|---|---|
| None | Interactive | User selects | User selects |
| `[command-name]` | Semi-interactive | Fixed from arg | User selects |
| `[command-name] --last` | Automatic | Fixed from arg | Most recent match |

#### Step 1.2: Command Selection (Interactive Mode)

**If no command argument provided**, scan `commands/` for available Writ commands and present selection:

```
AskQuestion({
  title: "Refresh Command — Select Target",
  questions: [
    {
      id: "command",
      prompt: "Which command do you want to refresh?",
      options: [
        // Dynamically generated from commands/*.md
        // Show command name + one-line description from each file's ## Overview
        { id: "create-spec", label: "create-spec — Generate feature specifications" },
        { id: "implement-story", label: "implement-story — Per-story 6-gate SDLC pipeline" },
        { id: "implement-spec", label: "implement-spec — End-to-end spec execution" },
        { id: "refresh-command", label: "refresh-command — Learning loop (bootstrap)" },
        // ... all discovered commands
      ]
    }
  ]
})
```

#### Step 1.3: Transcript Discovery

Scan for agent transcripts. Transcripts are `.jsonl` files containing conversation turns between the user and the AI agent.

**Search locations (in order):**

1. **Cursor IDE transcripts:** `agent-transcripts/*.jsonl` (project-level Cursor transcript directory)
2. **Explicit path:** If user provides a file path instead of a command name, use that directly

**For each transcript found:**
1. Read the first 20–30 lines to extract metadata
2. Determine the date from file modification time or content timestamps
3. Attempt to identify which Writ command was executed (see Step 2.2 for detection logic)
4. Build a selection list with: `[date] — [inferred command or "unknown"] — [transcript ID]`

**Filtering by command (when command is specified):**

- Scan each transcript's opening lines for the target command name
- Match patterns: `/[command-name]`, `command: [command-name]`, references to `commands/[command-name].md`
- If `--last` flag is set, sort matching transcripts by date descending and auto-select the first

#### Step 1.4: Transcript Selection (Interactive/Semi-Interactive Mode)

```
AskQuestion({
  title: "Select Transcript to Analyze",
  questions: [
    {
      id: "transcript",
      prompt: "Which transcript should I scan for improvement signals?",
      options: [
        // Dynamically generated from discovered transcripts
        // Filtered to matching command if one was specified
        { id: "abc123", label: "2026-02-27 — /create-spec — abc123.jsonl" },
        { id: "def456", label: "2026-02-26 — /create-spec — def456.jsonl" },
        { id: "ghi789", label: "2026-02-25 — /implement-story — ghi789.jsonl" },
        // ... sorted by date, most recent first
      ]
    }
  ]
})
```

**After selection, confirm and proceed:**

```
🔍 Refresh target locked.

Command:    /create-spec
Transcript: abc123.jsonl (2026-02-27)
Source:     commands/create-spec.md

Scanning transcript for improvement signals...
```

---

### Phase 2: Transcript Scanning

#### Step 2.1: Parse Transcript

Read the selected `.jsonl` file. Each line is a JSON object representing one conversation turn:

```jsonl
{"role": "user", "message": {"content": "..."}}
{"role": "assistant", "message": {"content": [{"type": "text", "text": "..."}]}}
{"role": "tool", "message": {"name": "Shell", "result": "..."}}
```

**Parsing rules:**

1. Read each line as independent JSON (newline-delimited)
2. Extract `role` (user/assistant/tool) and `message.content`
3. Content may be a plain string or an array of content blocks — normalize to text
4. For tool calls, extract `message.name` and `message.result`
5. Build an ordered list of conversation turns with: `[index, role, content_text, tool_name?]`
6. For very large transcripts (>500 turns), prioritize:
   - First 30 turns (setup/context)
   - Last 50 turns (completion/issues)
   - Any turns containing error messages, retries, or AskQuestion calls
   - Tool call sequences with >3 consecutive failures

#### Step 2.2: Identify Command

Determine which Writ command was being executed. Scan in this priority order:

1. **User's first message** — look for `/command-name` invocation pattern
2. **System context** — look for `<user_query>` tags referencing a command or `command:` metadata
3. **File reads** — look for `Read("commands/[name].md")` tool calls in early turns
4. **Content references** — look for mentions of specific command phases, steps, or agent names that uniquely identify a command

If identification is ambiguous, note the uncertainty and proceed — signal extraction still works on the raw conversation flow.

#### Step 2.3: Extract Signals

Scan the full transcript for four signal categories. For each signal found, record:
- **Turn range** — which conversation turns contain the signal
- **Category** — friction / skip / surprise / duration
- **Raw evidence** — the actual text or pattern that triggered detection
- **Severity** — how significant this signal appears (high/medium/low)

---

**Signal Category 1: Friction**

Points where the agent struggled, produced low-quality output, or required excessive iteration.

| Pattern to detect | Example evidence in transcript |
|---|---|
| Retry loops | Agent says "let me try again", "that didn't work", "I'll take a different approach" |
| Tool call failures | Consecutive failed Shell/Read/Write calls on the same target |
| Correction sequences | User says "no, that's wrong", "not what I asked for", "try again" |
| Confusion signals | Agent asks questions already answered, misinterprets instructions |
| Over-generation | Agent produces excessive output that user ignores or truncates |
| Backtracking | Agent undoes its own recent changes, rewrites same section multiple times |
| Missing context | Agent says "I don't have enough information", asks for context the command should provide |

---

**Signal Category 2: Skip**

Steps that users bypassed, dismissed, or found unnecessary.

| Pattern to detect | Example evidence in transcript |
|---|---|
| Explicit skips | User says "skip this", "let's move on", "that's not needed" |
| Ignored output | Agent produces a detailed section user doesn't reference or acknowledge |
| Dismissed questions | Agent asks a question, user gives minimal/dismissive answer ("fine", "whatever", "sure") |
| Workflow shortcuts | User jumps ahead in the prescribed command flow, skipping intermediate steps |
| Repeated skips | Same step type skipped across multiple invocations (cross-transcript, if available) |

---

**Signal Category 3: Surprise**

Places where output quality deviated significantly from expectations — positive or negative.

| Pattern to detect | Example evidence in transcript |
|---|---|
| Positive surprise | User says "perfect", "exactly what I needed", "that's great", "wow" |
| Negative surprise | User says "that's completely wrong", "why did you do that", "this doesn't make sense" |
| Unexpected scope | Agent produces much more or much less than the step seemed to require |
| Quality mismatch | Agent output quality varies dramatically between steps (stellar code, then terrible docs) |

---

**Signal Category 4: Duration**

Steps that consumed disproportionate time or conversation turns.

| Pattern to detect | Example evidence in transcript |
|---|---|
| Turn-heavy steps | A single logical step spans >15 conversation turns |
| Long tool chains | >10 consecutive tool calls without user interaction |
| Stalled progress | Multiple turns with no visible forward progress on the task |
| Repetitive patterns | Same type of action repeated many times (e.g., reading file after file without acting) |

---

**Output of Phase 2:** A structured signal list:

```markdown
## Transcript Scan Results

**Transcript:** abc123.jsonl
**Command:** /create-spec
**Total turns:** 127
**Signals found:** 6

### Signal 1: Friction — Retry loop in clarification phase
- **Turns:** 34–52
- **Evidence:** Agent asked 3 rounds of questions that overlapped; user corrected misinterpretation twice
- **Severity:** High

### Signal 2: Skip — Documentation step bypassed
- **Turns:** 98–101
- **Evidence:** User said "skip the docs for now" when agent began generating README content
- **Severity:** Low

### Signal 3: Surprise — Excellent story decomposition
- **Turns:** 78–85
- **Evidence:** User said "these stories are perfect, exactly the right granularity"
- **Severity:** Medium (positive — preserve this behavior)

[... etc]
```

---

### Phase 3: Friction Analysis

#### Step 3.1: Spawn Analysis Agent

For each extracted signal, spawn a read-only analysis agent to determine root cause and actionability:

```
Task({
  subagent_type: "generalPurpose",
  readonly: true,
  description: "Analyze transcript friction signals",
  prompt: `You are the Refresh Analysis Agent. Your job is to determine why friction
occurred during command execution and whether the command file can be changed to prevent it.

## Command Under Analysis
**Command:** /[command-name]
**Command file contents:**
[full contents of commands/[command-name].md]

## Signals Extracted from Transcript
[structured signal list from Phase 2]

## Analysis Framework

For EACH signal, determine:

### 1. Root Cause (pick one)
- **Command design** — The command's instructions are unclear, incomplete, or misleading.
  The agent followed the command correctly but the command led it astray.
- **Prompt quality** — The command is fine but the phrasing causes the agent to
  misinterpret intent or produce suboptimal output.
- **Context gap** — The command doesn't provide enough context for the agent to succeed.
  Missing information about the codebase, user preferences, or domain knowledge.
- **Agent limitation** — The agent hit a capability ceiling unrelated to the command
  (e.g., token limits, tool failures). Not fixable via command changes.
- **User behavior** — The friction was caused by the user, not the command.
  (e.g., unclear input, changing requirements mid-flow). Not fixable via command changes.

### 2. Impact Assessment
- **Time cost:** How many turns/minutes did this friction add? (Minor: 1-3 turns, Moderate: 4-10 turns, Major: 10+ turns)
- **Quality cost:** Did this degrade the final output? (None / Minor degradation / Significant degradation)
- **User experience:** How much frustration did this likely cause? (Low / Medium / High)

### 3. Frequency Assessment
- **Isolated:** Appears to be a one-off occurrence tied to specific input
- **Likely recurring:** Pattern suggests this would happen with similar inputs
- **Systematic:** Root cause is structural — will happen on every invocation

### 4. Fixability Assessment
- **Directly fixable:** A specific change to the command file would prevent this
- **Partially fixable:** Can reduce likelihood but not eliminate entirely
- **Not fixable via command:** Requires agent capability improvements or user behavior change

## Output Format

For each signal, output:

### Signal [N]: [Category] — [Brief description]
- **Root cause:** [classification + 1-sentence explanation]
- **Impact:** Time: [Minor/Moderate/Major] | Quality: [None/Minor/Significant] | UX: [Low/Medium/High]
- **Frequency:** [Isolated/Likely recurring/Systematic]
- **Fixability:** [Directly fixable/Partially fixable/Not fixable]
- **Recommendation:** [1-2 sentences on what to change, or "No command change needed" if not fixable]
`
})
```

#### Step 3.2: Filter Actionable Signals

From the analysis output, filter to signals that are:
1. **Fixable** — Root cause is command design, prompt quality, or context gap
2. **Impactful** — At least moderate time cost OR any quality/UX cost
3. **Not isolated** — Likely recurring or systematic (unless impact is Major)

Signals classified as "agent limitation" or "user behavior" with "not fixable" are logged but don't produce amendments.

#### Step 3.3: Present Analysis Summary

```
📊 Analysis Complete

Signals analyzed: 6
Actionable (will produce amendments): 3
Non-actionable (logged): 3

### Actionable Signals
1. 🔴 Friction — Overlapping clarification questions (command design, directly fixable)
2. 🟡 Skip — Documentation step unnecessary for quick runs (command design, directly fixable)
3. 🟢 Surprise — Story decomposition quality (positive — preserve in command)

### Non-Actionable Signals
4. Duration — Long codebase scan (agent limitation)
5. Friction — Tool call timeout (agent limitation)
6. Skip — User skipped validation (user behavior)

Generating amendment proposals for 3 actionable signals...
```

---

### Phase 4: Amendment Proposal

#### Step 4.1: Generate Amendments

For each actionable signal, produce a concrete amendment to the command file.

**Amendment format:**

```markdown
### Amendment [N]: [Brief title]

**Signal:** [Category] — [Description]
**Confidence:** High / Medium / Low
**Scope:** Project-specific / Universal

**Rationale:**
[2-3 sentences explaining why this change improves the command. Reference the specific
friction observed and how the change prevents it.]

**Diff:**

~~~diff
--- commands/[command].md
+++ commands/[command].md (amended)

@@ Section: [section name] @@

- [original lines]
+ [replacement lines]
~~~
```

**Confidence criteria:**

| Confidence | When to assign |
|---|---|
| **High** | Clear causal link between command text and friction. Signal is systematic. Fix is targeted and low-risk. |
| **Medium** | Probable causal link. Signal is likely recurring. Fix addresses the root cause but may have side effects. |
| **Low** | Possible connection. Signal may be isolated. Fix is speculative — needs more data to confirm. |

**Scope criteria:**

| Scope | When to assign |
|---|---|
| **Universal** | The improvement applies to any project using this command. The friction is inherent to the command design, not the project context. |
| **Project-specific** | The improvement is tied to this project's codebase, tech stack, or workflow. Other projects wouldn't benefit. |

#### Step 4.2: Handle Positive Signals

For positive surprise signals, generate a **preservation amendment** instead of a fix:

```markdown
### Amendment [N]: Preserve — [what worked well]

**Signal:** Surprise (positive) — [Description]
**Confidence:** Medium
**Scope:** Universal

**Rationale:**
This behavior produced excellent results but isn't explicitly documented in the command.
Making it explicit ensures it's preserved across future edits and adopted by other commands.

**Diff:**

~~~diff
--- commands/[command].md
+++ commands/[command].md (amended)

@@ Section: [relevant section] @@

+ **Best practice (observed):** [description of what the agent did well and why it worked]
~~~
```

#### Step 4.3: Present Proposals for Approval

Present all amendments and let the user choose which to apply:

```
AskQuestion({
  title: "Review Amendment Proposals",
  questions: [
    {
      id: "amendments",
      prompt: "Which amendments should I apply to the local command copy?",
      allow_multiple: true,
      options: [
        {
          id: "amend_1",
          label: "🔴 [High] Deduplicate clarification questions (Universal)"
        },
        {
          id: "amend_2",
          label: "🟡 [Medium] Add --quick skip for docs step (Universal)"
        },
        {
          id: "amend_3",
          label: "🟢 [Medium] Preserve story decomposition guidance (Universal)"
        },
        { id: "all", label: "Apply all amendments" },
        { id: "none", label: "Skip — don't apply any amendments" }
      ]
    }
  ]
})
```

If user selects "none", log the proposals to `.writ/refresh-log.md` as "proposed but not applied" and exit.

---

### Phase 5: Local Apply + Changelog

#### Step 5.1: Resolve Target File

Amendments are applied to the **local command copy**, not the core command.

**Resolution order:**

1. **Cursor:** `.cursor/commands/[command].md`
2. **Claude Code:** `.claude/commands/[command].md`
3. **Auto-detect:** Check which local directories exist and apply to all found

If no local copy exists, create one by copying the core command from `commands/[command].md` as the base, then apply amendments on top.

#### Step 5.2: Apply Amendments

For each approved amendment:

1. Read the current local command file
2. Locate the target section (match by heading text and surrounding context)
3. Apply the diff — replace the matched lines with the amended lines
4. If the section can't be located (command has diverged), present the diff to the user and ask for manual placement
5. Write the updated file

**After all amendments applied, verify:**
- The file is valid markdown (no broken headings, unclosed code blocks)
- No content was accidentally deleted
- The overall command structure is preserved

#### Step 5.3: Write Changelog

Append an entry to `.writ/refresh-log.md` (create the file if it doesn't exist):

```markdown
## [DATE] — /[command] refreshed

**Source transcript:** [transcript ID]
**Signals found:** [N] total, [M] actionable
**Amendments applied:** [K] of [M] proposed

**Changes:**
- [Amendment 1 title] — [one-line summary] (Confidence: [H/M/L], Scope: [scope])
- [Amendment 2 title] — [one-line summary] (Confidence: [H/M/L], Scope: [scope])

**Not applied:**
- [Amendment N title] — [reason: user declined / not fixable / low confidence]

**Scope:** Local only
**Confidence:** High / Medium / Low
**Target file:** .cursor/commands/[command].md
```

#### Step 5.4: Summary Report

```
✅ /[command] refreshed successfully

Transcript scanned: [transcript ID] ([date])
Signals found:      [N] total ([M] actionable)
Amendments applied: [K] to .cursor/commands/[command].md

Applied:
  ✅ Deduplicate clarification questions (High confidence, Universal)
  ✅ Add --quick skip for docs step (Medium confidence, Universal)
  ✅ Preserve story decomposition guidance (Medium confidence, Universal)

Changelog: .writ/refresh-log.md updated

💡 Run `/refresh-command [command] --last` again after your next use
   to see if the improvements landed.
```

---

### Phase 6: Promotion Review

After local apply, determine whether the improvements should be promoted upstream to Writ core. Promotion is **optional** — most refreshes stay local. The prompt only appears when improvements are genuinely universal.

#### Step 6.1: Evaluate Promotion Eligibility

Check the scope and confidence of all **applied** amendments from Phase 4/5:

| Condition | Result |
|---|---|
| **Any** applied amendment has Scope = Universal **AND** Confidence = High | Eligible — proceed to Step 6.2 |
| **All** applied amendments are Project-specific **OR** Confidence is Medium/Low | Not eligible — skip to Step 6.4 |
| No amendments were applied | Not eligible — skip to Step 6.4 |

Only amendments that are both universally applicable and high-confidence warrant the promotion conversation. Project-specific improvements (monorepo structure, tech stack quirks, team conventions) should never be promoted.

#### Step 6.2: Present Promotion Prompt

When eligible, present the promotion-eligible amendments and ask the user:

```
AskQuestion({
  title: "Promote to Writ Core?",
  questions: [
    {
      id: "promote",
      prompt: `These improvements look universally applicable:

${eligible_amendments.map(a => `• ${a.title} — ${a.summary} (${a.confidence})`).join('\n')}

Promote to Writ core? This creates a PR against the writ repository.`,
      options: [
        { id: "yes", label: "Yes — generate upstream PR" },
        { id: "no", label: "No — keep local only" },
        { id: "later", label: "Later — save for batch promotion review" }
      ]
    }
  ]
})
```

#### Step 6.3: Execute Promotion Decision

**If "Yes" — Generate PR:**

1. **Generate diff** between the core command (`commands/[command].md`) and the local amended copy (`.cursor/commands/[command].md`):

```bash
diff -u commands/[command].md .cursor/commands/[command].md > /tmp/refresh-promotion.diff
```

2. **Create a promotion branch:**

```bash
git checkout -b writ/refresh-[command]-[YYYY-MM-DD]
```

3. **Apply the local amendments to the core command:**

Copy the promotion-eligible changes (not project-specific amendments) from the local copy to the core file. If the local copy contains a mix of universal and project-specific amendments, apply only the universal ones to the core command.

```bash
# Apply targeted changes to the core command
# (use StrReplace for surgical edits rather than full file copy)
```

4. **Commit and create PR:**

```bash
git add commands/[command].md
git commit -m "refresh: /[command] — [amendment titles]

Source transcript: [transcript ID]
Confidence: High
Amendments: [list]

Generated by /refresh-command promotion pipeline."

gh pr create \
  --title "refresh: /[command] — [brief description]" \
  --body "$(cat <<'EOF'
## Refresh Promotion

**Source:** `/refresh-command` analysis of transcript `[transcript ID]`
**Confidence:** High
**Scope:** Universally applicable

### Changes

[For each promoted amendment:]
- **[Amendment title]:** [Rationale from Phase 4 analysis]

### Evidence

These improvements were identified by analyzing agent transcript `[transcript ID]`,
where the following friction was observed:

[Brief summary of the signals that led to these amendments]

### Verification

- [x] Applied locally and tested in project context
- [ ] Reviewed by maintainer
EOF
)"
```

5. **Return to original branch:**

```bash
git checkout -  # return to previous branch
```

6. **Update refresh-log entry:**

Update the `**Scope:**` line from "Local only" to "Promoted to core" and append the PR URL:

```markdown
**Scope:** Promoted to core
**Promoted via:** [PR URL from gh pr create output]
```

**If "No" — Keep Local:**

No additional action needed. The refresh-log entry from Phase 5 already reads `**Scope:** Local only`. Output confirmation:

```
📌 Improvements kept local. No PR created.
```

**If "Later" — Queue for Batch Review:**

Append the batch review flag to the refresh-log entry:

```markdown
**Batch review:** Queued
```

Output confirmation:

```
📋 Queued for batch promotion review.

To review accumulated improvements later, scan .writ/refresh-log.md
for entries marked "Batch review: Queued".
```

#### Step 6.4: Handle Non-Eligible (Skip Promotion)

When promotion eligibility check fails (Step 6.1), write the refresh-log entry with `**Scope:** Local only` and no batch flag. No user interaction. Output:

```
📝 Refresh complete. Improvements are project-specific or below promotion threshold — kept local.
```

#### Step 6.5: PR Creation Error Handling

If PR creation fails at any point in the "Yes" flow, handle gracefully:

**Authentication failure (no `gh` auth or no push access):**

```
⚠️ Could not create PR — GitHub CLI not authenticated or no push access.

Fallback: Saving promotion diff as a patch file.
```

Save the diff:

```bash
diff -u commands/[command].md .cursor/commands/[command].md \
  > .writ/refresh-promotion-[YYYY-MM-DD].patch
```

Update refresh-log:

```markdown
**Scope:** Local only
**Promotion fallback:** .writ/refresh-promotion-[YYYY-MM-DD].patch
```

**No remote / no fork:**

```
⚠️ No remote repository found for Writ core, or fork not configured.

Fallback: Saving promotion diff as a patch file.
You can manually apply this patch and create a PR when ready:

  cd /path/to/writ
  git apply .writ/refresh-promotion-[YYYY-MM-DD].patch
```

**Branch conflict:**

If the promotion branch already exists (from a previous attempt), append a counter:

```bash
git checkout -b writ/refresh-[command]-[YYYY-MM-DD]-2
```

**General failure:**

Any unexpected error during the PR creation flow should:
1. Revert to the original branch (`git checkout -`)
2. Clean up any partial state
3. Save the patch file as fallback
4. Update refresh-log with the fallback path
5. Never leave the working directory dirty

#### Step 6.6: Final Summary

Update the Phase 5 summary report to include promotion status:

```
✅ /[command] refreshed successfully

Transcript scanned: [transcript ID] ([date])
Signals found:      [N] total ([M] actionable)
Amendments applied: [K] to .cursor/commands/[command].md

Applied:
  ✅ Deduplicate clarification questions (High confidence, Universal)
  ✅ Add --quick skip for docs step (Medium confidence, Universal)
  ✅ Preserve story decomposition guidance (Medium confidence, Universal)

Promotion: [Promoted to core (PR #42) / Local only / Queued for batch review / Skipped (not eligible)]

Changelog: .writ/refresh-log.md updated

💡 Run `/refresh-command [command] --last` again after your next use
   to see if the improvements landed.
```

---

### Batch Promotion Review

Entries marked `**Batch review:** Queued` accumulate in `.writ/refresh-log.md` over time. Periodically reviewing these deferred promotions is valuable — patterns emerge across multiple refreshes that aren't visible in a single session.

#### When to Review

- After 5+ entries accumulate with `Batch review: Queued`
- Before a Writ release or version bump
- When a command has been refreshed 3+ times locally without promotion

#### Review Process

1. **Scan refresh-log** for entries with `Batch review: Queued`:

```bash
rg "Batch review: Queued" .writ/refresh-log.md -B 20
```

2. **Group by command** — multiple refreshes of the same command may have overlapping or complementary improvements

3. **Evaluate in aggregate** — an improvement that seemed marginal in isolation may be clearly valuable when the same pattern appears across 3 transcripts

4. **Promote or discard** — for each queued entry:
   - **Promote:** Follow the "Yes" flow from Step 6.3, using the current local command copy
   - **Discard:** Update the entry: replace `**Batch review:** Queued` with `**Batch review:** Reviewed — kept local`
   - **Superseded:** If a later refresh already covers this improvement, mark: `**Batch review:** Reviewed — superseded by [DATE] entry`

---

## Refresh-Log Format

See `.writ/docs/refresh-log-format.md` for the canonical refresh-log entry specification, including field definitions, scope/confidence values, and examples for every promotion outcome.

---

## Transcript Format Reference

Agent transcripts are `.jsonl` files — one JSON object per line, representing sequential conversation turns.

**Location:** `agent-transcripts/` directory (relative to project Cursor config)

**File naming:** `[uuid].jsonl` — each file represents one complete agent session

**Line format examples:**

```jsonl
{"role":"user","message":{"content":"Create a spec for the authentication feature"}}
{"role":"assistant","message":{"content":[{"type":"text","text":"I'll scan..."}]}}
{"role":"assistant","message":{"content":[{"type":"tool_use","name":"Read","input":{"path":"commands/create-spec.md"}}]}}
{"role":"tool","message":{"content":[{"type":"tool_result","content":"# Enhanced Create Spec..."}]}}
```

**Key fields:**

| Field | Type | Description |
|---|---|---|
| `role` | string | `"user"`, `"assistant"`, or `"tool"` |
| `message.content` | string or array | Plain text or array of content blocks |
| `content[].type` | string | `"text"`, `"tool_use"`, `"tool_result"` |
| `content[].text` | string | Text content (when type is "text") |
| `content[].name` | string | Tool name (when type is "tool_use") |
| `content[].input` | object | Tool parameters (when type is "tool_use") |

**Handling variations:**
- Content may be a raw string (`"content": "hello"`) or structured (`"content": [{"type": "text", "text": "hello"}]`) — normalize both to plain text for analysis
- Some transcripts include `system` role messages with context injection — these are useful for command identification but not for signal extraction
- Sub-agent transcripts (nested sessions) may exist but the primary `.jsonl` at the root level is the main analysis target

---

## Signal Detection Guide

### Friction Signals — What to Look For

**High-confidence friction indicators:**
- 3+ consecutive tool calls targeting the same file/resource (thrashing)
- Agent apologizing: "sorry", "my mistake", "let me correct that"
- User expressing frustration: "no", "wrong", "that's not what I meant", "try again"
- Agent re-reading a command file mid-execution (lost its place)
- Same content generated, deleted, and regenerated

**Context for determining command-attributable friction:**
- Was the agent following the command's instructions when friction occurred?
- Would clearer instructions in the command have prevented the confusion?
- Did the command fail to mention a prerequisite or common edge case?

### Skip Signals — What to Look For

**High-confidence skip indicators:**
- User explicitly says "skip", "next", "move on", "don't need this"
- Agent produces structured output (table, checklist, etc.) that user doesn't acknowledge
- Command defines N steps but only N-2 are executed with no explanation
- User provides a one-word answer to a multi-part question

**Context for determining if skip is a command issue:**
- Was the skipped step providing real value, or was it ceremonial?
- Is the step optional but not marked as such in the command?
- Would the command benefit from a `--quick` mode that skips this step?

### Surprise Signals — What to Look For

**Positive surprise indicators:**
- Enthusiastic user response: "perfect", "exactly right", "love it", "brilliant"
- User quotes or reuses agent output verbatim (high-quality generation)
- Agent handles an edge case the command didn't explicitly address

**Negative surprise indicators:**
- User rejects output entirely: "start over", "completely wrong"
- Agent's output contradicts the command's stated goals
- Output quality drops sharply between steps (e.g., great code, terrible tests)

### Duration Signals — What to Look For

**High-confidence duration indicators:**
- >15 turns for a step that similar commands complete in <5 turns
- >10 sequential tool calls without user interaction (automated thrashing)
- Agent explicitly notes it's taking longer than expected
- User asks "are you done?" or "how much longer?"

---

## Analysis Framework

### Root Cause Taxonomy

| Root Cause | Description | Command Fix? | Example |
|---|---|---|---|
| **Command design** | Instructions are unclear, incomplete, contradictory, or lead the agent down a wrong path | ✅ Yes | Command says "scan codebase" but doesn't specify what to scan for |
| **Prompt quality** | Instructions are correct but phrased in a way that causes misinterpretation | ✅ Yes | "Generate a summary" interpreted as 3 paragraphs when 3 bullets were intended |
| **Context gap** | Command doesn't provide enough background information for the agent to succeed | ✅ Yes | Command doesn't mention that the project uses a monorepo structure |
| **Agent limitation** | Agent hit a capability boundary (token limit, tool failure, reasoning error) | ❌ No | Transcript too large for context window |
| **User behavior** | Friction was caused by user input, not the command | ❌ No | User changed requirements mid-flow |

### Impact Matrix

| Dimension | Minor | Moderate | Major |
|---|---|---|---|
| **Time cost** | 1–3 extra turns | 4–10 extra turns | 10+ extra turns or session restart |
| **Quality cost** | Output slightly suboptimal | Noticeable degradation in output | Output unusable, required rework |
| **UX cost** | Mild inconvenience | Noticeable frustration | User abandoned the flow |

### Fixability Criteria

| Level | Criteria | Action |
|---|---|---|
| **Directly fixable** | A targeted edit to the command file would prevent this friction with high probability | Generate amendment |
| **Partially fixable** | An edit would reduce likelihood by ~50%+ but can't eliminate it entirely | Generate amendment with Medium confidence |
| **Not fixable via command** | The root cause is outside command control (agent capability, user behavior, environment) | Log signal, no amendment |

---

## Bootstrap Property

`/refresh-command` is designed to work on itself. This is not an afterthought — it's the core validation of the learning loop.

**How it works:**

1. Use `/refresh-command` to analyze any Writ command
2. After that session, run `/refresh-command refresh-command --last`
3. The command scans its own usage transcript
4. It identifies friction in its own transcript scanning, analysis, or proposal phases
5. It proposes amendments to `commands/refresh-command.md` itself

**Why this matters:**
- If `/refresh-command` can't improve itself, it's not sensitive enough to improve other commands
- The first post-ship validation is always: refresh the refresher
- Bootstrap loops expose meta-issues (e.g., "the signal detection guide missed a category")

**Bootstrap-specific signals to watch for:**
- Did the transcript scanning phase miss obvious friction in the analyzed transcript?
- Did the analysis agent misclassify a root cause?
- Were the proposed diffs too vague or too surgical?
- Was the interactive selection flow smooth, or did the user struggle to pick the right transcript?

**Self-referential constraint:** When refreshing itself, the command must not propose changes that would break its own execution flow. Amendments should be additive or refinement-level, not structural rewrites (those require a deliberate `/edit-spec` cycle).

---

## Error Handling

**No transcripts found:**
```
⚠️ No agent transcripts found in agent-transcripts/

The /refresh-command requires at least one agent transcript to analyze.
Use a Writ command first (e.g., /create-spec), then run /refresh-command.

Checked locations:
- agent-transcripts/*.jsonl
```

**Command not identified in transcript:**
```
⚠️ Could not determine which Writ command was used in transcript [ID].

The transcript doesn't contain clear command invocation patterns.

Options:
1. Specify the command manually: /refresh-command [command-name] --transcript [ID]
2. Select a different transcript
3. Proceed with general analysis (no command-specific context)
```

**No signals found (clean transcript):**
```
✅ No improvement signals found in transcript [ID].

The /[command] execution was clean — no friction, skips, surprises, or duration anomalies detected.

This is either a well-tuned command or the transcript was too short for meaningful analysis.
Consider running /refresh-command after a longer, more complex session.
```

**No actionable signals (all non-fixable):**
```
📊 Signals found but none are command-fixable.

[N] signals detected, but all root causes are:
- Agent limitation ([count])
- User behavior ([count])

No amendments proposed. Signals logged to .writ/refresh-log.md for reference.
```

**Local command file diverged significantly from core:**
```
⚠️ Local command file has diverged significantly from the core command.

The diff targets a section that no longer exists in .cursor/commands/[command].md.

Options:
1. Show me the diff — I'll apply it manually
2. Reset local copy to core and re-apply amendments
3. Skip this amendment
```

**Large transcript warning (>500 turns):**
```
⚠️ Large transcript detected ([N] turns).

Scanning will focus on high-signal regions:
- First 30 turns (setup)
- Last 50 turns (completion)
- Error/retry sequences
- AskQuestion interactions

This may miss signals in the middle of the session.
Continue with focused scan, or provide a turn range to analyze.
```

---

## Integration with Writ Ecosystem

| Command | Relationship |
|---------|-------------|
| All commands (`commands/*.md`) | Source files that `/refresh-command` proposes amendments to |
| `/implement-story` | May be the most frequently refreshed command (complex pipeline, most usage) |
| `/create-spec` | Good refresh target after spec creation sessions |
| `/verify-spec` | Could validate that refreshed commands still produce spec-compliant output |
| `/new-command` | Creates new commands; `/refresh-command` improves existing ones |
| **Phase 6: Promotion pipeline** | Promotes universal, high-confidence local amendments from `.cursor/commands/` back to core `commands/` via PR |
| **`.writ/docs/refresh-log-format.md`** | Canonical format specification for refresh-log entries |
