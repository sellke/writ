# Marker-Based `CLAUDE.md` Merge for `install.sh` and `update.sh`

> **Status:** Not Started
> **Created:** 2026-08-13
> **Owner:** @AdamSellke
> **Dependencies:** []
> **Origin:** Promoted from issue: `.writ/issues/bugs/2026-08-13-install-overwrites-existing-claude-md.md`

## Specification Contract

**Deliverable:** Give `CLAUDE.md` the same marker-bounded-block treatment
`AGENTS.md` already has in both `install.sh` and `update.sh`, so a
pre-existing hand-written `CLAUDE.md` is never silently destroyed, and both
scripts share one "already Writ-managed vs. hand-written" distinction via a
`CLAUDE.md.writ-block` manifest hash (mirroring `AGENTS.md.writ-block`).

**Must Include:** `install.sh` must never destroy pre-existing `CLAUDE.md`
content on the Claude platform's initial install — the exact failure this
issue reports.

**Hardest Constraint:** `update.sh`'s existing `CLAUDE.md` logic
(`update.sh:840-864`) compares the whole file's hash against the raw upstream
template. Once `install.sh` starts writing marker-wrapped content, that
comparison can never match the raw template again — `update.sh` must migrate
to inner-block hash tracking in the same spec, or every future
`/update-writ` run silently regresses to "preserved (local modifications)"
forever.

**📋 Business Rules:**
- Both scripts converge on one manifest key, `CLAUDE.md.writ-block` (inner
  block hash), fully replacing the old bare `CLAUDE.md` whole-file hash key.
- `--force` always overwrites the inner block in both scripts, consistent
  with existing `AGENTS.md` and other overlay behavior.
- Content outside the `<!-- writ:start -->`/`<!-- writ:end -->` markers is
  never touched by either script under any code path, including `--force`.
- Malformed markers (wrong count or order) are an error in both scripts —
  never guessed at or auto-repaired.
- A pre-fix installation (unmarked `CLAUDE.md` on disk, old bare `CLAUDE.md`
  manifest key) is treated as "existing file without markers" on first
  encounter by the upgraded script — wrapped in place, not treated as
  malformed or an error.

**Success Criteria:**
- A fresh project with a hand-written `CLAUDE.md`, after
  `install.sh --platform claude`, keeps 100% of its original content, with
  Writ's content appended in a marked block below it.
- A project with no `CLAUDE.md` gets one created, wrapped in markers, content
  matching `claude-code/CLAUDE.md`.
- `--dry-run` on `install.sh` shows the real action (new/append/preserve),
  not the current unconditional "always updated" claim.
- Re-running `install.sh`, or running `update.sh`, on an unmodified Writ
  block is a no-op; a user-edited block is preserved with a warning;
  upstream template changes propagate only when the local block still
  matches the manifest baseline.
- A pre-fix installation upgrades cleanly via `update.sh` into the
  marker-based model without data loss or a false "malformed" error.
- New/updated tests in `scripts/tests/` cover both scripts' full decision
  trees.

**Scope Boundaries:**
- Included: `install.sh` `CLAUDE.md` merge logic + manifest key, `update.sh`
  migration to match, dry-run preview fix, test coverage for both.
- Excluded: Cursor's `writ.mdc` / `system-instructions.md` (lower priority —
  Writ-authored artifacts, not user hand-written files; unchanged).
  Codex's `AGENTS.md` handling itself is unchanged — it's the pattern being
  copied. No new CLI flags beyond the existing `--force`.

**⚠️ Technical Concerns:**
- `update.sh`'s `merge_agents_md` is a separately-maintained duplicate of
  `install.sh`'s (no shared sourcing — both are standalone, curl-pipeable
  scripts). The new `merge_claude_md` will duplicate similarly across both
  files; comment each copy "keep synced," matching the existing convention.
- This is a manifest schema change (new `CLAUDE.md.writ-block` key retiring
  the bare `CLAUDE.md` key) — the upgrade edge case is a concrete acceptance
  criterion (Story 2), not just a note.

**💡 Recommendations:**
- Reuse `writ_compute_writ_block_inner_hash`, `writ_block_marker_counts`,
  `writ_file_ends_with_newline`, and `writ_rewrite_agents_md_with_inner`
  (or file-agnostic equivalents) rather than writing parallel helpers —
  they're already marker-position-agnostic (operate on any file passed in).

**⚠️ Cross-Spec Overlap:** None detected. The two other in-progress specs
(`2026-08-13-acceptance-criteria-traceability-ids`,
`2026-08-13-issue-adr-reconciliation`) don't touch `install.sh`, `update.sh`,
or `CLAUDE.md` handling.

## 🎯 Experience Design

This is a CLI script fix with no interactive UI; "experience" here means the
terminal output a developer sees when running `install.sh`/`update.sh`.

- **Entry point:** Same as today — `bash install.sh --platform claude` (fresh
  install) or `bash update.sh --platform claude` (existing install, e.g. via
  `/update-writ`).
- **Happy path (no pre-existing file):** Install creates `CLAUDE.md` wrapped
  in markers; output reads `✨ New: CLAUDE.md` (or equivalent), same tone as
  today's per-file install summary.
- **Happy path (pre-existing hand-written file):** Install appends the
  wrapped block below the user's content and reports something like
  `CLAUDE.md: Writ block appended (existing content preserved)` — the
  developer can `git diff` and see their original text untouched above a
  clearly delimited block.
- **Moment of truth:** The developer opens `CLAUDE.md` after install and
  finds their own instructions exactly as they left them, with Writ's
  content clearly demarcated below — no restore-from-git-history moment.
- **Feedback model:** Per-file console line during install/update
  (new/updated/preserved), plus `--dry-run` preview lines that now tell the
  truth about what will happen. No silent success.
- **Error experience:** Malformed markers print a clear `❌` error line and a
  non-zero exit code (matching `merge_agents_md`'s existing `return 13`
  convention) rather than silently corrupting the file.

## 📋 Business Rules (detailed)

See Specification Contract above for the authoritative list. Elaboration:

- **Decision tree (both scripts, per merge_agents_md precedent):**
  1. File absent → create, wrapped in markers. (`update.sh`: this is the
     `restore` action; `install.sh`: this is the `new`/creation path.)
  2. File exists, no markers found → append wrapped block below existing
     content, preserving everything above.
  3. File exists, malformed markers (≠1 start or ≠1 end, or wrong order) →
     error, non-zero exit, no write.
  4. File exists, well-formed markers, inner hash == upstream hash →
     unchanged, no-op.
  5. File exists, well-formed markers, inner hash == manifest baseline
     (`CLAUDE.md.writ-block`) and ≠ upstream → update (safe — matches last
     Writ-written state, upstream template has changed since).
  6. File exists, well-formed markers, inner hash matches neither upstream
     nor baseline → preserved, warning printed, unless `--force`.
  7. `--force` → always overwrite inner block (case 4-6 all become update).
- **Manifest migration:** `write_copy_manifest` (`install.sh`) and the
  manifest-writing step in `update.sh` write `CLAUDE.md.writ-block` (inner
  hash) instead of the current bare `CLAUDE.md` (whole-file hash) key. Old
  manifests with only the bare key are read as "no baseline for
  `CLAUDE.md.writ-block`" — falls into case 2 or case 6 above depending on
  whether markers happen to already be present (they won't be, pre-fix), so
  in practice always resolves to case 2 (wrap in place) on first encounter.

## Detailed Requirements

Derived from the source issue and the two discovery decisions (marker-based
merge over hash-preserve-and-skip; `update.sh` migration bundled into this
spec rather than filed separately):

1. `install.sh` gains a `merge_claude_md` function, structurally parallel to
   its existing `merge_agents_md` (`install.sh:235-396`), operating on
   `CLAUDE.md` / `claude-code/CLAUDE.md` instead of `AGENTS.md` /
   `codex/AGENTS.md.template`.
2. `install.sh`'s apply path (`install.sh:1053-1057`) and dry-run preview
   (`install.sh:951-952`) call `merge_claude_md` instead of the unconditional
   `cp`.
3. `install.sh`'s `write_copy_manifest` (`install.sh:520-530`, claude branch)
   writes the `CLAUDE.md.writ-block` inner-hash key.
4. `update.sh` gains its own `merge_claude_md`, structurally parallel to its
   existing `merge_agents_md` (`update.sh:318-407`), including the `restore`
   and `error` states, replacing the whole-file-hash `CLAUDE_MD_ACTION` logic
   (`update.sh:840-864`) and its apply step (`update.sh:975`).
5. Both scripts' `--dry-run`/preview output for `CLAUDE.md` reflects the real
   decision-tree outcome, not a hardcoded claim.
6. Test coverage: `scripts/tests/test_merge_claude_md.sh` for `install.sh`
   (mirroring `scripts/tests/test_merge_agents_md.sh`), plus equivalent
   coverage for `update.sh`'s variant including the pre-fix-manifest upgrade
   case.

## Implementation Approach

Bundle-extract each script's `merge_claude_md` for standalone testing the
same way `install.sh`'s `merge_agents_md` already is (see the
`# <<< writ-merge-bundled-begin/end >>>` markers at `install.sh:141` /
`install.sh:397`, and how `scripts/tests/test_merge_agents_md.sh` extracts
that chunk via `awk`). Since `install.sh` and `update.sh` are independent,
curl-pipeable scripts with no shared sourcing, `merge_claude_md` is
implemented once per script (structurally identical, "keep synced" by
comment convention) rather than factored into a shared library — consistent
with how `merge_agents_md` is already handled.
