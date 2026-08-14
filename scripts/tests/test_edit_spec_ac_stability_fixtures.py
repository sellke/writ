#!/usr/bin/env python3
"""Golden-fixture pin for Story 4 (`edit-spec-stability-guard`) of
`2026-08-13-acceptance-criteria-traceability-ids`.

`/edit-spec` is an LLM-interpreted markdown command with no executable harness
of its own — there is no function here to call. The fixtures below are the
artifact under test: a before-state and an expected after-state, byte-for-byte,
for each of the three edit shapes `commands/edit-spec.md` Step 2.2 governs
(insert, remove, first adoption). The insert and remove pairs are transcribed
verbatim from `.writ/docs/acceptance-criteria-ids.md` → "The High-Water Mark" →
its two worked examples, so this file also pins that doc against silent drift.

This gives anyone editing that prose later a concrete, checkable definition of
"correct" to diff their new reading against, rather than only prose to re-read.

Copied verbatim rather than imported, per this story's ownership boundary:
`scripts/ac-trace.py` may not exist yet and must not become a dependency of
this file or of `commands/edit-spec.md`.
"""

from __future__ import annotations

import re

import pytest

TAG = re.compile(r"`\[((?:AC-\d+\.\d+)(?:,\s*AC-\d+\.\d+)*)\]`\s*$")
MARKER = re.compile(r"^> \*\*AC IDs assigned through:\*\* (AC-\d+\.\d+)\s*$")


def _criterion_lines(markdown: str) -> list[str]:
    return [line for line in markdown.splitlines() if line.startswith("- [")]


def _marker(markdown: str) -> str:
    for line in markdown.splitlines():
        match = MARKER.match(line)
        if match:
            return match.group(1)
    raise AssertionError(f"no marker line found in:\n{markdown}")


def _ids(line: str) -> list[str]:
    match = TAG.search(line)
    assert match, f"expected a trailing [AC-n.m] tag on: {line!r}"
    return [item.strip() for item in match.group(1).split(",")]


# ---------------------------------------------------------------------------
# Fixture 1: insert — transcribed verbatim from acceptance-criteria-ids.md's
# "Worked example — insert". Marker at AC-3.4, three criteria; a fourth is
# inserted second in reading order and takes mark+1 regardless.
# ---------------------------------------------------------------------------

INSERT_BEFORE = """\
> **AC IDs assigned through:** AC-3.4

- [ ] Given a spec with no marker, when the check runs, then it reports a marker violation. `[AC-3.1]`
- [ ] Given a criterion with no citing task, when the check runs, then it reports uncovered. `[AC-3.3]`
- [ ] Given two criteria sharing an ID, when the check runs, then it reports a duplicate. `[AC-3.4]`
"""

INSERT_AFTER = """\
> **AC IDs assigned through:** AC-3.5

- [ ] Given a spec with no marker, when the check runs, then it reports a marker violation. `[AC-3.1]`
- [ ] Given a criterion with no test citation at Completed status, when the check runs, then it reports untested. `[AC-3.5]`
- [ ] Given a criterion with no citing task, when the check runs, then it reports uncovered. `[AC-3.3]`
- [ ] Given two criteria sharing an ID, when the check runs, then it reports a duplicate. `[AC-3.4]`
"""


def test_insert_assigns_mark_plus_one_and_advances_marker() -> None:
    assert _marker(INSERT_BEFORE) == "AC-3.4"
    assert _marker(INSERT_AFTER) == "AC-3.5"

    before_lines = _criterion_lines(INSERT_BEFORE)
    after_lines = _criterion_lines(INSERT_AFTER)
    assert len(before_lines) == 3
    assert len(after_lines) == 4

    # Exactly one line is new, and it is the new mark+1 ID.
    new_lines = [line for line in after_lines if line not in before_lines]
    assert len(new_lines) == 1
    assert _ids(new_lines[0]) == ["AC-3.5"]

    # Every surviving sibling is byte-identical to its pre-edit form, and no
    # sibling's ID changed even though the new criterion landed among them.
    surviving = [line for line in after_lines if line in before_lines]
    assert surviving == before_lines


# ---------------------------------------------------------------------------
# Fixture 2: remove — continues from the insert's after-state (marker
# AC-3.5) and deletes AC-3.3, transcribed verbatim from
# acceptance-criteria-ids.md's "Worked example — delete".
# ---------------------------------------------------------------------------

REMOVE_BEFORE = INSERT_AFTER

REMOVE_AFTER = """\
> **AC IDs assigned through:** AC-3.5

- [ ] Given a spec with no marker, when the check runs, then it reports a marker violation. `[AC-3.1]`
- [ ] Given a criterion with no test citation at Completed status, when the check runs, then it reports untested. `[AC-3.5]`
- [ ] Given two criteria sharing an ID, when the check runs, then it reports a duplicate. `[AC-3.4]`
"""


def test_remove_retires_id_without_moving_marker_back() -> None:
    # The marker stays at the highest ID ever assigned — it does not fall
    # back to AC-3.4, the new highest *surviving* ID.
    assert _marker(REMOVE_BEFORE) == "AC-3.5"
    assert _marker(REMOVE_AFTER) == "AC-3.5"

    before_lines = _criterion_lines(REMOVE_BEFORE)
    after_lines = _criterion_lines(REMOVE_AFTER)
    assert len(before_lines) == 4
    assert len(after_lines) == 3

    removed = [line for line in before_lines if line not in after_lines]
    assert len(removed) == 1
    assert _ids(removed[0]) == ["AC-3.3"]

    # Every surviving line is byte-identical to its pre-edit form, and the
    # retired ID is not reassigned to anything in the after-state.
    assert after_lines == [line for line in before_lines if line != removed[0]]
    after_ids = {id_ for line in after_lines for id_ in _ids(line)}
    assert "AC-3.3" not in after_ids


# ---------------------------------------------------------------------------
# Fixture 3: first adoption — a legacy story (zero IDs, no marker) gains a
# new criterion. The partial_adoption trap: tagging only the new criterion
# would leave the two pre-existing ones untagged and blocking. Correct
# behavior tags every criterion in the story, in reading order, and creates
# the marker beneath the heading.
# ---------------------------------------------------------------------------

ADOPTION_BEFORE = """\
## Acceptance Criteria

- [ ] Given a user submits an empty form, when validation runs, then it shows an error.
- [ ] Given a user submits a valid form, when validation runs, then it saves the record.
"""

ADOPTION_AFTER = """\
## Acceptance Criteria

> **AC IDs assigned through:** AC-7.3

- [ ] Given a user submits an empty form, when validation runs, then it shows an error. `[AC-7.1]`
- [ ] Given a user submits a valid form, when validation runs, then it saves the record. `[AC-7.2]`
- [ ] Given a user double-submits a valid form, when validation runs, then it rejects the duplicate. `[AC-7.3]`
"""


def test_first_adoption_creates_marker_and_tags_every_criterion() -> None:
    before_lines = _criterion_lines(ADOPTION_BEFORE)
    after_lines = _criterion_lines(ADOPTION_AFTER)
    assert len(before_lines) == 2
    assert len(after_lines) == 3

    # No marker and no tags before adoption — this is a legacy story.
    assert not any(TAG.search(line) for line in before_lines)
    with pytest.raises(AssertionError):
        _marker(ADOPTION_BEFORE)

    # Every criterion is tagged after adoption, not just the new one —
    # the partial_adoption trap this fixture exists to close.
    assert all(TAG.search(line) for line in after_lines)
    assert _marker(ADOPTION_AFTER) == "AC-7.3"

    # The two pre-existing criteria are byte-identical apart from gaining
    # their trailing tag; reading order fixes their assigned IDs.
    before_prose = [line.rstrip() for line in before_lines]
    after_prose_untagged = [TAG.sub("", line).rstrip() for line in after_lines[:2]]
    assert before_prose == after_prose_untagged
    assert _ids(after_lines[0]) == ["AC-7.1"]
    assert _ids(after_lines[1]) == ["AC-7.2"]
    assert _ids(after_lines[2]) == ["AC-7.3"]


if __name__ == "__main__":
    raise SystemExit(pytest.main([__file__, "-v"]))
