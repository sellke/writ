#!/usr/bin/env bash
# Upgrade paths for 2026-10-20-harness-cuts.
#
# Story 1: the lean command siblings (commands/*.lean.md) are deleted from the
# source, so install ships none, and update treats an old installed copy as
# stale because upstream no longer has it. An unmodified copy is removed; a
# locally modified copy is kept and warned about on every run.
#
# Story 4: scripts/recommend-state.py and
# .writ/docs/recommended-delivery-state-format.md stay in the source but are
# dev-only. The ship filters reject them, so install ships neither on any
# platform, and update treats an old installed copy as stale even though
# upstream still has it. No shipped file names the script by path.
#
# Runs the real scripts against temp targets. update.sh clones WRIT_REPO, so
# the source is a committed copy of this working tree. Does `git init`: run
# outside any sandbox. Never point it at the Writ repo itself.
set -euo pipefail

REPO="$(cd "$(dirname "$0")/../.." && pwd)"
WORK=$(mktemp -d "${TMPDIR:-/tmp}/writ-harness-cuts-test.XXXXXX")
trap 'rm -rf "$WORK"' EXIT

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

# One line per file under $1: "<sha256> <relative path>", sorted. Two equal
# digests mean nothing on disk changed.
tree_digest() {
  local dir="$1" f
  (cd "$dir" && find . -type f | LC_ALL=C sort | while IFS= read -r f; do
    printf '%s %s\n' "$(hash_file "$f")" "$f"
  done)
}

script_filter() {
  sed -n '/^is_shippable_script() {/,/^}/p' "$1"
}

doc_filter() {
  sed -n '/^is_shippable_writ_doc() {/,/^}/p' "$1"
}

# The two dev-only staging files, as project paths and manifest paths.
HELPER=scripts/recommend-state.py
STATE_DOC=.writ/docs/recommended-delivery-state-format.md
STAGING="$HELPER $STATE_DOC"

# ----- 2026-10-20-harness-cuts AC-4.1: both ship filters reject the staging files -----
for s in install update unlink; do
  body=$(script_filter "$REPO/scripts/$s.sh")
  [ -n "$body" ] || fail "$s.sh: cannot load is_shippable_script"
  if bash -c "$body"$'\n''is_shippable_script "$1"' _ recommend-state.py; then
    fail "$s.sh: is_shippable_script accepts recommend-state.py"
  fi
  bash -c "$body"$'\n''is_shippable_script "$1"' _ spec-status.py \
    || fail "$s.sh: is_shippable_script rejects spec-status.py"
done
[ "$(script_filter "$REPO/scripts/install.sh")" = "$(script_filter "$REPO/scripts/update.sh")" ] \
  || fail "is_shippable_script differs between install.sh and update.sh"
[ "$(script_filter "$REPO/scripts/install.sh")" = "$(script_filter "$REPO/scripts/unlink.sh")" ] \
  || fail "is_shippable_script differs between install.sh and unlink.sh"
doc_names=()
for f in "$REPO"/.writ/docs/*.md; do
  doc_names+=("$(basename "$f")")
done
for s in install update; do
  body=$(doc_filter "$REPO/scripts/$s.sh")
  [ -n "$body" ] || fail "$s.sh: cannot load is_shippable_writ_doc"
  # Every source doc goes through the filter; only the state doc may be rejected.
  rejected=$(bash -c "$body"$'\n''for n in "$@"; do is_shippable_writ_doc "$n" || echo "$n"; done; true' \
    _ "${doc_names[@]}")
  [ "$rejected" = "recommended-delivery-state-format.md" ] \
    || fail "$s.sh: is_shippable_writ_doc must reject exactly recommended-delivery-state-format.md, rejected: [$rejected]"
done
[ "$(doc_filter "$REPO/scripts/install.sh")" = "$(doc_filter "$REPO/scripts/update.sh")" ] \
  || fail "is_shippable_writ_doc differs between install.sh and update.sh"
for rel in $STAGING; do
  [ -f "$REPO/$rel" ] || fail "source $rel is gone; eval.sh still runs it"
done

# ----- 2026-10-20-harness-cuts AC-4.4: no shipped file names the script by path -----
hits=$(cd "$REPO" && grep -rnF -e 'scripts/recommend-state.py' -e 'recommend-state.py record-' \
  commands agents skills adapters SKILL.md .writ/docs 2>/dev/null \
  | grep -vF ".writ/docs/recommended-delivery-state-format.md:" || true)
[ -z "$hits" ] || fail "shipped source names recommend-state.py by path: $hits"
# The shipped scripts too: no top-level script the ship filter accepts names
# either staging file, by path or by bare name.
shipped_names=$(cd "$REPO/scripts" && bash -c "$(script_filter "$REPO/scripts/install.sh")"$'\n'\
'for n in "$@"; do [ -f "$n" ] && is_shippable_script "$n" && echo "$n"; done; true' _ *)
[ -n "$shipped_names" ] || fail "cannot list the shipped scripts"
hits=""
for name in $shipped_names; do
  h=$(cd "$REPO" && grep -nHF -e 'recommend-state.py' -e 'recommended-delivery-state-format.md' \
    "scripts/$name" || true)
  if [ -n "$h" ]; then
    hits="$hits$h"$'\n'
  fi
done
[ -z "$hits" ] || fail "shipped scripts name a dev-only staging file: $hits"

# Committed source copy of the working tree.
SRC="$WORK/src"
mkdir -p "$SRC"
(cd "$REPO" && tar --exclude=.git --exclude=.cursor --exclude=.claude --exclude=.codex --exclude=.writ \
  --exclude=__pycache__ -cf - .) | (cd "$SRC" && tar -xf -)
mkdir -p "$SRC/.writ/docs"
cp "$REPO"/.writ/docs/*.md "$SRC/.writ/docs/"
git -C "$SRC" init -q -b main
git -C "$SRC" -c user.name=t -c user.email=t@example.invalid add -A
git -C "$SRC" -c user.name=t -c user.email=t@example.invalid commit -q -m source

# The path under test is "upstream no longer has the file". If the source
# still carried a lean sibling, update would reach the stale branch some
# other way and this test would prove nothing about the deletion.
for f in "$SRC"/commands/*.lean.md; do
  [ -e "$f" ] && fail "source still ships $(basename "$f"); the lean siblings must be deleted"
done
[ -f "$SRC/commands/implement-story.md" ] || fail "fixture: source has no commands/implement-story.md"

# The Story 4 path under test is "upstream still has the file, the filter
# rejects it". If the source lacked either file, update would mark it stale
# because it is missing upstream, and this test would prove nothing about the
# filters.
for rel in $STAGING scripts/harness-cost.py; do
  [ -f "$SRC/$rel" ] || fail "fixture: source has no $rel"
done

# What install must still ship: the scripts the source's own filter accepts,
# and every source doc but the state doc.
SHIPPED_SCRIPTS=$(cd "$SRC/scripts" && bash -c "$(script_filter "$SRC/scripts/install.sh")"$'\n'\
'for n in "$@"; do [ -f "$n" ] && is_shippable_script "$n" && echo "$n"; done; true' _ *)
SHIPPED_DOCS=$(cd "$SRC/.writ/docs" && for f in *.md; do
  [ "$f" = recommended-delivery-state-format.md ] || echo "$f"
done)
[ -n "$SHIPPED_SCRIPTS" ] || fail "fixture: no shipped scripts in the source"
[ -n "$SHIPPED_DOCS" ] || fail "fixture: no shipped docs in the source"
printf '%s\n' "$SHIPPED_SCRIPTS" | grep -qx spec-status.py || fail "fixture: spec-status.py is not shipped"

# Number of manifest lines whose path is exactly $2.
manifest_count() {
  awk -v p="$2" '!/^#/ && $2 == p' "$1" | wc -l | tr -d ' '
}

# AC-4.2: an install dry run names neither staging file and lists every other
# shipped script and doc as new.
check_dry_run() {
  local label="$1" out="$2" rel name
  for rel in $STAGING; do
    if printf '%s\n' "$out" | grep -qF "$(basename "$rel")"; then
      fail "$label: dry run names $rel: $(printf '%s\n' "$out" | grep -F "$(basename "$rel")")"
    fi
  done
  for name in $SHIPPED_SCRIPTS; do
    printf '%s\n' "$out" | grep -qE "[[:space:]]scripts/${name//./\\.}\$" \
      || fail "$label: dry run does not list scripts/$name"
  done
  for name in $SHIPPED_DOCS; do
    printf '%s\n' "$out" | grep -qE "[[:space:]]\.writ/docs/${name//./\\.}\$" \
      || fail "$label: dry run does not list .writ/docs/$name"
  done
}

# AC-4.2: after a real install neither staging file is in the output, on
# disk, or in the manifest, and every other shipped script and doc is
# installed and recorded with its upstream hash.
check_installed() {
  local label="$1" project="$2" platform="$3" out="$4" manifest rel name
  manifest="$project/.$platform/.writ-manifest"
  [ -f "$manifest" ] || fail "$label: no manifest at .$platform/.writ-manifest"
  for rel in $STAGING; do
    if printf '%s\n' "$out" | grep -qF "$(basename "$rel")"; then
      fail "$label: install output names $rel"
    fi
    [ ! -e "$project/$rel" ] || fail "$label: install wrote $rel"
    [ "$(manifest_count "$manifest" "$rel")" = 0 ] || fail "$label: manifest records $rel"
  done
  for rel in $(printf 'scripts/%s\n' $SHIPPED_SCRIPTS) $(printf '.writ/docs/%s\n' $SHIPPED_DOCS); do
    cmp -s "$SRC/$rel" "$project/$rel" || fail "$label: $rel missing or differs from upstream"
    grep -qxF "$(hash_file "$SRC/$rel")  $rel" "$manifest" \
      || fail "$label: manifest has no upstream baseline for $rel"
  done
}

# ----- AC-1.2: install --dry-run lists commands, never a .lean.md -----
T1="$WORK/dry"
mkdir -p "$T1"
out=$(cd "$T1" && bash "$SRC/scripts/install.sh" --platform claude --dry-run --no-commit 2>&1) \
  || fail "install --dry-run exited non-zero: $out"
printf '%s' "$out" | grep -q 'commands/implement-story.md' \
  || fail "install dry run does not list commands/implement-story.md: $out"
if printf '%s\n' "$out" | grep -q '\.lean\.md'; then
  fail "install dry run lists a .lean.md file: $(printf '%s\n' "$out" | grep '\.lean\.md')"
fi
# 2026-10-20-harness-cuts AC-4.2 (claude): the dry run names neither staging file.
check_dry_run "claude install --dry-run" "$out"

# ----- AC-1.2: install copies and records no .lean.md, counts every command -----
T2="$WORK/proj"
mkdir -p "$T2"
out=$(cd "$T2" && bash "$SRC/scripts/install.sh" --platform claude --no-commit 2>&1) \
  || fail "install exited non-zero: $out"
CMDS="$T2/.claude/commands"
MANIFEST="$T2/.claude/.writ-manifest"
[ -f "$CMDS/implement-story.md" ] || fail "install: commands/implement-story.md missing"
[ -f "$MANIFEST" ] || fail "install: no manifest at .claude/.writ-manifest"
for f in "$CMDS"/*.lean.md; do
  [ -e "$f" ] && fail "install copied $(basename "$f") into .claude/commands/"
done
if grep -q '\.lean\.md$' "$MANIFEST"; then
  fail "install recorded a .lean.md in the manifest: $(grep '\.lean\.md$' "$MANIFEST")"
fi
expected=0
for f in "$SRC"/commands/*.md; do
  [ -f "$f" ] && expected=$((expected + 1))
done
printf '%s' "$out" | grep -q "Commands:  $expected\$" \
  || fail "install: command count is not $expected (every commands/*.md): $(printf '%s\n' "$out" | grep 'Commands:')"
# 2026-10-20-harness-cuts AC-4.2 (claude): install ships neither staging file.
check_installed "claude install" "$T2" claude "$out"

# ----- Plant an old install: two unmodified lean copies and one edited copy -----
# Each gets a manifest line, since update only removes what the manifest
# records. The source no longer has the real files, so any content works.
plant() {
  local name="$1"
  printf '# old %s from an earlier install\n' "$name" > "$CMDS/$name"
  printf '%s  commands/%s\n' "$(hash_file "$CMDS/$name")" "$name" >> "$MANIFEST"
}
plant implement-story.lean.md
plant _preamble.lean.md
plant verify-spec.lean.md
VERIFY_BASELINE=$(hash_file "$CMDS/verify-spec.lean.md")
printf 'local edit\n' >> "$CMDS/verify-spec.lean.md"
VERIFY_MODIFIED=$(hash_file "$CMDS/verify-spec.lean.md")

# 2026-10-20-harness-cuts AC-4.3: unmodified copies of both staging files from
# an older install, with their manifest lines. Upstream still has both.
plant_copy() {
  local project="$1" manifest="$2" rel="$3"
  mkdir -p "$project/$(dirname "$rel")"
  cp "$SRC/$rel" "$project/$rel"
  printf '%s  %s\n' "$(hash_file "$project/$rel")" "$rel" >> "$manifest"
}
for rel in $STAGING; do
  plant_copy "$T2" "$MANIFEST" "$rel"
done

KEPT_WARNING='⚠️  Stale (no longer shipped, locally modified — kept): commands/verify-spec.lean.md'

# ----- AC-1.3: update --dry-run lists both unmodified copies as stale, changes nothing -----
before=$(tree_digest "$T2")
out=$(cd "$T2" && WRIT_REPO="$SRC" bash "$SRC/scripts/update.sh" --platform claude --dry-run --no-commit 2>&1) \
  || fail "update --dry-run exited non-zero: $out"
printf '%s' "$out" | grep -qF 'Stale files (removed upstream, would be deleted):' \
  || fail "update dry run prints no stale-file list: $out"
for name in implement-story.lean.md _preamble.lean.md; do
  printf '%s' "$out" | grep -qF "🗑  commands/$name" \
    || fail "update dry run does not list commands/$name as stale: $out"
done
if printf '%s' "$out" | grep -qF '🗑  commands/verify-spec.lean.md'; then
  fail "update dry run lists the modified verify-spec.lean.md for deletion: $out"
fi
# AC-1.4: the dry run already warns about the modified copy.
printf '%s' "$out" | grep -qF "$KEPT_WARNING" \
  || fail "update dry run does not warn on the modified verify-spec.lean.md: $out"
# 2026-10-20-harness-cuts AC-4.3: the dry run lists both staging files as stale.
for rel in $STAGING; do
  printf '%s' "$out" | grep -qF "🗑  $rel" \
    || fail "update dry run does not list $rel as stale: $out"
done
[ "$(tree_digest "$T2")" = "$before" ] || fail "update --dry-run changed files on disk"

# ----- AC-1.3 / AC-1.4: update removes the unmodified copies, keeps the edited one -----
out=$(cd "$T2" && WRIT_REPO="$SRC" bash "$SRC/scripts/update.sh" --platform claude --no-commit 2>&1) \
  || fail "update exited non-zero: $out"
for name in implement-story.lean.md _preamble.lean.md; do
  [ ! -e "$CMDS/$name" ] || fail "update: unmodified commands/$name not removed"
  printf '%s' "$out" | grep -qF "🗑  Removed: commands/$name" \
    || fail "update: removal of commands/$name not reported: $out"
  if grep -qF "commands/$name" "$MANIFEST"; then
    fail "update: manifest still records the removed commands/$name"
  fi
done
[ -f "$CMDS/verify-spec.lean.md" ] || fail "update: locally modified verify-spec.lean.md was removed"
[ "$(hash_file "$CMDS/verify-spec.lean.md")" = "$VERIFY_MODIFIED" ] \
  || fail "update: locally modified verify-spec.lean.md was changed"
printf '%s' "$out" | grep -qF "$KEPT_WARNING" \
  || fail "update: no stale warning names the modified verify-spec.lean.md: $out"
grep -q "^$VERIFY_BASELINE  commands/verify-spec.lean.md\$" "$MANIFEST" \
  || fail "update: manifest dropped the original baseline of the kept verify-spec.lean.md"
[ -f "$CMDS/implement-story.md" ] || fail "update: default commands/implement-story.md missing"
# 2026-10-20-harness-cuts AC-4.3: update removes both unmodified staging copies.
for rel in $STAGING; do
  [ ! -e "$T2/$rel" ] || fail "update: unmodified $rel not removed"
  printf '%s' "$out" | grep -qF "🗑  Removed: $rel" \
    || fail "update: removal of $rel not reported: $out"
  [ "$(manifest_count "$MANIFEST" "$rel")" = 0 ] || fail "update: manifest still records the removed $rel"
done

# ----- AC-1.4: a second update still warns and leaves the edited copy alone -----
out=$(cd "$T2" && WRIT_REPO="$SRC" bash "$SRC/scripts/update.sh" --platform claude --no-commit 2>&1) \
  || fail "second update exited non-zero: $out"
printf '%s' "$out" | grep -qF "$KEPT_WARNING" \
  || fail "second update no longer warns on the kept verify-spec.lean.md: $out"
[ "$(hash_file "$CMDS/verify-spec.lean.md")" = "$VERIFY_MODIFIED" ] \
  || fail "second update changed the kept verify-spec.lean.md"
for name in implement-story.lean.md _preamble.lean.md; do
  [ ! -e "$CMDS/$name" ] || fail "second update: commands/$name reappeared"
done
for rel in $STAGING; do
  [ ! -e "$T2/$rel" ] || fail "second update: $rel reappeared"
  [ "$(manifest_count "$MANIFEST" "$rel")" = 0 ] || fail "second update: manifest records $rel"
  if printf '%s' "$out" | grep -qF "$(basename "$rel")"; then
    fail "second update still names $rel: $(printf '%s\n' "$out" | grep -F "$(basename "$rel")")"
  fi
done

# ----- 2026-10-20-harness-cuts AC-4.3: locally modified staging copies are kept on every run -----
# A second Claude Code project. Each staging file was installed by an older
# version (manifest baseline = upstream hash), then edited. An unmodified
# dev-only scripts/harness-cost.py is also planted: its removal makes run 1
# rewrite the manifest. Without a removal, update exits "Already up to date"
# before rewriting, and the carried-forward baseline would go untested.
T3="$WORK/proj-kept"
mkdir -p "$T3"
out=$(cd "$T3" && bash "$SRC/scripts/install.sh" --platform claude --no-commit 2>&1) \
  || fail "install (kept project) exited non-zero: $out"
MANIFEST3="$T3/.claude/.writ-manifest"
[ -f "$MANIFEST3" ] || fail "install (kept project): no manifest"
plant_copy "$T3" "$MANIFEST3" scripts/harness-cost.py
for rel in $STAGING; do
  plant_copy "$T3" "$MANIFEST3" "$rel"
  printf '\n# local edit\n' >> "$T3/$rel"
done
HELPER_BASELINE=$(hash_file "$SRC/$HELPER")
DOC_BASELINE=$(hash_file "$SRC/$STATE_DOC")
HELPER_MODIFIED=$(hash_file "$T3/$HELPER")
DOC_MODIFIED=$(hash_file "$T3/$STATE_DOC")

check_kept() {
  local label="$1" out="$2" rel baseline modified
  for rel in $STAGING; do
    if [ "$rel" = "$HELPER" ]; then
      baseline="$HELPER_BASELINE"; modified="$HELPER_MODIFIED"
    else
      baseline="$DOC_BASELINE"; modified="$DOC_MODIFIED"
    fi
    [ -f "$T3/$rel" ] || fail "$label: locally modified $rel was removed"
    [ "$(hash_file "$T3/$rel")" = "$modified" ] || fail "$label: locally modified $rel was changed"
    printf '%s' "$out" | grep -qF "⚠️  Stale (no longer shipped, locally modified — kept): $rel" \
      || fail "$label: no kept-stale warning names $rel: $out"
    if printf '%s' "$out" | grep -qF "🗑  Removed: $rel"; then
      fail "$label: reports removing the kept $rel"
    fi
    [ "$(manifest_count "$MANIFEST3" "$rel")" = 1 ] \
      || fail "$label: manifest must hold exactly one line for $rel: $(grep -F "$rel" "$MANIFEST3" || true)"
    grep -qxF "$baseline  $rel" "$MANIFEST3" \
      || fail "$label: manifest dropped the original baseline of the kept $rel"
  done
}

out=$(cd "$T3" && WRIT_REPO="$SRC" bash "$SRC/scripts/update.sh" --platform claude --no-commit 2>&1) \
  || fail "update (kept project) exited non-zero: $out"
[ ! -e "$T3/scripts/harness-cost.py" ] || fail "update (kept project): unmodified scripts/harness-cost.py not removed"
printf '%s' "$out" | grep -qF "🗑  Removed: scripts/harness-cost.py" \
  || fail "update (kept project): run 1 removed nothing, so the manifest was not rewritten: $out"
check_kept "update (kept project) run 1" "$out"

out=$(cd "$T3" && WRIT_REPO="$SRC" bash "$SRC/scripts/update.sh" --platform claude --no-commit 2>&1) \
  || fail "second update (kept project) exited non-zero: $out"
check_kept "update (kept project) run 2" "$out"

# ----- 2026-10-20-harness-cuts AC-4.2: Cursor and Codex install neither staging file -----
for platform in cursor codex; do
  P="$WORK/fresh-$platform"
  mkdir -p "$P"
  out=$(cd "$P" && bash "$SRC/scripts/install.sh" --platform "$platform" --dry-run --no-commit 2>&1) \
    || fail "$platform install --dry-run exited non-zero: $out"
  check_dry_run "$platform install --dry-run" "$out"
  [ -z "$(cd "$P" && find . -mindepth 1 -print -quit)" ] || fail "$platform install --dry-run wrote files"
  out=$(cd "$P" && bash "$SRC/scripts/install.sh" --platform "$platform" --no-commit 2>&1) \
    || fail "$platform install exited non-zero: $out"
  check_installed "$platform install" "$P" "$platform" "$out"
done

# AC-4.2: re-running install over copies an older version left behind never
# records them in the manifest. install.sh does not remove files, so both
# copies stay as they are.
P="$WORK/fresh-codex"
for rel in $STAGING; do
  cp "$SRC/$rel" "$P/$rel"
done
out=$(cd "$P" && bash "$SRC/scripts/install.sh" --platform codex --no-commit 2>&1) \
  || fail "codex re-install exited non-zero: $out"
for rel in $STAGING; do
  [ "$(manifest_count "$P/.codex/.writ-manifest" "$rel")" = 0 ] \
    || fail "codex re-install: manifest records the old copy of $rel"
  cmp -s "$SRC/$rel" "$P/$rel" || fail "codex re-install: changed the old copy of $rel"
done

# 2026-10-20-harness-cuts AC-4.3 (nil input): update removes only copies the
# manifest records. Those two copies have no manifest line, so update leaves
# them and does not record them; a recorded copy would be removed as stale on
# the next run. An unmodified scripts/harness-cost.py with a manifest line
# makes this run rewrite the manifest.
plant_copy "$P" "$P/.codex/.writ-manifest" scripts/harness-cost.py
out=$(cd "$P" && WRIT_REPO="$SRC" bash "$SRC/scripts/update.sh" --platform codex --no-commit 2>&1) \
  || fail "codex update exited non-zero: $out"
printf '%s' "$out" | grep -qF "🗑  Removed: scripts/harness-cost.py" \
  || fail "codex update removed nothing, so the manifest was not rewritten: $out"
for rel in $STAGING; do
  cmp -s "$SRC/$rel" "$P/$rel" || fail "codex update: removed or changed the unrecorded copy of $rel"
  [ "$(manifest_count "$P/.codex/.writ-manifest" "$rel")" = 0 ] \
    || fail "codex update: manifest records the unrecorded copy of $rel"
done

echo "PASS test_install_update_harness_cuts"
