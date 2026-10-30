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

Subcommands (Story 2):
  record   --trial FILE --story ID --arm ARM --output FILE [--origin MODEL]
           [--state NAME=on|off]... [--report-line TEXT] [--verifier FILE]
           [--kind bug|not-a-bug-fix] [--repro-ac AC-N.M --at-parent pass|fail
           --at-commit pass|fail] [--state-dir DIR]
              Check one arm's evidence, store its finding keys (parsed by
              scripts/review-panel.py), copy the raw output to the state dir,
              and recompute the story's upgrade-only and off-only findings.
  snapshot --trial FILE --yuss PATH
              Record yuss `after` and whether it equals `before`.
  sheet    --trial FILE --out FILE [--seed N] [--force] [--state-dir DIR]
              Give every upgrade-only finding a shuffled ID, write one excerpt
              per finding to <state>/findings/, and write the labeling sheet.
  label    --trial FILE --sheet FILE --labeled-by NAME
              Import a filled sheet whose body is unchanged.
  report   --trial FILE [--json]
              Per-upgrade verdicts (technical-spec § Verdict).

The state dir defaults to `<primary checkout>/.writ/state/gate-upgrade-trial/`
(gitignored); raw reviewer text lives only there and in the excerpts.

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
import random
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
    consonant_y = word.endswith("y") and len(word) > 1 and word[-2] not in "aeiou"
    return "%d %s" % (count, word[:-1] + "ies" if consonant_y else word + "s")


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


# --- Story 2: shared ----------------------------------------------------------

GATE3_ARMS = ("off-1", "off-2", "reviewer-filters", "safety-fact")
OFF_ARMS = ("off-1", "off-2")
# Gate 3 arms must report both review-route switches; every given state must
# read `on` for the arm's own upgrade and `off` for the rest.
REQUIRED_STATES = ("safety-fact", "reviewer-filters")
OFF_ONLY_UPGRADES = ("gate0-divergence", "safety-fact", "reviewer-filters")
SAFETY_HEADING = re.compile(r"^#{1,6}\s*Safety Fact\s*$", re.MULTILINE)
REPRO_HEADING = re.compile(r"^(#{1,6})\s*Repro\s*$")
AVOIDED_BY = re.compile(r"^\s*(?:[-*]\s+)?\*\*Avoided by:\*\*", re.IGNORECASE)
REPRO_AC = re.compile(r"AC-\d+\.\d+")
GATE0_CHOSE = "gate0-divergence: chose"
GATE0_SKIP = "gate0-divergence: skip"
VERIFIER_RESULTS = ("pass", "fail", "unverifiable")
PASS_FAIL = ("pass", "fail")
KINDS = ("bug", "not-a-bug-fix")
LABELS = ("valid", "invalid")
ACKS = ("remove", "amend")
NOTE_MAX = 200
AGENT_WORDS = ("claude", "agent", "gpt", "codex", "cursor", "gemini", "grok", "model", "bot")
STATE_REL = Path(".writ") / "state" / "gate-upgrade-trial"
ISSUES_HEADER = "### Issues Found"
NO_MATCH = "(no matching block found in the raw output)"
EXCERPT_NAME = re.compile(r"^F\d+\.md$")

# Local copies of review-panel.py patterns beyond the four names checked at
# load; the loaded module's own are used when present.
_ISSUES_HEADING = re.compile(r"^(#{2,6})\s*Issues Found\b", re.IGNORECASE)
_ANY_HEADING = re.compile(r"^(#{1,6})\s")
_ISSUE_START = re.compile(r"^\s*(?:[-*]|\d+\.)\s+\*\*Issue:\*\*\s*(.*)$")
_AC_ID = re.compile(r"AC-\d+\.\d+")

SHEET_TITLE = "# Gate Upgrade Trial — Labeling Sheet"
SHEET_HEADER = ("> Fill every `label:` with `valid` or `invalid` (spec.md Business Rule 6), "
                "optionally a one-line `note:` (at most 200 characters, no backticks), and every "
                "`ack:` with `remove` or `amend` (Rule 7). Do not change any other line. See "
                "rating-handoff.md.")
SHEET_FIELD = re.compile(r"^(label|note|ack):.*$", re.MULTILINE)
SHEET_FINDING = re.compile(r"^### (F\d+)$")
SHEET_ACK = re.compile(r"^### not exercised: (\S+)$")

SAMPLE = ("%s, two current-gates runs, one run per upgrade arm; one valid catch keeps an "
          "upgrade — a low bar, not a cost case")
PROXY = ("Gate 0 and Repro First arms are retrospective proxies (sketch comparison, repro "
         "re-run), not replays")
BLINDING = ("honor system — the sheet hides which upgrade raised a finding, but the trial file "
            "and raw outputs map IDs to arms, and Gate 0 excerpts show their Avoided by line")


def story_slug(story_id: str) -> str:
    return story_id.replace("/", "--")


def primary_root() -> Optional[Path]:
    """The primary checkout: the parent of the git common dir, from the cwd."""
    out = _git_text(Path.cwd(), "rev-parse", "--path-format=absolute", "--git-common-dir")
    if out is None or not out.strip():
        return None
    return Path(out.strip()).parent


def resolve_state_dir(value: Optional[str]) -> Path:
    if value:
        return Path(value)
    root = primary_root()
    if root is None:
        raise Refusal("state_dir_unresolved", "git cannot find the primary checkout from %s; "
                      "pass --state-dir" % Path.cwd())
    return root / STATE_REL


def upgrade_present(doc: dict, name: str) -> bool:
    upgrades = doc.get("upgrades")
    entry = upgrades.get(name) if isinstance(upgrades, dict) else None
    return isinstance(entry, dict) and entry.get("present") is True


def _routes(story: dict) -> dict:
    routes = story.get("routes")
    return routes if isinstance(routes, dict) else {}


def story_arms(story: dict) -> dict:
    arms = story.get("arms")
    return arms if isinstance(arms, dict) else {}


def arm_applies(doc: dict, story: dict, arm: str) -> bool:
    """technical-spec § Arms. The story's routes must be set."""
    if arm in OFF_ARMS:
        return True
    if not upgrade_present(doc, arm):
        return False
    if arm == "safety-fact":
        return _routes(story).get("gate3_route") == "review-agent"
    if arm == "gate0-divergence":
        return _routes(story).get("gate0_route") == "review-agent"
    return True


def exercises(story: dict, upgrade: str) -> bool:
    """Business Rule 4, once the story's applicable arms are recorded."""
    if upgrade == "reviewer-filters":
        return True
    if upgrade == "safety-fact":
        return _routes(story).get("gate3_route") == "review-agent"
    if upgrade == "gate0-divergence":
        return (story_arms(story).get(upgrade) or {}).get("report") == "chose"
    return story.get("repro_kind") == "bug"


def checked_stories(doc: dict) -> List[dict]:
    stories = doc["stories"]
    for story in stories:
        if not isinstance(story, dict) or not isinstance(story.get("story_id"), str):
            raise Refusal("trial_invalid", "a story entry lacks a story_id")
    return stories


def first_missing_arm(doc: dict) -> Optional[Tuple[str, str]]:
    """(story, arm) of the first applicable arm not recorded, or (story, "routes")."""
    for story in checked_stories(doc):
        if not isinstance(story.get("routes"), dict):
            return story["story_id"], "routes"
        arms = story_arms(story)
        for arm in ARMS:
            if arm_applies(doc, story, arm) and arm not in arms:
                return story["story_id"], arm
    return None


def not_exercised(doc: dict) -> List[Tuple[str, List[str]]]:
    """Present upgrades no story exercised, with one reason line per story."""
    stories = checked_stories(doc)
    out = []
    for name in UPGRADES:
        if not upgrade_present(doc, name) or any(exercises(s, name) for s in stories):
            continue
        out.append((name, ["- %s: %s" % (s["story_id"], _not_exercised_reason(s, name))
                           for s in stories]))
    return out


def _not_exercised_reason(story: dict, upgrade: str) -> str:
    routes = _routes(story)
    if upgrade == "gate0-divergence":
        if (story_arms(story).get(upgrade) or {}).get("report") == "skip":
            return "skip (gate0-divergence run)"
        route = routes.get("gate0_route") or "none"
        reason = routes.get("gate0_reason")
        return "route %s (%s)" % (route, reason) if route == "skip" and reason else "route %s" % route
    if upgrade == "safety-fact":
        return "route %s" % (routes.get("gate3_route") or "none")
    # repro-first; reviewer-filters runs on every story, so it never gets here
    return story.get("repro_kind") or "not-a-bug-fix"


def _rp_name(rp: ModuleType, name: str, fallback: object) -> object:
    return getattr(rp, name, fallback)


def issue_blocks(rp: ModuleType, text: str) -> List[List[str]]:
    """Issue entries inside an `Issues Found` section, as line blocks: each
    starts at a `**Issue:**` line and runs to the next issue start or heading
    (the same section rule as review-panel.py's parser)."""
    issues_heading = _rp_name(rp, "ISSUES_HEADING", _ISSUES_HEADING)
    any_heading = _rp_name(rp, "ANY_HEADING", _ANY_HEADING)
    issue_start = _rp_name(rp, "ISSUE_START", _ISSUE_START)
    blocks: List[List[str]] = []
    level = 0
    current: Optional[List[str]] = None
    for line in text.splitlines():
        heading = any_heading.match(line)
        if heading:
            issues = issues_heading.match(line)
            if issues:
                level = len(issues.group(1))
            elif level and len(heading.group(1)) <= level:
                level = 0
            current = None
            continue
        if not level:
            continue
        if issue_start.match(line):
            current = [line]
            blocks.append(current)
        elif current is not None:
            current.append(line)
    for block in blocks:
        while block and not block[-1].strip():
            block.pop()
    return blocks


def avoided_text(rp: ModuleType, text: str) -> str:
    """Gate 0: only the issue entries that carry `**Avoided by:**`."""
    kept = ["\n".join(block) for block in issue_blocks(rp, text)
            if any(AVOIDED_BY.match(line) for line in block)]
    return "\n\n".join([ISSUES_HEADER] + kept) + "\n"


def output_keys(rp: ModuleType, text: str) -> List[Dict[str, str]]:
    """Stored keys and severities, through review-panel.py's parser."""
    found: Dict[str, str] = {}
    for raw_key, finding in rp.parse_output(text).findings.items():
        found.setdefault(rp.trial_key(raw_key), finding.severity)
    return [{"key": key, "severity": found[key]} for key in sorted(found, key=rp._key_order)]


# --- record -------------------------------------------------------------------

def _read_bytes(path: Path, code: str, what: str) -> Tuple[bytes, str]:
    try:
        data = path.read_bytes()
        return data, data.decode("utf-8")
    except (OSError, UnicodeDecodeError) as exc:
        raise Refusal(code, "%s unreadable: %s (%s)" % (what, path, exc.__class__.__name__))


def parse_states(values: Optional[Sequence[str]]) -> Dict[str, str]:
    states: Dict[str, str] = {}
    for value in values or []:
        name, sep, state = value.partition("=")
        if not sep or name not in UPGRADES or state not in ("on", "off") or name in states:
            raise Refusal("bad_state", "--state must be <upgrade>=on|off, once per upgrade: %r"
                          % value)
        states[name] = state
    return states


def check_states(arm: str, states: Dict[str, str]) -> None:
    """Line 1 of `review-override.py switch` per arm config: the arm's own
    switch `on`, every other one `off`."""
    if arm in GATE3_ARMS:
        for name in REQUIRED_STATES:
            if name not in states:
                raise Refusal("evidence_mismatch", "the %s arm needs --state %s=%s"
                              % (arm, name, "on" if name == arm else "off"))
    for name, state in states.items():
        want = "on" if name == arm else "off"
        if state != want:
            raise Refusal("evidence_mismatch", "the %s arm needs %s=%s, got %s"
                          % (arm, name, want, state))


def _gate3_entry(rp: ModuleType, args: argparse.Namespace, text: str,
                 states: Dict[str, str]) -> Tuple[dict, Optional[bytes]]:
    arm = args.arm
    verdict = rp.parse_output(text).verdict
    if verdict is None:
        raise Refusal("no_verdict", "the %s output has no EVALUATION_RESULT or REVIEW_RESULT "
                      "line" % arm)
    check_states(arm, states)
    heading = SAFETY_HEADING.search(text) is not None
    entry = {"verdict": verdict, "keys": output_keys(rp, text), "states": states,
             "exercised": True}
    if arm != "safety-fact":
        if heading:
            raise Refusal("evidence_mismatch", "the %s output has a Safety Fact heading" % arm)
        return entry, None
    if not heading:
        raise Refusal("evidence_mismatch", "the safety-fact output has no Safety Fact heading")
    if not args.verifier:
        raise Refusal("verifier_missing", "the safety-fact arm needs --verifier FILE")
    data, verifier_text = _read_bytes(Path(args.verifier), "verifier_missing", "verifier output")
    first = (verifier_text.splitlines() or [""])[0].strip()
    if first not in VERIFIER_RESULTS:
        raise Refusal("evidence_mismatch", "verifier line 1 must be pass, fail, or unverifiable")
    entry["verifier"] = first
    return entry, data


def _gate0_entry(rp: ModuleType, args: argparse.Namespace, text: str,
                 states: Dict[str, str]) -> dict:
    line = (args.report_line or "").strip()
    if line.startswith(GATE0_CHOSE):
        report = "chose"
    elif line.startswith(GATE0_SKIP):
        report = "skip"
    else:
        raise Refusal("evidence_mismatch", "--report-line must start `%s` or `%s`"
                      % (GATE0_CHOSE, GATE0_SKIP))
    check_states(args.arm, states)
    keys = output_keys(rp, avoided_text(rp, text)) if report == "chose" else []
    # Only the word is stored, never the report line's text.
    return {"verdict": rp.parse_output(text).verdict, "keys": keys, "states": states,
            "exercised": report == "chose", "report": report}


def _repro_entry(rp: ModuleType, args: argparse.Namespace, text: str,
                 states: Dict[str, str]) -> dict:
    fields = (args.repro_ac, args.at_parent, args.at_commit)
    if args.kind is None:
        raise Refusal("evidence_mismatch", "the repro-first arm needs --kind")
    if args.kind == "bug":
        if any(value is None for value in fields):
            raise Refusal("evidence_mismatch", "--kind bug needs --repro-ac, --at-parent, and "
                          "--at-commit")
        if not REPRO_AC.fullmatch(args.repro_ac):
            raise Refusal("evidence_mismatch", "--repro-ac must be AC-N.M: %r" % args.repro_ac)
    elif any(value is not None for value in fields):
        raise Refusal("evidence_mismatch", "--kind not-a-bug-fix takes no repro field")
    check_states(args.arm, states)
    keys: List[Dict[str, str]] = []
    result = None
    if args.kind == "bug":
        if args.at_parent == "fail" and args.at_commit == "fail":
            result = "still_fails"
            keys = [{"key": "ac:%s" % args.repro_ac, "severity": "Critical"}]
        else:
            result = "no_repro" if args.at_parent == "pass" else "fixed"
    return {"verdict": rp.parse_output(text).verdict, "keys": keys, "states": states,
            "exercised": args.kind == "bug", "kind": args.kind, "repro_ac": args.repro_ac,
            "at_parent": args.at_parent, "at_commit": args.at_commit, "repro_result": result}


def recompute(story: dict) -> None:
    """The one place `upgrade_only` and `off_only` are computed (technical-spec
    § Upgrade-Only and Off-Only). `id`, `label`, and `note` carry over by
    (upgrade, key) for keys that stay upgrade-only."""
    arms = story_arms(story)

    def keys(arm: str) -> set:
        return {k["key"] for k in (arms.get(arm) or {}).get("keys", [])}

    off_union = keys("off-1") | keys("off-2")
    previous = {(e.get("upgrade"), e.get("key")): e for e in story.get("upgrade_only") or []
                if isinstance(e, dict)}
    found = []
    for upgrade in UPGRADES:
        entry = arms.get(upgrade)
        if not entry or not entry.get("exercised"):
            continue
        for key in entry["keys"]:
            if key["key"] in off_union:
                continue
            old = previous.get((upgrade, key["key"]), {})
            found.append({"id": old.get("id"), "upgrade": upgrade, "key": key["key"],
                          "severity": key["severity"], "label": old.get("label"),
                          "note": old.get("note")})
    story["upgrade_only"] = found
    both_off = all(arm in arms for arm in OFF_ARMS)
    off_both = keys("off-1") & keys("off-2")
    story["off_only"] = {
        upgrade: (len(off_both - keys(upgrade))
                  if both_off and (arms.get(upgrade) or {}).get("exercised") else 0)
        for upgrade in OFF_ONLY_UPGRADES}


def cmd_record(args: argparse.Namespace) -> int:
    rp = load_review_panel()
    trial_path = Path(args.trial)
    doc = load_trial(trial_path)
    story = trial_story(doc, args.story)
    check_identity(story)
    arm = args.arm
    routes = story.get("routes")
    if not isinstance(routes, dict):
        raise Refusal("not_prepared", "%s has no routes; run prepare first" % args.story)
    if not arm_applies(doc, story, arm):
        why = ("upgrade %s is absent" % arm if not upgrade_present(doc, arm) else
               "gate3_route is %s" % routes.get("gate3_route") if arm == "safety-fact" else
               "gate0_route is %s" % routes.get("gate0_route"))
        raise Refusal("arm_not_applicable", "%s does not apply to %s (%s)"
                      % (arm, args.story, why))
    stored_origin = doc.get("origin")
    if args.origin is not None and stored_origin is not None and args.origin != stored_origin:
        raise Refusal("origin_mismatch", "--origin %s differs from the stored origin %s"
                      % (args.origin, stored_origin))
    data, text = _read_bytes(Path(args.output), "output_unreadable", "arm output")
    if not text.strip():
        raise Refusal("output_unreadable", "arm output is empty: %s" % args.output)
    states = parse_states(args.state)
    verifier = None
    if arm in GATE3_ARMS:
        entry, verifier = _gate3_entry(rp, args, text, states)
    elif arm == "gate0-divergence":
        entry = _gate0_entry(rp, args, text, states)
    else:
        entry = _repro_entry(rp, args, text, states)
    state = resolve_state_dir(args.state_dir)

    slug = story_slug(story["story_id"])
    try:
        (state / slug).mkdir(parents=True, exist_ok=True)
        (state / slug / ("%s.md" % arm)).write_bytes(data)
        if verifier is not None:
            (state / slug / "safety-fact-verifier.txt").write_bytes(verifier)
    except OSError as exc:
        raise Refusal("state_dir_unwritable", "%s (%s)" % (state, exc.__class__.__name__))
    entry.update(raw="%s/%s.md" % (slug, arm), raw_sha256=hashlib.sha256(data).hexdigest())
    arms = story_arms(story)
    arms[arm] = entry
    story["arms"] = arms
    if arm == "repro-first":
        story["repro_kind"] = args.kind
    recompute(story)
    if args.origin is not None and stored_origin is None:
        doc["origin"] = args.origin
    write_json_atomic(trial_path, doc)

    count = len(entry["keys"])
    found = len(story["upgrade_only"])
    print("pass")
    print("arm: %s verdict=%s keys=%d exercised=%s" % (
        arm, entry["verdict"] or "none", count, "true" if entry["exercised"] else "false"))
    print("upgrade_only: %d" % found)
    print("gate-upgrade-trial: recorded %s %s — %s, %s" % (
        args.story, arm, _plural(count, "key"), _plural(found, "upgrade-only finding")))
    return 0


# --- snapshot -----------------------------------------------------------------

def cmd_snapshot(args: argparse.Namespace) -> int:
    trial_path = Path(args.trial)
    doc = load_trial(trial_path)
    snap = doc.get("yuss_snapshot")
    if not isinstance(snap, dict) or not snap.get("before"):
        raise Refusal("no_before_snapshot", "the trial file has no yuss before-snapshot "
                      "(init --yuss records it)")
    after = yuss_snapshot(Path(args.yuss))
    unchanged = after == snap["before"]
    snap.update(after=after, unchanged=unchanged)
    write_json_atomic(trial_path, doc)
    word = "unchanged" if unchanged else "changed"
    print("pass" if unchanged else "unverifiable")
    if not unchanged:
        print("reason: yuss_changed")
    print("yuss: %s" % word)
    print("gate-upgrade-trial: yuss snapshot after — %s" % word)
    return 0


# --- sheet --------------------------------------------------------------------

def finding_ids(count: int) -> List[str]:
    width = 3 if count > 99 else 2
    return ["F%0*d" % (width, n) for n in range(1, count + 1)]


def body_hash(text: str) -> str:
    """sha256 of the sheet with every label, note, and ack value blanked."""
    return hashlib.sha256(SHEET_FIELD.sub(r"\1:", text).encode("utf-8")).hexdigest()


def matching_blocks(rp: ModuleType, text: str, key: str) -> List[str]:
    kind, _, rest = key.partition(":")
    out: List[str] = []
    if kind == "ac":
        out = [line.strip() for line in text.splitlines()
               if key in rp.parse_output(line).findings]
    ac_id = _rp_name(rp, "AC_ID", _AC_ID)
    for block in issue_blocks(rp, text):
        body = "\n".join(block)
        if kind == "ac":
            hit = rest in ac_id.findall(body)
        else:
            parsed = rp.parse_output("%s\n%s\n" % (ISSUES_HEADER, body))
            hit = key in {rp.trial_key(k) for k in parsed.findings}
        if hit:
            out.append(body)
    return out


def repro_section(text: str) -> Optional[str]:
    lines = text.splitlines()
    for index, line in enumerate(lines):
        match = REPRO_HEADING.match(line)
        if match is None:
            continue
        section = [line]
        for following in lines[index + 1:]:
            heading = _ANY_HEADING.match(following)
            if heading and len(heading.group(1)) <= len(match.group(1)):
                break
            section.append(following)
        return "\n".join(section).strip("\n")
    return None


def excerpt_text(rp: ModuleType, state: Path, story: dict, entry: dict, fid: str) -> str:
    """The excerpt re-derived from the raw output; it never names the arm."""
    upgrade = entry["upgrade"]
    arm_entry = story_arms(story).get(upgrade) or {}
    raw = state / story_slug(story["story_id"]) / ("%s.md" % upgrade)
    try:
        data = raw.read_bytes()
    except OSError:
        raise Refusal("raw_missing", "raw output not found: %s" % raw)
    if hashlib.sha256(data).hexdigest() != arm_entry.get("raw_sha256"):
        raise Refusal("raw_missing", "raw output differs from its recorded sha256: %s" % raw)
    text = data.decode("utf-8", "replace")
    if upgrade == "repro-first":
        blocks = [repro_section(text) or NO_MATCH,
                  "targets: %s\nat parent: %s\nat commit: %s" % (
                      arm_entry.get("repro_ac"), arm_entry.get("at_parent"),
                      arm_entry.get("at_commit"))]
    else:
        source = avoided_text(rp, text) if upgrade == "gate0-divergence" else text
        blocks = matching_blocks(rp, source, entry["key"]) or [NO_MATCH]
    head = ["# %s" % fid, "story: %s" % story["story_id"], "key: %s" % entry["key"],
            "severity: %s" % entry["severity"], ""]
    return "\n".join(head) + "\n" + "\n\n".join(blocks) + "\n"


def display_path(path: Path, root: Optional[Path]) -> str:
    """Relative to the primary checkout when under it, else absolute."""
    absolute = Path(os.path.abspath(str(path)))
    if root is not None:
        try:
            return absolute.resolve().relative_to(root.resolve()).as_posix()
        except ValueError:
            pass
    return str(absolute)


def sheet_text(stories: List[dict], findings: List[Tuple[str, dict, str, str]],
               acks: List[Tuple[str, List[str]]]) -> str:
    """findings: (id, upgrade-only entry, story id, excerpt path)."""
    lines = [SHEET_TITLE, "", SHEET_HEADER, "", "## Findings", ""]
    if not findings:
        lines += ["(none)", ""]
    for fid, entry, story_id, excerpt in sorted(findings, key=lambda row: row[0]):
        lines += ["### %s" % fid, "story: %s" % story_id, "key: %s" % entry["key"],
                  "severity: %s" % entry["severity"], "excerpt: %s" % excerpt,
                  "label:", "note:", ""]
    lines += ["## Not exercised", ""]
    if not acks:
        lines += ["(none)", ""]
    for name, reasons in acks:
        lines += ["### not exercised: %s" % name, "exercised: 0/%d" % len(stories)]
        lines += reasons + ["ack:", ""]
    return "\n".join(lines).rstrip("\n") + "\n"


def write_text_atomic(path: Path, text: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    tmp = path.with_name(".%s.tmp" % path.name)
    try:
        tmp.write_text(text, encoding="utf-8")
        os.replace(str(tmp), str(path))
    finally:
        if tmp.exists():
            tmp.unlink()


def cmd_sheet(args: argparse.Namespace) -> int:
    rp = load_review_panel()
    trial_path = Path(args.trial)
    doc = load_trial(trial_path)
    if doc.get("sheet") and not args.force:
        raise Refusal("sheet_recorded", "the trial file already records a sheet; pass --force "
                      "to rewrite it")
    missing = first_missing_arm(doc)
    if missing is not None:
        raise Refusal("missing_arm", "%s %s" % missing)
    stories = checked_stories(doc)
    state = resolve_state_dir(args.state_dir)
    seed = args.seed if args.seed is not None else random.SystemRandom().randrange(1, 2 ** 31)

    ordered = []
    for index, story in enumerate(stories):
        for entry in story.get("upgrade_only") or []:
            ordered.append(((index, UPGRADES.index(entry["upgrade"]),
                             rp._key_order(entry["key"])), story, entry))
    ordered.sort(key=lambda row: row[0])
    pairs = [(story, entry) for _, story, entry in ordered]
    random.Random(seed).shuffle(pairs)
    ids = finding_ids(len(pairs))
    findings_dir = state / "findings"
    root = primary_root()
    excerpts = {fid: excerpt_text(rp, state, story, entry, fid)
                for fid, (story, entry) in zip(ids, pairs)}
    rows = [(fid, entry, story["story_id"],
             display_path(findings_dir / ("%s.md" % fid), root))
            for fid, (story, entry) in zip(ids, pairs)]
    acks = not_exercised(doc)
    text = sheet_text(stories, rows, acks)

    try:
        findings_dir.mkdir(parents=True, exist_ok=True)
        for stale in findings_dir.iterdir():
            if EXCERPT_NAME.match(stale.name):
                stale.unlink()
        for fid, excerpt in excerpts.items():
            (findings_dir / ("%s.md" % fid)).write_text(excerpt, encoding="utf-8")
    except OSError as exc:
        raise Refusal("state_dir_unwritable", "%s (%s)" % (findings_dir, exc.__class__.__name__))
    write_text_atomic(Path(args.out), text)
    for fid, (_story, entry) in zip(ids, pairs):
        entry["id"] = fid
    doc["sheet"] = {"path": args.out, "body_sha256": body_hash(text), "seed": seed,
                    "findings": len(ids)}
    write_json_atomic(trial_path, doc)

    print("pass")
    print("sheet: %s" % args.out)
    print("findings: %d" % len(ids))
    print("not_exercised: %s" % (", ".join(name for name, _ in acks) or "none"))
    print("excerpts: %s" % findings_dir)
    print("gate-upgrade-trial: sheet written — %s, %s" % (
        _plural(len(ids), "finding"), _plural(len(acks), "acknowledgment")))
    return 0


# --- label --------------------------------------------------------------------

def parse_sheet(text: str) -> Tuple[Dict[str, Dict[str, str]], Dict[str, str]]:
    """({id: {label, note}}, {upgrade: ack}) with raw values after the colon."""
    findings: Dict[str, Dict[str, str]] = {}
    acks: Dict[str, str] = {}
    current_id: Optional[str] = None
    current_ack: Optional[str] = None
    for line in text.split("\n"):
        finding = SHEET_FINDING.match(line)
        ack = SHEET_ACK.match(line)
        if finding:
            current_id, current_ack = finding.group(1), None
            findings[current_id] = {}
        elif ack:
            current_id, current_ack = None, ack.group(1)
        elif line.startswith("#"):
            current_id = current_ack = None
        elif current_id is not None and line.startswith(("label:", "note:")):
            field, _, value = line.partition(":")
            findings[current_id][field] = value
        elif current_ack is not None and line.startswith("ack:"):
            acks[current_ack] = line[len("ack:"):]
    return findings, acks


def cmd_label(args: argparse.Namespace) -> int:
    name = args.labeled_by.strip()
    if (not name or any(word in name.lower() for word in AGENT_WORDS)
            or any(char in name for char in "\r\n`")):
        raise Refusal("labeled_by_invalid", "--labeled-by must name the human who labeled the "
                      "sheet, not an agent or model: %r" % args.labeled_by)
    trial_path = Path(args.trial)
    doc = load_trial(trial_path)
    sheet = doc.get("sheet")
    if not isinstance(sheet, dict) or not sheet.get("body_sha256"):
        raise Refusal("no_sheet", "the trial file records no sheet; run sheet first")
    _, text = _read_bytes(Path(args.sheet), "sheet_unreadable", "sheet")
    if body_hash(text) != sheet["body_sha256"]:
        raise Refusal("sheet_changed", "%s differs from the sheet `sheet` wrote beyond its "
                      "label, note, and ack values" % args.sheet)
    fields, acks = parse_sheet(text)
    entries = [e for s in checked_stories(doc) for e in s.get("upgrade_only") or []]
    ids = [e.get("id") for e in entries]
    stale = [name for name, _ in not_exercised(doc)]
    if None in ids or sorted(ids) != sorted(fields) or sorted(stale) != sorted(acks):
        raise Refusal("sheet_stale", "a record ran after sheet: the trial's findings or "
                      "not-exercised upgrades differ from the sheet; run sheet --force")
    labels: Dict[str, Tuple[str, str]] = {}
    for fid in sorted(fields):
        label = fields[fid].get("label", "").strip()
        raw_note = fields[fid].get("note", "")
        note = raw_note.strip()
        if label not in LABELS:
            raise Refusal("bad_field", "%s label must be valid or invalid" % fid)
        if "\r" in raw_note or "`" in note or len(note) > NOTE_MAX:
            raise Refusal("bad_field", "%s note must be one line of at most %d characters "
                          "with no backtick" % (fid, NOTE_MAX))
        labels[fid] = (label, note)
    words: Dict[str, str] = {}
    for upgrade in UPGRADES:
        if upgrade not in acks:
            continue
        word = acks[upgrade].strip()
        if word not in ACKS:
            raise Refusal("bad_field", "ack for %s must be remove or amend" % upgrade)
        words[upgrade] = word
    for entry in entries:
        entry["label"], entry["note"] = labels[entry["id"]]
    doc["acks"] = words
    doc["labeled_by"] = name
    write_json_atomic(trial_path, doc)

    valid = sum(1 for label, _ in labels.values() if label == "valid")
    print("pass")
    print("labeled: %d (valid %d, invalid %d)" % (len(labels), valid, len(labels) - valid))
    print("acks: %s" % (" ".join("%s=%s" % pair for pair in words.items()) or "none"))
    print("labeled_by: %s" % name)
    print("gate-upgrade-trial: labels stored — %s, %s" % (
        _plural(len(labels), "finding"), _plural(len(words), "acknowledgment")))
    return 0


# --- report -------------------------------------------------------------------

def _missing_for(doc: dict, stories: List[dict], upgrade: str) -> Optional[str]:
    for story in stories:
        if not isinstance(story.get("routes"), dict):
            return "%s routes" % story["story_id"]
        if arm_applies(doc, story, upgrade):
            arms = story_arms(story)
            for arm in (upgrade,) + OFF_ARMS:
                if arm not in arms:
                    return "%s %s" % (story["story_id"], arm)
    return None


def upgrade_verdict(doc: dict, stories: List[dict], name: str) -> dict:
    """technical-spec § Verdict, steps 1-6 in order, for one upgrade."""
    row: Dict[str, object] = {"name": name, "verdict": None, "exercised": None,
                              "upgrade_only": None, "valid": None, "invalid": None,
                              "off_only": None, "reason": None}
    if not upgrade_present(doc, name):
        row["verdict"] = "absent"
        return row
    missing = _missing_for(doc, stories, name)
    if missing is not None:
        row.update(verdict="unverifiable", reason="missing_arm %s" % missing)
        return row
    exercised = sum(1 for story in stories if exercises(story, name))
    row["exercised"] = exercised
    if exercised == 0:
        acks = doc.get("acks") if isinstance(doc.get("acks"), dict) else {}
        ack = acks.get(name)
        if ack == "remove":
            row.update(verdict="remove", reason="not_exercised")
        elif ack == "amend":
            row.update(verdict="unverifiable", reason="amendment_requested")
        else:
            row.update(verdict="unverifiable", reason="not_exercised_unacknowledged")
        return row
    findings = [e for story in stories for e in story.get("upgrade_only") or []
                if isinstance(e, dict) and e.get("upgrade") == name]
    valid = sum(1 for e in findings if e.get("label") == "valid")
    invalid = sum(1 for e in findings if e.get("label") == "invalid")
    off_only = 0
    for story in stories:
        counts = story.get("off_only")
        value = counts.get(name, 0) if isinstance(counts, dict) else 0
        off_only += value if isinstance(value, int) else 0
    row.update(upgrade_only=len(findings), valid=valid, invalid=invalid, off_only=off_only)
    labeled = bool(doc.get("labeled_by"))
    unlabeled = len(findings) if not labeled else len(findings) - valid - invalid
    if not labeled or unlabeled:
        row.update(verdict="unverifiable", reason="unlabeled %d" % unlabeled)
    else:
        row["verdict"] = "keep" if valid else "remove"
    return row


def trial_report(doc: dict) -> dict:
    """The whole report as data; the text and `--json` outputs render it."""
    stories = checked_stories(doc)
    rows = [upgrade_verdict(doc, stories, name) for name in UPGRADES]
    story_rows = []
    for story in stories:
        routes = _routes(story)
        arms = story_arms(story)
        story_rows.append({"story_id": story["story_id"],
                           "gate3_route": routes.get("gate3_route"),
                           "gate0_route": routes.get("gate0_route"),
                           "repro": story.get("repro_kind"),
                           "arms": [arm for arm in ARMS if arm in arms]})
    counts = {word: sum(1 for row in rows if row["verdict"] == word)
              for word in ("keep", "remove", "unverifiable", "absent")}
    snap = doc.get("yuss_snapshot") if isinstance(doc.get("yuss_snapshot"), dict) else {}
    unchanged = snap.get("unchanged")
    yuss = "unchanged" if unchanged is True else "changed" if unchanged is False else "not checked"
    return {
        "verdict": "unverifiable" if counts["unverifiable"] else "pass",
        "reasons": ["%s %s" % (row["name"], row["reason"]) for row in rows
                    if row["verdict"] == "unverifiable"],
        "stories": story_rows,
        "upgrades": rows,
        "sample": SAMPLE % _plural(len(stories), "story"),
        "proxy": PROXY,
        "blinding": BLINDING,
        "yuss": yuss,
        "summary": "gate-upgrade-trial: keep %d, remove %d, unverifiable %d, absent %d — %s" % (
            counts["keep"], counts["remove"], counts["unverifiable"], counts["absent"],
            _plural(len(stories), "story")),
    }


def upgrade_line(row: dict, total: int) -> str:
    line = "upgrade: %s verdict=%s" % (row["name"], row["verdict"])
    if row["exercised"] is not None:
        line += " exercised=%d/%d" % (row["exercised"], total)
    if row["upgrade_only"] is not None:
        line += " upgrade_only=%d valid=%d invalid=%d off_only=%d" % (
            row["upgrade_only"], row["valid"], row["invalid"], row["off_only"])
    if row["reason"]:
        line += " reason=%s" % row["reason"]
    return line


def cmd_report(args: argparse.Namespace) -> int:
    report = trial_report(load_trial(Path(args.trial)))
    if args.json:
        print(json.dumps(report, sort_keys=True))
        return 0
    lines = [report["verdict"]]
    lines += ["reason: %s" % reason for reason in report["reasons"]]
    for story in report["stories"]:
        lines.append("story: %s gate3_route=%s gate0_route=%s repro=%s arms=%s" % (
            story["story_id"], story["gate3_route"] or "none", story["gate0_route"] or "none",
            story["repro"] or "none", ",".join(story["arms"]) or "none"))
    lines += [upgrade_line(row, len(report["stories"])) for row in report["upgrades"]]
    lines += ["sample: %s" % report["sample"], "proxy: %s" % report["proxy"],
              "blinding: %s" % report["blinding"], "yuss: %s" % report["yuss"],
              report["summary"]]
    print("\n".join(lines))
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
    p = sub.add_parser("record", help="check and store one arm's evidence and keys")
    p.add_argument("--trial", required=True)
    p.add_argument("--story", required=True)
    p.add_argument("--arm", required=True, choices=ARMS)
    p.add_argument("--output", required=True)
    p.add_argument("--origin", default=None)
    p.add_argument("--state", action="append", metavar="NAME=on|off")
    p.add_argument("--report-line", default=None)
    p.add_argument("--verifier", default=None)
    p.add_argument("--kind", choices=KINDS, default=None)
    p.add_argument("--repro-ac", default=None)
    p.add_argument("--at-parent", choices=PASS_FAIL, default=None)
    p.add_argument("--at-commit", choices=PASS_FAIL, default=None)
    p.add_argument("--state-dir", default=None)
    p.set_defaults(func=cmd_record)
    p = sub.add_parser("snapshot", help="record the yuss after-snapshot")
    p.add_argument("--trial", required=True)
    p.add_argument("--yuss", required=True)
    p.set_defaults(func=cmd_snapshot)
    p = sub.add_parser("sheet", help="write the labeling sheet and excerpts")
    p.add_argument("--trial", required=True)
    p.add_argument("--out", required=True)
    p.add_argument("--seed", type=int, default=None)
    p.add_argument("--force", action="store_true")
    p.add_argument("--state-dir", default=None)
    p.set_defaults(func=cmd_sheet)
    p = sub.add_parser("label", help="import a filled labeling sheet")
    p.add_argument("--trial", required=True)
    p.add_argument("--sheet", required=True)
    p.add_argument("--labeled-by", required=True)
    p.set_defaults(func=cmd_label)
    p = sub.add_parser("report", help="per-upgrade verdicts")
    p.add_argument("--trial", required=True)
    p.add_argument("--json", action="store_true")
    p.set_defaults(func=cmd_report)
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
