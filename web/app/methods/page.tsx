import type { Metadata } from "next";
import { readData } from "@/lib/server";
import type { T1 } from "@/lib/results";
import type { CalibrationDoc, Constants } from "@/lib/types";

export const metadata: Metadata = { title: "Methods · Blind Spot" };

export default function Methods() {
  const t1 = readData<T1>("results/t1.json");
  const c = readData<Constants>("constants.json");
  const cal = readData<CalibrationDoc>("results/calibration.json");
  const p = t1.parameters;
  const span = (ys: number[]) => `${ys[0]}–${ys[ys.length - 1]}`;
  // Aqua -> S-NPP factors across regions and months, read from calibration.json (rule 7: no typed numbers).
  const aquaFactors = Object.values(cal.factors["Aqua->SNPP"] ?? {})
    .flatMap((r) => r.factor)
    .filter((x): x is number => x !== null)
    .sort((a, b) => a - b);
  const fMin = aquaFactors[0] ?? 0;
  const fMax = aquaFactors[aquaFactors.length - 1] ?? 0;
  const mid = Math.floor(aquaFactors.length / 2);
  const fMed = aquaFactors.length % 2 ? (aquaFactors[mid] ?? 0) : ((aquaFactors[mid - 1] ?? 0) + (aquaFactors[mid] ?? 0)) / 2;
  const nAbove = aquaFactors.filter((x) => x > 1).length;
  return (
    <main id="main" className="page">
      <h1>Methods and limitations</h1>
      <p>Blind Spot counts satellite fire detections (hotspots) per local solar month and puts the whole record from 2003 on one scale: what S-NPP VIIRS would have seen.</p>

      <h2>From detections to a calendar</h2>
      <ol>
        <li>NASA FIRMS standard archive for Terra and Aqua MODIS, S-NPP and NOAA-20 VIIRS. Vegetation fires only (type 0), MODIS confidence of at least 30, VIIRS confidence nominal or high.</li>
        <li>A persistent-hotspot mask removes cells that burn all year (kilns, flares, industry). The Results page reports the share removed.</li>
        <li>Each detection gets a local solar date and time, so a month means the same hours everywhere.</li>
        <li>Counts are kept per platform. Platforms are never added together.</li>
      </ol>

      <h2>Harmonization</h2>
      <p>For each calibration region (Punjab, Pakistan; Punjab, India; the rest of the coverage box) and calendar month, the factor is the ratio of S-NPP to Aqua totals on days both observed, over {span(p.calib_years)}. Uncertainty comes from a bootstrap over years (B = {p.bootstrap_b}).</p>
      <ul>
        <li>Before {cal.snpp_first}: Aqua × factor.</li>
        <li>{cal.snpp_first} to {cal.snpp_last}: S-NPP as observed.</li>
        <li>After {cal.snpp_last}: NOAA-20 × its own factor (not yet in the data). <strong>NOAA-20 factor not held-out validated</strong>: it is fit on 2019–2025, which overlaps the held-out years (D-038).</li>
      </ul>
      <p>The years {span(p.heldout_years)} never touch calibration; they are the out-of-time test.</p>
      {aquaFactors.length > 0 ? (
        <p data-testid="factor-note">
          <strong>How large are the factors?</strong> One Aqua detection stands for {fMin.toFixed(1)} to {fMax.toFixed(1)} S-NPP detections across the three regions and twelve months (median {fMed.toFixed(1)}). S-NPP&rsquo;s 375 m pixels pick up more, smaller fires than MODIS&rsquo;s 1 km pixels (Schroeder et al. 2014), so the factor is above 1 in {nAbove} of {aquaFactors.length} region-months. Where Aqua counts are small the factor is large and its 95% interval is wide, so read MODIS-era months (before {cal.snpp_first.slice(0, 4)}) in those seasons as indicative, not exact.
        </p>
      ) : null}

      <h2>Drawn boxes and circles</h2>
      <p>District and region series are computed by the pipeline. For a drawn box or a point and radius, your browser reads the hotspot tiles with DuckDB-WASM and applies the same splice: each Aqua detection is scaled by the factor of its calibration region, found by testing the point against simplified Punjab outlines (tolerance {cal.polygon_simplify_tolerance_deg}°). Detections within that tolerance of the Punjab border may get the neighbouring region&rsquo;s factor.</p>

      <h2>The current-month card</h2>
      <p>&ldquo;Current fire&rdquo; is read at month level: the card compares one month with the median of the same calendar month in earlier complete years. This build has no near-real-time feed, so the card shows the latest complete month in the archive and says so. A future server function can add NOAA-20 near-real-time counts, labelled &ldquo;{c.nrt_label}&rdquo;; its key will live only on the server.</p>

      <p>The card shows two medians for the same month. <strong>All years</strong> uses every complete year of the baseline; the ratio printed next to the headline figure uses this one (it is the only median defined for NOAA-20). <strong>Excluding years we flag</strong> leaves out the caution years of the area&rsquo;s calibration region (see the reliability flags); for a drawn box or radius it leaves out the union of the caution years of every calibration region the area overlaps, so a flagged year cannot pull its own yardstick. NOAA-20 has no such second median because too few years would remain. The live current month appears on the card when the near-real-time service is switched on at launch; until then the label stays &ldquo;Latest available month, not live&rdquo;. Ratios are shown to two significant figures.</p>
      <p><strong>Critical period, also for drawn areas.</strong> For a drawn area the browser applies the same month-level rules as the pipeline does for districts: the typical value of a calendar month is the median over the baseline years with the caution years left out (at least five such complete years); critical months are those at or above the 75th percentile of the twelve typical values and above zero; onset and end are the ends of the run of critical months around the peak; this year versus typical uses the latest complete month. The pipeline&rsquo;s version is the reference, and an automated test checks that the browser code gives the same months, onset, peak and end, and typical values within 0.1 (rounding), on two real districts.</p>

      <h2>Critical periods</h2>
      <p>For each district and region the Explorer shows a critical period at month level, not daily, because the data are monthly. The typical level of a calendar month is the median of its complete harmonized values over the baseline years, with the area&rsquo;s caution years left out; a month needs at least five such years. <strong>Critical months</strong> are the months whose typical level is at or above the 75th percentile of the twelve typical monthly levels (the top quarter of the year) and above zero. The <strong>peak</strong> is the month with the highest typical level. <strong>Onset</strong> and <strong>end</strong> are the first and last month of the run of consecutive critical months (December joins January) that contains the peak; any other critical months are listed separately. <strong>This year vs typical</strong> compares the latest complete month in the data with the typical level of that calendar month. Drawn areas have no critical-period block.</p>

      <h2>Limitations</h2>
      <ul>
        <li>Hotspots count fire pixels at overpass time, not area burned or emissions. Cloud, smoke and overpass time change what is seen.</li>
        <li>The factors assume the Aqua / S-NPP ratio is stable. T2 tests this; Aqua&rsquo;s later overpass after its orbit drift makes recent years hard to evaluate.</li>
        <li>The two Punjab boundaries come from different sources and overlap slightly at the border. Each is reported on its own; Blind Spot never shows a combined total for both.</li>
        <li>District boundaries are simplified for the map; district series use the original boundaries.</li>
        <li>The hotspot CSV is capped at {c.csv_row_cap.toLocaleString("en-GB")} rows.</li>
        <li>{c.scope}</li>
      </ul>
    </main>
  );
}
