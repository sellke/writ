#!/usr/bin/env python3
"""Tests for `/ship` opening a PR without asking, recording the verification
ledger, and `/ship --watch` (spec `2026-11-06-ship-watch-and-merge`).

Prose pins and filled-template tests over `commands/ship.md`. A filled
template runs against the real `scripts/verify-ledger.py` or
`scripts/jev-judge.py` in a temp git repo. No test touches GitHub or the
Writ checkout's `.writ/state/`.
"""

from __future__ import annotations

import importlib.util
import os
import re
import subprocess
import sys
from pathlib import Path
from typing import List

import pytest


REPO_ROOT = Path(__file__).resolve().parents[2]
SHIP = REPO_ROOT / "commands" / "ship.md"
COMMAND_BYTE_BUDGET = 24960


def _load(name: str, rel: str):
    spec = importlib.util.spec_from_file_location(name, REPO_ROOT / rel)
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def read(rel: str) -> str:
    return (REPO_ROOT / rel).read_text(encoding="utf-8")


def ship() -> str:
    return SHIP.read_text(encoding="utf-8")


def section(text: str, heading: str) -> str:
    """From the line starting with `heading` to the next heading of the same or a
    higher level (fenced code skipped)."""
    lines = text.splitlines(keepends=True)
    level = len(heading) - len(heading.lstrip("#"))
    start = next(i for i, line in enumerate(lines) if line.startswith(heading))
    out = [lines[start]]
    fenced = False
    for line in lines[start + 1:]:
        if line.lstrip().startswith("```"):
            fenced = not fenced
        if not fenced:
            m = re.match(r"^(#{1,6}) ", line)
            if m and len(m.group(1)) <= level:
                break
        out.append(line)
    return "".join(out)


def flat(text: str) -> str:
    return " ".join(text.split())


def _git(repo: Path, *args: str) -> str:
    env = dict(os.environ, GIT_CONFIG_GLOBAL=os.devnull, GIT_CONFIG_NOSYSTEM="1")
    done = subprocess.run(["git", "-c", "user.name=t", "-c", "user.email=t@t",
                           "-c", "commit.gpgsign=false", *args],
                          cwd=str(repo), env=env, check=True, capture_output=True, text=True)
    return done.stdout.strip()


def _feature_repo(tmp_path: Path) -> Path:
    """main with one file and an origin/main ref; branch feat with one change."""
    repo = tmp_path / "repo"
    repo.mkdir()
    _git(repo, "init", "-q")
    _git(repo, "symbolic-ref", "HEAD", "refs/heads/main")
    (repo / "app.txt").write_text("one\ntwo\n", encoding="utf-8")
    _git(repo, "add", "app.txt")
    _git(repo, "commit", "-q", "-m", "base")
    _git(repo, "update-ref", "refs/remotes/origin/main", "HEAD")
    _git(repo, "checkout", "-q", "-b", "feat")
    (repo / "app.txt").write_text("one\nTWO\n", encoding="utf-8")
    _git(repo, "commit", "-q", "-am", "change")
    return repo


def _script_line(text: str, prefix: str) -> str:
    lines = [line.strip() for line in text.splitlines() if line.strip().startswith(prefix)]
    assert len(lines) == 1, (prefix, lines)
    return lines[0]


def _run_filled(line: str, repo: Path) -> subprocess.CompletedProcess:
    """Run a filled `python3 scripts/<x>.py ...` line from ship.md in `repo`, with
    the Writ checkout's script and this interpreter."""
    m = re.match(r"python3 scripts/([\w-]+\.py)( .*)$", line)
    assert m, line
    command = "%s %s%s" % (sys.executable, REPO_ROOT / "scripts" / m.group(1), m.group(2))
    env = dict(os.environ, GIT_CONFIG_GLOBAL=os.devnull, GIT_CONFIG_NOSYSTEM="1")
    return subprocess.run(["bash", "-c", command], cwd=str(repo), env=env,
                          capture_output=True, text=True, check=False)


def _known_over_budget_comments(rel: str) -> List[str]:
    lines = read("scripts/tests/test_governor_enforcement.py").splitlines()
    entry = re.compile(r'^\s*"%s": \d+,$' % re.escape(rel))
    index = next(i for i, line in enumerate(lines) if entry.match(line))
    comments: List[str] = []
    while index > 0 and lines[index - 1].lstrip().startswith("#"):
        index -= 1
        comments.insert(0, lines[index].strip())
    return comments


# --------------------------------------------------------------------------
# 2026-11-06-ship-watch-and-merge Story 2: `/ship` opens the PR without asking
# and records the ledger.
# --------------------------------------------------------------------------


def test_no_ask_block_before_step_5():
    """AC-2.1 — no AskQuestion( block on the open path before Step 5."""
    text = ship()
    assert "AskQuestion(" not in text[:text.index("### Step 5")]


@pytest.mark.parametrize("gone", [
    "Override?",
    "Save to `.writ/config.md`?",
    "┌",
    "Non-extraction note",
    "`--dry-run` output for Steps 4-5",
    "Detection chain details",
    "Opinionated defaults",
    "Do not restructure git history without explicit approval",
])
def test_open_path_prompts_and_duplicates_are_gone(gone):
    """AC-2.1 — the config-persist offer, the override prompt, the ASCII pipeline,
    the duplicate dry-run block, and the notes that restated other text are cut."""
    assert gone not in ship()


def test_step_1_prints_the_config_lines_and_writes_nothing():
    """AC-2.1 — Step 1 prints the .writ/config.md lines that would skip detection."""
    step1 = flat(section(ship(), "### Step 1"))
    assert "the `.writ/config.md` lines that would skip detection next time" in step1
    assert "Write nothing." in step1
    assert "- **Test Runner:**" in section(ship(), "### Step 1")


def test_decisions_run_the_doubt_rule_and_label_asked_answers():
    """AC-2.2 — every open-path decision writes a record and runs the doubt check;
    an asked answer is labeled."""
    decisions = flat(section(ship(), "### Decisions"))
    assert "python3 scripts/jev-judge.py doubt --record .writ/state/ship/decision-<name>.json" \
        in decisions
    assert "python3 scripts/jev-judge.py doubt-label --id <id> --outcome" in decisions
    assert "as_recommended" in decisions and "overridden" in decisions


@pytest.mark.parametrize("heading,record,site,options,recommended", [
    ("### Step 3", "decision-tests.json", "choice",
     ["Fix and retry", "Ship as a draft PR with the tests-failing label", "Abort"],
     "Fix and retry"),
    ("### Step 4", "decision-plan.json", "plan",
     ["Split as planned", "Ship as a single commit"], "Split as planned"),
    ("**Not on a feature branch:**", "decision-branch.json", "choice",
     ["Create branch `<name>`", "Abort"], "Create branch `<name>`"),
    ("**Uncommitted changes:**", "decision-commit.json", "choice",
     ["Commit now", "Stash changes", "Abort"], "Commit now"),
])
def test_each_decision_names_its_record(heading, record, site, options, recommended):
    """AC-2.2 — each decision names its record file, site, options, and recommended
    option."""
    text = ship()
    if heading.startswith("#"):
        part = section(text, heading)
    else:
        start = text.index(heading)
        part = text[start:text.index("\n**", start + len(heading))]
    part = flat(part)
    assert "`%s`" % record in part
    assert "`site: %s`" % site in part
    for option in options:
        assert '"%s"' % option in part, option
    assert 'recommended "%s"' % recommended in part


def test_untracked_files_carry_no_recommendation():
    """AC-2.2 — uncommitted changes with untracked files: no recommendation, so it asks."""
    text = ship()
    start = text.index("**Uncommitted changes:**")
    part = flat(text[start:text.index("\n**", start + 5)])
    assert "tracked modifications only" in part
    assert "untracked files present: no recommendation, so it asks" in part


def test_step_4_is_reversible_only_for_unpushed_commits():
    """AC-2.3 — presplit_sha saved first; reversible only with no upstream or every
    restructured commit unpushed; otherwise the record is not reversible and asks."""
    step4 = flat(section(ship(), "### Step 4"))
    saved = step4.index("save `presplit_sha` = `git rev-parse HEAD`")
    assert saved < step4.index("`decision-plan.json`")
    assert ("`reversible: true` only when the branch has no upstream or "
            "`git log origin/<branch>..HEAD` lists every commit the plan restructures, "
            "and `presplit_sha` is saved; otherwise `reversible: false`, so it asks") in step4


def test_step_3_saves_the_evidence_of_test_runner_then_eval_command():
    """AC-2.4 — Step 3 runs the Test Runner, then the Eval Command, and saves the
    commands, exits, HEAD, and tree."""
    step3 = flat(section(ship(), "### Step 3"))
    assert step3.index("run the Test Runner") < step3.index("then the `Eval Command`")
    for literal in (".writ/state/ship/branch-<slug>.json", "`git rev-parse HEAD^{tree}`",
                    "`git rev-parse HEAD`", "each command, its exit code"):
        assert literal in step3, literal


def test_step_5_records_only_a_tested_tree():
    """AC-2.4 — Step 5 records after gh pr create only when every exit is 0, re-runs
    the commands first when the trees differ, and never records a failing run."""
    step5 = flat(section(ship(), "### Step 5"))
    assert step5.index("gh pr create") < step5.index("python3 scripts/verify-ledger.py record")
    assert "when every saved exit code is 0" in step5
    assert "When the trees differ, re-run the commands on HEAD, save, then record." in step5
    assert "A non-zero exit is never recorded" in step5


def test_step_5_record_command_filled_writes_a_verified_row(tmp_path):
    """AC-2.4 — the Step 5 record line, filled with a temp repo's values, writes a
    row that verify-ledger.py check reads VERIFIED."""
    repo = _feature_repo(tmp_path)
    line = _script_line(section(ship(), "### Step 5"), "python3 scripts/verify-ledger.py record")
    filled = (line.replace("<n>", "7").replace("<default-branch>", "main")
              .replace("<exit>", "0").replace("<command>", "true"))
    assert "<" not in filled.replace("$(", ""), filled
    done = _run_filled(filled, repo)
    assert done.returncode == 0, done.stdout + done.stderr
    head = _git(repo, "rev-parse", "HEAD")
    check = subprocess.run([sys.executable, str(REPO_ROOT / "scripts" / "verify-ledger.py"),
                            "check", "--pr", "7", "--head", head, "--repo", str(repo)],
                           capture_output=True, text=True, check=False)
    assert check.returncode == 0 and check.stdout.splitlines()[0] == "pass", check.stdout


def test_step_5_record_command_refuses_failing_evidence(tmp_path):
    """AC-2.4 — the same line with a failing exit writes nothing."""
    repo = _feature_repo(tmp_path)
    line = _script_line(section(ship(), "### Step 5"), "python3 scripts/verify-ledger.py record")
    filled = (line.replace("<n>", "7").replace("<default-branch>", "main")
              .replace("<exit>", "1").replace("<command>", "false"))
    done = _run_filled(filled, repo)
    assert done.returncode == 1
    assert not (repo / ".writ" / "state" / "verify-ledger.json").exists()


def test_config_format_documents_eval_command():
    """AC-2.5 — config-format.md has the Eval Command row and example line."""
    text = read(".writ/docs/config-format.md")
    assert ("| `Eval Command` | ship | Command `/ship --test` and `--watch` run after the "
            "Test Runner; its exit code goes into the verification ledger. Absent: the Test "
            "Runner alone. |") in text
    assert "- **Eval Command:** make lint" in text


def test_verify_ledger_callers_cell_names_ship():
    """AC-2.5 — the verify-ledger.py row of agent-cli-contract.md names commands/ship.md."""
    rows = [line for line in read(".writ/docs/agent-cli-contract.md").splitlines()
            if line.startswith("| `verify-ledger.py` |")]
    assert len(rows) == 1
    assert rows[0].strip().strip("|").split("|")[3].strip() == "commands/ship.md"


@pytest.mark.parametrize("value", [
    "scripts/verify-ledger.py record --pr",
    "scripts/jev-judge.py doubt --record",
])
def test_command_structure_pins_the_open_path_calls(value):
    """AC-2.5 — eval-command-structure.py has passing invocation rows for the calls."""
    mod = _load("eval_command_structure_s2", "scripts/eval-command-structure.py")
    rows = [r for r in mod.ROWS if r.file == "commands/ship.md" and r.value == value]
    assert len(rows) == 1 and rows[0].kind == "invocation"
    assert rows[0].was == "check_command_structure"
    ok, _detail = mod.check_row(REPO_ROOT, rows[0])
    assert ok


def test_ship_overage_is_pinned_exactly_with_a_dated_line():
    """AC-2.5 — KNOWN_OVER_BUDGET equals the exact overage, the file stays above the
    budget, and Story 2 left a dated line above the entry."""
    gov = _load("governor_enforcement_s2", "scripts/tests/test_governor_enforcement.py")
    size = len(SHIP.read_bytes())
    assert size > COMMAND_BYTE_BUDGET
    assert gov.KNOWN_OVER_BUDGET["commands/ship.md"] == size - COMMAND_BYTE_BUDGET
    comments = _known_over_budget_comments("commands/ship.md")
    assert any(c.startswith("# 2026-11-06 (2026-11-06-ship-watch-and-merge Story 2): 3947 -> ")
               for c in comments), comments
    assert any("2026-10-20 (2026-10-20-harness-cuts Story 3): 4030 -> 4023;" in c
               for c in comments)
