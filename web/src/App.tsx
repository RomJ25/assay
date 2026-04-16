import { useState, useCallback, lazy, Suspense } from "react";
import { Routes, Route, useLocation } from "react-router-dom";
import { NavBar } from "./components/layout/NavBar";
import { SearchPalette } from "./components/layout/SearchPalette";
import { StockSheet } from "./components/stock/StockSheet";
import { Home } from "./pages/Home";
import { useScreenData } from "./hooks/useScreenData";

// Lazy-load secondary pages (reduces initial bundle)
const Universe = lazy(() => import("./pages/Universe").then((m) => ({ default: m.Universe })));
const Evidence = lazy(() => import("./pages/Evidence").then((m) => ({ default: m.Evidence })));
const Methodology = lazy(() => import("./pages/Methodology").then((m) => ({ default: m.Methodology })));

function PageLoader() {
  return (
    <div className="flex items-center justify-center min-h-[60vh]">
      <div className="w-32 h-0.5 rounded-full overflow-hidden" style={{ backgroundColor: "var(--color-surface-2)" }}>
        <div className="h-full rounded-full animate-pulse w-1/3" style={{ backgroundColor: "var(--color-cb)" }} />
      </div>
    </div>
  );
}

export function App() {
  const { data } = useScreenData();
  const location = useLocation();
  const [searchTicker, setSearchTicker] = useState<string | null>(null);

  const handleSearchSelect = useCallback((ticker: string) => {
    setSearchTicker(ticker);
  }, []);

  const searchStock = searchTicker && data
    ? data.stocks.find((s) => s.ticker === searchTicker)
    : null;

  return (
    <div className="min-h-screen" style={{ backgroundColor: "var(--color-surface-0)" }}>
      <NavBar />

      <main className="max-w-7xl mx-auto">
        <Suspense fallback={<PageLoader />}>
          {/* Keyed wrapper — route change triggers fade-up. Subtle, preserves scroll to top naturally. */}
          <div key={location.pathname} className="anim-fade">
            <Routes location={location}>
              <Route path="/" element={<Home />} />
              <Route path="/universe" element={<Universe />} />
              <Route path="/evidence" element={<Evidence />} />
              <Route path="/methodology" element={<Methodology />} />
            </Routes>
          </div>
        </Suspense>
      </main>

      <SearchPalette onSelect={handleSearchSelect} />

      {searchStock && (
        <StockSheet stock={searchStock} allStocks={data?.stocks} onClose={() => setSearchTicker(null)} />
      )}
    </div>
  );
}
