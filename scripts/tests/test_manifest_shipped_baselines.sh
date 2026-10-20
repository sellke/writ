#!/usr/bin/env bash
# install.sh and update.sh record manifest baselines only for paths Writ ships,
# and a preserved, locally customized file keeps its previous baseline
# (Story 3 of 2026-10-20-ci-and-update-integrity).
#
# AC-3.1: install into a project that already holds user files in Writ's
#         folders leaves them byte-identical and records none of them. The
#         manifest carries `# baselines: shipped`; over a manifest without that
#         header, install writes none.
# AC-3.2: three manifest-rewriting updates never record a user file, never name
#         one in a stale or removal line, never remove or change one, and report
#         the user-written commands/review.md as preserved every time.
# AC-3.3: a customized commands/status.md and CLAUDE.md Writ block (Claude
#         Code, in the AC-3.2 project) and rules/writ.mdc (Cursor) stay
#         byte-identical across rewriting updates, the last after upstream
#         changed all three, and the manifest keeps each one's install-time
#         baseline.
# AC-3.4: after a fresh install and after an update, on claude, cursor, and
#         codex, every shipped path has exactly one well-formed line holding
#         the upstream hash (or a preserved file's previous baseline), and no
#         other path is recorded.
# AC-3.5: on the pre-fix scripts this test fails at AC-3.1, naming the first
#         recorded user file (.writ/docs/tech-stack.md).
#
# Runs the real scripts against temp targets. update.sh clones WRIT_REPO, so
# the source is a committed copy of this working tree. Does `git init`: run
# outside any sandbox.
set -euo pipefail

REPO="$(cd "$(dirname "$0")/../.." && pwd)"
WORK=$(mktemp -d "${TMPDIR:-/tmp}/writ-shipped-baselines-test.XXXXXX")
trap 'rm -rf "$WORK"' EXIT

# A shipped command no project here edits. Changing it upstream before each
# update gives update.sh something to apply, so it rewrites the manifest
# instead of exiting early with "Already up to date".
BUMPED_COMMAND="commands/create-issue.md"

# User files in Writ's folders, as manifest paths. The first four exist before
# install (commands/review.md is a user-written file at a shipped path); the
# last two are created after install.
USER_PATHS_BEFORE=".writ/docs/tech-stack.md scripts/deploy.sh commands/my-own.md commands/review.md"
USER_PATHS_AFTER=".writ/docs/code-style.md agents/my-agent.md"

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

# Committed source copy of the working tree.
SRC="$WORK/src"
mkdir -p "$SRC"
(cd "$REPO" && tar --exclude=.git --exclude=.cursor --exclude=.claude --exclude=.codex --exclude=.writ \
  --exclude=__pycache__ --exclude=.venv --exclude=.pytest_cache -cf - .) | (cd "$SRC" && tar -xf -)
mkdir -p "$SRC/.writ/docs"
cp "$REPO"/.writ/docs/*.md "$SRC/.writ/docs/"
git -C "$SRC" init -q -b main
commit_src "$SRC" source
for f in "$BUMPED_COMMAND" commands/review.md commands/status.md claude-code/CLAUDE.md cursor/writ.mdc \
    system-instructions.md codex/AGENTS.md.template codex/config.toml.template; do
  [ -f "$SRC/$f" ] || fail "fixture: source copy has no $f"
done
for p in $USER_PATHS_BEFORE $USER_PATHS_AFTER; do
  [ "$p" = commands/review.md ] && continue
  [ ! -e "$SRC/$p" ] || fail "fixture: user path $p is shipped upstream"
done
[ ! -e "$SRC/claude-code/agents/my-agent.md" ] || fail "fixture: agents/my-agent.md is shipped upstream"

# The ship filter, loaded from update.sh, so the expected set below is
# computed from $SRC without update.sh's own manifest walk.
body=$(filter_body "$SRC/scripts/update.sh")
[ -n "$body" ] || fail "cannot load is_shippable_script from update.sh"
eval "$body"

# ----- helpers -----

manifest_of() {
  printf '%s/.%s/.writ-manifest\n' "$1" "$2"
}

# Project path of a manifest path in a Claude Code project.
claude_project_path() {
  case "$1" in
    commands/*|agents/*) printf '.claude/%s\n' "$1" ;;
    *) printf '%s\n' "$1" ;;
  esac
}

write_user_file() {
  local proj="$1" mpath="$2" path
  path=$(claude_project_path "$mpath")
  mkdir -p "$(dirname "$proj/$path")"
  printf '# %s\n\nWritten by the project, not shipped by Writ.\n' "$mpath" > "$proj/$path"
  printf '%s  %s\n' "$(hash_file "$proj/$path")" "$mpath" >> "$proj.user-hashes"
}

manifest_hash() {
  awk -v p="$2" '!/^#/ && $2 == p { print $1; exit }' "$1"
}

run_install() {
  local label="$1" proj="$2" platform="$3" out
  mkdir -p "$proj"
  out=$(cd "$proj" && bash "$SRC/scripts/install.sh" --platform "$platform" --no-commit 2>&1) \
    || fail "$label: install exited non-zero: $out"
}

run_update() {
  local label="$1" proj="$2" platform="$3"
  UPDATE_OUT=$(cd "$proj" && WRIT_REPO="$SRC" bash "$SRC/scripts/update.sh" --platform "$platform" --no-commit 2>&1) \
    || fail "$label: update exited non-zero: $UPDATE_OUT"
}

# Append an upstream change to BUMPED_COMMAND and to any other given source
# files, and commit it.
bump_upstream() {
  local tag="$1" f
  shift
  for f in "$BUMPED_COMMAND" "$@"; do
    printf '\n<!-- upstream change %s -->\n' "$tag" >> "$SRC/$f"
  done
  commit_src "$SRC" "upstream change $tag"
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

check_user_files_intact() {
  local label="$1" proj="$2" want mpath path
  while read -r want mpath; do
    path=$(claude_project_path "$mpath")
    [ -f "$proj/$path" ] || fail "$label: user file $mpath was removed"
    [ "$(hash_file "$proj/$path")" = "$want" ] || fail "$label: user file $mpath was changed"
  done < "$proj.user-hashes"
}

check_not_recorded() {
  local label="$1" manifest="$2" mpath
  shift 2
  for mpath in "$@"; do
    if awk -v p="$mpath" '!/^#/ && index($0, p) { found = 1 } END { exit !found }' "$manifest"; then
      fail "$label: manifest records user file $mpath"
    fi
  done
}

check_not_reported_stale() {
  local label="$1" lines mpath
  shift
  lines=$(printf '%s\n' "$UPDATE_OUT" | grep -E 'Stale|Removed|🗑' || true)
  for mpath in "$@"; do
    if grep -qF -- "$mpath" <<< "$lines"; then
      fail "$label: update named user file $mpath in a stale or removal line: $lines"
    fi
  done
}

check_reported_preserved() {
  local label="$1" line="$2"
  grep -qF -- "⚡ Preserved: $line" <<< "$UPDATE_OUT" \
    || fail "$label: update did not report '⚡ Preserved: $line': $UPDATE_OUT"
}

check_header() {
  local label="$1" manifest="$2"
  grep -qx '# baselines: shipped' "$manifest" || fail "$label: manifest has no '# baselines: shipped' line"
}

# Every line is a comment or exactly "<64 lowercase hex>  <path>".
check_format() {
  local label="$1" manifest="$2" bad
  bad=$(grep -nEv '^#|^[0-9a-f]{64}  [^ ]+$' "$manifest" || true)
  [ -z "$bad" ] || fail "$label: malformed manifest line(s): $bad"
}

# Hash many files in one process: one hash per line, in input order.
hash_files() {
  local files=() f
  while IFS= read -r f; do
    files+=("$f")
  done
  if command -v shasum &>/dev/null; then
    shasum -a 256 "${files[@]}" | cut -d' ' -f1
  else
    sha256sum "${files[@]}" | cut -d' ' -f1
  fi
}

# Print "<source file> <manifest path>" for every path the platform ships,
# computed from $SRC: top-level scripts the ship filter accepts,
# .writ/docs/*.md, commands and agents minus lean siblings whose default
# exists, agents by the platform's glob, skills/*/SKILL.md, and the platform
# units.
shipped_sources() {
  local platform="$1" f name agents_src agent_glob
  case "$platform" in
    cursor) agents_src=agents; agent_glob='*.md' ;;
    claude) agents_src=claude-code/agents; agent_glob='*.md' ;;
    codex)  agents_src=codex/agents; agent_glob='*.toml' ;;
  esac
  for f in "$SRC"/scripts/*; do
    [ -f "$f" ] || continue
    name=$(basename "$f")
    is_shippable_script "$name" || continue
    printf '%s scripts/%s\n' "$f" "$name"
  done
  for f in "$SRC"/.writ/docs/*.md; do
    [ -f "$f" ] || continue
    printf '%s .writ/docs/%s\n' "$f" "$(basename "$f")"
  done
  for f in "$SRC"/commands/*.md "$SRC/$agents_src"/$agent_glob; do
    [ -f "$f" ] || continue
    name=$(basename "$f")
    case "$name" in
      *.lean.md) [ -f "$(dirname "$f")/${name%.lean.md}.md" ] && continue ;;
    esac
    case "$f" in
      "$SRC"/commands/*) printf '%s commands/%s\n' "$f" "$name" ;;
      *) printf '%s agents/%s\n' "$f" "$name" ;;
    esac
  done
  for f in "$SRC"/skills/*/SKILL.md; do
    [ -f "$f" ] || continue
    printf '%s skills/%s/SKILL.md\n' "$f" "$(basename "$(dirname "$f")")"
  done
  case "$platform" in
    cursor)
      printf '%s rules/writ.mdc\n' "$SRC/cursor/writ.mdc"
      printf '%s system-instructions.md\n' "$SRC/system-instructions.md"
      ;;
    claude)
      printf '%s CLAUDE.md.writ-block\n' "$SRC/claude-code/CLAUDE.md"
      ;;
    codex)
      printf '%s AGENTS.md.writ-block\n' "$SRC/codex/AGENTS.md.template"
      printf '%s .codex/config.toml.baseline\n' "$SRC/codex/config.toml.template"
      ;;
  esac
}

# Print "<upstream hash>  <manifest path>" for the shipped set.
shipped_set() {
  shipped_sources "$1" > "$WORK/sources"
  cut -d' ' -f1 "$WORK/sources" | hash_files > "$WORK/source-hashes"
  awk 'NR == FNR { h[FNR] = $1; next } { print h[FNR] "  " $2 }' "$WORK/source-hashes" "$WORK/sources"
}

# The manifest holds exactly the shipped set, one well-formed line per path.
# Each override "<path>=<hash>" names a preserved file: its line must carry
# that previous baseline, or must be absent when <hash> is empty.
check_complete() {
  local label="$1" proj="$2" platform="$3" manifest override path hash
  shift 3
  manifest=$(manifest_of "$proj" "$platform")
  check_format "$label" "$manifest"
  shipped_set "$platform" > "$WORK/expected"
  for override in "$@"; do
    path="${override%%=*}"
    hash="${override#*=}"
    awk -v p="$path" '$2 == p { found = 1 } END { exit !found }' "$WORK/expected" \
      || fail "$label: override path $path is not in the shipped set"
    awk -v p="$path" -v h="$hash" '$2 != p { print; next } h != "" { print h "  " p }' \
      "$WORK/expected" > "$WORK/expected.next"
    mv "$WORK/expected.next" "$WORK/expected"
  done
  LC_ALL=C sort "$WORK/expected" > "$WORK/expected.sorted"
  { grep -v '^#' "$manifest" || true; } | LC_ALL=C sort > "$WORK/actual.sorted"
  if ! diff "$WORK/expected.sorted" "$WORK/actual.sorted" > "$WORK/manifest.diff"; then
    fail "$label: manifest is not the shipped set (< expected, > recorded): $(head -n 40 "$WORK/manifest.diff")"
  fi
}

# ----- AC-3.1: install records no user file and writes the header -----
P1="$WORK/claude-user-files"
mkdir -p "$P1"
: > "$P1.user-hashes"
for p in $USER_PATHS_BEFORE; do
  write_user_file "$P1" "$p"
done
run_install "AC-3.1 install" "$P1" claude
M1=$(manifest_of "$P1" claude)
check_user_files_intact "AC-3.1 install" "$P1"
check_not_recorded "AC-3.1 install" "$M1" $USER_PATHS_BEFORE
check_header "AC-3.1 install" "$M1"
# review.md was preserved with no baseline, so it has no line.
check_complete "AC-3.1 install" "$P1" claude "commands/review.md="

# Re-install over a manifest that has the header keeps it; over one without
# it (a pre-fix manifest), install writes none. A copy keeps P1 for AC-3.2.
P1B="$WORK/claude-reinstall"
cp -R "$P1" "$P1B"
cp "$P1.user-hashes" "$P1B.user-hashes"
M1B=$(manifest_of "$P1B" claude)
run_install "AC-3.1 re-install" "$P1B" claude
check_header "AC-3.1 re-install" "$M1B"
check_user_files_intact "AC-3.1 re-install" "$P1B"
check_not_recorded "AC-3.1 re-install" "$M1B" $USER_PATHS_BEFORE
check_complete "AC-3.1 re-install" "$P1B" claude "commands/review.md="
grep -vx '# baselines: shipped' "$M1B" > "$WORK/manifest.no-header"
cat "$WORK/manifest.no-header" > "$M1B"
run_install "AC-3.1 header-less re-install" "$P1B" claude
if grep -q '^# baselines:' "$M1B"; then
  fail "AC-3.1 header-less re-install: install wrote a baselines header over a manifest that had none"
fi
check_user_files_intact "AC-3.1 header-less re-install" "$P1B"
check_not_recorded "AC-3.1 header-less re-install" "$M1B" $USER_PATHS_BEFORE
check_complete "AC-3.1 header-less re-install" "$P1B" claude "commands/review.md="

# ----- AC-3.2 / AC-3.3 setup -----
# The Claude Code project also carries the AC-3.3 customizations: an edited
# commands/status.md and an edited line inside the CLAUDE.md Writ block.
for p in $USER_PATHS_AFTER; do
  write_user_file "$P1" "$p"
done
REVIEW_HASH=$(hash_file "$P1/.claude/commands/review.md")
STATUS_BASELINE=$(manifest_hash "$M1" commands/status.md)
BLOCK_BASELINE=$(manifest_hash "$M1" CLAUDE.md.writ-block)
[ "$STATUS_BASELINE" = "$(hash_file "$SRC/commands/status.md")" ] \
  || fail "fixture: install did not record the upstream commands/status.md hash"
printf '\n<!-- local edit -->\n' >> "$P1/.claude/commands/status.md"
awk '{ print } $0 == "<!-- writ:start -->" { print "Local note inside the Writ block." }' \
  "$P1/CLAUDE.md" > "$WORK/claude-md.edited"
cat "$WORK/claude-md.edited" > "$P1/CLAUDE.md"
grep -qx 'Local note inside the Writ block.' "$P1/CLAUDE.md" || fail "fixture: could not edit the CLAUDE.md Writ block"
STATUS_LOCAL=$(hash_file "$P1/.claude/commands/status.md")
CLAUDE_LOCAL=$(hash_file "$P1/CLAUDE.md")

# A Cursor project with an edited rules/writ.mdc. AC-3.4: a fresh install
# records exactly the shipped set.
P3="$WORK/cursor-customized"
run_install "AC-3.3 cursor install" "$P3" cursor
M3=$(manifest_of "$P3" cursor)
check_header "AC-3.4 cursor install" "$M3"
check_complete "AC-3.4 cursor install" "$P3" cursor
RULE_BASELINE=$(manifest_hash "$M3" rules/writ.mdc)
printf '\n<!-- local edit -->\n' >> "$P3/.cursor/rules/writ.mdc"
RULE_LOCAL=$(hash_file "$P3/.cursor/rules/writ.mdc")

check_claude_customized() {
  local label="$1"
  check_reported_preserved "$label" "commands/status.md (local modifications)"
  check_reported_preserved "$label" "CLAUDE.md (Writ block has local modifications)"
  [ "$(hash_file "$P1/.claude/commands/status.md")" = "$STATUS_LOCAL" ] \
    || fail "$label: customized commands/status.md was overwritten"
  [ "$(hash_file "$P1/CLAUDE.md")" = "$CLAUDE_LOCAL" ] \
    || fail "$label: customized CLAUDE.md Writ block was overwritten"
  [ "$(manifest_hash "$M1" commands/status.md)" = "$STATUS_BASELINE" ] \
    || fail "$label: commands/status.md baseline changed from $STATUS_BASELINE to '$(manifest_hash "$M1" commands/status.md)'"
  [ "$(manifest_hash "$M1" CLAUDE.md.writ-block)" = "$BLOCK_BASELINE" ] \
    || fail "$label: CLAUDE.md.writ-block baseline changed from $BLOCK_BASELINE to '$(manifest_hash "$M1" CLAUDE.md.writ-block)'"
}

check_cursor_customized() {
  local label="$1"
  check_reported_preserved "$label" "rules/writ.mdc (local modifications)"
  [ "$(hash_file "$P3/.cursor/rules/writ.mdc")" = "$RULE_LOCAL" ] \
    || fail "$label: customized rules/writ.mdc was overwritten"
  [ "$(manifest_hash "$M3" rules/writ.mdc)" = "$RULE_BASELINE" ] \
    || fail "$label: rules/writ.mdc baseline changed from $RULE_BASELINE to '$(manifest_hash "$M3" rules/writ.mdc)'"
}

# ----- AC-3.2 / AC-3.3: three rewriting updates -----
# AC-3.2: no user file is recorded, called stale, removed, or changed, and
# the user-written commands/review.md is preserved every time.
# AC-3.3: runs 1 and 2 rewrite the manifest; before run 3 upstream changes
# commands/status.md, the CLAUDE.md template, and cursor/writ.mdc. The Cursor
# project updates on runs 1 and 3.
for run in 1 2 3; do
  label="AC-3.2/AC-3.3 claude update $run"
  if [ "$run" -eq 3 ]; then
    bump_upstream "run-$run" commands/status.md claude-code/CLAUDE.md cursor/writ.mdc
  else
    bump_upstream "run-$run"
  fi
  run_update "$label" "$P1" claude
  check_rewritten "$label" "$M1"
  check_user_files_intact "$label" "$P1"
  check_not_recorded "$label" "$M1" $USER_PATHS_BEFORE $USER_PATHS_AFTER
  check_not_reported_stale "$label" $USER_PATHS_BEFORE $USER_PATHS_AFTER
  check_reported_preserved "$label" "commands/review.md"
  [ "$(hash_file "$P1/.claude/commands/review.md")" = "$REVIEW_HASH" ] \
    || fail "$label: user-written commands/review.md was overwritten"
  check_claude_customized "$label"
  check_header "$label" "$M1"
  check_complete "$label" "$P1" claude "commands/review.md=" \
    "commands/status.md=$STATUS_BASELINE" "CLAUDE.md.writ-block=$BLOCK_BASELINE"

  [ "$run" -eq 2 ] && continue
  label="AC-3.3 cursor update $run"
  run_update "$label" "$P3" cursor
  check_rewritten "$label" "$M3"
  check_cursor_customized "$label"
  check_header "$label" "$M3"
  check_complete "$label" "$P3" cursor "rules/writ.mdc=$RULE_BASELINE"
done

# ----- AC-3.4: Codex fresh install and one update -----
# The project holds copies of two upstream files Writ does not ship: a lean
# sibling whose default exists and a dev-only script the ship filter rejects.
# Their bytes equal upstream, so only the walk's filters keep them out of the
# manifest.
P4="$WORK/codex-fresh"
mkdir -p "$P4/.codex/commands" "$P4/scripts"
cp "$SRC/commands/implement-story.lean.md" "$P4/.codex/commands/implement-story.lean.md"
cp "$SRC/scripts/harness-cost.py" "$P4/scripts/harness-cost.py"
is_shippable_script harness-cost.py && fail "fixture: harness-cost.py passes the ship filter"
run_install "AC-3.4 codex install" "$P4" codex
M4=$(manifest_of "$P4" codex)
check_header "AC-3.4 codex install" "$M4"
check_complete "AC-3.4 codex install" "$P4" codex
bump_upstream codex-1
run_update "AC-3.4 codex update" "$P4" codex
check_rewritten "AC-3.4 codex update" "$M4"
check_header "AC-3.4 codex update" "$M4"
check_complete "AC-3.4 codex update" "$P4" codex
cmp -s "$P4/.codex/commands/implement-story.lean.md" "$SRC/commands/implement-story.lean.md" \
  || fail "AC-3.4 codex update: unshipped commands/implement-story.lean.md was changed or removed"
cmp -s "$P4/scripts/harness-cost.py" "$SRC/scripts/harness-cost.py" \
  || fail "AC-3.4 codex update: unshipped scripts/harness-cost.py was changed or removed"

echo "PASS test_manifest_shipped_baselines"
