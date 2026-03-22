# Verify Spec Command (verify-spec)

## Overview

Fast **metadata diagnostic** for Writ specs. Confirms story files, README tracking, statuses, deliverables, dependencies, and contract alignment are consistent. **Default mode auto-fixes** everything that can be repaired safely, then reports what still needs human judgment.

This command is **not a pipeline gate** — run it when you suspect spec drift, like a linter. Release-time tests, build verification, and changelog work live in `/release`.

## Modes

| Invocation | Mode | Behavior |
|---|---|---|
| `/verify-spec` | Default | Select spec (if needed); run checks 1–7; **auto-fix** fixable issues; report the rest — no confirmation prompt |
| `/verify-spec --check` | Read-only | Same checks; report only; no file changes |
| `/verify-spec --fix` | Fix spec-lite | Run Check 7; if divergence found, fully regenerate `spec-lite.md` from `spec.md` |
| `/verify-spec --spec [path]` | Targeted | Verify the spec at path (folder under `.writ/specs/` or path to `spec.md`) |
| `/verify-spec --all` | All specs | Run the full diagnostic for every spec under `.writ/specs/` |

## Command Process

### Phase 1: Spec Discovery & Loading

#### Step 1.1: Select Specification

**If `/verify-spec --spec [path]`:** Resolve to a spec folder (directory containing `spec.md`). Skip selection.

**If `/verify-spec --all`:** Build the list of all `.writ/specs/*/` folders that contain `spec.md`. Process each sequentially (or report per spec); aggregate a summary at the end.

**If not specified:**
```
AskQuestion({
  title: "Spec Verification",
  questions: [
    {
      id: "spec",
      prompt: "Which specification to verify?",
      options: [
        // Dynamically populated from .writ/specs/
        { id: "latest", label: "[DATE]-[name] (most recent)" },
        { id: "spec_2", label: "[DATE]-[name]" },
        { id: "all", label: "Verify ALL specifications" }
      ]
    }
  ]
})
```
Choosing **all** here is equivalent to `--all`.

#### Step 1.2: Load Everything

```
1. Read spec.md (contract, deliverables checklist)
2. Read spec-lite.md (summary) if present
3. Read user-stories/README.md (progress table)
4. Read ALL user-stories/story-N-*.md files
5. Read sub-specs/ (technical-spec, api-spec, etc.) if present
6. Scan git log for commits referencing this spec (optional context for Check 6)
```

Build complete data model:
```json
{
  "spec": {
    "name": "feature-name",
    "date": "2026-02-22",
    "status": "Planning",
    "deliverables": [
      { "text": "Auth middleware", "checked": false, "fileExists": true }
    ]
  },
  "readme": {
    "stories": [
      { "number": 1, "title": "Auth", "status": "Completed", "tasks": "5/5" }
    ],
    "totalProgress": "5/15"
  },
  "storyFiles": [
    {
      "file": "story-1-auth.md",
      "number": 1,
      "status": "Completed ✅",
      "tasks": { "total": 5, "checked": 5 },
      "acceptanceCriteria": { "total": 4, "checked": 4 },
      "definitionOfDone": { "total": 5, "checked": 5 },
      "dependencies": ["None"]
    }
  ]
}
```

---

### Phase 2: Verification Checks

Run checks **1–7**. Collect every finding before reporting — do not stop at the first issue.

**Default mode:** After reporting, apply all auto-fixes (Phase 4) unless contradicted by `--check`.

**`--check` mode:** Report only; Phase 4 does not run.

**`--fix` mode:** Run Check 7 and, if divergence is found, fully regenerate `spec-lite.md` from `spec.md` (see Check 7 and Phase 4 below).

---

#### Check 1: Story File Integrity

**1a. Orphan detection — files without README entries:**
```
For each story-N-*.md file in user-stories/:
  Does README.md reference this story? → if not, flag as orphan
```

**1b. Phantom detection — README entries without files:**
```
For each story row in README.md table:
  Does a corresponding story-N-*.md file exist? → if not, flag as phantom
```

**1c. Status header present:**
```
Every story file must have:
  > **Status:** [Not Started | In Progress | Completed ✅]
If missing or malformed → flag
```

**1d. Required sections present:**
```
Every story file must have:
  - User Story (As a / I want to / So that)
  - Acceptance Criteria
  - Implementation Tasks
  - Definition of Done
If any section missing → flag
```

---

#### Check 2: Status Consistency

**2a. README ↔ story file status sync:**
```
For each story:
  README says "Completed" but file says "In Progress"? → discrepancy
  README says "Not Started" but file says "Completed"? → discrepancy
```

**2b. Task count accuracy:**
```
For each story:
  README says "5/7 tasks" but file has 6 total tasks with 4 checked? → mismatch
  Count actual - [ ] and - [x] in Implementation Tasks section
```

**2c. Total progress accuracy:**
```
README footer says "Total: 15/20 tasks (75%)"
Sum actual checked tasks across all stories
If sum doesn't match → flag
```

---

#### Check 3: Completion Integrity

**3a. Acceptance criteria verification (for "Completed" stories):**
```
If story status is "Completed ✅":
  Are ALL acceptance criteria checked? (- [x] Given...)
  Any unchecked criteria → flag as false completion
```

**3b. Definition of Done verification (for "Completed" stories):**
```
If story status is "Completed ✅":
  Is the entire Definition of Done section checked?
  Any unchecked items → flag as incomplete DoD
```

**3c. Task completion (for "Completed" stories):**
```
If story status is "Completed ✅":
  Are ALL implementation tasks checked? (- [x] N.X ...)
  Any unchecked tasks → flag
```

**3d. Premature status (for "In Progress" or "Not Started" stories):**
```
If story status is "Not Started" but has checked tasks → should be "In Progress"
If story status is "In Progress" but all tasks checked → should be "Completed"
```

---

#### Check 4: Dependency Validation

**4a. Dependency satisfaction:**
```
For each story with dependencies:
  Are all dependency stories "Completed ✅"?
  If story is "Completed" but a dependency is not → flag ordering violation
```

**4b. Circular dependencies:**
```
Build dependency graph
Check for cycles → flag if found
```

**4c. Missing dependency declarations (heuristic):**
```
Cross-reference with spec.md and sub-specs/technical-spec.md
Flag if obvious dependencies are undeclared
```

> Checks **4** is **report-only** in both default and `--check` — dependency fixes need human judgment.

---

#### Check 5: Deliverables Checklist (spec.md)

**5a. Deliverable file existence:**
```
For each deliverable in spec.md checklist:
  Extract file paths mentioned
  Do the files exist? → if not, flag
  Is the checklist item checked but file doesn't exist? → flag as false deliverable
  Is the file present but checklist item unchecked? → flag as unsync'd
```

**5b. Spec status header:**
```
If ALL stories completed AND all deliverables checked:
  spec.md status should be "Complete" or "Completed"
  If not → flag
```

---

#### Check 6: Spec Contract vs Implementation

**Drift detection — does the built thing match the specced thing?**

```
Read spec.md "Contract Summary" section
Read spec.md "Scope Boundaries" → Included / Excluded lists

For each "Included" item:
  Is there evidence of implementation? (files, tests, stories covering it)
  If not → flag as unimplemented scope

For each "Excluded" item:
  Is there implementation that shouldn't be there? (scope creep — heuristic)
```

> Check **6** is **report-only** in both modes — heuristic; may have false positives.

---

#### Check 7: Spec-Lite Integrity

**Purpose:** Confirm that `spec-lite.md` accurately reflects the authoritative `spec.md`. `implement-story` may auto-amend `spec-lite.md` on Small drift without touching `spec.md` — over time, the derivative can silently diverge from the contract.

**Skip** if `spec-lite.md` does not exist (not all specs have one — no flag, just skip).

**Section mapping — compare these pairs:**

| spec-lite.md section | spec.md section |
|---|---|
| `## What We're Building` (or `## What`) | `## Contract Summary` (or equivalent top-level summary) |
| Key Constraints (inline bullets or `## Key Constraints`) | `## Business Rules` + constraint bullets in contract |
| Success Criteria (`## Success Criteria`) | `## Success Criteria (Phase A)` or `## Success Criteria` |
| Files in Scope (`## Files in Scope`) | `## Scope Boundaries` → Included list |

**Heading normalization:** If headings differ slightly (e.g. "What We're Building" vs "What"), match by semantic intent, not exact string. If no clear match exists, skip that pair and note it in the report.

**Material divergence — flag when:**
```
For each mapped section pair:
  Compare the substantive content (ignore formatting differences, bullet style, whitespace)
  Flag as DIVERGED if:
    - A key fact, constraint, or deliverable in spec.md is absent from spec-lite.md
    - spec-lite.md describes something not in spec.md (scope creep in the derivative)
    - Success criteria list differs materially (added, removed, or changed items)
    - Files in Scope lists differ by more than cosmetic renaming
  
  Do NOT flag:
    - Shorter phrasing that preserves intent
    - Formatting differences (bold vs plain, bullets vs prose)
    - spec-lite is condensed — brevity is expected; absence of detail is not divergence
```

**Report shape for Check 7:**
```
7. Spec-lite integrity     ✅       spec-lite aligned with spec.md
   — or —
7. Spec-lite integrity     ❌       Divergence in 2 sections:
                                    • Success Criteria: 2 items in spec.md missing from spec-lite
                                    • Files in Scope: spec-lite lists commands/foo.md (not in spec.md)
```

**`--fix` behavior:** When `--fix` is passed (or via default mode auto-fix trigger — see Phase 4), fully regenerate `spec-lite.md` from `spec.md`:
- Read `spec.md` in full
- Produce a condensed version (~100 lines max) covering: What We're Building, Key Constraints, Success Criteria, Files in Scope, and any Phase/dependency context
- Prepend a regeneration marker at the top: `> Regenerated from spec.md on YYYY-MM-DD`
- Write the full file — do not patch individual sections

> Check **7** divergence findings are **auto-fixable** in default mode (triggers regeneration). In `--check` mode: report only, no regeneration. In `--fix` mode: runs Check 7 and regenerates if diverged.

---

### Phase 3: Verification Report

Present all findings in a structured report (console). The table always has **seven** checks — no "Skipped" rows (except Check 7 when `spec-lite.md` is absent), no alternate layouts.

```
🔍 Spec Verification Report: 2026-02-22-feature-name

═══════════════════════════════════════════════════
 CHECK                           STATUS   FINDINGS
═══════════════════════════════════════════════════
 1. Story file integrity         ✅       All clean
 2. Status consistency           ❌       2 discrepancies
 3. Completion integrity         ⚠️       1 unchecked DoD item
 4. Dependency validation        ✅       All satisfied
 5. Deliverables checklist       ❌       3 items unsync'd
 6. Contract vs implementation   ✅       All scope items implemented
 7. Spec-lite integrity          ✅       spec-lite aligned with spec.md
═══════════════════════════════════════════════════

Overall: ⚠️ 4 issues found (2 auto-fixable, 2 need attention)
```

If `spec-lite.md` does not exist, omit row 7 from the table and note: `(Check 7 skipped — no spec-lite.md found)`.

**Findings detail:**

```
── Auto-Fixable ──────────────────────────────────

[FIX-1] README status mismatch
  Story 2: file says "Completed ✅", README says "In Progress"
  → Updating README (default mode only)

── Needs Attention ───────────────────────────────

[WARN-1] Unchecked Definition of Done
  Story 2: "Documentation updated" is unchecked
  → Confirm manually, then check it off if accurate.
```

**`--check` mode:** Stop after this phase (no auto-fix).

**Default mode:** Continue to Phase 4 automatically — **do not** prompt for fix confirmation.

---

### Phase 4: Auto-Fix (default mode only)

#### 4.1: Sync README with Story Files

- Update status column to match story file headers
- Update task counts to match actual checked/total counts
- Recalculate total progress
- Update Quick Links with completion markers when applicable

#### 4.2: Sync Deliverables Checklist

- Check off deliverables whose files exist
- Uncheck deliverables whose files are missing (with warning)

#### 4.3: Fix Status Headers

- Stories with all tasks done → "Completed ✅"
- Stories with some tasks done → "In Progress"
- Stories with no tasks done → "Not Started"
- Spec with all stories done → "Complete"

#### 4.4: Regenerate Spec-Lite (Check 7 finding or `--fix` flag)

If Check 7 flagged divergence **and** mode is default (not `--check`), or if `--fix` was passed:

1. Read `spec.md` in full — this is the source of truth
2. Produce a condensed `spec-lite.md` (~100 lines max) covering:
   - `## What We're Building` — condensed Contract Summary
   - `## Key Constraints` — business rules and hard limits
   - `## Success Criteria` — all success criteria items
   - `## Files in Scope` — Included list from Scope Boundaries
   - Phase/dependency context if applicable
3. Prepend regeneration marker: `> Regenerated from spec.md on YYYY-MM-DD`
4. Write the full file — always a complete replacement, never a partial patch

`spec.md` is never modified by this step — it is always the source, never the target.

---

### Phase 5: Verification Report File

Write to `.writ/specs/[spec-folder]/verification-YYYY-MM-DD.md`:

```markdown
# Verification Report: [Feature Name]

> **Date:** YYYY-MM-DD
> **Spec:** [spec folder]
> **Mode:** default | check
> **Result:** ✅ Passed / ⚠️ Passed with warnings / ❌ Failed

## Summary

| Check | Status | Details |
|-------|--------|---------|
| Story file integrity | ✅ | N stories, all well-formed |
| Status consistency | ✅ | README in sync (auto-fixed) |
| Completion integrity | ✅ | All criteria and DoD checked |
| Dependency validation | ✅ | All dependencies satisfied |
| Deliverables checklist | ✅ | N/N deliverables verified |
| Contract alignment | ✅ | No scope drift flagged |
| Spec-lite integrity | ✅ | spec-lite aligned with spec.md |

## Stories
| # | Title | Status | Tasks | Criteria | DoD |
|---|-------|--------|-------|----------|-----|
| 1 | Auth | ✅ | 5/5 | 4/4 | 5/5 |
| 2 | API | ✅ | 6/6 | 3/3 | 5/5 |

## Issues Found & Resolved
- [FIX-1] README status sync (auto-fixed)
- [FIX-2] Task count correction (auto-fixed)

## Outstanding Warnings
- [WARN-1] Heuristic: possible scope gap in "Included" list (see Check 6)

## Notes
Diagnostic only. Use `/release` when you are ready to publish; it runs build checks, conditional tests, and changelog work.
```

**Completion message (default):**
```
✅ Spec verification complete.

Checks 1–7 evaluated; fixable metadata updated.
See report: .writ/specs/[spec-folder]/verification-YYYY-MM-DD.md
```

**Completion message (`--check`):**
```
✅ Spec verification (--check) complete — no files modified.
```

---

## Integration with Writ

| Command | Relationship |
|---------|-------------|
| `/implement-spec` | May leave spec metadata noisy after bulk story work — `/verify-spec` cleans it up |
| `/ship` | Optionally runs a **subset** of these checks (1–3) inline when opening a PR |
| `/release` | Runs the **full** checks 1–6 again as part of its **internal** release gate (self-sufficient) — same logic, different entry point |
| `/security-audit` | Complementary — verify-spec checks spec structure; security-audit checks safety |
| `/status` | Quick overview; verify-spec is the deep metadata pass |

**Recommended posture:** `/verify-spec` is **optional**. Many sessions go straight `/ship` → `/release`. Run `/verify-spec` when you want a dedicated hygiene pass without releasing.

**Boundary principle:** `/verify-spec` owns **spec metadata integrity** only. `/release` owns **tests, build verification, and changelog** for publishing.
