#!/bin/bash
# recheck-uninstall.sh <writ-checkout> <evidence-dir> : matrix.sh's uninstall
# step rerun on HEAD after the D8 and refspec fixes, once per platform in each
# mode. The sample app gets a bare remote so install adds its refs/notes/writ
# refspecs. Never touches the checkout.
set -uo pipefail
REPO=$1; E=$2; mkdir -p "$E"
R=$(mktemp -d /tmp/writ-recheck.XXXXXX)
export GIT_AUTHOR_NAME=accept GIT_AUTHOR_EMAIL=accept@example.invalid GIT_COMMITTER_NAME=accept GIT_COMMITTER_EMAIL=accept@example.invalid
mkdir -p "$R/src" && git -C "$REPO" archive HEAD | tar -x -C "$R/src"
echo "source=$(git -C "$REPO" rev-parse --short HEAD)" > "$E/sources.txt"
git init -q --bare "$R/remote.git"

make_sample() {  # matrix.sh's sample app, plus a remote
  mkdir -p "$1/src" "$1/tests" && cd "$1" && git init -q
  cat > src/settings.py <<'PY'
"""User settings for the demo app."""
DEFAULTS = {"theme": "light", "page_size": 20}

def get(name, overrides=None):
    merged = dict(DEFAULTS, **(overrides or {}))
    return merged[name]
PY
  cat > tests/test_settings.py <<'PY'
from src.settings import get

def test_default_theme():
    assert get("theme") == "light"
PY
  printf '# Demo app\n\nA tiny app used to test Writ installs.\n' > README.md
  git add -A && git commit -qm initial && git remote add origin "$R/remote.git"
}
snapshot() {  # every file except .git, with its hash
  (cd "$1" && find . -type f -not -path './.git/*' -print0 | sort -z | xargs -0 shasum -a 256) > "$2"
}
refspecs() { git -C "$1" config --get-regexp '^remote\.origin\.(fetch|push)$' || true; }

for P in claude cursor codex; do
  for mode in default include-writ; do
    d=$R/$P-$mode; x=$E/$P-$mode
    make_sample "$d"; snapshot "$d" "$x-pre.sha"; refspecs "$d" > "$x-pre.refspecs"
    (cd "$d" && bash "$R/src/scripts/install.sh" --platform $P < /dev/null) > "$x-install.log" 2>&1; echo "exit=$?" >> "$x-install.log"
    refspecs "$d" > "$x-installed.refspecs"
    flags=(); [ $mode = include-writ ] && flags=(--include-writ)
    (cd "$d" && printf 'n\n' | bash "$R/src/scripts/uninstall.sh" --platform $P ${flags[@]+"${flags[@]}"}) > "$x-uninstall.log" 2>&1; echo "exit=$?" >> "$x-uninstall.log"
    snapshot "$d" "$x-post.sha"; refspecs "$d" > "$x-post.refspecs"
    diff "$x-pre.sha" "$x-post.sha" > "$x-pre-vs-uninstall.diff"
    diff "$x-pre.refspecs" "$x-post.refspecs" > "$x-refspecs.diff"
    echo "$P $mode: install $(tail -1 "$x-install.log"), uninstall $(tail -1 "$x-uninstall.log"), files differing $(grep -c '^[<>]' "$x-pre-vs-uninstall.diff"), refspec lines differing $(grep -c '^[<>]' "$x-refspecs.diff"), refspecs added by install $(grep -c . "$x-installed.refspecs")"
  done
done
echo "root=$R"
