# Suite Quality Polish Specification

> Created: 2026-03-22
> Status: Complete
> Contract Locked: ✅

## Contract Summary

**Deliverable:** Targeted quality fixes across 5 areas to bring the command/agent suite from A- to A+

**Must Include:** `/explain-code` rewrite (the only C+ in the suite), agent input consistency, verify-spec renumbering

**Hardest Constraint:** `/explain-code` rewrite is the largest change — everything else is surgical edits

**Success Criteria:** All commands follow established patterns, no broken markdown, no references to non-existent features, consistent agent input contracts

**Scope Boundaries:**
- Included:
  1. Rewrite `/explain-code` to match suite patterns
  2. Add `context_md_content` to Testing Agent and Documentation Agent
  3. Renumber `/verify-spec` checks from 1-5,8,9 → 1-7
  4. Replace OpenClaw cron example in `/security-audit` with platform-agnostic note
  5. Move `/prisma-migration` and `/test-database` to `contrib/`
- Excluded: New features, behavioral changes, changes to core pipeline commands

## Detailed Requirements

### 1. `/explain-code` Rewrite

The current command has:
- Broken markdown (unclosed code blocks at lines 267-270)
- References to non-existent sub-commands (`/list-explanations`, `/search-explanations`, `/explanation-history`, `/refresh-explanations`)
- Claims about non-existent IDE features (hover tooltips, right-click context menu)
- A "Future Enhancements" section with aspirational features
- Auto-save to `.writ/explanations/` for every query (file bloat)
- No contract-first pattern, no Integration with Writ table, no clear phases
- Overly rigid output (mandates Mermaid diagrams for everything)

Rewrite to:
- Follow the command structure pattern (Overview, Invocation table, Command Process with steps, Integration with Writ table)
- Remove all references to non-existent features
- Fix broken markdown
- Make output adaptive (diagrams when helpful, not mandatory)
- Remove auto-save default — print to conversation, offer to save if useful
- Keep it focused: explain code, show relevant context, done

### 2. Agent Input Consistency

Testing Agent (`agents/testing-agent.md`) and Documentation Agent (`agents/documentation-agent.md`) are missing `context_md_content` in their Input Requirements tables. Architecture Check, Coding, and Review agents all have it as the first parameter.

Add to both agents:
- `context_md_content` parameter in the Input Requirements table with description: "**First context item.** Contents of `.writ/context.md` if present — product mission, active spec state, recent drift. Pass empty string if file doesn't exist yet."
- Add `{context_md_content}` injection point in their Prompt Templates
- Add a `## Project Context` section at the top of the prompt, matching the pattern used by the other three agents

### 3. `/verify-spec` Check Renumbering

Current checks: 1, 2, 3, 4, 5, 8, 9 (skipping 6 and 7). This is confusing.

Renumber to sequential 1-7:
- Check 1: Story File Integrity (was 1)
- Check 2: Status Consistency (was 2)
- Check 3: Completion Integrity (was 3)
- Check 4: Dependency Validation (was 4)
- Check 5: Deliverables Checklist (was 5)
- Check 6: Spec Contract vs Implementation (was 8)
- Check 7: Spec-Lite Integrity (was 9)

Update all references to these check numbers throughout the file, including the Phase 3 report table, Phase 4 auto-fix section, and the Integration with Writ table. Also update any cross-references in other commands that mention specific check numbers (e.g., `/ship` references "checks 1-3", `/release` references "checks 1-5 and 8").

### 4. `/security-audit` Platform-Agnostic Fix

Replace the OpenClaw-specific cron example (lines ~493-501) with a platform-agnostic scheduling note. Remove the `openclaw cron add` command and replace with general guidance about scheduling periodic audits using whatever platform scheduling mechanism is available.

### 5. Move Project-Specific Commands to `contrib/`

Move `commands/prisma-migration.md` and `commands/test-database.md` to a new `contrib/` directory. These are project-specific utilities that shouldn't ship as core Writ commands. Update any cross-references in other commands or the `/status` command allowlist.

Keep `/migrate` in `commands/` — it's part of the install/onboarding story for users migrating from Code Captain.

## Implementation Approach

All changes are markdown file edits. No application code, build steps, or tests involved. Changes should be committed incrementally per story.
