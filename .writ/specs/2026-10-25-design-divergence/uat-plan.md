# UAT Plan: Design Divergence Skill and Usage-First Gate 0

> **Generated:** 2026-10-29
> **Spec:** `.writ/specs/2026-10-25-design-divergence/`
> **Stories Covered:** 5 of 6 completed (Story 6 waits on the blind rating)
> **Total Scenarios:** 36
> **Merged:** `df3b461` on `phase/15-code-level-rigor`
> **Verification recipe:** none. No `.writ/docs/app-verification.md` exists, and Writ has no app to launch: its checks (pytest, the bash tests, `scripts/eval.sh`) read markdown, not a running process. With no launch command detected, Step 1.3's recommended answer is skip, so no recipe was drafted, saved, or bound. Every scenario is `human — no recipe`.

## How to Use This Plan

1. Work through scenarios in order (they're grouped by story, ordered by priority)
2. For each scenario, follow the steps exactly as written
3. Mark Pass or Fail — add notes for any unexpected behavior
4. Scenarios marked Fail should be filed as issues or fed back to the spec
5. A feature passes UAT when all scenarios pass (or failures are accepted as known limitations)

**Conventions for this plan:**

- **Four kinds of scenario.** **Read and check** scenarios (1 to 8, 10 to 16, 28 to 33) read the shipped files and run the repository's own tests in a scratch clone. **Harness** scenarios (22 to 27) drive `scripts/divergence-trial.py` on the harness's own test fixtures in `$W/ft`, never on the real trial. **Live** scenarios (9, 17 to 21, 34) run `/prototype` or `/implement-story` in a Claude Code session inside the clone and are judged by eye. **Human handoff** scenarios (35, 36) run in the primary checkout: 35 is the blind rating, 36 is the Story 6 run that follows it.
- **Keep the rating blind.** Scenario 35 is the blind rating, and the rater is the person this plan is written for. Before Scenario 35, open nothing under `.writ/eval/divergence-trial/` except `rating-sheet.md`, `briefs/`, and `render/`, and do not run Scenario 33 or 36. Every other scenario reads only those, lists file names, runs tests that print pass or fail, or prints the single `rated_by` field, so it can run before the rating. Scenarios 33 and 36 are marked **After rating**.
- **Where each scenario runs.** Scenarios 1 to 34 run in a scratch clone pinned at `df3b461`, the tree as merged, so they describe what was built even after Story 6 later keeps or removes the feature or deletes the harness. Only Scenarios 35 and 36 touch the primary checkout (`$REPO`). **Never run `install.sh` or `update.sh` in the Writ repo.** `.claude/` and `.cursor/` there are symlinks into the source; the clone keeps them, so `/implement-story` and `/prototype` are project commands inside `$CL` with nothing installed.
- Every helper refuses to run unless the shell is inside `$W`. Run the plan in `bash` on macOS (`sed -i ''`), outside any sandbox, with `claude` and `uv` on `PATH`. Claude Code asks whether to trust each new scratch folder the first time a session opens there; accept it.
- **Live scenarios.** Start `live` from a second shell: set `UAT_W=<the path the first shell printed>`, then paste the setup block, which reuses that folder and clone. Start a new session for each scenario (`/exit`, then `live` again). The Gate 0 scenarios need only Gate 0: when the session moves past it (it starts Gate 0.5, the boundary map, or spawns the coding agent), press Escape and send the reply the scenario gives. If a run left a worktree behind, `git -C "$CL" worktree list` shows it; `rm -rf "$W"` at the end removes it.
- Expected results come from the spec, the five What Was Built records, the drift log, `rating-handoff.md`, and the tree at `df3b461`. Story 1 landed in `42754d7`, Story 2 in `6b10789`, Story 3 in `49719ed`, Story 4 in `c98a80d`, Story 5 in `c155132`. None of these scenarios has been run for this plan. After each scenario that edits the clone, run `reset` and confirm it prints nothing. When done: `rm -rf "$W"`.
- **Drift.** DEV-001 (one axis table per medium; Scenario 2), DEV-002 (raw drafts copied beside the trial file; Scenario 23), DEV-003 (refusals on stderr with stdout empty; Scenarios 22 to 27), DEV-004 (extra integrity refusals such as `already_blinded`; Scenario 24), DEV-005 (no filled-sheet fixture; this plan fills fixture sheets with `fill`), DEV-006 (`brief_count` as an `unverifiable` reason; Scenario 27), DEV-007 (`Title:` inside `Structure:` is content; unit tests in Scenario 28), DEV-008 (`test_harness_cuts.py` allows a disclosed upward re-pin; Scenario 14), DEV-009 (a script `unverifiable` arch-check still runs divergence; Scenarios 15 and 20), DEV-010 (first generation discarded for content tells; Scenarios 31 and 33), DEV-011 (the outcome test also checks the trial inputs; Scenarios 29 to 33).

**Setup.** Paste this block once in the first shell. Stop if the first line does not print `W=/...`.

```bash
# First shell: paste as is. Second shell: run UAT_W=<the W path the first shell printed>, then paste.
W=${UAT_W:-$(mktemp -d "${TMPDIR:-/tmp}/writ-uat-divergence.XXXXXX")} && cd "$W" && W=$PWD && echo "W=$W"
REPO=/Users/asellke/Projects/writ            # primary checkout: only Scenarios 35 and 36 touch it
CL="$W/clone"; [ -d "$CL/.git" ] || { git clone -q "$REPO" "$CL" && git -C "$CL" checkout -q df3b461; }
SPEC=.writ/specs/2026-10-25-design-divergence
TD=.writ/eval/divergence-trial
TRIAL=$TD/2026-10-26-divergence-trial.json
FX="$CL/scripts/tests/fixtures/divergence-trial"
G0=.writ/specs/2026-10-29-uat-gate0
inW() { case "$PWD/" in "$W"/*) ;; *) echo "refusing: $PWD is outside $W" >&2; return 1;; esac; }
# live: Claude Code inside the clone
live() { inW && (cd "$CL" && claude); }
# pt <pytest args>: pytest on Python 3.9 inside the clone
pt() { inW && (cd "$CL" && uv run --python 3.9 pytest "$@"); }
# reset: undo every edit in the clone, drop untracked files and Gate 0 state; prints nothing when clean
reset() { inW && git -C "$CL" checkout -q -- . && git -C "$CL" clean -qfd \
  && rm -f "$CL"/.writ/state/divergence-story-*.md "$CL"/.writ/state/boundary-story-*.json \
  && git -C "$CL" status --short; }
# dt <args>: the trial harness from the clone
dt() { inW && python3 "$CL/scripts/divergence-trial.py" "$@"; }
# rc <command...>: run it, keep its stdout in $W/out.txt, print its exit code and stdout size
rc() { inW || return 1; "$@" > "$W/out.txt"; local s=$?; echo "exit $s stdout-bytes $(wc -c < "$W/out.txt" | tr -d ' ')"; }
# h12 <file>: the first 12 hex digits of its sha256
h12() { shasum -a 256 "$1" | cut -c1-12; }
# tf [trial]: a trial file's rated_by, and whether ratings and blind are set (default: the fixture trial)
tf() { python3 -c 'import json,sys; d=json.load(open(sys.argv[1])); print("rated_by=%s ratings=%s blind=%s" % (d["rated_by"], "set" if d["ratings"] else None, "set" if d["blind"] else None))' "${1:-$W/ft/trial.json}"; }
# ftrial: a fresh FIXTURE trial in $W/ft: init, all twelve arms recorded from the test fixtures, blinded with seed 7
ftrial() { inW && rm -rf "$W/ft" && mkdir "$W/ft" \
  && dt init --briefs "$FX/briefs" --out "$W/ft/trial.json" > /dev/null || return 1
  local b; for b in api-1 api-2 data-model-1 data-model-2 ui-1 ui-2; do
    dt record --trial "$W/ft/trial.json" --brief "$b" --arm axes --drafts "$FX/drafts/axes.md" > /dev/null || return 1
    dt record --trial "$W/ft/trial.json" --brief "$b" --arm naive --drafts "$FX/drafts/naive.md" > /dev/null || return 1
  done
  dt blind --trial "$W/ft/trial.json" --sheet "$W/ft/rating-sheet.md" --seed 7 | tail -1; }
# frate / frep [--json]: rate and report the fixture trial
frate() { dt rate --trial "$W/ft/trial.json" --sheet "$W/ft/rating-sheet.md" --rated-by "UAT Tester"; }
frep() { dt report --trial "$W/ft/trial.json" "$@"; }
cat > "$W/fill.py" <<'PY'
# fill.py SHEET WINS AD ND: rate a FIXTURE sheet from its key.json. The declared-axes set is
# more_distinct on the first WINS briefs and tied on the rest; its distinct count is AD and the
# naive set's is ND; render_only_enough alternates yes, no, starting with yes.
import json, sys
from pathlib import Path
sheet = Path(sys.argv[1]).resolve()
if ".writ" in sheet.parts:
    sys.exit("refusing: fill.py rates fixture sheets only, never the real trial")
wins, ad, nd = int(sys.argv[2]), sys.argv[3], sys.argv[4]
key = json.loads((sheet.parent / "key.json").read_text())["briefs"]
lines = sheet.read_text().split("\n")
for n, brief in enumerate(sorted(key)):
    axes = "X" if key[brief]["X"]["arm"] == "axes" else "Y"
    i = lines.index("### Rating: " + brief) + 2
    lines[i:i + 5] = ["distinct_X: " + (ad if axes == "X" else nd),
                      "distinct_Y: " + (ad if axes == "Y" else nd),
                      "more_distinct: " + (axes if n < wins else "tie"),
                      "render_only_enough: " + ("yes" if n % 2 == 0 else "no"),
                      "note: fixture rating %d" % (n + 1)]
sheet.write_text("\n".join(lines))
PY
# fill <wins> <axes-distinct> <naive-distinct>: rate the fixture sheet in $W/ft
fill() { inW && python3 "$W/fill.py" "$W/ft/rating-sheet.md" "$@"; }

# Gate 0 fixture spec: three stories, never built; g0 copies it into the clone as untracked files
mkdir -p "$W/g0/user-stories"
cat > "$W/g0/spec.md" <<'EOF'
# UAT Gate 0 Fixture

> **Status:** In Progress
> **Created:** 2026-10-29

## Specification Contract

**Deliverable:** An order export a support rep can attach to a ticket. A UAT fixture for Gate 0 divergence; it is never built.
EOF
cat > "$W/g0/spec-lite.md" <<'EOF'
# UAT Gate 0 Fixture (Lite)

## For Coding Agents

**Deliverable:** An order export endpoint backed by an orders table, a glossary entry, and agreed wording.
EOF
cat > "$W/g0/user-stories/story-1-order-export.md" <<'EOF'
# Story 1: Order Export Endpoint

> **Status:** Not Started
> **Priority:** High
> **Dependencies:** None

## User Story

**As a** support rep
**I want to** export a customer's orders as CSV
**So that** I can attach them to a support ticket

## Acceptance Criteria

- [ ] Given a customer with orders, when a caller requests an export for that customer, then it receives a link to a CSV listing every order `[AC-1.1]`
- [ ] Given a customer with no orders, when a caller requests an export, then the CSV holds only the header row `[AC-1.2]`

## Implementation Tasks

- [ ] 1.1 Write failing tests in `tests/test_orders_export.py` `[AC-1.1, AC-1.2]`
- [ ] 1.2 Add the orders table in `migrations/0002_orders.sql` `[AC-1.1]`
- [ ] 1.3 Add the export endpoint in `api/orders.py` `[AC-1.1, AC-1.2]`
EOF
cat > "$W/g0/user-stories/story-2-glossary-note.md" <<'EOF'
# Story 2: Orders Glossary Note

> **Status:** Not Started
> **Priority:** Low
> **Dependencies:** None

## User Story

**As a** support rep
**I want to** a glossary entry for "order export"
**So that** I use the same words as the team

## Acceptance Criteria

- [ ] Given the glossary, when a rep reads it, then "order export" has a one-line definition `[AC-2.1]`

## Implementation Tasks

- [ ] 2.1 Add the "order export" entry to `docs/orders-glossary.md` `[AC-2.1]`
EOF
cat > "$W/g0/user-stories/story-3-no-files.md" <<'EOF'
# Story 3: Agree on Export Wording

> **Status:** Not Started
> **Priority:** Low
> **Dependencies:** None

## User Story

**As a** support rep
**I want to** agreed wording for the order export
**So that** every ticket describes it the same way

## Acceptance Criteria

- [ ] Given the support lead approved a term, when a rep describes an export, then the rep uses that term `[AC-3.1]`

## Implementation Tasks

- [ ] 3.1 Agree on the term with the support lead `[AC-3.1]`
EOF
g0() { inW && mkdir -p "$CL/$G0" && cp -R "$W/g0/." "$CL/$G0/" && ls "$CL/$G0/user-stories"; }
# sw <value>: put `- **Gate 0 Divergence:** <value>` under ## Conventions in the clone's .writ/config.md
sw() { inW && python3 -c 'import sys; p, v = sys.argv[1:3]; t = open(p).read(); open(p, "w").write(t.replace("## Conventions\n\n", "## Conventions\n\n- **Gate 0 Divergence:** %s\n" % v, 1))' "$CL/.writ/config.md" "$1" && grep -n 'Gate 0 Divergence' "$CL/.writ/config.md"; }
echo "setup done: clone at $(git -C "$CL" rev-parse --short HEAD), $(ls "$W/g0/user-stories" | wc -l | tr -d ' ') fixture stories"
```

The last line should read `setup done: clone at df3b461, 3 fixture stories`. The fixture stories are built so the route predictor gives a known answer: Story 1 plans `api/` and `migrations/` paths (`full-stack`, route `review-agent`), Story 2 plans one doc (`cross-component`, route `evaluator-agent`), and Story 3 plans no file.

## Coverage Summary

| Story | Status | Scenarios | Source Breakdown |
|-------|--------|-----------|-----------------|
| Story 1: Extract the design-divergence Skill and Register It | ✅ Covered | 5 | AC: 5, Errors: 0, Shadow: 0, Edge: 0, Experience: 0 |
| Story 2: /prototype Step 2.5 Loads the Skill | ✅ Covered | 4 | AC: 3, Errors: 0, Shadow: 0, Edge: 0, Experience: 1 |
| Story 3: Gate 0 Usage-First Divergence and the Gate 0 Divergence Switch | ✅ Covered | 12 | AC: 5, Errors: 2, Shadow: 1, Edge: 1, Experience: 3 |
| Story 4: Divergence Trial Harness | ✅ Covered | 7 | AC: 6, Errors: 0, Shadow: 1, Edge: 0 |
| Story 5: Trial Inputs, Generation, Blinding, and Rating Handoff | ✅ Covered | 5 | AC: 5, Errors: 0, Shadow: 0, Edge: 0 |
| Human handoff: blind rating and Story 6 follow-through | ⏳ Human step | 3 | Business Rule 12, `rating-handoff.md`, Story 6 AC-6.1 |
| Story 6: Act on the Blind Verdict (Human-Gated) | ⏳ Pending | — | Not Started; Scenario 36 starts it |

- Folded rows. Error Map: the `init`, `record`, `blind`, `rate`, and `report` rows run inside Scenarios 22 to 27; "Gate 0 switch read" (`.writ/config.md` or the line absent) is Scenarios 11 and 17, (value not `on`/`off`) is Scenario 19; "Route predictor" (planned set empty) is Scenarios 15 and 20, (`crossings` unverifiable or a script cannot run) is Scenario 15; "Sketch spawn" (spawn error; missing field) is Scenario 15; "Story 6 — report `unverifiable`" is Scenario 32.
- Shadow Paths: "Gate 0 divergence" happy path is Scenario 17, nil input Scenario 20, empty input and upstream error Scenario 15. "Trial report" happy path is Scenario 26, nil, empty, and upstream error Scenario 27.
- Interaction Edge Cases: converged sketches, ABORT resolved as proceed, Gate 1 recode, and two-fail escalation are Scenario 16; a rater who fills only some briefs or edits a draft is Scenario 25.
- Experience Design: Entry point `/prototype` is Scenario 9, `/implement-story` on a boundary-crossing story is Scenario 17. State Catalog: Off 18, On malformed 19, Skipped low stakes 19, Skipped unverifiable 20, Skipped ABORT 16, Skipped sketch failed 15, Chosen 17; the `--quick` note is Scenario 21.
- No live scenario for an architecture ABORT, a failed sketch spawn, or a forced `--full-pipeline` / `--panel` route: none can be produced reliably from a fixture. Scenarios 15 and 16 check their text and wiring tests.
- AC-5.2's "same tier in one session" cannot be read from the files; Story 5's What Was Built (decision 1) and `rating-handoff.md` record it.

---

## Story 1: Extract the design-divergence Skill and Register It

### Scenario 1: The skill's frontmatter is right and the skill lints `pass`

**Source:** Acceptance Criteria (AC-1.1) — Story 1
**Feature:** none
**Verification:** human — no recipe

**Preconditions:**
- Setup block pasted; `reset` prints nothing.

**Steps:**
1. `sed -n '1,6p' "$CL/skills/design-divergence/SKILL.md"`
2. `(cd "$CL" && bash scripts/lint-skill.sh skills/design-divergence/SKILL.md; echo "exit $?")`
3. `pt scripts/tests/test_design_divergence_wiring.py -q -k "SkillFrontmatterTest or SkillLintTest" 2>&1 | tail -1`

**Expected Result:**
- Step 1: `---`, `name: design-divergence`, `description: "Generate structurally different alternatives for a UI, an API shape, or a data model by declaring axes first and drafting each one in an independent context."`, `disable-model-invocation: true`, `status: candidate`, `---`.
- Step 2: `pass`, `reason: ✅ skills/design-divergence/SKILL.md: clean`, `lint-skill: pass (1 file(s) clean)`, `exit 0`.
- Step 3: `5 passed` (with a deselected count).

**Implementation Reference:** Story 1 — Files: `skills/design-divergence/SKILL.md`, `scripts/tests/test_design_divergence_wiring.py`

**Status:** [ ] Pass  [ ] Fail

**Notes:**

---

### Scenario 2: Eight rules in order, one axis table per medium, two examples, no caller steps; a command read fails lint

**Source:** Acceptance Criteria (AC-1.2) — Story 1; Business Rule 9 (Skill boundary); DEV-001
**Feature:** none
**Verification:** human — no recipe

**Preconditions:**
- Setup block pasted; `reset` prints nothing.

**Steps:**
1. `grep -n '^## \|^### \|^#### ' "$CL/skills/design-divergence/SKILL.md"`
2. `sed -n '/^### Rules/,/^### Axis catalog/p' "$CL/skills/design-divergence/SKILL.md"`
3. `grep -cE '^/|Read commands/|Read skills/|Task\(|Gate 0|exploration\.md' "$CL/skills/design-divergence/SKILL.md"`
4. `pt scripts/tests/test_design_divergence_wiring.py -q -k "SkillSectionsTest or SkillRulesTest or SkillAxisCatalogTest or SkillExamplesTest or SkillBoundaryTest" 2>&1 | tail -1`
5. `echo 'Read commands/prototype.md' >> "$CL/skills/design-divergence/SKILL.md"; (cd "$CL" && bash scripts/lint-skill.sh skills/design-divergence/SKILL.md | head -2; echo "exit ${PIPESTATUS[0]}"); reset`

**Expected Result:**
- Step 1: `## Purpose`, `## When to Use`, `## How to Apply`, `### Rules`, `### Axis catalog`, `#### UI`, `#### API shape`, `#### Data model`, `## Examples`, `### API: report export`, `### Data model: account balance`, in that order.
- Step 2: eight numbered rules with these bold leads, in order: Write the caller's usage first (3 to 10 lines, before any axis or draft); Declare the axes first; Generate independently; Commit before drafting; Use ordinary personas; Two or three drafts; The anti-pattern (one call asking "give me three options" returns one idea three times, because models fixate on their own early output and repeated samples converge); Same model family (other vendors out of scope, ADR-024).
- Step 1 and the file: each medium has its own three-row table under `### Axis catalog`, not one shared table (DEV-001). A line under the UI table keeps primary action placement as a fourth UI axis. The API example shows two drafts and the usage line each changes; the data-model example does the same.
- Step 3: `0`. The skill names no render table, Gate 0, report line, or `exploration.md`: callers own those.
- Step 4: `14 passed`.
- Step 5: line 1 `fail`, then a `reason:` line about a command invocation (skills do not invoke commands); `exit 1`. `reset` prints nothing.

**Implementation Reference:** Story 1 — Files: `skills/design-divergence/SKILL.md` (§ How to Apply, § Examples); WWB decisions 1 and 2

**Status:** [ ] Pass  [ ] Fail

**Notes:**

---

### Scenario 3: The manifest, the root catalog, and the README each list the skill once

**Source:** Acceptance Criteria (AC-1.3) — Story 1
**Feature:** none
**Verification:** human — no recipe

**Preconditions:**
- Setup block pasted; `reset` prints nothing.

**Steps:**
1. `grep -n -B5 -A5 '  - name: design-divergence$' "$CL/.writ/manifest.yaml"`
2. `(cd "$CL" && bash scripts/gen-skill.sh --check 2>/dev/null | head -1)`
3. `grep -n 'design-divergence' "$CL/SKILL.md" "$CL/README.md" | cut -c1-110`
4. `pt scripts/tests/test_design_divergence_wiring.py -q -k "ManifestEntryTest or CatalogAndReadmeTest" 2>&1 | tail -1`

**Expected Result:**
- Step 1: the entry reads `name: design-divergence`, `file: skills/design-divergence/SKILL.md`, the same description as the frontmatter, `status: candidate`, `tags: [design, divergence, exploration]`. The entry above it is `dependency-context-loading`; the one below is `drift-triage`.
- Step 2: `pass`.
- Step 3: one `SKILL.md` row, ``| `design-divergence` | `candidate` | `skills/design-divergence/SKILL.md` | Generate …``, and one `README.md` row in § Skills, ``| [`design-divergence`](skills/design-divergence/SKILL.md) | Generate …``.
- Step 4: `5 passed`.

**Implementation Reference:** Story 1 — Files: `.writ/manifest.yaml` (`skills:`), `SKILL.md` (generated by `scripts/gen-skill.sh`), `README.md` (§ Skills)

**Status:** [ ] Pass  [ ] Fail

**Notes:**

---

### Scenario 4: The generated trees carry the skill, the generator reports them current, and a hand edit is caught

**Source:** Acceptance Criteria (AC-1.4) — Story 1
**Feature:** none
**Verification:** human — no recipe

**Preconditions:**
- Setup block pasted; `reset` prints nothing.

**Steps:**
1. `(cd "$CL" && python3 scripts/gen-platform-trees.py --check | head -2)`
2. `ls "$CL/plugins/writ/skills/design-divergence/SKILL.md" "$CL/cursor/plugin/skills/design-divergence/SKILL.md"; grep -c 'design-divergence' "$CL/codex/AGENTS.md.template"`
3. `diff "$CL/skills/design-divergence/SKILL.md" "$CL/plugins/writ/skills/design-divergence/SKILL.md"`
4. `pt scripts/tests/test_design_divergence_wiring.py -q -k GeneratedTreesTest 2>&1 | tail -1`
5. `echo "hand edit" >> "$CL/plugins/writ/skills/design-divergence/SKILL.md"; (cd "$CL" && python3 scripts/gen-platform-trees.py --check | head -2); reset`

**Expected Result:**
- Step 1: `pass`, then `gen-platform-trees: pass (0 stale, 0 missing, 0 orphan, 0 unmapped, 0 vendor)`.
- Step 2: both paths listed; `1` (the Codex row points to `.agents/skills/design-divergence/SKILL.md`).
- Step 3: one difference: line 7 of the plugin copy is `<!-- generated by scripts/gen-platform-trees.py from skills/design-divergence/SKILL.md — do not hand-edit; regenerate -->`.
- Step 4: `2 passed`.
- Step 5: the first line is not `pass`, and the summary counts one stale file. `reset` prints nothing.

**Implementation Reference:** Story 1 — Files: `plugins/writ/skills/design-divergence/SKILL.md`, `cursor/plugin/skills/design-divergence/SKILL.md`, `codex/AGENTS.md.template` (all generated)

**Status:** [ ] Pass  [ ] Fail

**Notes:**

---

### Scenario 5: The wiring tests, the full suite on both interpreters, the bash tests, and the quality gate all pass

**Source:** Acceptance Criteria (AC-1.5) — Story 1; also AC-2.4, AC-3.5, AC-5.5 (full-suite parts); Success Criteria
**Feature:** none
**Verification:** human — no recipe

**Preconditions:**
- Setup block pasted; `reset` prints nothing. Run outside any sandbox (eval runs `git init` in a temp dir). About five minutes. Run pytest alone, not beside eval or the bash tests.

**Steps:**
1. `pt scripts/tests/test_design_divergence_wiring.py -q 2>&1 | tail -1`
2. `pt -q 2>&1 | tail -1`
3. `(cd "$CL" && uv run pytest -q 2>&1 | tail -1)`
4. `(cd "$CL" && for t in scripts/tests/test_*.sh; do bash "$t" >/dev/null 2>&1 || echo "FAIL $t"; done; echo "bash loop done")`
5. `(cd "$CL" && bash scripts/eval.sh >/dev/null; echo "exit $?"); tail -2 "$(ls -t "$CL"/.writ/state/eval-*.md | head -1)"`
6. `reset`

**Expected Result:**
- Step 1: `60 passed` (26 for Story 1, 8 for Story 2, 26 for Story 3).
- Steps 2 and 3: no `failed` in either summary. Story 5 recorded `3274 passed, 3 skipped` on its lane; the merged tree may count differently.
- Step 4: only `bash loop done`; no `FAIL` line.
- Step 5: `exit 0`, then `- Findings: 0` and `- Run errors: 0`.
- Step 6: prints nothing.

**Implementation Reference:** Story 1 — WWB Test Results; Story 5 commit `c155132` message (suite counts)

**Status:** [ ] Pass  [ ] Fail

**Notes:**

---

## Story 2: /prototype Step 2.5 Loads the Skill

### Scenario 6: Step 2.5 reads the skill and says what the step owns; restoring an inline rule fails the test

**Source:** Acceptance Criteria (AC-2.1) — Story 2; Business Rule 9 (Skill boundary)
**Feature:** none
**Verification:** human — no recipe

**Preconditions:**
- Setup block pasted; `reset` prints nothing.

**Steps:**
1. `sed -n '/^#### Getting drafts that actually differ/,/^#### Render through the platform/p' "$CL/commands/prototype.md"`
2. `grep -c 'Declare the axes first\.\|Use ordinary personas, not visionary ones\.' "$CL/commands/prototype.md"`
3. `grep -n 'design-divergence' "$CL/commands/prototype.md"`
4. `pt scripts/tests/test_design_divergence_wiring.py -q -k "PrototypeReadsSkillTest or PrototypeReferencesTest" 2>&1 | tail -1`
5. `printf '\n1. **Declare the axes first.**\n' >> "$CL/commands/prototype.md"; pt scripts/tests/test_design_divergence_wiring.py -q -k test_inline_rules_removed 2>&1 | tail -1; reset`

**Expected Result:**
- Step 1: the heading, then one paragraph and no numbered list: `` `Read skills/design-divergence/SKILL.md` for how to get drafts that differ: axes declared first, one context per draft, a commitment before rendering, ordinary personas. This step owns when drafts are made, what a draft is, how they render, and the record. Default to three drafts. ``
- Step 2: `0`.
- Step 3: two lines: the `Read` line in Step 2.5 (line 147) and `- Divergence rules: [design-divergence](../skills/design-divergence/SKILL.md)` under `## References` (line 328).
- Step 4: `7 passed`.
- Step 5: `1 failed` (with a deselected count). `reset` prints nothing.

**Implementation Reference:** Story 2 — Files: `commands/prototype.md` (Step 2.5 `#### Getting drafts that actually differ`; `## References`)

**Status:** [ ] Pass  [ ] Fail

**Notes:**

---

### Scenario 7: Step 2.5's pinned structure stays, and the plugin copies are regenerated

**Source:** Acceptance Criteria (AC-2.2, AC-2.4) — Story 2
**Feature:** none
**Verification:** human — no recipe

**Preconditions:**
- Setup block pasted; `reset` prints nothing.

**Steps:**
1. `sed -n '/^### Step 2.5/,/^### Step 3/p' "$CL/commands/prototype.md" | grep '^###'`
2. `sed -n '/^#### Render through the platform/,/^#### Present and choose/p' "$CL/commands/prototype.md" | grep '^| \|Never degrade'`
3. `grep -n 'Mockups for a spec that already exists\|Terminal constraint:\|\.writ/docs/design-system\.md' "$CL/commands/prototype.md" | cut -c1-80`
4. `pt scripts/tests/test_platform_neutral_names.py scripts/tests/test_prototype_worktree_integration.py -q 2>&1 | tail -1; pt scripts/tests/test_design_divergence_wiring.py -q -k PrototypeRenderPinsTest 2>&1 | tail -1`
5. `(cd "$CL" && python3 scripts/gen-platform-trees.py --check | head -1); grep -c 'design-divergence/SKILL.md' "$CL/plugins/writ/commands/prototype.md" "$CL/cursor/plugin/commands/prototype.md"`

**Expected Result:**
- Step 1: `### Step 2.5: Diverge & Choose`, `#### What a draft is`, `#### Getting drafts that actually differ`, `#### Render through the platform`, `#### Present and choose`, `### Step 3: Spawn Coding Agent`.
- Step 2: the header and separator rows, then three rows starting `| Native artboard/design surface |`, ``| `canvas-preview` (the adapter maps it) |``, `| Neither |`, then the line ending `Never degrade silently.`
- Step 3: `- Design tokens: .writ/docs/design-system.md (loaded)` in Step 2, the `| Mockups for a spec that already exists |` row, and the `**Terminal constraint:**` line.
- Step 4: no `failed` in the first summary; `1 passed` in the second.
- Step 5: `pass`; `2` for each plugin copy (the `Read` line and the References link, with the path rewritten to `${CLAUDE_PLUGIN_ROOT}/skills/design-divergence/SKILL.md`).

**Implementation Reference:** Story 2 — Files: `plugins/writ/commands/prototype.md`, `cursor/plugin/commands/prototype.md` (regenerated)

**Status:** [ ] Pass  [ ] Fail

**Notes:**

---

### Scenario 8: The Story 2 diff touches only the subsection body and one References line, and the file shrank

**Source:** Acceptance Criteria (AC-2.3) — Story 2
**Feature:** none
**Verification:** human — no recipe

**Preconditions:**
- Setup block pasted; `reset` prints nothing.

**Steps:**
1. `git -C "$CL" log --oneline 6b10789..HEAD -- commands/prototype.md`
2. `git -C "$CL" diff 6b10789^ 6b10789 -- commands/prototype.md | grep '^@@'`
3. `git -C "$CL" diff 6b10789^ 6b10789 -- commands/prototype.md | grep -E '^[-+]' | grep -vE '^(\+\+\+|---) ' | cut -c1-80`
4. `git -C "$CL" show 6b10789^:commands/prototype.md | wc -c; wc -c < "$CL/commands/prototype.md"`

**Expected Result:**
- Step 1: prints nothing (no later commit changed the file).
- Step 2: two hunks: `@@ -144,23 +144,10 @@` (the subsection) and `@@ -338,3 +325,4 @@` (References). The gate paragraph, the `--diverge`/`--no-diverge` rows, `#### What a draft is`, `#### Render through the platform`, `#### Present and choose`, the `exploration.md` paragraph, and the frontmatter sit outside both hunks.
- Step 3: removed: the three-line lead-in ("Asking one agent for "a few options" produces one idea three times…") and the five numbered rules; added: the four-line `Read` note and `- Divergence rules: [design-divergence](../skills/design-divergence/SKILL.md)`. Blank lines may also show.
- Step 4: `18773`, then `18034`.

**Implementation Reference:** Story 2 — WWB decision 2 (byte identity checked section by section at verification time)

**Status:** [ ] Pass  [ ] Fail

**Notes:**

---

### Scenario 9: `/prototype --diverge` reads the skill, declares axes before drafting, and records the choice

**Source:** Experience Design (Who uses it: a solo builder running `/prototype`; Entry point) — Story 2; Business Rule 9
**Feature:** none
**Verification:** human — no recipe

**Preconditions:**
- Setup block pasted; `reset` prints nothing. `ls "$CL/.writ/prototypes" 2>&1` reports no such directory.
- `live` running in a new session.

**Steps:**
1. `/prototype --diverge "an HTML page that lists Writ's commands grouped by pipeline stage, each with its one-line purpose"`
2. Let it run until it presents the drafts. Read the presentation.
3. Reply: `Pick B. Stop here; do not build.`
4. In the first shell: `git -C "$CL" status --short; ls "$CL"/.writ/prototypes/*/; cat "$CL"/.writ/prototypes/*/exploration.md`
5. `reset`

**Expected Result:**
- Step 2: before any draft exists, the session reads `skills/design-divergence/SKILL.md` and names two or three axes (for this page, from the UI catalog: information density, navigation model, progressive disclosure, or primary action placement), with a distinct combination per draft.
- Step 2: each draft is made in its own context (three spawns in one message, or the session says so). Drafts render as self-contained HTML pages, or the session says plainly that it could not render them and gives a structural description per draft.
- Step 2: the presentation starts `🎨 Three takes on …` and has `A —`, `B —`, `C —` lines, each naming its axis combination and the trade-off it accepts, then the pick / fourth draft / stop line.
- Step 4: `git status` lists only `.writ/prototypes/`. One folder `<date>-<slug>/` holds `exploration.md` and the rendered drafts. `exploration.md` lists the axes, one row per draft, B as the chosen draft, and why A and C lost. Nothing was written under `.writ/specs/` and no code was built.
- Step 5: prints nothing.

**Implementation Reference:** Story 2 — Files: `commands/prototype.md` (Step 2.5)

**Status:** [ ] Pass  [ ] Fail

**Notes:**

---

## Story 3: Gate 0 Usage-First Divergence and the Gate 0 Divergence Switch

### Scenario 10: Gate 0 carries every text-contract literal; dropping the hand-off label fails the wiring test

**Source:** Acceptance Criteria (AC-3.1) — Story 3; Business Rules 3 (Usage first), 4 (Two sketches, independent), 5 (Commit before sketching), 6 (Choice), 7 (Hand-off to Gate 1)
**Feature:** none
**Verification:** human — no recipe

**Preconditions:**
- Setup block pasted; `reset` prints nothing.

**Steps:**
1. `sed -n '/^\*\*Design divergence (boundary-crossing route)\.\*\*/,/^---$/p' "$CL/commands/implement-story.md"`
2. `pt scripts/tests/test_design_divergence_wiring.py -q -k Gate0DivergenceLiteralsTest 2>&1 | tail -1`
3. `` sed -i '' 's/ as `design sketch (Gate 0 divergence)`;/;/' "$CL/commands/implement-story.md"; pt scripts/tests/test_design_divergence_wiring.py -q -k Gate0DivergenceLiteralsTest 2>&1 | grep -E 'design sketch|failed|passed'; reset ``

**Expected Result:**
- Step 1: five bold-led paragraphs, then `---`: `**Design divergence (boundary-crossing route).**`, `**Switch.**`, `**Route.**`, `**Sketches.**`, `**Choice.**`. No `####` heading and no `> **Agent:**` marker inside.
- Step 1, Route: triggers `--full-pipeline`, `--panel`, and `route: review-agent`; a bash fence holds the three predictor commands verbatim: `boundary-map.py compute … > .writ/state/boundary-<story-stem>.json`, `change-surface.py classify --changed <planned files>`, `boundary-map.py crossings --map … --surface <class>`.
- Step 1, Sketches: opens with `Read skills/design-divergence/SKILL.md`; writes 3 to 10 lines of caller usage from the ACs (or tasks) to `.writ/state/divergence-<story-stem>.md` before picking two axes from the skill's catalog; spawns two `readonly` sketches at `anchor` in one message, each given the story, `spec_lite_for_coding`, the usage, its own axes, and the caller as persona; neither sees the other; each returns `COMMITMENT:`, `SKETCH:` (≤40 lines), `USAGE FIT:`.
- Step 1, Choice: prefers unchanged usage, then fewer new public names; adds the sketch, usage, and reason to the Gate 0 warnings as `design sketch (Gate 0 divergence)`.
- Step 2: `15 passed`.
- Step 3: an assertion naming `design sketch (Gate 0 divergence)`, then `1 failed, 14 passed` (with a deselected count). `reset` prints nothing.

**Implementation Reference:** Story 3 — Files: `commands/implement-story.md` (`#### Gate 0` block), `scripts/tests/test_design_divergence_wiring.py` (`Gate0DivergenceLiteralsTest`)

**Status:** [ ] Pass  [ ] Fail

**Notes:**

---

### Scenario 11: The switch and all seven report states appear in Gate 0, and config-format.md documents the switch

**Source:** Acceptance Criteria (AC-3.2) — Story 3; Business Rule 1 (Switch); Error Map "Gate 0 switch read" (config or line absent; value not `on`/`off`); Experience Design State Catalog
**Feature:** none
**Verification:** human — no recipe

**Preconditions:**
- Setup block pasted; `reset` prints nothing.

**Steps:**
1. `` grep -o '`gate0-divergence: [^`]*`' "$CL/commands/implement-story.md" | sort -u ``
2. `sed -n '/^\*\*Switch\.\*\*/p' "$CL/commands/implement-story.md"`
3. `grep -n 'Gate 0 Divergence' "$CL/.writ/docs/config-format.md" | cut -c1-110; sed -n '/^## Gate 0 Divergence/,/^## Rules/p' "$CL/.writ/docs/config-format.md"`
4. `grep -c 'Gate 0 Divergence' "$CL/.writ/config.md"`
5. `pt scripts/tests/test_design_divergence_wiring.py -q -k Gate0DivergenceSwitchTest 2>&1 | tail -1`

**Expected Result:**
- Step 1: exactly seven lines, one per State Catalog row: `chose <A|B> (<axis combination>) — <why the other lost>`, `off (config)`, `on (malformed: <value>)`, `skip (arch-check abort)`, `skip (route evaluator-agent)`, `skip (sketch incomplete: <A|B>)`, `skip (unverifiable: <reason>)`, each after `gate0-divergence: ` and in backticks.
- Step 2: `` `- **Gate 0 Divergence:** off` `` prints `gate0-divergence: off (config)`; absent or `on` means on; another value is on and prints `gate0-divergence: on (malformed: <value>)`.
- Step 3: the Supported Keys row (`` | `Gate 0 Divergence` | implement-story (Gate 0) | On by default; `off` disables the boundary-crossing-route sketches; … ``) and a `## Gate 0 Divergence` section: the fenced line, `on|off` under `## Conventions`, never detected or offered for saving, no line or `on` means on, any other value means on with the malformed line "so a typo never disables the sketches", only Gate 0 reads it, `/prototype` is unaffected.
- Step 4: `0`. The project's own config has no line, so Gate 0 divergence is on by default; a project with no `.writ/config.md` has no line either.
- Step 5: `6 passed`.

**Implementation Reference:** Story 3 — Files: `commands/implement-story.md` (`**Switch.**`), `.writ/docs/config-format.md` (Supported Keys; `## Gate 0 Divergence`)

**Status:** [ ] Pass  [ ] Fail

**Notes:**

---

### Scenario 12: No divergence outcome blocks the story, and the default-path and verdict-provenance checks pass

**Source:** Acceptance Criteria (AC-3.3) — Story 3; Business Rule 8 (Never blocking)
**Feature:** none
**Verification:** human — no recipe

**Preconditions:**
- Setup block pasted; `reset` prints nothing.

**Steps:**
1. `sed -n '/^\*\*Design divergence (boundary-crossing route)\.\*\*/p' "$CL/commands/implement-story.md"`
2. `pt scripts/tests/test_implement_story_default_path.py -q 2>&1 | tail -1; pt scripts/tests/test_design_divergence_wiring.py -q -k Gate0DivergenceNeverBlocksTest 2>&1 | tail -1`
3. `(cd "$CL" && python3 scripts/verdict-provenance.py check --command commands/implement-story.md --repo . --prose-only-blocking | sed -n '1p;$p')`

**Expected Result:**
- Step 1: `` **Design divergence (boundary-crossing route).** Each run prints a `gate0-divergence:` line and never blocks: no DEGRADED, AskQuestion, `review_cycle` increment, or retry. ``
- Step 2: no `failed` in the first summary (Gate 0 carries no unguarded `> **Agent:**` marker); `2 passed` in the second.
- Step 3: line 1 `pass`; the summary reports 10 gates and 0 findings. No new `gates:` entry was needed because the block adds no `#### Gate` heading.

**Implementation Reference:** Story 3 — WWB Test Results (`verdict-provenance.py check --prose-only-blocking` → pass, 10 gates, 0 findings)

**Status:** [ ] Pass  [ ] Fail

**Notes:**

---

### Scenario 13: Outside Gate 0, only the Overview clause, the Pipeline row, and the References line changed

**Source:** Acceptance Criteria (AC-3.4) — Story 3
**Feature:** none
**Verification:** human — no recipe

**Preconditions:**
- Setup block pasted; `reset` prints nothing.

**Steps:**
1. `git -C "$CL" log --oneline 49719ed..HEAD -- commands/implement-story.md`
2. `git -C "$CL" diff 49719ed^ 49719ed -- commands/implement-story.md | grep '^@@'`
3. `git -C "$CL" diff 49719ed^ 49719ed -- commands/implement-story.md | grep -E '^[-+](Default is|\| Gate 0 \||- Skills, each)' | cut -c1-120`
4. `for r in '/^### Step 1: Story Selection/,/^### Step 3: Run Pipeline/' '/^### Step 3: Run Pipeline/,/^#### Gate 0: Architecture/' '/^#### Gate 0.5/,/^## Error Handling/'; do diff -q <(git -C "$CL" show 49719ed^:commands/implement-story.md | sed -n "${r}p") <(sed -n "${r}p" "$CL/commands/implement-story.md") >/dev/null && echo "identical: $r" || echo "DIFFERS: $r"; done`
5. `pt scripts/tests/test_design_divergence_wiring.py -q -k Gate0DivergenceOtherEditsTest 2>&1 | tail -1`

**Expected Result:**
- Step 1: prints nothing (no later commit changed the file).
- Step 2: four hunks: `@@ -51,7 +51,7 @@` (Overview), `@@ -82,7 +82,7 @@` (Pipeline), `@@ -191,6 +191,24 @@` (the 18-line Gate 0 block), `@@ -478,4 +496,4 @@` (References). No frontmatter hunk, so `gates:` is unchanged.
- Step 3: three pairs. The Overview line gains "and two Gate 0 sketch spawns on the boundary-crossing route"; the `| Gate 0 |` row gains "two sketch spawns on the boundary-crossing route" in Runs as and `` `design-divergence` (boundary-crossing route) `` in Skill; the References skills line gains `[design-divergence](../skills/design-divergence/SKILL.md)`.
- Step 4: three `identical:` lines: Steps 1 and 2 (the routing table), the sub-agent completeness and worktree notes, and Gate 0.5 through Gate 5.
- Step 5: `3 passed`.

**Implementation Reference:** Story 3 — WWB decision 4 (Gate 0.5 to Gate 5 verified byte-identical section by section)

**Status:** [ ] Pass  [ ] Fail

**Notes:**

---

### Scenario 14: The block is under 2,000 bytes and the byte ratchet is re-pinned with a dated disclosure

**Source:** Acceptance Criteria (AC-3.5) — Story 3; DEV-008
**Feature:** none
**Verification:** human — no recipe

**Preconditions:**
- Setup block pasted; `reset` prints nothing.

**Steps:**
1. `awk '/^\*\*Design divergence \(boundary-crossing route\)\.\*\*/{p=1} p&&/^---$/{exit} p' "$CL/commands/implement-story.md" | sed '$d' | wc -c`
2. `git -C "$CL" show 49719ed^:commands/implement-story.md | wc -c; wc -c < "$CL/commands/implement-story.md"`
3. `grep -n -B3 '"commands/implement-story.md": ' "$CL/scripts/tests/test_governor_enforcement.py"`
4. `git -C "$CL" diff 49719ed^ 49719ed -- scripts/tests/test_harness_cuts.py | grep -E '^[-+] '`
5. `pt scripts/tests/test_governor_enforcement.py scripts/tests/test_harness_cuts.py -q 2>&1 | tail -1`
6. `(cd "$CL" && python3 scripts/gen-platform-trees.py --check | head -1); grep -c 'Design divergence (boundary-crossing route)' "$CL/plugins/writ/commands/implement-story.md" "$CL/cursor/plugin/commands/implement-story.md"`

**Expected Result:**
- Step 1: `1994`, under 2,000.
- Step 2: `36226`, then `38434`.
- Step 3: `# 2026-10-26 (2026-10-25-design-divergence Story 3): 11266 -> 13474; Gate 0`, `# boundary-crossing divergence block (1994 bytes) plus its Overview clause,`, `# Pipeline Gate 0 row, and References link.`, directly above `"commands/implement-story.md": 13474,` (38,434 − 24,960 = 13,474).
- Step 4: one removed line, `self.assertLess(recorded[rel], OVERAGE_BEFORE[rel])`, and one added comment pointing to `test_ac_3_4_each_lowered_entry_has_a_dated_ledger_line` (DEV-008).
- Step 5: no `failed`.
- Step 6: `pass`; `1` for each plugin copy.

**Implementation Reference:** Story 3 — Files: `scripts/tests/test_governor_enforcement.py` (`KNOWN_OVER_BUDGET`), `scripts/tests/test_harness_cuts.py`

**Status:** [ ] Pass  [ ] Fail

**Notes:**

---

### Scenario 15: A missing planned set, a failed helper, or a failed sketch skips divergence with a reason and no retry

**Source:** Error Map "Route predictor" (planned set empty; `crossings` unverifiable or a script cannot run) and "Sketch spawn" (spawn error or timeout; a missing field) — Story 3; Shadow Path "Gate 0 divergence" (nil, empty, upstream error); DEV-009
**Feature:** none
**Verification:** human — no recipe

**Preconditions:**
- Setup block pasted; `reset` prints nothing.

**Steps:**
1. `` sed -n '/^\*\*Route\.\*\*/,/^\*\*Sketches\.\*\*/p' "$CL/commands/implement-story.md" | grep -v '^python3\|^```' ``
2. `sed -n '/^\*\*Sketches\.\*\*/p' "$CL/commands/implement-story.md"`
3. `pt scripts/tests/test_design_divergence_wiring.py -q -k "test_sketch_failure_skips_without_retry or test_runs_after_proceed_or_caution_or_resolved_abort" 2>&1 | tail -1`

**Expected Result:**
- Step 1: divergence runs on PROCEED, CAUTION, `unverifiable` (DEV-009), or an ABORT resolved as proceed. "No planned files or usage, or a failed or `unverifiable` helper" prints `gate0-divergence: skip (unverifiable: <reason>)`. That one rule covers an empty planned set (nil input), a story with neither ACs nor tasks to take usage from (empty input), and a predictor script that cannot run (upstream error).
- Step 2: usage comes "from the ACs (or tasks)", so a story with no ACs falls back to its tasks. "A spawn error or missing field prints `gate0-divergence: skip (sketch incomplete: <A|B>)`". With the block's lead ("no … retry"), a failed sketch is not retried and the pipeline continues.
- Step 3: `2 passed`.
- The empty planned set is also run live in Scenario 20. A failed sketch spawn has no live scenario: it cannot be triggered reliably.

**Implementation Reference:** Story 3 — Files: `commands/implement-story.md` (`**Route.**`, `**Sketches.**`)

**Status:** [ ] Pass  [ ] Fail

**Notes:**

---

### Scenario 16: Converged sketches, an ABORT resolved as proceed, and a later recode or escalation are handled without re-running Gate 0

**Source:** Interaction Edge Cases — Story 3; Experience Design State Catalog "Skipped, ABORT"
**Feature:** none
**Verification:** human — no recipe

**Preconditions:**
- Setup block pasted; `reset` prints nothing.

**Steps:**
1. `sed -n '/^\*\*Choice\.\*\*/p' "$CL/commands/implement-story.md"`
2. `grep -o 'Run on PROCEED[^;]*; another ABORT prints [^.]*' "$CL/commands/implement-story.md"`
3. `grep -o 'Gate 3, Gate 4 and Gate 4.5 FAIL → back to Gate 1\|do not restart Gate 0; do not AskQuestion' "$CL/commands/implement-story.md"`
4. `grep -n 'any arch-check warnings' "$CL/commands/implement-story.md" | cut -c1-12`

**Expected Result:**
- Step 1: the Choice paragraph prefers unchanged usage, then fewer new public names, and notes `sketches converged` when the two are equal. Nothing in it fails the gate.
- Step 2: an ABORT the user resolved as proceed runs divergence; any other ABORT prints `gate0-divergence: skip (arch-check abort)`.
- Step 3: both phrases print. A Gate 3 FAIL returns to Gate 1, not Gate 0, and the two-fail escalation says not to restart Gate 0, so the design sketch from the first Gate 0 stays in the warnings.
- Step 4: `238:Spawns th`, the one match, in Gate 1: Gate 1 passes "any arch-check warnings" to the coding agent, the channel the sketch travels in (Business Rule 7). Gate 1 was not edited (Scenario 13 shows no Gate 1 hunk).
- No live scenario: the ABORT path needs `--full-pipeline` and a story the architecture agent rejects.

**Implementation Reference:** Story 3 — Files: `commands/implement-story.md` (`**Route.**`, `**Choice.**`, `## Pipeline` control flow, Gate 1)

**Status:** [ ] Pass  [ ] Fail

**Notes:**

---

### Scenario 17: A boundary-crossing story gets the caller usage first, two sketches that differ in structure, and a `chose` line

**Source:** Experience Design Happy path, Moment of Truth, Feedback Model, State Catalog "Chosen" — Story 3; Shadow Path "Gate 0 divergence" (happy path); Business Rules 2 to 7; Error Map "Gate 0 switch read" (line absent → on)
**Feature:** none
**Verification:** human — no recipe

**Preconditions:**
- Setup block pasted; `reset` prints nothing; `g0` lists the three fixture stories.
- `grep -c 'Gate 0 Divergence' "$CL/.writ/config.md"` prints `0`.
- `live` running in a new session.

**Steps:**
1. `/implement-story .writ/specs/2026-10-29-uat-gate0/user-stories/story-1-order-export.md`
2. Watch Gate 0. When the session moves past it, press Escape and reply: `Stop here. Print the gate0-divergence line, both sketches' COMMITMENT lines, and the design sketch block you added to the Gate 0 warnings.`
3. In the first shell: `cat "$CL/.writ/state/divergence-story-1-order-export.md"`
4. `reset`

**Expected Result:**
- Step 2, order of work in Gate 0: `arch-check.py` runs (default path) and continues; the three predictor commands run over `tests/test_orders_export.py`, `migrations/0002_orders.sql`, and `api/orders.py`; `classify` returns `full-stack` and `crossings` returns route `review-agent` with reason `full_stack_surface`. Then the session reads `skills/design-divergence/SKILL.md`, writes the usage file, names two axes, and spawns two sketches in one message.
- Step 2: each sketch returns `COMMITMENT:`, then `SKETCH:` (at most 40 lines), then `USAGE FIT:`.
- Step 2: the two commitments differ in structure, for example a synchronous export against a job the caller polls, or an orders table against an append-only events table, not only in names. Judge by eye: this is the spec's moment of truth.
- Step 2: the line reads `gate0-divergence: chose A (<axis combination>) — <one line on why B lost>` (or `chose B …`). The design sketch block is labeled `design sketch (Gate 0 divergence)` and holds the chosen sketch, the caller usage, and the reason. No question was asked and nothing was marked DEGRADED during Gate 0.
- Step 3: 3 to 10 lines of calls, requests and responses, or queries a caller would write to export a customer's orders, drawn from AC-1.1 (orders present) and AC-1.2 (no orders). In the Step 2 transcript, this file was written before the axes were named.
- Step 4: prints nothing.

**Status:** [ ] Pass  [ ] Fail

**Notes:**

---

### Scenario 18: With the switch off, Gate 0 prints `off (config)` and makes no sketches

**Source:** Experience Design State Catalog "Off" — Story 3; Business Rule 1 (Switch); Must Include 4
**Feature:** none
**Verification:** human — no recipe

**Preconditions:**
- Setup block pasted; `reset` prints nothing; `g0` lists the three fixture stories.
- `sw off` prints `8:- **Gate 0 Divergence:** off`.
- `live` running in a new session.

**Steps:**
1. `/implement-story .writ/specs/2026-10-29-uat-gate0/user-stories/story-1-order-export.md`
2. When the session moves past Gate 0, press Escape and reply: `Stop here. Print the gate0-divergence line.`
3. In the first shell: `ls "$CL"/.writ/state/divergence-* 2>&1`
4. `reset`

**Expected Result:**
- Step 2: `gate0-divergence: off (config)`. Gate 0 did not run the three predictor commands, did not read `skills/design-divergence/SKILL.md`, and spawned no sketch; the pipeline moved on to Gate 0.5 as it does without the feature.
- Step 3: no such file.
- Step 4: prints nothing (`.writ/config.md` restored).

**Status:** [ ] Pass  [ ] Fail

**Notes:**

---

### Scenario 19: A low-stakes story skips with `route evaluator-agent`, and a malformed switch value stays on and says so

**Source:** Error Map "Gate 0 switch read" (value not `on`/`off`) — Story 3; Experience Design State Catalog "Skipped, low stakes" and "On, malformed"; Business Rules 1 and 2
**Feature:** none
**Verification:** human — no recipe

**Preconditions:**
- Setup block pasted; `reset` prints nothing; `g0` lists the three fixture stories.
- `live` running in a new session.

**Steps:**
1. `/implement-story .writ/specs/2026-10-29-uat-gate0/user-stories/story-2-glossary-note.md`
2. When the session moves past Gate 0, press Escape and reply: `Stop here. Print every gate0-divergence line from Gate 0.`
3. `/exit`. In the first shell: `ls "$CL"/.writ/state/divergence-* 2>&1; reset; g0; sw of`
4. `live` again in a new session; repeat Steps 1 and 2.
5. `/exit`. In the first shell: `ls "$CL"/.writ/state/divergence-* 2>&1; reset`

**Expected Result:**
- Step 2: the predictor runs over `docs/orders-glossary.md`; `classify` returns `cross-component` and `crossings` returns route `evaluator-agent`. The line reads `gate0-divergence: skip (route evaluator-agent)`. No skill read and no sketch spawn.
- Step 3: no such file; `sw of` prints `8:- **Gate 0 Divergence:** of`.
- Step 4: `gate0-divergence: on (malformed: of)`, and divergence stays on: the predictor still runs and the run reports `gate0-divergence: skip (route evaluator-agent)`. No `off (config)` line.
- Step 5: no such file; `reset` prints nothing.

**Status:** [ ] Pass  [ ] Fail

**Notes:**

---

### Scenario 20: A story with no planned files skips as unverifiable, and the pipeline continues

**Source:** Shadow Path "Gate 0 divergence" (nil input) — Story 3; Error Map "Route predictor" (planned set empty); Experience Design State Catalog "Skipped, unverifiable"; DEV-009
**Feature:** none
**Verification:** human — no recipe

**Preconditions:**
- Setup block pasted; `reset` prints nothing; `g0` lists the three fixture stories.
- `live` running in a new session.

**Steps:**
1. `/implement-story .writ/specs/2026-10-29-uat-gate0/user-stories/story-3-no-files.md`
2. When the session moves past Gate 0 (or stops), press Escape and reply: `Stop here. Print the arch-check verdict and the gate0-divergence line.`
3. In the first shell: `ls "$CL"/.writ/state/divergence-* 2>&1; reset`

**Expected Result:**
- Step 2: `arch-check.py` returns `unverifiable` (no `--planned` files); Gate 0 continues and does not mark the story DEGRADED. Because a script `unverifiable` still runs divergence (DEV-009), a line is printed: `gate0-divergence: skip (unverifiable: <reason>)`, with a reason naming the missing planned files. No sketch spawn, no question.
- Step 3: no such file; `reset` prints nothing.

**Status:** [ ] Pass  [ ] Fail

**Notes:**

---

### Scenario 21: `--quick` prints no `gate0-divergence:` line and makes no sketches

**Source:** Experience Design State Catalog ("`--quick` and `--review-only` skip Gate 0 and print no line") — Story 3
**Feature:** none
**Verification:** human — no recipe

**Preconditions:**
- Setup block pasted; `reset` prints nothing; `g0` lists the three fixture stories.
- `live` running in a new session.

**Steps:**
1. `/implement-story .writ/specs/2026-10-29-uat-gate0/user-stories/story-1-order-export.md --quick`
2. When the coding agent is spawned, press Escape and reply: `Stop here. Did Gate 0 print a gate0-divergence line?`
3. In the first shell: `ls "$CL"/.writ/state/divergence-* 2>&1; reset`

**Expected Result:**
- Step 2: no `gate0-divergence:` line, no read of `skills/design-divergence/SKILL.md`, no sketch spawn. Quick Mode still runs the Gate 0 script (`arch-check.py`), and the Gate 0 block does not name `--quick`, so a `gate0-divergence:` line here is a Fail: quote it in Notes.
- Step 3: no such file; `reset` prints nothing.

**Status:** [ ] Pass  [ ] Fail

**Notes:**

---

## Story 4: Divergence Trial Harness

### Scenario 22: `init` writes a six-brief skeleton and refuses any other set without writing a file

**Source:** Acceptance Criteria (AC-4.1) — Story 4; Error Map `init` (not six briefs, wrong medium split, missing header); DEV-003
**Feature:** none
**Verification:** human — no recipe

**Preconditions:**
- Setup block pasted.

**Steps:**
1. `rm -f "$W/t1.json"; rc dt init --briefs "$FX/briefs" --out "$W/t1.json"; cat "$W/out.txt"`
2. `grep -c '"brief_sha256"' "$W/t1.json"; grep -c '"arms": {}' "$W/t1.json"; grep '"schema"' "$W/t1.json"`
3. `rc dt init --briefs "$FX/briefs" --out "$W/t1.json"; rc dt init --briefs "$FX/briefs" --out "$W/t1.json" --force`
4. `rm -rf "$W/b5" && mkdir "$W/b5" && cp "$FX"/briefs/*.md "$W/b5/" && rm "$W/b5/ui-2.md"; rc dt init --briefs "$W/b5" --out "$W/t5.json"; ls "$W/t5.json" 2>&1`
5. `cp "$FX/briefs/ui-2.md" "$W/b5/" && sed -i '' 's/^medium: ui$/medium: api/' "$W/b5/ui-2.md" && sed -i '' '1d' "$W/b5/api-1.md"; rc dt init --briefs "$W/b5" --out "$W/t5.json"; ls "$W/t5.json" 2>&1`

**Expected Result:**
- Step 1: `exit 0`; then `pass`, six lines `brief: api-1 medium=api`, `brief: api-2 medium=api`, `brief: data-model-1 medium=data-model`, `brief: data-model-2 medium=data-model`, `brief: ui-1 medium=ui`, `brief: ui-2 medium=ui`, and `divergence-trial: initialized — 6 briefs, no arms recorded`.
- Step 2: `6`, `6`, `  "schema": "divergence-trial-v1",`.
- Step 3: `exit 2 stdout-bytes 0`, with `reason: out_exists …/t1.json (pass --force to replace it)` and `divergence-trial: refused — out_exists …` on stderr; then `exit 0` with `--force`.
- Step 4: `exit 2 stdout-bytes 0`; on stderr `reason: brief_count 5 (need 6)`, `reason: medium_split ui=1 api=2 data-model=2 (need 2 each)`, `divergence-trial: refused — init wrote nothing — brief_count 5 (need 6)`; `ls` reports no such file.
- Step 5: `exit 2 stdout-bytes 0`; on stderr `reason: missing_header api-1.md id`, `reason: medium_split ui=1 api=3 data-model=2 (need 2 each)`, and a summary ending `init wrote nothing — missing_header api-1.md id`; no file.

**Implementation Reference:** Story 4 — Files: `scripts/divergence-trial.py` (`init`), `scripts/tests/fixtures/divergence-trial/briefs/`

**Status:** [ ] Pass  [ ] Fail

**Notes:**

---

### Scenario 23: `record` stores a valid arm beside the trial file and refuses every malformed drafts file unchanged

**Source:** Acceptance Criteria (AC-4.2) — Story 4; Error Map `record` (not three drafts; `Commitment:` missing in axes or present in naive); DEV-002, DEV-003
**Feature:** none
**Verification:** human — no recipe

**Preconditions:**
- Setup block pasted.
- `rm -rf "$W/r" && mkdir "$W/r" && dt init --briefs "$FX/briefs" --out "$W/r/trial.json" | tail -1` prints the `initialized` line.

**Steps:**
1. `rc dt record --trial "$W/r/trial.json" --brief ui-1 --arm axes --drafts "$FX/drafts/axes.md"; cat "$W/out.txt"; cmp "$FX/drafts/axes.md" "$W/r/raw/ui-1/axes.md" && echo copied`
2. `H=$(h12 "$W/r/trial.json"); for f in invalid/naive-with-commitment.md:naive drafts/axes.md:naive invalid/missing-title.md:naive invalid/empty-structure.md:naive invalid/axes-missing-commitment.md:axes invalid/missing-trade-off.md:axes invalid/two-drafts.md:axes invalid/four-drafts.md:axes; do echo "== $f"; rc dt record --trial "$W/r/trial.json" --brief ui-2 --arm "${f##*:}" --drafts "$FX/${f%%:*}"; done`
3. `[ "$H" = "$(h12 "$W/r/trial.json")" ] && echo "trial unchanged"; ls "$W/r/raw"`

**Expected Result:**
- Step 1: `exit 0`; `pass`, `brief: ui-1 arm=axes drafts=3 sha256=<12 hex>`, `raw: raw/ui-1/axes.md`, `divergence-trial: recorded ui-1 axes — 3 drafts, 1 of 12 arms recorded`; `copied`. The raw copy sits beside the trial file (DEV-002).
- Step 2: every case prints `exit 2 stdout-bytes 0` with its reasons on stderr and a summary `divergence-trial: refused — ui-2 <arm> not recorded — <first reason>`:
  - `naive-with-commitment.md` as naive: `commitment_present draft 2 (naive drafts carry none)`
  - `axes.md` as naive: `commitment_present draft 1`, `draft 2`, and `draft 3`
  - `missing-title.md` as naive: `missing_field draft 2 Title`
  - `empty-structure.md` as naive: `empty_field draft 3 Structure`
  - `axes-missing-commitment.md` as axes: `commitment_missing draft 2 (axes drafts declare one)`
  - `missing-trade-off.md` as axes: `missing_field draft 3 Trade-off`
  - `two-drafts.md` as axes: `draft_count 2 (need 3)`
  - `four-drafts.md` as axes: `draft_count 4 (need 3)`
- Step 3: `trial unchanged`; `ui-1` only.

**Implementation Reference:** Story 4 — Files: `scripts/divergence-trial.py` (`record`), `scripts/tests/fixtures/divergence-trial/invalid/`

**Status:** [ ] Pass  [ ] Fail

**Notes:**

---

### Scenario 24: `blind` refuses a missing arm, then writes a sheet with no titles or commitments and a key, byte-stable for a seed

**Source:** Acceptance Criteria (AC-4.3) — Story 4; Error Map `blind` (an arm missing); Business Rule 10 (Trial integrity); DEV-004
**Feature:** none
**Verification:** human — no recipe

**Preconditions:**
- Setup block pasted.

**Steps:**
1. `rm -rf "$W/b" && mkdir "$W/b" && dt init --briefs "$FX/briefs" --out "$W/b/trial.json" >/dev/null; for x in api-1 api-2 data-model-1 data-model-2 ui-1 ui-2; do dt record --trial "$W/b/trial.json" --brief $x --arm axes --drafts "$FX/drafts/axes.md" >/dev/null; [ $x = ui-2 ] || dt record --trial "$W/b/trial.json" --brief $x --arm naive --drafts "$FX/drafts/naive.md" >/dev/null; done; rc dt blind --trial "$W/b/trial.json" --sheet "$W/b/rating-sheet.md" --seed 7; ls "$W/b"`
2. `dt record --trial "$W/b/trial.json" --brief ui-2 --arm naive --drafts "$FX/drafts/naive.md" | tail -1; rc dt blind --trial "$W/b/trial.json" --sheet "$W/b/rating-sheet.md" --seed 7; tail -1 "$W/out.txt"`
3. `S="$W/b/rating-sheet.md"; for p in '^## Brief ' '^### Set [XY]$' '^#### Draft [123]$' '^### Rating: ' '^Commitment:' '^Title:' '^(distinct_X|distinct_Y|more_distinct|render_only_enough|note):$'; do echo "$(grep -cE "$p" "$S") $p"; done; grep -ciwE 'axes|naive' "$S"`
4. `sed -n '/^## Brief api-1/,/^#### Draft 2/p' "$S"`
5. `python3 -c 'import json,hashlib,sys; b=json.load(open(sys.argv[1]))["blind"]; print(b["sheet"], b["key"], b["key_sha256"] == hashlib.sha256(open(sys.argv[2],"rb").read()).hexdigest(), len(b["sheet_body_sha256"]))' "$W/b/trial.json" "$W/b/key.json"`
6. `A=$(h12 "$S"); dt blind --trial "$W/b/trial.json" --sheet "$S" --seed 7 >/dev/null; [ "$A" = "$(h12 "$S")" ] && echo "same sheet"`
7. `rc dt record --trial "$W/b/trial.json" --brief ui-1 --arm axes --drafts "$FX/drafts/axes.md"`

**Expected Result:**
- Step 1: `exit 2 stdout-bytes 0`; on stderr `reason: missing_arm ui-2 naive` and `divergence-trial: refused — no sheet or key written — missing_arm ui-2 naive`; `ls` shows only `raw` and `trial.json`.
- Step 2: `divergence-trial: recorded ui-2 naive — 3 drafts, 12 of 12 arms recorded`; `exit 0 …`; `divergence-trial: blinded 6 briefs — sheet rating-sheet.md, key key.json`.
- Step 3: `6`, `12`, `36`, `6`, `0`, `0`, `30` for the seven patterns (every rating field blank), then `0` (no arm name anywhere on the fixture sheet).
- Step 4: `## Brief api-1 (medium: api)`, `### Set X`, `#### Draft 1`, then a `Structure:` block and a `Trade-off:` line with no `Title:` and no `Commitment:` line, then `#### Draft 2`.
- Step 5: `rating-sheet.md key.json True 64`.
- Step 6: `same sheet`.
- Step 7: `exit 2 stdout-bytes 0`; `reason: already_blinded (re-recording would invalidate the sheet and key)` (DEV-004).

**Implementation Reference:** Story 4 — Files: `scripts/divergence-trial.py` (`blind`); WWB decisions 2 and 3

**Status:** [ ] Pass  [ ] Fail

**Notes:**

---

### Scenario 25: `rate` stores a complete rating by set label and refuses a partial, out-of-range, or edited sheet unchanged

**Source:** Acceptance Criteria (AC-4.4) — Story 4; Error Map `rate` (drafts edited after blinding; a field blank or out of range, a note too long or multi-line); Interaction Edge Cases (rater fills only some briefs; rater edits a draft by accident)
**Feature:** none
**Verification:** human — no recipe

**Preconditions:**
- Setup block pasted.
- `ftrial` prints `divergence-trial: blinded 6 briefs — sheet rating-sheet.md, key key.json`; `tf` prints `rated_by=None ratings=None blind=set`.

**Steps:**
1. `H=$(h12 "$W/ft/trial.json"); SH="$W/ft/rating-sheet.md"; fill 4 3 1; perl -pi -e '$d ||= s/^more_distinct: .+$/more_distinct:/' "$SH"; rc frate`
2. `fill 4 3 1; perl -pi -e '$d ||= s/^distinct_X: \d$/distinct_X: 4/' "$SH"; rc frate`
3. `fill 4 3 1; perl -pi -e 's/^note: fixture rating 1$/"note: " . "x" x 201/e' "$SH"; rc frate`
4. `fill 4 3 1; perl -pi -e 's/^note: fixture rating 1$/note: fixture rating 1\nsecond line/' "$SH"; rc frate`
5. `sed -i '' '/^second line$/d' "$SH"; fill 4 3 1; sed -i '' 's/^- a single table$/- one wide table/' "$SH"; rc frate`
6. `rc dt rate --trial "$W/ft/trial.json" --sheet "$SH" --rated-by " "`
7. `[ "$H" = "$(h12 "$W/ft/trial.json")" ] && echo "trial unchanged"; tf`
8. `sed -i '' 's/^- one wide table$/- a single table/' "$SH"; rc frate; cat "$W/out.txt"; tf`
9. `python3 -c 'import json,sys; r=json.load(open(sys.argv[1]))["ratings"]["api-1"]; print(sorted(r), r["more_distinct"])' "$W/ft/trial.json"`

**Expected Result:**
- Steps 1 to 6 each print `exit 2 stdout-bytes 0`, with this first reason on stderr and a summary `divergence-trial: refused — trial file unchanged — <reason>`:
  - Step 1: `blank_field api-1 more_distinct` (a partial rating is never stored)
  - Step 2: `out_of_range api-1 distinct_X='4' (allowed: 1|2|3)`
  - Step 3: `note_too_long api-1 (201 chars, max 200)`
  - Step 4: `note_multiline api-1 (the note must be one line)`
  - Step 5: `body_changed (the sheet differs from the blinded one outside the rating lines; restore it and re-fill)`
  - Step 6: `empty_rater (--rated-by names the human who rated)`
- Step 7: `trial unchanged`; `rated_by=None ratings=None blind=set`.
- Step 8: `exit 0`; `pass`, six `brief: <id> rated` lines, `divergence-trial: rated 6 briefs by UAT Tester`; `rated_by=UAT Tester ratings=set blind=set`.
- Step 9: `['distinct_X', 'distinct_Y', 'more_distinct', 'note', 'render_only_enough'] X` (or `Y`): ratings are stored by set label, never by arm name.

**Implementation Reference:** Story 4 — Files: `scripts/divergence-trial.py` (`rate`); WWB decision 4

**Status:** [ ] Pass  [ ] Fail

**Notes:**

---

### Scenario 26: `report` says `keep` only when declared axes win at least 4 of 6 briefs and the distinct total; a tie is not a win

**Source:** Acceptance Criteria (AC-4.5) — Story 4; Business Rule 11 (Trial verdict); Shadow Path "Trial report" (happy path)
**Feature:** none
**Verification:** human — no recipe

**Preconditions:**
- Setup block pasted.
- `ftrial` prints the `blinded` line.

**Steps:**
1. `fill 4 3 1; frate | tail -1; rc frep; cat "$W/out.txt"`
2. `fill 3 3 1; frate | tail -1; frep | sed -n '1p;$p'`
3. `fill 6 2 2; frate | tail -1; frep | sed -n '1p;$p'`
4. `fill 4 3 1; frate >/dev/null; frep --json | python3 -c 'import json,sys; d=json.load(sys.stdin); print(d["verdict"], d["axes_wins"], d["distinct"], d["render_only"]["yes"])'`

**Expected Result:**
- Step 1: `divergence-trial: rated 6 briefs by UAT Tester`; `exit 0 …`; then:
  - `keep`
  - `brief: api-1 medium=api winner=axes distinct axes=3 naive=1 render_only=yes`
  - `brief: api-2 medium=api winner=axes distinct axes=3 naive=1 render_only=no`
  - `brief: data-model-1 medium=data-model winner=axes distinct axes=3 naive=1 render_only=yes`
  - `brief: data-model-2 medium=data-model winner=axes distinct axes=3 naive=1 render_only=no`
  - `brief: ui-1 medium=ui winner=tie distinct axes=3 naive=1 render_only=yes`
  - `brief: ui-2 medium=ui winner=tie distinct axes=3 naive=1 render_only=no`
  - `render-only: yes on 3 of 6 briefs (ui 1 of 2)`
  - `sample: 6 briefs, one rater; declared axes must win 4 of 6 — a small sample, not a general result`
  - `blinding: honor-system; the rater opened only the sheet`
  - `divergence-trial: keep — axes won 4 of 6, distinct 18 vs 6`
- Step 2: `remove`, `divergence-trial: remove — axes won 3 of 6, distinct 18 vs 6` (three ties do not count).
- Step 3: `remove`, `divergence-trial: remove — axes won 6 of 6, distinct 12 vs 12` (wins alone are not enough; the total must be higher).
- Step 4: `keep 4 {'axes': 18, 'naive': 6} 3`.

**Implementation Reference:** Story 4 — Files: `scripts/divergence-trial.py` (`report`)

**Status:** [ ] Pass  [ ] Fail

**Notes:**

---

### Scenario 27: `report` says `unverifiable` with a reason for no ratings, a missing or changed key, or a short brief set, and refuses a missing trial file

**Source:** Shadow Path "Trial report" (nil input, empty input, upstream error) — Story 4; Error Map `report` (key missing or hash mismatch; ratings absent); DEV-006
**Feature:** none
**Verification:** human — no recipe

**Preconditions:**
- Setup block pasted.

**Steps:**
1. `ftrial; rc frep; cat "$W/out.txt"`
2. `fill 4 3 1; frate | tail -1; mv "$W/ft/key.json" "$W/ft/key.bak"; rc frep; cat "$W/out.txt"`
3. `cp "$W/ft/key.bak" "$W/ft/key.json" && printf ' ' >> "$W/ft/key.json"; frep | sed -n '1,2p;$p'`
4. `cp "$W/ft/key.bak" "$W/ft/key.json"; frep | sed -n '1p;$p'`
5. `python3 -c 'import json,sys; d=json.load(open(sys.argv[1])); d["briefs"]=[b for b in d["briefs"] if b["id"]!="ui-2"]; json.dump(d, open(sys.argv[2],"w"))' "$W/ft/trial.json" "$W/ft/trial5.json"; dt report --trial "$W/ft/trial5.json" | sed -n '1,2p;$p'`
6. `rc dt report --trial "$W/no-such-trial.json"`

**Expected Result:**
- Step 1: `exit 0 …`; `unverifiable`, `reason: unrated`, six `brief:` lines ending `winner=- distinct axes=- naive=- render_only=-`, `render-only: yes on 0 of 6 briefs (ui 0 of 2)`, the `sample:` and `blinding:` lines, and `divergence-trial: unverifiable — unrated` (empty input).
- Step 2: `divergence-trial: rated 6 briefs by UAT Tester`; `exit 0 …`; `unverifiable`, `reason: key_missing`, six `brief:` lines with `winner=- distinct axes=- naive=-` and `render_only` alternating `yes`, `no`, `render-only: yes on 3 of 6 briefs (ui 1 of 2)`, the two caveat lines, and `divergence-trial: unverifiable — key_missing` (upstream error).
- Step 3: `unverifiable`, `reason: key_changed`, `divergence-trial: unverifiable — key_changed`.
- Step 4: `keep`, `divergence-trial: keep — axes won 4 of 6, distinct 18 vs 6`.
- Step 5: `unverifiable`, `reason: brief_count 5 (need 6, 2 per medium: ui=1 api=2 data-model=2)`, `divergence-trial: unverifiable — brief_count` (DEV-006).
- Step 6: `exit 2 stdout-bytes 0`; on stderr `reason: trial_unreadable …/no-such-trial.json (FileNotFoundError)` and `divergence-trial: refused — trial_unreadable …` (nil input).

**Implementation Reference:** Story 4 — Files: `scripts/divergence-trial.py` (`report`, `load_key`, `score`)

**Status:** [ ] Pass  [ ] Fail

**Notes:**

---

### Scenario 28: The harness's 75 unit tests pass on Python 3.9, it uses only the standard library, and it never ships

**Source:** Acceptance Criteria (AC-4.1 to AC-4.5, task 4.7 verification) — Story 4; technical-spec.md → Trial Harness (Dev-only); DEV-007
**Feature:** none
**Verification:** human — no recipe

**Preconditions:**
- Setup block pasted; `reset` prints nothing.

**Steps:**
1. `pt scripts/tests/test_divergence_trial.py -q 2>&1 | tail -1`
2. `grep -nE '^(import|from) ' "$CL/scripts/divergence-trial.py"`
3. `grep -n 'divergence-trial' "$CL/scripts/gen-platform-trees.py" "$CL/scripts/install.sh" "$CL/scripts/update.sh" "$CL/scripts/unlink.sh" | cut -c1-100`
4. `ls "$CL/plugins/writ/scripts/divergence-trial.py" 2>&1; ls "$CL/plugins/writ/scripts" | grep -c 'pipeline-baseline\|divergence-trial'`

**Expected Result:**
- Step 1: `75 passed`. The tests cover every refusal and verdict branch, seed determinism, blinding leaks, and DEV-007 (a `Title:` line inside `Structure:` is draft content).
- Step 2: `from __future__ import annotations`, `argparse`, `hashlib`, `json`, `os`, `random`, `re`, `sys`, `from pathlib import Path`, `from typing import …`. Standard library only.
- Step 3: four lines: `"divergence-trial.py",` in `DEV_ONLY_SCRIPTS` in `gen-platform-trees.py`, and the dev-only `case` line in `install.sh`, `update.sh`, and `unlink.sh`, each listing it beside `pipeline-baseline.py`.
- Step 4: no such file; `0`.

**Implementation Reference:** Story 4 — Files: `scripts/divergence-trial.py`, `scripts/tests/test_divergence_trial.py`, `scripts/gen-platform-trees.py` (`DEV_ONLY_SCRIPTS`), `scripts/install.sh`, `scripts/update.sh`, `scripts/unlink.sh`; WWB coverage 97%

**Status:** [ ] Pass  [ ] Fail

**Notes:**

---

## Story 5: Trial Inputs, Generation, Blinding, and Rating Handoff

### Scenario 29: Six short briefs on Writ's own surfaces, three prompt files, and a trial file initialized from the briefs

**Source:** Acceptance Criteria (AC-5.1) — Story 5; DEV-011
**Feature:** none
**Verification:** human — no recipe

**Preconditions:**
- Setup block pasted. Safe before the rating: it opens only `briefs/`, lists names, and runs tests.

**Steps:**
1. `wc -l "$CL/$TD"/briefs/*.md`
2. `for f in "$CL/$TD"/briefs/*.md; do echo "$(sed -n 1p "$f") | $(sed -n 2p "$f") | $(sed -n 4p "$f" | cut -c1-70)"; done`
3. `ls "$CL/$TD" "$CL/$TD/prompts"`
4. `pt scripts/tests/test_divergence_trial_outcome.py -q -k "six_briefs or share_one_output_template or trial_file_matches" 2>&1 | tail -1`

**Expected Result:**
- Step 1: `api-1.md` 9 lines, the other five 8 lines; all at most 10.
- Step 2: six lines, each `id: <brief> | medium: <medium> | <first line>`: `api-1` the command-line contract of `pr-ready.py`; `api-2` the evidence record `/why` returns; `data-model-1` a verification ledger of verified pull request heads; `data-model-2` the rule-to-enforcer table `/retro` keeps; `ui-1` a page showing how far one Writ spec has progressed; `ui-2` a viewer for one `/prototype` exploration record. All are Writ's own surfaces; none quotes another repository's source.
- Step 3: `2026-10-26-divergence-trial.json`, `briefs`, `key.json`, `prompts`, `rating-sheet.md`, `raw`, `render`; then `axes.md`, `naive.md`, `render.md`.
- Step 4: `3 passed` (with a deselected count): the briefs are headed and short, both prompts share one output template, and the trial file's brief hashes match the briefs.

**Implementation Reference:** Story 5 — Files: `.writ/eval/divergence-trial/briefs/*.md`, `prompts/{naive,axes,render}.md`, `2026-10-26-divergence-trial.json`

**Status:** [ ] Pass  [ ] Fail

**Notes:**

---

### Scenario 30: The rating sheet is blind and blank, and every UI draft has a self-contained render

**Source:** Acceptance Criteria (AC-5.3) — Story 5; Business Rule 10 (Trial integrity)
**Feature:** none
**Verification:** human — no recipe

**Preconditions:**
- Setup block pasted. Safe before the rating: it reads the sheet and the renders the rater may open, and only lists `key.json`.

**Steps:**
1. `S="$CL/$TD/rating-sheet.md"; for p in '^## Brief ' '^### Set [XY]$' '^#### Draft [123]$' '^### Rating: ' '^Commitment:' '^Title:' '^(distinct_X|distinct_Y|more_distinct|render_only_enough|note):$'; do echo "$(grep -cE "$p" "$S") $p"; done`
2. `ls "$CL/$TD/render/ui-1" "$CL/$TD/render/ui-2"; ls "$CL/$TD/key.json"`
3. `grep -liE '<(script|link)[^>]*(src|href)[[:space:]]*=' "$CL/$TD"/render/*/*.html; grep -li '<html' "$CL/$TD"/render/*/*.html | wc -l | tr -d ' '`
4. `pt scripts/tests/test_divergence_trial_outcome.py -q -k "rating_sheet_is_blind or self_contained_render" 2>&1 | tail -1`
5. `open "$CL/$TD/render/ui-1/X-1.html"` (macOS; any browser)

**Expected Result:**
- Step 1: `6`, `12`, `36`, `6`, `0`, `0`, `30`: six briefs, Set X and Set Y each, drafts titled only `Draft 1` to `Draft 3`, no `Commitment:` or `Title:` line at column 0, and all thirty rating fields blank.
- Step 2: `X-1.html` to `X-3.html` and `Y-1.html` to `Y-3.html` in each folder; `key.json` exists (do not open it before the rating).
- Step 3: the first grep prints nothing (no external script or stylesheet); `12`.
- Step 4: `2 passed`.
- Step 5: a static page renders with no network access.

**Implementation Reference:** Story 5 — Files: `.writ/eval/divergence-trial/rating-sheet.md`, `key.json`, `render/ui-{1,2}/{X,Y}-{1,2,3}.html`

**Status:** [ ] Pass  [ ] Fail

**Notes:**

---

### Scenario 31: The handoff names the rater, the one file to open, the fields, and the exact commands; `report` says unrated and the spec awaits the rating

**Source:** Acceptance Criteria (AC-5.4) — Story 5; Business Rule 12 (Human-gated verdict); Hardest Constraint; DEV-010
**Feature:** none
**Verification:** human — no recipe

**Preconditions:**
- Setup block pasted. Safe before the rating: `report` uses no mapping until ratings exist, and `tf` prints one field. The clone is pinned at `df3b461`, so its trial stays unrated after Scenario 35.

**Steps:**
1. `grep -n '^## \|^> ' "$CL/$SPEC/rating-handoff.md"`
2. `sed -n '/^## Who rates/,/^## What to fill/p' "$CL/$SPEC/rating-handoff.md"`
3. `grep -n 'divergence-trial.py rate\|divergence-trial.py report' "$CL/$SPEC/rating-handoff.md" | cut -c1-150`
4. `sed -n '/^## State at handoff/,$p' "$CL/$SPEC/rating-handoff.md"`
5. `(cd "$CL" && python3 scripts/divergence-trial.py report --trial "$TRIAL"; echo "exit $?")`
6. `tf "$CL/$TRIAL"; sed -n 3p "$CL/$SPEC/spec.md"`
7. `pt scripts/tests/test_divergence_trial_outcome.py -q -k rating_handoff 2>&1 | tail -1`

**Expected Result:**
- Step 1: `> Status: waiting for the human rater. The lane did not rate.`; sections `## Who rates`, `## What to open`, `## What to fill`, `## Commands`, `## State at handoff`.
- Step 2: Adam Sellke, the spec owner, rates once; no agent fills the sheet or runs `rate`. Open one file, `rating-sheet.md`; the briefs and the UI renders may also be opened. Do not open `raw/`, `key.json`, or the trial JSON before `rate`. Blinding is honor-system.
- Step 3: the `rate` command with `--trial .writ/eval/divergence-trial/2026-10-26-divergence-trial.json --sheet .writ/eval/divergence-trial/rating-sheet.md --rated-by "Adam Sellke"`, and the `report` command on the same trial file.
- Step 4: all twelve arms recorded at one model and tier in one session; this is the second generation, and the first was discarded before anyone rated (DEV-010); ui-1 axes draft 1 was regenerated once after `record` refused it; no draft was hand-edited; content tells from the arm design may remain, so rate structure, not style; `report` prints unverifiable / unrated; `rated_by` is null; the lane did not rate or act on a verdict.
- Step 5: `unverifiable`, `reason: unrated`, six `brief:` lines ending `winner=- distinct axes=- naive=- render_only=-`, `render-only: yes on 0 of 6 briefs (ui 0 of 2)`, the `sample:` and `blinding:` lines, `divergence-trial: unverifiable — unrated`, `exit 0`.
- Step 6: `rated_by=None ratings=None blind=set`; `> **Status:** In Progress — awaiting blind rating (rating-handoff.md)`.
- Step 7: `1 passed`.

**Implementation Reference:** Story 5 — Files: `.writ/specs/2026-10-25-design-divergence/rating-handoff.md`, `spec.md` (header)

**Status:** [ ] Pass  [ ] Fail

**Notes:**

---

### Scenario 32: The outcome test skips until a report exists, and a committed report the repo does not match fails it

**Source:** Acceptance Criteria (AC-5.5) — Story 5; technical-spec.md → Verdict Execution; Error Map "Story 6" (report `unverifiable`); DEV-011
**Feature:** none
**Verification:** human — no recipe

**Preconditions:**
- Setup block pasted; `reset` prints nothing.

**Steps:**
1. `pt scripts/tests/test_divergence_trial_outcome.py -q -rs 2>&1 | tail -3`
2. `grep -nE '^(import|from) ' "$CL/scripts/tests/test_divergence_trial_outcome.py"`
3. `R="$CL/$SPEC/trial-report.md"; for v in 'keep' 'remove' 'unverifiable\nreason: unrated'; do printf "$v\n" > "$R"; echo "== $(head -1 "$R")"; pt scripts/tests/test_divergence_trial_outcome.py -q -vv -k committed_verdict 2>&1 | grep -oE "need 'Complete'|rated_by empty|skill_present [^'\"]*|need 'Closed — Not Implemented'|status_reason|[0-9]+ (failed|passed)" | sort -u; done; reset`

**Expected Result:**
- Step 1: a `SKIPPED [1]` line whose reason reads `trial-report.md is absent: the blind rating has not happened yet, so there is no verdict to check (Story 6 writes the report)`, then `68 passed, 1 skipped`.
- Step 2: `from __future__ import annotations`, `hashlib`, `json`, `os`, `re`, `subprocess`, `sys`, `pathlib`, `typing`, and `pytest`. It never imports the harness, so it keeps guarding the record after Story 6 deletes `scripts/divergence-trial.py`.
- Step 3, `== keep`: `1 failed`, `need 'Complete'`, `rated_by empty` (the status still awaits the rating and no person rated).
- Step 3, `== remove`: `1 failed`, `need 'Closed — Not Implemented'`, `skill_present skills/design-divergence`.
- Step 3, `== unverifiable`: `1 failed`, `status_reason` (the spec status names none of the report's reasons).
- `reset` prints nothing.

**Implementation Reference:** Story 5 — Files: `scripts/tests/test_divergence_trial_outcome.py` (`verdict_problems`, `keep_problems`, `remove_problems`, `unverifiable_problems`); WWB decision 4

**Status:** [ ] Pass  [ ] Fail

**Notes:**

---

### Scenario 33: Both arms are recorded for every brief, the axes arm follows declared axes, and the prompts share one template

**Source:** Acceptance Criteria (AC-5.2; AC-5.1 prompt content) — Story 5; Business Rule 10 (Trial integrity); DEV-010
**Feature:** none
**Verification:** human — no recipe

**Preconditions:**
- **After rating.** Scenario 35 is done. This scenario opens `raw/`, `prompts/`, and `key.json` in the clone.
- Setup block pasted.

**Steps:**
1. `ls "$CL/$TD"/raw/*/`
2. `for b in api-1 api-2 data-model-1 data-model-2 ui-1 ui-2; do printf '%s axes %s/%s naive %s/%s\n' $b "$(grep -c '^Commitment:' "$CL/$TD/raw/$b/axes.md")" "$(grep -c '^## Draft' "$CL/$TD/raw/$b/axes.md")" "$(grep -c '^Commitment:' "$CL/$TD/raw/$b/naive.md")" "$(grep -c '^## Draft' "$CL/$TD/raw/$b/naive.md")"; done`
3. `grep -c '^## Caller usage$\|^## Persona$\|^## Declared axes\|^## Combinations$' "$CL/$TD"/raw/*/axes-plan.md; sed -n '/^## Declared axes/,$p' "$CL/$TD/raw/api-1/axes-plan.md"`
4. `` diff <(awk '/^```text$/{f=1;next} /^```$/{f=0} f' "$CL/$TD/prompts/naive.md") <(awk '/^```text$/{f=1;next} /^```$/{f=0} f' "$CL/$TD/prompts/axes.md") && echo "one shared template" ``
5. `grep -c 'Give me three options' "$CL/$TD/prompts/naive.md"; grep -c 'Treat these lines as private input\|Do not mention the persona, the axis combination' "$CL/$TD/prompts/axes.md"; grep -c 'show the changed lines' "$CL/$TD/prompts/axes.md"`
6. `pt scripts/tests/test_divergence_trial_outcome.py -q -k recorded_arms 2>&1 | tail -1`
7. `python3 -c 'import json,sys; k=json.load(open(sys.argv[1]))["briefs"]; print(len(k), all(sorted(v[x]["arm"] for x in "XY") == ["axes", "naive"] and all(sorted(v[x]["drafts"]) == [1, 2, 3] for x in "XY") for v in k.values()))' "$CL/$TD/key.json"`

**Expected Result:**
- Step 1: each of the six brief folders holds `axes-plan.md`, `axes.md`, and `naive.md`.
- Step 2: every line reads `axes 3/3 naive 0/3`: three axes drafts with one `Commitment:` each, three naive drafts with none.
- Step 3: `:4` for each of the six plans (caller usage, persona, declared axes from the skill, one combination per draft, written before any spawn); the api-1 plan declares "One call vs several" and "Errors as exceptions vs result values" from the skill's API catalog and gives three combinations.
- Step 4: `one shared template` (Structure 15 to 25 lines; each draft stands alone).
- Step 5: `1`; `2`; `0` (DEV-010: the axes prompt keeps the caller lines and its own inputs out of the drafts).
- Step 6: `1 passed` (each recorded hash matches its raw file).
- Step 7: `6 True`.
- Not checkable from files: that both arms ran at one tier in one session. Story 5's What Was Built (decision 1) records 18 axes spawns and 6 naive spawns, same model and tier.

**Implementation Reference:** Story 5 — Files: `.writ/eval/divergence-trial/raw/<brief>/{axes,naive,axes-plan}.md`, `prompts/`, `key.json`

**Status:** [ ] Pass  [ ] Fail

**Notes:**

---

## Human Handoff: Blind Rating and Story 6 Follow-Through

Story 5 stops at `rating-handoff.md`. The verdict that decides whether the skill stays rests on one person's blind rating (Hardest Constraint; Business Rule 12). Scenario 34 checks that an agent cannot get past that gate. Scenario 35 is the rating itself. Scenario 36 hands the rated trial to Story 6.

### Scenario 34: Before any rating, `/implement-story` on Story 6 stops at task 6.1 and changes nothing

**Source:** Business Rule 12 (Human-gated verdict) — Spec; Story 6 task 6.1 and Notes; `user-stories/README.md` (Story 6 "stops at its task 6.1 until the rater has filled `rating-sheet.md` and run `rate`")
**Feature:** none
**Verification:** human — no recipe

**Preconditions:**
- Setup block pasted; `reset` prints nothing; `tf "$CL/$TRIAL"` prints `rated_by=None ratings=None blind=set`. The clone is pinned at `df3b461`, so this holds even after Scenario 35.
- `live` running in a new session.

**Steps:**
1. `/implement-story .writ/specs/2026-10-25-design-divergence/user-stories/story-6-act-on-blind-verdict.md`
2. Let it run until it stops or asks you something. If it asks how to proceed, reply `Stop here.` If it starts editing `commands/` or `skills/` or deleting scripts, press Escape: that is a Fail.
3. In the first shell: `tf "$CL/$TRIAL"; git -C "$CL" status --short; ls "$CL/$SPEC/trial-report.md" 2>&1; sed -n 3p "$CL/$SPEC/user-stories/story-6-act-on-blind-verdict.md"; git -C "$CL" rev-parse --short HEAD`
4. `reset`

**Expected Result:**
- Step 2: the session reports that Story 6 is waiting on the human rater (the sheet is not filled and `rated_by` is null) and stops at task 6.1. It does not fill `rating-sheet.md`, does not run `rate`, and does not act on any `report` it runs.
- Step 3: `rated_by=None ratings=None blind=set`; `git status` shows no change to `rating-sheet.md`, the trial JSON, `skills/`, `commands/`, or `scripts/`; no `trial-report.md`; the story status is not `Completed ✅` and not marked skipped; HEAD is still `df3b461`.
- Step 4: prints nothing.

**Status:** [ ] Pass  [ ] Fail

**Notes:**

---

### Scenario 35: The blind rating — the rater fills the sheet, runs `rate`, and reads the verdict

**Source:** Business Rule 12 (Human-gated verdict) and Hardest Constraint — Spec; `rating-handoff.md` (What to open, What to fill, Commands); Story 6 task 6.1 precondition
**Feature:** none
**Verification:** human — no recipe

**Preconditions:**
- You are the rater the handoff names, Adam Sellke. No agent runs this scenario or any step of it.
- You have not opened `raw/`, `key.json`, `2026-10-26-divergence-trial.json`, or `prompts/` under `.writ/eval/divergence-trial/`, and have not run Scenario 33.
- The primary checkout is on `phase/15-code-level-rigor`, and `git -C "$REPO" status --short -- .writ/eval .writ/specs/2026-10-25-design-divergence` prints nothing.
- `(cd "$REPO" && python3 scripts/divergence-trial.py report --trial .writ/eval/divergence-trial/2026-10-26-divergence-trial.json | head -2)` prints `unverifiable` and `reason: unrated`.

**Steps:**
1. Read `.writ/specs/2026-10-25-design-divergence/rating-handoff.md` § What to fill in the primary checkout.
2. Open `.writ/eval/divergence-trial/rating-sheet.md` in an editor. You may also open the briefs and the UI renders (for example `open "$REPO/.writ/eval/divergence-trial/render/ui-1/X-1.html"`). Count structure (where state lives, how many calls, which table owns identity), not naming or style.
3. For each of the six briefs, fill the five lines under `### Rating: <brief>`: `distinct_X`, `distinct_Y`, `more_distinct`, `render_only_enough`, `note`. Change nothing else. Save.
4. `git -C "$REPO" diff --stat; git -C "$REPO" diff -U0 -- .writ/eval/divergence-trial/rating-sheet.md | grep -E '^[-+][^-+]' | grep -cvE '^[-+](distinct_X|distinct_Y|more_distinct|render_only_enough|note):'`
5. `(cd "$REPO" && python3 scripts/divergence-trial.py rate --trial .writ/eval/divergence-trial/2026-10-26-divergence-trial.json --sheet .writ/eval/divergence-trial/rating-sheet.md --rated-by "Adam Sellke")`
6. `(cd "$REPO" && python3 scripts/divergence-trial.py report --trial .writ/eval/divergence-trial/2026-10-26-divergence-trial.json)`
7. `git -C "$REPO" status --short`

**Expected Result:**
- Step 4: `1 file changed, 30 insertions(+), 30 deletions(-)`; `0` (every changed line is a rating line).
- Step 5: `pass`, `brief: api-1 rated` through `brief: ui-2 rated`, `divergence-trial: rated 6 briefs by Adam Sellke`. A refusal prints `reason:` lines on stderr, exits 2, and leaves the trial file unchanged: `blank_field`, `out_of_range`, `note_too_long`, or `note_multiline` names the line to fix; `body_changed` means a draft line changed, so restore with `git checkout .writ/eval/divergence-trial/rating-sheet.md` and fill again. Fix it and repeat Step 5; a refusal is not a Fail. A rating stored despite a blank or out-of-range field is.
- Step 6: line 1 `keep` or `remove`, with no `reason:` line; six `brief:` lines, api-1 through ui-2, each with `winner=axes`, `naive`, or `tie`, `distinct axes=N naive=M`, and `render_only=yes|no` agreeing with what you entered (the report has now mapped Set X and Set Y to arms); `render-only: yes on N of 6 briefs (ui M of 2)`; the `sample:` caveat line; `blinding: honor-system; the rater opened only the sheet`; last, `divergence-trial: <verdict> — axes won W of 6, distinct A vs B`. The verdict follows the rule: `keep` only if W is at least 4 and A is greater than B; tie rows count for neither arm. `unverifiable` here is a Fail.
- Step 7: exactly two modified files, `.writ/eval/divergence-trial/rating-sheet.md` and `.writ/eval/divergence-trial/2026-10-26-divergence-trial.json`. Do not commit them: Story 6 commits them with the report (Scenario 36).
- After this scenario, Scenarios 33 and 36 may run.

**Status:** [ ] Pass  [ ] Fail

**Notes:**

---

### Scenario 36: Story 6 commits the report verbatim with the rated trial file before it keeps or removes anything

**Source:** `rating-handoff.md` § Commands (Story 5 → Story 6); Story 6 AC-6.1 (pending story); spec.md → Recommendations (delete the harness after the report commit)
**Feature:** none
**Verification:** human — no recipe

**Preconditions:**
- **After rating.** Scenario 35 passed, and `git -C "$REPO" status --short` shows only the two rated files.
- No other session is editing the primary checkout. This is the real Story 6 run: it commits to `phase/15-code-level-rigor` and keeps or removes the feature.
- In the first shell: `B=$(git -C "$REPO" rev-parse --short HEAD); (cd "$REPO" && python3 scripts/divergence-trial.py report --trial .writ/eval/divergence-trial/2026-10-26-divergence-trial.json) > "$W/report-before.txt"; head -1 "$W/report-before.txt"` prints `keep` or `remove`.

**Steps:**
1. Open a new Claude Code session in the primary checkout and run `/implement-story .writ/specs/2026-10-25-design-divergence/user-stories/story-6-act-on-blind-verdict.md`. Let it finish.
2. In the first shell: `git -C "$REPO" log --reverse --format='%h %s' "$B"..HEAD`
3. `F=$(git -C "$REPO" rev-list --reverse "$B"..HEAD | head -1); git -C "$REPO" show --stat --format='%h %s' "$F"`
4. `diff "$W/report-before.txt" <(git -C "$REPO" show "$F":.writ/specs/2026-10-25-design-divergence/trial-report.md) && echo verbatim; tf "$REPO/$TRIAL"`
5. `ls "$REPO/scripts/divergence-trial.py" 2>&1; (cd "$REPO" && uv run pytest scripts/tests/test_divergence_trial_outcome.py -q -rs 2>&1 | tail -1); sed -n 3p "$REPO/.writ/specs/2026-10-25-design-divergence/spec.md"`

**Expected Result:**
- Step 1: the story passes task 6.1 (a person rated the sheet), runs `report`, and acts on its verdict without asking you to rate anything.
- Step 2: two or more commits after `$B`; the first is the report commit.
- Step 3: the first commit adds `.writ/specs/2026-10-25-design-divergence/trial-report.md` and carries the rated trial file (and the filled sheet); it changes nothing under `commands/`, `skills/`, `scripts/`, `plugins/`, `README.md`, or `.writ/manifest.yaml`.
- Step 4: `verbatim`; `rated_by=Adam Sellke ratings=set blind=set`.
- Step 5: no such file for the harness (deleted after the report commit); the outcome test's summary has no `failed` and no `skipped` (the committed verdict and the repo agree); the status line reads `> **Status:** Complete` on `keep` or `> **Status:** Closed — Not Implemented` on `remove`.
- Then regenerate this plan (`/create-uat-plan 2026-10-25-design-divergence`) to add scenarios for Story 6's AC-6.2 to AC-6.5.

**Status:** [ ] Pass  [ ] Fail

**Notes:**

---

## Pending Stories

The following stories are not yet complete. Scenarios will be added when they complete:

- **Story 6:** Act on the Blind Verdict (Human-Gated) — Status: Not Started. It waits on the blind rating (Scenario 35); Scenario 36 runs it. Its acceptance criteria (AC-6.1 to AC-6.5: report committed first, the `keep` or `remove` repo state, `unverifiable` acted on by nothing, harness deleted) get scenarios when it completes.
