#!/usr/bin/env python3
"""Record and fit the Jev fixtures. Dev tool; not shipped with the plugin.

  calibrate.py record [--runs 2]   Live. Send every fixture through jev.py's own
                                   request builders, save each response as
                                   replay/<sha256 of request>.json, drop replay
                                   files no current request matches, and (with
                                   --runs 2) score everything a second time into
                                   rerun.json to measure run-to-run movement.
  calibrate.py scores [--split dev] [--code unclear]
                                   Offline. Every recorded probability beside
                                   its gold label, highest first.
  calibrate.py fit [--write]       Offline. Fit thresholds on the dev split with
                                   RULE, print dev and test confusion per code
                                   and the clean-document counts, and with
                                   --write save ../../../../plugins/writ/skills/
                                   writ-jev/thresholds.json.

`record` needs the same double opt-in as jev.py (`.writ/config.md` names a
backend and its key is set). It sends only the synthetic fixtures in this
folder. It never prints or stores a key. Any change to a question's wording in
jev.py changes the request hashes: record again, then fit again.
"""

from __future__ import annotations

import argparse
import importlib.util
import json
import os
import sys
import time
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

HERE = Path(__file__).resolve().parent
REPO = HERE.parents[3]
SKILL = REPO / "plugins" / "writ" / "skills" / "writ-jev"
REPLAY = HERE / "replay"
RERUN = HERE / "rerun.json"
MODEL_CODES = ("unclear", "out_of_scope", "contradiction", "gap", "no_measure",
               "unproven", "asserted", "could_be_checked")
# A criterion or proof row with a gold defect is a line worth re-reading
# whichever per-line code fires on it. So for each of these codes, a line whose
# gold label is the OTHER code in its pair is left out of the counts instead of
# being scored as a false flag ("skip" in `scores`).
DONT_CARE = {"unproven": ("asserted",), "asserted": ("unproven",),
             "unclear": ("out_of_scope",), "out_of_scope": ("unclear",)}
RULE = (
    "Per code, on the dev split only. Start from the TypeSafe docs' 0.70 flag / 0.30 "
    "check. flag: if every gold positive scores at least 0.10 above every gold "
    "negative, flag = the midpoint between the lowest positive and the highest "
    "negative, rounded to 0.05 and kept within 0.50 to 0.70 when that range lies "
    "inside the gap (recall is cheap: a wrong flag costs one re-read). Otherwise flag "
    "= 0.05 above the highest gold negative, rounded up to 0.05, and at least 0.70; "
    "if fewer than half of the gold positives reach that, the code did not separate "
    "and is check-only (flag = null). check: 0.30, raised to 0.05 above the highest "
    "score on a fully clean dev document when one reaches 0.30, and never above flag. "
    "A contract's contradiction score is the highest of its whole-list answer and its "
    "pair answers. A line whose gold label is the other code of its pair (unproven / "
    "asserted, unclear / out_of_scope) is left out of that code's counts."
)


def load_jev() -> Any:
    spec = importlib.util.spec_from_file_location("jev", SKILL / "jev.py")
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    sys.modules["jev"] = module
    spec.loader.exec_module(module)
    return module


jev = load_jev()


def labels() -> Dict[str, Dict[str, Any]]:
    data = json.loads((HERE / "labels.json").read_text(encoding="utf-8"))
    return {k: v for k, v in data.items() if not k.startswith("_")}


def request_for(name: str) -> Tuple[Dict[str, Any], Dict[str, Any], Dict[str, Any]]:
    path = HERE / name / "spec.md"
    spec = jev.parse_spec(path.read_text(encoding="utf-8"))
    if name.startswith("contracts/"):
        return jev.contract_request(spec)
    return jev.proof_request(spec, path.parent)[0]


def request_hash(name: str, backend: Any) -> str:
    state, questions, _ = request_for(name)
    return jev.request_hash(jev.canonical_body(jev.build_body(state, questions, backend)))


def record(runs: int) -> int:
    res = jev.resolve(REPO, os.environ)
    if not res.ok or res.backend is None or os.environ.get(jev.REPLAY_ENV):
        print("off: %s (record needs the live double opt-in and no %s)"
              % (res.reason, jev.REPLAY_ENV))
        return 1
    REPLAY.mkdir(exist_ok=True)
    keep = set()
    rerun: Dict[str, Dict[str, List[float]]] = {}
    for name in labels():
        state, questions, _ = request_for(name)
        captured: Dict[str, bytes] = {}

        def transport(url: str, headers: Dict[str, str], payload: bytes) -> Any:
            resp = jev.live_transport(url, headers, payload)
            captured["body"] = resp.body
            return resp

        digest = request_hash(name, res.backend)
        keep.add(digest + ".json")
        target = REPLAY / (digest + ".json")
        first: Optional[Dict[str, Any]] = None
        if target.exists():
            first = json.loads(target.read_text(encoding="utf-8"))["answers"]
        for run in range(runs):
            if run == 0 and first is not None:
                continue
            j = jev.judge(state, questions, res.backend, os.environ, transport)
            if not j.ok or j.answers is None:
                print("FAILED %s: %s" % (name, j.reason))
                return 1
            if run == 0:
                body = json.loads(captured["body"].decode("utf-8"))
                saved = {"model": body.get("model"), "answers": body["answers"],
                         "usage": body.get("usage"),
                         "writ_recording": {
                             "source": "live", "backend": res.backend.name,
                             "fixture": name, "recorded_on": time.strftime("%Y-%m-%d"),
                             "request_bytes": j.request_bytes,
                             "seconds": round(j.seconds, 3)}}
                target.write_text(json.dumps(saved, indent=2, sort_keys=True) + "\n",
                                  encoding="utf-8")
                first = j.answers
                print("recorded %-36s %5d bytes %5s tokens %.2fs"
                      % (name, j.request_bytes, j.input_tokens, j.seconds))
            else:
                rerun[name] = {q: [first[q]["noul"], j.answers[q]["noul"]]
                               for q in sorted(questions)}
    for stale in sorted(p.name for p in REPLAY.glob("*.json") if p.name not in keep):
        (REPLAY / stale).unlink()
        print("dropped stale %s" % stale)
    if rerun:
        RERUN.write_text(json.dumps(rerun, indent=1, sort_keys=True) + "\n", encoding="utf-8")
        print(rerun_summary())
    return 0


def rerun_summary() -> str:
    if not RERUN.exists():
        return "run-to-run: not measured"
    data = json.loads(RERUN.read_text(encoding="utf-8"))
    diffs = [abs(a - b) for per in data.values() for a, b in per.values()]
    moved = sum(1 for d in diffs if d > 0)
    return ("run-to-run: %d requests, %d answers, %d moved, largest difference %.2f"
            % (len(data), len(diffs), moved, max(diffs, default=0.0)))


def scored() -> List[Dict[str, Any]]:
    """One record per recorded answer: fixture, split, target, code, p, gold."""
    backend = jev.BACKENDS[json.loads(next(iter(REPLAY.glob("*.json"))).read_text(
        encoding="utf-8"))["writ_recording"]["backend"]]
    out: List[Dict[str, Any]] = []
    for name, label in labels().items():
        path = REPLAY / (request_hash(name, backend) + ".json")
        if not path.exists():
            raise SystemExit("no recording for %s: run `calibrate.py record`" % name)
        answers = json.loads(path.read_text(encoding="utf-8"))["answers"]
        _, _, index = request_for(name)
        gold = set(label["gold"])
        best: Dict[Tuple[str, str], float] = {}
        for qid, asked in index.items():
            # Pair questions fold into the contract's one contradiction score,
            # its highest: what matters is whether the contract gets the flag.
            target = "contract" if "+" in asked.target else asked.target
            key = (target, asked.code)
            best[key] = max(best.get(key, 0.0), answers[qid]["noul"])
        for (target, code), p in best.items():
            row_gold = [g.split()[1] for g in gold if g.split()[0] == target]
            out.append({"fixture": name, "split": label["split"], "target": target,
                        "code": code, "p": p, "gold": "%s %s" % (target, code) in gold,
                        "skip": any(g in DONT_CARE.get(code, ()) for g in row_gold),
                        "clean": not gold})
    return out


def _round05(value: float, up: bool = False) -> float:
    steps = value / 0.05
    whole = int(steps + (0.999999 if up else 0.5))
    return round(whole * 0.05, 2)


def fit_code(rows: List[Dict[str, Any]]) -> Dict[str, Any]:
    rows = [r for r in rows if not r["skip"]]
    pos = [r["p"] for r in rows if r["gold"]]
    neg = [r["p"] for r in rows if not r["gold"]]
    clean = [r["p"] for r in rows if r["clean"]]
    lo_pos, hi_neg = min(pos, default=1.0), max(neg, default=0.0)
    flag: Optional[float]
    if lo_pos - hi_neg >= 0.10:
        flag = min(0.70, max(0.50, _round05((lo_pos + hi_neg) / 2)))
        if not hi_neg < flag <= lo_pos:  # the clamp left the gap: stay inside it
            flag = _round05((lo_pos + hi_neg) / 2)
    else:
        flag = max(0.70, _round05(hi_neg + 0.05, up=True))
        if sum(1 for p in pos if p >= flag) * 2 < len(pos) or flag > 1.0:
            flag = None
    check = 0.30
    hi_clean = max(clean, default=0.0)
    if hi_clean >= check:
        check = _round05(hi_clean + 0.05, up=True)
    if flag is not None:
        check = min(check, flag)
    return {"flag": flag, "check": round(check, 2)}


def confusion(rows: List[Dict[str, Any]], bands: Dict[str, Dict[str, Any]]) -> Dict[str, Any]:
    out: Dict[str, Any] = {}
    for code in MODEL_CODES:
        c = {"tp": 0, "fn": 0, "fp": 0, "tn": 0, "fn_checked": 0, "tn_checked": 0}
        for r in rows:
            if r["code"] != code or r["skip"]:
                continue
            verdict = jev.band(r["p"], bands[code])
            key = ("tp" if verdict == "flag" else "fn") if r["gold"] else (
                "fp" if verdict == "flag" else "tn")
            c[key] += 1
            if verdict == "check":
                c["fn_checked" if r["gold"] else "tn_checked"] += 1
        out[code] = c
    docs: Dict[str, List[str]] = {}
    for r in rows:
        if r["clean"]:
            docs.setdefault(r["fixture"], []).append(jev.band(r["p"], bands[r["code"]]))
    out["clean_documents"] = {
        "total": len(docs),
        "no_flag": sum(1 for v in docs.values() if "flag" not in v),
        "fully_quiet": sum(1 for v in docs.values() if set(v) == {"quiet"})}
    return out


def fit(write: bool) -> int:
    rows = scored()
    dev = [r for r in rows if r["split"] == "dev"]
    bands = {code: fit_code([r for r in dev if r["code"] == code]) for code in MODEL_CODES}
    splits = {name: confusion([r for r in rows if r["split"] == name], bands)
              for name in ("dev", "test")}
    for code in MODEL_CODES:
        print("%-17s flag=%-5s check=%.2f" % (code, bands[code]["flag"], bands[code]["check"]))
    for name, result in splits.items():
        print("\n%s" % name)
        for code in MODEL_CODES:
            c = result[code]
            print("  %-17s tp=%d fn=%d (of which check=%d)  fp=%d tn=%d (of which check=%d)"
                  % (code, c["tp"], c["fn"], c["fn_checked"], c["fp"], c["tn"],
                     c["tn_checked"]))
        d = result["clean_documents"]
        print("  clean documents: %d, no flag: %d, fully quiet: %d"
              % (d["total"], d["no_flag"], d["fully_quiet"]))
    print("\n" + rerun_summary())
    if not write:
        return 0
    recordings = [json.loads(p.read_text(encoding="utf-8")) for p in sorted(REPLAY.glob("*.json"))]
    meta = recordings[0]["writ_recording"]
    counts = {split: {kind: sum(1 for k, v in labels().items()
                                if v["split"] == split and k.startswith(kind))
                      for kind in ("contracts", "proofs")} for split in ("dev", "test")}
    rerun = json.loads(RERUN.read_text(encoding="utf-8")) if RERUN.exists() else {}
    diffs = [abs(a - b) for per in rerun.values() for a, b in per.values()]
    flips = {"flag": 0, "any": 0}  # answers whose band differs between the two runs
    for name, per in rerun.items():
        index = request_for(name)[2]
        for qid, (first, second) in per.items():
            one, two = (jev.band(v, bands[index[qid].code]) for v in (first, second))
            flips["any"] += one != two
            flips["flag"] += (one == "flag") != (two == "flag")
    doc = {
        "backend": meta["backend"],
        "model": recordings[0]["model"],
        "calibrated_on": max(r["writ_recording"]["recorded_on"] for r in recordings),
        "codes": bands,
        "calibration": {
            "fit_split": "dev", "rule": RULE, "fixtures": counts,
            "check_only": [c for c in MODEL_CODES if bands[c]["flag"] is None],
            "splits": splits,
            "run_to_run": {"requests": len(rerun), "answers": len(diffs),
                           "moved": sum(1 for d in diffs if d > 0),
                           "moved_more_than_0.05": sum(1 for d in diffs if d > 0.05),
                           "moved_more_than_0.10": sum(1 for d in diffs if d > 0.10),
                           "largest_difference": round(max(diffs, default=0.0), 2),
                           "answers_that_changed_band": flips["any"],
                           "answers_that_crossed_flag": flips["flag"]},
        },
    }
    (SKILL / "thresholds.json").write_text(json.dumps(doc, indent=2) + "\n", encoding="utf-8")
    print("wrote %s" % (SKILL / "thresholds.json"))
    return 0


def scores(split: str, code: Optional[str]) -> int:
    for wanted in ([code] if code else MODEL_CODES):
        print("\n== %s (%s)" % (wanted, split))
        rows = [r for r in scored() if r["code"] == wanted and r["split"] == split]
        for r in sorted(rows, key=lambda r: -r["p"]):
            mark = "GOLD" if r["gold"] else ("skip" if r["skip"] else
                                             ("clean" if r["clean"] else ""))
            print("  %.2f  %-5s %-32s %s" % (r["p"], mark, r["fixture"], r["target"]))
    return 0


def main() -> int:
    parser = argparse.ArgumentParser(description=(__doc__ or "").split("\n\n")[0])
    sub = parser.add_subparsers(dest="action", required=True)
    p = sub.add_parser("record")
    p.add_argument("--runs", type=int, default=1, choices=(1, 2))
    p = sub.add_parser("scores")
    p.add_argument("--split", default="dev", choices=("dev", "test"))
    p.add_argument("--code", choices=MODEL_CODES)
    p = sub.add_parser("fit")
    p.add_argument("--write", action="store_true")
    args = parser.parse_args()
    if args.action == "record":
        return record(args.runs)
    if args.action == "scores":
        return scores(args.split, args.code)
    return fit(args.write)


if __name__ == "__main__":
    sys.exit(main())
