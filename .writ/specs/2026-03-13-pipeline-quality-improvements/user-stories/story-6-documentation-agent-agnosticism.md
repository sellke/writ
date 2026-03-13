# Story 6: Documentation Agent Framework Agnosticism

> **Status:** Completed ✅
> **Priority:** Medium
> **Dependencies:** None

## User Story

**As a** developer using Writ on a project that doesn't use VitePress
**I want** the documentation agent to detect and adapt to my project's documentation framework
**So that** documentation updates match my actual setup instead of assuming VitePress

## Acceptance Criteria

- [x] Given a project uses Docusaurus, when the documentation agent runs, then it creates/updates docs following Docusaurus conventions (sidebars.js, docs/ structure)
- [x] Given a project uses no documentation framework, when the documentation agent runs, then it defaults to inline JSDoc/docstrings and README.md updates — not attempting to create a VitePress site
- [x] Given the documentation agent's prompt, when it starts, then it runs a detection phase before any documentation work — checking for .vitepress/, docusaurus.config.js, nextra, mkdocs.yml, .storybook/, or plain README
- [x] Given the detection identifies a framework, when documentation is generated, then framework-specific conventions are followed (sidebar config, page structure, routing)

## Implementation Tasks

- [x] 6.1 Read current `agents/documentation-agent.md` to understand the VitePress-centric structure
- [x] 6.2 Add a Detection Phase (Step 0) to the agent prompt — detect documentation framework by checking for config files: `.vitepress/config.ts`, `docusaurus.config.js`, `next.config.js` + nextra, `mkdocs.yml`, `.storybook/`, or plain README
- [x] 6.3 Restructure the Documentation Tasks section — branch based on detected framework. Move current VitePress-specific content into a VitePress branch. Add a "No Framework (default)" branch for inline docs + README.
- [x] 6.4 Add brief framework-specific guidance for Docusaurus (sidebar config, MDX pages), Nextra (pages/ directory), MkDocs (mkdocs.yml nav), and Storybook (story files)
- [x] 6.5 Update the Documentation Structure section to show it as framework-dependent rather than hardcoded VitePress
- [x] 6.6 Verify the "No Framework" default path is robust — inline JSDoc for public APIs, README section updates, CHANGELOG entry. This should be the most common path.

## Notes

- The current prompt has a good structure for VitePress — it doesn't need to be removed, just gated behind framework detection.
- The "No Framework" path should be the primary path since most projects using Writ won't have a documentation site. It should feel like a first-class citizen, not a fallback.
- Framework-specific guidance doesn't need to be as detailed as the VitePress section — just enough for the agent to create/update files in the right places with the right format.
- Only touches `agents/documentation-agent.md`.

## Definition of Done

- [x] All tasks completed
- [x] All acceptance criteria met
- [x] `agents/documentation-agent.md` has framework detection phase
- [x] VitePress content preserved but gated behind detection
- [x] "No Framework" default path is robust and well-documented
