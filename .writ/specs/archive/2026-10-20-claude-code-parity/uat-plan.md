# UAT Plan: Claude Code Parity

> **Generated:** 2026-10-21
> **Spec:** `.writ/specs/2026-10-20-claude-code-parity/`
> **Stories Covered:** 4 of 4 completed
> **Total Scenarios:** 31
> **Verification recipe:** does not apply. Writ has no running app, so no `.writ/docs/app-verification.md` was drafted, saved, or bound. Every scenario is `human — no recipe`. The `**Automated Test:**` line on each scenario names the committed test that already asserts the same behavior, if any.

## How to Use This Plan

1. Work through scenarios in order (they're grouped by story, ordered by priority)
2. For each scenario, follow the steps exactly as written
3. Mark Pass or Fail — add notes for any unexpected behavior
4. Scenarios marked Fail should be filed as issues or fed back to the spec
5. A feature passes UAT when all scenarios pass (or failures are accepted as known limitations)

**Conventions for this plan:**

- **Never run `install.sh`, `update.sh`, or `uninstall.sh` in the Writ repo.** `.claude/` and `.cursor/` there are symlinks into the source (Business Rule 14). Every install, update, and uninstall below runs from a committed copy at `$SRC` into a temp folder under `$W`.
- The generator, `eval.sh`, and the suites run in a clone at `$CL`. Scenarios that break a file on purpose do it in `$CL` and restore it with `git checkout`. `$REPO` is only read.
- Run the plan in `bash` on macOS (`shasum`, `sed -i ''`, `stat -f`), outside any sandbox. The steps run `git init` and `git commit` in temp folders. Do not use zsh: it expands some of the patterns below differently.
- Paste this setup block once per shell:

  ```bash
  REPO=/Users/asellke/Projects/writ          # the Writ checkout; read from, never installed into
  W=$(mktemp -d "${TMPDIR:-/tmp}/writ-uat-parity.XXXXXX")
  cd "$W"   # run every helper from the temp folder: an empty path then fails instead of writing to the Writ repo
  h()      { shasum -a 256 "$1" | cut -d' ' -f1; }
  digest() { (cd "$1" && find . -type f -exec shasum -a 256 {} + | LC_ALL=C sort | shasum -a 256 | cut -d' ' -f1); }
  gc()     { case "$1" in "$W"/?*) ;; *) echo "gc: '$1' is not under $W; refusing" >&2; return 1;; esac
             git -C "$1" -c user.name=t -c user.email=t@example.invalid add -A &&
             git -C "$1" -c user.name=t -c user.email=t@example.invalid commit -q -m "$2"; }
  # Committed copy of the working tree. install.sh, update.sh, and uninstall.sh run from here.
  SRC="$W/src"; mkdir -p "$SRC"
  (cd "$REPO" && tar --exclude=.git --exclude=.cursor --exclude=.claude --exclude=.codex \
     --exclude=.writ --exclude='.writ-lanes-*' --exclude=__pycache__ --exclude=.venv \
     --exclude=.pytest_cache -cf - .) | (cd "$SRC" && tar -xf -)
  mkdir -p "$SRC/.writ/docs" && cp "$REPO"/.writ/docs/*.md "$SRC/.writ/docs/"
  git -C "$SRC" init -q -b main && gc "$SRC" source
  # Clone of the committed repo: the generator and eval run here, and scenarios break it on purpose.
  CL="$W/clone"; git clone -q "$REPO" "$CL"
  # inst / upd / uninst <project> [flags]: Claude Code lifecycle runs from $SRC (update clones $UPSTREAM if set).
  inst()   { local p="$1"; shift; mkdir -p "$p" && (cd "$p" && bash "$SRC/scripts/install.sh" --platform claude --no-commit "$@"); }
  upd()    { local p="$1"; shift; (cd "$p" && WRIT_REPO="${UPSTREAM:-$SRC}" bash "$SRC/scripts/update.sh" --platform claude --no-commit "$@"); }
  uninst() { local p="$1"; shift; (cd "$p" && bash "$SRC/scripts/uninstall.sh" --platform claude --no-commit "$@"); }
  # part pre|inner|post FILE: the bytes before the start-marker line, between the markers, or after the end-marker line.
  part() { python3 -c 'import sys; w, p = sys.argv[1:3]; L = open(p, "rb").read().splitlines(True); B = [l.rstrip(b"\n").rstrip(b"\r") for l in L]; s = B.index(b"<!-- writ:start -->"); e = B.index(b"<!-- writ:end -->"); sys.stdout.buffer.write(b"".join({"pre": L[:s], "inner": L[s + 1:e], "post": L[e + 1:]}[w]))' "$1" "$2"; }
  # user_md FILE: hand-written CLAUDE.md with CRLF lines, trailing spaces, non-ASCII text, an @notes.md line, and no final newline.
  user_md() { printf '# My project\r\nKeep this line.   \r\n\nCafé ünïcödé — naïve\n@notes.md\nLast line, no newline' > "$1"; }
  ```

- Manifest: `.claude/.writ-manifest`, one `<sha256>  <path>` line per file. The Writ block's baseline is the line ending `CLAUDE.md.writ-block`.
- Expected output was observed on 2026-10-21 against `e3f4a42`, on the branch `phase/13-subtract-and-repair`. Temp paths, hashes, and counts that grow with the repo (32 manifest commands, 33 installed command files, 8 agents, 16 skills) will differ later. `<W>` in expected output stands for your `$W`.
- When done: `rm -rf "$W"`.
- **Automated Test line:** names the test in `scripts/tests/` (or the `eval.sh` check) that asserts the behavior, `partial` when a test covers part of it, or `none — manual only`. CI runs pytest, every bash test, and `eval.sh` on each PR.
- **Human in Claude Code:** Scenarios 22, 23, 28, and 30 need a person in an interactive Claude Code session. No test can run them. The shell steps in those scenarios only prepare and inspect the temp project.

## Coverage Summary

| Story | Status | Scenarios | Source Breakdown |
|-------|--------|-----------|-----------------|
| Story 1: Generate the CLAUDE.md Template from the Manifest | ✅ Covered | 8 | AC: 5, Errors: 1, Shadow: 1, Edge: 1 |
| Story 2: Install the System Instructions and Import Line on Claude Code | ✅ Covered | 9 | AC: 6, Errors: 1, Shadow: 1, Edge: 1 |
| Story 3: Correct the Claude Code Adapter | ✅ Covered | 6 | AC: 4, Errors: 1, Experience: 1 |
| Story 4: Keep CLAUDE.md User-Owned on Uninstall and Reinstall | ✅ Covered | 8 | AC: 4, Errors: 1, Edge: 1, Experience: 1, Success Criteria: 1 |

Error-map, shadow-path, edge-case, and state-catalog items that a scenario already exercises are folded into it and named on its **Source** line, not counted twice. Several error-map rows share one scenario where they share one setup (Scenarios 6 and 15). Scenario 31 checks the spec-level Success Criteria (all suites, 0 eval findings); it sits under Story 4 because that story landed last.

**Automated vs. manual:** 22 scenarios are asserted by a committed test, 5 partly, 4 need a person in Claude Code. See the table at the end.

---

## Story 1: Generate the CLAUDE.md Template from the Manifest

### Scenario 1: The generator writes one row per manifest command, every agent, and the import line

**Source:** Acceptance Criteria — Story 1 (AC-1.1); Shadow Path (Generator: happy); Experience Design (State: maintainer runs the generator)
**Feature:** none
**Verification:** human — no recipe
**Automated Test:** `scripts/tests/test_gen_claude_md.py` (`test_ac_1_1_*`)

**Preconditions:**
- Setup block pasted.

**Steps:**
1. Run the generator in the clone and check that the committed template did not change:
   ```bash
   cd "$CL" && python3 scripts/gen-claude-md.py; echo "exit $?"; git status --short claude-code/; echo "status checked"
   ```
2. Compare the rows with the manifest's command order, and the agents list with the agent files:
   ```bash
   cd "$CL"
   grep -c '^| `/' claude-code/CLAUDE.md
   diff <(grep -o '^| `/[a-z0-9-]*`' claude-code/CLAUDE.md | sed 's/^| `\///; s/`$//') \
        <(awk '/^commands:/{f=1;next} f&&/^[^ #]/{f=0} f&&/^  - name:/{print $3}' .writ/manifest.yaml) && echo "rows match manifest order"
   grep -c -e '^| `/implement-phase` ' -e '^| `/knowledge` ' -e '^| `/revert` ' claude-code/CLAUDE.md
   grep -n '^| `/revert` ' claude-code/CLAUDE.md
   diff <(grep -o '^- `writ-[a-z-]*\.md`' claude-code/CLAUDE.md | sed 's/^- `//; s/`$//') <(ls claude-code/agents/) && echo "agents match files"
   ```
3. Check the import line, the pipeline line, line endings, and the final newline:
   ```bash
   cd "$CL"
   grep -n '^@' claude-code/CLAUDE.md; awk 'NR<7 && /^```/' claude-code/CLAUDE.md | wc -l
   grep -n '^/plan-product' claude-code/CLAUDE.md
   grep -c $'\r' claude-code/CLAUDE.md; tail -c 2 claude-code/CLAUDE.md | od -An -c
   ```
4. Run the generator a second time and compare bytes with the committed file:
   ```bash
   cd "$CL" && python3 scripts/gen-claude-md.py >/dev/null; h claude-code/CLAUDE.md; git show HEAD:claude-code/CLAUDE.md | shasum -a 256 | cut -d' ' -f1
   ```

**Expected Result:**
- Step 1: `pass`, `gen-claude-md: pass (32 commands, 8 agents)`, `exit 0`, then only `status checked` (no changed file).
- Step 2: `32`; `rows match manifest order`; `3`; line 39, the `/revert` row, reads `` | `/revert` | `.claude/commands/revert.md` | Safely unwind a story or spec via a layered commit resolver with plan-before-mutate guards. | ``; `agents match files` (eight files, `writ-evaluator.md` among them).
- Step 3: `7:@.claude/system-instructions.md` and `0` (no code fence opens before it, and the line has no backticks); `64:/plan-product → /create-spec → /implement-spec → /verify-spec → /release`; `0` CR characters; the last two bytes are `s  \n` (one final newline).
- Step 4: the two hashes are equal.

**Status:** [x] Pass  [ ] Fail

**Notes:** The spec said seven agents. There are eight because `writ-visual-qa.md` landed from `2026-10-20-claude-agent-generator`; the generator reads the folder, so the count follows it (DEV-004).
- agent-run 2026-10-21 @ b850e66: `pass (32 commands, 8 agents)`, exit 0, no status change; `32` rows, `rows match manifest order`, `3`, `agents match files`; `7:@.claude/system-instructions.md`, `0`; `64:/plan-product …`; `0` CR; tail `s  \n`; step 4 hashes equal. The `/revert` row is line 38, not 39: the `/design` row is now `/writ-design` and sorts last (legitimate change).
- Setup: `$SRC` from `git archive b850e66` and `$CL` reset to `b850e66`, because main briefly carried a stray commit from another run (`a8aa8d8`) when the setup block ran.

**Implementation Reference:** Story 1 — `scripts/gen-claude-md.py` (write mode, temp file plus `os.replace`); `claude-code/CLAUDE.md` regenerated.

---

### Scenario 2: `--check` passes on the committed template and names a removed row or a stale byte

**Source:** Acceptance Criteria — Story 1 (AC-1.2); Error Map (`--check`: template absent)
**Feature:** none
**Verification:** human — no recipe
**Automated Test:** `scripts/tests/test_gen_claude_md.py` (`test_ac_1_2_*`)

**Preconditions:**
- Setup block pasted.

**Steps:**
1. `cd "$CL" && python3 scripts/gen-claude-md.py --check; echo "exit $?"`
2. Delete the `/revert` row and check:
   ```bash
   cd "$CL" && sed -i '' '/^| `\/revert` |/d' claude-code/CLAUDE.md
   python3 scripts/gen-claude-md.py --check; echo "exit $?"; git checkout -q claude-code/CLAUDE.md
   ```
3. Add a line at the end, rows intact:
   ```bash
   cd "$CL" && printf '\nhand edit\n' >> claude-code/CLAUDE.md
   python3 scripts/gen-claude-md.py --check; echo "exit $?"; git checkout -q claude-code/CLAUDE.md
   ```
4. Remove the template:
   ```bash
   cd "$CL" && mv claude-code/CLAUDE.md "$W/template.bak"
   python3 scripts/gen-claude-md.py --check; echo "exit $?"; mv "$W/template.bak" claude-code/CLAUDE.md; git status --short
   ```

**Expected Result:**
- Step 1: `pass`, `gen-claude-md: pass (32 commands, 8 agents)`, `exit 0`.
- Step 2: `fail`, exactly one `reason: missing revert`, `gen-claude-md: fail (1 missing, 0 extra)` as the last line, `exit 1`. No `stale` reason.
- Step 3: `fail`, `reason: stale claude-code/CLAUDE.md`, `gen-claude-md: fail (1 stale)`, `exit 1`.
- Step 4: `fail`, `reason: absent claude-code/CLAUDE.md`, `gen-claude-md: fail (1 absent)`, `exit 1`. `git status` prints nothing afterwards.

**Status:** [x] Pass  [ ] Fail

**Notes:**
- agent-run 2026-10-21 @ b850e66: step 1 `pass`, exit 0; step 2 one `reason: missing revert`, `fail (1 missing, 0 extra)`, exit 1; step 3 `reason: stale claude-code/CLAUDE.md`, `fail (1 stale)`, exit 1; step 4 `reason: absent claude-code/CLAUDE.md`, `fail (1 absent)`, exit 1; `git status` empty.

**Implementation Reference:** Story 1 — a row-set difference suppresses `stale`, so one removed row gives one reason (Implementation Decision 2).

---

### Scenario 3: Bad input stops the generator, and write mode leaves the template untouched

**Source:** Acceptance Criteria — Story 1 (AC-1.3); Error Map (Generator reads manifest; validates manifest; renders a purpose with `@`; checks pipeline); Shadow Path (Generator: nil input)
**Feature:** none
**Verification:** human — no recipe
**Automated Test:** `scripts/tests/test_gen_claude_md.py` (`test_ac_1_3_*`)

**Preconditions:**
- Setup block pasted.

**Steps:**
1. Missing manifest:
   ```bash
   cd "$CL"; T0=$(h claude-code/CLAUDE.md)
   mv .writ/manifest.yaml "$W/manifest.bak"; python3 scripts/gen-claude-md.py; echo "exit $?"; mv "$W/manifest.bak" .writ/manifest.yaml
   ```
2. Unknown flag:
   ```bash
   cd "$CL"; python3 scripts/gen-claude-md.py --bogus >"$W/s3.out" 2>"$W/s3.err"; echo "exit $?"; wc -c < "$W/s3.out"; cat "$W/s3.err"
   ```
3. A command with no `purpose`:
   ```bash
   cd "$CL"; sed -i '' '/^  - name: revert$/,/purpose:/{/purpose:/d;}' .writ/manifest.yaml
   python3 scripts/gen-claude-md.py; echo "exit $?"; [ "$(h claude-code/CLAUDE.md)" = "$T0" ] && echo "template unchanged"; git checkout -q .writ/manifest.yaml
   ```
4. A purpose with `@` outside backticks, then the same `@` inside backticks:
   ```bash
   cd "$CL"; sed -i '' 's/purpose: "Safely unwind a story/purpose: "Ask @team, then unwind a story/' .writ/manifest.yaml
   python3 scripts/gen-claude-md.py; echo "exit $?"; [ "$(h claude-code/CLAUDE.md)" = "$T0" ] && echo "template unchanged"; git checkout -q .writ/manifest.yaml
   sed -i '' 's/purpose: "Safely unwind a story/purpose: "Ask `@team`, then unwind a story/' .writ/manifest.yaml
   python3 scripts/gen-claude-md.py --check | head -2; git checkout -q .writ/manifest.yaml
   ```
5. A pipeline command missing from the manifest (rename `verify-spec`):
   ```bash
   cd "$CL"; sed -i '' 's/^  - name: verify-spec$/  - name: check-spec/; s|file: commands/verify-spec.md|file: commands/check-spec.md|' .writ/manifest.yaml
   python3 scripts/gen-claude-md.py; echo "exit $?"; [ "$(h claude-code/CLAUDE.md)" = "$T0" ] && echo "template unchanged"; git checkout -q .writ/manifest.yaml; git status --short
   ```

**Expected Result:**
- Step 1: `unverifiable`, `reason: manifest missing: .writ/manifest.yaml`, `gen-claude-md: unverifiable (inputs missing)`, `exit 0`.
- Step 2: `exit 2`, `0` bytes on stdout, then on stderr `usage: gen-claude-md.py [-h] [--check]` and `gen-claude-md.py: error: unrecognized arguments: --bogus`.
- Step 3: `fail`, `reason: manifest revert missing purpose`, `gen-claude-md: fail (1 manifest)`, `exit 1`, `template unchanged`.
- Step 4: `fail`, `reason: import-token revert`, `gen-claude-md: fail (1 import-token)`, `exit 1`, `template unchanged`. With the backticks: `fail` and `reason: stale claude-code/CLAUDE.md` (the purpose text changed, but the `@` inside a code span is accepted; no `import-token` reason).
- Step 5: `fail`, `reason: pipeline verify-spec`, `gen-claude-md: fail (1 pipeline)`, `exit 1`, `template unchanged`. `git status` prints nothing.

**Status:** [x] Pass  [ ] Fail

**Notes:**
- agent-run 2026-10-21 @ b850e66: step 1 `unverifiable`, `manifest missing`, exit 0; step 2 exit 2, `0` bytes, argparse usage and `unrecognized arguments: --bogus`; step 3 `manifest revert missing purpose`, exit 1; step 4 `import-token revert`, exit 1, backticked `@team` gives `stale` only; step 5 `pipeline verify-spec`, exit 1. `template unchanged` each time; `git status` empty.

**Implementation Reference:** Story 1 — the generator writes nothing when any `fail` reason exists.

---

### Scenario 4: The generator is dev-only and never ships to a project

**Source:** Acceptance Criteria — Story 1 (AC-1.4)
**Feature:** none
**Verification:** human — no recipe
**Automated Test:** `scripts/tests/test_gen_claude_md_not_shipped.sh`

**Preconditions:**
- Setup block pasted.

**Steps:**
1. Compare the three ship filters and call each with the generator's name:
   ```bash
   cd "$REPO"
   for f in install update unlink; do sed -n '/^is_shippable_script()/,/^}/p' scripts/$f.sh | shasum -a 256 | cut -c1-16; done
   for f in install update unlink; do
     bash -c 'eval "$(sed -n "/^is_shippable_script()/,/^}/p" "$1")"
       is_shippable_script gen-claude-md.py && echo "$2: gen-claude-md.py ships" || echo "$2: gen-claude-md.py dev-only"
       is_shippable_script gen-skill.sh && echo "$2: gen-skill.sh ships"' _ "scripts/$f.sh" "$f"
   done
   ```
2. Install into a temp project and look for the generator:
   ```bash
   P="$W/s4"; inst "$P" > "$W/s4.txt" 2>&1; echo "exit $?"
   ls "$P/scripts/gen-skill.sh" "$P/scripts/gen-claude-md.py"; grep -c 'gen-claude-md' "$P/.claude/.writ-manifest"
   ```
3. `grep -c 'gen-claude-md.py' "$REPO/.writ/docs/agent-cli-contract.md" "$REPO/commands/update-writ.md"`

**Expected Result:**
- Step 1: three equal hashes; for each of `install`, `update`, `unlink`: `gen-claude-md.py dev-only` and `gen-skill.sh ships`.
- Step 2: `exit 0`; `ls` lists `<W>/s4/scripts/gen-skill.sh` and reports `<W>/s4/scripts/gen-claude-md.py: No such file or directory`; manifest count `0`.
- Step 3: `.writ/docs/agent-cli-contract.md:1` and `commands/update-writ.md:1`. The contract doc's sentence reads "`gen-claude-md.py` is dev-only too: it builds `claude-code/CLAUDE.md` from `.writ/manifest.yaml`, which installed projects do not have."

**Status:** [x] Pass  [ ] Fail

**Notes:** The contract doc still says "Six dev-only scripts" and adds the generator in a separate sentence, because `test_harness_cuts.py` pins that wording (DEV-002).
- agent-run 2026-10-21 @ b850e66: three equal hashes `f21807b6718a45b9`; `gen-claude-md.py dev-only` and `gen-skill.sh ships` for install, update, unlink; install exit 0, `gen-skill.sh` present, `gen-claude-md.py: No such file or directory`, manifest count `0`; `agent-cli-contract.md:1`, `update-writ.md:1`, contract sentence matches.

**Implementation Reference:** Story 1 — `gen-claude-md.py` added to the dev-only arm of `is_shippable_script` in `scripts/install.sh`, `scripts/update.sh`, `scripts/unlink.sh`.

---

### Scenario 5: `eval.sh` fails when the template falls behind the manifest, and CI runs the check

**Source:** Acceptance Criteria — Story 1 (AC-1.5); Error Map (`--check`: command added, template not regenerated); Experience Design (States: maintainer adds a manifest command and forgets to regenerate; maintainer hand-edits the template)
**Feature:** none
**Verification:** human — no recipe
**Automated Test:** `scripts/tests/test_eval_claude_md.sh`

**Preconditions:**
- Setup block pasted. `eval.sh` runs `git init` in a temp folder; run outside any sandbox.

**Steps:**
1. Clean clone:
   ```bash
   cd "$CL" && bash scripts/eval.sh --check=claude-md --report="$W/s5-a.md" >/dev/null 2>&1; echo "exit $?"; sed -n '/^## claude-md/,$p' "$W/s5-a.md"
   ```
2. Delete the `/revert` row:
   ```bash
   cd "$CL" && sed -i '' '/^| `\/revert` |/d' claude-code/CLAUDE.md
   bash scripts/eval.sh --check=claude-md --report="$W/s5-b.md" >/dev/null 2>&1; echo "exit $?"; grep -e '^FAIL' -e '^- `' "$W/s5-b.md"; git checkout -q claude-code/CLAUDE.md
   ```
3. Add a command to the manifest without regenerating:
   ```bash
   cd "$CL" && python3 -c 'p = ".writ/manifest.yaml"; t = open(p).read(); open(p, "w").write(t.replace("commands:\n", "commands:\n  - name: uat-probe\n    file: commands/uat-probe.md\n    category: utility\n    purpose: \"Probe command added for UAT.\"\n", 1))'
   bash scripts/eval.sh --check=claude-md --report="$W/s5-c.md" >/dev/null 2>&1; echo "exit $?"; grep -e '^FAIL' -e '^- `' "$W/s5-c.md"; git checkout -q .writ/manifest.yaml
   ```
4. Hand-edit the template:
   ```bash
   cd "$CL" && printf '\nhand edit\n' >> claude-code/CLAUDE.md
   bash scripts/eval.sh --check=claude-md --report="$W/s5-d.md" >/dev/null 2>&1; echo "exit $?"; grep -e '^FAIL' -e '^- `' "$W/s5-d.md"; git checkout -q claude-code/CLAUDE.md; git status --short
   ```
5. Check registration and CI:
   ```bash
   cd "$CL"; sed -n '/^CHECKS=(/,/^)/p' scripts/eval.sh | tr -s ' \t' '\n\n' | grep -x -e codex-tomls -e claude-agents -e claude-md
   grep -n 'run: bash scripts/eval.sh' .github/workflows/eval.yml
   ```

**Expected Result:**
- Step 1: `exit 0`; the section reads `PASS` with the note `NOTE [claude-md]: gen-claude-md: pass (32 commands, 8 agents)`; `Findings: 0`.
- Step 2: `exit 1`; `FAIL (1 finding(s))`; one finding: `` - `claude-code/CLAUDE.md`: manifest command /revert is missing from the Claude Code template. _Remediation:_ Run python3 scripts/gen-claude-md.py and commit claude-code/CLAUDE.md. ``
- Step 3: `exit 1`; `FAIL (1 finding(s))`; one finding naming `/uat-probe` with the same remedy.
- Step 4: `exit 1`; `FAIL (1 finding(s))`; one finding: `` - `claude-code/CLAUDE.md`: gen-claude-md.py --check: stale claude-code/CLAUDE.md _Remediation:_ Run python3 scripts/gen-claude-md.py and commit claude-code/CLAUDE.md. `` `git status` prints nothing.
- Step 5: `codex-tomls`, `claude-agents`, `claude-md` in that order; `28:        run: bash scripts/eval.sh --report=eval-report.md`.

**Status:** [x] Pass  [ ] Fail

**Notes:** `claude-md` sits after `claude-agents`, not directly after `codex-tomls` as the technical spec said; `test_eval_claude_agents.sh` requires that order (DEV-001).
- agent-run 2026-10-21 @ b850e66: step 1 exit 0, `PASS`, `NOTE [claude-md]: gen-claude-md: pass (32 commands, 8 agents)`, `Findings: 0`; steps 2–4 exit 1, `FAIL (1 finding(s))` naming `/revert`, `/uat-probe`, and `--check: stale claude-code/CLAUDE.md`, each with the expected remedy; order `codex-tomls`, `claude-agents`, `claude-md`; `28:        run: bash scripts/eval.sh --report=eval-report.md`.

**Implementation Reference:** Story 1 — `check_claude_md` in `scripts/eval.sh`, modeled on `check_codex_tomls`.

---

### Scenario 6: A `|` in a purpose is escaped; a broken agent file and a failed write stop the generator

**Source:** Error Map — Story 1 (Generator renders a purpose with `|`; Generator reads agents; Generator writes)
**Feature:** none
**Verification:** human — no recipe
**Automated Test:** `scripts/tests/test_gen_claude_md.py` (`test_ac_1_1_exact_bytes_escaping_and_agent_order`, `test_ac_1_3_agent_without_description`, `test_ac_1_3_write_error_leaves_template`)

**Preconditions:**
- Setup block pasted.

**Steps:**
1. Put a `|` in the `/revert` purpose and regenerate:
   ```bash
   cd "$CL"; T0=$(h claude-code/CLAUDE.md)
   sed -i '' 's/purpose: "Safely unwind a story or spec/purpose: "Safely unwind a story | spec/' .writ/manifest.yaml
   python3 scripts/gen-claude-md.py; echo "exit $?"; grep '^| `/revert`' claude-code/CLAUDE.md; git checkout -q .writ/manifest.yaml claude-code/CLAUDE.md
   ```
2. Remove `description:` from one agent file:
   ```bash
   cd "$CL"; sed -i '' '/^description:/d' claude-code/agents/writ-tester.md
   python3 scripts/gen-claude-md.py; echo "exit $?"; [ "$(h claude-code/CLAUDE.md)" = "$T0" ] && echo "template unchanged"; git checkout -q claude-code/agents/writ-tester.md
   ```
3. Make the template folder read-only:
   ```bash
   cd "$CL"; chmod a-w claude-code; python3 scripts/gen-claude-md.py; echo "exit $?"; chmod u+w claude-code
   ls -A claude-code; [ "$(h claude-code/CLAUDE.md)" = "$T0" ] && echo "template unchanged"; git status --short
   ```

**Expected Result:**
- Step 1: `pass`, `exit 0`; the row's purpose reads `Safely unwind a story \| spec via a layered commit resolver with plan-before-mutate guards.`
- Step 2: `fail`, `reason: agent writ-tester.md`, `gen-claude-md: fail (1 agent)`, `exit 1`, `template unchanged`.
- Step 3: `fail`, `reason: write [Errno 13] Permission denied: '<W>/clone/claude-code/.CLAUDE.md.<random>'`, `gen-claude-md: fail (1 write)`, `exit 1`; `ls -A` shows only `CLAUDE.md` and `agents` (no temp file left); `template unchanged`; `git status` prints nothing.

**Status:** [x] Pass  [ ] Fail

**Notes:**
- agent-run 2026-10-21 @ b850e66: step 1 `pass`, exit 0, purpose reads `Safely unwind a story \| spec via …`; step 2 `reason: agent writ-tester.md`, `fail (1 agent)`, exit 1, template unchanged; step 3 `reason: write [Errno 13] Permission denied: '<W>/clone/claude-code/.CLAUDE.md.nj71vxnp'`, `fail (1 write)`, exit 1, `ls -A` shows `CLAUDE.md agents`, template unchanged, `git status` empty.

---

### Scenario 7: An empty command list fails; a missing agents folder is unverifiable

**Source:** Shadow Path — Story 1 (Generator: empty input; upstream error)
**Feature:** none
**Verification:** human — no recipe
**Automated Test:** `scripts/tests/test_gen_claude_md.py` (`test_ac_1_3_empty_and_absent_commands_section`, `test_ac_1_3_missing_agents_dir_is_unverifiable`)

**Preconditions:**
- Setup block pasted.

**Steps:**
1. Build a temp root with the generator, the real agents, and a manifest whose `commands:` list is empty:
   ```bash
   G="$W/s7"; mkdir -p "$G/scripts" "$G/.writ" "$G/claude-code"
   cp "$CL/scripts/gen-claude-md.py" "$G/scripts/"; cp -R "$CL/claude-code/agents" "$G/claude-code/"
   printf 'version: 1\ncommands:\nagents:\n  - name: x\n' > "$G/.writ/manifest.yaml"
   python3 "$G/scripts/gen-claude-md.py"; echo "exit $?"; ls "$G/claude-code"
   ```
2. Remove the agents folder:
   ```bash
   rm -rf "$G/claude-code/agents"; python3 "$G/scripts/gen-claude-md.py"; echo "exit $?"
   ```

**Expected Result:**
- Step 1: `fail`, `reason: manifest no commands`, `gen-claude-md: fail (1 manifest)`, `exit 1`; `claude-code/` holds only `agents` (no template written).
- Step 2: `unverifiable`, `reason: agents missing: claude-code/agents`, `gen-claude-md: unverifiable (inputs missing)`, `exit 0`.

**Status:** [x] Pass  [ ] Fail

**Notes:** `eval.sh` turns `unverifiable` into a finding, so CI does not pass on missing inputs (technical spec → Eval Check, rule 3).
- agent-run 2026-10-21 @ b850e66: step 1 `reason: manifest no commands`, `fail (1 manifest)`, exit 1, `claude-code/` holds only `agents`; step 2 `reason: agents missing: claude-code/agents`, `unverifiable (inputs missing)`, exit 0.

---

### Scenario 8: A renamed command and a new agent file each make `--check` fail

**Source:** Edge Case — Story 1 (a manifest command renamed; a new file in `claude-code/agents/`)
**Feature:** none
**Verification:** human — no recipe
**Automated Test:** partial — `scripts/tests/test_gen_claude_md.py` (`test_ac_1_2_extra_row_and_rename`); the new-agent case is covered only by the generic `test_ac_1_2_other_byte_difference_is_stale`

**Preconditions:**
- Setup block pasted.

**Steps:**
1. Rename `/design` in the manifest:
   ```bash
   cd "$CL"; sed -i '' 's/^  - name: writ-design$/  - name: visual-design/; s|file: commands/writ-design.md|file: commands/visual-design.md|' .writ/manifest.yaml
   python3 scripts/gen-claude-md.py --check; echo "exit $?"; git checkout -q .writ/manifest.yaml
   ```
2. Add an agent file:
   ```bash
   cd "$CL"; printf -- '---\nname: writ-extra\ndescription: Extra agent for the UAT check.\n---\nBody\n' > claude-code/agents/writ-extra.md
   python3 scripts/gen-claude-md.py --check; echo "exit $?"; rm claude-code/agents/writ-extra.md; git status --short
   ```

**Expected Result:**
- Step 1: `fail`, `reason: missing visual-design`, `reason: extra design`, `gen-claude-md: fail (1 missing, 1 extra)`, `exit 1`.
- Step 2: `fail`, `reason: stale claude-code/CLAUDE.md`, `gen-claude-md: fail (1 stale)`, `exit 1`. `git status` prints nothing.

**Status:** [x] Pass  [ ] Fail

**Notes:**
- agent-run 2026-10-21 @ b850e66: step 1 as written is a no-op at this commit: the manifest entry is now `writ-design`, so the `sed` matched nothing and `--check` printed `pass`, exit 0. Re-run with `writ-design` in the `sed`: `reason: missing visual-design`, `reason: extra writ-design`, `fail (1 missing, 1 extra)`, exit 1. The plan's step 1 needs `design` → `writ-design`.
- Step 2: `reason: stale claude-code/CLAUDE.md`, `fail (1 stale)`, exit 1; `git status` empty.

---

## Story 2: Install the System Instructions and Import Line on Claude Code

### Scenario 9: A fresh Claude Code install copies the system instructions and imports them

**Source:** Acceptance Criteria — Story 2 (AC-2.1); Shadow Path (Install: nil input, no `CLAUDE.md`); Experience Design (States: fresh install, install dry run)
**Feature:** none
**Verification:** human — no recipe
**Automated Test:** `scripts/tests/test_install_update_claude_parity.sh` (AC-2.1 block)

**Preconditions:**
- Setup block pasted.

**Steps:**
1. Dry run into an empty folder:
   ```bash
   P="$W/s9-dry"; inst "$P" --dry-run > "$W/s9-dry.txt" 2>&1; echo "exit $?"
   grep -e 'System' -e 'CLAUDE.md' "$W/s9-dry.txt"; find "$P" -mindepth 1 | wc -l
   ```
2. Real install into a folder with no `CLAUDE.md`:
   ```bash
   P="$W/s9"; inst "$P" > "$W/s9.txt" 2>&1; echo "exit $?"
   grep -e '\[6/7\]' -e 'CLAUDE.md:' "$W/s9.txt"; grep -c 'skipped — no system-instructions' "$W/s9.txt"
   ```
3. Inspect the result:
   ```bash
   cmp "$SRC/system-instructions.md" "$P/.claude/system-instructions.md" && echo "byte copy"
   grep -n '^## Prime Directive' "$P/.claude/system-instructions.md"
   grep -c '  system-instructions.md$' "$P/.claude/.writ-manifest"
   grep -n '^@' "$P/CLAUDE.md"; grep -c '^| `/' "$P/CLAUDE.md"
   ```

**Expected Result:**
- Step 1: `exit 0`; `  📖 Root:      1 (CLAUDE.md)`, `  📖 System:    1 (system-instructions.md)`, `  System:  system-instructions.md → always updated`, `  CLAUDE.md integration plan:`, `Would create CLAUDE.md with Writ block (no prior file).`; `0` files written.
- Step 2: `exit 0`; `  [6/7] System instructions...`; `  CLAUDE.md: Writ block created`; `0` skipped lines.
- Step 3: `byte copy`; `7:## Prime Directive`; `1` manifest line under the key `system-instructions.md`; `8:@.claude/system-instructions.md` (line 1 is the start marker); `32` command rows.

**Status:** [x] Pass  [ ] Fail

**Notes:** Install leaves `CLAUDE.md` at mode `0600` (`-rw-------`). That comes from `merge_claude_md`'s `mktemp` + `mv`, predates this spec, and is out of scope (technical spec → Interaction Edge Cases, last row).
- agent-run 2026-10-21 @ b850e66: dry run exit 0 with the `Root`, `System`, `System:  … always updated`, `CLAUDE.md integration plan:`, and `Would create CLAUDE.md …` lines, `0` files; install exit 0, `[6/7] System instructions...`, `CLAUDE.md: Writ block created`, `0` skipped; `byte copy`, `7:## Prime Directive`, `1`, `8:@.claude/system-instructions.md`, `32` rows. Mode `-rw-------` as noted.

**Implementation Reference:** Story 2 — `scripts/install.sh`: platform step `[6/7] System instructions...`, `write_copy_manifest`, inventory and dry run.

---

### Scenario 10: Bytes outside the Writ block survive install, update to a longer template, and `--force`

**Source:** Acceptance Criteria — Story 2 (AC-2.2); Edge Case (CRLF `CLAUDE.md`); Business Rule 1
**Feature:** none
**Verification:** human — no recipe
**Automated Test:** `scripts/tests/test_install_update_claude_parity.sh` (AC-2.2 block); `test_merge_claude_md.sh` and `test_update_claude_md.sh` case 11

**Preconditions:**
- Setup block pasted.

**Steps:**
1. Install over a hand-written `CLAUDE.md`:
   ```bash
   P="$W/s10"; mkdir -p "$P"; user_md "$P/CLAUDE.md"; cp "$P/CLAUDE.md" "$W/s10.orig"
   inst "$P" > "$W/s10-inst.txt" 2>&1; echo "exit $?"; grep 'CLAUDE.md:' "$W/s10-inst.txt"
   { cat "$W/s10.orig"; printf '\n'; } | cmp - <(part pre "$P/CLAUDE.md") && echo "before-block bytes = original + one newline"
   ```
2. Add user text after the block and record both sides:
   ```bash
   printf '\n## After the block\r\nUser text below.  \n' >> "$P/CLAUDE.md"
   part pre "$P/CLAUDE.md" > "$W/s10.pre"; part post "$P/CLAUDE.md" > "$W/s10.post"
   ```
3. Commit a longer template upstream and update:
   ```bash
   git clone -q "$SRC" "$W/up10"; printf '\nOne more line from upstream.\n' >> "$W/up10/claude-code/CLAUDE.md"; gc "$W/up10" "longer template"
   n0=$(part inner "$P/CLAUDE.md" | wc -l | tr -d ' ')
   UPSTREAM="$W/up10" upd "$P" > "$W/s10-upd.txt" 2>&1; echo "exit $?"; grep 'Updated: CLAUDE.md' "$W/s10-upd.txt"
   echo "block lines $n0 -> $(part inner "$P/CLAUDE.md" | wc -l | tr -d ' ')"
   part pre "$P/CLAUDE.md" | cmp - "$W/s10.pre" && part post "$P/CLAUDE.md" | cmp - "$W/s10.post" && echo "outside bytes unchanged after update"
   ```
4. Edit inside the block, then run `install.sh --force`:
   ```bash
   sed -i '' 's/^## Principles$/## Principles (edited by hand)/' "$P/CLAUDE.md"
   inst "$P" --force > "$W/s10-force.txt" 2>&1; echo "exit $?"; grep 'CLAUDE.md:' "$W/s10-force.txt"
   part pre "$P/CLAUDE.md" | cmp - "$W/s10.pre" && part post "$P/CLAUDE.md" | cmp - "$W/s10.post" && echo "outside bytes unchanged after --force"
   part inner "$P/CLAUDE.md" | cmp - "$SRC/claude-code/CLAUDE.md" && echo "block = template"
   ```

**Expected Result:**
- Step 1: `exit 0`; `  CLAUDE.md: Writ block appended (existing content preserved)`; `before-block bytes = original + one newline` (the single `\n` install adds because the file had no final newline).
- Step 3: `exit 0`; `    🔄 Updated: CLAUDE.md (Writ block)`; `block lines 74 -> 76`; `outside bytes unchanged after update`.
- Step 4: `exit 0`; `  CLAUDE.md: Writ block updated (--force)`; `outside bytes unchanged after --force`; `block = template`.

**Status:** [x] Pass  [ ] Fail

**Notes:**
- agent-run 2026-10-21 @ b850e66: step 1 exit 0, `Writ block appended (existing content preserved)`, `before-block bytes = original + one newline`; step 3 exit 0, `🔄 Updated: CLAUDE.md (Writ block)`, `block lines 74 -> 76`, outside bytes unchanged; step 4 exit 0, `Writ block updated (--force)`, outside bytes unchanged, `block = template`.

**Implementation Reference:** Story 2 — `merge_claude_md` in `scripts/install.sh` and `scripts/update.sh` writes the template's bytes between the markers only.

---

### Scenario 11: Update keeps `.claude/system-instructions.md` current, preserves a local edit, and `--force` overwrites it

**Source:** Acceptance Criteria — Story 2 (AC-2.3); Error Map (Update system instructions: local copy modified); Experience Design (States: update with local file unmodified; modified)
**Feature:** none
**Verification:** human — no recipe
**Automated Test:** `scripts/tests/test_install_update_claude_parity.sh` (AC-2.3 block)

**Preconditions:**
- Setup block pasted.
- An upstream whose `system-instructions.md` changed:
  ```bash
  git clone -q "$SRC" "$W/up11"; printf '\n<!-- upstream change for UAT -->\n' >> "$W/up11/system-instructions.md"; gc "$W/up11" "change system instructions"
  ```

**Steps:**
1. Unmodified local copy:
   ```bash
   P="$W/s11a"; inst "$P" > /dev/null 2>&1
   UPSTREAM="$W/up11" upd "$P" > "$W/s11a.txt" 2>&1; echo "exit $?"; grep 'system-instructions' "$W/s11a.txt"
   cmp "$W/up11/system-instructions.md" "$P/.claude/system-instructions.md" && echo "now equals upstream"
   ```
2. Locally edited copy:
   ```bash
   P="$W/s11b"; inst "$P" > /dev/null 2>&1; printf '\n## My local rule\n' >> "$P/.claude/system-instructions.md"; cp "$P/.claude/system-instructions.md" "$W/s11b.si"
   UPSTREAM="$W/up11" upd "$P" > "$W/s11b.txt" 2>&1; echo "exit $?"; grep -e 'system-instructions' -e 'were preserved' "$W/s11b.txt"
   cmp "$W/s11b.si" "$P/.claude/system-instructions.md" && echo "local copy kept"
   ```
3. Same project with `--force`:
   ```bash
   UPSTREAM="$W/up11" upd "$P" --force > "$W/s11c.txt" 2>&1; echo "exit $?"; grep 'system-instructions' "$W/s11c.txt"
   cmp "$W/up11/system-instructions.md" "$P/.claude/system-instructions.md" && echo "overwritten with upstream"
   ```

**Expected Result:**
- Step 1: `exit 0`; `    🔄 Update:    system-instructions.md`; `now equals upstream`.
- Step 2: `exit 0`; `    ⚡ Preserved: system-instructions.md (local modifications)`, `  ⚠️  1 file(s) with local modifications were preserved:`, `    system-instructions.md`; `local copy kept`.
- Step 3: `exit 0`; `    🔄 Update:    system-instructions.md (forced)`; `overwritten with upstream`.

**Status:** [x] Pass  [ ] Fail

**Notes:** A manifest that lacks the `system-instructions.md` line while the local file differs from upstream gives `⚡ Preserved … (no baseline, assuming modified)`, not an update. That is Cursor's rule, copied as is (DEV-009). This plan does not exercise it; no test does either.
- agent-run 2026-10-21 @ b850e66: step 1 exit 0, `🔄 Update:    system-instructions.md`, `now equals upstream`; step 2 exit 0, `⚡ Preserved: system-instructions.md (local modifications)`, `1 file(s) with local modifications were preserved:`, `local copy kept`; step 3 exit 0, `🔄 Update:    system-instructions.md (forced)`, `overwritten with upstream`.

**Implementation Reference:** Story 2 — `scripts/update.sh`: the `SYSINST_ACTION` scan runs for Cursor or Claude.

---

### Scenario 12: A pre-parity project gets the file as new and a block with the import line

**Source:** Acceptance Criteria — Story 2 (AC-2.3, pre-parity case); Error Map (Update system instructions: no local copy); Experience Design (State: update from a pre-parity install)
**Feature:** none
**Verification:** human — no recipe
**Automated Test:** `scripts/tests/test_install_update_claude_parity.sh` (pre-parity upgrade block)

**Preconditions:**
- Setup block pasted.

**Steps:**
1. Install, then turn the project into a pre-parity install (no `.claude/system-instructions.md`, no manifest line for it, an old block whose hash is the recorded baseline):
   ```bash
   P="$W/s12"; mkdir -p "$P"; printf '# Team notes\n\nOur rules.\n' > "$P/CLAUDE.md"; inst "$P" > /dev/null 2>&1
   rm "$P/.claude/system-instructions.md"
   python3 -c 'import sys; p = sys.argv[1]; t = open(p).read(); s = t.index("<!-- writ:start -->\n"); e = t.index("<!-- writ:end -->"); open(p, "w").write(t[:s] + "<!-- writ:start -->\n# Writ (old template)\n" + t[e:])' "$P/CLAUDE.md"
   OLD=$(part inner "$P/CLAUDE.md" | shasum -a 256 | cut -d' ' -f1)
   grep -v -e '  system-instructions.md$' -e '  CLAUDE.md.writ-block$' "$P/.claude/.writ-manifest" > "$W/s12.m" && mv "$W/s12.m" "$P/.claude/.writ-manifest"
   printf '%s  CLAUDE.md.writ-block\n' "$OLD" >> "$P/.claude/.writ-manifest"
   part pre "$P/CLAUDE.md" > "$W/s12.pre"; cat "$P/CLAUDE.md"
   ```
2. Update:
   ```bash
   upd "$P" > "$W/s12.txt" 2>&1; echo "exit $?"; grep -e 'system-instructions' -e 'CLAUDE.md' -e 'to update' "$W/s12.txt"
   ```
3. Inspect:
   ```bash
   ls "$P/.claude/system-instructions.md"; grep -c '^@.claude/system-instructions.md$' "$P/CLAUDE.md"
   part pre "$P/CLAUDE.md" | cmp - "$W/s12.pre" && echo "user text unchanged"
   grep -c '  system-instructions.md$' "$P/.claude/.writ-manifest"
   ```

**Expected Result:**
- Step 1: the file shows `# Team notes`, a blank line, `Our rules.`, then `<!-- writ:start -->`, `# Writ (old template)`, `<!-- writ:end -->`.
- Step 2: `exit 0`; `    ✨ New:       system-instructions.md`, `  CLAUDE.md:`, `    🔄 Updated: CLAUDE.md (Writ block)`, `  2 file(s) to update`.
- Step 3: the file exists; `1` import line; `user text unchanged`; `1` manifest line.

**Status:** [x] Pass  [ ] Fail

**Notes:**
- agent-run 2026-10-21 @ b850e66: step 1 file shows `# Team notes`, blank, `Our rules.`, start marker, `# Writ (old template)`, end marker; update exit 0, `✨ New:       system-instructions.md`, `CLAUDE.md:`, `🔄 Updated: CLAUDE.md (Writ block)`, `2 file(s) to update`; file exists, `1` import line, `user text unchanged`, `1` manifest line.

---

### Scenario 13: A preserved block without the import line is warned about and left alone

**Source:** Acceptance Criteria — Story 2 (AC-2.4); Error Map (Install or update block: modified, no import line); Edge Case (preserved block that already has the import line); Experience Design (State: update, Writ block modified and missing the import line); Decision D3
**Feature:** none
**Verification:** human — no recipe
**Automated Test:** `scripts/tests/test_install_update_claude_parity.sh` (AC-2.4 block); `test_merge_claude_md.sh` cases 9–10; `test_update_claude_md.sh` cases 9–10

**Preconditions:**
- Setup block pasted.

**Steps:**
1. Install, then delete the import line from the block:
   ```bash
   P="$W/s13"; inst "$P" > /dev/null 2>&1
   sed -i '' '/^@\.claude\/system-instructions\.md$/d' "$P/CLAUDE.md"; H0=$(h "$P/CLAUDE.md")
   ```
2. Run install and update, each as a dry run and for real:
   ```bash
   inst "$P" --dry-run > "$W/s13-1.txt" 2>&1; echo "exit $?"; grep -e 'Would preserve' -e '⚠️  CLAUDE.md' "$W/s13-1.txt"
   inst "$P" > "$W/s13-2.txt" 2>&1; echo "exit $?"; grep -e '⚡ CLAUDE.md' -e '⚠️  CLAUDE.md' "$W/s13-2.txt"
   upd "$P" --dry-run > "$W/s13-3.txt" 2>&1; echo "exit $?"; grep -e 'Preserved: CLAUDE.md' -e '⚠️  CLAUDE.md' "$W/s13-3.txt"
   upd "$P" > "$W/s13-4.txt" 2>&1; echo "exit $?"; grep -e 'Preserved: CLAUDE.md' -e '⚠️  CLAUDE.md' "$W/s13-4.txt"
   [ "$(h "$P/CLAUDE.md")" = "$H0" ] && echo "CLAUDE.md unchanged by all four runs"
   ```
3. A second project whose block is edited but keeps the import line:
   ```bash
   P="$W/s13b"; inst "$P" > /dev/null 2>&1; sed -i '' 's/^## Principles$/## Principles (ours)/' "$P/CLAUDE.md"
   inst "$P" > "$W/s13b-1.txt" 2>&1; upd "$P" > "$W/s13b-2.txt" 2>&1
   grep -c 'Writ block preserved' "$W/s13b-1.txt"; grep -c 'Preserved: CLAUDE.md' "$W/s13b-2.txt"; cat "$W/s13b-1.txt" "$W/s13b-2.txt" | grep -c 'has no @'
   ```

**Expected Result:**
- Step 2, each run `exit 0`:
  - install dry run: `Would preserve Writ block (local modifications detected).` then `⚠️  CLAUDE.md: the preserved Writ block has no @.claude/system-instructions.md line. Add it inside the block, or re-run install.sh --force to replace the block.`
  - install: `⚡ CLAUDE.md: Writ block preserved (local modifications) — re-run with --force to overwrite the Writ block.` then the same `⚠️` line.
  - update dry run and update: `    ⚡ Preserved: CLAUDE.md (Writ block has local modifications)` then `⚠️  CLAUDE.md: the preserved Writ block has no @.claude/system-instructions.md line. Add it inside the block, or re-run update.sh --force to replace the block.`
  - `CLAUDE.md unchanged by all four runs`.
- Step 3: install reports the block preserved (count `2`: the `⚡` line and the summary line), update reports `Preserved: CLAUDE.md` (`1`), and `0` warning lines.

**Status:** [x] Pass  [ ] Fail

**Notes:** In `update.sh` output the `⚠️` line is flush-left under the indented `⚡ Preserved` line, because the spec's exact text has no indent (Story 2 reviewer note). Cosmetic.
- agent-run 2026-10-21 @ b850e66: all four runs exit 0 with the expected preserve line and the `⚠️  CLAUDE.md: the preserved Writ block has no @.claude/system-instructions.md line …` warning (`install.sh --force` for install, `update.sh --force` for update); `CLAUDE.md unchanged by all four runs`; second project `2`, `1`, `0`.

**Implementation Reference:** Story 2 — `writ_block_inner_has_line` inside each `writ-merge-bundled` region.

---

### Scenario 14: Uninstall lists and removes `.claude/system-instructions.md`; the lifecycle docs name it

**Source:** Acceptance Criteria — Story 2 (AC-2.5); Business Rule 6
**Feature:** none
**Verification:** human — no recipe
**Automated Test:** `scripts/tests/test_install_update_claude_parity.sh` (AC-2.5 block)

**Preconditions:**
- Setup block pasted.

**Steps:**
1. Dry run on an installed project:
   ```bash
   P="$W/s14"; inst "$P" > /dev/null 2>&1; D0=$(digest "$P")
   uninst "$P" --dry-run > "$W/s14-dry.txt" 2>&1; echo "exit $?"; grep -e 'Extras' -e '🗑  .claude/system-instructions.md' -e '🗑  CLAUDE.md' -e 'Would remove' "$W/s14-dry.txt"
   [ "$(digest "$P")" = "$D0" ] && echo "dry run changed nothing"
   ```
2. Real run:
   ```bash
   uninst "$P" > "$W/s14.txt" 2>&1; echo "exit $?"; grep '🗑' "$W/s14.txt"; ls -A "$P"
   ```
3. The Claude rows of the three lifecycle docs:
   ```bash
   cd "$REPO"
   grep -n '^| `claude`' commands/update-writ.md commands/reinstall-writ.md | cut -c1-150
   grep -n 'Claude Code: `.claude/system-instructions.md`' commands/update-writ.md commands/reinstall-writ.md | cut -c1-110
   grep -n 'Claude Code: `rm .claude/system-instructions.md`' commands/uninstall-writ.md | cut -c1-110
   ```

**Expected Result:**
- Step 1: `exit 0`; `    📄 Extras:    2 (.claude/system-instructions.md CLAUDE.md Writ block)`, `  🗑  .claude/system-instructions.md`, `  🗑  CLAUDE.md Writ block`, `  Would remove 60 file(s).`; `dry run changed nothing`. (The full dry run also lists each command, agent, and skill file and `.claude/.writ-manifest`.)
- Step 2: `exit 0`; `  🗑  Removed: CLAUDE.md (empty after Writ block removal)` and `  🗑  Removed 60 file(s)`; `ls -A` shows `.cursorindexingignore`, `.writ`, `scripts` (no `.claude/`, no `CLAUDE.md`).
- Step 3: the `claude` row of `update-writ.md` lists `` `.claude/system-instructions.md`, `CLAUDE.md` (project root) ``; the `claude` row of `reinstall-writ.md` lists `` `CLAUDE.md` Writ block (project root), `.claude/system-instructions.md` ``; `update-writ.md` (Step 3 platform files) and `reinstall-writ.md` (Step 3 removal) each have a `Claude Code: .claude/system-instructions.md` bullet; `uninstall-writ.md` line 99 starts `Claude Code: rm .claude/system-instructions.md`.

**Status:** [x] Pass  [ ] Fail

**Notes:** `scripts/` and `.writ/` stay after uninstall. That is not part of this spec.
- agent-run 2026-10-21 @ b850e66: dry run exit 0, `Extras:    2 (.claude/system-instructions.md CLAUDE.md Writ block)`, both `🗑` lines, `Would remove 60 file(s).`, nothing changed; real run exit 0, `Removed: CLAUDE.md (empty after Writ block removal)`, `Removed 60 file(s)`, left `.cursorindexingignore .writ scripts`.
- Docs: `update-writ.md:66` and `reinstall-writ.md:71` rows as expected; bullets at `update-writ.md:119` (Step 3), `reinstall-writ.md:116` (Step 3), `uninstall-writ.md:99`.

---

### Scenario 15: Install stops on a broken source or broken markers

**Source:** Error Map — Story 2 (Install copies system instructions: source lacks the file; Install merges block: malformed markers); Shadow Path (Install and Update: upstream error, template missing → return 12)
**Feature:** none
**Verification:** human — no recipe
**Automated Test:** partial — `scripts/tests/test_merge_claude_md.sh` cases 4 and 7 (malformed markers, missing template, function level); no test covers a source without `system-instructions.md`

**Preconditions:**
- Setup block pasted.

**Steps:**
1. A source with no `system-instructions.md`:
   ```bash
   git clone -q "$SRC" "$W/src15a"; git -C "$W/src15a" rm -q system-instructions.md; gc "$W/src15a" "no system instructions"
   P="$W/s15a"; mkdir -p "$P"; (cd "$P" && bash "$W/src15a/scripts/install.sh" --platform claude --no-commit) > "$W/s15a.txt" 2>&1; echo "exit $?"
   tail -2 "$W/s15a.txt"; ls -A "$P/.claude"
   ```
2. A source with no `claude-code/CLAUDE.md`:
   ```bash
   git clone -q "$SRC" "$W/src15b"; git -C "$W/src15b" rm -q claude-code/CLAUDE.md; gc "$W/src15b" "no template"
   P="$W/s15b"; mkdir -p "$P"; (cd "$P" && bash "$W/src15b/scripts/install.sh" --platform claude --no-commit) > "$W/s15b.txt" 2>&1; echo "exit $?"
   grep '❌' "$W/s15b.txt"; ls -A "$P"
   ```
3. A `CLAUDE.md` with two start markers:
   ```bash
   P="$W/s15c"; mkdir -p "$P"; printf '# Mine\n<!-- writ:start -->\nold\n<!-- writ:start -->\n<!-- writ:end -->\n' > "$P/CLAUDE.md"; H0=$(h "$P/CLAUDE.md")
   inst "$P" > "$W/s15c.txt" 2>&1; echo "exit $?"; grep '❌' "$W/s15c.txt"
   [ "$(h "$P/CLAUDE.md")" = "$H0" ] && echo "CLAUDE.md unchanged"; ls -A "$P/.claude"
   ```

**Expected Result:**
- Step 1: `exit 1`; `  [6/7] System instructions...` then `cp: <W>/src15a/system-instructions.md: No such file or directory`; `.claude/` holds `agents`, `commands`, `skills` and no `.writ-manifest` (the abort comes before the manifest is written).
- Step 2: `exit 12`; `❌ Missing <W>/src15b/claude-code/CLAUDE.md — cannot integrate CLAUDE.md for Claude Code.`; the project has `.claude`, `.writ`, `scripts` and no `CLAUDE.md`.
- Step 3: `exit 13`; `❌ CLAUDE.md: Writ block error: malformed markers (expected exactly one <!-- writ:start --> and one <!-- writ:end -->).`; `CLAUDE.md unchanged`; `.claude/` holds `agents`, `commands`, `skills` and no `.writ-manifest`.

**Status:** [x] Pass  [ ] Fail

**Notes:** In all three cases install has already copied commands, agents, and skills when it stops. That is existing behavior, not introduced here.
- agent-run 2026-10-21 @ b850e66: step 1 exit 1, `[6/7] System instructions...`, `cp: <W>/src15a/system-instructions.md: No such file or directory`, `.claude/` = `agents commands skills`; step 2 exit 12, `❌ Missing <W>/src15b/claude-code/CLAUDE.md — cannot integrate CLAUDE.md for Claude Code.`, project = `.claude .writ scripts`; step 3 exit 13, malformed-markers line, `CLAUDE.md unchanged`, `.claude/` = `agents commands skills`.

---

### Scenario 16: Empty inputs: an empty `CLAUDE.md`, an empty Writ block, and update with no `CLAUDE.md`

**Source:** Shadow Path — Story 2 (Install: empty input; Update: empty input; Update: nil input)
**Feature:** none
**Verification:** human — no recipe
**Automated Test:** partial — `scripts/tests/test_merge_claude_md.sh` case 6 (empty file); the empty block and the update guard have no dedicated test

**Preconditions:**
- Setup block pasted.

**Steps:**
1. Install over an empty `CLAUDE.md`:
   ```bash
   P="$W/s16a"; mkdir -p "$P"; : > "$P/CLAUDE.md"; inst "$P" > "$W/s16a.txt" 2>&1; echo "exit $?"; grep 'CLAUDE.md:' "$W/s16a.txt"
   head -1 "$P/CLAUDE.md"; part inner "$P/CLAUDE.md" | cmp - "$SRC/claude-code/CLAUDE.md" && echo "block = template"
   ```
2. Empty the Writ block of an installed project, then update:
   ```bash
   P="$W/s16b"; inst "$P" > /dev/null 2>&1; printf '<!-- writ:start -->\n<!-- writ:end -->\n' > "$P/CLAUDE.md"; H0=$(h "$P/CLAUDE.md")
   upd "$P" > "$W/s16b.txt" 2>&1; echo "exit $?"; grep -e 'Preserved: CLAUDE.md' -e '⚠️  CLAUDE.md' "$W/s16b.txt"; [ "$(h "$P/CLAUDE.md")" = "$H0" ] && echo "CLAUDE.md unchanged"
   ```
3. Delete `CLAUDE.md` from an installed project, then update:
   ```bash
   P="$W/s16c"; inst "$P" > /dev/null 2>&1; rm "$P/CLAUDE.md"
   upd "$P" > "$W/s16c.txt" 2>&1; echo "exit $?"; tail -2 "$W/s16c.txt"; ls "$P/CLAUDE.md" 2>&1 | grep -c 'No such file'
   ```

**Expected Result:**
- Step 1: `exit 0`; `  CLAUDE.md: Writ block appended (existing content preserved)`; line 1 is `<!-- writ:start -->` (no leading blank line); `block = template`.
- Step 2: `exit 0`; `    ⚡ Preserved: CLAUDE.md (Writ block has local modifications)` and the `⚠️  CLAUDE.md: … re-run update.sh --force to replace the block.` line; `CLAUDE.md unchanged`.
- Step 3: `exit 1`; `❌ Writ doesn't appear to be installed for Claude Code in this project.` and `   Run install.sh --platform claude first.`; `1` (no `CLAUDE.md` was created).

**Status:** [x] Pass  [ ] Fail

**Notes:**
- agent-run 2026-10-21 @ b850e66: step 1 exit 0, `Writ block appended (existing content preserved)`, line 1 `<!-- writ:start -->`, `block = template`; step 2 exit 0, `⚡ Preserved: CLAUDE.md (Writ block has local modifications)` and the `⚠️ … update.sh --force` line, unchanged; step 3 exit 1, `❌ Writ doesn't appear to be installed for Claude Code in this project.`, `Run install.sh --platform claude first.`, `1`.

---

### Scenario 17: Repeated update, re-install over an edited copy, and a user's own import line

**Source:** Edge Case — Story 2 (two updates in a row; `install.sh` re-run over a locally edited `.claude/system-instructions.md`; the user already wrote `@.claude/system-instructions.md` outside the block)
**Feature:** none
**Verification:** human — no recipe
**Automated Test:** partial — `scripts/tests/test_install_update_claude_parity.sh` asserts the second update ("Already up to date"); the other two cases are manual only

**Preconditions:**
- Setup block pasted.

**Steps:**
1. Two updates in a row with no upstream change:
   ```bash
   P="$W/s17a"; inst "$P" > /dev/null 2>&1; H0=$(h "$P/CLAUDE.md")
   upd "$P" > "$W/s17a-1.txt" 2>&1; upd "$P" > "$W/s17a-2.txt" 2>&1; echo "exit $?"
   grep -e 'up to date' -e 'system-instructions' -e 'Updated' "$W/s17a-2.txt"; [ "$(h "$P/CLAUDE.md")" = "$H0" ] && echo "CLAUDE.md unchanged"
   ```
2. Edit the installed copy, then re-run install:
   ```bash
   printf '\n## Local edit\n' >> "$P/.claude/system-instructions.md"
   inst "$P" > "$W/s17a-3.txt" 2>&1; echo "exit $?"; cmp "$SRC/system-instructions.md" "$P/.claude/system-instructions.md" && echo "overwritten with source"
   ```
3. A user file that already holds the import line:
   ```bash
   P="$W/s17c"; mkdir -p "$P"; printf '# Mine\n@.claude/system-instructions.md\n' > "$P/CLAUDE.md"; cp "$P/CLAUDE.md" "$W/s17c.orig"
   inst "$P" > /dev/null 2>&1; upd "$P" > /dev/null 2>&1; echo "exit $?"
   part pre "$P/CLAUDE.md" | cmp - "$W/s17c.orig" && echo "user text unchanged"; grep -c '^@.claude/system-instructions.md$' "$P/CLAUDE.md"
   ```

**Expected Result:**
- Step 1: `exit 0`; only `✅ Already up to date! (<SHA>)`; `CLAUDE.md unchanged`.
- Step 2: `exit 0`; `overwritten with source` (install always updates this file, same as Cursor; `update.sh` is the path that keeps edits).
- Step 3: `exit 0`; `user text unchanged`; `2` (the user's line and the block's line). Claude Code may read the file twice; the spec calls that harmless.

**Status:** [x] Pass  [ ] Fail

**Notes:**
- agent-run 2026-10-21 @ b850e66: step 1 exit 0, only `✅ Already up to date! (f4ecb4e)`, `CLAUDE.md unchanged`; step 2 exit 0, `overwritten with source`; step 3 exit 0, `user text unchanged`, `2`.

---

## Story 3: Correct the Claude Code Adapter

### Scenario 18: The adapter names no flag, workflow, or hook that does not exist

**Source:** Acceptance Criteria — Story 3 (AC-3.1, and the absence half of AC-3.5); Business Rule 13
**Feature:** none
**Verification:** human — no recipe
**Automated Test:** `scripts/tests/test_claude_code_adapter_claims.py` (`test_no_all_flag`, `test_no_agent_teams_*`, `test_no_merge_back_claims`, `test_no_undocumented_event_or_variable`)

**Preconditions:**
- Setup block pasted.

**Steps:**
1. Search the adapter:
   ```bash
   cd "$REPO"; A=adapters/claude-code.md
   grep -nE -e '--all\b' "$A"; echo "--all: exit $?"
   grep -ni 'agent teams' "$A"; echo "agent teams: exit $?"
   grep -n -e 'Merges changes back' -e 'changes merge back' -e 'merge back automatically' "$A"; echo "merge-back: exit $?"
   grep -n -e 'SubagentCompleted' -e '\$WORKTREE' "$A"; echo "hook names: exit $?"
   grep -niE 'six Claude-native|seventh' "$A"; echo "six/seventh: exit $?"
   ```

**Expected Result:**
- Every `grep` prints no line and each echo reports `exit 1`.

**Status:** [x] Pass  [ ] Fail

**Notes:**
- agent-run 2026-10-21 @ b850e66: all five `grep`s printed nothing; `--all`, `agent teams`, `merge-back`, `hook names`, `six/seventh` each `exit 1`.

---

### Scenario 19: Worktree text says what Claude Code does and points at the reconciliation skill

**Source:** Acceptance Criteria — Story 3 (AC-3.2, AC-3.3)
**Feature:** none
**Verification:** human — no recipe
**Automated Test:** `scripts/tests/test_claude_code_adapter_claims.py` (`test_base_branch_and_base_ref`, `test_cleanup_rule`, `test_reconcile_per_skill`, `test_parallel_stories_are_implement_spec_batches`, `test_gotcha_one_*`)

**Preconditions:**
- Setup block pasted.

**Steps:**
1. Read the worktree section: `sed -n '/^### Git Worktree Isolation/,/^### Persistent Memory/p' "$REPO/adapters/claude-code.md"`
2. Read the `create-spec` example's closing line: `grep -n 'copies each story file back' "$REPO/adapters/claude-code.md"`
3. Read the first two Gotchas: `sed -n '/^## Gotchas/,/^## Model-specific/p' "$REPO/adapters/claude-code.md" | sed -n 1,5p`
4. Open the skill and check its step 6 heading: `grep -n '^## \|^### ' "$REPO/skills/subagent-worktree-integration/SKILL.md" | head -12`

**Expected Result:**
- Step 1: the four numbered steps say the worktree branches from the repository's default branch unless `worktree.baseRef` is `"head"`; it is removed when the subagent made no changes; otherwise it stays on disk until a periodic sweep, and "Nothing copies the changes into your checkout." The next paragraph says the orchestrator reconciles per the worktree integration skill (diff, copy, re-verify, remove), links `../skills/subagent-worktree-integration/SKILL.md`, and cites the Claude Code worktrees docs. A **Parallel stories** line names `/implement-spec` parallel batches.
- Step 2: one line saying the orchestrator copies each story file back per the skill before it reads or commits it.
- Step 3: Gotcha 1 is **Stale worktrees can overwrite newer work**, names both causes (default base lacks commits not on the remote default branch; `worktree.baseRef: "head"` lacks commits made after creation), and links step 6 of the skill. No "Worktree merges can conflict" gotcha.
- Step 4: the skill has a step 6 about a stale worktree, matching the link.

**Status:** [x] Pass  [ ] Fail

**Notes:**
- agent-run 2026-10-21 @ b850e66: section has the four numbered steps (default branch unless `worktree.baseRef` is `"head"`; removed with no changes; stays until a periodic sweep; "Nothing copies the changes into your checkout."), the skill link and worktrees-docs citation, and the **Parallel stories** line; `349:` copy-back line.
- Gotcha 1 is **Stale worktrees can overwrite newer work** with both causes and a link to step 6; `0` "Worktree merges can conflict"; skill has `### 6. Recognize and resolve a stale worktree`.

---

### Scenario 20: The Installation section's manual Step 1 keeps the user's `CLAUDE.md` and copies the system instructions

**Source:** Acceptance Criteria — Story 3 (AC-3.4); Business Rule 16
**Feature:** none
**Verification:** human — no recipe
**Automated Test:** partial — `scripts/tests/test_claude_code_adapter_claims.py` checks the text (`test_manual_step_one_*`, `test_no_copy_over_claude_md`, `test_import_sentence`, `test_final_structure_lists_system_instructions_under_claude_dir`); running Step 1 is manual only

**Preconditions:**
- Setup block pasted.

**Steps:**
1. Read the section: `sed -n '/^## Installation/,/^### Final Structure/p' "$REPO/adapters/claude-code.md"`
2. Check the tree and the copy-over pattern:
   ```bash
   cd "$REPO"; grep -n 'system-instructions.md  ' adapters/claude-code.md
   grep -nE 'cp\s+\S*claude-code/CLAUDE\.md\s+(\./)?CLAUDE\.md' adapters/claude-code.md; echo "copy-over: exit $?"
   ```
3. Run manual Step 1 as written, with `path/to/writ` replaced by `$SRC`, in a project that has a hand-written `CLAUDE.md`:
   ```bash
   P="$W/s20"; mkdir -p "$P"; user_md "$P/CLAUDE.md"; cp "$P/CLAUDE.md" "$W/s20.orig"; cd "$P"
   mkdir -p .claude/agents .claude/commands .writ/state
   cp "$SRC"/commands/*.md .claude/commands/
   cp "$SRC"/claude-code/agents/*.md .claude/agents/
   [ -s CLAUDE.md ] && [ -n "$(tail -c 1 CLAUDE.md)" ] && printf '\n' >> CLAUDE.md   # end the file with a newline first
   { printf '%s\n' '<!-- writ:start -->'; cat "$SRC"/claude-code/CLAUDE.md; printf '%s\n' '<!-- writ:end -->'; } >> CLAUDE.md
   cp "$SRC"/system-instructions.md .claude/system-instructions.md
   { cat "$W/s20.orig"; printf '\n'; } | cmp - <(part pre CLAUDE.md) && echo "user text kept, plus one newline"
   part inner CLAUDE.md | cmp - "$SRC/claude-code/CLAUDE.md" && echo "block = template"
   cmp "$SRC/system-instructions.md" .claude/system-instructions.md && echo "system instructions copied"
   ```
4. Check the prose about later runs on a manual install (no manifest): run `install.sh` from a source with a newer template:
   ```bash
   git clone -q "$SRC" "$W/up20"; printf '\nOne more line from upstream.\n' >> "$W/up20/claude-code/CLAUDE.md"; gc "$W/up20" "newer template"
   H0=$(h "$P/CLAUDE.md"); (cd "$P" && bash "$W/up20/scripts/install.sh" --platform claude --no-commit) > "$W/s20-inst.txt" 2>&1; echo "exit $?"
   grep '⚡ CLAUDE.md' "$W/s20-inst.txt"; [ "$(h "$P/CLAUDE.md")" = "$H0" ] && echo "CLAUDE.md unchanged"
   ```

**Expected Result:**
- Step 1: the automated text names `.claude/system-instructions.md` and the `<!-- writ:start -->` / `<!-- writ:end -->` markers and says text outside them is kept. Manual Step 1 appends the template between the markers and copies `system-instructions.md` to `.claude/system-instructions.md`. One sentence says `CLAUDE.md` imports it with `@.claude/system-instructions.md` and that Claude Code asks once to approve an import that resolves outside the working directory. The prose after Step 1 says a manual install has no recorded baseline, so later runs report the block as locally modified, and that `--force` also overwrites other Writ files.
- Step 2: the Final Structure tree has `system-instructions.md         # Writ root contract, imported by CLAUDE.md` under `.claude/`; `copy-over: exit 1`.
- Step 3: `user text kept, plus one newline`; `block = template`; `system instructions copied`.
- Step 4: `exit 0`; `⚡ CLAUDE.md: Writ block preserved (local modifications) — re-run with --force to overwrite the Writ block.`; `CLAUDE.md unchanged`. This matches the Step 1 prose (DEV-005).

**Status:** [x] Pass  [ ] Fail

**Notes:** The automated-install paragraph still says "Files you have customized are never overwritten", which ignores `--force` (Story 3 reviewer note). Not in this spec's acceptance criteria.
- agent-run 2026-10-21 @ b850e66: Installation text names `.claude/system-instructions.md`, the markers, kept outside text, the import sentence with the approval clause, and the no-baseline / `--force` prose; tree `74:│   ├── system-instructions.md         # Writ root contract, imported by CLAUDE.md`; `copy-over: exit 1`.
- Manual Step 1: `user text kept, plus one newline`, `block = template`, `system instructions copied`; install from newer template exit 0, `⚡ CLAUDE.md: Writ block preserved (local modifications) — re-run with --force …`, `CLAUDE.md unchanged`.

**Implementation Reference:** Story 3 — `adapters/claude-code.md` § Installation.

---

### Scenario 21: The hook example uses `SubagentStop`, and every agent appears in the three adapter lists

**Source:** Acceptance Criteria — Story 3 (AC-3.5); Decision D6
**Feature:** none
**Verification:** human — no recipe
**Automated Test:** `scripts/tests/test_claude_code_adapter_claims.py` (`test_hook_*`, `test_goal_section_points_at_subagent_stop`, `test_model_*`, `test_permission_table_matches_frontmatter`, `test_final_structure_tree_lists_every_agent`)

**Preconditions:**
- Setup block pasted.

**Steps:**
1. Read the hook example: `sed -n '/^### Quality Gates with Hooks/,/^### The \/goal Stop Hook/p' "$REPO/adapters/claude-code.md"`
2. Check the `/goal` pointer: `sed -n '/^### The \/goal Stop Hook/,/^### /p' "$REPO/adapters/claude-code.md" | grep -o 'the `SubagentStop` example above'`
3. Check every agent's frontmatter `name` in the tier table, the permission table, and the tree:
   ```bash
   cd "$REPO"; A=adapters/claude-code.md
   for f in claude-code/agents/*.md; do
     n=$(awk 'NR==1&&/^---$/{f=1;next} f&&/^---$/{exit} f&&/^name:/{print $2}' "$f")
     t=$(sed -n '/^### Model Selection/,/^### Permission Modes/p' "$A" | grep -c "^| $n |")
     p=$(sed -n '/^### Permission Modes/,/^---/p' "$A" | grep -c "^| $n |")
     r=$(sed -n '/^### Final Structure/,/^---/p' "$A" | grep -c "$n\.md")
     echo "$n tier=$t perm=$p tree=$r"
   done
   ```

**Expected Result:**
- Step 1: a `.claude/settings.json` example with `"SubagentStop"` and `"matcher": "^writ-coder$"`; a hook script that reads `cwd` from the input JSON (`json.load(sys.stdin)["cwd"]`) and exits 2 when checks fail; a link to `https://code.claude.com/docs/en/hooks`; a statement that the docs do not say whether `cwd` is the subagent's worktree, so the orchestrator re-runs the checks in its own checkout after reconciling.
- Step 2: prints the phrase "the `SubagentStop` example above" once.
- Step 3: eight lines, each `tier=1 perm=1 tree=1`, for `writ-architect`, `writ-coder`, `writ-documenter`, `writ-evaluator`, `writ-reviewer`, `writ-story-gen`, `writ-tester`, `writ-visual-qa`.

**Status:** [x] Pass  [ ] Fail

**Notes:** This plan does not run the hook example; doing so needs an npm project and a live `writ-coder` run. AC-3.5 is a text check.
- agent-run 2026-10-21 @ b850e66: hook example has `"SubagentStop"`, `"matcher": "^writ-coder$"`, `json.load(sys.stdin)["cwd"]`, `exit 2`, the hooks-docs link, and the `cwd` caveat; the phrase "the `SubagentStop` example above" printed once; eight agents, each `tier=1 perm=1 tree=1`.

---

### Scenario 22: A session started in a subdirectory and the external-import approval (human, Claude Code)

**Source:** Error Map — Story 3 (Claude Code session: import resolves outside the working directory; out of scope for the scripts, stated by the adapter)
**Feature:** none
**Verification:** human — no recipe
**Automated Test:** none — manual only. A person must run this in an interactive Claude Code session.

**Preconditions:**
- Setup block pasted.
- Claude Code CLI installed and signed in.
- A temp project with a subdirectory:
  ```bash
  P="$W/s22"; mkdir -p "$P"; printf '# My project\n' > "$P/CLAUDE.md"; inst "$P" > /dev/null 2>&1; mkdir -p "$P/sub"; echo "$P/sub"
  ```

**Steps:**
1. In a new terminal, `cd` to the printed `sub` folder and start `claude`. Accept the folder-trust prompt if it appears.
2. Note whether Claude Code asks to approve an external import of `.claude/system-instructions.md`. If it asks, approve it.
3. Type `/context` and read **Memory files**.
4. Quit the session.

**Expected Result:**
- Step 2: the technical spec infers, without a source, that a prompt appears here, because the parent `CLAUDE.md`'s import resolves outside the working directory `sub/`. Record in Notes whether the prompt appeared.
- Step 3: **Memory files** lists the parent `CLAUDE.md` and `.claude/system-instructions.md`.
- Pass if Step 3 holds. The adapter states the approval as a condition ("an import that resolves outside the working directory"), so either outcome in Step 2 is consistent with it. A missing prompt only means the spec's inference was wrong.

**Status:** [x] Pass  [ ] Fail

**Notes:** Scenario 23 covers the plainer case, a session started at the project root. Declining the prompt disables external imports for the project (memory docs); this plan does not test the decline path because resetting it is outside Writ.
- needs live session (Claude Code): interactive `claude` session in the temp project; the agent did not start `claude`. Record whether the external-import prompt appears, then `/context` → Memory files.
- live run 2026-10-22 (maintainer, Claude Code, started in s22/sub): /context Memory files listed the parent CLAUDE.md and .claude/system-instructions.md. Whether the external-import prompt appeared was not reported.

---

### Scenario 23: A Claude Code session loads `.claude/system-instructions.md` through the import (human, Claude Code)

**Source:** Experience Design — Story 3 (Who uses it: developers need the Prime Directive in every session); Spec Success Criteria (import line). Validates Stories 1 and 2 end to end.
**Feature:** none
**Verification:** human — no recipe
**Automated Test:** none — manual only. A person must run this in an interactive Claude Code session.

**Preconditions:**
- Setup block pasted.
- Claude Code CLI installed and signed in.
- A temp project:
  ```bash
  P="$W/s23"; mkdir -p "$P"; printf '# My project\n\nProject notes.\n' > "$P/CLAUDE.md"; inst "$P" > /dev/null 2>&1; echo "$P"
  ```

**Steps:**
1. In a new terminal, `cd` to the folder printed above and start `claude`. Accept the folder-trust prompt if it appears.
2. Note whether Claude Code asks to approve an external import.
3. Type `/context` and read the **Memory files** section.
4. Quit the session (`/exit`).

**Expected Result:**
- Step 2: no import-approval prompt (the import resolves inside the working directory).
- Step 3: **Memory files** lists the project `CLAUDE.md` and `.claude/system-instructions.md` (alongside any user-level memory files you already have).

**Status:** [x] Pass  [ ] Fail

**Notes:** Claude Code docs name `/context` for this check (technical spec → Verification). If the file is missing from the list, check that `CLAUDE.md` line 8 is exactly `@.claude/system-instructions.md` with no backticks.
- needs live session (Claude Code): interactive `claude` session in the temp project; the agent did not start `claude`. Expect no import prompt; `/context` → Memory files lists `CLAUDE.md` and `.claude/system-instructions.md`.
- live run 2026-10-22 (maintainer, Claude Code): no external-import prompt; /context Memory files listed CLAUDE.md and .claude/system-instructions.md.

---

## Story 4: Keep CLAUDE.md User-Owned on Uninstall and Reinstall

### Scenario 24: Uninstall removes exactly the block lines and keeps the file mode

**Source:** Acceptance Criteria — Story 4 (AC-4.1); Edge Cases (blank lines next to the block kept; file mode unchanged); Decision D5
**Feature:** none
**Verification:** human — no recipe
**Automated Test:** `scripts/tests/test_remove_claude_md_block.sh` (AC-4.1 cases); `scripts/tests/test_uninstall_claude_md.sh` (project A)

**Preconditions:**
- Setup block pasted.

**Steps:**
1. Install over a hand-written file, then add a blank line before the start marker, user text with blank lines after the end marker, a CRLF end marker, and no final newline; set mode 0640:
   ```bash
   P="$W/s24"; mkdir -p "$P"; user_md "$P/CLAUDE.md"; inst "$P" > /dev/null 2>&1
   perl -pi -e 's/^<!-- writ:start -->$/\n<!-- writ:start -->/; s/^<!-- writ:end -->$/<!-- writ:end -->\r/' "$P/CLAUDE.md"
   printf '\n\n## After the block\r\nUser text below.  \n\nTrailing line, no newline' >> "$P/CLAUDE.md"
   chmod 640 "$P/CLAUDE.md"; { part pre "$P/CLAUDE.md"; part post "$P/CLAUDE.md"; } > "$W/s24.expect"
   ```
2. Uninstall and compare:
   ```bash
   uninst "$P" > "$W/s24.txt" 2>&1; echo "exit $?"; grep 'CLAUDE.md' "$W/s24.txt"
   cmp "$W/s24.expect" "$P/CLAUDE.md" && echo "only the block lines were removed"
   stat -f '%Sp' "$P/CLAUDE.md"; grep -c $'\r$' "$P/CLAUDE.md"; tail -c 30 "$P/CLAUDE.md" | od -An -c
   ```

**Expected Result:**
- Step 2: `exit 0`; `    📄 Extras:    2 (.claude/system-instructions.md CLAUDE.md Writ block)` and `  🗑  Removed: CLAUDE.md Writ block`; `only the block lines were removed`; `-rw-r-----`; `3` CRLF lines left (two from the hand-written top, one from the text after the block); the tail shows `.`, two spaces, `\n \n`, then `Trailing line, no newline` with no final `\n`.

**Status:** [x] Pass  [ ] Fail

**Notes:** Codex's `remove_agents_md_block` trims blank lines and adds a final newline; the Claude function deliberately does not (D5).
- agent-run 2026-10-21 @ b850e66: exit 0, `Extras:    2 (…)`, `🗑  Removed: CLAUDE.md Writ block`, `only the block lines were removed`, `-rw-r-----`, `3` CRLF lines; tail shows `.`, two spaces, `\n`, `\n`, then `Trailing line, no newline` with no final newline.

**Implementation Reference:** Story 4 — `remove_claude_md_block` in the `writ-remove-claude-md-bundled` region of `scripts/uninstall.sh` (`head`/`tail`, `cat "$tmp" >"$file"`).

---

### Scenario 25: Block-only, no-marker, malformed, and missing `CLAUDE.md` on uninstall

**Source:** Acceptance Criteria — Story 4 (AC-4.2); Error Map (Uninstall removes block: no `CLAUDE.md`; no markers; malformed markers; zero bytes left); Shadow Path (Uninstall: nil, empty, upstream error); Experience Design (States: uninstall with only the block; no markers; malformed markers)
**Feature:** none
**Verification:** human — no recipe
**Automated Test:** `scripts/tests/test_remove_claude_md_block.sh` (AC-4.2 cases); `scripts/tests/test_uninstall_claude_md.sh` (projects B and D)

**Preconditions:**
- Setup block pasted.

**Steps:**
1. `CLAUDE.md` holds only the block:
   ```bash
   P="$W/s25a"; inst "$P" > /dev/null 2>&1; uninst "$P" > "$W/s25a.txt" 2>&1; echo "exit $?"; grep 'Removed: CLAUDE.md' "$W/s25a.txt"; ls "$P/CLAUDE.md" 2>&1 | grep -c 'No such file'
   ```
2. `CLAUDE.md` has no markers:
   ```bash
   P="$W/s25b"; inst "$P" > /dev/null 2>&1; printf '# Mine\nNo Writ block here.\n' > "$P/CLAUDE.md"; H0=$(h "$P/CLAUDE.md")
   uninst "$P" > "$W/s25b.txt" 2>&1; echo "exit $?"; grep '✓ CLAUDE.md' "$W/s25b.txt"; [ "$(h "$P/CLAUDE.md")" = "$H0" ] && echo "CLAUDE.md unchanged"
   ```
3. Two start markers, then end before start:
   ```bash
   P="$W/s25c"; inst "$P" > /dev/null 2>&1; printf '<!-- writ:start -->\nstray second start\n' >> "$P/CLAUDE.md"; H0=$(h "$P/CLAUDE.md")
   uninst "$P" > "$W/s25c.out" 2> "$W/s25c.err"; echo "exit $?"; cat "$W/s25c.err"; [ "$(h "$P/CLAUDE.md")" = "$H0" ] && echo "CLAUDE.md unchanged"; ls -A "$P/.claude"
   P="$W/s25d"; inst "$P" > /dev/null 2>&1
   perl -0pi -e 's/<!-- writ:start -->/TMPMARK/; s/<!-- writ:end -->/<!-- writ:start -->/; s/TMPMARK/<!-- writ:end -->/' "$P/CLAUDE.md"; H0=$(h "$P/CLAUDE.md")
   uninst "$P" > "$W/s25d.out" 2> "$W/s25d.err"; echo "exit $?"; cat "$W/s25d.err"; [ "$(h "$P/CLAUDE.md")" = "$H0" ] && echo "CLAUDE.md unchanged"
   ```
4. No `CLAUDE.md`: through `uninstall.sh`, then by calling the function directly:
   ```bash
   P="$W/s25e"; inst "$P" > /dev/null 2>&1; rm "$P/CLAUDE.md"
   uninst "$P" > "$W/s25e.txt" 2>&1; echo "exit $?"; grep -e 'Extras' -e 'CLAUDE.md' "$W/s25e.txt"
   mkdir -p "$W/s25f" && cd "$W/s25f" && bash -c 'eval "$(sed -n "/writ-remove-claude-md-bundled-begin/,/writ-remove-claude-md-bundled-end/p" "$1")"
     remove_claude_md_block CLAUDE.md; echo "rc=$? note=$REMOVE_CLAUDE_MD_NOTE"' _ "$SRC/scripts/uninstall.sh"; ls -A | wc -l
   ```

**Expected Result:**
- Step 1: `exit 0`; `  🗑  Removed: CLAUDE.md (empty after Writ block removal)`; `1` (file gone).
- Step 2: `exit 0`; `  ✓ CLAUDE.md (no Writ block present)`; `CLAUDE.md unchanged`.
- Step 3: first project: `exit 13`; `❌ CLAUDE.md block error: malformed markers (expected exactly one <!-- writ:start --> and one <!-- writ:end -->).`; `CLAUDE.md unchanged`; `.claude/` holds only `.writ-manifest`. Second project: `exit 13`; `❌ CLAUDE.md block error: malformed markers (invalid marker order).`; `CLAUDE.md unchanged`.
- Step 4: `exit 0`; `    📄 Extras:    1 (.claude/system-instructions.md)` and no other `CLAUDE.md` line; then `rc=0 note=✓ CLAUDE.md (no file present)` and `0` (nothing created).

**Status:** [x] Pass  [ ] Fail

**Notes:**
- Step 3: by the time uninstall stops with 13, it has already removed commands, agents, skills, and `.claude/system-instructions.md`; only the manifest and `CLAUDE.md` remain. The spec keeps this, matching Codex ("do not add new recovery").
- Step 4: the error map says the person sees `✓ CLAUDE.md (no file present)`. Through `uninstall.sh` they see nothing about `CLAUDE.md`, because the call site checks for the file first (as the Codex branch does). The note exists only at function level, which is what AC-4.2 tests.
- agent-run 2026-10-21 @ b850e66: step 1 exit 0, `Removed: CLAUDE.md (empty after Writ block removal)`, `1`; step 2 exit 0, `✓ CLAUDE.md (no Writ block present)`, unchanged; step 3 exit 13 `(expected exactly one …)`, unchanged, `.claude/` = `.writ-manifest`; exit 13 `(invalid marker order)`, unchanged.
- Step 4: exit 0, `Extras:    1 (.claude/system-instructions.md)` and no other `CLAUDE.md` line; `rc=0 note=✓ CLAUDE.md (no file present)`, `0`.

---

### Scenario 26: Install → uninstall round trip, and a dry run that changes nothing

**Source:** Acceptance Criteria — Story 4 (AC-4.3); Edge Case (round trip on a file with no final newline); Experience Design (State: uninstall)
**Feature:** none
**Verification:** human — no recipe
**Automated Test:** `scripts/tests/test_uninstall_claude_md.sh` (projects A, B, C)

**Preconditions:**
- Setup block pasted.

**Steps:**
1. Project A, a hand-written `CLAUDE.md`:
   ```bash
   P="$W/s26a"; mkdir -p "$P"; user_md "$P/CLAUDE.md"; cp "$P/CLAUDE.md" "$W/s26a.orig"
   inst "$P" > /dev/null 2>&1; uninst "$P" > "$W/s26a.txt" 2>&1; echo "exit $?"; grep 'Removed: CLAUDE.md' "$W/s26a.txt"
   { cat "$W/s26a.orig"; printf '\n'; } | cmp - "$P/CLAUDE.md" && echo "CLAUDE.md = original + one newline"
   ```
2. Project B, no `CLAUDE.md` before install:
   ```bash
   P="$W/s26b"; inst "$P" > /dev/null 2>&1; uninst "$P" > /dev/null 2>&1; echo "exit $?"; ls -A "$P"
   ```
3. Project C, dry run:
   ```bash
   P="$W/s26c"; mkdir -p "$P"; user_md "$P/CLAUDE.md"; inst "$P" > /dev/null 2>&1; D0=$(digest "$P")
   uninst "$P" --dry-run > "$W/s26c.txt" 2>&1; echo "exit $?"; grep 'CLAUDE.md Writ block' "$W/s26c.txt"; [ "$(digest "$P")" = "$D0" ] && echo "dry run changed nothing"
   ```

**Expected Result:**
- Step 1: `exit 0`; `  🗑  Removed: CLAUDE.md Writ block`; `CLAUDE.md = original + one newline`.
- Step 2: `exit 0`; `.cursorindexingignore`, `.writ`, `scripts` (no `CLAUDE.md`, no `.claude/`).
- Step 3: `exit 0`; `    📄 Extras:    2 (.claude/system-instructions.md CLAUDE.md Writ block)` and `  🗑  CLAUDE.md Writ block`; `dry run changed nothing`.

**Status:** [x] Pass  [ ] Fail

**Notes:**
- agent-run 2026-10-21 @ b850e66: A exit 0, `🗑  Removed: CLAUDE.md Writ block`, `CLAUDE.md = original + one newline`; B exit 0, `.cursorindexingignore .writ scripts`; C exit 0, `Extras:    2 (…)` and `🗑  CLAUDE.md Writ block`, `dry run changed nothing`.

---

### Scenario 27: The lifecycle command docs never delete or overwrite `CLAUDE.md`

**Source:** Acceptance Criteria — Story 4 (AC-4.4); Business Rule 16
**Feature:** none
**Verification:** human — no recipe
**Automated Test:** `scripts/tests/test_lifecycle_commands_claude_md.py`

**Preconditions:**
- Setup block pasted.

**Steps:**
1. Search for the old commands:
   ```bash
   cd "$REPO"
   grep -nE 'rm\s+(-\S+\s+)*\S*CLAUDE\.md' commands/uninstall-writ.md; echo "rm: exit $?"
   grep -nE 'cp\s+\S*claude-code/CLAUDE\.md\s+(\./)?CLAUDE\.md' commands/reinstall-writ.md commands/uninstall-writ.md; echo "cp: exit $?"
   ```
2. Read the Claude bullets and the "Do NOT remove" lines:
   ```bash
   cd "$REPO"
   grep -n 'Claude Code:.*writ:start' commands/uninstall-writ.md commands/reinstall-writ.md | cut -c1-200
   grep -c 'install.sh --platform claude --force' commands/reinstall-writ.md
   ```

**Expected Result:**
- Step 1: no lines; `rm: exit 1` and `cp: exit 1`.
- Step 2: five lines: `uninstall-writ.md:99` (remove only the Writ block, keep every other byte, delete `CLAUDE.md` only if nothing is left), `uninstall-writ.md:110` (do not remove content outside the markers, including blank lines next to the block), `reinstall-writ.md:116` (leave `CLAUDE.md` in place; Step 4 replaces only the lines between the markers), `reinstall-writ.md:123` (do not remove content outside the markers), `reinstall-writ.md:143` (merge the template the way `install.sh --platform claude --force` does; never copy the template over the file). Count `1`.

**Status:** [x] Pass  [ ] Fail

**Notes:** `uninstall-writ.md`'s frontmatter `exit_criteria` (line 10) and its Step 2 confirm prompt still name only `AGENTS.md` content outside the markers (Story 4 evaluator residual). Not in AC-4.4.
- agent-run 2026-10-21 @ b850e66: `rm: exit 1`, `cp: exit 1`; five lines at `uninstall-writ.md:99`, `:110`, `reinstall-writ.md:116`, `:123`, `:143` with the expected text (99 ends "delete `CLAUDE.md` only if nothing is left"; 143 says "Never copy the template over the file"); count `1`.

---

### Scenario 28: `/reinstall-writ` in a Claude Code session keeps the user's text (human, Claude Code)

**Source:** Error Map — Story 4 (Reinstall merges block: user follows `/reinstall-writ` Step 4); Experience Design (State: `/reinstall-writ` on Claude Code); Business Rule 1
**Feature:** none
**Verification:** human — no recipe
**Automated Test:** none — manual only. A person must run this in an interactive Claude Code session; the agent follows the command doc, so no script exercises it.

**Preconditions:**
- Setup block pasted.
- Claude Code CLI installed and signed in; network access to github.com (`/reinstall-writ` Step 4 clones upstream `main`).
- A temp project with user text on both sides of the block:
  ```bash
  P="$W/s28"; mkdir -p "$P"; printf '# My project\r\nKeep this.  \n' > "$P/CLAUDE.md"; inst "$P" > /dev/null 2>&1
  printf '\n## After the block\nMore of my text.\n' >> "$P/CLAUDE.md"
  part pre "$P/CLAUDE.md" > "$W/s28.pre"; part post "$P/CLAUDE.md" > "$W/s28.post"
  rm "$P/.claude/commands/status.md"   # reinstall must put this back; proves it ran
  echo "$P"
  ```

**Steps:**
1. In a new terminal, `cd` to the printed folder and start `claude`.
2. Run `/reinstall-writ`. Choose Claude Code and confirm.
3. Watch the commands the agent runs. Quit when it reports done.
4. Back in the setup shell:
   ```bash
   part pre "$P/CLAUDE.md" | cmp - "$W/s28.pre" && part post "$P/CLAUDE.md" | cmp - "$W/s28.post" && echo "outside bytes unchanged"
   grep -c '^<!-- writ:start -->' "$P/CLAUDE.md"; ls "$P/.claude/system-instructions.md" "$P/.claude/commands/status.md"
   ```

**Expected Result:**
- Step 3: the agent never runs `rm CLAUDE.md` and never copies `claude-code/CLAUDE.md` onto `CLAUDE.md`. It replaces only the lines between the markers.
- Step 4: `outside bytes unchanged`; `1`; both files exist (`status.md` is back, so the reinstall ran).

**Status:** [x] Pass  [ ] Fail

**Notes:** The command doc the agent follows comes from this branch (installed from `$SRC`). The template it merges comes from GitHub `main`, so until Phase 13 is merged the new block may lack the import line. That does not affect this scenario, which checks the bytes outside the block.
- needs live session (Claude Code): interactive `claude` session in the temp project; the agent did not start `claude`. Also needs network access to github.com: `/reinstall-writ` Step 4 clones upstream `main`.
- live run 2026-10-22 (maintainer, Claude Code): /reinstall-writ ran without rm CLAUDE.md or a template copy over it. verify-s28.sh re-run by Claude: 'outside bytes unchanged', one Writ block, .claude/commands/status.md and .claude/system-instructions.md present.

---

### Scenario 29: Only whitespace left after the block is removed: the file is kept

**Source:** Edge Case — Story 4 (uninstall leaves only whitespace in `CLAUDE.md`); Decision D5
**Feature:** none
**Verification:** human — no recipe
**Automated Test:** `scripts/tests/test_remove_claude_md_block.sh` (whitespace-only remainder case)

**Preconditions:**
- Setup block pasted.

**Steps:**
1. A file with two blank lines, install, then two spaces and a newline after the block:
   ```bash
   P="$W/s29"; mkdir -p "$P"; printf '\n\n' > "$P/CLAUDE.md"; inst "$P" > /dev/null 2>&1; printf '  \n' >> "$P/CLAUDE.md"
   uninst "$P" > "$W/s29.txt" 2>&1; echo "exit $?"; grep 'Removed: CLAUDE.md' "$W/s29.txt"; od -An -c "$P/CLAUDE.md"
   ```

**Expected Result:**
- `exit 0`; `  🗑  Removed: CLAUDE.md Writ block`; the file holds 5 bytes: `\n  \n          \n` (two newlines, two spaces, a newline).

**Status:** [x] Pass  [ ] Fail

**Notes:** `commands/uninstall-writ.md` says "delete `CLAUDE.md` only if nothing is left"; the script means zero bytes. A person following the doc by hand could delete this file (Story 4 evaluator residual).
- agent-run 2026-10-21 @ b850e66: exit 0, `🗑  Removed: CLAUDE.md Writ block`; file is 5 bytes: `\n`, `\n`, two spaces, `\n`.

---

### Scenario 30: `/uninstall-writ` in a Claude Code session keeps the user's text (human, Claude Code)

**Source:** Experience Design — Story 4 (State: uninstall, every byte outside the block stays); Acceptance Criteria context (AC-4.4 doc text, followed by an agent); Business Rule 1
**Feature:** none
**Verification:** human — no recipe
**Automated Test:** none — manual only. A person must run this in an interactive Claude Code session.

**Preconditions:**
- Setup block pasted.
- Claude Code CLI installed and signed in.
- A temp project with user text on both sides of the block:
  ```bash
  P="$W/s30"; mkdir -p "$P"; printf '# My project\r\nKeep this.  \n' > "$P/CLAUDE.md"; inst "$P" > /dev/null 2>&1
  printf '\n## After the block\nMore of my text.\n' >> "$P/CLAUDE.md"
  { part pre "$P/CLAUDE.md"; part post "$P/CLAUDE.md"; } > "$W/s30.expect"; echo "$P"
  ```

**Steps:**
1. In a new terminal, `cd` to the printed folder and start `claude`.
2. Run `/uninstall-writ`. Choose Claude Code and confirm.
3. Watch the commands the agent runs. Quit when it reports done.
4. Back in the setup shell:
   ```bash
   cmp "$W/s30.expect" "$P/CLAUDE.md" && echo "only the block was removed"
   ls "$P/.claude/system-instructions.md" 2>&1 | grep -c 'No such file'; ls -d "$P/.writ"
   ```

**Expected Result:**
- Step 3: the agent never runs `rm CLAUDE.md`. It removes only the start-marker line through the end-marker line.
- Step 4: `only the block was removed`; `1` (`.claude/system-instructions.md` is gone); `.writ` still exists.

**Status:** [x] Pass  [ ] Fail

**Notes:** If the agent trims a blank line next to the block, `cmp` fails. That would be a Fail against Business Rule 1 even though `uninstall.sh` itself keeps those bytes (Scenario 24).
- needs live session (Claude Code): interactive `claude` session in the temp project; the agent did not start `claude`. Then compare `$W/s30.expect` with `CLAUDE.md`.
- live run 2026-10-22 (maintainer, Claude Code): /uninstall-writ did not rm CLAUDE.md. verify-s30.sh re-run by Claude: 'only the block was removed', 1, .writ kept.

---

### Scenario 31: Every suite passes and eval reports 0 findings

**Source:** Spec Success Criteria — all stories ("Full `eval.sh` reports 0 findings. pytest and the bash tests pass."; "The generator `--check` passes on the committed template")
**Feature:** none
**Verification:** human — no recipe
**Automated Test:** CI runs all of these on each PR (`.github/workflows/eval.yml`)

**Preconditions:**
- Setup block pasted. `uv` installed. Run outside any sandbox; the bash tests and eval run `git init` in temp folders.

**Steps:**
1. `cd "$CL" && uv run --python 3.9 pytest -q 2>&1 | tail -1`
2. `cd "$CL" && for t in scripts/tests/test_*.sh; do bash "$t" >/dev/null 2>&1 || echo "FAIL $t"; done; echo "bash tests done"`
3. `cd "$CL" && bash scripts/eval.sh --report="$W/s31-eval.md" >/dev/null 2>&1; echo "exit $?"; sed -n '/^## Summary/,$p' "$W/s31-eval.md"`
4. `cd "$CL" && python3 scripts/gen-claude-md.py --check | tail -1`

**Expected Result:**
- Step 1: `2682 passed, 2 skipped` (more passed if tests were added later), no failures.
- Step 2: no `FAIL` line, then `bash tests done` (44 bash tests at generation; the loop took about 9 minutes).
- Step 3: `exit 0`; `Findings: 0`, `Run errors: 0`.
- Step 4: `gen-claude-md: pass (32 commands, 8 agents)`.

**Status:** [x] Pass  [ ] Fail

**Notes:**
- agent-run 2026-10-21 @ b850e66: step 1 `2774 passed, 2 skipped in 215.09s` (Python 3.9; more tests than the plan's 2682, legitimate growth); step 2 no `FAIL` line, `bash tests done` (45 tests, about 12 minutes); step 3 exit 0, `Findings: 0`, `Run errors: 0`; step 4 `gen-claude-md: pass (32 commands, 8 agents)`.

---

## Automated vs. Manual

| Kind | Scenarios | Count |
|---|---|---|
| Asserted by a committed test (CI runs it) | 1, 2, 3, 4, 5, 6, 7, 9, 10, 11, 12, 13, 14, 18, 19, 21, 24, 25, 26, 27, 29, 31 | 22 |
| Partly automated (a test covers part; the rest is manual) | 8, 15, 16, 17, 20 | 5 |
| Manual only: a person in an interactive Claude Code session | 22, 23, 28, 30 | 4 |

Scenario 31 runs the suites themselves. Every scenario in the first two rows can also be run by hand from the shell with the steps above.

## Not Covered by This Plan

- **Uninstall prints no `CLAUDE.md` line when the file is absent.** The error map's `✓ CLAUDE.md (no file present)` is reachable only by calling `remove_claude_md_block` directly (Scenario 25, step 4). Spec text versus script; behavior is safe.
- **A read-only `CLAUDE.md` stops uninstall with exit 1** after commands, agents, and skills are removed; the old `rm -f` succeeded (Story 4 evaluator residual). Not tested here.
- **`uninstall.sh --help`** does not say that `CLAUDE.md` is edited (Story 4 evaluator residual).
- **`merge_claude_md` leaves `CLAUDE.md` at mode 0600** after install or update (Scenario 9 Notes). Out of scope in the technical spec.
- **`unlink.sh` does not record `system-instructions.md` for Claude.** Matters only for legacy symlinked installs (Story 2 reviewer note).
- **`update.sh` "manifest present, no baseline line, local differs" branch** has no test on either platform (DEV-009, Scenario 11 Notes).
- **The `SubagentStop` hook example is not executed** (Scenario 21 Notes), and whether `@` imports expand inside subagents is undocumented (technical spec → Import Line).
- **`scripts/measure-invocation.py` cites `adapters/claude-code.md:396`**, which was stale before this spec (Story 3 reviewer note).
- **The generator's manifest reader drops an entry that does not start with `  - name:`.** `check_manifest` (through `gen-skill.sh --dry-run`) rejects such a manifest in CI (Story 1 evaluator residual).

## Pending Stories

None. All four stories are Completed ✅.
