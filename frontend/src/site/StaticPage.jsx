import { useEffect } from "react";
import { ArrowLeft } from "lucide-react";
import { SiteFooter, SiteFrame, SiteNav } from "./SiteChrome";

// Placeholder legal/contact pages. They say plainly that the operator must supply the real text.
const PAGES = {
  privacy: {
    title: "Privacy",
    body: [
      "This is a placeholder. The organization that runs this SmartLab AI installation is responsible for publishing its privacy policy here.",
      "What the software itself stores: your account details (name, email, organization and a salted password hash), the documents you upload, your questions and answers, and an audit log of changes. If an AI service is configured, question text and the cited passages are sent to it to write answers.",
    ],
  },
  terms: {
    title: "Terms",
    body: [
      "This is a placeholder. The organization that runs this SmartLab AI installation is responsible for publishing its terms of use here.",
      "SmartLab AI supports decisions; it does not replace your lab supervisor, safety officer or your institution's procedures. Always check the cited pages before acting.",
    ],
  },
  contact: {
    title: "Contact",
    body: [
      "This is a placeholder. For access, account or data questions, contact the administrator of your SmartLab AI installation.",
      "For safety emergencies, follow your institution's emergency procedures. Do not rely on this website.",
    ],
  },
};

export default function StaticPage({ page, account }) {
  const p = PAGES[page];
  useEffect(() => { document.title = `${p.title} · SmartLab AI`; window.scrollTo(0, 0); }, [p.title]);
  return (
    <SiteFrame>
      <SiteNav account={account} />
      <main id="site-main" tabIndex={-1} className="mx-auto max-w-2xl px-4 py-16 outline-none sm:px-6">
        <a href="#/" className="inline-flex items-center gap-1.5 text-sm text-muted hover:text-ink"><ArrowLeft className="h-4 w-4" aria-hidden="true" /> Back to home</a>
        <h1 className="mt-6 font-serif text-4xl font-medium text-ink">{p.title}</h1>
        <div className="mt-6 space-y-4 text-[0.9375rem] leading-7 text-ink">
          {p.body.map((t) => <p key={t}>{t}</p>)}
        </div>
      </main>
      <SiteFooter />
    </SiteFrame>
  );
}
