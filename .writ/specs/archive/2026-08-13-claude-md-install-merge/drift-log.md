# Drift Log: Marker-Based CLAUDE.md Merge

#### [DEV-1] Bundle markers added around merge functions in update.sh
- **Severity:** Small
- **Spec said:** Story 2's tasks describe implementing `merge_claude_md` in `update.sh` mirroring `merge_agents_md`; no mention of bundle-marker comments for test extraction.
- **Implementation did:** Added `# <<< writ-merge-bundled-begin/end >>>` comments around the merge functions in `update.sh` (mirroring `install.sh`'s existing convention), enabling `scripts/tests/test_update_claude_md.sh` to `awk`-extract them the same way `test_merge_agents_md.sh`/`test_merge_claude_md.sh` do for `install.sh`.
- **Resolution:** Accepted — purely additive comments, no behavior change, keeps the two scripts' testing conventions visibly consistent.
- **Spec-lite updated:** No — spec-lite.md makes no claim about test-extraction mechanics that this contradicts; nothing to amend.

#### [DEV-2] AC citation comments in shared test files collide across specs (release-gate finding)
- **Severity:** Small
- **Spec said:** N/A — surfaced by `/release`'s inline spec-health check (Check 3, `scripts/ac-trace.py`), not the story tasks themselves.
- **Implementation did:** Added literal `AC-1.1`–`AC-1.5` / `AC-2.1`–`AC-2.5` citation comments to `scripts/tests/test_merge_claude_md.sh` / `test_update_claude_md.sh` so this spec's own criteria show real test coverage instead of `untested_criterion` findings. Because `ac-trace.py`'s citation scan is repo-wide (not scoped to the spec folder being checked) and AC numbers are only unique *within* a spec, `AC-1.5` now also appears as a `dangling_reference` when `/verify-spec`'s checker runs against `2026-08-13-acceptance-criteria-traceability-ids` (whose own Story 1 only defines AC-1.1–AC-1.4).
- **Resolution:** Accepted — this is the identical fixture-collision category that spec's own `DEV-4` already documents (two specs sharing story-number namespaces plus a repo-global scan). Not a new defect; a known, disclosed limitation of the current checker design. A future improvement would scope the citation scan to files under or referencing the spec folder being checked.
- **Spec-lite updated:** No.
