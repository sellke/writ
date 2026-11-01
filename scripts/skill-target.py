#!/usr/bin/env python3
"""Say where `/new-skill` writes a skill, and whether its name is free.

`/new-skill` runs in two kinds of project. The Writ source repository has
`.writ/manifest.yaml`; a project that got Writ from `install.sh` or a plugin
has none, and keeps the installed commands, agents, and skills in platform
folders. This script decides which kind of project it is in and checks the
name against what that project has. It writes nothing.

Subcommand:
  check <name> --platform {claude,cursor,codex} [--project DIR]

Source mode (`DIR/.writ/manifest.yaml` exists): a name is taken by an entry
under the manifest's `commands:`, `agents:`, or `skills:` list, or by a
folder `skills/<name>`. The target is `skills/<name>/SKILL.md`.

Installed mode (no manifest): a name is taken by a file `<name>.md` in the
platform's commands folder, a file `<name>.md` or `<name>.toml` in its agents
folder, or a folder `<name>` in its skills folder (PLATFORMS). When the
script runs from a Claude Code plugin (its parent folder holds
`.claude-plugin/plugin.json`), the plugin's `commands/`, `agents/`, and
`skills/` count too, named by absolute path. The target is
`<skills folder>/<name>/SKILL.md`. With no commands folder and no plugin there
is nothing to check against: `unverifiable`, usually a wrong `--platform`.

A name must match ^[a-z][a-z0-9-]*$.

Output (check shape; project paths are relative to DIR):
  pass | fail | unverifiable
  reason: name <name> is not kebab-case
  reason: name taken by <command|agent|skill> <path>      one per match
  reason: no <commands folder>/ and not run from a plugin; check --platform
  mode: source | installed <platform>
  target: <path of the SKILL.md to write>
  manifest: .writ/manifest.yaml | none
  skill-target: <verdict> (<mode>, <n> taken)

Exit 0: pass or unverifiable. Exit 1: fail. Exit 2: usage, or `--project` is
not a directory.
"""

from __future__ import annotations

import argparse
import re
import sys
from pathlib import Path
from typing import List, Optional, Tuple

MANIFEST_REL = ".writ/manifest.yaml"
NAME = re.compile(r"^[a-z][a-z0-9-]*$")
# platform -> (commands folder, agents folder, skills folder), as install.sh lays them out.
PLATFORMS = {
    "claude": (".claude/commands", ".claude/agents", ".claude/skills"),
    "cursor": (".cursor/commands", ".cursor/agents", ".cursor/skills"),
    "codex": (".codex/commands", ".codex/agents", ".agents/skills"),
}
MANIFEST_KINDS = {"commands": "command", "agents": "agent", "skills": "skill"}
TOP_KEY = re.compile(r"^([A-Za-z_]+):")
ENTRY_NAME = re.compile(r"^  - name: *(.+?) *$")
ENTRY_FILE = re.compile(r"^    file: *(.+?) *$")

Taken = Tuple[str, str]  # (kind, path)


def emit(verdict: str, details: List[str], summary: str) -> int:
    print(verdict)
    for line in details:
        print(line)
    print(summary)
    return 1 if verdict == "fail" else 0


def unquote(value: str) -> str:
    return value[1:-1] if len(value) > 1 and value[0] == value[-1] and value[0] in "\"'" else value


def manifest_taken(text: str, name: str) -> List[Taken]:
    """Manifest entries named `name`, as (kind, the entry's `file:` or the manifest)."""
    taken = []  # type: List[Taken]
    kind = None  # type: Optional[str]
    current = None  # type: Optional[str]
    for line in text.splitlines():
        top = TOP_KEY.match(line)
        if top:
            kind, current = MANIFEST_KINDS.get(top.group(1)), None
            continue
        if kind is None:
            continue
        entry = ENTRY_NAME.match(line)
        if entry:
            current = unquote(entry.group(1))
            if current == name:
                taken.append((kind, MANIFEST_REL))
            continue
        path = ENTRY_FILE.match(line)
        if path and current == name and taken and taken[-1] == (kind, MANIFEST_REL):
            taken[-1] = (kind, unquote(path.group(1)))
    return taken


def installed_taken(root: Path, folders: Tuple[str, str, str], name: str,
                    shown: str = "") -> List[Taken]:
    """What `name` collides with in root's commands, agents, and skills
    folders. Paths print relative to root, behind `shown` when it is set."""
    commands, agents, skills = (root / folder for folder in folders)
    candidates = [("command", commands / ("%s.md" % name)),
                  ("agent", agents / ("%s.md" % name)),
                  ("agent", agents / ("%s.toml" % name)),
                  ("skill", skills / name)]
    taken = []  # type: List[Taken]
    for kind, path in candidates:
        if path.exists():
            rel = path.relative_to(root).as_posix()
            taken.append((kind, "%s/%s" % (shown, rel) if shown else rel))
    return taken


def plugin_root() -> Optional[Path]:
    """The Claude Code plugin this script runs from, if any."""
    root = Path(__file__).resolve().parent.parent
    return root if (root / ".claude-plugin" / "plugin.json").is_file() else None


def run_check(project: Path, name: str, platform: str) -> int:
    reasons = []  # type: List[str]
    if not NAME.match(name):
        reasons.append("reason: name %s is not kebab-case" % name)
    taken = []  # type: List[Taken]
    unverifiable = False
    manifest = project / MANIFEST_REL
    if manifest.is_file():
        mode = "source"
        target = "skills/%s/SKILL.md" % name
        manifest_line = MANIFEST_REL
        taken = manifest_taken(manifest.read_text(encoding="utf-8"), name)
        if (project / "skills" / name).exists() and not any(k == "skill" for k, _ in taken):
            taken.append(("skill", "skills/%s" % name))
    else:
        mode = "installed %s" % platform
        commands, agents, skills = PLATFORMS[platform]
        target = "%s/%s/SKILL.md" % (skills, name)
        manifest_line = "none"
        taken = installed_taken(project, PLATFORMS[platform], name)
        plugin = plugin_root()
        if plugin is not None:
            taken += installed_taken(plugin, ("commands", "agents", "skills"), name, str(plugin))
        elif not (project / commands).is_dir():
            unverifiable = True
            reasons.append("reason: no %s/ and not run from a plugin; check --platform"
                           % commands)
    reasons += ["reason: name taken by %s %s" % pair for pair in taken]
    if taken or not NAME.match(name):
        verdict = "fail"
    elif unverifiable:
        verdict = "unverifiable"
    else:
        verdict = "pass"
    details = reasons + ["mode: %s" % mode, "target: %s" % target, "manifest: %s" % manifest_line]
    return emit(verdict, details, "skill-target: %s (%s, %d taken)" % (verdict, mode, len(taken)))


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="skill-target.py",
        description="Say where /new-skill writes a skill and whether its name is free.")
    sub = parser.add_subparsers(dest="command", metavar="check")
    sub.required = True
    check = sub.add_parser(
        "check", help="check a skill name and print the SKILL.md path to write",
        description="With .writ/manifest.yaml (the Writ source repository), check the "
                    "manifest's commands, agents, and skills and target skills/<name>/. "
                    "Without it, check the platform's installed commands, agents, and "
                    "skills (and the plugin's, when run from one) and target the "
                    "platform's skills folder. Writes nothing.")
    check.add_argument("name", help="the skill name (kebab-case)")
    check.add_argument("--platform", required=True, choices=sorted(PLATFORMS),
                       help="the platform running the command")
    check.add_argument("--project", default=".", metavar="DIR",
                       help="project root (default: the current directory)")
    return parser


def main(argv: Optional[List[str]] = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)
    project = Path(args.project)
    if not project.is_dir():
        parser.print_usage(sys.stderr)
        print("skill-target.py: error: --project %s is not a directory" % args.project,
              file=sys.stderr)
        return 2
    return run_check(project, args.name, args.platform)


if __name__ == "__main__":
    sys.exit(main())
