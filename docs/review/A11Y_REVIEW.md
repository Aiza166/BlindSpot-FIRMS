# Blind Spot web: accessibility review (WCAG 2.2 AA)

Date: 2026-10-31. Build: existing static export `web/out` (commit da7bc83), served locally with `web/scripts/serve.mjs`. Nothing deployed and no source changed.

Method: Playwright (Chromium) + axe-core 4.10.2 (wcag2a/aa, 21aa, 22aa, best-practice) on 5 pages x light/dark (`colorScheme` emulation) x 1440/390 px = 20 runs. Also scripted Tab order and focus-outline probes, keyboard district pick, calendar arrow-key navigation, and manual contrast math on the CSS tokens in `app/globals.css`, plus a source read of `components/*.tsx`.

## Summary

Overall the app is in good shape. axe found no text-contrast violations in any theme or width. `lang="en"` is set, every page has one h1 and the headings run in order, and form fields have labels. The calendar is a roving-tabindex grid with full names per cell ("February 2004: 0 S-NPP-equivalent hotspots, Aqua MODIS scaled to S-NPP"). Arrow keys, Home/End and Ctrl+Home/End all work, and the tooltip also shows on focus with an `aria-live` readout. The map is never the only way to pick an area: there is a district combobox and typed box and radius fields. Export buttons have text labels, and `prefers-reduced-motion` is honoured.

The remaining problems are mostly about **non-text contrast** (control borders, no-data hatch, focus ring on mid-ramp cells) and a few semantic gaps.

## Findings

| # | Page | Element / selector | WCAG | Sev | Finding | Fix |
|---|---|---|---|---|---|---|
| 1 | Explorer (all themes) | `input[type=search|number|month]`, `select`, `.seg`, `.theme-btn`, `.results-list` borders = `--rule` | 1.4.11 Non-text contrast | MEDIUM | The control borders are too faint to show where a control is: `--rule` vs `--sheet` is 1.52:1 (light) and 1.40:1 (dark), and vs `--paper` 1.37 / 1.54. The minimum is 3:1. | Add a `--control-border` token at 3:1 or more (e.g. light `#7b8894`, dark `#5f7282`) and use it on inputs, select, seg group and theme button. `--rule` can stay for decorative dividers. |
| 2 | Explorer calendar + legend | `.cell.nodata` hatch and its legend swatch (`--nodata`) | 1.4.11 | MEDIUM | The no-data hatch is 1.31:1 (light) and 1.22:1 (dark) against the sheet, so a no-data month can look like a blank or a zero month. The screen-reader name does say "no data". | Darken `--nodata` to 3:1 or more (light `#8d99a3`, dark `#5a6b78`), or add a visible glyph such as a small "–" in no-data cells. |
| 3 | Explorer calendar | `.cell:focus-visible` (outline `--focus`) | 1.4.11 / 2.4.7 | MEDIUM | The light-theme focus colour `#b5531c` is about 1.1:1 against the mid cividis stops (`#707173`, `#8a8678`), and the 1px offset ring sits over neighbouring cells. Focus is hard to see in the middle of the ramp. (Dark-theme `#f0a35e` is fine against dark cells but weak against the yellow end.) | Use a two-tone ring, e.g. `outline: 2px solid var(--ink); box-shadow: 0 0 0 4px var(--sheet)`, or an inner plus outer ring, so at least one edge is 3:1 or more against any ramp colour. |
| 4 | Explorer calendar | `.cell.out` (opacity 0.28) and its `aria-label` | 1.3.1 Info and relationships | MEDIUM | Months outside the chosen period are only faded. `describe()` does not mention it, so a screen-reader user hears out-of-period values as if they were in scope. Faded value text in "Show values" mode also drops below 4.5:1. | Add ", outside selected period" to the label for `!inRange` cells. Lighten the fill only (keep the cell or text opacity at 1), or hide the value text in out-of-range cells. |
| 5 | Results (390 px) | `table[data-testid=t1-table]`, `table[data-testid=t2-table]` (`display:block; overflow-x:auto`) | 2.1.1 Keyboard | MEDIUM (axe "serious") | On a phone these tables scroll sideways but cannot get keyboard focus, so keyboard users cannot reach the clipped columns. | Wrap each table in `<div role="region" aria-label="T1 verdicts" tabindex="0" class="table-wrap">` and move the overflow onto that wrapper (keep `display:table` on the table so its semantics stay intact). |
| 6 | All pages | no skip link; first Tab stops are 7 masthead items | 2.4.1 Bypass blocks | MEDIUM | There is no "Skip to content" link. On Explorer the calendar cell is about the 25th Tab stop. | Add a visually hidden-until-focused `<a href="#main">Skip to content</a>` as the first item in `<body>`, and give each `<main>` `id="main"`. |
| 7 | Explorer | `.tip[role=tooltip]` | 1.4.13 Content on hover or focus | LOW | The tooltip cannot be dismissed with Escape, and it has `pointer-events:none`, so the pointer cannot rest on it. The same text is in the `aria-live` readout, which limits the impact. | On Escape keydown in the grid, call `setHover(null)`. Optionally set `aria-describedby` on the focused cell to point at the tip. |
| 8 | Explorer | `.maplibregl-ctrl-zoom-in/out` | 2.4.7 Focus visible | LOW | These buttons have `outline:none` and rely on MapLibre's default blue box-shadow, which is not themed and is weak on the dark sheet. | `.maplibregl-ctrl button:focus-visible { outline: 2px solid var(--focus); outline-offset: 1px; }` |
| 9 | Explorer | Map canvas Tab stop (`canvas.maplibregl-canvas`, "Map") | 2.4.3 Focus order / 4.1.2 | LOW | The canvas takes focus between the search field and the period inputs. It pans with the arrow keys but cannot select a district by keyboard. This is acceptable because the combobox offers the same choice, but the accessible name is just "Map". | Give the canvas `aria-label` the region text ("Map of districts; use the district search to select by keyboard"), or set `keyboard:false` + `tabindex=-1` on the canvas and keep only the zoom buttons focusable. |
| 10 | Explorer | Box tab "Draw on map" (`[data-testid=box-draw]`) | 2.1.1 | LOW (alternative exists) | Drawing works only by mouse drag. The typed W/E/S/N fields cover the same function, so this passes. The button gives no hint to keyboard users. | When drawing is on, change the hint to "Mouse or touch only; type the edges above for keyboard use." |
| 11 | Explorer | `span[role=columnheader][aria-label="Sensor era"]`, `[aria-label="Year"]` | 1.3.1 | LOW (axe empty-table-header) | These header cells have no visible text. The era band itself is `aria-hidden`, although each cell label carries the platform. | Put sr-only text inside the spans instead of `aria-label`, or mark the era column `role="presentation"` and drop its header. |
| 12 | All pages | `p.scope` (outside landmarks) | 1.3.1 / best practice | LOW | This scope statement sits between the `<header>` and the `<main>`. | Move it inside `<header>`, or render it as the first child of each `<main>`. |
| 13 | Explorer | district combobox `#q` | 4.1.2 | LOW | `aria-expanded` stays true whenever matches exist, and the list is always shown. There is no Escape to clear. Hovering an option highlights it visually, but `aria-selected` follows only the keyboard selection, so the two can disagree. | Tie `aria-expanded` to whether the list is open, add Escape to clear, and drop the `li:hover` background in favour of the `aria-selected` styling only. |
| 14 | Explorer 390 px | `.cell` (about 20 x 18 px) | 2.5.8 Target size (minimum) | LOW / info | The calendar cells are smaller than 24 px, but they are hover-only readouts, not actions, so they arguably fall outside 2.5.8. Keyboard and screen-reader paths cover the content. | Optional: let a tap set the readout (`onClick={show}`) so touch users get values without hovering. |

## Passed checks (no action)

- **Text contrast**: axe passes in all 20 runs. By token: `--ink-2` vs sheet is 6.60 (light) / 6.25 (dark), `--warn` 7.94 / 8.74, `--accent` 8.55 / 8.29. In-cell text uses `textOn()` (light or dark text by ramp position) and passes.
- **Colour is never the only signal**:
  - Eras: hatched vs plain band, a text label, a seam line, and the source named in each cell label.
  - Partial months: a dot plus ", partial month" in the cell label.
  - Verdicts: text labels, with inconclusive also dashed.
  - Charts: Aqua is a thick line in the overpass chart, and points are crosses vs circles in the ratio chart.
- **Keyboard**: the area picker (District/Box/Point buttons, combobox with arrow keys and Enter, typed box and radius fields, Use buttons) is fully operable. Picking "Lahore" by keyboard loaded the series.
- **Calendar**: one Tab stop; Arrows, Home/End and Ctrl+Home/End work; every cell, including out-of-archive ones, has a full name; the tooltip shows on focus.
- **Focus**: the visible outline appeared on every Tab stop checked, apart from findings 3 and 8. The Tab order follows the visual order.
- **Labels and language**: PNG and CSV buttons have descriptive text ("Save calendar PNG", "Download hotspots CSV"). `html lang="en"` is set. Headings run h1 to h2 in order on all pages. Inputs have wrapping or `for` labels, and the raw-series select has an sr-only label.
- **Reduced motion**: a global `prefers-reduced-motion` rule is in place, map `fitBounds` uses `duration:0`, and MapLibre honours the media query.
- **Theme toggle**: the accessible name "Switch to dark theme" contains the visible label "Dark" (2.5.3).

## Priority order
1, 3, 2, 5, 4, 6, then the LOW items.

## Resolution (31 Oct, D-038)
Fixed: all six MEDIUMs. #1 is `--control-border` (≥3:1). #2 darkens `--nodata` (≥3.3:1). #3 is a two-tone ink + sheet focus ring in both themes. #4 adds ", outside selected period" to the label and hides values. #5 wraps each table in a focusable labelled `role=region` (4 on Results, 1 on Attribution). #6 adds a skip link and `#main`.
Also fixed: LOWs #7 (Escape closes the tooltip), #8 (MapLibre button focus outline), #9 (named canvas), #10 (keyboard hint while drawing), #11 (sr-only header text), #12 (scope line inside `<header>`) and #13 (`aria-expanded` follows list visibility, Escape clears, no hover-only highlight).
Deferred: #14 tap-to-read (optional).
**Rerun:** the same axe 4.10.2 script (5 pages × light/dark × 1440/390), against the new build. **20/20 runs with 0 violations** (26 before), in `axe-after.json`. A probe confirmed that the first Tab reaches "Skip to content", the focused cell shows the ink outline with a 4px sheet halo, Escape removes the tooltip, and there are 4 scrollable regions on Results.
