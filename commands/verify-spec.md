# Verify Spec Command (verify-spec)

## Overview

Fast **metadata diagnostic** for Writ specs. Confirms story files, README tracking, statuses, deliverables, dependencies, and contract alignment are consistent. **Default mode auto-fixes** everything that can be repaired safely, then reports what still needs human judgment.

This command is **not a pipeline gate** — run it when you suspect spec drift, like a linter. Release-time tests, build verification, and changelog work live in `/release`.

## Modes

| Invocation | Mode | Behavior |
|---|---|---|
| `/verify-spec` | Default | Select spec (if needed); run checks 1–8; **auto-fix** fixable issues; report the rest — no confirmation prompt |
| `/verify-spec --check` | Read-only | Same checks; report only; no file changes |
| `/verify-spec --fix` | Fix spec-lite | Run Check 7; if divergence found, fully regenerate `spec-lite.md` from `spec.md` |
| `/verify-spec --spec [path]` | Targeted | Verify the spec at path (folder under `.writ/specs/` or path to `spec.md`) |
| `/verify-spec --all` | All specs | Run the full diagnostic for every spec under `.writ/specs/` |
| `/verify-spec --product` | Product docs | Run the **Product Consistency** check set (its own ~4 checks — **not** spec checks 1–8) over `.writ/product/` + `.writ/context.md`; hybrid auto-fix (regenerate derivatives) / report-only (authoritative divergence) |

> **`--product` is a distinct check set, not spec checks pointed at product docs.** Default `/verify-spec` (checks 1–8) answers "is this *spec* internally consistent?"; `--product` answers "is the *product layer* internally consistent and true to reality?" The two do not share checks. See [Product Consistency Checks](#product-consistency-checks---product) below. `--product` is the consistency lint (the *before*); its revision counterpart is `/plan-product --reconcile` (the *after*).

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

Run checks **1–8**. Collect every finding before reporting — do not stop at the first issue.

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

**4d. Cross-spec dependency validation:**

This validates the spec-level `> **Dependencies:** [spec-folder-id, ...]` header — a
**separate contract** from the story-level checks in 4a–4c. Existing story dependency validation is unchanged; the two graphs stay distinct.

```
For the reachable cross-spec graph (this spec + every spec it references):
  Parse each spec's `> **Dependencies:** [...]` header (a legacy spec with no
    header is treated as `[]`; a header that is not the bracket form is malformed)
  Flag as blocking:
    - malformed header                 → malformed_dependencies
    - missing reference (no such folder under .writ/specs/) → missing_reference (name it)
    - self-reference (spec lists itself) → self_reference
    - duplicate entry in one list       → duplicate_reference (dedupe preserves order)
    - cross-spec cycle                  → dependency_cycle (print the exact path)
```

The executable reference for this contract is `scripts/spec-deps.py validate`. Invalid
explicit metadata is **blocking**; shared-file or prose overlap can only *warn* about a
potentially missing declaration and can never reorder a valid explicit graph.

> Checks **4a–4c** are **report-only** in both default and `--check` — story dependency
> fixes need human judgment. Check **4d** cross-spec findings are **blocking** (invalid
> explicit metadata must be corrected before a phase can execute), except duplicate
> entries, which may be safely auto-fixed by deduplication that preserves first-occurrence order.

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

#### Check 8: Spec Owner Field Presence

**Purpose:** Confirm every spec created on or after 2026-04-24 declares an owner, while keeping legacy specs quiet.

For each `spec.md` under `.writ/specs/`:

```bash
git log --diff-filter=A --format=%aI -- {spec.md} | tail -1
```

Use that first-add commit date as the authoritative creation date. If the command returns no date (for example, a new uncommitted spec), fall back to the date prefix in the spec folder name, then filesystem metadata if needed.

**Classification:**
```
If created date >= 2026-04-24:
  REQUIRE: frontmatter contains an owner field (`> **Owner:** ...` or `owner: ...`)
  On miss: WARN only (do not fail) and offer to backfill from `git config user.name`

If created date < 2026-04-24:
  REPORT: "legacy — owner not required"
  Missing owner is not a warning and is never auto-fixed
```

**Backfill offer:**
If a new spec is missing owner, offer an explicit opt-in fix:

```bash
OWNER="@$(git config user.name 2>/dev/null | tr -d ' ' || echo 'unknown')"
if [ "$OWNER" = "@" ]; then OWNER="@unknown"; fi
```

Then insert the owner line into the frontmatter/header. Never migrate legacy specs automatically.

> Check **8** is **warning/report-only** by default. It does not fail verification and does not backfill without explicit user approval.

---

### Phase 3: Verification Report

Present all findings in a structured report (console). The table always has **eight** checks — no "Skipped" rows (except Check 7 when `spec-lite.md` is absent), no alternate layouts.

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
 8. Spec owner field             ⚠️       1 new spec missing owner
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

[WARN-2] Missing owner on new spec
  .writ/specs/2026-04-24-feature/spec.md
  → Add `owner: @YourName` or approve backfill from `git config user.name`.

[INFO-1] Legacy spec without owner
  .writ/specs/2026-03-01-old-feature/spec.md
  → legacy — owner not required.
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
| Spec owner field | ✅ | New specs declare owners; legacy specs reported without warnings |

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

Checks 1–8 evaluated; fixable metadata updated.
See report: .writ/specs/[spec-folder]/verification-YYYY-MM-DD.md
```

**Completion message (`--check`):**
```
✅ Spec verification (--check) complete — no files modified.
```

---

## Product Consistency Checks (`--product`)

A **separate, self-contained check set** for the product layer, run only under
`/verify-spec --product`. These are **not** spec checks 1–8 pointed at product
docs — they are their own ~4 checks with their own dispositions, report, and
output file. Resist the urge to mirror all eight spec checks onto product docs;
the value is a tight, high-signal lint, not a second full diagnostic.

**Boundary (critical):** `--product` answers *"is the product layer internally
consistent and true to reality?"* — a lint you run **before** deciding anything.
Its revision counterpart is [`/plan-product --reconcile`](plan-product.md), which
answers *"is it still the right plan? revise it,"* run **after** you decide to
change. Run `--product` first to see *what* drifted; run `--reconcile` to decide
*what to do*. This is the same before/after discipline that keeps `/assess-spec`
(before) and default `/verify-spec` (after) distinct — do not let the two blur.

### Inputs

| File | Role |
|---|---|
| `.writ/product/mission.md` | **Authoritative** — vision + Key Features phase labels |
| `.writ/product/roadmap.md` | **Authoritative** — phase statuses (shipped / next / planned) |
| `.writ/product/mission-lite.md` | **Derivative** of `mission.md` |
| `.writ/context.md` | **Derivative** (regenerated by `/status` Step 8) |
| `.writ/decision-records/adr-*.md` | Reference targets for Check P2 |
| `.writ/specs/*/` | Evidence for Check P4 (shipped-claim sanity) |

**Graceful skip:** If no `.writ/product/` directory exists, print a clear message
(`No .writ/product/ found — nothing to verify. Run /plan-product first.`) and exit
with no error and no files written. A missing `.writ/context.md` is **not** an
error — it is treated as a derivative to (re)generate in Check P3.

### The Checks

Run all four, collect every finding before reporting (same discipline as the spec
checks). Numbered **P1–P4** to keep them visibly distinct from spec checks 1–8.

#### Check P1: Phase-Status Parity (mission ↔ roadmap) — report-only

Compare phase status between the two authoritative files. Flag when a phase is
marked complete/shipped in `roadmap.md` but still labeled "next"/planned/upcoming
in `mission.md`'s Key Features (or vice versa).

```
For each phase referenced in both mission.md Key Features and roadmap.md:
  roadmap says "✅ Complete" / "Shipped" / "IMPLEMENTED"
  but mission Key Features heading says "(next)" / "planned" / "upcoming"
  → flag as phase-status divergence (report-only)
```

> **Disposition: report-only.** The two files disagree on an *authoritative* fact;
> a human decides which is right (did the phase actually ship, or did the roadmap
> jump ahead?). `--product` never rewrites `mission.md` or `roadmap.md` prose.

#### Check P2: ADR Reference Resolution — report-only

Every `adr-0NN` (or `ADR-0NN`) referenced in `mission.md` / `roadmap.md` /
`mission-lite.md` must resolve to a file under `.writ/decision-records/`.

```
For each ADR id referenced in the product docs:
  Does .writ/decision-records/adr-{NN}-*.md exist?
  If not → flag as unresolved ADR reference (name the id and citing file)
```

> **Disposition: report-only.** A missing ADR file is a real bug worth human eyes —
> either the reference is wrong or the ADR was never written. Do not auto-create.

#### Check P3: Derivative Freshness — auto-fix (regenerate)

Confirm `mission-lite.md` and `.writ/context.md` reflect the current authoritative
`mission.md` (core value, current phase, differentiators). Flag material staleness
— e.g. `mission-lite.md`'s "Current Phase" section contradicts `mission.md`, or
`.writ/context.md` cites a superseded phase.

```
Compare mission-lite.md (and .writ/context.md) against mission.md:
  A key fact (core value, current phase, differentiator) in mission.md that is
    absent, stale, or contradicted in the derivative → flag as diverged
  Ignore condensation — brevity is expected; only material divergence counts
    (same threshold as spec Check 7)
```

> **Disposition: auto-fix in default `--product` (regenerate).** See below. In
> `--check` (or `--product --check`): report only, regenerate nothing.

#### Check P4: Shipped-Claim Sanity — report-only (heuristic)

For each roadmap feature/phase marked shipped/complete, look for plausible
evidence: a matching spec folder under `.writ/specs/` (status Complete) or a
changelog/CHANGELOG entry. Absence is a *soft* signal, not proof of error.

```
For each roadmap item marked shipped/complete:
  Is there a plausibly matching .writ/specs/*/ folder or changelog line?
  If none found → flag as unverified shipped-claim (heuristic, report-only)
```

> **Disposition: report-only, heuristic.** Naming rarely maps 1:1; treat findings
> as "worth a glance," never as failures. High false-positive tolerance by design.

### Auto-Fix Mechanics (Check P3 only)

Reuse default `/verify-spec`'s derivative-regeneration pattern (Phase 4.4 spec-lite
regen), applied to the product derivatives. Runs only in default `--product` (not
`--product --check`), and **only** for Check P3 findings:

1. **`mission-lite.md`** — regenerate from `mission.md`: a condensed (~5-sentence
   core + phase context) version covering core value, target users, key
   differentiators, success definition, and current phase. Prepend
   `> Regenerated from mission.md on YYYY-MM-DD`. Write the full file — never patch
   sections.
2. **`.writ/context.md`** — regenerate from the `/status` Step 8 schema (full
   rewrite; each write replaces the entire file). If it is absent, create it.

**Never touch authoritative prose.** `mission.md` and `roadmap.md` are always the
source, never the target of `--product` — exactly as `spec.md` is never modified by
spec Check 7. P1 (phase parity) and P2 (ADR references) surface *authoritative*
divergence, which is reported for a human to resolve, never silently rewritten.

### Report

Reuse the existing verification report shape, but the check table shows the **four
product checks (P1–P4)**, not the eight spec checks:

```
🔍 Product Consistency Report

═══════════════════════════════════════════════════
 CHECK                           STATUS   FINDINGS
═══════════════════════════════════════════════════
 P1. Phase-status parity          ❌       roadmap: Phase 6 Complete; mission: "Phase 6 (next)"
 P2. ADR reference resolution     ✅       All references resolve
 P3. Derivative freshness         🔧       mission-lite + context regenerated
 P4. Shipped-claim sanity         ⚠️       1 roadmap item without a matching spec (heuristic)
═══════════════════════════════════════════════════

Overall: ⚠️ authoritative drift found (P1) — regenerated derivatives (P3);
         P1/P4 need human judgment.
```

Write the report to **`.writ/product/verification-YYYY-MM-DD.md`** — product-scoped,
**not** a per-spec `verification-*.md`. Structure mirrors Phase 5's file, with the
P1–P4 summary table, a "Regenerated" list (P3), and an "Outstanding (needs human
judgment)" list (P1/P2/P4).

**Completion message (default `--product`):**
```
✅ Product consistency check complete.
Checks P1–P4 evaluated; stale derivatives regenerated.
See report: .writ/product/verification-YYYY-MM-DD.md
```

**Completion message (`--product --check`):**
```
✅ Product consistency check (--check) complete — no files modified.
```

---

## Integration with Writ

| Command | Relationship |
|---------|-------------|
| `/implement-spec` | May leave spec metadata noisy after bulk story work — `/verify-spec` cleans it up |
| `/plan-product --reconcile` | The revision counterpart to `--product`: `--product` lints (before), `--reconcile` revises (after) |
| `/ship` | Optionally runs a **subset** of these checks (1–3) inline when opening a PR |
| `/release` | Runs the **full** checks 1–8 again as part of its **internal** release gate (self-sufficient) — same logic, different entry point |
| `/security-audit` | Complementary — verify-spec checks spec structure; security-audit checks safety |
| `/status` | Quick overview; verify-spec is the deep metadata pass |

**Recommended posture:** `/verify-spec` is **optional**. Many sessions go straight `/ship` → `/release`. Run `/verify-spec` when you want a dedicated hygiene pass without releasing.

**Boundary principle:** `/verify-spec` owns **spec metadata integrity** only. `/release` owns **tests, build verification, and changelog** for publishing.

---

## References

- Standing instructions: [`commands/_preamble.md`](_preamble.md)
- Identity & Prime Directive: [`system-instructions.md`](../system-instructions.md)
