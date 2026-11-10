---
name: writ-research
description: Answer a question with evidence and a recommendation - why something in this project is the way it is, what the options are, what others do, whether an idea holds up. Use before a decision, not for quick lookups. Part of Writ.
---

# Writ research

Read `../writ/rules.md` first.

A person is about to decide something. Give them an answer they can check.

1. **Pin the question.** State it in one sentence and say which decision it feeds. If you cannot tell what would change depending on the answer, ask.

2. **Look where the answer lives.**
   - *About this project* ("why is it like this?", "what did we decide?"): the project's own record first, meaning the specs, decision records, research, and issues under `.writ/`. Then git history and pull requests. Then any connected tracker, chat, or document store. Code shows what is, not why; do not cite it as evidence of intent.
   - *About the world* (options, competitors, standards, how users behave): primary sources over summaries, recent over old. Give independent threads to separate helpers.

3. **Test what can be tested.** If part of the question can be settled by running something, run it.

4. **Answer.** Lead with the answer and your recommendation. Then the evidence, each claim labelled: confirmed (you ran it or read the source), likely (independent sources agree), or guess. Say what you looked for and did not find. Give the strongest case against your recommendation.

5. **If a change follows,** end with four short lists: what to keep, what to change, what to avoid, and what could go wrong.

Save the answer as `.writ/research/<date>-<name>.md` when it will be needed again or took real work. A quick answer stays in the conversation.
