#!/usr/bin/env python3
"""Unit tests for scripts/pipeline-baseline.py `run` and `ingest` (Story 4 of
2026-09-05-phase11-repair-and-baseline).

The fixture yuss is Story 3's `Repo` (imported by path from
`test_pipeline_baseline.py`), extended with a parent commit that carries the
active spec folder and a `Not Started` story — the state a real replay starts
from. Every subprocess goes through `Dispatcher`, a fake keyed on `argv[0]`:

* `git` — real only when the target (`-C <dir>` or `cwd`) is under the test's
  temp root; against the fixture yuss it is REFUSED unless the subcommand is
  `show` or `rev-parse` (Business Rule 2). The isolation test therefore does a
  real `git init` + `fetch --depth 1` + `checkout FETCH_HEAD`.
* `claude` — `Popen` only; writes a stream-json fixture to the given stdout
  handle (or raises `TimeoutExpired` on `wait`). Never the real binary.
* `pnpm` / `bash` — canned JSON and exit codes.
* `python3` — Writ's `build-smoke.py` / `test-integrity.py` gate scripts:
  canned `{"verdict": ...}` JSON, exit codes, garbage, or a timeout.

`os.killpg` is patched so the timeout path never signals a real process group.
These tests do `git init` and must run outside a sandbox.
"""

from __future__ import annotations

import contextlib
import importlib.util
import io
import json
import os
import shutil
import subprocess
import sys
import unittest
from pathlib import Path
from tempfile import TemporaryDirectory
from typing import Optional
from unittest import mock

HERE = Path(__file__).resolve().parent
_t3_spec = importlib.util.spec_from_file_location("test_pipeline_baseline", HERE / "test_pipeline_baseline.py")
t3 = importlib.util.module_from_spec(_t3_spec)
sys.modules["test_pipeline_baseline"] = t3
_t3_spec.loader.exec_module(t3)  # type: ignore[union-attr]

pb = t3.pb                      # the one loaded module object, shared with Story 3's tests
Repo = t3.Repo
four_class_repo = t3.four_class_repo
CLEAN_TEST = t3.CLEAN_TEST
walk_strings = t3.walk_strings

_REAL_RUN, _REAL_POPEN = subprocess.run, subprocess.Popen


def REAL_RUN(argv, *args, **kwargs):
    """The genuine subprocess.run. It looks Popen up on the module at call
    time, so the dispatcher's Popen patch is lifted for the duration."""
    with mock.patch.object(subprocess, "Popen", _REAL_POPEN):
        return _REAL_RUN(argv, *args, **kwargs)


FAKE_KEY = "sk-ant-fake-for-tests"   # never a real credential
FOLDER = "2026-05-05-widget"
STORY_STEM = "story-1-widget"
STORY_ID = "%s/%s" % (FOLDER, STORY_STEM)
STORY_REL = ".writ/specs/%s/user-stories/%s.md" % (FOLDER, STORY_STEM)
TEST_FILE = "lib/__tests__/widget.test.ts"
ARCHIVE_REL = ".writ/specs/archive/%s/user-stories/%s.md" % (FOLDER, STORY_STEM)


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------


def story_text(status: str, commit: Optional[str] = None, wwb: bool = False) -> str:
    lines = ["# Story 1: Widget", "", "> **Status:** %s" % status]
    if commit:
        lines.append("> **Commit:** %s" % commit)
    lines += ["> **Priority:** High", "", "## User Story", "", "As a user I want a widget.", ""]
    if wwb:
        lines += ["## What Was Built", "", "- lib/widget.ts", ""]
    return "\n".join(lines)


def replay_repo(root: Path) -> tuple:
    """A yuss whose *parent* commit carries the active spec folder (story Not
    Started), a Claude-platform Writ manifest, and a jest package.json; the
    story commit changes source + test and archives the story as Completed.

    Returns (repo, parent_sha, story_sha)."""
    repo = Repo(root)
    parent = repo.commit({
        ".writ/specs/%s/spec.md" % FOLDER: "# Widget spec\n",
        ".writ/specs/%s/spec-lite.md" % FOLDER: "# Widget lite\n",
        ".writ/specs/%s/sub-specs/technical-spec.md" % FOLDER: "# Tech\n",
        ".writ/specs/%s/sub-specs/nested/api.md" % FOLDER: "# API\n",
        STORY_REL: story_text("Not Started"),
        ".claude/.writ-manifest": "# Writ Manifest\n# mode: copy\n# platform: claude\n# version: e1a3fd1\n"
                                  "aaaa  commands/_preamble.md\nbbbb  commands/implement-story.md\n",
        ".claude/commands/implement-story.md": "# /implement-story\n",
        "package.json": json.dumps({"name": "yuss", "scripts": {"test": "jest"}}) + "\n",
        "pnpm-lock.yaml": "lockfileVersion: 9\n",
        "lib/widget.ts": "export const widget = () => 0;\n",
    }, "chore: parent state")
    repo.write(STORY_REL, None)
    story = repo.commit({
        "lib/widget.ts": "export const widget = () => 1;\n",
        TEST_FILE: CLEAN_TEST,
        ARCHIVE_REL: story_text("Completed ✅", wwb=True),
    }, "feat: Story 1 widget")
    return repo, parent, story


def selection_entry(parent: str, story: str, test_files: Optional[list] = None) -> dict:
    values = {
        "story_path": ARCHIVE_REL, "spec_folder": FOLDER, "story_id": STORY_ID,
        "story_commit": story, "parent_sha": parent, "parent_is_merge": False,
        "surface_class": "refactor", "eligible_classes": ["refactor"],
        "test_files": [TEST_FILE] if test_files is None else test_files,
        "criteria_values": {"status": "Completed"},
    }
    return {k: values[k] for k in pb.SELECTION_KEYS}


def write_baseline(path: Path, entries: list, head: str, model: str = pb.DEFAULT_MODEL,
                   runs: Optional[list] = None, runs_per_story=None) -> dict:
    doc = {
        "schema": pb.SCHEMA, "model": model, "generated_at": "2026-09-06T00:00:00Z",
        "yuss_head": head, "runs_per_story": runs_per_story,
        "criteria": {"status_required": "Completed"}, "selection": entries,
        "excluded": [], "rejection_tally": {}, "runs": runs or [],
    }
    assert tuple(doc) == pb.SCHEMA_KEYS
    pb.write_json(path, doc)
    return doc


def load(path: Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8"))


# -- stream-json fixture ------------------------------------------------------

USAGE = {"input_tokens": 10, "output_tokens": 20, "cache_read_input_tokens": 300, "cache_creation_input_tokens": 40}
TEMPLATE_MD = (
    "# /implement-story\n\n### ARCH_CHECK: [PROCEED/CAUTION/ABORT]\n\n### REVIEW_RESULT: [PASS/FAIL]\n"
    "AskQuestion({ title: 'x' })\nOn `STATUS: BLOCKED` apply the escalation.\n"
    "TEST_RESULT: [PASS/FAIL]\nDOCS_UPDATED: [YES/NO]\n"
)


def _assistant(blocks: list, usage: Optional[dict] = None) -> dict:
    return {"type": "assistant", "message": {"role": "assistant", "content": blocks,
                                             "usage": dict(usage or USAGE)}}


def _tool_use(tid: str, name: str, inputs: dict) -> dict:
    return {"type": "tool_use", "id": tid, "name": name, "input": inputs}


def _tool_result(tid: str, text) -> dict:
    content = text if isinstance(text, list) else [{"type": "text", "text": text}]
    return {"type": "user", "message": {"role": "user", "content": [
        {"type": "tool_result", "tool_use_id": tid, "content": content}]}}


def stream_events(*, subtype: str = "success", with_result: bool = True, final_text: str = "Story 1 Completed ✅",
                  ask: int = 1, review_fails: int = 1, text_fallback: bool = False) -> list:
    ev = [{"type": "system", "subtype": "init", "model": "claude-fable-5-1-20260801",
           "apiKeySource": "user", "claude_code_version": "2.1.260", "permissionMode": "bypassPermissions"}]
    # A Read of a command file: template strings must not count as verdicts,
    # interrupts, or STATUS: BLOCKED.
    ev.append(_assistant([_tool_use("t_read", "Read", {"file_path": "/x/.claude/commands/implement-story.md"})]))
    ev.append(_tool_result("t_read", TEMPLATE_MD))
    ev.append(_assistant([_tool_use("t_arch", "Task", {"subagent_type": "writ-architect"})]))
    ev.append(_tool_result("t_arch", "### ARCH_CHECK: CAUTION\n\nWatch the fee math."))
    ev.append(_assistant([_tool_use("t_code", "Task", {"subagent_type": "writ-coder"})]))
    # tool_result content as a plain string (both shapes occur)
    ev.append({"type": "user", "message": {"role": "user", "content": [
        {"type": "tool_result", "tool_use_id": "t_code", "content": "STATUS: BLOCKED\nFAILURE: flaky"}]}})
    for _ in range(ask):
        ev.append(_assistant([_tool_use("t_ask", "AskUserQuestion", {"questions": []})]))
        ev.append(_tool_result("t_ask", "retry"))
    n = 0
    for _ in range(review_fails):
        n += 1
        ev.append(_assistant([_tool_use("t_rev%d" % n, "Task", {"subagent_type": "writ-reviewer"})]))
        # --verbose echoes the subagent's own turns with parent_tool_use_id:
        # its usage, verdict text and STATUS lines are not the main thread's.
        sub = _assistant([{"type": "text", "text": "### REVIEW_RESULT: FAIL\nSTATUS: BLOCKED"}],
                         usage={"input_tokens": 7777, "output_tokens": 8888,
                                "cache_read_input_tokens": 0, "cache_creation_input_tokens": 0})
        sub["parent_tool_use_id"] = "t_rev%d" % n
        ev.append(sub)
        ev.append(_tool_result("t_rev%d" % n, "### REVIEW_RESULT: FAIL\n- issue"))
        # The orchestrator echoes the verdict in its own text; that echo must
        # not double the iteration count.
        ev.append(_assistant([{"type": "text", "text": "Review returned REVIEW_RESULT: FAIL; sending fixes back."}]))
    ev.append(_assistant([_tool_use("t_revok", "Task", {"subagent_type": "writ-reviewer"})]))
    ev.append(_tool_result("t_revok", "### REVIEW_RESULT: PASS"))
    ev.append(_assistant([_tool_use("t_test", "Agent", {"subagent_type": "writ-tester"})]))
    ev.append(_tool_result("t_test", "### TEST_RESULT: PASS\nCoverage threshold met: YES"))
    if text_fallback:
        ev.append(_assistant([{"type": "text", "text": "DOCS_UPDATED: NO — README unchanged"}]))
    else:
        ev.append(_assistant([_tool_use("t_docs", "Task", {"subagent_type": "writ-documenter"})]))
        ev.append(_tool_result("t_docs", "### DOCS_UPDATED: YES"))
    ev.append(_assistant([{"type": "text", "text": final_text}]))
    if with_result:
        ev.append({"type": "result", "subtype": subtype, "is_error": subtype != "success",
                   "duration_ms": 90_500, "num_turns": 42, "total_cost_usd": 12.25, "result": final_text,
                   "usage": {"input_tokens": 1000, "output_tokens": 2000,
                             "cache_read_input_tokens": 30000, "cache_creation_input_tokens": 4000}})
    return ev


def session_events() -> list:
    """`~/.claude/projects/*.jsonl` shape: no result event, per-line timestamps."""
    ev = []
    for i, e in enumerate(stream_events(with_result=False)):
        if e["type"] == "system":
            continue
        e = dict(e)
        e["timestamp"] = "2026-09-06T10:00:%02d.000Z" % (i % 60) if i < 60 else "2026-09-06T10:01:00.000Z"
        ev.append(e)
    ev[0]["timestamp"] = "2026-09-06T10:00:00.000Z"
    ev[-1]["timestamp"] = "2026-09-06T10:02:30.000Z"
    return ev


def main_thread_assistants(events: list) -> int:
    return sum(1 for e in events if e["type"] == "assistant" and not e.get("parent_tool_use_id"))


def gate_json(verdict: str, causes: Optional[list] = None) -> str:
    return json.dumps({"schema": "x-v1", "verdict": verdict, "findings": [], "unverifiable": causes or []})


def jest_json(passed: int, total: int) -> dict:
    return {"numPassedTests": passed, "numTotalTests": total, "numFailedTests": total - passed, "success": passed == total}


# ---------------------------------------------------------------------------
# Subprocess dispatcher
# ---------------------------------------------------------------------------


class FakeProc:
    def __init__(self, timeout: bool, ignores_term: bool = False, interrupt: bool = False) -> None:
        self.pid = 99_999_999
        self.returncode: Optional[int] = None
        self._timeout = timeout
        self._interrupt = interrupt
        self._raises = 2 if (timeout and ignores_term) else (1 if timeout else 0)
        self.waits: list = []

    def wait(self, timeout=None):
        self.waits.append(timeout)
        if self._interrupt and len(self.waits) == 1:
            raise KeyboardInterrupt()
        if len(self.waits) <= self._raises:
            raise subprocess.TimeoutExpired("claude", timeout)
        self.returncode = -15 if self._timeout else 0
        return self.returncode

    def poll(self):
        return self.returncode


class Dispatcher:
    """argv[0]-keyed fake for subprocess.run / subprocess.Popen."""

    YUSS_ALLOWED = {"show", "rev-parse"}

    def __init__(self, yuss: Path, tmp_root: Path, *, events: Optional[list] = None,
                 claude_timeout: bool = False, ignores_term: bool = False, interrupt: bool = False, on_claude=None,
                 jest_suite=(3, 3), jest_original=(1, 1), jest_exit: int = 0, jest_timeout: bool = False,
                 jest_writes_report: bool = True, jest_report_text: Optional[str] = None,
                 pnpm_install_exit: int = 0, pnpm_install_timeout: bool = False, install_version: str = "130b880",
                 install_exit: int = 0, build_smoke: Optional[dict] = None, test_integrity: Optional[dict] = None,
                 git_override=None, yuss_heads: Optional[list] = None) -> None:
        self.yuss = yuss.resolve()
        self.tmp_root = tmp_root.resolve()
        self.events = stream_events() if events is None else events
        self.claude_timeout, self.ignores_term, self.interrupt = claude_timeout, ignores_term, interrupt
        self.on_claude = on_claude
        self.jest_suite, self.jest_original, self.jest_exit = jest_suite, jest_original, jest_exit
        self.jest_timeout = jest_timeout
        # a jest that exits without writing --outputFile (crash, OOM), or one
        # that writes something other than its JSON report
        self.jest_writes_report, self.jest_report_text = jest_writes_report, jest_report_text
        self.pnpm_install_exit, self.pnpm_install_timeout = pnpm_install_exit, pnpm_install_timeout
        self.install_version, self.install_exit = install_version, install_exit
        # gate scripts: {"verdict": ..., "exit": n, "causes": [...]} or
        # {"stdout": raw, "exit": n} or {"timeout": True}
        self.build_smoke = {"verdict": "pass"} if build_smoke is None else build_smoke
        self.test_integrity = {"verdict": "pass"} if test_integrity is None else test_integrity
        self.git_override = git_override
        self.yuss_heads = list(yuss_heads or [])
        self.calls: list = []
        self.popen_kwargs: list = []
        self.procs: list = []

    # -- helpers --
    @staticmethod
    def _git_parts(argv: list, kwargs: dict) -> tuple:
        args = list(argv[1:])
        target = kwargs.get("cwd")
        rest = []
        i = 0
        while i < len(args):
            if args[i] == "-C":
                target = args[i + 1]
                i += 2
            elif args[i] == "-c":
                i += 2
            else:
                rest.append(args[i])
                i += 1
        sub = next((a for a in rest if not a.startswith("-")), "")
        return (Path(target).resolve() if target else Path.cwd().resolve()), sub

    def _under_tmp(self, path: Path) -> bool:
        return str(path).startswith(str(self.tmp_root) + os.sep) or path == self.tmp_root

    @staticmethod
    def _outfile(argv: list) -> Optional[str]:
        for a in argv:
            if a.startswith("--outputFile="):
                return a.split("=", 1)[1]
        return None

    # -- entry points --
    def run(self, argv, *args, **kwargs):
        argv = list(argv)
        self.calls.append(argv)
        prog = argv[0]
        if prog == "git":
            target, sub = self._git_parts(argv, kwargs)
            if target == self.yuss or str(target).startswith(str(self.yuss) + os.sep):
                assert sub in self.YUSS_ALLOWED, "REFUSED: git %s against the fixture yuss" % sub
                if sub == "rev-parse" and argv[-1] == "HEAD" and self.yuss_heads:
                    return subprocess.CompletedProcess(argv, 0, self.yuss_heads.pop(0) + "\n", "")
                return REAL_RUN(argv, *args, **kwargs)
            assert self._under_tmp(target), "git target outside the temp root: %s" % target
            if self.git_override is not None:
                faked = self.git_override(argv)
                if faked is not None:
                    return faked
            return REAL_RUN(argv, *args, **kwargs)
        if prog == "pnpm":
            cwd = Path(kwargs.get("cwd") or ".").resolve()
            assert self._under_tmp(cwd), "pnpm outside the checkout: %s" % cwd
            assert isinstance(kwargs.get("timeout"), (int, float)), "pnpm without a timeout: %s" % argv
            if argv[1] == "install":
                if self.pnpm_install_timeout:
                    raise subprocess.TimeoutExpired(argv, kwargs["timeout"])
                return subprocess.CompletedProcess(argv, self.pnpm_install_exit, "", "")
            assert argv[1:3] == ["exec", "jest"] and "--forceExit" in argv, argv
            out = self._outfile(argv)
            assert out is not None and not str(Path(out).resolve()).startswith(str(cwd) + os.sep), \
                "jest output must live outside the tree: %s" % out
            if self.jest_timeout:
                raise subprocess.TimeoutExpired(argv, kwargs["timeout"])
            cov = next((a.split("=", 1)[1] for a in argv if a.startswith("--coverageDirectory=")), None)
            if cov is not None:
                assert "--coverage" in argv and not str(Path(cov).resolve()).startswith(str(cwd) + os.sep), argv
                Path(cov).mkdir(parents=True, exist_ok=True)
                (Path(cov) / "coverage-final.json").write_text("{}", encoding="utf-8")
            counts = self.jest_original if "--runTestsByPath" in argv else self.jest_suite
            if self.jest_writes_report:
                text = json.dumps(jest_json(*counts)) if self.jest_report_text is None else self.jest_report_text
                Path(out).write_text(text, encoding="utf-8")
            return subprocess.CompletedProcess(argv, self.jest_exit, "", "")
        if prog == "python3":
            script = Path(argv[1])
            cwd = Path(kwargs["cwd"]).resolve()
            assert self._under_tmp(cwd) and (cwd / ".git").is_dir(), "gate script cwd is not the checkout: %s" % cwd
            assert isinstance(kwargs.get("timeout"), (int, float)), "gate script without a timeout: %s" % argv
            project = Path(argv[argv.index("--project") + 1]).resolve()
            assert project == cwd, argv
            if script.name == "build-smoke.py":
                assert argv[2] == "check" and argv[argv.index("--timeout") + 1] == "300", argv
                spec = self.build_smoke
            else:
                assert script.name == "test-integrity.py" and argv[2] == "coverage", argv
                report = Path(argv[argv.index("--report") + 1]).resolve()
                assert self._under_tmp(report) and not str(report).startswith(str(cwd) + os.sep), argv
                spec = self.test_integrity
            if spec.get("timeout"):
                raise subprocess.TimeoutExpired(argv, kwargs["timeout"])
            stdout = spec["stdout"] if "stdout" in spec else gate_json(spec["verdict"], spec.get("causes"))
            return subprocess.CompletedProcess(argv, spec.get("exit", 0), stdout, "")
        if prog == "bash":
            assert argv[1].endswith("scripts/install.sh"), argv
            assert argv[2:] == ["--platform", "claude", "--no-commit", "--force"], argv
            cwd = Path(kwargs["cwd"]).resolve()
            assert self._under_tmp(cwd)
            manifest = cwd / ".claude" / ".writ-manifest"
            manifest.parent.mkdir(parents=True, exist_ok=True)
            manifest.write_text(
                "# Writ Manifest\n# mode: copy\n# platform: claude\n# version: %s\n"
                "aaaa  commands/_preamble.md\ncccc  commands/implement-story.md\ndddd  commands/ship.md\n"
                % self.install_version, encoding="utf-8")
            return subprocess.CompletedProcess(argv, self.install_exit, "installed\n", "")
        if prog == "claude":
            raise AssertionError("claude must be started with Popen, not run(): %s" % argv)
        raise AssertionError("unexpected program %r" % prog)

    def popen(self, argv, *args, **kwargs):
        argv = list(argv)
        self.calls.append(argv)
        assert argv[0] == "claude", argv
        assert not args, "Popen positional kwargs are not expected"
        assert kwargs.get("start_new_session") is True, kwargs
        assert "capture_output" not in kwargs and kwargs.get("stdout") is not subprocess.PIPE
        cwd = Path(kwargs["cwd"]).resolve()
        assert self._under_tmp(cwd) and (cwd / ".git").is_dir(), cwd
        self.popen_kwargs.append(kwargs)
        payload = "".join(json.dumps(e) + "\n" for e in self.events)
        kwargs["stdout"].write(payload.encode("utf-8"))
        kwargs["stdout"].flush()
        if self.on_claude is not None:
            self.on_claude(cwd)
        proc = FakeProc(self.claude_timeout, self.ignores_term, self.interrupt)
        self.procs.append(proc)
        return proc

    def programs(self) -> list:
        return [c[0] for c in self.calls]


@contextlib.contextmanager
def dispatched(disp: Dispatcher):
    killed: list = []
    with mock.patch.object(pb.subprocess, "run", disp.run), \
            mock.patch.object(pb.subprocess, "Popen", disp.popen), \
            mock.patch.object(pb.os, "killpg", lambda pgid, sig: killed.append((pgid, sig))), \
            mock.patch.object(pb.os, "getpgid", lambda pid: pid):
        yield killed


def invoke(argv: list, disp: Optional[Dispatcher], env: Optional[dict] = None) -> tuple:
    """Run `pb.main(argv)` under the dispatcher. Returns (code, stdout, stderr, killed)."""
    out, err = io.StringIO(), io.StringIO()
    code = 0
    env = {"ANTHROPIC_API_KEY": FAKE_KEY} if env is None else env
    cm = dispatched(disp) if disp is not None else contextlib.nullcontext([])
    with mock.patch.dict(os.environ, env, clear=True), cm as killed:
        os.environ.setdefault("PATH", "/usr/bin:/bin")
        try:
            with contextlib.redirect_stdout(out), contextlib.redirect_stderr(err):
                pb.main(argv)
        except SystemExit as exc:
            code = exc.code if isinstance(exc.code, int) else 1
    return code, out.getvalue(), err.getvalue(), killed


def complete_story(checkout: Path) -> None:
    """What a successful /implement-story leaves behind: Completed status, a
    What Was Built section, a commit, and the commit SHA in the header."""
    story = checkout / STORY_REL
    story.write_text(story_text("Completed ✅", wwb=True), encoding="utf-8")
    g = ["git", "-C", str(checkout), "-c", "user.name=t", "-c", "user.email=t@x"]
    REAL_RUN(g + ["add", "-A"], check=True, capture_output=True)
    REAL_RUN(g + ["commit", "-q", "-m", "feat: story 1"], check=True, capture_output=True)
    sha = REAL_RUN(g + ["rev-parse", "HEAD"], check=True, capture_output=True, text=True).stdout.strip()
    story.write_text(story_text("Completed ✅", commit=sha, wwb=True), encoding="utf-8")


class Case(unittest.TestCase):
    """Shared scaffolding: a temp root, a replay yuss, a fake claude on PATH,
    a fake writ root, and a baseline with one selected story."""

    def setUp(self) -> None:
        self._tmp = TemporaryDirectory()
        self.root = Path(self._tmp.name).resolve()
        self.repo, self.parent, self.story = replay_repo(self.root / "yuss")
        self.head = self.repo.git("rev-parse", "HEAD")
        self.porcelain = self.repo.git("status", "--porcelain")
        # PATH under test: a fake `claude` plus the real git (and nothing else,
        # so the real claude on the developer's PATH is never found).
        self.bin = self.root / "bin"
        self.bin.mkdir()
        for name in ("claude", "pnpm"):
            fake = self.bin / name
            fake.write_text("#!/bin/sh\nexit 0\n", encoding="utf-8")
            fake.chmod(0o755)
        self.gitbin = self.root / "gitbin"
        self.gitbin.mkdir()
        (self.gitbin / "git").symlink_to(shutil.which("git"))
        self.writ = Repo(self.root / "writ")
        self.writ_head = self.writ.commit({"scripts/install.sh": "#!/bin/bash\n"}, "chore: install.sh")   # clean tree
        self.tmp_root = self.root / "tmp"
        self.tmp_root.mkdir()
        self.baseline = self.root / "baselines" / "2026-09-06-claude-fable-5-1.json"
        self.doc = write_baseline(self.baseline, [selection_entry(self.parent, self.story)], self.head)

    def tearDown(self) -> None:
        # Business Rule 2: the fixture yuss is untouched by every path.
        self.assertEqual(self.repo.git("status", "--porcelain"), self.porcelain)
        self.assertEqual(self.repo.git("rev-parse", "HEAD"), self.head)
        self._tmp.cleanup()

    def env(self, key: bool = True) -> dict:
        env = {"PATH": os.pathsep.join([str(self.bin), str(self.gitbin)]), "HOME": str(self.root)}
        if key:
            env["ANTHROPIC_API_KEY"] = FAKE_KEY
        return env

    def disp(self, **kw) -> Dispatcher:
        return Dispatcher(self.repo.root, self.root, **kw)

    def run_args(self, *extra: str, yuss: Optional[Path] = None) -> list:
        return ["run", "--baseline", str(self.baseline), "--yuss", str(yuss or self.repo.root),
                "--tmp-root", str(self.tmp_root), "--writ-root", str(self.writ.root), "--runs", "1", *extra]

    def run_dirs(self) -> list:
        return sorted(p.name for p in self.tmp_root.glob("writ-baseline-*"))


# ---------------------------------------------------------------------------
# Contract constants
# ---------------------------------------------------------------------------


class ContractTest(unittest.TestCase):
    def test_exported_key_orders(self) -> None:
        self.assertEqual(list(pb.RUN_KEYS), [
            "story_id", "run", "status", "reason", "started_at", "isolation", "writ", "inputs", "deps",
            "invocation", "wall_clock_s", "num_turns", "tokens", "tokens_main_thread", "cost_usd",
            "interrupts", "review_iterations", "tests", "gates", "rederivation", "exit_criteria",
            "yuss_head_unchanged",
        ])
        self.assertEqual(list(pb.GATE_NAMES), [
            "gate0_arch", "gate0_5_boundary", "gate2_build", "gate2_5_surface",
            "gate3_review", "gate3_5_drift", "gate4_tests", "gate5_docs",
        ])
        self.assertEqual(pb.WRIT_KEYS, ("source", "commit", "dirty", "checkout_manifest_version", "manifest_diff_count"))
        self.assertEqual(pb.REDERIVATION_KEYS, (
            "build_smoke", "test_integrity",
            "arch_check", "review_override", "docs_check",
            "boundary_map", "change_surface", "drift_format",
        ))
        self.assertEqual(pb.GATE_SCRIPT_VERDICTS, ("pass", "fail", "unverifiable"))
        self.assertEqual(pb.RUN_STATUSES, ("complete", "budget", "error", "timeout"))
        self.assertEqual(pb.PERMISSION_MODE, "bypass")
        self.assertEqual(list(pb.INVOCATION_KEYS), [
            "driver", "argv", "model", "model_resolved", "claude_version", "permission_mode",
            "api_key_source",
        ])
        self.assertEqual(pb.DRIVERS["claude"].implemented, True)
        self.assertFalse(pb.DRIVERS["codex"].implemented)
        self.assertFalse(pb.DRIVERS["cursor"].implemented)
        # Story 3's contract is byte-stable.
        self.assertEqual(pb.READ_ONLY_GIT, frozenset({"rev-parse", "log", "show", "diff-tree"}))
        self.assertEqual(len(pb.SCHEMA_KEYS), 10)

    def test_stdlib_only_including_39_fallback_set(self) -> None:
        """Story 3's StdlibOnlyTest pins a literal module set on 3.9; the new
        code must stay inside it (no shutil/signal/time). Story 5 added
        `statistics` for compare medians."""
        import ast
        tree = ast.parse(pb.__file__ and Path(pb.__file__).read_text(encoding="utf-8"))
        names = set()
        for node in ast.walk(tree):
            if isinstance(node, ast.Import):
                names.update(a.name.split(".")[0] for a in node.names)
            elif isinstance(node, ast.ImportFrom) and node.module:
                names.add(node.module.split(".")[0])
        allowed = {"argparse", "collections", "dataclasses", "datetime", "fnmatch", "json",
                   "os", "re", "statistics", "subprocess", "sys", "tempfile", "pathlib",
                   "typing", "__future__"}
        self.assertTrue(names <= allowed, names - allowed)


# ---------------------------------------------------------------------------
# Preflight (AC-4.1)
# ---------------------------------------------------------------------------


class PreflightTest(Case):
    def test_missing_key_does_not_refuse(self) -> None:
        """Writ does not require a resident API key — the operator's CLI login is enough."""
        disp = self.disp()
        code, out, err, _ = invoke(self.run_args(), disp, env=self.env(key=False))
        self.assertNotEqual(code, 2, err)
        self.assertNotIn("ANTHROPIC_API_KEY is not set", err)
        self.assertNotIn(FAKE_KEY, err + out)
        self.assertTrue(disp.calls)          # preflight passed; checkout started
        if disp.popen_kwargs:
            self.assertIsNone(disp.popen_kwargs[0]["env"].get("ANTHROPIC_API_KEY"))

    def test_missing_binary_names_install_path(self) -> None:
        disp = self.disp()
        env = self.env()
        env["PATH"] = str(self.gitbin)          # git present, driver absent
        code, out, err, _ = invoke(self.run_args(), disp, env=env)
        self.assertEqual(code, 2)
        self.assertIn("claude", err)
        self.assertIn(pb.CLAUDE_INSTALL_HINT, err)
        self.assertIn("ingest", err)
        self.assertNotIn(FAKE_KEY, err + out)
        self.assertEqual(disp.calls, [])
        self.assertEqual(self.run_dirs(), [])

    def test_missing_pnpm_is_refused_before_any_checkout(self) -> None:
        disp = self.disp()
        (self.bin / "pnpm").unlink()          # claude present, pnpm absent
        code, _, err, _ = invoke(self.run_args(), disp, env=self.env())
        self.assertEqual(code, 2)
        self.assertIn("pnpm", err)
        self.assertIn(pb.PNPM_INSTALL_HINT, err)
        self.assertEqual(disp.calls, [])
        self.assertEqual(self.run_dirs(), [])

    def test_preflight_runs_before_the_baseline_is_read(self) -> None:
        disp = self.disp()
        args = self.run_args()
        args[args.index("--baseline") + 1] = str(self.root / "nope.json")
        env = self.env()
        env["PATH"] = str(self.gitbin)          # git present, claude absent
        code, _, err, _ = invoke(args, disp, env=env)
        self.assertEqual(code, 2)
        self.assertIn("claude", err)
        self.assertNotIn("nope.json", err)
        self.assertEqual(disp.calls, [])

    def test_preflight_helper_direct(self) -> None:
        no_key = {"PATH": str(self.bin)}
        with mock.patch.dict(os.environ, no_key, clear=True):
            pb.preflight()  # no key required
        with mock.patch.dict(os.environ, {"PATH": str(self.gitbin)}, clear=True):
            with self.assertRaises(pb.Refusal) as ctx:
                pb.preflight()
            self.assertIn("claude", str(ctx.exception))
        with mock.patch.dict(os.environ, self.env(), clear=True):
            pb.preflight()  # key present is also fine
        self.assertEqual(pb.which("claude", str(self.bin)), str(self.bin / "claude"))
        self.assertIsNone(pb.which("claude", str(self.gitbin)))
        self.assertIsNone(pb.which("claude", str(self.root / "empty")))

    def test_resolve_driver_is_model_agnostic(self) -> None:
        self.assertEqual(pb.resolve_driver("auto", "claude-fable-5-1").name, "claude")
        self.assertEqual(pb.resolve_driver("claude", "grok-4").name, "claude")  # explicit wins
        with self.assertRaises(pb.Refusal) as grok:
            pb.resolve_driver("auto", "grok-4")
        self.assertIn("ingest", str(grok.exception))
        with self.assertRaises(pb.Refusal) as local:
            pb.resolve_driver("auto", "llama-3.3-70b")
        self.assertIn("ingest", str(local.exception))
        with self.assertRaises(pb.Refusal) as gpt:
            pb.resolve_driver("auto", "gpt-5")
        self.assertIn("codex", str(gpt.exception))
        self.assertIn("ingest", str(gpt.exception))
        with self.assertRaises(pb.Refusal) as cursor:
            pb.resolve_driver("cursor")
        self.assertIn("ingest", str(cursor.exception))
        with self.assertRaises(pb.Refusal) as unknown:
            pb.resolve_driver("auto", "mystery-weights-7b")
        self.assertIn("--driver", str(unknown.exception))

    def test_grok_baseline_refuses_with_ingest_zero_side_effects(self) -> None:
        grok = self.root / "baselines" / "2026-09-06-grok-4.json"
        write_baseline(grok, [selection_entry(self.parent, self.story)], self.head, model="grok-4")
        disp = self.disp()
        args = self.run_args()
        args[args.index("--baseline") + 1] = str(grok)
        code, out, err, _ = invoke(args, disp, env=self.env(key=False))
        self.assertEqual(code, 2)
        self.assertIn("grok-4", err)
        self.assertIn("ingest", err)
        self.assertNotIn("ANTHROPIC_API_KEY is not set", err)
        self.assertEqual(disp.calls, [])
        self.assertEqual(self.run_dirs(), [])

    def test_unimplemented_driver_flag_refuses_before_checkout(self) -> None:
        disp = self.disp()
        code, _, err, _ = invoke(self.run_args("--driver", "cursor"), disp, env=self.env())
        self.assertEqual(code, 2)
        self.assertIn("ingest", err)
        self.assertEqual(disp.calls, [])
        self.assertEqual(self.run_dirs(), [])

    def test_missing_baseline_and_empty_selection_refuse(self) -> None:
        disp = self.disp()
        args = self.run_args()
        args[args.index("--baseline") + 1] = str(self.root / "nope.json")
        code, _, err, _ = invoke(args, disp, env=self.env())
        self.assertEqual(code, 2)
        self.assertIn("nope.json", err)
        write_baseline(self.baseline, [], self.head)
        code, _, err, _ = invoke(self.run_args(), disp, env=self.env())
        self.assertEqual(code, 2)
        self.assertIn("select", err)
        self.assertEqual(disp.calls, [])
        self.assertEqual(self.run_dirs(), [])

    def test_model_mismatch_refused(self) -> None:
        disp = self.disp()
        code, _, err, _ = invoke(self.run_args("--model", "claude-other"), disp, env=self.env())
        self.assertEqual(code, 2)
        self.assertIn("claude-other", err)
        self.assertIn("claude-fable-5-1", err)
        self.assertEqual(set(disp.programs()), {"git"})       # only the read-only yuss check
        self.assertEqual(self.run_dirs(), [])

    def test_wrong_schema_bad_yuss_and_zero_runs_are_refused(self) -> None:
        disp = self.disp()
        before = self.baseline.read_bytes()
        other = self.root / "baselines" / "other.json"
        pb.write_json(other, {"schema": "something-else-v1", "runs": []})
        args = self.run_args()
        args[args.index("--baseline") + 1] = str(other)
        code, _, err, _ = invoke(args, disp, env=self.env())
        self.assertEqual(code, 2)
        self.assertIn(pb.SCHEMA, err)
        code, _, err, _ = invoke(self.run_args(yuss=self.root / "nowhere"), disp, env=self.env())
        self.assertEqual(code, 2)
        self.assertIn("not a directory", err)
        plain = self.root / "plain"
        plain.mkdir()
        code, _, err, _ = invoke(self.run_args(yuss=plain), disp, env=self.env())
        self.assertEqual(code, 2)
        self.assertIn("not a git repository", err)
        code, _, err, _ = invoke(self.run_args("--runs", "0"), disp, env=self.env())
        self.assertEqual(code, 2)
        self.assertIn("--runs", err)
        # every refusal happened before a checkout, a record, or a mutating process
        self.assertLessEqual(set(disp.programs()), {"git"})
        self.assertEqual(self.run_dirs(), [])
        self.assertEqual(self.baseline.read_bytes(), before)


# ---------------------------------------------------------------------------
# Transcript parsing (AC-4.4)
# ---------------------------------------------------------------------------


class ParseTranscriptTest(unittest.TestCase):
    def _write(self, tmp: str, events: list, name: str = "t.jsonl") -> Path:
        p = Path(tmp) / name
        p.write_text("".join(json.dumps(e) + "\n" for e in events) + "not json\n", encoding="utf-8")
        return p

    def test_stream_json_prefers_result_event(self) -> None:
        with TemporaryDirectory() as tmp:
            t = pb.parse_transcript(self._write(tmp, stream_events()))
        self.assertEqual(t["mode"], "stream")
        self.assertEqual(t["status"], "complete")
        self.assertEqual(t["tokens"], {"input": 1000, "output": 2000, "cache_read": 30000, "cache_creation": 4000})
        # main-thread sum is a cross-check, never the headline number; the
        # echoed subagent turn (parent_tool_use_id, 7777/8888 tokens) is not in it
        n_assistant = main_thread_assistants(stream_events())
        self.assertLess(n_assistant, sum(1 for e in stream_events() if e["type"] == "assistant"))
        self.assertEqual(t["tokens_main_thread"], {"input": 10 * n_assistant, "output": 20 * n_assistant,
                                                   "cache_read": 300 * n_assistant, "cache_creation": 40 * n_assistant})
        self.assertEqual(t["cost_usd"], 12.25)
        self.assertEqual(t["wall_clock_s"], 90.5)
        self.assertEqual(t["num_turns"], 42)
        self.assertEqual(t["init"], {"model_resolved": "claude-fable-5-1-20260801", "api_key_source": "user",
                                     "claude_version": "2.1.260"})
        self.assertEqual(t["exit_reported"], "COMPLETE")

    def test_verdicts_come_from_subagent_tool_results_and_ignore_templates(self) -> None:
        with TemporaryDirectory() as tmp:
            t = pb.parse_transcript(self._write(tmp, stream_events(review_fails=2)))
        self.assertEqual(t["gates"]["gate0_arch"], {"verdict": "CAUTION", "source": "tool_result"})
        self.assertEqual(t["gates"]["gate3_review"], {"verdict": "PASS", "source": "tool_result"})
        self.assertEqual(t["gates"]["gate4_tests"], {"verdict": "PASS", "source": "tool_result"})
        self.assertEqual(t["gates"]["gate5_docs"], {"verdict": "YES", "source": "tool_result"})
        self.assertEqual(t["gates"]["gate2_build"], {"verdict": None, "source": None})
        self.assertEqual(t["review_iterations"], 2)
        # `AskQuestion(` inside the Read result is not an interrupt; the
        # AskUserQuestion tool_use is. STATUS: BLOCKED in the .md is not
        # counted, nor the one inside the echoed subagent turn; the one in the
        # coder's tool_result is.
        self.assertEqual(t["interrupts"], {"ask_user_question": 1, "status_blocked": 1})

    def test_subagent_echo_events_are_not_main_thread(self) -> None:
        sub = _assistant([_tool_use("t_ask_sub", "AskUserQuestion", {"questions": []}),
                          {"type": "text", "text": "REVIEW_RESULT: FAIL\nSTATUS: BLOCKED"}],
                         usage={"input_tokens": 500, "output_tokens": 500,
                                "cache_read_input_tokens": 0, "cache_creation_input_tokens": 0})
        sub["parent_tool_use_id"] = "t_task"
        sub_result = _tool_result("t_ask_sub", "STATUS: BLOCKED")
        sub_result["parent_tool_use_id"] = "t_task"
        events = [_assistant([_tool_use("t_task", "Task", {"subagent_type": "writ-coder"})]), sub, sub_result,
                  _tool_result("t_task", "REVIEW_RESULT: PASS")]
        with TemporaryDirectory() as tmp:
            t = pb.parse_transcript(self._write(tmp, events))
        self.assertEqual(t["tokens_main_thread"], {"input": 10, "output": 20, "cache_read": 300, "cache_creation": 40})
        self.assertEqual(t["interrupts"], {"ask_user_question": 0, "status_blocked": 0})
        self.assertEqual(t["review_iterations"], 0)
        self.assertEqual(t["gates"]["gate3_review"], {"verdict": "PASS", "source": "tool_result"})

    def test_assistant_text_is_the_verdict_fallback(self) -> None:
        with TemporaryDirectory() as tmp:
            t = pb.parse_transcript(self._write(tmp, stream_events(text_fallback=True)))
        self.assertEqual(t["gates"]["gate5_docs"], {"verdict": "NO", "source": "assistant_text"})

    def test_template_strings_alone_yield_no_verdicts(self) -> None:
        events = [_assistant([_tool_use("r", "Read", {"file_path": "commands/implement-story.md"})]),
                  _tool_result("r", TEMPLATE_MD),
                  _assistant([{"type": "text", "text": "ARCH_CHECK: [PROCEED/CAUTION/ABORT] is the format"}])]
        with TemporaryDirectory() as tmp:
            t = pb.parse_transcript(self._write(tmp, events))
        for g in pb.GATE_NAMES:
            self.assertEqual(t["gates"][g], {"verdict": None, "source": None}, g)
        self.assertEqual(t["interrupts"], {"ask_user_question": 0, "status_blocked": 0})
        self.assertEqual(t["status"], "error")
        self.assertEqual(t["reason"], "no_result_event")
        self.assertIsNone(t["exit_reported"])

    def test_verdict_regex_boundaries(self) -> None:
        self.assertIsNone(pb.VERDICT_LINE.search("ARCH_CHECK: [PROCEED/CAUTION/ABORT]"))
        self.assertIsNone(pb.VERDICT_LINE.search("REVIEW_RESULT: PASSING"))
        m = pb.VERDICT_LINE.search("### REVIEW_RESULT: PAUSE\n")
        self.assertEqual(m.group(1, 2), ("REVIEW_RESULT", "PAUSE"))
        self.assertIsNotNone(pb.VERDICT_LINE.search("DOCS_UPDATED: BLOCKED"))
        self.assertIsNone(pb.STATUS_BLOCKED.search("STATUS: BLOCKED_BY"))

    def test_result_subtypes_map_to_statuses(self) -> None:
        with TemporaryDirectory() as tmp:
            for subtype, status in (("success", "complete"), ("error_max_budget_usd", "budget"),
                                    ("error_during_execution", "error"), ("error_max_turns", "error"),
                                    ("something_new", "error")):
                t = pb.parse_transcript(self._write(tmp, stream_events(subtype=subtype), subtype + ".jsonl"))
                self.assertEqual(t["status"], status, subtype)
                self.assertEqual(t["reason"], None if subtype == "success" else subtype)

    def test_exit_reported_degraded(self) -> None:
        with TemporaryDirectory() as tmp:
            t = pb.parse_transcript(self._write(tmp, stream_events(final_text="Story 1 ⚠️ DEGRADED — Gate 4 skipped")))
        self.assertEqual(t["exit_reported"], "DEGRADED")

    def test_session_jsonl_sums_usage_and_uses_timestamps(self) -> None:
        with TemporaryDirectory() as tmp:
            t = pb.parse_transcript(self._write(tmp, session_events()))
        self.assertEqual(t["mode"], "session")
        n_assistant = main_thread_assistants(session_events())
        self.assertEqual(t["tokens"]["input"], 10 * n_assistant)
        self.assertEqual(t["tokens"], t["tokens_main_thread"])
        self.assertEqual(t["wall_clock_s"], 150.0)
        self.assertEqual(t["num_turns"], n_assistant)
        self.assertIsNone(t["cost_usd"])
        self.assertEqual(t["status"], "complete")
        self.assertEqual(t["gates"]["gate3_review"]["verdict"], "PASS")
        self.assertEqual(t["init"], {"model_resolved": None, "api_key_source": None, "claude_version": None})

    def test_malformed_events_change_nothing(self) -> None:
        """A 90-minute stream carries shapes the fixture does not: non-object
        lines, blank lines, non-dict content blocks, user text that is not a
        tool_result, tool_result content that is not text, unparseable
        timestamps. None of it may raise or move a number."""
        clean = stream_events()
        noise = [
            ["not", "an", "object"],
            {"type": "assistant", "message": {"content": [None, "bare string", {"type": "tool_use"}]}},
            {"type": "user", "message": {"content": [
                {"type": "text", "text": "STATUS: BLOCKED — plain user text is not a gate result"},
                {"type": "tool_result", "tool_use_id": "t_code", "content": 42}]}},
            {"type": "assistant", "timestamp": "yesterday", "message": {"content": "narration only"}},
            {"type": "user", "message": "not a dict"},
            {"type": "assistant"},
        ]
        noisy = clean[:2] + noise + clean[2:]
        with TemporaryDirectory() as tmp:
            expected = pb.parse_transcript(self._write(tmp, clean, "clean.jsonl"))
            p = Path(tmp) / "noisy.jsonl"
            p.write_text("\n\n" + "".join(json.dumps(e) + "\n\n" for e in noisy) + "not json\n", encoding="utf-8")
            actual = pb.parse_transcript(p)
        self.assertEqual(actual, expected)
        self.assertEqual(actual["interrupts"], {"ask_user_question": 1, "status_blocked": 1})


# ---------------------------------------------------------------------------
# scrub (Business Rule 3)
# ---------------------------------------------------------------------------


class ScrubTest(unittest.TestCase):
    def test_rejects_keys_long_strings_and_newlines(self) -> None:
        pb.scrub({"a": {"b": ["x" * 200, 1, None, True, 2.5]}})
        for bad in ({"k": FAKE_KEY}, {"k": {"n": ["y" * 201]}}, {"k": "line\nbreak"}, {"k": ["ok", "sk-ant-x"]}):
            with self.assertRaises(pb.ScrubError) as ctx:
                pb.scrub(bad)
            self.assertIn("$.k", str(ctx.exception))
            self.assertNotIn(FAKE_KEY, str(ctx.exception))


# ---------------------------------------------------------------------------
# Checkout isolation (AC-4.2)
# ---------------------------------------------------------------------------


class BuildCheckoutTest(Case):
    def test_real_fetch_depth_1_leaves_one_reachable_commit(self) -> None:
        run_dir = self.tmp_root / "writ-baseline-x-1"
        disp = self.disp()
        with dispatched(disp):
            checkout, isolation = pb.build_checkout(self.repo.root, self.parent, run_dir)
        self.assertEqual(checkout, run_dir / "checkout")
        self.assertEqual(isolation, {"reachable_commits": 1, "expected": 1, "asserted": True,
                                     "answer_scrub_asserted": False})
        self.assertEqual(REAL_RUN(["git", "-C", str(checkout), "rev-parse", "HEAD"],
                                  capture_output=True, text=True).stdout.strip(), self.parent)
        self.assertFalse((checkout / ".git" / "FETCH_HEAD").exists())
        self.assertEqual(REAL_RUN(["git", "-C", str(checkout), "remote", "-v"],
                                  capture_output=True, text=True).stdout, "")
        # nothing under .git/ (objects aside) names yuss's path: FETCH_HEAD was the only reference
        yuss_path = str(self.repo.root).encode("utf-8")
        naming = []
        for root, dirs, files in os.walk(str(checkout / ".git")):
            dirs[:] = [d for d in dirs if not (Path(root) == checkout / ".git" and d == "objects")]
            for name in files:
                if yuss_path in Path(root, name).read_bytes():
                    naming.append(os.path.relpath(os.path.join(root, name), str(checkout)))
        self.assertEqual(naming, [])
        self.assertTrue((checkout / STORY_REL).is_file())
        self.assertFalse((checkout / TEST_FILE).exists())          # the answer is unreachable
        self.assertEqual(REAL_RUN(["git", "-C", str(checkout), "config", "commit.gpgsign"],
                                  capture_output=True, text=True).stdout.strip(), "false")
        # every git call against yuss was read-only; the fetch targets the checkout
        yuss_calls = [c for c in disp.calls if c[0] == "git" and "-C" in c and c[c.index("-C") + 1] == str(self.repo.root)]
        self.assertEqual(yuss_calls, [])
        self.assertTrue(any("fetch" in c and str(self.repo.root) in c for c in disp.calls))
        self.assertFalse(any("worktree" in c for c in disp.calls))

    def test_reachable_count_mismatch_aborts_before_overlay_or_claude(self) -> None:
        def two(argv):
            if "rev-list" in argv:
                return subprocess.CompletedProcess(argv, 0, "2\n", "")
            return None

        disp = self.disp(git_override=two)
        code, out, err, _ = invoke(self.run_args(), disp, env=self.env())
        self.assertEqual(code, 0, err)
        rec = load(self.baseline)["runs"][0]
        self.assertEqual(rec["status"], "error")
        self.assertEqual(rec["reason"], "isolation_failed")
        self.assertEqual(rec["isolation"], {"reachable_commits": 2, "expected": 1, "asserted": False,
                                            "answer_scrub_asserted": False})
        self.assertNotIn("claude", disp.programs())
        self.assertNotIn("bash", disp.programs())
        self.assertNotIn("pnpm", disp.programs())
        self.assertEqual(self.run_dirs(), [])
        self.assertIn("isolation_failed", out)

    def test_fetch_failure_is_an_error_record(self) -> None:
        entry = selection_entry("0" * 40, self.story)
        write_baseline(self.baseline, [entry], self.head)
        disp = self.disp()
        code, _, err, _ = invoke(self.run_args(), disp, env=self.env())
        self.assertEqual(code, 0, err)
        rec = load(self.baseline)["runs"][0]
        self.assertEqual((rec["status"], rec["reason"]), ("error", "fetch_failed"))
        self.assertFalse(rec["isolation"]["asserted"])
        self.assertNotIn("claude", disp.programs())

    def test_configured_remote_fails_the_isolation_assertion(self) -> None:
        """One reachable commit is necessary, not sufficient: a remote is a
        path back to yuss and every ref it advertises."""
        def with_remote(argv):
            if "remote" in argv:
                return subprocess.CompletedProcess(argv, 0, "origin\t%s (fetch)\n" % self.repo.root, "")
            return None

        disp = self.disp(git_override=with_remote)
        code, _, err, _ = invoke(self.run_args(), disp, env=self.env())
        self.assertEqual(code, 0, err)
        rec = load(self.baseline)["runs"][0]
        self.assertEqual((rec["status"], rec["reason"]), ("error", "isolation_failed"))
        self.assertEqual(rec["isolation"], {"reachable_commits": 1, "expected": 1, "asserted": False,
                                            "answer_scrub_asserted": False})
        self.assertNotIn("claude", disp.programs())
        self.assertNotIn("bash", disp.programs())
        self.assertNotIn(str(self.repo.root), json.dumps(rec))    # the remote's path never reaches the record

    def test_git_failure_after_fetch_is_an_error_record(self) -> None:
        def broken_checkout(argv):
            if "checkout" in argv:
                return subprocess.CompletedProcess(argv, 128, "", "fatal: broken")
            return None

        disp = self.disp(git_override=broken_checkout)
        code, out, err, _ = invoke(self.run_args(), disp, env=self.env())
        self.assertEqual(code, 0, err)
        rec = load(self.baseline)["runs"][0]
        self.assertEqual((rec["status"], rec["reason"]), ("error", "git_checkout_failed"))
        self.assertEqual(rec["isolation"], {"reachable_commits": None, "expected": 1, "asserted": False,
                                            "answer_scrub_asserted": False})
        self.assertNotIn("claude", disp.programs())
        self.assertNotIn("bash", disp.programs())
        self.assertEqual(self.run_dirs(), [])
        self.assertIn("git_checkout_failed", out)


# ---------------------------------------------------------------------------
# run — end to end (AC-4.3, AC-4.4, AC-4.5)
# ---------------------------------------------------------------------------


class RunTest(Case):
    def test_happy_path_record(self) -> None:
        before = load(self.baseline)
        disp = self.disp(on_claude=complete_story)
        env = dict(self.env(), CLAUDECODE="1")     # as if launched from a Claude Code terminal
        code, out, err, killed = invoke(self.run_args(), disp, env=env)
        self.assertEqual(code, 0, err)
        doc = load(self.baseline)
        self.assertEqual(doc["runs_per_story"], 1)
        for k in pb.SCHEMA_KEYS:
            if k not in ("runs", "runs_per_story"):
                self.assertEqual(doc[k], before[k], k)
        self.assertEqual(len(doc["runs"]), 1)
        rec = doc["runs"][0]
        self.assertEqual(list(rec)[:len(pb.RUN_KEYS)], list(pb.RUN_KEYS))
        self.assertEqual(rec["background_tasks_outstanding"], 0)
        self.assertEqual(rec["story_id"], STORY_ID)
        self.assertEqual(rec["run"], 1)
        self.assertEqual(rec["status"], "complete")
        self.assertIsNone(rec["reason"])
        self.assertTrue(rec["started_at"].endswith("Z"))
        self.assertEqual(rec["isolation"], {"reachable_commits": 1, "expected": 1, "asserted": True,
                                            "answer_scrub_asserted": True})
        self.assertEqual(rec["writ"], {"source": "overlay", "commit": self.writ_head, "dirty": False,
                                       "checkout_manifest_version": "e1a3fd1", "manifest_diff_count": 2})
        self.assertEqual(rec["inputs"], "parent")
        self.assertEqual(rec["deps"]["exit"], 0)
        self.assertIsInstance(rec["deps"]["seconds"], float)
        inv = rec["invocation"]
        self.assertEqual(list(inv), ["driver", "argv", "model", "model_resolved", "claude_version",
                                     "permission_mode", "api_key_source"])
        self.assertEqual(inv["driver"], "claude")
        self.assertEqual(inv["argv"], [
            "claude", "-p", "/implement-story " + STORY_REL, "--output-format", "stream-json", "--verbose",
            "--model", "claude-fable-5-1", "--max-budget-usd", "75",
            "--dangerously-skip-permissions", "--permission-prompts", "none", "--setting-sources", "project",
            "--strict-mcp-config", "--no-session-persistence",
        ])
        self.assertEqual(inv["model"], "claude-fable-5-1")
        self.assertEqual(inv["model_resolved"], "claude-fable-5-1-20260801")
        self.assertEqual(inv["claude_version"], "2.1.260")
        self.assertEqual(inv["permission_mode"], "bypass")
        self.assertEqual(inv["api_key_source"], "user")
        self.assertEqual(rec["wall_clock_s"], 90.5)
        self.assertEqual(rec["num_turns"], 42)
        self.assertEqual(rec["tokens"], {"input": 1000, "output": 2000, "cache_read": 30000, "cache_creation": 4000})
        self.assertEqual(rec["cost_usd"], 12.25)
        self.assertEqual(rec["interrupts"], {"ask_user_question": 1, "status_blocked": 1})
        self.assertEqual(rec["review_iterations"], 1)
        self.assertEqual(rec["tests"], {"suite": {"passed": 3, "total": 3, "reason": None},
                                        "original": {"passed": 1, "total": 1, "reason": None, "files": [TEST_FILE]}})
        self.assertEqual(list(rec["gates"]), list(pb.GATE_NAMES))
        self.assertEqual(rec["gates"]["gate0_arch"], {"verdict": "CAUTION", "source": "tool_result", "rederived": None})
        self.assertEqual(rec["gates"]["gate2_build"], {"verdict": None, "source": None, "rederived": "pass"})
        self.assertEqual(rec["gates"]["gate4_tests"], {"verdict": "PASS", "source": "tool_result",
                                                       "rederived": "pass", "integrity": "pass"})
        # Business Rule 5: the gate scripts ran from --writ-root against the
        # checkout; argv is recorded with machine paths as placeholders
        self.assertEqual(list(rec["rederivation"]), list(pb.REDERIVATION_KEYS))
        self.assertEqual(rec["rederivation"]["build_smoke"], {
            "argv": ["python3", "<writ_root>/scripts/build-smoke.py", "check", "--project", "<checkout>",
                     "--timeout", "300"], "verdict": "pass", "reason": None})
        self.assertEqual(rec["rederivation"]["test_integrity"], {
            "argv": ["python3", "<writ_root>/scripts/test-integrity.py", "coverage", "--project", "<checkout>",
                     "--report", "<artifacts>/coverage/coverage-final.json"], "verdict": "pass", "reason": None})
        self.assertEqual(rec["exit_criteria"], {"reported": "COMPLETE", "rederived": "met",
                                                "rederived_by": "implement-story success predicates"})
        self.assertTrue(rec["yuss_head_unchanged"])
        for path, value in walk_strings(rec):
            self.assertLessEqual(len(value), 200, path)
            self.assertNotIn("\n", value, path)
            self.assertNotIn("sk-ant-", value, path)
            self.assertNotIn(str(self.tmp_root), value, path)
        # order of operations: install deps before claude; jest and the gate
        # scripts after, with the scripts reading the produced tree before the
        # original tests are restored into it
        progs = disp.programs()
        self.assertLess(progs.index("bash"), progs.index("claude"))
        self.assertLess(progs.index("pnpm"), progs.index("claude"))
        self.assertLess(progs.index("claude"), progs.index("python3"))
        jest = [i for i, c in enumerate(disp.calls) if c[:3] == ["pnpm", "exec", "jest"]]
        self.assertEqual(len(jest), 2)
        self.assertLess(jest[0], progs.index("python3"))
        self.assertLess(progs.index("python3"), jest[1])
        self.assertEqual(progs.count("python3"), 2)
        self.assertEqual(killed, [])
        # Popen wiring: files, not pipes
        kw = disp.popen_kwargs[0]
        self.assertTrue(kw["stdout"].name.endswith("transcript.jsonl"))
        self.assertTrue(kw["stderr"].name.endswith("stderr.log"))
        self.assertEqual(disp.procs[0].waits, [pb.DEFAULT_CAP_S])
        # operator env is inherited (any vendor key included); nested session markers are not
        self.assertEqual(kw["env"].get("ANTHROPIC_API_KEY"), FAKE_KEY)
        self.assertFalse(set(kw["env"]) & pb.NESTED_SESSION_VARS)
        # one progress line; temp dir removed without --keep
        lines = [l for l in out.splitlines() if l.startswith("run: ")]
        self.assertEqual(len(lines), 1)
        for token in (STORY_ID, "complete", "exit=met", "tests=3/3", "tokens=1000/2000/30000", "wall=90.5s", "interrupts=2"):
            self.assertIn(token, lines[0])
        self.assertEqual(self.run_dirs(), [])

    def test_original_tests_come_from_the_story_commit(self) -> None:
        seen = {}

        def capture(cwd: Path) -> None:
            complete_story(cwd)
            seen["before"] = (cwd / TEST_FILE).exists()

        disp = self.disp(on_claude=capture, jest_original=(0, 1), jest_exit=1)
        code, _, err, _ = invoke(self.run_args("--keep"), disp, env=self.env())
        self.assertEqual(code, 0, err)
        self.assertFalse(seen["before"])   # the agent never saw the original test
        checkout = self.tmp_root / ("writ-baseline-%s-1" % STORY_STEM) / "checkout"
        self.assertEqual((checkout / TEST_FILE).read_text(encoding="utf-8"), CLEAN_TEST)
        rec = load(self.baseline)["runs"][0]
        self.assertEqual(rec["tests"]["original"], {"passed": 0, "total": 1, "reason": None, "files": [TEST_FILE]})
        self.assertEqual(rec["gates"]["gate4_tests"]["rederived"], "pass")   # suite still 3/3
        show = [c for c in disp.calls if c[0] == "git" and "show" in c and self.story in "".join(c)]
        self.assertEqual(len(show), 1)

    def test_timeout_records_status_and_kills_the_process_group(self) -> None:
        disp = self.disp(claude_timeout=True, events=stream_events(with_result=False))
        code, out, err, killed = invoke(self.run_args("--cap", "7"), disp, env=self.env())
        self.assertEqual(code, 0, err)
        rec = load(self.baseline)["runs"][0]
        self.assertEqual(rec["status"], "timeout")
        self.assertIsNone(rec["reason"])
        # SIGTERM, grace, then SIGKILL regardless: children the agent spawned share the group
        self.assertEqual(killed, [(99_999_999, 15), (99_999_999, 9)])
        self.assertEqual(disp.procs[0].waits, [7, pb.KILL_GRACE_S, pb.KILL_GRACE_S])
        self.assertIsInstance(rec["wall_clock_s"], float)
        self.assertEqual(rec["exit_criteria"]["rederived"], "unmet")
        self.assertEqual(rec["tests"]["suite"], {"passed": 3, "total": 3, "reason": None})
        self.assertIn("timeout", out)
        self.assertEqual(rec["invocation"]["argv"][rec["invocation"]["argv"].index("--max-budget-usd") + 1], "75")
        self.assertEqual(self.run_dirs(), [])

    def test_timeout_escalates_to_sigkill_when_term_is_ignored(self) -> None:
        disp = self.disp(claude_timeout=True, ignores_term=True, events=stream_events(with_result=False))
        code, _, err, killed = invoke(self.run_args("--cap", "7"), disp, env=self.env())
        self.assertEqual(code, 0, err)
        self.assertEqual(killed, [(99_999_999, 15), (99_999_999, 9)])
        self.assertEqual(disp.procs[0].waits, [7, pb.KILL_GRACE_S, pb.KILL_GRACE_S])
        self.assertEqual(load(self.baseline)["runs"][0]["status"], "timeout")

    def test_kill_group_is_best_effort_when_the_group_is_gone(self) -> None:
        proc = FakeProc(timeout=False)
        proc.returncode = 0

        def gone(pgid, sig):
            raise ProcessLookupError()

        with mock.patch.object(pb.os, "killpg", gone):
            pb._kill_group(proc)            # no raise
        self.assertEqual(proc.waits, [pb.KILL_GRACE_S, pb.KILL_GRACE_S])

    def test_interrupt_kills_the_group_and_keeps_the_run_dir(self) -> None:
        """Ctrl-C reaches only this process (`start_new_session=True` detaches
        claude from the terminal): the group must be killed on the way out
        and the transcript must survive for `ingest`."""
        disp = self.disp(interrupt=True)
        err = io.StringIO()
        with mock.patch.dict(os.environ, self.env(), clear=True), dispatched(disp) as killed, \
                contextlib.redirect_stdout(io.StringIO()), contextlib.redirect_stderr(err):
            with self.assertRaises(KeyboardInterrupt):
                pb.main(self.run_args())
        self.assertEqual(killed, [(99_999_999, 15), (99_999_999, 9)])
        run_dir = self.tmp_root / ("writ-baseline-%s-1" % STORY_STEM)
        self.assertEqual(self.run_dirs(), [run_dir.name])
        self.assertTrue((run_dir / "transcript.jsonl").is_file())
        self.assertTrue((run_dir / "run-meta.json").is_file())
        self.assertIn("run dir kept: %s" % run_dir, err.getvalue())
        self.assertEqual(load(self.baseline)["runs"], [])
        self.assertNotIn("pnpm", [c[0] for c in disp.calls if c[:3] == ["pnpm", "exec", "jest"]])

    def test_postprocess_failure_keeps_the_paid_run_dir(self) -> None:
        disp = self.disp(on_claude=complete_story)
        err = io.StringIO()
        with mock.patch.dict(os.environ, self.env(), clear=True), dispatched(disp), \
                mock.patch.object(pb, "postprocess", side_effect=RuntimeError("boom")), \
                contextlib.redirect_stdout(io.StringIO()), contextlib.redirect_stderr(err):
            with self.assertRaises(RuntimeError):
                pb.main(self.run_args())
        run_dir = self.tmp_root / ("writ-baseline-%s-1" % STORY_STEM)
        self.assertTrue(run_dir.is_dir())
        self.assertTrue((run_dir / "transcript.jsonl").is_file())
        self.assertIn("run dir kept: %s" % run_dir, err.getvalue())
        self.assertEqual(load(self.baseline)["runs"], [])

    def test_rmtree_handles_symlinks_and_missing_paths(self) -> None:
        target = self.root / "tree"
        (target / "sub").mkdir(parents=True)
        (target / "sub" / "f").write_text("x", encoding="utf-8")
        (target / "link-dir").symlink_to(self.repo.root)
        (target / "link-file").symlink_to(self.repo.root / "README.md")
        pb.rmtree(target)
        self.assertFalse(target.exists())
        self.assertTrue((self.repo.root / "README.md").is_file())   # symlink targets untouched
        pb.rmtree(self.root / "never-existed")
        lone = self.root / "lone"
        lone.write_text("x", encoding="utf-8")
        pb.rmtree(lone)
        self.assertFalse(lone.exists())

    def test_budget_flag_and_status(self) -> None:
        disp = self.disp(events=stream_events(subtype="error_max_budget_usd"))
        code, _, err, _ = invoke(self.run_args("--budget-usd", "12.5"), disp, env=self.env())
        self.assertEqual(code, 0, err)
        rec = load(self.baseline)["runs"][0]
        self.assertEqual(rec["status"], "budget")
        self.assertIn("12.5", rec["invocation"]["argv"])

    def test_resume_skips_present_pairs_and_flushes_per_run(self) -> None:
        existing = {"story_id": STORY_ID, "run": 1, "status": "complete"}
        write_baseline(self.baseline, [selection_entry(self.parent, self.story)], self.head,
                       runs=[existing], runs_per_story=2)
        disp = self.disp(on_claude=complete_story)
        code, out, err, _ = invoke(self.run_args("--runs", "2"), disp, env=self.env())
        self.assertEqual(code, 0, err)
        doc = load(self.baseline)
        self.assertEqual([(r["story_id"], r["run"]) for r in doc["runs"]], [(STORY_ID, 1), (STORY_ID, 2)])
        self.assertEqual(doc["runs"][0], existing)
        self.assertEqual(disp.programs().count("claude"), 1)
        self.assertIn("skip", out)

    def test_differing_runs_refused_unless_force(self) -> None:
        write_baseline(self.baseline, [selection_entry(self.parent, self.story)], self.head, runs_per_story=2)
        disp = self.disp()
        code, _, err, _ = invoke(self.run_args("--runs", "1"), disp, env=self.env())
        self.assertEqual(code, 2)
        self.assertIn("--force", err)
        self.assertEqual(set(disp.programs()), {"git"})
        self.assertEqual(self.run_dirs(), [])
        code, _, err, _ = invoke(self.run_args("--runs", "1", "--force"), disp, env=self.env())
        self.assertEqual(code, 0, err)
        self.assertEqual(load(self.baseline)["runs_per_story"], 1)

    def test_force_persists_runs_per_story_when_every_pair_is_skipped(self) -> None:
        present = [{"story_id": STORY_ID, "run": 1, "status": "complete"},
                   {"story_id": STORY_ID, "run": 2, "status": "complete"}]
        write_baseline(self.baseline, [selection_entry(self.parent, self.story)], self.head,
                       runs=present, runs_per_story=2)
        disp = self.disp()
        code, out, err, _ = invoke(self.run_args("--runs", "1", "--force"), disp, env=self.env())
        self.assertEqual(code, 0, err)
        doc = load(self.baseline)
        self.assertEqual(doc["runs_per_story"], 1)
        self.assertEqual(doc["runs"], present)          # nothing replayed, nothing dropped
        self.assertNotIn("claude", disp.programs())
        self.assertIn("runs_per_story set to 1", out)
        # an unchanged value with every pair skipped leaves the file byte-identical
        before = self.baseline.read_bytes()
        code, _, err, _ = invoke(self.run_args("--runs", "1"), disp, env=self.env())
        self.assertEqual(code, 0, err)
        self.assertEqual(self.baseline.read_bytes(), before)

    # -- Business Rule 5: Gate 2 / Gate 4 re-derived by Writ's own scripts --

    def _rederived(self, **disp_kw) -> dict:
        write_baseline(self.baseline, [selection_entry(self.parent, self.story)], self.head)
        disp = self.disp(on_claude=complete_story, **disp_kw)
        code, _, err, _ = invoke(self.run_args(), disp, env=self.env())
        self.assertEqual(code, 0, err)
        return load(self.baseline)["runs"][0]

    def test_gate_scripts_fail_verdicts(self) -> None:
        rec = self._rederived(build_smoke={"verdict": "fail", "exit": 1}, test_integrity={"verdict": "fail", "exit": 1})
        self.assertEqual(rec["gates"]["gate2_build"]["rederived"], "fail")
        self.assertEqual(rec["gates"]["gate4_tests"]["rederived"], "pass")      # jest 3/3 stays the suite value
        self.assertEqual(rec["gates"]["gate4_tests"]["integrity"], "fail")
        self.assertEqual(rec["rederivation"]["build_smoke"]["verdict"], "fail")
        self.assertIsNone(rec["rederivation"]["build_smoke"]["reason"])
        self.assertEqual(rec["rederivation"]["test_integrity"]["verdict"], "fail")

    def test_gate_scripts_unverifiable_carry_the_enumerated_cause(self) -> None:
        causes = [{"code": "build_failed_source", "reason": "environment_unavailable", "detail": "no postgres"}]
        rec = self._rederived(build_smoke={"verdict": "unverifiable", "causes": causes},
                              test_integrity={"verdict": "unverifiable",
                                              "causes": [{"code": "coverage_report_missing", "reason": None}]})
        self.assertEqual(rec["gates"]["gate2_build"]["rederived"], "unverifiable")
        self.assertEqual(rec["gates"]["gate4_tests"]["integrity"], "unverifiable")
        self.assertEqual(rec["rederivation"]["build_smoke"]["reason"], "environment_unavailable")
        self.assertEqual(rec["rederivation"]["test_integrity"]["reason"], "coverage_report_missing")

    def test_gate_scripts_that_cannot_run_are_unverifiable_never_an_exception(self) -> None:
        rec = self._rederived(build_smoke={"stdout": "Traceback (most recent call last)\n  boom\n", "exit": 2},
                              test_integrity={"timeout": True})
        self.assertEqual(rec["status"], "complete")
        self.assertEqual(rec["gates"]["gate2_build"]["rederived"], "unverifiable")
        self.assertEqual(rec["rederivation"]["build_smoke"]["reason"], "exit 2, no verdict in output")
        self.assertEqual(rec["gates"]["gate4_tests"]["integrity"], "unverifiable")
        self.assertEqual(rec["rederivation"]["test_integrity"]["reason"], "timeout after %ds" % pb.GATE_SCRIPT_TIMEOUT_S)
        rec = self._rederived(build_smoke={"stdout": json.dumps({"verdict": "maybe"}), "exit": 0})
        self.assertEqual(rec["gates"]["gate2_build"]["rederived"], "unverifiable")
        self.assertEqual(rec["rederivation"]["build_smoke"]["reason"], "exit 0, no verdict in output")

    def test_gate_script_missing_interpreter_is_unverifiable(self) -> None:
        def no_python(argv, *a, **k):
            raise FileNotFoundError(argv[0])

        with mock.patch.object(pb.subprocess, "run", no_python):
            block = pb.run_gate_script(Path("/w/scripts/build-smoke.py"), ["check", "--project", "/c"],
                                       Path("/c"), {"/w": "<writ_root>", "/c": "<checkout>"})
        self.assertEqual(block, {"argv": ["python3", "<writ_root>/scripts/build-smoke.py", "check", "--project", "<checkout>"],
                                 "verdict": "unverifiable", "reason": "could not start: FileNotFoundError"})

    def test_redact_paths_prefers_the_longest_prefix(self) -> None:
        names = {"/t/run": "<artifacts>", "/t/run/checkout": "<checkout>", "/w": "<writ_root>"}
        self.assertEqual(pb._redact_paths(["/w/s.py", "--project", "/t/run/checkout", "--report=/t/run/cov/x.json", "300"], names),
                         ["<writ_root>/s.py", "--project", "<checkout>", "--report=<artifacts>/cov/x.json", "300"])

    # -- writ.dirty, deps and jest timeouts, overlay / install failures --

    def test_writ_dirty_reflects_the_overlay_source_tree(self) -> None:
        (self.writ.root / "scratch.txt").write_text("uncommitted\n", encoding="utf-8")
        rec = self._rederived()
        self.assertTrue(rec["writ"]["dirty"])
        self.assertEqual(rec["writ"]["commit"], self.writ_head)
        self.assertEqual(list(rec["writ"]), list(pb.WRIT_KEYS))

    def test_pnpm_install_failure_is_recorded_and_the_run_proceeds(self) -> None:
        rec = self._rederived(pnpm_install_exit=1)
        self.assertEqual(rec["deps"]["exit"], 1)
        self.assertEqual(rec["status"], "complete")

    def test_pnpm_install_timeout_is_a_deps_value_not_an_exception(self) -> None:
        disp = self.disp(on_claude=complete_story, pnpm_install_timeout=True)
        code, _, err, _ = invoke(self.run_args("--keep"), disp, env=self.env())
        self.assertEqual(code, 0, err)
        rec = load(self.baseline)["runs"][0]
        self.assertEqual(rec["deps"]["exit"], "timeout")
        self.assertIn("claude", disp.programs())
        log = self.tmp_root / ("writ-baseline-%s-1" % STORY_STEM) / "pnpm-install.log"
        self.assertIn("timed out", log.read_text(encoding="utf-8"))

    def test_jest_timeout_is_zero_over_zero_with_a_reason(self) -> None:
        rec = self._rederived(jest_timeout=True)
        self.assertEqual(rec["tests"]["suite"], {"passed": 0, "total": 0, "reason": "timeout after %ds" % pb.JEST_TIMEOUT_S})
        self.assertEqual(rec["tests"]["original"]["reason"], "timeout after %ds" % pb.JEST_TIMEOUT_S)
        self.assertIsNone(rec["gates"]["gate4_tests"]["rederived"])       # no suite → no verdict
        self.assertEqual(rec["status"], "complete")

    def test_failing_suite_rederives_gate4_as_fail_beside_the_reported_pass(self) -> None:
        disp = self.disp(on_claude=complete_story, jest_suite=(2, 3), jest_exit=1)
        code, out, err, _ = invoke(self.run_args(), disp, env=self.env())
        self.assertEqual(code, 0, err)
        rec = load(self.baseline)["runs"][0]
        self.assertEqual(rec["tests"]["suite"], {"passed": 2, "total": 3, "reason": None})
        self.assertEqual(rec["gates"]["gate4_tests"]["rederived"], "fail")
        self.assertEqual(rec["gates"]["gate4_tests"]["verdict"], "PASS")     # the agent's claim stays beside it
        self.assertEqual(rec["status"], "complete")
        # Business Rule 5: no script exists for Gates 0, 3, 5
        for g in ("gate0_arch", "gate3_review", "gate5_docs"):
            self.assertIsNone(rec["gates"][g]["rederived"], g)
        self.assertIn("tests=2/3", out)

    def test_jest_without_a_report_is_zero_over_zero_never_a_stale_read(self) -> None:
        rec = self._rederived(jest_writes_report=False, jest_exit=1)
        self.assertEqual(rec["tests"]["suite"], {"passed": 0, "total": 0, "reason": "no jest report"})
        self.assertIsNone(rec["gates"]["gate4_tests"]["rederived"])
        self.assertEqual(rec["status"], "complete")
        # a report left behind by an earlier run is removed before jest starts,
        # so a crashed jest cannot be credited with the previous numbers
        checkout = self.tmp_root / "manual" / "checkout"
        report = self.tmp_root / "manual" / "jest-suite.json"
        disp = self.disp(jest_writes_report=False)
        with dispatched(disp):
            pb.build_checkout(self.repo.root, self.parent, checkout.parent)
            report.write_text(json.dumps(jest_json(99, 99)), encoding="utf-8")
            self.assertEqual(pb.run_jest(checkout, report), {"passed": 0, "total": 0, "reason": "no jest report"})
            self.assertFalse(report.exists())
        with dispatched(self.disp(jest_report_text="Killed: 9\n")):
            counts = pb.run_jest(checkout, report)
        self.assertEqual((counts["passed"], counts["total"]), (0, 0))

    def test_jest_compile_failure_is_a_failed_suite_not_an_empty_one(self) -> None:
        """A suite that cannot load reports numTotalTests 0 with success false
        and a failed-suite count; Gate 4 must read `fail`, not `null`."""
        broken = json.dumps({"numPassedTests": 0, "numFailedTests": 0, "numTotalTests": 0,
                             "numFailedTestSuites": 2, "numTotalTestSuites": 2, "success": False})
        rec = self._rederived(jest_report_text=broken, jest_exit=1)
        self.assertEqual(rec["tests"]["suite"], {"passed": 0, "total": 0, "reason": "suite failed to run (2 failed suites)"})
        self.assertEqual(rec["gates"]["gate4_tests"]["rederived"], "fail")
        self.assertEqual(rec["tests"]["original"]["reason"], "suite failed to run (2 failed suites)")
        self.assertEqual(rec["status"], "complete")
        # an honestly empty run (success true, nothing collected) stays null
        empty = json.dumps({"numPassedTests": 0, "numTotalTests": 0, "numFailedTestSuites": 0, "success": True})
        rec = self._rederived(jest_report_text=empty)
        self.assertEqual(rec["tests"]["suite"], {"passed": 0, "total": 0, "reason": None})
        self.assertIsNone(rec["gates"]["gate4_tests"]["rederived"])

    def test_unreadable_jest_report_names_itself(self) -> None:
        rec = self._rederived(jest_report_text="Killed: 9\n", jest_exit=137)
        self.assertEqual(rec["tests"]["suite"], {"passed": 0, "total": 0, "reason": "unreadable jest report"})
        self.assertIsNone(rec["gates"]["gate4_tests"]["rederived"])
        rec = self._rederived(jest_report_text=json.dumps([1, 2]))         # JSON, but not a report
        self.assertEqual(rec["tests"]["suite"]["reason"], "unreadable jest report")
        self.assertEqual(pb._suite_verdict({"passed": 2, "total": 3, "reason": None}), "fail")
        self.assertEqual(pb._suite_verdict({"passed": 3, "total": 3, "reason": None}), "pass")
        self.assertIsNone(pb._suite_verdict({"passed": 0, "total": 0, "reason": "no jest report"}))

    def test_original_test_files_absent_at_the_story_commit_are_skipped(self) -> None:
        ghost = "lib/__tests__/ghost.test.ts"
        write_baseline(self.baseline, [selection_entry(self.parent, self.story, [ghost, TEST_FILE])], self.head)
        disp = self.disp(on_claude=complete_story)
        code, _, err, _ = invoke(self.run_args("--keep"), disp, env=self.env())
        self.assertEqual(code, 0, err)
        rec = load(self.baseline)["runs"][0]
        self.assertEqual(rec["tests"]["original"], {"passed": 1, "total": 1, "reason": None, "files": [TEST_FILE]})
        checkout = self.tmp_root / ("writ-baseline-%s-1" % STORY_STEM) / "checkout"
        self.assertFalse((checkout / ghost).exists())            # never materialized as an empty file
        by_path = [c for c in disp.calls if c[:3] == ["pnpm", "exec", "jest"] and "--runTestsByPath" in c]
        self.assertEqual(by_path[0][by_path[0].index("--runTestsByPath") + 1:], [TEST_FILE])
        # nothing restorable → no second jest run and an empty original block
        write_baseline(self.baseline, [selection_entry(self.parent, self.story, [ghost])], self.head)
        disp = self.disp(on_claude=complete_story)
        code, _, err, _ = invoke(self.run_args(), disp, env=self.env())
        self.assertEqual(code, 0, err)
        rec = load(self.baseline)["runs"][0]
        self.assertEqual(rec["tests"]["original"], {"passed": 0, "total": 0, "reason": None, "files": []})
        self.assertEqual(sum(1 for c in disp.calls if c[:3] == ["pnpm", "exec", "jest"]), 1)

    def test_each_record_is_flushed_before_the_next_run_starts(self) -> None:
        seen = []

        def observe(cwd: Path) -> None:
            seen.append(len(load(self.baseline)["runs"]))    # what a crash right now would leave behind
            complete_story(cwd)

        disp = self.disp(on_claude=observe)
        code, out, err, _ = invoke(self.run_args("--runs", "3"), disp, env=self.env())
        self.assertEqual(code, 0, err)
        self.assertEqual(seen, [0, 1, 2])
        self.assertEqual([r["run"] for r in load(self.baseline)["runs"]], [1, 2, 3])
        self.assertEqual(len([l for l in out.splitlines() if l.startswith("run: ")]), 3)
        self.assertEqual(self.run_dirs(), [])

    def test_timeout_continues_to_the_next_run(self) -> None:
        disp = self.disp(claude_timeout=True, events=stream_events(with_result=False))
        code, out, err, killed = invoke(self.run_args("--runs", "2", "--cap", "7"), disp, env=self.env())
        self.assertEqual(code, 0, err)
        self.assertEqual([(r["run"], r["status"]) for r in load(self.baseline)["runs"]],
                         [(1, "timeout"), (2, "timeout")])
        self.assertEqual(disp.programs().count("claude"), 2)
        self.assertEqual([sig for _, sig in killed], [15, 9, 15, 9])
        self.assertEqual(len([l for l in out.splitlines() if l.startswith("run: ")]), 2)
        self.assertEqual(self.run_dirs(), [])

    def test_parent_without_sub_specs_is_inputs_missing(self) -> None:
        repo = Repo(self.root / "bare")
        parent = repo.commit({STORY_REL: story_text("Not Started"),
                              ".writ/specs/%s/spec.md" % FOLDER: "x\n",
                              ".writ/specs/%s/spec-lite.md" % FOLDER: "x\n"}, "parent without sub-specs")
        story = repo.commit({TEST_FILE: CLEAN_TEST}, "story")
        write_baseline(self.baseline, [selection_entry(parent, story)], repo.git("rev-parse", "HEAD"))
        disp = Dispatcher(repo.root, self.root)
        code, _, err, _ = invoke(self.run_args(yuss=repo.root), disp, env=self.env())
        self.assertEqual(code, 0, err)
        rec = load(self.baseline)["runs"][0]
        self.assertEqual((rec["status"], rec["reason"]), ("error", "inputs_missing"))
        self.assertTrue(rec["isolation"]["asserted"])
        self.assertNotIn("claude", disp.programs())
        self.assertEqual(repo.git("status", "--porcelain"), "")

    def test_overlay_failure_is_an_error_record_before_deps_or_claude(self) -> None:
        disp = self.disp(install_exit=1)
        code, _, err, _ = invoke(self.run_args(), disp, env=self.env())
        self.assertEqual(code, 0, err)
        rec = load(self.baseline)["runs"][0]
        self.assertEqual((rec["status"], rec["reason"]), ("error", "overlay_failed"))
        self.assertTrue(rec["isolation"]["answer_scrub_asserted"])
        self.assertIsNone(rec["writ"])
        self.assertIsNone(rec["deps"])
        self.assertNotIn("pnpm", disp.programs())
        self.assertNotIn("claude", disp.programs())
        self.assertEqual(self.run_dirs(), [])

    def test_invalid_baseline_json_is_refused(self) -> None:
        self.baseline.write_text("{not json", encoding="utf-8")
        disp = self.disp()
        code, _, err, _ = invoke(self.run_args(), disp, env=self.env())
        self.assertEqual(code, 2)
        self.assertIn("not valid JSON", err)
        self.assertEqual(disp.calls, [])
        self.assertEqual(self.run_dirs(), [])

    def test_inputs_missing_at_parent_is_an_error_record(self) -> None:
        with TemporaryDirectory() as tmp:
            repo, paths, shas = four_class_repo(Path(tmp) / "yuss")
            repo.stage_stories()
            head = repo.git("rev-parse", "HEAD")
            parent = repo.git("rev-parse", shas["api_route"] + "^1")
            entry = dict(selection_entry(parent, shas["api_route"], ["app/api/foo/__tests__/route.test.ts"]))
            entry.update(story_path=paths["api_route"], spec_folder="2026-01-01-alpha",
                         story_id="2026-01-01-alpha/story-1-api-foo")
            write_baseline(self.baseline, [entry], head)
            disp = Dispatcher(repo.root, self.root)
            code, out, err, _ = invoke(self.run_args(yuss=repo.root), disp, env=self.env())
            self.assertEqual(code, 0, err)
            rec = load(self.baseline)["runs"][0]
            self.assertEqual((rec["status"], rec["reason"]), ("error", "inputs_missing"))
            self.assertIsNone(rec["inputs"])
            self.assertTrue(rec["isolation"]["asserted"])
            self.assertNotIn("claude", disp.programs())
            # the fallback tried `git show <parent_sha>:<path>` against yuss, never HEAD
            shows = [c for c in disp.calls if c[0] == "git" and "show" in c]
            self.assertTrue(shows)
            self.assertTrue(all(parent in c[-1] for c in shows), shows)
            self.assertEqual(repo.git("status", "--porcelain"), "")

    def test_inputs_fallback_via_git_show_when_tree_lacks_them(self) -> None:
        """The checkout is the parent tree, so the fallback only fires when a
        file is absent from the tree; simulate by deleting it after checkout."""
        real_build = pb.build_checkout

        def build_then_drop(yuss, sha, run_dir):
            checkout, iso = real_build(yuss, sha, run_dir)
            (checkout / ".writ/specs" / FOLDER / "spec-lite.md").unlink()
            pb.rmtree(checkout / ".writ/specs" / FOLDER / "sub-specs")
            return checkout, iso

        disp = self.disp(on_claude=complete_story)
        with mock.patch.object(pb, "build_checkout", build_then_drop):
            code, _, err, _ = invoke(self.run_args("--keep"), disp, env=self.env())
        self.assertEqual(code, 0, err)
        rec = load(self.baseline)["runs"][0]
        self.assertEqual(rec["inputs"], "parent_show")
        self.assertEqual(rec["status"], "complete")
        spec = self.tmp_root / ("writ-baseline-%s-1" % STORY_STEM) / "checkout" / ".writ/specs" / FOLDER
        self.assertEqual((spec / "spec-lite.md").read_text(encoding="utf-8"), "# Widget lite\n")
        self.assertEqual((spec / "sub-specs/technical-spec.md").read_text(encoding="utf-8"), "# Tech\n")
        self.assertEqual((spec / "sub-specs/nested/api.md").read_text(encoding="utf-8"), "# API\n")
        # every input read named the parent SHA, never HEAD; the only other
        # `show` is the post-agent restore of the original test at story_commit
        shows = [c[-1] for c in disp.calls if c[0] == "git" and "show" in c and c[c.index("-C") + 1] == str(self.repo.root)]
        inputs = [s for s in shows if not s.startswith(self.story + ":")]
        self.assertGreaterEqual(len(inputs), 4)
        self.assertTrue(all(s.startswith(self.parent + ":") for s in inputs), inputs)
        self.assertEqual([s for s in shows if s.startswith(self.story + ":")], ["%s:%s" % (self.story, TEST_FILE)])

    def test_answer_leak_in_staged_story_aborts_before_claude(self) -> None:
        repo = Repo(self.root / "leaky")
        parent = repo.commit({STORY_REL: story_text("Completed ✅", commit="abc1234", wwb=True),
                              ".writ/specs/%s/spec.md" % FOLDER: "x\n",
                              ".writ/specs/%s/spec-lite.md" % FOLDER: "x\n",
                              ".writ/specs/%s/sub-specs/t.md" % FOLDER: "x\n"}, "leaky parent")
        story = repo.commit({TEST_FILE: CLEAN_TEST}, "story")
        write_baseline(self.baseline, [selection_entry(parent, story)], repo.git("rev-parse", "HEAD"))
        disp = Dispatcher(repo.root, self.root)
        code, _, err, _ = invoke(self.run_args(yuss=repo.root), disp, env=self.env())
        self.assertEqual(code, 0, err)
        rec = load(self.baseline)["runs"][0]
        self.assertEqual((rec["status"], rec["reason"]), ("error", "answer_leak"))
        self.assertFalse(rec["isolation"]["answer_scrub_asserted"])
        self.assertNotIn("claude", disp.programs())

    def test_keep_retains_run_dir_and_sidecar(self) -> None:
        disp = self.disp(on_claude=complete_story)
        code, _, err, _ = invoke(self.run_args("--keep"), disp, env=self.env())
        self.assertEqual(code, 0, err)
        self.assertEqual(self.run_dirs(), ["writ-baseline-%s-1" % STORY_STEM])
        run_dir = self.tmp_root / self.run_dirs()[0]
        meta = load(run_dir / "run-meta.json")
        for k in ("story_id", "run", "parent_sha", "isolation", "writ", "deps", "started_at", "invocation",
                  "elapsed_s", "timed_out"):
            self.assertIn(k, meta)
        self.assertEqual(meta["parent_sha"], self.parent)
        self.assertTrue((run_dir / "transcript.jsonl").is_file())
        self.assertTrue((run_dir / "stderr.log").is_file())
        self.assertTrue((run_dir / "jest-suite.json").is_file())
        self.assertTrue((run_dir / "coverage" / "coverage-final.json").is_file())
        self.assertFalse((run_dir / "checkout" / "jest-suite.json").exists())
        self.assertFalse((run_dir / "checkout" / "coverage").exists())
        self.assertFalse((run_dir / "checkout" / "run-meta.json").exists())

    def test_story_filter_and_stale_run_dir_replaced(self) -> None:
        stale = self.tmp_root / ("writ-baseline-%s-1" % STORY_STEM)
        (stale / "junk").mkdir(parents=True)
        disp = self.disp(on_claude=complete_story)
        code, _, err, _ = invoke(self.run_args("--story", STORY_STEM), disp, env=self.env())
        self.assertEqual(code, 0, err)
        self.assertEqual(len(load(self.baseline)["runs"]), 1)
        code, _, err, _ = invoke(self.run_args("--story", "nope"), disp, env=self.env())
        self.assertEqual(code, 2)
        self.assertIn("nope", err)

    def test_yuss_head_change_aborts_loudly(self) -> None:
        disp = self.disp(on_claude=complete_story, yuss_heads=[self.head, "f" * 40])
        code, _, err, _ = invoke(self.run_args("--runs", "2"), disp, env=self.env())
        self.assertEqual(code, 3)
        self.assertIn("yuss HEAD", err)
        doc = load(self.baseline)
        self.assertEqual(len(doc["runs"]), 1)
        self.assertFalse(doc["runs"][0]["yuss_head_unchanged"])
        self.assertEqual(disp.programs().count("claude"), 1)

    def test_scrub_failure_never_reaches_the_file(self) -> None:
        disp = self.disp(on_claude=complete_story)
        with mock.patch.object(pb, "assemble_record", lambda *a, **k: {"story_id": STORY_ID, "run": 1, "k": FAKE_KEY}):
            code, out, err, _ = invoke(self.run_args(), disp, env=self.env())
        self.assertEqual(code, 3)
        self.assertIn("scrub", err)
        self.assertNotIn(FAKE_KEY, err + out)
        self.assertEqual(load(self.baseline)["runs"], [])
        # the transcript is kept for a manual ingest after the record is fixed
        run_dir = self.tmp_root / ("writ-baseline-%s-1" % STORY_STEM)
        self.assertTrue((run_dir / "transcript.jsonl").is_file())
        self.assertIn("run dir kept: %s" % run_dir, err)

    def test_no_result_event_is_an_error_record(self) -> None:
        disp = self.disp(events=stream_events(with_result=False))
        code, _, err, _ = invoke(self.run_args(), disp, env=self.env())
        self.assertEqual(code, 0, err)
        rec = load(self.baseline)["runs"][0]
        self.assertEqual((rec["status"], rec["reason"]), ("error", "no_result_event"))
        self.assertEqual(rec["tokens"], {"input": None, "output": None, "cache_read": None, "cache_creation": None})
        self.assertIsNone(rec["cost_usd"])

    def test_rederive_completion_predicates(self) -> None:
        run_dir = self.tmp_root / "writ-baseline-x-1"
        disp = self.disp()
        with dispatched(disp):
            checkout, _ = pb.build_checkout(self.repo.root, self.parent, run_dir)
            self.assertEqual(pb.rederive_completion(checkout, STORY_REL), "unmet")
            story = checkout / STORY_REL
            story.write_text(story_text("Completed ✅", commit="deadbeefcafe", wwb=True), encoding="utf-8")
            self.assertEqual(pb.rederive_completion(checkout, STORY_REL), "unmet")   # sha not in repo
            complete_story(checkout)
            self.assertEqual(pb.rederive_completion(checkout, STORY_REL), "met")
            story.write_text(story_text("Completed ✅", commit=self.parent), encoding="utf-8")
            self.assertEqual(pb.rederive_completion(checkout, STORY_REL), "unmet")   # no What Was Built
            story.unlink()
            self.assertEqual(pb.rederive_completion(checkout, STORY_REL), "unmet")


# ---------------------------------------------------------------------------
# ingest (AC-4.5)
# ---------------------------------------------------------------------------


class IngestTest(Case):
    def _ingest_args(self, checkout: Path, transcript: Path, baseline: Path, *extra: str) -> list:
        return ["ingest", "--baseline", str(baseline), "--yuss", str(self.repo.root), "--writ-root", str(self.writ.root),
                "--tmp-root", str(self.tmp_root), "--checkout", str(checkout), "--transcript", str(transcript), *extra]

    def test_ingest_refuses_a_non_git_checkout_and_a_missing_transcript(self) -> None:
        plain = self.root / "plain"
        plain.mkdir()
        transcript = self.root / "t.jsonl"
        transcript.write_text("", encoding="utf-8")
        disp = self.disp()
        code, _, err, _ = invoke(self._ingest_args(plain, transcript, self.baseline), disp, env=self.env(key=False))
        self.assertEqual(code, 2)
        self.assertIn("not a git checkout", err)
        checkout = self.tmp_root / "manual" / "checkout"
        with dispatched(disp):
            pb.build_checkout(self.repo.root, self.parent, checkout.parent)
        code, _, err, _ = invoke(self._ingest_args(checkout, self.root / "missing.jsonl", self.baseline), disp,
                                 env=self.env(key=False))
        self.assertEqual(code, 2)
        self.assertIn("missing.jsonl", err)
        self.assertEqual(load(self.baseline)["runs"], [])
        self.assertEqual(self.run_dirs(), [])

    def test_ingest_reproduces_the_run_record(self) -> None:
        disp = self.disp(on_claude=complete_story)
        code, _, err, _ = invoke(self.run_args("--keep"), disp, env=self.env())
        self.assertEqual(code, 0, err)
        run_rec = load(self.baseline)["runs"][0]
        run_dir = self.tmp_root / ("writ-baseline-%s-1" % STORY_STEM)
        other = self.root / "baselines" / "copy.json"
        write_baseline(other, [selection_entry(self.parent, self.story)], self.head, runs_per_story=1)
        disp2 = self.disp()
        code, out, err, _ = invoke(self._ingest_args(run_dir / "checkout", run_dir / "transcript.jsonl", other),
                                   disp2, env=self.env(key=False))
        self.assertEqual(code, 0, err)
        doc = load(other)
        self.assertEqual(doc["runs_per_story"], 1)   # untouched
        self.assertEqual(doc["runs"][0], run_rec)
        self.assertNotIn("claude", disp2.programs())
        self.assertNotIn("bash", disp2.programs())
        self.assertTrue(any(l.startswith("ingest: ") for l in out.splitlines()))
        self.assertEqual(self.run_dirs(), ["writ-baseline-%s-1" % STORY_STEM])   # ingest never deletes

    def test_ingest_without_sidecar(self) -> None:
        checkout = self.tmp_root / "manual" / "checkout"
        disp = self.disp()
        with dispatched(disp):
            pb.build_checkout(self.repo.root, self.parent, checkout.parent)
            complete_story(checkout)
        transcript = self.root / "session.jsonl"
        transcript.write_text("".join(json.dumps(e) + "\n" for e in session_events()), encoding="utf-8")
        code, _, err, _ = invoke(self._ingest_args(checkout, transcript, self.baseline), disp, env=self.env(key=False))
        self.assertEqual(code, 2)
        self.assertIn("--story-id", err)
        code, _, err, _ = invoke(self._ingest_args(checkout, transcript, self.baseline, "--story-id", STORY_ID, "--run", "1"),
                                 disp, env=self.env(key=False))
        self.assertEqual(code, 0, err)
        rec = load(self.baseline)["runs"][0]
        self.assertEqual(list(rec)[:len(pb.RUN_KEYS)], list(pb.RUN_KEYS))
        self.assertEqual(rec["background_tasks_outstanding"], 0)
        self.assertEqual(rec["isolation"], {"reachable_commits": None, "expected": 1, "asserted": False,
                                            "answer_scrub_asserted": False})
        self.assertEqual(rec["reason"], "ingested without sidecar")
        self.assertIsNone(rec["writ"])
        self.assertIsNone(rec["deps"])
        self.assertEqual(rec["status"], "complete")
        self.assertEqual(rec["exit_criteria"]["rederived"], "met")
        self.assertEqual(rec["wall_clock_s"], 150.0)
        self.assertEqual(rec["invocation"]["permission_mode"], None)
        self.assertIsNone(load(self.baseline)["runs_per_story"])

    def test_sidecar_less_ingest_keeps_the_transcript_stop_reason(self) -> None:
        """A budget stop explains `status: budget`; the provenance note must
        not mask it (isolation.asserted: false already marks the ingest)."""
        checkout = self.tmp_root / "manual" / "checkout"
        disp = self.disp()
        with dispatched(disp):
            pb.build_checkout(self.repo.root, self.parent, checkout.parent)
        transcript = self.root / "budget.jsonl"
        transcript.write_text("".join(json.dumps(e) + "\n" for e in stream_events(subtype="error_max_budget_usd")),
                              encoding="utf-8")
        code, _, err, _ = invoke(self._ingest_args(checkout, transcript, self.baseline, "--story-id", STORY_ID, "--run", "1"),
                                 disp, env=self.env(key=False))
        self.assertEqual(code, 0, err)
        rec = load(self.baseline)["runs"][0]
        self.assertEqual((rec["status"], rec["reason"]), ("budget", "error_max_budget_usd"))
        self.assertFalse(rec["isolation"]["asserted"])
        # the same stream with a sidecar carries the same reason (AC-4.5 shape parity)
        pb.write_json(checkout.parent / "run-meta.json",
                      {"story_id": STORY_ID, "run": 1, "started_at": "2026-09-06T00:00:00Z", "reason": None})
        code, _, err, _ = invoke(self._ingest_args(checkout, transcript, self.baseline, "--force"), disp, env=self.env(key=False))
        self.assertEqual(code, 0, err)
        self.assertEqual(load(self.baseline)["runs"][0]["reason"], "error_max_budget_usd")

    def test_ingest_refuses_duplicate_pair_and_unknown_story(self) -> None:
        disp = self.disp(on_claude=complete_story)
        code, _, err, _ = invoke(self.run_args("--keep"), disp, env=self.env())
        self.assertEqual(code, 0, err)
        run_dir = self.tmp_root / ("writ-baseline-%s-1" % STORY_STEM)
        args = self._ingest_args(run_dir / "checkout", run_dir / "transcript.jsonl", self.baseline)
        code, _, err, _ = invoke(args, self.disp(), env=self.env(key=False))
        self.assertEqual(code, 2)
        self.assertIn("already", err)
        code, _, err, _ = invoke(args + ["--force"], self.disp(), env=self.env(key=False))
        self.assertEqual(code, 0, err)
        self.assertEqual(len(load(self.baseline)["runs"]), 1)   # replaced, not duplicated
        code, _, err, _ = invoke(args + ["--story-id", "nope/story-9-x", "--run", "1"], self.disp(), env=self.env(key=False))
        self.assertEqual(code, 2)
        self.assertIn("nope/story-9-x", err)

    def test_ingest_scrubs_transcript_controlled_strings_before_writing(self) -> None:
        """The `result` subtype lands in `reason` verbatim: a transcript is
        untrusted input to the record, and ingest has no earlier scrub."""
        checkout = self.tmp_root / "manual" / "checkout"
        disp = self.disp()
        with dispatched(disp):
            pb.build_checkout(self.repo.root, self.parent, checkout.parent)
            complete_story(checkout)
        pb.write_json(checkout.parent / "run-meta.json",
                      {"story_id": STORY_ID, "run": 1, "started_at": "2026-09-06T00:00:00Z", "reason": None})
        transcript = self.root / "hostile.jsonl"
        stale = self.tmp_root / ("writ-baseline-ingest-%s-1" % STORY_STEM)
        before = self.baseline.read_bytes()
        args = self._ingest_args(checkout, transcript, self.baseline)
        for subtype, marker in (("error_" + FAKE_KEY, "key material"), ("error_" + "x" * 200, "characters")):
            transcript.write_text("".join(json.dumps(e) + "\n" for e in stream_events(subtype=subtype)), encoding="utf-8")
            (stale / "junk").mkdir(parents=True)                  # artifacts left by an interrupted ingest
            code, out, err, _ = invoke(args, disp, env=self.env(key=False))
            self.assertEqual(code, 3)
            self.assertIn("scrub", err)
            self.assertIn(marker, err)
            self.assertNotIn(FAKE_KEY, err + out)
            self.assertNotIn("x" * 50, err + out)
            self.assertEqual(self.baseline.read_bytes(), before)
            self.assertFalse(stale.exists())                      # replaced, then removed even on refusal
        self.assertEqual(self.run_dirs(), [])


class CliTest(unittest.TestCase):
    def test_help_for_run_and_ingest(self) -> None:
        for sub in ("run", "ingest"):
            out = io.StringIO()
            with self.assertRaises(SystemExit) as ctx, contextlib.redirect_stdout(out):
                pb.main([sub, "--help"])
            self.assertEqual(ctx.exception.code, 0)
            self.assertIn("--baseline", out.getvalue())
            self.assertIn("--yuss", out.getvalue())
        out = io.StringIO()
        with self.assertRaises(SystemExit) as ctx, contextlib.redirect_stdout(out):
            pb.main(["run", "--help"])
        for flag in ("--runs", "--cap", "--budget-usd", "--keep", "--force", "--story", "--model", "--driver"):
            self.assertIn(flag, out.getvalue())

    def test_compare_requires_two_paths(self) -> None:
        err = io.StringIO()
        with self.assertRaises(SystemExit) as ctx, contextlib.redirect_stderr(err):
            pb.main(["compare"])
        self.assertEqual(ctx.exception.code, 2)
        self.assertNotIn("not implemented", err.getvalue())
        self.assertRegex(err.getvalue(), r"compare|the following arguments are required")


if __name__ == "__main__":
    unittest.main()
