#!/usr/bin/env python3
"""Gate 5 docs check (Story 3 of
`2026-09-08-phase11-stage2b-mechanize-the-gates`).

Diffs explicit public exports in `--changed` (or `git diff --name-only`
against `HEAD^`) against documented symbols in README / CHANGELOG / a
detected docs framework / adjacent docstrings.

Export discovery is conservative: Python `__all__`, JS/TS `export` /
`exports`, `export function|class|const`. Markdown never invents exports.

Subcommand:
  check --repo . [--changed FILE …]
  `--project` is accepted as an alias of `--repo`.

Prints one verdict line (`pass` / `fail` / `unverifiable`), optional
`reason: <code>` lines, then a summary line last.

Exit 0: ran, no blocking verdict (`pass` or `unverifiable`).
Exit 1: `fail`.
Exit 2: usage.
"""

from __future__ import annotations

import argparse
import re
import subprocess
import sys
from pathlib import Path
from typing import List, Optional, Sequence, Set, Tuple


EXPORT_SUFFIXES = frozenset({
    ".py", ".pyi", ".js", ".jsx", ".mjs", ".cjs", ".ts", ".tsx",
})
DOC_SUFFIXES = frozenset({
    ".md", ".mdx", ".rst", ".txt", ".html",
})
README_NAMES = frozenset({
    "readme", "readme.md", "readme.mdx", "readme.rst", "readme.txt",
})
CHANGELOG_NAMES = frozenset({
    "changelog", "changelog.md", "changelog.mdx", "changelog.rst",
    "changes", "changes.md", "history", "history.md",
})

IDENT = r"[A-Za-z_$][\w$]*"

RE_ALL = re.compile(
    r"__all__\s*=\s*(\[[^\]]*\]|\([^)]*\))",
    re.DOTALL,
)
RE_QUOTED = re.compile(r"""['"]([^'"]+)['"]""")
RE_EXPORT_DECL = re.compile(
    r"\bexport\s+(?:async\s+)?(?:function|class|const|let|var|type|interface|enum)\s+"
    r"(" + IDENT + r")"
)
RE_EXPORT_DEFAULT_NAMED = re.compile(
    r"\bexport\s+default\s+(?:async\s+)?(?:function|class)\s+(" + IDENT + r")"
)
RE_EXPORT_LIST = re.compile(r"\bexport\s+(?:type\s+)?\{([^}]+)\}")
RE_EXPORT_AS = re.compile(
    r"(?:" + IDENT + r"\s+as\s+)?(" + IDENT + r")"
)
RE_EXPORTS_DOT = re.compile(r"\bexports\.(" + IDENT + r")\s*=")
RE_MODULE_EXPORTS_OBJ = re.compile(
    r"\bmodule\.exports\s*=\s*\{([^}]+)\}"
)
RE_OBJ_KEY = re.compile(
    r"""(?:['"]([^'"]+)['"]|(""" + IDENT + r"))\s*:"
)
RE_PY_DEF = re.compile(
    r"^(?:async\s+)?(def|class)\s+(" + IDENT + r")\b.*:\s*$",
    re.MULTILINE,
)
RE_JSDOC_BEFORE = re.compile(
    r"/\*\*(.*?)\*/\s*(?:export\b)?",
    re.DOTALL,
)

# Whole-token match for a documented name (avoid `create` matching `create_user`).
def _name_re(name: str) -> re.Pattern:
    return re.compile(r"(?<![\w$])" + re.escape(name) + r"(?![\w$])")


class UsageError(Exception):
    """Exit-2 conditions."""


def _emit(verdict: str, reasons: Sequence[str], summary: str) -> int:
    print(verdict)
    for reason in reasons:
        print("reason: %s" % reason)
    print(summary)
    if verdict == "fail":
        return 1
    return 0


def _read(path: Path) -> Optional[str]:
    try:
        return path.read_text(encoding="utf-8")
    except (OSError, UnicodeDecodeError):
        return None


def _resolve_changed(repo: Path, changed: Optional[Sequence[str]]) -> Optional[List[Path]]:
    if changed is not None:
        paths: List[Path] = []
        for raw in changed:
            candidate = Path(raw)
            if not candidate.is_absolute():
                candidate = repo / candidate
            paths.append(candidate)
        return paths

    try:
        proc = subprocess.run(
            ["git", "-C", str(repo), "diff", "--name-only", "HEAD^"],
            capture_output=True,
            text=True,
        )
    except OSError:
        return None
    if proc.returncode != 0:
        return None
    paths = []
    for line in proc.stdout.splitlines():
        name = line.strip()
        if name:
            paths.append(repo / name)
    return paths


def _python_all(text: str) -> List[str]:
    names: List[str] = []
    for match in RE_ALL.finditer(text):
        names.extend(RE_QUOTED.findall(match.group(1)))
    return names


def _js_exports(text: str) -> List[str]:
    names: List[str] = []
    names.extend(RE_EXPORT_DECL.findall(text))
    names.extend(RE_EXPORT_DEFAULT_NAMED.findall(text))
    for block in RE_EXPORT_LIST.findall(text):
        for part in block.split(","):
            part = part.strip()
            if part.startswith("type "):
                part = part[5:].strip()
            if not part or part == "...":
                continue
            as_match = RE_EXPORT_AS.search(part)
            if as_match and as_match.group(1) not in ("type", "default"):
                names.append(as_match.group(1))
    names.extend(RE_EXPORTS_DOT.findall(text))
    for block in RE_MODULE_EXPORTS_OBJ.findall(text):
        for key in RE_OBJ_KEY.findall(block):
            names.append(key[0] or key[1])
        for ident in re.findall(r"(?:^|,)\s*(" + IDENT + r")\s*(?:,|$)", block):
            if ident not in ("true", "false", "null", "undefined"):
                names.append(ident)
    return names


def _public_exports(path: Path) -> List[str]:
    if path.suffix.lower() not in EXPORT_SUFFIXES:
        return []
    text = _read(path)
    if text is None:
        return []
    suffix = path.suffix.lower()
    if suffix in {".py", ".pyi"}:
        return _unique(_python_all(text))
    return _unique(_js_exports(text))


def _unique(names: Sequence[str]) -> List[str]:
    seen: Set[str] = set()
    out: List[str] = []
    for name in names:
        if not name or name == "default":
            continue
        if name not in seen:
            seen.add(name)
            out.append(name)
    return out


def _adjacent_documented(path: Path, name: str) -> bool:
    text = _read(path)
    if text is None:
        return False
    suffix = path.suffix.lower()
    if suffix in {".py", ".pyi"}:
        return _python_adjacent(text, name)
    return _js_adjacent(text, name)


def _python_adjacent(text: str, name: str) -> bool:
    for match in RE_PY_DEF.finditer(text):
        if match.group(2) != name:
            continue
        after = text[match.end():]
        stripped = after.lstrip()
        if stripped.startswith(('"""', "'''")):
            quote = stripped[:3]
            end = stripped.find(quote, 3)
            if end == -1:
                return False
            return bool(stripped[3:end].strip())
        return False
    # Module docstring that names the export counts as adjacent docs.
    stripped = text.lstrip()
    if stripped.startswith(('"""', "'''")):
        quote = stripped[:3]
        end = stripped.find(quote, 3)
        if end != -1 and _name_re(name).search(stripped[3:end]):
            return True
    return False


def _js_adjacent(text: str, name: str) -> bool:
    for match in re.finditer(
        r"(?:export\s+)?(?:async\s+)?(?:function|class|const|let|var|type|interface|enum)\s+"
        + re.escape(name) + r"\b",
        text,
    ):
        before = text[:match.start()]
        doc = None
        for jsdoc in RE_JSDOC_BEFORE.finditer(before):
            if jsdoc.end() == len(before.rstrip()) or before[jsdoc.end():].strip() == "":
                doc = jsdoc.group(1)
        # Nearest JSDoc immediately preceding this declaration.
        tail = before.rstrip()
        if tail.endswith("*/"):
            start = tail.rfind("/**")
            if start != -1:
                inner = tail[start + 3:-2]
                return bool(inner.strip())
        if doc and doc.strip():
            return True
    return False


def _detect_framework(repo: Path) -> Optional[str]:
    if (repo / ".vitepress").is_dir() or (repo / "docs" / ".vitepress").is_dir():
        return "vitepress"
    if (repo / "docusaurus.config.js").is_file() or (repo / "docusaurus.config.ts").is_file():
        return "docusaurus"
    if (repo / "mkdocs.yml").is_file() or (repo / "mkdocs.yaml").is_file():
        return "mkdocs"
    if (repo / ".storybook").is_dir():
        return "storybook"
    pkg = _read(repo / "package.json")
    if pkg:
        if "vitepress" in pkg:
            return "vitepress"
        if "docusaurus" in pkg or "@docusaurus/" in pkg:
            return "docusaurus"
        if "nextra" in pkg:
            return "nextra"
        if "storybook" in pkg or "@storybook/" in pkg:
            return "storybook"
    for name in ("README.md", "README", "README.rst", "README.txt"):
        if (repo / name).is_file():
            return "readme"
    return None


def _doc_roots(repo: Path, framework: Optional[str]) -> List[Path]:
    roots: List[Path] = []
    if framework == "vitepress":
        if (repo / "docs").is_dir():
            roots.append(repo / "docs")
        if (repo / ".vitepress").is_dir():
            roots.append(repo)
    elif framework == "docusaurus":
        for name in ("docs", "blog", "src/pages"):
            path = repo / name
            if path.is_dir():
                roots.append(path)
    elif framework == "nextra":
        for name in ("pages", "app", "docs"):
            path = repo / name
            if path.is_dir():
                roots.append(path)
    elif framework == "mkdocs":
        docs_dir = repo / "docs"
        for yml in (repo / "mkdocs.yml", repo / "mkdocs.yaml"):
            text = _read(yml)
            if text:
                match = re.search(r"^docs_dir:\s*(\S+)", text, re.MULTILINE)
                if match:
                    docs_dir = repo / match.group(1).strip("\"'")
        if docs_dir.is_dir():
            roots.append(docs_dir)
    elif framework == "storybook":
        roots.append(repo)
    return roots


def _iter_doc_files(repo: Path, framework: Optional[str]) -> List[Path]:
    files: List[Path] = []
    for child in repo.iterdir() if repo.is_dir() else []:
        if not child.is_file():
            continue
        lowered = child.name.lower()
        if lowered in README_NAMES or lowered in CHANGELOG_NAMES:
            files.append(child)
    for root in _doc_roots(repo, framework):
        if not root.is_dir():
            continue
        for path in root.rglob("*"):
            if not path.is_file():
                continue
            suffix = path.suffix.lower()
            name = path.name.lower()
            if suffix in DOC_SUFFIXES or name.endswith(".stories.ts") or name.endswith(".stories.js") or ".stories." in name:
                if "node_modules" in path.parts or ".git" in path.parts:
                    continue
                files.append(path)
    # Dedup while preserving order.
    seen: Set[Path] = set()
    out: List[Path] = []
    for path in files:
        resolved = path.resolve()
        if resolved not in seen:
            seen.add(resolved)
            out.append(path)
    return out


def _doc_corpus(repo: Path, framework: Optional[str]) -> str:
    chunks: List[str] = []
    for path in _iter_doc_files(repo, framework):
        text = _read(path)
        if text:
            chunks.append(text)
    return "\n".join(chunks)


def _is_documented(name: str, corpus: str, source: Path) -> bool:
    if corpus and _name_re(name).search(corpus):
        return True
    return _adjacent_documented(source, name)


def check(repo: Path, changed: Optional[Sequence[str]]) -> int:
    if not repo.is_dir():
        raise UsageError("repo is not a directory: %s" % repo)

    files = _resolve_changed(repo, changed)
    if files is None:
        return _emit(
            "unverifiable",
            ["changed_set_unresolved"],
            "docs-check: unverifiable (changed set could not be resolved)",
        )

    exports: List[Tuple[str, Path]] = []
    for path in files:
        if not path.is_file():
            continue
        for name in _public_exports(path):
            exports.append((name, path))

    framework = _detect_framework(repo)

    if not exports:
        return _emit(
            "unverifiable",
            ["no_public_exports"],
            "docs-check: unverifiable (no docs framework and no public exports)"
            if framework is None
            else "docs-check: unverifiable (no public exports in the changed set)",
        )

    corpus = _doc_corpus(repo, framework)
    missing: List[str] = []
    for name, source in exports:
        if not _is_documented(name, corpus, source):
            missing.append(name)

    if missing:
        reasons = ["undocumented_export"]
        for name in missing:
            reasons.append(name)
        return _emit(
            "fail",
            reasons,
            "docs-check: fail (%s has no matching documented symbol)"
            % ", ".join(missing),
        )

    return _emit(
        "pass",
        [],
        "docs-check: pass (%d export(s) documented)" % len(exports),
    )


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__)
    sub = parser.add_subparsers(dest="action", required=True)
    p = sub.add_parser("check", help="diff public exports against documented symbols")
    p.add_argument("--repo", "--project", dest="repo", type=Path, default=Path("."))
    p.add_argument("--changed", nargs="+", default=None)
    return parser


def main(argv: Optional[List[str]] = None) -> int:
    parser = build_parser()
    try:
        args = parser.parse_args(argv)
    except SystemExit as exc:
        code = exc.code
        return int(code) if isinstance(code, int) else 2
    try:
        return check(args.repo, args.changed)
    except UsageError as exc:
        print(str(exc), file=sys.stderr)
        return 2


if __name__ == "__main__":
    sys.exit(main())
