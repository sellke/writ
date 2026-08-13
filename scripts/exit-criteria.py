#!/usr/bin/env python3
"""Read-only stop-time exit-criteria checker (Story 3 of
`2026-08-12-machine-evaluable-exit-criteria`).

Given a run record written by `/implement-phase` or `/implement-spec`, answers
whether that command's declared `exit_criteria` are `met`, `unmet`, or
`impossible` — the third verdict being the safety property that lets a
stop-blocking gate coexist with Writ's retained pauses (a tripped loop bound,
an unresolved `challenge_required`, a criterion recorded unachievable, or a
state/git mismatch). See `.writ/specs/2026-08-12-machine-evaluable-exit-criteria/`
for the full contract this implements, and
`.writ/docs/exit-criteria-classification.md` for the per-criterion bucket
this module implements against — criterion by criterion, no more and no less.

This module is READ-ONLY. It never writes a file, and every git call it makes
is one of the read-only subcommand families (`rev-parse`, `branch`, `log`,
`merge-base`) — never anything that mutates the working tree or refs.

Subcommand:
  check --command {implement-phase,implement-spec} [--state PATH] [--spec DIR]
        [--repo .] [--classification PATH]

Prints one JSON object to stdout. Exit codes: 0 met, 1 unmet, 2 impossible.
"""

from __future__ import annotations

import argparse
import importlib.util
import json
import re
import subprocess
import sys
from datetime import datetime
from pathlib import Path
from typing import Any, Callable


SCHEMA = "exit-criteria-check-v1"

# --- Criterion vocabulary -------------------------------------------------
#
# Dotted string ids, matching `.writ/docs/exit-criteria-classification.md`
# and technical-spec.md's CLI Surface worked example -- NOT the bare integers
# in spec.md's Verdict Contract example, which is stale relative to the other
# two documents (Gate 0 architecture review, finding 5).

CRITERIA_BY_COMMAND: dict[str, tuple[str, ...]] = {
    "implement-phase": (
        "implement-phase.c1", "implement-phase.c2",
        "implement-phase.c3", "implement-phase.c4",
    ),
    "implement-spec": (
        "implement-spec.c1", "implement-spec.c2", "implement-spec.c3",
    ),
}

# Verbatim criterion text, copied from each command's `exit_criteria:`
# frontmatter list. Business Rule 4 ("prose and predicate are bound") wants
# each predicate to cite the text it evaluates -- these constants are that
# citation, and Story 4's `require_literal` binds them back to the command
# files so transcription drift is caught by the suite rather than a reader.
#
# Each value is a single-line string literal (not split across source lines)
# so a plain `grep -F '<the sentence>' scripts/exit-criteria.py` finds it
# verbatim. A multi-line-concatenated fragment produces the same runtime
# value but is invisible to a single-line grep -- Story 4's `require_literal`
# bindings need the former (Gate 0 review finding).
CRITERION_TEXT: dict[str, str] = {
    "implement-phase.c1": "every spec resolved from the phase reached merged, quarantined, skipped_blocked, or closed_not_implemented in .writ/state/phase-execution-*.json, and failed work exists only on writ/quarantine/<spec-id> branches",
    "implement-phase.c2": "each merged spec folder contains a populated uat-plan.md generated after that spec was implemented",
    "implement-phase.c3": "each machine-checkable roadmap exit criterion is recorded pass or fail with its evidence, and human-judgment criteria are handed off rather than self-certified",
    "implement-phase.c4": "the phase report ends in exactly one of COMPLETE, IMPLEMENTED pending human validation, or PARTIALLY COMPLETE",
    "implement-spec.c1": "scripts/story-deps.py validate returned status ok for the full story graph before the first story ran",
    "implement-spec.c2": "no story remains pending in .writ/state/execution-<timestamp>.json - each is complete, skipped with its blocking chain, or failed with a reason",
    "implement-spec.c3": "one typecheck plus full test suite ran after the final story, separate from the targeted per-story Gate 4 runs, and .writ/context.md was rewritten to the post-run story counts",
}

# The one criterion Story 1 classified structurally-unobservable, and the
# exact reason string both worked examples in the contract show.
UNOBSERVABLE_REASONS: dict[str, str] = {
    "implement-phase.c4": "declared unobservable: report is transcript-only",
}

PRE_STORY_2_REASON = "record predates exit-criteria instrumentation"

TERMINAL_STORY_STATUSES = {"complete", "completed", "skipped", "failed"}


class Impossible(Exception):
    """Raised anywhere the checker cannot trust its own inputs enough to
    render a met/unmet verdict. Caught either at the top level (a global
    input problem -- missing state, missing classification, a tripped Writ
    pause) or per-criterion (a single predicate's own git/read failure),
    per technical-spec.md's Error & Rescue Map."""


# --- Classification-doc parser --------------------------------------------
#
# First-class, tested code (Gate 0 finding 6): at load time this parses
# `.writ/docs/exit-criteria-classification.md`'s Bucket Table into an
# id -> bucket registry. Any criterion id this checker emits that is absent
# from the registry, or any registry id with no corresponding predicate, is
# `impossible` -- never a silent `unknown`. That silent-pass failure mode is
# the single most likely way this instrument goes wrong (spec.md Notes).

# Only matches actual table data rows (they alone start the line with `|`
# immediately followed by a backtick-quoted id); the "Bucket counts" summary
# line below the table also names ids in backticks but never starts a line
# with `|`, so it cannot be mistaken for a row.
_BUCKET_ROW_RE = re.compile(
    r"^\|\s*`([^`]+)`\s*\|\s*([^|]+?)\s*\|\s*([^|]+?)\s*\|\s*(.+?)\s*\|\s*$",
    re.MULTILINE,
)

# The Bucket Table lives under its own "## Bucket Table" heading and ends at
# the next "## " heading. The doc's closing "## Cross-Check Against Story 2's
# Field List" table ALSO has backtick-quoted, pipe-led rows (e.g.
# `terminalStatus`) that are not criterion ids -- scoping the row search to
# this section only is what keeps that table from being misread as more
# Bucket Table rows.
_BUCKET_TABLE_SECTION_RE = re.compile(
    r"^## Bucket Table\s*$(.*?)(?=^## |\Z)", re.MULTILINE | re.DOTALL,
)

KNOWN_BUCKETS = {"evaluable-now", "needs-run-record", "structurally-unobservable", "excluded"}


def _normalize_bucket(raw: str) -> str:
    """Map a Bucket Table cell's free text to one of the four canonical
    bucket names. Cells carry parenthetical detail ("evaluable-now (split:
    presence + ordering)", "structurally-unobservable (report-only)",
    "Scope: excluded") that the checker doesn't need to distinguish beyond
    the bucket itself."""
    text = raw.strip()
    low = text.lower()
    if low.startswith("scope:") and "exclud" in low:
        return "excluded"
    for bucket in ("evaluable-now", "needs-run-record", "structurally-unobservable"):
        if low.startswith(bucket):
            return bucket
    raise Impossible(f"unrecognized classification bucket text: {raw!r}")


def load_classification(path: Path) -> dict[str, str]:
    """Parse the Bucket Table into {criterion_id: bucket}. Missing doc, or a
    doc with no parseable rows, is `impossible` -- the checker cannot know
    which unknowns are legal without it (technical-spec.md Error & Rescue Map)."""
    if not path.is_file():
        raise Impossible(f"classification doc missing: {path}")
    text = path.read_text(encoding="utf-8")
    section_match = _BUCKET_TABLE_SECTION_RE.search(text)
    if not section_match:
        raise Impossible(f"no '## Bucket Table' section found in classification doc: {path}")
    section_text = section_match.group(1)
    registry: dict[str, str] = {}
    for match in _BUCKET_ROW_RE.finditer(section_text):
        criterion_id, _command, bucket_raw, _reason = match.groups()
        registry[criterion_id.strip()] = _normalize_bucket(bucket_raw)
    if not registry:
        raise Impossible(f"no criterion rows parsed from classification doc: {path}")
    return registry


# --- Result-entry helpers --------------------------------------------------

def _entry(criterion_id: str, verdict: str, *, evidence: str | None = None,
           reason: str | None = None) -> dict[str, Any]:
    result: dict[str, Any] = {"id": criterion_id, "verdict": verdict}
    if evidence is not None:
        result["evidence"] = evidence
    if reason is not None:
        result["reason"] = reason
    return result


def _rollup(criteria: list[dict[str, Any]]) -> str:
    """Rollup precedence, first match wins (technical-spec.md § Rollup):
    any `impossible` -> impossible; else any `unmet` -> unmet; else `met`.
    `unknown` never blocks -- but only criteria this module never assigns
    `unknown` to outside the two classified-legal buckets (structurally-
    unobservable, and needs-run-record with an absent pre-Story-2 field)
    ever carry that verdict, so this simple precedence is safe."""
    verdicts = {c["verdict"] for c in criteria}
    if "impossible" in verdicts:
        return "impossible"
    if "unmet" in verdicts:
        return "unmet"
    return "met"


EXIT_CODES = {"met": 0, "unmet": 1, "impossible": 2}


# --- Import shims (hyphenated filenames) -----------------------------------
#
# scripts/phase-state.py, scripts/spec-status.py, and scripts/story-deps.py
# all have filenames that cannot be `import`ed normally; each is loaded by
# path, deferred to first use, mirroring scripts/recommend-state.py's
# existing `_story_deps()` shim -- the house pattern for this exact problem.

_phase_state_module: Any = None
_spec_status_module: Any = None
_story_deps_module: Any = None


def _load_sibling(name: str, module_name: str) -> Any:
    path = Path(__file__).resolve().parent / name
    spec = importlib.util.spec_from_file_location(module_name, path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)  # type: ignore[union-attr]
    return module


def _phase_state() -> Any:
    global _phase_state_module
    if _phase_state_module is None:
        _phase_state_module = _load_sibling("phase-state.py", "phase_state_for_exit_criteria")
    return _phase_state_module


def _spec_status() -> Any:
    global _spec_status_module
    if _spec_status_module is None:
        _spec_status_module = _load_sibling("spec-status.py", "spec_status_for_exit_criteria")
    return _spec_status_module


def _story_deps_for_vacuous_check() -> Any:
    """Imported *only* for implement-spec.c2's empty-batch vacuous-pass
    guard (counting stories in the plan). Kept in its own clearly named
    function, deliberately separate from anything touching implement-spec.c1,
    because c1 must NEVER call `story-deps.py validate_graph` live -- doing
    so would prove the graph is valid *now*, not that it was validated
    *before dispatch* for *this* run (Gate 0 finding 4). c1's predicate below
    reads only the recorded `preflight` field; it does not import this
    module at all."""
    global _story_deps_module
    if _story_deps_module is None:
        _story_deps_module = _load_sibling("story-deps.py", "story_deps_for_exit_criteria")
    return _story_deps_module


# --- Git helpers (read-only subcommand families only) ----------------------

def _git(repo: Path, *args: str) -> subprocess.CompletedProcess:
    try:
        return subprocess.run(
            ["git", "-C", str(repo), *args], capture_output=True, text=True,
        )
    except FileNotFoundError as exc:
        raise Impossible(f"git is unavailable: {exc}") from exc


def _require_git_repo(repo: Path) -> None:
    if not repo.is_dir():
        raise Impossible(f"repo path does not exist: {repo}")
    proc = _git(repo, "rev-parse", "--is-inside-work-tree")
    if proc.returncode != 0 or proc.stdout.strip() != "true":
        raise Impossible(
            f"not a git repository: {repo} "
            f"({proc.stderr.strip() or 'git rev-parse failed'})"
        )


def _parse_git_date(raw: str) -> datetime:
    # `git log --format=%ai` emits e.g. "2026-08-12 15:26:49 +0000".
    return datetime.strptime(raw.strip(), "%Y-%m-%d %H:%M:%S %z")


def _first_add_timestamp(repo: Path, rel_path: str) -> datetime | None:
    """Earliest commit that added `rel_path`, following renames. `None` if
    git has never recorded an add for it (untracked, or an aborted history)."""
    proc = _git(repo, "log", "--follow", "--diff-filter=A", "--format=%ai", "--", rel_path)
    if proc.returncode != 0:
        raise Impossible(f"git log --follow failed for {rel_path}: {proc.stderr.strip()}")
    lines = [line for line in proc.stdout.splitlines() if line.strip()]
    if not lines:
        return None
    return min(_parse_git_date(line) for line in lines)


def _commit_timestamp(repo: Path, sha: str) -> datetime:
    proc = _git(repo, "log", "-1", "--format=%ai", sha)
    if proc.returncode != 0 or not proc.stdout.strip():
        raise Impossible(f"git log failed to resolve commit {sha}: {proc.stderr.strip()}")
    return _parse_git_date(proc.stdout.strip())


# --- State loading (schema + parse validation) ------------------------------

def _load_phase_state(path: Path) -> dict[str, Any]:
    if not path.is_file():
        raise Impossible(f"state file not found: {path}")
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except json.JSONDecodeError as exc:
        raise Impossible(f"state file is not valid JSON: {path} ({exc})") from exc
    if not isinstance(data, dict):
        raise Impossible(f"state file must contain a JSON object: {path}")
    if data.get("schemaVersion") != 2:
        raise Impossible(
            f"unsupported schema: expected phase-execution-v2 (schemaVersion 2), "
            f"got {data.get('schemaVersion')!r} in {path}"
        )
    if "specs" not in data or "specOrder" not in data:
        raise Impossible(
            f"state file does not match the phase-execution-v2 schema "
            f"(missing 'specs'/'specOrder'): {path}"
        )
    return data


def _load_spec_state(path: Path) -> dict[str, Any]:
    if not path.is_file():
        raise Impossible(f"state file not found: {path}")
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except json.JSONDecodeError as exc:
        raise Impossible(f"state file is not valid JSON: {path} ({exc})") from exc
    if not isinstance(data, dict):
        raise Impossible(f"state file must contain a JSON object: {path}")
    if "spec" not in data or "stories" not in data:
        raise Impossible(
            f"state file does not match the execution-<timestamp>.json schema "
            f"(missing 'spec'/'stories'): {path}"
        )
    return data


# --- The four impossible pre-pass triggers (implement-phase only) ----------
#
# These are phase-execution-v2 concepts (haltReported, challenges,
# exitCriteria[], and reconcile all live on that schema, per
# technical-spec.md's Data Contracts split) so this pre-pass runs only for
# `--command implement-phase`. Checked before any criterion predicate runs,
# because a tripped bound or an unresolved pause makes per-criterion
# verdicts irrelevant (technical-spec.md § Rollup).

def _check_impossible_pre_pass(state: dict[str, Any], state_path: Path, repo: Path) -> None:
    halt = state.get("haltReported")
    if halt:
        detail = ", ".join(f"{k}={v}" for k, v in halt.items()) if isinstance(halt, dict) else str(halt)
        raise Impossible(f"Loop bound tripped: haltReported present ({detail})")

    for challenge in state.get("challenges", []) or []:
        if challenge.get("status") == "unresolved":
            raise Impossible(
                f"Unresolved escalation: challenge {challenge.get('id')} "
                "has no resolve-challenge entry"
            )

    for criterion in state.get("exitCriteria", []) or []:
        if criterion.get("verdict") == "unachievable":
            raise Impossible(
                f"Criterion recorded unachievable: {criterion.get('id')} "
                f"-- {criterion.get('evidence')}"
            )

    ps = _phase_state()
    ns = argparse.Namespace(state=str(state_path), repo=str(repo))
    try:
        reconciled = ps.cmd_reconcile(ns)
    except ps.ContractError as exc:
        raise Impossible(f"reconcile failed: {exc.code}: {exc.summary}") from exc
    if reconciled.get("attention"):
        raise Impossible(
            "State/git mismatch: " + "; ".join(reconciled.get("mismatches", []))
        )


# --- implement-phase predicates ---------------------------------------------

def _predicate_phase_c1(state: dict[str, Any], state_path: Path, repo: Path) -> dict[str, Any]:
    """implement-phase.c1: "every spec resolved from the phase reached
    merged, quarantined, skipped_blocked, or closed_not_implemented in
    .writ/state/phase-execution-*.json, and failed work exists only on
    writ/quarantine/<spec-id> branches"

    "merged" (prose) maps to `"integrated"` (phase-state.py's actual
    SPEC_STATUSES/TERMINAL_SPEC_STATUSES vocabulary -- Gate 0 finding 1).
    Delegates spec-status counting to `cmd_progress` rather than re-reading
    the state file (technical-spec.md § Reuse); only quarantine-branch
    reachability is computed here, via git.
    """
    ps = _phase_state()
    try:
        progress = ps.cmd_progress(argparse.Namespace(state=str(state_path)))
    except ps.ContractError as exc:
        raise Impossible(f"cmd_progress failed: {exc.code}: {exc.summary}") from exc

    spec_order = state.get("specOrder") or []
    if not spec_order:
        # Shadow path: an empty spec set satisfies "every spec reached a
        # terminal status" only vacuously. Returning `met` here would pass a
        # phase that resolved to nothing.
        return _entry("implement-phase.c1", "unmet", reason="no spec resolved from the phase")

    specs = state.get("specs", {})
    non_terminal = [
        spec_id for spec_id in spec_order
        if specs.get(spec_id, {}).get("status") not in ps.TERMINAL_SPEC_STATUSES
    ]
    if non_terminal:
        return _entry(
            "implement-phase.c1", "unmet",
            reason=(
                f"{len(spec_order) - len(non_terminal)}/{len(spec_order)} specs terminal; "
                f"not yet terminal: {', '.join(non_terminal)}"
            ),
        )

    quarantine_branches = progress.get("quarantineBranches", [])
    phase_branch = state.get("phaseBranch")
    leaked = []
    for branch in quarantine_branches:
        proc = _git(repo, "merge-base", "--is-ancestor", branch, phase_branch)
        if proc.returncode == 0:
            leaked.append(branch)
    if leaked:
        return _entry(
            "implement-phase.c1", "unmet",
            reason=f"quarantined work reachable from the phase branch: {', '.join(leaked)}",
        )

    return _entry(
        "implement-phase.c1", "met",
        evidence=(
            f"{len(spec_order)}/{len(spec_order)} specs terminal; "
            f"{len(quarantine_branches)} quarantine branch(es), "
            f"0 reachable from {phase_branch}"
        ),
    )


def _is_populated_uat_plan(text: str) -> bool:
    """A populated plan carries at least one `##` section beyond its title
    and more than a trivial handful of content lines -- the same stub-vs-
    populated distinction technical-spec.md's Error & Rescue Map names for
    this exact file ("uat-plan.md present but a stub -> unmet")."""
    lines = [line for line in text.splitlines() if line.strip()]
    if len(lines) <= 2:
        return False
    has_subsection = any(line.strip().startswith("##") for line in lines[1:])
    return has_subsection and len(lines) >= 5


def _resolve_spec_dir(repo: Path, spec_id: str) -> Path | None:
    """A spec folder lives under `.writ/specs/<id>` while active, or
    `.writ/specs/archive/<id>` once archived. Either satisfies the criterion."""
    for candidate in (
        repo / ".writ" / "specs" / spec_id,
        repo / ".writ" / "specs" / "archive" / spec_id,
    ):
        if (candidate / "spec.md").is_file():
            return candidate
    return None


def _predicate_phase_c2(state: dict[str, Any], repo: Path) -> dict[str, Any]:
    """implement-phase.c2: "each merged spec folder contains a populated
    uat-plan.md generated after that spec was implemented"

    Recorded in the classification as a split entry (presence half +
    ordering half); both resolve to evaluable-now but by different
    mechanisms, so a failure in either is named rather than letting the
    presence half stand in for the whole criterion.
    """
    specs = state.get("specs", {})
    spec_order = state.get("specOrder") or []
    merged = [spec_id for spec_id in spec_order if specs.get(spec_id, {}).get("status") == "integrated"]
    if not merged:
        return _entry("implement-phase.c2", "met", evidence="no merged specs in this phase to check")

    ss = _spec_status()
    missing: list[str] = []
    stub: list[str] = []
    unordered: list[str] = []

    for spec_id in merged:
        spec_dir = _resolve_spec_dir(repo, spec_id)
        if spec_dir is None:
            missing.append(spec_id)
            continue

        # Delegate the "is this really a complete-family spec" cross-check
        # to spec-status.py rather than re-parsing spec.md ourselves
        # (technical-spec.md § Reuse).
        classification = ss.is_complete_file(spec_dir / "spec.md")
        if not classification.get("complete"):
            missing.append(f"{spec_id} (spec.md status is not complete-family)")
            continue

        plan_path = spec_dir / "uat-plan.md"
        if not plan_path.is_file():
            missing.append(spec_id)
            continue

        text = plan_path.read_text(encoding="utf-8")
        if not _is_populated_uat_plan(text):
            stub.append(spec_id)
            continue

        merge_commit = specs[spec_id].get("mergeCommit")
        if not merge_commit:
            unordered.append(f"{spec_id} (no recorded merge commit to order against)")
            continue

        rel_path = str(plan_path.relative_to(repo))
        first_add = _first_add_timestamp(repo, rel_path)
        if first_add is None:
            unordered.append(f"{spec_id} (uat-plan.md has no git history)")
            continue

        completed_at = _commit_timestamp(repo, merge_commit)
        # Strict "before": git commit timestamps carry only 1-second
        # resolution, so two events in the same second are indistinguishable
        # from simultaneous. Only a first-add strictly earlier than
        # completion is a provable ordering violation.
        if first_add < completed_at:
            unordered.append(f"{spec_id} (uat-plan.md predates its completion commit)")

    problems = []
    if missing:
        problems.append(f"lacks a populated uat-plan.md: {', '.join(missing)}")
    if stub:
        problems.append(f"uat-plan.md is a stub: {', '.join(stub)}")
    if unordered:
        problems.append(f"uat-plan.md ordering violation: {', '.join(unordered)}")
    if problems:
        return _entry("implement-phase.c2", "unmet", reason="; ".join(problems))

    return _entry(
        "implement-phase.c2", "met",
        evidence=f"{len(merged)}/{len(merged)} merged specs carry a populated, correctly ordered uat-plan.md",
    )


def _predicate_phase_c3(state: dict[str, Any]) -> dict[str, Any]:
    """implement-phase.c3: "each machine-checkable roadmap exit criterion is
    recorded pass or fail with its evidence, and human-judgment criteria are
    handed off rather than self-certified"

    needs-run-record: nothing to check before `/implement-phase` Step 4.1
    writes `exitCriteria[]`. Absent -> `unknown`, never `unmet`
    (Business Rule 2).
    """
    entries = state.get("exitCriteria")
    if not isinstance(entries, list) or not entries:
        return _entry("implement-phase.c3", "unknown", reason=PRE_STORY_2_REASON)

    bad = []
    for entry in entries:
        cls = entry.get("class")
        verdict = entry.get("verdict")
        if cls == "machine":
            if verdict not in {"pass", "fail", "unachievable"} or not entry.get("evidence"):
                bad.append(entry.get("id", "?"))
        elif cls == "human":
            if verdict != "handed_off":
                bad.append(entry.get("id", "?"))
        else:
            bad.append(entry.get("id", "?"))
    if bad:
        return _entry(
            "implement-phase.c3", "unmet",
            reason=f"exitCriteria entries not properly recorded: {', '.join(bad)}",
        )
    return _entry(
        "implement-phase.c3", "met",
        evidence=f"{len(entries)} roadmap criteria recorded in exitCriteria[]",
    )


def _predicate_phase_c4() -> dict[str, Any]:
    """implement-phase.c4: "the phase report ends in exactly one of
    COMPLETE, IMPLEMENTED pending human validation, or PARTIALLY COMPLETE"

    structurally-unobservable (report-only): the report's terminal line is
    transcript content, not a structured field. Always `unknown` with the
    exact reason both worked examples in the contract show.
    """
    return _entry("implement-phase.c4", "unknown", reason=UNOBSERVABLE_REASONS["implement-phase.c4"])


# --- implement-spec predicates -----------------------------------------------

def _predicate_spec_c1(state: dict[str, Any]) -> dict[str, Any]:
    """implement-spec.c1: "scripts/story-deps.py validate returned status ok
    for the full story graph before the first story ran"

    needs-run-record: the temporal clause ("before the first story ran") is
    the gap. Reads only the recorded `preflight.storyDepsValidated` /
    `.at` -- NEVER re-runs `story-deps.py validate_graph` live, which would
    only prove the graph is valid *now* (Gate 0 finding 4).
    """
    preflight = state.get("preflight")
    if not isinstance(preflight, dict) or "storyDepsValidated" not in preflight or "at" not in preflight:
        return _entry("implement-spec.c1", "unknown", reason=PRE_STORY_2_REASON)
    if preflight.get("storyDepsValidated") is not True:
        return _entry(
            "implement-spec.c1", "unmet",
            reason=f"preflight recorded storyDepsValidated={preflight.get('storyDepsValidated')!r} at {preflight.get('at')}",
        )
    return _entry(
        "implement-spec.c1", "met",
        evidence=f"story graph validated ok at {preflight['at']}, before batch 1",
    )


def _predicate_spec_c2(state: dict[str, Any]) -> dict[str, Any]:
    """implement-spec.c2: "no story remains pending in
    .writ/state/execution-<timestamp>.json - each is complete, skipped with
    its blocking chain, or failed with a reason"

    evaluable-now: names its own evidence file directly, no new Story 2
    field required. `story-deps.py` is imported here only for the
    empty-batch vacuous-pass guard's story count, never for graph
    validation (kept separate from implement-spec.c1 on purpose).
    """
    stories = state.get("stories")
    if not isinstance(stories, dict) or not stories:
        # Shadow path: zero stories in the batch plan -> unmet, never a
        # vacuous met (technical-spec.md § Shadow Paths).
        _story_deps_for_vacuous_check()  # imported per Task 3.5's delegation intent
        return _entry("implement-spec.c2", "unmet", reason="no spec resolved: batch plan has zero stories")

    pending = []
    malformed = []
    for story_id, record in stories.items():
        status = (record or {}).get("status")
        if status not in TERMINAL_STORY_STATUSES:
            pending.append(story_id)
            continue
        if status == "skipped" and not record.get("blockedBy"):
            malformed.append(f"{story_id} (skipped without a blocking chain)")
        if status == "failed" and not record.get("reason"):
            malformed.append(f"{story_id} (failed without a reason)")

    if pending:
        return _entry(
            "implement-spec.c2", "unmet",
            reason=f"story(ies) still pending: {', '.join(sorted(pending))}",
        )
    if malformed:
        return _entry(
            "implement-spec.c2", "unmet",
            reason=f"terminal story missing required detail: {', '.join(malformed)}",
        )
    return _entry(
        "implement-spec.c2", "met",
        evidence=f"{len(stories)}/{len(stories)} stories terminal",
    )


def _predicate_spec_c3(state: dict[str, Any]) -> dict[str, Any]:
    """implement-spec.c3: "one typecheck plus full test suite ran after the
    final story, separate from the targeted per-story Gate 4 runs, and
    .writ/context.md was rewritten to the post-run story counts"

    needs-run-record: the same before/after gap as c1, mirrored at the
    other end of the run. Reads only the recorded `postRun` fields.
    """
    post = state.get("postRun")
    required_fields = ("typecheck", "testSuite", "contextRewritten", "at")
    if not isinstance(post, dict) or any(field not in post for field in required_fields):
        return _entry("implement-spec.c3", "unknown", reason=PRE_STORY_2_REASON)
    if post.get("typecheck") != "pass" or post.get("testSuite") != "pass" or post.get("contextRewritten") is not True:
        return _entry(
            "implement-spec.c3", "unmet",
            reason=(
                f"postRun recorded typecheck={post.get('typecheck')!r} "
                f"testSuite={post.get('testSuite')!r} "
                f"contextRewritten={post.get('contextRewritten')!r}"
            ),
        )
    return _entry(
        "implement-spec.c3", "met",
        evidence=f"typecheck+test suite ran after the final story at {post['at']}; context.md rewritten",
    )


# --- Dispatch, per criterion, with fault isolation --------------------------

def _safe_eval(criterion_id: str, fn: Callable[[], dict[str, Any]]) -> dict[str, Any]:
    """A predicate that raises -- including our own `Impossible` -- becomes
    THIS criterion's `impossible` entry, naming the exception type and the
    criterion id (technical-spec.md Error & Rescue Map). Other criteria
    still get evaluated; the rollup's own precedence turns any single
    `impossible` entry into the overall verdict."""
    try:
        return fn()
    except Impossible as exc:
        return _entry(criterion_id, "impossible", reason=str(exc))
    except Exception as exc:  # noqa: BLE001 - deliberately broad, see docstring
        return _entry(criterion_id, "impossible", reason=f"predicate raised {type(exc).__name__}: {exc}")


def _eval_phase_criterion(criterion_id: str, bucket: str, state: dict[str, Any],
                          state_path: Path, repo: Path) -> dict[str, Any]:
    if bucket == "structurally-unobservable":
        if criterion_id not in UNOBSERVABLE_REASONS:
            raise Impossible(f"{criterion_id} is classified structurally-unobservable but has no recorded reason")
        return _entry(criterion_id, "unknown", reason=UNOBSERVABLE_REASONS[criterion_id])
    if criterion_id == "implement-phase.c1":
        return _predicate_phase_c1(state, state_path, repo)
    if criterion_id == "implement-phase.c2":
        return _predicate_phase_c2(state, repo)
    if criterion_id == "implement-phase.c3":
        return _predicate_phase_c3(state)
    if criterion_id == "implement-phase.c4":
        return _predicate_phase_c4()
    raise Impossible(f"no predicate wired for classified criterion {criterion_id}")


def _eval_spec_criterion(criterion_id: str, bucket: str, state: dict[str, Any]) -> dict[str, Any]:
    if bucket == "structurally-unobservable":
        if criterion_id not in UNOBSERVABLE_REASONS:
            raise Impossible(f"{criterion_id} is classified structurally-unobservable but has no recorded reason")
        return _entry(criterion_id, "unknown", reason=UNOBSERVABLE_REASONS[criterion_id])
    if criterion_id == "implement-spec.c1":
        return _predicate_spec_c1(state)
    if criterion_id == "implement-spec.c2":
        return _predicate_spec_c2(state)
    if criterion_id == "implement-spec.c3":
        return _predicate_spec_c3(state)
    raise Impossible(f"no predicate wired for classified criterion {criterion_id}")


# --- Top-level check flows ---------------------------------------------------

def _check_phase(args: argparse.Namespace, classification: dict[str, str], repo: Path) -> tuple[int, dict[str, Any]]:
    if not args.state:
        raise Impossible("--state is required for --command implement-phase but was not provided")
    state_path = Path(args.state)
    state = _load_phase_state(state_path)

    _require_git_repo(repo)
    _check_impossible_pre_pass(state, state_path, repo)

    criteria_results = []
    for criterion_id in CRITERIA_BY_COMMAND["implement-phase"]:
        bucket = classification[criterion_id]
        criteria_results.append(
            _safe_eval(criterion_id, lambda cid=criterion_id, b=bucket: _eval_phase_criterion(cid, b, state, state_path, repo))
        )

    verdict = _rollup(criteria_results)
    result = {
        "verdict": verdict, "command": "implement-phase",
        "state": str(state_path), "criteria": criteria_results,
    }
    return EXIT_CODES[verdict], result


def _check_spec(args: argparse.Namespace, classification: dict[str, str], repo: Path) -> tuple[int, dict[str, Any]]:
    if not args.spec:
        raise Impossible("--spec is required for --command implement-spec but was not provided")
    spec_dir = Path(args.spec)
    if not spec_dir.is_dir():
        raise Impossible(f"spec directory not found: {spec_dir}")
    if not args.state:
        raise Impossible("--state is required for --command implement-spec but was not provided")
    state_path = Path(args.state)
    state = _load_spec_state(state_path)

    criteria_results = []
    for criterion_id in CRITERIA_BY_COMMAND["implement-spec"]:
        bucket = classification[criterion_id]
        criteria_results.append(
            _safe_eval(criterion_id, lambda cid=criterion_id, b=bucket: _eval_spec_criterion(cid, b, state))
        )

    verdict = _rollup(criteria_results)
    result = {
        "verdict": verdict, "command": "implement-spec",
        "state": str(state_path), "spec": str(spec_dir), "criteria": criteria_results,
    }
    return EXIT_CODES[verdict], result


def run_check(args: argparse.Namespace) -> tuple[int, dict[str, Any]]:
    repo = Path(args.repo)
    classification_path = (
        Path(args.classification) if args.classification
        else repo / ".writ" / "docs" / "exit-criteria-classification.md"
    )
    classification = load_classification(classification_path)

    # Validate every id this checker could emit is registered -- an id
    # absent from the classification is `impossible`, not `unknown`
    # (technical-spec.md § Rollup; Gate 0 finding 6).
    for criterion_id in CRITERIA_BY_COMMAND[args.command]:
        if criterion_id not in classification:
            raise Impossible(
                f"criterion {criterion_id!r} is absent from the classification doc {classification_path}"
            )

    if args.command == "implement-phase":
        return _check_phase(args, classification, repo)
    return _check_spec(args, classification, repo)


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__)
    sub = parser.add_subparsers(dest="action", required=True)

    p = sub.add_parser("check", help="evaluate one command's exit criteria against a run record")
    p.add_argument("--command", required=True, choices=sorted(CRITERIA_BY_COMMAND))
    p.add_argument("--state", default="")
    p.add_argument("--spec", default="")
    p.add_argument("--repo", default=".")
    p.add_argument("--classification", default="",
                   help="override the classification doc path (primarily for tests)")
    p.set_defaults(func=run_check)

    return parser


def main(argv: list[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)
    try:
        exit_code, result = args.func(args)
    except Impossible as exc:
        result = {"verdict": "impossible", "command": args.command, "reason": str(exc)}
        exit_code = 2
    print(json.dumps(result))
    return exit_code


if __name__ == "__main__":
    sys.exit(main())
