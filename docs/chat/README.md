# Exported chat log

`CHAT_LOG.md` is the human-readable text of the Claude Code conversation that built this project: your messages ("You") and Claude's text replies ("Claude") in time order, 26 Oct to 1 Nov 2026. It exists so a new person or Claude account can see how decisions arose.

## What is and is not in it

- Only user messages and assistant text replies. Tool calls, tool results, system reminders, hook output, task notifications and images are left out; image attachments appear as "[image]" (and some messages say "<!-- attach -->").
- Many Claude turns were pure tool work, so the log is much shorter than the real session and has gaps. Subagent conversations are not included.
- The source transcripts may be **truncated or compacted** by Claude Code (long sessions are summarised to fit the context window), so early parts may be missing or condensed. Two transcript files of the same session were merged and de-duplicated by message id; messages after the last export (1 Nov, ~19:18 UTC) are not included.
- Secrets are redacted by pattern (long hex strings, `sk-` keys, `MAP_KEY=` values, tokens). The pattern is not perfect; read it before making the repo public. It also contains personal names and context.

## Which source to trust

`docs/DECISIONS.md` is the reliable, curated summary of every decision and why. Use this chat log only for background. It can contain superseded ideas.

## Regenerating

`python3 scripts/export_chat.py` (only works where the original transcripts at `~/.claude/projects/` exist; paths are at the top of the script). Re-running overwrites this folder's `CHAT_LOG*.md`.

## Full transcript

`FULL_TRANSCRIPT.md.gz` (gzipped Markdown, about 0.9 MB unpacked) keeps everything `CHAT_LOG.md` leaves out: tool calls (arguments clipped to 1,500 characters) and tool results (clipped to 3,000), with system reminders removed, images shown as [image], thinking omitted and secrets redacted (long hex strings, `sk-`/GitHub tokens, `MAP_KEY=` values, and one third-party key fragment). Some turns appear twice because two source files overlap. Read with `zcat docs/chat/FULL_TRANSCRIPT.md.gz | less`. Regenerate with `python3 scripts/export_chat_full.py` (needs the original transcripts under `~/.claude/projects/`). It is much larger than the readable log, so treat it as an archive to search, not to read start to finish.

A new session cannot literally resume the old one. Reading `docs/WORKING_WITH_AIZA.md`, `CHAT_LOG.md` and `docs/DECISIONS.md` is the closest substitute.
