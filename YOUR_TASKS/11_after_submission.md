# 11. After submission

**When:** 15 Nov and after. **Time:** 30 min.

## Steps
1. Re-open the team page: confirm the submission shows as submitted for both members, and Kissa sees the same.
2. Open the live URL and the video link logged out one more time (checkpoint H37).
3. **Repo visibility decision:** private is fine unless the 2026 rules or judging ask for code. If you make it public, first run the secret scan in `docs/DEPLOY.md` section G (`git log -p | grep -i "map_key=\|FIRMS_MAP_KEY=[a-f0-9]"`, and no tracked `.env` or `.dev.vars`). Also consider adding a licence first (none is chosen yet; do not pick one without deciding deliberately).
4. If you made the repo public: also check `docs/chat/CHAT_LOG.md` for anything personal (it holds your name, email context and the full conversation text).
5. Thank the people who replied (task 06), and tell them the link. Do not publish a quote you do not have written consent for.
6. Do **not** delete the Cloudflare project or the key until judging is over; rotate or delete the FIRMS key afterwards if you want.
7. Update `docs/CHECKPOINTS.md` (H37) and tell Claude to refresh `HANDOFF.md` with the final status.

## Common problems
- **Edit after submission:** depends on the 2026 rules; check the guide before assuming you can.
