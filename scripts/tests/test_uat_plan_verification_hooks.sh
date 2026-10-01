#!/usr/bin/env bash
# Spec 2026-10-01-behavioral-verification, Story 2: /create-uat-plan drafts the
# verification recipe, binds scenarios to feature IDs through app-verify.py, and
# runs the project's own checks for machine scenarios.
# [AC-2.1, AC-2.2, AC-2.3, AC-2.4, AC-2.5]
set -euo pipefail

REPO="$(cd "$(dirname "$0")/../.." && pwd)"
# Authenticity pin: test-integrity.py extracts JS-style from '…' specifiers,
# not shell paths. This test's unit under test is the command it reads.
# from "../../commands/create-uat-plan.md"
CMD="$REPO/commands/create-uat-plan.md"

fail() { printf 'FAIL: %s\n' "$1" >&2; exit 1; }
ok() { printf 'PASS: %s\n' "$1"; }
has() { grep -Fq -- "$1" "$CMD" || fail "create-uat-plan.md must contain: $1"; }

# AC-2.1: Step 1.3 after Step 1.2's zero-stories exit; four sources; one question.
python3 - "$CMD" <<'PY' || fail "Step 1.3 must follow Step 1.2 and precede Phase 2"
import sys
text = open(sys.argv[1], encoding="utf-8").read()
s12 = text.find("#### Step 1.2: Inventory Stories")
stub = text.find("No completed stories found. UAT plan stub created.")
s13 = text.find("#### Step 1.3: Verification Recipe")
p2 = text.find("### Phase 2:")
assert -1 not in (s12, stub, s13, p2) and s12 < stub < s13 < p2, (s12, stub, s13, p2)
PY
STEP_13="$(awk '/^#### Step 1.3:/{f=1} /^### Phase 2:/{f=0} f' "$CMD")"
in13() { printf '%s\n' "$STEP_13" | grep -Fq -- "$1" || fail "Step 1.3 must contain: $1"; }
in13 '.writ/docs/app-verification.md'
in13 '.writ/docs/app-verification-format.md'
for src in 'Playwright' 'Cypress' 'pytest' '`package.json` test scripts' \
           'dev or start command' 'readiness URL or port' 'environment files that name a database'; do
  in13 "$src"
done
in13 'backticked `Check` command'
in13 'human-only: no check yet'
in13 'No harness detected'
in13 'no draft and no question'
in13 'AskQuestion({'
in13 '{ id: "save", label: "Save (Recommended)" }'
in13 '{ id: "edit"'
in13 '{ id: "skip"'
[ "$(printf '%s\n' "$STEP_13" | grep -c 'AskQuestion({')" -eq 1 ] \
  || fail "Step 1.3 must ask exactly one AskQuestion"
[ "$(printf '%s\n' "$STEP_13" | grep -Fo '(Recommended)"' | wc -l | tr -d ' ')" -eq 1 ] \
  || fail "exactly one option label may carry (Recommended)"
in13 'Exactly one option carries `(Recommended)`'
in13 '`--check` shows the draft but asks nothing, saves nothing and runs nothing'
has 'No completed stories found. UAT plan stub created.'
ok "Step 1.3 drafts from four sources, one save/edit/skip question, --check saves nothing"

# AC-2.2: validate; failing draft never saved; existing invalid recipe untouched.
in13 'python3 scripts/app-verify.py validate --recipe .writ/docs/app-verification.md'
in13 'app-verify: recipe invalid — <first finding>'
in13 'never saved'
in13 'left untouched'
in13 '`**Feature:** none` and `**Verification:** human — recipe invalid`'
in13 'fix the recipe and re-run'
ok "validate step: invalid draft returns to edit; invalid existing recipe falls back to human"

# AC-2.3: scenario lines and touched binding.
has '**Feature:** <id>'
has '**Verification:** machine — evidence: evidence/uat/<id>/result.json'
has '**Verification:** human — <reason>'
has 'python3 scripts/app-verify.py touched --recipe .writ/docs/app-verification.md --changed'
has '`**Feature:** none`'
has '`**Verification:** human — no mapped feature`'
has '`**Verification:** human — no recipe`'
has 'directly under `**Source:**`'
has 'the verdict still comes from the script'
# touched never prints human-only rows (AC-3.1), so binding must read them from the recipe.
has '`touched` prints only features with a `Check`'
has "also read the recipe's \`human-only\` Feature Map rows whose \`Paths\` match the story's files"
has "Feature whose \`Check\` is \`human-only: <reason>\` → \`**Feature:** <id>\` and \`**Verification:** human — <reason>\`"
has 'give every other matched ID at least one scenario of its own'
python3 - "$CMD" <<'PY' || fail "template must place Feature/Verification directly under Source"
import sys
text = open(sys.argv[1], encoding="utf-8").read()
start = text.index("#### Step 3.1: Generate Scenarios")
block = text[start:text.index("#### Step 3.2:", start)]
lines = [ln for ln in block.splitlines() if ln.strip()]
i = next(n for n, ln in enumerate(lines) if ln.startswith("**Source:**"))
assert lines[i + 1].startswith("**Feature:**"), lines[i + 1]
assert lines[i + 2].startswith("**Verification:**"), lines[i + 2]
PY
ok "scenario template and touched binding rules"

# AC-2.4: one run call; verdict from exit code and result.json; report counts.
has 'python3 scripts/app-verify.py run --recipe .writ/docs/app-verification.md --spec .writ/specs/<spec-folder> --run-label uat --features <id,…>'
[ "$(grep -c 'app-verify.py run ' "$CMD")" -eq 1 ] || fail "exactly one run invocation"
has 'once with every distinct machine ID'
has 'verdict is `pass`'
has 'evidence/uat/_launch/'
has '`not_ready`'
has '`**Verification:** human — refused`'
has 'Status unticked'
has 'every machine scenario Fail'
has 'Never rewrite a failed scenario as human'
has 'never from agent judgment'
STEP_53="$(awk '/^#### Step 5.3:/{f=1} /^## Error Handling/{f=0} f' "$CMD")"
printf '%s\n' "$STEP_53" | grep -Fq 'app-verify:' || fail "Step 5.3 report must carry the app-verify: line"
printf '%s\n' "$STEP_53" | grep -Fq 'machine' && printf '%s\n' "$STEP_53" | grep -Fq 'human' \
  || fail "Step 5.3 report must carry machine/human counts"
ok "single run call, script-decided verdicts, report counts"

# AC-2.5: boundary sentence, exit criterion, error handling, budget, no twin, no recipe.
TERMINAL="$(grep -F '**Terminal constraint:**' "$CMD")"
printf '%s\n' "$TERMINAL" | grep -Fq 'never writes test code or check scripts' \
  || fail "the never-writes-test-code sentence must sit in the Terminal constraint"
printf '%s\n' "$TERMINAL" | grep -Fq "authoring checks is the coding agent's job" \
  || fail "Terminal constraint must name the coding agent as the check author"
printf '%s\n' "$TERMINAL" | grep -Fq 'scripts/app-verify.py' \
  || fail "Terminal constraint must say checks run only through app-verify.py"
python3 - "$CMD" <<'PY' || fail "exit_criteria must require Feature and Verification lines"
import sys
text = open(sys.argv[1], encoding="utf-8").read()
fm = text.split("---\n", 2)[1]
crit = [ln for ln in fm.splitlines() if ln.startswith("  - ")]
assert any("**Feature:**" in ln and "**Verification:**" in ln and "populated" in ln for ln in crit), crit
PY
ERR="$(awk '/^## Error Handling/{f=1} /^## Integration with Writ/{f=0} f' "$CMD")"
for heading in '**No test harness detected:**' '**Recipe invalid:**' '**Safety refused:**'; do
  printf '%s\n' "$ERR" | grep -Fq -- "$heading" || fail "Error Handling must cover $heading"
done
size="$(wc -c < "$CMD" | tr -d ' ')"
[ "$size" -lt 24960 ] || fail "create-uat-plan.md is $size bytes (budget 24960)"
[ ! -e "$REPO/commands/create-uat-plan.lean.md" ] || fail "no create-uat-plan.lean.md twin"
[ ! -e "$REPO/.writ/docs/app-verification.md" ] || fail "the Writ repo must not carry a project recipe"
ok "boundary sentence, exit criterion, error handling, $size bytes < 24960, no twin, no recipe"

echo "All create-uat-plan verification hook assertions passed."
