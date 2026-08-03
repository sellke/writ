#!/usr/bin/env python3
"""Fixture scenarios for the deterministic context-hint assembler (Story 2).

Emits PASS/FAIL TSV lines consumed by scripts/eval.sh check_story_context.
Every scenario builds a disposable spec tree in a temp directory and
exercises scripts/story-context.py end to end via subprocess, asserting the
contract documented in .writ/docs/context-hint-format.md and
sub-specs/technical-spec.md:

  - happy path            -> both reference forms resolve, all 4 categories
  - legacy absent hints   -> proceeds on spec-lite only, informational log
  - section absent        -> same as legacy (covered above)
  - category prefix typo  -> skip that line, warn, continue
  - malformed brackets    -> skip category, warn, continue
  - empty brackets []     -> skip category silently, no warning
  - missing referenced row -> skip that reference, warn, continue
  - technical-spec.md absent -> fall through to spec.md fallback
  - spec.md absent/unreadable -> warn, empty payload
  - duplicate Operation-name concatenation (Architecture Check Finding 1)
  - path traversal reference (`../`) degrades to missing-content, never leaks
  - byte-identical repeat runs
  - never raises: exit code is always 0 across every scenario above

Story 3 (2026-08-03-deterministic-story-substrate) adds budget-enforcement
scenarios:
  - over-budget truncation -> truncated: true, warning names actual + budget
  - exactly-at-threshold -> NOT truncated (strictly-greater comparison)
  - relevance-ordered retention -> higher-relevance categories survive whole
  - byte-identical repeat runs with a budget applied

Story 4 adds illustrative-only scenarios proving the *documented degrade
logic* in commands/implement-story.md's "Assembler-failure degradation"
table is internally sound against fake wrapper scripts (missing script,
non-zero exit, malformed stdout) — see the block above main() for why this
tests the algorithm's soundness, not story-context.py itself (which always
exits 0) and not runtime LLM compliance (not automatable).
"""

from __future__ import annotations

import json
import subprocess
import sys
import tempfile
from pathlib import Path


HELPER = Path(__file__).with_name("story-context.py")
passed = 0
failed = 0

DEFAULT_TECH_SPEC = (
    "# Technical Spec\n\n"
    "## Error & Rescue Map\n\n"
    "| Operation | What Can Fail | Planned Handling | Test Strategy |\n"
    "|---|---|---|---|\n"
    "| Create session | Redis unavailable | Retry once, then fail | Fixture |\n"
    "| Validate input | Missing field | 400 with field name | Fixture |\n\n"
    "## Shadow Paths\n\n"
    "| Flow | Happy Path | Nil Input | Empty Input | Upstream Error |\n"
    "|---|---|---|---|---|\n"
    "| User registration flow | Account created | N/A | Rejected | Retry |\n"
)

DEFAULT_SPEC_MD = (
    "# Spec: Example\n\n"
    "## \U0001F4CB Business Rules\n\n"
    "1. **One implementation per contract.** No duplicated parsers survive.\n\n"
    "## \U0001F3AF Experience Design\n\n"
    "### Entry Point\n\n"
    "No new user-invokable surface.\n\n"
    "### Error Experience\n\n"
    "| Situation | Behavior |\n"
    "|---|---|\n"
    "| Bad graph | Blocking. |\n"
)


def emit(name: str, ok: bool, detail: object = "") -> None:
    global passed, failed
    if ok:
        passed += 1
        print(f"PASS\t{name}")
    else:
        failed += 1
        safe = str(detail).replace("\n", "\\n").replace("\t", " ")
        print(f"FAIL\t{name}\t{safe}")


def run(*args: str) -> tuple[int, dict]:
    proc = subprocess.run(
        [sys.executable, str(HELPER), *args],
        capture_output=True,
        text=True,
    )
    try:
        payload = json.loads(proc.stdout or "{}")
    except json.JSONDecodeError:
        payload = {"_raw": proc.stdout, "_err": proc.stderr}
    return proc.returncode, payload


def make_spec_tree(
    root: Path,
    spec_id: str,
    *,
    spec_md: str | None = DEFAULT_SPEC_MD,
    technical_spec_md: str | None = DEFAULT_TECH_SPEC,
    hints: str | None,
) -> Path:
    folder = root / spec_id
    folder.mkdir(parents=True, exist_ok=True)
    if spec_md is not None:
        (folder / "spec.md").write_text(spec_md, encoding="utf-8")
    if technical_spec_md is not None:
        sub = folder / "sub-specs"
        sub.mkdir(parents=True, exist_ok=True)
        (sub / "technical-spec.md").write_text(technical_spec_md, encoding="utf-8")
    stories = folder / "user-stories"
    stories.mkdir(parents=True, exist_ok=True)
    lines = ["# Story 1: Example", "", "## User Story", "", "Body."]
    if hints is not None:
        lines += ["", "## Context for Agents", "", hints]
    path = stories / "story-1-example.md"
    path.write_text("\n".join(lines) + "\n", encoding="utf-8")
    return path


def scenario_happy_path_both_reference_forms() -> None:
    with tempfile.TemporaryDirectory() as tmp:
        root = Path(tmp)
        hints = (
            "- **Error map rows:** [Create session, Validate input]\n"
            "- **Shadow paths:** [User registration flow]\n"
            "- **Business rules:** [One implementation per contract]\n"
            "- **Experience:** `spec.md \u2192 ## \U0001F3AF Experience Design \u2192 ### Entry Point`\n"
        )
        story = make_spec_tree(root, "s-happy", hints=hints)
        code, payload = run("assemble", "--story", str(story))
        fetched = payload.get("fetched_context", {})
        emit("happy-path-exits-zero", code == 0, payload)
        emit("happy-path-no-warnings", payload.get("warnings") == [], payload)
        emit("happy-path-bracket-form-resolves",
             "Create session" in fetched.get("error_map_rows", ""), fetched)
        emit("happy-path-extended-form-resolves",
             "No new user-invokable surface" in fetched.get("experience", ""), fetched)
        emit("happy-path-all-four-categories-populated",
             set(fetched) == {"error_map_rows", "shadow_paths", "business_rules", "experience"}, fetched)
        emit("happy-path-truncated-always-false", payload.get("truncated") is False, payload)
        emit("happy-path-bytes-total-matches-sum",
             payload.get("bytes", {}).get("total") ==
             sum(v for k, v in payload.get("bytes", {}).items() if k != "total"),
             payload)


def scenario_legacy_absent_hints() -> None:
    with tempfile.TemporaryDirectory() as tmp:
        root = Path(tmp)
        story = make_spec_tree(root, "s-legacy", hints=None)
        code, payload = run("assemble", "--story", str(story))
        emit("legacy-absent-hints-exits-zero", code == 0, payload)
        emit("legacy-absent-hints-empty-payload", payload.get("fetched_context") == {}, payload)
        emit("legacy-absent-hints-informational-log",
             len(payload.get("warnings", [])) == 1
             and "No \"## Context for Agents\" section" in payload["warnings"][0],
             payload)


def scenario_category_prefix_typo() -> None:
    with tempfile.TemporaryDirectory() as tmp:
        root = Path(tmp)
        hints = "- **Eror map rows:** [Create session]\n- **Business rules:** [One implementation per contract]\n"
        story = make_spec_tree(root, "s-typo", hints=hints)
        code, payload = run("assemble", "--story", str(story))
        emit("typo-category-exits-zero", code == 0, payload)
        emit("typo-category-skips-and-warns",
             any("Unrecognized context hint category" in w for w in payload.get("warnings", [])), payload)
        emit("typo-category-other-categories-still-resolve",
             "business_rules" in payload.get("fetched_context", {}), payload)


def scenario_malformed_brackets() -> None:
    with tempfile.TemporaryDirectory() as tmp:
        root = Path(tmp)
        hints = (
            "- **Error map rows:** [Create session, Validate input\n"
            "- **Business rules:** [One implementation per contract]\n"
        )
        story = make_spec_tree(root, "s-malformed", hints=hints)
        code, payload = run("assemble", "--story", str(story))
        emit("malformed-brackets-exits-zero", code == 0, payload)
        emit("malformed-brackets-skips-and-warns",
             any("Malformed context hint category" in w for w in payload.get("warnings", [])), payload)
        emit("malformed-brackets-other-categories-still-resolve",
             "business_rules" in payload.get("fetched_context", {}), payload)


def scenario_empty_brackets() -> None:
    with tempfile.TemporaryDirectory() as tmp:
        root = Path(tmp)
        hints = "- **Error map rows:** []\n- **Business rules:** [One implementation per contract]\n"
        story = make_spec_tree(root, "s-empty", hints=hints)
        code, payload = run("assemble", "--story", str(story))
        emit("empty-brackets-exits-zero", code == 0, payload)
        emit("empty-brackets-no-warning", payload.get("warnings") == [], payload)
        emit("empty-brackets-category-absent-from-payload",
             "error_map_rows" not in payload.get("fetched_context", {}), payload)


def scenario_missing_referenced_row() -> None:
    with tempfile.TemporaryDirectory() as tmp:
        root = Path(tmp)
        hints = "- **Error map rows:** [Nonexistent Operation]\n"
        story = make_spec_tree(root, "s-missingref", hints=hints)
        code, payload = run("assemble", "--story", str(story))
        emit("missing-referenced-row-exits-zero", code == 0, payload)
        emit("missing-referenced-row-warns",
             any('"Nonexistent Operation"' in w for w in payload.get("warnings", [])), payload)
        emit("missing-referenced-row-empty-payload", payload.get("fetched_context") == {}, payload)


def scenario_technical_spec_absent_fallback() -> None:
    with tempfile.TemporaryDirectory() as tmp:
        root = Path(tmp)
        hints = "- **Error map rows:** [Create session]\n"
        story = make_spec_tree(root, "s-notech", technical_spec_md=None, hints=hints)
        code, payload = run("assemble", "--story", str(story))
        emit("technical-spec-absent-exits-zero", code == 0, payload)
        emit("technical-spec-absent-falls-back-silently", payload.get("warnings") == [], payload)
        emit("technical-spec-absent-fallback-content-delivered",
             "Bad graph" in payload.get("fetched_context", {}).get("error_map_rows", ""), payload)


def scenario_spec_md_absent() -> None:
    with tempfile.TemporaryDirectory() as tmp:
        root = Path(tmp)
        hints = "- **Error map rows:** [Create session]\n"
        story = make_spec_tree(root, "s-nospec", spec_md=None, hints=hints)
        code, payload = run("assemble", "--story", str(story))
        emit("spec-md-absent-exits-zero", code == 0, payload)
        emit("spec-md-absent-empty-payload", payload.get("fetched_context") == {}, payload)
        emit("spec-md-absent-warns",
             len(payload.get("warnings", [])) == 1
             and "spec.md absent or unreadable" in payload["warnings"][0],
             payload)


def scenario_duplicate_operation_name_concatenation() -> None:
    """Architecture Check Finding 1: a bracketed reference that matches
    multiple Error & Rescue Map rows sharing one Operation name concatenates
    ALL of them, table order, deduplicated, with NO warning — mirroring the
    real "Parse hint category" (3 rows) / "Read source spec" (2 rows) rows
    that already exist in this spec's own technical-spec.md."""
    tech = (
        "## Error & Rescue Map\n\n"
        "| Operation | What Can Fail | Planned Handling | Test Strategy |\n"
        "|---|---|---|---|\n"
        "| Read source spec | `technical-spec.md` absent | Fall through to spec.md fallback | Fixture 1 |\n"
        "| Read source spec | `spec.md` absent or unreadable | Warn, return empty payload | Fixture 2 |\n"
    )
    with tempfile.TemporaryDirectory() as tmp:
        root = Path(tmp)
        hints = "- **Error map rows:** [Read source spec]\n"
        story = make_spec_tree(root, "s-dupop", technical_spec_md=tech, hints=hints)
        code, payload = run("assemble", "--story", str(story))
        content = payload.get("fetched_context", {}).get("error_map_rows", "")
        emit("duplicate-operation-name-exits-zero", code == 0, payload)
        emit("duplicate-operation-name-no-warning", payload.get("warnings") == [], payload)
        emit("duplicate-operation-name-concatenates-both-rows",
             "Fall through to spec.md fallback" in content and "Warn, return empty payload" in content,
             content)
        emit("duplicate-operation-name-preserves-table-order",
             content.index("Fall through to spec.md fallback") < content.index("Warn, return empty payload"),
             content)


def scenario_path_traversal_reference_degrades_safely() -> None:
    """Security regression: an extended reference that escapes spec_folder
    (`../` relative traversal) must degrade exactly like a missing file —
    warn-and-skip, never disclose the escaped file's content, never raise."""
    with tempfile.TemporaryDirectory() as tmp:
        root = Path(tmp)
        secret = root / "secret.md"
        secret.write_text("## Secret\n\nTop secret content that must never leak.\n", encoding="utf-8")
        hints = "- **Experience:** `../secret.md \u2192 ## Secret`\n"
        story = make_spec_tree(root, "s-traversal", hints=hints)
        code, payload = run("assemble", "--story", str(story))
        fetched = payload.get("fetched_context", {})
        warnings = payload.get("warnings", [])
        emit("path-traversal-exits-zero", code == 0, payload)
        emit("path-traversal-does-not-leak-content",
             "Top secret content" not in json.dumps(payload), payload)
        emit("path-traversal-degrades-to-missing-content-warning",
             "experience" not in fetched
             and any('missing content: "../secret.md \u2192 ## Secret"' in w for w in warnings),
             payload)


def scenario_byte_identical_repeat_runs() -> None:
    with tempfile.TemporaryDirectory() as tmp:
        root = Path(tmp)
        hints = (
            "- **Error map rows:** [Create session, Validate input]\n"
            "- **Shadow paths:** [User registration flow]\n"
            "- **Business rules:** [One implementation per contract]\n"
            "- **Experience:** [Entry Point]\n"
        )
        story = make_spec_tree(root, "s-repeat", hints=hints)
        first_code, first_stdout_payload = run("assemble", "--story", str(story))
        second_code, second_stdout_payload = run("assemble", "--story", str(story))
        emit("repeated-runs-byte-identical",
             first_code == second_code
             and json.dumps(first_stdout_payload, sort_keys=False)
             == json.dumps(second_stdout_payload, sort_keys=False),
             (first_stdout_payload, second_stdout_payload))


def scenario_never_raises() -> None:
    """Assembler exit code is 0 across every degradation branch exercised
    above — collected here as one explicit cross-scenario assertion."""
    with tempfile.TemporaryDirectory() as tmp:
        root = Path(tmp)
        code, _ = run("assemble", "--story", str(root / "does-not-exist.md"))
        emit("missing-story-file-never-raises", code == 0, "")


def scenario_undecodable_bytes_never_raises() -> None:
    """Invalid UTF-8 raises UnicodeDecodeError inside assemble() itself — a
    distinct failure mode from a missing/unreadable file (OSError, already
    covered above). main()'s outer catch-all must degrade this too, never
    propagate a non-zero exit."""
    with tempfile.TemporaryDirectory() as tmp:
        root = Path(tmp)
        story = root / "binary.md"
        story.write_bytes(b"\xff\xfe\x00\x01## Context for Agents\n[broken\x80")
        code, payload = run("assemble", "--story", str(story))
        emit("undecodable-bytes-exits-zero", code == 0, payload)
        emit("undecodable-bytes-internal-error-warning",
             len(payload.get("warnings", [])) == 1
             and "story-context.py internal error" in payload["warnings"][0],
             payload)


def _four_category_hints() -> str:
    return (
        "- **Error map rows:** [Create session, Validate input]\n"
        "- **Shadow paths:** [User registration flow]\n"
        "- **Business rules:** [One implementation per contract]\n"
        "- **Experience:** [Entry Point]\n"
    )


def scenario_over_budget_truncates_with_warning() -> None:
    """Story 3, AC2: strictly exceeding the budget truncates, sets
    truncated: true, and warns naming actual and budget bytes."""
    with tempfile.TemporaryDirectory() as tmp:
        root = Path(tmp)
        story = make_spec_tree(root, "s-overbudget", hints=_four_category_hints())
        _, unbudgeted = run("assemble", "--story", str(story))
        actual_total = unbudgeted.get("bytes", {}).get("total", 0)
        budget = actual_total - 1

        code, payload = run("assemble", "--story", str(story), "--budget-bytes", str(budget))
        warnings = payload.get("warnings", [])
        emit("over-budget-exits-zero", code == 0, payload)
        emit("over-budget-truncated-flag-true", payload.get("truncated") is True, payload)
        emit("over-budget-bytes-total-equals-budget", payload.get("bytes", {}).get("total") == budget, payload)
        emit("over-budget-warning-names-actual-and-budget",
             any(str(actual_total) in w and str(budget) in w and "fetched_context truncated" in w for w in warnings),
             warnings)


def scenario_exactly_at_threshold_not_truncated() -> None:
    """Story 3, AC3 / Architecture Check Finding 6: total == budget must NOT
    truncate — the comparison is strictly-greater-than, tested in isolation
    from the over-budget case above."""
    with tempfile.TemporaryDirectory() as tmp:
        root = Path(tmp)
        story = make_spec_tree(root, "s-exactbudget", hints=_four_category_hints())
        _, unbudgeted = run("assemble", "--story", str(story))
        exact_budget = unbudgeted.get("bytes", {}).get("total", 0)

        code, payload = run("assemble", "--story", str(story), "--budget-bytes", str(exact_budget))
        emit("exact-threshold-exits-zero", code == 0, payload)
        emit("exact-threshold-not-truncated", payload.get("truncated") is False, payload)
        emit("exact-threshold-fetched-context-unchanged",
             payload.get("fetched_context") == unbudgeted.get("fetched_context"), payload)
        emit("exact-threshold-no-truncation-warning",
             not any("fetched_context truncated" in w for w in payload.get("warnings", [])), payload)


def scenario_relevance_ordered_retention() -> None:
    """Architecture Check Finding 4: CATEGORY_ORDER doubles as truncation
    priority. A budget covering exactly the first three categories keeps
    them whole and drops the lowest-relevance (experience) entirely."""
    with tempfile.TemporaryDirectory() as tmp:
        root = Path(tmp)
        story = make_spec_tree(root, "s-relevance", hints=_four_category_hints())
        _, unbudgeted = run("assemble", "--story", str(story))
        fetched = unbudgeted.get("fetched_context", {})
        by = unbudgeted.get("bytes", {})
        budget = by.get("error_map_rows", 0) + by.get("shadow_paths", 0) + by.get("business_rules", 0)

        code, payload = run("assemble", "--story", str(story), "--budget-bytes", str(budget))
        result_fetched = payload.get("fetched_context", {})
        emit("relevance-order-exits-zero", code == 0, payload)
        emit("relevance-order-truncated-flag-true", payload.get("truncated") is True, payload)
        emit("relevance-order-higher-relevance-kept-whole",
             result_fetched.get("error_map_rows") == fetched.get("error_map_rows")
             and result_fetched.get("shadow_paths") == fetched.get("shadow_paths")
             and result_fetched.get("business_rules") == fetched.get("business_rules"),
             result_fetched)
        emit("relevance-order-lowest-relevance-dropped-entirely",
             "experience" not in result_fetched, result_fetched)


def scenario_byte_identical_repeat_runs_with_budget() -> None:
    """Story 3, AC5 / Business Rule 5: determinism holds under enforcement."""
    with tempfile.TemporaryDirectory() as tmp:
        root = Path(tmp)
        story = make_spec_tree(root, "s-repeatbudget", hints=_four_category_hints())
        _, unbudgeted = run("assemble", "--story", str(story))
        budget = unbudgeted.get("bytes", {}).get("total", 0) // 2

        first_code, first_payload = run("assemble", "--story", str(story), "--budget-bytes", str(budget))
        second_code, second_payload = run("assemble", "--story", str(story), "--budget-bytes", str(budget))
        emit("repeated-runs-with-budget-byte-identical",
             first_code == second_code
             and json.dumps(first_payload, sort_keys=False) == json.dumps(second_payload, sort_keys=False),
             (first_payload, second_payload))


# --- Story 4, Task 4.5: illustrative-only proof of the *documented degrade
# logic*, not of story-context.py itself (which always exits 0 and can't be
# made to fail these ways for real — see main()'s catch-all). This models
# the exact three-row table in commands/implement-story.md's "Assembler-
# failure degradation" against small fake wrapper scripts, one per failure
# mode, to prove the algorithm is internally sound if an orchestrator
# implements it literally. It does not and cannot prove an LLM orchestrator
# will follow the prose at runtime — that isn't automatable.
def _degrade_on_assembler_invocation(script_path: Path, *args: str) -> dict:
    """Mirrors commands/implement-story.md's documented degrade table."""
    if not script_path.exists():
        return {"fetched_context": {}, "context_warnings": ["story-context.py not found — proceeding with spec-lite only"]}
    proc = subprocess.run([sys.executable, str(script_path), *args], capture_output=True, text=True)
    if proc.returncode != 0:
        return {"fetched_context": {}, "context_warnings": ["story-context.py exited non-zero — proceeding with spec-lite only"]}
    try:
        payload = json.loads(proc.stdout)
        if "fetched_context" not in payload or "warnings" not in payload:
            raise ValueError("missing required keys")
    except (json.JSONDecodeError, ValueError):
        return {"fetched_context": {}, "context_warnings": ["story-context.py produced unparseable output — proceeding with spec-lite only"]}
    return {"fetched_context": payload["fetched_context"], "context_warnings": payload["warnings"]}


def scenario_documented_degrade_handles_missing_script() -> None:
    with tempfile.TemporaryDirectory() as tmp:
        fake = Path(tmp) / "does-not-exist.py"
        result = _degrade_on_assembler_invocation(fake, "assemble", "--story", "irrelevant.md")
        emit("degrade-missing-script-empty-fetched-context", result["fetched_context"] == {}, result)
        emit("degrade-missing-script-names-failure-mode",
             any("not found" in w for w in result["context_warnings"]), result)


def scenario_documented_degrade_handles_non_zero_exit() -> None:
    with tempfile.TemporaryDirectory() as tmp:
        fake = Path(tmp) / "fake-nonzero.py"
        fake.write_text("import sys\nsys.exit(1)\n", encoding="utf-8")
        result = _degrade_on_assembler_invocation(fake)
        emit("degrade-non-zero-exit-empty-fetched-context", result["fetched_context"] == {}, result)
        emit("degrade-non-zero-exit-names-failure-mode",
             any("exited non-zero" in w for w in result["context_warnings"]), result)


def scenario_documented_degrade_handles_malformed_stdout() -> None:
    with tempfile.TemporaryDirectory() as tmp:
        fake = Path(tmp) / "fake-malformed.py"
        fake.write_text("print('not json at all')\n", encoding="utf-8")
        result = _degrade_on_assembler_invocation(fake)
        emit("degrade-malformed-stdout-empty-fetched-context", result["fetched_context"] == {}, result)
        emit("degrade-malformed-stdout-names-failure-mode",
             any("unparseable" in w for w in result["context_warnings"]), result)


def main() -> int:
    scenario_happy_path_both_reference_forms()
    scenario_legacy_absent_hints()
    scenario_category_prefix_typo()
    scenario_malformed_brackets()
    scenario_empty_brackets()
    scenario_missing_referenced_row()
    scenario_technical_spec_absent_fallback()
    scenario_spec_md_absent()
    scenario_duplicate_operation_name_concatenation()
    scenario_path_traversal_reference_degrades_safely()
    scenario_byte_identical_repeat_runs()
    scenario_never_raises()
    scenario_undecodable_bytes_never_raises()
    scenario_over_budget_truncates_with_warning()
    scenario_exactly_at_threshold_not_truncated()
    scenario_relevance_ordered_retention()
    scenario_byte_identical_repeat_runs_with_budget()
    scenario_documented_degrade_handles_missing_script()
    scenario_documented_degrade_handles_non_zero_exit()
    scenario_documented_degrade_handles_malformed_stdout()
    return 0 if failed == 0 else 1


if __name__ == "__main__":
    sys.exit(main())
