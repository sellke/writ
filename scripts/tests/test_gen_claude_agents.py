#!/usr/bin/env python3
"""Unit tests for scripts/gen-claude-agents.py (Story 1 of
`2026-10-20-claude-agent-generator`, AC-1.1..AC-1.5).

The generator writes `claude-code/agents/writ-*.md` from `agents/*.md`: overlay
frontmatter, a generated-header HTML comment, the canonical body (YAML
frontmatter and retired `model: "fast"` lines removed), then an optional
suffix, with exactly one trailing newline. The module filename contains a
hyphen, so it is imported by path.

Fixture runs use temp dirs. The Story 2 tests at the bottom run `--check`
against the committed `agents/` and `claude-code/agents/` trees.
"""

from __future__ import annotations

import importlib.util
import re
import subprocess
import sys
from pathlib import Path

import pytest

MODULE_PATH = Path(__file__).resolve().parent.parent / "gen-claude-agents.py"
_spec = importlib.util.spec_from_file_location("gen_claude_agents", MODULE_PATH)
gen = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(gen)  # type: ignore[union-attr]

REPO_ROOT = MODULE_PATH.parent.parent
CANONICAL_DIR = REPO_ROOT / "agents"
COMMITTED_DIR = REPO_ROOT / "claude-code" / "agents"
MANIFEST = REPO_ROOT / ".writ" / "manifest.yaml"

HEADER_TEMPLATE = (
    "<!-- Generated from agents/{stem}.md by scripts/gen-claude-agents.py"
    " — do not hand-edit. Regenerate: python3 scripts/gen-claude-agents.py -->"
)

FILE_MAP = {
    "coding-agent": "writ-coder.md",
    "architecture-check-agent": "writ-architect.md",
    "documentation-agent": "writ-documenter.md",
    "evaluator-agent": "writ-evaluator.md",
    "review-agent": "writ-reviewer.md",
    "testing-agent": "writ-tester.md",
    "user-story-generator": "writ-story-gen.md",
    "visual-qa-agent": "writ-visual-qa.md",
}
COMMITTED_STEMS = sorted(s for s in FILE_MAP if s != "visual-qa-agent")

CODER_FRONTMATTER = (
    "---\n"
    "name: writ-coder\n"
    "description: TDD implementation agent for Writ stories. Writes tests first, then"
    " implements code to make them pass. Use for story implementation.\n"
    "tools: Read, Write, Edit, Bash, Grep, Glob\n"
    "model: inherit\n"
    "permissionMode: acceptEdits\n"
    "isolation: worktree\n"
    "maxTurns: 50\n"
    "memory: project\n"
    "---\n"
)
CODER_SUFFIX = (
    "Update your agent memory with patterns and conventions you discover in this codebase."
)


# --------------------------------------------------------------------------
# Helpers
# --------------------------------------------------------------------------

def run_cli(*args: str) -> subprocess.CompletedProcess:
    return subprocess.run([sys.executable, str(MODULE_PATH), *args],
                          capture_output=True, text=True)


def snapshot(directory: Path) -> dict:
    if not directory.exists():
        return {}
    return {p.name: p.read_bytes() for p in sorted(directory.iterdir())}


def frontmatter_block(text: str) -> str:
    """The leading `---\\n...\\n---\\n` block, closing fence included."""
    assert text.startswith("---\n"), text[:40]
    end = text.index("\n---\n", 4)
    return text[: end + 5]


def manifest_purpose(name: str) -> str:
    in_agent = False
    for line in MANIFEST.read_text(encoding="utf-8").splitlines():
        m = re.match(r"^\s*-\s+name:\s*(\S+)\s*$", line)
        if m:
            in_agent = m.group(1) == name
            continue
        m = re.match(r'^\s+purpose:\s*"(.*)"\s*$', line)
        if m and in_agent:
            return m.group(1)
    raise AssertionError("no manifest purpose for %s" % name)


class Fixture:
    """Temp `agents/` and out-dir driven through the real CLI."""

    def __init__(self, root: Path) -> None:
        self.agents = root / "agents"
        self.out = root / "claude-code" / "agents"
        self.agents.mkdir()

    def add(self, stem: str, text: str = "") -> None:
        body = text or "---\nname: %s\n---\n# %s\n\nBody.\n" % (stem, stem)
        (self.agents / ("%s.md" % stem)).write_text(body, encoding="utf-8")

    def cli(self, *args: str) -> subprocess.CompletedProcess:
        return run_cli("--agents-dir", str(self.agents), "--out-dir", str(self.out), *args)

    def generate(self) -> None:
        result = self.cli()
        assert result.returncode == 0, result.stdout + result.stderr

    def read(self, filename: str) -> str:
        return (self.out / filename).read_text(encoding="utf-8")


@pytest.fixture
def fx(tmp_path: Path) -> Fixture:
    return Fixture(tmp_path)


# --------------------------------------------------------------------------
# AC-1.1 — write mode: file shape and check-shape output
# --------------------------------------------------------------------------

def test_write_creates_absent_out_dir_and_prints_check_shape(fx: Fixture) -> None:
    """AC-1.1 — absent out-dir is created; `pass`, one `wrote` per file, summary last."""
    fx.add("review-agent")
    fx.add("coding-agent")
    assert not fx.out.exists()

    result = fx.cli()

    assert result.returncode == 0, result.stdout + result.stderr
    assert result.stdout.splitlines() == [
        "pass",
        "wrote %s" % (fx.out / "writ-coder.md"),
        "wrote %s" % (fx.out / "writ-reviewer.md"),
        "gen-claude-agents: pass (2 written, 0 unmapped)",
    ]
    assert sorted(p.name for p in fx.out.iterdir()) == ["writ-coder.md", "writ-reviewer.md"]


def test_rendered_file_is_frontmatter_header_body_suffix(fx: Fixture) -> None:
    """AC-1.1 — exact bytes: frontmatter, blank, header, blank, body, blank, suffix, one newline."""
    fx.add("coding-agent", "---\nname: coding-agent\n---\n# Coding Agent\n\nBody line.\n")
    fx.generate()
    assert fx.read("writ-coder.md") == (
        CODER_FRONTMATTER
        + "\n"
        + HEADER_TEMPLATE.format(stem="coding-agent") + "\n"
        + "\n"
        + "# Coding Agent\n\nBody line.\n"
        + "\n"
        + CODER_SUFFIX + "\n"
    )


def test_stem_without_suffix_ends_with_body(fx: Fixture) -> None:
    """AC-1.1 — no suffix means the body is last, followed by exactly one newline."""
    fx.add("testing-agent", "# Testing Agent\n\nLast line.\n")
    fx.generate()
    text = fx.read("writ-tester.md")
    assert text.endswith(HEADER_TEMPLATE.format(stem="testing-agent")
                         + "\n\n# Testing Agent\n\nLast line.\n")


def test_exactly_one_trailing_newline(fx: Fixture) -> None:
    """AC-1.1 — trailing blank lines in the canonical body collapse to one newline."""
    fx.add("testing-agent", "# Testing Agent\n\nBody.\n\n\n\n")
    fx.add("coding-agent", "# Coding Agent\n\nBody.\n\n\n")
    fx.generate()
    tester = fx.read("writ-tester.md")
    coder = fx.read("writ-coder.md")
    assert tester.endswith("Body.\n") and not tester.endswith("\n\n")
    assert coder.endswith("Body.\n\n" + CODER_SUFFIX + "\n")


def test_header_comment_sits_between_frontmatter_and_body(fx: Fixture) -> None:
    """AC-1.1 — the header is the first line after the closing fence and one blank line."""
    fx.add("review-agent")
    fx.generate()
    text = fx.read("writ-reviewer.md")
    after = text[len(frontmatter_block(text)):]
    assert after.startswith("\n" + HEADER_TEMPLATE.format(stem="review-agent") + "\n\n# review-agent\n")
    assert text.count("<!-- Generated from") == 1


def test_retired_fast_lines_are_stripped_and_other_model_lines_survive(fx: Fixture) -> None:
    """AC-1.1 — bare and comma-terminated `model: "fast"` lines go; other `model:` lines stay."""
    fx.add("testing-agent", (
        "# Testing Agent\n"
        "\n"
        "```\n"
        'model: "fast"\n'
        "model: default (inherits from parent)\n"
        "```\n"
        "\n"
        "Task({\n"
        '  subagent_type: "generalPurpose",\n'
        '  model: "fast",\n'
        "  model: inherit\n"
        "})\n"
    ))
    fx.generate()
    text = fx.read("writ-tester.md")
    assert not re.search(r'^\s*model:\s*"fast",?\s*$', text, re.MULTILINE)
    assert "model: default (inherits from parent)\n" in text
    assert "  model: inherit\n" in text
    assert '  subagent_type: "generalPurpose",\n  model: inherit\n' in text


def test_body_rules_and_comments_pass_through(fx: Fixture) -> None:
    """Interaction edge: later `---` rules and `<!--` comments in the body are verbatim."""
    body = "# Testing Agent\n\n---\n\n<!-- keep me -->\n\nAfter rule.\n\n---\n\nEnd.\n"
    fx.add("testing-agent", "---\nname: x\n---\n" + body)
    fx.generate()
    text = fx.read("writ-tester.md")
    assert text.endswith("\n\n" + body)


def test_frontmatter_only_canonical_renders_header_and_suffix(fx: Fixture) -> None:
    """Shadow path (empty): body is empty; output is frontmatter, header, suffix."""
    fx.add("coding-agent", "---\nname: coding-agent\n---\n")
    fx.generate()
    assert fx.read("writ-coder.md") == (
        CODER_FRONTMATTER + "\n" + HEADER_TEMPLATE.format(stem="coding-agent")
        + "\n\n" + CODER_SUFFIX + "\n"
    )


def test_write_ignores_agents_dir_location_in_header(tmp_path: Path) -> None:
    """The header always names `agents/<stem>.md`, so output does not depend on --agents-dir."""
    fixtures = []
    for name in ("a", "b"):
        (tmp_path / name).mkdir()
        f = Fixture(tmp_path / name)
        f.add("review-agent")
        f.generate()
        fixtures.append(f)
    assert fixtures[0].read("writ-reviewer.md") == fixtures[1].read("writ-reviewer.md")


# --------------------------------------------------------------------------
# AC-1.2 — --check: pass, each reason kind, sorting, summary
# --------------------------------------------------------------------------

def test_check_passes_on_fresh_output_and_writes_nothing(fx: Fixture) -> None:
    """AC-1.2 — aligned tree: `pass`, zeroed summary, exit 0, no writes."""
    fx.add("coding-agent")
    fx.add("review-agent")
    fx.generate()
    before = snapshot(fx.out)

    result = fx.cli("--check")

    assert result.returncode == 0, result.stdout + result.stderr
    assert result.stdout.splitlines() == [
        "pass",
        "gen-claude-agents: pass (0 stale, 0 missing, 0 orphan, 0 unmapped)",
    ]
    assert snapshot(fx.out) == before


def test_check_reports_every_reason_kind_sorted(fx: Fixture) -> None:
    """AC-1.2 — stale, missing, orphan, unmapped: one `reason:` each, sorted, counted summary."""
    for stem in ("coding-agent", "review-agent", "testing-agent"):
        fx.add(stem)
    fx.generate()
    coder = fx.out / "writ-coder.md"
    coder.write_text(coder.read_text(encoding="utf-8") + "hand edit\n", encoding="utf-8")
    (fx.out / "writ-reviewer.md").unlink()
    (fx.out / "writ-foo.md").write_text("orphan\n", encoding="utf-8")
    (fx.out / "README.md").write_text("not a writ agent\n", encoding="utf-8")
    fx.add("mmm-unmapped")
    before = snapshot(fx.out)

    result = fx.cli("--check")

    assert result.returncode == 1, result.stdout + result.stderr
    assert result.stdout.splitlines() == [
        "fail",
        "reason: stale coding-agent",
        "reason: unmapped mmm-unmapped",
        "reason: missing review-agent",
        "reason: orphan writ-foo",
        "gen-claude-agents: fail (1 stale, 1 missing, 1 orphan, 1 unmapped)",
    ]
    assert snapshot(fx.out) == before


def test_check_flags_generated_file_whose_canonical_source_is_gone(fx: Fixture) -> None:
    """AC-1.2 — a `writ-*.md` with no canonical source is an orphan, even if overlay-mapped."""
    fx.add("coding-agent")
    fx.add("review-agent")
    fx.generate()
    (fx.agents / "review-agent.md").unlink()

    result = fx.cli("--check")

    assert result.returncode == 1
    assert result.stdout.splitlines() == [
        "fail",
        "reason: orphan writ-reviewer",
        "gen-claude-agents: fail (0 stale, 0 missing, 1 orphan, 0 unmapped)",
    ]


def test_check_detects_whitespace_only_drift(fx: Fixture) -> None:
    """AC-1.2 — byte comparison: an extra trailing newline is stale."""
    fx.add("testing-agent")
    fx.generate()
    path = fx.out / "writ-tester.md"
    path.write_text(path.read_text(encoding="utf-8") + "\n", encoding="utf-8")
    result = fx.cli("--check")
    assert result.returncode == 1
    assert "reason: stale testing-agent" in result.stdout.splitlines()


def test_check_missing_out_dir_reports_missing_without_creating_it(fx: Fixture) -> None:
    """AC-1.2 — absent out-dir: every stem is missing; the dir is not created."""
    fx.add("coding-agent")

    result = fx.cli("--check")

    assert result.returncode == 1
    assert result.stdout.splitlines() == [
        "fail",
        "reason: missing coding-agent",
        "gen-claude-agents: fail (0 stale, 1 missing, 0 orphan, 0 unmapped)",
    ]
    assert not fx.out.exists()


def test_check_with_absent_agents_dir_does_not_crash(tmp_path: Path) -> None:
    """Shadow path (nil): no `agents/` and no out-dir: nothing to compare, exit 0."""
    result = run_cli("--agents-dir", str(tmp_path / "none"), "--out-dir",
                     str(tmp_path / "out"), "--check")
    assert result.returncode == 0, result.stderr
    assert result.stdout.splitlines()[-1] == (
        "gen-claude-agents: pass (0 stale, 0 missing, 0 orphan, 0 unmapped)"
    )


# --------------------------------------------------------------------------
# AC-1.3 — validate before write
# --------------------------------------------------------------------------

def test_unmapped_stem_aborts_write_with_no_files(fx: Fixture) -> None:
    """AC-1.3 — unmapped stem: `fail`, one reason each, nothing written, exit 1."""
    fx.add("coding-agent")
    fx.add("alpha-unmapped")
    fx.add("zeta-unmapped")
    fx.out.mkdir(parents=True)
    (fx.out / "sentinel.txt").write_text("keep\n", encoding="utf-8")
    before = snapshot(fx.out)

    result = fx.cli()

    assert result.returncode == 1, result.stdout + result.stderr
    assert result.stdout.splitlines() == [
        "fail",
        "reason: unmapped alpha-unmapped",
        "reason: unmapped zeta-unmapped",
        "gen-claude-agents: fail (0 written, 2 unmapped)",
    ]
    assert snapshot(fx.out) == before


def test_unmapped_stem_does_not_create_out_dir(fx: Fixture) -> None:
    """AC-1.3 — the out-dir is not created when validation fails."""
    fx.add("coding-agent")
    fx.add("nope-agent")
    assert fx.cli().returncode == 1
    assert not fx.out.exists()


# --------------------------------------------------------------------------
# AC-1.4 — overlay seeded verbatim from the committed files
# --------------------------------------------------------------------------

def test_overlay_covers_every_canonical_stem_with_the_explicit_file_map() -> None:
    """Business Rule 4 — the overlay maps exactly the canonical stems to their filenames."""
    canonical = sorted(p.stem for p in CANONICAL_DIR.glob("*.md"))
    assert sorted(gen.OVERLAY) == canonical
    assert {stem: entry["file"] for stem, entry in gen.OVERLAY.items()} == FILE_MAP


@pytest.mark.parametrize("stem", COMMITTED_STEMS)
def test_overlay_frontmatter_matches_committed_file(stem: str) -> None:
    """AC-1.4 — rendered frontmatter equals the committed file's, byte for byte, key order included."""
    committed = (COMMITTED_DIR / FILE_MAP[stem]).read_text(encoding="utf-8")
    assert gen.render_frontmatter(stem) == frontmatter_block(committed)


@pytest.mark.parametrize("stem", COMMITTED_STEMS)
def test_overlay_suffix_matches_committed_memory_lines(stem: str) -> None:
    """AC-1.4 — the suffix is the committed file's trailing memory lines, verbatim, and is
    Claude-only: none of its lines appear in the canonical body."""
    committed = (COMMITTED_DIR / FILE_MAP[stem]).read_text(encoding="utf-8")
    lines = committed.rstrip("\n").split("\n")
    tail = []
    while lines and "memory" in lines[-1].lower():
        tail.insert(0, lines.pop())
    suffix = gen.OVERLAY[stem].get("suffix", "")
    assert suffix == "\n".join(tail)
    if suffix:
        assert committed.endswith("\n\n" + suffix + "\n")
        canonical = (CANONICAL_DIR / ("%s.md" % stem)).read_text(encoding="utf-8")
        for line in suffix.split("\n"):
            assert line not in canonical


def test_visual_qa_overlay_values() -> None:
    """AC-1.4 — the new entry: read-only tools, plan mode, 20 turns, manifest purpose, no memory, no suffix."""
    entry = gen.OVERLAY["visual-qa-agent"]
    assert entry["file"] == "writ-visual-qa.md"
    assert list(entry["frontmatter"]) == [
        ("name", "writ-visual-qa"),
        ("description", manifest_purpose("visual-qa-agent")),
        ("tools", "Read, Grep, Glob, Bash"),
        ("disallowedTools", "Write, Edit"),
        ("model", "inherit"),
        ("permissionMode", "plan"),
        ("maxTurns", "20"),
    ]
    assert entry.get("suffix", "") == ""


def test_visual_qa_renders_writ_visual_qa_md(fx: Fixture) -> None:
    """AC-1.4 — write mode emits `writ-visual-qa.md` with the overlay frontmatter."""
    fx.add("visual-qa-agent")
    fx.generate()
    text = fx.read("writ-visual-qa.md")
    assert frontmatter_block(text) == gen.render_frontmatter("visual-qa-agent")
    assert text.endswith("# visual-qa-agent\n\nBody.\n")


@pytest.mark.parametrize("stem", sorted(FILE_MAP))
def test_frontmatter_lines_are_plain_key_value(stem: str) -> None:
    """Risk note — values are unquoted, so each line must be a plain `key: value` that
    YAML reads as a string with no quoting."""
    for key, value in gen.OVERLAY[stem]["frontmatter"]:
        assert re.match(r"^[A-Za-z]+$", key), key
        assert value and value == value.strip(), (key, value)
        assert ": " not in value and " #" not in value, (key, value)
        assert value[0] not in "[]{}&*!|>'\"%@`#,?:-", (key, value)


# --------------------------------------------------------------------------
# AC-1.5 — usage errors and standalone script
# --------------------------------------------------------------------------

@pytest.mark.parametrize("args", [["--bogus"], ["--che"], ["extra-positional"]])
def test_bad_argument_prints_usage_to_stderr_and_exits_2(args: list) -> None:
    """AC-1.5 — usage on stderr, empty stdout, exit 2 (abbreviations rejected)."""
    result = run_cli(*args)
    assert result.returncode == 2
    assert result.stdout == ""
    assert "usage: gen-claude-agents.py" in result.stderr


def test_script_does_not_import_the_codex_generator() -> None:
    """Notes — standalone script: helpers are duplicated, not imported."""
    source = MODULE_PATH.read_text(encoding="utf-8")
    assert "gen-codex-agent-tomls" not in source.split('"""', 2)[2]
    assert "gen_codex" not in source
    assert hasattr(gen, "strip_optional_yaml_frontmatter")
    assert hasattr(gen, "RETIRED_FAST_LINE")


# --------------------------------------------------------------------------
# Story 2 — the committed tree is generated (AC-2.1, AC-2.3, AC-2.5)
# --------------------------------------------------------------------------

def test_committed_tree_passes_check() -> None:
    """AC-2.1, AC-2.5 — `--check` against the real `agents/` and `claude-code/agents/`
    passes with zero drift. Absolute paths, so the test works from any cwd."""
    result = run_cli("--agents-dir", str(CANONICAL_DIR), "--out-dir", str(COMMITTED_DIR), "--check")
    assert result.returncode == 0, result.stdout + result.stderr
    assert result.stdout.splitlines()[0] == "pass"
    assert result.stdout.splitlines()[-1] == (
        "gen-claude-agents: pass (0 stale, 0 missing, 0 orphan, 0 unmapped)"
    )


def test_committed_tree_holds_eight_generated_agents() -> None:
    """AC-2.1 — one `writ-*.md` per canonical stem, `writ-visual-qa.md` included."""
    assert sorted(p.name for p in COMMITTED_DIR.glob("writ-*.md")) == sorted(FILE_MAP.values())


def test_committed_coder_carries_the_canonical_prompt_contract() -> None:
    """AC-2.3 — the regenerated coder has the iteration cap and the boundary_map rules."""
    text = (COMMITTED_DIR / "writ-coder.md").read_text(encoding="utf-8")
    assert "MAX_SELF_FIX_ITERATIONS = 3" in text
    assert "**When `boundary_map` is non-empty (Gate 0.5 ran):**" in text
    assert "File Ownership Boundaries" in text


def test_committed_visual_qa_is_read_only_plan_mode() -> None:
    """AC-2.1 — `writ-visual-qa.md`: inherit model, plan mode, Write/Edit disallowed,
    generated header after the frontmatter."""
    text = (COMMITTED_DIR / "writ-visual-qa.md").read_text(encoding="utf-8")
    fm = frontmatter_block(text)
    assert "\nmodel: inherit\n" in fm
    assert "\npermissionMode: plan\n" in fm
    assert "\ndisallowedTools: Write, Edit\n" in fm
    assert text[len(fm):].startswith(
        "\n" + HEADER_TEMPLATE.format(stem="visual-qa-agent") + "\n"
    )
