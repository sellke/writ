#!/usr/bin/env bash
# scripts/install.sh: install, update, and uninstall the Writ skills.
#
# Each case runs the real installer in a temp project against a small fake
# Writ checkout (WRIT_SRC), so the cases do not depend on the skills in this
# repo. The last case installs from this repo and checks only that every
# SKILL.md present at that moment arrives.
#
# HOME is a temp folder for every run, so no case can reach the real home
# folder. Prints one PASS or FAIL line per case and a final count; exits 1 if
# any case failed. Does `git init` in temp dirs: run outside any sandbox.
set -uo pipefail

REPO="$(cd "$(dirname "$0")/../.." && pwd)"
INSTALL="$REPO/scripts/install.sh"
WORK=$(mktemp -d "${TMPDIR:-/tmp}/writ-install-test.XXXXXX")
trap 'rm -rf "$WORK"' EXIT
WORK=$(cd "$WORK" && pwd -P)

unset GIT_DIR GIT_WORK_TREE WRIT_SRC WRIT_REF WRIT_REPO CDPATH
export GIT_CEILING_DIRECTORIES="$WORK"   # temp projects never see a repo above them
export GIT_CONFIG_GLOBAL=/dev/null GIT_CONFIG_NOSYSTEM=1
export GIT_AUTHOR_NAME=t GIT_AUTHOR_EMAIL=t@example.invalid
export GIT_COMMITTER_NAME=t GIT_COMMITTER_EMAIL=t@example.invalid

LEGACY_CMD='bash <(curl -s https://raw.githubusercontent.com/sellke/writ/v0.49.0/scripts/uninstall.sh) --platform'
FAKE_HOME="$WORK/home"; mkdir -p "$FAKE_HOME"
SRC="" OUT="" RC=0 CASE="" CASE_ERR=""
pass_count=0 fail_count=0

# ---------------------------------------------------------------------------
# Case bookkeeping and checks. A case is begin ... checks ... finish; the first
# failed check is the one reported.
# ---------------------------------------------------------------------------

begin() { CASE="$1"; CASE_ERR=""; }
bad() { [ -n "$CASE_ERR" ] || CASE_ERR="$1"; }
finish() {
  if [ -z "$CASE_ERR" ]; then
    pass_count=$((pass_count + 1)); printf 'PASS: %s\n' "$CASE"
  else
    fail_count=$((fail_count + 1)); printf 'FAIL: %s -- %s\n' "$CASE" "$CASE_ERR"
    printf '%s\n' "$OUT" | sed 's/^/      | /' >&2
  fi
}

# run <dir> [installer args...]: sets OUT (stdout and stderr) and RC.
run() {
  local dir="$1"; shift
  RC=0
  OUT=$(cd "$dir" && HOME="$FAKE_HOME" WRIT_SRC="$SRC" bash "$INSTALL" "$@" 2>&1) || RC=$?
}

sha() { if command -v shasum >/dev/null 2>&1; then shasum -a 256 "$1"; else sha256sum "$1"; fi | cut -d' ' -f1; }
rel() { printf '%s' "${1#"$WORK"/}"; }

want_rc()     { [ "$RC" -eq "$1" ] || bad "exit code $RC, wanted $1"; }
want_out()    { case "$OUT" in *"$1"*) ;; *) bad "output lacks: $1" ;; esac; }
want_no_out() { case "$OUT" in *"$1"*) bad "output has: $1" ;; esac; }
want_gone()   { { [ ! -e "$1" ] && [ ! -L "$1" ]; } || bad "should not exist: $(rel "$1")"; }
want_text()   { [ "$(cat "$1" 2>/dev/null)" = "$2" ] || bad "$(rel "$1") does not hold: $2"; }
want_same()   { cmp -s "$1" "$2" || bad "$(rel "$2") differs from $(rel "$1")"; }
want_equal()  { [ "$1" = "$2" ] || bad "$3"; }

# One line per path under $1 (skipping .git): type, path, and a checksum for
# files. Equal snapshots mean nothing on disk changed.
snapshot() {
  (cd "$1" && find . -mindepth 1 \( -path ./.git -prune \) -o -print | LC_ALL=C sort | while IFS= read -r p; do
    if [ -L "$p" ]; then printf 'link %s -> %s\n' "$p" "$(readlink "$p")"
    elif [ -d "$p" ]; then printf 'dir  %s\n' "$p"
    else printf 'file %s %s\n' "$p" "$(cksum < "$p")"; fi
  done)
}

# want_exact <dest> <source root> <file list>: the destination holds exactly
# the listed files plus the manifest, each identical to the source.
want_exact() {
  local got want f
  got=$(cd "$1" 2>/dev/null && find . -type f | sed 's|^\./||' | LC_ALL=C sort)
  want=$(printf '%s\n.writ-manifest\n' "$3" | LC_ALL=C sort)
  [ "$got" = "$want" ] || bad "files in $(rel "$1") are: $(printf '%s' "$got" | tr '\n' ' ')"
  while IFS= read -r f; do
    cmp -s "$2/plugins/writ/skills/$f" "$1/$f" || bad "$f differs from the source"
  done <<< "$3"
}

# want_manifest <dest> <version> <source root> <file list>: the manifest names
# the version and holds exactly one "hash  path" line per listed file.
want_manifest() {
  local m="$1/.writ-manifest" f
  [ "$(head -n 1 "$m" 2>/dev/null)" = "# version: $2" ] || bad "manifest version header is not $2"
  while IFS= read -r f; do
    grep -Fxq -- "$(sha "$3/plugins/writ/skills/$f")  $f" "$m" 2>/dev/null || bad "manifest lacks the source hash of $f"
  done <<< "$4"
  [ "$(grep -vc '^#' "$m" 2>/dev/null)" = "$(grep -c '' <<< "$4")" ] || bad "manifest file-line count is wrong"
}

# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------

# make_source <dir> <version>: a small fake Writ checkout.
make_source() {
  local s="$1/plugins/writ/skills"
  mkdir -p "$s/writ" "$s/writ-spec/scripts/__pycache__"
  printf '%s\n' "$2" > "$1/VERSION"
  printf 'front door %s\n' "$2" > "$s/writ/SKILL.md"
  printf 'spec skill\n' > "$s/writ-spec/SKILL.md"
  printf 'template\n' > "$s/writ-spec/spec template.md"
  printf 'print("check %s")\n' "$2" > "$s/writ-spec/scripts/check.py"
  # Never installed:
  printf 'x' > "$s/writ-spec/scripts/__pycache__/check.cpython-312.pyc"
  printf 'x' > "$s/writ-spec/scripts/stray.pyc"
  printf 'x' > "$s/writ-spec/.DS_Store"
}

# v1 ships six files. v2 changes two, drops the writ-old skill, adds writ-ship.
V1="$WORK/src v1"; make_source "$V1" 1.0.0
mkdir -p "$V1/plugins/writ/skills/writ-old/ref"
printf 'old skill\n' > "$V1/plugins/writ/skills/writ-old/SKILL.md"
printf 'old guide\n' > "$V1/plugins/writ/skills/writ-old/ref/guide.md"
V2="$WORK/src v2"; make_source "$V2" 1.1.0
mkdir -p "$V2/plugins/writ/skills/writ-ship"
printf 'ship skill\n' > "$V2/plugins/writ/skills/writ-ship/SKILL.md"

COMMON='writ/SKILL.md
writ-spec/SKILL.md
writ-spec/spec template.md
writ-spec/scripts/check.py'
V1_LIST="$COMMON
writ-old/SKILL.md
writ-old/ref/guide.md"
V2_LIST="$COMMON
writ-ship/SKILL.md"
ADDED_6="Added 6, updated 0, kept 0 (customised), removed 0."
NO_CHANGE="Added 0, updated 0, kept 0 (customised), removed 0."

# new_project <name>: a git project with a spec under .writ/; prints its path.
new_project() {
  local p="$WORK/$1"
  mkdir -p "$p/.writ/specs"
  git init -q "$p" >/dev/null 2>&1
  printf 'my spec\n' > "$p/.writ/specs/a.md"
  printf 'readme\n' > "$p/README.md"
  printf '%s\n' "$p"
}

# installed_project <name> [installer args...]: a project with v1 installed.
installed_project() {
  local name="$1" p; shift
  p=$(new_project "$name")
  SRC="$V1"; run "$p" "$@"
  [ "$RC" -eq 0 ] || printf 'fixture: v1 install failed in %s\n%s\n' "$name" "$OUT" >&2
  printf '%s\n' "$p"
}

# ---------------------------------------------------------------------------
# Fresh install
# ---------------------------------------------------------------------------

# fresh_case <label> <destination> <the other destination's top folder> [args...]
fresh_case() {
  local label="$1" dest="$2" other="$3" P; shift 3
  begin "fresh install, $label: writes $dest and nothing else"
  P=$(new_project "fresh-$label"); SRC="$V1"
  run "$P" "$@"
  want_rc 0
  want_exact "$P/$dest" "$V1" "$V1_LIST"
  want_manifest "$P/$dest" 1.0.0 "$V1" "$V1_LIST"
  want_gone "$P/$other"
  want_gone "$P/$dest/writ-spec/scripts/__pycache__"
  want_text "$P/.writ/specs/a.md" "my spec"
  want_text "$P/README.md" "readme"
  want_out "in $dest"
  want_out "Version: none -> 1.0.0"
  want_out "$ADDED_6"
  want_out "uncommitted"
  # shellcheck disable=SC2016
  want_out 'type /writ (Cursor, Claude Code) or $writ (Codex)'
  finish
}
fresh_case "no --platform" .agents/skills .claude
fresh_case "cursor" .agents/skills .claude --platform cursor
fresh_case "codex" .agents/skills .claude --platform codex
fresh_case "claude" .claude/skills .agents --platform claude
fresh_case "--platform=claude" .claude/skills .agents --platform=claude

begin "repeated --platform flags for one destination write it once"
P=$(new_project dedupe); SRC="$V1"
run "$P" --platform cursor --platform codex --platform cursor
want_rc 0
want_exact "$P/.agents/skills" "$V1" "$V1_LIST"
want_gone "$P/.claude"
want_equal "$(printf '%s\n' "$OUT" | grep -c 'in \.agents/skills')" 1 "the .agents/skills report is not printed exactly once"
finish

begin "--platform codex --platform claude writes both destinations"
P=$(new_project both); SRC="$V1"
run "$P" --platform codex --platform claude
want_rc 0
want_exact "$P/.agents/skills" "$V1" "$V1_LIST"
want_exact "$P/.claude/skills" "$V1" "$V1_LIST"
want_out "Writ for Cursor and Codex, in .agents/skills"
want_out "Writ for Claude Code, in .claude/skills"
finish

begin "--global installs under HOME, from a folder that is not a project"
FAKE_HOME="$WORK/home-global"; mkdir -p "$FAKE_HOME" "$WORK/not-a-project"; SRC="$V1"
run "$WORK/not-a-project" --global
want_rc 0
want_exact "$FAKE_HOME/.agents/skills" "$V1" "$V1_LIST"
want_manifest "$FAKE_HOME/.agents/skills" 1.0.0 "$V1" "$V1_LIST"
want_gone "$FAKE_HOME/.claude"
want_equal "$(snapshot "$WORK/not-a-project")" "" "the current folder was written to"
want_out "in ~/.agents/skills"
want_no_out "uncommitted"
finish

begin "--global --platform claude installs under HOME/.claude/skills"
run "$WORK/not-a-project" --global --platform claude
want_rc 0
want_exact "$FAKE_HOME/.claude/skills" "$V1" "$V1_LIST"
finish

begin "--global --uninstall removes the personal install"
run "$WORK/not-a-project" --global --uninstall
want_rc 0
want_gone "$FAKE_HOME/.agents"
want_gone "$FAKE_HOME/.claude"
finish
FAKE_HOME="$WORK/home"

# ---------------------------------------------------------------------------
# Re-run and update
# ---------------------------------------------------------------------------

begin "re-run with the same source changes nothing"
P=$(installed_project rerun)
before=$(snapshot "$P")
run "$P"
want_rc 0
want_equal "$(snapshot "$P")" "$before" "the project changed on a re-run"
want_out "Version: 1.0.0 -> 1.0.0"
want_out "$NO_CHANGE"
want_out "No files were changed."
want_no_out "uncommitted"
finish

begin "update overwrites untouched files, removes dropped ones, bumps the version"
P=$(installed_project update)
SRC="$V2"; run "$P"
want_rc 0
want_exact "$P/.agents/skills" "$V2" "$V2_LIST"
want_manifest "$P/.agents/skills" 1.1.0 "$V2" "$V2_LIST"
want_gone "$P/.agents/skills/writ-old"
want_out "Version: 1.0.0 -> 1.1.0"
want_out "Added 1, updated 2, kept 0 (customised), removed 2."
finish

begin "no --platform on a re-run updates the existing install, wherever it is"
P=$(installed_project follow --platform claude)
SRC="$V2"; run "$P"
want_rc 0
want_exact "$P/.claude/skills" "$V2" "$V2_LIST"
want_gone "$P/.agents"
finish

begin "update keeps a customised file and reports it"
P=$(installed_project custom)
printf 'my front door\n' > "$P/.agents/skills/writ/SKILL.md"
SRC="$V2"; run "$P"
want_rc 0
want_text "$P/.agents/skills/writ/SKILL.md" "my front door"
want_same "$V2/plugins/writ/skills/writ-spec/scripts/check.py" "$P/.agents/skills/writ-spec/scripts/check.py"
want_out "Added 1, updated 1, kept 1 (customised), removed 2."
want_out "writ/SKILL.md (you changed it)"
want_out "--force"
want_equal "$(head -n 1 "$P/.agents/skills/.writ-manifest")" "# version: 1.1.0" "version header not bumped"
grep -Fxq -- "$(sha "$V1/plugins/writ/skills/writ/SKILL.md")  writ/SKILL.md" "$P/.agents/skills/.writ-manifest" ||
  bad "the manifest dropped the original hash of the customised file"
finish

begin "a customised file is still kept on the next run"
run "$P"
want_rc 0
want_text "$P/.agents/skills/writ/SKILL.md" "my front door"
want_out "Added 0, updated 0, kept 1 (customised), removed 0."
want_out "writ/SKILL.md (you changed it)"
finish

begin "--force overwrites a customised file and says so"
run "$P" --force
want_rc 0
want_same "$V2/plugins/writ/skills/writ/SKILL.md" "$P/.agents/skills/writ/SKILL.md"
want_out "Replaced your version of writ/SKILL.md (--force)."
want_out "Added 0, updated 1, kept 0 (customised), removed 0."
want_manifest "$P/.agents/skills" 1.1.0 "$V2" "$V2_LIST"
run "$P"
want_out "$NO_CHANGE"
finish

begin "a file dropped upstream is deleted when untouched and kept when changed"
P=$(installed_project dropped)
printf 'my guide\n' > "$P/.agents/skills/writ-old/ref/guide.md"
SRC="$V2"; run "$P"
want_rc 0
want_gone "$P/.agents/skills/writ-old/SKILL.md"
want_text "$P/.agents/skills/writ-old/ref/guide.md" "my guide"
want_out "Added 1, updated 2, kept 1 (customised), removed 1."
want_out "writ-old/ref/guide.md (no longer part of Writ, but you changed it)"
want_manifest "$P/.agents/skills" 1.1.0 "$V2" "$V2_LIST"
run "$P"
want_out "$NO_CHANGE"
want_text "$P/.agents/skills/writ-old/ref/guide.md" "my guide"
finish

begin "a file the person already had at a destination path is kept"
P=$(new_project unmanaged); SRC="$V1"
mkdir -p "$P/.agents/skills/writ"
printf 'mine, not from Writ\n' > "$P/.agents/skills/writ/SKILL.md"
run "$P"
want_rc 0
want_text "$P/.agents/skills/writ/SKILL.md" "mine, not from Writ"
want_out "Added 5, updated 0, kept 1 (customised), removed 0."
want_out "writ/SKILL.md (it was here before Writ)"
if grep -q '  writ/SKILL.md$' "$P/.agents/skills/.writ-manifest"; then bad "the manifest claims the person's file"; fi
run "$P"
want_out "Added 0, updated 0, kept 1 (customised), removed 0."
run "$P" --uninstall
want_text "$P/.agents/skills/writ/SKILL.md" "mine, not from Writ"
want_gone "$P/.agents/skills/writ-spec"
finish

begin "a file already identical to the Writ version is adopted, not reported"
P=$(new_project identical); SRC="$V1"
mkdir -p "$P/.agents/skills/writ-spec"
cp "$V1/plugins/writ/skills/writ-spec/SKILL.md" "$P/.agents/skills/writ-spec/SKILL.md"
run "$P"
want_rc 0
want_out "Added 5, updated 0, kept 0 (customised), removed 0."
want_manifest "$P/.agents/skills" 1.0.0 "$V1" "$V1_LIST"
finish

# ---------------------------------------------------------------------------
# Uninstall
# ---------------------------------------------------------------------------

begin "uninstall removes untouched files, keeps changed ones, leaves .writ/ and other skills"
P=$(installed_project uninstall)
mkdir -p "$P/.agents/skills/my-own"
printf 'my own skill\n' > "$P/.agents/skills/my-own/SKILL.md"
printf 'my spec skill\n' > "$P/.agents/skills/writ-spec/SKILL.md"
run "$P" --uninstall
want_rc 0
want_gone "$P/.agents/skills/writ"
want_gone "$P/.agents/skills/writ-old"
want_gone "$P/.agents/skills/writ-spec/scripts"
want_gone "$P/.agents/skills/writ-spec/spec template.md"
want_gone "$P/.agents/skills/.writ-manifest"
want_text "$P/.agents/skills/writ-spec/SKILL.md" "my spec skill"
want_text "$P/.agents/skills/my-own/SKILL.md" "my own skill"
want_text "$P/.writ/specs/a.md" "my spec"
want_out "Removed 5, kept 1 (customised)."
want_out "writ-spec/SKILL.md (you changed it)"
want_out ".writ/"
want_out "uncommitted"
finish

begin "install then uninstall leaves the project as it was (both destinations)"
P=$(new_project roundtrip); SRC="$V1"
before=$(snapshot "$P")
run "$P" --platform claude --platform cursor
run "$P" --uninstall
want_rc 0
want_equal "$(snapshot "$P")" "$before" "leftovers after uninstall: $(snapshot "$P" | tr '\n' ' ')"
finish

begin "uninstall with nothing installed changes nothing"
P=$(new_project nothing); SRC="$V1"
before=$(snapshot "$P")
run "$P" --uninstall
want_rc 0
want_out "Nothing to remove"
want_equal "$(snapshot "$P")" "$before" "the project changed"
finish

# ---------------------------------------------------------------------------
# Dry run
# ---------------------------------------------------------------------------

begin "dry-run fresh install writes nothing and creates no folder"
P=$(new_project dry-fresh); SRC="$V1"
before=$(snapshot "$P")
run "$P" --dry-run --platform claude --platform cursor
want_rc 0
want_equal "$(snapshot "$P")" "$before" "the project changed"
want_out "would add writ/SKILL.md"
want_out "Would add 6, update 0, keep 0 (customised), remove 0."
want_out "Dry run: nothing was changed."
finish

begin "dry-run update writes nothing"
P=$(installed_project dry-update)
printf 'my front door\n' > "$P/.agents/skills/writ/SKILL.md"
before=$(snapshot "$P")
SRC="$V2"; run "$P" --dry-run
want_rc 0
want_equal "$(snapshot "$P")" "$before" "the project changed"
want_out "would update writ-spec/scripts/check.py"
want_out "would remove writ-old/SKILL.md"
want_out "Would add 1, update 1, keep 1 (customised), remove 2."
finish

begin "dry-run --force writes nothing"
run "$P" --dry-run --force
want_rc 0
want_equal "$(snapshot "$P")" "$before" "the project changed"
want_out "would replace your version of writ/SKILL.md"
want_out "Would add 1, update 2, keep 0 (customised), remove 2."
finish

begin "dry-run uninstall writes nothing"
run "$P" --dry-run --uninstall
want_rc 0
want_equal "$(snapshot "$P")" "$before" "the project changed"
want_out "Would remove 5, keep 1 (customised)."
finish

begin "dry-run --global writes nothing under HOME"
FAKE_HOME="$WORK/home-dry"; mkdir -p "$FAKE_HOME"; SRC="$V1"
run "$WORK/not-a-project" --dry-run --global
want_rc 0
want_equal "$(snapshot "$FAKE_HOME")" "" "HOME was written to"
finish
FAKE_HOME="$WORK/home"

# ---------------------------------------------------------------------------
# Writ 0.x (legacy) installs
# ---------------------------------------------------------------------------

for platform in cursor claude codex; do
  begin "a Writ 0.x $platform install stops with exit 3 and its uninstall command"
  P=$(new_project "legacy-$platform"); SRC="$V1"
  mkdir -p "$P/.$platform"; printf '# version: abc1234\n' > "$P/.$platform/.writ-manifest"
  before=$(snapshot "$P")
  run "$P" --platform "$platform"
  want_rc 3
  want_out "$LEGACY_CMD $platform"
  for other in cursor claude codex; do
    [ "$other" = "$platform" ] || want_no_out "$LEGACY_CMD $other"
  done
  want_out ".writ/ (specs, decisions, research)"
  want_out "run this installer again afterwards"
  want_equal "$(snapshot "$P")" "$before" "the project changed"
  finish
done

begin "two Writ 0.x installs print both commands, and stop --uninstall too"
P=$(new_project legacy-two); SRC="$V1"
mkdir -p "$P/.cursor" "$P/.codex"
: > "$P/.cursor/.writ-manifest"; : > "$P/.codex/.writ-manifest"
run "$P" --uninstall
want_rc 3
want_out "$LEGACY_CMD cursor"
want_out "$LEGACY_CMD codex"
want_no_out "$LEGACY_CMD claude"
finish

begin "--ignore-legacy installs next to a Writ 0.x install"
run "$P" --ignore-legacy
want_rc 0
want_exact "$P/.agents/skills" "$V1" "$V1_LIST"
want_text "$P/.cursor/.writ-manifest" ""
finish

# ---------------------------------------------------------------------------
# Refusals
# ---------------------------------------------------------------------------

begin "refuses outside a git repository"
P="$WORK/loose"; mkdir -p "$P"; SRC="$V1"
run "$P"
want_rc 2
want_out "not a git repository"
want_out "--global"
want_equal "$(snapshot "$P")" "" "the folder was written to"
finish

for marker in .agents .claude; do
  begin "outside a git repository, an existing $marker folder is enough"
  P="$WORK/loose-$marker"; mkdir -p "$P/$marker"; SRC="$V1"
  run "$P"
  want_rc 0
  want_exact "$P/.agents/skills" "$V1" "$V1_LIST"
  want_no_out "uncommitted"
  finish
done

begin "refuses inside a Writ source checkout, in every mode"
P=$(new_project writ-checkout); SRC="$V1"
mkdir -p "$P/plugins/writ/skills/writ" "$P/.agents" "$P/.claude" "$P/scripts"
printf 'source skill\n' > "$P/plugins/writ/skills/writ/SKILL.md"
ln -s ../plugins/writ/skills "$P/.agents/skills"
ln -s ../plugins/writ/skills "$P/.claude/skills"
before=$(snapshot "$P")
for args in "" "--platform claude" "--uninstall" "--force --ignore-legacy"; do
  # shellcheck disable=SC2086
  run "$P" $args
  want_rc 2
  want_out "Writ source repository"
done
run "$P/scripts"
want_rc 2
want_equal "$(snapshot "$P")" "$before" "the checkout changed"
finish

begin "refuses a destination that is a link leading outside the project"
P=$(new_project link-out); SRC="$V1"
mkdir -p "$WORK/elsewhere/skills" "$P/.claude"
ln -s "$WORK/elsewhere" "$P/.agents"
ln -s "$WORK/elsewhere/skills" "$P/.claude/skills"
run "$P"
want_rc 2
want_out ".agents is a link that leads outside"
run "$P" --platform claude
want_rc 2
want_out ".claude/skills is a link that leads outside"
want_equal "$(snapshot "$WORK/elsewhere")" "dir  ./skills" "the folder outside the project was written to"
finish

begin "a destination linked to a folder inside the project is written"
P=$(new_project link-in); SRC="$V1"
mkdir -p "$P/.agents/skills" "$P/.claude"
ln -s ../.agents/skills "$P/.claude/skills"
run "$P" --platform claude --platform cursor
want_rc 0
want_exact "$P/.agents/skills" "$V1" "$V1_LIST"
[ -L "$P/.claude/skills" ] || bad ".claude/skills is no longer a link"
finish

begin "never writes through a linked file, even with --force"
P=$(new_project link-file); SRC="$V1"
mkdir -p "$P/.agents/skills/writ" "$WORK/outside"
printf 'outside the project\n' > "$WORK/outside/target.md"
ln -s "$WORK/outside/target.md" "$P/.agents/skills/writ/SKILL.md"
run "$P" --force
want_rc 0
want_text "$WORK/outside/target.md" "outside the project"
[ -L "$P/.agents/skills/writ/SKILL.md" ] || bad "the link was replaced"
want_out "writ/SKILL.md (a link or a folder is in the way)"
want_out "Added 5, updated 0, kept 1 (customised), removed 0."
finish

begin "a manifest path that points out of the destination is never followed"
P=$(installed_project tampered)
printf 'keep me\n' > "$P/victim.txt"
printf '%s  ../../victim.txt\n' "$(sha "$P/victim.txt")" >> "$P/.agents/skills/.writ-manifest"
SRC="$V2"; run "$P"
want_rc 0
want_text "$P/victim.txt" "keep me"
printf '%s  ../../victim.txt\n' "$(sha "$P/victim.txt")" >> "$P/.agents/skills/.writ-manifest"
run "$P" --uninstall
want_rc 0
want_text "$P/victim.txt" "keep me"
finish

begin "bad options exit 2 and write nothing; --help exits 0"
P=$(new_project options); SRC="$V1"
before=$(snapshot "$P")
run "$P" --bogus;            want_rc 2; want_out "Unknown option '--bogus'"
run "$P" --platform emacs;   want_rc 2; want_out "Unknown platform 'emacs'"
run "$P" --platform;         want_rc 2; want_out "--platform needs a name"
run "$P" --help;             want_rc 0; want_out "Usage: install.sh"
want_equal "$(snapshot "$P")" "$before" "the project changed"
finish

begin "in a subfolder of a repository, installs there and says so"
P=$(new_project subfolder); mkdir -p "$P/packages/app"; SRC="$V1"
run "$P/packages/app"
want_rc 0
want_out "Note: this is a subfolder of the git repository"
want_exact "$P/packages/app/.agents/skills" "$V1" "$V1_LIST"
want_gone "$P/.agents"
finish

# ---------------------------------------------------------------------------
# Paths with spaces (the fake sources already live under "src v1" / "src v2")
# ---------------------------------------------------------------------------

begin "install, update, and uninstall work in a path with spaces"
P=$(new_project "my projects/app one"); SRC="$V1"
before=$(snapshot "$P")
run "$P" --platform claude
want_rc 0
want_exact "$P/.claude/skills" "$V1" "$V1_LIST"
printf 'my template\n' > "$P/.claude/skills/writ-spec/spec template.md"
SRC="$V2"; run "$P"
want_rc 0
want_out "Added 1, updated 2, kept 1 (customised), removed 2."
want_out "writ-spec/spec template.md (you changed it)"
want_text "$P/.claude/skills/writ-spec/spec template.md" "my template"
run "$P" --force
want_rc 0
want_exact "$P/.claude/skills" "$V2" "$V2_LIST"
run "$P" --uninstall
want_rc 0
want_equal "$(snapshot "$P")" "$before" "leftovers after uninstall"
finish

# ---------------------------------------------------------------------------
# Download path: the script piped to bash with no WRIT_SRC, as curl would,
# cloning a local repository that stands in for GitHub.
# ---------------------------------------------------------------------------

# Tag v1.0.0 holds v1; the default branch holds v2. Each commit is built from
# its own index, so no file's size or timestamp can hide a change from git.
ORIGIN="$WORK/origin"
git init -q "$ORIGIN" >/dev/null 2>&1
git --git-dir="$ORIGIN/.git" --work-tree="$V1" add -A >/dev/null 2>&1
git --git-dir="$ORIGIN/.git" --work-tree="$V1" commit -q -m v1 >/dev/null 2>&1
git -C "$ORIGIN" tag v1.0.0
rm -f "$ORIGIN/.git/index"
git --git-dir="$ORIGIN/.git" --work-tree="$V2" add -A >/dev/null 2>&1
git --git-dir="$ORIGIN/.git" --work-tree="$V2" commit -q -m v2 >/dev/null 2>&1
if [ "$(git -C "$ORIGIN" show HEAD:VERSION 2>/dev/null)" != "1.1.0" ] || [ "$(git -C "$ORIGIN" show v1.0.0:VERSION 2>/dev/null)" != "1.0.0" ]; then
  printf 'fixture: the stand-in repository was not built correctly\n' >&2
fi

# run_piped <dir> <repo url> <ref> [args...]: like run, but the script arrives on stdin.
run_piped() {
  local dir="$1" url="$2" ref="$3"; shift 3
  RC=0
  OUT=$(cd "$dir" && HOME="$FAKE_HOME" TMPDIR="$WORK/tmp" WRIT_REPO="$url" WRIT_REF="$ref" bash -s -- "$@" < "$INSTALL" 2>&1) || RC=$?
}
mkdir -p "$WORK/tmp"

begin "piped to bash, downloads the default branch and cleans up its temp folder"
P=$(new_project piped)
run_piped "$P" "file://$ORIGIN" "" --platform claude
want_rc 0
want_out "Downloading Writ"
want_exact "$P/.claude/skills" "$V2" "$V2_LIST"
want_manifest "$P/.claude/skills" 1.1.0 "$V2" "$V2_LIST"
want_equal "$(snapshot "$WORK/tmp")" "" "the download folder was left behind"
finish

begin "WRIT_REF picks the tag to download"
P=$(new_project piped-ref)
run_piped "$P" "file://$ORIGIN" v1.0.0
want_rc 0
want_exact "$P/.agents/skills" "$V1" "$V1_LIST"
want_manifest "$P/.agents/skills" 1.0.0 "$V1" "$V1_LIST"
finish

begin "a failed download exits 1 and writes nothing"
P=$(new_project piped-fail)
before=$(snapshot "$P")
run_piped "$P" "file://$WORK/no-such-repo" ""
want_rc 1
want_out "Could not download Writ"
want_out "Git said:"
want_equal "$(snapshot "$P")" "$before" "the project changed"
want_equal "$(snapshot "$WORK/tmp")" "" "the download folder was left behind"
finish

# ---------------------------------------------------------------------------
# The real repo as the source: every SKILL.md present right now arrives.
# ---------------------------------------------------------------------------

begin "installing from this repo delivers every plugins/writ/skills/*/SKILL.md"
P=$(new_project real); SRC="$REPO"
skills=$(cd "$REPO/plugins/writ/skills" 2>/dev/null && ls -d ./*/SKILL.md 2>/dev/null)
[ -n "$skills" ] || bad "this repo has no plugins/writ/skills/*/SKILL.md to install"
run "$P" --platform codex --platform claude
want_rc 0
while IFS= read -r f; do
  [ -n "$f" ] || continue
  [ -f "$P/.agents/skills/$f" ] || bad "missing .agents/skills/${f#./}"
  [ -f "$P/.claude/skills/$f" ] || bad "missing .claude/skills/${f#./}"
done <<< "$skills"
finish

printf '\n%d passed, %d failed\n' "$pass_count" "$fail_count"
[ "$fail_count" -eq 0 ]
