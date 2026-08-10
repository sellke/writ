"""Shared composition model for `/release` Step 1.3c's post-merge archival
hook (Story 3 of `2026-08-04-post-merge-archival-hook`, extracted to a shared
module by Story 4 Task 4.0).

`commands/release.md` is a prose workflow document, not compiled code, so
there is no importable "hook" module to call directly. `run_archival_hook()`
below models Step 1.3c's exact control-flow composition -- resolve via
`scripts/resolve-spec-reference.py resolve`, branch on its `result` field,
and (only when `matched`) invoke `scripts/archive-sweep.py archive-one`,
branching purely on its returned `status` field -- then drives that
composition against real fixture directories via subprocess, exactly the way
Step 1.3c's prose describes the two scripts being chained.

This is the single source of truth for that composition model. Both
`scripts/tests/test_release_archival_hook.py`'s pytest suite (Story 3's
original 11 scenarios) and `scripts/eval-post-merge-archival.py`'s smoke
scenarios (Story 4's `eval.sh`-harness coverage) import from here rather than
each defining their own copy -- do not let a second copy of this logic exist
anywhere.
"""

from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path
from typing import Any

RESOLVER_PATH = Path(__file__).resolve().parent / "resolve-spec-reference.py"
ARCHIVE_SWEEP_PATH = Path(__file__).resolve().parent / "archive-sweep.py"


def run_archival_hook(
    *,
    branch: str | None,
    commits: str | None,
    specs_dir: Path,
    knowledge_dir: Path,
    repo_root: Path,
    pr_number: int | None,
    resolver_path: Path = RESOLVER_PATH,
    archive_sweep_path: Path = ARCHIVE_SWEEP_PATH,
) -> dict[str, Any]:
    """Model of `/release` Step 1.3c's post-merge archival hook.

    Only fires the archive call on the resolver's `matched` result (`none`
    and `ambiguous` are treated identically as "skip" -- Story 1's tri-state
    contract). Branches purely on `archive-one`'s own returned `status`
    field for the archived/not-archived outcome, never re-deriving
    eligibility itself (Task 3.3 -- no duplicated complete-family or
    already-archived check here). The entire chain is wrapped in one
    best-effort guard: any exception -- malformed JSON, a missing script, a
    non-zero exit that still can't be parsed -- degrades to a swallowed
    no-op result rather than propagating (Task 3.4 / AC 5), matching the
    "never blocks a release" guarantee Step 1.3c's prose describes.
    """
    try:
        resolve_proc = subprocess.run(
            [
                sys.executable,
                str(resolver_path),
                "resolve",
                "--branch",
                branch or "",
                "--commits",
                commits or "",
                "--specs-dir",
                str(specs_dir),
            ],
            capture_output=True,
            text=True,
            check=False,
        )
        resolve_result = json.loads(resolve_proc.stdout)

        if resolve_result.get("result") != "matched":
            return {"archived": False, "reason": resolve_result.get("result"), "spec": None}

        spec_name = resolve_result["spec"]

        archive_args = [
            sys.executable,
            str(archive_sweep_path),
            "archive-one",
            "--specs-dir",
            str(specs_dir),
            "--knowledge-dir",
            str(knowledge_dir),
            "--repo-root",
            str(repo_root),
            "--spec-name",
            spec_name,
        ]
        if pr_number is not None:
            archive_args += ["--pr-number", str(pr_number)]

        archive_proc = subprocess.run(archive_args, capture_output=True, text=True, check=False)
        archive_result = json.loads(archive_proc.stdout)
        status = archive_result.get("status")

        if status in ("archived", "archived_unlogged"):
            return {
                "archived": True,
                "spec": spec_name,
                "status": status,
                "ledger_line": archive_result.get("ledger_line"),
            }

        return {"archived": False, "reason": status, "spec": spec_name}
    except Exception as exc:  # best-effort guard -- never propagate (Task 3.4)
        return {"archived": False, "reason": "exception", "error": str(exc), "spec": None}


def _run_git(repo: Path, *args: str) -> subprocess.CompletedProcess:
    return subprocess.run(["git", *args], cwd=repo, capture_output=True, text=True)


def init_repo(root: Path) -> Path:
    repo = root / "repo"
    repo.mkdir()
    _run_git(repo, "init", "-q")
    _run_git(repo, "config", "user.email", "test@example.com")
    _run_git(repo, "config", "user.name", "Test")
    return repo


def make_spec(repo: Path, spec_id: str, header: str) -> Path:
    specs_dir = repo / ".writ" / "specs"
    folder = specs_dir / spec_id
    folder.mkdir(parents=True, exist_ok=True)
    (folder / "spec.md").write_text(f"# Spec: {spec_id}\n\n{header}\n", encoding="utf-8")
    return specs_dir


def commit_all(repo: Path) -> None:
    _run_git(repo, "add", "-A")
    _run_git(repo, "commit", "-q", "-m", "fixture commit")


def empty_knowledge_dir(repo: Path) -> Path:
    return repo / ".writ" / "knowledge"


def fixed_output_script(tmp_path: Path, name: str, stdout: str) -> Path:
    """Writes a throwaway script that unconditionally prints `stdout` and
    exits 0 -- used to stand in for one half of the resolve/archive chain so
    the other half's fixture (real specs_dir state) can drive a specific
    branch without depending on the two real scripts agreeing on a folder
    that may no longer exist (e.g. an already-archived spec is, by
    definition, no longer visible to the real resolver's folder scan)."""
    script = tmp_path / name
    script.write_text(f"import sys\nsys.stdout.write({stdout!r})\nsys.exit(0)\n", encoding="utf-8")
    return script


def fake_matched_resolver(tmp_path: Path, spec_name: str) -> Path:
    payload = json.dumps({"result": "matched", "spec": spec_name, "candidates": []})
    return fixed_output_script(tmp_path, "fake_matched_resolver.py", payload)
