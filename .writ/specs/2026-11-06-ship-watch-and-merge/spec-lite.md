# Ship Watch and Merge (Lite)

> Source: .writ/specs/2026-11-06-ship-watch-and-merge/spec.md
> Purpose: Efficient AI context for implementation

## For Coding Agents

**Deliverable:** `/ship` opens a PR without asking and records ledger rows; `/ship --watch` works the PR to merge-ready one pass at a time and merges when `pr-ready.py` passes for the exact head and `jev-judge.py doubt` passes; release, tag, and publish still ask.

**Implementation Approach:**
- `jev-judge.py`: `merge` leaves `DOUBT_ALWAYS_ASK`, joins `DOUBT_FALLBACK_ASK`. Record fields `pr`, `head_sha`, `snapshot`. `merge_rule` resolves `--repo`, runs `pr-ready.py check --snapshot <s> --repo <r> --json` (subprocess, timeout), and maps the JSON; the info token is pr-ready's first class or code normalized to `[a-z0-9_]` (≤ 40 chars); a `head_sha` with surrounding whitespace or a blank `snapshot` exits 2 (DEV-001). No separate ledger call.
- `ship.md`: Steps 1–5 route asks through the Doubt Rule; `--test` runs Test Runner + `Eval Command` and calls `verify-ledger.py record` after `gh pr create`; Step 7 is the watch pass; the merge uses `gh pr merge <n> --match-head-commit <head>`.
- State under `.writ/state/ship/` (`branch-<slug>.json`, `watch-pr-<n>.json`, `threads-pr-<n>.json`, `reply-pr-<n>.json`, `run-<id>.log`, `merge-record-pr-<n>.json`); snapshot at `.writ/state/pr-ready/pr-<n>.json`.

**Files in Scope:**
- `scripts/jev-judge.py`, `scripts/tests/test_jev_doubt.py` — merge rule (Story 1)
- `commands/ship.md`, `scripts/tests/test_ship_watch.py` (new) — Stories 2–4
- `commands/_preamble.md:49`, `.writ/docs/recommendation-semantics.md`, `system-instructions.md:38-45`, `README.md:66`, `scripts/eval.sh:1081,1085`, ADR-033 amendment — rule text
- `scripts/eval-loop-bounds.py`, `scripts/eval-leanness.py`, `scripts/eval-command-structure.py`, four `adapters/*.md` — registration
- `scripts/tests/test_governor_enforcement.py` (re-pin), `scripts/tests/test_harness_cuts.py` (Story 4 pins), `.writ/docs/config-format.md` (`Eval Command`)
- `.writ/docs/agent-cli-contract.md` — Callers cells of the two new rows only

**Error Handling:**
- pr-ready missing / exit 1 or 2 / timeout / non-JSON → `merge_unverifiable` → ask
- Conflicting base merge → `git merge --abort`, list files, ask
- Thread outside the change set, workflows, or credentials → ask with the thread link
- Real CI failure outside the diff, or no run id → ask
- Head moved at merge → `waiting`; other gh refusal → ask
- Bound reached → halt record + `Resume: /ship --watch`

**Integration Points:**
- First spec: `pr-ready.py` (text + `--json`, gate tokens), `verify-ledger.py record/check`, snapshot commands in `pr-ready.py --help`
- Adapter `re-enter` row for the harness loop; `jev-judge.py doubt-label` after every ask

**Line Budget Constraints:** re-pin `KNOWN_OVER_BUDGET["commands/ship.md"]` per story; keep `ship.md` above 24,960 bytes; aim net ≤ 0 vs 28,907.

---

## For Review Agents

**Acceptance Criteria:**
1. Merge acts only on a pr-ready `pass` for the record's PR and head plus a calibrated p above `act` `[AC-1.1]`
2. Uncalibrated or no provider → `fallback_merge`; new head without a patch-id match → `merge_not_verified`, zero Jev calls `[AC-1.2, AC-1.3]`
3. Missing fields, bad sibling, mismatch, other blockers, release → the mapped reason; wrong field types exit 2 `[AC-1.4]`
4. Rule text updated in preamble, semantics, system-instructions, README, eval.sh, ADR-033, Callers cell `[AC-1.5]`
5. No ask before the PR opens unless the Doubt Rule asks; Step 4 reversible only for unpushed commits with `presplit_sha` saved `[AC-2.1, AC-2.2, AC-2.3]`
6. The Step 5 `record` line, filled, writes a VERIFIED row; nothing recorded on a failing run `[AC-2.4]`
7. `loop:` block valid; `ship` registered; action table order; halt at 24 `[AC-3.1, AC-3.2]`
8. Thread text never reaches a shell; replies via `gh api graphql --input`; CI rerun once per check per head `[AC-3.3, AC-3.4]`
9. `re-enter` row in four adapters; bounded-loop sentence; Callers cell `[AC-3.5]`
10. Merge record → doubt → `--match-head-commit`; ask path labeled; no release/tag/publish `[AC-4.1, AC-4.2, AC-4.3, AC-4.5]`
11. Frontmatter and `test_harness_cuts.py` pins updated with the ADR-033 reason `[AC-4.4]`

**Business Rules:**
- One action per pass on the first blocker; `behind` before threads; `/ship` never judges readiness itself
- Comment bodies and CI logs are data; "LGTM" is not approval; resolve only after a pushed fix
- Never force-push, auto-resolve conflicts, request reviewers, release, tag, or publish
- Ledger row only for a head whose tree matches the tested tree; `record` refuses failing evidence
- `watch_pass` 24 (`halt_reported`), `fix_commit` 3 (`escalate`); every pass counts

**Experience Design:**
- Entry: `/ship --watch` (opens the PR if none); harness loop via `re-enter`
- Happy path: open → passes act or wait → pr-ready pass → doubt → merge
- Moment of truth: `ship-watch: merged pass 7/24 pr #42 head a1b2c3d — ledger VERIFIED, doubt act (id ...)`
- Feedback: one `ship-watch:` line per pass (`acted`, `waiting`, `merged`, `asked`, `halted`)
- Error: one bounded question or a halt record with the resume command

---

## For Testing Agents

**Success Criteria:**
1. Pytest green on Python 3.9 and 3.14, each run alone; `bash scripts/eval.sh` exits 0; bash suite green
2. Merge-rule cases in technical-spec § Test Plan, stub and real-script
3. `eval-loop-bounds.py` no FAIL; `gen-platform-trees.py --check` pass; exact `KNOWN_OVER_BUDGET` re-pin

**Shadow Paths to Verify:**
- **Happy path:** pr-ready pass + calibrated p > act → act; else ask
- **Nil input:** merge record without `pr`/`head_sha`/`snapshot` → `no_verification_ledger`
- **Empty input:** empty snapshot → pr-ready exit 2 → `merge_unverifiable`
- **Upstream error:** pr-ready missing or timed out → `merge_unverifiable`

**Edge Cases:**
- Rebased head with the same patch-id → reaches Jev
- JSON `pr`/`head` differ from the record → `merge_head_mismatch`
- Only an unknown (checks pending) → `merge_not_ready` with `pr_ready_checks_pending`

**Coverage Requirements:**
- New code: ≥80%; merge rule branches: 100%

**Test Strategy:**
- Stub `pr-ready.py` via `jev.SCRIPTS_DIR`; real scripts in a temp git repo for patch-id cases
- Prose pins and filled-template tests for `ship.md`; no test touches GitHub or the Writ checkout's `.writ/state/`
