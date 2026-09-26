#!/usr/bin/env python3
"""Generate codex/agents/*.toml from agents/*.md (developer_instructions = body).

    python3 scripts/gen-codex-agent-tomls.py           # write every TOML
    python3 scripts/gen-codex-agent-tomls.py --check   # report drift, write nothing

This generator is the only writer of codex/agents/*.toml: regenerate, never
hand-edit. Every agents/*.md stem needs PURPOSES and SANDBOX entries, and each
purpose must equal its .writ/manifest.yaml agents[].purpose. Write mode
validates every stem before the first write, so an unmapped stem never leaves a
half-written set behind.

--check prints `pass` or `fail`, one `reason: stale|missing|orphan|unmapped
<stem>` line per problem in stem order, then the summary
`gen-codex-agent-tomls: <verdict> (<n> stale, <m> missing, <o> orphan,
<u> unmapped)`. Exit 0 pass, 1 fail, 2 usage. `--agents-dir` and `--out-dir`
override the source and output directories.
"""

from __future__ import annotations

import argparse
import pathlib
import re
import sys

ROOT = pathlib.Path(__file__).resolve().parents[1]
AGENTS_DIR = ROOT / "agents"
OUT_DIR = ROOT / "codex" / "agents"

# Mirrors .writ/manifest.yaml agents[].purpose
PURPOSES: dict[str, str] = {
    "architecture-check-agent": (
        "Pre-implementation design review that catches architecture risks before coding."
    ),
    "coding-agent": (
        "TDD implementation agent that writes code, follows conventions, and self-verifies."
    ),
    "documentation-agent": (
        "Framework-adaptive documentation agent for feature, component, and architecture docs."
    ),
    "evaluator-agent": (
        "Fresh-context rubric agent that adjudicates acceptance criteria and recorded"
        " test results; residual architecture, security, and taste; never applies a patch."
    ),
    "review-agent": (
        "Quality gate agent that verifies acceptance criteria, code quality, tests, and drift."
    ),
    "testing-agent": (
        "Test and coverage agent that verifies pass rate, regressions, and coverage thresholds."
    ),
    "user-story-generator": "Parallel story authoring agent for create-spec workflows.",
    "visual-qa-agent": (
        "Optional UI validation gate that compares implementation screenshots against visual references."
    ),
}

SANDBOX: dict[str, str] = {
    "architecture-check-agent": "read-only",
    "coding-agent": "workspace-write",
    "documentation-agent": "workspace-write",
    "evaluator-agent": "read-only",
    "review-agent": "read-only",
    "testing-agent": "workspace-write",
    "user-story-generator": "workspace-write",
    "visual-qa-agent": "read-only",
}

# ADR-024: Codex is single-vendor, so the floor is effort-only — the parent's
# model is always used (`model` omitted), and floor stems run it at low effort.
# Mirrors the `model_tier: floor` declarations in agents/*.md.
FLOOR_STEMS = frozenset({"architecture-check-agent", "user-story-generator"})

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


def toml_long_string(body: str) -> str:
    """TOML multi-line basic string (triple quotes)."""
    escaped = body.replace("\\", "\\\\").replace('"""', '\\"""')
    return '"""\n' + escaped + '\n"""'


def strip_retired_fast_lines(body: str) -> str:
    return "\n".join(
        line for line in body.split("\n") if not RETIRED_FAST_LINE.match(line)
    )


def floor_effort_line(stem: str) -> str:
    """Effort-only floor: never a `model =` line, for any stem."""
    if stem in FLOOR_STEMS:
        return 'model_reasoning_effort = "low"'
    return ""


def emit_toml(stem: str, body: str) -> str:
    purpose = PURPOSES.get(stem)
    sandbox = SANDBOX.get(stem)
    if not purpose or not sandbox:
        raise SystemExit(f"Missing PURPOSES/SANDBOX for {stem}")

    parts = [
        f'name = "{stem}"',
        f'description = """{purpose}"""',
        f'sandbox_mode = "{sandbox}"',
    ]
    extra = floor_effort_line(stem)
    if extra:
        parts.append(extra)
    parts.append("")
    parts.append(
        "developer_instructions = " + toml_long_string(strip_retired_fast_lines(body))
    )
    parts.append("")
    return "\n".join(parts)


def source_stems(agents_dir: pathlib.Path) -> list[str]:
    return sorted(md.stem for md in agents_dir.glob("*.md"))


def unmapped_stems(stems: list[str]) -> list[str]:
    return [stem for stem in stems if stem not in PURPOSES or stem not in SANDBOX]


def render(agents_dir: pathlib.Path, stem: str) -> str:
    raw = (agents_dir / f"{stem}.md").read_text(encoding="utf-8")
    return emit_toml(stem, strip_optional_yaml_frontmatter(raw))


def expected_tomls(agents_dir: pathlib.Path = AGENTS_DIR) -> dict[str, str]:
    """Every stem's TOML text; exits naming all unmapped stems before rendering any."""
    stems = source_stems(agents_dir)
    unmapped = unmapped_stems(stems)
    if unmapped:
        raise SystemExit("Missing PURPOSES/SANDBOX for: " + ", ".join(unmapped))
    return {stem: render(agents_dir, stem) for stem in stems}


def display(path: pathlib.Path) -> str:
    try:
        return str(path.relative_to(ROOT))
    except ValueError:
        return str(path)


def write(agents_dir: pathlib.Path, out_dir: pathlib.Path) -> int:
    expected = expected_tomls(agents_dir)
    out_dir.mkdir(parents=True, exist_ok=True)
    for stem, text in expected.items():
        out = out_dir / f"{stem}.toml"
        out.write_text(text, encoding="utf-8")
        print("wrote", display(out))
    return 0


def check(agents_dir: pathlib.Path, out_dir: pathlib.Path) -> int:
    stems = set(source_stems(agents_dir))
    unmapped = set(unmapped_stems(sorted(stems)))
    tomls = {p.stem: p for p in out_dir.glob("*.toml")} if out_dir.is_dir() else {}

    reasons: list[tuple[str, str]] = []
    for stem in sorted(stems | set(tomls)):
        if stem not in stems:
            reasons.append(("orphan", stem))
        elif stem in unmapped:
            reasons.append(("unmapped", stem))
        elif stem not in tomls:
            reasons.append(("missing", stem))
        elif tomls[stem].read_text(encoding="utf-8") != render(agents_dir, stem):
            reasons.append(("stale", stem))

    verdict = "fail" if reasons else "pass"
    print(verdict)
    for kind, stem in reasons:
        print(f"reason: {kind} {stem}")
    counts = {kind: sum(1 for k, _ in reasons if k == kind)
              for kind in ("stale", "missing", "orphan", "unmapped")}
    print(
        f"gen-codex-agent-tomls: {verdict} ({counts['stale']} stale, "
        f"{counts['missing']} missing, {counts['orphan']} orphan, "
        f"{counts['unmapped']} unmapped)"
    )
    return 1 if reasons else 0


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        prog="gen-codex-agent-tomls.py",
        description="Generate or check codex/agents/*.toml from agents/*.md.",
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
