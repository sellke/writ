#!/usr/bin/env python3
"""Fail-closed cross-spec dependency parser and graph validator.

This helper is the executable reference for the authoritative cross-spec
`Dependencies` contract consumed by `/create-spec`, `/verify-spec`, and
`/implement-phase`. It is deliberately narrow: it parses only the spec-level
`> **Dependencies:** [...]` header and never touches story-level dependency
syntax, which remains a separate contract.

Subcommands:
  parse    --spec PATH
             Emit the declared cross-spec dependency list for one spec.
  validate --specs-dir DIR [--roadmap-order a,b,c]
             Build the reachable cross-spec graph across every spec folder in
             DIR, validate it, and emit a deterministic topological order.

Success prints a JSON object and exits 0. A contract violation prints a JSON
object with a `blocker` of {code, summary} and exits non-zero. Nothing is ever
mutated; this helper is read-only.
"""

from __future__ import annotations

import argparse
import json
import re
import sys
from pathlib import Path
from typing import Any


PARSE_SCHEMA = "spec-deps-parse-v1"
GRAPH_SCHEMA = "spec-deps-graph-v1"

# Spec folder IDs are dated slugs: 2026-07-09-autonomy-ceiling.
FOLDER_ID = re.compile(r"^[A-Za-z0-9._-]+$")
# The one authoritative header form. Anything shaped like a Dependencies
# header but not matching the bracket form is malformed, not legacy-absent.
HEADER_LINE = re.compile(r"^>\s*\*\*Dependencies:\*\*\s*(.*\S)?\s*$")
BRACKET = re.compile(r"^\[(.*)\]$")


class ContractError(Exception):
    def __init__(self, code: str, summary: str) -> None:
        super().__init__(summary)
        self.code = code
        self.summary = summary


def _fail(err: ContractError) -> None:
    print(json.dumps({"blocker": {"code": err.code, "summary": err.summary}}))
    raise SystemExit(1)


def parse_header(text: str, spec_id: str) -> dict[str, Any]:
    """Return {declared, dependencies} for one spec body.

    Legacy absence is declared=False with an empty list. An empty `[]` is a
    real declaration of no dependencies. A header that exists but is not the
    canonical bracket form is a blocking `malformed_dependencies` error.
    """
    header: str | None = None
    for raw in text.splitlines():
        if HEADER_LINE.match(raw):
            header = raw
            break

    if header is None:
        return {"declared": False, "dependencies": []}

    body = HEADER_LINE.match(header).group(1)  # type: ignore[union-attr]
    if body is None:
        raise ContractError(
            "malformed_dependencies",
            f"{spec_id}: Dependencies header must use bracket form `[...]`",
        )
    body = body.strip()
    bracket = BRACKET.match(body)
    if not bracket:
        raise ContractError(
            "malformed_dependencies",
            f"{spec_id}: Dependencies must be a bracketed list, got {body!r}",
        )

    inner = bracket.group(1).strip()
    if inner == "":
        return {"declared": True, "dependencies": []}

    deps: list[str] = []
    for token in inner.split(","):
        value = token.strip()
        if value == "" or not FOLDER_ID.match(value):
            raise ContractError(
                "malformed_dependencies",
                f"{spec_id}: invalid dependency identifier {value!r}"
                " (use exact spec-folder IDs)",
            )
        deps.append(value)
    return {"declared": True, "dependencies": deps}


def parse_spec(spec_path: Path) -> dict[str, Any]:
    if not spec_path.is_file():
        raise ContractError("missing_spec", f"spec file not found: {spec_path}")
    spec_id = spec_path.parent.name
    parsed = parse_header(spec_path.read_text(encoding="utf-8"), spec_id)
    parsed["spec"] = spec_id
    parsed["schema"] = PARSE_SCHEMA
    return parsed


def _discover(specs_dir: Path) -> dict[str, list[str]]:
    """Return {spec_id: declared_dependencies} for every spec folder.

    Also enforces the per-spec rules that are local to one declaration:
    malformed headers, self-reference, and duplicate entries.
    """
    graph: dict[str, list[str]] = {}
    for spec_file in sorted(specs_dir.glob("*/spec.md")):
        spec_id = spec_file.parent.name
        parsed = parse_header(spec_file.read_text(encoding="utf-8"), spec_id)
        deps = parsed["dependencies"]

        if spec_id in deps:
            raise ContractError(
                "self_reference",
                f"{spec_id}: a spec cannot depend on itself",
            )
        seen: set[str] = set()
        for dep in deps:
            if dep in seen:
                raise ContractError(
                    "duplicate_reference",
                    f"{spec_id}: duplicate dependency {dep!r}"
                    " (dedupe while preserving first-occurrence order)",
                )
            seen.add(dep)
        graph[spec_id] = deps
    return graph


def _topo_order(graph: dict[str, list[str]], roadmap_order: list[str]) -> list[str]:
    """Deterministic topological sort.

    Independent specs (all dependencies satisfied) are released in roadmap
    order when a roadmap order is supplied, otherwise lexicographically. This
    makes the plan reproducible run-to-run.
    """
    rank = {spec: i for i, spec in enumerate(roadmap_order)}

    def tiebreak(spec: str) -> tuple[int, str]:
        return (rank.get(spec, len(rank)), spec)

    remaining = {spec: set(deps) for spec, deps in graph.items()}
    ordered: list[str] = []
    while remaining:
        ready = sorted(
            (s for s, deps in remaining.items() if not deps),
            key=tiebreak,
        )
        if not ready:
            raise ContractError(
                "dependency_cycle",
                "unresolved cycle among: " + ", ".join(sorted(remaining)),
            )
        for spec in ready:
            ordered.append(spec)
            del remaining[spec]
            for deps in remaining.values():
                deps.discard(spec)
    return ordered


def _find_cycle(graph: dict[str, list[str]]) -> list[str] | None:
    WHITE, GRAY, BLACK = 0, 1, 2
    color = {spec: WHITE for spec in graph}
    stack: list[str] = []

    def visit(spec: str) -> list[str] | None:
        color[spec] = GRAY
        stack.append(spec)
        for dep in graph.get(spec, []):
            if dep not in color:
                continue  # missing refs handled separately
            if color[dep] == GRAY:
                return stack[stack.index(dep):] + [dep]
            if color[dep] == WHITE:
                found = visit(dep)
                if found:
                    return found
        stack.pop()
        color[spec] = BLACK
        return None

    for spec in sorted(graph):
        if color[spec] == WHITE:
            found = visit(spec)
            if found:
                return found
    return None


def validate_graph(specs_dir: Path, roadmap_order: list[str]) -> dict[str, Any]:
    graph = _discover(specs_dir)
    known = set(graph)

    for spec in sorted(graph):
        for dep in graph[spec]:
            if dep not in known:
                raise ContractError(
                    "missing_reference",
                    f"{spec}: depends on unknown spec {dep!r}"
                    f" (no folder .writ/specs/{dep}/)",
                )

    cycle = _find_cycle(graph)
    if cycle:
        raise ContractError(
            "dependency_cycle",
            "cross-spec cycle: " + " -> ".join(cycle),
        )

    order = _topo_order(graph, roadmap_order)
    return {
        "schema": GRAPH_SCHEMA,
        "status": "ok",
        "order": order,
        "graph": graph,
    }


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    sub = parser.add_subparsers(dest="command", required=True)

    p_parse = sub.add_parser("parse", help="parse one spec's dependency header")
    p_parse.add_argument("--spec", required=True, type=Path)

    p_val = sub.add_parser("validate", help="validate the cross-spec graph")
    p_val.add_argument("--specs-dir", required=True, type=Path)
    p_val.add_argument("--roadmap-order", default="")

    args = parser.parse_args(argv)

    try:
        if args.command == "parse":
            print(json.dumps(parse_spec(args.spec)))
        elif args.command == "validate":
            roadmap = [s.strip() for s in args.roadmap_order.split(",") if s.strip()]
            print(json.dumps(validate_graph(args.specs_dir, roadmap)))
    except ContractError as err:
        _fail(err)
    return 0


if __name__ == "__main__":
    sys.exit(main())
