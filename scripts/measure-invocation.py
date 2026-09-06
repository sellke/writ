#!/usr/bin/env python3
"""Per-invocation load measurement for Writ commands.

Phase 10's token success criterion reads *"`per_surface.commands.chars` drops
materially from 516,589 — **measured per-invocation load, not just file
size**"*. Nothing measured that. `eval-leanness.py` weighs the whole
`commands/` directory, which is the right instrument for surface drift and
the wrong one for the question progressive disclosure actually asks.

An invocation does not load `commands/`. It loads:

    system-instructions.md      the root behavioral contract   ┐ shared base,
  + commands/_preamble.md       standing instructions          ┘ every run
  + commands/<name>.md          the one command being run
  + skills/<n>/SKILL.md ...     by one of TWO mechanisms, which cost
                                differently and must not be conflated

The base is paid by every invocation and progressive disclosure cannot reduce
it, which bounds what the exercise can achieve.

### The two skill mechanisms (this distinction is the whole design)

**`required_skills:` frontmatter is EAGER.** `system-instructions.md`: the
harness loads the skill *"before any phase work begins"*;
`adapters/claude-code.md:396` says the same. It is a static array, so *"only
what that invocation needs"* is fixed per **command**, not per **run** — every
invocation pays for every declared skill. **Declared skills belong in the
floor.**

**An inline `Read skills/<n>/SKILL.md` in the body is CONDITIONAL.** The agent
issues that call only if execution reaches that step, so a skipped gate is
genuinely free. Seven commands already use this (`implement-story.md:525` ->
`tdd-cycle`). **Inline skills belong above the floor.**

  floor    = base + command + eagerly declared skills   always paid
  ceiling  = floor + inline-read skills                 worst-case path

An earlier version of this module counted `required_skills:` as conditional.
That was wrong, and it mattered: it understated the floor and would have let
progressive disclosure self-certify against a number nobody pays.
[ADR-021](../.writ/decision-records/adr-021-progressive-disclosure-token-budget.md)
caveat 2 warns disclosure can *raise* total load — under the eager mechanism it
essentially always does, because bytes moved out of a command reappear in the
floor plus per-skill overhead. Only the conditional mechanism can lower it.

### On tokens (roadmap caveat 1)

Bytes here are a **measurement**. Tokens are a **count** when
`ANTHROPIC_API_KEY` is in the environment — every measured text is sent to
the Anthropic Messages `count_tokens` endpoint for the model under test — and
an **estimate** otherwise. The output always says which it did via
`token_method` and `token_method_validated`.

The roadmap's `chars/4` was never validated against a tokenizer — it is an
assumption that has been quoted as though it were measured (`~129k tokens`).
This script does not repeat that. Without a key it records the divisor it
used, marks the estimate unvalidated, and accepts `--chars-per-token` so the
ratio can be calibrated. With a key it counts. Writ ships zero third-party
dependencies, so the API client is `urllib` and nothing is imported;
`tiktoken` is used only if it already happens to be installed and no key is
set.

Counts are cached by content hash (`sha256(model + NUL + text)`) under
`.writ/state/token-cache.json` — hashes and integers only, never the text,
the model name, or the key — so a second run over an unchanged tree makes
zero requests. A request that fails degrades that one text to the estimate,
increments `token_failures`, and flips `token_method_validated` to false; an
authentication failure stops further requests. The key is read from
`os.environ` only and never appears in the report, the cache, or a warning.

This is the same labeling discipline ADR-019 imposes on
`story_context_bytes`: a proxy may be reported, but never under a name that
reads like a measurement.

Usage:
  measure-invocation.py [--root .] [--command NAME] [--chars-per-token 4.0]
                        [--format json|table]
                        [--tokenizer auto|anthropic|estimate]
                        [--model claude-fable-5-1]
                        [--cache <root>/.writ/state/token-cache.json]

Always exits 0 — measurement never blocks its caller. The only write is the
token-count cache, and only on the Anthropic path, only when a new count was
obtained; a cache that cannot be written is a warning, not a failure.
"""

from __future__ import annotations

import argparse
import hashlib
import http.client
import importlib.util
import json
import os
import re
import socket
import statistics
import sys
import urllib.error
import urllib.request

HERE = os.path.dirname(os.path.abspath(__file__))

# The roadmap's inherited ratio. Named, not buried, precisely because it is an
# assumption rather than a finding — see the module docstring.
DEFAULT_CHARS_PER_TOKEN = 4.0

# --- the Anthropic count_tokens path ---------------------------------------
# Header value confirmed against the API reference (Messages → Count tokens)
# on 2026-09-06. A later bump is this one line.
ANTHROPIC_COUNT_TOKENS_URL = "https://api.anthropic.com/v1/messages/count_tokens"
ANTHROPIC_VERSION = "2023-06-01"
API_KEY_ENV = "ANTHROPIC_API_KEY"
DEFAULT_MODEL = "claude-fable-5-1"
REQUEST_TIMEOUT_SECONDS = 10.0
TOKENIZER_CHOICES = ("auto", "anthropic", "estimate")
TOKEN_CACHE_RELPATH = os.path.join(".writ", "state", "token-cache.json")

TOKEN_NOTE = (
    "Bytes are measured. Tokens are NOT measured: no tokenizer was available, "
    "so token figures are an estimate at the recorded chars_per_token ratio. "
    "The chars/4 ratio inherited from .writ/product/roadmap.md has never been "
    "validated against a real tokenizer — treat every *_tokens_estimated "
    "value as an order-of-magnitude figure. Set ANTHROPIC_API_KEY in the "
    "environment to count every measured text with the Anthropic "
    "count_tokens endpoint instead."
)

TOKEN_NOTE_TOKENIZER = (
    "Bytes are measured and tokens were counted with a real tokenizer "
    "({encoding}). These are not an estimate; chars_per_token is reported as "
    "the observed ratio for this corpus, which is the figure the roadmap's "
    "unvalidated chars/4 assumption should be replaced with."
)

TOKEN_NOTE_ANTHROPIC = (
    "Bytes are measured and tokens were counted with the Anthropic Messages "
    "count_tokens endpoint for model {model}. These are not an estimate. "
    "chars_per_token is the divisor a text would fall back to if its request "
    "failed; none did."
)

TOKEN_NOTE_ANTHROPIC_DEGRADED = (
    "Bytes are measured. Tokens were counted with the Anthropic Messages "
    "count_tokens endpoint for model {model}, except {count} text(s) whose "
    "request failed and fell back to the chars_per_token estimate: {items}. "
    "token_method_validated is therefore false. First failure: {reason}"
)


def _load_leanness():
    """Reuse eval-leanness.py's parsers rather than forking them.

    Hyphenated filename, so it loads by path — the recipe already used by
    test_archive_sweep.py and friends. Sitting beside this file, it is always
    present regardless of which --root is being measured.
    """
    path = os.path.join(HERE, "eval-leanness.py")
    spec = importlib.util.spec_from_file_location("_leanness_helpers", path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


_L = _load_leanness()


def _read_bytes(path: str) -> int:
    try:
        with open(path, "rb") as handle:
            return len(handle.read())
    except OSError:
        return 0


def _read_lines(path: str) -> int:
    try:
        with open(path, encoding="utf-8") as handle:
            return handle.read().count("\n")
    except (OSError, UnicodeDecodeError):
        return 0


INLINE_READ = re.compile(r"Read\s+skills/([A-Za-z0-9._-]+)/SKILL\.md")

# Where procedural work starts. A `Read` above this is executed on the way in,
# regardless of which branch the run takes.
FIRST_STEP = re.compile(
    r"^#{2,4}\s+(Command Process|Phase\s+\d|Step\s+\d|Gate\s+\d)", re.M)

CEILING_NOTE = (
    "ceiling_bytes is an ENVELOPE, not a path: it sums every inline read in the "
    "file, including reads on mutually exclusive branches that no single "
    "invocation can both reach. The maximal *reachable* path is therefore at or "
    "below this figure and must be derived by hand. Treat the envelope as an "
    "upper bound, never as what a run costs."
)


def _inline_read_skills(path: str) -> list[str]:
    """Skill names an `Read skills/<n>/SKILL.md` in the body would load.

    This is the genuinely conditional mechanism — `system-instructions.md`
    documents it as the standing alternative to `required_skills:`, and the
    agent only issues the call if execution reaches that step. Seven commands
    already use it (e.g. `implement-story.md:525` -> `tdd-cycle`), so a tool
    that only reads frontmatter understates their real cost.

    Frontmatter is excluded so a `required_skills:` block is never mistaken
    for an inline read. Order-preserving, deduplicated.
    """
    try:
        with open(path, encoding="utf-8") as handle:
            text = handle.read()
    except (OSError, UnicodeDecodeError):
        return []
    if text.startswith("---"):
        end = text.find("\n---", 3)
        if end != -1:
            text = text[end + 4:]
    step = FIRST_STEP.search(text)
    boundary = step.start() if step else None

    names: list[str] = []
    hoisted: list[str] = []
    for match in INLINE_READ.finditer(text):
        name = match.group(1)
        if name not in names:
            names.append(name)
        # No step heading -> structure undetectable -> no verdict. A false
        # accusation is worse than a missed one for an advisory check.
        if boundary is not None and match.start() < boundary and name not in hoisted:
            hoisted.append(name)
    return names, hoisted


def _tokenizer():
    """A real tokenizer if one is already installed, else None.

    Never a dependency: Writ ships none, and adding one to measure leanness
    would be its own joke. Absent tiktoken, the estimate path runs and says so.
    """
    try:
        import tiktoken  # type: ignore
    except Exception:
        return None
    try:
        return tiktoken.get_encoding("cl100k_base"), "cl100k_base"
    except Exception:
        return None


class TokenCountError(Exception):
    """The one failure type a caller degrades on. Never carries a response
    body — an API error body can quote the request's headers, and the
    x-api-key header is a secret (Business Rule 3)."""


class TokenAuthError(TokenCountError):
    """HTTP 401/403: the key was rejected. Retrying other texts with the same
    key cannot succeed, so the caller stops issuing requests."""


def _count_tokens_anthropic(text: str, model: str, api_key: str,
                            timeout: float = REQUEST_TIMEOUT_SECONDS) -> int:
    """`input_tokens` for one text from the Messages count_tokens endpoint.

    Module-level and importable by path so pipeline-baseline.py can reuse it
    rather than fork it. Raises TokenCountError (or its TokenAuthError
    subtype) on any transport, HTTP, timeout, or malformed-response failure.
    """
    body = json.dumps({"model": model,
                       "messages": [{"role": "user", "content": text}]}).encode("utf-8")
    request = urllib.request.Request(
        ANTHROPIC_COUNT_TOKENS_URL, data=body, method="POST",
        headers={"x-api-key": api_key,
                 "anthropic-version": ANTHROPIC_VERSION,
                 "content-type": "application/json"})
    try:
        with urllib.request.urlopen(request, timeout=timeout) as response:
            raw = response.read()
    except urllib.error.HTTPError as exc:
        # Deliberately not exc.read(): the body may echo request headers.
        if exc.code in (401, 403):
            raise TokenAuthError(
                f"count_tokens returned HTTP {exc.code}: the x-api-key header "
                f"was rejected") from None
        raise TokenCountError(f"count_tokens returned HTTP {exc.code}") from None
    except socket.timeout:  # 3.9: distinct from TimeoutError, so named
        raise TokenCountError(
            f"count_tokens timed out after {timeout:g}s") from None
    except urllib.error.URLError as exc:
        raise TokenCountError(f"count_tokens unreachable: {exc.reason}") from None
    except OSError as exc:
        raise TokenCountError(f"count_tokens transport error: {exc}") from None
    except http.client.HTTPException as exc:
        # IncompleteRead from response.read(), BadStatusLine, LineTooLong,
        # RemoteDisconnected: these subclass Exception, not OSError, so the
        # clauses above miss them. str(exc) reports byte counts or a status
        # line — never the response body.
        raise TokenCountError(f"count_tokens transport error: {exc}") from None
    try:
        payload = json.loads(raw.decode("utf-8"))
    except (UnicodeDecodeError, ValueError):
        raise TokenCountError("count_tokens returned a non-JSON body") from None
    count = payload.get("input_tokens") if isinstance(payload, dict) else None
    if isinstance(count, bool) or not isinstance(count, int) or count < 0:
        raise TokenCountError(
            "count_tokens response carried no non-negative integer input_tokens")
    return count


def token_cache_key(model: str, text: str) -> str:
    """sha256(model + NUL + text): a model change never returns a stale count,
    and NUL cannot occur in a model ID, so the pair is unambiguous."""
    return hashlib.sha256((model + "\0" + text).encode("utf-8")).hexdigest()


class TokenCache:
    """`hash -> int`, nothing else. Nothing in the file identifies the model,
    the text, or the key; a reader learns only that *something* hashed to a
    given digest cost N tokens.

    Tolerates a missing, empty, or malformed file by starting empty. Writes
    once via flush(), and only when a new count was obtained."""

    def __init__(self, path: str):
        self.path = path
        self._entries: dict[str, int] = {}
        self._dirty = False
        self._load()

    def _load(self) -> None:
        try:
            with open(self.path, encoding="utf-8") as handle:
                data = json.load(handle)
        except (OSError, ValueError):
            return
        if not isinstance(data, dict):
            return
        for key, value in data.items():
            if isinstance(key, str) and isinstance(value, int) \
                    and not isinstance(value, bool):
                self._entries[key] = value

    def get(self, model: str, text: str) -> int | None:
        return self._entries.get(token_cache_key(model, text))

    def put(self, model: str, text: str, count: int) -> None:
        key = token_cache_key(model, text)
        if self._entries.get(key) != count:
            self._entries[key] = count
            self._dirty = True

    @property
    def pending(self) -> bool:
        """True when a new count has been put and not yet flushed."""
        return self._dirty

    def flush(self) -> bool:
        """True if written. False if nothing was pending or the write failed
        — check `pending` first to tell those apart. Never raises."""
        if not self._dirty:
            return False
        try:
            os.makedirs(os.path.dirname(self.path) or ".", exist_ok=True)
            with open(self.path, "w", encoding="utf-8") as handle:
                json.dump(self._entries, handle, indent=0, sort_keys=True)
                handle.write("\n")
        except OSError:
            return False
        self._dirty = False
        return True


class _AnthropicCounter:
    """Per-text counting with the cache in front and per-item degradation.

    `count(path, label)` returns the real count for a file, or the estimate
    for that file alone if its request failed. Failures are remembered by
    content hash so a shared skill that fails is one failure, not one per
    command, and is not re-requested within the run. After an auth failure
    no further requests are issued at all.
    """

    def __init__(self, model: str, api_key: str, cache: TokenCache,
                 chars_per_token: float,
                 timeout: float = REQUEST_TIMEOUT_SECONDS):
        self.model = model
        self._api_key = api_key
        self.cache = cache
        self.chars_per_token = chars_per_token
        self.timeout = timeout
        self.failed_labels: list[str] = []
        self.first_failure: str | None = None
        self.fatal: str | None = None
        self._failed_keys: set[str] = set()

    @property
    def failures(self) -> int:
        return len(self._failed_keys)

    def count(self, path: str, label: str) -> int:
        try:
            with open(path, "rb") as handle:
                raw = handle.read()
            text = raw.decode("utf-8")
        except (OSError, UnicodeDecodeError):
            return 0  # unreadable -> 0 tokens, no request (technical-spec §8)
        if not text:
            return 0
        cached = self.cache.get(self.model, text)
        if cached is not None:
            return cached
        estimate = int(round(len(raw) / self.chars_per_token))
        key = token_cache_key(self.model, text)
        if key in self._failed_keys:
            return estimate
        if self.fatal is not None:
            return self._degrade(key, label, estimate, self.fatal)
        try:
            counted = _count_tokens_anthropic(text, self.model, self._api_key,
                                              self.timeout)
        except TokenAuthError as exc:
            self.fatal = str(exc)
            return self._degrade(key, label, estimate, str(exc))
        except TokenCountError as exc:
            return self._degrade(key, label, estimate, str(exc))
        self.cache.put(self.model, text, counted)
        return counted

    def _degrade(self, key: str, label: str, estimate: int, reason: str) -> int:
        self._failed_keys.add(key)
        self.failed_labels.append(label)
        if self.first_failure is None:
            self.first_failure = reason
        return estimate


def measure(root: str, chars_per_token: float = DEFAULT_CHARS_PER_TOKEN,
            command: str | None = None, tokenizer: str = "auto",
            model: str = DEFAULT_MODEL, cache_path: str | None = None) -> dict:
    """The whole report. Never raises on a missing or malformed tree.

    `tokenizer`: `auto` counts with the Anthropic API when ANTHROPIC_API_KEY is
    set and otherwise behaves exactly as before this parameter existed;
    `anthropic` insists on the API (and warns, then estimates, without a key);
    `estimate` is chars/N regardless of what is installed or set.
    """
    if tokenizer not in TOKENIZER_CHOICES:
        raise ValueError(f"tokenizer must be one of {TOKENIZER_CHOICES}, "
                         f"not {tokenizer!r}")
    warnings: list[str] = []

    api_key = os.environ.get(API_KEY_ENV)
    if tokenizer == "anthropic" and not api_key:
        warnings.append(
            f"--tokenizer anthropic was requested but {API_KEY_ENV} is not set "
            f"in the environment; token figures are the chars_per_token "
            f"estimate.")

    counter: _AnthropicCounter | None = None
    encoder = None
    if tokenizer != "estimate" and api_key:
        cache = TokenCache(cache_path or os.path.join(root, TOKEN_CACHE_RELPATH))
        counter = _AnthropicCounter(model, api_key, cache, chars_per_token)
    elif tokenizer == "auto":
        encoder = _tokenizer()

    if counter is not None:
        # validated and token_note are settled after the last text is counted;
        # the per-item fallback estimate lives inside the counter.
        token_method = "anthropic-count-tokens"
    elif encoder is not None:
        enc, encoding_name = encoder

        def to_tokens(text_bytes: int, text: str | None = None) -> int:
            return len(enc.encode(text)) if text is not None else \
                int(round(text_bytes / chars_per_token))
        token_method = f"tokenizer:{encoding_name}"
        validated = True
        token_note = TOKEN_NOTE_TOKENIZER.format(encoding=encoding_name)
    else:
        def to_tokens(text_bytes: int, text: str | None = None) -> int:
            return int(round(text_bytes / chars_per_token))
        token_method = f"estimate:chars/{chars_per_token}"
        validated = False
        token_note = TOKEN_NOTE

    def counted(path: str, label: str) -> int:
        """Real count for one file on the Anthropic path; 0 otherwise (the
        estimate paths divide byte sums, never per-file figures — rounding
        an aggregate is what keeps the no-key output byte-identical)."""
        return counter.count(path, label) if counter is not None else 0

    def total_tokens(byte_sum: int, counted_sum: int) -> int:
        return counted_sum if counter is not None else to_tokens(byte_sum)

    # --- the shared base: paid by every invocation, immune to disclosure ---
    base_components: dict[str, int] = {}
    base_tokens = 0
    for rel in ("system-instructions.md", os.path.join("commands", "_preamble.md")):
        path = os.path.join(root, rel)
        key = rel.replace(os.sep, "/")
        if not os.path.isfile(path):
            base_components[key] = 0
            warnings.append(
                f"{key} is absent from {root} — the shared base is understated "
                f"by its size. Every invocation loads it in a real tree.")
            continue
        base_components[key] = _read_bytes(path)
        base_tokens += counted(path, key)  # counted once, reused per command
    base_bytes = sum(base_components.values())

    # --- per command ---
    commands: dict[str, dict] = {}
    try:
        command_paths = _L.all_command_files(root)
    except Exception:
        command_paths = []
    if not command_paths:
        warnings.append(
            f"no command files found under {root}/commands/ — nothing to measure.")

    for path in command_paths:
        stem = os.path.splitext(os.path.basename(path))[0]
        if _L.is_infra(stem):
            continue  # _preamble.md is base, never an invocable command
        if command is not None and stem != command:
            continue

        command_bytes = _read_bytes(path)
        command_lines = _read_lines(path)
        command_tokens = counted(path, f"commands/{stem}.md")

        fields = _L.read_frontmatter(path) or {}
        declared = _L.parse_skill_names(fields.get("required_skills", ""))
        inlined, hoisted = _inline_read_skills(path)

        eager_skills: list[str] = []
        conditional_skills: list[str] = []
        unresolved: list[str] = []
        eager_bytes = 0
        conditional_bytes = 0
        eager_tokens = 0
        conditional_tokens = 0

        # Declared wins over inlined: `required_skills:` already paid for it
        # before phase 1, so an inline Read of the same skill costs nothing
        # extra. Counting both would double-charge.
        for name in declared:
            skill_path = os.path.join(root, "skills", name, "SKILL.md")
            if os.path.isfile(skill_path):
                eager_skills.append(name)
                eager_bytes += _read_bytes(skill_path)
                eager_tokens += counted(skill_path, f"skills/{name}/SKILL.md")
            else:
                unresolved.append(name)
        for name in inlined:
            if name in declared:
                warnings.append(
                    f"commands/{stem}.md loads `{name}` **both** ways — declared in "
                    f"required_skills: and inline-read in the body. The declaration "
                    f"wins: it is paid on every invocation, so the inline Read buys "
                    f"no conditionality. Drop one.")
                continue
            skill_path = os.path.join(root, "skills", name, "SKILL.md")
            if os.path.isfile(skill_path):
                conditional_skills.append(name)
                conditional_bytes += _read_bytes(skill_path)
                conditional_tokens += counted(skill_path, f"skills/{name}/SKILL.md")
            else:
                unresolved.append(name)

        if hoisted:
            warnings.append(
                f"commands/{stem}.md has hoisted {', '.join(hoisted)} — the inline Read "
                f"sits above the first step, so it is issued on every invocation. "
                f"That is eager loading in conditional syntax: the ceiling reads "
                f"the same, every gate passes, and the saving is gone. Move the "
                f"Read down to the narrowest step that needs it.")

        if unresolved:
            warnings.append(
                f"commands/{stem}.md references skills that resolve to no file: "
                f"{', '.join(sorted(set(unresolved)))}. Their load is unmeasurable, "
                f"so the figures below are a lower bound.")

        # `required_skills:` is EAGER — system-instructions.md: the harness loads
        # it "before any phase work begins", and adapters/claude-code.md:396 says
        # the same. A declared skill is therefore paid on every invocation and
        # belongs in the floor, not above it. Only an inline
        # `Read skills/<n>/SKILL.md` at the point of need is genuinely
        # conditional: the agent issues that call only if execution reaches it.
        floor_bytes = base_bytes + command_bytes + eager_bytes
        ceiling_bytes = floor_bytes + conditional_bytes
        floor_tokens = base_tokens + command_tokens + eager_tokens
        ceiling_tokens = floor_tokens + conditional_tokens

        commands[stem] = {
            "command_bytes": command_bytes,
            "command_lines": command_lines,
            "base_bytes": base_bytes,
            "eager_bytes": eager_bytes,
            "floor_bytes": floor_bytes,
            "conditional_bytes": conditional_bytes,
            "ceiling_bytes": ceiling_bytes,
            "eager_skills": eager_skills,
            "conditional_skills": conditional_skills,
            "hoisted_skills": hoisted,
            "resolved_skills": eager_skills + conditional_skills,
            "unresolved_skills": unresolved,
            "floor_tokens_estimated": total_tokens(floor_bytes, floor_tokens),
            "ceiling_tokens_estimated": total_tokens(ceiling_bytes, ceiling_tokens),
            "base_share_of_floor": (round(base_bytes / floor_bytes, 4)
                                    if floor_bytes else 0.0),
        }

    # --- corpus ---
    floors = [c["floor_bytes"] for c in commands.values()]
    total_command_lines = sum(c["command_lines"] for c in commands.values())
    total_command_bytes = sum(c["command_bytes"] for c in commands.values())
    corpus = {
        "commands_measured": len(commands),
        "irreducible_base_bytes": base_bytes,
        "irreducible_base_tokens_estimated": total_tokens(base_bytes, base_tokens),
        "min_floor_bytes": min(floors) if floors else 0,
        "median_floor_bytes": int(statistics.median(floors)) if floors else 0,
        "max_floor_bytes": max(floors) if floors else 0,
        "max_floor_command": (max(commands, key=lambda k: commands[k]["floor_bytes"])
                              if commands else None),
        "mean_bytes_per_command_line": (round(total_command_bytes / total_command_lines, 2)
                                        if total_command_lines else 0),
    }

    # --- the Anthropic path settles its verdict only once every text is in ---
    if counter is not None:
        if counter.fatal is not None:
            warnings.append(
                f"{counter.fatal}. No further count_tokens requests were issued; "
                f"every text from that point fell back to the chars_per_token "
                f"estimate.")
        if counter.failures:
            validated = False
            shown, hidden = counter.failed_labels[:10], counter.failed_labels[10:]
            token_note = TOKEN_NOTE_ANTHROPIC_DEGRADED.format(
                model=model, count=counter.failures,
                items=", ".join(shown) + (f" (+{len(hidden)} more)" if hidden else ""),
                reason=counter.first_failure)
        else:
            validated = True
            token_note = TOKEN_NOTE_ANTHROPIC.format(model=model)
        if counter.cache.pending and not counter.cache.flush():
            warnings.append(
                f"token cache could not be written to {counter.cache.path}; "
                f"the next run will re-request every text counted this run.")

    report = {
        "schema": "invocation-load-v1",
        "root": os.path.abspath(root),
        "token_method": token_method,
        "token_method_validated": validated,
        "chars_per_token": chars_per_token,
    }
    if counter is not None:
        # Additive and conditional: absent without a key so the no-key output
        # stays byte-identical to the pre-Story-2 output (AC-2.2).
        report["token_model"] = model
        report["token_failures"] = counter.failures
    report.update({
        "token_note": token_note,
        "ceiling_note": CEILING_NOTE,
        "base": {"bytes": base_bytes, "components": base_components},
        "commands": commands,
        "corpus": corpus,
        "warnings": warnings,
    })
    return report


def render_table(report: dict) -> str:
    rows = sorted(report["commands"].items(),
                  key=lambda kv: kv[1]["floor_bytes"], reverse=True)
    method = f"token method: {report['token_method']}"
    if report.get("token_model"):
        method += f" [{report['token_model']}]"
    method += f"  (validated: {report['token_method_validated']}"
    if "token_failures" in report:
        method += f", token_failures: {report['token_failures']}"
    method += ")"
    out = [
        f"Per-invocation load — {report['root']}",
        method,
        "",
        f"shared base (every invocation): {report['base']['bytes']:,} bytes",
    ]
    for key, value in report["base"]["components"].items():
        out.append(f"    {key:<32} {value:>10,}")
    out += ["", f"{'command':<26}{'floor':>12}{'cond':>10}{'ceiling':>12}"
                f"{'base%':>8}{'lines':>8}"]
    out.append("-" * 76)
    for stem, data in rows:
        out.append(
            f"{stem:<26}{data['floor_bytes']:>12,}{data['conditional_bytes']:>10,}"
            f"{data['ceiling_bytes']:>12,}{data['base_share_of_floor'] * 100:>7.1f}%"
            f"{data['command_lines']:>8,}")
    corpus = report["corpus"]
    out += [
        "-" * 76,
        f"commands: {corpus['commands_measured']}   "
        f"floor min/median/max: {corpus['min_floor_bytes']:,} / "
        f"{corpus['median_floor_bytes']:,} / {corpus['max_floor_bytes']:,}"
        f"  (worst: {corpus['max_floor_command']})",
        f"mean bytes per command line: {corpus['mean_bytes_per_command_line']}",
        "",
        report["token_note"],
    ]
    for warning in report["warnings"]:
        out.append(f"WARNING: {warning}")
    return "\n".join(out)


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Measure what a Writ command actually loads at invocation.")
    parser.add_argument("--root", default=".")
    parser.add_argument("--command", default=None,
                        help="measure one command instead of the whole corpus")
    parser.add_argument("--chars-per-token", type=float,
                        default=DEFAULT_CHARS_PER_TOKEN,
                        help="divisor for the token ESTIMATE; the default is the "
                             "roadmap's unvalidated chars/4")
    parser.add_argument("--format", choices=("json", "table"), default="json")
    parser.add_argument("--tokenizer", choices=TOKENIZER_CHOICES, default="auto",
                        help=f"auto: count with the Anthropic API when {API_KEY_ENV} "
                             f"is set, otherwise estimate; anthropic: insist on the "
                             f"API; estimate: chars/N regardless")
    parser.add_argument("--model", default=DEFAULT_MODEL,
                        help="model ID sent to count_tokens (default %(default)s)")
    parser.add_argument("--cache", default=None,
                        help="token-count cache path (default "
                             "<root>/.writ/state/token-cache.json)")
    args = parser.parse_args()

    report = measure(args.root, chars_per_token=args.chars_per_token,
                     command=args.command, tokenizer=args.tokenizer,
                     model=args.model, cache_path=args.cache)
    if args.format == "table":
        print(render_table(report))
    else:
        print(json.dumps(report, indent=2))
    return 0


if __name__ == "__main__":
    sys.exit(main())
