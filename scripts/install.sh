#!/usr/bin/env bash
# Writ installer. Adds, updates, or removes the Writ skills in a project.
#
#   bash <(curl -fsSL https://raw.githubusercontent.com/sellke/writ/main/scripts/install.sh)
#
# Run it from your project folder. Run it again at any time to update.
# It only touches the skill files it installed, which it lists in a
# .writ-manifest file next to them. It never changes a file you edited and
# never touches .writ/.
#
# Environment:
#   WRIT_SRC   install from this local Writ checkout instead of downloading
#   WRIT_REF   branch or tag to download (default: the repository's default)
#   WRIT_REPO  repository to download from
#
# Exit codes: 0 done. 1 something failed. 2 refused, or bad options.
#             3 an older Writ (0.x) install has to be removed first.
set -euo pipefail
unset CDPATH

WRIT_REPO="${WRIT_REPO:-https://github.com/sellke/writ.git}"
WRIT_REF="${WRIT_REF:-}"
LEGACY_UNINSTALL="https://raw.githubusercontent.com/sellke/writ/v0.49.0/scripts/uninstall.sh"

DRY_RUN=false FORCE=false GLOBAL=false UNINSTALL=false IGNORE_LEGACY=false
WANT_AGENTS=false WANT_CLAUDE=false IN_GIT=false
ROOT="" SHOWN_ROOT="" TMP_SRC="" SRC_SKILLS="" VERSION="" FILES="" CHANGES=0

say() { printf '%s\n' "$*"; }
die() { local code="$1"; shift; printf 'Error: %s\n' "$*" >&2; exit "$code"; }

usage() {
  cat <<'EOF'
Usage: install.sh [--platform <claude|cursor|codex>]... [--global] [--dry-run]
                  [--force] [--uninstall] [--ignore-legacy] [--help]

Installs or updates the Writ skills in the current project. Safe to run again.

  --platform <name>  Tool to install for. Repeat it to install for several.
                       cursor, codex   .agents/skills (the default)
                       claude          .claude/skills
                     With no --platform, a re-run updates what is installed.
  --global           Install for all your projects, under your home folder.
  --dry-run          Show what would happen. Change nothing.
  --force            Replace files you changed with the Writ versions.
  --uninstall        Remove the Writ skills. Files you changed are kept.
  --ignore-legacy    Install even if an older Writ (0.x) install is present.
  --help             Show this help.
EOF
}

hash_file() {
  if command -v shasum >/dev/null 2>&1; then shasum -a 256 "$1"; else sha256sum "$1"; fi | cut -d' ' -f1
}

add_platform() {
  case "$1" in
    cursor|codex) WANT_AGENTS=true ;;
    claude)       WANT_CLAUDE=true ;;
    *) die 2 "Unknown platform '$1'. Use claude, cursor, or codex." ;;
  esac
}

# Refuse the wrong folder, and stop for a Writ 0.x install, before any write.
check_project() {
  local top found="" p
  top=$(git -C "$ROOT" rev-parse --show-toplevel 2>/dev/null || true)
  if [ -d "$ROOT/plugins/writ/skills" ] || [ -d "${top:-$ROOT}/plugins/writ/skills" ]; then
    die 2 "This is the Writ source repository, where the skill folders are links to the source. Run the installer in another project."
  fi
  if [ -n "$top" ] || [ -e "$ROOT/.git" ]; then
    IN_GIT=true
  elif [ ! -e "$ROOT/.agents" ] && [ ! -e "$ROOT/.claude" ]; then
    die 2 "This folder is not a git repository, so it does not look like a project: $ROOT. Go to your project folder and run this again, or add --global to install for all your projects."
  fi
  if ! $IGNORE_LEGACY; then
    for p in cursor claude codex; do
      [ ! -f "$ROOT/.$p/.writ-manifest" ] || found="$found $p"
    done
    if [ -n "$found" ]; then
      {
        say "This project has an older Writ (0.x) install. Remove it first by running, in this folder:"
        for p in $found; do say "  bash <(curl -s $LEGACY_UNINSTALL) --platform $p"; done
        say "That keeps everything under .writ/ (specs, decisions, research); run this installer again afterwards."
      } >&2
      exit 3
    fi
  fi
  if [ -n "$(git -C "$ROOT" rev-parse --show-prefix 2>/dev/null || true)" ]; then
    say "Note: this is a subfolder of the git repository at $top. The skills go in this subfolder. Most tools look for them at the top, so run this from there unless you mean it."
  fi
}

# Never write through a destination that is a link leading out of the project.
check_dest() {
  local part real
  for part in "${1%/*}" "$1"; do
    [ -L "$ROOT/$part" ] || continue
    real=$(cd "$ROOT/$part" 2>/dev/null && pwd -P) || real=""
    case "$real/" in
      "$ROOT"/*) ;;
      *) die 2 "$SHOWN_ROOT$part is a link that leads outside $ROOT, so nothing was written. Replace the link with a real folder, then run this again." ;;
    esac
  done
}

# Sets SRC_SKILLS, VERSION, and FILES (every file to install, one per line).
find_source() {
  local src="${WRIT_SRC:-}" self="${BASH_SOURCE[0]:-}" err
  if [ -z "$src" ] && [ -f "$self" ] && [ -d "$(dirname "$self")/../plugins/writ/skills" ]; then
    src="$(dirname "$self")/.."   # run from a Writ checkout: install from it
  fi
  if [ -z "$src" ]; then
    command -v git >/dev/null 2>&1 || die 1 "git is needed to download Writ. Install git, then run this again."
    TMP_SRC=$(mktemp -d "${TMPDIR:-/tmp}/writ-install.XXXXXX")
    trap 'rm -rf "$TMP_SRC"' EXIT
    say "Downloading Writ..."
    set -- --quiet --depth 1
    [ -z "$WRIT_REF" ] || set -- "$@" --branch "$WRIT_REF"
    err=$(GIT_TERMINAL_PROMPT=0 git clone "$@" "$WRIT_REPO" "$TMP_SRC" 2>&1) ||
      die 1 "Could not download Writ from $WRIT_REPO${WRIT_REF:+ ($WRIT_REF)}. Check your connection, then run this again. Git said: $(tail -n 1 <<< "$err")"
    src="$TMP_SRC"
  fi
  [ -d "$src/plugins/writ/skills" ] || die 1 "No Writ skills found in $src (expected plugins/writ/skills there)."
  SRC_SKILLS=$(cd "$src/plugins/writ/skills" && pwd)
  VERSION="unknown"
  [ ! -f "$src/VERSION" ] || VERSION=$(tr -d ' \t\r\n' < "$src/VERSION")
  FILES=$(cd "$SRC_SKILLS" && find . -type f ! -name '*.pyc' ! -name .DS_Store ! -path '*/__pycache__/*' |
    sed 's|^\./||' | LC_ALL=C sort)
  [ -n "$FILES" ] || die 1 "No Writ skills found in $src (plugins/writ/skills is empty)."
}

# Prints the hash the current manifest holds for path $1, or nothing.
old_hash() {
  local line
  [ -f "$MANIFEST" ] || return 0
  while IFS= read -r line || [ -n "$line" ]; do
    if [ "${line#*  }" = "$1" ]; then say "${line%%  *}"; return 0; fi
  done < "$MANIFEST"
}

# True when no link sits at $1 or at a folder above it inside the destination.
plain_path() {
  local p="$1"
  while :; do
    [ ! -L "$DEST/$p" ] || return 1
    case "$p" in */*) p="${p%/*}" ;; *) return 0 ;; esac
  done
}

record() { NEW_MANIFEST="$NEW_MANIFEST$1  $2"$'\n'; }
step() { if $DRY_RUN; then say "    would $1 $2"; fi; }

# keep <path> <why> <hash>: leave the person's file alone and report it. A
# non-empty hash stays in the manifest, so the file still counts as changed.
keep() {
  KEPT=$((KEPT + 1))
  KEPT_LIST="$KEPT_LIST    $1 ($2)"$'\n'
  [ -z "$3" ] || record "$3" "$1"
}

# put <verb> <path>: copy one source file into the destination.
put() {
  local dst="$DEST/$2"
  step "$1" "$2"
  CHANGES=$((CHANGES + 1))
  $DRY_RUN && return 0
  { mkdir -p "$(dirname "$dst")" && cp "$SRC_SKILLS/$2" "$dst.writ-tmp" && mv -f "$dst.writ-tmp" "$dst"; } ||
    die 1 "Could not write $dst."
}

# Remove the folders above removed file $1 that are now empty, up to the destination.
prune() {
  local p="$1"
  while case "$p" in */*) true ;; *) false ;; esac; do
    p="${p%/*}"
    rmdir "$DEST/$p" 2>/dev/null || break
  done
}

# Install, update, or uninstall one destination ($1, relative to ROOT).
sync_dest() {
  DEST="$ROOT/$1"; MANIFEST="$DEST/.writ-manifest"
  local shown="$SHOWN_ROOT$1" tools="Cursor and Codex" old_version="none" f new old cur line p
  [ "$1" = ".agents/skills" ] || tools="Claude Code"
  ADDED=0 UPDATED=0 KEPT=0 REMOVED=0 KEPT_LIST="" NEW_MANIFEST="" CAN_FORCE=false
  if [ -f "$MANIFEST" ]; then
    old_version=$(sed -n '/^# version: /{s///p;q;}' "$MANIFEST")
  elif $UNINSTALL; then
    say "No Writ install found in $shown. Nothing to remove."
    return 0
  fi
  if $UNINSTALL; then
    say "Removing Writ ${old_version:-unknown} from $shown ($tools)"
  else
    say "Writ for $tools, in $shown"
    say "  Version: ${old_version:-unknown} -> $VERSION"
    while IFS= read -r f; do
      new=$(hash_file "$SRC_SKILLS/$f"); old=$(old_hash "$f")
      if ! plain_path "$f" || [ -d "$DEST/$f" ]; then
        keep "$f" "a link or a folder is in the way" "$old"
      elif [ ! -e "$DEST/$f" ]; then
        put add "$f"; ADDED=$((ADDED + 1)); record "$new" "$f"
      else
        cur=$(hash_file "$DEST/$f")
        if [ "$cur" = "$new" ]; then        # already the Writ version: nothing to do
          record "$new" "$f"
        elif [ "$cur" = "$old" ]; then      # untouched since install: safe to update
          put update "$f"; UPDATED=$((UPDATED + 1)); record "$new" "$f"
        elif $FORCE; then
          put "replace your version of" "$f"; UPDATED=$((UPDATED + 1)); record "$new" "$f"
          $DRY_RUN || say "    Replaced your version of $f (--force)."
        else
          CAN_FORCE=true
          if [ -n "$old" ]; then keep "$f" "you changed it" "$old"; else keep "$f" "it was here before Writ" ""; fi
        fi
      fi
    done <<< "$FILES"
  fi
  # Files the manifest lists that Writ no longer ships (on uninstall: all of them).
  if [ -f "$MANIFEST" ]; then
    while IFS= read -r line || [ -n "$line" ]; do
      case "$line" in '#'*|'') continue ;; esac
      old="${line%%  *}"; p="${line#*  }"
      case "$p" in /*|*..*|"$line") continue ;; esac   # never follow a path out of the destination
      if ! $UNINSTALL && grep -Fxq -- "$p" <<< "$FILES"; then continue; fi
      [ -e "$DEST/$p" ] || [ -L "$DEST/$p" ] || continue
      if plain_path "$p" && [ -f "$DEST/$p" ] && [ "$(hash_file "$DEST/$p")" = "$old" ]; then
        step remove "$p"; REMOVED=$((REMOVED + 1)); CHANGES=$((CHANGES + 1))
        $DRY_RUN || { rm -f "$DEST/$p"; prune "$p"; }
      elif $UNINSTALL; then
        keep "$p" "you changed it" ""
      else
        keep "$p" "no longer part of Writ, but you changed it" ""
      fi
    done < "$MANIFEST"
  fi
  if $UNINSTALL; then
    if ! $DRY_RUN; then
      rm -f "$MANIFEST"   # then the skills folder and its parent, only if nothing else is in them
      if rmdir "$DEST" 2>/dev/null; then rmdir "$(dirname "$DEST")" 2>/dev/null || true; fi
    fi
    say "  $REMOVED_WORD $REMOVED, $KEPT_WORD $KEPT (customised)."
  else
    if ! $DRY_RUN; then
      mkdir -p "$DEST"
      printf '# version: %s\n# Written by the Writ installer. It lists each installed file and its checksum. Leave it in place.\n%s' \
        "$VERSION" "$NEW_MANIFEST" > "$MANIFEST.writ-tmp"
      mv -f "$MANIFEST.writ-tmp" "$MANIFEST"
    fi
    say "  $ADDED_WORD $ADDED, $UPDATED_WORD $UPDATED, $KEPT_WORD $KEPT (customised), $REMOVED_WORD $REMOVED."
  fi
  if [ "$KEPT" -gt 0 ]; then
    say "  Kept as you have them:"
    printf '%s' "$KEPT_LIST"
    if $CAN_FORCE; then say "  To replace files you changed with the Writ versions, run this again with --force."; fi
  fi
}

main() {
  local dest dests=""
  while [ $# -gt 0 ]; do
    case "$1" in
      --platform)
        [ $# -ge 2 ] || die 2 "--platform needs a name: claude, cursor, or codex."
        add_platform "$2"; shift ;;
      --platform=*)    add_platform "${1#*=}" ;;
      --global)        GLOBAL=true ;;
      --dry-run)       DRY_RUN=true ;;
      --force)         FORCE=true ;;
      --uninstall)     UNINSTALL=true ;;
      --ignore-legacy) IGNORE_LEGACY=true ;;
      --help|-h)       usage; exit 0 ;;
      *) die 2 "Unknown option '$1'. Run with --help to see the options." ;;
    esac
    shift
  done
  command -v shasum >/dev/null 2>&1 || command -v sha256sum >/dev/null 2>&1 ||
    die 1 "Neither shasum nor sha256sum is installed, and one of them is needed."
  ADDED_WORD="Added" UPDATED_WORD="updated" KEPT_WORD="kept" REMOVED_WORD="removed"
  if $UNINSTALL; then REMOVED_WORD="Removed"; fi
  if $DRY_RUN; then
    ADDED_WORD="Would add" UPDATED_WORD="update" KEPT_WORD="keep" REMOVED_WORD="remove"
    if $UNINSTALL; then REMOVED_WORD="Would remove"; fi
  fi

  if $GLOBAL; then
    if [ -z "${HOME:-}" ] || [ ! -d "$HOME" ]; then die 2 "--global needs a home folder, and HOME is not set to one."; fi
    ROOT=$(cd "$HOME" && pwd -P)
    # shellcheck disable=SC2088
    SHOWN_ROOT="~/"   # literal text for the report, not a path
  else
    ROOT=$(pwd -P)
    check_project
  fi
  if ! $WANT_AGENTS && ! $WANT_CLAUDE; then
    # No --platform: every place Writ is already installed, else .agents/skills.
    if [ -f "$ROOT/.agents/skills/.writ-manifest" ]; then WANT_AGENTS=true; fi
    if [ -f "$ROOT/.claude/skills/.writ-manifest" ]; then WANT_CLAUDE=true; fi
    $WANT_CLAUDE || WANT_AGENTS=true
  fi
  if $WANT_AGENTS; then dests=".agents/skills"; fi
  if $WANT_CLAUDE; then dests="$dests .claude/skills"; fi
  for dest in $dests; do check_dest "$dest"; done
  $UNINSTALL || find_source
  for dest in $dests; do sync_dest "$dest"; done

  say ""
  if $DRY_RUN; then
    say "Dry run: nothing was changed."
  elif $UNINSTALL; then
    say "Nothing under .writ/ (specs, decisions, research) was touched."
    if $IN_GIT && [ "$CHANGES" -gt 0 ]; then say "Nothing was committed. The removals are uncommitted, and committing them is your call."; fi
  else
    if [ "$CHANGES" -eq 0 ]; then
      say "No files were changed."
    elif $IN_GIT; then
      say "Nothing was committed. The new and changed files are uncommitted, and committing them is your call."
    fi
    say "Restart or reload your tool, then type /writ (Cursor, Claude Code) or \$writ (Codex)."
  fi
}

main "$@"
