#!/usr/bin/env bash
# update.sh keeps the .codex/config.toml.baseline line in .codex/.writ-manifest
# (Story 2 of 2026-10-20-ci-and-update-integrity). write_copy_manifest used to
# truncate the manifest and then look the baseline up in the empty file, so
# every update that rewrote the manifest dropped the line.
#
# AC-2.1: an update that rewrites the manifest keeps one baseline line with the
#         same hash and leaves .codex/config.toml byte-identical.
# AC-2.2: a second rewriting update keeps the line; a --dry-run leaves the
#         manifest byte-identical.
# AC-2.3: with no baseline line in the manifest, update exits 0 and writes none.
# AC-2.4: on the pre-fix update.sh this test fails at AC-2.1 (count 1 -> 0).
#
# Runs the real scripts against temp targets. update.sh clones WRIT_REPO, so
# the source is a committed copy of this working tree. Does `git init`: run
# outside any sandbox.
set -euo pipefail

REPO="$(cd "$(dirname "$0")/../.." && pwd)"
WORK=$(mktemp -d "${TMPDIR:-/tmp}/writ-codex-baseline-test.XXXXXX")
trap 'rm -rf "$WORK"' EXIT

BASELINE_PATH=".codex/config.toml.baseline"
# A shipped command the project never edits. Changing it upstream gives update
# something to apply, so it rewrites the manifest instead of exiting early with
# "Already up to date".
BUMPED_COMMAND="commands/status.md"

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

# Committed source copy of the working tree.
SRC="$WORK/src"
mkdir -p "$SRC"
(cd "$REPO" && tar --exclude=.git --exclude=.cursor --exclude=.claude --exclude=.codex --exclude=.writ \
  --exclude=__pycache__ -cf - .) | (cd "$SRC" && tar -xf -)
mkdir -p "$SRC/.writ/docs"
cp "$REPO"/.writ/docs/*.md "$SRC/.writ/docs/"
git -C "$SRC" init -q -b main
commit_src "$SRC" source
[ -f "$SRC/$BUMPED_COMMAND" ] || fail "fixture: source copy has no $BUMPED_COMMAND"
[ -f "$SRC/codex/config.toml.template" ] || fail "fixture: source copy has no codex/config.toml.template"

PROJ="$WORK/proj"
MANIFEST="$PROJ/.codex/.writ-manifest"
CONFIG="$PROJ/.codex/config.toml"

bump_upstream() {
  printf '\n<!-- upstream change %s -->\n' "$1" >> "$SRC/$BUMPED_COMMAND"
  commit_src "$SRC" "upstream change $1"
}

baseline_count() {
  awk -v p="$BASELINE_PATH" '$2 == p { n++ } END { print n + 0 }' "$MANIFEST"
}

baseline_hash() {
  awk -v p="$BASELINE_PATH" '$2 == p { print $1 }' "$MANIFEST"
}

# Run update.sh in the project. Fails the test on a non-zero exit.
run_update() {
  local label="$1"
  shift
  UPDATE_OUT=$(cd "$PROJ" && WRIT_REPO="$SRC" bash "$SRC/scripts/update.sh" --platform codex --no-commit "$@" 2>&1) \
    || fail "$label: update exited non-zero: $UPDATE_OUT"
}

# The update must have rewritten the manifest; otherwise the baseline checks
# below prove nothing. The manifest's `# version:` must name the source HEAD.
check_rewritten() {
  local label="$1" version resolved
  version=$(sed -n 's/^# version: //p' "$MANIFEST")
  resolved=$(git -C "$SRC" rev-parse -q --verify "${version}^{commit}" 2>/dev/null || true)
  [ -n "$version" ] && [ "$resolved" = "$(git -C "$SRC" rev-parse HEAD)" ] \
    || fail "$label: update did not rewrite the manifest ('# version: $version' is not the source HEAD): $UPDATE_OUT"
}

check_baseline() {
  local label="$1" count
  count=$(baseline_count)
  [ "$count" -eq 1 ] || fail "$label: $BASELINE_PATH line count is $count, want 1"
  [ "$(baseline_hash)" = "$BASELINE_HASH" ] \
    || fail "$label: $BASELINE_PATH hash changed from $BASELINE_HASH to $(baseline_hash)"
  [ "$(hash_file "$CONFIG")" = "$CONFIG_HASH" ] || fail "$label: .codex/config.toml changed"
}

# ----- Install Codex; the manifest records the seed hash once -----
mkdir -p "$PROJ"
out=$(cd "$PROJ" && bash "$SRC/scripts/install.sh" --platform codex --no-commit 2>&1) \
  || fail "install exited non-zero: $out"
[ -f "$CONFIG" ] || fail "install did not seed .codex/config.toml"
count=$(baseline_count)
[ "$count" -eq 1 ] || fail "install: $BASELINE_PATH line count is $count, want 1"
BASELINE_HASH=$(baseline_hash)
[ "$BASELINE_HASH" = "$(hash_file "$SRC/codex/config.toml.template")" ] \
  || fail "install: $BASELINE_PATH is not the template hash"
# A user edit to the install-once config. The baseline must stay the seed hash,
# not a hash of the edited file.
printf '\n# local edit\n' >> "$CONFIG"
CONFIG_HASH=$(hash_file "$CONFIG")

# ----- AC-2.1: a manifest-rewriting update keeps the baseline -----
bump_upstream 1
run_update "first update"
check_rewritten "first update"
check_baseline "first update"

# ----- AC-2.2: a second rewriting update keeps it; a dry run writes nothing -----
bump_upstream 2
run_update "second update"
check_rewritten "second update"
check_baseline "second update"

bump_upstream 3
cp "$MANIFEST" "$WORK/manifest.before-dry-run"
run_update "dry run" --dry-run
printf '%s' "$UPDATE_OUT" | grep -qF 'DRY RUN' \
  || fail "dry run: update exited before the dry-run step: $UPDATE_OUT"
cmp -s "$MANIFEST" "$WORK/manifest.before-dry-run" || fail "dry run: manifest changed"
check_baseline "dry run"

# ----- AC-2.3: no baseline line in the manifest -> exit 0, none written -----
awk -v p="$BASELINE_PATH" '$2 != p' "$MANIFEST" > "$WORK/manifest.no-baseline"
cp "$WORK/manifest.no-baseline" "$MANIFEST"
[ "$(baseline_count)" -eq 0 ] || fail "fixture: could not remove the $BASELINE_PATH line"
bump_upstream 4
run_update "no-baseline update"
check_rewritten "no-baseline update"
count=$(baseline_count)
[ "$count" -eq 0 ] || fail "no-baseline update: $BASELINE_PATH line count is $count, want 0"
[ "$(hash_file "$CONFIG")" = "$CONFIG_HASH" ] || fail "no-baseline update: .codex/config.toml changed"

echo "PASS test_update_codex_config_baseline"
