# Technical Specification: Core A-Grade Refinement

> Created: 2026-03-18

## Architecture

This spec modifies instruction files (markdown), not runtime code. There are no database changes, API changes, or dependency additions. The "architecture" is the relationship between command files and the agent files they reference.

## File Dependency Map

```
plan-product.md ──────────────────────────────────── (standalone command)
create-spec.md ───→ agents/user-story-generator.md   (spawns for story creation)
implement-spec.md ──→ implement-story.md              (calls per-story)
implement-story.md ──→ agents/architecture-check-agent.md  (Gate 0)
                   ──→ agents/coding-agent.md               (Gate 1)
                   ──→ agents/review-agent.md               (Gate 3)
                   ──→ agents/testing-agent.md              (Gate 4)
                   ──→ agents/visual-qa-agent.md            (Gate 4.5, unchanged)
                   ──→ agents/documentation-agent.md        (Gate 5)
```

## Cross-Reference Integrity

The primary breakage risk is between implement-story.md and the agents it references. Key cross-references to verify:

| Source | Reference | Target |
|--------|-----------|--------|
| implement-story.md Gate 0 | "Agent: agents/architecture-check-agent.md" | architecture-check-agent.md |
| implement-story.md Gate 1 | "Agent: agents/coding-agent.md" | coding-agent.md |
| implement-story.md Gate 3 | "Agent: agents/review-agent.md" | review-agent.md |
| implement-story.md Gate 3.5 | References drift severity tiers | review-agent.md drift analysis section |
| implement-story.md Gate 4 | "Agent: agents/testing-agent.md" | testing-agent.md |
| implement-story.md Gate 5 | "Agent: agents/documentation-agent.md" | documentation-agent.md |
| implement-story.md Gate 3.5 | "Format reference: .writ/docs/drift-report-format.md" | drift-report-format.md (not in scope, must stay consistent) |
| implement-spec.md | "calls /implement-story" | implement-story.md invocation table |
| create-spec.md | "See agents/user-story-generator.md" | user-story-generator.md (unchanged) |

## Change Surface by File

| File | Change Type | Risk |
|------|------------|------|
| plan-product.md | Heavy rewrite (Phase 2) | Low — Phase 2 is file creation, not pipeline logic |
| create-spec.md | Heavy rewrite (Phase 2) | Low — same reasoning |
| implement-spec.md | Light edit (pre-flight) | Very low — orchestration logic untouched |
| implement-story.md | Medium rewrite (Gate 3.5) | Medium — drift handling is a safety mechanism |
| review-agent.md | Heavy rewrite (checklist) | Medium — review quality could degrade if principles too vague |
| coding-agent.md | Light edit (scope detection) | Very low — removing unused section |
| documentation-agent.md | Restructure (default-first) | Low — same content, different ordering |
| architecture-check-agent.md | Light edit (examples) | Very low — compression only |
| testing-agent.md | Light edit (detection) | Very low — removing recipes AI doesn't need |

## Rollback Strategy

All changes are to markdown files tracked in git. If any file's refinement degrades quality:

1. `git diff commands/[file].md` or `git diff agents/[file].md` to see changes
2. `git checkout commands/[file].md` to revert a single file
3. No cascading effects — each file can be independently reverted
