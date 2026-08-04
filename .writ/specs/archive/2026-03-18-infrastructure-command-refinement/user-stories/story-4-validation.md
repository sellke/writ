# Story 4: Validation

> **Status:** Not Started
> **Priority:** P1
> **Dependencies:** Stories 1, 2, 3
> **Estimated effort:** Medium

## User Story

As a Writ maintainer, I want a comprehensive validation of all three refined files so that I can confirm they meet A grade with zero capability loss.

## Acceptance Criteria

- Given all three refined files, when line counts are audited, then each falls within its target range
- Given all three refined files, when the litmus test is applied section-by-section, then zero lines fail
- Given all three refined files, when cross-references are checked, then all paths and command references resolve
- Given all three refined files, when capabilities are compared before/after, then zero capabilities are lost
- Given all three refined files, when voice and density are compared to A-grade benchmarks, then all match
- Given the validation results, when compiled into a report, then the report follows the format established by prior refinement validation reports

## Implementation Tasks

- [ ] Task 1: Line count audit — measure each file, verify within target range, calculate total reduction percentage
- [ ] Task 2: Section-by-section litmus test — for each file, test every section against the three criteria; document verdicts in a table
- [ ] Task 3: Cross-reference check — verify all file paths (.writ/*, commands/*, agents/*), command references (/test-database, etc.), and external references resolve
- [ ] Task 4: Capability comparison — build before/after capability table for each file; confirm zero loss, flag intentional changes
- [ ] Task 5: Voice and density comparison — compare all three files against assess-spec.md and edit-spec.md benchmarks using the standard pattern checklist

## Technical Notes

- Follow the exact validation report format from prior specs (see .writ/specs/2026-03-18-utility-command-refinement/validation-report.md and .writ/specs/2026-03-18-secondary-command-refinement/validation-report.md)
- The validation report goes in .writ/specs/2026-03-18-infrastructure-command-refinement/validation-report.md
- Cross-references to check: prisma-migration → /test-database, test-database → docs, migrate → install.sh patterns
- Benchmark files for voice comparison: commands/assess-spec.md (203 lines), commands/edit-spec.md (118 lines)

**Target ranges:**
- migrate.md: 144–176 lines (target ~160)
- prisma-migration.md: 234–286 lines (target ~260)
- test-database.md: 162–198 lines (target ~180)
- Total: ~600 lines (from ~1,460)

## Definition of Done

- [ ] Validation report created with all 5 tasks
- [ ] All 5 tasks pass
- [ ] Report follows established format from prior refinement specs
- [ ] Overall verdict is ✅ PASS with all three files confirmed at A grade
