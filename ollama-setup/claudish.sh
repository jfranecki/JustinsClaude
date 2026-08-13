#!/usr/bin/env bash
# ---------------------------------------------------------------------------
# claudish.sh — on-demand plain-English rewrite via the local ollama model.
#
# Companion to the claudish-to-english plugin's automatic MessageDisplay hook.
# Same model, same system prompt, same voice — but invoked deliberately via
# the /claudish command instead of firing on every assistant message.
#
# Because this is not a display hook it is NOT bound by the plugin's 60s hook
# timeout, so it can afford a much longer budget on long messages.
#
#   usage: claudish.sh <file>          # file holds the text to rewrite
#
#   CLAUDISH_MODEL        ollama model   (default gemma3:4b)
#   CLAUDISH_OLLAMA       base url       (default http://localhost:11434)
#   CLAUDISH_CMD_TIMEOUT  seconds        (default 300)
#
# Exits non-zero with a one-line reason on stderr for any failure. The caller
# must NOT silently substitute its own rewrite — the whole point is the local
# model.
# ---------------------------------------------------------------------------
set -uo pipefail

MODEL="${CLAUDISH_MODEL:-gemma3:4b}"
OLLAMA="${CLAUDISH_OLLAMA:-http://localhost:11434}"
TIMEOUT="${CLAUDISH_CMD_TIMEOUT:-300}"
# Unload the model as soon as the response is done. This command is invoked by
# hand, so ollama's default 5m idle window would just pin ~3GB of a 16GB box
# doing nothing between runs. Cost: each run pays the model load (~1-2s warm
# page cache). Set to "5m" (or any Go duration) to keep it resident instead.
KEEP_ALIVE="${CLAUDISH_KEEP_ALIVE:-0}"

src="${1:-}"
[ -n "$src" ] && [ -f "$src" ] || { echo "claudish: usage: claudish.sh <file>" >&2; exit 2; }

command -v jq   >/dev/null 2>&1 || { echo "claudish: jq is required" >&2; exit 1; }
command -v curl >/dev/null 2>&1 || { echo "claudish: curl is required" >&2; exit 1; }

full="$(cat "$src")"
[ -n "${full//[[:space:]]/}" ] || { echo "claudish: input file is empty" >&2; exit 2; }

# Fail fast and clearly if the daemon is down, rather than burning the timeout.
curl -sS --max-time 5 "$OLLAMA/api/tags" >/dev/null 2>&1 \
  || { echo "claudish: can't reach ollama at $OLLAMA — start it with \`ollama serve\`" >&2; exit 1; }

sys="You rewrite the assistant's message into much simpler, plain English. Keep every fact, name, number, and file path. Use short sentences and everyday words. Leave fenced code blocks unchanged. Output ONLY the rewritten message with no preamble, labels, or commentary."

req="$(jq -n --arg m "$MODEL" --arg s "$sys" --arg u "$full" --arg k "$KEEP_ALIVE" \
      '{model:$m,stream:false,think:false,keep_alive:$k,options:{temperature:0.3},
        messages:[{role:"system",content:$s},{role:"user",content:$u}]}' 2>/dev/null)"
[ -n "$req" ] || { echo "claudish: could not build request" >&2; exit 1; }

start="$(date +%s)"
resp="$(printf '%s' "$req" | curl -sS --max-time "$TIMEOUT" \
        -H 'Content-Type: application/json' -X POST "$OLLAMA/api/chat" -d @- 2>/dev/null)"
rc=$?
elapsed=$(( $(date +%s) - start ))

if [ "$rc" -eq 28 ]; then
  echo "claudish: timed out after ${TIMEOUT}s on '$MODEL' — raise CLAUDISH_CMD_TIMEOUT or use a smaller model" >&2
  exit 1
fi
[ "$rc" -eq 0 ] || { echo "claudish: curl failed (rc=$rc)" >&2; exit 1; }

err="$(printf '%s' "$resp" | jq -r '.error // empty' 2>/dev/null)"
if [ -n "$err" ]; then
  case "$err" in
    *not\ found*) echo "claudish: model '$MODEL' isn't available — \`ollama pull $MODEL\`" >&2 ;;
    *)            echo "claudish: ollama error: $err" >&2 ;;
  esac
  exit 1
fi

out="$(printf '%s' "$resp" | jq -j '.message.content // empty' 2>/dev/null)"
# Whitespace-stripped, matching the input check above. Command substitution already
# eats trailing newlines, so a newlines-only reply is caught by a bare -n; this also
# catches a spaces/tabs-only reply, which would otherwise exit 0 and emit nothing but
# the footer — on screen that is indistinguishable from a dropped rewrite.
[ -n "${out//[[:space:]]/}" ] || { echo "claudish: model returned an empty rewrite" >&2; exit 1; }

printf '%s\n' "$out"
printf '\n── %s · %ss\n' "$MODEL" "$elapsed" >&2
