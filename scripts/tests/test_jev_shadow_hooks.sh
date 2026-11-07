#!/usr/bin/env bash
# Story 5 of 2026-09-25-jev-judgment-pilot: pins the /implement-story Gate 3
# `ac-shadow` line, the evaluator `[AC-N.M]` checklist tag format, and a
# replay-mode `ac-shadow` + `shadow-report` run on the synthetic fixture.
# No network: replay only, keys stripped, proxy pointed at a dead port.
# [AC-5.2, AC-5.3, AC-5.5]
set -euo pipefail

REPO="$(cd "$(dirname "$0")/../.." && pwd)"
STORY_CMD="$REPO/commands/implement-story.md"
AGENT="$REPO/agents/evaluator-agent.md"
FIX="$REPO/scripts/tests/fixtures/jev-replay"

fail() { printf 'FAIL: %s\n' "$1" >&2; exit 1; }
ok() { printf 'PASS: %s\n' "$1"; }

# --- implement-story Gate 3 line [AC-5.3] -----------------------------------
GATE3="$(awk '/^#### Gate 3: Review Agent/{f=1} /^#### Gate 3.5:/{f=0} f' "$STORY_CMD")"
[ -n "$GATE3" ] || fail "implement-story.md must have a Gate 3 section"
SHADOW_LINES="$(printf '%s\n' "$GATE3" | grep -F 'jev-judge.py ac-shadow' || true)"
[ "$(printf '%s\n' "$SHADOW_LINES" | grep -c . || true)" = "1" ] \
  || fail "Gate 3 must carry exactly one ac-shadow line"
# 2026-11-06 (lean-story-pipeline Story 3): story-gate.py
# post-review runs `status`, then `ac-shadow` with the saved files; the prose
# names the condition and keeps the advisory-only terms.
for needle in \
  'only when its `status` prints `pass`' \
  'story-report note' \
  'never changes PASS/FAIL/PAUSE' \
  'never counts toward the review loop' \
  'never marks the story `⚠️ DEGRADED`'; do
  printf '%s\n' "$SHADOW_LINES" | grep -Fq "$needle" || fail "ac-shadow line must say: $needle"
done
# 2026-11-04 (2026-11-04-evidence-gated-review Story 4): Gate 3 saves the review
# and recorded run on every verdict, so ac-shadow reuses <review> and <tests>.
# <tests> is the story's targeted run, not the full suite.
for needle in \
  "\`recorded_test_results\` = the orchestrator's run (\`command:\`, \`exit code: N\`, output tail) of the story's tests" \
  'Save the review to `<review>` = `.writ/state/gate3-review-<story-stem>.md`' \
  '`recorded_test_results` to `<tests>` = `.writ/state/gate3-tests-<story-stem>.txt`'; do
  printf '%s\n' "$GATE3" | grep -Fq "$needle" || fail "Gate 3 must say: $needle"
done
python3 - "$STORY_CMD" "$REPO/scripts/story-gate.py" <<'PY' || fail "the ac-shadow line must follow the post-review call inside Gate 3, and story-gate.py must run status then ac-shadow last with the saved files"
import importlib.util, sys
text = open(sys.argv[1], encoding="utf-8").read()
g3 = text.find("#### Gate 3: Review Agent")
override = text.find("python3 scripts/story-gate.py run --phase post-review", g3)
bullet = text.find("A check `pass` or any `unverifiable` verdict → no override", override)
shadow = text.find("jev-judge.py ac-shadow", bullet)
g35 = text.find("#### Gate 3.5:", g3)
assert -1 < g3 < override < bullet < shadow < g35, (g3, override, bullet, shadow, g35)
spec = importlib.util.spec_from_file_location("story_gate", sys.argv[2])
gate = importlib.util.module_from_spec(spec)
spec.loader.exec_module(gate)
assert gate.CHECKS["post-review"][-1].id == "gate3_jev_shadow"
assert gate.CHECKS["post-review"][-1].counted is False
args = " ".join(gate.shadow_args("<story-file>", "<tests>", "<diff>", "<review>"))
assert args == ("ac-shadow --story <story-file> --tests-output <tests> --diff <diff> "
                "--review-output <review>"), args
source = open(sys.argv[2], encoding="utf-8").read()
assert '["status", "--repo", str(ctx.repo)]' in source
PY
ok "implement-story Gate 3 ac-shadow line pinned"

# --- evaluator [AC-N.M] tag format [AC-5.2] ---------------------------------
grep -Fq "ending with the criterion's \`[AC-N.M]\` tag" "$AGENT" \
  || fail "evaluator Output Format must require a trailing [AC-N.M] tag"
grep -Fq '`- [x]` satisfied or `- [ ]` not satisfied' "$AGENT" \
  || fail "evaluator Output Format must name the - [x] / - [ ] verdict marks"
# Every checklist line in the Output Examples section ends with a tag.
EXAMPLES="$(awk '/^## Output Examples/{f=1} /^## Evaluation Guidelines/{f=0} f' "$AGENT")"
CHECKLIST="$(printf '%s\n' "$EXAMPLES" | grep -E '^- \[[ xX]\] ' || true)"
[ -n "$CHECKLIST" ] || fail "Output Examples must show checklist lines"
UNTAGGED="$(printf '%s\n' "$CHECKLIST" | grep -Ev '\[AC-[0-9]+\.[0-9]+\]$' || true)"
[ -z "$UNTAGGED" ] || fail "untagged example checklist line: $UNTAGGED"
ok "evaluator checklist lines carry a trailing [AC-N.M] tag"

# --- replay-mode ac-shadow + shadow-report [AC-5.5] -------------------------
TMP="$(mktemp -d)"
trap 'rm -rf "$TMP"' EXIT
LOG="$TMP/state/jev-shadow.jsonl"
run_jev() {
  env -u TYPESAFE_API_KEY -u AI_GATEWAY_API_KEY -u VERCEL_OIDC_TOKEN \
    HTTPS_PROXY=http://127.0.0.1:9 https_proxy=http://127.0.0.1:9 \
    WRIT_JEV_REPLAY="$FIX" python3 "$REPO/scripts/jev-judge.py" "$@"
}
OUT="$(cd "$TMP" && run_jev ac-shadow --backend typesafe \
  --story "$FIX/ac-shadow/story.md" --tests-output "$FIX/ac-shadow/tests-output.txt" \
  --diff "$FIX/ac-shadow/diff.patch" --review-output "$FIX/ac-shadow/review.md" \
  --log "$LOG" 2>/dev/null)" || fail "replay ac-shadow must exit 0"
[ "$(printf '%s\n' "$OUT" | head -n1)" = "pass" ] || fail "replay ac-shadow verdict must be pass: $OUT"
printf '%s\n' "$OUT" | tail -n1 | grep -Eq '^jev-judge: pass \(judged\) criteria=3 agree=3 false_pass=0 false_block=0 excluded_paths=2 backend=typesafe model=jev-1\.13\.0 ' \
  || fail "ac-shadow summary format changed: $OUT"
[ "$(grep -c . "$LOG")" = "1" ] || fail "ac-shadow must append exactly one row"
python3 - "$LOG" <<'PY' || fail "shadow row shape"
import json, sys
row = json.loads(open(sys.argv[1], encoding="utf-8").read())
assert set(row) == {"ts", "story", "backend", "model", "criteria", "excluded_paths"}, row
assert row["excluded_paths"] == 2 and sorted(row["criteria"]) == ["AC-9.1", "AC-9.2", "AC-9.3"]
assert all(set(c) == {"p", "jev", "evaluator", "agree"} for c in row["criteria"].values())
PY
grep -Fq 'SHADOW_FIXTURE_MARKER' "$LOG" && fail "secret-path content reached the shadow log"
ok "replay ac-shadow wrote one row; summary format pinned; secret paths excluded"

REPORT="$(run_jev shadow-report --log "$LOG")" || fail "shadow-report must exit 0"
[ "$(printf '%s\n' "$REPORT" | head -n1)" = "unverifiable" ] || fail "1 story cannot meet promotion: $REPORT"
printf '%s\n' "$REPORT" | grep -Fxq 'reason: promotion_not_met' || fail "reason must be promotion_not_met"
printf '%s\n' "$REPORT" | tail -n1 | grep -Eq 'rows=1 stories=1 criteria=3 agree=3 agreement=100\.0% false_pass=0 false_block=0 skipped_rows=0 unmet=stories$' \
  || fail "shadow-report summary format changed: $REPORT"
ok "shadow-report reads the log: promotion_not_met at 1 story"

# The generated writ-evaluator.md carries the canonical tag wording
# (2026-10-20-claude-agent-generator AC-2.4).
grep -Fq "ending with the criterion's \`[AC-N.M]\` tag" "$REPO/claude-code/agents/writ-evaluator.md" \
  || fail "claude-code writ-evaluator must require [AC-N.M] tags on checklist lines"
awk '/^### On FAIL/{f=1} /^### On PAUSE/{f=0} f' "$AGENT" | grep -Eq '^- \[ \] .*\[AC-[0-9]+\.[0-9]+\]$' \
  || fail "On FAIL example must show a tagged unsatisfied checklist line"
ok "Claude Code evaluator and On FAIL example carry [AC-N.M] tags"

printf 'All jev shadow hook checks passed.\n'
