#!/usr/bin/env python3
"""Static asserter for the git-notes audit channel (spec: git-notes-audit-channel).

Emits PASS/FAIL TSV lines consumed by scripts/eval.sh check_git_notes_audit.
Unlike the fixture-based reducers, this channel has no runtime helper — the
deliverables are product-source markdown + install.sh — so the scenarios assert
the durable audit contract directly against the shipped files:

  - ship.md / release.md attach to refs/notes/writ (never refs/notes/commits)
  - both use `git notes --ref=writ add -f -F` and are strictly non-blocking
  - both honor the writ.auditNotes opt-out
  - ship.md attaches to the surviving (landed) commit and has a nil-WWB fallback
  - install.sh guards refspec config behind the writ.auditNotes marker,
    idempotently, and removes Writ-added refspecs on opt-out
  - status.md surfaces the read line; the format doc + ADR-017 define the contract
"""

from __future__ import annotations

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
passed = 0
failed = 0


def emit(name: str, ok: bool, detail: object = "") -> None:
    global passed, failed
    if ok:
        passed += 1
        print(f"PASS\t{name}")
    else:
        failed += 1
        safe = str(detail).replace("\n", "\\n").replace("\t", " ")
        print(f"FAIL\t{name}\t{safe}")


def read(rel: str) -> str:
    path = ROOT / rel
    try:
        return path.read_text(encoding="utf-8")
    except OSError:
        return ""


def has_all(text: str, *needles: str) -> bool:
    return all(n in text for n in needles)


def has_any(text: str, *needles: str) -> bool:
    return any(n in text for n in needles)


def scenario_ship() -> None:
    ship = read("commands/ship.md")
    emit("ship-references-writ-ref", "refs/notes/writ" in ship,
         "ship.md must reference refs/notes/writ")
    emit("ship-uses-notes-add-command",
         "git notes --ref=writ add -f -F" in ship,
         "ship.md must use `git notes --ref=writ add -f -F`")
    emit("ship-non-blocking",
         has_any(ship, "never fails the ship", "non-blocking", "audit note not attached"),
         "ship.md must state the audit step is non-blocking")
    emit("ship-honors-opt-out", "writ.auditNotes" in ship,
         "ship.md must honor the writ.auditNotes opt-out")
    emit("ship-attaches-to-landed-commit",
         has_all(ship, "landed") and has_any(ship, "surviving", "squash"),
         "ship.md must attach to the surviving/landed commit")
    emit("ship-nil-wwb-fallback",
         has_any(ship, "minimal digest", "Fallback"),
         "ship.md must document the nil-WWB minimal-digest fallback")
    emit("ship-never-default-ref",
         "refs/notes/commits" in ship and has_any(ship, "Never", "never"),
         "ship.md must forbid writing to refs/notes/commits")


def scenario_release() -> None:
    rel = read("commands/release.md")
    emit("release-references-writ-ref", "refs/notes/writ" in rel,
         "release.md must reference refs/notes/writ")
    emit("release-uses-notes-add-command",
         "git notes --ref=writ add -f -F" in rel,
         "release.md must use `git notes --ref=writ add -f -F`")
    emit("release-non-blocking",
         has_any(rel, "never fails the release", "non-blocking", "audit note not attached"),
         "release.md must state the rollup step is non-blocking")
    emit("release-honors-opt-out", "writ.auditNotes" in rel,
         "release.md must honor the writ.auditNotes opt-out")
    emit("release-rollup-on-tag-target",
         has_all(rel, "rollup") and has_any(rel, "tag", "TAG_TARGET_SHA"),
         "release.md must attach the version rollup to the tag target")


def scenario_install() -> None:
    inst = read("scripts/install.sh")
    emit("install-guards-behind-opt-out", "writ.auditNotes" in inst,
         "install.sh must gate refspec config behind writ.auditNotes")
    emit("install-fetch-refspec",
         "+refs/notes/writ:refs/notes/writ" in inst,
         "install.sh must configure the refs/notes/writ fetch refspec")
    emit("install-push-refspec", "refs/notes/writ" in inst,
         "install.sh must configure the refs/notes/writ push refspec")
    emit("install-idempotent",
         has_all(inst, "--get-all", "grep -Fxq"),
         "install.sh must grep existing refspecs before adding (idempotent)")
    emit("install-opt-out-removes-refspecs", "--unset-all" in inst,
         "install.sh must remove Writ-added refspecs on opt-out (no residue)")


def scenario_read_surface() -> None:
    status = read("commands/status.md")
    emit("status-audit-pointer-line",
         has_all(status, "Last audit note:", "--notes=writ"),
         "status.md must surface the last-audit-note pointer line")


def scenario_contract_docs() -> None:
    fmt = read(".writ/docs/git-notes-audit-format.md")
    emit("format-doc-exists", bool(fmt),
         ".writ/docs/git-notes-audit-format.md must exist")
    emit("format-doc-spec-digest", "Writ Audit Digest (spec)" in fmt,
         "format doc must define the spec-level digest schema")
    emit("format-doc-version-rollup", "Writ Release Audit" in fmt,
         "format doc must define the version rollup schema")
    emit("format-doc-sync-and-opt-out",
         has_all(fmt, "refs/notes/writ", "writ.auditNotes"),
         "format doc must document the ref, sync, and opt-out")

    adr = read(".writ/decision-records/adr-017-git-notes-audit-channel.md")
    emit("adr-017-exists", bool(adr),
         "ADR-017 must exist")
    emit("adr-017-squash-survival",
         has_any(adr, "squash-survival", "surviving", "squash-merge"),
         "ADR-017 must record the squash-survival rationale")
    emit("adr-017-audit-only",
         has_all(adr, "audit-only") and has_any(adr, "chain-of-thought", "transcripts"),
         "ADR-017 must record the audit-only content constraint")

    wwb = read(".writ/docs/what-was-built-format.md")
    emit("wwb-cross-links-adr-017", "adr-017" in wwb,
         "WWB format doc must reference ADR-017 for the boundary")


def main() -> int:
    scenario_ship()
    scenario_release()
    scenario_install()
    scenario_read_surface()
    scenario_contract_docs()
    return 0 if failed == 0 else 1


if __name__ == "__main__":
    sys.exit(main())
