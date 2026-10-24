# UAT Plan: Front Door

> **Generated:** 2026-10-22
> **Spec:** `.writ/specs/2026-10-22-front-door/`
> **Stories Covered:** 3 of 3 completed
> **Total Scenarios:** 16
> **Verification recipe:** does not apply. Writ is markdown plus Python and bash scripts with no application to boot, so no `.writ/docs/app-verification.md` was drafted, saved, or bound (Step 1.3 asked nothing). Every scenario is `human — no recipe`.

## How to Use This Plan

1. Work through scenarios in order (they're grouped by story, ordered by priority)
2. For each scenario, follow the steps exactly as written
3. Mark Pass or Fail — add notes for any unexpected behavior
4. Scenarios marked Fail should be filed as issues or fed back to the spec
5. A feature passes UAT when all scenarios pass (or failures are accepted as known limitations)

**Conventions for this plan:**

- There is no app to boot and no recipe. Scenarios 1 to 10 are live: the maintainer runs `/writ` in a Claude Code session opened in a scratch clone and judges the restatement, the route, and the todo list by eye, because the phase's success criteria for the front door are human judgments. Scenario 11 is a headless run. Scenarios 12 and 13 read the registration surfaces; 14 and 16 run the repository's own checks; 15 is the negative case.
- **Never run `install.sh` or `update.sh` in the Writ repo, and never open the live session there.** `.claude/` and `.cursor/` in the repo are symlinks into the source; the clone keeps the symlinks, so `/writ` is a project command inside `$CL` with nothing installed.
- Every helper refuses to run unless the shell is inside `$W`. `$REPO` is cloned from and never written to. Run the plan in `bash` on macOS (`sed -i ''`), outside any sandbox.
- Paste this setup block once per shell. Stop if the first line does not print `W=/...`.

  ```bash
  W=$(mktemp -d "${TMPDIR:-/tmp}/writ-uat-front-door.XXXXXX") && cd "$W" && W=$PWD && echo "W=$W"
  REPO=/Users/asellke/Projects/writ            # read only: cloned from, never edited, never installed into
  CL="$W/clone"; git clone -q "$REPO" "$CL"    # committed tree on the current branch; .claude/commands -> ../commands survives the clone
  inW() { case "$PWD/" in "$W"/*) ;; *) echo "refusing: $PWD is outside $W" >&2; return 1;; esac; }
  # live: open Claude Code inside the clone for Scenarios 1 to 10; never in $REPO
  live() { inW && (cd "$CL" && claude); }
  # pt <pytest args>: the front-door test file on Python 3.9 inside the clone
  pt() { inW && (cd "$CL" && uv run --python 3.9 pytest scripts/tests/test_front_door.py "$@"); }
  # reset: undo every edit to tracked files in the clone and drop untracked ones; prints nothing when clean
  reset() { inW && git -C "$CL" checkout -q -- . && git -C "$CL" clean -qfd && git -C "$CL" status --short; }
  ```

- **Live scenarios (1 to 10).** Run `live` from a second shell that has the setup block. Each scenario starts a fresh turn with its own `/writ "<request>"` line. On Claude Code the confirmation renders as the native question widget or as a numbered list (the adapter's `AskQuestion()` row). At the confirmation press Escape (widget) or reply `Not what I meant` (list) unless the scenario says to confirm; nothing runs either way. The restatement is Writ's wording: judge shape and substance, not exact words. The condensed restatements below come from Story 3's recorded fixture run. None of the eight fixture requests names evidence, so every `Proof:` line should read `(not stated — see prompting-guide.md § What a request carries)`. The option set has at most four options (DEV-007, 2026-10-24): the proposed route first with `(Recommended)`, the two other table routes closest to the request, `Not what I meant` last, and the prompt names the routes left out. Before DEV-007 the contract named every other route, and the widget capped the list at four.
- Expected output was observed on 2026-10-22 against `101d078` (branch `phase/14-front-door-and-distribution`). Story 1 landed in `00f8261`, Story 2 in `06b78eb`, Story 3 in `8bd79dc`. After each scenario that edits the clone, run `reset` and confirm it prints nothing. When done: `rm -rf "$W"`.
- Drift log: DEV-001 to DEV-006 are Small and auto-amended. Four change what the reader sees and are named where they appear: DEV-003 (`status.md`'s Maintainer Note bare list also leads with `writ`; Scenario 13), DEV-004 (the README install follow-up lines name `/writ "my feature"`; Scenario 12), DEV-006 (Step 2's tie-break counts an escalation signal only when the request states it or the restatement can name it, which keeps request 7 on `/prototype --no-diverge`; Scenario 7), DEV-001 (the Overview names `/writ:writ`; read in Scenario 14). DEV-002 (`/writ @file` restatement heuristic) and DEV-005 (test anchors) change nothing a tester sees. The spec's Experience Design journey lists five condensed todo names; the shipped command carries the routed file's heading text, so Scenario 9 expects six `/prototype` items.

## Coverage Summary

| Story | Status | Scenarios | Source Breakdown |
|-------|--------|-----------|-----------------|
| Story 1: The `/writ` Command File | ✅ Covered | 11 | AC: 9, Errors: 0, Shadow: 1, Edge: 0, Experience: 1 |
| Story 2: Registration and Catalogs | ✅ Covered | 2 | AC: 2, Errors: 0, Shadow: 0 (Upstream error folded into Scenario 13), Edge: 0 |
| Story 3: Structure Rows, Issue Resolution, and Routing Fixture | ✅ Covered | 3 | AC: 2, Errors: 0, Shadow: 1, Edge: 0 |

The technical spec's Error & Rescue Map is "Not required" (no data flow), so there are no error scenarios. Scenarios 1 to 8 are the live counterpart of Story 3's recorded fixture run (AC-3.3), one per fixture request, grouped under Story 1 because they exercise the command. No pending stories: all three are Completed ✅.

---

## Story 1: The `/writ` Command File

### Scenario 1: Fixture 1, a Safari paste bug, is restated and routed to `/prototype --no-diverge`

**Source:** Acceptance Criteria (AC-1.2, AC-1.3, AC-1.4) — Story 1; Routing Fixture row 1 (AC-3.3) — Story 3; State Catalog "Request lacks a done check or proof"; Business Rules 3 and 4
**Feature:** none
**Verification:** human — no recipe

**Preconditions:** setup block pasted; `live` running in `$CL`.

**Steps:**
1. `/writ "users can't paste into the search box on Safari"`
2. Read the restatement and the confirmation, then press Escape or reply `Not what I meant`.
3. In the shell: `git -C "$CL" status --short`

**Expected Result:**
- Step 2: four labeled lines, `Goal:`, `Problem:`, `Done check:`, `Proof:`, in Writ's words: goal, pasting into the search box works on Safari; problem, the box drops pasted text on Safari (the implied problem, not an echo of the request); done check, a paste on Safari fills the box; `Proof:` not stated, with the guide link. The missing proof is named, not asked about.
- Step 2: `Proposed: /prototype --no-diverge` with a one-line reason (a bug with one obvious shape, no escalation signal named); `/prototype --no-diverge (Recommended)` is the first option, `Not what I meant` the last; exactly one question.
- Step 3: prints nothing. No todo list appeared and no routed command ran.

**Status:** [x] Pass  [ ] Fail — **Notes:** maintainer run 2026-10-23 (live session in a clone of 73b31ed).

---
### Scenario 2: Fixture 2, an API-keys settings page, routes to `/create-spec` by the tie-break

**Source:** Acceptance Criteria (AC-1.3, AC-1.4) — Story 1; Routing Fixture row 2 (AC-3.3) — Story 3; Business Rule 2 (tie-break)
**Feature:** none
**Verification:** human — no recipe

**Preconditions:** setup block pasted; `live` running in `$CL`.

**Steps:**
1. `/writ "a settings page where people can manage API keys"`
2. Read the restatement and the confirmation, then press Escape or reply `Not what I meant`.

**Expected Result:**
- Restatement: goal, users create, view, and revoke API keys from a settings page; problem, no place to manage keys today; `Done check:` and `Proof:` both `(not stated — see prompting-guide.md § What a request carries)`; routing proceeds with no question about either.
- `Proposed: /create-spec`, reason: a capability users rely on, and the tie-break lands there too (key storage is a schema change; key handling is security-sensitive). `/create-spec (Recommended)` first; `Not what I meant` last.

**Status:** [x] Pass  [ ] Fail — **Notes:** maintainer run 2026-10-23 (live session in a clone of 73b31ed).

---
### Scenario 3: Fixture 3, an unsettled onboarding idea, routes to `/prototype`; "Not what I meant" restates again

**Source:** Acceptance Criteria (AC-1.3, AC-1.4) — Story 1; Routing Fixture row 3 (AC-3.3) — Story 3; State Catalog "User picks Not what I meant"
**Feature:** none
**Verification:** human — no recipe

**Preconditions:** setup block pasted; `live` running in `$CL`.

**Steps:**
1. `/writ "something to make onboarding feel less empty"`
2. Read the restatement and the confirmation; pick `Not what I meant`.
3. Answer the follow-up with: `the first screen after sign-up should suggest three things to try`. Read the second restatement; press Escape at its confirmation.

**Expected Result:**
- Step 2: goal, a new user's first screens feel populated; problem, onboarding shows empty states with nothing to do; done check and proof not stated. `Proposed: /prototype` (names a goal rather than a change; "something" leaves the direction unsettled); the `(Recommended)` option reads `/prototype`, with no `--no-diverge`.
- Step 3: one free-text question, no menu; then a fresh restatement built from the answer (goal: the post-sign-up screen suggests three actions) and one new confirmation. Nothing ran in between.

**Status:** [x] Pass  [ ] Fail — **Notes:** maintainer run 2026-10-23 (live session in a clone of 73b31ed).

---
### Scenario 4: Fixture 4, "do Phase 15", routes to `/implement-phase 15` and shows the matched phase

**Source:** Acceptance Criteria (AC-1.3, AC-1.4) — Story 1; Routing Fixture row 4 (AC-3.3) — Story 3; State Catalog "Request names a roadmap phase or feature"
**Feature:** none
**Verification:** human — no recipe

**Preconditions:** setup block pasted; `live` running in `$CL`; `grep -n '^## Phase 15' "$CL/.writ/product/roadmap.md"` prints `704:## Phase 15: Code-Level Rigor (2 weeks) — 📋 Committed (2026-10-20)`.

**Steps:**
1. `/writ "do Phase 15"`
2. Read the restatement and the confirmation, then press Escape or reply `Not what I meant`.

**Expected Result:**
- Restatement: goal, Phase 15 (Code-Level Rigor) implemented to its exit criteria; problem, the phase is committed and its specs unbuilt; done check, the phase's success criteria hold (carried by the roadmap); proof not stated.
- `Proposed: /implement-phase 15` with the matched phase named in the confirmation (`Phase 15: Code-Level Rigor`); `/implement-phase 15 (Recommended)` first.

**Status:** [x] Pass  [ ] Fail — **Notes:** maintainer run 2026-10-23 (live session in a clone of 73b31ed).

---
### Scenario 5: Fixture 5, a why question, routes to `/research` and notes `/why`

**Source:** Acceptance Criteria (AC-1.3, AC-1.4) — Story 1; Routing Fixture row 5 (AC-3.3) — Story 3; State Catalog "Request is a why or how question"
**Feature:** none
**Verification:** human — no recipe

**Preconditions:** setup block pasted; `live` running in `$CL`.

**Steps:**
1. `/writ "why does the importer skip rows with empty emails?"`
2. Read the restatement and the confirmation, then press Escape or reply `Not what I meant`.

**Expected Result:**
- Restatement: goal, an evidenced explanation of the skip; problem, unknown whether the skip is intended or a defect; done check, the reason is stated with the code path that produces it; proof not stated.
- `Proposed: /research`, and the confirmation says `/why` takes this route when it ships. `/research (Recommended)` first.

**Status:** [x] Pass  [ ] Fail — **Notes:** maintainer run 2026-10-23 (live session in a clone of 73b31ed).

---
### Scenario 6: Fixture 6, a Postgres-or-Meilisearch fork, routes to `/prototype` with the fork named, never a question

**Source:** Acceptance Criteria (AC-1.3, AC-1.4) — Story 1; Routing Fixture row 6 (AC-3.3) — Story 3; State Catalog "Request is a fork"; Technical Concern (empirical-fork test)
**Feature:** none
**Verification:** human — no recipe

**Preconditions:** setup block pasted; `live` running in `$CL`.

**Steps:**
1. `/writ "should we use Postgres full-text search or Meilisearch for this?"`
2. Read the restatement and the confirmation, then press Escape or reply `Not what I meant`.

**Expected Result:**
- Restatement: goal, one search backend chosen on evidence; problem, two candidates and no measured basis (relevance, latency, operating cost); done check and proof not stated.
- `Proposed: /prototype` with the fork named as the thing to try (index the project's data both ways and compare), and the reason says a throwaway run answers it faster than asking. `/writ` does not answer the fork with a question of its own and does not ask which backend the user prefers.

**Status:** [x] Pass  [ ] Fail — **Notes:** maintainer run 2026-10-23 (live session in a clone of 73b31ed).

---
### Scenario 7: Fixture 7, a rename "everywhere", stays on `/prototype --no-diverge` (DEV-006)

**Source:** Acceptance Criteria (AC-1.3, AC-1.4) — Story 1; Routing Fixture row 7 (AC-3.3, AC-3.4) — Story 3; Business Rule 2 (tie-break); drift log DEV-006
**Feature:** none
**Verification:** human — no recipe

**Preconditions:** setup block pasted; `live` running in `$CL`.

**Steps:**
1. `` /writ "rename `getUser` to `fetchUser` everywhere" ``
2. Read the restatement and the confirmation, then press Escape or reply `Not what I meant`.

**Expected Result:**
- Restatement: goal, every `getUser` reference reads `fetchUser` and nothing else changes; problem, the name does not say what the function does; done check, no `getUser` reference remains and the suite passes; proof not stated.
- `Proposed: /prototype --no-diverge`: a mechanical rename with one obvious shape. "Everywhere" is not treated as an over-5-files signal (DEV-006, `commands/writ.md` Step 2 Tie-break, last sentence: an unstated file count does not count; `/prototype` counts files when it runs and escalates itself), so the route is not `/create-spec`.

**Status:** [x] Pass  [ ] Fail — **Notes:** maintainer run 2026-10-23 (live session in a clone of 73b31ed).

---
### Scenario 8: Fixture 8, multi-tenant billing, routes to `/create-spec` on escalation signals

**Source:** Acceptance Criteria (AC-1.3, AC-1.4) — Story 1; Routing Fixture row 8 (AC-3.3) — Story 3; `## Routing Rules` row 3
**Feature:** none
**Verification:** human — no recipe

**Preconditions:** setup block pasted; `live` running in `$CL`.

**Steps:**
1. `/writ "add multi-tenant billing with per-seat pricing"`
2. Read the restatement and the confirmation, then press Escape or reply `Not what I meant`.

**Expected Result:**
- Restatement: goal, each tenant is billed per seat; problem, no tenant-scoped billing exists; done check and proof not stated.
- `Proposed: /create-spec`, with the reason naming at least one escalation signal (schema change, new payment dependency, core architecture). `/create-spec (Recommended)` first.

**Status:** [x] Pass  [ ] Fail — **Notes:** maintainer run 2026-10-23 (live session in a clone of 73b31ed).

---
### Scenario 9: Confirming the route puts `/prototype`'s six steps on the todo list with Step 2.5 marked `skip:`

**Source:** Acceptance Criteria (AC-1.5) — Story 1; Experience Design journey steps 4 and 5; State Catalog "Routed command has phases", "Route skips a phase"; Business Rules 5, 6, 7
**Feature:** none
**Verification:** human — no recipe

**Preconditions:** setup block pasted; `live` running in `$CL`; in the shell, `inW && printf 'hello wrold\n' > "$CL/scratch-note.txt"`.

**Steps:**
1. `/writ "fix the typo in scratch-note.txt"`
2. Pick `/prototype --no-diverge (Recommended)`.
3. Watch the todo list as the routed command starts; once its first step is under way, press Escape to stop the run (or let it finish).
4. In the shell: `git -C "$CL" status --short; ls "$CL/.writ/state/tracking.json" 2>&1`

**Expected Result:**
- Step 2: no second question; the restatement is unchanged by the pick.
- Step 3: six items on Claude Code's native todo list, in this order and carrying the heading text, before `/prototype` Step 1 runs: `Step 1: Extract Intent`, `Step 2: Context Scan`, `Step 2.5: Diverge & Choose — skip: --no-diverge …` (the reason names the flag), `Step 3: Spawn Coding Agent`, `Step 4: Lint & Typecheck`, `Step 5: Output Summary`. Only Step 2.5 carries `skip:`. The list is not printed as a markdown checklist in the reply (the Claude Code adapter maps `todo_write` to `TodoWrite`; Scenario 13).
- Step 4: `?? scratch-note.txt` only (content `hello world` if the run finished), then `No such file or directory`. Nothing under `.writ/` was created. Then `reset`.

**Implementation Reference:** Story 1 — `commands/writ.md` Steps 4 and 5; `commands/prototype.md` `### Step` headings; Story 2 — `adapters/claude-code.md` § Quick Reference, `todo_write` row.

**Status:** [x] Pass  [ ] Fail — **Notes:** maintainer run 2026-10-23 (live session in a clone of 73b31ed).

---
### Scenario 10: No request, no goal, no roadmap, and a missing routed file each get the contracted response

**Source:** Shadow Paths (Nil input, Empty input, Upstream error) — Story 1; State Catalog "Request lacks a goal", "`/writ` with no request and no context", "`roadmap.md` absent"; Required Artifacts
**Feature:** none
**Verification:** human — no recipe

**Preconditions:** setup block pasted; `live` running in `$CL`; `/clear` first so the session has no context; `reset` prints nothing.

**Steps:**
1. `/writ` with nothing after it.
2. `/writ "make it better"`; do not answer the question.
3. In the shell: `inW && mv "$CL/.writ/product/roadmap.md" "$W/roadmap.bak"`. In the session: `/writ "do Phase 15"`; press Escape at any confirmation. Then `mv "$W/roadmap.bak" "$CL/.writ/product/roadmap.md"`.
4. In the shell: `inW && printf 'hello wrold\n' > "$CL/scratch-note.txt" && rm "$CL/commands/prototype.md"` (the file `.claude/commands/prototype.md` points to). In the session: `/writ "fix the typo in scratch-note.txt"`; pick `/prototype --no-diverge (Recommended)`. Then `cat "$CL/scratch-note.txt"; reset`.

**Expected Result:**
- Step 1: one natural-language question, "What do you want to do?" (or words to that effect); no restatement, no route, no menu.
- Step 2: the `Goal:` line reads `(not stated — see prompting-guide.md § What a request carries)` and one natural-language question follows; no route options are shown before the answer.
- Step 3: the restatement says the roadmap is missing and that `/plan-product` creates it; `/implement-phase` is neither the proposed route nor an option.
- Step 4: the reply names `commands/prototype.md` as missing and names `/update-writ`; no prototype steps appear on the todo list and no improvised fix happens: `cat` still prints `hello wrold`. `reset` prints nothing.

**Status:** [x] Pass  [ ] Fail — **Notes:** maintainer run 2026-10-23 (live session in a clone of 73b31ed): steps 1 and 2 pass; steps 3 (missing roadmap) and 4 (missing routed file) not run. Observation for Scenarios 1 to 10: Claude Code's question widget holds four options, so a confirmation cannot list every route; the observed confirmation named the routes it could not show and pointed to Other, as this plan's conventions anticipate.

---
### Scenario 11: Headless `claude -p` restates and proposes the route without running anything

**Source:** Experience Design — Interaction Patterns ("One restatement, one question, then the routed command owns the conversation"); Business Rules 4 and 7; `adapters/claude-code.md` `AskQuestion()` row (formatted text, no interactive UI)
**Feature:** none
**Verification:** human — no recipe

**Preconditions:** setup block pasted; `claude` on `PATH` (`claude --version` printed `2.1.309 (Claude Code)` on 2026-10-22); `reset` prints nothing. One API round trip.

**Steps:**
1. `REQ="users can't paste into the search box on Safari"; (cd "$CL" && claude -p "/writ \"$REQ\"" --disallowedTools Write Edit Bash) > "$W/headless.txt" 2>&1; echo "exit $?"`
2. `grep -n -E '(Goal|Problem|Done check|Proof):|Proposed:|\(Recommended\)|Not what I meant|Extract Intent' "$W/headless.txt"`
3. `git -C "$CL" status --short`

**Expected Result:**
- Step 1: `exit 0`.
- Step 2: the four labeled lines, with `Proof:` carrying the guide link; a `Proposed: /prototype --no-diverge` line; `(Recommended)` on the first option and `Not what I meant` on the last, rendered as a numbered list because `-p` has no widget. No `Extract Intent` line: the run stops at the confirmation, which nobody can answer headless. Fail if `/prototype` steps ran without a confirmation.
- Step 3: prints nothing.

**Status:** [x] Pass  [ ] Fail — **Notes:** run 2026-10-23 at 73b31ed in a logged-in shell, Claude Code 2.1.310: `exit 0`; Goal, Problem, Done check, and Proof lines present, Proof carrying the guide link; `Proposed: \`/prototype --no-diverge\``; numbered list with `(Recommended)` first and `Not what I meant` last; no `Extract Intent` line; clone clean. Two observations: the reply added "this repo has no search box" (true for the Writ clone), and it listed four routes, omitting `/implement-phase` with "isn't listed because the roadmap has no phase or feature about this". The conventions say the option set is the same every time, so watch for the same omission in Scenarios 1 to 10.

---
## Story 2: Registration and Catalogs

### Scenario 12: README Quick Start opens with `/writ`; the five-command table sits under "What `/writ` routes to"

**Source:** Acceptance Criteria (AC-2.3, AC-2.4) — Story 2; Business Rule 10; drift log DEV-004
**Feature:** none
**Verification:** human — no recipe

**Preconditions:** setup block pasted.

**Steps:**
1. `awk '/^## Quick Start/{p=1} p' "$CL/README.md" | sed -n '1,12p'`
2. `` grep -n -E '^### Start here|^New here|^### What `/writ` routes to|picks the route|/writ "my feature"|32 commands' "$CL/README.md" ``
3. `sed -n '/^### Start here/,/^$/p' "$CL/README.md" | sed -n '2,4p' | cut -c1-60`

**Expected Result:**
- Step 1: `## Quick Start`, blank, `` Type `/writ` followed by what you want: ``, blank, a fence, `/writ "users can't paste into the search box on Safari"`, `→ Goal, Problem, Done check restated; route: /prototype --no-diverge (Recommended); one confirmation; then it runs.`, the closing fence, blank, the pointer line, blank, `` ### What `/writ` routes to ``. `/writ` appears before any table.
- Step 2: `106:### Start here` (under `## Commands`, above `### Planning & Specification`); `227:New here? …` ending `` then type `/writ` followed by what you want. ``; `` 229:### What `/writ` routes to ``; `241:` the closing sentence ending `` ; `/writ` picks the route for you. ``; lines 257, 287, and 307 naming `/writ "my feature"` for Cursor, Claude Code, and Codex (DEV-004). No `32 commands` line: the count sentence was dropped.
- Step 3: `| Command | Purpose |`, the separator, then `` | `/writ` | **The front door.** Restates a request as a goal ``.

**Status:** [x] Pass  [ ] Fail — **Notes:** agent run 2026-10-23 at 0b033a3: plan drift: the three DEV-004 `/writ "my feature"` lines sit at 268, 313, 333 (plan: 257, 287, 307) because plugin-distribution Story 5 (`0e4085e`) added install sections. Everything else exact: Quick Start opens with the `/writ` fence before any table, `106:### Start here` under `## Commands` above Planning (111), 227 New here, 229 What `/writ` routes to, 241 picks the route, no `32 commands` line, Step 3 rows as expected.

---
### Scenario 13: Every catalog and surface registers `/writ`, both generator checks pass, and a hand edit to `SKILL.md` fails them

**Source:** Acceptance Criteria (AC-2.1, AC-2.2, AC-2.3, AC-2.5) — Story 2; Business Rules 8, 9, 11; Shadow Path "Upstream error: stale generated file"; spec-lite edge cases (sort position, `(16)`); State Catalog "Platform maps `todo_write` to a file"; drift log DEV-003
**Feature:** none
**Verification:** human — no recipe

**Preconditions:** setup block pasted; `reset` prints nothing.

**Steps:**
1. `` grep -n -E '^### Start here|^### Planning & Specification|^\| `/writ` \|' "$CL/SKILL.md" "$CL/codex/AGENTS.md.template" "$CL/claude-code/CLAUDE.md"; grep -n '^Start with' "$CL/claude-code/CLAUDE.md" ``
2. `(cd "$CL" && bash scripts/gen-skill.sh --check 2>/dev/null | tail -1; python3 scripts/gen-claude-md.py --check | tail -1)`
3. `sed -n '8,10p' "$CL/.writ/manifest.yaml"; awk '/^commands:/{p=1} p && /^  - name: /{print NR": "$0}' "$CL/.writ/manifest.yaml" | sed -n '31,33p'; sed -n '187,190p' "$CL/.writ/manifest.yaml"`
4. `` grep -n -E 'commands:. entry|── (verify-spec|writ|writ-design)\.md ' "$CL/adapters/cursor.md"; grep -n -o -E '^`/writ`, `/create-spec`|^`writ`, `create-spec`' "$CL/commands/status.md"; grep -n -o -E '`security-audit`, `writ`, `writ-design` \([0-9]+\)' "$CL/.writ/docs/model-tiers.md"; grep -n '^| `todo_write`' "$CL/adapters/claude-code.md" ``
5. `` sed -i '' 's/^| `\/writ` | `commands\/writ.md` |/& STALE/' "$CL/SKILL.md"; (cd "$CL" && bash scripts/gen-skill.sh --check 2>/dev/null > "$W/check.txt"; echo "exit $?"; head -2 "$W/check.txt"); pt -q 2>&1 | grep -E 'AssertionError|passed|failed'; reset ``

**Expected Result:**
- Step 1: `SKILL.md:44:### Start here`, `SKILL.md:48:| `/writ` | `commands/writ.md` | Restate a request, …`, `SKILL.md:50:### Planning & Specification` (the entry category renders first); `codex/AGENTS.md.template:11:### Start here`, `:15:| `/writ` | `.codex/commands/writ.md` | …` (purpose truncated with `…` like its neighbours), `:17:### Planning & Specification`; `claude-code/CLAUDE.md:48:| `/writ` | `.claude/commands/writ.md` | …`; and `13:Start with `/writ "<what you want>"`: it restates the request and routes it to the right command.`, above the Commands table (line 15).
- Step 2: `gen-skill: pass (SKILL.md matches .writ/manifest.yaml)` and `gen-claude-md: pass (33 commands, 8 agents)`.
- Step 3: `categories:`, `  - id: entry`, `    label: "Start here"`; `181:   - name: verify-spec`, `186:   - name: writ`, `191:   - name: writ-design` (sorted); then `file: commands/writ.md`, `category: entry`, the purpose line, `tags: [entry, routing]`.
- Step 4: line 33 ends `(33)`; lines 64 to 66 are `verify-spec.md`, `│   │   ├── writ.md                # /writ`, `writ-design.md`, `#` comments aligned; `249:`/writ`, `/create-spec`` and `442:`writ`, `create-spec`` (both allowlists lead with it, DEV-003); `75:`security-audit`, `writ`, `writ-design` (16)`; `` 194:| `todo_write` | `TodoWrite` | Native todo list; phases mirror here | `` (the old `Write(".writ/state/tracking.json")` mapping is gone, which is why Scenario 9 sees a native list and no file).
- Step 5: `exit 1`, `fail`, `reason: SKILL.md drifts from .writ/manifest.yaml; run bash scripts/gen-skill.sh`; then `AssertionError: scripts/gen-skill.sh --check exit 1:` from `test_catalogs` and `1 failed, 10 passed`. `reset` prints nothing.

**Implementation Reference:** Story 2 — `scripts/gen-skill.sh`, `scripts/gen-claude-md.py` TEMPLATE, `.writ/manifest.yaml`, `adapters/cursor.md` § Directory Structure, `commands/status.md` allowlists, `.writ/docs/model-tiers.md` `high` row, `adapters/claude-code.md` § Quick Reference.

**Status:** [x] Pass  [ ] Fail — **Notes:** agent run 2026-10-23 at 0b033a3: plan drift: `codex/AGENTS.md.template` has Start here at 10, the `/writ` row at 14 with its full purpose (no `…` truncation), and Planning at 16 (plan: 11/15/17, truncated), because plugin-distribution Story 3 (`bf407c5`) regenerated it; the `todo_write` row in `adapters/claude-code.md` is at 217 (plan: 194), text exact, no `tracking.json` mapping left. The rest is exact: SKILL.md 44/48/50, CLAUDE.md 48 and 13 (table at 15), both `--check` pass (33 commands, 8 agents), manifest 181/186/191 and the writ entry, cursor.md `(33)` and 64 to 66, status.md 249/442, model-tiers 75 `(16)`. Step 5 printed `exit 1`, `fail`, the drift reason, the AssertionError from `test_catalogs`, and `1 failed, 10 passed`. `reset` was clean.

---
## Story 3: Structure Rows, Issue Resolution, and Routing Fixture

### Scenario 14: The structure checker pins `## Routing Rules` and `entry_level`, the issue is resolved, and the eleven pinned tests pass

**Source:** Acceptance Criteria (AC-3.1, AC-3.2, AC-3.5) — Story 3; the test halves of AC-1.1 to AC-1.5 and AC-2.1 to AC-2.5; Must Include 6 and 7; drift log DEV-001
**Feature:** none
**Verification:** human — no recipe

**Preconditions:** setup block pasted; `uv` installed; `reset` prints nothing.

**Steps:**
1. `(cd "$CL" && python3 scripts/eval-command-structure.py --root . > "$W/structure.txt"; echo "exit $?"; grep -E 'kind-|writ.md' "$W/structure.txt"; grep -c '^PASS' "$W/structure.txt")`
2. `I="$CL/.writ/issues/features/2026-10-13-in-your-own-words.md"; grep -n -E '^## |spec_ref' "$I"; sed -n '/^## Resolution/,$p' "$I" | grep -o -E '2026-10-22-front-door|/writ|Restate|does not end the turn|2026-10-22' | sort -u`
3. `grep -n -E '^entry_level|^## Routing Rules|/writ:writ' "$CL/commands/writ.md"; wc -l < "$CL/commands/writ.md"`
4. `pt -v 2>&1 | grep -E 'PASSED|FAILED|passed|failed'`

**Expected Result:**
- Step 1: `exit 0`; `PASS` for `command-structure-kind-heading`, `-frontmatter`, `-invocation`, then `PASS	command-structure:commands/writ.md:heading:Routing Rules` and `PASS	command-structure:commands/writ.md:frontmatter:entry_level`; the count is `35` (3 self-tests plus 32 rows), no `FAIL`.
- Step 2: `7:> **spec_ref:** .writ/specs/2026-10-22-front-door/`; six H2s ending with `37:## Resolution` as the last; then five lines, `/writ`, `2026-10-22`, `2026-10-22-front-door`, `Restate`, `does not end the turn`: the Resolution names the spec, `/writ` Step 1 Restate as the absorbed restatement, that it does not end the turn because it routes, and the date.
- Step 3: `6:entry_level: high`; `20:` the Overview line ending `` Under a Claude Code plugin the command reads `/writ:writ`. `` (DEV-001); `107:## Routing Rules`; `135` (under the 200-line budget).
- Step 4: eleven `PASSED` lines in this order: `test_command_file`, `test_guide_cited`, `test_routing_rules`, `test_confirmation_step`, `test_mirroring_step`, `test_manifest`, `test_catalogs`, `test_readme`, `test_surfaces`, `test_issue_resolution`, `test_structure_rows`; then `11 passed`. No `FAILED` line.

**Implementation Reference:** Story 3 — `scripts/eval-command-structure.py` `ROWS` (two `commands/writ.md` rows after `Artifact Integrity`); the issue's `## Resolution`; `scripts/tests/test_front_door.py` (490 lines).

**Status:** [x] Pass  [ ] Fail — **Notes:** agent run 2026-10-23 at 0b033a3: Step 1 `exit 0`, 35 PASS and 0 FAIL, including both `commands/writ.md` rows. Step 2: `spec_ref` at 7, six H2s with `## Resolution` last at 37, all five tokens present. Step 3: `6:entry_level: high`, line 20 ends `/writ:writ`, `107:## Routing Rules`, 135 lines. Step 4: eleven PASSED in the listed order, `11 passed`.

---
### Scenario 15: Removing a rule row fails `test_routing_rules`; renaming the heading fails the structure row too

**Source:** Shadow Path "Empty input: rule table with five rows → `test_routing_rules` fails" (spec-lite, Testing); Acceptance Criteria (AC-3.1, AC-3.4) — Story 3; Business Rule 1
**Feature:** none
**Verification:** human — no recipe

**Preconditions:** setup block pasted; `reset` prints nothing.

**Steps:**
1. `sed -i '' '/^| A fork that a throwaway run could answer faster than a question |/d' "$CL/commands/writ.md"; pt -q 2>&1 | grep -E 'AssertionError|^FAILED|passed|failed'; reset`
2. `sed -i '' 's/^## Routing Rules$/## Routing rules/' "$CL/commands/writ.md"; (cd "$CL" && python3 scripts/eval-command-structure.py --root . > "$W/structure.txt"; echo "exit $?"; grep '^FAIL' "$W/structure.txt"); pt -q 2>&1 | grep -E '^FAILED|passed|failed'; reset`

**Expected Result:**
- Step 1: `AssertionError: 5 data rows, expected 6`, `FAILED scripts/tests/test_front_door.py::test_routing_rules`, `1 failed, 10 passed`. The table is the only classifier, and the test counts its rows.
- Step 2: `exit 1` and one `FAIL	command-structure:commands/writ.md:heading:Routing Rules	writ.md must keep the Routing Rules heading … (no heading outside fenced code starts with 'Routing Rules'; …)` line; then `FAILED …::test_routing_rules` (heading not found) and `FAILED …::test_structure_rows`, `2 failed, 9 passed`.
- `reset` prints nothing after each step.

**Status:** [x] Pass  [ ] Fail — **Notes:** agent run 2026-10-23 at 0b033a3: Step 1: `AssertionError: 5 data rows, expected 6`, `FAILED ...::test_routing_rules`, `1 failed, 10 passed`. Step 2: `exit 1`, one `FAIL command-structure:commands/writ.md:heading:Routing Rules` line with the expected text, then `FAILED` for `test_routing_rules` (heading not found) and `test_structure_rows`, `2 failed, 9 passed`. `reset` was clean after each step.

---
### Scenario 16: The repository quality gate reports zero findings

**Source:** Acceptance Criteria (AC-3.5) — Story 3; Success Criteria "`bash scripts/eval.sh` reports 0 findings"; Hardest Constraint (the command stays thin)
**Feature:** none
**Verification:** human — no recipe

**Preconditions:** setup block pasted; `reset` prints nothing. Run outside any sandbox (the gate does `git init` in a temp dir). About two minutes.

**Steps:**
1. `(cd "$CL" && bash scripts/eval.sh; echo "exit $?")`
2. `tail -2 "$(ls -t "$CL"/.writ/state/eval-*.md | head -1)"`

**Expected Result:**
- Step 1: progress lines, then `Eval report: .writ/state/eval-<timestamp>.md`, then `exit 0`. No `check_manifest`, `check_command_structure`, `check_referenced_paths`, or leanness `structural` finding names `commands/writ.md`.
- Step 2: `- Findings: 0` and `- Run errors: 0`. Non-blocking leanness WARNINGs about surface lines past their ceilings pre-date this spec on the phase branch and are not findings.

**Status:** [x] Pass  [ ] Fail — **Notes:** agent run 2026-10-23 at 0b033a3: eval.sh ran inside the agent's sandbox (`git init` was not blocked), printed progress lines, `Eval report: .writ/state/eval-20261023-230006.md`, and `exit 0`. The report tail reads `- Findings: 0` and `- Run errors: 0`, and no line names `commands/writ.md`. The only WARNINGs are the non-blocking leanness ceiling and byte-budget ones.

---
