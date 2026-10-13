#!/usr/bin/env bash
# install.sh / update.sh / unlink.sh do not ship the six dev-only scripts
# (Story 2 of 2026-10-12-agent-cli-contract, ADR-029). They stay in the source
# repo because eval.sh runs them; installed projects get only agent-facing
# scripts. update.sh removes an unmodified copy a previous install left behind
# and keeps a locally modified one.
#
# Runs the real scripts against temp targets. update.sh clones WRIT_REPO, so
# the source is a committed copy of this working tree. Does `git init`: run
# outside any sandbox.
set -euo pipefail

REPO="$(cd "$(dirname "$0")/../.." && pwd)"
WORK=$(mktemp -d "${TMPDIR:-/tmp}/writ-dev-scripts-test.XXXXXX")
trap 'rm -rf "$WORK"' EXIT

DEV_SCRIPTS="pipeline-baseline.py measure-invocation.py harness-cost.py lean-decision.py prune-ledger.py spawn-cap.py"

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

# ----- AC-2.1: the filter rejects the six, accepts spec-status.py, and is one body -----
for s in install update unlink; do
  body=$(filter_body "$REPO/scripts/$s.sh")
  [ -n "$body" ] || fail "$s.sh: cannot load is_shippable_script"
  for name in $DEV_SCRIPTS; do
    if bash -c "$body"$'\n''is_shippable_script "$1"' _ "$name"; then
      fail "$s.sh: is_shippable_script accepts dev-only $name"
    fi
  done
  bash -c "$body"$'\n''is_shippable_script "$1"' _ spec-status.py \
    || fail "$s.sh: is_shippable_script rejects spec-status.py"
done
[ "$(filter_body "$REPO/scripts/install.sh")" = "$(filter_body "$REPO/scripts/update.sh")" ] \
  || fail "is_shippable_script differs between install.sh and update.sh"
[ "$(filter_body "$REPO/scripts/install.sh")" = "$(filter_body "$REPO/scripts/unlink.sh")" ] \
  || fail "is_shippable_script differs between install.sh and unlink.sh"
for name in $DEV_SCRIPTS; do
  [ -f "$REPO/scripts/$name" ] || fail "source scripts/$name is gone; eval.sh needs it"
done

# Committed source copy of the working tree; it still contains the six.
SRC="$WORK/src"
mkdir -p "$SRC"
(cd "$REPO" && tar --exclude=.git --exclude=.cursor --exclude=.claude --exclude=.codex --exclude=.writ \
  --exclude=__pycache__ -cf - .) | (cd "$SRC" && tar -xf -)
mkdir -p "$SRC/.writ/docs"
cp "$REPO"/.writ/docs/*.md "$SRC/.writ/docs/"
git -C "$SRC" init -q -b main
commit_src "$SRC" source
for name in $DEV_SCRIPTS; do
  [ -f "$SRC/scripts/$name" ] || fail "fixture: source copy has no scripts/$name"
done

# ----- AC-2.2: install never ships the six -----
T1="$WORK/dry"
mkdir -p "$T1"
out=$(cd "$T1" && bash "$SRC/scripts/install.sh" --platform claude --dry-run --no-commit 2>&1) \
  || fail "install --dry-run exited non-zero: $out"
printf '%s' "$out" | grep -q 'New: *scripts/spec-status.py' || fail "install dry run does not list spec-status.py"
for name in $DEV_SCRIPTS; do
  if printf '%s' "$out" | grep -qF "scripts/$name"; then
    fail "install dry run lists dev-only scripts/$name"
  fi
done

T2="$WORK/proj"
mkdir -p "$T2"
out=$(cd "$T2" && bash "$SRC/scripts/install.sh" --platform claude --no-commit 2>&1) \
  || fail "install exited non-zero: $out"
MANIFEST="$T2/.claude/.writ-manifest"
[ -f "$T2/scripts/spec-status.py" ] || fail "install: spec-status.py missing"
for name in $DEV_SCRIPTS; do
  [ ! -e "$T2/scripts/$name" ] || fail "install: dev-only scripts/$name was copied"
  if grep -qF "scripts/$name" "$MANIFEST"; then
    fail "install: manifest records dev-only scripts/$name"
  fi
done

# ----- AC-2.3 / AC-2.4: update removes an unmodified copy, keeps and warns on a modified one -----
KEPT_WARNING='⚠️  Stale (no longer shipped, locally modified — kept): scripts/lean-decision.py'

# A project an earlier release installed: harness-cost.py unmodified and
# lean-decision.py edited locally, both with manifest baselines.
plant_old_install() {
  local proj="$1" manifest="$1/.claude/.writ-manifest" out
  mkdir -p "$proj"
  out=$(cd "$proj" && bash "$SRC/scripts/install.sh" --platform claude --no-commit 2>&1) \
    || fail "install into $proj exited non-zero: $out"
  cp "$SRC/scripts/harness-cost.py" "$proj/scripts/harness-cost.py"
  printf '%s  scripts/harness-cost.py\n' "$(hash_file "$SRC/scripts/harness-cost.py")" >> "$manifest"
  cp "$SRC/scripts/lean-decision.py" "$proj/scripts/lean-decision.py"
  printf '%s  scripts/lean-decision.py\n' "$(hash_file "$SRC/scripts/lean-decision.py")" >> "$manifest"
  printf '# local edit\n' >> "$proj/scripts/lean-decision.py"
}

check_update() {
  local label="$1" proj="$2" src="$3" manifest="$2/.claude/.writ-manifest" out modified_hash name
  modified_hash=$(hash_file "$proj/scripts/lean-decision.py")

  out=$(cd "$proj" && WRIT_REPO="$src" bash "$src/scripts/update.sh" --platform claude --dry-run --no-commit 2>&1) \
    || fail "$label: update --dry-run exited non-zero: $out"
  printf '%s' "$out" | grep -qF '🗑  scripts/harness-cost.py' \
    || fail "$label: update dry run does not list harness-cost.py as stale: $out"
  printf '%s' "$out" | grep -qF "$KEPT_WARNING" \
    || fail "$label: update dry run does not warn on the modified lean-decision.py: $out"
  [ -f "$proj/scripts/harness-cost.py" ] || fail "$label: update --dry-run removed harness-cost.py"

  out=$(cd "$proj" && WRIT_REPO="$src" bash "$src/scripts/update.sh" --platform claude --no-commit 2>&1) \
    || fail "$label: update exited non-zero: $out"
  # AC-2.3: unmodified copy removed and reported.
  [ ! -e "$proj/scripts/harness-cost.py" ] || fail "$label: unmodified harness-cost.py not removed"
  printf '%s' "$out" | grep -qF '🗑  Removed: scripts/harness-cost.py' \
    || fail "$label: removal of harness-cost.py not reported: $out"
  if grep -qF 'scripts/harness-cost.py' "$manifest"; then
    fail "$label: manifest still records the removed harness-cost.py"
  fi
  # AC-2.4: modified copy kept byte for byte, warned about, and still tracked.
  [ -f "$proj/scripts/lean-decision.py" ] || fail "$label: locally modified lean-decision.py was removed"
  [ "$(hash_file "$proj/scripts/lean-decision.py")" = "$modified_hash" ] \
    || fail "$label: locally modified lean-decision.py was changed"
  printf '%s' "$out" | grep -qF "$KEPT_WARNING" \
    || fail "$label: no stale warning names the modified lean-decision.py: $out"
  grep -q "^$(hash_file "$SRC/scripts/lean-decision.py")  scripts/lean-decision.py\$" "$manifest" \
    || fail "$label: manifest dropped the original baseline of the kept lean-decision.py"
  for name in $DEV_SCRIPTS; do
    [ "$name" = lean-decision.py ] && continue
    [ -e "$proj/scripts/$name" ] && fail "$label: update shipped dev-only scripts/$name"
  done

  # A second run still warns: the kept file is not silently dropped.
  out=$(cd "$proj" && WRIT_REPO="$src" bash "$src/scripts/update.sh" --platform claude --no-commit 2>&1) \
    || fail "$label: second update exited non-zero: $out"
  printf '%s' "$out" | grep -qF "$KEPT_WARNING" \
    || fail "$label: second update no longer warns on the kept lean-decision.py: $out"
  [ "$(hash_file "$proj/scripts/lean-decision.py")" = "$modified_hash" ] \
    || fail "$label: second update changed the kept lean-decision.py"
  return 0
}

# Real case: upstream keeps the six for eval.sh; the ship filter rejects them.
plant_old_install "$WORK/proj-kept"
check_update "upstream keeps the six" "$WORK/proj-kept" "$SRC"

# Upstream deleted the six.
NEW_SRC="$WORK/src-new"
cp -R "$SRC" "$NEW_SRC"
for name in $DEV_SCRIPTS; do
  rm -f "$NEW_SRC/scripts/$name"
done
commit_src "$NEW_SRC" "drop dev-only scripts"
plant_old_install "$WORK/proj-deleted"
check_update "upstream deleted the six" "$WORK/proj-deleted" "$NEW_SRC"

# ----- AC-2.5: no shipped doc or command points at the six by path -----
for name in $DEV_SCRIPTS; do
  hits=$(cd "$REPO" && grep -rnF "scripts/$name" commands agents skills adapters .writ/docs 2>/dev/null || true)
  [ -z "$hits" ] || fail "shipped source references scripts/$name: $hits"
done
step3=$(sed -n '/^\*\*Apply same logic to runtime scripts\*\*/,/^\*\*Apply same logic to Writ reference docs\*\*/p' \
  "$REPO/commands/update-writ.md")
[ -n "$step3" ] || fail "commands/update-writ.md: runtime-scripts exclusion prose not found"
printf '%s' "$step3" | grep -qi 'dev-only' || fail "update-writ.md Step 3 does not name the dev-only helpers"
for name in $DEV_SCRIPTS; do
  printf '%s' "$step3" | grep -qF "\`$name\`" || fail "update-writ.md Step 3 does not list $name"
done

echo "PASS test_install_update_dev_scripts"
