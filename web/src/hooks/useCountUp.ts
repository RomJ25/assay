import { useEffect, useState } from "react";

// ease-out-expo to match --ease-out-expo in index.css
function easeOutExpo(t: number): number {
  return t === 1 ? 1 : 1 - Math.pow(2, -10 * t);
}

function prefersReducedMotion(): boolean {
  if (typeof window === "undefined") return false;
  return window.matchMedia("(prefers-reduced-motion: reduce)").matches;
}

/**
 * Count from 0 to `target` over `duration` ms using ease-out-expo.
 * Respects prefers-reduced-motion (returns target immediately).
 * Returns the interpolated number, re-triggering when `target` changes.
 */
export function useCountUp(target: number, duration = 900, delay = 0): number {
  const [value, setValue] = useState(() => (prefersReducedMotion() ? target : 0));

  useEffect(() => {
    if (prefersReducedMotion()) {
      setValue(target);
      return;
    }
    if (!Number.isFinite(target)) {
      setValue(target);
      return;
    }

    let rafId = 0;
    let startTs: number | null = null;
    const from = 0;
    const to = target;

    const tick = (ts: number) => {
      if (startTs === null) startTs = ts;
      const elapsed = ts - startTs - delay;
      if (elapsed < 0) {
        rafId = requestAnimationFrame(tick);
        return;
      }
      const t = Math.min(elapsed / duration, 1);
      const eased = easeOutExpo(t);
      setValue(from + (to - from) * eased);
      if (t < 1) {
        rafId = requestAnimationFrame(tick);
      }
    };

    // Reset to 0 before starting to handle re-triggers
    setValue(0);
    rafId = requestAnimationFrame(tick);

    return () => cancelAnimationFrame(rafId);
  }, [target, duration, delay]);

  return value;
}
