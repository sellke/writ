# Technical Spec: Claude Code Parity

> Spec: [`../spec.md`](../spec.md)
> Stories: [1](../user-stories/story-1-generate-claude-md-template.md), [2](../user-stories/story-2-install-system-instructions-on-claude.md), [3](../user-stories/story-3-correct-claude-code-adapter.md), [4](../user-stories/story-4-claude-md-ownership-on-uninstall-and-reinstall.md)
> Amended 2026-10-20 (maintainer-approved): Story 4, the uninstall and reinstall sections, and the hook and agent rows of Adapter Corrections.

## Files in Scope

| File | Story | Change |
|---|---|---|
| `scripts/gen-claude-md.py` | 1 | New generator, dev-only |
| `claude-code/CLAUDE.md` | 1 | Regenerated |
| `scripts/eval.sh` | 1 | `check_claude_md`; `claude-md` added to `CHECKS` |
| `scripts/install.sh`, `scripts/update.sh`, `scripts/unlink.sh` | 1 | `gen-claude-md.py` added to the dev-only arm of `is_shippable_script` |
| `.writ/docs/agent-cli-contract.md` | 1 | The note under the Classification table names the generator |
| `commands/update-writ.md` | 1, 2 | Step 3 dev-only list (1); Claude row of the platform table and the platform-files bullet (2) |
| `scripts/tests/test_agent_cli_contract_doc.py` | 1 | `DEV_ONLY` gains `gen-claude-md.py` |
| `scripts/tests/test_gen_claude_md.py` | 1 | New |
| `scripts/tests/test_eval_claude_md.sh` | 1 | New, mutation test for the eval check |
| `scripts/tests/test_gen_claude_md_not_shipped.sh` | 1 | New |
| `scripts/install.sh` | 2 | Inventory, dry run, platform step block, `write_copy_manifest`, scoped commit, `merge_claude_md` preserved branch |
| `scripts/update.sh` | 2 | `SYSINST_ACTION` scan and apply for `claude`, actionable count, `write_copy_manifest`, scoped commit, `merge_claude_md` preserved branch |
| `scripts/uninstall.sh` | 2 | Claude branch of the `EXTRA_FILES` block |
| `commands/reinstall-writ.md`, `commands/uninstall-writ.md` | 2 | Claude rows |
| `scripts/tests/test_install_update_claude_parity.sh` | 2 | New |
| `scripts/tests/test_merge_claude_md.sh`, `scripts/tests/test_update_claude_md.sh` | 2 | New cases |
| `adapters/claude-code.md` | 3 | Claims, Installation section, hook example, the eight agents |
| `scripts/tests/test_claude_code_adapter_claims.py` | 3 | New |
| `scripts/uninstall.sh` | 4 | New `remove_claude_md_block` bundle; `CLAUDE.md` leaves `EXTRA_FILES`; inventory, dry run, removal |
| `commands/uninstall-writ.md`, `commands/reinstall-writ.md` | 4 | Claude bullets: block removal, merge between markers, "Do NOT remove" lists |
| `scripts/tests/test_remove_claude_md_block.sh` | 4 | New, bundle test |
| `scripts/tests/test_uninstall_claude_md.sh` | 4 | New, temp-project install → uninstall round trip |
| `scripts/tests/test_lifecycle_commands_claude_md.py` | 4 | New, grep test of the two command docs |

`2026-10-20-harness-cuts` edits `install.sh`, `update.sh`, and `unlink.sh` before this spec runs. Find each edit point by function or block name, not by line.

## Import Line

Source: Claude Code memory docs, `https://code.claude.com/docs/en/memory`, § "Import additional files" (fetched 2026-10-20; `https://docs.anthropic.com/en/docs/claude-code/memory` returns 301 to it). The section says:

- `CLAUDE.md` may import files with `@path/to/import`. Imported files expand and load at launch with the file that imports them.
- "Relative paths resolve relative to the file containing the import". Project-root `CLAUDE.md` plus `@.claude/system-instructions.md` therefore loads `<project>/.claude/system-instructions.md`, wherever the session starts.
- Imports nest up to four hops. `system-instructions.md` contains no `@` token today, so it imports nothing.
- Import parsing skips Markdown code spans and fenced code blocks. The import line must not sit in backticks or a fence. The command table's backticked paths are therefore not imports.
- An import that resolves outside the working directory is "external". Claude Code asks once per project to approve external imports, and a declined approval disables them. Inference (not stated in the docs, verify in UAT): a session started in a subdirectory loads the parent `CLAUDE.md`, whose import then resolves outside that working directory and triggers the approval.
- Block-level HTML comments are stripped before the content enters context, so the `<!-- writ:start -->` and `<!-- writ:end -->` markers cost nothing.

Related, from `https://code.claude.com/docs/en/sub-agents` § What loads at startup: custom subagents load project `CLAUDE.md` files by default; built-in Explore and Plan, and agents with `omitClaudeMd: true`, do not. The docs do not say whether imports expand inside subagents. No file in `claude-code/agents/` sets `omitClaudeMd`.

`system-instructions.md` starts with a Cursor rule frontmatter block (`alwaysApply: true`). Claude Code imports it as plain text. That is harmless and needs no change.

## Generator (Story 1)

File: `scripts/gen-claude-md.py`.

### CLI

```
python3 scripts/gen-claude-md.py           # write claude-code/CLAUDE.md
python3 scripts/gen-claude-md.py --check   # compare with the committed file, write nothing
python3 scripts/gen-claude-md.py --help
```

`ROOT` is the parent of the script's own folder (`Path(__file__).resolve().parents[1]`), the way `gen-codex-agent-tomls.py` resolves it. Tests copy the script into a temp root and run it there. argparse handles usage errors: exit 2, usage on stderr, empty stdout.

### Inputs

- `ROOT/.writ/manifest.yaml`, `commands:` list only: `name`, `file`, `purpose` per entry. Other keys are ignored.
- `ROOT/claude-code/agents/*.md`, sorted by file name: the `name:` and `description:` lines of each file's `---` frontmatter.

### Manifest reader (no YAML library)

- Find the line `commands:` at column 0. The section ends at the next column-0 line that is not blank and not a `#` comment.
- An entry starts at `  - name: <value>`. The entry's keys are the `    <key>: <value>` lines that follow.
- Values: trim spaces. A double-quoted value drops its quotes and unescapes `\"` and `\\`. A single-quoted value drops its quotes and turns `''` into `'`. A bare value drops a trailing ` #...` comment.
- Validation, each failure a `reason: manifest <detail>` line: no `commands:` section; an entry missing `name`, `file`, or `purpose`; a name outside `[a-z0-9][a-z0-9-]*`; a `file` other than `commands/<name>.md`; a duplicate name.

### Output layout

The generator writes these bytes, LF only, one final newline. `<rows>` and `<agents>` expand as described below.

````markdown
# Writ

You are **Writ** — a methodical AI development partner. You organize all work in `.writ/` folders.

Writ's root contract (Prime Directive, interaction rules, model tiers) loads from this import:

@.claude/system-instructions.md

## Commands

Run Writ commands by reading the command file and following its workflow:

| Command | File | Purpose |
|---------|------|---------|
<rows>

## Agents

Writ uses Claude Code's native subagent system. Agents are defined in `.claude/agents/`:

<agents>

## Pipeline

```
/plan-product → /create-spec → /implement-spec → /verify-spec → /release
```

`/implement-phase` runs `/implement-spec` once per spec in a roadmap phase.

## Principles

- **Contract-first**: Establish agreement before creating files
- **TDD**: Tests first, then implementation
- **Challenge assumptions**: Push back on bad ideas with evidence
- **Commit incrementally**: Small commits, not big bangs
````

- `<rows>`: one line per manifest command, manifest order: ``| `/<name>` | `.claude/commands/<name>.md` | <purpose> |``. `|` inside the purpose becomes `\|`.
- `<agents>`: one line per agent file: ``- `<file name>` — <description>``, with the same escaping.
- The pipeline constant names `plan-product`, `create-spec`, `implement-spec`, `verify-spec`, `release`, and the follow-on sentence names `implement-phase`. Each must be a manifest command, or `reason: pipeline <name>`.
- Import guard: remove every backtick span from a purpose or description. If an `@` remains, `reason: import-token <name>`.
- The rendered file must not contain `ralph` in any case (`check_ralph_retirement` scans it).

### Output shape and reason codes

| Mode | Condition | stdout line 1 | `reason:` lines | Exit |
|---|---|---|---|---|
| write | rendered and written | `pass` | none | 0 |
| `--check` | committed bytes equal rendered bytes | `pass` | none | 0 |
| `--check` | row set differs | `fail` | `missing <name>` per manifest command with no row; `extra <name>` per row with no manifest command | 1 |
| `--check` | rows match, bytes differ | `fail` | `stale claude-code/CLAUDE.md` (once) | 1 |
| `--check` | no committed template | `fail` | `absent claude-code/CLAUDE.md` | 1 |
| any | manifest invalid, import token, pipeline name, agent frontmatter missing (`agent <file>`) | `fail` | the named reason | 1 |
| write | write failed | `fail` | `write <error>` | 1 |
| any | manifest or `claude-code/agents/` missing or unreadable | `unverifiable` | `manifest missing: .writ/manifest.yaml` or `agents missing: claude-code/agents` | 0 |
| any | bad flag | (empty) | usage on stderr | 2 |

The last stdout line is `gen-claude-md: <verdict> (<detail>)`, for example `gen-claude-md: pass (32 commands, 8 agents)` or `gen-claude-md: fail (1 missing, 0 extra)`. `--check` parses committed rows with ``^\| `/([a-z0-9-]+)` \|``. A row-set difference suppresses the `stale` line so one removed row yields exactly one reason.

Write mode writes a temp file in `claude-code/` and `os.replace`s it over `CLAUDE.md`. It writes nothing when any `fail` reason exists.

## Eval Check (Story 1)

Check name: `claude-md`.

`check_claude_md` follows `check_codex_tomls`:

1. Helper missing → one finding on `scripts/gen-claude-md.py`, remedy "Restore scripts/gen-claude-md.py".
2. Run `python3 "$PROJECT_ROOT/scripts/gen-claude-md.py" --check`. An exit other than 0 or 1 → one finding quoting the summary line.
3. Line 1 `pass` → no finding. Line 1 `unverifiable` → one finding carrying the reason (CI must not pass on a missing manifest).
4. Each `reason: missing <name>` → finding on `claude-code/CLAUDE.md`: `manifest command /<name> is missing from the Claude Code template.` Every other reason → a finding quoting it. Remedy on all: `Run python3 scripts/gen-claude-md.py and commit claude-code/CLAUDE.md.`
5. The summary line → `add_note`.
6. Exit 1 with no reason line → one finding.

Add `claude-md` to `CHECKS` after `codex-tomls`. CI's `bash scripts/eval.sh` step then runs it.

## Install, Update, Uninstall (Story 2)

### `install.sh`

| Block | Change |
|---|---|
| Inventory (`📖` lines) | The Claude branch also prints `📖 System:    1 (system-instructions.md)`. |
| Dry run, platform files | The Claude branch prints `  System:  system-instructions.md → always updated` before `merge_claude_md preview`. |
| Platform step block | The Claude branch replaces the `(skipped — no system-instructions for Claude Code)` step with `System instructions...` and `cp "$WRIT_SRC/system-instructions.md" "$PLATFORM_DIR/"`. `STEP_TOTAL` is unchanged. |
| `write_copy_manifest` | The `rules/writ.mdc` + `system-instructions.md` hashing loop runs for Cursor; Claude hashes `$PLATFORM_DIR/system-instructions.md` under the key `system-instructions.md`. |
| Scoped git commit | The Claude branch adds `"$PLATFORM_DIR/system-instructions.md"`. |
| `merge_claude_md` preserved branch | See "Preserved-block warning". |

### `update.sh`

| Block | Change |
|---|---|
| Scan, platform-specific files | The `SYSINST_ACTION` three-way check runs when `PLATFORM` is `cursor` or `claude`. Cursor's `RULE_ACTION` check stays Cursor-only. |
| Actionable count | The Claude branch counts `SYSINST_ACTION` `update` or `new`. Use `${SYSINST_ACTION:-unchanged}` so Codex is unaffected. |
| Apply | The Claude branch copies `system-instructions.md` into `.claude/` when `SYSINST_ACTION` is `update` or `new`. |
| `write_copy_manifest` | Same as install. |
| Scoped git commit | Same as install. |
| `detect_stale_files` | No change. The key `system-instructions.md` has no `/`, so its category falls to `*) continue`, as on Cursor. |
| `merge_claude_md` preserved branch | See below. |

### Preserved-block warning

Add `writ_block_inner_has_line FILE LINE` inside each `writ-merge-bundled` region. It reads the lines between the markers, strips `\r`, and returns 0 when one equals `LINE`. In the preserved branch of each `merge_claude_md`, when it returns non-zero for `@.claude/system-instructions.md`, print:

- `install.sh`: `⚠️  CLAUDE.md: the preserved Writ block has no @.claude/system-instructions.md line. Add it inside the block, or re-run install.sh --force to replace the block.`
- `update.sh`: the same, ending `re-run update.sh --force to replace the block.`

The warning prints in preview and apply. The branch still writes nothing. Keep the two bundles in sync; the bundle tests load each one separately.

### `uninstall.sh`

The Claude branch of the `EXTRA_FILES` block gains `[ -f "$PLATFORM_DIR/system-instructions.md" ] && EXTRA_FILES+=("$PLATFORM_DIR/system-instructions.md")`. The dry run, removal, count, `rmdir "$PLATFORM_DIR"`, and `git add -u "$PLATFORM_DIR/"` already handle every `EXTRA_FILES` entry.

### Byte-identity test method

`test_install_update_claude_parity.sh` builds a committed temp source copy the way `test_install_update_lean_siblings.sh` does (tar of the tree without `.git`, `.cursor`, `.claude`, `.codex`, `.writ`, plus `.writ/docs/*.md`; `git init`; commit). Update runs with `WRIT_REPO="$SRC"`.

The user content mixes CRLF lines, trailing spaces, a non-ASCII line, a line `@notes.md`, and no final newline. A short `python3 -c` helper splits the file on the marker lines and writes the prefix (bytes before the start-marker line) and the suffix (bytes after the end-marker line). The test compares them with `cmp`:

1. Install with no markers: the new prefix equals the original plus one `\n`.
2. Add suffix content below the end marker. Record prefix and suffix.
3. Commit a longer `claude-code/CLAUDE.md` in `$SRC` (one extra line). Run update. The block grows; prefix and suffix are unchanged.
4. Hand-edit the block inner, run `install.sh --force`. Prefix and suffix are unchanged.

## Adapter Corrections (Story 3)

| Location in `adapters/claude-code.md` | Today | Change |
|---|---|---|
| Intro line | "subagent system, git worktrees, agent teams, and hooks" | Drop "agent teams". |
| Installation, automated text, manual Step 1, Final Structure | No `system-instructions.md` | Add the copy to `.claude/system-instructions.md`, the tree entry, and one sentence: `CLAUDE.md` imports it with `@.claude/system-instructions.md`; Claude Code asks once to approve an import that resolves outside the working directory. |
| `### Git Worktree Isolation` steps | "Merges changes back when the subagent completes" | A worktree branches from the repo's default branch unless `worktree.baseRef` is `"head"`. It is removed when the agent made no changes; otherwise it stays on disk with the changes. The orchestrator reconciles them per `skills/subagent-worktree-integration/SKILL.md`. Source: `https://code.claude.com/docs/en/worktrees` § Isolate subagents with worktrees. |
| `/implement-story --all` paragraph | Nonexistent flag; claims merge-back | Remove. One line: `/implement-spec` runs independent stories in parallel batches. |
| `### implement-story --all: Agent Teams (Experimental)` | Nonexistent workflow | Remove the section. |
| `create-spec: Parallel Story Generation` comments | "Changes merge back automatically" | Each story file stays in its worktree until the orchestrator copies it back per the skill. |
| Gotcha 1 | "Worktree merges can conflict" | Copying worktree output back can overwrite newer work when the worktree is stale; follow the skill's stale-worktree step. |
| Gotcha 2 | Agent teams | Remove; renumber the list. |
| Manual Step 1, `cp path/to/writ/claude-code/CLAUDE.md ./CLAUDE.md` | Overwrites the user's file | Append the template between markers (block below). Say that later installs and updates replace only the block, and that `install.sh --platform claude` does all of this. |
| `### Quality Gates with Hooks` example | `"SubagentCompleted"` event and `cd $WORKTREE` | `SubagentStop` example below. Cite `https://code.claude.com/docs/en/hooks` (§ SubagentStart, § SubagentStop). |
| `/goal` section, "the `SubagentCompleted` example above" | Points at the removed event | "the `SubagentStop` example above". Nothing else in that section changes. |
| Model Selection intro | "The six Claude-native agents … do not infer a seventh" *(already replaced by spec 2026-10-20-claude-agent-generator)* | Eight agents, listing `writ-evaluator` and `writ-visual-qa`; no "no `visual-qa` equivalent" wording. |
| Model Selection tier table, Permission Modes table, Final Structure tree | No `writ-evaluator` *(both present since spec 2026-10-20-claude-agent-generator, with `writ-visual-qa`)* | Confirm it is there: `anchor`, `model: inherit`, `permissionMode: plan` (its frontmatter). |

Manual Step 1 target text (first install only):

```bash
[ -s CLAUDE.md ] && [ -n "$(tail -c 1 CLAUDE.md)" ] && printf '\n' >> CLAUDE.md   # end the file with a newline first
{ printf '%s\n' '<!-- writ:start -->'; cat path/to/writ/claude-code/CLAUDE.md; printf '%s\n' '<!-- writ:end -->'; } >> CLAUDE.md
cp path/to/writ/system-instructions.md .claude/system-instructions.md
```

Hook example target (replaces the `SubagentCompleted` JSON):

```json
// .claude/settings.json
{
  "hooks": {
    "SubagentStop": [
      {
        "matcher": "^writ-coder$",
        "hooks": [{ "type": "command", "command": "\"$CLAUDE_PROJECT_DIR\"/.claude/hooks/writ-coder-checks.sh" }]
      }
    ]
  }
}
```

```bash
#!/usr/bin/env bash
# .claude/hooks/writ-coder-checks.sh: reads the hook input JSON on stdin.
dir=$(python3 -c 'import json, sys; print(json.load(sys.stdin)["cwd"])')
cd "$dir" || exit 0
npm test && npx tsc --noEmit && exit 0
echo "Tests or typecheck failed. Fix them before you stop." >&2
exit 2
```

Facts the adapter states with it, from the hooks docs: the `SubagentStop` matcher is the agent type, which for a custom subagent is its frontmatter `name`; exit 2 keeps the subagent running and gives it the stderr text. The docs do not say whether `cwd` is a worktree-isolated subagent's worktree, so the orchestrator re-runs the checks in its own checkout after reconciling (worktree skill step 4).

Text the eval pins must stay untouched: `### Fresh Isolated Execution Lanes`, `phase-spec-result-v1`, `no prior conversational transcript`, `isolated worktree`, `### Quarantine and Resume`, `writ/quarantine/`, the three recommendation-semantics sentences, `**Review panel (ADR-028): unavailable.**`, and the `/goal` section that `test_goal_emit_gold.py` reads.

## CLAUDE.md Ownership on Uninstall and Reinstall (Story 4)

### `remove_claude_md_block` in `uninstall.sh`

Put it between `# <<< writ-remove-claude-md-bundled-begin (used by scripts/tests/test_remove_claude_md_block.sh — keep synced) >>>` and `# <<< writ-remove-claude-md-bundled-end >>>`. The region carries its own marker-count helper (`writ_claude_md_marker_counts`, a copy of `writ_agents_md_marker_counts`) so the bundle test can load it alone, the way `merge_claude_md` duplicates `merge_agents_md`.

| Input | Result | `REMOVE_CLAUDE_MD_NOTE` | Return |
|---|---|---|---|
| No file | Nothing | `✓ CLAUDE.md (no file present)` | 0 |
| No markers | Untouched | `✓ CLAUDE.md (no Writ block present)` | 0 |
| Not exactly one start and one end marker, or end before start | Untouched; `❌ … malformed markers …` on stderr | `CLAUDE.md block error: malformed markers` | 13 |
| Zero bytes left | File deleted | `🗑  Removed: CLAUDE.md (empty after Writ block removal)` | 0 |
| Otherwise | Bytes before the start-marker line plus bytes after the end-marker line | `🗑  Removed: CLAUDE.md Writ block` | 0 |

Write the result as `{ [ "$start_line" -gt 1 ] && head -n $((start_line - 1)) "$file"; tail -n +$((end_line + 1)) "$file"; } >"$tmp"`. `head` and `tail` copy those bytes exactly, CR characters and a missing final newline included. Test emptiness with `[ -s "$tmp" ]`. Write back with `cat "$tmp" >"$file"` so the file keeps its mode, then remove `$tmp`.

### Wiring in `uninstall.sh`

| Block | Change |
|---|---|
| Inventory | The Claude branch stops adding `CLAUDE.md` to `EXTRA_FILES`. When `CLAUDE.md` exists it sets `CLAUDE_EXTRA_COUNT=1` and `CLAUDE_EXTRA_DESC="CLAUDE.md Writ block "`, mirroring `CODEX_EXTRA_COUNT`/`CODEX_EXTRA_DESC`. The Extras line and `TOTAL` include them. `.claude/system-instructions.md` stays in `EXTRA_FILES` (Story 2). |
| Dry run | The Claude branch prints `  🗑  CLAUDE.md Writ block` when the file exists. |
| Remove | After the `EXTRA_FILES` loop, the Claude branch runs `remove_claude_md_block "CLAUDE.md"`, echoes the note, and counts a `🗑` note as removed, as the Codex branch does. |
| Git commit | No change. `git add -u "CLAUDE.md"` already records an edit or a deletion. |

### Lifecycle command docs

| File | Location | Change |
|---|---|---|
| `commands/uninstall-writ.md` | Step 3 "Platform-specific files", Claude bullet | Replace `rm CLAUDE.md` with: remove only the marker-bounded Writ block from `CLAUDE.md` (what `uninstall.sh --platform claude` does) and `.claude/system-instructions.md`; delete `CLAUDE.md` only if nothing is left. |
| `commands/uninstall-writ.md` | Step 3 "Do NOT remove" | Add: Claude Code content outside the `<!-- writ:start -->` / `<!-- writ:end -->` markers in `CLAUDE.md`. |
| `commands/reinstall-writ.md` | Platform table, Claude row | Extra files: `CLAUDE.md` Writ block (project root), `system-instructions.md`. |
| `commands/reinstall-writ.md` | Step 3 platform extras, Claude bullet | `[platform_dir]/system-instructions.md`. Leave `CLAUDE.md` in place; Step 4 replaces only its Writ block. |
| `commands/reinstall-writ.md` | Step 4 item 4, Claude bullet | Merge the template into `CLAUDE.md` the way `install.sh --platform claude --force` does: create the file with the block if absent, append the block if the file has no markers, otherwise replace only the lines between the markers. Then `cp $WRIT_SRC/system-instructions.md [platform_dir]/`. |
| `commands/reinstall-writ.md` | Step 3 "Do NOT remove" | Add the same Claude line as `/uninstall-writ`. |

`test_lifecycle_commands_claude_md.py` reads both files and fails on today's text: `rm CLAUDE.md` in `uninstall-writ.md`, and any `cp` whose target is `./CLAUDE.md` (regex `cp\s+\S*claude-code/CLAUDE\.md\s+\./CLAUDE\.md`) in `reinstall-writ.md`. It also requires the Claude bullets to mention the markers and Step 4 to name `install.sh --platform claude --force`.

### Round-trip test method

`test_uninstall_claude_md.sh` reuses the committed temp source copy from `test_install_update_lean_siblings.sh`. Project A starts with a hand-written `CLAUDE.md` (CRLF lines, trailing spaces, a non-ASCII line, blank lines, no final newline). Install, then `uninstall.sh --platform claude --no-commit`; the file must `cmp` equal to the original plus one `\n`. Project B starts with no `CLAUDE.md`; after install and uninstall it must not exist. A dry run on a third installed project must leave every file unchanged and print `CLAUDE.md Writ block`.

## Error & Rescue Map

| Operation | Failure | Handling | What the person sees |
|---|---|---|---|
| Generator reads manifest | Missing or unreadable | `unverifiable`, exit 0 | `reason: manifest missing: .writ/manifest.yaml`; eval turns it into a finding |
| Generator validates manifest | Entry lacks `purpose`, bad name, duplicate | `fail`, nothing written | `reason: manifest <detail>` naming the entry |
| Generator renders a purpose | `@` outside backticks | `fail`, nothing written | `reason: import-token <name>` |
| Generator renders a purpose | `\|` in text | Escaped as `\|` | Table renders intact |
| Generator checks pipeline | Pipeline command not in manifest (e.g. after a rename) | `fail` | `reason: pipeline <name>` |
| Generator reads agents | File lacks `name` or `description` | `fail` | `reason: agent <file>` |
| Generator writes | Permission or disk error | `fail`, temp file removed | `reason: write <error>` |
| `--check` | Template absent | `fail` | `reason: absent claude-code/CLAUDE.md` |
| `--check` | Command added to manifest, template not regenerated | `fail` | `reason: missing <name>`; eval finding names `/<name>` and the remedy |
| Install copies system instructions | Source lacks `system-instructions.md` | `cp` fails; `set -e` aborts before the manifest is written (same as Cursor) | `cp` error, non-zero exit |
| Install merges block | Malformed markers | Existing: return 13, file untouched, install aborts | Existing `❌` line |
| Update system instructions | Local copy modified | Preserved | `⚡ Preserved: system-instructions.md (local modifications)` |
| Update system instructions | No local copy (pre-parity install) | Copied | `✨ New:       system-instructions.md` |
| Install or update block | Modified, no import line | Preserved, warned | `⚠️` line naming the import line and `--force` |
| Uninstall system instructions | File absent | Skipped by the `-f` test | Not listed |
| Uninstall removes block | No `CLAUDE.md` | Nothing to do | `✓ CLAUDE.md (no file present)` |
| Uninstall removes block | No markers | File untouched | `✓ CLAUDE.md (no Writ block present)` |
| Uninstall removes block | Malformed markers (count or order) | Return 13, file untouched; uninstall stops under `set -e`, as Codex does | `❌ CLAUDE.md block error: malformed markers` on stderr |
| Uninstall removes block | Zero bytes left after removal | File deleted | `🗑  Removed: CLAUDE.md (empty after Writ block removal)` |
| Reinstall merges block | User follows `/reinstall-writ` Step 4 | Block created, appended, or replaced between markers; never a copy over the file | The user's text stays |
| Claude Code session | Import resolves outside the working directory | Claude Code asks once; a decline disables the import | [OUT OF SCOPE — Claude Code's rule; the adapter states it] |

## Shadow Paths

| Path | Install | Update | Uninstall | Generator |
|---|---|---|---|---|
| Happy | Block created or appended with the import line; system instructions copied | Block replaced from baseline; system instructions updated | Block removed, every other byte kept; system instructions removed | `pass`, template written |
| Nil input | No `CLAUDE.md` → created | No `CLAUDE.md` → existing guard aborts ("Run install.sh first") | No `CLAUDE.md` → note only | No manifest → `unverifiable` |
| Empty input | Empty `CLAUDE.md` → block written with no leading blank line (existing case 6) | Empty block inner → modified → preserved and warned | Block-only `CLAUDE.md` → deleted | Manifest with `commands:` and no entries → `fail` (`manifest no commands`) |
| Upstream error | Template missing → return 12 (existing) | Same | Malformed markers → return 13, untouched | Agents dir missing → `unverifiable` |

## Interaction Edge Cases

| Case | Expected |
|---|---|
| The user already wrote `@.claude/system-instructions.md` outside the block | Bytes untouched. Claude Code may read the file twice; harmless. |
| Preserved block that already has the import line | No warning. |
| Two updates in a row with no upstream change | Second run: block `unchanged`, system instructions unchanged, "Already up to date". |
| `install.sh` re-run over a locally edited `.claude/system-instructions.md` | Overwritten, same as Cursor's "always updated". `update.sh` is the path that preserves edits. |
| CRLF `CLAUDE.md` | Markers still found (`\r` stripped); bytes outside them unchanged. |
| A manifest command renamed (e.g. the `/design` rename in another Phase 13 spec) | `--check` reports `missing <new>` and `extra <old>`; regenerate. |
| A new file in `claude-code/agents/` | `--check` reports `stale`; regenerate. |
| Blank lines next to the block on uninstall | Kept. Codex's `remove_agents_md_block` trims them; Claude does not (spec.md → D5). |
| Uninstall leaves only whitespace in `CLAUDE.md` | Kept; only zero bytes counts as empty. |
| Install → uninstall round trip on a file with no final newline | Original plus the one `\n` install's append added. |
| File mode after uninstall | Unchanged: the result is written back with `cat "$tmp" >"$file"`, not `mv`. [OUT OF SCOPE — today's `merge_claude_md` writes through `mktemp` + `mv`, which leaves `CLAUDE.md` at mode 0600; reported, not fixed here] |

## Verification

```bash
uv run --python 3.9 pytest
uv run pytest
for t in scripts/tests/test_*.sh; do bash "$t" || echo "FAIL $t"; done
bash scripts/eval.sh                       # outside the sandbox; 0 findings
python3 scripts/gen-claude-md.py --check   # pass
```

Never run `install.sh`, `update.sh`, or `uninstall.sh` in the Writ repo; `.claude/` and `.cursor/` are symlinks into the product source. The tests create temp projects.

Manual UAT (Claude Code, not automatable here): in a temp project installed with `--platform claude`, start `claude`, run `/context`, and confirm `.claude/system-instructions.md` appears under **Memory files** (the memory docs name `/context` for this). Then repeat from a subdirectory to observe the external-import approval.
