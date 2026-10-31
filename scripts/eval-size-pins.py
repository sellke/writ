#!/usr/bin/env python3
"""Find byte caps on command files pinned outside KNOWN_OVER_BUDGET.

eval.sh's `size-pins` check (retro `.writ/retros/2026-10-30-phase-15.md` F9).
A command file's size cap lives in one place: KNOWN_OVER_BUDGET in
`scripts/tests/test_governor_enforcement.py`, with COMMAND_BYTE_BUDGET in
`scripts/eval-leanness.py` holding every file not listed there. A cap pinned
in another test module is a second pin that the next spec to touch the file
trips without knowing it exists.

Scans the top-level `scripts/tests/test_*.py` and `test_*.sh` files except
the registry. A Python pin is an upper-bound comparison (`<`, `<=`, `>`,
`>=`, assertLess, assertLessEqual, assertGreater, assertGreaterEqual) whose
bounded side measures a file's bytes (`len(p.read_bytes())`,
`p.stat().st_size`, `os.path.getsize(p)`, a local name holding one, or a
helper function that returns one) where `p` resolves, through the module's
assignments, to a `commands/<name>.md` path. A shell pin is a `wc -c` or
`stat` size of a `commands/<name>.md` path compared with -lt, -le, -gt, or
-ge. Hashes, equality checks, floors, and other files are not pins.

Usage: python3 scripts/eval-size-pins.py [--root DIR]

Prints the ADR-029 check shape: line 1 `pass`, `fail`, or `unverifiable`
(a test module that does not parse), one `reason: <path>:<line> ...` line
per pin or unparsable module, and the summary `size-pins: ...` last.
Exit 0 pass or unverifiable, 1 fail, 2 usage error (no scripts/tests).
"""

from __future__ import annotations

import argparse
import ast
import re
import sys
from pathlib import Path
from typing import Dict, List, NamedTuple, Optional, Tuple

REGISTRY = "test_governor_enforcement.py"
COMMAND_PATH = re.compile(r"""commands['"]?\)*\s*(?:/|,)\s*\(*['"]?([A-Za-z0-9_.-]+\.md)\b""")
IDENT = re.compile(r"[A-Za-z_][A-Za-z0-9_]*")
CAP_ASSERTS = {"assertLess": 0, "assertLessEqual": 0, "assertGreater": 1, "assertGreaterEqual": 1}
FIX = "KNOWN_OVER_BUDGET in scripts/tests/%s is the only cap" % REGISTRY

SH_ASSIGN = re.compile(r"^\s*(?:local\s+|export\s+|readonly\s+)?([A-Za-z_][A-Za-z0-9_]*)=(.*)$")
SH_MEASURE = re.compile(r"\bwc\s+-c\b|\bstat\s+(?:-f\s*%z|-c\s*%s)")
SH_COMPARE = re.compile(r"\s-(?:lt|le|gt|ge)\s")
SH_VAR = re.compile(r"\$\{?([A-Za-z_][A-Za-z0-9_]*)\}?")


class Pin(NamedTuple):
    rel: str
    line: int
    command: str


class Unparsable(NamedTuple):
    rel: str
    line: int
    error: str


def command_of(text: str, names: Dict[str, str]) -> Optional[str]:
    """`commands/<name>.md` when `text`, its names expanded, is a command path."""
    for _ in range(6):
        match = COMMAND_PATH.search(text)
        if match:
            return "commands/" + match.group(1)
        expanded = IDENT.sub(lambda m: "(%s)" % names[m.group(0)] if m.group(0) in names
                             else m.group(0), text)
        if expanded == text:
            return None
        text = expanded
    return None


class Module:
    """One parsed test module: its names, helper measurers, and pins."""

    def __init__(self, source: str, rel: str) -> None:
        self.source = source
        self.rel = rel
        self.tree = ast.parse(source)
        self.names = self.assignments(self.tree.body)
        for node in self.tree.body:
            if isinstance(node, ast.ClassDef):
                self.names.update(self.assignments(node.body))
        # helper name -> (parameter names, measured-path source)
        self.measurers: Dict[str, Tuple[List[str], str]] = {}
        for node in ast.walk(self.tree):
            if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
                local = self.measured_locals(node)
                for sub in ast.walk(node):
                    if isinstance(sub, ast.Return) and sub.value is not None:
                        target = self.measured(sub.value, local)
                        if target is not None:
                            self.measurers[node.name] = ([a.arg for a in node.args.args], target)

    def segment(self, node: ast.AST) -> str:
        return ast.get_source_segment(self.source, node) or ""

    def assignments(self, body: List[ast.stmt]) -> Dict[str, str]:
        names: Dict[str, str] = {}
        for node in body:
            if isinstance(node, ast.Assign) and len(node.targets) == 1 \
                    and isinstance(node.targets[0], ast.Name):
                names[node.targets[0].id] = self.segment(node.value)
            elif isinstance(node, ast.AnnAssign) and isinstance(node.target, ast.Name) \
                    and node.value is not None:
                names[node.target.id] = self.segment(node.value)
        return names

    def measured_locals(self, scope: ast.AST) -> Dict[str, str]:
        local: Dict[str, str] = {}
        for node in ast.walk(scope):
            if isinstance(node, ast.Assign) and len(node.targets) == 1 \
                    and isinstance(node.targets[0], ast.Name):
                target = self.measured(node.value, local)
                if target is not None:
                    local[node.targets[0].id] = target
        return local

    def measured(self, node: ast.AST, local: Dict[str, str]) -> Optional[str]:
        """Source of the path whose byte size `node` is, else None."""
        if isinstance(node, ast.Name):
            return local.get(node.id)
        if isinstance(node, ast.BinOp):
            return self.measured(node.left, local) or self.measured(node.right, local)
        if isinstance(node, ast.Attribute) and node.attr == "st_size":
            value = node.value
            if isinstance(value, ast.Call) and isinstance(value.func, ast.Attribute) \
                    and value.func.attr in ("stat", "lstat"):
                return self.segment(value.func.value)
            return None
        if not isinstance(node, ast.Call):
            return None
        func = node.func
        if isinstance(func, ast.Name) and func.id == "len" and len(node.args) == 1:
            inner = node.args[0]
            if isinstance(inner, ast.Call) and isinstance(inner.func, ast.Attribute) \
                    and inner.func.attr == "read_bytes":
                return self.segment(inner.func.value)
            return None
        if isinstance(func, ast.Attribute) and func.attr == "getsize" and node.args:
            return self.segment(node.args[0])
        name = func.attr if isinstance(func, ast.Attribute) else \
            func.id if isinstance(func, ast.Name) else None
        if name in getattr(self, "measurers", {}):
            params, target = self.measurers[name]
            if isinstance(func, ast.Attribute) and params[:1] in (["self"], ["cls"]):
                params = params[1:]
            for param, arg in zip(params, node.args):
                target = re.sub(r"\b%s\b" % re.escape(param), "(%s)" % self.segment(arg), target)
            return target
        return None

    def capped(self, node: ast.AST, local: Dict[str, str]) -> Optional[str]:
        """The measured path when `node` puts an upper bound on a byte size."""
        if isinstance(node, ast.Compare):
            operands = [node.left] + list(node.comparators)
            for index, op in enumerate(node.ops):
                if isinstance(op, (ast.Lt, ast.LtE)):
                    bounded = operands[index]
                elif isinstance(op, (ast.Gt, ast.GtE)):
                    bounded = operands[index + 1]
                else:
                    continue
                target = self.measured(bounded, local)
                if target is not None:
                    return target
            return None
        if isinstance(node, ast.Call) and isinstance(node.func, ast.Attribute) \
                and node.func.attr in CAP_ASSERTS and len(node.args) >= 2:
            return self.measured(node.args[CAP_ASSERTS[node.func.attr]], local)
        return None

    def pins(self) -> List[Pin]:
        scopes: List[Tuple[List[ast.AST], Dict[str, str]]] = []
        top = [n for n in self.tree.body
               if not isinstance(n, (ast.FunctionDef, ast.AsyncFunctionDef, ast.ClassDef))]
        scopes.append((top, {}))
        for node in ast.walk(self.tree):
            if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
                scopes.append(([node], self.measured_locals(node)))
        found: Dict[int, Pin] = {}
        for roots, local in scopes:
            names = dict(self.names)
            for root in roots:
                if isinstance(root, (ast.FunctionDef, ast.AsyncFunctionDef)):
                    names.update(self.assignments(list(ast.walk(root))[1:]))  # type: ignore[arg-type]
            for root in roots:
                for node in ast.walk(root):
                    target = self.capped(node, local)
                    if target is None:
                        continue
                    command = command_of(target, names)
                    if command is not None:
                        line = getattr(node, "lineno", 0)
                        found.setdefault(line, Pin(self.rel, line, command))
        return [found[line] for line in sorted(found)]


def shell_pins(source: str, rel: str) -> List[Pin]:
    lines = source.splitlines()
    names: Dict[str, str] = {}
    for line in lines:
        match = SH_ASSIGN.match(line)
        if match:
            names[match.group(1)] = match.group(2).strip().strip("\"'")
    pins: Dict[int, Pin] = {}
    for index, line in enumerate(lines):
        if not SH_MEASURE.search(line):
            continue
        expanded = line
        for _ in range(6):
            expanded = SH_VAR.sub(lambda m: names.get(m.group(1), m.group(0)), expanded)
        match = COMMAND_PATH.search(expanded)
        if match is None:
            continue
        command = "commands/" + match.group(1)
        if SH_COMPARE.search(line):
            pins.setdefault(index + 1, Pin(rel, index + 1, command))
            continue
        assigned = SH_ASSIGN.match(line)
        if assigned is None:
            continue
        var = re.escape(assigned.group(1))
        compare = re.compile(r"\$\{?%s\}?\"?\s+-(?:lt|le)\b|-(?:gt|ge)\s+\"?\$\{?%s\b"
                             r"|\(\(.*\b%s\b\s*<" % (var, var, var))
        for later in range(index + 1, len(lines)):
            if compare.search(lines[later]):
                pins.setdefault(later + 1, Pin(rel, later + 1, command))
    return [pins[line] for line in sorted(pins)]


def scan(root: Path) -> Tuple[List[Pin], List[Unparsable], int]:
    tests = root / "scripts" / "tests"
    files = sorted(p for p in tests.glob("test_*.py") if p.name != REGISTRY) + \
        sorted(tests.glob("test_*.sh"))
    pins: List[Pin] = []
    broken: List[Unparsable] = []
    for path in files:
        rel = path.relative_to(root).as_posix()
        source = path.read_text(encoding="utf-8", errors="replace")
        if path.suffix == ".sh":
            pins.extend(shell_pins(source, rel))
            continue
        try:
            pins.extend(Module(source, rel).pins())
        except SyntaxError as exc:
            broken.append(Unparsable(rel, exc.lineno or 1, exc.msg or "syntax error"))
    return pins, broken, len(files)


def plural(count: int, word: str) -> str:
    return "%d %s%s" % (count, word, "" if count == 1 else "s")


def main(argv: Optional[List[str]] = None) -> int:
    parser = argparse.ArgumentParser(prog="eval-size-pins.py", description=__doc__,
                                     formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--root", type=Path, default=Path(__file__).resolve().parents[1],
                        help="repository root (default: this script's repository)")
    args = parser.parse_args(argv)
    if not (args.root / "scripts" / "tests").is_dir():
        sys.stderr.write("eval-size-pins: no scripts/tests directory under %s\n" % args.root)
        return 2

    pins, broken, scanned = scan(args.root)
    verdict = "fail" if pins else "unverifiable" if broken else "pass"
    print(verdict)
    for pin in pins:
        print("reason: %s:%d pins a byte cap on %s; %s" % (pin.rel, pin.line, pin.command, FIX))
    for item in broken:
        print("reason: %s:%d cannot be parsed (%s), so its size pins are unchecked"
              % (item.rel, item.line, item.error))
    files = len({pin.rel for pin in pins})
    detail = "%s in %s" % (plural(len(pins), "pin"), plural(files, "file")) if pins \
        else plural(0, "pin")
    if broken:
        detail += ", %d unparsable" % len(broken)
    print("size-pins: %s (%s, %s scanned)" % (verdict, detail, plural(scanned, "test file")))
    return 1 if pins else 0


if __name__ == "__main__":
    sys.exit(main())
