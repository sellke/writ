#!/usr/bin/env bash
# Install and upgrade paths for the rename to /writ-design (Story 3 of
# 2026-10-20-platform-neutral-names).
#
# AC-3.1: a fresh install from the new source on cursor, claude, and codex
#         installs commands/writ-design.md and not the old command file, and
#         the project manifest records only the new path.
# AC-3.2: a project installed from the old source, old file unmodified, then
#         updated from the new source on each platform: the dry run lists the
#         old file as stale and changes nothing; the real run removes it,
#         reports the removal, installs writ-design.md, and drops the old path
#         from the manifest.
# AC-3.3: a claude project whose old file was edited locally keeps it byte for
#         byte across two updates, and each run prints the stale-kept warning
#         for it. The second run leaves through "Already up to date".
#
# The old name is built from OLD_NAME, never spelled out, so this file is not
# a hit of the reference gate in test_platform_neutral_names.py.
#
# Runs the real scripts against temp targets. update.sh clones WRIT_REPO, so
# both sources are committed copies of this working tree. Does `git init`: run
# outside any sandbox.
set -euo pipefail

REPO="$(cd "$(dirname "$0")/../.." && pwd)"
WORK=$(mktemp -d "${TMPDIR:-/tmp}/writ-design-rename-test.XXXXXX")
trap 'rm -rf "$WORK"' EXIT

OLD_NAME=design
OLD_PATH="commands/${OLD_NAME}.md"
NEW_PATH="commands/writ-design.md"
PLATFORMS=(cursor claude codex)

# The exact lines update.sh prints (scripts/update.sh: the dry-run stale list,
# the stale removal loop, and detect_stale_files).
DRY_RUN_STALE_LINE="    🗑  $OLD_PATH"
REMOVED_LINE="  🗑  Removed: $OLD_PATH"
KEPT_WARNING_LINE="  ⚠️  Stale (no longer shipped, locally modified — kept): $OLD_PATH"

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

platform_dir() {
  case "$1" in
    cursor) printf '.cursor\n' ;;
    claude) printf '.claude\n' ;;
    codex)  printf '.codex\n' ;;
    *) fail "unknown platform $1" ;;
  esac
}

# Manifest lines for one path: "<hash>  <path>".
manifest_lines() {
  awk -v p="$2" '!/^#/ && $2 == p' "$1"
}

# Exact-line match, indentation included.
has_line() {
  printf '%s\n' "$1" | grep -qxF -- "$2"
}

install_into() {
  local label="$1" proj="$2" src="$3" platform="$4" out
  mkdir -p "$proj"
  out=$(cd "$proj" && bash "$src/scripts/install.sh" --platform "$platform" --no-commit 2>&1) \
    || fail "$label: install exited non-zero: $out"
}

update_in() {
  local label="$1" proj="$2" platform="$3"
  shift 3
  UPDATE_OUT=$(cd "$proj" && WRIT_REPO="$SRC_NEW" bash "$SRC_NEW/scripts/update.sh" \
    --platform "$platform" --no-commit "$@" 2>&1) \
    || fail "$label: update exited non-zero: $UPDATE_OUT"
}

# ----- fixtures: SRC_NEW is this tree; SRC_OLD stands in for the last release -----
SRC_NEW="$WORK/src-new"
mkdir -p "$SRC_NEW"
(cd "$REPO" && tar --exclude=.git --exclude=.cursor --exclude=.claude --exclude=.codex --exclude=.writ \
  --exclude='.writ-lanes-*' --exclude=__pycache__ --exclude=.venv --exclude=.pytest_cache -cf - .) \
  | (cd "$SRC_NEW" && tar -xf -)
mkdir -p "$SRC_NEW/.writ/docs"
cp "$REPO"/.writ/docs/*.md "$SRC_NEW/.writ/docs/"
git -C "$SRC_NEW" init -q -b main
commit_src "$SRC_NEW" "new source"
[ -f "$SRC_NEW/$NEW_PATH" ] || fail "fixture: SRC_NEW has no $NEW_PATH"
[ ! -e "$SRC_NEW/$OLD_PATH" ] || fail "fixture: SRC_NEW still has $OLD_PATH"

# install.sh copies and records every commands/*.md and never reads
# .writ/manifest.yaml or the catalogs, so the old release differs from the
# new source only in the command file and its frontmatter name.
SRC_OLD="$WORK/src-old"
cp -R "$SRC_NEW" "$SRC_OLD"
git -C "$SRC_OLD" mv "$NEW_PATH" "$OLD_PATH"
sed "s/^name: writ-design\$/name: ${OLD_NAME}/" "$SRC_OLD/$OLD_PATH" > "$WORK/old-command.md"
mv "$WORK/old-command.md" "$SRC_OLD/$OLD_PATH"
grep -qx "name: ${OLD_NAME}" "$SRC_OLD/$OLD_PATH" || fail "fixture: SRC_OLD frontmatter was not set back to name: ${OLD_NAME}"
commit_src "$SRC_OLD" "old release"
[ ! -e "$SRC_OLD/$NEW_PATH" ] || fail "fixture: SRC_OLD still has $NEW_PATH"
OLD_HASH=$(hash_file "$SRC_OLD/$OLD_PATH")

# ----- AC-3.1: fresh install from SRC_NEW -----
for p in "${PLATFORMS[@]}"; do
  pdir=$(platform_dir "$p")
  proj="$WORK/fresh-$p"
  manifest="$proj/$pdir/.writ-manifest"
  install_into "AC-3.1 $p" "$proj" "$SRC_NEW" "$p"
  [ -f "$proj/$pdir/$NEW_PATH" ] || fail "AC-3.1 $p: $pdir/$NEW_PATH not installed"
  [ ! -e "$proj/$pdir/$OLD_PATH" ] || fail "AC-3.1 $p: $pdir/$OLD_PATH installed"
  [ -f "$manifest" ] || fail "AC-3.1 $p: no manifest at $pdir/.writ-manifest"
  [ "$(manifest_lines "$manifest" "$NEW_PATH" | wc -l | tr -d ' ')" = 1 ] \
    || fail "AC-3.1 $p: manifest does not record $NEW_PATH once"
  [ -z "$(manifest_lines "$manifest" "$OLD_PATH")" ] || fail "AC-3.1 $p: manifest records $OLD_PATH"
done

# ----- AC-3.2: unmodified old file, updated from SRC_NEW -----
for p in "${PLATFORMS[@]}"; do
  pdir=$(platform_dir "$p")
  proj="$WORK/upgrade-$p"
  manifest="$proj/$pdir/.writ-manifest"
  install_into "AC-3.2 $p" "$proj" "$SRC_OLD" "$p"
  # Fixture sanity: this is an old install.
  [ -f "$proj/$pdir/$OLD_PATH" ] || fail "AC-3.2 $p fixture: $pdir/$OLD_PATH not installed from SRC_OLD"
  [ ! -e "$proj/$pdir/$NEW_PATH" ] || fail "AC-3.2 $p fixture: $pdir/$NEW_PATH installed from SRC_OLD"
  [ "$(manifest_lines "$manifest" "$OLD_PATH")" = "$OLD_HASH  $OLD_PATH" ] \
    || fail "AC-3.2 $p fixture: manifest does not record $OLD_PATH with its shipped hash"
  cp "$manifest" "$WORK/manifest.before"

  update_in "AC-3.2 $p dry run" "$proj" "$p" --dry-run
  grep -qF 'DRY RUN' <<< "$UPDATE_OUT" || fail "AC-3.2 $p dry run: no dry-run report: $UPDATE_OUT"
  has_line "$UPDATE_OUT" "$DRY_RUN_STALE_LINE" \
    || fail "AC-3.2 $p dry run: no line '$DRY_RUN_STALE_LINE': $UPDATE_OUT"
  [ -f "$proj/$pdir/$OLD_PATH" ] || fail "AC-3.2 $p dry run: $pdir/$OLD_PATH removed"
  [ "$(hash_file "$proj/$pdir/$OLD_PATH")" = "$OLD_HASH" ] || fail "AC-3.2 $p dry run: $pdir/$OLD_PATH changed"
  [ ! -e "$proj/$pdir/$NEW_PATH" ] || fail "AC-3.2 $p dry run: $pdir/$NEW_PATH installed"
  cmp -s "$manifest" "$WORK/manifest.before" || fail "AC-3.2 $p dry run: manifest changed"

  update_in "AC-3.2 $p" "$proj" "$p"
  has_line "$UPDATE_OUT" "$REMOVED_LINE" || fail "AC-3.2 $p: no line '$REMOVED_LINE': $UPDATE_OUT"
  [ ! -e "$proj/$pdir/$OLD_PATH" ] || fail "AC-3.2 $p: $pdir/$OLD_PATH not removed"
  [ -f "$proj/$pdir/$NEW_PATH" ] || fail "AC-3.2 $p: $pdir/$NEW_PATH not installed"
  cmp -s "$proj/$pdir/$NEW_PATH" "$SRC_NEW/$NEW_PATH" || fail "AC-3.2 $p: $pdir/$NEW_PATH differs from SRC_NEW"
  [ -z "$(manifest_lines "$manifest" "$OLD_PATH")" ] || fail "AC-3.2 $p: manifest still records $OLD_PATH"
  [ "$(manifest_lines "$manifest" "$NEW_PATH" | wc -l | tr -d ' ')" = 1 ] \
    || fail "AC-3.2 $p: manifest does not record $NEW_PATH once"
done

# ----- AC-3.3: locally modified old file on claude, two updates -----
p=claude
pdir=$(platform_dir "$p")
proj="$WORK/modified-$p"
manifest="$proj/$pdir/.writ-manifest"
install_into "AC-3.3" "$proj" "$SRC_OLD" "$p"
[ "$(manifest_lines "$manifest" "$OLD_PATH")" = "$OLD_HASH  $OLD_PATH" ] \
  || fail "AC-3.3 fixture: manifest does not record $OLD_PATH with its shipped hash"
printf '# local edit\n' >> "$proj/$pdir/$OLD_PATH"
MODIFIED_HASH=$(hash_file "$proj/$pdir/$OLD_PATH")

for run in 1 2; do
  label="AC-3.3 $p update $run"
  update_in "$label" "$proj" "$p"
  [ -f "$proj/$pdir/$OLD_PATH" ] || fail "$label: the modified $pdir/$OLD_PATH was removed"
  [ "$(hash_file "$proj/$pdir/$OLD_PATH")" = "$MODIFIED_HASH" ] \
    || fail "$label: the modified $pdir/$OLD_PATH changed"
  has_line "$UPDATE_OUT" "$KEPT_WARNING_LINE" || fail "$label: no line '$KEPT_WARNING_LINE': $UPDATE_OUT"
  if grep -qF "Removed: $OLD_PATH" <<< "$UPDATE_OUT"; then
    fail "$label: reports removing the modified $OLD_PATH: $UPDATE_OUT"
  fi
  [ "$(manifest_lines "$manifest" "$OLD_PATH")" = "$OLD_HASH  $OLD_PATH" ] \
    || fail "$label: manifest dropped the install-time baseline of the kept $OLD_PATH"
  [ -f "$proj/$pdir/$NEW_PATH" ] || fail "$label: $pdir/$NEW_PATH not installed"
  if [ "$run" -eq 2 ]; then
    grep -qF 'Already up to date' <<< "$UPDATE_OUT" \
      || fail "$label: second update did not leave through 'Already up to date': $UPDATE_OUT"
  fi
done

echo "PASS test_install_update_writ_design"
