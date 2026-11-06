#!/usr/bin/env python3
"""Tests for `/ship` opening a PR without asking, recording the verification
ledger, and `/ship --watch` (spec `2026-11-06-ship-watch-and-merge`).

Prose pins and filled-template tests over `commands/ship.md`. A filled
template runs against the real `scripts/verify-ledger.py` or
`scripts/jev-judge.py` in a temp git repo. No test touches GitHub or the
Writ checkout's `.writ/state/`.
"""

from __future__ import annotations

import importlib.util
import json
import os
import re
import subprocess
import sys
from pathlib import Path
from typing import List

import pytest


REPO_ROOT = Path(__file__).resolve().parents[2]
SHIP = REPO_ROOT / "commands" / "ship.md"
COMMAND_BYTE_BUDGET = 24960


def _load(name: str, rel: str):
    spec = importlib.util.spec_from_file_location(name, REPO_ROOT / rel)
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def read(rel: str) -> str:
    return (REPO_ROOT / rel).read_text(encoding="utf-8")


def ship() -> str:
    return SHIP.read_text(encoding="utf-8")


def section(text: str, heading: str) -> str:
    """From the line starting with `heading` to the next heading of the same or a
    higher level (fenced code skipped)."""
    lines = text.splitlines(keepends=True)
    level = len(heading) - len(heading.lstrip("#"))
    start = next(i for i, line in enumerate(lines) if line.startswith(heading))
    out = [lines[start]]
    fenced = False
    for line in lines[start + 1:]:
        if line.lstrip().startswith("```"):
            fenced = not fenced
        if not fenced:
            m = re.match(r"^(#{1,6}) ", line)
            if m and len(m.group(1)) <= level:
                break
        out.append(line)
    return "".join(out)


def flat(text: str) -> str:
    return " ".join(text.split())


def _git(repo: Path, *args: str) -> str:
    env = dict(os.environ, GIT_CONFIG_GLOBAL=os.devnull, GIT_CONFIG_NOSYSTEM="1")
    done = subprocess.run(["git", "-c", "user.name=t", "-c", "user.email=t@t",
                           "-c", "commit.gpgsign=false", *args],
                          cwd=str(repo), env=env, check=True, capture_output=True, text=True)
    return done.stdout.strip()


def _feature_repo(tmp_path: Path) -> Path:
    """main with one file and an origin/main ref; branch feat with one change."""
    repo = tmp_path / "repo"
    repo.mkdir()
    _git(repo, "init", "-q")
    _git(repo, "symbolic-ref", "HEAD", "refs/heads/main")
    (repo / "app.txt").write_text("one\ntwo\n", encoding="utf-8")
    _git(repo, "add", "app.txt")
    _git(repo, "commit", "-q", "-m", "base")
    _git(repo, "update-ref", "refs/remotes/origin/main", "HEAD")
    _git(repo, "checkout", "-q", "-b", "feat")
    (repo / "app.txt").write_text("one\nTWO\n", encoding="utf-8")
    _git(repo, "commit", "-q", "-am", "change")
    return repo


def _script_line(text: str, prefix: str) -> str:
    lines = [line.strip() for line in text.splitlines() if line.strip().startswith(prefix)]
    assert len(lines) == 1, (prefix, lines)
    return lines[0]


def _run_filled(line: str, repo: Path) -> subprocess.CompletedProcess:
    """Run a filled `python3 scripts/<x>.py ...` line from ship.md in `repo`, with
    the Writ checkout's script and this interpreter."""
    m = re.match(r"python3 scripts/([\w-]+\.py)( .*)$", line)
    assert m, line
    command = "%s %s%s" % (sys.executable, REPO_ROOT / "scripts" / m.group(1), m.group(2))
    env = dict(os.environ, GIT_CONFIG_GLOBAL=os.devnull, GIT_CONFIG_NOSYSTEM="1")
    return subprocess.run(["bash", "-c", command], cwd=str(repo), env=env,
                          capture_output=True, text=True, check=False)


def _known_over_budget_comments(rel: str) -> List[str]:
    lines = read("scripts/tests/test_governor_enforcement.py").splitlines()
    entry = re.compile(r'^\s*"%s": \d+,$' % re.escape(rel))
    index = next(i for i, line in enumerate(lines) if entry.match(line))
    comments: List[str] = []
    while index > 0 and lines[index - 1].lstrip().startswith("#"):
        index -= 1
        comments.insert(0, lines[index].strip())
    return comments


# --------------------------------------------------------------------------
# 2026-11-06-ship-watch-and-merge Story 2: `/ship` opens the PR without asking
# and records the ledger.
# --------------------------------------------------------------------------


def test_no_ask_block_before_step_5():
    """AC-2.1 — no AskQuestion( block on the open path before Step 5."""
    text = ship()
    assert "AskQuestion(" not in text[:text.index("### Step 5")]


@pytest.mark.parametrize("gone", [
    "Override?",
    "Save to `.writ/config.md`?",
    "┌",
    "Non-extraction note",
    "`--dry-run` output for Steps 4-5",
    "Detection chain details",
    "Opinionated defaults",
    "Do not restructure git history without explicit approval",
])
def test_open_path_prompts_and_duplicates_are_gone(gone):
    """AC-2.1 — the config-persist offer, the override prompt, the ASCII pipeline,
    the duplicate dry-run block, and the notes that restated other text are cut."""
    assert gone not in ship()


def test_step_1_prints_the_config_lines_and_writes_nothing():
    """AC-2.1 — Step 1 prints the .writ/config.md lines that would skip detection."""
    step1 = flat(section(ship(), "### Step 1"))
    assert "the `.writ/config.md` lines that would skip detection next time" in step1
    assert "Write nothing." in step1
    assert "- **Test Runner:**" in section(ship(), "### Step 1")


def test_decisions_run_the_doubt_rule_and_label_asked_answers():
    """AC-2.2 — every open-path decision writes a record and runs the doubt check;
    an asked answer is labeled."""
    decisions = flat(section(ship(), "### Decisions"))
    assert "python3 scripts/jev-judge.py doubt --record .writ/state/ship/decision-<name>.json" \
        in decisions
    assert "python3 scripts/jev-judge.py doubt-label --id <id> --outcome" in decisions
    assert "as_recommended" in decisions and "overridden" in decisions


@pytest.mark.parametrize("heading,record,site,options,recommended", [
    ("### Step 3", "decision-tests.json", "choice",
     ["Fix and retry", "Ship as a draft PR with the tests-failing label", "Abort"],
     "Fix and retry"),
    ("### Step 4", "decision-plan.json", "plan",
     ["Split as planned", "Ship as a single commit"], "Split as planned"),
    ("**Not on a feature branch:**", "decision-branch.json", "choice",
     ["Create branch `<name>`", "Abort"], "Create branch `<name>`"),
    ("**Uncommitted changes:**", "decision-commit.json", "choice",
     ["Commit now", "Stash changes", "Abort"], "Commit now"),
])
def test_each_decision_names_its_record(heading, record, site, options, recommended):
    """AC-2.2 — each decision names its record file, site, options, and recommended
    option."""
    text = ship()
    if heading.startswith("#"):
        part = section(text, heading)
    else:
        start = text.index(heading)
        part = text[start:text.index("\n**", start + len(heading))]
    part = flat(part)
    assert "`%s`" % record in part
    assert "`site: %s`" % site in part
    for option in options:
        assert '"%s"' % option in part, option
    assert 'recommended "%s"' % recommended in part


def test_untracked_files_carry_no_recommendation():
    """AC-2.2 — uncommitted changes with untracked files: no recommendation, so it asks."""
    text = ship()
    start = text.index("**Uncommitted changes:**")
    part = flat(text[start:text.index("\n**", start + 5)])
    assert "tracked modifications only" in part
    assert "untracked files present: no recommendation, so it asks" in part


def test_step_4_is_reversible_only_for_unpushed_commits():
    """AC-2.3 — presplit_sha saved first; reversible only with no upstream or every
    restructured commit unpushed; otherwise the record is not reversible and asks."""
    step4 = flat(section(ship(), "### Step 4"))
    saved = step4.index("save `presplit_sha` = `git rev-parse HEAD`")
    assert saved < step4.index("`decision-plan.json`")
    assert ("`reversible: true` only when the branch has no upstream or "
            "`git log origin/<branch>..HEAD` lists every commit the plan restructures, "
            "and `presplit_sha` is saved; otherwise `reversible: false`, so it asks") in step4


def test_step_3_saves_the_evidence_of_test_runner_then_eval_command():
    """AC-2.4 — Step 3 runs the Test Runner, then the Eval Command, and saves the
    commands, exits, HEAD, and tree."""
    step3 = flat(section(ship(), "### Step 3"))
    assert step3.index("run the Test Runner") < step3.index("then the `Eval Command`")
    for literal in (".writ/state/ship/branch-<slug>.json", "`git rev-parse HEAD^{tree}`",
                    "`git rev-parse HEAD`", "each command, its exit code"):
        assert literal in step3, literal


def test_step_5_records_only_a_tested_tree():
    """AC-2.4 — Step 5 records after gh pr create only when every exit is 0, re-runs
    the commands first when the trees differ, and never records a failing run."""
    step5 = flat(section(ship(), "### Step 5"))
    assert step5.index("gh pr create") < step5.index("python3 scripts/verify-ledger.py record")
    assert "when every saved exit code is 0" in step5
    assert "When the trees differ, re-run the commands on HEAD, save, then record." in step5
    assert "A non-zero exit is never recorded" in step5


def test_step_5_record_command_filled_writes_a_verified_row(tmp_path):
    """AC-2.4 — the Step 5 record line, filled with a temp repo's values, writes a
    row that verify-ledger.py check reads VERIFIED."""
    repo = _feature_repo(tmp_path)
    line = _script_line(section(ship(), "### Step 5"), "python3 scripts/verify-ledger.py record")
    filled = (line.replace("<n>", "7").replace("<default-branch>", "main")
              .replace("<exit>", "0").replace("<command>", "true"))
    assert "<" not in filled.replace("$(", ""), filled
    done = _run_filled(filled, repo)
    assert done.returncode == 0, done.stdout + done.stderr
    head = _git(repo, "rev-parse", "HEAD")
    check = subprocess.run([sys.executable, str(REPO_ROOT / "scripts" / "verify-ledger.py"),
                            "check", "--pr", "7", "--head", head, "--repo", str(repo)],
                           capture_output=True, text=True, check=False)
    assert check.returncode == 0 and check.stdout.splitlines()[0] == "pass", check.stdout


def test_step_5_record_command_refuses_failing_evidence(tmp_path):
    """AC-2.4 — the same line with a failing exit writes nothing."""
    repo = _feature_repo(tmp_path)
    line = _script_line(section(ship(), "### Step 5"), "python3 scripts/verify-ledger.py record")
    filled = (line.replace("<n>", "7").replace("<default-branch>", "main")
              .replace("<exit>", "1").replace("<command>", "false"))
    done = _run_filled(filled, repo)
    assert done.returncode == 1
    assert not (repo / ".writ" / "state" / "verify-ledger.json").exists()


def test_config_format_documents_eval_command():
    """AC-2.5 — config-format.md has the Eval Command row and example line."""
    text = read(".writ/docs/config-format.md")
    assert ("| `Eval Command` | ship | Command `/ship --test` and `--watch` run after the "
            "Test Runner; its exit code goes into the verification ledger. Absent: the Test "
            "Runner alone. |") in text
    assert "- **Eval Command:** make lint" in text


def test_verify_ledger_callers_cell_names_ship():
    """AC-2.5 — the verify-ledger.py row of agent-cli-contract.md names commands/ship.md."""
    rows = [line for line in read(".writ/docs/agent-cli-contract.md").splitlines()
            if line.startswith("| `verify-ledger.py` |")]
    assert len(rows) == 1
    assert rows[0].strip().strip("|").split("|")[3].strip() == "commands/ship.md"


@pytest.mark.parametrize("value", [
    "scripts/verify-ledger.py record --pr",
    "scripts/jev-judge.py doubt --record",
])
def test_command_structure_pins_the_open_path_calls(value):
    """AC-2.5 — eval-command-structure.py has passing invocation rows for the calls."""
    mod = _load("eval_command_structure_s2", "scripts/eval-command-structure.py")
    rows = [r for r in mod.ROWS if r.file == "commands/ship.md" and r.value == value]
    assert len(rows) == 1 and rows[0].kind == "invocation"
    assert rows[0].was == "check_command_structure"
    ok, _detail = mod.check_row(REPO_ROOT, rows[0])
    assert ok


def test_ship_overage_is_pinned_exactly_with_a_dated_line():
    """AC-2.5 — KNOWN_OVER_BUDGET equals the exact overage, the file stays above the
    budget, and Story 2 left a dated line above the entry."""
    gov = _load("governor_enforcement_s2", "scripts/tests/test_governor_enforcement.py")
    size = len(SHIP.read_bytes())
    assert size > COMMAND_BYTE_BUDGET
    assert gov.KNOWN_OVER_BUDGET["commands/ship.md"] == size - COMMAND_BYTE_BUDGET
    comments = _known_over_budget_comments("commands/ship.md")
    assert any(c.startswith("# 2026-11-06 (2026-11-06-ship-watch-and-merge Story 2): 3947 -> ")
               for c in comments), comments
    assert any("2026-10-20 (2026-10-20-harness-cuts Story 3): 4030 -> 4023;" in c
               for c in comments)


# --------------------------------------------------------------------------
# 2026-11-06-ship-watch-and-merge Story 3: a watch pass works a PR to
# merge-ready.
# --------------------------------------------------------------------------


def watch() -> str:
    return section(ship(), "### Step 7: Watch Pass")


def watch_part(label: str) -> str:
    """One `**7.N ...**` part of Step 7, up to the next `**7.` part."""
    text = watch()
    start = text.index("**%s" % label)
    nxt = text.find("\n**7.", start + 3)
    return text[start:] if nxt < 0 else text[start:nxt]


def test_loop_block_declares_the_watch_bound():
    """AC-3.1 — `loop:` declares watch_pass 24 halt_reported and nested fix_commit 3
    escalate, both calibrated against no recorded run, and validates clean."""
    bounds = _load("eval_loop_bounds_s3", "scripts/eval-loop-bounds.py")
    parsed, err = bounds.frontmatter(ship())
    assert err is None
    loop = parsed["loop"]
    assert (loop["unit"], loop["max_iterations"], loop["on_exhaustion"]) == \
        ("watch_pass", 24, "halt_reported")
    assert "no recorded run" in loop["calibrated_against"]
    nested = loop["nested"]
    assert len(nested) == 1
    assert (nested[0]["unit"], nested[0]["max_iterations"], nested[0]["on_exhaustion"]) == \
        ("fix_commit", 3, "escalate")
    assert "no recorded run" in nested[0]["calibrated_against"]
    assert bounds.validate_loop("commands/ship.md", loop, False) == []


def test_ship_is_registered_as_loop_bearing():
    """AC-3.1 — ship is in both lists and eval-loop-bounds.py reports no FAIL."""
    bounds = _load("eval_loop_bounds_s3b", "scripts/eval-loop-bounds.py")
    lean = _load("eval_leanness_s3", "scripts/eval-leanness.py")
    assert "ship" in bounds.LOOP_BEARING_COMMANDS
    assert "ship" in lean.LOOP_BEARING_COMMANDS_FALLBACK
    assert "ship" in lean.LOOP_BEARING_COMMANDS
    done = subprocess.run([sys.executable, str(REPO_ROOT / "scripts" / "eval-loop-bounds.py")],
                          capture_output=True, text=True, check=False)
    assert not [line for line in done.stdout.splitlines() if line.startswith("FAIL")], \
        done.stdout
    assert "PASS\tschema-ship" in done.stdout


ACTION_ORDER = [
    "line 1 `pass`",
    "`conflicts`",
    "`merge_gates: behind`",
    "`unresolved_threads`",
    "`failing_checks`",
    "`merge_gates: not_verified`",
    "`merge_gates: draft`",
    "`merge_gates: not_open`",
    "`merge_gates: changes_requested`, `review_required`, `merge_state_blocked`; "
    "`unknown: checks_pending`, `mergeable_unknown`, `head_moved`",
    "`unknown: threads_truncated`, `merge_state_unexplained`",
]


def test_action_table_rows_are_in_the_fixed_order():
    """AC-3.2 — the 7.6 table: pass, conflicts, behind, threads, CI, not_verified,
    draft, not_open, the waiting row, the asking row."""
    part = watch_part("7.6")
    rows = [line for line in part.splitlines() if line.startswith("| ") and "---" not in line]
    firsts = [row.split(" | ")[0][2:].strip() for row in rows[1:]]
    assert firsts == ACTION_ORDER
    states = [row.rstrip(" |").rsplit("| ", 1)[1] for row in rows[1:]]
    assert states[-2] == "`waiting`" and states[-1] == "`asked`"


def test_step_7_counts_the_pass_before_acting_and_halts_at_24():
    """AC-3.2 — the pass count is written before any action; 24 halts with a record
    and the resume line; the judge runs pr-ready on the snapshot; one report line."""
    text = flat(watch())
    bound = flat(watch_part("7.2"))
    assert ".writ/state/ship/watch-pr-<n>.json" in bound
    assert "`passes` 24 or more → write `halt`" in bound
    assert "and report `halted`" in bound
    assert ("A `halt` record already present → ask the person directly, never through the "
            "doubt check") in bound
    assert "Reset clears `halt`, sets `passes: 0`, and continues; Leave → `halted`" in bound
    assert "add 1 to `passes` and write the file before anything else" in bound
    assert text.index("**7.2") < text.index("**7.6")
    assert ("`python3 scripts/pr-ready.py check --snapshot .writ/state/pr-ready/pr-<n>.json`"
            in flat(watch_part("7.4")))
    assert "`python3 scripts/pr-ready.py --help`" in flat(watch_part("7.3"))
    report = flat(watch_part("7.10"))
    assert "`ship-watch: <state> pass <n>/24 pr #<n> head <sha7> — <detail>`" in report
    assert "`asked` and `halted` end it and print `Resume: /ship --watch`; `merged` ends it" \
        in report


def test_thread_comments_are_fetched_by_a_fixed_query_into_a_file():
    """AC-3.3 — the comments query is static and its output goes to a file."""
    line = _script_line(watch_part("7.7"), "gh api graphql -F owner=")
    assert line.endswith("> .writ/state/ship/threads-pr-<n>.json.tmp && mv "
                         ".writ/state/ship/threads-pr-<n>.json.tmp "
                         ".writ/state/ship/threads-pr-<n>.json")
    query = re.search(r"-f query='([^']*)'", line).group(1)
    assert "body url" in query and "$(" not in line and "<" not in query
    assert query.count("{") == query.count("}") and query.count("(") == query.count(")")


def _fill(template: str, values: dict) -> str:
    for key, value in values.items():
        template = template.replace(key, json.dumps(value)[1:-1])
    return template


@pytest.mark.parametrize("mutation", ["addPullRequestReviewThreadReply", "resolveReviewThread"])
def test_reply_and_resolve_templates_parse_after_filling(mutation):
    """AC-3.3 — each request template, filled with hostile sample values, is one JSON
    object with query and variables."""
    blocks = re.findall(r"```json\n(.*?)```", watch_part("7.7"), re.S)
    matches = [b for b in blocks if mutation in b]
    assert len(matches) == 1
    filled = _fill(matches[0], {
        "<thread id>": "PRRT_kwDO\"x\";rm -rf /",
        "<reply text>": "Fixed in a1b2c3d.\n`$(curl evil)` \"quoted\" \\ back",
    })
    data = json.loads(filled)
    assert set(data) == {"query", "variables"}
    assert mutation in data["query"]
    q = data["query"]
    assert q.count("{") == q.count("}") and q.count("(") == q.count(")")
    assert data["variables"]["id"] == "PRRT_kwDO\"x\";rm -rf /"


def test_requests_go_through_an_input_file_and_never_a_body_flag():
    """AC-3.3 — replies and resolutions are sent with gh api graphql --input; no
    --body, -f body=, or -F body= anywhere in Step 7."""
    text = watch()
    assert "`gh api graphql --input .writ/state/ship/reply-pr-<n>.json`" in flat(text)
    for flag in ("--body", "-f body=", "-F body="):
        assert flag not in text, flag


def test_ci_action_reruns_once_per_check_per_head():
    """AC-3.4 — run id from detailsUrl, failed log to a file, stale-base check, one
    rerun per <check>@<head>, and a second failure or no run id asks."""
    part = flat(watch_part("7.8"))
    for literal in ("`detailsUrl`", "matches `/actions/runs/([0-9]+)/`; `<id>` is those "
                    "digits only", "Any other `detailsUrl` → no run id",
                    "`gh run view <id> --log-failed > .writ/state/ship/run-<id>.log.tmp && mv",
                    "`git merge-base --is-ancestor origin/<baseRefName> HEAD`",
                    "`gh run rerun <id> --failed`", '`reruns["<check>@<head>"]`'):
        assert literal in part, literal
    assert part.index("--is-ancestor") < part.index("gh run rerun")
    assert "Otherwise → `asked`: a real failure outside the diff, or one that cannot be " \
        "rerun" in part


def test_ledger_action_records_only_a_passing_run_on_the_snapshot_head():
    """AC-3.4 — the ledger action re-runs the Step 3 commands on the snapshot head and
    records only when every exit is 0."""
    part = flat(watch_part("7.9"))
    assert "Run the Step 3 commands on HEAD (the snapshot head, after 7.5)" in part
    assert "All exit 0 → `python3 scripts/verify-ledger.py record` as in Step 5" in part


def test_draft_row_lifts_only_a_tests_failed_draft():
    """AC-3.4 — gh pr ready only when draft_reason is tests_failed; otherwise ask."""
    rows = [line for line in watch_part("7.6").splitlines()
            if line.startswith("| `merge_gates: draft`")]
    assert len(rows) == 1
    assert "`draft_reason` is `tests_failed`: `gh pr ready <n>`. Otherwise ask" in rows[0]


def test_every_adapter_maps_re_enter():
    """AC-3.5 — all four adapters carry a `re-enter` row in their tool tables; ship.md
    names the loop only through that row."""
    gen = _load("gen_platform_trees_s3", "scripts/gen-platform-trees.py")
    for adapter in gen.ADAPTERS:
        table = gen.parse_adapter(REPO_ROOT / "adapters" / ("%s.md" % adapter))
        assert table.verdict == "pass", (adapter, table.reasons)
        assert "re-enter" in table.names, adapter
    claude = [row for row in gen.parse_adapter(REPO_ROOT / "adapters" / "claude-code.md").rows
              if row.name == "re-enter"]
    assert "`/loop /ship --watch`" in claude[0].mapping
    assert "/loop" not in ship()
    assert "the adapter's `re-enter` row" in ship()


def test_claude_code_records_the_loop_fact_with_a_date():
    """AC-3.5 — Claude Code's verification record has a dated `/loop` row."""
    text = read("adapters/claude-code.md")
    rows = [line for line in text.splitlines() if line.startswith("| `re-enter`: `/loop`")]
    assert len(rows) == 1
    assert "Claude Code 2.1.310" in rows[0] and "2026-11-06" in rows[0]
    assert re.search(r"\| (?:verified|unverified) 2026-11-06 \|$", rows[0])


def test_system_instructions_bound_autonomy_to_a_watch():
    """AC-3.5 — the base names the watch as a bound and forbids an unbounded loop."""
    system = flat(read("system-instructions.md"))
    assert ("Autonomy is session-started and bounded to one spec, one roadmap phase, or one "
            "PR's `/ship --watch` passes; it never becomes an unbounded loop.") in system
    assert ("no unbounded loop." in read("scripts/eval.sh")
            and 'require_literal "$system" "it never"' in read("scripts/eval.sh"))


def test_pr_ready_callers_cell_names_ship_and_jev_judge():
    """AC-3.5 — the pr-ready.py Callers cell reads commands/ship.md, scripts/jev-judge.py."""
    rows = [line for line in read(".writ/docs/agent-cli-contract.md").splitlines()
            if line.startswith("| `pr-ready.py` |")]
    assert rows[0].strip().strip("|").split("|")[3].strip() == \
        "commands/ship.md, scripts/jev-judge.py"


@pytest.mark.parametrize("kind,value", [
    ("invocation", "scripts/pr-ready.py check --snapshot"),
    ("heading", "Step 7: Watch Pass"),
])
def test_command_structure_pins_the_watch(kind, value):
    """AC-3.5 — eval-command-structure.py rows for the judge call and the heading pass."""
    mod = _load("eval_command_structure_s3", "scripts/eval-command-structure.py")
    rows = [r for r in mod.ROWS if r.file == "commands/ship.md" and r.value == value]
    assert len(rows) == 1 and rows[0].kind == kind
    ok, _detail = mod.check_row(REPO_ROOT, rows[0])
    assert ok


def test_watch_invocation_and_story_3_overage_line():
    """AC-3.5 — the --watch invocation row exists and Story 3 left a dated overage line."""
    text = ship()
    assert ("| `/ship --watch` | Open the PR if none is open (implies `--test`), then run one "
            "watch pass (Step 7). Keep watching with the adapter's `re-enter` row. |") in text
    assert "| Drive an open PR to merge-ready | `/ship --watch` |" in text
    comments = _known_over_budget_comments("commands/ship.md")
    assert any(c.startswith("# 2026-11-06 (2026-11-06-ship-watch-and-merge Story 3): ")
               for c in comments), comments
