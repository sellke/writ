#!/usr/bin/env python3
"""Gate upgrade removal trial harness (spec `2026-10-25-gate-upgrade-removal-measurement`).

Dev-only and temporary: it lives under `.writ/eval/`, never ships, and Story 4
deletes it. It runs each Phase 15 gate upgrade against all switches off on the
four Phase 11 baseline stories. It never spawns an agent and makes no network
call. The committed trial file holds IDs, SHAs, routes, keys, and labels only,
never yuss text.

Subcommands (Story 1):
  init    --baseline FILE --out FILE [--repo .] [--force] [--yuss PATH]
              Copy the five identity fields of each of the four selected
              stories, probe the four upgrades against --repo, and write a
              `gate-upgrade-trial-v1` skeleton. --yuss records a read-only
              before-snapshot of yuss (HEAD plus hashes of refs and status).
  prepare --trial FILE --story ID --yuss PATH [--tmp-root DIR]
              Fetch the story commit at depth 2 into
              <tmp-root>/writ-gate-trial-<slug>/ (yuss is only read), add a
              parent/ worktree, compute the Gate 2.5 and Gate 0 routes, run
              blast-radius when Gate 3 routes to review-agent and safety-fact
              is present, write one .writ/config.md per arm, then store the
              routes in the trial file.

Story 2 adds record, sheet, label, report, and snapshot.

Output (agent CLI contract, check shape): line 1 `pass`, detail lines, last
line `gate-upgrade-trial: ...`, exit 0. A refusal exits 2 with stdout empty
and exactly one stderr line `reason: <code> — <detail>`; files are left as
they were. Usage errors exit 2.
"""

from __future__ import annotations

import argparse
import hashlib
import importlib.util
import json
import os
import re
import shutil
import subprocess
import sys
from pathlib import Path, PurePosixPath
from types import ModuleType
from typing import Callable, Dict, List, Optional, Sequence, Tuple


REPO_ROOT = Path(__file__).resolve().parents[3]
SCRIPTS = REPO_ROOT / "scripts"
REVIEW_PANEL = SCRIPTS / "review-panel.py"

SCHEMA = "gate-upgrade-trial-v1"
TRIAL_STORIES = 4
IDENTITY_FIELDS = ("story_id", "story_path", "spec_folder", "story_commit", "parent_sha")
UPGRADES = ("gate0-divergence", "safety-fact", "reviewer-filters", "repro-first")
ARMS = ("off-1", "off-2", "reviewer-filters", "safety-fact", "gate0-divergence", "repro-first")
SWITCHES = {
    "gate0-divergence": "Gate 0 Divergence",
    "safety-fact": "Safety Fact",
    "reviewer-filters": "Reviewer Filters",
    "repro-first": "Repro First",
}
# The review-panel.py names this harness reuses; `PrepareError` is what
# `_prepare_run` raises, so it is checked at load time too.
REUSED = ("_prepare_run", "parse_output", "trial_key", "_key_order")
REQUIRED_NAMES = REUSED + ("PrepareError",)

# Local copies so `init` never loads review-panel.py.
SHA = re.compile(r"^[0-9a-f]{7,40}$")
SAFE_REL = re.compile(r"^[A-Za-z0-9._][A-Za-z0-9._/-]*$")
GIT_REDIRECTS = ("GIT_DIR", "GIT_WORK_TREE", "GIT_INDEX_FILE", "GIT_OBJECT_DIRECTORY",
                 "GIT_ALTERNATE_OBJECT_DIRECTORIES", "GIT_COMMON_DIR")

GATE0_MARKER = "**Design divergence (boundary-crossing route).**"
SURFACES = ("style-only", "single-component", "cross-component", "full-stack")
ROUTES = ("evaluator-agent", "review-agent")
CROSSINGS_VERDICTS = ("pass", "unverifiable")
HISTORICAL = "historical, not re-run"
NO_HISTORY = "(no historical test results in the story file)"
WHAT_WAS_BUILT = re.compile(r"^## What Was Built\s*$", re.MULTILINE)
TEST_RESULTS = re.compile(r"^### Test Results\s*$", re.MULTILINE)
H2_OR_H3 = re.compile(r"^#{2,3} ", re.MULTILINE)
NEXT_H2 = re.compile(r"^## ", re.MULTILINE)
EXIT_CODE_LINE = re.compile(r"^\s*exit code:", re.IGNORECASE)


class Refusal(Exception):
    """Exit 2 with one `reason: <code> — <detail>` line; nothing written."""

    def __init__(self, code: str, detail: str) -> None:
        super().__init__(code, detail)
        self.code = code
        self.detail = detail

    def line(self) -> str:
        return "reason: %s — %s" % (self.code, " ".join(self.detail.split()))


# --- shared helpers -----------------------------------------------------------

def _plural(count: int, word: str) -> str:
    if count == 1:
        return "1 %s" % word
    return "%d %s" % (count, word[:-1] + "ies" if word.endswith("y") else word + "s")


def write_json_atomic(path: Path, doc: dict) -> None:
    """Temp file beside the target, then `os.replace`."""
    path.parent.mkdir(parents=True, exist_ok=True)
    tmp = path.with_name(".%s.tmp" % path.name)
    try:
        tmp.write_text(json.dumps(doc, indent=2, sort_keys=True) + "\n", encoding="utf-8")
        os.replace(str(tmp), str(path))
    finally:
        if tmp.exists():
            tmp.unlink()


def load_json(path: Path, code: str, what: str) -> dict:
    try:
        doc = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, UnicodeDecodeError, ValueError) as exc:
        raise Refusal(code, "%s unreadable: %s (%s)" % (what, path, exc.__class__.__name__))
    if not isinstance(doc, dict):
        raise Refusal(code, "%s is not a JSON object: %s" % (what, path))
    return doc


def load_trial(path: Path) -> dict:
    doc = load_json(path, "trial_invalid", "trial file")
    stories = doc.get("stories")
    if doc.get("schema") != SCHEMA or not isinstance(stories, list):
        raise Refusal("trial_invalid", "not a %s file: %s" % (SCHEMA, path))
    return doc


def trial_story(doc: dict, story_id: str) -> dict:
    for story in doc["stories"]:
        if isinstance(story, dict) and story.get("story_id") == story_id:
            return story
    raise Refusal("story_unknown", "not in the trial file")


def load_review_panel() -> ModuleType:
    """`scripts/review-panel.py` by path; `review_panel_missing` when it is
    absent, fails to load, or lacks a reused name."""
    path = REVIEW_PANEL
    if not path.is_file():
        raise Refusal("review_panel_missing", "%s not found" % path)
    spec = importlib.util.spec_from_file_location("gate_trial_review_panel", path)
    if spec is None or spec.loader is None:
        raise Refusal("review_panel_missing", "%s cannot be loaded" % path)
    module = importlib.util.module_from_spec(spec)
    try:
        spec.loader.exec_module(module)
    except Exception as exc:  # any load failure means the reused names are unavailable
        raise Refusal("review_panel_missing", "%s failed to load (%s)"
                      % (path, exc.__class__.__name__))
    missing = [name for name in REQUIRED_NAMES if not hasattr(module, name)]
    if missing:
        raise Refusal("review_panel_missing", "%s lacks %s" % (path, ", ".join(missing)))
    return module


def _git_env() -> Dict[str, str]:
    env = {k: v for k, v in os.environ.items() if k not in GIT_REDIRECTS}
    env["GIT_OPTIONAL_LOCKS"] = "0"
    return env


def git(cwd: Path, *args: str) -> subprocess.CompletedProcess:
    return subprocess.run(["git", "-C", str(cwd), *args], capture_output=True,
                          env=_git_env())


def _git_text(cwd: Path, *args: str) -> Optional[str]:
    proc = git(cwd, *args)
    return proc.stdout.decode("utf-8", "replace") if proc.returncode == 0 else None


def require_yuss(yuss: Path) -> Path:
    """yuss must be the top of a git work tree; only read here."""
    if not yuss.is_dir():
        raise Refusal("yuss_missing", "yuss path missing: %s" % yuss)
    top = _git_text(yuss, "rev-parse", "--show-toplevel")
    if top is None or Path(top.strip()).resolve() != yuss.resolve():
        raise Refusal("yuss_missing", "not the top of a git work tree: %s" % yuss)
    return yuss.resolve()


def yuss_snapshot(yuss: Path) -> Dict[str, str]:
    """HEAD plus hashes of `git show-ref` and `git status --porcelain`. Read-only;
    no yuss text is kept. Story 2's `snapshot` records `after` with this."""
    yuss = require_yuss(yuss)
    head = _git_text(yuss, "rev-parse", "--verify", "HEAD")
    if head is None:
        raise Refusal("yuss_missing", "yuss has no HEAD commit: %s" % yuss)
    refs = git(yuss, "show-ref")
    status = git(yuss, "status", "--porcelain")
    # `show-ref` exits 1 when there are no refs at all.
    if refs.returncode not in (0, 1) or status.returncode != 0:
        raise Refusal("yuss_missing", "git cannot read refs or status in %s" % yuss)
    return {
        "head": head.strip(),
        "refs_sha256": hashlib.sha256(refs.stdout).hexdigest(),
        "status_sha256": hashlib.sha256(status.stdout).hexdigest(),
    }


def _safe_rel(value: str) -> bool:
    return bool(SAFE_REL.match(value)) and ".." not in value.split("/")


def check_identity(entry: object) -> Dict[str, str]:
    """The five identity fields, validated: hex SHAs and safe relative paths."""
    if not isinstance(entry, dict):
        raise Refusal("selection_invalid", "a selection entry is not an object")
    identity = {}
    for field in IDENTITY_FIELDS:
        value = entry.get(field)
        if not isinstance(value, str) or not value:
            raise Refusal("selection_invalid", "a selection entry lacks %s" % field)
        identity[field] = value
    for field in ("story_commit", "parent_sha"):
        if not SHA.match(identity[field]):
            raise Refusal("bad_sha", "%s of %s is not a hex commit SHA: %r"
                          % (field, identity["story_id"], identity[field]))
    for field in ("story_id", "story_path", "spec_folder"):
        if not _safe_rel(identity[field]):
            raise Refusal("unsafe_path", "%s is not a safe relative path: %r"
                          % (field, identity[field]))
    return identity


# --- init ---------------------------------------------------------------------

def _gate0_present(repo: Path) -> bool:
    text = (repo / "commands" / "implement-story.md").read_text(encoding="utf-8")
    return GATE0_MARKER in text


PROBES: Dict[str, Callable[[Path], bool]] = {
    "gate0-divergence": _gate0_present,
    "safety-fact": lambda repo: (repo / "skills" / "blast-radius" / "SKILL.md").is_file(),
    "reviewer-filters": lambda repo: (repo / "skills" / "review-judgment-filters"
                                      / "SKILL.md").is_file(),
    "repro-first": lambda repo: (repo / "scripts" / "repro-order.py").is_file(),
}


def probe_upgrades(repo: Path) -> Dict[str, Dict[str, bool]]:
    """A probe that errors stores `present: false`; it never fails the run."""
    upgrades = {}
    for name in UPGRADES:
        try:
            present = bool(PROBES[name](repo))
        except (OSError, UnicodeDecodeError):
            present = False
        upgrades[name] = {"present": present}
    return upgrades


def trial_skeleton(baseline: dict, baseline_path: str,
                   upgrades: Dict[str, Dict[str, bool]]) -> dict:
    selection = baseline.get("selection")
    if not isinstance(selection, list) or len(selection) != TRIAL_STORIES:
        raise Refusal("selection_invalid", "baseline selection must list exactly %d stories"
                      % TRIAL_STORIES)
    stories = []
    for entry in selection:
        story: Dict[str, object] = dict(check_identity(entry))
        story.update(routes=None, repro_kind=None, arms={}, upgrade_only=[], off_only={})
        stories.append(story)
    if len({s["story_id"] for s in stories}) != len(stories):
        raise Refusal("selection_invalid", "baseline selection repeats a story_id")
    return {
        "schema": SCHEMA,
        "baseline": baseline_path,
        "origin": None,
        "yuss_snapshot": {"before": None, "after": None, "unchanged": None},
        "upgrades": upgrades,
        "stories": stories,
        "sheet": None,
        "acks": {},
        "labeled_by": None,
    }


def cmd_init(args: argparse.Namespace) -> int:
    out = Path(args.out)
    if out.exists() and not args.force:
        raise Refusal("out_exists", "refusing to overwrite %s without --force" % out)
    repo = Path(args.repo)
    if not repo.is_dir():
        raise Refusal("repo_missing", "--repo is not a directory: %s" % repo)
    baseline = load_json(Path(args.baseline), "baseline_unreadable", "baseline")
    doc = trial_skeleton(baseline, args.baseline, probe_upgrades(repo))
    if args.yuss:
        doc["yuss_snapshot"]["before"] = yuss_snapshot(Path(args.yuss))
    write_json_atomic(out, doc)
    print("pass")
    for story in doc["stories"]:
        print("story: %s %s" % (story["story_id"], story["story_commit"][:12]))
    for name in UPGRADES:
        print("upgrade: %s present=%s" % (name, "true" if doc["upgrades"][name]["present"]
                                          else "false"))
    before = doc["yuss_snapshot"]["before"]
    if before is not None:
        print("yuss: before recorded (head %s)" % before["head"][:12])
    present = sum(1 for name in UPGRADES if doc["upgrades"][name]["present"])
    print("gate-upgrade-trial: initialized — %s, %s present, no arms recorded"
          % (_plural(len(doc["stories"]), "story"), _plural(present, "upgrade")))
    return 0


# --- prepare ------------------------------------------------------------------

def run_script(name: str, *args: str) -> subprocess.CompletedProcess:
    return subprocess.run([sys.executable, str(SCRIPTS / name), *args],
                          capture_output=True, text=True)


def _script_json(proc: subprocess.CompletedProcess, what: str) -> dict:
    try:
        doc = json.loads(proc.stdout)
    except ValueError:
        doc = None
    if not isinstance(doc, dict):
        raise Refusal("route_failed", "%s printed no JSON object" % what)
    return doc


def _route_script(name: str, what: str, *args: str) -> subprocess.CompletedProcess:
    proc = run_script(name, *args)
    if proc.returncode != 0:
        first = (proc.stderr.strip().splitlines() or ["no stderr"])[0]
        raise Refusal("route_failed", "%s exited %d (%s)" % (what, proc.returncode, first))
    return proc


def classify(files: Sequence[str], what: str) -> str:
    proc = _route_script("change-surface.py", what, "classify", "--changed", *files, "--pretty")
    surface = proc.stdout.strip()
    if surface not in SURFACES:
        raise Refusal("route_failed", "%s printed an unknown class: %r" % (what, surface))
    return surface


def crossings(boundary: Path, files: Sequence[str], story_file: Path, surface: str,
              checkout: Path, what: str) -> dict:
    proc = _route_script("boundary-map.py", what, "crossings", "--map", str(boundary),
                         "--changed", *files, "--story", str(story_file),
                         "--surface", surface, "--repo", str(checkout))
    doc = _script_json(proc, what)
    if doc.get("route") not in ROUTES or doc.get("verdict") not in CROSSINGS_VERDICTS:
        raise Refusal("route_failed", "%s printed no route" % what)
    return doc


def compute_routes(run: Path, checkout: Path, story_file: Path,
                   changed: Sequence[str]) -> Tuple[Dict[str, Optional[str]], dict]:
    """technical-spec § Routes. Returns (routes for the trial file, routes.json)."""
    boundary = run / "boundary.json"
    proc = run_script("boundary-map.py", "compute", "--story", str(story_file),
                      "--repo", str(checkout))
    if proc.returncode not in (0, 1):  # 1 is a malformed-story blocker; crossings reads it
        first = (proc.stderr.strip().splitlines() or ["no stderr"])[0]
        raise Refusal("route_failed", "boundary-map compute exited %d (%s)"
                      % (proc.returncode, first))
    boundary_doc = _script_json(proc, "boundary-map compute")
    boundary.write_text(proc.stdout, encoding="utf-8")

    surface = classify(changed, "change-surface classify (changed files)")
    gate3 = crossings(boundary, changed, story_file, surface, checkout,
                      "boundary-map crossings (changed files)")
    gate3_route = "review-agent" if gate3["verdict"] == "unverifiable" else gate3["route"]

    owned = boundary_doc.get("owned")
    planned = [p for p in owned if isinstance(p, str)] if isinstance(owned, list) else []
    routes: Dict[str, Optional[str]] = {"surface": surface, "gate3_route": gate3_route,
                                        "planned_surface": None, "gate0_route": "skip"}
    gate0: Dict[str, object] = {"planned": planned, "planned_surface": None,
                                "crossings": None, "reason": None}
    if not planned:
        routes["gate0_reason"] = "unverifiable: no planned files"
    else:
        planned_surface = classify(planned, "change-surface classify (planned files)")
        doc = crossings(boundary, planned, story_file, planned_surface, checkout,
                        "boundary-map crossings (planned files)")
        routes["planned_surface"] = planned_surface
        gate0.update(planned_surface=planned_surface, crossings=doc)
        if doc["verdict"] == "unverifiable":
            reasons = doc.get("reasons") or ["unverifiable"]
            routes["gate0_reason"] = "unverifiable: %s" % reasons[0]
        else:
            routes["gate0_route"] = doc["route"]
    gate0["reason"] = routes.get("gate0_reason")
    routes_doc = {"gate3": {"changed": list(changed), "surface": surface, "crossings": gate3},
                  "gate0": gate0}
    return routes, routes_doc


def historical_tests(story_text: str) -> str:
    """`tests.txt`: the What Was Built → Test Results text under a
    `historical, not re-run` line, with any `exit code:` line dropped so the
    safety-fact `tested` rung stays out of reach."""
    lines: List[str] = []
    built = WHAT_WAS_BUILT.search(story_text)
    if built is not None:
        section = story_text[built.end():]
        end = NEXT_H2.search(section)
        section = section[:end.start()] if end else section
        results = TEST_RESULTS.search(section)
        if results is not None:
            body = section[results.end():]
            stop = H2_OR_H3.search(body)
            body = body[:stop.start()] if stop else body
            kept = [line for line in body.splitlines() if not EXIT_CODE_LINE.match(line)]
            lines = "\n".join(kept).strip("\n").splitlines()
    if not any(line.strip() for line in lines):
        lines = [NO_HISTORY]
    return "\n".join([HISTORICAL] + lines) + "\n"


def arm_config(arm: str) -> str:
    """Switch states only: `off-1`/`off-2` all off; an upgrade arm turns on its own."""
    lines = ["# Writ Project Config (gate-upgrade-trial arm %s)" % arm, "", "## Conventions", ""]
    for name in UPGRADES:
        lines.append("- **%s:** %s" % (SWITCHES[name], "on" if name == arm else "off"))
    return "\n".join(lines) + "\n"


def _story_in_checkout(checkout: Path, story: dict) -> Path:
    stem = PurePosixPath(story["story_path"]).name
    active = checkout / ".writ" / "specs" / story["spec_folder"] / "user-stories" / stem
    return active if active.is_file() else checkout / story["story_path"]


def _changed_files(checkout: Path, parent: str, commit: str) -> List[str]:
    proc = git(checkout, "diff", "--name-only", "-z", parent, commit)
    if proc.returncode != 0:
        raise Refusal("prepare_failed", "git diff --name-only %s %s failed"
                      % (parent[:12], commit[:12]))
    return [p for p in proc.stdout.decode("utf-8", "replace").split("\0") if p]


def cmd_prepare(args: argparse.Namespace) -> int:
    rp = load_review_panel()  # review_panel_missing carries no story prefix
    try:
        return _prepare(args, rp)
    except Refusal as exc:
        raise Refusal(exc.code, "%s: %s" % (args.story, exc.detail))


def _prepare(args: argparse.Namespace, rp: ModuleType) -> int:
    # Pre-flight: no writes until every input checks out.
    trial_path = Path(args.trial)
    doc = load_trial(trial_path)
    story = trial_story(doc, args.story)
    check_identity(story)
    commit, parent = story["story_commit"], story["parent_sha"]
    yuss = require_yuss(Path(args.yuss))
    for field, sha in (("story_commit", commit), ("parent_sha", parent)):
        if _git_text(yuss, "rev-parse", "--verify", "--quiet", "%s^{commit}" % sha) is None:
            raise Refusal("sha_unreachable", "%s %s unreachable in %s" % (field, sha[:12], yuss))
    upgrades = doc.get("upgrades") if isinstance(doc.get("upgrades"), dict) else {}
    safety_fact = bool((upgrades.get("safety-fact") or {}).get("present"))

    tmp_root = Path(args.tmp_root or os.environ.get("TMPDIR") or "/tmp")
    run = tmp_root / ("writ-gate-trial-%s" % story["story_id"].replace("/", "--"))
    if run.exists():
        shutil.rmtree(str(run))
    done = False
    try:
        try:
            paths = rp._prepare_run(yuss, story, run)
        except (rp.PrepareError, OSError) as exc:
            raise Refusal("prepare_failed", str(exc))
        checkout = paths["checkout"]
        if git(checkout, "worktree", "add", "--detach", "../parent", parent).returncode != 0:
            raise Refusal("prepare_failed", "worktree add of parent %s failed" % parent[:12])
        paths["parent"] = run / "parent"

        changed = _changed_files(checkout, parent, commit)
        story_file = _story_in_checkout(checkout, story)
        routes, routes_doc = compute_routes(run, checkout, story_file, changed)
        paths["tests"] = run / "tests.txt"
        paths["tests"].write_text(historical_tests(paths["story"].read_text(encoding="utf-8")),
                                  encoding="utf-8")
        paths["boundary"] = run / "boundary.json"
        paths["routes-json"] = run / "routes.json"
        paths["routes-json"].write_text(json.dumps(routes_doc, indent=2, sort_keys=True) + "\n",
                                        encoding="utf-8")

        if routes["gate3_route"] == "review-agent" and safety_fact:
            proc = run_script("change-surface.py", "blast-radius", "--changed", *changed,
                              "--repo", str(checkout))
            try:
                blast = json.loads(proc.stdout) if proc.returncode == 0 else None
            except ValueError:
                blast = None
            if not isinstance(blast, dict):
                raise Refusal("blast_radius_unavailable", "change-surface.py blast-radius %s" % (
                    "printed no JSON object" if proc.returncode == 0
                    else "exited %d" % proc.returncode))
            paths["blast-radius"] = run / "blast-radius.json"
            paths["blast-radius"].write_text(proc.stdout, encoding="utf-8")

        configs = {}
        for arm in ARMS:
            config = run / "arms" / arm / ".writ" / "config.md"
            config.parent.mkdir(parents=True)
            config.write_text(arm_config(arm), encoding="utf-8")
            configs[arm] = config

        story["routes"] = routes
        write_json_atomic(trial_path, doc)  # last: the trial file changes only on success
        done = True
    finally:
        if not done:
            shutil.rmtree(str(run), ignore_errors=True)

    print("pass")
    for label in ("checkout", "parent", "diff", "story", "contract", "tests", "boundary",
                  "routes-json"):
        print("%s: %s" % (label, paths[label]))
    print("routes: surface=%s gate3_route=%s planned_surface=%s gate0_route=%s"
          % (routes["surface"], routes["gate3_route"], routes["planned_surface"] or "none",
             routes["gate0_route"]))
    if "gate0_reason" in routes:
        print("gate0_reason: %s" % routes["gate0_reason"])
    if "blast-radius" in paths:
        print("blast-radius: %s" % paths["blast-radius"])
    for arm in ARMS:
        print("arm: %s %s" % (arm, configs[arm]))
    print("gate-upgrade-trial: prepared %s at %s" % (story["story_id"], commit[:12]))
    return 0


# --- CLI ----------------------------------------------------------------------

def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="gate-upgrade-trial.py", description=__doc__,
        formatter_class=argparse.RawDescriptionHelpFormatter)
    sub = parser.add_subparsers(dest="command")
    sub.required = True
    p = sub.add_parser("init", help="write the trial skeleton from the baseline")
    p.add_argument("--baseline", required=True)
    p.add_argument("--out", required=True)
    p.add_argument("--repo", default=".")
    p.add_argument("--force", action="store_true")
    p.add_argument("--yuss", default=None)
    p.set_defaults(func=cmd_init)
    p = sub.add_parser("prepare", help="build one story's read-only inputs and arm configs")
    p.add_argument("--trial", required=True)
    p.add_argument("--story", required=True)
    p.add_argument("--yuss", required=True)
    p.add_argument("--tmp-root", default=None)
    p.set_defaults(func=cmd_prepare)
    return parser


def main(argv: Optional[List[str]] = None) -> int:
    parser = build_parser()
    try:
        args = parser.parse_args(argv)
    except SystemExit as exc:
        return exc.code if isinstance(exc.code, int) else 2
    try:
        return args.func(args)
    except Refusal as exc:
        sys.stderr.write(exc.line() + "\n")
        return 2


if __name__ == "__main__":
    sys.exit(main())
