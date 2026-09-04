#!/usr/bin/env bash
# Tests lint_model_tier() in scripts/lint-skill.sh — the ADR-024 grammar
# (spec 2026-09-03-model-delegation, Story 1: AC-1.4, AC-1.5).
#
# Cases (technical-spec §9):
#   model_tier: anchor|floor            → exit 0, no finding
#   model_tier: orchestration|capability → exit 0, exactly one ⚠️ alias line
#                                          naming the replacement and the
#                                          release that rejects the alias
#   model_tier: fast|n-1                → exit 1, ❌ naming anchor / floor
#   entry_level: high|standard|any      → exit 0, no finding
#   entry_level: max                    → exit 1, ❌ naming high, standard, any
set -euo pipefail

REPO="$(cd "$(dirname "$0")/../.." && pwd)"
LINT="$REPO/scripts/lint-skill.sh"

# The alias window closes at the next minor release after the spec ships
# (VERSION 0.33.0 → spec ships 0.34.0 → aliases rejected 0.35.0). Keep in
# sync with the header comment above lint_model_tier() in lint-skill.sh.
ALIAS_REJECT_RELEASE="0.35.0"

fail() {
  printf 'FAIL: %s\n' "$1" >&2
  exit 1
}

WORK=$(mktemp -d "${TMPDIR:-/tmp}/writ-lint-tier-test.XXXXXX")
trap 'rm -rf "$WORK"' EXIT

# Write a minimal SKILL.md-shaped fixture. Every field the other lint checks
# require (name, verb-phrase description, lifecycle status) is present so the
# only finding a fixture can produce comes from the line under test ($2).
write_fixture() {
  local path="$WORK/$1.md"
  {
    printf '%s\n' '---'
    printf '%s\n' "name: fixture-$1"
    printf '%s\n' 'description: "How to exercise the model_tier lint with one declared value."'
    printf '%s\n' 'status: candidate'
    printf '%s\n' "$2"
    printf '%s\n' '---'
    printf '\n%s\n\n%s\n' '# Fixture' 'Body text with nothing the boundary lint rejects.'
  } > "$path"
  printf '%s' "$path"
}

# Same fixture shape, but the line under test lives in the BODY (after the
# closing `---`), not the frontmatter. $2 is one or more body lines. Used to
# pin the two scan modes: model_tier is matched across the whole raw file,
# entry_level only where it starts a line (`^entry_level:`).
write_body_fixture() {
  local path="$WORK/$1.md"
  {
    printf '%s\n' '---'
    printf '%s\n' "name: fixture-$1"
    printf '%s\n' 'description: "How to exercise the model_tier lint with one declared value."'
    printf '%s\n' 'status: candidate'
    printf '%s\n' '---'
    printf '\n%s\n\n%s\n' '# Fixture' "$2"
  } > "$path"
  printf '%s' "$path"
}

count_of() {  # $1 needle, $2 haystack
  local n
  n=$(printf '%s\n' "$2" | grep -cF -- "$1" || true)
  printf '%s' "$n"
}

# Exit 0 and neither ❌ nor ⚠️ in the output.
assert_clean() {  # $1 label, $2 frontmatter line
  local f out
  f=$(write_fixture "$1" "$2")
  out=$(bash "$LINT" "$f") || fail "$1: expected exit 0 for '$2'"
  [ "$(count_of '❌' "$out")" = 0 ] || fail "$1: unexpected ❌ finding for '$2': $out"
  [ "$(count_of '⚠️' "$out")" = 0 ] || fail "$1: unexpected ⚠️ warning for '$2': $out"
}

# Exit 0, exactly one ⚠️ line, naming the replacement and the rejection release.
assert_alias_warned() {  # $1 label, $2 frontmatter line, $3 replacement
  local f out
  f=$(write_fixture "$1" "$2")
  out=$(bash "$LINT" "$f") || fail "$1: alias '$2' must exit 0 during the alias window"
  [ "$(count_of '⚠️' "$out")" = 1 ] || fail "$1: expected exactly one ⚠️ line for '$2': $out"
  [ "$(count_of '❌' "$out")" = 0 ] || fail "$1: alias '$2' must not produce a ❌ finding: $out"
  printf '%s\n' "$out" | grep -F -- '⚠️' | grep -qF -- "'$3'" \
    || fail "$1: ⚠️ line must name the replacement '$3': $out"
  printf '%s\n' "$out" | grep -F -- '⚠️' | grep -qF -- "$ALIAS_REJECT_RELEASE" \
    || fail "$1: ⚠️ line must name the rejection release $ALIAS_REJECT_RELEASE: $out"
}

# Exit 1 and a ❌ line that names every allowed value in $3...
# Runs the lint once: the `if out=$(...)` form captures output and tests the
# exit code in the same invocation.
assert_rejected() {  # $1 label, $2 frontmatter line, $3.. quoted allowed values
  local f out label="$1" line="$2"
  shift 2
  f=$(write_fixture "$label" "$line")
  if out=$(bash "$LINT" "$f" 2>&1); then
    fail "$label: expected exit 1 for '$line': $out"
  fi
  assert_names_allowed "$label" "$line" "$out" "$@"
}

# Shared tail of the rejection asserts: at least one ❌ line, naming each
# allowed value in $4...
assert_names_allowed() {  # $1 label, $2 line, $3 lint output, $4.. allowed values
  local label="$1" line="$2" out="$3"
  shift 3
  [ "$(count_of '❌' "$out")" -ge 1 ] || fail "$label: expected a ❌ finding for '$line': $out"
  for allowed in "$@"; do
    printf '%s\n' "$out" | grep -F -- '❌' | grep -qF -- "'$allowed'" \
      || fail "$label: ❌ line must name '$allowed': $out"
  done
}

# Body-placed variants of assert_clean / assert_rejected. The line under test
# is in the markdown body, not the `---` frontmatter.
assert_body_clean() {  # $1 label, $2 body line(s)
  local f out
  f=$(write_body_fixture "$1" "$2")
  out=$(bash "$LINT" "$f" 2>&1) || fail "$1: expected exit 0 for body '$2': $out"
  [ "$(count_of '❌' "$out")" = 0 ] || fail "$1: unexpected ❌ finding for body '$2': $out"
  [ "$(count_of '⚠️' "$out")" = 0 ] || fail "$1: unexpected ⚠️ warning for body '$2': $out"
}

assert_body_rejected() {  # $1 label, $2 body line(s), $3.. quoted allowed values
  local f out label="$1" body="$2"
  shift 2
  f=$(write_body_fixture "$label" "$body")
  if out=$(bash "$LINT" "$f" 2>&1); then
    fail "$label: expected exit 1 for body '$body': $out"
  fi
  assert_names_allowed "$label" "$body" "$out" "$@"
}

# ----- model_tier: the two live values -----
assert_clean tier-anchor 'model_tier: anchor'
assert_clean tier-floor  'model_tier: floor'

# ----- model_tier: the two warned aliases -----
assert_alias_warned tier-orchestration 'model_tier: orchestration' anchor
assert_alias_warned tier-capability    'model_tier: capability'    floor

# ----- model_tier: rejected values -----
assert_rejected tier-fast 'model_tier: fast' anchor floor
assert_rejected tier-n1   'model_tier: n-1'  anchor floor

# ----- entry_level: the three live values -----
assert_clean entry-high     'entry_level: high'
assert_clean entry-standard 'entry_level: standard'
assert_clean entry-any      'entry_level: any'

# ----- entry_level: rejected values -----
assert_rejected entry-max 'entry_level: max' high standard any
# The value match is case-sensitive: 'High' is not 'high'. Story 5's entry-level
# routing relies on the lowercase grammar being the only one that passes.
assert_rejected entry-High 'entry_level: High' high standard any

# ----- scan mode: model_tier is matched across the WHOLE raw file -----
# An agent's config block is a fenced block in the body, not `---` frontmatter,
# so a bad value inside a fence must still be caught.
assert_body_rejected tier-fast-in-fence "$(printf '%s\n' \
  '## Agent Configuration' '' '```' 'model_tier: fast' '```')" anchor floor

# ----- scan mode: entry_level is anchored on ^entry_level: -----
# A prose mention mid-line, or an indented one, is not a declaration.
assert_body_clean entry-prose-midline 'Prose says entry_level: nonsense.'
assert_body_clean entry-indented      '  entry_level: bogus'

printf 'OK lint_model_tier fixtures\n'
