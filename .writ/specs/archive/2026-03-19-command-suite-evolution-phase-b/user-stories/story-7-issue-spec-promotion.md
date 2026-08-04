# Story 7 — Issue → Spec Promotion Pipeline

> Status: Completed ✅
> Priority: Medium
> Dependencies: Phase A Story 4 (status North Star rewrite), Phase B Story 5 (context auto-loading — both land before extending `status.md` here)
> Phase A spec: `.writ/specs/2026-03-19-command-suite-evolution/`

## User Story

As a developer using Writ, I want issues under `.writ/issues/` to flow cleanly into the contract-first spec pipeline so that triage work is not a dead end and every promoted item leaves a durable link from the issue file to the new spec.

## Acceptance Criteria

**Given** `commands/create-spec.md` after this story
**When** the agent is instructed to create a spec with `--from-issue [path]` pointing to a valid issue file under `.writ/issues/{bugs,features,improvements}/`
**Then** the command reads that issue file and enters the normal multi-phase discovery conversation with the discovery contract **pre-populated** from the issue's type, description, and affected files (and any other mapped fields the command doc defines).

**Given** a `--from-issue` run completes successfully and a new spec directory exists at `.writ/specs/[date]-[name]/spec.md`
**When** the flow finishes
**Then** the source issue file is **updated in place** (never deleted) with `spec_ref: .writ/specs/[date]-[name]/spec.md` so promotion is additive and traceable.

**Given** `commands/create-issue.md` after this story
**When** a new issue file is created from the template
**Then** the template includes a `spec_ref` field **empty by default**, with brief guidance that it is set when the issue is promoted via `create-spec --from-issue`.

**Given** `commands/status.md` after Story 4, Story 5, and this story
**When** the agent runs status
**Then** it surfaces a **"Needs Triage"** section listing issues in `.writ/issues/` that are **older than 7 days**, have **no `spec_ref`** (empty or absent), and are otherwise valid issue files — so stale untriaged work is visible without conflating it with active spec work.

**Given** an issue file missing expected fields or an invalid `--from-issue` path
**When** the agent attempts `--from-issue`
**Then** `create-spec.md` documents clear failure or fallback behavior (e.g., error message, what to fix) without corrupting the issue file.

## Implementation Tasks

- [x] Define an AC verification checklist (template fields, `--from-issue` happy path, `spec_ref` writeback path format, 7-day / no-`spec_ref` query rules, and error cases) and use it as the gate before merging — treat it as the test plan for these markdown-only changes.
- [x] Update `commands/create-issue.md` so new issues include `spec_ref:` in the template (empty by default) and a one-line note on when it is filled.
- [x] Update `commands/create-spec.md` to document `--from-issue [path]`: how to parse the issue file (frontmatter / field layout consistent with existing issue fields: type, priority, description, affected files, effort estimate), and how mapped values seed the discovery contract before the normal conversation continues.
- [x] Extend `commands/create-spec.md` so that after successful spec creation from `--from-issue`, the agent writes or updates `spec_ref` on the source issue file to the new `spec.md` path; issue content otherwise preserved.
- [x] Update `commands/status.md` (on top of the Story 4 and Story 5 rewrites) with a **Needs Triage** section: enumerate `.writ/issues/**` markdown files where `spec_ref` is empty or missing and file age (from filename date `YYYY-MM-DD-` or documented rule) is **> 7 days**.
- [x] Walk the verification checklist against `create-issue.md`, `create-spec.md`, and `status.md`; confirm every AC passes and cross-links between issue and spec workflows read consistently.

## Technical Notes

- Scope is **markdown instruction files only** (no runtime code): behavior is specified for the agent executing the commands.
- Issue paths follow `commands/create-issue.md`: `.writ/issues/{bugs,features,improvements}/YYYY-MM-DD-{slug}.md`.
- **Promotion is additive:** update the issue with `spec_ref`; do not remove or archive the issue as part of this flow unless a future story explicitly adds that.
- **Story 4 dependency:** `status.md` structure and "North Star" layout land in Story 4; this story **extends** that file with Needs Triage rather than defining the whole status command.
- **Story 5 dependency:** Story 5 adds the context.md regeneration step to `status.md`; this story extends that file further. Story 5 must complete before this story to eliminate `status.md` merge conflicts.
- Align parsing with whatever issue template actually emits (type, description, affected files, etc.) so pre-population does not require hand-editing the issue before promotion.
- For the 7-day rule, prefer the date embedded in the filename (`YYYY-MM-DD`) when present for consistency; document if mtime is a fallback.

## Definition of Done

- [x] All tasks complete
- [x] All AC verified
- [x] Tests passing
- [x] Code reviewed
- [x] Docs updated if needed

## What Was Built

> Implemented: 2026-03-20
> Files modified: 3 (create-issue.md, create-spec.md, status.md)

Added `spec_ref:` to the `create-issue.md` template (empty by default, with guidance that it's filled on promotion). Added a full `--from-issue [path]` mode to `create-spec.md` that validates the path, parses issue fields, runs a shortened discovery conversation, and writes `spec_ref` back to the issue file after successful spec creation. Added a "Needs Triage" step (Step 5) to `status.md` that surfaces issue files older than 7 days with no `spec_ref`, and added the corresponding condition to the Suggested Actions table.
