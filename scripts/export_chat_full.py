#!/usr/bin/env python3
"""Export the complete working transcript of the original Claude Code sessions to a gzipped
Markdown file, for search and for a new assistant to read. Read-only on the transcripts.

Unlike scripts/export_chat.py (readable text only), this keeps tool calls and a truncated copy of
tool results, so a new session can see what was actually run and found. Secrets are redacted.

Usage: python scripts/export_chat_full.py
Output: docs/chat/FULL_TRANSCRIPT.md.gz  (read with: zcat docs/chat/FULL_TRANSCRIPT.md.gz | less)
"""

from __future__ import annotations

import gzip
import json
import re
import sys
from pathlib import Path

SOURCES = [
    Path("/root/.claude/projects/-home-user/d6880b4f-d2d5-5631-b1c1-41f3c2d31ab3.jsonl"),
    Path(
        "/root/.claude/projects/-home-user-nasa-hackathon/d6880b4f-d2d5-5631-b1c1-41f3c2d31ab3.jsonl"
    ),
]
OUT = Path(__file__).resolve().parents[1] / "docs" / "chat" / "FULL_TRANSCRIPT.md.gz"
RESULT_LIMIT = 3000
INPUT_LIMIT = 1500

REDACTIONS = [
    (re.compile(r"\b[0-9a-f]{32}\b"), "[REDACTED-third-party-key]"),
    (re.compile(r"\b[0-9a-fA-F]{32,}\b"), "[REDACTED-hex]"),
    (re.compile(r"\bsk-[A-Za-z0-9_\-]{8,}"), "[REDACTED-sk]"),
    (
        re.compile(r"\b(?:ghp|gho|ghs|github_pat|xox[abp]|AKIA|AIza)[A-Za-z0-9_\-]{10,}"),
        "[REDACTED-token]",
    ),
    (re.compile(r"\b(Bearer\s+)[A-Za-z0-9._\-]{20,}"), r"\1[REDACTED-token]"),
    (re.compile(r"(MAP_KEY\s*[=:]\s*)[^\s`'\"]+", re.I), r"\1[REDACTED]"),
]
REMINDER = re.compile(r"<system-reminder.*?</system-reminder[^>]*>", re.S)
counts = {"redactions": 0}


def redact(text: str) -> str:
    for pat, repl in REDACTIONS:
        text, n = pat.subn(repl, text)
        counts["redactions"] += n
    return text


def clip(text: str, limit: int) -> str:
    return (
        text
        if len(text) <= limit
        else text[:limit] + f"\n[... {len(text) - limit} more characters omitted]"
    )


def render_block(block: object) -> str:
    if isinstance(block, str):
        return block
    if not isinstance(block, dict):
        return ""
    kind = block.get("type")
    if kind == "text":
        return str(block.get("text", ""))
    if kind == "image":
        return "[image]"
    if kind == "tool_use":
        args = json.dumps(block.get("input", {}), ensure_ascii=False)
        return f"[tool call: {block.get('name')}] {clip(args, INPUT_LIMIT)}"
    if kind == "tool_result":
        body = block.get("content", "")
        if isinstance(body, list):
            body = "\n".join(render_block(b) for b in body)
        return f"[tool result] {clip(str(body), RESULT_LIMIT)}"
    return ""  # thinking and unknown blocks are skipped


def main() -> int:
    parts: list[str] = [
        "# Full working transcript (tool calls and truncated results included)\n",
        "Secrets are redacted; images are shown as [image]; long tool results are truncated. "
        "System reminders are removed. The two source files overlap, so some turns appear twice.\n",
    ]
    seen: set[str] = set()
    turns = 0
    for src in SOURCES:
        if not src.exists():
            print(f"missing: {src}", file=sys.stderr)
            continue
        parts.append(f"\n\n---\n\n## Source: {src.parent.name}\n")
        with src.open(encoding="utf-8", errors="replace") as fh:
            for line in fh:
                try:
                    rec = json.loads(line)
                except json.JSONDecodeError:
                    continue
                if rec.get("type") not in ("user", "assistant"):
                    continue
                msg = rec.get("message") or {}
                content = msg.get("content")
                blocks = content if isinstance(content, list) else [content]
                text = "\n".join(t for t in (render_block(b) for b in blocks) if t)
                text = REMINDER.sub("", text).strip()
                if not text:
                    continue
                key = f"{rec.get('uuid')}"
                if key in seen:
                    continue
                seen.add(key)
                who = "You" if rec["type"] == "user" else "Claude"
                ts = rec.get("timestamp", "")
                parts.append(f"\n### {who} {ts}\n\n{redact(text)}\n")
                turns += 1
    OUT.parent.mkdir(parents=True, exist_ok=True)
    with gzip.open(OUT, "wt", encoding="utf-8") as gz:
        gz.write("".join(parts))
    print(f"turns={turns} redactions={counts['redactions']} -> {OUT} ({OUT.stat().st_size} bytes)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
