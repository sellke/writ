# User Stories — Codex CLI Adapter

> Spec: `.writ/specs/2026-05-06-codex-cli-adapter/spec.md`

## Stories Summary

| # | Story | Status | Priority | Dependencies | Tasks | ACs |
|---|---|---|---|---|---|---|
| 1 | [ADR-009 Amendment & Skills Path Correction](story-1-adr-amendment-and-skills-path.md) | Complete ✅ | High | — | 7 | 5 |
| 2 | [Codex TOML Agent Translations & Parity Lint](story-2-codex-agent-translations.md) | Complete ✅ | High | 1 | 8 | 6 |
| 3 | [Codex Adapter Doc & AGENTS.md Block Template](story-3-codex-adapter-doc-and-agents-md-template.md) | Complete ✅ | High | 2 | 7 | 5 |
| 4 | [install.sh `--platform codex` Support](story-4-install-platform-codex.md) | Complete ✅ | High | 1, 2, 3 | 7 | 6 |
| 5 | [Lifecycle Scripts `--platform codex` Parity](story-5-lifecycle-scripts-codex-parity.md) | Complete ✅ | High | 4 | 7 | 5 |
| 6 | [Lifecycle Commands Codex Branches](story-6-lifecycle-commands-codex.md) | Complete ✅ | Medium | 5 | 7 | 5 |
| 7 | [README, End-to-End Smoke & Issue Writeback](story-7-readme-smoke-and-issue-writeback.md) | Complete ✅ | Medium | 6 | 7 | 4 |

**Totals:** 7 stories · 50 tasks · 36 acceptance criteria

## Progress

```
Stories complete: 7 / 7   (100%)
Tasks complete:   50 / 50  (100%)
```

## Dependency Graph

```
Story 1 (foundation: ADR amendment + SKILLS_DIR indirection)
   ↓
Story 2 (TOML translations + parity lint)
   ↓
Story 3 (adapter doc + AGENTS.md/config templates)
   ↓
Story 4 (install.sh --platform codex + AGENTS.md merger) ✅
   ↓
Story 5 (update.sh, unlink.sh, uninstall.sh parity) ✅
   ↓
Story 6 (/update-writ, /reinstall-writ, /uninstall-writ Codex branches) ✅
   ↓
Story 7 (README + end-to-end smoke + source-issue writeback) ✅
```

The graph is linear by design — each story closes a load-bearing piece the next one depends on. No parallel execution opportunities at the story level (parallelism lives inside Story 2's TOML authoring and Story 4's bash fixture work). All stories are complete; final Codex CLI smoke ran on `codex-cli 0.128.0`.

## Story Sizing

| Story | Estimated complexity | Why |
|---|---|---|
| 1 | Small | ADR amendment (paragraphs) + variable indirection refactor (small bash diff with regression check) |
| 2 | Medium | Seven TOML files + parity lint extension to existing command |
| 3 | Medium | Adapter doc matching `claude-code.md` depth + two template files with size budget |
| 4 | Large | New `merge_agents_md()` logic + new `seed_codex_config()` + variable wiring + bash test fixtures |
| 5 | Medium | New `remove_agents_md_block()` helper + three platform branches mirroring Story 4 patterns |
| 6 | Small | Mostly Markdown editing — Codex platform-detection branches in three command files |
| 7 | Medium | README update is small; smoke verification is the highest-confidence work in the spec |

## Cross-Cutting Concerns

- **AGENTS.md byte-stability outside markers** is a contract enforced across Stories 4, 5, and 7. The bash test fixtures in 4.1 and 5.1 plus the smoke verification in 7.2/7.3 form the verification chain.
- **Platform regression-clean** for Cursor and Claude Code is checked at every script-touching story (1, 4, 5, 6) — drift is the spec's hardest-constraint risk.
- **`/refresh-command --check-parity`** is built in Story 2 and exercised one final time in Story 7 to confirm zero drift at ship time.

## Next Steps

- Optional: run `/verify-spec` for a standalone metadata pass.
- Ship the Codex CLI adapter changes after review.

After all 7 stories ship:
- `.writ/issues/features/2026-04-02-codex-openclaw-lifecycle-support.md` `spec_ref` is set
- A follow-up spec is needed for the OpenClaw half of that issue
- Optional follow-up specs (out of scope here): Codex hooks integration, plugin packaging
