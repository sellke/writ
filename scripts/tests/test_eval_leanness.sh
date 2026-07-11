#!/usr/bin/env bash
# Tests scripts/eval-leanness.py — the Tier A leanness tripwire helper.
#
# Verifies the directional registry-parity contract (see DEV-001 in
# .writ/specs/2026-07-11-leanness-guardian/drift-log.md):
#   - README table  ↔ commands/*.md  is BIDIRECTIONAL (orphan + phantom)
#   - /status allowlist → files      is ONE-WAY (phantom only; never orphan)
# plus the warn-only growth signal and the missing-baseline hard error.
set -euo pipefail

REPO="$(cd "$(dirname "$0")/../.." && pwd)"
HELPER="$REPO/scripts/eval-leanness.py"

pass_count=0
fail() {
  printf 'FAIL: %s\n' "$1" >&2
  exit 1
}
ok() {
  pass_count=$((pass_count + 1))
  printf 'PASS: %s\n' "$1"
}

# Read one top-level array/field from the helper's JSON output.
# usage: field <json-file> <structural|warnings> -> prints element count
count_field() {
  python3 - "$1" "$2" <<'PY'
import json, sys
data = json.load(open(sys.argv[1]))
print(len(data[sys.argv[2]]))
PY
}

# usage: json_contains <json-file> <structural|warnings> <substring> -> exit 0 if any element's text contains substring
json_contains() {
  python3 - "$1" "$2" "$3" <<'PY'
import json, sys
data = json.load(open(sys.argv[1]))
needle = sys.argv[3]
hay = " ".join(
    f"{item.get('subject','')} {item.get('what','')} {item.get('fix','')}"
    for item in data[sys.argv[2]]
)
sys.exit(0 if needle in hay else 1)
PY
}

metric() {
  python3 - "$1" "$2" <<'PY'
import json, sys
data = json.load(open(sys.argv[1]))
print(data["metrics"][sys.argv[2]])
PY
}

# ---------------------------------------------------------------------------
# Build a clean, self-consistent temp repo skeleton.
# ---------------------------------------------------------------------------
build_repo() {
  local root="$1"
  mkdir -p "$root/commands" "$root/agents" "$root/skills/sample-skill" "$root/.writ"

  # Non-infra commands: alpha, beta. Infra: _preamble (excluded from parity).
  printf '# Alpha\n\nsome body line\n' > "$root/commands/alpha.md"
  printf '# Beta\n\nsome body line\n'  > "$root/commands/beta.md"
  printf '# Preamble\n\ninfra only\n'  > "$root/commands/_preamble.md"

  printf '# Agent\n' > "$root/agents/sample-agent.md"
  printf 'name: sample-skill\n' > "$root/skills/sample-skill/SKILL.md"

  # README command table names BOTH non-infra commands (authoritative registry).
  cat > "$root/README.md" <<'EOF'
# Demo

## Commands

| Command | Purpose |
|---------|---------|
| `/alpha` | first command |
| `/beta` | second command |
| `/status` | status command |
EOF

  # /status allowlist is a CURATED SUBSET — names only alpha, deliberately omits
  # beta. Directional parity means beta is NOT an orphan for being absent here.
  cat > "$root/commands/status.md" <<'EOF'
# Status

## Maintainer Note: Command Allowlist

Future edits must not introduce commands that do not exist:

`alpha`
EOF

  # Baseline chosen so the clean repo does NOT trip the growth warning.
  python3 - "$root" <<'PY'
import json, sys, glob, os
root = sys.argv[1]
files = glob.glob(os.path.join(root, "commands", "*.md"))
lines = sum(sum(1 for _ in open(f, encoding="utf-8")) for f in files)
chars = sum(os.path.getsize(f) for f in files)
json.dump({
    "recorded": "2026-07-11",
    "commands": len(files),
    "agents": 1,
    "skills": 1,
    "command_lines": lines,
    "command_chars": chars,
    "note": "test baseline",
}, open(os.path.join(root, ".writ", "leanness-baseline.json"), "w"))
PY
}

run_helper() {
  local root="$1" out="$2"
  python3 "$HELPER" --root "$root" > "$out" 2>/dev/null \
    || fail "helper exited non-zero (contract requires always exit 0)"
}

# ---------------------------------------------------------------------------
# Scenario 1: clean repo -> zero structural findings (PASS).
# ---------------------------------------------------------------------------
TMP1="$(mktemp -d)"; trap 'rm -rf "$TMP1"' EXIT
build_repo "$TMP1"
OUT1="$TMP1/out.json"
run_helper "$TMP1" "$OUT1"

[ "$(count_field "$OUT1" structural)" -eq 0 ] \
  || { cat "$OUT1"; fail "clean repo produced structural findings"; }
ok "clean repo: zero structural findings"

# Directional proof: beta is in README but absent from the allowlist — must NOT
# be flagged. (A bidirectional 'both' reading would wrongly fail here.)
if json_contains "$OUT1" structural "beta"; then
  fail "beta wrongly flagged — allowlist must be checked one-way only"
fi
ok "directional: command absent from curated allowlist is not an orphan"

# Metrics count ALL command files including _preamble (matches baseline convention).
[ "$(metric "$OUT1" commands)" -eq 4 ] || fail "commands metric should count all 4 files (alpha, beta, status, _preamble)"
ok "metrics: commands counts all files (incl. _preamble)"

# ---------------------------------------------------------------------------
# Scenario 2: orphan — command file with no README table row -> FAIL.
# ---------------------------------------------------------------------------
TMP2="$(mktemp -d)"
build_repo "$TMP2"
printf '# Ghost\n' > "$TMP2/commands/ghost.md"
OUT2="$TMP2/out.json"
run_helper "$TMP2" "$OUT2"

[ "$(count_field "$OUT2" structural)" -gt 0 ] || fail "orphan not detected"
json_contains "$OUT2" structural "ghost" || fail "orphan finding must name ghost"
ok "orphan (file missing from README table) -> structural FAIL naming ghost"
rm -rf "$TMP2"

# ---------------------------------------------------------------------------
# Scenario 3a: phantom in /status allowlist — name with no file -> FAIL.
# ---------------------------------------------------------------------------
TMP3="$(mktemp -d)"
build_repo "$TMP3"
printf '`phantom-cmd`\n' >> "$TMP3/commands/status.md"
OUT3="$TMP3/out.json"
run_helper "$TMP3" "$OUT3"

[ "$(count_field "$OUT3" structural)" -gt 0 ] || fail "allowlist phantom not detected"
json_contains "$OUT3" structural "phantom-cmd" || fail "phantom finding must name phantom-cmd"
ok "phantom (allowlist names missing file) -> structural FAIL"
rm -rf "$TMP3"

# ---------------------------------------------------------------------------
# Scenario 3b: phantom in README table — name with no file -> FAIL.
# ---------------------------------------------------------------------------
TMP4="$(mktemp -d)"
build_repo "$TMP4"
printf '| `/nowhere` | dangling row |\n' >> "$TMP4/README.md"
OUT4="$TMP4/out.json"
run_helper "$TMP4" "$OUT4"

[ "$(count_field "$OUT4" structural)" -gt 0 ] || fail "README phantom not detected"
json_contains "$OUT4" structural "nowhere" || fail "phantom finding must name nowhere"
ok "phantom (README table names missing file) -> structural FAIL"
rm -rf "$TMP4"

# ---------------------------------------------------------------------------
# Scenario 4: growth > +10% over baseline -> WARNING, non-blocking (exit 0).
# ---------------------------------------------------------------------------
TMP5="$(mktemp -d)"
build_repo "$TMP5"
# Shrink the baseline so current weight is >10% larger.
python3 - "$TMP5" <<'PY'
import json, os, sys
p = os.path.join(sys.argv[1], ".writ", "leanness-baseline.json")
b = json.load(open(p))
b["command_lines"] = 1
b["command_chars"] = 1
json.dump(b, open(p, "w"))
PY
OUT5="$TMP5/out.json"
run_helper "$TMP5" "$OUT5"

[ "$(count_field "$OUT5" structural)" -eq 0 ] || fail "growth must not be structural"
[ "$(count_field "$OUT5" warnings)" -gt 0 ] || fail "growth must emit a warning"
json_contains "$OUT5" warnings "leanness-baseline.json" \
  || fail "growth warning must name the baseline file"
ok "aggregate growth > +10% -> non-blocking WARNING naming baseline"
rm -rf "$TMP5"

# ---------------------------------------------------------------------------
# Scenario 5: missing baseline -> clear structural error, not silent pass.
# ---------------------------------------------------------------------------
TMP6="$(mktemp -d)"
build_repo "$TMP6"
rm -f "$TMP6/.writ/leanness-baseline.json"
OUT6="$TMP6/out.json"
run_helper "$TMP6" "$OUT6"

[ "$(count_field "$OUT6" structural)" -gt 0 ] || fail "missing baseline must not silently pass"
json_contains "$OUT6" structural "baseline" || fail "missing-baseline finding must name the baseline"
ok "missing baseline -> clear structural error (not silent pass)"
rm -rf "$TMP6"

printf '\nAll %d leanness helper assertions passed.\n' "$pass_count"
