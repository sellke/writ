# UAT Plan: Repro-First Bug Fixing

> **Generated:** 2026-10-29
> **Spec:** `.writ/specs/2026-10-25-repro-first-bug-fixing/`
> **Stories Covered:** 4 of 4 completed
> **Total Scenarios:** 32
> **Merged:** `31cf616` on `phase/15-code-level-rigor`
> **Verification recipe:** none. No `.writ/docs/app-verification.md` exists, and Writ has no app to launch: its checks (pytest, the bash tests, `scripts/eval.sh`) read markdown and run scripts, not a running process. With no launch command detected, Step 1.3's recommended answer is skip, so no recipe was drafted, saved, or bound. Every scenario is `human — no recipe`.

## How to Use This Plan

1. Work through scenarios in order (they're grouped by story, ordered by priority)
2. For each scenario, follow the steps exactly as written
3. Mark Pass or Fail — add notes for any unexpected behavior
4. Scenarios marked Fail should be filed as issues or fed back to the spec
5. A feature passes UAT when all scenarios pass (or failures are accepted as known limitations)

**Conventions for this plan:**

- **Three kinds of scenario.** **Script** scenarios (1 to 6, 8 to 10, 23, 25, 28) run `scripts/repro-order.py` from the clone against small git repositories built in `$W/r`. **Read and check** scenarios (7, 11 to 22, 24, 26, 27) read the shipped files and run the repository's own tests in a scratch clone. **Live** scenarios (29 to 32) run `/prototype` or `/implement-story` in a Claude Code session inside a second clone and are judged by eye.
- **Where each scenario runs.** Script and read-and-check scenarios run in `$CL`, a clone pinned at `31cf616`, the tree as merged. Live scenarios run in `$FX`, a second clone at `31cf616` plus one fixture commit (tag `uat-fixture`, branch `uat-live`). The fixture adds a `uatfx/slug.py` CLI whose `main` drops `+` before calling `slugify`, so `python3 -m uatfx.slug "C++ tips"` prints `c-tips` while the unit test of `slugify` passes; a bug issue for it under `.writ/issues/bugs/`; a one-story fixture spec whose `Origin` cites that issue; and a `- **Gate 0 Divergence:** off` line so `/implement-story` reaches Gate 1 sooner. **Never run `install.sh` or `update.sh` in the Writ repo.** `.claude/` and `.cursor/` there are symlinks into the source; the clones keep them, so `/prototype` and `/implement-story` are project commands inside `$FX` with nothing installed.
- **Worktree base for live runs.** `adapters/claude-code.md` § Git Worktree Isolation: an isolated subagent's worktree branches from the repository's default branch unless `worktree.baseRef` is `"head"`. The fixture commit lives only on the local branch `uat-live`, so the setup writes `{"worktree": {"baseRef": "head"}}` to `$FX/.claude/settings.local.json`. Without it the coding agent's worktree may not contain `uatfx/`.
- Every helper refuses to run unless the shell is inside `$W`. `$REPO` is cloned from and never written to. Run the plan in `bash` on macOS (`sed -i ''`), outside any sandbox, with `claude`, `uv`, and `python3` on `PATH`. Do not run it as root (Scenario 8 relies on a permission error). Claude Code asks whether to trust each new scratch folder the first time a session opens there; accept it.
- **Script fixtures.** `fx <name>` builds a fresh repository at `$W/r/<name>` with `src/app.py` and `tests/test_app.py` in one commit tagged `base`; rebuilding a name discards the earlier one. SHAs differ on every run. In expected results, `<R>` is a repro commit, `<F>` a fix commit, and `<M>` any other commit; each stands for the 7-character SHA that `hist <name>` prints for it, and numbered forms (`<R1>`, `<F2>`) follow `hist` order.
- **Live scenarios.** Start `live` from a second shell: set `UAT_W=<the path the first shell printed>`, then paste the setup block, which reuses that folder and both clones. Start a new session for each run (`/exit`, then `live` again). The coding agent commits, so approve the git and test commands it asks to run. To read the coding agent's report, expand its entry in the transcript (ctrl+o). An `/implement-story` run takes several minutes; let every gate run. Run `fxreset` after each live scenario; it also removes agent worktrees a run left behind.
- Expected results come from the spec, the technical spec, the four What Was Built records, the drift log, and the tree at `31cf616`. Story 1 landed in `35a211b`, Story 2 in `c687fab`, Story 3 in `320bbf6`, Story 4 in `cbf054a`. None of these scenarios has been run for this plan. After each scenario that edits `$CL`, run `reset` and confirm it prints nothing. When done: `rm -rf "$W"`.
- **Drift.** All thirteen entries are Small and auto-amended; this plan expects what was built. DEV-001 (Scenario 4), DEV-002 (2, 9), DEV-003 (2), DEV-004 (8, 10), DEV-005 (14), DEV-006 (3, 12, 13), DEV-007 (13, 26), DEV-008 (3, 16, 32), DEV-009 (17), DEV-010 (27), DEV-011 (27), DEV-012 (21, 25, 29), DEV-013 (22, 23, 32).
- **Known risks in Scenario 32.** (a) Step 4 item 8 of `commands/implement-story.md`, byte-identical by design, names the `gate3-route:`, `review-panel:`, and `arch-lint:` lines but not `repro-order:`. Only the Gate 1 Bug path line says to print it. A Step 4 report without a `repro-order:` line is a Fail against AC-4.2. (b) The `/implement-story` Bug path line does not say how to integrate; it relies on the integration skill's Ordered commits paragraph, which follows two steps that copy files, and `adapters/claude-code.md` still describes integration as "copy the changed files". A copy drops the commits, the check prints `fail` / `no_repro_commit`, and the story is falsely `⚠️ DEGRADED`. `/prototype` got an explicit cherry-pick in DEV-012; `/implement-story` did not.

**Setup.** Paste this block once in the first shell. Stop if the first line does not print `W=/...`.

```bash
# First shell: paste as is. Second shell: run UAT_W=<the W path the first shell printed>, then paste.
W=${UAT_W:-$(mktemp -d "${TMPDIR:-/tmp}/writ-uat-repro.XXXXXX")} && cd "$W" && W=$PWD && echo "W=$W"
REPO=/Users/asellke/Projects/writ            # read only: cloned from, never edited, never installed into
CL="$W/clone"; [ -d "$CL/.git" ] || { git clone -q "$REPO" "$CL" && git -C "$CL" checkout -q 31cf616; }
FX="$W/fx"                                   # second clone: 31cf616 plus the live fixture
FS=.writ/specs/2026-10-29-uat-slug-plus      # the fixture spec inside $FX
BUG=.writ/issues/bugs/2026-10-29-slug-cli-drops-plus.md   # the fixture bug issue inside $FX
RO="$CL/scripts/repro-order.py"
PY=$(python3 -c 'import sys; print(sys.executable)')   # absolute interpreter path, so it runs with an empty PATH
mkdir -p "$W/r" "$W/nobin"                   # $W/r holds the script fixtures; $W/nobin is an empty PATH
inW() { case "$PWD/" in "$W"/*) ;; *) echo "refusing: $PWD is outside $W" >&2; return 1;; esac; }
# pt <pytest args>: pytest on Python 3.9 inside $CL
pt() { inW && (cd "$CL" && uv run --python 3.9 pytest "$@"); }
# reset: undo every edit in $CL and drop untracked files; prints nothing when clean
reset() { inW && git -C "$CL" checkout -q -- . && git -C "$CL" clean -qfd && git -C "$CL" status --short; }
# rc <command...>: run it; print its exit code and stdout size, then its stderr
rc() { inW || return 1; "$@" > "$W/out.txt" 2> "$W/err.txt"; local s=$?; echo "exit $s stdout-bytes $(wc -c < "$W/out.txt" | tr -d ' ')"; cat "$W/err.txt"; }

# --- script fixtures (Stories 1 and 4) ---
# fx <name>: a new repo $W/r/<name> on main: src/app.py and a skipped tests/test_app.py in one commit, tagged base
fx() { inW || return 1; local d="$W/r/$1"; rm -rf "$d" && mkdir -p "$d/src" "$d/tests" && git -C "$d" init -q -b main || return 1
  git -C "$d" config user.name uat && git -C "$d" config user.email uat@example.invalid
  git -C "$d" config commit.gpgsign false && git -C "$d" config core.hooksPath /dev/null
  printf 'def add(a, b):\n    return a - b\n' > "$d/src/app.py"
  printf 'import pytest\n\n\n@pytest.mark.skip(reason="add returns a difference")\ndef test_add():\n    from src.app import add\n    assert add(2, 3) == 5\n' > "$d/tests/test_app.py"
  git -C "$d" add -A && git -C "$d" commit -qm "chore: base" && git -C "$d" tag base; }
# ci <name> <message> <path>...: append one line to each path (creating it), then commit everything with <message>
ci() { inW || return 1; local d="$W/r/$1" m=$2 p; shift 2
  for p in "$@"; do mkdir -p "$(dirname "$d/$p")" && printf '# edit\n' >> "$d/$p"; done
  git -C "$d" add -A && git -C "$d" commit -qm "$m"; }
# roc <name> [flags]: repro-order.py check on $W/r/<name> from tag base to HEAD, then its exit code
roc() { inW || return 1; python3 "$RO" check --repo "$W/r/$1" --base base "${@:2}"; echo "exit $?"; }
# hist <name>: the fixture's commits after base, oldest first, with the 7-character SHAs the check prints
hist() { git -C "$W/r/$1" log --reverse --abbrev=7 --format='%h %s' base..HEAD; }
# cfg <name> [line]: write $W/r/<name>/.writ/config.md with <line> under ## Conventions; no line removes the file
cfg() { inW || return 1; local d="$W/r/$1"; if [ $# -lt 2 ]; then rm -f "$d/.writ/config.md"; return 0; fi
  mkdir -p "$d/.writ" && printf '# Writ Project Config\n\n## Conventions\n\n- **Default Branch:** main\n%s\n' "$2" > "$d/.writ/config.md"; }
RM=$'test: reproduce add(2, 3) returning -1\n\nRepro: add(2, 3) returns -1, not 5'   # a repro message: trailer in the last paragraph
FM='fix: add returns the sum'

# --- live fixture (Story 4, end to end) ---
if [ ! -d "$FX/.git" ]; then
  git clone -q "$REPO" "$FX" && git -C "$FX" checkout -q -b uat-live 31cf616
  git -C "$FX" config user.name uat && git -C "$FX" config user.email uat@example.invalid && git -C "$FX" config commit.gpgsign false
  printf '.claude/worktrees/\n' >> "$FX/.git/info/exclude"
  mkdir -p "$FX/uatfx/tests" "$FX/$FS/user-stories" "$(dirname "$FX/$BUG")"
  touch "$FX/uatfx/__init__.py" "$FX/uatfx/tests/__init__.py"
  cat > "$FX/uatfx/slug.py" <<'EOF'
"""Make URL slugs from titles. Run from the repository root: python3 -m uatfx.slug <title words>"""
import re
import sys


def slugify(title):
    """Lowercase the title and join its words with '-'. Letters, digits, and '+' are kept."""
    return "-".join(re.findall(r"[a-z0-9+]+", title.lower()))


def main(argv):
    title = re.sub(r"[^\w\s-]", "", " ".join(argv))
    print(slugify(title))
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
EOF
  cat > "$FX/uatfx/tests/test_slug.py" <<'EOF'
from uatfx.slug import slugify


def test_slugify_joins_words():
    assert slugify("Hello World") == "hello-world"


def test_slugify_keeps_plus():
    assert slugify("C++ tips") == "c++-tips"
EOF
  cat > "$FX/$BUG" <<'EOF'
# The slug CLI drops '+' from titles

> **Type:** Bug
> **Priority:** Normal
> **Effort:** Small
> **Created:** 2026-10-29

## TL;DR

`python3 -m uatfx.slug "C++ tips"` prints `c-tips`. It should print `c++-tips`, as `slugify` documents.

## Current State

- Run from the repository root, `python3 -m uatfx.slug "C++ tips"` prints `c-tips`.
- `slugify("C++ tips")` called directly returns `c++-tips`, and its unit test passes.

## Expected Outcome

- The CLI prints `c++-tips` for `C++ tips`.

## Relevant Files

- `uatfx/slug.py`
- `uatfx/tests/test_slug.py`
EOF
  cat > "$FX/$FS/spec.md" <<'EOF'
# UAT Slug Plus Fixture

> **Status:** In Progress
> **Created:** 2026-10-29
> **Origin:** Promoted from issue: .writ/issues/bugs/2026-10-29-slug-cli-drops-plus.md

## Specification Contract

**Deliverable:** The slug CLI keeps '+' in a title, as `slugify` does. A UAT fixture for the repro-first spec; it is never merged.
EOF
  cat > "$FX/$FS/spec-lite.md" <<'EOF'
# UAT Slug Plus Fixture (Lite)

## For Coding Agents

**Deliverable:** `python3 -m uatfx.slug "C++ tips"` prints `c++-tips`. Change only `uatfx/slug.py` and `uatfx/tests/test_slug.py`.

## For Review Agents

**Acceptance:** the story's criteria, and no change outside the two files the story names.

## For Testing Agents

**Tests:** `uv run --python 3.9 pytest uatfx/tests -v`
EOF
  cat > "$FX/$FS/user-stories/story-1-cli-keeps-plus.md" <<'EOF'
# Story 1: The Slug CLI Keeps '+'

> **Status:** Not Started
> **Priority:** High
> **Dependencies:** None

## User Story

**As a** user of the slug CLI
**I want to** get `c++-tips` for the title `C++ tips`
**So that** the CLI prints the slug `slugify` documents

## Acceptance Criteria

- [ ] Given the title `C++ tips`, when `python3 -m uatfx.slug "C++ tips"` runs from the repository root, then it prints `c++-tips` `[AC-1.1]`
- [ ] Given the title `Hello World`, when the CLI runs, then it still prints `hello-world` `[AC-1.2]`

## Implementation Tasks

- [ ] 1.1 Add a failing test to `uatfx/tests/test_slug.py` `[AC-1.1, AC-1.2]`
- [ ] 1.2 Fix `uatfx/slug.py` `[AC-1.1, AC-1.2]`

## Notes

- Change only `uatfx/slug.py` and `uatfx/tests/test_slug.py`.
- Run the story's tests with `uv run --python 3.9 pytest uatfx/tests/test_slug.py -v`.
EOF
  python3 -c 'import sys; p = sys.argv[1]; t = open(p).read(); open(p, "w").write(t.replace("## Conventions\n\n", "## Conventions\n\n- **Gate 0 Divergence:** off\n", 1))' "$FX/.writ/config.md"
  printf '{\n  "worktree": {\n    "baseRef": "head"\n  }\n}\n' > "$FX/.claude/settings.local.json"
  git -C "$FX" add -A && git -C "$FX" commit -qm "uat: repro-first live fixture" && git -C "$FX" tag uat-fixture
fi
# live: Claude Code inside $FX
live() { inW && (cd "$FX" && claude); }
# fxreset: drop agent worktrees a run left behind and put $FX back on the fixture commit; prints nothing when clean
fxreset() { inW || return 1; local p; git -C "$FX" cherry-pick --abort > /dev/null 2>&1
  git -C "$FX" worktree list --porcelain | sed -n 's/^worktree //p' | tail -n +2 | while read -r p; do git -C "$FX" worktree remove --force "$p"; done
  git -C "$FX" reset -q --hard && git -C "$FX" checkout -q -B uat-live uat-fixture && git -C "$FX" clean -qfd && git -C "$FX" status --short; }
# fxoff: commit "- **Repro First:** off" under ## Conventions in $FX, tagged uat-off
fxoff() { inW && python3 -c 'import sys; p = sys.argv[1]; t = open(p).read(); open(p, "w").write(t.replace("## Conventions\n\n", "## Conventions\n\n- **Repro First:** off\n", 1))' "$FX/.writ/config.md" \
  && git -C "$FX" commit -qam "uat: Repro First off" && git -C "$FX" tag -f uat-off > /dev/null 2>&1 && grep -n 'Repro First' "$FX/.writ/config.md"; }
# fxlog <rev>: each commit after <rev> in $FX, oldest first: SHA and subject, its files, and its message's last paragraph
fxlog() { local c; for c in $(git -C "$FX" rev-list --reverse "$1"..HEAD); do git -C "$FX" log -1 --abbrev=7 --format='== %h %s' "$c"
  git -C "$FX" show --name-only --format= "$c" | sed 's/^/   file: /'
  git -C "$FX" log -1 --format=%B "$c" | awk 'BEGIN { RS = "" } END { print }' | sed 's/^/   last: /'; done; }
echo "setup done: clone at $(git -C "$CL" rev-parse HEAD | cut -c1-7), fixture $(git -C "$FX" log -1 --format=%s uat-fixture)"
```

The last line should read `setup done: clone at 31cf616, fixture uat: repro-first live fixture`.

## Coverage Summary

| Story | Status | Scenarios | Source Breakdown |
|-------|--------|-----------|-----------------|
| Story 1: Repro-Order Check Script | ✅ Covered | 10 | AC: 7, Errors: 1, Shadow: 0, Edge: 2, Experience: 0 |
| Story 2: The tdd-cycle Bug Path | ✅ Covered | 5 | AC: 5, Errors: 0, Shadow: 0, Edge: 0, Experience: 0 |
| Story 3: The Coding Agent's Repro Report | ✅ Covered | 5 | AC: 5, Errors: 0, Shadow: 0, Edge: 0, Experience: 0 |
| Story 4: Consumer Wiring and Ordered-Commit Integration | ✅ Covered | 12 | AC: 7, Errors: 1, Shadow: 0, Edge: 0, Experience: 4 |

- **Switch states.** `Repro First` is covered in each state:

  | Where | Absent | `on` | `off` | Malformed |
  |---|---|---|---|---|
  | `repro-order.py check` | 1, 4 | 4 | 4, 5 | 4 (`yes`, `off # trial run`, an indented line) |
  | `/prototype` end to end | 29, 31 | — | 30 | — |
  | `/implement-story` end to end | 32 | — | — | — |
  | Shipped text | — | — | 11, 14, 18, 21, 22 | 14 |

  No end-to-end run uses `on` or a malformed value: the script reads both as on (Scenario 4), and the skill and the agent act only on the exact `- **Repro First:** off` line.
- Folded rows. Error Map: "Read `.writ/config.md`" absent is Scenario 4 (Step 1), unreadable is 8; "Resolve `--base` / `--head`", "Ancestry", and "Run git" are 6; "Range shape" is 5; "Integration" (cherry-pick conflict) is 28. Shadow Paths: happy path 1 and 25 (orchestrator re-run 25, 29, 32); nil input 6 (Step 1); empty input 6 (Step 6); upstream error 6 (Steps 4 and 5). Interaction Edge Cases: two repros, un-skipped test, fix adding tests, renamed repro test, `.writ/`-only commit, and paths with spaces or non-ASCII are 9; tests outside known patterns is 10; switch value `yes` is 4.
- Experience Design: entry point 29 (`/prototype --no-diverge @<bug issue>`) and 32 (`/implement-story` on a story whose spec came from a bug issue); happy path, moment of truth, and feedback model 29 (Step 5 summary) and 32 (Step 4 report). State Catalog: not a bug fix 31; bug with a repro on the bug's surface 29; switch off 4, 5, 30; check fails after integration 28 (script) and 21, 22 (text); merge commit in range 5; cherry-pick conflict 28.
- No live scenario for "harness cannot reach the surface", "no repro possible", "check fails in the agent", the Error Map's "Agent self-check" row, or a story marked `⚠️ DEGRADED`: no fixture produces them reliably. Scenarios 17 and 18 check the `gap:` field and the `Repro: none` form, 12 checks "Fix every `fail` reason before handing off", and 22 and 28 check the DEGRADED mapping and the `fail` that triggers it.
- The front door's route for a bug (`/writ` → `/prototype --no-diverge`) predates this spec and is not exercised here.
- **Gaps the drift log does not record.** (1) Every drift entry reads "Auto-amended" with a technical-spec amendment, but `sub-specs/technical-spec.md` was never edited after `1fe981b`: it still gives the `(\S+)` switch regex, the old Check Rule 6 wording, the draft Report Block, and the draft Consumer Lines. This plan follows the drift log and the shipped files. (2) The switch reaches a worktree-isolated coding agent only when committed, because the agent's worktree starts from a commit. `.writ/docs/config-format.md` does not say so. Scenario 30 commits the line.
- No pending stories: all four are Completed ✅.

---

## Story 1: Repro-Order Check Script

### Scenario 1: A repro commit followed by a fix commit passes, with one line per commit

**Source:** Acceptance Criteria (AC-1.1) — Story 1; Shadow Path "Happy path"; Business Rules 4 and 5
**Feature:** none
**Verification:** human — no recipe

**Preconditions:**
- Setup block pasted.

**Steps:**
1. `fx pass && ci pass "$RM" tests/test_app.py && ci pass "$FM" src/app.py && hist pass`
2. `roc pass`

**Expected Result:**
- Step 1: two lines, `<R> test: reproduce add(2, 3) returning -1`, then `<F> fix: add returns the sum`.
- Step 2: exactly these lines, with Step 1's SHAs:
  ```text
  pass
  reason: repro <R> test: reproduce add(2, 3) returning -1 (1 test file)
  reason: fix <F> fix: add returns the sum (1 source file)
  repro-order: pass (1 repro, 1 fix commit(s))
  exit 0
  ```

**Implementation Reference:** Story 1 — Files: `scripts/repro-order.py` (`check`, `apply_rules`), `scripts/tests/test_repro_order.py` (`test_pass_repro_then_fix`)

**Status:** [ ] Pass  [ ] Fail

**Notes:**

---

### Scenario 2: Each of the six broken histories fails with its own reason code

**Source:** Acceptance Criteria (AC-1.2) — Story 1; Check Rules 1 to 6; DEV-002, DEV-003
**Feature:** none
**Verification:** human — no recipe

**Preconditions:**
- Setup block pasted.

**Steps:**
1. No repro commit: `fx nr && ci nr "$FM" src/app.py && roc nr`
2. A repro that also changes source: `fx rs && ci rs "$RM" tests/test_app.py src/app.py && ci rs "$FM" src/app.py && hist rs && roc rs`
3. A repro with no test file: `fx re && ci re "$RM" .writ/notes.md && ci re "$FM" src/app.py && hist re && roc re`
4. Source changed before the repro: `fx sb && ci sb "$FM" src/app.py && ci sb "$RM" tests/test_app.py && ci sb 'fix: add handles floats' src/app.py && hist sb && roc sb`
5. No fix after the repro: `fx nf && ci nf "$RM" tests/test_app.py && hist nf && roc nf`
6. A later commit edits a file the repro added: `fx tm && ci tm "$RM" tests/test_add_bug.py && ci tm 'fix: add returns the sum; loosen the new test' src/app.py tests/test_add_bug.py && hist tm && roc tm`
7. `pt scripts/tests/test_repro_order.py -q -k "test_fail_" 2>&1 | tail -1`

**Expected Result:**
- Step 1: `fail`, `reason: no_repro_commit`, `repro-order: fail (0 repro, 0 fix commit(s), 1 finding(s))`, `exit 1`.
- Step 2: `fail`, `reason: repro_touches_source <R> src/app.py`, `repro-order: fail (1 repro, 1 fix commit(s), 1 finding(s))`, `exit 1`.
- Step 3: `fail`, `reason: repro_empty <R>`, `repro-order: fail (1 repro, 1 fix commit(s), 1 finding(s))`, `exit 1`. The `.writ/` path counts as neither test nor source.
- Step 4: `fail`, `reason: source_before_repro <F1> src/app.py`, `repro-order: fail (1 repro, 1 fix commit(s), 1 finding(s))`, `exit 1`. `<F1>` is the first commit in `hist`, the one that broke the rule, not the repro (DEV-003).
- Step 5: `fail`, `reason: no_fix_after_repro <R>`, `repro-order: fail (1 repro, 0 fix commit(s), 1 finding(s))`, `exit 1`.
- Step 6: `fail`, `reason: repro_test_modified <F> tests/test_add_bug.py`, `repro-order: fail (1 repro, 1 fix commit(s), 1 finding(s))`, `exit 1`. The SHA is the fix commit (DEV-003).
- Step 7: `10 passed, 26 deselected`.

**Implementation Reference:** Story 1 — Files: `scripts/repro-order.py` (`apply_rules`); WWB decisions 2 and 3

**Status:** [ ] Pass  [ ] Fail

**Notes:**

---

### Scenario 3: Only a `Repro:` line in the message's last paragraph marks a repro commit

**Source:** Acceptance Criteria (AC-1.1, AC-1.2) — Story 1; Business Rule 4 (Repro commit); DEV-006, DEV-008; WWB decision 4 (Trailer placement)
**Feature:** none
**Verification:** human — no recipe

**Preconditions:**
- Setup block pasted.

**Steps:**
1. Trailers in one block: `fx t1 && ci t1 $'test: reproduce add(2, 3) returning -1\n\nRepro: add(2, 3) returns -1\nRef: .writ/specs/demo/user-stories/story-1-demo.md\nCo-Authored-By: UAT <uat@example.invalid>' tests/test_app.py && ci t1 "$FM" src/app.py && roc t1 | sed -n '1p;$p'`
2. `Repro:` in its own paragraph before a trailer paragraph: `fx t2 && ci t2 $'test: reproduce add(2, 3) returning -1\n\nRepro: add(2, 3) returns -1\n\nCo-Authored-By: UAT <uat@example.invalid>' tests/test_app.py && ci t2 "$FM" src/app.py && roc t2`
3. `Repro:` on the subject line: `fx t3 && ci t3 'test: reproduce add(2, 3) returning -1 Repro: add(2, 3) returns -1' tests/test_app.py && ci t3 "$FM" src/app.py && roc t3 | sed -n '1,2p;$p'`
4. The skill example's layout, `Repro:` directly under the subject: `fx t4 && ci t4 $'test: reproduce add(2, 3) returning -1\nRepro: add(2, 3) returns -1' tests/test_app.py && ci t4 "$FM" src/app.py && roc t4 | sed -n '1p;$p'`
5. `pt scripts/tests/test_repro_order.py -q -k trailer 2>&1 | tail -1`

**Expected Result:**
- Step 1: `pass`, `exit 0`. `Repro:` shares the last paragraph with `Ref:` and `Co-Authored-By:`, the layout `agents/coding-agent.md` Requirement 3 asks of story commits.
- Step 2: `fail`, `reason: no_repro_commit`, `repro-order: fail (0 repro, 0 fix commit(s), 1 finding(s))`, `exit 1`. A `Repro:` paragraph followed by another trailer paragraph is not read.
- Step 3: `fail`, `reason: no_repro_commit`, `exit 1`.
- Step 4: `pass`, `exit 0`. A subject and a `Repro:` line with no blank line between them form one paragraph, so the line is read.
- Step 5: `3 passed, 33 deselected`.

**Implementation Reference:** Story 1 — Files: `scripts/repro-order.py` (`is_repro`), `scripts/tests/test_repro_order.py` (`test_combined_trailer_block`, `test_repro_paragraph_before_separate_trailer_paragraph`)

**Status:** [ ] Pass  [ ] Fail

**Notes:**

---

### Scenario 4: The `Repro First` switch: absent, `on`, `off`, and malformed values

**Source:** Acceptance Criteria (AC-1.3) — Story 1; Business Rule 9 (The switch); Error Map "Read `.writ/config.md`" (absent); Interaction Edge Case "Switch value `yes`"; DEV-001
**Feature:** none
**Verification:** human — no recipe

**Preconditions:**
- Setup block pasted.
- `fx sw && ci sw "$RM" tests/test_app.py && ci sw "$FM" src/app.py && hist sw` prints two lines.

**Steps:**
1. Absent: `cfg sw; roc sw`
2. `on`: `cfg sw '- **Repro First:** on'; roc sw`
3. `off`: `cfg sw '- **Repro First:** off'; roc sw; cfg sw '- **Repro First:** OFF'; roc sw | sed -n '1p;$p'`
4. Malformed: `cfg sw '- **Repro First:** yes'; roc sw`
5. Near misses: `cfg sw '- **Repro First:** off # trial run'; roc sw | head -2; cfg sw '  - **Repro First:** off'; roc sw | head -2`
6. `cfg sw; pt scripts/tests/test_repro_order.py -q -k switch 2>&1 | tail -1`

**Expected Result:**
- Step 1: `pass`, `reason: repro <R> test: reproduce add(2, 3) returning -1 (1 test file)`, `reason: fix <F> fix: add returns the sum (1 source file)`, `repro-order: pass (1 repro, 1 fix commit(s))`, `exit 0`.
- Step 2: the same five lines as Step 1, with no `repro-first` reason line.
- Step 3: exactly `unverifiable`, `reason: repro-first off`, `repro-order: unverifiable (0 repro, 0 fix commit(s))`, `exit 0`. With `OFF`: `unverifiable` and `exit 0`.
- Step 4: `pass`, then `reason: repro-first value yes read as on` as the first reason line, then the repro and fix lines, the pass summary, and `exit 0`.
- Step 5 (DEV-001): `off # trial run` prints `pass`, then `reason: repro-first value off # trial run read as on`; only the bare value `off` turns the path off. The indented line prints `pass`, then `reason: repro <R> …`: a line that does not start with `- **Repro First:**` is not read, so the switch is absent.
- Step 6: `4 passed, 32 deselected`.

**Implementation Reference:** Story 1 — Files: `scripts/repro-order.py` (`SWITCH_LINE`, `switch_value`); WWB decision 1

**Status:** [ ] Pass  [ ] Fail

**Notes:**

---

### Scenario 5: With the switch off the check returns before any git call; a merge in range is unverifiable

**Source:** Acceptance Criteria (AC-1.3) — Story 1; Error Map "Range shape"; State Catalog "Switch off" and "Merge commit in the range"
**Feature:** none
**Verification:** human — no recipe

**Preconditions:**
- Setup block pasted.
- `mkdir -p "$W/nr/.writ"; git -C "$W/nr" rev-parse --git-dir` reports that `$W/nr` is not a git repository.

**Steps:**
1. `printf -- '- **Repro First:** off\n' > "$W/nr/.writ/config.md"; (cd "$W/nr" && env PATH="$W/nobin" "$PY" "$RO" check --base no-such-rev; echo "exit $?")`
2. `rm "$W/nr/.writ/config.md"; (cd "$W/nr" && env PATH="$W/nobin" "$PY" "$RO" check --base no-such-rev; echo "exit $?")`
3. `fx mg && git -C "$W/r/mg" checkout -qb side && ci mg "$RM" tests/test_app.py && git -C "$W/r/mg" checkout -q main && ci mg "$FM" src/app.py && git -C "$W/r/mg" merge -q --no-ff --no-edit side && git -C "$W/r/mg" log --oneline --merges base..HEAD | wc -l`
4. `roc mg`
5. `pt scripts/tests/test_repro_order.py -q -k "switch_off or merge" 2>&1 | tail -1`

**Expected Result:**
- Step 1: `unverifiable`, `reason: repro-first off`, `repro-order: unverifiable (0 repro, 0 fix commit(s))`, `exit 0`. The folder is not a repository, `git` is not on `PATH`, and the revision does not exist, so the switch was read before any git call.
- Step 2: `repro-order: git not found` and `exit 2`. Without the switch line, the same command needs git.
- Step 3: `1` (one merge commit in the range; `wc` may pad it with spaces).
- Step 4: `unverifiable`, `reason: merge_in_range`, `repro-order: unverifiable (0 repro, 0 fix commit(s))`, `exit 0`.
- Step 5: `3 passed, 33 deselected`.

**Implementation Reference:** Story 1 — Files: `scripts/repro-order.py` (`check`: switch first, then `rev-list --merges`)

**Status:** [ ] Pass  [ ] Fail

**Notes:**

---

### Scenario 6: Usage errors exit 2 with empty stdout; an empty range is a `fail`

**Source:** Acceptance Criteria (AC-1.4) — Story 1; Error Map "Resolve `--base` / `--head`", "Ancestry", "Run git"; Shadow Paths "Nil input", "Empty input", "Upstream error"
**Feature:** none
**Verification:** human — no recipe

**Preconditions:**
- Setup block pasted.
- `fx us && ci us "$RM" tests/test_app.py && ci us "$FM" src/app.py`
- `mkdir -p "$W/nr" && rm -f "$W/nr/.writ/config.md"`

**Steps:**
1. `rc python3 "$RO" check --repo "$W/r/us"`
2. `rc python3 "$RO" check --repo "$W/r/us" --base no-such-rev`
3. `rc python3 "$RO" check --repo "$W/r/us" --base HEAD --head base`
4. `rc python3 "$RO" check --repo "$W/nr" --base HEAD`
5. `rc env PATH="$W/nobin" "$PY" "$RO" check --repo "$W/r/us" --base base`
6. `python3 "$RO" check --repo "$W/r/us" --base HEAD; echo "exit $?"`
7. `pt scripts/tests/test_repro_order.py -q -k "usage_errors or git_not_found or base_equals_head or help" 2>&1 | tail -1`

**Expected Result:**
- Step 1: `exit 2 stdout-bytes 0`, then a `usage: repro-order.py check` line and `repro-order.py check: error: the following arguments are required: --base`.
- Step 2: `exit 2 stdout-bytes 0`, then `repro-order: cannot resolve no-such-rev`.
- Step 3: `exit 2 stdout-bytes 0`, then `repro-order: HEAD is not an ancestor of base`.
- Step 4: `exit 2 stdout-bytes 0`, then `repro-order: not a git repository`.
- Step 5: `exit 2 stdout-bytes 0`, then `repro-order: git not found`.
- Step 6: `fail`, `reason: no_repro_commit`, `repro-order: fail (0 repro, 0 fix commit(s), 1 finding(s))`, `exit 1`. Base equal to head is a verdict, not a usage error.
- Step 7: `4 passed, 32 deselected`.

**Implementation Reference:** Story 1 — Files: `scripts/repro-order.py` (`_git`, `_resolve`, `main`)

**Status:** [ ] Pass  [ ] Fail

**Notes:**

---

### Scenario 7: The CLI contract lists the script, and its test module passes

**Source:** Acceptance Criteria (AC-1.5) — Story 1
**Feature:** none
**Verification:** human — no recipe

**Preconditions:**
- Setup block pasted; `reset` prints nothing.

**Steps:**
1. ``grep -n '^| `repro-order.py`' "$CL/.writ/docs/agent-cli-contract.md"; grep -n '^- `repro-order.py`' "$CL/.writ/docs/agent-cli-contract.md" | cut -c1-110``
2. `grep -n 'Smoke("repro-order.py"' "$CL/scripts/tests/test_agent_cli_contract.py"`
3. `pt scripts/tests/test_agent_cli_contract.py -q 2>&1 | tail -1`
4. `pt scripts/tests/test_repro_order.py -q 2>&1 | tail -1`
5. `cmp "$CL/scripts/repro-order.py" "$CL/plugins/writ/scripts/repro-order.py" && echo same`

**Expected Result:**
- Step 1: the Classification row ``| `repro-order.py` | check |  | commands/implement-story.md, commands/prototype.md, skills/tdd-cycle/SKILL.md |``, and a Notes bullet that begins ``- `repro-order.py` — check. On `pass` the `reason:` lines are informational``.
- Step 2: `Smoke("repro-order.py", ["check", "--repo", "{repo}", "--base", "HEAD"], {}),`
- Step 3: no `failed`.
- Step 4: `36 passed`.
- Step 5: `same` (the plugin tree ships the script).

**Implementation Reference:** Story 1 — Files: `.writ/docs/agent-cli-contract.md`, `scripts/tests/test_agent_cli_contract.py`, `plugins/writ/scripts/repro-order.py` (generated)

**Status:** [ ] Pass  [ ] Fail

**Notes:**

---

### Scenario 8: An unreadable config or an unsearchable `.writ/` exits 2 without a traceback

**Source:** Error Map "Read `.writ/config.md`" (unreadable or not UTF-8) — Story 1; DEV-004
**Feature:** none
**Verification:** human — no recipe

**Preconditions:**
- Setup block pasted; not running as root.
- `fx bad`

**Steps:**
1. `mkdir -p "$W/r/bad/.writ" && printf '\377\376- **Repro First:** off\n' > "$W/r/bad/.writ/config.md"; rc python3 "$RO" check --repo "$W/r/bad" --base base`
2. `rm "$W/r/bad/.writ/config.md"; chmod 000 "$W/r/bad/.writ"; rc python3 "$RO" check --repo "$W/r/bad" --base base; chmod 755 "$W/r/bad/.writ"`
3. `grep -c Traceback "$W/err.txt"`
4. `pt scripts/tests/test_repro_order.py -q -k "unreadable_config or unsearchable" 2>&1 | tail -1`

**Expected Result:**
- Step 1: `exit 2 stdout-bytes 0`, then `repro-order: cannot read .writ/config.md ('utf-8' codec can't decode byte 0xff in position 0: invalid start byte)`. The `off` after the bad bytes is not read.
- Step 2: `exit 2 stdout-bytes 0`, then `repro-order: cannot read .writ/config.md ([Errno 13] Permission denied: '…/bad/.writ/config.md')`.
- Step 3: `0`.
- Step 4: `2 passed, 34 deselected`.

**Implementation Reference:** Story 1 — Files: `scripts/repro-order.py` (`switch_value`: one `OSError` / `UnicodeDecodeError` handler for the existence check and the read)

**Status:** [ ] Pass  [ ] Fail

**Notes:**

---

### Scenario 9: Un-skipped tests, extra tests in a fix, two repros, odd paths, and `.writ/` commits pass; renaming a repro test fails

**Source:** Interaction Edge Cases "Two bugs, two repro commits", "Repro un-skips an existing test", "Fix commit also adds new tests", "Completion commit touches only `.writ/`", "Paths with spaces or non-ASCII", "Repro test renamed after the fix" — Story 1; DEV-002
**Feature:** none
**Verification:** human — no recipe

**Preconditions:**
- Setup block pasted.

**Steps:**
1. Repro 1 un-skips the existing test: `fx ec && sed -i '' '/mark.skip/d' "$W/r/ec/tests/test_app.py" && git -C "$W/r/ec" commit -qam "$RM"`
2. Fix 1 also adds a test: `ci ec "$FM" src/app.py tests/test_add_more.py`
3. Repro 2 adds a test at a path with spaces and non-ASCII and touches repro 1's file; fix 2 follows: `ci ec $'test: reproduce a dropped plus sign\n\nRepro: a plus sign is dropped' "tests/plus cases/test_naïve plus.py" tests/test_app.py && ci ec 'fix: keep the plus sign' src/app.py`
4. A completion commit that touches only `.writ/`: `ci ec 'docs(writ): mark story 1 complete' .writ/specs/demo/user-stories/story-1-demo.md && hist ec && roc ec`
5. Rename repro 2's test: `git -C "$W/r/ec" mv "tests/plus cases/test_naïve plus.py" tests/test_plus.py && git -C "$W/r/ec" commit -qm "refactor: rename the plus-sign test" && roc ec`
6. `pt scripts/tests/test_repro_order.py -q -k "unskips or new_tests or writ_only or spaces or two_repros or renamed or deleted" 2>&1 | tail -1`

**Expected Result:**
- Step 4: `hist` lists five commits. The check prints:
  ```text
  pass
  reason: repro <R1> test: reproduce add(2, 3) returning -1 (1 test file)
  reason: fix <F1> fix: add returns the sum (1 source file)
  reason: repro <R2> test: reproduce a dropped plus sign (2 test files)
  reason: fix <F2> fix: keep the plus sign (1 source file)
  repro-order: pass (2 repro, 2 fix commit(s))
  exit 0
  ```
  The `.writ/`-only commit is neither a repro nor a fix and gets no line.
- Step 5:
  ```text
  fail
  reason: repro_test_modified <M> tests/plus cases/test_naïve plus.py
  repro-order: fail (2 repro, 2 fix commit(s), 1 finding(s))
  exit 1
  ```
  `<M>` is the rename commit; the path prints whole, spaces and `ï` included.
- Step 6: `7 passed, 29 deselected`.

**Implementation Reference:** Story 1 — Files: `scripts/repro-order.py` (`_parse_name_status`, `classify`, rule 6 in `apply_rules`)

**Status:** [ ] Pass  [ ] Fail

**Notes:**

---

### Scenario 10: Tests outside the known patterns need `--test-glob`; control characters in a path stay on one line

**Source:** Interaction Edge Case "Project tests outside known patterns" — Story 1; Technical Concerns (path heuristic); DEV-004
**Feature:** none
**Verification:** human — no recipe

**Preconditions:**
- Setup block pasted.

**Steps:**
1. `fx tg && ci tg "$RM" qa/login_check.py && ci tg "$FM" src/app.py && hist tg && roc tg`
2. `roc tg --test-glob 'qa/*'`
3. `fx cc && ci cc "$RM" tests/test_app.py "src/evil"$'\n'"reason: injected.py" && ci cc "$FM" src/app.py && roc cc && roc cc | grep -c '^reason:'`
4. `pt scripts/tests/test_repro_order.py -q -k "test_glob or control_characters" 2>&1 | tail -1`

**Expected Result:**
- Step 1: `fail`, `reason: repro_empty <R>`, `reason: repro_touches_source <R> qa/login_check.py`, `repro-order: fail (1 repro, 1 fix commit(s), 2 finding(s))`, `exit 1`.
- Step 2: `pass`, `reason: repro <R> … (1 test file)`, `reason: fix <F> … (1 source file)`, `repro-order: pass (1 repro, 1 fix commit(s))`, `exit 0`.
- Step 3: `fail`, then one line `reason: repro_touches_source <R> src/evil\nreason: injected.py` with a literal backslash and `n`, then `repro-order: fail (1 repro, 1 fix commit(s), 1 finding(s))`, `exit 1`; then `1`. The file name cannot add a `reason:` line.
- Step 4: `2 passed, 34 deselected`.

**Implementation Reference:** Story 1 — Files: `scripts/repro-order.py` (`classify`, `printable`)

**Status:** [ ] Pass  [ ] Fail

**Notes:**

---

## Story 2: The tdd-cycle Bug Path

### Scenario 11: The bug-path section follows "Staying honest" with the skip line, recognition rule, and surface rule

**Source:** Acceptance Criteria (AC-2.1) — Story 2; Business Rules 1 (Recognition) and 2 (Surface); State Catalog "Switch off" (skip line)
**Feature:** none
**Verification:** human — no recipe

**Preconditions:**
- Setup block pasted; `reset` prints nothing.

**Steps:**
1. `grep -n '^## \|^### ' "$CL/skills/tdd-cycle/SKILL.md"`
2. `sed -n '/^### Bug fixes: repro first/,/^1\. /p' "$CL/skills/tdd-cycle/SKILL.md"`
3. `sed -n '/^1\. \*\*Reproduce where the bug shows/,/^2\. /p' "$CL/skills/tdd-cycle/SKILL.md"`
4. `pt scripts/tests/test_repro_first_wiring.py -q -k "section_present or skip_line or recognition_and_surface" 2>&1 | tail -1`

**Expected Result:**
- Step 1: `## Purpose`, `## When to Use`, `## How to Apply`, `### The three beats`, `### Sizing each cycle`, `### Staying honest`, `### Bug fixes: repro first`, `## Examples`, in that order.
- Step 2: the heading; "Skip this section when `.writ/config.md` has the line `- **Repro First:** off`." and "A bug fix then starts from a failing test, as in the three beats."; then **Is it a bug?**: yes for an issue with `**Type:** Bug`, a file under `.writ/issues/bugs/`, a spec Origin citing such a file, or a request, issue, or story saying existing behavior is wrong (a crash, an error, a wrong result, a regression). When signals disagree, the deciding test is whether a test can fail today because the code does the wrong thing rather than because code is missing. A missing feature, a refactor, or a speed-up with correct output is not a bug.
- Step 3: enter through the surface the bug was seen on (run the CLI, send the request, render the component, call the public function). A unit test of the suspected cause is not the repro and can follow as a later cycle. When the harness cannot reach that surface, use the nearest one it can and note the gap.
- Step 4: `3 passed, 34 deselected`.

**Implementation Reference:** Story 2 — Files: `skills/tdd-cycle/SKILL.md` (§ Bug fixes: repro first)

**Status:** [ ] Pass  [ ] Fail

**Notes:**

---

### Scenario 12: The section's steps require a valid red, a test-only repro commit, a separate fix, the check, and a stated escape

**Source:** Acceptance Criteria (AC-2.2) — Story 2; Business Rules 3 to 5 and 8; DEV-006
**Feature:** none
**Verification:** human — no recipe

**Preconditions:**
- Setup block pasted; `reset` prints nothing.

**Steps:**
1. `sed -n '/^2\. \*\*Watch it fail/,/^## Examples/p' "$CL/skills/tdd-cycle/SKILL.md"`
2. `pt scripts/tests/test_repro_first_wiring.py -q -k "repro_fix_check_order or no_repro_escape" 2>&1 | tail -1`

**Expected Result:**
- Step 1, steps 2 to 6 and one closing paragraph:
  - Step 2: the failure shows the wrong value or the reported error; an import error, a missing fixture, or a broken harness is not a repro; keep the command and its output.
  - Step 3: commit the repro alone, test files only and at least one; fixtures under a test directory count, and so does un-skipping a test; type `test`; a `Repro: <issue path or one-line bug>` trailer "in the message's last paragraph with any other trailers and no blank line between them" (DEV-006).
  - Step 4: fix, then commit the fix separately; run the same command and keep the passing output; leave the repro's test files untouched; a wrong repro is reset and a corrected repro committed first; reset only unpushed commits.
  - Step 5: `python3 scripts/repro-order.py check --repo . --base <commit before the repro>`, then "Fix every `fail` reason before handing off."
  - Step 6: carry forward the command, the failing then passing output, both SHAs, and the check's output.
  - Closing paragraph: no repro possible (nondeterministic, environment-only, no harness): say `Repro: none` and why, add a regression test where one fits, and write no `Repro:` trailer.
- Step 2: `2 passed, 35 deselected`.

**Implementation Reference:** Story 2 — Files: `skills/tdd-cycle/SKILL.md`; WWB decisions 1 and 3

**Status:** [ ] Pass  [ ] Fail

**Notes:**

---

### Scenario 13: The When to Use bullet points at the section, and the bug example shows both commits and the check

**Source:** Acceptance Criteria (AC-2.3) — Story 2; DEV-006, DEV-007
**Feature:** none
**Verification:** human — no recipe

**Preconditions:**
- Setup block pasted; `reset` prints nothing.

**Steps:**
1. `sed -n '/^## When to Use/,/^## How to Apply/p' "$CL/skills/tdd-cycle/SKILL.md" | grep -i bug`
2. `sed -n '/^\*\*A bug fix that starts with a failing reproduction/,/^check:/p' "$CL/skills/tdd-cycle/SKILL.md"`
3. `grep -c parseDate "$CL/skills/tdd-cycle/SKILL.md"; git -C "$CL" show c687fab^:skills/tdd-cycle/SKILL.md | grep -c parseDate`
4. `pt scripts/tests/test_repro_first_wiring.py -q -k "when_to_use_points_here or example_shows_bug_path" 2>&1 | tail -1`

**Expected Result:**
- Step 1: two lines: "the code exists — the default for feature and bug-fix work." and "- Fixing a bug: follow `### Bug fixes: repro first` under How to Apply."
- Step 2: the bold label, the opening `text` fence, then:
  ```text
  red:    test "POST /login accepts a+b@example.com" → 401 (bug: plus sign rejected)
  commit: test(auth): reproduce login failure for plus-sign emails
          Repro: login fails for plus-sign emails
  green:  stop stripping '+' in normalizeEmail                       → 200
  commit: fix(auth): accept a plus sign in the login email
  check:  repro-order: pass (1 repro, 1 fix commit(s))
  ```
  The `Repro:` trailer sits on its own line under the repro commit (DEV-006).
- Step 3: `0`, then `1`. The former three-line `parseDate('')` example is gone (DEV-007).
- Step 4: `2 passed, 35 deselected`.

**Implementation Reference:** Story 2 — Files: `skills/tdd-cycle/SKILL.md` (§ When to Use, § Examples)

**Status:** [ ] Pass  [ ] Fail

**Notes:**

---

### Scenario 14: `config-format.md` documents the `Repro First` row and section after Reviewer Filters

**Source:** Acceptance Criteria (AC-2.4) — Story 2; Business Rule 9; DEV-005
**Feature:** none
**Verification:** human — no recipe

**Preconditions:**
- Setup block pasted; `reset` prints nothing.

**Steps:**
1. ``sed -n '/^## Supported Keys/,/^## Read Order/p' "$CL/.writ/docs/config-format.md" | grep '^| `' | tail -1``
2. `grep -n '^## ' "$CL/.writ/docs/config-format.md" | tail -6`
3. `sed -n '/^## Repro First/,/^## Rules/p' "$CL/.writ/docs/config-format.md"`
4. `pt scripts/tests/test_repro_first_wiring.py -q -k "config_row or config_section" 2>&1 | tail -1`

**Expected Result:**
- Step 1: the last Supported Keys row: ``| `Repro First` | tdd-cycle, coding-agent, prototype, implement-story (Gate 1) | `off` turns off the repro-first bug path; absent or `on` keeps it; see [Repro First](#repro-first) |``.
- Step 2: `## Review Panel`, `## Gate 0 Divergence`, `## Safety Fact`, `## Reviewer Filters`, `## Repro First`, `## Rules`. The section follows the last switch section, not Review Panel (DEV-005).
- Step 3: a fenced `- **Repro First:** off` example, then one paragraph: the line goes under `## Conventions`; it is never detected or offered for saving; no line, an empty value, or `on` means on; only `off`, in any case, turns it off; any other value means on and the check prints `reason: repro-first value <value> read as on`; the first matching line wins; the key must match the case shown. With `off`, the skill's bug path is skipped and a bug fix still starts from a failing test, the `### Repro` block reads `Repro: off`, neither `/prototype` nor `/implement-story` runs the check, the cherry-pick rule does not apply, and the check run by hand prints `unverifiable` and `reason: repro-first off` and exits 0 before reading git.
- Step 4: `2 passed, 35 deselected`.

**Implementation Reference:** Story 2 — Files: `.writ/docs/config-format.md` (§ Supported Keys, § Repro First)

**Status:** [ ] Pass  [ ] Fail

**Notes:**

---

### Scenario 15: The skill passes lint and the plain-prose scan, generators are current, and a missing skip line fails a test

**Source:** Acceptance Criteria (AC-2.5) — Story 2; Business Rule 12 (Plain prose and lint)
**Feature:** none
**Verification:** human — no recipe

**Preconditions:**
- Setup block pasted; `reset` prints nothing.

**Steps:**
1. `(cd "$CL" && bash scripts/lint-skill.sh skills/tdd-cycle/SKILL.md > "$W/lint.txt"; echo "exit $?"; sed -n '1p;$p' "$W/lint.txt")`
2. `sed -n '/^### Bug fixes: repro first/,/^## Examples/p' "$CL/skills/tdd-cycle/SKILL.md" > "$W/new-text.md"; sed -n '/^## Repro First/,/^## Rules/p' "$CL/.writ/docs/config-format.md" >> "$W/new-text.md"; sed -n '/^### 1\. Scan/,/^### 2\./p' "$CL/skills/plain-prose/SKILL.md" | grep '^grep ' | sed "s#FILE#$W/new-text.md#" | bash`
3. `(cd "$CL" && python3 scripts/gen-platform-trees.py --check | tail -1)`
4. `pt scripts/tests/test_repro_first_wiring.py -q -k "section_present or skip_line or recognition or repro_fix_check_order or no_repro_escape or when_to_use or example_shows or config_row or config_section or lint_skill_passes" 2>&1 | tail -1`
5. `sed -i '' '/^Skip this section when/d' "$CL/skills/tdd-cycle/SKILL.md"; pt scripts/tests/test_repro_first_wiring.py -q -k skip_line 2>&1 | grep -E 'does not name|failed|passed'; reset`

**Expected Result:**
- Step 1: `exit 0`, `pass`, and a last line starting `lint-skill: pass`.
- Step 2: prints nothing. The three step 1 greps from `skills/plain-prose/SKILL.md` find no hit in the new skill section or the config section.
- Step 3: `gen-platform-trees: pass (0 stale, 0 missing, 0 orphan, 0 unmapped, 0 vendor)`.
- Step 4: `10 passed, 27 deselected` (the ten Story 2 tests).
- Step 5: assertion lines with `section does not name '- **Repro First:** off'`, then `1 failed, 36 deselected`. `reset` prints nothing.

**Implementation Reference:** Story 2 — Files: `scripts/tests/test_repro_first_wiring.py` (Story 2 tests), `plugins/writ/skills/tdd-cycle/SKILL.md` and `cursor/plugin/skills/tdd-cycle/SKILL.md` (generated)

**Status:** [ ] Pass  [ ] Fail

**Notes:**

---

## Story 3: The Coding Agent's Repro Report

### Scenario 16: Requirement 1 names the bug path and Requirement 3 sets the `Ref:` footer rule

**Source:** Acceptance Criteria (AC-3.1) — Story 3; Business Rule 6 (Story pipeline footer); DEV-008
**Feature:** none
**Verification:** human — no recipe

**Preconditions:**
- Setup block pasted; `reset` prints nothing.

**Steps:**
1. `grep -n -o 'For a bug fix, follow .*$' "$CL/agents/coding-agent.md"`
2. ``grep -n -o 'Under `/implement-story`, the repro and fix commits .*$' "$CL/agents/coding-agent.md"``
3. `pt scripts/tests/test_repro_first_wiring.py -q -k "requirement_1 or requirement_3" 2>&1 | tail -1`

**Expected Result:**
- Step 1: line 116, Implementation Requirement 1 (**Follow TDD**), ending "For a bug fix, follow the `### Bug fixes: repro first` section of `skills/tdd-cycle/SKILL.md`."
- Step 2: line 118, inside Requirement 3 (**Small commits**): "Under `/implement-story`, the repro and fix commits each end with `Ref: .writ/specs/<spec-id>/user-stories/<story-file>.md` in the message's last paragraph, with any other trailers (and, on the repro commit, its `Repro:` trailer); `/prototype` commits carry no `Ref:` footer." The last-paragraph clause and the repro-commit qualifier are DEV-008.
- Step 3: `2 passed, 35 deselected`.

**Implementation Reference:** Story 3 — Files: `agents/coding-agent.md` (Implementation Requirements 1 and 3)

**Status:** [ ] Pass  [ ] Fail

**Notes:**

---

### Scenario 17: The `### Repro` block's bug form has seven fields in order between Self-Check Results and Boundary Compliance

**Source:** Acceptance Criteria (AC-3.2) — Story 3; Business Rule 7 (Report); State Catalog "Bug, harness cannot reach the surface" (`gap:` field); DEV-009
**Feature:** none
**Verification:** human — no recipe

**Preconditions:**
- Setup block pasted; `reset` prints nothing.

**Steps:**
1. `grep -n 'A \*\*### Repro\*\* subsection' "$CL/agents/coding-agent.md"`
2. `sed -n '/^### Self-Check Results/,/^_Bug without a repro:_/p' "$CL/agents/coding-agent.md"`
3. `pt scripts/tests/test_repro_first_wiring.py -q -k "output_requirements_repro_item or fence_and_position or bug_with_repro_form" 2>&1 | tail -1`

**Expected Result:**
- Step 1: `150:- A **### Repro** subsection in every report, in exactly one of the four forms under **Output Format** below`
- Step 2: `### Self-Check Results` and its lines, then `### Repro`, the line `_Every report has this section, in exactly one of these four forms. List commits oldest first._`, then `_Bug with a repro:_` and seven fields in this order: `Kind:` (bug and the recognition signal), `Surface:` (where the bug shows; the entry point the test enters through; an optional `gap:`), `Command:`, ``Commits:`` in the shape ``repro `[sha]` → fix `[sha]`[, `[sha]`]``, `Before the fix (failing):` with a `text` fence holding `[at most 20 lines]`, `After the fix (passing):` with `[at most 10 lines from the same command]`, and `Check:` (line 1, any `reason:` lines, and the summary line of `repro-order.py check`). The four forms sit in one block under italic labels (DEV-009).
- Step 3: `3 passed, 34 deselected`.

**Implementation Reference:** Story 3 — Files: `agents/coding-agent.md` (§ Output Requirements, § Output Format; outer fence widened to four backticks)

**Status:** [ ] Pass  [ ] Fail

**Notes:**

---

### Scenario 18: The three short forms: no repro, not a bug fix, switch off

**Source:** Acceptance Criteria (AC-3.3) — Story 3; Business Rules 8 and 9; State Catalog "Bug, no repro possible", "Not a bug fix", "Switch off"
**Feature:** none
**Verification:** human — no recipe

**Preconditions:**
- Setup block pasted; `reset` prints nothing.

**Steps:**
1. `sed -n '/^_Bug without a repro:_/,/^### Boundary Compliance/p' "$CL/agents/coding-agent.md"`
2. `pt scripts/tests/test_repro_first_wiring.py -q -k short_forms 2>&1 | tail -1`

**Expected Result:**
- Step 1: `_Bug without a repro:_` with `- **Kind:** bug: [signal]`, `- **Repro:** none: [reason]`, `- **Regression test:** [path, or none]`; `_Not a bug fix:_` with `- **Kind:** not a bug fix: [reason]`; ``_Switch off (`.writ/config.md` has `- **Repro First:** off`):_`` with `- **Repro:** off`; then `### Boundary Compliance`. None of the three names a commit.
- Step 2: `1 passed, 36 deselected`.

**Implementation Reference:** Story 3 — Files: `agents/coding-agent.md` (§ Output Format → `### Repro`)

**Status:** [ ] Pass  [ ] Fail

**Notes:**

---

### Scenario 19: The generated Claude Code and Codex agent files carry the block unchanged

**Source:** Acceptance Criteria (AC-3.4) — Story 3
**Feature:** none
**Verification:** human — no recipe

**Preconditions:**
- Setup block pasted; `reset` prints nothing.

**Steps:**
1. `for f in claude-code/agents/writ-coder.md codex/agents/coding-agent.toml; do diff <(sed -n '/^### Repro/,/^### Boundary Compliance/p' "$CL/agents/coding-agent.md") <(sed -n '/^### Repro/,/^### Boundary Compliance/p' "$CL/$f") > /dev/null && echo "same: $f"; done`
2. `sed -n '/^### Repro/,/^### Boundary Compliance/p' "$CL/codex/agents/coding-agent.toml" | grep -c '^- \*\*'`
3. `(cd "$CL" && python3 scripts/gen-platform-trees.py --check | tail -1)`
4. `pt scripts/tests/test_repro_first_wiring.py -q -k "generated_copy or generated_trees_current" 2>&1 | tail -1`

**Expected Result:**
- Step 1: `same: claude-code/agents/writ-coder.md` and `same: codex/agents/coding-agent.toml`.
- Step 2: `12` (seven fields in the bug form, three in the no-repro form, one each in the other two).
- Step 3: `gen-platform-trees: pass (0 stale, 0 missing, 0 orphan, 0 unmapped, 0 vendor)`.
- Step 4: `3 passed, 34 deselected`.

**Implementation Reference:** Story 3 — Files: `claude-code/agents/writ-coder.md`, `codex/agents/coding-agent.toml` (generated)

**Status:** [ ] Pass  [ ] Fail

**Notes:**

---

### Scenario 20: Story 3's wiring tests pass, and a changed switch-off form fails one

**Source:** Acceptance Criteria (AC-3.5) — Story 3
**Feature:** none
**Verification:** human — no recipe

**Preconditions:**
- Setup block pasted; `reset` prints nothing.

**Steps:**
1. `pt scripts/tests/test_repro_first_wiring.py -q -k "requirement or output_ or generated" 2>&1 | tail -1`
2. `sed -i '' 's/^- \*\*Repro:\*\* off$/- **Repro:** disabled/' "$CL/agents/coding-agent.md"; pt scripts/tests/test_repro_first_wiring.py -q -k short_forms 2>&1 | grep -E 'switch-off form changed|failed|passed'; reset`

**Expected Result:**
- Step 1: `9 passed, 28 deselected` (the nine Story 3 tests).
- Step 2: assertion lines with `switch-off form changed: ['- **Repro:** disabled']`, then `1 failed, 36 deselected`. `reset` prints nothing.
- The full pytest run, the bash test loop, and `bash scripts/eval.sh` for this criterion are Scenario 27, Steps 5 to 7.

**Implementation Reference:** Story 3 — Files: `scripts/tests/test_repro_first_wiring.py` (Story 3 tests)

**Status:** [ ] Pass  [ ] Fail

**Notes:**

---

## Story 4: Consumer Wiring and Ordered-Commit Integration

### Scenario 21: `/prototype` Step 3 names the bug path and integrates named commits by cherry-pick; nothing else changed

**Source:** Acceptance Criteria (AC-4.1) — Story 4; Business Rule 10 (Enforcement differs by consumer); DEV-012
**Feature:** none
**Verification:** human — no recipe

**Preconditions:**
- Setup block pasted; `reset` prints nothing.

**Steps:**
1. `sed -n '/^### Step 3: Spawn Coding Agent/,/^### Step 4:/p' "$CL/commands/prototype.md" | grep -n 'git apply\|^\*\*Bug path\|^1\. \*\*TDD'`
2. `git -C "$CL" diff --numstat cbf054a^ cbf054a -- commands/prototype.md; diff <(git -C "$CL" show cbf054a^:commands/prototype.md | sed '/^### Step 3:/,/^### Step 4:/d') <(sed '/^### Step 3:/,/^### Step 4:/d' "$CL/commands/prototype.md") && echo "outside Step 3: identical"`
3. `pt scripts/tests/test_repro_first_wiring.py -q -k prototype 2>&1 | tail -1; pt scripts/tests/test_prototype_worktree_integration.py -q 2>&1 | tail -1`

**Expected Result:**
- Step 1, three lines in this order:
  - the integration sentence that pipes a worktree's diff into `git apply` (unchanged);
  - the `**Bug path:**` line: record `git rev-parse HEAD` before spawning; when the agent's `### Repro` block names commits, bring them into this checkout with `git cherry-pick`, oldest first, as the integration skill's Ordered commits paragraph says, not through `git apply` (DEV-012); then run `python3 scripts/repro-order.py check --repo . --base <that SHA>` and put its output and the failing-then-passing output in the Step 5 summary; `fail` makes the summary "Prototype Complete (with issues)";
  - principle 1: "A bug fix follows the bug path in `skills/tdd-cycle/SKILL.md`: a failing repro committed before the fix."
- The line fires only when the block names commits. The switch-off form (`Repro: off`) names none, so it never fires.
- Step 2: `3`, `1`, `commands/prototype.md`, then `outside Step 3: identical` (Step 2.5 and every other section are byte-identical to before Story 4).
- Step 3: `5 passed, 32 deselected`; then a line with no `failed` (the `git apply` sentence is still pinned).

**Implementation Reference:** Story 4 — Files: `commands/prototype.md` (Step 3); WWB decision 1

**Status:** [ ] Pass  [ ] Fail

**Notes:**

---

### Scenario 22: `/implement-story` Gate 1 has the Bug path line; the rest of the file is unchanged and Gate 1 stays prose-only

**Source:** Acceptance Criteria (AC-4.2) — Story 4; Business Rule 10; State Catalog "Check fails after integration"; DEV-013
**Feature:** none
**Verification:** human — no recipe

**Preconditions:**
- Setup block pasted; `reset` prints nothing.

**Steps:**
1. `sed -n '/^#### Gate 1:/,/^#### Gate 2:/p' "$CL/commands/implement-story.md" | grep '^\*\*' | cut -c1-40`
2. `sed -n '/^#### Gate 1:/,/^#### Gate 2:/p' "$CL/commands/implement-story.md" | grep '^\*\*Bug path'`
3. `grep -n -A1 'id: gate1_coding' "$CL/commands/implement-story.md"`
4. `git -C "$CL" diff --numstat cbf054a^ cbf054a -- commands/implement-story.md; diff <(git -C "$CL" show cbf054a^:commands/implement-story.md | sed '/^#### Gate 1:/,/^#### Gate 2:/d') <(sed '/^#### Gate 1:/,/^#### Gate 2:/d' "$CL/commands/implement-story.md") && echo "outside Gate 1: identical"`
5. `(cd "$CL" && python3 scripts/verdict-provenance.py check --command commands/implement-story.md)`
6. `pt scripts/tests/test_repro_first_wiring.py -q -k "gate1 or implement" 2>&1 | tail -1`

**Expected Result:**
- Step 1: five leads in order: `**Context routing:**`, `**When Gate 0.5 was skipped**`, `**Report:**`, `**Bug path:**`, ``**On `STATUS: BLOCKED`:**``.
- Step 2: record `git rev-parse HEAD` before the story's first Gate 1 spawn and reuse it on recodes; when the report's `### Repro` block names commits, run `python3 scripts/repro-order.py check --repo . --base <that SHA>` after integration and print its first line as `repro-order:` in the Step 4 report; `fail` marks the story `⚠️ DEGRADED` with its `reason:` lines; `unverifiable`, or exit 2 with its stderr cause, prints and continues (DEV-013). No retry or loop increment is named.
- Step 3: `  - id: gate1_coding`, then `    verification: prose-only`.
- Step 4: `2`, `0`, `commands/implement-story.md`, then `outside Gate 1: identical`. Gates 0, 2.5, and 3, the `gates:` frontmatter, and Step 4 are byte-identical to before Story 4.
- Step 5: `pass`, a `note: prose_only_count: 1 (cap 1)` line, and a `verdict-provenance: pass (…)` summary with `prose-only: 1` and `findings: 0`.
- Step 6: `5 passed, 32 deselected`.

**Implementation Reference:** Story 4 — Files: `commands/implement-story.md` (Gate 1); WWB decisions 2 and 3

**Status:** [ ] Pass  [ ] Fail

**Notes:**

---

### Scenario 23: The story-start base keeps a recode's extra fix in range; a per-spawn base would fail it

**Source:** Acceptance Criteria (AC-4.2) — Story 4; DEV-013 (Gate 3 cycle 1 finding)
**Feature:** none
**Verification:** human — no recipe

**Preconditions:**
- Setup block pasted.

**Steps:**
1. A first pass (repro and fix), then a recode's fix: `fx rcd && ci rcd "$RM" tests/test_app.py && ci rcd "$FM" src/app.py && git -C "$W/r/rcd" tag pass1 && ci rcd 'fix: add also handles floats (recode after review)' src/app.py && hist rcd`
2. From the story-start base: `roc rcd`
3. From a base recorded again before the recode spawn: `python3 "$RO" check --repo "$W/r/rcd" --base pass1; echo "exit $?"`
4. `rc python3 "$RO" check --repo "$W/r/rcd" --base no-such-base`

**Expected Result:**
- Step 1: three commits: the repro, the first fix, the recode's fix.
- Step 2: `pass`, `reason: repro <R> …`, `reason: fix <F1> fix: add returns the sum (1 source file)`, `reason: fix <F2> fix: add also handles floats (recode after review) (1 source file)`, `repro-order: pass (1 repro, 2 fix commit(s))`, `exit 0`.
- Step 3: `fail`, `reason: no_repro_commit`, `repro-order: fail (0 repro, 0 fix commit(s), 1 finding(s))`, `exit 1`. This is the false `⚠️ DEGRADED` the story-start base prevents.
- Step 4: `exit 2 stdout-bytes 0`, then `repro-order: cannot resolve no-such-base`. Stdout is empty, which is why the Gate 1 line routes exit 2 by its stderr cause.

**Implementation Reference:** Story 4 — Files: `commands/implement-story.md` (Gate 1 `**Bug path:**`); WWB decision 2

**Status:** [ ] Pass  [ ] Fail

**Notes:**

---

### Scenario 24: The integration skill's step 3 ends with the Ordered commits paragraph

**Source:** Acceptance Criteria (AC-4.3) — Story 4
**Feature:** none
**Verification:** human — no recipe

**Preconditions:**
- Setup block pasted; `reset` prints nothing.

**Steps:**
1. `sed -n '/^### 3\. Copy changed/,/^### 4\./p' "$CL/skills/subagent-worktree-integration/SKILL.md"`
2. `(cd "$CL" && bash scripts/lint-skill.sh skills/subagent-worktree-integration/SKILL.md | tail -1)`
3. `pt scripts/tests/test_repro_first_wiring.py -q -k "ordered_commits or lint_integration" 2>&1 | tail -1`

**Expected Result:**
- Step 1: the copy paragraph, then a last paragraph beginning `**Ordered commits.**`: when the agent's result names commits whose order is evidence, such as a repro commit before its fix, carry them with `git cherry-pick <sha>...`, oldest first, instead of copying their files, so the order and message trailers survive; on a conflict, run `git cherry-pick --abort`, copy the files as above, and say that the order was lost.
- Step 2: a line starting `lint-skill: pass`.
- Step 3: `2 passed, 35 deselected`.

**Implementation Reference:** Story 4 — Files: `skills/subagent-worktree-integration/SKILL.md` (step 3)

**Status:** [ ] Pass  [ ] Fail

**Notes:**

---

### Scenario 25: Cherry-picking keeps the repro-then-fix order; applying a diff loses it

**Source:** Acceptance Criteria (AC-4.3) — Story 4; Shadow Path "Happy path" (orchestrator re-run `pass`); Hardest Constraint; DEV-012
**Feature:** none
**Verification:** human — no recipe

**Preconditions:**
- Setup block pasted.
- `rm -rf "$W/r/wt-agent"; fx wt && git -C "$W/r/wt" worktree add -q -b agent "$W/r/wt-agent" base` (an agent's worktree beside the orchestrator's checkout)

**Steps:**
1. The agent commits in its worktree: `B=$(git -C "$W/r/wt" rev-parse HEAD); ci wt-agent "$RM" tests/test_app.py && ci wt-agent "$FM" src/app.py && git -C "$W/r/wt-agent" log --reverse --format='%h %s' "$B"..HEAD`
2. Integrate by diff, as `/prototype` Step 3's `git apply` sentence does: `git -C "$W/r/wt-agent" diff "$B" HEAD | git -C "$W/r/wt" apply && git -C "$W/r/wt" status --short; python3 "$RO" check --repo "$W/r/wt" --base "$B"; echo "exit $?"`
3. Undo, then integrate by cherry-pick, oldest first: `git -C "$W/r/wt" checkout -q -- . && git -C "$W/r/wt" cherry-pick $(git -C "$W/r/wt" rev-list --reverse "$B"..agent) > /dev/null && hist wt && python3 "$RO" check --repo "$W/r/wt" --base "$B"; echo "exit $?"`
4. `git -C "$W/r/wt" log -1 --format=%B HEAD~1 | tail -1`

**Expected Result:**
- Step 1: the repro, then the fix.
- Step 2: ` M src/app.py` and ` M tests/test_app.py`: the files arrived and the commits did not. The check prints `fail`, `reason: no_repro_commit`, `repro-order: fail (0 repro, 0 fix commit(s), 1 finding(s))`, `exit 1`.
- Step 3: `hist` shows the repro, then the fix. The check prints `pass`, the repro and fix lines, `repro-order: pass (1 repro, 1 fix commit(s))`, `exit 0`.
- Step 4: `Repro: add(2, 3) returns -1, not 5`. The trailer survived.

**Implementation Reference:** Story 4 — Files: `skills/subagent-worktree-integration/SKILL.md` (Ordered commits), `commands/prototype.md` (Step 3 `**Bug path:**`)

**Status:** [ ] Pass  [ ] Fail

**Notes:**

---

### Scenario 26: Every Removal Inventory row is pinned, and deleting one fails a test that names it

**Source:** Acceptance Criteria (AC-4.4) — Story 4; spec.md § Removal Inventory; DEV-007
**Feature:** none
**Verification:** human — no recipe

**Preconditions:**
- Setup block pasted; `reset` prints nothing.

**Steps:**
1. `pt scripts/tests/test_repro_first_wiring.py -q -k "removal_inventory or generated_trees_current" 2>&1 | tail -1`
2. `sed -i '' '/^\*\*Ordered commits\.\*\*/,/^lost\.$/d' "$CL/skills/subagent-worktree-integration/SKILL.md"; pt scripts/tests/test_repro_first_wiring.py -q -k "removal_inventory or ordered_commits" 2>&1 | grep -E 'Removal Inventory row|failed|passed'; reset`
3. `rm "$CL/scripts/repro-order.py"; pt scripts/tests/test_repro_first_wiring.py -q -k removal_inventory 2>&1 | grep -E 'Removal Inventory row|failed|passed'; reset`
4. `echo "hand edit" >> "$CL/plugins/writ/skills/tdd-cycle/SKILL.md"; (cd "$CL" && python3 scripts/gen-platform-trees.py --check | tail -1); reset`

**Expected Result:**
- Step 1: `9 passed, 28 deselected`: one case per text row (`tdd-cycle`, `coding-agent`, `prototype`, `implement-story`, `worktree-integration`, `script-files`, `cli-contract`, `config-format`) plus the generated-trees row. The `tdd-cycle` case also requires the When to Use bullet (DEV-007).
- Step 2: lines with ``Removal Inventory row `skills/subagent-worktree-integration/SKILL.md`: missing the ordered-commits paragraph in step 3``, then `2 failed, 7 passed, 28 deselected`. `reset` prints nothing.
- Step 3: lines with ``Removal Inventory row `scripts/repro-order.py, scripts/tests/test_repro_order.py, scripts/tests/test_repro_first_wiring.py`: missing scripts/repro-order.py``, then `1 failed, 7 passed, 29 deselected`. `reset` prints nothing.
- Step 4: `gen-platform-trees: fail (1 stale, 0 missing, 0 orphan, 0 unmapped, 0 vendor)`. `reset` prints nothing.

**Implementation Reference:** Story 4 — Files: `scripts/tests/test_repro_first_wiring.py` (`REMOVAL_INVENTORY`, `test_removal_inventory_row`, `test_generated_trees_current`)

**Status:** [ ] Pass  [ ] Fail

**Notes:**

---

### Scenario 27: Generators, lint, byte caps, the full test suite, the bash tests, and the quality gate are green

**Source:** Acceptance Criteria (AC-4.5) — Story 4; also AC-3.5 and AC-2.5 (full-run parts), Story 1 task 1.7; Success Criteria; DEV-010, DEV-011
**Feature:** none
**Verification:** human — no recipe

**Preconditions:**
- Setup block pasted; `reset` prints nothing. Run outside any sandbox (`eval.sh` runs `git init` in a temp dir). About five minutes. Run pytest alone, not beside `eval.sh` or the bash tests.

**Steps:**
1. `(cd "$CL" && python3 scripts/gen-platform-trees.py --check | tail -1)`
2. `(cd "$CL" && bash scripts/lint-skill.sh skills/tdd-cycle/SKILL.md skills/subagent-worktree-integration/SKILL.md | tail -1)`
3. `wc -c < "$CL/commands/implement-story.md"; grep -n -B1 '"commands/implement-story.md": ' "$CL/scripts/tests/test_governor_enforcement.py"; grep -n -B2 '^IMPLEMENT_STORY_CAP =' "$CL/scripts/tests/test_review_route_rigor.py"`
4. `grep -n 'AC-3.5\|AC-4.5' "$CL/scripts/tests/test_repro_first_wiring.py"`
5. `pt -q 2>&1 | tail -1`
6. `(cd "$CL" && for t in scripts/tests/test_*.sh; do bash "$t" > /dev/null 2>&1 || echo "FAIL $t"; done; echo "bash loop done")`
7. `(cd "$CL" && bash scripts/eval.sh > /dev/null; echo "exit $?"); tail -2 "$(ls -t "$CL"/.writ/state/eval-*.md | head -1)"`
8. `reset`

**Expected Result:**
- Step 1: `gen-platform-trees: pass (0 stale, 0 missing, 0 orphan, 0 unmapped, 0 vendor)`.
- Step 2: a line starting `lint-skill: pass`.
- Step 3: `40677`; `# 2026-10-29 (2026-10-25-repro-first-bug-fixing Story 4): 15269 -> 15717; Gate 1 bug-path line.` directly above `"commands/implement-story.md": 15717,` (40,677 − 24,960 = 15,717); and the dated `40234 -> 40682, +448` comment above `IMPLEMENT_STORY_CAP = 40682`, the file plus 5 bytes (DEV-010).
- Step 4: docstring lines citing AC-3.5 and AC-4.5 as the full-run criteria (DEV-011).
- Step 5: no `failed` (Story 4 recorded `3518 passed, 3 skipped` on its lane; the merged tree's counts differ).
- Step 6: only `bash loop done`; no `FAIL` line.
- Step 7: `exit 0`, then `- Findings: 0` and `- Run errors: 0`.
- Step 8: prints nothing.

**Implementation Reference:** Story 4 — Files: `scripts/tests/test_governor_enforcement.py` (`KNOWN_OVER_BUDGET`), `scripts/tests/test_review_route_rigor.py` (`IMPLEMENT_STORY_CAP`), `scripts/tests/test_repro_first_wiring.py`

**Status:** [ ] Pass  [ ] Fail

**Notes:**

---

### Scenario 28: A cherry-pick conflict at integration ends in `fail` / `no_repro_commit`

**Source:** Error Map "Integration" (cherry-pick conflict) — Story 4; State Catalog "Cherry-pick conflict at integration"; Technical Concerns (stale base)
**Feature:** none
**Verification:** human — no recipe

**Preconditions:**
- Setup block pasted.
- `rm -rf "$W/r/cf-agent"; fx cf && git -C "$W/r/cf" worktree add -q -b agent "$W/r/cf-agent" base`

**Steps:**
1. The checkout moves past the commit the agent's worktree started from: `printf 'def add(a, b):\n    return b - a\n' > "$W/r/cf/src/app.py" && git -C "$W/r/cf" commit -qam "refactor: swap the operands" && B=$(git -C "$W/r/cf" rev-parse HEAD) && echo "$B" | cut -c1-7`
2. The agent commits a repro and a fix on the older base: `ci cf-agent "$RM" tests/test_app.py && printf 'def add(a, b):\n    return a + b\n' > "$W/r/cf-agent/src/app.py" && git -C "$W/r/cf-agent" commit -qam "$FM"`
3. `git -C "$W/r/cf" cherry-pick $(git -C "$W/r/cf" rev-list --reverse base..agent); echo "exit $?"`
4. Follow the paragraph: abort, copy the files: `git -C "$W/r/cf" cherry-pick --abort; git -C "$W/r/cf" log -1 --format='%h %s'; for f in $(git -C "$W/r/cf" diff --name-only base agent); do cp "$W/r/cf-agent/$f" "$W/r/cf/$f"; done; git -C "$W/r/cf" status --short`
5. `python3 "$RO" check --repo "$W/r/cf" --base "$B"; echo "exit $?"`

**Expected Result:**
- Step 3: a `CONFLICT (content): Merge conflict in src/app.py` line and a non-zero exit.
- Step 4: HEAD is the Step 1 SHA with `refactor: swap the operands` (the abort also undid the repro that had applied). Status: ` M src/app.py` and ` M tests/test_app.py`.
- Step 5: `fail`, `reason: no_repro_commit`, `repro-order: fail (0 repro, 0 fix commit(s), 1 finding(s))`, `exit 1`. The lost order shows as a failure rather than passing quietly. Under `/implement-story` this marks the story `⚠️ DEGRADED`; under `/prototype` the summary reads "Prototype Complete (with issues)".

**Implementation Reference:** Story 4 — Files: `skills/subagent-worktree-integration/SKILL.md` (Ordered commits, conflict clause)

**Status:** [ ] Pass  [ ] Fail

**Notes:**

---

### Scenario 29: `/prototype` on a bug issue: repro through the CLI, two ordered commits, `repro-order: pass`

**Source:** Experience Design Entry Point, Happy Path, Moment of Truth, and Feedback Model — Story 4; AC-4.1; State Catalog "Bug, repro on the bug's surface"; Business Rules 1, 2, 6, 7; Shadow Path "Happy path" (orchestrator re-run); DEV-012
**Feature:** none
**Verification:** human — no recipe

**Preconditions:**
- Setup block pasted. `fxreset` prints nothing; the switch is absent from `$FX/.writ/config.md`.
- `(cd "$FX" && python3 -m uatfx.slug "C++ tips")` prints `c-tips`, and `(cd "$FX" && uv run --python 3.9 pytest uatfx/tests -q 2>&1 | tail -1)` reports `2 passed`: the unit test passes while the CLI is wrong.
- `live` running in a new session in the second shell.

**Steps:**
1. `/prototype --no-diverge @.writ/issues/bugs/2026-10-29-slug-cli-drops-plus.md`
2. Approve the git and test commands. Read the Step 5 summary, then expand the coding agent's entry (ctrl+o) and read its `### Repro` section.
3. In the first shell: `fxlog uat-fixture`
4. `python3 "$FX/scripts/repro-order.py" check --repo "$FX" --base uat-fixture; echo "exit $?"`
5. `(cd "$FX" && python3 -m uatfx.slug "C++ tips" && uv run --python 3.9 pytest uatfx/tests -q 2>&1 | tail -1); git -C "$FX" status --short`
6. `fxreset`

**Expected Result:**
- Step 2, the summary: `✅ Prototype Complete`, not "(with issues)". It carries the check's output (`pass`, a `reason: repro …` line, one `reason: fix …` line per fix commit, `repro-order: pass (1 repro, <n> fix commit(s))`) and the same command's output before the fix (failing, showing `c-tips` where `c++-tips` was expected) and after it (passing). In the transcript, `git rev-parse HEAD` runs before the spawn; if the agent worked in a worktree, the orchestrator brought its commits in with `git cherry-pick`, oldest first, not `git apply`.
- Step 2, the agent's `### Repro`: the full form. `Kind:` names the bug issue under `.writ/issues/bugs/`. `Surface:` names the CLI's output, and the test enters through the CLI: it runs `python3 -m uatfx.slug` or calls `main` with arguments and reads what it prints. A test that calls only `slugify` is not the repro (that test already passes). `Commits:` reads `repro <sha> → fix <sha>`. The failing output is at most 20 lines and shows the wrong value, not an import or harness error; the passing output is at most 10 lines from the same command. `Check:` shows `pass`.
- Step 3: the first commit has a `test` subject and only files under `uatfx/tests/`; its last paragraph holds a `Repro:` line naming the issue path or the bug, and any `Co-Authored-By:` line sits in that same paragraph. Each later commit changes `uatfx/slug.py` and none touches the first commit's test files. No commit has a `Ref:` line.
- Step 4: the same `pass` output as the summary, with the SHAs from Step 3, and `exit 0`.
- Step 5: `c++-tips`, then a pytest line with no `failed`. `status` prints nothing.
- Step 6: prints nothing.

**Implementation Reference:** Story 4 — Files: `commands/prototype.md` (Step 3 `**Bug path:**`, Step 5); Story 2 — `skills/tdd-cycle/SKILL.md`; Story 3 — `agents/coding-agent.md` (`### Repro`)

**Status:** [ ] Pass  [ ] Fail

**Notes:**

---

### Scenario 30: `/prototype` with `Repro First: off`: `Repro: off`, no check, the fix still test-first

**Source:** Experience Design State Catalog "Switch off" — Story 4; Business Rule 9; AC-4.1 (a `Repro: off` report never triggers the line); Story 3 switch-off form
**Feature:** none
**Verification:** human — no recipe

**Preconditions:**
- Setup block pasted. `fxreset` prints nothing.
- `fxoff` prints the `- **Repro First:** off` line. The line is committed (tag `uat-off`) because the coding agent's worktree starts from a commit.
- `live` running in a new session.

**Steps:**
1. `/prototype --no-diverge @.writ/issues/bugs/2026-10-29-slug-cli-drops-plus.md`
2. Approve the commands. Read the Step 5 summary and the coding agent's `### Repro` section; search the transcript for `repro-order`.
3. In the first shell: `git -C "$FX" log --format=%B uat-off..HEAD | grep -c '^Repro:'; git -C "$FX" status --short`
4. `python3 "$FX/scripts/repro-order.py" check --repo "$FX" --base uat-off; echo "exit $?"`
5. `(cd "$FX" && python3 -m uatfx.slug "C++ tips")`
6. `fxreset`

**Expected Result:**
- Step 2: the agent's `### Repro` section is the single line `- **Repro:** off`. Neither the agent nor the orchestrator ran `repro-order.py`, and the summary has no `repro-order` output. The agent's report still lists a test written before the fix.
- Step 3: `0`. The fix is in the checkout, committed or listed by `status`.
- Step 4: `unverifiable`, `reason: repro-first off`, `repro-order: unverifiable (0 repro, 0 fix commit(s))`, `exit 0`.
- Step 5: `c++-tips`.
- Step 6: prints nothing.

**Implementation Reference:** Story 2 — `skills/tdd-cycle/SKILL.md` (skip line); Story 3 — `agents/coding-agent.md` (switch-off form); Story 4 — `commands/prototype.md` (fires only on named commits)

**Status:** [ ] Pass  [ ] Fail

**Notes:**

---

### Scenario 31: `/prototype` on a new option: `Kind: not a bug fix`, no check

**Source:** Experience Design State Catalog "Not a bug fix" — Story 4; Business Rule 1 (a missing feature is not a bug); Story 3 not-a-bug form
**Feature:** none
**Verification:** human — no recipe

**Preconditions:**
- Setup block pasted. `fxreset` prints nothing.
- `live` running in a new session.

**Steps:**
1. `/prototype --no-diverge "Add a --sep option to the slug CLI, so python3 -m uatfx.slug --sep _ hello world prints hello_world"`
2. Approve the commands. Read the Step 5 summary and the coding agent's `### Repro` section.
3. In the first shell: `git -C "$FX" log --format=%B uat-fixture..HEAD | grep -c '^Repro:'; (cd "$FX" && python3 -m uatfx.slug --sep _ hello world)`
4. `fxreset`

**Expected Result:**
- Step 2: the agent's `### Repro` section is `- **Kind:** not a bug fix: <reason>`, the reason naming a new option or missing behavior. No `repro-order` output in the summary or the transcript.
- Step 3: `0`, then `hello_world`.
- Step 4: prints nothing.

**Implementation Reference:** Story 2 — `skills/tdd-cycle/SKILL.md` (recognition rule); Story 3 — `agents/coding-agent.md` (not-a-bug form)

**Status:** [ ] Pass  [ ] Fail

**Notes:**

---

### Scenario 32: `/implement-story` on a story from a bug issue: `Ref:` footers and `repro-order: pass` in the Step 4 report

**Source:** Experience Design Entry Point and Feedback Model — Story 4; AC-4.2; Business Rules 1 (spec Origin signal), 6 (Story pipeline footer), 10; DEV-008, DEV-013
**Feature:** none
**Verification:** human — no recipe

**Preconditions:**
- Setup block pasted. `fxreset` prints nothing.
- `git -C "$FX" rev-parse uat-fixture | cut -c1-7` and note the SHA.
- `live` running in a new session. The run takes several minutes.

**Steps:**
1. `/implement-story .writ/specs/2026-10-29-uat-slug-plus/user-stories/story-1-cli-keeps-plus.md`
2. Approve the commands and let every gate run through Step 4. Read the Step 4 report, then expand the coding agent's entry and read its `### Repro` section.
3. In the first shell: `fxlog uat-fixture`
4. `python3 "$FX/scripts/repro-order.py" check --repo "$FX" --base uat-fixture; echo "exit $?"`
5. `grep -n '^> \*\*Status:\*\*' "$FX/$FS/user-stories/story-1-cli-keeps-plus.md"; python3 "$FX/scripts/revert-resolve.py" story 1 --repo "$FX" --spec 2026-10-29-uat-slug-plus --pretty`
6. `fxreset`

**Expected Result:**
- Step 2, the transcript: before the first Gate 1 spawn the orchestrator runs `git rev-parse HEAD` and gets the noted SHA. If a later gate sends the story back to Gate 1, no new base is recorded (DEV-013). After integration it runs `python3 scripts/repro-order.py check --repo . --base <that SHA>`; if the agent worked in a worktree, integration used `git cherry-pick`, oldest first.
- Step 2, the agent's `### Repro`: the full form. `Kind:` names the spec's `Origin` (or the bug issue it cites); `Commits:` names the repro and the fix.
- Step 2, the Step 4 report: a line `repro-order: pass`. The story is `Completed ✅`, with no `⚠️ DEGRADED`.
- Step 3: the repro commit comes first and changes only `uatfx/tests/test_slug.py`; its last paragraph holds both a `Repro:` line and `Ref: .writ/specs/2026-10-29-uat-slug-plus/user-stories/story-1-cli-keeps-plus.md`. Each fix commit changes `uatfx/slug.py` and ends with the same `Ref:` line. The story-completion commit or commits change only `.writ/` paths.
- Step 4: `pass`, one `reason: repro` line, one `reason: fix` line per fix commit, `repro-order: pass (1 repro, <n> fix commit(s))`, `exit 0`. The `.writ/`-only commits get no line. If the completion commit also changed a `uatfx/` file (a Gate 2 formatter), this re-run names it; record the file, because the Gate 1 check ran before Gate 2.
- Step 5: `> **Status:** Completed ✅ (…)`; the resolver lists the repro and fix commits, found by their `Ref:` footer, as well as the recorded completion commit.
- Step 6: prints nothing.
- See Known risks (a) and (b) under Conventions: a missing `repro-order:` line or a `⚠️ DEGRADED` story from a file-copy integration is a Fail.

**Implementation Reference:** Story 4 — Files: `commands/implement-story.md` (Gate 1 `**Bug path:**`); Story 3 — `agents/coding-agent.md` (Requirement 3); `scripts/revert-resolve.py` (`ref-footer` layer)

**Status:** [ ] Pass  [ ] Fail

**Notes:**

---

## Pending Stories

None. All four stories are Completed ✅.
