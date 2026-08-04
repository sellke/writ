# Story 4 — `/status` North Star Rewrite

> Status: Completed ✅
> Priority: High
> Dependencies: Story 1 (config persistence)

## User Story

As a developer using Writ, I want `/status` to orient my session from stable project state — config, in-flight batch work, and refresh opportunities — without bogus command suggestions, so that I trust its output as the single north star for what to do next.

## Acceptance Criteria

**Given** `.writ/config.md` exists (Story 1)
**When** an agent runs `/status`
**Then** it loads conventions and stable project facts from that file first and does not re-run full detection for keys already defined there on subsequent runs in the same session context.

**Given** one or more `.writ/state/execution-*.json` files exist from `/implement-spec`
**When** an agent runs `/status`
**Then** it inspects those files and surfaces any in-flight batch orchestration (e.g., active or incomplete stories/jobs) with paths or identifiers clear enough to resume or investigate.

**Given** agent transcripts exist per command and `/refresh-command` maintains a refresh history
**When** for a given command there are **three or more** new transcripts since the last logged refresh for that command (per the refresh log and transcript index conventions documented in `status.md`)
**Then** `/status` calls out a **pending refresh opportunity** for that command and suggests `/refresh-command` (not a phantom command).

**Given** the current `commands/status.md` content
**When** a maintainer searches for legacy or invalid command names
**Then** **zero** references remain to: `commit-wip`, `sync-main`, `doctor`, `reset-deps`, or `review-specs` (and no other non-existent slash-commands).

**Given** `status.md` suggests next actions or example invocations
**When** those suggestions name Writ commands
**Then** every named command exists in the suite allowlist: `create-spec`, `implement-story`, `implement-spec`, `prototype`, `review`, `verify-spec`, `refresh-command`, `assess-spec`, `ship`, `release`, `plan-product`, `design`, `research`, `refactor`, `status`, `new-command`, `initialize`, `create-adr`, `create-issue`, `edit-spec`, `migrate`, `prisma-migration`, `test-database`, `retro`, `security-audit`, `explain-code`.

## Implementation Tasks

- [x] Write an AC verification checklist (config read order, execution JSON glob behavior, refresh-opportunity counting rule, phantom-command grep, allowlist audit for every suggested command) and treat it as the test plan — markdown-only story, no unit test harness.
- [x] Read `commands/status.md` and `commands/implement-spec.md` (execution state shape); document in technical notes how to interpret `execution-*.json` fields for “in-flight” vs completed.
- [x] Cross-check refresh logging: confirm canonical path (e.g. `.writ/refresh-log.md` per `commands/refresh-command.md`) and how to associate “last refresh” per command; document the **3+ new transcripts** rule for `status.md` executors.
- [x] Rewrite `commands/status.md` so the default output covers: git position, active spec and story (from `.writ/specs/` conventions), **pending refresh opportunities**, **in-flight batch jobs**, project health signals, and **suggested next actions** — all grounded in Story 1 config when present.
- [x] Remove all five phantom command references and replace suggestions with only allowlisted real commands; add a short maintainer note in `status.md` listing the allowlist (or pointing to this story) so future edits do not reintroduce ghosts.
- [x] Align wording with Story 1: explicit read order (`.writ/config.md` → detect only for missing keys) where `status` overlaps with ship/release/initialize conventions.
- [x] Run the full verification checklist against `commands/status.md`; grep for phantoms and for any `/`-command tokens not in the allowlist; confirm every AC passes.

## Technical Notes

- Scope is **markdown instruction files only** (no runtime code): behavior is specified for the AI agent executing `/status`.
- **Execution state:** `/implement-spec` writes `.writ/state/execution-{timestamp}.json` — `status.md` should instruct agents to list/read matching files and summarize active batch work without parsing assumptions beyond what `implement-spec.md` documents.
- **Refresh opportunities:** Prefer `.writ/refresh-log.md` (canonical in `refresh-command.md`) for per-command last-refresh timestamps or transcript references; if counting “new transcripts,” reference the agent-transcript conventions already used elsewhere in Writ docs (e.g. transcript IDs in refresh-log entries). If path or format differs in this repo, `status.md` must state the **one** authoritative rule so executors do not guess.
- **Output contract:** Session orientation sections should be skimmable (headings + bullets); suggested commands must always include the leading `/` only for commands that exist.
- **Dependency:** Story 1 must land first so `.writ/config.md` is a defined artifact; until then, `status.md` should still specify graceful fallback (detect + optional persist offer per Story 1) without blocking this story’s merge.

## Definition of Done

- [x] All tasks complete
- [x] All AC verified
- [x] Tests passing
- [x] Code reviewed
- [x] Docs updated if needed
