# ollama setup — runbook for the `/claudish` command

This document is written to be **executed by an AI coding agent** (Claude Code, etc.). Open your agent in a terminal and say:

> Read ollama-setup/OLLAMA_SETUP.md from this repo and perform the setup it describes.

It also works fine as a manual checklist.

## What you are setting up

The `/claudish` command rewrites Claude's last response into plain English using a model that runs **locally and free** via [ollama](https://ollama.com) — no API key, nothing billed, and the text never leaves your machine. The pieces:

1. `ollama` itself, running as a background service that serves an HTTP API on `localhost:11434`.
2. One pulled model to do the rewriting — **which one depends on your hardware**, see below.
3. `claudish.sh` — a wrapper script **shipped in this repo** (`ollama-setup/claudish.sh`; it is NOT part of ollama) that sends the text with a plain-English system prompt, enforces a timeout, and prints the rewrite followed by a `── model · Ns` timing footer.

**Platform note:** the script itself is portable (`bash`, `curl`, `jq`). The install commands below use Homebrew, so they are macOS-first; on Linux use the official installer (`curl -fsSL https://ollama.com/install.sh | sh`) and `systemctl --user` in place of `brew services`.

## Prerequisites (verify before starting)

- `bash`, `curl`, and `jq` (`brew install jq`).
- Disk space for the model you choose — from ~3 GB to ~20 GB.
- Enough **usable** memory to hold that model while it runs. Measure it first; don't guess.

## Step 1 — Measure the hardware, then pick the model

This is the step that matters most, and the one most people skip. The binding constraint differs by machine:

- **NVIDIA GPU** (e.g. an RTX 4090) → **VRAM**. ollama offloads the model to the GPU; if it doesn't fit in VRAM it silently spills to CPU and gets dramatically slower.
- **Apple Silicon** → **unified memory**, shared with the OS and every running app. A 16 GB Mac with a browser open has far less than 16 GB available.
- **Neither** → system RAM, on the CPU, slowly.

Run this to find out what you're working with:

```bash
if command -v nvidia-smi >/dev/null 2>&1; then
  echo "NVIDIA GPU — VRAM is the binding constraint:"
  nvidia-smi --query-gpu=name,memory.total,memory.free --format=csv,noheader
elif [ "$(uname -s)" = "Darwin" ]; then
  echo "Apple Silicon / macOS — unified memory is the binding constraint:"
  echo "  total: $(( $(sysctl -n hw.memsize) / 1073741824 )) GB"
  system_profiler SPHardwareDataType 2>/dev/null | grep -i "Chip:"
else
  echo "CPU — system RAM is the binding constraint:"
  free -g | awk '/^Mem:/{print "  total: "$2" GB, available: "$7" GB"}'
fi
```

Then size the model against it, leaving **~25–30% headroom** for the KV cache and context window:

| Usable memory | Model size to aim for | Observed examples |
|---|---|---|
| 8 GB | ≤ 4 GB | `gemma3:4b` (3.3 GB) |
| 16 GB | ≤ 6 GB | `gemma3:4b`, `gemma4:e4b-it-qat` (6.1 GB) |
| **24 GB** (RTX 4090, RTX 3090) | ≤ 18 GB | a 26B-class `gemma4` quant (~18 GB) |
| 32 GB+ | ≤ 24 GB | larger `gemma4` / 27B+ quants |

Two traps worth knowing:

- **`-mlx` tags are Apple-Silicon only.** MLX is Apple's framework, so a tag like `gemma4:26b-mlx` will not serve a 4090 — pick the default/GGUF tag for that size instead. Confirm the exact tags for a family at `ollama.com/library/<model>` or just try `ollama pull <tag>`.
- **Bigger is not automatically better here.** The job is *simplification*, which small instruction-tuned models do well. A 4 GB model that answers in 8 seconds is often a better experience than an 18 GB model that takes 40 — and the quality gap on "rewrite this plainly" is much smaller than on reasoning tasks. Start one tier below your ceiling and move up only if the output disappoints.

Measured on an Apple M1 Pro / 16 GB, for calibration:

| Model | Size | Cold run | Warm run |
|---|---|---|---|
| `gemma3:4b` | 3.3 GB | ~20s | ~8s |
| `gemma4:e4b-it-qat` | 6.1 GB | ~39s | ~9s |

A 24 GB GPU changes this picture substantially — expect far faster warm runs and room for a much larger model.

## Step 2 — Install

Pick a location for the wrapper script; `~/ToolboxRepos/claudish` is the convention assumed below — adjust freely, but remember the final path: `/get-started` will ask for it as `CLAUDISH_SCRIPT`.

```bash
# 1. Install ollama
brew install ollama

# 2. Run it as a background service (survives reboot)
brew services start ollama

# 3. Pull the model you chose in Step 1 (gemma3:4b is the script's default)
ollama pull gemma3:4b

# 4. Install the wrapper script from THIS repo
mkdir -p ~/ToolboxRepos/claudish
cp <path-to-this-commands-repo>/ollama-setup/claudish.sh ~/ToolboxRepos/claudish/claudish.sh
chmod +x ~/ToolboxRepos/claudish/claudish.sh
```

If you chose a model other than `gemma3:4b`, set `CLAUDISH_MODEL` — either in your shell profile, or in the `env` block of `~/.claude/settings.json` so Claude Code sessions inherit it:

```json
{ "env": { "CLAUDISH_MODEL": "gemma4:e4b-it-qat" } }
```

Note that `env` in `settings.json` does **not** merge across settings scopes — the highest-precedence file defining `env` supplies the whole block — and changes need a Claude Code restart.

## Verify

```bash
printf 'The deployment gate is blocked because the service account lacks browse permission on the project.\n' > /tmp/claudish-test.md
bash ~/ToolboxRepos/claudish/claudish.sh /tmp/claudish-test.md
```

Expect a plainer sentence on stdout, then a footer like `── gemma3:4b · 8s`.

**If you have a GPU, confirm it is actually being used** — this is the single most valuable check, because a model that quietly fell back to CPU still works, just far slower:

```bash
ollama ps    # while a run is in flight, or with CLAUDISH_KEEP_ALIVE set
```

The `PROCESSOR` column should name your GPU (e.g. `100% GPU`), not `CPU`. If it says CPU, the model didn't fit in VRAM — drop to a smaller one.

## Knobs

All are environment variables read by `claudish.sh`:

| Variable | Default | What it does |
|---|---|---|
| `CLAUDISH_MODEL` | `gemma3:4b` | Which ollama model to use. |
| `CLAUDISH_OLLAMA` | `http://localhost:11434` | Base URL of the ollama API. |
| `CLAUDISH_CMD_TIMEOUT` | `300` | Seconds before the script gives up on a rewrite. |
| `CLAUDISH_KEEP_ALIVE` | `0` | Unload the model as soon as the response is done. Any Go duration (`5m`) keeps it resident instead. |

`CLAUDISH_KEEP_ALIVE=0` is the right default on a memory-constrained laptop — it frees several GB the moment the rewrite is done, at the cost of paying the model load on every run. **On a 24 GB GPU, set it to `5m`**: you have the headroom, and keeping the model resident removes the cold-load cost entirely, which is most of the wait.

## Troubleshooting

- `claudish: can't reach ollama at ...` — the service isn't running. `brew services start ollama`, or `ollama serve` in a spare terminal.
- `claudish: model 'X' isn't available` — `ollama pull X`. Check the tag spelling; `-mlx` variants won't load on non-Apple hardware.
- `claudish: timed out after 300s` — the model is too large or too slow for this machine. Drop a size tier, or raise `CLAUDISH_CMD_TIMEOUT`.
- `claudish: model returned an empty rewrite` — the model replied with nothing usable; usually a bad or truncated pull. Re-pull it, or try another model.
- **Every run is slow, even repeats** — `CLAUDISH_KEEP_ALIVE=0` unloads after each call, so each run pays the load cost. Set `CLAUDISH_KEEP_ALIVE=5m`.
- **Slower than expected on a good GPU** — check `ollama ps`; if `PROCESSOR` says CPU, the model overflowed VRAM.
- **The command prints only `── model · Ns` and no rewrite** — the script worked and the agent dropped its output. The rewrite reaches you only when the agent re-prints it in its own message, because tool output is collapsed in the UI. The command file warns against this explicitly; if you see it, say "print the rewrite."

## Optional: the automatic companion

[`claudish-to-english`](https://github.com/gvzdv/claudish-to-english) is a third-party Claude Code plugin that does this *automatically* on every assistant message, using the same local ollama setup. `/claudish` is the on-demand version — useful precisely because you usually don't want every message rewritten. They coexist; if you run the plugin in `append` mode, the `/claudish` command knows to strip its appended block before sending text to the model.

## Done?

Re-run `/get-started` in the commands repo and give it your `claudish.sh` path when it asks — it will validate the script, check the ollama daemon responds, and install the `/claudish` command.
