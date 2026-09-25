#!/usr/bin/env python3
"""Optional Jev judgment provider (`2026-09-25-jev-judgment-pilot`).

Decision record: `.writ/decision-records/adr-027-optional-judgment-provider.md`.

Subcommands:
  status [--repo .]   Resolve the double opt-in. Reads `.writ/config.md` and
                      the environment; prints stdout only; sends nothing.
  probe --state-file F --questions-file Q [--repo .] [--backend B]
                      Send one judgment request through the transport and
                      report the outcome. Live only when `status` would pass;
                      with WRIT_JEV_REPLAY set, reads a recorded response
                      instead and never opens a socket. `--backend` is
                      replay-only (live always uses the configured backend).
  spec-findings --spec PATH --out FILE [--repo .] [--backend B]
                      Judge every story of a spec in ONE request (Story 3).
                      Writes FILE (a spec-analyze.py --findings array with
                      extra keys `source` and `p`) and FILE.escalate.json (the
                      story filenames the orchestrator must still judge).
                      Same live/replay rule as probe.
  ac-shadow --story F --tests-output F --diff F --review-output F [--log P]
            [--repo .] [--backend B]
                      Gate 3 shadow (Story 5). One Noul per criterion, keyed
                      by AC ID, in one request; appends one JSONL row (default
                      <repo>/.writ/state/jev-shadow.jsonl) beside the
                      evaluator's `[AC-N.M]`-tagged verdicts. Secret paths are
                      dropped from the diff and counted; an unparsed secret
                      header sends nothing (secret_path_unparsed). Advisory
                      only. Same live/replay rule as probe.
  shadow-report [--log P] [--repo .]
                      Agreement, false passes, and the ADR-027 promotion rule
                      over the shadow log. Reads the log only; no network.
  calibrate --fixtures DIR [--live] [--write-thresholds] [--backend B]
            [--recordings DIR] [--repo .]
                      Story 4. Score recorded spec-findings responses (one per
                      labeled fixture, keyed by replay hash) against gold.json:
                      TP/FP/FN per class on the dev and test splits, and the
                      emit/escalate pair per class (SELECTION_RULE; table on
                      stderr). No live recordings and no --live: `unverifiable
                      no_live_run`, nothing written. --live records missing
                      fixtures first (double opt-in; never with replay set).
                      --write-thresholds writes jev-thresholds.json only after
                      a scored run.

The provider is enabled only when `.writ/config.md` has a line
`- **Judgment Provider:** <backend>` naming `typesafe` or `vercel-gateway`
AND that backend's key is set and non-empty. A key alone never enables it.

Prints one verdict line (`pass` / `fail` / `unverifiable`), optional
`reason:` lines, then a summary line last.

Exit 0: `pass` or `unverifiable`.
Exit 1: `fail` (malformed response).
Exit 2: usage.

Key handling: this script never prints, logs, or writes a key value. The
resolver returns the NAME of the env var that holds the key, never the value;
the transport reads the value only to build the Authorization header, and
anything written to stderr is redacted of it first.
"""

from __future__ import annotations

import argparse
import fnmatch
import hashlib
import http.client
import json
import os
import re
import socket
import sys
import time
import urllib.error
import urllib.request
from pathlib import Path
from typing import (Any, Callable, Dict, List, Mapping, NamedTuple, Optional,
                    Sequence, Tuple)


CONFIG_LINE = re.compile(r"^- \*\*Judgment Provider:\*\*\s*(\S+)", re.MULTILINE)


class Backend(NamedTuple):
    name: str
    base_url: str
    key_vars: Tuple[str, ...]  # first non-empty wins
    model: str
    pinned: bool


# technical-spec §2. Both use POST <base_url>/v1/systemone.
BACKENDS: Dict[str, Backend] = {
    "typesafe": Backend(
        name="typesafe",
        base_url="https://api.typesafe.ai",
        key_vars=("TYPESAFE_API_KEY",),
        model="jev-1.13.0",
        pinned=True,
    ),
    "vercel-gateway": Backend(
        name="vercel-gateway",
        base_url="https://ai-gateway.vercel.sh/typesafe",
        key_vars=("AI_GATEWAY_API_KEY", "VERCEL_OIDC_TOKEN"),
        model="typesafe-ai/jev",
        pinned=False,
    ),
}
DISABLED_VALUE = "none"


class UsageError(Exception):
    """Exit-2 conditions."""


class Resolution(NamedTuple):
    verdict: str
    reasons: List[str]
    backend: Optional[Backend]
    key_var: Optional[str]  # env var NAME holding the key; never the value


def _emit(verdict: str, reasons: Sequence[str], summary: str) -> int:
    print(verdict)
    for reason in reasons:
        print("reason: %s" % reason)
    print(summary)
    if verdict == "fail":
        return 1
    return 0


def _config_value(repo: Path) -> Optional[str]:
    """The Judgment Provider value, lowercased; None when file or line is absent."""
    try:
        text = (repo / ".writ" / "config.md").read_text(encoding="utf-8")
    except (OSError, UnicodeDecodeError):
        return None
    match = CONFIG_LINE.search(text)
    if not match:
        return None
    return match.group(1).lower()


def _key_var(backend: Backend, environ: Mapping[str, str]) -> Optional[str]:
    """Name of the first env var with a non-blank value, or None."""
    for var in backend.key_vars:
        if environ.get(var, "").strip():
            return var
    return None


def resolve(repo: Path, environ: Mapping[str, str]) -> Resolution:
    """Double opt-in: config line naming a backend AND that backend's key."""
    value = _config_value(repo)
    if value is None:
        return Resolution("unverifiable", ["no_config_line"], None, None)
    backend = BACKENDS.get(value)
    if backend is None:
        # `none` or an unknown value. The value is never echoed: a key pasted
        # into the config line by mistake must not reach output.
        return Resolution("unverifiable", ["provider_disabled"], None, None)
    info = [] if backend.pinned else ["model_unpinned"]
    var = _key_var(backend, environ)
    if var is None:
        return Resolution("unverifiable", ["no_api_key"] + info, backend, None)
    return Resolution("pass", ["enabled"] + info, backend, var)


def status(repo: Path, environ: Mapping[str, str]) -> int:
    res = resolve(repo, environ)
    primary = res.reasons[0]
    if res.backend is None:
        return _emit(res.verdict, res.reasons,
                     "jev-judge: %s (%s) backend=none" % (res.verdict, primary))
    detail = "backend=%s model=%s" % (res.backend.name, res.backend.model)
    if res.verdict == "pass":
        return _emit(res.verdict, res.reasons,
                     "jev-judge: pass (enabled) %s key_env=%s" % (detail, res.key_var))
    return _emit(res.verdict, res.reasons,
                 "jev-judge: unverifiable (no_api_key) %s export=%s"
                 % (detail, res.backend.key_vars[0]))


# --------------------------------------------------------------------------
# Transport (technical-spec §3) — Story 2
# --------------------------------------------------------------------------

API_PATH = "/v1/systemone"
REPLAY_ENV = "WRIT_JEV_REPLAY"
TIMEOUT_SECONDS = 10
MAX_ATTEMPTS = 3
BACKOFF_SECONDS = (1, 2, 4)  # before attempt 2, 3, (4); 3 attempts use 1 and 2
RETRY_AFTER_CAP_SECONDS = 30.0  # a hostile or buggy retry-after cannot hang a run
RETRY_STATUSES = (429, 529)
TOKEN_BUDGET = 30000
ERROR_BODY_LIMIT = 500
REDACTED = "[redacted]"
INFORMATIONAL = ("model_unpinned", "thresholds_missing", "uncalibrated_thresholds")
TYPED_FIELD = {"noul": "noul", "choice": "choice", "score": "score"}
NUMERIC_TYPES = ("noul", "score")


class HttpResponse(NamedTuple):
    status: int
    headers: Mapping[str, str]  # keys lowercased
    body: bytes


class TransportFailure(Exception):
    """Network, DNS, timeout, or connection failure: no HTTP status."""


class ReplayMiss(Exception):
    """No recorded response for the request hash."""


# (url, headers, canonical body bytes) -> HttpResponse
Transport = Callable[[str, Dict[str, str], bytes], HttpResponse]


class Judgment(NamedTuple):
    verdict: str
    reasons: List[str]
    backend: Backend
    answers: Optional[Dict[str, Any]]  # None unless verdict is pass
    model: Optional[str]  # response `model`; None when no response parsed
    input_tokens: Optional[int]
    cost: Optional[str]  # gateway provider_metadata.gateway.cost
    attempts: int  # transport calls made
    key_var: Optional[str]  # env var NAME used; never the value


def canonical_body(body: Mapping[str, Any]) -> bytes:
    """Deterministic encoding: the bytes sent and the replay hash input."""
    return json.dumps(body, sort_keys=True, separators=(",", ":")).encode("utf-8")


def request_hash(payload: bytes) -> str:
    return hashlib.sha256(payload).hexdigest()


def build_body(state: Mapping[str, Any], questions: Mapping[str, Any],
               backend: Backend) -> Dict[str, Any]:
    body: Dict[str, Any] = {"model": backend.model, "state": state, "questions": questions}
    if backend.name == "vercel-gateway":
        # Business Rule 11: state reaches only Vercel and TypeSafe.
        body["providerOptions"] = {"gateway": {"only": ["typesafe-ai"]}}
    return body


def estimate_tokens(state: Mapping[str, Any], questions: Mapping[str, Any]) -> float:
    """technical-spec §3: (state chars + longest question chars) / 4."""
    longest = max((len(json.dumps(q)) for q in questions.values()), default=0)
    return (len(json.dumps(state)) + longest) / 4


def live_transport(url: str, headers: Dict[str, str], payload: bytes) -> HttpResponse:
    req = urllib.request.Request(url, data=payload, headers=headers, method="POST")
    try:
        with urllib.request.urlopen(req, timeout=TIMEOUT_SECONDS) as resp:
            return HttpResponse(resp.getcode(), _lower_headers(resp.headers), resp.read())
    except urllib.error.HTTPError as exc:  # before URLError: it is a subclass
        try:
            body = exc.read() or b""
        except (OSError, http.client.HTTPException):
            body = b""
        return HttpResponse(exc.code, _lower_headers(exc.headers), body)
    except (urllib.error.URLError, socket.timeout, OSError,
            http.client.HTTPException, ValueError) as exc:
        raise TransportFailure(type(exc).__name__)


def replay_transport(directory: str) -> Transport:
    """Serve `<directory>/<sha256 of canonical body>.json` as an HTTP 200 body."""
    def _replay(_url: str, _headers: Dict[str, str], payload: bytes) -> HttpResponse:
        path = Path(directory) / ("%s.json" % request_hash(payload))
        try:
            return HttpResponse(200, {}, path.read_bytes())
        except OSError:
            raise ReplayMiss(path.name)
    return _replay


def _lower_headers(headers: Any) -> Dict[str, str]:
    if headers is None:
        return {}
    return {str(k).lower(): str(v) for k, v in headers.items()}


def _retry_delay(headers: Mapping[str, str], attempt: int) -> float:
    """`retry-after` seconds when numeric and >= 0, else exponential backoff."""
    raw = headers.get("retry-after", "").strip()
    try:
        value = float(raw)
    except ValueError:
        value = -1.0
    if value >= 0:
        return min(value, RETRY_AFTER_CAP_SECONDS)
    return BACKOFF_SECONDS[min(attempt - 1, len(BACKOFF_SECONDS) - 1)]


def _redact(text: str, secret: Optional[str]) -> str:
    if secret:
        text = text.replace(secret, REDACTED)
    return text


SAFE_TOKEN = re.compile(r"[A-Za-z0-9._/:-]{1,64}")
INVALID = "invalid"


def _safe_token(value: Any, secret: Optional[str]) -> str:
    """A server-derived scalar made safe for a `key=value` summary field.

    Anything outside `[A-Za-z0-9._/:-]{1,64}`, or containing the key, becomes
    `invalid`. This blocks key echo and newline verdict forgery on stdout.
    """
    if isinstance(value, bool) or not isinstance(value, (str, int, float)):
        return INVALID
    text = str(value)
    if secret and secret in text:
        return INVALID
    return text if SAFE_TOKEN.fullmatch(text) else INVALID


def _one_line(text: str, secret: Optional[str]) -> str:
    """Server text for stderr: key redacted, control and non-ASCII escaped.

    stderr is merged into eval notes (`2>&1`), so a newline in an error body
    must not become its own line.
    """
    return _redact(text, secret).encode("unicode_escape").decode("ascii")


def _log_error_body(status: int, body: bytes, secret: Optional[str]) -> None:
    """stderr: HTTP status, error type/message from either body shape, raw body.

    Gateway: {"error": {"message", "type"}}. TypeSafe: {"message", "error_type"}.
    Redacted before truncation so a cut can never expose part of a key.
    """
    text = body.decode("utf-8", errors="replace")
    etype, message = "", ""
    try:
        data = json.loads(text)
    except ValueError:
        data = None
    if isinstance(data, dict):
        err = data.get("error")
        if isinstance(err, dict):
            etype, message = str(err.get("type", "")), str(err.get("message", ""))
        else:
            etype = str(data.get("error_type", ""))
            message = str(data.get("message", ""))
    line = "jev-judge: http %d type=%s message=%s" % (
        status, _one_line(etype, secret) or "-", _one_line(message, secret) or "-")
    print(line[:ERROR_BODY_LIMIT], file=sys.stderr)
    print("jev-judge: body=%s" % _one_line(text, secret)[:ERROR_BODY_LIMIT], file=sys.stderr)


def _status_reason(status: int) -> str:
    if status in (401, 403):
        return "auth_error"
    if 400 <= status < 500:
        # 422, gateway 404 model_not_found, and any other client-side rejection.
        return "request_invalid"
    return "transport_error"  # 5xx other than 529, or an unexpected 1xx/3xx


def _answers_ok(answers: Any, questions: Mapping[str, Any]) -> bool:
    """Every asked question has an answer carrying its typed field."""
    if not isinstance(answers, dict) or not answers:
        return False
    for qid, question in questions.items():
        answer = answers.get(qid)
        if not isinstance(answer, dict):
            return False
        qtype = question.get("type") if isinstance(question, dict) else None
        field = TYPED_FIELD.get(str(qtype), str(qtype))
        value = answer.get(field)
        if value is None:
            return False
        if qtype in NUMERIC_TYPES and (isinstance(value, bool)
                                       or not isinstance(value, (int, float))):
            return False
    return True


def judge(state: Mapping[str, Any], questions: Mapping[str, Any], backend: Backend,
          environ: Mapping[str, str], transport: Optional[Transport] = None,
          sleep: Callable[[float], None] = time.sleep) -> Judgment:
    """One batched judgment request. Never raises for an HTTP or network outcome.

    Transport precedence: WRIT_JEV_REPLAY (always wins, so tests and eval can
    never reach the network) > injected `transport` > live urllib.
    Callers own the double opt-in (`resolve`); this function only needs the
    backend's key for a non-replay transport.
    """
    info = [] if backend.pinned else ["model_unpinned"]

    def result(verdict: str, reason: Optional[str], attempts: int = 0,
               answers: Optional[Dict[str, Any]] = None, model: Optional[str] = None,
               tokens: Optional[int] = None, cost: Optional[str] = None,
               key_var: Optional[str] = None) -> Judgment:
        reasons = ([reason] if reason else []) + info
        return Judgment(verdict, reasons, backend, answers, model, tokens, cost,
                        attempts, key_var)

    if estimate_tokens(state, questions) > TOKEN_BUDGET:
        return result("unverifiable", "state_too_large")

    replay_dir = environ.get(REPLAY_ENV, "")
    key_var = _key_var(backend, environ)
    secret: Optional[str] = None
    headers = {"Content-Type": "application/json"}
    if replay_dir:
        send = replay_transport(replay_dir)
    else:
        if key_var is None:
            return result("unverifiable", "no_api_key")
        secret = environ[key_var].strip()
        headers["Authorization"] = "Bearer %s" % secret
        send = transport or live_transport

    url = backend.base_url + API_PATH
    payload = canonical_body(build_body(state, questions, backend))
    attempts = 0
    while True:
        attempts += 1
        try:
            resp = send(url, headers, payload)
        except ReplayMiss:
            return result("unverifiable", "replay_miss", attempts, key_var=key_var)
        except TransportFailure as exc:
            print(_redact("jev-judge: transport_error %s" % exc, secret), file=sys.stderr)
            return result("unverifiable", "transport_error", attempts, key_var=key_var)
        if resp.status in RETRY_STATUSES:
            if attempts >= MAX_ATTEMPTS:
                return result("unverifiable", "rate_limited", attempts, key_var=key_var)
            sleep(_retry_delay(resp.headers, attempts))
            continue
        if resp.status != 200:
            reason = _status_reason(resp.status)
            if reason == "request_invalid":
                _log_error_body(resp.status, resp.body, secret)
            return result("unverifiable", reason, attempts, key_var=key_var)
        break

    try:
        data = json.loads(resp.body.decode("utf-8"))
    except (UnicodeDecodeError, ValueError):
        data = None
    if not isinstance(data, dict):
        return result("fail", "malformed_response", attempts, key_var=key_var)
    # Server-derived scalars are sanitized here, so no consumer of Judgment
    # can print a key or a forged line. The pin check uses the raw value.
    raw_model = data.get("model")
    model = _safe_token(raw_model, secret) if raw_model is not None else None
    usage = data.get("usage")
    tokens = usage.get("input_tokens") if isinstance(usage, dict) else None
    tokens = tokens if isinstance(tokens, int) and not isinstance(tokens, bool) else None
    meta = data.get("provider_metadata")
    gateway = meta.get("gateway") if isinstance(meta, dict) else None
    cost = gateway.get("cost") if isinstance(gateway, dict) else None
    cost = _safe_token(cost, secret) if cost is not None else None
    extras = dict(model=model, tokens=tokens, cost=cost, key_var=key_var)

    if backend.pinned and raw_model != backend.model:
        # Business Rule 5: a different model's answers are never applied.
        return result("unverifiable", "model_mismatch", attempts, **extras)
    answers = data.get("answers")
    if not _answers_ok(answers, questions):
        return result("fail", "malformed_response", attempts, **extras)
    return result("pass", None, attempts, answers=answers, **extras)


# --------------------------------------------------------------------------
# Thresholds (technical-spec §4) — Story 2; Story 4 calibrates
# --------------------------------------------------------------------------

THRESHOLDS_PATH = Path(__file__).resolve().parent / "jev-thresholds.json"
THRESHOLD_KEYS = ("backend", "model", "calibrated", "calibrated_on",
                  "spec_findings", "ac_shadow")


class ThresholdsError(Exception):
    """Thresholds file unreadable or missing a required key."""


def _default_thresholds() -> Dict[str, Any]:
    band = {"emit": 0.85, "escalate": 0.35}
    return {
        "backend": None,
        "model": None,
        "calibrated": False,
        "calibrated_on": None,
        "spec_findings": {k: dict(band) for k in ("contradiction", "gap", "ambiguity")},
        "ac_shadow": {"satisfied": 0.9},
    }


def load_thresholds(path: Optional[Path] = None, backend: Optional[str] = None,
                    model: Optional[str] = None) -> Tuple[Dict[str, Any], List[str]]:
    """Values plus informational reasons.

    A missing file falls back to the §4 starting values and reports the
    informational `thresholds_missing`, so a lost calibrated file is visible.
    When `calibrated` is true and the active backend or model differs from
    the recorded ones, reports `uncalibrated_thresholds` and keeps the values.
    """
    path = THRESHOLDS_PATH if path is None else path
    try:
        text = path.read_text(encoding="utf-8")
    except FileNotFoundError:
        return _default_thresholds(), ["thresholds_missing"]
    except (OSError, UnicodeDecodeError) as exc:
        raise ThresholdsError("cannot read %s: %s" % (path, type(exc).__name__))
    try:
        data = json.loads(text)
    except ValueError:
        raise ThresholdsError("%s is not JSON" % path)
    if not isinstance(data, dict) or any(k not in data for k in THRESHOLD_KEYS):
        raise ThresholdsError("%s lacks required keys %s" % (path, ", ".join(THRESHOLD_KEYS)))
    reasons: List[str] = []
    if data["calibrated"] is True and (data["backend"] != backend or data["model"] != model):
        reasons.append("uncalibrated_thresholds")
    return data, reasons


# --------------------------------------------------------------------------
# probe subcommand
# --------------------------------------------------------------------------


def _read_json_object(path: Path, label: str) -> Dict[str, Any]:
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, UnicodeDecodeError, ValueError) as exc:
        raise UsageError("%s unreadable: %s (%s)" % (label, path, type(exc).__name__))
    if not isinstance(data, dict):
        raise UsageError("%s must be a JSON object: %s" % (label, path))
    return data


def _read_questions(path: Path) -> Dict[str, Any]:
    questions = _read_json_object(path, "--questions-file")
    if not questions:
        raise UsageError("--questions-file has no questions: %s" % path)
    for qid, q in questions.items():
        if not isinstance(q, dict) or not isinstance(q.get("type"), str):
            raise UsageError("question %r must be an object with a string `type`" % qid)
    return questions


def _primary(reasons: Sequence[str]) -> str:
    for reason in reasons:
        if reason not in INFORMATIONAL:
            return reason
    return "judged"


def _judgment_summary(j: Judgment, counts: Optional[str] = None) -> str:
    parts = ["jev-judge: %s (%s)" % (j.verdict, _primary(j.reasons))]
    if counts:
        parts.append(counts)
    parts += ["backend=%s" % j.backend.name,
             "model=%s" % (j.model or j.backend.model)]
    if "model_mismatch" in j.reasons:
        parts.append("expected=%s" % j.backend.model)
    if j.input_tokens is not None:
        parts.append("input_tokens=%d" % j.input_tokens)
    parts.append("attempts=%d" % j.attempts)
    if j.cost is not None:
        parts.append("cost=%s" % j.cost)
    if j.answers is not None:
        parts.append("answers=%d" % len(j.answers))
    if "auth_error" in j.reasons and j.key_var:
        parts.append("key_env=%s" % j.key_var)
    return " ".join(parts)


class Selection(NamedTuple):
    backend: Optional[Backend]  # None: no request may be sent
    reasons: List[str]  # why not, when backend is None
    replay: bool
    named: Optional[Backend]  # the configured backend, even when its key is missing


def _select_backend(repo: Path, backend_arg: Optional[str],
                    environ: Mapping[str, str]) -> Selection:
    """Which backend a request goes to. Replay always wins and needs no key;
    live needs both opt-in halves (Business Rule 1). `--backend` is replay-only."""
    replay = bool(environ.get(REPLAY_ENV, ""))
    if backend_arg and not replay:
        raise UsageError("--backend is replay-only; the live backend comes from "
                         ".writ/config.md (set %s to replay)" % REPLAY_ENV)
    if replay and backend_arg:
        return Selection(BACKENDS[backend_arg], [], True, BACKENDS[backend_arg])
    if replay:
        value = _config_value(repo)
        if value is None:
            return Selection(None, ["no_config_line"], True, None)
        found = BACKENDS.get(value)
        if found is None:
            return Selection(None, ["provider_disabled"], True, None)
        return Selection(found, [], True, found)
    res = resolve(repo, environ)
    if res.verdict != "pass":
        return Selection(None, res.reasons, False, res.backend)
    return Selection(res.backend, [], False, res.backend)


def probe(args: argparse.Namespace, environ: Mapping[str, str],
          transport: Optional[Transport], sleep: Callable[[float], None]) -> int:
    state = _read_json_object(args.state_file, "--state-file")
    questions = _read_questions(args.questions_file)
    sel = _select_backend(args.repo, args.backend, environ)
    if sel.backend is None:
        if not sel.replay:
            return status(args.repo, environ)
        return _emit("unverifiable", sel.reasons,
                     "jev-judge: unverifiable (%s) backend=none" % sel.reasons[0])
    j = judge(state, questions, sel.backend, environ, transport=transport, sleep=sleep)
    return _emit(j.verdict, j.reasons, _judgment_summary(j))


# --------------------------------------------------------------------------
# spec-findings subcommand (technical-spec §4, §5) — Story 3
# --------------------------------------------------------------------------

# Criterion parsing matches scripts/spec-analyze.py exactly (CRITERION, the
# `Given` prefix rule, TAG_TAIL), so criterion positions and AC IDs agree with
# the findings checker. Copied, not imported: verifier scripts stay decoupled.
CRITERION = re.compile(r"^- \[[ xX]\]\s+(.*)$")
TAG_TAIL = re.compile(r"\s*`\[AC-\d+\.\d+(?:,\s*AC-\d+\.\d+)*\]`\s*$")
AC_ID = re.compile(r"AC-\d+\.\d+")
SPEC_CODES = ("contradiction", "gap", "ambiguity")


class Story(NamedTuple):
    filename: str
    user_story: str  # the `## User Story` block; "" when the story has none
    criteria: List[str]  # Given/When/Then bodies, AC tag tail removed
    ac_ids: List[List[str]]  # per criterion, from its tag tail; [] when untagged


class Asked(NamedTuple):
    """What a question ID means. Code-side only; never sent as state."""
    code: str
    story: str
    criterion: Optional[int]  # 0-based index into criteria; None for story questions
    key: Optional[str] = None  # the criterion's state key (AC ID or `C<n>`)


def _user_story_block(text: str) -> str:
    out: List[str] = []
    inside = False
    for line in text.splitlines():
        if line.startswith("## "):
            if inside:
                break
            inside = line[3:].strip().lower() == "user story"
            continue
        if inside:
            out.append(line)
    return "\n".join(out).strip()


def _parse_story(filename: str, text: str) -> Story:
    criteria: List[str] = []
    ac_ids: List[List[str]] = []
    for line in text.splitlines():
        match = CRITERION.match(line)
        if not match:
            continue
        body = match.group(1).strip()
        if not body.lower().startswith("given"):
            continue
        tail = TAG_TAIL.search(body)
        ac_ids.append(AC_ID.findall(tail.group(0)) if tail else [])
        criteria.append(TAG_TAIL.sub("", body).strip())
    return Story(filename, _user_story_block(text), criteria, ac_ids)


def load_stories(spec: Path) -> List[Story]:
    """Stories under `<spec>/user-stories/story-*.md`, in spec-analyze order."""
    folder = spec / "user-stories"
    if not folder.is_dir():
        return []
    stories: List[Story] = []
    for path in sorted(folder.glob("story-*.md")):
        try:
            text = path.read_text(encoding="utf-8")
        except (OSError, UnicodeDecodeError) as exc:
            raise UsageError("cannot read story %s (%s)" % (path, type(exc).__name__))
        stories.append(_parse_story(path.name, text))
    return stories


def _noul(instructions: str, true: str, false: str) -> Dict[str, Any]:
    return {"type": "noul", "instructions": instructions,
            "criteria": {"true": true, "false": false}}


def _story_questions(ref: str) -> Dict[str, Dict[str, Any]]:
    """The two per-story Nouls. `ref` is the backticked-path prefix of the story.

    jev-1.13 reads literally and is weak at counting and indirection, so each
    question names the exact state path it reads and puts the boundary cases
    in the criteria rather than leaving them to inference.

    Wording is calibrated (Story 4, DEV-019) against the dev split only; no
    example word may come from a test-split fixture. `contradiction` keeps the
    Story 3 text, which separated on live Jev. `gap` no longer lists six
    failure kinds and no longer reads `user_story` (that version scored clean
    stories above gap stories). It asks one literal condition: an input the
    user supplies that has a valid-case criterion and no absent/invalid-case
    criterion. Its examples (keyword, file, link, token, form field) come from
    dev fixtures, and it excludes verification steps (tests pass, a build
    succeeds), which are not inputs. Any change here changes every replay hash
    and needs `calibrate --live` again (fixtures/jev-replay/README.md).
    """
    crit = "`%s.criteria`" % ref
    return {
        "contradiction": _noul(
            "Do two criteria in %s require outcomes that cannot both hold?" % crit,
            "Two criteria in %s require outcomes that cannot both be true at the same "
            "time, so no implementation satisfies both. Example: one criterion fixes a "
            "stored value and another requires a result that value makes impossible." % crit,
            "One implementation can satisfy every criterion in %s at the same time. "
            "Criteria about different inputs or different steps do not conflict, and a "
            "list with zero or one criterion has no conflict." % crit),
        "gap": _noul(
            "Does %s give an outcome for some input the user supplies when it is valid but "
            "give no outcome for when it is absent, empty, unknown, or invalid?" % crit,
            "Some input the user supplies in %s (for example a keyword, a file, a link, a "
            "token, or a form field) has a criterion for its valid case and no criterion "
            "in %s for its absent, empty, unknown, or invalid case." % (crit, crit),
            "Every input the user supplies in %s that has a valid-case criterion also has "
            "a criterion for its absent, empty, unknown, or invalid case, or %s names no "
            "input the user supplies. Test runs, builds, and verdicts are not inputs the "
            "user supplies." % (crit, crit)),
    }


def _criterion_question(ref: str, key: str) -> Dict[str, Any]:
    """One Noul per criterion, addressed by its AC ID key (never by list
    position: jev-1.13 is weak at indirection). Calibrated wording (Story 4,
    dev split only): one question covering two ambiguity shapes, an undefined
    judgment word, and a Then that states a side effect instead of the
    decision its Given case needs. Its examples are generic or from dev
    fixtures (the fee case)."""
    c = "`%s.criteria[%s]`" % (ref, json.dumps(key))
    return _noul(
        "Does the Then clause of %s fail to decide the outcome it is about, so two "
        "opposite behaviors would both satisfy it?" % c,
        "Either the Then of %s rests on an undefined judgment word (such as "
        "'properly', 'suitable', or 'best'), or its Given sets up a case that needs a "
        "decision (for example whether a fee is assessed) and the Then states only a side "
        "effect. Two developers could build opposite behaviors and both satisfy it." % c,
        "The Then of %s states the decision itself as a concrete value, message, "
        "status, file, count, or state that a test checks with one expected result." % c)


def criterion_keys(story: Story) -> List[str]:
    """State key per criterion: its first AC ID not already used, else `C<n>`
    (1-based position) for an untagged criterion."""
    keys: List[str] = []
    for n, ids in enumerate(story.ac_ids, start=1):
        key = next((ac for ac in ids if ac not in keys), None)
        keys.append(key or "C%d" % n)
    return keys


def spec_request(stories: Sequence[Story]) -> Tuple[Dict[str, Any], Dict[str, Any],
                                                    Dict[str, Asked]]:
    """State, questions, and the code-side meaning of each question ID.

    Each story's `criteria` is an object keyed by AC ID (`criterion_keys`), so
    a question names its criterion directly."""
    state: Dict[str, Any] = {"stories": {}}
    questions: Dict[str, Any] = {}
    index: Dict[str, Asked] = {}
    for n, story in enumerate(stories, start=1):
        keys = criterion_keys(story)
        state["stories"][story.filename] = {
            "user_story": story.user_story,
            "criteria": {key: text for key, text in zip(keys, story.criteria)}}
        ref = "stories[%s]" % json.dumps(story.filename)
        for code, question in _story_questions(ref).items():
            qid = "s%d_%s" % (n, code)
            questions[qid] = question
            index[qid] = Asked(code, story.filename, None)
        for i, key in enumerate(keys):
            qid = "s%d_c%d_ambiguity" % (n, i + 1)
            questions[qid] = _criterion_question(ref, key)
            index[qid] = Asked("ambiguity", story.filename, i, key)
    return state, questions, index


def band(p: float, thresholds: Mapping[str, float]) -> str:
    """p >= emit: finding. escalate <= p < emit: escalate. Below: clean."""
    if p >= thresholds["emit"]:
        return "finding"
    if p >= thresholds["escalate"]:
        return "escalate"
    return "clean"


def _finding_summary(asked: Asked) -> str:
    """Built from the question's meaning only; server text never reaches it."""
    if asked.code == "contradiction":
        return "Two criteria in %s require outcomes that cannot both hold." % asked.story
    if asked.code == "gap":
        return ("%s implies a nil, empty, or error case that no criterion covers."
                % asked.story)
    return ("Criterion %d of %s has a Then clause two competent implementers could "
            "satisfy with opposite behavior." % ((asked.criterion or 0) + 1, asked.story))


def _is_number(value: Any) -> bool:
    return isinstance(value, (int, float)) and not isinstance(value, bool)


def _unit_interval(value: Any) -> bool:
    return _is_number(value) and 0.0 <= value <= 1.0  # NaN compares False


# An emit threshold no Noul reaches: the class never becomes a finding and every
# story escalates for it (Story 4: a class that did not separate on live Jev).
NEVER_EMIT = 1.01


def apply_thresholds(answers: Mapping[str, Any], index: Mapping[str, Asked],
                     thresholds: Mapping[str, Any], stories: Sequence[Story],
                     source: str) -> Tuple[List[Dict[str, Any]], List[str]]:
    """Findings rows (spec-analyze schema + `source`, `p`) and escalated stories."""
    by_name = {s.filename: s for s in stories}
    bands = thresholds["spec_findings"]
    findings: List[Dict[str, Any]] = []
    escalated = set()
    for qid, asked in index.items():
        p = float(answers[qid]["noul"])
        outcome = band(p, bands[asked.code])
        if outcome == "escalate":
            escalated.add(asked.story)
        elif outcome == "finding":
            row: Dict[str, Any] = {"code": asked.code, "story": asked.story,
                                   "summary": _finding_summary(asked)}
            if asked.criterion is not None:
                ids = by_name[asked.story].ac_ids[asked.criterion]
                if ids:
                    row["ac_ids"] = list(ids)
            row["source"] = source
            row["p"] = p
            findings.append(row)
    return findings, [s.filename for s in stories if s.filename in escalated]


def _spec_thresholds(backend: Optional[Backend]) -> Tuple[Dict[str, Any], List[str]]:
    """Loaded and validated before any request, so a broken file costs nothing."""
    try:
        data, reasons = load_thresholds(backend=backend.name if backend else None,
                                        model=backend.model if backend else None)
    except ThresholdsError as exc:
        raise UsageError("thresholds: %s" % exc)
    bands = data.get("spec_findings")
    for code in SPEC_CODES:
        entry = bands.get(code) if isinstance(bands, dict) else None
        if not isinstance(entry, dict):
            raise UsageError("thresholds: spec_findings.%s is missing" % code)
        emit, esc = entry.get("emit"), entry.get("escalate")
        emit_ok = _unit_interval(emit) or (_is_number(emit) and emit == NEVER_EMIT)
        if not (emit_ok and _unit_interval(esc) and esc <= emit):
            raise UsageError("thresholds: spec_findings.%s needs 0 <= escalate <= emit <= 1 "
                             "(or emit = %.2f, never emit)" % (code, NEVER_EMIT))
    if data.get("calibrated") is not True and "uncalibrated_thresholds" not in reasons:
        reasons.append("uncalibrated_thresholds")
    return data, reasons


def _write_json(path: Path, data: Any) -> None:
    try:
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(json.dumps(data, indent=2) + "\n", encoding="utf-8")
    except OSError as exc:
        raise UsageError("--out not writable: %s (%s)" % (path, type(exc).__name__))


def _counts(stories: Sequence[Story], escalated: Sequence[str]) -> str:
    return "%d judged, %d escalated" % (len(stories) - len(escalated), len(escalated))


def spec_findings(args: argparse.Namespace, environ: Mapping[str, str],
                  transport: Optional[Transport], sleep: Callable[[float], None]) -> int:
    """Any outcome other than a parsed judgment writes `[]` and escalates every
    story, so the orchestrator runs its full pass (Business Rule 3)."""
    if not args.spec.is_dir():
        raise UsageError("--spec is not a directory: %s" % args.spec)
    out: Path = args.out
    sidecar = Path(str(out) + ".escalate.json")
    sel = _select_backend(args.repo, args.backend, environ)
    stories = load_stories(args.spec)
    thresholds, info = _spec_thresholds(sel.backend or sel.named)
    everyone = [s.filename for s in stories]

    def fallback(verdict: str, reasons: List[str], summary_tail: str) -> int:
        _write_json(out, [])
        _write_json(sidecar, everyone)
        head = "jev-judge: %s (%s) %s" % (verdict, _primary(reasons), _counts(stories, everyone))
        return _emit(verdict, reasons + info, "%s %s" % (head, summary_tail))

    if not stories:
        name = (sel.backend or sel.named).name if (sel.backend or sel.named) else "none"
        return fallback("unverifiable", ["no_stories"], "backend=%s" % name)
    if sel.backend is None:
        tail = "backend=%s" % (sel.named.name if sel.named else "none")
        if "no_api_key" in sel.reasons and sel.named is not None:
            tail += " export=%s" % sel.named.key_vars[0]
        return fallback("unverifiable", list(sel.reasons), tail)

    state, questions, index = spec_request(stories)
    j = judge(state, questions, sel.backend, environ, transport=transport, sleep=sleep)
    if j.verdict == "pass" and j.answers is not None and not all(
            _unit_interval(j.answers[qid].get("noul")) for qid in index):
        j = j._replace(verdict="fail", answers=None,
                       reasons=["malformed_response"] + [r for r in j.reasons if r in INFORMATIONAL])
    if j.verdict != "pass" or j.answers is None:
        _write_json(out, [])
        _write_json(sidecar, everyone)
        return _emit(j.verdict, j.reasons + info,
                     _judgment_summary(j, _counts(stories, everyone)))

    source = j.model or sel.backend.model
    findings, escalated = apply_thresholds(j.answers, index, thresholds, stories, source)
    _write_json(out, findings)
    _write_json(sidecar, escalated)
    summary = "%s findings=%d" % (_judgment_summary(j, _counts(stories, escalated)),
                                  len(findings))
    return _emit(j.verdict, j.reasons + info, summary)


# --------------------------------------------------------------------------
# ac-shadow and shadow-report subcommands (technical-spec §1, §5) — Story 5
# --------------------------------------------------------------------------

SHADOW_LOG = Path(".writ") / "state" / "jev-shadow.jsonl"
# An evaluator Acceptance Criteria checklist line: `- [x]` or `- [ ]`, ending
# with one `[AC-N.M]` tag (optionally backticked). agents/evaluator-agent.md.
EVALUATOR_LINE = re.compile(r"^\s*[-*]\s+\[([ xX])\]\s+.*?`?\[(AC-\d+\.\d+)\]`?\s*$")
# Business Rule 7. Matched case-insensitively against each path and its basename.
SECRET_PATTERNS = (".env*", "*.pem", "*.key", "*secret*", "*credential*")
PROMOTION_STORIES = 30
PROMOTION_AGREEMENT_PCT = 95


def _ac_order(ac: str) -> Tuple[int, ...]:
    return tuple(int(n) for n in ac[3:].split("."))


def story_criteria(story: Story) -> Dict[str, str]:
    """Criterion text keyed by AC ID (first occurrence wins). Untagged criteria
    cannot be matched to an evaluator verdict and are left out."""
    out: Dict[str, str] = {}
    for text, ids in zip(story.criteria, story.ac_ids):
        for ac in ids:
            out.setdefault(ac, text)
    return out


def parse_evaluator(text: str) -> Tuple[Dict[str, bool], List[str]]:
    """Evaluator verdict per AC ID from tagged checklist lines. An ID given both
    verdicts is dropped (never compared) and listed as conflicting."""
    seen: Dict[str, set] = {}
    for line in text.splitlines():
        match = EVALUATOR_LINE.match(line)
        if match:
            seen.setdefault(match.group(2), set()).add(match.group(1) in "xX")
    verdicts = {ac: next(iter(v)) for ac, v in seen.items() if len(v) == 1}
    conflicting = sorted((ac for ac, v in seen.items() if len(v) > 1), key=_ac_order)
    return verdicts, conflicting


def _is_secret_path(path: str) -> bool:
    lowered = path.lower()
    base = lowered.rsplit("/", 1)[-1]
    return any(fnmatch.fnmatchcase(name, pattern)
               for pattern in SECRET_PATTERNS for name in (lowered, base))


def _clean_path(raw: str) -> str:
    path = raw.split("\t", 1)[0].strip().strip('"')
    if path[:2] in ("a/", "b/"):
        path = path[2:]
    return path


DIFF_HEADERS = ("diff --git ", "diff --cc ", "diff --combined ")
HUNK_HEADER = re.compile(r"^@@ -\d+(?:,(\d+))? \+\d+(?:,(\d+))? @@")
# Every line form that can name a file path in diff text (final guard).
HEADER_LIKE = ("diff ", "--- ", "+++ ", "rename from ", "rename to ", "copy from ",
               "copy to ", "Binary files ")


class SecretPathUnparsed(Exception):
    """The text left to send still has a header-like line naming a secret path:
    a diff shape the splitter did not follow. Nothing is sent."""


def _line_paths(text: str) -> List[str]:
    """Candidate paths on one header-like line: the whole remainder plus every
    space-separated token. Over-collecting is deliberate: a false match only
    drops a block (or, in the guard, the whole request)."""
    for prefix in HEADER_LIKE:
        if text.startswith(prefix):
            rest = text[len(prefix):]
            paths = [_clean_path(rest)] + [_clean_path(tok) for tok in rest.split(" ")]
            return [p for p in paths if p and p != "/dev/null"]
    return []


def _block_paths(block: Sequence[str]) -> List[str]:
    """Paths the file header of a block names (lines before its first hunk)."""
    paths: List[str] = []
    for line in block:
        text = line.rstrip("\r\n")
        if text.startswith("@@"):
            break  # hunk content from here on: its lines are not paths
        paths += _line_paths(text)
    return paths


def _diff_blocks(text: str) -> List[List[str]]:
    """Per-file blocks. A block starts at every `diff --git` / `--cc` /
    `--combined` header, and at a `--- ` line directly followed by `+++ ` that
    sits outside a hunk and is not the header pair of a `diff` line just seen.

    Hunk lengths come from standard `@@ -a,b +c,d @@` headers. A hunk this
    cannot count (combined `@@@`) runs to the next `diff` or `@@` line, and no
    `---`/`+++` pair splits inside it; `slice_diff`'s guard catches what folds.
    Text before the first header is its own block and names no path."""
    lines = text.splitlines(keepends=True)
    blocks: List[List[str]] = [[]]
    old = new = 0  # lines left in a counted hunk
    uncounted = False  # inside a hunk whose length is unknown
    pending_pair = False  # a `diff` header was seen; its ---/+++ pair is header
    for i, line in enumerate(lines):
        text = line.rstrip("\r\n")
        in_hunk = uncounted or old > 0 or new > 0
        pair = (text.startswith("--- ") and i + 1 < len(lines)
                and lines[i + 1].startswith("+++ "))
        starts = text.startswith(DIFF_HEADERS) or (pair and not in_hunk and not pending_pair)
        if starts:
            old = new = 0
            uncounted = False
            pending_pair = text.startswith(DIFF_HEADERS)
            if blocks[-1]:
                blocks.append([])
        elif text.startswith("@@"):
            pending_pair = False
            match = HUNK_HEADER.match(text)
            if match:
                old = int(match.group(1)) if match.group(1) is not None else 1
                new = int(match.group(2)) if match.group(2) is not None else 1
                uncounted = False
            else:
                old = new = 0
                uncounted = True
        elif old > 0 or new > 0:
            if text.startswith("-"):
                old -= 1
            elif text.startswith("+"):
                new -= 1
            elif text.startswith(" ") or text == "":
                old, new = old - 1, new - 1
            elif not text.startswith("\\"):  # not "\ No newline at end of file"
                old = new = 0  # malformed count: the hunk is over
            old, new = max(old, 0), max(new, 0)
        elif pair and pending_pair:
            pending_pair = False  # the header pair of the diff line above
        blocks[-1].append(line)
    return [b for b in blocks if b]


def slice_diff(text: str) -> Tuple[str, int, List[str]]:
    """Drop every whole file block that names a secret path (Business Rule 7).
    Returns the kept diff, the excluded-block count, and one name per block.

    Fail closed: if any header-like line left in the kept text still names a
    secret path, raise SecretPathUnparsed instead of returning it."""
    kept: List[str] = []
    names: List[str] = []
    for block in _diff_blocks(text):
        secret = [p for p in _block_paths(block) if _is_secret_path(p)]
        if secret:
            names.append(min(secret, key=len))
            continue
        kept.extend(block)
    for line in kept:
        if any(_is_secret_path(p) for p in _line_paths(line.rstrip("\r\n"))):
            raise SecretPathUnparsed(len(names))
    return "".join(kept), len(names), names


def _satisfied_question(ac: str) -> Dict[str, Any]:
    """jev-1.13 is weak at indirection, so the question names its criterion by
    AC ID path (never by list position) and states both outcomes in full."""
    ref = "`criteria[%s]`" % json.dumps(ac)
    return _noul(
        "Is the acceptance criterion in %s satisfied by the code change in `diff` and "
        "the recorded test output in `tests_output`?" % ref,
        "`diff` implements the outcome the Then clause of %s names, and `tests_output` "
        "shows a passing test that exercises that outcome, with no failing test for it."
        % ref,
        "`diff` does not implement the outcome the Then clause of %s names, or "
        "`tests_output` shows no passing test that exercises it, or `tests_output` shows "
        "a failing test for it." % ref)


def shadow_request(criteria: Mapping[str, str], tests_output: str,
                   diff: str) -> Tuple[Dict[str, Any], Dict[str, Any], Dict[str, str]]:
    """State keyed by AC ID, one Noul per criterion, and question ID -> AC ID."""
    state = {"criteria": dict(criteria), "tests_output": tests_output, "diff": diff}
    questions: Dict[str, Any] = {}
    index: Dict[str, str] = {}
    for n, ac in enumerate(sorted(criteria, key=_ac_order), start=1):
        qid = "c%d_satisfied" % n
        questions[qid] = _satisfied_question(ac)
        index[qid] = ac
    return state, questions, index


def _read_input(path: Path, label: str) -> str:
    try:
        return path.read_bytes().decode("utf-8", errors="replace")
    except OSError as exc:
        raise UsageError("%s unreadable: %s (%s)" % (label, path, type(exc).__name__))


def _story_key(path: Path) -> str:
    """`<spec folder>/<story file>` for a story under user-stories/, else the name."""
    if path.parent.name == "user-stories" and path.parent.parent.name:
        return "%s/%s" % (path.parent.parent.name, path.name)
    return path.name


def _shadow_threshold(backend: Optional[Backend]) -> Tuple[float, List[str]]:
    """Loaded and validated before any request, so a broken file costs nothing."""
    try:
        data, reasons = load_thresholds(backend=backend.name if backend else None,
                                        model=backend.model if backend else None)
    except ThresholdsError as exc:
        raise UsageError("thresholds: %s" % exc)
    entry = data.get("ac_shadow")
    value = entry.get("satisfied") if isinstance(entry, dict) else None
    if not _unit_interval(value):
        raise UsageError("thresholds: ac_shadow.satisfied must be a number in [0, 1]")
    return float(value), reasons


def _append_row(log: Path, row: Mapping[str, Any]) -> None:
    try:
        log.parent.mkdir(parents=True, exist_ok=True)
        with log.open("a", encoding="utf-8") as fh:
            fh.write(json.dumps(row, sort_keys=True) + "\n")
    except OSError as exc:
        raise UsageError("--log not writable: %s (%s)" % (log, type(exc).__name__))


def ac_shadow(args: argparse.Namespace, environ: Mapping[str, str],
              transport: Optional[Transport], sleep: Callable[[float], None]) -> int:
    """One shadow row per evaluated story. Advisory only (Business Rule 4):
    nothing reads the result to change a gate. A non-pass outcome writes no row."""
    story_text = _read_input(args.story, "--story")
    tests_output = _read_input(args.tests_output, "--tests-output")
    diff_text = _read_input(args.diff, "--diff")
    review = _read_input(args.review_output, "--review-output")
    log: Path = args.log if args.log is not None else args.repo / SHADOW_LOG
    sel = _select_backend(args.repo, args.backend, environ)
    satisfied, info = _shadow_threshold(sel.backend or sel.named)
    try:
        diff, excluded, names = slice_diff(diff_text)
        unparsed = False
    except SecretPathUnparsed as exc:
        diff, excluded, names, unparsed = "", int(exc.args[0]), [], True
    for name in names:
        print("jev-judge: excluded %s" % _one_line(name, None), file=sys.stderr)
    excluded_tail = "excluded_paths=%d" % excluded

    def skipped(reasons: List[str], backend_tail: str) -> int:
        return _emit("unverifiable", reasons + info, "jev-judge: unverifiable (%s) %s %s"
                     % (_primary(reasons), excluded_tail, backend_tail))

    if sel.backend is None:
        backend_tail = "backend=%s" % (sel.named.name if sel.named else "none")
        if "no_api_key" in sel.reasons and sel.named is not None:
            backend_tail += " export=%s" % sel.named.key_vars[0]
        return skipped(list(sel.reasons), backend_tail)
    backend_tail = "backend=%s" % sel.backend.name
    unpinned = [] if sel.backend.pinned else ["model_unpinned"]
    if unparsed:
        return skipped(["secret_path_unparsed"] + unpinned, backend_tail)
    criteria = story_criteria(_parse_story(args.story.name, story_text))
    if not criteria:
        return skipped(["no_criteria"] + unpinned, backend_tail)
    verdicts, conflicting = parse_evaluator(review)
    compared = {ac: text for ac, text in criteria.items() if ac in verdicts}
    if not compared:
        return skipped(["no_evaluator_ids"] + unpinned, backend_tail)

    state, questions, index = shadow_request(compared, tests_output, diff)
    j = judge(state, questions, sel.backend, environ, transport=transport, sleep=sleep)
    if j.verdict == "pass" and j.answers is not None and not all(
            _unit_interval(j.answers[qid].get("noul")) for qid in index):
        j = j._replace(verdict="fail", answers=None,
                       reasons=["malformed_response"] + [r for r in j.reasons if r in INFORMATIONAL])
    conflict_tail = " conflicting=%d" % len(conflicting) if conflicting else ""
    if j.verdict != "pass" or j.answers is None:
        counts = "criteria=%d %s%s" % (len(compared), excluded_tail, conflict_tail)
        return _emit(j.verdict, j.reasons + info, _judgment_summary(j, counts))

    cells: Dict[str, Dict[str, Any]] = {}
    for qid, ac in index.items():
        p = float(j.answers[qid]["noul"])  # typed numeric field only; no server text
        jev = p >= satisfied
        cells[ac] = {"p": p, "jev": jev, "evaluator": verdicts[ac],
                     "agree": jev == verdicts[ac]}
    _append_row(log, {"ts": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
                      "story": _story_key(args.story), "backend": sel.backend.name,
                      "model": j.model or sel.backend.model, "criteria": cells,
                      "excluded_paths": excluded})
    agree = sum(1 for c in cells.values() if c["agree"])
    false_pass = sum(1 for c in cells.values() if c["jev"] and not c["evaluator"])
    counts = "criteria=%d agree=%d false_pass=%d false_block=%d %s%s" % (
        len(cells), agree, false_pass, len(cells) - agree - false_pass, excluded_tail,
        conflict_tail)
    return _emit(j.verdict, j.reasons + info, _judgment_summary(j, counts))


def _valid_row(row: Any) -> bool:
    if not isinstance(row, dict) or not isinstance(row.get("story"), str) or not row["story"]:
        return False
    cells = row.get("criteria")
    if not isinstance(cells, dict) or not cells:
        return False
    for cell in cells.values():
        if not isinstance(cell, dict) or not _unit_interval(cell.get("p")):
            return False
        jev, evaluator, agree = cell.get("jev"), cell.get("evaluator"), cell.get("agree")
        if not all(isinstance(v, bool) for v in (jev, evaluator, agree)):
            return False
        if agree != (jev == evaluator):
            return False
    return True


def read_shadow_log(log: Path) -> Tuple[List[Dict[str, Any]], int]:
    """Valid rows plus the count of skipped (malformed) non-blank lines.
    A missing log is empty; an unreadable one is a usage error."""
    try:
        raw = log.read_bytes()
    except FileNotFoundError:
        return [], 0
    except OSError as exc:
        raise UsageError("--log unreadable: %s (%s)" % (log, type(exc).__name__))
    rows: List[Dict[str, Any]] = []
    skipped = 0
    for line in raw.splitlines():
        if not line.strip():
            continue
        try:
            row = json.loads(line.decode("utf-8"))
        except (UnicodeDecodeError, ValueError):
            row = None
        if _valid_row(row):
            rows.append(row)
        else:
            skipped += 1
    return rows, skipped


def shadow_report(args: argparse.Namespace) -> int:
    """Business Rule 8 over the shadow log. Reads the log only; sends nothing."""
    log: Path = args.log if args.log is not None else args.repo / SHADOW_LOG
    rows, skipped = read_shadow_log(log)
    stories = len({row["story"] for row in rows})
    total = agree = false_pass = false_block = 0
    for row in rows:
        for cell in row["criteria"].values():
            total += 1
            if cell["jev"] == cell["evaluator"]:
                agree += 1
            elif cell["jev"]:
                false_pass += 1  # Jev satisfied where the evaluator said not satisfied
            else:
                false_block += 1
    unmet = []
    if stories < PROMOTION_STORIES:
        unmet.append("stories")
    if false_pass:
        unmet.append("false_pass")
    if total == 0 or agree * 100 < PROMOTION_AGREEMENT_PCT * total:
        unmet.append("agreement")
    verdict, reason = ("unverifiable", "promotion_not_met") if unmet else ("pass", "promotion_met")
    pct = 100.0 * agree / total if total else 0.0
    summary = ("jev-judge: %s (%s) rows=%d stories=%d criteria=%d agree=%d agreement=%.1f%% "
               "false_pass=%d false_block=%d skipped_rows=%d" % (
                   verdict, reason, len(rows), stories, total, agree, pct, false_pass,
                   false_block, skipped))
    if unmet:
        summary += " unmet=%s" % ",".join(unmet)
    return _emit(verdict, [reason], summary)


# --------------------------------------------------------------------------
# calibrate subcommand (technical-spec §1, §4) — Story 4
# --------------------------------------------------------------------------

LABELS = ("contradiction", "gap", "ambiguity", "clean")
SPLITS_FILE = "splits.json"
DEFAULT_RECORDINGS = Path(__file__).resolve().parent / "tests" / "fixtures" / "jev-replay"
RECORDING_KEY = "writ_recording"  # metadata `calibrate --live` adds to a recorded body
CLEAN_MARGIN = 0.05
DATE = re.compile(r"\d{4}-\d{2}-\d{2}")
SELECTION_RULE = (
    "per class, on the fit split: emit = the lowest gold-positive score at least 0.05 "
    "above the highest clean score (zero clean false positives, then maximum recall); "
    "escalate = min(highest clean score + 0.01, lowest gold-positive score); when no "
    "gold-positive clears the margin, emit = 1.01 (never) and escalate = 0.0 (always)")


class Fixture(NamedTuple):
    slug: str
    path: Path
    label: str
    split: str  # "dev", "test", or "all" when there is no splits file
    stories: List[Story]


class Scored(NamedTuple):
    slug: str
    label: str
    split: str
    scores: Dict[str, float]  # per code: the highest Noul p among that code's questions


def _read_splits(root: Path, slugs: Sequence[str]) -> Dict[str, str]:
    """`<fixtures>/splits.json`: {"dev": [slug...], "test": [slug...]}; every
    fixture exactly once. No file: every fixture is in split "all"."""
    path = root / SPLITS_FILE
    if not path.is_file():
        return {}
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, UnicodeDecodeError, ValueError) as exc:
        raise UsageError("splits.json unreadable: %s (%s)" % (path, type(exc).__name__))
    if not isinstance(data, dict) or set(data) != {"dev", "test"} or not all(
            isinstance(v, list) and all(isinstance(x, str) for x in v) for v in data.values()):
        raise UsageError("splits.json must map exactly \"dev\" and \"test\" to fixture names")
    out: Dict[str, str] = {}
    for split in ("dev", "test"):
        for slug in data[split]:
            if slug not in slugs:
                raise UsageError("splits.json names an unknown fixture: %s" % slug)
            if slug in out:
                raise UsageError("splits.json assigns %s twice" % slug)
            out[slug] = split
    missing = [s for s in slugs if s not in out]
    if missing:
        raise UsageError("splits.json does not assign: %s" % ", ".join(missing))
    return out


def load_fixtures(root: Path) -> List[Fixture]:
    """Every `<root>/*/gold.json` fixture: its label, split, and stories."""
    if not root.is_dir():
        raise UsageError("--fixtures is not a directory: %s" % root)
    golds = sorted(root.glob("*/gold.json"))
    if not golds:
        raise UsageError("--fixtures has no */gold.json: %s" % root)
    splits = _read_splits(root, [g.parent.name for g in golds])
    out: List[Fixture] = []
    for gold_path in golds:
        slug = gold_path.parent.name
        try:
            gold = json.loads(gold_path.read_text(encoding="utf-8"))
        except (OSError, UnicodeDecodeError, ValueError) as exc:
            raise UsageError("gold.json unreadable: %s (%s)" % (gold_path, type(exc).__name__))
        label = gold.get("label") if isinstance(gold, dict) else None
        if label not in LABELS:
            raise UsageError("%s: gold label must be one of %s" % (slug, ", ".join(LABELS)))
        stories = load_stories(gold_path.parent)
        if not stories:
            raise UsageError("%s has no user-stories/story-*.md" % slug)
        out.append(Fixture(slug, gold_path.parent, label, splits.get(slug, "all"), stories))
    return out


def _fixture_request(fixture: Fixture, backend: Backend) -> Tuple[Dict[str, Any],
                                                                   Dict[str, Any],
                                                                   Dict[str, Asked], str]:
    """The exact spec-findings request for one fixture spec, and its replay hash."""
    state, questions, index = spec_request(fixture.stories)
    digest = request_hash(canonical_body(build_body(state, questions, backend)))
    return state, questions, index, digest


def _read_recording(directory: Path, digest: str) -> Tuple[str, Optional[Dict[str, Any]]]:
    """("missing" | "synthetic" | "live" | "malformed", body). Only a body that
    `calibrate --live` marked live is scored; hand-written replay fixtures are not."""
    path = directory / ("%s.json" % digest)
    try:
        raw = path.read_text(encoding="utf-8")
    except FileNotFoundError:
        return "missing", None
    except (OSError, UnicodeDecodeError):
        return "malformed", None
    try:
        body = json.loads(raw)
    except ValueError:
        return "malformed", None
    if not isinstance(body, dict):
        return "malformed", None
    meta = body.get(RECORDING_KEY)
    if not (isinstance(meta, dict) and meta.get("source") == "live"):
        return "synthetic", body
    return "live", body


def _class_scores(answers: Any, index: Mapping[str, Asked]) -> Optional[Dict[str, float]]:
    """Highest p per code, or None when any asked question lacks a valid Noul.
    A story with no criteria has no ambiguity question and scores 0.0 there."""
    scores = {code: 0.0 for code in SPEC_CODES}
    for qid, asked in index.items():
        answer = answers.get(qid) if isinstance(answers, dict) else None
        p = answer.get("noul") if isinstance(answer, dict) else None
        if not _unit_interval(p):
            return None
        scores[asked.code] = max(scores[asked.code], float(p))
    return scores


def _floor2(value: float) -> float:
    return float(int(round(value * 100, 6))) / 100  # 0.29 stays 0.29


def choose_band(records: Sequence[Scored], code: str) -> Dict[str, float]:
    """Emit/escalate for one class from the fit records (see SELECTION_RULE).

    Zero false positives on clean fixtures comes first: emit sits above every
    clean score by CLEAN_MARGIN, because three or four clean fixtures cannot
    pin the clean ceiling tighter than that. Maximum recall comes second: emit
    is the lowest gold-positive score that clears the margin. Escalate starts
    just above the highest clean score, so the band between the clean ceiling
    and emit (where the fit data cannot tell classes apart) goes back to the
    orchestrator; it drops lower when a gold positive scored under that, so no
    fit positive is silently cleared."""
    positives = [r.scores[code] for r in records if r.label == code]
    cleans = [r.scores[code] for r in records if r.label == "clean"]
    clean_max = max(cleans) if cleans else 0.0
    floor = round(clean_max + CLEAN_MARGIN, 4)
    above = [p for p in positives if round(p, 4) >= floor]
    if not above:
        return {"emit": NEVER_EMIT, "escalate": 0.0}
    emit = round(min(above), 4)
    escalate = min(round(clean_max + 0.01, 2), _floor2(min(positives)), emit)
    return {"emit": emit, "escalate": escalate}


def score_split(records: Sequence[Scored],
                bands: Mapping[str, Mapping[str, float]]) -> Dict[str, Any]:
    """TP/FP/FN per class at the given bands.

    For contradiction, gap, and ambiguity a story is predicted positive when
    its score reaches emit; `fp_clean` counts those false positives on clean
    fixtures. For clean, a story is predicted clean when no class reaches its
    escalate threshold (no finding and not escalated). A non-clean story
    predicted clean is a silent miss: neither Jev nor the orchestrator sees it."""
    out: Dict[str, Any] = {cls: {"tp": 0, "fp": 0, "fp_clean": 0, "fn": 0} for cls in LABELS}
    escalated = silent = 0
    for rec in records:
        raised = in_band = False
        for code in SPEC_CODES:
            outcome = band(rec.scores[code], bands[code])
            raised = raised or outcome != "clean"
            in_band = in_band or outcome == "escalate"
            if rec.label == code:
                out[code]["tp" if outcome == "finding" else "fn"] += 1
            elif outcome == "finding":
                out[code]["fp"] += 1
                if rec.label == "clean":
                    out[code]["fp_clean"] += 1
        if rec.label == "clean":
            out["clean"]["fn" if raised else "tp"] += 1
        elif not raised:
            out["clean"]["fp"] += 1
            silent += 1
        escalated += int(in_band)
    out.update(stories=len(records), escalated=escalated, silent_miss=silent)
    return out


def _scoring_backend(args: argparse.Namespace, fixtures: Sequence[Fixture],
                     recordings: Path) -> Optional[Backend]:
    """`--backend`, else the configured backend, else the one backend that has
    live recordings for these fixtures (None when neither has any)."""
    if args.backend:
        return BACKENDS[args.backend]
    configured = BACKENDS.get(_config_value(args.repo) or "")
    if configured is not None:
        return configured
    found = []
    for name in sorted(BACKENDS):
        if any(_read_recording(recordings, _fixture_request(fx, BACKENDS[name])[3])[0] == "live"
               for fx in fixtures):
            found.append(BACKENDS[name])
    if len(found) > 1:
        raise UsageError("recordings exist for more than one backend; pass --backend")
    return found[0] if found else None


def _record_live(fixtures: Sequence[Fixture], backend: Backend, recordings: Path,
                 environ: Mapping[str, str], transport: Optional[Transport],
                 sleep: Callable[[float], None]) -> Tuple[int, int, List[str]]:
    """One live spec-findings request per fixture without a live recording.
    Writes the full response body plus RECORDING_KEY metadata to
    `<recordings>/<hash>.json`. Returns (requested, reused, failure reasons)."""
    key_var = _key_var(backend, environ)
    secret = environ[key_var].strip() if key_var else None
    send = transport or live_transport
    today = time.strftime("%Y-%m-%d", time.gmtime())
    requested = reused = 0
    failures: List[str] = []
    for fx in fixtures:
        state, questions, index, digest = _fixture_request(fx, backend)
        if _read_recording(recordings, digest)[0] == "live":
            reused += 1
            continue
        captured: Dict[str, HttpResponse] = {}

        def capture(url: str, headers: Dict[str, str], payload: bytes) -> HttpResponse:
            resp = send(url, headers, payload)
            captured["resp"] = resp
            return resp

        requested += 1
        j = judge(state, questions, backend, environ, transport=capture, sleep=sleep)
        if j.verdict != "pass" or j.answers is None or "resp" not in captured:
            failures.append(_primary(j.reasons))
            continue
        if _class_scores(j.answers, index) is None:
            failures.append("malformed_response")
            continue
        body = json.loads(captured["resp"].body.decode("utf-8"))
        body[RECORDING_KEY] = {"source": "live", "backend": backend.name,
                               "recorded_on": today, "fixture": fx.slug}
        text = json.dumps(body, indent=2, sort_keys=True) + "\n"
        if secret and secret in text:
            failures.append("key_in_response")  # never written to disk
            continue
        try:
            recordings.mkdir(parents=True, exist_ok=True)
            (recordings / ("%s.json" % digest)).write_text(text, encoding="utf-8")
        except OSError as exc:
            raise UsageError("--recordings not writable: %s (%s)" % (recordings,
                                                                      type(exc).__name__))
    return requested, reused, sorted(set(failures), key=failures.index)


def _write_calibrated(bands: Mapping[str, Any], backend: Backend, model: str,
                      recorded_on: str, meta: Mapping[str, Any]) -> None:
    """Rewrite THRESHOLDS_PATH with the chosen bands. Other keys (ac_shadow)
    are kept."""
    try:
        data, _reasons = load_thresholds()
    except ThresholdsError:
        data = _default_thresholds()
    data = dict(data)
    data.update(backend=backend.name, model=model, calibrated=True,
                calibrated_on=recorded_on, spec_findings=dict(bands), calibration=dict(meta))
    tmp = THRESHOLDS_PATH.with_name(THRESHOLDS_PATH.name + ".tmp")
    try:
        tmp.write_text(json.dumps(data, indent=2) + "\n", encoding="utf-8")
        os.replace(str(tmp), str(THRESHOLDS_PATH))
    except OSError as exc:
        raise UsageError("thresholds not writable: %s (%s)" % (THRESHOLDS_PATH,
                                                               type(exc).__name__))


def _counts_line(split: str, cls: str, c: Mapping[str, int]) -> str:
    return "calibrate: split=%s class=%s tp=%d fp=%d fp_clean=%d fn=%d" % (
        split, cls, c["tp"], c["fp"], c["fp_clean"], c["fn"])


def calibrate(args: argparse.Namespace, environ: Mapping[str, str],
              transport: Optional[Transport], sleep: Callable[[float], None]) -> int:
    """Score recorded spec-findings responses against gold labels and choose
    per-class emit/escalate (Story 4). Scoring reads recordings only; `--live`
    first records every fixture that lacks one (double opt-in required)."""
    fixtures = load_fixtures(args.fixtures)
    replay = environ.get(REPLAY_ENV, "")
    if args.live and replay:
        raise UsageError("--live records real responses; unset %s first" % REPLAY_ENV)
    if args.live and args.backend:
        raise UsageError("--backend selects recordings to score; --live uses the backend "
                         "named in .writ/config.md")
    recordings: Path = args.recordings or (Path(replay) if replay else DEFAULT_RECORDINGS)
    live_tail = ""
    failures: List[str] = []
    if args.live:
        res = resolve(args.repo, environ)
        if res.verdict != "pass":
            tail = "backend=%s" % (res.backend.name if res.backend else "none")
            if "no_api_key" in res.reasons and res.backend is not None:
                tail += " export=%s" % res.backend.key_vars[0]
            return _emit("unverifiable", res.reasons,
                         "jev-judge: unverifiable (%s) %s" % (res.reasons[0], tail))
        backend: Optional[Backend] = res.backend
        requested, reused, failures = _record_live(fixtures, backend, recordings, environ,
                                                   transport, sleep)
        live_tail = " requested=%d reused=%d" % (requested, reused)
    else:
        backend = _scoring_backend(args, fixtures, recordings)
    if backend is None:
        return _emit("unverifiable", ["no_live_run"],
                     "jev-judge: unverifiable (no_live_run) fixtures=%d recorded=0 "
                     "thresholds_written=0" % len(fixtures))
    info = [] if backend.pinned else ["model_unpinned"]

    scored: List[Scored] = []
    models, dates = set(), set()
    missing = 0
    for fx in fixtures:
        _state, _questions, index, digest = _fixture_request(fx, backend)
        kind, body = _read_recording(recordings, digest)
        if kind in ("missing", "synthetic"):
            missing += 1
            continue
        scores = _class_scores(body.get("answers"), index) if body is not None else None
        if kind == "malformed" or scores is None:
            return _emit("fail", ["malformed_response"] + info,
                         "jev-judge: fail (malformed_response) fixture=%s backend=%s"
                         % (_one_line(fx.slug, None), backend.name))
        on = body[RECORDING_KEY].get("recorded_on")
        if not (isinstance(on, str) and DATE.fullmatch(on)):
            return _emit("fail", ["malformed_response"] + info,
                         "jev-judge: fail (malformed_response) fixture=%s backend=%s"
                         % (_one_line(fx.slug, None), backend.name))
        models.add(_safe_token(body.get("model"), None))
        dates.add(on)
        scored.append(Scored(fx.slug, fx.label, fx.split, scores))

    base = "fixtures=%d backend=%s" % (len(fixtures), backend.name)
    if not scored and not args.live:
        return _emit("unverifiable", ["no_live_run"] + info,
                     "jev-judge: unverifiable (no_live_run) %s recorded=0 thresholds_written=0"
                     % base)
    if missing:
        return _emit("unverifiable", ["recordings_incomplete"] + failures + info,
                     "jev-judge: unverifiable (recordings_incomplete) %s recorded=%d missing=%d%s "
                     "thresholds_written=0" % (base, len(scored), missing, live_tail))
    if len(models) != 1 or INVALID in models:
        return _emit("unverifiable", ["mixed_models"] + info,
                     "jev-judge: unverifiable (mixed_models) %s models=%d thresholds_written=0"
                     % (base, len(models)))
    model = next(iter(models))
    if backend.pinned and model != backend.model:
        return _emit("unverifiable", ["model_mismatch"] + info,
                     "jev-judge: unverifiable (model_mismatch) %s model=%s expected=%s"
                     % (base, model, backend.model))

    split_names = sorted({r.split for r in scored})
    fit = "dev" if "dev" in split_names else "all"
    fit_records = [r for r in scored if r.split == fit]
    if not any(r.label == "clean" for r in fit_records):
        raise UsageError("the %s split has no clean fixture; zero clean false positives "
                         "cannot be checked" % fit)
    bands = {code: choose_band(fit_records, code) for code in SPEC_CODES}
    unseparated = [code for code in SPEC_CODES if bands[code]["emit"] == NEVER_EMIT]

    per_split: Dict[str, Any] = {}
    for rec in scored:
        print("calibrate: fixture=%s split=%s label=%s %s" % (
            _one_line(rec.slug, None), rec.split, rec.label,
            " ".join("%s=%.2f" % (c, rec.scores[c]) for c in SPEC_CODES)), file=sys.stderr)
    for split in split_names:
        result = score_split([r for r in scored if r.split == split], bands)
        per_split[split] = result
        for cls in LABELS:
            print(_counts_line(split, cls, result[cls]), file=sys.stderr)
        print("calibrate: split=%s stories=%d escalated=%d silent_miss=%d" % (
            split, result["stories"], result["escalated"], result["silent_miss"]),
            file=sys.stderr)
    for code in SPEC_CODES:
        print("calibrate: class=%s emit=%.2f escalate=%.2f%s" % (
            code, bands[code]["emit"], bands[code]["escalate"],
            " unseparated" if code in unseparated else ""), file=sys.stderr)

    written = 0
    if args.write_thresholds:
        meta = {"fixtures": len(scored), "fit_split": fit, "rule": SELECTION_RULE,
                "unseparated": unseparated,
                "splits": {name: {k: v for k, v in res.items()}
                           for name, res in per_split.items()}}
        _write_calibrated(bands, backend, model, max(dates), meta)
        written = 1
    reasons = ["scored"] + (["unseparated"] if unseparated else []) + info
    summary = "jev-judge: pass (scored) fixtures=%d fit=%s backend=%s model=%s %s" % (
        len(scored), fit, backend.name, model,
        " ".join("%s=%.2f/%.2f" % (c, bands[c]["emit"], bands[c]["escalate"])
                 for c in SPEC_CODES))
    if unseparated:
        summary += " unseparated=%s" % ",".join(unseparated)
    headline = "test" if "test" in per_split else fit
    summary += " %s_escalated=%d/%d%s thresholds_written=%d" % (
        headline, per_split[headline]["escalated"], per_split[headline]["stories"], live_tail,
        written)
    return _emit("pass", reasons, summary)


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__,
                                     formatter_class=argparse.RawDescriptionHelpFormatter)
    sub = parser.add_subparsers(dest="action", required=True)
    p = sub.add_parser("status", help="report whether the judgment provider is enabled")
    p.add_argument("--repo", "--project", dest="repo", type=Path, default=Path("."))
    p = sub.add_parser("probe", help="send one judgment request and report the outcome")
    p.add_argument("--repo", "--project", dest="repo", type=Path, default=Path("."))
    p.add_argument("--state-file", type=Path, required=True)
    p.add_argument("--questions-file", type=Path, required=True)
    p.add_argument("--backend", choices=sorted(BACKENDS),
                   help="replay only: pick the backend whose request shape to replay")
    p = sub.add_parser("spec-findings",
                       help="judge a spec's stories in one request; write findings JSON")
    p.add_argument("--repo", "--project", dest="repo", type=Path, default=Path("."))
    p.add_argument("--spec", type=Path, required=True)
    p.add_argument("--out", type=Path, required=True)
    p.add_argument("--backend", choices=sorted(BACKENDS),
                   help="replay only: pick the backend whose request shape to replay")
    p = sub.add_parser("ac-shadow",
                       help="judge a story's criteria beside the evaluator; append a shadow row")
    p.add_argument("--repo", "--project", dest="repo", type=Path, default=Path("."))
    p.add_argument("--story", type=Path, required=True)
    p.add_argument("--tests-output", type=Path, required=True)
    p.add_argument("--diff", type=Path, required=True)
    p.add_argument("--review-output", type=Path, required=True)
    p.add_argument("--log", type=Path, default=None,
                   help="shadow log (default <repo>/.writ/state/jev-shadow.jsonl)")
    p.add_argument("--backend", choices=sorted(BACKENDS),
                   help="replay only: pick the backend whose request shape to replay")
    p = sub.add_parser("calibrate",
                       help="score recorded spec-findings responses against gold labels")
    p.add_argument("--repo", "--project", dest="repo", type=Path, default=Path("."))
    p.add_argument("--fixtures", type=Path, required=True,
                   help="labeled fixtures: <dir>/*/gold.json plus optional splits.json")
    p.add_argument("--live", action="store_true",
                   help="first record every fixture without a live recording (double opt-in)")
    p.add_argument("--write-thresholds", action="store_true",
                   help="after a scored run, write the chosen bands to jev-thresholds.json")
    p.add_argument("--backend", choices=sorted(BACKENDS),
                   help="score this backend's recordings (not with --live)")
    p.add_argument("--recordings", type=Path, default=None,
                   help="recorded responses (default $WRIT_JEV_REPLAY, else "
                        "scripts/tests/fixtures/jev-replay)")
    p = sub.add_parser("shadow-report",
                       help="agreement and the promotion rule over the shadow log (no network)")
    p.add_argument("--repo", "--project", dest="repo", type=Path, default=Path("."))
    p.add_argument("--log", type=Path, default=None,
                   help="shadow log (default <repo>/.writ/state/jev-shadow.jsonl)")
    return parser


def main(argv: Optional[List[str]] = None,
         environ: Optional[Mapping[str, str]] = None,
         transport: Optional[Transport] = None,
         sleep: Optional[Callable[[float], None]] = None) -> int:
    parser = build_parser()
    try:
        args = parser.parse_args(argv)
    except SystemExit as exc:
        code = exc.code
        return int(code) if isinstance(code, int) else 2
    env = os.environ if environ is None else environ
    try:
        if not args.repo.is_dir():
            raise UsageError("--repo is not a directory: %s" % args.repo)
        if args.action == "status":
            return status(args.repo, env)
        if args.action == "probe":
            return probe(args, env, transport, sleep or time.sleep)
        if args.action == "spec-findings":
            return spec_findings(args, env, transport, sleep or time.sleep)
        if args.action == "ac-shadow":
            return ac_shadow(args, env, transport, sleep or time.sleep)
        if args.action == "calibrate":
            return calibrate(args, env, transport, sleep or time.sleep)
        if args.action == "shadow-report":
            return shadow_report(args)
    except UsageError as exc:
        print("error: %s" % exc, file=sys.stderr)
        return 2
    return 2


if __name__ == "__main__":
    sys.exit(main())
