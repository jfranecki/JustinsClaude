---
description: Read the most recent response aloud using Kokoro TTS (pass --rsvp to also open a Rapid Serial Visual Presentation reader in the browser)
argument-hint: [voice] [--rsvp]
allowed-tools: Write, Bash
---

Recall your most recent response text from this conversation (the message immediately before the user invoked /speak).

Strip all code blocks, file paths, tool output, and markdown formatting from that text — keep only the natural language prose.

If the previous response was very long (more than ~2000 characters of prose), summarize it into a concise spoken version instead of reading verbatim.

Write the cleaned text to /tmp/claude_speak_input.txt using the Write tool.

Parse "$ARGUMENTS":
- If it contains the literal token `--rsvp` (in any position), set RSVP=true and remove that token from the argument string.
- The remaining non-empty token (if any) is the voice name. If empty, default voice = "bm_george,af_heart".

When RSVP is false, run this Bash command (substituting VOICE_NAME) and wait for it to finish:

```
{{KOKORO_DIR}}/.venv/bin/python {{KOKORO_DIR}}/speak.py --file /tmp/claude_speak_input.txt --voice VOICE_NAME
```

When RSVP is true, run this Bash command instead (it generates faster audio at ~300 WPM, embeds it into a self-contained HTML page at /tmp/claude_speak_rsvp.html, and opens that page in the default browser — the command returns immediately, do not wait for playback to finish):

```
{{KOKORO_DIR}}/.venv/bin/python {{KOKORO_DIR}}/speak.py --file /tmp/claude_speak_input.txt --voice VOICE_NAME --rsvp
```

After the command returns, confirm briefly that the response was spoken, which voice was used, and whether RSVP was enabled. Do NOT re-display the text.
