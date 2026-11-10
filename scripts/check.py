#!/usr/bin/env python3
"""Check that Writ's skills, manifests, and README hold together.

Dev-only: nothing under scripts/ ships. Python 3.9+, standard library only.

usage: python3 scripts/check.py [--root <repo root>]

Line 1 is `pass` or `fail`. Each failure is one line: `fail: <rule>: <detail>`.
The last line is a summary. Exit 0 on pass, 1 on fail, 2 on a usage error.

Rules:
  frontmatter   SKILL.md opens with name and description only; name is the
                folder name and starts with `writ`; description is 1-1024 chars
  rules-link    every skill tells the reader to read the shared rules first
  reference     every `../<skill>/<file>` path and every `writ-*` skill name
                written in a skill exists
  plain         no platform tool name appears in a skill (skills say what must
                happen, never which tool does it)
  manifest      the three plugin manifests carry name `writ` and the version in
                VERSION; the three marketplace files point at plugins/writ
  readme        README.md names every skill
"""
import argparse
import json
import re
import sys
from pathlib import Path
from typing import Dict, List, Optional, Tuple

PLUGIN = Path("plugins") / "writ"
SKILL_NAME = re.compile(r"^writ(-[a-z0-9]+)*$")
RELATIVE_REF = re.compile(r"`(\.\./[^`\s]+)`")
SKILL_MENTION = re.compile(r"`(writ-[a-z0-9-]+)`")
# Tool and mode names that belong to one platform. A skill that uses one stops
# working, or reads as noise, on the others.
PLATFORM_TERMS = (
    "AskQuestion", "AskUserQuestion", "todo_write", "TodoWrite", "subagent_type",
    "EnterPlanMode", "ExitPlanMode", "Task(", "Plan Mode", "Agent Mode",
    "run_in_background", "/compact", "CLAUDE_PLUGIN_ROOT", "CURSOR_PLUGIN_ROOT",
)
PLUGIN_MANIFESTS = (
    PLUGIN / "plugin.json",
    PLUGIN / ".claude-plugin" / "plugin.json",
    PLUGIN / ".cursor-plugin" / "plugin.json",
)
MARKETPLACES = (
    Path(".claude-plugin") / "marketplace.json",
    Path(".cursor-plugin") / "marketplace.json",
    Path(".agents") / "plugins" / "marketplace.json",
)


def parse_frontmatter(text: str) -> Optional[Dict[str, str]]:
    """Top-level `key: value` pairs between the opening `---` lines, or None."""
    lines = text.split("\n")
    if not lines or lines[0].strip() != "---":
        return None
    fields: Dict[str, str] = {}
    for line in lines[1:]:
        if line.strip() == "---":
            return fields
        if not line.strip() or line.startswith((" ", "\t", "#")):
            continue
        key, sep, value = line.partition(":")
        if not sep:
            return None
        fields[key.strip()] = value.strip().strip("\"'")
    return None  # never closed


def skill_dirs(root: Path) -> List[Path]:
    base = root / PLUGIN / "skills"
    if not base.is_dir():
        return []
    return sorted(p for p in base.iterdir() if p.is_dir() and not p.name.startswith("."))


def check_skill(skill: Path, names: List[str]) -> List[Tuple[str, str]]:
    found: List[Tuple[str, str]] = []
    label = "skills/%s" % skill.name
    path = skill / "SKILL.md"
    if not path.is_file():
        return [("frontmatter", "%s has no SKILL.md" % label)]
    text = path.read_text(encoding="utf-8")

    fields = parse_frontmatter(text)
    if fields is None:
        found.append(("frontmatter", "%s/SKILL.md has no closed frontmatter block" % label))
    else:
        extra = sorted(set(fields) - {"name", "description"})
        if extra:
            found.append(("frontmatter", "%s uses keys other than name and description: %s"
                          % (label, ", ".join(extra))))
        name = fields.get("name", "")
        if name != skill.name:
            found.append(("frontmatter", "%s declares name %r" % (label, name)))
        if not SKILL_NAME.match(skill.name):
            found.append(("frontmatter", "%s is not named writ or writ-<word>" % label))
        size = len(fields.get("description", ""))
        if not 1 <= size <= 1024:
            found.append(("frontmatter", "%s description is %d characters; 1 to 1024 allowed"
                          % (label, size)))

    wanted = "rules.md" if skill.name == "writ" else "../writ/rules.md"
    if wanted not in text:
        found.append(("rules-link", "%s/SKILL.md never says to read %s" % (label, wanted)))

    for md in sorted(skill.glob("*.md")):
        body = md.read_text(encoding="utf-8")
        where = "%s/%s" % (label, md.name)
        for ref in RELATIVE_REF.findall(body):
            if "<" in ref:
                continue  # a placeholder such as ../<step>/SKILL.md
            if not (skill / ref).exists():
                found.append(("reference", "%s points at %s, which does not exist" % (where, ref)))
        for mention in sorted(set(SKILL_MENTION.findall(body))):
            if mention not in names:
                found.append(("reference", "%s names the skill %s, which does not exist"
                              % (where, mention)))
        for term in PLATFORM_TERMS:
            if term in body:
                found.append(("plain", "%s uses the platform term %r" % (where, term)))
    return found


def check_manifests(root: Path) -> List[Tuple[str, str]]:
    found: List[Tuple[str, str]] = []
    try:
        version = (root / "VERSION").read_text(encoding="utf-8").strip()
    except OSError:
        return [("manifest", "VERSION is missing")]
    for rel in PLUGIN_MANIFESTS:
        try:
            data = json.loads((root / rel).read_text(encoding="utf-8"))
        except (OSError, ValueError):
            found.append(("manifest", "%s is missing or not JSON" % rel))
            continue
        if data.get("name") != "writ":
            found.append(("manifest", "%s name is %r, not 'writ'" % (rel, data.get("name"))))
        if data.get("version") != version:
            found.append(("manifest", "%s version is %r; VERSION says %s"
                          % (rel, data.get("version"), version)))
    for rel in MARKETPLACES:
        try:
            text = (root / rel).read_text(encoding="utf-8")
            json.loads(text)
        except (OSError, ValueError):
            found.append(("manifest", "%s is missing or not JSON" % rel))
            continue
        if "plugins/writ" not in text:
            found.append(("manifest", "%s does not point at plugins/writ" % rel))
    return found


def check_readme(root: Path, names: List[str]) -> List[Tuple[str, str]]:
    try:
        text = (root / "README.md").read_text(encoding="utf-8")
    except OSError:
        return [("readme", "README.md is missing")]
    words = set(re.findall(r"writ(?:-[a-z0-9]+)*", text))
    return [("readme", "README.md never mentions %s" % name)
            for name in names if name not in words]


def run(root: Path) -> List[Tuple[str, str]]:
    skills = skill_dirs(root)
    if not skills:
        return [("frontmatter", "no skill folders under %s/skills" % PLUGIN)]
    names = [s.name for s in skills]
    found: List[Tuple[str, str]] = []
    for skill in skills:
        found.extend(check_skill(skill, names))
    found.extend(check_manifests(root))
    found.extend(check_readme(root, names))
    return found


def main(argv: Optional[List[str]] = None) -> int:
    parser = argparse.ArgumentParser(description="Check Writ's skills, manifests, and README.")
    parser.add_argument("--root", default=str(Path(__file__).resolve().parent.parent))
    args = parser.parse_args(argv)
    root = Path(args.root)
    if not root.is_dir():
        print("usage: --root must be a directory", file=sys.stderr)
        return 2
    found = run(root)
    print("fail" if found else "pass")
    for rule, detail in found:
        print("fail: %s: %s" % (rule, detail))
    skills = skill_dirs(root)
    lines = sum(len(md.read_text(encoding="utf-8").splitlines())
                for s in skills for md in s.glob("*.md"))
    print("check: %d skills, %d lines of skill text, %d failures" % (len(skills), lines, len(found)))
    return 1 if found else 0


if __name__ == "__main__":
    sys.exit(main())
