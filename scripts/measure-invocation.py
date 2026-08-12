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

Bytes here are a **measurement**. Tokens are an **estimate** unless a real
tokenizer is importable, and the output always says which it did via
`token_method` and `token_method_validated`.

The roadmap's `chars/4` was never validated against a tokenizer — it is an
assumption that has been quoted as though it were measured (`~129k tokens`).
This script does not repeat that. It records the divisor it used, marks the
estimate unvalidated, and accepts `--chars-per-token` so the ratio can be
calibrated the first time a tokenizer is available. Writ ships zero
third-party dependencies, so none is imported; `tiktoken` is used only if it
already happens to be installed.

This is the same labeling discipline ADR-019 imposes on
`story_context_bytes`: a proxy may be reported, but never under a name that
reads like a measurement.

Usage:
  measure-invocation.py [--root .] [--command NAME] [--chars-per-token 4.0]
                        [--format json|table]

Always exits 0 — a read-only measurement never blocks its caller.
"""

from __future__ import annotations

import argparse
import importlib.util
import json
import os
import re
import statistics
import sys

HERE = os.path.dirname(os.path.abspath(__file__))

# The roadmap's inherited ratio. Named, not buried, precisely because it is an
# assumption rather than a finding — see the module docstring.
DEFAULT_CHARS_PER_TOKEN = 4.0

TOKEN_NOTE = (
    "Bytes are measured. Tokens are NOT measured: no tokenizer was available, "
    "so token figures are an estimate at the recorded chars_per_token ratio. "
    "The chars/4 ratio inherited from .writ/product/roadmap.md has never been "
    "validated against a real tokenizer — treat every *_tokens_estimated "
    "value as an order-of-magnitude figure, and recalibrate --chars-per-token "
    "the first time a tokenizer is available."
)

TOKEN_NOTE_TOKENIZER = (
    "Bytes are measured and tokens were counted with a real tokenizer "
    "({encoding}). These are not an estimate; chars_per_token is reported as "
    "the observed ratio for this corpus, which is the figure the roadmap's "
    "unvalidated chars/4 assumption should be replaced with."
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


def measure(root: str, chars_per_token: float = DEFAULT_CHARS_PER_TOKEN,
            command: str | None = None) -> dict:
    """The whole report. Never raises on a missing or malformed tree."""
    warnings: list[str] = []

    encoder = _tokenizer()
    if encoder is not None:
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

    # --- the shared base: paid by every invocation, immune to disclosure ---
    base_components: dict[str, int] = {}
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

        fields = _L.read_frontmatter(path) or {}
        declared = _L.parse_skill_names(fields.get("required_skills", ""))
        inlined, hoisted = _inline_read_skills(path)

        eager_skills: list[str] = []
        conditional_skills: list[str] = []
        unresolved: list[str] = []
        eager_bytes = 0
        conditional_bytes = 0

        # Declared wins over inlined: `required_skills:` already paid for it
        # before phase 1, so an inline Read of the same skill costs nothing
        # extra. Counting both would double-charge.
        for name in declared:
            skill_path = os.path.join(root, "skills", name, "SKILL.md")
            if os.path.isfile(skill_path):
                eager_skills.append(name)
                eager_bytes += _read_bytes(skill_path)
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
            "floor_tokens_estimated": to_tokens(floor_bytes),
            "ceiling_tokens_estimated": to_tokens(ceiling_bytes),
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
        "irreducible_base_tokens_estimated": to_tokens(base_bytes),
        "min_floor_bytes": min(floors) if floors else 0,
        "median_floor_bytes": int(statistics.median(floors)) if floors else 0,
        "max_floor_bytes": max(floors) if floors else 0,
        "max_floor_command": (max(commands, key=lambda k: commands[k]["floor_bytes"])
                              if commands else None),
        "mean_bytes_per_command_line": (round(total_command_bytes / total_command_lines, 2)
                                        if total_command_lines else 0),
    }

    return {
        "schema": "invocation-load-v1",
        "root": os.path.abspath(root),
        "token_method": token_method,
        "token_method_validated": validated,
        "chars_per_token": chars_per_token,
        "token_note": token_note,
        "ceiling_note": CEILING_NOTE,
        "base": {"bytes": base_bytes, "components": base_components},
        "commands": commands,
        "corpus": corpus,
        "warnings": warnings,
    }


def render_table(report: dict) -> str:
    rows = sorted(report["commands"].items(),
                  key=lambda kv: kv[1]["floor_bytes"], reverse=True)
    out = [
        f"Per-invocation load — {report['root']}",
        f"token method: {report['token_method']}  "
        f"(validated: {report['token_method_validated']})",
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
    args = parser.parse_args()

    report = measure(args.root, chars_per_token=args.chars_per_token,
                     command=args.command)
    if args.format == "table":
        print(render_table(report))
    else:
        print(json.dumps(report, indent=2))
    return 0


if __name__ == "__main__":
    sys.exit(main())
