#!/usr/bin/env python3
"""Generate claude-code/CLAUDE.md from the Claude Code capability map, after
checking .writ/manifest.yaml.

    python3 scripts/gen-claude-md.py           # write claude-code/CLAUDE.md
    python3 scripts/gen-claude-md.py --check   # compare with the committed file, write nothing

Dev-only (installed projects have no manifest); never hand-edit the template.
The template lists no commands and no agents: Claude Code's skill listing
shows each `.claude/commands/*.md` and its Agent tool shows each agent's
description every session, so repeating them here only costs context. The
manifest is still read so the Pipeline section names real commands.
The `{capability_map}` slot after the Commands section (spec
`2026-10-22-generated-platform-trees`, Rule 7) is filled by
`capability_map("claude-code", root)` from scripts/gen-platform-trees.py,
loaded by path because its name has a hyphen; it renders
adapters/claude-code.md's tool table. `python3 scripts/gen-platform-trees.py`
runs this generator after the adapters and every sub-generator check.

Check shape: line 1 `pass`/`fail`/`unverifiable`, `reason:` lines, `wrote
claude-code/CLAUDE.md` after a write, then `gen-claude-md: <verdict>
(<detail>)`. Reasons: `manifest <detail>`, `import-token capability-map`
(`@` outside backticks in the map), `pipeline <name>`, `capability-map
<reason>` (the adapter table did not parse: `malformed adapters/claude-code.md:<line>`,
`empty …`, `section <heading> in …`), `write <error>`; --check adds
`stale|absent claude-code/CLAUDE.md`. A missing input (the manifest, the
driver, or the adapter) is `unverifiable`. Exit 0 pass or unverifiable, 1 fail, 2 usage. Nothing is
written when any reason exists.
"""

from __future__ import annotations

import argparse
import importlib.util
import os
import re
import sys
import tempfile
from pathlib import Path
from typing import Dict, List, Optional, Tuple

ROOT = Path(__file__).resolve().parents[1]
MANIFEST_REL = ".writ/manifest.yaml"
TREES_REL = "scripts/gen-platform-trees.py"
ADAPTER_REL = "adapters/claude-code.md"
PLATFORM = "claude-code"
OUT_REL = "claude-code/CLAUDE.md"
PIPELINE = ("plan-product", "create-spec", "implement-spec", "verify-spec", "release")
PHASE = "implement-phase"
NAME_RE = re.compile(r"[a-z0-9][a-z0-9-]*\Z")
CODE_SPAN = re.compile(r"(`+).*?\1")
Pairs = List[Tuple[str, str]]

TEMPLATE = """# Writ

You are **Writ** — a methodical AI development partner. You organize all work in `.writ/` folders.

Writ's root contract (Prime Directive, interaction rules, model tiers) loads from this import:

@.claude/system-instructions.md

## Commands

Start with `/writ "<what you want>"`: it restates the request and routes it to the right command.

Writ commands live in `.claude/commands/` and its subagents in `.claude/agents/`; Claude Code lists both every session. To run a command, read its file and follow its workflow.

{capability_map}
## Pipeline

```
{pipeline}
```

`/{phase}` runs `/implement-spec` once per spec in a roadmap phase.

## Principles

- **Contract-first**: Establish agreement before creating files
- **TDD**: Tests first, then implementation
- **Challenge assumptions**: Push back on bad ideas with evidence
- **Commit incrementally**: Small commits, not big bangs
"""


def parse_value(raw: str) -> Optional[str]:
    """A one-line YAML scalar, quoted or bare. None for a broken quote."""
    raw = raw.strip()
    if raw.startswith('"'):
        m = re.match(r'"((?:[^"\\]|\\.)*)"\s*(#.*)?\Z', raw)
        return re.sub(r'\\(["\\])', r"\1", m.group(1)) if m else None
    if raw.startswith("'"):
        m = re.match(r"'((?:[^']|'')*)'\s*(#.*)?\Z", raw)
        return m.group(1).replace("''", "'") if m else None
    return re.sub(r"\s+#.*\Z", "", raw).strip()


def read_commands(text: str) -> Tuple[Pairs, List[str]]:
    """(name, purpose) per `commands:` entry, plus `manifest <detail>` reasons."""
    lines = text.splitlines()
    start = next((i for i, l in enumerate(lines) if re.match(r"commands:\s*(#.*)?\Z", l)), None)
    if start is None:
        return [], ["manifest no commands section"]
    entries: List[Dict[str, Optional[str]]] = []
    for line in lines[start + 1:]:
        if line.strip() and not line[0].isspace() and not line.startswith("#"):
            break
        m = re.match(r"  - name:(.*)\Z", line)
        if m:
            entries.append({"name": parse_value(m.group(1))})
            continue
        m = re.match(r"    ([A-Za-z_][\w-]*):(.*)\Z", line)
        if m and entries:
            entries[-1].setdefault(m.group(1), parse_value(m.group(2)))
    if not entries:
        return [], ["manifest no commands"]
    commands: Pairs = []
    reasons: List[str] = []
    for entry in entries:
        name = entry["name"] or ""
        if not NAME_RE.match(name):
            reasons.append("manifest bad name %s" % (name or '""'))
            continue
        missing = [k for k in ("file", "purpose") if not entry.get(k)]
        reasons += ["manifest %s missing %s" % (name, k) for k in missing]
        if "file" not in missing and entry["file"] != "commands/%s.md" % name:
            reasons.append("manifest %s file %s" % (name, entry["file"]))
        if name in dict(commands):
            reasons.append("manifest duplicate %s" % name)
        commands.append((name, entry.get("purpose") or ""))
    return commands, reasons


def read_capability_map(root: Path) -> Tuple[str, List[str]]:
    """(the Claude Code `## Capability Map` section rendered by
    scripts/gen-platform-trees.py, `capability-map <reason>` reasons when the
    adapter table did not parse)."""
    spec = importlib.util.spec_from_file_location("gen_platform_trees", root / TREES_REL)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)  # type: ignore[union-attr]
    try:
        return module.capability_map(PLATFORM, root), []
    except ValueError as err:
        return "", ["capability-map " + reason for reason in str(err).split("; ")]


def render(capability_map: str) -> str:
    """The template bytes: LF only, one final newline; the map section (one
    trailing newline) sits in its slot after the Commands section."""
    pipeline = " → ".join("/" + name for name in PIPELINE)
    return TEMPLATE.format(capability_map=capability_map, pipeline=pipeline, phase=PHASE)


def render_reasons(commands: Pairs, capability_map: str = "") -> List[str]:
    """`import-token` for an `@` outside backticks in the map; `pipeline` for
    a name not in the manifest."""
    reasons = []  # type: List[str]
    if "@" in CODE_SPAN.sub("", capability_map):
        reasons.append("import-token capability-map")
    names = {name for name, _ in commands}
    return reasons + ["pipeline %s" % n for n in PIPELINE + (PHASE,) if names and n not in names]


def finish(verdict: str, reasons: List[str], detail: str, wrote: Tuple[str, ...] = ()) -> int:
    print(verdict)
    for reason in reasons:
        print("reason: " + reason)
    for path in wrote:
        print("wrote " + path)
    print("gen-claude-md: %s (%s)" % (verdict, detail))
    return 1 if verdict == "fail" else 0


def check(out: Path, text: str, detail: str) -> int:
    if not out.is_file():
        return finish("fail", ["absent " + OUT_REL], "1 absent")
    if out.read_bytes() != text.encode("utf-8"):
        return finish("fail", ["stale " + OUT_REL], "1 stale")
    return finish("pass", [], detail)


def write(out: Path, text: str, detail: str) -> int:
    """Write a temp file next to the template, then os.replace it over the template."""
    mode = out.stat().st_mode & 0o777 if out.is_file() else 0o644
    tmp = None
    try:
        fd, tmp = tempfile.mkstemp(dir=str(out.parent), prefix=".CLAUDE.md.")
        with os.fdopen(fd, "wb") as handle:
            handle.write(text.encode("utf-8"))
        os.chmod(tmp, mode)
        os.replace(tmp, str(out))
    except OSError as err:
        if tmp and os.path.exists(tmp):
            os.unlink(tmp)
        return finish("fail", ["write %s" % err], "1 write")
    return finish("pass", [], detail, (OUT_REL,))


def main(argv: Optional[List[str]] = None, root: Path = ROOT) -> int:
    parser = argparse.ArgumentParser(
        prog="gen-claude-md.py", allow_abbrev=False,
        description="Generate or check claude-code/CLAUDE.md from .writ/manifest.yaml "
                    "and adapters/claude-code.md. Dev-only; never shipped.")
    parser.add_argument("--check", action="store_true",
                        help="compare with the committed file, write nothing; exit 0 pass, 1 fail")
    args = parser.parse_args(argv)

    unverifiable = []
    try:
        manifest = (root / MANIFEST_REL).read_text(encoding="utf-8")
    except (OSError, UnicodeDecodeError):
        unverifiable.append("manifest missing: " + MANIFEST_REL)
    if not (root / TREES_REL).is_file():
        unverifiable.append("platform-trees missing: " + TREES_REL)
    if not (root / ADAPTER_REL).is_file():
        unverifiable.append("adapter missing: " + ADAPTER_REL)
    if unverifiable:
        return finish("unverifiable", unverifiable, "inputs missing")

    commands, reasons = read_commands(manifest)
    capability_map, map_reasons = read_capability_map(root)
    reasons += map_reasons + render_reasons(commands, capability_map)
    if reasons:
        kinds = [r.split(" ", 1)[0] for r in reasons]
        return finish("fail", reasons, ", ".join(
            "%d %s" % (kinds.count(k), k) for k in dict.fromkeys(kinds)))
    text = render(capability_map)
    detail = "%d commands" % len(commands)
    out = root / OUT_REL
    if args.check:
        return check(out, text, detail)
    return write(out, text, detail)


if __name__ == "__main__":
    try:
        sys.exit(main())
    except BrokenPipeError:
        sys.exit(0)
