# Memories

A library of **generalized, loosely coupled memories**: engineering truths, architectural patterns, and debugging lessons distilled from real project memories, with everything project-specific removed. Any developer or coding agent (Claude Code, Codex, Grok, …) can ingest one of these files into their own memory ecosystem and gain value from it immediately.

## Why loose coupling is mandatory

A raw project memory is full of tight coupling: absolute paths, project and product names, personal names and dates, session IDs, `[[links]]` to sibling memories that only exist in the source project, and references to incidents only that project's history explains. Any one of these makes the memory useless — or actively misleading — in another codebase. Every memory in this library must pass the decoupling standard below before it lands.

## The decoupling standard

1. **No local environment references.** Replace paths, project names, and naming conventions with `[BRACKET_PLACEHOLDERS]` (e.g. `[YOUR_APP_NAME]`, `[PACKAGE_MANAGER]`). The installing agent fills these from the target project's context at install time.
   *Note:* `[BRACKETS]` here are deliberately different from the `{{TOKENS}}` used by the command templates in `commands/`. Those are filled mechanically by `/get-started` at install time; these are filled contextually by whichever agent ingests the memory.
2. **Extract the core truth.** The memory must state an engineering truth, architectural pattern, or debugging lesson that applies to any codebase using a similar tech stack — not a fact about one repo. If a project memory has no portable core, it does not belong here.
3. **Standard structure.** Every memory uses the frontmatter + three-section shape in [`TEMPLATE.md`](TEMPLATE.md):
   - **Context / Trigger** — the situation, task type, or symptom that should make an agent recall this memory.
   - **Core Rule / Insight** — the truth itself. Concrete techniques, named public tools, and external links belong here; they are the payload, not coupling.
   - **Expected Outcome** — what following the rule produces, and what ignoring it costs.
4. **No provenance.** Names, dates, session IDs, tool-generated metadata (`originSessionId`, `modified`, …), and `[[links]]` to memories outside this library are stripped entirely. The memory stands on its content.

External URLs (galleries, upstream repos, public docs) are **not** coupling — they are globally reachable and usually the most valuable part. Keep them.

The bar, always: **a stranger with a similar tech stack must be able to ingest the memory and gain value with zero knowledge of the source project.**

## Installing a memory

The intended workflow: clone this repo, then point your coding agent at a memory file and tell it one of:

> Install `memories/<name>.md` at the user level.

> Install `memories/<name>.md` in this project.

> Install `memories/<name>.md` for `/path/to/project`.

### Instructions for the installing agent

You are a coding agent that has been asked to install one of these memory files. Do the following:

1. **Read the memory file fully.**
2. **Resolve the placeholders.** Fill every `[BRACKET_PLACEHOLDER]` from what you know about the target project (its name, package manager, stack, conventions). Prefer resolving; leave a placeholder only if it is genuinely generic in context.
3. **Check for duplicates.** If the target memory store already holds a memory covering the same truth, update that one instead of adding a duplicate.
4. **Write it into your own memory system.** Adapt to whichever agent you are:
   - **Claude Code — project level** (the user said "this project" or gave a project path): the project memory directory is `~/.claude/projects/<munged-path>/memory/`, where `<munged-path>` is the target project's absolute path with each `/` replaced by `-` (e.g. `/Users/me/code/myapp` → `-Users-me-code-myapp`). If your own system prompt names your memory directory, trust that over this derivation. Write the file there (create the directory if needed), then add a one-line pointer to `MEMORY.md` in the same directory — `- [Title](<name>.md) — <one-line hook>` — creating `MEMORY.md` if it is missing.
   - **Claude Code — user level**: copy the file to `~/.claude/memories/<name>.md` and add an import line `@~/.claude/memories/<name>.md` to `~/.claude/CLAUDE.md`. If imports are not available in your version, append the memory body under a `## Memories` heading in `~/.claude/CLAUDE.md` instead.
   - **Agents without a file-based memory system** (Codex and similar): append the memory body under a `## Memories` heading in your instruction file — the project's `AGENTS.md` (or equivalent) for a project-level install, your user-level instruction file (e.g. `~/.codex/AGENTS.md`) for a user-level install.
5. **Report back**: where you wrote the memory, and which placeholders you resolved to which values.

## Adding a memory to this library

Use the **`/memorize`** command (installed by `/get-started`): point it at a raw project memory file and it audits the coupling, extracts the portable core, restructures it to the standard above, and drafts it here for your review before anything is written.

Or do it by hand: copy [`TEMPLATE.md`](TEMPLATE.md), apply the decoupling standard, and commit.
