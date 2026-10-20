# Setting up the status line

A four-row Claude Code status line, drawn by **`statusline.py`**, the small stdlib-only
Python script in this directory. This document is written so an AI agent can perform the
install for you. Open Claude Code (or any coding agent) in this repo and say:

> Read statusline-setup/STATUSLINE_SETUP.md and perform the setup it describes.

## What it shows

```
[CTX 42%] [COMPACT 1] [5H 18% 3:37p] [7D 61% Mon 12:57a]
[IN 12.0k +5] [OUT 3,400 +120] [CACHE +800 / 64.0k]
Opus · HIGH · 12m · $0.42
~/Documents/ClaudeCode/JustinsClaude · main
```

1. **Limits:** context window used and how many times this session has been compacted
   (yellow once it's above zero), then the 5-hour and 7-day rate limits with their reset
   times. Each percentage is green under 50, yellow under 80, red above.
2. **Tokens:** session input and output totals, with the last turn's change in gray, then
   cache writes (yellow) and cache reads (green) for the last turn.
3. **Config:** model, effort level (blue low → yellow medium → orange high → red-orange
   xhigh → red max), session duration, and session cost in USD.
4. **Where:** the working directory, with your home folder shortened to `~`, and the git branch.

## What it needs

Python 3. Nothing else: no pip install, no virtualenv, no network. The script imports only
`json`, `os`, `sys`, `time`, and `datetime`, and runs the same on Windows, macOS, and Linux.

## Installing

### 1. Copy the script into `~/.claude/`

```bash
cp statusline-setup/statusline.py ~/.claude/statusline.py
```

Copy it rather than pointing at the clone, so moving or re-cloning the repo doesn't break
the status line. To update later, copy it again.

### 2. Find the Python to run it with

The command in `settings.json` is run by Claude Code directly, so use an interpreter path
that is sure to work there:

- **macOS / Linux:** `python3` is fine. Confirm with `command -v python3`.
- **Windows:** use the **absolute path** to a real Python 3 install. `python` and
  `python3` on a Windows PATH are often the Microsoft Store stub, which opens the Store
  instead of running anything. Find the real one with `py -3 -c "import sys; print(sys.executable)"`,
  or look under `%LOCALAPPDATA%\Programs\Python\`. Confirm it isn't under `WindowsApps`.

### 3. Add the `statusLine` block to `~/.claude/settings.json`

**Merge** this key into the existing file. Don't replace the file, and keep every other key
as it is. If a `statusLine` key already exists, show the user the old value before you
replace it.

macOS / Linux:

```json
"statusLine": {
  "type": "command",
  "command": "python3 ~/.claude/statusline.py"
}
```

Windows, with both paths absolute and each wrapped in escaped quotes (the example is the
laptop this was built on; substitute the paths from step 2 and the user's home folder):

```json
"statusLine": {
  "type": "command",
  "command": "\"C:\\Users\\jfran\\AppData\\Local\\Programs\\Python\\Python310\\python.exe\" \"C:\\Users\\jfran\\.claude\\statusline.py\""
}
```

### 4. Effort level (usually nothing to do)

Claude Code sends the live effort level as `effort.level`, including mid-session `/effort`
changes, and the script shows that. When the payload has no `effort.level` (an older
Claude Code, or a model without the effort parameter), the script falls back to
`effortLevel` from settings, first match wins:

1. `<project>/.claude/settings.local.json`
2. `<project>/.claude/settings.json`
3. `~/.claude/settings.json`

If none of them sets it either, row 3 shows `?`. To set a fallback, add
`"effortLevel": "high"` (or `low`, `medium`, `xhigh`, `max`) to `~/.claude/settings.json`.

### 5. Verify

Pipe in a sample payload with the same Python from step 2 and check that four rows print
with no traceback:

```bash
echo '{"model":{"display_name":"Opus"},"workspace":{"current_dir":"."},"context_window":{"used_percentage":42,"total_input_tokens":12000,"total_output_tokens":3400,"current_usage":{"input_tokens":5,"output_tokens":120,"cache_creation_input_tokens":800,"cache_read_input_tokens":64000}},"rate_limits":{"five_hour":{"used_percentage":18},"seven_day":{"used_percentage":61}},"cost":{"total_cost_usd":0.42,"total_duration_ms":754000}}' \
  | python3 ~/.claude/statusline.py
```

On Windows, replace `python3` with the absolute path from step 2. `[COMPACT ?]` is expected
here: Claude Code doesn't send a compaction count, so the script counts the
`compact_boundary` records in the session transcript at `transcript_path`, and the sample
doesn't include one. Then tell the user the
status line appears on their next prompt, or after starting a new Claude Code session.

## Troubleshooting

- **Nothing appears.** Run the command from `settings.json` by hand with the sample payload
  above. A Store-stub `python` on Windows is the usual cause.
- **Gauges show `?`.** That field wasn't in the payload Claude Code sent. Some fields, such
  as the rate limits, may not be there yet early in a session, or on every plan.
- **Escape codes like `[32m` print literally.** The terminal doesn't render ANSI colors.
  Use Windows Terminal rather than the legacy console.
