#!/usr/bin/env python3
"""Per-invocation load measurement for Writ commands.

Phase 10's token success criterion reads *"`per_surface.commands.chars` drops
materially from 516,589 — **measured per-invocation load, not just file
size**"*. Nothing measured that. `eval-leanness.py` weighs the whole
`commands/` directory, which is the right instrument for surface drift and
the wrong one for the question progressive disclosure actually asks.

An invocation does not load `commands/`. It loads:

    system-instructions.md      the root behavioral contract
  + commands/_preamble.md       standing instructions
  + commands/<name>.md          the one command being run
  + skills/<n>/SKILL.md ...     only those in its `required_skills:`

The first two are a **shared base** paid by every invocation, and progressive
disclosure cannot reduce them — it only moves bytes out of the third into the
fourth. Reporting that split is the point of this script, because it bounds
what the exercise can achieve before six specs are written against it.

Two numbers per command, and the distinction is the whole design:

  floor    = base + command file            always paid
  ceiling  = floor + every declared skill   paid when a run needs them all

[ADR-021](../.writ/decision-records/adr-021-progressive-disclosure-token-budget.md)
caveat 2 warns that disclosure can *raise* total load: a command that ends up
pulling every skill costs more than the monolith did. `floor` is the number
that should fall; `ceiling` is the number that can rise. A report showing only
one of them cannot tell you whether disclosure worked.

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
        resolved: list[str] = []
        unresolved: list[str] = []
        conditional_bytes = 0
        for name in _L.parse_skill_names(fields.get("required_skills", "")):
            skill_path = os.path.join(root, "skills", name, "SKILL.md")
            if os.path.isfile(skill_path):
                resolved.append(name)
                conditional_bytes += _read_bytes(skill_path)
            else:
                unresolved.append(name)

        if unresolved:
            warnings.append(
                f"commands/{stem}.md declares required_skills that resolve to no "
                f"file: {', '.join(unresolved)}. Their load is unmeasurable, so "
                f"the ceiling below is a lower bound.")

        floor_bytes = base_bytes + command_bytes
        ceiling_bytes = floor_bytes + conditional_bytes

        commands[stem] = {
            "command_bytes": command_bytes,
            "command_lines": command_lines,
            "base_bytes": base_bytes,
            "floor_bytes": floor_bytes,
            "conditional_bytes": conditional_bytes,
            "ceiling_bytes": ceiling_bytes,
            "resolved_skills": resolved,
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
