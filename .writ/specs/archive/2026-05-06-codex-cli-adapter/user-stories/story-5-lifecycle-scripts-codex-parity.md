# Story 5: update.sh, unlink.sh, uninstall.sh --platform codex Parity

> **Status:** Code complete — PR review + upstream update-path evidence pending
> **Priority:** High
> **Dependencies:** Story 4

## User Story

**As a** Codex CLI user maintaining a Writ installation over time
**I want to** run update, unlink, and uninstall flows with `--platform codex` and have them respect my `AGENTS.md` modifications, my `.codex/config.toml` customizations, and the Writ-block boundary inside `AGENTS.md`
**So that** Writ behaves like a good citizen on Codex over time — never altering my owned content, always cleanly removable, and predictably updatable without a manual cleanup ritual

## Acceptance Criteria

**AC-1: `update.sh --platform codex` performs three-way overlay and detects Writ-block modification state**

- **Given** an existing Codex install (`.codex/.writ-manifest` present, `AGENTS.md` containing a `<!-- writ:start -->` / `<!-- writ:end -->` block) and a fresh Writ source with newer agent/command/skill content
- **When** `bash scripts/update.sh --platform codex` runs
- **Then** the three-way overlay applies to commands (`.codex/commands/`), agents (`.codex/agents/*.toml`), and skills (`.agents/skills/`) using the same upstream/local/baseline rules as Cursor and Claude; the `AGENTS.md` Writ block is treated according to its modification state — *upstream-baseline* (block hash matches manifest) → safe overwrite, summary line `🔄 Updated: AGENTS.md (Writ block)`; *local-modified* (block hash differs) → preserved with `⚡ Preserved: AGENTS.md (Writ block has local modifications)` warning unless `--force` is passed; *absent* (markers missing entirely, e.g. user removed them) → block re-added by the same `merge_agents_md()` append path used in Story 4, with summary line `✨ Restored: AGENTS.md (Writ block re-added)`; `.codex/config.toml` is never touched (install-once semantics); existing Cursor/Claude update flows produce byte-identical output to pre-Story-5 baselines

**AC-2: `unlink.sh --platform codex` converts symlinked installs to copies and leaves user-owned files intact**

- **Given** a Codex install with `.codex/agents/` populated by symlinks (the dogfooding pattern, or a user-initiated link install) and an unmodified `.codex/config.toml` and `AGENTS.md` Writ block
- **When** `bash scripts/unlink.sh --platform codex` runs
- **Then** every symlink under `.codex/commands/` and `.codex/agents/` (including directory-level symlinks from older link installs) is converted to an independent file copy via the same scan/replace pattern used for Cursor and Claude; `.codex/config.toml` is not touched (it's install-once and was never a symlink); `AGENTS.md` is not touched (it's a real file, not a symlink, and outside the unlink contract); the manifest is preserved; on a copy-mode install (no symlinks present) the script reports `No symlinks found — files are already independent copies` and exits 0

**AC-3: `uninstall.sh --platform codex` removes all Codex artifacts and cleanly excises the Writ block from `AGENTS.md`**

- **Given** a Codex install with `.codex/`, `.codex/.writ-manifest`, `.agents/skills/<name>/SKILL.md` entries, and an `AGENTS.md` containing a Writ block plus arbitrary user content above and/or below it
- **When** `bash scripts/uninstall.sh --platform codex` runs to completion (with the `.codex/config.toml` removal prompt answered "yes")
- **Then** `.codex/commands/`, `.codex/agents/`, `.codex/.writ-manifest`, `.codex/config.toml`, and `.codex/` itself are removed; `.agents/skills/<name>/SKILL.md` entries Writ installed are removed (user-authored skills outside the manifest are left alone, same overlay-aware logic as Cursor/Claude); the `AGENTS.md` Writ block is excised by the block-removal helper from Task 5.2 — markers and marker-bounded content are deleted, surrounding user content is byte-stable (verified by SHA-256 of the pre-state outside-markers region matching the post-state file content where applicable); the Writ workspace at `.writ/` is preserved unchanged (matches Cursor/Claude uninstall semantics)

**AC-4: `AGENTS.md` block-removal handles the four content scenarios correctly, including the empty-after-removal case**

- **Given** the bash test fixtures from Task 5.1 covering: (1) Writ block at top with no other content, (2) Writ block at bottom with content above, (3) Writ block in middle with content above and below, (4) `AGENTS.md` already lacks a Writ block (idempotency / re-run safety)
- **When** the test harness runs the block-removal helper against each fixture
- **Then** case (1) deletes `AGENTS.md` entirely (file becomes empty after marker removal — no whitespace-only file is left behind); case (2) removes the block plus the trailing newline/whitespace below it, with content above byte-stable up to and including its trailing newline; case (3) removes only the marker-bounded region plus exactly one normalizing newline so content above and below remains byte-stable and joined by a single newline; case (4) is a no-op exit 0 with summary line `✓ AGENTS.md (no Writ block present)` and the file untouched; malformed markers (start without end, or vice versa) halt with a descriptive error matching the install-side handling from Story 4

**AC-5: `.codex/config.toml` removal is gated by an explicit user prompt**

- **Given** a Codex install where `.codex/config.toml` exists (whether seeded by Writ at install time or further customized by the user)
- **When** `bash scripts/uninstall.sh --platform codex` reaches the config-removal step (and is run interactively, i.e. not under `--dry-run`)
- **Then** the user is shown a single prompt: `⚠️  .codex/config.toml is your Codex configuration (may contain user customizations). Remove it? [y/N]`; default is `N` (preserve); on `y` the file is deleted and the summary reports `🗑  Removed: .codex/config.toml (user-confirmed)`; on `N` (or any non-`y` answer) the file is preserved and the summary reports `⚡ Preserved: .codex/config.toml (kept by user; remove manually if desired)`; under `--dry-run` the prompt is replaced with a planned-action line (`Would prompt: remove .codex/config.toml?`) and no read from stdin occurs; under a future `--force` flag (out of scope for this story unless trivially aligned with existing flag semantics) the prompt is bypassed and the file is removed

## Implementation Tasks

- [x] **5.1** Write bash test fixtures for the `AGENTS.md` block-removal algorithm, extending the harness pattern from Story 4 — add `scripts/tests/test_remove_agents_md_block.sh` (or extend the existing harness) with four fixtures: `agents-md-writ-only.txt` (block at top, nothing else), `agents-md-writ-bottom.txt` (user content above, block at bottom), `agents-md-writ-middle.txt` (user content above and below the block), `agents-md-no-writ.txt` (no markers present); each fixture pairs with an expected post-state (or expected file-deleted assertion for case 1)

- [x] **5.2** Implement the `remove_agents_md_block()` helper in `scripts/uninstall.sh`: parses `<!-- writ:start -->` / `<!-- writ:end -->` line numbers via the same portable approach as Story 4's `merge_agents_md()`; deletes the marker-bounded region and the markers themselves; normalizes leading/trailing whitespace so the file doesn't end up with a leading blank line (case 1 with content below) or trailing blank tail; if the file's remaining content is whitespace-only or empty, deletes the file via `rm -f`; otherwise atomic-writes the trimmed content via `mktemp` + `mv`; halts with a descriptive error on malformed markers (mirrors install-side behavior); verify against all Task 5.1 fixtures

- [x] **5.3** Wire `--platform codex` branch into `scripts/update.sh`: extend the per-platform variable block to set `PLATFORM_DIR=".codex"`, `MANIFEST_FILE=".codex/.writ-manifest"`, `AGENTS_SRC="codex/agents"`, `PLATFORM_LABEL="Codex CLI"`, `SKILLS_DIR=".agents/skills"` (consuming Story 1's indirection); reuse Story 4's `merge_agents_md()` for the `AGENTS.md` Writ-block update path (the install-vs-update semantic difference is purely whether the manifest existed beforehand — the merger function already handles all three states); skip `seed_codex_config()` entirely on update paths (`.codex/config.toml` is install-once); ensure the existing three-way overlay logic for commands/agents/skills runs unchanged via `SKILLS_DIR`

- [x] **5.4** Wire `--platform codex` branch into `scripts/unlink.sh`: extend the per-platform variable block (parallel to Cursor/Claude) with the Codex paths and label; add `.codex/agents/` and `.codex/commands/` to the symlink scan loop; explicitly exclude `.codex/config.toml` and `AGENTS.md` from the scan (with a one-line comment explaining why — neither is symlink-managed); update the help text and the `--platform` value validation to accept `codex` alongside `cursor` / `claude`; verify the no-op messaging on a copy-mode Codex install (`No symlinks found — files are already independent copies`)

- [x] **5.5** Wire `--platform codex` branch into `scripts/uninstall.sh`: extend the per-platform variable block; extend the auto-detection logic (currently checking `.cursor/.writ-manifest` and `.claude/.writ-manifest`) to also check `.codex/.writ-manifest`; collect Codex `EXTRA_FILES` to include `.codex/config.toml` (gated by Task 5.6's prompt) and the `AGENTS.md` Writ-block excision (via Task 5.2's helper); collect skills under `.agents/skills/` for removal using the manifest's skill entries; update help text, error messages, and the final `bash <(curl …)` reinstall hint to recognize `codex`

- [x] **5.6** Implement the `.codex/config.toml` removal prompt in `scripts/uninstall.sh`: a single-line `read -r` prompt with default `N`, gated to interactive runs only (skipped under `--dry-run` with a planned-action line, skipped under any future `--force` flag with the file removed silently); summary lines for both branches (`🗑  Removed: .codex/config.toml (user-confirmed)` vs `⚡ Preserved: .codex/config.toml (kept by user; remove manually if desired)`); document the install-once-but-prompt-on-uninstall asymmetry in a brief comment block above the prompt so the next reader doesn't "fix" it into silent removal

- [ ] **5.7** Capture pre-Story-5 dry-run baselines for Cursor and Claude across all three lifecycle scripts (matching Story 1 and Story 4 discipline); run post-Story-5 dry-runs and diff against baselines; confirm zero diff (or document any cosmetic differences in the PR description); run Task 5.1's fixture harness; manually verify all five acceptance criteria on a sandbox Codex install; mark story Complete. **Current evidence:** `bash -n` for all three scripts; remove-block harness passes; local sandbox Codex install → unlink dry-run → uninstall dry-run → uninstall with config `y`; separate config-preserve `n` smoke passes. Upstream `update.sh --platform codex` full dry-run is pending because it clones upstream GitHub rather than this local working tree.

## Notes

**The block-removal helper is the only genuinely new logic in this story.** Everything else is paralleling the `--platform codex` branch into existing scripts using patterns Story 4 already established (variable block, `SKILLS_DIR` indirection, `merge_agents_md()` reuse on update). Expect the line-count of this PR to be smaller than Story 4's, and the review focus to be (a) `remove_agents_md_block()` byte-stability against the fixtures, and (b) the `.codex/config.toml` prompt UX.

**Why prompt rather than silent removal for `.codex/config.toml`.** The spec's Open Implementation Question 3 deferred this decision; recommended resolution is a prompt. Rationale: the file is owned by the user post-first-install (matches Claude's `settings.local.json` pattern), it's the only artifact in the Codex install where the install-once contract makes ownership ambiguous at uninstall time, and a single y/N prompt is cheap insurance against destroying user customizations someone forgot they made. A future `--force` flag (or its equivalent on the lifecycle commands) can bypass the prompt for non-interactive uninstall paths; explicit gating prevents accidental destruction in the common interactive case.

**`AGENTS.md` byte-stability is the same contract as install.** Outside the `<!-- writ:start -->` / `<!-- writ:end -->` markers, nothing changes. The empty-after-removal case (fixture 1) is the one place where the file *itself* is removed, not just modified — and that's a deliberate UX choice: leaving a zero-byte `AGENTS.md` after uninstall would be both useless and confusing for the next Codex session, and Codex itself would silently ignore it. The block-removal helper's "if remaining content is whitespace-only, delete the file" rule encodes this UX cleanly.

**Reuse `merge_agents_md()` from Story 4 for the update path, don't fork it.** The function already handles three cases (file absent, no markers, markers present) and that's exactly the surface the update flow needs. The "Writ block re-added" sub-case from AC-1 is just the no-markers branch invoked from update — no new function needed. If a fork emerges during implementation (e.g. update wants different summary line wording), prefer adding a small `MODE=install|update` parameter over a code copy.

**Consolidating three lifecycle scripts in one story is a deliberate trade.** Each script is small in incremental work (paralleling existing patterns), the AGENTS.md block-removal logic shared across uninstall is the only new bash logic, and a single PR makes the regression-diff exercise (Task 5.7) cleaner — one set of pre/post baselines covers all three scripts. If review feedback fragments the PR, splitting `update.sh` from `unlink.sh` + `uninstall.sh` is the natural seam (the block-removal helper lives with the latter pair).

**Portable shell discipline carries over from Story 4.** `set -euo pipefail`, `mktemp` + `mv` for atomic writes, no GNU-only flags, no `sed -i` without empty-string arg. The block-removal helper specifically should mirror `merge_agents_md()`'s style so both functions read like siblings rather than divergent dialects.

**Sequencing reconciliation note.** Story 4's "Files explicitly out of scope" section listed `scripts/update.sh` (Story 5) and `scripts/uninstall.sh` (Story 6) as separate stories. This story consolidates all three lifecycle scripts into Story 5; Story 6 in the resequenced plan covers the lifecycle *commands* (`/update-writ`, `/reinstall-writ`, `/uninstall-writ`) — the markdown command files in `commands/` that wrap the shell scripts with platform detection and user-facing messaging. The shell-script vs slash-command split is the natural seam.

## Definition of Done

- [x] Implementation tasks 5.1–5.6 coded
- [ ] Task 5.7 PR/regression evidence completed
- [ ] All five acceptance criteria fully evidenced at PR review time
- [x] Bash fixtures pass locally (`scripts/tests/test_remove_agents_md_block.sh`)
- [ ] Bash fixtures pass on at least one Linux environment
- [ ] Cursor and Claude lifecycle script `--dry-run` regression confirmed (zero diff, or documented cosmetic-only diffs in PR description)
- [ ] `AGENTS.md` byte-stability hash check executed manually on a fixture with non-trivial pre-existing user content above and below the Writ block; hash equality of the outside-markers region pre/post-uninstall confirmed in PR description
- [x] `.codex/config.toml` removal prompt manually verified with both `y` and `N` answers and under `--dry-run` in local sandbox
- [ ] Code reviewed
- [ ] PR description includes: pre/post dry-run diffs for all three scripts, fixture pass evidence, byte-stability hash check evidence, screenshot or transcript of the config.toml prompt UX

## Context for Agents

After reading `spec.md` and `sub-specs/technical-spec.md`, the following spec elements apply specifically to this story:

- **Error map rows (from technical-spec.md Error & Rescue Map):**
  - `Update detects modified Writ block` → preserve with `⚡` warning unless `--force` (AC-1's local-modified branch; reuses Story 4's overlay rule)
  - `Uninstall AGENTS.md cleanup` → file becomes empty after block removal → delete the file (AC-4 case 1; the block-removal helper's empty-content rule)
  - `Uninstall .codex/config.toml` → resolved here per Open Implementation Question 3: prompt with default-preserve, `y` to remove, surfaced summary line either way (AC-5)
  - Implicit row: malformed markers on uninstall → halts with descriptive error matching install-side handling (Task 5.2; mirrors Story 4 AC-3 case 4)

- **Shadow paths (from technical-spec.md Shadow Paths table):**
  - `Update` — all four columns: Happy Path (`Writ block updated`), Nil Input (`Manifest missing — re-run install`), Empty Input (n/a), Upstream Error (network failure surfaces same as install)
  - `Uninstall` — all four columns: Happy Path (`Writ removed; AGENTS.md preserved` for cases 2/3, `AGENTS.md deleted (empty after removal)` for case 1), Nil Input (`No Writ installation detected`), Empty Input (n/a), Upstream Error (n/a — uninstall is local-only)

- **Business rules (from spec.md Business Rules):**
  - **AGENTS.md ownership** — Writ owns content between markers exclusively; everything outside is user-owned; uninstall removes the block and the surrounding markers; if AGENTS.md becomes empty after removal, the file is also removed (the explicit uninstall sub-clause this story implements)
  - **`.codex/config.toml` is install-once** — and removal-with-prompt: the resolution to Open Implementation Question 3 is encoded here; subsequent updates never overwrite (AC-1's untouched-on-update guarantee), uninstall prompts before removing (AC-5)
  - **Self-dogfooding** — `.codex/agents/` symlinks to `codex/agents/` on the Writ repo; `unlink.sh --platform codex` understands the symlink-vs-copy distinction same as the existing platforms (AC-2's symlink-mode-vs-copy-mode handling)

- **Experience design hooks (from spec.md Experience Design):**
  - **Error experience table** — two of the seven rows are update/uninstall-time and land in this story: `User-modified Writ block detected on update` (AC-1) and `Existing AGENTS.md with Writ block on update` (AC-1's upstream-baseline branch)
  - **Empty / first-use states** — uninstall when AGENTS.md becomes empty (AC-4 case 1) is the symmetric "last-use state" of the empty/first-use Codex experience; the file-deletion behavior keeps the project clean for the next Codex session
  - **Feedback model** — same `[N/M]` step format and per-file overlay symbols (`✨ / 🔄 / ⚡ / ✓ / 🗑`) as Cursor/Claude lifecycle scripts; dedicated `AGENTS.md:` summary line on update (mirrors Story 4's install summary)

- **Files in scope:** `scripts/update.sh`, `scripts/unlink.sh`, `scripts/uninstall.sh`, `scripts/tests/test_remove_agents_md_block.sh` (new — or extension of Story 4's harness), and reads-only consumption of Story 1's `SKILLS_DIR` indirection, Story 4's `merge_agents_md()` helper, and the manifest format Story 4 finalized.

- **Files explicitly out of scope:** `scripts/install.sh` (Story 4 owns it; this story only reuses its functions); `commands/update-writ.md`, `commands/reinstall-writ.md`, `commands/uninstall-writ.md` (next story owns the slash-command wrappers and platform-detection messaging); `adapters/codex.md` lifecycle-section content (Story 3 deliverable, optionally referenced); `commands/refresh-command.md` `--check-parity` (Story 2/7 territory); README updates and live end-to-end smoke verification (final story).
