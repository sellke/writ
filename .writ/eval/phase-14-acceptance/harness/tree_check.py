"""Byte-for-byte check of a Writ install against its source tree.

usage: tree_check.py <platform> <project> <src> <out.json>
For every manifest line, compare: the file on disk, the manifest hash, and
the source file at the mapped path. Then list shippable source files that the
install is missing, using install.sh's own is_shippable_* functions.
"""
import hashlib, json, pathlib, subprocess, sys

platform, proj, src, out = sys.argv[1], pathlib.Path(sys.argv[2]), pathlib.Path(sys.argv[3]), sys.argv[4]
PDIR = {"claude": ".claude", "cursor": ".cursor", "codex": ".codex"}[platform]
SKILLS = {"claude": ".claude/skills", "cursor": ".cursor/skills", "codex": ".agents/skills"}[platform]
AGENTS_SRC = {"claude": "claude-code/agents", "cursor": "agents", "codex": "codex/agents"}[platform]

def sha(p):
    return hashlib.sha256(p.read_bytes()).hexdigest() if p.is_file() else None

def disk_path(mpath):
    if mpath.startswith(("scripts/", ".writ/")):
        return proj / mpath
    if mpath.startswith("skills/"):
        return proj / SKILLS / mpath[len("skills/"):]
    return proj / PDIR / mpath

def src_path(mpath):
    if mpath.startswith("agents/"):
        return src / AGENTS_SRC / mpath[len("agents/"):]
    if mpath == "rules/writ.mdc":
        return src / "cursor/writ.mdc"
    return src / mpath

manifest = proj / PDIR / ".writ-manifest"
rows, header = [], {}
for line in manifest.read_text().splitlines():
    if line.startswith("#"):
        if ":" in line:
            k, v = line[1:].split(":", 1); header[k.strip()] = v.strip()
        continue
    if not line.strip():
        continue
    h, mpath = line.split(None, 1)
    rows.append((h, mpath.strip()))

result = {"platform": platform, "manifest_header": header, "entries": len(rows),
          "mismatch": [], "missing_on_disk": [], "no_source": []}
for h, mpath in rows:
    d, s = disk_path(mpath), src_path(mpath)
    dh, sh = sha(d), sha(s)
    if mpath.endswith((".baseline", ".writ-block")) or mpath in ("CLAUDE.md", "AGENTS.md"):
        continue  # block and install-once baselines: checked separately
    if dh is None:
        result["missing_on_disk"].append(mpath); continue
    if sh is None:
        result["no_source"].append(mpath); continue
    if not (dh == h == sh):
        result["mismatch"].append({"path": mpath, "disk": dh[:12], "manifest": h[:12], "source": sh[:12]})

# Expected shippable set, from install.sh's own predicates.
def shippable(fn, names):
    script = 'eval "$(sed -n "/^%s()/,/^}/p" "%s/scripts/install.sh")"; for n in "$@"; do %s "$n" && echo "$n"; done' % (fn, src, fn)
    r = subprocess.run(["bash", "-c", script, "x"] + names, capture_output=True, text=True)
    return set(r.stdout.split())

installed = {m for _, m in rows}
expected = {"commands/" + p.name for p in (src / "commands").glob("*.md")}
expected |= {"agents/" + p.name for p in (src / AGENTS_SRC).iterdir() if p.is_file() and not p.name.startswith(".")}
expected |= {"skills/%s/SKILL.md" % p.parent.name for p in (src / "skills").glob("*/SKILL.md")}
expected |= {"scripts/" + n for n in shippable("is_shippable_script", [p.name for p in (src / "scripts").iterdir() if p.is_file()])}
expected |= {".writ/docs/" + n for n in shippable("is_shippable_writ_doc", [p.name for p in (src / ".writ/docs").glob("*.md")])}
# Every platform's entry file tells the agent to read system-instructions.md
# (CLAUDE.md imports it, writ.mdc and AGENTS.md name it), so all three ship it.
expected.add("system-instructions.md")
if platform == "cursor":
    expected.add("rules/writ.mdc")
result["expected_not_installed"] = sorted(expected - installed)
result["installed_not_expected"] = sorted(m for m in installed - expected if not m.endswith((".baseline", ".writ-block")) and m not in ("CLAUDE.md", "AGENTS.md"))
result["ok"] = not (result["mismatch"] or result["missing_on_disk"] or result["no_source"] or result["expected_not_installed"])
pathlib.Path(out).write_text(json.dumps(result, indent=2))
print("%s: entries=%d mismatch=%d missing=%d no_source=%d expected_not_installed=%d installed_not_expected=%d ok=%s" % (
    platform, len(rows), len(result["mismatch"]), len(result["missing_on_disk"]), len(result["no_source"]),
    len(result["expected_not_installed"]), len(result["installed_not_expected"]), result["ok"]))
