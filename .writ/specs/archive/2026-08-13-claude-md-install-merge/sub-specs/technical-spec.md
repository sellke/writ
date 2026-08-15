# Technical Spec: Marker-Based CLAUDE.md Merge

> Parent spec: `../spec.md` | Stories: `../user-stories/story-1-install-merge.md`, `../user-stories/story-2-update-migration.md`

## Why This Isn't a Data-Flow Feature

This is a CLI installer/updater fix — no API routes, auth, payments, or
external integrations. Per `/create-spec`'s heuristic, the Error & Rescue Map
/ Shadow Paths tables are skipped; failure modes are instead captured as the
decision-tree cases below, which already enumerate every branch (they're
exhaustive by construction, mirroring `merge_agents_md`).

## Reused Building Blocks (do not reimplement)

All defined in `scripts/install.sh:141-231`, inside the
`# <<< writ-merge-bundled-begin (used by scripts/tests/test_merge_agents_md.sh — keep synced) >>>`
/ `# <<< writ-merge-bundled-end >>>` block. `update.sh` maintains its own
synced copies of the same functions (no shared sourcing — both scripts are
standalone, curl-pipeable).

| Function | Signature | Purpose |
|---|---|---|
| `writ_block_marker_counts` | `(file) -> "starts ends"` | Counts `<!-- writ:start -->` / `<!-- writ:end -->` lines. |
| `writ_compute_writ_block_inner_hash` | `(file) -> hash` (exit 2 on malformed) | Hashes only the content between one well-formed marker pair. |
| `writ_file_ends_with_newline` | `(file) -> bool` | Guards against a missing trailing newline before appending. |
| `writ_rewrite_agents_md_with_inner` | `(file, new_inner)` | Splices new inner content between existing markers, in place. Despite the name, it's marker-position-agnostic — safe to reuse verbatim for `CLAUDE.md` (pass `CLAUDE.md` as `file`). |
| `hash_file` | `(path) -> sha256` | Portable (shasum/sha256sum/openssl fallback). |
| `manifest_hash_for` | `(key) -> hash or empty` | Greps `MANIFEST_FILE` for a `<hash>  <key>` line. |

None of these need modification — they already operate on an arbitrary
`$file` parameter, not a hardcoded `AGENTS.md` path.

## Story 1: `install.sh` — `merge_claude_md`

**New function**, placed inside (or immediately adjacent to, still within the
bundle markers) the existing `merge_agents_md` in `install.sh:235-396`, so
`scripts/tests/test_merge_claude_md.sh` can extract it via the same
`awk`-between-bundle-markers technique `test_merge_agents_md.sh` already uses.

```
merge_claude_md() {
  local op="${1:-apply}"   # preview | apply
  local template="$WRIT_SRC/claude-code/CLAUDE.md"
  local target="CLAUDE.md"
  # ... upstream_inner, upstream_hash = cat/hash $template
  # ... decision tree below, structurally identical to merge_agents_md
}
```

**Decision tree** (see spec.md → 📋 Business Rules (detailed) → Decision tree
for the authoritative numbered list; this restates it against exact call
sites):

1. `$target` absent → write `<!-- writ:start -->` / upstream_inner /
   `<!-- writ:end -->` as the entire new file. Note (preview) /
   `CLAUDE_MD_NOTE`/similar (apply).
2. `$target` exists, `writ_block_marker_counts` returns `0 0` → append: copy
   existing content, ensure trailing newline (`writ_file_ends_with_newline`),
   then append the wrapped block.
3. `$target` exists, counts ≠ `1 1`, or `start_line >= end_line` → error,
   `return 13`, no write in apply mode.
4. Well-formed markers, `inner_hash == upstream_hash` → unchanged, no write.
5. Well-formed markers, `inner_hash == manifest_hash_for "CLAUDE.md.writ-block"`
   (and ≠ upstream) → update via `writ_rewrite_agents_md_with_inner`.
6. Well-formed markers, matches neither → preserved, warning, no write
   (unless `--force`).
7. `FORCE=true` → treat as case 5 regardless of which of 4/6 it would
   otherwise be.

**Call site changes:**
- `install.sh:1053-1057` (apply phase, claude branch): replace
  `cp "$WRIT_SRC/claude-code/CLAUDE.md" "CLAUDE.md"` with
  `merge_claude_md apply`.
- `install.sh:951-952` (dry-run preview, claude branch): replace
  `echo "  Root:    CLAUDE.md → always updated"` with
  `echo "  Root:    CLAUDE.md:"` + `merge_claude_md preview` (mirroring the
  codex branch's `echo "  AGENTS.md integration plan:"` +
  `merge_agents_md preview` at install.sh:954-955).
- `install.sh:526-529` (`write_copy_manifest`, claude branch): replace the
  bare `echo "$(hash_file "CLAUDE.md")  CLAUDE.md"` with computing
  `writ_compute_writ_block_inner_hash "CLAUDE.md"` and writing
  `<inner_hash>  CLAUDE.md.writ-block` — mirroring the codex branch's
  `AGENTS.md.writ-block` write at install.sh:532-536.

**Test file:** `scripts/tests/test_merge_claude_md.sh`, structured like
`scripts/tests/test_merge_agents_md.sh` (`setup_ws`, `load_merge_bundle` via
awk extraction between the bundle markers, one `mktemp -d` workspace per
case). Minimum cases: absent → created+wrapped; existing without markers →
appended, original content intact above the block; clean markers matching
upstream → unchanged; locally-modified block → preserved + non-zero-ish
warning path, file untouched; `--force` → overwritten despite local
modification; malformed markers (extra/missing/reordered) → error, `CLAUDE.md`
left byte-for-byte untouched.

## Story 2: `update.sh` — `merge_claude_md` (migration)

**Replaces** the whole-file-hash `CLAUDE_MD_ACTION` block at
`update.sh:840-864` and the apply-phase conditional at `update.sh:975`, with
a function structurally identical to update.sh's own `merge_agents_md`
(`update.sh:318-407`) — same five action states (`unchanged`, `restore`,
`error`, `update`, `preserved`), same `restore` semantics for "file absent"
*and* "file exists but has zero markers" (update.sh:336-371).

**Manifest key:** reads/writes `CLAUDE.md.writ-block` (inner hash) — the
exact key Story 1 introduces. No new key invented independently; if Story 1's
key name changes during implementation, Story 2 must follow it.

**Reporting wiring** (mirrors `AGENTS_MD_ACTION`'s existing wiring exactly):
- Preview: call site parallel to `update.sh:867` (`merge_agents_md preview`)
  and the `case "$AGENTS_MD_ACTION" in preserved) ...` block at
  `update.sh:868-874` that feeds `TOTAL_PRESERVED` / `ALL_PRESERVED_FILES`.
- Actionable count: parallel to `update.sh:887,889` — `update`/`new` (or
  `restore`, matching AGENTS.md's convention) count as actionable.
- Apply: parallel to `update.sh:980-981` — call `merge_claude_md apply` when
  the action is `update` or `restore`.

**Upgrade edge case (hard acceptance criterion, Story 2):** a manifest
written by a pre-fix `install.sh`/`update.sh` has only the bare `CLAUDE.md`
(whole-file hash) key — no `CLAUDE.md.writ-block` key exists yet, and the
on-disk `CLAUDE.md` has zero markers. `manifest_hash_for "CLAUDE.md.writ-block"`
correctly returns empty in this case (it's a plain grep for a key that isn't
there), and `writ_block_marker_counts` correctly returns `0 0` for the
unmarked file — so this scenario naturally falls into decision-tree case 2
(`restore`: wrap in place) with zero special-casing required, *provided* the
marker-count check runs before any manifest-baseline lookup. Verify this
ordering explicitly in the test for this case — it's the crux of "upgrade
doesn't error."

**Test coverage:** extend or add an update.sh-focused test file
(`scripts/tests/test_update_claude_md.sh` or fold into an existing
update.sh test harness if one exists at implementation time — check
`scripts/tests/` first) covering the same six cases as Story 1's test file,
plus the upgrade-edge-case scenario (old bare-key manifest + unmarked file →
`restore`, not `error`).

## Manifest Schema Note

Both scripts converge on:

```
<sha256>  CLAUDE.md.writ-block
```

replacing:

```
<sha256>  CLAUDE.md
```

The old key is simply never written again after this spec ships; no explicit
migration/deletion step is needed since `manifest_hash_for` only ever reads
the key it's asked for, and stale unrelated lines in a manifest file are
otherwise harmless (same as how `AGENTS.md.writ-block` coexists with any
other keys already in the manifest).
