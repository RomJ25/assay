import { useState, useMemo } from "react";
import { useScreenData } from "../hooks/useScreenData";
import { StockSheet } from "../components/stock/StockSheet";
import { classificationColors } from "../lib/colors";
import type { ScreenStock, Classification } from "../lib/types";

const MATRIX: Classification[][] = [
  ["CONVICTION BUY", "WATCH LIST", "VALUE TRAP"],
  ["QUALITY GROWTH PREMIUM", "HOLD", "AVOID"],
  ["OVERVALUED QUALITY", "OVERVALUED", "AVOID"],
];

const SHORT_LABELS: Record<string, string> = {
  "CONVICTION BUY": "Conviction Buy",
  "QUALITY GROWTH PREMIUM": "Quality Growth",
  "WATCH LIST": "Watch List",
  HOLD: "Hold",
  "OVERVALUED QUALITY": "Overvalued Quality",
  OVERVALUED: "Overvalued",
  "VALUE TRAP": "Value Trap",
  AVOID: "Avoid",
};

export function Universe() {
  const { data, loading, error } = useScreenData();
  const [selectedCell, setSelectedCell] = useState<Classification | null>(null);
  const [selectedTicker, setSelectedTicker] = useState<string | null>(null);
  const [searchQuery, setSearchQuery] = useState("");

  const bucketMap = useMemo(() => {
    if (!data) return new Map<string, ScreenStock[]>();
    const map = new Map<string, ScreenStock[]>();
    for (const s of data.stocks) {
      const list = map.get(s.classification) || [];
      list.push(s);
      map.set(s.classification, list);
    }
    // Sort each bucket by conviction
    for (const [, list] of map) {
      list.sort((a, b) => (b.conviction_score || 0) - (a.conviction_score || 0));
    }
    return map;
  }, [data]);

  const filteredStocks = useMemo(() => {
    if (!data) return [];
    let stocks = selectedCell
      ? (bucketMap.get(selectedCell) || [])
      : data.stocks;
    if (searchQuery) {
      const q = searchQuery.toLowerCase();
      stocks = stocks.filter((s) => s.ticker.toLowerCase().includes(q) || s.company.toLowerCase().includes(q));
    }
    return stocks.sort((a, b) => (b.conviction_score || 0) - (a.conviction_score || 0));
  }, [data, selectedCell, searchQuery, bucketMap]);

  if (loading) {
    return (
      <div className="flex items-center justify-center min-h-[60vh]">
        <p className="text-[13px]" style={{ color: "var(--color-text-muted)" }}>Loading...</p>
      </div>
    );
  }
  if (error || !data) {
    return (
      <div className="flex items-center justify-center min-h-[60vh]">
        <p className="text-[13px]" style={{ color: "#ef4444" }}>{error || "No data"}</p>
      </div>
    );
  }

  const selectedStock = selectedTicker ? data.stocks.find((s) => s.ticker === selectedTicker) : null;

  return (
    <div className="px-8 py-10">
      <h1 className="text-xl font-semibold mb-1">Universe</h1>
      <p className="text-[13px] mb-8" style={{ color: "var(--color-text-secondary)" }}>
        All {data.screened} screened stocks on the classification matrix.
        {selectedCell && (
          <button className="ml-2 underline hover:opacity-80" onClick={() => setSelectedCell(null)}>
            Clear filter
          </button>
        )}
      </p>

      {/* 3×3 Classification Matrix */}
      <div className="mb-10">
        {/* Axis labels */}
        <div className="flex items-center mb-2">
          <div className="w-24" />
          <div className="flex-1 flex justify-between text-[10px] tracking-wide px-1"
               style={{ color: "var(--color-text-muted)" }}>
            <span>← Quality High (≥70)</span>
            <span>Quality Mid (40-70)</span>
            <span>Quality Low (&lt;40) →</span>
          </div>
        </div>

        <div className="flex gap-0">
          {/* Y-axis labels */}
          <div className="w-24 flex flex-col justify-around pr-2 text-right text-[10px] tracking-wide"
               style={{ color: "var(--color-text-muted)" }}>
            <span>Value High<br />(≥70)</span>
            <span>Value Mid<br />(40-70)</span>
            <span>Value Low<br />(&lt;40)</span>
          </div>

          {/* Grid */}
          <div className="flex-1 grid grid-rows-3 gap-1.5">
            {MATRIX.map((row, ri) => (
              <div key={ri} className="grid grid-cols-3 gap-1.5">
                {row.map((cl, ci) => {
                  // Handle AVOID appearing twice
                  const key = `${ri}-${ci}`;
                  const stocks = ri === 2 && ci === 2
                    ? (bucketMap.get("AVOID") || []).filter((s) => s.value_score < 40 && s.quality_score < 40)
                    : ri === 1 && ci === 2
                    ? (bucketMap.get("AVOID") || []).filter((s) => s.value_score >= 40)
                    : (bucketMap.get(cl) || []);
                  const count = cl === "AVOID" ? stocks.length : (bucketMap.get(cl) || []).length;
                  const displayCount = stocks.length;
                  const color = classificationColors[cl];
                  const isSelected = selectedCell === cl;

                  return (
                    <button
                      key={key}
                      className="rounded-lg p-3 text-left transition-all duration-150 hover:scale-[1.01]"
                      style={{
                        backgroundColor: isSelected ? `${color}1a` : `${color}0a`,
                        border: `1px solid ${isSelected ? `${color}40` : `${color}20`}`,
                      }}
                      onClick={() => setSelectedCell(isSelected ? null : cl)}
                    >
                      <div className="text-[11px] font-medium mb-1" style={{ color }}>
                        {SHORT_LABELS[cl]}
                      </div>
                      <div className="font-mono text-lg font-semibold" style={{ color: "var(--color-text-primary)" }}>
                        {cl === "AVOID" ? displayCount : count}
                      </div>
                      <div className="text-[10px]" style={{ color: "var(--color-text-muted)" }}>
                        stocks
                      </div>
                    </button>
                  );
                })}
              </div>
            ))}
          </div>
        </div>

        <div className="flex justify-between mt-2 text-[10px] italic pl-24"
             style={{ color: "var(--color-text-muted)" }}>
          <span>← Cheap + High Quality = best</span>
          <span>Expensive + Low Quality = worst →</span>
        </div>
      </div>

      {/* Search + Stock Table */}
      <div className="mb-4">
        <input
          type="text"
          placeholder="Search by ticker or company..."
          value={searchQuery}
          onChange={(e) => setSearchQuery(e.target.value)}
          className="w-full max-w-sm rounded-md px-3 py-2 text-[13px] outline-none transition-colors"
          style={{
            backgroundColor: "var(--color-surface-1)",
            border: "1px solid var(--color-border)",
            color: "var(--color-text-primary)",
          }}
        />
      </div>

      <div className="text-[11px] uppercase tracking-[0.06em] mb-3" style={{ color: "var(--color-text-muted)" }}>
        {selectedCell ? `${SHORT_LABELS[selectedCell]} — ${filteredStocks.length} stocks` : `All ${filteredStocks.length} stocks`}
      </div>

      <div className="overflow-x-auto">
        <table className="w-full">
          <thead>
            <tr className="border-b" style={{ borderColor: "var(--color-surface-3)" }}>
              {["Ticker", "Company", "Classification", "V", "Q", "Conv", "F", "EY%", "Sector"].map((h) => (
                <th key={h} className={`text-[10px] font-medium uppercase tracking-[0.06em] py-2.5 px-2 text-left ${
                  ["V", "Q", "Conv", "F", "EY%"].includes(h) ? "text-right" : ""
                }`} style={{ color: "var(--color-text-muted)" }}>
                  {h}
                </th>
              ))}
            </tr>
          </thead>
          <tbody>
            {filteredStocks.slice(0, 100).map((s) => {
              const clColor = classificationColors[s.classification] || "#71717a";
              return (
                <tr key={s.ticker}
                    className="border-b cursor-pointer transition-colors duration-100"
                    style={{ borderColor: "rgba(39,39,42,0.5)" }}
                    onClick={() => setSelectedTicker(s.ticker)}
                    onMouseEnter={(e) => (e.currentTarget.style.backgroundColor = "var(--color-surface-1)")}
                    onMouseLeave={(e) => (e.currentTarget.style.backgroundColor = "transparent")}>
                  <td className="font-mono text-sm font-semibold py-2.5 px-2">{s.ticker}</td>
                  <td className="text-[13px] py-2.5 px-2 truncate max-w-[200px]" style={{ color: "var(--color-text-secondary)" }}>{s.company}</td>
                  <td className="py-2.5 px-2">
                    <span className="inline-flex rounded-full px-2 py-0.5 text-[10px] font-medium"
                          style={{ backgroundColor: `${clColor}26`, color: clColor }}>
                      {SHORT_LABELS[s.classification]}
                    </span>
                  </td>
                  <td className="font-mono text-[13px] py-2.5 px-2 text-right">{Math.round(s.value_score)}</td>
                  <td className="font-mono text-[13px] py-2.5 px-2 text-right">{Math.round(s.quality_score)}</td>
                  <td className="font-mono text-[13px] py-2.5 px-2 text-right font-medium">{s.conviction_score.toFixed(1)}</td>
                  <td className="font-mono text-[13px] py-2.5 px-2 text-right" style={{ color: "var(--color-text-secondary)" }}>{s.piotroski_f}/9</td>
                  <td className="font-mono text-[13px] py-2.5 px-2 text-right" style={{ color: "var(--color-text-secondary)" }}>
                    {s.earnings_yield != null ? `${s.earnings_yield.toFixed(1)}%` : "—"}
                  </td>
                  <td className="text-[11px] uppercase tracking-wide py-2.5 px-2" style={{ color: "var(--color-text-muted)" }}>{s.sector}</td>
                </tr>
              );
            })}
          </tbody>
        </table>
        {filteredStocks.length > 100 && (
          <p className="text-[12px] py-4 text-center" style={{ color: "var(--color-text-muted)" }}>
            Showing 100 of {filteredStocks.length} stocks
          </p>
        )}
      </div>

      {/* Stock Deep Dive */}
      {selectedStock && (
        <StockSheet stock={selectedStock} onClose={() => setSelectedTicker(null)} />
      )}
    </div>
  );
}
