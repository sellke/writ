# Story 7: Ralph Retirement and Autonomy Acceptance

> **Status:** Complete
> **Priority:** High
> **Dependencies:** Stories 1-6

## User Story

**As a** Writ maintainer completing Phase 6
**I want to** archive Ralph, remove it from active product surfaces, and exercise the normal phase workflow in a disposable multi-spec sandbox
**So that** normal `/implement-phase` and single-spec `--recommend` delivery have distinct supported boundaries, while Phase 6 closes with honest mechanical evidence and real-use validation remains pending

## Acceptance Criteria

- [x] Given the Ralph command, script, prompt templates, and reference documentation, when retirement is complete, then they are preserved under `archive/ralph/` with recognizable grouping and an allowlisted search finds no Ralph references on active command, catalog, config, adapter, README, or status surfaces.
- [x] Given Writ's discovery, release, and migration surfaces, when catalogs are regenerated, then `.writ/manifest.yaml`, generated `SKILL.md`, config guidance, adapters, README, status suggestions, and quick actions point users to normal `/implement-phase` for multi-spec work and explicitly supported single-spec `--recommend` delivery where applicable, explain the loss of opaque unbounded execution, warn users to finish or abandon in-flight `ralph-*.json` runs before upgrading, and `bash scripts/gen-skill.sh --check` passes.
- [x] Given the retired active surface, when repository validation runs, then `bash scripts/eval.sh`, `bash scripts/install.sh --dry-run`, and `bash scripts/update.sh --dry-run` complete successfully and `CHANGELOG.md` records the retirement and supported replacement.
- [x] Given a temporary isolated repository or disposable directory containing the specified multi-spec phase, when acceptance UAT runs, then fresh per-spec execution, successful merges, terminal-failure quarantine, dependent blocking, independent continuation, resume reconciliation, User Challenge rendering, and categorical health are captured as evidence without leaving fixtures in active product discovery.
- [x] Given that sandbox evidence proves only mechanical behavior, when Phase 6 acceptance is reported, then the roadmap's real-use User Challenge criterion remains explicitly pending until a genuine phase run supplies that observation.

## Implementation Tasks

- [x] 7.1 Write or extend eval assertions for Ralph's absence from active surfaces, allowed historical/archive references, generated catalog consistency, and `/implement-phase` replacement guidance.
- [x] 7.2 Move `commands/ralph.md`, `scripts/ralph.sh`, `scripts/PROMPT_build.md`, `.writ/docs/ralph-cli-pipeline.md`, `.writ/docs/ralph-state-format.md`, and related Ralph reference material into a recognizably grouped `archive/ralph/` tree without creating compatibility readers or migration fixtures.
- [x] 7.3 Remove or redirect Ralph entries across `.writ/manifest.yaml`, active command discovery, `.writ/docs/config-format.md`, all three platform adapters, `README.md`, `commands/status.md` allowlists and suggestions, quick actions, and any remaining active product references.
- [x] 7.4 Regenerate `SKILL.md` from the cleaned manifest and confirm active catalog content presents `/implement-phase` as the supported supervised replacement.
- [x] 7.5 Update `CHANGELOG.md` and migration guidance to explain the archive, direct ongoing multi-spec work to normal `/implement-phase`, distinguish explicitly supported single-spec `--recommend` delivery, disclose the deliberate loss of opaque unbounded execution, warn users to finish or abandon in-flight `ralph-*.json` runs before upgrading, and state that existing Ralph state is not migrated.
- [x] 7.6 Verify retirement with `bash scripts/eval.sh`, `bash scripts/gen-skill.sh --check`, `bash scripts/install.sh --dry-run`, `bash scripts/update.sh --dry-run`, and an allowlisted active-reference search excluding `archive/`, historical specs, ADRs, changelog history, and roadmap history.
- [x] 7.7 Generate fixtures only at UAT time in an isolated disposable repository or temporary directory, execute the multi-spec sandbox, record plan/fresh-run/merge/quarantine/blocking/continuation/resume/challenge/health evidence, remove the sandbox, and leave the real-use User Challenge criterion pending.

## Notes

- Ralph is archived rather than deleted. Preserve enough relative grouping for historical comprehension without allowing archived material into command discovery or generated catalogs.
- Phase 6 does not add multi-spec `/implement-phase --recommend`; ADR-013's narrow exception applies only to commands that explicitly support the modifier.
- Stories 1-6 supply the dependency, isolation, challenge, quarantine, knowledge, and health mechanics exercised here; this story validates their integrated behavior rather than reimplementing them.
- Active-reference checks need a deliberate allowlist because ADRs, roadmap history, changelog history, locked specs, and `archive/ralph/` must continue to name Ralph.
- The migration note is informational only: it must carry ADR-012's finish-or-abandon-before-upgrade warning, but no compatibility reader, in-flight-state detector, or state migration is required.
- Do not commit permanent acceptance fixtures to active discovery. Build them only in the disposable UAT environment and retain evidence, not the sandbox.
- Mechanical sandbox success cannot close the human-observation criterion; report the phase as implemented with validation pending until genuine use produces evidence.

## Definition of Done

- [x] All tasks completed
- [x] All acceptance criteria met
- [x] Tests passing
- [x] Code reviewed
- [x] Documentation updated

## Context for Agents

- **Error map rows:** [`Archive Ralph` — active references remain; eval/catalog checks enforce cleanup, `Generate UAT` — post-merge generation failure resumes at the UAT step] — from `technical-spec.md` → `## Error & Rescue Map`
- **Shadow paths:** [`Ralph deprecation` — active discovery points to implement-phase and stale generated catalogs fail, `Fresh spec execution`, `Quarantine`, `Resume`, `Status health`] — from `technical-spec.md` → `## Shadow Paths`
- **Business rules:** [`Rule 10` — remove Ralph from active surfaces and preserve it under `archive/ralph/`, `Rule 11` — require no compatibility reader, detector, or state migration] — from `spec.md` → `### Business Rules`
- **Experience:** [`State Catalog` rows `Scope degradation proposed`, `Implemented`, and `Stale health evidence`; `User Challenge Format`; `Interaction and Output Rules` distinction between missing and failing evidence] — from `spec.md` → `## Experience Design`; [`Sandbox UAT Design` evidence list and real-use exclusion, `Interaction Edge Cases` row `Real-use criterion lacks evidence`] — from `technical-spec.md`
