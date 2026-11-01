# Gate Upgrade Removal Measurement (Lite)

> Source: .writ/specs/2026-10-25-gate-upgrade-removal-measurement/spec.md
> Purpose: Efficient AI context for implementation

## For Coding Agents

**Deliverable:** A retrospective trial over the four Phase 11 baseline stories that runs each Phase 15 gate upgrade on against all switches off, gets human labels for upgrade-only findings, and keeps or removes each upgrade.

**Implementation Approach:**
- Dev-only harness `.writ/eval/gate-upgrade-trial/gate-upgrade-trial.py` (3.9 stdlib, check shape): `init`, `prepare`, `record`, `sheet`, `label`, `report`. Loads `scripts/review-panel.py` by path for `_prepare_run`, `parse_output`, `trial_key`, `_key_order`.
- Arms per story: `off-1`, `off-2`, `reviewer-filters` (all stories); `safety-fact` (Gate 2.5 route review-agent); `gate0-divergence` (Gate 0 predicted route review-agent; sketch + comparison spawn); `repro-first` (recognition everywhere, full arm only on a bug).
- Upgrade-only = arm keys minus keys of both off runs. Gate 0 counts only `**Avoided by:**` issues. Repro fail/fail → `ac:<id>` Critical.
- Raw outputs in the primary checkout's gitignored `.writ/state/gate-upgrade-trial/`. Committed files hold IDs, SHAs, keys, labels only.

**Files in Scope:**
- `.writ/eval/gate-upgrade-trial/**` — harness (temporary), prompts, trial JSON, labeling sheet
- `scripts/tests/test_gate_upgrade_trial.py` + fixtures — unit tests (temporary)
- `scripts/tests/test_gate_upgrade_trial_outcome.py` — verdict ↔ repo state
- spec folder: `rating-handoff.md`, `trial-report.md`, status line
- Story 4 only: removal-inventory files of `remove` upgrades, roadmap "Removal measurement" line, ADR-030 § Review note

**Error Handling:**
- yuss missing / SHA unreachable / parent beyond depth 2 → exit 2, nothing written
- Arm evidence mismatch, wrong origin, inapplicable arm → `record` exit 2, file unchanged
- Edited sheet, blank field, agent-like labeler → `label` exit 2
- Missing arm, unlabeled, unacknowledged → that upgrade `unverifiable`

**Integration Points:**
- Switches and resolvers from the three dependency specs; `change-surface.py`, `boundary-map.py`, `review-override.py switch|safety-fact`
- design-divergence blind trial (Business Rule 12)

**Never touch:** `commands/{why,writ,retro,refresh-command}.md`; anything in yuss.

---

## For Review Agents

**Acceptance Criteria:**
1. `init`/`prepare` build read-only inputs, routes, and arm configs; yuss unchanged `[AC-1.1, AC-1.3, AC-1.4]`
2. `record` refuses arms whose switch evidence does not match `[AC-2.1]`
3. `report` verdicts follow technical-spec § Verdict; one `upgrade:` line each `[AC-2.4]`
4. Committed trial files hold no yuss text `[AC-2.5, AC-3.5]`
5. The lane stops at `rating-handoff.md`; status `In Progress — awaiting human labels (rating-handoff.md)` `[AC-3.4, AC-3.5]`
6. Story 4 waits for `labeled_by`; report committed before any removal `[AC-4.1]`
7. Each `remove` applies exactly its inventory; `rg` finds no wiring `[AC-4.2]`
8. Roadmap line, ADR-030 note, spec status match the report `[AC-4.4]`

**Business Rules:**
- Upgrade exercised only when its own trigger fires on that story
- `keep` on ≥1 valid; `remove` when exercised and none valid; not exercised + ack `remove` → `remove`; ack `amend` or missing → `unverifiable`
- Only a human labels; `valid` = real unmet AC or Critical/Major security/architecture defect at that commit
- Gate 0 removed + blind trial `keep` → skill stays with `/prototype` only

**Experience Design:**
- Entry: `/implement-spec` after the three dependencies complete
- Happy path: Stories 1–3 unattended → human labels → Story 4
- Moment of truth: `trial-report.md` `upgrade:` lines
- Feedback: `gate-upgrade-trial:` summary line; spec status while waiting
- Error: unverifiable upgrade untouched and named in status

---

## For Testing Agents

**Success Criteria:**
1. `uv run pytest` and `uv run --python 3.9 pytest` pass; outcome test skips until `trial-report.md` exists
2. Stand-in yuss HEAD, refs, `status --porcelain` identical before and after `prepare`
3. No-text scan of fixture trial files finds no diff markers or reviewer text
4. `bash scripts/eval.sh` 0 findings; `gen-platform-trees.py --check` pass after Story 4

**Shadow Paths to Verify:**
- **Happy path:** all arms recorded → sheet → labels → four decided verdicts
- **Nil input:** no trial file → exit 2
- **Empty input:** no upgrade-only findings → verdicts from acks and zero-finding `remove`
- **Upstream error:** yuss unreachable → exit 2 before any write

**Edge Cases:**
- Gate 0 removed by the blind trial before `init` → `absent`
- Both review-route upgrades removed → delete `review-override.py switch`
- `--at-parent pass` → `no_repro`, exercised, no finding

**Coverage Requirements:**
- New code: ≥80%; refusal paths: 100%

**Test Strategy:**
- Unit tests with a throwaway local git repo standing in for yuss; outcome test stdlib only, no harness import
