#!/usr/bin/env python3
"""Static asserter for the artifact-integrity handshake (spec: 2026-07-18-artifact-integrity-handshake).

Emits PASS/FAIL TSV lines consumed by scripts/eval.sh check_artifact_integrity.
Like the git-notes-audit channel, the deliverables are product-source markdown
(no runtime helper), so the scenarios assert the durable contract directly
against the shipped files:

  - _preamble.md carries an `## Artifact Integrity` section with the
    required/optional distinction, HALT behavior, and bounded-repair wording
  - each of the 7 high-traffic commands declares a `## Required Artifacts` block
  - the canonical context.md schema (implement-story Step 2) carries the
    `## Artifact Map` + Integrity line, and implement-spec/status emit it too
  - the rejected `.writ/index.md` pointer file is NOT reintroduced
"""

from __future__ import annotations

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
passed = 0
failed = 0

COMMANDS_WITH_DECLARATIONS = [
    "create-spec",
    "implement-story",
    "implement-spec",
    "implement-phase",
    "ship",
    "release",
    "status",
]


def emit(name: str, ok: bool, detail: object = "") -> None:
    global passed, failed
    if ok:
        passed += 1
        print(f"PASS\t{name}")
    else:
        failed += 1
        safe = str(detail).replace("\n", "\\n").replace("\t", " ")
        print(f"FAIL\t{name}\t{safe}")


def read(rel: str) -> str:
    path = ROOT / rel
    try:
        return path.read_text(encoding="utf-8")
    except OSError:
        return ""


def has_all(text: str, *needles: str) -> bool:
    return all(n in text for n in needles)


def has_any(text: str, *needles: str) -> bool:
    return any(n in text for n in needles)


def scenario_preamble() -> None:
    pre = read("commands/_preamble.md")
    emit("preamble-has-section", "## Artifact Integrity" in pre,
         "_preamble.md must define the `## Artifact Integrity` section")
    emit("preamble-required-optional",
         has_all(pre, "Required Artifacts") and has_all(pre, "*required*", "*optional*"),
         "_preamble.md must document the required/optional distinction")
    emit("preamble-halt",
         has_any(pre, "HALT"),
         "_preamble.md must HALT on a missing required artifact")
    emit("preamble-bounded-repair",
         has_all(pre, "bounded repair") and has_any(pre, "AskQuestion") and "auto-run" in pre,
         "_preamble.md must offer a bounded repair naming the creating command, no auto-mutation")
    emit("preamble-degrade",
         has_any(pre, "degraded mode", "warn and continue"),
         "_preamble.md must warn+degrade on a missing optional artifact")
    emit("preamble-adapter-neutral",
         has_all(pre, "adapter-neutral", "existence checks"),
         "_preamble.md must state the check is adapter-neutral (pure existence checks)")


def scenario_command_declarations() -> None:
    for cmd in COMMANDS_WITH_DECLARATIONS:
        text = read(f"commands/{cmd}.md")
        emit(f"{cmd}-required-artifacts-block", "## Required Artifacts" in text,
             f"commands/{cmd}.md must declare a `## Required Artifacts` block")


def scenario_artifact_map() -> None:
    story = read("commands/implement-story.md")
    emit("context-schema-artifact-map", "## Artifact Map" in story,
         "implement-story.md Step 2 schema must include the `## Artifact Map` section")
    emit("context-schema-integrity-line",
         has_all(story, "**Integrity:**") and has_any(story, "missing required"),
         "the canonical schema must include the Integrity line")
    emit("context-schema-wholesale",
         has_any(story, "rewritten wholesale", "never appended"),
         "the Artifact Map must be rewritten wholesale (never appended/patched)")

    spec = read("commands/implement-spec.md")
    emit("implement-spec-emits-map", "Artifact Map" in spec,
         "implement-spec.md regeneration must reference the Artifact Map")

    status = read("commands/status.md")
    emit("status-emits-map", "Artifact Map" in status,
         "status.md regeneration must reference the Artifact Map")


def scenario_no_index_file() -> None:
    index = ROOT / ".writ" / "index.md"
    emit("no-writ-index-file", not index.exists(),
         "the rejected .writ/index.md pointer file must not be reintroduced")


def main() -> int:
    scenario_preamble()
    scenario_command_declarations()
    scenario_artifact_map()
    scenario_no_index_file()
    return 0 if failed == 0 else 1


if __name__ == "__main__":
    sys.exit(main())
