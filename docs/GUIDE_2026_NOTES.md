# 2026 Project Submission Guide: notes (P5)

Read 14 Nov 2026 from https://www.spaceappschallenge.org/resources/project-submission-guide/ (page dated 13 Nov 2026). This replaces the 2025-guide assumptions marked ⚠️ in `docs/PLAN.md` §0 and `docs/VIDEO_GUIDE.md` §1. Where this file and an older doc disagree, this file and the guide win.

## Dates

- Submission opens **Sat 14 Nov 2026, 09:00** and closes **Sun 15 Nov 2026, 23:59**, local time of the team's Local Event.
- Universal Event teams: the same times, in the local time of the **Team Owner's area of residence**.
- Anything saved or submitted after the deadline is not judged. You can edit and resubmit as often as you like until then; judges see the **last saved submission**.
- Local judging and awards times may differ: ask the Local Lead.

## Where the form is

Profile icon → "My Team" → "Project" tab (appears from 14 Nov 09:00) → blue "Edit". Use "Save Progress" often. Turn the edit "Lock" on while editing; a teammate can still break the lock and overwrite unsaved work, so agree who edits.

## Form fields (2026 names)

| Field | What the guide asks | Our source |
|---|---|---|
| Project Name | Name of the project | `docs/SUBMISSION.md` "Project name" |
| High-Level Project Summary | What you built, how it addresses the challenge, why it matters | "High-level summary" |
| Link to Project Demo | Public link to a **≤30 s video** or a **≤7-slide deck** (title and intro slides count) | "Link to Project Demo" (YouTube URL from task 09) |
| Link to Final Project | Public link to the final project: website, repository or file host | "Link to Final Project" (Cloudflare Pages URL; repository as a second link) |
| Detailed Project Description | What it does, how it works, benefits, goals, tools/languages/hardware/software used | "Detailed description" (incl. "Tools and languages") |
| Use of Super Intelligence (SI) | Did you use SI tools, and how? **Judges do not see this answer.** | "Use of Super Intelligence (SI)" |
| NASA Data | Which NASA data and resources. **At least one is required for a Global Award.** | "NASA data used" |
| Space Agency Partner Data and Other References | All data, resources and tools used, including open-source code, text and images; permission for copyrighted material | "Space agency partner data and other references" |

Images (JPG, PNG, GIF, up to 10 MB) can be pasted or uploaded. Videos and documents cannot: link them.

## Links

- Every link must open with **no password, permission, login or registration**. Test each one in a private window before submitting. "If judges can't access your project, it can't be evaluated or judged."
- Optional for a new website: request a FortiGuard Web Filter classification (https://www.fortiguard.com/faq/wfratingsubmit; Company Name "N/A"; pick the closest category, e.g. education or web-based application) so school or office filters do not block judges. Not required.

## Demo

- **Video ≤30 s** or **slides ≤7** (including title and intro). **Projects over either limit are not eligible for Global Judging.**
- English. A video may be spoken in another language only with English subtitles. Slides must be in English.
- Suggested video order: 0:00 introduce yourself and the team name; 0:02 the challenge and why you chose it; 0:05 project title and tagline; 0:10 how it works, with images or the prototype, a user's experience, and how NASA and partner data made it possible; 0:20–0:30 the future: what it could do for people.
- Slides must show the team name, team member names and the chosen challenge, an image of the project, the user experience, and how NASA and space-agency data make it possible.
- The demo counts toward the whole score, mostly through **Presentation**; most of the judging is the project page itself.

## Super Intelligence (SI, i.e. AI) rules

- Allowed as a tool. **Not allowed for coming up with the idea** of how to solve the challenge.
- Generated content may not use or modify NASA branding (logos, flags, mission identifiers).
- **Images and videos:** visible watermark showing SI generation.
- **Audio:** acknowledge SI in descriptive text and metadata.
- **Code and data:** acknowledge SI in **descriptive text and metadata**. For us: README, the submission, and the package metadata (`pyproject.toml`, `web/package.json`). See `docs/DECISIONS.md` D-048.
- Judges do not see the SI form answer, but they do see watermarks, text and metadata in the project, and judge "originality, intent, and execution" on the SI-assisted parts we identify.

## Eligibility checklist

- [ ] All team members are confirmed participants at the **same** Local Event (or the same Universal Event team).
- [ ] Every required field is filled (the form will not submit otherwise).
- [ ] All content is in English.
- [ ] No images, video, audio or other likeness of anyone **under 18** in the demo or project.
- [ ] Tick "Terms and Conditions" and "Confirm All Work is Original", then **Submit for Judging**. A banner confirms success.
- [ ] Demo within 30 s / 7 slides.
- [ ] At least one NASA dataset named (FIRMS MODIS and VIIRS: yes).

## Judging

Five criteria: **Impact, Creativity, Validity, Relevance, Presentation** (details in the 2026 Judging and Awards Guide, https://www.spaceappschallenge.org/resources/judging-awards-guide/). Same five as `docs/GRADE.md`.

## Space Agency Partners 2026 (use encouraged, not required)

Angola National Space Programme Management Office, Bahrain Space Agency, Brazilian Space Agency, CSA, ESA, ISRO, Italian Space Agency, JAXA, KASA, Mohammed Bin Rashid Space Center (UAE), CONAE (Argentina), NASRDA (Nigeria), Paraguayan Space Agency, Senegalese Space Studies Agency, Spanish Space Agency, Turkish Space Agency, UK Space Agency. We use none; the submission says so.

## Certificate

Available on your Profile after the team submits ("Participant Information" → "Download Participant Certificate", PDF, Letter size). The name comes from "Full Name" in your Profile.

## What changed against our 2025-based plan

| Our assumption | 2026 guide | Action taken |
|---|---|---|
| ≤30 s video or ≤7 slides | Confirmed; over the limit = not eligible for Global Judging | PLAN §0 and VIDEO_GUIDE §1 marked ✅ |
| One "Demo and project links" field | Two fields: "Link to Project Demo" and "Link to Final Project" | Submission template split into two sections |
| "Use of AI" statement | "Use of Super Intelligence (SI)"; hidden from judges; SI in code and data must also be acknowledged in metadata | Section renamed; acknowledgement added to README and package metadata (D-048) |
| Detailed description content | Also asks which tools, languages, hardware and software were used | "Tools and languages" subsection added |
| Partner data field | "Space Agency Partner Data and Other References": list all code, text and images used | Section renamed; open-source libraries listed |
| Video order | Name and team name first, then challenge, title, how it works, future | Video script: gap noted below; not rewritten |
| Under-18 rule, English-only, NASA branding | Stated explicitly | Added to the checklist above and to task 10 |

## Not done (needs a person)

- **Team name.** The guide asks for the team name in the video and slides. The repo only has member names (`TEAM_NAMES` in `pipeline/blindspot/story.py`). Add the team name as registered.
- **Video "future" beat.** The current script ends on the caution flag, not on what the project could do next (the guide's 0:20–0:30 beat). Decide with the team whether to change the last line; any new line must keep the "cannot separate later burning from less burning" caveat and come from results JSON.
- **`make story`** was not re-run on 14 Nov: it needs `web/e2e/artifacts/custom_aoi_check.json` from `make web-test`. The prose edits were applied to both the templates and the generated files by hand; no number changed. A scratch render with `story.render` (AOI values stubbed from `docs/SUBMISSION_SOURCES.md`, outside the repo) produced bodies identical to the edited `SUBMISSION.md`, `VIDEO_SCRIPT.md` and `MORNING_SUMMARY.md`. Still run `make web-test` then `make story` and check that `git diff` shows no change to the generated files.
