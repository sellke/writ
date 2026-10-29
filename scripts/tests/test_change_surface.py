#!/usr/bin/env python3
"""Tests for scripts/change-surface.py (Story 4 of
`2026-09-08-phase11-stage2b-mechanize-the-gates`).

One fixture per surface class; empty / omitted `--changed` → exit 2.
[AC-4.3, AC-4.4, AC-4.5]
"""

from __future__ import annotations

import json
import subprocess
import sys
import unittest
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[2]
SCRIPT = REPO_ROOT / "scripts" / "change-surface.py"

CLASSES = (
    "style-only",
    "single-component",
    "cross-component",
    "full-stack",
)


def _run(args):
    proc = subprocess.run(
        [sys.executable, str(SCRIPT), *args],
        capture_output=True,
        text=True,
        cwd=str(REPO_ROOT),
    )
    return proc.returncode, proc.stdout.strip(), proc.stderr


def _class(out):
    return json.loads(out)["class"]


class ChangeSurfaceTests(unittest.TestCase):
    def test_style_only(self):
        code, out, err = _run(
            ["classify", "--changed", "src/styles/theme.css", "src/app.module.css"],
        )
        self.assertEqual(code, 0, err)
        self.assertEqual(_class(out), "style-only")

    def test_style_only_tailwind_config(self):
        code, out, err = _run(
            ["classify", "--changed", "tailwind.config.ts"],
        )
        self.assertEqual(code, 0, err)
        self.assertEqual(_class(out), "style-only")

    def test_single_component_plus_test(self):
        code, out, err = _run(
            [
                "classify",
                "--changed",
                "src/components/Form.tsx",
                "src/components/Form.test.tsx",
            ],
        )
        self.assertEqual(code, 0, err)
        self.assertEqual(_class(out), "single-component")

    def test_cross_component_shared_hook(self):
        code, out, err = _run(
            ["classify", "--changed", "src/hooks/useAuth.ts"],
        )
        self.assertEqual(code, 0, err)
        self.assertEqual(_class(out), "cross-component")

    def test_full_stack_schema(self):
        code, out, err = _run(
            ["classify", "--changed", "prisma/schema.prisma"],
        )
        self.assertEqual(code, 0, err)
        self.assertEqual(_class(out), "full-stack")

    def test_style_plus_migration_classifies_up_to_full_stack(self):
        code, out, err = _run(
            [
                "classify",
                "--changed",
                "src/styles/theme.css",
                "db/migrations/001_init.sql",
            ],
        )
        self.assertEqual(code, 0, err)
        self.assertEqual(_class(out), "full-stack")

    def test_two_components_classifies_up_to_cross_component(self):
        code, out, err = _run(
            [
                "classify",
                "--changed",
                "src/components/Form.tsx",
                "src/components/List.tsx",
            ],
        )
        self.assertEqual(code, 0, err)
        self.assertEqual(_class(out), "cross-component")

    def test_empty_changed_exits_2(self):
        code, out, _err = _run(["classify", "--changed"])
        self.assertEqual(code, 2)
        self.assertEqual(out, "")

    def test_omitted_changed_exits_2(self):
        code, out, _err = _run(["classify"])
        self.assertEqual(code, 2)
        self.assertEqual(out, "")

    def test_prints_one_json_object_with_class(self):
        """Agent CLI contract (data shape): stdout is one JSON object."""
        code, out, err = _run(["classify", "--changed", "src/lib/utils.ts"])
        self.assertEqual(code, 0, err)
        self.assertEqual(json.loads(out), {"class": "cross-component"})
        self.assertEqual(len(out.splitlines()), 1)

    def test_pretty_prints_bare_class_token(self):
        code, out, err = _run(["classify", "--changed", "src/lib/utils.ts", "--pretty"])
        self.assertEqual(code, 0, err)
        self.assertEqual(out, "cross-component")
        self.assertIn(out, CLASSES)

    def test_json_flag_is_a_no_op(self):
        args = ["classify", "--changed", "src/lib/utils.ts"]
        self.assertEqual(_run(args + ["--json"])[:2], _run(args)[:2])


class Gate25WiringTests(unittest.TestCase):
    """AC-4.4 / AC-4.5 — Gate 2.5 runs the classifier."""

    def test_gate_2_5_invokes_classify(self) -> None:
        text = (REPO_ROOT / "commands" / "implement-story.md").read_text(encoding="utf-8")
        start = text.index("#### Gate 2.5: Change Surface Classification")
        end = text.index("#### Gate 3:", start)
        gate = text[start:end]
        self.assertIn("scripts/change-surface.py classify", gate)

    def test_frontmatter_names_change_surface(self) -> None:
        text = (REPO_ROOT / "commands" / "implement-story.md").read_text(encoding="utf-8")
        self.assertIn("  - id: gate2_5_surface\n    script: scripts/change-surface.py", text)



# ---------------------------------------------------------------------------
# Story 3 of `2026-10-25-review-route-rigor`: the `blast-radius` subcommand and
# the Gate 2.5 "Blast radius." paragraph. Fixture repos are built in
# TemporaryDirectory; `classify` output is pinned unchanged.
# [AC-3.1, AC-3.2, AC-3.3, AC-3.4, AC-3.5]
# ---------------------------------------------------------------------------

import importlib.util  # noqa: E402
import os  # noqa: E402
from tempfile import TemporaryDirectory  # noqa: E402
from typing import Dict, List, Optional, Tuple, Union  # noqa: E402

BLAST_KEYS = ["verdict", "consumers", "tests", "truncated", "reasons"]


def _isolated_env(ceiling: Path) -> Dict[str, str]:
    """Env that keeps git off the user's config and out of enclosing repos."""
    env = dict(os.environ)
    env["GIT_CONFIG_GLOBAL"] = os.devnull
    env["GIT_CONFIG_NOSYSTEM"] = "1"
    env["GIT_CEILING_DIRECTORIES"] = str(ceiling)
    return env


class _BlastRepo(unittest.TestCase):
    """Base: a fresh temp dir per test; `git=True` makes it a repo (index only)."""

    git = True

    def setUp(self) -> None:
        self._tmp = TemporaryDirectory()
        self.addCleanup(self._tmp.cleanup)
        self.root = Path(self._tmp.name).resolve()
        self.repo = self.root / "repo"
        self.repo.mkdir()
        self.env = _isolated_env(self.root)
        if self.git:
            self._git("init", "-q")

    def _git(self, *args: str) -> None:
        subprocess.run(["git", *args], cwd=str(self.repo), env=self.env,
                       check=True, capture_output=True)

    def write(self, rel: str, content: Union[str, bytes]) -> Path:
        path = self.repo / rel
        path.parent.mkdir(parents=True, exist_ok=True)
        if isinstance(content, bytes):
            path.write_bytes(content)
        else:
            path.write_text(content, encoding="utf-8")
        return path

    def add_all(self) -> None:
        if self.git:
            self._git("add", "-A")

    def run_blast(self, *args: str, repo: Optional[str] = None) -> Tuple[int, str, str]:
        argv = [sys.executable, str(SCRIPT), "blast-radius", *args]
        argv += ["--repo", repo if repo is not None else str(self.repo)]
        proc = subprocess.run(argv, capture_output=True, text=True,
                              cwd=str(self.root), env=self.env)
        return proc.returncode, proc.stdout, proc.stderr

    def blast(self, *args: str, repo: Optional[str] = None) -> dict:
        code, out, err = self.run_blast(*args, repo=repo)
        self.assertEqual(code, 0, err)
        self.assertEqual(err, "")
        self.assertEqual(len(out.strip().splitlines()), 1, out)
        data = json.loads(out)
        self.assertEqual(list(data), BLAST_KEYS)
        return data

    def consumers_of(self, changed: str, *extra: str) -> List[str]:
        return self.blast("--changed", changed, *extra)["consumers"][changed]


class BlastRadiusTokenTests(_BlastRepo):
    """Story 3 of `2026-10-25-review-route-rigor` — tokens, boundaries,
    generic and short stems. [AC-3.1, AC-3.2]"""

    def test_stem_match_lists_referrer(self) -> None:
        self.write("scripts/review-override.py", "x = 1\n")
        self.write("docs/guide.md", "Run review-override before merging.\n")
        self.add_all()
        self.assertEqual(self.consumers_of("scripts/review-override.py"), ["docs/guide.md"])

    def test_path_match_with_and_without_extension(self) -> None:
        # `utils` is generic, so only the path tokens can match here.
        self.write("src/utils.py", "x = 1\n")
        self.write("a.md", "See src/utils.py for helpers.\n")
        self.write("b.ts", "import x from 'src/utils';\n")
        self.write("c.md", "The utils module.\n")
        self.add_all()
        self.assertEqual(self.consumers_of("src/utils.py"), ["a.md", "b.ts"])

    def test_generic_stem_index_matches_by_path_only(self) -> None:
        self.write("web/index.ts", "export {}\n")
        self.write("web/page.ts", "import { x } from './index';\n")
        self.write("web/app.ts", "import { x } from 'web/index';\n")
        self.add_all()
        self.assertEqual(self.consumers_of("web/index.ts"), ["web/app.ts"])

    def test_generic_stem_is_case_insensitive(self) -> None:
        self.write("docs/README.md", "# Docs\n")
        self.write("a.md", "Read the README first.\n")
        self.write("b.md", "Read docs/README.md first.\n")
        self.add_all()
        self.assertEqual(self.consumers_of("docs/README.md"), ["b.md"])

    def test_short_stem_matches_by_path_only(self) -> None:
        self.write("lib/abc.py", "x = 1\n")
        self.write("a.md", "The abc helper.\n")
        self.write("b.md", "See lib/abc.py.\n")
        self.add_all()
        self.assertEqual(self.consumers_of("lib/abc.py"), ["b.md"])

    def test_top_level_generic_file_needs_its_extension(self) -> None:
        # At the repo root the extensionless path is the bare stem; a generic
        # stem must not slip back in through that token.
        self.write("setup.py", "x = 1\n")
        self.write("a.md", "Run setup first.\n")
        self.write("b.md", "Run setup.py first.\n")
        self.add_all()
        self.assertEqual(self.consumers_of("setup.py"), ["b.md"])

    def test_token_boundaries(self) -> None:
        self.write("scripts/review-override.py", "x = 1\n")
        self.write("v2.md", "Use review-override-v2 now.\n")
        self.write("under.md", "my_review-override is different.\n")
        self.write("prefix.md", "xreview-override is different.\n")
        self.write("dotpy.md", "Run review-override.py check.\n")
        self.write("tick.md", "Run `review-override` check.\n")
        self.write("eol.md", "ends with review-override")
        self.add_all()
        self.assertEqual(self.consumers_of("scripts/review-override.py"),
                         ["dotpy.md", "eol.md", "tick.md"])

    def test_changed_path_is_normalized(self) -> None:
        self.write("scripts/review-override.py", "x = 1\n")
        self.write("docs/guide.md", "Run review-override.\n")
        self.add_all()
        data = self.blast("--changed", ".\\scripts\\review-override.py")
        self.assertEqual(data["consumers"], {"scripts/review-override.py": ["docs/guide.md"]})


class BlastRadiusCandidateTests(_BlastRepo):
    """Story 3 of `2026-10-25-review-route-rigor` — candidate exclusions and
    unreadable or oversized files. [AC-3.1]"""

    def test_writ_dir_is_excluded(self) -> None:
        self.write("scripts/review-override.py", "x = 1\n")
        self.write(".writ/specs/s/spec.md", "Calls review-override.\n")
        self.write("pkg/.writ/state/x.md", "Calls review-override.\n")
        self.write("docs/guide.md", "Calls review-override.\n")
        self.add_all()
        self.assertEqual(self.consumers_of("scripts/review-override.py"), ["docs/guide.md"])

    def test_changed_files_are_excluded(self) -> None:
        self.write("src/alpha.py", "import bravo\n")
        self.write("src/bravo.py", "import alpha\n")
        self.write("tests/test_alpha.py", "import alpha\n")
        self.write("docs/a.md", "alpha and bravo\n")
        self.add_all()
        data = self.blast("--changed", "src/alpha.py", "src/bravo.py", "tests/test_alpha.py")
        self.assertEqual(data["consumers"], {"src/alpha.py": ["docs/a.md"],
                                             "src/bravo.py": ["docs/a.md"]})
        self.assertEqual(data["tests"], {"src/alpha.py": [], "src/bravo.py": []})

    def test_oversized_and_non_utf8_files_are_skipped(self) -> None:
        self.write("scripts/review-override.py", "x = 1\n")
        self.write("big.md", "review-override\n" + "x" * (1024 * 1024))
        self.write("latin.md", b"review-override \xff\xfe caf\xe9\n")
        self.write("ok.md", "review-override\n")
        self.add_all()
        self.assertEqual(self.consumers_of("scripts/review-override.py"), ["ok.md"])

    def test_unreadable_candidates_are_skipped(self) -> None:
        self.write("scripts/review-override.py", "x = 1\n")
        self.write("real/f.md", "review-override\n")
        os.symlink("real", str(self.repo / "link"))
        self.write("gone.md", "review-override\n")
        self.add_all()
        (self.repo / "gone.md").unlink()
        self.assertEqual(self.consumers_of("scripts/review-override.py"), ["real/f.md"])

    @unittest.skipIf(not hasattr(os, "geteuid") or os.geteuid() == 0,
                     "root reads mode-000 files")
    def test_permission_denied_candidate_is_skipped(self) -> None:
        self.write("scripts/review-override.py", "x = 1\n")
        locked = self.write("locked.md", "review-override\n")
        self.write("ok.md", "review-override\n")
        self.add_all()
        locked.chmod(0)
        self.addCleanup(locked.chmod, 0o644)
        self.assertEqual(self.consumers_of("scripts/review-override.py"), ["ok.md"])


class BlastRadiusSplitTests(_BlastRepo):
    """Story 3 of `2026-10-25-review-route-rigor` — test-like referrers go
    under `tests`; test-like changed files get no key. [AC-3.1, AC-3.4]"""

    TEST_LIKE = (
        "src/widget.test.ts",
        "src/widget.spec.js",
        "src/__tests__/w.js",
        "pkg/test_widget.py",
        "pkg/widget_test.py",
        "go/widget_test.go",
        "test/check.sh",
        "tests/check.sh",
        "src/nested/tests/x.md",
    )
    NOT_TEST = ("src/app.py", "src/testing/x.py", "src/contest.py", "pkg/test_widget.md")

    def test_each_test_pattern_goes_to_tests(self) -> None:
        self.write("src/widget.py", "x = 1\n")
        for rel in self.TEST_LIKE + self.NOT_TEST:
            self.write(rel, "uses widget\n")
        self.add_all()
        data = self.blast("--changed", "src/widget.py")
        self.assertEqual(data["tests"], {"src/widget.py": sorted(self.TEST_LIKE)})
        self.assertEqual(data["consumers"], {"src/widget.py": sorted(self.NOT_TEST)})
        self.assertEqual(data["verdict"], "pass")

    def test_test_like_changed_file_is_not_a_key(self) -> None:
        self.write("src/widget.py", "x = 1\n")
        self.write("tests/test_widget.py", "import widget\n")
        self.write("docs/a.md", "widget and test_widget\n")
        self.add_all()
        data = self.blast("--changed", "src/widget.py", "tests/test_widget.py")
        self.assertEqual(list(data["consumers"]), ["src/widget.py"])
        self.assertEqual(list(data["tests"]), ["src/widget.py"])

    def test_every_changed_file_a_test_gives_empty_maps(self) -> None:
        self.write("tests/test_widget.py", "x = 1\n")
        self.write("src/widget.spec.ts", "x = 1\n")
        self.write("docs/a.md", "test_widget\n")
        self.add_all()
        data = self.blast("--changed", "tests/test_widget.py", "src/widget.spec.ts")
        self.assertEqual(data, {"verdict": "pass", "consumers": {}, "tests": {},
                                "truncated": [], "reasons": []})


class BlastRadiusCapTests(_BlastRepo):
    """Story 3 of `2026-10-25-review-route-rigor` — `--limit` cap and
    `truncated`. [AC-3.3]"""

    def _fixture(self) -> None:
        self.write("core/engine.py", "x = 1\n")
        for rel in ("d.md", "a.md", "c.md", "b.md", "tests/t1.md", "tests/t2.md",
                    "tests/t3.md"):
            self.write(rel, "engine\n")
        self.add_all()

    def test_limit_2_caps_both_lists_sorted_and_lists_truncated_once(self) -> None:
        self._fixture()
        data = self.blast("--changed", "core/engine.py", "--limit", "2")
        self.assertEqual(data["consumers"], {"core/engine.py": ["a.md", "b.md"]})
        self.assertEqual(data["tests"], {"core/engine.py": ["tests/t1.md", "tests/t2.md"]})
        self.assertEqual(data["truncated"], ["core/engine.py"])

    def test_default_limit_does_not_truncate_small_lists(self) -> None:
        self._fixture()
        data = self.blast("--changed", "core/engine.py")
        self.assertEqual(data["consumers"]["core/engine.py"], ["a.md", "b.md", "c.md", "d.md"])
        self.assertEqual(data["truncated"], [])

    def test_limit_below_1_is_usage(self) -> None:
        self._fixture()
        code, out, err = self.run_blast("--changed", "core/engine.py", "--limit", "0")
        self.assertEqual(code, 2)
        self.assertEqual(out, "")
        self.assertIn("usage", err)


class BlastRadiusNoGitTests(_BlastRepo):
    """Story 3 of `2026-10-25-review-route-rigor` — `git ls-files` fails, so
    the repo is walked: `pass` with `no_git_walked`. [AC-3.4]"""

    git = False

    def test_walk_fallback_skips_dot_dirs_and_node_modules(self) -> None:
        self.write("scripts/review-override.py", "x = 1\n")
        self.write("docs/a.md", "review-override\n")
        self.write(".hidden/b.md", "review-override\n")
        self.write(".writ/specs/c.md", "review-override\n")
        self.write("node_modules/pkg/d.js", "review-override\n")
        self.write("lib/node_modules/e.js", "review-override\n")
        self.write("tests/test_f.py", "review-override\n")
        data = self.blast("--changed", "scripts/review-override.py")
        self.assertEqual(data["verdict"], "pass")
        self.assertEqual(data["reasons"], ["no_git_walked"])
        self.assertEqual(data["consumers"], {"scripts/review-override.py": ["docs/a.md"]})
        self.assertEqual(data["tests"], {"scripts/review-override.py": ["tests/test_f.py"]})

    def test_walk_skips_oversized_and_non_utf8(self) -> None:
        self.write("scripts/review-override.py", "x = 1\n")
        self.write("big.md", "review-override\n" + "x" * (1024 * 1024))
        self.write("latin.md", b"review-override \xff\n")
        self.write("ok.md", "review-override\n")
        self.assertEqual(self.consumers_of("scripts/review-override.py"), ["ok.md"])

    @unittest.skipIf(not hasattr(os, "mkfifo"), "no named pipes on this platform")
    def test_walk_skips_fifo_without_blocking(self) -> None:
        self.write("scripts/review-override.py", "x = 1\n")
        self.write("ok.md", "review-override\n")
        os.mkfifo(str(self.repo / "pipe"))
        proc = subprocess.run(
            [sys.executable, str(SCRIPT), "blast-radius", "--changed",
             "scripts/review-override.py", "--repo", str(self.repo)],
            capture_output=True, text=True, cwd=str(self.root), env=self.env, timeout=60,
        )
        self.assertEqual(proc.returncode, 0, proc.stderr)
        self.assertEqual(json.loads(proc.stdout)["consumers"],
                         {"scripts/review-override.py": ["ok.md"]})


class BlastRadiusUsageTests(_BlastRepo):
    """Story 3 of `2026-10-25-review-route-rigor` — bad `--repo`, empty or
    omitted `--changed`, JSON and `--pretty` shapes. [AC-3.4]"""

    def test_bad_repo_is_unverifiable_exit_0(self) -> None:
        expected = {"verdict": "unverifiable", "consumers": {}, "tests": {},
                    "truncated": [], "reasons": ["repo_unreadable"]}
        missing = str(self.root / "missing")
        self.assertEqual(self.blast("--changed", "a.py", repo=missing), expected)
        afile = self.write("plain.txt", "x\n")
        self.assertEqual(self.blast("--changed", "a.py", repo=str(afile)), expected)

    def test_empty_changed_exits_2(self) -> None:
        for args in (["--changed"], [], ["--changed", ""], ["--changed", " "]):
            code, out, err = self.run_blast(*args)
            self.assertEqual(code, 2, args)
            self.assertEqual(out, "", args)
            self.assertIn("usage", err, args)

    def test_json_flag_is_a_no_op(self) -> None:
        self.write("scripts/review-override.py", "x = 1\n")
        self.write("docs/a.md", "review-override\n")
        self.add_all()
        args = ("--changed", "scripts/review-override.py")
        self.assertEqual(self.run_blast(*args, "--json"), self.run_blast(*args))

    def test_pretty_shape(self) -> None:
        self.write("src/alpha.py", "x = 1\n")
        self.write("src/bravo.py", "x = 1\n")
        self.write("docs/both.md", "alpha and bravo\n")
        self.write("docs/one.md", "alpha\n")
        self.write("tests/test_x.py", "bravo\n")
        self.add_all()
        code, out, err = self.run_blast("--changed", "src/bravo.py", "src/alpha.py",
                                        "--pretty")
        self.assertEqual(code, 0, err)
        self.assertEqual(out.splitlines(), [
            "pass",
            "src/alpha.py: 2 consumer(s), 0 test(s)",
            "src/bravo.py: 1 consumer(s), 1 test(s)",
            "change-surface blast-radius: pass (2 changed, 2 consumers)",
        ])

    def test_pretty_counts_every_match_and_prints_reasons(self) -> None:
        # Walk mode adds a reason line; counts are taken before the cap.
        shutil_dir = self.root / "plain"
        shutil_dir.mkdir()
        (shutil_dir / "core").mkdir()
        (shutil_dir / "core" / "engine.py").write_text("x = 1\n", encoding="utf-8")
        for name in ("a.md", "b.md", "c.md"):
            (shutil_dir / name).write_text("engine\n", encoding="utf-8")
        code, out, err = self.run_blast("--changed", "core/engine.py", "--limit", "1",
                                        "--pretty", repo=str(shutil_dir))
        self.assertEqual(code, 0, err)
        self.assertEqual(out.splitlines(), [
            "pass",
            "core/engine.py: 3 consumer(s), 0 test(s)",
            "reason: no_git_walked",
            "change-surface blast-radius: pass (1 changed, 3 consumers)",
        ])

    def test_pretty_unverifiable(self) -> None:
        code, out, err = self.run_blast("--changed", "a.py", "--pretty",
                                        repo=str(self.root / "missing"))
        self.assertEqual(code, 0, err)
        lines = out.splitlines()
        self.assertEqual(lines[0], "unverifiable")
        self.assertIn("reason: repo_unreadable", lines)
        self.assertTrue(lines[-1].startswith("change-surface blast-radius: unverifiable ("))


class BlastRadiusRealRepoTests(unittest.TestCase):
    """Story 3 of `2026-10-25-review-route-rigor` — one run on this repo.
    [AC-3.1]"""

    def test_change_surface_consumers_on_this_repo(self) -> None:
        if not (REPO_ROOT / ".git").exists():
            self.skipTest("not a git checkout")
        proc = subprocess.run(
            [sys.executable, str(SCRIPT), "blast-radius", "--changed",
             "scripts/change-surface.py", "--repo", str(REPO_ROOT), "--limit", "500"],
            capture_output=True, text=True, cwd=str(REPO_ROOT),
        )
        self.assertEqual(proc.returncode, 0, proc.stderr)
        data = json.loads(proc.stdout)
        consumers = data["consumers"]["scripts/change-surface.py"]
        tests = data["tests"]["scripts/change-surface.py"]
        self.assertEqual(data["verdict"], "pass")
        self.assertIn("commands/implement-story.md", consumers)
        self.assertIn("scripts/tests/test_change_surface.py", tests)
        self.assertFalse([p for p in consumers + tests if p.startswith(".writ/")])


def _load_module():
    spec = importlib.util.spec_from_file_location("change_surface_mod", str(SCRIPT))
    module = importlib.util.module_from_spec(spec)
    assert spec.loader is not None
    spec.loader.exec_module(module)
    return module


class ClassifyUnchangedTests(unittest.TestCase):
    """Story 3 of `2026-10-25-review-route-rigor` — `classify` output, exit
    codes, and `is_test` match the behavior before `blast-radius`. [AC-3.4]"""

    def test_classify_outputs_and_exit_codes(self) -> None:
        cases = [
            (["--changed", "src/lib/utils.ts"], 0, '{"class": "cross-component"}'),
            (["--changed", "src/lib/utils.ts", "--pretty"], 0, "cross-component"),
            (["--changed", "src/components/Form.tsx", "src/components/Form.test.tsx"],
             0, '{"class": "single-component"}'),
            (["--changed", "tests/test_x.py"], 0, '{"class": "cross-component"}'),
            (["--changed", "prisma/schema.prisma", "--json"], 0, '{"class": "full-stack"}'),
            (["--changed"], 2, ""),
            ([], 2, ""),
        ]
        for args, code, out in cases:
            got_code, got_out, _err = _run(["classify", *args])
            self.assertEqual((got_code, got_out), (code, out), args)

    def test_is_test_is_unchanged(self) -> None:
        mod = _load_module()
        self.assertTrue(mod.is_test("src/a.test.ts"))
        self.assertTrue(mod.is_test("src/__tests__/a.js"))
        self.assertFalse(mod.is_test("tests/test_x.py"))
        self.assertFalse(mod.is_test("pkg/a_test.go"))


class Gate25BlastRadiusTextTests(unittest.TestCase):
    """Story 3 of `2026-10-25-review-route-rigor` — Gate 2.5 runs blast-radius
    on the review-agent route when the safety-fact switch is on. [AC-3.5]"""

    def setUp(self) -> None:
        text = (REPO_ROOT / "commands" / "implement-story.md").read_text(encoding="utf-8")
        start = text.index("#### Gate 2.5:")
        self.gate = text[start:text.index("#### Gate 3:", start)]
        g0 = text.index("#### Gate 0:")
        self.gate0 = text[g0:text.index("#### Gate 0.5:", g0)]

    def test_gate_2_5_names_switch_command_file_and_input(self) -> None:
        for needle in ("review-override.py switch --name safety-fact",
                       "change-surface.py blast-radius",
                       ".writ/state/blast-radius-<story-stem>.json",
                       "`blast_radius`", "`(none)`", "`review-agent`"):
            self.assertIn(needle, self.gate)

    def test_blast_radius_follows_switch_and_unverifiable_sentence(self) -> None:
        unverifiable = self.gate.index("routes `review-agent` with reason `unverifiable: <reason>`")
        switch = self.gate.index("review-override.py switch --name safety-fact")
        blast = self.gate.index("change-surface.py blast-radius")
        self.assertLess(unverifiable, switch)
        self.assertLess(switch, blast)

    def test_gate_0_does_not_run_blast_radius(self) -> None:
        self.assertNotIn("blast-radius", self.gate0)
        self.assertNotIn("blast_radius", self.gate0)


if __name__ == "__main__":
    unittest.main()
