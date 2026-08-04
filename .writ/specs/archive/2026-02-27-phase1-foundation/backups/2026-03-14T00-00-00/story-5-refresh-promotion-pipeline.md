# Story 5: /refresh-command Promotion Pipeline

> **Status:** Completed ✅
> **Priority:** Medium
> **Dependencies:** Story 4 (/refresh-command core)

## User Story

**As a** solo developer using Writ
**I want to** optionally promote locally applied command improvements upstream to Writ core after `/refresh-command` applies them
**So that** good local improvements can flow back to the framework and benefit the broader community

## Acceptance Criteria

- [x] **AC1:** Given `/refresh-command` has just applied a local improvement, when the apply phase completes, then I am prompted: "This improvement looks universally applicable. Promote to Writ core?" with options: Yes, No, Later — but only when the scope assessment indicates universally applicable and confidence is High.
- [x] **AC2:** Given I choose "Yes" to promote, when the promotion flow runs, then a diff between the core command (`commands/[command].md`) and the local command (`.cursor/commands/[command].md`) is generated, a PR is created against the Writ repository with context and rationale, and the refresh-log entry is marked "Promoted to core."
- [x] **AC3:** Given I choose "No" to promote, when the flow continues, then the improvement remains local only; the refresh-log entry is marked "Local only"; no PR is created.
- [x] **AC4:** Given I choose "Later" to promote, when the flow continues, then the improvement remains local; the refresh-log entry is marked "Local only" with a flag indicating it is queued for batch promotion review; the change is accumulated for periodic batch review.
- [x] **AC5:** Given any outcome (Yes, No, Later, or no prompt when scope/confidence does not warrant it), when the refresh completes, then a changelog entry is written to `.writ/refresh-log.md` in the canonical format with source transcript, changes, scope, and confidence.

## Implementation Tasks

- [x] 5.1 Write tests for the promotion pipeline — mock scope assessment (universal vs project-specific) and confidence (High/Medium/Low); verify promotion prompt appears only when universal + High; verify "Yes" triggers PR creation flow; verify "No" keeps local and writes correct scope; verify "Later" writes correct scope and batch flag; verify refresh-log entry is created for all paths.
- [x] 5.2 Define the canonical refresh-log entry format in `.writ/docs/refresh-log-format.md` — document the markdown structure (date header, source transcript, changes list, scope, confidence); document scope values (Local only / Promoted to core); document batch promotion flag for "Later" entries.
- [x] 5.3 Implement promotion prompt logic — after local apply in refresh-command, check scope assessment and confidence; if universal + High, present AskQuestion with Yes/No/Later; otherwise skip prompt and write refresh-log with "Local only."
- [x] 5.4 Implement refresh-log writer — generate changelog entry per canonical format; append to `.writ/refresh-log.md`; include source transcript ID, change descriptions, scope, and confidence; create file if missing.
- [x] 5.5 Implement "Yes" promotion flow — generate diff between `commands/[command].md` and local copy; create PR against Writ repository with diff, context, rationale, and transcript reference; update refresh-log entry to "Promoted to core."
- [x] 5.6 Implement "Later" batch flag — when user selects Later, write refresh-log entry with scope "Local only" and a `batch-review: true` or equivalent marker; document batch promotion review process in `commands/refresh-command.md`.
- [x] 5.7 Update `commands/refresh-command.md` and `.cursor/commands/refresh-command.md` — add promotion pipeline stage after LOCAL APPLY; document when promotion is suggested (universal + High only); document Yes/No/Later flows; add reference to refresh-log-format.md; verify end-to-end: apply improvement → confirm prompt (or skip) → confirm refresh-log entry for each path.

## Notes

**Technical considerations:**
- **Local-first always:** Promotion is optional and never forced. The user always retains control.
- **Scope and confidence gating:** Only suggest promotion when scope assessment = universally applicable AND confidence = High. Medium/Low or project-specific → skip prompt, write "Local only."
- **Refresh-log format:**
```markdown
## [DATE] — /[command] refreshed

**Source transcript:** [transcript ID]
**Changes:**
- [Change 1 description]
- [Change 2 description]

**Scope:** Local only / Promoted to core
**Confidence:** High / Medium / Low
```
- **PR creation:** Requires git remote for Writ repo; may need GitHub CLI (`gh pr create`) or API; handle case where user is not a Writ contributor (fork workflow vs direct push).
- **Batch promotion:** "Later" accumulates entries; a future story or manual process can review batch and promote in bulk.

**Risks:**
- PR creation may fail (no auth, no fork, network); provide clear error and fallback (e.g., "Diff saved to .writ/refresh-promotion-[date].patch").
- Scope/confidence gating may be too strict or too loose; iterate based on usage.

**Integration points:**
- `commands/refresh-command.md` — promotion stage, flow documentation
- `.cursor/commands/`, `commands/` — diff source (local vs core)
- `.writ/refresh-log.md` — changelog output
- `.writ/docs/refresh-log-format.md` — format specification (new)
- Story 4 — local apply phase, scope assessment, confidence from analysis

## Definition of Done

- [x] All tasks completed
- [x] All acceptance criteria met
- [x] Tests passing
- [x] Promotion prompt appears only for universal + High confidence
- [x] Yes/No/Later flows behave correctly
- [x] refresh-log.md entry created for all paths (Yes, No, Later, skip)
- [x] Refresh-log format documented
- [x] PR creation verified for "Yes" path (or graceful fallback documented)
