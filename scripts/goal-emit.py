#!/usr/bin/env python3
"""Goal Card emit (Story 1 of
`2026-09-09-phase11-stage4-goal-emit`).

Writes paste-ready GOAL.md / VERIFY.md from a Goal Card and
schema-checks an emit directory. Does not call an LLM API. Does
not register a /goal hook. Does not decide accept / reject /
modify-spec.

Subcommands:
  emit --card PATH [--out DIR]
  check --card PATH [--out DIR]

Prints one verdict line (`pass` / `fail` / `unverifiable`), optional
`reason:` lines, then a summary line last. Successful emit prints
the pinned /goal invoke text after the summary.

Exit 0: ran, no blocking helper defect (`pass` or `unverifiable`).
Exit 1: `fail`.
Exit 2: usage.
"""

from __future__ import annotations

import argparse
import re
import sys
from pathlib import Path
from typing import List, Optional, Sequence, Tuple


ADR_SENTENCE = (
    "No `--recommend` command merges, opens PRs, or releases. "
    "Production remains a human decision."
)
ADR_PLAIN = (
    "No --recommend command merges, opens PRs, or releases. "
    "Production remains a human decision."
)
INVOKE = """\
/goal Treat this stop as acceptable when ANY of the following is true — do not
collapse these into "the checker passed":
(a) `python3 scripts/exit-criteria.py check --command implement-phase --state .writ/state/phase-execution-{timestamp}.json` exits 0 (verdict: met);
(b) the run is currently paused awaiting a retained AskQuestion — for example the
    Step 2.3 execute/edit/abort confirmation — regardless of whether the checker
    has been invoked yet; this state is met on its own;
(c) the checker exits 2 (verdict: impossible) — a tripped loop bound, an
    unresolved challenge_required, or a phase-state/git mismatch.
If none of these hold, the condition is not-met: continue the run rather than
stopping, and never treat a pause as something to route around."""
DONE_WHEN_COUNT = "count DONE WHEN lines on the card"
LOOP_RE = re.compile(r"^>\s*\*\*loop:\*\*\s*(yes|no)\s*$", re.IGNORECASE | re.MULTILINE)
HEADING_RE = re.compile(r"^##\s+(.+?)\s*$", re.MULTILINE)
TITLE_RE = re.compile(r"^#\s+(.+?)\s*$", re.MULTILINE)
SPEC_REF_RE = re.compile(r"(?:\*\*)?spec_ref(?:\*\*)?:\s*(.+)", re.IGNORECASE)


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


def _has_adr(text: str) -> bool:
    return ADR_PLAIN in text.replace("`", "")


def _read_text(path: Path) -> Optional[str]:
    try:
        return path.read_text(encoding="utf-8")
    except (OSError, UnicodeDecodeError):
        return None


def _section(text: str, heading: str) -> Optional[str]:
    matches = list(HEADING_RE.finditer(text))
    for index, match in enumerate(matches):
        if match.group(1).strip().upper() != heading.upper():
            continue
        start = match.end()
        end = matches[index + 1].start() if index + 1 < len(matches) else len(text)
        return text[start:end].strip()
    return None


def _title(text: str) -> str:
    match = TITLE_RE.search(text)
    if match is None:
        return ""
    return match.group(1).strip()


def _loop_value(text: str) -> Optional[str]:
    match = LOOP_RE.search(text)
    if match is None:
        return None
    return match.group(1).lower()


def _spec_md_exists(text: str, repo: Path) -> bool:
    match = SPEC_REF_RE.search(text)
    if match is None:
        return False
    remainder = match.group(1)
    for token in re.findall(r"[^\s]+", remainder):
        cleaned = token.strip("_,`'\"()")
        if cleaned.endswith("."):
            cleaned = cleaned[:-1]
        if not cleaned.endswith("spec.md"):
            continue
        candidate = Path(cleaned)
        if not candidate.is_absolute():
            candidate = repo / candidate
        if candidate.is_file():
            return True
    return False


def _parse_card(text: str) -> Tuple[Optional[str], Optional[str]]:
    loop = _loop_value(text)
    if loop is None:
        return None, "malformed_card"
    if loop == "no":
        return "no", None
    required = ("OBJECTIVE", "DONE WHEN", "STOP-CAPS")
    for heading in required:
        body = _section(text, heading)
        if body is None or body == "":
            return None, "malformed_card"
    return "yes", None


def _out_dir(out: Optional[Path], repo: Path, card: Path) -> Path:
    if out is not None:
        return out
    return repo / ".writ" / "goals" / card.stem


def _goal_md(text: str) -> str:
    objective = _section(text, "OBJECTIVE") or ""
    done_when = _section(text, "DONE WHEN") or ""
    stop_caps = _section(text, "STOP-CAPS") or ""
    return (
        "# %s\n\n"
        "## OBJECTIVE\n\n%s\n\n"
        "## DONE WHEN\n\n%s\n\n"
        "## STOP-CAPS\n\n%s\n\n"
        "%s\n\n"
        "```\n%s\n```\n"
    ) % (_title(text), objective, done_when, stop_caps, ADR_SENTENCE, INVOKE)


def _verify_md(text: str, repo: Path) -> str:
    parts: List[str] = []
    quality = _section(text, "QUALITY")
    if quality:
        parts.append("## QUALITY\n\n%s" % quality)
    if _spec_md_exists(text, repo):
        how = (
            "How to check DONE WHEN: run `python3 scripts/exit-criteria.py` "
            "against the spec named by spec_ref."
        )
    else:
        how = "How to check DONE WHEN: %s." % DONE_WHEN_COUNT
    parts.append(how)
    parts.append(ADR_SENTENCE)
    return "\n\n".join(parts) + "\n"


def _load_card(card: Optional[Path]) -> Tuple[Optional[Path], Optional[str], Optional[str]]:
    if card is None:
        return None, None, "missing_card"
    raw = _read_text(card)
    if raw is None:
        return card, None, "missing_card"
    return card, raw, None


def emit_cmd(card: Optional[Path], out: Optional[Path], repo: Path) -> int:
    path, raw, unread = _load_card(card)
    if unread:
        return _emit("unverifiable", [unread],
                     "goal-emit: unverifiable (missing_card)")
    assert path is not None and raw is not None
    loop, malformed = _parse_card(raw)
    if malformed:
        return _emit("fail", [malformed],
                     "goal-emit: fail (malformed_card)")
    if loop == "no":
        return _emit("unverifiable", ["loop_no"],
                     "goal-emit: unverifiable (loop_no)")
    dest = _out_dir(out, repo, path)
    dest.mkdir(parents=True, exist_ok=True)
    (dest / "GOAL.md").write_text(_goal_md(raw), encoding="utf-8")
    (dest / "VERIFY.md").write_text(_verify_md(raw, repo), encoding="utf-8")
    code = _emit("pass", [], "goal-emit: pass (GOAL.md and VERIFY.md)")
    print(INVOKE)
    return code


def check_cmd(card: Optional[Path], out: Optional[Path], repo: Path) -> int:
    path, raw, unread = _load_card(card)
    if unread:
        return _emit("unverifiable", [unread],
                     "goal-emit: unverifiable (missing_card)")
    assert path is not None and raw is not None
    loop, malformed = _parse_card(raw)
    if malformed:
        return _emit("fail", [malformed],
                     "goal-emit: fail (malformed_card)")
    if loop == "no":
        return _emit("unverifiable", ["loop_no"],
                     "goal-emit: unverifiable (loop_no)")
    dest = _out_dir(out, repo, path)
    goal_path = dest / "GOAL.md"
    verify_path = dest / "VERIFY.md"
    goal = _read_text(goal_path)
    verify = _read_text(verify_path)
    if goal is None or verify is None:
        return _emit("fail", ["missing_boundary"],
                     "goal-emit: fail (missing_boundary)")
    if not _has_adr(goal) or not _has_adr(verify):
        return _emit("fail", ["missing_boundary"],
                     "goal-emit: fail (missing_boundary)")
    return _emit("pass", [], "goal-emit: pass (GOAL.md and VERIFY.md)")


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__)
    sub = parser.add_subparsers(dest="action", required=True)
    for name, help_text in (
        ("emit", "write GOAL.md and VERIFY.md from a Goal Card"),
        ("check", "schema-check a Goal Card and emit directory"),
    ):
        p = sub.add_parser(name, help=help_text)
        p.add_argument("--card", type=Path, default=None)
        p.add_argument("--out", type=Path, default=None)
        p.add_argument("--repo", "--project", dest="repo", type=Path, default=Path("."))
    return parser


def main(argv: Optional[List[str]] = None) -> int:
    parser = build_parser()
    try:
        args = parser.parse_args(argv)
    except SystemExit as exc:
        code = exc.code
        return int(code) if isinstance(code, int) else 2
    action = getattr(args, "action", None)
    if action not in ("emit", "check"):
        return 2
    if action == "emit":
        return emit_cmd(args.card, args.out, args.repo)
    return check_cmd(args.card, args.out, args.repo)


if __name__ == "__main__":
    sys.exit(main())
