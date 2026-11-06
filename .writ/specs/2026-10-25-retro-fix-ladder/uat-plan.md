# UAT Plan: Retro Fix Ladder

> **Generated:** 2026-10-29
> **Spec:** `.writ/specs/2026-10-25-retro-fix-ladder/`
> **Stories Covered:** 4 of 4 completed
> **Total Scenarios:** 32
> **Verification recipe:** none. No `.writ/docs/app-verification.md` exists, and Writ has no app to launch: its checks (pytest, the bash tests, `scripts/eval.sh`) read markdown and run scripts, not a running process. With no launch command detected, Step 1.3's recommended answer is skip, so no recipe was drafted, saved, or bound. Every scenario is `human — no recipe`.

## How to Use This Plan

1. Work through scenarios in order (they're grouped by story, ordered by priority)
2. For each scenario, follow the steps exactly as written
3. Mark Pass or Fail — add notes for any unexpected behavior
4. Scenarios marked Fail should be filed as issues or fed back to the spec
5. A feature passes UAT when all scenarios pass (or failures are accepted as known limitations)

**Conventions for this plan:**

- Two kinds of scenario. **Live** scenarios (22, 24, 25, 32) run `/retro` or `/refresh-command` in a Claude Code session and judge the result by eye, because rung choice and signal matching are judgments. **Read and check** scenarios (all others) read the shipped files and run `scripts/retro-check.py` and the repository's own tests on fixtures in a scratch folder.
- **Never run `install.sh` or `update.sh` in the Writ repo, and never open a live session there.** `.claude/` and `.cursor/` in the repo are symlinks into the source. The live `/refresh-command` run happens in a clone, where the symlinks make it a project command. The live `/retro` runs happen in three small fixture projects that carry what an installed project has: `commands/retro.md` as `.claude/commands/retro.md`, plus `scripts/retro-check.py` and `scripts/arch-lint.py`.
- The live `/retro` fixtures share one story: a project whose `CLAUDE.md` says "never call print() in app code", whose `ruff.toml` does not select rule `T201` (flake8-print), and whose history holds a commit that added `print("starting")` and a later commit that fixed it. Each fixture has a hand-built transcript in Claude Code's JSONL shape (`<fixture>.jsonl`, outside the fixture repo) in which the agent writes `print()` and the user corrects it. They differ in the rule table: `$FA` tables the rule with Enforcer `none`; `$FB` has no `.writ/retros/` at all and three corrections; `$FD` tables the rule with a ruff enforcer and already selects `T201`.
- Live `/retro` scenarios need `uvx` (from uv) and network the first time `uvx ruff` runs. Scenario 11 needs `uv` with Python 3.9 available. Claude Code asks whether to trust each new scratch folder the first time a session opens there; accept it.
- Every helper that runs a session, pytest, or `reset` refuses to run unless the shell is inside `$W`. `$REPO` is cloned from and never written to. Run the plan in `bash` on macOS (`sed -i ''`), outside any sandbox. Paste the setup block below once per shell. Stop if the first line does not print `W=/...` or the last line differs from the one shown after the block.
- Expected results come from the spec, the four What Was Built records, the drift log, and the tree at `e66296c` (branch `phase/15-code-level-rigor`). Story 1 landed in `50ecd98`, Story 2 in `3f1f5e8`, Story 3 in `e32d567`, Story 4 in `87493ae`. None of these scenarios has been run for this plan. After each scenario that edits the clone, run `reset` and confirm it prints nothing. Each live fixture is used by one scenario; to repeat a live scenario, paste the setup block again in a new shell. When done: `rm -rf "$W"`.
- **Drift.** DEV-001 to DEV-013 are Small and auto-amended. Where the build differs from `sub-specs/technical-spec.md`, the expected results follow the drift log. Several DEV entries describe a "Spec amendment" to `technical-spec.md` that is not in that file (for example DEV-002's reason-code note, DEV-004's error-map row, DEV-009's enforcer, and DEV-011's edge-case row), so when the two disagree, read the DEV entry. Where testers see drift: DEV-002 (Scenarios 4, 7, 21), DEV-003 (2, 3), DEV-004 (8), DEV-006 and DEV-007 (27, 31), DEV-008 (26, 32), DEV-009 and DEV-010 (11, 14: two enforced seed rows, not three), DEV-011 (16, 22, 23: a second finding on a tabled rule is `dismissed` with a `**Reason:**` line), DEV-012 (17), DEV-013 (15, 19). DEV-001 (lenient field parsing) and DEV-005 (no reason code for a malformed finding heading, Since cell, or unknown signal; an open gap) have no scenario of their own.

### Setup block

```bash
W=$(mktemp -d "${TMPDIR:-/tmp}/writ-uat-ladder.XXXXXX") && cd "$W" && W=$PWD && echo "W=$W"
REPO=/Users/asellke/Projects/writ            # read only: cloned from, never edited, never installed into
CL="$W/clone"; git clone -q "$REPO" "$CL"    # committed tree on the current branch
PYX=$(python3 -c 'import sys; print(sys.executable)')   # python by absolute path, for a run with an empty PATH
inW() { case "$PWD/" in "$W"/*) ;; *) echo "refusing: $PWD is outside $W" >&2; return 1;; esac; }
# live [dir]: Claude Code in $CL, or in a fixture
live() { inW && (cd "${1:-$CL}" && claude); }
# pt <pytest args>: pytest on Python 3.9 inside the clone
pt() { inW && (cd "$CL" && uv run --python 3.9 pytest "$@"); }
# reset: undo every edit in the clone and drop untracked files; prints nothing when clean
reset() { inW && git -C "$CL" checkout -q -- . && git -C "$CL" clean -qfd && git -C "$CL" status --short; }
# rc <args>: the clone's retro-check.py
rc() { python3 "$CL/scripts/retro-check.py" "$@"; }
# cm <dir> <date> <message>: commit everything at a fixed date
cm() { (cd "$1" && git add -A && GIT_AUTHOR_DATE="$2T10:00:00" GIT_COMMITTER_DATE="$2T10:00:00" git commit -qm "$3"); }

# Fixtures for retro-check.py: $G is a git repo with one commit, $NG is outside any git work tree
G="$W/gitrepo"; mkdir -p "$G" && git -C "$G" init -q && echo seed > "$G/seed.txt" && cm "$G" 2026-10-01 "seed"
GSHA=$(git -C "$G" rev-parse HEAD)
NG="$W/nogit"; mkdir -p "$NG" "$W/pathless"
F="$W/rc"; mkdir -p "$F/ok"
cat > "$F/ok/2026-10-29-uat.md" <<EOF
# Retro: uat

## Transcripts

- \`~/.claude/projects/uat/s1.jsonl\`

## Findings

### F1 [High] Repeated mistake: print() in app code
**Rung:** lint
**Ladder:** architecture: no (one package); types: no (a type checker does not flag it); lint: yes
**Proof:** mistake $GSHA; check \`ruff check app.py\`; result fails
**Disposition:** applied

### F2 [Medium] Navigation churn: searched for a missing file
**Rung:** none
**Disposition:** deferred

## Rule table changes

- added: Log with the logging module
EOF
cat > "$F/ok/rule-enforcers.md" <<EOF
# Rule-to-Enforcer Table

| Rule | Written in | Enforcer | Rung | Proof | Since |
|---|---|---|---|---|---|
| Log with the logging module | \`CLAUDE.md\` | \`ruff check .\` | lint | $GSHA: fails | 2026-10-29-uat.md F1 |
| Plain prose | \`CLAUDE.md\` | none | docs | — | seed |
EOF
# mkd <name> <sed expression>: $F/<name>/ holds the ok table and the ok retro file edited by the expression
mkd() { mkdir -p "$F/$1" && cp "$F/ok/rule-enforcers.md" "$F/$1/" && sed -e "$2" "$F/ok/2026-10-29-uat.md" > "$F/$1/2026-10-29-uat.md"; }

# Fixtures for live /retro runs: a project whose history holds a print() mistake and its fix
# mkfx <dir> <none-row|no-table|enforced> <n files>
mkfx() {
  local d="$1" v="$2" n="$3" f files sel a row
  files=$(echo app.py cli.py worker.py | cut -d' ' -f1-"$n")
  mkdir -p "$d/.claude/commands" "$d/scripts" "$d/skills/plain-prose" "$d/.writ/docs"
  cp "$CL/commands/retro.md" "$CL/commands/_preamble.md" "$d/.claude/commands/"
  cp "$CL/scripts/retro-check.py" "$CL/scripts/arch-lint.py" "$d/scripts/"
  cp "$CL/skills/plain-prose/SKILL.md" "$d/skills/plain-prose/"
  cp "$CL/.writ/docs/architecture-lint.md" "$d/.writ/docs/"
  printf '# Project rules\n\n- Log with the logging module; never call print() in app code.\n- Lint with `uvx ruff check .` (config: ruff.toml).\n' > "$d/CLAUDE.md"
  sel='"E4", "E7", "E9", "F"'; if [ "$v" = enforced ]; then sel="$sel, \"T201\""; fi
  printf '[lint]\nselect = [%s]\n' "$sel" > "$d/ruff.toml"
  git -C "$d" init -q -b main
  for f in $files; do printf 'import logging\n\nlog = logging.getLogger(__name__)\n\n\ndef start():\n    pass\n' > "$d/$f"; done
  cm "$d" 2026-10-27 "chore: project setup"
  for f in $files; do sed -i '' 's/^    pass$/    print("starting")/' "$d/$f"; done
  cm "$d" 2026-10-28 "feat: add startup lines"
  for f in $files; do sed -i '' 's/^    print("starting")$/    log.info("starting")/' "$d/$f"; done
  cm "$d" 2026-10-28 "fix: log startup lines instead of printing"
  [ "$v" = no-table ] && return 0
  mkdir -p "$d/.writ/retros"; cp "$CL/.writ/retros/2026-03-15.json" "$d/.writ/retros/"
  a=$(git -C "$d" rev-parse HEAD~1)
  if [ "$v" = enforced ]; then row="| \`uvx ruff check .\` | lint | $a: fails |"; else row="| none | docs | — |"; fi
  printf '# Rule-to-Enforcer Table\n\n| Rule | Written in | Enforcer | Rung | Proof | Since |\n|---|---|---|---|---|---|\n| Log with the logging module; never call print() in app code | `CLAUDE.md` %s seed |\n' "$row" > "$d/.writ/retros/rule-enforcers.md"
  cm "$d" 2026-10-28 "chore: add the rule table"
}
# tx <dir> <n>: <dir>.jsonl, a Claude Code-style transcript with n print() edits, each corrected by the user
tx() {
python3 - "$1" "$2" <<'PY'
import json, sys
d, n = sys.argv[1], int(sys.argv[2])
files = ["app.py", "cli.py", "worker.py"][:n]
out, t = [], [0]
def ev(role, content, usage=None):
    t[0] += 30
    msg = {"role": role, "content": content}
    if usage:
        msg["usage"] = usage
    out.append(json.dumps({"type": role, "sessionId": "uat-" + d.rsplit("/", 1)[1], "cwd": d,
                           "gitBranch": "main", "message": msg,
                           "timestamp": "2026-10-28T10:%02d:%02d.000Z" % divmod(t[0], 60)}))
ev("user", "Add a startup log line to start() in " + ", ".join(files) + ".")
for i, f in enumerate(files):
    ev("assistant", [{"type": "tool_use", "id": "a%d" % i, "name": "Edit", "input": {
        "file_path": d + "/" + f, "old_string": "    pass", "new_string": '    print("starting")'}}],
       {"input_tokens": 9000, "output_tokens": 80})
    ev("user", [{"type": "tool_result", "tool_use_id": "a%d" % i, "content": "Updated " + f}])
    ev("user", "No print() in app code. CLAUDE.md says log with the logging module.")
    ev("assistant", [{"type": "tool_use", "id": "b%d" % i, "name": "Edit", "input": {
        "file_path": d + "/" + f, "old_string": '    print("starting")', "new_string": '    log.info("starting")'}}],
       {"input_tokens": 9500, "output_tokens": 80})
    ev("user", [{"type": "tool_result", "tool_use_id": "b%d" % i, "content": "Updated " + f}])
with open(d + ".jsonl", "w") as fh:
    fh.write("\n".join(out) + "\n")
PY
}
FA="$W/fx-a"; mkfx "$FA" none-row 1; tx "$FA" 1    # rule tabled with enforcer none; one correction
FB="$W/fx-b"; mkfx "$FB" no-table 3; tx "$FB" 3    # no .writ/retros/; three corrections
FD="$W/fx-d"; mkfx "$FD" enforced 1; tx "$FD" 1    # rule tabled with an enforcer; one correction
echo "setup done: commits $(git -C "$FA" rev-list --count HEAD) $(git -C "$FB" rev-list --count HEAD) $(git -C "$FD" rev-list --count HEAD); transcript lines $(awk 'END{print NR}' "$FA.jsonl") $(awk 'END{print NR}' "$FB.jsonl") $(awk 'END{print NR}' "$FD.jsonl")"
```

The last line should read `setup done: commits 4 3 4; transcript lines 6 16 6`. `$F/ok/` holds a conforming retro file (F1 an applied lint-rung finding whose proof cites `$GSHA`, F2 a `none`-rung finding) and a conforming two-row table beside it; most Story 1 scenarios edit a copy of it with `mkd`.

## Coverage Summary

| Story | Status | Scenarios | Source Breakdown |
|-------|--------|-----------|-----------------|
| Story 1: retro-check.py, the Rule Table and Ladder Checker | ✅ Covered | 9 | AC: 5, Errors: 3, Shadow: 1, Edge: 0 |
| Story 2: Seed This Repository's Rule-to-Enforcer Table | ✅ Covered | 5 | AC: 4, Errors: 1, Shadow: 0, Edge: 0 |
| Story 3: /retro Fix Ladder, Proof, Rule Table, and Signal Retirement | ✅ Covered | 11 | AC: 5, Errors: 2, Shadow: 1, Edge: 2, Experience: 1 |
| Story 4: /refresh-command Execution-Failure and Used-Skill Criteria | ✅ Covered | 7 | AC: 5, Errors: 1, Shadow: 1, Edge: 0 |

- Folded Error Map rows: "retro-check.py resolves a SHA" (no git, unknown SHA) is Scenario 3, with git off `PATH` in Scenario 9. "`/retro` Step 8 table update" (table missing) is Scenario 22. "`/refresh-command` skill target" (transcript not readable) is Scenario 32.
- Folded Shadow Paths: `retro-check.py --retro` Happy Path is Scenario 1 and Nil Input is Scenario 5. `/retro` ladder finding Happy Path is Scenario 25; Upstream Error (proof passes on the mistake) is Scenario 20, as text and record, not forced live. `/retro` Empty Input (no mistake findings, table untouched) has no live run; Scenario 9 shows an empty `## Findings` passes and Scenario 24 shows a run that applies nothing leaves the table unchanged. `/refresh-command` Happy Path and Nil Input (`no evidence`) predate this spec; the `no evidence` record is checked by `rejected-lacking-evidence-is-valid-record` in Scenario 29.
- Folded Interaction Edge Cases: "past mistake in an uncommitted transcript snippet" is Scenario 3 (a listed `.jsonl` ref resolves, an unlisted one fails) and Scenario 15 (the Proof paragraph). "Legacy retro file without Rung lines" is Scenario 25 (the legacy `2026-03-15.json` is present and unchanged). "Project with no `.writ/retros/` yet" is Scenario 22. "Rule table edited by hand" is Scenario 21.
- State Catalog: "No table yet" is Scenario 22; "Mistake against an unenforced rule" is Scenario 25; "Mistake against an enforced rule" is Scenario 24; "Proof fails to fail", "Proof cannot run", and "Docs rung chosen" are Scenario 20; "`retro-check.py` prints `fail`" is Scenario 21; both `/refresh-command` rows are Scenario 32. No fixture forces a check tool to be missing or a check to miss a mistake reliably, so those two states are checked from the command text and the records `retro-check.py` accepts.
- Moment of Truth (a finding that reads "lint: yes" with a proof that fails on the past commit) is Scenario 25.
- No pending stories: all four are Completed ✅.

---

## Story 1: retro-check.py, the Rule Table and Ladder Checker

### Scenario 1: A conforming retro file and rule table pass

**Source:** Acceptance Criteria (AC-1.1) — Story 1; Business Rules 6, 7, 9
**Feature:** none
**Verification:** human — no recipe

**Preconditions:**
- Setup block pasted.

**Steps:**
1. `cat "$F/ok/2026-10-29-uat.md" "$F/ok/rule-enforcers.md"`
2. `rc --retro "$F/ok/2026-10-29-uat.md" --table "$F/ok/rule-enforcers.md" --repo "$G"; echo "exit $?"`
3. `rc --retro "$F/ok/2026-10-29-uat.md" --repo "$G"; echo "exit $?"`
4. `pt scripts/tests/test_retro_check.py -q 2>&1 | tail -1`

**Expected Result:**
- Step 1: a retro file with `## Transcripts` (one `.jsonl` path) and `## Findings`. F1 is `[High] Repeated mistake` with Rung `lint`, a Ladder `architecture: no (...); types: no (...); lint: yes`, a Proof citing `$GSHA` with `result fails`, and Disposition `applied`. F2 is `[Medium] Navigation churn` with Rung `none` and Disposition `deferred`. The table has the six header cells, an enforced row whose Since is `2026-10-29-uat.md F1`, and a `none` / `docs` / `—` row.
- Step 2: `pass`, then `retro-check: pass (2 findings, 2 table rows, 0 reasons)`, then `exit 0`. No `reason:` line.
- Step 3: the same three lines. With no `--table`, the script reads `rule-enforcers.md` beside the retro file.
- Step 4: `62 passed` (the count Story 1 recorded) and no `failed`.

**Implementation Reference:** Story 1 — Files: `scripts/retro-check.py`, `scripts/tests/test_retro_check.py`

**Status:** [ ] Pass  [ ] Fail

**Notes:**

---

### Scenario 2: Each finding-level defect fails with its reason code and the finding ID

**Source:** Acceptance Criteria (AC-1.2) — Story 1; Business Rules 3, 5, 7; DEV-003
**Feature:** none
**Verification:** human — no recipe

**Preconditions:**
- Setup block pasted.

**Steps:**
1. Make one fixture per defect:
   ```bash
   mkd rung_missing '/^\*\*Rung:\*\* lint$/d'
   mkd ladder_order 's/architecture: no (one package); types: no (a type checker does not flag it)/types: no (a type checker does not flag it); architecture: no (one package)/'
   mkd proof_missing '/^\*\*Proof:\*\*/d'
   mkd proof_not_failing 's/result fails$/result passes/'
   mkd applied_test_rung 's/^\*\*Rung:\*\* lint$/**Rung:** test/; s/lint: yes$/lint: no (no rule fits); test: yes/'
   mkd disposition_missing '/^\*\*Disposition:\*\* applied$/d'
   ```
2. `for d in rung_missing ladder_order proof_missing proof_not_failing applied_test_rung disposition_missing; do echo "== $d"; rc --retro "$F/$d/2026-10-29-uat.md" --repo "$G"; echo "exit $?"; done`
3. `pt scripts/tests/test_retro_check.py -q -k finding_defect 2>&1 | tail -1`

**Expected Result:**
- Step 2: for each fixture, `fail`, one `reason:` line, the summary `retro-check: fail (2 findings, 2 table rows, 1 reasons)`, and `exit 1`. The reason lines, in order: `reason: rung_missing F1`, `reason: ladder_order F1`, `reason: proof_missing F1`, `reason: proof_not_failing F1`, `reason: applied_test_rung F1`, `reason: disposition_missing F1`.
- No fixture prints a second reason. `proof_missing` prints no `proof_not_failing` line, because there is no result to compare (DEV-003).
- Step 3: no `failed`.

**Implementation Reference:** Story 1 — Files: `scripts/retro-check.py` (`Checker.finding`, `Checker.ladder`)

**Status:** [ ] Pass  [ ] Fail

**Notes:**

---

### Scenario 3: Proof refs resolve against the repo or the transcript list, and a folder outside git is unverifiable

**Source:** Acceptance Criteria (AC-1.3) — Story 1; Error Map "retro-check.py resolves a SHA" (both rows); Edge Case "past mistake in an uncommitted transcript snippet"; DEV-003
**Feature:** none
**Verification:** human — no recipe

**Preconditions:**
- Setup block pasted.

**Steps:**
1. `mkd badsha "s/mistake $GSHA/mistake abcdef1234567/"; rc --retro "$F/badsha/2026-10-29-uat.md" --repo "$G"; echo "exit $?"`
2. `rc --retro "$F/ok/2026-10-29-uat.md" --repo "$G" | grep -c proof_ref_unknown`
3. `mkd jsonl "s|mistake $GSHA|mistake ~/.claude/projects/uat/s1.jsonl|"; rc --retro "$F/jsonl/2026-10-29-uat.md" --repo "$G"; echo "exit $?"`
4. `mkd jsonl2 "s|mistake $GSHA|mistake ~/.claude/projects/uat/other.jsonl|"; rc --retro "$F/jsonl2/2026-10-29-uat.md" --repo "$G" | sed -n 2p`
5. `git -C "$NG" rev-parse --is-inside-work-tree 2>&1 | head -1; rc --retro "$F/ok/2026-10-29-uat.md" --repo "$NG"; echo "exit $?"`

**Expected Result:**
- Step 1: `fail`, `reason: proof_ref_unknown F1 abcdef1234567`, `retro-check: fail (2 findings, 2 table rows, 1 reasons)`, `exit 1`.
- Step 2: `0`. The real commit SHA resolves.
- Step 3: `pass`, `retro-check: pass (2 findings, 2 table rows, 0 reasons)`, `exit 0`. A `.jsonl` ref listed under `## Transcripts` counts as a past mistake.
- Step 4: `reason: proof_ref_unknown F1 ~/.claude/projects/uat/other.jsonl`. A transcript ref must be listed under `## Transcripts`.
- Step 5: a `fatal: not a git repository` line, then `unverifiable`, `reason: no_git`, `retro-check: unverifiable (2 findings, 2 table rows, 1 reasons)`, `exit 0`. Two SHAs needed resolving and `no_git` prints once (DEV-003).

**Implementation Reference:** Story 1 — Files: `scripts/retro-check.py` (`Git.has_commit`, `Checker.commit_known`)

**Status:** [ ] Pass  [ ] Fail

**Notes:**

---

### Scenario 4: Table header and unenforced-row defects fail, and an explicit missing table is unverifiable

**Source:** Acceptance Criteria (AC-1.4) — Story 1; Business Rule 9; DEV-002
**Feature:** none
**Verification:** human — no recipe

**Preconditions:**
- Setup block pasted.

**Steps:**
1. `mkdir -p "$F/t"; sed 's/^| Rule | Written in |/| Rule | Where |/' "$F/ok/rule-enforcers.md" > "$F/t/header.md"; rc --table "$F/t/header.md" --repo "$G"; echo "exit $?"`
2. `sed 's/| none | docs |/| none | lint |/' "$F/ok/rule-enforcers.md" > "$F/t/nonelint.md"; rc --table "$F/t/nonelint.md" --repo "$G"; echo "exit $?"`
3. `rc --table "$F/t/missing.md"; echo "exit $?"`
4. `pt scripts/tests/test_retro_check.py -q -k "table_defect or explicit_table_missing" 2>&1 | tail -1`

**Expected Result:**
- Step 1: `fail`, `reason: table_header`, `retro-check: fail (0 findings, 2 table rows, 1 reasons)`, `exit 1`. No row-level reason: with a wrong header, rows are not read (DEV-002).
- Step 2: `fail`, `reason: table_unenforced_rung row 2`, `retro-check: fail (0 findings, 2 table rows, 1 reasons)`, `exit 1`.
- Step 3: `unverifiable`, `reason: table_missing $W/rc/t/missing.md` (the path as typed, with `$W` expanded), `retro-check: unverifiable (0 findings, 0 table rows, 1 reasons)`, `exit 0`.
- Step 4: no `failed`.

**Implementation Reference:** Story 1 — Files: `scripts/retro-check.py` (`parse_table`, `Checker.table`)

**Status:** [ ] Pass  [ ] Fail

**Notes:**

---

### Scenario 5: Usage errors exit 2 with empty stdout, `--help` exits 0, a run writes nothing, and the script ships

**Source:** Acceptance Criteria (AC-1.5) — Story 1; Business Rule 17
**Feature:** none
**Verification:** human — no recipe

**Preconditions:**
- Setup block pasted.

**Steps:**
1. `rc > "$W/out.txt" 2> "$W/err.txt"; echo "exit $?"; wc -c < "$W/out.txt"; cat "$W/err.txt"`
2. `rc --help > "$W/help.txt"; echo "exit $?"; head -1 "$W/help.txt"`
3. `snap() { (cd "$W" && find rc gitrepo -type f -exec shasum {} + | sort); }; snap > "$W/before.txt"; rc --retro "$F/ok/2026-10-29-uat.md" --repo "$G" > /dev/null; snap > "$W/after.txt"; diff "$W/before.txt" "$W/after.txt" && echo unchanged`
4. `grep -n 'retro-check' "$CL/.writ/docs/agent-cli-contract.md"; cmp "$CL/scripts/retro-check.py" "$CL/plugins/writ/scripts/retro-check.py" && echo "plugin copy matches"`
5. `pt scripts/tests/test_agent_cli_contract.py -q 2>&1 | tail -1`

**Expected Result:**
- Step 1: `exit 2`, then `0` (stdout is empty), then on stderr `usage: retro-check.py [-h] [--retro PATH] [--table PATH] [--repo DIR]` and `retro-check.py: error: give --retro, --table, or both`.
- Step 2: `exit 0`, then `usage: retro-check.py [-h] [--retro PATH] [--table PATH] [--repo DIR]`.
- Step 3: `unchanged`. File names and checksums under both fixture folders, `.git` included, are the same after a full run.
- Step 4: one Classification row, `` | `retro-check.py` | check |  | commands/retro.md | ``, then `plugin copy matches`.
- Step 5: no `failed`.

**Implementation Reference:** Story 1 — Files: `scripts/retro-check.py` (`main`), `.writ/docs/agent-cli-contract.md`, `plugins/writ/scripts/retro-check.py` (generated)

**Status:** [ ] Pass  [ ] Fail

**Notes:**

---

### Scenario 6: A missing retro file is unverifiable, not a failure

**Source:** Error Map "retro-check.py reads the retro file" — Story 1
**Feature:** none
**Verification:** human — no recipe

**Preconditions:**
- Setup block pasted. `ls "$F/none" 2>&1` reports no such directory.

**Steps:**
1. `rc --retro "$F/none/2026-10-29-uat.md" --repo "$G"; echo "exit $?"`
2. `pt scripts/tests/test_retro_check.py -q -k retro_missing 2>&1 | tail -1`

**Expected Result:**
- Step 1: `unverifiable`, `reason: retro_missing $W/rc/none/2026-10-29-uat.md`, `retro-check: unverifiable (0 findings, 0 table rows, 1 reasons)`, `exit 0`.
- Step 2: `1 passed` with a deselected count.

**Status:** [ ] Pass  [ ] Fail

**Notes:**

---

### Scenario 7: A needed default table that is missing fails, and so does a table without the finding's row

**Source:** Error Map "retro-check.py reads the table" (needed default missing) — Story 1; Success Criteria ("applied finding without a table row"); DEV-002
**Feature:** none
**Verification:** human — no recipe

**Preconditions:**
- Setup block pasted.

**Steps:**
1. `mkdir -p "$F/notable" && cp "$F/ok/2026-10-29-uat.md" "$F/notable/"; rc --retro "$F/notable/2026-10-29-uat.md" --repo "$G"; echo "exit $?"`
2. `mkd rowmissing 's/^$//'; sed -i '' 's/| 2026-10-29-uat.md F1 |$/| seed |/' "$F/rowmissing/rule-enforcers.md"; rc --retro "$F/rowmissing/2026-10-29-uat.md" --repo "$G"; echo "exit $?"`

**Expected Result:**
- Step 1: `fail`, `reason: table_missing $W/rc/notable/rule-enforcers.md`, `retro-check: fail (2 findings, 0 table rows, 1 reasons)`, `exit 1`. No `table_row_missing` line: the missing-table reason replaces it (DEV-002).
- Step 2: `fail`, `reason: table_row_missing F1`, `retro-check: fail (2 findings, 2 table rows, 1 reasons)`, `exit 1`. F2 (`none`, `deferred`) needs no row.

**Status:** [ ] Pass  [ ] Fail

**Notes:**

---

### Scenario 8: An unknown flag or an unreadable path exits 2 with nothing on stdout

**Source:** Error Map "retro-check.py args" — Story 1; DEV-004
**Feature:** none
**Verification:** human — no recipe

**Preconditions:**
- Setup block pasted.

**Steps:**
1. `rc --frob > "$W/out.txt" 2> "$W/err.txt"; echo "exit $?"; wc -c < "$W/out.txt"; tail -1 "$W/err.txt"`
2. `rc --retro "$F" > "$W/out.txt" 2> "$W/err.txt"; echo "exit $?"; wc -c < "$W/out.txt"; cat "$W/err.txt"`

**Expected Result:**
- Step 1: `exit 2`, `0`, `retro-check.py: error: unrecognized arguments: --frob`.
- Step 2: `exit 2`, `0`, `retro-check: cannot read $W/rc (Is a directory)`. A path that exists but cannot be read is a usage error, not a verdict (DEV-004).

**Status:** [ ] Pass  [ ] Fail

**Notes:**

---

### Scenario 9: An empty Findings section passes, a missing one fails, and git off PATH is `no_git`

**Source:** Shadow Path `retro-check.py --retro` (Empty Input, Upstream Error) — Story 1
**Feature:** none
**Verification:** human — no recipe

**Preconditions:**
- Setup block pasted.

**Steps:**
1. `mkdir -p "$F/empty"; printf '# Retro\n\n## Transcripts\n\n## Findings\n' > "$F/empty/2026-10-29-empty.md"; rc --retro "$F/empty/2026-10-29-empty.md"; echo "exit $?"`
2. `printf '# Retro\n\n## Transcripts\n' > "$F/empty/2026-10-29-nofindings.md"; rc --retro "$F/empty/2026-10-29-nofindings.md"; echo "exit $?"`
3. `env PATH="$W/pathless" "$PYX" "$CL/scripts/retro-check.py" --retro "$F/ok/2026-10-29-uat.md" --repo "$G"; echo "exit $?"`

**Expected Result:**
- Step 1: `pass`, `retro-check: pass (0 findings, 0 table rows, 0 reasons)`, `exit 0`. No table is read: none exists beside the file, and no finding needs a row.
- Step 2: `fail`, `reason: no_findings_section`, `retro-check: fail (0 findings, 0 table rows, 1 reasons)`, `exit 1`.
- Step 3: `unverifiable`, `reason: no_git`, `retro-check: unverifiable (2 findings, 2 table rows, 1 reasons)`, `exit 0`. With no `git` on `PATH`, a SHA cannot be looked up, which is not the same as an unknown SHA.

**Status:** [ ] Pass  [ ] Fail

**Notes:**

---

## Story 2: Seed This Repository's Rule-to-Enforcer Table

### Scenario 10: The seeded table has its heading and one six-column table, and lives in project history

**Source:** Acceptance Criteria (AC-2.1) — Story 2; Business Rules 9 (Table format), 10 (Table location)
**Feature:** none
**Verification:** human — no recipe

**Preconditions:**
- Setup block pasted; `reset` prints nothing.

**Steps:**
1. `head -1 "$CL/.writ/retros/rule-enforcers.md"; grep -n '^|' "$CL/.writ/retros/rule-enforcers.md" | cut -c1-70`
2. `git -C "$CL" ls-files .writ/retros; grep -c 'retros' "$CL/scripts/install.sh"`
3. `pt scripts/tests/test_retro_fix_ladder.py -q -k heading_and_header 2>&1 | tail -1`

**Expected Result:**
- Step 1: `# Rule-to-Enforcer Table`, then five `|` lines on lines 5 to 9 with nothing between them (one table): line 5 is `| Rule | Written in | Enforcer | Rung | Proof | Since |`, line 6 the delimiter, lines 7 to 9 the three rows.
- Step 2: `.writ/retros/2026-03-15.json` and `.writ/retros/rule-enforcers.md`, then `0`: the table sits in `.writ/retros/`, which `install.sh` does not ship.
- Step 3: `1 passed, 10 deselected`.

**Implementation Reference:** Story 2 — Files: `.writ/retros/rule-enforcers.md`, `scripts/tests/test_retro_fix_ladder.py`

**Status:** [ ] Pass  [ ] Fail

**Notes:**

---

### Scenario 11: Each enforced row's proof fails on the recorded parent and passes on the fix

**Source:** Acceptance Criteria (AC-2.2) — Story 2; Business Rules 6 (Proof line), 8 (Running a proof); DEV-009, DEV-010
**Feature:** none
**Verification:** human — no recipe

**Preconditions:**
- Setup block pasted. `uv python find 3.9` prints a path. About three minutes.

**Steps:**
1. `grep ': fails' "$CL/.writ/retros/rule-enforcers.md" | cut -d'|' -f4,6`
2. `for c in ebbf064 d47bcec; do git -C "$CL" log --format='%h parent=%p %s' -1 "$c"; done`
3. Run the Python 3.9 enforcer on the parent and on the fix, each in a detached worktree:
   ```bash
   for c in 0335b29 ebbf064; do git -C "$CL" worktree add -q --detach "$W/wt-$c" "$c"; (cd "$W/wt-$c" && uv run --python 3.9 --with pytest pytest -q scripts/tests/test_ac_trace.py::CitationScanTests::test_symlink_loop_does_not_crash_the_scan > "$W/p39-$c.txt" 2>&1; echo "$c exit $?"; grep -m2 -E 'RuntimeError|ymlink loop' "$W/p39-$c.txt"; tail -1 "$W/p39-$c.txt"); done
   ```
4. Run the generated-trees enforcer the same way:
   ```bash
   for c in ddfb17f d47bcec; do git -C "$CL" worktree add -q --detach "$W/wt-$c" "$c"; (cd "$W/wt-$c" && python3 scripts/gen-platform-trees.py --check > "$W/trees-$c.txt" 2>&1; echo "$c exit $?"; head -1 "$W/trees-$c.txt"; grep '^reason:' "$W/trees-$c.txt"; tail -1 "$W/trees-$c.txt"); done
   ```
5. `for c in 0335b29 ebbf064 ddfb17f d47bcec; do git -C "$CL" worktree remove --force "$W/wt-$c"; done; git -C "$CL" worktree list`

**Expected Result:**
- Step 1: two rows. The Python 3.9 row's Enforcer is `` `uv run --python 3.9 --with pytest pytest scripts/tests/test_ac_trace.py::CitationScanTests::test_symlink_loop_does_not_crash_the_scan` `` with Proof `0335b291e1403b38be6305a4de8154547d92604e: fails`. The trees row's Enforcer is `` `python3 scripts/gen-platform-trees.py --check` `` with Proof `ddfb17ffe9b6de163a0d9aa31b43d7e2d2e30878: fails`. There are two enforced rows, not three; the shipped-refs candidate is out (DEV-010, Scenario 14).
- Step 2: `ebbf064 parent=0335b29 fix(ac-trace): skip unresolvable symlinks on Python < 3.13` and `d47bcec parent=ddfb17f feat(why): register /why on every catalog and surface (Story 2)`.
- Step 3: `0335b29 exit 1`, output naming `RuntimeError` and a symlink loop, and a last line with `1 failed`. Then `ebbf064 exit 0` and a last line with `1 passed`. The `--with pytest` flag is there because neither commit has a `pyproject.toml` (DEV-009).
- Step 4: `ddfb17f exit 1`, line 1 `fail`, reason lines naming the two `status.md` copies as stale and the two `why.md` copies as missing, and a summary starting `gen-platform-trees: fail (2 stale, 2 missing`. Then `d47bcec exit 0`, line 1 `pass`, no reason line about a stale or missing file, and a summary with 0 stale and 0 missing.
- Step 5: one line, the clone itself.
- Judgment (DEV-010): `d47bcec` is a `feat` commit, and `ddfb17f` is a stale state the why-command spec left between its Stories 1 and 2 on purpose. The drift log accepts it as a real commit that broke the rule. If you read AC-2.2's "the parent of a fix commit" as excluding a planned intermediate state, mark Fail and say so in Notes.

**Implementation Reference:** Story 2 — WWB Implementation Decisions 1 to 4

**Status:** [ ] Pass  [ ] Fail

**Notes:**

---

### Scenario 12: At least one row is unenforced, and every unenforced row is a docs row with no proof

**Source:** Acceptance Criteria (AC-2.3) — Story 2; Business Rule 9
**Feature:** none
**Verification:** human — no recipe

**Preconditions:**
- Setup block pasted; `reset` prints nothing.

**Steps:**
1. `T="$CL/.writ/retros/rule-enforcers.md"; grep -c '| none |' "$T"; grep '| none |' "$T" | grep -vc '| none | docs | — |'; grep -c ': fails | seed |$' "$T"`
2. `grep '| none |' "$T" | cut -d'|' -f2,3`
3. `pt scripts/tests/test_retro_fix_ladder.py -q -k enforced_and_unenforced 2>&1 | tail -1`

**Expected Result:**
- Step 1: `1`, `0`, `2`: one `none` row, no `none` row with a rung other than `docs` or a Proof other than `—`, and two enforced rows.
- Step 2: `` Instruction files use plain prose | `skills/plain-prose/SKILL.md` ``.
- Step 3: `1 passed, 10 deselected`.

**Status:** [ ] Pass  [ ] Fail

**Notes:**

---

### Scenario 13: `retro-check.py --table` passes on the seeded table and catches a broken proof

**Source:** Acceptance Criteria (AC-2.4) — Story 2; Success Criteria (second bullet)
**Feature:** none
**Verification:** human — no recipe

**Preconditions:**
- Setup block pasted; `reset` prints nothing.

**Steps:**
1. `(cd "$CL" && python3 scripts/retro-check.py --table .writ/retros/rule-enforcers.md --repo .; echo "exit $?")`
2. `(cd "$CL" && python3 scripts/retro-check.py --table .writ/retros/rule-enforcers.md | head -1)`
3. `sed -i '' 's/0335b291e1403b38be6305a4de8154547d92604e: fails/abcdef1234567: fails/' "$CL/.writ/retros/rule-enforcers.md"; (cd "$CL" && python3 scripts/retro-check.py --table .writ/retros/rule-enforcers.md; echo "exit $?"); reset`
4. `pt scripts/tests/test_retro_fix_ladder.py -q 2>&1 | tail -1`

**Expected Result:**
- Step 1: `pass`, `retro-check: pass (0 findings, 3 table rows, 0 reasons)`, `exit 0`.
- Step 2: `pass`. `--repo` defaults to the current folder, so the Success Criteria's command form works as written.
- Step 3: `fail`, `reason: table_proof_ref_unknown row 1 abcdef1234567`, `retro-check: fail (0 findings, 3 table rows, 1 reasons)`, `exit 1`. `reset` prints nothing.
- Step 4: `11 passed`.

**Status:** [ ] Pass  [ ] Fail

**Notes:**

---

### Scenario 14: The candidate that could not be proven was left out, and no proof is synthetic

**Source:** Error Map "Story 2 seeding" — Story 2; Business Rule 6 ("A synthetic fixture written for the occasion is not a past mistake"); DEV-010
**Feature:** none
**Verification:** human — no recipe

**Preconditions:**
- Setup block pasted.

**Steps:**
1. `for c in 7967ea3 ce6e8ac; do git -C "$CL" cat-file -e "$c:scripts/eval-shipped-refs.py" 2>/dev/null && echo "$c has it" || echo "$c lacks scripts/eval-shipped-refs.py"; done; git -C "$CL" log --format='%h %s' --diff-filter=A -- scripts/eval-shipped-refs.py`
2. `grep -c 'eval-shipped-refs' "$CL/.writ/retros/rule-enforcers.md"; for s in 0335b29 ddfb17f; do git -C "$CL" merge-base --is-ancestor "$s" HEAD && echo "$s is on this branch"; done`
3. `grep -n 'Stop rule' "$CL/.writ/specs/2026-10-25-retro-fix-ladder/user-stories/story-2-seed-rule-table.md"`

**Expected Result:**
- Step 1: `7967ea3 lacks scripts/eval-shipped-refs.py`, `ce6e8ac lacks scripts/eval-shipped-refs.py`, then `6434d9c feat(eval): add shipped-refs check for internal references in commands`. The enforcer was added after both candidate fixes, so it cannot run on a copy of either.
- Step 2: `0`, then `0335b29 is on this branch` and `ddfb17f is on this branch`. Both proofs are commits in the branch's history, not fixtures.
- Step 3: the stop rule: fewer than two qualifying fix commits stops the story with no synthetic proof. Two qualified, so it did not trigger.

**Status:** [ ] Pass  [ ] Fail

**Notes:**

---

## Story 3: /retro Fix Ladder, Proof, Rule Table, and Signal Retirement

### Scenario 15: Step 5 carries the five-rung Fix ladder table, the Ladder and Proof grammar, and a filled example

**Source:** Acceptance Criteria (AC-3.1) — Story 3; Business Rules 1 to 6 and 8; DEV-013
**Feature:** none
**Verification:** human — no recipe

**Preconditions:**
- Setup block pasted; `reset` prints nothing.

**Steps:**
1. `sed -n '/^### Fix ladder/,/^### Step 6:/p' "$CL/commands/retro.md"`
2. `` sed -n '/^```markdown$/,/^```$/p' "$CL/commands/retro.md"; grep -n '^| `issue`' "$CL/commands/retro.md"; grep -c 'Never target source code or tests.' "$CL/commands/retro.md" ``
3. `pt scripts/tests/test_retro_fix_ladder.py -q -k "five_rungs or grammar" 2>&1 | tail -1`
4. `sed -i '' '/^| types | a type-checker setting |/d' "$CL/commands/retro.md"; pt scripts/tests/test_retro_fix_ladder.py -q -k five_rungs 2>&1 | grep -E 'assert|failed|passed' | head -3; reset`

**Expected Result:**
- Step 1: the `### Fix ladder` heading, then a sentence that Silent patch, Stale guidance, Repeated mistake, and User correction findings take the first rung that would have stopped the mistake, and other findings carry `**Rung:** none` unless a check would prevent them. A table `| Rung | What it is in /retro | Route |` with rows `architecture`, `types`, `lint`, `test`, `docs` in that order. The first three route `` `apply` when config-only; `issue` otherwise ``; `test` routes `` `issue`; never `applied` ``; `docs` routes `` `apply`, `refresh`, or `knowledge` ``. A **Ladder line.** paragraph with `<rung>: no (<reason>); ...; <rung>: yes`, starting at architecture, no gaps, a reason for each `no`, ending in the one `yes`. A **Proof line.** paragraph with ``**Proof:** mistake <ref>; check `<command>`; result <fails|passes|pending>``; the ref is a commit SHA in this repository or a transcript path exactly as listed under `## Transcripts`; "A fixture written for the occasion is not a past mistake"; the mistake is materialized with `git show` into a temp directory or `git worktree add --detach`, removed afterwards; a transcript snippet is rebuilt in a temp file; the result is `pending` until Step 6, `applied` requires `result fails`, and docs-rung findings need no proof.
- Step 2: the example `### F1 [High] Repeated mistake: bare except hides errors` with an Evidence block, `**Rule:**`, `**Rung:** lint`, `**Ladder:** architecture: no (...); types: no (...); lint: yes`, `**Target:** ruff.toml → [lint] select`, `**Change:**`, ``**Proof:** mistake 3f2c1ab; check `ruff check src/`; result fails`` (the example shows a finding after its proof ran, DEV-013), and `**Route:** apply`. The `issue` route row says a source or test edit carries the finding's proof as the issue's done check. Then `1`.
- Step 3: `3 passed, 8 deselected`. One of the three runs the Step 5 example through `retro-check.py` outside a git work tree; its SHA is illustrative, so the only reason there is `no_git`.
- Step 4: an assertion line showing a rung list without `types`, then `1 failed`. `reset` prints nothing.

**Implementation Reference:** Story 3 — Files: `commands/retro.md` (§ Step 5, § Fix ladder), `scripts/tests/test_retro_fix_ladder.py`

**Status:** [ ] Pass  [ ] Fail

**Notes:**

---

### Scenario 16: Step 6 runs the proof after an Apply, and Step 8 writes a checked record and the table

**Source:** Acceptance Criteria (AC-3.2) — Story 3; Business Rules 7, 9, 12; DEV-011
**Feature:** none
**Verification:** human — no recipe

**Preconditions:**
- Setup block pasted; `reset` prints nothing.

**Steps:**
1. `sed -n '/^### Step 6:/,/^### Step 7:/p' "$CL/commands/retro.md"`
2. `sed -n '/^### Step 8:/,/^## Error Handling/p' "$CL/commands/retro.md"`
3. `pt scripts/tests/test_retro_fix_ladder.py -q -k "step6 or step8" 2>&1 | tail -1`

**Expected Result:**
- Step 1: when two findings name the same rule, Apply is offered on the first only, and the second is recorded as `dismissed` with the reason `same rule as F<n>` and no table row (DEV-011). A **Proof run.** paragraph covers an Apply on architecture, types, or lint with three outcomes: the check fails on the mistake → keep the edit, `result fails`, `applied`; the check does not fail → restore the file to its pre-edit content, `result passes`, `issue`, and say the check passed on the past mistake; the check cannot run → `result pending`, `issue`, with the proof command as the issue draft's done check.
- Step 2: the retro file list names `## Transcripts` (one item per transcript, path in backticks first), `## Findings` (the `### F<n> [<Severity>] <Signal>: <title>` heading, a `**Rung:**` line, a `**Disposition:**` line holding only `applied`, `refreshed`, `issue`, `dismissed`, or `deferred`, and a dismissal's reason on a `**Reason:**` line), and `## Rule table changes` (rows added or replaced, or `none`). **Rule table.** replaces the rule's row in `.writ/retros/rule-enforcers.md` or adds one for each `applied` or `refreshed` finding whose rung is not `none`, creates the file with `# Rule-to-Enforcer Table` and the six-column header when it is absent, sets Since to `<retro file name> F<n>` (example `2026-10-29-spec-x.md F1`), and changes nothing under `--report-only`. **Check the record.** runs `python3 scripts/retro-check.py --retro <file>`, corrects and re-runs once on `fail`, and puts a second `fail` or an `unverifiable` verdict in the final report with its reason lines; the environment edits stay.
- Step 3: `2 passed, 9 deselected`.

**Implementation Reference:** Story 3 — Files: `commands/retro.md` (§ Step 6, § Step 8)

**Status:** [ ] Pass  [ ] Fail

**Notes:**

---

### Scenario 17: Step 3 renames the command signal and counts unenforced rules, and Step 4 reads the table first

**Source:** Acceptance Criteria (AC-3.3) — Story 3; Must Include 4; DEV-012
**Feature:** none
**Verification:** human — no recipe

**Preconditions:**
- Setup block pasted; `reset` prints nothing.

**Steps:**
1. `sed -n '/^### Step 3:/,/^### Step 5:/p' "$CL/commands/retro.md" | grep -n 'Writ command defect\|counts on its own\|rule-enforcers\|no rules are tabled\|did not hold\|Drop single'`
2. `pt scripts/tests/test_retro_fix_ladder.py -q -k "step3 or step4" 2>&1 | tail -1`

**Expected Result:**
- Step 1, in this order: the `**Writ command defect**` signal row; the line "A user correction or mistake against a rule whose enforcer is `none` in the rule table counts on its own, as a Repeated mistake. Keep single corrections and mistakes until Step 4 has read the table."; the line "Before ranking, read `.writ/retros/rule-enforcers.md` if it exists. If it does not, say no rules are tabled yet."; and one paragraph that holds **fix did not hold** and **enforcer did not hold** (raise one level, name the row, "even for a single event"; for an enforcer of `none` the ladder proposes one) and ends "Drop single user corrections and mistakes that match no row." (DEV-012).
- Step 2: `2 passed, 9 deselected`.

**Status:** [ ] Pass  [ ] Fail

**Notes:**

---

### Scenario 18: The friction-signal remnants are gone, the Step 7 pins stay, and the file fits its budget

**Source:** Acceptance Criteria (AC-3.4) — Story 3; Must Include 6; Success Criteria (third bullet)
**Feature:** none
**Verification:** human — no recipe

**Preconditions:**
- Setup block pasted; `reset` prints nothing.

**Steps:**
1. `(cd "$CL" && grep -c -e 'signals.jsonl' -e 'signal.py' -e 'ADR-025' -e '--friction' -e 'Writ friction' commands/retro.md plugins/writ/commands/retro.md cursor/plugin/commands/retro.md)`
2. `sed -n '/^### Step 7:/,/^### Step 8:/p' "$CL/commands/retro.md" | grep -o 'read-only\|mutates no knowledge file' | sort -u`
3. `wc -c < "$CL/commands/retro.md"; grep -n 'No transcripts found' "$CL/commands/retro.md"`
4. `(cd "$CL" && python3 scripts/gen-platform-trees.py --check | head -1)`
5. `pt scripts/tests/test_retro_fix_ladder.py scripts/tests/test_governor_mutation.py -q 2>&1 | tail -1`

**Expected Result:**
- Step 1: `:0` after each of the three file names.
- Step 2: `mutates no knowledge file` and `read-only`.
- Step 3: `19986` (under 24,960; Story 3 grew it from 14,135), then one line: the Error Handling row `| No transcripts found | Print the locations searched and offer `--session <path>` |`, with no ADR-025 clause.
- Step 4: `pass`.
- Step 5: no `failed`. `test_governor_mutation.py` pads `commands/retro.md` by 12,000 bytes and still treats the clean file as compliant at the new size.

**Status:** [ ] Pass  [ ] Fail

**Notes:**

---

### Scenario 19: The frontmatter keeps its description and adds the proof and retro-check exit criteria

**Source:** Acceptance Criteria (AC-3.5) — Story 3; DEV-013
**Feature:** none
**Verification:** human — no recipe

**Preconditions:**
- Setup block pasted; `reset` prints nothing.

**Steps:**
1. `sed -n '2,13p' "$CL/commands/retro.md"`
2. `diff <(git -C "$CL" show e32d567^:commands/retro.md | grep '^description:') <(grep '^description:' "$CL/commands/retro.md") && echo "description unchanged"`
3. `pt scripts/tests/test_retro_fix_ladder.py -q -k frontmatter 2>&1 | tail -1`

**Expected Result:**
- Step 1: `outcome` names "each mistake finding fixed at the highest rung that works" and "a retro file and rule table the next run reads". `exit_criteria` has five items: the three earlier ones, then "every mistake finding names its rung and the higher rungs it passed over, and every finding fixed at architecture, types, lint, or test cites a proof run against a real past mistake", then "python3 scripts/retro-check.py --retro <retro file> printed pass, or its reason lines are in the run's final report" (no backticks, like every other `exit_criteria` line; DEV-013).
- Step 2: `description unchanged`.
- Step 3: `1 passed, 10 deselected`.

**Status:** [ ] Pass  [ ] Fail

**Notes:**

---

### Scenario 20: Proof outcomes route as the ladder rules say, and the checker guards each record

**Source:** Error Map "`/retro` Step 6 proof run" (check passes on the mistake; check cannot run) — Story 3; Shadow Path `/retro` ladder finding (Upstream Error); State Catalog "Proof fails to fail", "Proof cannot run", "Docs rung chosen"; Business Rule 7
**Feature:** none
**Verification:** human — no recipe

**Preconditions:**
- Setup block pasted.

**Steps:**
1. `sed -n '/^\*\*Proof run\.\*\*/,/^### Step 7:/p' "$CL/commands/retro.md"; grep -n '^| Proof' "$CL/commands/retro.md"`
2. Records for the three Step 6 outcomes:
   ```bash
   mkd passes_issue 's/result fails$/result passes/; s/^\*\*Disposition:\*\* applied$/**Disposition:** issue/'
   mkd pending_issue 's/result fails$/result pending/; s/^\*\*Disposition:\*\* applied$/**Disposition:** issue/'
   mkd pending_applied 's/result fails$/result pending/'
   for d in passes_issue pending_issue pending_applied; do echo "== $d"; rc --retro "$F/$d/2026-10-29-uat.md" --repo "$G" | sed -n '1,2p'; done
   ```
3. A docs-rung finding with no proof:
   ```bash
   mkdir -p "$F/docs"; printf '## Transcripts\n\n## Findings\n\n### F1 [High] Stale guidance: README names a removed flag\n**Rung:** docs\n**Ladder:** architecture: no (not a boundary); types: no (not a type); lint: no (prose, not code); test: no (no behavior to test); docs: yes\n**Disposition:** applied\n' > "$F/docs/2026-10-29-uat.md"
   printf '# Rule-to-Enforcer Table\n\n| Rule | Written in | Enforcer | Rung | Proof | Since |\n|---|---|---|---|---|---|\n| README names only flags that exist | `README.md` | none | docs | — | 2026-10-29-uat.md F1 |\n' > "$F/docs/rule-enforcers.md"
   rc --retro "$F/docs/2026-10-29-uat.md"; echo "exit $?"
   ```

**Expected Result:**
- Step 1: the three outcome bullets (fails → `applied`; does not fail → restore, `result passes`, `issue`; cannot run → `result pending`, `issue`, proof command as the done check), and two Error Handling rows: `Proof check does not fail on the mistake` and `Proof cannot run`.
- Step 2: `passes_issue`: `pass` and a pass summary. `pending_issue`: `pass` and a pass summary. `pending_applied`: `fail` and `reason: proof_not_failing F1`. A finding recorded `applied` must carry `result fails`; `issue` allows `passes` or `pending`.
- Step 3: `pass`, `retro-check: pass (1 findings, 1 table rows, 0 reasons)`, `exit 0`. A docs-rung finding passes over every higher rung with a reason, needs no Proof, and its table row has Enforcer `none` and Proof `—`.
- The plan does not force a live check to miss or a check tool to be missing; these are the records Step 6 writes in those cases.

**Status:** [ ] Pass  [ ] Fail

**Notes:**

---

### Scenario 21: A hand-edited table fails the check with reason lines that name the problem

**Source:** Error Map "`/retro` Step 8 retro-check" (`fail` twice) — Story 3; Edge Case "Rule table edited by hand"; State Catalog "`retro-check.py` prints `fail`"; DEV-002
**Feature:** none
**Verification:** human — no recipe

**Preconditions:**
- Setup block pasted.

**Steps:**
1. `grep -n '^\*\*Check the record\.\*\*\|^| Rule table malformed' "$CL/commands/retro.md"`
2. `mkd handedit 's/^$//'; sed -i '' 's/^| Rule | Written in |/| Rule | Source |/' "$F/handedit/rule-enforcers.md"; rc --retro "$F/handedit/2026-10-29-uat.md" --repo "$G"; echo "exit $?"`
3. `mkd handrow 's/^$//'; sed -i '' 's/| none | docs | — |/| none | docs | n\/a |/' "$F/handrow/rule-enforcers.md"; rc --retro "$F/handrow/2026-10-29-uat.md" --repo "$G"; echo "exit $?"`

**Expected Result:**
- Step 1: the **Check the record.** paragraph (re-run once; a second `fail` or an `unverifiable` verdict goes in the final report with its reason lines; the environment edits stay) and the Error Handling row: read a malformed table as is, put the `retro-check.py` reason lines in the final report, and leave rows this run did not add or replace unchanged.
- Step 2: `fail`, `reason: table_header`, `retro-check: fail (2 findings, 2 table rows, 1 reasons)`, `exit 1`. No `table_row_missing F1` line: with a wrong header, rows are not read (DEV-002).
- Step 3: `fail`, `reason: table_unenforced_rung row 2`, `retro-check: fail (2 findings, 2 table rows, 1 reasons)`, `exit 1`.
- These are the reason lines a run carries into its final report when its second check fails on a table row it did not write.

**Status:** [ ] Pass  [ ] Fail

**Notes:**

---

### Scenario 22: Live — with no rule table yet, the first applied ladder finding creates it

**Source:** Shadow Path `/retro` ladder finding (Nil Input) — Story 3; Error Map "`/retro` Step 8 table update" (table missing); State Catalog "No table yet"; Edge Case "Project with no `.writ/retros/` yet"; DEV-011
**Feature:** none
**Verification:** human — no recipe

**Preconditions:**
- Setup block pasted. `uvx ruff --version` prints a version.
- `ls "$FB/.writ"` prints only `docs`.
- `echo "$FB.jsonl"`; copy the printed transcript path.
- `live "$FB"` running in a new session.

**Steps:**
1. `/retro --session <the transcript path>`
2. Read the findings. At the question for the first print() finding, choose **Apply**. If more findings name the same rule, note how they are offered.
3. Read to the end of the run.
4. In the first shell: `git -C "$FB" status --short; T="$FB/.writ/retros/rule-enforcers.md"; head -1 "$T"; grep -n '^|' "$T"; R=$(ls "$FB"/.writ/retros/*.md | grep -v '/rule-enforcers.md$'); grep -n '^### F\|^\*\*Disposition:\|^\*\*Reason:\|^## Rule table changes' "$R"`
5. `python3 "$FB/scripts/retro-check.py" --retro "$R" --repo "$FB"; echo "exit $?"`

**Expected Result:**
- Step 2: before ranking, the run says no rules are tabled yet. The three corrections in `app.py`, `cli.py`, and `worker.py` produce a `[High]` ladder finding (Repeated mistake or User correction) with `**Rung:** lint`, a Ladder `architecture: no (<reason>); types: no (<reason>); lint: yes`, a Target in `ruff.toml` that adds `T201`, a Proof line with `result pending`, and Route `apply`. Apply is offered on the first finding that names the rule only; any later finding for the same rule is recorded `dismissed` with `**Reason:** same rule as F<n>` (DEV-011).
- Step 3: the run edits `ruff.toml`, runs the proof against the commit that added `print("starting")` without checking it out, reports that the check fails, records `applied`, writes the retro file and the table, and reports `pass` from `retro-check.py`. It does not commit.
- Step 4: `git status` shows only ` M ruff.toml` and `?? .writ/retros/`. The table's first line is `# Rule-to-Enforcer Table`; its `|` lines are the header `| Rule | Written in | Enforcer | Rung | Proof | Since |`, the delimiter, and one row for the print() rule with Rung `lint`, Proof `<sha>: fails`, and Since `<retro file name> F1`. The retro file shows `**Disposition:** applied` for the applied finding, a `**Reason:**` line under any dismissed one, and `## Rule table changes`.
- Step 5: `pass`, `retro-check: pass (<n> findings, 1 table rows, 0 reasons)`, `exit 0`.

**Status:** [ ] Pass  [ ] Fail

**Notes:**

---

### Scenario 23: A second finding on an already-tabled rule is dismissed with its reason on a Reason line

**Source:** Edge Case "Two findings name the same rule" — Story 3; DEV-011
**Feature:** none
**Verification:** human — no recipe

**Preconditions:**
- Setup block pasted.

**Steps:**
1. `grep -n 'same rule as\|Reason:' "$CL/commands/retro.md"`
2. Write a retro file where F2 names F1's rule:
   ```bash
   mkdir -p "$F/same" && cp "$F/ok/rule-enforcers.md" "$F/same/" && printf '## Transcripts\n\n## Findings\n\n### F1 [High] Repeated mistake: print() in app.py\n**Rung:** lint\n**Ladder:** architecture: no (one package); types: no (a type checker does not flag it); lint: yes\n**Proof:** mistake %s; check `ruff check app.py`; result fails\n**Disposition:** applied\n\n### F2 [High] User correction: print() in cli.py\n**Rung:** lint\n**Ladder:** architecture: no (one package); types: no (a type checker does not flag it); lint: yes\n**Proof:** mistake %s; check `ruff check cli.py`; result pending\n**Disposition:** dismissed\n**Reason:** same rule as F1\n' "$GSHA" "$GSHA" > "$F/same/2026-10-29-uat.md"
   rc --retro "$F/same/2026-10-29-uat.md" --repo "$G"; echo "exit $?"
   ```
3. `sed -i '' 's/^\*\*Disposition:\*\* dismissed$/**Disposition:** dismissed (same rule as F1)/; /^\*\*Reason:\*\*/d' "$F/same/2026-10-29-uat.md"; rc --retro "$F/same/2026-10-29-uat.md" --repo "$G"; echo "exit $?"`

**Expected Result:**
- Step 1: Step 6's "When two findings name the same rule, offer Apply on the first only. Record the second as `dismissed` with the reason `same rule as F<n>`; it gets no table row." and Step 8's "a dismissal's reason goes on a `**Reason:**` line".
- Step 2: `pass`, `retro-check: pass (2 findings, 2 table rows, 0 reasons)`, `exit 0`. The table has one row for the rule, and F2 needs none.
- Step 3: `fail`, `reason: disposition_invalid F2 dismissed (same rule as F1)`, `exit 1`. A reason written on the Disposition line fails the check, which is why it has its own line.

**Status:** [ ] Pass  [ ] Fail

**Notes:**

---

### Scenario 24: Live — a report-only run marks a mistake against an enforced rule and changes nothing

**Source:** Edge Case "`--report-only` run" — Story 3; State Catalog "Mistake against an enforced rule"; Must Include 4; Business Rule 7
**Feature:** none
**Verification:** human — no recipe

**Preconditions:**
- Setup block pasted.
- `grep 'print()' "$FD/.writ/retros/rule-enforcers.md"` shows Enforcer `` `uvx ruff check .` ``, Rung `lint`, Proof `<sha>: fails`; `grep T201 "$FD/ruff.toml"` shows `T201` selected.
- `shasum "$FD/.writ/retros/rule-enforcers.md" "$FD/ruff.toml" "$FD/CLAUDE.md" > "$W/fd-before.txt"; echo "$FD.jsonl"`; copy the printed transcript path.
- `live "$FD"` running in a new session.

**Steps:**
1. `/retro --session <the transcript path> --report-only`
2. Read to the end of the run. No question should be asked.
3. In the first shell: `git -C "$FD" status --short; shasum -c "$W/fd-before.txt"; R=$(ls "$FD"/.writ/retros/*.md | grep -v '/rule-enforcers.md$'); grep -n 'did not hold\|^### F\|^\*\*Proof:\|^\*\*Disposition:' "$R"; grep -A2 '^## Rule table changes' "$R"`
4. `python3 "$FD/scripts/retro-check.py" --retro "$R" --repo "$FD"; echo "exit $?"`

**Expected Result:**
- Step 2: the run reads the table. The print() finding is marked **enforcer did not hold**, names the table row (`uvx ruff check .`), and is `[Critical]`: one level above the High a correction or repeated mistake carries, even though it happened once. No Apply question appears.
- Step 3: `git status` shows only `?? .writ/retros/<today>-<slug>.md`. `shasum -c` prints `OK` for all three files. The finding's heading reads `[Critical]`, any Proof line reads `result pending`, every `**Disposition:**` is `deferred`, and `## Rule table changes` is followed by `none`.
- Step 4: `pass` and `exit 0`.

**Status:** [ ] Pass  [ ] Fail

**Notes:**

---

### Scenario 25: Live — a single correction against an unenforced rule becomes a lint check proven on the past commit

**Source:** Experience Design Journey and Moment of Truth — Story 3; State Catalog "Mistake against an unenforced rule"; Shadow Path `/retro` ladder finding (Happy Path); Must Include 2 to 4; Edge Case "Legacy retro file without Rung lines"; Business Rules 5, 8, 9
**Feature:** none
**Verification:** human — no recipe

**Preconditions:**
- Setup block pasted. `uvx ruff --version` prints a version.
- The fixture's lint config misses the mistake and rule `T201` catches it:
  ```bash
  A=$(git -C "$FA" log --format=%h -1 --grep='^feat: add startup lines'); git -C "$FA" show "$A":app.py > "$W/a.py"; (cd "$FA" && uvx ruff check -q --config ruff.toml "$W/a.py" > /dev/null; echo "current config: exit $?"; uvx ruff check -q --config ruff.toml --extend-select T201 "$W/a.py" > /dev/null; echo "with T201: exit $?")
  ```
  prints `current config: exit 0` and `with T201: exit 1`.
- `cat "$FA/.writ/retros/rule-enforcers.md"` shows the print() rule with Enforcer `none`, Rung `docs`, Proof `—`, Since `seed`.
- `shasum "$FA/app.py" "$FA/.writ/retros/2026-03-15.json" > "$W/fa-before.txt"; git -C "$FA" rev-parse HEAD > "$W/fa-head.txt"; echo "$FA.jsonl"`; copy the printed transcript path.
- `live "$FA"` running in a new session.

**Steps:**
1. `/retro --session <the transcript path>`
2. Read the findings. At the question for the print() finding, choose **Apply**.
3. Read to the end of the run.
4. In the first shell: `git -C "$FA" status --short; git -C "$FA" diff ruff.toml | grep '^[-+]select'; R=$(ls "$FA"/.writ/retros/*.md | grep -v '/rule-enforcers.md$'); grep -n '^## \|^### F\|^\*\*Rung:\|^\*\*Ladder:\|^\*\*Proof:\|^\*\*Disposition:' "$R"; grep -n 'print()' "$FA/.writ/retros/rule-enforcers.md"`
5. `python3 "$FA/scripts/retro-check.py" --retro "$R" --repo "$FA"; echo "exit $?"; P=$(grep -o 'mistake [0-9a-f]\{7,40\}' "$R" | head -1 | cut -d' ' -f2); git -C "$FA" log --format='%h %s' -1 "$P"; git -C "$FA" worktree list | wc -l; shasum -c "$W/fa-before.txt"; diff "$W/fa-head.txt" <(git -C "$FA" rev-parse HEAD) && echo "no commit"`

**Expected Result:**
- Step 2: before ranking, the run says it read `.writ/retros/rule-enforcers.md` and that the print() rule's enforcer is `none`. One finding covers the mistake as `[High] Repeated mistake`: a single correction counts because the rule is unenforced. It names the table row and carries `**Rung:** lint`, `**Ladder:** architecture: no (<reason>); types: no (<reason>); lint: yes`, a Target in `ruff.toml` that adds `T201`, ``**Proof:** mistake <ref>; check `<command>`; result pending``, and `**Route:** apply`, with Apply labelled `(Recommended)`. The ref is the `feat: add startup lines` commit (a transcript path exactly as listed under `## Transcripts` is also valid), and the check command runs ruff with the project's `ruff.toml`.
- Step 3: the run shows a diff adding `"T201"` to `select`, runs the proof against the past commit in a temporary copy or detached worktree (not a checkout), reports that the check fails on it, and records `result fails` and `applied`. It writes the retro file, updates the table, runs `python3 scripts/retro-check.py --retro <file>`, and reports `pass`. It does not commit. This is the moment of truth: the rule is now a check that would have caught the original mistake.
- Step 4: `git status` shows exactly ` M .writ/retros/rule-enforcers.md`, ` M ruff.toml`, and `?? .writ/retros/<today>-<slug>.md`. The diff's `+select` line gains `"T201"`. The retro file has `## Transcripts`, `## Findings`, the F1 heading with its Rung, Ladder, Proof (`result fails`), and `**Disposition:** applied` lines, and `## Rule table changes`. The table has exactly one line for the print() rule: Enforcer a backticked ruff command or `ruff.toml`, Rung `lint`, Proof `<sha>: fails`, Since `<retro file name> F1`. The `none` row was replaced, not kept beside it.
- Step 5: `pass`, `retro-check: pass (<n> findings, 1 table rows, 0 reasons)`, `exit 0`; the proof SHA resolves to `feat: add startup lines` (if the ref is a transcript path, `P` is empty and the log line is the latest commit; check the path against `## Transcripts` instead); `1` worktree; `OK` for `app.py` and the legacy `2026-03-15.json`; `no commit`.
- If the run instead reports that the check passed on the past mistake and records `issue`, the proof ran without the edited config. Mark Fail.

**Implementation Reference:** Story 3 — Files: `commands/retro.md` (Steps 3 to 6 and 8), `scripts/retro-check.py`

**Status:** [ ] Pass  [ ] Fail

**Notes:**

---

## Story 4: /refresh-command Execution-Failure and Used-Skill Criteria

### Scenario 26: Phase 3 checks for covered guidance and for skill targets before any proposal

**Source:** Acceptance Criteria (AC-4.1) — Story 4; Business Rules 13, 14; DEV-008
**Feature:** none
**Verification:** human — no recipe

**Preconditions:**
- Setup block pasted; `reset` prints nothing.

**Steps:**
1. `sed -n '/^## Phase 3:/,/^\*\*For each proposal/p' "$CL/commands/refresh-command.md"`
2. `grep -n 'For a skill amendment, the affected section' "$CL/commands/refresh-command.md"`
3. `pt scripts/tests/test_refresh_command_criteria.py -q -k "phase3 or covered or unused_skill or skill_section" 2>&1 | tail -1`

**Expected Result:**
- Step 1: a `**Covered already?**` paragraph before the five required fields: search the command file and each `skills/<name>/SKILL.md` it names for text that already requires the skipped behavior; a covered signal is an execution failure; propose no rule text and do not move, repeat, or reword the guidance; record it under `**Rejected:**` with reason `execution failure` and the covering section; suggest `/retro` if it recurs (DEV-008). Then a `**Skill targets**` paragraph: a proposal may amend `skills/<name>/SKILL.md` only when the command file contains that path and the cited transcript is readable here and shows a read of that path or an invocation of the skill by name; an unreadable transcript cannot show use; otherwise reject with `skill not used`, naming the skill and the transcript.
- Step 2: ``For a skill amendment, the affected section reads `skills/<name>/SKILL.md → "<section>"`.``
- Step 3: `5 passed` with a deselected count.

**Implementation Reference:** Story 4 — Files: `commands/refresh-command.md` (§ Phase 3), `scripts/tests/test_refresh_command_criteria.py`

**Status:** [ ] Pass  [ ] Fail

**Notes:**

---

### Scenario 27: Step 4.1a lints skill amendments, and Step 4.2 logs all four reason tokens

**Source:** Acceptance Criteria (AC-4.2) — Story 4; Business Rule 15; DEV-006, DEV-007
**Feature:** none
**Verification:** human — no recipe

**Preconditions:**
- Setup block pasted; `reset` prints nothing.

**Steps:**
1. `sed -n '/^### Step 4.1a:/,/^\*\*Structural Tier 2/p' "$CL/commands/refresh-command.md"`
2. `sed -n '/^\*\*Rejected:\*\*$/,/^\*\*Target file:\*\*/p' "$CL/commands/refresh-command.md"`
3. `grep -n 'to the command file or skill' "$CL/commands/refresh-command.md"`
4. `pt scripts/tests/test_refresh_command_criteria.py -q -k "41a or step_42" 2>&1 | tail -1`

**Expected Result:**
- Step 1: the base gate `bash scripts/eval.sh --check=refresh-evidence`, then a bullet: a skill amendment also runs `bash scripts/lint-skill.sh skills/<name>/SKILL.md` with the diff applied, and on line 1 `fail` the file is restored and the amendment rejected with reason `eval failed` (DEV-007).
- Step 2: four bullets, `reason: no evidence`, `reason: eval failed`, `reason: execution failure (covered by commands/[command].md → "[section]")`, `reason: skill not used (skills/<name>/SKILL.md; transcript <id>)`, then `**Scope:** Local only` and `**Target file:** commands/[command].md[, skills/<name>/SKILL.md]`.
- Step 3: Step 4.1 applies the diff "to the command file or skill" (DEV-006).
- Step 4: `6 passed` with a deselected count.

**Status:** [ ] Pass  [ ] Fail

**Notes:**

---

### Scenario 28: The frontmatter and Completion name all four tokens, and the description is unchanged

**Source:** Acceptance Criteria (AC-4.3) — Story 4
**Feature:** none
**Verification:** human — no recipe

**Preconditions:**
- Setup block pasted; `reset` prints nothing.

**Steps:**
1. `sed -n '2,11p' "$CL/commands/refresh-command.md"`
2. `diff <(git -C "$CL" show 87493ae^:commands/refresh-command.md | grep '^description:') <(grep '^description:' "$CL/commands/refresh-command.md") && echo "description unchanged"`
3. `sed -n '/^## Completion/,/^---$/p' "$CL/commands/refresh-command.md"`
4. `pt scripts/tests/test_refresh_command_criteria.py -q -k "description or exit_criteria or completion" 2>&1 | tail -1`

**Expected Result:**
- Step 1: the first `exit_criteria` line reads "every amendment written to commands/<name>.md or to a skill it read cites a transcript ID or path plus a short observable signal…"; the third names "no evidence, eval failed, execution failure, or skill not used". `outcome` is unchanged (Story 4 WWB decision 4).
- Step 2: `description unchanged`.
- Step 3: the success sentence covers "commands/<name>.md or … a skill it read"; the next paragraph lists "no evidence, eval failed, execution failure, or skill not used"; the terminal constraint reads "This command improves one command file, and the skills that run read, from evidence."
- Step 4: `11 passed` with a deselected count.

**Status:** [ ] Pass  [ ] Fail

**Notes:**

---

### Scenario 29: The evidence validator accepts the two new tokens and still rejects an unknown one

**Source:** Acceptance Criteria (AC-4.4) — Story 4; Success Criteria (fourth bullet)
**Feature:** none
**Verification:** human — no recipe

**Preconditions:**
- Setup block pasted; `reset` prints nothing.

**Steps:**
1. `(cd "$CL" && python3 scripts/eval-refresh-evidence.py > "$W/ev.txt"; echo "exit $?"; grep -c '^PASS' "$W/ev.txt"; grep -c '^FAIL' "$W/ev.txt"; grep 'rejected-' "$W/ev.txt")`
2. `(cd "$CL" && python3 -c 'import importlib.util as u; s = u.spec_from_file_location("e", "scripts/eval-refresh-evidence.py"); m = u.module_from_spec(s); s.loader.exec_module(m); print(m.validate_entry(m.rejected_with_reason_entry("seemed wrong")))')`

**Expected Result:**
- Step 1: `exit 0`, `25`, `0`, then five `PASS` lines: `rejected-lacking-evidence-is-valid-record`, `rejected-missing-reason-fails`, `rejected-execution-failure-is-valid-record`, `rejected-skill-not-used-is-valid-record`, `rejected-unknown-token-fails`.
- Step 2: `(False, 'rejected: candidate missing reason token (no evidence / eval failed / execution failure / skill not used)')`. A rejection with no recognized token is still refused, and the message lists all four.

**Implementation Reference:** Story 4 — Files: `scripts/eval-refresh-evidence.py` (`REASON_TOKENS`, `_REASON_RE`, the three new scenarios)

**Status:** [ ] Pass  [ ] Fail

**Notes:**

---

### Scenario 30: The refresh-evidence gate passes, the command fits its budget, and the full suite and quality gate are clean

**Source:** Acceptance Criteria (AC-4.5) — Story 4; Success Criteria (fifth bullet); also the full-suite parts of every story's verification tasks
**Feature:** none
**Verification:** human — no recipe

**Preconditions:**
- Setup block pasted; `reset` prints nothing. Run outside any sandbox (eval runs `git init` in a temp dir). About five minutes. Run pytest alone, not beside eval or the bash tests.

**Steps:**
1. `(cd "$CL" && bash scripts/eval.sh --check=refresh-evidence > /dev/null; echo "exit $?")`
2. `wc -c < "$CL/commands/refresh-command.md"`
3. `pt scripts/tests/test_refresh_command_criteria.py -q 2>&1 | tail -1`
4. `pt -q 2>&1 | tail -1`
5. `(cd "$CL" && for t in scripts/tests/test_*.sh; do bash "$t" > /dev/null 2>&1 || echo "FAIL $t"; done; echo "bash loop done")`
6. `(cd "$CL" && bash scripts/eval.sh > /dev/null; echo "exit $?"); tail -2 "$(ls -t "$CL"/.writ/state/eval-*.md | head -1)"`
7. `(cd "$CL" && python3 scripts/gen-platform-trees.py --check | head -1)`
8. `reset`

**Expected Result:**
- Step 1: `exit 0`.
- Step 2: `23187`, under 24,960.
- Step 3: `45 passed`.
- Step 4: no `failed` in the summary (Story 3 recorded `3641 passed, 3 skipped`; later merges on the phase branch may change the counts).
- Step 5: only `bash loop done`; no `FAIL` line.
- Step 6: `exit 0`, then `- Findings: 0` and `- Run errors: 0`.
- Step 7: `pass`.
- Step 8: prints nothing.

**Status:** [ ] Pass  [ ] Fail

**Notes:**

---

### Scenario 31: A skill amendment that fails the boundary lint is the `eval failed` case

**Source:** Error Map "`/refresh-command` skill target" (`lint-skill.sh` line 1 `fail`) — Story 4; DEV-006, DEV-007
**Feature:** none
**Verification:** human — no recipe

**Preconditions:**
- Setup block pasted; `reset` prints nothing.

**Steps:**
1. ``grep -n '^| `eval failed`' "$CL/.writ/docs/refresh-log-format.md"``
2. `(cd "$CL" && bash scripts/lint-skill.sh skills/plain-prose/SKILL.md | head -1)`
3. `printf '\n/create-spec is how to start.\n' >> "$CL/skills/plain-prose/SKILL.md"; (cd "$CL" && bash scripts/lint-skill.sh skills/plain-prose/SKILL.md > "$W/lint.txt"; echo "exit $?"; head -2 "$W/lint.txt"); reset`

**Expected Result:**
- Step 1: the `eval failed` row names `bash scripts/lint-skill.sh` for a skill amendment (DEV-006).
- Step 2: `pass`.
- Step 3: `exit 1`, `fail`, then a `reason:` line naming `skills/plain-prose/SKILL.md`, a line number, and `Slash command`. `reset` prints nothing. This line 1 `fail` is what Step 4.1a turns into a restore and an `eval failed` rejection (Scenario 27, Step 1).

**Status:** [ ] Pass  [ ] Fail

**Notes:**

---

### Scenario 32: Live — `/refresh-command` logs a covered signal as an execution failure and rejects an unproven skill target

**Source:** Shadow Path `/refresh-command` signal (Empty Input: already covered; Upstream Error: unreadable transcript) — Story 4; Error Map "`/refresh-command` skill target" (transcript not readable here); State Catalog "`/refresh-command` signal already covered" and "skill target not used"; DEV-008
**Feature:** none
**Verification:** human — no recipe

**Preconditions:**
- Setup block pasted; `reset` prints nothing.
- `grep -c 'skills/plain-prose/SKILL.md' "$CL/commands/retro.md"` prints at least `1`. `ls ~/.claude/projects/uat-missing/0000.jsonl` reports no such file.
- `live` running in a new session (in the clone).

**Steps:**
1. `/refresh-command retro`
2. When asked how `/retro` went, reply: `Two things. (1) In my last /retro run the agent wrote the retro file and never ran retro-check.py on it. (2) Add a rule to skills/plain-prose/SKILL.md: write every date as YYYY-MM-DD. The run where the agent wrote "Oct 28" in the retro file is transcript ~/.claude/projects/uat-missing/0000.jsonl.`
3. Confirm the signal summary. If any amendment is still proposed, choose Skip all and note what it was.
4. Read the final output. In the first shell: `git -C "$CL" status --short; git -C "$CL" diff -- .writ/refresh-log.md | grep '^+' | tail -20`
5. `(cd "$CL" && python3 -c 'import importlib.util as u; s = u.spec_from_file_location("e", "scripts/eval-refresh-evidence.py"); m = u.module_from_spec(s); s.loader.exec_module(m); t = open(".writ/refresh-log.md").read(); print(m.validate_entry("## " + t.split("\n## ")[-1]))')`
6. `reset`

**Expected Result:**
- Step 3: no amendment is written. Signal 1 is reported as already covered by `commands/retro.md` Step 8 (the **Check the record.** paragraph), an execution failure, with a suggestion to run `/retro` if it recurs. Signal 2 is rejected as `skill not used`: `commands/retro.md` names the skill's path, but the cited transcript cannot be read here.
- Step 4: `git status` shows only ` M .writ/refresh-log.md`. The new entry has a `## <today> — /retro refreshed` heading, an `**Amendments applied:** 0 of …` line, and a `**Rejected:**` list with `reason: execution failure (covered by commands/retro.md → "Step 8: Persist the Retro File")` or the Check the record paragraph named, and `reason: skill not used (skills/plain-prose/SKILL.md; transcript ~/.claude/projects/uat-missing/0000.jsonl)`. No transcript body or prompt text appears.
- Step 5: `(True, '')`.
- Step 6: prints nothing.

**Implementation Reference:** Story 4 — Files: `commands/refresh-command.md` (§ Phase 3, § Step 4.2), `.writ/docs/refresh-log-format.md`

**Status:** [ ] Pass  [ ] Fail

**Notes:**

---

## Pending Stories

None. All four stories are Completed ✅.
