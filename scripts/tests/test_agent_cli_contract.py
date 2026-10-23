#!/usr/bin/env python3
"""Agent CLI contract test (Story 3 of `2026-10-12-agent-cli-contract`).

Checks every script Writ ships against `.writ/docs/agent-cli-contract.md`.
The shipped set comes from running the real `is_shippable_script` function
out of `scripts/install.sh` over `scripts/*` (Business Rule 1); this file
keeps no list of its own. The Classification table in the contract doc
gives each script's shape (data or check) and allowances.

Rule keys and where each rule comes from (spec.md -> Business Rules
(Expanded), unless noted):

    table         Business Rules 1-2: every shipped script has exactly one
                  well-formed row, and every row is a shipped script.
    help          ADR-029 rule 7 (document subcommands in --help); the
                  technical spec's `test_help`. Python: `--help` exits 0.
                  Shell: `--help` prints a usage line naming the script.
    bad_flag      Business Rule 5: `--zz-contract-probe` exits non-zero
                  with stdout empty or one JSON object with `blocker`.
    network       Business Rule 8: network imports only under
                  `network: opt-in`. Python only (ast import scan).
    agent_launch  Business Rule 6: no launch call whose target is an agent
                  CLI. Python only (ast call scan).
    bounded_wait  Business Rule 7: `time.sleep` or `while True` only under
                  `bounded-wait`. Python only (ast scan).
    shape         Business Rules 3-4: a SMOKE_INVOCATIONS run prints the
                  row's shape (data: one JSON value; check: verdict alone on
                  line 1, `<tool>...` summary last).
    exit_code     Business Rule 4: a check run's exit code matches its
                  line-1 verdict: 0 when the check ran (pass or
                  unverifiable), 1 for fail. Exit 2 is reserved for usage
                  errors or a tool that could not start, which no smoke
                  invocation triggers. When line 1 is not a verdict, `shape`
                  owns the failure and this rule does not apply.

Data tools are not held to "non-zero exit requires `blocker`": a non-zero
exit may carry a verdict-bearing JSON document (ac-trace exit 1 with
findings, exit-criteria exit 2). `blocker` is required only when the tool
could not do its job, which per-script tests own.

Shell scripts get only the table, help, and bad-flag rule checks (the ast
scans are Python-only); they also appear in the shape smoke, which is how
Story 5's shell fixes are enforced.

KNOWN_VIOLATIONS is strict debt (Business Rule 10): each `(script, rule)`
entry makes that case `xfail(strict=True)`; for a smoke run in a further
mode, the key is `<script> <mode>`. When the script is fixed the
case XPASSes, and strict mode fails it until the entry is removed. Stories 4
and 5 emptied the dict; the fixture tests below keep the mechanism proven.

Run: uv run pytest scripts/tests/test_agent_cli_contract.py
"""

from __future__ import annotations

import ast
import collections
import json
import os
import re
import shutil
import subprocess
import sys
from pathlib import Path
from typing import Dict, Iterable, List, Optional, Sequence, Tuple

import pytest

REPO_ROOT = Path(__file__).resolve().parents[2]
SCRIPTS = REPO_ROOT / "scripts"
TESTS_DIR = Path(__file__).resolve().parent
INSTALL_SH = SCRIPTS / "install.sh"
DOC_REL = ".writ/docs/agent-cli-contract.md"
DOC = REPO_ROOT / DOC_REL

SHIP_FILTER_ERROR = "cannot load is_shippable_script from scripts/install.sh"
TABLE_ERROR = "no classification table in %s" % DOC_REL
TABLE_HEADER = ["Script", "Shape", "Allowances", "Callers"]
SHAPES = ("data", "check")
ALLOWANCES = ("network: opt-in", "bounded-wait")
VERDICT_EXIT = {"pass": 0, "fail": 1, "unverifiable": 0}

RULE_REFS = {
    "table": "Business Rules 1-2",
    "help": "ADR-029 rule 7",
    "bad_flag": "Business Rule 5",
    "network": "Business Rule 8",
    "agent_launch": "Business Rule 6",
    "bounded_wait": "Business Rule 7",
    "shape": "Business Rules 3-4",
    "exit_code": "Business Rule 4",
}
STATIC_RULES = ("network", "agent_launch", "bounded_wait")

# ast scan targets. `urllib.parse` is exempt: it splits URLs, opens nothing.
NETWORK_MODULES = ("urllib.request", "urllib.error", "http.client", "socket", "requests")
AGENT_CLIS = ("claude", "codex", "cursor-agent", "gemini", "openclaw")
LAUNCH_NAMES = ("run", "call", "check_call", "check_output", "Popen", "system", "popen",
                "create_subprocess_exec", "create_subprocess_shell")
LAUNCH_PREFIXES = ("exec", "spawn", "posix_spawn")
SLEEP_REFS = ("time.sleep", "asyncio.sleep")

RUN_TIMEOUT = 120

Row = collections.namedtuple("Row", "shape allowances")
NO_ALLOWANCES = Row("data", frozenset())


# --------------------------------------------------------------------------
# Shipped set and Classification table
# --------------------------------------------------------------------------

def load_ship_filter(install_text: str) -> str:
    """The `is_shippable_script` function text, extracted (never sourced whole)."""
    match = re.search(r"^is_shippable_script\(\) \{\n.*?^\}\n", install_text, re.M | re.S)
    if match is None:
        raise AssertionError(SHIP_FILTER_ERROR)
    return match.group(0)


def shipped_scripts(install_text: str, names: Iterable[str]) -> List[str]:
    """Run the ship filter over `names`; keep the *.py/*.sh files it accepts."""
    script = load_ship_filter(install_text) + (
        'for f in "$@"; do if is_shippable_script "$f"; then echo "$f"; fi; done\n')
    result = subprocess.run(["bash", "-c", script, "bash"] + sorted(names),
                            capture_output=True, text=True)
    if result.returncode != 0:
        raise AssertionError("%s (bash exited %d: %s)"
                             % (SHIP_FILTER_ERROR, result.returncode, result.stderr.strip()))
    return sorted(n for n in result.stdout.split() if n.endswith((".py", ".sh")))


def _split_row(line: str) -> List[str]:
    return [cell.strip() for cell in line.strip().strip("|").split("|")]


def parse_classification(doc_text: str) -> Dict[str, Row]:
    """First table under `## Classification`: script -> Row(shape, allowances)."""
    match = re.search(r"^## Classification\n(.*?)(?=^## |\Z)", doc_text, re.M | re.S)
    lines = match.group(1).splitlines() if match else []
    start = next((i for i, line in enumerate(lines) if line.startswith("|")), None)
    if start is None or _split_row(lines[start]) != TABLE_HEADER:
        raise AssertionError(TABLE_ERROR)
    rows: Dict[str, Row] = {}
    for line in lines[start + 2:]:
        if not line.startswith("|"):
            break
        cells = _split_row(line)
        allow = frozenset(a.strip() for a in cells[2].split(",") if a.strip())
        rows[cells[0].strip("`")] = Row(cells[1], allow)
    return rows


def table_problems(shipped: Iterable[str], table: Dict[str, Row]) -> List[str]:
    """Table completeness both ways, plus the Shape and Allowances vocabularies."""
    shipped = set(shipped)
    problems = []
    for name in sorted(shipped - set(table)):
        problems.append("%s is shipped but has no row in %s [rule table, %s]; add a row"
                        % (name, DOC_REL, RULE_REFS["table"]))
    for name in sorted(set(table) - shipped):
        problems.append("%s has a row in %s but is not shipped [rule table, %s]; "
                        "remove the row" % (name, DOC_REL, RULE_REFS["table"]))
    for name in sorted(set(table) & shipped):
        row = table[name]
        bad = sorted(row.allowances - set(ALLOWANCES))
        if row.shape not in SHAPES or bad:
            problems.append("%s has shape %r and allowances %r in %s [rule table, %s]; "
                            "use shape data or check and allowances from %s"
                            % (name, row.shape, bad, DOC_REL, RULE_REFS["table"],
                               ", ".join(ALLOWANCES)))
    return problems


def rules_for(script: str) -> Tuple[str, ...]:
    """Per-script rule checks: shell scripts get table, help, and bad flag only."""
    base = ("table", "help", "bad_flag")
    return base if script.endswith(".sh") else base + STATIC_RULES


def fail_msg(script: str, rule: str, detail: str, fix: str) -> str:
    """Every failure starts with the script and ends with the fix."""
    return "%s: %s [rule %s, %s]; fix: %s" % (script, detail, rule, RULE_REFS[rule], fix)


# --------------------------------------------------------------------------
# Running scripts
# --------------------------------------------------------------------------

def script_env() -> Dict[str, str]:
    """Deterministic env: no WRIT_* switches, no bytecode written next to scripts."""
    env = {k: v for k, v in os.environ.items() if not k.startswith("WRIT_")}
    env["PYTHONDONTWRITEBYTECODE"] = "1"
    return env


def run_script(path: Path, args: Sequence[str], cwd: Path) -> subprocess.CompletedProcess:
    runner = ["bash"] if path.suffix == ".sh" else [sys.executable]
    return subprocess.run(runner + [str(path)] + list(args), cwd=str(cwd), env=script_env(),
                          capture_output=True, text=True, timeout=RUN_TIMEOUT)


def _tail(text: str, lines: int = 3) -> str:
    return " | ".join(text.strip().splitlines()[-lines:])


def check_help(script: str, path: Path, cwd: Path) -> Optional[str]:
    """Python: `--help` exits 0. Shell: `--help` prints a usage line naming the script."""
    result = run_script(path, ["--help"], cwd)
    if path.suffix == ".sh":
        usage = re.compile(r"usage:.*%s" % re.escape(script), re.I)
        if any(usage.search(line) for line in (result.stdout + result.stderr).splitlines()):
            return None
        return fail_msg(script, "help", "--help printed no usage line naming %s (exit %d: %s)"
                        % (script, result.returncode, _tail(result.stdout + result.stderr)),
                        "handle --help by printing a `Usage: ... %s ...` line" % script)
    if result.returncode == 0:
        return None
    return fail_msg(script, "help", "--help exited %d (stderr: %s)"
                    % (result.returncode, _tail(result.stderr)),
                    "make --help print usage and exit 0 (argparse does this)")


def _is_blocker_object(stdout: str) -> bool:
    try:
        value = json.loads(stdout)
    except ValueError:
        return False
    return isinstance(value, dict) and "blocker" in value


def check_bad_flag(script: str, path: Path, cwd: Path) -> Optional[str]:
    """`--zz-contract-probe`: non-zero exit; stdout empty or one JSON `blocker` object."""
    result = run_script(path, ["--zz-contract-probe"], cwd)
    if result.returncode != 0 and (not result.stdout.strip() or _is_blocker_object(result.stdout)):
        return None
    if result.returncode == 0:
        detail = "--zz-contract-probe exited 0"
    else:
        detail = "--zz-contract-probe printed to stdout: %r" % result.stdout.strip()[:80]
    return fail_msg(script, "bad_flag", detail,
                    "reject unknown flags with a non-zero exit and usage on stderr, leaving "
                    "stdout empty (argparse's default) or printing one JSON `blocker` object")


# --------------------------------------------------------------------------
# Static (ast) scans — Python only. Import and call nodes, never string text.
# --------------------------------------------------------------------------

def _dotted(node: ast.AST) -> str:
    if isinstance(node, ast.Name):
        return node.id
    if isinstance(node, ast.Attribute):
        base = _dotted(node.value)
        return base + "." + node.attr if base else node.attr
    return ""


def _parse(script: str, path: Path, rule: str) -> Tuple[Optional[ast.AST], Optional[str]]:
    try:
        return ast.parse(path.read_text(encoding="utf-8"), filename=str(path)), None
    except SyntaxError as exc:
        return None, fail_msg(script, rule, "does not parse on Python %d.%d (line %s: %s)"
                              % (sys.version_info[0], sys.version_info[1], exc.lineno, exc.msg),
                              "use syntax that runs on the Python 3.9 floor")


def _is_network(module: str) -> bool:
    return any(module == m or module.startswith(m + ".") for m in NETWORK_MODULES)


def network_imports(tree: ast.AST) -> List[Tuple[int, str]]:
    """(line, module) for each import of a network module, incl. literal __import__."""
    found = []
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            found += [(node.lineno, a.name) for a in node.names if _is_network(a.name)]
        elif isinstance(node, ast.ImportFrom) and node.module and not node.level:
            if _is_network(node.module):
                found.append((node.lineno, node.module))
            else:
                found += [(node.lineno, node.module + "." + a.name) for a in node.names
                          if _is_network(node.module + "." + a.name)]
        elif (isinstance(node, ast.Call)
              and _dotted(node.func) in ("__import__", "importlib.import_module", "import_module")
              and node.args and isinstance(node.args[0], ast.Constant)
              and isinstance(node.args[0].value, str) and _is_network(node.args[0].value)):
            found.append((node.lineno, node.args[0].value))
    return found


def _launch_target(node: ast.AST) -> Optional[str]:
    """The program a launch call's first argument names, when it is a literal."""
    if isinstance(node, (ast.List, ast.Tuple)) and node.elts:
        node = node.elts[0]
        if (isinstance(node, ast.Call) and _dotted(node.func).endswith("which")
                and node.args):
            node = node.args[0]
    if isinstance(node, ast.Constant) and isinstance(node.value, str) and node.value.strip():
        return os.path.basename(node.value.split()[0])
    return None


def agent_launches(tree: ast.AST) -> List[Tuple[int, str]]:
    """(line, cli) for subprocess/os.exec/Popen-style calls whose target is an agent CLI."""
    found = []
    for node in ast.walk(tree):
        if not isinstance(node, ast.Call):
            continue
        name = _dotted(node.func).rsplit(".", 1)[-1]
        if name not in LAUNCH_NAMES and not name.startswith(LAUNCH_PREFIXES):
            continue
        first = node.args[0] if node.args else next(
            (k.value for k in node.keywords if k.arg in ("args", "file", "path")), None)
        target = _launch_target(first) if first is not None else None
        if target in AGENT_CLIS:
            found.append((node.lineno, target))
    return found


def waits(tree: ast.AST) -> List[Tuple[int, str]]:
    """(line, what) for each sleep reference or import and each `while True` loop."""
    found = []
    for node in ast.walk(tree):
        if isinstance(node, ast.Attribute) and _dotted(node) in SLEEP_REFS:
            found.append((node.lineno, _dotted(node)))
        elif (isinstance(node, ast.ImportFrom) and node.module in ("time", "asyncio")
              and any(a.name == "sleep" for a in node.names)):
            found.append((node.lineno, "%s.sleep" % node.module))
        elif (isinstance(node, ast.While) and isinstance(node.test, ast.Constant)
              and node.test.value is not False and node.test.value in (True, 1)):
            found.append((node.lineno, "while True"))
    return sorted(found)


def _where(found: List[Tuple[int, str]]) -> str:
    return ", ".join("%s at line %d" % (what, line) for line, what in found)


def check_network(script: str, path: Path, row: Row) -> Optional[str]:
    tree, error = _parse(script, path, "network")
    if error:
        return error
    found = network_imports(tree)
    if not found or "network: opt-in" in row.allowances:
        return None
    return fail_msg(script, "network", "imports %s without `network: opt-in`" % _where(found),
                    "mark `network: opt-in` in the %s row and document the opt-in, "
                    "or drop the import" % script)


def check_agent_launch(script: str, path: Path, row: Row) -> Optional[str]:
    tree, error = _parse(script, path, "agent_launch")
    if error:
        return error
    found = agent_launches(tree)
    if not found:
        return None
    return fail_msg(script, "agent_launch", "launches agent CLI %s" % _where(found),
                    "remove the launch; spawning agents is the harness's job")


def check_bounded_wait(script: str, path: Path, row: Row) -> Optional[str]:
    tree, error = _parse(script, path, "bounded_wait")
    if error:
        return error
    found = waits(tree)
    if not found or "bounded-wait" in row.allowances:
        return None
    return fail_msg(script, "bounded_wait", "has %s without `bounded-wait`" % _where(found),
                    "put the bound in the loop (`for` or `while <condition>`), or mark "
                    "`bounded-wait` in the %s row and enforce a timeout" % script)


STATIC_CHECKS = {
    "network": check_network,
    "agent_launch": check_agent_launch,
    "bounded_wait": check_bounded_wait,
}


# --------------------------------------------------------------------------
# Shape checks on a finished run
# --------------------------------------------------------------------------

def check_shape(script: str, shape: str, args: Sequence[str],
                result: subprocess.CompletedProcess) -> Optional[str]:
    """Data: stdout is one JSON value. Check: verdict alone on line 1, summary last."""
    shown = " ".join([script] + [str(a) for a in args])
    out = result.stdout
    if shape == "data" or "--json" in args:
        try:
            json.loads(out)
            return None
        except ValueError:
            return fail_msg(script, "shape", "`%s` stdout is not one JSON value (exit %d, "
                            "starts %r)" % (shown, result.returncode, out.strip()[:60]),
                            "print one JSON document by default and put text behind --pretty")
    lines = out.splitlines()
    stem = re.sub(r"\.(py|sh)$", "", script)
    fix = ("print the verdict alone on line 1 and a `%s: <verdict> (...)` summary last"
           % stem)
    if not lines or lines[0] not in VERDICT_EXIT:
        return fail_msg(script, "shape", "`%s` line 1 is %r, not pass/fail/unverifiable "
                        "(exit %d)" % (shown, lines[0][:60] if lines else "", result.returncode),
                        fix)
    if len(lines) < 2 or not lines[-1].startswith(stem):
        return fail_msg(script, "shape", "`%s` last line is %r, not a summary starting %r"
                        % (shown, lines[-1][:60], stem), fix)
    return None


def check_exit_code(script: str, args: Sequence[str],
                    result: subprocess.CompletedProcess) -> Optional[str]:
    """A check run's exit code matches its line-1 verdict. No verdict: `shape` owns it."""
    lines = result.stdout.splitlines()
    verdict = lines[0] if lines else ""
    if verdict not in VERDICT_EXIT or result.returncode == VERDICT_EXIT[verdict]:
        return None
    shown = " ".join([script] + [str(a) for a in args])
    return fail_msg(script, "exit_code", "`%s` printed %r but exited %d"
                    % (shown, verdict, result.returncode),
                    "exit 0 when the check ran (pass or unverifiable), 1 for fail, "
                    "2 only for usage or could-not-start")


# --------------------------------------------------------------------------
# KNOWN_VIOLATIONS -> strict xfail marks
# --------------------------------------------------------------------------

def xfail_reason(script: str, rule: str, reason: str) -> str:
    return ("%s: known violation of rule %s (%s): %s; fix: remove (%r, %r) from "
            "KNOWN_VIOLATIONS once it passes" % (script, rule, RULE_REFS[rule], reason,
                                                  script, rule))


def cases(rule: str, scripts: Iterable[str],
          known: Optional[Dict[Tuple[str, str], str]] = None) -> list:
    """pytest params for `rule`; listed (script, rule) pairs get xfail(strict=True)."""
    known = KNOWN_VIOLATIONS if known is None else known
    params = []
    for script in scripts:
        marks = []
        if (script, rule) in known:
            marks.append(pytest.mark.xfail(
                strict=True, reason=xfail_reason(script, rule, known[(script, rule)])))
        params.append(pytest.param(script, id=script, marks=marks))
    return params


# --------------------------------------------------------------------------
# Real-repo data
# --------------------------------------------------------------------------

def _read(path: Path) -> str:
    return path.read_text(encoding="utf-8")


SHIPPED = shipped_scripts(_read(INSTALL_SH), [p.name for p in SCRIPTS.iterdir() if p.is_file()])
TABLE = parse_classification(_read(DOC))
PY_SHIPPED = [s for s in SHIPPED if set(STATIC_RULES) <= set(rules_for(s))]

# (script, rule) -> reason. Strict debt: empty since Story 5 of this spec; a
# new entry needs a reason and a story that removes it.
KNOWN_VIOLATIONS: Dict[Tuple[str, str], str] = {}


def _spec_dir() -> Path:
    """This spec's folder, active or archived, so the smoke survives archival."""
    name = "2026-10-12-agent-cli-contract"
    for base in (REPO_ROOT / ".writ" / "specs", REPO_ROOT / ".writ" / "specs" / "archive"):
        if (base / name).is_dir():
            return base / name
    return REPO_ROOT / ".writ" / "specs" / name


SPEC_DIR = _spec_dir()
SPEC = "{repo}/" + SPEC_DIR.relative_to(REPO_ROOT).as_posix()
STORY = SPEC + "/user-stories/story-1-contract-doc-and-adr-amendment.md"

Smoke = collections.namedtuple("Smoke", "script args files mode setup", defaults=("", None))

GOAL_CARD = ("# Smoke Goal\n\n> **loop:** yes\n\n## OBJECTIVE\n\nEmit goal files.\n\n"
             "## DONE WHEN\n\n- GOAL.md exists\n\n## STOP-CAPS\n\n- loop.max_iterations: 2\n")


def smoke_key(smoke: Smoke) -> str:
    """Case id and KNOWN_VIOLATIONS key: the script, plus the mode when one is set."""
    return "%s %s" % (smoke.script, smoke.mode) if smoke.mode else smoke.script


def key_script(key: str) -> str:
    """The script a smoke key names (`boundary-map.py crossings` -> `boundary-map.py`)."""
    return key.split(" ", 1)[0]


def _git_in(cwd: Path, *args: str) -> str:
    return subprocess.run(["git", "-C", str(cwd), "-c", "user.name=t", "-c",
                           "user.email=t@example.com", "-c", "commit.gpgsign=false"]
                          + list(args), capture_output=True, text=True, check=True).stdout.strip()


GEN_SKILL_TREE = {
    ".writ/manifest.yaml": (
        'version: 1\nmetadata:\n  name: fixture\n  version: 0.0.1\n'
        '  description: "Fixture catalog."\n  runtime_contract: ".writ/docs/contract.md"\n\n'
        'categories:\n  - id: core\n    label: "Core"\n\n'
        'commands:\n  - name: hello\n    file: commands/hello.md\n    category: core\n'
        '    purpose: "Say hello."\n\n'
        'agents:\n  - name: helper\n    file: agents/helper.md\n    purpose: "Help."\n'
        '    model_tier: floor\n\nskills: []\n'),
    ".writ/docs/contract.md": "# Contract\n",
    "commands/hello.md": "# Hello\n",
    "agents/helper.md": "# Helper\n",
    "SKILL.md": "---\nname: fixture\n---\n",
}


def gen_skill_copy(tmp: Path) -> Path:
    """gen-skill.sh reads and writes relative to its own folder, so its write
    mode runs from a copy inside the `GEN_SKILL_TREE` fixture in `{tmp}` and
    regenerates `{tmp}/SKILL.md`, never the repo's."""
    copy = tmp / "scripts" / "gen-skill.sh"
    copy.parent.mkdir(parents=True, exist_ok=True)
    shutil.copy2(str(SCRIPTS / "gen-skill.sh"), str(copy))
    return copy


def panel_trial_setup(tmp: Path) -> None:
    """A throwaway yuss repo (parent + story commit) and a trial file naming it,
    so `review-panel.py trial-prepare` runs its success path inside `{tmp}`."""
    yuss = tmp / "yuss"
    spec = yuss / ".writ" / "specs" / "s"
    (spec / "user-stories").mkdir(parents=True)
    _git_in(yuss, "init", "-q")
    (spec / "spec.md").write_text("# S\n\n## Specification Contract\n\nA route.\n",
                                  encoding="utf-8")
    story = spec / "user-stories" / "story-1.md"
    story.write_text("# Story 1: Route\n", encoding="utf-8")
    _git_in(yuss, "add", "-A")
    _git_in(yuss, "commit", "-q", "-m", "parent")
    parent = _git_in(yuss, "rev-parse", "HEAD")
    (yuss / "app.py").write_text("print('route')\n", encoding="utf-8")
    _git_in(yuss, "add", "-A")
    _git_in(yuss, "commit", "-q", "-m", "story 1")
    stories = [{"story_id": "s/story-1", "story_path": ".writ/specs/s/user-stories/story-1.md",
                "spec_folder": "s", "story_commit": _git_in(yuss, "rev-parse", "HEAD"),
                "parent_sha": parent, "arms": {}, "panel_only": []}]
    for n in (2, 3, 4):
        stories.append({"story_id": "s/story-%d" % n, "spec_folder": "s",
                        "story_path": ".writ/specs/s/user-stories/story-%d.md" % n,
                        "story_commit": str(n) * 40, "parent_sha": str(n) * 39 + "0",
                        "arms": {}, "panel_only": []})
    (tmp / "trial.json").write_text(json.dumps({"schema": "panel-trial-v1", "baseline": "x",
                                                "stories": stories}), encoding="utf-8")
    (tmp / "runs").mkdir()


PANEL_FX = "{repo}/scripts/tests/fixtures/review-panel/"


def _trial_story(n: int, panel_only: list) -> dict:
    return {"story_id": "s/story-%d" % n, "spec_folder": "s",
            "story_path": ".writ/specs/s/user-stories/story-%d.md" % n,
            "story_commit": str(n) * 40, "parent_sha": str(n) * 39 + "0",
            "arms": {"evaluator": {}, "panel": {}}, "panel_only": panel_only}


# A finished trial: both arms on all four stories, one valid panel-only miss.
PANEL_TRIAL_KEEP = json.dumps({"schema": "panel-trial-v1", "baseline": "x", "stories": [
    _trial_story(1, [{"key": "ac:AC-1.1", "label": "valid", "note": "n"}])]
    + [_trial_story(n, []) for n in (2, 3, 4)]})


# Read-only invocations. `{repo}` is this repo, `{tmp}` a fresh temp dir that
# is also the cwd; `files` are written under `{tmp}` first, then `setup(tmp)`
# runs when set. A setup that returns a path runs that copy of the script in
# place of `scripts/<script>`. Nothing here may
# launch an app, touch the network, or write outside `{tmp}` — the smoke
# asserts the repo's git status is unchanged. Each script has one default
# invocation keyed by its name; a further mode of the same script sets `mode`
# and is keyed `<script> <mode>`. A KNOWN_VIOLATIONS (key, shape|exit_code)
# entry maps to exactly one case.
SMOKE_INVOCATIONS: List[Smoke] = [
    # data
    Smoke("ac-trace.py", ["check", "--spec", SPEC, "--repo", "{repo}"], {}),
    Smoke("archive-sweep.py", ["scan", "--specs-dir", "{repo}/.writ/specs",
                               "--knowledge-dir", "{repo}/.writ/knowledge"], {}),
    Smoke("boundary-map.py", ["compute", "--story", "{tmp}/missing-story.md",
                              "--repo", "{repo}"], {}),
    Smoke("boundary-map.py", ["crossings", "--map", "{tmp}/map.json", "--changed",
                              "src/a.py", "--repo", "{tmp}"],
          {"map.json": '{"owned": ["src/"], "readable": [], "out_of_scope": []}'},
          "crossings"),
    Smoke("build-smoke.py", ["check", "--project", "{tmp}/empty"], {"empty/.keep": ""}),
    Smoke("change-surface.py", ["classify", "--changed", "scripts/spec-status.py"], {}),
    Smoke("exit-criteria.py", ["check-uat", "--spec", SPEC], {}),
    Smoke("knowledge-consolidate.py", ["--knowledge-dir", "{tmp}/kb", "--repo-root", "{tmp}"],
          {"kb/.keep": ""}),
    Smoke("phase-state.py", ["health", "--repo", "{repo}"], {}),
    Smoke("quality-config-audit.py", ["check", "--project", "{repo}"], {}),
    Smoke("resolve-spec-reference.py", ["resolve", "--branch", "feature/agent-cli-contract",
                                        "--specs-dir", "{repo}/.writ/specs"], {}),
    Smoke("revert-resolve.py", ["--repo", "{repo}", "--spec", SPEC_DIR.name, "story", "1"], {}),
    Smoke("roadmap-sync.py", ["check", "--roadmap", "{tmp}/roadmap.md",
                              "--spec-name", SPEC_DIR.name], {"roadmap.md": "# Roadmap\n"}),
    Smoke("spec-deps.py", ["parse", "--spec", SPEC], {}),
    Smoke("spec-status.py", ["scan", "--specs-dir", "{repo}/.writ/specs"], {}),
    Smoke("story-context.py", ["assemble", "--story", STORY, "--state-dir", "{tmp}/state"],
          {}),
    Smoke("story-deps.py", ["validate", "--spec-dir", SPEC], {}),
    Smoke("supersession-writeback.py", ["scan", "--new-spec-file", SPEC + "/spec.md"], {}),
    Smoke("test-integrity.py", ["authenticity", "--project", "{repo}", "--tests",
                                "scripts/tests/test_agent_cli_contract_doc.py"], {}),
    # check
    Smoke("app-verify.py", ["validate", "--recipe", "{tmp}/missing-recipe.md"], {}),
    Smoke("app-verify.py", ["touched", "--recipe", "{repo}/scripts/tests/fixtures/app-verify/"
                            "recipe-pass.md", "--changed", "scripts/tests/fixtures/app-verify/"
                            "app.py"], {}, "touched"),
    Smoke("arch-check.py", ["check", "--story", STORY, "--repo", "{repo}"], {}),
    Smoke("arch-lint.py", ["detect", "--repo", "{tmp}/proj"], {"proj/package.json": "{"}),
    Smoke("docs-check.py", ["check", "--repo", "{repo}", "--changed",
                            "scripts/tests/test_agent_cli_contract_doc.py"], {}),
    Smoke("drift-format.py", ["check", "--story", "{tmp}/missing-story.md"], {}),
    Smoke("gen-claude-agents.py", ["--agents-dir", "{repo}/agents", "--out-dir",
                                   "{tmp}/claude-agents"], {}),
    Smoke("gen-codex-agent-tomls.py", ["--agents-dir", "{repo}/agents", "--out-dir",
                                       "{tmp}/codex-agents"], {}),
    Smoke("goal-emit.py", ["check", "--card", "{tmp}/missing-card.md", "--repo", "{tmp}"], {}),
    Smoke("goal-emit.py", ["emit", "--card", "{tmp}/card.md", "--out", "{tmp}/out",
                           "--repo", "{tmp}"], {"card.md": GOAL_CARD}, "emit"),
    Smoke("jev-judge.py", ["status", "--repo", "{tmp}"], {}),
    Smoke("review-override.py", ["check", "--spec", SPEC, "--repo", "{repo}",
                                 "--story", STORY], {}),
    Smoke("review-panel.py", ["status", "--repo", "{tmp}", "--origin", "claude"], {}),
    Smoke("review-panel.py", ["trial-init", "--baseline", "{repo}/scripts/tests/fixtures/"
                              "review-panel/trial/mini-baseline.json", "--out",
                              "{tmp}/trial.json"], {}, "trial-init"),
    Smoke("review-panel.py", ["trial-prepare", "--trial", "{tmp}/trial.json", "--yuss",
                              "{tmp}/yuss", "--story", "s/story-1", "--tmp-root",
                              "{tmp}/runs"], {}, "trial-prepare", panel_trial_setup),
    Smoke("review-panel.py", ["tally", "--origin", "Claude Fable 5.1", "--primary",
                              PANEL_FX + "primary-fail-ac23.md", "--reviewer",
                              "gpt-5.6-sol-medium=" + PANEL_FX + "panel-ac23.md"], {}, "tally"),
    Smoke("review-panel.py", ["trial-report", "--trial", "{tmp}/trial.json"],
          {"trial.json": PANEL_TRIAL_KEEP}, "trial-report"),
    Smoke("scaffold-writ.py", ["scaffold", "--project", "{tmp}/proj"], {"proj/.keep": ""}),
    Smoke("spec-analyze.py", ["check", "--spec", SPEC, "--repo", "{repo}"], {}),
    Smoke("verdict-provenance.py", ["check", "--command", "{repo}/commands/implement-story.md",
                                    "--repo", "{repo}"], {}),
    Smoke("check-agent-parity.sh", [], {}),
    Smoke("gen-skill.sh", ["--check"], {}),
    Smoke("gen-skill.sh", [], GEN_SKILL_TREE, "write", gen_skill_copy),
    Smoke("lint-skill.sh", ["{repo}/skills/tdd-cycle/SKILL.md"], {}),
]
SMOKE_BY_KEY = {smoke_key(s): s for s in SMOKE_INVOCATIONS}
SMOKE_KEYS = [smoke_key(s) for s in SMOKE_INVOCATIONS]
CHECK_SMOKES = [k for k in SMOKE_KEYS
                if TABLE.get(key_script(k), NO_ALLOWANCES).shape == "check"]


def repo_snapshot() -> str:
    """git status (untracked files listed) plus `.writ/state/`, which git ignores."""
    status = subprocess.run(["git", "-C", str(REPO_ROOT), "status", "--porcelain", "-uall"],
                            capture_output=True, text=True, check=True).stdout
    state = REPO_ROOT / ".writ" / "state"
    listing = sorted("%s %d" % (p.relative_to(REPO_ROOT), p.stat().st_mtime_ns)
                     for p in state.rglob("*")) if state.is_dir() else []
    return status + "\n".join(listing)


@pytest.fixture(scope="module")
def smoke_run(tmp_path_factory):
    """Run each smoke invocation once; cache (shown args, result, repo before, after)."""
    cache: Dict[str, tuple] = {}

    def run(key: str) -> tuple:
        if key not in cache:
            inv = SMOKE_BY_KEY[key]
            tmp = tmp_path_factory.mktemp("smoke")
            for rel, text in inv.files.items():
                (tmp / rel).parent.mkdir(parents=True, exist_ok=True)
                (tmp / rel).write_text(text, encoding="utf-8")
            copy = inv.setup(tmp) if inv.setup is not None else None
            args = [a.replace("{repo}", str(REPO_ROOT)).replace("{tmp}", str(tmp))
                    for a in inv.args]
            before = repo_snapshot()
            result = run_script(copy or SCRIPTS / inv.script, args, tmp)
            cache[key] = (inv.args, result, before, repo_snapshot())
        return cache[key]

    return run


# --------------------------------------------------------------------------
# Real-repo tests
# --------------------------------------------------------------------------

def test_table_complete():
    """AC-3.1 — shipped set and Classification table rows match both ways."""
    problems = table_problems(SHIPPED, TABLE)
    assert not problems, "\n".join(problems)


@pytest.mark.parametrize("script", cases("help", SHIPPED))
def test_help(script, tmp_path):
    """AC-3.2 — `--help` exits 0 (Python) or prints usage naming the script (shell)."""
    msg = check_help(script, SCRIPTS / script, tmp_path)
    if msg:
        pytest.fail(msg, pytrace=False)


@pytest.mark.parametrize("script", cases("bad_flag", SHIPPED))
def test_bad_flag(script, tmp_path):
    """AC-3.2 — `--zz-contract-probe` exits non-zero; stdout empty or a JSON blocker."""
    msg = check_bad_flag(script, SCRIPTS / script, tmp_path)
    if msg:
        pytest.fail(msg, pytrace=False)


@pytest.mark.parametrize("script", cases("network", PY_SHIPPED))
def test_no_unmarked_network(script):
    """AC-3.2 — network imports only in rows marked `network: opt-in`."""
    msg = check_network(script, SCRIPTS / script, TABLE.get(script, NO_ALLOWANCES))
    if msg:
        pytest.fail(msg, pytrace=False)


@pytest.mark.parametrize("script", cases("agent_launch", PY_SHIPPED))
def test_no_agent_launch(script):
    """AC-3.2 — no launch call targets an agent CLI."""
    msg = check_agent_launch(script, SCRIPTS / script, TABLE.get(script, NO_ALLOWANCES))
    if msg:
        pytest.fail(msg, pytrace=False)


@pytest.mark.parametrize("script", cases("bounded_wait", PY_SHIPPED))
def test_bounded_wait_marked(script):
    """AC-3.2 — `time.sleep` / `while True` only in rows marked `bounded-wait`."""
    msg = check_bounded_wait(script, SCRIPTS / script, TABLE.get(script, NO_ALLOWANCES))
    if msg:
        pytest.fail(msg, pytrace=False)


@pytest.mark.parametrize("key", SMOKE_KEYS)
def test_smoke_leaves_repo_unchanged(key, smoke_run):
    """AC-3.5 — a smoke invocation run from a temp cwd leaves the repo's git status unchanged."""
    args, _, before, after = smoke_run(key)
    assert before == after, ("%s: `%s` changed the repo; fix: remove it from "
                             "SMOKE_INVOCATIONS" % (key, " ".join(args)))


@pytest.mark.parametrize("key", cases("shape", SMOKE_KEYS))
def test_shape_smoke(key, smoke_run):
    """AC-3.5 — data stdout is one JSON value; check line 1 is the verdict, summary last."""
    args, result, _, _ = smoke_run(key)
    script = key_script(key)
    msg = check_shape(script, TABLE[script].shape, args, result)
    if msg:
        pytest.fail(msg, pytrace=False)


@pytest.mark.parametrize("key", cases("exit_code", CHECK_SMOKES))
def test_exit_code_smoke(key, smoke_run):
    """AC-3.5 — a check run's exit code matches its verdict (0/1/2)."""
    args, result, _, _ = smoke_run(key)
    msg = check_exit_code(key_script(key), args, result)
    if msg:
        pytest.fail(msg, pytrace=False)


def test_smoke_covers_each_shape_and_shell():
    """AC-3.5 — SMOKE_INVOCATIONS hold shipped scripts, one default per script, both shapes, and a shell script."""
    assert len(SMOKE_KEYS) == len(set(SMOKE_KEYS)), "one smoke invocation per key"
    defaults = [s.script for s in SMOKE_INVOCATIONS if not s.mode]
    assert len(defaults) == len(set(defaults)), "one default smoke invocation per script"
    scripts = [s.script for s in SMOKE_INVOCATIONS]
    assert set(scripts) == set(defaults), "every moded smoke has a default for its script"
    assert set(scripts) <= set(SHIPPED), sorted(set(scripts) - set(SHIPPED))
    shapes = {TABLE[s].shape for s in scripts}
    assert shapes == set(SHAPES)
    assert any(s.endswith(".sh") for s in scripts)


def test_smoke_key_names_mode_and_maps_to_script():
    """AC-3.5 — a moded smoke is keyed `<script> <mode>` and its xfail entry marks only that case."""
    default = Smoke("x.py", ["status"], {})
    moded = Smoke("x.py", ["write"], {}, "write")
    assert (smoke_key(default), smoke_key(moded)) == ("x.py", "x.py write")
    assert key_script("x.py write") == "x.py"
    params = cases("shape", ["x.py", "x.py write"], {("x.py write", "shape"): "fixture"})
    assert [bool(p.marks) for p in params] == [False, True]


def test_known_violations_are_well_formed():
    """AC-3.4 — each KNOWN_VIOLATIONS entry has a reason and maps to a case that runs."""
    smoked = set(SMOKE_KEYS)
    for (key, rule), reason in KNOWN_VIOLATIONS.items():
        script = key_script(key)
        assert isinstance(reason, str) and reason.strip(), "%s/%s: empty reason" % (key, rule)
        assert script in SHIPPED, "%s: not shipped; fix: remove it from KNOWN_VIOLATIONS" % script
        assert rule in RULE_REFS, "%s: unknown rule %r" % (script, rule)
        runs = {
            "table": False,
            "help": key == script,
            "bad_flag": key == script,
            "shape": key in smoked,
            "exit_code": key in CHECK_SMOKES,
        }.get(rule, key == script and script.endswith(".py"))
        assert runs, ("%s: (%r, %r) matches no test case; fix: remove it from "
                      "KNOWN_VIOLATIONS" % (key, key, rule))


STORY5_SCRIPTS = ("app-verify.py", "check-agent-parity.sh", "gen-skill.sh", "lint-skill.sh")

# Pre-contract output that Story 5 removed (including review-panel tally's
# bare `block`): a caller still quoting it would misread the check shape.
# (file, literal) pairs, one per retired phrasing.
STORY5_STALE_CALLER_TEXT = (
    ("commands/new-skill.md", "exited 0 on the captured description"),
    ("commands/new-skill.md", "reports no delta"),
    ("commands/refresh-command.md", "always exit 0"),
    ("commands/refresh-command.md", "parity OK line"),
    ("commands/refresh-command.md", "exits `0` (all clean)"),
    ("commands/implement-story.md", "printed no IDs"),
    ("commands/implement-story.md", "- **exit 2** (no recipe"),
    ("commands/create-uat-plan.md", "- Exit 2 →"),
    (".writ/docs/app-verification-format.md", "and 2 when the file is missing"),
    ("adapters/codex.md", "warnings must be intentional"),
    ("commands/implement-story.md", "`block` is a Gate 3 FAIL"),
)


def test_story5_scripts_carry_no_known_violation():
    """AC-5.5 — the shell scripts and app-verify.py pass every rule with no strict-xfail entry."""
    listed = sorted({key_script(key) for key, _ in KNOWN_VIOLATIONS} & set(STORY5_SCRIPTS))
    assert listed == [], ("%s: listed in KNOWN_VIOLATIONS; fix: make the script conform "
                          "instead of exempting it" % ", ".join(listed))


def test_story5_callers_quote_no_old_output():
    """AC-5.4 — callers of the Story 5 scripts read line 1, not the retired output."""
    stale = ["%s still says %r" % (rel, text) for rel, text in STORY5_STALE_CALLER_TEXT
             if text in _read(REPO_ROOT / rel)]
    assert not stale, ("callers quote pre-contract output; fix: branch on the line-1 "
                       "verdict\n" + "\n".join(stale))


# --------------------------------------------------------------------------
# Fixture tests: prove each rule's failure path without breaking real scripts
# --------------------------------------------------------------------------

def write(path: Path, text: str) -> Path:
    path.write_text(text, encoding="utf-8")
    return path


GOOD_PY = '''\
import argparse, json
p = argparse.ArgumentParser(description="fixture")
p.add_argument("--repo", default=".")
args = p.parse_args()
print(json.dumps({"ok": True}))
'''
GOOD_SH = '''\
usage() { echo "Usage: bash good.sh [--check]"; }
case "${1:-}" in
  --help|-h) usage; exit 0 ;;
  --check|"") echo pass; echo "good: pass (fixture)"; exit 0 ;;
  *) usage >&2; exit 2 ;;
esac
'''


def test_ship_filter_missing_is_setup_error():
    """AC-3.1 — install.sh without is_shippable_script raises the named setup error."""
    with pytest.raises(AssertionError, match=re.escape(SHIP_FILTER_ERROR)):
        shipped_scripts("#!/bin/bash\necho no filter here\n", ["a.py"])


def test_ship_filter_runs_extracted_function():
    """AC-3.1 — the extracted function decides the set; non-script files are dropped."""
    text = ('echo "install logic must not run"; exit 9\n'
            'is_shippable_script() {\n  case "$1" in\n    skip.py) return 1 ;;\n'
            '  esac\n  return 0\n}\n')
    assert shipped_scripts(text, ["a.py", "skip.py", "b.sh", "data.json"]) == ["a.py", "b.sh"]


def test_missing_table_is_setup_error():
    """AC-3.1 — a doc with no Classification table raises the named setup error."""
    with pytest.raises(AssertionError, match=re.escape(TABLE_ERROR)):
        parse_classification("# Doc\n\n## Classification\n\nNo table yet.\n")


def test_table_parser_reads_shape_and_allowances():
    """AC-3.1 — the parser keeps shape and the allowance set for each row."""
    doc = ("## Classification\n\n| Script | Shape | Allowances | Callers |\n|---|---|---|---|\n"
           "| `a.py` | check | network: opt-in, bounded-wait | x |\n| `b.sh` | data |  | y |\n"
           "\nnote\n\n## Next\n| `c.py` | data |  | z |\n")
    assert parse_classification(doc) == {
        "a.py": Row("check", frozenset(ALLOWANCES)),
        "b.sh": Row("data", frozenset()),
    }


def test_table_missing_row_fixture():
    """AC-3.1 — a shipped script with no row: message starts with the script, ends 'add a row'."""
    problems = table_problems({"a.py", "new.py"}, {"a.py": Row("data", frozenset())})
    assert len(problems) == 1
    assert problems[0].startswith("new.py ")
    assert problems[0].endswith("add a row")


def test_table_extra_row_fixture():
    """AC-3.1 — a row with no shipped script fails the same way, naming the row."""
    problems = table_problems({"a.py"}, {"a.py": NO_ALLOWANCES, "gone.py": NO_ALLOWANCES})
    assert len(problems) == 1
    assert problems[0].startswith("gone.py ")


def test_table_bad_vocabulary_fixture():
    """AC-3.1 — an unknown shape or allowance in a row fails, naming the row."""
    problems = table_problems({"a.py"}, {"a.py": Row("json", frozenset({"sleepy"}))})
    assert len(problems) == 1 and problems[0].startswith("a.py ")


def test_network_fixture(tmp_path):
    """AC-3.2 — a network import without `network: opt-in` names script, Business Rule 8, and fix."""
    path = write(tmp_path / "net.py", "import socket\nfrom urllib import request\n")
    msg = check_network("net.py", path, NO_ALLOWANCES)
    assert msg and msg.startswith("net.py:")
    assert "Business Rule 8" in msg and "socket" in msg and "urllib.request" in msg
    assert msg.endswith("drop the import")
    assert check_network("net.py", path, Row("check", frozenset({"network: opt-in"}))) is None


def test_agent_launch_fixture(tmp_path):
    """AC-3.2 — an agent CLI launch literal names script, Business Rule 6, and fix."""
    path = write(tmp_path / "agent.py",
                 "import subprocess, os\nsubprocess.run(['claude', '-p', 'hi'])\n"
                 "os.execvp('codex', ['codex'])\nsubprocess.Popen('cursor-agent run', shell=True)\n")
    msg = check_agent_launch("agent.py", path, NO_ALLOWANCES)
    assert msg and msg.startswith("agent.py:")
    assert "Business Rule 6" in msg
    for cli in ("claude at line 2", "codex at line 3", "cursor-agent at line 4"):
        assert cli in msg
    assert msg.endswith("the harness's job")


def test_bounded_wait_fixture(tmp_path):
    """AC-3.2 — time.sleep or while True without `bounded-wait` names script, Business Rule 7, and fix."""
    path = write(tmp_path / "sleepy.py",
                 "import time\ntime.sleep(1)\nwhile True:\n    break\n")
    msg = check_bounded_wait("sleepy.py", path, NO_ALLOWANCES)
    assert msg and msg.startswith("sleepy.py:")
    assert "Business Rule 7" in msg and "time.sleep at line 2" in msg
    assert "while True at line 3" in msg and msg.endswith("enforce a timeout")
    assert check_bounded_wait("sleepy.py", path, Row("check", frozenset({"bounded-wait"}))) is None


def test_string_literals_do_not_trigger_static_rules(tmp_path):
    """AC-3.2 — scans read import and call nodes, so strings like 'socket hang up' pass."""
    path = write(tmp_path / "quiet.py",
                 "import urllib.parse\nMSG = 'socket hang up; time.sleep; while True'\n"
                 "PLATFORMS = ['claude', 'codex']\nprint(sorted(['claude']))\n"
                 "import subprocess\nsubprocess.run(['git', 'status'])\n")
    for check in STATIC_CHECKS.values():
        assert check("quiet.py", path, NO_ALLOWANCES) is None


def test_syntax_error_fails_static_rules(tmp_path):
    """AC-3.2 — a script that does not parse on this Python fails with the floor in the fix."""
    path = write(tmp_path / "new.py", "def f(:\n    pass\n")
    msg = check_network("new.py", path, NO_ALLOWANCES)
    assert msg and msg.startswith("new.py:") and msg.endswith("Python 3.9 floor")


def test_help_exit_fixture(tmp_path):
    """AC-3.2 — a Python --help that exits non-zero fails, naming the script and the fix."""
    path = write(tmp_path / "badhelp.py", "import sys\nsys.stderr.write('boom\\n')\nsys.exit(3)\n")
    msg = check_help("badhelp.py", path, tmp_path)
    assert msg and msg.startswith("badhelp.py:") and "exited 3" in msg and "boom" in msg
    assert "ADR-029 rule 7" in msg and msg.endswith("(argparse does this)")


def test_shell_help_without_usage_fixture(tmp_path):
    """AC-3.2 — a shell --help with no usage line naming the script fails."""
    path = write(tmp_path / "plain.sh", 'echo "did the work"\nbasename --zz 2>&1 || true\n')
    msg = check_help("plain.sh", path, tmp_path)
    assert msg and msg.startswith("plain.sh:") and "usage line" in msg


def test_bad_flag_prose_fixture(tmp_path):
    """AC-3.2 — a Python bad flag that prints prose to stdout fails Business Rule 5."""
    path = write(tmp_path / "noisy.py", "print('hello there')\nraise SystemExit(1)\n")
    msg = check_bad_flag("noisy.py", path, tmp_path)
    assert msg and msg.startswith("noisy.py:") and "Business Rule 5" in msg
    assert "hello there" in msg and msg.endswith("JSON `blocker` object")


def test_shell_bad_flag_prose_fixture(tmp_path):
    """AC-3.2 — a shell script whose bad flag prints prose to stdout fails Business Rule 5."""
    path = write(tmp_path / "noisy.sh", 'echo "Unknown option: $1"\nexit 1\n')
    msg = check_bad_flag("noisy.sh", path, tmp_path)
    assert msg and msg.startswith("noisy.sh:") and "Business Rule 5" in msg
    exit0 = write(tmp_path / "ignores.sh", 'echo "all good"\n')
    assert "exited 0" in check_bad_flag("ignores.sh", exit0, tmp_path)


def test_bad_flag_json_blocker_is_allowed(tmp_path):
    """AC-3.2 — a JSON blocker on stdout with a non-zero exit conforms (recommend-state.py style)."""
    path = write(tmp_path / "blocker.py", "import json\nprint(json.dumps({'blocker': "
                 "{'code': 'invalid_arguments', 'summary': 'x'}}))\nraise SystemExit(2)\n")
    assert check_bad_flag("blocker.py", path, tmp_path) is None


def test_conforming_python_fixture(tmp_path):
    """AC-3.2 — a conforming Python fixture passes every rule check."""
    path = write(tmp_path / "good.py", GOOD_PY)
    assert check_help("good.py", path, tmp_path) is None
    assert check_bad_flag("good.py", path, tmp_path) is None
    for check in STATIC_CHECKS.values():
        assert check("good.py", path, NO_ALLOWANCES) is None


def test_conforming_shell_fixture(tmp_path):
    """AC-3.2 — a conforming shell fixture passes the help and bad-flag checks."""
    path = write(tmp_path / "good.sh", GOOD_SH)
    assert check_help("good.sh", path, tmp_path) is None
    assert check_bad_flag("good.sh", path, tmp_path) is None


def test_shell_gets_only_table_help_bad_flag():
    """AC-3.2 — shell scripts get only the table, help, and bad-flag checks."""
    assert rules_for("x.sh") == ("table", "help", "bad_flag")
    assert rules_for("x.py") == ("table", "help", "bad_flag") + STATIC_RULES


def test_shape_fixtures(tmp_path):
    """AC-3.5 — data needs one JSON value; check needs the verdict on line 1 and a summary last."""
    good_sh = write(tmp_path / "good.sh", GOOD_SH)
    good_py = write(tmp_path / "good.py", GOOD_PY)
    prose = write(tmp_path / "prose.py", "print('Revert plan:')\nprint('{}')\n")
    late = write(tmp_path / "late.sh", 'echo "late: pass (x)"\necho pass\n')
    assert check_shape("good.sh", "check", ["--check"], run_script(good_sh, ["--check"],
                                                                  tmp_path)) is None
    assert check_shape("good.py", "data", [], run_script(good_py, [], tmp_path)) is None
    msg = check_shape("prose.py", "data", [], run_script(prose, [], tmp_path))
    assert msg and msg.startswith("prose.py:") and "Business Rules 3-4" in msg
    msg = check_shape("late.sh", "check", [], run_script(late, [], tmp_path))
    assert msg and msg.startswith("late.sh:") and "line 1" in msg


def test_exit_code_fixture(tmp_path):
    """AC-3.5 — exit 0 for pass/unverifiable and 1 for fail pass; unverifiable exit 2 or fail exit 0 fail Business Rule 4."""
    def sh(name: str, verdict: str, code: int) -> Path:
        return write(tmp_path / name, 'echo %s\necho "%s: %s (x)"\nexit %d\n'
                     % (verdict, name[:-3], verdict, code))

    for name, verdict, code in (("ok.sh", "pass", 0), ("ran.sh", "unverifiable", 0),
                                ("bad.sh", "fail", 1)):
        assert check_exit_code(name, [], run_script(sh(name, verdict, code), [],
                                                    tmp_path)) is None, name
    for name, verdict, code in (("two.sh", "unverifiable", 2), ("lax.sh", "fail", 0)):
        msg = check_exit_code(name, [], run_script(sh(name, verdict, code), [], tmp_path))
        assert msg and msg.startswith(name + ":") and "Business Rule 4" in msg, name
        assert msg.endswith("2 only for usage or could-not-start"), msg


MINI_MODULE = '''\
import sys
sys.path.insert(0, %(tests_dir)r)
from pathlib import Path
import pytest
import test_agent_cli_contract as c

PATHS = {"fixed.py": Path(%(fixed)r), "still.py": Path(%(still)r)}
KNOWN = {("fixed.py", "bounded_wait"): "fixture: used to sleep",
         ("still.py", "bounded_wait"): "fixture: still sleeps"}


@pytest.mark.parametrize("script", c.cases("bounded_wait", sorted(PATHS), KNOWN))
def test_bounded_wait(script):
    msg = c.check_bounded_wait(script, PATHS[script], c.NO_ALLOWANCES)
    if msg:
        pytest.fail(msg, pytrace=False)
'''


def test_known_violation_xfail_and_strict_xpass(tmp_path):
    """AC-3.3 — a listed violation xfails with its reason; a fixed one fails as strict XPASS."""
    fixed = write(tmp_path / "fixed.py", "for _ in range(3):\n    pass\n")
    still = write(tmp_path / "still.py", "import time\ntime.sleep(1)\n")
    module = write(tmp_path / "test_mini_contract.py", MINI_MODULE % {
        "tests_dir": str(TESTS_DIR), "fixed": str(fixed), "still": str(still)})
    result = subprocess.run(
        [sys.executable, "-m", "pytest", "-q", "-rxX", "-p", "no:cacheprovider", str(module)],
        cwd=str(tmp_path), env=script_env(), capture_output=True, text=True, timeout=RUN_TIMEOUT)
    out = result.stdout + result.stderr
    assert result.returncode == 1, out
    assert "1 failed" in out and "1 xfailed" in out, out
    assert "XPASS(strict)" in out, out
    assert "remove ('fixed.py', 'bounded_wait') from KNOWN_VIOLATIONS" in out, out
    assert "fixture: still sleeps" in out, out


def test_every_test_names_its_ac_id():
    """AC-3.4 — every test in this file names a Story 3 or Story 5 AC ID in its docstring."""
    for name, obj in sorted(globals().items()):
        if name.startswith("test_") and callable(obj):
            assert re.search(r"\bAC-[35]\.[1-5]\b", obj.__doc__ or ""), name
