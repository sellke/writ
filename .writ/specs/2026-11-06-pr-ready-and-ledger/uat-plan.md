# UAT Plan: PR Ready and Verification Ledger

> **Generated:** 2026-11-06
> **Spec:** `.writ/specs/2026-11-06-pr-ready-and-ledger/`
> **Stories Covered:** 3 of 3 completed
> **Total Scenarios:** 7 (6 scripted, 1 human)
> **Verification recipe:** none. Writ has no app to launch, so no `.writ/docs/app-verification.md` was drafted or saved, and no scenario is `machine`. A **scripted** scenario is decided by the commands in its Steps: the expected line 1, reason lines, and exit code. It cites no `evidence/uat/<id>/result.json`, so `exit-criteria.py check-uat` counts it as non-machine. A **human** scenario needs a person, and its Verification line says why. Items that a passing test already exercises are listed under Covered by Tests instead of becoming scenarios.

## How to Use This Plan

1. Paste the setup block below once per shell.
2. Run each Covered by Tests row. A row passes when its command exits 0.
3. Work through the scenarios in order. For each one, run the steps exactly as written and compare the output with Expected Result.
4. Mark Pass or Fail and add notes for anything unexpected. File each Fail as an issue or feed it back to the spec.
5. The feature passes UAT when every row and scenario passes, or a failure is accepted as a known limitation.

**Conventions for this plan:**

- Run in bash or zsh, from the root of a Writ checkout that contains this spec. The scripts run from `$REPO`. Each writes only under the `--repo` it is given (`<repo>/.writ/state/verify-ledger.json`), and every scenario passes a scratch folder under `$W`, never `$REPO`.
- Paste this setup block once per shell. Stop if the first two lines do not print `REPO=/...` and `W=/...`.

  ```bash
  REPO=$(git rev-parse --show-toplevel) && test -f "$REPO/scripts/pr-ready.py" && test -f "$REPO/scripts/verify-ledger.py" && echo "REPO=$REPO"
  W=$(mktemp -d "${TMPDIR:-/tmp}/writ-uat-prready.XXXXXX") && echo "W=$W"
  export PYTHONDONTWRITEBYTECODE=1
  PRR="$REPO/scripts/pr-ready.py"; VL="$REPO/scripts/verify-ledger.py"; FX="$REPO/scripts/tests/fixtures/pr-ready"
  mkdir -p "$W/empty"   # a --repo with no ledger
  # g: git with a throwaway identity and no signing, for the scratch repos
  g() { git -c user.name=t -c user.email=t@example.com -c commit.gpgsign=false "$@"; }
  # edit FILE OLD NEW: replace the whole line OLD with NEW (no sed -i, so it works on macOS and Linux)
  edit() { sed "s/^$2\$/$3/" "$1" > "$1.tmp" && mv "$1.tmp" "$1"; }
  # mkrepo DIR: main holds app.txt (lines L01 to L20); branch feature changes L10; prints feature's head
  mkrepo() {
    mkdir -p "$1" && g -C "$1" init -q -b main && printf '.writ/\n' >> "$1/.git/info/exclude" &&
    seq -f 'L%02g' 1 20 > "$1/app.txt" && g -C "$1" add -A && g -C "$1" commit -qm base &&
    g -C "$1" checkout -qb feature && edit "$1/app.txt" L10 "L10 changed" && g -C "$1" commit -qam change &&
    git -C "$1" rev-parse HEAD
  }
  # rec DIR PR: record DIR's checked-out head for PR against main, with one passing evidence command
  rec() { python3 "$VL" record --pr "$2" --head "$(git -C "$1" rev-parse HEAD)" --base main --evidence 0 uat --repo "$1"; }
  # chk DIR PR HEAD [--base REF]: check one head, then print its exit code
  chk() { d=$1 p=$2 h=$3; shift 3; python3 "$VL" check --pr "$p" --head "$h" --repo "$d" "$@"; echo "exit $?"; }
  # pt SELECTION...: pytest on Python 3.9 from the checkout root; PY=3.14 pt ... runs it on 3.14
  pt() { (cd "$REPO" && uv run --isolated --python "${PY:-3.9}" --with pytest pytest -q -p no:cacheprovider "$@"); }
  ```

- Expected results come from the spec, `drift-log.md` (DEV-001 to DEV-010), the three What Was Built records, and the tree at `516f4b1` (branch `phase/16-verified-landing`). Story 1 landed in `23ba716`, Story 2 in `5fbaa73`, Story 3 in `76ea787`.
- Short SHAs and patch-ids in the output change from run to run, because commit times differ. Compare the line shapes, reason codes, and exit codes. `<H>`, `<J>`, and `<R>` stand for the 7-character short SHAs a step prints.
- Scenarios 1 to 6 were run for this plan on 2026-11-06 against `516f4b1`, once in bash and once in zsh. All matched. Scenario 7 was not run. The Status boxes are left for the tester.
- When done: `rm -rf "$W"`.

## Coverage Summary

| Story | Status | Scenarios | Source Breakdown |
|-------|--------|-----------|-----------------|
| Story 1: Verification ledger | ✅ Covered | 4 | AC: 0, Errors: 0, Shadow: 0, Edge: 4. AC-1.1 to AC-1.5 are in Covered by Tests |
| Story 2: `pr-ready.py` snapshot and blocker classes | ✅ Covered | 2 | AC: 0, Errors: 2, Shadow: 0, Edge: 0. AC-2.1 to AC-2.5 are in Covered by Tests |
| Story 3: Ledger gate and machine output | ✅ Covered | 1 | AC: 0, Errors: 0, Shadow: 0, Edge: 0, Experience: 1. AC-3.1 to AC-3.5 are in Covered by Tests |

- Every acceptance criterion has a passing test named in its story's What Was Built record, so all 15 are Covered by Tests rows. The scenarios cover only what no test exercises.
- Error & Rescue Map: all 16 rows are exercised by tests. Scenarios 5 and 6 check the two drift amendments to "Validate snapshot" that no test covers: DEV-006 (a missing key in the comments chain) and DEV-008 (the 80-character cut).
- Shadow Paths: all 12 cells are exercised by tests.
- Interaction Edge Cases: four have no test and are Scenarios 1 to 4. The other seven are Covered by Tests rows: "Force-push back to a verified head" and "Re-record the same head" (AC-1.1), "UNSTABLE with a failing optional check" (AC-2.1), "Checks pending and a thread unresolved", "BLOCKED with review required", and "head_moved together with a blocker" (AC-2.2), and "BLOCKED, ledger not verified, nothing else" (AC-3.1).
- Experience Design: the Moment of truth, Error experience, both State Catalog tables, and Feedback model are exercised by tests (AC-1.1 to AC-3.3). Scenario 7 covers the parts that need a live PR: the entry point (a person runs the scripts by hand), the `gh` step of the happy path, and whether the reason lines match what GitHub shows.
- Drift: DEV-001 and DEV-002 are in the AC-1.4 rows, DEV-004 in AC-1.2, DEV-005 in AC-2.2, DEV-007 in AC-2.5 and the contract row, DEV-008 (containers) and DEV-010 in AC-2.3, and DEV-009 in AC-3.5. DEV-003 changed only the test harness. DEV-006 is Scenario 5 and the DEV-008 length cut is Scenario 6.
- No pending stories: all three are Completed ✅.

## Covered by Tests

| Item | Test selection |
|-----------|----------------|
| AC-1.1: `record` writes one full `verify-ledger/1` row, `check` reads `verified_exact`, and recording the same head again replaces the row with `reason: replaced`. Also Shadow Paths `record` and `check` happy path and `check` nil and empty input (`no_rows`); Edge Cases "Re-record the same head" and "Force-push back to a verified head" (an exact-row match does not depend on history); State Catalog `record` accepted, `check` exact head, no row for the PR | `pt scripts/tests/test_verify_ledger.py::RecordTests` |
| AC-1.2: each refusal (`evidence_failed`, `head_not_checked_out`, `dirty_tree`) prints `fail`, exits 1, and leaves the ledger byte-identical; every refusal that holds prints. Also Error Map "Record" (refusals) and "Write ledger" (`os.replace` raises: file unchanged, no `*.tmp`); State Catalog `record` refused; DEV-004 (a submodule at another commit refuses `record`) | `pt scripts/tests/test_verify_ledger.py::RefusalTests scripts/tests/test_verify_ledger.py::PopulatedSubmoduleTests` |
| AC-1.3: one changed byte, a whitespace-only re-indent, `chmod +x`, changed binary bytes, and H's diff under PR 8 each read `patch_id_mismatch`, exit 1; an unchanged rebase reads `verified_patch_id`. Also State Catalog `check` same-PR patch-id and id differs | `pt scripts/tests/test_verify_ledger.py::MutationTests` |
| AC-1.4 (config): hostile diff config (`diff.noprefix`, `diff.algorithm=patience`, `diff.renames=copies`, `color.ui=always`) and `GIT_DIFF_OPTS=-u0` leave the ids unchanged; a submodule pointer bump reads `patch_id_mismatch` under ignore config. Also Error Map "Compute patch-id" (hostile user diff config); DEV-001 | `pt scripts/tests/test_verify_ledger.py::HostileConfigTests scripts/tests/test_verify_ledger.py::SubmoduleTests` |
| AC-1.4 (fail closed): a head not in the repo reads `head_unavailable`, an unresolvable base `base_unavailable`; without `patch-id --verbatim` the row stores `patch_id: null` and only the exact head passes; an empty diff or no merge base stores a null id with the reason; with `git` missing or failing, `record` exits 2 and `check` answers an exact head and otherwise fails closed; a head with a trailing newline fails closed. Also Error Map "Check", "Compute patch-id" (unsupported; empty diff, no merge base), and "Run git"; Shadow Paths `record` empty input and upstream error; DEV-002 (`git_failed`) | `pt scripts/tests/test_verify_ledger.py::FailClosedTests scripts/tests/test_verify_ledger.py::ContractTests::test_head_with_trailing_newline_is_not_a_full_id` |
| AC-1.5: the Classification row with the shared Callers text; `check` in an empty dir prints `fail` with `no_rows`, exit 1; `--help` exits 0; a malformed ledger makes `check` and `record` exit 2 with stdout empty and the file untouched; usage errors (unresolvable `--head` or `--base`, bad evidence exit, empty command, `--pr` below 1, no `--evidence`, not a git work tree) exit 2; the plugin copy matches. Also Error Map "Read ledger (check)" and "Record" (unresolvable rev, bad evidence); Shadow Paths `record` nil input and `check` upstream error; State Catalog ledger file malformed | `pt scripts/tests/test_verify_ledger.py::ContractTests` |
| AC-2.1: each blocker fixture prints `fail`, its `<class>: <detail>` line, a `pr-ready: fail (` summary, and exit 3, 4, 5, or 6; each `merge_gates` detail starts with its gate token; a failing optional check blocks; merge state `DRAFT` alone is `draft`; a merged PR is `not_open MERGED`. Also Business Rules 5 and 6; Edge Case "UNSTABLE with a failing optional check"; State Catalog merge conflict, open review thread, failing check, draft PR | `pt scripts/tests/test_pr_ready.py::BlockerTests scripts/tests/test_pr_ready.py::OrderAndUnknownTests::test_merged_pr_is_not_open` |
| AC-2.2: `all-four.json` prints the four classes in order, exit 3; each unknown fixture alone is `unverifiable`, exit 0; `pending-and-thread.json` exits 4 with the unknown after the thread; `BLOCKED` with review required prints only `review_required`; `head_moved` lists beside a blocker; unresolved threads in a truncated page still block; unknowns print in table order; no checks and no threads pass; null path, line, and login print `?`. Also Edge Cases "Checks pending and a thread unresolved", "BLOCKED with review required", "head_moved together with a blocker"; Error Map "Judge threads" (more than 100); Shadow Paths `pr-ready.py check` empty input; State Catalog checks running, mergeability unknown, several at once; DEV-005 (a running check's conclusion `""` in `checks-pending.json`) | `pt scripts/tests/test_pr_ready.py::OrderAndUnknownTests` |
| AC-2.3: a missing file and each bad fixture exit 2 with stdout empty and stderr starting `pr-ready: `; wrong types, a short or uppercase head, unknown enum values, and deeply nested JSON exit 2; a rejected container prints as `<dict>` (DEV-008); `--help` prints the three `gh` lines byte for byte, also on an ASCII stdout; a head with a trailing newline exits 2 (DEV-010 repro). Also Error Map "Read snapshot" and both "Validate snapshot" rows; Shadow Paths `pr-ready.py check` nil input and upstream error; State Catalog snapshot missing or malformed | `pt scripts/tests/test_pr_ready.py::SnapshotValidityTests scripts/tests/test_pr_ready_head_repro.py` |
| AC-2.4: hostile path and login text (newline, ESC, U+2028) is escaped onto one line; the comment-body marker never reaches stdout or stderr; a hostile check name is escaped; the script names no comment-body field. Also Error Map "Judge threads" (hostile text); Business Rule 7; Interaction pattern "identifiers only" | `pt scripts/tests/test_pr_ready.py::UntrustedTextTests` |
| AC-2.5: the `pr-ready.py` row, Notes entry (exit codes 3 to 6 and the gate tokens), Check-shape exception, ADR-029 amendment, the `draft.json` smoke at exit 6, and the plugin copy. Also DEV-007 | `pt scripts/tests/test_pr_ready.py::ContractTests` |
| AC-3.1: a recorded head passes with `pr-ready: pass (PR 66 head <short>, ledger VERIFIED)`, exit 0; a one-byte change exits 6 with `merge_gates: not_verified head <short>: patch_id_mismatch ...`; `BLOCKED` with only `not_verified` prints both gates; no ledger gives `not_verified head 3ddc8c8: no_rows PR 66`, exit 6. Also Experience Design Moment of truth and Error experience (new head); Shadow Paths `pr-ready.py check` happy path; Edge Case "BLOCKED, ledger not verified, nothing else"; State Catalog ready and new head; the success criterion that changing only `headRefOid` flips exit 0 to 6 | `pt scripts/tests/test_pr_ready.py::LedgerGateTests::test_verified_head_passes_and_a_changed_head_exits_6 scripts/tests/test_pr_ready.py::LedgerGateTests::test_blocked_with_only_not_verified_prints_both scripts/tests/test_pr_ready.py::JsonTests::test_no_ledger_row_is_not_verified` |
| AC-3.2: an unchanged rebase passes through `verified_patch_id`; a whitespace-only re-indent exits 6 with `not_verified` | `pt scripts/tests/test_pr_ready.py::LedgerGateTests::test_rebase_passes_and_reindent_exits_6` |
| AC-3.3: a ledger holding `{"schema": "x"}` plus an unresolved thread prints `unresolved_threads: ...` and `merge_gates: not_verified ledger_unreadable (...)`, exit 4, not 2. Also Error Map "Read ledger (pr-ready)"; State Catalog ledger file unreadable | `pt scripts/tests/test_pr_ready.py::LedgerGateTests::test_unreadable_ledger_keeps_other_blockers` |
| AC-3.4: `--json` over every fixture and the AC-3.1 repo prints one object with the seven keys, the full 40-hex `head`, `{class, detail}` and `{code, detail}` items, and the text run's exit code; the exit-2 cases print nothing on stdout; details match the text and are JSON-escaped | `pt scripts/tests/test_pr_ready.py::JsonTests scripts/tests/test_pr_ready.py::LedgerGateTests::test_json_on_the_ledger_repo` |
| AC-3.5: copied beside `verify-ledger.py`, `pr-ready.py` gives the same line 1 and exit; copied alone it exits 2 with `pr-ready: cannot load verify-ledger.py (...)`; a broken sibling or one without `ledger_check` exits 2; a check writes no bytecode; the Notes entry names `--json` and the ledger requirement. Also Error Map "Load ledger module"; DEV-009 | `pt scripts/tests/test_pr_ready.py::SiblingLoadTests` |
| Contract registration for both scripts: Classification rows, Notes entries, the Check-shape exception, ADR-029 rules 1 to 7 unchanged, both smokes, `FAIL_EXITS` limited to `pr-ready.py`, and the widened AC-ID guard (AC-1.5, AC-2.5, AC-3.5; DEV-007) | `pt scripts/tests/test_agent_cli_contract.py scripts/tests/test_agent_cli_contract_doc.py` |
| The plugin copies of both scripts are current (AC-1.5, AC-2.5, AC-3.5). Line 1 is `pass` | `(cd "$REPO" && python3 scripts/gen-platform-trees.py --check)` |

The spec's success criteria name Python 3.9 and 3.14. Rerun any row on 3.14 with `PY=3.14 pt ...`.

---

## Story 1: Verification ledger

### Scenario 1: A commit added and then reverted keeps the head VERIFIED

**Source:** Edge Case ("A commit added and then reverted, with the net diff unchanged") — Story 1
**Feature:** none
**Verification:** scripted — the line 1 and exit code of `verify-ledger.py check` in Step 4 decide it

**Preconditions:**
- Setup block pasted in this shell.

**Steps:**
1. `H=$(mkrepo "$W/s1") && rec "$W/s1" 7`
2. `edit "$W/s1/app.txt" L15 "L15 extra" && g -C "$W/s1" commit -qam extra && g -C "$W/s1" revert --no-edit HEAD >/dev/null`
3. `R=$(git -C "$W/s1" rev-parse HEAD) && git -C "$W/s1" diff "$H" "$R"; echo "H=${H:0:7} R=${R:0:7}"`
4. `chk "$W/s1" 7 "$R"`

**Expected Result:**
- Step 1: `pass`, then `reason: recorded PR 7 head <H> patch-id <id>`, then `verify-ledger: pass (recorded PR 7 head <H>, 1 command(s))`.
- Step 2: prints nothing.
- Step 3: the diff prints nothing, because the reverted head has H's tree. The last line shows two different SHAs.
- Step 4: `pass`, `reason: verified_patch_id <R> matches <H>`, `verify-ledger: pass (PR 7 head <R> VERIFIED, patch-id)`, `exit 0`.

**Implementation Reference:** Story 1 — `scripts/verify-ledger.py` (patch-id over the pinned diff; DEV-001)

**Status:** [ ] Pass  [ ] Fail

**Notes:**

---

### Scenario 2: A base change inside the PR's hunk context reads NOT VERIFIED

**Source:** Edge Case ("Rebase onto a base that changed a line inside the PR's hunk context") — Story 1
**Feature:** none
**Verification:** scripted — the line 1 and exit code of `verify-ledger.py check` in Step 4 decide it

**Preconditions:**
- Setup block pasted in this shell.

**Steps:**
1. `H=$(mkrepo "$W/s2") && rec "$W/s2" 7`
2. `g -C "$W/s2" checkout -q main && edit "$W/s2/app.txt" L12 "L12 base edit" && g -C "$W/s2" commit -qam "base edit" && g -C "$W/s2" checkout -q feature && g -C "$W/s2" rebase -q main`
3. `J=$(git -C "$W/s2" rev-parse HEAD) && git -C "$W/s2" diff main feature`
4. `chk "$W/s2" 7 "$J"`

**Expected Result:**
- Step 1: `pass` with a `recorded PR 7` reason.
- Step 2: prints nothing. The rebase applies cleanly because the unchanged L11 separates the two edits.
- Step 3: one hunk with `-L10` and `+L10 changed`; ` L12 base edit` is among its context lines.
- Step 4: `fail`, `reason: patch_id_mismatch <J> patch-id <id> matches no verified row for PR 7`, `verify-ledger: fail (PR 7 head <J> NOT VERIFIED, patch_id_mismatch)`, `exit 1`. The PR's own change is the same, but its diff now carries different context, so the ledger fails closed.

**Implementation Reference:** Story 1 — `scripts/verify-ledger.py` (`-U3` context in the pinned diff)

**Status:** [ ] Pass  [ ] Fail

**Notes:**

---

### Scenario 3: Two `record` runs at once leave a valid ledger and fail closed

**Source:** Edge Case ("Two `record` runs at once") — Story 1
**Feature:** none
**Verification:** scripted — the exit codes in Step 2, the ledger parse in Step 3, and each `check`'s line 1 and exit code in Step 4 decide it

**Preconditions:**
- Setup block pasted in this shell.

**Steps:**
1. `H=$(mkrepo "$W/s3")`
2. `(rec "$W/s3" 1 > "$W/s3-a.out"; echo "a exit $?") & (rec "$W/s3" 2 > "$W/s3-b.out"; echo "b exit $?") & wait`
3. `python3 -c 'import json, sys; d = json.load(open(sys.argv[1])); print(d["schema"], sorted(r["pr"] for r in d["rows"]))' "$W/s3/.writ/state/verify-ledger.json"; ls -A "$W/s3/.writ/state"`
4. `chk "$W/s3" 1 "$H"; chk "$W/s3" 2 "$H"`

**Expected Result:**
- Step 2: `a exit 0` and `b exit 0`, in either order. The shell may also print job numbers.
- Step 3: `verify-ledger/1` followed by `[1, 2]`, `[1]`, or `[2]`. The folder holds only `verify-ledger.json`, with no `*.tmp` file left behind.
- Step 4: a PR whose row survived prints `pass`, a `verified_exact` reason, and `exit 0`. A PR whose row was lost prints `fail`, `reason: no_rows PR <n>`, and `exit 1`. Neither prints `exit 2`.
- A lost row is the trade-off the spec accepts (Technical Concerns, "Lost write under concurrency"): it reads NOT VERIFIED, so a merge asks rather than proceeds. Each of the four runs made for this plan lost one of the two rows.

**Implementation Reference:** Story 1 — `scripts/verify-ledger.py` (atomic write through `mkstemp` and `os.replace`, no lock)

**Status:** [ ] Pass  [ ] Fail

**Notes:**

---

### Scenario 4: After a PR is retargeted, the exact head stays VERIFIED and a new head is judged against the recorded base

**Source:** Edge Case ("PR retargeted to another base branch after a record") — Story 1
**Feature:** none
**Verification:** scripted — the line 1 and exit code of each `verify-ledger.py check` in Steps 3 to 5 decide it

**Preconditions:**
- Setup block pasted in this shell.

**Steps:**
1. `H=$(mkrepo "$W/s4") && rec "$W/s4" 7`
2. `g -C "$W/s4" checkout -qb release main && echo extra > "$W/s4/extra.txt" && g -C "$W/s4" add extra.txt && g -C "$W/s4" commit -qm "release only" && g -C "$W/s4" rebase -q --onto release main feature`
3. `J=$(git -C "$W/s4" rev-parse HEAD) && chk "$W/s4" 7 "$H"`
4. `chk "$W/s4" 7 "$J"`
5. `chk "$W/s4" 7 "$J" --base release`

**Expected Result:**
- Step 1: `pass` with a `recorded PR 7` reason.
- Step 2: prints nothing.
- Step 3: `pass`, `reason: verified_exact <H> (recorded <time>)`, `exit 0`.
- Step 4: `fail`, `reason: patch_id_mismatch <J> patch-id <id> matches no verified row for PR 7`, `exit 1`. With no `--base`, the ledger diffs against the row's recorded base (`main`), so J's diff also carries the release-only commit.
- Step 5: `pass`, `reason: verified_patch_id <J> matches <H>`, `verify-ledger: pass (PR 7 head <J> VERIFIED, patch-id)`, `exit 0`.

**Implementation Reference:** Story 1 — `scripts/verify-ledger.py` (base from the PR's latest row unless `--base` is given)

**Status:** [ ] Pass  [ ] Fail

**Notes:**

---

## Story 2: `pr-ready.py` snapshot and blocker classes

### Scenario 5: A thread with no `comments` key prints `by ?` instead of stopping the check

**Source:** Error Map ("Validate snapshot": missing or mistyped field), as amended by DEV-006 — Story 2
**Feature:** none
**Verification:** scripted — the reason lines and exit code of `pr-ready.py check` in Step 3 decide it

**Preconditions:**
- Setup block pasted in this shell.

**Steps:**
1. `python3 "$PRR" check --snapshot "$FX/unresolved-thread.json" --repo "$W/empty"; echo "exit $?"`
2. Write a copy of that fixture whose unresolved thread has no `comments` key:

   ```bash
   python3 - "$FX/unresolved-thread.json" "$W/no-comments.json" <<'PY'
   import json, sys
   snap = json.load(open(sys.argv[1]))
   for node in snap["threads"]["data"]["repository"]["pullRequest"]["reviewThreads"]["nodes"]:
       if not node["isResolved"]:
           del node["comments"]
   json.dump(snap, open(sys.argv[2], "w"))
   PY
   ```
3. `python3 "$PRR" check --snapshot "$W/no-comments.json" --repo "$W/empty"; echo "exit $?"`

**Expected Result:**
- Step 1 prints exactly:

  ```
  fail
  reason: unresolved_threads: PRRT_kwDOAbc123 src/app.py:14 by alice
  reason: merge_gates: not_verified head 3ddc8c8: no_rows PR 66
  pr-ready: fail (PR 66 head 3ddc8c8, blockers: unresolved_threads, merge_gates; exit 4)
  exit 4
  ```

  The `not_verified ... no_rows` line is expected: `$W/empty` holds no ledger.
- Step 3 prints the same five lines, except the thread line ends `by ?` instead of `by alice`. It does not exit 2: a missing key in the comments chain reads as null (DEV-006). A value of the wrong type there is still exit 2.

**Implementation Reference:** Story 2 — `scripts/pr-ready.py` (snapshot validation of the comments chain)

**Status:** [ ] Pass  [ ] Fail

**Notes:**

---

### Scenario 6: A rejected snapshot value prints cut to 80 characters

**Source:** Error Map ("Validate snapshot": unrecognized enum value), as amended by DEV-008 — Story 2
**Feature:** none
**Verification:** scripted — the exit code, empty stdout, and the counted length in Steps 2 and 3 decide it

**Preconditions:**
- Setup block pasted in this shell.

**Steps:**
1. Write a copy of `clean.json` whose `mergeable` value is 200 `X` characters:

   ```bash
   python3 - "$FX/clean.json" "$W/long-enum.json" <<'PY'
   import json, sys
   snap = json.load(open(sys.argv[1]))
   snap["view"]["mergeable"] = "X" * 200
   json.dump(snap, open(sys.argv[2], "w"))
   PY
   ```
2. `python3 "$PRR" check --snapshot "$W/long-enum.json" --repo "$W/empty" > "$W/long.out" 2> "$W/long.err"; echo "exit $?"; wc -c < "$W/long.out"; cat "$W/long.err"`
3. `grep -o 'X*$' "$W/long.err" | awk '{ print length }'`

**Expected Result:**
- Step 2: `exit 2`, then `0` (stdout is empty), then one stderr line: `pr-ready: snapshot <path>/long-enum.json: unrecognized view.mergeable XXXX...`.
- Step 3: `80`.

**Implementation Reference:** Story 2 — `scripts/pr-ready.py` (bounded echo of a rejected value)

**Status:** [ ] Pass  [ ] Fail

**Notes:**

---

## Story 3: Ledger gate and machine output

### Scenario 7: On a real PR, the report matches the PR page and clears `not_verified` after a record

**Source:** Experience Design (Entry point, Happy path, Feedback model, Interaction patterns) — Stories 2 and 3
**Feature:** none
**Verification:** human — it needs a live GitHub PR, a `gh` login, and a person comparing the report with the PR page. The test suite reads fixtures only, and the script makes no network call.

**Preconditions:**
- Setup block pasted in this shell.
- `gh auth status` shows you logged in.
- An open PR you can read, number `<N>` in repository `<OWNER>/<NAME>` (not a fork of another repository). One with an unresolved review conversation, or a failing or running check, gives the report something to compare.

**Steps:**
1. `gh repo clone <OWNER>/<NAME> "$W/live" -- -q && cd "$W/live" && N=<N> && gh pr checkout "$N"`
2. `python3 "$PRR" --help`. Copy the three lines after "Write it with these commands" (they start `VIEW=$(gh pr view`, `THREADS=$(gh api graphql`, and `printf`).
3. `SNAP="$W/pr-$N.json"`, then paste the three lines from Step 2 and press Return.
4. `python3 "$PRR" check --snapshot "$SNAP" --repo "$W/live"; echo "exit $?"`
5. `gh pr view "$N" --web` and compare the PR page with the output of Step 4.
6. `python3 "$VL" record --pr "$N" --head "$(git rev-parse HEAD)" --base "origin/$(gh pr view "$N" --json baseRefName -q .baseRefName)" --evidence 0 "manual UAT"`
7. Repeat Steps 3 and 4.
8. `cd "$REPO"`

**Expected Result:**
- Step 3 writes `$SNAP` with no error from `gh`.
- Step 4: the exit is 0, 3, 4, 5, or 6, never 2, so the live `gh` output is a snapshot the script accepts. Line 1 is `fail` or `unverifiable`. A reason line reads `merge_gates: not_verified head <short>: no_rows PR <N>`, because nothing is recorded yet.
- Step 5: each blocker the page shows has a matching reason line: a merge conflict as `conflicts:`, each unresolved conversation as `unresolved_threads: <id> <path>:<line> by <first commenter>`, each failed check as `failing_checks: <name> <conclusion>` (optional checks count too), a draft, requested changes, a required review, or an out-of-date branch as the matching `merge_gates:` token, and a running check as `unknown: checks_pending <name>`. No reason line names a blocker the page does not show. No review comment text appears anywhere in the output. `merge_gates: merge_state_blocked` is correct only when GitHub blocks the merge for a reason none of the other lines name, such as a branch rule.
- Step 6: `pass` and exit 0. The ledger row lives only in the scratch clone.
- Step 7: the `not_verified` line is gone. If the page showed nothing blocking, line 1 is `pass` and the last line reads `pr-ready: pass (PR <N> head <short>, ledger VERIFIED)`, exit 0.

**Implementation Reference:** Stories 2 and 3 — `scripts/pr-ready.py` (`--help` commands, blocker classes, ledger gate), `scripts/verify-ledger.py` (`record`)

**Status:** [ ] Pass  [ ] Fail

**Notes:**

---

## Pending Stories

None. All three stories are Completed ✅.
