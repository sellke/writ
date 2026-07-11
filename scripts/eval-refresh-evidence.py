#!/usr/bin/env python3
"""Fixture-driven scenarios for the evidence-bound /refresh-command learning loop.

Emits PASS/FAIL TSV lines consumed by scripts/eval.sh check_refresh_evidence.
Modeled on scripts/eval-phase-knowledge.py: synthetic refresh-log entries built
in-memory (no dependency on the live .writ/refresh-log.md) are run through a
deterministic validator so CI never depends on real log contents.

The validator enforces the evidence contract (spec 2026-07-10-evidence-bound-
refresh-command):

  - a well-formed evidenced applied amendment passes
  - an applied amendment with no transcript citation fails ("no evidence")
  - an applied amendment missing the observable signal fails
  - an entry embedding a verbatim private transcript body / chain-of-thought
    fails the Prime Directive privacy guard
  - a reviewed-with-zero-amendments entry is exempt (passes)
  - a rejected-for-lacking-evidence entry is a valid record (passes)
  - a rejected entry with no reason token fails
  - a live entry dated before LEARNING_CONTRACT_SINCE is grandfathered (passes)
  - a cited transcript file absent on disk still passes on the ID citation

Story 3 appends the Tier 2 structural + pre-merge-gate scenarios below the base
scenarios; both share this single fixture script and the single registered
`refresh-evidence` check.
"""

from __future__ import annotations

import datetime as _dt
import re
import sys

# The evidence contract takes effect the day after the spec's Created date.
# Entries dated strictly before this are grandfathered and never fail.
LEARNING_CONTRACT_SINCE = "2026-07-11"

# High-traffic commands get the additional structural Tier 2 check (Story 3).
HIGH_TRAFFIC = ("create-spec", "implement-story", "ship", "refactor")

# A short observable signal is a single brief quote — never a transcript body.
MAX_SIGNAL_LEN = 200

passed = 0
failed = 0


def emit(name: str, ok: bool, detail: object = "") -> None:
    global passed, failed
    if ok:
        passed += 1
        print(f"PASS\t{name}")
    else:
        failed += 1
        safe = str(detail).replace("\n", "\\n").replace("\t", " ")
        print(f"FAIL\t{name}\t{safe}")


# ---------------------------------------------------------------------------
# Validator (the parser the fixtures exercise)
# ---------------------------------------------------------------------------

_HEADER_RE = re.compile(r"^##\s+(\d{4}-\d{2}-\d{2})\s+—\s+/(\S+)", re.MULTILINE)
_APPLIED_RE = re.compile(r"\*\*Amendments applied:\*\*\s*(\d+)\s+of\s+(\d+)")
_TRANSCRIPT_RE = re.compile(r"(?mi)^\s*[-*]?\s*Transcript:\s*(.+?)\s*$")
_SIGNAL_RE = re.compile(r"(?mi)^\s*[-*]?\s*Observable signal:\s*(.+?)\s*$")
_SECTION_RE = re.compile(r"(?mi)^\s*[-*]?\s*Affected section:\s*(.+?)\s*$")
_REASON_RE = re.compile(r"reason:\s*(no evidence|eval failed)", re.IGNORECASE)

# Markers of forbidden private content (chain-of-thought / verbatim body).
_PRIVATE_MARKERS = (
    "chain-of-thought",
    "chain of thought",
    "<thinking>",
    "</thinking>",
)


def _date_before(date_str: str, boundary: str) -> bool:
    try:
        d = _dt.date.fromisoformat(date_str)
        b = _dt.date.fromisoformat(boundary)
    except ValueError:
        return False
    return d < b


def _privacy_violation(text: str) -> str:
    """Return a reason string if the entry stores forbidden private content."""
    low = text.lower()
    for marker in _PRIVATE_MARKERS:
        if marker in low:
            return f"privacy: embeds forbidden marker '{marker}'"

    # A fenced code block that carries transcript-body JSON is a verbatim body.
    if "```" in text and re.search(r'"role"\s*:|"content"\s*:', text):
        return "privacy: embeds verbatim transcript body (fenced JSON)"

    # An observable signal must be a short quote, not a pasted body.
    for m in _SIGNAL_RE.finditer(text):
        if len(m.group(1)) > MAX_SIGNAL_LEN:
            return "privacy: observable signal too long (looks like a body, not a quote)"

    return ""


def validate_entry(text: str) -> tuple[bool, str]:
    """Validate a single refresh-log entry against the evidence contract.

    Returns (ok, reason). `reason` is empty on success.
    """
    header = _HEADER_RE.search(text)
    if not header:
        return False, "malformed: missing '## YYYY-MM-DD — /command' header"
    date_str = header.group(1)

    # Grandfather pre-contract history: never retroactively fail it.
    if _date_before(date_str, LEARNING_CONTRACT_SINCE):
        return True, ""

    # Privacy guard applies to every in-contract entry, regardless of outcome.
    priv = _privacy_violation(text)
    if priv:
        return False, priv

    applied = _APPLIED_RE.search(text)
    if not applied:
        return False, "malformed: missing '**Amendments applied:** K of M'"
    k = int(applied.group(1))

    # Validate any rejection records: each must carry a recognized reason token.
    if "**Rejected:**" in text:
        rejected_block = text.split("**Rejected:**", 1)[1]
        # Stop at the next bold field header so we only read rejection bullets.
        rejected_block = re.split(r"\n\*\*\w", rejected_block, 1)[0]
        bullets = [ln for ln in rejected_block.splitlines() if ln.lstrip().startswith(("- ", "* "))]
        if not bullets:
            return False, "rejected: section present but lists no candidates"
        for bullet in bullets:
            if not _REASON_RE.search(bullet):
                return False, "rejected: candidate missing reason token (no evidence / eval failed)"

    # No-op review is a valid, evidence-exempt outcome.
    if k == 0:
        return True, ""

    # Applied amendments must carry a complete Evidence block.
    if "**Evidence:**" not in text:
        return False, "no evidence: applied amendment lacks an Evidence block"
    if not _TRANSCRIPT_RE.search(text):
        return False, "no evidence: missing transcript citation (Transcript:)"
    if not _SIGNAL_RE.search(text):
        return False, "missing signal: no Observable signal line"
    if not _SECTION_RE.search(text):
        return False, "missing affected section: no Affected section anchor"

    return True, ""


# ---------------------------------------------------------------------------
# Fixture builders
# ---------------------------------------------------------------------------

def evidenced_entry(date: str = "2026-07-11", command: str = "create-spec") -> str:
    return (
        f"## {date} — /{command} refreshed\n\n"
        "**Signals found:** 4 total, 2 actionable\n"
        "**Amendments applied:** 1 of 2 proposed\n\n"
        "**Changes:**\n"
        "- Detect monorepo workspace root during codebase scan (Confidence: High)\n"
        "  **Evidence:**\n"
        "  - Transcript: agent-transcripts/session-uuid/session-uuid.jsonl\n"
        '  - Observable signal: "user re-ran /create-spec after the scan skipped the monorepo root"\n'
        '  - Affected section: commands/create-spec.md → "Phase 2: Codebase Scan"\n\n'
        "**Scope:** Local only\n"
        f"**Target file:** commands/{command}.md\n"
    )


def missing_citation_entry() -> str:
    return (
        "## 2026-07-11 — /create-spec refreshed\n\n"
        "**Signals found:** 3 total, 1 actionable\n"
        "**Amendments applied:** 1 of 1 proposed\n\n"
        "**Changes:**\n"
        "- Reword the scan prompt (Confidence: Medium)\n\n"
        "**Scope:** Local only\n"
        "**Target file:** commands/create-spec.md\n"
    )


def missing_signal_entry() -> str:
    return (
        "## 2026-07-11 — /create-spec refreshed\n\n"
        "**Signals found:** 3 total, 1 actionable\n"
        "**Amendments applied:** 1 of 1 proposed\n\n"
        "**Changes:**\n"
        "- Reword the scan prompt (Confidence: Medium)\n"
        "  **Evidence:**\n"
        "  - Transcript: agent-transcripts/session-uuid/session-uuid.jsonl\n"
        '  - Affected section: commands/create-spec.md → "Phase 2: Codebase Scan"\n\n'
        "**Scope:** Local only\n"
        "**Target file:** commands/create-spec.md\n"
    )


def private_body_entry() -> str:
    return (
        "## 2026-07-11 — /create-spec refreshed\n\n"
        "**Signals found:** 3 total, 1 actionable\n"
        "**Amendments applied:** 1 of 1 proposed\n\n"
        "**Changes:**\n"
        "- Fix the scan (Confidence: High)\n"
        "  **Evidence:**\n"
        "  - Transcript: agent-transcripts/session-uuid/session-uuid.jsonl\n"
        '  - Observable signal: "see transcript"\n'
        '  - Affected section: commands/create-spec.md → "Phase 2: Codebase Scan"\n\n'
        "```jsonl\n"
        '{"role": "assistant", "content": "verbatim private transcript body pasted here"}\n'
        "```\n\n"
        "**Scope:** Local only\n"
        "**Target file:** commands/create-spec.md\n"
    )


def cot_entry() -> str:
    return (
        "## 2026-07-11 — /create-spec refreshed\n\n"
        "**Signals found:** 3 total, 1 actionable\n"
        "**Amendments applied:** 1 of 1 proposed\n\n"
        "**Changes:**\n"
        "- Fix the scan (Confidence: High)\n"
        "  **Evidence:**\n"
        "  - Transcript: agent-transcripts/session-uuid/session-uuid.jsonl\n"
        '  - Observable signal: "the chain-of-thought showed the model reasoning about monorepos"\n'
        '  - Affected section: commands/create-spec.md → "Phase 2: Codebase Scan"\n\n'
        "**Scope:** Local only\n"
        "**Target file:** commands/create-spec.md\n"
    )


def long_signal_entry() -> str:
    body = "x" * (MAX_SIGNAL_LEN + 50)
    return (
        "## 2026-07-11 — /create-spec refreshed\n\n"
        "**Signals found:** 3 total, 1 actionable\n"
        "**Amendments applied:** 1 of 1 proposed\n\n"
        "**Changes:**\n"
        "- Fix the scan (Confidence: High)\n"
        "  **Evidence:**\n"
        "  - Transcript: agent-transcripts/session-uuid/session-uuid.jsonl\n"
        f'  - Observable signal: "{body}"\n'
        '  - Affected section: commands/create-spec.md → "Phase 2: Codebase Scan"\n\n'
        "**Scope:** Local only\n"
        "**Target file:** commands/create-spec.md\n"
    )


def noop_review_entry() -> str:
    return (
        "## 2026-07-11 — /create-spec reviewed — no changes\n\n"
        "**Signals found:** 1 total, 0 actionable\n"
        "**Amendments applied:** 0 of 0 proposed\n\n"
        "**Scope:** Local only\n"
        "**Target file:** —\n"
    )


def rejected_valid_entry() -> str:
    return (
        "## 2026-07-11 — /prototype refreshed\n\n"
        "**Signals found:** 3 total, 1 actionable\n"
        "**Amendments applied:** 0 of 1 proposed\n\n"
        "**Rejected:**\n"
        "- Add \"touches authentication\" escalation trigger — reason: no evidence\n\n"
        "**Scope:** Local only\n"
        "**Target file:** commands/prototype.md\n"
    )


def rejected_missing_reason_entry() -> str:
    return (
        "## 2026-07-11 — /prototype refreshed\n\n"
        "**Signals found:** 3 total, 1 actionable\n"
        "**Amendments applied:** 0 of 1 proposed\n\n"
        "**Rejected:**\n"
        "- Add an escalation trigger because it feels right\n\n"
        "**Scope:** Local only\n"
        "**Target file:** commands/prototype.md\n"
    )


def grandfathered_entry() -> str:
    return (
        "## 2026-03-15 — /ship refreshed\n\n"
        "**Source transcript:** This conversation (legacy pre-contract format)\n"
        "**Signals found:** 5 total, 4 actionable\n"
        "**Amendments applied:** 4 of 4 proposed\n\n"
        "**Changes:**\n"
        "- Auto-label fallback (Confidence: High)\n\n"
        "**Scope:** Local only\n"
        "**Target file:** commands/ship.md\n"
    )


def transcript_absent_entry() -> str:
    # Cites a path that does not exist on this machine; the ID citation stands.
    return (
        "## 2026-07-11 — /refactor refreshed\n\n"
        "**Signals found:** 2 total, 1 actionable\n"
        "**Amendments applied:** 1 of 1 proposed\n\n"
        "**Changes:**\n"
        "- Clarify the extraction step (Confidence: High)\n"
        "  **Evidence:**\n"
        "  - Transcript: agent-transcripts/does-not-exist-on-this-machine/xyz.jsonl\n"
        '  - Observable signal: "user corrected the extraction order"\n'
        '  - Affected section: commands/refactor.md → "Phase 3: Extract"\n\n'
        "**Scope:** Local only\n"
        "**Target file:** commands/refactor.md\n"
    )


# ---------------------------------------------------------------------------
# Base scenarios (Story 2)
# ---------------------------------------------------------------------------

def run_base_scenarios() -> None:
    ok, reason = validate_entry(evidenced_entry())
    emit("evidenced-entry-passes", ok, reason)

    ok, reason = validate_entry(missing_citation_entry())
    emit("missing-citation-fails", (not ok) and "no evidence" in reason, reason)

    ok, reason = validate_entry(missing_signal_entry())
    emit("missing-signal-fails", (not ok) and "signal" in reason, reason)

    ok, reason = validate_entry(private_body_entry())
    emit("private-body-fails", (not ok) and "privacy" in reason, reason)

    ok, reason = validate_entry(cot_entry())
    emit("chain-of-thought-fails", (not ok) and "privacy" in reason, reason)

    ok, reason = validate_entry(long_signal_entry())
    emit("long-signal-privacy-fails", (not ok) and "privacy" in reason, reason)

    ok, reason = validate_entry(noop_review_entry())
    emit("reviewed-no-amendments-exempt", ok, reason)

    ok, reason = validate_entry(rejected_valid_entry())
    emit("rejected-lacking-evidence-is-valid-record", ok, reason)

    ok, reason = validate_entry(rejected_missing_reason_entry())
    emit("rejected-missing-reason-fails", (not ok) and "rejected" in reason, reason)

    ok, reason = validate_entry(grandfathered_entry())
    emit("pre-contract-entry-grandfathered", ok, reason)

    ok, reason = validate_entry(transcript_absent_entry())
    emit("transcript-absent-passes-on-id", ok, reason)


def main() -> int:
    run_base_scenarios()
    return 0 if failed == 0 else 1


if __name__ == "__main__":
    sys.exit(main())
