# UAT Plan: Review-Route Rigor

> **Generated:** 2026-10-29
> **Spec:** `.writ/specs/2026-10-25-review-route-rigor/`
> **Stories Covered:** 4 of 4 completed
> **Total Scenarios:** 42
> **Merged:** `7b6de50` on `phase/15-code-level-rigor`
> **Verification recipe:** none. No `.writ/docs/app-verification.md` exists, and Writ has no app to launch: its checks (pytest, the bash tests, `scripts/eval.sh`) read markdown and run scripts, not a running process. With no launch command detected, Step 1.3's recommended answer is skip, so no recipe was drafted, saved, or bound. Every scenario is `human — no recipe`.

## How to Use This Plan

1. Work through scenarios in order (they're grouped by story, ordered by priority)
2. For each scenario, follow the steps exactly as written
3. Mark Pass or Fail — add notes for any unexpected behavior
4. Scenarios marked Fail should be filed as issues or fed back to the spec
5. A feature passes UAT when all scenarios pass (or failures are accepted as known limitations)

**Conventions for this plan:**

- **Three kinds of scenario.** **Read and check** scenarios (6, 7, 9 to 14, 23, 25 to 27, 33 to 36) read the shipped files and run the repository's own tests in a scratch clone. **Script** scenarios (1 to 5, 8, 17 to 22, 24, 28 to 32, 37, 38) run `review-override.py` and `change-surface.py` from that clone against small fixtures in `$W`. **Live** scenarios (15, 16, 39 to 42) run `/review` or `/implement-story` in a Claude Code session inside a second clone and are judged by eye.
- **Where each scenario runs.** Read-and-check and script scenarios run in `$CL`, a clone pinned at `7b6de50`, the tree as merged. Live scenarios run in `$FX`, a second clone at `7b6de50` plus one fixture commit (tag `uat-fixture`, branch `uat-live`). The fixture adds a small `uatfx/` package, a two-story fixture spec, and a `- **Gate 0 Divergence:** off` line so live runs reach Gate 3 sooner. Keeping it out of `$CL` keeps the full suite and the generator checks clean. **Never run `install.sh` or `update.sh` in the Writ repo.** `.claude/` and `.cursor/` there are symlinks into the source; the clones keep them, so `/review` and `/implement-story` are project commands inside `$FX` with nothing installed.
- Every helper refuses to run unless the shell is inside `$W`. `$REPO` is cloned from and never written to. Run the plan in `bash` on macOS, outside any sandbox, with `claude` and `uv` on `PATH`. Claude Code asks whether to trust each new scratch folder the first time a session opens there; accept it.
- **Live scenarios.** Start `live` from a second shell: set `UAT_W=<the path the first shell printed>`, then paste the setup block, which reuses that folder and both clones. Start a new session for each run (`/exit`, then `live` again). An `/implement-story` scenario needs Gates 2.5 and 3 only: let Gates 0 to 2 run (the coding agent makes the change), and when the session moves past Gate 3 (it starts Gate 3.5, writes to the fixture's drift log, or runs `test-integrity.py`), press Escape and send the reply the scenario gives. To see what a spawned agent read, expand its entry in the transcript (ctrl+o). Each `/implement-story` run takes several minutes. Run `fxreset` after each live scenario. If a run left a worktree behind, `git -C "$FX" worktree list` shows it; `rm -rf "$W"` at the end removes it.
- Expected results come from the spec, the technical spec, the four What Was Built records, the drift log, and the tree at `7b6de50`. Story 1 landed in `35d670f`, Story 2 in `36dc9e4`, Story 3 in `6382e24`, Story 4 in `149dc40`. None of these scenarios has been run for this plan. After each scenario that edits `$CL`, run `reset` and confirm it prints nothing. When done: `rm -rf "$W"`.
- **Drift.** Two Medium items are flagged for review, and this plan expects what was built for both. **DEV-001:** `review-override.py switch` prints `on` or `off` on line 1, an exception to the agent CLI Check shape recorded in `.writ/docs/agent-cli-contract.md` (Scenarios 1 to 5, 7, 8). **DEV-012:** Gate 3's story-report line is `safety-fact: <measured> (claimed <claimed>) — <fact>`, without the State Catalog's ` — below floor`, ` — does not hold`, and ` — contradicts verdict` suffixes (Scenarios 38 to 41). Scenarios 7 and 38 each end with the decision the maintainer still owes. The Small, auto-amended items: DEV-002 (Scenario 3), DEV-003 (6), DEV-004 (12, 35), DEV-005 (7), DEV-006 and DEV-007 (10), DEV-008 (18), DEV-009 (17), DEV-010 (20), DEV-011 (19), DEV-013 and DEV-014 (31), DEV-015 to DEV-017 (29), DEV-018 (27), DEV-019 (33).
- **Known risk.** Scenarios 40 and 42 check report lines no run has printed yet. Gate 3 states `safety-fact: off` and `safety-fact: not on route` only inside the paragraph headed **Safety fact (`safety_fact` on).**, and Story 4's own run had the switch on and the risk route. A missing `safety-fact:` line in either scenario is a Fail against AC-4.5.

**Setup.** Paste this block once in the first shell. Stop if the first line does not print `W=/...`.

```bash
# First shell: paste as is. Second shell: run UAT_W=<the W path the first shell printed>, then paste.
W=${UAT_W:-$(mktemp -d "${TMPDIR:-/tmp}/writ-uat-rrr.XXXXXX")} && cd "$W" && W=$PWD && echo "W=$W"
REPO=/Users/asellke/Projects/writ            # read only: cloned from, never edited, never installed into
CL="$W/clone"; [ -d "$CL/.git" ] || { git clone -q "$REPO" "$CL" && git -C "$CL" checkout -q 7b6de50; }
OLD="$W/old"; [ -d "$OLD/scripts" ] || { mkdir -p "$OLD" && git -C "$CL" archive df3b461 scripts | tar -x -C "$OLD"; }   # scripts before Story 1
FX="$W/fx"                                   # second clone: 7b6de50 plus the live fixture
SPEC=.writ/specs/2026-10-25-review-route-rigor
FS=.writ/specs/2026-10-29-uat-review-rigor   # the fixture spec inside $FX
inW() { case "$PWD/" in "$W"/*) ;; *) echo "refusing: $PWD is outside $W" >&2; return 1;; esac; }
# pt <pytest args>: pytest on Python 3.9 inside $CL
pt() { inW && (cd "$CL" && uv run --python 3.9 pytest "$@"); }
# reset: undo every edit in $CL and drop untracked files; prints nothing when clean
reset() { inW && git -C "$CL" checkout -q -- . && git -C "$CL" clean -qfd && git -C "$CL" status --short; }
# rc <command...>: run it, keep its stdout in $W/out.txt, print its exit code and stdout size
rc() { inW || return 1; "$@" > "$W/out.txt"; local s=$?; echo "exit $s stdout-bytes $(wc -c < "$W/out.txt" | tr -d ' ')"; }

# --- switches (Story 1) ---
# swcase <case> [line ...]: $W/sw/<case>/.writ/config.md holding the given lines under ## Conventions
swcase() { inW || return 1; local d="$W/sw/$1" l; shift; rm -rf "$d" && mkdir -p "$d/.writ" || return 1
  { printf '# Writ Project Config\n\n## Conventions\n\n- **Default Branch:** main\n'; for l in "$@"; do printf '%s\n' "$l"; done; } > "$d/.writ/config.md"; }
# both <case>: resolve both switches against $W/sw/<case>, each followed by its exit code
both() { inW || return 1; local n; for n in safety-fact reviewer-filters; do python3 "$CL/scripts/review-override.py" switch --name "$n" --repo "$W/sw/$1"; echo "exit $?"; done; }

# --- blast radius (Story 3) ---
# cs <args>: change-surface.py from $CL, then its exit code
cs() { inW || return 1; python3 "$CL/scripts/change-surface.py" "$@"; echo "exit $?"; }
# brj <args>: blast-radius JSON printed one key per line, then the exit code
brj() { inW || return 1; python3 "$CL/scripts/change-surface.py" blast-radius "$@" > "$W/br.json"; local s=$?
  python3 -c 'import json, sys
d = json.load(open(sys.argv[1]))
for k in ("verdict", "consumers", "tests", "truncated", "reasons"): print("%s: %s" % (k, json.dumps(d[k])))' "$W/br.json" 2>/dev/null; echo "exit $s"; }
BR="$W/br"; if [ ! -d "$BR/.git" ]; then
  mkdir -p "$BR/lib" "$BR/app" "$BR/docs" "$BR/notes" "$BR/tests" "$BR/sub/.writ" "$BR/.writ/specs/s"
  printf 'def parse(text):\n    return text.split()\n' > "$BR/lib/parser.py"
  printf 'def clamp(n):\n    return max(0, n)\n' > "$BR/lib/utils.py"
  printf 'from lib.parser import parse\nfrom lib import utils\n' > "$BR/app/cli.py"
  printf '# formats what parser returns\n' > "$BR/app/report.py"
  printf 'Run lib/parser.py on a file. Clamp values with lib/utils.py.\n' > "$BR/docs/usage.md"
  printf 'Build with python setup.py sdist.\n' > "$BR/docs/build.md"
  printf 'parser-v2 and parsers are planned.\n' > "$BR/notes/rewrite.md"
  printf 'Run setup before the first build.\n' > "$BR/notes/install.md"
  printf 'from lib.parser import parse\n' > "$BR/tests/test_parser.py"
  printf 'from setuptools import setup\nsetup()\n' > "$BR/setup.py"
  printf 'Touches lib/parser.py.\n' > "$BR/.writ/specs/s/spec.md"
  printf 'Also touches lib/parser.py.\n' > "$BR/sub/.writ/notes.md"
  python3 -c 'import sys; open(sys.argv[1], "w").write("parser\n" + "x" * 1100000 + "\n")' "$BR/big.txt"
  printf '\377\376parser\n' > "$BR/blob.dat"
  git -C "$BR" init -q && git -C "$BR" add -A && git -C "$BR" -c user.name=uat -c user.email=uat@example.invalid commit -qm "blast-radius fixture"
fi
BRNG="$W/br-nogit"; [ -d "$BRNG" ] || { mkdir -p "$BRNG" && git -C "$BR" archive HEAD | tar -x -C "$BRNG"; }   # the same tree with no .git

# --- safety-fact verifier (Story 4) ---
SF="$W/sf"; if [ ! -d "$SF" ]; then
  mkdir -p "$SF/src" "$SF/tests" "$SF/evidence/uat/parse"
  printf 'def parse(items):\n    if not items:\n        raise ValueError("empty")\n    return items[0]\n' > "$SF/src/lib.py"
  printf 'from src.lib import parse\n\nparse([1, 2])\n' > "$SF/src/caller.py"
  printf 'x = 1\n' > "$SF/src/other.py"
  printf 'class LibTests:\n    def test_rejects_empty(self):\n        pass\n' > "$SF/tests/test_lib.py"
  printf '{"schema": "app-verify-result-v1", "verdict": "pass"}\n' > "$SF/evidence/uat/parse/result.json"
  printf 'secret = 1\nsecret = 2\n' > "$W/outside.py"
  printf '{"verdict": "pass", "consumers": {"src/lib.py": ["src/caller.py"]}, "tests": {"src/lib.py": ["tests/test_lib.py"]}, "truncated": [], "reasons": []}\n' > "$W/blast.json"
  printf '{"verdict": "pass", "consumers": {"src/lib.py": []}, "tests": {"src/lib.py": []}, "truncated": [], "reasons": []}\n' > "$W/blast-empty.json"
  printf '{"verdict": "unverifiable", "consumers": {}, "tests": {}, "truncated": [], "reasons": ["repo_unreadable"]}\n' > "$W/blast-unverifiable.json"
  printf 'not json\n' > "$W/blast-bad.json"
  printf 'command: python3 -m pytest tests/test_lib.py -v\nexit code: 0\ntests/test_lib.py::LibTests::test_rejects_empty PASSED\n1 passed in 0.01s\n' > "$W/tests-ok.txt"
  printf 'command: python3 -m pytest tests/test_lib.py -v\nexit code: 1\ntests/test_lib.py::LibTests::test_rejects_empty FAILED\n1 failed in 0.01s\n' > "$W/tests-fail.txt"
fi
BT=(--blast-radius "$W/blast.json" --tests-output "$W/tests-ok.txt")   # the standard blast radius and passing test run
# sfv <review> [flags]: the safety-fact verifier on $SF, then its exit code
sfv() { inW || return 1; python3 "$CL/scripts/review-override.py" safety-fact --review-output "$1" --repo "$SF" "${@:2}"; echo "exit $?"; }
# rv <file> <verdict|-> <holds> <rung> [evidence ...]: a review output with a Safety Fact section.
#   '-' leaves out the REVIEW_RESULT line; FACT= rv ... writes an empty Fact.
rv() { inW || return 1; local f=$1 v=$2 h=$3 r=$4 e; shift 4
  { [ "$v" = - ] || printf '### REVIEW_RESULT: %s\n\n' "$v"
    printf '### Security Assessment\n**Risk Level:** Clean\n\n### Safety Fact\n'
    printf '**Fact:** %s\n**Holds:** %s\n**Rung:** %s\n**Evidence:**\n' "${FACT-no caller passes an empty list to parse()}" "$h" "$r"
    for e in "$@"; do printf -- '- %s\n' "$e"; done
    printf '\n### Recommendations\nNone.\n'; } > "$f"; }

# --- live fixture (Stories 2 to 4, end to end) ---
if [ ! -d "$FX/.git" ]; then
  git clone -q "$REPO" "$FX" && git -C "$FX" checkout -q -b uat-live 7b6de50
  mkdir -p "$FX/uatfx/api" "$FX/uatfx/tests" "$FX/$FS/user-stories"
  touch "$FX/uatfx/__init__.py" "$FX/uatfx/api/__init__.py" "$FX/uatfx/tests/__init__.py"
  printf 'def parcel_fee(weight_kg):\n    """Flat 5.00 plus 1.50 per kilogram."""\n    return 5.00 + 1.50 * weight_kg\n' > "$FX/uatfx/api/parcel_fee.py"
  printf 'from uatfx.api.parcel_fee import parcel_fee\n\n\ndef order_total(subtotal, weight_kg):\n    return subtotal + parcel_fee(weight_kg)\n' > "$FX/uatfx/api/orders.py"
  printf 'from uatfx.api.parcel_fee import parcel_fee\n\n\ndef test_fee_for_two_kg():\n    assert parcel_fee(2) == 8.00\n' > "$FX/uatfx/tests/test_parcel_fee.py"
  printf 'from uatfx.api.orders import order_total\n\n\ndef test_total_adds_the_fee():\n    # order_total adds parcel_fee(weight_kg) to the subtotal\n    assert order_total(10.00, 2) == 18.00\n' > "$FX/uatfx/tests/test_orders.py"
  printf 'def greet(name):\n    return "Hello, " + name\n' > "$FX/uatfx/greeting.py"
  printf 'from uatfx.greeting import greet\n\n\ndef test_greet():\n    assert greet("Ada") == "Hello, Ada"\n' > "$FX/uatfx/tests/test_greeting.py"
  cat > "$FX/$FS/spec.md" <<'EOF'
# UAT Review-Route Fixture

> **Status:** In Progress
> **Created:** 2026-10-29

## Specification Contract

**Deliverable:** Two small changes to the `uatfx/` sample code. A UAT fixture for the review-route rigor spec; it is never merged.
EOF
  cat > "$FX/$FS/spec-lite.md" <<'EOF'
# UAT Review-Route Fixture (Lite)

## For Coding Agents

**Deliverable:** A negative-weight guard in `uatfx/api/parcel_fee.py` and a trimmed name in `uatfx/greeting.py`, each with its test.

## For Review Agents

**Acceptance:** each story's criteria, and no change outside the files its tasks name.

## For Testing Agents

**Tests:** `uv run --python 3.9 pytest uatfx/tests -v`
EOF
  cat > "$FX/$FS/user-stories/story-1-reject-negative-weight.md" <<'EOF'
# Story 1: Reject a Negative Weight

> **Status:** Not Started
> **Priority:** High
> **Dependencies:** None

## User Story

**As a** checkout caller
**I want to** get an error for a negative parcel weight
**So that** an order total never drops below its subtotal

## Acceptance Criteria

- [ ] Given a weight below zero, when `parcel_fee` is called, then it raises `ValueError` `[AC-1.1]`
- [ ] Given a weight of zero or more, when `parcel_fee` is called, then it returns 5.00 plus 1.50 per kilogram, as before `[AC-1.2]`

## Implementation Tasks

- [ ] 1.1 Add failing tests to `uatfx/tests/test_parcel_fee.py` `[AC-1.1, AC-1.2]`
- [ ] 1.2 Raise `ValueError` for a negative weight in `uatfx/api/parcel_fee.py` `[AC-1.1, AC-1.2]`

## Notes

- Change only `uatfx/api/parcel_fee.py` and `uatfx/tests/test_parcel_fee.py`.
- Run the story's tests with `uv run --python 3.9 pytest uatfx/tests/test_parcel_fee.py uatfx/tests/test_orders.py -v`.
EOF
  cat > "$FX/$FS/user-stories/story-2-trim-greeting-name.md" <<'EOF'
# Story 2: Trim the Greeting Name

> **Status:** Not Started
> **Priority:** Low
> **Dependencies:** None

## User Story

**As a** caller of `greet`
**I want to** get a greeting without stray spaces around the name
**So that** a padded name never reaches a user

## Acceptance Criteria

- [ ] Given a name with spaces around it, when `greet` is called, then the greeting uses the name without those spaces `[AC-2.1]`

## Implementation Tasks

- [ ] 2.1 Add a failing test to `uatfx/tests/test_greeting.py` `[AC-2.1]`
- [ ] 2.2 Strip the name in `uatfx/greeting.py` `[AC-2.1]`

## Notes

- Change only `uatfx/greeting.py` and `uatfx/tests/test_greeting.py`.
- Run the story's tests with `uv run --python 3.9 pytest uatfx/tests/test_greeting.py -v`.
EOF
  python3 -c 'import sys; p = sys.argv[1]; t = open(p).read(); open(p, "w").write(t.replace("## Conventions\n\n", "## Conventions\n\n- **Gate 0 Divergence:** off\n", 1))' "$FX/.writ/config.md"
  git -C "$FX" add -A && git -C "$FX" -c user.name=uat -c user.email=uat@example.invalid commit -qm "uat: review-route rigor live fixture" && git -C "$FX" tag uat-fixture
fi
# live: Claude Code inside $FX
live() { inW && (cd "$FX" && claude); }
# fsw <safety-fact value|-> <reviewer-filters value|->: set the two switch lines in $FX's config ('-' leaves a line out)
fsw() { inW && python3 -c 'import sys
p, sf, rf = sys.argv[1:4]
keep = [l for l in open(p).read().split("\n") if not l.startswith(("- **Safety Fact:**", "- **Reviewer Filters:**"))]
at = keep.index("## Conventions") + 2
keep[at:at] = ["- **%s:** %s" % (k, v) for k, v in (("Safety Fact", sf), ("Reviewer Filters", rf)) if v != "-"]
open(p, "w").write("\n".join(keep))' "$FX/.writ/config.md" "$1" "$2" && grep -n 'Safety Fact\|Reviewer Filters\|Gate 0 Divergence' "$FX/.writ/config.md"; }
# rvb: branch uat-review in $FX with one commit on the fixture that rejects a negative weight
rvb() { inW && git -C "$FX" checkout -q -B uat-review uat-fixture \
  && printf 'def parcel_fee(weight_kg):\n    """Flat 5.00 plus 1.50 per kilogram."""\n    if weight_kg < 0:\n        raise ValueError("weight_kg must not be negative")\n    return 5.00 + 1.50 * weight_kg\n' > "$FX/uatfx/api/parcel_fee.py" \
  && git -C "$FX" -c user.name=uat -c user.email=uat@example.invalid commit -qam "uat: reject a negative weight" && git -C "$FX" log -1 --format=%s; }
# fxreset: $FX back on uat-live at the fixture commit; drops edits, untracked files, and Gate state; prints nothing when clean
fxreset() { inW && git -C "$FX" checkout -q -f uat-live && git -C "$FX" reset -q --hard uat-fixture && git -C "$FX" clean -qfd \
  && rm -f "$FX"/.writ/state/blast-radius-story-* "$FX"/.writ/state/gate3-*-story-* "$FX"/.writ/state/boundary-story-* "$FX"/.writ/state/review-uat-* \
  && git -C "$FX" status --short; }
echo "setup done: clone at $(git -C "$CL" rev-parse --short HEAD); fixture $(git -C "$FX" describe --tags --exact-match uat-live 2>/dev/null) on $(git -C "$FX" branch --show-current); fixture tests: $(cd "$FX" && uv run --python 3.9 pytest uatfx/tests -q 2>&1 | tail -1 | cut -d' ' -f1-2)"
```

The last line should read `setup done: clone at 7b6de50; fixture uat-fixture on uat-live; fixture tests: 3 passed`.

The live fixture is built so Gate 2.5 gives a known route. Story 1 changes `uatfx/api/parcel_fee.py`; the `api` folder makes the surface `full-stack`, so `crossings` routes `review-agent` with reason `full_stack_surface`. Its one caller, `uatfx/api/orders.py`, and a test that names it, `uatfx/tests/test_orders.py`, sit outside the change, so the blast radius has one consumer and one test. Story 2 changes two listed files outside any shared or full-stack folder, so it routes `evaluator-agent`. The script fixtures: `$BR` is a small git repo for blast-radius (`$BRNG` is the same tree with no `.git`), and `$SF` is a small repo for the safety-fact verifier with a library, one caller, one unrelated file, a test, and a passing `app-verify-result-v1` file. `$W/outside.py` sits next to `$SF`, not inside it.

## Coverage Summary

| Story | Status | Scenarios | Source Breakdown |
|-------|--------|-----------|-----------------|
| Story 1: Upgrade switches | ✅ Covered | 8 | AC: 7, Errors: 1, Shadow: 0, Edge: 0, Experience: 0 |
| Story 2: Reviewer lead-judgment filters | ✅ Covered | 8 | AC: 8, Errors: 0, Shadow: 0, Edge: 0, Experience: 0 |
| Story 3: Blast radius at Gate 2.5 | ✅ Covered | 8 | AC: 7, Errors: 1, Shadow: 0, Edge: 0, Experience: 0 |
| Story 4: Safety fact at Gate 3 | ✅ Covered | 18 | AC: 12, Errors: 1, Shadow: 0, Edge: 0, Experience: 5 |

- **Switch states.** Each switch is covered in each state, by the resolver and end to end:

  | Switch | Absent | `on` | `off` | Malformed |
  |---|---|---|---|---|
  | `Safety Fact` | 2, 8, 39 | 3, 42 | 1, 40 | 4, 41 |
  | `Reviewer Filters` | 2, 8, 15, 39 | 3, 42 | 1, 16, 40 | 4, 15, 41 |

  Scenario 42 runs `Safety Fact: on` on the evaluator route, where Gate 2.5 never resolves it; that is the business rule that the safety fact applies only on the `review-agent` route.
- Folded rows. Error Map: "`switch` parses value" is Scenarios 4 and 41; "`blast-radius` reads a candidate" is 17 and 20; "`git ls-files` fails" is 20; "`safety-fact` reads review output" is 32; "resolves a cited path" is 29; "Reviewer omits the section twice" and "cannot reach `traced` twice" are checked in the Gate 3 text (33) and the verifier's reasons (31). Shadow Paths: "Switch resolution" happy 1, nil 2, empty 3, upstream error 8; "Blast radius" happy 17, nil 21, empty 21, upstream error 20 and 21; "Safety-fact verify" happy 28, nil 32, empty 28 (Step 1), upstream error 32; "Gate 3 routing" happy 39, upstream error 33 (text only).
- Experience Design: entry point and happy path 39; moment of truth and feedback model 39 (report lines, claim beside measurement), 15 and 16 (`/review` header); error experience 33 (text) and 41. State Catalog: evaluator route 42; fact at or above floor 32 and 39; `Holds: no` with FAIL 32; `Holds: no` with PASS 31; section missing after one re-review 31 and 33; below floor after one re-review 33 and 38; `safety-fact` switch off 40; `reviewer-filters` switch off 16 and 40; verifier cannot read the review output 32 and 38; blast radius unverifiable 21 and 37; config line with a bad value 4 and 41.
- The technical spec has no Interaction Edge Cases section, so there are no edge-case scenarios.
- No live scenario for a re-review that ends in BLOCKED or a recode, a contradiction recode, a verifier crash, panel reviewers, `--full-pipeline`, the two-fail escalation route, or the `reproduced` rung at Gate 3: none can be produced reliably from a fixture. Scenarios 28 to 33 and 37 check the verifier and the Gate 3 text that route them.
- One gap the drift log does not record: the Error Map's first row says a missing config shows `on` with `reason: no_config` "in the story report". Gate 3 prints only `reviewer-filters: <on|off>` and the `safety-fact:` line, so the reason reaches the transcript (the switch command's output) but not the report. Scenario 8 checks the resolver only.
- No pending stories: all four are Completed ✅.

---

## Story 1: Upgrade switches

### Scenario 1: `off` turns each switch off in any letter case and with padding, and the first matching line wins

**Source:** Acceptance Criteria (AC-1.1) — Story 1; Shadow Path "Switch resolution" (happy path); Business Rule "Switch resolution" (first match wins); DEV-001
**Feature:** none
**Verification:** human — no recipe

**Preconditions:**
- Setup block pasted.

**Steps:**
1. `swcase off '- **Safety Fact:** off' '- **Reviewer Filters:** off'; both off`
2. `swcase mixed '- **Safety Fact:** OFF' '- **Reviewer Filters:**    oFf   '; both mixed`
3. `swcase first '- **Safety Fact:** off' '- **Safety Fact:** on' '- **Reviewer Filters:** on' '- **Reviewer Filters:** off'; both first`
4. `pt scripts/tests/test_review_override.py -q -k "SwitchSubcommandTests and (off or first_match)" 2>&1 | tail -1`

**Expected Result:**
- Step 1: for each switch, four lines: `off`, `reason: config_off`, `review-override switch: safety-fact off (.writ/config.md)` (`reviewer-filters` for the second), `exit 0`. Line 1 is the state word, not `pass` (DEV-001).
- Step 2: the same as Step 1. Letter case and surrounding spaces do not matter.
- Step 3: `safety-fact` prints `off` and `reason: config_off`; `reviewer-filters` prints `on`, `reason: config_on`, and `review-override switch: reviewer-filters on (.writ/config.md)`. Both exit 0: the first matching line decides.
- Step 4: `4 passed` (with a deselected count).

**Implementation Reference:** Story 1 — Files: `scripts/review-override.py` (`switch`, `SWITCH_LINES`), `scripts/tests/test_review_override.py` (`SwitchSubcommandTests`)

**Status:** [ ] Pass  [ ] Fail

**Notes:**

---

### Scenario 2: With no config file, or no line for the switch, each switch reads as on and says why

**Source:** Acceptance Criteria (AC-1.2) — Story 1; Shadow Path "Switch resolution" (nil input); Error Map "`switch` reads `.writ/config.md`" (file absent)
**Feature:** none
**Verification:** human — no recipe

**Preconditions:**
- Setup block pasted.

**Steps:**
1. `mkdir -p "$W/sw/none"; ls -A "$W/sw/none" | wc -l; both none`
2. `swcase noline; both noline`
3. `swcase onlyone '- **Safety Fact:** off'; both onlyone`
4. `pt scripts/tests/test_review_override.py -q -k "SwitchSubcommandTests and (no_config_file or without_line or other_switch)" 2>&1 | tail -1`

**Expected Result:**
- Step 1: `0` (no `.writ/` folder), then for each switch: `on`, `reason: no_config`, `review-override switch: <name> on (.writ/config.md)`, `exit 0`.
- Step 2: for each switch: `on`, `reason: no_config_line`, the summary, `exit 0`.
- Step 3: `safety-fact` prints `off` and `reason: config_off`; `reviewer-filters` prints `on` and `reason: no_config_line`. One switch's line does not count for the other.
- Step 4: `3 passed`.

**Implementation Reference:** Story 1 — Files: `scripts/review-override.py` (`_resolve_switch`)

**Status:** [ ] Pass  [ ] Fail

**Notes:**

---

### Scenario 3: `on`, `ON`, or an empty value reads as on with `config_on`

**Source:** Acceptance Criteria (AC-1.2) — Story 1; Shadow Path "Switch resolution" (empty input); DEV-002
**Feature:** none
**Verification:** human — no recipe

**Preconditions:**
- Setup block pasted.

**Steps:**
1. `swcase on '- **Safety Fact:** on' '- **Reviewer Filters:** ON'; both on`
2. `swcase empty '- **Safety Fact:**' '- **Reviewer Filters:**   '; both empty`
3. `pt scripts/tests/test_review_override.py -q -k "SwitchSubcommandTests and (value_on or empty_value)" 2>&1 | tail -1`

**Expected Result:**
- Step 1: for each switch: `on`, `reason: config_on`, `review-override switch: <name> on (.writ/config.md)`, `exit 0`. `ON` resolves as `config_on`, not `malformed_value ON` (DEV-002).
- Step 2: the same four lines for each switch: an empty value is on.
- Step 3: `2 passed`.

**Implementation Reference:** Story 1 — WWB decision 2 (`on` in any case is `config_on`)

**Status:** [ ] Pass  [ ] Fail

**Notes:**

---

### Scenario 4: A malformed value reads as on and names the value; the key's case must match

**Source:** Acceptance Criteria (AC-1.3) — Story 1; Error Map "`switch` parses value"; State Catalog "Config line with a bad value"
**Feature:** none
**Verification:** human — no recipe

**Preconditions:**
- Setup block pasted.

**Steps:**
1. `swcase typo '- **Safety Fact:** of' '- **Reviewer Filters:** of'; both typo`
2. `swcase words '- **Safety Fact:** false' '- **Reviewer Filters:** off  # trial arm B'; both words`
3. `swcase keycase '- **safety fact:** off' '- **Reviewer filters:** off'; both keycase`
4. `pt scripts/tests/test_review_override.py -q -k "SwitchSubcommandTests and malformed" 2>&1 | tail -1`

**Expected Result:**
- Step 1: for each switch: `on`, `reason: malformed_value of`, `review-override switch: <name> on (.writ/config.md)`, `exit 0`. A trial operator who meant `off` sees the arm did not switch.
- Step 2: `safety-fact` prints `on` and `reason: malformed_value false`; `reviewer-filters` prints `on` and `reason: malformed_value off  # trial arm B`. A trailing comment makes the value malformed: only `off` itself turns a switch off.
- Step 3: both print `on` and `reason: no_config_line`. A key in another case is not the switch's line.
- Step 4: `2 passed`.

**Implementation Reference:** Story 1 — WWB decision 3 (key match stays case-sensitive)

**Status:** [ ] Pass  [ ] Fail

**Notes:**

---

### Scenario 5: An unknown or missing `--name` is a usage error, and `check` prints what it printed before Story 1

**Source:** Acceptance Criteria (AC-1.4) — Story 1; Business Rule "Switch resolution" (unknown `--name` is exit 2)
**Feature:** none
**Verification:** human — no recipe

**Preconditions:**
- Setup block pasted. `ls "$OLD/scripts/review-override.py"` lists the file.

**Steps:**
1. `rc python3 "$CL/scripts/review-override.py" switch --name safety_fact`
2. `rc python3 "$CL/scripts/review-override.py" switch`
3. `(cd "$CL" && for s in "$OLD" "$CL"; do for a in "" "--spec $SPEC --repo ." "--spec $SPEC --repo . --story $SPEC/user-stories/story-1-upgrade-switches.md" "--name safety-fact"; do python3 "$s/scripts/review-override.py" check $a 2>/dev/null; echo "exit $?"; done > "$W/check-${s##*/}.txt"; done); diff "$W/check-old.txt" "$W/check-clone.txt" && echo identical`
4. `cat "$W/check-clone.txt"`
5. `pt scripts/tests/test_review_override.py -q -k "(SwitchSubcommandTests and usage_error) or CheckUnchangedBySwitchTests" 2>&1 | tail -1`

**Expected Result:**
- Step 1: a usage line and an `invalid choice` error naming `reviewer-filters` and `safety-fact` on stderr, then `exit 2 stdout-bytes 0`.
- Step 2: a usage line and an error that `--name` is required on stderr, then `exit 2 stdout-bytes 0`.
- Step 3: `identical`. The script from before Story 1 (`df3b461`) and the merged one print the same `check` output and exit codes.
- Step 4: `unverifiable`, `reason: missing_spec`, `review-override: unverifiable (missing --spec)`, `exit 0`; then `unverifiable`, `reason: missing_story`, `review-override: unverifiable (missing --story)`, `exit 0`; then the Story 1 run's verdict line and `review-override:` summary with its exit code; then `exit 2` alone (`check` refuses `--name` with stdout empty).
- Step 5: `6 passed`.

**Implementation Reference:** Story 1 — Files: `scripts/review-override.py` (`build_parser`, `main`); `scripts/tests/test_review_override.py` (`CheckUnchangedBySwitchTests`)

**Status:** [ ] Pass  [ ] Fail

**Notes:**

---

### Scenario 6: `config-format.md` documents both switches, the script documents `switch`, and the plugin copy matches

**Source:** Acceptance Criteria (AC-1.1 to AC-1.3, through task 1.4) — Story 1; DEV-003
**Feature:** none
**Verification:** human — no recipe

**Preconditions:**
- Setup block pasted; `reset` prints nothing. Run outside any sandbox.

**Steps:**
1. `grep -n '^| .Safety Fact.\|^| .Reviewer Filters.' "$CL/.writ/docs/config-format.md"`
2. `sed -n '/^## Safety Fact$/,/^## Rules$/p' "$CL/.writ/docs/config-format.md"`
3. `sed -n '22,33p' "$CL/scripts/review-override.py"`
4. `cmp "$CL/scripts/review-override.py" "$CL/plugins/writ/scripts/review-override.py" && echo same`
5. `pt scripts/tests/test_review_override.py -q -k "SwitchSubcommandTests or CheckUnchangedBySwitchTests" 2>&1 | tail -1`
6. `(cd "$CL" && bash scripts/eval.sh --check=review-override >/dev/null; echo "exit $?"); tail -2 "$(ls -t "$CL"/.writ/state/eval-*.md | head -1)"`

**Expected Result:**
- Step 1: two Supported Keys rows. `Safety Fact`: implement-story (Gate 2.5, Gate 3), on by default, `off` turns off the blast radius and the safety-fact section. `Reviewer Filters`: implement-story (Gate 3) and review, on by default, `off` turns off the reviewer lead-judgment filters.
- Step 2: a `## Safety Fact` and a `## Reviewer Filters` section, each with its one-line example (`- **Safety Fact:** off`, `- **Reviewer Filters:** off`). Each states: no line, an empty value, or `on` means on; only `off` in any case turns it off; any other value means on with `reason: malformed_value <value>`; the key must match the case shown; and the `review-override.py switch --name … --repo .` command. The Safety Fact section also says surrounding whitespace is ignored and the first matching line wins.
- Step 3: the module docstring for `switch`: both config lines, first match wins, on by default, line 1 the state word, every reason (`no_config`, `no_config_line`, `config_off`, `config_on`, `malformed_value <value>`), and exit 0 except 2 for a usage error.
- Step 4: `same`. `scripts/` is mirrored into `plugins/writ/scripts/`, so the script edit regenerated the plugin copy (DEV-003).
- Step 5: `19 passed`.
- Step 6: `exit 0`, then `- Findings: 0` and `- Run errors: 0`.

**Implementation Reference:** Story 1 — Files: `.writ/docs/config-format.md`, `scripts/review-override.py` (docstring), `plugins/writ/scripts/review-override.py` (generated)

**Status:** [ ] Pass  [ ] Fail

**Notes:**

---

### Scenario 7: The agent CLI contract records `switch` as the one exception to the Check shape (DEV-001)

**Source:** Acceptance Criteria (AC-1.1 to AC-1.3) — Story 1; DEV-001 (Medium, flagged for review); DEV-005
**Feature:** none
**Verification:** human — no recipe

**Preconditions:**
- Setup block pasted; `reset` prints nothing.

**Steps:**
1. `sed -n '/^## Check shape/,/^## Usage errors/p' "$CL/.writ/docs/agent-cli-contract.md"`
2. `grep -n '^| .review-override.py.\|^- .review-override.py.' "$CL/.writ/docs/agent-cli-contract.md"`
3. `grep -c 'Smoke("review-override.py"' "$CL/scripts/tests/test_agent_cli_contract.py"; grep -c '"switch"' "$CL/scripts/tests/test_agent_cli_contract.py"`
4. `grep -n 'switch --name' "$CL/commands/implement-story.md" "$CL/commands/review.md" | cut -c1-160`
5. `pt scripts/tests/test_agent_cli_contract.py -q 2>&1 | tail -1`

**Expected Result:**
- Step 1: the rule that line 1 of stdout is exactly `pass`, `fail`, or `unverifiable`, and that every subcommand and mode of a check tool prints in this shape.
- Step 2: the table row `review-override.py | check | | commands/implement-story.md, commands/review.md` (DEV-005 added `commands/review.md`), and a Notes bullet: `switch` prints a state word, `on` or `off`, on line 1 instead of a verdict, then one `reason:` line, then the summary; it always exits 0 except 2 for a usage error; this is a documented exception to the Check shape.
- Step 3: `1`, then `0`. The contract test smoke-runs `check` only; no row runs `switch`.
- Step 4: three callers branch on line 1: Gate 2.5 (`switch --name safety-fact`, "On `on`"), Gate 3 (`switch --name reviewer-filters`, "pass line 1"), and `/review` Step 3 ("keep line 1").
- Step 5: no `failed` in the summary.
- **Decision owed (DEV-001).** Keeping the exception needs nothing. Making the contract uniform (line 1 `pass`, the state in a `reason:` line, as `review-panel.py status` does) needs a later spec that changes the three callers in Step 4 together. Record the decision in Notes.

**Implementation Reference:** Story 1 — Files: `.writ/docs/agent-cli-contract.md` (Notes); Story 2 — same file (Callers cell)

**Status:** [ ] Pass  [ ] Fail

**Notes:**

---

### Scenario 8: An unreadable config reads as on with `no_config`

**Source:** Error Map "`switch` reads `.writ/config.md`" (file unreadable) — Story 1; Shadow Path "Switch resolution" (upstream error)
**Feature:** none
**Verification:** human — no recipe

**Preconditions:**
- Setup block pasted.

**Steps:**
1. `rm -rf "$W/sw/dir"; mkdir -p "$W/sw/dir/.writ/config.md"; both dir`
2. `rm -rf "$W/sw/latin1"; mkdir -p "$W/sw/latin1/.writ"; printf '\377\376- **Safety Fact:** off\n- **Reviewer Filters:** off\n' > "$W/sw/latin1/.writ/config.md"; both latin1`
3. `pt scripts/tests/test_review_override.py -q -k "SwitchSubcommandTests and unreadable" 2>&1 | tail -1`

**Expected Result:**
- Step 1: `.writ/config.md` is a folder. For each switch: `on`, `reason: no_config`, `review-override switch: <name> on (.writ/config.md)`, `exit 0`. No traceback.
- Step 2: the file is not valid UTF-8, so its `off` lines are not read. For each switch: `on`, `reason: no_config`, the summary, `exit 0`.
- Step 3: `1 passed`.

**Implementation Reference:** Story 1 — WWB (`_resolve_switch` never raises on a bad config)

**Status:** [ ] Pass  [ ] Fail

**Notes:**

---

## Story 2: Reviewer lead-judgment filters

### Scenario 9: The filters skill states three filters, applies filter 3 before filter 2, and lints `pass`

**Source:** Acceptance Criteria (AC-2.1) — Story 2; Business Rules "Filters" 1 to 3
**Feature:** none
**Verification:** human — no recipe

**Preconditions:**
- Setup block pasted; `reset` prints nothing.

**Steps:**
1. `sed -n '1,7p' "$CL/skills/review-judgment-filters/SKILL.md"`
2. `grep -n '^## \|^### ' "$CL/skills/review-judgment-filters/SKILL.md"`
3. `sed -n '/^## How to Apply/,/^### Severity mapping/p' "$CL/skills/review-judgment-filters/SKILL.md"`
4. `grep -c '^Example:' "$CL/skills/review-judgment-filters/SKILL.md"`
5. `sed -n '/^### Severity mapping/,$p' "$CL/skills/review-judgment-filters/SKILL.md"`
6. `(cd "$CL" && bash scripts/lint-skill.sh skills/review-judgment-filters/SKILL.md; echo "exit $?")`
7. `pt scripts/tests/test_review_route_rigor.py -q -k "SkillFrontmatterTest or SkillLintTest or SkillBodyTest" 2>&1 | tail -1`

**Expected Result:**
- Step 1: `---`, `name: review-judgment-filters`, `description: "Separate findings that change a verdict from nits and untraced hypotheticals, without dismissing security findings."`, `disable-model-invocation: true`, `status: candidate`, `status_evidence: "Phase 15 (2026-10-25). 3 consumers: agents/review-agent.md, agents/evaluator-agent.md, commands/review.md."`, `---`.
- Step 2: `## Purpose`, `## When to Use`, `## How to Apply`, `### Filter 1: All nits means the code is fine`, `### Filter 2: Trace the call site before accepting a hypothetical`, `### Filter 3: Be slow to dismiss security findings`, and the `/review` severity mapping heading, in that order.
- Step 3: How to Apply checks each finding security first (filter 3), then nits (filter 1), then hypotheticals (filter 2), and says filter 3 is applied before filter 2 so the hypothetical rule never drops a security finding. Filter 1: if every finding is a nit, the verdict is PASS, the nits go under recommendations, and a nit's severity is never raised to justify a FAIL. Filter 2: a hypothetical stands only when the reviewer cites a caller, `path:line`, that can produce it; input that crosses a trust boundary can produce any value; otherwise the finding is dropped or moved to recommendations. Filter 3: filter 2 does not apply to security; a security finding is dismissed only by citing the guard, `path:line`, and otherwise stays at Major or above.
- Step 4: `3`, one example per filter.
- Step 5: a nit is Low; "Major or above" is High or above; PASS is the ready-to-ship recommendation; a moved finding stays in the `/review` registry as Low and never goes into the Recommendation; `evaluator-agent` lists moved findings under Residual as taste.
- Step 6: `pass`, `reason: ✅ skills/review-judgment-filters/SKILL.md: clean`, `lint-skill: pass (1 file(s) clean)`, `exit 0`.
- Step 7: `12 passed`.

**Implementation Reference:** Story 2 — Files: `skills/review-judgment-filters/SKILL.md`; WWB decisions 2 and 3

**Status:** [ ] Pass  [ ] Fail

**Notes:**

---

### Scenario 10: The filters skill is registered in the manifest, README, and root catalog, and a hand edit to a generated copy is caught

**Source:** Acceptance Criteria (AC-2.1, through task 2.2) — Story 2; DEV-006, DEV-007
**Feature:** none
**Verification:** human — no recipe

**Preconditions:**
- Setup block pasted; `reset` prints nothing.

**Steps:**
1. `awk '/^skills:/{s=1;next} s && /^[a-z]/{s=0} s && /^  - name:/{print $3}' "$CL/.writ/manifest.yaml" > "$W/skills.txt"; grep -n -B1 -A1 '^review-judgment-filters$' "$W/skills.txt"; sort -c "$W/skills.txt" && echo sorted; wc -l < "$W/skills.txt"`
2. `grep -n -A4 '  - name: review-judgment-filters$' "$CL/.writ/manifest.yaml"`
3. `grep -n 'skills are live\|skills/review-judgment-filters/SKILL.md' "$CL/README.md" | cut -c1-120`
4. `grep -n 'skills/review-judgment-filters/SKILL.md' "$CL/SKILL.md"`
5. `(cd "$CL" && bash scripts/gen-skill.sh --check 2>/dev/null | head -1; python3 scripts/gen-platform-trees.py --check | head -2)`
6. `echo "hand edit" >> "$CL/plugins/writ/skills/review-judgment-filters/SKILL.md"; (cd "$CL" && python3 scripts/gen-platform-trees.py --check | head -2); reset`
7. `pt scripts/tests/test_review_route_rigor.py -q -k "SkillRegistrationTest and not Blast" 2>&1 | tail -1`

**Expected Result:**
- Step 1: `11-project-context-snapshot`, `12:review-judgment-filters`, `13-safe-refactor-loop`; `sorted`; `19`. The entry sits in alphabetical order (DEV-007).
- Step 2: `file: skills/review-judgment-filters/SKILL.md`, the same description as the skill, `status: candidate`, `tags: [review, judgment, security]`.
- Step 3: line 46 says `19 skills are live today` (DEV-006: Story 2 corrected a stale 16 to 18; Story 4 made it 19), and line 206 is the skill's row.
- Step 4: one row: `review-judgment-filters`, `candidate`, `skills/review-judgment-filters/SKILL.md`, and the description.
- Step 5: `pass` (gen-skill), then `pass` and `gen-platform-trees: pass (0 stale, 0 missing, 0 orphan, 0 unmapped, 0 vendor)`.
- Step 6: `fail`, then `reason: stale plugins/writ/skills/review-judgment-filters/SKILL.md`. `reset` prints nothing.
- Step 7: `4 passed`.

**Implementation Reference:** Story 2 — Files: `.writ/manifest.yaml`, `README.md`, `SKILL.md`, `plugins/writ/skills/review-judgment-filters/SKILL.md` and `cursor/plugin/skills/review-judgment-filters/SKILL.md` (generated)

**Status:** [ ] Pass  [ ] Fail

**Notes:**

---

### Scenario 11: Both reviewer agents take `reviewer_filters` and read the skill only when it is `on`

**Source:** Acceptance Criteria (AC-2.2) — Story 2; Must Include 6 (agent bodies carry only a conditional `Read` line and an input row)
**Feature:** none
**Verification:** human — no recipe

**Preconditions:**
- Setup block pasted; `reset` prints nothing.

**Steps:**
1. `grep -n 'reviewer_filters' "$CL/agents/review-agent.md" "$CL/agents/evaluator-agent.md" | cut -c1-200`
2. `grep -rn 'review-judgment-filters' "$CL/agents/"`
3. `grep -n '^## Output Format' "$CL/agents/review-agent.md" "$CL/agents/evaluator-agent.md"`
4. `grep -n 'review-judgment-filters' "$CL/claude-code/agents/writ-reviewer.md" "$CL/claude-code/agents/writ-evaluator.md"`
5. `pt scripts/tests/test_review_route_rigor.py -q -k AgentWiringTest 2>&1 | tail -1`

**Expected Result:**
- Step 1: `review-agent.md:48` and `evaluator-agent.md:42` are input rows (`reviewer_filters`: `on` or `off`, resolved by Gate 3 from the `reviewer-filters` switch); `review-agent.md:196` and `evaluator-agent.md:89` are the conditional lines.
- Step 2: exactly two lines. `review-agent.md:196` reads "When `{reviewer_filters}` is `on`, `Read skills/review-judgment-filters/SKILL.md` and apply it before you set REVIEW_RESULT." `evaluator-agent.md:89` reads the same with EVALUATION_RESULT. Neither body carries filter wording.
- Step 3: `review-agent.md:200` and `evaluator-agent.md:91`: each conditional line sits above `## Output Format`.
- Step 4: `writ-reviewer.md:209` and `writ-evaluator.md:102` carry the same lines in the generated Claude Code agents.
- Step 5: `4 passed`.

**Implementation Reference:** Story 2 — Files: `agents/review-agent.md`, `agents/evaluator-agent.md`, `claude-code/agents/writ-reviewer.md` and `writ-evaluator.md` (generated)

**Status:** [ ] Pass  [ ] Fail

**Notes:**

---

### Scenario 12: Gate 3 resolves the filters switch once per story, passes it to every spawn, and prints `reviewer-filters:`

**Source:** Acceptance Criteria (AC-2.2, AC-2.3; text half) — Story 2; DEV-004
**Feature:** none
**Verification:** human — no recipe

**Preconditions:**
- Setup block pasted; `reset` prints nothing.

**Steps:**
1. `sed -n '/^#### Gate 3: Review Agent/,/^#### Gate 3.5/p' "$CL/commands/implement-story.md" | grep '^\*\*Reviewer filters'`
2. `grep -c 'switch --name reviewer-filters' "$CL/commands/implement-story.md"; grep -c 'review-judgment-filters' "$CL/commands/implement-story.md"`
3. `sed -n '/^### Step 4: Story Completion/,/^## Error Handling/p' "$CL/commands/implement-story.md" | grep -c 'reviewer'`
4. `for c in 36dc9e4^ 36dc9e4; do git -C "$CL" show "${c}:commands/implement-story.md" | wc -c; done`
5. `pt scripts/tests/test_review_route_rigor.py -q -k Gate3WiringTest 2>&1 | tail -1`

**Expected Result:**
- Step 1: one paragraph: **Reviewer filters.** Once per story, run `python3 scripts/review-override.py switch --name reviewer-filters` and pass line 1 as `reviewer_filters` to every Gate 3 spawn: the evaluator or `review-agent`, panel reviewers, and any re-review. The story report prints `reviewer-filters: <on|off>`.
- Step 2: `1`, then `0`. Gate 3 resolves the switch once and never reads the skill itself; the agents do.
- Step 3: `0`. Step 4's report-line list is unchanged; Gate 3 states the new line.
- Step 4: `38434`, then `38729` (+295, within the 1,800-byte allowance; DEV-004 moved the governor pin by the same amount).
- Step 5: `4 passed`.
- The live half of AC-2.2 and AC-2.3 is Scenarios 39 to 42.

**Implementation Reference:** Story 2 — Files: `commands/implement-story.md` (`#### Gate 3`); WWB decision 1 (the orchestrator resolves the switch and passes it as an input)

**Status:** [ ] Pass  [ ] Fail

**Notes:**

---

### Scenario 13: `/review` resolves the switch in Step 3 and records it in the report header

**Source:** Acceptance Criteria (AC-2.4; text half) — Story 2
**Feature:** none
**Verification:** human — no recipe

**Preconditions:**
- Setup block pasted; `reset` prints nothing.

**Steps:**
1. `sed -n '/^### Step 3: Apply Review Techniques/,/^#### Technique 1/p' "$CL/commands/review.md"`
2. `sed -n '/^### Step 4: Produce Report/,/^## Architecture/p' "$CL/commands/review.md"`
3. `grep -c 'review-judgment-filters' "$CL/commands/review.md"`
4. `pt scripts/tests/test_review_route_rigor.py -q -k ReviewCommandWiringTest 2>&1 | tail -1`

**Expected Result:**
- Step 1: Step 3 opens by running `python3 scripts/review-override.py switch --name reviewer-filters` and keeping line 1 (`on` or `off`) for the Step 4 header. On `on`, it reads `skills/review-judgment-filters/SKILL.md` and applies it before Technique 4 assigns severities and before the Recommendation. No filter wording.
- Step 2: the report template header: `# Code Review: [branch-name]`, `> Reviewed:`, `> Scope:`, `> Spec:`, `> Reviewer filters: on|off`.
- Step 3: `1`.
- Step 4: `3 passed`.
- The live half is Scenarios 15 and 16.

**Implementation Reference:** Story 2 — Files: `commands/review.md` (Step 3, Step 4)

**Status:** [ ] Pass  [ ] Fail

**Notes:**

---

### Scenario 14: Filter text lives only in the skill, and a filter sentence pasted into an agent body fails the test

**Source:** Acceptance Criteria (AC-2.5) — Story 2; Hardest Constraint (the off arm carries none of the upgrade's text)
**Feature:** none
**Verification:** human — no recipe

**Preconditions:**
- Setup block pasted; `reset` prints nothing.

**Steps:**
1. `(cd "$CL" && grep -rli 'be slow to dismiss security findings\|trace the call site before accepting a hypothetical\|all nits means the code is fine' --include='*.md' --include='*.toml' --include='*.template' --exclude-dir=.writ --exclude-dir=.git --exclude-dir=.venv .)`
2. `pt scripts/tests/test_review_route_rigor.py -q -k FilterTextIsolationTest 2>&1 | tail -1`
3. `echo 'Be slow to dismiss security findings.' >> "$CL/agents/evaluator-agent.md"; pt scripts/tests/test_review_route_rigor.py -q -k "FilterTextIsolationTest and absent" 2>&1 | grep -E 'evaluator-agent.md: be slow|failed|passed'; reset`
4. `(cd "$CL" && python3 scripts/gen-platform-trees.py --check | head -1)`

**Expected Result:**
- Step 1: exactly three paths, in any order: `skills/review-judgment-filters/SKILL.md`, `plugins/writ/skills/review-judgment-filters/SKILL.md`, `cursor/plugin/skills/review-judgment-filters/SKILL.md`. No agent, command, generated native agent, or Codex file.
- Step 2: `2 passed`.
- Step 3: a line naming `agents/evaluator-agent.md: be slow to dismiss security findings`, then `1 failed` (with a deselected count). `reset` prints nothing.
- Step 4: `pass`.

**Implementation Reference:** Story 2 — Files: `scripts/tests/test_review_route_rigor.py` (`FILTER_SENTENCES`, `FilterTextIsolationTest`)

**Status:** [ ] Pass  [ ] Fail

**Notes:**

---

### Scenario 15: Live `/review` with the line absent, then malformed: the header says `on` and the skill is read

**Source:** Acceptance Criteria (AC-2.4) — Story 2; Experience Design Feedback Model (the `/review` header line); switch states: Reviewer Filters absent and malformed
**Feature:** none
**Verification:** human — no recipe

**Preconditions:**
- Setup block pasted in both shells; `fxreset` prints nothing.
- `rvb` prints `uat: reject a negative weight`.
- `fsw - -` prints only `8:- **Gate 0 Divergence:** off`.
- `live` running in a new session.

**Steps:**
1. `/review --diff uat-fixture`
2. Read the reply to the end. In the first shell: `sed -n '1,6p' "$FX/.writ/state/review-uat-review.md"`
3. In the first shell: `fsw - of`. In the second shell: `/exit`, then `live`, then `/review --diff uat-fixture`.
4. In the first shell: `sed -n '1,6p' "$FX/.writ/state/review-uat-review.md"`
5. `fxreset`

**Expected Result:**
- Step 1: the scope line names one changed file, `uatfx/api/parcel_fee.py` (+2), against `uat-fixture`. In Step 3 of the review, `python3 scripts/review-override.py switch --name reviewer-filters` prints `on`, `reason: no_config_line`, and `review-override switch: reviewer-filters on (.writ/config.md)`. The session then reads `skills/review-judgment-filters/SKILL.md` before it assigns severities.
- Step 2: `# Code Review: uat-review`, a blank line, `> Reviewed: <today>`, `> Scope: …`, `> Spec: Standalone review`, `> Reviewer filters: on`.
- Step 2, judge by eye: a finding that rests on an imagined input with no cited caller (a `None` or string `weight_kg`; nothing in `uatfx/` passes one) is Low, not High or Critical. If every finding is Low, the Recommendation is ready to ship.
- Step 3: `fsw` prints `8:- **Reviewer Filters:** of` and `9:- **Gate 0 Divergence:** off`. The switch prints `on` and `reason: malformed_value of`, and the session reads the skill again.
- Step 4: the header ends `> Reviewer filters: on`.
- Step 5: prints nothing.

**Status:** [ ] Pass  [ ] Fail

**Notes:**

---

### Scenario 16: Live `/review` with the switch `off`: the header says `off` and the skill is not read

**Source:** Acceptance Criteria (AC-2.4) — Story 2; State Catalog "`reviewer-filters` switch off"; switch state: Reviewer Filters `off`
**Feature:** none
**Verification:** human — no recipe

**Preconditions:**
- Setup block pasted in both shells; `fxreset` prints nothing.
- `rvb` prints `uat: reject a negative weight`.
- `fsw - off` prints `8:- **Reviewer Filters:** off` and `9:- **Gate 0 Divergence:** off`.
- `live` running in a new session.

**Steps:**
1. `/review --diff uat-fixture`
2. Read the reply to the end. In the first shell: `sed -n '1,6p' "$FX/.writ/state/review-uat-review.md"`
3. `fxreset`

**Expected Result:**
- Step 1: `python3 scripts/review-override.py switch --name reviewer-filters` prints `off`, `reason: config_off`, and `review-override switch: reviewer-filters off (.writ/config.md)`. No step reads `skills/review-judgment-filters/SKILL.md`. The review still runs every applicable technique and ends with a Recommendation.
- Step 2: the header ends `> Reviewer filters: off`.
- Step 3: prints nothing.

**Status:** [ ] Pass  [ ] Fail

**Notes:**

---

## Story 3: Blast radius at Gate 2.5

### Scenario 17: Consumers and tests are listed per changed file; `.writ/`, changed files, oversized files, and non-UTF-8 files are left out

**Source:** Acceptance Criteria (AC-3.1) — Story 3; Error Map "`blast-radius` reads a candidate"; Shadow Path "Blast radius" (happy path); DEV-009
**Feature:** none
**Verification:** human — no recipe

**Preconditions:**
- Setup block pasted.

**Steps:**
1. `git -C "$BR" ls-files | wc -l; ls -l "$BR/big.txt" | awk '{print $5}'`
2. `brj --changed lib/parser.py lib/utils.py --repo "$BR"`
3. `brj --changed lib/parser.py app/cli.py --repo "$BR"`
4. `brj --changed lib/parser.py tests/test_parser.py --repo "$BR"`
5. `pt scripts/tests/test_change_surface.py -q -k "BlastRadiusCandidateTests or BlastRadiusSplitTests" 2>&1 | tail -1`

**Expected Result:**
- Step 1: `14` tracked files; `big.txt` is `1100008` bytes, over the 1 MB (1,048,576-byte) limit.
- Step 2: `verdict: "pass"`; `consumers: {"lib/parser.py": ["app/cli.py", "app/report.py", "docs/usage.md"], "lib/utils.py": ["docs/usage.md"]}`; `tests: {"lib/parser.py": ["tests/test_parser.py"], "lib/utils.py": []}`; `truncated: []`; `reasons: []`; `exit 0`. `.writ/specs/s/spec.md` and `sub/.writ/notes.md` name `lib/parser.py` but are skipped (`.writ/` at any depth, DEV-009); `big.txt` (over 1 MB) and `blob.dat` (not UTF-8) contain `parser` but are skipped without an error.
- Step 3: `consumers: {"app/cli.py": [], "lib/parser.py": ["app/report.py", "docs/usage.md"]}` and `tests: {"app/cli.py": [], "lib/parser.py": ["tests/test_parser.py"]}`. A changed file is never listed as a referrer.
- Step 4: `consumers: {"lib/parser.py": ["app/cli.py", "app/report.py", "docs/usage.md"]}` and `tests: {"lib/parser.py": []}`. The changed test file is not a key and is not listed.
- Step 5: `8 passed`.

**Implementation Reference:** Story 3 — Files: `scripts/change-surface.py` (`blast_radius`, `is_test_like`, `_under_writ`, `_read_text`)

**Status:** [ ] Pass  [ ] Fail

**Notes:**

---

### Scenario 18: Generic and short stems match by path only, and a token needs a clean boundary on both sides

**Source:** Acceptance Criteria (AC-3.2) — Story 3; DEV-008
**Feature:** none
**Verification:** human — no recipe

**Preconditions:**
- Setup block pasted.

**Steps:**
1. `grep -n 'utils' "$BR/app/cli.py" "$BR/docs/usage.md"; brj --changed lib/utils.py --repo "$BR"`
2. `grep -n 'setup' "$BR/docs/build.md" "$BR/notes/install.md"; brj --changed setup.py --repo "$BR"`
3. `cat "$BR/notes/rewrite.md"; brj --changed lib/parser.py --repo "$BR" | grep -c 'notes/rewrite.md'`
4. `pt scripts/tests/test_change_surface.py -q -k BlastRadiusTokenTests 2>&1 | tail -1`

**Expected Result:**
- Step 1: `app/cli.py` has only the bare stem (`from lib import utils`) and `docs/usage.md` has the path. Then `consumers: {"lib/utils.py": ["docs/usage.md"]}` and `tests: {"lib/utils.py": []}`: `utils` is a generic stem, so only the path counts.
- Step 2: `docs/build.md` names `setup.py`; `notes/install.md` has only the bare word `setup`. Then `consumers: {"setup.py": ["docs/build.md"]}` and `tests: {"setup.py": []}`. At the repo root the extensionless path is the bare generic stem, so it is not a token either (DEV-008).
- Step 3: `parser-v2 and parsers are planned.`, then `0`: `parser` followed by `-` or `s` is not a match.
- Step 4: `8 passed`.

**Implementation Reference:** Story 3 — Files: `scripts/change-surface.py` (`search_tokens`, `token_pattern`, `GENERIC_STEMS`)

**Status:** [ ] Pass  [ ] Fail

**Notes:**

---

### Scenario 19: `--limit` caps each list and names the file in `truncated`; `--pretty` counts before the cap

**Source:** Acceptance Criteria (AC-3.3) — Story 3; DEV-011
**Feature:** none
**Verification:** human — no recipe

**Preconditions:**
- Setup block pasted.

**Steps:**
1. `brj --changed lib/parser.py lib/utils.py --repo "$BR" --limit 2`
2. `cs blast-radius --changed lib/parser.py lib/utils.py --repo "$BR" --limit 2 --pretty`
3. `cs blast-radius --changed lib/parser.py --repo "$BR" --json`
4. `pt scripts/tests/test_change_surface.py -q -k "BlastRadiusCapTests or (BlastRadiusUsageTests and pretty)" 2>&1 | tail -1`

**Expected Result:**
- Step 1: `consumers: {"lib/parser.py": ["app/cli.py", "app/report.py"], "lib/utils.py": ["docs/usage.md"]}` (the first two by path); `tests: {"lib/parser.py": ["tests/test_parser.py"], "lib/utils.py": []}`; `truncated: ["lib/parser.py"]`; `reasons: []`; `exit 0`.
- Step 2: `pass`, `lib/parser.py: 3 consumer(s), 1 test(s)`, `lib/utils.py: 1 consumer(s), 0 test(s)`, `change-surface blast-radius: pass (2 changed, 3 consumers)`, `exit 0`. The counts are taken before the cap, so `3` exceeds the JSON list length (DEV-011).
- Step 3: one JSON line, `{"verdict": "pass", "consumers": {"lib/parser.py": ["app/cli.py", "app/report.py", "docs/usage.md"]}, "tests": {"lib/parser.py": ["tests/test_parser.py"]}, "truncated": [], "reasons": []}`, then `exit 0`. JSON is the default; `--json` is a no-op.
- Step 4: `6 passed`.

**Implementation Reference:** Story 3 — Files: `scripts/change-surface.py` (`pretty_blast`, `--limit`)

**Status:** [ ] Pass  [ ] Fail

**Notes:**

---

### Scenario 20: Without git, blast-radius walks the tree and says so; a FIFO or a deleted tracked file is skipped

**Source:** Acceptance Criteria (AC-3.4) — Story 3; Error Map "`blast-radius` lists candidates" (`git ls-files` fails); Shadow Path "Blast radius" (upstream error, no git); DEV-010
**Feature:** none
**Verification:** human — no recipe

**Preconditions:**
- Setup block pasted. `git -C "$BRNG" rev-parse --is-inside-work-tree 2>&1 | head -1` prints a `not a git repository` error.

**Steps:**
1. `brj --changed lib/parser.py lib/utils.py --repo "$BRNG"`
2. `mkfifo "$BRNG/app/pipe.md"; time brj --changed lib/parser.py --repo "$BRNG"; rm "$BRNG/app/pipe.md"`
3. `rm "$BR/app/report.py"; brj --changed lib/parser.py --repo "$BR"; git -C "$BR" checkout -q -- app/report.py; git -C "$BR" status --short`
4. `pt scripts/tests/test_change_surface.py -q -k BlastRadiusNoGitTests 2>&1 | tail -1`

**Expected Result:**
- Step 1: the same `consumers` and `tests` as Scenario 17 Step 2, `truncated: []`, `reasons: ["no_git_walked"]`, `verdict: "pass"`, `exit 0`. The walk skips the dot-folders `.writ/` and `sub/.writ/`.
- Step 2: returns at once (`real` well under a second) with `consumers: {"lib/parser.py": ["app/cli.py", "app/report.py", "docs/usage.md"]}`, `reasons: ["no_git_walked"]`, `exit 0`. A FIFO is not a regular file and is never opened. If the command hangs, press Ctrl-C and mark Fail.
- Step 3: `consumers: {"lib/parser.py": ["app/cli.py", "docs/usage.md"]}`, `reasons: []`, `exit 0`, no error for the tracked file missing from disk; `status` prints nothing after the restore.
- Step 4: `3 passed`.

**Implementation Reference:** Story 3 — Files: `scripts/change-surface.py` (`_git_files`, `_walk_files`, `_read_text`); WWB decision 2 (FIFO guard)

**Status:** [ ] Pass  [ ] Fail

**Notes:**

---

### Scenario 21: A bad `--repo` is unverifiable, a missing `--changed` or `--limit 0` is a usage error, and test-only changes give empty maps

**Source:** Acceptance Criteria (AC-3.4) — Story 3; Shadow Path "Blast radius" (nil input, empty input, bad `--repo`); State Catalog "Blast radius unverifiable"
**Feature:** none
**Verification:** human — no recipe

**Preconditions:**
- Setup block pasted. `ls "$W/no-such-dir" 2>&1` reports no such file.

**Steps:**
1. `brj --changed lib/parser.py --repo "$W/no-such-dir"`
2. `cs blast-radius --changed lib/parser.py --repo "$W/no-such-dir" --pretty`
3. `rc python3 "$CL/scripts/change-surface.py" blast-radius --repo "$BR"`
4. `rc python3 "$CL/scripts/change-surface.py" blast-radius --changed lib/parser.py --repo "$BR" --limit 0`
5. `brj --changed tests/test_parser.py --repo "$BR"`
6. `pt scripts/tests/test_change_surface.py -q -k "BlastRadiusUsageTests and not pretty" 2>&1 | tail -1`

**Expected Result:**
- Step 1: `verdict: "unverifiable"`, `consumers: {}`, `tests: {}`, `truncated: []`, `reasons: ["repo_unreadable"]`, `exit 0`.
- Step 2: `unverifiable`, `reason: repo_unreadable`, `change-surface blast-radius: unverifiable (1 changed, 0 consumers)`, `exit 0`.
- Step 3: a usage line and `error: --changed needs at least one file` on stderr, then `exit 2 stdout-bytes 0`.
- Step 4: a usage error saying `--limit` must be an integer >= 1 on stderr, then `exit 2 stdout-bytes 0`.
- Step 5: `verdict: "pass"`, `consumers: {}`, `tests: {}`, `truncated: []`, `reasons: []`, `exit 0`.
- Step 6: `3 passed`.

**Implementation Reference:** Story 3 — Files: `scripts/change-surface.py` (`run_blast_radius`, `_positive_int`)

**Status:** [ ] Pass  [ ] Fail

**Notes:**

---

### Scenario 22: `classify` prints the same output and exit codes as before Story 3

**Source:** Acceptance Criteria (AC-3.4, `classify` unchanged) — Story 3
**Feature:** none
**Verification:** human — no recipe

**Preconditions:**
- Setup block pasted. `ls "$OLD/scripts/change-surface.py"` lists the file.

**Steps:**
1. `for s in "$OLD" "$CL"; do (for a in src/components/Button.tsx styles/site.css api/orders.py lib/utils/format.ts "src/components/Card.tsx src/components/Card.test.tsx" README.md; do python3 "$s/scripts/change-surface.py" classify --changed $a; echo "exit $?"; python3 "$s/scripts/change-surface.py" classify --changed $a --pretty; echo "exit $?"; done; python3 "$s/scripts/change-surface.py" classify 2>/dev/null; echo "exit $?") > "$W/classify-${s##*/}.txt"; done; diff "$W/classify-old.txt" "$W/classify-clone.txt" && echo identical`
2. `cat "$W/classify-clone.txt"`
3. `pt scripts/tests/test_change_surface.py -q -k ClassifyUnchangedTests 2>&1 | tail -1`

**Expected Result:**
- Step 1: `identical`.
- Step 2: each input prints a JSON line, `exit 0`, the bare word, `exit 0`: `{"class": "single-component"}` for the button, `style-only` for the stylesheet, `full-stack` for `api/orders.py`, `cross-component` for the `lib/utils/` file, `single-component` for the card and its paired test, `cross-component` for `README.md`. The last line is `exit 2` (no `--changed`).
- Step 3: `2 passed`.

**Implementation Reference:** Story 3 — Files: `scripts/change-surface.py` (`classify`, `is_test` unchanged)

**Status:** [ ] Pass  [ ] Fail

**Notes:**

---

### Scenario 23: Gate 2.5 runs blast-radius only on the `review-agent` route with the switch on

**Source:** Acceptance Criteria (AC-3.5; text half) — Story 3; Business Rule "When the safety fact applies"; Experience Design Journey steps 1 and 2
**Feature:** none
**Verification:** human — no recipe

**Preconditions:**
- Setup block pasted; `reset` prints nothing.

**Steps:**
1. `sed -n '282,284p' "$CL/commands/implement-story.md"`
2. `grep -n 'change-surface.py blast-radius' "$CL/commands/implement-story.md" | cut -c1-12`
3. `for c in 6382e24^ 6382e24; do git -C "$CL" show "${c}:commands/implement-story.md" | wc -c; done`
4. `pt scripts/tests/test_change_surface.py -q -k Gate25BlastRadiusTextTests 2>&1 | tail -1`

**Expected Result:**
- Step 1: line 282 is the sentence that an `unverifiable` verdict, or a helper that cannot run, routes `review-agent`. Line 284 is the paragraph: **Blast radius.** When `gate3_route` names `review-agent`, run `python3 scripts/review-override.py switch --name safety-fact`. On `on`, run `python3 scripts/change-surface.py blast-radius --changed <files> --repo . > .writ/state/blast-radius-<story-stem>.json` and pass the file to Gate 3 as `blast_radius`. Otherwise `blast_radius` is `(none)`. This is the technical spec's draft word for word.
- Step 2: one line, starting `284:`. Gate 0 and Gate 3 do not run blast-radius.
- Step 3: `38729`, then `39076` (+347).
- Step 4: `3 passed`.
- The live half: Scenario 39 (switch on, file written), 40 (switch off, no file), 41 (malformed, file written), 42 (evaluator route, no file).

**Implementation Reference:** Story 3 — Files: `commands/implement-story.md` (`#### Gate 2.5`)

**Status:** [ ] Pass  [ ] Fail

**Notes:**

---

### Scenario 24: One blast-radius pass over this repo finishes quickly; Story 3's tests and the eval check pass

**Source:** Error Map "`blast-radius` on a huge repo" (slow scan) — Story 3; Acceptance Criteria (task 3.5)
**Feature:** none
**Verification:** human — no recipe

**Preconditions:**
- Setup block pasted; `reset` prints nothing. Run outside any sandbox.

**Steps:**
1. `time cs blast-radius --changed scripts/review-override.py --repo "$CL" --pretty`
2. `pt scripts/tests/test_change_surface.py -q 2>&1 | tail -1`
3. `(cd "$CL" && bash scripts/eval.sh --check=change-surface >/dev/null; echo "exit $?"); tail -2 "$(ls -t "$CL"/.writ/state/eval-*.md | head -1)"`

**Expected Result:**
- Step 1: `pass`, `scripts/review-override.py: <n> consumer(s), <m> test(s)` with `<n>` at least 12 and `<m>` at least 14 (Story 3 recorded 12 and 14 before Story 4 added references), `change-surface blast-radius: pass (1 changed, <n> consumers)`, `exit 0`. `real` is well under a few seconds (Story 3 recorded 0.14 s over about 2,310 tracked files).
- Step 2: `48 passed`.
- Step 3: `exit 0`, then `- Findings: 0` and `- Run errors: 0`.

**Implementation Reference:** Story 3 — WWB decision 3 (smoke on this repo); `scripts/tests/test_change_surface.py` (`BlastRadiusRealRepoTests`)

**Status:** [ ] Pass  [ ] Fail

**Notes:**

---

## Story 4: Safety fact at Gate 3

### Scenario 25: The blast-radius skill holds the ladder, the section format, and the rules, and lints `pass`

**Source:** Acceptance Criteria (AC-4.5, through task 4.3) — Story 4
**Feature:** none
**Verification:** human — no recipe

**Preconditions:**
- Setup block pasted; `reset` prints nothing.

**Steps:**
1. `sed -n '1,7p' "$CL/skills/blast-radius/SKILL.md"`
2. `grep -n '^## \|^### ' "$CL/skills/blast-radius/SKILL.md"`
3. `sed -n '/^### Evidence Ladder/,/^### Safety Fact section/p' "$CL/skills/blast-radius/SKILL.md"`
4. `sed -n '/^### Rules/,/^### Reading/p' "$CL/skills/blast-radius/SKILL.md"`
5. `sed -n '/^### .reproduced./,$p' "$CL/skills/blast-radius/SKILL.md"`
6. `(cd "$CL" && bash scripts/lint-skill.sh skills/blast-radius/SKILL.md; echo "exit $?")`
7. `pt scripts/tests/test_review_route_rigor.py -q -k BlastSkillTest 2>&1 | tail -1`

**Expected Result:**
- Step 1: `name: blast-radius`, `description: "Name the one fact a change is safe because of and push its evidence up a five-rung ladder."`, `disable-model-invocation: true`, `status: candidate`, `status_evidence` naming one consumer, `agents/review-agent.md`, and that it stays a skill so the safety-fact switch can remove it cleanly.
- Step 2: `## Purpose`, `## When to Use`, `## How to Apply`, `### Evidence Ladder`, `### Safety Fact section`, `### Safety Fact` (the format example inside a code fence), `### Rules`, `### Reading `blast_radius``, `### `reproduced``, `### On a re-review`.
- Step 3: the ladder is not cumulative; the measured rung is the highest rung whose evidence checks out; the floor is `traced`. A five-row table, `claimed`, `read`, `traced`, `tested`, `reproduced`, each with its meaning and evidence line. "What makes a line count": repo-relative paths only (absolute or escaping paths do not count); `read` needs the line within the file; `traced` needs every cite valid and one among the consumers, with `none` only when the blast radius is `pass` with no consumers; `tested` needs the name in the file, `exit code: 0`, and the file named in the run; `reproduced` needs `app-verify-result-v1` with verdict `pass`; one bad citation drops that rung.
- Step 4: one fact (the weaker of two); a fact about the code, not the process; push up the ladder; on `Holds: no`, cite the breaking caller and FAIL with category `architecture` or `security`; `Holds: no` beside PASS is a contradiction the gate fails.
- Step 5: `reproduced` only on a recode iteration, with a passing result for this story and unchanged checked paths; on a re-review, fix `safety_fact_missing <item>`, `safety_fact_below_floor <measured>`, and a `rung:` line whose measured rung is below the claim.
- Step 6: `pass`, `reason: ✅ skills/blast-radius/SKILL.md: clean`, `lint-skill: pass (1 file(s) clean)`, `exit 0`.
- Step 7: `6 passed`.

**Implementation Reference:** Story 4 — Files: `skills/blast-radius/SKILL.md`

**Status:** [ ] Pass  [ ] Fail

**Notes:**

---

### Scenario 26: The blast-radius skill is registered, its generated copies are current, and their example citations stay repo-relative

**Source:** Acceptance Criteria (AC-4.5, through task 4.3) — Story 4
**Feature:** none
**Verification:** human — no recipe

**Preconditions:**
- Setup block pasted; `reset` prints nothing.

**Steps:**
1. `grep -n -A4 '  - name: blast-radius$' "$CL/.writ/manifest.yaml"; grep -n '^skills:' "$CL/.writ/manifest.yaml"`
2. `grep -n 'skills are live\|skills/blast-radius/SKILL.md' "$CL/README.md" | cut -c1-120; grep -n 'skills/blast-radius/SKILL.md' "$CL/SKILL.md"`
3. `ls "$CL/plugins/writ/skills/blast-radius/SKILL.md" "$CL/cursor/plugin/skills/blast-radius/SKILL.md"; sed -n '/^### Safety Fact section/,/^### Rules/p' "$CL/plugins/writ/skills/blast-radius/SKILL.md" | grep '^- '`
4. `(cd "$CL" && bash scripts/gen-skill.sh --check 2>/dev/null | head -1; python3 scripts/gen-platform-trees.py --check | head -2)`
5. `pt scripts/tests/test_review_route_rigor.py -q -k BlastSkillRegistrationTest 2>&1 | tail -1`

**Expected Result:**
- Step 1: `259:  - name: blast-radius`, then `file: skills/blast-radius/SKILL.md`, the description, `status: candidate`, `tags: [review, safety, evidence]`; `258:skills:`. It is the first skill, in alphabetical order.
- Step 2: README line 46 says `19 skills are live today`, and line 207 is the skill's row; root `SKILL.md` line 140 is the row `blast-radius`, `candidate`, `skills/blast-radius/SKILL.md`, and the description.
- Step 3: both copies listed. Three example lines: `- read: `src/parser.py:142``, `- traced: `src/cli.py:88` — passes the user's file list, rejected earlier when empty`, `- tested: `tests/test_parser.py::test_empty_input``. The plugin generator did not rewrite them to a `scripts/` or absolute path, which the skill's own rule would reject.
- Step 4: `pass`; then `pass` and `gen-platform-trees: pass (0 stale, 0 missing, 0 orphan, 0 unmapped, 0 vendor)`.
- Step 5: `5 passed`.

**Implementation Reference:** Story 4 — Files: `.writ/manifest.yaml`, `README.md`, `SKILL.md`, generated skill copies; WWB decision 4 (neutral example paths)

**Status:** [ ] Pass  [ ] Fail

**Notes:**

---

### Scenario 27: `review-agent` takes three new inputs, reads the skill only on `on`, and has a one-line output slot; the evaluator takes none of them

**Source:** Acceptance Criteria (AC-4.4, AC-4.5, through task 4.4) — Story 4; Must Include 6; DEV-018
**Feature:** none
**Verification:** human — no recipe

**Preconditions:**
- Setup block pasted; `reset` prints nothing.

**Steps:**
1. `sed -n '/^## Input Requirements/,/^## Prompt Template/p' "$CL/agents/review-agent.md" | grep 'reviewer_filters\|recorded_test_results\|safety_fact\|blast_radius'`
2. `grep -n '^## Recorded Test Results\|{recorded_test_results}\|Read skills/\|^## Output Format\|^### Security Assessment\|^### Safety Fact' "$CL/agents/review-agent.md" | cut -c1-160`
3. `grep -c 'safety_fact\|blast_radius\|blast-radius' "$CL/agents/evaluator-agent.md"`
4. `grep -n 'Read skills/blast-radius\|^### Safety Fact' "$CL/claude-code/agents/writ-reviewer.md" | cut -c1-120`
5. `pt scripts/tests/test_review_route_rigor.py -q -k "ReviewAgentSafetyFactTest or EvaluatorHasNoSafetyFactTest" 2>&1 | tail -1`

**Expected Result:**
- Step 1: four input rows: `reviewer_filters` (`on` or `off`, resolved by Gate 3), `recorded_test_results` (the orchestrator's own run, not the coding agent's report), `safety_fact` (`on` when Gate 2.5 wrote a blast radius), `blast_radius` (the Gate 2.5 JSON, or `(none)`).
- Step 2: `94:## Recorded Test Results` and `95:{recorded_test_results}` (the prompt block DEV-018 added); `196:` the filters line; `198:` "When `{safety_fact}` is `on`, `Read skills/blast-radius/SKILL.md` and write its `### Safety Fact` section, starting from `{blast_radius}`."; `200:## Output Format`; `211:### Security Assessment`; `215:### Safety Fact (only when safety_fact is on; format in the skill)`; and `350:### Security Assessment` from an output example. No ladder text.
- Step 3: `0`. The evaluator never runs on the risk route.
- Step 4: `211:` the same conditional line and `228:` the same slot line in the generated reviewer.
- Step 5: `8 passed`.

**Implementation Reference:** Story 4 — Files: `agents/review-agent.md`, `claude-code/agents/writ-reviewer.md` (generated)

**Status:** [ ] Pass  [ ] Fail

**Notes:**

---

### Scenario 28: Each rung is measured on its own evidence

**Source:** Acceptance Criteria (AC-4.1) — Story 4; Must Include 1; Shadow Path "Safety-fact verify" (happy path; empty input: a section with no evidence lines measures `claimed`)
**Feature:** none
**Verification:** human — no recipe

**Preconditions:**
- Setup block pasted. `wc -l < "$SF/src/lib.py"` prints `4`.

**Steps:**
1. `rv "$W/r.md" PASS yes claimed; sfv "$W/r.md" "${BT[@]}"`
2. `` rv "$W/r.md" PASS yes read 'read: `src/lib.py:2`'; sfv "$W/r.md" "${BT[@]}" ``
3. `rv "$W/r.md" PASS yes traced 'traced: src/caller.py:3 — passes [1, 2], never an empty list'; sfv "$W/r.md" "${BT[@]}"`
4. `rv "$W/r.md" PASS yes tested 'tested: tests/test_lib.py::LibTests::test_rejects_empty'; sfv "$W/r.md" "${BT[@]}"`
5. `rv "$W/r.md" PASS yes reproduced 'reproduced: evidence/uat/parse/result.json'; sfv "$W/r.md" "${BT[@]}"`
6. `pt scripts/tests/test_review_override.py -q -k SafetyFactRungTests 2>&1 | tail -1`

**Expected Result:**
- Step 1: `fail`, `rung: claimed=claimed measured=claimed`, `fact: no caller passes an empty list to parse()`, `reason: safety_fact_below_floor claimed`, `review-override safety-fact: fail (measured claimed, floor traced)`, `exit 1`. A non-empty Fact alone is `claimed`.
- Step 2: the same shape with `rung: claimed=read measured=read` and `reason: safety_fact_below_floor read`; `exit 1`. The backticks around the citation are stripped.
- Step 3: `pass`, `rung: claimed=traced measured=traced`, the `fact:` line, no `reason:` line, `review-override safety-fact: pass (measured traced, floor traced)`, `exit 0`.
- Step 4: `pass`, `rung: claimed=tested measured=tested`, `exit 0`. No `read` or `traced` line was needed: the ladder is not cumulative.
- Step 5: `pass`, `rung: claimed=reproduced measured=reproduced`, `exit 0`.
- Step 6: `29 passed`.

**Implementation Reference:** Story 4 — Files: `scripts/review-override.py` (`_measured_rung`, `_cite_ok`, `_traced_ok`, `_tested_ok`, `_reproduced_ok`)

**Status:** [ ] Pass  [ ] Fail

**Notes:**

---

### Scenario 29: A citation that is missing, out of range, outside the repo, absolute, or one bad line among good ones does not count

**Source:** Acceptance Criteria (AC-4.1) — Story 4; Error Map "`safety-fact` resolves a cited path"; DEV-015, DEV-016, DEV-017
**Feature:** none
**Verification:** human — no recipe

**Preconditions:**
- Setup block pasted. `wc -l < "$W/outside.py"` prints `2`.

**Steps:**
1. `rv "$W/r.md" PASS yes read 'read: src/missing.py:1'; sfv "$W/r.md" "${BT[@]}"`
2. `rv "$W/r.md" PASS yes read 'read: src/lib.py:99'; sfv "$W/r.md" "${BT[@]}"`
3. `rv "$W/r.md" PASS yes read 'read: ../outside.py:1'; sfv "$W/r.md" "${BT[@]}"`
4. `rv "$W/r.md" PASS yes read "read: $SF/src/lib.py:2"; sfv "$W/r.md" "${BT[@]}"`
5. `ln -s "$W/outside.py" "$SF/src/link.py"; rv "$W/r.md" PASS yes read 'read: src/link.py:1'; sfv "$W/r.md" "${BT[@]}"; rm "$SF/src/link.py"`
6. `rv "$W/r.md" PASS yes read 'read: src/lib.py:2' 'read: src/missing.py:1'; sfv "$W/r.md" "${BT[@]}"`
7. `rv "$W/r.md" PASS yes read 'read: src/../src/lib.py:2'; sfv "$W/r.md" "${BT[@]}"`
8. `rv "$W/r.md" PASS yes tested 'tested: tests/test_lib.py::LibTests::test_rejects_empty[case-1]'; sfv "$W/r.md" "${BT[@]}"`
9. `printf '{"schema": "app-verify-result-v1", "verdict": "fail"}\n' > "$SF/evidence/uat/parse/fail.json"; rv "$W/r.md" PASS yes reproduced 'reproduced: evidence/uat/parse/fail.json'; sfv "$W/r.md" "${BT[@]}"; rm "$SF/evidence/uat/parse/fail.json"`

**Expected Result:**
- Steps 1 to 6: each prints `fail`, `rung: claimed=read measured=claimed`, the `fact:` line, `reason: safety_fact_below_floor claimed`, the `fail` summary, `exit 1`. The `read` rung is rejected for a missing file (1), a line past the end of a 4-line file (2), a `../` path that leaves the repo although the file exists (3), an absolute path even inside the repo (4, DEV-016), a symlink that resolves outside the repo (5), and one bad line among good ones (6, DEV-015). No traceback in any step.
- Step 7: `fail`, `rung: claimed=read measured=read`, `reason: safety_fact_below_floor read`, `exit 1`. A `..` that stays inside the repo counts.
- Step 8: `pass`, `rung: claimed=tested measured=tested`, `exit 0`. A pytest node ID with a class and a `[param]` suffix is accepted (DEV-017).
- Step 9: `fail`, `rung: claimed=reproduced measured=claimed`, `reason: safety_fact_below_floor claimed`, `exit 1`. A result whose verdict is not `pass` does not count.

**Implementation Reference:** Story 4 — Files: `scripts/review-override.py` (`_inside`, `CITE_LINE`, `PARAM_ID`)

**Status:** [ ] Pass  [ ] Fail

**Notes:**

---

### Scenario 30: `traced` needs a cited caller from the blast radius's consumers; `none` counts only when there are none

**Source:** Acceptance Criteria (AC-4.2) — Story 4
**Feature:** none
**Verification:** human — no recipe

**Preconditions:**
- Setup block pasted. `cat "$W/blast.json"` lists `src/caller.py` as the one consumer of `src/lib.py`; `cat "$W/blast-empty.json"` lists none.

**Steps:**
1. `rv "$W/r.md" PASS yes traced 'traced: src/caller.py:3 — passes [1, 2]'; sfv "$W/r.md" "${BT[@]}"`
2. `rv "$W/r.md" PASS yes traced 'traced: src/other.py:1 — sets x'; sfv "$W/r.md" "${BT[@]}"`
3. `rv "$W/r.md" PASS yes traced 'traced: src/caller.py:3 — passes [1, 2]' 'traced: src/other.py:1 — sets x'; sfv "$W/r.md" "${BT[@]}"`
4. `rv "$W/r.md" PASS yes traced 'traced: src/caller.py:3 — passes [1, 2]' 'traced: src/missing.py:1 — no such file'; sfv "$W/r.md" "${BT[@]}"`
5. `rv "$W/r.md" PASS yes traced 'traced: none — searched for parse( in src/'; sfv "$W/r.md" --blast-radius "$W/blast-empty.json" --tests-output "$W/tests-ok.txt"`
6. `rv "$W/r.md" PASS yes traced 'traced: none — searched for parse( in src/'; sfv "$W/r.md" "${BT[@]}"`

**Expected Result:**
- Step 1: `pass`, `rung: claimed=traced measured=traced`, `exit 0`.
- Step 2: `fail`, `rung: claimed=traced measured=claimed`, `reason: safety_fact_below_floor claimed`, `exit 1`. `src/other.py` exists but is not a consumer.
- Step 3: `pass`, `rung: claimed=traced measured=traced`, `exit 0`. Every cite exists and at least one is a consumer.
- Step 4: `fail`, `rung: claimed=traced measured=claimed`, `exit 1`. Every cited path must exist.
- Step 5: `pass`, `rung: claimed=traced measured=traced`, `exit 0`. `none` counts when the blast radius is `pass` with no consumers.
- Step 6: `fail`, `rung: claimed=traced measured=claimed`, `reason: safety_fact_below_floor claimed`, `exit 1`. `none` does not count when consumers exist.

**Implementation Reference:** Story 4 — Files: `scripts/review-override.py` (`_traced_ok`, `_consumer_union`)

**Status:** [ ] Pass  [ ] Fail

**Notes:**

---

### Scenario 31: Each fail reason fires on its own condition and prints in table order

**Source:** Acceptance Criteria (AC-4.3) — Story 4; Business Rule "`Holds: no` with PASS is a Gate 3 FAIL"; State Catalog "`Holds: no`, reviewer PASS" and "section missing"; DEV-013, DEV-014
**Feature:** none
**Verification:** human — no recipe

**Preconditions:**
- Setup block pasted.

**Steps:**
1. `printf '### REVIEW_RESULT: PASS\n\n### Security Assessment\n**Risk Level:** Clean\n\n### Recommendations\nNone.\n' > "$W/r.md"; sfv "$W/r.md" "${BT[@]}"`
2. `FACT= rv "$W/r.md" PASS maybe proven; sfv "$W/r.md" "${BT[@]}"`
3. `rv "$W/r.md" PASS no traced 'traced: src/caller.py:3 — passes [1, 2]'; sfv "$W/r.md" "${BT[@]}"`
4. `rv "$W/r.md" - no traced 'traced: src/caller.py:3 — passes [1, 2]'; sfv "$W/r.md" "${BT[@]}"`
5. `rv "$W/r.md" PASS no proven 'read: src/lib.py:2'; sfv "$W/r.md" "${BT[@]}"`
6. `pt scripts/tests/test_review_override.py -q -k SafetyFactVerdictTests 2>&1 | tail -1`

**Expected Result:**
- Step 1: `fail`, `rung: claimed=none measured=none`, `fact: (none)`, `reason: safety_fact_missing section`, `reason: safety_fact_below_floor none`, `review-override safety-fact: fail (measured none, floor traced)`, `exit 1`. With no section both reasons apply, missing first (DEV-014).
- Step 2: `fail`, `rung: claimed=none measured=none`, `fact: (none)`, then `reason: safety_fact_missing fact`, `reason: safety_fact_missing holds`, `reason: safety_fact_missing rung`, `reason: safety_fact_below_floor none`, the summary, `exit 1`.
- Step 3: `fail`, `rung: claimed=traced measured=traced`, the `fact:` line, `reason: safety_fact_contradicts_verdict` and no other reason, `exit 1`.
- Step 4: the same as Step 3. `Holds: no` with no verdict line is a contradiction (DEV-013).
- Step 5: `fail`, `rung: claimed=none measured=read`, then `reason: safety_fact_missing rung`, `reason: safety_fact_below_floor read`, `reason: safety_fact_contradicts_verdict`, in that order, `exit 1`.
- Step 6: `22 passed`.

**Implementation Reference:** Story 4 — Files: `scripts/review-override.py` (`safety_fact`, `_parse_safety_section`)

**Status:** [ ] Pass  [ ] Fail

**Notes:**

---

### Scenario 32: An overclaim alone passes, `Holds: no` with FAIL passes, an unreadable review is unverifiable, and a missing flag is a usage error

**Source:** Acceptance Criteria (AC-4.3) — Story 4; Business Rule "The measured rung, not the claimed rung, decides the floor"; Shadow Path "Safety-fact verify" (nil input, upstream error); Error Map "`safety-fact` reads review output"; State Catalog "fact at or above floor", "`Holds: no`, reviewer FAIL", "Verifier cannot read the review output"
**Feature:** none
**Verification:** human — no recipe

**Preconditions:**
- Setup block pasted. `ls "$W/no-such-review.md" 2>&1` reports no such file.

**Steps:**
1. `rv "$W/r.md" PASS yes tested 'traced: src/caller.py:3 — passes [1, 2]'; sfv "$W/r.md" "${BT[@]}"`
2. `rv "$W/r.md" FAIL no traced 'traced: src/caller.py:3 — passes [1, 2]'; sfv "$W/r.md" "${BT[@]}"; rv "$W/r.md" PAUSE no traced 'traced: src/caller.py:3 — passes [1, 2]'; sfv "$W/r.md" "${BT[@]}"`
3. `sfv "$W/no-such-review.md" "${BT[@]}"`
4. `rc python3 "$CL/scripts/review-override.py" safety-fact --repo "$SF"`
5. `pt scripts/tests/test_review_override.py -q -k SafetyFactLeavesOtherSubcommandsTests 2>&1 | tail -1`

**Expected Result:**
- Step 1: `pass`, `rung: claimed=tested measured=traced`, the `fact:` line, no `reason:` line, `review-override safety-fact: pass (measured traced, floor traced)`, `exit 0`. The overclaim shows on the `rung:` line and is not a reason on its own.
- Step 2: twice, `pass`, `rung: claimed=traced measured=traced`, no `reason:` line, `exit 0`. A fact that does not hold agrees with a FAIL or PAUSE verdict; the agent's verdict still decides Gate 3.
- Step 3: `unverifiable`, `reason: review_output_unreadable`, `review-override safety-fact: unverifiable (review_output_unreadable)`, `exit 0`.
- Step 4: a usage line and an error that `--review-output` is required on stderr, then `exit 2 stdout-bytes 0`.
- Step 5: `2 passed` (`check` and `switch` unchanged by Story 4).

**Implementation Reference:** Story 4 — Files: `scripts/review-override.py` (`safety_fact`, `build_parser`)

**Status:** [ ] Pass  [ ] Fail

**Notes:**

---

### Scenario 33: Gate 3 saves the review and the test run, runs the verifier, and routes each reason in order

**Source:** Acceptance Criteria (AC-4.4; text half) — Story 4; Business Rules "When the safety fact applies" and "Verifier outcomes"; Error Map "Reviewer omits the section twice" and "Reviewer cannot reach `traced` twice"; Shadow Path "Gate 3 routing" (verifier crash); DEV-019
**Feature:** none
**Verification:** human — no recipe

**Preconditions:**
- Setup block pasted; `reset` prints nothing.

**Steps:**
1. `grep -n 'Same inputs:' "$CL/commands/implement-story.md"`
2. `sed -n '/^\*\*Safety fact/,/^\*\*Jev shadow/p' "$CL/commands/implement-story.md"`
3. `grep -c 'review-override.py safety-fact' "$CL/commands/implement-story.md"`
4. `pt scripts/tests/test_review_route_rigor.py -q -k "Gate3SafetyFactTest and not byte_cap" 2>&1 | tail -1`

**Expected Result:**
- Step 1: line 305, the `review-agent` inputs, ends with `recorded_test_results`, `blast_radius`, `safety_fact` (`on` unless `blast_radius` is `(none)`). The risk-route paragraph above it spawns `review-agent` "with the inputs below".
- Step 2: the paragraph is headed **Safety fact (`safety_fact` on).** It saves the review and `recorded_test_results` to `.writ/state/gate3-review-<story-stem>.md` and `gate3-tests-<story-stem>.txt` and runs `python3 scripts/review-override.py safety-fact --review-output <review> --repo . --blast-radius <blast_radius> --tests-output <tests>`. "First match wins", in this order:
  - `safety_fact_contradicts_verdict` → Gate 3 FAIL, with no re-review (DEV-019).
  - `safety_fact_missing` or `safety_fact_below_floor` → re-spawn `review-agent` once with the `rung:` and `reason:` lines appended and re-verify, in the same Gate 3 attempt with no `review_cycle` increment. Still missing → BLOCKED escalation (`review-agent`, restart Gate 3). Still below floor → Gate 3 FAIL, and the coder gets the `fact:` and `rung:` lines to add a test that exercises the fact.
  - `pass`, `unverifiable`, or an exit other than 0, 1, or 2 → continue, print the reason, never `⚠️ DEGRADED`.
  - "A fail counts as a panel `block`: one increment; on PAUSE, accept recodes." Then the report sentence (Scenario 38).
- Step 3: `1`. No other gate runs the verifier.
- Step 4: `6 passed`.
- The live half: Scenario 39 (the pass path).

**Implementation Reference:** Story 4 — Files: `commands/implement-story.md` (`#### Gate 3`); WWB decision 1 (Gate 3 prose owns routing)

**Status:** [ ] Pass  [ ] Fail

**Notes:**

---

### Scenario 34: Ladder text lives only in the skill, and a rung definition pasted into a command fails the test

**Source:** Acceptance Criteria (AC-4.5) — Story 4; Hardest Constraint
**Feature:** none
**Verification:** human — no recipe

**Preconditions:**
- Setup block pasted; `reset` prints nothing.

**Steps:**
1. `(cd "$CL" && grep -rli 'the ladder is not cumulative\|someone said so' --include='*.md' --include='*.toml' --include='*.template' --exclude-dir=.writ --exclude-dir=.git --exclude-dir=.venv .)`
2. `pt scripts/tests/test_review_route_rigor.py -q -k LadderTextIsolationTest 2>&1 | tail -1`
3. `echo 'The ladder is not cumulative.' >> "$CL/commands/review.md"; pt scripts/tests/test_review_route_rigor.py -q -k "LadderTextIsolationTest and absent" 2>&1 | grep -E 'review.md: the ladder|failed|passed'; reset`

**Expected Result:**
- Step 1: exactly three paths, in any order: `skills/blast-radius/SKILL.md`, `plugins/writ/skills/blast-radius/SKILL.md`, `cursor/plugin/skills/blast-radius/SKILL.md`.
- Step 2: `2 passed`.
- Step 3: a line naming `commands/review.md: the ladder is not cumulative`, then `1 failed` (with a deselected count). `reset` prints nothing.

**Implementation Reference:** Story 4 — Files: `scripts/tests/test_review_route_rigor.py` (`LADDER_SENTENCES`, `LadderTextIsolationTest`)

**Status:** [ ] Pass  [ ] Fail

**Notes:**

---

### Scenario 35: Gate 2.5 and Gate 3 grew 1,795 bytes, under the 1,800-byte cap, with dated governor pins

**Source:** Acceptance Criteria (AC-4.4, AC-4.5, through task 4.5) — Story 4; Technical Concerns (byte budget); DEV-004
**Feature:** none
**Verification:** human — no recipe

**Preconditions:**
- Setup block pasted; `reset` prints nothing.

**Steps:**
1. `wc -c < "$CL/commands/implement-story.md"; git -C "$CL" show df3b461:commands/implement-story.md | wc -c`
2. `git -C "$CL" diff -U0 df3b461 7b6de50 -- commands/implement-story.md | grep '^@@' | cut -c1-30; grep -n '^#### Gate 2.5\|^#### Gate 3' "$CL/commands/implement-story.md"`
3. `grep -n -B4 '"commands/implement-story.md": ' "$CL/scripts/tests/test_governor_enforcement.py"`
4. `pt scripts/tests/test_review_route_rigor.py -q -k byte_cap 2>&1 | tail -1; pt scripts/tests/test_governor_enforcement.py -q 2>&1 | tail -1`

**Expected Result:**
- Step 1: `40229`, then `38434`: +1,795 bytes (295 in Story 2, 347 in Story 3, 1,153 in Story 4), under the 1,800-byte cap.
- Step 2: four hunks, adding lines at 284–285, 294–296, 305, and 322–329. Gate 2.5 starts at line 267, Gate 3 at 288, and Gate 3.5 at 332, so every change sits in Gate 2.5 or Gate 3.
- Step 3: three dated comments, `2026-10-29 (2026-10-25-review-route-rigor Story 2): 13474 -> 13769`, `Story 3): 13769 -> 14116`, `Story 4): 14116 -> 15269`, directly above `"commands/implement-story.md": 15269,` (40,229 − 24,960 = 15,269).
- Step 4: `1 passed` (with a deselected count), then a summary with no `failed`.

**Implementation Reference:** Story 4 — Files: `scripts/tests/test_governor_enforcement.py` (`KNOWN_OVER_BUDGET`), `scripts/tests/test_review_route_rigor.py` (`IMPLEMENT_STORY_CAP = 40234`)

**Status:** [ ] Pass  [ ] Fail

**Notes:**

---

### Scenario 36: The full suite on Python 3.9, the bash tests, the generators, and the quality gate pass

**Source:** Acceptance Criteria (AC-4.1 to AC-4.5, through task 4.7) — Story 4; Success Criteria; Must Include 7
**Feature:** none
**Verification:** human — no recipe

**Preconditions:**
- Setup block pasted; `reset` prints nothing. Run outside any sandbox (eval runs `git init` in a temp dir). About five minutes. Run pytest alone, not beside eval or the bash tests.

**Steps:**
1. `pt -q 2>&1 | tail -1`
2. `(cd "$CL" && for t in scripts/tests/test_*.sh; do bash "$t" >/dev/null 2>&1 || echo "FAIL $t"; done; echo "bash loop done")`
3. `(cd "$CL" && bash scripts/gen-skill.sh --check 2>/dev/null | head -1; python3 scripts/gen-platform-trees.py --check | head -2)`
4. `(cd "$CL" && bash scripts/eval.sh >/dev/null; echo "exit $?"); tail -2 "$(ls -t "$CL"/.writ/state/eval-*.md | head -1)"`
5. `reset`

**Expected Result:**
- Step 1: no `failed` in the summary. Story 4 recorded 3436 passed and 3 skipped, plus one failure that occurs only while `agents/review-agent.md` is uncommitted (`test_review_agent_not_in_story_edit_set`); a clean clone does not have it. Later merges on the phase branch may change the counts.
- Step 2: only `bash loop done`; no `FAIL` line.
- Step 3: `pass`; then `pass` and `gen-platform-trees: pass (0 stale, 0 missing, 0 orphan, 0 unmapped, 0 vendor)`.
- Step 4: `exit 0`, then `- Findings: 0` and `- Run errors: 0`.
- Step 5: prints nothing.

**Implementation Reference:** Story 4 — WWB Test Results

**Status:** [ ] Pass  [ ] Fail

**Notes:**

---

### Scenario 37: A missing or malformed blast radius or test run lowers the rung instead of making the verifier unverifiable

**Source:** Error Map "`safety-fact` reads blast radius" and "`safety-fact` reads tests output" — Story 4; State Catalog "Blast radius unverifiable"
**Feature:** none
**Verification:** human — no recipe

**Preconditions:**
- Setup block pasted. `ls "$W/no-such-tests.txt" 2>&1` reports no such file.

**Steps:**
1. `rv "$W/r.md" PASS yes traced 'traced: src/other.py:1 — sets x'; sfv "$W/r.md" --tests-output "$W/tests-ok.txt"`
2. `sfv "$W/r.md" --blast-radius "$W/blast-bad.json" --tests-output "$W/tests-ok.txt"; sfv "$W/r.md" --blast-radius "$W/blast-unverifiable.json" --tests-output "$W/tests-ok.txt"`
3. `rv "$W/r.md" PASS yes traced 'traced: none — searched for parse( in src/'; sfv "$W/r.md" --tests-output "$W/tests-ok.txt"`
4. `rv "$W/r.md" PASS yes traced 'traced: src/missing.py:1 — no such file'; sfv "$W/r.md" --blast-radius "$W/blast-unverifiable.json" --tests-output "$W/tests-ok.txt"`
5. `rv "$W/r.md" PASS yes tested 'tested: tests/test_lib.py::LibTests::test_rejects_empty'; sfv "$W/r.md" --blast-radius "$W/blast.json" --tests-output "$W/tests-fail.txt"; sfv "$W/r.md" --blast-radius "$W/blast.json" --tests-output "$W/no-such-tests.txt"`
6. `rv "$W/r.md" PASS yes tested 'traced: src/caller.py:3 — passes [1, 2]' 'tested: tests/test_lib.py::LibTests::test_rejects_empty'; sfv "$W/r.md" --blast-radius "$W/blast.json" --tests-output "$W/tests-fail.txt"`

**Expected Result:**
- Step 1: `pass`, `rung: claimed=traced measured=traced`, `exit 0`. With no blast radius, any cited caller that exists counts.
- Step 2: twice the same `pass` result: a malformed file and an `unverifiable` blast radius both fall back to "a cited caller that exists".
- Step 3: `fail`, `rung: claimed=traced measured=claimed`, `reason: safety_fact_below_floor claimed`, `exit 1`. `none` needs a readable `pass` blast radius.
- Step 4: `fail`, `rung: claimed=traced measured=claimed`, `exit 1`. A missing caller never counts.
- Step 5: twice `fail`, `rung: claimed=tested measured=claimed`, `reason: safety_fact_below_floor claimed`, `exit 1`. No `exit code: 0` line, or no test run at all, rejects `tested`; line 1 is `fail`, not `unverifiable`.
- Step 6: `pass`, `rung: claimed=tested measured=traced`, `exit 0`. The rung falls to the next accepted one.

**Implementation Reference:** Story 4 — Files: `scripts/review-override.py` (`_consumer_union`, `_tested_ok`)

**Status:** [ ] Pass  [ ] Fail

**Notes:**

---

### Scenario 38: The story-report line has no State Catalog suffixes, and the verifier's lines carry the outcome (DEV-012)

**Source:** Experience Design State Catalog (all `safety-fact:` rows) — Story 4; DEV-012 (Medium, flagged for review)
**Feature:** none
**Verification:** human — no recipe

**Preconditions:**
- Setup block pasted; `reset` prints nothing.

**Steps:**
1. `sed -n '/^### State Catalog/,/^### Interaction Patterns/p' "$CL/$SPEC/spec.md" | grep 'safety-fact'`
2. `sed -n '/^\*\*Safety fact/,/^\*\*Jev shadow/p' "$CL/commands/implement-story.md" | grep -o 'Report .*'`
3. `grep -c -- '— below floor\|— does not hold\|— contradicts verdict\|safety-fact: missing\|safety-fact: unverifiable' "$CL/commands/implement-story.md"`
4. `rv "$W/r.md" PASS yes traced 'read: src/lib.py:2'; sfv "$W/r.md" "${BT[@]}"`
5. `rv "$W/r.md" PASS no traced 'traced: src/caller.py:3 — passes [1, 2]'; sfv "$W/r.md" "${BT[@]}"`
6. `grep -n -A6 '^#### \[DEV-012\]' "$CL/$SPEC/drift-log.md" | cut -c1-200`

**Expected Result:**
- Step 1: eight State Catalog rows, among them `safety-fact: traced (claimed traced) — <fact> — does not hold`, `safety-fact: … — contradicts verdict`, `safety-fact: missing`, `safety-fact: read (claimed traced) — <fact> — below floor`, and `safety-fact: unverifiable (<reason>)`.
- Step 2: ``Report `safety-fact: <measured> (claimed <claimed>) — <fact>`, else `safety-fact: off` or `safety-fact: not on route`.`` This is the shipped form.
- Step 3: `0`. Gate 3 carries none of the suffixes or the `missing` and `unverifiable` report forms; for `unverifiable` it says only "print the reason".
- Step 4: `fail`, `rung: claimed=traced measured=read`, `fact: no caller passes an empty list to parse()`, `reason: safety_fact_below_floor read`, `review-override safety-fact: fail (measured read, floor traced)`, `exit 1`. From these lines Gate 3 reports `safety-fact: read (claimed traced) — no caller passes an empty list to parse()`; the State Catalog would add ` — below floor`. The outcome is on line 1 and the `reason:` line, which the removal-measurement spec reads.
- Step 5: `fail`, `rung: claimed=traced measured=traced`, `reason: safety_fact_contradicts_verdict`, `exit 1`. The report line would read `safety-fact: traced (claimed traced) — <fact>`, with no ` — contradicts verdict`.
- Step 6: DEV-012, Severity Medium, Resolution "Flagged for review"; the 1,800-byte cap left 5 bytes, too few for the suffixes.
- **Decision owed (DEV-012).** Either amend the State Catalog to the shipped form, or add ` — <reason>` on a fail and trim elsewhere in Gate 3 to stay under the cap. Record the decision in Notes.

**Implementation Reference:** Story 4 — `.writ/specs/2026-10-25-review-route-rigor/drift-log.md` DEV-012

**Status:** [ ] Pass  [ ] Fail

**Notes:**

---

### Scenario 39: Live — risk route with both switches absent: a blast radius, a verified safety fact, and three report lines

**Source:** Experience Design Happy Path, Moment of Truth, Feedback Model, State Catalog "Risk route, fact at or above floor" — Story 4; AC-4.4; AC-3.5 (switch on); AC-2.2 (`review-agent`); Shadow Path "Gate 3 routing" (happy path); switch states: Safety Fact absent, Reviewer Filters absent
**Feature:** none
**Verification:** human — no recipe

**Preconditions:**
- Setup block pasted in both shells; `fxreset` prints nothing.
- `fsw - -` prints only `8:- **Gate 0 Divergence:** off`.
- `live` running in a new session.

**Steps:**
1. `/implement-story .writ/specs/2026-10-29-uat-review-rigor/user-stories/story-1-reject-negative-weight.md`
2. Let Gates 0 to 3 run. When the session moves past Gate 3, press Escape and reply: `Stop here. Print the gate3-route, reviewer-filters, and safety-fact lines this run will put in the story report, and the safety-fact verifier's output.`
3. Open the `review-agent` spawn in the transcript (ctrl+o) and note which skill files it read.
4. In the first shell: `cat "$FX/.writ/state/blast-radius-story-1-reject-negative-weight.json"; echo; grep -n '^command:\|^exit code:' "$FX/.writ/state/gate3-tests-story-1-reject-negative-weight.txt"`
5. `sed -n '/^#* *Safety Fact *$/,/^#/p' "$FX/.writ/state/gate3-review-story-1-reject-negative-weight.md"`
6. `(cd "$FX" && python3 scripts/review-override.py safety-fact --review-output .writ/state/gate3-review-story-1-reject-negative-weight.md --repo . --blast-radius .writ/state/blast-radius-story-1-reject-negative-weight.json --tests-output .writ/state/gate3-tests-story-1-reject-negative-weight.txt; echo "exit $?")`
7. `fxreset`

**Expected Result:**
- Step 2, Gate 0: `gate0-divergence: off (config)` (the fixture's config line).
- Step 2, Gate 2.5, in this order: `classify` returns `full-stack`; `crossings` routes `review-agent` with reason `full_stack_surface`; `review-override.py switch --name safety-fact` prints `on` and `reason: no_config_line`; `change-surface.py blast-radius --changed <files> --repo .` writes `.writ/state/blast-radius-story-1-reject-negative-weight.json`.
- Step 2, Gate 3: `review-override.py switch --name reviewer-filters` runs once and prints `on` and `reason: no_config_line`. The `review-agent` spawn gets `reviewer_filters: on`, `safety_fact: on`, the blast-radius JSON (or its saved path) as `blast_radius`, and a recorded test run with a `command:` and an `exit code:` line. After `review-override.py check`, the session saves the two `gate3-*` files and runs `review-override.py safety-fact` with `--review-output`, `--repo .`, `--blast-radius`, and `--tests-output`.
- Step 2, the reply: `gate3-route: review-agent (full_stack_surface)`, `reviewer-filters: on`, and `safety-fact: <measured> (claimed <claimed>) — <fact>`, with `<measured>` `traced` or `tested` and no suffix after the fact (DEV-012). This is the spec's moment of truth: judge by eye that the fact is one sentence about the code (for example, that `order_total`, the only caller, passes the weight through and a negative weight now raises), not about the process ("the tests pass").
- Step 3: the agent read `skills/review-judgment-filters/SKILL.md` and `skills/blast-radius/SKILL.md`.
- Step 4: JSON with `"verdict": "pass"`, `"consumers"` mapping `uatfx/api/parcel_fee.py` to `["uatfx/api/orders.py"]`, `"tests"` mapping it to `["uatfx/tests/test_orders.py"]`, `"truncated": []`, and `"reasons": []`. The changed test file `uatfx/tests/test_parcel_fee.py` is not a key. Then a `command:` line naming the story's test files and `exit code: 0`.
- Step 5: `### Safety Fact` with `**Fact:**`, `**Holds:** yes`, `**Rung:**`, `**Evidence:**`, and at least one `traced:` line citing `uatfx/api/orders.py:<line>` or a `tested:` line naming a test in `uatfx/tests/`.
- Step 6: line 1 `pass`, then `rung: claimed=<c> measured=<m>`, `fact: <the fact>`, no `reason:` line, `review-override safety-fact: pass (measured <m>, floor traced)`, `exit 0`, matching the Step 2 reply.
- If the first verifier run printed `fail` with `safety_fact_missing` or `safety_fact_below_floor`, the transcript shows exactly one re-spawn of `review-agent` with the `rung:` and `reason:` lines appended, then a second verifier run, and no Gate 1 run between them. That is the designed path; record it in Notes.
- Step 7: prints nothing.

**Status:** [ ] Pass  [ ] Fail

**Notes:**

---

### Scenario 40: Live — risk route with both switches `off`: no blast radius, no skill reads, no verifier

**Source:** Experience Design State Catalog "`safety-fact` switch off" and "`reviewer-filters` switch off" — Story 4; AC-4.5 (switch off); AC-3.5 (switch off); AC-2.3; Experience Design "Who uses it" (the removal trial's off arm); switch states: Safety Fact `off`, Reviewer Filters `off`
**Feature:** none
**Verification:** human — no recipe

**Preconditions:**
- Setup block pasted in both shells; `fxreset` prints nothing.
- `fsw off off` prints `8:- **Safety Fact:** off`, `9:- **Reviewer Filters:** off`, `10:- **Gate 0 Divergence:** off`.
- `live` running in a new session.

**Steps:**
1. `/implement-story .writ/specs/2026-10-29-uat-review-rigor/user-stories/story-1-reject-negative-weight.md`
2. Let Gates 0 to 3 run. When the session moves past Gate 3, press Escape and reply: `Stop here. Print the gate3-route, reviewer-filters, and safety-fact lines this run will put in the story report.`
3. Open the `review-agent` spawn in the transcript (ctrl+o) and note which skill files it read and whether its output has a Safety Fact section.
4. In the first shell: `ls "$FX/.writ/state/" | grep -c '^blast-radius-'`
5. `fxreset`

**Expected Result:**
- Step 2, Gate 2.5: `crossings` routes `review-agent` with reason `full_stack_surface`; `review-override.py switch --name safety-fact` prints `off` and `reason: config_off`; no `blast-radius` command runs.
- Step 2, Gate 3: `review-override.py switch --name reviewer-filters` prints `off` and `reason: config_off`. The `review-agent` spawn gets `reviewer_filters: off`, `safety_fact: off`, and `blast_radius: (none)`. No `review-override.py safety-fact` command runs.
- Step 2, the reply: `gate3-route: review-agent (full_stack_surface)`, `reviewer-filters: off`, `safety-fact: off`. A missing `safety-fact:` line is a Fail (Known risk).
- Step 3: the agent read neither `skills/review-judgment-filters/SKILL.md` nor `skills/blast-radius/SKILL.md`, and its output has no Fact, Holds, Rung, or Evidence fields. This is the removal trial's off arm: the prompt carries no filter or ladder text (Scenarios 14 and 34 check the files).
- Step 4: `0`.
- Step 5: prints nothing.

**Status:** [ ] Pass  [ ] Fail

**Notes:**

---

### Scenario 41: Live — risk route with both switches malformed: both read as on, and the report shows the arm did not switch

**Source:** Experience Design State Catalog "Config line with a bad value" — Story 4; Error Map "`switch` parses value" (end to end); AC-1.3; switch states: Safety Fact malformed, Reviewer Filters malformed
**Feature:** none
**Verification:** human — no recipe

**Preconditions:**
- Setup block pasted in both shells; `fxreset` prints nothing.
- `fsw of of` prints `8:- **Safety Fact:** of`, `9:- **Reviewer Filters:** of`, `10:- **Gate 0 Divergence:** off`.
- `live` running in a new session.

**Steps:**
1. `/implement-story .writ/specs/2026-10-29-uat-review-rigor/user-stories/story-1-reject-negative-weight.md`
2. Let Gates 0 to 3 run. When the session moves past Gate 3, press Escape and reply: `Stop here. Print the gate3-route, reviewer-filters, and safety-fact lines this run will put in the story report, and the output of both switch commands.`
3. In the first shell: `ls "$FX/.writ/state/" | grep -c '^blast-radius-story-1-reject-negative-weight.json$'`
4. `fxreset`

**Expected Result:**
- Step 2, Gate 2.5: `review-override.py switch --name safety-fact` prints `on` and `reason: malformed_value of`, and blast-radius runs.
- Step 2, Gate 3: `review-override.py switch --name reviewer-filters` prints `on` and `reason: malformed_value of`. The `review-agent` spawn gets `reviewer_filters: on` and `safety_fact: on`, reads both skills, and the verifier runs.
- Step 2, the reply: `gate3-route: review-agent (full_stack_surface)`, `reviewer-filters: on`, and `safety-fact: <measured> (claimed <claimed>) — <fact>`, not `safety-fact: off`. A trial operator who meant `off` reads `on` in the report and `malformed_value of` in the switch output: the arm did not switch.
- Step 3: `1`.
- Step 4: prints nothing.

**Status:** [ ] Pass  [ ] Fail

**Notes:**

---

### Scenario 42: Live — evaluator route with both switches `on`: `safety-fact: not on route`, filters on

**Source:** Experience Design State Catalog "Evaluator route" — Story 4; AC-4.5 (evaluator route); AC-3.5 (evaluator route); AC-2.2 (`evaluator-agent`); Business Rule "When the safety fact applies" (default run, `evaluator-agent`); switch states: Safety Fact `on`, Reviewer Filters `on`
**Feature:** none
**Verification:** human — no recipe

**Preconditions:**
- Setup block pasted in both shells; `fxreset` prints nothing.
- `fsw on on` prints `8:- **Safety Fact:** on`, `9:- **Reviewer Filters:** on`, `10:- **Gate 0 Divergence:** off`.
- `live` running in a new session.

**Steps:**
1. `/implement-story .writ/specs/2026-10-29-uat-review-rigor/user-stories/story-2-trim-greeting-name.md`
2. Let Gates 0 to 3 run. When the session moves past Gate 3, press Escape and reply: `Stop here. Print the gate3-route, reviewer-filters, and safety-fact lines this run will put in the story report.`
3. Open the `evaluator-agent` spawn in the transcript (ctrl+o) and note which skill files it read.
4. In the first shell: `ls "$FX/.writ/state/" | grep -c '^blast-radius-'`
5. `fxreset`

**Expected Result:**
- Step 2, Gate 2.5: `classify` returns `cross-component`; `crossings` routes `evaluator-agent` with no reasons. No `switch --name safety-fact` and no `blast-radius` command run: Gate 2.5 resolves that switch only on the `review-agent` route.
- Step 2, Gate 3: `review-override.py switch --name reviewer-filters` prints `on` and `reason: config_on`. The `evaluator-agent` spawn gets `reviewer_filters: on` and no `safety_fact` or `blast_radius` input. No `review-override.py safety-fact` command runs.
- Step 2, the reply: `gate3-route: evaluator-agent`, `reviewer-filters: on`, `safety-fact: not on route`. A missing `safety-fact:` line is a Fail (Known risk).
- Step 3: the evaluator read `skills/review-judgment-filters/SKILL.md` before setting EVALUATION_RESULT, and did not read `skills/blast-radius/SKILL.md`.
- Step 4: `0`.
- Step 5: prints nothing.
- If Gate 2.5 routed `review-agent` because the coding agent touched a file the story does not list, the scenario does not apply: note the `gate3-route` reasons, run `fxreset`, and run it again.

**Status:** [ ] Pass  [ ] Fail

**Notes:**

---

## Pending Stories

None. All four stories are Completed ✅.
