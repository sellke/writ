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

printf 'OK %d shell check-shape assertions\n' "$pass_count"
