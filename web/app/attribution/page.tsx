import type { Metadata } from "next";
import { Marked, type Tokens } from "marked";
import { readText } from "@/lib/server";

export const metadata: Metadata = { title: "Attribution · Blind Spot" };

const esc = (s: string) => s.replace(/&/g, "&amp;").replace(/</g, "&lt;").replace(/>/g, "&gt;").replace(/"/g, "&quot;");
const SAFE_HREF = /^(https?:|mailto:|\/|#)/i;

// ATTRIBUTION.md is pipeline output. Raw HTML is escaped (never live) and only http(s),
// mailto and same-site links are kept, so an edited file cannot inject script (SECURITY #3, D-038).
const md = new Marked({
  async: false,
  renderer: {
    html: ({ text }: Tokens.HTML | Tokens.Tag) => esc(text),
    link(token: Tokens.Link) {
      if (!SAFE_HREF.test(token.href.trim())) return this.parser.parseInline(token.tokens);
      return false;
    },
    image: ({ text }: Tokens.Image) => esc(text),
  },
});

export default function Attribution() {
  const html = (md.parse(readText("ATTRIBUTION.md")) as string)
    .replace(/<table>/g, '<div class="table-wrap" role="region" aria-label="Boundary licences (scrollable table)" tabindex="0"><table>')
    .replace(/<\/table>/g, "</table></div>");
  return <main id="main" className="page" data-testid="attribution" dangerouslySetInnerHTML={{ __html: html }} />;
}
