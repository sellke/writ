# Drift Log: Marker-Based CLAUDE.md Merge

#### [DEV-1] Bundle markers added around merge functions in update.sh
- **Severity:** Small
- **Spec said:** Story 2's tasks describe implementing `merge_claude_md` in `update.sh` mirroring `merge_agents_md`; no mention of bundle-marker comments for test extraction.
- **Implementation did:** Added `# <<< writ-merge-bundled-begin/end >>>` comments around the merge functions in `update.sh` (mirroring `install.sh`'s existing convention), enabling `scripts/tests/test_update_claude_md.sh` to `awk`-extract them the same way `test_merge_agents_md.sh`/`test_merge_claude_md.sh` do for `install.sh`.
- **Resolution:** Accepted — purely additive comments, no behavior change, keeps the two scripts' testing conventions visibly consistent.
- **Spec-lite updated:** No — spec-lite.md makes no claim about test-extraction mechanics that this contradicts; nothing to amend.
