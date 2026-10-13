import { useEffect, useRef } from "react";
import {
  AlignLeft, ArrowRight, BookOpen, ChevronDown, FileCheck2, FileText, FlaskConical, ImageIcon, Info, KeyRound, Layers,
  Lock, MessageSquareText, Plus, Search, SendHorizontal, ShieldCheck, ShieldQuestion, UploadCloud, UserPlus, Users, Wrench,
  House, Boxes, Activity, Settings,
} from "lucide-react";
import SmartLabOrb from "../components/SmartLabOrb";
import { SiteFooter, SiteFrame, SiteNav } from "./SiteChrome";
import useReveal from "./useReveal";

// Only features that exist in the app today.
const FEATURES = [
  { icon: FileText, title: "Cited answers from your documents", body: "Ask across your SOPs, manuals and safety documents. Every answer cites the document and page it came from." },
  { icon: ImageIcon, title: "Image analysis", body: "Add a photo of an equipment display or sample and get the matching SOP passages and recorded fixes." },
  { icon: FlaskConical, title: "Reagent lookup", body: "Check stock, storage location, expiry and hazards, or simply ask where something is kept." },
  { icon: BookOpen, title: "Scientific literature search", body: "Search published research on Europe PMC and see which of your own SOPs relate to it." },
  { icon: ShieldCheck, title: "Safety resources", body: "Find safety documents, recorded hazard classes and the emergency contacts your institution has entered." },
];

const STEPS = [
  { icon: UploadCloud, title: "Upload your documents", body: "Add SOPs, manuals and safety documents as text-based PDFs." },
  { icon: MessageSquareText, title: "Ask in plain language", body: "Type a question, attach a photo of a display, or search for a reagent." },
  { icon: FileCheck2, title: "Get cited answers you can verify", body: "Open the cited page with the passage highlighted and check it yourself." },
];

// Statements describe what the software actually does; no certifications are claimed.
const TRUST = [
  { icon: Lock, title: "Protected sign-in", body: "Passwords are stored only as salted hashes and sessions use httpOnly cookies. Serve SmartLab over HTTPS to encrypt every connection." },
  { icon: Users, title: "Accounts and roles", body: "Every page and API request requires signing in, and each account has an admin or member role." },
  { icon: FileText, title: "Citations for every answer", body: "Answers point to the exact document page, and unapproved or outdated sources are flagged." },
  { icon: ShieldQuestion, title: "Honest about gaps", body: "When your documents don't cover a question, SmartLab says so instead of guessing." },
];

/** Static, non-interactive mock of the app's home screen built from the real design tokens. */
function ProductPreview() {
  const railIcons = [House, MessageSquareText, FileText, Boxes, BookOpen, ShieldCheck, Wrench, Layers];
  return (
    <figure className="mx-auto w-full max-w-4xl">
      <div aria-hidden="true" inert="" className="pointer-events-none select-none overflow-hidden rounded-2xl border border-line bg-surface shadow-prompt">
        <div className="flex">
          <div className="hidden w-12 shrink-0 flex-col items-center gap-2 border-r border-line py-3 sm:flex">
            <FlaskConical className="mb-1 h-5 w-5 text-accent" strokeWidth={1.8} />
            {railIcons.map((Icon, i) => (
              <span key={i} className={`relative flex h-8 w-8 items-center justify-center rounded-lg ${i === 0 ? "bg-subtle text-accent" : "text-faint"}`}>
                {i === 0 && <span className="absolute -left-2 top-1.5 h-5 w-[3px] rounded-r-full bg-accent" />}
                <Icon className="h-4 w-4" strokeWidth={1.6} />
              </span>
            ))}
            <span className="mt-auto" />
            <Activity className="h-4 w-4 text-faint" strokeWidth={1.6} />
            <Settings className="h-4 w-4 text-faint" strokeWidth={1.6} />
          </div>
          <div className="min-w-0 flex-1">
            <div className="flex h-11 items-center gap-1.5 border-b border-line px-3">
              <span className="pill h-7 text-xs"><FileText />All documents<ChevronDown /></span>
              <span className="pill hidden h-7 text-xs sm:inline-flex"><AlignLeft />Concise<ChevronDown /></span>
              <span className="mx-auto hidden items-center gap-1 text-xs font-medium text-ink md:flex"><Plus className="h-3.5 w-3.5" />Collection<ChevronDown className="h-3.5 w-3.5 text-muted" /></span>
              <span className="pill ml-auto hidden h-7 text-xs sm:inline-flex"><Search />Search thread</span>
              <span className="pill hidden h-7 text-xs lg:inline-flex"><UserPlus />Invite</span>
              <span className="btn-dark h-7 text-xs"><Plus className="h-3.5 w-3.5" />New thread</span>
            </div>
            <div className="flex flex-col items-center bg-canvas px-4 pb-10 pt-8 sm:pb-12 sm:pt-10">
              <SmartLabOrb size={46} />
              <p className="mt-4 font-serif text-[clamp(1.5rem,3vw,2.1rem)] font-medium leading-tight text-ink">Good afternoon, Alex</p>
              <p className="mt-1 font-serif text-[clamp(1.05rem,2vw,1.4rem)] text-muted">What are you cooking <span className="gradient-text">today</span>?</p>
              <div className="mt-6 flex w-full max-w-xl items-center gap-2 rounded-2xl border border-line bg-surface p-1.5 shadow-prompt">
                <span className="flex h-8 w-8 items-center justify-center rounded-full"><Plus className="h-4 w-4" strokeWidth={1.6} /></span>
                <span className="min-w-0 flex-1 truncate text-sm text-faint">Ask about a procedure, document, experiment, or reagent...</span>
                <span className="hidden items-center gap-1.5 text-xs font-medium text-accent-strong sm:flex">
                  Citations<span className="switch" aria-checked="true"><span className="switch-knob" /></span>
                </span>
                <span className="flex h-8 w-8 items-center justify-center rounded-full bg-primary text-white"><SendHorizontal className="h-3.5 w-3.5" /></span>
              </div>
            </div>
          </div>
        </div>
      </div>
      <figcaption className="sr-only">Preview of the SmartLab AI home screen: a greeting and a question box for asking about your lab's documents.</figcaption>
    </figure>
  );
}

function SectionHeading({ id, title, children, center = false }) {
  return (
    <div className={center ? "mx-auto max-w-2xl text-center" : "max-w-2xl"}>
      <h2 id={id} tabIndex={-1} className="scroll-mt-24 outline-none font-serif text-[clamp(1.6rem,3vw,2.25rem)] font-medium leading-tight text-ink">{title}</h2>
      {children && <p className="mt-2 text-[0.9375rem] text-muted">{children}</p>}
    </div>
  );
}

export default function LandingPage({ account = null }) {
  const rootRef = useRef(null);
  useReveal(rootRef);
  useEffect(() => {
    document.title = "SmartLab AI · Answers from your lab's documents, with citations";
    window.scrollTo(0, 0);
  }, []);

  return (
    <SiteFrame>
      <SiteNav onLanding account={account} />
      <main id="site-main" tabIndex={-1} ref={rootRef} className="outline-none">
        {/* Hero */}
        <section aria-labelledby="hero-title" className="px-4 pb-16 pt-14 sm:px-6 sm:pt-20">
          <div className="mx-auto flex max-w-3xl flex-col items-center text-center">
            <SmartLabOrb size={60} />
            <h1 id="hero-title" className="mt-7 font-serif text-[clamp(2.2rem,5vw,3.6rem)] font-medium leading-[1.08] tracking-[-0.015em] text-ink">
              Your lab&rsquo;s knowledge,<br className="hidden sm:block" /> with the evidence behind <span className="gradient-text">every answer.</span>
            </h1>
            <p className="mt-5 max-w-xl text-base leading-7 text-muted">
              Ask questions across your SOPs, manuals, reagents and safety documents. Get clear answers with cited sources you can check.
            </p>
            <div className="mt-7 flex flex-wrap justify-center gap-2.5">
              {account ? (
                <a href="#/overview" className="btn-primary h-10 px-4">Open SmartLab <ArrowRight className="h-4 w-4" aria-hidden="true" /></a>
              ) : (
                <>
                  <a href="#/signup" className="btn-primary h-10 px-4">Get started <ArrowRight className="h-4 w-4" aria-hidden="true" /></a>
                  <a href="#/login" className="btn-secondary h-10 px-4">Log in</a>
                </>
              )}
            </div>
          </div>
          <div className="mt-14" data-reveal><ProductPreview /></div>
        </section>

        {/* Features */}
        <section aria-labelledby="features" className="scroll-mt-20 border-t border-line bg-canvas px-4 py-16 sm:px-6">
          <div className="mx-auto max-w-6xl">
            <div data-reveal><SectionHeading id="features" center title="Features built for working labs">Find the information you need, when you need it.</SectionHeading></div>
            <ul className="mt-10 grid grid-cols-1 gap-3 sm:grid-cols-2 lg:grid-cols-5">
              {FEATURES.map((f, i) => (
                <li key={f.title} data-reveal style={{ transitionDelay: `${i * 60}ms` }} className="card p-5">
                  <span className="flex h-9 w-9 items-center justify-center rounded-lg bg-accent-soft"><f.icon className="h-[18px] w-[18px] text-accent" strokeWidth={1.6} aria-hidden="true" /></span>
                  <h3 className="mt-4 text-sm font-semibold text-ink">{f.title}</h3>
                  <p className="mt-1.5 text-[0.8125rem] leading-relaxed text-muted">{f.body}</p>
                </li>
              ))}
            </ul>
          </div>
        </section>

        {/* How it works */}
        <section aria-labelledby="how-it-works" className="scroll-mt-20 px-4 py-16 sm:px-6">
          <div className="mx-auto max-w-6xl">
            <div data-reveal><SectionHeading id="how-it-works" title="How it works">From your documents to trusted answers in three steps.</SectionHeading></div>
            <ol className="mt-10 grid grid-cols-1 gap-3 md:grid-cols-3">
              {STEPS.map((s, i) => (
                <li key={s.title} data-reveal style={{ transitionDelay: `${i * 80}ms` }} className="relative">
                  <div className="card flex h-full items-start gap-4 p-5">
                    <span className="flex h-7 w-7 shrink-0 items-center justify-center rounded-full bg-accent text-xs font-semibold text-white" aria-hidden="true">{i + 1}</span>
                    <div>
                      <h3 className="flex items-center gap-2 text-sm font-semibold text-ink"><span className="sr-only">Step {i + 1}: </span><s.icon className="h-4 w-4 text-accent" strokeWidth={1.6} aria-hidden="true" />{s.title}</h3>
                      <p className="mt-1.5 text-[0.8125rem] leading-relaxed text-muted">{s.body}</p>
                    </div>
                  </div>
                  {i < STEPS.length - 1 && <ArrowRight className="absolute -right-3 top-1/2 z-10 hidden h-4 w-4 -translate-y-1/2 text-faint md:block" aria-hidden="true" />}
                </li>
              ))}
            </ol>
          </div>
        </section>

        {/* Security and trust */}
        <section aria-labelledby="security" className="scroll-mt-20 border-t border-line bg-canvas px-4 py-16 sm:px-6">
          <div className="mx-auto max-w-6xl">
            <div data-reveal><SectionHeading id="security" title="Security and trust">Your data, your lab, in your control.</SectionHeading></div>
            <ul className="mt-10 grid grid-cols-1 gap-3 sm:grid-cols-2 lg:grid-cols-4">
              {TRUST.map((t, i) => (
                <li key={t.title} data-reveal style={{ transitionDelay: `${i * 60}ms` }} className="flex gap-3 rounded-xl border border-line bg-surface p-4">
                  <t.icon className="mt-0.5 h-[18px] w-[18px] shrink-0 text-accent" strokeWidth={1.6} aria-hidden="true" />
                  <div>
                    <h3 className="text-sm font-semibold text-ink">{t.title}</h3>
                    <p className="mt-1 text-[0.8125rem] leading-relaxed text-muted">{t.body}</p>
                  </div>
                </li>
              ))}
            </ul>
            <p data-reveal className="mt-6 flex items-start gap-2.5 rounded-xl border border-accent/20 bg-accent-soft px-4 py-3 text-sm text-ink">
              <Info className="mt-0.5 h-4 w-4 shrink-0 text-accent-strong" aria-hidden="true" />
              SmartLab AI supports decisions; it does not replace your lab supervisor or safety officer.
            </p>
          </div>
        </section>

        {/* Closing call to action */}
        {!account && (
          <section aria-labelledby="cta" className="px-4 py-16 text-center sm:px-6">
            <div data-reveal className="mx-auto max-w-xl">
              <KeyRound className="mx-auto h-5 w-5 text-accent" strokeWidth={1.6} aria-hidden="true" />
              <h2 id="cta" className="mt-3 font-serif text-[clamp(1.5rem,3vw,2rem)] font-medium text-ink">Start with your own documents</h2>
              <p className="mt-2 text-[0.9375rem] text-muted">Create an account, upload an SOP, and ask your first question.</p>
              <div className="mt-6 flex flex-wrap justify-center gap-2.5">
                <a href="#/signup" className="btn-primary h-10 px-4">Get started <ArrowRight className="h-4 w-4" aria-hidden="true" /></a>
                <a href="#/login" className="btn-secondary h-10 px-4">Log in</a>
              </div>
            </div>
          </section>
        )}
      </main>
      <SiteFooter />
    </SiteFrame>
  );
}
