"""export.py <root> <evidence-dir> : copies each run's condensed transcript and
grade into <evidence-dir>/<condition>/<probe>-<n>.{txt,json}, after grading,
with temp paths and the local account replaced. Raw event streams stay in the
temp root; they are never committed."""
import getpass, re, shutil, sys, pathlib

R, E = pathlib.Path(sys.argv[1]), pathlib.Path(sys.argv[2])
user = getpass.getuser()
def scrub(s):
    s = re.sub(r"/(?:private/)?tmp/d2\.\w+", "<tmp>", s)
    s = re.sub(r"/Users/[^/\s\"']+", "<home>", s)
    return s.replace(user, "<user>")
for line in (R / "map.txt").read_text().splitlines():
    rid, cond, probe, n = line.split()
    d = E / cond; d.mkdir(parents=True, exist_ok=True)
    for src, ext in (("transcript.txt", "txt"), ("grade.json", "json")):
        f = R / "runs" / rid / src
        if f.exists():
            (d / ("%s-%s.%s" % (probe, n, ext))).write_text(scrub(f.read_text()))
