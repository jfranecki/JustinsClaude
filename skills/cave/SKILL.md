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

Read `{{CAVE_DIR}}/PERSONALITY.md` in full, every run. It sets his mood for how the work went, his casting, what he calls the listener, his moves, his vocabulary, his delivery tags, and example reads. Follow it for everything about how he sounds.

If the file is missing, reply `Cave's personality file is missing: {{CAVE_DIR}}/PERSONALITY.md` and stop. Don't improvise him.

Then read `{{CAVE_DIR}}/recent-reads.txt`, his last eight reads with the newest last. The "Keep him fresh" rules in PERSONALITY.md are checked against it. If the file doesn't exist yet, there's no history to avoid.

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

## Step 4: Write the read to disk

Use the **Write** tool to write the tagged read, and nothing else (no quotes, no preamble), to the temp file below. The Write tool needs a platform-absolute path:

| Platform | Path to write |
|---|---|
| macOS / Linux | `/tmp/claude_cave_input.txt` |
| Windows | `%LOCALAPPDATA%\Temp\claude_cave_input.txt`, expanded, e.g. `C:\Users\<you>\AppData\Local\Temp\claude_cave_input.txt` |

On Windows that is the same file Git Bash sees as `/tmp/claude_cave_input.txt`. Step 5 resolves it either way.

## Step 5: Send it to ElevenLabs, log it, and play it

**Set the Bash tool's `timeout` to `600000`.** Every player in the block waits out the whole read. The 120-second default would cut off a long read after it has already been billed.

```bash
set -euo pipefail

VOICE_ID="{{CAVE_VOICE_ID}}"   # your Cave voice, see Voice below
MODEL_ID="eleven_v4"           # eleven_v4_turbo costs about half the credits, with less range
STABILITY=0.0                  # 0.0 most expressive (default) · 0.5 holds his voice tighter if a read drifts
CAVE_DIR="$(cygpath -u '{{CAVE_DIR}}' 2>/dev/null || echo '{{CAVE_DIR}}')"

: "${ELEVENLABS_API_KEY:?ELEVENLABS_API_KEY is not set. Set it in your shell profile (on Windows, at user scope) and start a new Claude Code session.}"
command -v jq >/dev/null || { echo "jq is required: brew install jq / apt install jq / winget install jqlang.jq" >&2; exit 1; }

# Resolve the input file written in Step 4 (Windows temp differs from /tmp on some setups).
IN=/tmp/claude_cave_input.txt
if [ ! -s "$IN" ] && [ -n "${LOCALAPPDATA:-}" ]; then
  ALT="$(cygpath -u "$LOCALAPPDATA" 2>/dev/null || echo "")/Temp/claude_cave_input.txt"
  if [ -s "$ALT" ]; then IN="$ALT"; fi
fi
OUT="$(dirname "$IN")/claude_cave_output.mp3"
[ -s "$IN" ] || { echo "Input file $IN is empty or missing. Did Step 4 write it?" >&2; exit 1; }

# Credit backstop: ElevenLabs bills per character, tags included.
ABS_MAX_CHARS=1800
CHARS=$(wc -m < "$IN" | tr -d '[:space:]')
if [ "$CHARS" -gt "$ABS_MAX_CHARS" ]; then
  echo "Refusing to send: ${CHARS} characters, over the ${ABS_MAX_CHARS}-character cap. Rewrite it shorter." >&2
  exit 1
fi

# Send the JSON through stdin with non-ASCII escaped (jq -a). If it's passed as a curl
# argument instead, an em-dash or ellipsis reaches ElevenLabs as invalid UTF-8 on Windows (HTTP 400).
# v4 takes only stability and similarity_boost; it has no style or speed setting.
HTTP=$(jq -a -Rs --arg model "$MODEL_ID" --argjson stab "$STABILITY" '{
  text: ., model_id: $model,
  voice_settings: {stability: $stab, similarity_boost: 0.75}
}' < "$IN" | curl -sS -o "$OUT" -w '%{http_code}' -X POST \
  "https://api.elevenlabs.io/v1/text-to-speech/${VOICE_ID}?output_format=mp3_44100_128" \
  -H "xi-api-key: ${ELEVENLABS_API_KEY}" -H "Content-Type: application/json" -H "Accept: audio/mpeg" \
  --data-binary @-)
if [ "$HTTP" != "200" ]; then
  echo "ElevenLabs returned HTTP $HTTP:" >&2; cat "$OUT" >&2; echo >&2; exit 1
fi

# Log the read for "Keep him fresh" in PERSONALITY.md: keep the last eight, newest last.
mkdir -p "$CAVE_DIR"
LOG="$CAVE_DIR/recent-reads.txt"
{ [ -f "$LOG" ] && tail -n 7 "$LOG"; printf '%s  %s\n' "$(date +%F)" "$(tr '\n' ' ' < "$IN")"; } > "$LOG.tmp"
mv "$LOG.tmp" "$LOG"

# Print the length before playback blocks, so a read that gets cut off is obvious. Non-fatal.
afinfo "$OUT" 2>/dev/null | grep -i 'estimated duration' \
  || ffprobe -v error -show_entries format=duration -of default=nw=1 "$OUT" 2>/dev/null \
  || true

# Play it: first available player wins (macOS, then cross-platform, then a Windows fallback).
if command -v afplay >/dev/null 2>&1; then
  afplay "$OUT"
elif command -v ffplay >/dev/null 2>&1; then
  ffplay -nodisp -autoexit -loglevel error "$OUT"
elif command -v mpv >/dev/null 2>&1; then
  mpv --really-quiet --no-video "$OUT"
elif command -v mpg123 >/dev/null 2>&1; then
  mpg123 -q "$OUT"
elif command -v cvlc >/dev/null 2>&1; then
  cvlc --play-and-exit --intf dummy "$OUT" >/dev/null 2>&1
elif command -v powershell.exe >/dev/null 2>&1; then
  WIN_OUT="$(cygpath -w "$OUT" 2>/dev/null || echo "$OUT")"
  powershell.exe -NoProfile -Command "
    Add-Type -AssemblyName presentationCore
    \$p = New-Object System.Windows.Media.MediaPlayer
    \$p.Open([uri]'$WIN_OUT'); Start-Sleep -Milliseconds 700
    \$d = \$p.NaturalDuration; if (\$d.HasTimeSpan) { \$p.Play(); Start-Sleep -Seconds ([int]\$d.TimeSpan.TotalSeconds + 1) }
    \$p.Close()"
else
  echo "No audio player found. Install ffmpeg (ffplay), mpv, or mpg123. Audio saved at: $OUT" >&2
  exit 1
fi
```

## Step 6: Confirm

Reply with one short line naming the tier and the Cave you played, e.g. `Cave has spoken · auto→brief · 1950s showman.` Don't repeat the read; the user just heard it. If the block printed an error, report it in one line.

## Voice

`VOICE_ID` in the Step 5 block is the ElevenLabs voice Cave speaks in. Any voice your API key can use will work; a booming mid-century pitchman suits him best. PERSONALITY.md bans accent and character-voice tags, so the voice itself has to carry the likeness.

The original is an Instant Voice Clone of a friend's Cave impression, made with that friend's permission, and it isn't shared. If you clone one, clone a voice you have the right to use, not the game's voice actor.

- **Model:** `eleven_v4`. It follows his delivery tags, phrase directions, and sound effects more closely than v3 did, and ElevenLabs says it holds a cloned voice more faithfully. It has only two settings, Stability and Similarity: no Style or Speed, and no SSML. `eleven_v4_turbo` costs about half the credits per character, with less range; set `MODEL_ID` in the block to use it.
- **Stability:** `0.0`, the most expressive end. On v3 it kept his likeness as well as `0.5` did, with more range. If a read drifts off his voice or overplays its tags, set `STABILITY=0.5` in the block.

## What not to do

- Don't run `/cave` on your own after responses. Only run it when the user asks.
- Don't read the response verbatim or narrate it from the outside. Cave is the one making the announcement.
- Don't let a bit bury the one thing the user has to do.
- Don't use character-voice or accent tags.
