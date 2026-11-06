# Technical Spec: Ship Watch and Merge

> Spec: [`../spec.md`](../spec.md) · Stories: [`../user-stories/README.md`](../user-stories/README.md)

## Current State (2026-11-06, `3ddc8c8`)

| Fact | Where |
|---|---|
| `commands/ship.md` is 644 lines and 28,907 bytes. It stops at an opened PR (line 637). | `commands/ship.md` |
| Asks on the open path: "Override?" (line 120), "Save to `.writ/config.md`?" (line 75), "Ask user" fallbacks (lines 79-80), test-failure options (187-195), commit-plan `AskQuestion` (264-279), branch creation (551-558), uncommitted changes (583-592), combined case (598-606). | `commands/ship.md` |
| `DOUBT_ALWAYS_ASK = {"merge": "no_verification_ledger", "release": "outward"}` (line 1862). `DOUBT_FALLBACK_ASK = ("direction", "design")` (line 1860). `doubt_rule(rec)` (line 1947) has one caller, `doubt()` (line 2043). `--help` says "merge and release always ask" (line 43). | `scripts/jev-judge.py` |
| `({"site": "merge"}, "no_verification_ledger")` is a parametrized row of `test_rules_ask_without_calling_jev`. Helpers: `_repo`, `_record`, `Fake`, `_run`, `_log_rows`, `_calibrated`, `ENABLED`. | `scripts/tests/test_jev_doubt.py:106` |
| Doubt Rule table row `` | `merge`, `release` (tag, publish, deploy) | Always | ``. 73 lines; the eval cap is 95. | `commands/_preamble.md:49` |
| "How the check decides" step 1 and step 4 state the always-ask rule and the fallback sites. | `.writ/docs/recommendation-semantics.md:58,61` |
| "Merging, releasing, tagging, and publishing wait for a person's answer." / "it never becomes an unattended loop." Both lines date from 2026-11-05, after the pruned-base pin `cf84742`. | `system-instructions.md:38-45` |
| Pins: `"Release stays a person's call"` (message says merge) and `"it never"` (message says unattended loop). `require_literal` is a one-line `grep -F`. | `scripts/eval.sh:1081,1085` |
| "Merge, release, tag, and publish always wait for you." | `README.md:66` |
| `LOOP_BEARING_COMMANDS` holds five commands; the docstring says the list is fixed at five. The leanness fallback copies it. | `scripts/eval-loop-bounds.py:72`, `scripts/eval-leanness.py:760` |
| `KNOWN_OVER_BUDGET["commands/ship.md"] = 3947`, the exact overage over `COMMAND_BYTE_BUDGET = 24960`. `total_overage == sum(KNOWN_OVER_BUDGET.values())` is asserted exactly (line 798). | `scripts/tests/test_governor_enforcement.py:654` |
| `SHIP_KEPT_FRONTMATTER` pins `problem`, `outcome`, `exit_criteria` byte for byte. `MERGE_CLAIMS` forbids "merged pr", "branch to merged", "gets it merged" in the description and Overview. `recorded[SHIP] == size - 24960`. The comment line `# 2026-10-20 (2026-10-20-harness-cuts Story 3): 4030 -> 4023;` must stay in the contiguous comment block above the entry. | `scripts/tests/test_harness_cuts.py:397-411, 568-631` |
| Step 6 literals pinned: `refs/notes/writ`, `writ.auditNotes`, `refs/notes/origin-writ`, `git push origin refs/notes/writ`, `git notes --ref=writ add -f -F`, "non-blocking", "landed", "squash", "minimal digest", `refs/notes/commits`. | `scripts/eval.sh:3184-3191`, `scripts/eval-git-notes-audit.py:57-77` |
| `ROWS` kinds: `heading`, `frontmatter`, `invocation` (script path plus subcommand), `lead`. New rows use `was = "check_command_structure"`. | `scripts/eval-command-structure.py:54` |
| A neutral capability needs a row in each adapter's tool table; the vendor scan skips backticked tokens that start with `/`. | `scripts/gen-platform-trees.py` (`HEADINGS`, `vendor_hits`) |

## Seams Consumed

From the locked seam sheet. Contract A owns these; this spec reads them.

| Seam | Interface this spec uses |
|---|---|
| Snapshot | Commands printed verbatim by `python3 scripts/pr-ready.py --help`, run with `N=<pr>` and `SNAP=.writ/state/pr-ready/pr-<n>.json`. Schema `pr-ready-snapshot/1`: `{"schema", "view", "threads"}`. `view` holds `number`, `state`, `isDraft`, `mergeable`, `mergeStateStatus`, `reviewDecision`, `headRefOid`, `baseRefName`, `statusCheckRollup[]` (with `detailsUrl`). No comment bodies. |
| `pr-ready.py` | `check --snapshot <file> [--repo .] [--json]`. Text: line 1 verdict, `reason: <class>: <detail>` per blocker in class order, `reason: unknown: <code> [detail]` per unknown, summary last (`pr-ready: pass (PR <n> head <short>, ledger VERIFIED)`). `--json`: `{verdict, exit, pr, head (40-hex), blockers[{class, detail}], unknowns[{code, detail}], ledger}`. Exit 0 pass or unverifiable, 2 usage or bad snapshot, 3 conflicts, 4 unresolved_threads, 5 failing_checks, 6 merge_gates; 1 is a crash. |
| Merge gates | `not_verified <ledger reason>`, `draft`, `changes_requested`, `review_required`, `not_open <STATE>`, `behind`, `merge_state_blocked`. Unknowns: `mergeable_unknown`, `checks_pending`, `threads_truncated`, `head_moved`, `merge_state_unexplained`. |
| `verify-ledger.py` | `record --pr N --head SHA --base REF --evidence EXIT CMD [--evidence EXIT CMD ...] [--repo .]` writes only when every exit is 0, `--head` is the checked-out HEAD, and no tracked file is modified; otherwise `fail`, exit 1, nothing written. `check --pr N --head SHA [--base REF]`: VERIFIED `pass` exit 0, NOT VERIFIED `fail` exit 1, 2 usage. Ledger file `<repo>/.writ/state/verify-ledger.json`. |

## `/ship` State Files

All under `.writ/state/ship/`. `/ship` is the only writer. Write each file to `<name>.tmp`, then `mv` it over the target. `<slug>` is the branch name with `/` replaced by `-`.

| File | Written by | Content |
|---|---|---|
| `branch-<slug>.json` | Steps 3, 4, 5 | `{"schema": "ship-branch/1", "branch", "presplit_sha" (40-hex or null), "evidence": {"head", "tree", "commands": [{"command", "exit"}]} or null, "draft_reason": null, "tests_failed", "drift", or "flag"}` |
| `watch-pr-<n>.json` | Step 7 | `{"schema": "ship-watch/1", "pr", "branch", "passes", "max_passes": 24, "fix_commits", "reruns": {"<check>@<head>": 1}, "replied": [<thread id>], "pre_merge_base" (40-hex or null), "last": {"state", "detail", "head"}, "halt": null or {"unit": "watch_pass", "bound": 24, "count", "last_state", "last_detail", "resume": "/ship --watch"}}` |
| `threads-pr-<n>.json` | Step 7 thread action | stdout of the thread-comments query |
| `reply-pr-<n>.json` | Step 7 thread action | one GraphQL request body (below) |
| `run-<id>.log` | Step 7 CI action | `gh run view <id> --log-failed` output |
| `merge-record-pr-<n>.json` | Step 7 merge | the doubt record (below) |

The snapshot itself lives at `.writ/state/pr-ready/pr-<n>.json` (seam sheet).

## `jev-judge.py` Merge Rule (Story 1)

**Constants**

```python
DOUBT_FALLBACK_ASK = ("direction", "design", "merge")
DOUBT_ALWAYS_ASK = {"release": "outward"}
SCRIPTS_DIR = Path(__file__).resolve().parent   # tests monkeypatch this
PR_READY = "pr-ready.py"
MERGE_CHECK_TIMEOUT = 120  # seconds
HEAD_SHA = re.compile(r"^[0-9a-fA-F]{40}$")
```

**Record fields.** `DoubtRecord` gains `pr: Optional[int]`, `head_sha: str` (`""` when absent), `snapshot: str` (`""` when absent). `parse_doubt_record` accepts them on any site. A present field of the wrong type is a `UsageError` (exit 2): `pr` must be an `int` greater than 0 and not a `bool`; `head_sha` must match `HEAD_SHA`; `snapshot` must be a non-empty string.

**`merge_rule(rec, repo) -> Tuple[Optional[str], List[str]]`**, called by `doubt()` before `doubt_rule(rec)` when `rec.site == "merge"`. A non-None reason sets `act, source, reason = False, "rules", <reason>` and appends the info list.

1. `rec.pr is None` or `not rec.head_sha` or `not rec.snapshot` → `("no_verification_ledger", [])`.
2. `script = SCRIPTS_DIR / PR_READY`. Not a file → `("merge_unverifiable", ["pr_ready_missing"])`.
3. `snapshot = Path(rec.snapshot)`; when relative, resolve against `repo`.
4. `subprocess.run([sys.executable, str(script), "check", "--snapshot", str(snapshot), "--repo", str(repo), "--json"], cwd=str(repo), capture_output=True, text=True, timeout=MERGE_CHECK_TIMEOUT, check=False)`.
   - `TimeoutExpired` → `("merge_unverifiable", ["pr_ready_timeout"])`. `OSError` → `("merge_unverifiable", ["pr_ready_not_run"])`.
   - Return code not in `(0, 3, 4, 5, 6)` → `("merge_unverifiable", ["pr_ready_exit_<code>"])`.
   - stdout not one JSON object with `verdict` (str), `pr` (int), `head` (str), `blockers` (list), `unknowns` (list) → `("merge_unverifiable", ["pr_ready_unparseable"])`.
5. `data["pr"] != rec.pr` or `data["head"].lower() != rec.head_sha.lower()` → `("merge_head_mismatch", [])`.
6. Any blocker with `class == "merge_gates"` and `detail.startswith("not_verified")` → `("merge_not_verified", [])`.
7. `data["verdict"] != "pass"` → `("merge_not_ready", ["pr_ready_" + <first blocker class, else first unknown code, else verdict>])`.
8. Otherwise `(None, [])`. Then `doubt_rule(rec)` runs the generic rules, then Jev, then the threshold or the fallback (`fallback_merge`).

**Log row.** A merge row adds `"pr"` and `"head_sha"`. Other rows do not change.

**`--help`.** Replace "Rules first, no network: merge and release always ask;" with: "Rules first, no network: release always asks; merge asks unless `pr-ready.py check --json`, run locally on the record's snapshot, passes for the record's pr and head_sha (its pass needs the ledger to read VERIFIED);". Add `pr`, `head_sha`, and `snapshot` to the `--record` help string.

**Test stub.** Tests write `pr-ready.py` into a temp dir and `monkeypatch.setattr(jev, "SCRIPTS_DIR", that_dir)`. The stub prints the contents of the file named by `PR_READY_STUB_OUT`, exits with `PR_READY_STUB_EXIT` (default 0), and sleeps `PR_READY_STUB_SLEEP` seconds first when set (with `MERGE_CHECK_TIMEOUT` monkeypatched to 1 for the timeout case).

**Real-script fixture.** A temp git repo: `main` with one file; branch `feat` with a one-line change (head A); `git -c user.name=t -c user.email=t@t commit` for every commit. `python3 <REPO_ROOT>/scripts/verify-ledger.py record --pr 7 --head A --base main --evidence 0 true --repo <tmp>`. A snapshot with `view` = `{number: 7, url, state: OPEN, isDraft: false, mergeable: MERGEABLE, mergeStateStatus: CLEAN, reviewDecision: APPROVED, headRefOid: <head>, baseRefName: main, statusCheckRollup: [{__typename: CheckRun, name: ci, status: COMPLETED, conclusion: SUCCESS}]}` and `threads.data.repository.pullRequest` = `{number: 7, headRefOid: <head>, reviewThreads: {totalCount: 0, pageInfo: {hasNextPage: false}, nodes: []}}`. `SCRIPTS_DIR` stays the real `scripts/`.
- New head: commit B changes the line again. Snapshot and record name B → `merge_not_verified`, `Fake.calls == 0`.
- Rebase: commit an unrelated file on `main`, `git rebase main` on `feat` (head A'). Snapshot and record name A' → the rules pass and Jev is called once.

## `ship.md` Changes by Story

### Story 2: open path

| Section | Change |
|---|---|
| Overview | Drop the "How `/ship` absorbs the PR agent concept" paragraph. |
| Pipeline | Replace the ASCII diagram with: `detect conventions → merge the default branch → (--test) run tests and eval → organize commits → open the PR → (--test) record the ledger row`. |
| Step 1 | Drop item 3 ("Offer to persist"), "Detection chain details", "Opinionated defaults", and the "Override?" prompt. Print the detected values and the `.writ/config.md` lines that would skip detection next time; write nothing. A needed convention that cannot be detected (default branch; Test Runner with `--test`) runs the Doubt Rule with no recommendation, so it asks. |
| Step 3 | With `--test`: run the Test Runner, then the `Eval Command` when `.writ/config.md` sets one. Save each command, its exit code, HEAD, and `git rev-parse HEAD^{tree}` to `branch-<slug>.json` → `evidence`. On failure, write a `site: choice` record (options: "Fix and retry", "Ship as a draft PR with the tests-failing label", "Abort"; recommended "Fix and retry" when the failures name files in the diff, "Ship as a draft PR with the tests-failing label" after one fix pass) and run the Doubt Rule. "Ship as a draft" sets `draft_reason: "tests_failed"`. |
| Step 4 | Save `presplit_sha = git rev-parse HEAD` to `branch-<slug>.json` first. Print the plan. Write a `site: plan` record: options "Split as planned", "Ship as a single commit"; `reversible` true only when the branch has no upstream or `git log origin/<branch>..HEAD` lists every commit the plan restructures, and `presplit_sha` is saved. `pass` executes the plan. Otherwise ask the existing three-option question and label the answer. Drop the `AskQuestion` block, "Do not restructure git history without explicit approval", and the non-extraction note. |
| Step 5 | After `gh pr create`, with `--test`: when every saved exit is 0 and `git rev-parse HEAD^{tree}` equals the saved tree, run `python3 scripts/verify-ledger.py record --pr <n> --head "$(git rev-parse HEAD)" --base origin/<default-branch> --evidence <exit> "<command>"` (one `--evidence` per saved command). When the trees differ, re-run the commands on HEAD, save, then record. When any exit is non-zero, do not record. Print the `verify-ledger:` summary line in the completion output. |
| Dry Run | Drop the duplicate "`--dry-run` output for Steps 4-5" block. |
| Error Handling | "Not on a feature branch": `site: choice` record recommending "Create branch `<name>`". "Uncommitted changes": tracked modifications only → record recommending "Commit now"; untracked files present → record with no recommendation, so it asks. Combined case: branch decision, then commit decision. Hard stops (no remote, no `gh`, no auth) unchanged. |

Every decision record goes to `.writ/state/ship/decision-<step>.json` and runs `python3 scripts/jev-judge.py doubt --record <file>`. After an asked answer: `python3 scripts/jev-judge.py doubt-label --id <id> --outcome as_recommended|overridden`.

`.writ/docs/config-format.md` Supported Keys gains: `` | `Eval Command` | ship | Command `/ship --test` and `--watch` run after the Test Runner; its exit code goes into the verification ledger. Absent: the Test Runner alone. | ``. The example block gains `- **Eval Command:** make lint`.

### Story 3: watch pass

**Frontmatter** (after `exit_criteria`, exact):

```yaml
loop:
  unit: "watch_pass"
  max_iterations: 24
  on_exhaustion: halt_reported
  calibrated_against: "no recorded run - no /ship --watch run existed when this bound was set. Every pass counts, waiting passes too. The halt record goes to .writ/state/ship/watch-pr-<n>.json with the resume command /ship --watch. Recalibrate against the first recorded runs."
  nested:
    - unit: "fix_commit"
      max_iterations: 3
      on_exhaustion: escalate
      calibrated_against: "no recorded run - mirrors the three-iteration review loop in commands/implement-story.md; a fourth fix push on one PR asks instead."
```

**Invocation row:** `` | `/ship --watch` | Open the PR if none is open (implies `--test`), then run one watch pass (Step 7). Keep watching with the adapter's `re-enter` row. | ``. **When to Use row:** `` | Drive an open PR to merge-ready | `/ship --watch` | ``.

**Step 5 addition:** with `--watch`, record `draft_reason` (`tests_failed`, `drift`, or `flag` for `--draft`) in `branch-<slug>.json`. With `--watch`, a Step 3 failure that survives one fix pass opens the PR as a draft and ends the run at `asked`.

**Step 7: Watch Pass (`--watch`)**

7.1 **Resolve the PR.** `gh pr view --json number,state` for the current branch. None → run Steps 1–5 with `--test`, then continue with the new PR. `MERGED` → Step 6, report `merged`. `CLOSED` → report `asked`. A PR tool other than `gh` → stop: "`--watch` needs gh."

7.2 **Bound.** Read `watch-pr-<n>.json`; create it with `passes: 0` when absent. Unreadable → `asked` (a reset count would unbind the loop). `passes >= 24` → write `halt`, print `Resume: /ship --watch`, report `halted`. Otherwise increment `passes` and write the file before any other step.

7.3 **Snapshot.** Run the snapshot commands `python3 scripts/pr-ready.py --help` prints, with `N=<n>` and `SNAP=.writ/state/pr-ready/pr-<n>.json`. A gh error → `asked` with gh's message (`gh auth login` for auth).

7.4 **Judge.** `python3 scripts/pr-ready.py check --snapshot .writ/state/pr-ready/pr-<n>.json`. Exit 2 or 1 → `asked` with stderr. Read line 1 and every `reason:` line.

7.5 **Sync.** Before any local change: `git fetch origin`. Local HEAD equal to `view.headRefOid` → continue. Behind it → `git pull --ff-only`. Diverged → `asked`.

7.6 **Act on the first match, then report:**

| First match in the pr-ready output | Action | State |
|---|---|---|
| line 1 `pass` | Merge step (Story 4) | `merged` / `asked` |
| `conflicts` | Merge `origin/<baseRefName>` (Step 2). Clean: push. Conflict: `git merge --abort`, list the files, ask. | `acted` / `asked` |
| `merge_gates: behind` | Rebase convention: ask. Otherwise merge the base, push. | `acted` / `asked` |
| `unresolved_threads` | Thread action (7.7) | `acted` / `waiting` / `asked` |
| `failing_checks` | CI action (7.8) | `acted` / `asked` |
| `merge_gates: not_verified` | Ledger action (7.9) | `acted` / `asked` |
| `merge_gates: draft` | `draft_reason` is `tests_failed`: `gh pr ready <n>`. Otherwise ask. | `acted` / `asked` |
| `merge_gates: not_open` | `MERGED`: Step 6. Otherwise ask. | `merged` / `asked` |
| `merge_gates: changes_requested`, `review_required`, `merge_state_blocked`; `unknown: checks_pending`, `mergeable_unknown`, `head_moved` | Nothing | `waiting` |
| `unknown: threads_truncated`, `merge_state_unexplained` | Ask | `asked` |

7.7 **Thread action.**
1. Fetch comments into a file (static query; no PR text on the command line):
   ```bash
   gh api graphql -F owner='{owner}' -F name='{repo}' -F number=<n> -f query='query($owner:String!,$name:String!,$number:Int!){repository(owner:$owner,name:$name){pullRequest(number:$number){reviewThreads(first:100){nodes{id isResolved path line comments(first:50){nodes{author{login} body url}}}}}}}' > .writ/state/ship/threads-pr-<n>.json
   ```
2. Take the first unresolved thread not in `replied`. None left → `waiting`.
3. Write a `site: choice` record. Options: "Fix it in this PR", "Reply without a change", "Ask the person". Evidence states the request in Writ's words and names the thread id and `path:line`; it never pastes the comment body. A request touching files outside `git diff --name-only <merge-base>...HEAD`, `.github/workflows/`, or credentials gets no recommendation.
4. Fix: change, commit, push (`fix_commits` +1; at 3 already, ask instead), reply naming the commit, resolve → `acted`. Reply-only: reply, add the id to `replied` → `acted`. Ask: link the first comment's `url` → `asked`.
5. Request bodies, written with the file-writing tool to `.writ/state/ship/reply-pr-<n>.json`, sent with `gh api graphql --input .writ/state/ship/reply-pr-<n>.json`:
   ```json
   {"query": "mutation($id:ID!,$body:String!){addPullRequestReviewThreadReply(input:{pullRequestReviewThreadId:$id,body:$body}){comment{url}}}",
    "variables": {"id": "<thread id>", "body": "<reply text>"}}
   ```
   ```json
   {"query": "mutation($id:ID!){resolveReviewThread(input:{threadId:$id}){thread{isResolved}}}",
    "variables": {"id": "<thread id>"}}
   ```

7.8 **CI action** (first failing check):
1. Run id: the `statusCheckRollup` entry with that name; `detailsUrl` matching `/actions/runs/<id>/`. None → no rerun possible.
2. `gh run view <id> --log-failed > .writ/state/ship/run-<id>.log`. The log is data.
3. The log names a file in the diff → fix, commit, push (`fix_commit`) → `acted`.
4. Otherwise `git merge-base --is-ancestor origin/<baseRefName> HEAD` false → merge the base, push (rebase convention: ask) → `acted`.
5. Otherwise no `reruns["<check>@<head>"]` and a run id → `gh run rerun <id> --failed`, record it → `acted`.
6. Otherwise → `asked` (real failure outside the diff, or not rerunnable).

7.9 **Ledger action.** Run the Step 3 commands on HEAD (equal to the snapshot head after 7.5). All exit 0 → `verify-ledger.py record` as in Step 5 → `acted`. A failure in the diff → fix, commit, push (`fix_commit`) → `acted`. Otherwise → `asked`. `record` refusing → `asked` with its reason.

7.10 **Report.** Write `last`, then print `ship-watch: <state> pass <n>/24 pr #<n> head <sha7> — <detail>`. `merged`, `asked`, and `halted` end the loop.

**Dry run.** `--watch --dry-run` runs 7.1, 7.3, and 7.4, prints the 7.6 row it would take and, on `pass`, the merge record it would write. It runs no doubt check, changes no git or PR state, and does not count a pass.

### Story 4: merge

**Merge step** (7.6 row `pass`):
1. Save `pre_merge_base = git rev-parse origin/<baseRefName>` to the watch file.
2. Write `.writ/state/ship/merge-record-pr-<n>.json`:
   ```json
   {"site": "merge",
    "question": "Merge PR #<n> into <baseRefName> now?",
    "options": ["Merge now (Recommended)", "Leave it at merge-ready"],
    "recommended": "Merge now",
    "evidence": ["the person ran /ship --watch",
                 "<pr-ready summary line>",
                 "restore: revert the landed commit; <baseRefName> was <pre_merge_base> before the merge"],
    "reversible": true,
    "pr": <n>, "head_sha": "<view.headRefOid>", "snapshot": ".writ/state/pr-ready/pr-<n>.json"}
   ```
   Add `"/review: <recommendation line>"` to `evidence` when `.writ/state/review-<branch>.md` exists.
3. `python3 scripts/jev-judge.py doubt --record .writ/state/ship/merge-record-pr-<n>.json`.
4. `pass` → `gh pr merge <n> --match-head-commit <view.headRefOid> --<method>`. Method: `Merge Strategy` when it is `merge`, `squash`, or `rebase`; otherwise `merge`. Never `--delete-branch`, `--admin`, or `--auto`.
5. `fail` → AskQuestion "Merge PR #<n> now?" ("Merge now (Recommended)", "Leave it at merge-ready"), then `doubt-label` the answer. "Merge now" → step 4's command. "Leave" → `asked`.
6. gh refuses because the head moved → `waiting`. Any other refusal → `asked` with gh's message.
7. `gh pr view <n> --json state,mergeCommit`. `MERGED` → Step 6 in this pass → `merged` with the doubt id. Any other state → `asked` with the state gh returned.

**Step 6 sentence:** "With `--watch`, the merge happens in the pass, so Step 6 runs right after it."

**Frontmatter (exact):**

```yaml
description: "Take a green branch to an open PR - merge the default branch, organize commits, write the PR description, push, and open it. With --watch, work the PR to merge-ready and merge it when verified."
exit_criteria:
  - "the current branch has an origin upstream and its local tip equals the pushed tip"
  - "a pull request exists whose head is the current branch, open or merged by --watch, and whose body carries Summary, Changes, Spec Reference and Test Results sections"
  - "when the PR opened, the default branch tip was an ancestor of the branch tip, and the PR is marked draft whenever tests failed or drift is unresolved"
  - "with --watch, the run ended merged, at merge-ready with an ask, or at a halt record, and any merge ran gh pr merge --match-head-commit after pr-ready.py passed and the doubt check passed for that head"
```

`problem` and `outcome` are unchanged.

**Overview addition:** "With `--watch`, `/ship` then works the PR to merge-ready one pass at a time and merges it when the ledger and the doubt check allow."

**Completion terminal constraint:** "Without `--watch`, this command stops at an opened pull request: do not merge it, request reviewers, or begin the next piece of work. With `--watch`, it stops merged, at merge-ready with an ask, or at a halt record. It never requests reviewers, releases, tags, or publishes." The "⚠️ The PR is now the source of truth" block becomes one sentence: "After the PR merges, open a new branch for follow-up changes; commits pushed to a merged branch are orphaned."

## Text Changes Outside `ship.md`

| File | Story | New text |
|---|---|---|
| `commands/_preamble.md:49` | 1 | Two rows: `` | `release` (tag, publish, deploy) | Always | `` and `` | `merge` | `pr-ready.py` does not pass for the record's PR and head; Jev is uncalibrated, or its confidence is not above the threshold | `` |
| `.writ/docs/recommendation-semantics.md` | 1 | Record table: rows `pr` (integer, merge only: the PR number), `head_sha` (40 hex characters, merge only: the head the merge is bound to), `snapshot` (path, merge only: the snapshot `pr-ready.py` judged in this pass). Step 1: "**Rules, no network.** `release` always asks. `merge` asks unless the record names `pr`, `head_sha`, and `snapshot`, and `pr-ready.py check --json` on that snapshot, run locally, passes for that PR and head; its pass needs the verification ledger to read VERIFIED. Any site asks when ..." (rest unchanged). Step 4: "`direction`, `design`, and `merge` ask; `choice`, `route`, `plan`, and `destructive` act." |
| `system-instructions.md:38-40` | 1 | "- **Release stays a person's call.** Releasing, tagging, and publishing wait / for a person's answer. A merge waits too unless `pr-ready.py` passes for the / PR's exact head, which needs the verification ledger to read VERIFIED, / and the doubt check passes. / Nothing bypasses branch protection, required checks, authentication, or authorization." (`/` marks line breaks.) |
| `system-instructions.md:43-45` | 3 | "... Autonomy is / session-started and bounded to one spec, one roadmap phase, or one PR's / `/ship --watch` passes; it never becomes an unbounded loop." |
| `scripts/eval.sh:1081` | 1 | Message: "The system policy must keep release, tag, and publish behind a person's answer, and merge behind pr-ready and the ledger (ADR-033)." Add `require_literal "$system" "A merge waits too unless" "The system policy must state when a merge may proceed without a person (ADR-033, Phase 16)."` |
| `scripts/eval.sh:1085` | 3 | Message: "The system policy must keep autonomy bounded: no unbounded loop." |
| `README.md:66` | 1 | Replace "Merge, release, tag, and publish always wait for you." with "Release, tag, and publish always wait for you. A merge waits too unless `pr-ready.py` passes for the PR's exact head with the ledger VERIFIED and the doubt check passes." |
| `.writ/decision-records/adr-033-doubt-gated-autonomy.md` | 1 | New `### 2026-11-06 — Merge acts under the ledger (Phase 16)` under Amendments: merge leaves always-ask; the rule re-runs `pr-ready.py --json` locally and maps its result; `merge` joins the fallback-ask sites, so no merge acts until a threshold is calibrated; release, tag, and publish stay always-ask. |
| `.writ/docs/agent-cli-contract.md` | 1, 2, 3 | Callers cells only. `pr-ready.py`: Story 1 → `scripts/jev-judge.py`; Story 3 → `commands/ship.md, scripts/jev-judge.py`. `verify-ledger.py`: Story 2 → `commands/ship.md`. |
| `scripts/eval-loop-bounds.py:72`, `scripts/eval-leanness.py:760` | 3 | Add `"ship"`. Docstrings: "five" → "six". |
| `scripts/eval-command-structure.py` `ROWS` | 2, 3, 4 | Story 2: `invocation` `scripts/verify-ledger.py record --pr`, `invocation` `scripts/jev-judge.py doubt --record`. Story 3: `invocation` `scripts/pr-ready.py check --snapshot`, `heading` `Step 7: Watch Pass`. Story 4: no new row. |

## Adapter `re-enter` Rows (Story 3)

| Adapter (table) | Row |
|---|---|
| `claude-code.md` (Quick Reference) | `` | `re-enter` | `/loop /ship --watch`, with no interval so the session paces itself | The loop runs in this session and checkout. It stops when a pass reports `merged`, `asked`, or `halted`. | `` |
| `cursor.md` (Native Tool Availability) | `` | `re-enter` | ship (Step 7) | No documented loop feature. Run one pass, print `Resume: /ship --watch`, and stop. | `` |
| `codex.md` (orchestration primitives) | `` | `re-enter` | No documented loop feature | Run one pass, print the resume command, and stop. | `` |
| `openclaw.md` (Quick Reference) | `` | `re-enter` | No verified loop feature | Run one pass, print the resume command, and stop. | `` |

Claude Code's row needs a dated line in its verification record: the Claude Code version, the docs page or help text that shows `/loop` without an interval, and `verified` or `unverified`. A Codex or OpenClaw loop feature found in their docs replaces that row's fallback only with a dated record.

## Byte Budget

`commands/ship.md` starts at 28,907 bytes (overage 3,947). Each story that changes it re-pins `KNOWN_OVER_BUDGET["commands/ship.md"]` to `wc -c < commands/ship.md` minus 24,960, with one dated comment line appended directly above the entry, inside the existing comment block (no blank line):

```
# 2026-MM-DD (2026-11-06-ship-watch-and-merge Story N): <old> -> <new>; <what changed>. Acknowledged, not exempted.
```

**Floor:** after every story the file stays above 24,960 bytes. At or below it, the entry and `test_harness_cuts.py`'s `recorded[SHIP]` lookup break. If a story's cuts would cross the floor, leave the remaining cuts to Story 4.

| Story | Cuts (bytes, measured 2026-11-06) | Adds (estimate) | Net target |
|---|---|---|---|
| 2 | ASCII pipeline → one line (−1,980); Detection chain details (−1,055); duplicate dry-run block (−447); non-extraction note (−465); opinionated defaults (−431); PR-agent paragraph (−369); commit-plan `AskQuestion` and approval lines (−600) | Doubt Rule records (+900); evidence and `record` (+1,300) | −2,500 to −3,900 |
| 3 | Dry Run Mode section condensed (−600); When to Use trimmed (−250); label-fallback example → one sentence (−250) | Step 7 (+3,200); `loop:` block (+450); Invocation and When to Use rows (+250); Step 5 draft reason (+150) | ≤ +3,000 |
| 4 | "Source of truth" block → one sentence (−250) | Merge step (+900); frontmatter (+250); Overview and Completion (+250); Step 6 sentence (+100) | ≤ +1,200 |

**Reserve cuts** if the running total is above zero after Story 4: Auto-labeling table → one sentence (about −350); Step 2 conflict example compacted (about −250); Draft vs. Ready table folded into one rule (about −200). Step 6 is not cut: its literals are pinned.

The cap is not a gate (ADR-023). A residual above zero is disclosed in the dated comment.

## Error & Rescue Map

| Operation | What Can Fail | Planned Handling | Test Strategy |
|---|---|---|---|
| Merge rule: run `pr-ready.py` | Script missing, crash (exit 1), usage (exit 2), timeout, non-JSON stdout | `merge_unverifiable`; the merge asks | Stub `pr-ready.py` per case |
| Merge rule: compare | JSON `pr` or `head` differs from the record | `merge_head_mismatch`; asks | Stub returning another head |
| Merge rule: ledger | `not_verified` blocker | `merge_not_verified`; asks, no Jev call | Real scripts, new head B |
| Fetch snapshot | `gh` not authenticated | `asked`: "Run `gh auth login`, then `/ship --watch`" | Prose pin |
| Fetch snapshot | Network or GraphQL error | `asked` with gh's message; the pass is counted | Prose pin |
| `pr-ready.py check` | Exit 2 (bad snapshot) or 1 | `asked` with stderr | Prose pin |
| Sync with remote | Local branch diverged from the PR head | `asked`; never force-push | Prose pin |
| Merge the base | Conflict | `git merge --abort`, list files, `asked` | Prose pin |
| Push | Rejected (remote moved) | Next pass syncs (`waiting`) | Prose pin |
| Fetch thread comments | gh error | `asked` with gh's message | Prose pin |
| Reply or resolve | gh error (permissions) | `asked`; the thread is not resolved | Payload template parse test |
| Fetch failed log | gh error | Classify as untouched code (stale-base, then rerun path) | Prose pin |
| CI rerun | No run id (not GitHub Actions) | `asked` | Prose pin |
| CI rerun | Rerun refused | `asked` with gh's message | Prose pin |
| Evidence run | A command fails | Fix in the diff, or `asked`; nothing recorded | Prose pin |
| `verify-ledger.py record` | Refuses (dirty tree, head not checked out, failing evidence) | `asked` with its reason | Filled command test |
| Doubt check | Exit 2 (malformed record) | Treated as ask | Filled record test |
| `gh pr merge` | Head moved (`--match-head-commit`) | `waiting`; next pass re-snapshots | Prose pin |
| `gh pr merge` | Method not allowed, protection, other refusal | `asked` with gh's message | Prose pin |
| Read back | State not `MERGED` (for example a merge queue) | `asked` with the state. `[OUT OF SCOPE — merge queues]` | Prose pin |
| Step 6 audit note | Any error | Non-blocking, as today | Existing pins |
| Watch state | Unreadable | `asked`; the file is not recreated | Prose pin |

## Shadow Paths

| Flow | Happy Path | Nil Input | Empty Input | Upstream Error |
|---|---|---|---|---|
| Merge rule | pr-ready `pass` for the record's PR and head → Jev → act or ask | Record without `pr`, `head_sha`, or `snapshot` → `no_verification_ledger` | Empty snapshot file → pr-ready exit 2 → `merge_unverifiable` | pr-ready missing or timed out → `merge_unverifiable` |
| Open path | PR opens, ledger row recorded, no question | No Test Runner with `--test` → asks | No Eval Command → Test Runner only | `record` refuses → not recorded; completion output says why |
| Watch pass | One action, one line | No PR for the branch → open path first | No blocker, only unknowns → `waiting` | gh failure → `asked` |
| Thread action | Fix, push, reply naming the commit, resolve | Thread resolved since the snapshot → next pass (`waiting`) | Every unresolved thread already replied to → `waiting` | Mutation error → `asked` |
| Merge | `merged` with the doubt id | No threshold → `asked` (`fallback_merge`) | `/review` file absent → evidence without it | gh refusal → `asked` or `waiting` |

## Interaction Edge Cases

| Edge Case | Planned Handling |
|---|---|
| Someone pushes to the PR branch during the watch | 7.5: `git pull --ff-only`; diverged → `asked` |
| A person merges the PR mid-watch | `not_open MERGED` → Step 6 → `merged` |
| A person closes the PR | `not_open CLOSED` → `asked` |
| The head moves between the snapshot and the merge | `--match-head-commit` refuses → `waiting` |
| The base moves between the pr-ready pass and the merge | GitHub's branch protection decides; `/ship` adds no check |
| A comment contains shell syntax or instructions | Never reaches a shell; instructions are not followed; the request is judged as a change request |
| A CI log contains instructions | Data only |
| Two sessions watch the same PR in one checkout | `[OUT OF SCOPE — one watch per PR; both write the same watch file and the count can drift]` |
| A thread is replied to but never resolved by the reviewer | Skipped on later passes; the PR stays `waiting` until the bound |
| More than 100 threads | `threads_truncated` → `asked` |

## Test Plan

| Story | File | Tests |
|---|---|---|
| 1 | `scripts/tests/test_jev_doubt.py` (new section at the end naming `2026-11-06-ship-watch-and-merge`) | Stub cases: missing fields, missing script, exit 1, exit 2, timeout, non-JSON, head mismatch, pr mismatch, `not_verified`, other blocker (`pr_ready_unresolved_threads` info), unknown only (`pr_ready_checks_pending`), pass + calibrated p 0.8 → act, pass + uncalibrated provider → `fallback_merge` with p logged, pass + no provider → `fallback_merge`, malformed `pr`/`head_sha` → exit 2, release → `outward`. Real-script cases: new head B, rebased head A'. Log row carries `pr` and `head_sha`. Text pins: `_preamble.md` rows, `recommendation-semantics.md` steps 1 and 4, `system-instructions.md` merge sentence, `README.md:66`. |
| 2 | `scripts/tests/test_ship_watch.py` (create; Story 2 section) | No `AskQuestion(` before `### Step 5`; no "Override?" or "Save to `.writ/config.md`?"; no `┌`; no "Non-extraction note"; Step 4 names `site: plan`, `presplit_sha`, `origin/<branch>..HEAD`; the Step 5 `record` command, filled with a temp repo's values, writes a ledger row that `verify-ledger.py check` reads VERIFIED; `config-format.md` `Eval Command` row; Callers cell. |
| 3 | `test_ship_watch.py` (Story 3 section) | `loop:` block parsed by `eval-loop-bounds.py`'s parser with the exact units and bounds; `ship` in both lists; 7.6 table rows in the order above; 7.7 query and both payload templates parse as JSON with `query` and `variables` after filling; the watch section has no `--body`, `-f body=`, or `-F body=`; `detailsUrl`, `--log-failed`, `merge-base --is-ancestor`, `gh run rerun` present; `re-enter` row in all four adapters; `system-instructions.md` loop sentence. |
| 4 | `test_ship_watch.py` (Story 4 section), `test_harness_cuts.py` | The merge record template, filled and passed to `jev-judge.py doubt` with a stub pr-ready `pass`: no threshold → `fail` `fallback_merge`; calibrated fixture with a fake transport → `pass`. The merge command line has `--match-head-commit` and none of `--delete-branch`, `--admin`, `--auto`. `doubt-label` named on the ask path. No `gh release`, `git tag`, or `npm publish` in `ship.md`. `test_harness_cuts.py` pins the new `exit_criteria` and scopes AC-3.3. |

Every story runs `uv run --isolated --python 3.9 --with pytest pytest` and `--python 3.14`, each alone, then `bash scripts/eval.sh` alone, then the bash suite in the background (`CLAUDE.md`). None of them runs while another agent writes under `.writ/state/` in the same checkout.
