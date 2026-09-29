#!/usr/bin/env bash
# /speak-api's sender: bash speak-api.sh f|m
# Streams the tagged summary from ElevenLabs straight into a player that reads
# stdin (ffplay, mpv or mpg123), so the voice starts on the first chunk (about
# 1 s) instead of after the whole render (13 s for a medium read). With none of
# those installed it downloads first, then plays, as before.
set -euo pipefail

VOICE="${1:-UNSET}"
# Voice IDs — change these to swap voices (browse: https://elevenlabs.io/app/voice-library).
VOICE_ID_F="u8ADrbquiJqufR9XMtb8"   # laid back friendly Australian girl
VOICE_ID_M="lF0PpOQjCl3K89rt0U83"   # young professional British male ("Q")
MODEL="eleven_v4"                   # Eleven v4; the audio tags need v3 or later
STABILITY=0.0                       # 0.0 most expressive · 0.5 holds the voice tighter if a read drifts

case "$VOICE" in
  f) VOICE_ID="$VOICE_ID_F" ;;
  m) VOICE_ID="$VOICE_ID_M" ;;
  *) echo "Usage: speak-api.sh f|m (got '$VOICE'). Never guess a voice." >&2; exit 1 ;;
esac

: "${ELEVENLABS_API_KEY:?ELEVENLABS_API_KEY is not set — see 'Required setup' in speak-api.md. On Windows, set it for the User scope and start a NEW Claude Code session.}"
command -v jq >/dev/null || { echo "jq is required — brew install jq / apt install jq / winget install jqlang.jq" >&2; exit 1; }

# Resolve the input file the command wrote (Windows temp differs from /tmp on some setups).
IN=/tmp/claude_speak_api_input.txt
if [ ! -s "$IN" ] && [ -n "${LOCALAPPDATA:-}" ]; then
  ALT="$(cygpath -u "$LOCALAPPDATA" 2>/dev/null || echo "")/Temp/claude_speak_api_input.txt"
  if [ -s "$ALT" ]; then IN="$ALT"; fi
fi
OUT="$(dirname "$IN")/claude_speak_api_output.mp3"
[ -s "$IN" ] || { echo "No new summary at $IN — did the Write step run?" >&2; exit 1; }

# Consume the input, so a Write that failed can never replay the previous summary.
# (It also lets the next Write create the file fresh, even after a refusal below.)
SENT="$IN.last"
mv -f "$IN" "$SENT"

# Hard credit backstop — ElevenLabs bills per character (audio tags count too).
ABS_MAX_CHARS=1800
CHARS=$(wc -m < "$SENT" | tr -d '[:space:]')
if [ "$CHARS" -gt "$ABS_MAX_CHARS" ]; then
  echo "Refusing to send: input is ${CHARS} characters, over the ${ABS_MAX_CHARS}-char credit cap." >&2
  echo "Re-run with --brief or --medium, or raise ABS_MAX_CHARS in speak-api.sh if this was intentional." >&2
  exit 1
fi

# JSON through stdin with non-ASCII escaped (jq -a): as a curl argument, an em-dash
# or ellipsis can reach ElevenLabs as invalid UTF-8 on Windows (HTTP 400).
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
  PLAYER=(ffplay -nodisp -autoexit -loglevel error -f mp3 -probesize 32 -analyzeduration 0 -i -)
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
  # Length of what played, so a read cut off by the tool timeout is obvious.
  ffprobe -v error -show_entries format=duration -of default=nw=1 "$OUT" 2>/dev/null || true
  exit 0
fi

# No stdin player: download the whole clip, then play it.
HTTP=$(payload | curl -sS -o "$OUT" -w '%{http_code}' -X POST "${URL}?output_format=mp3_44100_128" "${HDRS[@]}" --data-binary @-)
if [ "$HTTP" != "200" ]; then
  echo "ElevenLabs returned HTTP $HTTP. Body:" >&2; cat "$OUT" >&2; exit 1
fi
afinfo "$OUT" 2>/dev/null | grep -i 'estimated duration' || true
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
