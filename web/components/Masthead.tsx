"use client";
import Link from "next/link";
import { usePathname } from "next/navigation";
import { useEffect, useState } from "react";

const LINKS = [
  { href: "/", label: "Explorer" },
  { href: "/use-case/", label: "Use case" },
  { href: "/results/", label: "Results" },
  { href: "/methods/", label: "Methods" },
  { href: "/about/", label: "About" },
  { href: "/attribution/", label: "Attribution" },
];

type Theme = "light" | "dark";

function systemTheme(): Theme {
  return window.matchMedia("(prefers-color-scheme: dark)").matches ? "dark" : "light";
}

export function Masthead({ scope }: { scope: string }) {
  const path = usePathname();
  const [theme, setTheme] = useState<Theme | null>(null);
  useEffect(() => {
    const t = document.documentElement.dataset.theme;
    setTheme(t === "light" || t === "dark" ? t : systemTheme());
  }, []);
  const toggle = () => {
    const next: Theme = theme === "dark" ? "light" : "dark";
    document.documentElement.dataset.theme = next;
    try { localStorage.setItem("bs-theme", next); } catch { /* storage may be blocked */ }
    setTheme(next);
  };
  return (
    <header className="mast">
      <Link href="/" className="wordmark"><span aria-hidden="true" />Blind Spot</Link>
      <nav className="nav" aria-label="Main">
        {LINKS.map((l) => (
          <Link key={l.href} href={l.href} aria-current={path === l.href || path === l.href.replace(/\/$/, "") ? "page" : undefined}>{l.label}</Link>
        ))}
        <button type="button" className="theme-btn" onClick={toggle} aria-label={theme ? `Switch to ${theme === "dark" ? "light" : "dark"} theme` : "Switch theme"}>
          {theme === "dark" ? "Light" : "Dark"}
        </button>
      </nav>
      <p className="scope" data-testid="scope">{scope}</p>
    </header>
  );
}
