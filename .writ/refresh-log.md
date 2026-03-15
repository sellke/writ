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
