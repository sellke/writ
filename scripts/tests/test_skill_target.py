"""Tests for scripts/skill-target.py: where /new-skill writes a skill, and
whether the name is free.

- Writ source repository (`.writ/manifest.yaml` present): the names are the
  manifest's `commands:`, `agents:`, and `skills:` entries plus the folders
  under `skills/`; the target is `skills/<name>/SKILL.md` and the manifest
  line names the manifest.
- Installed project (no manifest; install.sh and the plugin create none): the
  names are the files in the platform's commands and agents folders and the
  folders in its skills folder, plus the plugin's own when the script runs
  from a Claude Code plugin; the target is the platform's skills folder and
  the manifest line is `none`.
- The check writes nothing.

scripts/tests/test_new_skill_installed.sh runs the installed command's own
call against real install.sh installs and the plugin.

Run: uv run --python 3.9 pytest scripts/tests/test_skill_target.py
"""

from __future__ import annotations

import re
import shutil
import subprocess
import sys
from pathlib import Path
from typing import Dict, List

import pytest

REPO_ROOT = Path(__file__).resolve().parents[2]
SCRIPT = REPO_ROOT / "scripts" / "skill-target.py"
COMMAND = REPO_ROOT / "commands" / "new-skill.md"

MANIFEST = """\
version: 1
categories:
  - id: build
    label: Build
commands:
  - name: review
    file: commands/review.md
    category: build
    purpose: "Review."
agents:
  - name: coding-agent
    file: agents/coding-agent.md
    purpose: "Code."
skills:
  - name: tdd-cycle
    file: skills/tdd-cycle/SKILL.md
    description: "Run a cycle."
    status: candidate
"""

# platform -> (commands dir, agent file, skills dir), as install.sh lays them out.
INSTALLED = {
    "claude": (".claude/commands", ".claude/agents/writ-coder.md", ".claude/skills"),
    "cursor": (".cursor/commands", ".cursor/agents/coding-agent.md", ".cursor/skills"),
    "codex": (".codex/commands", ".codex/agents/coding-agent.toml", ".agents/skills"),
}


def run(args: List[str], cwd: Path, script: Path = SCRIPT) -> subprocess.CompletedProcess:
    return subprocess.run([sys.executable, str(script)] + args, cwd=str(cwd),
                          capture_output=True, text=True, timeout=60)


def fields(stdout: str) -> Dict[str, str]:
    """`key: value` detail lines; `reason` lines are joined with newlines."""
    out = {}  # type: Dict[str, str]
    for line in stdout.splitlines()[1:-1]:
        key, _, value = line.partition(": ")
        out[key] = out[key] + "\n" + value if key in out else value
    return out


def write(path: Path, text: str = "x\n") -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text, encoding="utf-8")


def tree(root: Path) -> List[str]:
    return sorted(str(p.relative_to(root)) for p in root.rglob("*"))


@pytest.fixture
def source(tmp_path: Path) -> Path:
    write(tmp_path / ".writ" / "manifest.yaml", MANIFEST)
    write(tmp_path / "commands" / "review.md")
    write(tmp_path / "skills" / "tdd-cycle" / "SKILL.md")
    return tmp_path


def installed(root: Path, platform: str) -> Path:
    commands, agent, skills = INSTALLED[platform]
    write(root / commands / "review.md")
    write(root / commands / "_preamble.md")
    write(root / agent)
    write(root / skills / "tdd-cycle" / "SKILL.md")
    return root


# -- Writ source repository --------------------------------------------------


def test_source_free_name_targets_skills_and_the_manifest(source):
    before = tree(source)
    result = run(["check", "release-notes", "--platform", "claude"], source)
    assert result.returncode == 0, result.stdout + result.stderr
    lines = result.stdout.splitlines()
    assert lines[0] == "pass"
    assert lines[-1] == "skill-target: pass (source, 0 taken)"
    got = fields(result.stdout)
    assert got["target"] == "skills/release-notes/SKILL.md"
    assert got["manifest"] == ".writ/manifest.yaml"
    assert "reason" not in got
    assert tree(source) == before


@pytest.mark.parametrize("name,taken", [
    ("review", "command commands/review.md"),
    ("coding-agent", "agent agents/coding-agent.md"),
    ("tdd-cycle", "skill skills/tdd-cycle/SKILL.md"),
])
def test_source_name_taken_by_a_manifest_entry(source, name, taken):
    result = run(["check", name, "--platform", "claude"], source)
    assert result.returncode == 1
    assert result.stdout.splitlines()[0] == "fail"
    assert fields(result.stdout)["reason"] == "name taken by %s" % taken
    assert result.stdout.splitlines()[-1] == "skill-target: fail (source, 1 taken)"


def test_source_skill_folder_missing_from_the_manifest_is_taken(source):
    write(source / "skills" / "stray" / "SKILL.md")
    result = run(["check", "stray", "--platform", "claude"], source)
    assert result.stdout.splitlines()[0] == "fail"
    assert fields(result.stdout)["reason"] == "name taken by skill skills/stray"


def test_the_writ_repository_is_a_source_checkout():
    result = run(["check", "new-skill", "--platform", "claude"], REPO_ROOT)
    assert result.stdout.splitlines()[0] == "fail"
    assert "name taken by command commands/new-skill.md" in fields(result.stdout)["reason"]
    result = run(["check", "zz-unused-skill", "--platform", "cursor"], REPO_ROOT)
    assert result.stdout.splitlines()[0] == "pass"
    assert fields(result.stdout)["target"] == "skills/zz-unused-skill/SKILL.md"
    assert not (REPO_ROOT / "skills" / "zz-unused-skill").exists()


# -- Installed project ---------------------------------------------------------


@pytest.mark.parametrize("platform", sorted(INSTALLED))
def test_installed_free_name_targets_the_platform_skills_folder(tmp_path, platform):
    project = installed(tmp_path, platform)
    before = tree(project)
    result = run(["check", "release-notes", "--platform", platform], project)
    assert result.returncode == 0, result.stdout + result.stderr
    assert result.stdout.splitlines()[0] == "pass"
    got = fields(result.stdout)
    assert got["target"] == "%s/release-notes/SKILL.md" % INSTALLED[platform][2]
    assert got["manifest"] == "none"
    assert result.stdout.splitlines()[-1] == "skill-target: pass (installed %s, 0 taken)" % platform
    assert tree(project) == before
    assert not (project / ".writ" / "manifest.yaml").exists()


@pytest.mark.parametrize("platform", sorted(INSTALLED))
def test_installed_names_are_the_installed_files(tmp_path, platform):
    project = installed(tmp_path, platform)
    commands, agent, skills = INSTALLED[platform]
    cases = {
        "review": "command %s/review.md" % commands,
        Path(agent).stem: "agent %s" % agent,
        "tdd-cycle": "skill %s/tdd-cycle" % skills,
    }
    for name, taken in cases.items():
        result = run(["check", name, "--platform", platform], project)
        assert result.returncode == 1, (name, result.stdout)
        assert fields(result.stdout)["reason"] == "name taken by %s" % taken


def test_installed_check_reads_only_the_named_platform(tmp_path):
    project = installed(tmp_path, "cursor")
    write(project / ".claude" / "commands" / "only-claude.md")
    result = run(["check", "only-claude", "--platform", "cursor"], project)
    assert result.stdout.splitlines()[0] == "pass"


def test_plugin_names_count_when_run_from_a_plugin(tmp_path):
    plugin = tmp_path / "plugin"
    write(plugin / ".claude-plugin" / "plugin.json", "{}\n")
    write(plugin / "commands" / "review.md")
    write(plugin / "agents" / "writ-coder.md")
    write(plugin / "skills" / "tdd-cycle" / "SKILL.md")
    script = plugin / "scripts" / "skill-target.py"
    script.parent.mkdir(parents=True)
    shutil.copy(str(SCRIPT), str(script))
    project = tmp_path / "project"
    project.mkdir()
    root = plugin.resolve()

    for name, taken in (("review", "command %s/commands/review.md" % root),
                        ("writ-coder", "agent %s/agents/writ-coder.md" % root),
                        ("tdd-cycle", "skill %s/skills/tdd-cycle" % root)):
        result = run(["check", name, "--platform", "claude"], project, script)
        assert fields(result.stdout)["reason"] == "name taken by %s" % taken
    result = run(["check", "release-notes", "--platform", "claude"], project, script)
    assert result.stdout.splitlines()[0] == "pass"
    assert fields(result.stdout)["target"] == ".claude/skills/release-notes/SKILL.md"
    assert fields(result.stdout)["manifest"] == "none"
    assert tree(project) == []


def test_no_install_found_is_unverifiable(tmp_path):
    result = run(["check", "release-notes", "--platform", "codex"], tmp_path)
    assert result.returncode == 0
    lines = result.stdout.splitlines()
    assert lines[0] == "unverifiable"
    assert fields(result.stdout)["reason"] == (
        "no .codex/commands/ and not run from a plugin; check --platform")
    assert lines[-1] == "skill-target: unverifiable (installed codex, 0 taken)"


# -- Name format and usage -----------------------------------------------------


@pytest.mark.parametrize("name", ["Bad", "1st", "a_b", "a.b", "a/b"])
def test_a_name_that_is_not_kebab_case_fails(source, name):
    result = run(["check", name, "--platform", "claude"], source)
    assert result.returncode == 1
    assert fields(result.stdout)["reason"] == "name %s is not kebab-case" % name


@pytest.mark.parametrize("args", [
    ["check", "x"],
    ["check", "x", "--platform", "openclaw"],
    ["check", "x", "--platform", "claude", "--project", "missing-dir"],
    [],
])
def test_usage_errors_exit_2_with_empty_stdout(tmp_path, args):
    result = run(args, tmp_path)
    assert result.returncode == 2
    assert result.stdout == ""


# -- The command ---------------------------------------------------------------


def section(text: str, heading: str) -> str:
    match = re.search(r"^#### %s\n(.*?)(?=^#{2,4} )" % re.escape(heading), text, re.M | re.S)
    assert match, heading
    return match.group(1)


def test_new_skill_checks_names_with_the_script():
    """Step 1.1 calls the script; it no longer reads the manifest by hand."""
    text = COMMAND.read_text(encoding="utf-8")
    step = section(text, "Step 1.1: Resolve the Name")
    assert "python3 scripts/skill-target.py check <name> --platform <platform>" in step
    assert "Read `.writ/manifest.yaml`" not in text


def test_new_skill_skips_the_manifest_in_an_installed_project():
    text = COMMAND.read_text(encoding="utf-8")
    step = section(text, "Step 3.2: Append to `.writ/manifest.yaml`")
    assert "`manifest: none`" in step
    assert "do not create one" in step
    assert "`target:`" in section(text, "Step 3.1: Write the Skill File")
