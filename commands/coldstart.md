---
description: State-of-the-project brief at session start — codebase discovery + a review of your recent Claude Code session transcripts for the current directory
allowed-tools: Bash(pwd:*), Bash(ls:*), Bash(tree:*), Bash(git:*), Bash(jq:*), Bash(head:*), Bash(grep:*), Bash(sed:*), Read, Glob, Grep
---

# /coldstart — Project Situational Awareness

Build a state-of-the-project brief from two sources: the codebase as it exists
now, and the prior Claude Code session transcripts for this directory. Run the
three phases in order. Output style is terse, bullet-pointed,
engineering-report shape — no preamble, no narration of the process, no
restating of these instructions.

## Phase 1 — Discovery pass

Run tool calls in parallel where possible.

- Project structure: `tree -L 2` (or `ls` per directory if tree is missing),
  skipping `node_modules`, `.git`, and build/output dirs
  (`tree -L 2 -I 'node_modules|.git|dist|build|target|__pycache__|.venv'`).
- Read README, `docs/`, `CLAUDE.md`, and package manifests (`package.json`,
  `pyproject.toml`, `Cargo.toml`, `go.mod`, `Gemfile`, etc.) — whichever exist.
- `git log --oneline -20` and `git status` for recent activity and in-flight
  work. If the directory is not a git repo, note that in one line and move on —
  do not abort.
- Note the tech stack, entry points, and test setup.

## Phase 2 — Session history pass

Transcripts for the current project live at
`~/.claude/projects/<encoded-cwd>/*.jsonl`, where `<encoded-cwd>` is the
absolute cwd path with all non-alphanumeric characters replaced by `-`
(example: `/Users/you/repos/my-app` → `-Users-you-repos-my-app`).

1. Resolve the directory by encoding `$PWD`:

   ```bash
   ENCODED=$(pwd | sed 's/[^a-zA-Z0-9]/-/g')
   ls -d ~/.claude/projects/"$ENCODED" 2>/dev/null
   ```

   Verify with `ls ~/.claude/projects/ | grep -i <repo-name>` if the exact
   match fails. If no transcript directory exists, say so in one line and
   deliver Phase 1 + Phase 3 only.

2. List the `.jsonl` files sorted by mtime (`ls -t`) and take the 3–5 most
   recent sessions. The newest file is usually the *current* session (often
   near-empty or containing only this coldstart request) — look past it to the
   next files rather than spending a slot on it.

3. Extract conversation text. **Never cat entire transcript files** — they can
   be tens of MB. Extract only user messages and assistant text blocks; skip
   tool_use/tool_result entries entirely. The JSONL schema is internal to
   Claude Code and changes between versions, so be defensive: parse
   line-by-line, tolerate and skip lines that fail to parse, use loose jq
   filters with fallbacks, and cap output per session:

   ```bash
   jq -R -r 'fromjson? | select(.type=="user" or .type=="assistant")
             | (.message.content? // empty)
             | if type=="array" then map(.text // empty) | join("\n") else . end' \
     "$FILE" 2>/dev/null | grep -v '^\s*$' | head -200
   ```

   `-R` + `fromjson?` reads each line as raw text and silently skips any that
   fail to parse (plain `jq` would halt at the first malformed line). The
   `// empty` fallback skips lines without `message.content` (summary/meta
   entries) instead of printing literal `null`, and `.content?` guards against
   a `message` that isn't an object. If the filter yields nothing readable,
   adjust it against the actual schema of a sample line
   (`head -5 "$FILE" | jq 'keys'`) rather than giving up.

4. From each session reconstruct: what was being worked on, decisions made and
   their rationale, open threads, and anything explicitly deferred ("we'll do
   X later", "TODO", "for now").

5. Cross-reference against `git log`: work discussed in transcripts but absent
   from commits is likely in-progress or abandoned — flag it as such rather
   than assuming it's done.

## Phase 3 — Synthesis

Emit a state-of-the-project brief with these sections:

- **Current focus** — what the project is converging on right now.
- **Recent decisions + rationale** — from transcripts, marked as historical
  context that current code supersedes if they conflict.
- **Open threads / deferred work** — with in-progress vs. abandoned flags from
  the git cross-reference.
- **Known landmines** — recurring bugs, fragile areas, gotchas mentioned
  across sessions.

End by asking what the user wants to pick up.
