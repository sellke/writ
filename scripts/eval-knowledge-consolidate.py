#!/usr/bin/env python3
"""Scenarios for knowledge ledger consolidation (Phase 7).

Emits PASS/FAIL TSV lines consumed by scripts/eval.sh check_knowledge_consolidate.
Exercises scripts/knowledge-consolidate.py to prove the locked contract:

  - dup merge proposed        : a genuine duplicate pair yields one canonical + replaces
  - distinct not merged       : below-threshold entries are left alone
  - contradiction surfaced    : conflicting same-subject entries flagged, not merged
  - unrelated not contradiction: disjoint-subject entries are not flagged
  - stale flagged             : dangling related_artifacts flagged; still-referenced is not
  - non-destructive default   : dry-run writes no file (ledger byte-identical)
  - lineage preserved         : apply writes bidirectional replaces / superseded_by
  - clean-ledger no-op        : a clean ledger changes no file and reports noop
  - malformed skipped         : a malformed entry is skipped with a reason, never rewritten
"""

from __future__ import annotations

import json
import subprocess
import sys
import tempfile
from pathlib import Path

REDUCER = Path(__file__).with_name("knowledge-consolidate.py")
passed = 0
failed = 0


def emit(name, ok, detail=""):
    global passed, failed
    if ok:
        passed += 1
        print("PASS\t%s" % name)
    else:
        failed += 1
        safe = str(detail).replace("\n", "\\n").replace("\t", " ")
        print("FAIL\t%s\t%s" % (name, safe))


def run(knowledge_dir, repo_root, apply=False):
    args = [sys.executable, str(REDUCER), "--knowledge-dir", str(knowledge_dir),
            "--repo-root", str(repo_root), "--json"]
    if apply:
        args.append("--apply")
    proc = subprocess.run(args, capture_output=True, text=True)
    try:
        payload = json.loads(proc.stdout or "{}")
    except json.JSONDecodeError:
        payload = {"_raw": proc.stdout, "_err": proc.stderr}
    return proc.returncode, payload


def write_entry(kd, category, slug, title, tldr, tags,
                related=None, context="Captured for testing.", detail="Body detail.",
                created="2026-01-01", extra_fm=""):
    cat_dir = kd / category
    cat_dir.mkdir(parents=True, exist_ok=True)
    if related is None:
        related_block = "related_artifacts: []\n"
    else:
        related_block = "related_artifacts:\n" + "".join("  - %s\n" % r for r in related)
    text = (
        "---\n"
        "category: %s\n"
        "tags: [%s]\n"
        "created: %s\n"
        "%s"
        "%s"
        "---\n\n"
        "# %s\n\n"
        "## TL;DR\n\n%s\n\n"
        "## Context\n\n- %s\n\n"
        "## Detail\n\n%s\n"
    ) % (category, ", ".join(tags), created, related_block, extra_fm,
         title, tldr, context, detail)
    path = cat_dir / ("%s.md" % slug)
    path.write_text(text, encoding="utf-8")
    return path


def snapshot(kd):
    return {str(p): p.read_bytes() for p in sorted(kd.rglob("*.md"))}


def main():
    # --- duplicate merge proposed + non-destructive default ------------------
    with tempfile.TemporaryDirectory() as t:
        tmp = Path(t)
        kd = tmp / "knowledge"
        write_entry(
            kd, "lessons", "2026-01-01-retry-quarantine-a",
            "Bounded Retries Keep Failures Recoverable",
            "Bounded retries plus quarantine keep partial failures recoverable "
            "without contaminating the shared phase branch.",
            ["retries", "quarantine", "phase"],
            detail="Bounded retries plus quarantine keep partial failures recoverable "
                   "without contaminating the shared phase branch during phase execution.")
        write_entry(
            kd, "lessons", "2026-01-01-retry-quarantine-b",
            "Retries And Quarantine For Recoverable Failures",
            "Bounded retries and quarantine keep partial failures recoverable "
            "without contaminating the shared phase branch.",
            ["retries", "quarantine", "phase"],
            detail="Bounded retries and quarantine keep partial failures recoverable "
                   "without contaminating the shared phase branch during phase execution.")
        # a genuinely distinct entry that must NOT be pulled into the merge
        write_entry(
            kd, "lessons", "2026-01-01-distinct-topic",
            "Documentation Belongs Beside Code",
            "Keep contributor documentation adjacent to the module it explains "
            "so reviewers discover it during review.",
            ["docs", "review"],
            detail="Keep contributor documentation adjacent to the module it explains.")

        before = snapshot(kd)
        code, out = run(kd, tmp)
        after = snapshot(kd)

        merges = out.get("merges", [])
        dup = next((m for m in merges if set(m["members"]) ==
                    {"2026-01-01-retry-quarantine-a", "2026-01-01-retry-quarantine-b"}), None)
        emit("dup-merge-proposed",
             code == 0 and dup is not None and len(dup["replaces"]) == 1, out)
        emit("distinct-not-merged",
             all("2026-01-01-distinct-topic" not in m["members"] for m in merges), merges)
        emit("non-destructive-default",
             before == after and out.get("mode") == "dry-run", "ledger changed in dry-run")

        # --- lineage preserved on apply --------------------------------------
        code_a, out_a = run(kd, tmp, apply=True)
        canonical_slug = dup["canonical"] if dup else ""
        superseded_slug = dup["replaces"][0] if dup and dup["replaces"] else ""
        canon_text = (kd / "lessons" / ("%s.md" % canonical_slug)).read_text(encoding="utf-8") \
            if canonical_slug else ""
        tomb_text = (kd / "lessons" / ("%s.md" % superseded_slug)).read_text(encoding="utf-8") \
            if superseded_slug else ""
        emit("lineage-preserved",
             out_a.get("mode") == "apply"
             and "replaces:" in canon_text
             and superseded_slug in canon_text
             and ("superseded_by: %s" % canonical_slug) in tomb_text,
             {"canon": canon_text[:200], "tomb": tomb_text[:200]})

    # --- contradiction surfaced + unrelated not flagged ----------------------
    with tempfile.TemporaryDirectory() as t:
        tmp = Path(t)
        kd = tmp / "knowledge"
        write_entry(
            kd, "conventions", "2026-01-01-indent-tabs",
            "Indentation Uses Tabs",
            "Always use tabs for indentation in this codebase.",
            ["indentation", "style"],
            context="Editor defaults were inconsistent.",
            detail="Configure the editor to insert a real tab character on indent.")
        write_entry(
            kd, "conventions", "2026-01-01-indent-spaces",
            "Indentation Uses Spaces",
            "Never use tabs for indentation in this codebase; use spaces.",
            ["indentation", "style"],
            context="A linter enforced spaces.",
            detail="Configure the editor to expand indentation into space characters.")
        # unrelated pair — different subject, must not be a contradiction
        write_entry(
            kd, "conventions", "2026-01-01-commit-messages",
            "Commit Messages Use Imperative Mood",
            "Write commit subject lines in the imperative mood under fifty characters.",
            ["git", "commits"])

        code, out = run(kd, tmp)
        contradictions = out.get("contradictions", [])
        indent = next((c for c in contradictions if set(c["pair"]) ==
                       {"2026-01-01-indent-tabs", "2026-01-01-indent-spaces"}), None)
        emit("contradiction-surfaced", code == 0 and indent is not None, out)
        emit("contradiction-not-merged",
             all(set(m["members"]) != {"2026-01-01-indent-tabs", "2026-01-01-indent-spaces"}
                 for m in out.get("merges", [])), out.get("merges"))
        emit("unrelated-not-contradiction",
             all("2026-01-01-commit-messages" not in c["pair"] for c in contradictions),
             contradictions)

    # --- stale flagged (dangling artifacts) vs still-referenced --------------
    with tempfile.TemporaryDirectory() as t:
        tmp = Path(t)
        kd = tmp / "knowledge"
        (tmp / "present.md").write_text("real artifact\n", encoding="utf-8")
        write_entry(
            kd, "decisions", "2026-01-01-dangling",
            "Decision With Vanished Artifacts",
            "A decision whose supporting files were all deleted.",
            ["cleanup"],
            related=["gone/removed-one.md", "gone/removed-two.md"])
        write_entry(
            kd, "decisions", "2026-01-01-referenced",
            "Decision Still Referenced",
            "A decision whose supporting file still exists on disk.",
            ["active"],
            related=["present.md"])

        code, out = run(kd, tmp)
        stale = out.get("stale", [])
        dangling = next((s for s in stale if s["slug"] == "2026-01-01-dangling"), None)
        emit("stale-flagged",
             code == 0 and dangling is not None
             and any("related_artifacts missing" in sig for sig in dangling["signals"]), out)
        emit("referenced-not-stale",
             all(s["slug"] != "2026-01-01-referenced" for s in stale), stale)

    # --- clean-ledger no-op --------------------------------------------------
    with tempfile.TemporaryDirectory() as t:
        tmp = Path(t)
        kd = tmp / "knowledge"
        write_entry(kd, "glossary", "reducer",
                    "Reducer", "A markdown-in markdown-out consolidation function.",
                    ["consolidation"])
        write_entry(kd, "lessons", "2026-01-01-only-lesson",
                    "A Solitary Lesson",
                    "One isolated lesson about spec sequencing with no peer entry.",
                    ["sequencing"])
        before = snapshot(kd)
        code, out = run(kd, tmp)
        after = snapshot(kd)
        emit("clean-ledger-noop",
             code == 0 and out.get("noop") is True
             and not out.get("merges") and not out.get("contradictions")
             and not out.get("stale") and before == after, out)

    # --- malformed entry skipped, never rewritten ---------------------------
    with tempfile.TemporaryDirectory() as t:
        tmp = Path(t)
        kd = tmp / "knowledge"
        (kd / "lessons").mkdir(parents=True)
        broken = kd / "lessons" / "2026-01-01-broken.md"
        broken.write_text("---\ncategory: lessons\ntags: [x]\n"
                          "# No closing fence and no TL;DR\n", encoding="utf-8")
        before = broken.read_bytes()
        code, out = run(kd, tmp)
        after = broken.read_bytes()
        skipped = out.get("skipped", [])
        emit("malformed-skipped",
             code == 0 and any(s["path"].endswith("2026-01-01-broken.md") and s["reason"]
                               for s in skipped) and before == after, out)

    return 0 if failed == 0 else 1


if __name__ == "__main__":
    sys.exit(main())
