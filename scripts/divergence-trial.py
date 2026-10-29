#!/usr/bin/env python3
"""Divergence trial harness (spec `2026-10-25-design-divergence`, Story 4).

Temporary and dev-only: it never ships, and Story 6 deletes it once the trial
report is committed. It scores declared-axes drafts against naive drafts on six
briefs, rated blind by one human. It never spawns a model and makes no network
call.

Subcommands:
  init   --briefs DIR --out FILE [--force]
                      DIR/*.md, each starting with `id:` and `medium:` lines.
                      Exactly six briefs, two each of ui, api, data-model.
  record --trial FILE --brief ID --arm axes|naive --drafts FILE
                      Exactly three `## Draft` blocks, each with `Title:`,
                      `Structure:`, `Trade-off:`; `Commitment:` in every axes
                      draft and in no naive draft. Copies the drafts to
                      <trial dir>/raw/<brief>/<arm>.md. Re-recording replaces.
  blind  --trial FILE --sheet OUT [--seed N]
                      Needs all twelve arms. Writes the rating sheet and
                      key.json beside it; records both hashes.
  rate   --trial FILE --sheet FILE --rated-by NAME
                      Stores every brief's ratings by set label (X/Y).
  report --trial FILE [--json]
                      keep | remove | unverifiable (reason: unrated,
                      missing_arm, key_missing, key_changed).

Output: the verdict or `pass` first, `reason:` lines when unverifiable, detail
lines, and a `divergence-trial:` summary last. `--json` prints one object.
A refusal prints `reason:` lines and the summary on stderr, leaves stdout
empty, and changes no file.

Exit 0: ran (any report verdict). Exit 2: usage error or refusal. Exit 1 is
never used.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import os
import random
import re
import sys
from pathlib import Path
from typing import Dict, List, Optional, Sequence, Tuple

SCHEMA = "divergence-trial-v1"
KEY_SCHEMA = "divergence-trial-key-v1"
ARMS = ("axes", "naive")
SETS = ("X", "Y")
MEDIA = ("ui", "api", "data-model")
PER_MEDIUM = 2
BRIEF_COUNT = PER_MEDIUM * len(MEDIA)
DRAFTS = 3
NOTE_MAX = 200
SAFE_ID = re.compile(r"^[a-z0-9][a-z0-9._-]*$")
DRAFT_HEADING = re.compile(r"^## Draft\b")
LABELS = ("Title:", "Structure:", "Trade-off:")
COMMITMENT = "Commitment:"
FIELDS = ("distinct_X", "distinct_Y", "more_distinct", "render_only_enough", "note")
ALLOWED = {
    "distinct_X": ("1", "2", "3"),
    "distinct_Y": ("1", "2", "3"),
    "more_distinct": ("X", "Y", "tie"),
    "render_only_enough": ("yes", "no"),
}
CAVEAT = ("sample: 6 briefs, one rater; declared axes must win 4 of 6 — "
          "a small sample, not a general result")
BLINDING = "blinding: honor-system; the rater opened only the sheet"
WINS_NEEDED = 4

SHEET_HEADER = """# Divergence trial rating sheet

Rate from this file alone. Do not open raw/, key.json, or the trial JSON.
Each brief shows two sets of three drafts. Fill the five lines under each
Rating heading and change nothing else:

- distinct_X / distinct_Y: 1, 2, or 3 (how many structurally different drafts the set holds)
- more_distinct: X, Y, or tie (which set is more distinct)
- render_only_enough: yes or no (could you choose a direction from these drafts without running code?)
- note: one line, at most 200 characters
"""


class Refusal(Exception):
    """Exit 2: print the reasons and a summary on stderr; no file changes."""

    def __init__(self, reasons: Sequence[str], summary: Optional[str] = None) -> None:
        super().__init__(summary or reasons[0])
        self.reasons = list(reasons)
        self.summary = summary or self.reasons[0]


# --- files ------------------------------------------------------------------


def sha256_bytes(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def sha256_file(path: Path) -> str:
    return sha256_bytes(path.read_bytes())


def write_atomic(path: Path, data: bytes) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    tmp = path.with_name(".%s.tmp" % path.name)
    try:
        tmp.write_bytes(data)
        os.replace(str(tmp), str(path))
    except BaseException:
        if tmp.is_file():
            tmp.unlink()
        raise


def json_bytes(doc: dict, sort_keys: bool = False) -> bytes:
    return (json.dumps(doc, indent=2, sort_keys=sort_keys, ensure_ascii=False)
            + "\n").encode("utf-8")


def read_text(path: Path, what: str) -> str:
    try:
        return path.read_text(encoding="utf-8")
    except (OSError, UnicodeDecodeError) as exc:
        raise Refusal(["%s_unreadable %s (%s)" % (what, path, exc.__class__.__name__)])


def load_trial(path: Path) -> dict:
    try:
        doc = json.loads(read_text(path, "trial"))
    except ValueError:
        raise Refusal(["trial_unreadable %s (not JSON)" % path])
    briefs = doc.get("briefs") if isinstance(doc, dict) else None
    if not isinstance(doc, dict) or doc.get("schema") != SCHEMA or not isinstance(briefs, list):
        raise Refusal(["not_a_trial %s is not a %s file" % (path, SCHEMA)])
    for brief in briefs:
        if (not isinstance(brief, dict) or not SAFE_ID.match(str(brief.get("id", "")))
                or brief.get("medium") not in MEDIA or not isinstance(brief.get("arms"), dict)):
            raise Refusal(["not_a_trial %s has a malformed brief entry" % path])
    return doc


def rel_to(path: Path, base: Path) -> str:
    try:
        return os.path.relpath(str(path.resolve()), str(base.resolve())).replace(os.sep, "/")
    except ValueError:  # different drives on Windows
        return str(path.resolve())


def find_brief(doc: dict, brief_id: str) -> dict:
    for brief in doc["briefs"]:
        if brief["id"] == brief_id:
            return brief
    raise Refusal(["unknown_brief %s" % brief_id])


def raw_path(trial: Path, brief_id: str, arm: str) -> Path:
    return trial.parent / "raw" / brief_id / ("%s.md" % arm)


def arms_recorded(doc: dict) -> int:
    return sum(1 for b in doc["briefs"] for arm in ARMS if arm in b["arms"])


# --- init -------------------------------------------------------------------


def parse_brief_header(text: str) -> Dict[str, str]:
    """`key: value` lines from the top of the file up to the first blank line."""
    header = {}
    for line in text.replace("\r\n", "\n").split("\n"):
        if not line.strip():
            break
        key, sep, value = line.partition(":")
        if sep:
            header.setdefault(key.strip(), value.strip())
    return header


def cmd_init(args: argparse.Namespace) -> int:
    out = Path(args.out)
    briefs_dir = Path(args.briefs)
    if out.exists() and not args.force:
        raise Refusal(["out_exists %s (pass --force to replace it)" % out])
    if not briefs_dir.is_dir():
        raise Refusal(["briefs_dir_missing %s" % briefs_dir])
    reasons: List[str] = []
    briefs = []
    for path in sorted(briefs_dir.glob("*.md")):
        data = path.read_bytes()
        header = parse_brief_header(data.decode("utf-8", errors="replace"))
        brief_id, medium = header.get("id", ""), header.get("medium", "")
        if not brief_id:
            reasons.append("missing_header %s id" % path.name)
        elif not SAFE_ID.match(brief_id):
            reasons.append("bad_id %s %r" % (path.name, brief_id))
        if not medium:
            reasons.append("missing_header %s medium" % path.name)
        elif medium not in MEDIA:
            reasons.append("bad_medium %s %r" % (path.name, medium))
        briefs.append({"id": brief_id, "medium": medium, "brief_sha256": sha256_bytes(data),
                       "arms": {}})
    if len(briefs) != BRIEF_COUNT:
        reasons.append("brief_count %d (need %d)" % (len(briefs), BRIEF_COUNT))
    split = {m: sum(1 for b in briefs if b["medium"] == m) for m in MEDIA}
    if any(n != PER_MEDIUM for n in split.values()):
        reasons.append("medium_split %s (need %d each)" % (
            " ".join("%s=%d" % (m, split[m]) for m in MEDIA), PER_MEDIUM))
    ids = [b["id"] for b in briefs if b["id"]]
    for dup in sorted({i for i in ids if ids.count(i) > 1}):
        reasons.append("duplicate_id %s" % dup)
    if reasons:
        raise Refusal(reasons, "init wrote nothing — %s" % reasons[0])
    briefs.sort(key=lambda b: b["id"])
    doc = {"schema": SCHEMA, "briefs": briefs, "blind": None, "rated_by": None, "ratings": None}
    write_atomic(out, json_bytes(doc))
    print("pass")
    for brief in briefs:
        print("brief: %s medium=%s" % (brief["id"], brief["medium"]))
    print("divergence-trial: initialized — %d briefs, no arms recorded" % len(briefs))
    return 0


# --- record -----------------------------------------------------------------


def split_drafts(text: str) -> List[List[str]]:
    """Body lines of each `## Draft` block; text before the first heading is dropped."""
    blocks: List[List[str]] = []
    for line in text.replace("\r\n", "\n").split("\n"):
        if DRAFT_HEADING.match(line):
            blocks.append([])
        elif blocks:
            blocks[-1].append(line)
    return blocks


def is_commitment(line: str) -> bool:
    return line.lstrip().startswith(COMMITMENT)


def structure_span(body: List[str]) -> Tuple[int, int]:
    """(index of the `Structure:` line, index where its block ends).

    The block runs until the next `Structure:`, `Trade-off:`, or `Commitment:`
    line, so a `Title:` line inside it (a UI field, say) is content.
    """
    start = next((i for i, line in enumerate(body) if line.startswith("Structure:")), None)
    if start is None:
        return len(body), len(body)
    for end in range(start + 1, len(body)):
        line = body[end]
        if line.startswith(("Structure:", "Trade-off:")) or is_commitment(line):
            return start, end
    return start, len(body)


def title_lines(body: List[str]) -> List[int]:
    """`Title:` lines outside the Structure block; the first is the draft's title."""
    start, end = structure_span(body)
    return [i for i, line in enumerate(body)
            if line.startswith("Title:") and not start < i < end]


def draft_problems(blocks: List[List[str]], arm: str) -> List[str]:
    reasons: List[str] = []
    if len(blocks) != DRAFTS:
        return ["draft_count %d (need %d)" % (len(blocks), DRAFTS)]
    for n, body in enumerate(blocks, 1):
        for label in LABELS:
            if label == "Title:":
                hits = title_lines(body)
            else:
                hits = [i for i, line in enumerate(body) if line.startswith(label)]
            name = label[:-1]
            if not hits:
                reasons.append("missing_field draft %d %s" % (n, name))
                continue
            if len(hits) > 1:
                reasons.append("duplicate_field draft %d %s" % (n, name))
            value = body[hits[0]][len(label):].strip()
            if label == "Structure:" and not value:
                start, end = structure_span(body)
                value = "".join(body[start + 1:end]).strip()
            if not value:
                reasons.append("empty_field draft %d %s" % (n, name))
        commitments = [i for i, line in enumerate(body) if is_commitment(line)]
        if arm == "axes":
            reasons += commitment_problems(n, body, commitments)
        if arm == "naive" and commitments:
            reasons.append("commitment_present draft %d (naive drafts carry none)" % n)
    return reasons


def commitment_problems(n: int, body: List[str], hits: List[int]) -> List[str]:
    """An axes draft's commitment is one non-empty line, so `blind` can drop all of it.

    Text carried onto the next line would survive blinding and mark the set.
    """
    if not hits:
        return ["commitment_missing draft %d (axes drafts declare one)" % n]
    if len(hits) > 1:
        return ["duplicate_field draft %d Commitment" % n]
    line = body[hits[0]].lstrip()
    if not line[len(COMMITMENT):].strip():
        return ["empty_field draft %d Commitment" % n]
    following = body[hits[0] + 1] if hits[0] + 1 < len(body) else ""
    if following.strip() and not following.startswith(LABELS):
        return ["commitment_multiline draft %d (keep the commitment on one line)" % n]
    return []


def cmd_record(args: argparse.Namespace) -> int:
    trial = Path(args.trial)
    doc = load_trial(trial)
    brief = find_brief(doc, args.brief)
    if doc.get("blind"):
        raise Refusal(["already_blinded (re-recording would invalidate the sheet and key)"])
    drafts = Path(args.drafts)
    try:
        data = drafts.read_bytes()
        text = data.decode("utf-8")
    except (OSError, UnicodeDecodeError) as exc:
        raise Refusal(["drafts_unreadable %s (%s)" % (drafts, exc.__class__.__name__)])
    blocks = split_drafts(text)
    reasons = draft_problems(blocks, args.arm)
    if reasons:
        raise Refusal(reasons, "%s %s not recorded — %s" % (args.brief, args.arm, reasons[0]))
    raw = raw_path(trial, args.brief, args.arm)
    write_atomic(raw, data)
    brief["arms"][args.arm] = {"sha256": sha256_bytes(data), "drafts": len(blocks)}
    write_atomic(trial, json_bytes(doc))
    print("pass")
    print("brief: %s arm=%s drafts=%d sha256=%s" % (args.brief, args.arm, len(blocks),
                                                     brief["arms"][args.arm]["sha256"][:12]))
    print("raw: %s" % rel_to(raw, trial.parent))
    print("divergence-trial: recorded %s %s — %d drafts, %d of %d arms recorded" % (
        args.brief, args.arm, len(blocks), arms_recorded(doc), len(doc["briefs"]) * len(ARMS)))
    return 0


# --- sheet ------------------------------------------------------------------


def blinded_body(lines: List[str]) -> List[str]:
    """A draft as the rater sees it: no title, no Commitment line, no trailing spaces,
    and no run of blank lines a dropped line could leave behind."""
    titles = title_lines(lines)
    title = titles[0] if titles else None
    kept: List[str] = []
    for i, line in enumerate(lines):
        if i == title or is_commitment(line):
            continue
        line = line.rstrip()
        if line or (kept and kept[-1]):
            kept.append(line)
    while kept and not kept[0]:
        kept.pop(0)
    while kept and not kept[-1]:
        kept.pop()
    return kept


def brief_heading(brief: dict) -> str:
    return "## Brief %s (medium: %s)" % (brief["id"], brief["medium"])


def rating_heading(brief_id: str) -> str:
    return "### Rating: %s" % brief_id


def normalize(text: str) -> List[str]:
    lines = [line.rstrip() for line in text.replace("\r\n", "\n").replace("\r", "\n").split("\n")]
    while lines and not lines[-1]:
        lines.pop()
    return lines


def locate_ratings(lines: List[str], brief_ids: Sequence[str]) -> Tuple[Dict[str, int], List[str]]:
    """Index of the first field line under each brief's Rating heading.

    The heading is followed by one blank line and the five field lines in order.
    """
    found: Dict[str, int] = {}
    problems: List[str] = []
    for brief_id in brief_ids:
        heading = rating_heading(brief_id)
        if heading not in lines:
            problems.append("sheet_malformed %s (no '%s' heading)" % (brief_id, heading))
            continue
        start = lines.index(heading) + 2
        block = lines[start:start + len(FIELDS)]
        if (lines[start - 1:start] != [""] or len(block) != len(FIELDS)
                or any(not line.startswith(f + ":") for line, f in zip(block, FIELDS))):
            problems.append("sheet_malformed %s (the five rating lines are not intact)" % brief_id)
            continue
        found[brief_id] = start
    return found, problems


def body_hash(lines: List[str], starts: Dict[str, int]) -> str:
    blank = list(lines)
    for start in starts.values():
        for offset, field in enumerate(FIELDS):
            blank[start + offset] = field + ":"
    return sha256_bytes(("\n".join(blank) + "\n").encode("utf-8"))


def build_sheet(doc: dict, drafts: Dict[Tuple[str, str], List[List[str]]],
                rng: random.Random) -> Tuple[str, dict]:
    out = [SHEET_HEADER.rstrip("\n")]
    key: Dict[str, dict] = {}
    for brief in doc["briefs"]:
        arms = list(ARMS)
        rng.shuffle(arms)
        entry = {}
        out += ["", brief_heading(brief)]
        for label, arm in zip(SETS, arms):
            order = list(range(1, DRAFTS + 1))
            rng.shuffle(order)
            entry[label] = {"arm": arm, "drafts": order}
            out += ["", "### Set %s" % label]
            for position, original in enumerate(order, 1):
                out += ["", "#### Draft %d" % position, ""]
                out += blinded_body(drafts[(brief["id"], arm)][original - 1])
        out += ["", rating_heading(brief["id"]), ""]
        out += [field + ":" for field in FIELDS]
        key[brief["id"]] = entry
    return "\n".join(out) + "\n", {"schema": KEY_SCHEMA, "briefs": key}


# --- blind ------------------------------------------------------------------


def cmd_blind(args: argparse.Namespace) -> int:
    trial = Path(args.trial)
    doc = load_trial(trial)
    if doc.get("ratings"):
        raise Refusal(["already_rated (a new sheet would orphan the stored ratings)"])
    reasons: List[str] = []
    drafts: Dict[Tuple[str, str], List[List[str]]] = {}
    for brief in doc["briefs"]:
        for arm in ARMS:
            recorded = brief["arms"].get(arm)
            if not isinstance(recorded, dict):
                reasons.append("missing_arm %s %s" % (brief["id"], arm))
                continue
            raw = raw_path(trial, brief["id"], arm)
            if not raw.is_file():
                reasons.append("raw_missing %s %s (%s)" % (brief["id"], arm, raw))
                continue
            data = raw.read_bytes()
            if sha256_bytes(data) != recorded.get("sha256"):
                reasons.append("raw_changed %s %s (re-record it)" % (brief["id"], arm))
                continue
            drafts[(brief["id"], arm)] = split_drafts(data.decode("utf-8"))
    if reasons:
        raise Refusal(reasons, "no sheet or key written — %s" % reasons[0])
    rng = random.Random(args.seed) if args.seed is not None else random.Random()
    sheet_text, key_doc = build_sheet(doc, drafts, rng)
    lines = normalize(sheet_text)
    starts, problems = locate_ratings(lines, [b["id"] for b in doc["briefs"]])
    if problems:  # a draft line collides with the sheet's own structure
        raise Refusal(problems, "no sheet or key written — the sheet would not parse")
    sheet = Path(args.sheet)
    key_path = sheet.parent / "key.json"
    key_data = json_bytes(key_doc, sort_keys=True)
    write_atomic(sheet, sheet_text.encode("utf-8"))
    write_atomic(key_path, key_data)
    doc["blind"] = {"sheet": rel_to(sheet, trial.parent),
                    "sheet_body_sha256": body_hash(lines, starts),
                    "key": rel_to(key_path, trial.parent),
                    "key_sha256": sha256_bytes(key_data)}
    write_atomic(trial, json_bytes(doc))
    print("pass")
    print("sheet: %s" % sheet)
    print("key: %s" % key_path)
    print("divergence-trial: blinded %d briefs — sheet %s, key %s" % (
        len(doc["briefs"]), doc["blind"]["sheet"], doc["blind"]["key"]))
    return 0


# --- rate -------------------------------------------------------------------


def field_problems(brief_id: str, values: Dict[str, str]) -> List[str]:
    reasons = []
    for field in FIELDS:
        value = values[field]
        if not value:
            reasons.append("blank_field %s %s" % (brief_id, field))
        elif field == "note":
            if len(value) > NOTE_MAX:
                reasons.append("note_too_long %s (%d chars, max %d)" % (brief_id, len(value),
                                                                        NOTE_MAX))
        elif value not in ALLOWED[field]:
            reasons.append("out_of_range %s %s=%r (allowed: %s)" % (
                brief_id, field, value, "|".join(ALLOWED[field])))
    return reasons


def cmd_rate(args: argparse.Namespace) -> int:
    trial = Path(args.trial)
    doc = load_trial(trial)
    blind = doc.get("blind")
    if not isinstance(blind, dict) or not blind.get("sheet_body_sha256"):
        raise Refusal(["not_blinded (run blind first)"])
    rater = args.rated_by.strip()
    if not rater or "\n" in rater:
        raise Refusal(["empty_rater (--rated-by names the human who rated)"])
    lines = normalize(read_text(Path(args.sheet), "sheet"))
    brief_ids = [b["id"] for b in doc["briefs"]]
    starts, problems = locate_ratings(lines, brief_ids)
    if problems:
        raise Refusal(problems, "trial file unchanged — %s" % problems[0])
    reasons: List[str] = []
    ratings: Dict[str, dict] = {}
    for brief_id in brief_ids:
        start = starts[brief_id]
        after = start + len(FIELDS)
        if after < len(lines) and lines[after]:
            reasons.append("note_multiline %s (the note must be one line)" % brief_id)
        values = {f: lines[start + i][len(f) + 1:].strip() for i, f in enumerate(FIELDS)}
        reasons += field_problems(brief_id, values)
        ratings[brief_id] = {
            "distinct_X": int(values["distinct_X"]) if values["distinct_X"].isdigit() else None,
            "distinct_Y": int(values["distinct_Y"]) if values["distinct_Y"].isdigit() else None,
            "more_distinct": values["more_distinct"],
            "render_only_enough": values["render_only_enough"],
            "note": values["note"],
        }
    if not any(r.startswith("note_multiline") for r in reasons):
        if body_hash(lines, starts) != blind["sheet_body_sha256"]:
            reasons.insert(0, "body_changed (the sheet differs from the blinded one outside "
                              "the rating lines; restore it and re-fill)")
    if reasons:
        raise Refusal(reasons, "trial file unchanged — %s" % reasons[0])
    doc["rated_by"] = rater
    doc["ratings"] = ratings
    write_atomic(trial, json_bytes(doc))
    print("pass")
    for brief_id in brief_ids:
        print("brief: %s rated" % brief_id)
    print("divergence-trial: rated %d briefs by %s" % (len(brief_ids), rater))
    return 0


# --- report -----------------------------------------------------------------


def valid_rating(rating: object) -> bool:
    if not isinstance(rating, dict):
        return False
    for field in FIELDS:
        value = rating.get(field)
        if field == "note":
            if not isinstance(value, str) or not value.strip() or len(value) > NOTE_MAX \
                    or "\n" in value:
                return False
        elif field.startswith("distinct_"):
            if isinstance(value, bool) or value not in (1, 2, 3):
                return False
        elif value not in ALLOWED[field]:
            return False
    return True


def load_key(trial: Path, doc: dict) -> Tuple[Optional[Dict[str, Dict[str, str]]], Optional[str]]:
    """brief -> {set label: arm}, or the reason the key cannot be used."""
    blind = doc.get("blind")
    if not isinstance(blind, dict) or not blind.get("key"):
        return None, "key_missing"
    path = trial.parent / blind["key"]
    if not path.is_file():
        return None, "key_missing"
    data = path.read_bytes()
    if sha256_bytes(data) != blind.get("key_sha256"):
        return None, "key_changed"
    try:
        key = json.loads(data.decode("utf-8"))
        mapping = {}
        for brief in doc["briefs"]:
            entry = key["briefs"][brief["id"]]
            arms = {label: entry[label]["arm"] for label in SETS}
            if sorted(arms.values()) != sorted(ARMS):
                return None, "key_changed"
            mapping[brief["id"]] = arms
    except (ValueError, KeyError, TypeError, UnicodeDecodeError):
        return None, "key_changed"
    return mapping, None


def score(trial: Path, doc: dict) -> dict:
    reasons: List[str] = []
    split = {m: sum(1 for b in doc["briefs"] if b["medium"] == m) for m in MEDIA}
    if len(doc["briefs"]) != BRIEF_COUNT or any(v != PER_MEDIUM for v in split.values()):
        reasons.append("brief_count %d (need %d, %d per medium: %s)" % (
            len(doc["briefs"]), BRIEF_COUNT, PER_MEDIUM,
            " ".join("%s=%d" % (m, split[m]) for m in MEDIA)))
    for brief in doc["briefs"]:
        reasons += ["missing_arm %s %s" % (brief["id"], arm)
                    for arm in ARMS if arm not in brief["arms"]]
    mapping, key_reason = load_key(trial, doc)
    if key_reason:
        reasons.append(key_reason)
    ratings = doc.get("ratings")
    rater = doc.get("rated_by")
    if not isinstance(ratings, dict) or not isinstance(rater, str) or not rater.strip():
        reasons.append("unrated")
        ratings = ratings if isinstance(ratings, dict) else {}
    else:
        reasons += ["unrated %s" % b["id"] for b in doc["briefs"]
                    if not valid_rating(ratings.get(b["id"]))]

    rows = []
    wins = axes_total = naive_total = yes = ui_yes = 0
    for brief in doc["briefs"]:
        rating = ratings.get(brief["id"])
        rated = valid_rating(rating)
        row = {"id": brief["id"], "medium": brief["medium"], "winner": None,
               "distinct_axes": None, "distinct_naive": None,
               "render_only": rating["render_only_enough"] if rated else None}
        if rated and rating["render_only_enough"] == "yes":
            yes += 1
            ui_yes += brief["medium"] == "ui"
        if rated and mapping is not None:
            arms = mapping[brief["id"]]
            label_of = {arm: label for label, arm in arms.items()}
            row["distinct_axes"] = rating["distinct_" + label_of["axes"]]
            row["distinct_naive"] = rating["distinct_" + label_of["naive"]]
            choice = rating["more_distinct"]
            row["winner"] = "tie" if choice == "tie" else arms[choice]
            wins += row["winner"] == "axes"
            axes_total += row["distinct_axes"]
            naive_total += row["distinct_naive"]
        rows.append(row)

    ui_count = sum(1 for b in doc["briefs"] if b["medium"] == "ui")
    render = {"yes": yes, "of": len(rows), "ui_yes": ui_yes, "ui_of": ui_count}
    if reasons:
        verdict = "unverifiable"
        codes: List[str] = []
        for reason in reasons:
            code = reason.split(" ", 1)[0]
            if code not in codes:
                codes.append(code)
        summary = "divergence-trial: unverifiable — %s" % ", ".join(codes)
        return {"verdict": verdict, "reasons": reasons, "briefs": rows, "render_only": render,
                "axes_wins": None, "distinct": None, "caveat": CAVEAT, "blinding": BLINDING,
                "summary": summary}
    keep = wins >= WINS_NEEDED and axes_total > naive_total
    verdict = "keep" if keep else "remove"
    summary = "divergence-trial: %s — axes won %d of %d, distinct %d vs %d" % (
        verdict, wins, len(rows), axes_total, naive_total)
    return {"verdict": verdict, "reasons": [], "briefs": rows, "render_only": render,
            "axes_wins": wins, "distinct": {"axes": axes_total, "naive": naive_total},
            "caveat": CAVEAT, "blinding": BLINDING, "summary": summary}


def dash(value: object) -> str:
    return "-" if value is None else str(value)


def cmd_report(args: argparse.Namespace) -> int:
    trial = Path(args.trial)
    report = score(trial, load_trial(trial))
    if args.json:
        print(json.dumps(report, sort_keys=True, ensure_ascii=False))
        return 0
    print(report["verdict"])
    for reason in report["reasons"]:
        print("reason: %s" % reason)
    for row in report["briefs"]:
        print("brief: %s medium=%s winner=%s distinct axes=%s naive=%s render_only=%s" % (
            row["id"], row["medium"], dash(row["winner"]), dash(row["distinct_axes"]),
            dash(row["distinct_naive"]), dash(row["render_only"])))
    render = report["render_only"]
    print("render-only: yes on %d of %d briefs (ui %d of %d)" % (
        render["yes"], render["of"], render["ui_yes"], render["ui_of"]))
    print(report["caveat"])
    print(report["blinding"])
    print(report["summary"])
    return 0


# --- CLI --------------------------------------------------------------------


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="divergence-trial.py", description=__doc__,
        formatter_class=argparse.RawDescriptionHelpFormatter)
    sub = parser.add_subparsers(dest="action")
    sub.required = True

    p = sub.add_parser("init", help="write a divergence-trial-v1 skeleton from six briefs")
    p.add_argument("--briefs", required=True)
    p.add_argument("--out", required=True)
    p.add_argument("--force", action="store_true")
    p.set_defaults(func=cmd_init)

    p = sub.add_parser("record", help="record one arm's drafts for one brief")
    p.add_argument("--trial", required=True)
    p.add_argument("--brief", required=True)
    p.add_argument("--arm", required=True, choices=ARMS)
    p.add_argument("--drafts", required=True)
    p.set_defaults(func=cmd_record)

    p = sub.add_parser("blind", help="write the blinded rating sheet and key.json")
    p.add_argument("--trial", required=True)
    p.add_argument("--sheet", required=True)
    p.add_argument("--seed", type=int, default=None)
    p.set_defaults(func=cmd_blind)

    p = sub.add_parser("rate", help="store the filled sheet's ratings by set label")
    p.add_argument("--trial", required=True)
    p.add_argument("--sheet", required=True)
    p.add_argument("--rated-by", required=True)
    p.set_defaults(func=cmd_rate)

    p = sub.add_parser("report", help="score the trial: keep, remove, or unverifiable")
    p.add_argument("--trial", required=True)
    p.add_argument("--json", action="store_true")
    p.set_defaults(func=cmd_report)
    return parser


def main(argv: Optional[List[str]] = None) -> int:
    parser = build_parser()
    try:
        args = parser.parse_args(argv)
    except SystemExit as exc:
        if exc.code in (0, None):
            return 0
        print("divergence-trial: refused — usage error", file=sys.stderr)
        return 2
    try:
        return args.func(args)
    except OSError as exc:
        refusal = Refusal(["io_error %s" % exc])
    except Refusal as exc:
        refusal = exc
    for reason in refusal.reasons:
        print("reason: %s" % reason, file=sys.stderr)
    print("divergence-trial: refused — %s" % refusal.summary, file=sys.stderr)
    return 2


if __name__ == "__main__":
    sys.exit(main())
