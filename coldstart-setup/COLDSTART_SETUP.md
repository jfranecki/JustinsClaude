# Setting up `history.py` for `/coldstart`

`/coldstart` reads your past Claude Code sessions for the current project. The reading is
done by **`history.py`**, the small stdlib-only Python script in this directory — not by
the command itself. `/get-started` installs it for you; this document explains what it is,
why it works the way it does, and how to install it by hand.

## What it needs

Python 3. Nothing else — no pip install, no virtualenv, no network. The script imports
only `argparse`, `json`, `os`, `re`, `sys`, and `pathlib`.

## Installing by hand

Copy it anywhere stable and point the command at that absolute path:

```bash
mkdir -p ~/.claude/bin
cp coldstart-setup/history.py ~/.claude/bin/history.py
python3 ~/.claude/bin/history.py index      # verify
```

Then replace every `{{HISTORY_SCRIPT}}` token in `~/.claude/commands/coldstart.md` with
that absolute path. If the clone moves, the installed command keeps pointing at the old
path — re-run `/get-started`, or fix the path in place.

`index` on a project with prior sessions prints one row per transcript (size, message
count, first and last timestamp). If it prints `no transcript history found for this
project`, the script is working and this project genuinely has no sessions yet.

## Why a script instead of inline `jq`

Three things a one-liner gets wrong, all of which quietly corrupt the briefing:

1. **Project-directory resolution.** Claude Code files transcripts under
   `~/.claude/projects/<encoded-path>/`, encoding the absolute cwd by replacing `:`, `\`,
   and `/` with `-`. A session started in a **worktree or subdirectory** can be filed under
   the parent project, so an exact match misses. `project_dir()` falls back to the
   longest-matching candidate directory instead of reporting no history.
2. **Noise.** Transcripts are full of `<system-reminder>`, `<command-name>`,
   `<local-command-caveat>`, and hook output that reads like the user talking but isn't.
   The script filters those out; a naive extraction feeds them to you as conversation.
3. **Scale.** Transcripts run to hundreds of megabytes. The script searches and returns
   matching snippets with timestamps, so nothing is bulk-loaded into context.

## Why it returns your messages by default

This is the important one, and it is a deliberate default rather than a limitation.

- **User turns are decisions** — rulings, corrections, preferences, priorities.
- **Assistant turns are reasoning**, including wrong turns and claims that were retracted
  later in the same session. Searching them surfaces confident-sounding text with **no
  signal that it was withdrawn**, which is worse than not searching at all.

`--all` includes assistant turns. Use it to reconstruct *how* something was worked out, and
treat every hit as a lead to verify against code or a committed doc — never as a fact.

## Commands

```bash
python3 history.py index                              # what history exists
python3 history.py recent -n 3                        # what the last sessions were about
python3 history.py search "currency system" -n 10     # your messages, newest first
python3 history.py search "for now" -n 10             # deferred work rarely reaches a doc
python3 history.py search "the bug" --all             # include assistant turns (leads only)
```

`--cwd <path>` searches another project's history instead of the current directory.
`--context N` widens the snippet around each match (default 240 characters).
