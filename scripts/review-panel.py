#!/usr/bin/env python3
"""Cross-family review panel helper (spec `2026-10-01-cross-family-review-panel`).

The panel is additive: the session's Gate 3 agent and `review-override.py`
decide exactly as before, and a finding raised by two or more vendors adds a
block. This script never spawns a model and never touches the network; the
orchestrator spawns, this script owns the config contract, the vendor table,
the matching rule, and the verdict.

Subcommands:
  status --repo . --origin "<model>" [--platform cursor|claude-code|codex|openclaw] [--json]
                      Resolve `- **Review Panel:** <slug>[, <slug>…]` in
                      `.writ/config.md` against the session vendor and the
                      platform: which reviewers are kept, which are dropped
                      (`same_vendor`, `unknown_vendor`, `duplicate_slug`,
                      `over_cap`) and why the panel is off or skipped.

Prints one verdict line first (`pass` / `unverifiable`), then `reason:`,
`reviewer:` and `dropped:` lines, and a `review-panel:` summary line last.
`--json` prints one object instead.

Exit 0: ran (any verdict above).
Exit 2: usage (missing `--origin`, unreadable repo or config, unknown platform).
"""

from __future__ import annotations

import argparse
import json
import os
import re
import sys
from pathlib import Path
from typing import Dict, List, NamedTuple, Optional, Sequence, Tuple


CONFIG_LINE = re.compile(r"^- \*\*Review Panel:\*\*[ \t]*(.*)$",
                         re.MULTILINE | re.IGNORECASE)
DISABLED_VALUE = "none"
MAX_REVIEWERS = 3  # Cursor runs 4 concurrent Tasks, one of them the primary.

# The only vendor knowledge Writ holds. Slug prefixes are matched literally,
# longest first; adding a vendor is one entry here plus a test.
SLUG_PREFIXES: Tuple[Tuple[str, str], ...] = (
    ("cursor-grok-", "xai"),
    ("composer-", "cursor"),
    ("claude-", "anthropic"),
    ("gemini-", "google"),
    ("grok-", "xai"),
    ("muse-", "meta"),
    ("gpt-", "openai"),
)
O_SERIES = re.compile(r"^o[1-9]\d*(?:-|$)")
ORIGIN_WORDS: Dict[str, str] = {
    "claude": "anthropic",
    "gpt": "openai",
    "grok": "xai",
    "gemini": "google",
    "composer": "cursor",
    "muse": "meta",
}
O_SERIES_WORD = re.compile(r"^o[1-9]\d*$")

PLATFORMS = ("cursor", "claude-code", "codex", "openclaw")
NO_CROSS_VENDOR_PLATFORMS = frozenset({"claude-code", "codex"})


class UsageError(Exception):
    """Exit-2 conditions."""


def slug_vendor(slug: str) -> Optional[str]:
    """Vendor for a Cursor model slug, or None when no table row matches."""
    for prefix, vendor in sorted(SLUG_PREFIXES, key=lambda row: -len(row[0])):
        if slug.startswith(prefix):
            return vendor
    if O_SERIES.match(slug):
        return "openai"
    return None


def origin_vendor(origin: str) -> Optional[str]:
    """Vendor for the harness-reported origin model name, by case-insensitive
    word match. None when no word matches or words name two vendors."""
    found = set()
    for word in re.split(r"[^a-z0-9]+", origin.lower()):
        if word in ORIGIN_WORDS:
            found.add(ORIGIN_WORDS[word])
        elif O_SERIES_WORD.match(word):
            found.add("openai")
    if len(found) == 1:
        return next(iter(found))
    return None


def config_value(repo: Path) -> Optional[str]:
    """The raw Review Panel value (first matching line); None when the file
    or the line is absent. An existing but unreadable file is a usage error."""
    config = repo / ".writ" / "config.md"
    if not config.exists():
        return None
    try:
        text = config.read_text(encoding="utf-8")
    except (OSError, UnicodeDecodeError) as exc:
        raise UsageError("cannot read %s (%s)" % (config, exc))
    match = CONFIG_LINE.search(text)
    if not match:
        return None
    return match.group(1).strip()


class Panel(NamedTuple):
    verdict: str
    reasons: List[str]
    reviewers: List[Tuple[str, str]]  # (slug, vendor), config order
    dropped: List[Tuple[str, str]]    # (slug, reason), config order
    session_vendor: Optional[str]
    summary: str


def _drop_list(dropped: Sequence[Tuple[str, str]]) -> str:
    return ", ".join("%s %s" % pair for pair in dropped)


def resolve(repo: Path, origin: str, platform: Optional[str]) -> Panel:
    """Apply the config line, platform, and vendor table, in that order."""
    session = origin_vendor(origin)

    def off(reason: str, kind: str, summary: Optional[str] = None,
            dropped: Sequence[Tuple[str, str]] = ()) -> Panel:
        return Panel("unverifiable", [reason], [], list(dropped), session,
                     summary or "review-panel: %s — %s" % (kind, reason))

    value = config_value(repo)
    if value is None:
        return off("no_config_line", "off")
    if value.lower() == DISABLED_VALUE:
        return off("panel_disabled", "off")
    slugs = [s.strip() for s in value.split(",") if s.strip()]
    if not slugs:
        return off("malformed_config", "skipped")
    if platform in NO_CROSS_VENDOR_PLATFORMS:
        return off("platform_cannot_spawn_other_vendors", "skipped",
                   "review-panel: skipped — platform cannot spawn other vendors")
    if session is None:
        return off("unknown_session_vendor", "skipped")

    kept: List[Tuple[str, str]] = []
    dropped: List[Tuple[str, str]] = []
    seen = set()
    for slug in slugs:
        vendor = slug_vendor(slug)
        if slug in seen:
            dropped.append((slug, "duplicate_slug"))
        elif vendor is None:
            dropped.append((slug, "unknown_vendor"))
        elif vendor == session:
            dropped.append((slug, "same_vendor"))
        elif len(kept) >= MAX_REVIEWERS:
            dropped.append((slug, "over_cap"))
        else:
            kept.append((slug, vendor))
        seen.add(slug)

    if not kept:
        return off("no_other_vendor", "skipped",
                   "review-panel: skipped — no_other_vendor (dropped: %s)"
                   % _drop_list(dropped), dropped)
    reasons = ["unverified_platform"] if platform == "openclaw" else []
    noun = "reviewer" if len(kept) == 1 else "reviewers"
    summary = "review-panel: pass — %d %s (%s)" % (
        len(kept), noun, ", ".join("%s %s" % pair for pair in kept))
    return Panel("pass", reasons, kept, dropped, session, summary)


def cmd_status(args: argparse.Namespace) -> int:
    repo = Path(args.repo)
    if not repo.is_dir() or not os.access(str(repo), os.R_OK | os.X_OK):
        raise UsageError("repo is not a readable directory: %s" % repo)
    panel = resolve(repo, args.origin, args.platform)
    if args.json:
        print(json.dumps({
            "verdict": panel.verdict,
            "reasons": panel.reasons,
            "reviewers": [{"slug": s, "vendor": v} for s, v in panel.reviewers],
            "dropped": [{"slug": s, "reason": r} for s, r in panel.dropped],
            "session_vendor": panel.session_vendor,
            "platform": args.platform,
            "summary": panel.summary,
        }, sort_keys=True))
        return 0
    print(panel.verdict)
    for reason in panel.reasons:
        print("reason: %s" % reason)
    for slug, vendor in panel.reviewers:
        print("reviewer: %s %s" % (slug, vendor))
    for slug, reason in panel.dropped:
        print("dropped: %s %s" % (slug, reason))
    print(panel.summary)
    return 0


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    sub = parser.add_subparsers(dest="action", required=True)

    p = sub.add_parser("status", help="resolve the Review Panel config line")
    p.add_argument("--repo", default=".")
    p.add_argument("--origin", required=True,
                   help="origin model name captured at command entry")
    p.add_argument("--platform", choices=PLATFORMS, default=None)
    p.add_argument("--json", action="store_true")
    p.set_defaults(func=cmd_status)
    return parser


def main(argv: Optional[List[str]] = None) -> int:
    parser = build_parser()
    try:
        args = parser.parse_args(argv)
    except SystemExit as exc:
        code = exc.code
        return int(code) if isinstance(code, int) else 2
    try:
        return args.func(args)
    except UsageError as exc:
        print("review-panel: usage — %s" % exc, file=sys.stderr)
        return 2


if __name__ == "__main__":
    sys.exit(main())
