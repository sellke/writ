#!/usr/bin/env python3
"""Knowledge ledger consolidation reducer (Phase 7).

Reads the markdown knowledge ledger under `.writ/knowledge/`, proposes merges of
near-duplicate entries, surfaces contradiction pairs for human review, and flags
stale entries on observable signals only. It is **non-destructive by default**:
`--dry-run` (the default) emits a proposal report plus a preview unified diff and
writes nothing; `--apply` writes only human-approved merges.

Core principle: **merge, never append.** A log grows unbounded; a merged document
stays searchable. Markdown in, markdown out, reviewable as a PR diff.

Design (see .writ/specs/2026-07-10-knowledge-consolidation/):
  - D2  Non-destructive by default: dry-run writes nothing; a dry-run scenario is
        byte-identical before and after.
  - D3  Duplicate detection reuses the `_tokens` + Jaccard approach from
        scripts/phase-state.py, applied pairwise within a category.
  - D4  Lineage is bidirectional: the surviving canonical entry gains
        `replaces: [...]`; each merged-away entry becomes a tombstone carrying
        `superseded_by: <canonical-slug>`. Glossary entries are always tombstoned,
        never deleted (the filename is an addressable identifier).
  - D5  Contradictions are surfaced, never auto-resolved.
  - D6  Stale is defined by observable signal (superseded, all `related_artifacts`
        missing, or dominated by a newer merged entry) — never age alone.
  - D7  Detection spans all four categories; comparisons are within-category.
  - D8  Markdown in, markdown out; the reviewable diff is the deliverable.

Usage:
  python3 scripts/knowledge-consolidate.py --dry-run          # default; preview only
  python3 scripts/knowledge-consolidate.py --json             # machine-readable proposal
  python3 scripts/knowledge-consolidate.py --apply            # write approved merges
  python3 scripts/knowledge-consolidate.py \
      --knowledge-dir path/to/knowledge --repo-root path/to/repo --json
"""

from __future__ import annotations

import argparse
import difflib
import json
import re
import sys
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Optional

CATEGORIES = ("decisions", "conventions", "glossary", "lessons")

# Conservative thresholds. A false-positive merely surfaces a proposal a human
# dismisses; silent auto-resolution or a spurious merge is what we must avoid.
DUP_THRESHOLD = 0.5          # body-token Jaccard to nominate a merge candidate
SUBJECT_THRESHOLD = 0.34     # tags+title Jaccard for contradiction subject overlap
DOMINATION_COVERAGE = 0.9    # fraction of an entry's tokens covered by a newer entry

# Words whose asymmetric presence between two same-subject TL;DRs signals a
# polarity conflict ("do X" vs. "never do X"). Heuristic and deliberately narrow.
NEGATIONS = {
    "not", "never", "no", "avoid", "avoids", "avoided", "without",
    "dont", "don't", "cannot", "cant", "can't", "shouldnt", "shouldn't",
    "stop", "reject", "rejects", "rejected", "forbid", "forbidden",
}

_WORD = re.compile(r"[a-z0-9]+")
_STOP = {"the", "a", "an", "and", "or", "of", "to", "in", "is", "for",
         "when", "then", "with", "that", "this", "it", "be", "on", "as"}


def _tokens(text: str) -> set:
    """Stopword-filtered, lowercased word set (len > 2).

    Reused verbatim from scripts/phase-state.py `_tokens` so the similarity metric
    stays consistent across the substrate (D3). Do not diverge without cause."""
    return {w for w in _WORD.findall(text.lower()) if len(w) > 2 and w not in _STOP}


def _jaccard(a: set, b: set) -> float:
    if not a or not b:
        return 0.0
    return len(a & b) / len(a | b)


@dataclass
class Entry:
    path: Path
    category: str
    slug: str
    title: str
    tldr: str
    body: str
    raw: str
    fm_lines: list  # frontmatter lines (between the --- fences), keepends
    open_fence: str
    close_fence: str
    tags: list = field(default_factory=list)
    created: str = ""
    related_artifacts: list = field(default_factory=list)
    superseded_by: Optional[str] = None
    replaces: list = field(default_factory=list)

    @property
    def body_tokens(self) -> set:
        return _tokens(self.body)

    @property
    def subject_tokens(self) -> set:
        return _tokens(self.title) | {t.lower() for t in self.tags}

    @property
    def is_tombstone(self) -> bool:
        return bool(self.superseded_by)


# --------------------------------------------------------------------------- #
# Tolerant parsing
# --------------------------------------------------------------------------- #

def _parse_frontmatter(fm_lines: list) -> dict:
    """Minimal, tolerant YAML-subset parser: `key: value`, inline `[a, b]`
    lists, and block lists of `  - item`. Never raises on unfamiliar shapes."""
    data: dict = {}
    current_key = None
    for raw in fm_lines:
        line = raw.rstrip("\n")
        if not line.strip():
            continue
        m = re.match(r"^(\s*)-\s+(.*)$", line)
        if m and current_key is not None:
            data.setdefault(current_key, [])
            if isinstance(data[current_key], list):
                data[current_key].append(m.group(2).strip())
            continue
        m = re.match(r"^([A-Za-z_][\w-]*):\s*(.*)$", line)
        if not m:
            continue
        key, value = m.group(1), m.group(2).strip()
        current_key = key
        if value == "":
            data[key] = []  # a block list (items follow) or an empty value
        elif value.startswith("[") and value.endswith("]"):
            inner = value[1:-1].strip()
            data[key] = [v.strip() for v in inner.split(",") if v.strip()] if inner else []
        else:
            data[key] = value
    return data


def parse_entry(path: Path, category: str):
    """Return (Entry, None) on success or (None, reason) when the entry must be
    skipped. Never rewrites or drops a file; a skip is advisory only."""
    try:
        raw = path.read_text(encoding="utf-8")
    except (OSError, UnicodeDecodeError) as err:
        return None, f"unreadable file ({err.__class__.__name__})"

    lines = raw.splitlines(keepends=True)
    if not lines or lines[0].strip() != "---":
        return None, "missing frontmatter"
    close_idx = None
    for i in range(1, len(lines)):
        if lines[i].strip() == "---":
            close_idx = i
            break
    if close_idx is None:
        return None, "unterminated frontmatter"

    fm_lines = lines[1:close_idx]
    body = "".join(lines[close_idx + 1:])
    fm = _parse_frontmatter(fm_lines)

    fm_category = fm.get("category")
    if not fm_category:
        return None, "missing category in frontmatter"
    if isinstance(fm_category, list):
        return None, "malformed category"
    if fm_category != category:
        return None, f"category '{fm_category}' does not match directory '{category}'"

    title_match = re.search(r"^#\s+(.*)$", body, re.MULTILINE)
    title = title_match.group(1).strip() if title_match else ""

    tldr = _section(body, "TL;DR")
    if tldr is None:
        return None, "missing '## TL;DR' section"

    def _as_list(value) -> list:
        if value is None:
            return []
        if isinstance(value, list):
            return value
        return [value]

    entry = Entry(
        path=path,
        category=category,
        slug=path.stem,
        title=title,
        tldr=tldr.strip(),
        body=body,
        raw=raw,
        fm_lines=fm_lines,
        open_fence=lines[0],
        close_fence=lines[close_idx],
        tags=_as_list(fm.get("tags")),
        created=fm.get("created", "") if not isinstance(fm.get("created"), list) else "",
        related_artifacts=_as_list(fm.get("related_artifacts")),
        superseded_by=(fm.get("superseded_by") or None) if not isinstance(fm.get("superseded_by"), list) else None,
        replaces=_as_list(fm.get("replaces")),
    )
    return entry, None


def _section(body: str, name: str):
    """Return the text of `## <name>` up to the next `## ` header, or None."""
    pattern = re.compile(r"^##\s+" + re.escape(name) + r"\s*$", re.MULTILINE)
    m = pattern.search(body)
    if not m:
        return None
    start = m.end()
    nxt = re.search(r"^##\s+", body[start:], re.MULTILINE)
    return body[start:start + nxt.start()] if nxt else body[start:]


def scan_ledger(knowledge_dir: Path):
    """Return (entries_by_category, skipped). Ignores README.md and .gitkeep."""
    by_category: dict = {c: [] for c in CATEGORIES}
    skipped: list = []
    for category in CATEGORIES:
        cat_dir = knowledge_dir / category
        if not cat_dir.is_dir():
            continue
        for path in sorted(cat_dir.glob("*.md")):
            if path.name in ("README.md", ".gitkeep"):
                continue
            entry, reason = parse_entry(path, category)
            if entry is None:
                skipped.append({"path": str(path), "category": category, "reason": reason})
            else:
                by_category[category].append(entry)
    return by_category, skipped


# --------------------------------------------------------------------------- #
# Detection
# --------------------------------------------------------------------------- #

def _clusters(entries: list):
    """Union-find over pairwise duplicate edges → list of index clusters."""
    n = len(entries)
    parent = list(range(n))

    def find(x):
        while parent[x] != x:
            parent[x] = parent[parent[x]]
            x = parent[x]
        return x

    def union(a, b):
        parent[find(a)] = find(b)

    scores: dict = {}
    tokens = [e.body_tokens for e in entries]
    for i in range(n):
        for j in range(i + 1, n):
            score = _jaccard(tokens[i], tokens[j])
            if score >= DUP_THRESHOLD:
                union(i, j)
                scores[(i, j)] = score

    groups: dict = {}
    for i in range(n):
        groups.setdefault(find(i), []).append(i)
    return [idxs for idxs in groups.values() if len(idxs) > 1], scores


def _pick_canonical(entries: list, idxs: list) -> int:
    """Richer (longer body), tie-break newer `created`, then slug for stability."""
    return max(idxs, key=lambda i: (len(entries[i].body), entries[i].created, entries[i].slug))


def detect_duplicates(entries: list):
    """Return merge proposals for one category. Tombstones are excluded."""
    live = [e for e in entries if not e.is_tombstone]
    clusters, scores = _clusters(live)
    proposals = []
    for idxs in clusters:
        canon_i = _pick_canonical(live, idxs)
        canonical = live[canon_i]
        members = [live[i] for i in idxs]
        superseded = [e for e in members if e is not canonical]
        best = 0.0
        for (i, j), s in scores.items():
            if i in idxs and j in idxs:
                best = max(best, s)
        proposals.append({
            "canonical": canonical,
            "superseded": superseded,
            "members": members,
            "score": round(best, 3),
        })
    return proposals


def _has_negation(text: str) -> bool:
    return bool(_WORD.findall(text.lower())) and any(
        w in NEGATIONS for w in re.findall(r"[a-z']+", text.lower())
    )


def detect_contradictions(entries: list):
    """Pairs with high subject overlap but a polarity conflict in their TL;DRs.
    Surfaced for human review only; never resolved (D5)."""
    live = [e for e in entries if not e.is_tombstone]
    pairs = []
    for i in range(len(live)):
        for j in range(i + 1, len(live)):
            a, b = live[i], live[j]
            subject = _jaccard(a.subject_tokens, b.subject_tokens)
            if subject < SUBJECT_THRESHOLD:
                continue
            if _jaccard(a.body_tokens, b.body_tokens) >= DUP_THRESHOLD:
                continue  # a duplicate, not a contradiction
            shared_tldr = _tokens(a.tldr) & _tokens(b.tldr)
            if len(shared_tldr) < 2:
                continue
            if _has_negation(a.tldr) == _has_negation(b.tldr):
                continue  # no polarity asymmetry
            pairs.append({
                "pair": (a, b),
                "subject_overlap": round(subject, 3),
                "signal": "high subject overlap with a negation-asymmetric assertion",
            })
    return pairs


def detect_stale(entries: list, repo_root: Path):
    """Flag entries on observable signals only (D6). Never age-based."""
    flags = []
    live = [e for e in entries if not e.is_tombstone]
    token_index = [(e, e.body_tokens) for e in live]
    for entry in entries:
        signals = []
        if entry.is_tombstone:
            signals.append("superseded (carries superseded_by lineage)")
        if entry.related_artifacts:
            missing = [a for a in entry.related_artifacts if not _artifact_exists(a, repo_root)]
            if len(missing) == len(entry.related_artifacts):
                signals.append("all related_artifacts missing on disk: " + ", ".join(missing))
        if not entry.is_tombstone:
            dominated_by = _dominating_entry(entry, token_index)
            if dominated_by is not None:
                signals.append("dominated by newer entry '%s'" % dominated_by)
        if signals:
            flags.append({"entry": entry, "signals": signals})
    return flags


def _dominating_entry(entry: Entry, token_index):
    my = entry.body_tokens
    if not my:
        return None
    for other, other_tokens in token_index:
        if other is entry:
            continue
        if not (other.created and entry.created and other.created > entry.created):
            continue
        coverage = len(my & other_tokens) / len(my)
        if coverage >= DOMINATION_COVERAGE:
            return other.slug
    return None


def _artifact_exists(artifact: str, repo_root: Path) -> bool:
    try:
        p = Path(artifact)
        if p.is_absolute():
            return p.exists()
        return (repo_root / artifact).exists()
    except OSError:
        # A path-check error must never over-flag: treat as present (D6 shadow path).
        return True


# --------------------------------------------------------------------------- #
# Merge / lineage construction
# --------------------------------------------------------------------------- #

def _canonical_with_replaces(canonical: Entry, superseded_slugs: list) -> str:
    """Return canonical file content with a `replaces:` block appended to the
    frontmatter. Minimal edit: body is untouched, existing frontmatter preserved."""
    existing = set(canonical.replaces)
    additions = [s for s in superseded_slugs if s not in existing]
    new_fm = list(canonical.fm_lines)
    if canonical.replaces:
        # `replaces` already present; append missing slugs after the block.
        insert_at = _end_of_block(new_fm, "replaces")
        for k, slug in enumerate(additions):
            new_fm.insert(insert_at + k, "  - %s\n" % slug)
    else:
        new_fm.append("replaces:\n")
        for slug in superseded_slugs:
            new_fm.append("  - %s\n" % slug)
    return canonical.open_fence + "".join(new_fm) + canonical.close_fence + canonical.body


def _end_of_block(fm_lines: list, key: str) -> int:
    start = None
    for idx, line in enumerate(fm_lines):
        if re.match(r"^%s:\s*$" % re.escape(key), line.rstrip("\n")):
            start = idx
            break
    if start is None:
        return len(fm_lines)
    idx = start + 1
    while idx < len(fm_lines) and re.match(r"^\s*-\s+", fm_lines[idx]):
        idx += 1
    return idx


def _tombstone_content(entry: Entry, canonical: Entry) -> str:
    rel = "../%s/%s.md" % (canonical.category, canonical.slug)
    label = canonical.title or canonical.slug
    lines = ["---\n", "category: %s\n" % entry.category]
    if entry.created:
        lines.append("created: %s\n" % entry.created)
    lines.append("superseded_by: %s\n" % canonical.slug)
    lines.append("---\n\n")
    lines.append("# Superseded\n\n")
    lines.append("Merged into [%s](%s).\n" % (label, rel))
    return "".join(lines)


def _proposed_files(proposals: list):
    """Map each merge proposal to the (Entry, new_content) pairs it would write."""
    plans = []
    for prop in proposals:
        canonical = prop["canonical"]
        superseded = prop["superseded"]
        slugs = [e.slug for e in superseded]
        files = [{
            "entry": canonical,
            "action": "add-replaces",
            "content": _canonical_with_replaces(canonical, slugs),
        }]
        for e in superseded:
            files.append({
                "entry": e,
                "action": "tombstone",
                "content": _tombstone_content(e, canonical),
            })
        plans.append({"proposal": prop, "files": files})
    return plans


def _unified_diff(entry: Entry, new_content: str, repo_root: Path) -> str:
    try:
        rel = str(entry.path.relative_to(repo_root))
    except ValueError:
        rel = str(entry.path)
    before = entry.raw.splitlines(keepends=True)
    after = new_content.splitlines(keepends=True)
    diff = difflib.unified_diff(before, after, fromfile="a/" + rel, tofile="b/" + rel)
    return "".join(diff)


# --------------------------------------------------------------------------- #
# Orchestration
# --------------------------------------------------------------------------- #

def consolidate(knowledge_dir: Path, repo_root: Path, apply: bool) -> dict:
    if not knowledge_dir.is_dir():
        return {
            "knowledge_dir": str(knowledge_dir),
            "mode": "apply" if apply else "dry-run",
            "status": "no-ledger",
            "entries_scanned": 0,
            "skipped": [], "merges": [], "contradictions": [], "stale": [],
            "diff": "", "written": [], "noop": True,
        }

    by_category, skipped = scan_ledger(knowledge_dir)
    entries_scanned = sum(len(v) for v in by_category.values())

    all_merges = []
    all_contradictions = []
    all_stale = []
    for category in CATEGORIES:
        entries = by_category[category]
        for prop in detect_duplicates(entries):
            all_merges.append((category, prop))
        for con in detect_contradictions(entries):
            all_contradictions.append((category, con))
        for flag in detect_stale(entries, repo_root):
            all_stale.append((category, flag))

    proposals = [p for _, p in all_merges]
    plans = _proposed_files(proposals)

    diff_parts = []
    for plan in plans:
        for f in plan["files"]:
            diff_parts.append(_unified_diff(f["entry"], f["content"], repo_root))
    diff_text = "".join(diff_parts)

    written = []
    if apply:
        for plan in plans:
            for f in plan["files"]:
                f["entry"].path.write_text(f["content"], encoding="utf-8")
                written.append({"path": str(f["entry"].path), "action": f["action"]})

    noop = not proposals and not all_contradictions and not all_stale

    return {
        "knowledge_dir": str(knowledge_dir),
        "mode": "apply" if apply else "dry-run",
        "status": "ok",
        "entries_scanned": entries_scanned,
        "skipped": skipped,
        "merges": [_merge_json(cat, p) for cat, p in all_merges],
        "contradictions": [_contradiction_json(cat, c) for cat, c in all_contradictions],
        "stale": [_stale_json(cat, f) for cat, f in all_stale],
        "diff": diff_text,
        "written": written,
        "noop": noop,
    }


def _merge_json(category: str, prop: dict) -> dict:
    return {
        "category": category,
        "canonical": prop["canonical"].slug,
        "canonical_title": prop["canonical"].title,
        "replaces": [e.slug for e in prop["superseded"]],
        "members": [e.slug for e in prop["members"]],
        "score": prop["score"],
    }


def _contradiction_json(category: str, con: dict) -> dict:
    a, b = con["pair"]
    return {
        "category": category,
        "pair": [a.slug, b.slug],
        "subject_overlap": con["subject_overlap"],
        "signal": con["signal"],
        "assertions": {a.slug: a.tldr, b.slug: b.tldr},
    }


def _stale_json(category: str, flag: dict) -> dict:
    return {
        "category": category,
        "slug": flag["entry"].slug,
        "signals": flag["signals"],
    }


# --------------------------------------------------------------------------- #
# Reporting
# --------------------------------------------------------------------------- #

def render_markdown(result: dict) -> str:
    out = []
    mode = result["mode"]
    out.append("# Knowledge Consolidation Proposal (%s)\n" % mode)
    if result.get("status") == "no-ledger":
        out.append("\nNo `.writ/knowledge/` directory found — nothing to consolidate.\n")
        return "".join(out)

    out.append("\nScanned %d entries across %s.\n" % (
        result["entries_scanned"], ", ".join(CATEGORIES)))

    if result["noop"]:
        out.append("\n**Nothing to consolidate.** No duplicate, contradiction, or "
                   "stale signal was found. No file changes.\n")

    if result["merges"]:
        out.append("\n## Proposed merges (merge, never append)\n")
        for m in result["merges"]:
            out.append("\n- **%s** / canonical `%s` — %s\n" % (
                m["category"], m["canonical"], m["canonical_title"] or "(untitled)"))
            out.append("  - replaces: %s\n" % ", ".join(m["replaces"]))
            out.append("  - duplicate signal: token overlap %.3f (>= %.2f)\n" % (
                m["score"], DUP_THRESHOLD))

    if result["contradictions"]:
        out.append("\n## Contradictions — surfaced for human review, never auto-resolved\n")
        for c in result["contradictions"]:
            out.append("\n- **%s**: `%s` vs `%s` (subject overlap %.3f)\n" % (
                c["category"], c["pair"][0], c["pair"][1], c["subject_overlap"]))
            out.append("  - signal: %s\n" % c["signal"])
            for slug, tldr in c["assertions"].items():
                out.append("  - `%s`: %s\n" % (slug, tldr.replace("\n", " ").strip()))

    if result["stale"]:
        out.append("\n## Stale flags — observable signal only, awaiting explicit retirement\n")
        for s in result["stale"]:
            out.append("\n- **%s** `%s`\n" % (s["category"], s["slug"]))
            for sig in s["signals"]:
                out.append("  - %s\n" % sig)

    if result["skipped"]:
        out.append("\n## Skipped (malformed — never rewritten or dropped)\n")
        for s in result["skipped"]:
            out.append("- `%s`: %s\n" % (s["path"], s["reason"]))

    if result["diff"]:
        header = "Preview diff (no files written)" if mode == "dry-run" else "Applied diff"
        out.append("\n## %s\n\n```diff\n%s\n```\n" % (header, result["diff"].rstrip("\n")))

    if mode == "apply" and result["written"]:
        out.append("\n## Files written\n")
        for w in result["written"]:
            out.append("- `%s` (%s)\n" % (w["path"], w["action"]))
        out.append("\nThe working tree now carries a reviewable diff. Inspect it and "
                   "commit as a PR; this command does not commit.\n")

    return "".join(out)


def main(argv: Optional[list] = None) -> int:
    parser = argparse.ArgumentParser(
        description="Non-destructive knowledge ledger consolidation reducer.")
    parser.add_argument("--knowledge-dir", default=".writ/knowledge",
                        help="Path to the knowledge ledger (default: .writ/knowledge)")
    parser.add_argument("--repo-root", default="",
                        help="Repo root for resolving related_artifacts "
                             "(default: two levels above the knowledge dir)")
    group = parser.add_mutually_exclusive_group()
    group.add_argument("--dry-run", action="store_true", default=True,
                       help="Preview proposals and diff, write nothing (default)")
    group.add_argument("--apply", action="store_true", default=False,
                       help="Write human-approved merges (canonical + tombstones)")
    parser.add_argument("--json", action="store_true", default=False,
                        help="Emit machine-readable JSON instead of markdown")
    args = parser.parse_args(argv)

    knowledge_dir = Path(args.knowledge_dir)
    repo_root = Path(args.repo_root) if args.repo_root else _default_repo_root(knowledge_dir)

    result = consolidate(knowledge_dir, repo_root, apply=args.apply)

    if args.json:
        print(json.dumps(result))
    else:
        print(render_markdown(result))
    return 0


def _default_repo_root(knowledge_dir: Path) -> Path:
    # `.writ/knowledge` → repo root is two levels up. Fall back to cwd.
    resolved = knowledge_dir.resolve()
    if resolved.name == "knowledge" and resolved.parent.name == ".writ":
        return resolved.parent.parent
    return Path.cwd()


if __name__ == "__main__":
    sys.exit(main())
