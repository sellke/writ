# Drift Report Format Specification

> Canonical reference for `drift-log.md` — the append-only amendment record for spec drift.
> Any agent writing or parsing drift entries MUST follow this format exactly.

## Overview

When implementation deviates from spec, the deviation is recorded in `drift-log.md` rather than modifying the original spec files. This preserves the original contract while documenting how reality refined it. The drift log is **append-only** — existing entries are never modified or deleted.

**Core invariant:** `spec.md` and `spec-lite.md` are never changed by the pipeline. `drift-log.md` is the sole amendment record.

## File Location & Lifecycle

**Path:** `.writ/specs/[spec-folder]/drift-log.md`

| Event | Action |
|-------|--------|
| First drift in a spec folder | Create `drift-log.md` with header + first story section |
| Subsequent drift in same spec | Append new story section below existing content |
| Story run with no drift (`Overall Drift: None`) | No write — absence of entry signals clean implementation |
| Large deviation resolved by user | Append entry with recorded human decision |

**Atomic writes:** Write to a temporary file (e.g., `drift-log.md.tmp`) then rename to `drift-log.md`. This prevents partial writes if the process is interrupted mid-write. For appends, read existing content, concatenate new section, write full file atomically.

## File Structure

### Header (written once, on file creation)

```markdown
# Drift Log

> Spec: .writ/specs/[spec-folder]/
> Created: YYYY-MM-DD
> ⚠️ Append-only — do not modify existing entries.

---
```

The header is written exactly once when the file is created. It is never rewritten on subsequent appends.

### Story Run Section (appended per story)

Each story run that produces drift appends one section:

```markdown
## Story N: [Story Title] — Drift Report

> Run: YYYY-MM-DD
> Overall Drift: Small | Medium | Large

### Deviations

#### [DEV-XXX] [Brief description]
- **Severity:** Small | Medium | Large
- **Spec said:** [What the spec expected]
- **Implementation did:** [What actually happened]
- **Reason:** [Why the deviation occurred]
- **Resolution:** [See resolution values by severity below]
- **Spec amendment:** [Diff or description of spec change, if applicable]
```

### No-Drift Runs

When `Overall Drift: None`, **do not write to drift-log.md**. The absence of an entry is the signal. Writing "None" entries would create noise and make the log harder to scan.

## Field Reference

### Severity

| Value | Meaning |
|-------|---------|
| `Small` | Cosmetic or naming difference — spec intent fully preserved |
| `Medium` | Scope or integration impact — spec intent met, but with notable changes |
| `Large` | Fundamental deviation — spec intent NOT met or constraints violated |

### Resolution (determined by severity)

| Severity | Resolution Value | Pipeline Behavior |
|----------|-----------------|-------------------|
| `Small` | `Auto-amended` | Pipeline continues PASS |
| `Medium` | `Flagged for review` | Pipeline continues PASS with ⚠️ warning |
| `Large` | One of the following, based on user decision: | Pipeline PAUSES until resolved |
| | `Pipeline paused — accepted by user` | User chose to accept the deviation |
| | `Pipeline paused — rejected, sent back to coding agent` | User chose to reject; code revised |
| | `Pipeline paused — spec modified by user` | User updated the spec to match |

### Spec Amendment Field

| Severity | Spec Amendment |
|----------|---------------|
| `Small` | **Required.** Describe the amendment (e.g., "Rename `validateInput` → `validateRegistrationData` in spec") |
| `Medium` | **Optional.** Include if the deviation suggests a spec update; otherwise write `N/A — flagged for post-implementation review` |
| `Large` | Based on resolution: the amendment text if spec was modified, `N/A — deviation accepted as-is` if accepted, or `N/A — implementation revised to match spec` if rejected |

### DEV-ID Numbering

**Format:** `DEV-XXX` where `XXX` is a zero-padded 3-digit number.

**Scope:** Global increment within the entire `drift-log.md` file.

| Rule | Example |
|------|---------|
| First deviation ever in this spec folder | `DEV-001` |
| Second deviation in same story run | `DEV-002` |
| First deviation in a later story run | Continues from last ID (e.g., `DEV-003`) |
| IDs never reset, never reuse | Monotonically increasing across all story runs |

**To determine the next ID:** Scan existing `drift-log.md` for the highest `DEV-XXX` number. If the file doesn't exist, start at `DEV-001`.

### Date Format

**`YYYY-MM-DD`** — ISO 8601 date, consistent with spec headers (e.g., `2026-02-27`).

Used in:
- The file header `Created:` field
- Each story section `Run:` field

## Examples

### Small Deviation

```markdown
## Story 2: Spec-Healing Review Agent — Drift Report

> Run: 2026-02-27
> Overall Drift: Small

### Deviations

#### [DEV-001] Validation function renamed
- **Severity:** Small
- **Spec said:** Validation function named `validateUserInput`
- **Implementation did:** Named `validateRegistrationData` for specificity
- **Reason:** Cosmetic naming preference; behavior identical to spec intent
- **Resolution:** Auto-amended
- **Spec amendment:** Update spec references from `validateUserInput` to `validateRegistrationData`
```

### Medium Deviation

```markdown
## Story 4: Refresh Command Core — Drift Report

> Run: 2026-02-28
> Overall Drift: Medium

### Deviations

#### [DEV-003] Added zod dependency for transcript parsing
- **Severity:** Medium
- **Spec said:** Parse transcripts using built-in string matching
- **Implementation did:** Added `zod` for schema validation of parsed transcript data
- **Reason:** Scope expansion — adds external dependency not anticipated by spec; improves reliability but changes dependency footprint
- **Resolution:** Flagged for review
- **Spec amendment:** N/A — flagged for post-implementation review
```

### Large Deviation

```markdown
## Story 6: Command Overlay System — Drift Report

> Run: 2026-03-02
> Overall Drift: Large

### Deviations

#### [DEV-005] File-copy overlay instead of symlink-based system
- **Severity:** Large
- **Spec said:** Command overlay uses symlinks to reference core command files
- **Implementation did:** Copies command files into project directory, breaking link to upstream
- **Reason:** Symlink approach incompatible with Windows; fundamentally changes the update model
- **Resolution:** Pipeline paused — accepted by user
- **Spec amendment:** Update spec to document file-copy overlay model with explicit refresh step for upstream sync
```

The above shows a deviation **accepted** by the user. The two alternative Large resolutions:

**Rejected** — implementation sent back to coding agent for revision:

```markdown
#### [DEV-008] REST API replaced with GraphQL
- **Severity:** Large
- **Spec said:** Expose data via REST endpoints with JSON responses
- **Implementation did:** Built a GraphQL API with schema and resolvers
- **Reason:** Architectural approach change — other stories depend on REST endpoint signatures
- **Resolution:** Pipeline paused — rejected, sent back to coding agent
- **Spec amendment:** N/A — implementation revised to match spec
```

**Spec modified** — user updated the spec to match reality:

```markdown
#### [DEV-009] Session auth replaced with JWT
- **Severity:** Large
- **Spec said:** Use server-side sessions with httpOnly cookies
- **Implementation did:** Stateless JWT tokens with refresh token rotation
- **Reason:** Deployment target changed to serverless (no persistent session store); JWT is the practical choice
- **Resolution:** Pipeline paused — spec modified by user
- **Spec amendment:** Replace session-based auth with JWT + refresh token rotation. Update stories referencing session store to use token validation instead.
```

### Mixed Severities (Small + Medium in one run)

```markdown
## Story 5: Refresh Promotion Pipeline — Drift Report

> Run: 2026-03-01
> Overall Drift: Medium

### Deviations

#### [DEV-006] Changelog file renamed
- **Severity:** Small
- **Spec said:** Write changelog to `.writ/refresh-log.md`
- **Implementation did:** Named file `.writ/refresh-changelog.md`
- **Reason:** Cosmetic — avoids collision with potential future `refresh-log` debug output
- **Resolution:** Auto-amended
- **Spec amendment:** Update spec to reference `.writ/refresh-changelog.md`

#### [DEV-007] Added confidence threshold for auto-promotion
- **Severity:** Medium
- **Spec said:** All improvements offered for promotion regardless of confidence
- **Implementation did:** Only High-confidence improvements auto-offered; Medium/Low require explicit flag
- **Reason:** Reduces noise — Low-confidence changes were cluttering the promotion flow
- **Resolution:** Flagged for review
- **Spec amendment:** N/A — flagged for post-implementation review
```

Note: `Overall Drift` reflects the **highest** severity among all deviations. Here, Medium outranks Small.

## Complete drift-log.md Example

This shows what a `drift-log.md` looks like after three story runs across a spec:

```markdown
# Drift Log

> Spec: .writ/specs/2026-02-27-phase1-foundation/
> Created: 2026-02-27
> ⚠️ Append-only — do not modify existing entries.

---

## Story 2: Spec-Healing Review Agent — Drift Report

> Run: 2026-02-27
> Overall Drift: Small

### Deviations

#### [DEV-001] Severity classifier uses string enum instead of constants
- **Severity:** Small
- **Spec said:** Severity tiers defined as named constants (`DRIFT_SMALL`, `DRIFT_MEDIUM`, `DRIFT_LARGE`)
- **Implementation did:** Uses string literals `"Small"`, `"Medium"`, `"Large"` inline
- **Reason:** No runtime code in Phase 1 — string literals in markdown prompts are the implementation
- **Resolution:** Auto-amended
- **Spec amendment:** Remove reference to named constants; severity tiers are string values in prompt text

---

## Story 4: Refresh Command Core — Drift Report

> Run: 2026-02-28
> Overall Drift: Medium

### Deviations

#### [DEV-002] Transcript scanner reads full file instead of streaming
- **Severity:** Small
- **Spec said:** Stream-parse transcript files for memory efficiency
- **Implementation did:** Reads full `.jsonl` file into memory before parsing
- **Reason:** Transcript files are small (< 1MB typically); streaming adds complexity with no practical benefit
- **Resolution:** Auto-amended
- **Spec amendment:** Remove streaming requirement; full-file read is acceptable for Phase 1 transcript sizes

#### [DEV-003] Added pattern frequency analysis across multiple transcripts
- **Severity:** Medium
- **Spec said:** Analyze a single transcript per invocation
- **Implementation did:** When `--last` flag used, also scans the 3 most recent transcripts for recurring patterns
- **Reason:** Scope expansion — multi-transcript analysis provides stronger signal but wasn't in spec
- **Resolution:** Flagged for review
- **Spec amendment:** N/A — flagged for post-implementation review

---

## Story 6: Command Overlay System — Drift Report

> Run: 2026-03-02
> Overall Drift: Large

### Deviations

#### [DEV-004] File-copy overlay instead of symlink-based system
- **Severity:** Large
- **Spec said:** Command overlay uses symlinks to reference core command files
- **Implementation did:** Copies command files into project directory, breaking link to upstream
- **Reason:** Symlink approach incompatible with Windows; fundamentally changes the update model
- **Resolution:** Pipeline paused — accepted by user
- **Spec amendment:** Update spec to document file-copy overlay model with explicit refresh step for upstream sync

#### [DEV-005] Overlay precedence inverted
- **Severity:** Small
- **Spec said:** Core commands take precedence; overlays extend
- **Implementation did:** Local overlays take precedence; core commands serve as fallback
- **Reason:** Local-first precedence is the standard pattern (CSS cascade, PATH resolution); spec had it backwards
- **Resolution:** Auto-amended
- **Spec amendment:** Invert precedence model: local overlay > core command. Add note explaining cascade rationale.
```

## Parsing Guide (for Agents)

When reading `drift-log.md` to extract data, follow these rules:

### Extracting the Next DEV-ID

1. Scan the file for all occurrences matching the pattern `#### [DEV-(\d{3})]`
2. Find the highest number
3. Next ID = highest + 1, zero-padded to 3 digits
4. If no matches found (or file doesn't exist), start at `DEV-001`

### Extracting a Specific Story's Drift

1. Find the `## Story N:` heading that matches the target story number
2. Read from that heading to the next `---` horizontal rule (or end of file)
3. Parse deviation entries by splitting on `#### [DEV-XXX]` headings

### Determining Overall Drift Level for a Story

1. Find the `> Overall Drift:` line in the story's section
2. Value is one of: `Small`, `Medium`, `Large`

### Writing a New Section

1. Read existing file content (if file exists)
2. Scan for highest DEV-ID to determine next ID
3. Construct the new section following the story run template
4. If file doesn't exist: write header + `---` + new section
5. If file exists: append `\n---\n\n` + new section to existing content
6. Write atomically (temp file → rename)

## Validation Rules

Agents writing drift entries MUST verify before committing the write:

| Rule | Check |
|------|-------|
| **All six fields present** | Every `#### [DEV-XXX]` entry contains: Severity, Spec said, Implementation did, Reason, Resolution, Spec amendment |
| **DEV-ID is unique and sequential** | No duplicates; next ID = highest existing + 1 |
| **Severity ↔ Resolution consistency** | Small → `Auto-amended`, Medium → `Flagged for review`, Large → one of the three `Pipeline paused` variants |
| **Overall Drift = highest severity** | If any deviation is Large, overall must be `Large`; if highest is Medium, overall is `Medium` |
| **Date is valid** | `YYYY-MM-DD` format, matches the current run date |
| **Story number is correct** | `## Story N:` header references the story being implemented |
| **Small requires amendment text** | Small deviations always have concrete amendment text — never `N/A` |
| **Append-only invariant** | Existing content is never modified; new sections are only appended after `---` |
