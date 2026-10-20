# Story 5: Repair Legacy Manifests and Remove Stale Files From Their Real Path

> **Status:** Not Started
> **Priority:** High
> **Dependencies:** Story 4

## User Story

**As a** user upgrading a project whose manifest was written by a pre-fix Writ release
**I want to** have the first fixed `update.sh` run leave my own files and my edits alone, and remove only retired Writ files, from the folder they actually live in
**So that** the fixes in Stories 3 and 4 protect me on the first update, not only from the second update on

## Acceptance Criteria

> **AC IDs assigned through:** AC-5.5

- [ ] Given a legacy manifest (no `# baselines: shipped` header) whose `# version:` resolves upstream and which records user-authored `.writ/docs/tech-stack.md`, `scripts/deploy.sh`, and `.claude/commands/my-own.md` with their local hashes, when `update.sh` runs, then the three files are byte-identical, no stale or removal line names them, and the rewritten manifest has the header and no line for them; a second update also leaves them alone `[AC-5.1]`
- [ ] Given the same kind of legacy manifest, plus an unmodified `commands/zz-retired.md` that upstream shipped at the recorded version and no longer ships, plus a customized `commands/status.md` whose recorded baseline equals its local hash (re-baselined by the old scripts), when `update.sh` runs after an upstream change to `status.md`, then `zz-retired.md` is removed with `🗑  Removed: commands/zz-retired.md`, and `status.md` is preserved byte-identical with its baseline set to the upstream content at the recorded version `[AC-5.2]`
- [ ] Given a legacy manifest whose version does not resolve (`unknown`, or a commit upstream lacks), when `update.sh` runs, then it prints one notice naming the reason, removes nothing, overwrites no file that differs from upstream, keeps the `.codex/config.toml.baseline` line on Codex, and writes a manifest with the header. With `WRIT_REPO=file://…` (a shallow clone) and a version older than the clone's tip, the version resolves after one `git fetch --unshallow`, and AC-5.1 and AC-5.2 hold. `commands/update-writ.md` Step 3 describes this legacy handling in one sentence `[AC-5.3]`
- [ ] Given a Codex project with an unmodified stale skill at `.agents/skills/zz-old/SKILL.md`, when `update.sh` runs, then the file is removed and `🗑  Removed: skills/zz-old/SKILL.md` is printed; on Claude Code and Codex, each path printed as `🗑  Removed:` is absent from disk after the run `[AC-5.4]`
- [ ] Given `scripts/tests/test_update_legacy_manifest.sh` and the pre-fix `update.sh`, when the test runs, then it fails, naming a removed user file, an overwritten customization, or a Codex skill still on disk after a Removed line; after the fix it passes, and every existing install/update bash test passes `[AC-5.5]`

## Implementation Tasks

- [ ] 5.1 Write a new `scripts/tests/test_update_legacy_manifest.sh` covering AC-5.1 through AC-5.4. Build each legacy manifest by installing with the fixed `install.sh`, deleting the `# baselines: shipped` line, rewriting `# version:` (a source commit, `unknown`, or a bogus hash), and appending the lines a pre-fix script would have written. Use `WRIT_REPO=file://$SRC` for the shallow case. Run the test against the unchanged `scripts/update.sh`, confirm it fails, and save the failing line `[AC-5.1, AC-5.2, AC-5.3, AC-5.4, AC-5.5]`
- [ ] 5.2 Add a legacy-baseline step to `scripts/update.sh`, after the clone and before the scan. When the manifest lacks the header, resolve `# version:` in `$WRIT_SRC`, running `git fetch --quiet --unshallow` once if the clone is shallow and the commit is missing. Then build the per-run baseline file (Story 3) from upstream content at that version: an upstream blob hash for each manifest path whose source exists there, the inner hash of the template at that version for the Writ blocks, and `.codex/config.toml.baseline` as recorded. Drop every other path `[AC-5.1, AC-5.2, AC-5.3]`
- [ ] 5.3 Add the unresolvable fallback. When the version cannot be resolved or the fetch fails, the per-run baseline file holds only `.codex/config.toml.baseline`, so the run behaves like the existing no-manifest path. Print one notice: `⚠️  Manifest predates shipped-only baselines and version <v> was not found upstream; files that differ from upstream are preserved this run.` Add one sentence on legacy manifests to `commands/update-writ.md` Step 3 `[AC-5.3]`
- [ ] 5.4 Fix the stale-removal block (`scripts/update.sh:1114-1129`). Resolve skills paths through `$SKILLS_DIR` (`.agents/skills` on Codex, `update.sh:86`) instead of `$PLATFORM_DIR`, and print `🗑  Removed: <path>` only when the file is gone after `rm` `[AC-5.4]`
- [ ] 5.5 Verify: run the new test and every `scripts/tests/test_install_update_*.sh` and `test_update_*.sh`, and all pass. Re-prove the pre-fix failure by copying the new test into a temp `git archive <pre-fix commit>` extract and running it there `[AC-5.1, AC-5.2, AC-5.3, AC-5.4, AC-5.5]`
- [ ] 5.6 Verify the regression surface: `uv run --python 3.9 pytest`, `for t in scripts/tests/test_*.sh; do bash "$t" || echo "FAIL $t"; done` (no `FAIL` lines), and `bash scripts/eval.sh` outside any sandbox; all pass `[AC-5.5]`

## Notes

- **Why this story exists.** Every manifest written before this spec was produced by the pre-fix scripts. It records user files (probe: `/initialize`'s `.writ/docs/tech-stack.md`) and customizations re-baselined to their local hash. Without the legacy step, the first fixed update removes the former and overwrites the latter. The maintainer's rule says "on the first or any later update".
- **Why not just never remove legacy stale files.** It is simpler, but Writ files retired in this release would then never leave existing installs. One example is `commands/design.md` (`2026-10-20-platform-neutral-names` relies on stale removal). The version lookup removes them precisely and falls back to keeping everything when it cannot be sure.
- **Shallow clones.** `update.sh` clones with `--depth 1`, and git ignores `--depth` for a plain local path (`warning: --depth is ignored in local clones`). Only `file://` or a network URL is shallow, so the shallow case needs `WRIT_REPO=file://…`. Grounding: the Writ pack is 4.9 MiB, and `--unshallow` took under a second locally.
- **Source path mapping.**

  | Manifest path | Source path |
  |---|---|
  | `commands/x` | `commands/x` |
  | `agents/x` | `$AGENTS_SRC/x` |
  | `skills/n/SKILL.md` | `skills/n/SKILL.md` |
  | `scripts/x`, `.writ/docs/x` | same path |
  | `rules/writ.mdc` | `cursor/writ.mdc` |
  | `system-instructions.md` | `system-instructions.md` |
  | `CLAUDE.md.writ-block` | `claude-code/CLAUDE.md` |
  | `AGENTS.md.writ-block` | `codex/AGENTS.md.template` |
- **Dry runs** build the same per-run file in a temp path and never write the manifest. The fetch only touches the temp clone.
- **Removal message.** Detection already requires the local file to exist (`update.sh:838`). After the path fix, a "Removed" line without a removal can only come from a failed `rm`. Do not count such a path in the summary.
- **Out of scope:** `unlink.sh` writes header-less manifests. This story reads them as legacy and does not change `unlink.sh`. Stale-skill sidecars stay behind, and only `SKILL.md` is removed, as today.
- **Never run `install.sh` or `update.sh` against the Writ repo.** It is symlinked into `.claude/` and `.cursor/`. Run everything in temp directories. The test does `git init`, so run it outside any sandbox.
- **Citations.** Name this spec (`2026-10-20-ci-and-update-integrity`) in the comment that carries `AC-5.n` tokens.

## Definition of Done

- [ ] All tasks completed
- [ ] All acceptance criteria met
- [ ] Tests passing
- [ ] Code reviewed
- [ ] Documentation updated

## Context for Agents

- **Error map rows:** [Legacy manifest (version found), Legacy manifest (version not found or fetch fails), Stale removal (Codex skills path), Stale removal (rm fails)] — technical-spec.md → ## Error & Rescue Map
- **Shadow paths:** [Legacy manifest upgrade] — technical-spec.md → ## Shadow Paths
- **Business rules:** [Rule 5 (removal path and message), Rule 9 (legacy manifests), Rule 13 (temp dirs only)] — spec.md → ## Business Rules (Expanded)
- **Experience:** [State Catalog rows "Update from a legacy manifest, version found", "Update from a legacy manifest, version not found", "Codex update"] — spec.md → ## Experience Design → ### State Catalog
- **Technical:** technical-spec.md → ## Story 5 Design: Legacy manifests and removal paths
