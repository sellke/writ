"""scripts/check.py: a valid tree passes, and each rule fails on the mistake it exists for."""
import importlib.util
import json
from pathlib import Path

import pytest

REPO = Path(__file__).resolve().parents[2]
SPEC = importlib.util.spec_from_file_location("writ_check", REPO / "scripts" / "check.py")
check = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(check)

VERSION = "1.2.3"


def skill(root: Path, name: str, body: str, description: str = "What it does. Part of Writ.") -> Path:
    folder = root / "plugins" / "writ" / "skills" / name
    folder.mkdir(parents=True, exist_ok=True)
    (folder / "SKILL.md").write_text(
        "---\nname: %s\ndescription: %s\n---\n\n%s\n" % (name, description, body), encoding="utf-8")
    return folder


@pytest.fixture
def tree(tmp_path: Path) -> Path:
    front = skill(tmp_path, "writ", "Read `rules.md` in this folder first. Then `writ-build`.")
    (front / "rules.md").write_text("# Rules\n", encoding="utf-8")
    skill(tmp_path, "writ-build",
          "Read `../writ/rules.md` first. Hand off to `../writ-verify/SKILL.md`.")
    skill(tmp_path, "writ-verify", "Read `../writ/rules.md` first. Take `../<step>/SKILL.md`.")
    (tmp_path / "VERSION").write_text(VERSION + "\n", encoding="utf-8")
    for rel in check.PLUGIN_MANIFESTS:
        path = tmp_path / rel
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(json.dumps({"name": "writ", "version": VERSION}), encoding="utf-8")
    for rel in check.MARKETPLACES:
        path = tmp_path / rel
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(json.dumps({"plugins": [{"source": "./plugins/writ"}]}), encoding="utf-8")
    (tmp_path / "README.md").write_text("Use /writ, /writ-build, and /writ-verify.\n",
                                        encoding="utf-8")
    return tmp_path


def rules(root: Path):
    return [rule for rule, _ in check.run(root)]


def details(root: Path) -> str:
    return "\n".join(detail for _, detail in check.run(root))


def test_valid_tree_passes(tree, capsys):
    assert check.main(["--root", str(tree)]) == 0
    out = capsys.readouterr().out.splitlines()
    assert out[0] == "pass"
    assert out[-1].startswith("check: 3 skills")


def test_failure_prints_fail_first_and_exits_1(tree, capsys):
    (tree / "README.md").write_text("Use /writ.\n", encoding="utf-8")
    assert check.main(["--root", str(tree)]) == 1
    out = capsys.readouterr().out.splitlines()
    assert out[0] == "fail"
    assert any(line.startswith("fail: readme:") for line in out)


def test_root_must_be_a_directory(tmp_path):
    assert check.main(["--root", str(tmp_path / "nope")]) == 2


def test_name_must_match_folder(tree):
    skill(tree, "writ-build", "Read `../writ/rules.md` first.").joinpath("SKILL.md").write_text(
        "---\nname: build\ndescription: x\n---\nRead `../writ/rules.md` first.\n", encoding="utf-8")
    assert "frontmatter" in rules(tree)
    assert "declares name 'build'" in details(tree)


def test_skill_must_carry_the_writ_prefix(tree):
    skill(tree, "build", "Read `../writ/rules.md` first.")
    assert "skills/build is not named writ or writ-<word>" in details(tree)


def test_extra_frontmatter_keys_fail(tree):
    (tree / "plugins/writ/skills/writ-verify/SKILL.md").write_text(
        "---\nname: writ-verify\ndescription: x\nallowed-tools: Read\n---\n"
        "Read `../writ/rules.md` first.\n", encoding="utf-8")
    assert "keys other than name and description: allowed-tools" in details(tree)


def test_unclosed_frontmatter_fails(tree):
    (tree / "plugins/writ/skills/writ-verify/SKILL.md").write_text(
        "---\nname: writ-verify\ndescription: x\n\nRead `../writ/rules.md` first.\n",
        encoding="utf-8")
    assert "no closed frontmatter block" in details(tree)


@pytest.mark.parametrize("description", ["", "x" * 1025])
def test_description_length_is_bounded(tree, description):
    skill(tree, "writ-verify", "Read `../writ/rules.md` first.", description=description)
    assert "frontmatter" in rules(tree)


def test_folder_without_skill_file_fails(tree):
    (tree / "plugins/writ/skills/writ-empty").mkdir()
    assert "skills/writ-empty has no SKILL.md" in details(tree)


def test_skill_must_point_at_the_rules(tree):
    skill(tree, "writ-verify", "Just do it.")
    assert "rules-link" in rules(tree)


def test_dangling_relative_path_fails(tree):
    skill(tree, "writ-build", "Read `../writ/rules.md` first. Then `../writ-gone/SKILL.md`.")
    assert "points at ../writ-gone/SKILL.md" in details(tree)


def test_placeholder_paths_are_not_checked(tree):
    assert "<step>" not in details(tree)


def test_naming_a_skill_that_does_not_exist_fails(tree):
    skill(tree, "writ-build", "Read `../writ/rules.md` first. Next is `writ-deploy`.")
    assert "names the skill writ-deploy" in details(tree)


@pytest.mark.parametrize("term", ["AskUserQuestion", "todo_write", "Plan Mode", "Task("])
def test_platform_terms_fail(tree, term):
    skill(tree, "writ-build", "Read `../writ/rules.md` first. Use %s here." % term)
    assert "plain" in rules(tree)


def test_sibling_markdown_files_are_checked_too(tree):
    (tree / "plugins/writ/skills/writ/rules.md").write_text("Use TodoWrite.\n", encoding="utf-8")
    assert "skills/writ/rules.md uses the platform term 'TodoWrite'" in details(tree)


def test_manifest_version_must_match_version_file(tree):
    (tree / "VERSION").write_text("9.9.9\n", encoding="utf-8")
    found = details(tree)
    for rel in check.PLUGIN_MANIFESTS:
        assert "%s version is '%s'; VERSION says 9.9.9" % (rel, VERSION) in found


def test_manifest_name_must_be_writ(tree):
    path = tree / check.PLUGIN_MANIFESTS[0]
    path.write_text(json.dumps({"name": "other", "version": VERSION}), encoding="utf-8")
    assert "name is 'other'" in details(tree)


def test_missing_marketplace_fails(tree):
    (tree / check.MARKETPLACES[2]).unlink()
    assert "marketplace.json is missing or not JSON" in details(tree)


def test_marketplace_must_point_at_the_plugin(tree):
    (tree / check.MARKETPLACES[0]).write_text(json.dumps({"plugins": []}), encoding="utf-8")
    assert "does not point at plugins/writ" in details(tree)


def test_readme_must_name_every_skill(tree):
    (tree / "README.md").write_text("Use /writ and /writ-build.\n", encoding="utf-8")
    assert "README.md never mentions writ-verify" in details(tree)


def test_empty_plugin_fails(tmp_path):
    assert rules(tmp_path) == ["frontmatter"]


def test_this_repository_passes():
    assert check.run(REPO) == []
