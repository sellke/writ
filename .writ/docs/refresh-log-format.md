# Refresh-Log Format Specification

> Canonical reference for `.writ/refresh-log.md` entries.
> Used by `/refresh-command` (Phase 5: Changelog + Phase 6: Promotion Review).

---

## File Location & Lifecycle

**Path:** `.writ/refresh-log.md`

**Creation:** `/refresh-command` creates the file on first run if it doesn't exist. The file opens with a single header:

```markdown
# Refresh Log
```

**Append-only:** New entries are appended below the header. Entries are never modified after writing, with one exception: the "Yes" promotion flow updates `**Scope:**` from "Local only" to "Promoted to core" and appends the PR URL.

**Ordering:** Most recent entry at the bottom (natural append). Readers who want reverse-chronological order read from the end.

---

## Entry Structure

Every `/refresh-command` completion writes exactly one entry, regardless of outcome.

```markdown
## YYYY-MM-DD — /[command] refreshed

**Source transcript:** [transcript ID]
**Signals found:** [N] total, [M] actionable
**Amendments applied:** [K] of [M] proposed

**Changes:**
- [Amendment title] — [one-line summary] (Confidence: High/Medium/Low, Scope: Universal/Project-specific)
- [Amendment title] — [one-line summary] (Confidence: High/Medium/Low, Scope: Universal/Project-specific)

**Not applied:**
- [Amendment title] — [reason: user declined / not fixable / low confidence]

**Scope:** Local only | Promoted to core
**Confidence:** High | Medium | Low
**Target file:** .cursor/commands/[command].md
```

### Field Reference

| Field | Format | Description |
|---|---|---|
| **Date** | `YYYY-MM-DD` | Date the refresh was performed |
| **Command** | `/[command-name]` | The Writ command that was refreshed |
| **Source transcript** | Transcript filename (e.g., `abc123.jsonl`) | The agent transcript that was analyzed |
| **Signals found** | `N total, M actionable` | Signal counts from the scan phase |
| **Amendments applied** | `K of M proposed` | How many proposals the user accepted |
| **Changes** | Bulleted list | Each applied amendment with title, summary, confidence, and scope |
| **Not applied** | Bulleted list | Each declined/skipped amendment with reason. Omit section if all were applied. |
| **Scope** | `Local only` or `Promoted to core` | Whether the changes were promoted upstream |
| **Confidence** | `High`, `Medium`, or `Low` | Overall confidence — the highest confidence among applied amendments |
| **Target file** | Relative path | The local command file that was modified |

### Optional Fields

These fields appear only when relevant:

| Field | When Present | Format |
|---|---|---|
| **Batch review:** | User chose "Later" on promotion prompt | `Queued` |
| **Promoted via:** | User chose "Yes" and PR was created | PR URL (e.g., `https://github.com/user/writ/pull/42`) |
| **Promotion fallback:** | PR creation failed, patch file saved instead | Path to `.writ/refresh-promotion-YYYY-MM-DD.patch` |

---

## Scope Values

| Value | Meaning | When Set |
|---|---|---|
| **Local only** | Changes remain in the project's local command copy. No upstream PR. | Default for all entries. Set when: user chooses "No", user chooses "Later", promotion prompt was skipped (scope not universal or confidence not High). |
| **Promoted to core** | A PR was created to merge changes into the Writ core repository. | Set when user chooses "Yes" and PR creation succeeds. Replaces the initial "Local only" value. |

## Confidence Values

| Value | Meaning |
|---|---|
| **High** | Clear causal link between command text and friction. Signal is systematic. Fix is targeted and low-risk. |
| **Medium** | Probable causal link. Signal is likely recurring. Fix addresses root cause but may have side effects. |
| **Low** | Possible connection. Signal may be isolated. Fix is speculative — needs more data to confirm. |

The entry-level confidence is the **highest** confidence among applied amendments. If three amendments were applied at High, Medium, and Low, the entry reads `Confidence: High`.

---

## Batch Promotion Flag

When the user selects "Later" at the promotion prompt, the entry includes:

```markdown
**Batch review:** Queued
```

This flag marks the entry for future batch promotion review. Entries with this flag can be collected and reviewed in bulk — the user (or a future `/promote-batch` command) scans `.writ/refresh-log.md` for entries where `Batch review: Queued`, presents them together, and promotes or discards as a group.

---

## Examples

### Example 1: Applied locally, promotion skipped (scope not universal)

```markdown
## 2026-02-28 — /create-spec refreshed

**Source transcript:** abc123.jsonl
**Signals found:** 4 total, 2 actionable
**Amendments applied:** 2 of 2 proposed

**Changes:**
- Reduce clarification rounds — Cap follow-up questions at 2 rounds max (Confidence: High, Scope: Project-specific)
- Add monorepo context — Include workspace root detection in codebase scan (Confidence: Medium, Scope: Project-specific)

**Scope:** Local only
**Confidence:** High
**Target file:** .cursor/commands/create-spec.md
```

### Example 2: Promoted to core ("Yes" flow)

```markdown
## 2026-03-01 — /implement-story refreshed

**Source transcript:** def456.jsonl
**Signals found:** 6 total, 3 actionable
**Amendments applied:** 3 of 3 proposed

**Changes:**
- Deduplicate review feedback — Merge overlapping review comments before presenting to coder (Confidence: High, Scope: Universal)
- Preserve TDD sequencing — Explicit instruction to write test before implementation in Gate 3 (Confidence: High, Scope: Universal)
- Add retry budget display — Show "Attempt 2 of 3" in review cycle output (Confidence: Medium, Scope: Universal)

**Scope:** Promoted to core
**Confidence:** High
**Target file:** .cursor/commands/implement-story.md
**Promoted via:** https://github.com/user/writ/pull/42
```

### Example 3: User declined promotion ("No" flow)

```markdown
## 2026-03-02 — /prototype refreshed

**Source transcript:** ghi789.jsonl
**Signals found:** 3 total, 1 actionable
**Amendments applied:** 1 of 1 proposed

**Changes:**
- Expand escalation heuristic — Add "touches authentication" as a trigger for escalation to /create-spec (Confidence: High, Scope: Universal)

**Scope:** Local only
**Confidence:** High
**Target file:** .cursor/commands/prototype.md
```

### Example 4: Deferred for batch review ("Later" flow)

```markdown
## 2026-03-03 — /refresh-command refreshed

**Source transcript:** jkl012.jsonl
**Signals found:** 5 total, 2 actionable
**Amendments applied:** 2 of 2 proposed

**Changes:**
- Widen skip detection — Add "that's fine" and "ok whatever" as skip signal patterns (Confidence: High, Scope: Universal)
- Improve transcript size warning — Show estimated scan time for large transcripts (Confidence: Medium, Scope: Universal)

**Scope:** Local only
**Confidence:** High
**Target file:** .cursor/commands/refresh-command.md
**Batch review:** Queued
```

### Example 5: No amendments applied (clean transcript)

```markdown
## 2026-03-04 — /create-spec refreshed

**Source transcript:** mno345.jsonl
**Signals found:** 1 total, 0 actionable
**Amendments applied:** 0 of 0 proposed

**Changes:**
- (none)

**Not applied:**
- Token limit during codebase scan — Agent limitation, not fixable via command

**Scope:** Local only
**Confidence:** —
**Target file:** —
```

### Example 6: Partial apply (some amendments declined)

```markdown
## 2026-03-05 — /implement-story refreshed

**Source transcript:** pqr678.jsonl
**Signals found:** 7 total, 4 actionable
**Amendments applied:** 2 of 4 proposed

**Changes:**
- Strengthen Gate 2 contract — Require architect to list touched files before coding begins (Confidence: High, Scope: Universal)
- Add lint-fix auto-retry — Auto-run lint fix once before failing Gate 5 (Confidence: Medium, Scope: Universal)

**Not applied:**
- Skip visual QA when no mockups — User declined (wants visual QA to always run)
- Reduce review iterations to 2 — Low confidence, user wants more data

**Scope:** Local only
**Confidence:** High
**Target file:** .cursor/commands/implement-story.md
```
