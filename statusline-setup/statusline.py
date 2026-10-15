#!/usr/bin/env python3
"""Claude Code status line"""

import json
import sys
import os
import time
from datetime import datetime

# ── ANSI colors ───────────────────────────────────────────────────────────────
RESET = "\033[0m"
BOLD = "\033[1m"
DIM = "\033[2m"
GREEN = "\033[32m"
YELLOW = "\033[33m"
RED = "\033[91m"
BLUE = "\033[94m"
CYAN = "\033[36m"
PINK = "\033[95m"
ORANGE = "\033[38;5;208m"
LABEL = "\033[38;5;244m"  # muted gray for row labels
DELTA = "\033[38;5;244m"  # muted gray for (+N) deltas


def fmt_pct(pct):
    if pct is None:
        return "  ?"
    return f"{int(round(float(pct))):3d}%"


def fmt_tokens(n):
    try:
        return f"{int(n):,}"
    except Exception:
        return str(n)


def fmt_k(n):
    """Short format: commas for <10k, 12.3k / 1.2m above."""
    try:
        n = int(n)
    except Exception:
        return str(n)
    if n >= 1_000_000:
        return f"{n/1_000_000:.1f}m"
    if n >= 10_000:
        return f"{n/1_000:.1f}k"
    return f"{n:,}"


def pct_color(pct):
    """Gradient: green <50, yellow 50-80, red >80."""
    if pct is None:
        return LABEL
    try:
        p = float(pct)
    except Exception:
        return LABEL
    if p < 50:
        return GREEN
    if p < 80:
        return YELLOW
    return RED


def fmt_reset(epoch):
    """Compact '4:32p' for <12h, 'Fri 4:32p' for longer."""
    if not epoch:
        return ""
    try:
        dt = datetime.fromtimestamp(int(epoch))
    except Exception:
        return ""
    delta_s = int(epoch) - int(time.time())
    # Portable 12-hour clock (strftime "%-I" is glibc-only, "%#I" is Windows-only).
    h = f"{dt.hour % 12 or 12}:{dt.minute:02d}"
    suffix = "a" if dt.hour < 12 else "p"
    if 0 <= delta_s < 12 * 3600:
        return f"{h}{suffix}"
    return f"{dt.strftime('%a')} {h}{suffix}"


def fmt_duration(ms):
    """Compact session duration: 45s / 12m / 1h23m."""
    try:
        s = int(ms) // 1000
    except Exception:
        return ""
    if s <= 0:
        return ""
    if s < 60:
        return f"{s}s"
    m, s = divmod(s, 60)
    if m < 60:
        return f"{m}m"
    h, m = divmod(m, 60)
    return f"{h}h{m:02d}m"


def effort_color(level):
    return {
        "LOW": BLUE,
        "MEDIUM": YELLOW,
        "HIGH": ORANGE,
        "MAX": RED,
    }.get((level or "").upper(), LABEL)


def shorten_home(path):
    home = os.path.expanduser("~")
    if path.startswith(home):
        return "~" + path[len(home):]
    return path


def git_branch(cwd):
    d = os.path.abspath(cwd)
    while True:
        head = os.path.join(d, ".git", "HEAD")
        if os.path.isfile(head):
            try:
                with open(head) as f:
                    line = f.read().strip()
                if line.startswith("ref: refs/heads/"):
                    return line[len("ref: refs/heads/"):]
                return line[:7]
            except Exception:
                return None
        parent = os.path.dirname(d)
        if parent == d:
            return None
        d = parent


def read_effort_level(cwd):
    """Cascade: project local > project > user settings.json."""
    candidates = [
        os.path.join(cwd, ".claude", "settings.local.json"),
        os.path.join(cwd, ".claude", "settings.json"),
        os.path.expanduser("~/.claude/settings.json"),
    ]
    for path in candidates:
        try:
            with open(path, encoding="utf-8") as f:
                v = json.load(f).get("effortLevel")
            if v:
                return v
        except Exception:
            continue
    return None


def main():
    try:
        sys.stdout.reconfigure(encoding="utf-8")
    except Exception:
        pass

    try:
        data = json.load(sys.stdin)
    except Exception:
        data = {}

    SEP = DIM + " · " + RESET

    # ── Data extraction ───────────────────────────────────────────────────────
    ctx = data.get("context_window") or {}
    used_pct = ctx.get("used_percentage")
    total_in = ctx.get("total_input_tokens") or 0
    total_out = ctx.get("total_output_tokens") or 0
    cu = ctx.get("current_usage") or {}
    cu_in = cu.get("input_tokens") or 0
    cu_out = cu.get("output_tokens") or 0
    cu_cc = cu.get("cache_creation_input_tokens") or 0
    cu_cr = cu.get("cache_read_input_tokens") or 0

    rate = data.get("rate_limits") or {}
    five_pct = (rate.get("five_hour") or {}).get("used_percentage")
    seven_pct = (rate.get("seven_day") or {}).get("used_percentage")
    five_reset = (rate.get("five_hour") or {}).get("resets_at")
    seven_reset = (rate.get("seven_day") or {}).get("resets_at")

    duration_ms = (data.get("cost") or {}).get("total_duration_ms")

    cwd_raw = (data.get("workspace") or {}).get("current_dir") or data.get("cwd") or os.getcwd()
    model = (data.get("model") or {}).get("display_name") or (data.get("model") or {}).get("id") or "?"
    effort = (read_effort_level(cwd_raw) or "?").upper()
    cwd = shorten_home(cwd_raw)
    branch = git_branch(cwd_raw)

    # ── Row 1: LIMITS ─────────────────────────────────────────────────────────
    def fmt_pct_tight(pct):
        if pct is None:
            return "?"
        return f"{int(round(float(pct)))}%"

    def _bracket(inner):
        return DIM + "[" + RESET + inner + DIM + "]" + RESET

    def gauge(label, pct, reset_epoch=None):
        col = pct_color(pct)
        inner = LABEL + label + " " + RESET + BOLD + col + fmt_pct_tight(pct) + RESET
        r = fmt_reset(reset_epoch)
        if r:
            inner += " " + LABEL + r + RESET
        return _bracket(inner)

    row1 = gauge("CTX", used_pct) + " " + gauge("5H", five_pct, five_reset) + " " + gauge("7D", seven_pct, seven_reset)

    # ── Row 2: TOKENS — [IN 949 (+1)] [OUT 13,133 (+36)] [CACHE +277 / 64.6k]
    def delta(n):
        return "" if not n else " " + DELTA + f"+{fmt_tokens(n)}" + RESET

    def bracket(inner):
        return DIM + "[" + RESET + inner + DIM + "]" + RESET

    in_part = LABEL + "IN " + RESET + BOLD + fmt_k(total_in) + RESET + delta(cu_in)
    out_part = LABEL + "OUT " + RESET + BOLD + RED + fmt_k(total_out) + RESET + delta(cu_out)
    cache_write = YELLOW + "+" + fmt_k(cu_cc) + RESET + DIM + " / " + RESET if cu_cc else ""
    cache_part = (
        LABEL + "CACHE " + RESET
        + cache_write
        + GREEN + fmt_k(cu_cr) + RESET
    )

    row2 = bracket(in_part) + " " + bracket(out_part) + " " + bracket(cache_part)

    # ── Row 3: CONFIG — model · effort · duration ─────────────────────────────
    row3 = (
        CYAN + model + RESET + SEP
        + BOLD + effort_color(effort) + effort + RESET
    )
    dur = fmt_duration(duration_ms)
    if dur:
        row3 += SEP + LABEL + dur + RESET

    # ── Row 4: WHERE — cwd · branch ───────────────────────────────────────────
    parts = [PINK + cwd + RESET]
    if branch:
        parts.append(GREEN + branch + RESET)
    row4 = (SEP).join(parts)

    print(row1)
    print(row2)
    print(row3)
    print(row4)


if __name__ == "__main__":
    main()
