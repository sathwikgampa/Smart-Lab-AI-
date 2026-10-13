import { lazy, Suspense, useEffect, useRef, useState } from "react";
import { AppProvider, useApp } from "./context/AppContext";
import AppShell, { ALL_NAV } from "./components/AppShell";
import EvidencePanel from "./components/EvidencePanel";
import { Drawer, Page, SkeletonRows } from "./components/ui";
import { useRoute } from "./lib/router";

// Overview (home) and Ask share one component instance so a question asked on the home page
// continues in place when the URL changes to its thread.
const AskView = lazy(() => import("./views/AskView"));
const VIEWS = {
  overview: AskView,
  ask: AskView,
  documents: lazy(() => import("./views/DocumentsView")),
  reagents: lazy(() => import("./views/ReagentsView")),
  literature: lazy(() => import("./views/LiteratureView")),
  safety: lazy(() => import("./views/SafetyView")),
  activity: lazy(() => import("./views/ActivityView")),
  settings: lazy(() => import("./views/SettingsView")),
  search: lazy(() => import("./views/SearchView")),
  troubleshooting: lazy(() => import("./views/TroubleshootingView")),
  experiments: lazy(() => import("./views/ExperimentsView")),
  data: lazy(() => import("./views/DataView")),
  collaboration: lazy(() => import("./views/CollaborationView")),
  simulation: lazy(() => import("./views/SimulationView")),
  training: lazy(() => import("./views/LabTourView")),
};

function useIsWide() {
  const query = "(min-width: 1280px)";
  const [wide, setWide] = useState(() => window.matchMedia(query).matches);
  useEffect(() => {
    const mq = window.matchMedia(query);
    const on = () => setWide(mq.matches);
    mq.addEventListener("change", on);
    return () => mq.removeEventListener("change", on);
  }, []);
  return wide;
}

function Shell({ route }) {
  const { evidence, closeEvidence } = useApp();
  const wide = useIsWide();
  const id = VIEWS[route.path[0]] ? route.path[0] : null;

  // A source belongs to the page/conversation it was opened from; close it when that changes.
  const routeKey = route.path.join("/");
  const lastKey = useRef(routeKey);
  useEffect(() => {
    const prev = lastKey.current;
    lastKey.current = routeKey;
    const sameAskThread = (prev === "ask" || prev === "overview") && routeKey.startsWith("ask/"); // new conversation just got its id
    const sameDocuments = prev.startsWith("documents") && routeKey.startsWith("documents");
    if (prev !== routeKey && !sameAskThread && !sameDocuments) closeEvidence();
  }, [routeKey, closeEvidence]);

  const View = id ? VIEWS[id] : null;
  const label = ALL_NAV.find((n) => n.id === id)?.label ?? "Not found";
  // Evidence: docked column on wide screens, overlay drawer elsewhere. Closed until a citation is opened.
  const aside = evidence && wide ? (
    <aside className="w-[24rem] shrink-0 border-l border-line bg-surface" aria-label="Source evidence"><EvidencePanel onClose={closeEvidence} /></aside>
  ) : null;

  return (
    <AppShell current={id} route={route} title={label} aside={aside}>
      <Suspense fallback={<Page><SkeletonRows rows={6} /></Page>}>
        {View ? <View route={route} /> : (
          <Page><h1 className="text-lg font-semibold">Page not found</h1><p className="mt-1 text-muted">This address does not match any page. <a className="link" href="#/overview">Go to Overview</a></p></Page>
        )}
      </Suspense>
      {evidence && !wide && (
        <Drawer open bare onClose={closeEvidence} title="Source evidence" width="sm:w-[28rem]">
          <EvidencePanel onClose={closeEvidence} />
        </Drawer>
      )}
    </AppShell>
  );
}

// Public pages render outside the app shell. "" is the landing page at "/".
const LandingPage = lazy(() => import("./site/LandingPage"));
const StaticPage = lazy(() => import("./site/StaticPage"));
const AuthPages = {
  login: lazy(() => import("./site/AuthPages").then((m) => ({ default: m.LoginPage }))),
  signup: lazy(() => import("./site/AuthPages").then((m) => ({ default: m.SignupPage }))),
  forgot: lazy(() => import("./site/AuthPages").then((m) => ({ default: m.ForgotPasswordPage }))),
  reset: lazy(() => import("./site/AuthPages").then((m) => ({ default: m.ResetPasswordPage }))),
};
const PUBLIC = {
  "": () => <LandingPage />,
  privacy: () => <StaticPage page="privacy" />,
  terms: () => <StaticPage page="terms" />,
  contact: () => <StaticPage page="contact" />,
  login: (route) => <AuthPages.login route={route} />,
  signup: () => <AuthPages.signup />,
  "forgot-password": () => <AuthPages.forgot />,
  "reset-password": (route) => <AuthPages.reset route={route} />,
};

function Root() {
  const route = useRoute();
  const Public = PUBLIC[route.path[0] ?? ""];
  if (Public) return <Suspense fallback={<div className="min-h-full bg-page" />}>{Public(route)}</Suspense>;
  return <Shell route={route} />;
}

export default function App() {
  return (
    <AppProvider>
      <Root />
    </AppProvider>
  );
}
