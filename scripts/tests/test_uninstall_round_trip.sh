#!/usr/bin/env bash
# Uninstall leaves the project as install found it (defect D8 of the Phase 14
# acceptance pass).
#
# For each platform (cursor, claude, codex), install.sh then uninstall.sh run
# in temp projects, and the file tree is compared with a snapshot taken before
# install:
#   - --include-writ: the tree equals the snapshot. Shipped scripts, shipped
#     .writ/docs, the .gitignore lines, a seeded .cursorindexingignore, and an
#     unmodified .codex/config.toml are all gone; a user's .gitignore is
#     byte-for-byte what it was.
#   - default: only the kept .writ/ scaffold, the two ignore files, and the
#     files the user modified differ. A user's file at a shipped path that
#     install preserved (no baseline) stays untouched. The output names each
#     modified file it kept.
#   - a modified .codex/config.toml still prompts; with no answer it stays.
#   - two platforms installed: uninstalling one keeps the shared scripts and
#     docs; uninstalling the last removes them.
#   - with git: uninstall's commit leaves a clean working tree.
#
# Runs the real scripts from a committed temp copy of this working tree. Does
# `git init`: run outside any sandbox. Never point it at the Writ repo itself.
set -euo pipefail

REPO="$(cd "$(dirname "$0")/../.." && pwd)"
WORK=$(mktemp -d "${TMPDIR:-/tmp}/writ-uninstall-round-trip-test.XXXXXX")
trap 'rm -rf "$WORK"' EXIT
WORK=$(cd "$WORK" && pwd)

export GIT_AUTHOR_NAME=t GIT_AUTHOR_EMAIL=t@example.invalid
export GIT_COMMITTER_NAME=t GIT_COMMITTER_EMAIL=t@example.invalid

pass_count=0

fail() {
  printf 'FAIL: %s\n' "$1" >&2
  exit 1
}

ok() {
  pass_count=$((pass_count + 1))
  printf 'PASS: %s\n' "$1"
}

run_install() {
  local proj="$1" platform="$2"
  shift 2
  (cd "$proj" && bash "$SRC/scripts/install.sh" --platform "$platform" "$@" 2>&1)
}

# stdin is /dev/null: a prompt reads no answer and takes its default.
run_uninstall() {
  local proj="$1" platform="$2"
  shift 2
  (cd "$proj" && bash "$SRC/scripts/uninstall.sh" --platform "$platform" "$@" </dev/null 2>&1)
}

# One line per path under $1 (skipping .git): relative path, type, mode, and a
# sha256 for regular files. Equal snapshots mean nothing on disk changed.
tree_snapshot() {
  python3 - "$1" <<'PY'
import hashlib, os, stat, sys
root = sys.argv[1]
rows = []
for dirpath, dirnames, filenames in os.walk(root):
    if dirpath == root and ".git" in dirnames:
        dirnames.remove(".git")
    for name in dirnames + filenames:
        path = os.path.join(dirpath, name)
        st = os.lstat(path)
        rel = os.path.relpath(path, root)
        if stat.S_ISLNK(st.st_mode):
            rows.append("%s\tlink %o %s" % (rel, st.st_mode, os.readlink(path)))
        elif stat.S_ISDIR(st.st_mode):
            rows.append("%s\tdir %o" % (rel, st.st_mode))
        else:
            with open(path, "rb") as f:
                digest = hashlib.sha256(f.read()).hexdigest()
            rows.append("%s\tfile %o %s" % (rel, st.st_mode, digest))
for row in sorted(rows):
    print(row)
PY
}

# Paths whose snapshot rows differ between files $1 and $2 (added, removed, or
# changed), one per line, sorted.
changed_paths() {
  python3 - "$1" "$2" <<'PY'
import sys
def load(p):
    with open(p) as f:
        return dict(line.rstrip("\n").split("\t", 1) for line in f if line.strip())
a, b = load(sys.argv[1]), load(sys.argv[2])
for path in sorted(set(a) | set(b)):
    if a.get(path) != b.get(path):
        print(path)
PY
}

# Fails unless every path in changed-path list $2 matches one of the extended
# regexes in $3 (one per line). $1 names the case.
assert_only_changed() {
  local label="$1" changed="$2" allowed="$3" path
  while IFS= read -r path; do
    [ -n "$path" ] || continue
    if ! printf '%s\n' "$path" | grep -qE -f <(printf '%s\n' "$allowed"); then
      fail "$label: unexpected leftover or change after uninstall: $path (all changes: $(printf '%s' "$changed" | tr '\n' ' '))"
    fi
  done <<<"$changed"
}

new_project() {
  local proj="$WORK/$1"
  mkdir -p "$proj"
  printf '%s\n' "$proj"
}

# Committed source copy of the working tree.
SRC="$WORK/src"
mkdir -p "$SRC"
(cd "$REPO" && tar --exclude=.git --exclude=.cursor --exclude=.claude --exclude=.codex --exclude=.writ \
  --exclude=__pycache__ --exclude=.venv --exclude=.pytest_cache -cf - .) | (cd "$SRC" && tar -xf -)
mkdir -p "$SRC/.writ/docs"
cp "$REPO"/.writ/docs/*.md "$SRC/.writ/docs/"
git -C "$SRC" init -q -b main
git -C "$SRC" add -A
git -C "$SRC" commit -q -m source
for f in scripts/install.sh scripts/uninstall.sh scripts/spec-status.py .writ/docs/spec-format.md; do
  [ -f "$SRC/$f" ] || fail "fixture: source copy has no $f"
done

# Left after a default uninstall by design: the .writ/ scaffold and the two
# ignore files that protect it.
KEPT_BY_DESIGN='^\.writ(/.*)?$
^\.gitignore$
^\.cursorindexingignore$'

for platform in cursor claude codex; do
  # ----- --include-writ, user .gitignore and a user script: tree equals the snapshot -----
  P=$(new_project "full-$platform")
  printf '# My project\n' >"$P/README.md"
  mkdir -p "$P/scripts"
  printf '#!/bin/sh\necho build\n' >"$P/scripts/build.sh"
  chmod 755 "$P/scripts/build.sh"
  printf 'node_modules/\n*.log\n' >"$P/.gitignore"
  tree_snapshot "$P" >"$WORK/pre"
  out=$(run_install "$P" "$platform" --no-commit) || fail "full-$platform: install exited non-zero: $out"
  [ -f "$P/scripts/spec-status.py" ] || fail "full-$platform: install shipped no scripts/spec-status.py"
  grep -qxF '.writ/state/' "$P/.gitignore" || fail "full-$platform: install added no .writ/state/ to .gitignore"
  out=$(run_uninstall "$P" "$platform" --no-commit --include-writ) \
    || fail "full-$platform: uninstall exited non-zero: $out"
  tree_snapshot "$P" >"$WORK/post"
  changed=$(changed_paths "$WORK/pre" "$WORK/post")
  [ -z "$changed" ] || fail "full-$platform: tree differs from the pre-install snapshot: $(printf '%s' "$changed" | tr '\n' ' ')"
  ok "$platform: --include-writ restores a project with its own .gitignore and script"

  # ----- --include-writ, empty project: nothing left -----
  P=$(new_project "bare-$platform")
  out=$(run_install "$P" "$platform" --no-commit) || fail "bare-$platform: install exited non-zero: $out"
  [ -f "$P/.cursorindexingignore" ] || fail "bare-$platform: install seeded no .cursorindexingignore"
  out=$(run_uninstall "$P" "$platform" --no-commit --include-writ) \
    || fail "bare-$platform: uninstall exited non-zero: $out"
  left=$(cd "$P" && find . -mindepth 1 | sort)
  [ -z "$left" ] || fail "bare-$platform: uninstall left: $(printf '%s' "$left" | tr '\n' ' ')"
  ok "$platform: --include-writ leaves an empty project empty"

  # ----- default uninstall: modified files and the user's own file stay -----
  P=$(new_project "keep-$platform")
  mkdir -p "$P/scripts"
  printf '# my own story-deps\n' >"$P/scripts/story-deps.py"
  tree_snapshot "$P" >"$WORK/pre"
  out=$(run_install "$P" "$platform" --no-commit) || fail "keep-$platform: install exited non-zero: $out"
  [ "$(cat "$P/scripts/story-deps.py")" = '# my own story-deps' ] \
    || fail "keep-$platform: install overwrote the user's scripts/story-deps.py"
  printf '# local tweak\n' >>"$P/scripts/spec-status.py"
  printf '\nLocal note.\n' >>"$P/.writ/docs/spec-format.md"
  allowed="$KEPT_BY_DESIGN
^scripts/spec-status\\.py\$"
  if [ "$platform" = codex ]; then
    printf '# local setting\n' >>"$P/.codex/config.toml"
    allowed="$allowed
^\\.codex\$
^\\.codex/config\\.toml\$"
  fi
  out=$(run_uninstall "$P" "$platform" --no-commit) || fail "keep-$platform: uninstall exited non-zero: $out"
  tree_snapshot "$P" >"$WORK/post"
  changed=$(changed_paths "$WORK/pre" "$WORK/post")
  assert_only_changed "keep-$platform" "$changed" "$allowed"
  [ -f "$P/scripts/spec-status.py" ] || fail "keep-$platform: uninstall removed the modified scripts/spec-status.py"
  [ -f "$P/.writ/docs/spec-format.md" ] || fail "keep-$platform: uninstall removed the modified .writ/docs/spec-format.md"
  [ ! -e "$P/scripts/spec-deps.py" ] || fail "keep-$platform: uninstall left the unmodified scripts/spec-deps.py"
  writ_files=$(cd "$P" && find .writ -type f | sort)
  [ "$writ_files" = '.writ/docs/spec-format.md' ] \
    || fail "keep-$platform: .writ/ holds more than the modified doc: $(printf '%s' "$writ_files" | tr '\n' ' ')"
  printf '%s\n' "$out" | grep -qF 'scripts/spec-status.py' \
    || fail "keep-$platform: uninstall did not name the kept scripts/spec-status.py: $out"
  printf '%s\n' "$out" | grep -qF '.writ/docs/spec-format.md' \
    || fail "keep-$platform: uninstall did not name the kept .writ/docs/spec-format.md: $out"
  grep -qxF '.writ/state/' "$P/.gitignore" \
    || fail "keep-$platform: default uninstall removed .writ/state/ from .gitignore while .writ/ stays"
  [ -f "$P/.cursorindexingignore" ] \
    || fail "keep-$platform: default uninstall removed .cursorindexingignore while .writ/ stays"
  if [ "$platform" = codex ]; then
    [ -f "$P/.codex/config.toml" ] || fail "keep-codex: uninstall removed a modified .codex/config.toml without an answer"
    printf '%s\n' "$out" | grep -qF 'Remove it? [y/N]' \
      || fail "keep-codex: uninstall did not prompt for a modified .codex/config.toml: $out"
  fi
  ok "$platform: default uninstall keeps modified files, the user's file, and the ignore files"
done

# ----- two platforms: the shared files stay until the last uninstall -----
P=$(new_project multi)
printf '# My project\n' >"$P/README.md"
tree_snapshot "$P" >"$WORK/pre"
out=$(run_install "$P" cursor --no-commit) || fail "multi: cursor install exited non-zero: $out"
out=$(run_install "$P" claude --no-commit) || fail "multi: claude install exited non-zero: $out"
out=$(run_uninstall "$P" claude --no-commit) || fail "multi: claude uninstall exited non-zero: $out"
[ -f "$P/scripts/spec-status.py" ] || fail "multi: uninstalling claude removed scripts the cursor install still uses"
[ -f "$P/.writ/docs/spec-format.md" ] || fail "multi: uninstalling claude removed docs the cursor install still uses"
[ -f "$P/.cursor/.writ-manifest" ] || fail "multi: uninstalling claude removed the cursor manifest"
out=$(run_uninstall "$P" cursor --no-commit --include-writ) || fail "multi: cursor uninstall exited non-zero: $out"
tree_snapshot "$P" >"$WORK/post"
changed=$(changed_paths "$WORK/pre" "$WORK/post")
[ -z "$changed" ] || fail "multi: tree differs from the pre-install snapshot: $(printf '%s' "$changed" | tr '\n' ' ')"
ok "two platforms: shared files stay until the last uninstall"

# ----- with git: uninstall's commit includes every removal -----
P=$(new_project git)
git -C "$P" init -q -b main
printf '# My project\n' >"$P/README.md"
printf 'node_modules/\n' >"$P/.gitignore"
git -C "$P" add -A
git -C "$P" commit -q -m init
tree_snapshot "$P" >"$WORK/pre"
out=$(run_install "$P" claude) || fail "git: install exited non-zero: $out"
out=$(run_uninstall "$P" claude --include-writ) || fail "git: uninstall exited non-zero: $out"
tree_snapshot "$P" >"$WORK/post"
changed=$(changed_paths "$WORK/pre" "$WORK/post")
[ -z "$changed" ] || fail "git: tree differs from the pre-install snapshot: $(printf '%s' "$changed" | tr '\n' ' ')"
status=$(git -C "$P" status --porcelain)
[ -z "$status" ] || fail "git: uninstall's commit left changes: $status"
ok "git: uninstall's commit leaves a clean working tree"

printf '\n%d checks passed\n' "$pass_count"
