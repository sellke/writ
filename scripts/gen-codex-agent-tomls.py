#!/usr/bin/env python3
"""Generate codex/agents/*.toml from agents/*.md (developer_instructions = body).

Run from repo root: python3 scripts/gen-codex-agent-tomls.py

Purposes must stay aligned with .writ/manifest.yaml agents[].purpose.
"""

from __future__ import annotations

import pathlib
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
    "review-agent": "read-only",
    "testing-agent": "workspace-write",
    "user-story-generator": "workspace-write",
    "visual-qa-agent": "read-only",
}

# Manifest model: fast → concrete Codex tier ID (revisit when upstream aliases change).
FAST_MODEL = "gpt-5-mini"


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


def optional_model_line(stem: str) -> str:
    if stem in ("architecture-check-agent", "user-story-generator"):
        return f'model = "{FAST_MODEL}"\n'
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
    extra = optional_model_line(stem).rstrip()
    if extra:
        parts.append(extra)
    parts.append("")
    parts.append("developer_instructions = " + toml_long_string(body))
    parts.append("")
    return "\n".join(parts)


def main() -> None:
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    for md in sorted(AGENTS_DIR.glob("*.md")):
        stem = md.stem
        raw = md.read_text(encoding="utf-8")
        body = strip_optional_yaml_frontmatter(raw)
        out = OUT_DIR / f"{stem}.toml"
        out.write_text(emit_toml(stem, body), encoding="utf-8")
        print("wrote", out.relative_to(ROOT))


if __name__ == "__main__":
    try:
        main()
    except BrokenPipeError:
        sys.exit(0)
