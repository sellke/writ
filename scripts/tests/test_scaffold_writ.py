#!/usr/bin/env python3
"""Tests for Story 4 of `2026-10-22-plugin-distribution`: `scripts/scaffold-writ.py`,
the bash `init_writ_workspace` the installers keep, `/initialize` Step 0, and
ADR-031.

- The script, run in temp directories only: a fresh directory gets the eleven
  paths and both `.gitignore` entries with check-shape output; a second run
  creates nothing and leaves `.gitignore` byte-identical; an existing
  `.writ/state` or `.writ/state/` line is not appended again; `--check`
  reports what is missing and writes nothing; usage errors exit 2 with empty
  stdout `[AC-4.1, AC-4.2, AC-4.3]`.
- The installers: `install.sh` and `update.sh` hold one byte-identical
  `init_writ_workspace`; its `mkdir -p` brace list expands to the script's
  `PATHS` (`test_bash_list_matches`); run in bash, it leaves `.gitignore` with
  the same bytes the script does; neither installer calls python; `update.sh`
  calls the function after `WRIT_SRC` is set `[AC-4.4]`.
- `commands/initialize.md` Step 0, its rendered plugin copy, ADR-031, the
  ADR-029 header line, and the script-install-location issue's resolution
  `[AC-4.4, AC-4.5]`.

EXPECTED_PATHS is written out here, not imported, so a change to the script's
list fails this file until the test says the same.

Run: uv run --python 3.9 pytest scripts/tests/test_scaffold_writ.py
"""

from __future__ import annotations

import importlib.util
import re
import subprocess
import sys
from pathlib import Path
from typing import List, Optional

import pytest

REPO_ROOT = Path(__file__).resolve().parents[2]
SCRIPT = REPO_ROOT / "scripts" / "scaffold-writ.py"
INSTALL_SH = REPO_ROOT / "scripts" / "install.sh"
UPDATE_SH = REPO_ROOT / "scripts" / "update.sh"
INITIALIZE = REPO_ROOT / "commands" / "initialize.md"
PLUGIN_INITIALIZE = REPO_ROOT / "plugins" / "writ" / "commands" / "initialize.md"
PLUGIN_SCRIPT = REPO_ROOT / "plugins" / "writ" / "scripts" / "scaffold-writ.py"
ADR_DIR = REPO_ROOT / ".writ" / "decision-records"
ADR_029 = ADR_DIR / "adr-029-agent-cli-contract.md"
ADR_031 = ADR_DIR / "adr-031-script-location.md"
ISSUE = REPO_ROOT / ".writ" / "issues" / "improvements" / "2026-10-12-script-install-location.md"
SPEC_PATH = ".writ/specs/2026-10-22-plugin-distribution/spec.md"

EXPECTED_PATHS = [
    ".writ/specs",
    ".writ/product",
    ".writ/research",
    ".writ/decision-records",
    ".writ/docs",
    ".writ/knowledge",
    ".writ/state",
    ".writ/issues/bugs",
    ".writ/issues/features",
    ".writ/issues/improvements",
    ".writ/issues/goals",
]
ENTRIES = [".writ/state/", ".writ-lanes-*/"]
COMMENT = "# Writ ephemeral state"
FRESH_GITIGNORE = COMMENT + "\n.writ/state/\n.writ-lanes-*/\n"


def run(args: List[str], cwd: Path) -> subprocess.CompletedProcess:
    return subprocess.run([sys.executable, str(SCRIPT)] + args, cwd=str(cwd),
                          capture_output=True, text=True, timeout=60)


def scaffold(project: Path, *extra: str) -> subprocess.CompletedProcess:
    return run(["scaffold", "--project", str(project)] + list(extra), project)


def tree(root: Path) -> List[str]:
    """Every path under `root`, relative, sorted: the "nothing was written" probe."""
    return sorted(p.relative_to(root).as_posix() for p in root.rglob("*"))


def load_script():
    spec = importlib.util.spec_from_file_location("scaffold_writ", SCRIPT)
    assert spec is not None and spec.loader is not None, "cannot load %s" % SCRIPT
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def bash_function(path: Path, name: str = "init_writ_workspace") -> str:
    """The `name() {` ... `}` block of a bash script, both lines included."""
    lines = path.read_text(encoding="utf-8").splitlines(keepends=True)
    start = next((i for i, l in enumerate(lines) if l.startswith(name + "() {")), None)
    assert start is not None, "%s has no %s() function" % (path.name, name)
    end = next(i for i in range(start, len(lines)) if lines[i].rstrip("\n") == "}")
    return "".join(lines[start:end + 1])


def expand_braces(word: str) -> List[str]:
    """Bash brace expansion for `a/{b,c}` words, innermost group first."""
    match = re.search(r"\{([^{}]*,[^{}]*)\}", word)
    if match is None:
        return [word]
    out: List[str] = []
    for alt in match.group(1).split(","):
        out.extend(expand_braces(word[:match.start()] + alt + word[match.end():]))
    return out


def mkdir_paths(function_text: str) -> List[str]:
    lines = [l.strip() for l in function_text.splitlines() if l.strip().startswith("mkdir -p ")]
    assert len(lines) == 1, "expected one `mkdir -p` line in init_writ_workspace, got %r" % lines
    paths: List[str] = []
    for word in lines[0].split()[2:]:
        paths.extend(expand_braces(word))
    return paths


def write_gitignore(project: Path, text: Optional[str]) -> None:
    if text is not None:
        (project / ".gitignore").write_bytes(text.encode("utf-8"))


def normalized(line: str) -> str:
    line = line.strip()
    return line[:-1] if line.endswith("/") else line


# --------------------------------------------------------------------------
# scaffold: error paths
# --------------------------------------------------------------------------

def test_no_subcommand_is_usage_error(tmp_path):
    """AC-4.3 — no subcommand: usage on stderr, stdout empty, exit 2."""
    result = run([], tmp_path)
    assert result.returncode == 2, result
    assert result.stdout == ""
    assert "usage" in result.stderr.lower()


def test_unknown_flag_is_usage_error(tmp_path):
    """AC-4.3 — an unknown flag: usage on stderr, stdout empty, exit 2, nothing written."""
    result = run(["scaffold", "--project", str(tmp_path), "--zz-unknown"], tmp_path)
    assert result.returncode == 2, result
    assert result.stdout == ""
    assert "usage" in result.stderr.lower()
    assert tree(tmp_path) == []


def test_help_exits_zero(tmp_path):
    """AC-4.3 — `--help` and `scaffold --help` exit 0 and name the subcommand and flags."""
    for args in (["--help"], ["scaffold", "--help"]):
        result = run(args, tmp_path)
        assert result.returncode == 0, result
        assert "scaffold" in result.stdout
    assert "--check" in run(["scaffold", "--help"], tmp_path).stdout
    assert "--project" in run(["scaffold", "--help"], tmp_path).stdout


def test_missing_project_directory_is_usage_error(tmp_path):
    """AC-4.3 — `--project` that is not a directory cannot start: stderr, stdout empty, exit 2."""
    result = run(["scaffold", "--project", str(tmp_path / "absent")], tmp_path)
    assert result.returncode == 2, result
    assert result.stdout == ""
    assert "--project" in result.stderr and "not a directory" in result.stderr
    assert not (tmp_path / "absent").exists()


def test_path_blocked_by_a_file_fails(tmp_path):
    """AC-4.1 — a file where a directory belongs is a `fail` with a reason; the rest are created."""
    (tmp_path / ".writ").mkdir()
    (tmp_path / ".writ" / "specs").write_text("not a dir\n", encoding="utf-8")
    result = scaffold(tmp_path)
    lines = result.stdout.splitlines()
    assert result.returncode == 1, result
    assert lines[0] == "fail"
    assert "reason: not a directory .writ/specs" in lines
    assert lines[-1] == "scaffold-writ: fail (10 created, 0 existing, 1 not a directory)"
    for rel in EXPECTED_PATHS[1:]:
        assert (tmp_path / rel).is_dir(), rel


# --------------------------------------------------------------------------
# scaffold: the tree and .gitignore
# --------------------------------------------------------------------------

def test_fresh_directory_gets_the_tree(tmp_path):
    """AC-4.1 — eleven directories, `pass` on line 1, one `created` line per path, summary last."""
    result = scaffold(tmp_path)
    lines = result.stdout.splitlines()
    assert result.returncode == 0, result
    assert lines[0] == "pass"
    assert [l for l in lines if l.startswith("created ")] == ["created " + p for p in EXPECTED_PATHS]
    assert lines[-1] == "scaffold-writ: pass (11 created, 0 existing)"
    for rel in EXPECTED_PATHS:
        assert (tmp_path / rel).is_dir(), rel
    assert not (tmp_path / ".writ" / "explanations").exists()


def test_fresh_directory_gets_a_gitignore(tmp_path):
    """AC-4.1 — no `.gitignore`: it is created holding each entry once, under the comment."""
    result = scaffold(tmp_path)
    assert result.returncode == 0, result
    assert (tmp_path / ".gitignore").read_text(encoding="utf-8") == FRESH_GITIGNORE
    added = [l for l in result.stdout.splitlines() if l.startswith("added ")]
    assert added == ["added .gitignore entry " + e for e in ENTRIES]


def test_project_defaults_to_the_current_directory(tmp_path):
    """AC-4.1 — `scaffold` with no `--project` scaffolds the cwd."""
    result = run(["scaffold"], tmp_path)
    assert result.returncode == 0, result
    assert result.stdout.splitlines()[-1] == "scaffold-writ: pass (11 created, 0 existing)"
    assert all((tmp_path / rel).is_dir() for rel in EXPECTED_PATHS)


def test_partial_tree_reports_only_missing_paths(tmp_path):
    """AC-4.1 — a `created` line only for a path that was missing; intermediate parents get none."""
    (tmp_path / ".writ" / "specs").mkdir(parents=True)
    (tmp_path / ".writ" / "issues" / "bugs").mkdir(parents=True)
    result = scaffold(tmp_path)
    lines = result.stdout.splitlines()
    assert result.returncode == 0, result
    created = [l[len("created "):] for l in lines if l.startswith("created ")]
    assert created == [p for p in EXPECTED_PATHS if p not in (".writ/specs", ".writ/issues/bugs")]
    assert "created .writ" not in lines and "created .writ/issues" not in lines
    assert lines[-1] == "scaffold-writ: pass (9 created, 2 existing)"


def test_second_run_creates_nothing(tmp_path):
    """AC-4.2 — a complete tree: `0 created, 11 existing`, no new path, `.gitignore` byte-identical."""
    assert scaffold(tmp_path).returncode == 0
    before_tree = tree(tmp_path)
    before_ignore = (tmp_path / ".gitignore").read_bytes()
    result = scaffold(tmp_path)
    assert result.returncode == 0, result
    assert result.stdout.splitlines() == ["pass", "scaffold-writ: pass (0 created, 11 existing)"]
    assert tree(tmp_path) == before_tree
    assert (tmp_path / ".gitignore").read_bytes() == before_ignore


@pytest.mark.parametrize("line", [".writ/state", ".writ/state/", "  .writ/state/  "])
def test_existing_state_line_is_not_appended_again(tmp_path, line):
    """AC-4.2 — `.writ/state` with or without `/` (trimmed whole line) counts as present."""
    write_gitignore(tmp_path, "node_modules/\n%s\n" % line)
    result = scaffold(tmp_path)
    assert result.returncode == 0, result
    text = (tmp_path / ".gitignore").read_text(encoding="utf-8")
    assert text.startswith("node_modules/\n%s\n" % line), text
    assert [normalized(l) for l in text.splitlines()].count(".writ/state") == 1
    assert [normalized(l) for l in text.splitlines()].count(".writ-lanes-*") == 1
    added = [l for l in result.stdout.splitlines() if l.startswith("added ")]
    assert added == ["added .gitignore entry .writ-lanes-*/"]


def test_existing_gitignore_keeps_its_bytes_and_gains_the_block(tmp_path):
    """AC-4.1 — user lines stay byte for byte; the block follows a blank line, written once."""
    write_gitignore(tmp_path, "dist/\r\n*.log")
    assert scaffold(tmp_path).returncode == 0
    assert (tmp_path / ".gitignore").read_bytes() == (
        b"dist/\r\n*.log\n" + FRESH_GITIGNORE.encode("utf-8"))
    assert not [p for p in tmp_path.iterdir() if p.name.startswith(".gitignore.")]


def test_old_install_block_gains_the_lanes_entry_under_its_comment(tmp_path):
    """AC-4.2 — the comment today's installer wrote is not repeated; the missing entry follows it."""
    write_gitignore(tmp_path, "dist/\n\n%s\n.writ/state/\n" % COMMENT)
    assert scaffold(tmp_path).returncode == 0
    assert (tmp_path / ".gitignore").read_text(encoding="utf-8") == (
        "dist/\n\n%s\n.writ/state/\n.writ-lanes-*/\n" % COMMENT)


# --------------------------------------------------------------------------
# scaffold --check
# --------------------------------------------------------------------------

def test_check_on_an_empty_directory_fails_and_writes_nothing(tmp_path):
    """AC-4.3 — `fail`, one `reason: missing` line per path and entry, summary last, exit 1."""
    result = scaffold(tmp_path, "--check")
    lines = result.stdout.splitlines()
    assert result.returncode == 1, result
    assert lines[0] == "fail"
    assert lines[1:-1] == (["reason: missing " + p for p in EXPECTED_PATHS]
                           + ["reason: missing .gitignore entry " + e for e in ENTRIES])
    assert lines[-1] == "scaffold-writ: fail (13 missing)"
    assert tree(tmp_path) == []


def test_check_on_a_complete_tree_passes(tmp_path):
    """AC-4.3 — after a scaffold, `--check` prints `pass` and exits 0."""
    assert scaffold(tmp_path).returncode == 0
    result = scaffold(tmp_path, "--check")
    assert result.returncode == 0, result
    assert result.stdout.splitlines() == ["pass", "scaffold-writ: pass (0 missing)"]


def test_check_names_a_missing_gitignore_entry(tmp_path):
    """AC-4.3 — the tree is complete but one entry is missing: `fail`, that entry named, nothing written."""
    assert scaffold(tmp_path).returncode == 0
    write_gitignore(tmp_path, "%s\n.writ/state/\n" % COMMENT)
    before = (tmp_path / ".gitignore").read_bytes()
    result = scaffold(tmp_path, "--check")
    assert result.returncode == 1, result
    assert result.stdout.splitlines() == [
        "fail", "reason: missing .gitignore entry .writ-lanes-*/", "scaffold-writ: fail (1 missing)"]
    assert (tmp_path / ".gitignore").read_bytes() == before


# --------------------------------------------------------------------------
# The installers' bash mirror
# --------------------------------------------------------------------------

def test_script_paths_are_the_eleven():
    """AC-4.1 — the script's PATHS constant is the eleven-path list, in order."""
    assert list(load_script().PATHS) == EXPECTED_PATHS


@pytest.mark.parametrize("installer", [INSTALL_SH, UPDATE_SH], ids=["install.sh", "update.sh"])
def test_bash_list_matches(installer):
    """AC-4.4 — the `mkdir -p` brace list in init_writ_workspace expands to the script's PATHS."""
    paths = mkdir_paths(bash_function(installer))
    assert len(paths) == len(set(paths)), paths
    assert sorted(paths) == sorted(load_script().PATHS)


def test_installers_share_one_function():
    """AC-4.4 — update.sh carries a byte-identical copy of install.sh's init_writ_workspace."""
    assert bash_function(UPDATE_SH) == bash_function(INSTALL_SH)


@pytest.mark.parametrize("installer", [INSTALL_SH, UPDATE_SH], ids=["install.sh", "update.sh"])
def test_installers_do_not_call_python(installer):
    """AC-4.4 — no installer line outside a comment runs python."""
    for number, line in enumerate(installer.read_text(encoding="utf-8").splitlines(), 1):
        code = line.split("#", 1)[0] if line.lstrip().startswith("#") else line
        assert not re.search(r"\bpython3?\b", code), "%s:%d: %s" % (installer.name, number, line)


@pytest.mark.parametrize("installer", [INSTALL_SH, UPDATE_SH], ids=["install.sh", "update.sh"])
def test_installer_calls_the_function_after_writ_src(installer):
    """AC-4.4 — each installer calls init_writ_workspace once, after WRIT_SRC is set."""
    lines = installer.read_text(encoding="utf-8").splitlines()
    calls = [i for i, l in enumerate(lines) if re.match(r"\s*init_writ_workspace\s*$", l)]
    assert len(calls) == 1, calls
    sets = [i for i, l in enumerate(lines) if re.match(r"\s*WRIT_SRC=\S", l)]
    assert sets and min(sets) < calls[0]


def test_update_dry_run_skips_the_scaffold():
    """AC-4.4 — update.sh's call sits behind the dry-run guard, so `--dry-run` writes nothing."""
    text = UPDATE_SH.read_text(encoding="utf-8")
    assert re.search(r'if \[ "\$DRY_RUN" != true \]; then\n\s+init_writ_workspace\n\s*fi', text)


GITIGNORE_CASES = [
    None,
    "",
    "node_modules/",
    "node_modules/\n",
    "dist/\r\n*.log",
    "dist/\n\n%s\n.writ/state/\n" % COMMENT,
    "a\n%s\nb" % COMMENT,
    ".writ/state\n",
    "  .writ/state/  \n\t.writ-lanes-*\n",
]


@pytest.mark.parametrize("before", GITIGNORE_CASES)
def test_bash_gitignore_matches_script(tmp_path, before):
    """AC-4.4 — install.sh's init_writ_workspace leaves `.gitignore` with the script's bytes."""
    py_dir, sh_dir = tmp_path / "py", tmp_path / "sh"
    py_dir.mkdir()
    sh_dir.mkdir()
    write_gitignore(py_dir, before)
    write_gitignore(sh_dir, before)
    assert scaffold(py_dir).returncode == 0
    program = "set -euo pipefail\n" + bash_function(INSTALL_SH) + "init_writ_workspace\n"
    result = subprocess.run(["bash", "-c", program], cwd=str(sh_dir),
                            capture_output=True, text=True, timeout=60)
    assert result.returncode == 0, result
    assert (sh_dir / ".gitignore").read_bytes() == (py_dir / ".gitignore").read_bytes()
    assert tree(sh_dir) == tree(py_dir)


# --------------------------------------------------------------------------
# /initialize Step 0 and the plugin copy
# --------------------------------------------------------------------------

def test_initialize_step_zero_runs_before_detection():
    """AC-4.4 — `### Step 0: Scaffold .writ/` sits under Overview, directly before Detection Logic."""
    text = INITIALIZE.read_text(encoding="utf-8")
    headings = [l for l in text.splitlines() if l.startswith("#")]
    step0 = headings.index("### Step 0: Scaffold .writ/")
    assert headings[step0 - 1] == "## Overview"
    assert headings[step0 + 1] == "### Detection Logic"
    body = text.split("### Step 0: Scaffold .writ/", 1)[1].split("### Detection Logic", 1)[0]
    assert "python3 scripts/scaffold-writ.py scaffold" in body
    assert "`created`" in body and "`reason:`" in body and "`pass`" in body
    assert "director" in body


def test_initialize_drops_the_installation_sentence():
    """AC-4.4 — "`.writ/` exists from installation" is replaced by the Step 0 sentence."""
    text = INITIALIZE.read_text(encoding="utf-8")
    assert "exists from installation" not in text
    assert "Step 0 creates `.writ/` when it is absent; create docs within `.writ/docs/`." in text


def test_plugin_copy_runs_the_script_from_the_plugin_root():
    """AC-4.4 — the generated plugin command names `${CLAUDE_PLUGIN_ROOT}/scripts/scaffold-writ.py`."""
    text = PLUGIN_INITIALIZE.read_text(encoding="utf-8")
    assert "python3 ${CLAUDE_PLUGIN_ROOT}/scripts/scaffold-writ.py scaffold" in text
    assert "python3 scripts/scaffold-writ.py" not in text
    assert PLUGIN_SCRIPT.read_bytes() == SCRIPT.read_bytes()


# --------------------------------------------------------------------------
# ADR-031, ADR-029, and the issue
# --------------------------------------------------------------------------

def header_fields(text: str) -> List[str]:
    return re.findall(r"^> \*\*([^*]+):\*\*", text, flags=re.M)


def sections(text: str) -> List[str]:
    return [l[3:] for l in text.splitlines() if l.startswith("## ")]


def test_adr_031_has_adr_029_header_fields_and_sections():
    """AC-4.5 — ADR-031 carries every ADR-029 header field and `##` section."""
    adr = ADR_031.read_text(encoding="utf-8")
    base = ADR_029.read_text(encoding="utf-8")
    fields = set(header_fields(adr))
    for field in header_fields(base):
        if field != "Superseded in part by":
            assert field in fields, field
    own = sections(adr)
    for heading in sections(base):
        key = heading.split(":", 1)[0]
        assert any(h.split(":", 1)[0] == key for h in own), heading


def test_adr_031_states_the_two_paths_and_the_shared_name_rule():
    """AC-4.5 — both install paths, the plugin root, the shared-name rule, and the superseded bullet."""
    adr = ADR_031.read_text(encoding="utf-8")
    assert adr.startswith("# ADR-031: Script Location Under Two Install Paths\n")
    assert re.search(r"^> \*\*Status:\*\* (Accepted|Proposed)\b", adr, flags=re.M)
    assert "${CLAUDE_PLUGIN_ROOT}/scripts" in adr
    assert "install.sh" in adr and "`scripts/`" in adr
    assert "--force" in adr
    assert "Scripts install into the project-root `scripts/` folder." in adr
    assert SPEC_PATH.split("/")[-2] in adr


def test_adr_029_is_superseded_in_part_by_adr_031():
    """AC-4.5 — ADR-029's header links ADR-031."""
    header = ADR_029.read_text(encoding="utf-8").split("\n## ", 1)[0]
    assert "> **Superseded in part by:** [ADR-031](adr-031-script-location.md)" in header


def test_issue_is_resolved_by_adr_031():
    """AC-4.5 — `## Resolution` names ADR-031 and spec.md; `spec_ref` is the spec path."""
    text = ISSUE.read_text(encoding="utf-8")
    assert "> **spec_ref:** %s\n" % SPEC_PATH in text
    assert "\n## Resolution\n" in text
    resolution = text.split("\n## Resolution\n", 1)[1]
    assert "adr-031-script-location.md" in resolution
    assert SPEC_PATH.split("/")[-2] in resolution and "spec.md" in resolution
