<div align="center">
<pre>
/\/\/\/\/\/\/\/\/\/\/\/\/\/\/\/\/\/\/\/\
  ██╗    ██╗██████╗ <span style="color: #FF9900;">  ██╗    </span>████████╗  
  ██║    ██║██╔══██╗<span style="color: #FF9900;">  ╚██╗   </span>╚══██╔══╝  
  ██║ █╗ ██║██████╔╝<span style="color: #FF9900;"> ██████╗ </span>   ██║     
  ██║███╗██║██╔══██╗<span style="color: #FF9900;"> ╚══██╔╝ </span>   ██║     
  ╚███╔███╔╝██║  ██║<span style="color: #FF9900;">   ██╔╝  </span>   ██║     
   ╚══╝╚══╝ ╚═╝  ╚═╝<span style="color: #FF9900;">   ╚═╝   </span>   ╚═╝     
\/\/\/\/\/\/\/\/\/\/\/\/\/\/\/\/\/\/\/\/
</pre>

**Agree what to build. Let the model build it. See proof it works.**

*A writ is a written command by an authority: you.*

</div>

---

## What Writ is

Writ is a way for a product manager and an AI coding agent to work together. It is ten short skills that run in Claude Code, Cursor, and Codex.

- **You decide what and why. The model decides how.** Writ asks you about the problem, the objective, what is in and out, how things should look and read, and whether to merge and release. It does not ask you which library to use.
- **A contract before a build.** One file states the problem, the outcome and its measure, the scope, and how anyone could tell it is done. Nothing is built until you agree it, and it cannot change without you.
- **Proof, not a report.** A verifier that did not write the change checks every line of the contract against the running product, writes down what it ran and what it saw, and gives you steps to try it yourself.
- **Plain files in git.** Your plan, contracts, decisions, and proofs live under `.writ/` and outlast any session, model, or tool.

## How it goes

Type `/writ` and say what you want, in your own words.

```
/writ people keep abandoning signup at the email-verification step
```

Writ says it back as a goal, a problem, and a done-when, picks the step that fits, and starts. From there:

| Step | What happens | What it asks of you |
|---|---|---|
| `/writ` | Start anything, or ask where things stand and what is waiting on you | Whether it understood the goal |
| `/writ-plan` | Who the product serves, the objective and its measure, the bets in order | The user, the objective, what comes first |
| `/writ-research` | An answer with evidence and a recommendation | The question; whether to take the recommendation |
| `/writ-prototype` | Two or three working drafts to compare | Which one |
| `/writ-spec` | The contract for one change | What is in, what is out, what done means |
| `/writ-build` | The model builds it its own way and has it verified | Only changes to the contract |
| `/writ-verify` | Independent proof against the running product | What only a person can judge |
| `/writ-ship` | Pull request, then merge and release | When to merge; when to release |
| `/writ-issue` | A bug or idea captured in two minutes | Nothing |
| `/writ-retro` | Did it move the measure, and what changes next | Which changes to make |

You can start at any step. A small fix goes straight from `/writ` to built and verified with no spec file.

In Codex, type `$writ` in place of `/writ`. Under the Claude Code plugin the names read `/writ:writ`, `/writ:writ-build`, and so on; typing `writ-build` finds them.

## Install

### Claude Code (terminal and desktop)

```bash
claude plugin marketplace add sellke/writ
```

```bash
claude plugin install writ@writ
```

### Cursor, Codex CLI, and the ChatGPT desktop app

From your project's root:

```bash
bash <(curl -fsSL https://raw.githubusercontent.com/sellke/writ/main/scripts/install.sh)
```

This copies the skills into `.agents/skills/`, which Cursor and Codex both read. It commits nothing. Restart or reload the tool afterwards.

| Flag | Effect |
|---|---|
| `--platform claude` | Install into `.claude/skills/`, for Claude Code without the plugin. Repeat `--platform` to install for several tools |
| `--global` | Install for every project, under your home folder |
| `--dry-run` | Show what would happen and change nothing |
| `--uninstall` | Remove what was installed, keeping any file you changed |
| `--force` | Overwrite files you changed |

**Updating:** run the same line again. Files you have not touched are updated. Files you changed are kept and listed.

**Coming from Writ 0.x:** the installer stops and prints the one command that removes the old install. Everything under `.writ/` stays. Specs written with 0.x still build: `/writ-build` reads the old `spec.md` as the contract.

## What Writ keeps in your project

```
.writ/
├── product/
│   ├── mission.md        who the product serves, the objective and its measure
│   └── roadmap.md        the bets, in order
├── specs/<date>-<name>/
│   ├── spec.md           one contract: problem, outcome, scope, criteria, decisions, proof
│   └── proof/            what the verifier ran and saw
├── prototypes/           drafts that were compared, and which won
├── research/             questions, evidence, recommendations
├── decision-records/     changes of direction and why
└── issues/               bugs and ideas for later
```

Folders appear when they are first needed. There is no setup step.

## A second reader (optional)

`writ-jev` adds [TypeSafe's Jev](https://docs.typesafe.ai/introduction) as a second reader of the two documents you decide from. Before you agree a contract, it flags criteria that two people could read differently, that contradict each other, or that leave a case out. Before you read a proof, it flags lines whose evidence does not show what they claim.

It only points. It never decides anything, and Writ works the same without it. It is off until you add a provider line to `.writ/config.md` and set the provider's API key; `/writ-jev` walks you through it. When on, it sends the contract's text and the proof's evidence text to the provider.

## Developing Writ

The product is the folder [`plugins/writ/`](plugins/writ/): the skills and three small plugin manifests. Nothing is generated and nothing is copied.

```bash
python3 scripts/check.py
```

```bash
uv run --isolated --python 3.9 --with pytest pytest
```

```bash
for t in scripts/tests/test_*.sh; do bash "$t" || echo "FAIL $t"; done
```

`check.py` fails when a skill's name and folder disagree, when a skill points at a file or skill that does not exist, when a platform tool name appears in a skill, when a manifest's version differs from `VERSION`, or when this README leaves a skill out.

Why Writ is shaped this way: [mission](.writ/product/mission.md), [roadmap](.writ/product/roadmap.md), and [ADR-034](.writ/decision-records/adr-034-product-manager-audience.md) to [ADR-037](.writ/decision-records/adr-037-jev-second-reader.md). Versions before 1.0 are at tag `v0.49.0`.

## Attribution

Writ is derived from [Code Captain](https://github.com/devobsessed/code-captain) by [@DevObsessed](https://github.com/devobsessed), originally released under the MIT License. Its build and verification principles draw on [pstack](https://github.com/cursor/plugins/tree/main/pstack) by Lauren Tan.

## License

MIT. See [LICENSE](LICENSE).
