#!/usr/bin/env python3
"""Story 3 measurement sweep: `fetched_context` `bytes.total` across every
`user-stories/story-*.md` file under `.writ/specs/`.

Committed rather than a throwaway one-off (Architecture Check Finding 8):
the Finding-2 heading-mismatch bug (`extract_markdown_section()`'s exact
match against `## \U0001F3AF Experience Design` breaks when the heading
carries trailing text, e.g. a parenthetical) means this sweep undercounts
an unknown subset of the corpus today. Once that bug is fixed elsewhere,
someone needs to re-run this exact script against corrected measurements
to confirm `FETCHED_CONTEXT_BUDGET_BYTES` still holds — a one-off shell
loop would not survive to that day.

Usage: python3 scripts/sweep-story-context-bytes.py [--specs-dir PATH]

Degrades exactly like `eval-leanness.py`'s `assembler_bytes_for_story()`:
a malformed story file, a crashed subprocess, or a timeout contributes 0
bytes and is recorded in the report, never aborts the sweep.
"""

from __future__ import annotations

import argparse
import glob
import json
import os
import re
import statistics
import subprocess
import sys

STORY_CONTEXT_HELPER = os.path.join(os.path.dirname(__file__), "story-context.py")

# The exact heading `resolve_table_category()`/`resolve_experience()` match
# against, per story-context.py. A story is flagged as "heading mismatch
# suspected" when its spec.md carries this heading with trailing text after
# it (e.g. `## 🎯 Experience Design (CLI / CI — no user-facing UI)`) — the
# exact-match contract silently treats that as "heading not found" rather
# than resolving the section, which can undercount error_map_rows and
# shadow_paths (via the technical-spec-absent fallback) as well as
# experience itself. Flagging is independent of whether this story's own
# hints reference the category — a later reader re-running this sweep after
# the bug is fixed needs to see every affected spec, not just the ones that
# happened to reference Experience in this snapshot.
EXPERIENCE_HEADING_PREFIX_RE = re.compile(r"^##\s*\U0001F3AF\s*Experience Design(.*)$")


def find_story_files(specs_dir: str) -> list[str]:
    pattern = os.path.join(specs_dir, "*", "user-stories", "story-*.md")
    return sorted(glob.glob(pattern))


def assembler_bytes(story_path: str) -> tuple[int, list[str], str | None]:
    """(bytes_total, warnings, degrade_reason). degrade_reason is None on a
    normal run; otherwise names why this story contributed 0 without a
    normal payload (subprocess failure, non-zero exit, unparseable stdout)
    — mirrors `assembler_bytes_for_story()`'s degrade-to-0 posture rather
    than reinventing it, but keeps the reason for the report instead of
    silently discarding it."""
    try:
        proc = subprocess.run(
            [sys.executable, STORY_CONTEXT_HELPER, "assemble", "--story", story_path],
            capture_output=True, text=True, timeout=30,
        )
    except (OSError, subprocess.SubprocessError) as exc:
        return 0, [], f"subprocess failed: {exc}"
    if proc.returncode != 0:
        return 0, [], f"non-zero exit {proc.returncode}"
    try:
        payload = json.loads(proc.stdout or "{}")
    except json.JSONDecodeError:
        return 0, [], "unparseable stdout"
    total = payload.get("bytes", {}).get("total")
    warnings = payload.get("warnings", [])
    return (total if isinstance(total, int) else 0), warnings, None


def heading_mismatch_suspected(story_path: str) -> bool:
    spec_path = os.path.join(os.path.dirname(os.path.dirname(story_path)), "spec.md")
    try:
        with open(spec_path, encoding="utf-8") as handle:
            text = handle.read()
    except OSError:
        return False
    for line in text.splitlines():
        match = EXPERIENCE_HEADING_PREFIX_RE.match(line.strip())
        if match and match.group(1).strip():
            return True
    return False


def percentile(data: list[int], pct: float) -> float:
    if not data:
        return 0.0
    k = (len(data) - 1) * pct
    f, c = int(k), min(int(k) + 1, len(data) - 1)
    if f == c:
        return float(data[f])
    return data[f] + (data[c] - data[f]) * (k - f)


def build_report(story_files: list[str], repo_root: str) -> dict:
    results = []
    for path in story_files:
        total, warnings, degrade_reason = assembler_bytes(path)
        results.append({
            "story": os.path.relpath(path, repo_root),
            "bytes_total": total,
            "warning_count": len(warnings),
            "heading_mismatch_suspected": heading_mismatch_suspected(path),
            "degrade_reason": degrade_reason,
        })

    totals_sorted = sorted(r["bytes_total"] for r in results)
    n = len(totals_sorted)
    affected = [r for r in results if r["heading_mismatch_suspected"]]
    degraded = [r for r in results if r["degrade_reason"]]

    return {
        "story_count": n,
        "min": totals_sorted[0] if n else 0,
        "max": totals_sorted[-1] if n else 0,
        "median": statistics.median(totals_sorted) if n else 0,
        "p90": percentile(totals_sorted, 0.90),
        "p95": percentile(totals_sorted, 0.95),
        "p99": percentile(totals_sorted, 0.99),
        "heading_mismatch_suspected_count": len(affected),
        "heading_mismatch_suspected_stories": [r["story"] for r in affected],
        "degraded_count": len(degraded),
        "degraded_stories": [{"story": r["story"], "reason": r["degrade_reason"]} for r in degraded],
        "top10_by_bytes": sorted(results, key=lambda r: r["bytes_total"], reverse=True)[:10],
        "results": results,
    }


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--specs-dir", default=None, help="Override .writ/specs/ location.")
    args = parser.parse_args(argv)

    repo_root = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
    specs_dir = args.specs_dir or os.path.join(repo_root, ".writ", "specs")

    story_files = find_story_files(specs_dir)
    report = build_report(story_files, repo_root)
    json.dump(report, sys.stdout, indent=2)
    sys.stdout.write("\n")
    return 0


if __name__ == "__main__":
    sys.exit(main())
