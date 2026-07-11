#!/usr/bin/env python3
"""Tier A leanness tripwire — aggregate surface + cross-registry parity.

Dogfooding-only self-governance for Writ-the-framework (never ships to users).
Measures the framework's own command/agent/skill surface and cross-checks the
command registries that nothing else covers. Deliberately does NOT duplicate:

  - manifest parity  -> owned by eval.sh check_manifest
  - per-file length  -> owned by eval.sh check_length
  - skill boundary   -> owned by lint-skill.sh / skill-lifecycle

Registry parity is DIRECTIONAL (see DEV-001 in the leanness-guardian drift-log):
  - README "## Commands" table  <-> commands/*.md   is BIDIRECTIONAL
        orphan  = command file with no README table row
        phantom = README table names a command with no file
  - /status "Maintainer Note" allowlist -> files     is ONE-WAY
        phantom = allowlist names a command with no file
        (never an orphan: the allowlist is a curated *suggestion* subset)

Contract:
  usage:  eval-leanness.py [--root PATH] [--baseline PATH] [--update-baseline]
  output: JSON to stdout:
    {
      "structural": [ {"subject","what","fix"} ],   # -> eval.sh FAILs the run
      "warnings":   [ {"subject","what","fix"} ],   # -> non-blocking, exit 0
      "metrics":    {"commands","agents","skills",
                     "command_lines","command_chars"}
    }
  exit code: always 0 — the bash check decides FAIL from `structural`.
"""

from __future__ import annotations

import argparse
import glob
import json
import os
import re
import sys

# Count ceilings — headroom over today's 31/7/6 so the tripwire stays silent
# until genuine growth, then speaks once (warn-only, never blocking).
MAX_COMMANDS = 35
MAX_AGENTS = 10
MAX_SKILLS = 12

# Aggregate-weight growth tolerance before a (non-blocking) warning fires.
GROWTH_TOLERANCE = 0.10

# Files under commands/ that are infrastructure, not user-invokable commands.
# Kept explicit and small; if it grows, that is itself a leanness signal.
INFRA_PREFIXES = ("_",)

# Backticked slash-command token, e.g. `/create-spec`. Anchored on both
# backticks so paths like `adapters/cursor.md` and prose slashes never match.
COMMAND_TOKEN = re.compile(r"`/([a-z][a-z0-9-]*)`")
# A bare backticked command name, e.g. `create-spec` (the /status allowlist form).
BARE_TOKEN = re.compile(r"`([a-z][a-z0-9-]*)`")


def repo_root(explicit: str | None) -> str:
    if explicit:
        return os.path.abspath(explicit)
    return os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))


def is_infra(name: str) -> bool:
    return name.startswith(INFRA_PREFIXES)


def all_command_files(root: str) -> list[str]:
    return sorted(glob.glob(os.path.join(root, "commands", "*.md")))


def command_names(root: str) -> set[str]:
    """Non-infra command names (stem, no extension)."""
    names = set()
    for path in all_command_files(root):
        stem = os.path.splitext(os.path.basename(path))[0]
        if not is_infra(stem):
            names.add(stem)
    return names


def readme_command_names(root: str) -> set[str]:
    """Command names named in table rows of the README '## Commands' section.

    Scoped to the Commands section so command references elsewhere (e.g.
    `/agent` in the Platform Support table) never create false phantoms.
    Fenced code blocks are ignored so diagram headings can't open the section.
    """
    path = os.path.join(root, "README.md")
    if not os.path.isfile(path):
        return set()

    names: set[str] = set()
    in_commands = False
    in_fence = False
    with open(path, encoding="utf-8") as handle:
        for raw in handle:
            line = raw.rstrip("\n")
            stripped = line.strip()
            if stripped.startswith("```"):
                in_fence = not in_fence
                continue
            if in_fence:
                continue
            if stripped.startswith("## "):
                # Enter on the Commands heading; leave on the next H2.
                in_commands = stripped[3:].strip().lower() == "commands"
                continue
            if in_commands and stripped.startswith("|"):
                names.update(COMMAND_TOKEN.findall(line))
    return names


def status_allowlist_names(root: str) -> set[str]:
    """Command names in the /status 'Maintainer Note: Command Allowlist' block."""
    path = os.path.join(root, "commands", "status.md")
    if not os.path.isfile(path):
        return set()

    names: set[str] = set()
    in_section = False
    with open(path, encoding="utf-8") as handle:
        for raw in handle:
            stripped = raw.strip()
            if stripped.startswith("## "):
                heading = stripped[3:].strip().lower()
                in_section = heading.startswith("maintainer note: command allowlist")
                continue
            if in_section:
                names.update(BARE_TOKEN.findall(raw))
    return names


def count_skills(root: str) -> int:
    skills_dir = os.path.join(root, "skills")
    if not os.path.isdir(skills_dir):
        return 0
    total = 0
    for entry in os.scandir(skills_dir):
        if entry.is_dir() and os.path.isfile(os.path.join(entry.path, "SKILL.md")):
            total += 1
    return total


def compute_metrics(root: str) -> dict:
    files = all_command_files(root)
    lines = 0
    chars = 0
    for path in files:
        with open(path, "rb") as handle:
            data = handle.read()
        lines += data.count(b"\n")
        chars += len(data)
    return {
        "commands": len(files),
        "agents": len(glob.glob(os.path.join(root, "agents", "*.md"))),
        "skills": count_skills(root),
        "command_lines": lines,
        "command_chars": chars,
    }


def load_baseline(path: str) -> tuple[dict | None, str | None]:
    if not os.path.isfile(path):
        return None, "missing"
    try:
        with open(path, encoding="utf-8") as handle:
            return json.load(handle), None
    except (json.JSONDecodeError, OSError) as exc:
        return None, f"unreadable ({exc})"


def check_parity(root: str) -> list[dict]:
    findings: list[dict] = []
    files = command_names(root)
    readme = readme_command_names(root)
    allowlist = status_allowlist_names(root)

    # README <-> files (bidirectional).
    for name in sorted(files - readme):
        findings.append({
            "subject": f"commands/{name}.md",
            "what": "command file has no row in the README '## Commands' table (orphan).",
            "fix": f"Add a `/{name}` row to the README Commands table, or remove the command file.",
        })
    for name in sorted(readme - files):
        findings.append({
            "subject": f"README.md -> /{name}",
            "what": "README Commands table names a command with no commands/*.md file (phantom).",
            "fix": f"Create commands/{name}.md or remove the stale `/{name}` README row.",
        })

    # allowlist -> files (one-way; a curated subset is never an orphan source).
    for name in sorted(allowlist - files):
        findings.append({
            "subject": f"commands/status.md -> {name}",
            "what": "the /status command allowlist names a command with no commands/*.md file (phantom).",
            "fix": f"Create commands/{name}.md or remove `{name}` from the /status Maintainer Note allowlist.",
        })

    return findings


def check_baseline(baseline: dict | None, err: str | None, baseline_path: str,
                   metrics: dict) -> tuple[list[dict], list[dict]]:
    structural: list[dict] = []
    warnings: list[dict] = []

    if baseline is None:
        structural.append({
            "subject": relpath(baseline_path),
            "what": f"leanness baseline is {err}; aggregate-weight drift cannot be measured.",
            "fix": "Restore the committed baseline, or seed it with "
                   "`python3 scripts/eval-leanness.py --update-baseline`.",
        })
        return structural, warnings

    for key, current in (("command_lines", metrics["command_lines"]),
                         ("command_chars", metrics["command_chars"])):
        base = baseline.get(key)
        if not isinstance(base, (int, float)) or base <= 0:
            continue
        if current > base * (1 + GROWTH_TOLERANCE):
            pct = (current / base - 1) * 100
            warnings.append({
                "subject": relpath(baseline_path),
                "what": f"aggregate {key} grew {pct:.0f}% ({base} -> {current}), "
                        f"exceeding the +{int(GROWTH_TOLERANCE * 100)}% tolerance.",
                "fix": "If the growth is deliberate, bump the baseline in "
                       f"{relpath(baseline_path)} (rerun with --update-baseline). "
                       "Otherwise prune surface — the delta is the signal.",
            })
    return structural, warnings


def check_ceilings(metrics: dict) -> list[dict]:
    warnings: list[dict] = []
    for label, value, ceiling in (
        ("commands", metrics["commands"], MAX_COMMANDS),
        ("agents", metrics["agents"], MAX_AGENTS),
        ("skills", metrics["skills"], MAX_SKILLS),
    ):
        if value > ceiling:
            warnings.append({
                "subject": label,
                "what": f"{label} count is {value}, over the soft ceiling of {ceiling}.",
                "fix": f"Run the Tier B leanness audit to justify or prune {label}; "
                       "raise the ceiling deliberately only if the growth is sound.",
            })
    return warnings


# Set once in main() so finding text can render repo-relative paths.
_ROOT = ""


def relpath(path: str) -> str:
    if _ROOT and path.startswith(_ROOT):
        return os.path.relpath(path, _ROOT)
    return path


def main(argv: list[str] | None = None) -> int:
    global _ROOT
    parser = argparse.ArgumentParser(description="Writ Tier A leanness tripwire.")
    parser.add_argument("--root", default=None, help="Repository root (default: script's repo).")
    parser.add_argument("--baseline", default=None, help="Baseline JSON path.")
    parser.add_argument("--update-baseline", action="store_true",
                        help="Write current metrics to the baseline file and exit.")
    args = parser.parse_args(argv)

    root = repo_root(args.root)
    _ROOT = root
    baseline_path = args.baseline or os.path.join(root, ".writ", "leanness-baseline.json")

    metrics = compute_metrics(root)

    if args.update_baseline:
        payload = {
            "recorded": _today(),
            **metrics,
            "note": "Bump deliberately when growth is legitimate; the delta is the signal.",
        }
        os.makedirs(os.path.dirname(baseline_path), exist_ok=True)
        with open(baseline_path, "w", encoding="utf-8") as handle:
            json.dump(payload, handle, indent=2)
            handle.write("\n")
        print(f"Wrote baseline: {relpath(baseline_path)}", file=sys.stderr)
        return 0

    baseline, err = load_baseline(baseline_path)

    structural = check_parity(root)
    base_structural, base_warnings = check_baseline(baseline, err, baseline_path, metrics)
    structural += base_structural

    warnings = base_warnings + check_ceilings(metrics)

    json.dump({"structural": structural, "warnings": warnings, "metrics": metrics},
              sys.stdout, indent=2)
    sys.stdout.write("\n")
    return 0


def _today() -> str:
    import datetime
    return datetime.date.today().isoformat()


if __name__ == "__main__":
    sys.exit(main())
