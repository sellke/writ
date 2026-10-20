# Story 2: Rename `/design` to `/writ-design` Across Every Reference

> **Status:** Not Started
> **Priority:** High
> **Dependencies:** Story 1

## User Story

**As a** Writ user on Claude Code, Cursor, or Codex
**I want to** reach Writ's wireframe and mockup command as `/writ-design`, with every Writ file pointing at that name
**So that** `/design` on Claude Code no longer collides with the platform's native command, and no Writ file sends me to a command that no longer exists

## Acceptance Criteria

> **AC IDs assigned through:** AC-2.5

- [ ] Given the rename commit, when `git show -M --stat` and `git show -M` run on it, then they report `commands/{design.md => writ-design.md}`; every changed line in that file is a self-naming line (frontmatter `name: writ-design`, the H1, the five invocation-table rows, and the two in-body `/writ-design` references); and `commands/design.md` does not exist `[AC-2.1]`
- [ ] Given `.writ/manifest.yaml`, when it is read, then it has a `writ-design` entry with `file: commands/writ-design.md` and the old category, purpose, and tags; no command is named `design`; no `aliases` list contains `design`; the commands list is sorted; and `bash scripts/gen-skill.sh --check` prints `pass` with `SKILL.md` showing a `` `/writ-design` `` row `[AC-2.2]`
- [ ] Given every rename-class line in technical-spec.md → ## Reference Inventory, plus any the re-run grep adds, when the story is done, then each names `/writ-design`, `writ-design`, or `writ-design.md`: `README.md`, `adapters/cursor.md`, `codex/AGENTS.md.template`, `commands/create-spec.md` Step 1.5, `commands/create-spec.lean.md` if present, `commands/create-adr.md`, `commands/research.md`, `commands/status.md`, `commands/prototype.md` (two lines), `.writ/docs/model-tiers.md`, and the five `scripts/eval.sh` allowlist rows `[AC-2.3]`
- [ ] Given `scripts/gen-claude-md.py` from `2026-10-20-claude-code-parity`, when it regenerates `claude-code/CLAUDE.md`, then the file lists `` `/writ-design` `` and no `` `/design` ``, `python3 scripts/gen-claude-md.py --check` prints `pass`, its eval check passes, and the file was not hand-edited `[AC-2.4]`
- [ ] Given the keep-class lines in the inventory (`design-system.md` paths, "roadmap/design", "artboard/design", record paths, the three dated snapshots), when the story is done, then none of them has changed; and `uv run --python 3.9 pytest`, the bash tests, and `bash scripts/eval.sh` (0 findings) pass `[AC-2.5]`

## Implementation Tasks

- [ ] 2.1 Re-run `git grep -n -e '/design' -e 'design\.md'` and compare it with technical-spec.md → ## Reference Inventory. Classify any new or moved line. Then add failing registration tests to `scripts/tests/test_platform_neutral_names.py` (`test_writ_design_file`, `test_manifest_entry`, `test_skill_catalog`, `test_eval_allowlist_rows`), citing AC IDs in docstrings, and confirm they fail `[AC-2.1, AC-2.2, AC-2.3, AC-2.5]`
- [ ] 2.2 Run `git mv commands/design.md commands/writ-design.md`, then edit only the self-naming lines listed in technical-spec.md → ## Rename → File edits `[AC-2.1]`
- [ ] 2.3 Rename the manifest entry, move it after `verify-spec`, run `bash scripts/gen-skill.sh`, and confirm `bash scripts/gen-skill.sh --check` prints `pass` `[AC-2.2]`
- [ ] 2.4 Update the rename-class references in `README.md`, `adapters/cursor.md` (directory tree, sorted), `codex/AGENTS.md.template` (row moved after `/verify-spec`), `commands/create-spec.md`, `commands/create-spec.lean.md` if it still exists, `commands/create-adr.md`, `commands/research.md`, `commands/status.md`, `commands/prototype.md`, `.writ/docs/model-tiers.md`, and the five allowlist rows in `scripts/eval.sh` `[AC-2.3]`
- [ ] 2.5 Confirm `scripts/gen-claude-md.py` exists. If it does not, stop and report blocked; do not hand-edit. Otherwise run `python3 scripts/gen-claude-md.py`, then `--check` (before regenerating it reports `missing /writ-design` and `extra /design`; after, `pass`), and confirm the `/writ-design` row `[AC-2.4]`
- [ ] 2.6 Verify the sweep: re-run the inventory grep and check that only keep-class lines remain; check `git diff --stat` shows no edits to keep-class files; commit with a `BREAKING CHANGE: /design is renamed to /writ-design` footer, then run `git show -M --stat` and `git show -M` on the commit `[AC-2.1, AC-2.3, AC-2.5]`
- [ ] 2.7 Verify the regression surface: `uv run --python 3.9 pytest`, `for t in scripts/tests/test_*.sh; do bash "$t" || echo "FAIL $t"; done`, and `bash scripts/eval.sh` outside the sandbox, with 0 findings `[AC-2.2, AC-2.4, AC-2.5]`

## Notes

- **Name only.** Do not touch the modes, flags, exit criteria, or outputs of the command. `/design` Mode A modernization is out of scope (roadmap parking lot).
- **No alias.** A `design` alias would bring the collision back. If anything asks for one, the answer is no.
- **The grep misses bare names.** `.writ/manifest.yaml` `name: design`, the command's own frontmatter and H1, and the `.writ/docs/model-tiers.md` entry-level list do not contain `/design` or `design.md`. The inventory lists them under "Rename-class references the grep misses".
- **Eval allowlist rows fail silently if missed.** `check_referenced_paths` judges a row's staleness only when `commands/<creating-command>.md` exists. A row still naming `/design` is skipped with no finding. `test_eval_allowlist_rows` and Story 3's gate are the only things that catch it.
- **Generated files.** `SKILL.md` comes from `gen-skill.sh`. `claude-code/CLAUDE.md` comes from `scripts/gen-claude-md.py` (dev-only, added by the parity spec). `codex/AGENTS.md.template` is hand-maintained today; if the parity spec has put it under a generator, regenerate it instead. No `codex/agents/*.toml` names the command, so do not run `gen-codex-agent-tomls.py` for this story.
- **Cross-spec edits.** The Phase 13 `create-spec` reduction pass and the cuts spec may have rewritten `create-spec.md` Step 1.5, `prototype.md`, or deleted the `*.lean.md` siblings. Find each line by its text, not by line number.
- **Symlinks.** `.claude/commands` and `.cursor/commands` link to `commands/`. `git mv` in `commands/` is enough. Never replace a symlink with a copy.
- **Never run `install.sh` or `update.sh` against the Writ repo.** Story 3 tests installs in temp directories.
- **Release.** `/release` Step 1.2 finds breaking changes by the `BREAKING CHANGE` commit footer, and its table proposes a major bump for one. The maintainer picks the version.

## Definition of Done

- [ ] All tasks completed
- [ ] All acceptance criteria met
- [ ] Tests passing
- [ ] Code reviewed
- [ ] Documentation updated

## Context for Agents

- **Error map rows:** [Rename sweep, Eval allowlist rows left as `/design`, Regenerate `claude-code/CLAUDE.md`, `SKILL.md`] — technical-spec.md → ## Error & Rescue Map
- **Shadow paths:** []
- **Business rules:** [Rule 5 (name-only rename), Rule 6 (`git mv`, symlinks stay), Rule 7 (reference classes), Rule 8 (regenerate generated files), Rule 9 (no alias), Rule 10 (manifest order)] — spec.md → ## Business Rules (Expanded)
- **Experience:** [State Catalog rows "User types `/design` on Claude Code after upgrade" and "on Cursor or Codex after upgrade"] — spec.md → ## Experience Design → ### State Catalog
- **Technical:** technical-spec.md → ## Rename (Story 2), ## Reference Inventory (2026-10-20)
