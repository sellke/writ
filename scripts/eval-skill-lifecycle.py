#!/usr/bin/env python3
"""Scenarios for the skill lifecycle lint (skill-lifecycle Story 2).

Emits PASS/FAIL TSV lines consumed by scripts/eval.sh check_skill_lifecycle.
Drives eight disposable SKILL.md fixtures through scripts/lint-skill.sh and
asserts each expected exit code and lifecycle finding, proving the earned-state
contract from ADR-014 / technical-spec D3–D5:

  1. valid-candidate    status: candidate, no evidence           -> exit 0
  2. valid-proven       status: proven, 3 well-formed entries     -> exit 0
  3. valid-promoted     status: promoted, proven bar + promotion  -> exit 0
  4. unearned-proven    status: proven, 2 entries                 -> exit 1, L3
  5. unearned-promoted  status: promoted, 3 usage, no promotion   -> exit 1, L4
  6. invalid-status     status: shipped                           -> exit 1, L2
  7. malformed-evidence status: proven, 3 entries, one missing ref-> exit 1, L5
  8. missing-status     frontmatter without status:               -> exit 1, L1

Fixtures live only in a TemporaryDirectory — they are never written under
skills/ so `lint-skill.sh skills/*/SKILL.md` and the catalog never discover
them (excluded from product discovery by construction).

Failing-first: before scripts/lint-skill.sh gains lifecycle checks, the invalid
fixtures lint clean (exit 0), so scenarios 4–8 fail. They go green only once the
lint proves earned state.
"""

from __future__ import annotations

import subprocess
import sys
import tempfile
from pathlib import Path

LINT = Path(__file__).with_name("lint-skill.sh")
passed = 0
failed = 0


def emit(name: str, ok: bool, detail: object = "") -> None:
    global passed, failed
    if ok:
        passed += 1
        print(f"PASS\t{name}")
    else:
        failed += 1
        safe = str(detail).replace("\n", "\\n").replace("\t", " ")
        print(f"FAIL\t{name}\t{safe}")


# A clean, verb-phrase description and a lint-safe body so the ONLY thing that
# can ever trip lint-skill.sh in these fixtures is the lifecycle contract.
BODY = (
    "\n# Fixture Skill\n\n"
    "## Purpose\n\n"
    "Validate the skill lifecycle lint against a controlled frontmatter shape.\n\n"
    "## When to Use\n\n"
    "- Only inside the skill-lifecycle eval fixtures\n\n"
    "## How to Apply\n\n"
    "Exercise the earned-state rules with a known-good body.\n"
)

DESC = 'description: "Validate skill lifecycle fixtures against the earned-state contract."'

# Each fixture: (frontmatter_lines_after_description, expected_exit, expected_substr)
FIXTURES = {
    "valid-candidate": (
        ["status: candidate"],
        0,
        None,
    ),
    "valid-proven": (
        [
            "status: proven",
            "evidence:",
            "  - date: 2026-05-06",
            "    type: usage",
            "    ref: commands/ship.md",
            '    note: "Used in ship."',
            "  - date: 2026-05-12",
            "    type: usage",
            "    ref: commands/release.md",
            '    note: "Used in release."',
            "  - date: 2026-06-01",
            "    type: eval",
            "    ref: scripts/eval.sh",
            '    note: "Exercised by an eval check."',
        ],
        0,
        None,
    ),
    "valid-promoted": (
        [
            "status: promoted",
            "evidence:",
            "  - date: 2026-05-06",
            "    type: usage",
            "    ref: commands/ship.md",
            '    note: "Used in ship."',
            "  - date: 2026-05-12",
            "    type: usage",
            "    ref: commands/release.md",
            '    note: "Used in release."',
            "  - date: 2026-06-01",
            "    type: promotion",
            "    ref: agents/coding-agent.md",
            '    note: "Declared in required_skills."',
        ],
        0,
        None,
    ),
    "unearned-proven": (
        [
            "status: proven",
            "evidence:",
            "  - date: 2026-05-06",
            "    type: usage",
            "    ref: commands/ship.md",
            '    note: "Used in ship."',
            "  - date: 2026-05-12",
            "    type: usage",
            "    ref: commands/release.md",
            '    note: "Used in release."',
        ],
        1,
        "Lifecycle-unearned",
    ),
    "unearned-promoted": (
        [
            "status: promoted",
            "evidence:",
            "  - date: 2026-05-06",
            "    type: usage",
            "    ref: commands/ship.md",
            '    note: "Used in ship."',
            "  - date: 2026-05-12",
            "    type: usage",
            "    ref: commands/release.md",
            '    note: "Used in release."',
            "  - date: 2026-06-01",
            "    type: usage",
            "    ref: agents/coding-agent.md",
            '    note: "Used by coding-agent."',
        ],
        1,
        "Lifecycle-unearned",
    ),
    "invalid-status": (
        ["status: shipped"],
        1,
        "Lifecycle-invalid",
    ),
    "malformed-evidence": (
        [
            "status: proven",
            "evidence:",
            "  - date: 2026-05-06",
            "    type: usage",
            "    ref: commands/ship.md",
            '    note: "Used in ship."',
            "  - date: 2026-05-12",
            "    type: usage",
            '    note: "Missing ref field."',
            "  - date: 2026-06-01",
            "    type: usage",
            "    ref: agents/coding-agent.md",
            '    note: "Used by coding-agent."',
        ],
        1,
        "Lifecycle-evidence",
    ),
    "missing-status": (
        [],
        1,
        "Lifecycle-missing",
    ),
}


def write_fixture(tmp: Path, name: str, extra_fm: list[str]) -> Path:
    lines = ["---", "name: fixture-skill", DESC, "disable-model-invocation: true"]
    lines.extend(extra_fm)
    lines.append("---")
    content = "\n".join(lines) + "\n" + BODY
    path = tmp / f"{name}.md"
    path.write_text(content, encoding="utf-8")
    return path


def run_lint(path: Path) -> tuple[int, str]:
    proc = subprocess.run(
        ["bash", str(LINT), str(path)],
        capture_output=True,
        text=True,
    )
    return proc.returncode, proc.stdout + proc.stderr


def main() -> int:
    with tempfile.TemporaryDirectory() as t:
        tmp = Path(t)
        for name, (extra_fm, want_exit, want_substr) in FIXTURES.items():
            path = write_fixture(tmp, name, extra_fm)
            code, output = run_lint(path)
            exit_ok = code == want_exit
            substr_ok = want_substr is None or want_substr in output
            emit(
                name,
                exit_ok and substr_ok,
                f"exit={code} want={want_exit} substr={want_substr!r} output={output.strip()}",
            )

    return 0 if failed == 0 else 1


if __name__ == "__main__":
    sys.exit(main())
