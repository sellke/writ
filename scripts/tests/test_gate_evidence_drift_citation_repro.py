import re
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[2]


def _gate_evidence(gate_id):
    text = (REPO_ROOT / "commands" / "implement-story.md").read_text(encoding="utf-8")
    entry = re.search(r"(?m)^  - id: %s\n((?:    \S.*\n)*)" % re.escape(gate_id), text)
    assert entry, gate_id
    value = re.search(r'(?m)^    evidence: "(.*)"$', entry.group(1))
    assert value, gate_id
    return value.group(1)


def _drift_entry(spec_name, dev_id):
    logs = sorted((REPO_ROOT / ".writ" / "specs").glob("**/*-%s/drift-log.md" % spec_name))
    assert logs, spec_name
    text = logs[0].read_text(encoding="utf-8")
    m = re.search(r"(?ms)^#### \[%s\].*?(?=^#### \[|\Z)" % re.escape(dev_id), text)
    assert m, dev_id
    return m.group(0)


def test_gate3_5_drift_evidence_cites_a_gate3_pause():
    # AC-1.4 / Rule 1: the cited drift entry must show Gate 3 returning PAUSE,
    # so Gate 3.5's drift response changed the outcome.
    evidence = _gate_evidence("gate3_5_drift")
    cite = re.match(r"(\S+) (DEV-\d+)", evidence)
    assert cite, evidence
    entry = _drift_entry(cite.group(1), cite.group(2))
    assert "PAUSE" in entry, "%s %s records no Gate 3 PAUSE" % cite.groups()
