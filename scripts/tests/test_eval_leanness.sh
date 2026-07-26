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

# usage: per_surface_metric <json-file> <surface> <lines|chars>
per_surface_metric() {
  python3 - "$1" "$2" "$3" <<'PY'
import json, sys
data = json.load(open(sys.argv[1]))
print(data["metrics"]["per_surface"][sys.argv[2]][sys.argv[3]])
PY
}

# ---------------------------------------------------------------------------
# Build a clean, self-consistent temp repo skeleton.
# ---------------------------------------------------------------------------
build_repo() {
  local root="$1"
  mkdir -p "$root/commands" "$root/agents" "$root/skills/sample-skill" \
           "$root/adapters" "$root/scripts/tests" "$root/.writ/decision-records"

  # Non-infra commands: alpha, beta. Infra: _preamble (excluded from parity).
  printf '# Alpha\n\nsome body line\n' > "$root/commands/alpha.md"
  printf '# Beta\n\nsome body line\n'  > "$root/commands/beta.md"
  printf '# Preamble\n\ninfra only\n'  > "$root/commands/_preamble.md"

  printf '# Agent\n' > "$root/agents/sample-agent.md"
  printf 'name: sample-skill\n' > "$root/skills/sample-skill/SKILL.md"

  # Full-surface stubs (Story 1): adapters/, scripts/ (incl. a nested test
  # file so the recursive glob is exercised), system-instructions.md, and a
  # .writ/ file (ungated — reported only, never gated).
  printf '# Adapter\n\nadapter body\n' > "$root/adapters/sample.md"
  printf 'print("stub")\n' > "$root/scripts/tool.py"
  printf '#!/usr/bin/env bash\necho stub\n' > "$root/scripts/deploy.sh"
  printf '#!/usr/bin/env bash\necho nested\n' > "$root/scripts/tests/nested.sh"
  printf '# System Instructions\n\nidentity body\n' > "$root/system-instructions.md"
  printf '# ADR Stub\n\nworkspace body\n' > "$root/.writ/decision-records/adr-000-stub.md"

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

  # Seed the baseline from the helper's own --update-baseline writer so it is
  # always in the current per-surface schema and exactly matches the fixture's
  # current metrics (silent on the ratchet — decrease-or-equal is free).
  python3 "$HELPER" --root "$root" --update-baseline >/dev/null 2>&1
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
OUT1="$(mktemp)"
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
# Scenario 1b (Story 1): full-surface measurement — per_surface covers all six
# gated registry entries, plus total_product_{lines,chars} and the ungated
# writ_workspace_lines.
# ---------------------------------------------------------------------------
for surface in commands agents skills adapters scripts system_instructions; do
  val="$(per_surface_metric "$OUT1" "$surface" lines)"
  [ "$val" -gt 0 ] || fail "per_surface.$surface.lines missing or zero"
done
ok "full-surface measurement: per_surface covers all six gated registry entries"

[ "$(metric "$OUT1" total_product_lines)" -gt 0 ] || fail "total_product_lines missing or zero"
[ "$(metric "$OUT1" total_product_chars)" -gt 0 ] || fail "total_product_chars missing or zero"
ok "full-surface measurement: total_product_lines/chars rolled up"

[ "$(metric "$OUT1" writ_workspace_lines)" -gt 0 ] || fail "writ_workspace_lines missing or zero"
ok "full-surface measurement: ungated writ_workspace_lines reported"

# ---------------------------------------------------------------------------
# Scenario 1c (Story 1): legacy metric keys still present and Tier-B compatible.
# ---------------------------------------------------------------------------
python3 - "$OUT1" <<'PY'
import json, sys
m = json.load(open(sys.argv[1]))["metrics"]
for key in ("commands", "agents", "skills", "command_lines", "command_chars"):
    assert key in m, f"legacy key missing: {key}"
assert m["command_lines"] == m["per_surface"]["commands"]["lines"]
assert m["command_chars"] == m["per_surface"]["commands"]["chars"]
PY
ok "legacy metric keys (commands/agents/skills/command_lines/command_chars) preserved"

# ---------------------------------------------------------------------------
# Scenario 1d (Story 1): the guardian measures itself — no self-exemption.
# Run against the REAL repo (not a fixture) so eval-leanness.py's own bytes
# land inside the `scripts` surface.
# ---------------------------------------------------------------------------
OUT_SELF="$(mktemp)"
python3 "$HELPER" --root "$REPO" > "$OUT_SELF" 2>/dev/null \
  || fail "helper exited non-zero measuring the real repo"
SELF_LINES="$(python3 -c "import subprocess; print(len(open('$HELPER','rb').read().split(b'\n')) - 1)")"
SCRIPTS_LINES="$(per_surface_metric "$OUT_SELF" scripts lines)"
[ "$SCRIPTS_LINES" -ge "$SELF_LINES" ] \
  || fail "scripts surface ($SCRIPTS_LINES lines) does not appear to include eval-leanness.py ($SELF_LINES lines)"
ok "guardian measures itself: scripts surface includes eval-leanness.py, no self-exemption"
rm -f "$OUT_SELF"

# ---------------------------------------------------------------------------
# Scenario 1e (Story 1): unreadable file under a measured surface is skipped
# with a non-blocking warning, never a crash.
# ---------------------------------------------------------------------------
TMP_UNREADABLE="$(mktemp -d)"
build_repo "$TMP_UNREADABLE"
printf '# Locked\n\nnever read\n' > "$TMP_UNREADABLE/commands/locked.md"
printf '| `/locked` | locked command |\n' >> "$TMP_UNREADABLE/README.md"
chmod 000 "$TMP_UNREADABLE/commands/locked.md"
OUT_UNREADABLE="$(mktemp)"
run_helper "$TMP_UNREADABLE" "$OUT_UNREADABLE"
if [ "$(id -u)" -ne 0 ]; then
  [ "$(count_field "$OUT_UNREADABLE" warnings)" -gt 0 ] || fail "unreadable file must emit a warning"
  json_contains "$OUT_UNREADABLE" warnings "locked.md" || fail "unreadable-file warning must name the path"
  ok "unreadable file under a measured surface -> skipped with warning, exit 0"
else
  ok "unreadable file check skipped (running as root; chmod 000 has no effect)"
fi
chmod 644 "$TMP_UNREADABLE/commands/locked.md"
rm -rf "$TMP_UNREADABLE"

# ---------------------------------------------------------------------------
# Scenario 1f (Story 1): --update-baseline writes the new per-surface schema.
# ---------------------------------------------------------------------------
TMP_BASELINE="$(mktemp -d)"
build_repo "$TMP_BASELINE"
python3 "$HELPER" --root "$TMP_BASELINE" --update-baseline >/dev/null 2>&1 \
  || fail "--update-baseline exited non-zero"
python3 - "$TMP_BASELINE" <<'PY'
import json, os, sys
root = sys.argv[1]
b = json.load(open(os.path.join(root, ".writ", "leanness-baseline.json")))
assert b.get("schema") == 2, "baseline schema must be 2 after --update-baseline"
surfaces = b.get("surfaces")
assert isinstance(surfaces, dict), "baseline must have a 'surfaces' map"
for name in ("commands", "agents", "skills", "adapters", "scripts", "system_instructions"):
    entry = surfaces.get(name)
    assert isinstance(entry, dict), f"surfaces.{name} missing"
    assert "lines" in entry and "chars" in entry, f"surfaces.{name} missing lines/chars"
for key in ("recorded", "commands", "agents", "skills", "command_lines", "command_chars", "note"):
    assert key in b, f"legacy top-level key missing after reseed: {key}"
PY
ok "--update-baseline writes per-surface schema (schema=2, surfaces map) + legacy keys"
rm -rf "$TMP_BASELINE"

# ---------------------------------------------------------------------------
# Story 3 fixture: a repo with a `.writ/context.md`, an active spec (spec.md,
# spec-lite.md), and story files under user-stories/ — the declared-load set
# `story_context_bytes` sums.
# ---------------------------------------------------------------------------
build_context_repo() {
  local root="$1"
  build_repo "$root"

  printf '# Writ Project Context\n\nsome context body\n' > "$root/.writ/context.md"

  mkdir -p "$root/.writ/specs/2026-01-01-demo-spec/user-stories"
  printf '# Spec: Demo\n\nsome spec body\n' > "$root/.writ/specs/2026-01-01-demo-spec/spec.md"
  printf '# Spec Lite: Demo\n\nsome spec-lite body\n' > "$root/.writ/specs/2026-01-01-demo-spec/spec-lite.md"
  printf '# Story 1: Demo\n\nSome story body.\n\n## Context for Agents\n\n- **Business rules:** `spec.md -> ## Business Rules`\n' \
    > "$root/.writ/specs/2026-01-01-demo-spec/user-stories/story-1-demo.md"

  # Exact gate-agent filenames the metric mirrors from implement-story.md's
  # routing table (architecture-check, coding, review, testing, documentation).
  for gate in architecture-check-agent coding-agent review-agent testing-agent documentation-agent; do
    printf '# %s\n\nstub agent body for %s\n' "$gate" "$gate" > "$root/agents/${gate}.md"
  done
}

# ---------------------------------------------------------------------------
# Scenario 3a (Story 3): story_context_bytes is present and a non-negative int.
# ---------------------------------------------------------------------------
TMP_CTX="$(mktemp -d)"
build_context_repo "$TMP_CTX"
OUT_CTX="$(mktemp)"
run_helper "$TMP_CTX" "$OUT_CTX"
SCB="$(metric "$OUT_CTX" story_context_bytes)"
[ "$SCB" -ge 0 ] 2>/dev/null || fail "story_context_bytes must be a non-negative integer, got: $SCB"
[ "$SCB" -gt 0 ] || fail "story_context_bytes should be > 0 for a populated fixture"
ok "story_context_bytes: present as a non-negative integer"

# ---------------------------------------------------------------------------
# Scenario 3b (Story 3): determinism — byte-identical across repeated runs on
# an unchanged tree.
# ---------------------------------------------------------------------------
OUT_CTX2="$(mktemp)"
run_helper "$TMP_CTX" "$OUT_CTX2"
SCB2="$(metric "$OUT_CTX2" story_context_bytes)"
[ "$SCB" -eq "$SCB2" ] || fail "story_context_bytes not deterministic: $SCB vs $SCB2"
ok "story_context_bytes: byte-identical across repeated runs on an unchanged tree"

# ---------------------------------------------------------------------------
# Scenario 3c (Story 3): a gate agent file grows by N bytes -> the metric
# increases by exactly N.
# ---------------------------------------------------------------------------
EXTRA=137
python3 -c "
with open('$TMP_CTX/agents/coding-agent.md', 'a') as f:
    f.write('x' * $EXTRA)
"
OUT_CTX3="$(mktemp)"
run_helper "$TMP_CTX" "$OUT_CTX3"
SCB3="$(metric "$OUT_CTX3" story_context_bytes)"
DELTA=$((SCB3 - SCB))
[ "$DELTA" -eq "$EXTRA" ] || fail "growing a gate agent file by $EXTRA bytes should grow story_context_bytes by exactly $EXTRA, got delta $DELTA"
ok "story_context_bytes: tracks declared-load change (+$EXTRA bytes on a gate agent file -> +$EXTRA)"
rm -rf "$TMP_CTX"

# ---------------------------------------------------------------------------
# Scenario 3d (Story 3): missing declared-load artifacts contribute 0, no
# crash, no structural finding, exit 0. The plain build_repo() fixture has no
# .writ/context.md and no .writ/specs/ — exactly the missing-artifact case.
# ---------------------------------------------------------------------------
TMP_NOCTX="$(mktemp -d)"
build_repo "$TMP_NOCTX"
OUT_NOCTX="$(mktemp)"
run_helper "$TMP_NOCTX" "$OUT_NOCTX"
[ "$(count_field "$OUT_NOCTX" structural)" -eq 0 ] || fail "missing story-context artifacts must not produce a structural finding"
SCB_NOCTX="$(metric "$OUT_NOCTX" story_context_bytes)"
[ "$SCB_NOCTX" -ge 0 ] 2>/dev/null || fail "story_context_bytes must still be a non-negative integer when artifacts are absent"
ok "story_context_bytes: absent artifacts contribute 0, exit 0, no structural finding"
rm -rf "$TMP_NOCTX"

# ---------------------------------------------------------------------------
# Scenario 3e (Story 3): the proxy label is present wherever the metric appears.
# ---------------------------------------------------------------------------
python3 - "$OUT1" <<'PY'
import json, sys
m = json.load(open(sys.argv[1]))["metrics"]
assert "story_context_bytes" in m, "story_context_bytes missing from metrics"
note = m.get("story_context_bytes_note", "")
assert "proxy" in note.lower(), "story_context_bytes must carry an explicit proxy-label note"
assert "declared" in note.lower(), "proxy note must say it measures declared load, not consumed tokens"
PY
ok "story_context_bytes: proxy label (declared load, not consumed tokens) present in metrics"

# ---------------------------------------------------------------------------
# Story 2 (coverage guard) scenarios.
# ---------------------------------------------------------------------------

# Scenario 2a: the real repo resolves every top-level entry -> zero coverage
# findings (the registry + OUT_OF_SCOPE must actually match this repo).
OUT_SELF_COV="$(mktemp)"
python3 "$HELPER" --root "$REPO" > "$OUT_SELF_COV" 2>/dev/null \
  || fail "helper exited non-zero running coverage guard on the real repo"
[ "$(count_field "$OUT_SELF_COV" structural)" -eq 0 ] \
  || { cat "$OUT_SELF_COV"; fail "real repo should resolve every top-level entry (zero coverage findings)"; }
ok "coverage guard: real repo resolves every top-level entry, zero findings"
rm -f "$OUT_SELF_COV"

# Scenario 2b: a synthetic undeclared top-level directory -> exactly one
# coverage-guard structural finding naming it, offering both remedies.
TMP_COV="$(mktemp -d)"
build_repo "$TMP_COV"
mkdir -p "$TMP_COV/newthing"
printf 'stray file\n' > "$TMP_COV/newthing/stray.txt"
OUT_COV="$(mktemp)"
run_helper "$TMP_COV" "$OUT_COV"
[ "$(count_field "$OUT_COV" structural)" -eq 1 ] \
  || { cat "$OUT_COV"; fail "expected exactly one coverage finding for the undeclared 'newthing' dir"; }
json_contains "$OUT_COV" structural "newthing" || fail "coverage finding must name 'newthing'"
json_contains "$OUT_COV" structural "out of scope" || fail "coverage finding must offer the out-of-scope remedy"
ok "coverage guard: undeclared top-level dir -> exactly one structural finding naming it"
rm -rf "$TMP_COV"

# Scenario 2c: a registry entry whose path no longer exists on disk -> a
# distinguishable stale-registry structural finding.
TMP_STALE="$(mktemp -d)"
build_repo "$TMP_STALE"
rm -rf "$TMP_STALE/adapters"
OUT_STALE="$(mktemp)"
run_helper "$TMP_STALE" "$OUT_STALE"
[ "$(count_field "$OUT_STALE" structural)" -gt 0 ] || fail "missing registry path (adapters/) must produce a structural finding"
json_contains "$OUT_STALE" structural "adapters" || fail "stale-registry finding must name 'adapters'"
json_contains "$OUT_STALE" structural "does not exist on disk" || fail "stale-registry finding must be distinguishable from the undeclared-entry case"
ok "coverage guard: registry path missing on disk -> distinguishable stale-registry finding"
rm -rf "$TMP_STALE"

# Scenario 2d: declared out-of-scope and dot-prefixed entries stay silent.
TMP_OOS="$(mktemp -d)"
build_repo "$TMP_OOS"
mkdir -p "$TMP_OOS/test" "$TMP_OOS/archive" "$TMP_OOS/.writ-lanes-3" "$TMP_OOS/.cursor"
printf 'noop\n' > "$TMP_OOS/test/spec.test.js"
printf '# License\n' > "$TMP_OOS/LICENSE"
printf '0.1.0\n' > "$TMP_OOS/VERSION"
OUT_OOS="$(mktemp)"
run_helper "$TMP_OOS" "$OUT_OOS"
[ "$(count_field "$OUT_OOS" structural)" -eq 0 ] \
  || { cat "$OUT_OOS"; fail "out-of-scope and dot-prefixed entries must never produce coverage findings"; }
ok "coverage guard: out-of-scope list + dot-prefix rule stay silent (test/, archive/, .writ-lanes-3/, .cursor/, LICENSE, VERSION)"
rm -rf "$TMP_OOS"

# ---------------------------------------------------------------------------
# Scenario 2: orphan — command file with no README table row -> FAIL.
# ---------------------------------------------------------------------------
TMP2="$(mktemp -d)"
build_repo "$TMP2"
printf '# Ghost\n' > "$TMP2/commands/ghost.md"
OUT2="$(mktemp)"
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
OUT3="$(mktemp)"
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
OUT4="$(mktemp)"
run_helper "$TMP4" "$OUT4"

[ "$(count_field "$OUT4" structural)" -gt 0 ] || fail "README phantom not detected"
json_contains "$OUT4" structural "nowhere" || fail "phantom finding must name nowhere"
ok "phantom (README table names missing file) -> structural FAIL"
rm -rf "$TMP4"

# ---------------------------------------------------------------------------
# Story 4 (reduction ratchet) scenarios. Replaces the old +10%-tolerance test:
# GROWTH_TOLERANCE is gone — every gated surface ratchets against its own
# per-surface baseline instead of one aggregate percentage.
# ---------------------------------------------------------------------------
set_surface_field() {
  # usage: set_surface_field <baseline.json> <surface> <field> <value(json-literal)>
  python3 - "$1" "$2" "$3" "$4" <<'PY'
import json, sys
path, surface, field, raw = sys.argv[1:5]
b = json.load(open(path))
b["surfaces"][surface][field] = json.loads(raw)
json.dump(b, open(path, "w"))
PY
}

# Scenario 4a: decrease -> silent, and --update-baseline ratchets it down.
TMP5="$(mktemp -d)"
build_repo "$TMP5"
BASE5="$TMP5/.writ/leanness-baseline.json"
BASE5_COMMANDS_LINES_BEFORE="$(python3 -c "import json; print(json.load(open('$BASE5'))['surfaces']['commands']['lines'])")"
# Shrink commands/ so current < baseline.
: > "$TMP5/commands/beta.md"
printf '# Beta\n' > "$TMP5/commands/beta.md"
OUT5A="$(mktemp)"
run_helper "$TMP5" "$OUT5A"
[ "$(count_field "$OUT5A" warnings)" -eq 0 ] || { cat "$OUT5A"; fail "a decreased surface must not warn"; }
ok "ratchet: current <= baseline -> silent (zero warnings)"

python3 "$HELPER" --root "$TMP5" --update-baseline >/dev/null 2>&1
BASE5_COMMANDS_LINES_AFTER="$(python3 -c "import json; print(json.load(open('$BASE5'))['surfaces']['commands']['lines'])")"
[ "$BASE5_COMMANDS_LINES_AFTER" -lt "$BASE5_COMMANDS_LINES_BEFORE" ] \
  || fail "--update-baseline must ratchet a decreased surface's baseline down ($BASE5_COMMANDS_LINES_BEFORE -> $BASE5_COMMANDS_LINES_AFTER expected lower)"
ok "ratchet: --update-baseline auto-ratchets a decreased surface's baseline down"
rm -rf "$TMP5"

# Scenario 4b: unjustified increase -> warning naming surface, baseline,
# current, and delta; zero structural findings for this condition.
TMP6="$(mktemp -d)"
build_repo "$TMP6"
BASE6="$TMP6/.writ/leanness-baseline.json"
printf '# Alpha\n\nsome body line\nanother new line of growth\n' > "$TMP6/commands/alpha.md"
OUT6="$(mktemp)"
run_helper "$TMP6" "$OUT6"
[ "$(count_field "$OUT6" structural)" -eq 0 ] || { cat "$OUT6"; fail "unjustified growth must not be structural"; }
[ "$(count_field "$OUT6" warnings)" -gt 0 ] || fail "unjustified growth must emit a warning"
json_contains "$OUT6" warnings "commands" || fail "growth warning must name the 'commands' surface"
ok "ratchet: unjustified increase -> warning naming surface + delta, zero structural findings"
rm -rf "$TMP6"

# Scenario 4c: justified increase -> silent (zero warnings for that surface).
TMP7="$(mktemp -d)"
build_repo "$TMP7"
BASE7="$TMP7/.writ/leanness-baseline.json"
printf '# Alpha\n\nsome body line\nanother new line of growth\n' > "$TMP7/commands/alpha.md"
set_surface_field "$BASE7" commands justification '"Deliberate: added an alpha usage example."'
OUT7="$(mktemp)"
run_helper "$TMP7" "$OUT7"
[ "$(count_field "$OUT7" structural)" -eq 0 ] || fail "justified growth must not be structural"
if json_contains "$OUT7" warnings "commands"; then
  fail "justified growth must be silent — a non-empty justification suppresses the warning"
fi
ok "ratchet: justified increase (non-empty justification) -> silent"
rm -rf "$TMP7"

# Scenario 4d: legacy (schema 1 / no 'surfaces' key) baseline -> structural
# finding directing the maintainer to migrate via --update-baseline.
TMP8="$(mktemp -d)"
build_repo "$TMP8"
BASE8="$TMP8/.writ/leanness-baseline.json"
python3 - "$BASE8" <<'PY'
import json, sys
json.dump({
    "recorded": "2026-07-11",
    "commands": 4, "agents": 1, "skills": 1,
    "command_lines": 16, "command_chars": 188,
    "note": "legacy schema",
}, open(sys.argv[1], "w"))
PY
OUT8="$(mktemp)"
run_helper "$TMP8" "$OUT8"
[ "$(count_field "$OUT8" structural)" -gt 0 ] || fail "legacy (schema 1) baseline must produce a structural finding"
json_contains "$OUT8" structural "update-baseline" || fail "legacy-schema finding must point at --update-baseline"
ok "ratchet: legacy (pre-schema-2) baseline -> structural finding, migrate via --update-baseline"
rm -rf "$TMP8"

# Scenario 4e: count-ceiling warnings remain warn-only alongside the ratchet.
TMP9="$(mktemp -d)"
build_repo "$TMP9"
for i in $(seq 1 40); do
  printf '# Extra %d\n' "$i" > "$TMP9/commands/extra-$i.md"
  printf '| `/extra-%d` | extra command |\n' "$i" >> "$TMP9/README.md"
done
python3 "$HELPER" --root "$TMP9" --update-baseline >/dev/null 2>&1
OUT9="$(mktemp)"
run_helper "$TMP9" "$OUT9"
[ "$(count_field "$OUT9" structural)" -eq 0 ] || { cat "$OUT9"; fail "over-ceiling commands must not be structural"; }
json_contains "$OUT9" warnings "over the soft ceiling" || fail "count-ceiling warning must still fire"
ok "ratchet: count-ceiling warnings (MAX_COMMANDS/etc.) remain warn-only alongside the ratchet"
rm -rf "$TMP9"

# ---------------------------------------------------------------------------
# Scenario 5: missing baseline -> clear structural error, not silent pass.
# ---------------------------------------------------------------------------
TMP6="$(mktemp -d)"
build_repo "$TMP6"
rm -f "$TMP6/.writ/leanness-baseline.json"
OUT6="$(mktemp)"
run_helper "$TMP6" "$OUT6"

[ "$(count_field "$OUT6" structural)" -gt 0 ] || fail "missing baseline must not silently pass"
json_contains "$OUT6" structural "baseline" || fail "missing-baseline finding must name the baseline"
ok "missing baseline -> clear structural error (not silent pass)"
rm -rf "$TMP6"

# ---------------------------------------------------------------------------
# Story 5 (documentation): static presence assertions — ADR-019 exists,
# references ADR-015, and the Tier B template points at it too. This is the
# doc story's "test-first" anchor: a static assertion via the harness rather
# than a unit test, since there is no runtime behavior to exercise.
# ---------------------------------------------------------------------------
ADR019="$REPO/.writ/decision-records/adr-019-full-surface-leanness-measurement.md"
[ -f "$ADR019" ] || fail "ADR-019 must exist at .writ/decision-records/adr-019-full-surface-leanness-measurement.md"
grep -q "ADR-015" "$ADR019" || fail "ADR-019 must reference ADR-015 (Extends / partial supersession)"
ok "ADR-019 exists and references ADR-015"

AUDIT_FORMAT="$REPO/.writ/docs/leanness-audit-format.md"
grep -q "ADR-019" "$AUDIT_FORMAT" || fail "leanness-audit-format.md must reference ADR-019"
grep -q "story_context_bytes" "$AUDIT_FORMAT" || fail "leanness-audit-format.md must document story_context_bytes in its metrics snapshot"
grep -q "per_surface" "$AUDIT_FORMAT" || fail "leanness-audit-format.md must document per_surface in its metrics snapshot"
ok "leanness-audit-format.md references ADR-019 and documents the new metric set"

printf '\nAll %d leanness helper assertions passed.\n' "$pass_count"
