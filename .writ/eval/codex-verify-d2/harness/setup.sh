#!/bin/bash
# setup.sh <writ-checkout> : builds a temp root with one installed sample app per
# condition (rubric.md -> Conditions) and prints the root. Never touches the checkout.
set -euo pipefail
H=$(cd "$(dirname "$0")" && pwd)
REPO=$1
R=$(mktemp -d /tmp/d2.XXXXXX)
export GIT_AUTHOR_NAME=accept GIT_AUTHOR_EMAIL=accept@example.invalid GIT_COMMITTER_NAME=accept GIT_COMMITTER_EMAIL=accept@example.invalid
git -C "$REPO" rev-parse --short HEAD > "$R/source-rev.txt"

make_sample() {  # the acceptance pass's sample app (phase-14-acceptance/harness/matrix.sh)
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

make_sample "$R/apps/control"
for v in base pd-first pd-last intro-op; do
  mkdir -p "$R/src/$v"
  git -C "$REPO" archive HEAD | tar -x -C "$R/src/$v"
  python3 "$H/variants.py" "$R/src/$v/codex/AGENTS.md.template" "$v" > "$R/tmpl"
  mv "$R/tmpl" "$R/src/$v/codex/AGENTS.md.template"
  make_sample "$R/apps/$v"
  (cd "$R/apps/$v" && bash "$R/src/$v/scripts/install.sh" --platform codex < /dev/null) > "$R/install-$v.log" 2>&1
  # The installed Writ block must be the variant template, byte for byte.
  awk '/^<!-- writ:end -->$/{f=0} f; /^<!-- writ:start -->$/{f=1}' "$R/apps/$v/AGENTS.md" > "$R/block-$v.md"
  cmp -s "$R/block-$v.md" "$R/src/$v/codex/AGENTS.md.template" || { echo "block mismatch: $v" >&2; exit 1; }
  git -C "$R/apps/$v" status --short | head -3 > "$R/status-$v.txt"
done
mkdir -p "$R/grader" "$R/runs" "$R/w"
echo "$R"
