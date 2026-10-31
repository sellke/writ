#!/usr/bin/env bash
# Install must not hijack a plain `git push` (ADR-017).
#
# Any remote.<name>.push line replaces push.default for a plain `git push`.
# Installs used to add `remote.<remote>.push = refs/notes/writ`, so `git push`
# pushed only the notes and never the current branch; with no notes yet it
# failed with "src refspec refs/notes/writ does not match any". /ship and
# /release push the notes explicitly, so install adds no push line.
#
# In temp git projects with a bare-repo remote:
#   - a fresh install adds the fetch refspec and no push line, and a plain
#     `git push` afterwards lands the branch on the remote.
#   - re-running install.sh over an earlier install removes its push line,
#     keeps the fetch line and the user's own refspecs. --dry-run lists the
#     removal and changes nothing.
#   - update.sh removes the push line too, including when there is nothing
#     to update. --dry-run lists the removal and changes nothing.
#
# Runs the real scripts from a committed temp copy of this working tree. Does
# `git init`: run outside any sandbox. Never point it at the Writ repo itself.
set -euo pipefail

REPO="$(cd "$(dirname "$0")/../.." && pwd)"
WORK=$(mktemp -d "${TMPDIR:-/tmp}/writ-notes-push-refspec-test.XXXXXX")
trap 'rm -rf "$WORK"' EXIT
WORK=$(cd "$WORK" && pwd)

export GIT_AUTHOR_NAME=t GIT_AUTHOR_EMAIL=t@example.invalid
export GIT_COMMITTER_NAME=t GIT_COMMITTER_EMAIL=t@example.invalid
# The user's global push.default, push.autoSetupRemote, or signing settings
# must not decide what a plain `git push` does here.
: >"$WORK/gitconfig"
export GIT_CONFIG_GLOBAL="$WORK/gitconfig" GIT_CONFIG_NOSYSTEM=1

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
  local proj="$1"
  shift
  (cd "$proj" && bash "$SRC/scripts/install.sh" --platform claude "$@" 2>&1)
}

run_update() {
  local proj="$1"
  shift
  (cd "$proj" && WRIT_REPO="$SRC" bash "$SRC/scripts/update.sh" --platform claude "$@" 2>&1)
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

# A git project whose main branch tracks a bare-repo origin, plus a second
# remote carrying the user's own push refspec.
new_git_project() {
  local proj="$WORK/$1"
  mkdir -p "$proj"
  git init -q --bare "$WORK/$1-remote.git"
  git -C "$proj" init -q -b main
  printf '# My project\n' >"$proj/README.md"
  git -C "$proj" add -A
  git -C "$proj" commit -q -m init
  git -C "$proj" remote add origin "$WORK/$1-remote.git"
  git -C "$proj" push -q -u origin main
  git -C "$proj" remote add upstream "$WORK/$1-remote.git"
  git -C "$proj" config --add remote.upstream.push 'refs/heads/main:refs/heads/main'
  printf '%s\n' "$proj"
}

# Commit, run a plain `git push`, and require the remote's main to match HEAD.
assert_plain_push_lands() {
  local proj="$1" label="$2" out
  printf 'change\n' >>"$proj/README.md"
  git -C "$proj" commit -q -am "change after $label"
  out=$(git -C "$proj" push 2>&1) || fail "$label: plain git push failed: $out"
  [ "$(git -C "$proj" rev-parse HEAD)" = "$(git -C "$proj" rev-parse origin/main)" ] \
    || fail "$label: plain git push did not update origin/main: $out"
  [ "$(git -C "$proj" rev-parse HEAD)" = "$(git --git-dir="$WORK/$label-remote.git" rev-parse main)" ] \
    || fail "$label: the remote's main is not the pushed HEAD: $out"
}

# Committed source copy of the working tree.
SRC="$WORK/src"
mkdir -p "$SRC"
(cd "$REPO" && tar --exclude=.git --exclude=.cursor --exclude=.claude --exclude=.codex --exclude=.writ \
  --exclude='.writ-lanes-*' --exclude=__pycache__ --exclude=.venv --exclude=.pytest_cache -cf - .) \
  | (cd "$SRC" && tar -xf -)
mkdir -p "$SRC/.writ/docs"
cp "$REPO"/.writ/docs/*.md "$SRC/.writ/docs/"
git -C "$SRC" init -q -b main
git -C "$SRC" add -A
git -C "$SRC" commit -q -m source

WRIT_FETCH='remote.origin.fetch +refs/notes/writ:refs/notes/origin-writ'
WRIT_PUSH='remote.origin.push refs/notes/writ'

# ----- fresh install: fetch refspec, no push line, plain push lands -----
P=$(new_git_project fresh)
out=$(run_install "$P") || fail "fresh: install exited non-zero: $out"
post=$(refspecs "$P")
printf '%s\n' "$post" | grep -qxF "$WRIT_FETCH" || fail "fresh: install added no fetch refspec: $post"
if printf '%s\n' "$post" | grep -qxF "$WRIT_PUSH"; then
  fail "fresh: install added remote.origin.push refs/notes/writ, which hijacks a plain git push"
fi
printf '%s\n' "$post" | grep -qxF 'remote.upstream.push refs/heads/main:refs/heads/main' \
  || fail "fresh: install removed the user's own push refspec: $post"
assert_plain_push_lands "$P" fresh
git -C "$P" notes --ref=writ add -m 'audit' HEAD
assert_plain_push_lands "$P" fresh
ok "fresh install: no push refspec, and a plain git push lands the branch with or without notes"

# ----- re-running install.sh migrates an earlier install -----
P=$(new_git_project reinstall)
out=$(run_install "$P") || fail "reinstall: install exited non-zero: $out"
git -C "$P" config --add remote.origin.push 'refs/notes/writ'
pre=$(refspecs "$P")
out=$(run_install "$P" --dry-run) || fail "reinstall: install --dry-run exited non-zero: $out"
[ "$(refspecs "$P")" = "$pre" ] || fail "reinstall: install --dry-run changed the refspecs"
printf '%s\n' "$out" | grep -qF 'remote.origin.push' \
  || fail "reinstall: install --dry-run did not list the push refspec it would remove: $out"
out=$(run_install "$P") || fail "reinstall: second install exited non-zero: $out"
post=$(refspecs "$P")
if printf '%s\n' "$post" | grep -qxF "$WRIT_PUSH"; then
  fail "reinstall: re-running install left remote.origin.push refs/notes/writ: $post"
fi
[ "$(printf '%s\n' "$post" | grep -cxF "$WRIT_FETCH")" = 1 ] \
  || fail "reinstall: expected exactly one fetch refspec: $post"
printf '%s\n' "$post" | grep -qxF 'remote.upstream.push refs/heads/main:refs/heads/main' \
  || fail "reinstall: install removed the user's own push refspec: $post"
assert_plain_push_lands "$P" reinstall
ok "re-running install.sh removes an earlier install's push refspec; --dry-run only lists it"

# ----- update.sh migrates an earlier install, even with nothing to update -----
P=$(new_git_project update)
out=$(run_install "$P") || fail "update: install exited non-zero: $out"
git -C "$P" config --add remote.origin.push 'refs/notes/writ'
pre=$(refspecs "$P")
out=$(run_update "$P" --dry-run) || fail "update: update.sh --dry-run exited non-zero: $out"
[ "$(refspecs "$P")" = "$pre" ] || fail "update: update.sh --dry-run changed the refspecs"
printf '%s\n' "$out" | grep -qF 'remote.origin.push' \
  || fail "update: update.sh --dry-run did not list the push refspec it would remove: $out"
out=$(run_update "$P" --no-commit) || fail "update: update.sh exited non-zero: $out"
post=$(refspecs "$P")
if printf '%s\n' "$post" | grep -qxF "$WRIT_PUSH"; then
  fail "update: update.sh left remote.origin.push refs/notes/writ: $post"
fi
printf '%s\n' "$post" | grep -qxF "$WRIT_FETCH" || fail "update: update.sh removed the fetch refspec: $post"
printf '%s\n' "$post" | grep -qxF 'remote.upstream.push refs/heads/main:refs/heads/main' \
  || fail "update: update.sh removed the user's own push refspec: $post"
assert_plain_push_lands "$P" update
ok "update.sh removes an earlier install's push refspec; --dry-run only lists it"

printf '\n%d checks passed\n' "$pass_count"
