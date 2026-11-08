# Technical Spec: Platform-Neutral Names

> Spec: [`../spec.md`](../spec.md) · Issues: [`prototype-visual-preview-cursor-only`](../../../issues/bugs/2026-10-19-prototype-visual-preview-cursor-only.md), [`design-command-name-collision`](../../../issues/bugs/2026-10-19-design-command-name-collision.md)

## Current State (audit, 2026-10-20)

- **`cursor-ide-browser`.** One match in shipped source: `commands/prototype.md` Step 2, the "Figma MCP detection" sentence. PR #59 already rewrote Step 2.5 into a three-row "Render through the platform" table that names no tool and says "See the adapter for the platform's capability name. Never degrade silently." No adapter has such a row, so that pointer leads nowhere. The other matches are records: ADR-030, the origin issue, the roadmap, and two research files.
- **Adapter tool tables.** `adapters/cursor.md` § Native Tool Availability (`Tool | Used By | Purpose`); `adapters/claude-code.md` § Tool Mapping (Cursor → Claude Code) → Quick Reference (`Cursor Tool | Claude Code Native | Notes`); `adapters/codex.md` § Tool Mapping (Cursor → Codex CLI) → Quick reference — orchestration primitives (`Cursor / Writ generic | Codex CLI | Notes`); `adapters/openclaw.md` § Quick Reference (`Cursor Tool | OpenClaw Equivalent | Notes`). None has a visual or canvas row.
- **Command placement.** `install.sh` and `update.sh` copy `commands/*.md` (minus unshipped `*.lean.md` siblings) into `<platform_dir>/commands/` for `cursor` (`.cursor`), `claude` (`.claude`), and `codex` (`.codex`). There is no `--platform openclaw`. The manifest records each file as `commands/<name>.md`.
- **Stale handling.** `update.sh` `detect_stale_files` marks a manifest path stale when the upstream file is gone. An unmodified stale file is removed (`🗑  Removed: <path>`). A modified one is warned about and kept only under `scripts/`. In other categories it is re-baselined from the local copy and deleted on the next run. `2026-10-20-ci-and-update-integrity` fixes that for every category.
- **Generated catalogs.** `SKILL.md` comes from `scripts/gen-skill.sh` (reads `.writ/manifest.yaml`). `claude-code/CLAUDE.md` is hand-maintained today; `2026-10-20-claude-code-parity` adds `scripts/gen-claude-md.py` (dev-only, with `--check`) and an eval check. Its technical spec already expects this rename: `--check` reports `missing <new>` and `extra <old>` until the template is regenerated. `codex/AGENTS.md.template` is hand-maintained, and its purposes are stale and truncated. `codex/agents/*.toml` come from `scripts/gen-codex-agent-tomls.py` and do not name the command.
- **Eval.** `check_manifest` fails if a manifest `file:` is missing or a `commands/*.md` file is unregistered. `check_referenced_paths` has five allowlist rows whose creating command is `/design`. Its stale-row pass runs only when `commands/<cmd>.md` exists, so after the rename those rows would be skipped with no finding unless they are renamed too. No eval check pins `prototype.md` Step 2.5 text or the adapters' tool tables.
- **Manifest order.** The `commands:` list is sorted by name (`sort -c` passes).

## Canvas-Preview Capability (Story 1)

### `commands/prototype.md`

| Location | Today | After |
|---|---|---|
| § Step 2: Context Scan → "Figma MCP detection" | if `` `cursor-ide-browser` `` MCP and `design-system.md` or Figma MCP server are available, note in context … | if the `` `canvas-preview` `` capability (see the adapter) and `design-system.md` or a Figma MCP server are available, note in context … (rest unchanged) |
| § Step 2.5 → Render through the platform, middle row label | `Artifact / canvas / preview pane` | `` `canvas-preview` `` (the adapter maps it) |
| § Step 2.5 → Render through the platform, sentence under the table | See the adapter for the platform's capability name. Never degrade silently. | Each adapter maps `canvas-preview` to its own tool and states what to do when it has none. Never degrade silently. |

The first row ("Native artboard/design surface") and the third row ("Neither → a written structural description per draft — say plainly that drafts were not rendered") stay as they are.

### Adapter rows

Add one row to each table named in Current State. The first cell is always `` `canvas-preview` ``. Every row ends with the same degradation clause.

Degradation clause (verbatim): `No renderer: write a structural description of each draft and say the drafts were not rendered.`

| Adapter | Row (cells after the first) |
|---|---|
| `adapters/cursor.md` | `prototype (Step 2.5)` · `` The `cursor-ide-browser` canvas renders each draft. `` + clause |
| `adapters/claude-code.md` | `An artifact, or the preview pane` · `One self-contained HTML page per draft.` + clause |
| `adapters/codex.md` | `` `Write` one self-contained HTML file per draft to `.writ/prototypes/<date>-<slug>/` `` · `Inline CSS, no network fetch; give the user each path. Includes a read-only sandbox.` + clause |
| `adapters/openclaw.md` | `` `Write({ path: ".writ/prototypes/<date>-<slug>/<draft>.html" })`, one self-contained file per draft `` · `Inline CSS, no network fetch; send the user each path. Includes a run that cannot write files.` + clause |

Put the clause in the last cell. The Codex and OpenClaw folder is the same one `/prototype` writes `exploration.md` to, so drafts and the decision record sit together.

### Test (`scripts/tests/test_platform_neutral_names.py`, canvas section)

| Test | Assertion |
|---|---|
| `test_prototype_names_capability` | `commands/prototype.md` contains `canvas-preview` inside § Step 2 and inside § Step 2.5; contains no `cursor-ide-browser`; still contains `Never degrade silently.` |
| `test_adapter_canvas_row[<adapter>]` | Exactly one line in the adapter starts with `` | `canvas-preview` | ``. It contains the platform keyword(s) (cursor: `cursor-ide-browser`; claude-code: `artifact` and `preview pane`; codex, openclaw: `.writ/prototypes/<date>-<slug>/` and `HTML`) and both `structural description` and `not rendered`. |
| `test_cursor_ide_browser_confined` | Every `git grep -n --null cursor-ide-browser` hit is `adapters/cursor.md` or a record path (see Reference Gate → Record list). |

## Rename (Story 2)

### File edits

| File | Edit |
|---|---|
| `commands/design.md` → `commands/writ-design.md` | `git mv`. Then: frontmatter `name: design` → `name: writ-design`; H1 `# Design Command (design)` → `# Design Command (writ-design)`; § Invocation table, five `/design` → `/writ-design`; § Visual References in Stories "(added by `/design` or `/create-spec`)" → `/writ-design`; § References related-commands row "Generates specs that `/design` adds visuals to" → `/writ-design`. Nothing else. |
| `.writ/manifest.yaml` | Entry becomes `name: writ-design`, `file: commands/writ-design.md`; move it after `verify-spec`; keep `category`, `purpose`, `tags`; no `aliases`. |
| `SKILL.md` | `bash scripts/gen-skill.sh`, then `--check` prints `pass`. The row moves to the end of the Planning & Specification table. |
| `claude-code/CLAUDE.md` | `python3 scripts/gen-claude-md.py`, then `python3 scripts/gen-claude-md.py --check` prints `pass` (added by `2026-10-20-claude-code-parity`). Never hand-edit. |
| `codex/AGENTS.md.template` | Planning & Specification row: `` `/writ-design` `` · `` `.codex/commands/writ-design.md` `` · same purpose; move it after `/verify-spec`. Hand edit, unless the parity spec has put this file under a generator by then. In that case, regenerate it. |
| `README.md` | § Commands → Planning & Specification row `` `/design` `` → `` `/writ-design` ``. |
| `adapters/cursor.md` | § Directory Structure tree: the `design.md  # /design` line becomes `writ-design.md  # /writ-design` in sorted position (last, `└──`). `verify-spec.md` becomes `├──`. Count stays 32. |
| `commands/create-spec.md` | § Step 1.5 "generate" bullet: "wireframe conventions from `/writ-design` command". |
| `commands/create-spec.lean.md` | Same bullet, if the file still exists (the Phase 13 cuts spec deletes lean siblings). |
| `commands/create-adr.md`, `commands/research.md` | Related-commands table row `` `/design` `` → `` `/writ-design` ``. |
| `commands/status.md` | The comma-separated command list: `/design` → `/writ-design`. |
| `commands/prototype.md` | § When to Use table row "Mockups for a spec that already exists" and § Completion terminal constraint "drafts for a spec that already exists are `/design`" → `/writ-design`. |
| `.writ/docs/model-tiers.md` | Entry-level table, `high` row: `` `design` `` → `` `writ-design` `` (move it to sorted position). Count stays 15. |
| `scripts/eval.sh` | `referenced_paths_allowlist`: the five rows with creating command `/design` → `/writ-design`, column 2 and reason text. |

### Commit

The commit message carries `BREAKING CHANGE: /design is renamed to /writ-design` as a footer, so `/release` Step 1.2 picks it up.

### Test (`scripts/tests/test_platform_neutral_names.py`, registration section)

| Test | Assertion |
|---|---|
| `test_writ_design_file` | `commands/writ-design.md` exists, frontmatter `name: writ-design`; `commands/design.md` does not exist. |
| `test_manifest_entry` | Manifest has `name: writ-design` with `file: commands/writ-design.md`, no command named `design`, no `aliases` containing `design`, and the commands list is sorted. |
| `test_skill_catalog` | `bash scripts/gen-skill.sh --check` first line is `pass`; `SKILL.md` has the `` `/writ-design` `` row. |
| `test_eval_allowlist_rows` | No `referenced_paths_allowlist` row in `scripts/eval.sh` has `/design` as its creating command; the five path rows name `/writ-design`. |

## Reference Inventory (2026-10-20)

Command: `git grep -n -e '/design' -e 'design\.md'` → **137 lines**.

| Class | Lines | Action |
|---|---|---|
| Writ-command reference | 25 grep lines + 4 the grep misses | Rename |
| Not a command reference (`design-system.md` paths, "roadmap/design", "artboard/design") | 13 | Keep |
| Historical record, dated snapshot outside the listed paths | 7 | Keep; named in the gate's record list |
| Historical record, listed paths | 92 | Keep |
| Claude Code native `/design`, active files | 0 | — (12 native mentions sit inside the 92 record lines) |

### Active-file matches (45)

| File:line | Text (abridged) | Class | Action |
|---|---|---|---|
| `.writ/manifest.yaml:60` | `file: commands/design.md` | Writ command | Rename (with line 59 `name: design`) |
| `README.md:112` | `` `/design` `` table row | Writ command | Rename |
| `SKILL.md:53` | `` `/design` `` · `commands/design.md` | Writ command | Regenerate |
| `adapters/cursor.md:40` | `design.md  # /design` | Writ command | Rename |
| `claude-code/CLAUDE.md:33` | `` `/design` `` · `.claude/commands/design.md` | Writ command | Regenerate (parity generator) |
| `codex/AGENTS.md.template:19` | `` `/design` `` · `.codex/commands/design.md` | Writ command | Rename |
| `commands/create-adr.md:210` | related-commands row | Writ command | Rename |
| `commands/create-spec.md:518` | "wireframe conventions from `/design` command" | Writ command | Rename |
| `commands/create-spec.lean.md:367` | "Follow `/design` wireframe conventions" | Writ command | Rename if the file exists |
| `commands/design.md:25-29` | invocation table (5 lines) | Writ command | Rename |
| `commands/design.md:194` | "added by `/design` or `/create-spec`" | Writ command | Rename |
| `commands/design.md:237` | "specs that `/design` adds visuals to" | Writ command | Rename |
| `commands/prototype.md:315` | When to Use row | Writ command | Rename |
| `commands/prototype.md:329` | terminal constraint | Writ command | Rename |
| `commands/research.md:167` | related-commands row | Writ command | Rename |
| `commands/status.md:249` | command list | Writ command | Rename |
| `scripts/eval.sh:622,624,625,626,627` | allowlist rows, creating command `/design` | Writ command | Rename |
| `.writ/docs/model-tiers.md:68` | "spec/ADR/roadmap/design" | Not a reference | Keep |
| `agents/visual-qa-agent.md:43,144` | `.writ/docs/design-system.md` | Not a reference | Keep |
| `codex/agents/visual-qa-agent.toml:48,149` | `.writ/docs/design-system.md` | Not a reference | Keep |
| `commands/create-spec.md:525` | `.writ/docs/design-system.md` | Not a reference | Keep |
| `commands/create-spec.lean.md:371` | `.writ/docs/design-system.md` | Not a reference | Keep |
| `commands/design.md:50,179` | `.writ/docs/design-system.md` | Not a reference | Keep |
| `commands/implement-story.md:116` | `.writ/docs/design-system.md` | Not a reference | Keep |
| `commands/implement-story.lean.md:112` | `.writ/docs/design-system.md` | Not a reference | Keep |
| `commands/prototype.md:117` | `.writ/docs/design-system.md` | Not a reference | Keep |
| `commands/prototype.md:171` | "Native artboard/design surface" | Not a reference | Keep |
| `.writ/docs/leanness-audit-2026-07-11.md:41,67` | dated 2026-07-11 audit | Record (snapshot) | Keep |
| `.writ/docs/swot-2026-03-01.md:30,56,88` | dated 2026-03-01 SWOT | Record (snapshot) | Keep |
| `.writ/explanations/2026-03-20-WritPipelineArchitecture .md:32,97` | dated 2026-03-20 diagram | Record (snapshot) | Keep |

### Rename-class references the grep misses (4)

| File | Text | Why the grep misses it |
|---|---|---|
| `.writ/manifest.yaml:59` | `- name: design` | Bare name |
| `commands/design.md:2` | `name: design` | Bare name |
| `commands/design.md:13` | `# Design Command (design)` | Bare name |
| `.writ/docs/model-tiers.md:75` | `` `design` `` in the `high` entry-level list | Bare name |

### Record-path matches (92)

`.writ/specs/archive/` 44 · `.writ/research/` 31 · `.writ/issues/` 7 · `.writ/product/` 6 · `.writ/decision-records/` 2 · `CHANGELOG.md` 2. All kept. Claude Code's native command is named in the collision issue (lines 1, 11, 16), the roadmap (595, 674), and the prototype research (51, 122, 134, 209, 227, 238, 262).

Story 2 re-runs the grep before editing, because other Phase 13 specs may have moved or removed lines since this audit.

## Reference Gate (Story 3)

Function `writ_design_refs(root: Path) -> list[str]` in `scripts/tests/test_platform_neutral_names.py`:

1. Run `git -C <root> grep -n -I --null -e '/design' -e 'design\.md'`. Exit 1 means no matches, so return `[]`. Exit 2 or higher is an error: fail with stderr.
2. Parse each hit as `path\0line\0text`. `--null` keeps paths with spaces intact.
3. Keep a hit only if `text` matches `CMD = re.compile(r"(?<![\w-])/design(?![\w-])")` or `FILE = re.compile(r"(?<![\w-])design\.md")`. These drop `.writ/docs/design-system.md`, `/writ-design`, `writ-design.md`, "roadmap/design", and "artboard/design".
4. Drop a hit whose path is in the record list.
5. Drop a hit whose `text` matches `` NATIVE = re.compile(r"native\s+`?/design(?![\w-])", re.I) ``. A line about Claude Code's own command must write it as "native `/design`". The word "native" elsewhere on the line does not exempt it.
6. Return the rest as `path:line: text`.

### Record list

```python
RECORD_PREFIXES = (
    "CHANGELOG.md",
    ".writ/specs/archive/",
    ".writ/research/",
    ".writ/decision-records/",
    ".writ/product/",
    ".writ/decision-log.md",
    ".writ/issues/",
    ".writ/specs/2026-10-20-platform-neutral-names/",  # this spec describes the rename
    ".writ/specs/2026-10-20-claude-code-parity/",  # its technical spec cites the rename as a generator edge case
)
DATED_SNAPSHOTS = {
    ".writ/docs/leanness-audit-2026-07-11.md": "dated leanness audit",
    ".writ/docs/swot-2026-03-01.md": "dated SWOT analysis",
    ".writ/explanations/2026-03-20-WritPipelineArchitecture .md": "dated pipeline explanation",
}
```

`test_cursor_ide_browser_confined` uses the same list, plus `adapters/cursor.md`.

If the gate names a path in another `.writ/specs/<folder>/` (an in-flight Phase 13 spec), that folder is a record of planned work. Add it to `RECORD_PREFIXES` with a one-line reason and log it in the drift log. Never add a shipped path (`commands/`, `agents/`, `adapters/`, `skills/`, `scripts/`, `.writ/docs/` other than the named snapshots, `claude-code/`, `codex/`, `cursor/`, `SKILL.md`, `README.md`, `system-instructions.md`, `.writ/manifest.yaml`).

### Tests

| Test | Assertion |
|---|---|
| `test_no_writ_design_reference` | `writ_design_refs(REPO) == []`; on failure, the message lists every hit. |
| `test_gate_fixture` | In a `tmp_path` git repo (`git init`, `git add`), the gate reports exactly: `commands/a.md` (`` `/design` ``), `commands/b.md` (`` `commands/design.md` ``), `commands/f.md`, and `.writ/specs/2026-01-01-other/spec.md` (`/design`). `commands/f.md` holds "`/design` uses native browser tools". It ignores `commands/c.md` (`.writ/docs/design-system.md`), `commands/d.md` (`/writ-design`, `commands/writ-design.md`), `commands/e.md` ("roadmap/design"), `adapters/x.md` ("Claude Code's native `/design`"), `CHANGELOG.md`, `.writ/docs/swot-2026-03-01.md`, and `.writ/specs/2026-10-20-platform-neutral-names/spec.md`. |
| `test_gate_git_error` | Pointing the gate at a non-repo `tmp_path` raises a failure, not an empty pass. |

## Upgrade Path Test (Story 3)

File: `scripts/tests/test_install_update_writ_design.sh`. Follow `scripts/tests/test_install_update_dev_scripts.sh` (tar copy of the working tree excluding `.git`, `.cursor`, `.claude`, `.codex`, `.writ`; copy `.writ/docs/*.md`; `git init`; `commit_src`; `fail`; `hash_file`). It runs `git init`, so run it outside any sandbox.

| Fixture | Built how |
|---|---|
| `SRC_NEW` | The committed copy. Assert `commands/writ-design.md` exists and `commands/design.md` does not. |
| `SRC_OLD` | `cp -R SRC_NEW`; `git mv commands/writ-design.md commands/design.md`; set its frontmatter back to `name: design`; commit. This stands in for the last release. |

| Case | Platforms | Steps | Assertions |
|---|---|---|---|
| Fresh install (AC-3.1) | cursor, claude, codex | `install.sh --platform <p> --no-commit` from `SRC_NEW` in a temp dir | `<pdir>/commands/writ-design.md` exists; `<pdir>/commands/design.md` absent; manifest has `commands/writ-design.md`, lacks `commands/design.md` |
| Unmodified upgrade (AC-3.2) | cursor, claude, codex | Install from `SRC_OLD`; check fixture sanity (`design.md` present and in manifest); `WRIT_REPO=SRC_NEW update.sh --dry-run`; then a real update | Dry run prints `🗑  commands/design.md` and removes nothing; the real run prints `🗑  Removed: commands/design.md`, removes the file, installs `writ-design.md`; manifest lacks `commands/design.md` |
| Modified upgrade (AC-3.3) | claude | Install from `SRC_OLD`; append `# local edit` to `.claude/commands/design.md`; update twice | File byte-identical after both runs; each run prints the stale-kept warning naming `commands/design.md` |

`2026-10-20-ci-and-update-integrity` keeps the warning text byte-identical to today's and names the manifest-relative path, so the expected line is `⚠️  Stale (no longer shipped, locally modified — kept): commands/design.md`. Read `detect_stale_files` and the removal block in `scripts/update.sh` after that spec lands and confirm the text before asserting it. The second update has nothing else to do and exits through the "Already up to date" path; that spec requires the warning on that path too, so assert it there.

To prove the assertions can fail, point `SRC_NEW` at `SRC_OLD` in a scratch copy of the test and confirm the fresh-install case fails. Record the output in What Was Built.

## Error & Rescue Map

| Operation | What Can Fail | Planned Handling | Test Strategy |
|---|---|---|---|
| Render drafts via `canvas-preview` | Platform has no artifact, canvas, or preview tool | The agent writes a structural description per draft and tells the user the drafts were not rendered | `test_adapter_canvas_row` checks the clause in all four rows |
| Write HTML drafts (Codex, OpenClaw) | Read-only sandbox, or the write fails | Same structural description, said out loud; the agent does not claim files it did not write | Row text; markdown has no runtime test |
| Fresh install | `design.md` still shipped, or `writ-design.md` missing | Test fails naming the platform and path | Bash fresh-install case, three platforms |
| Update, unmodified `design.md` | Not listed in the project's manifest (hand-copied install) | `[OUT OF SCOPE — update.sh only removes what its manifest recorded; an untracked file is the user's]`. The Upgrade Note tells users to delete it. | — |
| Update, unmodified `design.md` | Listed in manifest | Removed and reported | Bash unmodified case |
| Update, modified `design.md` | Kept once, then deleted on the next run (today's bug) | Relies on `2026-10-20-ci-and-update-integrity`; if it has not landed, AC-3.3 fails and the story stops and reports. `update.sh` is not patched here. | Bash modified case, two runs |
| Rename sweep | A reference is missed | The gate prints `path:line: text` | `test_no_writ_design_reference` + fixture |
| Eval allowlist rows left as `/design` | Stale-row check skips them, no finding | Rows renamed; test asserts it; the gate also scans `scripts/eval.sh` | `test_eval_allowlist_rows` |
| Regenerate `claude-code/CLAUDE.md` | `scripts/gen-claude-md.py` not present (parity spec not landed) | Stop and report blocked; never hand-edit | Story 2 task checks the generator first |
| `SKILL.md` | Drifts from the manifest | Regenerate | `test_skill_catalog`, eval `check_manifest` |
| Gate run | `git grep` errors (exit ≥2) | Test fails with stderr; never reads as a pass | `test_gate_git_error` |
| Native `/design` behavior on the user's Claude Code | Older version without it; or it shadows differently than reported | `[OUT OF SCOPE — platform behavior; the rename removes the collision either way]` | — |

## Shadow Paths

| Flow | Happy Path | Nil Input | Empty Input | Upstream Error |
|---|---|---|---|---|
| `/prototype` Step 2.5 render | Each draft rendered by the adapter's tool | No `canvas-preview` row (prevented by test) → the agent says the drafts were not rendered | User stops before drafts → nothing rendered, decision recorded | Renderer errors → structural description, said out loud |
| Upgrade an old install | `design.md` removed, `writ-design.md` installed, CHANGELOG note | No manifest → `design.md` left untracked, Upgrade Note covers it | Project with no commands dir → `writ-design.md` installed | `WRIT_REPO` clone fails → `update.sh` exits as today, nothing changed |
| Reference gate | Zero hits | `git` missing → test errors | No matches (`git grep` exit 1) → pass | `git grep` exit ≥2 → fail with stderr |

## Interaction Edge Cases

| Edge Case | Planned Handling |
|---|---|
| Update run twice | Second run finds nothing stale for `design.md`; no output about it |
| User kept a modified `design.md` on Claude Code | `.claude/commands/design.md` still answers `/design` in that project until they delete it; the stale warning repeats every run, and the Upgrade Note says to move edits into `writ-design.md` |
| `update.sh --force` | Stale detection ignores `--force`; a modified `design.md` is still kept |
| Dry run | Lists `design.md` as stale, changes nothing |
| User's own files say `/design` | Not rewritten; the Upgrade Note tells them |

## Files in Scope

| File | Story | Change |
|---|---|---|
| `scripts/tests/test_platform_neutral_names.py` | 1, 2, 3 | New: canvas section (1), registration section (2), reference gate (3) |
| `commands/prototype.md` | 1, 2 | Step 2 and Step 2.5 capability name (1); When to Use row and terminal constraint (2) |
| `adapters/cursor.md` | 1, 2 | `canvas-preview` row (1); directory tree line (2) |
| `adapters/claude-code.md`, `adapters/codex.md`, `adapters/openclaw.md` | 1 | `canvas-preview` row |
| `commands/design.md` → `commands/writ-design.md` | 2 | `git mv` + self-naming lines |
| `.writ/manifest.yaml`, `SKILL.md` | 2 | Entry renamed and moved; regenerate |
| `claude-code/CLAUDE.md` | 2 | Regenerate with the parity generator |
| `codex/AGENTS.md.template` | 2 | Row renamed and moved |
| `README.md`, `commands/create-spec.md`, `commands/create-spec.lean.md` (if present), `commands/create-adr.md`, `commands/research.md`, `commands/status.md`, `.writ/docs/model-tiers.md` | 2 | Reference renamed |
| `scripts/eval.sh` | 2 | Five allowlist rows |
| `scripts/tests/test_install_update_writ_design.sh` | 3 | New |
| `.writ/issues/bugs/2026-10-19-prototype-visual-preview-cursor-only.md`, `.writ/issues/bugs/2026-10-19-design-command-name-collision.md` | 3 | `## Resolution`; `spec_ref` |
| `.writ/specs/2026-10-20-platform-neutral-names/spec.md` | 3 | Upgrade Note checked against observed output |
