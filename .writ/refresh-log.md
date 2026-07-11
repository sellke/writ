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
