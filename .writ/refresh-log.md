# Writ Refresh Log

> Append-only record of command improvements from `/refresh-command` analysis.

---

## 2026-03-15 — /ship refreshed

**Source transcript:** This conversation (Phase 2a implementation + shipping session)
**Signals found:** 5 total, 4 actionable
**Amendments applied:** 4 of 4 proposed

**Changes:**
- Auto-label fallback — try labels, skip gracefully if they don't exist in the repo (Confidence: High, Scope: Universal)
- Branch creation offer — when on default branch, offer to create + checkout a branch automatically instead of just telling the user (Confidence: High, Scope: Universal)
- Post-ship commit warning — warn that commits pushed after PR merge are orphaned; for follow-up changes, open a new branch (Confidence: High, Scope: Universal)
- Commit plan confirmation gate — AskQuestion before executing commit splits; restructuring git history shouldn't auto-proceed (Confidence: Medium, Scope: Universal)

**Not applied:**
- Signal 5 (positive surprise: clean 2-commit split) — behavior already implicit in splitting heuristic

**Scope:** Local only
**Target file:** commands/ship.md

---

## 2026-07-10 — /implement-phase refreshed

**Source transcript:** This conversation (Phase 7 decomposition discussion — how to turn a roadmap phase into the right set of specs)
**Signals found:** 4 total, 4 actionable
**Amendments applied:** 5 of 5 proposed

**Signals:**
- `/implement-phase` dead-ends on unspecced features ("Stop so I can run /create-spec first") — the phase→specs decomposition is left as tacit human judgment with no artifact
- Decomposition is the highest-leverage quality step (context scoping per fresh subagent, single-writer file ownership to avoid lane merge collisions, explicit seams, right-sized independently-testable specs)
- Decomposition wants just-in-time binding against the current codebase — exactly when `/implement-phase` runs — not stale plan-time boundaries
- Must stay adaptive: no value for a single unspecced feature; must not break the single-confirmation autonomy contract

**Changes:**
- Decomposition pre-pass added as new Step 1.2b — analyze → propose specs + dependency graph + file-ownership map + seams → one planning confirmation → seed `/create-spec` per proposed spec → re-resolve and continue (Confidence: High, Scope: Universal)
- "Decompose now" option added to the Step 1.2 unspecced-feature ask, recommended default for 2+ unspecced features, N=1 routed straight to one `/create-spec` (Confidence: High, Scope: Universal)
- Question Policy condition 4 (decomposition approval) added and closing "only routine interaction" line reconciled (Confidence: High, Scope: Universal)
- Overview updated to advertise the pre-pass (Confidence: Medium, Scope: Universal)
- Integration table `/create-spec` row updated to reflect per-spec invocation by the pre-pass (Confidence: Medium, Scope: Universal)

**Design boundaries honored:**
- Contract-first preserved — specs are still contract-locked per ADR-001; the pre-pass only seeds `/create-spec`, it does not auto-author specs
- `--all` mode never auto-enters the pre-pass (creating specs requires human agreement)
- Adaptive ceremony — no decomposition for a single unspecced feature

**Not applied:**
- No new invocation flags (`--decompose`/`--no-decompose`) — the in-conversation option covers control without adding surface

**Scope:** Product source (Writ repo — `commands/` is the distributable source; this ships to all Writ users, not local-only)
**Target file:** commands/implement-phase.md

---

## 2026-07-11 — /refresh-command refreshed

**Signals found:** 3 total, 2 actionable
**Amendments applied:** 1 of 2 proposed

**Changes:**
- Restore mandatory structured Evidence citation to Phase 3 (Confidence: High)
  **Evidence:**
  - Transcript: .writ/specs/2026-07-10-evidence-bound-refresh-command/spec.md
  - Observable signal: "refresh-log-format.md documented a Source transcript field that Phase 3 of the command never produced"
  - Affected section: commands/refresh-command.md → "Phase 3: Propose Amendments"

**Rejected:**
- Add a `--since` flag to auto-collect friction since the last refresh — reason: no evidence

**Scope:** Local only
**Target file:** commands/refresh-command.md

---

## 2026-07-11 — /status refreshed

**Signals found:** 2 total, 1 actionable
**Amendments applied:** 0 of 1 proposed

**Rejected:**
- Rank refresh opportunities by a per-command "friction score" — reason: no evidence

**Scope:** Local only
**Target file:** commands/status.md

## 2026-08-12 — /implement-phase refreshed

**Signals found:** 6 total, 4 actionable (2 positive, preserved unchanged)
**Amendments applied:** 3 of 4 proposed

**Changes:**

- Phase branch must not sit under `writ/phase/{phase-id}` (Confidence: High)
  **Evidence:**
  - Transcript: session `b94d98ad-caa3-49db-a1ae-d8ea5b3c3f93` (orchestrator, Phase 10 run 1)
  - Observable signal: "create-lane failed: cannot lock ref 'refs/heads/writ/phase/10/2026-08-11-autonomy-gate-classes': 'refs/heads/writ/phase/10' exists"
  - Affected section: commands/implement-phase.md → "Step 3.1: Initialize Phase State"

- Lane briefs carry context, never new scope (Confidence: High)
  **Evidence:**
  - Transcript: `tasks/a95dc9c6be95ba732.output` (UAT plan author, component-contract)
  - Observable signal: "an unauthorized fourth roadmap edit ... it invalidates retire-dead-prescription/uat-plan.md Scenario 3 step 4"
  - Affected section: commands/implement-phase.md → "Step 3.2: Per-Spec Iteration" → Inherited-answer rule

- A truncated or dropped subagent result must be re-requested, not classified (Confidence: High)
  **Evidence:**
  - Transcript: `tasks/a02d90be6309626bb.output` (Scenario 20 harness probe)
  - Observable signal: "4 of 5 subagents had their final reports dropped by the harness and needed a SendMessage follow-up to restate them"
  - Affected section: commands/implement-phase.md → "Step 3.2: Per-Spec Iteration" → item 2

**Rejected:**
- Add a `closed_unimplemented` spec status to phase-execution-v2 — reason: no evidence
  The friction is real and observed (5 specs closed on measured evidence still report `pending`, so `/status` shows them as work-in-flight). But the fix is a schema change to `phase-execution-v2` and its reducer in `scripts/phase-state.py`, not a command-file amendment. `/refresh-command` amends commands; this needs a spec. Recorded here so the signal is not lost.

**Preserved (worked well, deliberately unchanged):**
- Lane isolation: 12 specs across two runs, 0 quarantined, phase branch never touched by unverified work.
- The Step 1.2b decomposition pre-pass caught two planning defects before any code moved — `commands/new-command.md` double-claimed by two specs with opposite intent, and ADR-021's `_preamble.md` escape valve being full at 93/95 lines.

**Scope:** Local only
**Target file:** commands/implement-phase.md
