import { NavLink } from "react-router-dom";
import { RunScreener } from "./RunScreener";

const links = [
  { to: "/", label: "Home" },
  { to: "/universe", label: "Universe" },
  { to: "/evidence", label: "Evidence" },
  { to: "/methodology", label: "How It Works" },
];

export function NavBar() {
  return (
    <nav className="sticky top-0 z-50 flex h-14 items-center border-b px-8"
         style={{ backgroundColor: "var(--color-surface-0)", borderColor: "var(--color-border)" }}>
      <NavLink to="/" className="font-mono text-base font-medium tracking-widest mr-10"
               style={{ color: "var(--color-text-primary)" }}>
        ASSAY
      </NavLink>
      <div className="flex gap-6 flex-1">
        {links.map((l) => (
          <NavLink
            key={l.to}
            to={l.to}
            end={l.to === "/"}
            className={({ isActive }) =>
              `text-[13px] pb-0.5 transition-colors duration-150 ${
                isActive ? "border-b-2 font-medium" : "hover:opacity-80"
              }`
            }
            style={({ isActive }) => ({
              color: isActive ? "var(--color-text-primary)" : "var(--color-text-secondary)",
              borderColor: isActive ? "var(--color-text-primary)" : "transparent",
            })}
          >
            {l.label}
          </NavLink>
        ))}
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
