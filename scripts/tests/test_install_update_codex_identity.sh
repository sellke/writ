#!/usr/bin/env bash
# Codex installs carry Writ's identity (Phase 14 acceptance, defect "Codex
# install has no Prime Directive"). Before this, AGENTS.md told the agent to
# read a system-instructions.md that install.sh never copied for Codex, and
# headless probes showed Codex confirming a false claim without checking.
#
# 1. A fresh install copies .codex/system-instructions.md byte for byte and
#    records it in the manifest. The AGENTS.md Writ block carries the Hard
#    Constraints and names .codex/system-instructions.md.
# 2. update.sh updates an unmodified copy and gives an older install that
#    lacks the file the file as new.
# 3. update.sh preserves and lists a modified copy; --force overwrites it.
# 4. uninstall.sh removes the file.
#
# Runs the real scripts against temp targets. update.sh clones WRIT_REPO, so
# the source is a committed copy of this working tree. Does `git init`: run
# outside any sandbox. Never point it at the Writ repo itself.
set -euo pipefail

REPO="$(cd "$(dirname "$0")/../.." && pwd)"
WORK=$(mktemp -d "${TMPDIR:-/tmp}/writ-codex-identity-test.XXXXXX")
trap 'rm -rf "$WORK"' EXIT

fail() { printf 'FAIL: %s\n' "$1" >&2; exit 1; }
hash_file() { if command -v shasum &>/dev/null; then shasum -a 256 "$1" | cut -d' ' -f1; else sha256sum "$1" | cut -d' ' -f1; fi; }
commit_src() {
  git -C "$1" -c user.name=t -c user.email=t@example.invalid add -A
  git -C "$1" -c user.name=t -c user.email=t@example.invalid commit -q -m "$2"
}
manifest_hash() { awk -v p="$2" '!/^#/ && $2 == p {print $1}' "$1"; }
run_install() { (cd "$1" && bash "$SRC/scripts/install.sh" --platform codex --no-commit 2>&1); }
run_update() { local p="$1"; shift; (cd "$p" && WRIT_REPO="$SRC" bash "$SRC/scripts/update.sh" --platform codex --no-commit "$@" 2>&1); }
run_uninstall() { (cd "$1" && printf 'n\n' | bash "$SRC/scripts/uninstall.sh" --platform codex --no-commit 2>&1); }
new_project() { mkdir -p "$1" && git -C "$1" init -q -b main && printf '# demo\n' > "$1/README.md" && commit_src "$1" init; }

SRC="$WORK/src"; mkdir -p "$SRC"
(cd "$REPO" && tar --exclude=.git --exclude=.cursor --exclude=.claude --exclude=.codex --exclude=.writ \
  --exclude=__pycache__ --exclude=.venv --exclude=.pytest_cache -cf - .) | (cd "$SRC" && tar -xf -)
mkdir -p "$SRC/.writ/docs"; cp "$REPO"/.writ/docs/*.md "$SRC/.writ/docs/"; cp "$REPO/.writ/manifest.yaml" "$SRC/.writ/"
git -C "$SRC" init -q -b main; commit_src "$SRC" source

FIRST_BULLET='- **Never reverse a position without new evidence.** If the user pushes back'

# 1. Fresh install.
P1="$WORK/p1"; new_project "$P1"; out=$(run_install "$P1")
[ -f "$P1/.codex/system-instructions.md" ] || fail "install did not copy .codex/system-instructions.md"
[ "$(hash_file "$P1/.codex/system-instructions.md")" = "$(hash_file "$SRC/system-instructions.md")" ] \
  || fail ".codex/system-instructions.md differs from the source"
[ "$(manifest_hash "$P1/.codex/.writ-manifest" system-instructions.md)" = "$(hash_file "$SRC/system-instructions.md")" ] \
  || fail "manifest has no baseline for system-instructions.md"
grep -qF -- "### Hard Constraints" "$P1/AGENTS.md" || fail "AGENTS.md Writ block has no Hard Constraints heading"
grep -qF -- "$FIRST_BULLET" "$P1/AGENTS.md" || fail "AGENTS.md Writ block lacks the first hard constraint"
grep -qF -- '.codex/system-instructions.md' "$P1/AGENTS.md" || fail "AGENTS.md does not name .codex/system-instructions.md"
printf '%s\n' "$out" | grep -qF "System instructions" || fail "install printed no System instructions step"

# 2. Update an unmodified copy, and give an older install the file as new.
printf '\n<!-- source change for the update test -->\n' >> "$SRC/system-instructions.md"; commit_src "$SRC" "change system instructions"
out=$(run_update "$P1")
[ "$(hash_file "$P1/.codex/system-instructions.md")" = "$(hash_file "$SRC/system-instructions.md")" ] \
  || fail "update did not update an unmodified .codex/system-instructions.md: $out"
P2="$WORK/p2"; new_project "$P2"; run_install "$P2" >/dev/null
rm "$P2/.codex/system-instructions.md"
awk '!(!/^#/ && $2 == "system-instructions.md")' "$P2/.codex/.writ-manifest" > "$P2/m" && mv "$P2/m" "$P2/.codex/.writ-manifest"
out=$(run_update "$P2")
[ -f "$P2/.codex/system-instructions.md" ] || fail "update did not add the file to an older install: $out"
printf '%s\n' "$out" | grep -qF "New:       system-instructions.md" || fail "update did not report the file as new: $out"

# 3. Preserve a modified copy; --force overwrites it.
P3="$WORK/p3"; new_project "$P3"; run_install "$P3" >/dev/null
printf '\nlocal edit\n' >> "$P3/.codex/system-instructions.md"
printf '\n<!-- second source change -->\n' >> "$SRC/system-instructions.md"; commit_src "$SRC" "second change"
out=$(run_update "$P3")
grep -qF "local edit" "$P3/.codex/system-instructions.md" || fail "update overwrote a modified copy: $out"
printf '%s\n' "$out" | grep -qF "Preserved: system-instructions.md" || fail "update did not list the preserved copy: $out"
run_update "$P3" --force >/dev/null
[ "$(hash_file "$P3/.codex/system-instructions.md")" = "$(hash_file "$SRC/system-instructions.md")" ] \
  || fail "update --force did not overwrite the modified copy"

# 4. Uninstall removes it.
run_uninstall "$P1" >/dev/null
[ ! -e "$P1/.codex/system-instructions.md" ] || fail "uninstall left .codex/system-instructions.md"

echo "PASS: test_install_update_codex_identity"
