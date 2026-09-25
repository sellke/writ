#!/usr/bin/env python3
"""Keep-or-revert verdict for the WRIT_HARNESS_LEAN lean siblings.

Story 5 of 2026-09-24-flagged-harness-cuts. `decide` reads two
`pipeline-baseline-v1` files written by `pipeline-baseline.py run` on one
model — a control arm (no `--lean`) and a lean arm (`--lean`) — and prints
one verdict with the numbers behind it:

  compare_error  a file is missing, unreadable, or not pipeline-baseline-v1;
                 `runs` is empty; the models differ; the two files did not run
                 the same stories the same number of times (or at different
                 parent commits); a run is a setup failure, not a story attempt
                 (see ATTEMPT_STATUSES); the arms overlaid different
                 `writ.commit`s or a dirty tree; a lean-file record is not a
                 lean-arm run, or a control-file record is; a run has no
                 `cost_usd`.
  quality_miss   any exit-criteria row (per story, runs whose
                 `exit_criteria.rederived` is `met`, out of runs) is under N/N
                 in either arm. Both arms' `cost_usd` is printed, marked
                 informational.
  keep           the full sample (FULL_SAMPLE_STORIES stories x
                 FULL_SAMPLE_RUNS runs per arm), every row N/N, and the lean
                 arm's summed driver `cost_usd` strictly below control's.
  null           everything else — including a reduced sample that is cheaper.

`cost_usd` is the price of record. `harness-cost.py`'s formula figure is
printed beside it and does not decide. No verdict flips the default load
path; this script only reads.

Usage:
  lean-decision.py decide --control PATH --lean PATH [--format text|json]

Exit codes: 0 a verdict was computed (any of the four) · 2 usage error.
"""

from __future__ import annotations

import argparse
import importlib.util
import json
import sys
from collections import Counter
from pathlib import Path
from typing import Optional

HERE = Path(__file__).resolve().parent

FULL_SAMPLE_STORIES = 4
FULL_SAMPLE_RUNS = 2
VERDICTS = ("keep", "null", "quality_miss", "compare_error")
MET = "met"

# Which failed runs count against an arm's quality. A run is a story attempt
# when the driver ran the story and stopped on its own terms: the transcript's
# `result` event mapped to `complete`, to `budget`, or to `error` with one of
# these subtypes (pipeline-baseline.py RESULT_SUBTYPE_STATUS). Everything else
# is a setup failure and a compare error: no `writ` block, a pre-model
# RunError reason (pipeline-baseline.py `RunError("...")`), `timeout` (the
# wall-clock cap killed the group), `no_result_event`, or any status/reason
# this list does not name.
ATTEMPT_STATUSES = frozenset({"complete", "budget"})
ATTEMPT_ERROR_REASONS = frozenset({"error_during_execution", "error_max_turns"})
SETUP_REASONS = frozenset({"fetch_failed", "isolation_failed", "inputs_missing", "answer_leak",
                           "overlay_failed", "lean_overlay_failed"})


def _load_sibling(name: str, filename: str):
    spec = importlib.util.spec_from_file_location(name, HERE / filename)
    module = importlib.util.module_from_spec(spec)
    sys.modules[name] = module          # dataclasses resolve annotations through sys.modules
    spec.loader.exec_module(module)     # type: ignore[union-attr]
    return module


pb = _load_sibling("pipeline_baseline", "pipeline-baseline.py")
hc = _load_sibling("harness_cost", "harness-cost.py")


def _read(label: str, path: Path) -> tuple:
    """(doc, reason). `reason` is None when the file is a usable baseline."""
    if not path.is_file():
        return None, "%s file %s does not exist" % (label, path)
    try:
        doc = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, ValueError, UnicodeDecodeError) as exc:
        return None, "%s file %s is not valid JSON (%s)" % (label, path, exc.__class__.__name__)
    if not isinstance(doc, dict) or doc.get("schema") != pb.SCHEMA:
        return None, "%s file %s is not a %s file" % (label, path, pb.SCHEMA)
    runs = doc.get("runs")
    if not isinstance(runs, list) or not [r for r in runs if isinstance(r, dict)]:
        return None, "%s file %s has empty runs" % (label, path)
    return doc, None


def _runs(doc: dict) -> list:
    return [r for r in doc["runs"] if isinstance(r, dict)]


def _run_counts(doc: dict) -> Counter:
    return Counter(r.get("story_id") for r in _runs(doc))


def _parents(doc: dict) -> dict:
    return {sid: (path, parent) for path, parent, sid in pb._story_pairs(doc)}


def _arm_errors(label: str, doc: dict, want_lean: bool) -> list:
    """A record that reached the overlay says which arm it was. Records
    written before the lean arm existed lack the key and count as control."""
    for rec in _runs(doc):
        writ = rec.get("writ")
        if not isinstance(writ, dict):
            continue                     # failed before the overlay: no arm to check
        if bool(writ.get("harness_lean", False)) != want_lean:
            return ["%s file holds a %s-arm record (%s run %s, writ.harness_lean=%s); "
                    "run the %s arm %s --lean" % (
                        label, "control" if want_lean else "lean", rec.get("story_id"), rec.get("run"),
                        json.dumps(writ.get("harness_lean")), label,
                        "with" if want_lean else "without")]
    return []


def is_attempt(rec: dict) -> bool:
    if not isinstance(rec.get("writ"), dict) or rec.get("reason") in SETUP_REASONS:
        return False
    status = rec.get("status")
    if status in ATTEMPT_STATUSES:
        return True
    return status == "error" and rec.get("reason") in ATTEMPT_ERROR_REASONS


def _setup_failures(label: str, doc: dict) -> list:
    out = []
    for rec in _runs(doc):
        if is_attempt(rec):
            continue
        detail = rec.get("status")
        if rec.get("reason"):
            detail = "%s (%s)" % (detail, rec.get("reason"))
        if not isinstance(rec.get("writ"), dict):
            detail += ", no writ block"
        out.append("setup failure: %s run %s %s [%s]" % (rec.get("story_id"), rec.get("run"), detail, label))
    return out


def _provenance_errors(control: dict, lean: dict) -> list:
    """Both arms must overlay the same committed Writ tree."""
    commits = {}
    dirty = []
    for label, doc in (("control", control), ("lean", lean)):
        for rec in _runs(doc):
            writ = rec.get("writ")
            if not isinstance(writ, dict):
                continue
            commits.setdefault(label, set()).add(writ.get("commit"))
            if writ.get("dirty") is not False:
                dirty.append("%s %s run %s" % (label, rec.get("story_id"), rec.get("run")))
    c = sorted(map(str, commits.get("control", ())))
    l = sorted(map(str, commits.get("lean", ())))
    errors = []
    if c != l or len(c) > 1:
        errors.append("writ.commit differs: control %s, lean %s (both arms must overlay one commit)"
                      % (", ".join(c) or "none", ", ".join(l) or "none"))
    if dirty:
        errors.append("writ.dirty is not false on %s (control commit %s, lean commit %s); "
                      "commit the Writ tree before a paid run" % (dirty[0], ", ".join(c) or "none",
                                                                 ", ".join(l) or "none"))
    return errors


def _price(value) -> Optional[float]:
    if isinstance(value, bool) or not isinstance(value, (int, float)):
        return None
    return float(value)


def _rows(control: dict, lean: dict, order: list) -> list:
    rows = []
    for sid in order:
        cr, lr = pb._runs_for(control, sid), pb._runs_for(lean, sid)
        c_met = sum(1 for r in cr if pb._lookup(r, "exit_criteria.rederived") == MET)
        l_met = sum(1 for r in lr if pb._lookup(r, "exit_criteria.rederived") == MET)
        rows.append({"story_id": sid, "control": "%d/%d" % (c_met, len(cr)), "lean": "%d/%d" % (l_met, len(lr)),
                     "full": c_met == len(cr) and l_met == len(lr)})
    return rows


def decide(control_path: Path, lean_path: Path) -> dict:
    result = {"verdict": None, "reasons": [], "model": None, "sample": None, "exit_criteria": [],
              "cost_usd": None, "formula_usd": None,
              "files": {"control": str(control_path), "lean": str(lean_path)}}

    def done(verdict: str, *reasons: str) -> dict:
        result["verdict"] = verdict
        result["reasons"].extend(reasons)
        return result

    control, c_err = _read("control", control_path)
    lean, l_err = _read("lean", lean_path)
    if c_err or l_err:
        return done("compare_error", *[e for e in (c_err, l_err) if e])

    if control.get("model") != lean.get("model"):
        return done("compare_error", "model differs: control %s, lean %s (one model per compare)"
                    % (control.get("model"), lean.get("model")))
    result["model"] = control.get("model")

    c_counts, l_counts = _run_counts(control), _run_counts(lean)
    if c_counts != l_counts:
        only = sorted(set(c_counts.items()) ^ set(l_counts.items()), key=str)
        return done("compare_error", "story selection differs (story id, runs): control %s, lean %s; first "
                    "difference %s" % (dict(c_counts), dict(l_counts), only[0] if only else "?"))
    c_parents, l_parents = _parents(control), _parents(lean)
    for sid in c_counts:
        if c_parents.get(sid) != l_parents.get(sid):
            return done("compare_error", "story selection differs: %s has story_path/parent_sha %s in control, "
                        "%s in lean" % (sid, c_parents.get(sid), l_parents.get(sid)))

    setup = _setup_failures("control", control) + _setup_failures("lean", lean)
    if setup:
        return done("compare_error", *setup)

    provenance = _provenance_errors(control, lean)
    if provenance:
        return done("compare_error", *provenance)

    arm = _arm_errors("control", control, False) + _arm_errors("lean", lean, True)
    if arm:
        return done("compare_error", *arm)

    order = [sid for _, _, sid in pb._story_pairs(control) if sid in c_counts]
    order += sorted((sid for sid in c_counts if sid not in order), key=str)
    runs_per = sorted(set(c_counts.values()))
    full = len(c_counts) >= FULL_SAMPLE_STORIES and min(runs_per) >= FULL_SAMPLE_RUNS
    result["sample"] = {"stories": len(c_counts), "runs_per_story": runs_per[0] if len(runs_per) == 1 else runs_per,
                        "full": full}
    result["exit_criteria"] = _rows(control, lean, order)
    result["formula_usd"] = {"control": hc.summarize_baseline(control)["formula_usd"],
                             "lean": hc.summarize_baseline(lean)["formula_usd"],
                             "note": "harness-cost.py formula; lower bound; does not decide"}

    misses = [r for r in result["exit_criteria"] if not r["full"]]
    if misses:
        # Informational only: a quality miss is never priced into a keep.
        c_cost = sum(_price(r.get("cost_usd")) or 0.0 for r in _runs(control))
        l_cost = sum(_price(r.get("cost_usd")) or 0.0 for r in _runs(lean))
        result["cost_usd"] = {"control": c_cost, "lean": l_cost, "delta": l_cost - c_cost, "informational": True}
        return done("quality_miss", "exit-criteria rows under N/N: %s" % ", ".join(
            "%s control %s lean %s" % (r["story_id"], r["control"], r["lean"]) for r in misses))

    unpriced = [(label, r.get("story_id"), r.get("run")) for label, doc in (("control", control), ("lean", lean))
                for r in _runs(doc) if _price(r.get("cost_usd")) is None]
    if unpriced:
        return done("compare_error", "cost_usd missing on %s %s run %s; cost_usd is the price of record"
                    % unpriced[0])
    c_cost = sum(_price(r.get("cost_usd")) for r in _runs(control))
    l_cost = sum(_price(r.get("cost_usd")) for r in _runs(lean))
    result["cost_usd"] = {"control": c_cost, "lean": l_cost, "delta": l_cost - c_cost}
    cheaper = l_cost < c_cost

    if not full:
        return done("null", "reduced sample: keep requires %d stories × %d; have %d stor%s × %s"
                    % (FULL_SAMPLE_STORIES, FULL_SAMPLE_RUNS, len(c_counts),
                       "y" if len(c_counts) == 1 else "ies", result["sample"]["runs_per_story"]),
                    "lean cost_usd is %s control" % ("below" if cheaper else "not below"))
    if not cheaper:
        return done("null", "lean arm not cheaper: cost_usd %.2f vs control %.2f" % (l_cost, c_cost))
    return done("keep", "full sample, every exit-criteria row N/N, lean cost_usd %.2f below control %.2f"
                % (l_cost, c_cost))


def _usd(value) -> str:
    return "—" if value is None else "$%.2f" % value


def format_text(result: dict) -> str:
    lines = ["verdict: %s" % result["verdict"]]
    lines += ["reason: %s" % r for r in result["reasons"]]
    lines.append("control: %s" % result["files"]["control"])
    lines.append("lean: %s" % result["files"]["lean"])
    if result["model"] is not None:
        lines.append("model: %s" % result["model"])
    sample = result["sample"]
    if sample is not None:
        lines.append("sample: %d stor%s × %s runs per arm (%s; keep requires %d × %d)" % (
            sample["stories"], "y" if sample["stories"] == 1 else "ies", sample["runs_per_story"],
            "full" if sample["full"] else "reduced", FULL_SAMPLE_STORIES, FULL_SAMPLE_RUNS))
    if result["exit_criteria"]:
        lines.append("exit_criteria (control / lean):")
        for row in result["exit_criteria"]:
            lines.append("  %s  %s / %s" % (row["story_id"], row["control"], row["lean"]))
    cost = result["cost_usd"]
    if cost is not None:
        lines.append("cost_usd (price of record%s): control %s, lean %s, delta %s%s" % (
            ", informational" if cost.get("informational") else "",
            _usd(cost["control"]), _usd(cost["lean"]), "-" if cost["delta"] < 0 else "+",
            _usd(abs(cost["delta"]))))
    formula = result["formula_usd"]
    if formula is not None:
        lines.append("formula_usd (harness-cost.py, lower bound, does not decide): control %s, lean %s"
                     % (_usd(formula["control"]), _usd(formula["lean"])))
    return "\n".join(lines)


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(prog="lean-decision.py",
                                     description="Keep-or-revert verdict for the lean siblings.")
    sub = parser.add_subparsers(dest="command", required=True)
    dec = sub.add_parser("decide", help="compare a control and a lean pipeline-baseline-v1 file")
    dec.add_argument("--control", required=True, help="baseline from `pipeline-baseline.py run` without --lean")
    dec.add_argument("--lean", required=True, help="baseline from `pipeline-baseline.py run --lean`, same model")
    dec.add_argument("--format", choices=("text", "json"), default="text")
    return parser


def main(argv: Optional[list] = None) -> int:
    args = build_parser().parse_args(argv)
    result = decide(Path(args.control).expanduser(), Path(args.lean).expanduser())
    if args.format == "json":
        print(json.dumps(result, indent=2, sort_keys=True, ensure_ascii=False))
    else:
        print(format_text(result))
    return 0


if __name__ == "__main__":
    sys.exit(main())
