import { useState, useCallback } from "react";
import { Routes, Route } from "react-router-dom";
import { NavBar } from "./components/layout/NavBar";
import { SearchPalette } from "./components/layout/SearchPalette";
import { StockSheet } from "./components/stock/StockSheet";
import { Home } from "./pages/Home";
import { Universe } from "./pages/Universe";
import { Evidence } from "./pages/Evidence";
import { Methodology } from "./pages/Methodology";
import { useScreenData } from "./hooks/useScreenData";

export function App() {
  const { data } = useScreenData();
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
        <Routes>
          <Route path="/" element={<Home />} />
          <Route path="/universe" element={<Universe />} />
          <Route path="/evidence" element={<Evidence />} />
          <Route path="/methodology" element={<Methodology />} />
        </Routes>
      </main>

      {/* Global search palette (Cmd+K from any page) */}
      <SearchPalette onSelect={handleSearchSelect} />

      {/* Stock deep dive from global search */}
      {searchStock && (
        <StockSheet stock={searchStock} allStocks={data?.stocks} onClose={() => setSearchTicker(null)} />
      )}
    </div>
  );
}
