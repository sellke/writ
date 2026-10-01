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
        """AC-1.1 — the format doc's worked example is a valid recipe."""
        doc = (REPO_ROOT / ".writ" / "docs" / "app-verification-format.md").read_text(
            encoding="utf-8")
        start = doc.index("```markdown\n# App Verification Recipe")
        body = doc[start + len("```markdown\n"):]
        example = body[:body.index("\n```")] + "\n"
        self.assertEqual(av.validate_text(example), [])


class ProductAmendmentTests(unittest.TestCase):
    """AC-1.5 — ADR-028, roadmap, and mission describe the recipe design."""

    def read(self, rel: str) -> str:
        return (REPO_ROOT / rel).read_text(encoding="utf-8")

    def phase_12(self, text: str) -> str:
        start = text.index("Phase 12")
        return text[start:start + 4000]

    def test_adr_028_names_the_recipe_and_runtime_boundary(self) -> None:
        adr = self.read(".writ/decision-records/"
                        "adr-028-behavioral-verification-and-cross-family-panels.md")
        self.assertIn("`.writ/docs/app-verification.md`", adr)
        self.assertIn("`/create-uat-plan` drafts", adr)
        self.assertIn("Features 1 and 2 merged", adr)
        self.assertIn("**Runtime boundary.**", adr)
        self.assertIn("is not a Writ runtime", adr)
        for line in adr.splitlines():
            if "verify-<app>" in line:
                self.assertIn("Superseded", line)

    def test_roadmap_phase_12_merged_with_fixture_criterion(self) -> None:
        roadmap = self.read(".writ/product/roadmap.md")
        section = roadmap[roadmap.index("## Phase 12: Behavioral Verification"):]
        section = section[:section.index("\n## ", 5)]
        self.assertIn("**Behavioral verification**", section)
        self.assertIn("A fixture app's UAT scenarios pass end to end", section)
        self.assertNotIn("**Project verification skill**", section)
        self.assertNotIn("`/initialize` generates", section)
        self.assertNotIn("Feature 2 depends on Feature 1", section)

    def test_mission_phase_12_lines_match(self) -> None:
        for rel in (".writ/product/mission.md", ".writ/product/mission-lite.md"):
            text = self.read(rel)
            self.assertNotIn("verify-<app>", text, rel)
            self.assertIn("/create-uat-plan", self.phase_12(text[text.index("Phase 12 —"):]), rel)


# --- Story 3: touched and run ----------------------------------------------
#
# Spec `2026-10-01-behavioral-verification`, Story 3 (AC-3.1 .. AC-3.5). Every
# launched run picks a free port and rewrites the fixture recipe's 8765, so
# runs never collide or trip `instance_already_running` by accident. After
# every launched run, the fixture's own PID must be gone.

import os
import socket
import threading
import time
from http.server import BaseHTTPRequestHandler, HTTPServer
from unittest import mock

APP = FIXTURE_DIR / "app.py"


def free_port() -> int:
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as sock:
        sock.bind(("127.0.0.1", 0))
        return sock.getsockname()[1]


def pid_gone(pid: int, wait_s: float = 5.0) -> bool:
    deadline = time.monotonic() + wait_s
    while time.monotonic() < deadline:
        try:
            os.kill(pid, 0)
        except ProcessLookupError:
            return True
        except PermissionError:
            return False
        time.sleep(0.05)
    return False


class RunFixture:
    """A temp spec folder, a port-rewritten recipe, and a PID file."""

    def __init__(self, variant: str | None = None, text: str | None = None) -> None:
        self._tmp = tempfile.TemporaryDirectory()
        self.root = Path(self._tmp.name)
        self.spec = self.root / "spec"
        self.spec.mkdir()
        self.port = free_port()
        self.pidfile = self.root / "fixture.pid"
        source = text if text is not None else (FIXTURE_DIR / variant).read_text(encoding="utf-8")
        self.recipe = self.root / "recipe.md"
        self.recipe.write_text(source.replace("8765", str(self.port)), encoding="utf-8")
        self.env = dict(os.environ)
        self.env["APP_VERIFY_FIXTURE_PIDFILE"] = str(self.pidfile)
        self.env.pop("APP_VERIFY_FIXTURE_DB", None)

    def run(self, label: str = "story-3", **kwargs):
        kwargs.setdefault("env", self.env)
        kwargs.setdefault("cwd", REPO_ROOT)
        return av.run_verification(self.recipe, self.spec, label, **kwargs)

    def pids(self) -> list[int]:
        if not self.pidfile.exists():
            return []
        return [int(x) for x in self.pidfile.read_text().split()]

    def cleanup(self) -> None:
        self._tmp.cleanup()


def custom_recipe(launch: str, checks: list[tuple[str, str]], *, artifacts: str = "none",
                  after: str = "none", timeout: str = "30s", ready: str = "http://127.0.0.1:8765/",
                  reuse: str = "no") -> str:
    rows = "\n".join(f"| {fid} | Feature {fid} | `src/{fid}/**` | `{cmd}` |" for fid, cmd in checks)
    return f"""\
# App Verification Recipe

## Launch
- **Command:** `{launch}`
- **Ready when:** {ready}
- **Ready timeout:** {timeout}
- **Reuse running instance:** {reuse}

## Safety
- **Safety:** none — test recipe

## Login
- **Method:** none

## Feature Map
| ID | Feature | Paths | Check |
|---|---|---|---|
{rows}

## Evidence
- **Artifacts:** {artifacts}

## Cleanup
- **After:** {after}
"""


FIXTURE_LAUNCH = f"PORT=8765 {sys.executable} {APP}"


class TouchedTests(unittest.TestCase):
    """AC-3.1 — changed files map to feature IDs by Paths globs."""

    def setUp(self) -> None:
        self.fx = RecipeFixture()
        self.recipe = self.fx.write(VALID_RECIPE.replace(
            "| oauth | Third-party login | `app/auth/**` |",
            "| oauth | Third-party login | `app/auth/**` |").replace(
            "## Evidence",
            "| events | Events | `src/events/**`, `src/lib/events.ts` | `npm test -- events` |\n\n"
            "## Evidence"))

    def tearDown(self) -> None:
        self.fx.cleanup()

    def test_match_prints_ids_in_feature_map_order(self) -> None:
        proc = run_cli("touched", "--recipe", str(self.recipe), "--changed",
                       "src/lib/events.ts", "app.py")
        self.assertEqual(proc.returncode, 0, proc.stderr)
        self.assertEqual(proc.stdout.split(), ["home", "events"])

    def test_multiple_globs_and_dot_slash(self) -> None:
        proc = run_cli("touched", "--recipe", str(self.recipe), "--changed",
                       "./templates/a/b.html")
        self.assertEqual(proc.stdout.split(), ["home"])

    def test_human_only_rows_never_print(self) -> None:
        proc = run_cli("touched", "--recipe", str(self.recipe), "--changed", "app/auth/login.py")
        self.assertEqual(proc.returncode, 0)
        self.assertIn("app-verify: no mapped features touched by this story", proc.stdout)
        self.assertNotIn("oauth", proc.stdout)

    def test_no_match(self) -> None:
        proc = run_cli("touched", "--recipe", str(self.recipe), "--changed", "README.md")
        self.assertEqual(proc.returncode, 0)
        self.assertEqual(proc.stdout.strip(),
                         "app-verify: no mapped features touched by this story")

    def test_no_recipe(self) -> None:
        proc = run_cli("touched", "--recipe", str(self.fx.root / "nope.md"), "--changed", "a")
        self.assertEqual(proc.returncode, 2)
        self.assertIn("unverifiable (no_recipe)", proc.stdout)

    def test_invalid_recipe(self) -> None:
        bad = self.fx.write(VALID_RECIPE.replace("## Login\n", ""), "bad.md")
        proc = run_cli("touched", "--recipe", str(bad), "--changed", "a")
        self.assertEqual(proc.returncode, 2)
        self.assertIn("unverifiable (recipe_invalid: missing_section", proc.stdout)

    def test_json_lists_ids(self) -> None:
        proc = run_cli("touched", "--recipe", str(self.recipe), "--changed", "app.py", "--json")
        self.assertEqual(json.loads(proc.stdout.strip().splitlines()[-1])["features"], ["home"])


class SafetyTests(unittest.TestCase):
    """AC-3.2 — refuse by default; nothing launches on refusal."""

    def make(self, safety: str, env_file_text: str | None = None) -> RunFixture:
        text = custom_recipe(FIXTURE_LAUNCH, [("home", "true")]).replace(
            "- **Safety:** none — test recipe", safety)
        fx = RunFixture(text=text)
        self.addCleanup(fx.cleanup)
        if env_file_text is not None:
            (fx.root / "target.env").write_text(env_file_text, encoding="utf-8")
        return fx

    SAFETY = ("- **Variable:** APP_DB\n- **Allowed:** *dev-host*\n- **Never:** *prod*\n"
              "- **Env file:** {env}")

    def assert_refused(self, fx: RunFixture, fragment: str) -> None:
        code, summary, payload = fx.run()
        self.assertEqual(code, 2, summary)
        self.assertTrue(summary.startswith("app-verify: refused ("), summary)
        self.assertIn(fragment, summary)
        self.assertEqual(payload["verdict"], "refused")
        self.assertFalse((fx.spec / "evidence" / "story-3" / "_launch").exists())
        self.assertEqual(fx.pids(), [])

    def test_env_value_not_matching_allowed_refuses(self) -> None:
        fx = self.make(self.SAFETY.format(env="missing.env"))
        fx.env["APP_DB"] = "postgres://other-host/db"
        self.assert_refused(fx, "APP_DB does not match an allowed target")

    def test_never_match_refuses(self) -> None:
        fx = self.make(self.SAFETY.format(env="missing.env"))
        fx.env["APP_DB"] = "dev-host-prod"
        self.assert_refused(fx, "APP_DB matches a Never pattern")

    def test_unset_and_missing_env_file_refuses(self) -> None:
        fx = self.make(self.SAFETY.format(env="missing.env"))
        fx.env.pop("APP_DB", None)
        self.assert_refused(fx, "APP_DB unset")

    def test_env_file_value_refuses_without_echoing_it(self) -> None:
        fx = self.make(self.SAFETY.format(env="{root}/target.env"), "# c\nAPP_DB=secret-prod\n")
        fx.recipe.write_text(fx.recipe.read_text().replace("{root}", str(fx.root)))
        fx.env.pop("APP_DB", None)
        code, summary, payload = fx.run()
        self.assertEqual(code, 2)
        self.assertNotIn("secret-prod", summary + json.dumps(payload))

    def test_env_file_value_allows(self) -> None:
        fx = self.make(self.SAFETY.format(env="{root}/target.env"), "export APP_DB='my-dev-host'\n")
        fx.recipe.write_text(fx.recipe.read_text().replace("{root}", str(fx.root)))
        fx.env.pop("APP_DB", None)
        code, summary, _ = fx.run()
        self.assertEqual(code, 0, summary)
        for pid in fx.pids():
            self.assertTrue(pid_gone(pid))

    def test_fixture_safety_refused_recipe(self) -> None:
        fx = RunFixture("recipe-safety-refused.md")
        self.addCleanup(fx.cleanup)
        self.assert_refused(fx, "APP_VERIFY_FIXTURE_DB matches a Never pattern")

    def test_unsupported_platform(self) -> None:
        fx = RunFixture("recipe-pass.md")
        self.addCleanup(fx.cleanup)
        with mock.patch.object(av, "_is_posix", return_value=False):
            code, summary, _ = fx.run()
        self.assertEqual(code, 2)
        self.assertEqual(summary, "app-verify: unverifiable (unsupported_platform)")


class _OkHandler(BaseHTTPRequestHandler):
    def do_GET(self) -> None:  # noqa: N802
        body = b"app-verify fixture: home\n"
        self.send_response(200)
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)

    def log_message(self, *args: object) -> None:
        pass


class PreLaunchProbeTests(unittest.TestCase):
    """AC-3.2 — an instance already answering is refused unless reuse is yes."""

    def setUp(self) -> None:
        self.fx = RunFixture("recipe-pass.md")
        self.server = HTTPServer(("127.0.0.1", self.fx.port), _OkHandler)
        self.thread = threading.Thread(target=self.server.serve_forever, daemon=True)
        self.thread.start()

    def tearDown(self) -> None:
        self.server.shutdown()
        self.server.server_close()
        self.fx.cleanup()

    def test_running_instance_refused(self) -> None:
        code, summary, _ = self.fx.run()
        self.assertEqual(code, 2)
        self.assertEqual(summary, "app-verify: refused (instance_already_running)")
        self.assertEqual(self.fx.pids(), [])

    def test_running_instance_reused_when_allowed(self) -> None:
        self.fx.recipe.write_text(self.fx.recipe.read_text().replace(
            "- **Reuse running instance:** no", "- **Reuse running instance:** yes"))
        code, summary, payload = self.fx.run()
        self.assertEqual(code, 0, summary)
        self.assertFalse(payload["launched"])
        self.assertEqual(self.fx.pids(), [])


class RunTests(unittest.TestCase):
    """AC-3.3, AC-3.4, AC-3.5 — launch, checks, evidence, cleanup."""

    def make(self, variant: str | None = None, text: str | None = None) -> RunFixture:
        fx = RunFixture(variant, text)
        self.addCleanup(fx.cleanup)
        return fx

    def assert_no_fixture_survives(self, fx: RunFixture) -> None:
        for pid in fx.pids():
            self.assertTrue(pid_gone(pid), f"fixture pid {pid} survived")

    def test_pass_writes_full_result_and_launch_logs(self) -> None:
        fx = self.make("recipe-pass.md")
        code, summary, payload = fx.run()
        self.assertEqual(code, 0, summary)
        self.assertEqual(summary, "app-verify: 1/1 pass — evidence/story-3/; "
                                  "human-only — oauth (third-party consent screen)")
        feature_dir = fx.spec / "evidence" / "story-3" / "home"
        result = json.loads((feature_dir / "result.json").read_text())
        self.assertEqual(result["schema"], "app-verify-result-v1")
        for key in ("feature", "command", "exit_code", "verdict", "started_at", "ended_at",
                    "duration_s", "recipe_sha256", "truncated", "artifacts"):
            self.assertIn(key, result)
        self.assertEqual(result["verdict"], "pass")
        self.assertEqual(result["exit_code"], 0)
        self.assertEqual(set(result["truncated"]), {"stdout", "stderr"})
        self.assertEqual(len(result["recipe_sha256"]), 64)
        self.assertIn("check_home: ok", (feature_dir / "stdout.log").read_text())
        self.assertTrue((feature_dir / "stderr.log").exists())
        self.assertIn("app-verify fixture: home", (feature_dir / "home-body.txt").read_text())
        launch = fx.spec / "evidence" / "story-3" / "_launch"
        self.assertIn("serving on", (launch / "stdout.log").read_text())
        self.assertTrue(payload["launched"])
        self.assertEqual(payload["human_only"],
                         [{"feature": "oauth", "reason": "third-party consent screen"}])
        self.assert_no_fixture_survives(fx)
        self.assertTrue(fx.pids())

    def test_features_flag_restricts_and_reports_human_only(self) -> None:
        fx = self.make("recipe-pass.md")
        code, summary, payload = fx.run(features=["home", "oauth"])
        self.assertEqual(code, 0, summary)
        self.assertEqual([h["feature"] for h in payload["human_only"]], ["oauth"])
        self.assertIn("human-only — oauth (third-party consent screen)", summary)
        self.assert_no_fixture_survives(fx)

    def test_unknown_feature_is_unverifiable(self) -> None:
        fx = self.make("recipe-pass.md")
        code, summary, _ = fx.run(features=["nope"])
        self.assertEqual(code, 2)
        self.assertIn("unknown_feature: nope", summary)

    def test_only_human_only_selected_runs_nothing(self) -> None:
        fx = self.make("recipe-pass.md")
        code, summary, payload = fx.run(features=["oauth"])
        self.assertEqual(code, 2)
        self.assertEqual(summary, "app-verify: human-only — oauth (third-party consent screen)")
        self.assertEqual(payload["reason"], "no_runnable_features")
        self.assertEqual(fx.pids(), [])

    def test_fail_recipe(self) -> None:
        fx = self.make("recipe-fail.md")
        code, summary, payload = fx.run()
        self.assertEqual(code, 1, summary)
        self.assertEqual(summary,
                         "app-verify: 1/2 fail — broken (exit 1) — evidence/story-3/broken/")
        result = json.loads((fx.spec / "evidence/story-3/broken/result.json").read_text())
        self.assertEqual(result["verdict"], "fail")
        self.assertEqual(result["exit_code"], 1)
        home = json.loads((fx.spec / "evidence/story-3/home/result.json").read_text())
        self.assertEqual(home["verdict"], "pass")
        self.assert_no_fixture_survives(fx)

    def test_launch_exited(self) -> None:
        fx = self.make(text=custom_recipe("echo booting; exit 3", [("home", "true")]))
        code, summary, _ = fx.run()
        self.assertEqual(code, 1)
        self.assertEqual(summary, "app-verify: fail (launch_exited 3) — evidence/story-3/_launch/")
        self.assertIn("booting", (fx.spec / "evidence/story-3/_launch/stdout.log").read_text())
        self.assertFalse((fx.spec / "evidence/story-3/home").exists())

    def test_not_ready(self) -> None:
        fx = self.make("recipe-not-ready.md")
        code, summary, _ = fx.run()
        self.assertEqual(code, 1)
        self.assertEqual(summary, "app-verify: fail (not_ready 2s) — evidence/story-3/_launch/")
        self.assert_no_fixture_survives(fx)
        self.assertTrue(fx.pids())

    def test_port_readiness(self) -> None:
        fx = self.make(text=custom_recipe(
            FIXTURE_LAUNCH, [("home", f"PORT=8765 {sys.executable} {FIXTURE_DIR / 'check_home.py'}")],
            ready="port 8765"))
        code, summary, _ = fx.run()
        self.assertEqual(code, 0, summary)
        self.assert_no_fixture_survives(fx)

    def test_check_timeout_kills_its_group(self) -> None:
        marker = Path(tempfile.mkdtemp()) / "child.pid"
        self.addCleanup(lambda: marker.exists() and marker.unlink())
        sleeper = (f"{sys.executable} -c \"import os,time; open('{marker}','w').write(str(os.getpid()));"
                   f" time.sleep(60)\"")
        fx = self.make(text=custom_recipe(FIXTURE_LAUNCH, [("slow", sleeper)]))
        started = time.monotonic()
        code, summary, _ = fx.run(check_timeout_s=1)
        self.assertLess(time.monotonic() - started, 20)
        self.assertEqual(code, 1)
        result = json.loads((fx.spec / "evidence/story-3/slow/result.json").read_text())
        self.assertEqual(result["verdict"], "fail (timeout)")
        self.assertIsNone(result["exit_code"])
        self.assertTrue(pid_gone(int(marker.read_text())))
        self.assert_no_fixture_survives(fx)

    def test_log_truncation(self) -> None:
        noisy = f"{sys.executable} -c \"import sys; sys.stdout.write('x' * 300000)\""
        fx = self.make(text=custom_recipe(FIXTURE_LAUNCH, [("noisy", noisy)]))
        code, summary, _ = fx.run()
        self.assertEqual(code, 0, summary)
        feature_dir = fx.spec / "evidence/story-3/noisy"
        self.assertEqual((feature_dir / "stdout.log").stat().st_size, av.LOG_CAP_BYTES)
        result = json.loads((feature_dir / "result.json").read_text())
        self.assertTrue(result["truncated"]["stdout"])
        self.assertFalse(result["truncated"]["stderr"])
        self.assert_no_fixture_survives(fx)

    def test_artifacts_copied_too_large_and_missing(self) -> None:
        work = Path(tempfile.mkdtemp())
        self.addCleanup(lambda: __import__("shutil").rmtree(work, ignore_errors=True))
        (work / "out").mkdir()
        (work / "out" / "small.txt").write_text("trace")
        (work / "out" / "big.bin").write_bytes(b"\0" * (av.ARTIFACT_CAP_BYTES + 1))
        fx = self.make(text=custom_recipe(
            FIXTURE_LAUNCH, [("home", "true")],
            artifacts="out/small.txt, out/big.bin, out/missing.txt, ../escape.txt"))
        code, summary, _ = fx.run(cwd=work)
        self.assertEqual(code, 0, summary)
        feature_dir = fx.spec / "evidence/story-3/home"
        result = json.loads((feature_dir / "result.json").read_text())
        status = {a["path"]: a["status"] for a in result["artifacts"]}
        self.assertEqual(status, {"out/small.txt": "copied", "out/big.bin": "too_large",
                                  "out/missing.txt": "missing",
                                  "../escape.txt": "outside_project"})
        self.assertEqual((feature_dir / "artifacts" / "out" / "small.txt").read_text(), "trace")
        self.assertFalse((feature_dir / "artifacts" / "out" / "big.bin").exists())
        self.assert_no_fixture_survives(fx)

    def test_failing_after_command_is_a_note(self) -> None:
        fx = self.make(text=custom_recipe(FIXTURE_LAUNCH, [("home", "true")], after="exit 4"))
        code, summary, payload = fx.run()
        self.assertEqual(code, 0, summary)
        self.assertTrue(any("after" in n for n in payload["notes"]), payload["notes"])
        self.assert_no_fixture_survives(fx)

    def test_cleanup_escalates_to_sigkill(self) -> None:
        stubborn = (f"{sys.executable} -c \"import signal,os,time;"
                    f" signal.signal(signal.SIGTERM, signal.SIG_IGN);"
                    f" open('{{pidfile}}','a').write(str(os.getpid()));"
                    f" import http.server as h; h.HTTPServer(('127.0.0.1', 8765),"
                    f" h.SimpleHTTPRequestHandler).serve_forever()\"")
        fx = self.make(text=custom_recipe(stubborn, [("home", "true")]))
        fx.recipe.write_text(fx.recipe.read_text().replace("{pidfile}", str(fx.pidfile)))
        code, summary, payload = fx.run(cleanup_grace_s=0.5)
        self.assertEqual(code, 0, summary)
        self.assertTrue(any("SIGKILL" in n for n in payload["notes"]), payload["notes"])
        self.assert_no_fixture_survives(fx)

    def test_missing_spec_dir_is_unverifiable(self) -> None:
        fx = self.make("recipe-pass.md")
        code, summary, _ = av.run_verification(fx.recipe, fx.root / "nope", "uat",
                                               env=fx.env, cwd=REPO_ROOT)
        self.assertEqual(code, 2)
        self.assertIn("no_spec_dir", summary)

    def test_invalid_recipe_is_unverifiable(self) -> None:
        fx = self.make(text=VALID_RECIPE.replace("## Login\n", ""))
        code, summary, _ = fx.run()
        self.assertEqual(code, 2)
        self.assertIn("unverifiable (recipe_invalid: missing_section", summary)


class RunCliTests(unittest.TestCase):
    """AC-3.5 — exactly one summary line; JSON under --json; exit codes."""

    def test_cli_pass_json(self) -> None:
        fx = RunFixture("recipe-pass.md")
        self.addCleanup(fx.cleanup)
        proc = subprocess.run(
            [sys.executable, str(HELPER_PATH), "run", "--recipe", str(fx.recipe),
             "--spec", str(fx.spec), "--run-label", "uat", "--features", "home", "--json"],
            capture_output=True, text=True, cwd=str(REPO_ROOT), env=fx.env, timeout=60)
        self.assertEqual(proc.returncode, 0, proc.stdout + proc.stderr)
        lines = proc.stdout.strip().splitlines()
        self.assertEqual(len(lines), 2)
        self.assertEqual(lines[0], "app-verify: 1/1 pass — evidence/uat/")
        payload = json.loads(lines[1])
        self.assertEqual(payload["verdict"], "pass")
        self.assertTrue((fx.spec / "evidence/uat/home/result.json").exists())
        for pid in fx.pids():
            self.assertTrue(pid_gone(pid))

    def test_cli_sigterm_still_cleans_up(self) -> None:
        text = custom_recipe(f"{FIXTURE_LAUNCH} --never-ready", [("home", "true")])
        fx = RunFixture(text=text)
        self.addCleanup(fx.cleanup)
        proc = subprocess.Popen(
            [sys.executable, str(HELPER_PATH), "run", "--recipe", str(fx.recipe),
             "--spec", str(fx.spec), "--run-label", "uat"],
            stdout=subprocess.PIPE, stderr=subprocess.PIPE, cwd=str(REPO_ROOT), env=fx.env)
        deadline = time.monotonic() + 10
        while not fx.pids() and time.monotonic() < deadline:
            time.sleep(0.1)
        self.assertTrue(fx.pids(), "fixture never started")
        proc.terminate()
        proc.communicate(timeout=30)
        self.assertEqual(proc.returncode, 128 + 15)
        for pid in fx.pids():
            self.assertTrue(pid_gone(pid), f"fixture pid {pid} survived SIGTERM")

    def test_cli_main_in_process_missing_recipe(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            code = av.main(["run", "--recipe", f"{tmp}/none.md", "--spec", tmp,
                            "--run-label", "uat"])
        self.assertEqual(code, 2)


if __name__ == "__main__":
    unittest.main()
