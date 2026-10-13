import { useEffect, useState } from "react";
import { FlaskConical, Menu, X } from "lucide-react";

export const NAV_SECTIONS = [
  { id: "features", label: "Features" },
  { id: "how-it-works", label: "How it works" },
  { id: "security", label: "Security" },
];

/** Smooth-scroll to a landing section (hash links would collide with the hash router). */
export function scrollToSection(id) {
  const el = document.getElementById(id);
  if (!el) return false;
  const reduce = window.matchMedia?.("(prefers-reduced-motion: reduce)").matches;
  el.scrollIntoView({ behavior: reduce ? "auto" : "smooth", block: "start" });
  el.focus({ preventScroll: true });
  return true;
}

export function Logo({ href = "#/" }) {
  return (
    <a href={href} className="flex items-center gap-2 rounded-md text-[0.9375rem] font-semibold text-ink">
      <FlaskConical className="h-5 w-5 text-accent" strokeWidth={1.8} aria-hidden="true" />
      SmartLab AI
    </a>
  );
}

/**
 * Sticky top navigation for public pages. Section links scroll on the landing page and
 * navigate there first from other public pages. `account` swaps the auth buttons for "Open app".
 */
export function SiteNav({ onLanding = false, account = null }) {
  const [open, setOpen] = useState(false);
  useEffect(() => {
    if (!open) return undefined;
    const onKey = (e) => { if (e.key === "Escape") setOpen(false); };
    document.addEventListener("keydown", onKey);
    return () => document.removeEventListener("keydown", onKey);
  }, [open]);

  const go = (id) => {
    setOpen(false);
    if (onLanding) scrollToSection(id);
    else { window.location.hash = "#/"; setTimeout(() => scrollToSection(id), 120); }
  };
  const actions = account ? (
    <a href="#/overview" className="btn-primary h-9">Open app</a>
  ) : (
    <>
      <a href="#/login" className="btn-secondary h-9">Log in</a>
      <a href="#/signup" className="btn-primary h-9">Get started</a>
    </>
  );

  return (
    <header className="sticky top-0 z-30 rounded-t-frame border-b border-line bg-surface/90 backdrop-blur supports-[backdrop-filter]:bg-surface/80">
      <div className="mx-auto flex h-16 max-w-6xl items-center gap-4 px-4 sm:px-6">
        <Logo />
        <nav aria-label="Site" className="mx-auto hidden items-center gap-1 md:flex">
          {NAV_SECTIONS.map((s) => (
            <button key={s.id} type="button" onClick={() => go(s.id)} className="rounded-md px-3 py-1.5 text-sm text-muted hover:bg-subtle hover:text-ink">{s.label}</button>
          ))}
        </nav>
        <div className="ml-auto hidden items-center gap-2 md:flex">{actions}</div>
        <button type="button" className="btn-ghost btn-icon ml-auto md:hidden" aria-expanded={open} aria-controls="site-menu"
          aria-label={open ? "Close menu" : "Open menu"} onClick={() => setOpen((o) => !o)}>
          {open ? <X className="h-5 w-5" /> : <Menu className="h-5 w-5" />}
        </button>
      </div>
      {open && (
        <div id="site-menu" className="border-t border-line px-4 pb-4 pt-2 md:hidden">
          <nav aria-label="Site" className="flex flex-col">
            {NAV_SECTIONS.map((s) => (
              <button key={s.id} type="button" onClick={() => go(s.id)} className="rounded-md px-2 py-2.5 text-left text-sm text-ink hover:bg-subtle">{s.label}</button>
            ))}
          </nav>
          <div className="mt-3 grid grid-cols-2 gap-2 [&>*]:w-full">{actions}</div>
        </div>
      )}
    </header>
  );
}

export function SiteFooter() {
  return (
    <footer className="border-t border-line">
      <div className="mx-auto flex max-w-6xl flex-col gap-4 px-4 py-8 text-sm sm:flex-row sm:items-center sm:px-6">
        <Logo />
        <nav aria-label="Legal" className="flex gap-5 sm:mx-auto">
          <a href="#/privacy" className="text-muted hover:text-ink">Privacy</a>
          <a href="#/terms" className="text-muted hover:text-ink">Terms</a>
          <a href="#/contact" className="text-muted hover:text-ink">Contact</a>
        </nav>
        <p className="text-xs text-muted">© {new Date().getFullYear()} SmartLab AI</p>
      </div>
    </footer>
  );
}

/** Moves focus to the main region without touching the URL (a "#id" link would change the hash route). */
export function SkipLink({ target }) {
  return (
    <a href={`#${target}`} onClick={(e) => { e.preventDefault(); document.getElementById(target)?.focus(); }}
      className="sr-only focus:not-sr-only focus:fixed focus:left-2 focus:top-2 focus:z-[70] focus:rounded focus:bg-surface focus:px-3 focus:py-2">
      Skip to content
    </a>
  );
}

/** Public page frame: light-gray page with a large rounded white frame, as in the app shell. */
export function SiteFrame({ children }) {
  return (
    <div className="min-h-full bg-page p-0 sm:p-3 lg:p-4">
      <SkipLink target="site-main" />
      <div className="mx-auto max-w-[1320px] border-line bg-surface shadow-panel sm:rounded-frame sm:border">{children}</div>
    </div>
  );
}
