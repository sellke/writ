#!/usr/bin/env python3
"""Regression guard for Story 1 task 1.1 of
`2026-08-13-acceptance-criteria-traceability-ids`.

`scripts/recommend-state.py` parses criterion lines with two anchored
regexes (lines ~378 and ~2981). The acceptance-criterion-ID grammar
(`.writ/docs/acceptance-criteria-ids.md`) places the `[AC-N.M]` tag as a
trailing suffix specifically because a prefixed ID would break both
patterns. This test pins that assumption so a future edit to either regex,
or to the tag's placement, is caught by the suite rather than resting on a
one-time manual check reported only in prose.
"""

from __future__ import annotations

import re
import unittest

# Copied verbatim from scripts/recommend-state.py — not imported, since that
# module is out of scope for this spec and must not gain a dependency on it.
LINE_378 = re.compile(r"^- \[([ xX])\] Given ")
LINE_2981 = re.compile(r"(?m)^- \[x\] (Given .+)$")


class RecommendStateAcTagCompatTests(unittest.TestCase):
    def test_unchecked_trailing_tag_matches_line_378_only(self) -> None:
        line = "- [ ] Given a criterion no task cites, when the check runs, then it reports uncovered. `[AC-3.1]`"
        self.assertIsNotNone(LINE_378.match(line))
        self.assertIsNone(LINE_2981.search(line))

    def test_checked_trailing_tag_matches_both_patterns(self) -> None:
        line = "- [x] Given a criterion no task cites, when the check runs, then it reports uncovered. `[AC-3.1]`"
        self.assertIsNotNone(LINE_378.match(line))
        match = LINE_2981.search(line)
        self.assertIsNotNone(match)
        self.assertEqual(match.group(1), line[len("- [x] "):])

    def test_checked_multi_id_trailing_tag_matches_both_patterns(self) -> None:
        line = "- [x] Given two IDs on one line, then both defined. `[AC-3.1, AC-3.6]`"
        self.assertIsNotNone(LINE_378.match(line))
        self.assertIsNotNone(LINE_2981.search(line))

    def test_prefixed_id_would_break_line_378(self) -> None:
        line = "- [ ] `[AC-3.1]` Given a criterion no task cites, then it reports uncovered."
        self.assertIsNone(LINE_378.match(line))


if __name__ == "__main__":
    unittest.main()
