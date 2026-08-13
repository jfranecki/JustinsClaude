---
description: Rewrite the most recent response in plain English using a local ollama model (free, private, no API tokens)
argument-hint: [text to simplify]
allowed-tools: Write, Bash
---

The rewrite is produced by a **local ollama model**, not by you. Your job is only to hand
it the text and show what comes back.

Determine the source text:
- If "$ARGUMENTS" is non-empty, that is the source text.
- If "$ARGUMENTS" is empty, use your most recent response in this conversation (the
  message immediately before the user invoked /claudish).

**If the optional [claudish-to-english](https://github.com/gvzdv/claudish-to-english)
plugin is also installed**, it appends a rewrite to every assistant message: a separator
line (`────────`) followed by `💬 In plain English:` and a local-model rewrite. When you
take your most recent response as the source, cut that entire trailing block off and send
**only your original text**. Feeding the model its own previous output produces degraded
nonsense and silently invalidates the result.

Steps:

1. Write the source text **verbatim** to a file in your scratchpad directory (e.g.
   `claudish-src.md`). Do not summarize, trim, reformat, or "clean it up" first — the
   local model does the rewriting, and pre-editing it corrupts the comparison.

2. Run: `bash {{CLAUDISH_SCRIPT}} <that file>`

   **Set the Bash tool's `timeout` parameter to `600000` on this call.** The script's own
   budget is 300s (`CLAUDISH_CMD_TIMEOUT`), but the Bash tool defaults to **120s** — so on
   any slower run the harness kills the call before the script can report its own timeout,
   and the rewrite is lost with no diagnostic at all. A large model, a long message, or a
   cold model load exceeds 120s easily.

3. **Reproduce the script's entire output in your own message text, verbatim.** That is
   the one deliverable of this command. Do not re-edit, re-order, trim, summarize, or
   improve it.

   **The user cannot see the script's output.** Claude Code collapses tool calls in
   their UI to a one-line summary (`ran 1 shell command`), so stdout is shown to *you*
   and to no one else. Re-printing it is not redundant — it is the only channel the
   rewrite has. If your message does not contain the full rewrite, this command has
   failed, however complete the tool result looked to you.

   About the trailing footer: stdout and stderr come back **merged into one blob**, so
   the last line you see is the script's `── model · Ns` timing note, not part of the
   rewrite. Keep it as your final line. It is a subordinate detail — **never emit the
   footer on its own.** A message containing only `── model · Ns` is the exact failure
   this instruction exists to prevent.

Before you end the turn, confirm your message is about as long as the script's output.
If it is dramatically shorter, you dropped the rewrite — print it.

Failure handling (important):
- If the script exits non-zero it prints a single `claudish: ...` line in place of a
  rewrite. Show that line and **stop**.
- Do **not** fall back to rewriting the text yourself. The entire point of this command
  is to use the local model; substituting yourself silently would hide that ollama is
  down or the model is too slow, and would burn API tokens the user was avoiding.
- If the user would rather have a Claude-authored rewrite, offer one — but only when they
  ask for it.

No preamble, no commentary beyond the rewrite and the timing note.
