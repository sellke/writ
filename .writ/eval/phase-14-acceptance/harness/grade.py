"""grade.py <run.jsonl> <rubric-file> <section-heading|-> <prompt-file> <out.json>
Blind grading: strips condition-identifying lines, sends rubric + prompt + transcript
to a fresh `claude -p` with no tools, and saves its JSON verdict."""
import json, re, subprocess, sys, pathlib
run, rubric_file, heading, prompt_file, out = sys.argv[1:6]
S = pathlib.Path(__file__).parent
GRADER_DIR = str(pathlib.Path(S / "root.txt").read_text().strip()) + "/grader"
t = subprocess.run([sys.executable, str(S / "condense.py"), run], capture_output=True, text=True).stdout
t = "\n".join(l for l in t.splitlines() if not l.startswith(("[init]", "[codex thread]", "[result]", "[turn.completed]")))
rub = pathlib.Path(rubric_file).read_text()
if heading != "-":
    m = re.search(r"^## " + re.escape(heading) + r"\n(.*?)(?=^## |\Z)", rub, re.S | re.M)
    rub = "## " + heading + "\n" + m.group(1)
task = pathlib.Path(prompt_file).read_text()
msg = f"""You grade one run of an AI coding agent against a rubric that was written before the run. You see only the rubric, the prompt the agent received, and the agent's transcript. Judge each criterion strictly from the transcript. Do not give credit for intent; quote the evidence. If the transcript is empty or cut off, criteria it cannot show are not met.

<rubric>
{rub}
</rubric>

<agent_prompt>
{task}
</agent_prompt>

<transcript>
{t[:60000]}
</transcript>

Reply with only a JSON object, no code fence:
{{"criteria": {{"<id>": {{"met": true or false, "evidence": "<short quote or reason>"}}}}, "verdict": "pass" or "fail", "note": "<one sentence>"}}"""
r = subprocess.run(["claude", "-p", msg, "--tools", "", "--setting-sources", "project", "--no-session-persistence",
                    "--model", "claude-opus-5-5", "--output-format", "json"], capture_output=True, text=True,
                   cwd=GRADER_DIR)
res = json.loads(r.stdout)["result"].strip()
res = re.sub(r"^```(?:json)?\s*|\s*```$", "", res)
try:
    v = json.loads(res)
except Exception:
    v = {"verdict": "unparsed", "raw": res}
pathlib.Path(out).write_text(json.dumps(v, indent=2))
print(pathlib.Path(run).parent.name, pathlib.Path(run).stem, v.get("verdict"), "|", v.get("note", "")[:120])
