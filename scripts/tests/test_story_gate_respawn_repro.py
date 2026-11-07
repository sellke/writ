import json

from test_story_gate import Repo

FIELD = "REVIEW" + "_RESULT"


def test_evidence_waits_for_the_safety_fact_re_spawn():
    repo = Repo()
    try:
        repo.write_map()
        repo.stub("boundary-map.py", "crossings", json.dumps({
            "verdict": "pass", "route": "review-agent", "reasons": ["r"], "summary": "s"}), 0)
        repo.run(phase="pre-review")
        repo.stub("review-override.py", "safety-fact",
                  "fail\nrung: claimed=traced measured=traced\nfact: f\n"
                  "reason: safety_fact_below_floor traced\nreview-override safety-fact: fail\n", 1)
        review = repo.review("### %s: FAIL\n" % FIELD)
        result = repo.run("--review-output", str(review), phase="post-review")
        assert "restart: gate3\n" in result.stdout, result.stdout
        ran = [args[0] for name, args in repo.calls() if name == "review-override.py"]
        assert "evidence" not in ran, ran
    finally:
        repo.close()
