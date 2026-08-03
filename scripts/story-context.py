#!/usr/bin/env python3
"""Deterministic context-hint assembler — the executable reference for the
`## Context for Agents` contract documented in `.writ/docs/context-hint-format.md`
and currently *run* by LLM judgment at `commands/implement-story.md` lines
75-123. This script becomes the single implementation; Story 4 points the
prose at it and deletes the parsing steps (not this story's job).

Subcommand:
  assemble --story PATH [--budget-bytes N]
             Parse one story file's `## Context for Agents` section, resolve
             every bracketed and extended reference against the story's spec
             folder, and emit a bounded JSON payload.

Always exits 0, even when the story file is missing, the hints section is
absent, or a source spec cannot be read — thin/absent context degrades the
payload rather than halting the caller. This is the deliberate asymmetry
documented in `sub-specs/technical-spec.md`: the sibling `story-deps.py`
blocks on an invalid graph; this script never blocks on absent context.

`--budget-bytes` is optional and, when supplied, enforced (Story 3):
resolved content strictly exceeding it is truncated by relevance order
(`FETCHED_CONTEXT_BUDGET_BYTES` below documents the derivation), `truncated`
becomes `true`, and a warning names actual and budget bytes. Omitting the
flag (`budget_bytes=None`) remains unbounded — Story 4, not this script,
decides whether/when a caller passes the derived constant.

```json
{
  "fetched_context": { "error_map_rows": "...", "business_rules": "..." },
  "warnings": ["Context hint references missing content: \"...\" in ..."],
  "bytes": { "error_map_rows": 812, "business_rules": 431, "total": 1243 },
  "truncated": false
}
```
"""

from __future__ import annotations

import argparse
import json
import re
import sys
from pathlib import Path
from typing import Any

# Display name (as it appears in the story's "- **{Category}:**" line) ->
# the JSON payload key. Order is the canonical, deterministic output order —
# independent of the order categories appear in the story file, so repeated
# runs are byte-identical regardless of authoring order.
#
# Story 3 (Architecture Check Finding 4): this same sequence ALSO doubles as
# truncation priority when a budget is enforced — earlier entries are
# higher-relevance and retained first. Nothing in spec.md or technical-spec.md
# states that the output order and the truncation order must match; reusing
# CATEGORY_ORDER for both is a deliberate implementation choice (error map
# rows and shadow paths, which name concrete failure/flow rows, outrank the
# more general business-rules/experience prose when budget is tight), not
# something the spec mandates. See `enforce_budget()`.
CATEGORIES: dict[str, str] = {
    "Error map rows": "error_map_rows",
    "Shadow paths": "shadow_paths",
    "Business rules": "business_rules",
    "Experience": "experience",
}
CATEGORY_ORDER: list[str] = list(CATEGORIES)

# --- Story 3: derived fetched_context budget --------------------------------
# Measured, not invented (Business Rule 4). Derivation, reproducible via
# `python3 scripts/sweep-story-context-bytes.py`:
#
#   Swept every user-stories/story-*.md under .writ/specs/ (170 stories,
#   2026-08-03): bytes.total distribution was min=0, median=0 (most stories
#   carry no hints at all), p95≈2205, p99≈3619, max=10251 (one real,
#   unaffected outlier: 2026-07-10-recommended-autonomous-delivery story-3).
#
#   Heuristic: FETCHED_CONTEXT_BUDGET_BYTES = 2 x observed max, rounded up to
#   the nearest 1000 bytes. 2x (not 1x, not p99) is a deliberate margin for
#   the known Finding-2 undercount below — a straight round-up of the
#   observed max would sit right on top of legitimate normal-work content
#   (theater risk: the cap should catch pathology, not today's biggest real
#   story), and the corpus's true high end is unmeasured, not merely
#   underestimated at the margin.
#
#   Finding-2 caveat (do not silently ignore): `extract_markdown_section()`
#   requires an exact heading match, so any spec.md whose
#   "## \U0001F3AF Experience Design" heading carries trailing text (e.g. a
#   parenthetical) undercounts error_map_rows/shadow_paths (via the
#   technical-spec-absent fallback) and experience itself. 9 of the 170
#   swept stories were flagged by this sweep's heading-mismatch heuristic —
#   including this very spec's own story-1 through story-4 — and undercount
#   is invisible in the measurement (a missing section reads as "0 bytes for
#   that category", not as an error). The 2x margin exists specifically so
#   fixing that bug later doesn't retroactively invalidate this constant;
#   re-run scripts/sweep-story-context-bytes.py once it's fixed to confirm.
FETCHED_CONTEXT_BUDGET_BYTES = 21000

# Canonical arrow for extended references. `>>`/`>` leniency lived only in
# the eval-leanness.py regex being replaced (an implementation accident, not
# a documented contract) — see Architecture Check Finding 3. Not supported.
ARROW = "\u2192"  # →

CATEGORY_LINE = re.compile(r"^-\s*\*\*([^:*]+):\*\*\s*(.*)$")
BRACKET = re.compile(r"\[(.*?)\]")
# A single backtick span containing both ".md" and the canonical arrow is an
# extended reference, e.g. `file.md → ## Section → ### Subsection`. Backtick
# spans that merely happen to contain a word in backticks (e.g. an Operation
# name like `` `eval-leanness` calls assembler ``) never match: no ".md",
# no arrow.
EXTENDED_REF = re.compile(r"`([^`]*\.md[^`]*" + ARROW + r"[^`]*)`")
NUMBERED_ITEM = re.compile(r"^\d+\.\s+")
NUMBERED_ITEM_BOLD = re.compile(r"^\d+\.\s+\*\*(.+?)\*\*\.?\s*")


def extract_markdown_section(text: str, heading_line: str) -> str | None:
    """Return the section body (heading through the next heading of equal or
    higher level, or EOF) for the FIRST line matching `heading_line` exactly
    (after stripping). None if not found.

    Exact-match-after-strip mirrors eval-leanness.py's `extract_markdown_section`
    deliberately (Architecture Check Finding 2 / notes): Unicode headers like
    `## 🎯 Experience Design` already resolve correctly under plain string
    equality, and a regex reimplementation risks mishandling the emoji.
    """
    target = heading_line.strip()
    level = len(target) - len(target.lstrip("#"))
    if level == 0:
        return None
    lines = text.splitlines(keepends=True)
    start = next((i for i, line in enumerate(lines) if line.strip() == target), None)
    if start is None:
        return None
    end = len(lines)
    for j in range(start + 1, len(lines)):
        stripped = lines[j].rstrip("\n")
        if stripped.startswith("#") and (len(stripped) - len(stripped.lstrip("#"))) <= level:
            end = j
            break
    return "".join(lines[start:end])


def resolve_spec_file(spec_folder: Path, filename: str) -> Path | None:
    """Resolve `filename` against `spec_folder` (directly, then under
    `sub-specs/`), rejecting any candidate that escapes `spec_folder` —
    via `../` relative traversal or an absolute `filename` that would
    otherwise make `Path.__truediv__` discard `spec_folder` entirely.
    An out-of-bounds candidate is treated identically to a missing one
    (None) so callers can't distinguish "rejected" from "not found".
    """
    base = spec_folder.resolve()
    for candidate in (spec_folder / filename, spec_folder / "sub-specs" / filename):
        resolved = candidate.resolve()
        if not resolved.is_relative_to(base):
            continue
        if resolved.is_file():
            return resolved
    return None


def parse_table(section_text: str) -> tuple[str | None, str | None, list[str]]:
    """First markdown table in `section_text` -> (header, separator, data_rows).

    (None, None, []) when no table is present. Only the first contiguous run
    of `|`-prefixed lines is treated as the table — trailing prose after the
    table (present in the real Error & Rescue Map section) naturally ends
    the scan.
    """
    lines = section_text.splitlines()
    pipe_indexes = [i for i, line in enumerate(lines) if line.strip().startswith("|")]
    if not pipe_indexes:
        return None, None, []
    start = pipe_indexes[0]
    rows: list[str] = []
    i = start
    while i < len(lines) and lines[i].strip().startswith("|"):
        rows.append(lines[i])
        i += 1
    if len(rows) < 2:
        return None, None, []
    return rows[0], rows[1], rows[2:]


def row_first_cell(row: str) -> str:
    """First column's text, backticks and all — Finding 2: row-matching is an
    exact match on the raw cell text, never backtick-stripped."""
    inner = row.strip()
    if inner.startswith("|"):
        inner = inner[1:]
    if inner.endswith("|"):
        inner = inner[:-1]
    cells = inner.split("|")
    return cells[0].strip() if cells else ""


def resolve_extended_ref(spec_folder: Path, ref: str) -> str | None:
    """`file.md → ## Section → ### Subsection` -> resolved section text, or
    None if the file or any heading in the chain doesn't resolve."""
    parts = [p.strip() for p in ref.split(ARROW) if p.strip()]
    if len(parts) < 2:
        return None
    path = resolve_spec_file(spec_folder, parts[0])
    if path is None:
        return None
    try:
        text = path.read_text(encoding="utf-8")
    except OSError:
        return None
    for heading in parts[1:]:
        extracted = extract_markdown_section(text, heading)
        if extracted is None:
            return None
        text = extracted
    return text


def parse_numbered_items(section_text: str) -> list[tuple[str | None, str]]:
    """Numbered list items (`N. **Bold**. rest...`) -> [(bold_phrase, full_item_text)].

    An item's text runs from its `N.` line through the line before the next
    `N.` item, a blank line, or a heading — single-line items (the form every
    existing Business Rules list uses) are the common case, but multi-line
    items are captured too rather than silently truncated.
    """
    items: list[list[str]] = []
    current: list[str] | None = None
    for line in section_text.splitlines():
        stripped = line.strip()
        if NUMBERED_ITEM.match(stripped):
            if current is not None:
                items.append(current)
            current = [line.rstrip("\n")]
        elif current is not None and stripped and not stripped.startswith("#"):
            current.append(line.rstrip("\n"))
        elif current is not None:
            items.append(current)
            current = None
    if current is not None:
        items.append(current)

    result: list[tuple[str | None, str]] = []
    for block in items:
        bold_match = NUMBERED_ITEM_BOLD.match(block[0].strip())
        name = bold_match.group(1).strip() if bold_match else None
        result.append((name, "\n".join(block)))
    return result


def _missing(warnings: list[str], ref: str, source: str) -> None:
    warnings.append(f'\u26a0\ufe0f Context hint references missing content: "{ref}" in {source}')


def resolve_table_category(
    refs: list[str],
    tech_text: str | None,
    table_heading: str,
    spec_text: str,
    fallback_subheading: str,
    warnings: list[str],
) -> str:
    """Error map rows / Shadow paths: `technical-spec.md` table rows by exact
    Operation/Flow name (Finding 1: a name matching multiple rows concatenates
    ALL matches, table order, deduplicated — no warning; that is a real
    multi-cause signal, not an error). Falls through to the whole documented
    `spec.md` Experience Design fallback subsection when `technical-spec.md`
    itself is absent/unreadable (silent — a per-reference table lookup makes
    no sense against a subsection with no row structure).
    """
    if tech_text is not None:
        section = extract_markdown_section(tech_text, table_heading)
        header, separator, rows = parse_table(section) if section is not None else (None, None, [])
        if header is None:
            for ref in refs:
                _missing(warnings, ref, "technical-spec.md")
            return ""
        matched: list[str] = []
        for ref in refs:
            hits = [row for row in rows if row_first_cell(row) == ref]
            if not hits:
                _missing(warnings, ref, "technical-spec.md")
                continue
            for row in hits:
                if row not in matched:
                    matched.append(row)
        if not matched:
            return ""
        return "\n".join([header, separator] + matched)

    experience = extract_markdown_section(spec_text, "## \U0001F3AF Experience Design")
    fallback = extract_markdown_section(experience, fallback_subheading) if experience is not None else None
    if fallback is None:
        for ref in refs:
            _missing(warnings, ref, "spec.md (Experience Design fallback)")
        return ""
    return fallback.strip()


def resolve_business_rules(refs: list[str], spec_text: str, warnings: list[str]) -> str:
    """Business rules category: match each ref against spec.md's numbered
    Business Rules list by bold-phrase name (trailing period normalized on
    both sides, since bracket hints omit it and spec.md doesn't). Warns per
    unmatched ref, or per ref if the section itself is absent; matched item
    bodies are deduplicated and joined with a blank line between them."""
    section = extract_markdown_section(spec_text, "## \U0001F4CB Business Rules")
    if section is None:
        for ref in refs:
            _missing(warnings, ref, "spec.md")
        return ""
    items = parse_numbered_items(section)
    matched: list[str] = []
    for ref in refs:
        # Bracket hints omit the source's trailing period ("One implementation
        # per contract" vs. spec.md's "One implementation per contract.") —
        # normalize on that one point only; otherwise exact, case-sensitive.
        norm_ref = ref.strip().rstrip(".")
        hit = next(
            (text for name, text in items if name is not None and name.strip().rstrip(".") == norm_ref),
            None,
        )
        if hit is None:
            _missing(warnings, ref, "spec.md")
        elif hit not in matched:
            matched.append(hit)
    return "\n\n".join(matched)


def resolve_experience(refs: list[str], spec_text: str, warnings: list[str]) -> str:
    """Experience category: match each ref against spec.md's `## 🎯
    Experience Design` section by exact `### {ref}` subsection name. Warns
    per unmatched ref, or per ref if the parent section itself is absent;
    matched subsections are deduplicated and joined with a blank line
    between them."""
    section = extract_markdown_section(spec_text, "## \U0001F3AF Experience Design")
    if section is None:
        for ref in refs:
            _missing(warnings, ref, "spec.md")
        return ""
    matched: list[str] = []
    for ref in refs:
        sub = extract_markdown_section(section, f"### {ref}")
        if sub is None:
            _missing(warnings, ref, "spec.md")
        elif sub.strip() not in matched:
            matched.append(sub.strip())
    return "\n\n".join(matched)


def resolve_bracket_refs(
    label: str, refs: list[str], spec_text: str, tech_text: str | None, warnings: list[str]
) -> str:
    """Dispatch a bracket-form category's refs to its category-specific
    resolver, by display-name label. Callers (`resolve_category`, via
    `parse_hint_lines`) only ever pass a label already narrowed to
    `CATEGORIES`, so the trailing `return ""` case below is unreachable."""
    if label == "Error map rows":
        return resolve_table_category(
            refs, tech_text, "## Error & Rescue Map", spec_text, "### Error Experience", warnings
        )
    if label == "Shadow paths":
        return resolve_table_category(
            refs, tech_text, "## Shadow Paths", spec_text, "### Happy Path", warnings
        )
    if label == "Business rules":
        return resolve_business_rules(refs, spec_text, warnings)
    if label == "Experience":
        return resolve_experience(refs, spec_text, warnings)
    return ""  # unreachable: caller only dispatches recognized labels


def parse_category_value(rest: str) -> tuple[str, list[str]] | None:
    """One category line's value -> (kind, refs).

    kind is "extended" (backtick-delimited `file.md → ## Section` spans),
    "bracket" (`[item 1, item 2]`), or "empty" (`[]` — a valid signal, never
    an error). None means unparseable (no recognizable form at all, or an
    opening `[` with no matching `]`) — the caller skips and warns once.
    """
    extended = EXTENDED_REF.findall(rest)
    if extended:
        return "extended", [ref.strip() for ref in extended]
    if "[" in rest:
        match = BRACKET.search(rest)
        if not match:
            return None
        inner = match.group(1).strip()
        if inner == "":
            return "empty", []
        return "bracket", [item.strip() for item in inner.split(",")]
    return None


def parse_hint_lines(section_text: str) -> tuple[dict[str, dict[str, list[str]]], list[str]]:
    """`## Context for Agents` section body -> (category_data, warnings).

    category_data maps display name -> {"bracket_refs": [...], "extended_refs": [...]},
    already merged and deduplicated across every line for that category
    (Interaction Edge Case: duplicate category lines merge and warn once —
    not once per repeated line).
    """
    category_data: dict[str, dict[str, list[str]]] = {}
    seen: set[str] = set()
    duplicate_warned: set[str] = set()
    warnings: list[str] = []

    for raw_line in section_text.splitlines():
        match = CATEGORY_LINE.match(raw_line.strip())
        if not match:
            continue
        label = match.group(1).strip()
        rest = match.group(2)

        if label not in CATEGORIES:
            warnings.append(f'\u26a0\ufe0f Unrecognized context hint category: "{label}"')
            continue

        parsed = parse_category_value(rest)
        entry = category_data.setdefault(label, {"bracket_refs": [], "extended_refs": []})
        if parsed is None:
            warnings.append(
                f'\u26a0\ufe0f Malformed context hint category: "{label}" '
                "(unclosed bracket or unrecognized reference form)"
            )
        elif parsed[0] != "empty":
            kind, refs = parsed
            bucket = entry["bracket_refs"] if kind == "bracket" else entry["extended_refs"]
            for ref in refs:
                if ref not in bucket:
                    bucket.append(ref)

        if label in seen and label not in duplicate_warned:
            warnings.append(f'\u26a0\ufe0f Duplicate context hint category: "{label}" \u2014 merged and deduplicated')
            duplicate_warned.add(label)
        seen.add(label)

    return category_data, warnings


def resolve_category(
    label: str,
    entry: dict[str, list[str]],
    spec_text: str,
    tech_text: str | None,
    spec_folder: Path,
    warnings: list[str],
) -> str:
    """One category's full resolved content: `bracket_refs` (if any) resolved
    as a single batch via `resolve_bracket_refs`, concatenated with every
    `extended_refs` entry resolved independently via `resolve_extended_ref`
    (a story can mix both forms across duplicate category lines). Empty or
    whitespace-only parts are dropped; survivors joined with a blank line."""
    parts: list[str] = []
    if entry["bracket_refs"]:
        parts.append(resolve_bracket_refs(label, entry["bracket_refs"], spec_text, tech_text, warnings))
    for ref in entry["extended_refs"]:
        content = resolve_extended_ref(spec_folder, ref)
        if content is None:
            _missing(warnings, ref, "extended reference chain")
        else:
            parts.append(content)
    return "\n\n".join(part.strip() for part in parts if part and part.strip())


def enforce_budget(
    fetched: dict[str, str], byte_counts: dict[str, int], budget_bytes: int
) -> tuple[dict[str, str], dict[str, int], bool]:
    """Relevance-ordered truncation against `budget_bytes` (Story 3, AC2/AC3).

    Walks `CATEGORY_ORDER` (highest relevance first — see the comment on
    that constant for why truncation reuses the output-order sequence).
    Each category is kept whole while it fits in the remaining budget; the
    first category that doesn't fit is truncated to exactly the remaining
    byte allowance (a UTF-8-safe prefix — a trailing partial multi-byte
    character is dropped rather than emitting invalid UTF-8), and every
    category after it is dropped entirely, never partially (it never gets a
    turn at the budget). `byte_counts` in the returned dict reflect what was
    actually kept, i.e. bytes the pipeline actually delivers, not the
    pre-truncation size.

    Comparison is strictly-greater-than: a total exactly equal to
    `budget_bytes` returns the input unchanged with `truncated=False`
    (Interaction Edge Case: "Budget exactly at threshold").
    """
    total = sum(byte_counts.values())
    if total <= budget_bytes:
        return fetched, byte_counts, False

    kept_fetched: dict[str, str] = {}
    kept_bytes: dict[str, int] = {}
    remaining = budget_bytes
    for label in CATEGORY_ORDER:
        key = CATEGORIES[label]
        if key not in fetched or remaining <= 0:
            continue
        encoded = fetched[key].encode("utf-8")
        if len(encoded) <= remaining:
            kept_fetched[key] = fetched[key]
            kept_bytes[key] = len(encoded)
            remaining -= len(encoded)
        else:
            truncated_text = encoded[:remaining].decode("utf-8", errors="ignore")
            if truncated_text:
                kept_fetched[key] = truncated_text
                kept_bytes[key] = len(truncated_text.encode("utf-8"))
            remaining = 0
    return kept_fetched, kept_bytes, True


def _payload(
    fetched: dict[str, str],
    byte_counts: dict[str, int],
    warnings: list[str],
    budget_bytes: int | None = None,
) -> dict[str, Any]:
    truncated = False
    if budget_bytes is not None:
        actual_total = sum(byte_counts.values())
        fetched, byte_counts, truncated = enforce_budget(fetched, byte_counts, budget_bytes)
        if truncated:
            warnings.append(
                f"\u26a0\ufe0f fetched_context truncated ({actual_total} of {budget_bytes} bytes)"
            )
    bytes_out = dict(byte_counts)
    bytes_out["total"] = sum(byte_counts.values())
    return {
        "fetched_context": fetched,
        "warnings": warnings,
        "bytes": bytes_out,
        "truncated": truncated,
    }


def assemble(story_path: Path, budget_bytes: int | None = None) -> dict[str, Any]:
    """Assemble the bounded context payload for one story file.

    `budget_bytes`, when given, is enforced by `_payload()` via
    `enforce_budget()` (Story 3) — content strictly exceeding it is
    truncated by relevance order. `None` (the default) remains unbounded.
    """
    warnings: list[str] = []
    fetched: dict[str, str] = {}
    byte_counts: dict[str, int] = {}

    try:
        story_text = story_path.read_text(encoding="utf-8")
    except OSError:
        warnings.append(f"\u26a0\ufe0f Story file unreadable or missing: {story_path}")
        return _payload(fetched, byte_counts, warnings)

    section = extract_markdown_section(story_text, "## Context for Agents")
    if section is None:
        warnings.append('\u2139\ufe0f No "## Context for Agents" section \u2014 proceeding with spec-lite only')
        return _payload(fetched, byte_counts, warnings)

    category_data, parse_warnings = parse_hint_lines(section)
    warnings.extend(parse_warnings)
    category_data = {
        label: entry for label, entry in category_data.items() if entry["bracket_refs"] or entry["extended_refs"]
    }
    if not category_data:
        return _payload(fetched, byte_counts, warnings)

    spec_folder = story_path.resolve().parent.parent
    spec_path = resolve_spec_file(spec_folder, "spec.md")
    spec_text: str | None = None
    if spec_path is not None:
        try:
            spec_text = spec_path.read_text(encoding="utf-8")
        except OSError:
            spec_text = None
    if spec_text is None:
        warnings.append("\u26a0\ufe0f spec.md absent or unreadable \u2014 falling back to spec-lite only")
        return _payload(fetched, byte_counts, warnings)

    tech_path = resolve_spec_file(spec_folder, "technical-spec.md")
    tech_text: str | None = None
    if tech_path is not None:
        try:
            tech_text = tech_path.read_text(encoding="utf-8")
        except OSError:
            tech_text = None

    for label in CATEGORY_ORDER:
        entry = category_data.get(label)
        if entry is None:
            continue
        content = resolve_category(label, entry, spec_text, tech_text, spec_folder, warnings)
        if content:
            key = CATEGORIES[label]
            fetched[key] = content
            byte_counts[key] = len(content.encode("utf-8"))

    return _payload(fetched, byte_counts, warnings, budget_bytes)


def main(argv: list[str] | None = None) -> int:
    """CLI entrypoint: `assemble --story PATH [--budget-bytes N]`.

    The outer `except Exception` around the `assemble()` call is a second,
    broader degrade path on top of `assemble()`'s own internal handling: it
    catches failures `assemble()` doesn't already guard against internally
    (e.g. invalid-UTF-8 story content raising `UnicodeDecodeError` from
    `Path.read_text()`, distinct from the `OSError` `assemble()` catches for
    a missing/unreadable file) so the process still prints a valid JSON
    payload and exits 0 — this script never raises (Business Rule 1)."""
    parser = argparse.ArgumentParser(description=__doc__)
    sub = parser.add_subparsers(dest="command", required=True)

    p_asm = sub.add_parser("assemble", help="assemble bounded context for one story")
    p_asm.add_argument("--story", required=True, type=Path)
    p_asm.add_argument("--budget-bytes", type=int, default=None)

    args = parser.parse_args(argv)

    if args.command == "assemble":
        try:
            result = assemble(args.story, budget_bytes=args.budget_bytes)
        except Exception as exc:  # never raise — degrade instead (Business Rule 1)
            result = {
                "fetched_context": {},
                "warnings": [f"\u26a0\ufe0f story-context.py internal error: {exc}"],
                "bytes": {"total": 0},
                "truncated": False,
            }
        print(json.dumps(result))
    return 0


if __name__ == "__main__":
    sys.exit(main())
