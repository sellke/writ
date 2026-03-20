# Command Suite Evolution — Technical Spec

> Spec: Command Suite Evolution
> Created: 2026-03-19
> Stories: 1–9

---

## Implementation Approach

All nine changes are edits to existing markdown command and agent files. No build step, no CLI, no runtime code. The methodology is: identify the exact lines to add/change/remove in each file, make the minimum change that achieves the behavior, verify by reading the result.

---

## New Files and Formats

### `.writ/config.md` (Story 1)

Introduced by `/initialize` on greenfield setup, or auto-written on first `/ship` run when conventions are detected. Format:

```markdown
# Writ Project Config

> Last Updated: YYYY-MM-DD
> Auto-generated — edit manually if needed

## Conventions

- **Default Branch:** main
- **Test Runner:** jest (detected: package.json scripts.test)
- **Merge Strategy:** squash
- **Version File:** package.json
- **Test Coverage Tool:** jest --coverage

## Paths

- **Changelog:** CHANGELOG.md
- **Writ Specs:** .writ/specs/
- **Writ Issues:** .writ/issues/
```

Commands that read config: check for `.writ/config.md` → if found, use values → if not found, detect → after detection, offer "Save to `.writ/config.md`? (y/n)".

Never auto-save without offering. Never overwrite without confirmation.

### `.writ/context.md` (Story 5)

Auto-generated summary file. Written by `/status`, `/implement-story` (at gate transitions), `/implement-spec` (on story completion). Format:

```markdown
# Writ Project Context

> Last Updated: YYYY-MM-DD HH:MM
> Auto-generated — do not edit manually

## Product Mission

[1-3 sentences from .writ/product/mission-lite.md, or "No mission document found"]

## Active Spec

- **Spec:** [spec identifier and title, or "No active spec"]
- **Current Story:** [story number + title, or "—"]
- **Progress:** [X/Y stories complete (Z%)]

## Recent Drift

[Last 3 entries from active spec's drift-log.md, or "No drift events recorded"]

## Open Issues

[N unresolved issues in .writ/issues/ (X need triage)]
```

**Regeneration rule:** Every write is a full file replace. No incremental patching. Source of truth for each section:
- Mission: `.writ/product/mission-lite.md` → first paragraph
- Active spec: most recently modified spec with non-Complete status
- Drift: active spec's `drift-log.md` → last 3 entries
- Issues: count `.writ/issues/**/*.md` where `spec_ref` is empty

---

## File-Level Changes

### Story 1: `commands/ship.md`, `commands/release.md`, `commands/status.md`, `commands/initialize.md`

**Pattern for ship.md and release.md — replace Step 1 (convention detection):**

```
Before: Auto-detect [convention] by running [commands]...
After:  Read from `.writ/config.md` if present. Key: [Convention Name].
        If not in config, detect via [commands]. After detection, offer: 
        "Detected [value]. Save to .writ/config.md? (y/n)"
```

**For initialize.md (greenfield):** After "verify the project runs" step, write `.writ/config.md` with detected values. No confirmation needed here — initialization is the natural save point.

**For status.md:** Add config read as the first operation. Use cached values for display. Offer save if config doesn't exist.

### Story 2: `agents/coding-agent.md`, `agents/testing-agent.md`, `commands/implement-story.md`

**Add to both agent files — self-fix section:**

```markdown
## Iteration Cap

MAX_SELF_FIX_ITERATIONS = 3. After 3 failed attempts to fix the same issue, 
stop and output:

STATUS: BLOCKED
AGENT: [coding-agent | testing-agent]
ATTEMPTS: 3
FAILURE: [specific description of what failed and why]
PARTIAL_STATE: [what was completed successfully before the block]
NEXT_STEP: Surface to orchestrator for human decision
```

**Add to implement-story.md — after each agent call:**

```markdown
If agent returns STATUS: BLOCKED, surface to user via AskQuestion:
- Retry (restart the gate with fresh context)
- Skip gate (continue with warning in final report)
- Abort pipeline (preserve current state)
```

### Story 3: `commands/verify-spec.md`

**Add Check 9 to the check suite:**

```markdown
**Check 9: Spec-Lite Integrity**
Compare key sections of spec-lite.md against spec.md:
- What We're Building / Contract Summary
- Key Constraints  
- Success Criteria
- Files in Scope

Flag as DIVERGED if sections differ materially (not just formatting).
Add to report: diff summary showing what changed.

With --fix flag: regenerate spec-lite.md from spec.md in full.
Mark regenerated file: "> Regenerated from spec.md on YYYY-MM-DD"
```

### Story 4: `commands/status.md`

**Remove all references to phantom commands:** commit-wip, sync-main, doctor, reset-deps, review-specs.

**Add sections:**
1. Config read (top of command) — use `.writ/config.md` for conventions display
2. In-flight jobs — check `.writ/state/execution-*.json`, report active batch job name + progress if found
3. Refresh opportunities — check `.writ/state/refresh-log.md` for commands with 3+ new transcripts; surface: "3 transcripts since last /refresh-command on implement-story"

**Suggested commands in output must only reference:** create-spec, implement-story, implement-spec, prototype, review, verify-spec, refresh-command, assess-spec, ship, release, plan-product, research, refactor, create-adr, create-issue, edit-spec, initialize, retro

### Story 5: `agents/coding-agent.md`, `agents/review-agent.md`, `agents/architecture-check-agent.md`, `commands/implement-story.md`, `commands/implement-spec.md`, `commands/status.md`

**Add to each agent's context loading section:**

```markdown
## Context Loading

Load in this order:
1. `.writ/context.md` — project context (mission, active spec, drift history, issues)
2. [spec-lite.md for active spec]
3. [story file]
4. [codebase patterns, related files]
```

**Add to implement-story.md and implement-spec.md — after any gate transition or story completion:**

```markdown
Regenerate `.writ/context.md`:
- Read .writ/product/mission-lite.md (first paragraph)
- Read active spec: identifier, current story, completion %
- Read active spec's drift-log.md (last 3 entries)
- Count .writ/issues/**/*.md where spec_ref is empty
- Write full file (always regenerate, never patch)
```

**Add to status.md:** Same regeneration step at end of status run.

### Story 6: `commands/prototype.md`, `commands/create-spec.md`

**Add to prototype.md — post-escalation section:**

```markdown
## Escalation Path

When scope escalation signals fire (>5 files, schema changes, core architecture, 
external dependencies), complete implementation but add post-completion offer:

"This grew beyond prototype scope — escalation signals detected:
[list signals]

The implementation is complete and in your working tree. Want to formalize it?
/create-spec --from-prototype will:
  - Create a spec using the current diff as context
  - Mark the prototype work as Story 1 (already complete)
  - Start discovery for Story 2+ (what comes next)

[Yes, formalize it] [No, leave as-is]"
```

**Add to create-spec.md — new mode before Phase 1:**

```markdown
## --from-prototype Mode

When invoked with --from-prototype:
1. Read current git diff (files changed, lines added/removed)
2. Read coding agent implementation summary if available in thread
3. Pre-populate discovery contract:
   - Deliverable: inferred from diff file names and summary
   - Files in scope: from diff
   - Implementation approach: from coding agent summary
   - Story 1: [prototype description] — Status: Completed ✅
4. Proceed with shortened discovery conversation focused on:
   "The prototype is done. What should Story 2+ build on top of it?"
5. Phase 2 creates spec with Story 1 pre-marked complete
```

### Story 7: `commands/create-spec.md`, `commands/create-issue.md`, `commands/status.md`

**Add to create-spec.md — new mode:**

```markdown
## --from-issue [path] Mode

When invoked with --from-issue:
1. Read the issue file at [path]
2. Extract: type (bug/feature/improvement), description, affected files, priority
3. Pre-populate discovery contract with issue context:
   - If bug: deliverable = "Fix [description]", entry point = affected files
   - If feature/improvement: deliverable = [description], scope = affected files
4. Proceed with normal discovery conversation — issue context anchors it, not replaces it
5. After spec creation, write back to issue file:
   spec_ref: .writ/specs/[date]-[slug]/spec.md
```

**Add to create-issue.md — issue template:**

```markdown
Add field to issue template:
- spec_ref: (leave empty — filled when issue is promoted to spec)
```

**Add to status.md — "Needs Triage" section:**

```markdown
## Needs Triage

Issues older than 7 days with no spec_ref:
- [date] [type] [slug] — [1-line description]
  → /create-spec --from-issue .writ/issues/[type]/[filename].md

(omit section if no untriaged issues)
```

### Story 8: `commands/plan-product.md`, `commands/create-adr.md`

**Update plan-product.md Phase 2:**

```markdown
Replace: Generate `decisions.md` with key decisions from the discovery conversation
With:    Generate ADR files for each major decision surfaced in discovery:
         - ADR-000: [Product posture decision]
         - ADR-001: [Market focus / target user decision]
         - ADR-002: [Positioning / differentiator decision]
         Use /create-adr format. Store in .writ/decision-records/.
         These are the foundational ADRs for the product.
         
Note: Existing decisions.md files in existing projects are not modified.
```

**Update create-adr.md — add context note:**

```markdown
## ADR Families

**Product-level ADRs (000-series):** Seeded by /plan-product during product 
discovery. Cover: posture, market focus, positioning. These are foundational 
and change rarely.

**Technical ADRs (sequential from 001 or after product ADRs):** Created via 
/create-adr for architectural, infrastructure, and implementation decisions.

If your project has a decisions.md from an earlier plan-product run, you can 
create ADRs to formalize those decisions — but migration is optional.
```

### Story 9: `commands/refresh-command.md`

**Add --batch mode documentation:**

```markdown
## --batch Mode

/refresh-command --batch [command-name] [--n 5]

Analyzes the last N transcripts (default: 5) for [command-name]:

Phase 2b (batch): Instead of one transcript → N transcripts in parallel
  - Spawn one analysis agent per transcript (same Phase 3 signal extraction)
  - Collect all signals into a cross-session pattern matrix
  - Identify patterns appearing in 2+ sessions: these are recurring friction
  - Weight by recurrence: 2/5 = low, 3/5 = medium, 4/5 = high, 5/5 = critical

Amendment proposals (Phase 4b):
  - Each amendment includes: "Observed in N/M sessions"
  - Sort proposals by recurrence (most frequent first)
  - Confidence for promotion: frequency × single-session confidence
  - "Appeared in 5/5 sessions, high confidence" → auto-promote candidate

Auto-trigger condition (surfaced in /status):
  Count transcripts for [command] since last refresh-log.md entry.
  If count ≥ 3: surface "3 new /implement-story sessions since last refresh — 
  consider: /refresh-command --batch implement-story"
```

---

## Cross-Reference Updates

After implementing all 9 stories, update cross-references in:
- `commands/implement-story.md` → references to coding-agent, testing-agent (BLOCKED status handling)
- `agents/user-story-generator.md` → no changes needed
- `README.md` (if it lists commands) → no file additions, only behavior changes

---

## Error Mapping

| Operation | What Can Fail | Planned Handling |
|---|---|---|
| Read `.writ/config.md` | File doesn't exist | Fall back to detection, offer to save |
| Write `.writ/config.md` | Permission error | Warn, continue without saving |
| Read `.writ/context.md` | File doesn't exist | Skip gracefully, agent continues without it |
| Regenerate context.md | Source files missing | Use empty/default values for missing sections |
| `--fix` spec-lite regeneration | spec.md not found | Error: "No spec.md found at expected path" |
| `--from-issue` mode | Issue file not found | Error: "File not found: [path]" |
| `--from-prototype` mode | No git diff | Warn: "No changes detected in working tree" |
| BLOCKED agent escalation | User aborts | Pipeline aborts cleanly, partial state preserved |
| Batch transcript analysis | Fewer than N transcripts | Analyze available transcripts, note count |

---

## Story Traceability

| Story | Recommendation | Audit Plan Ref |
|---|---|---|
| 1 | Config Persistence | Rec 1 (Efficiency) |
| 2 | Iteration Caps | Rec 7 (Reliability) |
| 3 | Spec-Lite Check | Rec 5 (Intelligence) |
| 4 | Status Rewrite | Rec 8 (Context) |
| 5 | Context Auto-Loading | Rec 4 (Context+Intelligence) |
| 6 | Prototype Escalation | Rec 6 (Automation) |
| 7 | Issue→Spec | Rec 3 (Automation+Separation) |
| 8 | ADR Unification | Rec 9 (Separation) |
| 9 | Batch Refresh | Rec 2 (Intelligence) |
