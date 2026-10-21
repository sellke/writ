#!/usr/bin/env bash
# The shipped shell check scripts print the agent CLI contract's check shape
# (Story 5 of 2026-10-12-agent-cli-contract; .writ/docs/agent-cli-contract.md,
# Check shape and Usage errors):
#
#   - stdout line 1 is exactly `pass`, `fail`, or `unverifiable`
#   - `reason:` and detail lines follow; a `<tool>: <verdict> (...)` summary is last
#   - exit 0 when the check ran (`pass` or `unverifiable`), 1 on `fail`,
#     2 on a usage error (usage on stderr, stdout empty)
#   - `--help` prints a `usage:` line naming the script and exits 0
#
# Each script runs on a passing, a failing, and an unusable input. Fixtures live
# in a temp dir; nothing here writes inside the repo.
#
# lint-skill.sh, gen-skill.sh (--check, write, --dry-run) [AC-5.1]
# check-agent-parity.sh [AC-5.2; 2026-10-20-claude-agent-generator AC-3.1..AC-3.3]
set -euo pipefail

REPO="$(cd "$(dirname "$0")/../.." && pwd)"
WORK=$(mktemp -d "${TMPDIR:-/tmp}/writ-shell-shape-test.XXXXXX")
trap 'rm -rf "$WORK"' EXIT

pass_count=0
fail() {
  printf 'FAIL: %s\n' "$1" >&2
  exit 1
}
ok() {
  pass_count=$((pass_count + 1))
}

# run <cmd...>: capture stdout in OUT, stderr in ERR, exit code in RC.
run() {
  RC=0
  OUT="$("$@" 2>"$WORK/stderr")" || RC=$?
  ERR="$(cat "$WORK/stderr")"
}

# assert_shape <label> <stem> <verdict> <exit>: line 1 is the verdict, a
# summary starting with the stem is last, and the exit code matches.
assert_shape() {
  local label="$1" stem="$2" verdict="$3" want="$4" first last n
  first="$(printf '%s\n' "$OUT" | sed -n '1p')"
  last="$(printf '%s\n' "$OUT" | sed -n '$p')"
  n="$(printf '%s\n' "$OUT" | grep -c '' || true)"
  [ "$first" = "$verdict" ] || fail "$label: line 1 is '$first', want '$verdict':
$OUT
stderr: $ERR"
  [ "$n" -ge 2 ] || fail "$label: expected a summary after the verdict:
$OUT"
  case "$last" in
    "$stem: $verdict"*) ;;
    *) fail "$label: last line is '$last', want a '$stem: $verdict ...' summary:
$OUT" ;;
  esac
  [ "$RC" -eq "$want" ] || fail "$label: exit $RC, want $want:
$OUT"
}

# assert_usage_error <label> <script-name>: exit 2, stdout empty, usage on stderr.
assert_usage_error() {
  local label="$1" name="$2"
  [ "$RC" -eq 2 ] || fail "$label: usage error must exit 2, got $RC:
$OUT"
  [ -z "$OUT" ] || fail "$label: usage error must leave stdout empty, got:
$OUT"
  printf '%s\n' "$ERR" | grep -qi "usage:.*$name" \
    || fail "$label: stderr must carry a usage line naming $name, got:
$ERR"
}

# assert_help <label> <script-name>: exit 0 and a usage line naming the script.
assert_help() {
  local label="$1" name="$2"
  [ "$RC" -eq 0 ] || fail "$label: --help must exit 0, got $RC"
  printf '%s\n%s\n' "$OUT" "$ERR" | grep -qi "usage:.*$name" \
    || fail "$label: --help must print a usage line naming $name:
$OUT
$ERR"
}

# ---------------------------------------------------------------------------
# lint-skill.sh
# ---------------------------------------------------------------------------
LINT="$REPO/scripts/lint-skill.sh"

write_skill() {  # $1 path, $2 description
  mkdir -p "$(dirname "$1")"
  {
    printf '%s\n' '---' 'name: fixture-skill' "description: \"$2\"" 'status: candidate' '---'
    printf '\n%s\n\n%s\n' '# Fixture' 'Body text with nothing the boundary lint rejects.'
  } > "$1"
}

CLEAN="$WORK/lint/clean/SKILL.md"
ROLE="$WORK/lint/role/SKILL.md"
MISSING="$WORK/lint/missing/SKILL.md"
write_skill "$CLEAN" "Exercise the check shape with a clean verb-phrase description."
write_skill "$ROLE" "Acts as the reviewer for fixture skills."

run bash "$LINT" "$CLEAN"
assert_shape "lint-skill pass" lint-skill pass 0
printf '%s\n' "$OUT" | grep -q "^reason: .*$CLEAN.*clean" \
  || fail "lint-skill pass: expected a reason: line naming the clean file:
$OUT"
ok

run bash "$LINT" "$CLEAN" "$ROLE"
assert_shape "lint-skill fail" lint-skill fail 1
printf '%s\n' "$OUT" | grep -q "^reason: .*$ROLE.*Role-shape" \
  || fail "lint-skill fail: expected a reason: line naming the file and category:
$OUT"
printf '%s\n' "$OUT" | grep -q "^reason: .*$CLEAN.*clean" \
  || fail "lint-skill fail: the clean file still gets its reason: line:
$OUT"
ok

run bash "$LINT" "$MISSING"
assert_shape "lint-skill missing file" lint-skill unverifiable 0
printf '%s\n' "$OUT" | grep -q "^reason: .*$MISSING.*not found" \
  || fail "lint-skill missing file: expected a reason: line naming the missing file:
$OUT"
ok

run bash "$LINT" "$CLEAN" "$MISSING"
assert_shape "lint-skill clean + missing" lint-skill unverifiable 0
ok

run bash "$LINT" "$ROLE" "$MISSING"
assert_shape "lint-skill fail + missing" lint-skill fail 1
ok

run bash "$LINT"
assert_usage_error "lint-skill no arguments" lint-skill.sh
ok

run bash "$LINT" --bogus "$CLEAN"
assert_usage_error "lint-skill unknown flag" lint-skill.sh
ok

run bash "$LINT" --help
assert_help "lint-skill --help" lint-skill.sh
ok


# ---------------------------------------------------------------------------
# gen-skill.sh — runs from a temp copy: it reads and writes relative to its
# own location, so a minimal manifest tree stands in for the repo.
# ---------------------------------------------------------------------------
make_gen_tree() {  # $1 root
  mkdir -p "$1/scripts" "$1/.writ/docs" "$1/commands" "$1/agents"
  cp "$REPO/scripts/gen-skill.sh" "$1/scripts/gen-skill.sh"
  printf '# Contract\n' > "$1/.writ/docs/contract.md"
  printf '# Hello\n' > "$1/commands/hello.md"
  printf '# Helper\n' > "$1/agents/helper.md"
  cat > "$1/.writ/manifest.yaml" <<'YAML'
version: 1
metadata:
  name: fixture
  version: 0.0.1
  description: "Fixture catalog."
  runtime_contract: ".writ/docs/contract.md"

categories:
  - id: core
    label: "Core"

commands:
  - name: hello
    file: commands/hello.md
    category: core
    purpose: "Say hello."

agents:
  - name: helper
    file: agents/helper.md
    purpose: "Help."
    model_tier: floor

skills: []
YAML
  printf '%s\n' '---' 'name: fixture' '---' > "$1/SKILL.md"
}

GEN_ROOT="$WORK/gen"
make_gen_tree "$GEN_ROOT"
GEN="$GEN_ROOT/scripts/gen-skill.sh"

run bash "$GEN"
assert_shape "gen-skill write" gen-skill pass 0
grep -qF '| `/hello` | `commands/hello.md` | Say hello. |' "$GEN_ROOT/SKILL.md" \
  || fail "gen-skill write: SKILL.md must carry the generated command row"
ok

run bash "$GEN" --check
assert_shape "gen-skill --check clean" gen-skill pass 0
ok

run bash "$GEN" --dry-run
assert_shape "gen-skill --dry-run" gen-skill pass 0
printf '%s\n' "$OUT" | grep -qF '| `/hello` | `commands/hello.md` | Say hello. |' \
  || fail "gen-skill --dry-run: the generated catalog must print between verdict and summary:
$OUT"
ok

printf 'hand edit\n' >> "$GEN_ROOT/SKILL.md"
run bash "$GEN" --check
assert_shape "gen-skill --check drift" gen-skill fail 1
printf '%s\n' "$OUT" | grep -q '^reason: SKILL.md' \
  || fail "gen-skill --check drift: expected a reason: line naming SKILL.md:
$OUT"
ok

sed 's/^  description: "Fixture catalog."$//' "$GEN_ROOT/.writ/manifest.yaml" > "$WORK/bad-manifest.yaml"
cp "$GEN_ROOT/.writ/manifest.yaml" "$WORK/good-manifest.yaml"
cp "$WORK/bad-manifest.yaml" "$GEN_ROOT/.writ/manifest.yaml"
cp "$GEN_ROOT/SKILL.md" "$WORK/skill-before.md"
run bash "$GEN"
assert_shape "gen-skill write, invalid manifest" gen-skill fail 1
printf '%s\n' "$OUT" | grep -q "^reason: .*description" \
  || fail "gen-skill invalid manifest: expected a reason: line naming the missing field:
$OUT"
cmp -s "$GEN_ROOT/SKILL.md" "$WORK/skill-before.md" \
  || fail "gen-skill invalid manifest: write mode must leave SKILL.md untouched"
run bash "$GEN" --check
assert_shape "gen-skill --check, invalid manifest" gen-skill fail 1
ok
cp "$WORK/good-manifest.yaml" "$GEN_ROOT/.writ/manifest.yaml"

rm "$GEN_ROOT/SKILL.md"
run bash "$GEN" --check
assert_shape "gen-skill --check, missing SKILL.md" gen-skill unverifiable 0
run bash "$GEN"
assert_shape "gen-skill write, missing SKILL.md" gen-skill unverifiable 0
ok

rm "$GEN_ROOT/.writ/manifest.yaml"
run bash "$GEN" --check
assert_shape "gen-skill --check, missing manifest" gen-skill unverifiable 0
ok

run bash "$GEN" --bogus
assert_usage_error "gen-skill unknown flag" gen-skill.sh
ok

run bash "$GEN" --help
assert_help "gen-skill --help" gen-skill.sh
ok


# ---------------------------------------------------------------------------
# check-agent-parity.sh — runs from a temp copy: it reads the agents folders
# beside its own scripts/ folder. [AC-5.2]
# ---------------------------------------------------------------------------
PAR_ROOT="$WORK/parity"
mkdir -p "$PAR_ROOT/scripts" "$PAR_ROOT/agents" "$PAR_ROOT/claude-code/agents" "$PAR_ROOT/codex/agents"
cp "$REPO/scripts/check-agent-parity.sh" "$PAR_ROOT/scripts/check-agent-parity.sh"
PARITY="$PAR_ROOT/scripts/check-agent-parity.sh"
printf '# Coding\n' > "$PAR_ROOT/agents/coding-agent.md"
printf '# Coder\n' > "$PAR_ROOT/claude-code/agents/writ-coder.md"
printf 'name = "coding-agent"\n' > "$PAR_ROOT/codex/agents/coding-agent.toml"
printf '# Visual QA\n' > "$PAR_ROOT/agents/visual-qa-agent.md"
printf '# Visual QA\n' > "$PAR_ROOT/claude-code/agents/writ-visual-qa.md"
printf 'name = "visual-qa-agent"\n' > "$PAR_ROOT/codex/agents/visual-qa-agent.toml"

# No generators beside the copied script: presence only, and the summary says
# the content check was skipped. [AC-3.3]
run bash "$PARITY"
assert_shape "parity aligned" check-agent-parity pass 0
printf '%s\n' "$OUT" | sed -n '$p' | grep -Fq '; content not checked: gen-claude-agents.py gen-codex-agent-tomls.py)' \
  || fail "parity aligned, no generators: summary must note the skipped content check:
$OUT"
ok

# visual-qa-agent is checked like every other agent: a missing writ-visual-qa.md is drift. [AC-3.1]
rm "$PAR_ROOT/claude-code/agents/writ-visual-qa.md"
run bash "$PARITY"
assert_shape "parity, writ-visual-qa.md missing" check-agent-parity fail 1
printf '%s\n' "$OUT" | grep -Fxq 'reason: agents/visual-qa-agent.md has no counterpart in claude-code/agents/' \
  || fail "parity, writ-visual-qa.md missing: expected a claude-code/ reason for visual-qa-agent:
$OUT"
printf '# Visual QA\n' > "$PAR_ROOT/claude-code/agents/writ-visual-qa.md"
ok

rm "$PAR_ROOT/codex/agents/coding-agent.toml" "$PAR_ROOT/claude-code/agents/writ-coder.md"
run bash "$PARITY"
assert_shape "parity drift" check-agent-parity fail 1
[ "$(printf '%s\n' "$OUT" | grep -c '^reason: agents/coding-agent.md has no counterpart')" -eq 2 ] \
  || fail "parity drift: expected one reason: line per missing counterpart:
$OUT"
ok

mv "$PAR_ROOT/agents" "$PAR_ROOT/agents.off"
run bash "$PARITY"
assert_shape "parity without agents/" check-agent-parity unverifiable 0
mv "$PAR_ROOT/agents.off" "$PAR_ROOT/agents"
ok

run bash "$PARITY" --bogus
assert_usage_error "parity unknown flag" check-agent-parity.sh
run bash "$PARITY" extra
assert_usage_error "parity positional argument" check-agent-parity.sh
ok

run bash "$PARITY" --help
assert_help "parity --help" check-agent-parity.sh
ok

# Content drift: both generators beside the script, real canonical agents, and
# outputs generated in the temp tree. Each generator resolves agents/ and its
# out-dir from its own location, so they must sit in <tmp>/scripts/. [AC-3.2]
CON_ROOT="$WORK/parity-content"
mkdir -p "$CON_ROOT/scripts"
cp "$REPO/scripts/check-agent-parity.sh" "$REPO/scripts/gen-claude-agents.py" \
  "$REPO/scripts/gen-codex-agent-tomls.py" "$CON_ROOT/scripts/"
cp -R "$REPO/agents" "$CON_ROOT/agents"
python3 "$CON_ROOT/scripts/gen-claude-agents.py" >/dev/null
python3 "$CON_ROOT/scripts/gen-codex-agent-tomls.py" >/dev/null
CPARITY="$CON_ROOT/scripts/check-agent-parity.sh"

run bash "$CPARITY"
assert_shape "parity content aligned" check-agent-parity pass 0
case "$OUT" in
  *"content not checked"*) fail "parity content aligned: both generators are present:
$OUT" ;;
esac
ok

cp "$CON_ROOT/agents/coding-agent.md" "$WORK/coding-agent.md.orig"
printf '\nOne canonical line, not regenerated.\n' >> "$CON_ROOT/agents/coding-agent.md"
run bash "$CPARITY"
assert_shape "parity content stale" check-agent-parity fail 1
printf '%s\n' "$OUT" | grep -Fxq 'reason: gen-claude-agents.py: stale coding-agent' \
  || fail "parity content stale: expected 'reason: gen-claude-agents.py: stale coding-agent':
$OUT"
if printf '%s\n' "$OUT" | grep -q '^reason: agents/'; then
  fail "parity content stale: presence is aligned, so no presence reason is expected:
$OUT"
fi
cp "$WORK/coding-agent.md.orig" "$CON_ROOT/agents/coding-agent.md"
ok

# A generator whose --check crashes (rc >= 2) is drift, never a silent pass. [AC-3.3]
cp "$CON_ROOT/scripts/gen-codex-agent-tomls.py" "$WORK/gen-codex.orig"
printf 'import sys\nsys.exit(2)\n' > "$CON_ROOT/scripts/gen-codex-agent-tomls.py"
run bash "$CPARITY"
assert_shape "parity generator crash" check-agent-parity fail 1
printf '%s\n' "$OUT" | grep -Fxq 'reason: gen-codex-agent-tomls.py --check exited 2' \
  || fail "parity generator crash: expected 'reason: gen-codex-agent-tomls.py --check exited 2':
$OUT"
cp "$WORK/gen-codex.orig" "$CON_ROOT/scripts/gen-codex-agent-tomls.py"
ok

# One generator absent: the other still runs; the summary names the skipped one
# and the verdict comes from the remaining reasons only. [AC-3.3]
rm "$CON_ROOT/scripts/gen-claude-agents.py"
run bash "$CPARITY"
assert_shape "parity, claude generator absent" check-agent-parity pass 0
printf '%s\n' "$OUT" | sed -n '$p' | grep -Fq '; content not checked: gen-claude-agents.py)' \
  || fail "parity, claude generator absent: summary must name only gen-claude-agents.py:
$OUT"
ok

# Parity drift warns and never blocks (/refresh-command), so the live repo is
# held to the shape, not to zero drift: pass exits 0, fail exits 1.
run bash "$REPO/scripts/check-agent-parity.sh"
case "$(printf '%s\n' "$OUT" | sed -n '1p')" in
  pass) assert_shape "parity on this repo" check-agent-parity pass 0 ;;
  fail) assert_shape "parity on this repo" check-agent-parity fail 1 ;;
  *) fail "parity on this repo: line 1 is not pass or fail:
$OUT" ;;
esac
ok

# gen-skill write mode on a read-only SKILL.md still prints the check shape.
RO="$WORK/ro"
mkdir -p "$RO/scripts" "$RO/.writ"
cp "$REPO/scripts/gen-skill.sh" "$RO/scripts/"
cp "$REPO/.writ/manifest.yaml" "$RO/.writ/"
cp "$REPO/SKILL.md" "$RO/SKILL.md"
chmod 444 "$RO/SKILL.md"
run bash "$RO/scripts/gen-skill.sh"
chmod 644 "$RO/SKILL.md"
assert_shape "gen-skill write, read-only SKILL.md" gen-skill fail 1
ok

printf 'OK %d shell check-shape assertions\n' "$pass_count"
