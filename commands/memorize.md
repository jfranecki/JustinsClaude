---
description: Generalize a project memory into the shared memories/ library — audits it for tight coupling, extracts the portable core, restructures it, and drafts it for your review
argument-hint: "[path to a project memory file — omit to pick from this project's memories]"
allowed-tools: Read, Write, Glob, Grep, Bash(ls:*), Bash(git:*), Bash(test:*)
---

# /memorize — generalize a project memory into the shared library

You are turning a raw, project-specific memory into a **loosely coupled** memory that any developer or coding agent can ingest into their own memory ecosystem. The library lives in the user's clone of their ClaudeCommands repo at `{{MEMORIES_REPO}}/memories/`. Its rules are in `{{MEMORIES_REPO}}/memories/README.md` and the required file shape in `{{MEMORIES_REPO}}/memories/TEMPLATE.md` — **read both before drafting anything.**

If `{{MEMORIES_REPO}}/memories/` does not exist, stop: the clone has moved or is missing. Tell the user to restore it (and re-run `/get-started` if it now lives at a new path).

## Step 1 — Locate the source memory

- If "$ARGUMENTS" is a file path, read that file.
- If "$ARGUMENTS" is empty: list this project's memory directory — `~/.claude/projects/<munged-path>/memory/`, where `<munged-path>` is the current project's absolute path with each `/` replaced by `-`. (If your own system prompt names your memory directory, use that instead of deriving it.) Show the memories found (name + description) with AskUserQuestion and let the user pick. If the directory is missing or empty, say so and stop.

## Step 2 — Coupling audit

Read the memory and enumerate **every** instance of tight coupling, tagged by category:

- **(a)** absolute or machine-local paths
- **(b)** project / product / repo names
- **(c)** personal names and attribution
- **(d)** dates, timestamps, session IDs, and tool-generated metadata (`originSessionId`, `modified`, …)
- **(e)** `[[links]]` to memories that exist only in the source project
- **(f)** references to project-internal history — a PR, an incident, "the X treatment" — that a stranger cannot resolve
- **(g)** environment specifics (machines, ports, OS-specific paths)
- **(h)** team-local conventions presented as if they were universal truths

Also mark what is **NOT** coupling and must be preserved: external URLs, concrete techniques, named public tools and libraries, code idioms. These are the payload — a generalization that discards them is worthless.

## Step 3 — Extract the portable core

State, in one sentence, the engineering truth, architectural pattern, or debugging lesson that survives outside the source project.

**If there is no portable core** — the memory is pure project trivia (one teammate's preference about one file, a workaround for one machine) — say so plainly and stop. Do not force a generalization; a hollow memory pollutes the library.

## Step 4 — Restructure

Rewrite the memory into the library's standard shape (`TEMPLATE.md`):

- **Frontmatter:** a fresh kebab-case `name` for the generalized truth (not the source slug if that was project-flavored), a one-line `description` an agent can match against when deciding to recall it, and `metadata.type` (usually `feedback` for how-to-work rules, `reference` for pointer collections).
- **Body:** `## Context / Trigger`, `## Core Rule / Insight`, `## Expected Outcome`.
- Replace category (a)/(b)/(g)/(h) items with `[BRACKET_PLACEHOLDERS]` like `[YOUR_APP_NAME]` or `[PACKAGE_MANAGER]`.
- Strip categories (c)/(d)/(e)/(f) **entirely** — no provenance, no dead links, no attribution, no dates.
- Keep every payload item identified in Step 2.

## Step 5 — Present the draft for review

Do **NOT** write anything yet. Show the user, in one message:

1. The coupling-audit table: each finding → its category → what you did with it (placeholder / stripped / kept as payload).
2. The one-sentence portable core from Step 3.
3. The full draft memory, verbatim.
4. If `{{MEMORIES_REPO}}/memories/` already contains a memory covering the same truth, say so and propose updating that file instead of creating a new one.

Then ask for a decision (AskUserQuestion): **approve** / **revise** (take their notes and redraft) / **abandon**.

## Step 6 — On approval, write

1. Write the file to `{{MEMORIES_REPO}}/memories/<name>.md`.
2. Self-check the written file: grep it for the source project's name, any personal names from the source, `originSessionId`, and `[[` — any hit means Step 4 missed something; fix it before declaring success.
3. Remind the user the library is a git repo: show `git -C {{MEMORIES_REPO}} status --short` and suggest a commit message, but do **not** commit or push unless they ask.
