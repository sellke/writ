# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/),
and this project adheres to [Semantic Versioning](https://semver.org/).

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
