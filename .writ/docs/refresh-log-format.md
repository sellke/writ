# Refresh-Log Format Specification

> Canonical reference for `.writ/refresh-log.md` entries.
> Used by `/refresh-command` (Phase 3: Propose Amendments + Phase 4: Apply & Log).

---

## File Location & Lifecycle

**Path:** `.writ/refresh-log.md` — this is the single canonical path. There is no
`.writ/state/refresh-log.md` variant; the log is a committed audit trail, not
ephemeral state.

**Creation:** `/refresh-command` creates the file on first run if it doesn't exist. The file opens with a single header:

```markdown
# Writ Refresh Log
```

**Append-only:** New entries are appended below the header. Entries are never
modified after writing. The log is the canonical, auditable record of every
refresh run — applied amendments with their evidence, and rejected candidates with
their reason.

**Ordering:** Most recent entry at the bottom (natural append). Readers who want reverse-chronological order read from the end.

---

## The Evidence Contract

Writ's learning loop is **evidence-bound**: every applied amendment must be
justified, and every unjustifiable proposal must be visibly rejected. The log is
where that "kept vs. discarded" decision becomes auditable.

- **Every applied amendment cites evidence** — a transcript ID/path, a short
  observable signal, and the affected command section.
- **Unevidenced proposals are rejected**, not applied, and the rejection is
  recorded with reason `no evidence`.
- **Eval-failing proposals are rejected** with reason `eval failed`.
- **Privacy (Prime Directive):** evidence references transcript IDs/paths and
  short observable signals only — never chain-of-thought, prompts, or verbatim
  private transcript bodies. Transcript bodies live outside the repository and are
  never committed.

### `LEARNING_CONTRACT_SINCE` grandfathering

The evidence contract takes effect on **`LEARNING_CONTRACT_SINCE = 2026-07-11`**
(the day after this feature's spec was created). Any log entry dated strictly
**before** that date is **grandfathered**: it predates the contract and is not
retroactively required to carry an Evidence block. Entries dated on or after
`LEARNING_CONTRACT_SINCE` must conform to the schema below. The fixture-driven
eval check (`scripts/eval-refresh-evidence.py`) honors this date so pre-contract
history never fails CI.

---

## Entry Structure

Every `/refresh-command` completion writes exactly one entry, regardless of outcome.

```markdown
## YYYY-MM-DD — /[command] refreshed

**Signals found:** [N] total, [M] actionable
**Amendments applied:** [K] of [M] proposed

**Changes:**
- [Amendment title] (Confidence: High/Medium/Low)
  **Evidence:**
  - Transcript: agent-transcripts/<session-uuid>/<session-uuid>.jsonl
  - Observable signal: "[short factual quote of a correction/retry/override/error]"
  - Affected section: commands/[command].md → "[real section heading]"

**Rejected:**
- [Amendment title] — reason: no evidence
- [Amendment title] — reason: eval failed

**Scope:** Local only
**Target file:** commands/[command].md
```

### Field Reference

| Field | Format | Description |
|---|---|---|
| **Date** | `YYYY-MM-DD` | Date the refresh was performed |
| **Command** | `/[command-name]` | The Writ command that was refreshed |
| **Signals found** | `N total, M actionable` | Signal counts from Phase 2 |
| **Amendments applied** | `K of M proposed` | How many proposals passed the evidence gate and were applied |
| **Changes** | Bulleted list | Each applied amendment with title, confidence, and its **Evidence** block |
| **Evidence** | Structured 3-part block | Transcript ID/path + short observable signal + affected section. **Mandatory** for every applied amendment. |
| **Rejected** | Bulleted list | Each rejected candidate with a reason token (`no evidence` / `eval failed`). Omit the section if nothing was rejected. |
| **Scope** | `Local only` | Amendments are applied to the project's local command copy. |
| **Target file** | `commands/[command].md` | The command file that was modified. |

### The Evidence block (mandatory for applied amendments)

Each applied amendment carries an `**Evidence:**` block with exactly three parts:

| Part | Format | Rule |
|---|---|---|
| **Transcript** | `agent-transcripts/<uuid>/<uuid>.jsonl` (or `.../subagents/<sub-uuid>.jsonl`), or a transcript ID | Identifies the session the signal came from. The file may be absent on this machine — the ID citation still stands; a body is never required. |
| **Observable signal** | A single short quoted line | A factual quote of a correction, retry, override, or error. **Never** reasoning, a prompt, or a private body. |
| **Affected section** | `commands/[command].md → "[section]"` | Anchors the change to a real section of the target command file. |

### Rejection reasons

| Reason token | Meaning |
|---|---|
| `no evidence` | The proposal could not cite a transcript ID/path plus a short observable signal. Rejected before any file write. |
| `eval failed` | The proposal was evidenced but failed the pre-merge eval gate (`bash scripts/eval.sh --check=refresh-evidence`, plus the structural Tier 2 check for high-traffic commands). |

### The no-op exemption

A run that reviews a command and applies **zero** amendments is a valid outcome and
is **exempt** from the evidence requirement — there is nothing to justify. Record
the review without an Evidence block:

```markdown
## YYYY-MM-DD — /[command] reviewed — no changes

**Signals found:** 1 total, 0 actionable
**Amendments applied:** 0 of 0 proposed

**Scope:** Local only
**Target file:** —
```

---

## Confidence Values

| Value | Meaning |
|---|---|
| **High** | Clear causal link between command text and friction. Signal is systematic. Fix is targeted and low-risk. |
| **Medium** | Probable causal link. Signal is likely recurring. Fix addresses root cause but may have side effects. |
| **Low** | Possible connection. Signal may be isolated. Fix is speculative — needs more data to confirm. |

---

## Not implemented (do not use)

Earlier drafts of this doc described mechanics the command does **not** implement.
They are removed to keep the doc honest:

- **Promotion-to-core flow** (`**Scope:** Promoted to core`, `**Promoted via:**`,
  `**Promotion fallback:**`) — `/refresh-command` is local-first; it does not open
  upstream PRs. Scope is always `Local only`.
- **Batch review** (`**Batch review:** Queued`, `--batch`) — there is no batch
  promotion queue or `--batch` invocation.

If any of these are ever implemented, restore them here **and** in
`commands/refresh-command.md` together — no aspirational drift.

---

## Examples

### Example 1: Applied with cited evidence

```markdown
## 2026-07-11 — /create-spec refreshed

**Signals found:** 4 total, 2 actionable
**Amendments applied:** 1 of 2 proposed

**Changes:**
- Detect monorepo workspace root during codebase scan (Confidence: High)
  **Evidence:**
  - Transcript: agent-transcripts/session-uuid/session-uuid.jsonl
  - Observable signal: "user re-ran /create-spec after the scan skipped the monorepo root"
  - Affected section: commands/create-spec.md → "Phase 2: Codebase Scan"

**Scope:** Local only
**Target file:** commands/create-spec.md
```

### Example 2: Rejected for lacking evidence

```markdown
## 2026-07-11 — /prototype refreshed

**Signals found:** 3 total, 1 actionable
**Amendments applied:** 0 of 1 proposed

**Rejected:**
- Add "touches authentication" escalation trigger — reason: no evidence

**Scope:** Local only
**Target file:** commands/prototype.md
```

### Example 3: Reviewed, no amendments (exempt)

```markdown
## 2026-07-11 — /create-spec reviewed — no changes

**Signals found:** 1 total, 0 actionable
**Amendments applied:** 0 of 0 proposed

**Scope:** Local only
**Target file:** —
```
