# UAT Plan: Generated Platform Trees

> **Generated:** 2026-10-23
> **Spec:** `.writ/specs/2026-10-22-generated-platform-trees/`
> **Stories Covered:** 5 of 5 completed
> **Total Scenarios:** 25
> **Verification recipe:** does not apply. Writ is markdown plus Python and bash scripts with no application to boot, so no `.writ/docs/app-verification.md` was drafted, saved, or bound (Step 1.3 asked nothing). Every scenario is `human — no recipe`.

## How to Use This Plan

1. Work through scenarios in order (they're grouped by story, ordered by priority)
2. For each scenario, follow the steps exactly as written
3. Mark Pass or Fail — add notes for any unexpected behavior
4. Scenarios marked Fail should be filed as issues or fed back to the spec
5. A feature passes UAT when all scenarios pass (or failures are accepted as known limitations)

**Conventions for this plan:**

- There is no app to boot and no recipe. Every scenario except Scenario 6 runs shell commands in a scratch clone and compares output by eye. Scenario 6 is live: the maintainer drives `/create-spec` in a Claude Code session opened in the clone and judges how discovery enters Plan Mode.
- **Never run `install.sh` or `update.sh` in the Writ repo, never run the driver's write mode there during this plan, and never open the live session there.** `.claude/`, `.cursor/`, and `.codex/` in the repo are symlinks into the source; the clone keeps them, so `/create-spec` is a project command inside `$CL` with nothing installed.
- Every helper refuses to run unless the shell is inside `$W`; `$REPO` is cloned from and never written to. Run the plan in `bash` on macOS (`sed -i ''`), outside any sandbox (`eval.sh` and the install test do `git init`).
- Paste this setup block once per shell. Stop if the first line does not print `W=/...`.

  ```bash
  W=$(mktemp -d "${TMPDIR:-/tmp}/writ-uat-trees.XXXXXX") && cd "$W" && W=$PWD && echo "W=$W"
  REPO=/Users/asellke/Projects/writ            # read only: cloned from, never edited, never installed into
  CL="$W/clone"; git clone -q "$REPO" "$CL"    # committed tree on the current branch; generated files included
  inW() { case "$PWD/" in "$W"/*) ;; *) echo "refusing: $PWD is outside $W" >&2; return 1;; esac; }
  # gen <args>: the driver inside the clone, then its exit code
  gen() { inW && (cd "$CL" && python3 scripts/gen-platform-trees.py "$@"; echo "exit $?"); }
  # pt <pytest args>: the spec's test file on Python 3.9 inside the clone; prints the summary line
  pt() { inW && (cd "$CL" && uv run --python 3.9 pytest scripts/tests/test_gen_platform_trees.py -q "$@" 2>&1 | tail -1); }
  # ev: eval's platform-trees check inside the clone; prints its exit code, then the report section
  ev() { inW && (cd "$CL" && bash scripts/eval.sh --check=platform-trees --report="$W/eval-report.md" >/dev/null; echo "exit $?"; awk '/^## platform-trees$/{f=1;next} f&&/^## /{exit} f' "$W/eval-report.md"); }
  # proj <cursor|claude|codex>: a fresh git-init project under $W installed from the clone; prints the install's source line
  proj() { inW || return 1; local p="$W/proj-$1"; mkdir -p "$p" && git -C "$p" init -q -b main && (cd "$p" && bash "$CL/scripts/install.sh" --platform "$1" --no-commit | grep -F 'Using local writ'); }
  # names <file>: the first column of that file's Capability Map, in order, blanks removed
  names() { awk '/^## Capability Map$/{f=1;next} f&&/^## /{f=0} f&&/^\| `/' "$1" | cut -d'|' -f2 | tr -d ' ' | tr '\n' ' '; echo; }
  # reset: undo every edit to tracked files in the clone and drop untracked ones; prints nothing when clean
  reset() { inW && git -C "$CL" checkout -q -- . && git -C "$CL" clean -qfd && git -C "$CL" status --short; }
  ```

- Expected output was observed on 2026-10-23 against `304d63e` (branch `phase/14-front-door-and-distribution`). Story 1 landed in `bf7434a`, Story 2 in `19ffbc5`, Story 3 in `bf407c5`, Story 4 in `4677ef3`, Story 5 in `1340368`. Line numbers (`adapters/codex.md:142`, `commands/status.md:500`, `skills/tdd-cycle/SKILL.md:122`, the `## ` heading lines of `claude-code/CLAUDE.md`) hold for that commit; recompute them from the file if the tree has moved. After each scenario that edits the clone, run `reset` and confirm it prints nothing. When done: `rm -rf "$W"`.
- Drift log: DEV-001 to DEV-010 are Small and auto-amended. Those that change what the reader sees are named where they appear: DEV-001 (the dev-only denylist entry is in three scripts, `unlink.sh` included; Scenario 20), DEV-003 (the Cursor `canvas-preview` and `Plan Mode` rows repeat the degradation sentence in both map cells; Scenario 8), DEV-004 (write mode summarizes `(<n> written, <r> reasons)`, `--check` the five counts; Scenarios 10, 15), DEV-005 (a stale generated file blocks nothing in write mode, write repairs it; Scenario 15), DEV-006 (`claude-code/CLAUDE.md` carries no generated-file comment; Scenario 9), DEV-007 (the Codex renderer fails closed on an `adapters/` mention or at 16 KiB; Scenario 14), DEV-008 (eval runs `--check` once, so each hit is exactly one finding; Scenario 19), DEV-009 (`writ-design.md:137` was reworded, not renamed; Scenario 17), DEV-010 (`install.sh --no-commit`; Scenarios 21 to 23). DEV-002 (`http://…` tokens are not identifiers) changes nothing a step shows.

## Coverage Summary

| Story | Status | Scenarios | Source Breakdown |
|-------|--------|-----------|-----------------|
| Story 1: Adapter Table Parser and Parity Repairs | ✅ Covered | 6 | AC: 3, Errors: 0, Shadow: 2, Edge: 0, Experience: 1 |
| Story 2: Driver Write Mode for the Cursor and Claude Code Root Files | ✅ Covered | 5 | AC: 4, Errors: 0, Shadow: 1, Edge: 0 |
| Story 3: Generated Codex Template | ✅ Covered | 3 | AC: 2, Errors: 0, Shadow: 0, Edge: 1 |
| Story 4: `--check`, Coverage, Tokens, and Eval Wiring | ✅ Covered | 6 | AC: 6, Errors: 0, Shadow: 0, Edge: 0 (the three edge cases are folded into 15, 16, 18) |
| Story 5: Install Evidence and Issue Closure | ✅ Covered | 5 | AC: 4, Errors: 0, Shadow: 0, Edge: 0, Experience: 1 |

The technical spec's Error & Rescue Map is "Not required" (a build-time generator; its failure modes are the check-shape reasons), so there are no error scenarios; the reasons are covered under Shadow Paths and the State Catalog. No pending stories: all five are Completed ✅.

---

## Story 1: Adapter Table Parser and Parity Repairs

### Scenario 1: `coverage` passes on the committed tree and every map lists the ten neutral names in its adapter's row order

**Source:** Acceptance Criteria (AC-1.1) — Story 1; Success Criteria; State Catalog "Clean tree"; Edge Case "`Task` variants collapse to one name; `Plan Mode` keeps its space"
**Feature:** none
**Verification:** human — no recipe

**Preconditions:** setup block pasted.

**Steps:**
1. `gen coverage`
2. `for f in cursor/writ.mdc claude-code/CLAUDE.md codex/AGENTS.md.template; do printf '%s: ' "$f"; names "$CL/$f"; done`
3. `pt -k "parse_real_adapters or capability_name or vendor_only_tokens"`

**Expected Result:**
- Step 1: `pass`, then `gen-platform-trees: pass (0 stale, 0 missing, 0 orphan, 0 unmapped, 0 vendor)`, `exit 0`.
- Step 2: `cursor/writ.mdc` lists `` `Task` `AskQuestion` `codebase_search` `file_search` `todo_write` `read_file` `run_terminal_cmd` `list_dir` `canvas-preview` `PlanMode` `` (the helper strips blanks; the row reads `Plan Mode`). `claude-code/CLAUDE.md` is the same with `` `Task({readonly:true})` `` second (a variant sub-row, not an eleventh name). `codex/AGENTS.md.template` lists `read_file`, `run_terminal_cmd`, `list_dir`, `todo_write` in that order after `file_search` (the Codex table's order). No file lists `readonly`, `EnterPlanMode`, `Grep`, or `Glob` in its first column.
- Step 3: `11 passed, 89 deselected …` — the golden ten-name set, nine name normalizations (`Task({ prompt })` → `Task`; `canvas-preview` and `Plan Mode` kept whole), and `EnterPlanMode` in the vendor-only set with `Read`, `Write`, `Bash` allowlisted.

**Status:** [x] Pass  [ ] Fail — **Notes:** agent run 2026-10-23 at 0b033a3: `coverage` prints `pass` with five zeros, exit 0; maps list 10 Cursor names, 11 Claude Code names with `Task({readonly:true})` second, Codex order `read_file` `run_terminal_cmd` `list_dir` `todo_write`; no `readonly`/`EnterPlanMode`/`Grep`/`Glob` rows; `11 passed, 89 deselected`.

---
### Scenario 2: The parity repairs, the four `Plan Mode` rows, the three command sentences, and the Plan Mode issue's Resolution are on disk

**Source:** Acceptance Criteria (AC-1.5) — Story 1; Contract items 4 and 7; Business Rules 9 and 10
**Feature:** none
**Verification:** human — no recipe

**Preconditions:** setup block pasted.

**Steps:**
1. `grep -n '^| `Plan Mode`' "$CL"/adapters/{cursor,claude-code,codex,openclaw}.md; grep -n '^| `file_search`' "$CL/adapters/codex.md"; grep -n '^| `Task({ readonly: true })`\|^| `readonly' "$CL/adapters/openclaw.md"`
2. `grep -n "Plan Mode\` row" "$CL"/commands/{create-spec,plan-product,new-command}.md`
3. `grep -n 'spec_ref\|^## Resolution' "$CL/.writ/issues/improvements/2026-10-22-create-spec-discovery-skips-plan-mode-on-claude-code.md"; pt -k "plan_mode_row or command_sentence or issue_resolution or codex_file_search or openclaw_readonly"`

**Expected Result:**
- Step 1: one `Plan Mode` row per adapter, each the last row of its tool table. `cursor.md:116`: column 2 `create-spec, plan-product, new-command`, column 3 "Ask the user to switch to Plan Mode; continue when they have. If the platform has no toggle, say so and proceed read-only." `claude-code.md:199`: "`EnterPlanMode`; present the contract proposal as the plan; after `ExitPlanMode` approval, lock with AskQuestion". `codex.md:148`: "No agent-side mode: run discovery as a read-only conversation and say so; Codex's `/plan` is user-side". `openclaw.md:20`: "No agent-side mode: run discovery as a read-only conversation and say so". The three non-Cursor rows end with the same degradation sentence as Cursor's. `codex.md:142` is `` | `file_search` | `Glob("**/pattern*")` | Built-in Glob tool | ``. `openclaw.md:18` is the `` `Task({ readonly: true })` `` row, and no row starts with `` `readonly ``.
- Step 2: exactly one line per file. `create-spec.md:246` begins "After the context scan, run discovery in Plan Mode, entered through the adapter's `Plan Mode` row; the user controls when to switch back."; `plan-product.md:178` and `new-command.md:45` each contain "through the adapter's `Plan Mode` row".
- Step 3: `> **spec_ref:** .writ/specs/2026-10-22-generated-platform-trees/spec.md` and a `## Resolution` heading; `10 passed, 90 deselected …`.

**Status:** [x] Pass  [ ] Fail — **Notes:** agent run 2026-10-23 at 0b033a3: plan drift: adapter line numbers moved after the plugin-distribution merge (`cursor.md:156`, `claude-code.md:222`, `codex.md:150`, `file_search` at `codex.md:144`; openclaw 18 and 20 unchanged). Row text matches and each `Plan Mode` row is the last in its table; one sentence each at `create-spec.md:246`, `plan-product.md:178`, `new-command.md:45`; issue has `spec_ref` and `## Resolution`; `10 passed, 90 deselected`.

---
### Scenario 3: An adapter without its tool-table heading is `unverifiable`, exit 0, and nothing is written

**Source:** Shadow Path "Nil input" (technical spec); Acceptance Criteria (AC-1.3) — Story 1; State Catalog "Adapter section heading missing"
**Feature:** none
**Verification:** human — no recipe

**Preconditions:** setup block pasted; `reset` prints nothing.

**Steps:**
1. `sed -i '' '/^### Quick reference — orchestration primitives/d' "$CL/adapters/codex.md"; gen --check; gen; git -C "$CL" status --short; reset`

**Expected Result:**
- `--check`: `unverifiable`, `reason: section ### Quick reference — orchestration primitives in adapters/codex.md`, `gen-platform-trees: unverifiable (0 stale, 0 missing, 0 orphan, 0 unmapped, 0 vendor)`, `exit 0`.
- Write mode: the same verdict and reason, `gen-platform-trees: unverifiable (0 written, 1 reasons)`, `exit 0`.
- `git status --short` prints only ` M adapters/codex.md`: no generated file changed. `reset` prints nothing.

**Status:** [x] Pass  [ ] Fail — **Notes:** agent run 2026-10-23 at 0b033a3: `--check` and write both print `unverifiable` with the section reason, exit 0, write `(0 written, 1 reasons)`; status shows only ` M adapters/codex.md`; `reset` clean.

---
### Scenario 4: A header-only table and a row with the wrong cell count each fail closed, naming the file and line

**Source:** Shadow Path "Empty input" (technical spec); Acceptance Criteria (AC-1.2) — Story 1; State Catalog "Malformed table row"; Hardest Constraint
**Feature:** none
**Verification:** human — no recipe

**Preconditions:** setup block pasted; `reset` prints nothing.

**Steps:**
1. `awk 'BEGIN{s=0} /^### Quick reference — orchestration primitives/{s=1} s==1&&/^\|/{s=2;print;next} s==2&&/^\|/{s=3;print;next} s==3&&/^\|/{next} s==3&&!/^\|/{s=0} {print}' "$CL/adapters/codex.md" > "$W/t" && mv "$W/t" "$CL/adapters/codex.md"; gen --check; gen; reset`
2. `L=$(grep -n '^| `file_search`' "$CL/adapters/codex.md" | cut -d: -f1); echo "line $L"; sed -i '' "${L}s/.*/| \`file_search\` | two cells |/" "$CL/adapters/codex.md"; gen --check; gen; git -C "$CL" status --short; reset`
3. `pt -k "malformed_row or missing_section or test_parity"`

**Expected Result:**
- Step 1 (the Codex table keeps its header and separator rows only): `fail`, `reason: empty adapters/codex.md`, five zeros, `exit 1`; write mode `fail`, the same reason, `gen-platform-trees: fail (0 written, 1 reasons)`, `exit 1`.
- Step 2: `line 142`; `fail`, `reason: malformed adapters/codex.md:142` (the 1-based line of the bad row), `exit 1` from both modes; `git status --short` prints only ` M adapters/codex.md`.
- Step 3: `5 passed, 95 deselected …` (wrong cell count, empty first cell, header-only, missing heading, parity gap on fixtures).
- `reset` prints nothing after steps 1 and 2.

**Status:** [x] Pass  [ ] Fail — **Notes:** agent run 2026-10-23 at 0b033a3: plan drift: the bad row is line 144, not 142. Header-only table gives `reason: empty adapters/codex.md`, exit 1 in both modes, `(0 written, 1 reasons)`; bad row gives `malformed adapters/codex.md:144`, exit 1 in both modes; status only ` M adapters/codex.md`; `5 passed, 95 deselected`.

---
### Scenario 5: A neutral name missing from one adapter is `unmapped`, and `--check` also reports the map it would change

**Source:** Acceptance Criteria (AC-1.4) — Story 1; Acceptance Criteria (AC-4.2) — Story 4; State Catalog "Capability used in a command with no row in one adapter"; Business Rule 3
**Feature:** none
**Verification:** human — no recipe

**Preconditions:** setup block pasted; `reset` prints nothing.

**Steps:**
1. `sed -i '' '/^| `file_search` |/d' "$CL/adapters/codex.md"; gen coverage; gen --check; gen; git -C "$CL" status --short; reset`

**Expected Result:**
- `coverage`: `fail`, `reason: unmapped file_search in adapters/codex.md`, `gen-platform-trees: fail (0 stale, 0 missing, 0 orphan, 1 unmapped, 0 vendor)`, `exit 1`.
- `--check`: the same reason plus `reason: stale codex/AGENTS.md.template` (the committed Codex map still has the row a fresh render would drop), summary `(1 stale, 0 missing, 0 orphan, 1 unmapped, 0 vendor)`, `exit 1`.
- Write mode: `fail`, only the `unmapped` reason, `(0 written, 1 reasons)`; `git status --short` prints only ` M adapters/codex.md`. `reset` prints nothing.

**Status:** [x] Pass  [ ] Fail — **Notes:** agent run 2026-10-23 at 0b033a3: `coverage` gives `unmapped file_search in adapters/codex.md` (1 unmapped), exit 1; `--check` adds `stale codex/AGENTS.md.template` (1 stale, 1 unmapped); write mode only the unmapped reason, `(0 written, 1 reasons)`; status only ` M adapters/codex.md`.

---
### Scenario 6: `/create-spec` discovery on Claude Code enters Plan Mode itself through `EnterPlanMode` (live)

**Source:** Experience Design — State Catalog "`/create-spec` discovery on Claude Code"; Contract item 4; Acceptance Criteria (AC-1.5) — Story 1; the Plan Mode issue's Resolution ("hygiene Scenario 29 was not re-run … That is UAT for this spec")
**Feature:** none
**Verification:** human — no recipe

**Preconditions:** setup block pasted; `reset` prints nothing; Claude Code installed, with a model and thinking level of at least `create-spec`'s `entry_level`. Open the session from a second shell that has the setup block: `inW && (cd "$CL" && claude)`. Never in `$REPO`.

**Steps:**
1. Type: `/create-spec a --json mode for /status that prints project state for scripts` (a request that needs open-ended shaping and fits the Writ repo; a UI request makes the command correctly decline, since Writ has no UI).
2. Watch the turn after the context scan. Answer one or two discovery questions, then say you are ready for a contract.
3. When the contract proposal appears as the plan, approve the plan exit. At the **Contract Decision** question, do not choose "Lock contract and create spec package"; pick the option that revises or stops, then end the session.
4. In the first shell: `reset`

**Expected Result:**
- Step 2: after the context summary the agent enters Plan Mode on its own (an `EnterPlanMode` call or the plan-mode indicator), without asking you to switch modes and without saying the platform has no toggle. Discovery questions arrive one at a time while in Plan Mode; no file is written during discovery.
- Step 3: the plan the agent presents for exit is the contract proposal (deliverable, must-include, success criteria), not a build plan. Only after the plan exit is approved does the Contract Decision render as the native question widget (or a numbered list). Discovery is not absorbed into Plan Mode: the command reaches its Contract Decision step.
- Step 4: `reset` prints nothing: no spec folder, no `.writ/` edits.

**Status:** [x] Pass  [ ] Fail — **Notes:** maintainer run 2026-10-23 in a clone of 35d81a0, Claude Code 2.1.310. Run 1 with the plan's request (an API-keys settings page): after the context scan the agent loaded and called `EnterPlanMode` on its own, asked one question, then presented a plan that stopped the command because Writ has no UI to host the page (correct pushback; the contract half was not exercised). plan drift: the scenario's request does not fit the Writ repo; use a Writ-shaped request. Run 2 with `/create-spec a --json mode for /status that prints project state for scripts` ran in the primary checkout rather than the clone (session cwd `/Users/asellke/Projects/writ`; it wrote only its plan file under `~/.claude/plans/`, and the repo stayed clean): the agent called `EnterPlanMode` itself, asked three questions one at a time, presented a plan titled "Specification Contract: ..." (deliverable, must-include, success criteria) for exit, and after the exit was approved the Contract Decision question rendered (Lock / Edit / Explore risks / More questions); not locked. The clone stayed clean after run 1. Finding: Claude Code's ExitPlanMode dialog says the plan is "ready to execute", which reads as if approval starts implementation; it only accepts the contract draft. A first line in the contract plan saying so would remove the ambiguity.

---

## Story 2: Driver Write Mode for the Cursor and Claude Code Root Files

### Scenario 7: `cursor/writ.mdc` is the frontmatter, the generator comment, the whole of `system-instructions.md`, and the Cursor map (the takeover diff)

**Source:** Acceptance Criteria (AC-2.1, AC-2.5) — Story 2; Business Rules 6 and 12; Interaction Pattern "every generated file opens with a comment naming the generator"
**Feature:** none
**Verification:** human — no recipe

**Preconditions:** setup block pasted.

**Steps:**
1. `head -4 "$CL/cursor/writ.mdc"`
2. `diff "$CL/system-instructions.md" "$CL/cursor/writ.mdc"; echo "diff exit $?"`
3. `diff <(awk '/^## Prime Directive/,/^## [^P]/' "$CL/system-instructions.md") <(awk '/^## Prime Directive/,/^## [^P]/' "$CL/cursor/writ.mdc") && echo "prime directive byte-equal"`

**Expected Result:**
- Step 1: `---`, `alwaysApply: true`, `---`, then `<!-- generated by scripts/gen-platform-trees.py from system-instructions.md and adapters/cursor.md — do not hand-edit; regenerate -->`.
- Step 2: only `>` lines, two hunks: `3a4` (the comment line) and `82a84,100` (a blank line, `## Capability Map`, the lead sentence "Commands name capabilities; this table maps them to this platform.", the `Capability | On this platform | When unavailable` header, and the ten Cursor rows); `diff exit 1`. No `<` line: nothing of the source file is missing, which is the Story 2 takeover record (the hand copy was byte-identical to `system-instructions.md`).
- Step 3: `prime directive byte-equal`.

**Status:** [x] Pass  [ ] Fail — **Notes:** agent run 2026-10-23 at 0b033a3: head shows frontmatter and the generator comment; diff has only `>` lines in hunks `3a4` and `82a84,100` (heading, lead sentence, header, ten rows), `diff exit 1`; `prime directive byte-equal`.

---
### Scenario 8: Each Capability Map follows the rendering rule, with the degradation text only where the adapter carries it

**Source:** Acceptance Criteria (AC-2.2) — Story 2; Business Rule 5; technical spec § Capability Map Section; Edge Case "`Task` variants collapse to one name"; DEV-003
**Feature:** none
**Verification:** human — no recipe

**Preconditions:** setup block pasted.

**Steps:**
1. `awk '/^## Capability Map$/,0' "$CL/cursor/writ.mdc"`
2. `awk '/^## Capability Map$/{f=1} f&&/^## Agents$/{exit} f' "$CL/claude-code/CLAUDE.md"`
3. `awk '/^## Capability Map$/{f=1} f&&/^## Catalog source$/{exit} f' "$CL/codex/AGENTS.md.template"`
4. `pt -k "writ_mdc or claude_md_map or test_capability_map or degradation"`

**Expected Result:**
- Each section: the heading, the lead sentence, the three-column header, then the rows; `—` in "When unavailable" for every row except `canvas-preview` ("No renderer: write a structural description of each draft and say the drafts were not rendered.") and `Plan Mode` ("If the platform has no toggle, say so and proceed read-only.").
- Step 1: 10 rows; the mapping cell is the adapter's Purpose column verbatim, so the `canvas-preview` and `Plan Mode` rows show the degradation sentence in both cells (DEV-003).
- Step 2: 11 rows: `` `Task` `` ("Automatic delegation to named subagent") followed by the sub-row `` `Task({ readonly: true })` `` ("`permissionMode: plan` + `disallowedTools: Write, Edit`"); `` `Plan Mode` `` maps to "`EnterPlanMode`; present the contract proposal as the plan; after `ExitPlanMode` approval, lock with AskQuestion". The section is the last thing before `## Agents`.
- Step 3: 10 rows (the Codex `Task` row is a single row); `` `Plan Mode` `` maps to "No agent-side mode: run discovery as a read-only conversation and say so; Codex's `/plan` is user-side".
- Step 4: `6 passed, 94 deselected …`.

**Status:** [x] Pass  [ ] Fail — **Notes:** agent run 2026-10-23 at 0b033a3: Cursor 10 rows with the degradation sentence in both cells for `canvas-preview` and `Plan Mode`; Claude Code 11 rows with the `Task({ readonly: true })` sub-row and `EnterPlanMode` row, ending before `## Agents`; Codex 10 rows with the user-side `/plan` row; `6 passed, 94 deselected`.

---
### Scenario 9: `claude-code/CLAUDE.md` carries the map between the Commands table and `## Agents`, and its own generator still passes

**Source:** Acceptance Criteria (AC-2.3) — Story 2; Business Rule 7; DEV-006
**Feature:** none
**Verification:** human — no recipe

**Preconditions:** setup block pasted.

**Steps:**
1. `head -1 "$CL/claude-code/CLAUDE.md"; grep -n '^## ' "$CL/claude-code/CLAUDE.md"`
2. `(cd "$CL" && python3 scripts/gen-claude-md.py --check; echo "exit $?")`

**Expected Result:**
- Step 1: the file opens with `# Writ` and no generated-file comment (DEV-006: the existing generator keeps its header); the headings are `9:## Commands`, `51:## Capability Map`, `69:## Agents`, `82:## Pipeline`, `90:## Principles`, in that order.
- Step 2: `pass`, `gen-claude-md: pass (33 commands, 8 agents)`, `exit 0`.

**Status:** [x] Pass  [ ] Fail — **Notes:** agent run 2026-10-23 at 0b033a3: opens `# Writ` with no generated comment; headings at 9, 51, 69, 82, 90 in plan order; `gen-claude-md: pass (33 commands, 8 agents)`, exit 0.

---
### Scenario 10: Write mode on a clean clone rewrites all nineteen files byte-identically and reports them

**Source:** Acceptance Criteria (AC-2.4) — Story 2; Journey step 2; Contract item 6 ("only what differs is committed"); DEV-004
**Feature:** none
**Verification:** human — no recipe

**Preconditions:** setup block pasted; `reset` prints nothing.

**Steps:**
1. `gen > "$W/write.txt"; sed -n '1,3p' "$W/write.txt"; echo "wrote lines: $(grep -c '^wrote ' "$W/write.txt")"; tail -2 "$W/write.txt"`
2. `git -C "$CL" status --short; echo "(end status)"; ls "$CL/cursor" "$CL/codex" | grep -c commands`

**Expected Result:**
- Step 1: `pass`, `wrote cursor/writ.mdc`, `wrote codex/AGENTS.md.template`; `wrote lines: 19` (those two, eight `claude-code/agents/writ-*.md`, eight `codex/agents/*.toml`, and `wrote claude-code/CLAUDE.md` last); `gen-platform-trees: pass (19 written, 0 reasons)`, `exit 0`.
- Step 2: nothing between the command and `(end status)`: every regenerated file equals the committed one, so the committed tree is the generator's output. `0`: identity targets write no `commands/` or `skills/` copies.

**Status:** [x] Pass  [ ] Fail — **Notes:** agent run 2026-10-23 at 0b033a3: plan drift: write mode reports `186 written`, not 19: the 19 named files in the plan's order, then 167 files from the `claude-code-plugin` and `cursor-plugin` targets, so `claude-code/CLAUDE.md` is no longer the last line. `git status` empty after the write; `0` commands dirs in `cursor/` and `codex/`.

---
### Scenario 11: A sub-generator that exits 2 fails the driver with the exit code, and nothing is written

**Source:** Shadow Path "Upstream error" (technical spec); Acceptance Criteria (AC-2.4) — Story 2; spec-lite Error Handling "Sub-generator exit ≥ 2"
**Feature:** none
**Verification:** human — no recipe

**Preconditions:** setup block pasted; `reset` prints nothing.

**Steps:**
1. `printf 'import sys\nsys.exit(2)\n' > "$CL/scripts/gen-claude-agents.py"; gen --check; gen; git -C "$CL" status --short; reset`

**Expected Result:**
- `--check`: `fail`, `reason: gen-claude-agents --check exited 2`, five zeros, `exit 1`.
- Write mode: `fail`, the same reason, `gen-platform-trees: fail (0 written, 1 reasons)`, `exit 1`.
- `git status --short` prints only ` M scripts/gen-claude-agents.py`; `reset` prints nothing.

**Status:** [x] Pass  [ ] Fail — **Notes:** agent run 2026-10-23 at 0b033a3: plan drift: `--check` prints a second reason, `gen-claude-agents load SystemExit`, after `gen-claude-agents --check exited 2` (the claude-code-plugin target loads that module, bc7e964). Both modes fail, exit 1; write `(0 written, 1 reasons)`; status only ` M scripts/gen-claude-agents.py`.

---

## Story 3: Generated Codex Template

### Scenario 12: `codex/AGENTS.md.template` has the merge marker on line 1, the generator comment on line 2, the seven sections in order, no `adapters/`, and is under 16 KiB

**Source:** Acceptance Criteria (AC-3.2, AC-3.4) — Story 3; Business Rule 8; State Catalog "Installed Codex project"
**Feature:** none
**Verification:** human — no recipe

**Preconditions:** setup block pasted.

**Steps:**
1. `sed -n '1,2p;6p' "$CL/codex/AGENTS.md.template" | cut -c1-160; grep -n '^## ' "$CL/codex/AGENTS.md.template"`
2. `echo "adapters/: $(grep -c 'adapters/' "$CL/codex/AGENTS.md.template")"; wc -c < "$CL/codex/AGENTS.md.template"`

**Expected Result:**
- Step 1: line 1 starts `<!-- Writ-managed AGENTS.md fragment: merged between HTML comment markers writ:start and writ:end`; line 2 starts `<!-- generated by scripts/gen-platform-trees.py from .writ/manifest.yaml, skills/*/SKILL.md, and the Codex adapter tool table`; line 6 ends "map tools with the Capability Map below." (no "via `adapters/codex.md`"). The `## ` headings, in order: `Writ on Codex`, `Available Commands`, `Available Agents`, `Available Skills`, `Built-in Codex slash commands vs Writ`, `Capability Map`, `Catalog source`.
- Step 2: `adapters/: 0`; `12478` (under 16384).

**Status:** [x] Pass  [ ] Fail — **Notes:** agent run 2026-10-23 at 0b033a3: line 1 merge marker, line 2 generator comment, line 6 ends "map tools with the Capability Map below."; seven `## ` headings in plan order; `adapters/: 0`; 12478 bytes.

---
### Scenario 13: Every manifest command, every agent, and every skill has a row, with `/writ` first under `### Start here`

**Source:** Acceptance Criteria (AC-3.1) — Story 3; Technical Concern "today lists 28 commands … one skill of sixteen"
**Feature:** none
**Verification:** human — no recipe

**Preconditions:** setup block pasted.

**Steps:**
1. `T="$CL/codex/AGENTS.md.template"; echo "commands $(grep -c '^| `/' "$T") agents $(grep -c '\.codex/agents/' "$T") skills $(grep -c '\.agents/skills/' "$T")"; awk '/^### Start here/{f=1} f&&/^\| `\//{print; exit}' "$T" | cut -c1-60`
2. `for f in "$CL"/commands/*.md; do n=$(basename "$f" .md); [ "$n" = _preamble ] || grep -q "^| \`/$n\` | \`.codex/commands/$n.md\` |" "$T" || echo "missing /$n"; done; for f in "$CL"/agents/*.md; do n=$(basename "$f" .md); grep -q "\`.codex/agents/$n.toml\`" "$T" || echo "missing agent $n"; done; for d in "$CL"/skills/*/; do n=$(basename "$d"); grep -q "\`.agents/skills/$n/SKILL.md\`" "$T" || echo "missing skill $n"; done; echo "(loops done)"; pt -k codex_template`

**Expected Result:**
- Step 1: `commands 33 agents 9 skills 17` (the agents and skills counts include each table's header row, so 8 agents and 16 skills); the first row under `### Start here` is `` | `/writ` | `.codex/commands/writ.md` | ``.
- Step 2: nothing but `(loops done)`: all 33 commands (`/create-goal`, `/implement-phase`, `/revert`, and `/writ` among them), all 8 agents (`evaluator-agent` included), and all 16 skills are present with their install paths; `7 passed, 93 deselected …`, which includes the byte-for-byte match of a fresh render against the committed file.

**Status:** [x] Pass  [ ] Fail — **Notes:** agent run 2026-10-23 at 0b033a3: `commands 33 agents 9 skills 17`; first row under `### Start here` is `/writ`; loops print only `(loops done)`; `7 passed, 93 deselected`.

---
### Scenario 14: An `adapters/` mention that would reach the Codex template fails both modes and writes nothing

**Source:** DEV-007 (render-time guards); Acceptance Criteria (AC-3.2) — Story 3; Contract item 2 ("resolves every capability without `adapters/`")
**Feature:** none
**Verification:** human — no recipe

**Preconditions:** setup block pasted; `reset` prints nothing.

**Steps:**
1. `L=$(grep -n '^| `AskQuestion' "$CL/adapters/codex.md" | head -1 | cut -d: -f1); sed -i '' "${L}s/ | Structured numbered options in prose | / | Structured numbered options in prose (see adapters\/codex.md) | /" "$CL/adapters/codex.md"; sed -n "${L}p" "$CL/adapters/codex.md" | cut -c1-90; gen --check; gen; git -C "$CL" status --short; reset`

**Expected Result:**
- The printed row now contains `(see adapters/codex.md)`.
- `--check`: `fail`, `reason: codex template mentions adapters/`, five zeros, `exit 1`. Write mode: `fail`, the same reason, `(0 written, 1 reasons)`, `exit 1`.
- `git status --short` prints only ` M adapters/codex.md`: the template was not rewritten with the mention. `reset` prints nothing.

**Status:** [x] Pass  [ ] Fail — **Notes:** agent run 2026-10-23 at 0b033a3: edited row shows `(see adapters/codex.md)`; both modes print `codex template mentions adapters/`, exit 1, write `(0 written, 1 reasons)`; status only ` M adapters/codex.md`.

---

## Story 4: `--check`, Coverage, Tokens, and Eval Wiring

### Scenario 15: `--check` passes on the clean clone, names a stale, a missing, and an orphan file, and write mode repairs the stale one

**Source:** Acceptance Criteria (AC-4.1) — Story 4; Journey step 3 (the moment of truth); State Catalog "Hand edit to a generated file"; DEV-004, DEV-005
**Feature:** none
**Verification:** human — no recipe

**Preconditions:** setup block pasted; `reset` prints nothing.

**Steps:**
1. `gen --check; git -C "$CL" status --short`
2. `printf '\nhand edit\n' >> "$CL/cursor/writ.mdc"; gen --check; gen | sed -n '1p;$p'; gen --check | head -1; git -C "$CL" status --short; echo "(end status)"`
3. `rm "$CL/claude-code/CLAUDE.md"; gen --check; reset`
4. `printf '# helper\n' > "$CL/claude-code/agents/helper.md"; gen --check; gen; reset`

**Expected Result:**
- Step 1: `pass`, `gen-platform-trees: pass (0 stale, 0 missing, 0 orphan, 0 unmapped, 0 vendor)`, `exit 0`; status empty (nothing written).
- Step 2: `fail`, `reason: stale cursor/writ.mdc`, `(1 stale, 0 missing, 0 orphan, 0 unmapped, 0 vendor)`, `exit 1`. Write mode then prints `pass` and `gen-platform-trees: pass (19 written, 0 reasons)` (the stale file is what write repairs, DEV-005); `--check` prints `pass`; status is empty, because the regenerated file equals the committed one.
- Step 3: `fail`, `reason: missing claude-code/CLAUDE.md`, `(0 stale, 1 missing, …)`, `exit 1`. `reset` prints nothing.
- Step 4: `fail`, `reason: orphan claude-code/agents/helper.md` and `reason: gen-claude-md: agent helper.md`, `(0 stale, 0 missing, 1 orphan, …)`, `exit 1`; write mode `fail` with the orphan reason, `(0 written, 1 reasons)` (a stray agent file would otherwise ship with the install). `reset` prints nothing.

**Status:** [x] Pass  [ ] Fail — **Notes:** agent run 2026-10-23 at 0b033a3: plan drift: write mode repairs the stale file with `(186 written, 0 reasons)`, not 19, and the step's `sed -n '1p;$p'` shows `pass` and `exit 0` because the summary is the second-to-last line. Clean `--check` passes with five zeros; stale, missing, and orphan reasons and counts match, exit 1; `--check` passes and status is empty after the repair; orphan blocks writes `(0 written, 1 reasons)`.

---
### Scenario 16: A vendor tool name in shipped text is a `vendor` hit with its line; an allowlisted verb and a dotted field are not

**Source:** Acceptance Criteria (AC-4.2) — Story 4; Business Rule 4; Edge Case "`Read` in prose is allowlisted; `TodoWrite` is a vendor hit"; State Catalog "Vendor identifier in a shipped command"
**Feature:** none
**Verification:** human — no recipe

**Preconditions:** setup block pasted; `reset` prints nothing.

**Steps:**
1. `printf '\n`TodoWrite`\n' >> "$CL/commands/status.md"; L=$(wc -l < "$CL/commands/status.md" | tr -d ' '); printf '\n`Read`\n`message.usage`\n' >> "$CL/commands/status.md"; echo "hit line $L"; gen coverage; gen --check | sed -n '2p'; gen | sed -n '1,2p'`
2. `printf '\nUse `Grep("pattern")` here.\n' >> "$CL/skills/tdd-cycle/SKILL.md"; gen coverage | grep '^reason'; reset`
3. `pt -k "vendor_hit or tool_reference or coverage_unmapped"`

**Expected Result:**
- Step 1: `hit line 500` (on `304d63e`); `coverage`: `fail`, `reason: vendor TodoWrite in commands/status.md:500`, `(0 stale, 0 missing, 0 orphan, 0 unmapped, 1 vendor)`, `exit 1`; no reason for `` `Read` `` (allowlisted) or `` `message.usage` `` (a dotted field, not a tool reference). `--check` prints the same reason line; write mode prints `fail` and that reason (a hit blocks every write).
- Step 2: two reasons: the `TodoWrite` line and `reason: vendor Grep in skills/tdd-cycle/SKILL.md:122` (call syntax is normalized to its leading identifier, so `Grep("pattern")` is a hit for `Grep`). `reset` prints nothing.
- Step 3: `15 passed, 85 deselected …`.

**Status:** [x] Pass  [ ] Fail — **Notes:** agent run 2026-10-23 at 0b033a3: plan drift: `gen --check | sed -n '2p'` prints `reason: stale plugins/writ/commands/status.md`; the vendor reason is on line 4, after a second stale reason for `cursor/plugin/commands/status.md` (the plugin targets copy `commands/`). `coverage` gives `vendor TodoWrite in commands/status.md:500` (1 vendor), exit 1, no reason for `Read` or `message.usage`; write mode fails with the vendor reason; step 2 adds `vendor Grep in skills/tdd-cycle/SKILL.md:122`; `15 passed, 85 deselected`.

---
### Scenario 17: The three vendor hits the first `coverage` run found are rewritten, one line each

**Source:** Contract item 3; Acceptance Criteria (AC-4.2) — Story 4; DEV-009
**Feature:** none
**Verification:** human — no recipe

**Preconditions:** setup block pasted.

**Steps:**
1. `sed -n '54p;70p' "$CL/commands/create-issue.md"; sed -n '137p' "$CL/commands/writ-design.md" | cut -c1-120`
2. `grep -rn '`Grep`\|`Glob`\|`browser_navigate`\|`TodoWrite`' "$CL/commands" "$CL/agents" "$CL"/skills/*/SKILL.md; echo "exit $?"`

**Expected Result:**
- Step 1: line 54 says "Use `codebase_search` to find relevant files …"; line 70 says "… with `file_search` for existing issues …"; `writ-design.md:137` reads "navigate to each screen with the platform's browser tool and take screenshots …" with no backticked tool name (DEV-009: no neutral name covers browser navigation, so the sentence was reworded).
- Step 2: no matches, `exit 1`.

**Status:** [x] Pass  [ ] Fail — **Notes:** agent run 2026-10-23 at 0b033a3: `create-issue.md:54` names `codebase_search`, `:70` names `file_search`, `writ-design.md:137` reads "navigate to each screen with the platform's browser tool"; grep finds nothing, exit 1.

---
### Scenario 18: The fixture target writes a full `commands/` and `skills/` tree with only the script-root tokens rewritten; identity targets write in place and refuse `--out-dir`

**Source:** Acceptance Criteria (AC-4.3) — Story 4; Contract item 5; Business Rules 1 and 11; State Catalog "Fixture target with `script_root: ${PLUGIN_ROOT}/scripts`"; Edge Case "Prose `scripts/` mentions outside invocation lines are never rewritten"
**Feature:** none
**Verification:** human — no recipe

**Preconditions:** setup block pasted; `reset` prints nothing.

**Steps:**
1. `gen --target fixture --out-dir "$W/out" > "$W/fx.txt"; sed -n '1,2p' "$W/fx.txt"; echo "wrote lines: $(grep -c '^wrote ' "$W/fx.txt")"; tail -2 "$W/fx.txt"; ls "$W/out/fixture"; echo "commands $(ls "$W/out/fixture/commands" | wc -l | tr -d ' ') skills $(ls "$W/out/fixture/skills" | wc -l | tr -d ' ')"`
2. `echo "tokens in source: $(grep -rEo '\b(python3|bash) scripts/[a-z0-9_-]+\.(py|sh)' "$CL/commands" "$CL/skills" | wc -l | tr -d ' ')  rewritten: $(grep -rEo '\b(python3|bash) \$\{PLUGIN_ROOT\}/scripts/[a-z0-9_-]+\.(py|sh)' "$W/out/fixture" | wc -l | tr -d ' ')  left: $(grep -rEo '\b(python3|bash) scripts/[a-z0-9_-]+\.(py|sh)' "$W/out/fixture" | wc -l | tr -d ' ')"; diff -r "$CL/commands" "$W/out/fixture/commands" | grep '^[<>]' | grep -vcE '(python3|bash) (\$\{PLUGIN_ROOT\}/)?scripts/'; diff "$CL/commands/_preamble.md" "$W/out/fixture/commands/_preamble.md" | grep -c 'scripts/phase-state.py validate-challenge'`
3. `git -C "$CL" status --short; gen --target cursor; ls "$CL/cursor"; gen --target cursor --out-dir "$W/x" 2>&1 | tail -2; gen --target fixture 2>&1 | tail -2; reset`

**Expected Result:**
- Step 1: `pass`, `wrote fixture/commands/_preamble.md`; `wrote lines: 50`; `gen-platform-trees: pass (50 written, 0 reasons)`, `exit 0`; `commands` and `skills`; `commands 34 skills 16` (the same counts as the source).
- Step 2: `tokens in source: 69  rewritten: 69  left: 0`; then `0` (every differing line is a token line, so prose is byte-identical); then `0` (the prose mention `` `scripts/phase-state.py validate-challenge` `` in `_preamble.md:46` is unchanged).
- Step 3: status empty (the in-place tree is untouched by a fixture run); `pass`, `wrote cursor/writ.mdc`, `gen-platform-trees: pass (1 written, 0 reasons)`, `exit 0`, and `cursor/` holds `writ.mdc` only, no `commands`; `--target cursor writes in place; it takes no --out-dir` with `exit 2`; `--target fixture needs --out-dir` with `exit 2`. `reset` prints nothing.

**Status:** [x] Pass  [ ] Fail — **Notes:** agent run 2026-10-23 at 0b033a3: plan drift: 70 script tokens, not 69 (rewritten 70, left 0); `cursor/` holds the committed `plugin/` beside `writ.mdc` (cursor-plugin target), still no `commands`. Otherwise matches: `50 written`, `commands 34 skills 16`, prose diff `0`, `_preamble.md` `0`, `--target cursor` `(1 written, 0 reasons)` exit 0, both `--out-dir` misuse errors exit 2.

---
### Scenario 19: `eval.sh` turns each `--check` reason into one finding with the regenerate remedy, and treats a broken helper as a run error

**Source:** Acceptance Criteria (AC-4.4) — Story 4; Business Rule 13; Journey step 3; DEV-008
**Feature:** none
**Verification:** human — no recipe

**Preconditions:** setup block pasted; `reset` prints nothing. Outside any sandbox.

**Steps:**
1. `ev`
2. `printf '\nhand edit\n' >> "$CL/cursor/writ.mdc"; ev; reset`
3. `printf '\n`TodoWrite`\n' >> "$CL/commands/status.md"; ev | grep -c 'gen-platform-trees --check: vendor TodoWrite in commands/status.md:500'; reset`
4. `printf 'import sys\nsys.exit(2)\n' > "$CL/scripts/gen-platform-trees.py"; ev | sed -n '1p;3,4p'; grep '^- Run errors' "$W/eval-report.md"; reset`
5. `(cd "$CL" && bash scripts/tests/test_eval_platform_trees.sh | tail -1)`

**Expected Result:**
- Step 1: `exit 0`; the section reads `PASS`, then under `Notes (non-blocking):` the line `- NOTE [platform-trees]: gen-platform-trees: pass (0 stale, 0 missing, 0 orphan, 0 unmapped, 0 vendor)`.
- Step 2: `exit 1`; `FAIL (1 finding(s))`; one finding, `` - `cursor/writ.mdc`: gen-platform-trees --check: stale cursor/writ.mdc _Remediation:_ Run python3 scripts/gen-platform-trees.py, then commit the regenerated files. ``; the note shows `fail (1 stale, …)`. `reset` prints nothing.
- Step 3: `1`: exactly one finding, located at `` `commands/status.md:500` `` (DEV-008: `--check` runs once, so a hit is never counted twice). `reset` prints nothing.
- Step 4: `exit 2`; `FAIL (1 finding(s))` and a finding at `` `scripts/gen-platform-trees.py` `` saying `--check exited 2 without a verdict`; `- Run errors: 1`. `reset` prints nothing.
- Step 5: `All 6 platform-trees check assertions passed.`

**Status:** [x] Pass  [ ] Fail — **Notes:** agent run 2026-10-23 at 0b033a3: plan drift: step 3's report has 3 findings (stale `plugins/writ/` and `cursor/plugin/` copies of `status.md` plus the vendor hit), but the vendor hit is counted once (`1`). Step 1 `PASS` with the pass note; step 2 exit 1, one stale finding with the regenerate remedy; step 4 exit 2, finding at `scripts/gen-platform-trees.py` "--check exited 2 without a verdict", `- Run errors: 1`; step 5 `All 6 platform-trees check assertions passed.`

---
### Scenario 20: The driver is dev-only: denied by `is_shippable_script` in three byte-identical bodies

**Source:** Acceptance Criteria (AC-4.5) — Story 4; Business Rule 1; DEV-001
**Feature:** none
**Verification:** human — no recipe

**Preconditions:** setup block pasted.

**Steps:**
1. `grep -n 'gen-platform-trees' "$CL"/scripts/{install,update,unlink}.sh; pt -k test_dev_only`

**Expected Result:**
- One line per script (three in all, `unlink.sh` included per DEV-001), each inside `is_shippable_script`'s dev-only case beside `gen-claude-md.py`; `1 passed, 99 deselected …` (the three bodies compare byte-identical, the driver is denied, a shipped script such as `spec-status.py` is allowed). Scenario 21 confirms the installed `scripts/` has no copy.

**Status:** [x] Pass  [ ] Fail — **Notes:** agent run 2026-10-23 at 0b033a3: one line each at `install.sh:1001`, `update.sh:792`, `unlink.sh:162`, in the dev-only case beside `gen-claude-md.py`; `1 passed, 99 deselected`.

---

## Story 5: Install Evidence and Issue Closure

### Scenario 21: A fresh Cursor install from the clone carries the map in `.cursor/rules/writ.mdc`

**Source:** Acceptance Criteria (AC-5.1, AC-5.3) — Story 5; Contract item 8; State Catalog "Installed Cursor project"; AC-4.5 (no driver shipped); DEV-010
**Feature:** none
**Verification:** human — no recipe

**Preconditions:** setup block pasted. Outside any sandbox. The install reads the clone and writes only under `$W/proj-cursor`.

**Steps:**
1. `proj cursor; F="$W/proj-cursor/.cursor/rules/writ.mdc"; grep -c '^## Capability Map$' "$F"; names "$F"; ls "$W/proj-cursor/scripts" | grep -c 'gen-'; ls -d "$W"/proj-cursor/adapters 2>&1 | tail -1`

**Expected Result:**
- `📦 Using local writ: <$W>/clone` (the clone, not a network clone of upstream); `1` (exactly one map heading); the ten Cursor names ending `` `canvas-preview` `PlanMode` ``; `0` (no `gen-*.py` shipped: the driver and its siblings are dev-only); `No such file or directory` (no `adapters/` is installed; the map is what the installed agent reads).

**Status:** [x] Pass  [ ] Fail — **Notes:** agent run 2026-10-23 at 0b033a3: plan drift: `ls scripts | grep -c 'gen-'` prints `3` (`gen-claude-agents.py`, `gen-codex-agent-tomls.py`, `gen-skill.sh`), not `0`. A 304d63e install also gives 3, so the expectation was wrong when written; these ship by design (`/refresh-command` runs them), and `gen-platform-trees.py` and `gen-claude-md.py` are absent. Source line names the clone, one map heading, ten Cursor names ending `canvas-preview` `PlanMode`, no `adapters/`.

---
### Scenario 22: A fresh Claude Code install carries the map inside the `CLAUDE.md` Writ block, and its `Plan Mode` row names `EnterPlanMode`

**Source:** Acceptance Criteria (AC-5.1, AC-5.3) — Story 5; State Catalog "Installed Claude Code project"; DEV-010
**Feature:** none
**Verification:** human — no recipe

**Preconditions:** setup block pasted. Outside any sandbox.

**Steps:**
1. `proj claude; awk '/^<!-- writ:start -->$/{f=1} f; /^<!-- writ:end -->$/{exit}' "$W/proj-claude/CLAUDE.md" > "$W/cb"; grep -c '^## Capability Map$' "$W/cb"; grep '^| `Plan Mode`' "$W/cb" | cut -c1-80; names "$W/cb"; ls "$W/proj-claude/.claude"`

**Expected Result:**
- `📦 Using local writ: <$W>/clone`; `1`; the row begins `` | `Plan Mode` | `EnterPlanMode`; present the contract proposal as the plan; after ``; the eleven Claude Code names (with `` `Task({readonly:true})` `` second); `.claude/` holds `agents`, `commands`, `skills`, `system-instructions.md` and no `adapters`.

**Status:** [x] Pass  [ ] Fail — **Notes:** agent run 2026-10-23 at 0b033a3: source line names the clone; one map heading; `Plan Mode` row begins with `EnterPlanMode`; eleven names with `Task({readonly:true})` second; `.claude/` holds `agents`, `commands`, `skills`, `system-instructions.md`, no `adapters`.

---
### Scenario 23: A fresh Codex install carries the map inside the `AGENTS.md` Writ block with no `adapters/` mention, and the install evidence test passes

**Source:** Acceptance Criteria (AC-5.1, AC-5.2, AC-5.3) — Story 5; Business Rule 14; State Catalog "Installed Codex project"; DEV-010
**Feature:** none
**Verification:** human — no recipe

**Preconditions:** setup block pasted. Outside any sandbox.

**Steps:**
1. `proj codex; awk '/^<!-- writ:start -->$/{f=1} f; /^<!-- writ:end -->$/{exit}' "$W/proj-codex/AGENTS.md" > "$W/xb"; grep -c '^## Capability Map$' "$W/xb"; echo "adapters/: $(grep -c 'adapters/' "$W/xb")"; grep '^| `Plan Mode`' "$W/xb" | cut -c1-90; names "$W/xb"`
2. `(cd "$CL" && bash scripts/tests/test_install_platform_trees.sh | tail -1); git -C "$CL" status --short`

**Expected Result:**
- Step 1: `📦 Using local writ: <$W>/clone`; `1`; `adapters/: 0`; the row begins `` | `Plan Mode` | No agent-side mode: run discovery as a read-only conversation and say so; ``; the ten Codex names.
- Step 2: `All 8 install platform-trees assertions passed.` (three temp projects of its own, installed with `--no-commit`, DEV-010); status empty: the test wrote nothing into the clone.

**Status:** [x] Pass  [ ] Fail — **Notes:** agent run 2026-10-23 at 0b033a3: source line names the clone; one map heading; `adapters/: 0`; `Plan Mode` row begins "No agent-side mode: run discovery as a read-only conversation and say so;"; ten Codex names; `All 8 install platform-trees assertions passed.`; clone status empty.

---
### Scenario 24: The adapter-mappings issue is resolved on installed-file evidence, and no adapter Installation section sends a user to `adapters/`

**Source:** Acceptance Criteria (AC-5.4, AC-5.5) — Story 5; spec Origin (the issue this spec closes)
**Feature:** none
**Verification:** human — no recipe

**Preconditions:** setup block pasted.

**Steps:**
1. `I="$CL/.writ/issues/improvements/2026-10-21-adapter-mappings-never-reach-installed-projects.md"; grep -n 'spec_ref' "$I"; awk '/^## Resolution/,0' "$I" | grep -c '2026-10-22-generated-platform-trees\|\.cursor/rules/writ\.mdc\|CLAUDE\.md. Writ block\|AGENTS\.md. Writ block\|^2026-10-22'`
2. `for a in codex claude-code; do echo "$a: $(awk '/^## Installation/{f=1;next} f&&/^## /{f=0} f' "$CL/adapters/$a.md" | grep -ci 'read adapters/\|see adapters/\|adapters/.*for tool mapping')"; done`

**Expected Result:**
- Step 1: `> **spec_ref:** .writ/specs/2026-10-22-generated-platform-trees/spec.md`; the count is at least `4`: the Resolution names the spec, the three install paths (`.cursor/rules/writ.mdc`, the `CLAUDE.md` Writ block, the `AGENTS.md` Writ block), and opens with the date `2026-10-22`.
- Step 2: `codex: 0` and `claude-code: 0`: neither `## Installation` section tells an installed user to read an adapter file for tool mappings (AC-5.5 held without an edit; Story 5 recorded the audit).

**Status:** [x] Pass  [ ] Fail — **Notes:** agent run 2026-10-23 at 0b033a3: `spec_ref` line present; Resolution count `4`; `codex: 0`, `claude-code: 0`.

---
### Scenario 25: The spec's test file, the bash tests, and the repository quality gate pass on the clone

**Source:** Success Criteria (`uv run --python 3.9 pytest`, the bash tests, `bash scripts/eval.sh` with 0 findings); Acceptance Criteria (AC-4.4, AC-5.5) — Stories 4 and 5; Technical Concern "`check_prime_directive_sync` … passes by construction"
**Feature:** none
**Verification:** human — no recipe

**Preconditions:** setup block pasted; `reset` prints nothing. Outside any sandbox. About three minutes.

**Steps:**
1. `pt`
2. `(cd "$CL" && for t in scripts/tests/test_eval_platform_trees.sh scripts/tests/test_install_platform_trees.sh scripts/tests/test_eval_claude_md.sh scripts/tests/test_install_update_dev_scripts.sh; do bash "$t" >/dev/null 2>&1 && echo "ok $t" || echo "FAIL $t"; done)`
3. `(cd "$CL" && bash scripts/eval.sh > "$W/eval.out" 2>&1; echo "exit $?"); tail -1 "$W/eval.out"; R="$(ls -t "$CL"/.writ/state/eval-*.md | head -1)"; grep '^- Findings\|^- Run errors' "$R"; for c in platform-trees prime-directive-sync claude-md claude-agents codex-tomls; do printf '%s: ' "$c"; awk -v h="## $c" '$0==h{f=1;next} f&&NF{print;exit}' "$R"; done; reset`

**Expected Result:**
- Step 1: `100 passed in …`.
- Step 2: four `ok` lines, no `FAIL`.
- Step 3: `exit 0`; `Eval report: .writ/state/eval-<timestamp>.md`; `- Findings: 0` and `- Run errors: 0`; each of the five checks prints `PASS` (`prime-directive-sync` passes by construction now that `cursor/writ.mdc` is generated from `system-instructions.md`). Non-blocking leanness WARNINGs pre-date this spec and are not findings. `reset` prints nothing.

**Status:** [x] Pass  [ ] Fail — **Notes:** agent run 2026-10-23 at 0b033a3: `100 passed`; four `ok` lines; `eval.sh` exit 0, `- Findings: 0`, `- Run errors: 0`; platform-trees, prime-directive-sync, claude-md, claude-agents, codex-tomls all `PASS`; `reset` clean.

---
