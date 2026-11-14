# Cold read 2: prompt for a fresh reader

The session that rewrote the submission (1 Nov) had no Agent tool, so it did not run this cold read. Run it in a fresh session or subagent that has not seen the project.

## Give the reader only

- `docs/SUBMISSION.md`
- `docs/VIDEO_SCRIPT.md`

Strip the "Number sources" table from both before pasting. Give no other file, no repo access and no context about earlier reviews.

## Prompt

> You are a busy NASA Space Apps judge with ten minutes for this project. The challenge is "Harmonization of MODIS and VIIRS Hot Spots". Read the submission and the 30-second video script below, once, as a judge would.
>
> 1. Score each criterion 1–5 with one or two sentences of reasons: Impact, Creativity, Validity, Relevance, Presentation.
> 2. List what is unclear, what is overclaimed and what is missing, quoting the exact phrase each time.
> 3. Give the top fixes ranked by how much they would raise the scores, with the criterion each one helps.
>
> Be blunt. Do not suggest new analyses that would take more than a day.
>
> [paste SUBMISSION.md]
>
> [paste VIDEO_SCRIPT.md]

## After the read

1. Save the reply verbatim to `docs/review/COLD_READ_2.md`, with reviewer, date and model at the top.
2. Fix what holds up in `docs/templates/*.tmpl.md` (numbers only via JSON placeholders), then `make story` and `make test`.
3. Append a Resolution table (point, holds up?, action) and a before/after score table. Before = docs/review/COLD_READ.md: Impact 3, Creativity 4, Validity 3, Relevance 4, Presentation 3.
