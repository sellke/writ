#!/usr/bin/env python3
"""Fixture scenario for the .cursorindexingignore install-once seed (Story 4).

Runs the real scripts/install.sh against disposable temp workspaces (it
resolves WRIT_SRC to this local checkout automatically — see install.sh's
"Resolve writ source" section) to prove the install-once contract end to end:
- --dry-run preview reports the seed/skip line before any file exists,
  without creating it.
- The first apply creates .cursorindexingignore containing the archive
  exclusion pattern and prints the Seeded message.
- Once the file exists (Writ-created or user-customized), every subsequent
  run — including --force — preserves it unchanged and prints the
  Preserved/skip messages instead of overwriting it.
"""

from __future__ import annotations

import subprocess
import sys
import tempfile
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parent.parent
INSTALL_SH = PROJECT_ROOT / "scripts" / "install.sh"

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


def run_install(cwd: Path, *args: str) -> subprocess.CompletedProcess:
    return subprocess.run(
        ["bash", str(INSTALL_SH), *args],
        cwd=cwd,
        text=True,
        capture_output=True,
    )


def scenario_dry_run_preview_before_first_install() -> None:
    with tempfile.TemporaryDirectory() as tmp:
        target = Path(tmp)
        result = run_install(target, "--platform", "cursor", "--dry-run", "--no-commit")
        emit(
            "dry-run-previews-seed-before-first-install",
            result.returncode == 0
            and "Would seed .cursorindexingignore (first install)." in result.stdout,
            result.stdout + result.stderr,
        )
        emit(
            "dry-run-does-not-create-file",
            not (target / ".cursorindexingignore").exists(),
            "dry-run unexpectedly created .cursorindexingignore",
        )


def scenario_first_apply_seeds_archive_pattern() -> None:
    with tempfile.TemporaryDirectory() as tmp:
        target = Path(tmp)
        result = run_install(target, "--platform", "cursor", "--no-commit")
        dest = target / ".cursorindexingignore"
        emit(
            "first-apply-creates-file",
            result.returncode == 0 and dest.is_file(),
            result.stdout + result.stderr,
        )
        emit(
            "first-apply-prints-seeded-message",
            "✨ Seeded: .cursorindexingignore" in result.stdout,
            result.stdout + result.stderr,
        )
        contents = dest.read_text(encoding="utf-8") if dest.is_file() else ""
        emit(
            "first-apply-contains-archive-pattern",
            ".writ/specs/archive/**" in contents.splitlines(),
            contents,
        )


def scenario_existing_file_survives_reruns_and_force() -> None:
    with tempfile.TemporaryDirectory() as tmp:
        target = Path(tmp)
        dest = target / ".cursorindexingignore"
        custom = "custom-pattern/**\n"
        dest.write_text(custom, encoding="utf-8")

        preview = run_install(target, "--platform", "cursor", "--dry-run", "--no-commit")
        emit(
            "dry-run-previews-skip-when-file-exists",
            preview.returncode == 0
            and "Would skip .cursorindexingignore (already exists; install-once)." in preview.stdout,
            preview.stdout + preview.stderr,
        )

        result = run_install(target, "--platform", "cursor", "--force", "--no-commit")
        emit(
            "force-apply-preserves-existing-file-content",
            result.returncode == 0 and dest.read_text(encoding="utf-8") == custom,
            dest.read_text(encoding="utf-8") if dest.is_file() else "<missing>",
        )
        emit(
            "force-apply-prints-preserved-message",
            "⚡ Preserved: .cursorindexingignore (install-once)" in result.stdout,
            result.stdout + result.stderr,
        )


def main() -> int:
    if not INSTALL_SH.is_file():
        emit("install-sh-present", False, f"missing {INSTALL_SH}")
        return 1
    scenario_dry_run_preview_before_first_install()
    scenario_first_apply_seeds_archive_pattern()
    scenario_existing_file_survives_reruns_and_force()
    return 0 if failed == 0 else 1


if __name__ == "__main__":
    sys.exit(main())
