#!/usr/bin/env python3
"""Generate claude-code/agents/writ-*.md from agents/*.md plus a Claude overlay.

    python3 scripts/gen-claude-agents.py           # write every agent file
    python3 scripts/gen-claude-agents.py --check   # report drift, write nothing

This generator is the only writer of claude-code/agents/*.md: regenerate,
never hand-edit. Each file is the OVERLAY frontmatter for its stem, a
generated-header HTML comment, the canonical agents/<stem>.md body (YAML
frontmatter and retired `model: "fast"` lines removed, otherwise verbatim),
then the optional OVERLAY suffix, with exactly one trailing newline. Every
agents/*.md stem needs an OVERLAY entry. Write mode validates every stem
before the first write, so an unmapped stem never leaves a half-written set
behind.

Both modes print the check shape (agent CLI contract). Write mode prints
`pass`, one `wrote <path>` line per file, then `gen-claude-agents: pass
(<n> written, 0 unmapped)`; with an unmapped stem it writes nothing and prints
`fail`, one `reason: unmapped <stem>` line each, and `gen-claude-agents: fail
(0 written, <u> unmapped)`, exit 1.

--check prints `pass` or `fail`, one `reason: stale|missing|unmapped <stem>`
or `reason: orphan writ-<x>` line per problem in stem order, then the summary
`gen-claude-agents: <verdict> (<n> stale, <m> missing, <o> orphan,
<u> unmapped)`. An orphan is a `writ-*.md` in the out-dir that no current
canonical stem generates. Exit 0 pass, 1 fail, 2 usage. `--agents-dir` and
`--out-dir` override the source and output directories.
"""

from __future__ import annotations

import argparse
import pathlib
import re
import sys

ROOT = pathlib.Path(__file__).resolve().parents[1]
AGENTS_DIR = ROOT / "agents"
OUT_DIR = ROOT / "claude-code" / "agents"

# Claude-only metadata per canonical stem: the output filename, frontmatter as
# ordered (key, value) pairs emitted unquoted, and an optional suffix appended
# after the body. Values for the seven pre-generator files are copied verbatim
# from them; a changed value changes Claude agent behavior.
OVERLAY: dict[str, dict] = {
    "architecture-check-agent": {
        "file": "writ-architect.md",
        "frontmatter": [
            ("name", "writ-architect"),
            ("description", (
                "Pre-implementation design review for Writ stories. Use before coding"
                " to validate approach, check integration risk, and catch design"
                " issues early."
            )),
            ("tools", "Read, Grep, Glob, Bash"),
            ("disallowedTools", "Write, Edit"),
            ("model", "haiku"),
            ("permissionMode", "plan"),
            ("isolation", "worktree"),
            ("maxTurns", "15"),
            ("memory", "project"),
        ],
        "suffix": "Update your agent memory with architectural patterns and decisions you discover.",
    },
    "coding-agent": {
        "file": "writ-coder.md",
        "frontmatter": [
            ("name", "writ-coder"),
            ("description", (
                "TDD implementation agent for Writ stories. Writes tests first, then"
                " implements code to make them pass. Use for story implementation."
            )),
            ("tools", "Read, Write, Edit, Bash, Grep, Glob"),
            ("model", "inherit"),
            ("permissionMode", "acceptEdits"),
            ("isolation", "worktree"),
            ("maxTurns", "50"),
            ("memory", "project"),
        ],
        "suffix": (
            "Update your agent memory with patterns and conventions you discover in"
            " this codebase."
        ),
    },
    "documentation-agent": {
        "file": "writ-documenter.md",
        "frontmatter": [
            ("name", "writ-documenter"),
            ("description", (
                "Framework-adaptive documentation agent for Writ. Detects the"
                " project's doc framework (VitePress, Docusaurus, README, etc.) and"
                " creates/updates documentation accordingly."
            )),
            ("tools", "Read, Write, Edit, Bash, Grep, Glob"),
            ("model", "inherit"),
            ("permissionMode", "acceptEdits"),
            ("maxTurns", "25"),
        ],
        "suffix": "",
    },
    "evaluator-agent": {
        "file": "writ-evaluator.md",
        "frontmatter": [
            ("name", "writ-evaluator"),
            ("description", (
                "Fresh-context rubric gate for Writ. Adjudicates acceptance criteria"
                " and recorded test results; names residual architecture, security,"
                " and taste. Returns EVALUATION_RESULT. Never applies a patch."
            )),
            ("tools", "Read, Grep, Glob, Bash"),
            ("disallowedTools", "Write, Edit"),
            ("model", "inherit"),
            ("permissionMode", "plan"),
            ("maxTurns", "20"),
            ("memory", "project"),
        ],
        "suffix": (
            "Consult your agent memory for patterns seen in previous evaluations.\n"
            "Update memory with new patterns discovered during this evaluation."
        ),
    },
    "review-agent": {
        "file": "writ-reviewer.md",
        "frontmatter": [
            ("name", "writ-reviewer"),
            ("description", (
                "Code quality and security review gate for Writ. Reviews"
                " implementations against acceptance criteria, code quality"
                " standards, and security best practices. Returns PASS or FAIL, or"
                " PAUSE on Large drift."
            )),
            ("tools", "Read, Grep, Glob, Bash"),
            ("disallowedTools", "Write, Edit"),
            ("model", "inherit"),
            ("permissionMode", "plan"),
            ("maxTurns", "20"),
            ("memory", "project"),
        ],
        "suffix": (
            "Consult your agent memory for patterns and issues seen in previous reviews.\n"
            "Update memory with new patterns discovered during this review."
        ),
    },
    "testing-agent": {
        "file": "writ-tester.md",
        "frontmatter": [
            ("name", "writ-tester"),
            ("description", (
                "Test execution and coverage enforcement for Writ. Runs tests, fixes"
                " failures, ensures 80% coverage on new code. Returns PASS or FAIL."
            )),
            ("tools", "Read, Write, Edit, Bash, Grep, Glob"),
            ("model", "inherit"),
            ("permissionMode", "acceptEdits"),
            ("maxTurns", "30"),
        ],
        "suffix": "",
    },
    "user-story-generator": {
        "file": "writ-story-gen.md",
        "frontmatter": [
            ("name", "writ-story-gen"),
            ("description", (
                "Parallel story file generator for Writ create-spec. Creates"
                " individual user story markdown files. Designed to run multiple"
                " instances simultaneously in worktrees."
            )),
            ("tools", "Read, Write, Bash"),
            ("model", "haiku"),
            ("permissionMode", "acceptEdits"),
            ("isolation", "worktree"),
            ("maxTurns", "10"),
        ],
        "suffix": "",
    },
    "visual-qa-agent": {
        "file": "writ-visual-qa.md",
        "frontmatter": [
            ("name", "writ-visual-qa"),
            # Mirrors .writ/manifest.yaml agents[].purpose
            ("description", (
                "Optional UI validation gate that compares implementation screenshots"
                " against visual references."
            )),
            ("tools", "Read, Grep, Glob, Bash"),
            ("disallowedTools", "Write, Edit"),
            ("model", "inherit"),
            ("permissionMode", "plan"),
            ("maxTurns", "20"),
        ],
        "suffix": "",
    },
}

GENERATED_HEADER = (
    "<!-- Generated from agents/{stem}.md by scripts/gen-claude-agents.py"
    " — do not hand-edit. Regenerate: python3 scripts/gen-claude-agents.py -->"
)

# Historical template argument retired by ADR-024; stripped defensively so a
# stale body can never re-embed it (bare or comma-terminated Task({...}) form).
RETIRED_FAST_LINE = re.compile(r'^\s*model:\s*"fast",?\s*$')


def strip_optional_yaml_frontmatter(text: str) -> str:
    if not text.startswith("---\n"):
        return text
    end = text.find("\n---\n", 4)
    if end == -1:
        return text
    return text[end + 5 :].lstrip("\n")


def strip_retired_fast_lines(body: str) -> str:
    return "\n".join(
        line for line in body.split("\n") if not RETIRED_FAST_LINE.match(line)
    )


def render_frontmatter(stem: str) -> str:
    lines = ["---"]
    lines.extend(f"{key}: {value}" for key, value in OVERLAY[stem]["frontmatter"])
    lines.append("---")
    return "\n".join(lines) + "\n"


def emit_agent(stem: str, body: str) -> str:
    """Frontmatter, header comment, body, suffix: blank-line separated, one trailing newline."""
    parts = [
        render_frontmatter(stem).rstrip("\n"),
        GENERATED_HEADER.format(stem=stem),
    ]
    body = strip_retired_fast_lines(body).strip("\n")
    if body:
        parts.append(body)
    suffix = OVERLAY[stem].get("suffix", "")
    if suffix:
        parts.append(suffix)
    return "\n\n".join(parts) + "\n"


def source_stems(agents_dir: pathlib.Path) -> list[str]:
    return sorted(md.stem for md in agents_dir.glob("*.md"))


def unmapped_stems(stems: list[str]) -> list[str]:
    return [stem for stem in stems if stem not in OVERLAY]


def render(agents_dir: pathlib.Path, stem: str) -> str:
    raw = (agents_dir / f"{stem}.md").read_text(encoding="utf-8")
    return emit_agent(stem, strip_optional_yaml_frontmatter(raw))


def display(path: pathlib.Path) -> str:
    try:
        return str(path.relative_to(ROOT))
    except ValueError:
        return str(path)


def write(agents_dir: pathlib.Path, out_dir: pathlib.Path) -> int:
    stems = source_stems(agents_dir)
    unmapped = unmapped_stems(stems)
    if unmapped:
        print("fail")
        for stem in unmapped:
            print(f"reason: unmapped {stem}")
        print(f"gen-claude-agents: fail (0 written, {len(unmapped)} unmapped)")
        return 1
    expected = {stem: render(agents_dir, stem) for stem in stems}
    out_dir.mkdir(parents=True, exist_ok=True)
    print("pass")
    for stem, text in expected.items():
        out = out_dir / OVERLAY[stem]["file"]
        out.write_text(text, encoding="utf-8")
        print("wrote", display(out))
    print(f"gen-claude-agents: pass ({len(expected)} written, 0 unmapped)")
    return 0


def check(agents_dir: pathlib.Path, out_dir: pathlib.Path) -> int:
    stems = source_stems(agents_dir)
    unmapped = set(unmapped_stems(stems))
    files = {p.name: p for p in out_dir.glob("writ-*.md")} if out_dir.is_dir() else {}
    generated = {OVERLAY[stem]["file"] for stem in stems if stem not in unmapped}

    reasons: list[tuple[str, str]] = []
    for stem in stems:
        if stem in unmapped:
            reasons.append(("unmapped", stem))
            continue
        path = files.get(OVERLAY[stem]["file"])
        if path is None:
            reasons.append(("missing", stem))
        elif path.read_text(encoding="utf-8") != render(agents_dir, stem):
            reasons.append(("stale", stem))
    for name in files:
        if name not in generated:
            reasons.append(("orphan", name[: -len(".md")]))
    reasons.sort(key=lambda reason: reason[1])

    verdict = "fail" if reasons else "pass"
    print(verdict)
    for kind, stem in reasons:
        print(f"reason: {kind} {stem}")
    counts = {kind: sum(1 for k, _ in reasons if k == kind)
              for kind in ("stale", "missing", "orphan", "unmapped")}
    print(
        f"gen-claude-agents: {verdict} ({counts['stale']} stale, "
        f"{counts['missing']} missing, {counts['orphan']} orphan, "
        f"{counts['unmapped']} unmapped)"
    )
    return 1 if reasons else 0


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        prog="gen-claude-agents.py",
        description="Generate or check claude-code/agents/writ-*.md from agents/*.md.",
        allow_abbrev=False,
    )
    parser.add_argument("--check", action="store_true",
                        help="report drift without writing; exit 0 pass, 1 fail")
    parser.add_argument("--agents-dir", type=pathlib.Path, default=AGENTS_DIR)
    parser.add_argument("--out-dir", type=pathlib.Path, default=OUT_DIR)
    args = parser.parse_args(argv)
    if args.check:
        return check(args.agents_dir, args.out_dir)
    return write(args.agents_dir, args.out_dir)


if __name__ == "__main__":
    try:
        sys.exit(main())
    except BrokenPipeError:
        sys.exit(0)
