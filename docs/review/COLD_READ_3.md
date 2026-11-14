# Cold read 3 (judge view, SUBMISSION.md + VIDEO_SCRIPT.md only)

| Criterion | Score | Reason |
|---|---|---|
| Impact | 4 | A district officer can trust a 2003–2025 history, and the Sangrur/Kasur example is persuasive, but coverage is Punjab only and NRT data is not live. |
| Creativity | 4 | Pairing the factor with reliability flags per region and year ("where the correction stops working") is new; the calendar UI itself is the standard ask. |
| Validity | 5 | Tests fixed in advance, the failure is reported openly, the post-hoc rule change is disclosed, NOAA-20 is used as a cross-check, and the circular MCD64A1 check was rejected with a reason. |
| Relevance | 4 | Every item in the brief is mapped, but the brief is global and "a selected area" here means Pakistan and northern India only; the video never shows the current month against the median. |
| Presentation | 4 | Clear and honest, but long and dense (T1/T2/T3, O/T/D, log-SD) and it leaks internal references (template comment, D-008, RESULTS_T2, "brag or Hyperframes"). |

## Top 5 remaining fixes
1. Video: put the month card (current month against the median, plus NOAA-20) on screen in 0:24–0:30. It is a headline requirement and is currently missing. Replace {NAMES}.
2. Strip internal artefacts from the judge-facing text: the HTML template comment, "D-008", "RESULTS_T2", "docs/..." paths, and "We did not use brag or Hyperframes" (meaningless to a judge). Link to a public repo instead.
3. Fix the summary wording: "+613% more" is redundant (use "+613%" or "7.1x"), and "disappears after harmonization" overstates +12.7%; say "falls to +12.7%, within normal year-to-year spread".
4. Results table: make the verdict format consistent ("pass" in lower case vs "**Fail.**"), and add one plain-English line under the table (for example "Correction works for 2012 in both regions; after 2021 it is flagged").
5. Say plainly why the work is limited to Punjab and how to extend it (global FIRMS inputs, so only the factor fit per region is needed), so Relevance to a global brief is not marked down; for example, name one ready-made extra region.
