#!/usr/bin/env bash
# install.sh / update.sh ship scripts/jev-thresholds.json beside
# scripts/jev-judge.py (Story 4 of 2026-09-25-jev-judgment-pilot, DEV-006).
# Without it an installed jev-judge.py falls back to the uncalibrated §4
# defaults and reports thresholds_missing. Only that one data file ships:
# any other scripts/*.json stays behind.
#
# Runs the real scripts against temp targets. update.sh clones WRIT_REPO, so
# the source is a committed copy of this working tree. Does `git init`: run
# outside any sandbox.
set -euo pipefail

REPO="$(cd "$(dirname "$0")/../.." && pwd)"
WORK=$(mktemp -d "${TMPDIR:-/tmp}/writ-thresholds-ship-test.XXXXXX")
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

commit_src() {
  git -C "$SRC" -c user.name=t -c user.email=t@example.invalid add -A
  git -C "$SRC" -c user.name=t -c user.email=t@example.invalid commit -q -m "$1"
}

# Committed source copy of the working tree, plus a decoy JSON that must not ship.
SRC="$WORK/src"
mkdir -p "$SRC"
(cd "$REPO" && tar --exclude=.git --exclude=.cursor --exclude=.claude --exclude=.codex --exclude=.writ \
  --exclude=__pycache__ -cf - .) | (cd "$SRC" && tar -xf -)
mkdir -p "$SRC/.writ/docs"
cp "$REPO"/.writ/docs/*.md "$SRC/.writ/docs/"
printf '{"decoy": true}\n' > "$SRC/scripts/decoy-data.json"
git -C "$SRC" init -q -b main
commit_src source

[ -f "$SRC/scripts/jev-thresholds.json" ] || fail "fixture: source has no scripts/jev-thresholds.json"

# ----- install: dry run lists the thresholds file, not the decoy -----
T1="$WORK/dry"
mkdir -p "$T1"
out=$(cd "$T1" && bash "$SRC/scripts/install.sh" --platform claude --dry-run --no-commit 2>&1) \
  || fail "install --dry-run exited non-zero: $out"
printf '%s' "$out" | grep -q 'New: *scripts/jev-thresholds.json' \
  || fail "install dry run does not list scripts/jev-thresholds.json"
printf '%s' "$out" | grep -q 'New: *scripts/jev-judge.py' || fail "install dry run does not list jev-judge.py"
if printf '%s' "$out" | grep -q 'decoy-data.json'; then
  fail "install dry run lists a non-shipped scripts/*.json"
fi
[ ! -e "$T1/scripts" ] || fail "install --dry-run wrote scripts/"

# ----- install: the file lands, is recorded, and is committed -----
T2="$WORK/proj"
mkdir -p "$T2"
git -C "$T2" init -q -b main
git -C "$T2" config user.name t
git -C "$T2" config user.email t@example.invalid
git -C "$T2" config commit.gpgsign false
git -C "$T2" commit -q --allow-empty -m init
out=$(cd "$T2" && bash "$SRC/scripts/install.sh" --platform claude 2>&1) \
  || fail "install exited non-zero: $out"
[ -f "$T2/scripts/jev-thresholds.json" ] || fail "install: scripts/jev-thresholds.json missing"
cmp -s "$T2/scripts/jev-thresholds.json" "$SRC/scripts/jev-thresholds.json" \
  || fail "install: jev-thresholds.json differs from source"
[ ! -e "$T2/scripts/decoy-data.json" ] || fail "install: a non-shipped scripts/*.json was copied"
grep -q '  scripts/jev-thresholds.json$' "$T2/.claude/.writ-manifest" \
  || fail "install: manifest does not record scripts/jev-thresholds.json"
git -C "$T2" ls-files --error-unmatch scripts/jev-thresholds.json >/dev/null 2>&1 \
  || fail "install: scoped commit did not add scripts/jev-thresholds.json"
# The installed helper reads the shipped file: no thresholds_missing.
out=$(cd "$T2" && env -u WRIT_JEV_REPLAY python3 scripts/jev-judge.py spec-findings --spec "$SRC/scripts/tests/fixtures/spec-analyze/story-2-event-creation-payment-flow" \
  --out "$WORK/f.json" --repo "$T2" 2>&1) || true
printf '%s' "$out" | grep -q 'thresholds_missing' && fail "installed jev-judge.py cannot find its thresholds file: $out"

# ----- update: a changed upstream file updates an unmodified local copy -----
python3 - "$SRC/scripts/jev-thresholds.json" <<'PY'
import json, sys
path = sys.argv[1]
data = json.load(open(path))
data["ac_shadow"]["satisfied"] = 0.91
open(path, "w").write(json.dumps(data, indent=2) + "\n")
PY
commit_src "bump thresholds"
out=$(cd "$T2" && WRIT_REPO="$SRC" bash "$SRC/scripts/update.sh" --platform claude --dry-run --no-commit 2>&1) \
  || fail "update --dry-run exited non-zero: $out"
printf '%s' "$out" | grep -q 'Update: *scripts/jev-thresholds.json' \
  || fail "update dry run does not list scripts/jev-thresholds.json: $out"
out=$(cd "$T2" && WRIT_REPO="$SRC" bash "$SRC/scripts/update.sh" --platform claude --no-commit 2>&1) \
  || fail "update exited non-zero: $out"
cmp -s "$T2/scripts/jev-thresholds.json" "$SRC/scripts/jev-thresholds.json" \
  || fail "update: jev-thresholds.json not updated"
grep -q "^$(hash_file "$SRC/scripts/jev-thresholds.json")  scripts/jev-thresholds.json\$" \
  "$T2/.claude/.writ-manifest" || fail "update: manifest hash for jev-thresholds.json not refreshed"
[ ! -e "$T2/scripts/decoy-data.json" ] || fail "update: a non-shipped scripts/*.json was copied"

# ----- update: an install that predates the file gains it -----
rm -f "$T2/scripts/jev-thresholds.json"
grep -v '  scripts/jev-thresholds.json$' "$T2/.claude/.writ-manifest" > "$WORK/m" || true
cp "$WORK/m" "$T2/.claude/.writ-manifest"
out=$(cd "$T2" && WRIT_REPO="$SRC" bash "$SRC/scripts/update.sh" --platform claude --no-commit 2>&1) \
  || fail "update exited non-zero: $out"
[ -f "$T2/scripts/jev-thresholds.json" ] || fail "update: missing jev-thresholds.json not restored"

# ----- a locally modified thresholds file is preserved -----
printf '{"local": true}\n' > "$T2/scripts/jev-thresholds.json"
out=$(cd "$T2" && WRIT_REPO="$SRC" bash "$SRC/scripts/update.sh" --platform claude --no-commit 2>&1) \
  || fail "update exited non-zero: $out"
grep -q '"local": true' "$T2/scripts/jev-thresholds.json" || fail "update: local thresholds edit overwritten"

# ----- unlink: a symlinked thresholds file becomes a recorded copy -----
T3="$WORK/linked"
mkdir -p "$T3/scripts" "$T3/.claude/commands"
ln -s "$SRC/scripts/jev-judge.py" "$T3/scripts/jev-judge.py"
ln -s "$SRC/scripts/jev-thresholds.json" "$T3/scripts/jev-thresholds.json"
ln -s "$SRC/scripts/decoy-data.json" "$T3/scripts/decoy-data.json"
ln -s "$SRC/commands/status.md" "$T3/.claude/commands/status.md"
printf '# Writ Manifest\n# mode: link\n# platform: claude\n# link_target: %s\n' "$SRC" \
  > "$T3/.claude/.writ-manifest"
out=$(cd "$T3" && bash "$SRC/scripts/unlink.sh" --platform claude --dry-run --no-commit 2>&1) \
  || fail "unlink --dry-run exited non-zero: $out"
printf '%s' "$out" | grep -q 'scripts/jev-thresholds.json' \
  || fail "unlink dry run does not list scripts/jev-thresholds.json: $out"
out=$(cd "$T3" && bash "$SRC/scripts/unlink.sh" --platform claude --no-commit 2>&1) \
  || fail "unlink exited non-zero: $out"
[ -f "$T3/scripts/jev-thresholds.json" ] && [ ! -L "$T3/scripts/jev-thresholds.json" ] \
  || fail "unlink: jev-thresholds.json is still a symlink"
cmp -s "$T3/scripts/jev-thresholds.json" "$SRC/scripts/jev-thresholds.json" \
  || fail "unlink: jev-thresholds.json differs from source"
grep -q '  scripts/jev-thresholds.json$' "$T3/.claude/.writ-manifest" \
  || fail "unlink: manifest does not record scripts/jev-thresholds.json"
[ -L "$T3/scripts/decoy-data.json" ] || fail "unlink: converted a non-shipped scripts/*.json"
grep -q 'decoy-data.json' "$T3/.claude/.writ-manifest" && fail "unlink: manifest records the decoy"
[ ! -x "$T3/scripts/jev-thresholds.json" ] || fail "unlink: jev-thresholds.json made executable"

echo "PASS test_install_update_thresholds"
