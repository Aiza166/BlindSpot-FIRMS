# YOUR_TASKS: what only a human can do

Written 1 Nov 2026 for Aiza Gazyani (or whoever inherits this repo). Do the tasks in number order; numbers follow date order. Tick the box in the table and write the result in the place named in each file.

## The hard rule

**Do not publish, deploy, upload or submit anything before Saturday 14 Nov 2026, 09:00 PKT.** That means no public repo, no Cloudflare deploy, no YouTube upload, no Space Apps form submission, no posting the app link. Local work, accounts and practice are fine (the Universal Event Local Lead allowed local work, see `docs/DECISIONS.md` D-005). The deadline is **Sun 15 Nov 23:59 local time of the team creator**; submit early, not at 23:50.

## What the AI already did vs what only you can do

| The AI already did (in this repo) | Only you can do |
|---|---|
| Research, plan, 42 logged decisions (`docs/DECISIONS.md`) | Confirm the team is on the right event with both members |
| Data pipeline, tests T1 to T3, results (`docs/RESULTS_*.md`) | Get your own FIRMS MAP_KEY (it is emailed to you) |
| Web app, screenshots, accessibility and security reviews | Run the project on your own PC (the data download needs your network) |
| Deploy steps and local rehearsal (`docs/DEPLOY.md`) | Create the Cloudflare account, log in, deploy on 14 Nov |
| Submission text, video script, subtitles (`docs/SUBMISSION.md`, `docs/VIDEO_SCRIPT.md`) | Record the video with your own voice, upload it, fill and press Submit on the form |
| Outreach drafts with consent wording (`docs/OUTREACH.md`) | Send messages from your LinkedIn, keep replies, get written consent |
| Read the 2025 rules | Read the official 2026 guide on 13 Nov and tell the AI what changed |

## Task index

| # | Task | When | Time | Done |
|---|---|---|---|---|
| [01](01_confirm_team_event.md) | Confirm team event and both members on the same team | Now | 15 min | [ ] |
| [02](02_firms_map_key.md) | Get FIRMS MAP_KEY, save in `.env` | By 3 Nov | 15 min | [ ] |
| [03](03_set_up_windows_pc.md) | Set up the project on your Windows PC | Before 10 Nov | 30 min (no data rebuild) | [ ] |
| [04](04_cloudflare_account.md) | Cloudflare account and `wrangler login` (no deploy) | Before 13 Nov | 20 min | [ ] |
| [05](05_obs_practice.md) | Install OBS, practise a 30 s capture | Before 13 Nov | 45 min | [ ] |
| [06](06_outreach.md) | Outreach and keeping replies | Notes now; follow-up from 14 Nov | 1 h + waiting | [ ] |
| [07](07_nov13_read_2026_guide.md) | Read the 2026 submission guide and resources | Fri 13 Nov | 1-2 h | [ ] |
| [08](08_nov14_deploy.md) | Deploy and test (after 09:00 PKT) | Sat 14 Nov | 1-2 h | [ ] |
| [09](09_record_video.md) | Record the 30 s video | Sat 14 Nov | 2-3 h | [ ] |
| [10](10_submit_form.md) | Fill and submit the Space Apps form | Sat 14 Nov (early) | 1 h | [ ] |
| [11](11_after_submission.md) | After submission | 15 Nov and after | 30 min | [ ] |

## If you are stuck

Open the repo in Claude Code and paste the prompt in `docs/CONTINUE.md`. Say which task number you are on and paste the exact error text (never paste a key).

## Things this folder could not verify

Each task file marks anything that was not checked against a real run. In short: nothing here has been tested on Windows, and the real 2026 Space Apps form fields are unknown until you open it.

## Before the repo goes public (decide by 13 Nov)
**Update 14 Nov:** the work moved to a new repository, `Aiza166/BlindSpot-FIRMS`, which starts from one import commit. Its history and its scripts do not contain the key characters described below (the redaction rule now matches any 32-character hex string). The note below applies only to the old `Aiza166/nasa-hackathon` repository, which is still public.

The first 8 hex characters of a third-party key are in git history (commits 22a3694 and 553125b) and in the redaction rule of `scripts/export_chat.py` and `scripts/export_chat_full.py`. Options, in order of effort:
1. **Accept it.** 8 of 32 characters cannot be used to recover the key. Cheapest.
2. **Rewrite history in this repo** (git filter-repo or an orphan squash), then force-push. Needs the same care as any force-push; keep a local clone first.
3. **New repo.** Copy the working tree (not `.git`) into a new private repo, make one first commit, make that one public. Loses history and the chat-based audit trail; keep the old private repo as the archive.
Whichever you pick, run the checks in `docs/QA_REPORT_FINAL.md` section D2 again afterwards. Do not make anything public before 14 Nov 09:00 PKT.
