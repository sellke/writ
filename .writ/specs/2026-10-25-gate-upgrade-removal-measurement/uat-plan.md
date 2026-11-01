# UAT Plan: Gate Upgrade Removal Measurement

> **Generated:** 2026-10-29
> **Spec:** `.writ/specs/2026-10-25-gate-upgrade-removal-measurement/`
> **Stories Covered:** 3 of 4 completed (Story 4 waits on the human labels)
> **Total Scenarios:** 23
> **Merged:** `6b3267a` on `phase/15-code-level-rigor`
> **Verification recipe:** none. No `.writ/docs/app-verification.md` exists, and Writ has no app to launch: its checks (pytest, the bash tests, `scripts/eval.sh`) read markdown, not a running process. With no launch command detected, Step 1.3's recommended answer is skip, so no recipe was drafted, saved, or bound. Every scenario is `human — no recipe`.

## How to Use This Plan

1. Work through scenarios in order (they're grouped by story, ordered by priority)
2. For each scenario, follow the steps exactly as written
3. Mark Pass or Fail — add notes for any unexpected behavior
4. Scenarios marked Fail should be filed as issues or fed back to the spec
5. A feature passes UAT when all scenarios pass (or failures are accepted as known limitations)

**Conventions for this plan:**

- **Four kinds of scenario.** **Harness** scenarios (1 to 12) drive the clone's copy of `.writ/eval/gate-upgrade-trial/gate-upgrade-trial.py` on a throwaway stand-in repo (`$W/yuss-standin`) and on the harness's own test fixtures (`$W/fx`), never on the real trial. **Read and check** scenarios (13 to 19) read the committed real trial, sheet, handoff, and drift log in the clone and run the repository's own tests. **Live** Scenario 20 runs `/implement-story` in a Claude Code session inside the clone. **Human handoff** scenarios (21 to 23) run in the primary checkout: 21 is the labeling, 22 and 23 check the Story 4 run that follows it.
- **Keep the labeling blind.** Scenario 21 is the labeling, and the labeler (the maintainer) is likely the person running this plan. Before Scenario 21, do not open the real trial JSON, the raw outputs under `.writ/state/gate-upgrade-trial/<story slug>/`, or the excerpt files. Scenarios 13 to 20 print only counts, arm names, routes, switch states, and verdict words from the real trial, never which upgrade raised a given finding ID. Scenarios 22 and 23 are **After labeling**.
- **yuss is never written.** Harness refusal cases use the stand-in at `$W/yuss-standin`. Only Scenarios 17, 18, and 21 read `/Users/asellke/Projects/yuss`, with `git show`, `rev-parse`, `show-ref`, `for-each-ref`, `worktree list`, and `status --porcelain` under `GIT_OPTIONAL_LOCKS=0` (no index refresh). Never run `checkout`, `fetch`, `stash`, `reset`, or an editor in yuss as part of this plan.
- **Where each scenario runs.** Scenarios 1 to 20 run in a scratch clone pinned at `6b3267a`, the tree as merged, so they describe what was built even after Story 4 later removes upgrades or deletes the harness. Only Scenarios 21 to 23 write to the primary checkout (`$REPO`); Scenario 17 lists its gitignored state folder read-only. **Never run `install.sh` or `update.sh` in the Writ repo.** `.claude/` and `.cursor/` there are symlinks into the source; the clone keeps them, so `/implement-story` is a project command inside `$CL` with nothing installed.
- Every helper refuses to run unless the shell is inside `$W`, and every helper script that writes refuses a path outside the scratch folder. Run the plan in `bash` on macOS (`sed -i ''`), outside any sandbox, with `claude`, `uv`, and `rg` on `PATH`. Every fixture `record` and `sheet` call passes `--state-dir "$W/fx/state"`; without it the harness would write into a primary checkout's `.writ/state/`. Claude Code asks whether to trust a new scratch folder the first time a session opens there; accept it.
- Expected results come from the spec, the three What Was Built records, the drift log, `rating-handoff.md`, and the tree at `6b3267a`. Story 1 landed in `2d1f3e5`, Story 2 in `5935516`, Story 3 in `4542d78`. None of these scenarios has been run for this plan. `…` in an expected path stands for the scratch folder prefix. After each scenario that edits the clone, run `reset` and confirm it prints nothing. When done: `rm -rf "$W"`.
- **Expected failure.** Scenario 14 is expected to fail at Step 1: Story 3 ran `init` while `2026-10-25-design-divergence` was not complete, which AC-3.2 and task 3.2 forbid (DEV-007, Medium, flagged for review). Mark it Fail, or accept DEV-007 as a known limitation and say so in Notes.
- **Drift.** DEV-001 (`init --yuss`, `repo_missing`, `yuss_missing`; Scenarios 2 and 3), DEV-002 (stricter `prepare` input checks; Scenario 5), DEV-003 (`prepare` writes `tests.txt` and `routes.json`, prints `gate0_reason:`; Scenarios 3, 4, 6), DEV-004 (`snapshot` subcommand; Scenario 3), DEV-005 (extra refusals, including `sheet_stale`; Scenario 9), DEV-006 (`blinding:` report line and per-arm evidence fields; Scenarios 10 and 16), DEV-007 (Medium: the trial ran before design-divergence was Complete; Scenario 14), DEV-008 (`- [ ] Unmet:` line in the Gate 0 comparison prompt; Scenario 15), DEV-009 (`Targets:` and `Repro: none:` in the repro prompt; Scenario 15), DEV-010 (`tests.txt` hand-written for two stories; Scenarios 4 and 18), DEV-011 (removal-inventory corrections Story 4 must apply; Scenarios 19 and 23).

**Setup.** Paste this block once in the first shell. Stop if the first line does not print `W=/...`.

```bash
# First shell: paste as is. Second shell (Scenario 20): run UAT_W=<the W path the first shell printed>, then paste.
W=${UAT_W:-$(mktemp -d "${TMPDIR:-/tmp}/writ-uat-gate-trial.XXXXXX")} && cd "$W" && W=$PWD && echo "W=$W"
REPO=/Users/asellke/Projects/writ   # primary checkout: only Scenarios 21 to 23 write to it
YUSS=/Users/asellke/Projects/yuss   # never written; Scenarios 17, 18, 21 read it with GIT_OPTIONAL_LOCKS=0
CL="$W/clone"; [ -d "$CL/.git" ] || { git clone -q "$REPO" "$CL" && git -C "$CL" checkout -q 6b3267a; }
SPEC=.writ/specs/2026-10-25-gate-upgrade-removal-measurement
TD=.writ/eval/gate-upgrade-trial
TRIAL=$TD/2026-10-29-gate-upgrade-trial.json
H="$CL/$TD/gate-upgrade-trial.py"
FX="$CL/scripts/tests/fixtures/gate-upgrade-trial"
B0="$CL/.writ/eval/baselines/2026-09-07-claude-fable-5-1.json"
V="$FX/verifier-pass.txt"
S1=2026-01-01-alpha/story-1-api
RUN="$W/runs/writ-gate-trial-2026-01-01-alpha--story-1-api"
FT="$W/fx/trial.json"
CHOSE="gate0-divergence: chose B (sketch B keeps the ledger in one module)"
SKIP="gate0-divergence: skip (sketch incomplete: sketch A has no Files line)"
inW() { case "$PWD/" in "$W"/*) ;; *) echo "refusing: $PWD is outside $W" >&2; return 1;; esac; }
# gt <args>: the trial harness from the clone (never the primary checkout's copy)
gt() { inW && python3 "$H" "$@"; }
# rc <command...>: run it, keep its stdout in $W/out.txt, print its exit code and stdout size; stderr shows
rc() { inW || return 1; "$@" > "$W/out.txt"; local s=$?; echo "exit $s stdout-bytes $(wc -c < "$W/out.txt" | tr -d ' ')"; }
# pt <pytest args>: pytest on Python 3.9 inside the clone
pt() { inW && (cd "$CL" && uv run --python 3.9 pytest "$@"); }
# reset: undo every edit in the clone and drop untracked files; prints nothing when clean
reset() { inW && git -C "$CL" checkout -q -- . && git -C "$CL" clean -qfd && git -C "$CL" status --short; }
h12() { shasum -a 256 "$1" | cut -c1-12; }
# ysnap <repo>: one hash over HEAD, refs, worktrees, and porcelain status; read-only (no index refresh)
ysnap() { (export GIT_OPTIONAL_LOCKS=0; { git -C "$1" rev-parse HEAD; git -C "$1" for-each-ref; git -C "$1" worktree list --porcelain; git -C "$1" status --porcelain; } | shasum -a 256 | cut -c1-12); }
# live: Claude Code inside the clone
live() { inW && (cd "$CL" && claude); }
# tf [trial]: labeled_by, how many upgrade-only findings have no label, and the acks; never an ID (default: the clone's real trial)
tf() { python3 -c 'import json,sys; d=json.load(open(sys.argv[1])); f=[e for s in d["stories"] for e in s["upgrade_only"]]; print("labeled_by=%s null_labels=%d of %d acks=%s" % (d["labeled_by"], sum(e["label"] is None for e in f), len(f), d["acks"]))' "${1:-$CL/$TRIAL}"; }

cat > "$W/standin.py" <<'PY'
# standin.py DIR [init|no-results|no-paths]: a throwaway git repo that stands in for yuss.
#   init: base -> parent -> story commit (story 1 plans lib/payments.py and has Test Results); prints "base parent commit"
#   no-results: one more story commit whose story file has no What Was Built; prints "parent commit"
#   no-paths: one more story commit whose task names no file; prints "parent commit"
import os, subprocess, sys
root, mode = os.path.realpath(sys.argv[1]), (sys.argv[2] if len(sys.argv) > 2 else "init")
if "writ-uat-gate-trial." not in root or os.path.basename(root) != "yuss-standin":
    sys.exit("refusing: the stand-in lives only at $W/yuss-standin, never in the real yuss")
STORY = ".writ/specs/2026-01-01-alpha/user-stories/story-1-api.md"
SPEC = ".writ/specs/2026-01-01-alpha/spec.md"
PAYMENTS = "- [x] 1.1 Round amounts in `lib/payments.py` [AC-1.1]"
NO_PATHS = "- [x] 1.1 Round every amount to whole cents [AC-1.1]"
BUILT = ("## What Was Built\n\n### Test Results\n\n- 12 passed in 0.4s\nexit code: 0\n"
         "- coverage 91%\n\n### Files Changed\n\n- lib/payments.py\n")
def story(task, built=BUILT):
    return "# Story 1: API\n\n> **Status:** Completed ✅\n\n## Implementation Tasks\n\n%s\n\n%s" % (task, built)
def git(*args):
    return subprocess.run(["git", "-C", root, "-c", "user.name=uat", "-c", "user.email=uat@example.com",
                           "-c", "commit.gpgsign=false", "-c", "core.hooksPath=/dev/null", *args],
                          check=True, capture_output=True, text=True).stdout.strip()
def commit(files, message):
    for rel, text in files.items():
        path = os.path.join(root, rel)
        os.makedirs(os.path.dirname(path), exist_ok=True)
        with open(path, "w", encoding="utf-8") as handle:
            handle.write(text)
    git("add", "-A")
    git("commit", "-q", "-m", message)
    return git("rev-parse", "HEAD")
if mode == "init":
    os.makedirs(root)
    git("init", "-q")
    base = commit({SPEC: "# Alpha\n\n## Specification Contract\n\nDeliverable: a payment helper.\n\n"
                         "## Detailed Requirements\n\nnot part of the contract\n",
                   STORY: story(PAYMENTS, built=""),
                   "lib/payments.py": "def pay(amount):\n    return amount\n",
                   "lib/other.py": "VALUE = 1\n",
                   "app/checkout.py": "from lib import payments\n\nprint(payments.pay(3))\n",
                   "tests/test_payments.py": "from lib import payments\n"}, "base")
    parent = commit({"README.md": "stand-in\n"}, "parent")
    print(base, parent, commit({"lib/payments.py": "def pay(amount):\n    return round(amount, 2)\n",
                                "lib/other.py": "VALUE = 2\n", STORY: story(PAYMENTS)}, "story 1"))
else:
    parent = git("rev-parse", "HEAD")
    files = ({STORY: story(PAYMENTS, built=""), "lib/payments.py": "def pay(a):\n    return a\n"}
             if mode == "no-results" else {STORY: story(NO_PATHS), "lib/other.py": "VALUE = 3\n"})
    print(parent, commit(files, mode))
PY
cat > "$W/retarget.py" <<'PY'
# retarget.py IN OUT COMMIT PARENT: copy a baseline or trial file with story 1 pointed at COMMIT and PARENT
import json, os, sys
src, out, commit, parent = sys.argv[1:5]
if "writ-uat-gate-trial." not in os.path.realpath(out):
    sys.exit("refusing: %s is outside the UAT scratch folder" % out)
d = json.load(open(src, encoding="utf-8"))
for s in d.get("selection") or d.get("stories"):
    if s["story_id"] == "2026-01-01-alpha/story-1-api":
        s["story_commit"], s["parent_sha"] = commit, parent
with open(out, "w", encoding="utf-8") as handle:
    handle.write(json.dumps(d, indent=2, sort_keys=True) + "\n")
PY
cat > "$W/bl.py" <<'PY'
# bl.py BASELINE DIR: four bad copies of the real baseline (three stories, a non-hex SHA, an unsafe path, broken JSON)
import json, os, sys
src, out = sys.argv[1:3]
if "writ-uat-gate-trial." not in os.path.realpath(out):
    sys.exit("refusing: %s is outside the UAT scratch folder" % out)
os.makedirs(out, exist_ok=True)
def save(name, change):
    d = json.load(open(src, encoding="utf-8"))
    change(d)
    with open(os.path.join(out, name), "w", encoding="utf-8") as handle:
        handle.write(json.dumps(d))
save("three.json", lambda d: d.update(selection=d["selection"][:3]))
save("badsha.json", lambda d: d["selection"][0].update(story_commit="z" * 40))
save("unsafe.json", lambda d: d["selection"][1].update(story_path="../outside/story.md"))
with open(os.path.join(out, "broken.json"), "w", encoding="utf-8") as handle:
    handle.write("{")
PY
cat > "$W/routes.py" <<'PY'
# routes.py TRIAL: write the unit tests' default routes into a FIXTURE trial (no prepare)
import json, os, sys
path = sys.argv[1]
if "writ-uat-gate-trial." not in os.path.realpath(path):
    sys.exit("refusing: %s is outside the UAT scratch folder" % path)
RR = {"surface": "full-stack", "gate3_route": "review-agent", "planned_surface": "full-stack", "gate0_route": "review-agent"}
RE = dict(RR, planned_surface="cross-component", gate0_route="evaluator-agent")
ER = {"surface": "single-component", "gate3_route": "evaluator-agent", "planned_surface": "full-stack", "gate0_route": "review-agent"}
RS = {"surface": "cross-component", "gate3_route": "review-agent", "planned_surface": None, "gate0_route": "skip",
      "gate0_reason": "unverifiable: no planned files"}
ids = ["2026-01-01-alpha/story-1-api", "2026-01-02-beta/story-2-ui", "2026-01-03-gamma/story-3-db", "2026-01-04-delta/story-4-lib"]
routes = dict(zip(ids, [RR, RE, ER, RS]))
d = json.load(open(path, encoding="utf-8"))
for s in d["stories"]:
    s["routes"] = routes[s["story_id"]]
with open(path, "w", encoding="utf-8") as handle:
    handle.write(json.dumps(d, indent=2, sort_keys=True) + "\n")
PY
cat > "$W/fill.py" <<'PY'
# fill.py BLANK OUT LABEL ACK [--note TEXT] [VALID_KEY ...]: fill a FIXTURE sheet. Every label is LABEL except findings
# whose key is a VALID_KEY (those read valid); every ack is ACK; --note goes on the first finding only.
import os, sys
blank, out, label, ack, rest = sys.argv[1], sys.argv[2], sys.argv[3], sys.argv[4], sys.argv[5:]
note = None
if rest[:1] == ["--note"]:
    note, rest = rest[1], rest[2:]
for path in (blank, out):
    if "writ-uat-gate-trial." not in os.path.realpath(path):
        sys.exit("refusing: fill.py fills fixture sheets in the UAT scratch folder only, never the real sheet")
key, lines = None, []
for line in open(blank, encoding="utf-8").read().split("\n"):
    if line.startswith("key: "):
        key = line[len("key: "):]
    if line == "label:":
        line = "label: " + ("valid" if key in rest else label)
    elif line == "note:" and note is not None:
        line, note = "note: " + note, None
    elif line == "ack:":
        line = "ack: " + ack
    lines.append(line)
with open(out, "w", encoding="utf-8") as handle:
    handle.write("\n".join(lines))
PY
cat > "$W/arms.py" <<'PY'
# arms.py TRIAL: per story, its routes, the arms recorded in pipeline order, the safety-fact verifier word, the Gate 0
# report word, and the repro kind; then how many arms turned on only their own switch. Prints no key and no ID.
import json, sys
ARMS = ("off-1", "off-2", "reviewer-filters", "safety-fact", "gate0-divergence", "repro-first")
d = json.load(open(sys.argv[1], encoding="utf-8"))
total = own = 0
for s in d["stories"]:
    arms, routes = s["arms"], s["routes"] or {}
    total += len(arms)
    own += sum(all(v == ("on" if k == name else "off") for k, v in arms[name]["states"].items()) for name in arms)
    print("%s: gate3=%s gate0=%s | %s | verifier=%s gate0-report=%s repro=%s" % (
        s["story_id"], routes.get("gate3_route"), routes.get("gate0_route"),
        " ".join(a for a in ARMS if a in arms), (arms.get("safety-fact") or {}).get("verifier", "-"),
        (arms.get("gate0-divergence") or {}).get("report", "-"), s["repro_kind"]))
print("origin=%s arms=%d own-switch-only=%d" % (d["origin"], total, own))
PY
cat > "$W/ycmp.py" <<'PY'
# ycmp.py TRIAL YUSS: compare yuss now with the trial file's `after` snapshot, taken the way the harness takes it
# (HEAD, sha256 of `git show-ref`, sha256 of `git status --porcelain`). Read-only: GIT_OPTIONAL_LOCKS=0.
import hashlib, json, os, subprocess, sys
after = json.load(open(sys.argv[1], encoding="utf-8"))["yuss_snapshot"]["after"]
env = dict(os.environ, GIT_OPTIONAL_LOCKS="0")
def run(*args):
    return subprocess.run(["git", "-C", sys.argv[2], *args], capture_output=True, env=env).stdout
now = {"head": run("rev-parse", "--verify", "HEAD").decode().strip(),
       "refs_sha256": hashlib.sha256(run("show-ref")).hexdigest(),
       "status_sha256": hashlib.sha256(run("status", "--porcelain")).hexdigest()}
print(" ".join("%s=%s" % (k, "same" if now[k] == after[k] else "differs") for k in ("head", "refs_sha256", "status_sha256")))
PY

# bl: the four bad baselines in $W/bl
bl() { inW && python3 "$W/bl.py" "$B0" "$W/bl" && ls "$W/bl"; }
# sb: a fresh stand-in yuss ($W/yuss-standin) and a stand-in trial ($W/sb/trial.json) from the mini baseline with
#     story 1 pointed at it; init records the stand-in's before-snapshot. Sets BASE, PARENT, COMMIT.
sb() { inW || return 1; rm -rf "$W/yuss-standin" "$W/sb" "$W/runs" && mkdir -p "$W/sb" "$W/runs" || return 1
  local out; out=$(python3 "$W/standin.py" "$W/yuss-standin") || return 1; set -- $out; BASE=$1 PARENT=$2 COMMIT=$3
  python3 "$W/retarget.py" "$FX/mini-baseline.json" "$W/sb/baseline.json" "$COMMIT" "$PARENT" \
  && gt init --baseline "$W/sb/baseline.json" --out "$W/sb/trial.json" --repo "$CL" --yuss "$W/yuss-standin" | grep -E '^(yuss|gate-upgrade-trial):'; }
# sp [story] [yuss]: prepare one story of the stand-in trial into $W/runs
sp() { gt prepare --trial "$W/sb/trial.json" --story "${1:-$S1}" --yuss "${2:-$W/yuss-standin}" --tmp-root "$W/runs"; }
# sv <no-results|no-paths>: add a story-1 variant commit to the stand-in and point the stand-in trial at it
sv() { inW || return 1; local out; out=$(python3 "$W/standin.py" "$W/yuss-standin" "$1") || return 1; set -- $out
  python3 "$W/retarget.py" "$W/sb/trial.json" "$W/sb/trial.json" "$2" "$1" && echo "story 1 now at ${2:0:12} (parent ${1:0:12})"; }
sid() { case $1 in 1) echo 2026-01-01-alpha/story-1-api;; 2) echo 2026-01-02-beta/story-2-ui;; 3) echo 2026-01-03-gamma/story-3-db;; 4) echo 2026-01-04-delta/story-4-lib;; esac; }
# fx: a FIXTURE trial at $FT from the mini baseline (fake SHAs, no prepare), routes written as the unit tests write them:
#     story 1 review-agent/review-agent, 2 review-agent/evaluator-agent, 3 evaluator-agent/review-agent, 4 review-agent/skip
fx() { inW && rm -rf "$W/fx" && mkdir "$W/fx" && gt init --baseline "$FX/mini-baseline.json" --out "$FT" --repo "$CL" >/dev/null \
  && python3 "$W/routes.py" "$FT" && echo "fixture trial: 4 stories, routes set, no arms"; }
# fr <story 1-4> <arm> <fixture file> [record flags]: record one FIXTURE arm with that arm's switch states
fr() { inW || return 1; local n=$1 arm=$2 out=$3; shift 3
  case $arm in
    off-1|off-2) set -- --state safety-fact=off --state reviewer-filters=off "$@";;
    reviewer-filters) set -- --state reviewer-filters=on --state safety-fact=off "$@";;
    safety-fact) set -- --state safety-fact=on --state reviewer-filters=off "$@";;
  esac
  gt record --trial "$FT" --story "$(sid "$n")" --arm "$arm" --output "$FX/$out" --state-dir "$W/fx/state" "$@"; }
# fxall: a fixture trial shaped like the real one: every applicable arm recorded, repro-first never a bug fix
fxall() { fx >/dev/null || return 1
  { fr 1 off-1 off-fail.md && fr 1 off-2 off-fail.md && fr 1 reviewer-filters filters-on.md \
    && fr 1 safety-fact safety-on.md --verifier "$V" && fr 1 gate0-divergence gate0-comparison.md --report-line "$CHOSE" \
    && fr 2 off-1 off-pass.md && fr 2 off-2 off-pass.md && fr 2 reviewer-filters off-pass.md \
    && fr 2 safety-fact safety-on-pass.md --verifier "$V" \
    && fr 3 off-1 off-pass.md && fr 3 off-2 off-pass.md && fr 3 reviewer-filters off-pass.md \
    && fr 3 gate0-divergence gate0-no-avoided.md --report-line "$SKIP" \
    && fr 4 off-1 off-fail.md && fr 4 off-2 off-fail.md && fr 4 reviewer-filters filters-on.md \
    && fr 4 safety-fact safety-on.md --verifier "$V" \
    && for n in 1 2 3 4; do fr $n repro-first repro-not-bug.md --kind not-a-bug-fix || return 1; done; } > /dev/null || return 1
  python3 -c 'import json,sys; d=json.load(open(sys.argv[1])); print("fixture trial: %d arms, %d upgrade-only findings" % (sum(len(s["arms"]) for s in d["stories"]), sum(len(s["upgrade_only"]) for s in d["stories"])))' "$FT"; }
# fsheet: the FIXTURE sheet with seed 7, plus a blank copy for fill
fsheet() { inW && gt sheet --trial "$FT" --out "$W/fx/labeling-sheet.md" --seed 7 --state-dir "$W/fx/state" && cp "$W/fx/labeling-sheet.md" "$W/fx/blank.md"; }
# fill <label> <ack> [--note TEXT] [valid key...]: refill the FIXTURE sheet from its blank copy
fill() { inW && python3 "$W/fill.py" "$W/fx/blank.md" "$W/fx/labeling-sheet.md" "$@"; }
flabel() { gt label --trial "$FT" --sheet "$W/fx/labeling-sheet.md" --labeled-by "${1-UAT Tester}"; }
frep() { gt report --trial "$FT" "$@"; }
# af <story 1-4> <arm> <field>: one field of a FIXTURE arm, as JSON
af() { python3 -c 'import json,sys; d=json.load(open(sys.argv[1])); s=[x for x in d["stories"] if x["story_id"]==sys.argv[2]][0]; print(json.dumps(s["arms"][sys.argv[3]].get(sys.argv[4])))' "$FT" "$(sid "$1")" "$2" "$3"; }
# drop <story 1-4> <arm>: delete one recorded arm from the FIXTURE trial
drop() { inW && python3 -c 'import json,sys; p=sys.argv[1]; d=json.load(open(p)); s=[x for x in d["stories"] if x["story_id"]==sys.argv[2]][0]; del s["arms"][sys.argv[3]]; open(p,"w").write(json.dumps(d, indent=2, sort_keys=True)+"\n")' "$FT" "$(sid "$1")" "$2"; }
echo "setup done: clone at $(git -C "$CL" rev-parse --short HEAD), $(ls "$W"/*.py | wc -l | tr -d ' ') helper scripts"
```

The last line should read `setup done: clone at 6b3267a, 7 helper scripts`. The stand-in mirrors the unit tests' stand-in: story 1 plans `lib/payments.py` but also changes `lib/other.py`, so Gate 2.5 routes it to review-agent while the Gate 0 predictor routes it to evaluator-agent.

## Coverage Summary

| Story | Status | Scenarios | Source Breakdown |
|-------|--------|-----------|-----------------|
| Story 1: Trial Harness: init and prepare | ✅ Covered | 6 | AC: 5, Errors: 1, Shadow: 0, Edge: 0 |
| Story 2: Trial Harness: record, sheet, label, and report | ✅ Covered | 6 | AC: 5, Errors: 0, Shadow: 1, Edge: 0 |
| Story 3: Run the Arms and Hand Off for Labeling | ✅ Covered | 7 | AC: 5, Errors: 0, Shadow: 0, Edge: 0, Drift: 2 |
| Human handoff: labeling and Story 4 follow-through | ⏳ Human step | 4 | Business Rule 9, `rating-handoff.md`, Story 4 AC-4.1 to AC-4.5, DEV-011 |
| Story 4: Act on the Labeled Trial (Human-Gated) | ⏳ Pending | — | Not Started; Scenarios 22 and 23 check its run |

- Folded rows. Error Map: `init` rows are Scenarios 1 and 2; `prepare` (yuss missing, SHA unreachable, parent beyond depth 2, `review-panel.py` missing or lacking a name) is Scenario 5; `prepare` (planned set empty or crossings `unverifiable`, `blast-radius` absent) is Scenario 6; every `record` row is Scenario 7; `sheet` (an applicable arm missing) is Scenario 11; every `label` row is Scenario 9; `report` (unlabeled, missing arm, missing ack) is Scenario 11; "Spawn (any arm)" is Scenario 15 (no arm failed); "Repro arm" is Scenario 8 Step 6 (a bug without its repro results is refused); "Story 4 — report `unverifiable`" is Scenario 13's outcome-test unit tests and Scenario 23.
- Shadow Paths: "Trial run" happy path is Scenarios 15 and 16, nil (no trial file) Scenarios 5 and 11, empty (no upgrade-only findings) the unit test `test_no_findings_and_three_acks` inside Scenario 12, upstream error (yuss unreachable) Scenario 5. "Report" happy path is Scenario 10, empty (no labels) Scenarios 11 and 16, upstream error (malformed trial) Scenario 11. "Story 4" nil (`labeled_by` null) is Scenario 20; empty (every verdict `keep`) and upstream error (a removal leaves `rg` hits) are Scenarios 22 and 23.
- Interaction Edge Cases: Gate 0 removed before `init` (`absent`) is Scenario 11 Step 3; Gate 0 removed after `init`, and this trial removing Gate 0 while the blind trial keeps the skill, are Scenario 23; both review-route upgrades removed and two removals editing `commands/implement-story.md` are Scenario 23; a Gate 0 finding whose sketch line does not avoid the defect is the label rule in Scenario 21. "An upgrade-only key equals a key another upgrade's arm raised" does not occur in the real trial (F01 to F06 are six distinct story and key pairs) and has no scenario.
- Experience Design: the entry point ("after its three dependencies are complete") is Scenario 14; the moment of truth (`upgrade:` lines) is Scenarios 10, 16, and 21; the feedback model (the `gate-upgrade-trial:` summary line, the awaiting-labels status) is Scenarios 16 and 17; the error experience is Scenarios 11 and 23.

---

## Story 1: Trial Harness: init and prepare

### Scenario 1: `init` writes a four-story skeleton from the real baseline and stores `present: false` for a probe that fails

**Source:** Acceptance Criteria (AC-1.1) — Story 1; Error Map `init` (presence probe fails)
**Feature:** none
**Verification:** human — no recipe

**Preconditions:**
- Setup block pasted.

**Steps:**
1. `rm -f "$W/i1.json"; rc gt init --baseline "$B0" --out "$W/i1.json" --repo "$CL"; cat "$W/out.txt"`
2. `python3 -c 'import json,sys; t=json.load(open(sys.argv[1])); b=json.load(open(sys.argv[2])); F=("story_id","story_path","spec_folder","story_commit","parent_sha"); print(t["schema"], [[s[f] for f in F] for s in t["stories"]] == [[s[f] for f in F] for s in b["selection"]], sum(len(s["arms"]) for s in t["stories"]), {s["routes"] for s in t["stories"]}, t["labeled_by"], t["yuss_snapshot"])' "$W/i1.json" "$B0"`
3. `mkdir -p "$W/halfrepo/commands" "$W/halfrepo/scripts" && printf '# no divergence block\n' > "$W/halfrepo/commands/implement-story.md" && touch "$W/halfrepo/scripts/repro-order.py"; rc gt init --baseline "$B0" --out "$W/i2.json" --repo "$W/halfrepo"; grep -E 'present=|^gate-upgrade-trial:' "$W/out.txt"`

**Expected Result:**
- Step 1: `exit 0 stdout-bytes …`, then:
  - `pass`
  - `story: 2026-07-24-per-event-fee-revenue-model/story-2-event-creation-payment-flow 79d79ae4a2fb`
  - `story: 2026-07-23-quick-split-single-transaction/story-3-settlement-view-share-link 8d97930a73bf`
  - `story: 2026-07-24-per-event-fee-revenue-model/story-3-fee-sharing-pro-exemption c9350fca11ca`
  - `story: 2026-07-24-per-event-fee-revenue-model/story-4-messaging-migration-quick-split-guard 12eea11e766c`
  - `upgrade: gate0-divergence present=true`, `upgrade: safety-fact present=true`, `upgrade: reviewer-filters present=true`, `upgrade: repro-first present=true`
  - `gate-upgrade-trial: initialized — 4 stories, 4 upgrades present, no arms recorded`
- Step 2: `gate-upgrade-trial-v1 True 0 {None} None {'after': None, 'before': None, 'unchanged': None}`: the five identity fields of each story equal the baseline's selection, in order; no arms, no routes, no labeler, and no yuss snapshot (no `--yuss` was given).
- Step 3: `exit 0 …`; `upgrade: gate0-divergence present=false` (the file lacks the divergence block), `upgrade: safety-fact present=false`, `upgrade: reviewer-filters present=false`, `upgrade: repro-first present=true`, and `gate-upgrade-trial: initialized — 4 stories, 1 upgrade present, no arms recorded`. A failed probe is stored, not fatal.

**Implementation Reference:** Story 1 — Files: `.writ/eval/gate-upgrade-trial/gate-upgrade-trial.py` (`cmd_init`, `probe_upgrades`, `trial_skeleton`)

**Status:** [ ] Pass  [ ] Fail

**Notes:**

---

### Scenario 2: `init` refuses a bad baseline, a missing repo or yuss path, and an existing `--out`, and writes nothing

**Source:** Acceptance Criteria (AC-1.2) — Story 1; Error Map `init` (baseline missing, unparseable, not four stories, bad SHA, unsafe path, `--out` exists); DEV-001
**Feature:** none
**Verification:** human — no recipe

**Preconditions:**
- Setup block pasted.

**Steps:**
1. `bl; for f in missing broken three badsha unsafe; do echo "== $f"; rc gt init --baseline "$W/bl/$f.json" --out "$W/bl/out.json" --repo "$CL"; done; ls "$W/bl/out.json" 2>&1`
2. `gt init --baseline "$B0" --out "$W/bl/out.json" --repo "$CL" | tail -1; A=$(h12 "$W/bl/out.json"); rc gt init --baseline "$B0" --out "$W/bl/out.json" --repo "$CL"; rc gt init --baseline "$W/bl/three.json" --out "$W/bl/out.json" --repo "$CL" --force; [ "$A" = "$(h12 "$W/bl/out.json")" ] && echo "out unchanged"`
3. `rc gt init --baseline "$B0" --out "$W/bl/o2.json" --repo "$W/no-such-repo"; rc gt init --baseline "$B0" --out "$W/bl/o2.json" --repo "$CL" --yuss "$W/no-such-yuss"; ls "$W/bl/o2.json" 2>&1`

**Expected Result:**
- Step 1: `badsha.json broken.json three.json unsafe.json`, then each case prints `exit 2 stdout-bytes 0` and one stderr line:
  - `missing`: `reason: baseline_unreadable — baseline unreadable: …/bl/missing.json (FileNotFoundError)`
  - `broken`: `reason: baseline_unreadable — baseline unreadable: …/bl/broken.json (JSONDecodeError)`
  - `three`: `reason: selection_invalid — baseline selection must list exactly 4 stories`
  - `badsha`: `reason: bad_sha — story_commit of 2026-07-24-per-event-fee-revenue-model/story-2-event-creation-payment-flow is not a hex commit SHA: 'zzzz…'`
  - `unsafe`: `reason: unsafe_path — story_path is not a safe relative path: '../outside/story.md'`
  - `ls` reports no such file.
- Step 2: `gate-upgrade-trial: initialized — 4 stories, 4 upgrades present, no arms recorded`; then `exit 2 stdout-bytes 0` with `reason: out_exists — refusing to overwrite …/bl/out.json without --force`; then `exit 2 stdout-bytes 0` with `reason: selection_invalid …` (`--force` does not let a bad baseline replace a good file); `out unchanged`.
- Step 3: `exit 2 stdout-bytes 0` with `reason: repo_missing — --repo is not a directory: …/no-such-repo` (DEV-001: without it, four silent `present: false` probes); `exit 2 stdout-bytes 0` with `reason: yuss_missing — yuss path missing: …/no-such-yuss`; `ls` reports no such file.

**Implementation Reference:** Story 1 — Files: `gate-upgrade-trial.py` (`cmd_init`, `check_identity`, `Refusal`); refusals print to stderr with stdout empty

**Status:** [ ] Pass  [ ] Fail

**Notes:**

---

### Scenario 3: `prepare` builds the checkout, parent worktree, diff, story, and contract from a stand-in yuss, and the stand-in is unchanged

**Source:** Acceptance Criteria (AC-1.3) — Story 1; Business Rule 2 (yuss isolation); DEV-001 (`init --yuss`), DEV-004 (`snapshot`)
**Feature:** none
**Verification:** human — no recipe

**Preconditions:**
- Setup block pasted. This scenario uses the stand-in at `$W/yuss-standin`, never the real yuss.

**Steps:**
1. `sb; echo "${COMMIT:0:12}"`
2. `Y0=$(ysnap "$W/yuss-standin"); I0=$(h12 "$W/yuss-standin/.git/index"); rc sp; cat "$W/out.txt"`
3. `[ "$Y0" = "$(ysnap "$W/yuss-standin")" ] && [ "$I0" = "$(h12 "$W/yuss-standin/.git/index")" ] && echo "stand-in unchanged"; [ "$(git -C "$RUN/checkout" rev-parse HEAD)" = "$COMMIT" ] && echo "checkout at story commit"; git -C "$RUN/checkout" remote | wc -l | tr -d ' '; [ "$(git -C "$RUN/parent" rev-parse HEAD)" = "$PARENT" ] && echo "parent at parent sha"`
4. `ls "$RUN"; grep -c '^+    return round(amount, 2)$' "$RUN/diff.patch"; grep -c 'Deliverable: a payment helper.' "$RUN/contract.md"; grep -c 'not part of the contract' "$RUN/contract.md"; grep -c 'Completed ✅' "$RUN/story.md"`
5. `gt snapshot --trial "$W/sb/trial.json" --yuss "$W/yuss-standin"`
6. `touch "$W/yuss-standin/stray.txt"; gt snapshot --trial "$W/sb/trial.json" --yuss "$W/yuss-standin"; rm "$W/yuss-standin/stray.txt"`

**Expected Result:**
- Step 1: `yuss: before recorded (head <12 hex>)` and `gate-upgrade-trial: initialized — 4 stories, 4 upgrades present, no arms recorded`; the 12 hex digits equal the echoed value (DEV-001: the before-snapshot is HEAD plus hashes of refs and status).
- Step 2: `exit 0 …`; `pass`; `checkout:`, `parent:`, `diff:`, `story:`, `contract:`, `tests:`, `boundary:`, and `routes-json:` lines with paths under `…/runs/writ-gate-trial-2026-01-01-alpha--story-1-api/`; a `routes:` line; a `blast-radius:` path; six `arm: <arm> …/arms/<arm>/.writ/config.md` lines in the order off-1, off-2, reviewer-filters, safety-fact, gate0-divergence, repro-first; last `gate-upgrade-trial: prepared 2026-01-01-alpha/story-1-api at <first 12 of the Step 1 echo>`. Nothing on stderr.
- Step 3: `stand-in unchanged` (HEAD, refs, worktrees, porcelain status, and index), `checkout at story commit`, `0` (the checkout has no remote back to yuss), `parent at parent sha`.
- Step 4: `arms`, `blast-radius.json`, `boundary.json`, `checkout`, `contract.md`, `diff.patch`, `parent`, `routes.json`, `story.md`, `tests.txt`; then `1`, `1`, `0` (the contract stops at the next `##` section), `1`.
- Step 5: `pass`, `yuss: unchanged`, `gate-upgrade-trial: yuss snapshot after — unchanged` (DEV-004).
- Step 6: `unverifiable`, `reason: yuss_changed`, `yuss: changed`, `gate-upgrade-trial: yuss snapshot after — changed`. It exits 0: a changed yuss is a finding, not a refusal.

**Implementation Reference:** Story 1 — Files: `gate-upgrade-trial.py` (`cmd_prepare`, `_prepare`, `yuss_snapshot`); `scripts/review-panel.py` (`_prepare_run`, loaded by path); Story 2 adds `cmd_snapshot`

**Status:** [ ] Pass  [ ] Fail

**Notes:**

---

### Scenario 4: `prepare` stores the routes, writes the blast radius and `tests.txt`, and writes one switch-only config per arm

**Source:** Acceptance Criteria (AC-1.4) — Story 1; technical-spec.md → Arms; DEV-003 (`tests.txt`, `routes.json`); DEV-010 (the placeholder `prepare` writes when a story has no `### Test Results`)
**Feature:** none
**Verification:** human — no recipe

**Preconditions:**
- Setup block pasted; `sb >/dev/null && sp | tail -1` prints the `prepared` line.

**Steps:**
1. `python3 -c 'import json,sys; d=json.load(open(sys.argv[1])); print(d["stories"][0]["routes"]); print([s["routes"] for s in d["stories"][1:]])' "$W/sb/trial.json"; ls -A "$W/sb"`
2. `python3 -c 'import json,sys; r,b,x=(json.load(open(p)) for p in sys.argv[1:4]); print(r["gate3"]["crossings"]["reasons"], r["gate0"]["planned"], r["gate0"]["crossings"]["route"], b["owned"], x["verdict"], x["consumers"]["lib/payments.py"], x["tests"]["lib/payments.py"])' "$RUN/routes.json" "$RUN/boundary.json" "$RUN/blast-radius.json"`
3. `for a in off-1 off-2 reviewer-filters safety-fact gate0-divergence repro-first; do f="$RUN/arms/$a/.writ/config.md"; printf '%s off=%s on=%s\n' "$a" "$(grep -c ' off$' "$f")" "$(grep ' on$' "$f" | sed 's/^- \*\*\(.*\):\*\* on$/\1/')"; done`
4. `for a in off-1 safety-fact reviewer-filters; do for n in safety-fact reviewer-filters; do echo "$a $n $(python3 "$CL/scripts/review-override.py" switch --name $n --repo "$RUN/arms/$a" | head -1)"; done; done`
5. `cat "$RUN/tests.txt"`
6. `sv no-results && sp | tail -1; cat "$RUN/tests.txt"`

**Expected Result:**
- Step 1: `{'gate0_route': 'evaluator-agent', 'gate3_route': 'review-agent', 'planned_surface': 'cross-component', 'surface': 'cross-component'}` and `[None, None, None]` (only the prepared story changed); `ls` shows `baseline.json` and `trial.json` only (the atomic write left no temp file).
- Step 2: `['outside_boundary lib/other.py'] ['lib/payments.py'] evaluator-agent ['lib/payments.py'] pass ['app/checkout.py'] ['tests/test_payments.py']`: Gate 2.5 sees `lib/other.py` cross the story boundary and routes to review-agent; Gate 0's planned set is the owned file and routes to evaluator-agent; the blast radius ran because Gate 3 routes to review-agent and safety-fact is present.
- Step 3: `off-1 off=4 on=`, `off-2 off=4 on=`, `reviewer-filters off=3 on=Reviewer Filters`, `safety-fact off=3 on=Safety Fact`, `gate0-divergence off=3 on=Gate 0 Divergence`, `repro-first off=3 on=Repro First`.
- Step 4: `off-1 safety-fact off`, `off-1 reviewer-filters off`, `safety-fact safety-fact on`, `safety-fact reviewer-filters off`, `reviewer-filters safety-fact off`, `reviewer-filters reviewer-filters on`: the shipped switch reader agrees with every config.
- Step 5: exactly three lines, `historical, not re-run`, `- 12 passed in 0.4s`, `- coverage 91%`: the story's Test Results with the `exit code: 0` line dropped and nothing from `### Files Changed` (DEV-003; the `tested` rung stays out of reach).
- Step 6: `story 1 now at <12 hex> (parent <12 hex>)`, the `prepared` line, then exactly `historical, not re-run` and `(no historical test results in the story file)`. This placeholder is what `prepare` wrote for two real stories; DEV-010 records that the orchestrator replaced those two files by hand (Scenario 18).

**Implementation Reference:** Story 1 — Files: `gate-upgrade-trial.py` (`compute_routes`, `historical_tests`, `arm_config`); `scripts/change-surface.py` (`classify`, `blast-radius`), `scripts/boundary-map.py` (`compute`, `crossings`)

**Status:** [ ] Pass  [ ] Fail

**Notes:**

---

### Scenario 5: `prepare` refuses a missing yuss, an unreachable commit, a parent beyond depth 2, and a missing or incomplete `review-panel.py`, and leaves no run directory

**Source:** Acceptance Criteria (AC-1.5) — Story 1; Error Map `prepare` (yuss path missing or SHA unreachable; parent not reachable at depth 2; `review-panel.py` missing or lacks a reused name); Shadow Path "Trial run" (nil: no trial file; upstream error: yuss unreachable); DEV-002
**Feature:** none
**Verification:** human — no recipe

**Preconditions:**
- Setup block pasted; `sb` prints its two lines; then `T=$(h12 "$W/sb/trial.json"); Y0=$(ysnap "$W/yuss-standin")`.

**Steps:**
1. `rc sp "$S1" "$W/no-such-yuss"`
2. `rc sp 2026-01-02-beta/story-2-ui`
3. `python3 "$W/retarget.py" "$W/sb/trial.json" "$W/sb/deep.json" "$COMMIT" "$BASE"; D=$(h12 "$W/sb/deep.json"); rc gt prepare --trial "$W/sb/deep.json" --story "$S1" --yuss "$W/yuss-standin" --tmp-root "$W/runs"; echo "${BASE:0:12}"; [ "$D" = "$(h12 "$W/sb/deep.json")" ] && echo "deep trial unchanged"`
4. `mv "$CL/scripts/review-panel.py" "$W/review-panel.py.bak"; rc sp; mv "$W/review-panel.py.bak" "$CL/scripts/review-panel.py"`
5. `sed -i '' 's/^def trial_key(/def renamed_trial_key(/' "$CL/scripts/review-panel.py"; rc sp; reset`
6. `rc gt prepare --trial "$W/no-trial.json" --story "$S1" --yuss "$W/yuss-standin" --tmp-root "$W/runs"`
7. `ls -A "$W/runs"; [ "$T" = "$(h12 "$W/sb/trial.json")" ] && echo "trial unchanged"; [ "$Y0" = "$(ysnap "$W/yuss-standin")" ] && echo "stand-in unchanged"`

**Expected Result:**
- Every refusal prints `exit 2 stdout-bytes 0` and exactly one stderr line:
  - Step 1: `reason: yuss_missing — 2026-01-01-alpha/story-1-api: yuss path missing: …/no-such-yuss`
  - Step 2: `reason: sha_unreachable — 2026-01-02-beta/story-2-ui: story_commit 222222222222 unreachable in …/yuss-standin` (the mini baseline's fake SHA)
  - Step 3: `reason: prepare_failed — 2026-01-01-alpha/story-1-api: parent <12 hex> not reachable at depth 2`, where the 12 hex digits equal the echoed `$BASE` prefix (the grandparent exists in the stand-in but not in a depth-2 fetch); then `deep trial unchanged`.
  - Step 4: `reason: review_panel_missing — …/clone/scripts/review-panel.py not found` (no story prefix: the module loads before the story is read).
  - Step 5: `reason: review_panel_missing — …/clone/scripts/review-panel.py lacks trial_key`; `reset` prints nothing.
  - Step 6: `reason: trial_invalid — 2026-01-01-alpha/story-1-api: trial file unreadable: …/no-trial.json (FileNotFoundError)`
- Step 7: nothing from `ls` (every failure removed its partial run directory), `trial unchanged`, `stand-in unchanged`.

**Implementation Reference:** Story 1 — Files: `gate-upgrade-trial.py` (`cmd_prepare`, `load_review_panel`, `require_yuss`); WWB decision 2 (pre-flight with local git helpers)

**Status:** [ ] Pass  [ ] Fail

**Notes:**

---

### Scenario 6: An empty planned set skips Gate 0 with a reason, and a missing `blast-radius` subcommand or a failing route script refuses

**Source:** Error Map — Story 1 (`prepare`: planned set empty or crossings `unverifiable`; `blast-radius` absent while `safety-fact` present); DEV-003 (`gate0_reason`)
**Feature:** none
**Verification:** human — no recipe

**Preconditions:**
- Setup block pasted; `reset` prints nothing.

**Steps:**
1. `sb >/dev/null && sv no-paths && rc sp; grep -E '^(routes|gate0_reason):' "$W/out.txt"; tail -1 "$W/out.txt"`
2. `python3 -c 'import json,sys; print(json.load(open(sys.argv[1]))["stories"][0]["routes"])' "$W/sb/trial.json"`
3. `T=$(h12 "$W/sb/trial.json"); sed -i '' 's/add_parser("blast-radius"/add_parser("blast-radius-renamed"/' "$CL/scripts/change-surface.py"; rc sp; ls -A "$W/runs"; [ "$T" = "$(h12 "$W/sb/trial.json")" ] && echo "trial unchanged"; reset`
4. `pt scripts/tests/test_gate_upgrade_trial.py -q -k "route_script_failure or unverifiable_gate0_crossings or blast_radius_without_json" 2>&1 | tail -1`

**Expected Result:**
- Step 1: `story 1 now at …`; `exit 0 …`; `routes: surface=cross-component gate3_route=review-agent planned_surface=none gate0_route=skip`; `gate0_reason: unverifiable: no planned files`; the `prepared` line.
- Step 2: `{'gate0_reason': 'unverifiable: no planned files', 'gate0_route': 'skip', 'gate3_route': 'review-agent', 'planned_surface': None, 'surface': 'cross-component'}`.
- Step 3: `exit 2 stdout-bytes 0`; stderr `reason: blast_radius_unavailable — 2026-01-01-alpha/story-1-api: change-surface.py blast-radius exited 2`; `ls` prints nothing (`prepare` replaced Step 1's run directory, then removed it on the failure); `trial unchanged`; `reset` prints nothing.
- Step 4: `7 passed, 302 deselected`. These stub the route scripts: a `classify` or `compute` that exits 2, prints an unknown class, or prints no JSON, and a `crossings` with no route, each refuse `route_failed` and remove the run directory; a blast radius that prints no JSON is `blast_radius_unavailable`; Gate 0 crossings that read `unverifiable` store `gate0_route: skip` with the reason.

**Implementation Reference:** Story 1 — Files: `gate-upgrade-trial.py` (`compute_routes`, `_prepare` blast-radius block); `scripts/tests/test_gate_upgrade_trial.py` (`TestPrepareRefusals`, `TestPrepareStubbedRoutes`)

**Status:** [ ] Pass  [ ] Fail

**Notes:**

---

## Story 2: Trial Harness: record, sheet, label, and report

### Scenario 7: `record` refuses an arm whose evidence does not match it, and the trial file stays unchanged

**Source:** Acceptance Criteria (AC-2.1) — Story 2; Error Map `record` (arm not applicable; switch states or report line mismatch; `--origin` differs; output unreadable); DEV-005
**Feature:** none
**Verification:** human — no recipe

**Preconditions:**
- Setup block pasted.

**Steps:**
1. `fx; fr 1 off-1 off-fail.md --origin model-a | tail -1; fr 1 off-2 off-fail.md | tail -1; H=$(h12 "$FT")`
2. `rc fr 1 safety-fact off-fail.md --verifier "$V"; rc fr 1 off-1 safety-on.md`
3. `rc gt record --trial "$FT" --story "$S1" --arm reviewer-filters --output "$FX/filters-on.md" --state-dir "$W/fx/state" --state reviewer-filters=off --state safety-fact=off; rc gt record --trial "$FT" --story "$S1" --arm off-2 --output "$FX/off-fail.md" --state-dir "$W/fx/state" --state safety-fact=off`
4. `rc fr 1 gate0-divergence gate0-comparison.md --report-line "gate0-divergence: off (config)"`
5. `rc fr 2 gate0-divergence gate0-comparison.md --report-line "$CHOSE"; rc fr 3 safety-fact safety-on.md --verifier "$V"`
6. `rc fr 1 reviewer-filters filters-on.md --origin model-b; rc fr 1 reviewer-filters no-such-output.md`
7. `[ "$H" = "$(h12 "$FT")" ] && echo "trial unchanged"; ls "$W/fx/state/2026-01-01-alpha--story-1-api"`

**Expected Result:**
- Step 1: `fixture trial: 4 stories, routes set, no arms`; `gate-upgrade-trial: recorded 2026-01-01-alpha/story-1-api off-1 — 2 keys, 0 upgrade-only findings`; the same line for `off-2`.
- Steps 2 to 6: every call prints `exit 2 stdout-bytes 0` and one stderr line, in order:
  - `reason: evidence_mismatch — the safety-fact output has no Safety Fact heading`
  - `reason: evidence_mismatch — the off-1 output has a Safety Fact heading`
  - `reason: evidence_mismatch — the reviewer-filters arm needs reviewer-filters=on, got off`
  - `reason: evidence_mismatch — the off-2 arm needs --state reviewer-filters=off`
  - ``reason: evidence_mismatch — --report-line must start `gate0-divergence: chose` or `gate0-divergence: skip` ``
  - `reason: arm_not_applicable — gate0-divergence does not apply to 2026-01-02-beta/story-2-ui (gate0_route is evaluator-agent)`
  - `reason: arm_not_applicable — safety-fact does not apply to 2026-01-03-gamma/story-3-db (gate3_route is evaluator-agent)`
  - `reason: origin_mismatch — --origin model-b differs from the stored origin model-a`
  - `reason: output_unreadable — arm output unreadable: …/no-such-output.md (FileNotFoundError)`
- Step 7: `trial unchanged`; `off-1.md` and `off-2.md` only (no refused arm's output was copied).

**Implementation Reference:** Story 2 — Files: `gate-upgrade-trial.py` (`cmd_record`, `check_states`, `_gate3_entry`, `_gate0_entry`); fixtures `off-fail.md`, `safety-on.md`, `filters-on.md`

**Status:** [ ] Pass  [ ] Fail

**Notes:**

---

### Scenario 8: Gate 0 keys come only from `**Avoided by:**` issues, and a repro that fails at both commits keys its criterion at Critical

**Source:** Acceptance Criteria (AC-2.2) — Story 2; Business Rule 5 (Upgrade-only findings); Error Map "Repro arm" (a bug without its repro results is refused)
**Feature:** none
**Verification:** human — no recipe

**Preconditions:**
- Setup block pasted.

**Steps:**
1. `fx; fr 1 off-1 off-fail.md | tail -1; fr 1 off-2 off-fail.md | tail -1`
2. `fr 1 gate0-divergence gate0-comparison.md --report-line "$CHOSE"; af 1 gate0-divergence keys`
3. `fr 1 gate0-divergence gate0-no-avoided.md --report-line "$CHOSE" | sed -n 2p; fr 3 gate0-divergence gate0-no-avoided.md --report-line "$SKIP" | sed -n 2p; af 3 gate0-divergence report`
4. `fr 1 repro-first repro-bug.md --kind bug --repro-ac AC-1.3 --at-parent fail --at-commit fail | sed -n 2,3p; af 1 repro-first keys`
5. `for p in "fail pass" "pass fail" "pass pass"; do set -- $p; fr 1 repro-first repro-bug.md --kind bug --repro-ac AC-1.3 --at-parent $1 --at-commit $2 | sed -n 2p; af 1 repro-first repro_result; done`
6. `rc fr 1 repro-first repro-bug.md --kind bug; rc fr 1 repro-first repro-not-bug.md --kind not-a-bug-fix --at-parent fail`

**Expected Result:**
- Step 1: the two `recorded … — 2 keys, 0 upgrade-only findings` lines.
- Step 2: `pass`, `arm: gate0-divergence verdict=none keys=1 exercised=true`, `upgrade_only: 1`, `gate-upgrade-trial: recorded 2026-01-01-alpha/story-1-api gate0-divergence — 1 key, 1 upgrade-only finding`; then `[{"key": "security:app/api/pay/webhook.ts", "severity": "Critical"}]`. The fixture's second issue (no `**Avoided by:**`), its Recommendations entry (outside `### Issues Found`), and its unchecked checklist line give no key.
- Step 3: `arm: gate0-divergence verdict=none keys=0 exercised=true`; `arm: gate0-divergence verdict=none keys=0 exercised=false`; `"skip"` (a skip report line stores the story as not exercised).
- Step 4: `arm: repro-first verdict=none keys=1 exercised=true`, `upgrade_only: 1`; `[{"key": "ac:AC-1.3", "severity": "Critical"}]`.
- Step 5: three pairs: `arm: repro-first verdict=none keys=0 exercised=true` then `"fixed"`; the same arm line then `"no_repro"`; the same arm line then `"no_repro"`. Only fail at the parent and fail at the story commit yields a key.
- Step 6: both `exit 2 stdout-bytes 0`, with `reason: evidence_mismatch — --kind bug needs --repro-ac, --at-parent, and --at-commit` and `reason: evidence_mismatch — --kind not-a-bug-fix takes no repro field`.

**Implementation Reference:** Story 2 — Files: `gate-upgrade-trial.py` (`avoided_text`, `_repro_entry`, `recompute`); fixtures `gate0-comparison.md`, `gate0-no-avoided.md`, `repro-bug.md`

**Status:** [ ] Pass  [ ] Fail

**Notes:**

---

### Scenario 9: `sheet` writes shuffled IDs, blank fields, and one excerpt per finding; `label` stores labels only from an unedited, fully filled sheet and a human name

**Source:** Acceptance Criteria (AC-2.3) — Story 2; Business Rules 6 (Labels) and 7 (Acknowledgments); Error Map `label` (sheet body changed; blank or bad field; agent-like `--labeled-by`); DEV-005 (`sheet_stale`)
**Feature:** none
**Verification:** human — no recipe

**Preconditions:**
- Setup block pasted; `fxall` prints `fixture trial: 21 arms, 7 upgrade-only findings`.

**Steps:**
1. `rc fsheet; cat "$W/out.txt"; H=$(h12 "$FT"); S="$W/fx/labeling-sheet.md"`
2. `grep -c '^### F0[1-7]$' "$S"; grep -cx 'label:' "$S"; grep -cx 'note:' "$S"; grep -cx 'ack:' "$S"; sed -n '/^## Not exercised/,$p' "$S"; grep -cwE 'gate0-divergence|safety-fact|reviewer-filters|off-1|off-2' "$S"`
3. `ls "$W/fx/state/findings"; grep -l 'Avoided by' "$W/fx/state/findings"/F0*.md | wc -l | tr -d ' '; python3 -c 'import json,sys; s=json.load(open(sys.argv[1]))["sheet"]; print(s["findings"], s["seed"], len(s["body_sha256"]))' "$FT"`
4. `rc flabel`
5. `fill invalid remove; for n in Claude "review agent" ""; do rc flabel "$n"; done`
6. `` fill invalid remove --note 'see `pay.ts`'; rc flabel; fill invalid remove --note "$(printf 'x%.0s' $(seq 201))"; rc flabel ``
7. `fill invalid keep; rc flabel`
8. `fill invalid remove; sed -i '' 's/^severity: Major$/severity: Minor/' "$S"; rc flabel`
9. `[ "$H" = "$(h12 "$FT")" ] && echo "trial unchanged"`
10. `fill invalid remove security:app/api/pay/webhook.ts; flabel`
11. `fr 2 reviewer-filters filters-on.md | tail -1; rc flabel`

**Expected Result:**
- Step 1: `exit 0 …`; `pass`, `sheet: …/fx/labeling-sheet.md`, `findings: 7`, `not_exercised: repro-first`, `excerpts: …/fx/state/findings`, `gate-upgrade-trial: sheet written — 7 findings, 1 acknowledgment`.
- Step 2: `7`, `7`, `7`, `1`; then `## Not exercised`, a blank line, `### not exercised: repro-first`, `exercised: 0/4`, four lines `- <story id>: not-a-bug-fix`, and `ack:`; then `0` (the sheet names no arm; the never-exercised upgrade appears only in its ack heading).
- Step 3: `F01.md` to `F07.md`; `1` (only the Gate 0 excerpt carries an `**Avoided by:**` line); `7 7 64` (findings, seed, body-hash length).
- Step 4: `exit 2 stdout-bytes 0`; `reason: bad_field — F01 label must be valid or invalid`.
- Step 5: three times `exit 2 stdout-bytes 0` with `reason: labeled_by_invalid — --labeled-by must name the human who labeled the sheet, not an agent or model: 'Claude'` (then `'review agent'`, then `''`).
- Step 6: twice `exit 2 stdout-bytes 0` with `reason: bad_field — F01 note must be one line of at most 200 characters with no backtick` (a backtick, then 201 characters).
- Step 7: `exit 2 …`; `reason: bad_field — ack for repro-first must be remove or amend`.
- Step 8: `exit 2 …`; ``reason: sheet_changed — …/fx/labeling-sheet.md differs from the sheet `sheet` wrote beyond its label, note, and ack values``.
- Step 9: `trial unchanged`.
- Step 10: `pass`, `labeled: 7 (valid 1, invalid 6)`, `acks: repro-first=remove`, `labeled_by: UAT Tester`, `gate-upgrade-trial: labels stored — 7 findings, 1 acknowledgment`.
- Step 11: `gate-upgrade-trial: recorded 2026-01-02-beta/story-2-ui reviewer-filters — 3 keys, 3 upgrade-only findings`; `exit 2 …`; `reason: sheet_stale — a record ran after sheet: the trial's findings or not-exercised upgrades differ from the sheet; run sheet --force` (DEV-005: labels never land on a finding set the sheet does not show).

**Implementation Reference:** Story 2 — Files: `gate-upgrade-trial.py` (`cmd_sheet`, `excerpt_text`, `body_hash`, `cmd_label`, `parse_sheet`); WWB decision 3 (`sheet_stale`)

**Status:** [ ] Pass  [ ] Fail

**Notes:**

---

### Scenario 10: `report` keeps an upgrade on one valid catch, removes one with none, applies the ack, and gives the same verdicts as JSON

**Source:** Acceptance Criteria (AC-2.4) — Story 2; Business Rule 8 (Verdict); Shadow Path "Report" (happy path); Experience Design (Moment of truth); DEV-006 (`blinding:` line)
**Feature:** none
**Verification:** human — no recipe

**Preconditions:**
- Setup block pasted; `fxall` prints `fixture trial: 21 arms, 7 upgrade-only findings`; `fsheet | tail -1` prints `gate-upgrade-trial: sheet written — 7 findings, 1 acknowledgment`.

**Steps:**
1. `fill invalid remove security:app/api/pay/webhook.ts && flabel | sed -n 2,3p; rc frep; cat "$W/out.txt"`
2. `fill invalid amend && flabel | sed -n 3p; frep | grep -E '^(pass|unverifiable)$|^reason:|^upgrade:|^gate-upgrade-trial:'`
3. `frep --json | python3 -c 'import json,sys; d=json.load(sys.stdin); print(d["verdict"], d["reasons"], [(u["name"], u["verdict"], u["valid"]) for u in d["upgrades"]], d["yuss"]); print(d["summary"])'`

**Expected Result:**
- Step 1: `labeled: 7 (valid 1, invalid 6)`, `acks: repro-first=remove`; `exit 0 …`; then:
  - `pass`
  - `story: 2026-01-01-alpha/story-1-api gate3_route=review-agent gate0_route=review-agent repro=not-a-bug-fix arms=off-1,off-2,reviewer-filters,safety-fact,gate0-divergence,repro-first`
  - `story: 2026-01-02-beta/story-2-ui gate3_route=review-agent gate0_route=evaluator-agent repro=not-a-bug-fix arms=off-1,off-2,reviewer-filters,safety-fact,repro-first`
  - `story: 2026-01-03-gamma/story-3-db gate3_route=evaluator-agent gate0_route=review-agent repro=not-a-bug-fix arms=off-1,off-2,reviewer-filters,gate0-divergence,repro-first`
  - `story: 2026-01-04-delta/story-4-lib gate3_route=review-agent gate0_route=skip repro=not-a-bug-fix arms=off-1,off-2,reviewer-filters,safety-fact,repro-first`
  - `upgrade: gate0-divergence verdict=keep exercised=1/4 upgrade_only=1 valid=1 invalid=0 off_only=2`
  - `upgrade: safety-fact verdict=remove exercised=3/4 upgrade_only=2 valid=0 invalid=2 off_only=2`
  - `upgrade: reviewer-filters verdict=remove exercised=4/4 upgrade_only=4 valid=0 invalid=4 off_only=2`
  - `upgrade: repro-first verdict=remove exercised=0/4 reason=not_exercised`
  - `sample: 4 stories, two current-gates runs, one run per upgrade arm; one valid catch keeps an upgrade — a low bar, not a cost case`
  - `proxy: Gate 0 and Repro First arms are retrospective proxies (sketch comparison, repro re-run), not replays`
  - `blinding: honor system — the sheet hides which upgrade raised a finding, but the trial file and raw outputs map IDs to arms, and Gate 0 excerpts show their Avoided by line`
  - `yuss: not checked`
  - `gate-upgrade-trial: keep 1, remove 3, unverifiable 0, absent 0 — 4 stories`
  - Off-only counts (keys both off runs raised that the arm missed) print for information and decide nothing.
- Step 2: `acks: repro-first=amend`; then `unverifiable`, `reason: repro-first amendment_requested`, `upgrade: gate0-divergence verdict=remove exercised=1/4 upgrade_only=1 valid=0 invalid=1 off_only=2`, the safety-fact and reviewer-filters lines as in Step 1, `upgrade: repro-first verdict=unverifiable exercised=0/4 reason=amendment_requested`, and `gate-upgrade-trial: keep 0, remove 3, unverifiable 1, absent 0 — 4 stories`.
- Step 3: `unverifiable ['repro-first amendment_requested'] [('gate0-divergence', 'remove', 0), ('safety-fact', 'remove', 0), ('reviewer-filters', 'remove', 0), ('repro-first', 'unverifiable', None)] not checked`, then `gate-upgrade-trial: keep 0, remove 3, unverifiable 1, absent 0 — 4 stories`.

**Implementation Reference:** Story 2 — Files: `gate-upgrade-trial.py` (`upgrade_verdict`, `trial_report`, `cmd_report`); WWB decision 4 (`blinding:` line)

**Status:** [ ] Pass  [ ] Fail

**Notes:**

---

### Scenario 11: `report` says `unverifiable` with a named reason for no labels, a missing arm, or no ack, says `absent` for a missing upgrade, and refuses a missing or malformed trial file

**Source:** Shadow Path "Report" (nil, empty, upstream error) and "Trial run" (nil) — Story 2; Error Map `sheet` (an applicable arm missing) and `report` (unlabeled, missing arm, missing ack); Error Map `init` (presence probe fails → `absent`); Interaction Edge Case "blind trial removed Gate 0 before `init`"
**Feature:** none
**Verification:** human — no recipe

**Preconditions:**
- Setup block pasted.

**Steps:**
1. `fxall >/dev/null; rc frep; cat "$W/out.txt"`
2. `drop 4 off-2; rc gt sheet --trial "$FT" --out "$W/fx/s2.md" --seed 7 --state-dir "$W/fx/state"; ls "$W/fx/s2.md" 2>&1; frep | sed -n '1,5p'`
3. `mkdir -p "$W/emptyrepo"; gt init --baseline "$FX/mini-baseline.json" --out "$W/fx/absent.json" --repo "$W/emptyrepo" | tail -1; gt report --trial "$W/fx/absent.json" | grep -vE '^(story|sample|proxy|blinding):'`
4. `rc gt report --trial "$W/no-such-trial.json"; printf '{"schema": "panel-trial-v1", "stories": []}\n' > "$W/fx/wrong.json"; rc gt report --trial "$W/fx/wrong.json"; printf '{' > "$W/fx/broken.json"; rc gt report --trial "$W/fx/broken.json"`

**Expected Result:**
- Step 1 (empty input: no labels): `exit 0 …`; then `unverifiable`, `reason: gate0-divergence unlabeled 1`, `reason: safety-fact unlabeled 2`, `reason: reviewer-filters unlabeled 4`, `reason: repro-first not_exercised_unacknowledged`, the four `story:` lines from Scenario 10, then:
  - `upgrade: gate0-divergence verdict=unverifiable exercised=1/4 upgrade_only=1 valid=0 invalid=0 off_only=2 reason=unlabeled 1`
  - `upgrade: safety-fact verdict=unverifiable exercised=3/4 upgrade_only=2 valid=0 invalid=0 off_only=2 reason=unlabeled 2`
  - `upgrade: reviewer-filters verdict=unverifiable exercised=4/4 upgrade_only=4 valid=0 invalid=0 off_only=2 reason=unlabeled 4`
  - `upgrade: repro-first verdict=unverifiable exercised=0/4 reason=not_exercised_unacknowledged`
  - the `sample:`, `proxy:`, and `blinding:` lines, `yuss: not checked`, and `gate-upgrade-trial: keep 0, remove 0, unverifiable 4, absent 0 — 4 stories`.
- Step 2: `exit 2 stdout-bytes 0` with `reason: missing_arm — 2026-01-04-delta/story-4-lib off-2`; no `s2.md`; then `unverifiable`, `reason: gate0-divergence unlabeled 1` (Gate 0 does not apply to story 4), and `reason: safety-fact missing_arm 2026-01-04-delta/story-4-lib off-2`, the same for `reviewer-filters` and `repro-first`.
- Step 3: `gate-upgrade-trial: initialized — 4 stories, 0 upgrades present, no arms recorded`; then `pass`, `upgrade: gate0-divergence verdict=absent`, `upgrade: safety-fact verdict=absent`, `upgrade: reviewer-filters verdict=absent`, `upgrade: repro-first verdict=absent`, `yuss: not checked`, `gate-upgrade-trial: keep 0, remove 0, unverifiable 0, absent 4 — 4 stories`. Absence is decided first, before any arm check.
- Step 4: three times `exit 2 stdout-bytes 0`, with `reason: trial_invalid — trial file unreadable: …/no-such-trial.json (FileNotFoundError)` (nil), `reason: trial_invalid — not a gate-upgrade-trial-v1 file: …/fx/wrong.json`, and `reason: trial_invalid — trial file unreadable: …/fx/broken.json (JSONDecodeError)` (upstream error). Nothing on stdout.

**Implementation Reference:** Story 2 — Files: `gate-upgrade-trial.py` (`_missing_for`, `upgrade_verdict`, `first_missing_arm`, `load_trial`)

**Status:** [ ] Pass  [ ] Fail

**Notes:**

---

### Scenario 12: The harness's 309 unit tests pass on Python 3.9, its trial files and sheet hold no reviewer, diff, or story text, it uses only the standard library, it never ships, and the full gates pass

**Source:** Acceptance Criteria (AC-2.5) — Story 2; tasks 1.7, 2.7, 3.7 (full verification); Shadow Path "Trial run" (empty input: no upgrade-only findings); technical-spec.md → Harness (dev-only)
**Feature:** none
**Verification:** human — no recipe

**Preconditions:**
- Setup block pasted; `reset` prints nothing. Run outside any sandbox (eval runs `git init` in a temp dir). About five minutes. Run pytest alone, not beside eval or the bash tests.

**Steps:**
1. `pt scripts/tests/test_gate_upgrade_trial.py -q 2>&1 | tail -1`
2. `pt scripts/tests/test_gate_upgrade_trial.py -q -k "TestNoText or no_findings_and_three_acks" 2>&1 | tail -1`
3. `fxall >/dev/null && fsheet >/dev/null && fill invalid remove && flabel >/dev/null; P='The story says|^[[:space:]]*@@|\+\+\+ b/|REVIEW_RESULT|\*\*Issue:\*\*|Suggested Fix'; grep -cE "$P" "$FT" "$W/fx/labeling-sheet.md" "$W/fx/state/2026-01-01-alpha--story-1-api/off-1.md"`
4. `grep -nE '^(import|from) ' "$H" | cut -d: -f2-`
5. `ls "$CL/plugins/writ/scripts" | grep -c gate-upgrade; grep -c 'gate-upgrade-trial' "$CL/scripts/install.sh" "$CL/scripts/gen-platform-trees.py"; git -C "$CL" ls-files .writ/state | wc -l | tr -d ' '`
6. `pt -q 2>&1 | tail -1; (cd "$CL" && uv run pytest -q 2>&1 | tail -1)`
7. `(cd "$CL" && for t in scripts/tests/test_*.sh; do bash "$t" >/dev/null 2>&1 || echo "FAIL $t"; done; echo "bash loop done"; python3 scripts/gen-platform-trees.py --check | tail -1)`
8. `(cd "$CL" && bash scripts/eval.sh >/dev/null; echo "exit $?"); tail -2 "$(ls -t "$CL"/.writ/state/eval-*.md | head -1)"; reset`

**Expected Result:**
- Step 1: `309 passed`.
- Step 2: `7 passed, 302 deselected`: the six no-text tests scan every fixture trial file written by `init`, `record`, `sheet`, and `label` for reviewer lines, diff markers, and story text, and one test checks a trial with no upgrade-only findings writes a sheet with acks only.
- Step 3: `…/fx/trial.json:0`, `…/fx/labeling-sheet.md:0`, and `…/off-1.md:8`: the raw output in the state directory holds a story sentence, a diff, and reviewer issue text; the trial file and sheet built from it hold none.
- Step 4: `from __future__ import annotations`, `import argparse`, `import hashlib`, `import importlib.util`, `import json`, `import os`, `import random`, `import re`, `import shutil`, `import subprocess`, `import sys`, `from pathlib import Path, PurePosixPath`, `from types import ModuleType`, `from typing import …`. Standard library only.
- Step 5: `0`; `…/install.sh:0` and `…/gen-platform-trees.py:0` (the harness lives under `.writ/eval/`, so `is_shippable_script` never sees it and no Classification row exists); `0` (nothing under `.writ/state/` is tracked).
- Step 6: no `failed` in either summary. Story 3's reviewer recorded `3987 passed, 7 skipped`; the merged tree may count differently. Four of the skips are the outcome test's live checks (Scenario 13).
- Step 7: only `bash loop done`; then `gen-platform-trees: pass (0 stale, 0 missing, 0 orphan, 0 unmapped, 0 vendor)`.
- Step 8: `exit 0`, then `- Findings: 0` and `- Run errors: 0`; `reset` prints nothing.

**Implementation Reference:** Story 2 — Files: `scripts/tests/test_gate_upgrade_trial.py` (`TestNoText`, `TestSheet.test_no_findings_and_three_acks`); WWB coverage 99% (Stories 1 and 2)

**Status:** [ ] Pass  [ ] Fail

**Notes:**

---

## Story 3: Run the Arms and Hand Off for Labeling

### Scenario 13: The outcome test skips while `trial-report.md` is absent, imports nothing from the harness, and fails a committed report the trial does not back

**Source:** Acceptance Criteria (AC-3.1) — Story 3; technical-spec.md → Verdict Execution ("Repo state the outcome test asserts"); Error Map "Story 4 — report `unverifiable`"
**Feature:** none
**Verification:** human — no recipe

**Preconditions:**
- Setup block pasted; `reset` prints nothing.

**Steps:**
1. `pt scripts/tests/test_gate_upgrade_trial_outcome.py -q -rs 2>&1 | tail -2`
2. `grep -nE '^(import|from) ' "$CL/scripts/tests/test_gate_upgrade_trial_outcome.py" | cut -d: -f2-; grep -c 'importlib\|spec_from_file_location\|gate-upgrade-trial.py' "$CL/scripts/tests/test_gate_upgrade_trial_outcome.py"`
3. `R="$CL/$SPEC/trial-report.md"; printf 'pass\n' > "$R"; for n in gate0-divergence safety-fact reviewer-filters repro-first; do echo "upgrade: $n verdict=keep" >> "$R"; done; pt scripts/tests/test_gate_upgrade_trial_outcome.py -q -rf 2>&1 | grep -E '^FAILED|failed' | sed 's/^FAILED .*AssertionError: //'; reset`

**Expected Result:**
- Step 1: a `SKIPPED [4]` line whose reason reads `trial-report.md is absent: the human has not labeled the trial yet, so there is no verdict to check (Story 4 writes the report)`, then `37 passed, 4 skipped`.
- Step 2: `from __future__ import annotations`, `import ast`, `import json`, `import os`, `import re`, `import subprocess`, `import sys`, `from pathlib import Path`, `from typing import …`, `import pytest`; then `0`. It never loads the harness, so it keeps guarding the record after Story 4 deletes `gate-upgrade-trial.py`.
- Step 3: four lines `upgrade: <name> verdict=keep: labeled_by is None (need the labeler's name)` for gate0-divergence, safety-fact, reviewer-filters, and repro-first, then `4 failed, 37 passed`. `reset` prints nothing.

**Implementation Reference:** Story 3 — Files: `scripts/tests/test_gate_upgrade_trial_outcome.py` (`test_upgrade_verdict_matches_repo`, `_trial`, `_check_present`, `_check_removed`, `_check_status`)

**Status:** [ ] Pass  [ ] Fail

**Notes:**

---

### Scenario 14: `init` recorded four present upgrades, the four baseline identities, and a yuss before-snapshot, but one dependency was not complete when it ran (DEV-007)

**Source:** Acceptance Criteria (AC-3.2) — Story 3; task 3.2; Experience Design (Entry point: "after its three dependencies are complete"); DEV-007 (Medium)
**Feature:** none
**Verification:** human — no recipe

**Preconditions:**
- Setup block pasted.

**Steps:**
1. `(cd "$CL" && for s in 2026-10-25-design-divergence 2026-10-25-review-route-rigor 2026-10-25-repro-first-bug-fixing; do python3 scripts/spec-status.py is-complete --file .writ/specs/$s/spec.md | python3 -c 'import json,sys; d=json.load(sys.stdin); print(sys.argv[1], d["complete"], d["matched_value"])' $s; done)`
2. `grep -n '^#### \[DEV-007\]' "$CL/$SPEC/drift-log.md"; grep -n 'Design-divergence blind trial still open' "$CL/$SPEC/rating-handoff.md" | cut -c1-80`
3. `python3 -c 'import json,sys; t=json.load(open(sys.argv[1])); b=json.load(open(sys.argv[2])); F=("story_id","story_path","spec_folder","story_commit","parent_sha"); print(sorted(k for k, v in t["upgrades"].items() if v["present"])); print("identities match baseline:", [[s[f] for f in F] for s in t["stories"]] == [[s[f] for f in F] for s in b["selection"]]); y=t["yuss_snapshot"]["before"]; print("before", y["head"][:12], len(y["refs_sha256"]), len(y["status_sha256"]))' "$CL/$TRIAL" "$B0"`

**Expected Result:**
- Step 1: AC-3.2 requires all three to read `True`. As built, it prints `2026-10-25-design-divergence False In Progress — awaiting blind rating (rating-handoff.md)`, `2026-10-25-review-route-rigor True Complete`, `2026-10-25-repro-first-bug-fixing True Complete`. **This step is expected to Fail.** Story 3 ran `init`, every arm, and `sheet` on the Phase 15 orchestrator's lane instruction, not a human's, overriding task 3.2's stop rule (DEV-007, flagged for review). Gate 0's switch and wiring existed, so Gate 0 was measured as shipped. Record Fail, or accept DEV-007 as a known limitation in Notes.
- Step 2: ``82:#### [DEV-007] Story 3 ran before `2026-10-25-design-divergence` was Complete ⚠️``; a `Design-divergence blind trial still open` caveat line in the handoff, which names Business Rule 12.
- Step 3: `['gate0-divergence', 'repro-first', 'reviewer-filters', 'safety-fact']`; `identities match baseline: True`; `before a5afd43585fe 64 64` (HEAD plus two sha256 hashes; no yuss text).

**Implementation Reference:** Story 3 — Files: `.writ/eval/gate-upgrade-trial/2026-10-29-gate-upgrade-trial.json`; WWB decision 2 (proceeded with design-divergence incomplete)

**Status:** [ ] Pass  [ ] Fail

**Notes:**

---

### Scenario 15: Every applicable arm is recorded on the four stories, each with only its own switch on, at one model, and the prompts are Writ's own text

**Source:** Acceptance Criteria (AC-3.3) — Story 3; Business Rules 3 (Arms) and 4 (Exercise); Error Map "Spawn (any arm)"; DEV-008, DEV-009
**Feature:** none
**Verification:** human — no recipe

**Preconditions:**
- Setup block pasted. Safe before labeling: this prints no key and no finding ID.

**Steps:**
1. `python3 "$W/arms.py" "$CL/$TRIAL"`
2. `(cd "$CL/$TD/prompts" && grep -n '^- \*\*Avoided by:\*\*' gate0-comparison.md; grep -c 'Unmet: \[AC-N.M\]' gate0-comparison.md; grep -nE '^(Kind|Targets|Repro):' repro-stop.md | cut -c1-40; grep -c 'indented four spaces' repro-stop.md; grep -cE 'app/|yuss|per-event|quick-split' gate0-comparison.md repro-stop.md)`

**Expected Result:**
- Step 1:
  - `2026-07-24-per-event-fee-revenue-model/story-2-event-creation-payment-flow: gate3=review-agent gate0=review-agent | off-1 off-2 reviewer-filters safety-fact gate0-divergence repro-first | verifier=pass gate0-report=chose repro=not-a-bug-fix`
  - `2026-07-23-quick-split-single-transaction/story-3-settlement-view-share-link: gate3=review-agent gate0=evaluator-agent | off-1 off-2 reviewer-filters safety-fact repro-first | verifier=pass gate0-report=- repro=not-a-bug-fix`
  - `2026-07-24-per-event-fee-revenue-model/story-3-fee-sharing-pro-exemption: gate3=review-agent gate0=review-agent | off-1 off-2 reviewer-filters safety-fact gate0-divergence repro-first | verifier=pass gate0-report=chose repro=not-a-bug-fix`
  - `2026-07-24-per-event-fee-revenue-model/story-4-messaging-migration-quick-split-guard: gate3=review-agent gate0=review-agent | off-1 off-2 reviewer-filters safety-fact gate0-divergence repro-first | verifier=pass gate0-report=chose repro=not-a-bug-fix`
  - `origin=claude-opus-5-5 arms=23 own-switch-only=23`
  - So: `off-1`, `off-2`, and `reviewer-filters` on all four; `safety-fact` on all four (Gate 2.5 routes each to review-agent); `gate0-divergence` on the three stories whose predicted route is review-agent; repro recognition on all four, with no full repro arm because none was a bug fix. Exercise: Gate 0 Divergence 3/4, Safety Fact 4/4, Reviewer Filters 4/4, Repro First 0/4.
- Step 2: `41:- **Avoided by:** "<one line from the chosen sketch, quoted verbatim>"`; `1` (DEV-008: a `criterion` entry ends with `- [ ] Unmet: [AC-N.M]` so the reused parser can key it); `29:Kind: not a bug fix: …`, `47:Kind: bug: …`, `51:Targets: AC-N.M …`, `61:Kind: bug: …`, `62:Repro: none: <reason>` (DEV-009); `1`; `gate0-comparison.md:0` and `repro-stop.md:0` (no yuss path or story name).
- Not checkable from files: no arm failed both spawns, so none is unrecorded (Scenario 16's `report` names no `missing_arm`); 30 spawns ran, one of them a single safety-fact re-review on story-4 after `safety_fact_below_floor read`, all at `claude-opus-5-5` in one session (Story 3 What Was Built → Trial Run).

**Implementation Reference:** Story 3 — Files: `.writ/eval/gate-upgrade-trial/2026-10-29-gate-upgrade-trial.json` (`arms`, `routes`, `origin`), `prompts/gate0-comparison.md`, `prompts/repro-stop.md`

**Status:** [ ] Pass  [ ] Fail

**Notes:**

---

### Scenario 16: The labeling sheet is blank and exactly what `sheet` wrote, the handoff covers who, what, and how, and `report` says unlabeled with no labeler

**Source:** Acceptance Criteria (AC-3.4) — Story 3; Business Rule 9 (Human gate); Shadow Path "Report" (no labels); Experience Design (Feedback model); DEV-006
**Feature:** none
**Verification:** human — no recipe

**Preconditions:**
- Setup block pasted. Safe before labeling: `report` prints per-upgrade counts the handoff already shows, and no finding ID.

**Steps:**
1. `S="$CL/$TD/labeling-sheet.md"; grep -c '^### F0[1-6]$' "$S"; grep -cx 'label:' "$S"; grep -cx 'note:' "$S"; grep -cx 'ack:' "$S"; grep -c '^### not exercised: repro-first$' "$S"`
2. `python3 -c 'import hashlib,json,re,sys; t=open(sys.argv[1], encoding="utf-8").read(); s=json.load(open(sys.argv[2]))["sheet"]; print(hashlib.sha256(re.sub(r"(?m)^(label|note|ack):.*$", r"\1:", t).encode()).hexdigest() == s["body_sha256"], s["findings"], s["path"])' "$CL/$TD/labeling-sheet.md" "$CL/$TRIAL"`
3. `grep -n '^## ' "$CL/$SPEC/rating-handoff.md"; grep -c 'gate-upgrade-trial.py label\|gate-upgrade-trial.py report' "$CL/$SPEC/rating-handoff.md"`
4. `(cd "$CL" && python3 $TD/gate-upgrade-trial.py report --trial $TRIAL; echo "exit $?")`
5. `tf`

**Expected Result:**
- Step 1: `6`, `6`, `6`, `1`, `1`.
- Step 2: `True 6 .writ/eval/gate-upgrade-trial/labeling-sheet.md` (the committed sheet's body matches the hash `sheet` recorded, so `label` will accept it once filled).
- Step 3: `## Who labels`, `## What to open`, `## Honor-system blinding`, `## Label rule (spec.md Business Rule 6)`, `## Acknowledgment rule (spec.md Business Rule 7)`, `## Exercise counts`, `## Commands`, `## Caveats`; then `2`.
- Step 4:
  - `unverifiable`
  - `reason: gate0-divergence unlabeled 3`, `reason: safety-fact unlabeled 2`, `reason: reviewer-filters unlabeled 1`, `reason: repro-first not_exercised_unacknowledged`
  - four `story:` lines: story-2, quick-split story-3, fee-sharing story-3, and story-4, each `gate3_route=review-agent` and `repro=not-a-bug-fix`; quick-split story-3 reads `gate0_route=evaluator-agent arms=off-1,off-2,reviewer-filters,safety-fact,repro-first`, the other three `gate0_route=review-agent arms=off-1,off-2,reviewer-filters,safety-fact,gate0-divergence,repro-first`
  - `upgrade: gate0-divergence verdict=unverifiable exercised=3/4 upgrade_only=3 valid=0 invalid=0 off_only=0 reason=unlabeled 3`
  - `upgrade: safety-fact verdict=unverifiable exercised=4/4 upgrade_only=2 valid=0 invalid=0 off_only=0 reason=unlabeled 2`
  - `upgrade: reviewer-filters verdict=unverifiable exercised=4/4 upgrade_only=1 valid=0 invalid=0 off_only=0 reason=unlabeled 1`
  - `upgrade: repro-first verdict=unverifiable exercised=0/4 reason=not_exercised_unacknowledged`
  - the `sample:`, `proxy:`, and `blinding:` lines, `yuss: unchanged`, `gate-upgrade-trial: keep 0, remove 0, unverifiable 4, absent 0 — 4 stories`, then `exit 0`.
- Step 5: `labeled_by=None null_labels=6 of 6 acks={}`.

**Implementation Reference:** Story 3 — Files: `.writ/eval/gate-upgrade-trial/labeling-sheet.md`, `.writ/specs/2026-10-25-gate-upgrade-removal-measurement/rating-handoff.md`, the trial file (`sheet`, `labeled_by`)

**Status:** [ ] Pass  [ ] Fail

**Notes:**

---

### Scenario 17: The committed trial files hold no yuss text, the yuss snapshot is unchanged, and the spec awaits the labels

**Source:** Acceptance Criteria (AC-3.5) — Story 3; Business Rule 2 (yuss isolation); Experience Design (Feedback model)
**Feature:** none
**Verification:** human — no recipe

**Preconditions:**
- Setup block pasted.

**Steps:**
1. `git -C "$CL" show --name-only --format= 4542d78`
2. `P='The story says|^[[:space:]]*@@|\+\+\+ b/|REVIEW_RESULT|\*\*Issue:\*\*|Suggested Fix|I want to|So that'; (cd "$CL" && grep -cE "$P" $TRIAL $TD/labeling-sheet.md $SPEC/rating-handoff.md)`
3. `python3 -c 'import json,sys; v=[]; w=lambda x: [w(i) for i in (x.values() if isinstance(x, dict) else x)] if isinstance(x, (dict, list)) else (v.append(x) if isinstance(x, str) else None); w(json.load(open(sys.argv[1]))); print(len(v), "strings,", sum(" " in s for s in v), "contain a space, longest", max(map(len, v)))' "$CL/$TRIAL"; grep -c '/Users/\|/var/folders/\|/private/' "$CL/$TRIAL" "$CL/$TD/labeling-sheet.md"`
4. `python3 -c 'import json,sys; y=json.load(open(sys.argv[1]))["yuss_snapshot"]; print(y["unchanged"], y["before"] == y["after"], y["after"]["head"][:12])' "$CL/$TRIAL"; python3 "$W/ycmp.py" "$CL/$TRIAL" "$YUSS"`
5. `sed -n 3p "$CL/$SPEC/spec.md"`
6. `ls "$REPO/.writ/state/gate-upgrade-trial"; git -C "$REPO" check-ignore -q .writ/state/gate-upgrade-trial && echo ignored`

**Expected Result:**
- Step 1: eleven paths: `.writ/context.md`, the trial JSON, `labeling-sheet.md`, the two prompt files, the spec's `drift-log.md`, `rating-handoff.md`, `spec.md`, `user-stories/README.md`, the Story 3 story file, and `scripts/tests/test_gate_upgrade_trial_outcome.py`. Nothing under `.writ/state/`.
- Step 2: `0` for the trial JSON, the sheet, and the handoff (no reviewer line, diff marker, or story sentence).
- Step 3: `276 strings, 0 contain a space, longest 120` (only IDs, SHAs, paths, keys, routes, and words); `0` and `0` (every path is repo-relative).
- Step 4: `True True a5afd43585fe`; then `head=same refs_sha256=same status_sha256=same`. A `differs` here means yuss has changed since 2026-10-29 for another reason; note it, and judge the trial by the recorded `True True`.
- Step 5: `> **Status:** In Progress — awaiting human labels (rating-handoff.md)`.
- Step 6: the four story slug folders and `findings` (the raw outputs and excerpts live only in the primary checkout's state folder); `ignored`. Do not open them before Scenario 21.

**Implementation Reference:** Story 3 — commit `4542d78`; WWB → Trial Run ("yuss: HEAD `a5afd435…`, refs and status hashes identical before and after")

**Status:** [ ] Pass  [ ] Fail

**Notes:**

---

### Scenario 18: The two hand-written `tests.txt` files (DEV-010) and the thin baseline on two stories are disclosed

**Source:** Business Rule 3 (Arms: the story's historical test results, labeled "historical, not re-run") — Story 3; DEV-010; Story 3 What Was Built → Review Outcome ("Reviewer note before labeling")
**Feature:** none
**Verification:** human — no recipe

**Preconditions:**
- Setup block pasted. Step 2 reads yuss read-only and prints counts only.

**Steps:**
1. `sed -n '/^#### \[DEV-010\]/,/^#### \[DEV-011\]/p' "$CL/$SPEC/drift-log.md" | sed '$d'`
2. `python3 -c 'import json,sys; [print(s["story_id"], s["story_commit"], ".writ/specs/%s/user-stories/%s" % (s["spec_folder"], s["story_path"].rsplit("/", 1)[1])) for s in json.load(open(sys.argv[1]))["stories"]]' "$CL/$TRIAL" | while read id c p; do echo "$id test_results=$(GIT_OPTIONAL_LOCKS=0 git -C "$YUSS" show "$c:$p" | grep -c '^### Test Results')"; done`
3. `python3 -c 'import json,sys; [print(s["story_id"], " ".join("%s=%d(%s)" % (n, len(s["arms"][n]["keys"]), s["arms"][n]["verdict"]) for n in ("off-1", "off-2"))) for s in json.load(open(sys.argv[1]))["stories"]]' "$CL/$TRIAL"`
4. `grep -n 'Thin baseline' "$CL/$SPEC/rating-handoff.md" | cut -c1-90`

**Expected Result:**
- Step 1: the DEV-010 entry: severity Small; `prepare` wrote the placeholder line for quick-split story-3 and per-event story-4 because they record results under `### Verification` and a "Gate 4 (Testing/Coverage)" paragraph; the orchestrator replaced those two files in `$TMPDIR` with that text under `historical, not re-run`, with no `exit code:` line, before any arm ran; never committed.
- Step 2: `…/story-2-event-creation-payment-flow test_results=1`, `…/story-3-settlement-view-share-link test_results=0`, `…/story-3-fee-sharing-pro-exemption test_results=1`, `…/story-4-messaging-migration-quick-split-guard test_results=0`. The two zeros are the two stories DEV-010 names; Scenario 4 Step 6 shows the placeholder `prepare` writes for them.
- Step 3: `story-2 … off-1=3(FAIL) off-2=2(FAIL)`, `quick-split story-3 … off-1=1(FAIL) off-2=2(FAIL)`, `fee-sharing story-3 … off-1=3(FAIL) off-2=0(PAUSE)`, `story-4 … off-1=0(FAIL) off-2=1(FAIL)`. On the last two stories one "current gates" run produced no key, so the baseline there is effectively one run and a finding counts as upgrade-only more easily.
- Step 4: the `Thin baseline on two stories` caveat, which tells the labeler to amend the key rule before labeling, not after, if that matters.
- Not checkable: the hand-written `tests.txt` text itself. It lived only in `$TMPDIR`, and the trial file records no hash of it, so Business Rule 3's "every arm of a story read the same file" rests on the drift entry.

**Implementation Reference:** Story 3 — drift-log.md DEV-010; `rating-handoff.md` § Caveats

**Status:** [ ] Pass  [ ] Fail

**Notes:**

---

### Scenario 19: The anchors DEV-011 tells Story 4 to remove or restore exist at the merge commit as measured

**Source:** DEV-011 — Story 3 (removal-inventory corrections from the dependency specs' drift logs); technical-spec.md → Verdict Execution → Removal inventories
**Feature:** none
**Verification:** human — no recipe

**Preconditions:**
- Setup block pasted.

**Steps:**
1. `sed -n '/^#### \[DEV-011\]/,$p' "$CL/$SPEC/drift-log.md" | grep -c '^  - '`
2. `(cd "$CL" && grep -cE '^\*\*(Design divergence \(boundary-crossing route\)|Switch|Route|Sketches|Choice)\.\*\*' commands/implement-story.md; grep -c 'gate0-divergence' scripts/tests/test_review_override.py)`
3. `(cd "$CL" && grep -n '^\*\*Bug path:\*\*' commands/implement-story.md commands/prototype.md | cut -c1-55)`
4. `(cd "$CL" && grep -n '"commands/implement-story.md":' scripts/tests/test_governor_enforcement.py; grep -n '^IMPLEMENT_STORY_CAP' scripts/tests/test_review_route_rigor.py; wc -c < commands/implement-story.md | tr -d ' ')`
5. `` (cd "$CL" && grep -c '^## Recorded Test Results' agents/review-agent.md; grep '^| `review-override.py`' .writ/docs/agent-cli-contract.md; grep -o '[0-9]* skills are live today' README.md) ``
6. `(cd "$CL" && grep -n 'Fixing a bug' skills/tdd-cycle/SKILL.md; git show c687fab^:skills/tdd-cycle/SKILL.md | grep -n 'Fixing a bug\|parseDate')`
7. `(cd "$CL" && wc -c < commands/retro.md | tr -d ' '; wc -c < commands/refresh-command.md | tr -d ' ')`

**Expected Result:**
- Step 1: `8` (eight correction bullets).
- Step 2: `5` (Gate 0's divergence block is five bold-led paragraphs; "block" in the inventory means all five, from design-divergence DEV-009); `1` (`test_review_override.py` names `gate0-divergence` only as a value `switch` refuses; it is not Gate 0 wiring).
- Step 3: `commands/implement-story.md:246:**Bug path:** …` and `commands/prototype.md:199:**Bug path:** …` (repro-first DEV-012 and DEV-013: delete these as built).
- Step 4: `641:    "commands/implement-story.md": 15717,`; `525:IMPLEMENT_STORY_CAP = 40682`; `40677` (repro-first DEV-010: any removal re-pins both downward from the values present at Story 4 time, unless both review-route upgrades go and `test_review_route_rigor.py` is deleted).
- Step 5: `1` (the `## Recorded Test Results` block in `agents/review-agent.md`, part of safety-fact's removal per review-route-rigor DEV-018); ``| `review-override.py` | check |  | commands/implement-story.md, commands/review.md |`` (reviewer-filters' removal drops `commands/review.md` from this Callers cell, review-route-rigor DEV-005); `19 skills are live today` (each removed skill decrements it, review-route-rigor DEV-006).
- Step 6: ``40:- Fixing a bug: follow `### Bug fixes: repro first` under How to Apply.`` now; before repro-first (`c687fab^`), `40:- Fixing a bug: reproduce it with a failing test first, then make that test pass,` and `114:red:   test "parseDate('') returns null, does not throw"   → fails (throws)`, the first of the three-line example. A repro-first removal restores both (repro-first DEV-007).
- Step 7: `19986` and `23187` (reference only; no removal touches either file).

**Implementation Reference:** Story 3 — drift-log.md DEV-011; sibling drift logs: design-divergence DEV-009, review-route-rigor DEV-005/DEV-006/DEV-018, repro-first-bug-fixing DEV-007/DEV-010/DEV-012/DEV-013

**Status:** [ ] Pass  [ ] Fail

**Notes:**

---

## Human Handoff: Labeling and Story 4 Follow-Through

Story 3 stops at `rating-handoff.md`. Whether each upgrade stays rests on one person's labels and one acknowledgment (Hardest Constraint; Business Rule 9). Scenario 20 checks that an agent cannot get past that gate. Scenario 21 is the labeling. Scenarios 22 and 23 check the Story 4 run that follows it, including the DEV-011 corrections.

### Scenario 20: Before any labels, `/implement-story` on Story 4 stops at task 4.1 and changes nothing

**Source:** Business Rule 9 (Human gate) — Spec; Story 4 task 4.1 and Notes; Shadow Path "Story 4" (nil: `labeled_by` null → stop at task 4.1); `user-stories/README.md`
**Feature:** none
**Verification:** human — no recipe

**Preconditions:**
- Setup block pasted; `reset` prints nothing; `tf` prints `labeled_by=None null_labels=6 of 6 acks={}`. The clone is pinned at `6b3267a`, so this holds even after Scenario 21.
- `live` running in a new session from the second shell.

**Steps:**
1. `/implement-story .writ/specs/2026-10-25-gate-upgrade-removal-measurement/user-stories/story-4-act-on-labeled-trial.md`
2. Let it run until it stops or asks you something. If it asks how to proceed, reply `Stop here.` If it starts filling `labeling-sheet.md`, running `label`, writing `trial-report.md`, or editing `commands/`, `agents/`, `skills/`, or `scripts/`, press Escape: that is a Fail.
3. In the first shell: `tf; git -C "$CL" status --short; ls "$CL/$SPEC/trial-report.md" 2>&1; sed -n 3p "$CL/$SPEC/user-stories/story-4-act-on-labeled-trial.md"; git -C "$CL" rev-parse --short HEAD`
4. `reset`

**Expected Result:**
- Step 2: the session reports that Story 4 waits on human input (`labeled_by` is null and the sheet is unfilled) and stops at task 4.1. It does not fill the sheet, run `label`, or act on any `report` output.
- Step 3: `labeled_by=None null_labels=6 of 6 acks={}`; `git status` shows no change to the sheet, the trial JSON, `commands/`, `agents/`, `skills/`, or `scripts/` (a note in `.writ/context.md` or the story file saying it waits is acceptable); no `trial-report.md`; the story status is not `Completed ✅` and not marked skipped; HEAD is still `6b3267a`.
- Step 4: prints nothing.

**Status:** [ ] Pass  [ ] Fail

**Notes:**

---

### Scenario 21: The labeling — the maintainer fills the sheet, runs `label`, and reads the verdicts

**Source:** Hardest Constraint and Business Rules 6, 7, 9 — Spec; `rating-handoff.md` (What to open, Label rule, Acknowledgment rule, Commands); Interaction Edge Case (a Gate 0 finding whose sketch line does not avoid it); Story 4 task 4.1 precondition
**Feature:** none
**Verification:** human — no recipe

**Preconditions:**
- You are the labeler the handoff names (Adam Sellke). No agent runs this scenario or any step of it.
- You have not opened the trial JSON or anything under `.writ/state/gate-upgrade-trial/<story slug>/`.
- The primary checkout is on `phase/15-code-level-rigor`, and `git -C "$REPO" status --short -- .writ/eval/gate-upgrade-trial .writ/specs/2026-10-25-gate-upgrade-removal-measurement` prints nothing.
- `(cd "$REPO" && python3 $TD/gate-upgrade-trial.py report --trial $TRIAL | head -1)` prints `unverifiable`; `tf "$REPO/$TRIAL"` prints `labeled_by=None null_labels=6 of 6 acks={}`; `ls "$REPO/.writ/state/gate-upgrade-trial/findings"` lists `F01.md` to `F06.md`.
- In the first shell: `Y1=$(ysnap "$YUSS")`.

**Steps:**
1. Read `.writ/specs/2026-10-25-gate-upgrade-removal-measurement/rating-handoff.md` in the primary checkout: § Label rule, § Acknowledgment rule, § Exercise counts, § Caveats.
2. Open `.writ/eval/gate-upgrade-trial/labeling-sheet.md` in an editor. For each of F01 to F06, open the file on its `excerpt:` line (for example `open "$REPO/.writ/state/gate-upgrade-trial/findings/F01.md"`) and judge it against the story's acceptance criteria at its story commit (the handoff lists the four commits). To read code or the story there, use only `git -C "$YUSS" show <story_commit>:<path>`. For a finding whose excerpt has an `**Avoided by:**` line, the quoted sketch line must also avoid the defect, or it is `invalid`.
3. Fill `label:` with `valid` or `invalid` for F01 to F06, optionally a one-line `note:` (no backticks, at most 200 characters, no quoted source), and the `ack:` under `### not exercised: repro-first` with `remove` or `amend`. Change nothing else and keep the file's final newline. Save.
4. `git -C "$REPO" diff --stat; git -C "$REPO" diff -U0 -- .writ/eval/gate-upgrade-trial/labeling-sheet.md | grep -E '^[-+][^-+]' | grep -cvE '^[-+](label|note|ack):'`
5. `(cd "$REPO" && python3 $TD/gate-upgrade-trial.py label --trial $TRIAL --sheet $TD/labeling-sheet.md --labeled-by "Adam Sellke")`
6. `(cd "$REPO" && python3 $TD/gate-upgrade-trial.py report --trial $TRIAL)`
7. `git -C "$REPO" status --short; tf "$REPO/$TRIAL"; [ "$Y1" = "$(ysnap "$YUSS")" ] && echo "yuss unchanged"`

**Expected Result:**
- Step 4: one file changed, `labeling-sheet.md`, with 7 to 13 insertions and the same number of deletions (six labels, the ack, and any notes); then `0` (every changed line is a field line).
- Step 5: `pass`, `labeled: 6 (valid V, invalid 6−V)`, `acks: repro-first=<your ack>`, `labeled_by: Adam Sellke`, `gate-upgrade-trial: labels stored — 6 findings, 1 acknowledgment`. A refusal exits 2 with one stderr `reason:` line and leaves the trial file unchanged: `bad_field` names the line to fix; `sheet_changed` means a non-field line changed or the final newline was lost, so restore with `git -C "$REPO" checkout -- .writ/eval/gate-upgrade-trial/labeling-sheet.md` and fill again. Fix it and repeat Step 5; a refusal is not a Fail. Labels stored despite a blank or bad field are.
- Step 6: line 1 is `pass` when the ack is `remove`, or `unverifiable` with the single line `reason: repro-first amendment_requested` when it is `amend`. The four `story:` lines match Scenario 16. Then:
  - `upgrade: gate0-divergence verdict=<keep|remove> exercised=3/4 upgrade_only=3 valid=a invalid=3−a off_only=0`, `keep` exactly when a is 1 or more
  - `upgrade: safety-fact verdict=<keep|remove> exercised=4/4 upgrade_only=2 valid=b invalid=2−b off_only=0`
  - `upgrade: reviewer-filters verdict=<keep|remove> exercised=4/4 upgrade_only=1 valid=c invalid=1−c off_only=0`
  - `upgrade: repro-first verdict=remove exercised=0/4 reason=not_exercised` (ack `remove`) or `upgrade: repro-first verdict=unverifiable exercised=0/4 reason=amendment_requested` (ack `amend`)
  - a + b + c equals V from Step 5; the `sample:`, `proxy:`, and `blinding:` lines; `yuss: unchanged`; last, `gate-upgrade-trial: keep K, remove R, unverifiable U, absent 0 — 4 stories`, agreeing with the four lines. Any `unlabeled` here is a Fail.
- Step 7: exactly two modified files, `.writ/eval/gate-upgrade-trial/2026-10-29-gate-upgrade-trial.json` and `.writ/eval/gate-upgrade-trial/labeling-sheet.md`; `labeled_by=Adam Sellke null_labels=0 of 6 acks={'repro-first': '<your ack>'}`; `yuss unchanged` (if not, and you changed nothing there, check whether other work touched yuss meanwhile and note it). Do not commit the two files: Story 4 commits them with the report (Scenario 22).
- After this scenario, Scenarios 22 and 23 may run.

**Status:** [ ] Pass  [ ] Fail

**Notes:**

---

### Scenario 22: Story 4 commits the report verbatim with the labeled trial file before any removal, records the result, and deletes the harness last

**Source:** `rating-handoff.md` § Commands (Story 3 → Story 4); Story 4 AC-4.1, AC-4.4, AC-4.5 (pending story); Business Rules 10 (Commit order) and 13 (Spec status); Shadow Path "Story 4" (every verdict `keep` → records only)
**Feature:** none
**Verification:** human — no recipe

**Preconditions:**
- **After labeling.** Scenario 21 passed, and `git -C "$REPO" status --short` shows only the two labeled files.
- No other session is editing the primary checkout. This is the real Story 4 run: it commits to `phase/15-code-level-rigor` and removes upgrades.
- In the first shell: `B=$(git -C "$REPO" rev-parse --short HEAD); (cd "$REPO" && python3 $TD/gate-upgrade-trial.py report --trial $TRIAL) > "$W/report-before.txt"; head -1 "$W/report-before.txt"; grep '^upgrade:' "$W/report-before.txt"` prints `pass` (or `unverifiable` after an `amend`) and the four lines from Scenario 21 Step 6.

**Steps:**
1. Open a new Claude Code session in the primary checkout and run `/implement-spec .writ/specs/2026-10-25-gate-upgrade-removal-measurement`, as `rating-handoff.md` § Commands says. Let it finish.
2. In the first shell: `git -C "$REPO" log --reverse --format='%h %s' "$B"..HEAD`
3. `F=$(git -C "$REPO" rev-list --reverse "$B"..HEAD | head -1); git -C "$REPO" show --stat --format='%h %s' "$F"`
4. `diff "$W/report-before.txt" <(git -C "$REPO" show "$F:$SPEC/trial-report.md") && echo verbatim; tf "$REPO/$TRIAL"`
5. `git -C "$REPO" log --format='%h %s' --diff-filter=D "$B"..HEAD -- $TD/gate-upgrade-trial.py scripts/tests/test_gate_upgrade_trial.py scripts/tests/fixtures/gate-upgrade-trial; ls "$REPO/$TD/gate-upgrade-trial.py" "$REPO/scripts/tests/test_gate_upgrade_trial.py" "$REPO/scripts/tests/fixtures/gate-upgrade-trial" 2>&1 | grep -c 'No such file'`
6. `(cd "$REPO" && uv run pytest scripts/tests/test_gate_upgrade_trial_outcome.py -q -rs 2>&1 | tail -1)`
7. `sed -n 3p "$REPO/$SPEC/spec.md"; git -C "$REPO" diff --stat "$B"..HEAD -- .writ/product/roadmap.md | tail -1; grep -n 'Removal measurement' "$REPO/.writ/product/roadmap.md" | cut -c1-400; git -C "$REPO" diff -U0 "$B"..HEAD -- .writ/decision-records/adr-030-contract-verifier-boundary-front-door.md | grep '^+[^+]' | cut -c1-400`
8. `(cd "$REPO" && uv run pytest -q 2>&1 | tail -1; uv run --python 3.9 pytest -q 2>&1 | tail -1; for t in scripts/tests/test_*.sh; do bash "$t" >/dev/null 2>&1 || echo "FAIL $t"; done; echo "bash loop done"; python3 scripts/gen-platform-trees.py --check | tail -1; bash scripts/eval.sh >/dev/null; echo "eval exit $?")`

**Expected Result:**
- Step 1: the run resumes at Story 4, passes task 4.1 (a person labeled every finding), runs `report`, and acts on each verdict without asking you to label anything.
- Step 2: one or more commits after `$B`; the first is the report commit.
- Step 3: the first commit adds `.writ/specs/2026-10-25-gate-upgrade-removal-measurement/trial-report.md` and carries the labeled trial file (and may carry the filled sheet); it changes nothing under `commands/`, `agents/`, `skills/`, `scripts/`, `plugins/`, `.writ/docs/`, `README.md`, or `.writ/manifest.yaml`.
- Step 4: `verbatim`; `labeled_by=Adam Sellke null_labels=0 of 6 acks={'repro-first': '<your ack>'}`.
- Step 5: one commit that deletes the harness, its unit tests, and their fixtures, after every removal and record commit (only a commit recording Story 4's SHA, or a lane merge, may follow it); `3`.
- Step 6: `41 passed`: the four live checks now run (no skip) and agree with the repo, and the 37 unit tests still pass without the harness.
- Step 7: `> **Status:** Complete` when every verdict is `keep`, `remove`, or `absent`, else `> **Status:** In Progress — <reason from the report>` (for an `amend`, `repro-first amendment_requested`); `1 file changed, 1 insertion(+), 1 deletion(-)` (the roadmap's one line only); the Phase 15 "Removal measurement" line ending with the date, a link to `trial-report.md`, and one word per upgrade (`kept` or `removed`); added ADR-030 § Review lines with the date, the four story IDs, each upgrade's verdict and valid count, the not-exercised reason for repro-first, the proxy and small-sample caveats, and the Gate 0 / blind-trial outcome (Business Rule 12).
- Step 8: no `failed` in either pytest summary; `bash loop done` with no `FAIL` line; `gen-platform-trees: pass (0 stale, 0 missing, 0 orphan, 0 unmapped, 0 vendor)`; `eval exit 0`.
- Then regenerate this plan (`/create-uat-plan 2026-10-25-gate-upgrade-removal-measurement`) to give Story 4's AC-4.1 to AC-4.5 their own scenarios.

**Status:** [ ] Pass  [ ] Fail

**Notes:**

---

### Scenario 23: Story 4 applies each `remove` inventory as amended by DEV-011, leaves every other upgrade untouched, and follows Business Rule 12 for Gate 0

**Source:** Story 4 AC-4.2 and AC-4.3 (pending story); Business Rules 11 (Removal) and 12 (Gate 0 and the blind trial); DEV-011; Interaction Edge Cases (Gate 0 removed after `init`; this trial removes Gate 0 while the blind trial keeps the skill; both review-route upgrades removed; two removals editing `commands/implement-story.md`); Shadow Path "Story 4" (a removal leaves `rg` hits); Error Map "Story 4" (`unverifiable` → untouched)
**Feature:** none
**Verification:** human — no recipe

**Preconditions:**
- **After labeling.** Scenario 22 passed, in the same shell (`$B` and `$W/report-before.txt` are set).

**Steps:**
1. `grep '^upgrade:' "$W/report-before.txt"; head -1 "$REPO/.writ/specs/2026-10-25-design-divergence/trial-report.md" 2>&1`
2. Run the line for each upgrade whose verdict is `remove`:
   - gate0-divergence: `(cd "$REPO" && rg -n 'Gate 0 Divergence|Design divergence \(boundary-crossing route\)' commands .writ/docs; grep -cE '^\*\*(Switch|Route|Sketches|Choice)\.\*\*' commands/implement-story.md; git diff --stat "$B"..HEAD -- scripts/tests/test_review_override.py | tail -1; grep -n 'status_evidence' skills/design-divergence/SKILL.md 2>&1 | cut -c1-200)`
   - safety-fact: `(cd "$REPO" && ls -d skills/blast-radius 2>&1; rg -n 'Safety Fact' commands agents .writ/docs; grep -c '^## Recorded Test Results' agents/review-agent.md)`
   - reviewer-filters: `` (cd "$REPO" && ls -d skills/review-judgment-filters 2>&1; rg -n 'Reviewer Filters|reviewer_filters' commands agents .writ/docs; grep '^| `review-override.py`' .writ/docs/agent-cli-contract.md) ``
   - repro-first: `(cd "$REPO" && ls scripts/repro-order.py 2>&1; rg -n 'Repro First' commands agents skills .writ/docs; grep -n 'Fixing a bug' skills/tdd-cycle/SKILL.md; grep -c "parseDate('')" skills/tdd-cycle/SKILL.md; grep -c '^\*\*Bug path:\*\*' commands/implement-story.md commands/prototype.md)`
3. If safety-fact or reviewer-filters was removed: `(cd "$REPO" && grep -o '[0-9]* skills are live today' README.md; ls scripts/tests/test_review_route_rigor.py 2>&1; python3 scripts/review-override.py --help 2>&1 | grep -c switch)`
4. If any upgrade was removed: `(cd "$REPO" && grep -n '"commands/implement-story.md":' scripts/tests/test_governor_enforcement.py; grep -n 'gate-upgrade-removal-measurement' scripts/tests/test_governor_enforcement.py | cut -c1-160; grep -n '^IMPLEMENT_STORY_CAP' scripts/tests/test_review_route_rigor.py 2>&1; git log --format=%h "$B"..HEAD -- scripts/tests/test_governor_enforcement.py | wc -l | tr -d ' ')`
5. For each upgrade whose verdict is `keep` or `unverifiable`: `(cd "$REPO" && grep -c 'Design divergence (boundary-crossing route)' commands/implement-story.md; ls skills/blast-radius/SKILL.md skills/review-judgment-filters/SKILL.md scripts/repro-order.py 2>&1)` and read that upgrade's line.
6. `git -C "$REPO" diff --stat "$B"..HEAD -- commands/why.md commands/writ.md commands/retro.md commands/refresh-command.md`

**Expected Result:**
- Step 1: the four verdict lines from Scenario 21; the blind-trial report is absent (`No such file`) while `2026-10-25-design-divergence` still awaits its rating, or its line 1 reads `keep` or `remove`.
- Step 2, per removed upgrade:
  - gate0-divergence: `rg` prints nothing; `0` (all five bold-led paragraphs of the divergence block are gone, DEV-011); no diff line for `test_review_override.py` unless both review-route upgrades were also removed. Business Rule 12: when the blind trial has said `keep` or has not reported, `skills/design-divergence/SKILL.md` remains and its `status_evidence` names `/prototype` as the one consumer, and the ADR-030 note says why the "two live callers" wording no longer holds; when it said `remove` before Story 4, the wiring was already gone and Story 4 recorded "already removed by design-divergence Story 6" instead of editing.
  - safety-fact: `ls` reports no such directory; `rg` prints nothing; `0` (the `## Recorded Test Results` block is gone from `agents/review-agent.md`, DEV-011).
  - reviewer-filters: `ls` reports no such directory; `rg` prints nothing; the `review-override.py` row's Callers cell no longer lists `commands/review.md` (DEV-011).
  - repro-first: `ls` reports no such file; `rg` prints nothing; the When to Use bullet reads `- Fixing a bug: reproduce it with a failing test first, then make that test pass,` again; `1` or more (the three-line red/green/refactor `parseDate('')` example is back, as at `c687fab^`); `commands/implement-story.md:0` and `commands/prototype.md:0` (both `**Bug path:**` paragraphs deleted as built, DEV-011).
- Step 3: `N skills are live today` with N equal to 19 minus the number of skills removed (`blast-radius`, `review-judgment-filters`), matching the README Skills table. When both review-route upgrades were removed, `test_review_route_rigor.py` is gone and the help names no `switch` (`0`); otherwise the file exists and `switch` is still listed.
- Step 4: the `"commands/implement-story.md":` pin is below `15717`; a dated disclosure line names this spec and Story 4; `IMPLEMENT_STORY_CAP` is below `40682` (or the file is gone, as in Step 3); `1` (re-pinned once, even when two removals edited `commands/implement-story.md` in one pass).
- Step 5: each kept or unverifiable upgrade still reads as it did at `init`: Gate 0 prints `1` (unless Business Rule 12's already-removed case applies), and the kept upgrade's file is listed. An `unverifiable` upgrade (an `amend` ack) is untouched and named in the spec status (Scenario 22 Step 7).
- Step 6: prints nothing.

**Status:** [ ] Pass  [ ] Fail

**Notes:**

---

## Pending Stories

The following stories are not yet complete. Scenarios will be added when they complete:

- **Story 4:** Act on the Labeled Trial (Human-Gated) — Status: Not Started. It waits on the labeling (Scenario 21) and on the `repro-first` acknowledgment; Scenarios 22 and 23 check its run, including the DEV-011 corrections. Its acceptance criteria (AC-4.1 to AC-4.5: report committed first, each `remove` inventory applied, `keep`/`unverifiable`/`absent` untouched, roadmap and ADR-030 records, harness deleted) get their own scenarios when it completes.
