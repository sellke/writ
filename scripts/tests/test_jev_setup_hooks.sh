#!/usr/bin/env bash
# Story 6 of 2026-09-25-jev-judgment-pilot: pins the /create-spec Step 2.6c
# one-time Jev setup sub-step, the item-3 exception for it, and a real
# status -> setup -> status round trip in a temp repo.
# No network: keys stripped except one fake key; no request is ever built.
# [AC-6.3, AC-6.4, AC-6.5]
set -euo pipefail

REPO="$(cd "$(dirname "$0")/../.." && pwd)"
CREATE="$REPO/commands/create-spec.md"
LEAN="$REPO/commands/create-spec.lean.md"
SCRIPT="$REPO/scripts/jev-judge.py"

fail() { printf 'FAIL: %s\n' "$1" >&2; exit 1; }
ok() { printf 'PASS: %s\n' "$1"; }

STEP_26C="$(awk '/^#### Step 2.6c:/{f=1} /^#### Step 2.7:/{f=0} f' "$CREATE")"
[ -n "$STEP_26C" ] || fail "create-spec.md must have Step 2.6c"

# --- The sub-step: at most 4 lines, placed after the Jev paragraph [AC-6.5] --
SUBSTEP="$(printf '%s\n' "$STEP_26C" | awk '/^\*\*Jev setup \(once\)\.\*\*/{f=1} f&&/^$/{exit} f')"
[ -n "$SUBSTEP" ] || fail "Step 2.6c must carry a **Jev setup (once).** sub-step"
LINES="$(printf '%s\n' "$SUBSTEP" | wc -l | tr -d ' ')"
[ "$LINES" -le 4 ] || fail "the setup sub-step must be at most 4 lines (got $LINES)"
python3 - "$CREATE" <<'PY' || fail "setup sub-step must sit after the Jev paragraph, before item 1"
import sys
text = open(sys.argv[1], encoding="utf-8").read()
c = text.find("#### Step 2.6c:")
jev = text.find("**Jev first (opt-in).**", c)
setup = text.find("**Jev setup (once).**", c)
llm = text.find("1. **LLM pass", c)
assert -1 < c < jev < setup < llm, (c, jev, setup, llm)
PY
ok "setup sub-step: $LINES lines, after the Jev paragraph, before item 1"

has() { printf '%s\n' "$SUBSTEP" | grep -Fq -- "$1" || fail "setup sub-step must contain: $1"; }
# --- Prompt and mapping [AC-6.3] --------------------------------------------
has 'no_config_line'
has 'interactive run'
has 'one AskQuestion titled "Jev judgment provider"'
has 'TypeSafe direct / Vercel AI Gateway / Not now / Never'
has 'python3 scripts/jev-judge.py setup --provider'
has '`typesafe` / `vercel-gateway` / nothing / `none`'
has 'print its export line'
has 'take the Otherwise path this run'
# --- Never collect a key --------------------------------------------------------
has 'export the key in your shell'
has 'never paste a key into chat'
has 'write it nowhere'
has 'rotate it'
ok "setup sub-step: one titled AskQuestion, four options mapped to setup, export line, never-paste"

# --- No-prompt cases [AC-6.4] ---------------------------------------------------
has '(not `--recommend`)'
has '`--recommend`, non-interactive, or `none`: one `jev:` note'
has '`no_api_key`: note `jev: unverifiable (no_api_key) — export <VAR>`; no re-prompt'
ok "setup sub-step: --recommend / non-interactive / none are notes; no_api_key has no re-prompt"

# --- Item-3 sentence exempts only the setup prompt [AC-6.5] -------------------
printf '%s\n' "$STEP_26C" \
  | grep -Fq 'does **not** open an AskQuestion gate (the one-time Jev setup prompt is the only exception).' \
  || fail "item 3 must exempt the one-time Jev setup prompt from the no-AskQuestion rule"
[ "$(printf '%s\n' "$STEP_26C" | grep -c 'AskQuestion')" -eq 2 ] \
  || fail "Step 2.6c must name AskQuestion only in the setup sub-step and the item-3 exception"
ok "item 3: no AskQuestion gate, one-time setup prompt the only exception"

# --- Lean sibling stays the no-Jev baseline ---------------------------------------
if grep -Fq 'jev-judge.py setup' "$LEAN"; then
  fail "create-spec.lean.md must not gain the setup sub-step (no-Jev baseline arm)"
fi
ok "create-spec.lean.md unchanged by the setup sub-step"

# --- status -> setup -> status round trip [AC-6.3] ------------------------------
TMP="$(mktemp -d)"
trap 'rm -rf "$TMP"' EXIT
mkdir -p "$TMP/.writ"
printf '# Config\n\n## Conventions\n\n- **Default Branch:** main\n' > "$TMP/.writ/config.md"
FAKE="sk-jev-FAKE-hooks-DO-NOT-PRINT"
run() {
  env -u TYPESAFE_API_KEY -u AI_GATEWAY_API_KEY -u VERCEL_OIDC_TOKEN -u WRIT_JEV_REPLAY \
    "$@"
}
OUT="$(run AI_GATEWAY_API_KEY="$FAKE" python3 "$SCRIPT" status --repo "$TMP")"
printf '%s\n' "$OUT" | sed -n 2p | grep -Fxq 'reason: no_config_line' \
  || fail "status before setup must report no_config_line: $OUT"
OUT="$(run python3 "$SCRIPT" setup --provider vercel-gateway --repo "$TMP")"
[ "$(printf '%s\n' "$OUT" | head -1)" = "pass" ] || fail "setup must print pass: $OUT"
printf '%s\n' "$OUT" | grep -Fxq 'reason: configured' || fail "setup must print reason: configured"
printf '%s\n' "$OUT" | tail -1 | grep -Fq 'export=AI_GATEWAY_API_KEY' \
  || fail "setup summary must name AI_GATEWAY_API_KEY"
OUT="$(run AI_GATEWAY_API_KEY="$FAKE" python3 "$SCRIPT" status --repo "$TMP")"
[ "$(printf '%s\n' "$OUT" | head -1)" = "pass" ] || fail "status after setup with a key must pass: $OUT"
[ "$(grep -c 'Judgment Provider' "$TMP/.writ/config.md")" -eq 1 ] || fail "exactly one config line"
if grep -rFq "$FAKE" "$TMP" || printf '%s\n' "$OUT" | grep -Fq "$FAKE"; then
  fail "the key must never reach output or files"
fi
ok "status no_config_line -> setup vercel-gateway -> status pass; key never written"

printf '\nAll Jev setup-prompt wiring assertions passed.\n'
