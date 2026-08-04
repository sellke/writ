# Story 4: `/ralph status` — Monitoring and Cursor Re-entry

> **Status:** Completed ✅
> **Priority:** Medium
> **Dependencies:** Story 1

## User Story

**As a** Writ developer returning to Cursor after CLI autonomous execution
**I want** a `/ralph status` mode in `commands/ralph.md` that reads Ralph state from `.writ/state/`, summarizes human-readable progress (stories completed, in progress, failed, blocked), surfaces blockers and escalation reports, and suggests concrete next steps
**So that** I can close the Cursor→CLI→Cursor loop with a clear picture of what happened, what remains, and how to proceed without manually diffing JSON or git history

## Acceptance Criteria

- [ ] **Given** one or more `.writ/state/ralph-*.json` files written per Story 1’s schema (and optional story-file Status metadata), **when** the developer runs `/ralph status` in Cursor, **then** the command prints a **human-readable progress dashboard** grouping work by outcome (e.g., completed, in-progress, attempted-failed, blocked) with spec/story identifiers and last-updated signals
- [ ] **Given** state records that include failure or blocked semantics per the spec’s **Error Experience** (single failure vs. 3+ blocked, escalation when all remaining stories are blocked), **when** `/ralph status` runs, **then** it surfaces **blockers and escalation summaries** in plain language (reasons, diagnostics pointers, iteration counts where applicable), not only raw JSON dumps
- [ ] **Given** the **State Catalog** states (empty, planned, executing, paused, escalated, complete), **when** `/ralph status` evaluates the workspace, **then** it classifies the current Ralph phase, explains what that means, and gives **next-step guidance** (e.g., run `./ralph.sh` to resume, re-run `/ralph plan` if stale, open specific story files or drift logs, address blockers before continuing)
- [ ] **Given** git history with per-story commits from the CLI pipeline, **when** `/ralph status` runs, **then** it optionally correlates **recent Ralph-related commits** (or tagged messages) with state for extra confidence — without replacing state files as the source of truth (**Feedback Model**)
- [ ] **Given** no Ralph state files exist yet, **when** `/ralph status` runs, **then** it fails gracefully with a clear message (e.g., run `/ralph plan` first) and does not claim false progress — aligned with **Success Criteria** “state files from CLI readable in Cursor”

## Implementation Tasks

- [x] 4.1 Write a **verification matrix** (Given/When/Then) for `/ralph status`: empty state, planned-only, mid-loop executing, paused, single attempted-failed, blocked after 3+, full escalation, complete; include expected dashboard sections and next-step copy — use as the acceptance harness (no automated test runner in repo)
- [x] 4.2 Extend **`commands/ralph.md`** with a **`/ralph status`** workflow: discover and read `.writ/state/ralph-*.json` (latest vs. full history per command design), parse fields per **`.writ/docs/ralph-state-format.md`** (Story 1), and render the progress dashboard (structured sections, scannable bullets)
- [x] 4.3 Implement **blocker and escalation presentation**: map JSON fields to the spec’s **Error Experience** vocabulary; call out “all remaining blocked” escalation reports; link or name related artifacts (e.g., story paths, optional drift logs) when state references them
- [x] 4.4 Add **phase detection** using the **State Catalog** plus simple heuristics (e.g., newest state timestamp, presence of plan/handoff artifacts, incomplete vs. complete story sets); emit **next-step guidance** that distinguishes resume, replan, unblock, and review-merge paths
- [x] 4.5 Document **differentiation from `commands/status.md`**: `/status` = project-wide specs/issues/health; `/ralph status` = Ralph loop execution only — short table or callout in `ralph.md` to prevent confusion
- [x] 4.6 Optional **git correlation** subsection: how to surface recent commits that match Ralph story iterations (conventions from CLI story pipeline / commit message pattern); keep state JSON authoritative; skip if no stable convention yet — document the choice
- [x] 4.7 **Verify** with the matrix from 4.1 across fixture states (manual JSON fixtures under `.writ/state/` acceptable for dry-run); confirm alignment with **Feedback Model** and **Success Criteria** item 5; update **`SKILL.md`** / discoverability if `/ralph status` is user-facing and not already listed

## Notes

**Technical considerations**

- Deliverables are markdown commands and docs — “tests” are the verification matrix and manual dry-runs (`AGENTS.md`).
- Prefer reading **human-readable JSON** as specified in Story 1; tolerate minor schema evolution via optional fields and explicit “unknown field” handling in narrative output.
- **Single source of truth:** State files win over git for progress; git is supplementary signal only.
- Cursor-native presentation: phased steps, AskQuestion only if choosing among multiple state files or specs is required; otherwise deterministic summary from disk.

**Integration points**

- **Story 1:** `.writ/docs/ralph-state-format.md` is authoritative for field names and semantics; `/ralph status` must not invent a parallel schema.
- **Story 2+ (CLI pipeline):** Failure/blocker flags and escalation payloads should display as written by the loop; cross-link **`/.writ/docs/ralph-cli-pipeline.md`** for “what this field means.”
- **`commands/status.md`:** Complementary, not duplicate — cross-link in both directions if maintainers expect overlap.
- **Story files / drift logs:** When state or file paths point to them, include actionable paths in output; do not require parsing full spec bodies in v1 unless already in state.

**Risks**

- **Multiple `ralph-*.json` files:** Ambiguity about “current” state — mitigation: define selection rules (newest by timestamp, or merge summaries) in the command and document edge cases.
- **Schema drift** between plan, CLI, and status — mitigation: version field in JSON (Story 1) and defensive messaging when required keys are missing.
- **Overloading `/ralph`:** Keep `plan` vs. `status` subcommands clearly separated in `commands/ralph.md` with parallel structure for discoverability.

## Definition of Done

- [ ] All tasks completed
- [ ] All acceptance criteria met
- [ ] Verification matrix executed with no blocking gaps
- [ ] `commands/ralph.md` documents `/ralph status` end-to-end and distinguishes it from `/status`
- [ ] Cross-links to `ralph-state-format.md` (and `ralph-cli-pipeline.md` where relevant) are accurate
- [ ] Ready for developers to use as the default “return to Cursor” review step after CLI runs

## Context for Agents

- **Error map rows:** Story fails once → `attempted-failed`, may retry later — **Experience Design → Error Experience**. Story fails 3+ → `blocked` + diagnostics — same section. All remaining blocked → escalation report + clean stop — same section. Environment broken → stop loop — same section.
- **Shadow paths:** Happy path step 10 — developer returns to Cursor; **Happy Path Flow** step 10. Monitoring during run — steps 8–9 (state/git); **Feedback Model** (state per iteration, commits, `/ralph status` dashboard, no push notifications v1).
- **Business rules:** State as single source of truth — **Business Rules → State as Single Source of Truth**. Platform separation — `/ralph status` Cursor-native — **Platform Separation**. Plan disposability — next steps may include `/ralph plan` again — **Plan Disposability**.
- **Experience:** **State Catalog** (empty, planned, executing, paused, escalated, complete) for phase copy and guidance; **Moment of Truth** for the “Monday morning” review framing; **Success Criteria** item 5 — seamless round-trip readability of CLI-written state in Cursor.

---
