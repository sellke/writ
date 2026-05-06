# Story 4: install.sh --platform codex Support

> **Status:** Code complete — PR review + AC/regression evidence (DoD checklist) pending
> **Priority:** High
> **Dependencies:** Stories 1, 2, 3

## User Story

**As a** Codex CLI user setting up Writ on a new project
**I want to** run a single `bash scripts/install.sh --platform codex` command and get a working Writ installation — agents in `.codex/agents/*.toml`, skills at `.agents/skills/`, my `AGENTS.md` updated with a Writ-managed block, and `.codex/config.toml` seeded once with sensible defaults
**So that** the next `codex` session recognizes Writ and I can run `/create-spec`, `/implement-story`, etc., immediately, without manual setup chores or surprise edits to my existing `AGENTS.md` content

## Acceptance Criteria

**AC-1: `--platform codex --dry-run` shows complete and correct file fanout**

- **Given** a project with no prior Writ install and no pre-existing `AGENTS.md`
- **When** `bash scripts/install.sh --platform codex --dry-run` runs
- **Then** the dry-run output enumerates: every command file destined for `.codex/commands/`, all seven agent TOMLs destined for `.codex/agents/*.toml`, any skills destined for `.agents/skills/<name>/SKILL.md`, the `AGENTS.md` merge plan (action: `create`, `append`, or `replace` depending on pre-state), the `.codex/config.toml` seed plan (action: `seed` or `skip`), and the manifest write to `.codex/.writ-manifest`; no files are created on disk

**AC-2: Live install produces the expected file tree on a fresh project**

- **Given** a fresh project directory (no `.codex/`, no `AGENTS.md`, no `.agents/`)
- **When** `bash scripts/install.sh --platform codex` runs to completion
- **Then** the resulting tree contains `.codex/commands/*.md` (full command set), `.codex/agents/*.toml` (seven agents from Story 2), `.codex/config.toml` (seeded from `codex/config.toml.template`), `.codex/.writ-manifest` (with platform line `# platform: codex` and entries for every installed file plus `AGENTS.md.writ-block` and `.codex/config.toml.baseline` hashes), `AGENTS.md` containing only the marker-bounded Writ block, and `.agents/skills/<name>/SKILL.md` for any skills present in the source manifest

**AC-3: `merge_agents_md()` handles all five marker scenarios correctly**

- **Given** the bash test fixtures from Task 4.1 covering: (1) file-absent, (2) no-markers, (3) markers-found-clean, (4) malformed-markers, (5) modified-Writ-block
- **When** the test harness runs `merge_agents_md()` against each fixture
- **Then** case (1) creates `AGENTS.md` with the Writ block plus markers; case (2) appends `\n<!-- writ:start -->\n…\n<!-- writ:end -->\n` to end of file with user content byte-stable above; case (3) replaces only the marker-bounded region atomically with surrounding content byte-stable; case (4) halts with a non-zero exit and an error message naming the malformed marker pair, leaving the file untouched; case (5) preserves the user-modified block with a `⚡` warning unless `--force` is passed (in which case the block is overwritten and a notice surfaced)

**AC-4: AGENTS.md byte-stability outside markers is verifiable**

- **Given** a project with a pre-existing `AGENTS.md` containing arbitrary user content above and below where the Writ block will sit (after first install) or already does sit (on update)
- **When** `bash scripts/install.sh --platform codex` runs (whether on first install with append, or simulated update by editing the block content and re-running)
- **Then** SHA-256 of every byte outside the `<!-- writ:start -->` / `<!-- writ:end -->` region is identical to the pre-install hash; the only allowed delta is the marker-bounded region itself plus exactly one trailing newline normalization if the original file did not end with one

**AC-5: `.codex/config.toml` is seeded once and never overwritten on subsequent installs**

- **Given** a project where `.codex/config.toml` already exists (whether from a prior Writ install or hand-authored by the user)
- **When** `bash scripts/install.sh --platform codex` runs again
- **Then** the existing `.codex/config.toml` is preserved byte-for-byte, the install summary reports `⚡ Preserved: .codex/config.toml (install-once)` (or equivalent), the manifest's stored baseline hash for `.codex/config.toml` is unchanged from first install, and `--force` does not change this default behavior (Story 5 owns the `--force` reset flow if any)

**AC-6: Cursor and Claude install paths are regression-clean**

- **Given** the variable indirection from Story 1 (`SKILLS_DIR`) and the new `--platform codex` branch landing in this story
- **When** `bash scripts/install.sh --platform cursor --dry-run` and `bash scripts/install.sh --platform claude --dry-run` run pre-Story-4 and post-Story-4
- **Then** outputs are byte-identical (or any difference is purely cosmetic — e.g. ordering of variable echoes — and is documented in the PR description); no Cursor or Claude install path silently shifts because of the Codex wiring

## Implementation Tasks

- [x] **4.1** Write bash test fixtures and a minimal harness in `scripts/tests/test_merge_agents_md.sh` (single shell script, `assert_eq` / `assert_file_eq` helpers, no external framework) covering the five `merge_agents_md()` cases: file-absent, no-markers, markers-found-clean, malformed-markers, modified-block; each fixture includes both the input AGENTS.md state and the expected post-state file
- [x] **4.2** Implement `merge_agents_md()` in `scripts/install.sh`: parses markers via `grep -n` line numbers (or equivalent portable shell), uses `mktemp` for atomic write-then-rename, computes Writ-block SHA-256 via existing `hash_file()`, compares against `manifest_hash_for("AGENTS.md.writ-block")`; reads injected content from `codex/AGENTS.md.template` (Story 3 deliverable); halts with descriptive error on malformed markers; emits the `⚡` preserve warning unless `FORCE=1`; verify the function passes all Task 4.1 fixtures
- [x] **4.3** Implement `seed_codex_config()` in `scripts/install.sh`: copies `codex/config.toml.template` (Story 3 deliverable) to `.codex/config.toml` only if the destination file does not already exist; emits `✨ Seeded: .codex/config.toml` on first install and `⚡ Preserved: .codex/config.toml (install-once)` on subsequent installs; records baseline hash in the manifest on the first-install path only
- [x] **4.4** Wire the `--platform codex` branch into `scripts/install.sh`: extend the per-platform variable block to set `PLATFORM_DIR=".codex"`, `MANIFEST_FILE=".codex/.writ-manifest"`, `AGENTS_SRC="codex/agents"`, `PLATFORM_LABEL="Codex CLI"`, `SKILLS_DIR=".agents/skills"` (the divergent path); add the `merge_agents_md` and `seed_codex_config` calls in the same step where Cursor copies `writ.mdc` and Claude copies `CLAUDE.md`
- [x] **4.5** Extend `write_copy_manifest()` to track two new entries on Codex installs: `<sha256>  AGENTS.md.writ-block` (hash of the marker-bounded content, exclusive of markers) and `<sha256>  .codex/config.toml.baseline` (hash of the seeded template content at first-install time); ensure these entries are stable across re-runs when the underlying content hasn't changed
- [x] **4.6** Update install summary output: add a dedicated `AGENTS.md:` line reporting one of `Writ block created` / `Writ block appended (existing content preserved)` / `Writ block updated` / `Writ block preserved (local modifications)` / `Writ block error: malformed markers`; ensure the `⚡ Writ Installer (Codex CLI)` banner uses `PLATFORM_LABEL`; verify the per-file overlay symbols (`✨ / 🔄 / ⚡ / ✓`) appear consistently for the new file types
- [x] **4.7** Capture pre-Story-4 dry-run baselines for cursor and claude — **Evidence:** Cursor `--dry-run` smoke from empty `TMPDIR` after Story 4 (exit 0); byte-identical regressions belong in PR description when this ships. (matching Story 1's discipline), run post-Story-4 dry-runs, diff against baselines, attach diff (or zero-diff confirmation) to the PR description; verify all six acceptance criteria; mark story Complete

## Notes

**Highest-risk piece is `merge_agents_md()`.** Byte-stability of user content outside the markers is a contract — if Writ ever silently re-flows the user's surrounding text (line endings, trailing whitespace, encoding), trust in the integration breaks immediately and silently. Bash fixtures are the right discipline here even though this repo doesn't currently bash-test anything else; the foundation lands in `scripts/tests/` and Story 5 (update.sh) and Story 6 (uninstall.sh) can reuse the harness. If a future spec extends the merger algorithm, the fixtures are the regression net.

**Atomic write pattern.** `merge_agents_md()` should write to a temp file via `mktemp` and `mv` into place — not edit-in-place — so a SIGINT or disk-full mid-merge leaves the original file untouched. Same pattern as the existing overlay code paths.

**Install-once semantics for `.codex/config.toml`.** Mirrors Claude Code's `settings.local.json` pattern: Writ seeds a baseline on first install, then treats the file as user-owned. Make the convention explicit in an `install.sh` comment block above `seed_codex_config()` so the next reader doesn't accidentally "fix" it into an overlay-managed file. The manifest baseline hash is recorded so a future `--force` flow (Story 5) can offer to reset, but default behavior preserves user customization indefinitely.

**`--force` flag scope for this story.** When `--force` is passed and a Writ block is detected as user-modified (case 5), overwrite it with a clear notice. This matches existing `--force` semantics for commands and agents in `install.sh`. Out of scope: `--force` interaction with `.codex/config.toml` seeding (Story 5 owns the reset flow), and any new flag surface for selective force (`--force-agents-only` etc. are not introduced here).

**Marker parsing must be portable.** The existing scripts target macOS/BSD `bash`/`grep`/`sed` plus Linux GNU equivalents. Avoid GNU-only flags (`grep -P`, `sed -i` without empty-string arg). When in doubt, prefer a small awk one-liner or a portable `grep -n | head -n1` pattern. The `set -euo pipefail` discipline at the top of the script applies to the new functions.

**No live Codex CLI verification in this story.** Manual smoke on a sandbox project, opening `codex`, and running `/create-spec` end-to-end is owned by Story 7. Story 4 ships when the bash fixtures pass and the dry-run output looks right. This deliberate split keeps the install-script PR reviewable in one sitting.

**Bash test harness convention.** A single `scripts/tests/test_merge_agents_md.sh` script with inline `assert_eq()`, `assert_file_byte_eq()`, and `assert_exit()` helpers, runnable as `bash scripts/tests/test_merge_agents_md.sh`. No CI wiring in this story (the repo doesn't currently run CI on shell scripts) — running the harness is a manual gate documented in the story's DoD.

## Definition of Done

- [x] All implementation tasks coded (Task 4.7 formal pre/post `--dry-run` byte baselines owed in PR narrative per story checklist)
- [ ] All six acceptance criteria fully evidenced at PR review time (fixture + dry-run cover much of AC-3/AC-1/AC-2 locally; AC-6 byte-identical Cursor/Claude diff not captured yet; AC-4 hash proof still for PR/manual)
- [x] Bash test harness passes locally (`bash scripts/tests/test_merge_agents_md.sh`)
- [ ] Bash harness exercised on Linux in CI or container _(manual follow-up recommended)_
- [x] Cursor `--dry-run` regression smoke post-change (exit 0 from empty TMPDIR install)
- [ ] Claude `--dry-run` byte-identical baseline diff _(attach at PR alongside cursor if required by process)_
- [ ] Manual byte-stability hash check documented in PR _(optional deepening)_
- [x] Manifest extensions documented inline in installer / manifest samples
- [ ] Code reviewed
- [ ] PR description checklist from story _(pre/post dry-run diffs, parity, hash evidence as applicable)_

## Context for Agents

After reading `spec.md` and `sub-specs/technical-spec.md`, the following spec elements apply specifically to this story:

- **Error map rows (from technical-spec.md Error & Rescue Map):**
  - `install.sh --platform codex initial run` → exit nonzero on git/network failure with no partial state
  - `Install AGENTS.md merge (file absent)` → catch disk-full / permission-denied, leave no partial file
  - `Install AGENTS.md merge (markers malformed)` → halt with error, do not modify
  - `Install AGENTS.md merge (combined size > 32 KiB)` → warning surfaced, steer to `project_doc_max_bytes` or `AGENTS.override.md` split
  - `Install .codex/config.toml seeding` (file already exists) → skip silently, install-once semantics
  - `Install agent TOMLs (codex/agents/ empty)` → warning emitted, commands and skills still install, exit nonzero
  - `Install skills to .agents/skills/` → three-way overlay applies, user-modified `SKILL.md` files preserved (overlay logic from Story 1's `SKILLS_DIR` indirection)

- **Shadow paths (from technical-spec.md Shadow Paths table):**
  - `Install on fresh project` — all four columns: Happy Path (✅ banner + agent count), Nil Input (❌ source missing + retry hint), Empty Input (n/a), Upstream Error (clone failure surfaces clearly)
  - `Install on existing AGENTS.md` — all four columns: Happy Path (`Writ block appended`), Nil Input (n/a), Empty Input (`AGENTS.md was empty, Writ block written`), Upstream Error (`⚠️ Malformed markers` + manual fix instructions)

- **Business rules (from spec.md Business Rules):**
  - **AGENTS.md ownership** — Writ owns content between `<!-- writ:start -->` and `<!-- writ:end -->` exclusively; everything outside is user-owned and never touched (the byte-stability contract this story implements)
  - **`.codex/config.toml` is install-once** — baseline written on first install; subsequent updates never overwrite; manifest tracks baseline hash for future `--force` reset (deferred to Story 5)
  - **Skills install path is platform-divergent** — `.agents/skills/` for Codex (per Story 1's `SKILLS_DIR` indirection); the divergence from Cursor's `.cursor/skills/` and Claude's `.claude/skills/` is enforced here, not just documented

- **Experience design hooks (from spec.md Experience Design):**
  - **Happy path on fresh project** — six-step install: commands → agents → skills → AGENTS.md → `.codex/config.toml` → manifest; this story implements the AGENTS.md and config-seeding steps and wires the rest into the existing overlay machinery
  - **Happy path on existing AGENTS.md** — `AGENTS.md: Writ block appended (existing content preserved)` summary line is mandated by AC-6 of the spec and AC-3/AC-4 of this story
  - **Feedback model** — same `[N/M]` step format as Cursor/Claude installs; same per-file overlay symbols (`✨ / 🔄 / ⚡ / ✓`); dedicated AGENTS.md merger summary line
  - **Error experience table rows** — five of the seven rows are install-time and land in this story (the other two are update/lifecycle and land in Story 5)

- **Files in scope:** `scripts/install.sh`, `scripts/tests/test_merge_agents_md.sh` (new), and reads-only consumption of Story 1's `SKILLS_DIR` indirection, Story 2's `codex/agents/*.toml`, Story 3's `codex/AGENTS.md.template` and `codex/config.toml.template`.

- **Files explicitly out of scope:** `scripts/update.sh` (Story 5), `scripts/uninstall.sh` (Story 6), `scripts/unlink.sh` (Story 5/6), any `commands/*.md` lifecycle command updates (Stories 5–6), `adapters/codex.md` content (Story 3), README updates and live smoke verification (Story 7).
