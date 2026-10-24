#!/usr/bin/env bash
# Uninstall removes the refs/notes/writ refspecs install adds to .git/config
# (ADR-017), the one install side effect the file-tree round-trip test cannot
# see because it skips .git.
#
# In temp git projects with a bare-repo remote:
#   - default uninstall of the only platform: remote.<name>.fetch and .push
#     read exactly what they read before install. The user's own refspecs,
#     including a near-match in the refs/notes/writ namespace, stay.
#   - a pre-0.33 fetch refspec (+refs/notes/writ:refs/notes/writ) goes too.
#   - --dry-run lists the refspecs and changes nothing.
#   - two platforms: uninstalling one keeps the refspecs; uninstalling the last
#     removes them.
#   - the notes themselves (refs/notes/writ) stay.
#
# Runs the real scripts from a committed temp copy of this working tree. Does
# `git init`: run outside any sandbox. Never point it at the Writ repo itself.
set -euo pipefail

REPO="$(cd "$(dirname "$0")/../.." && pwd)"
WORK=$(mktemp -d "${TMPDIR:-/tmp}/writ-uninstall-notes-refspecs-test.XXXXXX")
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

run_uninstall() {
  local proj="$1" platform="$2"
  shift 2
  (cd "$proj" && bash "$SRC/scripts/uninstall.sh" --platform "$platform" "$@" </dev/null 2>&1)
}

# Every fetch and push refspec on every remote of project $1, one per line.
refspecs() {
  local proj="$1" remote key
  for remote in $(git -C "$proj" remote); do
    for key in fetch push; do
      git -C "$proj" config --get-all "remote.$remote.$key" | sed "s|^|remote.$remote.$key |" || true
    done
  done
}

# A git project with a bare-repo origin, a second remote, and the user's own
# refspecs set before install.
new_git_project() {
  local proj="$WORK/$1"
  mkdir -p "$proj"
  git init -q --bare "$WORK/$1-remote.git"
  git -C "$proj" init -q -b main
  printf '# My project\n' >"$proj/README.md"
  git -C "$proj" add -A
  git -C "$proj" commit -q -m init
  git -C "$proj" remote add origin "$WORK/$1-remote.git"
  git -C "$proj" remote add upstream "$WORK/$1-remote.git"
  git -C "$proj" config --add remote.origin.fetch '+refs/notes/writ:refs/notes/team-writ'
  git -C "$proj" config --add remote.upstream.push 'refs/heads/main:refs/heads/main'
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

WRIT_FETCH='remote.origin.fetch +refs/notes/writ:refs/notes/origin-writ'
WRIT_PUSH='remote.origin.push refs/notes/writ'

# ----- one platform: default uninstall restores the refspecs -----
P=$(new_git_project single)
pre=$(refspecs "$P")
out=$(run_install "$P" claude --no-commit) || fail "single: install exited non-zero: $out"
post_install=$(refspecs "$P")
printf '%s\n' "$post_install" | grep -qxF "$WRIT_FETCH" || fail "single: install added no fetch refspec: $post_install"
printf '%s\n' "$post_install" | grep -qxF "$WRIT_PUSH" || fail "single: install added no push refspec: $post_install"
git -C "$P" notes --ref=writ add -m 'audit' HEAD
out=$(run_uninstall "$P" claude --no-commit) || fail "single: uninstall exited non-zero: $out"
post=$(refspecs "$P")
[ "$post" = "$pre" ] || fail "single: refspecs differ from before install.
before:
$pre
after:
$post"
git -C "$P" notes --ref=writ show HEAD >/dev/null 2>&1 || fail "single: uninstall removed the refs/notes/writ notes"
ok "one platform: default uninstall removes Writ's refspecs, keeps the user's and the notes"

# ----- a pre-0.33 fetch refspec goes too -----
P=$(new_git_project legacy)
pre=$(refspecs "$P")
out=$(run_install "$P" claude --no-commit) || fail "legacy: install exited non-zero: $out"
git -C "$P" config --add remote.origin.fetch '+refs/notes/writ:refs/notes/writ'
out=$(run_uninstall "$P" claude --no-commit --include-writ) || fail "legacy: uninstall exited non-zero: $out"
post=$(refspecs "$P")
[ "$post" = "$pre" ] || fail "legacy: refspecs differ from before install.
before:
$pre
after:
$post"
ok "legacy: uninstall removes the pre-0.33 fetch refspec"

# ----- --dry-run lists the refspecs and changes nothing -----
P=$(new_git_project dry)
out=$(run_install "$P" claude --no-commit) || fail "dry: install exited non-zero: $out"
pre=$(refspecs "$P")
out=$(run_uninstall "$P" claude --dry-run) || fail "dry: uninstall exited non-zero: $out"
[ "$(refspecs "$P")" = "$pre" ] || fail "dry: --dry-run changed the refspecs"
printf '%s\n' "$out" | grep -qF '+refs/notes/writ:refs/notes/origin-writ' \
  || fail "dry: --dry-run did not list the fetch refspec: $out"
printf '%s\n' "$out" | grep -qF 'remote.origin.push' \
  || fail "dry: --dry-run did not list the push refspec: $out"
ok "dry run: lists the refspecs and changes nothing"

# ----- two platforms: the refspecs stay until the last uninstall -----
P=$(new_git_project multi)
pre=$(refspecs "$P")
out=$(run_install "$P" cursor --no-commit) || fail "multi: cursor install exited non-zero: $out"
out=$(run_install "$P" claude --no-commit) || fail "multi: claude install exited non-zero: $out"
out=$(run_uninstall "$P" claude --no-commit) || fail "multi: claude uninstall exited non-zero: $out"
mid=$(refspecs "$P")
printf '%s\n' "$mid" | grep -qxF "$WRIT_FETCH" || fail "multi: uninstalling claude removed the fetch refspec cursor still uses"
printf '%s\n' "$mid" | grep -qxF "$WRIT_PUSH" || fail "multi: uninstalling claude removed the push refspec cursor still uses"
out=$(run_uninstall "$P" cursor --no-commit) || fail "multi: cursor uninstall exited non-zero: $out"
post=$(refspecs "$P")
[ "$post" = "$pre" ] || fail "multi: refspecs differ from before install.
before:
$pre
after:
$post"
ok "two platforms: the refspecs stay until the last uninstall"

printf '\n%d checks passed\n' "$pass_count"
