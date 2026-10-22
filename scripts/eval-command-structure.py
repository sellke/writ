#!/usr/bin/env python3
"""Check the structure that converted literal pins used to guard in commands.

Spec: 2026-10-20-shipped-command-hygiene, Story 2. Consumed by scripts/eval.sh
check_command_structure.

Some eval.sh literal pins on commands/*.md guarded structure rather than
wording: a heading, a frontmatter key, or a script call. A substring pin
passes when the heading turns into prose or the call turns into a bare
mention. Each such pin is now one row in ROWS, checked by structure. Rules
added later with no earlier pin get rows here too, not literal pins:

  heading      a line outside fenced code is a heading (^#{1,6} ) whose text
               begins with the value, so "User Challenge" matches
               "## User Challenge (Scope-Degradation Escalation)"
  frontmatter  the YAML frontmatter block has a top-level "<value>:" key
  invocation   a line contains the value, the script path plus the subcommand
               (and any flags or arguments) the command must call, with or
               without a leading python3/bash. The value must appear whole and
               end at a delimiter. A value with no subcommand never passes,
               because a path alone cannot tell a call from a mention, so a
               bare "x.py" or "scripts/x.py" mention never passes.
  lead         the value is "<heading> | <label>". Every heading (outside
               fenced code) whose text begins with <heading> opens its
               section with a "**<label>:**" paragraph: the first non-blank
               line after the heading, ahead of any fenced block such as the
               step's AskQuestion prompt. At least one heading must match.

Each row records `was`, the eval.sh check function the pin came from
(check_command_structure for a rule that never had a pin), and the
message a finding shows. The pin map in the spec folder lists every
converted pin and the row that replaced it.

Output is PASS/FAIL TSV, the shape of the other eval-*.py emitters. One
self-test scenario per kind runs first, against synthetic text, so a matcher
that passes everything or nothing fails the check instead of passing it.
Then one line per row.

Exit codes: 0 all PASS, 1 any FAIL, 2 no commands/ directory under --root.
Dev-only: install.sh never ships eval-* scripts. Python 3.9, standard
library only.
"""

from __future__ import annotations

import argparse
import re
import sys
from pathlib import Path
from typing import Callable, Dict, Iterator, List, NamedTuple, Optional, Tuple

ROOT = Path(__file__).resolve().parent.parent

KINDS = ("heading", "frontmatter", "invocation", "lead")


class Row(NamedTuple):
    file: str
    kind: str
    value: str
    was: str
    message: str


REQUIRED_ARTIFACTS_COMMANDS = (
    "create-spec", "implement-story", "implement-spec", "implement-phase",
    "ship", "release", "status",
)

ROWS: Tuple[Row, ...] = (
    Row("commands/_preamble.md", "heading", "Narrow Recommended-Delivery Exception",
        "check_recommended_spec_implementation",
        "_preamble.md must keep the heading that defines the narrow recommended-planning exception."),
    Row("commands/create-spec.md", "heading", "Authoritative `--recommend` Invocation Matrix",
        "check_recommended_spec_implementation",
        "create-spec.md must keep the heading over its fail-before-mutation --recommend invocation matrix."),
    Row("commands/status.md", "invocation", "scripts/spec-status.py is-complete",
        "check_spec_status",
        "status.md must invoke the shared format-tolerant detector, not only name it."),
    Row("commands/create-spec.md", "invocation", "scripts/spec-status.py is-complete",
        "check_spec_status",
        "create-spec.md Step 1.3b must invoke the shared format-tolerant detector."),
    Row("commands/status.md", "invocation", "scripts/archive-sweep.py sweep",
        "check_archive_sweep",
        "status.md --archive must invoke the shared archive-sweep reducer."),
    Row("commands/create-spec.md", "invocation", "scripts/supersession-writeback.py apply",
        "check_supersession_writeback",
        "create-spec.md Step 2.4b must invoke the supersession-writeback helper."),
    Row("commands/edit-spec.md", "invocation", "scripts/supersession-writeback.py apply",
        "check_supersession_writeback",
        "edit-spec.md must invoke the same supersession-writeback helper as create-spec.md."),
    Row("commands/release.md", "invocation",
        'scripts/resolve-spec-reference.py resolve --branch "${LAST_MERGED_BRANCH}"',
        "check_post_merge_archival",
        "release.md Step 1.3c's archival hook must resolve via the shared "
        "resolve-spec-reference.py CLI, not a second drifting heuristic."),
    Row("commands/release.md", "invocation",
        "scripts/archive-sweep.py archive-one --specs-dir .writ/specs "
        "--knowledge-dir .writ/knowledge --repo-root . --spec-name",
        "check_post_merge_archival",
        "release.md Step 1.3c's archival hook must call archive-sweep.py archive-one "
        "directly with the documented flags."),
    Row("commands/release.md", "invocation",
        "scripts/roadmap-sync.py check --roadmap .writ/product/roadmap.md --spec-name",
        "check_roadmap_sync",
        "release.md Step 3.1b must check via the shared roadmap-sync.py CLI, "
        "not a second drifting heuristic."),
    Row("commands/release.md", "invocation",
        "scripts/roadmap-sync.py append-row --roadmap .writ/product/roadmap.md",
        "check_roadmap_sync",
        "release.md Step 3.1b must append via the shared roadmap-sync.py CLI."),
    Row("commands/implement-spec.md", "invocation", "scripts/story-deps.py validate --spec-dir",
        "check_story_deps",
        "implement-spec.md must invoke the executable story-graph validator."),
    Row("commands/implement-story.md", "invocation", "scripts/story-context.py assemble",
        "check_story_context",
        "implement-story.md must invoke the executable context-hint assembler "
        "instead of parsing hints by prose."),
    Row("commands/implement-phase.md", "invocation", "scripts/phase-state.py create-lane",
        "check_phase_lanes",
        "implement-phase.md must create each spec's lane through the phase-state reducer."),
    Row("commands/implement-phase.md", "invocation", "scripts/phase-state.py validate-result",
        "check_phase_lanes",
        "implement-phase.md must gate each merge on the phase-state reducer's result validation."),
    Row("commands/_preamble.md", "heading", "User Challenge",
        "check_phase_challenges",
        "_preamble.md must keep the User Challenge section heading."),
    Row("commands/knowledge.md", "heading", "Phase-Close Writeback",
        "check_phase_knowledge",
        "knowledge.md must keep the Phase-Close Writeback section heading."),
    Row("commands/refresh-command.md", "invocation", "scripts/eval.sh --check=refresh-evidence",
        "check_refresh_evidence",
        "refresh-command.md Phase 4 must run the pre-merge eval gate."),
    Row("commands/_preamble.md", "heading", "Artifact Integrity",
        "check_artifact_integrity",
        "_preamble.md must keep the Artifact Integrity section heading."),
) + tuple(
    Row(f"commands/{name}.md", "heading", "Required Artifacts",
        "check_artifact_integrity",
        f"commands/{name}.md must declare its Required Artifacts block under its own heading.")
    for name in REQUIRED_ARTIFACTS_COMMANDS
) + (
    Row("commands/refactor.md", "heading", "Step 1.1b: Dirty-Tree Guard",
        "check_revert",
        "refactor.md must carry the dirty-tree guard as its own numbered step ahead of Step 1.2."),
    Row("commands/verify-spec.md", "invocation", "scripts/ac-trace.py check --spec",
        "check_ac_trace",
        "verify-spec.md must invoke ac-trace.py for Check 3e/3f."),
    Row("commands/initialize.md", "invocation", "scripts/quality-config-audit.py check --project .",
        "check_quality_config_audit",
        "initialize.md must run the quality-config audit during brownfield Gap Analysis."),
    Row("commands/status.md", "invocation", "scripts/quality-config-audit.py check --project .",
        "check_quality_config_audit",
        "status.md must surface the quality-config findings by running the pure file-read audit."),
    Row("commands/create-spec.md", "lead",
        "Step 1.3: Discovery Conversation | One question per prompt",
        "check_command_structure",
        "create-spec.md Step 1.3 must open with its one-question-per-prompt rule: never "
        "several questions in one prompt or AskQuestion call."),
    Row("commands/create-spec.md", "lead",
        "Step 1: Shortened Discovery Conversation | One question per prompt",
        "check_command_structure",
        "create-spec.md --from-prototype and --from-issue Step 1 must each open with the "
        "one-question-per-prompt rule."),
    Row("commands/create-spec.md", "lead", "Step 1.4b: Contract Decision | Precondition",
        "check_command_structure",
        "create-spec.md Step 1.4b must open with its precondition: the full contract is "
        "printed as a visible message before the Contract Decision prompt."),
    Row("commands/create-spec.md", "lead", "Step 3: Phase 2 with Story 1 | Precondition",
        "check_command_structure",
        "create-spec.md --from-prototype Step 3 must open with its precondition: the "
        "Step 2 contract is locked at Step 1.4b."),
    Row("commands/create-spec.md", "lead", "Step 3: Phase 2 with `spec_ref` | Precondition",
        "check_command_structure",
        "create-spec.md --from-issue Step 3 must open with its precondition: the "
        "Step 2 contract is locked at Step 1.4b."),
)

FENCE = re.compile(r"^\s*(`{3,}|~{3,})")
HEADING = re.compile(r"^#{1,6} (.*)$")
# A character before the value that would make it part of a longer path.
PATH_CHAR = re.compile(r"[\w./-]")
# What may follow the value: a delimiter, never more of a word or path.
VALUE_END = set(" \t`'\")];,|\\")


def marked_lines(text: str) -> Iterator[Tuple[str, bool]]:
    """Yield (line, fenced) for every line; fence markers count as fenced."""
    fence = ""
    for line in text.splitlines():
        match = FENCE.match(line)
        if not fence:
            if match:
                fence = match.group(1)
                yield line, True
                continue
            yield line, False
            continue
        yield line, True
        stripped = line.strip()
        if stripped and set(stripped) == {fence[0]} and len(stripped) >= len(fence):
            fence = ""


def unfenced_lines(text: str) -> Iterator[str]:
    """Yield the lines outside fenced code blocks."""
    return (line for line, fenced in marked_lines(text) if not fenced)


def has_heading(text: str, value: str) -> bool:
    for line in unfenced_lines(text):
        match = HEADING.match(line)
        if match and match.group(1).startswith(value):
            return True
    return False


def has_frontmatter_key(text: str, value: str) -> bool:
    lines = text.splitlines()
    if not lines or lines[0].strip() != "---":
        return False
    key = re.compile(r"^%s\s*:" % re.escape(value))
    found = False
    for line in lines[1:]:
        if line.strip() == "---":
            return found
        found = found or bool(key.match(line))
    return False  # no closing --- : not a frontmatter block


def has_invocation(text: str, value: str) -> bool:
    if not re.search(r"\S\s+\S", value):
        return False  # no subcommand: a path alone cannot tell a call from a mention
    for line in text.splitlines():
        start = line.find(value)
        while start >= 0:
            before = line[start - 1] if start else ""
            rest = line[start + len(value):]
            if not (before and PATH_CHAR.match(before)) and (not rest or rest[0] in VALUE_END):
                return True
            start = line.find(value, start + 1)
    return False


def has_lead(text: str, value: str) -> bool:
    heading, _, label = value.rpartition(" | ")
    if not heading.strip() or not label.strip():
        return False  # a value without both parts names no rule
    lead = f"**{label}:**"
    found = waiting = False
    for line, fenced in marked_lines(text):
        if waiting and line.strip():
            if fenced or not line.startswith(lead):
                return False
            waiting = False
            continue
        match = None if fenced else HEADING.match(line)
        if match and match.group(1).startswith(heading):
            found = waiting = True
    return found and not waiting


MATCHERS: Dict[str, Callable[[str, str], bool]] = {
    "heading": has_heading,
    "frontmatter": has_frontmatter_key,
    "invocation": has_invocation,
    "lead": has_lead,
}

DESCRIBE = {
    "heading": "no heading outside fenced code starts with '{value}'",
    "frontmatter": "the frontmatter has no top-level '{value}:' key",
    "invocation": "no line calls '{value}'",
    "lead": "no heading matches '{value}', or one whose section does not open "
            "with the bold-labelled paragraph it names",
}

# Per kind: (value, texts that must pass, texts that must fail).
SELF_TESTS = {
    "heading": [
        ("User Challenge",
         ["## User Challenge (Scope-Degradation Escalation)\n", "#### User Challenge\n"],
         ["User Challenge (Scope-Degradation Escalation)\n",
          "```\n## User Challenge\n```\n", "## The User Challenge\n"]),
    ],
    "frontmatter": [
        ("loop",
         ["---\nname: x\nloop:\n  unit: spec\n---\n# Body\n"],
         ["---\nname: x\nloops: 1\n---\n", "---\nname: x\n---\nloop: 1\n",
          "---\nname: x\n  loop: 1\n---\n"]),
    ],
    "invocation": [
        ("scripts/x.py check",
         ["python3 scripts/x.py check --spec a\n", "`scripts/x.py check --spec <folder>`\n"],
         ["x.py\n", "`scripts/x.py`\n", "python3 scripts/x.py checker\n",
          "See scripts/x.py for details\n", "scripts/x.py cmd_classify\n"]),
        # A value with no subcommand never passes, even on a real call.
        ("scripts/x.py",
         [],
         ["python3 scripts/x.py init\n", "See scripts/x.py for details\n"]),
    ],
    "lead": [
        ("Step 1.4b | Precondition",
         ["#### Step 1.4b: Decision\n\n**Precondition:** shown.\n\n```\nAsk()\n```\n",
          "## Step 1.4b\n**Precondition:** shown.\n## Step 1.4b again\n\n**Precondition:** x\n"],
         ["#### Step 1.4b: Decision\n\n```\nAsk()\n```\n\n**Precondition:** shown.\n",
          "#### Step 1.4b: Decision\n\nPrecondition: shown.\n",
          "#### Step 1.4b: Decision\n\n**Note:** shown.\n",
          "#### Step 1.4b: Decision\n\nAsk.\n\n**Precondition:** shown.\n",
          "Step 1.4b\n\n**Precondition:** shown.\n",
          "```\n## Step 1.4b\n```\n**Precondition:** shown.\n",
          "## Step 1.4b\n\n**Precondition:** a\n## Step 1.4b again\n\nAsk.\n",
          "## Step 1.4b\n"]),
        # A value without both parts never passes.
        ("Step 1.4b",
         [],
         ["#### Step 1.4b: Decision\n\n**Precondition:** shown.\n"]),
    ],
}


def self_test() -> List[Tuple[str, bool, str]]:
    """Run each kind's matcher on its synthetic texts; return (name, ok, detail)."""
    results = []
    for kind in KINDS:
        problems = []
        for value, positives, negatives in SELF_TESTS[kind]:
            for text in positives:
                if not MATCHERS[kind](text, value):
                    problems.append(f"missed: {text!r}")
            for text in negatives:
                if MATCHERS[kind](text, value):
                    problems.append(f"passed: {text!r}")
        results.append((f"command-structure-kind-{kind}", not problems, "; ".join(problems)))
    return results


def check_row(root: Path, row: Row) -> Tuple[bool, str]:
    path = root / row.file
    if not path.is_file():
        return False, "file is missing"
    text = path.read_text(encoding="utf-8", errors="replace")
    if MATCHERS[row.kind](text, row.value):
        return True, ""
    return False, DESCRIBE[row.kind].format(value=row.value)


def clean(value: object) -> str:
    return str(value).replace("\n", "\\n").replace("\t", " ")


def main(argv: Optional[List[str]] = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("--root", default=str(ROOT), help="repo root to check (default: this repo)")
    args = parser.parse_args(argv)
    root = Path(args.root).resolve()

    failed = False
    for name, ok, detail in self_test():
        print(f"PASS\t{name}" if ok else f"FAIL\t{name}\t{clean(detail)}")
        failed = failed or not ok

    if not (root / "commands").is_dir():
        print(f"eval-command-structure: no commands/ directory under {root}", file=sys.stderr)
        return 2

    for row in ROWS:
        name = clean(f"command-structure:{row.file}:{row.kind}:{row.value}")
        ok, detail = check_row(root, row)
        if ok:
            print(f"PASS\t{name}")
        else:
            print(f"FAIL\t{name}\t{clean(row.message)} ({clean(detail)}; was {row.was})")
            failed = True
    return 1 if failed else 0


if __name__ == "__main__":
    sys.exit(main())
