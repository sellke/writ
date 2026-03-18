# Technical Spec: Remaining Command Refinement

> Parent: `.writ/specs/2026-03-18-remaining-command-refinement/spec.md`

## Overview

Pure text refinement of 4 markdown command files. No code changes, no database, no API, no UI. The technical challenge is applying a consistent quality heuristic (the litmus test) to reduce line count while preserving all functional capability.

## Files Modified

| File | Location | Current | Target |
|------|----------|---------|--------|
| new-command.md | `commands/new-command.md` | 438 | ~200 |
| refactor.md | `commands/refactor.md` | 416 | ~220 |
| review.md | `.cursor/commands/review.md` | 292 | ~200 |
| retro.md | `.cursor/commands/retro.md` | 455 | ~220 |

### Location Note

`review.md` and `retro.md` are in `.cursor/commands/` (Cursor adapter layer). In the Writ repo, `.cursor/` is symlinked to product source — edits are edits to the product. No special handling needed; edit in place.

## Refinement Pattern (Proven in 3 Prior Specs)

Each file follows the same transformation:

1. **Read current file** — verify line numbers, identify sections by litmus test classification
2. **Cut sections that fail all 3 litmus tests** — templates, JSON schemas, bash scripts, hardcoded references, generic advice, redundant summaries
3. **Compress sections that partially pass** — keep the non-obvious principle, cut the procedural scaffolding
4. **Preserve sections that pass cleanly** — quality bars, judgment calls, heuristics, decision gates, safety guarantees
5. **Verify** — litmus test every remaining line, check cross-references, count lines

## Cross-References to Preserve

| Reference | File | What It Does |
|-----------|------|-------------|
| `.writ/state/review-[branch].md` | review.md | Review writes report, `/ship` reads it |
| `/create-adr` | refactor.md | Auto-create ADR for significant architectural refactors |
| `.writ/retros/YYYY-MM-DD.json` | retro.md | Snapshot persistence for trend comparison |
| `.writ/retros/trends.json` | retro.md | Rolling averages across periods |
| `.writ/specs/` | retro.md | Spec context for `--spec` flag |
| `.writ/refresh-log.md` | retro.md | Command refresh data for Writ integration |
| `/create-spec` error mapping | review.md | Shared table format for plan-vs-actual comparison |

## Quality Benchmarks

Already-refined commands to use as voice/density reference:

| File | Lines | Grade |
|------|-------|-------|
| commands/assess-spec.md | ~203 | A |
| commands/edit-spec.md | ~118 | A |

Refined files should match these benchmarks in: sentence length, table-vs-prose ratio, principle-vs-prescription balance, section structure (Overview, Invocation, Command Process, Notes/Integration), and information density per line.

## Validation Protocol

Story 5 performs 5 checks against each refined file:

1. **Line count** — within ±10% of target
2. **Litmus test** — every line passes at least one of the three criteria
3. **Cross-references** — all paths resolvable, all integrations intact
4. **Capability preservation** — before/after matrix shows zero functional loss
5. **Voice/density** — consistent with A-grade benchmarks

Results documented in `validation-report.md` at the spec root.

## Traceability

| Story | File | Key Preservation Targets |
|-------|------|------------------------|
| Story 1 | new-command.md | Contract-first discovery, critical analysis, pushback phrasing |
| Story 2 | refactor.md | Safety guarantees, baseline verification, mode detection targets, commit-per-change |
| Story 3 | review.md | 5 techniques, severity classification, "Recommendation is the soul", ship integration |
| Story 4 | retro.md | Session heuristics, Ship of the Week, pattern guidance, tweetable, spec-scoping |
| Story 5 | All 4 files | Litmus test, cross-references, capabilities, voice/density |
