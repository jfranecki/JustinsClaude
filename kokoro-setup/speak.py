#!/usr/bin/env python3
"""Kokoro TTS speak script for Claude Code integration.

Reads text from stdin or a file, generates speech audio, and plays it via afplay (macOS).
Streams audio chunk-by-chunk so playback starts quickly.

Usage:
    echo "Hello world" | python speak.py
    python speak.py --file /tmp/text.txt
    python speak.py --text "Hello world"
    python speak.py --voice af_heart --speed 1.2 --text "Fast speech"
"""

import argparse
import base64
import html as htmllib
import json
import os
import re
import subprocess
import sys
import tempfile
import wave

import numpy as np

os.environ.setdefault("PYTORCH_ENABLE_MPS_FALLBACK", "1")

# Suppress noisy warnings
import warnings
warnings.filterwarnings("ignore", category=UserWarning)

from loguru import logger
logger.remove()  # silence loguru

from kokoro import KPipeline


def strip_markdown(text: str) -> str:
    """Strip common markdown formatting so TTS reads clean prose."""
    # Remove code blocks entirely
    text = re.sub(r'```[\s\S]*?```', '', text)
    # Remove inline code
    text = re.sub(r'`[^`]+`', '', text)
    # Remove markdown links but keep text: [text](url) -> text
    text = re.sub(r'\[([^\]]+)\]\([^)]+\)', r'\1', text)
    # Remove images
    text = re.sub(r'!\[[^\]]*\]\([^)]+\)', '', text)
    # Remove headers markers
    text = re.sub(r'^#{1,6}\s+', '', text, flags=re.MULTILINE)
    # Remove bold/italic markers
    text = re.sub(r'\*{1,3}([^*]+)\*{1,3}', r'\1', text)
    text = re.sub(r'_{1,3}([^_]+)_{1,3}', r'\1', text)
    # Remove horizontal rules
    text = re.sub(r'^[-*_]{3,}\s*$', '', text, flags=re.MULTILINE)
    # Remove bullet points / list markers
    text = re.sub(r'^\s*[-*+]\s+', '', text, flags=re.MULTILINE)
    text = re.sub(r'^\s*\d+\.\s+', '', text, flags=re.MULTILINE)
    # Remove blockquote markers
    text = re.sub(r'^\s*>\s+', '', text, flags=re.MULTILINE)
    # Collapse multiple blank lines
    text = re.sub(r'\n{3,}', '\n\n', text)
    return text.strip()


def compute_word_timings(text: str, duration: float):
    """Return a list of {text, start} dicts distributing duration across words."""
    words = text.split()
    if not words or duration <= 0:
        return []

    weights = []
    for w in words:
        weight = 1.0
        if w.endswith(('.', '!', '?')):
            weight = 1.25
        elif w.endswith((':', ';')):
            weight = 1.12
        elif w.endswith(','):
            weight = 1.06
        if len(w) > 10:
            weight *= 1.08
        weights.append(weight)

    per_unit = duration / sum(weights)
    out = []
    t = 0.0
    for w, weight in zip(words, weights):
        out.append({"text": w, "start": round(t, 3)})
        t += weight * per_unit
    return out


def launch_browser_rsvp(text: str, wav_path: str):
    """Build a self-contained HTML page with embedded audio and RSVP playback, then open it."""
    with wave.open(wav_path, "rb") as w:
        duration = w.getnframes() / float(w.getframerate())

    with open(wav_path, "rb") as f:
        wav_b64 = base64.b64encode(f.read()).decode("ascii")

    timings = compute_word_timings(text, duration)
    words_json = json.dumps(timings)
    full_text_safe = htmllib.escape(text)

    html = RSVP_HTML_TEMPLATE.replace("__WORDS_JSON__", words_json) \
        .replace("__AUDIO_B64__", wav_b64) \
        .replace("__FULL_TEXT__", full_text_safe) \
        .replace("__DURATION__", f"{duration:.2f}")

    html_path = os.path.join(tempfile.gettempdir(), "claude_speak_rsvp.html")
    with open(html_path, "w", encoding="utf-8") as f:
        f.write(html)

    subprocess.run(["open", html_path], check=False)
    return html_path


RSVP_HTML_TEMPLATE = r"""<!doctype html>
<html lang="en">
<head>
<meta charset="utf-8">
<title>Speak — RSVP</title>
<style>
  :root {
    --bg: #0b0b0e;
    --fg: #e8e8ea;
    --muted: #5a5a66;
    --pivot: #ff6a5c;
    --accent: #4a9eff;
  }
  * { box-sizing: border-box; }
  html, body {
    margin: 0; padding: 0; height: 100%;
    background: var(--bg); color: var(--fg);
    font-family: ui-monospace, "SF Mono", Menlo, Consolas, monospace;
    overflow: hidden;
  }
  body {
    display: grid;
    grid-template-rows: 1fr auto auto;
    gap: 0;
  }
  .stage {
    display: flex; align-items: center; justify-content: center;
    position: relative;
    padding: 48px;
  }
  .guide {
    position: absolute;
    top: 50%; left: 50%;
    width: 2px; height: 120px;
    background: linear-gradient(to bottom, transparent, rgba(255,255,255,0.06) 20%, rgba(255,255,255,0.06) 80%, transparent);
    transform: translate(-50%, -50%);
    pointer-events: none;
  }
  .word {
    font-size: clamp(48px, 9vw, 120px);
    font-weight: 500;
    letter-spacing: -0.03em;
    white-space: nowrap;
    font-variant-ligatures: none;
    position: relative;
    display: inline-flex;
    min-height: 1.2em;
    align-items: center;
    will-change: transform, opacity;
  }
  @keyframes punch {
    0%   { opacity: 0.25; transform: translateY(-2px); }
    40%  { opacity: 1;    transform: translateY(0); }
    100% { opacity: 1;    transform: translateY(0); }
  }
  .word.flash { animation: punch 60ms steps(2, end); }
  .word .pivot { color: var(--pivot); }
  .word.idle { color: var(--muted); font-size: clamp(20px, 2vw, 28px); letter-spacing: 0.02em; }
  .transcript {
    padding: 24px 48px;
    color: var(--muted);
    font-size: 14px;
    line-height: 1.7;
    max-height: 22vh;
    overflow-y: auto;
    border-top: 1px solid rgba(255,255,255,0.05);
  }
  .transcript .active { color: var(--fg); background: rgba(74,158,255,0.12); border-radius: 3px; padding: 0 3px; }
  .transcript .past { color: #888; }
  .bar {
    height: 4px; background: rgba(255,255,255,0.06);
    position: relative;
  }
  .bar > div {
    position: absolute; left: 0; top: 0; bottom: 0;
    background: var(--accent);
    width: 0%;
  }
  .meta {
    position: fixed; top: 16px; right: 20px;
    color: var(--muted); font-size: 12px;
    display: flex; gap: 16px; align-items: center;
  }
  .meta kbd {
    border: 1px solid rgba(255,255,255,0.12);
    border-radius: 4px; padding: 1px 6px;
    font-size: 11px;
  }
  .start-overlay {
    position: fixed; inset: 0;
    display: none; align-items: center; justify-content: center;
    background: rgba(11,11,14,0.92);
    cursor: pointer; z-index: 10;
    font-size: 18px; color: var(--fg);
  }
  .start-overlay.show { display: flex; }
  .start-overlay .btn {
    border: 1px solid rgba(255,255,255,0.2);
    border-radius: 999px;
    padding: 16px 32px;
  }
</style>
</head>
<body>
  <div class="stage">
    <div class="guide"></div>
    <div class="word idle" id="word">ready</div>
  </div>
  <div class="transcript" id="transcript"></div>
  <div class="bar"><div id="bar"></div></div>
  <div class="meta">
    <span id="clock">0.0 / __DURATION__s</span>
    <span><kbd>Space</kbd> play/pause</span>
    <span><kbd>R</kbd> restart</span>
  </div>
  <div class="start-overlay" id="overlay"><div class="btn">▶ Click to start</div></div>
  <audio id="audio" preload="auto"></audio>
<script>
const WORDS = __WORDS_JSON__;
const FULL_TEXT = "__FULL_TEXT__";
const AUDIO_B64 = "__AUDIO_B64__";

const audio = document.getElementById('audio');
audio.src = "data:audio/wav;base64," + AUDIO_B64;

const wordEl = document.getElementById('word');
const barEl = document.getElementById('bar');
const clockEl = document.getElementById('clock');
const transcriptEl = document.getElementById('transcript');
const overlay = document.getElementById('overlay');

function pivotIndex(word) {
  const stripped = word.replace(/[^\p{L}\p{N}]/gu, '');
  const len = stripped.length || word.length;
  if (len <= 1) return 0;
  if (len <= 5) return 1;
  if (len <= 9) return 2;
  if (len <= 13) return 3;
  return 4;
}

function renderWord(w) {
  wordEl.classList.remove('idle');
  if (!w) { wordEl.innerHTML = '&nbsp;'; return; }
  const i = Math.min(pivotIndex(w), w.length - 1);
  const before = w.slice(0, i);
  const mid = w.slice(i, i + 1);
  const after = w.slice(i + 1);
  wordEl.innerHTML =
    escapeHtml(before) +
    '<span class="pivot">' + escapeHtml(mid) + '</span>' +
    escapeHtml(after);
  wordEl.classList.remove('flash');
  void wordEl.offsetWidth;
  wordEl.classList.add('flash');
}

function escapeHtml(s) {
  return s.replace(/[&<>"']/g, c => ({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;',"'":'&#39;'}[c]));
}

for (let i = 0; i < WORDS.length; i++) {
  const span = document.createElement('span');
  span.textContent = WORDS[i].text + ' ';
  span.dataset.idx = i;
  transcriptEl.appendChild(span);
}
const transcriptSpans = transcriptEl.querySelectorAll('span');

const LEAD = 0.15; // seconds — show word slightly before audio says it
let currentIdx = -1;
function tick() {
  const t = audio.currentTime + LEAD;
  let idx = -1;
  for (let i = 0; i < WORDS.length; i++) {
    if (WORDS[i].start <= t) idx = i;
    else break;
  }
  if (idx !== currentIdx) {
    currentIdx = idx;
    renderWord(idx >= 0 ? WORDS[idx].text : '');
    transcriptSpans.forEach((s, i) => {
      s.className = i < idx ? 'past' : (i === idx ? 'active' : '');
    });
    const active = transcriptEl.querySelector('.active');
    if (active) active.scrollIntoView({block: 'nearest'});
  }
  const dur = audio.duration || 0;
  if (dur > 0) {
    barEl.style.width = (100 * audio.currentTime / dur) + '%';
    clockEl.textContent = audio.currentTime.toFixed(1) + ' / ' + dur.toFixed(1) + 's';
  }
  requestAnimationFrame(tick);
}

function tryPlay() {
  const p = audio.play();
  if (p && p.catch) {
    p.then(() => { overlay.classList.remove('show'); })
     .catch(() => { overlay.classList.add('show'); });
  }
}

overlay.addEventListener('click', () => { overlay.classList.remove('show'); tryPlay(); });

audio.addEventListener('ended', () => {
  wordEl.classList.add('idle');
  wordEl.textContent = 'done';
});

document.addEventListener('keydown', (e) => {
  if (e.code === 'Space') {
    e.preventDefault();
    if (audio.paused) tryPlay(); else audio.pause();
  } else if (e.key === 'r' || e.key === 'R') {
    audio.currentTime = 0;
    tryPlay();
  }
});

audio.addEventListener('loadedmetadata', () => {
  tryPlay();
  requestAnimationFrame(tick);
});
</script>
</body>
</html>
"""


def speak(text: str, voice: str = "af_heart", speed: float = 1.0, rsvp: bool = False):
    """Generate TTS audio and play it chunk-by-chunk."""
    text = strip_markdown(text)
    if not text:
        print("Nothing to speak.", file=sys.stderr)
        return

    pipeline = KPipeline(lang_code=voice[0], repo_id="hexgrad/Kokoro-82M")

    # Generate all chunks into a single wav, then play
    tmp = tempfile.NamedTemporaryFile(suffix=".wav", delete=False)
    tmp_path = tmp.name
    tmp.close()

    try:
        with wave.open(tmp_path, "wb") as wav_file:
            wav_file.setnchannels(1)
            wav_file.setsampwidth(2)
            wav_file.setframerate(24000)

            chunk_count = 0
            for result in pipeline(text, voice=voice, speed=speed, split_pattern=r'\n+'):
                if result.audio is None:
                    continue
                audio_bytes = (result.audio.numpy() * 32767).astype(np.int16).tobytes()
                wav_file.writeframes(audio_bytes)
                chunk_count += 1

        if chunk_count == 0:
            print("No audio generated.", file=sys.stderr)
            return

        if rsvp:
            html_path = launch_browser_rsvp(text, tmp_path)
            print(f"Opened RSVP page: {html_path}", file=sys.stderr)
            return
        subprocess.run(["afplay", tmp_path], check=True)
    finally:
        try:
            os.unlink(tmp_path)
        except OSError:
            pass


def main():
    parser = argparse.ArgumentParser(description="Speak text aloud using Kokoro TTS")
    parser.add_argument("--text", "-t", help="Text to speak")
    parser.add_argument("--file", "-f", help="File containing text to speak")
    parser.add_argument("--voice", "-v", default="af_heart", help="Voice name (default: af_heart)")
    parser.add_argument("--speed", "-s", type=float, default=None, help="Speech speed (default: 1.0 for audio-only, 1.85 with --rsvp to hit ~300 WPM)")
    parser.add_argument("--rsvp", action="store_true", help="Open an HTML page in the default browser with embedded audio and a Rapid Serial Visual Presentation reader")
    args = parser.parse_args()

    if args.text:
        text = args.text
    elif args.file:
        with open(args.file) as f:
            text = f.read()
    elif not sys.stdin.isatty():
        text = sys.stdin.read()
    else:
        print("No text provided. Use --text, --file, or pipe to stdin.", file=sys.stderr)
        sys.exit(1)

    speed = args.speed if args.speed is not None else (1.85 if args.rsvp else 1.0)
    speak(text, voice=args.voice, speed=speed, rsvp=args.rsvp)


if __name__ == "__main__":
    main()
