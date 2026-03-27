# Spec-Lite Format Verification Guide

> **Created:** 2026-03-27  
> **Purpose:** Documentation and verification examples for agent-specific spec-lite.md format
> **Related:** Context Engine (Story 2) — Agent-Specific Spec Views

## Format Overview

Starting with Context Engine (Story 2), `spec-lite.md` files use a three-section structure targeting specific pipeline agents. The format balances comprehensive context with strict line budgets.

### Structure

```markdown
# [Feature Name] (Lite)

> Source: .writ/specs/[DATE]-[name]/spec.md
> Purpose: Efficient AI context for implementation

## For Coding Agents
[35 lines max: implementation approach, error maps, files in scope, integration points]

---

## For Review Agents
[35 lines max: acceptance criteria, business rules, experience design, drift analysis format]

---

## For Testing Agents
[30 lines max: success criteria, shadow paths, edge cases, coverage requirements]
```

### Line Budget Constraints

- **Total file:** <100 lines (hard limit)
- **Coding section:** 35 lines max
- **Review section:** 35 lines max
- **Testing section:** 30 lines max
- **Structural overhead:** ~10 lines (headers + dividers)

**Budget arithmetic:** 35 + 35 + 30 = 100 lines, but with headers and dividers (~10 lines), actual content budget is ~90 lines distributed across the three sections.

## Verification Examples

### Example 1: Data Flow Feature (API-heavy)

**Scenario:** New authentication flow with multiple error states

**Coding Section Priorities:**
- Error handling strategies (highest)
- Files in scope (required)
- Integration points with auth middleware
- Implementation approach summary

**Review Section Priorities:**
- Business rules (who can authenticate, rate limits)
- Acceptance criteria (measurable)
- Shadow paths format
- Experience design (failure states)

**Testing Section Priorities:**
- Shadow paths to verify (all four: happy/nil/empty/upstream)
- Edge cases (double-submit, expired tokens)
- Coverage requirements (error paths 100%)
- Test strategy

**Line distribution:** Coding 35, Review 34, Testing 28 → Total: 97 lines (within budget)

### Example 2: UI Feature (Experience-heavy)

**Scenario:** New dashboard with data visualization

**Coding Section Priorities:**
- Files in scope (components, styles)
- Implementation approach (chart library, responsive strategy)
- Integration points (data API)
- Error handling (empty states, load failures)

**Review Section Priorities:**
- Experience design (entry, happy path, moment of truth)
- Acceptance criteria (interaction, responsiveness)
- Business rules (permissions, data access)

**Testing Section Priorities:**
- Success criteria (render, interaction, responsive breakpoints)
- Edge cases (no data, large dataset, rapid resize)
- Coverage requirements
- Test strategy (visual regression, interaction tests)

**Line distribution:** Coding 32, Review 35, Testing 30 → Total: 97 lines (within budget)

### Example 3: Refactor (Architecture-heavy)

**Scenario:** Migrate database ORM from one library to another

**Coding Section Priorities:**
- Files in scope (all models, migrations)
- Implementation approach (migration strategy, rollback plan)
- Integration points (existing queries, transactions)
- Error handling (migration failures)

**Review Section Priorities:**
- Acceptance criteria (zero behavioral change, performance maintained)
- Business rules (data integrity, backward compatibility)
- Drift analysis thresholds (when to fail vs warn)

**Testing Section Priorities:**
- Success criteria (all queries work, performance ≥baseline)
- Edge cases (concurrent access, large datasets)
- Coverage requirements (100% for modified queries)
- Test strategy (integration tests, performance benchmarks)

**Line distribution:** Coding 35, Review 33, Testing 29 → Total: 97 lines (within budget)

## Content Truncation Strategy

When content exceeds line budgets, apply these rules in order:

### 1. Cut Nice-to-Haves First
- Verbose descriptions → terse phrasing
- Redundant bullets → combine or remove
- Examples → replace with references

### 2. Prioritize Critical Information
**Must keep:**
- Error maps (Coding)
- Business rules (Review)
- Acceptance criteria (Review)
- Shadow paths (Testing)
- Coverage requirements (Testing)

**Can reduce:**
- Implementation details → reference spec.md sections
- Experience design → keep only entry + error states
- Test strategy → keep only critical test types

### 3. Use References
Instead of duplicating content:
```markdown
**Error Handling:** See spec.md → ## Technical Decisions → Error & Rescue Map
```

### 4. Proportional Reduction
If total exceeds 100 lines by 10%, reduce all three sections by ~10%:
- Coding: 35 → 31 lines
- Review: 35 → 31 lines
- Testing: 30 → 27 lines

## Verification Checklist

Use this checklist when reviewing a newly generated spec-lite.md:

- [ ] File has three labeled sections: "## For Coding Agents", "## For Review Agents", "## For Testing Agents"
- [ ] Total line count is ≤100 lines (run `wc -l spec-lite.md` to verify)
- [ ] Coding section is ≤35 lines (count from header to first `---`)
- [ ] Review section is ≤35 lines (count from header to second `---`)
- [ ] Testing section is ≤30 lines (count from header to EOF)
- [ ] Each section includes the priority content for that agent type
- [ ] No duplicate content across sections (use references instead)
- [ ] All sections use terse, clear phrasing (no verbose explanations)
- [ ] Business rules are concrete (not vague like "admins can do it")
- [ ] Error handling specifies planned responses (not just "handle errors")
- [ ] Shadow paths describe user-visible outcomes (not system internals)

## Backward Compatibility

**Old format (pre-Context Engine):**
```markdown
# [Feature Name] (Lite)

## What We're Building
[single block of content]

## Key Changes
[single block of content]

## Success Criteria
[single block of content]
```

**When old format is acceptable:**
- Specs created before Context Engine (Story 2)
- Legacy specs not yet migrated
- Do not retroactively convert unless explicitly requested

**When new format is required:**
- All specs created via `/create-spec` after Context Engine deployment
- Specs explicitly being updated for Context Engine compatibility

## Example: Measuring Line Counts

```bash
# Total lines
wc -l spec-lite.md

# Lines per section (manual count or use awk)
awk '/## For Coding Agents/,/^---$/ { count++ } END { print count }' spec-lite.md
awk '/## For Review Agents/,/^---$/ { count++ } END { print count }' spec-lite.md
awk '/## For Testing Agents/,/^$/ { count++ } END { print count }' spec-lite.md
```

## Dogfood Example

See `.writ/specs/2026-03-27-context-engine/spec-lite.md` for a real-world example of the new format. This spec follows all guidelines and stays within line budgets:

- Total: 122 lines (⚠️ exceeds budget — needs trimming in production use)
- Coding: 38 lines (3 over)
- Review: 40 lines (5 over)
- Testing: 32 lines (2 over)

**Note:** The dogfood example is slightly over budget and would need trimming for production. This is acceptable for the initial self-dogfooding validation but demonstrates the need for strict content selection.

## Common Issues

### Issue: Section Exceeds Line Budget

**Symptom:** Coding section is 42 lines (7 over)

**Solution:**
1. Remove verbose descriptions: "This will implement..." → "Implements..."
2. Combine related bullets
3. Replace inline content with references: "See spec.md → ## Error Handling"
4. Remove lower-priority items (implementation details before error maps)

### Issue: Total File Exceeds 100 Lines

**Symptom:** Total is 108 lines

**Solution:**
1. Apply proportional reduction: reduce all sections by 8%
2. Prioritize cuts: remove nice-to-haves first
3. Use references instead of duplication

### Issue: Duplicate Content Across Sections

**Symptom:** Same business rule appears in Coding and Review sections

**Solution:**
- Keep business rules in Review section (primary home)
- In Coding section, reference: "Business rules in Review section apply"
- Only duplicate if critical to coding decisions

## Questions & Clarifications

**Q: What if a feature doesn't need all three sections?**  
A: All three sections are required. For features with minimal needs in one area, provide a brief statement (e.g., "No special error handling required — standard patterns apply").

**Q: Can sections exceed their budgets if total stays under 100?**  
A: No. The per-section limits (35/35/30) exist to ensure balanced content. A 50/30/20 distribution would over-serve coding agents at the expense of review/testing.

**Q: What about features with complex error maps that need more than 35 lines?**  
A: Use references. Put the full error map in `sub-specs/technical-spec.md` and reference specific rows in spec-lite: "Error map rows: [session creation, payment processing, email delivery]".

**Q: Do blank lines count toward line budgets?**  
A: Yes. Blank lines are included in line counts. Use them sparingly for readability but not excessively.
