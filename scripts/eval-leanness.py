#!/usr/bin/env python3
"""Tier A leanness tripwire — full-surface measurement + cross-registry parity.

Dogfooding-only self-governance for Writ-the-framework (never ships to users).
Measures the framework's ENTIRE product surface (commands, agents, skills,
adapters, scripts, system-instructions.md — see SURFACE_REGISTRY) via a
registry-driven walk, and cross-checks the command registries that nothing
else covers. Deliberately does NOT duplicate:

  - manifest parity  -> owned by eval.sh check_manifest
  - per-file length  -> owned by eval.sh check_length
  - skill boundary   -> owned by lint-skill.sh / skill-lifecycle

The guardian measures itself: this file lives under `scripts/` and is counted
in the `scripts` surface like everything else — no self-exemption.

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
                     "command_lines","command_chars",
                     "per_surface", "total_product_lines",
                     "total_product_chars", "writ_workspace_lines",
                     "story_context_bytes", "story_context_bytes_note"}
    }

  "story_context_bytes" is a declared-load PROXY, not consumed tokens — see
  STORY_CONTEXT_BYTES_NOTE and the sibling "story_context_bytes_note" key.
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

# The full declared product surface (spec: 2026-07-26-leanness-instrumentation).
# Each entry: name, path (repo-relative), glob patterns to sum (None = a single
# file, not a directory), and whether it is gated (counted toward
# total_product_lines/chars and eligible for the reduction ratchet). Anything
# NOT covered here — and not in OUT_OF_SCOPE — trips the coverage guard.
SURFACE_REGISTRY = [
    {"name": "commands", "path": "commands", "globs": ["*.md"], "gated": True},
    {"name": "agents", "path": "agents", "globs": ["*.md"], "gated": True},
    {"name": "skills", "path": "skills", "globs": ["*/SKILL.md"], "gated": True},
    {"name": "adapters", "path": "adapters", "globs": ["*.md"], "gated": True},
    {"name": "scripts", "path": "scripts", "globs": ["**/*.py", "**/*.sh"], "gated": True},
    {"name": "system_instructions", "path": "system-instructions.md", "globs": None, "gated": True},
]

# .writ/ is ceremony cost, not product (Business Rule 2): reported for trend
# visibility only, never gated, never part of total_product_lines/chars, and
# never eligible for the reduction ratchet.
WRIT_WORKSPACE = {"name": "writ_workspace", "path": ".writ", "globs": ["**/*.md"], "gated": False}

SURFACE_BY_NAME = {entry["name"]: entry for entry in SURFACE_REGISTRY}

# --- story_context_bytes: a static, declared-load proxy --------------------
# Sums the byte size of every artifact commands/implement-story.md Step 2
# declares it loads for a full-pipeline story. See the module docstring:
# this is a PROXY for declared load, not consumed tokens.

# implement-story.md Step 2 documents knowledge_context as capped at ~2KB.
# Actual assembly is keyword-driven and non-reproducible across runs, so this
# charges the flat documented budget rather than an assembled block.
KNOWLEDGE_CONTEXT_CAP_BYTES = 2048

# Mirrors the Gate 0/1/3/4/5 "Agent:" lines in commands/implement-story.md's
# routing table. If a gate is added there and not mirrored here, this metric
# silently understates story_context_bytes — kept in sync by hand.
GATE_AGENT_FILES = [
    "architecture-check-agent.md",
    "coding-agent.md",
    "review-agent.md",
    "testing-agent.md",
    "documentation-agent.md",
]

STORY_CONTEXT_BYTES_NOTE = (
    "story_context_bytes is a declared-load PROXY (the byte sum of what "
    "implement-story.md Step 2 says it loads for a full-pipeline story) — "
    "it is NOT measured/consumed tokens and must never be reported as such."
)

# Best-effort keyword anchors for resolving a bracketed context-hint category
# (no explicit file -> heading path) to its documented primary source section.
# Kept intentionally loose: an unresolvable hint contributes 0, never an error.
CONTEXT_HINT_CATEGORY_KEYWORDS = {
    "error map rows": [("technical-spec.md", "error"), ("spec.md", "error experience")],
    "shadow paths": [("technical-spec.md", "shadow path"), ("spec.md", "happy path")],
    "business rules": [("spec.md", "business rules")],
    "experience": [("spec.md", "experience design")],
}


def _file_size(path: str | None) -> int:
    if not path:
        return 0
    try:
        return os.path.getsize(path)
    except OSError:
        return 0


def select_story_file(root: str) -> str | None:
    """Deterministic worst-case story selection: no "current story" exists at
    eval time, so pick the largest story file under the lexicographically
    last date-prefixed folder in .writ/specs/. Zero (None) when none exist.
    """
    specs_dir = os.path.join(root, ".writ", "specs")
    if not os.path.isdir(specs_dir):
        return None
    spec_folders = sorted(entry.name for entry in os.scandir(specs_dir) if entry.is_dir())
    if not spec_folders:
        return None
    latest = spec_folders[-1]
    stories_dir = os.path.join(specs_dir, latest, "user-stories")
    story_files = sorted(glob.glob(os.path.join(stories_dir, "story-*.md")))
    if not story_files:
        return None
    return max(story_files, key=lambda p: os.path.getsize(p))


def extract_markdown_section(text: str, heading_line: str) -> str | None:
    """Return the section body (heading through the next heading of equal or
    higher level, or EOF) for the FIRST line matching `heading_line` exactly
    (after stripping). None if not found — callers treat that as a 0."""
    target = heading_line.strip()
    level = len(target) - len(target.lstrip("#"))
    if level == 0:
        return None
    lines = text.splitlines(keepends=True)
    start = next((i for i, line in enumerate(lines) if line.strip() == target), None)
    if start is None:
        return None
    end = len(lines)
    for j in range(start + 1, len(lines)):
        stripped = lines[j].rstrip("\n")
        if stripped.startswith("#") and (len(stripped) - len(stripped.lstrip("#"))) <= level:
            end = j
            break
    return "".join(lines[start:end])


def find_heading_containing(text: str, keyword: str) -> str | None:
    for line in text.splitlines():
        stripped = line.strip()
        if stripped.startswith("#") and keyword in stripped.lower():
            return stripped
    return None


def resolve_spec_file(spec_folder: str, filename: str) -> str | None:
    for candidate in (os.path.join(spec_folder, filename),
                      os.path.join(spec_folder, "sub-specs", filename)):
        if os.path.isfile(candidate):
            return candidate
    return None


def _read_text(path: str) -> str:
    try:
        with open(path, encoding="utf-8", errors="ignore") as handle:
            return handle.read()
    except OSError:
        return ""


def resolve_extended_ref(spec_folder: str, ref: str) -> int:
    """`file.md -> ## Section -> ### Subsection` -> byte size of the deepest
    resolved section, or 0 if the file/heading chain doesn't resolve."""
    parts = [p.strip() for p in re.split(r"[→>]{1,2}", ref) if p.strip()]
    if len(parts) < 2:
        return 0
    path = resolve_spec_file(spec_folder, parts[0])
    if not path:
        return 0
    section_text = _read_text(path)
    for heading in parts[1:]:
        extracted = extract_markdown_section(section_text, heading)
        if extracted is None:
            return 0
        section_text = extracted
    return len(section_text.encode("utf-8"))


def resolve_category_ref(spec_folder: str, category: str) -> int:
    for filename, keyword in CONTEXT_HINT_CATEGORY_KEYWORDS.get(category, []):
        path = resolve_spec_file(spec_folder, filename)
        if not path:
            continue
        text = _read_text(path)
        heading = find_heading_containing(text, keyword)
        if heading is None:
            continue
        section = extract_markdown_section(text, heading)
        if section is not None:
            return len(section.encode("utf-8"))
    return 0


def context_for_agents_section(story_text: str) -> str:
    match = re.search(r"^## Context for Agents\s*$", story_text, re.MULTILINE)
    if not match:
        return ""
    start = match.end()
    rest = story_text[start:]
    next_heading = re.search(r"^##(?!#)", rest, re.MULTILINE)
    end = start + next_heading.start() if next_heading else len(story_text)
    return story_text[start:end]


def resolve_context_hints(spec_folder: str, story_text: str) -> int:
    """Sum declared context-hint sources for the story's `## Context for
    Agents` block. Unresolvable references contribute 0, never an error —
    this must never sum whole source files (that overstates declared load)."""
    section = context_for_agents_section(story_text)
    if not section:
        return 0
    total = 0
    for line in section.splitlines():
        stripped = line.strip()
        cat_match = re.match(r"-\s*\*\*([^:*]+):\*\*", stripped)
        category = cat_match.group(1).strip().lower() if cat_match else None
        refs = re.findall(r"`([^`]+)`", line)
        extended_refs = [r for r in refs if re.search(r"\.md\s*[→>]{1,2}", r)]
        if extended_refs:
            for ref in extended_refs:
                total += resolve_extended_ref(spec_folder, ref)
        elif category and category in CONTEXT_HINT_CATEGORY_KEYWORDS and "[" in line:
            total += resolve_category_ref(spec_folder, category)
    return total


def story_context_components(root: str) -> dict[str, int]:
    """Ordered component -> byte-size map for the declared-load proxy."""
    components: dict[str, int] = {}

    components["context_md"] = _file_size(os.path.join(root, ".writ", "context.md"))

    story_file = select_story_file(root)
    components["story_file"] = _file_size(story_file)

    spec_lite_bytes = 0
    hint_bytes = 0
    if story_file:
        spec_folder = os.path.dirname(os.path.dirname(story_file))
        spec_lite_bytes = _file_size(os.path.join(spec_folder, "spec-lite.md"))
        hint_bytes = resolve_context_hints(spec_folder, _read_text(story_file))
    components["spec_lite"] = spec_lite_bytes
    components["context_hints"] = hint_bytes

    components["knowledge_context_cap"] = KNOWLEDGE_CONTEXT_CAP_BYTES

    agents_dir = os.path.join(root, "agents")
    components["gate_agents"] = sum(
        _file_size(os.path.join(agents_dir, name)) for name in GATE_AGENT_FILES
    )

    return components

# Files under commands/ that are infrastructure, not user-invokable commands.
# Kept explicit and small; if it grows, that is itself a leanness signal.
INFRA_PREFIXES = ("_",)

# Non-product top-level paths, declared explicitly rather than inferred, so a
# future root-level product file can never silently fall outside the frame.
# Growth in this list is itself a leanness signal — mirrors INFRA_PREFIXES.
# Any leading-dot top-level name (`.git`, `.github`, `.claude`, `.codex`,
# `.cursor`, `.writ`, `.writ-lanes-*`, `.gitignore`, `.DS_Store`, …) is out of
# scope unconditionally; see the dot-prefix check in check_coverage() below.
OUT_OF_SCOPE = {
    "archive", "bin", "claude-code", "codex", "cursor", "node_modules", "test",
    "README.md", "CHANGELOG.md", "CLAUDE.md", "AGENTS.md", "SKILL.md",
    "LICENSE", "VERSION", "package.json",
}

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


def surface_files(root: str, entry: dict) -> list[str]:
    """Sorted file list for a registry entry: its globs, or the single file.

    A missing directory (or missing single file) yields an empty list rather
    than raising — "directory absent" is a coverage-guard concern (Story 2),
    not a measurement-time crash.
    """
    surface_path = os.path.join(root, entry["path"])
    if entry["globs"] is None:
        return [surface_path] if os.path.isfile(surface_path) else []
    files: set[str] = set()
    for pattern in entry["globs"]:
        files.update(glob.glob(os.path.join(surface_path, pattern), recursive=True))
    return sorted(files)


def measure_files(files: list[str], warnings: list[dict]) -> tuple[int, int]:
    """Sum (lines, chars) across files, skipping unreadable ones with a warning."""
    lines = 0
    chars = 0
    for path in files:
        try:
            with open(path, "rb") as handle:
                data = handle.read()
        except OSError as exc:
            warnings.append({
                "subject": relpath(path),
                "what": f"file could not be read ({exc.strerror or exc}); "
                        "skipped from leanness metrics.",
                "fix": "Fix file permissions or remove the unreadable path.",
            })
            continue
        lines += data.count(b"\n")
        chars += len(data)
    return lines, chars


def compute_metrics(root: str) -> tuple[dict, list[dict]]:
    """Registry-driven full-surface walk.

    Returns (metrics, scan_warnings) — scan_warnings carries unreadable-file
    notices so main() can merge them into the top-level `warnings` list.
    """
    scan_warnings: list[dict] = []
    per_surface: dict[str, dict[str, int]] = {}
    total_lines = 0
    total_chars = 0

    for entry in SURFACE_REGISTRY:
        files = surface_files(root, entry)
        lines, chars = measure_files(files, scan_warnings)
        per_surface[entry["name"]] = {"lines": lines, "chars": chars}
        if entry["gated"]:
            total_lines += lines
            total_chars += chars

    writ_files = surface_files(root, WRIT_WORKSPACE)
    writ_lines, _writ_chars = measure_files(writ_files, scan_warnings)

    story_context_bytes = sum(story_context_components(root).values())

    metrics = {
        "commands": len(surface_files(root, SURFACE_BY_NAME["commands"])),
        "agents": len(surface_files(root, SURFACE_BY_NAME["agents"])),
        "skills": len(surface_files(root, SURFACE_BY_NAME["skills"])),
        "command_lines": per_surface["commands"]["lines"],
        "command_chars": per_surface["commands"]["chars"],
        "per_surface": per_surface,
        "total_product_lines": total_lines,
        "total_product_chars": total_chars,
        "writ_workspace_lines": writ_lines,
        "story_context_bytes": story_context_bytes,
        "story_context_bytes_note": STORY_CONTEXT_BYTES_NOTE,
    }
    return metrics, scan_warnings


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


def check_coverage(root: str) -> list[dict]:
    """Every top-level repo entry must resolve to the gated registry, the
    ungated .writ workspace, OUT_OF_SCOPE, or a leading-dot name. Anything
    left over is the anti-recurrence finding this story exists to add — the
    blind spot that let `scripts/` go unmeasured across two audit cycles.
    """
    findings: list[dict] = []
    accounted = {entry["path"] for entry in SURFACE_REGISTRY} | {WRIT_WORKSPACE["path"]} | OUT_OF_SCOPE

    for entry in SURFACE_REGISTRY:
        full = os.path.join(root, entry["path"])
        exists = os.path.isfile(full) if entry["globs"] is None else os.path.isdir(full)
        if not exists:
            findings.append({
                "subject": entry["path"],
                "what": f"gated registry entry '{entry['name']}' is declared in SURFACE_REGISTRY "
                        "but does not exist on disk.",
                "fix": f"Restore {entry['path']}, or remove the stale SURFACE_REGISTRY entry "
                       "in scripts/eval-leanness.py if it is genuinely gone.",
            })

    try:
        top_level = sorted(entry.name for entry in os.scandir(root))
    except OSError:
        return findings

    for name in top_level:
        if name.startswith("."):
            continue
        if name in accounted:
            continue
        findings.append({
            "subject": name,
            "what": f"top-level entry '{name}' is neither in the gated product registry "
                    "nor declared out of scope.",
            "fix": f"Add '{name}' to SURFACE_REGISTRY with a measurement rule, or add it to "
                   "OUT_OF_SCOPE in scripts/eval-leanness.py if it is genuinely non-product.",
        })

    return findings


def check_baseline(baseline: dict | None, err: str | None, baseline_path: str,
                   metrics: dict) -> tuple[list[dict], list[dict]]:
    """The reduction ratchet (replaces GROWTH_TOLERANCE): every gated surface
    is compared to its own recorded baseline, independently.

      current <= baseline                       -> silent (down is free)
      current >  baseline, justification present -> silent (up costs a sentence)
      current >  baseline, no justification      -> warning naming the delta

    A missing/malformed baseline, or a legacy (pre-schema-2) baseline with no
    `surfaces` map, is a structural finding — the ratchet cannot run blind.
    """
    structural: list[dict] = []
    warnings: list[dict] = []

    if baseline is None:
        structural.append({
            "subject": relpath(baseline_path),
            "what": f"leanness baseline is {err}; per-surface drift cannot be measured.",
            "fix": "Restore the committed baseline, or seed it with "
                   "`python3 scripts/eval-leanness.py --update-baseline`.",
        })
        return structural, warnings

    surfaces = baseline.get("surfaces")
    if baseline.get("schema") != 2 or not isinstance(surfaces, dict):
        structural.append({
            "subject": relpath(baseline_path),
            "what": "leanness baseline uses the legacy pre-full-surface schema "
                    "(no per-surface `surfaces` map); the reduction ratchet cannot run.",
            "fix": "Migrate the baseline: "
                   "`python3 scripts/eval-leanness.py --update-baseline`.",
        })
        return structural, warnings

    per_surface = metrics.get("per_surface", {})
    for entry in SURFACE_REGISTRY:
        name = entry["name"]
        base_entry = surfaces.get(name)
        if not isinstance(base_entry, dict):
            continue  # newly-added surface with no prior baseline: no history to ratchet yet
        current = per_surface.get(name, {})
        justification = str(base_entry.get("justification") or "").strip()
        for metric_key in ("lines", "chars"):
            base_value = base_entry.get(metric_key)
            current_value = current.get(metric_key)
            if not isinstance(base_value, (int, float)) or not isinstance(current_value, (int, float)):
                continue
            if current_value <= base_value or justification:
                continue
            delta = current_value - base_value
            warnings.append({
                "subject": name,
                "what": f"{name} {metric_key} grew from {base_value} to {current_value} "
                        f"(+{delta}) with no justification.",
                "fix": f"If deliberate, add a one-line justification to surfaces.{name} in "
                       f"{relpath(baseline_path)} and rerun --update-baseline. "
                       "Otherwise prune the surface back down — the delta is the signal.",
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

    metrics, scan_warnings = compute_metrics(root)

    if args.update_baseline:
        # Reseeding is a clean-slate ratchet: every gated surface's baseline
        # becomes exactly the current measurement (down is free; a shrink
        # ratchets down automatically) and `justification` resets to "" —
        # a justification describes a specific past delta, and that delta no
        # longer exists once absorbed into the new baseline. A future
        # increase past this fresh baseline requires a fresh justification.
        payload = {
            "recorded": _today(),
            "schema": 2,
            "surfaces": {
                name: {
                    "lines": per_surface["lines"],
                    "chars": per_surface["chars"],
                    "justification": "",
                }
                for name, per_surface in metrics["per_surface"].items()
            },
            "commands": metrics["commands"],
            "agents": metrics["agents"],
            "skills": metrics["skills"],
            "command_lines": metrics["command_lines"],
            "command_chars": metrics["command_chars"],
            "total_product_lines": metrics["total_product_lines"],
            "note": "Down is free. Any increase to a gated surface requires a "
                    "justification string in its baseline entry, or it warns.",
        }
        os.makedirs(os.path.dirname(baseline_path), exist_ok=True)
        with open(baseline_path, "w", encoding="utf-8") as handle:
            json.dump(payload, handle, indent=2)
            handle.write("\n")
        print(f"Wrote baseline: {relpath(baseline_path)}", file=sys.stderr)
        return 0

    baseline, err = load_baseline(baseline_path)

    structural = check_parity(root) + check_coverage(root)
    base_structural, base_warnings = check_baseline(baseline, err, baseline_path, metrics)
    structural += base_structural

    warnings = scan_warnings + base_warnings + check_ceilings(metrics)

    json.dump({"structural": structural, "warnings": warnings, "metrics": metrics},
              sys.stdout, indent=2)
    sys.stdout.write("\n")
    return 0


def _today() -> str:
    import datetime
    return datetime.date.today().isoformat()


if __name__ == "__main__":
    sys.exit(main())
