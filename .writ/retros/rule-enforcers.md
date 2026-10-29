# Rule-to-Enforcer Table

This file lists the rules this repository follows and the check that enforces each one. `/retro` reads it to see which rules already have an enforcer, and adds a row when it applies a fix. A Proof cell names a past commit that broke the rule: the enforcer fails on that commit and passes on the commit that fixed it. A rule with Enforcer `none` is written down but not checked.

| Rule | Written in | Enforcer | Rung | Proof | Since |
|---|---|---|---|---|---|
| The suite runs on Python 3.9 | `CLAUDE.md` | `uv run --python 3.9 --with pytest pytest scripts/tests/test_ac_trace.py::CitationScanTests::test_symlink_loop_does_not_crash_the_scan` | test | 0335b291e1403b38be6305a4de8154547d92604e: fails | seed |
| Generated platform trees are never hand-edited or stale | `adapters/claude-code.md` | `python3 scripts/gen-platform-trees.py --check` | lint | ddfb17ffe9b6de163a0d9aa31b43d7e2d2e30878: fails | seed |
| Instruction files use plain prose | `skills/plain-prose/SKILL.md` | none | docs | — | seed |
