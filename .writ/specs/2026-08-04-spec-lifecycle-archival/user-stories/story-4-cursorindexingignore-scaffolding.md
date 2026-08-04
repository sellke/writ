# Story 4: .cursorindexingignore Scaffolding

> **Status:** Completed ✅
> **Priority:** Medium
> **Dependencies:** None
> **Commit:** 090d038

## User Story

**As a** developer installing or updating Writ in my project
**I want to** have a `.cursorindexingignore` file seeded at the project root on first install (install-once, never overwritten)
**So that** completed specs moved to `.writ/specs/archive/` are excluded from Cursor's semantic search indexing by default in every Writ project — not just this repo — without me having to discover or configure the exclusion manually

## Acceptance Criteria

- [x] Given a fresh project with no `.cursorindexingignore` at the root, when `install.sh` runs (apply mode, any platform — implementer may gate to Cursor-only but must document the choice), then a `.cursorindexingignore` file is created containing at minimum the pattern `.writ/specs/archive/**` and apply output includes a `✨ Seeded: .cursorindexingignore` line matching the `seed_codex_config` style.
- [x] Given `.cursorindexingignore` already exists at the project root (including one the user created or customized), when `install.sh` runs again — including with `--force` — then the existing file is **preserved unchanged**, apply output includes `⚡ Preserved: .cursorindexingignore (install-once)`, and no Writ-managed template overwrites local indexing preferences.
- [x] Given `install.sh --dry-run --platform cursor` (and the equivalent dry-run path for whichever platforms the implementer wires), when the preview pass runs, then output includes an install-once preview line following `seed_codex_config preview` style: `Would seed .cursorindexingignore (first install).` when absent, or `Would skip .cursorindexingignore (already exists; install-once).` when present — visible before the "Install" section, not only as a side effect of apply.
- [x] Given the Writ source repo itself (which does **not** run `install.sh` — it uses symlinks per `.writ/docs/self-dogfooding.md`), when this story completes, then a `.cursorindexingignore` file exists at the repo root with `.writ/specs/archive/**` as a direct, committed manual step — independent of testing `install.sh` against this repo.
- [x] Given the seeded file content, when inspected, then it contains only the archive exclusion pattern (or additional commented guidance is acceptable), and the pattern `.writ/specs/archive/**` is present on its own line — satisfying Business Rule 7 and `spec.md` Success Criterion 4.

## Implementation Tasks

- [x] 4.1 Write failing shell tests (prefer extending `scripts/eval.sh` install beat or a focused `scripts/tests/test_install_cursorindexingignore.sh` fixture) that run `install.sh --dry-run --platform cursor` in a temp workspace: assert preview contains the seed/skip line; run apply twice and assert first run creates the file with `.writ/specs/archive/**`, second run preserves content and prints the Preserved message even with `--force`.
- [x] 4.2 Add `seed_cursorindexingignore()` to `scripts/install.sh` mirroring `seed_codex_config()` exactly: `preview | apply` op argument, `[ -f "$dest" ]` guard, global note variable, preview messages (`Would seed …` / `Would skip …`), apply messages (`✨ Seeded:` / `⚡ Preserved:`), inline content creation (no external template file required unless the implementer prefers one — either way, document the choice).
- [x] 4.3 Wire the new function into both code paths: **dry-run** preview section (alongside platform-specific blocks — e.g. under the Cursor platform header, matching where `seed_codex_config preview` lives for Codex) and **apply** path (call after `init_writ_workspace` or from within it — implementer's choice, but dry-run must not depend on apply-only calls).
- [x] 4.4 Decide and document platform scope in a code comment and this story's Notes: either create for all platforms (harmless on Claude/Codex) or Cursor-only — default recommendation is all platforms for consistency unless preview clutter argues otherwise.
- [x] 4.5 Manually create `.cursorindexingignore` at the Writ source repo root (this repo) with `.writ/specs/archive/**` — a direct commit in this story, not achieved by running `install.sh` on the dogfood workspace.
- [x] 4.6 Add an `eval.sh` static or scenario assertion that `install.sh` defines `seed_cursorindexingignore` (or equivalent), references `.writ/specs/archive/**`, and that dry-run output for cursor platform includes the preview line — preventing silent regression if someone removes the wiring.
- [x] 4.7 Run the new tests, `bash scripts/install.sh --dry-run --platform cursor` from a disposable fixture, and confirm Success Criterion 4 from `spec.md` before marking complete.

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

- [x] All tasks completed
- [x] All acceptance criteria met
- [x] Tests passing
- [x] Code reviewed
- [x] Documentation updated

## Context for Agents

- **Error map rows:** []
- **Shadow paths:** [install-once preservation on re-run]
- **Business rules:** [.cursorindexingignore ships via install.sh (install-once, same pattern as .codex/config.toml)]
- **Experience:** []

Reference: `.writ/docs/context-hint-format.md` — read `spec.md` directly for full contract text at `## 📋 Business Rules` (item 7), `## Detailed Requirements` → `### .cursorindexingignore scaffolding`, and Success Criterion 4.

---

## What Was Built

**Implementation Date:** 2026-08-04

### Files Created

1. **`scripts/eval-cursorindexingignore.py`** (3 scenario groups, 8 assertions) — runs the real `scripts/install.sh` against disposable temp workspaces (it self-resolves `WRIT_SRC` to this checkout) to prove the dry-run preview lines, first-apply seeding, and force-apply preservation behavior end to end.
2. **`.cursorindexingignore`** (repo root) — the manual seed for this repo itself (`.writ/specs/archive/**`), since this repo uses symlinked dev install and never runs `install.sh` on itself.

### Files Modified

- **`scripts/install.sh`**:
  - Added `seed_cursorindexingignore()` mirroring `seed_codex_config()`'s `preview | apply` contract exactly — same guard shape, same message style, and (unlike the codex config seed, which is Codex-only) wired for **all platforms**, since the file is inert-but-harmless outside Cursor and this keeps installs consistent.
  - Wired into the dry-run preview block unconditionally (covers both symlink-conversion and normal preview paths), and into the apply path right after `configure_audit_notes_sync apply`.
  - Added the note variable to the unconditional summary print (not gated to `codex`, unlike `SEED_CODEX_CONFIG_NOTE`) and to the scoped git-commit `git add` list.
- **`scripts/eval.sh`** — registered the `cursorindexingignore` check (CHECKS array + `check_cursorindexingignore()`), with static assertions that `install.sh` defines the helper, references the archive pattern, and calls it from both preview and apply, plus a direct check that this repo's own root `.cursorindexingignore` exists and carries the pattern on its own line.

### Implementation Decisions

1. **All platforms, not Cursor-only.** The story's Notes flagged this as the implementer's call with "all platforms" as the default recommendation. Chose it: the file is a no-op outside Cursor, and gating it would mean a project that switches platforms later silently loses the seed opportunity (install-once means there's no second chance).
2. **`Would skip` (not `Would preserve`) in the preview message.** The technical-spec's illustrative pseudocode used "Would preserve…", but the locked acceptance criteria (AC 3) and the real `seed_codex_config()` implementation both use "Would skip … (already exists; install-once)." Followed the AC and the real precedent over the illustrative snippet.
3. **No external template file.** Unlike `seed_codex_config()` (which copies from `codex/config.toml.template`), the archive-exclusion pattern is a single line — inlined via `printf` rather than adding a one-line template file to `scripts/`/`cursor/`, consistent with the "no template required" option the story explicitly allowed.
4. **`--force` never overwrites.** The `[ -f "$dest" ]` guard doesn't branch on `$FORCE` at all (unlike the overlay-scan force-overwrite path), so install-once holds even under `--force` — verified directly by the `force-apply-preserves-existing-file-content` scenario.

### Test Results

**Verification:** `python3 scripts/eval-cursorindexingignore.py` + `bash scripts/eval.sh --check=cursorindexingignore`
- ✅ 8/8 eval scenarios passing (dry-run preview seed/skip lines, dry-run makes no file, first-apply creates file + message + pattern, force-apply preserves customized content + message)
- ✅ `bash scripts/eval.sh --check=cursorindexingignore` — PASS, 0 findings (including the repo-root-file assertion)
- ✅ Manual verification: ran `install.sh --dry-run`, `install.sh` (apply), `install.sh --force` in a disposable `/tmp` workspace and inspected output/file contents directly before writing the automated fixture

### Review Outcome

**Result:** PASS

- **Iteration count:** 1 iteration
- **Drift:** None
- **Security:** N/A — install.sh addition follows the existing install-once pattern; no new external input or network surface

### Deviations from Spec

None. The one implementer's-choice decision (all platforms vs. Cursor-only) is documented above per the story's own Notes allowance.
