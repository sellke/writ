# UAT Plan: Why Command

> **Generated:** 2026-10-25
> **Spec:** `.writ/specs/2026-10-25-why-command/`
> **Stories Covered:** 4 of 4 completed
> **Total Scenarios:** 36
> **Verification recipe:** none. No `.writ/docs/app-verification.md` exists, and Writ has no app to launch: its checks (pytest, the bash tests, `scripts/eval.sh`) read markdown, not a running process. With no launch command detected, Step 1.3's recommended answer is skip, so no recipe was drafted, saved, or bound. Every scenario is `human — no recipe`.

## How to Use This Plan

1. Work through scenarios in order (they're grouped by story, ordered by priority)
2. For each scenario, follow the steps exactly as written
3. Mark Pass or Fail — add notes for any unexpected behavior
4. Scenarios marked Fail should be filed as issues or fed back to the spec
5. A feature passes UAT when all scenarios pass (or failures are accepted as known limitations)

**Conventions for this plan:**

- Two kinds of scenario. **Live** scenarios (5 to 20, 29, 33 to 36) run `/why`, `/writ`, or `/create-spec` in a Claude Code session and judge the answer by eye, because tier assignment is a judgment the spec asks a person to confirm. **Read and check** scenarios (1 to 4, 21 to 28, 30 to 32) read the shipped files and run the repository's own tests in a scratch clone.
- **Never run `install.sh` or `update.sh` in the Writ repo, and never open a live session there.** `.claude/` and `.cursor/` in the repo are symlinks into the source. The clone keeps the symlinks, so `/why` is a project command inside `$CL` with nothing installed.
- Every helper refuses to run unless the shell is inside `$W`. `$REPO` is cloned from and never written to. Run the plan in `bash` on macOS (`sed -i ''`), outside any sandbox. Claude Code asks whether to trust each new scratch folder the first time a session opens there; accept it.
- Paste this setup block once per shell. Stop if the first line does not print `W=/...`.

  ```bash
  W=$(mktemp -d "${TMPDIR:-/tmp}/writ-uat-why.XXXXXX") && cd "$W" && W=$PWD && echo "W=$W"
  REPO=/Users/asellke/Projects/writ            # read only: cloned from, never edited, never installed into
  CL="$W/clone"; git clone -q "$REPO" "$CL"    # committed tree on the current branch
  git -C "$CL" fetch -q "$REPO" refs/notes/writ:refs/notes/writ   # a plain clone leaves the audit notes behind
  NG="$W/nogit"; mkdir -p "$NG" && git -C "$CL" archive HEAD | tar -x -C "$NG"   # the same tree with no .git
  printf '{"mcpServers":{}}\n' > "$W/no-mcp.json"
  inW() { case "$PWD/" in "$W"/*) ;; *) echo "refusing: $PWD is outside $W" >&2; return 1;; esac; }
  # live [dir]: Claude Code with your usual MCP servers, in $CL unless a dir is given
  live() { inW && (cd "${1:-$CL}" && claude); }
  # livebare [dir]: Claude Code with no MCP server connected
  livebare() { inW && (cd "${1:-$CL}" && claude --strict-mcp-config --mcp-config "$W/no-mcp.json"); }
  # liveplan: Claude Code in Plan Mode inside $CL
  liveplan() { inW && (cd "$CL" && claude --permission-mode plan); }
  # pt <pytest args>: pytest on Python 3.9 inside the clone
  pt() { inW && (cd "$CL" && uv run --python 3.9 pytest "$@"); }
  # reset: undo every edit in the clone and drop untracked files; prints nothing when clean
  reset() { inW && git -C "$CL" checkout -q -- . && git -C "$CL" clean -qfd && git -C "$CL" status --short; }
  # mk <dir>: an empty repo with /why available as a project command
  mk() { mkdir -p "$1/.claude/commands" && cp "$CL/commands/why.md" "$CL/commands/_preamble.md" "$1/.claude/commands/" \
    && git -C "$1" init -q && cm "$1" 2026-01-01 "chore: add tooling"; }
  # cm <dir> <date> <message>: commit everything at a fixed date
  cm() { (cd "$1" && git add -A && GIT_AUTHOR_DATE="$2T10:00:00" GIT_COMMITTER_DATE="$2T10:00:00" git commit -qm "$3"); }

  # $NL: a project with git history and no .writ/ ledger
  NL="$W/noledger"; mk "$NL"
  printf 'MAX_RETRIES = 3\n' > "$NL/retry.py";     cm "$NL" 2026-01-05 "Cap retries at 3: the payments API rate-limits a client after its fourth call in a minute"
  printf 'TIMEOUT_SECONDS = 30\n' > "$NL/timeout.py"; cm "$NL" 2026-01-06 "Raise request timeout to 30s (#42)"
  printf 'MAX_ROWS = 5000\n' > "$NL/limits.py";     cm "$NL" 2026-01-07 "add limits module"
  printf 'EVICTION = "fifo"\n' > "$NL/cache.py";    cm "$NL" 2026-01-08 "add cache module"
  printf 'EVICTION = "lru"\n' > "$NL/cache.py";     cm "$NL" 2026-01-09 "Switch cache eviction to LRU"
  (cd "$NL" && GIT_AUTHOR_DATE=2026-01-10T10:00:00 GIT_COMMITTER_DATE=2026-01-10T10:00:00 git revert --no-edit HEAD >/dev/null)

  # $SL: a project with a small .writ/ ledger and no .writ/research/
  SL="$W/ledger"; mk "$SL"; mkdir -p "$SL/.writ/knowledge/conventions" "$SL/.writ/decision-records"
  printf 'LOG_FORMAT = "jsonl"\n' > "$SL/logging_setup.py"
  printf '# Log format\n\nLogs are written as JSON lines because the log shipper parses one JSON object per line.\nEvidence: `.writ/research/2026-01-04-log-shipping-research.md`.\n' > "$SL/.writ/knowledge/conventions/log-format.md"
  cm "$SL" 2026-01-05 "add JSON-lines logging"
  printf 'CACHE_TTL_SECONDS = 60\n' > "$SL/pricing_cache.py"
  printf '# ADR-001: Pricing cache TTL\n\n> **Status:** Accepted\n> **Date:** 2026-01-10\n\n## Decision\n\nThe pricing cache TTL is 60 seconds because the pricing feed refreshes every minute.\n' > "$SL/.writ/decision-records/adr-001-cache-ttl.md"
  cm "$SL" 2026-01-10 "add pricing cache (ADR-001)"
  printf 'CACHE_TTL_SECONDS = 60\nLEGACY_ONLY = True\n' > "$SL/pricing_cache.py"
  cm "$SL" 2026-03-02 "pricing cache: keep the 60s TTL only for legacy clients; the feed now refreshes hourly"
  echo "setup done: $(git -C "$NL" rev-list --count HEAD) commits in noledger, $(git -C "$SL" rev-list --count HEAD) in ledger"
  ```

  The last line should read `setup done: 7 commits in noledger, 4 in ledger`. The research document the `$SL` knowledge entry cites does not exist, on purpose (Scenario 12).
- **Live scenarios.** Run the helper from a second shell that has the setup block. Start a new session for each scenario (`/exit`, then the helper again), because `/why` reads the conversation for context. Tiers, sources, and the Sources searched order are what to judge; the answer's wording is Writ's own. Unless a scenario says a change follows, `/why` writes nothing: each live scenario ends by checking the working tree.
- Expected results come from the spec, the four What Was Built records, and the tree at `1af50ee` (branch `phase/15-code-level-rigor`). Story 1 landed in `6625f74`, Story 2 in `d47bcec`, Story 3 in `b0f881e`, Story 4 in `f9569cb`. None of these scenarios has been run for this plan. After each scenario that edits the clone, run `reset` and confirm it prints nothing. When done: `rm -rf "$W"`.
- **Drift and later history.** DEV-001 to DEV-003 are Small and auto-amended. DEV-001 (the answer template's ADR placeholder reads `adr-<NNN>-<slug>.md`; Scenario 4) and DEV-002 (`/why` points to `/research` for a subject outside the project; Scenario 9) change what a reader sees. DEV-003 (three more test pins moved with registration) changes nothing a tester sees beyond the tests passing in Scenario 24. One expected difference from Story 1's recorded fixture run: Story 2's commit `d47bcec` added `/why` to both `commands/status.md` allowlists after dogfood question 3 was answered, so that answer now carries a stale-ledger line (Scenario 7).

## Coverage Summary

| Story | Status | Scenarios | Source Breakdown |
|-------|--------|-----------|-----------------|
| Story 1: The `/why` Command File | ✅ Covered | 20 | AC: 7, Errors: 7, Shadow: 3, Edge: 0, Experience: 3 |
| Story 2: Registration and Catalogs | ✅ Covered | 4 | AC: 4, Errors: 0, Shadow: 0, Edge: 0 |
| Story 3: The Front Door Routes Why Questions to `/why` | ✅ Covered | 5 | AC: 4, Errors: 0, Shadow: 0, Edge: 0, Experience: 1 |
| Story 4: `/create-spec` Reads the `/why` Handoff | ✅ Covered | 7 | AC: 5, Errors: 2, Shadow: 0, Edge: 0 |

- The technical spec has no Interaction Edge Cases section, so there are no edge-case scenarios.
- Folded rows: Error Map "Read git notes" is checked in Scenarios 5 to 7 (no note on the anchor commits); Shadow Paths "Happy path" is Scenarios 5 to 7, "Empty input" is Scenario 8, "No ledger" is Scenario 11, "Stale ledger" is Scenario 7, "Change follows" is Scenarios 14 and 33. Experience Design "Moment of Truth" and "Feedback Model" are checked in Scenarios 5, 6, 14, and 33.
- State Catalog "Two sources point to it, none states it" (`Corroborated`) has no live scenario: no local fixture produces it reliably. Scenario 2 checks its definition in the tier table.
- Dogfood acceptance criteria: AC-1.5 is Scenarios 5, 6, and 7; AC-4.4 is Scenarios 33 and 34.
- No pending stories: all four are Completed ✅.

---

## Story 1: The `/why` Command File

### Scenario 1: The command file has the required frontmatter, sections, and budgets

**Source:** Acceptance Criteria (AC-1.1) — Story 1; Business Rules 16 (Budgets) and 17 (Entry level)
**Feature:** none
**Verification:** human — no recipe

**Preconditions:**
- Setup block pasted; `reset` prints nothing.

**Steps:**
1. `sed -n '2,11p' "$CL/commands/why.md"`
2. `grep -n '^## ' "$CL/commands/why.md"`
3. `wc -lc "$CL/commands/why.md"`
4. `pt scripts/tests/test_why_command.py -q -k "command_file or budgets"`

**Expected Result:**
- Step 1: `name: why`, `description:`, `problem:`, `outcome:`, `entry_level: high`, and `exit_criteria:` with exactly three entries.
- Step 2: `## Overview`, `## Invocation`, `## Required Artifacts`, `## Confidence Tiers`, `## Command Process`, `## Integration with Writ`, `## Completion`, `## References`, in that order, with `## Completion` directly before `## References`. Template headings inside code fences (`## Why:`, `## Preserve / Change / Avoid / Risk`) may also print; they sit between `## Command Process` and `## Integration with Writ`.
- Step 3: 173 lines and 11,226 bytes, under the 200-line and 24,960-byte budgets.
- Step 4: `2 passed`.

**Implementation Reference:** Story 1 — Files: `commands/why.md`, `scripts/tests/test_why_command.py`

**Status:** [ ] Pass  [ ] Fail

**Notes:**

---

### Scenario 2: The five confidence tiers appear in order with their rules, and a swapped tier fails the test

**Source:** Acceptance Criteria (AC-1.2) — Story 1; Business Rules 3 (Five tiers), 4 (Code is not evidence), 6 (Conflicts take the lower tier); State Catalog `Corroborated` row (definition only)
**Feature:** none
**Verification:** human — no recipe

**Preconditions:**
- Setup block pasted; `reset` prints nothing.

**Steps:**
1. `sed -n '/^## Confidence Tiers/,/^## Command Process/p' "$CL/commands/why.md"`
2. `pt scripts/tests/test_why_command.py -q -k test_tiers`
3. `sed -i '' 's/^| `Stated` |/| `STATED_TMP` |/; s/^| `Recorded` |/| `Stated` |/; s/^| `STATED_TMP` |/| `Recorded` |/' "$CL/commands/why.md"; pt scripts/tests/test_why_command.py -q -k test_tiers 2>&1 | grep -E 'tier column|failed|passed'; reset`

**Expected Result:**
- Step 1: a table whose first column reads `Recorded`, `Stated`, `Corroborated`, `Inferred`, `Unknown`, top to bottom. `Corroborated` reads "No source states it; two or more independent sources point to it". Below the table, three bullets: code is not evidence of its own intent (a claim resting only on the code is `Unknown`); a claim never takes a tier above its strongest evidence; disagreeing sources are both shown, the newer one named, and the claim takes the lower tier.
- Step 2: `1 passed`.
- Step 3: an assertion line `tier column is ['Stated', 'Recorded', 'Corroborated', 'Inferred', 'Unknown']`, then `1 failed`. `reset` prints nothing.

**Implementation Reference:** Story 1 — Files: `commands/why.md` (§ Confidence Tiers), `scripts/tests/test_why_command.py` (`test_tiers`)

**Status:** [ ] Pass  [ ] Fail

**Notes:**

---

### Scenario 3: Six steps read the ledger, then git, then MCP, and each names its absent-source case

**Source:** Acceptance Criteria (AC-1.3) — Story 1; Business Rules 1 (Ledger first), 2 (The anchor locates), 7 (MCP only when needed), 9 (No subagents)
**Feature:** none
**Verification:** human — no recipe

**Preconditions:**
- Setup block pasted; `reset` prints nothing.

**Steps:**
1. `grep -n '^### Step' "$CL/commands/why.md"`
2. `sed -n '/^### Step 1:/,/^### Step 5:/p' "$CL/commands/why.md"`
3. `pt scripts/tests/test_why_command.py -q -k "source_order or step_headings"`

**Expected Result:**
- Step 1: six headings: `Step 1: Anchor the Question`, `Step 2: Read the Ledger`, `Step 3: Read Git History`, `Step 4: Read MCP Servers When Needed`, `Step 5: Answer`, `Step 6: Hand Off a Change`.
- Step 2: Step 1 asks one natural-language question when the subject is not found, offers no menu, and says the anchor is never cited as a reason. Step 2 reads `refs/notes/writ`, then specs with `drift-log.md` and What Was Built, then `.writ/decision-records/`, then knowledge and issues, and stops once a `Recorded` claim answers; with no `.writ/` it records `Ledger: none in this project`. Step 3 always runs, uses `git log`, and records `Git: not a git repository` when there is none. Step 4 runs only when the strongest claim is below `Stated`, uses only servers already connected, says "Never prompt to connect, install, or authorize a server", and records `MCP: none connected`. No step starts a subagent.
- Step 3: `2 passed`.

**Implementation Reference:** Story 1 — Files: `commands/why.md` (§ Command Process); WWB decision 2 (absent-source literals printed where each absence is detected)

**Status:** [ ] Pass  [ ] Fail

**Notes:**

---

### Scenario 4: The saved record's path and handoff section have the fixed shape

**Source:** Acceptance Criteria (AC-1.4) — Story 1; Business Rules 10 (A change follows), 11 (Fixed handoff shape), 12 (Saved record); DEV-001
**Feature:** none
**Verification:** human — no recipe

**Preconditions:**
- Setup block pasted; `reset` prints nothing.

**Steps:**
1. `sed -n '/^### Step 5:/,/^## Integration with Writ/p' "$CL/commands/why.md"`
2. `pt scripts/tests/test_why_command.py -q -k test_handoff_shape`

**Expected Result:**
- Step 1: the answer template's ADR evidence example reads `adr-<NNN>-<slug>.md` (DEV-001). Step 6 says it runs only when a change follows and otherwise prints one line and writes nothing. The record path is `.writ/research/<YYYY-MM-DD>-why-<slug>.md`, the slug at most six words, an existing path gets `-2`, `-3`, and a record is never overwritten. The record template has the four header lines `Asked`, `Subject`, `Change`, `Question`, then the answer, then `## Preserve / Change / Avoid / Risk` with `### Preserve`, `### Change`, `### Avoid`, `### Risk` in that order. An empty subsection reads `- none found`.
- Step 2: `1 passed`.

**Implementation Reference:** Story 1 — Files: `commands/why.md` (§ Step 5, § Step 6)

**Status:** [ ] Pass  [ ] Fail

**Notes:**

---

### Scenario 5: Dogfood question 1 — why `/writ-design` is not `/design` — answers at Recorded

**Source:** Acceptance Criteria (AC-1.5) — Story 1; Dogfood Fixture row 1; Shadow Path "Happy path"; Error Map "Read git notes"; Experience Design Moment of Truth, Feedback Model, State Catalog "Ledger states the reason" and "No change follows"; Business Rule 8 (Read-only)
**Feature:** none
**Verification:** human — no recipe

**Preconditions:**
- Setup block pasted; `reset` prints nothing.
- In the first shell: `git -C "$CL" for-each-ref | wc -l` and note the number.
- `live` running in a new session.

**Steps:**
1. `/why "Why is the visual design command named /writ-design and not /design?"`
2. Read the answer to the end.
3. In the first shell: `git -C "$CL" status --short; git -C "$CL" for-each-ref | wc -l`

**Expected Result:**
- Step 2: a `## Why:` heading, then an `**Answer:**` line ending in `Recorded`: Claude Code shipped its own `/design`, so a Writ `/design` collided with it, and the maintainer chose to rename with no alias.
- Step 2: the Claims table cites `.writ/specs/2026-10-20-platform-neutral-names/spec.md` (contract or Technical Concerns) or `.writ/issues/bugs/2026-10-19-design-command-name-collision.md`, by path and section, and quotes the decision.
- Step 2: Sources searched has three lines in the order Ledger, Git, MCP. Ledger notes no `refs/notes/writ` note on the anchor commits. Git names `d36a283` (`feat(design)!: rename /design to /writ-design`); if the anchor includes `commands/writ-design.md`, Git also names `4677ef3` (2026-10-23) with a line that the entry may describe an earlier shape, and the tier stays `Recorded`. MCP reads `not read: the ledger answered at Recorded`.
- Step 2: ends with the one line saying that naming a change makes `/why` add the Preserve / Change / Avoid / Risk list. No record is saved.
- Step 3: `status` prints nothing; the ref count equals the number noted.

**Implementation Reference:** Story 1 — WWB Dogfood Fixture, question 1

**Status:** [ ] Pass  [ ] Fail

**Notes:**

---

### Scenario 6: Dogfood question 2 — why friction signals were never built — quotes ADR-030

**Source:** Acceptance Criteria (AC-1.5) — Story 1; Dogfood Fixture row 2; Experience Design Moment of Truth
**Feature:** none
**Verification:** human — no recipe

**Preconditions:**
- Setup block pasted; `reset` prints nothing.
- `live` running in a new session.

**Steps:**
1. `/why "Why were friction signals never built?"`
2. Read the answer to the end.
3. In the first shell: `git -C "$CL" status --short`

**Expected Result:**
- Step 2: the `**Answer:**` line ends in `Recorded`: ADR-030 retired friction signals before they were built, because `/retro` already reads transcripts and is Writ's learning channel.
- Step 2: a claim cites `.writ/decision-records/adr-030-contract-verifier-boundary-front-door.md` § Decision and quotes "Friction signals are retired". The ADR-025 decisions it supersedes may be named.
- Step 2: Sources searched in the order Ledger, Git, MCP; MCP reads `not read: the ledger answered at Recorded`. No record is saved.
- Step 3: prints nothing.

**Implementation Reference:** Story 1 — WWB Dogfood Fixture, question 2 (Git: `bede42e`, `5da628c`)

**Status:** [ ] Pass  [ ] Fail

**Notes:**

---

### Scenario 7: Dogfood question 3 — why `/status` lists `/writ` first — answers at Recorded with a stale-ledger line

**Source:** Acceptance Criteria (AC-1.5) — Story 1; Dogfood Fixture row 3; Shadow Path "Stale ledger"; State Catalog "Code changed after the ledger entry"
**Feature:** none
**Verification:** human — no recipe

**Preconditions:**
- Setup block pasted; `reset` prints nothing.
- `live` running in a new session.

**Steps:**
1. `/why "Why does commands/status.md list /writ first in both allowlists?"`
2. Read the answer to the end.
3. In the first shell: `git -C "$CL" status --short`

**Expected Result:**
- Step 2: the `**Answer:**` line ends in `Recorded`: the front-door spec put `/writ` first in the slash allowlist as the entry command, and DEV-003 extended it to the Maintainer Note's bare list.
- Step 2: a claim cites `.writ/specs/2026-10-22-front-door/drift-log.md` → DEV-003; the front-door technical spec's Registration Edits may also be cited.
- Step 2: Git names `06b78eb` (front-door Story 2, 2026-10-22) and `d47bcec` (this spec's Story 2, 2026-10-25, which added `/why` to both lists). Because `d47bcec` touched the allowlists after the ledger entry, a line says the entry may describe an earlier shape, and the claim stays `Recorded`. Story 1's recorded run had no such line because it ran before `d47bcec`; this difference is expected.
- Step 2: MCP reads `not read: the ledger answered at Recorded`. No record is saved.
- Step 3: prints nothing.

**Implementation Reference:** Story 1 — WWB Dogfood Fixture, question 3

**Status:** [ ] Pass  [ ] Fail

**Notes:**

---

### Scenario 8: A subject the project does not contain gets one natural-language question and no answer

**Source:** Error Map "Locate the subject" — Story 1; Shadow Path "Empty input"; Experience Design Error Experience and State Catalog "Subject not found"
**Feature:** none
**Verification:** human — no recipe

**Preconditions:**
- Setup block pasted; `reset` prints nothing.
- `live` running in a new session.

**Steps:**
1. `/why "Why does the mobile app cache push tokens for 90 days?"`
2. Read the reply.
3. In the first shell: `git -C "$CL" status --short`

**Expected Result:**
- Step 2: the reply says what it searched for (terms such as "push token", "mobile app") and found nothing, then asks one plain question about where the subject lives. No option menu, no `**Answer:**` line, no Claims table, no tier.
- Step 3: prints nothing.

**Status:** [ ] Pass  [ ] Fail

**Notes:**

---

### Scenario 9: A question about an outside standard is pointed to `/research`

**Source:** Error Map "Locate the subject" — Story 1; DEV-002; Integration with Writ `/research` row
**Feature:** none
**Verification:** human — no recipe

**Preconditions:**
- Setup block pasted; `reset` prints nothing.
- `live` running in a new session.

**Steps:**
1. `/why "Why does HTTP/2 compress headers with HPACK?"`
2. Read the reply.
3. In the first shell: `git -C "$CL" status --short`

**Expected Result:**
- Step 2: the reply says the subject is not in this project and points to `/research` for a question about a standard, library, or vendor. No Claims table and no tier.
- Step 3: prints nothing.

**Status:** [ ] Pass  [ ] Fail

**Notes:**

---

### Scenario 10: Outside a git repository, `/why` answers from the ledger and says git is absent

**Source:** Error Map "Find anchor commits" — Story 1; Experience Design Error Experience "Not a git repository"
**Feature:** none
**Verification:** human — no recipe

**Preconditions:**
- Setup block pasted. `ls -a "$NG" | grep -c '^\.git$'` prints `0`.
- `live "$NG"` running in a new session.

**Steps:**
1. `/why "Why were friction signals never built?"`
2. Read the answer to the end.

**Expected Result:**
- Step 2: the `**Answer:**` line still ends in `Recorded`, citing `.writ/decision-records/adr-030-contract-verifier-boundary-front-door.md` § Decision, found by path and term search.
- Step 2: under Sources searched, the Git line reads `Git: not a git repository`. No commit SHA is cited as evidence.

**Status:** [ ] Pass  [ ] Fail

**Notes:**

---

### Scenario 11: With no `.writ/` ledger, a reason in a commit message answers at Stated

**Source:** Error Map "Read ledger files" (`.writ/` absent) — Story 1; Shadow Path "No ledger"; Experience Design Error Experience "No ledger" and State Catalog "Only a commit message states it"
**Feature:** none
**Verification:** human — no recipe

**Preconditions:**
- Setup block pasted. `ls -a "$NL" | grep -c '^\.writ$'` prints `0`.
- `live "$NL"` running in a new session.

**Steps:**
1. `/why "Why does retry.py cap retries at 3?"`
2. Read the answer to the end.
3. In the first shell: `git -C "$NL" status --short`

**Expected Result:**
- Step 2: the `**Answer:**` line ends in `Stated`: the payments API rate-limits a client after its fourth call in a minute.
- Step 2: the claim's evidence is the commit SHA of `Cap retries at 3: …` (`git -C "$NL" log --oneline -1 -- retry.py` prints it).
- Step 2: Sources searched reads `Ledger: none in this project` first, then the Git line.
- Step 3: prints nothing.

**Status:** [ ] Pass  [ ] Fail

**Notes:**

---

### Scenario 12: A ledger entry citing a missing file answers from the entry and lists the missing path

**Source:** Error Map "Read ledger files" (a cited path does not resolve) — Story 1
**Feature:** none
**Verification:** human — no recipe

**Preconditions:**
- Setup block pasted. `ls "$SL/.writ/research" 2>&1` reports no such directory.
- `live "$SL"` running in a new session.

**Steps:**
1. `/why "Why are logs written as JSON lines?"`
2. Read the answer to the end.
3. In the first shell: `git -C "$SL" status --short`

**Expected Result:**
- Step 2: the `**Answer:**` line ends in `Recorded`, citing `.writ/knowledge/conventions/log-format.md`: the log shipper parses one JSON object per line.
- Step 2: `.writ/research/2026-01-04-log-shipping-research.md` appears under Sources searched as a path that does not resolve. No claim cites it as evidence.
- Step 3: prints nothing.

**Status:** [ ] Pass  [ ] Fail

**Notes:**

---

### Scenario 13: An unresolvable PR number becomes a lead, and with no MCP server the answer says none connected

**Source:** Error Map "Read git history" and "Read MCP server" (no server connected) — Story 1; Business Rule 7 (MCP only when needed)
**Feature:** none
**Verification:** human — no recipe

**Preconditions:**
- Setup block pasted.
- `livebare "$NL"` running in a new session (no MCP server connected).

**Steps:**
1. `/why "Why is the request timeout in timeout.py 30 seconds?"`
2. Read the answer to the end.
3. In the first shell: `git -C "$NL" status --short`

**Expected Result:**
- Step 2: the strongest tier is below `Stated` (`Inferred` or `Unknown`); the commit message names the change but not the reason.
- Step 2: `#42` is listed as a lead git could not resolve.
- Step 2: the MCP line under Sources searched reads `MCP: none connected`. If the reply also names the code host's CLI, it says the CLI could not resolve `#42` (the project has no remote). No prompt to connect, install, or authorize anything appears.
- Step 3: prints nothing.

**Status:** [ ] Pass  [ ] Fail

**Notes:**

---

### Scenario 14: A planned change creates `.writ/research/`, saves the record, and a second save never overwrites it

**Source:** Error Map "Save why record" (`.writ/research/` absent; the dated path exists) — Story 1; Shadow Path "Change follows"; State Catalog "A change follows"; Feedback Model "A saved record prints its path and the `/create-spec` line"
**Feature:** none
**Verification:** human — no recipe

**Preconditions:**
- Setup block pasted. `ls "$SL/.writ/research" 2>&1` reports no such directory.
- `live "$SL"` running in a new session.

**Steps:**
1. `/why "Why are logs written as JSON lines? I want to switch them to plain text."`
2. Read the reply, then in the first shell: `ls "$SL/.writ/research/"; R1=$(ls "$SL"/.writ/research/*-why-*.md | head -1); shasum "$R1"; grep -n '^> \*\*\|^## \|^### ' "$R1"`
3. In the live session reply: `I also want them rotated daily once they are plain text.`
4. In the first shell: `ls "$SL/.writ/research/"; shasum "$R1"; git -C "$SL" status --short`

**Expected Result:**
- Step 2: the reply prints the saved path and suggests `/create-spec "switch logs to plain text"` (or close wording). `.writ/research/` now exists with one `<today>-why-<slug>.md` file. The grep shows `Asked`, `Subject`, `Change`, `Question` header lines; `## Why:`; `### Claims`; `### Sources searched`; then `## Preserve / Change / Avoid / Risk` as the last `##` heading, followed by `### Preserve`, `### Change`, `### Avoid`, `### Risk` in order. Each list item ends with a tier and a source; an empty one reads `- none found`.
- Step 4: a second record exists. If its slug matches the first, its name ends in `-2.md`. The first record's checksum is unchanged. `git status` lists only `.writ/research/` as untracked.

**Status:** [ ] Pass  [ ] Fail

**Notes:**

---

### Scenario 15: A refused MCP call is named under Sources searched and the answer stands on git

**Source:** Shadow Path "Upstream error" — Story 1; Error Map "Read MCP server" (the call fails or is refused); Experience Design Error Experience "An MCP call fails"
**Feature:** none
**Verification:** human — no recipe

**Preconditions:**
- Setup block pasted.
- `claude mcp list` shows at least one connected server, and Claude Code asks before calling MCP tools (default permission mode). If no server is connected, mark this scenario N/A; Scenario 13 covers that case.
- `live "$NL"` running in a new session.

**Steps:**
1. `/why "Why is the request timeout in timeout.py 30 seconds?"`
2. Deny every MCP tool permission prompt.
3. Read the answer to the end.

**Expected Result:**
- Step 3: under Sources searched, the MCP line names each server it tried and the reason (refused or denied). The answer is still printed, at the tier git supports (`Inferred` or `Unknown`).
- No step asks you to connect, install, or authorize a server, including servers that need sign-in.

**Status:** [ ] Pass  [ ] Fail

**Notes:**

---

### Scenario 16: `/why` with no question asks what to explain and waits

**Source:** Shadow Path "Nil input" — Story 1; Invocation `/why` row
**Feature:** none
**Verification:** human — no recipe

**Preconditions:**
- Setup block pasted; `reset` prints nothing.
- `live` running in a new session; type nothing else first.

**Steps:**
1. `/why`
2. Read the reply.
3. In the first shell: `git -C "$CL" status --short`

**Expected Result:**
- Step 2: one question, in substance "what do you want to know why about?", and nothing else: no anchor list, no answer, no menu.
- Step 3: prints nothing.

**Status:** [ ] Pass  [ ] Fail

**Notes:**

---

### Scenario 17: When the ledger and a later commit disagree, both are shown and the claim takes the lower tier

**Source:** Shadow Path "Conflicting sources" — Story 1; Business Rule 6; State Catalog "Ledger and later history disagree"
**Feature:** none
**Verification:** human — no recipe

**Preconditions:**
- Setup block pasted.
- `live "$SL"` running in a new session.

**Steps:**
1. `/why "Why is the pricing cache TTL 60 seconds?"`
2. Read the answer to the end.

**Expected Result:**
- Step 2: both reasons are shown: ADR-001 (`.writ/decision-records/adr-001-cache-ttl.md` § Decision, dated 2026-01-10: the feed refreshes every minute) and the 2026-03-02 commit (`keep the 60s TTL only for legacy clients; the feed now refreshes hourly`).
- Step 2: the commit is named as the newer source, and the claim is at `Stated`, the lower of the two tiers, not `Recorded`.
- A stale-ledger line may also appear (the commit touched `pricing_cache.py` after the ADR); it does not raise the tier.

**Status:** [ ] Pass  [ ] Fail

**Notes:**

---

### Scenario 18: `/why <path>:<line>` anchors on that line's history

**Source:** Experience Design Entry Point — Story 1; Invocation `/why <path>[:<line>]` row; Business Rule 2 (The anchor locates)
**Feature:** none
**Verification:** human — no recipe

**Preconditions:**
- Setup block pasted. `sed -n 249p "$CL/commands/status.md" | cut -c1-30` prints `` `/writ`, `/create-spec`, `/im ``.
- `live` running in a new session.

**Steps:**
1. `/why commands/status.md:249`
2. Read the reply to the end.
3. In the first shell: `git -C "$CL" status --short`

**Expected Result:**
- Step 2: a one-line restatement naming the slash allowlist in `commands/status.md`, then an anchor with the path, the line, and commits that touched it (among them `d47bcec`, `06b78eb`, `d36a283`).
- Step 2: an answer with a tier on every claim, citing ledger entries for the reason. No claim cites a commit's existence or the code's shape as the reason.
- Step 3: prints nothing.

**Status:** [ ] Pass  [ ] Fail

**Notes:**

---

### Scenario 19: With no recorded or stated reason, the answer is Unknown and does not reason from the code

**Source:** Experience Design State Catalog "Nothing found" — Story 1; Business Rules 4 (Code is not evidence of its own intent) and 5 (Null results are reported); Completion ("An `Unknown` answer with its sources searched is a valid result")
**Feature:** none
**Verification:** human — no recipe

**Preconditions:**
- Setup block pasted.
- `livebare "$NL"` running in a new session.

**Steps:**
1. `/why "Why is MAX_ROWS in limits.py set to 5000?"`
2. Read the answer to the end.
3. In the first shell: `git -C "$NL" status --short`

**Expected Result:**
- Step 2: the `**Answer:**` line ends in `Unknown`. No claim offers a reason drawn from the value or the code's shape (for example, a memory or performance guess).
- Step 2: Sources searched names every source read and what held nothing: `Ledger: none in this project`, the `add limits module` commit, `MCP: none connected`.
- Step 3: prints nothing.

**Status:** [ ] Pass  [ ] Fail

**Notes:**

---

### Scenario 20: A reverted change alone suggests the reason, and the answer says Inferred

**Source:** Experience Design State Catalog "One source suggests it" — Story 1; Confidence Tiers `Inferred` row ("a reverted change")
**Feature:** none
**Verification:** human — no recipe

**Preconditions:**
- Setup block pasted. `git -C "$NL" log --oneline -2 -- cache.py` shows the `Revert "Switch cache eviction to LRU"` commit on top.
- `livebare "$NL"` running in a new session.

**Steps:**
1. `/why "Why does cache.py use FIFO eviction?"`
2. Read the answer to the end.

**Expected Result:**
- Step 2: the `**Answer:**` line ends in `Inferred`, citing the revert commit: LRU was tried and reverted, which suggests but does not state that FIFO was preferred.
- Step 2: no claim is at `Recorded` or `Stated`; Sources searched names `Ledger: none in this project` and `MCP: none connected`.

**Status:** [ ] Pass  [ ] Fail

**Notes:**

---

## Story 2: Registration and Catalogs

### Scenario 21: The manifest registers `why` in the planning category, sorted by name

**Source:** Acceptance Criteria (AC-2.1) — Story 2
**Feature:** none
**Verification:** human — no recipe

**Preconditions:**
- Setup block pasted; `reset` prints nothing.

**Steps:**
1. `grep -n -B5 -A5 '  - name: why$' "$CL/.writ/manifest.yaml"`
2. `awk '/^commands:/{c=1;next} /^[a-z]/{c=0} c && /^  - name:/{print $3}' "$CL/.writ/manifest.yaml" > "$W/names.txt"; sort -c "$W/names.txt" && echo sorted`

**Expected Result:**
- Step 1: the entry reads `name: why`, `file: commands/why.md`, `category: planning`, `purpose: "Answer why code is the way it is from the ledger, git history, and MCP servers, with a confidence tier on every claim."`, `tags: [planning, why, history, ledger]`. The entry above it is `verify-spec`; the one below is `writ`.
- Step 2: `sorted`.

**Implementation Reference:** Story 2 — Files: `.writ/manifest.yaml`

**Status:** [ ] Pass  [ ] Fail

**Notes:**

---

### Scenario 22: Generated files carry `/why`, the generators report them current, and a hand edit is caught

**Source:** Acceptance Criteria (AC-2.2) — Story 2; Business Rule 15 (Generated files are regenerated)
**Feature:** none
**Verification:** human — no recipe

**Preconditions:**
- Setup block pasted; `reset` prints nothing.

**Steps:**
1. `(cd "$CL" && bash scripts/gen-skill.sh --check 2>/dev/null | head -1; python3 scripts/gen-platform-trees.py --check | head -2)`
2. `(cd "$CL" && grep -c '/why' SKILL.md claude-code/CLAUDE.md codex/AGENTS.md.template && ls cursor/plugin/commands/why.md plugins/writ/commands/why.md)`
3. `echo "hand edit" >> "$CL/plugins/writ/commands/why.md"; (cd "$CL" && python3 scripts/gen-platform-trees.py --check | head -2); reset`

**Expected Result:**
- Step 1: `pass` (gen-skill), then `pass` and `gen-platform-trees: pass (0 stale, 0 missing, 0 orphan, 0 unmapped, 0 vendor)`.
- Step 2: a count of at least 1 for each of the three files, and both plugin copies listed.
- Step 3: the first line is not `pass`, and the summary counts one stale file. `reset` prints nothing.

**Implementation Reference:** Story 2 — Files: `SKILL.md`, `claude-code/CLAUDE.md`, `codex/AGENTS.md.template`, `cursor/plugin/commands/why.md`, `plugins/writ/commands/why.md` (all generated)

**Status:** [ ] Pass  [ ] Fail

**Notes:**

---

### Scenario 23: The hand-maintained catalogs list `/why` in the right place with updated counts

**Source:** Acceptance Criteria (AC-2.3) — Story 2
**Feature:** none
**Verification:** human — no recipe

**Preconditions:**
- Setup block pasted; `reset` prints nothing.

**Steps:**
1. `grep -n -B1 '^| `/why`' "$CL/README.md"`
2. `grep -n -B1 -A1 'why.md  *# /why' "$CL/adapters/cursor.md"; grep -n 'manifest.yaml (34)' "$CL/adapters/cursor.md"`
3. `grep -o '`/research`, `/why`' "$CL/commands/status.md"; grep -o '`research`, `why`' "$CL/commands/status.md"`
4. `grep -n '^| `high`' "$CL/.writ/docs/model-tiers.md"`

**Expected Result:**
- Step 1: the `/why` row sits directly after the `/research` row in § Commands → Planning & Specification and ends "…ends with a Preserve / Change / Avoid / Risk list `/create-spec` reads".
- Step 2: `why.md  # /why` between the `verify-spec.md` and `writ.md` lines, its `#` aligned with theirs; the commands count comment reads `(34)`.
- Step 3: one match from each command: the slash list has `` `/research`, `/why` `` and the bare list has `` `research`, `why` ``.
- Step 4: the `high` row lists `` `security-audit`, `why`, `writ` `` in that order and ends with `(17)`.

**Implementation Reference:** Story 2 — Files: `README.md`, `adapters/cursor.md`, `commands/status.md`, `.writ/docs/model-tiers.md`

**Status:** [ ] Pass  [ ] Fail

**Notes:**

---

### Scenario 24: Structure rows pass, and the full test suite and quality gate report zero failures and findings

**Source:** Acceptance Criteria (AC-2.4) — Story 2; also AC-3.4 and AC-4.3 (full-suite parts); Success Criteria; DEV-003
**Feature:** none
**Verification:** human — no recipe

**Preconditions:**
- Setup block pasted; `reset` prints nothing. Run outside any sandbox (eval runs `git init` in a temp dir). About five minutes. Run pytest alone, not beside eval or the bash tests.

**Steps:**
1. `(cd "$CL" && python3 scripts/eval-command-structure.py --root . | grep -E 'why|Step 1.2')`
2. `grep -n 'CURSOR_COUNT =\|HIGH_COUNT =' "$CL/scripts/tests/test_front_door.py"`
3. `pt -q 2>&1 | tail -1`
4. `(cd "$CL" && for t in scripts/tests/test_*.sh; do bash "$t" >/dev/null 2>&1 || echo "FAIL $t"; done; echo "bash loop done")`
5. `(cd "$CL" && bash scripts/eval.sh >/dev/null; echo "exit $?"); tail -2 "$(ls -t "$CL"/.writ/state/eval-*.md | head -1)"`
6. `reset`

**Expected Result:**
- Step 1: three `PASS` lines: `command-structure:commands/why.md:heading:Confidence Tiers`, `command-structure:commands/why.md:frontmatter:entry_level`, and ``command-structure:commands/create-spec.md:heading:Step 1.2: Read a `/why` Handoff``.
- Step 2: `CURSOR_COUNT = "(34)"` and `HIGH_COUNT = "(17)"` (DEV-003).
- Step 3: no `failed` in the summary (Story 4 recorded `3071 passed, 2 skipped`; later merges on the phase branch may change the counts).
- Step 4: only `bash loop done`; no `FAIL` line.
- Step 5: `exit 0`, then `- Findings: 0` and `- Run errors: 0`.
- Step 6: prints nothing.

**Implementation Reference:** Story 2 — Files: `scripts/eval-command-structure.py` (`ROWS`), `scripts/tests/test_front_door.py`, `scripts/tests/test_platform_neutral_names.py`, `scripts/tests/test_gen_platform_trees.py`

**Status:** [ ] Pass  [ ] Fail

**Notes:**

---

## Story 3: The Front Door Routes Why Questions to `/why`

### Scenario 25: The routing table keeps six rows and its fifth row routes `/why`

**Source:** Acceptance Criteria (AC-3.1) — Story 3; Business Rule 14 (Front-door route)
**Feature:** none
**Verification:** human — no recipe

**Preconditions:**
- Setup block pasted; `reset` prints nothing.

**Steps:**
1. `sed -n '/^## Routing Rules/,/^## /p' "$CL/commands/writ.md" | grep '^| '`

**Expected Result:**
- Step 1: a header row, a separator row, and six data rows. The fifth data row reads `| Asks why something in this project is the way it is, or how it works | `/why` (a question about something outside the project: `/research`) |`.

**Implementation Reference:** Story 3 — Files: `commands/writ.md` (§ Routing Rules)

**Status:** [ ] Pass  [ ] Fail

**Notes:**

---

### Scenario 26: Step 2's "Why or how" bullet routes `/why`, and the interim note is gone

**Source:** Acceptance Criteria (AC-3.2) — Story 3
**Feature:** none
**Verification:** human — no recipe

**Preconditions:**
- Setup block pasted; `reset` prints nothing.

**Steps:**
1. `grep -n 'Why or how' "$CL/commands/writ.md"`
2. `grep -c 'when it ships' "$CL/commands/writ.md"`

**Expected Result:**
- Step 1: `- **Why or how.** Route `/why`. A question about something outside the project, such as a library, a standard, or a vendor, routes `/research`.`
- Step 2: `0`.

**Implementation Reference:** Story 3 — Files: `commands/writ.md` (§ Step 2)

**Status:** [ ] Pass  [ ] Fail

**Notes:**

---

### Scenario 27: The prompting guide's why-or-how recipe routes `/why` first

**Source:** Acceptance Criteria (AC-3.3) — Story 3
**Feature:** none
**Verification:** human — no recipe

**Preconditions:**
- Setup block pasted; `reset` prints nothing.

**Steps:**
1. `sed -n '/A why or how question/,/^## /p' "$CL/.writ/docs/prompting-guide.md" | grep -n 'Route:\|Weak\|Strong'`
2. `grep -c 'when it ships' "$CL/.writ/docs/prompting-guide.md"`

**Expected Result:**
- Step 1: `Route: `/why` (`/research` for a question about something outside the project)`, with the recipe's Weak and Strong lines still present.
- Step 2: `0`.

**Implementation Reference:** Story 3 — Files: `.writ/docs/prompting-guide.md`

**Status:** [ ] Pass  [ ] Fail

**Notes:**

---

### Scenario 28: The front-door and guide tests pass, and a fifth row without `/why` fails

**Source:** Acceptance Criteria (AC-3.4) — Story 3
**Feature:** none
**Verification:** human — no recipe

**Preconditions:**
- Setup block pasted; `reset` prints nothing.

**Steps:**
1. `pt scripts/tests/test_front_door.py scripts/tests/test_prompting_guide.py -q 2>&1 | tail -1`
2. `(cd "$CL" && python3 scripts/gen-platform-trees.py --check | head -1)`
3. ``sed -i '' 's#| `/why` (a question about something outside the project: `/research`) |$#| `/research` |#' "$CL/commands/writ.md"; pt scripts/tests/test_front_door.py -q -k "routing_rules or why_route" 2>&1 | grep -E 'lacks|failed|passed'; reset``

**Expected Result:**
- Step 1: `21 passed` (the count Story 3 recorded) and no `failed`.
- Step 2: `pass`.
- Step 3: an assertion that the row 5 Route cell lacks `/why`, then `1 failed, 1 passed` (with a deselected count). `reset` prints nothing.
- Eval for this story: Scenario 24, Step 5.

**Implementation Reference:** Story 3 — Files: `scripts/tests/test_front_door.py` (`ROUTES`, `test_why_route`), `scripts/tests/test_prompting_guide.py`

**Status:** [ ] Pass  [ ] Fail

**Notes:**

---

### Scenario 29: `/writ` proposes `/why` for a project question and `/research` for an outside one

**Source:** Experience Design Entry Point (`/writ "why is X like this?"`) — Story 3; Business Rule 14
**Feature:** none
**Verification:** human — no recipe

**Preconditions:**
- Setup block pasted; `reset` prints nothing.
- `live` running in a new session.

**Steps:**
1. `/writ "why does commands/status.md list /writ first in both allowlists?"`
2. Read the restatement and the confirmation, then press Escape (widget) or reply `Not what I meant` (list).
3. Start a new session. `/writ "why does HTTP/2 compress headers with HPACK?"`
4. Read the confirmation, then press Escape or reply `Not what I meant`.
5. In the first shell: `git -C "$CL" status --short`

**Expected Result:**
- Step 2: the restatement, then `Proposed: /why` with a one-line reason; `/why (Recommended)` is the first option and `Not what I meant` the last; at most four options. Nothing runs.
- Step 4: the proposed route is `/research`, because the subject is a standard outside the project.
- Step 5: prints nothing.

**Status:** [ ] Pass  [ ] Fail

**Notes:**

---

## Story 4: `/create-spec` Reads the `/why` Handoff

### Scenario 30: Step 1.2 sits between Steps 1.1 and 1.3 and names its three search places

**Source:** Acceptance Criteria (AC-4.1) — Story 4
**Feature:** none
**Verification:** human — no recipe

**Preconditions:**
- Setup block pasted; `reset` prints nothing.

**Steps:**
1. `grep -n '^#### Step 1\.' "$CL/commands/create-spec.md" | head -4`
2. `sed -n '/^#### Step 1.2:/,/^#### Step 1.3:/p' "$CL/commands/create-spec.md"`

**Expected Result:**
- Step 1: `Step 1.1: Initial Context Scan`, ``Step 1.2: Read a `/why` Handoff``, `Step 1.3: Discovery Conversation (Plan Mode)`, in that order (Step 1.0 may print first).
- Step 2: one paragraph that looks for the handoff section in this conversation, in a file the invocation names, and in `.writ/research/*-why-*.md` records whose `Subject` or `Change` line shares a keyword with the feature idea, and ends "None found: skip this step." No question to the user is added.

**Implementation Reference:** Story 4 — Files: `commands/create-spec.md` (Step 1.2)

**Status:** [ ] Pass  [ ] Fail

**Notes:**

---

### Scenario 31: The seam test ties Step 1.2 to the heading `/why` writes, and a renamed heading breaks it

**Source:** Acceptance Criteria (AC-4.2) — Story 4; Business Rule 13 (The handoff maps into the contract)
**Feature:** none
**Verification:** human — no recipe

**Preconditions:**
- Setup block pasted; `reset` prints nothing.

**Steps:**
1. `sed -n '/^#### Step 1.2:/,/^#### Step 1.3:/p' "$CL/commands/create-spec.md" | grep -o 'Preserve into Business Rules\|Change into the Deliverable\|Avoid into Scope Boundaries → Excluded\|Risk into Technical Concerns\|Keep each item.s tier and cite the record'`
2. `pt scripts/tests/test_why_command.py -q -k handoff`
3. `sed -i '' 's|^## Preserve / Change / Avoid / Risk$|## Preserve, Change, Avoid, Risk|' "$CL/commands/why.md"; pt scripts/tests/test_why_command.py -q -k handoff 2>&1 | grep -E 'no handoff heading|lacks|failed|passed'; reset`

**Expected Result:**
- Step 1: five lines: the four mappings and the keep-tier-and-cite sentence.
- Step 2: `2 passed` (`test_handoff_shape` and `test_create_spec_reads_handoff`).
- Step 3: assertion lines saying `commands/why.md` has no handoff heading line (and lacks the heading), then `2 failed`. `reset` prints nothing.

**Implementation Reference:** Story 4 — Files: `scripts/tests/test_why_command.py` (`test_create_spec_reads_handoff` reads the literal from `commands/why.md`)

**Status:** [ ] Pass  [ ] Fail

**Notes:**

---

### Scenario 32: The create-spec byte budget is re-pinned with a dated disclosure

**Source:** Acceptance Criteria (AC-4.3) — Story 4; Business Rule 16 (Budgets)
**Feature:** none
**Verification:** human — no recipe

**Preconditions:**
- Setup block pasted; `reset` prints nothing.

**Steps:**
1. `wc -c < "$CL/commands/create-spec.md"`
2. `sed -n '/^#### Step 1.2:/,/^#### Step 1.3:/p' "$CL/commands/create-spec.md" | sed '$d' | wc -c`
3. `grep -n -B1 '"commands/create-spec.md": ' "$CL/scripts/tests/test_governor_enforcement.py"`
4. `pt scripts/tests/test_governor_enforcement.py -q 2>&1 | tail -1`

**Expected Result:**
- Step 1: `39169`.
- Step 2: `555`, under 700.
- Step 3: `# 2026-10-25 (2026-10-25-why-command Story 4): 13654 -> 14209; Step 1.2 reads a /why handoff.` directly above `"commands/create-spec.md": 14209,` (39,169 − 24,960 = 14,209), in the same form as the dated comments above it.
- Step 4: no `failed`.

**Implementation Reference:** Story 4 — Files: `scripts/tests/test_governor_enforcement.py` (`KNOWN_OVER_BUDGET`)

**Status:** [ ] Pass  [ ] Fail

**Notes:**

---

### Scenario 33: Dogfood question 4 — a planned fifth confirmation option — saves a record with the handoff last

**Source:** Acceptance Criteria (AC-4.4) — Story 4; Dogfood Fixture row 4; Shadow Path "Change follows"; Error Map "Save why record"; Experience Design Output Shape and Feedback Model
**Feature:** none
**Verification:** human — no recipe

**Preconditions:**
- Setup block pasted; `reset` prints nothing.
- `live` running in a new session.

**Steps:**
1. In the first shell, read the committed evidence: `grep -n '^> \*\*\|^## \|^### ' "$CL/.writ/research/2026-10-25-why-writ-confirmation-four-options.md"`
2. In the live session: `/why "Why does /writ's confirmation offer at most four options? I want to add a fifth."`
3. Read the reply to the end.
4. In the first shell: `git -C "$CL" status --short; N=$(git -C "$CL" status --short | awk '{print $2}' | head -1); grep -n '^## \|^### ' "$CL/$N"`
5. `reset`

**Expected Result:**
- Step 1: the four header lines (`Asked: 2026-10-25`, `Subject`, `Change: add a fifth option to /writ's confirmation`, `Question`); `## Why:`; `### Claims`; `### Sources searched`; then `## Preserve / Change / Avoid / Risk` as the last `##` heading, with `### Preserve`, `### Change`, `### Avoid`, `### Risk` in order.
- Step 3: the `**Answer:**` line ends in `Recorded`: Claude Code's question tool takes two to four options, so the confirmation was cut to four. Claims cite `.writ/specs/2026-10-22-front-door/spec.md` Business Rule 4 or `.writ/specs/2026-10-22-front-door/drift-log.md` DEV-007. Git names `9d75383`. MCP reads `not read: the ledger answered at Recorded`.
- Step 3: the handoff's Preserve keeps at most four options; Risk names the question tool dropping a fifth option or `test_confirmation_fits_four_options` failing. The reply prints the saved path and suggests `/create-spec "add a fifth option to /writ's confirmation"` (or close wording).
- Step 4: exactly one untracked file, `.writ/research/<today>-why-<slug>.md` (ending `-2.md` if today is 2026-10-25 and the slug matches the committed record), whose headings match Step 1's shape. No other file changed.
- Step 5: prints nothing.

**Implementation Reference:** Story 4 — Files: `.writ/research/2026-10-25-why-writ-confirmation-four-options.md`; WWB Dogfood Fixture

**Status:** [ ] Pass  [ ] Fail

**Notes:**

---

### Scenario 34: Dogfood question 4, part 2 — `/create-spec` Steps 1.1 and 1.2 carry the handoff into a draft contract

**Source:** Acceptance Criteria (AC-4.4) — Story 4; Business Rule 13 (The handoff maps into the contract)
**Feature:** none
**Verification:** human — no recipe

**Preconditions:**
- Setup block pasted; `reset` prints nothing, so the only why record in the clone is the committed one.
- `liveplan` running in a new session (Plan Mode).

**Steps:**
1. `/create-spec "add a fifth option to /writ's confirmation"`
2. Let it run through its context scan. When discovery starts asking questions, reply: `Stop after Step 1.2. List each item you carried from a /why handoff, the contract section it went to, its tier, and the record it cites.`
3. Read the reply.
4. In the first shell: `git -C "$CL" status --short`

**Expected Result:**
- Step 3: the record found is `.writ/research/2026-10-25-why-writ-confirmation-four-options.md`, matched on its `Change` or `Subject` line.
- Step 3: Business Rules carries the Preserve items: at most four options because Claude Code's question tool renders two to four (`Recorded`), and "Not what I meant" stays with the left-out routes named (`Recorded`).
- Step 3: Technical Concerns carries the Risk items: the question tool drops or truncates a fifth option, and `test_confirmation_fits_four_options` fails on one (both `Recorded`). The Deliverable carries the Change item (`Inferred`); Scope Boundaries → Excluded carries the Avoid item, offering every route as its own option (`Recorded`). Every item cites the record.
- Step 2: discovery did not ask how many options the confirmation should hold.
- Step 4: prints nothing; no file under `.writ/specs/` was written.

**Implementation Reference:** Story 4 — WWB Dogfood Fixture (draft contract)

**Status:** [ ] Pass  [ ] Fail

**Notes:**

---

### Scenario 35: With no matching handoff, Step 1.2 is skipped silently

**Source:** Error Map "Find handoff in create-spec" (no section anywhere) — Story 4
**Feature:** none
**Verification:** human — no recipe

**Preconditions:**
- Setup block pasted; `reset` prints nothing.
- `liveplan` running in a new session.

**Steps:**
1. `/create-spec "give /status a --json output mode"`
2. Read the context summary. When discovery starts asking questions, reply: `Stop here. Did Step 1.2 carry anything from a /why handoff?`
3. In the first shell: `git -C "$CL" status --short`

**Expected Result:**
- Step 2: the context summary says nothing about a `/why` handoff, and discovery proceeds normally. The answer to the follow-up is that none was found, so nothing was carried. The four-options record is not used.
- Step 3: prints nothing.

**Status:** [ ] Pass  [ ] Fail

**Notes:**

---

### Scenario 36: A named file without the handoff heading gets one line in the context summary

**Source:** Error Map "Find handoff in create-spec" (the named file lacks the heading) — Story 4
**Feature:** none
**Verification:** human — no recipe

**Preconditions:**
- Setup block pasted; `reset` prints nothing. `grep -c 'Preserve / Change' "$CL/commands/status.md"` prints `0`.
- `liveplan` running in a new session.

**Steps:**
1. `/create-spec "give /status a --json output mode; the handoff is in commands/status.md"`
2. Read the context summary, then press Escape or reply `Stop here.`
3. In the first shell: `git -C "$CL" status --short`

**Expected Result:**
- Step 2: the context summary has one line saying `commands/status.md` has no `## Preserve / Change / Avoid / Risk` section, and the command continues to discovery. No handoff items are carried.
- Step 3: prints nothing.

**Status:** [ ] Pass  [ ] Fail

**Notes:**

---

## Pending Stories

None. All four stories are Completed ✅.
