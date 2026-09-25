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


def _judgment_summary(j: Judgment) -> str:
    parts = ["jev-judge: %s (%s)" % (j.verdict, _primary(j.reasons)),
             "backend=%s" % j.backend.name,
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


def probe(args: argparse.Namespace, environ: Mapping[str, str],
          transport: Optional[Transport], sleep: Callable[[float], None]) -> int:
    state = _read_json_object(args.state_file, "--state-file")
    questions = _read_questions(args.questions_file)
    replay = bool(environ.get(REPLAY_ENV, ""))
    if args.backend and not replay:
        raise UsageError("--backend is replay-only; the live backend comes from "
                         ".writ/config.md (set %s to replay)" % REPLAY_ENV)
    if replay and args.backend:
        backend = BACKENDS[args.backend]
    elif replay:
        value = _config_value(args.repo)
        if value is None:
            return _emit("unverifiable", ["no_config_line"],
                         "jev-judge: unverifiable (no_config_line) backend=none")
        found = BACKENDS.get(value)
        if found is None:
            return _emit("unverifiable", ["provider_disabled"],
                         "jev-judge: unverifiable (provider_disabled) backend=none")
        backend = found
    else:
        res = resolve(args.repo, environ)  # Business Rule 1: live needs both halves
        if res.verdict != "pass":
            return status(args.repo, environ)
        assert res.backend is not None
        backend = res.backend
    j = judge(state, questions, backend, environ, transport=transport, sleep=sleep)
    return _emit(j.verdict, j.reasons, _judgment_summary(j))


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
    except UsageError as exc:
        print("error: %s" % exc, file=sys.stderr)
        return 2
    return 2


if __name__ == "__main__":
    sys.exit(main())
