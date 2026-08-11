#!/usr/bin/env python3
"""Correctness asserter for declared loop bounds (spec: 2026-08-11-loop-bounds).

Emits PASS/FAIL/SKIP TSV lines consumed by scripts/eval.sh check_loop_bounds.

WHAT THIS CHECK OWNS — correctness, not presence.
`2026-08-11-governor-instrumentation` Check 3 owns *presence*: is a `loop:`
block there at all, with `max_iterations` and `on_exhaustion`. This check owns
*correctness*: given a block exists, is it well-formed, legally valued, honestly
cited, and calibrated against reality. A file with **no** `loop:` block is
therefore SKIPped as `deferred_to_check3` and never reported as a finding here.
A maintainer who sees the same missing block reported twice by two checks learns
to skim the registry, and that is how an enforced contract decays back into an
unenforced one.

THE EIGHT ASSERTIONS (sub-specs/technical-spec.md -> The eval check):
  1. `unit` and `calibrated_against` present alongside the two contract-named
     keys, at the top level of `loop:` and in every `nested` entry
  2. `max_iterations` is a positive integer literal - not a range, string, or
     expression
  3. `on_exhaustion` in {quarantine, escalate, halt_reported}; `retry` is
     rejected *by name with its reason*
  4. `calibrated_against` is non-empty and carries a path token or the literal
     `no recorded run`
  5. `unit` values unique within a file; `nested` never contains `nested`
  6. `on_exhaustion: quarantine` only on a unit whose command integrates with
     phase state (a `phase-execution-*.json` record exists for it)
  7. HISTORICAL-RUN REGRESSION: no declared bound sits below a value a real run
     already reached
  8. TRANSCRIPTION DRIFT: every transcribed number is cross-read from its source
     file, never hardcoded here

Assertions 7 and 8 are this check's reason to exist. Presence checking alone
would let a bound of 1 ship green on a command whose recorded runs reached 4 -
the failure the locked contract names as hardest.

NOTHING IN ASSERTION 8 IS HARDCODED. `spec_attempt` is read from
scripts/phase-state.py's own `attempts < N` guard; implement-story's three
numbers are read from its own prose caps and from agents/*-agent.md's
MAX_SELF_FIX_ITERATIONS. A check that hardcoded 2 would pass while
phase-state.py changed underneath it, which is worse than no check at all.

`.writ/state/` IS GITIGNORED. Assertion 7 binds on a maintainer's working copy,
where the run history exists, and has no input in CI or a fresh clone. It SKIPs
there with a stated reason rather than passing silently - a check that passes
because its input is absent is exactly the failure mode ADR-020 diagnosed.
Malformed or unrecognised state-file shapes are also SKIPped, never turned into
findings: a false-failing check trains a maintainer to ignore it.

THE COMMAND LIST IS FIXED AT FIVE and is the enforcement point when a sixth
command acquires a loop - update LOOP_BEARING_COMMANDS with it. Inferring "does
this command loop?" from prose across 32 markdown files would produce false
positives, which is the heading-variant grammar problem ADR-020 rejects.

Reporting convention: PASS/FAIL/SKIP TSV, one line per scenario, matching the
20+ sibling eval-*.py scenario emitters (eval-artifact-integrity.py,
eval-story-deps.py, ...). eval.sh owns findings aggregation; SKIP lines surface
as non-blocking notes so a skip is always reported, never silent.
"""

from __future__ import annotations

import json
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent

# The five commands the roadmap verifies as loop-bearing. Fixed list by design -
# a sixth looping command is caught here or not at all (see module docstring).
LOOP_BEARING_COMMANDS = [
    "implement-phase",
    "implement-spec",
    "implement-story",
    "refactor",
    "verify-spec",
]

REQUIRED_KEYS = ("unit", "max_iterations", "on_exhaustion", "calibrated_against")
LEGAL_ON_EXHAUSTION = ("quarantine", "escalate", "halt_reported")
NO_RECORDED_RUN = "no recorded run"

PATH_TOKEN = re.compile(r"(?:\.writ|commands|agents|scripts|skills|adapters)/[\w./*-]+")

passed = 0
failed = 0
skipped = 0


def emit(name: str, ok: bool, detail: object = "") -> None:
    global passed, failed
    if ok:
        passed += 1
        print(f"PASS\t{name}")
    else:
        failed += 1
        safe = str(detail).replace("\n", "\\n").replace("\t", " ")
        print(f"FAIL\t{name}\t{safe}")


def emit_skip(name: str, reason: str) -> None:
    """A skip is always reported. Never a silent pass."""
    global skipped
    skipped += 1
    safe = str(reason).replace("\n", "\\n").replace("\t", " ")
    print(f"SKIP\t{name}\t{safe}")


# --------------------------------------------------------------------------
# Minimal YAML-subset parser
#
# Writ ships with no dependencies and PyYAML is not available, so this parses
# the block-mapping / block-sequence subset the `loop:` schema uses. It is
# deliberately strict about scalar shape: an integer is returned only for a
# bare, unquoted, all-digit token, so `"twelve"`, `3-5`, and `null` all come
# back as strings and fail assertion 2 rather than being coerced.
# --------------------------------------------------------------------------


def scalar(raw: str) -> object:
    raw = raw.strip()
    if len(raw) >= 2 and raw[0] == raw[-1] and raw[0] in "\"'":
        return raw[1:-1]
    if re.fullmatch(r"[0-9]+", raw):
        return int(raw)
    return raw


def _lines(text: str) -> list[tuple[int, str]]:
    out = []
    for raw in text.split("\n"):
        if not raw.strip() or raw.lstrip().startswith("#"):
            continue
        out.append((len(raw) - len(raw.lstrip(" ")), raw.strip()))
    return out


def _parse(lines: list[tuple[int, str]], i: int, indent: int) -> tuple[object, int]:
    if i >= len(lines) or lines[i][0] < indent:
        return None, i

    if lines[i][1].startswith("- "):
        items: list[object] = []
        while i < len(lines) and lines[i][0] == indent and lines[i][1].startswith("- "):
            item_indent = indent + 2
            sub = [(item_indent, lines[i][1][2:].strip())]
            j = i + 1
            while j < len(lines) and lines[j][0] > indent:
                sub.append(lines[j])
                j += 1
            value, _ = _parse(sub, 0, item_indent)
            items.append(value)
            i = j
        return items, i

    mapping: dict[str, object] = {}
    while i < len(lines) and lines[i][0] == indent and not lines[i][1].startswith("- "):
        text = lines[i][1]
        if ":" not in text:
            mapping.setdefault("__malformed__", text)
            i += 1
            continue
        key, _, rest = text.partition(":")
        key, rest = key.strip(), rest.strip()
        if rest:
            mapping[key] = scalar(rest)
            i += 1
        elif i + 1 < len(lines) and lines[i + 1][0] > indent:
            mapping[key], i = _parse(lines, i + 1, lines[i + 1][0])
        else:
            mapping[key] = None
            i += 1
    return mapping, i


def frontmatter(text: str) -> tuple[dict, str | None]:
    """Return (parsed frontmatter mapping, parse error or None)."""
    raw = text.split("\n")
    if not raw or raw[0].strip() != "---":
        return {}, "file does not open with a --- frontmatter fence"
    body: list[str] = []
    for line in raw[1:]:
        if line.strip() == "---":
            break
        body.append(line)
    else:
        return {}, "frontmatter fence is never closed"
    try:
        parsed, _ = _parse(_lines("\n".join(body)), 0, 0)
    except Exception as exc:  # never crash on a malformed file
        return {}, f"frontmatter is unparseable: {exc}"
    return (parsed if isinstance(parsed, dict) else {}), None


# --------------------------------------------------------------------------
# Assertions 1-6: schema correctness of one `loop:` block
# --------------------------------------------------------------------------


def validate_entry(where: str, entry: object, errors: list[str], nested_ok: bool) -> str | None:
    """Validate one loop declaration. Returns its `unit` if usable."""
    if not isinstance(entry, dict):
        errors.append(f"{where} must be a mapping of the four required keys, not "
                      f"a {type(entry).__name__} ({entry!r})")
        return None

    for key in REQUIRED_KEYS:
        if key not in entry or entry[key] is None:
            errors.append(f"{where} is missing the required key '{key}'")

    value = entry.get("max_iterations")
    if "max_iterations" in entry and value is not None:
        if not isinstance(value, int):
            errors.append(f"{where} max_iterations must be a positive integer literal, "
                          f"not {value!r} - a range, string, or expression is not a bound")
        elif value < 1:
            errors.append(f"{where} max_iterations must be positive, not {value}")

    disposition = entry.get("on_exhaustion")
    if disposition is not None:
        if disposition == "retry":
            errors.append(
                f"{where} on_exhaustion 'retry' is illegal. Retry is a PRE-exhaustion "
                "state, already governed in code by scripts/phase-state.py's "
                "`attempts < 2` guard; admitting it here would create a second, weaker "
                f"retry authority in markdown. Legal values: {', '.join(LEGAL_ON_EXHAUSTION)}")
        elif disposition not in LEGAL_ON_EXHAUSTION:
            errors.append(f"{where} on_exhaustion {disposition!r} is not one of "
                          f"{', '.join(LEGAL_ON_EXHAUSTION)}")

    citation = entry.get("calibrated_against")
    if isinstance(citation, str) and citation.strip():
        if not (PATH_TOKEN.search(citation) or NO_RECORDED_RUN in citation.lower()):
            errors.append(f"{where} calibrated_against cites no path and does not say "
                          f"'{NO_RECORDED_RUN}' - a bound with no citation is a defect")
    elif "calibrated_against" in entry and entry["calibrated_against"] is not None:
        errors.append(f"{where} calibrated_against must be a non-empty string")

    if not nested_ok and "nested" in entry:
        errors.append(f"{where} carries its own 'nested' - nesting is capped at one "
                      "level; a nested entry may not itself nest")

    unit = entry.get("unit")
    return unit if isinstance(unit, str) and unit else None


def validate_loop(command: str, loop: object, phase_state_integrated: bool) -> list[str]:
    errors: list[str] = []
    units: list[str] = []

    unit = validate_entry(f"{command} loop:", loop, errors, nested_ok=True)
    if unit:
        units.append(unit)

    nested = loop.get("nested") if isinstance(loop, dict) else None
    if nested is not None:
        if not isinstance(nested, list):
            errors.append(f"{command} loop.nested must be a list of entries, not a "
                          f"{type(nested).__name__}")
            nested = []
        for index, entry in enumerate(nested):
            unit = validate_entry(f"{command} loop.nested[{index}]:", entry, errors,
                                  nested_ok=False)
            if unit:
                units.append(unit)

    for name in sorted({u for u in units if units.count(u) > 1}):
        errors.append(f"{command} declares the unit '{name}' more than once - every "
                      "unit in a file must name a distinct thing being counted")

    # Assertion 6: quarantine calls scripts/phase-state.py quarantine, which needs
    # a phase-execution record to act on. Legality is derived from the command file
    # itself, never from a hardcoded allow-list.
    entries = [loop] if isinstance(loop, dict) else []
    entries += [e for e in (nested or []) if isinstance(e, dict)]
    for entry in entries:
        if entry.get("on_exhaustion") == "quarantine" and not phase_state_integrated:
            errors.append(
                f"{command} unit '{entry.get('unit')}' declares on_exhaustion: quarantine, "
                "but the command has no phase-execution-*.json record to quarantine "
                "against. Use escalate (or halt_reported) instead")
    return errors


# --------------------------------------------------------------------------
# Assertion 7: historical-run regression
# --------------------------------------------------------------------------


def recorded_maxima(state_dir: Path) -> tuple[dict[str, int], list[str]]:
    """Largest value each bounded unit reached in a recorded run.

    Returns ({unit: max}, notes). Unreadable or unrecognised shapes are skipped
    with a note - never converted into a finding.
    """
    maxima: dict[str, int] = {}
    notes: list[str] = []

    def record(unit: str, value: object, origin: str) -> None:
        if isinstance(value, int) and value > 0:
            if value > maxima.get(unit, 0):
                maxima[unit] = value
        elif value is not None:
            notes.append(f"{origin}: unrecognised value {value!r}")

    if not state_dir.is_dir():
        return maxima, notes

    for path in sorted(state_dir.glob("phase-execution-*.json")):
        try:
            data = json.loads(path.read_text(encoding="utf-8"))
        except Exception as exc:
            notes.append(f"{path.name}: unreadable ({exc})")
            continue
        order = data.get("specOrder")
        if isinstance(order, list):
            record("spec", len(order), path.name)
        else:
            notes.append(f"{path.name}: no specOrder list")

    for path in sorted(state_dir.glob("execution-*.json")):
        try:
            data = json.loads(path.read_text(encoding="utf-8"))
        except Exception as exc:
            notes.append(f"{path.name}: unreadable ({exc})")
            continue
        stories = data.get("stories")
        if isinstance(stories, (list, dict)):
            record("story", len(stories), path.name)
        else:
            notes.append(f"{path.name}: no stories collection")

    for path in sorted(state_dir.glob("*result*.json")):
        try:
            data = json.loads(path.read_text(encoding="utf-8"))
        except Exception as exc:
            notes.append(f"{path.name}: unreadable ({exc})")
            continue
        if "stories_total" in data:
            record("story", data.get("stories_total"), path.name)

    return maxima, notes


def declared_bounds(loop: object) -> dict[str, int]:
    out: dict[str, int] = {}
    entries = [loop] if isinstance(loop, dict) else []
    entries += [e for e in (loop.get("nested") or []) if isinstance(e, dict)] \
        if isinstance(loop, dict) and isinstance(loop.get("nested"), list) else []
    for entry in entries:
        unit, value = entry.get("unit"), entry.get("max_iterations")
        if isinstance(unit, str) and isinstance(value, int):
            out[unit] = value
    return out


def regression_findings(bounds: dict[str, int], maxima: dict[str, int],
                        command: str) -> list[str]:
    findings = []
    for unit, declared in bounds.items():
        observed = maxima.get(unit)
        if observed is not None and declared < observed:
            findings.append(
                f"{command} bounds '{unit}' at {declared}, but a recorded run in "
                f".writ/state/ already reached {observed}. A bound below history "
                "would have failed a run that worked - raise it, never exempt it")
    return findings


# --------------------------------------------------------------------------
# Assertion 8: transcription cross-reads (nothing hardcoded)
# --------------------------------------------------------------------------


def read(rel: str) -> str:
    try:
        return (ROOT / rel).read_text(encoding="utf-8")
    except OSError:
        return ""


def first_int(pattern: str, text: str) -> int | None:
    match = re.search(pattern, text, re.IGNORECASE)
    return int(match.group(1)) if match else None


def body_of(rel: str) -> str:
    """The command body with its frontmatter removed, so a cross-read never
    matches the very declaration it is meant to be checking."""
    text = read(rel)
    parts = text.split("\n")
    if parts and parts[0].strip() == "---":
        for index in range(1, len(parts)):
            if parts[index].strip() == "---":
                return "\n".join(parts[index + 1:])
    return text


# --------------------------------------------------------------------------
# Scenarios
# --------------------------------------------------------------------------


def load_command(name: str) -> tuple[object, str | None, bool]:
    """Return (loop node or None, error, phase-state integrated)."""
    rel = f"commands/{name}.md"
    path = ROOT / rel
    if not path.is_file():
        return None, f"{rel} does not exist", False
    text = path.read_text(encoding="utf-8")
    parsed, err = frontmatter(text)
    if err:
        return None, f"{rel}: {err}", False
    integrated = "phase-execution" in text
    return parsed.get("loop", "__absent__"), None, integrated


def scenario_shipped_commands() -> None:
    """Assertions 1-6 against the five shipped command files."""
    for name in LOOP_BEARING_COMMANDS:
        loop, err, integrated = load_command(name)
        if err:
            emit(f"schema-{name}", False, err)
            continue
        if loop == "__absent__":
            emit_skip(f"schema-{name}",
                      f"commands/{name}.md declares no loop: block - deferred_to_check3 "
                      "(2026-08-11-governor-instrumentation Check 3 owns presence)")
            continue
        errors = validate_loop(f"commands/{name}.md", loop, integrated)
        emit(f"schema-{name}", not errors, "; ".join(errors))


def scenario_historical_regression() -> None:
    """Assertion 7. Skips - loudly - when .writ/state/ has no runs to compare."""
    state_dir = ROOT / ".writ" / "state"
    maxima, notes = recorded_maxima(state_dir)
    if notes:
        emit_skip("historical-run-shapes",
                  "state files skipped rather than failed: " + "; ".join(notes))
    if not maxima:
        emit_skip("historical-run-regression",
                  ".writ/state/ holds no readable run records (it is gitignored, so this "
                  "is expected in CI and on a fresh clone). The bounds were NOT compared "
                  "against recorded history in this run - re-run on a working copy that "
                  "has the run files")
        return

    findings: list[str] = []
    for name in LOOP_BEARING_COMMANDS:
        loop, err, _ = load_command(name)
        if err or loop == "__absent__" or not isinstance(loop, dict):
            continue
        findings += regression_findings(declared_bounds(loop), maxima, f"commands/{name}.md")
    observed = ", ".join(f"{unit}={value}" for unit, value in sorted(maxima.items()))
    emit("historical-run-regression", not findings,
         "; ".join(findings) or f"observed maxima: {observed}")


def scenario_transcription_drift() -> None:
    """Assertion 8. Every expected value is read from its source, not hardcoded."""
    # implement-phase nested spec_attempt <- scripts/phase-state.py's own guard
    guard = first_int(r"attempts\s*<\s*(\d+)", read("scripts/phase-state.py"))
    loop, err, _ = load_command("implement-phase")
    declared = declared_bounds(loop) if not err and isinstance(loop, dict) else {}
    if guard is None:
        emit_skip("drift-spec-attempt",
                  "scripts/phase-state.py exposes no `attempts < N` guard to cross-read")
    elif "spec_attempt" not in declared:
        emit_skip("drift-spec-attempt",
                  "implement-phase declares no spec_attempt unit - deferred_to_check3")
    else:
        emit("drift-spec-attempt", declared["spec_attempt"] == guard,
             f"implement-phase bounds spec_attempt at {declared['spec_attempt']}, but "
             f"scripts/phase-state.py enforces `attempts < {guard}`. The declaration "
             "transcribes the code; it may not diverge from it")

    # implement-story's three numbers <- its own prose caps and the agent definitions
    story_body = body_of("commands/implement-story.md")
    loop, err, _ = load_command("implement-story")
    declared = declared_bounds(loop) if not err and isinstance(loop, dict) else {}
    sources = {
        "review_cycle": (
            first_int(r"Max (\d+) iterations across review", story_body),
            "commands/implement-story.md's 'Max N iterations across review and visual QA gates'"),
        "testing_cycle": (
            first_int(r"(\d+) fix iterations max", story_body),
            "commands/implement-story.md's 'N fix iterations max' at Gate 4"),
    }
    coding = first_int(r"MAX_SELF_FIX_ITERATIONS\s*=\s*(\d+)", read("agents/coding-agent.md"))
    testing = first_int(r"MAX_SELF_FIX_ITERATIONS\s*=\s*(\d+)", read("agents/testing-agent.md"))
    if coding is not None and coding == testing:
        sources["agent_self_fix"] = (
            coding, "MAX_SELF_FIX_ITERATIONS in agents/coding-agent.md and agents/testing-agent.md")
    else:
        emit("drift-agent-parity", False,
             f"MAX_SELF_FIX_ITERATIONS disagrees across the agent definitions: "
             f"coding-agent={coding}, testing-agent={testing}")

    for unit, (source_value, origin) in sources.items():
        if source_value is None:
            emit_skip(f"drift-{unit.replace('_', '-')}",
                      f"no source value to cross-read from {origin}")
        elif unit not in declared:
            emit_skip(f"drift-{unit.replace('_', '-')}",
                      f"implement-story declares no {unit} unit - deferred_to_check3")
        else:
            emit(f"drift-{unit.replace('_', '-')}", declared[unit] == source_value,
                 f"implement-story bounds {unit} at {declared[unit]}, but {origin} says "
                 f"{source_value}. These are the same number in two places and must agree")

    # refactor's weak evidence may not be quietly upgraded
    loop, err, _ = load_command("refactor")
    if err or not isinstance(loop, dict):
        emit_skip("refactor-no-recorded-run-literal", err or "refactor declares no loop: block")
    else:
        citation = str(loop.get("calibrated_against") or "")
        emit("refactor-no-recorded-run-literal", NO_RECORDED_RUN in citation.lower(),
             f"commands/refactor.md's calibrated_against must contain the literal "
             f"'{NO_RECORDED_RUN}'. /refactor has zero recorded executions; replacing that "
             "admission with a confident-looking citation requires an explicit edit, not a drift")

    # verify-spec's bound of 1 is only true while the command stays single-pass.
    # The guard reads STRUCTURE (headings and numbered steps), not prose - the
    # bound's own citation says the words "re-check" and "re-run" while asserting
    # their absence, and prose describing an absence must not trip the guard.
    verify_body = body_of("commands/verify-spec.md")
    structural = [line.strip() for line in verify_body.split("\n")
                  if re.match(r"^\s*(#{2,4} |\d+\.\d* )", line)]
    offenders = [line for line in structural
                 if re.search(r"re-?(check|verify|run)", line, re.IGNORECASE)]
    emit("verify-spec-no-recheck-step", not offenders,
         f"commands/verify-spec.md gained a re-check step ({offenders}). Its bound of 1 "
         "auto-fix pass is justified only by the command being single-pass by "
         "construction - re-derive the bound")


def scenario_governor_boundary() -> None:
    """The presence/correctness split with 2026-08-11-governor-instrumentation.

    If that spec's Check 3 has not landed, presence is simply unchecked. This
    check must NOT fill the gap, and must not assert a `structural` finding
    classification that does not exist yet - it degrades to a reported skip.
    """
    landed = "check_loop_bounds" in read("scripts/eval-leanness.py")
    if landed:
        emit("governor-boundary-intact", True)
    else:
        emit_skip("governor-boundary-intact",
                  "2026-08-11-governor-instrumentation Check 3 has not landed, so loop-bound "
                  "PRESENCE is currently unchecked. This check deliberately does not fill "
                  "that gap (duplicate findings are worse than a stated one) and asserts no "
                  "blocking `structural` classification, which that spec also owns")


# --------------------------------------------------------------------------
# Fixture scenarios - the Story 1 fixture set, one-for-one
# --------------------------------------------------------------------------

FIXTURE_BASE = """unit: "story"
max_iterations: 4
on_exhaustion: escalate
calibrated_against: "commands/x.md - evidence: strong."
"""


def fixture(block: str, command: str = "fixture.md",
            integrated: bool = False) -> list[str]:
    text = "---\nname: fixture\n" + block + "---\n\nbody\n"
    parsed, err = frontmatter(text)
    if err:
        return [err]
    loop = parsed.get("loop", "__absent__")
    if loop == "__absent__":
        return ["__absent__"]
    return validate_loop(command, loop, integrated)


def indent(block: str, spaces: int = 2) -> str:
    return "".join(" " * spaces + line + "\n" for line in block.strip().split("\n"))


def scenario_fixtures() -> None:
    def check(name: str, errors: list[str], want_reject: bool, needle: str = "") -> None:
        if want_reject:
            emit(f"fixture-{name}", bool(errors) and needle.lower() in " ".join(errors).lower(),
                 f"expected a rejection mentioning {needle!r}, got: {errors}")
        else:
            emit(f"fixture-{name}", not errors, f"expected acceptance, got: {errors}")

    check("valid-minimal", fixture("loop:\n" + indent(FIXTURE_BASE)), False)

    check("valid-nested", fixture(
        "loop:\n" + indent(FIXTURE_BASE) +
        '  nested:\n    - unit: "sub_cycle"\n      max_iterations: 2\n'
        '      on_exhaustion: escalate\n      calibrated_against: "agents/x.md - strong."\n'),
        False)

    errors = fixture("")
    emit("fixture-no-loop-block", errors == ["__absent__"],
         f"a file with no loop: block must be skipped as deferred_to_check3, not "
         f"validated; got: {errors}")

    for key in REQUIRED_KEYS:
        block = "".join(line + "\n" for line in FIXTURE_BASE.strip().split("\n")
                        if not line.startswith(key + ":"))
        check(f"missing-{key.replace('_', '-')}", fixture("loop:\n" + indent(block)),
              True, key)

    # The retry rejection must name the value AND give the reason (Business Rule 4),
    # so this fixture asserts both halves of the message.
    retry_errors = fixture("loop:\n" + indent(FIXTURE_BASE.replace("escalate", "retry")))
    joined = " ".join(retry_errors)
    emit("fixture-on-exhaustion-retry",
         "'retry' is illegal" in joined and "PRE-exhaustion" in joined
         and "attempts < 2" in joined,
         f"rejecting retry must name the value and give the reason - that retry is a "
         f"pre-exhaustion state governed by phase-state.py's `attempts < 2` guard; "
         f"got: {retry_errors}")
    check("on-exhaustion-out-of-set",
          fixture("loop:\n" + indent(FIXTURE_BASE.replace("escalate", "continue_anyway"))),
          True, "continue_anyway")
    check("max-iterations-string",
          fixture("loop:\n" + indent(FIXTURE_BASE.replace("max_iterations: 4",
                                                          'max_iterations: "four"'))),
          True, "positive integer literal")
    check("max-iterations-range",
          fixture("loop:\n" + indent(FIXTURE_BASE.replace("max_iterations: 4",
                                                          "max_iterations: 3-5"))),
          True, "positive integer literal")
    check("max-iterations-zero",
          fixture("loop:\n" + indent(FIXTURE_BASE.replace("max_iterations: 4",
                                                          "max_iterations: 0"))),
          True, "must be positive")

    check("duplicate-unit", fixture(
        "loop:\n" + indent(FIXTURE_BASE) +
        '  nested:\n    - unit: "story"\n      max_iterations: 2\n'
        '      on_exhaustion: escalate\n      calibrated_against: "agents/x.md - strong."\n'),
        True, "more than once")

    check("nested-in-nested", fixture(
        "loop:\n" + indent(FIXTURE_BASE) +
        '  nested:\n    - unit: "sub_cycle"\n      max_iterations: 2\n'
        '      on_exhaustion: escalate\n      calibrated_against: "agents/x.md - strong."\n'
        '      nested:\n        - unit: "deep"\n          max_iterations: 1\n'
        '          on_exhaustion: escalate\n          calibrated_against: "agents/x.md - s."\n'),
        True, "one level")

    check("loop-not-a-mapping", fixture("loop: 12\n"), True, "must be a mapping")

    check("nested-missing-key", fixture(
        "loop:\n" + indent(FIXTURE_BASE) +
        '  nested:\n    - unit: "sub_cycle"\n      max_iterations: 2\n'
        "      on_exhaustion: escalate\n"),
        True, "calibrated_against")

    check("citation-no-path",
          fixture("loop:\n" + indent(FIXTURE_BASE.replace(
              'calibrated_against: "commands/x.md - evidence: strong."',
              'calibrated_against: "seemed about right"'))),
          True, "no path")

    check("quarantine-without-phase-state",
          fixture("loop:\n" + indent(FIXTURE_BASE.replace("escalate", "quarantine")),
                  integrated=False),
          True, "no phase-execution")
    check("quarantine-with-phase-state",
          fixture("loop:\n" + indent(FIXTURE_BASE.replace("escalate", "quarantine")),
                  integrated=True),
          False)

    # A `loop:` block validates identically with and without the ADR-020 keys,
    # so the two specs may land in either order.
    with_adr020 = fixture('problem: "p"\noutcome: "o"\nexit_criteria:\n  - "e"\n'
                          "loop:\n" + indent(FIXTURE_BASE))
    emit("fixture-no-adr020-keys",
         not fixture("loop:\n" + indent(FIXTURE_BASE)) and not with_adr020,
         "loop: must validate identically whether the component-contract keys are "
         f"present or absent; got {with_adr020}")


def scenario_history_fixtures() -> None:
    """Assertion 7's own fixtures: a bound below history fails; an empty state
    directory skips with a reason rather than passing silently."""
    import tempfile

    with tempfile.TemporaryDirectory() as tmp:
        state = Path(tmp)
        (state / "execution-fixture.json").write_text(json.dumps(
            {"stories": {f"story-{n}": {} for n in range(1, 5)}}), encoding="utf-8")
        (state / "phase-execution-fixture.json").write_text(json.dumps(
            {"specOrder": ["a", "b", "c", "d", "e", "f"]}), encoding="utf-8")
        maxima, notes = recorded_maxima(state)
        emit("history-fixture-reads-runs", maxima == {"story": 4, "spec": 6},
             f"expected story=4 and spec=6 from the fixture runs, got {maxima} ({notes})")

        low = regression_findings({"story": 2}, maxima, "commands/fixture.md")
        emit("history-fixture-rejects-low-bound",
             len(low) == 1 and "already reached 4" in low[0],
             f"a bound of 2 against a recorded 4-story run must fail naming the value; got {low}")

        ok = regression_findings({"story": 12, "spec": 12}, maxima, "commands/fixture.md")
        emit("history-fixture-accepts-shipped-bounds", not ok,
             f"the shipped bounds must clear the fixture history; got {ok}")

    with tempfile.TemporaryDirectory() as tmp:
        maxima, notes = recorded_maxima(Path(tmp))
        emit("history-fixture-empty-state-skips", maxima == {} and notes == [],
             f"an empty state dir must yield no maxima and no findings; got {maxima} / {notes}")

    with tempfile.TemporaryDirectory() as tmp:
        state = Path(tmp)
        (state / "execution-broken.json").write_text("{not json", encoding="utf-8")
        maxima, notes = recorded_maxima(state)
        emit("history-fixture-malformed-skips", maxima == {} and len(notes) == 1,
             f"a malformed state file must be noted and skipped, never a finding; "
             f"got {maxima} / {notes}")


def main() -> int:
    scenario_shipped_commands()
    scenario_historical_regression()
    scenario_transcription_drift()
    scenario_governor_boundary()
    scenario_fixtures()
    scenario_history_fixtures()
    return 0 if failed == 0 else 1


if __name__ == "__main__":
    sys.exit(main())
