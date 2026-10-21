#!/usr/bin/env python3
"""Lifecycle command docs keep `CLAUDE.md` user-owned, Story 4 of
`2026-10-20-claude-code-parity`.

`commands/uninstall-writ.md` and `commands/reinstall-writ.md` must never tell
the reader to delete `CLAUDE.md` or copy the template over it. Their Claude
Code bullets remove or merge only between the Writ markers, `/reinstall-writ`
Step 4 names the scripted path (`install.sh --platform claude --force`), and
both "Do NOT remove" lists name the Claude Code content outside the markers.
These tests read the two docs as text.

Covers AC-4.4.

Run: uv run pytest scripts/tests/test_lifecycle_commands_claude_md.py
"""

from __future__ import annotations

import re
import unittest
from pathlib import Path
from typing import List, Optional

REPO_ROOT = Path(__file__).resolve().parents[2]
UNINSTALL_DOC = REPO_ROOT / "commands" / "uninstall-writ.md"
REINSTALL_DOC = REPO_ROOT / "commands" / "reinstall-writ.md"

START_MARKER = "<!-- writ:start -->"
END_MARKER = "<!-- writ:end -->"

# An `rm` whose arguments include the project-root CLAUDE.md, within one line
# or one code span: `rm CLAUDE.md`, `rm -f ./CLAUDE.md`, `rm a.md CLAUDE.md`.
RM_CLAUDE_MD = re.compile(r"\brm\b[^`\n]*?(?<![\w./-])(?:\./)?CLAUDE\.md\b")
# A `cp` of the template onto the project-root CLAUDE.md, with or without `./`.
CP_TEMPLATE_ONTO_CLAUDE_MD = re.compile(
    r"\bcp(?:\s+-\w+)*\s+\S*claude-code/CLAUDE\.md\s+[\"']?(?:\./)?CLAUDE\.md\b"
)
FORCE_INSTALL = "install.sh --platform claude --force"
UNINSTALL_SCRIPT = "uninstall.sh --platform claude"


def read(path: Path) -> str:
    return path.read_text(encoding="utf-8")


def claude_bullet_after(text: str, anchor: str) -> Optional[str]:
    """The first `- Claude Code:` bullet after the anchor line, with its
    indented continuation lines, or None."""
    lines = text.splitlines()
    for i, line in enumerate(lines):
        if anchor in line:
            break
    else:
        return None
    for j in range(i + 1, len(lines)):
        m = re.match(r"^(\s*)- Claude Code: ", lines[j])
        if not m:
            continue
        indent = len(m.group(1))
        bullet = [lines[j]]
        for k in range(j + 1, len(lines)):
            nxt = lines[k]
            if not nxt.strip():
                break
            lead = len(nxt) - len(nxt.lstrip())
            if lead <= indent or nxt.lstrip().startswith("- "):
                break
            bullet.append(nxt)
        return "\n".join(bullet)
    return None


def list_after(text: str, anchor: str) -> List[str]:
    """The `- ` items of the list that follows the anchor line."""
    lines = text.splitlines()
    for i, line in enumerate(lines):
        if line.strip() == anchor:
            break
    else:
        return []
    items: List[str] = []
    for line in lines[i + 1:]:
        if line.startswith("- "):
            items.append(line)
        elif items and line.startswith("  ") and line.strip():
            items[-1] += "\n" + line
        elif items or line.strip():
            break
    return items


def claude_table_row(text: str) -> Optional[str]:
    for line in text.splitlines():
        if line.startswith("| `claude` |"):
            return line
    return None


class NoDeleteOrCopyOverClaudeMd(unittest.TestCase):
    """AC-4.4: neither doc deletes CLAUDE.md or copies the template onto it."""

    def test_uninstall_doc_has_no_rm_claude_md(self) -> None:
        found = [m.group(0) for m in RM_CLAUDE_MD.finditer(read(UNINSTALL_DOC))]
        self.assertEqual(found, [], f"uninstall-writ.md deletes CLAUDE.md: {found}")

    def test_reinstall_doc_has_no_rm_claude_md(self) -> None:
        found = [m.group(0) for m in RM_CLAUDE_MD.finditer(read(REINSTALL_DOC))]
        self.assertEqual(found, [], f"reinstall-writ.md deletes CLAUDE.md: {found}")

    def test_no_copy_of_template_onto_claude_md(self) -> None:
        for doc in (REINSTALL_DOC, UNINSTALL_DOC):
            found = [m.group(0) for m in CP_TEMPLATE_ONTO_CLAUDE_MD.finditer(read(doc))]
            self.assertEqual(
                found, [], f"{doc.name} copies claude-code/CLAUDE.md onto CLAUDE.md: {found}"
            )

    def test_patterns_catch_the_old_text(self) -> None:
        # The two lines the docs carried before this story.
        self.assertTrue(
            RM_CLAUDE_MD.search("- Claude Code: `rm .claude/system-instructions.md` and `rm CLAUDE.md`")
        )
        self.assertTrue(RM_CLAUDE_MD.search("`rm -f ./CLAUDE.md`"))
        self.assertTrue(RM_CLAUDE_MD.search("`rm .claude/system-instructions.md CLAUDE.md`"))
        self.assertIsNone(RM_CLAUDE_MD.search("`rm .claude/system-instructions.md`"))
        self.assertTrue(
            CP_TEMPLATE_ONTO_CLAUDE_MD.search("`cp $WRIT_SRC/claude-code/CLAUDE.md ./CLAUDE.md`")
        )
        self.assertTrue(
            CP_TEMPLATE_ONTO_CLAUDE_MD.search("cp $WRIT_SRC/claude-code/CLAUDE.md CLAUDE.md")
        )


class ClaudeBulletsUseTheMarkers(unittest.TestCase):
    """AC-4.4: the Claude bullets remove or merge only between the markers."""

    def assert_names_markers(self, doc: Path, anchor: str) -> str:
        bullet = claude_bullet_after(read(doc), anchor)
        self.assertIsNotNone(bullet, f"{doc.name}: no Claude Code bullet after {anchor!r}")
        assert bullet is not None
        self.assertIn(START_MARKER, bullet, f"{doc.name}: bullet after {anchor!r} does not name {START_MARKER}")
        self.assertIn(END_MARKER, bullet, f"{doc.name}: bullet after {anchor!r} does not name {END_MARKER}")
        self.assertIn("CLAUDE.md", bullet)
        return bullet

    def test_uninstall_step_3_removes_only_the_block(self) -> None:
        bullet = self.assert_names_markers(UNINSTALL_DOC, "**Platform-specific files:**")
        self.assertIn(UNINSTALL_SCRIPT, bullet, "uninstall-writ.md Step 3: does not name the scripted path")

    def test_reinstall_step_3_leaves_claude_md(self) -> None:
        self.assert_names_markers(REINSTALL_DOC, "**Files to remove:**")

    def test_reinstall_step_4_merges_between_markers(self) -> None:
        bullet = self.assert_names_markers(REINSTALL_DOC, "Copy platform-specific files:")
        self.assertIn(FORCE_INSTALL, bullet, f"reinstall-writ.md Step 4: does not name {FORCE_INSTALL}")

    def test_reinstall_platform_table_names_the_block(self) -> None:
        row = claude_table_row(read(REINSTALL_DOC))
        self.assertIsNotNone(row, "reinstall-writ.md: no Claude platform table row")
        self.assertIn("`CLAUDE.md` Writ block", row or "")


class DoNotRemoveListsNameUserContent(unittest.TestCase):
    """AC-4.4: both "Do NOT remove" lists name the content outside the markers."""

    def assert_lists_outside_content(self, doc: Path) -> None:
        items = list_after(read(doc), "**Do NOT remove:**")
        self.assertTrue(items, f"{doc.name}: no 'Do NOT remove' list")
        claude_items = [
            item
            for item in items
            if "CLAUDE.md" in item
            and "outside" in item
            and START_MARKER in item
            and END_MARKER in item
        ]
        self.assertTrue(
            claude_items,
            f"{doc.name}: the 'Do NOT remove' list does not name CLAUDE.md content outside the markers",
        )

    def test_uninstall_do_not_remove(self) -> None:
        self.assert_lists_outside_content(UNINSTALL_DOC)

    def test_reinstall_do_not_remove(self) -> None:
        self.assert_lists_outside_content(REINSTALL_DOC)


if __name__ == "__main__":
    unittest.main()
