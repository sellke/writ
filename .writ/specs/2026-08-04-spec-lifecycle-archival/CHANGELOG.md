# Changelog: Spec Lifecycle & Archival

## 2026-08-04 — Amendment: Remove knowledge-evidence gate from archive eligibility

**Change type:** Modifying existing stories (business rule correction)

**What changed:** Business Rule 1 flipped from a two-signal AND-gate (complete-family status AND knowledge-ledger citation) to a single-signal check (complete-family status alone). Knowledge-ledger citation is retained as ledger enrichment — recorded on each `LEDGER.md` line when it exists, replaced with "no knowledge evidence yet" when it doesn't — but no longer blocks a move.

**Why:** Post-ship dogfooding data showed the original gate excluded 36 of 39 real Complete specs in this repo (92% exclusion rate). The gate's stated purpose — substituting for a per-spec confirmation prompt — duplicated the safety already provided by Business Rule 3's reversible `git mv` + committed audit ledger, and conflated two unrelated concerns: spec lifecycle completion (a human-declared status) versus knowledge-extraction completeness (a separate, optional authoring process). Full rationale in `spec.md` → Technical Concerns → Amendment.

**Files updated:**
- `spec.md` — Business Rule 1 rewritten (original text preserved in Technical Concerns for audit trail); Success Criterion 2 annotated; Feedback Model's confirmation-substitute language corrected; Error/Edge Experience table row updated; Detection fix section documents `Closed — Cancelled` vocabulary (no new status prefix added).
- `spec-lite.md` — Eligibility, Business Rules, Experience Design, and Edge Cases sections updated to match.
- `user-stories/README.md` — Progress table updated to reflect Stories 2 and 6 reopening (42/44 tasks).
- `user-stories/story-2-archive-sweep-mechanism.md` — ACs 1–3 rewritten; tasks 2.2/2.3 annotated ⚠️; new task 2.8 added (code + test + eval updates); "What Was Built" gets a dated amendment addendum; header reopened to "In Progress."
- `user-stories/story-6-dogfood-sweep.md` — New task 6.8 added (re-run the real sweep under the corrected rule); header reopened to "In Progress."
- `sub-specs/technical-spec.md` — Eligibility check and detection-vocabulary sections updated with amendment notes.
- `scripts/archive-sweep.py` — `eligible = complete` (was `complete and bool(evidence)`); `sweep()`'s evidence-skip branch removed; ledger writer emits "no knowledge evidence yet" for empty evidence; terminal summary simplified (no more "skipped (no knowledge evidence yet)" clause); module docstring rewritten.
- `scripts/tests/test_archive_sweep.py` — 3 assertions flipped from "Complete-without-evidence is skipped" to "Complete-without-evidence is archived with an enrichment marker"; `skipped_no_evidence` references removed (key no longer exists in output).
- `scripts/eval-archive-sweep.py` — Added `scenario_complete_without_evidence_still_archives`.
- `scripts/eval.sh` — `check_spec_lifecycle_docs`'s doc-section-header assertion updated (`## Two-Signal Archive Eligibility` → `## Archive Eligibility`).
- `commands/status.md` — `### Archive Sweep (--archive)` phase prose and sample terminal output updated to the status-alone contract.
- `.writ/docs/spec-lifecycle.md` — "Two-Signal Archive Eligibility" section renamed and rewritten to "Archive Eligibility"; status vocabulary table updated for `Closed — Cancelled`; Quick Reference note corrected.

**Verification:** `python3 -m pytest scripts/tests/test_archive_sweep.py` (10/10 passing) and `python3 scripts/eval-archive-sweep.py` (5/5 scenarios passing, including the new one) — both re-run after the code change.

**Backup:** Pre-edit snapshot at `backups/2026-08-04T18-55-18/`.

**Real-world re-run:** See Story 6's second dated "What Was Built" section for the actual mass `git mv` executed against this repo's corpus under the corrected rule.
