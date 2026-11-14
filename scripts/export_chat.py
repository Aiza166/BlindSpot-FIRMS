#!/usr/bin/env python3
"""Export the human-readable text of a Claude Code chat to Markdown.

Reads Claude Code session transcripts (JSON lines, read-only) and writes only
user messages and assistant text replies, in time order, to docs/chat/CHAT_LOG.md
(split into part files above ~2 MB). Tool calls, tool results, system reminders,
hook output, task notifications and images are skipped (images become "[image]").
Likely secrets are redacted. Messages are de-duplicated by uuid across files, so
overlapping transcripts of the same session are merged.

Usage (from the repo root):
    python3 scripts/export_chat.py [transcript.jsonl ...]
With no arguments it uses the two default transcript paths below. Transcripts live
outside the repo (in ~/.claude/projects/); they are not available to a new account,
which is why the exported log is kept in the repo.
"""

import json
import re
import sys
from pathlib import Path

DEFAULTS = [
    "/root/.claude/projects/-home-user/d6880b4f-d2d5-5631-b1c1-41f3c2d31ab3.jsonl",
    "/root/.claude/projects/-home-user-nasa-hackathon/d6880b4f-d2d5-5631-b1c1-41f3c2d31ab3.jsonl",
]
OUT_DIR = Path(__file__).resolve().parent.parent / "docs" / "chat"
MAX_BYTES = 2_000_000

SKIP_PREFIXES = (
    "<system-reminder",
    "<task-notification",
    "<command-",
    "<local-command",
    "<user-prompt-submit-hook",
    "<bash-",
    "Caveat:",
    "[Request interrupted",
)
BLOCK_RE = re.compile(
    r"<(system-reminder|task-notification|local-command-[a-z]+|command-[a-z]+|"
    r"user-prompt-submit-hook)[^>]*>.*?</\1>",
    re.S,
)
COUNTS = {"hex32": 0, "sk": 0, "map_key": 0, "token": 0, "third_party_key": 0}


def redact(text: str) -> str:
    def sub(name, pat, repl, flags=0):
        nonlocal text
        text, n = re.subn(pat, repl, text, flags=flags)
        COUNTS[name] += n

    sub("third_party_key", r"\b[0-9a-f]{32}\b", "[REDACTED-third-party-key]")
    sub("map_key", r"(MAP_KEY\s*[=:]\s*)[^\s`'\"]+", r"\1[REDACTED]", re.I)
    sub("sk", r"\bsk-[A-Za-z0-9_\-]{8,}", "[REDACTED-sk]")
    sub(
        "token",
        r"\b(?:ghp|gho|ghs|github_pat|xox[abp]|AKIA|AIza)[A-Za-z0-9_\-]{10,}",
        "[REDACTED-token]",
    )
    sub("token", r"\b(Bearer\s+)[A-Za-z0-9._\-]{20,}", r"\1[REDACTED-token]")
    sub("hex32", r"\b[0-9a-fA-F]{32,}\b", "[REDACTED-hex]")
    return text


def clean(text: str) -> str:
    text = BLOCK_RE.sub("", text)
    text = re.sub(r"data:[a-z]+/[a-z0-9.+-]+;base64,[A-Za-z0-9+/=]{100,}", "[image]", text)
    text = re.sub(r"[A-Za-z0-9+/=]{500,}", "[binary omitted]", text)
    return text.strip()


def extract(d):
    """Return (role, text) or None."""
    t = d.get("type")
    if t not in ("user", "assistant") or d.get("isSidechain") or d.get("isMeta"):
        return None
    msg = d.get("message")
    if not isinstance(msg, dict):
        return None
    content = msg.get("content")
    parts = []
    if isinstance(content, str):
        parts.append(content)
    elif isinstance(content, list):
        for b in content:
            if not isinstance(b, dict):
                continue
            bt = b.get("type")
            if bt == "text" and isinstance(b.get("text"), str):
                parts.append(b["text"])
            elif bt in ("image", "document") and t == "user":
                parts.append("[image]")
            # tool_use, tool_result, thinking: skipped on purpose
    else:
        return None
    text = "\n\n".join(parts)
    if t == "user" and text.lstrip().startswith(SKIP_PREFIXES):
        text = BLOCK_RE.sub("", text)
        if text.lstrip().startswith(SKIP_PREFIXES):
            return None
    text = clean(text)
    if not text:
        return None
    return ("You" if t == "user" else "Claude"), text


def main(paths):
    items, seen, stats = [], set(), {}
    for p in paths:
        n = bad = 0
        try:
            fh = open(p, encoding="utf-8", errors="replace")
        except OSError as e:
            print(f"cannot open {p}: {e}", file=sys.stderr)
            continue
        with fh:
            for line in fh:
                try:
                    d = json.loads(line)
                except Exception:
                    bad += 1
                    continue
                if not isinstance(d, dict):
                    continue
                uid = d.get("uuid")
                if uid in seen:
                    continue
                r = extract(d)
                if r is None:
                    continue
                seen.add(uid)
                items.append((d.get("timestamp") or "", len(items), r[0], r[1]))
                n += 1
        stats[p] = (n, bad)
    items.sort(key=lambda x: (x[0], x[1]))
    # drop immediate exact duplicates
    out, prev = [], None
    for ts, _, who, text in items:
        key = (who, text)
        if key == prev:
            continue
        prev = key
        out.append(f"### {who}" + (f" · {ts}" if ts else "") + "\n\n" + redact(text) + "\n")
    header = (
        "# Chat log (human-readable text only)\n\nSee README.md in this folder for what this is "
        "and its limits. Tool calls and results are omitted. Secrets are redacted.\n\n---\n\n"
    )
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    for old in OUT_DIR.glob("CHAT_LOG*.md"):
        old.unlink()
    chunks, cur, size = [], [], 0
    for blk in out:
        b = len(blk.encode("utf-8"))
        if size + b > MAX_BYTES and cur:
            chunks.append(cur)
            cur, size = [], 0
        cur.append(blk)
        size += b
    chunks.append(cur)
    names = []
    for i, c in enumerate(chunks, 1):
        name = "CHAT_LOG.md" if len(chunks) == 1 else f"CHAT_LOG_part{i}.md"
        title = header if i == 1 else f"# Chat log, part {i}\n\n---\n\n"
        (OUT_DIR / name).write_text(title + "\n".join(c), encoding="utf-8")
        names.append(name)
    print("files:", names)
    print("turns:", len(out), "per input:", stats)
    print("redactions:", COUNTS)
    for n in names:
        print(n, (OUT_DIR / n).stat().st_size, "bytes")


if __name__ == "__main__":
    main(sys.argv[1:] or DEFAULTS)
