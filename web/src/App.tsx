import { Routes, Route } from "react-router-dom";
import { NavBar } from "./components/layout/NavBar";
import { Home } from "./pages/Home";
import { Universe } from "./pages/Universe";
import { Evidence } from "./pages/Evidence";

export function App() {
  return (
    <div className="min-h-screen" style={{ backgroundColor: "var(--color-surface-0)" }}>
      <NavBar />
      <main className="max-w-7xl mx-auto">
        <Routes>
          <Route path="/" element={<Home />} />
          <Route path="/universe" element={<Universe />} />
          <Route path="/evidence" element={<Evidence />} />
          <Route path="/methodology" element={<Placeholder title="How It Works" />} />
        </Routes>
      </main>
    </div>
  );
}

function Placeholder({ title }: { title: string }) {
  return (
    <div className="flex items-center justify-center min-h-[60vh]">
      <p className="text-lg" style={{ color: "var(--color-text-muted)" }}>
        {title} — coming soon
      </p>
    </div>
  );
}
