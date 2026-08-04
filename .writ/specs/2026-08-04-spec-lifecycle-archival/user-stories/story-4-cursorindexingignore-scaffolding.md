# Story 4: .cursorindexingignore Scaffolding

> **Status:** Not Started
> **Priority:** Medium
> **Dependencies:** None

## User Story

**As a** developer installing or updating Writ in my project
**I want to** have a `.cursorindexingignore` file seeded at the project root on first install (install-once, never overwritten)
**So that** completed specs moved to `.writ/specs/archive/` are excluded from Cursor's semantic search indexing by default in every Writ project — not just this repo — without me having to discover or configure the exclusion manually

## Acceptance Criteria

- [ ] Given a fresh project with no `.cursorindexingignore` at the root, when `install.sh` runs (apply mode, any platform — implementer may gate to Cursor-only but must document the choice), then a `.cursorindexingignore` file is created containing at minimum the pattern `.writ/specs/archive/**` and apply output includes a `✨ Seeded: .cursorindexingignore` line matching the `seed_codex_config` style.
- [ ] Given `.cursorindexingignore` already exists at the project root (including one the user created or customized), when `install.sh` runs again — including with `--force` — then the existing file is **preserved unchanged**, apply output includes `⚡ Preserved: .cursorindexingignore (install-once)`, and no Writ-managed template overwrites local indexing preferences.
- [ ] Given `install.sh --dry-run --platform cursor` (and the equivalent dry-run path for whichever platforms the implementer wires), when the preview pass runs, then output includes an install-once preview line following `seed_codex_config preview` style: `Would seed .cursorindexingignore (first install).` when absent, or `Would skip .cursorindexingignore (already exists; install-once).` when present — visible before the "Install" section, not only as a side effect of apply.
- [ ] Given the Writ source repo itself (which does **not** run `install.sh` — it uses symlinks per `.writ/docs/self-dogfooding.md`), when this story completes, then a `.cursorindexingignore` file exists at the repo root with `.writ/specs/archive/**` as a direct, committed manual step — independent of testing `install.sh` against this repo.
- [ ] Given the seeded file content, when inspected, then it contains only the archive exclusion pattern (or additional commented guidance is acceptable), and the pattern `.writ/specs/archive/**` is present on its own line — satisfying Business Rule 7 and `spec.md` Success Criterion 4.

## Implementation Tasks

- [ ] 4.1 Write failing shell tests (prefer extending `scripts/eval.sh` install beat or a focused `scripts/tests/test_install_cursorindexingignore.sh` fixture) that run `install.sh --dry-run --platform cursor` in a temp workspace: assert preview contains the seed/skip line; run apply twice and assert first run creates the file with `.writ/specs/archive/**`, second run preserves content and prints the Preserved message even with `--force`.
- [ ] 4.2 Add `seed_cursorindexingignore()` to `scripts/install.sh` mirroring `seed_codex_config()` exactly: `preview | apply` op argument, `[ -f "$dest" ]` guard, global note variable, preview messages (`Would seed …` / `Would skip …`), apply messages (`✨ Seeded:` / `⚡ Preserved:`), inline content creation (no external template file required unless the implementer prefers one — either way, document the choice).
- [ ] 4.3 Wire the new function into both code paths: **dry-run** preview section (alongside platform-specific blocks — e.g. under the Cursor platform header, matching where `seed_codex_config preview` lives for Codex) and **apply** path (call after `init_writ_workspace` or from within it — implementer's choice, but dry-run must not depend on apply-only calls).
- [ ] 4.4 Decide and document platform scope in a code comment and this story's Notes: either create for all platforms (harmless on Claude/Codex) or Cursor-only — default recommendation is all platforms for consistency unless preview clutter argues otherwise.
- [ ] 4.5 Manually create `.cursorindexingignore` at the Writ source repo root (this repo) with `.writ/specs/archive/**` — a direct commit in this story, not achieved by running `install.sh` on the dogfood workspace.
- [ ] 4.6 Add an `eval.sh` static or scenario assertion that `install.sh` defines `seed_cursorindexingignore` (or equivalent), references `.writ/specs/archive/**`, and that dry-run output for cursor platform includes the preview line — preventing silent regression if someone removes the wiring.
- [ ] 4.7 Run the new tests, `bash scripts/install.sh --dry-run --platform cursor` from a disposable fixture, and confirm Success Criterion 4 from `spec.md` before marking complete.

## Notes

**Fully independent of Stories 1–3.** This is a purely additive `install.sh` change. It does not touch status detection, the archive sweep mechanism, or lifecycle documentation. It can ship in parallel with any other story once reviewed.

**Install-once is stronger than `--force`.** Unlike commands/agents/skills overlays, `.cursorindexingignore` represents a local indexing preference. Once created — by Writ or by the user — `install.sh` must never overwrite it, even when `--force` is passed. This matches the `seed_codex_config` / `.codex/config.toml` contract (Business Rule 7).

**Mirror `seed_codex_config`, not `overlay_scan`.** The reference implementation is `scripts/install.sh` lines ~399–431: check destination exists → preview or preserve → create with desired content. Do not route this file through the force-overwrite overlay path.

**Dogfood repo is a manual step.** This repo uses symlinked `.cursor/` (see `.writ/docs/self-dogfooding.md`) and does not invoke `install.sh` on itself. Task 4.5 creates the root `.cursorindexingignore` directly. Confirmed absent at story authoring time.

**Platform scope (implementer's choice):** Cursor is the only platform where `.cursorindexingignore` has functional effect. Creating it on Claude/Codex installs is harmless consistency; skipping non-Cursor platforms reduces noise. Either choice is valid — document it in a `# seed_cursorindexingignore — …` comment and note here.

**Risks:**

- Dry-run currently does not call `init_writ_workspace`; if the seed logic lives only there, preview will miss the step. Wire preview explicitly like `seed_codex_config preview`.
- Someone may add `.cursorindexingignore` to `.gitignore` — out of scope; the file is intended to be committed so teams share the archive exclusion default.
- Eval install beat runs `--dry-run` per platform — extend assertions for cursor (and any other platform where seeding is enabled).

## Definition of Done

- [ ] All tasks completed
- [ ] All acceptance criteria met
- [ ] Tests passing
- [ ] Code reviewed
- [ ] Documentation updated

## Context for Agents

- **Error map rows:** []
- **Shadow paths:** [install-once preservation on re-run]
- **Business rules:** [.cursorindexingignore ships via install.sh (install-once, same pattern as .codex/config.toml)]
- **Experience:** []

Reference: `.writ/docs/context-hint-format.md` — read `spec.md` directly for full contract text at `## 📋 Business Rules` (item 7), `## Detailed Requirements` → `### .cursorindexingignore scaffolding`, and Success Criterion 4.
