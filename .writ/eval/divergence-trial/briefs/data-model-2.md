id: data-model-2
medium: data-model

The rule-to-enforcer table /retro keeps for a project.
Who uses it: /retro, which adds entries when it turns a transcript finding into a fix, and a maintainer asking which rules nothing enforces.
A rule is a project convention written in steering files or docs. Its enforcer is what checks it: an architecture constraint, a type, a lint rule, a test, or documentation only.
/retro ranks fixes in that order and proves each new check fails on a real past mistake.
It must answer: which rules have no enforcer, what enforces a given rule, and which past mistake proved a check works.
