#!/usr/bin/env bash
# Tests the three Stage 1 dead-end regression checks in scripts/eval.sh
# (spec 2026-09-05-phase11-repair-and-baseline, Story 1, Business Rule 6):
#
#   check_referenced_paths      — every backticked `*.md` path a command names
#                                 resolves, is created by a named command
#                                 (allowlisted with a reason), or fails   [AC-1.1]
#   check_skill_manifest_parity — skills/<name>/SKILL.md on disk and the
#                                 `skills:` section of .writ/manifest.yaml
#                                 name the same set                        [AC-1.2]
#   check_knowledge_integrity   — no .writ/knowledge/**/*.md carries a bullet
#                                 whose content is a single character, or an
#                                 empty ## TL;DR                            [AC-1.3]
#
# Each check must BLOCK (add_finding, exit 1) and name the file and line.
# Each has a red fixture (the dead-end class it exists to catch) and a green
# fixture (the repaired shape passes with exit 0). A check that only notes,
# or that names no location, fails these tests. check_referenced_paths also
# polices its own allowlist — a row missing a field, or a stale row nothing
# references — and those two self-checks have fixtures here too.
#
# Harness: scripts/eval.sh derives PROJECT_ROOT from its own directory, so
# copying it into a temp `scripts/` dir alongside synthetic content exercises
# the real check against a synthetic tree — the recipe test_eval_length_caps.sh
# uses. No flag, no environment variable, no mutation of the real repository.
set -euo pipefail

REPO="$(cd "$(dirname "$0")/../.." && pwd)"
EVAL="$REPO/scripts/eval.sh"

pass_count=0
fail() {
  printf 'FAIL: %s\n' "$1" >&2
  exit 1
}
ok() {
  pass_count=$((pass_count + 1))
  printf 'PASS: %s\n' "$1"
}

TMP_ROOTS=()
cleanup() {
  local rc=$? root
  for root in "${TMP_ROOTS[@]:-}"; do
    [ -n "$root" ] || continue
    rm -rf "$root"
  done
  return "$rc"
}
trap cleanup EXIT

# usage: new_root -> prints a fresh temp project root with scripts/eval.sh in it
new_root() {
  local root
  root="$(mktemp -d)"
  TMP_ROOTS+=("$root")
  mkdir -p "$root/scripts" "$root/commands" "$root/.writ/state" "$root/.writ/knowledge"
  cp "$EVAL" "$root/scripts/eval.sh"
  printf "%s" "$root"
}

# usage: run_check <root> <check> -> prints exit code; report at <root>/eval-report.md
run_check() {
  local root="$1" check="$2" rc=0
  ( cd "$root" && bash scripts/eval.sh --check="$check" --report=eval-report.md >/dev/null 2>&1 ) || rc=$?
  printf "%s" "$rc"
}

report_of() {
  cat "$1/eval-report.md"
}

# usage: assert_blocking <root> <check> <literal> <label>
# The finding must be a FAIL (add_finding), not a note, and must carry <literal>.
assert_blocking() {
  local root="$1" check="$2" literal="$3" label="$4" rc
  rc="$(run_check "$root" "$check")"
  [ "$rc" -eq 1 ] || { report_of "$root"; fail "$label: expected exit 1 (blocking finding), got exit $rc"; }
  grep -q '^FAIL' "$root/eval-report.md" \
    || { report_of "$root"; fail "$label: must be a blocking finding (FAIL), not a non-blocking note"; }
  grep -Fq -- "$literal" "$root/eval-report.md" \
    || { report_of "$root"; fail "$label: report must name '$literal'"; }
}

# usage: assert_green <root> <check> <label>
assert_green() {
  local root="$1" check="$2" label="$3" rc
  rc="$(run_check "$root" "$check")"
  [ "$rc" -eq 0 ] || { report_of "$root"; fail "$label: expected exit 0, got exit $rc"; }
  grep -q '^PASS' "$root/eval-report.md" || { report_of "$root"; fail "$label: report must say PASS"; }
}

# ---------------------------------------------------------------------------
# referenced-paths, red: a command backticks a `.md` path that does not exist,
# that no command creates, and that no allowlist entry covers. This is the
# `objective.md` class (assessment §2.4 row 1). The finding names file:line.
# ---------------------------------------------------------------------------
ROOT="$(new_root)"
printf '# Example\n\nStep 1.\n\n- Load `.writ/docs/phantom-context.md` before planning.\n' > "$ROOT/commands/example.md"
assert_blocking "$ROOT" referenced-paths '`commands/example.md:5`' "referenced-paths red (path form)"
grep -Fq '.writ/docs/phantom-context.md' "$ROOT/eval-report.md" \
  || { report_of "$ROOT"; fail "referenced-paths red: finding must name the unresolved path"; }
ok 'referenced-paths: nonexistent, uncreated `.writ/...md` path -> blocking finding at commands/example.md:5'

# Bare filenames are claims too — `objective.md` had no path. A bare name
# resolves when a file by that basename exists anywhere in the tree (the
# assessment's own criterion: "zero files by that name in the repo").
ROOT="$(new_root)"
printf '# Example\n\n- Load project context (`tech-stack.md`, `objective.md`).\n' > "$ROOT/commands/example.md"
mkdir -p "$ROOT/.writ/docs" && printf '# Stack\n' > "$ROOT/.writ/docs/tech-stack.md"
assert_blocking "$ROOT" referenced-paths '`commands/example.md:3`' "referenced-paths red (bare form)"
grep -Fq "objective.md" "$ROOT/eval-report.md" || { report_of "$ROOT"; fail "bare-name red: must name objective.md"; }
if grep -Fq "tech-stack.md'" "$ROOT/eval-report.md"; then
  report_of "$ROOT"; fail "bare-name red: tech-stack.md exists by basename and must not be reported"
fi
ok 'referenced-paths: bare `objective.md` with no file by that name -> blocking finding; existing basename passes'

# ---------------------------------------------------------------------------
# referenced-paths, green: paths that exist (repo-root or commands/-relative),
# placeholder tokens (`{name}`, `<slug>`, `*`, `YYYY-MM-DD`), and an
# allowlisted runtime-created path all pass.
# ---------------------------------------------------------------------------
ROOT="$(new_root)"
mkdir -p "$ROOT/.writ/docs"
printf '# Other\n' > "$ROOT/commands/other.md"
printf '# Preamble\n' > "$ROOT/commands/_preamble.md"
printf '# Guide\n' > "$ROOT/.writ/docs/guide.md"
cat > "$ROOT/commands/example.md" <<'EOF'
# Example

Read `commands/other.md`, `_preamble.md`, and `.writ/docs/guide.md`.
Write `.writ/specs/{name}/spec.md`, `skills/<name>/SKILL.md`, `commands/*.md`,
and `.writ/research/YYYY-MM-DD-{topic}-research.md`.
`/initialize` writes `.writ/docs/tech-stack.md` (allowlisted: created at runtime).
EOF
assert_green "$ROOT" referenced-paths "referenced-paths green"
ok "referenced-paths: existing paths, placeholders, and an allowlisted runtime path -> exit 0"

# The allowlist is a table with three columns — path, creating command, reason —
# so the check cannot degrade into a second check_broken_refs with bare names.
grep -Eq '^\.writ/docs/tech-stack\.md\|/initialize\|' "$EVAL" \
  || fail "referenced-paths allowlist must carry '.writ/docs/tech-stack.md|/initialize|<reason>' (path|command|reason)"
if awk '/^referenced_paths_allowlist\(\)/{f=1} f && /^}/{exit} f && /^[^#| ]+\|/ && !/^[^|]+\|[^|]+\|[^|]+/' "$EVAL" | grep -q .; then
  fail "every referenced-paths allowlist row must have three fields: path|command|reason"
fi
ok "referenced-paths: allowlist rows are path|command|reason"

# usage: inject_allowlist_row <root> <row>
# Appends <row> to the copied eval.sh's referenced_paths_allowlist heredoc so
# the allowlist's own self-checks can be exercised without depending on which
# real rows the table carries today. Fails loudly if the heredoc was not found.
inject_allowlist_row() {
  local root="$1" row="$2" target
  target="$root/scripts/eval.sh"
  awk -v row="$row" '
    /^referenced_paths_allowlist\(\)/ { f = 1 }
    f && /^EOF$/ { print row; f = 0 }
    { print }
  ' "$target" > "$target.patched" && mv "$target.patched" "$target"
  grep -Fxq -- "$row" "$target" || fail "inject_allowlist_row: could not inject '$row' into the copied allowlist"
}

# ---------------------------------------------------------------------------
# referenced-paths, allowlist self-check (a): a row with only two fields —
# a path and a command but no reason — is the "silence a finding" degradation
# the table's header comment warns about. The check must block and name the
# row, even though no command in the tree references the path at all.
# ---------------------------------------------------------------------------
ROOT="$(new_root)"
printf '# Example\n\nNothing referenced here.\n' > "$ROOT/commands/example.md"
inject_allowlist_row "$ROOT" '.writ/docs/half-row.md|/fixture-cmd'
assert_blocking "$ROOT" referenced-paths "'.writ/docs/half-row.md' lacks" "referenced-paths allowlist self-check (missing field)"
grep -q 'FAIL (1 finding' "$ROOT/eval-report.md" \
  || { report_of "$ROOT"; fail "allowlist missing-field: expected exactly 1 finding (the malformed row, nothing else)"; }
ok "referenced-paths: allowlist row with no reason field -> blocking finding naming the row"

# ---------------------------------------------------------------------------
# referenced-paths, allowlist self-check (b): a stale row. The creating command
# exists in the tree but no command references the allowlisted path any more,
# so the row must be reported. A sibling row for the same command whose path
# IS still referenced must not be — the judgement is per row, on the
# reference, not on the command's presence.
# ---------------------------------------------------------------------------
ROOT="$(new_root)"
printf '# Fixture\n\nThis command writes `.writ/docs/still-used.md` at runtime.\n' > "$ROOT/commands/fixture-cmd.md"
inject_allowlist_row "$ROOT" '.writ/docs/still-used.md|/fixture-cmd|Written by /fixture-cmd at runtime; still referenced.'
inject_allowlist_row "$ROOT" '.writ/docs/orphaned.md|/fixture-cmd|Written by /fixture-cmd at runtime; the reference was removed.'
assert_blocking "$ROOT" referenced-paths "'.writ/docs/orphaned.md' is no longer referenced" "referenced-paths allowlist self-check (stale row)"
if grep -Fq "'.writ/docs/still-used.md'" "$ROOT/eval-report.md"; then
  report_of "$ROOT"; fail "allowlist stale-row: the still-referenced sibling row must not be reported"
fi
grep -q 'FAIL (1 finding' "$ROOT/eval-report.md" \
  || { report_of "$ROOT"; fail "allowlist stale-row: expected exactly 1 finding (the orphaned row only)"; }
ok "referenced-paths: stale allowlist row (command present, path unreferenced) -> blocking finding; referenced sibling row passes"

# ---------------------------------------------------------------------------
# skill-manifest-parity, red: a skill on disk is absent from the manifest AND
# a manifest skill is absent from disk. Both directions block, and each names
# a location (the SKILL.md for disk-only, the manifest line for manifest-only).
# ---------------------------------------------------------------------------
ROOT="$(new_root)"
mkdir -p "$ROOT/skills/on-disk-only"
printf -- '---\nname: on-disk-only\n---\n# On disk only\n' > "$ROOT/skills/on-disk-only/SKILL.md"
cat > "$ROOT/.writ/manifest.yaml" <<'EOF'
version: 1
commands: []
agents: []
skills:
  - name: manifest-only
    file: skills/manifest-only/SKILL.md
    description: "Registered but absent from disk."
    status: candidate
    tags: [test]
EOF
assert_blocking "$ROOT" skill-manifest-parity 'on-disk-only' "skill-manifest-parity red (disk-only)"
grep -Fq '`skills/on-disk-only/SKILL.md:1`' "$ROOT/eval-report.md" \
  || { report_of "$ROOT"; fail "parity red: disk-only finding must be located at skills/on-disk-only/SKILL.md:1"; }
grep -Fq '`.writ/manifest.yaml:6`' "$ROOT/eval-report.md" \
  || { report_of "$ROOT"; fail "parity red: manifest-only finding must be located at the manifest file: line (.writ/manifest.yaml:6)"; }
grep -Fq 'manifest-only' "$ROOT/eval-report.md" \
  || { report_of "$ROOT"; fail "parity red: must name the manifest-only skill"; }
grep -q 'FAIL (2 finding' "$ROOT/eval-report.md" \
  || { report_of "$ROOT"; fail "parity red: expected exactly 2 findings (one per direction)"; }
ok "skill-manifest-parity: disk-only and manifest-only skills -> two blocking findings with locations"

# ---------------------------------------------------------------------------
# skill-manifest-parity, green: disk and manifest name the same set.
# ---------------------------------------------------------------------------
ROOT="$(new_root)"
mkdir -p "$ROOT/skills/alpha" "$ROOT/skills/beta"
printf -- '---\nname: alpha\n---\n# Alpha\n' > "$ROOT/skills/alpha/SKILL.md"
printf -- '---\nname: beta\n---\n# Beta\n' > "$ROOT/skills/beta/SKILL.md"
cat > "$ROOT/.writ/manifest.yaml" <<'EOF'
version: 1
commands: []
agents: []
skills:
  - name: alpha
    file: skills/alpha/SKILL.md
    description: "A."
    status: candidate
    tags: [test]
  - name: beta
    file: skills/beta/SKILL.md
    description: "B."
    status: candidate
    tags: [test]
EOF
assert_green "$ROOT" skill-manifest-parity "skill-manifest-parity green"
ok "skill-manifest-parity: matching sets -> exit 0"

# ---------------------------------------------------------------------------
# knowledge-integrity, red: an entry with single-character bullets (the
# shredded-writeback class) in lessons/, and one in conventions/ to prove the
# check scans every category, not only lessons/. Findings name file:line.
# ---------------------------------------------------------------------------
ROOT="$(new_root)"
mkdir -p "$ROOT/.writ/knowledge/lessons" "$ROOT/.writ/knowledge/conventions"
cat > "$ROOT/.writ/knowledge/lessons/2026-08-11-shredded.md" <<'EOF'
---
category: lessons
tags: [phase-close]
created: 2026-08-11
related_artifacts:
  - /
  - .
---

# Shredded

## TL;DR



## Context

- 2
- 0
- .
EOF
cat > "$ROOT/.writ/knowledge/conventions/2026-08-11-also-shredded.md" <<'EOF'
---
category: conventions
tags: [phase-close]
created: 2026-08-11
related_artifacts: []
---

# Also shredded

## TL;DR

A real statement.

## Context

- x
EOF
assert_blocking "$ROOT" knowledge-integrity '`.writ/knowledge/lessons/2026-08-11-shredded.md:6`' "knowledge-integrity red"
grep -Fq '`.writ/knowledge/lessons/2026-08-11-shredded.md:18`' "$ROOT/eval-report.md" \
  || { report_of "$ROOT"; fail "knowledge-integrity red: must name the body bullet line (:18)"; }
grep -Fq '`.writ/knowledge/conventions/2026-08-11-also-shredded.md:16`' "$ROOT/eval-report.md" \
  || { report_of "$ROOT"; fail "knowledge-integrity red: must scan conventions/ too (:16)"; }
grep -Fq 'TL;DR' "$ROOT/eval-report.md" \
  || { report_of "$ROOT"; fail "knowledge-integrity red: an empty ## TL;DR is the same failure class and must be reported"; }
ok "knowledge-integrity: single-character bullets (frontmatter and body, two categories) and an empty TL;DR -> blocking findings with file:line"

# ---------------------------------------------------------------------------
# knowledge-integrity, green: a healthy entry, plus a README (bullets of real
# prose), pass. A `- ` line with real content and a nested list are fine.
# ---------------------------------------------------------------------------
ROOT="$(new_root)"
mkdir -p "$ROOT/.writ/knowledge/lessons"
cat > "$ROOT/.writ/knowledge/lessons/2026-08-11-healthy.md" <<'EOF'
---
category: lessons
tags: [phase-close]
created: 2026-08-11
related_artifacts:
  - commands/implement-story.md
---

# Healthy

## TL;DR

Anchor spec citations to text a sibling spec cannot shift.

## Context

- 2026-08-11 loop-bounds re-verification: all citations shifted +6.
  - nested detail with more than one character
- `commands/implement-story.md` Gate 0

## Related

- `commands/implement-story.md`
EOF
printf '# Knowledge\n\n- Entries live in four categories.\n' > "$ROOT/.writ/knowledge/README.md"
assert_green "$ROOT" knowledge-integrity "knowledge-integrity green"
ok "knowledge-integrity: healthy entry and README -> exit 0"

# ---------------------------------------------------------------------------
# Registration: all three checks are in CHECKS=(...) as a group (Story 5 adds a
# fourth beside them), and each uses add_finding — never add_note — so the
# class blocks (Business Rule 6).
# ---------------------------------------------------------------------------
for name in referenced-paths skill-manifest-parity knowledge-integrity; do
  awk '/^CHECKS=\(/{f=1} f && /^\)/{exit} f' "$EVAL" | grep -Fxq "  $name" \
    || fail "$name must be registered in CHECKS=(...)"
done
for func in check_referenced_paths check_skill_manifest_parity check_knowledge_integrity; do
  body="$(awk -v fn="$func" '$0 ~ "^"fn"\\(\\)"{f=1} f{print} f && /^}/{exit}' "$EVAL")"
  [ -n "$body" ] || fail "$func must be defined in scripts/eval.sh"
  printf '%s\n' "$body" | grep -q 'add_finding' || fail "$func must use add_finding (blocking)"
  if printf '%s\n' "$body" | grep -q 'add_note'; then
    fail "$func must not use add_note — dead ends block, they do not note (Business Rule 6)"
  fi
done
ok "registration: three checks in CHECKS, each blocking via add_finding and never add_note"

printf '\nAll %d dead-end check assertions passed.\n' "$pass_count"
