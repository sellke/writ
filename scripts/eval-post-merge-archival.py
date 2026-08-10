#!/usr/bin/env python3
"""Smoke-level fixture scenarios for `/release` Step 1.3c's post-merge
archival hook (Story 4, Task 4.1).

This is deliberately narrow: Story 3's full scenario matrix (11 cases —
happy path, `archived_unlogged`, none/ambiguous skips, every non-archiving
`archive-one` status, and exceptions at either CLI boundary) already lives in
`scripts/tests/test_release_archival_hook.py` and is not re-derived here.

This script's only job is to confirm the shared `run_archival_hook()` model
in `scripts/_archival_hook_model.py` still executes end-to-end under
`eval.sh`'s scenario-TSV harness (the same PASS/FAIL contract every other
`eval-*.py` fixture script emits) — one happy-path archive, one skip case.
The check function's real payload is the `require_literal`/`forbid_literal`
prose-pinning of `commands/release.md`'s Step 1.3c, which lives directly in
`scripts/eval.sh`'s `check_post_merge_archival()`, not in this file.
"""

from __future__ import annotations

import importlib.util
import sys
import tempfile
from pathlib import Path

_MODEL_PATH = Path(__file__).with_name("_archival_hook_model.py")
_SPEC = importlib.util.spec_from_file_location("archival_hook_model", _MODEL_PATH)
assert _SPEC is not None and _SPEC.loader is not None
_archival_hook_model = importlib.util.module_from_spec(_SPEC)
sys.modules["archival_hook_model"] = _archival_hook_model
_SPEC.loader.exec_module(_archival_hook_model)

run_archival_hook = _archival_hook_model.run_archival_hook
init_repo = _archival_hook_model.init_repo
make_spec = _archival_hook_model.make_spec
commit_all = _archival_hook_model.commit_all
empty_knowledge_dir = _archival_hook_model.empty_knowledge_dir

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


def scenario_happy_path_archive() -> None:
    with tempfile.TemporaryDirectory() as tmp:
        root = Path(tmp)
        repo = init_repo(root)
        specs_dir = make_spec(repo, "2026-02-02-smoke-happy-path", "> **Status:** Complete")
        commit_all(repo)

        result = run_archival_hook(
            branch="feature/smoke-happy-path",
            commits=None,
            specs_dir=specs_dir,
            knowledge_dir=empty_knowledge_dir(repo),
            repo_root=repo,
            pr_number=42,
        )
        emit(
            "shared-model-happy-path-archives-with-pr-annotation",
            result.get("archived") is True
            and result.get("status") == "archived"
            and "via PR #42" in (result.get("ledger_line") or ""),
            result,
        )


def scenario_skip_on_no_match() -> None:
    with tempfile.TemporaryDirectory() as tmp:
        root = Path(tmp)
        repo = init_repo(root)
        specs_dir = make_spec(repo, "2026-02-03-smoke-skip-case", "> **Status:** Complete")
        commit_all(repo)

        result = run_archival_hook(
            branch="totally-unrelated-smoke-branch",
            commits="chore: bump deps",
            specs_dir=specs_dir,
            knowledge_dir=empty_knowledge_dir(repo),
            repo_root=repo,
            pr_number=43,
        )
        emit(
            "shared-model-skips-with-no-side-effect-on-no-match",
            result.get("archived") is False
            and result.get("reason") == "none"
            and (specs_dir / "2026-02-03-smoke-skip-case").exists(),
            result,
        )


def main() -> int:
    scenario_happy_path_archive()
    scenario_skip_on_no_match()
    return 0 if failed == 0 else 1


if __name__ == "__main__":
    sys.exit(main())
