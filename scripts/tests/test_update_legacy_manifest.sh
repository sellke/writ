#!/usr/bin/env bash
# update.sh repairs a manifest written by a pre-fix Writ release before it
# trusts any baseline in it, and removes stale files from the folder they live
# in (Story 5 of 2026-10-20-ci-and-update-integrity).
#
# AC-5.1: a legacy manifest (no `# baselines: shipped`) whose version resolves
#         and that records three user files with their local hashes. The files
#         stay byte-identical, no stale or removal line names them, and the
#         rewritten manifest has the header and no line for them. A second
#         update also leaves them alone.
# AC-5.2: in the same project, the unmodified commands/zz-retired.md (shipped
#         at the recorded version, dropped since) is removed with a Removed
#         line. The customized commands/status.md, recorded at its local hash,
#         is preserved byte-identical, and its baseline becomes the upstream
#         hash at the recorded version.
# AC-5.3: a legacy manifest whose version is unknown, missing, or absent
#         upstream: one notice naming the reason, nothing removed, no file
#         changed (so none that differs from upstream is overwritten), the
#         Codex config baseline line kept, and a manifest with the header. On
#         Cursor the customized rules/writ.mdc and system-instructions.md are
#         preserved on that run and on the next one. With
#         WRIT_REPO=file://... (a shallow clone) and a version older than the
#         tip, AC-5.1 and AC-5.2 hold. update-writ.md Step 3 describes the
#         legacy handling.
# AC-5.4: on Codex, an unmodified stale skill is removed from .agents/skills
#         with `🗑  Removed: skills/zz-old/SKILL.md`. After every update here,
#         each path printed as Removed is absent from disk, and a stale file
#         rm cannot remove gets no Removed line and is tried again next run.
# AC-5.5: on the pre-fix update.sh this test fails at case A: the user file
#         .writ/docs/tech-stack.md is removed.
#
# Runs the real scripts against temp targets. update.sh clones WRIT_REPO, so
# the source is a committed copy of this working tree. Does `git init`: run
# outside any sandbox.
set -euo pipefail

REPO="$(cd "$(dirname "$0")/../.." && pwd)"
WORK=$(mktemp -d "${TMPDIR:-/tmp}/writ-legacy-manifest-test.XXXXXX")
# Case D makes one skill folder read-only; restore write access so rm works.
trap 'chmod -R u+w "$WORK" 2>/dev/null || true; rm -rf "$WORK"' EXIT

NOTICE_START='⚠️  Manifest predates shipped-only baselines and '
NOTICE_END='; files that differ from upstream are preserved this run.'
# User files in Writ's folders, as manifest paths. Upstream never ships them.
USER_PATHS=".writ/docs/tech-stack.md scripts/deploy.sh commands/my-own.md"
# Shipped by source A only. Projects never edit them.
RETIRED="commands/zz-retired.md"
OLD_SKILL="skills/zz-old/SKILL.md"
LOCKED_SKILL="skills/zz-locked/SKILL.md"
# Source B changes this shipped command; no project edits it. A resolved
# legacy run updates it; a fallback run preserves it (no baseline).
BUMPED_COMMAND="commands/create-issue.md"
# Source B adds this command, so even a fallback run has a file to apply and
# rewrites the manifest instead of exiting early with "Already up to date".
NEW_COMMAND="commands/zz-new.md"
# Source C adds this one, for the same reason.
NEW_COMMAND_C="commands/zz-new-c.md"
# Cursor files copied whole, as manifest paths.
CURSOR_UNITS="rules/writ.mdc system-instructions.md"

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

# ----- source A: the working tree plus the zz-* fixtures -----
SRC="$WORK/src"
mkdir -p "$SRC"
(cd "$REPO" && tar --exclude=.git --exclude=.cursor --exclude=.claude --exclude=.codex --exclude=.writ \
  --exclude='.writ-lanes-*' --exclude=__pycache__ --exclude=.venv --exclude=.pytest_cache -cf - .) \
  | (cd "$SRC" && tar -xf -)
mkdir -p "$SRC/.writ/docs"
cp "$REPO"/.writ/docs/*.md "$SRC/.writ/docs/"
for f in "$BUMPED_COMMAND" commands/status.md cursor/writ.mdc system-instructions.md; do
  [ -f "$SRC/$f" ] || fail "fixture: source copy has no $f"
done
for p in $USER_PATHS "$RETIRED" "$OLD_SKILL" "$LOCKED_SKILL" "$NEW_COMMAND" "$NEW_COMMAND_C"; do
  [ ! -e "$SRC/$p" ] || fail "fixture: $p already exists upstream"
done
for p in "$RETIRED" "$OLD_SKILL" "$LOCKED_SKILL"; do
  mkdir -p "$(dirname "$SRC/$p")"
  printf '# %s fixture\n\nShipped by source A only.\n' "$p" > "$SRC/$p"
done
git -C "$SRC" init -q -b main
commit_src "$SRC" "source A"
# install.sh records this as `# version:`.
VERSION_A=$(git -C "$SRC" log -1 --format=%h)
STATUS_A_HASH=$(hash_file "$SRC/commands/status.md")
RULE_A_HASH=$(hash_file "$SRC/cursor/writ.mdc")

# ----- helpers -----

manifest_of() {
  printf '%s/.%s/.writ-manifest\n' "$1" "$2"
}

# Project path of a manifest path, as update.sh resolves it.
local_path() {
  local platform="$1" mpath="$2" skills_dir
  case "$platform" in
    codex) skills_dir=".agents/skills" ;;
    *)     skills_dir=".$platform/skills" ;;
  esac
  case "$mpath" in
    CLAUDE.md) printf 'CLAUDE.md\n' ;;
    skills/*) printf '%s/%s\n' "$skills_dir" "${mpath#skills/}" ;;
    scripts/*|.writ/*) printf '%s\n' "$mpath" ;;
    *) printf '.%s/%s\n' "$platform" "$mpath" ;;
  esac
}

manifest_hash() {
  awk -v p="$2" '!/^#/ && $2 == p { print $1; exit }' "$1"
}

run_install() {
  local proj="$1" platform="$2" out
  mkdir -p "$proj"
  out=$(cd "$proj" && bash "$SRC/scripts/install.sh" --platform "$platform" --no-commit 2>&1) \
    || fail "install into $proj exited non-zero: $out"
}

# A copy of the source A install for the platform (see below).
new_project() {
  cp -R "$WORK/base-$2" "$1"
}

run_update() {
  local label="$1" proj="$2" platform="$3" repo="$4"
  UPDATE_OUT=$(cd "$proj" && WRIT_REPO="$repo" bash "$SRC/scripts/update.sh" --platform "$platform" --no-commit 2>&1) \
    || fail "$label: update exited non-zero: $UPDATE_OUT"
}

# Turn a fixed install's manifest into one a pre-fix script wrote: no
# `# baselines: shipped` line, and `# version:` set to $2 (no line when empty).
make_legacy() {
  local manifest="$1" version="$2"
  awk -v v="$version" '
    $0 == "# baselines: shipped" { next }
    /^# version:/ { if (v != "") print "# version: " v; next }
    { print }' "$manifest" > "$WORK/legacy.tmp"
  cat "$WORK/legacy.tmp" > "$manifest"
  if grep -q '^# baselines:' "$manifest"; then
    fail "fixture: could not remove the baselines header from $manifest"
  fi
}

# Replace the manifest line for one path with "<hash>  <path>".
set_baseline() {
  local manifest="$1" mpath="$2" hash="$3"
  awk -v p="$mpath" '$2 != p' "$manifest" > "$WORK/baseline.tmp"
  printf '%s  %s\n' "$hash" "$mpath" >> "$WORK/baseline.tmp"
  cat "$WORK/baseline.tmp" > "$manifest"
}

# Write the user files and record each at its local hash, as the pre-fix
# scripts did. $proj.user-hashes keeps "<hash> <manifest path>" per file.
add_user_files() {
  local proj="$1" platform="$2" manifest mpath path
  manifest=$(manifest_of "$proj" "$platform")
  : > "$proj.user-hashes"
  for mpath in $USER_PATHS; do
    path=$(local_path "$platform" "$mpath")
    mkdir -p "$(dirname "$proj/$path")"
    printf '# %s\n\nWritten by the project, not shipped by Writ.\n' "$mpath" > "$proj/$path"
    set_baseline "$manifest" "$mpath" "$(hash_file "$proj/$path")"
    printf '%s %s\n' "$(hash_file "$proj/$path")" "$mpath" >> "$proj.user-hashes"
  done
}

# Edit commands/status.md and re-baseline it to its local hash, as the pre-fix
# scripts did. Prints the local hash.
customize_status() {
  local proj="$1" platform="$2" file
  file="$proj/.$platform/commands/status.md"
  printf '\n<!-- local edit -->\n' >> "$file"
  set_baseline "$(manifest_of "$proj" "$platform")" commands/status.md "$(hash_file "$file")"
  hash_file "$file"
}

# The update must have rewritten the manifest, or the checks after it prove
# nothing: its `# version:` must name the source HEAD.
check_rewritten() {
  local label="$1" manifest="$2" version resolved
  version=$(sed -n 's/^# version: //p' "$manifest")
  resolved=$(git -C "$SRC" rev-parse -q --verify "${version}^{commit}" 2>/dev/null || true)
  [ -n "$version" ] && [ "$resolved" = "$(git -C "$SRC" rev-parse HEAD)" ] \
    || fail "$label: update did not rewrite the manifest ('# version: $version' is not the source HEAD): $UPDATE_OUT"
}

check_header() {
  grep -qx '# baselines: shipped' "$2" || fail "$1: manifest has no '# baselines: shipped' line"
}

# The stale and removal lines of the last update, on one line.
stale_lines() {
  { printf '%s\n' "$UPDATE_OUT" | grep -E 'Stale|Removed|🗑' || printf '(none)\n'; } \
    | sed 's/^ *//' | paste -sd ';' -
}

output_has_line() {
  printf '%s\n' "$UPDATE_OUT" | sed 's/^ *//' | grep -qxF -- "$1"
}

# AC-5.1: every user file is byte-identical, unnamed, and unrecorded.
check_user_files() {
  local label="$1" proj="$2" platform="$3" manifest want mpath path lines
  manifest=$(manifest_of "$proj" "$platform")
  lines=$(stale_lines)
  while read -r want mpath; do
    path=$(local_path "$platform" "$mpath")
    [ -f "$proj/$path" ] || fail "$label: user file $mpath was removed. Stale lines: $lines"
    [ "$(hash_file "$proj/$path")" = "$want" ] || fail "$label: user file $mpath was changed"
    if grep -qF -- "$mpath" <<< "$lines"; then
      fail "$label: update named user file $mpath in a stale or removal line: $lines"
    fi
    if awk -v p="$mpath" '!/^#/ && $2 == p { found = 1 } END { exit !found }' "$manifest"; then
      fail "$label: manifest records user file $mpath"
    fi
  done < "$proj.user-hashes"
}

# AC-5.4: each path printed as Removed is gone from disk.
check_removed_absent() {
  local label="$1" proj="$2" platform="$3" mpath path
  while IFS= read -r mpath; do
    [ -n "$mpath" ] || continue
    path=$(local_path "$platform" "$mpath")
    if [ -e "$proj/$path" ]; then
      fail "$label: printed '🗑  Removed: $mpath' but $path is still on disk"
    fi
  done <<< "$(printf '%s\n' "$UPDATE_OUT" | sed -n 's/^ *🗑  Removed: //p')"
}

notice_count() {
  printf '%s\n' "$UPDATE_OUT" | grep -cF 'Manifest predates shipped-only baselines' || true
}

check_no_notice() {
  [ "$(notice_count)" -eq 0 ] || fail "$1: printed the legacy fallback notice: $UPDATE_OUT"
}

# Every file in the project except the manifest, as sorted "<hash>  ./<path>".
snapshot() {
  if command -v shasum &>/dev/null; then
    (cd "$1" && find . -type f ! -name .writ-manifest -exec shasum -a 256 {} +)
  else
    (cd "$1" && find . -type f ! -name .writ-manifest -exec sha256sum {} +)
  fi | LC_ALL=C sort
}

# ----- install from source A once per platform, then age each copy's manifest -----
run_install "$WORK/base-claude" claude
run_install "$WORK/base-codex" codex
run_install "$WORK/base-cursor" cursor

# Cases A (plain-path clone) and C (shallow file:// clone): legacy manifests
# whose version resolves.
PA="$WORK/claude-resolved"
PC="$WORK/claude-shallow"
for proj in "$PA" "$PC"; do
  new_project "$proj" claude
  make_legacy "$(manifest_of "$proj" claude)" "$VERSION_A"
  add_user_files "$proj" claude
done
STATUS_LOCAL_A=$(customize_status "$PA" claude)
STATUS_LOCAL_C=$(customize_status "$PC" claude)

# Case B: legacy manifests whose version does not resolve. "-" stands for a
# manifest with no `# version:` line.
B_VERSIONS="unknown - 0000000"
for v in $B_VERSIONS; do
  proj="$WORK/claude-unresolved-$v"
  new_project "$proj" claude
  if [ "$v" = "-" ]; then
    make_legacy "$(manifest_of "$proj" claude)" ""
  else
    make_legacy "$(manifest_of "$proj" claude)" "$v"
  fi
  add_user_files "$proj" claude
  customize_status "$proj" claude > /dev/null
done

# Case B on Codex: an edited install-once config and its baseline line.
PX="$WORK/codex-unresolved"
MX=$(manifest_of "$PX" codex)
new_project "$PX" codex
make_legacy "$MX" unknown
add_user_files "$PX" codex
CONFIG_BASELINE=$(manifest_hash "$MX" .codex/config.toml.baseline)
[ -n "$CONFIG_BASELINE" ] || fail "fixture: codex install recorded no .codex/config.toml.baseline line"
printf '\n# local edit\n' >> "$PX/.codex/config.toml"

# Case D: a fixed Codex install. zz-old is removed; zz-locked sits in a
# read-only folder, so rm fails for any user but root.
PD="$WORK/codex-skills"
MD=$(manifest_of "$PD" codex)
new_project "$PD" codex
for p in "$OLD_SKILL" "$LOCKED_SKILL"; do
  [ -f "$PD/$(local_path codex "$p")" ] || fail "fixture: codex install did not copy $p to .agents/skills"
done
chmod 555 "$PD/$(dirname "$(local_path codex "$LOCKED_SKILL")")"

# Case B on Cursor: the rule and the system instructions are customized.
# $proj.unit-hashes keeps "<hash> <manifest path>" for each.
for v in unknown 0000000; do
  proj="$WORK/cursor-unresolved-$v"
  new_project "$proj" cursor
  make_legacy "$(manifest_of "$proj" cursor)" "$v"
  : > "$proj.unit-hashes"
  for u in $CURSOR_UNITS; do
    printf '\n<!-- local edit -->\n' >> "$proj/$(local_path cursor "$u")"
    printf '%s %s\n' "$(hash_file "$proj/$(local_path cursor "$u")")" "$u" >> "$proj.unit-hashes"
  done
done

# Cursor, resolved: the rule is customized and re-baselined to its local
# hash, as the pre-fix scripts did.
PR="$WORK/cursor-resolved"
MR=$(manifest_of "$PR" cursor)
new_project "$PR" cursor
make_legacy "$MR" "$VERSION_A"
printf '\n<!-- local edit -->\n' >> "$PR/.cursor/rules/writ.mdc"
RULE_LOCAL_R=$(hash_file "$PR/.cursor/rules/writ.mdc")
set_baseline "$MR" rules/writ.mdc "$RULE_LOCAL_R"

# ----- source B: drop the zz-* fixtures, change three files, add one -----
rm -f "$SRC/$RETIRED" "$SRC/$OLD_SKILL" "$SRC/$LOCKED_SKILL"
rmdir "$SRC/skills/zz-old" "$SRC/skills/zz-locked"
printf '\n<!-- upstream change B -->\n' >> "$SRC/commands/status.md"
printf '\n<!-- upstream change B -->\n' >> "$SRC/$BUMPED_COMMAND"
printf '\n<!-- upstream change B -->\n' >> "$SRC/cursor/writ.mdc"
printf '# zz-new fixture\n\nAdded by source B.\n' > "$SRC/$NEW_COMMAND"
commit_src "$SRC" "source B"

# Case C needs history the clone lacks: a --depth 1 clone of file://$SRC is
# shallow and does not hold source A.
git clone -q --depth 1 "file://$SRC" "$WORK/shallow-probe" 2>/dev/null
[ "$(git -C "$WORK/shallow-probe" rev-parse --is-shallow-repository)" = "true" ] \
  || fail "fixture: a --depth 1 clone of file://$SRC is not shallow"
if git -C "$WORK/shallow-probe" rev-parse -q --verify "${VERSION_A}^{commit}" >/dev/null 2>&1; then
  fail "fixture: the shallow clone already holds $VERSION_A"
fi
rm -rf "$WORK/shallow-probe"

# AC-5.1 / AC-5.2 for the first update from a resolved legacy manifest.
check_resolved_update() {
  local label="$1" proj="$2" status_local="$3" manifest
  manifest=$(manifest_of "$proj" claude)
  check_rewritten "$label" "$manifest"
  check_user_files "$label" "$proj" claude
  check_header "$label" "$manifest"
  check_no_notice "$label"
  [ "$(hash_file "$proj/.claude/commands/status.md")" = "$status_local" ] \
    || fail "$label: customized commands/status.md was overwritten"
  output_has_line "⚡ Preserved: commands/status.md (local modifications)" \
    || fail "$label: update did not report commands/status.md as preserved: $UPDATE_OUT"
  [ "$(manifest_hash "$manifest" commands/status.md)" = "$STATUS_A_HASH" ] \
    || fail "$label: commands/status.md baseline is '$(manifest_hash "$manifest" commands/status.md)', want its source A hash $STATUS_A_HASH"
  output_has_line "🗑  Removed: $RETIRED" \
    || fail "$label: removal of the unmodified $RETIRED not reported. Stale lines: $(stale_lines)"
  [ ! -e "$proj/.claude/$RETIRED" ] || fail "$label: the unmodified $RETIRED was not removed"
  [ -z "$(manifest_hash "$manifest" "$RETIRED")" ] || fail "$label: the manifest still records the removed $RETIRED"
  # Only a baseline rebuilt from source A lets update.sh replace this
  # unmodified, upstream-changed file. The fallback would preserve it.
  cmp -s "$proj/.claude/$BUMPED_COMMAND" "$SRC/$BUMPED_COMMAND" \
    || fail "$label: the unmodified $BUMPED_COMMAND was not updated to upstream"
  check_removed_absent "$label" "$proj" claude
}

# ----- case A: resolved, plain-path clone (full history) -----
run_update "A update 1" "$PA" claude "$SRC"
check_resolved_update "A update 1" "$PA" "$STATUS_LOCAL_A"

# ----- case C: resolved after one --unshallow of a file:// clone -----
# A dry run repairs the baselines the same way and writes nothing.
label="C dry run"
cp "$(manifest_of "$PC" claude)" "$WORK/manifest.before"
UPDATE_OUT=$(cd "$PC" && WRIT_REPO="file://$SRC" bash "$SRC/scripts/update.sh" --platform claude --no-commit --dry-run 2>&1) \
  || fail "$label: update exited non-zero: $UPDATE_OUT"
grep -qF 'DRY RUN' <<< "$UPDATE_OUT" || fail "$label: update did not reach the dry-run report: $UPDATE_OUT"
cmp -s "$(manifest_of "$PC" claude)" "$WORK/manifest.before" || fail "$label: the manifest changed"
check_no_notice "$label"
output_has_line "🗑  $RETIRED" || fail "$label: $RETIRED not listed as stale. Stale lines: $(stale_lines)"
# The manifest is still the legacy one, so it still records the user files;
# only check that the dry run would leave them alone.
while read -r _ mpath; do
  [ -f "$PC/$(local_path claude "$mpath")" ] || fail "$label: user file $mpath was removed"
  if grep -qF -- "$mpath" <<< "$(stale_lines)"; then
    fail "$label: dry run lists user file $mpath as stale: $(stale_lines)"
  fi
done < "$PC.user-hashes"
run_update "C update 1" "$PC" claude "file://$SRC"
check_resolved_update "C update 1" "$PC" "$STATUS_LOCAL_C"

# ----- case B: unresolved versions fall back to no-manifest behavior -----
for v in $B_VERSIONS; do
  proj="$WORK/claude-unresolved-$v"
  label="B update (version $v)"
  manifest=$(manifest_of "$proj" claude)
  repo="$SRC"
  case "$v" in
    0000000)
      reason="version 0000000 was not found upstream"
      # A shallow clone: the fetch runs, and the version is still missing.
      repo="file://$SRC"
      ;;
    *) reason="its version is unknown" ;;
  esac
  snapshot "$proj" > "$WORK/before"
  run_update "$label" "$proj" claude "$repo"
  check_rewritten "$label" "$manifest"
  check_header "$label" "$manifest"
  [ "$(notice_count)" -eq 1 ] || fail "$label: want one legacy notice, got $(notice_count): $UPDATE_OUT"
  output_has_line "$NOTICE_START$reason$NOTICE_END" \
    || fail "$label: the legacy notice does not read '$NOTICE_START$reason$NOTICE_END': $UPDATE_OUT"
  if grep -qF 'No manifest found' <<< "$UPDATE_OUT"; then
    fail "$label: printed the no-manifest notice for a legacy manifest: $UPDATE_OUT"
  fi
  if grep -qF 'Removed' <<< "$UPDATE_OUT"; then
    fail "$label: removed a file. Stale lines: $(stale_lines)"
  fi
  snapshot "$proj" > "$WORK/after"
  changed=$(LC_ALL=C comm -23 "$WORK/before" "$WORK/after")
  [ -z "$changed" ] || fail "$label: update changed or removed files (old hashes shown): $changed"
  check_user_files "$label" "$proj" claude
  [ -z "$(manifest_hash "$manifest" commands/status.md)" ] \
    || fail "$label: the manifest records a baseline for the preserved commands/status.md"
done

label="B update (codex, version unknown)"
snapshot "$PX" > "$WORK/before"
run_update "$label" "$PX" codex "$SRC"
check_rewritten "$label" "$MX"
check_header "$label" "$MX"
[ "$(notice_count)" -eq 1 ] || fail "$label: want one legacy notice, got $(notice_count): $UPDATE_OUT"
output_has_line "${NOTICE_START}its version is unknown$NOTICE_END" \
  || fail "$label: the legacy notice does not name the unknown version: $UPDATE_OUT"
if grep -qF 'Removed' <<< "$UPDATE_OUT"; then
  fail "$label: removed a file. Stale lines: $(stale_lines)"
fi
snapshot "$PX" > "$WORK/after"
changed=$(LC_ALL=C comm -23 "$WORK/before" "$WORK/after")
[ -z "$changed" ] || fail "$label: update changed or removed files (old hashes shown): $changed"
check_user_files "$label" "$PX" codex
[ "$(awk '$2 == ".codex/config.toml.baseline"' "$MX")" = "$CONFIG_BASELINE  .codex/config.toml.baseline" ] \
  || fail "$label: the .codex/config.toml.baseline line is not the one recorded at install: $(grep -F config.toml.baseline "$MX" || echo none)"

# The customized Cursor files of a $proj.unit-hashes project are
# byte-identical, reported as preserved with no baseline, and unrecorded.
check_cursor_units() {
  local label="$1" proj="$2" manifest want u
  manifest=$(manifest_of "$proj" cursor)
  while read -r want u; do
    [ "$(hash_file "$proj/$(local_path cursor "$u")")" = "$want" ] \
      || fail "$label: customized $u was overwritten"
    output_has_line "⚡ Preserved: $u (no baseline, assuming modified)" \
      || fail "$label: update did not report $u as preserved with no baseline: $UPDATE_OUT"
    [ -z "$(manifest_hash "$manifest" "$u")" ] || fail "$label: the manifest records a baseline for the preserved $u"
  done < "$proj.unit-hashes"
}

for v in unknown 0000000; do
  proj="$WORK/cursor-unresolved-$v"
  label="B update (cursor, version $v)"
  manifest=$(manifest_of "$proj" cursor)
  case "$v" in
    0000000) reason="version 0000000 was not found upstream" ;;
    *) reason="its version is unknown" ;;
  esac
  snapshot "$proj" > "$WORK/before"
  run_update "$label" "$proj" cursor "$SRC"
  check_rewritten "$label" "$manifest"
  check_header "$label" "$manifest"
  [ "$(notice_count)" -eq 1 ] || fail "$label: want one legacy notice, got $(notice_count): $UPDATE_OUT"
  output_has_line "$NOTICE_START$reason$NOTICE_END" \
    || fail "$label: the legacy notice does not read '$NOTICE_START$reason$NOTICE_END': $UPDATE_OUT"
  check_cursor_units "$label" "$proj"
  if grep -qF 'Removed' <<< "$UPDATE_OUT"; then
    fail "$label: removed a file. Stale lines: $(stale_lines)"
  fi
  snapshot "$proj" > "$WORK/after"
  changed=$(LC_ALL=C comm -23 "$WORK/before" "$WORK/after")
  [ -z "$changed" ] || fail "$label: update changed or removed files (old hashes shown): $changed"
done

# ----- Cursor, resolved: the re-baselined rule is preserved -----
label="Cursor resolved update"
run_update "$label" "$PR" cursor "$SRC"
check_rewritten "$label" "$MR"
check_header "$label" "$MR"
check_no_notice "$label"
[ "$(hash_file "$PR/.cursor/rules/writ.mdc")" = "$RULE_LOCAL_R" ] \
  || fail "$label: customized rules/writ.mdc was overwritten"
output_has_line "⚡ Preserved: rules/writ.mdc (local modifications)" \
  || fail "$label: update did not report rules/writ.mdc as preserved: $UPDATE_OUT"
[ "$(manifest_hash "$MR" rules/writ.mdc)" = "$RULE_A_HASH" ] \
  || fail "$label: rules/writ.mdc baseline is '$(manifest_hash "$MR" rules/writ.mdc)', want its source A hash $RULE_A_HASH"
output_has_line "🗑  Removed: $RETIRED" \
  || fail "$label: removal of the unmodified $RETIRED not reported. Stale lines: $(stale_lines)"
check_removed_absent "$label" "$PR" cursor

# ----- case D: Codex stale skills leave .agents/skills -----
label="D update 1"
run_update "$label" "$PD" codex "$SRC"
check_rewritten "$label" "$MD"
check_removed_absent "$label" "$PD" codex
output_has_line "🗑  Removed: $OLD_SKILL" \
  || fail "$label: removal of the unmodified $OLD_SKILL not reported. Stale lines: $(stale_lines)"
[ ! -e "$PD/$(local_path codex "$OLD_SKILL")" ] || fail "$label: $OLD_SKILL is still in .agents/skills"
LOCKED_LOCAL="$PD/$(local_path codex "$LOCKED_SKILL")"
if [ -e "$LOCKED_LOCAL" ]; then
  # rm failed: no Removed line (checked above), and the manifest keeps the
  # path so the next update removes it.
  [ -n "$(manifest_hash "$MD" "$LOCKED_SKILL")" ] \
    || fail "$label: the manifest dropped $LOCKED_SKILL, which rm could not remove"
  chmod 755 "$(dirname "$LOCKED_LOCAL")"
  label="D update 2"
  run_update "$label" "$PD" codex "$SRC"
  check_removed_absent "$label" "$PD" codex
  output_has_line "🗑  Removed: $LOCKED_SKILL" \
    || fail "$label: removal of $LOCKED_SKILL not reported once rm could remove it. Stale lines: $(stale_lines)"
  [ -z "$(manifest_hash "$MD" "$LOCKED_SKILL")" ] || fail "$label: the manifest still records the removed $LOCKED_SKILL"
else
  # Running as root: rm ignores the read-only folder.
  output_has_line "🗑  Removed: $LOCKED_SKILL" \
    || fail "$label: $LOCKED_SKILL is gone but no Removed line names it"
fi

# ----- AC-5.1: a second rewriting update leaves the user files alone -----
printf '\n<!-- upstream change C -->\n' >> "$SRC/$BUMPED_COMMAND"
printf '# zz-new-c fixture\n\nAdded by source C.\n' > "$SRC/$NEW_COMMAND_C"
commit_src "$SRC" "source C"
for c in A C; do
  if [ "$c" = A ]; then
    proj="$PA"; repo="$SRC"; status_local="$STATUS_LOCAL_A"
  else
    proj="$PC"; repo="file://$SRC"; status_local="$STATUS_LOCAL_C"
  fi
  label="$c update 2"
  manifest=$(manifest_of "$proj" claude)
  run_update "$label" "$proj" claude "$repo"
  check_rewritten "$label" "$manifest"
  check_user_files "$label" "$proj" claude
  check_header "$label" "$manifest"
  [ "$(hash_file "$proj/.claude/commands/status.md")" = "$status_local" ] \
    || fail "$label: customized commands/status.md was overwritten"
  [ "$(manifest_hash "$manifest" commands/status.md)" = "$STATUS_A_HASH" ] \
    || fail "$label: commands/status.md baseline changed from $STATUS_A_HASH to '$(manifest_hash "$manifest" commands/status.md)'"
  check_removed_absent "$label" "$proj" claude
done

# ----- AC-5.3: on Cursor, the next update (a header manifest with no line
# for the customized files) preserves them again -----
for v in unknown 0000000; do
  proj="$WORK/cursor-unresolved-$v"
  label="Cursor update 2 (was version $v)"
  manifest=$(manifest_of "$proj" cursor)
  run_update "$label" "$proj" cursor "$SRC"
  check_rewritten "$label" "$manifest"
  check_header "$label" "$manifest"
  check_no_notice "$label"
  check_cursor_units "$label" "$proj"
  if grep -qF 'Removed' <<< "$UPDATE_OUT"; then
    fail "$label: removed a file. Stale lines: $(stale_lines)"
  fi
done

# ----- AC-5.3: update-writ.md Step 3 names the legacy handling -----
step3=$(sed -n '/^### Step 3: Three-Way Scan/,/^### Step 4/p' "$REPO/commands/update-writ.md")
[ -n "$step3" ] || fail "commands/update-writ.md: Step 3 not found"
printf '%s\n' "$step3" | grep -F '`# baselines: shipped`' | grep -qF '`# version:`' \
  || fail "commands/update-writ.md Step 3 has no sentence on manifests without \`# baselines: shipped\` and their \`# version:\`"

echo "PASS test_update_legacy_manifest"
