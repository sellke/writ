# Story 3: prototype.md Refinement

> **Status:** Not Started
> **Priority:** High
> **Dependencies:** None

## User Story

**As a** Writ maintainer
**I want to** refine prototype.md to A-grade quality
**So that** the innovative features (visual preview, scope escalation, experience gaps) shine through without being buried in template bloat

## Acceptance Criteria

1. **Given** the refined prototype.md, **when** an AI agent executes the command, **then** the full pipeline (Context Scan → Visual Preview → Coding Agent → Lint & Typecheck → Summary) remains executable with no functional capability lost.

2. **Given** the refined file, **when** checking preserved content, **then** the pipeline diagram (lines 30–40), Visual Preview step (Step 2.5), scope escalation flags (six explicit signals), experience gaps concept, "When to Use" comparison table, UI detection heuristic, and nearby rules sniffing are all intact.

3. **Given** the refined file, **when** counting lines, **then** the total is within ~210 ±10% (189–231 lines), down from 358.

4. **Given** the refined file, **when** an AI agent reads the coding agent spawn section, **then** it receives ~25 lines of principles covering: change description, codebase context, TDD requirement, scope detection triggers, experience gap awareness, and respect for nearby rules — without exact output format headers or template scaffolding.

5. **Given** the refined file, **when** an AI agent reads the output summary section, **then** it understands what to show (success), when to surface escalation (scope flags triggered), and how to handle lint failures — in ~20 lines consolidated from the three former format blocks.

## Implementation Tasks

1. **Read and map the current file** — Open `commands/prototype.md`, verify line numbers for sections to rewrite/consolidate. Confirm the pipeline diagram, Visual Preview step, scope escalation flags, and comparison table locations. Note the agent spawn prompt structure (lines 148–229).

2. **Rewrite the agent spawn prompt** — Replace the 80-line prompt block (lines 148–229) with ~25 lines of principles. Include: change description, codebase context, TDD requirement, scope detection triggers (the six flags as explicit list), experience gap awareness, respect nearby rules instruction. Remove exact output format headers (Implementation Summary, Files Created, etc.) — trust the AI to structure. Preserve the six scope escalation signals verbatim; they encode judgment the AI might not infer.

3. **Consolidate output format sections** — Merge the three blocks (success / success-with-escalation / failure, lines 251–323) into ~20 lines. State: what to show on success (files, tests, lint status, visual preview note); when to surface escalation (scope flags triggered — show the specific flags and suggest `/create-spec`); how to handle lint failures after retries (report remaining issues, offer options: fix manually, retry, discard). Remove redundant template scaffolding.

4. **Merge error handling into pipeline** — Inline the Error Handling section (lines 327–345) into the pipeline description as principles: agent crash → retry once; implementation blocked → present blocker, attempted actions, partial progress, options; insufficient context → ask one natural-language question. Remove the standalone Error Handling section.

5. **Trim Lint & Typecheck step** — Keep the detection-and-retry logic (auto-fix, re-run, send to agent for one fix attempt, report if still failing). Remove or compress the language/tool matrix (Node/TS, Python, Rust) — the AI can infer tool selection from project structure.

6. **Apply litmus test to remaining content** — For every line: teaches something non-obvious, sets a quality bar, or prevents a specific mistake. Trim filler. Ensure Invocation, Extract Intent, Context Scan, UI detection heuristic, nearby rules sniffing, and Visual Preview guidelines remain clear.

7. **Verification** — Confirm line count within target (~210 ±10%), run a mental execution to ensure no capability lost. Verify scope escalation flags are preserved as an explicit list, not summarized.

## Notes

**Technical considerations:**
- The agent prompt rewrite is the most judgment-intensive change. The six scope flags (5+ files, schema changes, core architecture, low test coverage, in-flight dependencies, new external deps) must remain explicit — they prevent silent scope creep.
- Experience gaps ("no empty state", "no error feedback", "no loading indicator") are non-obvious — the AI might ship silently without this concept. Preserve it.
- Visual Preview step is well-written and innovative; don't compress it aggressively. The canvas guidelines and "what the canvas is NOT" are high-value.

**Risks:**
- Agent prompt losing scope detection nuance if principles are too abstract. The six flags are the crown jewels — keep them verbatim.
- Over-consolidation of output formats could leave the agent unsure when to show escalation vs success. Make the branching logic explicit.

**Watch for:**
- `agents/coding-agent.md` reference and prototype mode behavior must remain clear.
- The comparison table against `/implement-story --quick` is valuable disambiguation — keep it intact.
- Design tokens / Figma MCP detection in Context Scan — trim if verbose, but preserve the concept.

## Definition of Done

- [ ] All tasks completed
- [ ] All acceptance criteria met
- [ ] Line count within target range (~210 ±10%)
- [ ] No functional capability lost
- [ ] Scope escalation flags preserved as explicit list
