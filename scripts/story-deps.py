#!/usr/bin/env python3
"""Fail-closed story-dependency parser and graph validator.

This is the executable reference for the authoritative story-level
`> **Dependencies:** ...` contract consumed by `/implement-spec` before it
computes parallel worktree batches. It is deliberately narrow: it parses
only the story-level header on files under `<spec-dir>/user-stories/` and
never touches the spec-level cross-spec header, which is `spec-deps.py`'s
separate contract.

Subcommand:
  validate --spec-dir PATH
             Build the story dependency graph for one spec folder, validate
             it, and emit deterministic topologically ordered batches.

`--spec-dir` points at **one** spec folder (e.g. `.writ/specs/<spec-id>`),
deliberately distinct from `spec-deps.py`'s `--specs-dir`, which points at
the `.writ/specs/` root. The near-collision is intentional — the flags name
different things at different scopes, and unifying them would blur that.

Success prints a JSON object and exits 0. A contract violation prints a JSON
object with a `blocker` of {code, summary} and exits non-zero — the exact
`ContractError`/`_fail` shape `spec-deps.py` uses, verbatim. Nothing is ever
mutated; this helper is read-only.

Graph validity is blocking, unlike the sibling `story-context.py` assembler,
which always exits 0 and degrades instead. The asymmetry is deliberate: an
invalid story graph corrupts parallel worktree execution order and must halt
before any batch is computed, while thin context is still judged by the
review and testing gates that run afterward.
"""

from __future__ import annotations

import argparse
import json
import re
import sys
from pathlib import Path
from typing import Any


SCHEMA = "story-graph/v1"

# Story files are named story-N-slug.md.
STORY_FILE = re.compile(r"^story-(\d+)-")
# The one authoritative header form for story-level dependencies.
HEADER_LINE = re.compile(r"(?m)^> \*\*Dependencies:\*\* (.+)$")
NONE_VALUE = re.compile(r"(?i)^none\b")
PARENTHETICAL = re.compile(r"\([^)]*\)")
LIST_SEPARATOR = re.compile(r",|\band\b", re.IGNORECASE)
# Accepts "Story 1", "story-1", "Stories 1" (singular/plural prefix).
SINGLE_TOKEN = re.compile(r"(?i)^stor(?:y|ies)[\s-]*(\d+)$")
# Accepts "Stories 1-3" / "Stories 1–3" (hyphen or en/em dash range).
RANGE_TOKEN = re.compile(r"(?i)^stor(?:y|ies)[\s-]*(\d+)\s*[-\u2013\u2014]\s*(\d+)$")
# A bare number continuing a preceding "Stories" list, e.g. the "3" in
# "Stories 1, 2, 3".
BARE_NUMBER = re.compile(r"^(\d+)$")


class ContractError(Exception):
    def __init__(self, code: str, summary: str) -> None:
        super().__init__(summary)
        self.code = code
        self.summary = summary


def _fail(err: ContractError) -> None:
    print(json.dumps({"blocker": {"code": err.code, "summary": err.summary}}))
    raise SystemExit(1)


def story_number(story_id: str) -> int:
    match = re.match(r"^story-(\d+)$", story_id)
    if not match:
        raise ContractError("malformed_dependencies", f"unparseable story id: {story_id!r}")
    return int(match.group(1))


def story_id_from_path(path: Path) -> str:
    match = STORY_FILE.match(path.name)
    if not match:
        raise ContractError("malformed_dependencies", f"unparseable story filename: {path.name}")
    return f"story-{match.group(1)}"


def parse_dependencies(text: str, story_id: str) -> list[str]:
    """Return the declared dependency story IDs for one story body.

    Legacy absence (no header at all) is `[]` — legacy stories are valid,
    not errors. `None` (case-insensitive), including an annotated form like
    `None (independent of Story 3)`, is a real declaration of no
    dependencies and is also `[]`.

    Otherwise the value must resolve to a list of story numbers: singular or
    plural `Story`/`Stories` prefixes, `,` or `and` as separators, a bare
    number continuing a preceding `Stories` list (`Stories 1, 2, 3`), a
    hyphen/en-dash range (`Stories 1-3`), and a trailing parenthetical
    annotation on any token are all accepted — this is the real-world
    prose observed across every existing spec's story files, not just the
    minimal `Story N` form. Anything that doesn't resolve to at least one
    story number is a blocking `malformed_dependencies` error, so a genuine
    typo (`Story ???`) still fails closed.
    """
    match = HEADER_LINE.search(text)
    if match is None:
        return []

    raw = match.group(1).strip()
    if NONE_VALUE.match(raw):
        return []

    working = PARENTHETICAL.sub("", raw)
    numbers: list[int] = []
    for segment in LIST_SEPARATOR.split(working):
        value = segment.strip()
        if not value:
            raise ContractError(
                "malformed_dependencies",
                f"{story_id}: unparseable Dependencies value {raw!r} (empty list entry)",
            )

        range_match = RANGE_TOKEN.match(value)
        if range_match:
            low, high = int(range_match.group(1)), int(range_match.group(2))
            if low > high:
                raise ContractError(
                    "malformed_dependencies",
                    f"{story_id}: invalid story range {value!r} in {raw!r}",
                )
            numbers.extend(range(low, high + 1))
            continue

        single_match = SINGLE_TOKEN.match(value)
        if single_match:
            numbers.append(int(single_match.group(1)))
            continue

        bare_match = BARE_NUMBER.match(value)
        if bare_match and numbers:
            numbers.append(int(bare_match.group(1)))
            continue

        raise ContractError(
            "malformed_dependencies",
            f"{story_id}: unparseable Dependencies value {raw!r}",
        )

    return [f"story-{number}" for number in numbers]


def build_graph(spec_dir: Path) -> dict[str, list[str]]:
    """Read every story file under `<spec_dir>/user-stories/` into a graph.

    A story file that cannot be read is treated as a missing reference —
    the failure is surfaced against the story that could not be verified,
    since anything depending on it can never be validated either.
    """
    story_dir = spec_dir / "user-stories"
    story_files = sorted(story_dir.glob("story-*.md"))
    if not story_files:
        raise ContractError("no_stories_found", f"no story files found under {story_dir}")

    graph: dict[str, list[str]] = {}
    for story_file in story_files:
        story_id = story_id_from_path(story_file)
        if story_id in graph:
            raise ContractError(
                "malformed_dependencies",
                f"{story_id}: duplicate story file {story_file.name} collides with"
                " an earlier story number",
            )
        try:
            text = story_file.read_text(encoding="utf-8")
        except (OSError, UnicodeError) as exc:
            raise ContractError(
                "missing_reference",
                f"{story_id}: story file unreadable ({exc}); treated as a missing"
                " reference target",
            ) from exc
        graph[story_id] = parse_dependencies(text, story_id)
    return graph


def _find_cycle(graph: dict[str, list[str]]) -> list[str] | None:
    """Return the first cycle found as an ordered path, or `None` if acyclic.

    Standard three-color DFS (white/gray/black): a story goes gray on entry
    to the current recursion stack and black once every dependency below it
    is resolved. Hitting a gray story means the traversal has looped back
    onto its own stack, so the cycle path is reconstructed by slicing the
    stack from that story's position and closing the loop back onto it —
    this is what lets the caller report the full cycle (e.g.
    `story-1 -> story-2 -> story-3 -> story-1`) rather than just "a cycle
    exists somewhere." Missing references are not cycles and are skipped
    here; `validate_graph` diagnoses them separately as
    `missing_reference`.
    """
    WHITE, GRAY, BLACK = 0, 1, 2
    color = {story: WHITE for story in graph}
    stack: list[str] = []

    def visit(story: str) -> list[str] | None:
        color[story] = GRAY
        stack.append(story)
        for dep in graph.get(story, []):
            if dep not in color:
                continue  # missing refs are diagnosed separately
            if color[dep] == GRAY:
                return stack[stack.index(dep):] + [dep]
            if color[dep] == WHITE:
                found = visit(dep)
                if found:
                    return found
        stack.pop()
        color[story] = BLACK
        return None

    for story in sorted(graph, key=story_number):
        if color[story] == WHITE:
            found = visit(story)
            if found:
                return found
    return None


def _batches(graph: dict[str, list[str]]) -> list[list[str]]:
    """Deterministic topological batches, tie-broken by numeric story number.

    A naive lexicographic sort on the string ID would misorder story-10
    before story-2, so the tie-break key is the extracted integer, not the
    ID string.
    """
    remaining = {story: set(deps) for story, deps in graph.items()}
    batches: list[list[str]] = []
    while remaining:
        ready = sorted(
            (story for story, deps in remaining.items() if not deps),
            key=story_number,
        )
        if not ready:
            cycle = _find_cycle({story: sorted(deps, key=story_number) for story, deps in remaining.items()})
            summary = (
                "story cycle: " + " -> ".join(cycle)
                if cycle
                else "unresolved cycle among: " + ", ".join(sorted(remaining, key=story_number))
            )
            raise ContractError("dependency_cycle", summary)
        batches.append(ready)
        for story in ready:
            del remaining[story]
        for deps in remaining.values():
            deps.difference_update(ready)
    return batches


def validate_graph(graph: dict[str, list[str]]) -> dict[str, Any]:
    """Validate an already-parsed story graph and return deterministic batches.

    Structural checks (self-reference, duplicate-reference, missing
    reference) and the cycle/batch computation are independent of how the
    graph was built, so callers that already have their own parsed
    dependency map — `recommend-state.py`'s `validate_dag()` — can reuse
    this directly instead of re-reading story files from disk.
    """
    known = set(graph)
    for story in sorted(graph, key=story_number):
        deps = graph[story]
        if story in deps:
            raise ContractError("self_reference", f"{story}: a story cannot depend on itself")
        seen: set[str] = set()
        for dep in deps:
            if dep in seen:
                raise ContractError(
                    "duplicate_reference",
                    f"{story}: duplicate dependency {dep!r} (dedupe while preserving"
                    " first-occurrence order)",
                )
            seen.add(dep)
        for dep in deps:
            if dep not in known:
                raise ContractError(
                    "missing_reference",
                    f"{story}: depends on unknown story {dep!r} (no story file for it)",
                )

    batches = _batches(graph)
    return {
        "schema": SCHEMA,
        "status": "ok",
        "batches": batches,
        "graph": {story: graph[story] for story in sorted(graph, key=story_number)},
    }


def validate(spec_dir: Path) -> dict[str, Any]:
    graph = build_graph(spec_dir)
    return validate_graph(graph)


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    sub = parser.add_subparsers(dest="command", required=True)

    p_val = sub.add_parser("validate", help="validate one spec's story dependency graph")
    p_val.add_argument("--spec-dir", required=True, type=Path)

    args = parser.parse_args(argv)

    try:
        if args.command == "validate":
            print(json.dumps(validate(args.spec_dir)))
    except ContractError as err:
        _fail(err)
    return 0


if __name__ == "__main__":
    sys.exit(main())
