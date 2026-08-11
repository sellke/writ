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
                     "story_context_bytes", "story_context_bytes_note",
                     "contract_compliance", "required_skills_declarations"}
    }

  Component-contract findings (see CONTRACT_CHECK_SEVERITY) land in
  "warnings" today and become "structural" when the governor-enforcement
  spec flips that one constant. "contract_compliance" is the trend channel
  beside them: counts of files checked and files compliant, so the migration
  specs have one number to move instead of a diff of findings.

  "story_context_bytes" is a mixed measurement, not consumed tokens — see
  STORY_CONTEXT_BYTES_NOTE and the sibling "story_context_bytes_note" key.
  Its `context_hints` component (Story 3, 2026-08-03-deterministic-story-
  substrate) is real delivered bytes from scripts/story-context.py's own
  assembler output; the remaining components (`knowledge_context_cap`,
  `gate_agents`, etc.) stay declared-load proxies. The aggregate sum is
  still not consumed-token accounting either way (ADR-019 labeling
  discipline).
  exit code: always 0 — the bash check decides FAIL from `structural`.
"""

from __future__ import annotations

import argparse
import glob
import json
import os
import re
import subprocess
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

# --- story_context_bytes: mixed real-measurement + declared-load proxy -----
# Sums the byte size of every artifact commands/implement-story.md Step 2
# declares it loads for a full-pipeline story. As of Story 3
# (2026-08-03-deterministic-story-substrate), the context_hints component
# below is no longer part of that declared-load family — it calls the real
# assembler (scripts/story-context.py) and reports its actual bytes.total.
# The other components here remain the PROXY described in the module
# docstring: declared load, not consumed tokens.

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
    "story_context_bytes is a MIXED measurement — its context_hints component "
    "is real delivered bytes from scripts/story-context.py's assembler output "
    "(Story 3), while the remaining components (context_md, story_file, "
    "spec_lite, knowledge_context_cap, gate_agents) stay a declared-load "
    "PROXY of what implement-story.md Step 2 says it loads. Neither half is "
    "measured/consumed TOKENS, and the aggregate must never be reported as such."
)

# Hint-category resolution now delegates to scripts/story-context.py — the
# single implementation of the `## Context for Agents` contract (Business
# Rule 2: "one implementation per contract"). Invoked via subprocess rather
# than `import`: story-context.py is a hyphenated filename, not a valid
# Python module identifier for a literal `import` statement, and the
# established precedent for hyphenated-script-to-hyphenated-script
# integration in this codebase is eval-spec-deps.py's subprocess call into
# spec-deps.py, not importlib.util (that mechanism is for callers needing
# custom exception translation, which this measurement does not).
STORY_CONTEXT_HELPER = os.path.join(os.path.dirname(__file__), "story-context.py")


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


def assembler_bytes_for_story(story_file: str) -> int:
    """Invoke `story-context.py assemble` and return its `bytes.total`.

    This is the sole surviving hint-resolution path — `resolve_context_hints()`
    and its category-keyword helpers are deleted, not merely rewritten
    (Business Rule 2: one implementation per contract; Architecture Check
    Finding 4). Unresolvable references, a missing/crashed subprocess, or
    unparseable stdout all contribute 0 — never an exception — preserving
    the "unresolvable contributes 0" contract this replaces (Finding 5).
    """
    try:
        proc = subprocess.run(
            [sys.executable, STORY_CONTEXT_HELPER, "assemble", "--story", story_file],
            capture_output=True, text=True, timeout=30,
        )
    except (OSError, subprocess.SubprocessError):
        return 0
    if proc.returncode != 0:
        return 0
    try:
        payload = json.loads(proc.stdout or "{}")
    except json.JSONDecodeError:
        return 0
    total = payload.get("bytes", {}).get("total")
    return total if isinstance(total, int) else 0


def story_context_components(root: str) -> dict[str, int]:
    """Ordered component -> byte-size map for story_context_bytes.

    `context_hints` is real delivered bytes from the assembler
    (`assembler_bytes_for_story()`); every other component remains the
    declared-load proxy described in the module docstring and
    `STORY_CONTEXT_BYTES_NOTE`.
    """
    components: dict[str, int] = {}

    components["context_md"] = _file_size(os.path.join(root, ".writ", "context.md"))

    story_file = select_story_file(root)
    components["story_file"] = _file_size(story_file)

    spec_lite_bytes = 0
    hint_bytes = 0
    if story_file:
        spec_folder = os.path.dirname(os.path.dirname(story_file))
        spec_lite_bytes = _file_size(os.path.join(spec_folder, "spec-lite.md"))
        hint_bytes = assembler_bytes_for_story(story_file)
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
    # eval.sh's own `--report=eval-report.md` convention (see its usage
    # comment and .github/workflows/*.yml): a transient CI artifact written
    # to repo root DURING the very eval.sh run that invokes this coverage
    # check, never committed. Without this entry the guardian would flag
    # its own tool output as an unmeasured surface on every CI run.
    "eval-report.md",
}

# Backticked slash-command token, e.g. `/create-spec`. Anchored on both
# backticks so paths like `adapters/cursor.md` and prose slashes never match.
COMMAND_TOKEN = re.compile(r"`/([a-z][a-z0-9-]*)`")
# A bare backticked command name, e.g. `create-spec` (the /status allowlist form).
BARE_TOKEN = re.compile(r"`([a-z][a-z0-9-]*)`")

# --- Component-contract instrumentation (spec: 2026-08-11-governor-
# instrumentation; decision: ADR-020) ---------------------------------------
#
# Phase 10 sequencing, ADR-020 "Enforcement sequencing (load-bearing)" and the
# roadmap's Phase 10 -> Dependencies, in the same words: component-contract
# findings land NON-BLOCKING while 2026-08-11-component-contract and
# 2026-08-11-loop-bounds migrate the surface. Landing them blocking on day one
# turns every eval run red, and a permanently red gate becomes invisible —
# exactly how the growth warnings came to be ignored.
#
# THE GOVERNOR-ENFORCEMENT SPEC FLIPS THIS ONE STRING to "structural".
# Nothing else changes: every check below is a pure function returning
# list[dict] and routes through emit_contract_findings().
#
# Precondition for the flip: the two migration specs have brought commands and
# agents into compliance, so a flipped run is green on a clean tree. Flipping
# early is the failure this constant exists to prevent, which is why the
# shipped value is asserted by the test suite.
#
# The one-line diff it becomes:
#     -CONTRACT_CHECK_SEVERITY = "warnings"
#     +CONTRACT_CHECK_SEVERITY = "structural"
CONTRACT_CHECK_SEVERITY = "warnings"   # -> "structural"

# The three fields ADR-020 makes the component contract. Presence and
# non-emptiness only: the lint can verify the field exists and says something;
# it cannot verify the assertion is true.
CONTRACT_FIELDS = ("problem", "outcome", "exit_criteria")

# Agent config blocks live under one of two headings, both legitimate today —
# `system-instructions.md` documents the split for `model_tier`, and ADR-020
# item 2 reuses the same carrier. 6 agents use `## Agent Configuration` with a
# plain fence; visual-qa-agent.md uses `## Agent Specification` with a ```yaml
# fence. Recognising only one produces three false findings against a
# compliant file, and a false finding is the fastest way to teach a maintainer
# to ignore the whole channel.
AGENT_CARRIER_HEADINGS = ("## Agent Configuration", "## Agent Specification")

# A frontmatter/config key at column 0 (or at the block's own left margin),
# e.g. `problem:`, `loop:`, or the flattened `loop.max_iterations:`.
FIELD_KEY = re.compile(r"^([A-Za-z_][A-Za-z0-9_.-]*):(.*)$")

# Values that are syntactically present but assert nothing. `exit_criteria: []`
# declares no falsifiable condition, which is the entire point of the field.
EMPTY_VALUES = frozenset({"", "[]", "{}", "~", "null", "none"})


def emit_contract_findings(findings: list[dict], structural: list[dict],
                           warnings: list[dict], severity: str | None = None) -> None:
    """Route a check's findings to the blocking or non-blocking bucket.

    `severity=None` means "follow CONTRACT_CHECK_SEVERITY" — the normal case.
    An explicit "warnings" pins a check non-blocking regardless of the flip
    (`required_skills:`, per system-instructions.md graceful degradation).
    Any unrecognised value falls back to `warnings`: a typo in the flip must
    never silently disable a check, and must never accidentally block a run.
    """
    chosen = severity or CONTRACT_CHECK_SEVERITY
    target = structural if chosen == "structural" else warnings
    target.extend(findings)


def all_agent_files(root: str) -> list[str]:
    return sorted(glob.glob(os.path.join(root, "agents", "*.md")))


def _has_content(raw: str) -> bool:
    """True when a declared field actually asserts something."""
    value = raw.strip()
    if len(value) >= 2 and value[0] == value[-1] and value[0] in "\"'":
        value = value[1:-1].strip()
    return value.lower() not in EMPTY_VALUES


def _parse_fields(lines: list[str]) -> dict[str, str]:
    """Key -> value map for a frontmatter or config block.

    A key with a block/list value (e.g. `exit_criteria:` followed by indented
    `- "..."` lines) maps to the joined continuation lines, so presence-and-
    non-emptiness is decidable without a YAML parse. No YAML library is
    imported: this helper runs inside eval.sh on every CI run and the module
    has zero third-party dependencies.
    """
    fields: dict[str, str] = {}
    current: str | None = None
    for line in lines:
        match = FIELD_KEY.match(line)
        if match:
            current = match.group(1)
            fields[current] = match.group(2).strip()
            continue
        if current is not None and line.strip():
            joined = (fields[current] + " " + line.strip()).strip()
            fields[current] = joined
    return fields


def frontmatter_lines(path: str) -> list[str] | None:
    """The raw lines of a leading `---` block, or None.

    Only a fence starting on line 1 counts — a `---` horizontal rule mid-
    document is not frontmatter, and several command files use one. An
    unterminated fence, an unreadable file, and a file with no fence all
    return None rather than raising: a read-only check must never crash the
    eval run.
    """
    try:
        with open(path, encoding="utf-8") as handle:
            lines = handle.read().split("\n")
    except (OSError, UnicodeDecodeError):
        return None
    if not lines or lines[0].strip() != "---":
        return None
    for index in range(1, len(lines)):
        if lines[index].rstrip() == "---":
            return lines[1:index]
    return None


def read_frontmatter(path: str) -> dict[str, str] | None:
    """Leading `---` block only. {key: raw_value_string}, or None."""
    lines = frontmatter_lines(path)
    if lines is None:
        return None
    return _parse_fields(lines)


def agent_config_lines(path: str) -> list[str] | None:
    """The raw lines of an agent's config block, either carrier, or None.

    Accepts `## Agent Configuration` or `## Agent Specification`, and any
    fence info-string (plain or ```yaml). A file with neither heading, or a
    heading with no fenced block after it, returns None — the carrier is the
    contract's only home, so its absence is one finding, not three.
    """
    try:
        with open(path, encoding="utf-8") as handle:
            lines = handle.read().split("\n")
    except (OSError, UnicodeDecodeError):
        return None

    start = None
    for index, line in enumerate(lines):
        if line.strip() in AGENT_CARRIER_HEADINGS:
            start = index + 1
            break
    if start is None:
        return None

    for index in range(start, len(lines)):
        stripped = lines[index].strip()
        if stripped.startswith("## "):
            return None  # next section reached before any fence
        if stripped.startswith("```"):
            body: list[str] = []
            for inner in range(index + 1, len(lines)):
                if lines[inner].strip().startswith("```"):
                    return body
                body.append(lines[inner])
            return body
    return None


def read_agent_config(path: str) -> dict[str, str] | None:
    """Dual-carrier agent config block. Same shape as read_frontmatter()."""
    lines = agent_config_lines(path)
    if lines is None:
        return None
    return _parse_fields(lines)


def check_component_contract(root: str) -> list[dict]:
    """Every command and agent must declare problem, outcome, exit_criteria.

    One finding per missing field per file — never an aggregate. A file with
    no carrier at all yields one file-level finding instead, because
    field-level findings against a missing carrier are noise.
    """
    findings: list[dict] = []

    for path in all_command_files(root):
        stem = os.path.splitext(os.path.basename(path))[0]
        if is_infra(stem):
            continue  # Business Rule 7 — the existing rule, not a skip list
        rel = f"commands/{stem}.md"
        fields = read_frontmatter(path)
        if fields is None:
            findings.append({
                "subject": rel,
                "what": "no frontmatter block; the component contract "
                        "(problem:/outcome:/exit_criteria:) has nowhere to live.",
                "fix": f"Add a leading `---` YAML frontmatter block to {rel} declaring "
                       "problem:, outcome:, and exit_criteria: (ADR-020).",
            })
            continue
        for field in CONTRACT_FIELDS:
            if not _has_content(fields.get(field, "")):
                findings.append({
                    "subject": f"{rel} → {field}:",
                    "what": f"frontmatter does not declare a non-empty `{field}:` "
                            "(ADR-020 component contract).",
                    "fix": f"Declare `{field}:` in {rel}'s frontmatter with content. "
                           "An empty value or an empty list asserts nothing and does "
                           "not satisfy the contract.",
                })

    for path in all_agent_files(root):
        stem = os.path.splitext(os.path.basename(path))[0]
        rel = f"agents/{stem}.md"
        fields = read_agent_config(path)
        if fields is None:
            findings.append({
                "subject": f"{rel} → no Agent Configuration/Specification block",
                "what": "no fenced config block under `## Agent Configuration` or "
                        "`## Agent Specification`; the component contract has no carrier.",
                "fix": f"Add a `## Agent Configuration` section to {rel} with a fenced "
                       "block declaring problem:, outcome:, and exit_criteria: "
                       "(`## Agent Specification` with a ```yaml fence is equally valid).",
            })
            continue
        for field in CONTRACT_FIELDS:
            if not _has_content(fields.get(field, "")):
                findings.append({
                    "subject": f"{rel} → {field}:",
                    "what": f"the agent config block does not declare a non-empty "
                            f"`{field}:` (ADR-020 component contract).",
                    "fix": f"Declare `{field}:` in {rel}'s config block with content. "
                           "An empty value or an empty list asserts nothing and does "
                           "not satisfy the contract.",
                })

    return findings


def _offender_files(findings: list[dict]) -> set[str]:
    """The file half of each finding's subject — `a/b.md → field:` -> `a/b.md`."""
    return {finding["subject"].split(" →")[0] for finding in findings}


def contract_compliance(root: str, contract_findings: list[dict]) -> dict:
    """Counts, not finding text: the trend channel beside the work queue.

    Derived from the findings themselves rather than re-parsed, so the metric
    can never disagree with the list a maintainer is working through.
    """
    commands = [os.path.splitext(os.path.basename(p))[0] for p in all_command_files(root)]
    checkable = [stem for stem in commands if not is_infra(stem)]
    agents = [os.path.splitext(os.path.basename(p))[0] for p in all_agent_files(root)]
    offenders = _offender_files(contract_findings)
    return {
        "commands_checked": len(checkable),
        "commands_with_contract": sum(
            1 for stem in checkable if f"commands/{stem}.md" not in offenders),
        "agents_checked": len(agents),
        "agents_with_contract": sum(
            1 for stem in agents if f"agents/{stem}.md" not in offenders),
    }


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


def justified_ceiling(base_entry: dict, metric_key: str) -> tuple[float | None, str, str]:
    """Ceiling, text, and date for ONE (surface, metric) justification.

    Schema 3:  surfaces.<name>.justifications.<metric> =
                   {"value": <number>, "date": "YYYY-MM-DD", "text": "<why>"}
    A justification silences growth only up to `value`. Past it, the ratchet
    speaks again and names the ceiling that was passed. This is per METRIC by
    construction: `lines` and `chars` measure different kinds of growth, and a
    reason for one is not a reason for the other.

    Returns (None, "", "") when there is no usable justification: key absent,
    `justifications` not a dict, entry not a dict, `value` non-numeric, or
    `text` blank. The legacy schema-2 string form (`justification: "<why>"`)
    carries no bound, so it returns (None, <its text>, "") — the caller warns
    with a migration hint. An unbounded mute must not survive in old data.
    """
    justifications = base_entry.get("justifications")
    if isinstance(justifications, dict):
        record = justifications.get(metric_key)
        if isinstance(record, dict):
            value = record.get("value")
            text = str(record.get("text") or "").strip()
            date = str(record.get("date") or "").strip()
            # `bool` is an `int` subclass; `{"value": true}` is not a ceiling.
            if isinstance(value, (int, float)) and not isinstance(value, bool) and text:
                return value, text, date

    legacy = str(base_entry.get("justification") or "").strip()
    if legacy:
        return None, legacy, ""
    return None, "", ""


def check_baseline(baseline: dict | None, err: str | None, baseline_path: str,
                   metrics: dict) -> tuple[list[dict], list[dict]]:
    """The reduction ratchet (replaces GROWTH_TOLERANCE): every gated surface
    is compared to its own recorded baseline, per metric, independently.

      current <= baseline                            -> silent (down is free)
      current >  baseline, bound justification covers -> silent up to its `value`
      current >  baseline, past/absent/legacy bound   -> warning naming the delta

    "Down is free" is evaluated FIRST and UNCONDITIONALLY, so no justification
    state — valid, stale, malformed, or legacy — can make a shrinking surface
    warn.

    A justification is bound to a recorded ceiling, per metric, or it silences
    nothing (spec 2026-08-11-governor-instrumentation, Business Rule 9). The
    pre-schema-3 form read one string per SURFACE and skipped both metrics at
    any magnitude forever: one sentence bought unlimited unmonitored growth.
    See justified_ceiling() for the replacement.

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
    # Schema 2 and 3 are both readable: 3 only adds the per-metric
    # `justifications` map and drops the unbounded `justification` string, so a
    # committed schema-2 file still measures correctly. The reader accepting
    # both is what lets the writer bump to 3 without the introducing commit
    # failing its own eval run. Schema 1 (no `surfaces` map) stays structural.
    if baseline.get("schema") not in (2, 3) or not isinstance(surfaces, dict):
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
        for metric_key in ("lines", "chars"):
            base_value = base_entry.get(metric_key)
            current_value = current.get(metric_key)
            if not isinstance(base_value, (int, float)) or not isinstance(current_value, (int, float)):
                continue
            if current_value <= base_value:
                continue  # down is free — first, and unconditional
            # Read per METRIC, never per surface: a reason for `lines` is not a
            # reason for `chars`.
            ceiling, text, date = justified_ceiling(base_entry, metric_key)
            if ceiling is not None and current_value <= ceiling:
                continue  # covers the increment it names, and nothing more
            delta = current_value - base_value
            if ceiling is not None:
                what = (f"{name} {metric_key} grew from {base_value} to {current_value} "
                        f"(+{delta}), past the justified ceiling of {ceiling} recorded "
                        f"{date or 'undated'} (\"{text}\"). That justification covered "
                        f"growth to {ceiling}.")
            elif text:
                what = (f"surfaces.{name} carries a legacy unbounded `justification` "
                        f"(schema 2); it silences nothing. {name} {metric_key} grew from "
                        f"{base_value} to {current_value} (+{delta}).")
            else:
                what = (f"{name} {metric_key} grew from {base_value} to {current_value} "
                        f"(+{delta}) with no justification recorded for this metric.")
            warnings.append({
                "subject": f"{name}.{metric_key}",
                "what": what,
                "fix": "Prune the surface back down — the delta is the signal — or record "
                       f"the increment: set surfaces.{name}.justifications.{metric_key} to "
                       f'{{"value": {current_value}, "date": "YYYY-MM-DD", "text": "<why>"}} '
                       f"in {relpath(baseline_path)}. That silences growth to "
                       f"{current_value} and nothing beyond it. --update-baseline is the "
                       "other option: it moves EVERY surface's floor to its current "
                       "measurement and records no reason.",
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
        # ratchets down automatically) and `justifications` resets to {} —
        # a justification describes a specific past delta, and that delta no
        # longer exists once absorbed into the new baseline. Under a BOUND
        # justification the reset is more clearly right than it was under the
        # old string: a recorded ceiling at or below the new floor is dead
        # data, silencing nothing it did not already silence. A future
        # increase past this fresh baseline requires a fresh bound entry.
        #
        # The legacy `justification` string key is not written at all —
        # schema 3 replaced it, and carrying an empty one forward would keep
        # the shape of a mute that no longer exists.
        payload = {
            "recorded": _today(),
            "schema": 3,
            "surfaces": {
                name: {
                    "lines": per_surface["lines"],
                    "chars": per_surface["chars"],
                    "justifications": {},
                }
                for name, per_surface in metrics["per_surface"].items()
            },
            "commands": metrics["commands"],
            "agents": metrics["agents"],
            "skills": metrics["skills"],
            "command_lines": metrics["command_lines"],
            "command_chars": metrics["command_chars"],
            "total_product_lines": metrics["total_product_lines"],
            "note": "Down is free. An increase to a gated surface is silent only up "
                    "to a recorded ceiling: set surfaces.<name>.justifications.<lines"
                    "|chars> to {\"value\": <measurement>, \"date\": \"YYYY-MM-DD\", "
                    "\"text\": \"<why>\"}. It silences growth to that value and nothing "
                    "beyond it. Rerunning --update-baseline instead moves EVERY "
                    "surface's floor to its current measurement and records no reason.",
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

    # Component-contract instrumentation. Every check below is a pure function
    # returning list[dict]; emit_contract_findings() is the only thing that
    # decides which bucket they land in (CONTRACT_CHECK_SEVERITY).
    contract_findings = check_component_contract(root)
    emit_contract_findings(contract_findings, structural, warnings)
    metrics["contract_compliance"] = contract_compliance(root, contract_findings)

    json.dump({"structural": structural, "warnings": warnings, "metrics": metrics},
              sys.stdout, indent=2)
    sys.stdout.write("\n")
    return 0


def _today() -> str:
    import datetime
    return datetime.date.today().isoformat()


if __name__ == "__main__":
    sys.exit(main())
