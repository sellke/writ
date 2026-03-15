# Story 4: /refresh-command Core

> **Status:** Completed ✅
> **Priority:** High
> **Dependencies:** None

## User Story

**As a** solo developer using Writ
**I want to** run `/refresh-command` to scan agent transcripts after command use, identify friction patterns and improvement opportunities, and receive concrete diffs to apply to command files
**So that** commands get better through use — the core learning loop for Writ

## Acceptance Criteria

- [x] **AC1:** Given I invoke `/refresh-command` with no arguments, when the command runs, then I am prompted interactively to select a command (from available Writ commands) and a transcript (from agent-transcripts/); the command lists transcripts with metadata (date, command inferred if detectable) to aid selection.
- [x] **AC2:** Given I invoke `/refresh-command create-spec`, when the command runs, then I am prompted only to select a transcript; the command to refresh is fixed as `create-spec`.
- [x] **AC3:** Given I invoke `/refresh-command create-spec --last`, when the command runs, then the most recent transcript that used `create-spec` is selected automatically; no interactive transcript selection is required.
- [x] **AC4:** Given a transcript is selected, when the command scans it, then it identifies real friction signals (agent struggled, unnecessary questions, low-quality output, many iterations), skip signals (user skipped/dismissed steps), surprise signals (unexpectedly good or bad output), and duration signals (disproportionately long steps); the analysis determines root cause (command design, prompt quality, context gap), impact, frequency, and fixability.
- [x] **AC5:** Given friction patterns are identified, when the command proposes amendments, then each proposal includes: (1) a concrete diff — specific changes to the command markdown file, (2) rationale — why each change improves the command, (3) confidence — High/Medium/Low, and (4) scope assessment — project-specific or universally applicable; amendments are applied to the local command copy (e.g., `.cursor/commands/[command].md`) and a changelog entry is written to `.writ/refresh-log.md`.

## Implementation Tasks

- [x] 4.1 Write tests for the refresh-command flow — mock transcript .jsonl content, verify command identification from transcript, verify friction signal extraction (friction, skip, surprise, duration), verify amendment proposal format (diff + rationale + confidence + scope); verify local apply and changelog write.
- [x] 4.2 Create `commands/refresh-command.md` — document the full command process: invocation modes (interactive, specific command, --last), pipeline stages (SELECT → SCAN → ANALYZE → PROPOSE → LOCAL APPLY + changelog), transcript scanning targets, analysis criteria, output format, and local-first application paths.
- [x] 4.3 Implement transcript scanning logic — parse .jsonl files from agent-transcripts/, extract conversation turns; implement command identification (detect which Writ command was executed from user messages, tool calls, or context); implement signal extraction for friction, skip, surprise, and duration patterns.
- [x] 4.4 Implement friction analysis — for each extracted signal, determine root cause (command design, prompt quality, context gap), impact, frequency (if cross-transcript data available), and fixability; produce structured analysis output for the proposal phase.
- [x] 4.5 Implement amendment proposal — given analysis output, generate concrete diffs to the command markdown file; attach rationale, confidence (High/Medium/Low), and scope assessment (project-specific vs universal) per amendment; support local apply to `.cursor/commands/`, `.claude/commands/`, etc.; write changelog entry to `.writ/refresh-log.md`.
- [x] 4.6 Copy `commands/refresh-command.md` to `.cursor/commands/refresh-command.md` for Cursor command discovery.
- [x] 4.7 Verify end-to-end: run `/refresh-command` interactive → select command and transcript → confirm scan, analysis, proposal, and local apply; run `/refresh-command create-spec --last` → confirm automatic transcript selection; run `/refresh-command refresh-command --last` → confirm bootstrap property (refresh-command can refresh itself).

## Notes

**Technical considerations:**
- **Transcript .jsonl format:** Each line is a JSON object with `role` and `message`; `message.content` may contain text or structured content. Parsing must handle nested structures (e.g., `content[].text` for user queries, tool calls for agent actions). Transcripts may live in `agent-transcripts/[uuid]/[uuid].jsonl` or `agent-transcripts/[uuid]/subagents/[sub-uuid].jsonl`; main transcript is the primary target.
- **Identifying which command was used:** Scan user messages for command invocation patterns (e.g., `/create-spec`, `/implement-story`); check for references in system context or tool parameters; if ambiguous, prompt user or use "unknown" and still attempt signal extraction.
- **Handling large transcripts:** For very long transcripts, consider chunking or sampling; prioritize recent turns and high-signal regions (tool calls, AskQuestion responses, error/retry sequences); document token budget constraints for analysis phase.
- **Bootstrap property:** `/refresh-command` should be designed to work on itself. The command file must describe its own flow clearly enough that an agent can execute it to refresh `refresh-command.md`; the first post-ship validation is refreshing the learner with itself.

**Risks:**
- Command identification from transcripts may be unreliable if invocation patterns vary across adapters; consider explicit metadata injection in future phases.
- Friction signal extraction is heuristic — may miss subtle patterns or over-flag noise; start with high-confidence signals, iterate based on usage.

**Integration points:**
- `agent-transcripts/` — transcript source (JSONL)
- `commands/` — canonical command source
- `.cursor/commands/`, `.claude/commands/` — local command copies (amendments applied here)
- `.writ/refresh-log.md` — changelog for applied amendments

## Definition of Done

- [x] All tasks completed
- [x] All acceptance criteria met
- [x] Tests passing
- [x] `commands/refresh-command.md` created and copied to `.cursor/commands/`
- [x] Transcript scanning identifies real friction patterns
- [x] Proposed amendments are concrete diffs with rationale, confidence, and scope
- [x] Local apply and changelog write verified
- [x] Bootstrap property validated: `/refresh-command refresh-command --last` runs successfully
