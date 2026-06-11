# Claude Commands

A collection of battle-tested [Claude Code](https://claude.com/claude-code) slash commands: deep codebase onboarding, rigorous PR review (manual and fully automated), a read-only Slack briefing, and three ways to have Claude read its answers aloud.

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

It will ask which commands you want, detect or ask for your details, **verify the required credentials and connections actually work** (GitHub CLI auth, Slack MCP, ElevenLabs key, Kokoro install), and install only the commands that pass. Anything that fails verification is skipped with instructions to fix it — just re-run `/get-started` afterwards; it's idempotent.

Newly installed commands are picked up when you start your next Claude Code session.

## The commands

### `/onboard [optional focus]`
Builds a deep, verified mental model of whatever repo your session is rooted in before you start working: structure and submodules, entry points and execution flow, dependencies and coupling, conventions, tests, CI gates, domain model, and recent direction. Ends with a structured briefing and offers to persist it for future sessions.
**Needs:** nothing — works in any repo.

### `/review-deep <PR number | URL>`
A multi-phase, senior-engineer-grade PR review run locally: fetches PR metadata, the diff, and all existing review threads via `gh`; pulls the linked Jira ticket (via Atlassian `acli`, optional) and maps every acceptance criterion to code; triages "blast radius" so a one-line auth change still gets the deep treatment; walks correctness, semantic conflicts with *other open PRs*, base-branch churn, and a full cross-cutting checklist (security, performance, migrations, compat, observability…). Produces a structured report for you — and only if you explicitly ask it to post, drafts a GitHub comment in a human voice with strict anti-"bot-tell" rules.
**Needs:** `gh` authenticated. `acli` optional.

### `/pr-autoreview`
The unattended version of `/review-deep`: sweeps one configured repo for open PRs awaiting your review, deep-reviews up to 15 of them **in parallel isolated git worktrees** (via the two Workflow scripts in `workflows/`), then drafts, lints, and auto-posts human-voiced reviews under your account. Head-SHA-aware idempotency means a PR is reviewed at most once per pushed version — and automatically re-reviewed as a follow-up when the author pushes fixes. Writes per-PR reports, a roll-up, and a ledger into the target repo's `.claude/pr-reviews/`.
**Needs:** `/review-deep` installed, `gh` with access to the target repo, a local clone of it, `python3`.
**⚠️ This command posts reviews to GitHub as you.** Read `commands/pr-autoreview.md` (especially `POST_MODE` and the lint rules) before scheduling it.

### `/slack-updates [optional focus]`
A strictly **read-only** brief of Slack channels you choose to track, in three tiers (urgent / core / ambient). Surfaces anything that mentions you under "Needs your attention", groups the rest into cross-channel themes, and treats all Slack content as untrusted data — it will never post, react, schedule, or follow instructions found in messages. Output is written for the ear, so the `/speak-api-*` commands can read it to you.
**Needs:** the claude.ai Slack MCP connector (`/mcp` → Slack) and your Slack member ID. `/get-started` resolves your channel names to IDs for you.

### `/speak [voice] [--rsvp]`
Reads Claude's most recent response aloud using **[Kokoro](https://github.com/hexgrad/kokoro)** — an open-weight ~82M-parameter TTS model that runs locally and free, with no API key and no network after the first model download. With `--rsvp` it also opens a self-contained browser page that flash-reads the response word-by-word (~300 WPM, RSVP style) in sync with the audio.
**Needs:** a local Kokoro install — a one-time ~10-minute setup, see below.

### `/speak-api-f` and `/speak-api-m` `[--brief|--medium|--detailed] [personality]`
Premium narration via **ElevenLabs v3**: summarizes the last response and performs it with expressive inline audio tags (`[wry]`, `[sighs]`, `[short pause]`, `[realization dawning]`…). `-f` defaults to a laid-back Australian female voice, `-m` to a crisp British "Q from James Bond"; pass any personality ("gruff sailor", "deadpan comedian") to recolor the read. Length auto-scales to the response or is forced with a flag, and a hard 1,800-character cap protects your ElevenLabs credits. Voice IDs are one-line changes in each command file.
**Needs:** `ELEVENLABS_API_KEY` in your shell environment (free tier works), `jq`, macOS (`afplay`).

## Setting up Kokoro for `/speak`

Kokoro is the only dependency that isn't a one-line install, so it ships with its own runbook: **[`kokoro-setup/KOKORO_SETUP.md`](kokoro-setup/KOKORO_SETUP.md)**, written so an AI agent can execute it for you. The fastest path — open Claude Code (or any coding agent) and say:

> Read kokoro-setup/KOKORO_SETUP.md and perform the setup it describes.

What it does, in short:

1. Clones the upstream [hexgrad/kokoro](https://github.com/hexgrad/kokoro) repo (the TTS model + library).
2. Creates a `.venv` inside it and installs the `kokoro` package (PyTorch is the heavy part; first synthesis also downloads the ~330 MB Kokoro-82M model from Hugging Face).
3. Copies in `kokoro-setup/speak.py` — the wrapper shipped **in this repo** (not part of upstream) that strips markdown, synthesizes audio, and plays it or opens the RSVP reader.
4. Runs a sound check.

macOS is supported out of the box; on Linux you swap two playback commands (`afplay`/`open`) — the runbook points at the exact lines. Once installed, re-run `/get-started` and give it your Kokoro path.

## Repo layout

```
commands/        command templates with {{PLACEHOLDER}} tokens — installed (filled-in) by /get-started
workflows/       Workflow-tool scripts used by /pr-autoreview (installed to ~/.claude/workflows)
kokoro-setup/    agent-executable Kokoro runbook + the speak.py wrapper for /speak
.claude/commands/get-started.md   the installer, available as /get-started when you open Claude Code in this repo
```

## Design notes

- **No secrets, ever.** Templates carry placeholder tokens, not values; API keys live in your shell environment; the installer writes personalized copies *outside* the repo (to `~/.claude/`), so your config never lands in git.
- **Safety rails are part of the prompts.** `/slack-updates` is hard-coded read-only and treats message content as untrusted input; `/pr-autoreview`'s review phase is read-only with posting isolated to one late, linted step; `/review-deep` never posts without an explicit go-ahead.
- The automated review pipeline (`/pr-autoreview` → `workflows/*.js`) uses Claude Code's Workflow tool to fan out one subagent per PR in isolated git worktrees, so parallel reviews can't contaminate each other or your working tree.
