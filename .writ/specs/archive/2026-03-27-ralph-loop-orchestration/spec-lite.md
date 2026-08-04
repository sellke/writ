# Ralph Loop Orchestration (Lite)

> Source: .writ/specs/2026-03-27-ralph-loop-orchestration/spec.md
> Purpose: Efficient AI context for implementation

## For Coding Agents

**Deliverable:** Ralph loop — epic-level autonomous execution across Writ specs via CLI, with Cursor-based planning and file-based state persistence.

**Implementation Approach:**
- `/ralph plan` (Cursor): scan specs, resolve dependencies, assess codebase, generate execution plan + CLI handoff artifacts (PROMPT files, ralph.sh)
- `/ralph status` (Cursor): read state files, present progress/blockers/results
- CLI pipeline: PROMPT_build.md instructs CLI agent to execute one story per iteration (code → test → lint → commit)
- State: `.writ/state/ralph-*.json` updated every iteration, survives context resets

**Files in Scope:**
- `commands/ralph.md` — plan + status modes
- `scripts/ralph.sh` — loop script template
- `.writ/docs/ralph-state-format.md` — state format reference
- `.writ/docs/ralph-cli-pipeline.md` — CLI pipeline reference
- `.writ/docs/config-format.md` — add Ralph config section
- `adapters/claude-code.md` — add Ralph execution guidance

**Key Architecture:**
- Three nested loops: Ralph (epic, fresh context) → story pipeline (CLI gates) → fix loop (test retry, max 3)
- Dependency graph = hard constraints; Ralph assessment = soft navigation within constraints
- One story per iteration. Story is atomic: completes or fails as unit.

---

## For Review Agents

**Acceptance Criteria:**
1. `/ralph plan` scans 3+ specs, resolves cross-spec dependencies, produces valid execution plan
2. Handoff artifacts (PROMPT files, ralph.sh) are generated and tailored to project's tech stack
3. State file format captures: iteration count, story results, blockers, files changed, test outcomes
4. `/ralph status` presents human-readable progress from state files
5. CLI pipeline PROMPT instructs code → test → lint → commit with back pressure
6. Failed stories logged with diagnostics, retried or skipped on subsequent iterations

**Business Rules:**
- Dependency graph ordering is mandatory — never attempt Story B before dependency Story A completes
- Plan is disposable — regenerate anytime from current codebase reality
- State files are single source of truth (not context window memory)
- `/plan-product` = strategic (what to build); `/ralph plan` = tactical (execution order for existing specs)
- `/implement-story` unchanged — Ralph's CLI pipeline is parallel path, not replacement

**Experience Design:**
- Entry: `/ralph plan` in Cursor after specs exist
- Happy path: plan → handoff → CLI loop → return to Cursor for review
- Error: blocker → log diagnostics → stop or skip → developer reviews in Cursor
- Feedback: state files + git commits as progress markers

---

## For Testing Agents

**Success Criteria:**
1. Multi-spec execution plan respects dependency ordering (zero out-of-order attempts)
2. State files enable resume after interruption (crash, stop, context reset)
3. CLI pipeline produces code passing tests + lint autonomously
4. Escalation triggers only on genuine blockers (<10% of iterations)
5. Cursor→CLI→Cursor round-trip: state from CLI readable in Cursor `/ralph status`

**Shadow Paths to Verify:**
- **Happy path:** Plan 3 specs → CLI executes all stories → complete state file
- **Dependency blocked:** Story attempted before dependency → correctly skipped/deferred
- **Story failure:** CLI pipeline fails → state records failure → next iteration picks different story
- **Environment broken:** Test runner crashes → Ralph stops (not infinite retry)

**Edge Cases:**
- No eligible specs found → `/ralph plan` reports "nothing to plan"
- All stories blocked → loop stops with escalation report
- State file corrupted → loop starts fresh (regenerate from git + spec state)
- Story exceeds context window → treated as failure, logged, skipped
