# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/),
and this project adheres to [Semantic Versioning](https://semver.org/).

## [0.5.0] - 2026-03-19

### Changed

- **Pipeline streamlining** (`/verify-spec`, `/ship`, `/release`) — each command owns one job. `/verify-spec` is a metadata-only diagnostic (checks 1–5 and 8) with default auto-fix; `/ship` skips tests unless `/ship --test`; `/release` runs an inline gate (spec validation, build probes when configured, conditional full test suite via `gh` merge-commit vs `HEAD`) before changelog work. Added `/release --skip-gate`. README command summaries aligned.
- **Migration docs** — `SKILL.md` and `commands/migrate.md` updated for the new flow (no `--pre-deploy` / Trello).

## [0.4.4] - 2026-03-19

### Fixed

- `unlink.sh` crashing with `unbound variable` on bash 3.2 (macOS default) when `DIR_SYMLINKS` array is empty — `set -u` treats `"${arr[@]}"` on an empty array as unbound. Fixed all four array iterations to use the `${arr[@]+"${arr[@]}"}` safe expansion pattern.

## [0.4.3] - 2026-03-19

### Removed

- **Symlink install mode** — `install.sh --link` is no longer offered. Copy mode is the only installation method for external users. Linked installations posed risks around shared mutable state and non-portable `.cursor/` directories.
- Link mode update handler in `update.sh` — now errors with guidance to convert via `unlink.sh`
- README "Link mode (power users)" section and "Copy vs Link" callout

### Added

- `scripts/unlink.sh` — converts existing symlinked Writ installations to independent file copies with manifest rewrite, supporting both per-file and directory-level symlinks
- `/migrate` entry in README command table (was documented in migration section but missing from the table)

### Changed

- `install.sh` retains defensive symlink-removal when it detects an existing linked installation, ensuring a clean conversion to copy mode
- `update.sh` rejects linked installations with a clear error pointing to `unlink.sh`

## [0.4.2] - 2026-03-19

### Fixed

- `install.sh` and `update.sh` `overlay_scan` silently exiting on `set -e` when the last file alphabetically needed an update — `[ "$mode" = "apply" ] && cp ...` returns exit code 1 in preview mode, which became the function's return value and killed the script. Replaced all `[ ... ] && ...` conditionals with `if/fi` blocks. Affected copy-mode install and update on all platforms.

## [0.4.1] - 2026-03-18

### Added

- **README freshness check in `/release`** — new Step 1.3 cross-references `README.md` against the repo before each release, catching silent staleness in command tables, agent tables, pipeline diagrams, and install URLs. Structural drift detection only; semantic accuracy remains a human judgment call.

## [0.4.0] - 2026-03-18

### Changed

- **A-Grade Command Refinement** — 12 commands refined across 4 spec batches, applying the litmus test: every line must teach something non-obvious, set a quality bar, or prevent a specific mistake — or it gets cut. Templates become principles. Net reduction of ~2,700 lines, zero capability lost.
  - `assess-spec` and `edit-spec` — continued core refinement; compressed assessment tables, replaced edit-spec templates with principles (-633 lines)
  - `initialize`, `research`, `create-adr` — utility commands refined ~57%; cut duplicate next-steps blocks, replaced 86-line document template and 155-line ADR template with principles, converted auto-execute research to prerequisite gate
  - `create-issue`, `design`, `prototype` — secondary commands refined ~47%; cut Excalidraw JSON schema and component primitives, rewrote 80-line agent prompt to 25 lines of principles
  - `new-command`, `refactor`, `review`, `retro` — remaining commands refined ~47%; collapsed 5 mode-specific refactor workflows into one principle, cut JSON/markdown templates and bash pseudocode

### Removed

- Verbose templates in all 12 commands — replaced with concise principles the AI can generalize from
- Redundant "AI Implementation Prompt," "Best Practices," "Common Pitfalls," "Future Enhancements," and "Integration Notes" sections across all refined commands
- Hardcoded line-number references in `new-command` template selection logic (broke on any edit)
- Excalidraw JSON schema and component primitive definitions in `design` (the AI knows SVG primitives)
- Dialog mockups and bash pseudocode that restated CLI behavior the AI already knows

### Added

- Refinement specs for 4 command groups: utility, secondary, remaining, infrastructure (Specs: `2026-03-18-*-command-refinement`)
- Infrastructure command refinement spec for the next batch (migrate, prisma-migration, test-database) — planning documentation, not yet implemented

## [0.3.0] - 2026-03-18

### Changed

- **Core A-Grade Refinement** — all 9 core command and agent files refined from mixed B-/B/B+/A- grades to A-grade quality (Spec: `2026-03-18-core-agrade-refinement`)
  - Templates replaced with principles — the AI knows how to format; tell it what matters
  - `/plan-product` reduced 56% (623 → 272 lines) — Phase 1 discovery preserved intact, Phase 2 templates replaced with principles
  - `/create-spec` reduced 43% (805 → 458 lines) — discovery phase untouched, file-creation templates condensed to principled guidance
  - `/implement-story` reduced 39% (469 → 285 lines) — drift response rewritten from 117 procedural lines to ~40 lines of principles
  - `/implement-spec` reduced 17% (294 → 244 lines) — already near A-grade, minor tightening
  - Review agent: 31-item checklist → 5 categorized review dimensions; examples condensed 50%
  - Documentation agent: framework-specific sections (VitePress, Docusaurus, Nextra, MkDocs, Storybook) replaced with single "follow detected conventions" principle
  - Coding agent: verbose scope detection heuristic → single-paragraph principle
  - Architecture-check and testing agents: condensed examples and removed redundant sections
- Clean testing boundaries between `/implement-spec` and `/verify-spec` — clarified which command owns test execution vs. verification

### Removed

- Redundant "Key Improvements," "Best Practices," "Tool Integration," and "Integration with Writ Ecosystem" sections from all commands
- `SwitchMode` API calls replaced with natural language guidance (Cursor doesn't support programmatic mode switching)
- Verbose output format examples in review and documentation agents — one example demonstrates judgment, not three

## [0.2.0] - 2026-03-16

### Added

- `/assess-spec` command — pre-implementation health check that flags oversized stories, deep dependency chains, context accumulation risks, and file-overlap conflicts with specific decomposition recommendations
- Pre-flight assessment hook in `/implement-spec` (Step 2.3b) — runs lightweight sizing checks automatically before showing the execution plan, with option to hand off to full `/assess-spec`
- AI workflow best practices research (`.writ/research/2026-03-16-ai-workflow-best-practices-research.md`) with self-challenge appendix validating Writ's thin-rule architecture

### Changed

- `install.sh` link mode now creates per-file symlinks instead of directory symlinks, enabling per-project command customization alongside linked Writ commands
- `install.sh` link mode auto-cleans stale symlinks when source files are removed upstream
- `install.sh` link mode now commits linked command and agent files to git (previously only committed manifest)
- README updated with `/assess-spec` in pipeline diagram, commands table, and key features

## [0.1.0] - 2026-03-15

First public release. Three completed specs deliver the full Writ pipeline — from product planning through retrospective.

### Added

**Phase 1 — Foundation** (Spec: `2026-02-27-phase1-foundation`)

- `/prototype` command — lightweight executor for quick changes without a full spec, with auto-escalation to `/create-spec` when complexity warrants it
- Tiered spec-healing review agent with drift detection and auto-amendment
- Drift report format (`drift-log.md`) for tracking spec amendments across story implementation
- `/refresh-command` — learning loop that scans agent transcripts and proposes concrete command diffs
- `/refresh-command` promotion pipeline for staged rollout of command updates
- Command overlay system enabling per-project customization of Writ commands
- `/plan-product` gstack enhancement with opinionated posture and strategic framing (DEC-006)

**Pipeline Quality Improvements** (Spec: `2026-03-13-pipeline-quality-improvements`)

- Coding agent self-check to reduce pipeline round-trips
- Weighted review with change surface classification for proportional review depth
- "What Was Built" record auto-generated on story completion
- Living spec auto-amendment when drift is detected during implementation
- Cross-spec consistency check in `/create-spec` to catch planning-level conflicts
- Documentation agent framework agnosticism — adapts to VitePress, Docusaurus, README, etc.

**Phase 2a — Shipping & Review** (Spec: `2026-03-15-phase2a-shipping-review`)

- `/ship` command — unified shipping workflow: merge default branch, run tests, split commits by concern, create PR with structured body and auto-labels
- `/review` command — standalone pre-landing code review with error & rescue maps, shadow path tracing, interaction edge cases, and failure modes registry
- `/retro` command — git-based retrospective with session detection, streak tracking, Ship of the Week, persistent JSON snapshots, and rolling trend analysis
- Error mapping in `/create-spec` for systematic error handling and rescue paths

**Infrastructure & Platform**

- Install script (`install.sh`) with manifest tracking, three-way merge, and `--link` mode for multi-project sync
- Update script (`update.sh`) with file-level preservation of user customizations
- Migration script (`migrate.sh`) for Code Captain → Writ transition with full artifact preservation
- Platform adapters: Cursor (native), Claude Code (subagent system), OpenClaw
- `/implement-spec` orchestrator with parallel batch execution and dependency graph resolution
- `/implement-story` 6-gate SDLC pipeline: arch-check → code → lint → review → test → docs
- Proportional verification strategy for `/implement-spec` — scales validation to change scope
- Plan Mode for open-ended discovery, AskQuestion for bounded decisions (ADR-001)
- Visual design system — `/design` command, visual QA agent, mockup management
- `.writ/` workspace directory structure for specs, research, retros, decision records, and documentation

### Fixed

- Cross-platform migration script compatibility (macOS + Linux)
- Documentation bugs across commands and agents
- Retro data contract: `test_ratio` uses numeric `0` instead of `null` for zero-test periods
