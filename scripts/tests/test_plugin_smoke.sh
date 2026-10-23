#!/usr/bin/env bash
# Story 5 of 2026-10-22-plugin-distribution: one smoke test across the five
# install targets (spec.md Rule 9; technical-spec.md -> Smoke Test).
#
#   cursor, claude, codex  `scripts/install.sh --platform <p> --no-commit` in a
#                          fresh `git init` temp project, run from a committed
#                          temp copy of this working tree
#   claude-plugin          a temp copy of plugins/writ/, under a temp
#                          marketplace root holding copies of .claude-plugin/
#                          and README.md
#   cursor-plugin          a temp copy of cursor/plugin/
#
# Checks (AC-5.2, AC-5.3):
#   install         install.sh exits 0 from the temp copy (install.sh targets)
#   copy            printed only as `fail`, when the plugin directory is
#                   missing from the source copy (plugin targets); the
#                   target's other checks are skipped and its summary is fail
#   commands        every `file:` under `commands:` in .writ/manifest.yaml is
#                   at the platform's command path, and a plugin manifest that
#                   lists commands lists it
#   script-run      `python3 <root>/scripts/spec-status.py --help` exits 0;
#                   `unverifiable (no cursor session)` for a Cursor layout
#                   with no plugin-root scripts/
#   instructions    the instructions file is where the platform loads it, or
#                   the Writ block imports it
#   scaffold        `scaffold-writ.py scaffold --project <empty temp dir>`
#                   creates the .writ/ tree and the .gitignore entries
#   scaffold-check  `scripts/scaffold-writ.py scaffold --check` passes in the
#                   installed project (install.sh targets)
#   validate, validate-marketplace
#                   `claude plugin validate` on the plugin copy and on the
#                   marketplace copy (claude-plugin), only when
#                   `command -v claude` succeeds, else
#                   `unverifiable (no claude CLI)`; exit 1 or 2 is `fail`
#
# Output: one stdout line per target and check, then one per target:
#   <target> <check> pass | fail | unverifiable (<reason>)
#   <target> pass | fail | unverifiable
# A target reads pass only when every check passed, fail when any check
# failed, else unverifiable. Failure details go to stderr (every check's
# detail with --verbose). Exit 1 when any check fails, 2 on a usage error,
# else 0.
#
# Usage: bash scripts/tests/test_plugin_smoke.sh [--record] [--targets a,b]
#          [--no-self-test] [--verbose]
#   (default)       the self-tests below, then all five targets. The self-tests
#                   assert AC-5.1: the line format, the summary rule, and exit 1
#                   exactly when a line reads `fail`
#   --record        also write scripts/tests/fixtures/plugin-smoke-results.txt:
#                   the run date, `claude --version`, the five summary lines,
#                   and `cursor-uat pending`, or `cursor-uat run` when the
#                   existing fixture already reads run (all five targets only)
#   --targets       run only the named targets, comma-separated
#   --no-self-test  skip the self-tests
#
# Temp dirs only, removed by a trap. HOME points at a temp dir for every git,
# install.sh, and claude call, so nothing is written under ~/.claude or
# ~/.cursor. No network: install.sh runs from the temp copy, never cloning.
# Never runs against the Writ repository itself. Does `git init`: run outside
# any sandbox.
set -euo pipefail
# No pathname expansion: `.writ-lanes-*/` and the target names are data.
set -f

REPO="$(cd "$(dirname "$0")/../.." && pwd -P)"
SELF="$REPO/scripts/tests/$(basename "$0")"
FIXTURE="$REPO/scripts/tests/fixtures/plugin-smoke-results.txt"
ALL_TARGETS="cursor claude codex claude-plugin cursor-plugin"
# spec.md Rule 7: the eleven paths and two .gitignore entries scaffold-writ.py makes.
WRIT_TREE=".writ/specs .writ/product .writ/research .writ/decision-records .writ/docs .writ/knowledge
.writ/state .writ/issues/bugs .writ/issues/features .writ/issues/improvements .writ/issues/goals"
IGNORE_ENTRIES='.writ/state/ .writ-lanes-*/'

usage() {
  printf 'usage: bash scripts/tests/test_plugin_smoke.sh [--record] [--targets a,b] [--no-self-test] [--verbose]\n' >&2
  printf 'targets: %s\n' "$ALL_TARGETS" >&2
  exit 2
}

RECORD=false
SELF_TEST=true
VERBOSE=false
TARGETS="$ALL_TARGETS"
SUBSET=false
while [ $# -gt 0 ]; do
  case "$1" in
    --record) RECORD=true ;;
    --no-self-test) SELF_TEST=false ;;
    --verbose) VERBOSE=true ;;
    --targets)
      [ $# -ge 2 ] || usage
      TARGETS=$(printf '%s' "$2" | tr ',' ' ')
      SUBSET=true
      shift
      ;;
    *) usage ;;
  esac
  shift
done
[ -n "$(printf '%s' "$TARGETS" | tr -d ' ')" ] || usage
for t in $TARGETS; do
  case " $ALL_TARGETS " in *" $t "*) ;; *) usage ;; esac
  [ "$(printf '%s\n' $TARGETS | grep -cxF -- "$t")" = 1 ] || usage
done
if $RECORD && $SUBSET; then
  printf 'test_plugin_smoke: --record runs all five targets; drop --targets\n' >&2
  usage
fi

WORK=$(mktemp -d "${TMPDIR:-/tmp}/writ-plugin-smoke.XXXXXX")
trap 'rm -rf "$WORK"' EXIT
trap 'exit 130' INT TERM
WORK=$(cd "$WORK" && pwd -P)
case "$WORK/" in
  "$REPO/"*) printf 'FAIL: temp dir %s is inside the repository\n' "$WORK" >&2; exit 1 ;;
esac
SMOKE_HOME="$WORK/home"
mkdir -p "$SMOKE_HOME"
SRC="$WORK/src"
RESULTS="$WORK/results"
: > "$RESULTS"
DETAIL=""

# Here-strings, not pipes, feed `grep -q`: under pipefail an early `grep -q`
# exit can SIGPIPE the writer and fail a check that matched.

# report TARGET CHECK VERDICT: one stdout line, kept for the summary.
report() {
  printf '%s %s %s\n' "$1" "$2" "$3" | tee -a "$RESULTS"
  if [ "$3" = fail ] || $VERBOSE; then
    [ -z "$DETAIL" ] || printf '  %s %s: %s\n' "$1" "$2" "$DETAIL" >&2
  fi
  DETAIL=""
}

# check TARGET CHECK FUNCTION [ARGS...]: pass when FUNCTION returns 0.
check() {
  local target="$1" name="$2"
  shift 2
  DETAIL=""
  if "$@"; then report "$target" "$name" pass; else report "$target" "$name" fail; fi
}

# summary_for TARGET FILE: the summary rule on TARGET's check lines in FILE.
summary_for() {
  awk -v t="$1" '
    $1 == t && NF >= 3 { n++; if ($3 == "fail") f = 1; else if ($3 == "unverifiable") u = 1 }
    END { print (n == 0 || f) ? "fail" : (u ? "unverifiable" : "pass") }
  ' "$2"
}

# write_record OUT RESULTS VERSION: the fixture test_readme_install_order reads.
write_record() {
  local out="$1" results="$2" t uat=pending
  # The Cursor UAT result is set by hand; a re-record keeps a `run` line.
  if [ -f "$out" ] && grep -qxF 'cursor-uat run' "$out"; then
    uat=run
  fi
  {
    printf '# Written by `bash scripts/tests/test_plugin_smoke.sh --record`; re-record after a plugin layout or platform version change.\n'
    printf '# run date: %s\n' "$(date +%Y-%m-%d)"
    printf '# claude --version: %s\n' "$3"
    printf '# cursor-uat reads pending until the Cursor local plugin UAT protocol (technical-spec.md -> UAT Protocols) has run; then edit it to run.\n'
    for t in $ALL_TARGETS; do
      printf '%s %s\n' "$t" "$(summary_for "$t" "$results")"
    done
    printf 'cursor-uat %s\n' "$uat"
  } > "$WORK/record.txt"
  mkdir -p "$(dirname "$out")"
  mv -f "$WORK/record.txt" "$out"
}

claude_version() {
  local out
  if ! command -v claude >/dev/null 2>&1; then
    printf 'no claude CLI'
  elif out=$(HOME="$SMOKE_HOME" claude --version 2>&1) && [ -n "$out" ]; then
    printf '%s' "${out%%$'\n'*}"
  else
    printf 'claude --version failed'
  fi
}

# ---------------------------------------------------------------------------
# Source copy
# ---------------------------------------------------------------------------

commit_src() {
  HOME="$SMOKE_HOME" git -C "$1" -c user.name=t -c user.email=t@example.invalid add -A
  HOME="$SMOKE_HOME" git -C "$1" -c user.name=t -c user.email=t@example.invalid commit -q -m "$2"
}

# make_src: copy this working tree to $SRC, as test_install_update_claude_parity.sh
# does, with .writ/docs/ (install.sh ships it) and .writ/manifest.yaml (the
# command list). Committed when an install.sh target runs.
make_src() {
  local t
  mkdir -p "$SRC"
  (cd "$REPO" && tar --exclude=.git --exclude=.cursor --exclude=.claude --exclude=.codex --exclude=.writ \
    --exclude='.writ-lanes-*' --exclude=__pycache__ --exclude=.venv --exclude=.pytest_cache -cf - .) \
    | (cd "$SRC" && tar -xf -)
  mkdir -p "$SRC/.writ/docs"
  find "$REPO/.writ/docs" -maxdepth 1 -type f -name '*.md' -exec cp {} "$SRC/.writ/docs/" \;
  cp "$REPO/.writ/manifest.yaml" "$SRC/.writ/manifest.yaml"
  # install.sh clones from GitHub unless its own root has these.
  [ -f "$SRC/SKILL.md" ] && [ -d "$SRC/commands" ] && [ -f "$SRC/scripts/install.sh" ] \
    || { printf 'FAIL: source copy has no SKILL.md, commands/, or scripts/install.sh\n' >&2; exit 1; }
  CMD_LIST="$WORK/manifest-commands"
  awk '
    /^commands:[[:space:]]*$/ { on = 1; next }
    on && /^[^[:space:]#-]/ { exit }
    on && /^[[:space:]]*(-[[:space:]]+)?file:[[:space:]]*/ {
      sub(/^[[:space:]]*(-[[:space:]]+)?file:[[:space:]]*/, ""); sub(/[[:space:]]+$/, ""); gsub(/"/, ""); print
    }
  ' "$SRC/.writ/manifest.yaml" > "$CMD_LIST"
  for t in $TARGETS; do
    case "$t" in
      cursor|claude|codex)
        HOME="$SMOKE_HOME" git -C "$SRC" init -q -b main
        commit_src "$SRC" source
        return 0
        ;;
    esac
  done
}

# ---------------------------------------------------------------------------
# Checks. Each returns 0 for pass and sets DETAIL.
# ---------------------------------------------------------------------------

# check_commands DIR [PLUGIN_JSON]: every manifest command file is in DIR; a
# plugin manifest with a `commands` key (it replaces folder discovery) lists
# each one as ./commands/<file>.
check_commands() {
  local dir="$1" plugin_json="${2:-}" f base n=0 missing="" unlisted
  while IFS= read -r f; do
    [ -n "$f" ] || continue
    n=$((n + 1))
    base=${f##*/}
    [ -f "$dir/$base" ] || missing="$missing $base"
  done < "$CMD_LIST"
  [ "$n" -gt 0 ] || { DETAIL="no file: entries under commands: in .writ/manifest.yaml"; return 1; }
  [ -z "$missing" ] || { DETAIL="not in ${dir#"$WORK"/}:$missing"; return 1; }
  if [ -n "$plugin_json" ]; then
    unlisted=$(python3 - "$plugin_json" "$CMD_LIST" <<'PY'
import json, sys
with open(sys.argv[1], encoding="utf-8") as f:
    manifest = json.load(f)
if not manifest.get("name"):
    print("(plugin.json has no name)")
    sys.exit(0)
listed = manifest.get("commands")
if listed is None:
    sys.exit(0)
if isinstance(listed, str):
    listed = [listed]
paths = {(p[2:] if p.startswith("./") else p).rstrip("/") for p in map(str, listed)}
with open(sys.argv[2], encoding="utf-8") as f:
    for line in f:
        base = line.strip().rsplit("/", 1)[-1]
        if base and "commands" not in paths and "commands/" + base not in paths:
            print(base)
PY
) || { DETAIL="cannot read ${plugin_json#"$WORK"/}"; return 1; }
    [ -z "$unlisted" ] || { DETAIL="${plugin_json#"$WORK"/} does not list: $(printf '%s' "$unlisted" | tr '\n' ' ')"; return 1; }
  fi
  DETAIL="$n manifest commands in ${dir#"$WORK"/}"
}

# check_script_run ROOT CWD: python3 ROOT/scripts/spec-status.py --help exits 0 from CWD.
check_script_run() {
  local rc
  [ -f "$1/scripts/spec-status.py" ] || { DETAIL="no ${1#"$WORK"/}/scripts/spec-status.py"; return 1; }
  (cd "$2" && python3 "$1/scripts/spec-status.py" --help >/dev/null 2>&1) && rc=0 || rc=$?
  DETAIL="python3 ${1#"$WORK"/}/scripts/spec-status.py --help exit $rc"
  [ "$rc" = 0 ]
}

# check_scaffold SCRIPT CWD: SCRIPT scaffold --project <empty dir> makes the tree.
check_scaffold() {
  local script="$1" cwd="$2" empty out rc p e
  empty=$(mktemp -d "$WORK/empty.XXXXXX")
  out=$( (cd "$cwd" && python3 "$script" scaffold --project "$empty") 2>&1 ) && rc=0 || rc=$?
  [ "$rc" = 0 ] || { DETAIL="exit $rc: $(printf '%s' "$out" | tail -n 3 | tr '\n' ' ')"; return 1; }
  for p in $WRIT_TREE; do
    [ -d "$empty/$p" ] || { DETAIL="scaffold made no $p"; return 1; }
  done
  for e in $IGNORE_ENTRIES; do
    grep -qxF -- "$e" "$empty/.gitignore" 2>/dev/null || { DETAIL="no .gitignore entry $e"; return 1; }
  done
  DETAIL="${script#"$WORK"/} created the .writ/ tree"
}

# check_scaffold_project_copy SCRIPT CWD: check_scaffold on the project's
# install.sh copy of scaffold-writ.py, saying so in the detail.
check_scaffold_project_copy() {
  local rc=0
  check_scaffold "$@" || rc=1
  DETAIL="$DETAIL; the layout ships no scripts/, so this ran the project's install.sh copy of scripts/scaffold-writ.py"
  return "$rc"
}

# check_scaffold_check PROJ: scripts/scaffold-writ.py scaffold --check passes in PROJ.
check_scaffold_check() {
  local out rc
  out=$( (cd "$1" && python3 scripts/scaffold-writ.py scaffold --check) 2>&1 ) && rc=0 || rc=$?
  DETAIL="exit $rc: $(printf '%s' "$out" | tr '\n' ' ')"
  [ "$rc" = 0 ]
}

# same_file A B: A exists and has B's bytes.
same_file() {
  [ -f "$1" ] || { DETAIL="no ${1#"$WORK"/}"; return 1; }
  cmp -s "$1" "$2" || { DETAIL="${1#"$WORK"/} differs from ${2#"$WORK"/}"; return 1; }
}

# writ_block FILE OUT: OUT gets the lines between the one writ:start line and
# the one writ:end line of FILE.
writ_block() {
  local starts ends
  [ -f "$1" ] || { DETAIL="no ${1#"$WORK"/}"; return 1; }
  starts=$(grep -cxF '<!-- writ:start -->' "$1" || true)
  ends=$(grep -cxF '<!-- writ:end -->' "$1" || true)
  [ "$starts" = 1 ] && [ "$ends" = 1 ] || { DETAIL="${1#"$WORK"/}: $starts start and $ends end markers"; return 1; }
  awk '$0 == "<!-- writ:start -->" { on = 1; next } $0 == "<!-- writ:end -->" { exit } on' "$1" > "$2"
  [ -s "$2" ] || { DETAIL="${1#"$WORK"/}: empty or reversed Writ block"; return 1; }
}

# has_carrier FILE FRONTMATTER_LINE: FILE's frontmatter has the line and its
# body the Prime Directive heading.
has_carrier() {
  [ -f "$1" ] || { DETAIL="no ${1#"$WORK"/}"; return 1; }
  local fm
  fm=$(awk 'NR == 1 && $0 != "---" { exit } NR > 1 && $0 == "---" { exit } NR > 1' "$1")
  grep -qxF -- "$2" <<< "$fm" || { DETAIL="${1#"$WORK"/} frontmatter has no '$2'"; return 1; }
  grep -qx '## Prime Directive' "$1" || { DETAIL="${1#"$WORK"/} has no Prime Directive"; return 1; }
}

instructions_cursor() {
  same_file "$1/.cursor/system-instructions.md" "$SRC/system-instructions.md" || return 1
  same_file "$1/.cursor/rules/writ.mdc" "$SRC/cursor/writ.mdc" || return 1
  DETAIL=".cursor/system-instructions.md and .cursor/rules/writ.mdc match the source"
}

instructions_claude() {
  same_file "$1/.claude/system-instructions.md" "$SRC/system-instructions.md" || return 1
  writ_block "$1/CLAUDE.md" "$WORK/claude-block" || return 1
  grep -qxF '@.claude/system-instructions.md' "$WORK/claude-block" \
    || { DETAIL="the CLAUDE.md Writ block does not import @.claude/system-instructions.md"; return 1; }
  DETAIL="the CLAUDE.md Writ block imports .claude/system-instructions.md"
}

instructions_codex() {
  writ_block "$1/AGENTS.md" "$WORK/codex-block" || return 1
  cmp -s "$WORK/codex-block" "$SRC/codex/AGENTS.md.template" \
    || { DETAIL="the AGENTS.md Writ block differs from codex/AGENTS.md.template"; return 1; }
  DETAIL="the AGENTS.md Writ block is codex/AGENTS.md.template"
}

instructions_claude_plugin() {
  has_carrier "$1/output-styles/writ.md" "force-for-plugin: true" || return 1
  DETAIL="output-styles/writ.md is forced and carries the Prime Directive"
}

instructions_cursor_plugin() {
  has_carrier "$1/rules/writ.mdc" "alwaysApply: true" || return 1
  DETAIL="rules/writ.mdc always applies and carries the Prime Directive"
}

# check_validate PATH: claude plugin validate PATH exits 0 (with or without warnings).
check_validate() {
  local out rc
  out=$(HOME="$SMOKE_HOME" claude plugin validate "$1" 2>&1 </dev/null) && rc=0 || rc=$?
  DETAIL="claude plugin validate ${1#"$WORK"/} exit $rc: $(printf '%s' "$out" | tr '\n' ' ')"
  [ "$rc" = 0 ]
}

# ---------------------------------------------------------------------------
# Targets
# ---------------------------------------------------------------------------

# install_target PLATFORM: install.sh from the temp copy into a fresh git project.
install_target() {
  local p="$1" proj="$WORK/proj-$1" out rc
  mkdir -p "$proj"
  case "$proj/" in "$REPO/"*) printf 'FAIL: %s is inside the repository\n' "$proj" >&2; exit 1 ;; esac
  out=$( { HOME="$SMOKE_HOME" git -C "$proj" init -q -b main \
           && (cd "$proj" && HOME="$SMOKE_HOME" bash "$SRC/scripts/install.sh" --platform "$p" --no-commit </dev/null); } 2>&1 ) \
    && rc=0 || rc=$?
  if [ "$rc" = 0 ] && grep -qxF -- "📦 Using local writ: $SRC" <<< "$out"; then
    DETAIL="install.sh --platform $p --no-commit exit 0"
    report "$p" install pass
  else
    DETAIL="install.sh --platform $p exit $rc: $(printf '%s' "$out" | tail -n 5 | tr '\n' ' ')"
    report "$p" install fail
  fi
  check "$p" commands check_commands "$proj/.$p/commands"
  check "$p" script-run check_script_run "$proj" "$proj"
  check "$p" instructions "instructions_$p" "$proj"
  check "$p" scaffold check_scaffold "$proj/scripts/scaffold-writ.py" "$proj"
  check "$p" scaffold-check check_scaffold_check "$proj"
}

claude_plugin_target() {
  local market="$WORK/claude-marketplace" plugin session t=claude-plugin
  plugin="$market/plugins/writ"
  session=$(mktemp -d "$WORK/session.XXXXXX")
  mkdir -p "$market/plugins"
  if [ ! -d "$SRC/plugins/writ" ] || [ ! -d "$SRC/.claude-plugin" ]; then
    DETAIL="the source copy has no plugins/writ/ or .claude-plugin/"
    report "$t" copy fail
    return 0
  fi
  if ! cp -R "$SRC/plugins/writ" "$plugin" || ! cp -R "$SRC/.claude-plugin" "$market/.claude-plugin"; then
    DETAIL="cannot copy plugins/writ/ or .claude-plugin/"
    report "$t" copy fail
    return 0
  fi
  if [ -f "$SRC/README.md" ]; then
    cp "$SRC/README.md" "$market/README.md"
  fi
  check "$t" commands check_commands "$plugin/commands" "$plugin/.claude-plugin/plugin.json"
  check "$t" script-run check_script_run "$plugin" "$session"
  check "$t" instructions instructions_claude_plugin "$plugin"
  check "$t" scaffold check_scaffold "$plugin/scripts/scaffold-writ.py" "$session"
  if command -v claude >/dev/null 2>&1; then
    check "$t" validate check_validate "$plugin"
    check "$t" validate-marketplace check_validate "$market"
  else
    report "$t" validate "unverifiable (no claude CLI)"
    report "$t" validate-marketplace "unverifiable (no claude CLI)"
  fi
}

cursor_plugin_target() {
  local layout="$WORK/cursor-plugin/writ" session scaffold t=cursor-plugin
  session=$(mktemp -d "$WORK/session.XXXXXX")
  mkdir -p "$WORK/cursor-plugin"
  if [ ! -d "$SRC/cursor/plugin" ]; then
    DETAIL="the source copy has no cursor/plugin/"
    report "$t" copy fail
    return 0
  fi
  if ! cp -R "$SRC/cursor/plugin" "$layout"; then
    DETAIL="cannot copy cursor/plugin/"
    report "$t" copy fail
    return 0
  fi
  check "$t" commands check_commands "$layout/commands" "$layout/.cursor-plugin/plugin.json"
  if [ -d "$layout/scripts" ]; then
    check "$t" script-run check_script_run "$layout" "$session"
  else
    # AC-3.3 second branch: the commands call python3 scripts/<name>.py in
    # the project, and no checked form names the plugin's folder.
    DETAIL="the layout has no plugin-root scripts/"
    report "$t" script-run "unverifiable (no cursor session)"
  fi
  check "$t" instructions instructions_cursor_plugin "$layout"
  if [ -f "$layout/scripts/scaffold-writ.py" ]; then
    check "$t" scaffold check_scaffold "$layout/scripts/scaffold-writ.py" "$session"
  else
    # The project's scripts/ copy that install.sh makes (adapters/cursor.md -> Plugin).
    mkdir -p "$session/scripts"
    cp "$SRC/scripts/scaffold-writ.py" "$session/scripts/scaffold-writ.py"
    check "$t" scaffold check_scaffold_project_copy "$session/scripts/scaffold-writ.py" "$session"
  fi
}

run_target() {
  case "$1" in
    cursor|claude|codex) install_target "$1" ;;
    claude-plugin) claude_plugin_target ;;
    cursor-plugin) cursor_plugin_target ;;
  esac
}
# ---------------------------------------------------------------------------
# Self-tests (default run; skipped with --no-self-test). They re-run this
# script on the two plugin targets with a stub `claude` first on PATH (exit
# 0, 1, 2) and with a PATH that has no `claude`, and assert the line format,
# the summary rule, the exit code, and the `unverifiable` labels. The real
# `claude` is never called here.
# ---------------------------------------------------------------------------

st_fail() {
  printf 'FAIL: self-test: %s\n' "$1" >&2
  exit 1
}

CHECK_LINE='^(cursor|claude|codex|claude-plugin|cursor-plugin) [a-z][a-z-]* (pass|fail|unverifiable \([^()]+\))$'
SUMMARY_LINE='^(cursor|claude|codex|claude-plugin|cursor-plugin) (pass|fail|unverifiable)$'

# PATH entries with no executable `claude`, joined with ':'.
path_without_claude() {
  local out="" dir
  local IFS=:
  for dir in $PATH; do
    [ -n "$dir" ] || continue
    [ -x "$dir/claude" ] && continue
    out="${out:+$out:}$dir"
  done
  printf '%s' "$out"
}

# make_stub DIR EXIT LOG: DIR/claude logs its arguments to LOG and exits EXIT.
make_stub() {
  mkdir -p "$1"
  cat > "$1/claude" <<STUB
#!/bin/sh
printf '%s\n' "\$*" >> '$3'
exit $2
STUB
  chmod +x "$1/claude"
}

# inner PATH [ARGS...]: run $ST_SCRIPT (this script unless set) on the plugin
# targets; sets ST_OUT, ST_ERR, ST_RC.
ST_SCRIPT=""
inner() {
  local path="$1"
  shift
  ST_ERR="$ST_DIR/stderr"
  ST_OUT=$(PATH="$path" "$BASH" "${ST_SCRIPT:-$SELF}" --no-self-test --targets claude-plugin,cursor-plugin "$@" \
    2>"$ST_ERR") && ST_RC=0 || ST_RC=$?
}

has_out_line() {
  grep -qxF -- "$1" <<< "$ST_OUT"
}

expect_line() {
  has_out_line "$2" || st_fail "$1: no line '$2' in: $ST_OUT $(cat "$ST_ERR")"
}

# expect_shape LABEL: every line has the check or summary form; one summary
# per target, after every check line, equal to the rule on its check lines;
# exit 1 exactly when a check line reads fail.
expect_shape() {
  local label="$1" line seen_summary=false t lines
  [ -n "$ST_OUT" ] || st_fail "$label: no output: $(cat "$ST_ERR")"
  while IFS= read -r line; do
    if grep -qE "$SUMMARY_LINE" <<< "$line"; then
      seen_summary=true
    elif grep -qE "$CHECK_LINE" <<< "$line"; then
      $seen_summary && st_fail "$label: check line after a summary line: $line"
    else
      st_fail "$label: line has neither form: '$line'"
    fi
  done <<< "$ST_OUT"
  lines="$ST_DIR/lines"
  grep -E "$CHECK_LINE" <<< "$ST_OUT" > "$lines" || true
  for t in claude-plugin cursor-plugin; do
    grep -q "^$t " "$lines" || st_fail "$label: no check line for $t: $ST_OUT"
    [ "$(grep -cE "^$t (pass|fail|unverifiable)$" <<< "$ST_OUT")" = 1 ] \
      || st_fail "$label: not one summary line for $t: $ST_OUT"
    expect_line "$label" "$t $(summary_for "$t" "$lines")"
  done
  if grep -qE ' fail$' "$lines"; then
    [ "$ST_RC" = 1 ] || st_fail "$label: a check failed but the exit code is $ST_RC"
  else
    [ "$ST_RC" = 0 ] || st_fail "$label: no check failed but the exit code is $ST_RC: $(cat "$ST_ERR")"
  fi
}

# The checks that run whatever `claude` does (AC-5.3: other checks still run).
expect_other_checks() {
  local label="$1" check
  for check in commands script-run instructions scaffold; do
    expect_line "$label" "claude-plugin $check pass"
  done
  for check in commands instructions scaffold; do
    expect_line "$label" "cursor-plugin $check pass"
  done
  if [ -d "$REPO/cursor/plugin/scripts" ]; then
    expect_line "$label" "cursor-plugin script-run pass"
  else
    expect_line "$label" "cursor-plugin script-run unverifiable (no cursor session)"
    expect_line "$label" "cursor-plugin unverifiable"
  fi
}

self_test() {
  local tools tool p nopath log code rec fake t
  ST_DIR="$WORK/self-test"
  mkdir -p "$ST_DIR"

  # The summary rule on hand-written check lines.
  rec="$ST_DIR/rule"
  printf 'x a pass\nx b pass\n' > "$rec"
  [ "$(summary_for x "$rec")" = pass ] || st_fail "rule: every check passed is not pass"
  printf 'x a pass\nx b unverifiable (no claude CLI)\n' > "$rec"
  [ "$(summary_for x "$rec")" = unverifiable ] || st_fail "rule: pass plus unverifiable is not unverifiable"
  printf 'x a fail\nx b unverifiable (no claude CLI)\nx c pass\n' > "$rec"
  [ "$(summary_for x "$rec")" = fail ] || st_fail "rule: a fail among unverifiable is not fail"
  printf 'y a pass\n' > "$rec"
  [ "$(summary_for x "$rec")" = fail ] || st_fail "rule: a target with no check line is not fail"
  printf '%s\n' 'self-test: summary rule ok' >&2

  # The --record file, written to a temp path.
  printf 'cursor a pass\nclaude a pass\ncodex a fail\nclaude-plugin a unverifiable (no claude CLI)\n' > "$rec"
  write_record "$ST_DIR/fixture.txt" "$rec" "no claude CLI"
  grep -qE '^# run date: 20[0-9]{2}-[0-9]{2}-[0-9]{2}$' "$ST_DIR/fixture.txt" || st_fail "record: no run date line"
  grep -qxF '# claude --version: no claude CLI' "$ST_DIR/fixture.txt" || st_fail "record: no claude --version line"
  [ "$(grep -v '^#' "$ST_DIR/fixture.txt")" = "$(printf 'cursor pass\nclaude pass\ncodex fail\nclaude-plugin unverifiable\ncursor-plugin fail\ncursor-uat pending')" ] \
    || st_fail "record: summary lines are: $(grep -v '^#' "$ST_DIR/fixture.txt")"
  # A fixture that reads `cursor-uat run` keeps it; one that reads pending stays pending.
  printf 'cursor-uat run\n' > "$ST_DIR/fixture.txt"
  write_record "$ST_DIR/fixture.txt" "$rec" "no claude CLI"
  [ "$(grep -c '^cursor-uat ' "$ST_DIR/fixture.txt")" = 1 ] && grep -qxF 'cursor-uat run' "$ST_DIR/fixture.txt" \
    || st_fail "record: an existing cursor-uat run line was not kept: $(grep '^cursor-uat' "$ST_DIR/fixture.txt")"
  write_record "$ST_DIR/fixture.txt" "$rec" "no claude CLI"
  grep -qxF 'cursor-uat run' "$ST_DIR/fixture.txt" || st_fail "record: a second re-record dropped cursor-uat run"
  printf 'cursor-uat pending\n' > "$ST_DIR/fixture.txt"
  write_record "$ST_DIR/fixture.txt" "$rec" "no claude CLI"
  grep -qxF 'cursor-uat pending' "$ST_DIR/fixture.txt" || st_fail "record: cursor-uat pending did not stay pending"
  printf '%s\n' 'self-test: record file ok' >&2

  # Usage errors exit 2 and print nothing on stdout.
  for args in "--bogus" "--targets nope" "--targets" "--targets ," "--record --targets claude-plugin"; do
    # shellcheck disable=SC2086
    ST_OUT=$("$BASH" "$SELF" $args 2>/dev/null) && ST_RC=0 || ST_RC=$?
    [ "$ST_RC" = 2 ] || st_fail "usage '$args': exit $ST_RC, not 2"
    [ -z "$ST_OUT" ] || st_fail "usage '$args': stdout '$ST_OUT'"
  done
  printf '%s\n' 'self-test: usage errors ok' >&2

  # A PATH with no `claude`: python3, git, and tar stay reachable through links.
  tools="$ST_DIR/tools"
  mkdir -p "$tools"
  for tool in python3 git tar; do
    p=$(command -v "$tool") || st_fail "no $tool on PATH"
    ln -s "$p" "$tools/$tool"
  done
  nopath="$tools:$(path_without_claude)"
  if (PATH="$nopath"; command -v claude >/dev/null 2>&1); then
    st_fail "could not build a PATH without claude"
  fi

  # No claude CLI: both validate lines unverifiable, the target unverifiable, exit 0.
  inner "$nopath" --verbose
  expect_shape "no claude"
  expect_line "no claude" "claude-plugin validate unverifiable (no claude CLI)"
  expect_line "no claude" "claude-plugin validate-marketplace unverifiable (no claude CLI)"
  expect_line "no claude" "claude-plugin unverifiable"
  expect_other_checks "no claude"
  [ "$ST_RC" = 0 ] || st_fail "no claude: exit $ST_RC"
  if [ ! -f "$REPO/cursor/plugin/scripts/scaffold-writ.py" ]; then
    grep -qE "^  cursor-plugin scaffold: .*the project's install.sh copy of scripts/scaffold-writ.py$" "$ST_ERR" \
      || st_fail "no claude: --verbose does not say the cursor-plugin scaffold ran the install.sh copy: $(cat "$ST_ERR")"
  fi
  printf '%s\n' 'self-test: no claude CLI ok' >&2

  # A source copy with no plugins/writ/ and no cursor/plugin/: each plugin
  # target prints `copy fail` and its summary instead of aborting, exit 1.
  fake="$ST_DIR/no-plugins"
  mkdir -p "$fake/scripts/tests" "$fake/commands" "$fake/.writ/docs"
  cp "$SELF" "$fake/scripts/tests/$(basename "$SELF")"
  : > "$fake/SKILL.md"
  : > "$fake/scripts/install.sh"
  printf 'commands:\n  - name: writ\n    file: commands/writ.md\n' > "$fake/.writ/manifest.yaml"
  ST_SCRIPT="$fake/scripts/tests/$(basename "$SELF")"
  inner "$nopath"
  ST_SCRIPT=""
  expect_shape "no plugin directories"
  for t in claude-plugin cursor-plugin; do
    [ "$(grep -c "^$t " <<< "$ST_OUT")" = 2 ] || st_fail "no plugin directories: $t lines: $ST_OUT"
    expect_line "no plugin directories" "$t copy fail"
    expect_line "no plugin directories" "$t fail"
  done
  [ "$ST_RC" = 1 ] || st_fail "no plugin directories: exit $ST_RC"
  printf '%s\n' 'self-test: missing plugin directories ok' >&2

  # Stub claude exiting 0: validate runs on temp copies, the target passes.
  log="$ST_DIR/claude-0.log"
  make_stub "$ST_DIR/bin-0" 0 "$log"
  inner "$ST_DIR/bin-0:$nopath"
  expect_shape "claude exit 0"
  expect_line "claude exit 0" "claude-plugin validate pass"
  expect_line "claude exit 0" "claude-plugin validate-marketplace pass"
  expect_line "claude exit 0" "claude-plugin pass"
  expect_other_checks "claude exit 0"
  [ "$ST_RC" = 0 ] || st_fail "claude exit 0: exit $ST_RC"
  [ "$(wc -l < "$log" | tr -d ' ')" = 2 ] || st_fail "claude exit 0: stub calls: $(cat "$log")"
  while read -r a b path; do
    [ "$a $b" = "plugin validate" ] || st_fail "claude exit 0: stub called with '$a $b $path'"
    case "$path" in
      "$REPO"|"$REPO"/*) st_fail "claude exit 0: validate ran on the repository: $path" ;;
    esac
    [ ! -e "$path" ] || st_fail "claude exit 0: temp copy $path was not removed"
  done < "$log"
  grep -qE ' .*/plugins/writ$' "$log" || st_fail "claude exit 0: plugin directory not validated: $(cat "$log")"
  grep -qvE ' .*/plugins/writ$' "$log" || st_fail "claude exit 0: marketplace root not validated: $(cat "$log")"
  printf '%s\n' 'self-test: claude exit 0 ok' >&2

  # Stub claude exiting 1 or 2: both validate lines fail, the target fails, exit 1.
  for code in 1 2; do
    make_stub "$ST_DIR/bin-$code" "$code" "$ST_DIR/claude-$code.log"
    inner "$ST_DIR/bin-$code:$nopath"
    expect_shape "claude exit $code"
    expect_line "claude exit $code" "claude-plugin validate fail"
    expect_line "claude exit $code" "claude-plugin validate-marketplace fail"
    expect_line "claude exit $code" "claude-plugin fail"
    expect_other_checks "claude exit $code"
    [ "$ST_RC" = 1 ] || st_fail "claude exit $code: exit $ST_RC"
    printf 'self-test: claude exit %s ok\n' "$code" >&2
  done
}

# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------

if $SELF_TEST; then
  self_test
fi
make_src
for t in $TARGETS; do
  run_target "$t"
done
failed=false
for t in $TARGETS; do
  verdict=$(summary_for "$t" "$RESULTS")
  printf '%s %s\n' "$t" "$verdict"
  [ "$verdict" != fail ] || failed=true
done
if $RECORD; then
  write_record "$FIXTURE" "$RESULTS" "$(claude_version)"
  printf 'recorded %s\n' "${FIXTURE#"$REPO"/}" >&2
fi
if $failed; then
  exit 1
fi
exit 0
