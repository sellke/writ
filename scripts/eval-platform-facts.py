#!/usr/bin/env python3
"""Recheck third-party platform facts that Writ's adapters rely on.

Dev-only (the `eval-` prefix keeps it out of installs). Phase 14's acceptance
pass found adapter rows written from docs or memory that the installed CLIs
contradicted: Cursor agent frontmatter, the removed `/agents` wizard, a
`--tools ""` flag that ate the prompt, Codex's missing identity file, and
Claude Code's question tool. Each fact below names the adapter row it
supports and how to observe it on the installed version.

usage: python3 scripts/eval-platform-facts.py [--live] [--json]
  default  help-text and version checks only; no model call
  --live   also start one short headless session per CLI (small model cost)
Exit 0 when every checked fact holds, 1 when one changed. A fact whose CLI is
missing is `unverifiable` and does not fail the run.
"""
import json
import shutil
import subprocess
import sys
import tempfile
from typing import Callable, Dict, List, Optional

HOLDS, CHANGED, UNVERIFIABLE = "holds", "changed", "unverifiable"


def run(args: List[str], cwd: Optional[str] = None, timeout: int = 300) -> str:
    try:
        r = subprocess.run(args, capture_output=True, text=True, timeout=timeout, cwd=cwd,
                           stdin=subprocess.DEVNULL)
    except (OSError, subprocess.TimeoutExpired) as e:
        return "ERROR: %s" % e
    return r.stdout + r.stderr


def has_all(text: str, needles: List[str]) -> bool:
    return all(n in text for n in needles)


def claude_init(tools: str) -> Dict:
    """The init event of a one-turn headless session in an empty folder."""
    with tempfile.TemporaryDirectory() as d:
        out = run(["claude", "-p", "Reply with: ok", "--output-format", "stream-json", "--verbose",
                   "--setting-sources", "project", "--no-session-persistence", "--max-turns", "1",
                   "--model", "claude-haiku-5-5", "--tools", tools], cwd=d)
    for line in out.splitlines():
        try:
            e = json.loads(line)
        except ValueError:
            continue
        if e.get("type") == "system" and e.get("subtype") == "init":
            return e
    return {}


# (id, CLI, adapter row the fact supports, statement, live?, check) where
# check returns (observed text, holds?)
FACTS = []  # type: List[tuple]


def fact(fid: str, cli: str, row: str, statement: str, live: bool = False):
    def wrap(check: Callable[[], tuple]):
        FACTS.append((fid, cli, row, statement, live, check))
        return check
    return wrap


@fact("CC1", "claude", "UAT plans and the acceptance harness",
      "`claude --help` offers --tools, --setting-sources, --plugin-dir, --output-format, "
      "--no-session-persistence, and --permission-mode")
def _cc1():
    flags = ["--tools", "--setting-sources", "--plugin-dir", "--output-format",
             "--no-session-persistence", "--permission-mode"]
    text = run(["claude", "--help"])
    return ", ".join(f for f in flags if f not in text) or "all present", has_all(text, flags)


@fact("CC2", "claude", "README § Claude Code (plugin)",
      "`claude plugin install` installs at user scope by default")
def _cc2():
    text = run(["claude", "plugin", "install", "--help"])
    ok = '(default: "user")' in " ".join(text.split())
    return "default user scope" if ok else "default scope text not found", ok


@fact("CC3", "claude", "adapters/claude-code.md AskQuestion row (fallback)",
      "Headless `claude -p` has no AskUserQuestion, TodoWrite, or EnterPlanMode, even when "
      "--tools names them; Glob, Grep, and Read load when named", live=True)
def _cc3():
    tools = claude_init("AskUserQuestion,TodoWrite,EnterPlanMode,Glob,Grep,Read").get("tools", [])
    if not tools:
        return "no init event", False
    absent = [t for t in ("AskUserQuestion", "TodoWrite", "EnterPlanMode") if t not in tools]
    present = [t for t in ("Glob", "Grep", "Read") if t in tools]
    return "loaded: %s" % ", ".join(sorted(tools)), len(absent) == 3 and len(present) == 3


@fact("CC4", "claude", "adapters/claude-code.md Verification record, headless row",
      "Headless `claude -p` loads the Artifact tool by default (2026-10-24 observation; "
      "account-dependent)", live=True)
def _cc4():
    tools = claude_init("default").get("tools", [])
    return ("Artifact loaded" if "Artifact" in tools else "Artifact not loaded"), "Artifact" in tools


@fact("CC5", "claude", "plugin-distribution UAT S9 (inventory step)",
      "The headless init event lists the loaded agents and slash commands, so the inventory "
      "check needs no interactive `/agents` screen", live=True)
def _cc5():
    init = claude_init("Read")
    agents, cmds = init.get("agents", []), init.get("slash_commands", [])
    return "%d agents, %d slash commands" % (len(agents), len(cmds)), bool(agents) and bool(cmds)


@fact("CX1", "codex", "acceptance harness (codex exec)",
      "`codex exec` offers --json, --ignore-user-config, and --sandbox; `codex exec resume` "
      "has no --sandbox, so a resumed turn sets sandbox_mode with -c")
def _cx1():
    ex, rs = run(["codex", "exec", "--help"]), run(["codex", "exec", "resume", "--help"])
    ok = has_all(ex, ["--json", "--ignore-user-config", "--sandbox"]) and "--sandbox" not in rs
    return "exec flags present; resume without --sandbox" if ok else "flags differ", ok


@fact("CX2", "codex", "adapters/codex.md file_search and codebase_search rows",
      "Codex calls shell commands (exec_command) and apply_patch; it has no Glob or Grep tool "
      "(model self-report, weaker than a platform record)", live=True)
def _cx2():
    with tempfile.TemporaryDirectory() as d:
        last = d + "/last.txt"
        run(["codex", "exec", "--ignore-user-config", "--skip-git-repo-check", "-s", "read-only",
             "-o", last, "List the exact names of every tool or function you can call in this session, "
             "one per line, with no other text."], cwd=d)
        try:
            out = open(last).read()
        except OSError:
            out = ""
    names = {line.strip().split(".")[-1] for line in out.splitlines() if line.strip()}
    ok = "exec_command" in names and "apply_patch" in names and not names & {"Glob", "Grep", "glob", "grep"}
    keep = sorted(n for n in names if not n.startswith("mcp__"))[:12]
    return "self-reported: %s" % ", ".join(keep), ok


@fact("CU1", "cursor-agent", "adapters/cursor.md (all plugin and canvas rows)",
      "A Cursor CLI is installed, so Cursor facts can be rechecked headless")
def _cu1():
    return "cursor-agent on PATH", True


def main(argv: List[str]) -> int:
    live, as_json = "--live" in argv, "--json" in argv
    rows = []
    versions = {cli: run([cli, "--version"]).strip().splitlines()[0] if shutil.which(cli) else "not installed"
                for cli in ("claude", "codex", "cursor-agent")}
    for fid, cli, row, statement, needs_live, check in FACTS:
        if not shutil.which(cli):
            rows.append((fid, cli, row, statement, UNVERIFIABLE, "%s not installed" % cli))
            continue
        if needs_live and not live:
            rows.append((fid, cli, row, statement, UNVERIFIABLE, "needs --live"))
            continue
        observed, ok = check()
        rows.append((fid, cli, row, statement, HOLDS if ok else CHANGED, observed))
    if as_json:
        print(json.dumps({"versions": versions, "facts": [dict(zip(
            ("id", "cli", "row", "fact", "status", "observed"), r)) for r in rows]}, indent=2))
    else:
        print("versions: " + "; ".join("%s %s" % kv for kv in versions.items()))
        print("| Id | Fact | Status | Observed |\n|---|---|---|---|")
        for fid, _, _, statement, status, observed in rows:
            print("| %s | %s | %s | %s |" % (fid, statement, status, observed.replace("|", "/")[:160]))
    return 1 if any(r[4] == CHANGED for r in rows) else 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
