# Claude Code Parity

> **Status:** Not Started
> **Created:** 2026-10-20
> **Owner:** @AdamSellke
> **Dependencies:** [2026-10-20-harness-cuts]
> **Phase:** 13 — Subtract and Repair ([roadmap](../../product/roadmap.md), [ADR-030](../../decision-records/adr-030-contract-verifier-boundary-front-door.md))
> **Origin:** Phase 13 decomposition pre-pass (`/implement-phase 13`, 2026-10-20). Finding F6 and defects 1 and 4 in `.writ/research/2026-10-19-writ-vs-pstack-research.md`.

## Specification Contract

**Deliverable:** Claude Code installs carry the same root contract as Cursor installs, and the Writ block in CLAUDE.md is generated from the command registry so it cannot go stale.

**Must Include** (maintainer chose "install file + @import"):

1. `install.sh --platform claude` copies `system-instructions.md` to `.claude/system-instructions.md`. That makes the `../system-instructions.md` links in installed commands resolve. The Writ block that `merge_claude_md` writes into the project's `CLAUDE.md` contains an import line `@.claude/system-instructions.md`, so the Prime Directive loads every session. `update.sh` keeps `.claude/system-instructions.md` current the same way it keeps the Cursor copy current, and keeps the import line in the block. `uninstall.sh` removes the file if it removes other platform files (check its current behavior and match it).
2. A generator (Python 3.9 stdlib, follows the agent CLI contract in `.writ/docs/agent-cli-contract.md`, dev-only like `gen-skill.sh` — exclude it from shipping if it lives in `scripts/`) builds `claude-code/CLAUDE.md` from `.writ/manifest.yaml`: the commands table (name, file, purpose), the agents list, and the pipeline line, plus the import line. A `--check` mode exits 1 when the committed template differs from what the manifest produces. An `eval.sh` check (running in CI) fails when the template is stale or a manifest command is missing from it, proven by a mutation test.
3. `adapters/claude-code.md`: remove the `/implement-story --all` text and the "implement-story --all: Agent Teams (Experimental)" section, and every claim that worktree changes "merge back automatically"; worktree guidance agrees with `skills/subagent-worktree-integration`. *(Amended 2026-10-20:)* replace the nonexistent `SubagentCompleted` hook example with a documented Claude Code hook event, drop the undocumented `$WORKTREE` variable, and name all seven Claude-native agents, `writ-evaluator` included.
4. *(Added 2026-10-20.)* `uninstall.sh --platform claude` removes only the Writ block (the start-marker line through the end-marker line) from `CLAUDE.md` and leaves every other byte. A `CLAUDE.md` that held only the Writ block is removed only if it is then empty. The function follows the shape of Codex's `remove_agents_md_block` for `AGENTS.md`. `commands/uninstall-writ.md` stops saying `rm CLAUDE.md`.
5. *(Added 2026-10-20.)* `commands/reinstall-writ.md` Step 4 and the adapter's manual install step stop overwriting the user's `CLAUDE.md` with `cp claude-code/CLAUDE.md ./CLAUDE.md`. They merge between the markers, the same path `install.sh` uses.

**Hardest Constraint:** `CLAUDE.md` is user-owned. `merge_claude_md` must keep every byte outside the Writ markers unchanged on install and update, including when the block grows the import line. *(Amended 2026-10-20:)* the same holds for uninstall and for `/reinstall-writ`.

**🎯 Experience Design:**
- A developer runs `install.sh --platform claude` in a project. `.claude/system-instructions.md` exists, and `CLAUDE.md`'s Writ block lists every command and imports the system instructions.
- A maintainer adds a command to the manifest and forgets the template. `eval.sh` (and CI) fails, naming the missing command and the regenerate command.

**Success Criteria:**
- A temp-project Claude install has `.claude/system-instructions.md` containing the Prime Directive heading, and the CLAUDE.md Writ block contains the import line.
- User content outside the markers is byte-identical before and after install and update.
- The generator `--check` passes on the committed template and fails when a manifest command is removed from the template.
- `adapters/claude-code.md` contains no `--all` and no "Agent Teams" section.
- *(Added 2026-10-20.)* After `uninstall.sh --platform claude`, the bytes of `CLAUDE.md` outside the Writ block are unchanged, and a `CLAUDE.md` that held only the block is deleted. Proven by a test that fails on today's `uninstall.sh`.
- *(Added 2026-10-20.)* `commands/uninstall-writ.md` contains no `rm CLAUDE.md`. `commands/reinstall-writ.md` and `adapters/claude-code.md` contain no copy of `claude-code/CLAUDE.md` onto `./CLAUDE.md`. Proven by a grep test that fails on today's files.
- *(Added 2026-10-20.)* `adapters/claude-code.md` contains no `SubagentCompleted` and no `$WORKTREE`, and names all seven files in `claude-code/agents/`. The generated template lists `writ-evaluator.md` (Story 1 already requires it). Proven by a grep test that fails on today's adapter.
- Full `eval.sh` reports 0 findings. pytest and the bash tests pass.

**Scope Boundaries:**
- Included: the five Must Include items, their tests, and the Claude rows of the lifecycle command docs (`/update-writ`, `/reinstall-writ`, `/uninstall-writ`) that describe what the scripts install, remove, and merge.
- Excluded: Cursor and Codex install changes (Codex's `remove_agents_md_block` stays as it is); making `claude-code/agents/*.md` prompt bodies match `agents/*.md` (filed separately as `.writ/issues/improvements/2026-10-20-claude-agent-prompt-parity.md`); the `writ-story-gen` worktree base (tracked in that same issue); the general adapter coverage check (Phase 14).

**Dependency:** `2026-10-20-harness-cuts` edits `install.sh` and `update.sh` first (lean skip logic, the shippable list). Tasks here name functions and blocks, never fixed line numbers.

### Contract Amendment — 2026-10-20 (maintainer-approved)

The maintainer widened the contract with grounding concerns 1–4 from the first authoring pass. The items above carry the amended text, marked with the date.

| # | Concern found while grounding | Amendment | Story |
|---|---|---|---|
| 1 | `uninstall.sh --platform claude` puts `CLAUDE.md` in `EXTRA_FILES` and deletes the whole file. `commands/uninstall-writ.md` Step 3 says `rm CLAUDE.md`. | Remove only the Writ block; delete the file only if nothing is left. Must Include 4. | 4 |
| 2 | `commands/reinstall-writ.md` Step 4 and the adapter's manual Step 1 run `cp .../claude-code/CLAUDE.md ./CLAUDE.md`, with no markers. | Merge between the markers as `install.sh` does. Must Include 5. | 4 (reinstall), 3 (adapter) |
| 3 | The adapter's hook example uses `SubagentCompleted`, which is not a Claude Code hook event, and `$WORKTREE`, which the hooks docs do not define. | Use `SubagentStop`, read `cwd` from the hook's input JSON, cite the hooks docs. Must Include 3. | 3 |
| 4 | The adapter says "six Claude-native agents… do not infer a seventh". `claude-code/agents/` has seven; `writ-evaluator` is missing from its tables and tree. | Name all seven. The generated template already lists `writ-evaluator.md` (AC-1.1). Must Include 3. | 3 |

Each change is proven by a test that fails before the fix: uninstall byte preservation (Story 4), a grep of the two lifecycle command docs (Story 4), and a grep of the adapter (Story 3). Grounding concern 5 (the `writ-story-gen` worktree base) stays out of scope.

## Grounding Notes

Facts read from the tree on 2026-10-20. They set the numbers the tests use.

- `claude-code/CLAUDE.md` is 59 lines. It lists 25 of the 32 commands in `.writ/manifest.yaml`. Missing: `implement-phase`, `knowledge`, `new-skill`, `reinstall-writ`, `revert`, `uninstall-writ`, `update-writ`. It lists 6 of the 7 files in `claude-code/agents/`; `writ-evaluator.md`, the default Gate 3 agent, is missing. It calls `/retro` "Git-based retrospective", which v0.41.0 replaced.
- 37 lines in 36 shipped command files link `../system-instructions.md`; 55 lines in `commands/` mention the file. The research doc's "49" counted differently. Either way, every one of those links is broken on a Claude Code install today, because `install.sh` prints `(skipped — no system-instructions for Claude Code)` in its platform step block.
- On Cursor, `install.sh` copies `system-instructions.md` unconditionally ("always updated"). `update.sh` runs a three-way check (`SYSINST_ACTION`) and records the manifest key `system-instructions.md`. `uninstall.sh` lists `$PLATFORM_DIR/system-instructions.md` in `EXTRA_FILES`. Claude Code gets the same three behaviors.
- `merge_claude_md` exists twice, once in each script's `writ-merge-bundled` region (`install.sh`, `update.sh`). Both write the block from the template's bytes and touch nothing outside the markers, except that an append adds one `\n` when the user's file has no final newline. `scripts/tests/test_merge_claude_md.sh` and `test_update_claude_md.sh` extract and test each copy.
- `gen-skill.sh` and `gen-codex-agent-tomls.py` both ship (they have rows in the agent CLI contract's Classification table). The pattern this spec borrows from them is "generator plus `--check`", not their ship status. The new generator is dev-only, like `pipeline-baseline.py`.
- `uninstall.sh` handles Codex's `AGENTS.md` with `remove_agents_md_block`, bundled between `writ-remove-agents-md-bundled` markers and tested by `scripts/tests/test_remove_agents_md_block.sh`. It validates the markers (malformed → return 13, file untouched), deletes the file when nothing but whitespace remains, and otherwise rewrites the rest through `awk`. That rewrite trims blank lines next to the block, joins the two sides with one blank line, and adds a final newline, so it does not keep every byte.
- Claude Code hooks docs (`https://code.claude.com/docs/en/hooks`, fetched 2026-10-20) list 33 events. `SubagentCompleted` is not one; `SubagentStop` fires when a subagent finishes. Its matcher is the agent type, which for a custom subagent is the frontmatter `name`. Exit 2 keeps the subagent running and hands it the stderr text. Hook input carries `cwd`; no `$WORKTREE` variable is documented, and the docs do not say whether `cwd` is a worktree-isolated subagent's worktree.
- Claude Code memory docs (`https://code.claude.com/docs/en/memory`, § Import additional files; `docs.anthropic.com/en/docs/claude-code/memory` redirects there): `@path` imports expand at launch, relative paths resolve against the file that holds the import, imports inside code spans and fenced blocks are not expanded, and an import that resolves outside the working directory needs a one-time approval. See `sub-specs/technical-spec.md` → Import Line.

### Decisions made while grounding

These fill gaps the contract leaves open. None changes its scope.

- **D1 — Agents list source.** The generator lists the agents from the frontmatter (`name`, `description`) of `claude-code/agents/*.md`, not from the manifest's `agents:` list. The manifest names platform-neutral agents (`coding-agent`, `agents/coding-agent.md`). A Claude Code install has `.claude/agents/writ-coder.md` instead, because `install.sh` sets `AGENTS_SRC="claude-code/agents"`. Listing manifest names would print files a Claude install does not have. The commands table and the pipeline check still come from the manifest.
- **D2 — Pipeline line.** The generator holds the pipeline line as a constant. Every `/name` in it must be a manifest command, or the generator fails.
- **D3 — A preserved block without the import line.** When a user has edited their Writ block, install and update preserve it, as they do today, so the import line cannot be added. Both scripts then print a warning that names the line and `--force`. They never edit the block.
- **D4 — Generator name and ship status.** `scripts/gen-claude-md.py`. It joins the dev-only arm of `is_shippable_script`, which stays byte-identical in `install.sh`, `update.sh`, and `unlink.sh`.
- **D5 — Uninstall keeps bytes exactly; it does not copy Codex's trimming.** The amendment says to keep every other byte and to match Codex. Those conflict on one point: Codex trims blank lines next to the block and normalizes the final newline. `remove_claude_md_block` takes Codex's structure (bundled region, marker validation, return 13, notes, delete when empty) but writes `head -n $((start-1))` plus `tail -n +$((end+1))`, so the remaining bytes are untouched. "Empty" means zero bytes left. A file left with only whitespace is kept.
- **D6 — Hook example.** `SubagentStop` with matcher `^writ-coder$`. The command reads `cwd` from the hook's input JSON and exits 2 with a message when checks fail. The adapter says the docs do not define `cwd` for worktree-isolated subagents, so the gate is re-run in the orchestrator checkout after reconciliation (worktree skill step 4).

## 🎯 Experience Design

### Who uses it

- **Developers** installing or updating Writ in a Claude Code project. They need the Prime Directive in every session and a `CLAUDE.md` they still own.
- **The maintainer**, adding or renaming commands in the Writ source repo. They need CI to fail when the Claude template falls behind the manifest.

### State Catalog

| State | What the person sees |
|---|---|
| Fresh install, no `CLAUDE.md` | `CLAUDE.md` created with the Writ block (import line, 32 command rows). `.claude/system-instructions.md` written. Summary: `CLAUDE.md: Writ block created`. |
| Install into a project with a hand-written `CLAUDE.md` | Their text stays first, byte for byte. The block is appended below it. |
| Install dry run | `System:  system-instructions.md → always updated` and the CLAUDE.md plan. Nothing written. |
| Update from a pre-parity install | `✨ New:       system-instructions.md`. The block is replaced (it matches its baseline), so it now holds the import line. |
| Update, local `system-instructions.md` unmodified | `🔄 Update:    system-instructions.md` when upstream changed. |
| Update, local `system-instructions.md` modified | `⚡ Preserved: system-instructions.md (local modifications)`, listed with the other preserved files. `--force` overwrites it. |
| Update, Writ block modified and missing the import line | The existing `⚡ Preserved` line, then a `⚠️` line naming `@.claude/system-instructions.md` and `--force`. `CLAUDE.md` is unchanged. |
| Uninstall | Dry run lists `.claude/system-instructions.md` and `CLAUDE.md Writ block`. The real run removes the file with the other platform files and removes the block from `CLAUDE.md`: `🗑  Removed: CLAUDE.md Writ block`. Every byte outside the block stays. |
| Uninstall, `CLAUDE.md` holds only the Writ block | The file is deleted: `🗑  Removed: CLAUDE.md (empty after Writ block removal)`. |
| Uninstall, `CLAUDE.md` has no markers | Untouched: `✓ CLAUDE.md (no Writ block present)`. |
| Uninstall, malformed markers | `❌` line naming the markers, `CLAUDE.md` untouched, uninstall stops with exit 13 (as Codex does for `AGENTS.md`). |
| `/reinstall-writ` on Claude Code | Step 4 replaces only the Writ block (or appends it); the user's text stays. |
| Maintainer adds a manifest command, forgets to regenerate | `eval.sh` FAIL: one finding naming `/<name>` and `python3 scripts/gen-claude-md.py`. |
| Maintainer hand-edits `claude-code/CLAUDE.md` | `eval.sh` FAIL: `stale claude-code/CLAUDE.md`, same remedy. |
| Maintainer runs the generator | Line 1 `pass`, summary last, template rewritten atomically. |

### Interaction Patterns

- Install and update messages keep their existing glyphs and wording (`✨ New`, `🔄 Update`, `⚡ Preserved`). The new warning uses `⚠️` like the stale-file warning.
- Every eval finding for the template names the file, the command or reason, and the one remedy command.

## 📋 Business Rules

1. **User-owned bytes.** For any `CLAUDE.md`, the bytes before the `<!-- writ:start -->` line and after the `<!-- writ:end -->` line are identical before and after install, update, `--force`, uninstall, and `/reinstall-writ`. The one allowed change: when install or update appends a block to a file with no final newline, it adds a single `\n` before the start marker. This is today's behavior; the tests pin it.
2. **The block comes only from the template.** `merge_claude_md` writes the template's bytes and never inserts the import line itself. The import line reaches a project only through `claude-code/CLAUDE.md`.
3. **Import line.** Exactly the line `@.claude/system-instructions.md`, alone on its line, outside any backtick span or fenced block. Claude Code skips imports inside code.
4. **System instructions copy.** `.claude/system-instructions.md` is a byte copy of the source `system-instructions.md`. Its manifest key is `system-instructions.md`, the same key Cursor uses, relative to the platform dir.
5. **Update decision.** Mirrors Cursor's `SYSINST_ACTION`: no local file → new; local equals upstream → unchanged; `--force`, no baseline, or local equals baseline → update; otherwise preserved.
6. **Uninstall.** Removes `.claude/system-instructions.md` the way it removes `.cursor/system-instructions.md` (the `EXTRA_FILES` list). `CLAUDE.md` leaves that list.
7. **Generator is dev-only.** `is_shippable_script` rejects `gen-claude-md.py` in all three lifecycle scripts, whose bodies stay byte-identical. The Classification note in the agent CLI contract doc names it.
8. **Generator output shape.** Check shape from the agent CLI contract: line 1 `pass`, `fail`, or `unverifiable`; `reason:` lines; a `gen-claude-md:` summary last. Exit 0 for pass or unverifiable, 1 for fail, 2 for a usage error.
9. **Deterministic template.** Same inputs, same bytes. LF line endings, exactly one final newline. This keeps a fresh block's inner hash equal to the template hash, so the next update reports the block unchanged.
10. **Command rows.** One row per manifest command, in manifest order. File column `.claude/commands/<name>.md`. Purpose is the manifest `purpose`, with `|` escaped as `\|`.
11. **No accidental imports.** A purpose or agent description with `@` outside a backtick span fails generation. Claude Code would treat it as an import.
12. **CI coverage.** The eval check is in `CHECKS`, so `bash scripts/eval.sh` and the CI workflow run it. This spec does not edit `.github/workflows/eval.yml`.
13. **Adapter claims.** `adapters/claude-code.md` names no `--all` flag, no agent-teams workflow, and no automatic merge-back. Its worktree facts match the Claude Code worktree docs and the worktree skill. Its hook examples use documented events and inputs only. Its agent tables and tree name every file in `claude-code/agents/`.
14. **Test isolation.** No test or story runs `install.sh`, `update.sh`, or `uninstall.sh` against the Writ repo. They run in temp directories against a committed temp copy of the tree.
15. **Uninstall removes only the block.** `remove_claude_md_block` deletes the start-marker line through the end-marker line and keeps every other byte. It deletes `CLAUDE.md` only when zero bytes remain. No markers → untouched. Malformed markers → return 13, untouched (D5).
16. **No copy over `CLAUDE.md`.** `/reinstall-writ` and the adapter's manual install never copy the template onto `./CLAUDE.md`. They create the file with the block, append the block, or replace only the lines between the markers, as `merge_claude_md` does. `install.sh --platform claude --force` is the scripted path.

## Detailed Requirements

### Story 1: Generate the CLAUDE.md template from the manifest

- New `scripts/gen-claude-md.py` (stdlib, Python 3.9). Write mode by default, `--check`, `--help`. Reads `.writ/manifest.yaml` and `claude-code/agents/*.md` under the repo root it resolves from its own path.
- Regenerate and commit `claude-code/CLAUDE.md`: header, import line, 32 command rows, 7 agents, pipeline, principles.
- Add `gen-claude-md.py` to the dev-only arm of `is_shippable_script` in `install.sh`, `update.sh`, `unlink.sh`. Name it in the agent CLI contract doc's Classification note, in `test_agent_cli_contract_doc.py`'s `DEV_ONLY`, and in `commands/update-writ.md` Step 3's dev-only list.
- New eval check `claude-md` (`check_claude_md`), modeled on `check_codex_tomls`.
- Tests: `scripts/tests/test_gen_claude_md.py`, `scripts/tests/test_eval_claude_md.sh` (mutation), `scripts/tests/test_gen_claude_md_not_shipped.sh`.

### Story 2: Install the system instructions and import line on Claude Code

- `install.sh`: the Claude branch of the platform step block copies `system-instructions.md` into `.claude/`. The inventory, dry-run, `write_copy_manifest`, and scoped-commit blocks gain the file.
- `update.sh`: the `SYSINST_ACTION` scan and apply run for `claude` as well as `cursor`. `write_copy_manifest` and the scoped commit gain the file.
- Both `merge_claude_md` copies: the preserved branch warns when the inner block has no import line.
- `uninstall.sh`: the Claude branch of the `EXTRA_FILES` block gains the file.
- `commands/update-writ.md`, `commands/reinstall-writ.md`, `commands/uninstall-writ.md`: the Claude rows name `.claude/system-instructions.md`.
- Tests: new `scripts/tests/test_install_update_claude_parity.sh`; new cases in `test_merge_claude_md.sh` and `test_update_claude_md.sh`.

### Story 3: Correct the Claude Code adapter

- Remove the `/implement-story --all` paragraph, the `### implement-story --all: Agent Teams (Experimental)` section, the "agent teams" mention in the intro, and Gotcha 2.
- Rewrite the worktree steps, the `create-spec` example comments, and Gotcha 1 to match the worktree docs and `skills/subagent-worktree-integration/SKILL.md`.
- Installation section: add the `system-instructions.md` copy, the tree entry, and one sentence on the import. Manual Step 1 appends the template between markers instead of copying it over `CLAUDE.md`.
- *(Amended 2026-10-20.)* Replace the `SubagentCompleted` example with a `SubagentStop` example that reads `cwd` from the hook input (D6), and fix the `/goal` section's pointer to it. Name all seven agents in the Model Selection text and tier table, the Permission Modes table, and the Final Structure tree.
- Test: new `scripts/tests/test_claude_code_adapter_claims.py`.

### Story 4: Keep CLAUDE.md user-owned on uninstall and reinstall

*Added 2026-10-20 by the contract amendment.*

- `uninstall.sh`: new `remove_claude_md_block` in a `writ-remove-claude-md-bundled` region (D5). `CLAUDE.md` leaves `EXTRA_FILES`; the inventory, dry run, removal, and count handle the block the way the Codex branch handles `AGENTS.md`.
- `commands/uninstall-writ.md` Step 3: remove only the marker-bounded block; delete the file only if nothing is left. Its "Do NOT remove" list names content outside the markers.
- `commands/reinstall-writ.md`: platform table, Step 3 (no `CLAUDE.md` removal), Step 4 (merge between markers; `install.sh --platform claude --force`), and the "Do NOT remove" list.
- Tests: new `scripts/tests/test_remove_claude_md_block.sh`, `scripts/tests/test_uninstall_claude_md.sh`, `scripts/tests/test_lifecycle_commands_claude_md.py`.

## Implementation Approach

- **Template first, then install.** Story 1 makes the committed template carry the import line. Story 2's install tests read that template from a temp source copy. Between the two stories the template imports a file the scripts do not yet install. Both land in this spec before any release.
- **No shared helper across scripts.** The generator stands alone. The import-line check in the preserved branch is a small helper inside each `writ-merge-bundled` region, so the bundle tests load it.
- **No YAML dependency.** The generator parses only the `commands:` list of the manifest with a line reader. The manifest's shape is regular, and `gen-codex-agent-tomls.py` already avoids a YAML library.
- **Ordering:** Story 1 and Story 3 are independent. Story 2 depends on Story 1 (the template, and both edit `install.sh` and `update.sh`). Story 4 depends on Story 2 (both edit the `EXTRA_FILES` block of `uninstall.sh` and the Claude rows of `commands/uninstall-writ.md` and `commands/reinstall-writ.md`). Story 3 and Story 4 share no file.
- **Verification:** `uv run --python 3.9 pytest`, `uv run pytest`, the bash test loop, and `bash scripts/eval.sh` outside the sandbox. Install and update only in temp directories.
