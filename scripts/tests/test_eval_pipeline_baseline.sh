#!/usr/bin/env bash
# Tests check_pipeline_baseline in scripts/eval.sh (spec
# 2026-09-05-phase11-repair-and-baseline, Story 5, AC-5.2 / AC-5.3).
#
# Harness: copy eval.sh and pipeline-baseline.py into a temp scripts/ so
# PROJECT_ROOT is the fixture tree. No mutation of the real repository.
set -euo pipefail

REPO="$(cd "$(dirname "$0")/../.." && pwd)"
EVAL="$REPO/scripts/eval.sh"
HELPER="$REPO/scripts/pipeline-baseline.py"

pass_count=0
fail() {
  printf 'FAIL: %s\n' "$1" >&2
  exit 1
}
ok() {
  pass_count=$((pass_count + 1))
  printf 'PASS: %s\n' "$1"
}

TMP_ROOTS=()
cleanup() {
  local rc=$? root
  for root in "${TMP_ROOTS[@]:-}"; do
    [ -n "$root" ] || continue
    rm -rf "$root"
  done
  return "$rc"
}
trap cleanup EXIT

new_root() {
  local root
  root="$(mktemp -d)"
  TMP_ROOTS+=("$root")
  mkdir -p "$root/scripts"
  cp "$EVAL" "$root/scripts/eval.sh"
  cp "$HELPER" "$root/scripts/pipeline-baseline.py"
  printf "%s" "$root"
}

run_check() {
  local root="$1" rc=0
  ( cd "$root" && bash scripts/eval.sh --check=pipeline-baseline --report=eval-report.md >/dev/null 2>&1 ) || rc=$?
  printf "%s" "$rc"
}

report_of() {
  cat "$1/eval-report.md"
}

# Write an eight-record clean fixture (or a mutated one) via the copied helper.
write_fixture() {
  local dest="$1" mutate="${2:-}"
  python3 - "$dest" "$mutate" <<'PY'
import importlib.util
import json
import sys
from pathlib import Path

dest = Path(sys.argv[1])
mutate = sys.argv[2]
spec = importlib.util.spec_from_file_location(
    "pipeline_baseline", Path("scripts/pipeline-baseline.py").resolve())
pb = importlib.util.module_from_spec(spec)
sys.modules["pipeline_baseline"] = pb
spec.loader.exec_module(pb)

def hexn(n):
    return "%040x" % n

selection = []
runs = []
for i, cls in enumerate(pb.SURFACE_CLASSES):
    sid = "f%d/story-%d" % (i, i)
    selection.append({
        "story_path": "s%d.md" % i, "spec_folder": "f%d" % i, "story_id": sid,
        "story_commit": hexn(i), "parent_sha": hexn(100 + i),
        "parent_is_merge": False, "surface_class": cls,
        "eligible_classes": [cls], "test_files": ["t%d.test.ts" % i],
        "criteria_values": {"status": "Completed"},
    })
    for n in range(1, 3):
        rec = pb._null_record(sid, n, "2026-09-06T00:00:00Z")
        rec["status"] = "complete"
        rec["gates"]["gate4_tests"]["integrity"] = None
        rec["wall_clock_s"] = 10.0
        rec["num_turns"] = 4
        rec["tokens"] = {k: 1 for k in pb.TOKEN_KEYS}
        rec["tokens_main_thread"] = {k: 1 for k in pb.TOKEN_KEYS}
        rec["cost_usd"] = 0.1
        rec["interrupts"] = {k: 0 for k in pb.INTERRUPT_KEYS}
        rec["review_iterations"] = 0
        rec["exit_criteria"]["rederived"] = "met"
        rec["invocation"]["argv"] = ["claude", "-p", "go"]
        runs.append(rec)

doc = {
    "schema": pb.SCHEMA, "model": "claude-fable-5-1",
    "generated_at": "2026-09-06T00:00:00Z", "yuss_head": hexn(1),
    "runs_per_story": 2, "criteria": {"status_required": "Completed"},
    "selection": selection, "excluded": [], "rejection_tally": {}, "runs": runs,
}
if mutate == "schema":
    doc["schema"] = "pipeline-baseline-v0"
dest.parent.mkdir(parents=True, exist_ok=True)
dest.write_text(json.dumps(doc, indent=2) + "\n", encoding="utf-8")
PY
}

# ---------------------------------------------------------------------------
# AC-5.2: no dir / empty glob → one add_note, zero findings, exit 0
# ---------------------------------------------------------------------------
ROOT="$(new_root)"
rc="$(run_check "$ROOT")"
[ "$rc" -eq 0 ] || { report_of "$ROOT"; fail "no-dir: expected exit 0, got $rc"; }
grep -q '^PASS' "$ROOT/eval-report.md" || { report_of "$ROOT"; fail "no-dir: report must say PASS"; }
if grep -q '^FAIL' "$ROOT/eval-report.md"; then
  report_of "$ROOT"; fail "no-dir: must have zero findings"
fi
note_count="$(grep -c '^\- NOTE' "$ROOT/eval-report.md" || true)"
[ "$note_count" -eq 1 ] || { report_of "$ROOT"; fail "no-dir: expected exactly one add_note, got $note_count"; }
grep -Fq '.writ/eval/baselines' "$ROOT/eval-report.md" \
  || { report_of "$ROOT"; fail "no-dir: note must name the missing directory"; }
grep -Fq 'pipeline-baseline.py select' "$ROOT/eval-report.md" \
  || { report_of "$ROOT"; fail "no-dir: note must name pipeline-baseline.py select"; }
ok "no dir / empty glob -> one note, zero findings, exit 0"

ROOT="$(new_root)"
mkdir -p "$ROOT/.writ/eval/baselines"
rc="$(run_check "$ROOT")"
[ "$rc" -eq 0 ] || { report_of "$ROOT"; fail "empty-dir: expected exit 0, got $rc"; }
note_count="$(grep -c '^\- NOTE' "$ROOT/eval-report.md" || true)"
[ "$note_count" -eq 1 ] || { report_of "$ROOT"; fail "empty-dir: expected exactly one add_note, got $note_count"; }
ok "empty baselines/ glob -> one note, zero findings, exit 0"

# ---------------------------------------------------------------------------
# AC-5.3: clean eight-record fixture → PASS exit 0
# ---------------------------------------------------------------------------
ROOT="$(new_root)"
mkdir -p "$ROOT/.writ/eval/baselines"
( cd "$ROOT" && write_fixture "$ROOT/.writ/eval/baselines/2026-09-06-claude-fable-5-1.json" )
rc="$(run_check "$ROOT")"
[ "$rc" -eq 0 ] || { report_of "$ROOT"; fail "clean fixture: expected exit 0, got $rc"; }
grep -q '^PASS' "$ROOT/eval-report.md" || { report_of "$ROOT"; fail "clean fixture: report must say PASS"; }
ok "clean eight-record fixture -> exit 0"

# ---------------------------------------------------------------------------
# AC-5.3: one broken fixture → exit 1, one finding per path: reason line
# ---------------------------------------------------------------------------
ROOT="$(new_root)"
mkdir -p "$ROOT/.writ/eval/baselines"
( cd "$ROOT" && write_fixture "$ROOT/.writ/eval/baselines/2026-09-06-claude-fable-5-1.json" schema )
expected="$( ( cd "$ROOT" && python3 scripts/pipeline-baseline.py validate \
  .writ/eval/baselines/2026-09-06-claude-fable-5-1.json || true ) | grep -c ': ' || true)"
[ "$expected" -ge 1 ] || fail "broken fixture: validate produced no path: reason lines"
rc="$(run_check "$ROOT")"
[ "$rc" -eq 1 ] || { report_of "$ROOT"; fail "broken fixture: expected exit 1, got $rc"; }
grep -q "^FAIL ($expected finding" "$ROOT/eval-report.md" \
  || { report_of "$ROOT"; fail "broken fixture: expected $expected finding(s) (one per path: reason line)"; }
ok "one broken fixture -> exit 1, one finding per path: reason line"

awk '/^CHECKS=\(/{f=1} f && /^\)/{exit} f' "$EVAL" | grep -Fxq "  pipeline-baseline" \
  || fail "pipeline-baseline must be registered in CHECKS=(...)"
grep -q '^check_pipeline_baseline()' "$EVAL" \
  || fail "check_pipeline_baseline must be defined in scripts/eval.sh"
ok "registration: pipeline-baseline in CHECKS and check_pipeline_baseline exists"

printf '\nAll %d pipeline-baseline check assertions passed.\n' "$pass_count"
