# "What Was Built" Record Format

## Purpose

The "What Was Built" record is a **system spec** — a permanent record of what was actually implemented, appended to each completed story file. It serves as the **implementation reality** alongside the original plan, enabling:

1. **Cross-story continuity** — downstream stories know what upstream stories actually produced
2. **Drift tracking** — deviation history visible in context
3. **Historical reference** — future maintainers see decisions and tradeoffs made during implementation
4. **Audit trail** — third-party verification (review agent output) rather than self-reporting

## Source of Truth

"What Was Built" records are **sourced from review agent output** (Gate 3), not from coding agent self-reports. This ensures third-party verification and captures:

- Review-validated file changes
- Security assessment results
- Drift analysis and deviations
- Integration and boundary compliance findings

## Record Structure

The record is appended to the story file after Gate 5 (Documentation) completes. It uses the following structure:

```markdown
---

## What Was Built

**Implementation Date:** {YYYY-MM-DD}

### {Optional Context Section}

[Optional narrative context about scope overlap, discovery, or special circumstances]

### Files Created

1. **`path/to/file.ext`** ({line_count} lines)
   - Brief description of purpose
   - Key functionality or components

2. **`path/to/another.ext`** ({line_count} lines)
   - Description

### Files Modified

- **`path/to/modified.ext`** ({section_reference})
  - Summary of changes made
  - Why the changes were necessary

### Implementation Decisions

1. **Decision name** — Rationale and impact
2. **Decision name** — Context and tradeoffs

### Test Results

**Verification:** {Manual | Automated | N/A}
- ✅ Test category or acceptance criterion
- ✅ Coverage details

**Coverage:** {percentage or N/A}

### Review Outcome

**Result:** {PASS | PASS with drift note | PAUSE}

- **Iteration count:** {N} iteration(s)
- **Drift:** {None | Small | Medium | Large}
- **Security:** {Clean | Low | Medium | High risk level}
- **Boundary Compliance:** {summary from review agent}

### Deviations from Spec

[If drift analysis found deviations:]

- **[DEV-NNN] Deviation title** — Severity: {Small | Medium | Large}
  - Spec said: {expected behavior}
  - Reality: {actual implementation}
  - Resolution: {how it was handled}
  - Spec amendment: {changes to spec-lite if applicable}

[If no deviations: "None"]

### Lessons Learned (optional)

1. **Lesson title** — Insight or principle discovered
2. **Lesson title** — Process improvement or warning for future stories

### Next Story (optional)

**Story N:** {title} — {brief description of what it will build}
```

## Field Definitions

### Mandatory Fields

These fields MUST be present in every "What Was Built" record:

| Field | Source | Description | Fallback if Missing |
|-------|--------|-------------|---------------------|
| **Implementation Date** | Orchestrator | ISO 8601 date (YYYY-MM-DD) | Current date |
| **Files Created** | Review Agent → Coding Agent Output | List with descriptions | Empty list (continue with warning) |
| **Files Modified** | Review Agent → Coding Agent Output | List with change summaries | Empty list (continue with warning) |
| **Review Outcome → Result** | Review Agent | PASS / FAIL / PAUSE | "Unknown" (log error) |

### Best-Effort Fields

These fields should be included when available, but missing data should not block completion:

| Field | Source | Description | Fallback if Missing |
|-------|--------|-------------|---------------------|
| **Implementation Decisions** | Review Agent → Coding Agent Output | Key decisions section | Omit section |
| **Test Results** | Review Agent | Test coverage and verification approach | "Verification: N/A" |
| **Review Outcome → Iteration count** | Orchestrator | Number of review loops | "1 iteration" |
| **Review Outcome → Drift** | Review Agent → Drift Analysis | None / Small / Medium / Large | "None" |
| **Review Outcome → Security** | Review Agent → Security Assessment | Risk level | "Not assessed" |
| **Review Outcome → Boundary Compliance** | Review Agent | Compliance summary | Omit if no boundary map |
| **Deviations from Spec** | Review Agent → Drift Analysis | List of DEV-IDs with details | "None" or empty section |
| **Lessons Learned** | Review Agent or manual | Insights from implementation | Omit section (optional) |

### Optional Context Sections

Additional freeform sections may be added for special circumstances:

- **Scope Overlap Discovery** — when stories overlap unexpectedly
- **Architecture Changes** — when fundamental approach changed
- **Blocked State Resolution** — when coding or testing agent hit iteration caps
- **Manual Intervention** — when human input was required

## Parsing Review Agent Output

The orchestrator extracts "What Was Built" data from the review agent's structured markdown output. Parse defensively:

### Files Created/Modified

**Source:** Review Agent → Coding Agent Output summary, or direct file inspection

**Extraction:**
1. Look for `### Coding Agent Output` or similar section
2. Parse `### Files Created` and `### Files Modified` sections
3. Extract file paths (in backticks or code blocks) and descriptions
4. If section missing, run `git diff --name-status` to infer files

**Validation:**
- At least one file should be present (created or modified)
- If empty, log warning: `⚠️ "What Was Built" record incomplete — no files found`
- Continue with empty lists

### Implementation Decisions

**Source:** Review Agent → Coding Agent Output → `### Implementation Decisions`

**Extraction:**
1. Look for the section in coding agent output
2. Parse list items or paragraphs
3. Clean up formatting

**Validation:**
- Optional field
- If missing, omit section entirely (don't write "None")

### Test Results

**Source:** Review Agent → `### Test Coverage` and Gate 4 (Testing Agent) results

**Extraction:**
1. Parse Test Coverage section for coverage percentages
2. Extract verification approach (manual/automated)
3. List passing test categories

**Validation:**
- If missing, write: `**Verification:** N/A`
- If partial, use available data (e.g., coverage without test list)

### Review Outcome

**Source:** Review Agent → multiple sections

**Extraction:**
1. **Result:** Parse `### REVIEW_RESULT: [PASS/FAIL/PAUSE]` header
2. **Drift:** Parse `### Drift Analysis → **Overall Drift:** [level]`
3. **Security:** Parse `### Security Assessment → **Risk Level:** [level]`
4. **Boundary Compliance:** Parse `### Boundary Compliance → **Summary:**` line
5. **Iteration count:** Track in orchestrator state across Gate 3 loops

**Validation:**
- Result is MANDATORY — if missing, log error and use "Unknown"
- All other fields are best-effort
- If Drift section missing, use "None"
- If Security section missing, use "Not assessed"

### Deviations from Spec (Drift)

**Source:** Review Agent → `### Drift Analysis`

**Extraction:**
1. Look for deviation entries: `#### [DEV-NNN] Title`
2. Parse fields: Severity, Spec said, Implementation did, Reason, Resolution
3. Preserve DEV-ID numbering for continuity with drift-log.md

**Validation:**
- If "Overall Drift: None", write "None" in Deviations section
- If drift level > None but no deviation entries found, log warning and write "See drift-log.md"
- Preserve all deviation entries as-is (don't summarize)

## Size and Context Budget

"What Was Built" records are appended AFTER story completion, so they don't bloat story files during planning. However:

- **Target size:** 50-150 lines per record (typical)
- **Maximum size:** No hard limit, but records >200 lines should be reviewed for verbosity
- **Context budget impact:** When loading dependency records (Step 2), apply truncation:
  - Load full record by default
  - If record exceeds 1000 lines, truncate to: Files → Decisions → Tests → Review notes → Drift (in priority order)
  - Log truncation: `⚠️ Truncated Story N "What Was Built" record (1234 → 1000 lines)`

## Cross-Story Continuity (Step 2)

When a story depends on completed upstream stories, the orchestrator loads "What Was Built" records and passes them to the coding agent:

**Process:**
1. Parse story dependencies from `## Dependencies:` or `spec.md` dependency graph
2. For each dependency story, check for `## What Was Built` section
3. If present, extract full section content
4. Apply size limits (1000 lines per record)
5. Pass to coding agent in prompt:

```
## Dependency Context

**Story 1 completed — "What Was Built":**
{full record from story-1.md}

**Story 2 completed — "What Was Built":**
{full record from story-2.md}
```

**Fallback behavior:**
- If dependency story has no "What Was Built" section yet (incomplete), log:
  ```
  ⚠️ Story 1 depends on Story 0 (not yet complete).
  Proceeding anyway — some integration points may be unavailable.
  ```
- If dependency story file not found, log error and continue
- ONLY load direct dependencies (not transitive)

## Backward Compatibility

For stories completed before this feature was implemented:

- If a dependency story has no `## What Was Built` section, gracefully skip
- Manual "What Was Built" sections (like Story 2's example) are valid and should be parsed
- Future stories will have auto-generated records

## Validation Warnings (Non-Blocking)

The orchestrator logs validation warnings but does NOT block story completion:

| Warning | Condition | Action |
|---------|-----------|--------|
| `⚠️ "What Was Built" record incomplete — no files found` | No files created or modified | Log, continue with empty lists |
| `⚠️ Review agent output missing required section: {section}` | Expected section not found | Log, use fallback value |
| `⚠️ Unable to parse {field} — using fallback` | Parse error on best-effort field | Log, omit field |
| `⚠️ Drift level is {level} but no deviation entries found` | Mismatch between level and details | Log, write "See drift-log.md" |
| `⚠️ Truncated Story N "What Was Built" record ({from} → {to} lines)` | Record exceeds context budget | Log, include truncated version |

## Example Record

See `.writ/specs/2026-03-27-context-engine/user-stories/story-2-agent-specific-spec-views.md` lines 73-168 for a complete example of a manually-created "What Was Built" record that follows this format.

## Related Documentation

- **Drift Analysis Format:** `.writ/docs/drift-report-format.md`
- **Review Agent Output:** `agents/review-agent.md` — structured output sections
- **Spec-Lite Format:** `.writ/docs/spec-lite-format-verification.md`
