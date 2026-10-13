import { useEffect } from "react";

/**
 * Scroll-reveal: elements with [data-reveal] inside `rootRef` fade/slide in once they reach the
 * viewport (opacity + transform only; see .reveal in index.css). Anything already scrolled past
 * (e.g. after a jump to a section) is revealed too, so content is never left hidden. With reduced
 * motion, everything is simply shown.
 */
export default function useReveal(rootRef) {
  useEffect(() => {
    const root = rootRef.current;
    if (!root) return undefined;
    let pending = [...root.querySelectorAll("[data-reveal]")];
    if (window.matchMedia?.("(prefers-reduced-motion: reduce)").matches) {
      pending.forEach((el) => el.classList.add("is-visible"));
      return undefined;
    }
    pending.forEach((el) => el.classList.add("reveal"));

    // Checked directly on scroll (a handful of elements); requestAnimationFrame would stall in background tabs.
    const check = () => {
      const limit = window.innerHeight * 0.92;
      pending = pending.filter((el) => {
        if (el.getBoundingClientRect().top < limit) { el.classList.add("is-visible"); return false; }
        return true;
      });
      if (!pending.length) stop();
    };
    const stop = () => {
      window.removeEventListener("scroll", check);
      window.removeEventListener("resize", check);
    };
    window.addEventListener("scroll", check, { passive: true });
    window.addEventListener("resize", check);
    check();
    return stop;
  }, [rootRef]);
}
