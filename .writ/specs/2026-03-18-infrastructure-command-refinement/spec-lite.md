# Infrastructure Command Refinement — Spec Lite

> Source: spec.md
> Purpose: Efficient AI context for implementation

## What We're Building

Refine 3 infrastructure Writ commands (migrate, prisma-migration, test-database) from mixed B-/B to all-A by applying the same litmus test used in all prior refinement specs: every line must teach the AI something non-obvious, set a quality bar, or prevent a specific mistake. Templates become principles. ~59% line reduction, zero capability lost.

## The Litmus Test

For every line in every file: (1) teaches something non-obvious, (2) sets a quality bar the AI wouldn't reach alone, (3) prevents a specific mistake — or it gets cut.

## Key Changes

- **migrate:** Cut Phase 2 bash scripts (mv/sed/find — AI knows file operations), one-liner migration script, verbose FAQ. Replace with principles about what to rename, verify, and preserve. Keep what-changes/what-doesn't tables, integrity verification, rollback, platform detection. 371 → ~160 lines.
- **prisma-migration:** Cut dialog mockups (~100 lines), JSON todo block, Future Enhancements, Integration Notes, Best Practices naming section, verbose bash that restates Prisma CLI behavior. Keep setup detection heuristics, safety check logic, dev/prod separation branching, deployment options, error scenarios as principles. 667 → ~260 lines.
- **test-database:** Cut AI Implementation Prompt (restates process), JSON todo block, Future Enhancements, verbose status report templates, bash pseudocode. Keep multi-layer testing approach (Docker → Prisma → App), safe/destructive fix classification, diagnostic logic, actionable recovery principles. 422 → ~180 lines.

## Files in Scope

commands/migrate.md, commands/prisma-migration.md, commands/test-database.md

## Key Constraints

- Same litmus test and simplification principle as all prior refinement specs
- migrate's what-changes/what-doesn't tables are the migration contract — preserve fully
- prisma-migration's setup detection heuristics and safety check matrix are the organizing spine
- test-database's safe vs destructive classification boundary is genuinely non-obvious — keep prominent
- test-database's three-layer model (Docker → Prisma → App) structures all diagnostics

## Success Criteria

- All sections pass the litmus test
- ~600 total lines (from ~1,460)
- No cross-reference breakage (prisma-migration → test-database)
- Zero functional capability lost
- Consistent voice and density with already-refined commands
