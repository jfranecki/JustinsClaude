# Kokoro TTS setup — runbook for the `/speak` command

This document is written to be **executed by an AI coding agent** (Claude Code, etc.). Open your agent in a terminal and say:

> Read kokoro-setup/KOKORO_SETUP.md from this repo and perform the setup it describes.

It also works fine as a manual checklist.

## What you are setting up

The `/speak` command turns Claude's last response into speech using [Kokoro](https://github.com/hexgrad/kokoro), an open-weight ~82M-parameter TTS model that runs **locally and free** (no API key, no network after the first model download). The pieces:

1. A clone of the upstream `hexgrad/kokoro` repository.
2. A Python virtual environment inside it with the `kokoro` package installed.
3. `speak.py` — a wrapper script **shipped in this repo** (`kokoro-setup/speak.py`, it is NOT part of upstream Kokoro) that strips markdown, synthesizes audio, and either plays it or opens an RSVP speed-reading page in the browser.

**Platform note:** playback uses `afplay` and `open`, so the script is **macOS-only** as shipped. On Linux, edit the two `subprocess.run` calls in `speak.py` (`afplay` → `aplay`/`ffplay -nodisp -autoexit`, `open` → `xdg-open`).

## Prerequisites (verify before starting)

- Python **3.10–3.12** available as `python3` (check: `python3 --version`).
- `git`.
- ~3 GB free disk (PyTorch is the bulk of it; the voice model itself is ~330 MB, downloaded from Hugging Face on first run).

## Steps

Pick an install location; `~/ToolboxRepos/kokoro` is the convention assumed below — adjust freely, but remember the final path: the `/get-started` command will ask for it as `KOKORO_DIR`.

```bash
# 1. Clone upstream Kokoro
mkdir -p ~/ToolboxRepos
git clone https://github.com/hexgrad/kokoro.git ~/ToolboxRepos/kokoro
cd ~/ToolboxRepos/kokoro

# 2. Create the virtual environment the /speak command expects at .venv/
python3 -m venv .venv

# 3. Install the kokoro package (pulls torch, spacy, espeakng-loader, etc. — several minutes)
.venv/bin/pip install --upgrade pip
.venv/bin/pip install kokoro numpy loguru

# 4. Copy the wrapper script from THIS commands repo into the kokoro clone root
cp <path-to-this-commands-repo>/kokoro-setup/speak.py ~/ToolboxRepos/kokoro/speak.py
```

## Verify

```bash
cd ~/ToolboxRepos/kokoro
.venv/bin/python speak.py --text "Kokoro is working." --voice af_heart
```

- **First run** downloads the `hexgrad/Kokoro-82M` model from Hugging Face (~330 MB) — expect a delay, then audio from the speakers.
- Also test the RSVP mode (opens a dark speed-reading page in the browser with synced audio):

```bash
.venv/bin/python speak.py --text "This is the RSVP reader. Words flash in time with the audio." --rsvp
```

## Troubleshooting

- `ModuleNotFoundError: kokoro` — you installed into the wrong interpreter; always use `.venv/bin/pip` / `.venv/bin/python`, not system pip.
- Slow/garbled on Apple Silicon — the script already sets `PYTORCH_ENABLE_MPS_FALLBACK=1`; first synthesis is slower while the model warms up.
- No sound but no error — check the Mac's output device; `afplay /System/Library/Sounds/Ping.aiff` should ping.
- Voices: pass any Kokoro voice name with `--voice` (e.g. `af_heart`, `bm_george`, `af_bella`). The `/speak` command's default is `bm_george,af_heart` (a blend).

## Done?

Re-run `/get-started` in the commands repo and give it your Kokoro path when it asks — it will validate `.venv/bin/python` and `speak.py` and install the `/speak` command.
