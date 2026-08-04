# Remaining Command Refinement — Spec Lite

> Source: spec.md
> Purpose: Efficient AI context for implementation

## What We're Building

Refine 4 remaining Writ commands (new-command, refactor, review, retro) from mixed B-/B/B+ to all-A by applying the same litmus test used in the core, secondary, and utility refinement specs: every line must teach the AI something non-obvious, set a quality bar the AI wouldn't reach alone, or prevent a specific mistake. Templates become principles. ~47% line reduction, zero capability lost.

## The Litmus Test

For every line in every file: (1) teaches something non-obvious, (2) sets a quality bar the AI wouldn't reach alone, (3) prevents a specific mistake — or it gets cut.

## Key Changes

- **new-command:** Cut AI Implementation Prompt (restates process), Template Selection Logic (hardcoded line numbers that break), Implementation Details, Future Enhancements. Keep contract-first discovery workflow and critical analysis pushback. 438 → ~200 lines.
- **refactor:** Cut ~100 lines of bash examples per mode (replace with principles about what to detect). Collapse 5 mode-specific workflows that repeat scan→propose→execute→verify into one principle. Keep safety guarantees, baseline verification, commit-per-change. 416 → ~220 lines.
- **review:** Lightest touch — already tight. Cut pipeline comparison table, error handling, command routing. Preserve all 5 techniques, severity classification, "Recommendation is the soul" quality bar. 292 → ~200 lines.
- **retro:** Cut JSON schema templates (~75 lines), output markdown templates (~60 lines), detailed bash commands (~35 lines). Keep session detection heuristics, Ship of the Week selection, opinionated pattern guidance, tweetable forcing function. 455 → ~220 lines.

## Files in Scope

commands/new-command.md, commands/refactor.md, .cursor/commands/review.md, .cursor/commands/retro.md

## Key Constraints

- Same litmus test and simplification principle as all prior refinement specs
- Review's 5 structured techniques are the organizing spine — compress prose, not technique substance
- Retro's session detection and pattern heuristics encode real algorithmic judgment — express as principles, not pseudocode
- Refactor's safety guarantees (baseline, verify-per-change, rollback, commit-per-change) are genuinely non-obvious — keep prominent
- New-command's contract-first discovery workflow follows the Writ crown jewel pattern — preserve fully

## Success Criteria

- All sections pass the litmus test
- ~840 total lines (from ~1,601)
- No cross-reference breakage (review → ship, refactor → create-adr, retro → .writ/retros/)
- Zero functional capability lost
- Consistent voice and density with already-refined commands
