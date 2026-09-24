---
name: verify-spec-lean
description: "Lean variant of /verify-spec for WRIT_HARNESS_LEAN=1 baseline runs. Metadata linter for a spec - story files, statuses, deliverables, dependencies, contract alignment. Auto-fixes what it safely can."
problem: "Spec bookkeeping drifts from the story files that are its source of truth — README statuses, task counts, deliverable checkboxes and spec-lite all rot silently."
outcome: "The spec's derived metadata is realigned where realignment is safe, and every finding that needs human judgement is recorded against the check that raised it."
entry_level: standard
exit_criteria:
  - "in default mode .writ/specs/<spec>/verification-YYYY-MM-DD.md exists with an eight-row check table plus Issues Found & Resolved and Outstanding Warnings sections"
  - "every finding appears under exactly one of those two sections — auto-fixed, or left open and named with its check number"
  - "any regenerated spec-lite.md is a whole-file replacement carrying its regeneration date marker, and spec.md is byte-identical to its pre-run state"
loop:
  unit: "autofix_pass"
  max_iterations: 1
  on_exhaustion: halt_reported
  calibrated_against: "Single-pass by construction: commands/verify-spec.md runs Phase 2 (checks 1-8) then Phase 4 (auto-fixes 4.1-4.4) then Phase 5 (report file), and contains no re-check, re-run, or re-verify step - the only 'again' in the file describes /release invoking checks 1-8 through its own entry point, which is a separate entry point and not a loop. Declaring 1 codifies what the file already does and can break no recorded run. Evidence: strong by construction. Read this as a declaration, not a mitigation - this command has no runaway loop and none has ever been observed. If a re-check pass is ever added, this bound is wrong and must be re-derived."
---

# Verify Spec Command (verify-spec, lean)

## Overview

**Metadata diagnostic** for Writ specs: story files, README tracking, statuses, deliverables, dependencies, and contract alignment. **Default mode auto-fixes** what can be repaired safely, then reports what needs human judgment. Not a pipeline gate; tests, build verification, and changelog work live in `/release`.

## Modes

| Invocation | Mode | Behavior |
|---|---|---|
| `/verify-spec` | Default | Select spec (if needed); run checks 1–8; **auto-fix** fixable issues; report the rest — no confirmation prompt |
| `/verify-spec --check` | Read-only | Same checks; report only; no file changes |
| `/verify-spec --fix` | Fix spec-lite | Run Check 7; if divergence found, fully regenerate `spec-lite.md` from `spec.md` |
| `/verify-spec --spec [path]` | Targeted | Verify the spec at path (folder under `.writ/specs/` or path to `spec.md`) |
| `/verify-spec --all` | All specs | Run the full diagnostic for every spec under `.writ/specs/` |
| `/verify-spec --product` | Product docs | Run the **Product Consistency** check set (P1–P4, **not** spec checks 1–8) over `.writ/product/` + `.writ/context.md`; hybrid auto-fix (regenerate derivatives) / report-only (authoritative divergence) |

`--product` is its own check set, not spec checks pointed at product docs. Its revision counterpart is `/plan-product --reconcile`.

## Command Process

### Phase 1: Spec Discovery & Loading

#### Step 1.1: Select Specification

**`--spec [path]`:** resolve to a spec folder (directory containing `spec.md`). Skip selection.

**`--all`:** every `.writ/specs/*/` folder containing `spec.md`, processed sequentially, with an aggregate summary at the end. This single-level glob excludes `.writ/specs/archive/<name>/spec.md` by construction; do not add an explicit `archive/` filter (see [`.writ/docs/spec-lifecycle.md`](../.writ/docs/spec-lifecycle.md#verify-spec---all-and-archive-exclusion)).

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
Choosing **all** is equivalent to `--all`.

#### Step 1.2: Load Everything

Read `spec.md` (contract, deliverables checklist), `spec-lite.md` if present, `user-stories/README.md`, every `user-stories/story-N-*.md`, and `sub-specs/` if present. Optionally scan git log for commits referencing this spec (context for Check 6). Build a data model of spec status and deliverables, README rows and totals, and per-story status, task / acceptance-criteria / Definition-of-Done counts (total and checked), and dependencies.

---

### Phase 2: Verification Checks

Run checks **1–8**. Collect every finding before reporting — do not stop at the first issue. **Default:** after reporting, apply Phase 4. **`--check`:** report only. **`--fix`:** run Check 7 and regenerate `spec-lite.md` if diverged.

#### Check 1: Story File Integrity

- **1a. Orphan:** a `story-N-*.md` file with no README entry.
- **1b. Phantom:** a README row with no story file.
- **1c. Status header:** every story has `> **Status:** [Not Started | In Progress | Completed ✅]`; missing or malformed → flag.
- **1d. Required sections:** User Story (As a / I want to / So that), Acceptance Criteria, Implementation Tasks, Definition of Done; any missing → flag.

#### Check 2: Status Consistency

- **2a.** README status ≠ story file status → discrepancy.
- **2b.** README task count ≠ actual `- [ ]` / `- [x]` count in the Implementation Tasks section → mismatch.
- **2c.** README total progress ≠ sum of checked tasks across stories → flag.

#### Check 3: Completion Integrity

**Status rollup:** Check 3's single status cell in the Phase 3 table is the **worst status across all of 3a through 3f**. A 3e/3f finding fails the row exactly as a 3a finding would.

For stories reading `Completed ✅`:
- **3a.** Any unchecked acceptance criterion → false completion.
- **3b.** Any unchecked Definition of Done item → incomplete DoD.
- **3c.** Any unchecked implementation task → flag.

- **3d. Premature status:** `Not Started` with checked tasks → should be `In Progress`; `In Progress` with all tasks checked → should be `Completed`.

**3e. Criterion coverage.** Validates the per-criterion `AC-<story>.<n>` IDs ([`.writ/docs/acceptance-criteria-ids.md`](../.writ/docs/acceptance-criteria-ids.md)), a separate contract from 3a–3d. Run `scripts/ac-trace.py check --spec <folder> [--repo .]`; the script decides. Blocking:
- a defined ID cited by no implementation task, at any story status → `untasked_criterion`
- a tasked ID with no test citation, on a story that reads `Completed ✅` → `untested_criterion`

**3f. Dangling and malformed references.** Same `ac-trace.py` run. Blocking:
- a task or test cites an undefined ID → `dangling_reference`
- the same ID on two criterion lines → `duplicate_id`
- an ID exceeds the marker, or the marker is missing/malformed while IDs are present → `marker_violation`
- some criteria in a story carry IDs and others do not → `partial_adoption`

**Legacy posture:** zero criteria in a story carry IDs → `legacy_story`, informational and never blocking. Some-but-not-all is `partial_adoption`, which is blocking.

> Checks **3e** and **3f** are **report-only in every mode**; Phase 4 never touches them, because choosing which task covers a criterion, or repointing a dangling reference, needs human judgment. Every 3e/3f finding goes under **Outstanding Warnings**, never **Issues Found & Resolved**.

**3g. Spec analysis (advisory — not in the 3a–3f roll-up).** Contradictory, missing, and ambiguous acceptance criteria — meaning, not ID coverage; do not reuse 3e/3f or `ac-trace.py`.

```
Run python3 scripts/spec-analyze.py check --spec <folder> [--findings <json>]
Relay the verdict and every reason: line as notes.
A script fail (including malformed_findings) or unverifiable does not
fail this check, the 3a–3f status cell, or the verify report.
add_finding only if the helper is missing or exits 2.
```

Omit `--findings` when no orchestrator JSON exists for this run; `unverifiable` is then a note.

#### Check 4: Dependency Validation

- **4a. Satisfaction:** a `Completed` story whose dependency is not `Completed ✅` → ordering violation.
- **4b. Circular:** a cycle in the story dependency graph → flag.
- **4c. Missing declarations (heuristic):** cross-reference `spec.md` and `sub-specs/technical-spec.md`; flag obvious undeclared dependencies.

**4d. Cross-spec dependency validation.** The spec-level `> **Dependencies:** [spec-folder-id, ...]` header — a separate graph from 4a–4c. Over the reachable cross-spec graph (this spec + every spec it references; a legacy spec with no header is `[]`), flag as blocking:
- malformed header (not the bracket form) → `malformed_dependencies`
- no such folder under `.writ/specs/` → `missing_reference` (name it)
- spec lists itself → `self_reference`
- duplicate entry in one list → `duplicate_reference` (dedupe preserves order)
- cross-spec cycle → `dependency_cycle` (print the exact path)

The executable reference is `scripts/spec-deps.py validate`. Shared-file or prose overlap can only warn about a possibly missing declaration and never reorders a valid explicit graph.

> **4a–4c** are **report-only** in both default and `--check`. **4d** findings are **blocking**, except duplicate entries, which may be auto-fixed by deduplication that preserves first-occurrence order.

#### Check 5: Deliverables Checklist (spec.md)

- **5a.** For each deliverable in the `spec.md` checklist, extract file paths: missing file → flag; checked but file missing → false deliverable; file present but unchecked → unsync'd.
- **5b.** All stories completed and all deliverables checked, but `spec.md` status is not `Complete`/`Completed` → flag.

#### Check 6: Spec Contract vs Implementation

Read the `spec.md` Contract Summary and Scope Boundaries. An **Included** item with no evidence of implementation (files, tests, stories) → unimplemented scope. An **Excluded** item that appears implemented → possible scope creep.

> Check **6** is **report-only** in both modes — heuristic; false positives expected.

#### Check 7: Spec-Lite Integrity

Confirms `spec-lite.md` reflects the authoritative `spec.md` (implement-story may auto-amend spec-lite on Small drift without touching spec.md). **Skip** if `spec-lite.md` does not exist — no flag.

| spec-lite.md section | spec.md section |
|---|---|
| `## What We're Building` (or `## What`) | `## Contract Summary` (or equivalent top-level summary) |
| Key Constraints (inline bullets or `## Key Constraints`) | `## Business Rules` + constraint bullets in contract |
| Success Criteria (`## Success Criteria`) | `## Success Criteria (Phase A)` or `## Success Criteria` |
| Files in Scope (`## Files in Scope`) | `## Scope Boundaries` → Included list |

Match headings by semantic intent; if no clear match exists, skip that pair and note it.

**DIVERGED** when a key fact, constraint, or deliverable in `spec.md` is absent from spec-lite; spec-lite describes something not in `spec.md`; success criteria differ materially; or Files in Scope differ beyond cosmetic renaming. **Not** divergence: shorter phrasing that preserves intent, formatting differences, or absent detail in a condensed file.

Report row: `7. Spec-lite integrity ✅ spec-lite aligned with spec.md`, or `❌ Divergence in N sections:` followed by one bullet per diverged section.

**Regeneration** (`--fix`, or default-mode auto-fix via Phase 4.4): read `spec.md` in full; produce a condensed spec-lite (~100 lines max) covering What We're Building, Key Constraints, Success Criteria, Files in Scope, and any phase/dependency context; prepend `> Regenerated from spec.md on YYYY-MM-DD`; write the full file — never patch sections.

> Check **7** divergence is **auto-fixable** in default mode. `--check`: report only. `--fix`: run Check 7 and regenerate if diverged.

#### Check 8: Spec Owner Field Presence

For each `spec.md` under `.writ/specs/`, the creation date is the first-add commit date:

```bash
git log --diff-filter=A --format=%aI -- {spec.md} | tail -1
```

No date (e.g. uncommitted) → fall back to the folder-name date prefix, then filesystem metadata.

- **Created ≥ 2026-04-24:** require an owner field (`> **Owner:** ...` or `owner: ...`). On miss: WARN only, and offer to backfill from `git config user.name`.
- **Created < 2026-04-24:** report "legacy — owner not required". Never a warning, never auto-fixed.

**Backfill** is an explicit opt-in:

```bash
OWNER="@$(git config user.name 2>/dev/null | tr -d ' ' || echo 'unknown')"
if [ "$OWNER" = "@" ]; then OWNER="@unknown"; fi
```

Then insert the owner line into the header. Never migrate legacy specs automatically.

> Check **8** is **warning/report-only** by default. It does not fail verification and does not backfill without explicit user approval.

---

### Phase 3: Verification Report

Console report. The table always has **eight** checks — no "Skipped" rows except Check 7 when `spec-lite.md` is absent (omit the row and note `(Check 7 skipped — no spec-lite.md found)`).

```
🔍 Spec Verification Report: 2026-02-22-feature-name

 CHECK                           STATUS   FINDINGS
 1. Story file integrity         ✅       All clean
 2. Status consistency           ❌       2 discrepancies
 ...
 8. Spec owner field             ⚠️       1 new spec missing owner

Overall: ⚠️ 4 issues found (2 auto-fixable, 2 need attention)
```

Findings detail groups **Auto-Fixable** (`[FIX-N]`, with the fix applied in default mode) and **Needs Attention** (`[WARN-N]`, with the manual action), plus `[INFO-N]` for legacy/owner notes.

**`--check` mode:** stop after this phase. **Default mode:** continue to Phase 4 automatically — **do not** prompt for fix confirmation.

---

### Phase 4: Auto-Fix (default mode only)

#### 4.1: Sync README with Story Files

Update the status column and task counts to match the story files, recalculate total progress, and update Quick Links completion markers when applicable.

#### 4.2: Sync Deliverables Checklist

Check off deliverables whose files exist; uncheck those whose files are missing (with warning).

#### 4.3: Fix Status Headers

All tasks done → `Completed ✅`; some → `In Progress`; none → `Not Started`; spec with all stories done → `Complete`.

#### 4.4: Regenerate Spec-Lite (Check 7 finding or `--fix` flag)

If Check 7 flagged divergence **and** mode is default (not `--check`), or `--fix` was passed, regenerate per Check 7: `spec.md` is the source of truth; the result covers `## What We're Building`, `## Key Constraints`, `## Success Criteria`, `## Files in Scope`, and phase/dependency context; prepend `> Regenerated from spec.md on YYYY-MM-DD`; write a complete replacement, never a partial patch.

`spec.md` is never modified by this step.

**Iteration bound:** auto-fix is bounded at `loop.max_iterations` (1) **pass**; Phase 4 runs once and has no re-check to loop into. On exhaustion, `loop.on_exhaustion: halt_reported`: if a fix would itself require re-running Phase 2 to confirm, do not run a second pass. Record it as unresolved under **Outstanding Warnings** in the Phase 5 file, naming the unit (`autofix_pass`), the bound, the pass reached, the last fix applied, and `/verify-spec` as the resume command. `--product` Check P3 regeneration is the same single pass.

---

### Phase 5: Verification Report File

Write `.writ/specs/[spec-folder]/verification-YYYY-MM-DD.md`:

```markdown
# Verification Report: [Feature Name]

> **Date:** YYYY-MM-DD
> **Spec:** [spec folder]
> **Mode:** default | check
> **Result:** ✅ Passed / ⚠️ Passed with warnings / ❌ Failed

## Summary

| Check | Status | Details |
|-------|--------|---------|
| Story file integrity | | |
| Status consistency | | |
| Completion integrity | | |
| Dependency validation | | |
| Deliverables checklist | | |
| Contract alignment | | |
| Spec-lite integrity | | |
| Spec owner field | | |

## Stories
| # | Title | Status | Tasks | Criteria | DoD |
|---|-------|--------|-------|----------|-----|

## Issues Found & Resolved
- [FIX-N] ... (auto-fixed)

## Outstanding Warnings
- [WARN-N] ... (Check N)

## Notes
Diagnostic only. Use `/release` when you are ready to publish; it runs build checks, conditional tests, and changelog work.
```

**Completion message (default):** `✅ Spec verification complete.` / `Checks 1–8 evaluated; fixable metadata updated.` / `See report: .writ/specs/[spec-folder]/verification-YYYY-MM-DD.md`

**Completion message (`--check`):** `✅ Spec verification (--check) complete — no files modified.`

---

## Product Consistency Checks (`--product`)

A separate, self-contained check set run only under `/verify-spec --product`, with its own dispositions, report, and output file. Do not mirror the eight spec checks onto product docs. `--product` lints (before a decision); `/plan-product --reconcile` revises (after).

| File | Role |
|---|---|
| `.writ/product/mission.md` | **Authoritative** — vision + Key Features phase labels |
| `.writ/product/roadmap.md` | **Authoritative** — phase statuses (shipped / next / planned) |
| `.writ/product/mission-lite.md` | **Derivative** of `mission.md` |
| `.writ/context.md` | **Derivative** (regenerated by `/status` Step 8) |
| `.writ/decision-records/adr-*.md` | Reference targets for Check P2 |
| `.writ/specs/*/` | Evidence for Check P4 (shipped-claim sanity) |

**Graceful skip:** no `.writ/product/` → print `No .writ/product/ found — nothing to verify. Run /plan-product first.` and exit with no error and no files written. A missing `.writ/context.md` is not an error; Check P3 (re)generates it.

Run all four and collect every finding before reporting.

#### Check P1: Phase-Status Parity (mission ↔ roadmap) — report-only

A phase marked complete/shipped/IMPLEMENTED in `roadmap.md` but labeled "(next)"/planned/upcoming in `mission.md` Key Features (or vice versa) → phase-status divergence. **Report-only:** a human decides which authoritative file is right; never rewrite `mission.md` or `roadmap.md`.

#### Check P2: ADR Reference Resolution — report-only

Every `adr-0NN` / `ADR-0NN` referenced in `mission.md`, `roadmap.md`, or `mission-lite.md` must resolve to `.writ/decision-records/adr-{NN}-*.md`; otherwise flag, naming the id and citing file. **Report-only;** do not auto-create.

#### Check P3: Derivative Freshness — auto-fix (regenerate)

A key fact (core value, current phase, differentiator) in `mission.md` that is absent, stale, or contradicted in `mission-lite.md` or `.writ/context.md` → diverged. Condensation is not divergence (same threshold as Check 7). **Auto-fix in default `--product`**; report only under `--product --check`.

#### Check P4: Shipped-Claim Sanity — report-only (heuristic)

A roadmap item marked shipped/complete with no plausibly matching `.writ/specs/*/` folder (status Complete) or changelog line → unverified shipped-claim. **Report-only, heuristic;** findings are prompts to look, never failures.

### Auto-Fix Mechanics (Check P3 only)

Default `--product` only (not `--product --check`), and only for P3 findings:

1. **`mission-lite.md`** — regenerate from `mission.md`: condensed core (~5 sentences) + phase context covering core value, target users, key differentiators, success definition, current phase. Prepend `> Regenerated from mission.md on YYYY-MM-DD`. Write the full file.
2. **`.writ/context.md`** — regenerate from the `/status` Step 8 schema (full rewrite); create it if absent.

**Never touch authoritative prose.** `mission.md` and `roadmap.md` are always the source, never the target. P1/P2 divergence is reported for a human to resolve.

### Report

Same shape as the spec report, with the **four product checks (P1–P4)** in the table (P3 shows `🔧` when regenerated). Write it to **`.writ/product/verification-YYYY-MM-DD.md`** — not a per-spec file — with the P1–P4 summary table, a "Regenerated" list (P3), and an "Outstanding (needs human judgment)" list (P1/P2/P4).

**Completion message (default `--product`):** `✅ Product consistency check complete.` / `Checks P1–P4 evaluated; stale derivatives regenerated.` / `See report: .writ/product/verification-YYYY-MM-DD.md`

**Completion message (`--product --check`):** `✅ Product consistency check (--check) complete — no files modified.`

---

## Completion

This command succeeds when `.writ/specs/<spec>/verification-<YYYY-MM-DD>.md` carries the eight-row check table and every finding sits under exactly one of Issues Found & Resolved or Outstanding Warnings.

A finding that cannot be auto-fixed is recorded rather than fixed by guesswork. An outstanding warning is a valid result, not an incomplete run.

**Boundary principle:** `/verify-spec` owns spec metadata integrity only; `/release` owns tests, build verification, and changelog.

**Production boundary:** the only writes are the metadata fixes above and the report file. Do not commit, merge, open a PR, release, tag, or publish.

**Terminal constraint:** This command reconciles a spec's derived metadata. `spec.md` is never modified — do not implement stories, change scope, or edit the contract.

---

## References

- Standing instructions: [`commands/_preamble.lean.md`](_preamble.lean.md) (the `WRIT_HARNESS_LEAN=1` sibling of `commands/_preamble.md`)
- Identity & Prime Directive: [`system-instructions.md`](../system-instructions.md)
