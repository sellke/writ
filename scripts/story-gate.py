#!/usr/bin/env python3
"""Run `/implement-story`'s default-path checks in a fixed order (Story 3 of
`2026-11-06-lean-story-pipeline`).

One command's fixed check sequence, not a dispatcher: the table below names
the checker scripts that `commands/implement-story.md` would otherwise call one
by one. Each checker is a sibling of this file.

Subcommands:
  run --phase pre-review|post-review --story PATH --spec DIR --base SHA
      [--repo .] [--review-output PATH] [--tests-output PATH] [--checks PATH]
      [--manifest PATH] [--state-dir <repo>/.writ/state]
  tally [--state-dir <repo>/.writ/state]

`run` computes the changed files as `git diff --name-only <base>` plus
untracked files, then runs every check of the phase in table order, even after
a fail. pre-review: build smoke (only when a file outside `.writ/` that is not
markdown changed), arch-lint (detect, then each `command:` line; a failing
command is advisory and never counted), change-surface classify, boundary-map
crossings against `<state-dir>/boundary-<story-stem>.json` (no map: skipped,
route evaluator-agent), and blast radius (only on the review-agent route with
the Safety Fact switch on; written to `<state-dir>/blast-radius-<stem>.json`).
It resolves the three `review-override.py switch` states and prints `route:`,
`change_surface:`, `blast_radius:`, `safety_fact:`, `reviewer_filters:` and
`evidence_gate:` lines for Gate 3. post-review: review-override check,
safety-fact (when pre-review turned it on), evidence (on an agent FAIL, or any
verdict once the manifest exists, with `--prior`; never when safety-fact
re-spawns Gate 3), the Gate 3 decision (the `EVALUATION_RESULT`/`REVIEW_RESULT`
heading in `--review-output`, first match, after evidence),
drift-format check, test-integrity coverage and authenticity, repro-order
(only when a commit since `--base` has a `Repro:` line), then the Jev shadow
(only when `jev-judge.py status` prints `pass`; never counted). It applies
Gate 3's first-match evidence table and prints `gate3: PASS|FAIL|PAUSE (...)`.
The repros the evidence manifest records (ADR-032: committed unchanged) stay
out of the `--tests` list given to review-override check and authenticity,
with the reason `skipped <n> evidence repro(s): adr032_repro`; a missing or
unreadable manifest leaves the list as it is.
Without `--review-output`, the review checks read `unverifiable
(no_review_output)`.

A check's verdict is its checker's line 1 (check shape) or JSON `verdict`
(data shape). A missing checker, an exit outside 0/1/2, exit 2, empty stdout,
or unparseable output reads `unverifiable (helper_error: ...)`; a check over
its time limit (its checker's own `--timeout` plus a margin, else 600 s;
`STORY_GATE_TIMEOUT` caps every check) reads `unverifiable (timeout)`. Not a
git repo: git-dependent checks read `unverifiable (no_git)`. A check that does
not apply reads `skip (<why>)`. `unverifiable` and `skip` never set `fail`.

Overall verdict: `fail` when any counted check is `fail`, else `pass`.
`restart:` (only on fail) is Gate 3's table target when Gate 3 fails, else the
first failing counted check's target: `gate1` recode, `gate2` BLOCKED at Gate
2, `gate3` re-spawn the Gate 3 agent, `gate3-blocked` BLOCKED at Gate 3,
`gate4` BLOCKED at Gate 4's integrity check. A failing check with no target
(repro-order) prints no `restart:` line.

Output, check shape: line 1 `pass` or `fail`; one `check: <id> <verdict>
(<first reason or ok>)` line per check; `restart:`; `gate3:` (post-review);
the pre-review lines; `reason: record_write_failed` when the record could not
be written; the summary `story-gate: <verdict> (phase <phase>, <n> checks, <f>
fail, <u> unverifiable)`; then the `story-gate-v1` JSON record as the last
line. The record is written atomically to
`<state-dir>/story-gate-<story-stem>-<phase>.json`, replacing the last one, and
a copy goes to `<state-dir>/story-gate-history/<stem>-<phase>-<at>.json`. It
holds `head_sha` (`git rev-parse HEAD`) and `dirty` (uncommitted changes
outside the `--spec` folder).

`tally` reads the history and prints `pass`, one `tally: <id> runs=<n>
fails=<n> sole_catches=<n>` line per check id (sole catch: the record's only
counted fail), and `story-gate tally: pass (<n> records, <k> checks)`. No
history prints `unverifiable` and `reason: no_records`. It writes nothing.

Exit 0: pass (or tally ran). Exit 1: fail. Exit 2: usage, including a `--base`
that is not a commit (cause on stderr, stdout empty). Stdlib only, Python 3.9.
Runs only the checkers, `git`, and the arch-lint commands; no network.
"""

from __future__ import annotations

import argparse
import datetime as _dt
import json
import os
import posixpath
import re
import shlex
import subprocess
import sys
import tempfile
from pathlib import Path
from typing import Any, Callable, Dict, List, NamedTuple, Optional, Set, Tuple

SCHEMA = "story-gate-v1"
SCRIPTS_DIR = Path(__file__).resolve().parent
DEFAULT_TIMEOUT = 600
VERDICTS = ("pass", "fail", "unverifiable")
TEST_DIRS = {"test", "tests", "__tests__", "spec", "e2e", "cypress"}
TEST_NAME = re.compile(r"^(test_.*|.*_test\..*|.*\.test\..*|.*\.spec\..*|.*_spec\..*|conftest\.py)$")
# review-override.py's VERDICT_LINE: the heading line, first match wins.
AGENT_VERDICT = re.compile(r"^#{1,6}\s*(?:EVALUATION_RESULT|REVIEW_RESULT):\s*\**\s*([A-Za-z]+)",
                           re.MULTILINE)
# Test suffixes test-integrity.py authenticity can read: its SOURCE_SUFFIXES plus .py.
AUTHENTICITY_SUFFIXES = (".py", ".ts", ".tsx", ".js", ".jsx", ".mts", ".cts", ".mjs", ".cjs")
SHELL_SUFFIXES = (".sh", ".bash", ".zsh")
REPRO_LINE = re.compile(r"^Repro:\s*\S", re.MULTILINE)
PRIOR_CODES = ("repro_removed", "repro_modified", "repro_still_failing")
MANIFEST_SCHEMA = "evidence-manifest-v1"  # review-override.py --manifest-out


class UsageError(Exception):
    pass


class Row(NamedTuple):
    id: str
    gate: str            # the `gates:` id in commands/implement-story.md
    script: Optional[str]
    run: Callable[["Ctx", "Row"], Dict[str, Any]]
    counted: bool = True


class Ctx:
    """Inputs shared by every check in one run."""

    def __init__(self, args: argparse.Namespace) -> None:
        self.phase = args.phase
        self.repo = Path(args.repo).resolve()
        self.story = Path(args.story).resolve()
        self.stem = self.story.stem
        self.spec = Path(args.spec).resolve()
        self.base = args.base
        self.state = Path(args.state_dir).resolve() if args.state_dir else self.repo / ".writ" / "state"
        self.review = Path(args.review_output).resolve() if args.review_output else None
        self.tests_output = Path(args.tests_output).resolve() if args.tests_output else None
        self.checks = (Path(args.checks).resolve() if args.checks
                       else self.state / ("gate2-checks-%s.txt" % self.stem))
        self.manifest = (Path(args.manifest).resolve() if args.manifest
                         else self.state / ("evidence-%s.json" % self.stem))
        self.cap = _env_cap()
        self.git_ok = _git(self.repo, "rev-parse", "--is-inside-work-tree") == "true"
        self.changed: Optional[List[str]] = None
        self.new_files: Optional[List[str]] = None
        self.head: Optional[str] = None
        self.dirty: Optional[bool] = None
        self.inputs: Dict[str, Any] = {}
        self.results: Dict[str, Dict[str, Any]] = {}
        self.agent: Optional[str] = None
        self.pre: Dict[str, Any] = {}
        self.evidence_gate = "on"
        self.agent_why = "no_review_output"
        self._repros: Optional[Set[str]] = None
        if self.git_ok:
            sha = _git(self.repo, "rev-parse", "--verify", "--quiet", self.base + "^{commit}")
            if sha is None:
                raise UsageError("--base %s is not a commit in %s" % (self.base, self.repo))
            self.base = sha
            self._git_facts()

    def _git_facts(self) -> None:
        diff = _git_list(self.repo, "diff", "--name-only", "-z", "--diff-filter=d", self.base)
        added = _git_list(self.repo, "diff", "--name-only", "-z", "--diff-filter=A", self.base)
        untracked = _git_list(self.repo, "ls-files", "--others", "--exclude-standard", "-z")
        self.changed = sorted(set(diff) | set(untracked))
        self.new_files = sorted(set(added) | set(untracked))
        self.head = _git(self.repo, "rev-parse", "HEAD")
        status = _git_list(self.repo, "status", "--porcelain", "-z", "--untracked-files=all")
        paths: List[str] = []
        skip = False
        for entry in status:
            if skip:  # a rename's or copy's source path, which has no status field
                paths.append(entry)
                skip = False
                continue
            paths.append(entry[3:])
            skip = entry[:1] in ("R", "C")
        try:
            own = self.spec.relative_to(self.repo).as_posix().rstrip("/") + "/"
        except ValueError:
            own = None
        # Gate 3.5 § A edits drift-log.md and spec-lite.md in the story's spec
        # folder before post-review; every other uncommitted path is dirty.
        self.dirty = any(own is None or not p.startswith(own) for p in paths)

    @property
    def tests(self) -> Optional[List[str]]:
        if self.changed is None:
            return None
        return [p for p in self.changed if not p.startswith(".writ/") and _is_test(p)]

    @property
    def repros(self) -> Set[str]:
        """Repro paths the evidence manifest records for this story (empty when
        the manifest is missing, unreadable, or not `evidence-manifest-v1`)."""
        if self._repros is None:
            self._repros = _manifest_repros(self.manifest)
        return self._repros

    @property
    def new_source(self) -> Optional[List[str]]:
        if self.new_files is None:
            return None
        return [p for p in self.new_files if not p.startswith(".writ/") and not _is_test(p)]


# --- helpers -----------------------------------------------------------------

def _env_cap() -> Optional[int]:
    raw = os.environ.get("STORY_GATE_TIMEOUT", "").strip()
    return int(raw) if raw.isdigit() and int(raw) > 0 else None


def _git(repo: Path, *args: str, strip: bool = True) -> Optional[str]:
    try:
        out = subprocess.run(["git", "-C", str(repo)] + list(args), capture_output=True,
                             text=True, timeout=60)
    except (OSError, subprocess.SubprocessError):
        return None
    if out.returncode != 0:
        return None
    return out.stdout.strip() if strip else out.stdout


def _git_list(repo: Path, *args: str) -> List[str]:
    # Never strip -z output: a porcelain entry opens with a status column that
    # may be a space (` M path`), and a path may start or end with a space.
    out = _git(repo, *args, strip=False)
    return [p for p in (out or "").split("\0") if p]


def _manifest_repros(path: Path) -> Set[str]:
    try:
        doc = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, ValueError, RecursionError):
        return set()
    if not isinstance(doc, dict) or doc.get("schema") != MANIFEST_SCHEMA:
        return set()
    repros = doc.get("repros")
    if not isinstance(repros, list):
        return set()
    return {posixpath.normpath(e["path"]) for e in repros
            if isinstance(e, dict) and isinstance(e.get("path"), str) and e["path"]}


def _without_repros(ctx: "Ctx", tests: List[str]) -> Tuple[List[str], Optional[str]]:
    """`tests` less the ADR-032 evidence repros, and the reason note when any
    were left out. A repro must be committed unchanged and often reads a
    command or data file instead of importing source, which authenticity
    reports as `test_imports_no_source`: a fail the coder cannot fix."""
    repros = ctx.repros
    kept = [p for p in tests if posixpath.normpath(p) not in repros]
    dropped = len(tests) - len(kept)
    return kept, ("skipped %d evidence repro(s): adr032_repro" % dropped if dropped else None)


def _is_test(path: str) -> bool:
    parts = path.split("/")
    return any(seg in TEST_DIRS for seg in parts[:-1]) or bool(TEST_NAME.match(parts[-1]))


def _result(row: Row, verdict: str, reasons: List[str], command: Optional[List[str]] = None,
            exit_code: Optional[int] = None, restart: Optional[str] = None,
            detail: Optional[List[str]] = None, summary: str = "") -> Dict[str, Any]:
    return {"id": row.id, "gate": row.gate, "command": command, "exit": exit_code,
            "verdict": verdict, "reasons": reasons, "counted": row.counted,
            "restart": restart if verdict == "fail" else None,
            "detail": detail or [], "summary": summary}


def _skip(row: Row, why: str) -> Dict[str, Any]:
    return _result(row, "skip", [why])


def _unverifiable(row: Row, why: str, command: Optional[List[str]] = None,
                  exit_code: Optional[int] = None) -> Dict[str, Any]:
    return _result(row, "unverifiable", [why], command, exit_code)


def _invoke(ctx: Ctx, row: Row, args: List[str], shape: str, own_timeout: Optional[int] = None,
            script: Optional[str] = None) -> Dict[str, Any]:
    """Run one checker. Returns a result, or a dict with `_ok` holding parsed output."""
    path = SCRIPTS_DIR / (script or row.script or "")
    command = [sys.executable, str(path)] + args
    if not path.is_file():
        return _unverifiable(row, "helper_error: missing %s" % path, command)
    limit = own_timeout or DEFAULT_TIMEOUT
    if ctx.cap:
        limit = min(limit, ctx.cap)
    try:
        proc = subprocess.run(command, cwd=str(ctx.repo), capture_output=True, text=True,
                              timeout=limit)
    except subprocess.TimeoutExpired:
        return _unverifiable(row, "timeout", command)
    except OSError as exc:
        return _unverifiable(row, "helper_error: %s" % exc, command)
    code = proc.returncode
    stdout = proc.stdout.strip()
    if code not in (0, 1, 2):
        return _unverifiable(row, "helper_error: exit %d" % code, command, code)
    if not stdout:
        return _unverifiable(row, "helper_error: exit %d, empty stdout" % code, command, code)
    if code == 2:
        cause = (proc.stderr.strip().splitlines() or stdout.splitlines() or [""])[-1]
        return _unverifiable(row, "helper_error: exit 2 (%s)" % cause[:200], command, code)
    if shape == "json":
        try:
            data = json.loads(stdout)
        except ValueError:
            return _unverifiable(row, "helper_error: output is not JSON", command, code)
        if not isinstance(data, dict):
            return _unverifiable(row, "helper_error: output is not a JSON object", command, code)
        return {"_ok": data, "command": command, "exit": code, "stdout": proc.stdout}
    lines = stdout.splitlines()
    head = lines[0].strip()
    reasons = [ln[len("reason:"):].strip() for ln in lines[1:] if ln.startswith("reason:")]
    detail = [ln for ln in lines[1:-1] if not ln.startswith("reason:")]
    return {"_ok": {"line1": head, "reasons": reasons, "detail": detail,
                    "summary": lines[-1] if len(lines) > 1 else ""},
            "command": command, "exit": code, "stdout": proc.stdout}


def _check_shape(row: Row, out: Dict[str, Any], restart: Optional[str] = None) -> Dict[str, Any]:
    if "_ok" not in out:
        return out
    data = out["_ok"]
    if data["line1"] not in VERDICTS:
        return _unverifiable(row, "helper_error: line 1 is %r" % data["line1"][:40],
                             out["command"], out["exit"])
    return _result(row, data["line1"], data["reasons"], out["command"], out["exit"], restart,
                   data["detail"], data["summary"])


def _json_verdict(row: Row, out: Dict[str, Any], restart: Optional[str] = None) -> Dict[str, Any]:
    """Data-shape checkers (build-smoke, test-integrity): `verdict`, findings, unverifiable."""
    if "_ok" not in out:
        return out
    data = out["_ok"]
    verdict = data.get("verdict")
    if verdict not in VERDICTS:
        return _unverifiable(row, "helper_error: no verdict in JSON", out["command"], out["exit"])
    reasons: List[str] = []
    for f in data.get("findings") or []:
        if isinstance(f, dict) and (verdict != "fail" or f.get("severity") == "blocking"):
            reasons.append(" ".join(str(x) for x in (f.get("code"), f.get("file")) if x))
    for u in data.get("unverifiable") or []:
        if isinstance(u, dict):
            reasons.append(" ".join(str(x) for x in (u.get("code"), u.get("reason")) if x))
    return _result(row, verdict, reasons, out["command"], out["exit"], restart)


def _changed_or(ctx: Ctx, row: Row) -> Optional[Dict[str, Any]]:
    """Unverifiable result when there is no file list to give a checker."""
    if ctx.changed is None:
        return _unverifiable(row, "no_git")
    if not ctx.changed:
        return _unverifiable(row, "no_changed_files")
    return None


def _needs_review(ctx: Ctx, row: Row) -> Optional[Dict[str, Any]]:
    if ctx.review is None:
        return _unverifiable(row, "no_review_output")
    if not ctx.review.is_file():
        return _unverifiable(row, "review_output_unreadable")
    return None


def _write_atomic(path: Path, text: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    fd, tmp = tempfile.mkstemp(prefix="." + path.name + ".", dir=str(path.parent))
    try:
        with os.fdopen(fd, "w", encoding="utf-8") as fh:
            fh.write(text)
        os.replace(tmp, str(path))
    except BaseException:
        try:
            os.unlink(tmp)
        except OSError:
            pass
        raise


# --- pre-review checks ---------------------------------------------------------

def build_smoke(ctx: Ctx, row: Row) -> Dict[str, Any]:
    missing = _changed_or(ctx, row)
    if missing:
        return missing
    if not any(not p.startswith(".writ/") and not p.endswith(".md") for p in ctx.changed or []):
        return _skip(row, "no_source_changed")
    out = _invoke(ctx, row, ["check", "--project", str(ctx.repo)], "json", own_timeout=360)
    return _json_verdict(row, out, "gate2")


def arch_lint(ctx: Ctx, row: Row) -> Dict[str, Any]:
    out = _invoke(ctx, row, ["detect", "--repo", str(ctx.repo)], "check")
    if "_ok" not in out:
        return out
    data = out["_ok"]
    if data["line1"] != "pass":
        return _check_shape(row, out)
    tools = [ln[len("tool:"):].strip() for ln in data["detail"] if ln.startswith("tool:")]
    commands = [ln[len("command:"):].strip() for ln in data["detail"] if ln.startswith("command:")]
    failures: List[str] = []
    for cmd in commands:
        limit = min(DEFAULT_TIMEOUT, ctx.cap) if ctx.cap else DEFAULT_TIMEOUT
        try:
            proc = subprocess.run(shlex.split(cmd), cwd=str(ctx.repo), capture_output=True,
                                  text=True, timeout=limit)
            if proc.returncode != 0:
                failures.append("command_failed %s (exit %d)" % (cmd, proc.returncode))
        except subprocess.TimeoutExpired:
            failures.append("command_timeout %s" % cmd)
        except (OSError, ValueError) as exc:
            failures.append("command_failed %s (%s)" % (cmd, exc))
    reasons = failures + (tools or ["none — see .writ/docs/architecture-lint.md"])
    return _result(row, "fail" if failures else "pass", reasons, out["command"], out["exit"],
                   None, data["detail"], data["summary"])


ARCH_SUFFIX = {"via-eslint": " (via eslint)", "via-tests": " (via tests)",
               "not-installed": " (not installed)"}


def arch_lint_line(result: Dict[str, Any]) -> str:
    """The story report's `arch-lint:` line from the arch-lint check."""
    if result.get("verdict") == "unverifiable":
        return "arch-lint: unverifiable (%s)" % (result.get("reasons") or ["?"])[0]
    names = []
    for line in result.get("detail") or []:
        parts = line[len("tool:"):].split() if line.startswith("tool:") else []
        if len(parts) >= 2:
            names.append(parts[0] + ARCH_SUFFIX.get(parts[1], ""))
    if not names:
        return "arch-lint: none — see .writ/docs/architecture-lint.md"
    return "arch-lint: %s" % ", ".join(names)


def change_surface(ctx: Ctx, row: Row) -> Dict[str, Any]:
    ctx.inputs["change_surface"] = "full-stack"
    missing = _changed_or(ctx, row)
    if missing:
        ctx.inputs["change_surface"] = "full-stack (unverifiable: %s)" % missing["reasons"][0]
        return missing
    out = _invoke(ctx, row, ["classify", "--changed"] + list(ctx.changed or []), "json")
    if "_ok" not in out:
        ctx.inputs["change_surface"] = "full-stack (unverifiable: helper_error)"
        return out
    surface = out["_ok"].get("class")
    if not isinstance(surface, str) or not surface:
        ctx.inputs["change_surface"] = "full-stack (unverifiable: no class)"
        return _unverifiable(row, "helper_error: no class in JSON", out["command"], out["exit"])
    ctx.inputs["change_surface"] = surface
    return _result(row, "pass", [surface], out["command"], out["exit"])


def crossings(ctx: Ctx, row: Row) -> Dict[str, Any]:
    boundary = ctx.state / ("boundary-%s.json" % ctx.stem)
    if not boundary.is_file():
        ctx.inputs["route"] = {"agent": "evaluator-agent", "reasons": ["no_boundary_map"]}
        return _skip(row, "no_boundary_map")
    result = _changed_or(ctx, row)
    if result is None:
        surface = str(ctx.inputs.get("change_surface", "full-stack")).split(" ")[0]
        args = ["crossings", "--map", str(boundary), "--changed"] + list(ctx.changed or []) + [
            "--story", str(ctx.story), "--surface", surface, "--repo", str(ctx.repo)]
        out = _invoke(ctx, row, args, "json")
        if "_ok" in out:
            data = out["_ok"]
            verdict = data.get("verdict")
            reasons = [str(r) for r in data.get("reasons") or []]
            if verdict == "pass" and data.get("route") in ("evaluator-agent", "review-agent"):
                ctx.inputs["route"] = {"agent": data["route"], "reasons": reasons}
                return _result(row, "pass", reasons or [data["route"]], out["command"], out["exit"])
            why = reasons[0] if reasons else "verdict %s" % verdict
            result = _unverifiable(row, why, out["command"], out["exit"])
        else:
            result = out
    ctx.inputs["route"] = {"agent": "review-agent",
                           "reasons": ["unverifiable: %s" % result["reasons"][0]]}
    return result


def _switch(ctx: Ctx, name: str) -> str:
    row = Row("switch", "", "review-override.py", lambda c, r: {})
    out = _invoke(ctx, row, ["switch", "--name", name, "--repo", str(ctx.repo)], "check")
    state = out.get("_ok", {}).get("line1")
    # A switch is on by default; a switch that cannot be read stays on.
    return state if state in ("on", "off") else "on"


def blast_radius(ctx: Ctx, row: Row) -> Dict[str, Any]:
    for name in ("safety-fact", "reviewer-filters", "evidence-gate"):
        ctx.inputs[name.replace("-", "_")] = _switch(ctx, name)
    switch = ctx.inputs.pop("safety_fact")
    ctx.inputs["blast_radius"] = None
    ctx.inputs["safety_fact"] = "not on route"
    if ctx.inputs.get("route", {}).get("agent") != "review-agent":
        return _skip(row, "not_on_route")
    ctx.inputs["safety_fact"] = "off"
    if switch != "on":
        return _skip(row, "safety_fact_off")
    missing = _changed_or(ctx, row)
    if missing:
        return missing
    out = _invoke(ctx, row, ["blast-radius", "--changed"] + list(ctx.changed or []) +
                  ["--repo", str(ctx.repo)], "json")
    if "_ok" not in out:
        return out
    target = ctx.state / ("blast-radius-%s.json" % ctx.stem)
    try:
        _write_atomic(target, out["stdout"])
    except OSError:
        return _unverifiable(row, "blast_radius_write_failed", out["command"], out["exit"])
    ctx.inputs["blast_radius"] = str(target)
    ctx.inputs["safety_fact"] = "on"
    verdict = out["_ok"].get("verdict")
    reasons = [str(r) for r in out["_ok"].get("reasons") or []]
    if verdict not in ("pass", "unverifiable"):
        verdict = "unverifiable"
        reasons = ["helper_error: no verdict in JSON"] + reasons
    return _result(row, verdict, reasons, out["command"], out["exit"])


# --- post-review checks --------------------------------------------------------

def _pre_inputs(ctx: Ctx) -> Dict[str, Any]:
    path = ctx.state / ("story-gate-%s-pre-review.json" % ctx.stem)
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, ValueError):
        return {}
    inputs = data.get("inputs") if isinstance(data, dict) else None
    return inputs if isinstance(inputs, dict) else {}


def evidence_args(review: str, changed: List[str], tests_output: Optional[str],
                  checks: Optional[str], manifest: str, prior: bool) -> List[str]:
    """`review-override.py evidence` arguments: always `--manifest-out`, and
    `--prior` once the manifest exists. The checker runs with cwd = the repo."""
    args = ["evidence", "--review-output", review]
    if changed:
        args += ["--changed"] + list(changed)
    if tests_output:
        args += ["--tests-output", tests_output]
    if checks:
        args += ["--checks", checks]
    if prior:
        args += ["--prior", manifest]
    return args + ["--manifest-out", manifest, "--timeout", "60"]


def shadow_args(story: str, tests_output: str, diff: str, review: str) -> List[str]:
    """`jev-judge.py ac-shadow` arguments: it reuses the saved Gate 3 files."""
    return ["ac-shadow", "--story", story, "--tests-output", tests_output, "--diff", diff,
            "--review-output", review]


def override(ctx: Ctx, row: Row) -> Dict[str, Any]:
    early = _needs_review(ctx, row)
    if early:
        return early
    args = ["check", "--spec", str(ctx.spec), "--story", str(ctx.story), "--repo", str(ctx.repo)]
    if ctx.new_source:
        args += ["--new-files"] + ctx.new_source
    tests, note = _without_repros(ctx, ctx.tests or [])
    if tests:
        args += ["--tests"] + tests
    # No skip when only repros changed: `check` still runs ac-trace.
    result = _check_shape(row, _invoke(ctx, row, args, "check"), "gate1")
    if note:
        result["reasons"] = list(result.get("reasons") or []) + [note]
    return result


def safety_fact(ctx: Ctx, row: Row) -> Dict[str, Any]:
    early = _needs_review(ctx, row)
    if early:
        return early
    if not ctx.pre:
        return _unverifiable(row, "no_pre_review_record")
    if ctx.pre.get("safety_fact") != "on" or not ctx.pre.get("blast_radius"):
        return _skip(row, str(ctx.pre.get("safety_fact") or "off"))
    args = ["safety-fact", "--review-output", str(ctx.review), "--repo", str(ctx.repo),
            "--blast-radius", str(ctx.pre["blast_radius"])]
    if ctx.tests_output:
        args += ["--tests-output", str(ctx.tests_output)]
    result = _check_shape(row, _invoke(ctx, row, args, "check"))
    if result["verdict"] == "fail":
        codes = " ".join(result["reasons"])
        result["restart"] = "gate1" if "safety_fact_contradicts_verdict" in codes else "gate3"
    return result


def evidence_runs(agent: Optional[str], manifest_exists: bool,
                  safety: Optional[Dict[str, Any]] = None) -> bool:
    """`evidence` runs on an agent FAIL, and on any verdict once the manifest
    exists (then with `--prior`), after `check`, `safety-fact`, and any
    re-spawn: never in a run whose safety-fact result re-spawns Gate 3, since
    that review is replaced and its repros must not reach the manifest."""
    if _respawns(safety):
        return False
    return agent == "FAIL" or manifest_exists


def _respawns(safety: Optional[Dict[str, Any]]) -> bool:
    return bool(safety) and safety.get("verdict") == "fail" and safety.get("restart") == "gate3"


def evidence(ctx: Ctx, row: Row) -> Dict[str, Any]:
    early = _needs_review(ctx, row)
    if early:
        return early
    prior = ctx.manifest.is_file()
    safety = ctx.results.get("gate3_safety_fact")
    if _respawns(safety):
        return _skip(row, "safety_fact_respawn_first")
    if not evidence_runs(ctx.agent, prior, safety):
        return _skip(row, "not run (%s)" % (ctx.agent or "no verdict"))
    if ctx.changed is None:
        return _unverifiable(row, "no_git")
    args = evidence_args(str(ctx.review), ctx.changed,
                         str(ctx.tests_output) if ctx.tests_output else None,
                         str(ctx.checks) if ctx.checks.is_file() else None,
                         str(ctx.manifest), prior)
    result = _check_shape(row, _invoke(ctx, row, args, "check", own_timeout=360))
    if result["verdict"] == "fail":
        codes = " ".join(result["reasons"])
        result["restart"] = "gate3-blocked" if "repro_mutated_tree" in codes else "gate1"
    return result


def agent_verdict(ctx: Ctx, row: Row) -> Dict[str, Any]:
    """Gate 3's decision, the same one the record's `gate3` key holds. Rows 1-4a
    are decided by another check's fail, so this line reads `skip` there and the
    tally counts that catch once; rows 5-9 are the agent verdict after evidence."""
    early = _needs_review(ctx, row)
    if early:
        return early
    if ctx.agent is None:
        return _unverifiable(row, ctx.agent_why or "no_verdict_line")
    r = ctx.results
    decision = decide_gate3(ctx.agent, r.get("gate3_override"), r.get("gate3_safety_fact"),
                            r.get("gate3_evidence"), ctx.evidence_gate)
    if decision["row"] in ("1", "2", "3", "4", "4a"):
        return _skip(row, "FAIL (row %s: %s)" % (decision["row"], decision["why"]))
    if decision["verdict"] == "FAIL":
        return _result(row, "fail", ["FAIL (row %s: %s)" % (decision["row"], decision["why"])],
                       restart="gate1")
    return _result(row, "pass", ["%s (row %s)" % (decision["verdict"], decision["row"])])


def drift_format(ctx: Ctx, row: Row) -> Dict[str, Any]:
    early = _needs_review(ctx, row)
    if early:
        return early
    args = ["check", "--story", str(ctx.story)]
    log = ctx.spec / "drift-log.md"
    if log.is_file():
        args += ["--drift-log", str(log)]
    args += ["--review-output", str(ctx.review)]
    return _check_shape(row, _invoke(ctx, row, args, "check"), "gate3-blocked")


def coverage(ctx: Ctx, row: Row) -> Dict[str, Any]:
    if ctx.new_source is None:
        return _unverifiable(row, "no_git")
    args = ["coverage", "--project", str(ctx.repo)]
    if ctx.new_source:
        args += ["--new-files"] + ctx.new_source
    return _json_verdict(row, _invoke(ctx, row, args, "json"), "gate4")


def authenticity(ctx: Ctx, row: Row) -> Dict[str, Any]:
    tests = ctx.tests
    if tests is None:
        return _unverifiable(row, "no_git")
    if not tests:
        return _skip(row, "no_test_files")
    tests, repro_note = _without_repros(ctx, tests)
    # test-integrity.py authenticity reads module specifiers, so it handles only
    # the stacks .writ/docs/quality-signal-classification.md supports (Node /
    # TypeScript, Python). It fails every shell test by construction, so those
    # stay out of its input and the reason line counts them.
    kept = [p for p in tests if p.endswith(AUTHENTICITY_SUFFIXES)]
    dropped = [p for p in tests if p not in kept]
    notes = [repro_note] if repro_note else []
    if dropped:
        kind = "shell" if all(p.endswith(SHELL_SUFFIXES) for p in dropped) else "unsupported-stack"
        notes.append("skipped %d %s test(s): unsupported_stack" % (len(dropped), kind))
    if not kept:
        return _result(row, "skip", notes or ["no_test_files"])
    args = ["authenticity", "--project", str(ctx.repo), "--tests"] + kept
    result = _json_verdict(row, _invoke(ctx, row, args, "json"), "gate4")
    if notes:
        result["reasons"] = list(result.get("reasons") or []) + notes
    return result


def repro_order(ctx: Ctx, row: Row) -> Dict[str, Any]:
    if not ctx.git_ok:
        return _unverifiable(row, "no_git")
    log = _git(ctx.repo, "log", "--format=%B", ctx.base + "..HEAD") or ""
    if not REPRO_LINE.search(log):
        return _skip(row, "no_repro_commit")
    out = _invoke(ctx, row, ["check", "--repo", str(ctx.repo), "--base", ctx.base], "check")
    return _check_shape(row, out)  # no restart: a fail marks the story DEGRADED


def jev_shadow(ctx: Ctx, row: Row) -> Dict[str, Any]:
    early = _needs_review(ctx, row)
    if early:
        return early
    status = _invoke(ctx, row, ["status", "--repo", str(ctx.repo)], "check")
    if status.get("_ok", {}).get("line1") != "pass":
        return _skip(row, "jev off")
    if not ctx.git_ok:
        return _unverifiable(row, "no_git")
    diff_path = ctx.state / ("story-diff-%s.patch" % ctx.stem)
    try:
        _write_atomic(diff_path, _git(ctx.repo, "diff", ctx.base) or "")
    except OSError:
        return _unverifiable(row, "diff_write_failed")
    args = shadow_args(str(ctx.story), str(ctx.tests_output or os.devnull), str(diff_path),
                       str(ctx.review)) + ["--repo", str(ctx.repo)]
    return _check_shape(row, _invoke(ctx, row, args, "check"))


CHECKS: Dict[str, List[Row]] = {
    "pre-review": [
        Row("gate2_build_smoke", "gate2_build", "build-smoke.py", build_smoke),
        Row("gate2_arch_lint", "gate2_build", "arch-lint.py", arch_lint, counted=False),
        Row("gate2_5_change_surface", "gate2_5_surface", "change-surface.py", change_surface),
        Row("gate0_5_crossings", "gate0_5_boundary", "boundary-map.py", crossings),
        Row("gate2_5_blast_radius", "gate2_5_surface", "change-surface.py", blast_radius),
    ],
    "post-review": [
        Row("gate3_override", "gate3_review", "review-override.py", override),
        Row("gate3_safety_fact", "gate3_review", "review-override.py", safety_fact),
        Row("gate3_evidence", "gate3_review", "review-override.py", evidence),
        Row("gate3_verdict", "gate3_review", None, agent_verdict),
        Row("gate3_5_drift_format", "gate3_5_drift", "drift-format.py", drift_format),
        Row("gate4_coverage", "gate4_tests", "test-integrity.py", coverage),
        Row("gate4_authenticity", "gate4_tests", "test-integrity.py", authenticity),
        Row("gate1_repro_order", "gate1_coding", "repro-order.py", repro_order),
        Row("gate3_jev_shadow", "gate3_review", "jev-judge.py", jev_shadow, counted=False),
    ],
}


def _codes(result: Optional[Dict[str, Any]]) -> List[str]:
    return [r.split()[0] for r in (result or {}).get("reasons", []) if r.split()]


def _failed(result: Optional[Dict[str, Any]]) -> bool:
    return bool(result) and result.get("verdict") == "fail"


def decide_gate3(agent: Optional[str], check: Optional[Dict[str, Any]],
                 safety: Optional[Dict[str, Any]], evidence_result: Optional[Dict[str, Any]],
                 evidence_gate: str = "on") -> Dict[str, Any]:
    """Gate 3's first-match decision. Each result is a check result ({verdict,
    reasons}) or None when it did not run. Returns {verdict, restart, row, why};
    verdict is PASS, FAIL, or PAUSE, and restart is set only on FAIL.

    Rows: 1 `repro_mutated_tree` -> BLOCKED escalation, restart Gate 3
    (`gate3-blocked`); 2 `check` fail -> recode; 3 `safety_fact_contradicts_verdict`
    -> recode; 4 `safety_fact_missing` / `safety_fact_below_floor` -> re-spawn
    (`gate3`); 4a `repro_removed`/`repro_modified`/`repro_still_failing` ->
    recode; 5 agent PASS or PAUSE -> that verdict; 6 `evidence_gate` off -> the
    FAIL stands; 7 evidence line 1 `fail` -> recode with the `confirmed`
    findings; 8 evidence `unverifiable`, exit 2, or no helper -> the FAIL
    stands, never DEGRADED; 9 evidence line 1 `pass` -> PASS."""
    ev = _codes(evidence_result)
    if _failed(evidence_result) and "repro_mutated_tree" in ev:
        return {"verdict": "FAIL", "restart": "gate3-blocked", "row": "1",
                "why": "repro_mutated_tree"}
    if _failed(check):
        return {"verdict": "FAIL", "restart": "gate1", "row": "2",
                "why": "check fail: %s" % ((check or {}).get("reasons") or ["fail"])[0]}
    sf = _codes(safety)
    if _failed(safety) and "safety_fact_contradicts_verdict" in sf:
        return {"verdict": "FAIL", "restart": "gate1", "row": "3",
                "why": "safety_fact_contradicts_verdict"}
    if _failed(safety) and ("safety_fact_missing" in sf or "safety_fact_below_floor" in sf):
        why = next(r for r in (safety or {})["reasons"]
                   if r.split()[0] in ("safety_fact_missing", "safety_fact_below_floor"))
        return {"verdict": "FAIL", "restart": "gate3", "row": "4", "why": why}
    if _failed(evidence_result) and any(c in ev for c in PRIOR_CODES):
        why = next(r for r in (evidence_result or {})["reasons"] if r.split()[0] in PRIOR_CODES)
        return {"verdict": "FAIL", "restart": "gate1", "row": "4a", "why": why}
    if agent in ("PASS", "PAUSE"):
        return {"verdict": agent, "restart": None, "row": "5", "why": "agent %s" % agent}
    if evidence_gate == "off":
        return {"verdict": "FAIL", "restart": "gate1", "row": "6", "why": "evidence_gate off"}
    line1 = (evidence_result or {}).get("verdict")
    if line1 == "fail":
        return {"verdict": "FAIL", "restart": "gate1", "row": "7",
                "why": (evidence_result or {}).get("summary") or "confirmed"}
    if line1 == "pass":
        return {"verdict": "PASS", "restart": None, "row": "9", "why": "no finding confirmed"}
    reason = ((evidence_result or {}).get("reasons") or ["not run"])[0]
    return {"verdict": "FAIL", "restart": "gate1", "row": "8", "why": "evidence %s" % reason}


# Every form `evidence_gate_line` prints, after `evidence-gate: `.
EVIDENCE_GATE_FORMS = ("off", "not run (PASS|PAUSE)", "blocked (<reason>)", "fail (<reason>)",
                       "unverifiable (<reason>)",
                       "<c> confirmed, <a> advisory, <u> unverifiable")
COUNTS = re.compile(r"\((\d+ confirmed, \d+ advisory, \d+ unverifiable)\)\s*$")


def evidence_gate_line(agent: Optional[str], evidence_result: Optional[Dict[str, Any]],
                       evidence_gate: str = "on") -> str:
    """The story report's `evidence-gate:` line."""
    if evidence_gate == "off":
        return "evidence-gate: off"
    reasons = (evidence_result or {}).get("reasons") or []
    codes = _codes(evidence_result)
    if codes and codes[0] == "repro_mutated_tree":
        return "evidence-gate: blocked (%s)" % reasons[0]
    if codes and codes[0] in PRIOR_CODES and _failed(evidence_result):
        return "evidence-gate: fail (%s)" % reasons[0]
    if agent in ("PASS", "PAUSE"):
        return "evidence-gate: not run (%s)" % agent
    counts = COUNTS.search((evidence_result or {}).get("summary") or "")
    if (evidence_result or {}).get("verdict") in ("pass", "fail") and counts:
        return "evidence-gate: %s" % counts.group(1)
    return "evidence-gate: unverifiable (%s)" % (reasons[0] if reasons else "no helper")


def safety_fact_line(result: Optional[Dict[str, Any]]) -> str:
    """The story report's `safety-fact:` line."""
    if not result or result.get("verdict") == "skip":
        why = ((result or {}).get("reasons") or ["off"])[0]
        return "safety-fact: %s" % ("not on route" if why == "not on route" else "off")
    fields = {}
    for line in result.get("detail") or []:
        key, _, value = line.partition(":")
        fields[key.strip()] = value.strip()
    rung = dict(p.split("=", 1) for p in fields.get("rung", "").split() if "=" in p)
    if not rung:
        return "safety-fact: %s (%s)" % (result.get("verdict"), (result.get("reasons") or ["?"])[0])
    return "safety-fact: %s (claimed %s) — %s" % (rung.get("measured", "none"),
                                                  rung.get("claimed", "none"),
                                                  fields.get("fact", ""))


# --- run -----------------------------------------------------------------------

def _now() -> _dt.datetime:
    return _dt.datetime.now(_dt.timezone.utc)


def _read_agent(ctx: Ctx) -> None:
    """The Gate 3 agent's verdict from its heading line; the first one wins, so a
    later mention of the field in the review's prose never changes it."""
    if ctx.review is None or not ctx.review.is_file():
        return
    try:
        text = ctx.review.read_text(encoding="utf-8", errors="replace")
    except OSError:
        ctx.agent_why = "review_output_unreadable"
        return
    match = AGENT_VERDICT.search(text)
    verdict = match.group(1).upper() if match else ""
    ctx.agent = verdict if verdict in ("PASS", "FAIL", "PAUSE") else None
    ctx.agent_why = "" if ctx.agent else "no_verdict_line"


def run(args: argparse.Namespace) -> int:
    ctx = Ctx(args)
    if ctx.phase == "post-review":
        _read_agent(ctx)
        ctx.pre = _pre_inputs(ctx)
        ctx.evidence_gate = ctx.pre.get("evidence_gate") or _switch(ctx, "evidence-gate")
    for row in CHECKS[ctx.phase]:
        ctx.results[row.id] = row.run(ctx, row)
    results = [ctx.results[row.id] for row in CHECKS[ctx.phase]]
    counted_fails = [x for x in results if x["counted"] and x["verdict"] == "fail"]
    verdict = "fail" if counted_fails else "pass"
    gate3 = None
    if ctx.phase == "post-review" and ctx.review is not None and ctx.agent is not None:
        r = ctx.results
        gate3 = decide_gate3(ctx.agent, r["gate3_override"], r["gate3_safety_fact"],
                             r["gate3_evidence"], ctx.evidence_gate)
    if gate3 and gate3["verdict"] == "FAIL":
        restart = gate3["restart"]
    else:
        restart = next((x["restart"] for x in counted_fails if x["restart"]), None)
    if verdict == "pass":
        restart = None

    at = _now()
    record: Dict[str, Any] = {
        "schema": SCHEMA, "story": ctx.stem, "phase": ctx.phase, "head_sha": ctx.head,
        "dirty": ctx.dirty, "base": ctx.base, "at": at.strftime("%Y-%m-%dT%H:%M:%SZ"),
        "verdict": verdict, "restart": restart, "checks": results,
    }
    if ctx.phase == "pre-review":
        record["inputs"] = ctx.inputs
    if gate3:
        record["gate3"] = gate3

    write_failed = False
    text = json.dumps(record, sort_keys=True)
    try:
        _write_atomic(ctx.state / ("story-gate-%s-%s.json" % (ctx.stem, ctx.phase)), text + "\n")
        stamp = at.strftime("%Y%m%dT%H%M%S%fZ")
        _write_atomic(ctx.state / "story-gate-history" /
                      ("%s-%s-%s.json" % (ctx.stem, ctx.phase, stamp)), text + "\n")
    except OSError:
        write_failed = True

    out = [verdict]
    for x in results:
        out.append("check: %s %s (%s)" % (x["id"], x["verdict"], (x["reasons"] or ["ok"])[0]))
    if restart:
        out.append("restart: %s" % restart)
    if gate3:
        out.append("gate3: %s (row %s: %s)" % (gate3["verdict"], gate3["row"], gate3["why"]))
    if ctx.phase == "post-review":
        out.append(safety_fact_line(ctx.results["gate3_safety_fact"]))
        out.append(evidence_gate_line(ctx.agent, ctx.results["gate3_evidence"], ctx.evidence_gate))
    if ctx.phase == "pre-review":
        route = ctx.inputs.get("route", {"agent": "review-agent", "reasons": []})
        joined = "; ".join(route["reasons"])
        out.append(arch_lint_line(ctx.results["gate2_arch_lint"]))
        out.append("route: %s%s" % (route["agent"], " (%s)" % joined if joined else ""))
        out.append("change_surface: %s" % ctx.inputs.get("change_surface"))
        out.append("blast_radius: %s" % (ctx.inputs.get("blast_radius") or "(none)"))
        out.append("safety_fact: %s" % ctx.inputs.get("safety_fact"))
        out.append("reviewer_filters: %s" % ctx.inputs.get("reviewer_filters"))
        out.append("evidence_gate: %s" % ctx.inputs.get("evidence_gate"))
    if write_failed:
        out.append("reason: record_write_failed")
    fails = sum(1 for x in results if x["verdict"] == "fail")
    unver = sum(1 for x in results if x["verdict"] == "unverifiable")
    out.append("story-gate: %s (phase %s, %d checks, %d fail, %d unverifiable)"
               % (verdict, ctx.phase, len(results), fails, unver))
    out.append(text)
    print("\n".join(out))
    return 1 if verdict == "fail" else 0


# --- tally ---------------------------------------------------------------------

def tally(args: argparse.Namespace) -> int:
    state = Path(args.state_dir).resolve() if args.state_dir else Path(".writ/state").resolve()
    history = state / "story-gate-history"
    files = sorted(history.glob("*.json")) if history.is_dir() else []
    counts: Dict[str, Dict[str, int]] = {}
    records = 0
    bad: List[str] = []
    for path in files:
        try:
            data = json.loads(path.read_text(encoding="utf-8"))
            checks = data["checks"] if data.get("schema") == SCHEMA else None
        except (OSError, ValueError, KeyError, AttributeError, TypeError):
            checks = None
        if not isinstance(checks, list):
            bad.append(path.name)
            continue
        records += 1
        fails = [c for c in checks if isinstance(c, dict) and c.get("verdict") == "fail"]
        counted = [c for c in fails if c.get("counted", True)]
        for c in checks:
            if not isinstance(c, dict) or "id" not in c:
                continue
            row = counts.setdefault(str(c["id"]), {"runs": 0, "fails": 0, "sole": 0})
            if c.get("verdict") == "skip":
                continue
            row["runs"] += 1
            if c.get("verdict") == "fail":
                row["fails"] += 1
                if len(counted) == 1 and counted[0] is c:
                    row["sole"] += 1
    if not records:
        lines = ["unverifiable", "reason: no_records"] + ["reason: unreadable %s" % b for b in bad]
        lines.append("story-gate tally: unverifiable (0 records)")
        print("\n".join(lines))
        return 0
    lines = ["pass"]
    for cid in sorted(counts):
        c = counts[cid]
        lines.append("tally: %s runs=%d fails=%d sole_catches=%d"
                     % (cid, c["runs"], c["fails"], c["sole"]))
    lines += ["reason: unreadable %s" % b for b in bad]
    lines.append("story-gate tally: pass (%d records, %d checks)" % (records, len(counts)))
    print("\n".join(lines))
    return 0


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__,
                                     formatter_class=argparse.RawDescriptionHelpFormatter)
    sub = parser.add_subparsers(dest="action")
    sub.required = True
    p = sub.add_parser("run", help="run one phase's checks and write the record")
    p.add_argument("--phase", required=True, choices=sorted(CHECKS))
    p.add_argument("--story", required=True)
    p.add_argument("--spec", required=True)
    p.add_argument("--base", required=True, help="the commit before the story's first Gate 1 spawn")
    p.add_argument("--repo", default=".")
    p.add_argument("--review-output", help="the saved Gate 3 agent output (post-review)")
    p.add_argument("--tests-output", help="the orchestrator's recorded test run (post-review)")
    p.add_argument("--checks", help="Gate 2's saved check commands (default <state-dir>/gate2-checks-<stem>.txt)")
    p.add_argument("--manifest", help="evidence manifest (default <state-dir>/evidence-<stem>.json)")
    p.add_argument("--state-dir", help="default <repo>/.writ/state")
    p.set_defaults(func=run)
    t = sub.add_parser("tally", help="count runs, fails, and sole catches per check id")
    t.add_argument("--state-dir", help="default .writ/state")
    t.set_defaults(func=tally)
    return parser


def main(argv: Optional[List[str]] = None) -> int:
    args = build_parser().parse_args(argv)
    try:
        return args.func(args)
    except UsageError as exc:
        print("story-gate: %s" % exc, file=sys.stderr)
        return 2


if __name__ == "__main__":
    sys.exit(main())
