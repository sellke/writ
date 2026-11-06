#!/usr/bin/env python3
"""Tests for `scripts/zsh-guard.py`, the dev-only PreToolUse hook on Bash.

Retro `.writ/retros/2026-10-30-phase-15.md` F5: about 200 Bash calls in the
Phase 15 run broke on four zsh pitfalls. The guard names each one and its
fix; a quoted or escaped form of the same text must pass, so the false
positive rate stays near zero. Where zsh is installed, the real shell
confirms that each blocked form misbehaves and each passing twin does not.
"""

from __future__ import annotations

import json
import shutil
import subprocess
import sys
from pathlib import Path
from typing import List, Tuple

import pytest

REPO_ROOT = Path(__file__).resolve().parents[2]
GUARD = REPO_ROOT / "scripts" / "zsh-guard.py"

BLOCKED = [
    # (command, rule)
    ("echo =====", "equals-word"),
    ("echo '---'; echo ===== done", "equals-word"),
    ("x=$(echo =====)", "equals-word"),
    ('[ "$a" == b ] && echo same', "equals-word"),
    ("grep -rn x --include=*.py scripts", "option-glob"),
    ("grep -rn x scripts --exclude-dir=node_*", "option-glob"),
    ("rg x --glob=*.md", "option-glob"),
    ('echo "$dir:t"', "name-modifier"),
    ("echo $f:h", "name-modifier"),
    ('printf "%s\\n" "$file:line"', "name-modifier"),
    ('echo "$1:r"', "name-modifier"),
    ("timeout 30 pytest -q", "gnu-timeout"),
    ("cd scripts && timeout 5 python3 x.py", "gnu-timeout"),
    ("FOO=1 timeout 5 make", "gnu-timeout"),
    ("out=$(timeout 5 jev)", "gnu-timeout"),
    ("ls | xargs -n1 echo; timeout 2 true", "gnu-timeout"),
    ("cat <<EOF\nfile $name:t\nEOF", "name-modifier"),
]

PASSING = [
    'echo "====="',
    "echo '====='",
    "echo \\=====",
    "echo =",
    "echo a=====b",
    "git log --format==%H",
    "[ a = b ] || echo differ",
    '[[ "$a" == b ]] && echo same',
    "(( n == 1 )) && echo one",
    "echo $((1 == 1))",
    "grep -rn x '--include=*.py' scripts",
    "grep -rn x --include='*.py' scripts",
    'grep -rn x --include="*.py" scripts',
    "grep -rn x --include=\\*.py scripts",
    "ls scripts/*.py",
    "git log --format=%H -1",
    "pytest --timeout=30 -q",
    'echo "${dir}:t"',
    'echo "${dir:t}"',
    "echo '$dir:t'",
    'echo "\\$dir:t"',
    'echo "$host:8080"',
    'echo "$host:main"',
    "PATH=$PATH:/usr/local/bin",
    'echo "$a:$b"',
    "awk '{print $1\":\"$2}' f",
    "grep -n timeout scripts/app-verify.py",
    'echo "timeout 5"',
    "gtimeout 5 true",
    "python3 -c 'print(\"=====\")'",
    "# ===== timeout 5 $x:t --include=*.py\necho ok",
    "cat <<'EOF'\n=====\ntimeout 5 x\n$name:t\n--include=*.py\nEOF",
    "cat <<EOF\n=====\ntimeout 5\nEOF",
    "sed -n '1,5p' f",
    "noglob grep -rn x --include=*.py .",
]


def run(args: List[str], stdin: str = "") -> subprocess.CompletedProcess:
    return subprocess.run([sys.executable, str(GUARD)] + args, input=stdin,
                          capture_output=True, text=True, check=False)


def payload(command: str, tool: str = "Bash") -> str:
    return json.dumps({"hook_event_name": "PreToolUse", "tool_name": tool,
                       "tool_input": {"command": command}})


def check(command: str) -> Tuple[int, List[str]]:
    proc = run(["--command", command])
    return proc.returncode, proc.stdout.splitlines()


# -- the four rules -----------------------------------------------------------


@pytest.mark.parametrize("command,rule", BLOCKED)
def test_blocked_command_fails_naming_rule_and_fix(command: str, rule: str) -> None:
    code, lines = check(command)
    assert code == 1, lines
    assert lines[0] == "fail"
    reasons = [line for line in lines if line.startswith("reason: ")]
    assert any(line.startswith("reason: %s: " % rule) for line in reasons), reasons
    for line in reasons:
        assert "; " in line and line.split("; ", 1)[1], "reason must name the fix: " + line


@pytest.mark.parametrize("command", PASSING)
def test_quoted_or_safe_form_passes(command: str) -> None:
    code, lines = check(command)
    assert (code, lines) == (0, ["pass", "zsh-guard: pass (0 findings)"]), lines


def test_each_rule_names_its_fix() -> None:
    fixes = {
        "echo =====": "quote it: '====='",
        "grep -rn x --include=*.py scripts": "quote it: '--include=*.py'",
        'echo "$dir:t"': "brace the name: ${dir}:t",
        "timeout 30 pytest": "Bash tool's timeout parameter",
    }
    for command, fix in fixes.items():
        _, lines = check(command)
        assert any(fix in line for line in lines), (command, lines)


def test_one_reason_per_finding_and_count_in_summary() -> None:
    code, lines = check("timeout 5 grep x --include=*.py . && echo ===== \"$d:t\"")
    assert code == 1
    reasons = [line for line in lines if line.startswith("reason: ")]
    assert [r.split(":", 2)[1].strip() for r in reasons] == [
        "gnu-timeout", "option-glob", "equals-word", "name-modifier"]
    assert lines[-1] == "zsh-guard: fail (4 findings)"
    assert lines[1:-1] == reasons


# -- check mode: ADR-029 check shape -------------------------------------------


def test_reads_hook_json_on_stdin_like_the_retro_proof() -> None:
    proc = run([], stdin=payload("grep -rn x --include=*.py scripts"))
    assert proc.returncode == 1
    assert proc.stdout.splitlines()[0] == "fail"
    assert proc.stdout.splitlines()[-1] == "zsh-guard: fail (1 finding)"


def test_clean_hook_json_passes() -> None:
    proc = run([], stdin=payload("grep -rn x --include='*.py' scripts"))
    assert (proc.returncode, proc.stdout) == (0, "pass\nzsh-guard: pass (0 findings)\n")


@pytest.mark.parametrize("stdin", ["not json", "{}", '{"tool_input": {}}',
                                   '{"tool_input": {"command": 5}}'])
def test_unreadable_payload_is_a_usage_error(stdin: str) -> None:
    proc = run([], stdin=stdin)
    assert proc.returncode == 2
    assert proc.stdout == ""
    assert "zsh-guard" in proc.stderr


def test_unknown_flag_is_a_usage_error() -> None:
    proc = run(["--nope"])
    assert proc.returncode == 2 and proc.stdout == ""


# -- hook mode: Claude Code's PreToolUse contract -------------------------------


def test_hook_blocks_with_exit_2_and_the_fix_on_stderr() -> None:
    proc = run(["--hook"], stdin=payload("echo ====="))
    assert proc.returncode == 2
    assert proc.stdout == ""
    err = proc.stderr.splitlines()
    assert err[0] == "fail"
    assert err[-1] == "zsh-guard: fail (1 finding)"
    assert "quote it: '====='" in proc.stderr


def test_hook_allows_a_clean_command_silently() -> None:
    proc = run(["--hook"], stdin=payload('echo "====="'))
    assert (proc.returncode, proc.stdout, proc.stderr) == (0, "", "")


def test_hook_ignores_other_tools() -> None:
    proc = run(["--hook"], stdin=payload("echo =====", tool="Write"))
    assert (proc.returncode, proc.stdout, proc.stderr) == (0, "", "")


def test_hook_never_blocks_on_its_own_input_error() -> None:
    proc = run(["--hook"], stdin="not json")
    assert proc.returncode == 1, "exit 1 is Claude Code's non-blocking error"
    assert "zsh-guard" in proc.stderr


def test_docstring_carries_the_settings_snippet() -> None:
    text = GUARD.read_text(encoding="utf-8")
    assert '"PreToolUse"' in text and '"matcher": "Bash"' in text
    assert 'scripts/zsh-guard.py\\" --hook' in text


# -- the rules agree with real zsh ------------------------------------------------

ZSH = shutil.which("zsh")
# Each blocked form fails or rewrites its own text; each twin prints it intact.
REAL = [
    ("echo =====", "echo '====='", "====="),
    ("echo --include=*.py", "echo '--include=*.py'", "--include=*.py"),
    ('d=/a/b; echo "$d:t"', 'd=/a/b; echo "${d}:t"', "/a/b:t"),
]


@pytest.mark.skipif(ZSH is None, reason="zsh not installed")
@pytest.mark.parametrize("blocked,twin,want", REAL)
def test_real_zsh_breaks_the_blocked_form_and_not_its_twin(
        blocked: str, twin: str, want: str, tmp_path: Path) -> None:
    def zsh(command: str) -> subprocess.CompletedProcess:
        return subprocess.run([ZSH, "-f", "-c", command], cwd=str(tmp_path),
                              capture_output=True, text=True, check=False)
    bad, good = zsh(blocked), zsh(twin)
    assert bad.returncode != 0 or bad.stdout.strip() != want, bad
    assert (good.returncode, good.stdout.strip()) == (0, want), good
    assert check(blocked)[0] == 1 and check(twin)[0] == 0
