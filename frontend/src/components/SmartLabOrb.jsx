import { useEffect, useState } from "react";

/**
 * Decorative glossy orb for the home page. Pure CSS (see .orb-* in index.css); animates only
 * transform and opacity, honours prefers-reduced-motion, and pauses while the tab is hidden.
 * state: "idle" | "focused" | "thinking"
 */
export default function SmartLabOrb({ state = "idle", size = 60 }) {
  const [hidden, setHidden] = useState(() => document.hidden);
  useEffect(() => {
    const on = () => setHidden(document.hidden);
    document.addEventListener("visibilitychange", on);
    return () => document.removeEventListener("visibilitychange", on);
  }, []);

  return (
    <div className="orb" data-state={state} data-paused={hidden || undefined} aria-hidden="true" style={{ "--orb-size": `${size}px` }}>
      <div className="orb-float">
        <div className="orb-glow" />
        <div className="orb-scale">
          <div className="orb-body">
            <div className="orb-light" />
            <div className="orb-shade" />
            <div className="orb-spec" />
            <div className="orb-bright" />
          </div>
        </div>
      </div>
      <div className="orb-ground" />
    </div>
  );
}
