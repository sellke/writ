#!/usr/bin/env bash
# update.sh keeps a locally modified file that upstream stopped shipping, in
# every category, warns about it on every run, and keeps its install-time
# baseline in the manifest (Story 4 of 2026-10-20-ci-and-update-integrity).
#
# AC-4.1: five kept files (commands, agents, skills, .writ/docs, scripts) stay
#         byte-identical across three updates that each rewrite the manifest.
# AC-4.2: the three updates, an "Already up to date" run, and a --dry-run each
#         print the stale warning for all five. The dry run and the
#         "Already up to date" run leave the manifest byte-identical.
# AC-4.3: after each run the manifest has exactly one line per kept path, with
#         the hash recorded at install. The unmodified commands/zz-clean.md is
#         removed on update 1 and its line drops. After the user deletes one
#         kept file, the next update does not warn about it and drops its line.
# AC-4.4: on the pre-fix update.sh this test fails at update 1: no stale
#         warning for the kept commands/zz-kept.md.
# AC-4.5: commands/update-writ.md writes `# baselines: shipped` in the Step 7
#         manifest template and no longer promises a fresh baseline for every
#         installed file.
#
# Runs the real scripts against temp targets. update.sh clones WRIT_REPO, so
# the source is a committed copy of this working tree. Does `git init`: run
# outside any sandbox.
set -euo pipefail

REPO="$(cd "$(dirname "$0")/../.." && pwd)"
WORK=$(mktemp -d "${TMPDIR:-/tmp}/writ-kept-stale-test.XXXXXX")
trap 'rm -rf "$WORK"' EXIT

WARNING='⚠️  Stale (no longer shipped, locally modified — kept): '
# A shipped command the project never edits. Changing it upstream gives
# update.sh something to apply, so it rewrites the manifest instead of exiting
# early with "Already up to date".
BUMPED_COMMAND="commands/create-issue.md"

# Kept files: "<source path> <manifest path> <project path>". The source ships
# them, the project edits them, then the source drops them.
KEPT_FIXTURES="commands/zz-kept.md commands/zz-kept.md .claude/commands/zz-kept.md
claude-code/agents/zz-kept.md agents/zz-kept.md .claude/agents/zz-kept.md
skills/zz-kept/SKILL.md skills/zz-kept/SKILL.md .claude/skills/zz-kept/SKILL.md
.writ/docs/zz-kept.md .writ/docs/zz-kept.md .writ/docs/zz-kept.md
scripts/zz_kept.py scripts/zz_kept.py scripts/zz_kept.py"
# Shipped, left unmodified, then dropped: removed on update 1.
CLEAN_PATH="commands/zz-clean.md"

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

filter_body() {
  sed -n '/^is_shippable_script() {/,/^}/p' "$1"
}

commit_src() {
  git -C "$1" -c user.name=t -c user.email=t@example.invalid add -A
  git -C "$1" -c user.name=t -c user.email=t@example.invalid commit -q -m "$2"
}

# Committed source copy of the working tree, plus the zz-* fixtures.
SRC="$WORK/src"
mkdir -p "$SRC"
(cd "$REPO" && tar --exclude=.git --exclude=.cursor --exclude=.claude --exclude=.codex --exclude=.writ \
  --exclude='.writ-lanes-*' --exclude=__pycache__ --exclude=.venv --exclude=.pytest_cache -cf - .) \
  | (cd "$SRC" && tar -xf -)
mkdir -p "$SRC/.writ/docs"
cp "$REPO"/.writ/docs/*.md "$SRC/.writ/docs/"
[ -f "$SRC/$BUMPED_COMMAND" ] || fail "fixture: source copy has no $BUMPED_COMMAND"
while read -r src_path _ _; do
  [ ! -e "$SRC/$src_path" ] || fail "fixture: $src_path already exists upstream"
  mkdir -p "$(dirname "$SRC/$src_path")"
  printf '# zz-kept fixture\n\nShipped by the first source only.\n' > "$SRC/$src_path"
done <<< "$KEPT_FIXTURES"
printf '#!/usr/bin/env python3\nprint("zz-kept fixture")\n' > "$SRC/scripts/zz_kept.py"
printf '# zz-clean fixture\n\nShipped by the first source only.\n' > "$SRC/$CLEAN_PATH"
body=$(filter_body "$SRC/scripts/update.sh")
[ -n "$body" ] || fail "cannot load is_shippable_script from update.sh"
bash -c "$body"$'\n''is_shippable_script "$1"' _ zz_kept.py \
  || fail "fixture: the ship filter rejects zz_kept.py"
git -C "$SRC" init -q -b main
commit_src "$SRC" "source A"

# ----- install from source A, then edit each kept file -----
PROJ="$WORK/proj"
MANIFEST="$PROJ/.claude/.writ-manifest"
mkdir -p "$PROJ"
out=$(cd "$PROJ" && bash "$SRC/scripts/install.sh" --platform claude --no-commit 2>&1) \
  || fail "install exited non-zero: $out"

manifest_lines() {
  awk -v p="$1" '!/^#/ && $2 == p' "$MANIFEST"
}

# $WORK/kept holds "<manifest path> <project path> <install hash> <local hash>"
# for each kept file the project still has.
: > "$WORK/kept"
while read -r src_path mpath ppath; do
  [ -f "$PROJ/$ppath" ] || fail "fixture: install did not copy $src_path to $ppath"
  install_hash=$(hash_file "$SRC/$src_path")
  [ "$(manifest_lines "$mpath")" = "$install_hash  $mpath" ] \
    || fail "fixture: install did not record the upstream hash of $mpath"
  printf '\n# local edit\n' >> "$PROJ/$ppath"
  printf '%s %s %s %s\n' "$mpath" "$ppath" "$install_hash" "$(hash_file "$PROJ/$ppath")" >> "$WORK/kept"
done <<< "$KEPT_FIXTURES"
[ -f "$PROJ/.claude/$CLEAN_PATH" ] || fail "fixture: install did not copy $CLEAN_PATH"
[ -n "$(manifest_lines "$CLEAN_PATH")" ] || fail "fixture: install did not record $CLEAN_PATH"

# Source B drops all six.
while read -r src_path _ _; do
  rm -f "$SRC/$src_path"
done <<< "$KEPT_FIXTURES"
rm -f "$SRC/$CLEAN_PATH"
rmdir "$SRC/skills/zz-kept"
commit_src "$SRC" "source B: drop the zz fixtures"

# ----- helpers -----

run_update() {
  local label="$1"
  shift
  UPDATE_OUT=$(cd "$PROJ" && WRIT_REPO="$SRC" bash "$SRC/scripts/update.sh" --platform claude --no-commit "$@" 2>&1) \
    || fail "$label: update exited non-zero: $UPDATE_OUT"
}

# Output lines with leading spaces stripped, for exact-line matching.
output_has_line() {
  printf '%s\n' "$UPDATE_OUT" | sed 's/^ *//' | grep -qxF -- "$1"
}

# The stale and removal lines of the last update, on one line.
stale_lines() {
  { printf '%s\n' "$UPDATE_OUT" | grep -E 'Stale|Removed' || printf '(none)\n'; } \
    | sed 's/^ *//' | paste -sd ';' -
}

bump_upstream() {
  printf '\n<!-- upstream change %s -->\n' "$1" >> "$SRC/$BUMPED_COMMAND"
  commit_src "$SRC" "upstream change $1"
}

# The update must have rewritten the manifest, or the checks after it prove
# nothing: its `# version:` must name the source HEAD.
check_rewritten() {
  local label="$1" version resolved
  version=$(sed -n 's/^# version: //p' "$MANIFEST")
  resolved=$(git -C "$SRC" rev-parse -q --verify "${version}^{commit}" 2>/dev/null || true)
  [ -n "$version" ] && [ "$resolved" = "$(git -C "$SRC" rev-parse HEAD)" ] \
    || fail "$label: update did not rewrite the manifest ('# version: $version' is not the source HEAD): $UPDATE_OUT"
}

# AC-4.1, AC-4.2, AC-4.3 for every file in $WORK/kept.
check_kept() {
  local label="$1" mpath ppath install_hash local_hash lines
  while read -r mpath ppath install_hash local_hash; do
    [ -f "$PROJ/$ppath" ] || fail "$label: update removed the kept $mpath"
    [ "$(hash_file "$PROJ/$ppath")" = "$local_hash" ] || fail "$label: update changed the kept $mpath"
    output_has_line "$WARNING$mpath" \
      || fail "$label: no stale warning for the kept $mpath. Stale lines: $(stale_lines)"
    lines=$(manifest_lines "$mpath")
    [ -n "$lines" ] || fail "$label: the manifest dropped the kept $mpath"
    [ "$lines" = "$install_hash  $mpath" ] \
      || fail "$label: the manifest line for the kept $mpath is not the one install-time baseline: $lines"
  done < "$WORK/kept"
}

# ----- updates 1-3: each rewrites the manifest -----
for run in 1 2 3; do
  label="update $run"
  [ "$run" -eq 1 ] || bump_upstream "run-$run"
  run_update "$label"
  check_rewritten "$label"
  check_kept "$label"
  if [ "$run" -eq 1 ]; then
    output_has_line "🗑  Removed: $CLEAN_PATH" \
      || fail "$label: removal of the unmodified $CLEAN_PATH not reported. Stale lines: $(stale_lines)"
    [ ! -e "$PROJ/.claude/$CLEAN_PATH" ] || fail "$label: the unmodified $CLEAN_PATH was not removed"
    [ -z "$(manifest_lines "$CLEAN_PATH")" ] || fail "$label: the manifest still records the removed $CLEAN_PATH"
  fi
done

# ----- "Already up to date": still warns, manifest untouched -----
cp "$MANIFEST" "$WORK/manifest.before"
run_update "up-to-date run"
grep -qF 'Already up to date' <<< "$UPDATE_OUT" \
  || fail "up-to-date run: update did not report 'Already up to date': $UPDATE_OUT"
cmp -s "$MANIFEST" "$WORK/manifest.before" || fail "up-to-date run: the manifest changed"
check_kept "up-to-date run"

# ----- --dry-run with an upstream change pending: warns, writes nothing -----
bump_upstream dry-run
cp "$MANIFEST" "$WORK/manifest.before"
run_update "dry run" --dry-run
grep -qF 'DRY RUN' <<< "$UPDATE_OUT" || fail "dry run: update did not reach the dry-run report: $UPDATE_OUT"
cmp -s "$MANIFEST" "$WORK/manifest.before" || fail "dry run: the manifest changed"
check_kept "dry run"

# ----- the user deletes one kept file: no warning, its line drops -----
DELETED="commands/zz-kept.md"
rm -f "$PROJ/.claude/$DELETED"
awk -v p="$DELETED" '$1 != p' "$WORK/kept" > "$WORK/kept.next"
mv "$WORK/kept.next" "$WORK/kept"
run_update "after delete"
check_rewritten "after delete"
if printf '%s\n' "$UPDATE_OUT" | grep -E 'Stale|Removed' | grep -qF -- "$DELETED"; then
  fail "after delete: update still names the deleted $DELETED: $(stale_lines)"
fi
[ -z "$(manifest_lines "$DELETED")" ] || fail "after delete: the manifest still records the deleted $DELETED"
[ ! -e "$PROJ/.claude/$DELETED" ] || fail "after delete: update restored the deleted $DELETED"
check_kept "after delete"

# ----- AC-4.5: update-writ.md describes the same manifest -----
DOC="$REPO/commands/update-writ.md"
step7=$(sed -n '/^### Step 7: Regenerate Manifest/,/^### Step 8/p' "$DOC")
[ -n "$step7" ] || fail "commands/update-writ.md: Step 7 not found"
printf '%s\n' "$step7" | grep -A1 -xF '# Tracks installed file baselines for safe overlay updates.' \
  | tail -n 1 | grep -qxF '# baselines: shipped' \
  || fail "commands/update-writ.md Step 7: the manifest template has no '# baselines: shipped' line where update.sh writes it"
for retired in 'fresh baseline for every installed file' 'their current hash becomes the new baseline' \
    'the manifest re-baselines both kinds' 'The manifest still re-baselines'; do
  if grep -qF -- "$retired" "$DOC"; then
    fail "commands/update-writ.md still says '$retired'"
  fi
done

echo "PASS test_update_kept_stale_files"
