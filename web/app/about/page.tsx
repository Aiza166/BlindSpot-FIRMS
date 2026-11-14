import type { Metadata } from "next";
import { readData } from "@/lib/server";
import type { Constants } from "@/lib/types";

export const metadata: Metadata = { title: "About · Blind Spot" };

export default function About() {
  const c = readData<Constants>("constants.json");
  return (
    <main id="main" className="page">
      <h1>About Blind Spot</h1>
      <p>Blind Spot is a burning calendar for any district or drawn area in Pakistan and northern India, back to 2003. It answers one question: is this month&rsquo;s burning unusual here? It also tests whether the satellite record itself changed underneath that answer.</p>
      <p>Built for the NASA Space Apps Challenge 2026, &ldquo;Harmonization of MODIS and VIIRS Hot Spots&rdquo;. {c.scope}</p>

      <h2>How AI was used</h2>
      <p data-testid="ai-statement">We used Claude Code, with subagents, to help plan the work, write the pipeline and web code, and review it. People on the team decided the research question, the pre-registered tests and thresholds, and every scientific and product choice, and checked the results. Every number in the app is read from the pipeline&rsquo;s output files, not typed by hand.</p>

      <h2>Source and data</h2>
      <p>Fire detections from NASA FIRMS; boundaries from geoBoundaries. See <a href="/attribution/">Attribution</a> for citations and licences.</p>
    </main>
  );
}
