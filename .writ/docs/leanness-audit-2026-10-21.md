# Leanness Audit — 2026-10-21

> **Ritual:** Tier B, per phase close ([format](leanness-audit-format.md)). Run at the close of Phase 13 (Subtract and Repair).
> **Tree audited:** `phase/13-subtract-and-repair` at `ef65139`. The phase delta compares against `953f47e`, the commit that added the Phase 13 specs.
> **Previous audit:** [2026-07-18](leanness-audit-2026-07-18.md). The ritual lapsed for three months; ADR-030 restarted it.

## Metrics Snapshot

From `python3 scripts/eval-leanness.py` (`metrics` block).

| Surface | Baseline (2026-08-04) | Phase 13 start (`953f47e`) | Now (`ef65139`) | Phase 13 delta |
|---|---|---|---|---|
| commands | 10,974 lines / 514,594 chars | 13,428 / 721,522 | 11,289 / 584,343 | −2,139 lines / −137,179 chars |
| agents | 1,768 / 67,012 | 2,081 / 85,902 | 2,081 / 85,902 | 0 |
| skills | 932 / 41,620 | 2,045 / 88,339 | 2,034 / 87,563 | −11 / −776 |
| adapters | 1,677 / 84,865 | 1,758 / 95,187 | 1,781 / 100,824 | +23 / +5,637 |
| scripts | 27,210 / 1,155,797 | 87,084 / 3,761,989 | 94,320 / 4,080,973 | +7,236 / +318,984 |
| system_instructions | — | 82 / 4,572 | 82 / 4,572 | 0 |

- `total_product_lines`: 106,478 → 111,587. `total_product_chars`: 4,757,511 → 4,944,177.
- `writ_workspace_lines`: 205,226 (ungated).
- `story_context_bytes`: 63,582 → 63,644. *Note from the tool:* this is a mixed measurement. Its `context_hints` component is real delivered bytes from `scripts/story-context.py`. The other components are a declared-load proxy of what `implement-story.md` Step 2 says it loads. Neither half is measured tokens.
- Legacy keys: `command_lines` 11,289, `command_chars` 584,343. Counts: 33 commands, 8 agents, 16 skills.
- Warnings: 17, all non-blocking. Every surface is past a justified ceiling recorded in August. Six commands are over the 24,960-byte per-invocation budget. The worst are `create-spec.md` at 38,562 bytes (154%, down from about 215%) and `implement-phase.md` at 34,881 bytes (140%).

**What moved in Phase 13.**
- **Commands fell by 16% (lines).** The five lean siblings were deleted. `create-spec.md` lost 15,050 bytes of coaching. Links to Writ's development history were stripped.
- **Scripts grew by 8% (lines).** The `scripts` surface includes `scripts/tests/`, so most of the growth is new tests that pin Phase 13's fixes. The new generators (`gen-claude-md.py`, plus `gen-claude-agents.py` from a peer spec) and two new eval helpers make up the rest.
- **Adapters grew slightly.** That is the canvas-preview rows.

## Findings → Decisions

| Surface | Finding | Decision | Follow-up |
|---|---|---|---|
| `.writ/docs/leanness-audit-*.md`, `swot-2026-03-01.md`, `.writ/explanations/` | Dev-only governance records ship to every installed project. `is_shippable_writ_doc` excludes only the state-format doc. This audit is itself one more such file. | **prune** (from the ship set; keep in the repo) | [`2026-10-21-dev-only-docs-ship-to-users`](../issues/improvements/2026-10-21-dev-only-docs-ship-to-users.md) |
| `scripts` surface metric | The metric counts tests together with shipped scripts. A phase that adds regression tests reads as bloat, and a growth in shipped script lines is hidden inside test growth. | **defer** | [`2026-10-21-leanness-metric-refresh`](../issues/improvements/2026-10-21-leanness-metric-refresh.md) |
| Justified ceilings in `.writ/leanness-baseline.json` | Every ceiling dates from August. All 17 warnings are standing, so none carries signal. Commands fell in Phase 13, but the ratchet did not record the drop. | **defer** | [`2026-10-21-leanness-metric-refresh`](../issues/improvements/2026-10-21-leanness-metric-refresh.md) |
| `commands/implement-phase.md` (34,881 bytes) | Now the largest command after `create-spec.md`. It is the next candidate for a coaching-only reduction pass like Phase 13's, with a cut log. | **defer** | [`2026-10-21-leanness-metric-refresh`](../issues/improvements/2026-10-21-leanness-metric-refresh.md) |
| `recommend-state.py` (3,807 lines) and its eval checks | Dev-only since Phase 13. It is kept as ADR-013's preserved staging design and is no longer shipped. Its maintenance cost remains in the source repo. | **defer** | Roadmap Phase 16: the ceiling ADR decides whether the staging design is still wanted |
| `commands/writ-design.md` Mode A (Excalidraw) | Claude Code now ships native `/design` artboards (secondary reporting). Mode A's hand-authored Excalidraw is a 2024 technique. | **defer** | Roadmap parking lot, "`/design` Mode A modernization" |
| Install via `install.sh` copy (native displacement test) | Cursor and Claude Code both have plugin marketplaces, and a peer project (pstack) installs through them. | **keep** for now | Roadmap Phase 14, plugin distribution |
| Front door (Phase 14) vs `/status` "what to do next" | The two will overlap once the front door exists. Settle it in the front-door spec, not here. | **defer** | Roadmap Phase 14, front door |
| `skills/` | No change in Phase 13. `design-divergence` is planned as the 17th skill in Phase 15, with a removal trial. | **keep** | — |

## Recommend-Only Guarantee

This audit deletes nothing. Each non-keep row routes to an issue or roadmap entry for a human to act on.
