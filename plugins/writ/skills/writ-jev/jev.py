#!/usr/bin/env python3
"""Jev: the calibrated second reader of a Writ contract and proof. Optional.

  jev.py status [--repo DIR]
  jev.py setup <typesafe|vercel-gateway|none> [--repo DIR]
  jev.py contract <path/to/spec.md> [--repo DIR] [--json]
  jev.py proof <path/to/spec.md> [--repo DIR] [--json]

--repo is the project root holding `.writ/config.md`. Default for `contract`
and `proof`: the nearest folder above the spec that holds `.writ/`, so the
opt-in is always read from the project that owns the spec. Default for
`status` and `setup`: the current directory.

`contract` reads a spec before a person agrees it and flags criteria that are
unclear, out of scope, or contradict each other, and a contract with a gap or
no measure. `proof` reads the Proof section before a person relies on it and
flags `Proved` rows whose evidence does not show the criterion or only asserts
it, `Needs a person` rows a check could decide, and criteria with no row. Each
sends ONE request of narrow yes/no questions to TypeSafe's Jev and compares the
probabilities with thresholds.json. Jev never decides, routes, or acts: a flag
means "read this line again".

Output: line 1 is `flag`, `pass`, or `off`. Then one line per flag
(`A2 unclear 0.81 — reason`), weaker `check A3 ...` lines for borderline
answers (not counted in line 1), `reason:` lines when `off`, and a `jev:`
summary last. `--json` prints one JSON document with every probability.
Exit 0 for flag, pass, and off: the check is advisory and never blocks a run.
Exit 2 for usage errors only.

On only when `.writ/config.md` has `- **Judgment Provider:** <backend>` AND
that backend's API key env var is set; a key alone never enables it. A key
value is never printed, logged, or written. WRIT_JEV_REPLAY=<dir> serves
`<sha256 of the request body>.json` from disk and never opens a socket.
"""

from __future__ import annotations

import argparse
import fnmatch
import hashlib
import http.client
import itertools
import json
import os
import re
import socket
import sys
import time
import urllib.error
import urllib.request
from pathlib import Path
from typing import Any, Callable, Dict, List, Mapping, NamedTuple, Optional, Tuple

# ---- Backends and the double opt-in ---------------------------------------

CONFIG_LINE = re.compile(r"^- \*\*Judgment Provider:\*\*\s*(\S+)", re.MULTILINE)
PROVIDER_PREFIX = "- **Judgment Provider:**"
CONVENTIONS_HEADING = "## Conventions"
REPLAY_ENV = "WRIT_JEV_REPLAY"


class Backend(NamedTuple):
    name: str
    base_url: str
    key_vars: Tuple[str, ...]  # first non-empty wins
    model: str
    pinned: bool  # True: the response must name exactly this model


# Both take POST <base_url>/v1/systemone with the native TypeSafe body. The
# gateway accepts only its alias and echoes it back, so the Jev version behind
# it is not visible; thresholds.json records what it was fitted on.
BACKENDS: Dict[str, Backend] = {
    "typesafe": Backend("typesafe", "https://api.typesafe.ai",
                        ("TYPESAFE_API_KEY",), "jev-1.14.0", True),
    "vercel-gateway": Backend("vercel-gateway", "https://ai-gateway.vercel.sh/typesafe",
                              ("AI_GATEWAY_API_KEY", "VERCEL_OIDC_TOKEN"),
                              "typesafe-ai/jev", False),
}
SETUP_PROVIDERS = tuple(sorted(BACKENDS)) + ("none",)


class UsageError(Exception):
    """Exit-2 conditions."""


class Resolution(NamedTuple):
    ok: bool
    reason: str
    backend: Optional[Backend]
    key_var: Optional[str]  # env var NAME holding the key; never the value


def _key_var(backend: Backend, environ: Mapping[str, str]) -> Optional[str]:
    return next((v for v in backend.key_vars if environ.get(v, "").strip()), None)


def resolve(repo: Path, environ: Mapping[str, str]) -> Resolution:
    """Config line naming a backend AND that backend's key. The config value is
    never echoed: a key pasted there by mistake must not reach output. Replay
    needs the config line only, since it sends nothing."""
    try:
        match = CONFIG_LINE.search((repo / ".writ" / "config.md").read_text(encoding="utf-8"))
    except (OSError, UnicodeDecodeError):
        match = None
    if match is None:
        return Resolution(False, "no_config_line", None, None)
    backend = BACKENDS.get(match.group(1).lower())
    if backend is None:
        return Resolution(False, "provider_disabled", None, None)
    if environ.get(REPLAY_ENV, ""):
        return Resolution(True, "replay", backend, None)
    var = _key_var(backend, environ)
    if var is None:
        return Resolution(False, "no_api_key", backend, None)
    return Resolution(True, "enabled", backend, var)


def _off_summary(reason: str, backend: Optional[Backend]) -> str:
    tail = " export=%s" % backend.key_vars[0] if backend and reason == "no_api_key" else ""
    return "jev: off (%s) backend=%s%s" % (reason, backend.name if backend else "none", tail)


def status(repo: Path, environ: Mapping[str, str]) -> int:
    res = resolve(repo, environ)
    print("%s\nreason: %s" % ("ready" if res.ok else "off", res.reason))
    if res.ok and res.backend:
        print("jev: ready backend=%s model=%s key_env=%s"
              % (res.backend.name, res.backend.model, res.key_var or "none"))
    else:
        print(_off_summary(res.reason, res.backend))
    return 0


def set_provider_line(text: str, provider: str) -> str:
    """`text` with exactly one Judgment Provider line: an existing line is
    replaced in place (later duplicates dropped), else the line goes after the
    last bullet under `## Conventions`, and a missing section is appended."""
    line = "%s %s\n" % (PROVIDER_PREFIX, provider)
    lines = text.splitlines(keepends=True)
    hits = [i for i, ln in enumerate(lines) if ln.startswith(PROVIDER_PREFIX)]
    if hits:
        lines[hits[0]] = line
        return "".join(ln for i, ln in enumerate(lines) if i not in hits[1:])
    if lines and not lines[-1].endswith("\n"):
        lines[-1] += "\n"
    head = next((i for i, ln in enumerate(lines) if ln.strip() == CONVENTIONS_HEADING), None)
    if head is None:
        return "".join(lines) + ("\n" if lines else "") + CONVENTIONS_HEADING + "\n\n" + line
    end = next((i for i in range(head + 1, len(lines)) if lines[i].startswith("#")),
               len(lines))
    bullets = [i for i in range(head + 1, end) if lines[i].startswith("- ")]
    if bullets:
        lines.insert(bullets[-1] + 1, line)
    else:
        lines[head + 1:head + 1] = ["\n", line]
    return "".join(lines)


def setup(repo: Path, provider: str) -> int:
    """Write the config line and name the env var to export. Reads no key."""
    config = repo / ".writ" / "config.md"
    try:
        text = config.read_text(encoding="utf-8") if config.exists() else ""
        config.parent.mkdir(parents=True, exist_ok=True)
        config.write_text(set_provider_line(text, provider), encoding="utf-8")
    except (OSError, UnicodeDecodeError) as exc:
        raise UsageError("cannot update %s: %s" % (config, type(exc).__name__))
    backend = BACKENDS.get(provider)
    print("configured")
    if backend is None:
        print("jev: provider=none (Jev is off; nothing to export)")
    else:
        print("jev: provider=%s export=%s (set that variable in your shell or secret "
              "manager; never paste a key into chat)" % (backend.name, backend.key_vars[0]))
    return 0


# ---- Transport: one batched request, retries, redaction, replay -----------

API_PATH = "/v1/systemone"
TIMEOUT_SECONDS = 10
MAX_ATTEMPTS = 3
BACKOFF_SECONDS = (1, 2, 4)
RETRY_AFTER_CAP_SECONDS = 30.0  # a hostile or buggy retry-after cannot hang a run
RETRY_STATUSES = (429, 529)
QUESTION_BUDGET = 30000  # tokens, state + one question; Jev allows 32k
REQUEST_BUDGET = 60000  # tokens, state + every question; Jev allows 64k
ERROR_BODY_LIMIT = 300
SAFE_TOKEN = re.compile(r"[A-Za-z0-9._/:-]{1,64}")


class HttpResponse(NamedTuple):
    status: int
    headers: Mapping[str, str]  # keys lowercased
    body: bytes


class TransportFailure(Exception):
    """Network, DNS, timeout, or connection failure: no HTTP status."""


class ReplayMiss(Exception):
    """No recorded response for the request hash."""


Transport = Callable[[str, Dict[str, str], bytes], HttpResponse]


class Judgment(NamedTuple):
    ok: bool
    reason: str
    answers: Optional[Dict[str, Any]] = None
    model: Optional[str] = None  # the model name the response carries
    input_tokens: Optional[int] = None
    attempts: int = 0
    request_bytes: int = 0
    seconds: float = 0.0


def build_body(state: Mapping[str, Any], questions: Mapping[str, Any],
               backend: Backend) -> Dict[str, Any]:
    body: Dict[str, Any] = {"model": backend.model, "state": state, "questions": questions}
    if backend.name == "vercel-gateway":
        # The state reaches only Vercel and TypeSafe, never a fallback provider.
        body["providerOptions"] = {"gateway": {"only": ["typesafe-ai"]}}
    return body


def canonical_body(body: Mapping[str, Any]) -> bytes:
    """The bytes sent, and the replay hash input."""
    return json.dumps(body, sort_keys=True, separators=(",", ":")).encode("utf-8")


def request_hash(payload: bytes) -> str:
    return hashlib.sha256(payload).hexdigest()


def over_budget(state: Mapping[str, Any], questions: Mapping[str, Any]) -> bool:
    """Rough token counts (characters / 4) against both of Jev's context limits."""
    sizes = [len(json.dumps(q)) for q in questions.values()]
    base = len(json.dumps(state))
    return ((base + max(sizes, default=0)) / 4 > QUESTION_BUDGET
            or (base + sum(sizes)) / 4 > REQUEST_BUDGET)


def _lower(headers: Any) -> Dict[str, str]:
    return {str(k).lower(): str(v) for k, v in headers.items()} if headers else {}


def live_transport(url: str, headers: Dict[str, str], payload: bytes) -> HttpResponse:
    req = urllib.request.Request(url, data=payload, headers=headers, method="POST")
    try:
        with urllib.request.urlopen(req, timeout=TIMEOUT_SECONDS) as resp:
            return HttpResponse(resp.getcode(), _lower(resp.headers), resp.read())
    except urllib.error.HTTPError as exc:  # before URLError: it is a subclass
        try:
            body = exc.read() or b""
        except (OSError, http.client.HTTPException):
            body = b""
        return HttpResponse(exc.code, _lower(exc.headers), body)
    except (urllib.error.URLError, socket.timeout, OSError,
            http.client.HTTPException, ValueError) as exc:
        raise TransportFailure(type(exc).__name__)


def replay_transport(directory: str) -> Transport:
    def _replay(_url: str, _headers: Dict[str, str], payload: bytes) -> HttpResponse:
        try:
            return HttpResponse(200, {}, (Path(directory) / (
                "%s.json" % request_hash(payload))).read_bytes())
        except OSError:
            raise ReplayMiss()
    return _replay


def _retry_delay(headers: Mapping[str, str], attempt: int) -> float:
    try:
        value = float(headers.get("retry-after", "").strip())
    except ValueError:
        value = -1.0
    if value >= 0:
        return min(value, RETRY_AFTER_CAP_SECONDS)
    return BACKOFF_SECONDS[min(attempt - 1, len(BACKOFF_SECONDS) - 1)]


def _one_line(text: str, secret: Optional[str]) -> str:
    """Server text for stderr: key redacted first, then control chars escaped."""
    if secret:
        text = text.replace(secret, "[redacted]")
    return text.encode("unicode_escape").decode("ascii")[:ERROR_BODY_LIMIT]


def _unit(value: Any) -> bool:
    return (isinstance(value, (int, float)) and not isinstance(value, bool)
            and 0.0 <= value <= 1.0)


def judge(state: Mapping[str, Any], questions: Mapping[str, Any], backend: Backend,
          environ: Mapping[str, str], transport: Optional[Transport] = None,
          sleep: Callable[[float], None] = time.sleep) -> Judgment:
    """One request. Never raises for an HTTP or network outcome. Replay always
    wins over an injected or live transport, so tests cannot reach the network."""
    if over_budget(state, questions):
        return Judgment(False, "state_too_large")
    headers = {"Content-Type": "application/json"}
    secret: Optional[str] = None
    if environ.get(REPLAY_ENV, ""):
        send = replay_transport(environ[REPLAY_ENV])
    else:
        key_var = _key_var(backend, environ)
        if key_var is None:
            return Judgment(False, "no_api_key")
        secret = environ[key_var].strip()
        headers["Authorization"] = "Bearer %s" % secret
        send = transport or live_transport
    payload = canonical_body(build_body(state, questions, backend))
    attempts, started = 0, time.time()

    def fail(reason: str) -> Judgment:
        return Judgment(False, reason, attempts=attempts, request_bytes=len(payload))

    while True:
        attempts += 1
        try:
            resp = send(backend.base_url + API_PATH, headers, payload)
        except ReplayMiss:
            return fail("replay_miss")
        except TransportFailure as exc:
            print("jev: transport_error %s" % _one_line(str(exc), secret), file=sys.stderr)
            return fail("transport_error")
        if resp.status in RETRY_STATUSES and attempts < MAX_ATTEMPTS:
            sleep(_retry_delay(resp.headers, attempts))
            continue
        break
    if resp.status in RETRY_STATUSES:
        return fail("rate_limited")
    if resp.status != 200:
        print("jev: http %d body=%s" % (resp.status, _one_line(
            resp.body.decode("utf-8", errors="replace"), secret)), file=sys.stderr)
        if resp.status in (401, 403):
            return fail("auth_error")
        return fail("request_invalid" if 400 <= resp.status < 500 else "transport_error")
    try:
        data = json.loads(resp.body.decode("utf-8"))
    except (UnicodeDecodeError, ValueError):
        data = None
    if not isinstance(data, dict):
        return fail("malformed_response")
    if backend.pinned and data.get("model") != backend.model:
        return fail("model_mismatch")  # another model's answers are never applied
    answers = data.get("answers")
    if not isinstance(answers, dict) or not all(
            isinstance(answers.get(q), dict) and _unit(answers[q].get("noul"))
            for q in questions):
        return fail("malformed_response")
    model = data.get("model")  # printed later, so only a safe token survives
    model = model if isinstance(model, str) and SAFE_TOKEN.fullmatch(model) and not (
        secret and secret in model) else None
    usage = data.get("usage")
    tokens = usage.get("input_tokens") if isinstance(usage, dict) else None
    return Judgment(True, "judged", answers, model, tokens if type(tokens) is int else None,
                    attempts, len(payload), time.time() - started)


# ---- The spec file: contract sections, criteria, proof rows, evidence -----

CRITERION = re.compile(r"^- \*\*(A\d+)\.\*\*\s*(.*)$")
ROW = re.compile(r"^- \*\*(A\d+)\.\s*(Proved|Not proved|Needs a person)\.?\*\*\s*(.*)$",
                 re.IGNORECASE)
MEASURE = re.compile(r"^\*\*Measure:\*\*\s*(.*)$", re.IGNORECASE)
SCOPE_MARK = re.compile(r"^\*\*(In|Out):?\*\*:?\s*(.*)$", re.IGNORECASE)
EVIDENCE_REF = re.compile(r"proof/[A-Za-z0-9_./-]*[A-Za-z0-9_]")
SECRET_PATTERNS = (".env*", "*.pem", "*.key", "*secret*", "*credential*")
FILE_HEAD, FILE_TAIL = 2500, 1500  # characters kept from each evidence file
MAX_FILES = 12
MAX_PAIR_CRITERIA = 16  # above this, 120+ pair questions: ask the whole-list one only


class Spec(NamedTuple):
    problem: str
    outcome: str
    measure: str  # "" when the Outcome has no **Measure:** line
    scope_in: List[str]
    scope_out: List[str]
    criteria: Dict[str, str]
    rows: Dict[str, Tuple[str, str]]  # id -> (verdict lowercased, evidence)


def sections(text: str) -> Dict[str, List[str]]:
    """Level-2 sections by lowercased heading. Fenced code is never a heading."""
    out: Dict[str, List[str]] = {}
    current: Optional[List[str]] = None
    fenced = False
    for line in text.splitlines():
        if line.lstrip().startswith("```"):
            fenced = not fenced
        if not fenced and line.startswith("## "):
            current = out.setdefault(line[3:].strip().strip("#").strip().lower(), [])
        elif current is not None:
            current.append(line)
    return out


def _items(lines: List[str], pattern: "re.Pattern[str]") -> List[Tuple[str, ...]]:
    """Bullets matching `pattern`, each joined with its continuation lines:
    everything up to the next top-level bullet or heading."""
    found: List[List[str]] = []
    open_item = False
    for line in lines:
        match = pattern.match(line)
        if match:
            found.append([g.strip() for g in match.groups()])
            open_item = True
        elif line.startswith(("- ", "* ", "#")):
            open_item = False
        elif open_item and line.strip():
            found[-1][-1] = (found[-1][-1] + " " + line.strip()).strip()
    return [tuple(item) for item in found]


def _prose(lines: List[str]) -> str:
    return " ".join(ln.strip() for ln in lines if ln.strip())


def parse_spec(text: str) -> Spec:
    sec = sections(text)
    outcome: List[str] = []
    measure: List[str] = []
    in_measure = False
    for line in sec.get("outcome", []):
        match = MEASURE.match(line.strip())
        if match:
            measure, in_measure = [match.group(1)], True
        elif in_measure and line.strip():
            measure.append(line)
        else:
            in_measure = False
            outcome.append(line)
    scope: Dict[str, List[str]] = {"in": [], "out": []}
    side = ""
    for line in sec.get("scope", []):
        mark = SCOPE_MARK.match(line.strip())
        if mark:
            side = mark.group(1).lower()
            scope[side] += [mark.group(2).strip()] if mark.group(2).strip() else []
        elif side and line.startswith(("- ", "* ")):
            scope[side].append(line[2:].strip())
        elif side and line.strip() and scope[side]:
            scope[side][-1] += " " + line.strip()
    criteria: Dict[str, str] = {}
    for cid, body in _items(sec.get("acceptance criteria", []), CRITERION):
        criteria.setdefault(cid, body)
    rows: Dict[str, Tuple[str, str]] = {}
    for rid, verdict, body in _items(sec.get("proof", []), ROW):
        rows.setdefault(rid, (verdict.lower(), body))
    return Spec(_prose(sec.get("problem", [])), _prose(outcome), _prose(measure),
                scope["in"], scope["out"], criteria, rows)


def is_secret_path(path: str) -> bool:
    lowered = path.lower()
    return any(fnmatch.fnmatchcase(part, pattern) for pattern in SECRET_PATTERNS
               for part in [lowered] + lowered.split("/"))


def read_evidence(spec_dir: Path, evidence: str) -> Tuple[Dict[str, str], List[Dict[str, str]]]:
    """Text files under `proof/` that a row names, cut to head and tail.
    Skipped, with a reason: secret-looking names, anything outside `proof/`,
    missing files, and binary or empty files."""
    kept: Dict[str, str] = {}
    skipped: List[Dict[str, str]] = []
    root = (spec_dir / "proof").resolve()
    for ref in dict.fromkeys(EVIDENCE_REF.findall(evidence)):
        path = (spec_dir / ref).resolve()
        text = ""
        if is_secret_path(ref) or is_secret_path(path.name):
            why = "secret_pattern"
        elif root not in path.parents:
            why = "outside_proof"
        elif not path.is_file():
            why = "not_found"
        else:
            try:
                raw = path.read_bytes()
                text = "" if b"\0" in raw[:8192] else raw.decode("utf-8")
            except (OSError, UnicodeDecodeError):
                pass
            why = "" if text.strip() else "binary_or_empty"
        if why:
            skipped.append({"file": ref, "why": why})
        elif len(text) > FILE_HEAD + FILE_TAIL:
            kept[ref] = "%s\n[... %d characters cut ...]\n%s" % (
                text[:FILE_HEAD], len(text) - FILE_HEAD - FILE_TAIL, text[-FILE_TAIL:])
        else:
            kept[ref] = text
    return kept, skipped


# ---- Questions -------------------------------------------------------------
# Jev reads literally and is weak at indirection and counting, so each question
# names the exact state path it reads, in backticks, and puts the boundary
# cases in the criteria. {c} and {d} are criterion paths; {r} is a proof-row
# path. Any wording change changes every replay hash and needs thresholds.json
# refitted (scripts/tests/fixtures/jev/calibrate.py).

WORDING: Dict[str, Tuple[str, str, str]] = {  # code: (question, yes means, no means)
    "unclear": (
        "Does {c} fail to decide the result it is about, so two people could build "
        "opposite behaviours and both satisfy it?",
        "Either {c} rests on a judgment word with no number or example (such as 'fast', "
        "'intuitive', 'robust', 'properly', 'appropriate', 'easy'), or it sets up a "
        "situation and names no result someone can see or measure. Two builders could "
        "build opposite behaviours and both satisfy it.",
        "{c} names a situation and states the result itself as a concrete value, message, "
        "status, file, count, or state that one check confirms with one expected result."),
    "out_of_scope": (
        "Does {c} require something that an entry in `scope_out` says this change "
        "leaves out?",
        "An entry in `scope_out` names a feature, platform, user group, or behaviour as "
        "left out, and {c} requires that same thing to be built or changed.",
        "No entry in `scope_out` leaves out what {c} requires. A criterion about something "
        "`scope_out` does not mention is in scope, and so is a criterion that says the "
        "left-out thing stays as it is."),
    "pair": (
        "Do {c} and {d} require outcomes that cannot both hold?",
        "There is a situation that both {c} and {d} cover in which they require different "
        "outcomes, so nothing built satisfies both.",
        "One implementation can satisfy {c} and {d} at the same time. Entries about "
        "different situations, different inputs, or different steps do not conflict."),
    "contradiction": (
        "Do two entries in `criteria` require outcomes that cannot both hold?",
        "Two entries in `criteria` require outcomes that cannot both be true at the same "
        "time, so nothing built satisfies both. Example: one entry fixes a limit or a "
        "stored value and another requires a result that value makes impossible.",
        "One implementation can satisfy every entry in `criteria` at the same time. "
        "Entries about different inputs or different steps do not conflict."),
    "gap": (
        "Is there something a user types, enters, picks, or uploads in `criteria` whose "
        "missing, empty, or invalid case no entry in `criteria` covers?",
        "At least one entry in `criteria` says what happens when a user types, enters, "
        "picks, or uploads something valid, and no entry in `criteria` says what happens "
        "when that same thing is missing, empty, unknown, or invalid.",
        "Every entry in `criteria` about something a user types, enters, picks, or uploads "
        "is matched by an entry for its missing, empty, unknown, or invalid case, or no "
        "entry in `criteria` involves anything a user types, enters, picks, or uploads."),
    "no_measure": (
        "Is `measure` empty, undecided, or a general statement with no number and nothing "
        "specific to look at?",
        "`measure` is empty, says the measure will be decided later, or is a general "
        "statement such as 'users are happier' or 'the experience improves'.",
        "`measure` names a number, count, rate, or time, or one specific thing someone can "
        "look at after release."),
    "unproven": (
        "Does {r}.evidence` fail to show the result that {r}.criterion` requires?",
        "{r}.evidence` and {r}.files` are about a different behaviour, or show a different "
        "result from the one {r}.criterion` requires, or show only part of what it "
        "requires.",
        "{r}.evidence` or {r}.files` shows the situation in {r}.criterion` and the result "
        "it requires, in full."),
    "asserted": (
        "Does {r}.evidence` only claim the criterion is met or describe the code, without "
        "reporting what happened when something was run or looked at?",
        "{r}.evidence` says the feature works, is implemented, or was reviewed, or "
        "describes how the code is written, and reports no command, test, request, or "
        "screen that was run or looked at together with what it showed.",
        "{r}.evidence` or {r}.files` reports something that was run or looked at (a test, "
        "a command, a request, a screen) and what it showed, such as an output, a count, "
        "a status, or a message."),
    "could_be_checked": (
        "Could an automated test or a scripted run decide whether {r}.criterion` holds, "
        "with no person judging it?",
        "{r}.criterion` names a result a program can compare with an expected value: a "
        "value, message, status, count, file, time limit, or state. Waiting, repeating a "
        "step many times, or changing the clock does not need a person.",
        "{r}.criterion` needs real people: their approval or sign-off, their taste "
        "(whether wording reads well or a design looks right), or watching whether real "
        "users manage a task unaided."),
}
REASONS = {  # plain words: the calling agent relays these to a product manager
    "unclear": "two readers could build opposite behaviours and both meet this",
    "out_of_scope": "this asks for something the Out list says is left out",
    "contradiction": "two of the criteria cannot both hold",
    "pair": "these two criteria cannot both hold",
    "gap": "something the user supplies has no criterion for when it is missing or invalid",
    "no_measure": "the Outcome names nothing that would show the change worked",
    "unproven": "the evidence does not show this criterion holding",
    "asserted": "the evidence says it works without reporting what was run or seen",
    "could_be_checked": "a test or a run could decide this without a person",
    "missing": "the proof has no row for this criterion",
}
CODES = tuple(code for code in REASONS if code != "pair")  # pairs report `contradiction`


class Asked(NamedTuple):
    target: str  # a criterion id, a pair such as "A2+A5", or "contract"
    code: str


class Request(NamedTuple):
    state: Dict[str, Any]
    questions: Dict[str, Any]
    index: Dict[str, Asked]

    def ask(self, target: str, code: str, wording: str = "", **paths: str) -> None:
        text = [part.format(**paths) for part in WORDING[wording or code]]
        self.questions["%s_%s" % (target, code)] = {
            "type": "noul", "instructions": text[0],
            "criteria": {"true": text[1], "false": text[2]}}
        self.index["%s_%s" % (target, code)] = Asked(target, code)


def contract_request(spec: Spec) -> Request:
    """The state holds only what a question reads."""
    req = Request({"measure": spec.measure, "scope_out": spec.scope_out,
                   "criteria": dict(spec.criteria)}, {}, {})
    paths = {cid: "`criteria.%s`" % cid for cid in spec.criteria}
    for cid, path in paths.items():
        req.ask(cid, "unclear", c=path)
        if spec.scope_out:  # nothing listed as out: code already knows the answer
            req.ask(cid, "out_of_scope", c=path)
    if len(paths) <= MAX_PAIR_CRITERIA:
        for a, b in itertools.combinations(paths, 2):
            req.ask("%s+%s" % (a, b), "contradiction", "pair", c=paths[a], d=paths[b])
    for code in ("contradiction", "gap", "no_measure"):
        req.ask("contract", code)
    return req


def proof_request(spec: Spec, spec_dir: Path) -> Tuple[Request, List[Dict[str, str]]]:
    """Only rows that get a question go into the state, each beside its own
    criterion and evidence files, so no question has to follow a reference."""
    req = Request({"rows": {}}, {}, {})
    skipped: List[Dict[str, str]] = []
    files = 0
    for rid, (verdict, evidence) in spec.rows.items():
        if rid not in spec.criteria or verdict == "not proved":
            continue
        row: Dict[str, Any] = {"criterion": spec.criteria[rid], "evidence": evidence}
        req.state["rows"][rid] = row
        if verdict == "needs a person":
            req.ask(rid, "could_be_checked", r="`rows.%s" % rid)
            continue
        kept, dropped = read_evidence(spec_dir, evidence)
        skipped += dropped
        for name in list(kept)[max(0, MAX_FILES - files):]:
            skipped.append({"file": name, "why": "too_many_files"})
            del kept[name]
        files += len(kept)
        row["files"] = kept
        req.ask(rid, "unproven", r="`rows.%s" % rid)
        req.ask(rid, "asserted", r="`rows.%s" % rid)
    return req, skipped


# ---- Thresholds and the two commands ---------------------------------------

THRESHOLDS_PATH = Path(__file__).resolve().parent / "thresholds.json"
DEFAULT_BAND = {"flag": 0.7, "check": 0.3}  # the TypeSafe docs' starting point


def load_thresholds(path: Optional[Path] = None) -> Tuple[Dict[str, Dict[str, Any]], str]:
    """Per-code `flag` and `check` thresholds and the model they were fitted on.
    A missing or malformed file or entry falls back to 0.7 / 0.3. `flag: null`
    means the code never flags, only checks."""
    try:
        data = json.loads((path or THRESHOLDS_PATH).read_text(encoding="utf-8"))
        codes, model = data["codes"], str(data.get("model", ""))
    except (OSError, ValueError, KeyError, TypeError):
        codes, model = {}, ""
    bands: Dict[str, Dict[str, Any]] = {}
    for code in CODES:
        entry = codes.get(code) if isinstance(codes, dict) else None
        ok = (isinstance(entry, dict) and _unit(entry.get("check"))
              and (entry.get("flag") is None or _unit(entry.get("flag"))))
        bands[code] = ({"flag": entry["flag"], "check": entry["check"]} if ok
                       else dict(DEFAULT_BAND))
    return bands, model


def band(p: float, entry: Mapping[str, Any]) -> str:
    if entry["flag"] is not None and p >= entry["flag"]:
        return "flag"
    return "check" if p >= entry["check"] else "quiet"


def compose(answers: List[Dict[str, Any]]) -> None:
    """Drop lines that repeat a more specific one: `unproven` on a row already
    flagged `asserted`, and the whole-contract `contradiction` when a named pair
    is flagged (or both are only checks)."""
    asserted = {a["id"] for a in answers if a["code"] == "asserted" and a["band"] == "flag"}
    pairs = {a["band"] for a in answers if a["code"] == "contradiction" and "+" in a["id"]}
    for a in answers:
        if a["code"] == "unproven" and a["id"] in asserted:
            a["covered_by"] = "asserted"
        elif (a["code"], a["id"]) == ("contradiction", "contract") and (
                "flag" in pairs or (a["band"] == "check" and "check" in pairs)):
            a["covered_by"] = "pair"


def _count(n: int, one: str, many: str) -> str:
    return "%d %s" % (n, one if n == 1 else many)


def _order(item: Mapping[str, Any]) -> Tuple[int, int, int, str]:
    if item["id"] == "contract":
        return (1, 0, 0, item["code"])
    first, _, second = item["id"].partition("+")
    return (0, int(first[1:]), int(second[1:] or 0), item["code"])


def review(kind: str, spec_path: Path, repo: Path, as_json: bool,
           environ: Mapping[str, str], transport: Optional[Transport] = None,
           sleep: Callable[[float], None] = time.sleep) -> int:
    """`contract` or `proof`. Always returns 0: flag, pass, and off all exit 0."""
    res = resolve(repo, environ)
    doc: Dict[str, Any] = {"verdict": "off", "kind": kind,
                           "backend": res.backend.name if res.backend else "none"}

    def off(reason: str) -> int:
        doc.update(reasons=[reason], summary=_off_summary(reason, res.backend))
        print(json.dumps(doc, indent=2) if as_json
              else "off\nreason: %s\n%s" % (reason, doc["summary"]))
        return 0

    if not res.ok or res.backend is None:
        return off(res.reason)
    try:
        spec = parse_spec(spec_path.read_text(encoding="utf-8"))
    except (OSError, UnicodeDecodeError):
        return off("spec_unreadable")
    if not spec.criteria:
        return off("no_criteria")
    if kind == "proof" and not spec.rows:
        return off("no_proof_rows")
    skipped: List[Dict[str, str]] = []
    answers: List[Dict[str, Any]] = []
    if kind == "contract":
        req = contract_request(spec)
    else:
        req, skipped = proof_request(spec, spec_path.parent)
        answers = [{"id": cid, "code": "missing", "p": None, "band": "flag"}
                   for cid in spec.criteria if cid not in spec.rows]
    bands, fitted_on = load_thresholds()
    note = ""
    if req.questions:
        j = judge(req.state, req.questions, res.backend, environ, transport, sleep)
        if not j.ok or j.answers is None:
            return off(j.reason)
        for qid, asked in req.index.items():
            p = float(j.answers[qid]["noul"])
            answers.append({"id": asked.target, "code": asked.code, "p": p,
                            "band": band(p, bands[asked.code])})
        if j.model != fitted_on:  # also true when thresholds.json is missing
            note = " thresholds=%s" % ("fitted_on_other_model" if fitted_on else "default")
        doc.update(model=j.model, input_tokens=j.input_tokens, request_bytes=j.request_bytes)
    answers.sort(key=_order)
    compose(answers)
    for item in answers:
        item["reason"] = REASONS["pair" if "+" in item["id"] else item["code"]]
    shown = [a for a in answers if "covered_by" not in a]
    flags = [a for a in shown if a["band"] == "flag"]
    checks = [a for a in shown if a["band"] == "check"]
    if kind == "proof":
        files = sum(len(row.get("files", {})) for row in req.state["rows"].values())
        note = " files=%d skipped=%d%s" % (files, len(skipped), note)
        doc["skipped_files"] = skipped
        size = _count(len(spec.rows), "row", "rows")
    else:
        size = _count(len(spec.criteria), "criterion", "criteria")
    summary = "jev: %s, %s, %s, backend=%s%s" % (
        _count(len(flags), "flag", "flags"), _count(len(checks), "check", "checks"),
        size, res.backend.name, note)
    doc.update(verdict="flag" if flags else "pass", flags=flags, checks=checks,
               answers=answers, summary=summary)
    if as_json:
        print(json.dumps(doc, indent=2))
        return 0
    print(doc["verdict"])
    for item in flags + checks:
        soft = item["band"] == "check"
        print("%s%s %s %s — %s%s" % (
            "check " if soft else "", item["id"], item["code"],
            "n/a" if item["p"] is None else "%.2f" % item["p"],
            "less certain: " if soft else "", item["reason"]))
    print(summary)
    return 0


# ---- CLI --------------------------------------------------------------------


class _Parser(argparse.ArgumentParser):
    """Never repeats an unrecognized or invalid value: a key typed as an
    argument by mistake must not reach stderr or a transcript."""

    def error(self, message: str):  # type: ignore[override]
        if message.startswith("unrecognized arguments"):
            message = "unrecognized arguments (values not echoed)"
        message = re.sub(r"invalid choice: .*?\(choose from", "invalid choice (choose from",
                         message)
        self.print_usage(sys.stderr)
        self.exit(2, "%s: error: %s\n" % (self.prog, message))


def build_parser() -> argparse.ArgumentParser:
    parser = _Parser(prog="jev.py", description=(__doc__ or "").split("\n\n")[0])
    sub = parser.add_subparsers(dest="action", required=True, parser_class=_Parser)
    repo: Dict[str, Any] = dict(type=Path, help="project root holding .writ/config.md")
    sub.add_parser("status", help="say whether Jev is ready or off, and why").add_argument(
        "--repo", **repo)
    p = sub.add_parser("setup", help="write the Judgment Provider line (never a key)")
    p.add_argument("provider", choices=SETUP_PROVIDERS)
    p.add_argument("--repo", **repo)
    for name, text in (("contract", "flag unclear lines in a contract before it is agreed"),
                       ("proof", "flag weak rows in a proof before it is relied on")):
        p = sub.add_parser(name, help=text)
        p.add_argument("spec", type=Path, help="path to spec.md")
        p.add_argument("--repo", **repo)
        p.add_argument("--json", action="store_true", help="print one JSON document")
    return parser


def main(argv: Optional[List[str]] = None, environ: Optional[Mapping[str, str]] = None,
         transport: Optional[Transport] = None,
         sleep: Optional[Callable[[float], None]] = None) -> int:
    try:
        args = build_parser().parse_args(argv)
    except SystemExit as exc:
        return exc.code if isinstance(exc.code, int) else 2
    env = os.environ if environ is None else environ
    repo = args.repo
    if repo is None:
        spec = getattr(args, "spec", None)
        if spec is None:
            repo = Path(".")  # status and setup act on the project you are in
        else:
            # The opt-in belongs to the project that owns the spec: the nearest
            # folder above it holding `.writ/`. Never the current directory, or
            # one project's opt-in would send another project's text.
            above = list(spec.resolve().parents)
            repo = next((d for d in above if (d / ".writ").is_dir()),
                        next((d for d in above if d.is_dir()), Path(".")))
    try:
        if not repo.is_dir():
            raise UsageError("--repo is not a directory")
        if args.action == "status":
            return status(repo, env)
        if args.action == "setup":
            return setup(repo, args.provider)
        return review(args.action, args.spec, repo, args.json, env, transport,
                      sleep or time.sleep)
    except UsageError as exc:
        print("error: %s" % exc, file=sys.stderr)
        return 2


if __name__ == "__main__":
    sys.exit(main())
