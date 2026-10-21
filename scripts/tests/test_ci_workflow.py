#!/usr/bin/env python3
"""CI workflow test (Story 1 of `2026-10-20-ci-and-update-integrity`).

Reads `.github/workflows/eval.yml` as text (Python 3.9 stdlib, no YAML
parser) and checks that CI runs every suite:

    AC-1.1  The workflow triggers on `pull_request` and `push`, keeps the
            checkout, SKILL.md check, eval, and upload steps, installs uv
            with `astral-sh/setup-uv@v<N>`, and runs
            `uv run --python 3.9 pytest` as its own step.
    AC-1.2  The bash-tests step's `run:` block, executed with `bash -e` the
            way GitHub Actions runs it on Linux (`bash -e {0}`, no
            pipefail), runs every `scripts/tests/test_*.sh`, prints
            `FAIL <path>` per failing test, and exits non-zero when any
            test fails. With only passing tests, or none, it exits 0.
    AC-1.3  The job runs on `ubuntu-latest`, and the comment above
            `runs-on` records the BSD-only scan and the Linux run.
    AC-1.4  CI runs eval.sh, pytest on Python 3.9, and the bash-test loop,
            and the pytest step collects this file.

The parser below handles only the YAML shapes this workflow uses: a
top-level `on:` key, `- uses:` / `run:` step keys, and literal `run: |`
blocks.
"""

from __future__ import annotations

import re
import subprocess
from pathlib import Path
from typing import List, Optional

REPO_ROOT = Path(__file__).resolve().parents[2]
WORKFLOW = REPO_ROOT / ".github" / "workflows" / "eval.yml"

BASH_TEST_GLOB = "scripts/tests/test_*.sh"

STEP_START = re.compile(r"^(\s*)- ")
RUN_KEY = re.compile(r"^(\s*)(?:- )?run:\s*(.*?)\s*$")


def workflow_lines() -> List[str]:
    return WORKFLOW.read_text(encoding="utf-8").splitlines()


def indent_of(line: str) -> int:
    return len(line) - len(line.lstrip(" "))


def trigger_names(lines: List[str]) -> List[str]:
    """Return the event names under the top-level `on:` key."""
    for index, line in enumerate(lines):
        match = re.match(r"^[\"']?on[\"']?:\s*(.*?)\s*$", line)
        if not match:
            continue
        inline = match.group(1)
        if inline:
            # `on: push` or `on: [push, pull_request]`
            return re.findall(r"[A-Za-z_]+", inline)
        names = []
        child_indent = None
        for child in lines[index + 1:]:
            if not child.strip() or child.lstrip().startswith("#"):
                continue
            if indent_of(child) == 0:
                break
            if child_indent is None:
                child_indent = indent_of(child)
            if indent_of(child) == child_indent:
                key = re.match(r"^\s*([A-Za-z_]+):", child)
                if key:
                    names.append(key.group(1))
        return names
    return []


def step_blocks(lines: List[str]) -> List[List[str]]:
    """Split the `steps:` list into one list of lines per step."""
    steps_index = next(
        (i for i, line in enumerate(lines) if line.strip() == "steps:"), None)
    assert steps_index is not None, "eval.yml has no steps: key"
    steps_indent = indent_of(lines[steps_index])
    steps = []
    item_indent = None
    for line in lines[steps_index + 1:]:
        if line.strip() and indent_of(line) <= steps_indent:
            break
        start = STEP_START.match(line)
        if start and (item_indent is None or len(start.group(1)) == item_indent):
            item_indent = len(start.group(1))
            steps.append([line])
        elif steps:
            steps[-1].append(line)
    return steps


def run_command(step: List[str]) -> Optional[str]:
    """Return a step's `run:` value: the single-line value, or the dedented
    text of a literal `run: |` block."""
    for index, line in enumerate(step):
        match = RUN_KEY.match(line)
        if not match:
            continue
        key_indent = len(match.group(1)) + (2 if line.lstrip().startswith("- ") else 0)
        value = match.group(2)
        if not value.startswith("|"):
            return value
        body = []
        for child in step[index + 1:]:
            if child.strip() and indent_of(child) <= key_indent:
                break
            body.append(child)
        while body and not body[-1].strip():
            body.pop()
        content = [child for child in body if child.strip()]
        if not content:
            return ""
        block_indent = indent_of(content[0])
        return "\n".join(child[block_indent:] for child in body) + "\n"
    return None


def uses_value(step: List[str]) -> Optional[str]:
    for line in step:
        match = re.match(r"^\s*(?:- )?uses:\s*(\S+)", line)
        if match:
            return match.group(1)
    return None


def has_key(step: List[str], pattern: str) -> bool:
    return any(re.match(r"^\s*(?:- )?" + pattern, line) for line in step)


def bash_test_step(steps: List[List[str]]) -> List[str]:
    loop = re.compile(r"^\s*for\s+\w+\s+in\s+" + re.escape(BASH_TEST_GLOB) + r"\s*;?")
    for step in steps:
        command = run_command(step)
        if command and any(loop.match(line) for line in command.splitlines()):
            return step
    raise AssertionError(f"no step's run: block iterates {BASH_TEST_GLOB}")


def run_bash_block(tmp_path: Path, fixtures: dict) -> subprocess.CompletedProcess:
    """Write the fixtures into tmp_path/repo/scripts/tests/ and run the
    extracted bash-tests block from tmp_path/repo with `bash -e`."""
    block = run_command(bash_test_step(step_blocks(workflow_lines())))
    repo = tmp_path / "repo"
    tests = repo / "scripts" / "tests"
    tests.mkdir(parents=True)
    for name, body in fixtures.items():
        (tests / name).write_text(body, encoding="utf-8")
    script = tmp_path / "step.sh"
    script.write_text(block, encoding="utf-8")
    return subprocess.run(
        ["bash", "-e", str(script)], cwd=repo, capture_output=True,
        text=True, timeout=60)


PASSING = "echo 'ran {name}'\nexit 0\n"
FAILING = "echo 'ran {name}'\nexit 1\n"


# --- AC-1.1: workflow shape -------------------------------------------------

def test_triggers_on_pull_request_and_push() -> None:
    """AC-1.1: `on:` names both `pull_request` and `push`."""
    names = trigger_names(workflow_lines())
    assert "pull_request" in names, names
    assert "push" in names, names


def test_existing_steps_kept() -> None:
    """AC-1.1: checkout, SKILL.md check, eval, and upload steps stay."""
    steps = step_blocks(workflow_lines())
    commands = [run_command(step) or "" for step in steps]
    assert any("bash scripts/gen-skill.sh --check" in c for c in commands), commands
    assert any("bash scripts/eval.sh" in c for c in commands), commands

    checkout = [s for s in steps if (uses_value(s) or "").startswith("actions/checkout@")]
    assert checkout, "checkout step missing"
    assert has_key(checkout[0], r"fetch-depth:\s*0\s*$"), checkout[0]

    upload = [s for s in steps if (uses_value(s) or "").startswith("actions/upload-artifact@")]
    assert upload, "upload step missing"
    assert has_key(upload[0], r"if:\s*failure\(\)\s*$"), upload[0]


def test_setup_uv_pinned_to_major_tag_before_pytest_step() -> None:
    """AC-1.1: `uses: astral-sh/setup-uv@v<N>` precedes the pytest step."""
    steps = step_blocks(workflow_lines())
    uv_steps = [i for i, s in enumerate(steps)
                if (uses_value(s) or "").startswith("astral-sh/setup-uv@")]
    assert uv_steps, "no astral-sh/setup-uv step"
    pin = uses_value(steps[uv_steps[0]])
    assert re.fullmatch(r"astral-sh/setup-uv@v\d+", pin or ""), pin

    pytest_steps = [i for i, s in enumerate(steps)
                    if (run_command(s) or "").strip().startswith("uv run --python 3.9 pytest")]
    assert pytest_steps, "no step runs `uv run --python 3.9 pytest`"
    assert uv_steps[0] < pytest_steps[0], (uv_steps, pytest_steps)


def test_pytest_runs_as_its_own_step() -> None:
    """AC-1.1: the pytest step is not the bash-tests step."""
    steps = step_blocks(workflow_lines())
    pytest_steps = [s for s in steps
                    if (run_command(s) or "").strip().startswith("uv run --python 3.9 pytest")]
    assert pytest_steps, "no step runs `uv run --python 3.9 pytest`"
    assert BASH_TEST_GLOB not in (run_command(pytest_steps[0]) or "")


def test_bash_step_iterates_test_glob() -> None:
    """AC-1.2: a step's `run: |` block loops over scripts/tests/test_*.sh."""
    step = bash_test_step(step_blocks(workflow_lines()))
    assert BASH_TEST_GLOB in (run_command(step) or "")


# --- AC-1.2: the bash-tests block, executed ---------------------------------

def test_bash_block_fails_on_red_and_runs_every_test(tmp_path: Path) -> None:
    """AC-1.2: one failing test makes the block exit non-zero, prints
    `FAIL scripts/tests/test_fail.sh`, and the passing test still runs.
    The glob sorts test_fail.sh first, so this also proves `bash -e` does
    not stop the loop at the first failure."""
    result = run_bash_block(tmp_path, {
        "test_pass.sh": PASSING.format(name="test_pass.sh"),
        "test_fail.sh": FAILING.format(name="test_fail.sh"),
    })
    output = result.stdout + result.stderr
    assert result.returncode != 0, output
    assert "FAIL scripts/tests/test_fail.sh" in output, output
    assert "FAIL scripts/tests/test_pass.sh" not in output, output
    assert "ran test_fail.sh" in output, output
    assert "ran test_pass.sh" in output, output


def test_bash_block_reports_each_failure(tmp_path: Path) -> None:
    """AC-1.2: several failing tests give one FAIL line each."""
    result = run_bash_block(tmp_path, {
        "test_a.sh": FAILING.format(name="test_a.sh"),
        "test_b.sh": PASSING.format(name="test_b.sh"),
        "test_c.sh": FAILING.format(name="test_c.sh"),
    })
    output = result.stdout + result.stderr
    assert result.returncode != 0, output
    assert "FAIL scripts/tests/test_a.sh" in output, output
    assert "FAIL scripts/tests/test_c.sh" in output, output
    assert output.count("FAIL scripts/tests/") == 2, output
    assert "ran test_b.sh" in output, output


def test_bash_block_passes_on_green(tmp_path: Path) -> None:
    """AC-1.2: only passing tests: exit 0 and no FAIL line."""
    result = run_bash_block(tmp_path, {
        "test_one.sh": PASSING.format(name="test_one.sh"),
        "test_two.sh": PASSING.format(name="test_two.sh"),
    })
    output = result.stdout + result.stderr
    assert result.returncode == 0, output
    assert "FAIL" not in output, output
    assert "ran test_one.sh" in output, output
    assert "ran test_two.sh" in output, output


def test_bash_block_with_no_tests_exits_zero(tmp_path: Path) -> None:
    """AC-1.2 nil case: no test_*.sh files means zero tests and exit 0, with
    no FAIL line for the unexpanded glob."""
    result = run_bash_block(tmp_path, {"helper.sh": FAILING.format(name="helper.sh")})
    output = result.stdout + result.stderr
    assert result.returncode == 0, output
    assert "FAIL" not in output, output
    assert "ran helper.sh" not in output, output


# --- AC-1.3 / AC-1.4: runner evidence and the Python 3.9 run ----------------

def runs_on_and_comment(lines: List[str]) -> tuple:
    """Return the `runs-on:` value and the comment lines directly above it,
    joined with spaces."""
    index = next((i for i, line in enumerate(lines) if re.match(r"^\s*runs-on:", line)), None)
    assert index is not None, "eval.yml has no runs-on: key"
    comment: List[str] = []
    for line in reversed(lines[:index]):
        if not line.lstrip().startswith("#"):
            break
        comment.insert(0, line.strip().lstrip("#").strip())
    return lines[index].split(":", 1)[1].strip(), " ".join(comment)


def test_runner_choice_records_its_evidence_above_runs_on() -> None:
    """AC-1.3: the job runs on `ubuntu-latest`, and the comment directly
    above `runs-on` records the scan for BSD-only calls and the Linux run
    of the bash tests."""
    runner, comment = runs_on_and_comment(workflow_lines())
    assert runner == "ubuntu-latest", runner
    assert "BSD-only calls" in comment, comment
    assert re.search(r"ran \d+ tests with 0 failures", comment), comment


def test_ci_runs_all_three_suites_and_this_file_on_python_3_9() -> None:
    """AC-1.4: the workflow runs eval.sh, `uv run --python 3.9 pytest`, and
    the bash-test loop. The pytest step collects this file on the 3.9 floor:
    pyproject.toml declares `requires-python = ">=3.9"` and its testpaths
    hold scripts/tests, where this file lives."""
    steps = step_blocks(workflow_lines())
    commands = [(run_command(step) or "").strip() for step in steps]
    assert any(c.startswith("bash scripts/eval.sh") for c in commands), commands
    assert any(c.startswith("uv run --python 3.9 pytest") for c in commands), commands
    bash_test_step(steps)

    pyproject = (REPO_ROOT / "pyproject.toml").read_text(encoding="utf-8")
    assert re.search(r'^requires-python\s*=\s*">=3\.9"\s*$', pyproject, re.M), pyproject
    testpaths = re.search(r"^testpaths\s*=\s*\[(.*?)\]\s*$", pyproject, re.M)
    assert testpaths is not None, pyproject
    assert '"scripts/tests"' in testpaths.group(1), testpaths.group(1)
    assert Path(__file__).resolve().parent == REPO_ROOT / "scripts" / "tests"
