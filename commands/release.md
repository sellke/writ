# Release Command (release)

## Overview

Automate the release lifecycle: generate changelogs from completed stories, bump version numbers, create git tags, and optionally publish GitHub releases.

**Self-sufficient:** `/release` runs an **inline release gate** (spec metadata validation, build verification, conditional test suite) before changelog generation, unless `--skip-gate` is set.

## Modes

| Invocation | Mode | Behavior |
|---|---|---|
| `/release` | Interactive | Run release gate (unless skipped), then detects changes since last release, proposes version bump |
| `/release patch` | Explicit | Force a patch release (0.0.X) |
| `/release minor` | Explicit | Force a minor release (0.X.0) |
| `/release major` | Explicit | Force a major release (X.0.0) |
| `/release --dry-run` | Preview | Show gate preview + what would happen without making changes |
| `/release --no-tag` | Changelog only | Generate changelog and bump version, skip git tag + GitHub release |
| `/release --skip-gate` | Bypass validation | Skip spec validation, build verification, and test suite (use when CI already validated) |

## Command Process

### Phase 1: Release Context Gathering

#### Step 1.1: Detect Current State

**Auto-detect version source:**
```bash
# Check in order of priority:
1. package.json         → "version" field (Node/Bun)
2. Cargo.toml           → [package] version (Rust)
3. pyproject.toml       → [project] version or [tool.poetry] version (Python)
4. setup.py / setup.cfg → version field (Python legacy)
5. VERSION file         → plain text version
6. Git tags             → latest semver tag (v*.*.*)
7. None found           → start at 0.1.0
```

**Gather release context:**
```bash
# Current version
CURRENT_VERSION=$(detected above)

# Last release tag
LAST_TAG=$(git describe --tags --abbrev=0 2>/dev/null || echo "none")

# Commits since last release
COMMITS=$(git log ${LAST_TAG}..HEAD --oneline)

# Completed specs since last release
SPECS=$(scan .writ/specs/ for specs completed after last release date)
```

#### Step 1.2: Analyze Changes

**Categorize all changes since last release:**

1. **From completed specs/stories:**
   - Read all `user-stories/README.md` files
   - Extract completed stories with their titles and descriptions
   - Categorize: feature, fix, refactor, docs, chore

2. **From git history:**
   - Parse conventional commits if used (`feat:`, `fix:`, `docs:`, `BREAKING CHANGE:`)
   - Fall back to commit message analysis
   - Identify files changed per commit

3. **Breaking change detection:**
   - Look for `BREAKING CHANGE` in commit messages
   - Check if public API signatures changed
   - Check if database migrations are destructive
   - Check if environment variables were added/removed/renamed

#### Step 1.3: Release Gate

Unless `--skip-gate` is set, run **before** README freshness and version proposal. If any **blocking** step fails (build verification or test suite), stop — do not generate changelog or bump versions.

**1.3a: Spec metadata validation**

For **completed specs** relevant to this release (same inventory you use for changelog context — e.g. specs marked complete or stories done since `LAST_TAG`):

- Run `/verify-spec` **checks 1–5 and 8** inline against each applicable spec (same logic as the standalone command).
- **Auto-fix** discrepancies the same way `/verify-spec` default mode would.
- **Unfixable issues** (e.g. Check 4/8 findings needing judgment): emit **warnings** and continue — do not block the release unless the team policy treats a finding as critical (default: warn only).

**1.3b: Build verification (always runs)**

Fast checks; run only when tooling/config is present — do not fail the repo for missing tools:

Run each check **only** when configuration exists (probe for `tsconfig.json`, ESLint config variants, Prettier config variants — same heuristics as `/ship`). Example pattern:

```bash
[ -f tsconfig.json ] && npx tsc --noEmit
# eslint / prettier: run only after detecting a config file for that tool
```

If a tool is not configured, skip it — **do not** treat “no config” as failure.

**On failure:** Block release. Report which command failed and where.

**1.3c: Conditional test suite**

```bash
LAST_MERGED_SHA=$(gh pr list --state merged --limit 1 --json mergeCommit --jq '.[0].mergeCommit.oid' 2>/dev/null)
HEAD_SHA=$(git rev-parse HEAD)
```

| Condition | Behavior |
|---|---|
| `gh` unavailable, errors, or returns empty | Log `gh CLI unavailable or no merge data — running full test suite` → run **full** suite |
| `LAST_MERGED_SHA` equals `HEAD_SHA` | Log `Tests skipped — HEAD matches last merged PR (${HEAD_SHA}). Build verification still runs.` → **skip** test suite |
| Otherwise | Run **full** test suite |

**Test runner:** Use the same detection chain as `/ship` Step 1 (`npm test`, `pytest`, `cargo test`, `make test`, etc.).

**On test failure:** Block release. Suggest fixing and re-running, or `--skip-gate` only if the user explicitly accepts skipping validation.

**`--dry-run` preview:** State whether the gate **would** run, whether tests **would** run vs skipped (include resolved `HEAD_SHA` and whether `gh` produced a merge SHA), and that build + spec steps **would** always run except when `--skip-gate`.

#### Step 1.4: README Freshness Check

Cross-reference `README.md` against the actual repo to catch silent staleness — the release is the natural checkpoint because you're already enumerating what changed.

**Automated checks:**

| Check | How | Flag when |
|---|---|---|
| Commands table | Compare `commands/*.md` filenames against every command listed in README tables | File exists with no README entry, or README lists a command with no file |
| Agents table | Compare `agents/*.md` against README agents table | Same — missing or stale entries |
| Pipeline diagram | Verify commands named in the ASCII pipeline still exist | Diagram references a renamed or removed command |
| Install URLs | Verify repo name and branch in install/update `curl` commands match `git remote` | URL points to wrong repo or non-existent branch |

**On all checks pass:** Continue silently — `📋 README: ✅ current`.

**On discrepancies found:**

```
⚠️ README discrepancies detected:

- commands/foo.md exists but is not listed in any README table
- README lists /bar but commands/bar.md does not exist
- Install URL references 'sellke/old-name', remote is 'sellke/writ'

Options:
1. Fix now — I'll update README.md, include in the release commit
2. Skip — release without README changes
3. Abort — fix manually first
```

I recommend **option 1** (fix now) — bundling the README fix into the release commit is the cleanest outcome. The discrepancy was already shipped; the release is the right moment to heal it.

**What this check does NOT do:** Validate that command *descriptions* in the README are accurate. Descriptions are judgment calls — the check catches structural drift (missing/extra entries), not semantic drift. If a command's purpose fundamentally changed, the changelog entry is the signal to review its README description manually.

#### Step 1.5: Propose Version Bump

**Automatic determination:**
| Changes Found | Suggested Bump | Reason |
|---|---|---|
| `BREAKING CHANGE` present | **Major** (X.0.0) | Public API contract changed |
| New features (specs completed) | **Minor** (0.X.0) | New functionality added |
| Bug fixes only | **Patch** (0.0.X) | No new features |
| Docs/chore only | **Patch** (0.0.X) | Non-functional changes |

**Present proposal:**
```
AskQuestion({
  title: "Release Planning",
  questions: [
    {
      id: "version_bump",
      prompt: `Current version: ${CURRENT_VERSION}\nChanges detected: ${change_summary}\n\nSuggested bump:`,
      options: [
        { id: "suggested", label: "${SUGGESTED_BUMP}: ${CURRENT} → ${NEW_VERSION} (recommended)" },
        { id: "patch", label: "Patch: ${CURRENT} → ${patch_version}" },
        { id: "minor", label: "Minor: ${CURRENT} → ${minor_version}" },
        { id: "major", label: "Major: ${CURRENT} → ${major_version}" },
        { id: "custom", label: "Custom version (I'll specify)" },
        { id: "preview", label: "Show full changelog preview first" }
      ]
    }
  ]
})
```

### Phase 2: Changelog Generation

> **Order:** Phase 2 runs only after Phase 1 completes successfully (including the release gate unless `--skip-gate`).

#### Step 2.1: Generate Changelog Entry

**Format: [Keep a Changelog](https://keepachangelog.com/)**

```markdown
## [X.Y.Z] - YYYY-MM-DD

### Added
- Feature description from completed story ([Story N: Title])
- Another new feature ([Story M: Title])

### Changed
- Modification description ([Story N: Title])

### Fixed
- Bug fix description ([commit hash or story ref])

### Security
- Security improvement description (if any)

### Breaking Changes
- Description of what changed and migration path (if any)

### Internal
- Refactoring, dependency updates, CI changes (optional section)
```

**Source priority for descriptions:**
1. Story titles + acceptance criteria summaries (richest context)
2. Conventional commit messages
3. Spec contract summaries
4. Raw commit messages (last resort)

**Quality rules:**
- Write for users, not developers (unless it's a library)
- Each entry should be a complete sentence
- Link to stories/specs where possible
- Group related changes
- Don't list every commit — summarize logical changes

#### Step 2.2: Update CHANGELOG.md

**If CHANGELOG.md exists:** Prepend new entry after the header.

**If CHANGELOG.md doesn't exist:** Create it with standard header:
```markdown
# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/),
and this project adheres to [Semantic Versioning](https://semver.org/).

## [X.Y.Z] - YYYY-MM-DD
...
```

#### Step 2.3: Preview and Confirm

Present the full changelog entry:
```
## Changelog Preview

[Full changelog entry shown here]

---
Files to update:
- CHANGELOG.md (new entry prepended)
- package.json (version: X.Y.Z)
- [other version files detected]
```

```
AskQuestion({
  title: "Confirm Release",
  questions: [
    {
      id: "confirm",
      prompt: "Proceed with this release?",
      options: [
        { id: "yes", label: "Create release" },
        { id: "edit", label: "Edit the changelog first" },
        { id: "bump_only", label: "Bump version + changelog, skip git tag" },
        { id: "abort", label: "Cancel release" }
      ]
    }
  ]
})
```

### Phase 3: Version Bump

#### Step 3.1: Update Version Files

**Update all detected version sources:**

```bash
# Node/Bun — package.json (and package-lock.json / bun.lock if present)
npm version ${VERSION} --no-git-tag-version 2>/dev/null || \
  jq ".version = \"${VERSION}\"" package.json > tmp && mv tmp package.json

# Also check for version in:
# - package-lock.json
# - bun.lock (may auto-update on next install)

# Python — pyproject.toml
sed -i "s/^version = .*/version = \"${VERSION}\"/" pyproject.toml

# Rust — Cargo.toml
sed -i "s/^version = .*/version = \"${VERSION}\"/" Cargo.toml

# VERSION file
echo "${VERSION}" > VERSION
```

#### Step 3.2: Commit Release

```bash
git add -A
git commit -m "chore: release v${VERSION}

## Changes
${changelog_summary}

Generated by Writ /release"
```

### Phase 4: Tag & Publish

#### Step 4.1: Create Git Tag

```bash
git tag -a "v${VERSION}" -m "Release v${VERSION}

${changelog_entry}"
```

#### Step 4.2: Push

```bash
git push origin HEAD
git push origin "v${VERSION}"
```

#### Step 4.3: GitHub Release (Optional)

**Detect if gh CLI is available and authenticated:**

```bash
gh release create "v${VERSION}" \
  --title "v${VERSION}" \
  --notes "${changelog_entry}" \
  --latest
```

**If `gh` is not available:** Skip and inform user:
```
✅ Release v${VERSION} tagged and pushed.

GitHub Release was skipped (gh CLI not available).
Create manually at: https://github.com/${owner}/${repo}/releases/new?tag=v${VERSION}
```

### Phase 5: Release Summary

```
✅ Release v${VERSION} complete!

## Summary
- **Version:** ${PREVIOUS} → ${VERSION}
- **Changelog:** Updated with ${N} entries
- **README:** ✅ Current / 🔧 Updated (N fixes)
- **Tag:** v${VERSION} pushed to origin
- **GitHub Release:** ✅ Created / ⏭️ Skipped

## Changes Released
${changelog_summary}

## What's Next
- Verify CI/CD pipeline picks up the tag
- Monitor deployment if auto-deploy is configured
- Update any external documentation or announcements
```

---

## Dry Run Mode (`--dry-run`)

When `--dry-run` is specified, the command:
1. ✅ Gathers all context (versions, commits, specs)
2. ✅ **Previews the release gate** — spec checks that would run, build commands that would run, and whether the **test suite would run or be skipped** (HEAD vs last merged PR via `gh`, or full suite if `gh` unavailable)
3. ✅ Runs README freshness check (read-only assessment)
4. ✅ Generates the changelog entry (display only)
5. ✅ Shows the version bump proposal
6. ✅ Displays exactly what files would change
7. ❌ Does NOT modify any files
8. ❌ Does NOT commit, tag, or push

Output:
```
🏃 DRY RUN — No changes will be made

Release gate preview:
- Spec metadata (same as `/verify-spec` checks 1–5, 8): would run on [N] spec(s); auto-fix where applicable
- Build verification: typecheck/lint/format where configured — would run
- Tests: would run | would skip (HEAD matches last merged PR SHA …) | would run (gh unavailable — safe default)

Current version: 1.2.3
Proposed version: 1.3.0 (minor — new features detected)

README check: ✅ Current (or: ⚠️ 2 discrepancies — details above)

Changelog entry that would be generated:
[full entry]

Files that would be modified:
- CHANGELOG.md (prepend new entry)
- package.json (version: 1.2.3 → 1.3.0)

Commands that would run:
- git add -A
- git commit -m "chore: release v1.3.0 ..."
- git tag -a v1.3.0 -m "..."
- git push origin HEAD
- git push origin v1.3.0
- gh release create v1.3.0 ...

Run `/release minor` to execute for real.
```

---

## Monorepo Support

For monorepos with multiple packages:

```
AskQuestion({
  title: "Monorepo Release",
  questions: [
    {
      id: "scope",
      prompt: "Which package(s) to release?",
      options: [
        // Dynamically populated from detected packages
        { id: "all", label: "All changed packages" },
        { id: "pkg_1", label: "@scope/package-a (3 changes)" },
        { id: "pkg_2", label: "@scope/package-b (1 change)" }
      ]
    }
  ]
})
```

Each package gets its own version bump and changelog entry. Tags follow the pattern `@scope/package@version`.

---

## Integration with Writ

| Command | Relationship |
|---------|-------------|
| `/implement-spec` | Finishes implementation and per-story tests; often followed by `/ship` |
| `/ship` | Opens the PR; default path toward merging |
| `/verify-spec` | **Optional** metadata diagnostic — not a prerequisite; `/release` re-runs the same checks internally |
| `/status` | Quick check before releasing |

**Recommended release flow:**
```
/release --dry-run             # Preview gate + changelog + version
/release                       # Execute (gate runs again for real unless --skip-gate)
```

Run `/verify-spec` when you want a **standalone** spec hygiene pass without cutting a release.

## Error Handling

**No changes since last release:**
```
ℹ️ No releasable changes found since v${LAST_VERSION}.

Commits since last release: ${N}
But none are features, fixes, or breaking changes.

Options:
1. Force a release anyway (chore/docs changes)
2. Cancel
```

**Dirty working tree:**
```
⚠️ Working tree has uncommitted changes.

Modified files:
${git_status}

Options:
1. Stash changes, release, then restore
2. Commit changes first, then release
3. Cancel
```

**No version source found:**
```
ℹ️ No version file detected. Starting at v0.1.0.

I'll create a VERSION file to track releases.
Proceed?
```
