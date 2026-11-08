# Platform-Neutral Names (Lite)

> Source: .writ/specs/2026-10-20-platform-neutral-names/spec.md
> Purpose: Efficient AI context for implementation

## For Coding Agents

**Deliverable:** No shipped command names a one-platform tool; Writ's `/design` becomes `/writ-design`, so it no longer collides with Claude Code's native `/design`.

**Implementation Approach:**
- Capability name `canvas-preview`. `prototype.md` Step 2 and Step 2.5 use it. Each adapter's tool table gets one `` | `canvas-preview` | `` row with the mapping and the fixed clause "No renderer: write a structural description of each draft and say the drafts were not rendered."
- Mappings: Cursor → `cursor-ide-browser` canvas; Claude Code → artifact or preview pane; Codex, OpenClaw → one self-contained HTML file per draft in `.writ/prototypes/<date>-<slug>/`.
- `git mv commands/design.md commands/writ-design.md`. Change only self-naming lines. Manifest entry renamed and moved to sorted position (after `verify-spec`). No alias.
- Regenerate `SKILL.md` (`gen-skill.sh`) and `claude-code/CLAUDE.md` (`python3 scripts/gen-claude-md.py`, from the parity spec). Never hand-edit either.
- Upgrade uses stale detection only. No rename map in `update.sh`.
- Commit footer `BREAKING CHANGE: /design is renamed to /writ-design`.

**Files in Scope:**
- `commands/prototype.md`, `adapters/{cursor,claude-code,codex,openclaw}.md` — capability (S1)
- `commands/writ-design.md`, `.writ/manifest.yaml`, `SKILL.md`, `claude-code/CLAUDE.md`, `codex/AGENTS.md.template`, `README.md`, `adapters/cursor.md` tree, `commands/{create-spec,create-adr,research,status,prototype}.md`, `create-spec.lean.md` if present, `.writ/docs/model-tiers.md`, `scripts/eval.sh` allowlist, both `status.md` command lists, the `create-spec.md` byte ledger in `scripts/tests/test_governor_enforcement.py` — rename (S2)
- `scripts/tests/test_platform_neutral_names.py` (S1–S3), `scripts/tests/test_install_update_writ_design.sh` (S3), both origin issues (S3)

**Error Handling:**
- No renderer or no write access → structural description, said out loud.
- Modified old `design.md` → kept; `⚠️  Stale (no longer shipped, locally modified — kept): commands/design.md` every run (needs `2026-10-20-ci-and-update-integrity`; if absent, stop and report).
- `scripts/gen-claude-md.py` missing → stop, report blocked; no hand edit.
- `git grep` exit ≥2 → gate fails, never passes.

**Integration Points:**
- `2026-10-20-claude-code-parity` lands first (edits `adapters/claude-code.md`, owns the CLAUDE.md generator).
- Other Phase 13 specs may edit `create-spec.md`, `prototype.md`, `*.lean.md`. Find text by section, re-run the inventory grep first.

See spec.md → ## Business Rules (Expanded) and sub-specs/technical-spec.md → ## Reference Inventory.

---

## For Review Agents

**Acceptance Criteria:**
1. `prototype.md` names `canvas-preview` in Step 2 and Step 2.5, keeps "Never degrade silently.", and has no `cursor-ide-browser` `[AC-1.1]`
2. All four adapters carry one `canvas-preview` row with the contracted mapping and the degradation clause `[AC-1.2, AC-1.3, AC-1.4]`
3. `git grep cursor-ide-browser` hits only `adapters/cursor.md` and record paths `[AC-1.5]`
4. `writ-design.md` replaces `design.md` with a name-only diff; manifest, `SKILL.md`, and generated `CLAUDE.md` agree `[AC-2.1, AC-2.2, AC-2.4]`
5. Every rename-class inventory line is updated, including eval allowlist rows and `model-tiers.md`; keep-class lines are untouched `[AC-2.3, AC-2.5]`
6. Fresh installs on cursor, claude, codex create `writ-design.md` and no `design.md` `[AC-3.1]`
7. Update removes an unmodified old `design.md`, and keeps and warns on a modified one, on every run `[AC-3.2, AC-3.3]`
8. The reference gate passes on the repo, and its fixture proves it reports and ignores the right lines `[AC-3.4]`
9. Both issues have `## Resolution`; the Upgrade Note matches observed update output `[AC-3.5]`

**Business Rules:**
- Commands name capabilities; adapters name tools.
- Rename changes names only: no mode, flag, or output change. No `design` alias.
- Generated files are regenerated, never hand-edited.
- Gate record list = contract paths with all of `.writ/specs/` (DEV-004) + `.writ/context.md` (DEV-006) + three named dated snapshots. Native refs must read "native `/design`".
- Never run `install.sh`/`update.sh` against the Writ repo; temp dirs only.

**Experience Design:**
- Entry: `/prototype` Step 2.5, `update.sh`, or typing `/writ-design`.
- Happy path: drafts render via the adapter's tool; update swaps the file.
- Moment of truth: `/writ-design` opens Writ's flow unchanged; `/design` no longer does.
- Feedback: update prints `🗑  Removed: commands/design.md`.
- Error: unrendered drafts are said to be unrendered.

---

## For Testing Agents

**Success Criteria:**
1. `uv run --python 3.9 pytest` passes, including `scripts/tests/test_platform_neutral_names.py`.
2. `for t in scripts/tests/test_*.sh; do bash "$t" || echo "FAIL $t"; done` prints no FAIL.
3. `bash scripts/eval.sh` (outside the sandbox): 0 findings.

**Shadow Paths to Verify:**
- **Happy path:** gate returns `[]`; old install upgrades cleanly.
- **Nil input:** project without a manifest entry for `design.md` → file left alone (out of scope).
- **Empty input:** `git grep` exit 1 → gate passes with no hits.
- **Upstream error:** `git grep` exit ≥2, or not a repo → gate fails.

**Edge Cases:**
- `design-system.md`, `/writ-design`, "roadmap/design" → not reported.
- "`/design` uses native browser tools" → reported.
- Update run twice → no further output about `design.md`.
- Dry run → lists stale, removes nothing.

**Test Strategy:**
- Static pytest for prototype, adapters, registration, gate; gate fixture in a `tmp_path` git repo.
- Bash install/update test from committed source copies (`SRC_NEW`, `SRC_OLD`) in temp dirs.
- Mutation check: point `SRC_NEW` at `SRC_OLD` once and see the fresh-install case fail.
