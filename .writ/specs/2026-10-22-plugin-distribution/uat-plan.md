# UAT Plan: Plugin Distribution

> **Generated:** 2026-10-23
> **Spec:** `.writ/specs/2026-10-22-plugin-distribution/`
> **Stories Covered:** 5 of 5 completed
> **Total Scenarios:** 11
> **Verification recipe:** does not apply. Writ is markdown plus Python and bash scripts with no application to boot, so no `.writ/docs/app-verification.md` was drafted, saved, or bound (Step 1.3 asked nothing). Every scenario is `human — no recipe`.

## How to Use This Plan

1. Work through scenarios in order (they're grouped by story, ordered by priority)
2. For each scenario, follow the steps exactly as written
3. Mark Pass or Fail — add notes for any unexpected behavior
4. Scenarios marked Fail should be filed as issues or fed back to the spec
5. A feature passes UAT when all scenarios pass (or failures are accepted as known limitations)

**Conventions for this plan:**

- There is no app to boot and no recipe. Scenarios run shell commands against a read-only clone of the repository. Scenarios 2, 3, 5, and 9 also need a live Claude Code or Cursor session, and the maintainer judges the replies. These are the checks the lane could not run (V73, V76 to V79) or that need a person to judge.
- **Never run `install.sh` against the Writ repo, never use it as a marketplace source, and never point a helper at it.** `$REPO` is cloned from and nothing else. Create `$W` with `mktemp` under `$TMPDIR`, not under `~/Projects`: `~/Projects/CLAUDE.md` names the Writ persona and would leak into the probes.
- **Machine state.** Every plugin install uses `--scope local` from inside the scenario's project, so the declaration lands in `<project>/.claude/settings.local.json` and no scenario edits `~/.claude/settings.json`. (The README's `claude plugin install writ@writ` installs at user scope and is not run here.) Each installing scenario starts with `snap` and ends with its undo: `claude plugin uninstall writ@writ --scope local` and `claude plugin marketplace remove writ --scope local` (the `undo` helper runs both) for Claude Code, or `rm -rf ~/.cursor/plugins/local/writ` for Cursor, then `regdiff` against the snapshot. The only writes outside `$W` are Claude Code's own registry and cache entries, which `undo` reverses, and Scenario 5's `~/.cursor/plugins/local/writ`, which its last step removes. `~/.claude/plugins/cache/writ/` survives an uninstall and is swept 14 days later (V35). Deleting it sooner is optional.
- Run in `bash` on macOS (`sed -i ''`), outside any sandbox (the smoke test and install do `git init`). Paste this block once per shell, and stop if the first line does not print `W=/...`:

  ```bash
  W=$(mktemp -d "${TMPDIR:-/tmp}/writ-uat-plugin.XXXXXX") && cd "$W" && W=$PWD && echo "W=$W"
  REPO=/Users/asellke/Projects/writ          # read only: cloned from, never edited, never a marketplace source
  CL="$W/writ"; git clone -q "$REPO" "$CL"   # committed tree of the current branch, generated plugin trees included
  inW() { case "$PWD/" in "$W"/*) ;; *) echo "refusing: $PWD is outside $W" >&2; return 1;; esac; }
  gen() { inW && (cd "$CL" && python3 scripts/gen-platform-trees.py "$@"; echo "exit $?"); }
  pt() { inW && (cd "$CL" && uv run --python 3.9 pytest "$@" -q 2>&1 | tail -1); }
  # reset: undo every edit in the clone; prints nothing when clean
  reset() { inW && git -C "$CL" checkout -q -- . && git -C "$CL" clean -qfd && git -C "$CL" status --short; }
  # newproj <name>: a fresh git repo at $W/proj-<name>, made the working directory; never reuses one
  newproj() { inW || return 1; P="$W/proj-$1"; [ ! -e "$P" ] || { echo "exists: $P" >&2; return 1; }; mkdir -p "$P" && git -C "$P" init -q -b main && cd "$P" && echo "P=$P"; }
  R=~/.claude/plugins
  # snap: copy both registries, hash ~/.claude/settings.json, print the writ entries already there (expect 0, then 0)
  snap() { inW && cp "$R/installed_plugins.json" "$W/installed.before.json" && cp "$R/known_marketplaces.json" "$W/known.before.json" && shasum -a 256 ~/.claude/settings.json > "$W/settings.sha"; grep -c '"writ@' "$W/installed.before.json"; grep -c '"writ"' "$W/known.before.json"; }
  regdiff() { diff "$W/installed.before.json" "$R/installed_plugins.json" && echo "installed_plugins.json: same as snapshot"; diff "$W/known.before.json" "$R/known_marketplaces.json" && echo "known_marketplaces.json: same as snapshot"; shasum -a 256 -c "$W/settings.sha"; }
  # undo: uninstall writ@writ and remove the writ marketplace from $P's local scope, then regdiff
  undo() { cd "$P" && inW || return 1; claude plugin uninstall writ@writ --scope local; claude plugin marketplace remove writ --scope local; regdiff; }
  # ipath: scope, version, in-place folder (or -), and install path of writ@writ as this project sees it
  ipath() { claude plugin list --json | python3 -c 'import json,sys; [print(p.get("scope"), p.get("version"), p.get("readFromFolder", "-"), p.get("installPath")) for p in json.load(sys.stdin) if p["id"] == "writ@writ"]'; }
  # P2: Story 1's discriminating Prime Directive probe (reconstructed from V67 to V69; the evidence log with the exact wording was not committed)
  P2='Quote word for word the first bullet under the heading "Hard Constraints" in your instructions. On the next line print SOURCE followed by the name of the heading that "Hard Constraints" sits under. If your instructions have no "Hard Constraints" heading, print NONE and then SOURCE NONE.'
  ```

- Scripted expected output (smoke test, pytest, scaffold, `--check`, validate) was observed on 2026-10-23 against `b2d9ea7` (branch `phase/14-front-door-and-distribution`, Claude Code 2.1.309, `VERSION` 0.43.0). Live-session expected output comes from § Verification Record (V67 to V85) and Story 5's What Was Built, not from a run made for this plan. Story commits: Story 1 `e907b67`, Story 2 `bc7e964`, Story 3 `1f076f9`, Story 4 `88c3655`, Story 5 `0e4085e`. Line numbers hold for `b2d9ea7`. When done: `rm -rf "$W"`.
- **Known limitations (Medium drift, flagged for review).** Each is named in the scenario that exposes it: DEV-005, Writ-source scripts resolve their root to the plugin (Scenario 3); DEV-006, no `.writ/docs/` reference docs in a plugin-only project (Scenarios 3 and 9); DEV-017, Cursor `agents/` files lack the frontmatter Cursor requires (Scenario 5); DEV-022, the README keeps `### Cursor (plugin)` when `cursor-plugin` fails (Scenario 8). Small entries that change what a step shows: DEV-009 (Scenarios 4, 9), DEV-011 and DEV-012 (Scenario 6), DEV-021 (Scenario 8).
- **Record edits after a live pass.** Scenarios 3 and 5 end with the record edit to make. Some tests pin the pre-UAT state, and each scenario names the ones that will fail after its edit.

## Coverage Summary

| Story | Status | Scenarios | Source Breakdown |
|-------|--------|-----------|-----------------|
| Story 1: Verify Both Plugin Formats and Decide the Layout | ✅ Covered | 2 | AC: 2, Errors: 0, Shadow: 0, Edge: 0 (Upstream error folded into 1; Moment of truth into 2) |
| Story 2: Claude Code Plugin | ✅ Covered | 2 | AC: 2, Errors: 0, Shadow: 0, Edge: 0 (Entry and Happy path folded into 3) |
| Story 3: Cursor Plugin | ✅ Covered | 1 | AC: 1, Errors: 0, Shadow: 0, Edge: 0 |
| Story 4: Scaffold Script, `/initialize` Step 0, and ADR-031 | ✅ Covered | 2 | AC: 2, Errors: 0, Shadow: 0, Edge: 0 (Empty input and the `.gitignore` edge case folded into 6) |
| Story 5: Smoke Test Across Five Targets, README Install Order, and Live-Run Evidence | ✅ Covered | 4 | AC: 3, Errors: 0, Shadow: 1, Edge: 0 (Happy path folded into 8; both-installs edge case into 9) |

The technical spec's Error & Rescue Map is "Not required" (no runtime data flow), so there are no error scenarios. The smoke test's per-target checks cover the install-time failure surface. No pending stories: all five are Completed ✅.

---

## Story 1: Verify Both Plugin Formats and Decide the Layout

### Scenario 1: The Verification Record has a dated, sourced row per claim, and only the rows the spec leaves open are unverified

**Source:** Acceptance Criteria (AC-1.1, AC-1.3, AC-1.5) — Story 1; Shadow Path "Upstream error" (technical spec)
**Feature:** none
**Verification:** human — no recipe

**Preconditions:** setup block pasted.

**Steps:**
1. `TS="$CL/.writ/specs/2026-10-22-plugin-distribution/sub-specs/technical-spec.md"; awk '/^## Verification Record/{f=1} f&&/^## Relative Path/{exit} f' "$TS" | grep -E '^\| V[0-9]+ ' | awk -F'|' '{s=$(NF-1); gsub(/^ +| +$/,"",s); print s}' | sort | uniq -c`
2. `grep -E '^\| V[0-9]+ ' "$TS" | grep -E '\| unverified ' | awk '{print $2}' | tr '\n' ' '; echo`
3. `sed -n '/^### Upstream changes since 2026-10-22/,/^## Relative Path/p' "$TS" | grep -c '^- '; grep -n '^### Decision (Story 1' "$TS"`
4. `pt scripts/tests/test_plugin_distribution.py -k "TestVerificationRecord or TestStory1Record"`

**Expected Result:**
- Step 1: `77 verified 2026-10-23`, `3 unverified 2026-10-23`, `5 unverified 2026-10-23 (pending UAT)`: 85 rows.
- Step 2: `V66 V73 V74 V75 V76 V77 V78 V79`. V73 is the GitHub install (Scenario 3), V76 to V79 are the Cursor live checks (Scenario 5), V66 is the agent keys no live run could show, and V75 is the layout-A exception that was never run. V74 (`validate .` on the repository root) still reads unverified, although Story 2's What Was Built records exit 0 and Scenario 4 shows it passing. That is a record gap, not a failure of this scenario.
- Step 3: `7` upstream-change bullets, each naming the row re-read (V26, V05, V25, V38, V37, V36, V48). Two decision headings: line 205 `Layout B` and line 265 `carrier 2, the forced output style`.
- Step 4: `7 passed, 108 deselected …`. These tests check the header, the status grammar, `https://` sources, unique IDs, that every `Rests on:` line cites verified rows only, the live and Cursor rows, and the path inventory.

**Status:** [x] Pass  [ ] Fail — **Notes:** agent run 2026-10-23 at 0b033a3: 77 verified / 3 unverified / 5 pending-UAT (85 rows); unverified V66 V73-V79; 7 upstream bullets (V26 V05 V25 V38 V37 V36 V48); decisions at lines 205 and 265; 7 passed, 108 deselected

---

### Scenario 2: In a plugin session, the forced output style carries the Prime Directive, and without the plugin the session has none

**Source:** Acceptance Criteria (AC-1.2 probe, AC-1.5 carrier decision) — Story 1; AC-2.3 — Story 2; Experience Design "Moment of truth"
**Feature:** none
**Verification:** human — no recipe

**Preconditions:** setup block pasted; `claude --version` recorded; no Writ plugin installed in any scope.

**Steps:**
1. `newproj probe && snap`
2. Baseline, before any install: `claude -p --tools "" "$P2"`
3. `claude plugin marketplace add "$CL" --scope local && claude plugin install writ@writ --scope local && ipath`
4. `claude -p --tools "" "$P2"`, then `claude -p --tools "" "Name your persona in one word."`
5. `undo` (runs `claude plugin uninstall writ@writ --scope local` and `claude plugin marketplace remove writ --scope local` in `$P`, then `regdiff`)

**Expected Result:**
- Step 1: `P=$W/proj-probe`, then `0` and `0`. If either count is not 0, a Writ install already exists: stop.
- Step 2: `NONE` and `SOURCE NONE` (V67).
- Step 3: `✔ Successfully added marketplace: writ (declared in local settings)`, `✔ Successfully installed plugin: writ@writ (scope: local)`, then `local 0.43.0 $W/writ/plugins/writ …` (loaded in place from the clone, V57, V81).
- Step 4: the reply quotes `**Never reverse a position without new evidence.** If the user pushes back and you still believe you're right, say so. Reverse only on new information.` (a leading `- ` is fine), then `SOURCE Prime Directive` (V69, V85). The persona reply is `Writ` (V69).
- Step 5: both commands exit 0; `installed_plugins.json: same as snapshot`; `known_marketplaces.json: same as snapshot`, or a diff confined to another marketplace's `lastUpdated` (Claude Code's own refresh, V71); `/Users/asellke/.claude/settings.json: OK`.
- If step 4 prints `NONE`, check for another enabled plugin that forces an output style before failing the scenario. The first plugin loaded wins (V42): `grep -rl 'force-for-plugin: true' ~/.claude/plugins/cache 2>/dev/null | grep -v '/cache/writ/'`.

**Implementation Reference:** Story 2 — `plugins/writ/output-styles/writ.md` (`force-for-plugin: true`, `keep-coding-instructions: true`, body = `system-instructions.md`).

**Status:** [x] Pass  [ ] Fail — **Notes:** full rerun 2026-10-23 at 73b31ed in a logged-in shell, Claude Code 2.1.310, with the prompt placed before `--tools ""`: snap 0/0; step 2 `NONE` / `SOURCE NONE`; step 3 add and install lines as expected, ipath `local 0.43.0 $W/writ/plugins/writ <cache>/writ/writ/0.43.0`; step 4 quotes the "Never reverse a position without new evidence" bullet with a leading `- `, then `SOURCE Prime Directive`; persona `Writ.`; step 5 both exit 0, both registries same as snapshot, settings.json OK. Earlier blocked run (0b033a3): Steps 1, 3, 5 ran: snap 0/0; add and install lines as expected; ipath `local 0.43.0 $W/writ/plugins/writ <cache>/writ/writ/0.43.0`; undo exit 0, both registries same as snapshot, settings.json OK. Supplementary: `--debug` log with the plugin installed shows "Using forced plugin output style: writ:writ", after undo none. plan drift: `--tools` is variadic and swallows "$P2", so steps 2 and 4 as written print "Input must be provided…"; the prompt must come before `--tools ""`.

---

## Story 2: Claude Code Plugin

### Scenario 3: After the phase merges, `marketplace add sellke/writ` and `install writ@writ` give a working plugin from a cache copy

**Source:** Acceptance Criteria (AC-2.1) — Story 2 user story; Rule 11 and V73 (pending UAT); Experience Design "Entry" and "Happy path"; State Catalog "plugin installed, project without `.writ/`" and "command calls a script"
**Feature:** none
**Verification:** human — no recipe

**Preconditions:**
- The phase is merged to `main` on `sellke/writ`: `gh api repos/sellke/writ/contents/.claude-plugin/marketplace.json --jq .path` prints `.claude-plugin/marketplace.json`. Before the merge it returns a 404; run Scenario 9 instead.
- Setup block pasted; any earlier scenario's `undo` has run.

**Steps:**
1. `newproj github && snap`
2. `claude plugin marketplace add sellke/writ --scope local && claude plugin install writ@writ --scope local && ipath; ls scripts`
3. Run `claude` in `$P` and accept the folder-trust prompt. Type `/writ:initialize` and approve its one Bash call. When the discovery questions appear, press Esc.
4. In the same session, type `/writ:writ "add a health endpoint"`. When the proposed route appears, press Esc, then `/exit`.
5. `find .writ -type d | sort; cat .gitignore; ls -A .writ/docs | wc -l`
6. Expose DEV-005, read only: `IP=$(claude plugin list --json | python3 -c 'import json,sys; print([p["installPath"] for p in json.load(sys.stdin) if p["id"] == "writ@writ"][0])'); grep -n '^ROOT = ' "$IP/scripts/gen-claude-agents.py"; grep -n '^PROJECT_ROOT=' "$IP/scripts/gen-skill.sh"`
7. `cd "$P" && claude plugin uninstall writ@writ --scope local && claude plugin marketplace remove writ --scope local; regdiff`

**Expected Result:**
- Step 2: `✔ Successfully added marketplace: writ (declared in local settings)`, `✔ Successfully installed plugin: writ@writ (scope: local)`. `ipath` prints `local <VERSION on main>`, no in-place folder (`-`), and an install path under `~/.claude/plugins/cache/writ/writ/`: a cache copy (V34), not a checkout. `ls: scripts: No such file or directory`.
- Step 3: the tool call reads `python3 <the cache path>/scripts/scaffold-writ.py scaffold`. Its output is `pass`, eleven `created .writ/…` lines, `added .gitignore entry .writ/state/`, `added .gitignore entry .writ-lanes-*/`, and `scaffold-writ: pass (11 created, 0 existing)`. The session then says the project is greenfield and asks the technical-discovery questions (V82).
- Step 4: a Restatement block whose Goal says the project serves an HTTP health endpoint, then `Proposed: /writ:prototype (Recommended)`, with every route option spelled `/writ:<command>` (V83).
- Step 5: `.writ`, `.writ/issues`, and the eleven directories; `.gitignore` reads `# Writ ephemeral state`, `.writ/state/`, `.writ-lanes-*/`; `0`. **Known limitation DEV-006:** the plugin ships none of the `.writ/docs/` format docs that `install.sh` copies, so commands that cite `.writ/docs/<name>.md` find nothing.
- Step 6: `37:ROOT = pathlib.Path(__file__).resolve().parents[1]` and `24:PROJECT_ROOT="$(cd "$SCRIPT_DIR/.." && pwd)"`. Both roots resolve inside `$IP`, the plugin copy. **Known limitation DEV-005:** in a plugin project, do not run `/writ:new-skill` or the agent-regeneration steps of `/writ:refresh-command`, because they read, and would write, inside the plugin.
- Step 7: as Scenario 2 step 5.
- **Record edit on pass:** in `technical-spec.md` § Verification Record, set V73's Observed to the step 2 add and install lines, the cache path, and the step 3 summary line, and set its Status to `verified <run date>`. In `adapters/claude-code.md` § Installation → Plugin → Install, replace the sentence "The install from `sellke/writ` itself has not run yet: …" with the run date, the Claude Code version, and the cache observation, keeping the loading.md URL. If `claude --version` is not 2.1.309, `TestStory1Record::test_live_rows_name_the_version_and_the_observation` fails, because it pins every live row's Platform to `Claude Code 2.1.309`. Update that pin in the same commit.

**Status:** [ ] Pass  [ ] Fail — **Notes:** blocked: phase not merged

---

### Scenario 4: The generated plugin validates, matches its sources, and names scripts and commands the plugin way

**Source:** Acceptance Criteria (AC-2.2, AC-2.3, AC-2.4) — Story 2; State Catalog "`claude plugin validate .`"
**Feature:** none
**Verification:** human — no recipe

**Preconditions:** setup block pasted; `claude` on `PATH`.

**Steps:**
1. `inW && (cd "$CL" && claude plugin validate plugins/writ | tail -1; claude plugin validate . | tail -1)`
2. `gen --check`
3. ``grep -rhoE '`/(create-spec|prototype|initialize|writ)`' "$CL/plugins/writ/commands" | wc -l; grep -rhoE '`/writ:(create-spec|prototype|initialize|writ)`' "$CL/plugins/writ/commands" | wc -l; grep -rEoh '\b(python3|bash) scripts/[a-z0-9_-]+\.(py|sh)' "$CL/plugins/writ/commands" "$CL/plugins/writ/skills" | sort | uniq -c``
4. `ls "$CL/plugins/writ/scripts" | grep -cE '^(install|update|uninstall|eval|gen-platform-trees)\.'; diff <(awk 'f; /^---$/{n++; if(n==2) f=1}' "$CL/plugins/writ/output-styles/writ.md") <(awk 'f; /^---$/{n++; if(n==2) f=1}' "$CL/system-instructions.md") && echo carrier-body-equal`
5. `sed -i '' 's/Reverse only on new information\./Reverse on new information./' "$CL/system-instructions.md"; gen --check; reset`

**Expected Result:**
- Step 1: `✔ Validation passed with warnings`, where the warnings are the eight prompt-template docs in `agents/` with no frontmatter (DEV-009; the manifest's `agents` list keeps them from loading). Then `✔ Validation passed`.
- Step 2: `pass`, `gen-platform-trees: pass (0 stale, 0 missing, 0 orphan, 0 unmapped, 0 vendor)`, `exit 0`.
- Step 3: `0` bare references and `98` namespaced ones. Then exactly `4 bash scripts/eval.sh`, a dev-only script named in prose that addresses the Writ repo (DEV-008), and `1 bash scripts/gen-skill.sh`, which sits in `new-skill.md`'s YAML frontmatter, where token classes do not reach. No other bare script call appears.
- Step 4: `0` (no dev-only script ships), then `carrier-body-equal`.
- Step 5: `fail`, five `reason: stale …` lines (`cursor/writ.mdc`, `plugins/writ/output-styles/writ.md`, `plugins/writ/system-instructions.md`, `cursor/plugin/rules/writ.mdc`, `cursor/plugin/system-instructions.md`), `gen-platform-trees: fail (5 stale, 0 missing, 0 orphan, 0 unmapped, 0 vendor)`, `exit 1`. `reset` prints nothing.

**Status:** [x] Pass  [ ] Fail — **Notes:** agent run 2026-10-23 at 0b033a3: plan drift: `validate plugins/writ` also prints one plugin-directory warning (ICON_MISSING, "do not change the result") besides the eight no-frontmatter `agents/` warnings (DEV-009). Otherwise as expected: "Validation passed with warnings" / "Validation passed"; gen --check pass 0/0/0/0/0 exit 0; 0 bare, 98 namespaced, `4 bash scripts/eval.sh` + `1 bash scripts/gen-skill.sh`; 0 dev-only scripts, carrier-body-equal; after the edit fail with the five named stale files, exit 1; reset printed nothing

---

## Story 3: Cursor Plugin

### Scenario 5: The Cursor local plugin loads its rule and commands, and a script-calling command runs from the project's `scripts/`

**Source:** Acceptance Criteria (AC-3.5 protocol; AC-3.2, AC-3.3, AC-3.4) — Story 3; State Catalog "Cursor local plugin"; V76 to V79 (pending UAT)
**Feature:** none
**Verification:** human — no recipe

**Preconditions:**
- Cursor installed; record its version (Cursor → About Cursor). On Enterprise, Allow Local Plugin Imports is on (V50).
- `ls -A ~/.cursor/plugins/local/` shows no `writ`. If it does, stop, because an earlier copy would mix with this one.
- Setup block pasted.

**Steps:**
1. `gen --check | tail -2; cmp "$CL/cursor/plugin/rules/writ.mdc" "$CL/cursor/writ.mdc" && test ! -e "$CL/cursor/plugin/scripts" && echo layout-ok`
2. `newproj cursor && bash "$CL/scripts/install.sh" --no-commit | grep -F 'Using local writ' && rm -rf .cursor && test -f scripts/quality-config-audit.py && test ! -e .cursor && echo sample-ok`. The project keeps install.sh's `scripts/`, and every rule, command, agent, and skill the session shows comes from the plugin.
3. `snap; ls -A ~/.cursor/plugins/local/ > "$W/cursor-local.before" 2>/dev/null; test ! -e ~/.cursor/plugins/local/writ && mkdir -p ~/.cursor/plugins/local/writ && cp -R "$CL/cursor/plugin/." ~/.cursor/plugins/local/writ/ && ls -A ~/.cursor/plugins/local/writ`
4. Restart Cursor or run **Developer: Reload Window**. Open `$P` (File → Open Folder, the path step 2 printed). Open **Customize** and note the `writ` plugin and the rules, commands, skills, and agents it lists.
5. Start a new chat in `$P`:
   a. Check that the rules list shows `writ.mdc`. Send the P2 prompt (`echo "$P2"` prints it).
   b. Type `/` and note `/writ`, the other commands, and whether `/_preamble` is listed.
   c. Run `/status`.
6. Optional: run `bash "$CL/scripts/install.sh" --no-commit` in `$P` again, reload, and note which `/status` and which `writ.mdc` Cursor uses, the plugin's or the project's `.cursor/` copy.
7. Undo: `rm -rf ~/.cursor/plugins/local/writ`, reload Cursor, then `diff "$W/cursor-local.before" <(ls -A ~/.cursor/plugins/local/) && echo cursor-local-restored; regdiff`

**Expected Result:**
- Step 1: `pass` summary, `exit 0`, `layout-ok`: the rule is byte-equal, and the layout has no `scripts/`.
- Step 2: `P=…`, `📦 Using local writ: $W/writ`, `sample-ok`.
- Step 3: `0`, `0`; listing `.cursor-plugin agents commands rules skills system-instructions.md`.
- Step 4: Customize lists `writ` with the rule `writ.mdc`, the commands from `commands/` (34 files), and 16 skills. **Known limitation DEV-017:** the eight `agents/*.md` have no YAML frontmatter, which Cursor requires (V80). Cursor may omit them or show them as broken. Record what it shows; it decides the open review item before a marketplace submission.
- Step 5a (V76): `writ.mdc` is listed. The reply quotes the first Hard Constraints bullet and `SOURCE Prime Directive`.
- Step 5b (V77): `/writ` and the other commands are listed.
- Step 5c (V78): the agent runs `python3 scripts/quality-config-audit.py check --project .` from the project root, and the script prints a JSON report with a `verdict` field (exit 0). `can't open file` or exit 2 fails this look-for.
- Step 7: `cursor-local-restored`, then the registry lines as in Scenario 2 step 5. Cursor writes neither registry.
- **Record these fields:** Cursor version: ___; Rules list result (is `writ.mdc` listed; is the Prime Directive visible): ___; Commands seen (`/writ`; others; `/_preamble`): ___; Script call result (command, script path, exit code): ___; Agents shown (DEV-017): ___; Result (`pass`, or `fail` with the failing check named): ___
- **Record edit on pass** (5a to 5c all hold):
  1. `adapters/cursor.md` § Plugin table: in rows V76, V77, and V78, change Status `unverified 2026-10-23 (pending UAT)` to `verified <run date>`, set Read to `<run date>`, and append `(Cursor <version>)` to the Claim. In the `/_preamble` and agents rows (Record `—`), restate the Claim as what the run showed, with Status `verified <run date>` and Read `<run date>`. The both-copies row stays pending unless step 6 ran. V79 stays pending (no `${CURSOR_PLUGIN_ROOT}` command body was tried).
  2. `technical-spec.md` § Verification Record, rows V76 to V78: set Platform & version to `Cursor <version>`, Observed to the transcript line or the Customize listing, and Status to `verified <run date>`.
  3. `scripts/tests/fixtures/plugin-smoke-results.txt`: change `cursor-uat pending` to `cursor-uat run`.
  4. Two tests pin the pre-UAT state and fail after edits 1 and 2:
     - `TestStory1Record::test_cursor_live_rows_are_pending_uat` expects every `Cursor (no session in lane)` row to be pending, plus the Observed text "nothing written to `~/.cursor/plugins/local/`", which leaves with V76.
     - `TestCursorAdapterPlugin::test_claims_carry_status_source_and_date` pins V76 to V79 to pending UAT.

     Narrow both to V79 in the same commit; then `pt scripts/tests/test_plugin_distribution.py` passes. The README order does not change. `### Cursor (plugin)` moves first only on `cursor-plugin pass` with `cursor-uat run`, and the target reads `unverifiable` while the layout has no `scripts/` (DEV-021).
- **Record edit on fail:** in both files, each failing row among V76 to V78 reads `unverified <run date>`, with no `(pending UAT)`. A sentence above the adapter table names the failing check and what the run showed, and the record's Observed names the failing check. Passing rows flip as on pass. The fixture still gets `cursor-uat run`, and the same two tests need the same narrowing. The README stays as it is.

**Status:** [ ] Pass  [ ] Fail — **Notes:**

---

## Story 4: Scaffold Script, `/initialize` Step 0, and ADR-031

### Scenario 6: `scaffold-writ.py` builds the tree in an empty directory, a second run creates nothing, and `/initialize` runs it as Step 0

**Source:** Acceptance Criteria (AC-4.1, AC-4.2, AC-4.3, AC-4.4) — Story 4; Shadow Path "Empty input"; Edge Case "`.gitignore` already has `.writ/state/` → scaffold adds nothing"
**Feature:** none
**Verification:** human — no recipe

**Preconditions:** setup block pasted.

**Steps:**
1. `inW && mkdir "$W/empty" && cd "$W/empty" && python3 "$CL/scripts/scaffold-writ.py" scaffold --check; echo "exit $?"; ls -A | wc -l`
2. `python3 "$CL/scripts/scaffold-writ.py" scaffold; echo "exit $?"; cat .gitignore; shasum .gitignore > "$W/gi.sha"`
3. `python3 "$CL/scripts/scaffold-writ.py" scaffold; echo "exit $?"; shasum -c "$W/gi.sha"; find . -type f`
4. `inW && mkdir "$W/pre" && cd "$W/pre" && printf '.writ/state\n' > .gitignore && python3 "$CL/scripts/scaffold-writ.py" scaffold | tail -2; cat .gitignore`
5. `python3 "$CL/scripts/scaffold-writ.py" > /dev/null; echo "exit $?"`
6. `grep -n 'scaffold-writ.py scaffold' "$CL/commands/initialize.md" "$CL/plugins/writ/commands/initialize.md" "$CL/cursor/plugin/commands/initialize.md"; grep -c 'exists from installation' "$CL/commands/initialize.md"; grep -n '^### Step 0\|^### Detection Logic' "$CL/commands/initialize.md"`

**Expected Result:**
- Step 1: `fail`; eleven `reason: missing .writ/…` lines; `reason: missing .gitignore entry .writ/state/`; `reason: missing .gitignore entry .writ-lanes-*/`; `scaffold-writ: fail (13 missing)`. The count includes the two entries (DEV-012). Then `exit 1` and `0`: nothing was written.
- Step 2: `pass`; `created` lines for `.writ/specs`, `product`, `research`, `decision-records`, `docs`, `knowledge`, `state`, `issues/bugs`, `issues/features`, `issues/improvements`, `issues/goals`; two `added .gitignore entry` lines (DEV-011); `scaffold-writ: pass (11 created, 0 existing)`; `exit 0`. `.gitignore` reads `# Writ ephemeral state`, `.writ/state/`, `.writ-lanes-*/`.
- Step 3: `pass`, `scaffold-writ: pass (0 created, 11 existing)`, `exit 0`, `.gitignore: OK`, and `./.gitignore` is the only file.
- Step 4: `added .gitignore entry .writ-lanes-*/`, `scaffold-writ: pass (11 created, 0 existing)`. `.gitignore` keeps one `.writ/state` line, followed by a blank line, `# Writ ephemeral state`, and `.writ-lanes-*/`. `.writ/state/` is not appended again.
- Step 5: usage on stderr, `exit 2`.
- Step 6: line 22 in each file. The source and Cursor copies read `python3 scripts/scaffold-writ.py scaffold`; the Claude plugin copy reads `python3 ${CLAUDE_PLUGIN_ROOT}/scripts/scaffold-writ.py scaffold`. Then `0`, and `### Step 0: Scaffold .writ/` sits directly above `### Detection Logic`. Scenarios 3 and 9 show Step 0 running live, and Scenario 10 covers the installers' matching bash list.

**Status:** [x] Pass  [ ] Fail — **Notes:** agent run 2026-10-23 at 0b033a3: plan drift: step 6 finds the Step 0 line at line 21 in `commands/initialize.md` (also 21 at b2d9ea7) and line 22 in the plugin and Cursor copies, not 22 in all three. Otherwise as expected: --check fail (13 missing, DEV-012) exit 1, dir empty; scaffold 11 created + two .gitignore entries (DEV-011) exit 0; rerun 0 created / 11 existing, .gitignore: OK, only file; pre-seeded `.writ/state` kept once, only `.writ-lanes-*/` added; no args usage exit 2; plugin copy uses `${CLAUDE_PLUGIN_ROOT}`; 0 "exists from installation"; Step 0 (19) directly above Detection Logic (27)

---

### Scenario 7: ADR-031 and the closed script-install-location issue record the decision as built

**Source:** Acceptance Criteria (AC-4.5) — Story 4; Contract item 5
**Feature:** none
**Verification:** human — no recipe

**Preconditions:** setup block pasted.

**Steps:**
1. `A="$CL/.writ/decision-records/adr-031-script-location.md"; sed -n '1,8p' "$A"; grep -n '^## \|^### ' "$A"`
2. `grep -n 'Superseded in part by' "$CL/.writ/decision-records/adr-029-agent-cli-contract.md"`
3. `I="$CL/.writ/issues/improvements/2026-10-12-script-install-location.md"; grep -n 'spec_ref\|^## Resolution' "$I"; sed -n '/^## Resolution/,$p' "$I"`
4. `grep -n 'DEV-005\|DEV-006' "$A"`

**Expected Result:**
- Step 1: Date `2026-10-23`, Status `Accepted`, and `Supersedes in part:` ADR-029's Consequences bullet "Scripts install into the project-root `scripts/` folder." The sections are Decision (with `### Shared-name rule` and `### The .writ/ scaffold`), Context and Problem Statement, Decision Drivers, Considered Options A to D (A chosen), Decision Outcome, Consequences, Implementation Notes, Evidence, and References.
- Step 2: line 4, `> **Superseded in part by:** [ADR-031](adr-031-script-location.md) (2026-10-23): …`.
- Step 3: `spec_ref` names `.writ/specs/2026-10-22-plugin-distribution/spec.md` (line 7) and `## Resolution` is at line 42. The Resolution states three points:
  - `install.sh` projects keep `scripts/`, and the Claude Code plugin runs `${CLAUDE_PLUGIN_ROOT}/scripts/<name>`.
  - A same-named project file keeps today's behavior: no baseline, kept as modified, overwritten by `--force`.
  - A plugin command never runs that project file.
- Step 4: two Consequences bullets record DEV-005 and DEV-006 as follow-ups.
- Judge: the decision matches what Scenarios 3 and 9 show, with the plugin command naming the plugin's own script path.

**Status:** [x] Pass  [ ] Fail — **Notes:** agent run 2026-10-23 at 0b033a3: plan drift: ADR-029 "Superseded in part by" is at line 5 (also 5 at b2d9ea7), not line 4; step 4 also matches a References line (144) besides the two Consequences bullets. Otherwise as expected: ADR-031 Date 2026-10-23, Accepted, supersedes ADR-029 scripts/ bullet; sections and Options A-D (A chosen) as listed; issue spec_ref line 7, Resolution line 42 stating the three points; DEV-005 and DEV-006 Consequences bullets at 110-111. Judge: plugin `initialize.md` names `${CLAUDE_PLUGIN_ROOT}/scripts/scaffold-writ.py` (Scenario 6); the live Step 0 call in Scenarios 3 and 9 was not observed

---

## Story 5: Smoke Test Across Five Targets, README Install Order, and Live-Run Evidence

### Scenario 8: The smoke test passes four targets, reports `cursor-plugin` unverifiable, and its recorded results set the README order

**Source:** Acceptance Criteria (AC-5.1, AC-5.2, AC-5.3, AC-5.4) — Story 5; Shadow Path "Happy path"; State Catalog "README install section"
**Feature:** none
**Verification:** human — no recipe

**Preconditions:** setup block pasted; `claude` on `PATH`; outside any sandbox (each run takes about 20 seconds).

**Steps:**
1. `inW && (cd "$CL" && bash scripts/tests/test_plugin_smoke.sh > "$W/smoke.out" 2> "$W/smoke.err"; echo "exit $?"); wc -l < "$W/smoke.out"; grep -E '^[a-z-]+ (pass|fail|unverifiable)$' "$W/smoke.out"; grep unverifiable "$W/smoke.out"; grep -c '^self-test: .* ok$' "$W/smoke.err"`
2. `F="$CL/scripts/tests/fixtures/plugin-smoke-results.txt"; diff <(grep -E '^[a-z-]+ (pass|fail|unverifiable)$' "$W/smoke.out") <(grep -Ev '^#|^cursor-uat ' "$F") && echo fixture-matches; grep -E '^cursor-uat|^# run date|^# claude' "$F"`
3. `awk '/^## Quick Start/{f=1;next} f&&/^## /{exit} f&&/^### /' "$CL/README.md"; grep -c 'local install; marketplace listing pending' "$CL/README.md"`
4. `pt scripts/tests/test_plugin_distribution.py -k readme_install_order`
5. `sed -i '' 's/^claude-plugin pass$/claude-plugin unverifiable/' "$F"; inW && (cd "$CL" && uv run --python 3.9 pytest scripts/tests/test_plugin_distribution.py -q -k readme_install_order 2>&1 | grep '^E .*AssertionError'); reset`
6. `sed -i '' 's/^cursor-plugin unverifiable$/cursor-plugin fail/' "$F"; pt scripts/tests/test_plugin_distribution.py -k readme_install_order; reset`
7. `inW && (cd "$CL" && bash scripts/tests/test_plugin_smoke.sh --record --no-self-test > /dev/null; echo "exit $?"); git -C "$CL" diff -U0 -- "$F" | grep '^[-+][^-+]'; reset`

**Expected Result:**
- Step 1: `exit 0` and `33` lines: 28 `<target> <check> <result>` lines (`install`, `commands`, `script-run`, `instructions`, `scaffold`, `scaffold-check` for the three `install.sh` targets; `commands`, `script-run`, `instructions`, `scaffold`, `validate`, `validate-marketplace` for `claude-plugin`; four for `cursor-plugin`), then five summaries: `cursor pass`, `claude pass`, `codex pass`, `claude-plugin pass`, `cursor-plugin unverifiable`. The unverifiable lines are `cursor-plugin script-run unverifiable (no cursor session)` and `cursor-plugin unverifiable`: the layout has no plugin-root `scripts/`, so that check cannot pass without a session (DEV-021). Then `8` self-tests.
- Step 2: `fixture-matches`; `# run date: 2026-10-23`, `# claude --version: 2.1.309 (Claude Code)`, `cursor-uat pending`.
- Step 3: in order, `### What /writ routes to` (backticked), `### Claude Code (plugin)`, `### Cursor (one-line install)`, `### Updating`, `### Cursor (plugin)`, `### Claude Code (one-line install)`, `### Codex CLI (one-line install)`; then `1`. The Claude plugin comes first because the fixture reads `claude-plugin pass`. The Cursor plugin follows the Cursor `install.sh` section because the fixture reads `cursor-plugin unverifiable` and `cursor-uat pending`.
- Step 4: `1 passed, 114 deselected …`. The test reads the committed fixture, not a live run, so the README follows the last recorded run.
- Step 5: `E   AssertionError: claude-plugin reads unverifiable, so README lists no Claude Code plugin`. `unverifiable` never counts as a pass. `reset` prints nothing.
- Step 6: `1 passed, 114 deselected …`. **Known limitation DEV-022:** Rule 10 says to omit `### Cursor (plugin)` when the target fails, but the test, following AC-5.4, keeps it after the `install.sh` section. Mark Pass when the output matches; the open decision is logged in the drift log.
- Step 7: `exit 0`. On 2026-10-23 with the same CLI, no diff lines. On a later date, only `-# run date: 2026-10-23` / `+# run date: <today>` changes, plus the `claude --version` line if the CLI changed. The five summaries and `cursor-uat` stay. Re-record after any plugin layout or platform version change.

**Implementation Reference:** Story 5 — `scripts/tests/test_plugin_smoke.sh`, `scripts/tests/fixtures/plugin-smoke-results.txt`, `test_readme_install_order` in `scripts/tests/test_plugin_distribution.py`.

**Status:** [x] Pass  [ ] Fail — **Notes:** agent run 2026-10-23 at 0b033a3 (steps 1 and 7 outside the sandbox): smoke exit 0, 33 lines, summaries cursor/claude/codex/claude-plugin pass and cursor-plugin unverifiable via `script-run unverifiable (no cursor session)` (DEV-021), 8 self-tests; fixture-matches, run date 2026-10-23, claude 2.1.309, cursor-uat pending; README order as listed, 1 "listing pending"; 1 passed, 114 deselected; unverifiable fixture gives the expected AssertionError; `cursor-plugin fail` still 1 passed (known limitation DEV-022); --record exit 0 with no diff lines; every reset clean

---

### Scenario 9: Before the merge, the plugin installed from a local clone scaffolds and routes in a project with no `scripts/`

**Source:** Acceptance Criteria (AC-5.5) — Story 5; Rule 11 and V81 to V84; Edge Case "plugin and `install.sh` install in one project → both command sets exist" (State Catalog)
**Feature:** none
**Verification:** human — no recipe

**Preconditions:** setup block pasted; any earlier scenario's `undo` has run. This repeats what the lane ran (V81), from the clone in `$W` instead of the primary checkout.

**Steps:**
1. `newproj local && snap`
2. `claude plugin marketplace add "$CL" --scope local && claude plugin install writ@writ --scope local && ipath; ls scripts`
3. `claude -p --tools "" --output-format stream-json --verbose "Reply OK" | head -1 | python3 -c 'import json,sys; e=json.loads(sys.stdin.readline()); print(sorted(a for a in e.get("agents", []) if a.startswith("writ:"))); s=[c for c in e.get("slash_commands", []) if c.lstrip("/").startswith("writ:")]; print(len(s), [c for c in s if "preamble" in c])'`
4. Run `claude` in `$P`: type `/writ:initialize` (approve the Bash call, Esc at the discovery questions), then `/writ:writ "add a health endpoint"` (Esc at the route), then `/exit`. Afterwards run `ls -A .writ/docs | wc -l`.
5. Both installs: `bash "$CL/scripts/install.sh" --platform claude --no-commit | grep -F 'Using local writ'`. Run `claude`, type `/create-spec` and read the menu, run `/agents` and read the list, then `/exit`.
6. `cd "$P" && claude plugin uninstall writ@writ --scope local && claude plugin marketplace remove writ --scope local; regdiff`

**Expected Result:**
- Step 2: the add and install lines as in Scenario 2 step 3. `ipath` prints `local 0.43.0 $W/writ/plugins/writ …`, loaded in place (V81). `ls: scripts: No such file or directory`.
- Step 3: the eight `writ:writ-architect` … `writ:writ-visual-qa` agents, with no prompt-template doc such as `writ:coding-agent` (DEV-009, V84). Then `49 []`: 33 commands and 16 skills, no `_preamble`.
- Step 4: as Scenario 3 steps 3 and 4, with the tool call reading `python3 $W/writ/plugins/writ/scripts/scaffold-writ.py scaffold` (V82, V83). Then `0` (DEV-006).
- Step 5: `📦 Using local writ: $W/writ`. The menu offers both `/create-spec` (project) and `/writ:create-spec` (plugin), and `/agents` lists both `writ-coder` and `writ:writ-coder`. `adapters/claude-code.md` § Installation → Plugin documents this and recommends one install path per project.
- Step 6: as Scenario 2 step 5.

**Status:** [ ] Pass  [ ] Fail — **Notes:** blocked: agent run 2026-10-23 at 0b033a3: step 4 (interactive `/writ:initialize` and `/writ:writ`) not run, because nested `claude` cannot authenticate (OAuth session expired) and the agent has no TTY; rerun step 4 and the step 5 menu read in a logged-in terminal. Ran: snap 0/0; add and install lines as expected, ipath `local 0.43.0 $W/writ/plugins/writ`, `ls: scripts: No such file or directory`; step 3 the eight `writ:writ-*` agents and `49 []` (DEV-009); step 5 install.sh exit 0 with `Using local writ: $W/writ`, and the stream-json init event (in place of the menu and `/agents`) lists `create-spec` and `writ:create-spec`, `writ-coder` and `writ:writ-coder`; adapter bullet says "Use one install path per project"; undo exit 0, both registries same as snapshot, settings.json OK

---

### Scenario 10: The spec's Python tests pass on the 3.9 floor

**Source:** Success Criteria (spec contract); Acceptance Criteria AC-1.1, AC-2.1 to AC-2.4, AC-3.1 to AC-3.5, AC-4.1 to AC-4.5, AC-5.4 — Stories 1 to 5
**Feature:** none
**Verification:** human — no recipe

**Preconditions:** setup block pasted; `uv` on `PATH`.

**Steps:**
1. `pt scripts/tests/test_plugin_distribution.py scripts/tests/test_scaffold_writ.py`
2. `pt scripts/tests/test_scaffold_writ.py -k "bash_list_matches or bash_gitignore_matches_script"`

**Expected Result:**
- Step 1: `158 passed in …s`. A failure names the AC in its test's docstring.
- Step 2: `11 passed, 32 deselected …`. The `mkdir -p` lists in `install.sh` and `update.sh` expand to the script's eleven paths, and the bash function writes the same `.gitignore` bytes as the script on each fixture (no Python enters the installers).

**Status:** [x] Pass  [ ] Fail — **Notes:** agent run 2026-10-23 at 0b033a3: Python 3.9 via uv, pytest alone in the clone: `158 passed in 24.25s`; `11 passed, 32 deselected in 0.38s`

---

### Scenario 11: Without the `claude` CLI, only the validate checks read `unverifiable`, and the other plugin checks still run

**Source:** Shadow Path "Nil input" (technical spec); Acceptance Criteria (AC-5.3) — Story 5; State Catalog "Smoke test on a machine without the `claude` CLI"
**Feature:** none
**Verification:** human — no recipe

**Preconditions:** setup block pasted; `/usr/bin/python3` exists (the macOS system interpreter) and `claude` is not in `/usr/bin` or `/bin`.

**Steps:**
1. `inW && (cd "$CL" && env PATH=/usr/bin:/bin bash scripts/tests/test_plugin_smoke.sh --targets claude-plugin --no-self-test; echo "exit $?")`

**Expected Result:**
- `claude-plugin commands pass`, `claude-plugin script-run pass`, `claude-plugin instructions pass`, `claude-plugin scaffold pass`, `claude-plugin validate unverifiable (no claude CLI)`, `claude-plugin validate-marketplace unverifiable (no claude CLI)`, `claude-plugin unverifiable`, then `exit 0`. A recorded run like this would keep the Claude plugin out of first place in the README (Scenario 8 step 5).

**Status:** [x] Pass  [ ] Fail — **Notes:** agent run 2026-10-23 at 0b033a3 (outside the sandbox): with PATH=/usr/bin:/bin, commands/script-run/instructions/scaffold pass, `validate unverifiable (no claude CLI)`, `validate-marketplace unverifiable (no claude CLI)`, `claude-plugin unverifiable`, exit 0
