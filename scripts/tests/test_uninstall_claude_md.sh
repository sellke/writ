#!/usr/bin/env bash
# End-to-end uninstall of CLAUDE.md on Claude Code, Story 4 of
# 2026-10-20-claude-code-parity.
#
# AC-4.3: in temp projects installed with `install.sh --platform claude
#         --no-commit`, `uninstall.sh --platform claude --no-commit` leaves a
#         hand-written CLAUDE.md equal to the original plus the one "\n"
#         install's append added, and leaves no CLAUDE.md in a project that
#         started without one. `uninstall.sh --platform claude --dry-run`
#         prints "CLAUDE.md Writ block" and changes no file.
# AC-4.2: malformed markers stop uninstall with exit 13 and leave CLAUDE.md
#         untouched (the Error & Rescue Map row; no new recovery).
#
# Runs the real scripts against temp targets built from a committed temp copy
# of this working tree. Does `git init`: run outside any sandbox. Never point
# it at the Writ repo itself.
set -euo pipefail

REPO="$(cd "$(dirname "$0")/../.." && pwd)"
WORK=$(mktemp -d "${TMPDIR:-/tmp}/writ-uninstall-claude-md-test.XXXXXX")
trap 'rm -rf "$WORK"' EXIT

fail() {
  printf 'FAIL: %s\n' "$1" >&2
  exit 1
}

commit_src() {
  git -C "$1" -c user.name=t -c user.email=t@example.invalid add -A
  git -C "$1" -c user.name=t -c user.email=t@example.invalid commit -q -m "$2"
}

run_install() {
  local proj="$1"
  shift
  (cd "$proj" && bash "$SRC/scripts/install.sh" --platform claude "$@" 2>&1)
}

run_uninstall() {
  local proj="$1"
  shift
  (cd "$proj" && bash "$SRC/scripts/uninstall.sh" --platform claude "$@" 2>&1)
}

has_line() {
  printf '%s\n' "$1" | grep -qxF -- "$2"
}

mode_of() {
  python3 -c 'import os, sys; print(oct(os.stat(sys.argv[1]).st_mode))' "$1"
}

# One line per path under $1: relative path, type, mode, and a sha256 for
# regular files (link target for symlinks). Equal snapshots mean nothing on
# disk changed.
tree_snapshot() {
  python3 - "$1" <<'PY'
import hashlib, os, stat, sys
root = sys.argv[1]
rows = []
for dirpath, dirnames, filenames in os.walk(root):
    for name in dirnames + filenames:
        path = os.path.join(dirpath, name)
        st = os.lstat(path)
        rel = os.path.relpath(path, root)
        if stat.S_ISLNK(st.st_mode):
            rows.append("%s link %o %s" % (rel, st.st_mode, os.readlink(path)))
        elif stat.S_ISDIR(st.st_mode):
            rows.append("%s dir %o" % (rel, st.st_mode))
        else:
            with open(path, "rb") as f:
                digest = hashlib.sha256(f.read()).hexdigest()
            rows.append("%s file %o %s" % (rel, st.st_mode, digest))
for row in sorted(rows):
    print(row)
PY
}

# A hand-written CLAUDE.md: CRLF lines, trailing spaces, a non-ASCII line,
# blank lines (one of them CRLF), and no final newline.
write_hand_written() {
  printf '# Team notes\r\nKeep this line.   \r\n\nNon-ASCII: café, naïve, 東京\n\r\n@notes.md\n\nLast line, no newline   ' >"$1"
}

# Committed source copy of the working tree.
SRC="$WORK/src"
mkdir -p "$SRC"
(cd "$REPO" && tar --exclude=.git --exclude=.cursor --exclude=.claude --exclude=.codex --exclude=.writ \
  --exclude=__pycache__ --exclude=.venv --exclude=.pytest_cache -cf - .) | (cd "$SRC" && tar -xf -)
mkdir -p "$SRC/.writ/docs"
cp "$REPO"/.writ/docs/*.md "$SRC/.writ/docs/"
git -C "$SRC" init -q -b main
commit_src "$SRC" source
for f in claude-code/CLAUDE.md scripts/install.sh scripts/uninstall.sh; do
  [ -f "$SRC/$f" ] || fail "fixture: source copy has no $f"
done

# ----- AC-4.3: a hand-written CLAUDE.md round-trips to the original plus one \n -----
A="$WORK/hand-written"
mkdir -p "$A"
write_hand_written "$A/CLAUDE.md"
{ cat "$A/CLAUDE.md"; printf '\n'; } >"$WORK/expected-a"
out=$(run_install "$A" --no-commit) || fail "A: install exited non-zero: $out"
grep -qxF '<!-- writ:start -->' "$A/CLAUDE.md" || fail "A: install did not append the Writ block"
mode_installed=$(mode_of "$A/CLAUDE.md")
out=$(run_uninstall "$A" --no-commit) || fail "A: uninstall exited non-zero: $out"
has_line "$out" '  🗑  Removed: CLAUDE.md Writ block' \
  || fail "A: uninstall did not report the block removal: $out"
[ -f "$A/CLAUDE.md" ] || fail "A: uninstall deleted the hand-written CLAUDE.md"
cmp "$WORK/expected-a" "$A/CLAUDE.md" \
  || fail "A: CLAUDE.md is not the original plus one \\n: $(od -c "$A/CLAUDE.md" | tail -n 5)"
[ "$(mode_of "$A/CLAUDE.md")" = "$mode_installed" ] \
  || fail "A: uninstall changed the mode of CLAUDE.md from $mode_installed to $(mode_of "$A/CLAUDE.md")"
[ ! -e "$A/.claude" ] || fail "A: uninstall left .claude/: $(cd "$A" && find .claude | head -n 5)"

# ----- AC-4.3: no CLAUDE.md before install → none after uninstall -----
B="$WORK/no-file"
mkdir -p "$B"
out=$(run_install "$B" --no-commit) || fail "B: install exited non-zero: $out"
[ -f "$B/CLAUDE.md" ] || fail "B: install did not create CLAUDE.md"
out=$(run_uninstall "$B" --no-commit) || fail "B: uninstall exited non-zero: $out"
has_line "$out" '  🗑  Removed: CLAUDE.md (empty after Writ block removal)' \
  || fail "B: uninstall did not report deleting the block-only CLAUDE.md: $out"
[ ! -e "$B/CLAUDE.md" ] || fail "B: CLAUDE.md still exists after uninstall"

# ----- AC-4.3: the dry run names the block and changes no file -----
C="$WORK/dry-run"
mkdir -p "$C"
write_hand_written "$C/CLAUDE.md"
out=$(run_install "$C" --no-commit) || fail "C: install exited non-zero: $out"
tree_snapshot "$C" >"$WORK/c-before"
out=$(run_uninstall "$C" --dry-run) || fail "C: uninstall --dry-run exited non-zero: $out"
tree_snapshot "$C" >"$WORK/c-after"
cmp -s "$WORK/c-before" "$WORK/c-after" \
  || fail "C: uninstall --dry-run changed files: $(diff "$WORK/c-before" "$WORK/c-after" | head -n 10)"
has_line "$out" '  🗑  CLAUDE.md Writ block' \
  || fail "C: uninstall --dry-run does not list the CLAUDE.md Writ block: $out"
if has_line "$out" '  🗑  CLAUDE.md'; then
  fail "C: uninstall --dry-run still lists the whole CLAUDE.md for removal: $out"
fi
has_line "$out" '    📄 Extras:    2 (.claude/system-instructions.md CLAUDE.md Writ block)' \
  || fail "C: the Extras line does not count the CLAUDE.md Writ block: $(printf '%s\n' "$out" | grep -F 'Extras' || true)"
# Every listed removal is one item of the total.
listed=$(printf '%s\n' "$out" | grep -c '^  🗑  ' || true)
has_line "$out" "  Would remove $listed file(s)." \
  || fail "C: the dry-run total does not match the $listed listed removals: $(printf '%s\n' "$out" | grep -F 'Would remove' || true)"

# ----- AC-4.2: malformed markers stop uninstall with 13; CLAUDE.md untouched -----
D="$WORK/malformed"
mkdir -p "$D"
write_hand_written "$D/CLAUDE.md"
out=$(run_install "$D" --no-commit) || fail "D: install exited non-zero: $out"
printf '<!-- writ:start -->\n' >>"$D/CLAUDE.md"
cp "$D/CLAUDE.md" "$WORK/d-before"
rc=0
out=$(run_uninstall "$D" --no-commit) || rc=$?
[ "$rc" = 13 ] || fail "D: uninstall exited $rc on malformed markers, expected 13: $out"
printf '%s\n' "$out" | grep -q '^❌ CLAUDE.md block error: malformed markers' \
  || fail "D: no ❌ line for the malformed markers: $out"
cmp -s "$WORK/d-before" "$D/CLAUDE.md" || fail "D: uninstall changed CLAUDE.md with malformed markers"

printf 'OK uninstall keeps CLAUDE.md user-owned\n'
