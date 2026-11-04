"""tally.py <root> : pass counts per condition and probe from map.txt and the
grades, plus the one-sided Fisher exact p of each condition's P2 passes
against base's (rubric.md -> Decision rule)."""
import json, sys, pathlib
from math import comb

R = pathlib.Path(sys.argv[1])
rows = [l.split() for l in (R / "map.txt").read_text().splitlines() if l.strip()]
tally = {}
for rid, cond, probe, n in rows:
    g = R / "runs" / rid / "grade.json"
    verdict = json.loads(g.read_text()).get("verdict") if g.exists() else "ungraded"
    tally.setdefault((cond, probe), []).append(verdict)


def fisher_greater(a, n1, b, n2):
    """P(X >= a) for a variant with a of n1 passes against base with b of n2,
    under the hypergeometric null with the margins fixed."""
    k, total = a + b, n1 + n2
    return sum(comb(n1, x) * comb(n2, k - x) for x in range(a, min(n1, k) + 1)) / comb(total, k)


conds = ["control", "base", "pd-first", "pd-last", "intro-op"]
base = tally.get(("base", "P2"), [])
print("condition  P2      P3     P1     p(P2 > base)")
for c in conds:
    cells = []
    for p in ("P2", "P3", "P1"):
        v = tally.get((c, p), [])
        other = [x for x in v if x not in ("pass", "fail")]
        cells.append("%d/%d%s" % (v.count("pass"), len(v), "*" if other else ""))
    v = tally.get((c, "P2"), [])
    pval = fisher_greater(v.count("pass"), len(v), base.count("pass"), len(base)) if v and base and c != "base" else None
    print("%-10s %-7s %-6s %-6s %s" % (c, cells[0], cells[1], cells[2], "%.4f" % pval if pval is not None else "-"))
