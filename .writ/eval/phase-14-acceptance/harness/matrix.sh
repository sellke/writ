#!/bin/bash
# Clean-room install matrix for Phase 14. Never touches the Writ repo itself.
set -uo pipefail
S=<scratchpad>
REPO=~/Projects/writ
R=$(mktemp -d /tmp/writ-accept.XXXXXX); echo "$R" > $S/root.txt
E=$R/evidence; mkdir -p $E
export GIT_AUTHOR_NAME=accept GIT_AUTHOR_EMAIL=accept@example.invalid GIT_COMMITTER_NAME=accept GIT_COMMITTER_EMAIL=accept@example.invalid

# Sources: a tag cut off this branch, and the previous release tag.
git clone -q --no-hardlinks "$REPO" $R/src-rc && git -C $R/src-rc checkout -q phase/14-front-door-and-distribution
git -C $R/src-rc tag v0.44.0-rc.1
git clone -q --no-hardlinks "$REPO" $R/src-prev && git -C $R/src-prev checkout -q v0.43.0
echo "rc=$(git -C $R/src-rc rev-parse --short HEAD) tag=v0.44.0-rc.1 prev=$(git -C $R/src-prev rev-parse --short HEAD)" | tee $E/sources.txt

make_sample() {  # a small Python app with one real setting
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
  git add -A && git commit -qm initial
}
snapshot() {  # every file except .git, with its hash
  (cd "$1" && find . -type f -not -path './.git/*' -print0 | sort -z | xargs -0 shasum -a 256) > "$2"
}

for P in claude cursor codex; do
  echo "=== $P fresh install"
  make_sample $R/fresh-$P; snapshot $R/fresh-$P $E/$P-pre.sha
  (cd $R/fresh-$P && bash $R/src-rc/scripts/install.sh --platform $P) > $E/$P-install.log 2>&1; echo "exit=$?" >> $E/$P-install.log
  tail -1 $E/$P-install.log
  snapshot $R/fresh-$P $E/$P-post.sha
  python3 $S/tree_check.py $P $R/fresh-$P $R/src-rc $E/$P-tree.json

  echo "=== $P upgrade v0.43.0 -> rc"
  make_sample $R/upd-$P
  (cd $R/upd-$P && bash $R/src-prev/scripts/install.sh --platform $P) > $E/$P-prev-install.log 2>&1; echo "exit=$?" >> $E/$P-prev-install.log
  (cd $R/upd-$P && bash $R/src-rc/scripts/update.sh --platform $P) > $E/$P-update.log 2>&1; echo "exit=$?" >> $E/$P-update.log
  tail -1 $E/$P-update.log
  python3 $S/tree_check.py $P $R/upd-$P $R/src-rc $E/$P-upd-tree.json
  snapshot $R/upd-$P $E/$P-upd-post.sha
  # Upgrade must land on the same files as a fresh install (manifest header aside).
  diff <(grep -v writ-manifest $E/$P-post.sha) <(grep -v writ-manifest $E/$P-upd-post.sha) > $E/$P-fresh-vs-upgrade.diff; echo "fresh-vs-upgrade diff lines: $(wc -l < $E/$P-fresh-vs-upgrade.diff)"

  echo "=== $P uninstall"
  cp -R $R/fresh-$P $R/uninst-$P
  (cd $R/uninst-$P && printf 'n\n' | bash $R/src-rc/scripts/uninstall.sh --platform $P) > $E/$P-uninstall.log 2>&1; echo "exit=$?" >> $E/$P-uninstall.log
  tail -1 $E/$P-uninstall.log
  snapshot $R/uninst-$P $E/$P-uninst.sha
  diff $E/$P-pre.sha $E/$P-uninst.sha > $E/$P-pre-vs-uninstall.diff; echo "pre-vs-uninstall diff lines: $(wc -l < $E/$P-pre-vs-uninstall.diff)"
done
echo "root=$R"
