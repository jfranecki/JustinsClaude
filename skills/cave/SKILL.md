---
name: cave
description: Voice the previous response as Cave Johnson from Portal 2. The gist is rewritten as one of his pre-recorded Aperture Science announcements and performed through ElevenLabs v4 on the local speakers. Use when the user types /cave or asks to hear the last response in Cave Johnson's voice.
argument-hint: "[--brief|--medium|--detailed] [direction, e.g. furious]"
allowed-tools: Read, Write, Bash
user-invocable: true
---

# /cave: Cave Johnson reads it back

Speak your most recent assistant message aloud as Cave Johnson, founder and CEO of Aperture Science. This is not a read-aloud, and not a summary with an accent. Keep the gist of what happened, rewritten as one of his pre-recorded announcements to a test subject, with his bits, his mood, and his sign-off.

This file is the mechanics. **Who Cave is and how he talks lives in `{{CAVE_DIR}}/PERSONALITY.md`.**

## Arguments for this run

$ARGUMENTS

(Whatever the user typed after `/cave`. If the line above is the literal placeholder, read the arguments the harness appended instead.)

- **Length flag, optional:** `--brief`, `--medium`, or `--detailed`, matched as exact tokens. With no flag the length is **auto**.
- **Direction, optional:** any text left after the flag is a stage direction for this read, such as `furious`, `bring up Black Mesa`, or `he's in a great mood`. It overrides the mood his personality would pick.

## Step 1: Find the source

Use the most recent assistant message before `/cave` was invoked. Skip past /cave's own one-line confirmations (`Cave has spoken · …`) to the last message with real content. If there is none, reply `Nothing for Cave to announce yet. Run /cave after I've said something.` and stop.

## Step 2: Read his personality

Read both files **in one message** (two Read calls side by side), every run:

- `{{CAVE_DIR}}/PERSONALITY.md`, in full. It sets his mood for how the work went, his casting, what he calls the listener, his moves, his vocabulary, his delivery tags, and example reads. Follow it for everything about how he sounds.
- `{{CAVE_DIR}}/recent-reads.txt`, his last eight reads with the newest last. The "Keep him fresh" rules in PERSONALITY.md are checked against it.

If PERSONALITY.md is missing, reply `Cave's personality file is missing: {{CAVE_DIR}}/PERSONALITY.md` and stop. Don't improvise him. If recent-reads.txt doesn't exist yet, there's no history to avoid.

## Step 3: Write the read

**Carry the gist and spend the rest on Cave.** Say what happened and what the listener has to do next, if anything. That's one or two facts. Everything else is his.

- If the source ended with a question or a decision for the user, Cave must put it to them. Barking it as an order is fine. It stays in even if a joke has to go.
- Translate into his words but keep it recognizable: a bug is a gremlin, the code is the gizmo or the machine, a deploy is a launch. No file paths, code, commands, URLs, or version numbers, unless the number is the joke.
- Invented comedy is fine; invented facts are not. Never claim something worked that didn't, or add results the source doesn't have.
- If the source is already a Cave read, don't rewrite it. Re-tag it and perform it again.

Tag it following the delivery tags in PERSONALITY.md.

**Length tiers.** The character ceiling counts the tags, because ElevenLabs bills per character.

| Tier | Selected by | Target | Bits | Ceiling |
|---|---|---|---|---|
| brief | `--brief` | 2–4 sentences | 1 | 450 |
| medium | `--medium` | 5–8 sentences | 1–2 | 900 |
| detailed | `--detailed` | 9–14 sentences | 2–3 | 1500 |
| auto | no flag | the smallest tier that fits the gist plus a bit, usually brief or medium | | 1500 |

## Steps 4 and 5: Write the read and play it, in one message

Make **both tool calls in the same message**, Write first. They run in order, so the script sees the fresh file, and the user hears Cave one round trip sooner.

1. **Write** the tagged read, and nothing else (no quotes, no preamble), to the temp file below. The Write tool needs a platform-absolute path:

   | Platform | Path to write |
   |---|---|
   | macOS / Linux | `/tmp/claude_cave_input.txt` |
   | Windows | `%LOCALAPPDATA%\Temp\claude_cave_input.txt`, expanded, e.g. `C:\Users\<you>\AppData\Local\Temp\claude_cave_input.txt` |

   On Windows that is the same file Git Bash sees as `/tmp/claude_cave_input.txt`. The script resolves it either way.

2. **Bash**, with `timeout` set to `600000`:

   ```bash
   bash ~/.claude/skills/cave/speak.sh
   ```

   The script streams the read from ElevenLabs into a player that reads stdin (`ffplay`, `mpv` or `mpg123`), so Cave starts talking about a second after the call; with none of those it downloads first, then plays. It blocks until he finishes, and the 120-second default timeout would cut off a long read that has already been billed. It enforces the character cap, logs the read to `recent-reads.txt`, prints the read's length, and consumes the input file, so a Write that failed can never replay the previous read. The voice, model and stability are set at the top of the script.

## Step 6: Confirm

Reply with one short line naming the tier and the Cave you played, e.g. `Cave has spoken · auto→brief · 1950s showman.` Don't repeat the read; the user just heard it. If the script printed an error, report it in one line.

## Voice

`VOICE_ID` at the top of `speak.sh` is the ElevenLabs voice Cave speaks in. Any voice your API key can use will work; a booming mid-century pitchman suits him best. PERSONALITY.md bans accent and character-voice tags, so the voice itself has to carry the likeness.

The original is an Instant Voice Clone of a friend's Cave impression, made with that friend's permission, and it isn't shared. If you clone one, clone a voice you have the right to use, not the game's voice actor.

- **Model:** `eleven_v4`. It follows his delivery tags, phrase directions, and sound effects more closely than v3 did, and ElevenLabs says it holds a cloned voice more faithfully. It has only two settings, Stability and Similarity: no Style or Speed, and no SSML. `eleven_v4_turbo` costs about half the credits per character, with less range; set `MODEL` in `speak.sh` to use it.
- **Stability:** `0.0`, the most expressive end. On v3 it kept his likeness as well as `0.5` did, with more range. If a read drifts off his voice or overplays its tags, set `STABILITY=0.5` in `speak.sh`.

## What not to do

- Don't run `/cave` on your own after responses. Only run it when the user asks.
- Don't read the response verbatim or narrate it from the outside. Cave is the one making the announcement.
- Don't let a bit bury the one thing the user has to do.
- Don't use character-voice or accent tags.
