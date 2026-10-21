#!/usr/bin/env bash
# Story 2 of 2026-10-20-claude-code-parity: install, update, and uninstall
# handle .claude/system-instructions.md on Claude Code, and CLAUDE.md stays
# user-owned outside the Writ block.
#
# AC-2.1: a fresh install copies system-instructions.md byte for byte, records
#         it in the manifest, writes a block that holds the import line, and
#         prints a System instructions step. The dry run writes nothing.
# AC-2.2: the bytes before the start-marker line and after the end-marker line
#         survive install (append), update (replace from the baseline with a
#         longer template), and install --force (replace a modified block).
#         The one allowed change is the "\n" an append adds.
# AC-2.3: update updates an unmodified copy, preserves and lists a modified
#         one, overwrites it with --force, and gives a pre-parity project the
#         file as new plus a block with the import line.
# AC-2.4: a preserved block without the import line is left byte-identical
#         and warned about; one with the line is not warned about.
# AC-2.5: uninstall lists and removes the file, and the Claude rows of the
#         three lifecycle command docs name it.
#
# Runs the real scripts against temp targets. update.sh clones WRIT_REPO, so
# the source is a committed copy of this working tree. Does `git init`: run
# outside any sandbox. Never point it at the Writ repo itself.
set -euo pipefail

REPO="$(cd "$(dirname "$0")/../.." && pwd)"
WORK=$(mktemp -d "${TMPDIR:-/tmp}/writ-claude-parity-test.XXXXXX")
trap 'rm -rf "$WORK"' EXIT

IMPORT_LINE='@.claude/system-instructions.md'
SKIPPED_STEP='(skipped — no system-instructions for Claude Code)'
INSTALL_WARNING='⚠️  CLAUDE.md: the preserved Writ block has no @.claude/system-instructions.md line. Add it inside the block, or re-run install.sh --force to replace the block.'
UPDATE_WARNING='⚠️  CLAUDE.md: the preserved Writ block has no @.claude/system-instructions.md line. Add it inside the block, or re-run update.sh --force to replace the block.'

fail() {
  printf 'FAIL: %s\n' "$1" >&2
  exit 1
}

hash_file() {
  if command -v shasum &>/dev/null; then
    shasum -a 256 "$1" | cut -d' ' -f1
  else
    sha256sum "$1" | cut -d' ' -f1
  fi
}

commit_src() {
  git -C "$1" -c user.name=t -c user.email=t@example.invalid add -A
  git -C "$1" -c user.name=t -c user.email=t@example.invalid commit -q -m "$2"
}

# Number of manifest lines whose path is exactly $2.
manifest_count() {
  awk -v p="$2" '!/^#/ && $2 == p' "$1" | wc -l | tr -d ' '
}

# Python shared by split_block and set_inner. Lines keep their endings. A
# marker line matches with one trailing "\r" stripped, as in merge_claude_md.
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

# split_block FILE DIR: DIR/prefix gets the bytes before the start-marker
# line, DIR/inner the lines between the markers, DIR/suffix the bytes after
# the end-marker line.
split_block() {
  mkdir -p "$2"
  python3 -c "$BLOCK_PY"'
pre, _, inner, _, post = parts(sys.argv[1])
for name, part in (("prefix", pre), ("inner", inner), ("suffix", post)):
    with open(sys.argv[2] + "/" + name, "wb") as f:
        f.write(b"".join(part))
' "$1" "$2" || fail "cannot split the Writ block of $1"
}

# set_inner FILE NEW: replace the lines between the markers with the bytes of
# file NEW. Every other byte of FILE stays.
set_inner() {
  python3 -c "$BLOCK_PY"'
pre, start, _, end, post = parts(sys.argv[1])
with open(sys.argv[2], "rb") as f:
    new = f.read()
with open(sys.argv[1], "wb") as f:
    f.write(b"".join(pre + start) + new + b"".join(end + post))
' "$1" "$2" || fail "cannot replace the Writ block of $1"
}

# Run a lifecycle script from source $2 in project $1 with the remaining
# arguments. update.sh clones WRIT_REPO, so it points at the same source.
run_install() {
  local proj="$1" src="$2"
  shift 2
  (cd "$proj" && bash "$src/scripts/install.sh" --platform claude "$@" 2>&1)
}

run_update() {
  local proj="$1" src="$2"
  shift 2
  (cd "$proj" && WRIT_REPO="$src" bash "$src/scripts/update.sh" --platform claude "$@" 2>&1)
}

run_uninstall() {
  local proj="$1"
  shift
  (cd "$proj" && bash "$SRC/scripts/uninstall.sh" --platform claude "$@" 2>&1)
}

has_line() {
  printf '%s\n' "$1" | grep -qxF -- "$2"
}

has_text() {
  printf '%s\n' "$1" | grep -qF -- "$2"
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
for f in system-instructions.md claude-code/CLAUDE.md scripts/install.sh scripts/update.sh scripts/uninstall.sh; do
  [ -f "$SRC/$f" ] || fail "fixture: source copy has no $f"
done
grep -qxF "$IMPORT_LINE" "$SRC/claude-code/CLAUDE.md" \
  || fail "fixture: claude-code/CLAUDE.md has no $IMPORT_LINE line"
grep -q '^## Prime Directive' "$SRC/system-instructions.md" \
  || fail "fixture: system-instructions.md has no Prime Directive section"
SI_HASH=$(hash_file "$SRC/system-instructions.md")

# A source whose system-instructions.md changed upstream.
SRC_SI="$WORK/src-si"
git clone -q "$SRC" "$SRC_SI"
printf '\nUpstream change for the update test.\n' >> "$SRC_SI/system-instructions.md"
commit_src "$SRC_SI" "change system-instructions.md"
SI_NEW_HASH=$(hash_file "$SRC_SI/system-instructions.md")

# A source whose CLAUDE.md template is one line longer.
SRC_LONG="$WORK/src-long"
git clone -q "$SRC" "$SRC_LONG"
printf 'One more template line for the byte-identity test.\n' >> "$SRC_LONG/claude-code/CLAUDE.md"
commit_src "$SRC_LONG" "lengthen claude-code/CLAUDE.md"

# ----- AC-2.1: install --dry-run prints the copy and writes nothing -----
T_DRY="$WORK/dry"
mkdir -p "$T_DRY"
out=$(run_install "$T_DRY" "$SRC" --dry-run --no-commit) || fail "install --dry-run exited non-zero: $out"
has_line "$out" '  System:  system-instructions.md → always updated' \
  || fail "install --dry-run does not print the system-instructions.md copy: $out"
has_line "$out" '  📖 System:    1 (system-instructions.md)' \
  || fail "install --dry-run inventory does not list system-instructions.md: $out"
left=$(cd "$T_DRY" && find . -mindepth 1 | head -n 5)
[ -z "$left" ] || fail "install --dry-run wrote files: $left"

# ----- AC-2.1: fresh install into a project with no CLAUDE.md -----
T1="$WORK/fresh"
mkdir -p "$T1"
out=$(run_install "$T1" "$SRC" --no-commit) || fail "install exited non-zero: $out"
[ -f "$T1/.claude/system-instructions.md" ] || fail "install: .claude/system-instructions.md missing"
cmp -s "$SRC/system-instructions.md" "$T1/.claude/system-instructions.md" \
  || fail "install: .claude/system-instructions.md differs from the source"
grep -q '^## Prime Directive' "$T1/.claude/system-instructions.md" \
  || fail "install: .claude/system-instructions.md has no Prime Directive section"
MANIFEST1="$T1/.claude/.writ-manifest"
grep -qxF "$SI_HASH  system-instructions.md" "$MANIFEST1" \
  || fail "install: manifest does not record system-instructions.md with the upstream hash: $(grep 'system-instructions' "$MANIFEST1" || true)"
[ "$(manifest_count "$MANIFEST1" system-instructions.md)" = 1 ] \
  || fail "install: manifest records system-instructions.md more than once"
split_block "$T1/CLAUDE.md" "$WORK/t1"
grep -qxF "$IMPORT_LINE" "$WORK/t1/inner" || fail "install: the Writ block has no $IMPORT_LINE line"
cmp -s "$WORK/t1/inner" "$SRC/claude-code/CLAUDE.md" || fail "install: the Writ block is not the template"
printf '%s\n' "$out" | grep -qE '^  \[[0-9]+/[0-9]+\] System instructions\.\.\.$' \
  || fail "install: no System instructions step: $out"
if has_text "$out" "$SKIPPED_STEP"; then
  fail "install still prints the skipped step: $(printf '%s\n' "$out" | grep -F "$SKIPPED_STEP")"
fi
has_line "$out" '  📖 System:    1 (system-instructions.md)' \
  || fail "install inventory does not list system-instructions.md: $out"
# The step count is unchanged: steps run 1..N with no gap, and N is the total.
steps=$(printf '%s\n' "$out" | sed -n -E 's/^  \[([0-9]+)\/([0-9]+)\] .*/\1 \2/p')
expected_step=1
total=""
while read -r n t; do
  [ "$n" = "$expected_step" ] || fail "install: step $n follows step $((expected_step - 1)): $steps"
  [ -z "$total" ] || [ "$t" = "$total" ] || fail "install: step totals differ: $steps"
  total="$t"
  expected_step=$((expected_step + 1))
done <<< "$steps"
[ "$((expected_step - 1))" = "$total" ] || fail "install: ran $((expected_step - 1)) of $total steps: $steps"

# ----- AC-2.2: bytes outside the markers survive append, update, and --force -----
T2="$WORK/bytes"
mkdir -p "$T2"
printf '# Team notes\r\nKeep this line.   \r\nNon-ASCII: café, naïve, 東京\n@notes.md\nLast line, no newline   ' \
  > "$T2/CLAUDE.md"
cp "$T2/CLAUDE.md" "$WORK/user-original"
out=$(run_install "$T2" "$SRC" --no-commit) || fail "byte test install exited non-zero: $out"
split_block "$T2/CLAUDE.md" "$WORK/b1"
{ cat "$WORK/user-original"; printf '\n'; } > "$WORK/expected-prefix"
cmp "$WORK/expected-prefix" "$WORK/b1/prefix" \
  || fail "install append: the bytes before the block are not the original plus one \\n"
[ ! -s "$WORK/b1/suffix" ] || fail "install append: bytes appeared after the block"
grep -qxF "$IMPORT_LINE" "$WORK/b1/inner" || fail "install append: the block has no $IMPORT_LINE line"

# User text below the block too, again with CRLF, an @ line, and no final newline.
printf 'Below the block.\r\n@notes.md\nTrailing spaces, no newline   ' >> "$T2/CLAUDE.md"
split_block "$T2/CLAUDE.md" "$WORK/b2"
cp "$WORK/b2/prefix" "$WORK/prefix0"
cp "$WORK/b2/suffix" "$WORK/suffix0"

out=$(run_update "$T2" "$SRC_LONG" --no-commit) || fail "byte test update exited non-zero: $out"
has_text "$out" 'Updated: CLAUDE.md (Writ block)' || fail "update did not replace the block: $out"
split_block "$T2/CLAUDE.md" "$WORK/b3"
cmp "$WORK/prefix0" "$WORK/b3/prefix" || fail "update: the bytes before the block changed"
cmp "$WORK/suffix0" "$WORK/b3/suffix" || fail "update: the bytes after the block changed"
cmp -s "$WORK/b3/inner" "$SRC_LONG/claude-code/CLAUDE.md" || fail "update: the block is not the longer template"

printf 'A local edit inside the block.\n' > "$WORK/edit-line"
cat "$WORK/b3/inner" "$WORK/edit-line" > "$WORK/edited-inner"
set_inner "$T2/CLAUDE.md" "$WORK/edited-inner"
out=$(run_install "$T2" "$SRC_LONG" --force --no-commit) || fail "byte test install --force exited non-zero: $out"
split_block "$T2/CLAUDE.md" "$WORK/b4"
cmp "$WORK/prefix0" "$WORK/b4/prefix" || fail "install --force: the bytes before the block changed"
cmp "$WORK/suffix0" "$WORK/b4/suffix" || fail "install --force: the bytes after the block changed"
cmp -s "$WORK/b4/inner" "$SRC_LONG/claude-code/CLAUDE.md" || fail "install --force: the block is not the template"

# ----- AC-2.3: update an unmodified copy when upstream changed -----
U1="$WORK/upd-clean"
mkdir -p "$U1"
out=$(run_install "$U1" "$SRC" --no-commit) || fail "U1 install exited non-zero: $out"
out=$(run_update "$U1" "$SRC_SI" --no-commit) || fail "U1 update exited non-zero: $out"
has_line "$out" '    🔄 Update:    system-instructions.md' \
  || fail "update: no Update line for an unmodified system-instructions.md: $out"
cmp -s "$SRC_SI/system-instructions.md" "$U1/.claude/system-instructions.md" \
  || fail "update: the unmodified system-instructions.md was not updated"
grep -qxF "$SI_NEW_HASH  system-instructions.md" "$U1/.claude/.writ-manifest" \
  || fail "update: manifest does not record the new system-instructions.md hash"
# A second update with no upstream change has nothing to do.
out=$(run_update "$U1" "$SRC_SI" --no-commit) || fail "U1 second update exited non-zero: $out"
has_text "$out" 'Already up to date' || fail "second update is not up to date: $out"
if printf '%s\n' "$out" | grep -qE '(New|Update|Preserved): +system-instructions\.md'; then
  fail "second update acts on system-instructions.md: $out"
fi

# ----- AC-2.3: a locally modified copy is preserved and listed; --force overwrites it -----
# Installed from SRC, edited locally, then updated from SRC_SI, whose copy
# also changed: a real three-way conflict.
U2="$WORK/upd-modified"
mkdir -p "$U2"
out=$(run_install "$U2" "$SRC" --no-commit) || fail "U2 install exited non-zero: $out"
printf '\nA local team rule.\n' >> "$U2/.claude/system-instructions.md"
LOCAL_SI_HASH=$(hash_file "$U2/.claude/system-instructions.md")
out=$(run_update "$U2" "$SRC_SI" --no-commit) || fail "U2 update exited non-zero: $out"
has_line "$out" '    ⚡ Preserved: system-instructions.md (local modifications)' \
  || fail "update: no Preserved line for a modified system-instructions.md: $out"
has_line "$out" '    system-instructions.md' \
  || fail "update: system-instructions.md is not in the preserved files list: $out"
[ "$(hash_file "$U2/.claude/system-instructions.md")" = "$LOCAL_SI_HASH" ] \
  || fail "update: the modified system-instructions.md was changed"
grep -qxF "$SI_HASH  system-instructions.md" "$U2/.claude/.writ-manifest" \
  || fail "update: manifest dropped the install-time baseline of the preserved system-instructions.md"
out=$(run_update "$U2" "$SRC_SI" --force --no-commit) || fail "U2 update --force exited non-zero: $out"
has_line "$out" '    🔄 Update:    system-instructions.md (forced)' \
  || fail "update --force: no forced Update line: $out"
cmp -s "$SRC_SI/system-instructions.md" "$U2/.claude/system-instructions.md" \
  || fail "update --force: the modified system-instructions.md was not overwritten"

# ----- AC-2.3: a pre-parity project gets the file and the import line -----
# Before this spec: no .claude/system-instructions.md, no manifest line for
# it, and an old block body that matches its CLAUDE.md.writ-block baseline.
make_pre_parity() {
  local proj="$1" manifest stub_hash
  manifest="$proj/.claude/.writ-manifest"
  rm -f "$proj/.claude/system-instructions.md"
  printf '# Writ\n\nThe block body from before the import line.\n' > "$WORK/old-inner"
  set_inner "$proj/CLAUDE.md" "$WORK/old-inner"
  stub_hash=$(hash_file "$WORK/old-inner")
  awk -v h="$stub_hash" '
    !/^#/ && $2 == "system-instructions.md" { next }
    !/^#/ && $2 == "CLAUDE.md.writ-block" { print h "  CLAUDE.md.writ-block"; next }
    { print }
  ' "$manifest" > "$manifest.new"
  mv "$manifest.new" "$manifest"
  [ "$(manifest_count "$manifest" system-instructions.md)" = 0 ] \
    || fail "fixture: pre-parity manifest still records system-instructions.md"
  grep -qxF "$stub_hash  CLAUDE.md.writ-block" "$manifest" \
    || fail "fixture: pre-parity manifest has no baseline for the old block"
  if grep -qxF "$IMPORT_LINE" "$proj/CLAUDE.md"; then
    fail "fixture: pre-parity CLAUDE.md already has the import line"
  fi
}

check_upgraded() {
  local label="$1" proj="$2" out="$3"
  has_line "$out" '    ✨ New:       system-instructions.md' \
    || fail "$label: no New line for system-instructions.md: $out"
  cmp -s "$SRC/system-instructions.md" "$proj/.claude/system-instructions.md" \
    || fail "$label: .claude/system-instructions.md missing or differs from the source"
  grep -qxF "$SI_HASH  system-instructions.md" "$proj/.claude/.writ-manifest" \
    || fail "$label: manifest does not record system-instructions.md"
  split_block "$proj/CLAUDE.md" "$WORK/upgraded"
  grep -qxF "$IMPORT_LINE" "$WORK/upgraded/inner" || fail "$label: the block has no $IMPORT_LINE line"
  cmp -s "$WORK/upgraded/inner" "$SRC/claude-code/CLAUDE.md" || fail "$label: the block is not the template"
}

U3="$WORK/upd-pre-parity"
mkdir -p "$U3"
out=$(run_install "$U3" "$SRC" --no-commit) || fail "U3 install exited non-zero: $out"
make_pre_parity "$U3"
out=$(run_update "$U3" "$SRC" --no-commit) || fail "pre-parity update exited non-zero: $out"
check_upgraded "pre-parity update" "$U3" "$out"

# The scoped commits of install and update include the file.
G="$WORK/git-project"
mkdir -p "$G"
git -C "$G" init -q -b main
git -C "$G" config user.name t
git -C "$G" config user.email t@example.invalid
out=$(run_install "$G" "$SRC") || fail "git install exited non-zero: $out"
git -C "$G" ls-files --error-unmatch .claude/system-instructions.md >/dev/null 2>&1 \
  || fail "install commit does not include .claude/system-instructions.md"
[ -z "$(git -C "$G" status --porcelain -- .claude/system-instructions.md CLAUDE.md)" ] \
  || fail "install left .claude/system-instructions.md or CLAUDE.md uncommitted"
make_pre_parity "$G"
git -C "$G" add -A
git -C "$G" commit -q -m "pre-parity state"
out=$(run_update "$G" "$SRC") || fail "git update exited non-zero: $out"
check_upgraded "git pre-parity update" "$G" "$out"
[ -z "$(git -C "$G" status --porcelain -- .claude/system-instructions.md CLAUDE.md)" ] \
  || fail "update left .claude/system-instructions.md or CLAUDE.md uncommitted"
git -C "$G" diff --name-status HEAD~1 HEAD -- .claude/system-instructions.md | grep -q '^A' \
  || fail "update commit does not add .claude/system-instructions.md"

# ----- AC-2.4: a preserved block without the import line is warned about and left alone -----
W="$WORK/warn"
mkdir -p "$W"
out=$(run_install "$W" "$SRC" --no-commit) || fail "W install exited non-zero: $out"
printf '# My own Writ block\n\nCustom text, no import line.\n' > "$WORK/custom-inner"
set_inner "$W/CLAUDE.md" "$WORK/custom-inner"
cp "$W/CLAUDE.md" "$WORK/warn-before"

out=$(run_install "$W" "$SRC" --dry-run --no-commit) || fail "W install --dry-run exited non-zero: $out"
has_line "$out" "$INSTALL_WARNING" || fail "install --dry-run: no warning for a preserved block without the import line: $out"
out=$(run_install "$W" "$SRC" --no-commit) || fail "W install exited non-zero: $out"
has_line "$out" "$INSTALL_WARNING" || fail "install: no warning for a preserved block without the import line: $out"
cmp "$WORK/warn-before" "$W/CLAUDE.md" || fail "install: the preserved CLAUDE.md changed"
out=$(run_update "$W" "$SRC" --dry-run --no-commit) || fail "W update --dry-run exited non-zero: $out"
has_line "$out" "$UPDATE_WARNING" || fail "update --dry-run: no warning for a preserved block without the import line: $out"
out=$(run_update "$W" "$SRC" --no-commit) || fail "W update exited non-zero: $out"
has_line "$out" "$UPDATE_WARNING" || fail "update: no warning for a preserved block without the import line: $out"
preserved_at=$(printf '%s\n' "$out" | grep -nF 'Preserved: CLAUDE.md' | head -n 1 | cut -d: -f1)
warning_at=$(printf '%s\n' "$out" | grep -nxF "$UPDATE_WARNING" | head -n 1 | cut -d: -f1)
[ -n "$preserved_at" ] && [ "$preserved_at" -lt "$warning_at" ] \
  || fail "update: the warning does not follow the Preserved line: $out"
cmp "$WORK/warn-before" "$W/CLAUDE.md" || fail "update: the preserved CLAUDE.md changed"

# The same customized block with the import line: no warning.
printf '# My own Writ block\n\n%s\n\nCustom text.\n' "$IMPORT_LINE" > "$WORK/custom-inner"
set_inner "$W/CLAUDE.md" "$WORK/custom-inner"
cp "$W/CLAUDE.md" "$WORK/warn-before"
out=$(run_install "$W" "$SRC" --no-commit) || fail "W install with the line exited non-zero: $out"
has_text "$out" 'Writ block preserved (local modifications)' \
  || fail "install: the block with the import line was not preserved: $out"
if has_text "$out" 'has no @.claude/system-instructions.md line'; then
  fail "install warns about a preserved block that has the import line: $out"
fi
out=$(run_update "$W" "$SRC" --no-commit) || fail "W update with the line exited non-zero: $out"
has_text "$out" 'Preserved: CLAUDE.md' || fail "update: the block with the import line was not preserved: $out"
if has_text "$out" 'has no @.claude/system-instructions.md line'; then
  fail "update warns about a preserved block that has the import line: $out"
fi
cmp "$WORK/warn-before" "$W/CLAUDE.md" || fail "the preserved CLAUDE.md with the import line changed"

# ----- AC-2.5: uninstall lists and removes .claude/system-instructions.md -----
# The fresh install from the AC-2.1 case.
X="$T1"
[ -f "$X/.claude/system-instructions.md" ] || fail "fixture: install wrote no .claude/system-instructions.md"
out=$(run_uninstall "$X" --dry-run) || fail "uninstall --dry-run exited non-zero: $out"
has_line "$out" '  🗑  .claude/system-instructions.md' \
  || fail "uninstall --dry-run does not list .claude/system-instructions.md: $out"
[ -f "$X/.claude/system-instructions.md" ] || fail "uninstall --dry-run removed .claude/system-instructions.md"
out=$(run_uninstall "$X" --no-commit) || fail "uninstall exited non-zero: $out"
[ ! -e "$X/.claude/system-instructions.md" ] || fail "uninstall left .claude/system-instructions.md"
[ ! -e "$X/.claude/commands" ] || fail "uninstall left .claude/commands"
[ ! -e "$X/.claude" ] || fail "uninstall left .claude/: $(cd "$X" && find .claude | head -n 5)"

# ----- AC-2.5: the Claude rows of the lifecycle command docs name the file -----
# Each row is the platform table row, or the first "- Claude Code:" bullet
# after an anchor line, so later Claude bullets elsewhere do not count.
claude_table_rows() {
  grep -E '^\| `claude` \|' "$REPO/$1" || true
}

claude_bullet_after() {
  awk -v anchor="$2" '
    index($0, anchor) { on = 1; next }
    on && /^[[:space:]]*- Claude Code: / { print; exit }
  ' "$REPO/$1"
}

check_row() {
  local doc="$1" what="$2" row="$3"
  [ -n "$row" ] || fail "$doc: no Claude row for $what"
  has_text "$row" '.claude/system-instructions.md' \
    || fail "$doc: the Claude row for $what does not name .claude/system-instructions.md: $row"
}

check_row commands/update-writ.md "the platform table" "$(claude_table_rows commands/update-writ.md)"
check_row commands/update-writ.md "Step 3 platform files" \
  "$(claude_bullet_after commands/update-writ.md '**Apply same logic to platform-specific files:**')"
check_row commands/reinstall-writ.md "the platform table" "$(claude_table_rows commands/reinstall-writ.md)"
check_row commands/reinstall-writ.md "Step 3 removal" \
  "$(claude_bullet_after commands/reinstall-writ.md '**Files to remove:**')"
check_row commands/reinstall-writ.md "Step 4 copy" \
  "$(claude_bullet_after commands/reinstall-writ.md 'Copy platform-specific files:')"
check_row commands/uninstall-writ.md "Step 3 platform files" \
  "$(claude_bullet_after commands/uninstall-writ.md '**Platform-specific files:**')"

printf 'OK Claude Code parity install, update, uninstall\n'
