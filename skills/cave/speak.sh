#!/usr/bin/env bash
# /cave's sender. The skill writes the read to the temp file, then runs this.
# It streams the read from ElevenLabs straight into a player that reads stdin
# (ffplay, mpv or mpg123), so Cave starts on the first chunk (about 1 s) instead
# of after the whole render (about 15 s for a medium read). With none of those
# installed it downloads the read first, then plays it.
set -euo pipefail

VOICE_ID="{{CAVE_VOICE_ID}}"   # your Cave voice, see Voice in SKILL.md
MODEL="eleven_v4"              # eleven_v4_turbo costs about half the credits, with less range
STABILITY=0.0                  # 0.0 most expressive (default) · 0.5 holds the voice tighter if a read drifts
# v4 keeps a clone's sample loudness (about -20 LUFS for the original Cave clone), where v3
# pushed it to about -13. ffplay adds this gain behind a limiter; $OUT stays unboosted. 0 disables it.
PLAY_GAIN_DB=6.5
CAVE_DIR="$(cygpath -u '{{CAVE_DIR}}' 2>/dev/null || echo '{{CAVE_DIR}}')"

: "${ELEVENLABS_API_KEY:?ELEVENLABS_API_KEY is not set. Set it in your shell profile (on Windows, at user scope) and start a new Claude Code session.}"
command -v jq >/dev/null || { echo "jq is required: brew install jq / apt install jq / winget install jqlang.jq" >&2; exit 1; }

# Resolve the input file the skill wrote (Windows temp differs from /tmp on some setups).
IN=/tmp/claude_cave_input.txt
if [ ! -s "$IN" ] && [ -n "${LOCALAPPDATA:-}" ]; then
  ALT="$(cygpath -u "$LOCALAPPDATA" 2>/dev/null || echo "")/Temp/claude_cave_input.txt"
  if [ -s "$ALT" ]; then IN="$ALT"; fi
fi
OUT="$(dirname "$IN")/claude_cave_output.mp3"
[ -s "$IN" ] || { echo "No new read at $IN. Did the Write step run?" >&2; exit 1; }

# Consume the input, so a Write that failed can never replay the previous read.
# (It also lets the next Write create the file fresh, even after a refusal below.)
SENT="$IN.last"
mv -f "$IN" "$SENT"

# Credit backstop: ElevenLabs bills per character, tags included.
ABS_MAX_CHARS=1800
CHARS=$(wc -m < "$SENT" | tr -d '[:space:]')
if [ "$CHARS" -gt "$ABS_MAX_CHARS" ]; then
  echo "Refusing to send: ${CHARS} characters, over the ${ABS_MAX_CHARS}-character cap. Rewrite it shorter." >&2
  exit 1
fi

# Send the JSON through stdin with non-ASCII escaped (jq -a). If it's passed as a curl
# argument instead, an em-dash or ellipsis reaches ElevenLabs as invalid UTF-8 on Windows (HTTP 400).
payload() {
  jq -a -Rs --arg model "$MODEL" --argjson stab "$STABILITY" '{
    text: ., model_id: $model,
    voice_settings: {stability: $stab, similarity_boost: 0.75}
  }' < "$SENT"
}
URL="https://api.elevenlabs.io/v1/text-to-speech/${VOICE_ID}"
HDRS=(-H "xi-api-key: ${ELEVENLABS_API_KEY}" -H "Content-Type: application/json" -H "Accept: audio/mpeg")

# Stream into the first player that reads stdin.
if command -v ffplay >/dev/null 2>&1; then
  PLAYER=(ffplay -nodisp -autoexit -loglevel error -f mp3 -probesize 32 -analyzeduration 0 -i -
          -af "volume=${PLAY_GAIN_DB}dB,alimiter=limit=0.891:level=0")
elif command -v mpv >/dev/null 2>&1; then
  PLAYER=(mpv --really-quiet --no-video --cache=no -)
elif command -v mpg123 >/dev/null 2>&1; then
  PLAYER=(mpg123 -q -)
else
  PLAYER=()
fi

if [ ${#PLAYER[@]} -gt 0 ]; then
  set +e
  payload | curl -sS -N --fail-with-body -X POST "${URL}/stream?output_format=mp3_44100_128" "${HDRS[@]}" --data-binary @- \
    | tee "$OUT" | "${PLAYER[@]}"
  ST=("${PIPESTATUS[@]}")
  set -e
  if [ "${ST[1]}" != "0" ]; then
    echo "ElevenLabs request failed (curl exit ${ST[1]}):" >&2; cat "$OUT" >&2; echo >&2; exit 1
  fi
  if [ "${ST[3]}" != "0" ]; then
    echo "${PLAYER[0]} exited ${ST[3]}, so nothing may have played. The audio is saved at $OUT" >&2; exit 1
  fi
else
  # No stdin player: download the whole read, then play it.
  HTTP=$(payload | curl -sS -o "$OUT" -w '%{http_code}' -X POST "${URL}?output_format=mp3_44100_128" "${HDRS[@]}" --data-binary @-)
  if [ "$HTTP" != "200" ]; then
    echo "ElevenLabs returned HTTP $HTTP:" >&2; cat "$OUT" >&2; echo >&2; exit 1
  fi
  if command -v afplay >/dev/null 2>&1; then
    afplay "$OUT"
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
fi

# Log the read for "Keep him fresh" in PERSONALITY.md: keep the last eight, newest last.
mkdir -p "$CAVE_DIR"
LOG="$CAVE_DIR/recent-reads.txt"
{ [ -f "$LOG" ] && tail -n 7 "$LOG"; printf '%s  %s\n' "$(date +%F)" "$(tr '\n' ' ' < "$SENT")"; } > "$LOG.tmp"
mv "$LOG.tmp" "$LOG"

# Length of what played, so a read cut off by the tool timeout is obvious. Non-fatal.
afinfo "$OUT" 2>/dev/null | grep -i 'estimated duration' \
  || ffprobe -v error -show_entries format=duration -of default=nw=1 "$OUT" 2>/dev/null \
  || true
