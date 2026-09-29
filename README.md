# Claude Commands

A collection of battle-tested [Claude Code](https://claude.com/claude-code) slash commands: deep codebase onboarding, a state-of-the-project coldstart brief that catches you up on where past sessions left off, rigorous PR review (manual and fully automated), a safe end-of-session close-out, a read-only Slack briefing, two ways to have Claude read its answers aloud (plus a third, as [Cave Johnson](#cave---brief--medium--detailed-direction)), and a plain-English rewrite powered by a local LLM — plus an [orchestrator mode](#orchestrator-framework) that keeps long sessions coherent by delegating the heavy lifting, and a [library of portable engineering memories](#memories) any coding agent can ingest.

The files in `commands/` and `skills/` are **templates** — they contain `{{PLACEHOLDER}}` tokens for everything specific to you (GitHub username, repos, Slack channels, local paths). Nothing here assumes a particular company or codebase. The bundled `/get-started` installer interviews you, verifies your credentials, fills in the templates, and installs working commands into `~/.claude/`.

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

It will ask which commands you want, detect or ask for your details, **verify the required credentials and connections actually work** (GitHub CLI auth, Slack MCP, ElevenLabs key, Kokoro install, ollama daemon, Python 3), and install only the commands that pass. Anything that fails verification is skipped with instructions to fix it — just re-run `/get-started` afterwards; it's idempotent.

Newly installed commands are picked up when you start your next Claude Code session.

## The commands

### `/onboard [optional focus]`
Builds a deep, verified mental model of whatever repo your session is rooted in before you start working: structure and submodules, entry points and execution flow, dependencies and coupling, conventions, tests, CI gates, domain model, and recent direction. Ends with a structured briefing and offers to persist it for future sessions.
**Needs:** nothing — works in any repo.

### `/coldstart`
Full situational awareness when you start a fresh session in a project with history. A discovery pass reads the **filesystem**; it never reads your past conversations — yet on a project with months of history, that is where a lot of the decisions live, including ones that never reached a document. `/coldstart` reads both: structure, manifests and recent git activity, plus your prior Claude Code sessions for that directory.

Transcripts are treated as the *third* source, after committed docs and the git log, and they are **searched, never bulk-read** — they run to hundreds of megabytes. Search returns **your own messages by default**, newest first, and that default is the point: your turns are decisions, while assistant turns are reasoning that includes wrong turns and claims retracted later in the same session, with no signal in the text that they were withdrawn. `--all` includes them for reconstructing *how* something was worked out, as leads to verify rather than facts.

Everything a transcript claims was done is cross-referenced against `git log`, so work discussed but never committed is flagged **in progress** or **abandoned** instead of assumed done. Ends with a terse brief — current focus, recent decisions and rationale, open threads, known landmines, and any contradictions between docs, said out loud rather than silently resolved — then asks what you want to pick up. Where `/onboard` builds a mental model of the code, `/coldstart` reconstructs the story so far. It reads only your own local `~/.claude/projects/` history.
**Needs:** Python 3 — the transcript search is a stdlib-only sidecar script, installed for you, see below.

### `/bye`
The end-of-session bookend to `/onboard`: answers **"are we safe to close?"** before you kill the session. Read-only audit first — did the goal actually land, do tests pass, is anything uncommitted or unpushed, is a shared checkout stranded on a feature branch, which session-created worktrees and branches are confirmed-merged and safe to clean, and does any external tracker or doc still reflect reality (merge ≠ deploy). Then one severity-grouped report and a choice: finish the work, housekeep & close, or close anyway — the bypass path writes a handoff note so the next session doesn't start cold. Nothing state-changing runs without approval, and unmerged work is never force-deleted.
**Needs:** nothing — `gh` recommended for confirming merges (falls back to plain git checks).

### `/orchestrator [optional session goal]`
Turns a fresh session into an **orchestrator**: it plans, rules, and holds state, while subagents do the heavy lifting in their own disposable context and return summaries. The point is lifespan — bulk work done in the main context burns the window on output referenced once and never again, so delegation is the default and the orchestrator stays coherent instead of degrading into compaction. First it declares which model it is and therefore which tiers it may delegate to (**Fable > Opus > Sonnet > Haiku**, strictly below its own, never a same-tier peer, never a `fork` — a fork inherits the parent's model; the advisor is exempt because it is consulted, not spawned). Then it finds the file that actually governs how work is done here — **not assuming that is `CLAUDE.md`**, which in some projects is persona text or product content — reads whichever state register the project actually maintains, and reports position without re-asking what you have already answered. Ends with a tier line, the governing docs, where the work stands, and a proposed first move behind a 🟢/🟡/🔴 confidence gate. Delegation goes through tier-named worker agents — `sonnet-worker`, `haiku-worker`, `opus-worker` — whose frontmatter pins the model, so the agent panel and task list show the tier of every running subagent by name instead of leaving you to infer it. Pairs with the [Orchestrator Framework](Orchestrator%20Framework/) bundled in this repo, which carries the full writeup, the worker-agent files, the drop-in `CLAUDE.md` blocks, and the retrofit path for projects that already have their own conventions.
**Needs:** nothing — works standalone; richer if the framework path is filled in.

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
Premium narration via **ElevenLabs v4**: summarizes the last response and performs it with expressive inline audio tags, from single words to natural-language direction (`[wry]`, `[sighs]`, `[short pause]`, `[dry, quietly pleased with himself]`…). The **voice flag is required** — `--f` is a laid-back Australian female voice, `--m` a crisp British "Q from James Bond" — and matching is on exact tokens, so `--m` is always the male voice and `--medium` always the length tier. Pass any personality ("gruff sailor", "deadpan comedian") to recolor the read. Length auto-scales to the response or is forced with a flag, and a hard 1,800-character cap protects your ElevenLabs credits. The read streams, so the voice starts about a second after the call instead of after the whole render. Both voice IDs are one-line changes in `commands/speak-api.sh`, the script the command runs.
**Needs:** `ELEVENLABS_API_KEY` in your environment (free tier works), `jq`, and an audio player, auto-detected: `ffplay`/`mpv`/`mpg123` stream the read; `afplay` on macOS, `cvlc`, or a PowerShell fallback on Windows download it first.

### `/cave [--brief|--medium|--detailed] [direction]`
Has Cave Johnson, founder and CEO of Aperture Science, read back what just happened. The gist of the last response is rewritten as one of his pre-recorded announcements to a test subject and performed through ElevenLabs v4. His mood follows the outcome: a 1950s showman when it worked, a broke 1970s Cave when it half-worked, a moon-rock-poisoned 1980s Cave when it failed. The lab boys take the blame, Greg corrects him off mic, and anything you have to do next survives the jokes. It keeps a log of his last eight reads so his openers, bits, and sign-off don't repeat. Any text after the flag is a stage direction (`/cave furious`, `/cave bring up Black Mesa`).

It's a skill rather than a command, so Claude also runs it when you ask to hear something in Cave's voice. The mechanics are in `skills/cave/SKILL.md`, and `skills/cave/speak.sh` streams the read so he starts talking about a second after the call. Who he is lives in a separate [`PERSONALITY.md`](cave-setup/PERSONALITY.md) that's read on every run, so you can retune him without touching the skill. It has its own length tiers (brief, medium, detailed, or auto), and its 1,800-character credit cap matches `/speak-api`'s.
**Needs:** `ELEVENLABS_API_KEY`, `jq`, an audio player, and an ElevenLabs voice for Cave. Any voice your key can use works. The original is a private clone of a friend's impression that isn't shared, so bring your own. If you clone one, use a voice you have the right to, not the game's voice actor.

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

## Orchestrator Framework

[`Orchestrator Framework/`](Orchestrator%20Framework/) is a way of running long Claude Code sessions, and [`/orchestrator`](#orchestrator-optional-session-goal) is the command that switches a session into it. The framework is the writeup; the command is the on-ramp.

### The idea

**The orchestrator's context window is the scarce resource, and delegation is what extends its lifespan.** Heavy lifting done in the main session — full log dumps, recursive scans, long file reads, large query results — burns the window on output that gets referenced once and never again. Push that work into subagents and only the conclusions come back, so the session stays coherent across hours of work instead of degrading into compaction.

A subagent's context is disposable. The orchestrator's is not. Every rule below follows from that sentence, and it is the tiebreaker whenever a judgment call about delegating is close.

So you talk to **one session, the orchestrator**. It plans, elicits decisions, rules on tradeoffs, and maintains state. Subagents do the legwork in their own disposable context and return summaries. **Gathering goes down, judgment stays up** — rulings, the final call, and anything needing context only you hold are never delegated, but collecting the evidence behind them is exactly what subagents are for. You read the orchestrator, not its workers.

### The model hierarchy

Tiers, strongest first: **Fable > Opus > Sonnet > Haiku**. An orchestrator spawns subagents **strictly below its own tier** — never its own tier, never higher. Fable spawns Opus or Sonnet; Opus spawns Sonnet or Haiku. Reasoning stays at the top and legwork goes down: two peers deliberating is waste, and a worker outranking its orchestrator inverts who is supposed to be ruling.

In practice that means delegating through the bundled tier-named worker agents — `opus-worker`, `sonnet-worker`, `haiku-worker`, copied once to `~/.claude/agents/` — whose frontmatter pins the model, so the `model` parameter is omitted and the type name shown in the agent panel and task list *is* the tier. (Where they are not installed: pass the model explicitly on every delegation rather than relying on a default that may match your own tier, and prefix the description with the tier so it still shows on screen.) It also means never using a `fork`-style subagent to delegate — a fork inherits the parent's model and ignores the override, breaking the hierarchy by construction. The advisor is the one exception: it is **consulted, not spawned**, so the tier rule does not bind it and any agent may call it at any depth. Consulting upward is the one direction the hierarchy does not restrict.

### State that outlives the window

Delegation keeps the window from filling; a written state record makes filling *survivable*. Decisions written down live outside the context window, so a compacted or restarted session resumes from the file instead of from memory it no longer has. Write rulings when they are made, not when the window gets tight.

Two failure modes the framework designs against, both learned the hard way:

- **Status rots; dated rulings do not.** "On <date> we decided X because Y" stays true forever. "Current phase: 3" is wrong within a week. Keep the append-only rulings log and be sparing with anything claiming present state — read any status line you find as a *start date*, not a state.
- **Never let one doc point at another doc as authoritative.** The recurring failure in mature repos is a pointer problem, not a prose problem: every doc names another as the source of truth, and the targets drift. Point at code and at reality.

Which is why the framework requires the *function*, not the filename. A project may already run this under its own names — a handoff or "brain" file, a rulings ledger, a parked-questions file. Where that exists, extend it. A second state surface is worse than none.

### Adopting it

Four things are decided per project, not inherited: whether subagents may change things or are read-only; what the audit trail is (in a git-tracked project, the commits already are one); whether spec/stage machinery applies; and the project's own hard rules and protected paths.

For an existing project, **step one is to audit what it already does, and it can cancel the rest.** A mature project may have invented most of this under other names, may keep its working agreement somewhere other than `CLAUDE.md`, and may have *documented reasons* for refusing an artifact this framework recommends. Those reasons win — they are evidence, the framework is a default. Adopting a framework wholesale over a project that already solved the problem is the failure this step exists to prevent.

The folder ships three files: `README.md` (the writeup and adoption steps), `CLAUDE-sections-template.md` (drop-in blocks with `{{placeholder}}` tokens), and `STATE-template.md` (a state-file skeleton to use only if step one says you need one).

### When to run `/orchestrator`

Not "new projects only." The rule is: **run it wherever the framework is not already auto-loaded into the session.** A project *having* the framework and a session *seeing* it are different things.

| Situation | Run it? |
|---|---|
| Project has no framework yet — new or existing | **Yes.** This is the on-ramp. |
| Framework lives in a file the session does not auto-load — e.g. `CLAUDE.md` is persona text, a prompt, or product content, and the working agreement is in `docs/DEV_CONTINUE.md` or `CONTRIBUTING.md` | **Yes — the best case for it.** Nothing else performs that mode switch. |
| Project has the orchestrator conventions but no tier rule | **Optional.** Adds the tier declaration; the rest is already established. |
| `CLAUDE.md` carries the framework and auto-loads it | **Skip.** Pure ceremony. |

The command's unique value is its first step: declaring which model the session is, and therefore which tiers it may delegate to, **before it spawns anything**. That cannot live in a static doc, because which model a session runs varies per launch. Everything else it does is loading and ritual — which is why it is never harmful where the framework is already loaded, only redundant.

## Setting up `history.py` for `/coldstart`

No setup needed — `/get-started` copies **[`coldstart-setup/history.py`](coldstart-setup/history.py)** to `~/.claude/bin/` and points the installed command at it. Python 3 is the only requirement: the script is stdlib-only, with no pip install, no virtualenv, and no network.

It exists as a script rather than an inline one-liner because three things quietly corrupt a briefing otherwise: sessions started in a **worktree or subdirectory** are filed under the parent project, so exact path-encoding misses and reports no history; transcripts are full of `<system-reminder>` and hook output that reads like the user talking but isn't; and at hundreds of megabytes they have to be searched rather than loaded. It is also usable on its own — `index`, `recent`, and `search` against any project's history. Details and manual install: **[`coldstart-setup/COLDSTART_SETUP.md`](coldstart-setup/COLDSTART_SETUP.md)**.

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
skills/          skill templates, same idea, installed to ~/.claude/skills (currently /cave)
cave-setup/      Cave Johnson's PERSONALITY.md, installed next to his read log for /cave
memories/        portable, loosely coupled memories any coding agent can ingest — see memories/README.md
Orchestrator Framework/   the orchestrator writeup, the CLAUDE.md and STATE.md templates, and the
                          tier-named worker agents (installed to ~/.claude/agents), used by /orchestrator
workflows/       Workflow-tool scripts used by /pr-autoreview (installed to ~/.claude/workflows)
kokoro-setup/    agent-executable Kokoro runbook + the speak.py wrapper for /speak
ollama-setup/    agent-executable ollama runbook + the claudish.sh wrapper for /claudish
.claude/commands/get-started.md   the installer, available as /get-started when you open Claude Code in this repo
```

## Design notes

- **No secrets, ever.** Templates carry placeholder tokens, not values; API keys live in your shell environment; the installer writes personalized copies *outside* the repo (to `~/.claude/`), so your config never lands in git.
- **Safety rails are part of the prompts.** `/slack-updates` is hard-coded read-only and treats message content as untrusted input; `/pr-autoreview`'s review phase is read-only with posting isolated to one late, linted step; `/review-deep` never posts without an explicit go-ahead.
- The automated review pipeline (`/pr-autoreview` → `workflows/*.js`) uses Claude Code's Workflow tool to fan out one subagent per PR in isolated git worktrees, so parallel reviews can't contaminate each other or your working tree.
