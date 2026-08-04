#!/usr/bin/env python3
"""Real-repo readiness probe for the post-merge archival hook's live
dogfood evidence (Story 4, Task 4.5 of `2026-08-04-post-merge-archival-hook`).

Unlike `scripts/eval-archive-dogfood.py` (Story 6's post-sweep regression
guard, which runs *after* its real sweep already happened and hard-fails if
`.writ/specs/archive/` is empty), this story's motivating live event — a real
merge + `/release` run that archives `2026-08-04-spec-lifecycle-archival` and
this spec itself (`2026-08-04-post-merge-archival-hook`) via the hook — has
NOT happened yet as of this writing. AC5 of `story-4-dogfood-and-verify.md`
explicitly cannot be satisfied within this implementation session.

This script must therefore **never hard-fail by default**. Its job today is
only to report how many of the two motivating specs have been archived via a
genuine hook-triggered commit so far (0, until the real merges + `/release`
runs happen), and to always exit 0 in that "not yet occurred" state — never a
footgun that fails every future contributor's `eval.sh` run in the meantime.

**Anti-false-positive guard:** a spec folder simply *existing* under
`.writ/specs/archive/<name>/` is not evidence of a hook-triggered archival —
a manual `/status --archive` move produces the exact same directory shape.
The only trustworthy signal is a commit whose message matches the hook's
exact pattern from `commands/release.md` Step 1.3c:
`chore(archive): auto-archive <spec> via PR #<n>`. This script greps
committed history for that literal pattern per motivating spec, not
directory existence, so an uncommitted or manually-committed move (e.g. the
`2026-08-04-spec-lifecycle-archival` move that pre-dates this story, staged
via `/status --archive` before Story 3/4 existed) is correctly never counted.

**How/when to register this in `scripts/eval.sh`'s `CHECKS=()` array:**
Once both `MOTIVATING_SPECS` below show a real hook-triggered commit (i.e.
this script reports "2 of 2"), flip `main()` to `return 0 if archived_count
== len(MOTIVATING_SPECS) else 1`, add `post-merge-dogfood` to `CHECKS=()`
immediately after `post-merge-archival`, and add a `check_post_merge_dogfood()`
function mirroring `check_archive_dogfood()`'s structure (scenario-output TSV
loop only — this script has no prose to pin, unlike `check_post_merge_archival`).
Until then, leave it unregistered so it never blocks `eval.sh --check=all`
runs before the live event it is designed to detect has occurred.
"""

from __future__ import annotations

import subprocess
import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parent.parent

# The two specs this story's motivating gap names explicitly (AC5): once each
# reaches Complete and merges, the next `/release` run should archive it via
# the hook — closing the exact gap `/status --archive` reminders used to fill.
MOTIVATING_SPECS = (
    "2026-08-04-spec-lifecycle-archival",
    "2026-08-04-post-merge-archival-hook",
)


def hook_triggered_commit_exists(spec_name: str) -> bool:
    """True only if committed history contains a commit whose message
    matches the hook's exact hard-coded pattern from `commands/release.md`
    Step 1.3c: `chore(archive): auto-archive <spec> via PR #<n>`. A manual
    `/status --archive` move (delete + add, or an ordinary commit message)
    does not match and is correctly never counted."""
    pattern = f"chore(archive): auto-archive {spec_name} via PR #"
    proc = subprocess.run(
        ["git", "log", "--all", "--fixed-strings", "--grep", pattern, "--oneline"],
        cwd=PROJECT_ROOT,
        capture_output=True,
        text=True,
    )
    return bool(proc.stdout.strip())


def main() -> int:
    archived_count = 0
    for spec_name in MOTIVATING_SPECS:
        confirmed = hook_triggered_commit_exists(spec_name)
        if confirmed:
            archived_count += 1
        status = "hook-archived" if confirmed else "not-yet-hook-archived"
        print(f"INFO\t{spec_name}\t{status}")

    print(
        f"INFO\tsummary\t{archived_count} of {len(MOTIVATING_SPECS)} motivating specs "
        "archived via the hook so far"
    )

    # Deliberately always 0 today (see module docstring's registration note)
    # — this script is a readiness probe, not yet a gate.
    return 0


if __name__ == "__main__":
    sys.exit(main())
