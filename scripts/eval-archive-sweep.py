#!/usr/bin/env python3
"""Fixture scenarios for the status-alone archive sweep contract (Story 2,
amended 2026-08-04).

Emits PASS/FAIL TSV lines consumed by scripts/eval.sh check_archive_sweep.
Complements scripts/tests/test_archive_sweep.py's pytest coverage with the
CLI-boundary contract: JSON shape, subcommand behavior, and the collision /
git-mv-failure "skip one, continue the rest" guarantee at the process level.
"""

from __future__ import annotations

import json
import subprocess
import sys
import tempfile
from pathlib import Path

HELPER = Path(__file__).with_name("archive-sweep.py")
passed = 0
failed = 0


def emit(name: str, ok: bool, detail: object = "") -> None:
    global passed, failed
    if ok:
        passed += 1
        print(f"PASS\t{name}")
    else:
        failed += 1
        safe = str(detail).replace("\n", "\\n").replace("\t", " ")
        print(f"FAIL\t{name}\t{safe}")


def run_git(repo: Path, *args: str) -> subprocess.CompletedProcess:
    return subprocess.run(["git", *args], cwd=repo, capture_output=True, text=True)


def init_repo(root: Path) -> Path:
    repo = root / "repo"
    repo.mkdir()
    run_git(repo, "init", "-q")
    run_git(repo, "config", "user.email", "test@example.com")
    run_git(repo, "config", "user.name", "Test")
    return repo


def make_spec(repo: Path, spec_id: str, header: str) -> Path:
    specs_dir = repo / ".writ" / "specs"
    folder = specs_dir / spec_id
    folder.mkdir(parents=True, exist_ok=True)
    (folder / "spec.md").write_text(f"# Spec: {spec_id}\n\n{header}\n", encoding="utf-8")
    return specs_dir


def make_knowledge(repo: Path, category: str, name: str, related: list[str]) -> Path:
    knowledge_dir = repo / ".writ" / "knowledge"
    cat_dir = knowledge_dir / category
    cat_dir.mkdir(parents=True, exist_ok=True)
    items = "\n".join(f"  - {r}" for r in related)
    (cat_dir / name).write_text(f"---\nrelated_artifacts:\n{items}\n---\n", encoding="utf-8")
    return knowledge_dir


def commit_all(repo: Path) -> None:
    run_git(repo, "add", "-A")
    run_git(repo, "commit", "-q", "-m", "fixture commit")


def run_cli(*args: str) -> tuple[int, dict]:
    proc = subprocess.run(
        [sys.executable, str(HELPER), *args],
        capture_output=True,
        text=True,
    )
    try:
        payload = json.loads(proc.stdout or "{}")
    except json.JSONDecodeError:
        payload = {"_raw": proc.stdout, "_err": proc.stderr}
    return proc.returncode, payload


def scenario_scan_cli() -> None:
    with tempfile.TemporaryDirectory() as tmp:
        root = Path(tmp)
        repo = init_repo(root)
        specs_dir = make_spec(repo, "2026-01-01-eligible", "> **Status:** Complete")
        knowledge_dir = make_knowledge(repo, "lessons", "cites.md", ["2026-01-01-eligible"])
        commit_all(repo)

        code, payload = run_cli("scan", "--specs-dir", str(specs_dir), "--knowledge-dir", str(knowledge_dir))
        emit("scan-cli-reports-eligible-count",
             code == 0 and payload.get("eligible_count") == 1, payload)


def scenario_sweep_cli_happy_path() -> None:
    with tempfile.TemporaryDirectory() as tmp:
        root = Path(tmp)
        repo = init_repo(root)
        specs_dir = make_spec(repo, "2026-01-01-eligible", "> **Status:** Complete")
        knowledge_dir = make_knowledge(repo, "decisions", "cites.md", ["2026-01-01-eligible"])
        commit_all(repo)

        code, payload = run_cli(
            "sweep", "--specs-dir", str(specs_dir), "--knowledge-dir", str(knowledge_dir),
            "--repo-root", str(repo),
        )
        emit("sweep-cli-archives-and-writes-ledger",
             code == 0 and len(payload.get("archived", [])) == 1
             and (specs_dir / "archive" / "LEDGER.md").exists(), payload)

        # Second run: idempotent no-op at the CLI boundary too.
        code2, payload2 = run_cli(
            "sweep", "--specs-dir", str(specs_dir), "--knowledge-dir", str(knowledge_dir),
            "--repo-root", str(repo),
        )
        emit("sweep-cli-second-run-is-idempotent",
             code2 == 0 and payload2.get("archived") == [], payload2)


def scenario_complete_without_evidence_still_archives() -> None:
    """Amendment 2026-08-04: knowledge evidence is enrichment, not a gate —
    a Complete spec with zero citing knowledge entries must still archive."""
    with tempfile.TemporaryDirectory() as tmp:
        root = Path(tmp)
        repo = init_repo(root)
        specs_dir = make_spec(repo, "2026-01-01-lonely-complete", "> **Status:** Complete")
        knowledge_dir = repo / ".writ" / "knowledge"
        commit_all(repo)

        code, payload = run_cli(
            "sweep", "--specs-dir", str(specs_dir), "--knowledge-dir", str(knowledge_dir),
            "--repo-root", str(repo),
        )
        emit("sweep-cli-complete-without-evidence-still-archives",
             code == 0 and len(payload.get("archived", [])) == 1
             and payload["archived"][0]["evidence"] == [],
             payload)


def scenario_collision_and_failure_skip_and_continue() -> None:
    with tempfile.TemporaryDirectory() as tmp:
        root = Path(tmp)
        repo = init_repo(root)
        specs_dir = make_spec(repo, "2026-01-01-collides", "> **Status:** Complete")
        make_spec(repo, "2026-01-02-clean", "> **Status:** Complete")
        knowledge_dir = make_knowledge(
            repo, "glossary", "cites.md", ["2026-01-01-collides", "2026-01-02-clean"]
        )
        collision_dest = specs_dir / "archive" / "2026-01-01-collides"
        collision_dest.mkdir(parents=True)
        (collision_dest / "spec.md").write_text("# collision\n", encoding="utf-8")
        commit_all(repo)

        code, payload = run_cli(
            "sweep", "--specs-dir", str(specs_dir), "--knowledge-dir", str(knowledge_dir),
            "--repo-root", str(repo),
        )
        emit("sweep-cli-collision-skips-one-continues-rest",
             code == 0 and payload.get("collisions") == ["2026-01-01-collides"]
             and any(a["spec"] == "2026-01-02-clean" for a in payload.get("archived", [])),
             payload)


def scenario_archive_one_cli_happy_path_with_pr_annotation() -> None:
    with tempfile.TemporaryDirectory() as tmp:
        root = Path(tmp)
        repo = init_repo(root)
        specs_dir = make_spec(repo, "2026-01-01-eligible", "> **Status:** Complete")
        knowledge_dir = repo / ".writ" / "knowledge"
        commit_all(repo)

        code, payload = run_cli(
            "archive-one", "--specs-dir", str(specs_dir), "--knowledge-dir", str(knowledge_dir),
            "--repo-root", str(repo), "--spec-name", "2026-01-01-eligible", "--pr-number", "32",
        )
        emit("archive-one-cli-archives-with-pr-annotation",
             code == 0 and payload.get("status") == "archived"
             and "via PR #32" in (payload.get("ledger_line") or ""), payload)

        # Second run: idempotent no-op at the CLI boundary too.
        code2, payload2 = run_cli(
            "archive-one", "--specs-dir", str(specs_dir), "--knowledge-dir", str(knowledge_dir),
            "--repo-root", str(repo), "--spec-name", "2026-01-01-eligible",
        )
        emit("archive-one-cli-second-run-is-idempotent",
             code2 == 0 and payload2.get("status") == "already_archived", payload2)


def scenario_archive_one_cli_not_eligible_and_collision() -> None:
    with tempfile.TemporaryDirectory() as tmp:
        root = Path(tmp)
        repo = init_repo(root)
        specs_dir = make_spec(repo, "2026-01-01-in-progress", "> **Status:** In Progress")
        knowledge_dir = repo / ".writ" / "knowledge"
        collision_dest = specs_dir / "archive" / "2026-01-02-collides"
        make_spec(repo, "2026-01-02-collides", "> **Status:** Complete")
        collision_dest.mkdir(parents=True)
        (collision_dest / "spec.md").write_text("# already here\n", encoding="utf-8")
        commit_all(repo)

        code, payload = run_cli(
            "archive-one", "--specs-dir", str(specs_dir), "--knowledge-dir", str(knowledge_dir),
            "--repo-root", str(repo), "--spec-name", "2026-01-01-in-progress",
        )
        emit("archive-one-cli-not-yet-complete-is-not-eligible",
             code == 0 and payload.get("status") == "not_eligible", payload)

        code2, payload2 = run_cli(
            "archive-one", "--specs-dir", str(specs_dir), "--knowledge-dir", str(knowledge_dir),
            "--repo-root", str(repo), "--spec-name", "2026-01-02-collides",
        )
        emit("archive-one-cli-collision-hard-stops",
             code2 == 0 and payload2.get("status") == "collision", payload2)


def main() -> int:
    scenario_scan_cli()
    scenario_sweep_cli_happy_path()
    scenario_complete_without_evidence_still_archives()
    scenario_collision_and_failure_skip_and_continue()
    scenario_archive_one_cli_happy_path_with_pr_annotation()
    scenario_archive_one_cli_not_eligible_and_collision()
    return 0 if failed == 0 else 1


if __name__ == "__main__":
    sys.exit(main())
