# Architecture Lint

> **Status:** Guidance. Gate 2 of `/implement-story` runs the rulesets described here; nothing requires a project to have one.
> **Rule source:** spec `2026-09-26-arch-lint-and-follow-ups` (Business Rules 1 and 3); detection lives in [`scripts/arch-lint.py`](../../scripts/arch-lint.py), which wins if this page and the helper ever disagree.
> **Applies:** any project with Writ installed. `scripts/install.sh` ships `.writ/docs/*.md`, so installed projects carry this file.

When a story report says `arch-lint: none — see .writ/docs/architecture-lint.md`, this is the page it means: pick the example below for your ecosystem, commit the file it names, and install the tool; the next Gate 2 enforces it. A detected but uninstalled dependency-cruiser or import-linter reports `not-installed` and runs nothing.

## Why mechanical rules beat judgment

"The domain layer never imports the UI" is easy to agree to and easy to break. The review agent may notice the import or may not; it depends on what else is in the diff, and a reviewer that missed it once will miss it again. A lint rule has no attention to spend: the forbidden import fails every run, the failure names the file and the rule, and nobody has to remember the decision for it to hold.

So Writ treats layering like formatting. A decision about import direction belongs in a ruleset the gate runs, not in a paragraph a reviewer is supposed to recall.

## How Gate 2 finds and runs rulesets

After the existing linters, Gate 2 runs `python3 scripts/arch-lint.py detect --repo .`. The helper is read-only and offline: it looks for the files below, checks `PATH`, and prints what to run. It never installs anything.

| Tool | Detected by | Mode | Command Gate 2 runs |
|---|---|---|---|
| dependency-cruiser | `.dependency-cruiser.js`, `.dependency-cruiser.cjs`, `.dependency-cruiser.mjs` or `.dependency-cruiser.json` at the repo root | `run` when `node_modules/.bin/depcruise` exists, else `not-installed` | a `package.json` script whose body contains `depcruise` → `npm run <name>`; else `npx --no-install depcruise --config <cfg> src` (`.` when there is no `src/`) |
| import-linter | `.importlinter`; an `[importlinter]` section in `setup.cfg`; a `[tool.importlinter]` table in `pyproject.toml` | `run` when `lint-imports` is on `PATH`, else `not-installed` | `lint-imports` |
| eslint-plugin-boundaries | a `dependencies` or `devDependencies` entry in `package.json` | `via-eslint` | none (eslint already runs it) |
| ArchUnit | `archunit` (any case) in `pom.xml`, `build.gradle` or `build.gradle.kts` | `via-tests` | none (the test suite already runs it) |

Only the two standalone checkers get a `command:` line. eslint-plugin-boundaries and ArchUnit are reported, not re-run, because their violations already fail the lint step and the test gate.

A non-zero exit from a `command:` takes Gate 2's existing failure path. None of these tools auto-fix, so a violation is flagged for review. A missing or not-installed ruleset never fails the gate; it only changes the report line:

| Detect result | Story report line |
|---|---|
| runnable tool(s) | `arch-lint: dependency-cruiser` |
| runs elsewhere | `arch-lint: eslint-plugin-boundaries (via eslint)` / `archunit (via tests)` |
| configured, not installed | `arch-lint: import-linter (not installed)` |
| no ruleset | `arch-lint: none — see .writ/docs/architecture-lint.md` |
| unreadable config | `arch-lint: unverifiable (config_unreadable <path>)` |

Run the helper yourself to see what Gate 2 will do before a story does it.

## Examples

Each example encodes the same three-layer rule: `ui` may import `domain`, `domain` may import `data`, and nothing imports upward. Rename the paths to your layers. Each is the smallest ruleset the tool accepts; grow it from there.

### dependency-cruiser: a `forbidden` rule

File: `.dependency-cruiser.json` (the `.js`, `.cjs` and `.mjs` names hold the same object via `module.exports` or `export default`). dependency-cruiser also reads `.ts`, `.cts` and `.mts` configs, but Gate 2 does not detect those names. Each `forbidden` rule fails the run when a module matching `from` imports one matching `to`.

```json
{
  "forbidden": [
    {
      "name": "no-upward-imports",
      "severity": "error",
      "from": { "path": "^src/(domain|data)/" },
      "to": { "path": "^src/ui/" }
    },
    {
      "name": "data-not-to-domain",
      "severity": "error",
      "from": { "path": "^src/data/" },
      "to": { "path": "^src/domain/" }
    }
  ]
}
```

### import-linter: a `layers` contract

File: `.importlinter`, or the same INI in `setup.cfg` (`[importlinter]` section). A `layers` contract lists layers highest first; a lower layer importing a higher one breaks it.

```ini
[importlinter]
root_package = myapp

[importlinter:contract:layers]
name = UI over domain over data
type = layers
layers =
    myapp.ui
    myapp.domain
    myapp.data
```

In `pyproject.toml` the same contract lives under `[tool.importlinter]`:

```toml
[tool.importlinter]
root_package = "myapp"

[[tool.importlinter.contracts]]
name = "UI over domain over data"
type = "layers"
layers = ["myapp.ui", "myapp.domain", "myapp.data"]
```

### eslint-plugin-boundaries: a `dependencies` rule (formerly `element-types`)

Detected through `package.json`; the rule itself goes in `eslint.config.js`. v6 renamed `boundaries/element-types` to `boundaries/dependencies` (the old name still works as a deprecated alias) and v7 renamed its `rules` option to `policies`. The example uses the v7 names. `default: "disallow"` blocks every import between elements that no policy allows.

```js
import boundaries from "eslint-plugin-boundaries";

export default [
  {
    plugins: { boundaries },
    settings: {
      "boundaries/elements": [
        { type: "ui", pattern: "src/ui", partialMatch: false },
        { type: "domain", pattern: "src/domain", partialMatch: false },
        { type: "data", pattern: "src/data", partialMatch: false },
      ],
    },
    rules: {
      // Before v6 this rule was "boundaries/element-types".
      "boundaries/dependencies": [2, {
        default: "disallow",
        policies: [
          { from: { element: { type: "ui" } }, allow: { to: { element: { type: "domain" } } } },
          { from: { element: { type: "domain" } }, allow: { to: { element: { type: "data" } } } },
        ],
      }],
    },
  },
];
```

### ArchUnit: a `layeredArchitecture()` test

Detected through `archunit` in `pom.xml`, `build.gradle` or `build.gradle.kts` (the `com.tngtech.archunit:archunit-junit5` test dependency, or `archunit-junit6` for JUnit 6). The rule is an ordinary test, so it runs wherever the suite runs.

```java
import com.tngtech.archunit.junit.AnalyzeClasses;
import com.tngtech.archunit.junit.ArchTest;
import com.tngtech.archunit.lang.ArchRule;

import static com.tngtech.archunit.library.Architectures.layeredArchitecture;

@AnalyzeClasses(packages = "com.example.myapp")
class LayeredArchitectureTest {
    @ArchTest
    static final ArchRule layers_are_respected = layeredArchitecture().consideringAllDependencies()
            .layer("UI").definedBy("..ui..")
            .layer("Domain").definedBy("..domain..")
            .layer("Data").definedBy("..data..")
            .whereLayer("UI").mayNotBeAccessedByAnyLayer()
            .whereLayer("Domain").mayOnlyBeAccessedByLayers("UI")
            .whereLayer("Data").mayOnlyBeAccessedByLayers("Domain");
}
```

## Relation to ADRs

An ADR records why a boundary exists; a ruleset makes it hold. When a decision constrains layering, import direction, or module dependencies, `/create-adr` asks for an **Enforcement** note: the rule that encodes the decision (for example, "dependency-cruiser rule `no-upward-imports` in `.dependency-cruiser.json`") and a link to this page.

The two stay paired. Superseding the ADR means changing or deleting the rule in the same change. A rule with no ADR behind it is fine for mechanical hygiene, but a boundary someone will ask "why?" about deserves both.
