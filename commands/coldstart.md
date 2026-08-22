---
description: State-of-the-project brief at session start — filesystem, git, docs, and the past conversations a normal discovery pass never reads
allowed-tools: Bash(pwd:*), Bash(ls:*), Bash(tree:*), Bash(git:*), Bash(python:*), Bash(python3:*), Bash(head:*), Bash(grep:*), Bash(sed:*), Read, Glob, Grep
---

# /coldstart — Project Situational Awareness

A discovery pass reads the **filesystem**. It never reads your past conversations — yet on
a project with months of history, that is where a lot of the decisions live, including
ones that never made it into a document.

This gives a new session both, cheaply, without dragging hundreds of megabytes of
transcript into context. Output is terse and engineering-report shaped: no preamble, no
narrating the process, no restating these instructions.

## Run these first (parallel, one message)

Transcript search is done by `history.py`, installed at `{{HISTORY_SCRIPT}}`. It is
stdlib-only Python 3 — use `python3` if present, otherwise `python`.

```bash
git -C . log --oneline -20
git -C . status --porcelain
python3 "{{HISTORY_SCRIPT}}" index
tree -L 2 -I 'node_modules|.git|dist|build|target|__pycache__|.venv'
```

Plus a filesystem sweep:

- `CLAUDE.md`, `README.md`, and any `docs/`, `audit/` or `specs/` index files.
- Package manifests — `package.json`, `pyproject.toml`, `Cargo.toml`, `go.mod`, `Gemfile`,
  whichever exist. Note the tech stack, entry points, and test setup.
- Glob for `*HANDOFF*`, `*BACKLOG*`, `*STATUS*`, `*DECISION*` — on a long-lived project
  those names carry the state.

If the directory is not a git repo, note it in one line and continue; do not abort.

## Then orient, in this order

1. **Committed docs are the primary source.** They hold rulings and reasoning that survived
   review. Read them before any transcript.
2. **Git log is the second source.** Commit messages on a well-kept project say *why*.
3. **Transcripts are the third source, and they are for SPECIFIC QUESTIONS ONLY.** Do not
   bulk-read them. Search when you have a question the docs did not answer:

```bash
python3 "{{HISTORY_SCRIPT}}" search "currency system" -n 10
python3 "{{HISTORY_SCRIPT}}" recent -n 3   # what were the last sessions about
```

`recent` surfaces the last sessions' subject matter. The newest transcript is usually the
*current* session — often near-empty or holding only this coldstart request — so read past
it rather than spending a slot on it.

Hunt deferred work explicitly, since it rarely reaches a document — search the phrases
people actually use when postponing something:

```bash
python3 "{{HISTORY_SCRIPT}}" search "for now" -n 10
python3 "{{HISTORY_SCRIPT}}" search "later" -n 10
python3 "{{HISTORY_SCRIPT}}" search "TODO" -n 10
```

If `index` reports no history, this project simply has no prior sessions — carry on with
the filesystem pass and say so in the briefing.

## The rule that makes transcript search safe

`search` returns **the user's own messages by default, newest first.** That is deliberate.

- **User turns are decisions.** Rulings, corrections, preferences, priorities.
- **Assistant turns are reasoning**, including wrong turns and claims later retracted.
  Searching them surfaces confident text with no signal it was withdrawn — worse than not
  searching at all.

`--all` includes assistant turns. Use it only to reconstruct *how* something was worked
out, and treat every hit as a lead to verify, never a fact to act on.

**Newest wins.** If an old message and a recent one conflict, the recent one is the
ruling. If a transcript and a committed doc conflict, check dates — usually the doc is the
distilled version, but not always, and the disagreement itself is worth raising.

## Cross-reference before you believe any of it

Anything a transcript says was done, but which no commit reflects, is **not done**. Check
every claimed piece of work against `git log` and the working tree, then label it:

- **in progress** — uncommitted changes or a live branch back it up.
- **abandoned** — discussed, never landed, nothing in flight.

Report the label. Never let a transcript's intent read as completed work.

## Report back

A short briefing, not a book:

- **What this project is**, in two sentences.
- **Where it is right now** — branch, recent commits, anything uncommitted or in flight.
- **Current focus** — what the project is converging on.
- **Recent decisions + rationale** — marked as historical context that current code
  supersedes where they conflict.
- **Authoritative documents**, by path.
- **Open threads / deferred work**, each flagged in progress or abandoned.
- **Known landmines** — recurring bugs, fragile areas, gotchas repeated across sessions.
- **Contradictions** between docs. **Say so rather than silently picking one.**
- **What you believe the next task is** — then **ask**, because the user has context no
  artifact holds.

## Do not

- Do not bulk-ingest transcripts. They can be hundreds of megabytes and are mostly noise.
- Do not treat a transcript hit as current truth. Verify against code or a committed doc.
- Do not report transcript-discussed work as done without a commit backing it.
- Do not start work off this briefing alone. Confirm the goal first.
