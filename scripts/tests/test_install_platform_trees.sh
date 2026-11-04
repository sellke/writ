#!/usr/bin/env bash
# Story 5 of 2026-10-22-generated-platform-trees: a fresh install carries the
# Capability Map in the file each platform loads every session, so an
# installed agent resolves every capability name without reading adapters/.
#
# AC-5.1: install.sh --platform cursor|claude|codex, run from a committed copy
#         of this tree into a fresh git-init project, puts `## Capability Map`
#         in .cursor/rules/writ.mdc, inside the Writ block of CLAUDE.md, and
#         inside the Writ block of AGENTS.md.
# AC-5.2: the installed Codex Writ block contains no `adapters/`.
# AC-5.3: each installed map has a `canvas-preview` row and a `Plan Mode` row,
#         and the Claude Code `Plan Mode` row names `EnterPlanMode`.
#
# Every assertion reads an installed file; the source copy is checked only for
# the files the install needs, so a source tree without the map fails here.
# The copy's own scripts/install.sh runs, and it resolves the copy as the Writ
# source. Does `git init`: run
# outside any sandbox. Never point it at the Writ repo itself.
set -euo pipefail

REPO="$(cd "$(dirname "$0")/../.." && pwd)"
WORK=$(mktemp -d "${TMPDIR:-/tmp}/writ-platform-trees-install-test.XXXXXX")
trap 'rm -rf "$WORK"' EXIT
# install.sh prints the source path it resolved with pwd; match that form (a
# TMPDIR with a trailing slash would otherwise leave a "//" in $WORK).
WORK=$(cd "$WORK" && pwd)

MAP_HEADING='## Capability Map'
pass_count=0

fail() {
  printf 'FAIL: %s\n' "$1" >&2
  exit 1
}

ok() {
  pass_count=$((pass_count + 1))
  printf 'PASS: %s\n' "$1"
}

commit_src() {
  git -C "$1" -c user.name=t -c user.email=t@example.invalid add -A
  git -C "$1" -c user.name=t -c user.email=t@example.invalid commit -q -m "$2"
}

# Marker split copied from test_install_update_claude_parity.sh. Lines keep
# their endings. A marker line matches with one trailing "\r" stripped, as in
# merge_claude_md and merge_agents_md.
BLOCK_PY='
import sys
def parts(path):
    with open(path, "rb") as f:
        data = f.read()
    lines = [l + b"\n" for l in data.split(b"\n")]
    lines[-1] = lines[-1][:-1]
    if not lines[-1]:
        lines.pop()
    def bare(l):
        l = l[:-1] if l.endswith(b"\n") else l
        return l[:-1] if l.endswith(b"\r") else l
    starts = [i for i, l in enumerate(lines) if bare(l) == b"<!-- writ:start -->"]
    ends = [i for i, l in enumerate(lines) if bare(l) == b"<!-- writ:end -->"]
    if len(starts) != 1 or len(ends) != 1 or starts[0] > ends[0]:
        sys.exit("malformed markers in " + path)
    s, e = starts[0], ends[0]
    return lines[:s], lines[s:s + 1], lines[s + 1:e], lines[e:e + 1], lines[e + 1:]
'

# writ_block FILE OUT: write the lines between the markers of FILE to OUT.
# Every Claude Code and Codex check reads OUT, never the whole file, so map
# text outside the markers cannot make a check pass.
writ_block() {
  python3 -c "$BLOCK_PY"'
_, _, inner, _, _ = parts(sys.argv[1])
with open(sys.argv[2], "wb") as f:
    f.write(b"".join(inner))
' "$1" "$2" || fail "cannot extract the Writ block of $1"
}

# map_row FILE NAME: print the first table row under the map heading whose
# first cell, backticks and surrounding blanks stripped, is NAME. The section
# ends at the next "## " heading.
map_row() {
  awk -v want="$2" -v heading="$MAP_HEADING" '
    $0 == heading { on = 1; next }
    on && /^## / { on = 0 }
    on && /^\|/ {
      split($0, cells, "|")
      cell = cells[2]
      gsub(/`/, "", cell)
      gsub(/^[[:space:]]+|[[:space:]]+$/, "", cell)
      if (cell == want) { print; exit }
    }
  ' "$1"
}

# assert_map LABEL FILE: FILE has exactly one map heading (AC-5.1) and the map
# has a canvas-preview row and a Plan Mode row (AC-5.3).
assert_map() {
  local label="$1" file="$2" n
  n=$(grep -cxF "$MAP_HEADING" "$file" || true)
  [ "$n" = 1 ] || fail "$label: expected one '$MAP_HEADING' heading, found $n"
  ok "$label: $MAP_HEADING present"
  [ -n "$(map_row "$file" canvas-preview)" ] || fail "$label: the map has no canvas-preview row"
  [ -n "$(map_row "$file" 'Plan Mode')" ] || fail "$label: the map has no Plan Mode row"
  ok "$label: the map has canvas-preview and Plan Mode rows"
}

# install_into PROJ PLATFORM: fresh git-init project, installed from the copy.
# --no-commit keeps the install's commit output out of failure messages; the
# files it writes are the same either way.
install_into() {
  local proj="$1" platform="$2" out
  mkdir -p "$proj"
  git -C "$proj" init -q -b main
  out=$(cd "$proj" && bash "$SRC/scripts/install.sh" --platform "$platform" --no-commit 2>&1) \
    || fail "$platform: install exited non-zero: $out"
  printf '%s\n' "$out" | grep -qF "Using local writ: $SRC" \
    || fail "$platform: install did not use the source copy: $out"
}

# Committed source copy of the working tree.
SRC="$WORK/src"
mkdir -p "$SRC"
(cd "$REPO" && tar --exclude=.git --exclude=.cursor --exclude=.claude --exclude=.codex --exclude=.writ \
  --exclude='.writ-lanes-*' --exclude=__pycache__ --exclude=.venv --exclude=.pytest_cache -cf - .) | (cd "$SRC" && tar -xf -)
mkdir -p "$SRC/.writ/docs"
cp "$REPO"/.writ/docs/*.md "$SRC/.writ/docs/"
git -C "$SRC" init -q -b main
commit_src "$SRC" source
for f in scripts/install.sh cursor/writ.mdc claude-code/CLAUDE.md codex/AGENTS.md.template; do
  [ -f "$SRC/$f" ] || fail "fixture: source copy has no $f"
done

# ----- cursor: .cursor/rules/writ.mdc, the whole file (no markers) -----
P_CURSOR="$WORK/cursor"
install_into "$P_CURSOR" cursor
CURSOR_RULES="$P_CURSOR/.cursor/rules/writ.mdc"
[ -f "$CURSOR_RULES" ] || fail "cursor: install wrote no .cursor/rules/writ.mdc"
assert_map "cursor: .cursor/rules/writ.mdc" "$CURSOR_RULES"

# ----- claude: the Writ block of CLAUDE.md -----
P_CLAUDE="$WORK/claude"
install_into "$P_CLAUDE" claude
[ -f "$P_CLAUDE/CLAUDE.md" ] || fail "claude: install wrote no CLAUDE.md"
writ_block "$P_CLAUDE/CLAUDE.md" "$WORK/claude-block"
assert_map "claude: CLAUDE.md Writ block" "$WORK/claude-block"
row=$(map_row "$WORK/claude-block" 'Plan Mode')
printf '%s\n' "$row" | grep -qF 'EnterPlanMode' \
  || fail "claude: the Plan Mode row does not name EnterPlanMode: $row"
ok "claude: the Plan Mode row names EnterPlanMode"

# ----- codex: the Writ block of AGENTS.md -----
P_CODEX="$WORK/codex"
install_into "$P_CODEX" codex
[ -f "$P_CODEX/AGENTS.md" ] || fail "codex: install wrote no AGENTS.md"
writ_block "$P_CODEX/AGENTS.md" "$WORK/codex-block"
assert_map "codex: AGENTS.md Writ block" "$WORK/codex-block"
hits=$(grep -nF 'adapters/' "$WORK/codex-block" || true)
[ -z "$hits" ] || fail "codex: the AGENTS.md Writ block mentions adapters/: $hits"
ok "codex: the AGENTS.md Writ block has no adapters/ mention"

printf '\nAll %d install platform-trees assertions passed.\n' "$pass_count"
