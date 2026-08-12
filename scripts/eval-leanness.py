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
                     "contract_compliance", "required_skills_declarations",
                     "inline_skill_reads", "command_budget",
                     "per_command_invocation"}
    }

  Component-contract findings (see CONTRACT_CHECK_SEVERITY) are BLOCKING as
  of 2026-08-12: 2026-08-12-governor-enforcement threw that one constant to
  "structural" once the surface measured compliant. "contract_compliance" is
  the coverage channel beside them — counts of files checked and files
  compliant, so a red or green run says how much surface it covers. The
  absolute per-invocation byte budget (COMMAND_BYTE_BUDGET) is a separate
  decision under COMMAND_BUDGET_SEVERITY and is reported non-blocking; the
  reasoning is at its constant.

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
import ast
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

# MAX_SKILLS: 12 -> 45, re-derived 2026-08-12 by 2026-08-12-governor-enforcement
# Story 7. Five sibling specs flagged the old 12 and none could take it, because
# every progressive-disclosure spec bars itself from scripts/.
#
#     MAX_SKILLS = MAX_COMMANDS + MAX_AGENTS = 35 + 10 = 45
#
# WHY THAT, AND NOT A NUMBER THAT CLEARS THE ROSTER. Under ADR-021 a skill is
# not an independent artifact: it exists only because a CONSUMER — a command or
# an agent — extracted a capability out of itself, and §4 requires shared
# capability rather than per-consumer copies. So the skill population is
# structurally bounded by the consumer population, and that population already
# carries two deliberate ceilings, in this block, set for their own reasons.
# One skill per potential consumer is the line where extraction has stopped
# producing shared capability and become a 1:1 shadow of the consumer surface —
# ADR-021 §4's "two copies instead of one shared skill" expressed as a count,
# which is the only thing a count can meaningfully express here.
#
# 2026-08-11-autonomy-gate-classes Business Rule 1: "a cap chosen after the fact
# to accommodate whatever was written is not a cap." The three tests it implies:
#   - computed from constants that exist for other reasons — MAX_COMMANDS and
#     MAX_AGENTS are untouched here, and the derivation never reads the roster;
#   - IT CAN STILL FIRE — it fires at 46, and ADR-021 §4 explicitly anticipates
#     a second disclosure programme (implement-spec among its targets);
#   - it moves only when its inputs move, each by a deliberate edit.
# The counterfactual is the whole argument: had the phase's roster landed at 50,
# this derivation would still yield 45, the cap would fire, and the correct
# output would be a Tier B escalation rather than a bigger constant.
#
# MEASURED 2026-08-12: the corpus is 14 skills — 31 of headroom. The phase's
# authored rosters projected 35 (29 new across six specs + 6 existing), but five
# of the six disclosure specs were closed UNIMPLEMENTED after the pilot measured
# ~1,017 bytes of per-skill overhead and a +9.7% worst-path ceiling regression.
# Only the pilot's 8 landed. The projection is recorded because the derivation
# must be answerable to it and clears it either way, not because 14 was the
# input — a cap derived from what shipped could not have said anything about
# what did not.
#
# WARN-ONLY, and stated because everything around it became blocking. A count is
# not a unit of load: that is ADR-021's central finding, and Story 3 of the same
# spec retires a 2000-line command limit for exactly that reason
# (commands/implement-phase.md is 321 lines and 4,176 bytes over budget). Three
# further reasons, each independently sufficient: a blocking count cap would
# BLOCK THE FIX, since under conditional loading a skill on an untaken path
# costs that run nothing and extraction is the action that lowers per-invocation
# load; skill bloat is already governed in BYTES by ADR-019's per-surface
# ratchet with schema-3 bound justifications, which is the right unit and is
# blocking; and the ceiling_bytes budget that would supersede this count is
# deferred pending post-disclosure data. Revisit condition, recorded now: if a
# ceiling_bytes budget is ever adopted, this count cap becomes REDUNDANT, not
# stricter.
MAX_SKILLS = 45

# --- The absolute per-invocation byte budget (spec: 2026-08-12-governor-
# enforcement Story 2; decision: ADR-021 reason 3 + its 2026-08-12 amendment)
#
# "A ratchet is not a budget." check_baseline()'s per-surface delta ratchet
# stays exactly as it is; this is an absolute ceiling ALONGSIDE it. They answer
# different questions — the ratchet detects drift from a recorded floor, the
# budget refuses a size regardless of history.
#
# The budget is the irreducible shared base every invocation pays before it
# reads the command it was asked to run:
#     system-instructions.md   20,153
#     commands/_preamble.md     4,807
#                              ------
#                              24,960   (measure-invocation.py -> base.bytes)
#
# A command file may not cost more to load than the shared contract it runs
# inside. PINNED, not derived live: a live derivation would let growth in
# system-instructions.md silently raise every command's allowance, which is
# reason 3 rebuilt in a new place. check_budget_derivation() reports base drift
# as a non-blocking finding so re-deriving stays a deliberate, dated act.
COMMAND_BYTE_BUDGET = 24960
COMMAND_BYTE_BUDGET_DERIVED = (
    "2026-08-12: pinned by decision. Originally derived as "
    "system-instructions.md + commands/_preamble.md, and NO LONGER derived from them."
)

# Why the budget is pinned rather than tracking its base (decided 2026-08-12).
#
# The original rule read: a command may not cost more to load than the shared
# contract it runs inside. As a *live derivation* that rule has a perverse
# incentive, and it fired within a day of shipping — correcting the
# required_skills: record grew system-instructions.md by 1,298 bytes, which
# would have RAISED every command's allowance by the same amount.
#
# system-instructions.md and _preamble.md are paid on EVERY invocation, so a
# byte there is the most expensive byte in the repository. A rule where growing
# the most expensive surface relaxes the constraint on every other one serves
# its own letter and defeats its purpose. The number is therefore a decision
# with a date; check_budget_derivation() reports base drift for a human to act
# on, and never adjusts anything.
#
# The base gets its own tighter cap below — the constraint the original rule was
# reaching for, pointed at the surface that actually deserves it.
BASE_BYTE_CAP = 25600

# The two files the budget was derived from, in the order the derivation
# records them. Read live by check_budget_derivation() and by nothing else.
BUDGET_BASE_COMPONENTS = ("system-instructions.md", os.path.join("commands", "_preamble.md"))

# NON-BLOCKING, by the 2026-08-12 (d) rescope, and the reasoning belongs at the
# constant rather than in a spec folder:
#
# The five sibling progressive-disclosure specs were closed UNIMPLEMENTED after
# the pilot (2026-08-12-disclosure-implement-story) measured ~1,017 bytes of
# per-skill extraction overhead and a +9.7% worst-path ceiling regression. Five
# of the six target commands are therefore unconverted and stay over budget,
# and nobody is converting them. Landing this cap blocking would make eval.sh
# permanently red on files no owner exists for — and a permanently-red gate
# becomes invisible, which is precisely the ADR-021 reason 2 failure this spec
# was written to prevent.
#
# So the cap ships MEASURED and REPORTED: computed on every run, every violator
# named with its overage in `warnings` and in `metrics.command_budget`.
#
# DEMOTED PERMANENTLY, 2026-08-12, by ADR-023 (stakes-proportional diligence).
# The paragraph above framed non-blocking as circumstantial — "blocking once a
# future decision converts the remaining commands." That decision came, and it
# went the other way: there will be no conversion, and byte count is no longer
# a design constraint at any threshold.
#
# The reason is that this cap measures the wrong quantity. The goal is economy
# of steps and ruminations to reach exit criteria; bytes measure file size.
# Where they diverge bytes point the wrong way — the pilot cut implement-story's
# floor 35.9% while adding eight decision points, five of which fire on every
# run and buy nothing. No byte instrument can see that: it counts what is
# loaded, never what must be decided.
#
# Nothing here is deleted. The number is still computed and still reported,
# because the ADR-019 ratchet is cheap and does catch genuine runaway growth.
# Only its AUTHORITY is removed: no command is restructured to satisfy it, and
# it must not be flipped to blocking without a recorded derivation linking the
# threshold to measured harm. Reviewed 2026-11-11 with ADR-021 and ADR-023.
#
# What is NOT done to make it green: no command gains an `eval-exempt:` marker
# and this module gains no exemption reader (Business Rule 1). The half of the
# deliverable the surface passes — the four component-contract checks — flips
# to blocking on its own evidence (CONTRACT_CHECK_SEVERITY). Enforcing what
# complies and warning on what does not is the deliverable applied honestly,
# not a softened one.
COMMAND_BUDGET_SEVERITY = "warnings"

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
# THE FLIP WAS THROWN ON 2026-08-12 by 2026-08-12-governor-enforcement Story 5.
# The whole handoff lives here, at the constant, rather than in a spec folder —
# which is what the seam was built for. Everything below this line is history a
# reader arriving cold needs, not decoration.
#
#     -CONTRACT_CHECK_SEVERITY = "warnings"
#     +CONTRACT_CHECK_SEVERITY = "structural"
#
# One string. Nothing else changed: every check below is still a pure function
# returning list[dict] and still routes through emit_contract_findings(). That
# was 2026-08-11-governor-instrumentation Story 7's promise and it held.
#
# THE PRECONDITION, MEASURED BEFORE IT WAS THROWN (Story 4, and it is a
# committed test — ComplianceGateTests in scripts/tests/test_governor_
# enforcement.py — not a note someone wrote after checking once):
#
#     contract_compliance   commands_with_contract   31/31
#                           commands_with_completion 31/31
#                           loop_commands_bounded      5/5
#                           agents_with_contract       7/7
#     required_skills_declarations                       0
#     structural under an in-process "structural" pin   []
#
# The last line is the one that mattered: `structural: []` under the shipped
# "warnings" value proves nothing, because the findings would sit in `warnings`
# either way. Pinning "structural" in-process and finding the list STILL empty
# is what proved the flip was safe. That test stays in the suite as the
# permanent regression guard for the state this constant now depends on.
#
# GOVERNING DECISIONS. ADR-020 "Enforcement sequencing (load-bearing)": checks
# land as `warnings` and flip to blocking ONLY once the migration brings the
# surface into compliance. ADR-021 reason 2 ("growth warns, it does not fail")
# is what this answers — the reason the old governor never caught 516KB of
# command prose. Both are satisfied in that order and not before.
#
# WHAT AN UN-FLIP WOULD MEAN. Setting this back to "warnings" does not weaken
# one check; it silently disarms all four across every command and agent, and
# the surface would stay green while drifting. If a future migration genuinely
# needs the channel quiet, un-flip DELIBERATELY, record the date and the reason
# here, and expect FlipSeamTests.test_shipped_default_is_structural to go red —
# that test exists to make an accidental un-flip impossible to land unnoticed.
#
# WHAT THIS CONSTANT DOES NOT GOVERN. The absolute per-invocation byte budget
# (COMMAND_BYTE_BUDGET / COMMAND_BUDGET_SEVERITY) is its own decision and never
# routes through here — one string must not control two independent gates, or
# an un-flip would take the budget out as collateral. `check_required_skills`
# stays pinned to "warnings" regardless of this value, per system-instructions.md's
# graceful-degradation contract. An unrecognised value here still falls back to
# "warnings": a typo must never silently disable a check and must never
# accidentally block a run.
CONTRACT_CHECK_SEVERITY = "structural"

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


def has_completion_section(path: str) -> bool | None:
    """True/False for an exact `## Completion` H2; None when unreadable.

    Exact match is deliberate. A tolerant `startswith("## Completion")` would
    accept `## Completion Criteria`, which defeats the point of one canonical
    section name that /verify-spec and /refresh-command can later key off.
    Fenced regions are skipped — a command file quoting `## Completion` as
    example markdown has not declared one — using the same fence tracking
    readme_command_names() already does in this module.
    """
    try:
        with open(path, encoding="utf-8") as handle:
            lines = handle.read().split("\n")
    except (OSError, UnicodeDecodeError):
        return None
    in_fence = False
    for line in lines:
        if line.strip().startswith("```"):
            in_fence = not in_fence
            continue
        if in_fence:
            continue
        if line.rstrip() == "## Completion":
            return True
    return False


def check_completion_sections(root: str) -> list[dict]:
    """Every non-invokable command declares where it stops.

    Presence, not content: a `## Completion` heading with nothing under it
    passes. Asserting the section is *useful* means judging prose, which is
    exactly what ADR-020 rejects.
    """
    findings: list[dict] = []
    for path in all_command_files(root):
        stem = os.path.splitext(os.path.basename(path))[0]
        if is_infra(stem):
            continue
        present = has_completion_section(path)
        if present is not False:
            continue  # True, or None (unreadable — measure_files already said so)
        rel = f"commands/{stem}.md"
        findings.append({
            "subject": f"{rel} → ## Completion",
            "what": f"no `## Completion` section; {rel} never states the condition "
                    "under which a run of it is finished.",
            "fix": "Add a `## Completion` section (exact H2 spelling — "
                   "`## Completion Criteria` and `### Completion` do not satisfy "
                   "this check, and a heading inside a fenced block does not "
                   "count). See commands/new-command.md's generated-command "
                   "structure for the authoring template.",
        })
    return findings


# The two fields 2026-08-11-loop-bounds requires at the top level of `loop:`.
# That spec owns the shape; this check asserts PRESENCE only and defers every
# question of correctness — enum closure, integer type, citation quality, unit
# uniqueness, historical-run regression — to scripts/eval-loop-bounds.py.
# Presence and correctness are checked once each, by one owner each: a
# maintainer who sees the same missing field reported twice learns to skim.
LOOP_BOUND_FIELDS = ("max_iterations", "on_exhaustion")

# The five loop-bearing commands, measured in Phase 10 discovery (roadmap
# Phase 10 -> Problem table: "Loop-bearing commands declaring an iteration
# bound: 0 of 5"). Deliberately a fixed list, never inferred from file
# contents: inferring "does this command loop?" from prose needs a
# heading/keyword grammar per variant, the exact fragility ADR-020 rejects.
#
# The list is CROSS-READ from scripts/eval-loop-bounds.py, which declares
# itself the enforcement point when a sixth command acquires a loop. Presence
# and correctness split one population; two hand-maintained copies of it would
# drift, and a drifted split reports a file twice or not at all. The literal
# below is the fallback for a tree where the sibling is absent or unparseable
# — never a second source of truth.
LOOP_BEARING_COMMANDS_FALLBACK = (
    "implement-phase", "implement-spec", "implement-story", "refactor", "verify-spec",
)


def _loop_bearing_from_sibling() -> list[str] | None:
    """Read LOOP_BEARING_COMMANDS out of scripts/eval-loop-bounds.py.

    Parsed with `ast`, not imported: the sibling has a hyphenated filename and
    executing it for a constant would be a heavier contract than reading one.
    Any failure returns None so the fallback applies — a cross-read that
    cannot happen must never empty the population.
    """
    sibling = os.path.join(os.path.dirname(os.path.abspath(__file__)),
                           "eval-loop-bounds.py")
    try:
        with open(sibling, encoding="utf-8") as handle:
            tree = ast.parse(handle.read())
    except (OSError, SyntaxError, UnicodeDecodeError, ValueError):
        return None
    for node in tree.body:
        if not isinstance(node, ast.Assign):
            continue
        if not any(isinstance(target, ast.Name)
                   and target.id == "LOOP_BEARING_COMMANDS" for target in node.targets):
            continue
        try:
            value = ast.literal_eval(node.value)
        except (ValueError, TypeError, SyntaxError):
            return None
        if isinstance(value, (list, tuple)) and value and all(
                isinstance(item, str) for item in value):
            return list(value)
    return None


LOOP_BEARING_COMMANDS = tuple(_loop_bearing_from_sibling()
                              or LOOP_BEARING_COMMANDS_FALLBACK)


def _declares_loop_field(fields: dict[str, str], field: str) -> bool:
    """True when `loop.<field>` is declared, nested under `loop:` or flattened.

    Both shapes are accepted because 2026-08-11-loop-bounds owns the final
    form — slack in the reader, never ambiguity in the contract.
    """
    if _has_content(fields.get(f"loop.{field}", "")):
        return True
    block = fields.get("loop", "")
    return bool(re.search(r"(?:^|\s)" + re.escape(field) + r":\s*\S", block))


def check_loop_bounds(root: str) -> list[dict]:
    """Each loop-bearing command declares how many times it may go round.

    A named command that does not exist on disk is itself a finding, so the
    population cannot silently rot the way GATE_AGENT_FILES can — its own
    comment admits it is "kept in sync by hand" and understates a metric when
    a gate is added and not mirrored.
    """
    findings: list[dict] = []
    for name in LOOP_BEARING_COMMANDS:
        rel = f"commands/{name}.md"
        path = os.path.join(root, "commands", f"{name}.md")
        if not os.path.isfile(path):
            findings.append({
                "subject": f"{rel} → missing",
                "what": f"`{name}` is named as loop-bearing but no such command file "
                        "exists; the population this check measures has rotted.",
                "fix": f"Restore {rel}, or remove `{name}` from LOOP_BEARING_COMMANDS "
                       "in scripts/eval-loop-bounds.py (the list this check cross-reads).",
            })
            continue
        fields = read_frontmatter(path)
        if fields is None:
            findings.append({
                "subject": rel,
                "what": "no frontmatter block; the iteration bound has nowhere to live.",
                "fix": f"Add a leading `---` YAML frontmatter block to {rel} declaring "
                       "`loop:` with max_iterations and on_exhaustion.",
            })
            continue
        for field in LOOP_BOUND_FIELDS:
            if _declares_loop_field(fields, field):
                continue
            findings.append({
                "subject": f"{rel} → loop.{field}",
                "what": f"loop-bearing command declares no `{field}`; a bound with no "
                        "exhaustion behaviour (or an exhaustion behaviour with no "
                        "bound) is half a contract.",
                "fix": f"Declare `{field}:` under `loop:` in {rel}'s frontmatter. "
                       "scripts/eval-loop-bounds.py then asserts the value is legal "
                       "and honestly calibrated.",
            })
    return findings


def parse_skill_names(raw: str) -> list[str]:
    """Skill names from a `required_skills:` value, in declaration order.

    Accepts the inline flow form (`[tdd-cycle, gbrain-interop]`) and the block
    list form, which _parse_fields() joins into `- tdd-cycle - gbrain-interop`.
    Duplicates are silently deduplicated, per system-instructions.md's schema.
    """
    value = raw.strip()
    if not value or value in ("[]", "{}", "~", "null"):
        return []
    value = value.strip("[]")
    names: list[str] = []
    for token in re.split(r"[,\s]+", value):
        token = token.strip("-\"' ")
        if token and token not in names:
            names.append(token)
    return names


# The phase's ACTUAL loading mechanism. The 2026-08-12 mechanism ruling
# (ADR-021, second amendment) retired `required_skills:` for Phase 10 because
# it is an EAGER pre-load — the harness loads every declared skill "before any
# phase work begins", so extraction under it moves bytes into the floor and
# makes a command cost MORE per invocation than the monolith it replaced. Every
# consumer switched to an inline `Read skills/<name>/SKILL.md` at the point of
# need, which is genuinely conditional.
#
# Byte-identical to scripts/measure-invocation.py's INLINE_READ, and a test
# asserts the two patterns stay equal: one accounting, two readers. A literal
# `<name>` placeholder (commands/new-skill.md teaches the form) cannot match —
# angle brackets are outside the class — so documenting the convention is never
# a finding.
INLINE_SKILL_READ = re.compile(r"Read\s+skills/([A-Za-z0-9._-]+)/SKILL\.md")


def inline_skill_reads(path: str) -> list[str]:
    """Skill names an inline `Read skills/<n>/SKILL.md` in the body would load.

    Frontmatter is excluded so a `required_skills:` block is never counted as
    an inline read. Order-preserving and deduplicated, matching the declared
    path's own schema.
    """
    try:
        with open(path, encoding="utf-8") as handle:
            text = handle.read()
    except (OSError, UnicodeDecodeError):
        return []
    if text.startswith("---"):
        end = text.find("\n---", 3)
        if end != -1:
            text = text[end + 4:]
    names: list[str] = []
    for match in INLINE_SKILL_READ.finditer(text):
        if match.group(1) not in names:
            names.append(match.group(1))
    return names


def check_required_skills(root: str) -> tuple[list[dict], int, int]:
    """Every skill name a consumer names resolves to a real SKILL.md.

    BOTH mechanisms, since 2026-08-12-governor-enforcement Story 7. Returns
    (findings, declaration_count, inline_read_count).

    Two counts because there are two loading mechanisms and they mean opposite
    things. `required_skills:` is EAGER — the harness loads every declared skill
    "before any phase work begins" (system-instructions.md -> Harness contract;
    adapters/claude-code.md), so a declaration moves those bytes into the floor
    where every invocation pays them. An inline `Read skills/<n>/SKILL.md` is
    CONDITIONAL — it costs a run only if execution reaches it. Phase 10 measured
    that difference and retired the declarative form, so declaration_count is 0
    by design and indefinitely, while inline_read_count is where the whole
    surface actually lives.

    Reporting both is Business Rule 8 of 2026-08-11-governor-instrumentation
    doing its job: "0 findings" must not read the same as "0 things checked",
    and a permanent 0 on one mechanism is only legible next to a non-zero count
    on the other. check_baseline() is the established precedent for a check that
    returns more than a bare list.

    WHY THE INLINE HALF EXISTS. Until this story, a mistyped
    `Read skills/tdd-cyle/SKILL.md` was a silent no-op: the gate passed, the
    skill never loaded, and the command quietly lost a capability with nothing
    failing anywhere. The phase moved its entire skill-loading surface from a
    mechanism WITH a resolution check to one WITHOUT.
    scripts/measure-invocation.py does report it under `unresolved_skills`, but
    it always exits 0 by design and therefore cannot gate.

    Resolution is a filesystem check, never a lookup in .writ/manifest.yaml:
    the manifest is separately known-stale, and resolving against it would
    produce findings about the manifest rather than about the declaration.
    """
    findings: list[dict] = []
    declarations = 0
    inline_reads = 0

    sources: list[tuple[str, str, dict[str, str] | None]] = []
    for path in all_command_files(root):
        stem = os.path.splitext(os.path.basename(path))[0]
        if is_infra(stem):
            continue
        sources.append((f"commands/{stem}.md", path, read_frontmatter(path)))
    for path in all_agent_files(root):
        stem = os.path.splitext(os.path.basename(path))[0]
        sources.append((f"agents/{stem}.md", path, read_agent_config(path)))

    def resolves(name: str) -> bool:
        return os.path.isfile(os.path.join(root, "skills", name, "SKILL.md"))

    for rel, path, fields in sources:
        # A missing carrier is check_component_contract's finding, not this
        # one — but the body is still readable, and an inline read in a file
        # with no frontmatter is exactly as broken as one in a file with it.
        for name in parse_skill_names((fields or {}).get("required_skills", "")):
            declarations += 1
            if resolves(name):
                continue
            findings.append({
                "subject": f"{rel} → required_skills: {name}",
                "what": f"declared skill `{name}` resolves to no "
                        f"skills/{name}/SKILL.md.",
                "fix": f"Create skills/{name}/SKILL.md, correct the name in {rel}, "
                       f"or drop it from required_skills:.",
            })

        for name in inline_skill_reads(path):
            inline_reads += 1
            if resolves(name):
                continue
            findings.append({
                "subject": f"{rel} → Read skills/{name}/SKILL.md",
                "what": f"inline read of `{name}` resolves to no "
                        f"skills/{name}/SKILL.md. This is a silent no-op at "
                        "run time: the agent issues the read, nothing loads, "
                        "and the command quietly runs without the capability.",
                "fix": f"Create skills/{name}/SKILL.md, correct the path in {rel}, "
                       "or remove the read. Inline reads are the phase's loading "
                       "mechanism (ADR-021, amended 2026-08-12), so a typo here "
                       "costs a capability rather than a byte.",
            })

    return findings, declarations, inline_reads


def _offender_files(findings: list[dict]) -> set[str]:
    """The file half of each finding's subject — `a/b.md → field:` -> `a/b.md`."""
    return {finding["subject"].split(" →")[0] for finding in findings}


def contract_compliance(root: str, contract_findings: list[dict],
                        completion_findings: list[dict],
                        loop_findings: list[dict]) -> dict:
    """Counts, not finding text: the trend channel beside the work queue.

    Derived from the findings themselves rather than re-parsed, so the metric
    can never disagree with the list a maintainer is working through.
    """
    commands = [os.path.splitext(os.path.basename(p))[0] for p in all_command_files(root)]
    checkable = [stem for stem in commands if not is_infra(stem)]
    agents = [os.path.splitext(os.path.basename(p))[0] for p in all_agent_files(root)]
    offenders = _offender_files(contract_findings)
    without_completion = _offender_files(completion_findings)
    unbounded = _offender_files(loop_findings)
    return {
        "commands_checked": len(checkable),
        "commands_with_contract": sum(
            1 for stem in checkable if f"commands/{stem}.md" not in offenders),
        "commands_with_completion": sum(
            1 for stem in checkable if f"commands/{stem}.md" not in without_completion),
        "loop_commands_checked": len(LOOP_BEARING_COMMANDS),
        "loop_commands_bounded": sum(
            1 for name in LOOP_BEARING_COMMANDS
            if f"commands/{name}.md" not in unbounded),
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


# --- The absolute per-invocation byte budget -------------------------------
#
# Accounting is REUSED, never re-invented. scripts/measure-invocation.py loads
# this module by path to reuse its parsers (all_command_files, is_infra,
# read_frontmatter, parse_skill_names), so the dependency runs measure ->
# leanness and cannot be reversed without a cycle. The cap therefore lives here
# and uses the identical definition of command_bytes: the raw byte length of
# the file. Two implementations of "how big is this command" that can disagree
# is a defect waiting for its first file, so a test asserts the two agree per
# command against the real repo.


def _read_command_bytes(path: str) -> int | None:
    """Raw byte length, or None when the file cannot be read.

    None is a distinguishable outcome rather than a 0, because a 0 would read
    as a compliant empty command and silently exempt an unreadable file from
    the budget.
    """
    try:
        with open(path, "rb") as handle:
            return len(handle.read())
    except OSError:
        return None


def command_byte_sizes(root: str) -> dict[str, int]:
    """Non-infra command stem -> raw file bytes. Unreadable files are omitted.

    The shared accounting behind both check_command_budget() and
    metrics.per_command_invocation, and the thing that must equal
    measure-invocation.py's `command_bytes` for every command.
    """
    sizes: dict[str, int] = {}
    for path in all_command_files(root):
        stem = os.path.splitext(os.path.basename(path))[0]
        if is_infra(stem):
            continue
        size = _read_command_bytes(path)
        if size is not None:
            sizes[stem] = size
    return sizes


def check_command_budget(root: str) -> list[dict]:
    """A command file may not cost more to load than the contract it runs in.

    Pure function returning list[dict]. It reads no baseline, consults no
    `justifications` map, and knows nothing about CONTRACT_CHECK_SEVERITY: a
    justification explains growth against a BASELINE and has no meaning against
    an ABSOLUTE budget (Business Rule 3), and the flip governs the four
    component-contract checks it was built for, not this. Non-silenceability is
    structural — there is no exemption reader in this module to reach for.

    `commands/_preamble.md` is base, not a command, and is excluded by the
    existing is_infra() rule. Hardcoding the filename here would be the defect.
    """
    findings: list[dict] = []
    for path in all_command_files(root):
        stem = os.path.splitext(os.path.basename(path))[0]
        if is_infra(stem):
            continue
        rel = f"commands/{stem}.md"
        size = _read_command_bytes(path)
        if size is None:
            findings.append({
                "subject": rel,
                "what": "the file could not be read, so its per-invocation cost "
                        "is unknown and the budget could not be applied.",
                "fix": f"Restore read permission on {rel} (or fix its encoding) "
                       "and re-run. An unmeasurable command is not a compliant one.",
            })
            continue
        # `>` and not `>=`: exactly at budget is compliant.
        if size <= COMMAND_BYTE_BUDGET:
            continue
        over = size - COMMAND_BYTE_BUDGET
        findings.append({
            "subject": rel,
            "what": f"{size} bytes, over the {COMMAND_BYTE_BUDGET}-byte "
                    f"per-invocation budget by {over} "
                    f"({round(100.0 * size / COMMAND_BYTE_BUDGET)}% of budget). "
                    "A command may not cost more to load than the shared "
                    "contract it runs inside.",
            "fix": "Extract procedural detail to skills/<name>/SKILL.md and load "
                   f"it inline at its point of need (ADR-021, amended 2026-08-12). "
                   f"Budget derivation: {COMMAND_BYTE_BUDGET_DERIVED}. "
                   "Reported non-blocking today because the disclosure specs that "
                   "owned this file were closed unimplemented — never exempt it.",
        })
    return findings


def check_base_budget(root: str) -> list[dict]:
    """The shared base is paid on every invocation, so it is capped tightest.

    Non-blocking, matching the command budget's disposition: a number a human
    decides about. It exists because the original base-parity rule left the most
    expensive surface in the repository entirely ungoverned, while using it to
    set everyone else's allowance.
    """
    live = 0
    for component in BUDGET_BASE_COMPONENTS:
        try:
            with open(os.path.join(root, component), "rb") as handle:
                live += len(handle.read())
        except OSError:
            return []
    if live <= BASE_BYTE_CAP:
        return []
    return [{
        "subject": "BASE_BYTE_CAP",
        "what": f"the shared base measures {live} bytes, over its {BASE_BYTE_CAP}-byte "
                f"cap by {live - BASE_BYTE_CAP}. Every invocation pays this, so it is "
                f"the most expensive surface in the repository.",
        "fix": "Trim system-instructions.md or commands/_preamble.md on merit, or raise "
               "BASE_BYTE_CAP deliberately with a dated reason. Do not raise it to fit "
               "whatever was just added.",
    }]


def check_budget_derivation(root: str) -> list[dict]:
    """COMMAND_BYTE_BUDGET is pinned; the base it was derived from is live.

    Base drift must be a visible finding demanding a deliberate re-derivation,
    never a silent allowance increase — a budget that tracks its own inputs is
    ADR-021 reason 3 rebuilt. This check therefore reports and never mutates.
    """
    live = 0
    for component in BUDGET_BASE_COMPONENTS:
        size = _read_command_bytes(os.path.join(root, component))
        live += size or 0
    if live == COMMAND_BYTE_BUDGET:
        return []
    delta = live - COMMAND_BYTE_BUDGET
    components = " + ".join(BUDGET_BASE_COMPONENTS)
    return [{
        "subject": "COMMAND_BYTE_BUDGET",
        "what": f"the pinned budget is {COMMAND_BYTE_BUDGET} bytes "
                f"({COMMAND_BYTE_BUDGET_DERIVED}); the live base "
                f"({components}) now measures {live}, a delta of "
                f"{delta:+d}. The budget is UNCHANGED — this is a report, not "
                "an adjustment.",
        "fix": "Re-derive COMMAND_BYTE_BUDGET deliberately and re-record it with "
               "its components and a date, or shrink the base back. Never let the "
               "budget track its own inputs: a self-raising ceiling is ADR-021 "
               "reason 3 in a new place.",
    }]


def per_command_invocation(root: str) -> dict:
    """command_bytes / floor_bytes / ceiling_bytes for every non-infra command.

    ADR-021 caveat 2 — disclosure can RAISE total load, because a command that
    pulls every skill costs more than the monolith did — is made visible here
    as a metric rather than gated. Gating on ceiling_bytes needs post-disclosure
    data this spec is the first to produce, and is a decision it does not have.

    floor  = base + command + every EAGER byte (a `required_skills:` skill is
             pre-loaded before any phase work begins, so every invocation pays
             it — see system-instructions.md -> Harness contract).
    ceiling = floor + every CONDITIONAL byte (inline `Read skills/<n>/SKILL.md`
             occurrences, which only cost a run that reaches them). It is an
             ENVELOPE, not a path: mutually exclusive branches are both summed.
    """
    base = 0
    for component in BUDGET_BASE_COMPONENTS:
        base += _read_command_bytes(os.path.join(root, component)) or 0

    def skill_bytes(name: str) -> int:
        return _read_command_bytes(os.path.join(root, "skills", name, "SKILL.md")) or 0

    report: dict[str, dict] = {}
    for path in all_command_files(root):
        stem = os.path.splitext(os.path.basename(path))[0]
        if is_infra(stem):
            continue
        size = _read_command_bytes(path)
        if size is None:
            continue
        fields = read_frontmatter(path) or {}
        eager = [n for n in parse_skill_names(fields.get("required_skills", ""))]
        conditional = [n for n in inline_skill_reads(path) if n not in eager]
        eager_bytes = sum(skill_bytes(name) for name in eager)
        conditional_bytes = sum(skill_bytes(name) for name in conditional)
        floor = base + size + eager_bytes
        report[stem] = {
            "command_bytes": size,
            "floor_bytes": floor,
            "ceiling_bytes": floor + conditional_bytes,
        }
    return report


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

    # The absolute per-invocation byte budget (ADR-021 reason 3). Appended to
    # its bucket DIRECTLY — never through emit_contract_findings(), never
    # reading CONTRACT_CHECK_SEVERITY. Routing the budget behind the flip's
    # string would put two independent decisions behind one constant, so a
    # future un-flip (or the typo fallback) would disable the budget as
    # collateral. COMMAND_BUDGET_SEVERITY is the budget's own decision and
    # carries its own reasoning at the constant.
    budget_findings = check_command_budget(root)
    if COMMAND_BUDGET_SEVERITY == "structural":
        structural += budget_findings
    else:
        warnings += budget_findings
    # Base drift: pinned budget vs. live base. Non-blocking by design — it
    # demands a deliberate re-derivation, it never performs one.
    warnings += check_budget_derivation(root)
    warnings += check_base_budget(root)

    metrics["command_budget"] = {
        "budget": COMMAND_BYTE_BUDGET,
        "derivation": COMMAND_BYTE_BUDGET_DERIVED,
        "severity": COMMAND_BUDGET_SEVERITY,
        "checked": len(command_byte_sizes(root)),
        "over_budget": sorted(
            ({"subject": f"commands/{stem}.md", "bytes": size,
              "over_by": size - COMMAND_BYTE_BUDGET}
             for stem, size in command_byte_sizes(root).items()
             if size > COMMAND_BYTE_BUDGET),
            key=lambda entry: -entry["over_by"]),
    }
    metrics["command_budget"]["total_overage"] = sum(
        entry["over_by"] for entry in metrics["command_budget"]["over_budget"])
    metrics["per_command_invocation"] = per_command_invocation(root)

    # Component-contract instrumentation. Every check below is a pure function
    # returning list[dict]; emit_contract_findings() is the only thing that
    # decides which bucket they land in (CONTRACT_CHECK_SEVERITY).
    contract_findings = check_component_contract(root)
    completion_findings = check_completion_sections(root)
    loop_findings = check_loop_bounds(root)
    emit_contract_findings(contract_findings, structural, warnings)
    emit_contract_findings(completion_findings, structural, warnings)
    emit_contract_findings(loop_findings, structural, warnings)

    # PINNED NON-BLOCKING, even after the flip. system-instructions.md:
    # "Unknown skill names produce a warning at consumer load time, not a hard
    # failure (graceful degradation: a pilot extraction may rename a skill
    # mid-flight; consumers shouldn't break catastrophically)." Hard-failing
    # eval.sh on an unresolved name would contradict the root behavioral
    # contract during exactly the phase that renames skills most.
    skill_findings, skill_declarations, skill_inline_reads = check_required_skills(root)
    emit_contract_findings(skill_findings, structural, warnings, severity="warnings")

    metrics["contract_compliance"] = contract_compliance(
        root, contract_findings, completion_findings, loop_findings)
    metrics["required_skills_declarations"] = skill_declarations
    # Beside the permanently-zero declaration count, the count of the mechanism
    # the phase actually uses. Read them as a pair or neither means anything.
    metrics["inline_skill_reads"] = skill_inline_reads

    json.dump({"structural": structural, "warnings": warnings, "metrics": metrics},
              sys.stdout, indent=2)
    sys.stdout.write("\n")
    return 0


def _today() -> str:
    import datetime
    return datetime.date.today().isoformat()


if __name__ == "__main__":
    sys.exit(main())
