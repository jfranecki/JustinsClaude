---
description: Install and wire up these Claude commands — gathers your config, verifies credentials and connections, and installs ready-to-use commands into ~/.claude
argument-hint: "[optional: specific commands to install, e.g. 'review-deep slack-updates']"
allowed-tools: Bash(git:*), Bash(gh:*), Bash(ls:*), Bash(echo:*), Bash(test:*), Bash(command:*), Bash(mkdir:*), Bash(python3:*), Bash(jq:*), Bash(acli:*), Bash(diff:*), Bash(ollama:*), Bash(curl:*), Bash(sysctl:*), Bash(nvidia-smi:*), Read, Write, Glob, Grep, ToolSearch
---

# /get-started — command installer & wiring assistant

You are setting up this repository's Claude Code commands for the current user. The files under `commands/` are **templates**: they contain `{{PLACEHOLDER}}` tokens for everything specific to a person, team, or codebase. Your job is to gather the values, **verify the user actually has the required credentials and connections**, fill the templates, and install working copies into `~/.claude/commands/` (and `~/.claude/workflows/`). A command whose required prerequisites fail verification must NOT be installed — report what is missing and how to fix it instead.

Optional pre-selection from the user (may be empty): **$ARGUMENTS** — if non-empty, treat it as the list of commands to install and skip the selection question.

Work conversationally but efficiently: batch your detection commands, use AskUserQuestion for choices, and never invent a value you could not detect or confirm with the user.

## Step 0 — Locate the repo and sanity-check

1. Resolve the repo root: `git rev-parse --show-toplevel` (fall back to cwd). Verify `commands/` exists there and contains the template `.md` files. If not, stop: tell the user to `cd` into their clone of this repo and re-run `/get-started`.
2. `mkdir -p ~/.claude/commands ~/.claude/workflows` so installs can't fail on missing dirs.

## Step 1 — What's on offer

Present this menu (with AskUserQuestion, multiSelect, unless $ARGUMENTS already chose). Briefly describe each:

| Command | What it does | Hard requirements |
|---|---|---|
| `onboard` | Deep codebase onboarding briefing for whatever repo a session starts in | none |
| `coldstart` | State-of-the-project brief at session start: codebase discovery + a review of your recent Claude Code session transcripts for the repo, cross-referenced against git log | `python3` — installs the `history.py` sidecar, see `coldstart-setup/COLDSTART_SETUP.md` |
| `bye` | End-of-session close-out: verifies the session's goal landed, audits git state, cleans up merged worktrees/branches | none; `gh` recommended |
| `review-deep` | Rigorous multi-phase GitHub PR review (spec alignment, conflicts, security) | `gh` authenticated; Atlassian `acli` optional |
| `pr-autoreview` | Unattended sweep: finds open PRs needing your review in one configured repo, deep-reviews them in parallel worktrees, auto-posts human-voiced reviews | `review-deep` installed, `gh` authed with access to the target repo, a local clone of it, `python3` |
| `slack-updates` | Read-only spoken-style brief of Slack channels you choose to track | Slack MCP connected, your Slack member ID |
| `speak` | Reads the last response aloud with local Kokoro TTS (free, offline) | local Kokoro install — see `kokoro-setup/KOKORO_SETUP.md` |
| `speak-api` | Reads a summary of the last response aloud via ElevenLabs v3 with expressive audio tags; a required `--f`/`--m` flag picks the female AU or male UK voice | `ELEVENLABS_API_KEY` env var, `jq`, an audio player (`afplay` on macOS, else `ffplay`/`mpv`/`mpg123`/`cvlc`) |
| `claudish` | Rewrites the last response into plain English using a local ollama model — free, private, no API tokens | ollama installed and running with one model pulled, `jq` — see `ollama-setup/OLLAMA_SETUP.md` |
| `memorize` | Generalizes a project memory into this repo's shared `memories/` library — audits coupling, restructures, drafts for review | a local clone of this repo, kept at a stable path (it *is* the library) |

## Step 2 — Detect the environment (batch these)

Run in parallel where possible; record every result:

- `echo $HOME` → **{{HOME}}**
- `gh auth status` and `gh api user -q .login` → proposed **{{GITHUB_USERNAME}}** (confirm with the user — some people have separate work/personal GitHub accounts; the one that matters is the one with access to the repo they review in)
- `command -v acli`, `command -v jira`, `command -v python3`, `command -v jq`, `command -v afplay`
- `test -n "$ELEVENLABS_API_KEY" && echo set || echo missing` — on Windows also check the persistent user scope, which the current shell may not have inherited: `[Environment]::GetEnvironmentVariable('ELEVENLABS_API_KEY','User')`
- audio player for `speak-api`: `command -v afplay ffplay mpv mpg123 cvlc` — any one is enough
- Slack MCP: use ToolSearch with query `select:mcp__claude_ai_Slack__slack_read_channel`. If it resolves, Slack is connected. If not, the fix is: run `/mcp` and connect "claude.ai Slack".
- Kokoro: check the conventional spots (`~/ToolboxRepos/kokoro`, `~/Tools/kokoro`, `~/kokoro`) for a dir containing both `.venv/bin/python` and `speak.py`.
- `history.py` for `coldstart`: it ships in this repo at `<repo>/coldstart-setup/history.py`. Confirm it is present and that `python3 -c 'import ast,sys; ast.parse(open(sys.argv[1]).read())' <path>` parses it.
- ollama: `command -v ollama`, then probe the daemon with `curl -sS --max-time 5 http://localhost:11434/api/tags` (a running daemon returns JSON containing a `models` array). List what is pulled with `ollama list`.
- `claudish.sh`: check the conventional spots (`~/ToolboxRepos/claudish/claudish.sh`, `~/.claude/bin/claudish.sh`) for the wrapper script.
- Platform: `speak` (Kokoro) plays audio via `afplay`/`open`, so it is macOS-first — on Linux or Windows, warn that `speak.py` needs its playback command swapped. `speak-api` auto-detects a player and needs no changes.

## Step 3 — Interview for the values

Only ask for what the selected commands actually need. The full placeholder map:

| Placeholder | Needed by | How to obtain |
|---|---|---|
| `{{HOME}}` | pr-autoreview | detected, never ask |
| `{{GITHUB_USERNAME}}` | pr-autoreview | detected via `gh api user`, confirm with user |
| `{{GITHUB_REPO}}` | pr-autoreview | ask: the `owner/repo` they review PRs in. Validate with `gh repo view <owner/repo>`. |
| `{{MAIN_CHECKOUT}}` | pr-autoreview | ask: absolute path to their canonical local clone of that repo. Validate: dir exists and `git -C <path> remote get-url origin` ends in `<owner>/<repo>(.git)`. |
| `{{JIRA_PROJECT_KEY}}` | pr-autoreview | ask: their Jira project prefix (e.g. `ABC` for tickets like `ABC-1234`). If they don't use Jira, substitute `XXXX` (the regex will simply never match) and note it. |
| `{{REPO_NOTES}}` | pr-autoreview | ask (optional): 1–3 sentences of repo-specific sharp edges every reviewer should check (layering rules, known dangerous patterns, pre-commit gotchas). Default `(none provided)`. |
| `{{CLONE_ROOTS}}` | review-deep | ask: the director(y/ies) where they keep local clones. Render as indented markdown bullets keeping `<repo>` as a literal pattern token, e.g.:<br>`   - \`/Users/me/code/<repo>\`` |
| `{{SLACK_USER_ID}}` | slack-updates | ask. Where to find it: Slack → click your profile photo → **Profile** → **⋮ (three dots)** → **Copy member ID**. Looks like `U0XXXXXXXXX`. If Slack MCP is connected you may instead `slack_search_users` for their name and confirm the match. |
| `{{SLACK_CHANNELS_TABLE}}` | slack-updates | ask which channels to track and at which tier (`urgent` / `core` / `ambient`). If Slack MCP is connected, resolve each name to its ID with `slack_search_channels` yourself; otherwise ask the user for IDs (channel → ⋮ → copy link; the ID is the `C…` segment). Render as markdown table rows: `\| urgent \| #incidents \| C0XXXXXXX \|` — one line per channel, no header (the template provides it). |
| `{{KOKORO_DIR}}` | speak | detected candidate or ask. Validate `<dir>/.venv/bin/python` and `<dir>/speak.py` both exist. If Kokoro isn't installed and they want `/speak`, offer two paths: (a) you perform the setup now by following `kokoro-setup/KOKORO_SETUP.md` in this repo, or (b) they do it later and re-run `/get-started`. |
| `{{HISTORY_SCRIPT}}` | coldstart | detected, never ask: the absolute path the sidecar is installed to in Step 5 — `~/.claude/bin/history.py`, expanded. Do **not** point it at the copy inside the clone; the clone can move or be deleted and the installed command would silently lose its history search. |
| `{{CLAUDISH_SCRIPT}}` | claudish | detected candidate or ask: the absolute path to `claudish.sh` (shipped in `ollama-setup/`). Validate the file exists and `bash -n <path>` parses. If ollama isn't set up and they want `/claudish`, offer two paths: (a) you perform the setup now by following `ollama-setup/OLLAMA_SETUP.md` in this repo — it measures their hardware (GPU VRAM / unified memory / RAM) and sizes the model to match, which matters a lot here — or (b) they do it later and re-run `/get-started`. |
| `{{MEMORIES_REPO}}` | memorize | detected, never ask: the repo root resolved in Step 0. Confirm with the user that their clone will stay at this path — `/memorize` writes drafts into it, so if the clone moves they must re-run `/get-started`. |

Use absolute paths everywhere (expand `~` before substitution).

## Step 4 — Verify before allowing use (the gate)

For each selected command, evaluate its gate. **Required failures block installation of that command** (skip it, explain the fix); optional failures install with a clear warning.

- `onboard` — no gate.
- `coldstart` — required: `python3` present; `<repo>/coldstart-setup/history.py` present and parsing. Also installs the sidecar (Step 5). The command degrades gracefully with no transcript history — it reports that and delivers the filesystem pass — so an empty `~/.claude/projects/` is not a gate failure.
- `bye` — no gate. Optional: `gh` authenticated — without it, merge confirmation falls back to plain git checks.
- `review-deep` — required: `gh auth status` logged in. Optional: `acli`/`jira` present (without it, Jira spec-mapping degrades gracefully); each CLONE_ROOTS directory exists.
- `pr-autoreview` — required: `review-deep` being installed in this same run (or already present in `~/.claude/commands/`); `gh` access to `{{GITHUB_REPO}}`; valid `{{MAIN_CHECKOUT}}`; `python3` present. Also installs both workflow files (Step 5). **Warn explicitly**: this command POSTS REVIEWS to GitHub under their account when run — they should read `commands/pr-autoreview.md` before scheduling it.
- `slack-updates` — required: Slack MCP tools resolvable via ToolSearch; a plausible `{{SLACK_USER_ID}}`; at least one tracked channel resolved.
- `speak` — required: validated `{{KOKORO_DIR}}`; `afplay` present (macOS).
- `speak-api` — required: `ELEVENLABS_API_KEY` resolvable (key from elevenlabs.io → Profile → API Key; if missing, `export ELEVENLABS_API_KEY="sk_..."` in the shell profile, or on Windows `[Environment]::SetEnvironmentVariable('ELEVENLABS_API_KEY','sk_...','User')`, then start a **new** Claude Code session — a running session keeps its old environment); `jq`; at least one audio player from `afplay`/`ffplay`/`mpv`/`mpg123`/`cvlc`. If the key is only set for the persistent user scope and not yet visible to the running shell, install it but report status as `ready after restart`, not `ready`.
- `memorize` — required: `<repo>/memories/` exists in the clone (it ships with the repo, so a failure means a broken or partial clone).
- `claudish` — required: a validated `{{CLAUDISH_SCRIPT}}`; `jq` (the script exits without it); the ollama daemon answering on `/api/tags` (if not: `brew services start ollama`, or `ollama serve`); at least one model pulled — `ollama list` must be non-empty. If the script's default `gemma3:4b` is **not** among the pulled models, still install, but tell the user which model they do have and that they must set `CLAUDISH_MODEL` (shell profile, or the `env` block of `~/.claude/settings.json`) or the command will fail with `model isn't available`. Optional but worth reporting: if they have an NVIDIA GPU with ≥24 GB VRAM, mention they can run a much larger model and should set `CLAUDISH_KEEP_ALIVE=5m`.

## Step 5 — Install

For each command that passed its gate:

1. **Read** the template from `<repo>/commands/<name>.md`.
2. Replace every `{{PLACEHOLDER}}` with the gathered value (do the substitution in memory — do not use `sed`, paths contain slashes).
3. If `~/.claude/commands/<name>.md` already exists, tell the user and ask before overwriting (offer to show a diff).
4. **Write** the result to `~/.claude/commands/<name>.md`.
5. After writing, `grep` the installed file for `{{` — any leftover token means a substitution was missed; fix it before declaring success.

For `coldstart` additionally install the transcript-search sidecar **before** substituting `{{HISTORY_SCRIPT}}`:
- `mkdir -p ~/.claude/bin`, then copy `<repo>/coldstart-setup/history.py` → `~/.claude/bin/history.py` (verbatim — it takes all config via runtime args).
- Verify with `python3 ~/.claude/bin/history.py index` run from any git repo. Both a transcript table and `no transcript history found for this project` are passes; a traceback is not.
- `{{HISTORY_SCRIPT}}` is that absolute path with `~` expanded.

For `pr-autoreview` additionally copy the two workflow files (they take all config via runtime args, so they are copied verbatim):
- `<repo>/workflows/pr-review-fanout.js` → `~/.claude/workflows/pr-review-fanout.js`
- `<repo>/workflows/pr-draft-fanout.js` → `~/.claude/workflows/pr-draft-fanout.js`

## Step 6 — Final report

End with a single summary the user can act on:

1. A table: command → installed path → status (`ready` / `skipped: <missing requirement + fix>` / `declined`).
2. Any warnings (e.g. `acli` missing, Kokoro deferred, Linux playback caveats).
3. Remind them: newly installed commands are picked up in a **new Claude Code session** — restart or open a new session, then try `/onboard` in any repo as a smoke test.
4. If `pr-autoreview` was installed, repeat the one-line warning that it posts reviews as them, and that scheduling it is a separate, deliberate step — never arm it automatically.

Do not install anything the user did not select, and do not leave half-written files behind: if a substitution fails mid-way, delete the partial file and report it.
