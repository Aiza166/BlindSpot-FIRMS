import type { Metadata } from "next";
import "@fontsource/newsreader/400.css";
import "@fontsource/newsreader/500.css";
import "@fontsource-variable/instrument-sans";
import "./globals.css";
import { Masthead } from "@/components/Masthead";
import { readData } from "@/lib/server";
import type { Constants } from "@/lib/types";

export const metadata: Metadata = {
  title: "Blind Spot",
  description: "A harmonized MODIS + VIIRS burning calendar for Pakistan and northern India.",
};

// Runs before paint so the stored theme choice does not flash.
const themeScript = `try{var t=localStorage.getItem("bs-theme");if(t==="light"||t==="dark")document.documentElement.dataset.theme=t}catch(e){}`;

export default function RootLayout({ children }: { children: React.ReactNode }) {
  const c = readData<Constants>("constants.json");
  return (
    <html lang="en" suppressHydrationWarning>
      <head>
        <script dangerouslySetInnerHTML={{ __html: themeScript }} />
      </head>
      <body>
        <a className="skip" href="#main">Skip to content</a>
        <Masthead scope={c.scope} />
        {children}
      </body>
    </html>
  );
}
