# PR Ready and Verification Ledger

> **Status:** In Progress
> **Created:** 2026-11-06
> **Owner:** @AdamSellke
> **Dependencies:** []
> **Phase:** 16 — Verified Landing ([roadmap](../../product/roadmap.md), [ADR-033](../../decision-records/adr-033-doubt-gated-autonomy.md), [ADR-029](../../decision-records/adr-029-agent-cli-contract.md))
> **Origin:** Phase 16 decomposition, features 1 (`pr-ready.py`) and 2 (Verification ledger). Research F2 ([pstack comparison](../../research/2026-10-19-writ-vs-pstack-research.md)): pstack's `watch-pr` reports typed blockers with distinct exit codes, and its ledger is keyed by (PR, SHA). ADR-013's dormant design binds approval to the reviewed head SHA.
> **Depended on by:** `2026-11-06-ship-watch-and-merge` (`/ship --watch` and the ADR-033 merge rule)

## Specification Contract

Locked by the maintainer on 2026-11-06 as drafted, with the recommended answers to both open questions (doubt log `e92baa518105`). The reconciled seams with the sibling spec are binding and are recorded under § Locked Answers and Reconciliation.

**Deliverable:** Two check-shape scripts. `scripts/pr-ready.py` (read-only) judges a saved `gh` snapshot of one PR and reports typed blockers with one exit code per class. `scripts/verify-ledger.py` records which PR heads passed the project's test and eval commands and answers whether a given head is VERIFIED, matching by exact SHA or by patch-id within the same PR.

**Must Include:**
1. `pr-ready.py check --snapshot <file> [--repo .]` in the ADR-029 check shape. Four blocker classes, each with its own exit code: conflicts (3), unresolved threads (4), failing checks (5), merge gates (6). All blockers print. The exit code is the first class in that order.
2. A snapshot schema and the exact `gh` commands that produce it, printed by `pr-ready.py --help`, so `/ship` can cite them.
3. `verify-ledger.py record` and `check`. The ledger is a plain JSON file with one writer and atomic writes. A head reads VERIFIED only by exact SHA or by a whitespace-, mode-, and binary-sensitive patch-id equal to a verified head of the same PR.
4. A mutation test: each one-property change to a verified head (one byte, whitespace only, mode only, binary only, different PR) reads NOT VERIFIED, and a rebase that leaves the diff unchanged reads VERIFIED.
5. Contract registration: two Classification rows, a documented exit-code exception in `.writ/docs/agent-cli-contract.md`, an ADR-029 amendment note, contract-test smokes, and regenerated plugin copies.

**Hardest Constraint:** The ledger must separate a head whose behavior could differ from a verified head from a head that only moved its base. `git patch-id --stable` cannot do this: it strips whitespace, so a Python re-indent keeps the verified id (probe in technical-spec § Probes). The ledger needs `git patch-id --verbatim` over a `git diff` with every output-affecting option pinned, and it must fail closed whenever it cannot compute an id: old Git, a head or base missing locally, or an empty diff.

**🎯 Experience Design:**
- **Entry point:** No new command. `/ship --watch` (second spec) calls both scripts by path. A person can run them by hand.
- **Happy path:**
  1. Tests and eval pass on the checked-out head. The caller runs `verify-ledger.py record --pr 66 --head <sha> --base origin/main --evidence 0 "<test cmd>" --evidence 0 "<eval cmd>"`.
  2. The caller writes a snapshot with the documented `gh` commands and runs `pr-ready.py check --snapshot <file>`.
  3. Line 1 is `pass`, and the exit code is 0.
- **Moment of truth:** `pr-ready: pass (PR 66 head 3ddc8c8, ledger VERIFIED)`.
- **Feedback model:** one `reason:` line per blocker or unknown, in class order, for example `reason: unresolved_threads: PRRT_kw src/app.py:14 by alice` or `reason: merge_gates: not_verified head 9f1e2a7: patch-id 1a2b3c4 matches no verified row for PR 66`.
- **Error experience:**
  - A new head is pushed after verification and its diff changed: `fail`, `merge_gates: not_verified`, exit 6.
  - Checks still running: `unverifiable` with `reason: unknown: checks_pending ci/test`, exit 0. The harness loop calls again later.
  - A bad snapshot (missing file, not JSON, a GraphQL `errors` key, wrong schema): exit 2, stdout empty, cause on stderr after `pr-ready: `.
  - `record` with a non-zero evidence exit, a different checked-out HEAD, or tracked changes: `fail`, exit 1, nothing written.

**📋 Business Rules:**
1. `pr-ready.py` reads only the snapshot file, the ledger file, and local git. It makes no network call, writes nothing, and never sleeps or loops (ADR-029 rules 2 and 6).
2. Verdict: `fail` when at least one blocker holds. `unverifiable` when no blocker holds and at least one unknown does. `pass` only when neither holds and the ledger reads VERIFIED for the snapshot's head.
3. Exit codes: 0 for `pass` or `unverifiable`. 2 for a usage error or a snapshot that cannot be judged. 3 conflicts, 4 unresolved threads, 5 failing checks, 6 merge gates. The tool never exits 1 on purpose, so exit 1 means a crash.
4. Every blocker prints, in class order, then every unknown. The exit code is the first class present.
5. A failing check blocks whether or not it is required. `gh pr view` does not say which checks are required, and ADR-033 point 5 says "never looser without evidence".
6. "Changes requested" and "review required" are merge gates read from the snapshot. They are never ledger state.
7. `pr-ready.py` never reads or prints review-comment bodies. A thread prints as its id, `path:line`, the first author's login, and an `outdated` flag. Control characters in any printed field are escaped.
8. A ledger row exists only for a head whose evidence commands all exited 0. `record` refuses when `--head` is not the checked-out `HEAD` or when tracked files are modified or staged.
9. `check` reads VERIFIED when a row for the same PR has the same head, or has a non-null patch-id equal to the head's patch-id. Patch-ids never match across PRs. Anything else reads NOT VERIFIED, including every case where the id cannot be computed.
10. Recording the same (PR, head) again replaces that row. The ledger has one writer (`verify-ledger.py record`) and writes atomically.

**Success Criteria:**
- Fixture snapshots cover each blocker, each unknown, all four classes at once, and each exit-2 case. Each run prints the expected line 1, reason lines, and exit code.
- The mutation test passes on Python 3.9 and 3.14: each single-property mutation of a verified head reads NOT VERIFIED with the expected reason, and the identical-diff rebase reads VERIFIED.
- The same snapshot with only `headRefOid` changed to an unverified commit flips `pr-ready.py` from exit 0 to exit 6.
- `test_agent_cli_contract.py`, `test_agent_cli_contract_doc.py`, and `eval.sh --check=platform-trees` pass with both scripts shipped.

**Scope Boundaries:**
- Included: `pr-ready.py`, `verify-ledger.py`, the snapshot schema and `gh` commands, the ledger file format, tests and fixtures, contract rows and exception, the ADR-029 note, and plugin copies.
- Excluded: fetching from GitHub, `/ship --watch` and its loop, CI retry and flake handling, thread replies, the merge itself, `jev-judge.py`'s `merge` rule, ledger pruning, sharing the ledger across clones or worktrees, required-check filtering, and paginating beyond 100 threads.

**⚠️ Technical Concerns:**
- **Whitespace blindness.** `--stable` treats a whitespace-only change as identical (probe). *Mitigation:* use `git patch-id --verbatim`. Older Git lacks the flag. The script feature-detects it (`git patch-id --verbatim </dev/null` exits 0 when supported) and stores `patch_id: null` when it cannot. A null row matches only its exact head.
- **User diff config changes the id.** `diff.noprefix=true` changed the id (probe). *Mitigation:* pin `git diff --no-color --no-ext-diff --no-textconv --binary --full-index --no-renames --src-prefix=a/ --dst-prefix=b/ --diff-algorithm=myers -U3 --no-relative`. A test sets hostile config (`diff.noprefix`, `diff.algorithm=patience`, `diff.renames=copies`) and asserts the same id.
- **Patch-id equality is not tree equality.** A rebase onto a moved base keeps the id (probe), but the tests ran against the old base. This is the roadmap's intended rule (and pstack's "a verdict follows the patch"). *Mitigation:* `failing_checks` still judges CI on the new head, and `behind` and `merge_state_blocked` still apply.
- **Two `gh` calls can see two heads.** *Mitigation:* the threads query also returns `headRefOid` and `number`. A mismatch is `unknown: head_moved`, so the result is `unverifiable` unless a blocker already holds.
- **Head not fetched locally.** The snapshot's head may not exist in the clone. *Mitigation:* an exact-SHA match needs no git. Otherwise the result is NOT VERIFIED with `head_unavailable`. The caller fetches first (second spec).
- **Per-checkout ledger.** `<repo>/.writ/state/verify-ledger.json` is per clone and per worktree, so a record made in a lane worktree is invisible from the primary checkout. That fails closed: the merge asks. Record and check from the checkout `/ship` runs in.
- **Lost write under concurrency.** Two `record` runs at once can drop a row (read, modify, replace). The result is NOT VERIFIED, which fails closed. No lock file.
- **Evidence is self-reported.** `record` checks exit codes, HEAD, and tracked changes, but it does not run the commands or decide which commands count. The row keeps the commands for audit (ADR-033 "accountability by record").
- **Check truncation.** `gh pr view` may cap `statusCheckRollup`, and the output does not show it. Thread truncation is detected (`pageInfo.hasNextPage`). Check truncation is accepted.
- **Roadmap gate.** As of the 2026-11-05 status line, Phase 12 is not closed (Scenario 26 issue, no real-project `app-verify.py` run). Whether to proceed is the orchestrator's call. Neither script depends on Phase 12 output.

**💡 Recommendations:**
- `pr-ready.py` loads `verify-ledger.py` by path with the `exit-criteria.py` `_load_sibling` pattern and calls one function, `ledger_check(repo, pr, head, base=None) -> (verdict, reasons)`. One implementation, and both files ship together in `scripts/` and `plugins/writ/scripts/`.
- A ledger read error inside `pr-ready.py` becomes `merge_gates: not_verified ledger_unreadable (<detail>)`, not exit 2, so the other blockers still print. `verify-ledger.py check` alone exits 2 for an unreadable ledger.
- `--json` on `pr-ready.py check` replaces the verdict lines with one JSON object and keeps the exit code. This matches `check_shape`'s `--json` branch, where all of stdout must be one JSON value. The second spec can read this object or line 1 plus the exit code.
- Keep the full CLI, snapshot schema, `gh` commands, and ledger format in each script's module docstring (house style). Do not add a `.writ/docs/` format doc.
- The default contract smoke for `pr-ready.py` uses a draft-PR fixture. It exits 6 before and after the ledger gate lands, so the exit-code exception is exercised from the first story.

**⚠️ Cross-Spec Overlap:**
- `2026-10-25-gate-upgrade-removal-measurement` (In Progress) also writes under gitignored `.writ/state/` (its `gate-upgrade-trial/` folder) and loads a shipped script by path. Different files, no conflict. Advisory only.
- `2026-11-06-ship-watch-and-merge` consumes S1-S5. It owns `commands/ship.md`, `commands/_preamble.md`, `scripts/jev-judge.py`, `.writ/docs/recommendation-semantics.md`, and the roadmap. One shared file: it updates the Callers cells of the two new rows in `.writ/docs/agent-cli-contract.md` when `ship.md` starts calling the scripts. It depends on this spec.
- No `conflict: true`.

### Locked Answers and Reconciliation

- **A-OQ1, Callers cells.** This spec writes both Callers cells as `none shipped yet; /ship --watch (spec 2026-11-06-ship-watch-and-merge)`. The second spec replaces them with `commands/ship.md` (and `scripts/jev-judge.py` for `pr-ready.py`) in the story that adds the calls. It edits nothing else in that doc.
- **A-OQ2, required evidence.** `record` takes no `--require` set in this phase. It records the commands it is given.
- **`--json` head.** `pr-ready.py check --json` carries the full 40-hex `head`. The text summary keeps the short head.
- **The second spec parses the JSON.** `jev-judge.py doubt` (site `merge`) runs `pr-ready.py check --snapshot <snapshot> --repo <repo> --json` and reads `pr`, `head`, `verdict`, `blockers[].class`, and `blockers[].detail`. A `merge_gates` blocker whose detail starts with `not_verified` maps to its `merge_not_verified` reason. So every `merge_gates` detail starts with its gate token, in text and in JSON. `/ship` branches on the first `reason:` class and gate token, not on exit numbers.
- **Snapshot path.** The second spec writes snapshots at `.writ/state/pr-ready/pr-<n>.json`.
- **Roadmap gate.** Phase 12 is not closed. The maintainer directed the build anyway on 2026-11-06. The orchestrator records this in the roadmap at phase close. This spec does not edit the roadmap.

## Experience Design

### Who uses it

- **The `/ship --watch` loop (second spec).** After tests and eval pass on the checked-out head, it runs `verify-ledger.py record`. On each pass of its loop it writes a snapshot with the `gh` commands from `pr-ready.py --help`, runs `pr-ready.py check --json`, and acts on the first blocker class.
- **`jev-judge.py doubt` at site `merge` (second spec).** It runs `pr-ready.py check --json` and merges only on `pass`.
- **A developer.** They run either script by hand to see why a PR is not ready, or whether a head was verified.

### Journey

1. Tests and eval pass on the checked-out head of PR 66. `verify-ledger.py record --pr 66 --head <sha> --base origin/main --evidence 0 "<test>" --evidence 0 "<eval>"` prints `pass` and writes one row.
2. The caller writes `.writ/state/pr-ready/pr-66.json` with the S1 commands.
3. `pr-ready.py check --snapshot .writ/state/pr-ready/pr-66.json` reads the snapshot, loads `verify-ledger.py` beside it, and asks the ledger about the snapshot's head.
4. It prints line 1, every blocker and unknown, and a summary, and exits with the code of the first blocker class, or 0.
5. A reviewer pushes a fix. The new head's diff differs, so its patch-id differs. The next `check` prints `merge_gates: not_verified ...` and exits 6 until tests run and `record` writes a row for the new head.

### State Catalog

| State | `pr-ready.py` line 1 | Exit | Reason lines |
|---|---|---|---|
| Ready: no blocker, no unknown, ledger VERIFIED | `pass` | 0 | none |
| Checks still running, nothing else wrong | `unverifiable` | 0 | `unknown: checks_pending <names>` |
| GitHub still computing mergeability | `unverifiable` | 0 | `unknown: mergeable_unknown` |
| Merge conflict | `fail` | 3 | `conflicts: ...` |
| Open review thread | `fail` | 4 | one `unresolved_threads:` line per thread |
| Failing check | `fail` | 5 | one `failing_checks:` line per check |
| New head, not verified | `fail` | 6 | `merge_gates: not_verified ...` |
| Draft PR | `fail` | 6 | `merge_gates: draft` |
| Several at once | `fail` | first class present | all of them, class order, then unknowns |
| Snapshot missing, not JSON, wrong schema, GraphQL errors | none (stdout empty) | 2 | cause on stderr |
| Ledger file unreadable | `fail` | per class order | `merge_gates: not_verified ledger_unreadable (...)` |

| State | `verify-ledger.py` line 1 | Exit | Reason |
|---|---|---|---|
| `record` accepted | `pass` | 0 | `recorded PR <n> head <short> patch-id <short\|null>` |
| `record` refused | `fail` | 1 | `evidence_failed`, `head_not_checked_out`, `dirty_tree` |
| `check`, exact head | `pass` | 0 | `verified_exact ...` |
| `check`, same-PR patch-id | `pass` | 0 | `verified_patch_id ...` |
| `check`, no row for the PR | `fail` | 1 | `no_rows ...` |
| `check`, id differs or cannot be computed | `fail` | 1 | `patch_id_mismatch`, `head_unavailable`, `base_unavailable`, `patch_id_unavailable` |
| Ledger file malformed | none (stdout empty) | 2 | cause on stderr |

### Interaction patterns

- Line 1 decides. Callers branch on line 1, then on the first `reason:` class and gate token. Exit numbers are a second signal (Business Rule 3).
- Reason lines name things a person can act on: a thread id and `path:line`, a check name and its conclusion, a gate token.
- Nothing the PR's authors or reviewers wrote reaches stdout except identifiers: thread ids, paths, logins, check names. All are escaped.

## Business Rules (Expanded)

### Verdict and exit code

1. Blockers come from four classes in fixed order: `conflicts`, `unresolved_threads`, `failing_checks`, `merge_gates`.
2. `fail` if any blocker holds. Otherwise `unverifiable` if any unknown holds. Otherwise `pass`. A `pass` needs the ledger gate to be clear. That gate lands in Story 3.
3. On `fail`, the exit code is that of the first class present: 3, 4, 5, or 6. On `pass` or `unverifiable`, it is 0. A snapshot that cannot be judged, a usage error, or a missing sibling `verify-ledger.py` exits 2 with stdout empty.
4. Reason lines print all blockers in class order, then all unknowns. Within a class, lines keep snapshot order.

### Blocker classes

- **conflicts:** `mergeable == CONFLICTING` or `mergeStateStatus == DIRTY`. One line.
- **unresolved_threads:** each thread with `isResolved == false`, outdated or not. One line per thread.
- **failing_checks:** each `CheckRun` that is `COMPLETED` with a conclusion other than `SUCCESS`, `NEUTRAL`, or `SKIPPED`, and each `StatusContext` in `FAILURE` or `ERROR`. One line per check. Required and optional checks count alike.
- **merge_gates:** see below. One line per gate. Each detail starts with its gate token.

### Merge gates

| Gate token | Holds when |
|---|---|
| `not_verified` | The ledger does not read VERIFIED for the snapshot's PR and `headRefOid` (Story 3) |
| `draft` | `isDraft` is true, or `mergeStateStatus == DRAFT` |
| `changes_requested` | `reviewDecision == CHANGES_REQUESTED` |
| `review_required` | `reviewDecision == REVIEW_REQUIRED` |
| `not_open` | `state` is not `OPEN`; the detail names the state |
| `behind` | `mergeStateStatus == BEHIND` |
| `merge_state_blocked` | `mergeStateStatus == BLOCKED`, and no other blocker except `not_verified` holds, and no check is pending |

`not_verified` never explains a GitHub `BLOCKED` state: the ledger is Writ's record, not GitHub's.

### Unknowns

| Code | Holds when |
|---|---|
| `mergeable_unknown` | `mergeable` or `mergeStateStatus` is `UNKNOWN` |
| `checks_pending` | a `CheckRun` is not `COMPLETED`, or a `StatusContext` is `PENDING` or `EXPECTED` |
| `threads_truncated` | `reviewThreads.pageInfo.hasNextPage` is true |
| `head_moved` | `view.headRefOid` differs from the threads query's `headRefOid` |
| `merge_state_unexplained` | `mergeStateStatus == UNSTABLE` and no check is failing or pending |

### Snapshot validity (exit 2)

The snapshot cannot be judged when the file is missing or unreadable, or is not JSON. It also cannot be judged when:
- `schema` is not `pr-ready-snapshot/1`, or `view` or `threads` is missing or not an object
- `threads` has an `errors` key
- a required field is missing or has the wrong type, or `headRefOid` is not 40 lowercase hex
- an enum field holds a value outside the technical spec's tables (`mergeable`, `mergeStateStatus`, `reviewDecision`, `state`, a check `__typename`, `status`, `conclusion`, or `state`)
- `view.number` differs from the threads `number`

### Ledger record

- Write only when all hold: every `--evidence` exit is 0, `--head` resolves to the checked-out `HEAD`, and `git status --porcelain --untracked-files=no` is empty. Otherwise print `fail`, print every refusal reason that holds, exit 1, and leave the file as it was.
- An unresolvable `--head` or `--base`, a non-integer evidence exit, an empty command, `--pr` below 1, or a `--repo` that is not a git work tree is a usage error: exit 2.
- The row stores the patch-id, or `null` with a printed `patch_id_unavailable (<why>)` reason when `--verbatim` is unsupported, the diff is empty, or there is no merge base.
- The same (PR, head) replaces its row in place. Other rows are untouched.

### Ledger check

1. No row for the PR: `fail no_rows`.
2. A row with the same head: `pass verified_exact`. No git call is needed when `--head` is full hex.
3. Otherwise compute the head's patch-id against `--base`, or against the `base_ref` of the PR's most recent row (latest `recorded_at`). An unresolvable head or base, or an id that cannot be computed, is `fail` with `head_unavailable`, `base_unavailable`, or `patch_id_unavailable`.
4. A non-null row of the same PR with an equal id: `pass verified_patch_id`. Otherwise `fail patch_id_mismatch`.

### Untrusted content

Comment bodies are never requested by the S1 query, never read, and never printed, even when a hostile snapshot includes them. Every printed snapshot string is escaped with `repro-order.py`'s `printable` pattern, so each `reason:` line stays one line.

### State file

`<repo>/.writ/state/verify-ledger.json` is the only state. `verify-ledger.py record` is its only writer. It writes via `tempfile.mkstemp` in the same directory and `os.replace`. `.writ/state/` is gitignored in this repo and in installed projects.

## Detailed Requirements

### Story 1: Verification ledger

`scripts/verify-ledger.py` with `record` and `check`, the ledger file, the pinned patch-id recipe, and the public `ledger_check()` function. `scripts/tests/test_verify_ledger.py` builds temp git repos and carries the mutation test. Story 1 also registers the script: its Classification row and Notes entry, a contract smoke, and the plugin copy.

### Story 2: `pr-ready.py` snapshot and blocker classes

`scripts/pr-ready.py check --snapshot <file> [--repo .]` validates the S1 snapshot and judges the four classes and the unknowns. `merge_gates` here holds every gate except `not_verified`. `--help` prints the `gh` commands. Fixtures live under `scripts/tests/fixtures/pr-ready/`. Story 2 registers the script: its row and Notes entry, the Check-shape sentence for the exit-code exception, the ADR-029 amendment, the `FAIL_EXITS` exception in `test_agent_cli_contract.py`, the `draft.json` smoke, and the plugin copy.

### Story 3: Ledger gate and machine output

`pr-ready.py` loads `verify-ledger.py` from its own directory and adds the `not_verified` gate. A clean snapshot then passes only when the ledger reads VERIFIED for its head. `--json` prints one object. Story 3 updates Story 2's clean-fixture tests to supply a ledger row and extends the `pr-ready.py` Notes entry with `--json`.

## Implementation Approach

- **Tests first.** Each story writes its pytest file before the script. Test docstrings name `2026-11-06-pr-ready-and-ledger` and the story above the AC tags (`.writ/docs/acceptance-criteria-ids.md` → Scan Bounds).
- **House patterns.** Copy `repro-order.py`'s `_git`, `_resolve`, `UsageError`, and `printable`. Copy `exit-criteria.py`'s `_load_sibling`. Copy `phase-state.py`'s atomic write. Copy patterns, not imports: each script stands alone (agent-cli-contract § Runtime).
- **Bytes, not text, for diffs.** Binary diffs are not UTF-8. Pass the `git diff` stdout to `git patch-id --verbatim` as bytes.
- **Temp repos only.** No test runs either script against the Writ working tree's `.writ/state/`. Every test builds its own repo under `tmp_path` with `git -c user.name=t -c user.email=t@example.com -c commit.gpgsign=false`.
- **Regenerate, never hand-edit.** After a new or changed script, run `python3 scripts/gen-platform-trees.py` and commit `plugins/writ/scripts/` in the same story.
- **Python 3.9 floor.** `from __future__ import annotations`. No `match`, no runtime `X | Y`, no 3.10+ stdlib behavior. Stdlib only.
- **Order.** Story 1, then Story 2, then Story 3. Stories 1 and 2 both edit `.writ/docs/agent-cli-contract.md`, `scripts/tests/test_agent_cli_contract.py`, and `plugins/writ/scripts/`, so they do not run in parallel.

Full CLI, schemas, tables, error map, and test plan: [`sub-specs/technical-spec.md`](sub-specs/technical-spec.md).
