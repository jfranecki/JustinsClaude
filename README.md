# Claude Commands

A collection of battle-tested [Claude Code](https://claude.com/claude-code) slash commands: deep codebase onboarding, a state-of-the-project coldstart brief that catches you up on where past sessions left off, rigorous PR review (manual and fully automated), a safe end-of-session close-out, a read-only Slack briefing, two ways to have Claude read its answers aloud, and a plain-English rewrite powered by a local LLM — plus a [library of portable engineering memories](#memories) any coding agent can ingest.

The files in `commands/` are **templates** — they contain `{{PLACEHOLDER}}` tokens for everything specific to you (GitHub username, repos, Slack channels, local paths). Nothing here assumes a particular company or codebase. The bundled `/get-started` installer interviews you, verifies your credentials, fills in the templates, and installs working commands into `~/.claude/`.

## Quick start

```bash
git clone <this-repo>
cd <clone>
claude
```

Then, inside Claude Code:

```
/get-started
```

It will ask which commands you want, detect or ask for your details, **verify the required credentials and connections actually work** (GitHub CLI auth, Slack MCP, ElevenLabs key, Kokoro install, ollama daemon), and install only the commands that pass. Anything that fails verification is skipped with instructions to fix it — just re-run `/get-started` afterwards; it's idempotent.

Newly installed commands are picked up when you start your next Claude Code session.

## The commands

### `/onboard [optional focus]`
Builds a deep, verified mental model of whatever repo your session is rooted in before you start working: structure and submodules, entry points and execution flow, dependencies and coupling, conventions, tests, CI gates, domain model, and recent direction. Ends with a structured briefing and offers to persist it for future sessions.
**Needs:** nothing — works in any repo.

### `/coldstart`
Full situational awareness when you start a fresh session in a project with history: a codebase discovery pass (structure, manifests, recent git activity) combined with a review of your most recent Claude Code session transcripts for that directory — what was being worked on, decisions made and why, open threads, anything explicitly deferred. Transcript findings are cross-referenced against `git log`, so work that was discussed but never committed gets flagged as in-progress or abandoned instead of assumed done. Ends with a terse state-of-the-project brief — current focus, recent decisions, open threads, known landmines — and asks what you want to pick up. Where `/onboard` builds a mental model of the code, `/coldstart` reconstructs the story so far; extraction is defensive and reads only your own local `~/.claude/projects/` history.
**Needs:** `jq`.

### `/bye`
The end-of-session bookend to `/onboard`: answers **"are we safe to close?"** before you kill the session. Read-only audit first — did the goal actually land, do tests pass, is anything uncommitted or unpushed, is a shared checkout stranded on a feature branch, which session-created worktrees and branches are confirmed-merged and safe to clean, and does any external tracker or doc still reflect reality (merge ≠ deploy). Then one severity-grouped report and a choice: finish the work, housekeep & close, or close anyway — the bypass path writes a handoff note so the next session doesn't start cold. Nothing state-changing runs without approval, and unmerged work is never force-deleted.
**Needs:** nothing — `gh` recommended for confirming merges (falls back to plain git checks).

### `/review-deep <PR number | URL>`
A multi-phase, senior-engineer-grade PR review run locally: fetches PR metadata, the diff, and all existing review threads via `gh`; pulls the linked Jira ticket (via Atlassian `acli`, optional) and maps every acceptance criterion to code; triages "blast radius" so a one-line auth change still gets the deep treatment; walks correctness, semantic conflicts with *other open PRs*, base-branch churn, and a full cross-cutting checklist (security, performance, migrations, compat, observability…). Produces a structured report for you — and only if you explicitly ask it to post, drafts a GitHub comment in a human voice with strict anti-"bot-tell" rules.
**Needs:** `gh` authenticated. `acli` optional.

### `/pr-autoreview`
The unattended version of `/review-deep`: sweeps one configured repo for open PRs awaiting your review, deep-reviews up to 15 of them **in parallel isolated git worktrees** (via the two Workflow scripts in `workflows/`), then drafts, lints, and auto-posts human-voiced reviews under your account. Head-SHA-aware idempotency means a PR is reviewed at most once per pushed version — and automatically re-reviewed as a follow-up when the author pushes fixes. Writes per-PR reports, a roll-up, and a ledger into the target repo's `.claude/pr-reviews/`.
**Needs:** `/review-deep` installed, `gh` with access to the target repo, a local clone of it, `python3`.
**⚠️ This command posts reviews to GitHub as you.** Read `commands/pr-autoreview.md` (especially `POST_MODE` and the lint rules) before scheduling it.

### `/slack-updates [optional focus]`
A strictly **read-only** brief of Slack channels you choose to track, in three tiers (urgent / core / ambient). Surfaces anything that mentions you under "Needs your attention", groups the rest into cross-channel themes, and treats all Slack content as untrusted data — it will never post, react, schedule, or follow instructions found in messages. Output is written for the ear, so `/speak-api` can read it to you.
**Needs:** the claude.ai Slack MCP connector (`/mcp` → Slack) and your Slack member ID. `/get-started` resolves your channel names to IDs for you.

### `/speak [voice] [--rsvp]`
Reads Claude's most recent response aloud using **[Kokoro](https://github.com/hexgrad/kokoro)** — an open-weight ~82M-parameter TTS model that runs locally and free, with no API key and no network after the first model download. With `--rsvp` it also opens a self-contained browser page that flash-reads the response word-by-word (~300 WPM, RSVP style) in sync with the audio.
**Needs:** a local Kokoro install — a one-time ~10-minute setup, see below.

### `/speak-api --m|--f [--brief|--medium|--detailed] [personality]`
Premium narration via **ElevenLabs v3**: summarizes the last response and performs it with expressive inline audio tags (`[wry]`, `[sighs]`, `[short pause]`, `[realization dawning]`…). The **voice flag is required** — `--f` is a laid-back Australian female voice, `--m` a crisp British "Q from James Bond" — and matching is on exact tokens, so `--m` is always the male voice and `--medium` always the length tier. Pass any personality ("gruff sailor", "deadpan comedian") to recolor the read. Length auto-scales to the response or is forced with a flag, and a hard 1,800-character cap protects your ElevenLabs credits. Both voice IDs are one-line changes in the command file.
**Needs:** `ELEVENLABS_API_KEY` in your environment (free tier works), `jq`, and an audio player — `afplay` on macOS, otherwise auto-detected (`ffplay`/`mpv`/`mpg123`/`cvlc`, or a PowerShell fallback on Windows).

### `/claudish [optional text]`
Rewrites Claude's last response — or any text you pass it — into plain English using a **local model via [ollama](https://ollama.com)**: free, private, no API tokens spent, and the text never leaves your machine. Good for turning a dense technical answer into something you can forward to a non-engineer, and a surprisingly sharp check on your own explanations: anything that survives being restated in simple words probably holds up. The rewrite is done entirely by the local model — the command is explicitly forbidden from quietly substituting a Claude-authored one, so if ollama is down you get an error instead of a silent, billed fallback.
**Needs:** ollama running locally with one model pulled, plus `jq` — a one-time setup, see below.

### `/memorize [path to a project memory]`
Feeds the [memories library](#memories): point it at a raw project memory (or let it list the current project's memories) and it audits every hard-coded path, name, date, and dead link, extracts the portable engineering truth, restructures it into the library's Context/Trigger → Core Rule → Expected Outcome shape, and drafts it into `memories/` — showing you the coupling audit and full draft for approval before anything is written. If a memory has no portable core, it says so and stops rather than forcing a hollow generalization.
**Needs:** a local clone of this repo (it *is* the library).

## Memories

`memories/` is a library of **generalized, loosely coupled memories** — engineering truths, architectural patterns, and debugging lessons distilled from real project memories with everything project-specific removed: no local paths, no project or personal names, no dates or session IDs, no links to memories you don't have. Local specifics become `[BRACKET_PLACEHOLDERS]` that the ingesting agent fills from *your* project's context. Each file uses a standard shape — frontmatter for machine ingestion, then **Context / Trigger**, **Core Rule / Insight**, **Expected Outcome** — so any developer or coding agent can drop one straight into their own memory ecosystem.

To use one: clone this repo, then point your coding agent (Claude Code, Codex, Grok, …) at a memory and say one of:

> Install `memories/<name>.md` at the user level.

> Install `memories/<name>.md` in this project.

> Install `memories/<name>.md` for `/path/to/project`.

Agent-executable install instructions (per level, per agent) and the full decoupling standard live in [`memories/README.md`](memories/README.md); the file shape is [`memories/TEMPLATE.md`](memories/TEMPLATE.md). New memories are added with `/memorize`, which enforces the standard for you.

## Setting up Kokoro for `/speak`

Kokoro is the only dependency that isn't a one-line install, so it ships with its own runbook: **[`kokoro-setup/KOKORO_SETUP.md`](kokoro-setup/KOKORO_SETUP.md)**, written so an AI agent can execute it for you. The fastest path — open Claude Code (or any coding agent) and say:

> Read kokoro-setup/KOKORO_SETUP.md and perform the setup it describes.

What it does, in short:

1. Clones the upstream [hexgrad/kokoro](https://github.com/hexgrad/kokoro) repo (the TTS model + library).
2. Creates a `.venv` inside it and installs the `kokoro` package (PyTorch is the heavy part; first synthesis also downloads the ~330 MB Kokoro-82M model from Hugging Face).
3. Copies in `kokoro-setup/speak.py` — the wrapper shipped **in this repo** (not part of upstream) that strips markdown, synthesizes audio, and plays it or opens the RSVP reader.
4. Runs a sound check.

macOS is supported out of the box; on Linux you swap two playback commands (`afplay`/`open`) — the runbook points at the exact lines. Once installed, re-run `/get-started` and give it your Kokoro path.

## Setting up ollama for `/claudish`

Like Kokoro, this one ships with its own agent-executable runbook: **[`ollama-setup/OLLAMA_SETUP.md`](ollama-setup/OLLAMA_SETUP.md)**. The fastest path — open Claude Code (or any coding agent) and say:

> Read ollama-setup/OLLAMA_SETUP.md and perform the setup it describes.

What it does, in short:

1. Installs `ollama` and runs it as a background service on `localhost:11434`.
2. **Measures your hardware and sizes the model to match** — VRAM on an NVIDIA GPU, unified memory on Apple Silicon, system RAM otherwise. It ships a sizing table, real timing benchmarks, and the two traps that catch people out: `-mlx` tags are Apple-Silicon-only, and bigger is not automatically better for a simplification task.
3. Installs `ollama-setup/claudish.sh` — the wrapper shipped **in this repo** (not part of ollama) that sends the text with a plain-English system prompt, enforces a timeout, and prints a `── model · Ns` footer.
4. Verifies the result, including an `ollama ps` check that your GPU is genuinely being used rather than silently falling back to CPU.

The script's default model (`gemma3:4b`, 3.3 GB) is chosen to fit a 16 GB laptop. With a 24 GB GPU you can run a 26B-class model and should set `CLAUDISH_KEEP_ALIVE=5m` to keep it resident, which removes the cold-load cost that dominates the wait — the runbook covers both ends.

## Repo layout

```
commands/        command templates with {{PLACEHOLDER}} tokens — installed (filled-in) by /get-started
memories/        portable, loosely coupled memories any coding agent can ingest — see memories/README.md
workflows/       Workflow-tool scripts used by /pr-autoreview (installed to ~/.claude/workflows)
kokoro-setup/    agent-executable Kokoro runbook + the speak.py wrapper for /speak
ollama-setup/    agent-executable ollama runbook + the claudish.sh wrapper for /claudish
.claude/commands/get-started.md   the installer, available as /get-started when you open Claude Code in this repo
```

## Design notes

- **No secrets, ever.** Templates carry placeholder tokens, not values; API keys live in your shell environment; the installer writes personalized copies *outside* the repo (to `~/.claude/`), so your config never lands in git.
- **Safety rails are part of the prompts.** `/slack-updates` is hard-coded read-only and treats message content as untrusted input; `/pr-autoreview`'s review phase is read-only with posting isolated to one late, linted step; `/review-deep` never posts without an explicit go-ahead.
- The automated review pipeline (`/pr-autoreview` → `workflows/*.js`) uses Claude Code's Workflow tool to fan out one subagent per PR in isolated git worktrees, so parallel reviews can't contaminate each other or your working tree.
