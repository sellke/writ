---
name: what-was-built-authoring
description: "Extract implementation facts from agent output and format them into a What Was Built record."
disable-model-invocation: true
status: candidate
---

# What Was Built Authoring

## Purpose

Capture **implementation reality** — what was actually created, changed,
decided, tested and deviated from — as a durable record appended to the work
item, so downstream work builds on facts rather than the plan. Two halves:
extracting the data defensively from whatever output exists, and formatting it
into the record's fixed shape.

> **Format reference:** `.writ/docs/what-was-built-format.md` — the authority on
> the record's conventions, including the `> **Reverted:**` banner.

**The single governing rule: never block completion on incomplete data.
Partial records are better than no records.** Every extraction below has a
fallback for exactly that reason.

## When to Use

- Closing out a unit of work whose successors will need to know what it
  produced.
- Whenever review or test output exists that will otherwise be discarded when
  the transcript ends.
- Also on reduced runs where no review happened — a smaller record is still
  written (see *Minimal record*).

## How to Apply

### 1. Extract — five sources, three failure semantics

**Files Created/Modified — mandatory.** Parse the `### Files Created` and
`### Files Modified` sections of the implementation output; extract file paths
(in backticks) and descriptions. *Fallback:* if the sections are missing, run
`git diff --name-status` against the branch start. *Validation:* if no files are
found, log `⚠️ "What Was Built" record incomplete — no files found` and continue
with empty lists.

**Implementation Decisions — best-effort.** Parse the
`### Implementation Decisions` list items or paragraphs. *Fallback:* omit the
section from the final record.

**Test Results — best-effort.** Parse `### Test Coverage` and any testing
results available; extract coverage percentages and the verification approach.
*Fallback:* `**Verification:** N/A`.

**Review Outcome — mandatory result, best-effort detail.**
- **Result** (mandatory): parse `### REVIEW_RESULT: [PASS/FAIL/PAUSE]`. If it is
  missing, log an error and use `"Unknown"`.
- **Drift** (best-effort): `### Drift Analysis → **Overall Drift:** [level]`.
- **Security** (best-effort): `### Security Assessment → **Risk Level:** [level]`.
- **Boundary Compliance** (best-effort): the
  `### Boundary Compliance → **Summary:**` line.
- **Iteration count**: tracked by the caller — the number of review loops.
- *Fallbacks* for missing best-effort fields: `"None"` / `"Not assessed"` / omit.

**Deviations from Spec — best-effort.** Parse the `#### [DEV-NNN]` entries under
`### Drift Analysis` with all their fields, **preserving DEV-ID numbering**.
*Fallback:* if overall drift is "None", use `"None"`.

Hold the extracted fields until the record is written: extraction and writing
are separate moments, and later results (test results in particular) update the
held data before it is formatted.

### 2. Format

```markdown
---

## What Was Built

**Implementation Date:** {implementation_date}

### Files Created

{For each file created:}
1. **`{file.path}`** ({file.line_count} lines)
   - {file.description}

{If empty: "[None created]"}

### Files Modified

{For each file modified:}
- **`{file.path}`** ({file.section_reference})
  - {file.changes}

{If empty: "[None modified]"}

### Implementation Decisions

{For each decision:}
{N}. **{decision.title}** — {decision.rationale}

{If empty: omit section entirely — don't write "None"}

### Test Results

**Verification:** {test_results.verification}
{If coverage present: "**Coverage:** {coverage}%"}
{For each detail:}
- ✅ {detail}

### Review Outcome

**Result:** {review_outcome.result}

- **Iteration count:** {review_outcome.iteration_count} iteration(s)
- **Drift:** {review_outcome.drift}
- **Security:** {review_outcome.security}
{If boundary_compliance present: "- **Boundary Compliance:** {boundary_compliance}"}

### Deviations from Spec

{If deviations is empty or drift is "None":}
None

{Otherwise, for each deviation:}
- **[{dev.id}] {dev.title}** — Severity: {dev.severity}
  - Spec said: {dev.spec_said}
  - Reality: {dev.implementation_did}
  - Resolution: {dev.resolution}
  {If spec_amendment present: "- Spec amendment: {dev.spec_amendment}"}
```

Three empty-state rules differ deliberately and must not be harmonized: Files
Created/Modified print `[None created]` / `[None modified]`; Implementation
Decisions is **omitted entirely** rather than printing "None"; Deviations prints
the word `None`.

### 3. Append

1. Open the work item's file for append.
2. Add the separator `\n---\n\n`.
3. Add the formatted content.
4. Save.

Append — never rewrite the file around the record.

### Minimal record (reduced runs, no review data)

When no review ran, no extracted data exists. Construct a smaller record from
the implementation and testing output. It is a **second template**, not a
degraded copy of the first — its own banner, its own section list:

```markdown
## What Was Built

> Note: Review skipped (`--quick` mode) — record sourced from coding and testing agents only

**Implementation Date:** {current_date}

### Files Created
{From coding agent output}

### Files Modified
{From coding agent output}

### Test Results
{From testing agent output}
```

### Graceful degradation

- **Incomplete extraction:** already handled by the validation warnings and
  fallback values above — use the partial data, log the warnings, continue.
- **Missing test results:** if testing was skipped or failed, use
  `**Verification:** N/A`.
- **Any other gap:** write the record anyway. **The work must NEVER be blocked
  from completing because the record is incomplete.**
