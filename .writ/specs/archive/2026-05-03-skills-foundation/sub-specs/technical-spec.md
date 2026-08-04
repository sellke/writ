# Technical Specification — Skills Foundation

> **Parent spec:** `../spec.md`
> **ADR:** `../../decision-records/adr-009-command-agent-skill-boundary.md`
> **Status:** Not Started

This sub-spec captures the concrete technical contracts, schemas, and grammar that Stories 1–7 implement. It is the source-of-truth for *exactly what to write* once contract-level agreement is locked.

## File × Story Matrix

| File | Story 1 | Story 2 | Story 3 | Story 4 | Story 5 | Story 6 | Story 7 |
|---|---|---|---|---|---|---|---|
| `.writ/manifest.yaml` | extend schema | — | add+remove smoke entry | — | — | append on `/new-skill` | empty `skills:` final |
| `scripts/gen-skill.sh` | extend parsers + body | — | regenerate | — | — | — | regenerate |
| `scripts/install.sh` | — | add Skills step + overlay | run install | — | — | — | — |
| `scripts/update.sh` | — | mirror install logic | — | — | — | — | — |
| `scripts/lint-skill.sh` (NEW) | — | — | — | — | — | create | — |
| `commands/new-skill.md` (NEW) | — | — | — | — | — | create | — |
| `commands/refresh-command.md` | — | — | — | — | — | add boundary section | — |
| `adapters/cursor.md` | — | — | — | add Skills section | append `required_skills:` ref | — | — |
| `adapters/claude-code.md` | — | — | — | add Skills section | append `required_skills:` ref | — | — |
| `adapters/openclaw.md` | — | — | — | add Skills section | append `required_skills:` ref | — | — |
| `system-instructions.md` | — | — | — | — | add Skills section | — | — |
| `cursor/writ.mdc` | — | — | — | — | mirror Skills section | — | — |
| `skills/hello-writ/SKILL.md` (TRANSIENT) | — | — | create + delete | — | — | — | — |
| `.writ/docs/skills.md` (NEW) | — | — | — | — | — | — | create |
| `README.md` | — | — | — | — | — | — | three-primitives section |
| `AGENTS.md` | — | — | — | — | — | — | Repository Structure update |
| `.writ/docs/self-dogfooding.md` | — | — | — | — | — | — | Skills section |
| `.cursor/skills` (symlink) | — | — | — | — | — | — | create |
| `SKILL.md` (root) | regenerate | — | regenerate | — | — | — | regenerate |

## Manifest Schema (Story 1)

### YAML structure

```yaml
skills:
  - name: <kebab-case-name>          # required, unique across commands/agents/skills
    file: skills/<name>/SKILL.md     # required, must exist on disk
    description: "<verb-phrase>"     # required, non-empty
    tags: [<tag1>, <tag2>]           # optional, kebab-case strings
    aliases: [<alias1>]              # optional, kebab-case strings
```

### Validation rules

| Rule | Severity | Error message |
|---|---|---|
| Missing `name` | Fatal | `YAML error: skills[N] missing required field 'name'` |
| Missing `file` | Fatal | `YAML error: skills[N] (<name>) missing required field 'file'` |
| Missing `description` | Fatal | `YAML error: skills[N] (<name>) missing required field 'description'` |
| `file` does not exist | Fatal | `YAML error: skills[N] (<name>) references missing file '<file>'` |
| Duplicate name across commands/agents/skills | Fatal | `YAML error: skills[N] (<name>) name conflicts with existing <command\|agent\|skill>` |
| Empty list (`skills: []`) | OK | (no error; renders no Skills section) |
| Section absent entirely | OK | (no error; backward compat) |

### Bash fallback parser additions (`parse_with_bash`)

New section detection:

```bash
case "$line" in
  ...existing cases...
  skills:)
    flush_command_item
    flush_agent_item
    flush_category_item
    flush_skill_item       # NEW
    section="skills"
    continue
    ;;
esac
```

New section handler:

```bash
case "$section" in
  ...existing handlers...
  skills)
    if [[ "$line" == "- name:"* ]]; then
      flush_skill_item
      _SKILL_STARTED="true"
      _SKILL_NAME="$(strip_value "${line#- name:}")"
    elif [[ "$line" == "file:"* ]]; then
      _SKILL_STARTED="true"
      _SKILL_FILE="$(strip_value "${line#file:}")"
    elif [[ "$line" == "description:"* ]]; then
      _SKILL_STARTED="true"
      _SKILL_DESCRIPTION="$(strip_value "${line#description:}")"
    elif [[ "$line" == "tags:"* ]]; then
      _SKILL_STARTED="true"
      _SKILL_TAGS="$(strip_value "${line#tags:}")"
    elif [[ "$line" == "aliases:"* ]]; then
      _SKILL_STARTED="true"
      _SKILL_ALIASES="$(strip_value "${line#aliases:}")"
    fi
    ;;
esac
```

### `parse_with_yq` additions

```bash
while IFS=$'\t' read -r name file description tags aliases; do
  SKILL_NAMES+=("$name")
  SKILL_FILES+=("$file")
  SKILL_DESCRIPTIONS+=("$description")
  SKILL_TAGS+=("${tags:-}")
  SKILL_ALIASES+=("${aliases:-}")
done < <(yq_read ".skills[] | [.name, .file, .description, ((.tags // []) | join(\",\")), ((.aliases // []) | join(\",\"))] | @tsv")
```

### Body generation (`generate_body`)

After `## Available Agents` table, conditionally add:

```bash
if [ ${#SKILL_NAMES[@]} -gt 0 ]; then
  cat <<EOF

## Available Skills

| Skill | File | Description |
|-------|------|-------------|
EOF
  for ((i = 0; i < ${#SKILL_NAMES[@]}; i++)); do
    echo "| \`${SKILL_NAMES[$i]}\` | \`${SKILL_FILES[$i]}\` | ${SKILL_DESCRIPTIONS[$i]} |"
  done
fi
```

## Install/Update Fanout (Story 2)

### `overlay_scan_skills` function

```bash
_NEW=0; _UPDATED=0; _PRESERVED=0; _UNCHANGED=0

overlay_scan_skills() {
  local src_dir="$1" local_dir="$2" mode="$3"
  _NEW=0; _UPDATED=0; _PRESERVED=0; _UNCHANGED=0

  local skill_folder skill_name src_skill local_skill rel_path
  for skill_folder in "$src_dir"/*/; do
    [ -d "$skill_folder" ] || continue
    skill_name=$(basename "$skill_folder")
    src_skill="$skill_folder/SKILL.md"
    [ -f "$src_skill" ] || continue

    local_skill="$local_dir/$skill_name/SKILL.md"
    rel_path="skills/$skill_name/SKILL.md"

    # 1. Apply three-way overlay to SKILL.md (same logic as overlay_scan)
    # 2. Copy sidecar files (everything except SKILL.md) install-once
    # ... (full implementation in Story 2)
  done
}
```

### Integration in `install.sh`

```bash
mkdir -p "$PLATFORM_DIR/commands" "$PLATFORM_DIR/agents" "$PLATFORM_DIR/skills"  # NEW
[ "$PLATFORM" = "cursor" ] && mkdir -p "$PLATFORM_DIR/rules"

STEP_TOTAL=6   # was 5

STEP=$((STEP + 1))
echo "  [$STEP/$STEP_TOTAL] Commands..."
overlay_scan "$WRIT_SRC/commands" "$PLATFORM_DIR/commands" "commands" "apply"
CMD_NEW=$_NEW; CMD_UPDATED=$_UPDATED; CMD_PRESERVED=$_PRESERVED

STEP=$((STEP + 1))
echo "  [$STEP/$STEP_TOTAL] Agents..."
overlay_scan "$WRIT_SRC/$AGENTS_SRC" "$PLATFORM_DIR/agents" "agents" "apply"
AGENT_NEW=$_NEW; AGENT_UPDATED=$_UPDATED; AGENT_PRESERVED=$_PRESERVED

STEP=$((STEP + 1))                                        # NEW
echo "  [$STEP/$STEP_TOTAL] Skills..."                    # NEW
if [ -d "$WRIT_SRC/skills" ]; then                        # NEW
  overlay_scan_skills "$WRIT_SRC/skills" "$PLATFORM_DIR/skills" "apply"
  SKILL_NEW=$_NEW; SKILL_UPDATED=$_UPDATED; SKILL_PRESERVED=$_PRESERVED
else                                                       # NEW
  SKILL_NEW=0; SKILL_UPDATED=0; SKILL_PRESERVED=0          # NEW
  echo "    (no skills/ in source; skipping)"             # NEW
fi                                                         # NEW
```

### Manifest writeback extension

In `write_copy_manifest`, after the existing commands/agents loop:

```bash
local skill_folder skill_name src_skill rel
for skill_folder in "$PLATFORM_DIR"/skills/*/; do
  [ -d "$skill_folder" ] || continue
  skill_name=$(basename "$skill_folder")
  src_skill="$skill_folder/SKILL.md"
  [ -f "$src_skill" ] || continue
  rel="skills/$skill_name/SKILL.md"
  echo "$(hash_file "$src_skill")  $rel" >> "$target"
done
```

## `Required skills:` Convention (Story 5)

### Schema

```yaml
---
name: <agent-or-command-name>
required_skills:
  - <skill-name-1>
  - <skill-name-2>
---
```

### Semantics

- `required_skills` is an **optional** array.
- Values are skill names matching `name:` entries in `.writ/manifest.yaml`.
- Order is **preserved** (downstream tooling may use it for load priority).
- Duplicates are **silently deduplicated**.
- Unknown skill names produce a **warning** at consumer load time, not a hard failure.
- The harness pre-loads each named skill (via `Read skills/<name>/SKILL.md`) before the consumer's first phase begins.

### Reserve-only status

This convention is documented but **not adopted by any existing agent or command** in this spec. Adoption happens organically during pilot skill extraction (separate specs).

### 90-day review

| Date | Action |
|---|---|
| 2026-05-03 | Convention defined and documented |
| 2026-08-03 | Review trigger: if no agent or command has adopted `required_skills:`, deprecate or revisit |

## Boundary Lint Grammar (Story 6)

### Description-shape rejections

Applied to the `description:` frontmatter value (string match, case-sensitive at start):

| Pattern | Category | Suggested remediation |
|---|---|---|
| `^Acts as` | Role-shape | "Skills describe a capability, not a role. Rephrase as a verb-phrase, or move this to an agent." |
| `^Is responsible for` | Role-shape | "Skills are tools, not responsibilities. Rephrase as 'How to <verb> ...'." |
| `^The .* agent` | Role-shape | "Skills are not roles. Rephrase as a verb-phrase, or move this to an agent." |
| `^Run the full` | Workflow-shape | "Skills describe a capability, not a workflow. Move this to a /command." |
| `^Execute the entire` | Workflow-shape | "Skills are not workflows. Inline the steps as 'How to ...' or move this to a /command." |

### Body-shape rejections

Applied to the rendered markdown body (post-frontmatter), scoped to the **first 200 characters of each paragraph**, **excluding fenced code blocks**:

| Pattern | Category | Suggested remediation |
|---|---|---|
| `Read commands/` | Command invocation | "Skills do not invoke commands. Inline the steps or describe the capability." |
| `Read skills/` | Skill chaining | "Skills do not call other skills. Combine them into the consumer (agent/command) that uses both." |
| `\bTask\(` | Subagent dispatch | "Skills do not spawn subagents. Move orchestration to a command." |
| `^/[a-z][a-z-]+` (paragraph start) | Slash command | "Skills do not invoke slash commands. Skills are tools the agent already has." |

### Lint output format

For each violation:

```
❌ <file>:<line>: <category> — pattern "<offending phrase>"
   Remediation: <one-line guidance>
```

Exit codes: `0` = pass, `1` = lint failure (one or more violations), `2` = usage error (e.g., file not found).

### Code block exemption

The lint scanner identifies fenced code blocks via `^```` markers and excludes their content from body-shape checks. Indented code blocks (4-space indent) are also exempt. Inline code spans (single backticks) are not exempt — workflow-shaped language inside inline code is still flagged.

## Test Fixtures

### Description-shape rejection fixtures (Story 6)

Five fixture descriptions, all expected to be rejected:

1. `Acts as a senior code reviewer who validates ...` → Role-shape
2. `Is responsible for verifying every commit follows ...` → Role-shape
3. `The review agent compares the diff against ...` → Role-shape
4. `Run the full security audit pipeline including ...` → Workflow-shape
5. `Execute the entire TDD cycle from red through green ...` → Workflow-shape

### Body-shape rejection fixtures (Story 6)

Four fixture body snippets, all expected to be rejected:

1. `When working through the issue, Read commands/triage.md and follow the steps.`
2. `Begin by invoking Read skills/foundational-research/SKILL.md to gather context.`
3. `If a deeper analysis is required, dispatch via Task(subagent_type: "review-agent", ...).`
4. `/security-audit will produce the threat report; consume its output.`

### Happy-path fixture

```yaml
---
name: write-conventional-commits
description: "Write commit messages in Conventional Commits format from a diff"
disable-model-invocation: true
---

# Write Conventional Commits

## Purpose
Help an agent write a commit message that conforms to the Conventional Commits 1.0 specification given a staged diff.

## When to Use
Whenever an agent or command needs to author or revise a commit message...
```

This input must pass the lint cleanly.

### Code-block exemption fixture

```yaml
---
name: example-skill
description: "Validate input data against a schema"
---

## How to Apply

For example, when running tests:

```bash
# Run the full test suite to confirm
npm test
```

The phrase "Run the full" appears here, but inside a code block — lint must NOT flag it.
```

## Smoke Skill Spec (Story 3)

### `skills/hello-writ/SKILL.md` content

```yaml
---
name: hello-writ
description: "Demonstrates the skill loading path end-to-end. Throwaway smoke artifact."
disable-model-invocation: true
---

# Hello Writ

## Purpose

Demonstrate that a skill authored in `skills/<name>/SKILL.md` propagates through `gen-skill.sh`, `install.sh`, and lands at the platform-native skill path with frontmatter intact.

## When to Use

Never. This is a smoke artifact and is removed before merge.

## How to Apply

If you are reading this in a non-test context, the cleanup task in Story 3 of `2026-05-03-skills-foundation` did not run. Please open an issue.

## Examples

N/A.
```

### Lifecycle gate

This file is **created in Story 3 task 1** and **deleted in Story 3 final task**. Story 3's PR must show zero net diff for `skills/hello-writ/` against `main`.

## Cross-References

- ADR-009 — Composition rules, file format decision, invocation policy
- Phase 4 spec (`2026-04-24-phase4-production-grade-substrate`) — Manifest pattern this extends
- `scripts/gen-skill.sh` — existing yq + bash parser pattern to extend
- `scripts/install.sh` — existing three-way overlay pattern to mirror
- `cursor/writ.mdc` — Prime Directive parity requirement (mirrors `system-instructions.md`)

## Open Questions (Resolved)

| Question | Resolution | Source |
|---|---|---|
| Should skills include all 3 pilot extractions in this spec? | No — infrastructure only | User decision in contract phase |
| Include `/new-skill` command in this spec? | Yes | User decision in contract phase |
| Create `adapters/codex.md` here? | No — Skills sections in existing 3 adapters only | User decision in contract phase |
| Define `Required skills:` convention now? | Yes — schema + docs, no consumer adoption yet | User decision in contract phase |
| Overlay granularity — folder or SKILL.md? | SKILL.md only; sidecar install-once | Spec → Business Rules |
| Empty skills list rendering | Silent skip (no Skills section) | Spec → Acceptance Scenario 1 (Story 1) |
| Smoke skill name | `hello-writ` | Spec → Risks → mitigation row |
| 90-day review trigger date | 2026-08-03 | Story 5 / ADR-009 review date alignment |
