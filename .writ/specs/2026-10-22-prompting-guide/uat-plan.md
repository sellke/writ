# UAT Plan: Prompting Guide

> **Generated:** 2026-10-22
> **Spec:** `.writ/specs/2026-10-22-prompting-guide/`
> **Stories Covered:** 2 of 2 completed
> **Total Scenarios:** 9
> **Verification recipe:** does not apply. Writ is markdown plus Python and bash scripts with no application to boot, so no `.writ/docs/app-verification.md` was drafted, saved, or bound (Step 1.3 asked nothing). Every scenario is `human — no recipe`.

## How to Use This Plan

1. Work through scenarios in order (they're grouped by story, ordered by priority)
2. For each scenario, follow the steps exactly as written
3. Mark Pass or Fail — add notes for any unexpected behavior
4. Scenarios marked Fail should be filed as issues or fed back to the spec
5. A feature passes UAT when all scenarios pass (or failures are accepted as known limitations)

**Conventions for this plan:**

- There is no app to boot and no recipe. Scenarios 1 to 5 are reads of the shipped guide and the README; 6 and 9 run the repository's own checks; 7 proves the guide is in the ship set; 8 is the negative case, where edits in a scratch clone make the named test fail.
- **Never run `install.sh` or `update.sh` in the Writ repo.** `.claude/` and `.cursor/` there are symlinks into the source. Scenario 7 previews an install from a clone into a sample project inside `$W`.
- Every helper refuses to run unless the shell is inside `$W`. `$REPO` is cloned from and never written to. Run the plan in `bash` on macOS (`sed -i ''`), outside any sandbox.
- Paste this setup block once per shell. Stop if the first line does not print `W=/...`. The `W=$PWD` after the `cd` normalizes a `$TMPDIR` that ends in `/`; without it every helper refuses.

  ```bash
  W=$(mktemp -d "${TMPDIR:-/tmp}/writ-uat-guide.XXXXXX") && cd "$W" && W=$PWD && echo "W=$W"
  REPO=/Users/asellke/Projects/writ            # read only: cloned from, never edited, never installed into
  CL="$W/clone"; git clone -q "$REPO" "$CL"    # committed tree on the current branch
  G="$CL/.writ/docs/prompting-guide.md"
  SAMPLE="$W/sample"; mkdir -p "$SAMPLE" && cd "$SAMPLE" && git init -q \
    && printf '# sample\n' > README.md && git add -A && git commit -qm "sample project" && cd "$W"
  inW() { case "$PWD/" in "$W"/*) ;; *) echo "refusing: $PWD is outside $W" >&2; return 1;; esac; }
  # pt <pytest args>: run the guide's test file on Python 3.9 inside the clone
  pt() { inW && (cd "$CL" && uv run --python 3.9 pytest scripts/tests/test_prompting_guide.py "$@"); }
  # dryrun: preview an install from the clone into $SAMPLE; never touches $REPO
  dryrun() { inW && (cd "$SAMPLE" && bash "$CL/scripts/install.sh" --dry-run --platform claude); }
  # shipfn <script> <filename>: the test's own extraction and call; exit 64 means no function found
  shipfn() { inW && bash -c 'fn=$(sed -n "/^is_shippable_writ_doc()/,/^}/p" "$1"); [ -n "$fn" ] || exit 64; source /dev/stdin <<<"$fn"; is_shippable_writ_doc "$2"' bash "$1" "$2"; echo "exit $?"; }
  # reset: undo every edit to tracked files in the clone; prints nothing when clean
  reset() { inW && git -C "$CL" checkout -q -- . && git -C "$CL" status --short; }
  ```

- Expected output was observed on 2026-10-22 against `016ad21` (branch `phase/14-front-door-and-distribution`). Story 1 landed in `4fe27c7`, Story 2 in `9c21831`. After each scenario that edits the clone, run `reset` and confirm it prints nothing. When done: `rm -rf "$W"`.
- Drift log: DEV-001 to DEV-004 are Small and auto-amended. Three change what a reader sees and are named where they appear: DEV-001 (a colon, not an em-dash, after each bold part name; Scenario 1), DEV-002 (the opening paragraph states coverage instead of the sketch's metaphor; Scenario 1), DEV-003 (the roadmap Route line adds "where N is the phase number"; Scenario 2). DEV-004 (here-string sourcing in `test_ships`) changes no reader-visible text; the `shipfn` helper uses the shipped form (Scenario 7).

## Coverage Summary

| Story | Status | Scenarios | Source Breakdown |
|-------|--------|-----------|-----------------|
| Story 1: Write the Prompting Guide | ✅ Covered | 4 | AC: 4, Errors: 0, Shadow: 0, Edge: 0 (Experience Design folded into Scenario 1; both spec-lite edge cases named on Scenarios 2 and 4) |
| Story 2: Ship, Link, and Pin the Guide | ✅ Covered | 5 | AC: 4, Errors: 0, Shadow: 1, Edge: 0 |

The technical spec's Error & Rescue Map is "Not required" (documentation only), so there are no error scenarios. Scenario 8 covers all three non-happy shadow paths (Empty input, Nil input, Upstream error) in one run. No pending stories: both are Completed ✅.

---

## Story 1: Write the Prompting Guide

### Scenario 1: A new user reads the guide: title, opening paragraph, and the three parts

**Source:** Acceptance Criteria (AC-1.2) — Story 1; Experience Design "Happy path" and State Catalog "Fresh install"; Business Rules 1 and 2
**Feature:** none
**Verification:** human — no recipe

**Preconditions:**
- Setup block pasted.

**Steps:**
1. `grep -n '^## ' "$G"`
2. `sed -n '1,11p' "$G"`
3. Read the whole file top to bottom once, timing yourself.

**Expected Result:**
- Step 1: exactly three lines, `5:## What a request carries`, `13:## Recipes`, `55:## Pitfalls`, in that order and spelled so (the front door cites these by text).
- Step 2: the H1 `# Prompting Guide`; one paragraph that names the three sections and says to read the guide once before the first request (DEV-002); under the first H2 exactly three list items beginning `- **Goal**:`, `- **Done check**:`, `- **Proof**:`, one sentence each (DEV-001: a colon follows each bold name); then the line "The strong examples below state all three in a few sentences."
- Step 3: the read takes under two minutes, the time the README claims; nothing in it assumes a Writ maintainer's artifacts (research, ADRs, spec folders).

**Status:** [ ] Pass  [ ] Fail

**Notes:**

---

### Scenario 2: Five recipes in the contracted order, each with one Weak, Strong, and Route line

**Source:** Acceptance Criteria (AC-1.3) — Story 1; Business Rule 3; Edge case "A `Route:` line with extra flags passes if the contracted command is named"
**Feature:** none
**Verification:** human — no recipe

**Preconditions:**
- Setup block pasted.

**Steps:**
1. `grep -n '^### ' "$G"`
2. `grep -c -E '^(Weak|Strong|Route):' "$G"; grep -n '^Route:' "$G"`
3. Read each recipe's `Weak:` and `Strong:` lines.

**Expected Result:**
- Step 1: five lines in this order: `15:### An unsettled idea`, `23:### A bug or a small change`, `31:### A feature`, `39:### Roadmap work`, `47:### A why or how question`.
- Step 2: `15` (three labelled lines per recipe), then five Route lines: `` `/prototype` `` with no `--no-diverge`; `` `/prototype --no-diverge` ``; `` `/create-spec` ``; `` `/implement-phase <N>`, where N is the phase number `` (DEV-003 added the clause; the command is still named); `` `/research` (`/why` replaces it when it ships) ``.
- Step 3: each Weak line is a one-line request with no done check (`Fix the login bug.`, `Add export.`); each Strong line is one line that states a goal, a "Done when" check, and a "Proof:" clause (the bug recipe's `a+b@example.com` test, for one). Labels sit at column 0 with a blank line between them.

**Status:** [ ] Pass  [ ] Fail

**Notes:**

---

### Scenario 3: Five one-sentence pitfalls, in plain prose with no em-dash

**Source:** Acceptance Criteria (AC-1.5) — Story 1; Business Rules 4 and 8
**Feature:** none
**Verification:** human — no recipe

**Preconditions:**
- Setup block pasted.

**Steps:**
1. `awk '/^## Pitfalls/{p=1;next} p&&/^- /' "$G"`
2. `grep -c '—' "$G"`
3. The step 1 scan from `skills/plain-prose/SKILL.md`: `grep -nwiE "comprehensive|robust|seamless(ly)?|elegant(ly)?|powerful|crucial|meticulous(ly)?|genuinely|truly|holistic|paramount|pivotal|leverage|streamline|delve|journey|landscape|navigate|unlock|non-negotiable|note that|it'?s (important|worth) (to note|noting)|keep in mind|remember:|this ensures|ensures? that|earns its place|the beauty of|think of (it|this) as" "$G"`, then `grep -nE "— not [a-z]|: not [a-z]|not (just|only|merely|simply) [^.]{0,40},? but|isn'?t (just|only|merely|simply) |is more than (just )?an?\b" "$G"`

**Expected Result:**
- Step 1: exactly five items, one sentence each, in this order: no done check; asking "A or B?" when running both would answer it; specifying the how instead of the what; bundling several requests into one; restating the codebase to the agent. Each names the pitfall before the colon and the fix after it.
- Step 2: `0`.
- Step 3: no output from either grep.

**Status:** [ ] Pass  [ ] Fail

**Notes:**

---

### Scenario 4: Under the line budget, with no links and no Writ-internal path

**Source:** Acceptance Criteria (AC-1.1, AC-1.4) — Story 1; State Catalog "Guide over 150 lines" and "Guide links a Writ-internal path"; Business Rules 6 and 7; Edge case "Exactly 150 lines fails (`< 150`)"
**Feature:** none
**Verification:** human — no recipe

**Preconditions:**
- Setup block pasted.

**Steps:**
1. `wc -l < "$G"`
2. `grep -c '](' "$G"`
3. `grep -n '\.writ/' "$G"; echo "rc=$?"`
4. `grep -n -i 'writ' "$G"`

**Expected Result:**
- Step 1: `61`. The test asserts strictly under 150, so 150 itself would fail; the ceiling is not a target.
- Step 2: `0`: the guide carries no Markdown link at all.
- Step 3: no lines and `rc=1`: nothing under `.writ/research/`, `.writ/decision-records/`, `.writ/specs/`, `.writ/product/`, or any other `.writ/` path.
- Step 4: one hit, line 57, the word "write" in the first pitfall. The guide names neither Writ nor a `/writ` command (the front-door spec adds that later).

**Status:** [ ] Pass  [ ] Fail

**Notes:**

---

## Story 2: Ship, Link, and Pin the Guide

### Scenario 5: README Quick Start points to the guide before the five-command table

**Source:** Acceptance Criteria (AC-2.1) — Story 2; State Catalog "Fresh install, README Quick Start"; Experience Design "Entry"
**Feature:** none
**Verification:** human — no recipe

**Preconditions:**
- Setup block pasted.

**Steps:**
1. `awk '/^## Quick Start/{p=1} p' "$CL/README.md" | sed -n '1,8p'`
2. `grep -n '^New here' "$CL/README.md"`
3. Open the link target relative to `$CL`: `wc -l < "$CL/.writ/docs/prompting-guide.md"`

**Expected Result:**
- Step 1: `## Quick Start`, a blank line, `` New here? Read [`.writ/docs/prompting-guide.md`](.writ/docs/prompting-guide.md) (two minutes). ``, a blank line, `Writ ships 32 commands, but you only need five to go from idea to PR:`, a blank line, then the `| Command | What it does |` table header. The pointer sits above the table and the lead-in sentence keeps its colon.
- Step 2: exactly one line, `215`. The sentence ends at "(two minutes)." with no `/writ` clause (the front-door spec appends it).
- Step 3: `61`: the link resolves from the repository root.

**Implementation Reference:** Story 2 — `README.md` § Quick Start (lines 215 to 216).

**Status:** [ ] Pass  [ ] Fail

**Notes:**

---

### Scenario 6: The seven pinned tests pass on Python 3.9, from one test file

**Source:** Acceptance Criteria (AC-2.2, AC-2.3, AC-2.4) — Story 2; Shadow Path "Happy path"
**Feature:** none
**Verification:** human — no recipe

**Preconditions:**
- Setup block pasted; `uv` installed.

**Steps:**
1. `pt -v 2>&1 | grep -E 'PASSED|FAILED|passed|failed'`
2. `ls "$CL/scripts/tests" | grep -i prompting`

**Expected Result:**
- Step 1: seven PASSED lines in this order: `test_exists_and_budget`, `test_headings`, `test_parts`, `test_recipes`, `test_no_internal_links`, `test_readme_links_guide`, `test_ships`; then `7 passed`. No FAILED line.
- Step 2: exactly one line, `test_prompting_guide.py`.

**Implementation Reference:** Story 2 — `scripts/tests/test_prompting_guide.py` (a loop rather than `parametrize` keeps the collected count at seven).

**Status:** [ ] Pass  [ ] Fail

**Notes:**

---

### Scenario 7: The guide is in the ship set: both scripts admit it and an install preview lists it

**Source:** Acceptance Criteria (AC-2.3) — Story 2; Business Rule 5 "Ships"; Must Include 4
**Feature:** none
**Verification:** human — no recipe

**Preconditions:**
- Setup block pasted. `$SAMPLE` holds only `.git` and `README.md`.

**Steps:**
1. `shipfn "$CL/scripts/install.sh" prompting-guide.md; shipfn "$CL/scripts/update.sh" prompting-guide.md`
2. `diff <(sed -n '/^is_shippable_writ_doc()/,/^}/p' "$CL/scripts/install.sh") <(sed -n '/^is_shippable_writ_doc()/,/^}/p' "$CL/scripts/update.sh") && echo identical`
3. `dryrun | tee "$W/dryrun.txt" | grep -n 'DRY RUN\|Writ docs:\|prompting-guide\|recommended-delivery'`
4. `ls -A "$SAMPLE"`

**Expected Result:**
- Step 1: `exit 0` twice.
- Step 2: `identical`. The two scripts carry the same denylist; only `recommended-delivery-state-format.md` is excluded.
- Step 3: `🏃 DRY RUN — No changes will be made`, then `Writ docs:`, then `✨ New:       .writ/docs/prompting-guide.md` among the listed docs; no `recommended-delivery` line.
- Step 4: `.git` and `README.md` only. The preview wrote nothing into the sample project, and `$REPO` was never touched.

**Implementation Reference:** `scripts/install.sh` and `scripts/update.sh`, `is_shippable_writ_doc` (read, not modified). DEV-004: `shipfn` sources the function from a here-string, the form `test_ships` ships, because `source <(sed …)` defines nothing on macOS bash 3.2.

**Status:** [ ] Pass  [ ] Fail

**Notes:**

---

### Scenario 8: Breaking a pinned heading, a Route line, the README pointer, or the ship-set function fails the named test

**Source:** Shadow Paths (Empty input, Nil input, Upstream error) — Stories 1 and 2; State Catalog "Guide over 150 lines" and "Guide links a Writ-internal path" (same failure mode); the fail halves of AC-2.2 and AC-2.3
**Feature:** none
**Verification:** human — no recipe

**Preconditions:**
- Setup block pasted; `reset` prints nothing.

**Steps:**
1. Heading: `sed -i '' 's/^## Recipes$/## Recipe/' "$G"; pt -q 2>&1 | grep -E 'AssertionError|Failed:|passed|failed'; reset`
2. Route: `` sed -i '' '/^Route: `\/create-spec`$/d' "$G"; pt -q 2>&1 | grep -E 'AssertionError|passed|failed'; reset ``
3. README: `sed -i '' '/^New here? Read/d' "$CL/README.md"; pt -q 2>&1 | grep -E 'AssertionError|passed|failed'; reset`
4. Function missing, then function rejecting: `shipfn "$CL/README.md" prompting-guide.md; shipfn "$CL/scripts/install.sh" recommended-delivery-state-format.md`

**Expected Result:**
- Step 1: `2 failed, 5 passed`; `AssertionError: H2 headings are ['## What a request carries', '## Recipe', '## Pitfalls'], expected ['## What a request carries', '## Recipes', '## Pitfalls']` from `test_headings`, and `Failed: heading not found: '## Recipes'` from `test_recipes`.
- Step 2: `1 failed, 6 passed`; `AssertionError: '### A feature' has 0 'Route:' lines, expected one` (`test_recipes` names the recipe).
- Step 3: `1 failed, 6 passed`; `AssertionError: README.md section '## Quick Start' does not link .writ/docs/prompting-guide.md`.
- Step 4: `exit 64` (no function in that file; `test_ships` would fail with "fix this test's extraction, not the guide"), then `exit 1` (the denylist rejects its one excluded doc, so Scenario 7's admission is a real decision).
- `reset` prints nothing after each of steps 1 to 3.

**Status:** [ ] Pass  [ ] Fail

**Notes:**

---

### Scenario 9: The repository quality gate reports zero findings

**Source:** Acceptance Criteria (AC-2.5) — Story 2; Success Criteria "`bash scripts/eval.sh` reports 0 findings"
**Feature:** none
**Verification:** human — no recipe

**Preconditions:**
- Setup block pasted; `reset` prints nothing. Run outside any sandbox (the gate does `git init` in a temp dir). About two minutes.

**Steps:**
1. `(cd "$CL" && bash scripts/eval.sh; echo "exit $?")`
2. `tail -2 "$(ls -t "$CL"/.writ/state/eval-*.md | head -1)"`

**Expected Result:**
- Step 1: progress lines, then `Eval report: .writ/state/eval-<timestamp>.md`, then `exit 0`.
- Step 2: `- Findings: 0` and `- Run errors: 0`. In particular no `broken-refs`, `referenced-paths`, `shipped-refs`, or `length` finding names the guide or the README.

**Status:** [ ] Pass  [ ] Fail

**Notes:**

---
