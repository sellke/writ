#!/usr/bin/env python3
"""Unit tests for scripts/app-verify.py (spec `2026-10-01-behavioral-verification`).

Story 1 covers the recipe grammar and the `validate` subcommand: a valid
recipe exits 0, each defect yields exactly its finding code with exit 1, and
a missing or undecodable recipe exits 2. It also guards the install overlay:
Writ must never ship `.writ/docs/app-verification.md`, because that path
belongs to the project-authored recipe.

Run: python3 scripts/tests/test_app_verify.py
"""

from __future__ import annotations

import importlib.util
import json
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[2]
HELPER_PATH = REPO_ROOT / "scripts" / "app-verify.py"
FIXTURE_DIR = REPO_ROOT / "scripts" / "tests" / "fixtures" / "app-verify"

_spec = importlib.util.spec_from_file_location("app_verify", HELPER_PATH)
assert _spec and _spec.loader
av = importlib.util.module_from_spec(_spec)
sys.modules[_spec.name] = av
_spec.loader.exec_module(av)


VALID_RECIPE = """\
# App Verification Recipe

## Launch
- **Command:** `PORT=8765 python3 app.py`
- **Ready when:** http://127.0.0.1:8765/
- **Ready timeout:** 30s
- **Reuse running instance:** no

## Safety
- **Variable:** DATABASE_URL
- **Allowed:** *dev-branch-host*
- **Never:** *prod*
- **Env file:** .env.local

## Login
- **Method:** checks sign in themselves with the seeded user
- **Credentials from:** E2E_USER_EMAIL, E2E_USER_PASSWORD

## Feature Map
| ID | Feature | Paths | Check |
|---|---|---|---|
| home | Home page renders | `app.py`, `templates/**` | `python3 check_home.py --a-very-long-argument-that-is-definitely-over-32-characters` |
| oauth | Third-party login | `app/auth/**` | human-only: third-party consent screen |

## Evidence
- **Artifacts:** test-results/

## Cleanup
- **After:** none
"""


def run_cli(*args: str) -> subprocess.CompletedProcess:
    return subprocess.run(
        [sys.executable, str(HELPER_PATH), *args],
        capture_output=True, text=True, cwd=str(REPO_ROOT),
    )


class RecipeFixture:
    def __init__(self) -> None:
        self._tmp = tempfile.TemporaryDirectory()
        self.root = Path(self._tmp.name)

    def write(self, text: str, name: str = "recipe.md") -> Path:
        path = self.root / name
        path.write_text(text, encoding="utf-8")
        return path

    def cleanup(self) -> None:
        self._tmp.cleanup()


def _codes(text: str) -> list[str]:
    return sorted({f["code"] for f in av.validate_text(text)})


class ValidateCliTests(unittest.TestCase):
    """AC-1.2, AC-1.3 — the CLI contract."""

    def setUp(self) -> None:
        self.fx = RecipeFixture()

    def tearDown(self) -> None:
        self.fx.cleanup()

    def test_valid_recipe_exits_zero_with_one_summary_line(self) -> None:
        path = self.fx.write(VALID_RECIPE)
        proc = run_cli("validate", "--recipe", str(path))
        self.assertEqual(proc.returncode, 0, proc.stdout + proc.stderr)
        lines = proc.stdout.strip().splitlines()
        self.assertEqual(len(lines), 1)
        self.assertTrue(lines[0].startswith("app-verify: "))

    def test_valid_recipe_json_has_verdict_and_empty_findings(self) -> None:
        path = self.fx.write(VALID_RECIPE)
        proc = run_cli("validate", "--recipe", str(path), "--json")
        self.assertEqual(proc.returncode, 0, proc.stdout + proc.stderr)
        lines = proc.stdout.strip().splitlines()
        self.assertTrue(lines[0].startswith("app-verify: "))
        payload = json.loads(lines[-1])
        self.assertEqual(payload["verdict"], "valid")
        self.assertEqual(payload["findings"], [])

    def test_invalid_recipe_exits_one_with_first_finding(self) -> None:
        path = self.fx.write(VALID_RECIPE.replace("## Cleanup\n- **After:** none\n", ""))
        proc = run_cli("validate", "--recipe", str(path))
        self.assertEqual(proc.returncode, 1)
        self.assertIn("app-verify: recipe invalid — missing_section", proc.stdout)

    def test_missing_recipe_exits_two(self) -> None:
        proc = run_cli("validate", "--recipe", str(self.fx.root / "nope.md"))
        self.assertEqual(proc.returncode, 2)
        self.assertIn("unverifiable (no_recipe)", proc.stdout)

    def test_undecodable_recipe_exits_two(self) -> None:
        path = self.fx.root / "binary.md"
        path.write_bytes(b"\xff\xfe\x00\x81 not utf-8")
        proc = run_cli("validate", "--recipe", str(path))
        self.assertEqual(proc.returncode, 2)
        self.assertIn("unverifiable (recipe_unreadable", proc.stdout)


class FindingCodeTests(unittest.TestCase):
    """AC-1.3 — one defect, exactly its finding code."""

    def test_valid_recipe_has_no_findings(self) -> None:
        self.assertEqual(av.validate_text(VALID_RECIPE), [])

    def test_missing_section(self) -> None:
        text = VALID_RECIPE.replace("## Login\n", "## Signin\n")
        self.assertEqual(_codes(text), ["missing_section"])

    def test_missing_launch_command(self) -> None:
        text = VALID_RECIPE.replace("- **Command:** `PORT=8765 python3 app.py`\n", "")
        self.assertEqual(_codes(text), ["missing_launch_command"])

    def test_missing_ready(self) -> None:
        text = VALID_RECIPE.replace("- **Ready when:** http://127.0.0.1:8765/\n", "")
        self.assertEqual(_codes(text), ["missing_ready"])

    def test_bad_ready_target_is_missing_ready(self) -> None:
        text = VALID_RECIPE.replace("http://127.0.0.1:8765/", "whenever it feels ready")
        self.assertEqual(_codes(text), ["missing_ready"])

    def test_port_ready_target_is_valid(self) -> None:
        text = VALID_RECIPE.replace("http://127.0.0.1:8765/", "port 8765")
        self.assertEqual(_codes(text), [])

    def test_missing_safety(self) -> None:
        text = VALID_RECIPE.replace(
            "- **Variable:** DATABASE_URL\n- **Allowed:** *dev-branch-host*\n"
            "- **Never:** *prod*\n- **Env file:** .env.local\n", "")
        self.assertEqual(_codes(text), ["missing_safety"])

    def test_safety_none_without_reason_is_missing_safety(self) -> None:
        text = VALID_RECIPE.replace(
            "- **Variable:** DATABASE_URL\n- **Allowed:** *dev-branch-host*\n"
            "- **Never:** *prod*\n- **Env file:** .env.local\n",
            "- **Safety:** none\n")
        self.assertEqual(_codes(text), ["missing_safety"])

    def test_safety_none_with_reason_is_valid(self) -> None:
        text = VALID_RECIPE.replace(
            "- **Variable:** DATABASE_URL\n- **Allowed:** *dev-branch-host*\n"
            "- **Never:** *prod*\n- **Env file:** .env.local\n",
            "- **Safety:** none — fixture app holds no state\n")
        self.assertEqual(_codes(text), [])

    def test_variable_without_allowed_is_missing_safety(self) -> None:
        text = VALID_RECIPE.replace("- **Allowed:** *dev-branch-host*\n", "")
        self.assertEqual(_codes(text), ["missing_safety"])

    def test_bad_feature_row_wrong_cell_count(self) -> None:
        text = VALID_RECIPE.replace(
            "| oauth | Third-party login | `app/auth/**` | human-only: third-party consent screen |",
            "| oauth | Third-party login | human-only: third-party consent screen |")
        self.assertEqual(_codes(text), ["bad_feature_row"])

    def test_bad_feature_row_check_neither_command_nor_human_only(self) -> None:
        text = VALID_RECIPE.replace(
            "human-only: third-party consent screen", "someone should look at it")
        self.assertEqual(_codes(text), ["bad_feature_row"])

    def test_bad_feature_row_human_only_without_reason(self) -> None:
        text = VALID_RECIPE.replace(
            "human-only: third-party consent screen", "human-only:")
        self.assertEqual(_codes(text), ["bad_feature_row"])

    def test_bad_feature_row_check_without_paths(self) -> None:
        text = VALID_RECIPE.replace("| `app.py`, `templates/**` |", "|  |")
        self.assertEqual(_codes(text), ["bad_feature_row"])

    def test_duplicate_feature_id(self) -> None:
        text = VALID_RECIPE.replace("| oauth |", "| home |")
        self.assertEqual(_codes(text), ["duplicate_feature_id"])

    def test_bad_feature_id(self) -> None:
        text = VALID_RECIPE.replace("| oauth |", "| OAuth_Login |")
        self.assertEqual(_codes(text), ["bad_feature_id"])

    def test_secret_value_url_credentials(self) -> None:
        text = VALID_RECIPE.replace(
            "- **Allowed:** *dev-branch-host*",
            "- **Allowed:** postgres://admin:hunter2@dev-branch-host/db")
        self.assertEqual(_codes(text), ["secret_value"])

    def test_secret_value_url_credentials_inside_backticks(self) -> None:
        text = VALID_RECIPE.replace(
            "`PORT=8765 python3 app.py`",
            "`DATABASE_URL=postgres://admin:hunter2@localhost/db python3 app.py`")
        self.assertEqual(_codes(text), ["secret_value"])

    def test_secret_value_long_token(self) -> None:
        text = VALID_RECIPE.replace(
            "- **Method:** checks sign in themselves with the seeded user",
            "- **Method:** token fake_token_0a1b2c3d4e5f6a7b8c9d0e1f2a3b")
        self.assertEqual(_codes(text), ["secret_value"])

    def test_secret_value_password_only_url(self) -> None:
        text = VALID_RECIPE.replace(
            "- **Allowed:** *dev-branch-host*", "- **Allowed:** redis://:hunter2@dev-host")
        self.assertEqual(_codes(text), ["secret_value"])

    def test_long_env_variable_name_is_not_secret(self) -> None:
        text = VALID_RECIPE.replace(
            "E2E_USER_EMAIL, E2E_USER_PASSWORD",
            "E2E_USER_EMAIL, NEXT_PUBLIC_FIREBASE_MESSAGING_SENDER_ID")
        self.assertEqual(_codes(text), [])

    def test_backticked_long_command_is_not_secret(self) -> None:
        self.assertNotIn("secret_value", _codes(VALID_RECIPE))

    def test_long_unbackticked_path_is_not_secret(self) -> None:
        text = VALID_RECIPE.replace(
            "| `app.py`, `templates/**` |",
            "| scripts/tests/fixtures/app-verify/app.py |")
        self.assertEqual(_codes(text), [])

    def test_bad_timeout(self) -> None:
        text = VALID_RECIPE.replace("- **Ready timeout:** 30s", "- **Ready timeout:** soon")
        self.assertEqual(_codes(text), ["bad_timeout"])

    def test_bare_seconds_timeout_is_valid(self) -> None:
        text = VALID_RECIPE.replace("- **Ready timeout:** 30s", "- **Ready timeout:** 45")
        self.assertEqual(_codes(text), [])

    def test_pipe_inside_backticked_check_is_one_cell(self) -> None:
        text = VALID_RECIPE.replace(
            "`python3 check_home.py --a-very-long-argument-that-is-definitely-over-32-characters`",
            "`curl -s localhost:8765 | grep Home`")
        self.assertEqual(_codes(text), [])


class ParserTests(unittest.TestCase):
    """The parser is shared by `touched` and `run` (Story 3)."""

    def test_parse_extracts_launch_safety_and_features(self) -> None:
        recipe = av.parse_recipe(VALID_RECIPE)
        self.assertEqual(recipe.launch_command, "PORT=8765 python3 app.py")
        self.assertEqual(recipe.ready_when, "http://127.0.0.1:8765/")
        self.assertEqual(recipe.ready_timeout_s, 30)
        self.assertFalse(recipe.reuse_running)
        self.assertEqual(recipe.env_file, ".env.local")
        self.assertEqual(len(recipe.variables), 1)
        self.assertEqual(recipe.variables[0].name, "DATABASE_URL")
        self.assertEqual(recipe.variables[0].allowed, ["*dev-branch-host*"])
        self.assertEqual(recipe.variables[0].never, ["*prod*"])
        ids = [f.id for f in recipe.features]
        self.assertEqual(ids, ["home", "oauth"])
        home = recipe.features[0]
        self.assertEqual(home.paths, ["app.py", "templates/**"])
        self.assertTrue(home.check.startswith("python3 check_home.py"))
        self.assertIsNone(home.human_only)
        self.assertEqual(recipe.features[1].human_only, "third-party consent screen")
        self.assertEqual(recipe.artifacts, ["test-results/"])
        self.assertIsNone(recipe.after)


class InstallOverlayGuardTests(unittest.TestCase):
    """AC-1.4 — Writ never ships the project-authored recipe path."""

    def test_repo_has_no_project_recipe(self) -> None:
        self.assertFalse(
            (REPO_ROOT / ".writ" / "docs" / "app-verification.md").exists(),
            ".writ/docs/app-verification.md is project-authored; install's overlay "
            "of .writ/docs/*.md would collide with it",
        )

    def test_format_doc_worked_example_validates(self) -> None:
        doc = (REPO_ROOT / ".writ" / "docs" / "app-verification-format.md").read_text(
            encoding="utf-8")
        start = doc.index("```markdown\n# App Verification Recipe")
        body = doc[start + len("```markdown\n"):]
        example = body[:body.index("\n```")] + "\n"
        self.assertEqual(av.validate_text(example), [])


if __name__ == "__main__":
    unittest.main()
