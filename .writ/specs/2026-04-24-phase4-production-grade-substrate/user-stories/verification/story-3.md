# Story 3 Verification Checklist: SKILL.md Template Generation

> **Story:** [SKILL.md Template Generation](../story-3-skill-md-generation.md)
> **Verified:** 2026-04-24
> **Result:** Passed

## Acceptance Criteria

- [x] `.writ/manifest.yaml` exists and enumerates every current command in `commands/` and every current agent in `agents/`, excluding `_*.md` infra files.
- [x] `bash scripts/gen-skill.sh` regenerates `SKILL.md`, preserves the YAML frontmatter block, replaces the body from manifest data, and exits 0.
- [x] `bash scripts/gen-skill.sh --check` exits 0 when committed `SKILL.md` matches `.writ/manifest.yaml`.
- [x] A deliberate drift simulation causes `bash scripts/gen-skill.sh --check` to exit 1 and print a unified diff.
- [x] A malformed manifest simulation, with a command entry missing required field `name`, causes `gen-skill.sh` to exit 1 with a targeted schema error.
- [x] The generator reports its active parser mode. In this environment it used the pure-bash fallback because `yq` was not available.

## Commands Run

```bash
bash scripts/gen-skill.sh --dry-run >/tmp/writ-skill-dry-run.md
bash scripts/gen-skill.sh
bash scripts/gen-skill.sh --check
bash -c 'set +e; tmp_skill=$(mktemp); cp "SKILL.md" "$tmp_skill"; printf "\nmanual drift\n" >> "SKILL.md"; bash "scripts/gen-skill.sh" --check >/tmp/writ-skill-drift.out 2>&1; rc=$?; cp "$tmp_skill" "SKILL.md"; rm -f "$tmp_skill"; [ "$rc" -eq 1 ]'
bash -c 'set +e; tmp_manifest=$(mktemp); cp ".writ/manifest.yaml" "$tmp_manifest"; python3 -c "from pathlib import Path; p=Path(\".writ/manifest.yaml\"); lines=p.read_text().splitlines(True); target=\"  - name: assess-spec\"+chr(10); removed=[False]; p.write_text(\"\".join([line for line in lines if not (line == target and not removed[0] and not removed.__setitem__(0, True))]))"; bash "scripts/gen-skill.sh" --dry-run >/tmp/writ-malformed-manifest.out 2>&1; rc=$?; cp "$tmp_manifest" ".writ/manifest.yaml"; rm -f "$tmp_manifest"; [ "$rc" -eq 1 ]'
```

## Notes

- The CI workflow currently runs only the Story 3 gate: `bash scripts/gen-skill.sh --check`. Story 5 will extend the same workflow with `scripts/eval.sh`.
- The malformed-manifest simulation was reverted immediately after verification; no deliberate violation remains in the working tree.
