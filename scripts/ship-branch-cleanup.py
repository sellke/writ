#!/usr/bin/env python3
"""Delete the local branch `/ship` landed (Story 2 of `2026-11-09-delete-merged-branches`).

`/ship` Step 6b runs this after the PR merges. It deletes the local branch only
when no commit is lost, and never touches a remote head.

CLI:
  ship-branch-cleanup.py delete --branch B --default D [--pr-state S]
                                [--pr-head SHA] [--repo .]

  --branch    the local branch the PR came from
  --default   the branch the PR merged into
  --pr-state  the PR state from a `gh pr view` the caller already ran (MERGED)
  --pr-head   the PR's headRefOid from that same call (a full object id)
  --repo      the checkout to clean up (default .)

The script never calls gh. Without --pr-head only the `git branch --merged`
proof applies.

Checks, in order (the first that decides wins):
  1  git config --bool writ.deleteMergedBranches is false -> skipped opted_out
     (absent or unreadable means true)
  2  B equals D -> skipped default_branch; B absent locally -> skipped no_branch
  3  B checked out in a worktree other than --repo
                                    -> kept checked_out_elsewhere:<path>
  4  git fetch origin D fails       -> kept fetch_failed
  5  git branch --merged origin/D lists B -> method -d
  6  else --pr-state MERGED and git rev-parse B equals --pr-head -> method -D
  7  else -> kept not_merged, or local_commits_not_in_pr when --pr-head was
     given and differs
  8  B checked out here and git status --porcelain non-empty or failing
     -> kept dirty_tree
  9  B checked out here -> git checkout D, then git pull --ff-only; a failure
     -> kept switch_failed (the checkout may be left on D)
  10 git branch <method> B -> deleted; else kept delete_failed:<git message>

Output: one JSON line on stdout, exit 0 for every outcome:
  {"schema": "ship-branch-cleanup-v1", "status": "deleted"|"kept"|"skipped",
   "reason": "<code>", "method": "-d"|"-D"|null, "branch": B, "default": D}
  reason on deleted: merged (method -d) or pr_merged (method -D).
  method is the `git branch` flag that ran; null when no delete ran.

Usage errors (a missing option, a name starting with "-", a --repo that is not
a git checkout) exit 2 with usage on stderr and nothing on stdout.

The fetch and the pull reach origin through git, each under a
NETWORK_TIMEOUT-second timeout with terminal prompts off; a timeout counts as a
failure.
"""

from __future__ import annotations

import argparse
import json
import os
import subprocess
import sys
from typing import List, Optional, Tuple

SCHEMA = "ship-branch-cleanup-v1"
NETWORK_TIMEOUT = 120


class UsageError(Exception):
    pass


def git(repo: str, *args: str, timeout: Optional[int] = None) -> Tuple[int, str, str]:
    """Run git in `repo`; return (exit, stdout, stderr). A timeout reads as exit 124."""
    env = dict(os.environ, GIT_TERMINAL_PROMPT="0")
    try:
        done = subprocess.run(["git", "-C", repo] + list(args), capture_output=True,
                              text=True, env=env, timeout=timeout)
    except subprocess.TimeoutExpired:
        return 124, "", "timed out after %ds" % timeout
    except OSError as exc:  # no git on PATH
        raise UsageError("cannot run git: %s" % exc)
    return done.returncode, done.stdout, done.stderr


def opted_out(repo: str) -> bool:
    code, out, _ = git(repo, "config", "--bool", "writ.deleteMergedBranches")
    return code == 0 and out.strip() == "false"


def branch_exists(repo: str, branch: str) -> bool:
    return git(repo, "show-ref", "--verify", "--quiet", "refs/heads/" + branch)[0] == 0


def worktrees_with(repo: str, branch: str) -> List[str]:
    """Paths of every worktree that has `branch` checked out."""
    code, out, _ = git(repo, "worktree", "list", "--porcelain")
    if code != 0:
        return []
    paths, current = [], None
    for line in out.splitlines():
        if line.startswith("worktree "):
            current = line[len("worktree "):]
        elif line == "branch refs/heads/" + branch and current is not None:
            paths.append(current)
    return paths


def merged_into(repo: str, branch: str, target: str) -> bool:
    code, out, _ = git(repo, "branch", "--list", "--merged", target,
                       "--format=%(refname)")
    return code == 0 and ("refs/heads/" + branch) in out.splitlines()


def first_line(text: str) -> str:
    for line in text.splitlines():
        if line.strip():
            return line.strip()
    return "unknown error"


def decide(repo: str, toplevel: str, branch: str, default: str,
           pr_state: Optional[str], pr_head: Optional[str]) -> Tuple[str, str, Optional[str]]:
    """Return (status, reason, method) after running checks 1-10."""
    # 1-2: skipped, nothing read beyond config and refs.
    if opted_out(repo):
        return "skipped", "opted_out", None
    if branch == default:
        return "skipped", "default_branch", None
    if not branch_exists(repo, branch):
        return "skipped", "no_branch", None

    # 3: another worktree holds the branch; git would refuse, so never force it.
    here = os.path.realpath(toplevel)
    holders = worktrees_with(repo, branch)
    for path in holders:
        if os.path.realpath(path) != here:
            return "kept", "checked_out_elsewhere:" + path, None
    checked_out_here = bool(holders)

    # 4: refresh origin/<default> so the merge proof is current.
    if git(repo, "fetch", "origin", default, timeout=NETWORK_TIMEOUT)[0] != 0:
        return "kept", "fetch_failed", None

    # 5-7: the proof that no commit is lost.
    tip = git(repo, "rev-parse", "--verify", "refs/heads/" + branch)[1].strip()
    if merged_into(repo, branch, "refs/remotes/origin/" + default):
        method = "-d"
    elif (pr_state or "").upper() == "MERGED" and pr_head and tip == pr_head.strip().lower():
        method = "-D"
    elif pr_head and tip != pr_head.strip().lower():
        return "kept", "local_commits_not_in_pr", None
    else:
        return "kept", "not_merged", None

    # 8-9: leave the branch before deleting it, but never carry local changes.
    if checked_out_here:
        code, out, _ = git(repo, "status", "--porcelain")
        if code != 0 or out.strip():
            return "kept", "dirty_tree", None
        if (git(repo, "checkout", "-q", default)[0] != 0
                or git(repo, "symbolic-ref", "-q", "HEAD")[1].strip() != "refs/heads/" + default):
            return "kept", "switch_failed", None
        if git(repo, "pull", "-q", "--ff-only", "--no-rebase",
               timeout=NETWORK_TIMEOUT)[0] != 0:
            return "kept", "switch_failed", None

    # 10: the delete itself; git's refusal is reported, never overridden.
    code, out, err = git(repo, "branch", method, "--", branch)
    if code != 0:
        return "kept", "delete_failed:" + first_line(err or out), method
    return "deleted", "merged" if method == "-d" else "pr_merged", method


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="ship-branch-cleanup.py",
        description="Delete the local branch /ship landed, only when no commit is lost.",
        epilog=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    sub = parser.add_subparsers(dest="command")
    sub.required = True
    delete = sub.add_parser("delete", help="delete a landed local branch",
                            description="Run checks 1-10 and print one %s line." % SCHEMA)
    delete.add_argument("--branch", required=True, help="the local branch the PR came from")
    delete.add_argument("--default", required=True, help="the branch the PR merged into")
    delete.add_argument("--pr-state", help="PR state from the caller's gh pr view (MERGED)")
    delete.add_argument("--pr-head", help="PR headRefOid from the caller's gh pr view")
    delete.add_argument("--repo", default=".", help="the checkout to clean up (default .)")
    return parser


def main(argv: Optional[List[str]] = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)
    try:
        for name, value in (("--branch", args.branch), ("--default", args.default)):
            if not value or value.startswith("-"):
                raise UsageError("%s must be a branch name, got %r" % (name, value))
        code, out, err = git(args.repo, "rev-parse", "--show-toplevel")
        if code != 0:
            raise UsageError("%s is not a git checkout: %s" % (args.repo, first_line(err)))
        status, reason, method = decide(args.repo, out.strip(), args.branch, args.default,
                                        args.pr_state, args.pr_head)
    except UsageError as exc:
        parser.print_usage(sys.stderr)
        print("ship-branch-cleanup.py: error: %s" % exc, file=sys.stderr)
        return 2
    print(json.dumps({"schema": SCHEMA, "status": status, "reason": reason, "method": method,
                      "branch": args.branch, "default": args.default}))
    return 0


if __name__ == "__main__":
    sys.exit(main())
