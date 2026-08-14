# Marker-Based CLAUDE.md Merge (Lite)

> Source: .writ/specs/2026-08-13-claude-md-install-merge/spec.md
> Purpose: Efficient AI context for implementation

## For Coding Agents

**Deliverable:** Stop `install.sh` from clobbering a pre-existing `CLAUDE.md`
by giving it the same `<!-- writ:start/end -->` marker-block treatment
`AGENTS.md` already has; migrate `update.sh`'s CLAUDE.md logic to match.

**Implementation Approach:**
- Mirror `merge_agents_md` in both scripts (`install.sh:235-396`,
  `update.sh:318-407`) — new `merge_claude_md`, same decision tree, same
  bundle-marker convention for test extraction.
- Reuse existing helpers: `writ_compute_writ_block_inner_hash`,
  `writ_block_marker_counts`, `writ_file_ends_with_newline`,
  `writ_rewrite_agents_md_with_inner` (file-agnostic already).
- New manifest key `CLAUDE.md.writ-block` (inner hash) replaces the bare
  `CLAUDE.md` (whole-file hash) key in both scripts.

**Files in Scope:**
- `scripts/install.sh` — new `merge_claude_md`; wire into apply
  (`:1053-1057`) and dry-run preview (`:951-952`); `write_copy_manifest`
  (`:520-530`) writes new key.
- `scripts/update.sh` — new `merge_claude_md` replacing `CLAUDE_MD_ACTION`
  logic (`:840-864`) and apply step (`:975`); include `restore`/`error`
  states like its `merge_agents_md`.
- `scripts/tests/test_merge_claude_md.sh` — new, mirrors
  `test_merge_agents_md.sh`.

**Error Handling:**
- Malformed markers (≠1 start/end, wrong order) → error, return 13, no write.
- Pre-fix manifest (old bare `CLAUDE.md` key, unmarked file on disk) →
  treated as "existing file without markers," wrapped in place — not an
  error, not malformed.

**Integration Points:** None beyond the two scripts.

---

## For Review Agents

**Acceptance Criteria:**
1. Hand-written `CLAUDE.md` + `install.sh --platform claude` → 100% of
   original content preserved, Writ block appended below.
2. No `CLAUDE.md` + install → created, wrapped in markers, matches
   `claude-code/CLAUDE.md`.
3. `--dry-run` shows real action (new/append/preserve), not "always updated."
4. Re-run with unmodified block → no-op; user-edited block → preserved +
   warning; template changed + block still at baseline → safe update.
5. Pre-fix install (unmarked file, old manifest key) → `update.sh` wraps in
   place without data loss or false "malformed" error.

**Business Rules:**
- One shared manifest key (`CLAUDE.md.writ-block`) across both scripts.
- `--force` always overwrites the inner block only — never content outside
  markers.
- Content outside markers is never touched, ever, including `--force`.
- Malformed markers are always an error, never auto-repaired.

**Experience Design:**
- Entry: same `install.sh`/`update.sh --platform claude` invocations.
- Happy path: per-file console line (new/updated/preserved), same tone as
  existing `AGENTS.md` reporting.
- Moment of truth: developer opens `CLAUDE.md` post-install, own content
  intact above a clearly delimited Writ block.
- Feedback: `--dry-run` preview line tells the truth; apply prints the
  real per-file action.
- Error: `❌` line + non-zero exit on malformed markers, no partial write.

---

## For Testing Agents

**Success Criteria:**
1. Full decision tree covered for both scripts: absent, unmarked-existing,
   clean-match, local-mod-preserved, `--force`, malformed→error.
2. `update.sh`-only: pre-fix-manifest upgrade case covered.
3. No existing `AGENTS.md`/other-file tests regress.

**Shadow Paths to Verify:**
- **Happy path:** fresh install, no prior file → wrapped block created.
- **Nil input:** `CLAUDE.md` absent → created (install) / restored (update).
- **Empty input:** `CLAUDE.md` exists but empty → treated as "no markers,"
  wrapped block appended to empty file (no leading blank-line artifacts).
- **Upstream error:** missing `claude-code/CLAUDE.md` template → clear error,
  matching `merge_agents_md`'s missing-template handling.

**Edge Cases:**
- Malformed markers (extra start/end, reversed order) → error, no write.
- Pre-fix manifest + unmarked file → wrap in place, not an error.
- `--force` with locally-modified block → block replaced, content outside
  markers untouched.

**Test Strategy:**
- Bash test scripts mirroring `scripts/tests/test_merge_agents_md.sh`
  (bundle-extract the function, run each case in an isolated `mktemp -d`
  workspace, assert file contents + exit codes).
