# Lean Story Pipeline (Lite)

> Source: .writ/specs/2026-11-06-lean-story-pipeline/spec.md
> Purpose: Efficient AI context for implementation

## For Coding Agents

**Deliverable:** The default `/implement-story` path runs its deterministic checks through two `story-gate.py` calls. Every gate declares `catches`, `evidence`, and `kill_when`. Gates with no recorded catch move to `--full-pipeline`. Each story runs targeted tests only.

**Implementation Approach:**
- Story 1 records the evidence per gate (`gate-evidence.md`) before anything is demoted.
- Story 2 demotes; Story 3 builds the runner over the default set that remains.
- `story-gate.py` is a check-shape script (Python 3.9 stdlib). It computes changed files from `--base`, runs a fixed check table, writes `.writ/state/story-gate-<stem>-<phase>.json` atomically, and keeps history for `tally`.
- A test asserts that the runner's check table equals the `gates:` entries with `path: default`.
- Kept gates (Safety Fact, Reviewer Filters, Gate 0 Divergence, evidence gate) and the inputs they need stay on the default path (Business Rule 3).

**Files in Scope:**
- `commands/implement-story.md`: `gates:` frontmatter, demoted sections, two runner calls, Gate 4 prose
- `scripts/verdict-provenance.py` + tests: new finding codes
- `scripts/story-gate.py`, `scripts/tests/test_story_gate.py`: new
- `agents/supervisor-agent.md`, `commands/implement-spec.md`: record input, Step 2.3 removed, no context regen in 3.3
- `agents/coding-agent.md`, `agents/evaluator-agent.md`, `agents/review-agent.md`: targeted tests only
- `.writ/docs/agent-cli-contract.md`, ADR-029 note, `test_governor_enforcement.py` ledger, generated trees

**Error Handling:**
- A missing or crashing checker records `unverifiable (helper_error: …)`, and the run continues
- Record write fails → `reason: record_write_failed`; story `⚠️ DEGRADED`
- Code commit after the record → supervisor `RERUN`

**Integration Points:**
- `/implement-spec` supervisor reads the record; `/implement-phase` lanes inherit it
- `test_gate_upgrade_trial_outcome.py` presence probes must keep passing

**Line Budget Constraints:** `implement-story.md` must shrink; disclose sizes in `KNOWN_OVER_BUDGET`.

---

## For Review Agents

**Acceptance Criteria:**
1. Every `gates:` entry has `catches`, `evidence`, `kill_when`; `verdict-provenance.py check` fails on a missing one `[AC-1.1, AC-1.3]`
2. Each gate with `evidence: none recorded` runs only under `--full-pipeline`; no gate script is deleted `[AC-2.1, AC-2.2, AC-2.5]`
3. The default path names at most 4 script invocations, and `implement-story.md` is smaller `[AC-3.5]`
4. `story-gate.py run` prints check shape, writes one record per story and phase with the head SHA, and never fails on `unverifiable` `[AC-3.1, AC-3.2, AC-3.3]`
5. The supervisor returns `RERUN` when the record is missing, or when its head is not the final code commit `[AC-5.1, AC-5.2]`
6. Coding and Gate 3 agents run targeted tests only; the full suite runs once at `implement-spec` Step 4.1 `[AC-4.1, AC-4.2, AC-4.3]`
7. The trial report compares the before and after arms and states a verdict `[AC-6.2, AC-6.4]`

**Business Rules:**
- Rules 1–8 in `spec.md` → Specification Contract; expanded detail in `spec.md` → Business Rules (Expanded)
- The keep verdicts are not reopened (Rule 3); the file-creation rule is unchanged (Rule 8)

**Experience Design:**
- Entry: `/implement-story`, `/implement-spec`, or an `/implement-phase` lane
- Happy path: coder → `story-gate` pre-review → Gate 3 → `story-gate` post-review → completion
- Moment of truth: one `story-gate:` line per phase; the supervisor reads the record
- Feedback: report lines plus the state record
- Error: typed reason plus `restart:`; `unverifiable` never DEGRADED

**Drift thresholds:** demoting a gate whose `gate-evidence.md` row cites a catch is Large drift.

---

## For Testing Agents

**Success Criteria:**
1. `test_story_gate.py` covers run, tally, record shape, atomic write, and every Error & Rescue Map row
2. `verdict-provenance.py` tests cover each new finding code
3. Both pytest interpreters, the bash tests, and `eval.sh` pass; `gen-platform-trees.py --check` is clean

**Shadow Paths to Verify:**
- **Happy path:** all checks pass → `pass`, record written
- **Nil input:** no `--review-output` → review checks `unverifiable (no_review_output)`
- **Empty input:** no changed files → overall `pass`
- **Upstream error:** checker crashes → `unverifiable (helper_error: …)`; others still run

**Edge Cases:**
- Commit after the record → supervisor `RERUN`
- Two stories writing records in parallel → separate files, no clobber
- Not a git repo → git-dependent checks `unverifiable (no_git)`

**Coverage Requirements:**
- New code: ≥80%; record write and verdict paths: 100%

**Test Strategy:**
- Unit tests with stub checker scripts in a temp repo; no real project linters
- Pin tests: default check set equals `gates:` with `path: default`
