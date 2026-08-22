#!/usr/bin/env python3
"""Search this project's past Claude Code conversations. Stdlib only.

Why this exists: a discovery pass reads the filesystem, never your past
conversations — but those transcripts are sitting on disk, and on a long-running
project they hold decisions that never made it into a document.

Why it defaults to YOUR messages only: assistant turns are full of mid-reasoning,
wrong turns, and claims that were later retracted. Searching them surfaces
confident-sounding text with no signal that it was withdrawn. Your own messages
are decisions. Use --all only when you specifically want to see how something was
worked out, and treat what you find as a lead, not a fact.

  python history.py index
  python history.py search "currency system" [-n 20] [--all] [--context 200]
  python history.py recent [-n 5]
"""
from __future__ import annotations

import argparse
import json
import os
import re
import sys
from pathlib import Path

PROJECTS = Path.home() / ".claude" / "projects"

# transcript noise that is not the user talking
_SKIP = re.compile(
    r"^\s*<(?:local-command-caveat|local-command-stdout|command-name|command-message"
    r"|command-args|system-reminder|user-prompt-submit-hook|task-notification)",
    re.I,
)


def project_dir(cwd: Path | None = None) -> Path | None:
    """Claude Code encodes the project path into a folder name (: \\ / -> -).

    A worktree or subdirectory session can be filed under the parent project, so
    an exact miss falls back to the longest-matching candidate.
    """
    cwd = (cwd or Path.cwd()).resolve()
    exact = PROJECTS / re.sub(r"[:\\/]", "-", str(cwd))
    if exact.is_dir():
        return exact
    if not PROJECTS.is_dir():
        return None
    key = re.sub(r"[:\\/]", "-", str(cwd))
    best, best_len = None, 0
    for cand in PROJECTS.iterdir():
        if cand.is_dir() and key.startswith(cand.name) and len(cand.name) > best_len:
            best, best_len = cand, len(cand.name)
    return best


def _text(entry: dict) -> str:
    msg = entry.get("message") or {}
    content = msg.get("content")
    if isinstance(content, str):
        return content
    if isinstance(content, list):
        return " ".join(
            b.get("text", "")
            for b in content
            if isinstance(b, dict) and b.get("type") == "text"
        )
    return ""


def walk(path: Path, roles=("user",)):
    """Yield (timestamp, role, text) for real prose turns in one transcript."""
    try:
        fh = path.open(encoding="utf-8", errors="ignore")
    except OSError:
        return
    with fh:
        for line in fh:
            try:
                e = json.loads(line)
            except ValueError:
                continue
            if e.get("type") not in roles:
                continue
            txt = _text(e).strip()
            if not txt or _SKIP.match(txt):
                continue
            yield e.get("timestamp", "")[:19], e.get("type", ""), txt


def transcripts(d: Path):
    return sorted(d.glob("*.jsonl"), key=os.path.getmtime, reverse=True)


def cmd_index(d: Path, args):
    print(f"{len(transcripts(d))} transcripts in {d}\n")
    print(f"{'file':38}{'MB':>7}{'msgs':>7}  {'first':21}last")
    for f in transcripts(d):
        stamps = [t for t, _, _ in walk(f) if t]
        size = f.stat().st_size / 1e6
        print(f"{f.stem[:36]:38}{size:>7.1f}{len(stamps):>7}  "
              f"{(stamps[0] if stamps else '-'):21}{stamps[-1] if stamps else '-'}")


def cmd_search(d: Path, args):
    roles = ("user", "assistant") if args.all else ("user",)
    try:
        rx = re.compile(args.query, re.I)
    except re.error:
        rx = re.compile(re.escape(args.query), re.I)
    hits = []
    for f in transcripts(d):
        for ts, role, txt in walk(f, roles):
            m = rx.search(txt)
            if m:
                lo = max(0, m.start() - args.context // 2)
                hits.append((ts, role, f.stem[:8], txt[lo:lo + args.context]))
    hits.sort(key=lambda h: h[0], reverse=True)          # newest first
    if not hits:
        print(f"no matches for {args.query!r} in {len(transcripts(d))} transcripts")
        return
    print(f"{len(hits)} matches for {args.query!r} — newest first, showing {args.n}\n")
    for ts, role, sid, snippet in hits[:args.n]:
        tag = "YOU " if role == "user" else "ai  "
        print(f"[{ts}] {tag} {sid}  {' '.join(snippet.split())}\n")
    if len(hits) > args.n:
        print(f"... {len(hits) - args.n} older matches not shown (-n to raise)")
    if args.all:
        print("\nNOTE: --all includes assistant turns, which contain reasoning that "
              "was later corrected. Verify anything you act on.")


def cmd_recent(d: Path, args):
    for f in transcripts(d)[:args.n]:
        msgs = list(walk(f))
        if not msgs:
            continue
        print(f"\n=== {f.stem[:8]}  {msgs[0][0]} -> {msgs[-1][0]}  ({len(msgs)} msgs)")
        for ts, _, txt in msgs[:3]:
            print(f"  [{ts}] {' '.join(txt.split())[:150]}")


def main():
    ap = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    ap.add_argument("--cwd", default=None, help="project dir (default: current)")
    sub = ap.add_subparsers(dest="cmd", required=True)
    sub.add_parser("index")
    s = sub.add_parser("search")
    s.add_argument("query")
    s.add_argument("-n", type=int, default=15)
    s.add_argument("--context", type=int, default=240)
    s.add_argument("--all", action="store_true", help="include assistant turns")
    r = sub.add_parser("recent")
    r.add_argument("-n", type=int, default=5)
    args = ap.parse_args()

    d = project_dir(Path(args.cwd) if args.cwd else None)
    if d is None:
        print("no transcript history found for this project", file=sys.stderr)
        return 1
    {"index": cmd_index, "search": cmd_search, "recent": cmd_recent}[args.cmd](d, args)
    return 0


if __name__ == "__main__":
    sys.exit(main())
