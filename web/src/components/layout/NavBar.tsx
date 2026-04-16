import { NavLink, useLocation } from "react-router-dom";
import { useEffect, useLayoutEffect, useRef, useState } from "react";
import { RunScreener } from "./RunScreener";

const links = [
  { to: "/", label: "Home" },
  { to: "/universe", label: "Universe" },
  { to: "/evidence", label: "Evidence" },
  { to: "/methodology", label: "How It Works" },
];

function matchesLink(pathname: string, to: string): boolean {
  if (to === "/") return pathname === "/";
  return pathname === to || pathname.startsWith(to + "/");
}

export function NavBar() {
  const location = useLocation();
  const containerRef = useRef<HTMLDivElement>(null);
  const [indicator, setIndicator] = useState<{ left: number; width: number } | null>(null);
  const [hasMoved, setHasMoved] = useState(false);

  useLayoutEffect(() => {
    if (!containerRef.current) return;
    const activeIdx = links.findIndex((l) => matchesLink(location.pathname, l.to));
    if (activeIdx < 0) {
      setIndicator(null);
      return;
    }
    const active = containerRef.current.children[activeIdx] as HTMLElement | undefined;
    if (!active) return;
    const containerRect = containerRef.current.getBoundingClientRect();
    const rect = active.getBoundingClientRect();
    setIndicator({ left: rect.left - containerRect.left, width: rect.width });
  }, [location.pathname]);

  // After first position, enable transitions (prevents initial mount slide-from-0)
  useEffect(() => {
    if (indicator && !hasMoved) {
      const t = setTimeout(() => setHasMoved(true), 50);
      return () => clearTimeout(t);
    }
  }, [indicator, hasMoved]);

  return (
    <nav className="sticky top-0 z-50 flex h-14 items-center border-b px-4 sm:px-8"
         style={{ backgroundColor: "var(--color-surface-0)", borderColor: "var(--color-border)" }}>
      <NavLink to="/" className="font-mono text-base font-medium tracking-widest mr-4 sm:mr-10"
               style={{ color: "var(--color-text-primary)" }}>
        ASSAY
      </NavLink>
      <div ref={containerRef} className="relative flex gap-3 sm:gap-6 flex-1 overflow-x-auto h-14 items-center">
        {links.map((l) => (
          <NavLink
            key={l.to}
            to={l.to}
            end={l.to === "/"}
            className={({ isActive }) =>
              `text-[13px] transition-colors duration-150 ${isActive ? "font-medium" : "hover:opacity-80"}`
            }
            style={({ isActive }) => ({
              color: isActive ? "var(--color-text-primary)" : "var(--color-text-secondary)",
            })}
          >
            {l.label}
          </NavLink>
        ))}
        {/* Magic-line indicator — slides between active items */}
        {indicator && (
          <span
            aria-hidden
            className="absolute pointer-events-none"
            style={{
              left: 0,
              bottom: 0,
              height: 2,
              width: indicator.width,
              transform: `translateX(${indicator.left}px)`,
              backgroundColor: "var(--color-text-primary)",
              transition: hasMoved ? "transform 220ms var(--ease-in-out-quart), width 220ms var(--ease-in-out-quart)" : "none",
            }}
          />
        )}
      </div>

      {/* Right side: search hint + run button */}
      <div className="flex items-center gap-4">
        <kbd className="hidden sm:flex items-center gap-1 text-[10px] rounded px-2 py-1 font-mono cursor-pointer hover:opacity-80"
             style={{ backgroundColor: "var(--color-surface-1)", color: "var(--color-text-muted)", border: "1px solid var(--color-border)" }}
             onClick={() => window.dispatchEvent(new KeyboardEvent("keydown", { key: "k", metaKey: true }))}>
          ⌘K
        </kbd>
        <RunScreener onComplete={() => window.location.reload()} />
      </div>
    </nav>
  );
}
